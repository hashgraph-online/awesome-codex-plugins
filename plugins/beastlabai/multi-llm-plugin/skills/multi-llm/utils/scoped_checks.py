"""Scoped batch checks: ``driver.batch_checks: scoped`` and the full run it owes.

Opt-in; the default ``full`` changes nothing. Under ``scoped``, an
apply-code-fixes batch dispatched by the write executor (``--exec-subagents``)
is told to run ``driver.verify_command`` narrowed to the tests of the files it
changed (the command followed by a list of test selectors), and the phase then
owes one full run of that exact command against the final written state
before it can be recorded completed. Only a pytest command narrows that way
(:func:`narrowing_refusal`); any other command, the native leg and every other
phase run their checks as before, with one line saying why (:func:`narrowing`).
A batch whose scoped run would test nothing of what it changes runs the
command in full (:func:`full_check_reason`), and a scoped ``passed`` its reply
does not back is recorded ``not run`` (:func:`backed_scoped`).

The debt is a record in ``state.json`` (:data:`OWED_KEY`): written, and saved,
immediately before a narrowed prompt is first sent (:func:`record_owed`, from
the scheduler's dispatch hook), in the same save that drops the phase's
earlier completion, so no composite reads a stale completion while the run is
owed. It names the command by its SHA-256, so only the exact string the
batches deferred to settles it. Every writer of the phase's completion
settles it first through one rule (:func:`settle_action`): the executor's
finalize (``write_verify.VerifyStep``) and the completions the apply
orchestrator records itself (:func:`settle_owed_check`). A pass drops the
record, by its token, in the save that records the completion
(:func:`discharge`); a failure, or a configured command that is no longer the
one deferred to, leaves the phase not completed at exit 3.
``state_manager.mark_phase_completed_in_state`` refuses the completion while
the record stands, and ``StateManager.save`` applies the same rule to the
merged document under the state file's lock, whatever the caller.
``--fresh`` keeps it: the edits the narrowed batches made may still be in the
tree.

docs/development/checks.md#scoped-batch-checks holds the rest.
"""

from __future__ import annotations

import hashlib
import os
import posixpath
import re
import shlex
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from types import SimpleNamespace
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from .known_checks import (
    APPLY_FIX_BATCH_CHECKS_KEY,
    LISTED_FAILED,
    LISTED_NOT_RUN,
    LISTED_PASSED,
    listed_check_outcomes,
)
from .provider_registry import get_batch_check_settings
from .redact import redact_text
from .state_manager import (
    SCOPED_CHECK_OWED_KEY,
    SCOPED_CHECK_PHASE,
    SCOPED_CHECK_REVIEW_PHASE,
    owed_scoped_check_in_state,
    owed_scoped_check_token,
)
from .text_clip import clip

#: ``driver.batch_checks``'s two words.
BATCH_CHECKS_FULL = "full"
BATCH_CHECKS_SCOPED = "scoped"

#: The write kind and the phase word the setting applies to.
KIND = "apply_code_fixes"
PHASE = SCOPED_CHECK_PHASE

#: ``state.json``'s record of the owed full run:
#: ``{command_sha256, command, batches, token, recorded_at,
#: review_completed_at}``. ``command`` is the command redacted, for display
#: only; ``command_sha256`` is what settles it; ``token`` is new on every
#: write, so a settlement drops only the exact debt it checked
#: (:func:`discharge`); ``review_completed_at`` is the code review's
#: completion stamp at the last admission, the cycle a resume belongs to.
OWED_KEY = SCOPED_CHECK_OWED_KEY

#: How a line about an owed full run opens: on a stop, on a refusal, on the
#: summary's Verification line (``verification_lines.verification_line``).
OWED_LEAD = "The full check is owed"

#: How much of a command a line shows.
SHOWN_COMMAND_MAX_CHARS = 160

#: How a narrowed run is named beside its command, wherever one is shown.
SCOPED_LABEL = "scoped to the batch's tests"

#: Characters that make a command more than one plain command.
_SHELL_CHARACTERS = frozenset("&|;$`\\<>(){}!#\n\r")

#: The pytest launchers, by file name.
_PYTEST_NAMES = frozenset({"pytest", "py.test", "pytest.exe"})
_PYTHON = re.compile(r"python(?:3(?:\.\d+)?)?(?:\.exe)?")

#: The wrappers a pytest command may run under, and the ``uv run`` options
#: that take the next word as their value.
_RUN_WRAPPERS = frozenset({"uv", "poetry", "pdm"})
_UV_VALUE_OPTIONS = frozenset({
    "--project", "--directory", "--python", "-p", "--group", "--extra",
    "--package", "--with",
})

#: pytest options that take the next word as their value: a word after one
#: of them is that value, not a test the command already selects.
_PYTEST_VALUE_OPTIONS = frozenset({
    "-n", "-m", "-k", "-p", "-c", "-o", "-W", "-r", "--maxfail", "--dist",
    "--tb", "--rootdir", "--durations", "--timeout", "--junitxml",
    "--junit-xml", "--cov", "--cov-report", "--cov-config", "--deselect",
    "--ignore", "--ignore-glob", "--basetemp", "--confcutdir",
    "--import-mode", "--log-level", "--capture", "--numprocesses",
    "--maxprocesses", "--color", "--override-ini", "--cache-dir",
})


#: Files pytest reads for every test it collects: a batch that changes one
#: runs the full check, since no list of tests covers what it changed.
SHARED_COLLECTION_FILES = frozenset({"conftest.py", "pytest.ini", "tox.ini"})

#: Files that count as :data:`SHARED_COLLECTION_FILES` when they hold
#: pytest's configuration, by the section that holds it.
_PYTEST_CONFIG_SECTIONS = {"pyproject.toml": "[tool.pytest", "setup.cfg": "[tool:pytest]"}

#: A pytest test file's name.
_TEST_FILE = re.compile(r"(?:test_.+|.+_test)\.py")


def _digest(command: str) -> str:
    return hashlib.sha256(command.encode("utf-8")).hexdigest()


def shown(command: Any) -> str:
    """*command* as a line shows it: redacted, cut short, in backticks."""
    return f"`{clip(redact_text(str(command or '')), SHOWN_COMMAND_MAX_CHARS)}`"


def narrowing_refusal(command: str) -> Optional[str]:
    """Why *command* cannot be narrowed by appending test selectors to it, or
    ``None`` when it can: one plain pytest command (``pytest``, ``py.test``,
    ``python -m pytest``, optionally under ``uv run``, ``poetry run`` or
    ``pdm run``) carrying options only. A word that is no option's value is
    a selection of its own, which appended selectors would add to rather
    than narrow."""
    if any(character in _SHELL_CHARACTERS for character in command):
        return "it is more than one plain command"
    try:
        tokens = shlex.split(command)
    except ValueError:
        return "it does not parse as one command"
    index = 0
    if len(tokens) > 1 and tokens[0] in _RUN_WRAPPERS and tokens[1] == "run":
        index = 2
        while index < len(tokens) and tokens[index].startswith("-"):
            word = tokens[index]
            index += 1
            if word == "--":
                break
            if tokens[0] == "uv" and word in _UV_VALUE_OPTIONS:
                index += 1
    rest = tokens[index:]
    head = os.path.basename(rest[0]) if rest else ""
    if head in _PYTEST_NAMES:
        arguments = rest[1:]
    elif _PYTHON.fullmatch(head) and rest[1:3] == ["-m", "pytest"]:
        arguments = rest[3:]
    else:
        return "it is not a pytest command"
    index = 0
    while index < len(arguments):
        word = arguments[index]
        index += 1
        if not word.startswith("-") or word == "--":
            return f"it already selects what it runs ({clip(word, 60)})"
        if "=" not in word and word in _PYTEST_VALUE_OPTIONS:
            index += 1
    return None


def shared_collection_file(paths: Sequence[str], repo_root: str) -> Optional[str]:
    """The first of *paths* (repository-relative) that every test is
    collected or configured by (:data:`SHARED_COLLECTION_FILES`, or a
    ``pyproject.toml``/``setup.cfg`` holding a pytest section or not
    readable), else ``None``."""
    for path in paths:
        name = os.path.basename(str(path))
        if name in SHARED_COLLECTION_FILES:
            return str(path)
        section = _PYTEST_CONFIG_SECTIONS.get(name)
        if section is None:
            continue
        try:
            with open(os.path.join(repo_root, str(path)), encoding="utf-8",
                      errors="replace") as handle:
                text = handle.read()
        except OSError:
            return str(path)
        if section in text:
            return str(path)
    return None


def covering_tests(
    paths: Sequence[str], known: Sequence[str],
) -> Tuple[List[str], Optional[str]]:
    """``(tests, uncovered)``: the test files known to cover *paths*
    (repository-relative), found by name among *known* (the worktree's
    files), and the first path none covers (``None`` when each is covered).

    A test file covers itself; another ``.py`` file ``x.py`` is covered by a
    known ``test_x.py`` or ``x_test.py`` anywhere; nothing else is covered.
    """
    by_name: Dict[str, List[str]] = {}
    for item in known:
        by_name.setdefault(os.path.basename(item), []).append(item)
    tests: List[str] = []
    for path in paths:
        name = os.path.basename(str(path))
        if _TEST_FILE.fullmatch(name):
            found = [str(path)]
        elif name.endswith(".py"):
            stem = name[:-3]
            found = by_name.get(f"test_{stem}.py", []) + by_name.get(f"{stem}_test.py", [])
        else:
            found = []
        if not found:
            return [], str(path)
        tests += [item for item in found if item not in tests]
    return sorted(tests), None


def full_check_reason(
    declared: Sequence[str], repo_root: str, known: Optional[Sequence[str]],
) -> Tuple[Optional[str], List[str]]:
    """``(why, tests)``: why a batch declaring *declared* (repository-relative)
    runs the verify command in full instead of scoped, or ``None`` with the
    test files it is told to run scoped (:func:`covering_tests`).

    It runs in full when it changes a file every test is collected or
    configured by (:func:`shared_collection_file`), when the worktree's
    files could not be listed (*known* is ``None``), or when no test is
    known to cover one of its files: a scoped run would test nothing of it.
    """
    if not declared:
        return "it declares no file a test could cover", []
    shared = shared_collection_file(declared, repo_root)
    if shared is not None:
        return f"it changes {shared}, which every test is collected or configured by", []
    if known is None:
        return "the repository's test files could not be listed", []
    tests, uncovered = covering_tests(declared, known)
    if uncovered is not None:
        return f"no test file is known to cover {uncovered}", []
    return None, tests


def reply_ran(result: Any) -> Any:
    """A write reply's ``check.ran`` value, or ``None``."""
    check = result.get("check") if isinstance(result, dict) else None
    return check.get("ran") if isinstance(check, dict) else None


#: How many ``check.ran`` entries :func:`_scoped_evidence` reads.
_RAN_ENTRIES_MAX = 50

#: pytest options a scoped run may not add to the configured command: each
#: selects, deselects or reorders what runs (``-k``, ``--lf``), reads another
#: configuration (its ``addopts`` or ``testpaths``), or runs no test at all,
#: so a pass carrying one need not have run the files it names. Matched in
#: every spelling: ``--deselect=x``, ``-kkeep``, ``-qk keep``. ``-x`` stays.
_SELECTING_OPTIONS = frozenset({
    "-k", "-m", "--deselect", "--ignore", "--ignore-glob", "--pyargs",
    "--lf", "--last-failed", "--ff", "--failed-first", "--nf", "--new-first",
    "--sw", "--stepwise", "--sw-skip", "--stepwise-skip",
    "-c", "--config-file", "-o", "--override-ini",
    "--co", "--collect-only", "--collectonly", "--setup-only", "--setup-plan", "--fixtures",
    "--fixtures-per-test", "--markers", "-h", "--help", "-V", "--version",
})

#: What joins a shell line to another command or redirects it, unquoted.
_COMPOSING = frozenset("|&;<>()`$#\n\r")


def _composed(text: str) -> bool:
    """Whether shell line *text* is more than one plain command: an unquoted
    pipe, ``&&``/``||``, ``;``, ``&``, redirection, subshell, substitution,
    comment or line break, or a ``$``/backtick inside double quotes."""
    quote = ""
    escaped = False
    for character in text:
        if escaped:
            escaped = False
        elif character == "\\" and quote != "'":
            escaped = True
        elif quote:
            if character == quote:
                quote = ""
            elif quote == '"' and character in "$`":
                return True
        elif character in "'\"":
            quote = character
        elif character in _COMPOSING:
            return True
    return False


def canonical_path(path: str, repo_root: str) -> str:
    """*path* (a test selector's file part) repository-relative with ``/``,
    so absolute, ``./``-prefixed and relative spellings of one file compare
    equal. Lexical against *repo_root*: nothing is read on disk."""
    text = str(path).replace("\\", "/")
    if os.path.isabs(text) or posixpath.isabs(text):
        try:
            text = os.path.relpath(text, repo_root).replace("\\", "/")
        except ValueError:  # another drive: outside the repository
            pass
    return posixpath.normpath(text)


def _scoped_run_selectors(
    command_argv: Sequence[str], key: str, repo_root: str,
) -> Tuple[Optional[List[str]], Optional[str]]:
    """One ``check.ran`` key read as a scoped run of the configured command
    (*command_argv*, its argv): ``(None, None)`` when it is no such run (not
    that argv followed by more words); ``(None, why)`` when it is one that
    credits nothing (:func:`_composed`, :data:`_SELECTING_OPTIONS`); else the
    test files it names (:func:`canonical_path`), ``[]`` for options only."""
    text = str(key).strip()
    if len(text) > 1 and text[0] == text[-1] == "`":
        text = text[1:-1].strip()
    try:
        argv = shlex.split(text)
    except ValueError:
        return None, None
    if len(argv) <= len(command_argv) or argv[:len(command_argv)] != list(command_argv):
        return None, None
    if _composed(text):
        return None, "it is more than one plain command (a pipe, `||`, `&&`, `;` or a redirection)"
    words = argv[len(command_argv):]
    for word in words:
        if word.startswith("@"):
            # pytest expands any whole `@file` argument into more arguments,
            # `--` or not, an option's value included (`-W @args.txt`).
            return None, f"it reads more arguments from {clip(word, 60)}"
    picks: List[str] = []
    index = 0
    positional = False
    while index < len(words):
        word = words[index]
        index += 1
        if positional or not word.startswith("-") or word == "-":
            picks.append(canonical_path(word.split("::", 1)[0], repo_root))
        elif word == "--":
            positional = True
        elif word.startswith("--"):
            name = word.split("=", 1)[0]
            if name in _SELECTING_OPTIONS:
                return None, f"it adds {name}, so it need not have run every test it names"
            if "=" not in word and name in _PYTEST_VALUE_OPTIONS:
                index += 1
        else:
            for offset in range(1, len(word)):
                name = "-" + word[offset]
                if name in _SELECTING_OPTIONS:
                    return None, f"it adds {name}, so it need not have run every test it names"
                if name in _PYTEST_VALUE_OPTIONS:
                    index += 1 if offset == len(word) - 1 else 0
                    break
    return picks, None


def _scoped_evidence(
    command: str, ran: Any, repo_root: str,
) -> Tuple[Optional[List[str]], List[str]]:
    """``(selected, refused)``: the test files the passed scoped runs of
    *command* in *ran* (a reply's ``check.ran``) name, ``None`` when none
    names any, and why each passed entry that claims to be one credits
    nothing. Read here rather than through
    ``known_checks.listed_check_outcomes``, whose length cap would drop a
    run that names several test files."""
    try:
        command_argv = shlex.split(command)
    except ValueError:
        return None, []
    selected: List[str] = []
    refused: List[str] = []
    found = False
    entries = list(ran.items())[:_RAN_ENTRIES_MAX] if isinstance(ran, dict) else []
    for key, value in entries:
        if listed_check_outcomes({"x": value}).get("x") != LISTED_PASSED:
            continue
        picks, why = _scoped_run_selectors(command_argv, str(key), repo_root)
        if why is not None:
            refused.append(why)
        elif picks:
            found = True
            selected += picks
    return (selected if found else None), refused


def backed_scoped(
    scoped: Mapping[str, str], command: str, ran: Any, touched: Sequence[str],
    repo_root: str, tests: Sequence[str] = (),
) -> Tuple[Dict[str, str], Optional[str]]:
    """``(scoped, why)``: a batch's scoped outcome (:func:`split_listed`)
    with a ``passed`` its reply does not back read as ``not run``, and why.

    ``passed`` stands only when the reply's ``check.ran`` names the scoped
    run itself as passed: the command's argv followed by test selectors,
    one plain command (no shell composition) adding no option that
    selects what runs (:data:`_SELECTING_OPTIONS`). Its selectors, read
    against the repository root (:func:`canonical_path`), must include each
    test file the batch was told to (*tests*, repository-relative), and the
    batch must have changed no file every test is collected or configured
    by (*touched*). What pytest actually executed per file is never seen:
    the evidence is still the batch's own report, and the full run the
    phase owes is what checks it.
    """
    current = dict(scoped)
    if current.get(command) != LISTED_PASSED:
        return current, None
    shared = shared_collection_file(touched, repo_root)
    selected, refused = _scoped_evidence(command, ran, repo_root)
    missing = [test for test in tests
               if selected is not None and canonical_path(test, repo_root) not in selected]
    uncredited = f" (a run it reported credits nothing: {refused[0]})" if refused else ""
    if shared is not None:
        why = f"it changed {shared}, which every test is collected or configured by"
    elif selected is None and refused:
        why = f"its reply's scoped run of it credits nothing: {refused[0]}"
    elif selected is None:
        why = ("its reply's `ran` names no scoped run of it that passed (the "
               "command followed by the tests it ran)")
    elif missing:
        why = (f"its scoped run left out {', '.join(missing)}, which it was told "
               f"to include{uncredited}")
    else:
        return current, None
    current[command] = LISTED_NOT_RUN
    return current, why


def _raw(state: Any) -> Optional[Dict[str, Any]]:
    """The state dict behind *state* (a ``StateManager``, a test fake, a dict)."""
    if isinstance(state, dict):
        return state
    raw = getattr(state, "state", None)
    return raw if isinstance(raw, dict) else None


def owed(state: Any) -> Optional[Dict[str, Any]]:
    """The owed full run on record in *state*, or ``None``
    (``state_manager.owed_scoped_check_in_state``)."""
    return owed_scoped_check_in_state(_raw(state))


def defers_to(record: Mapping[str, Any], command: Optional[str]) -> bool:
    """Whether *record* is owed a run of exactly *command* (no normalising)."""
    return bool(command) and record.get("command_sha256") == _digest(str(command))


def _batches(record: Mapping[str, Any]) -> List[str]:
    return [str(item) for item in (record.get("batches") or []) if str(item)]


@dataclass(frozen=True)
class ScopedRun:
    """What one apply-code-fixes batch is told to run scoped: the verify
    *command* followed by the *tests* known to cover its files."""

    command: str
    tests: Tuple[str, ...]


@dataclass(frozen=True)
class Narrowing:
    """:func:`narrowing`'s answer."""

    #: The command an apply-code-fixes batch runs narrowed; ``None``: every
    #: batch runs its checks as before.
    command: Optional[str] = None
    #: The one line saying what the setting does for this run; ``None`` when
    #: the setting is ``full`` (nothing is said, nothing changes).
    line: Optional[str] = None


def narrowing(
    kind: str, *, executor: bool, anchor: Optional[str], state: Any = None,
    phase: Optional[str] = None,
) -> Narrowing:
    """Whether this run's apply-code-fixes batches run the verify command
    narrowed, and the line that says so or says why not.

    Narrows only under ``batch_checks: scoped``, on the executor leg
    (*executor*), for apply-code-fixes, when ``driver.verify_command`` is set
    and narrows by a selector list (:func:`narrowing_refusal`), and when no
    owed run of another command is on record in *state* (a run never defers
    two commands). Never raises: a config read that fails narrows nothing.
    """
    try:
        settings = get_batch_check_settings(anchor=anchor)
    except Exception:  # noqa: BLE001 - no config read narrows nothing
        return Narrowing()
    if settings.mode != BATCH_CHECKS_SCOPED:
        return Narrowing()
    lead = f"driver.batch_checks ({settings.mode_layer}): scoped"
    full = "every batch runs the repository's checks in full"
    if kind != KIND:
        return Narrowing(line=(
            f"{lead} applies to apply-code-fixes only; this "
            f"{phase or kind} phase runs its checks as before."
        ))
    if not executor:
        return Narrowing(line=(
            f"{lead} applies under --exec-subagents only; on the native leg "
            f"{full}."
        ))
    command = settings.command
    if not command:
        return Narrowing(line=f"{lead} does not apply: driver.verify_command is not set, so {full}.")
    refusal = narrowing_refusal(command)
    if refusal:
        return Narrowing(line=(
            f"{lead} does not apply: driver.verify_command ({settings.command_layer}) "
            f"{shown(command)} cannot be narrowed to a list of tests ({refusal}), so {full}."
        ))
    record = owed(state)
    if record is not None and not defers_to(record, command):
        return Narrowing(line=(
            f"{lead} does not narrow: earlier batches deferred the full run of "
            f"{shown(record.get('command'))}, and driver.verify_command "
            f"({settings.command_layer}) now reads {shown(command)}, so {full}; "
            f"the phase cannot complete until driver.verify_command reads the "
            f"deferred command again."
        ))
    return Narrowing(command=command, line=(
        f"{lead}: each batch runs {shown(command)} ({settings.command_layer}) "
        f"narrowed to the tests of the files it changed; the full command runs "
        f"once, before the phase can complete."
    ))


def record_owed(state: Any, command: str, task_id: str) -> bool:
    """Record that *task_id* deferred the full run of *command*, and drop the
    phase's earlier completion with it; the caller saves.

    Returns ``False`` (nothing written) for an owed run of another command
    or a state that keeps no dict: the batch is then told the full checks.
    """
    raw = _raw(state)
    if raw is None:
        return False
    record = owed(state)
    if record is not None and not defers_to(record, command):
        return False
    batches = _batches(record or {})
    if str(task_id) not in batches:
        batches.append(str(task_id))
    completed = raw.get("phases_completed")
    reviewed = completed.get(SCOPED_CHECK_REVIEW_PHASE) if isinstance(completed, dict) else None
    value = {
        "command_sha256": _digest(command),
        "command": clip(redact_text(command), SHOWN_COMMAND_MAX_CHARS),
        "batches": batches,
        # New on every write, the same batch sent again included: a full
        # run that started before this write never settles it.
        "token": uuid.uuid4().hex,
        "recorded_at": str((record or {}).get("recorded_at") or datetime.now().isoformat()),
    }
    if isinstance(reviewed, str) and reviewed:
        # This admission's review cycle, refreshed on every write
        # (``state_manager.owed_scoped_check_is_current``).
        value["review_completed_at"] = reviewed
    setter = getattr(state, "set", None)
    if callable(setter) and not isinstance(state, dict):
        setter(OWED_KEY, value)
    else:
        raw[OWED_KEY] = value
    reopen = getattr(state, "reopen_phase", None)
    if callable(reopen):
        reopen(PHASE)
    else:
        completed = raw.get("phases_completed")
        if isinstance(completed, dict):
            completed.pop(PHASE, None)
    return True


def discharge(state: Any, record: Mapping[str, Any]) -> None:
    """Drop *record*, the owed run whose full run just passed, and only it;
    the caller records the completion in the same save.

    On a ``StateManager`` the drop is conditional on the file still holding
    that record when it saves (``StateManager.discharge_scoped_check``, by
    its token): a debt recorded since the check started stays, and the
    completion beside it is refused at exit 3.
    """
    token = owed_scoped_check_token(record)
    settle = getattr(state, "discharge_scoped_check", None)
    if callable(settle):
        settle(token)
        return
    raw = _raw(state)
    if raw is not None and owed_scoped_check_token(owed(raw)) == token:
        raw.pop(OWED_KEY, None)


@dataclass(frozen=True)
class Settlement:
    """:func:`settle_action`'s answer for an owed full run."""

    record: Dict[str, Any]
    #: Run the configured command now: it is the one deferred to.
    run: bool
    #: Lines to log before it runs (a changed setting, the command).
    notes: List[str] = field(default_factory=list)
    #: The refusal, when it does not run: the headline first.
    lines: List[str] = field(default_factory=list)

    @property
    def batches(self) -> List[str]:
        return _batches(self.record)


def settle_action(
    record: Mapping[str, Any], *, mode: str, command: Optional[str],
    command_layer: str,
) -> Settlement:
    """What a completion does about the owed full run *record*, given the
    configuration now (*mode*, *command* from *command_layer*).

    It runs the command when it is exactly the one the batches deferred to,
    whatever ``batch_checks`` says now (a note says when it is no longer
    ``scoped``). Otherwise it refuses: only the configured command is ever
    run, and it is not the check the batches deferred, so nothing runs.
    """
    record = dict(record)
    batches = _batches(record)
    if defers_to(record, command):
        notes = []
        if mode != BATCH_CHECKS_SCOPED:
            notes.append(
                f"driver.batch_checks is now {mode}; running the full check "
                f"{len(batches)} scoped batch(es) deferred to."
            )
        return Settlement(record, True, notes)
    deferred = shown(record.get("command"))
    now = f"{shown(command)} ({command_layer})" if command else "nothing (it is unset)"
    headline = (
        f"{OWED_LEAD}, and it did not run: {len(batches)} batch(es) "
        f"({', '.join(batches) or 'none named'}) ran {deferred} scoped to their "
        f"tests and deferred its full run to the end of the phase, but "
        f"driver.verify_command now reads {now}."
    )
    return Settlement(record, False, lines=[
        headline,
        f"ERROR: the {PHASE} phase is NOT marked completed. Only the configured "
        f"command is ever run, and it is not the check those batches deferred, "
        f"so nothing ran.",
        f"Set driver.verify_command back to {deferred} and re-run {PHASE} with "
        f"--resume: nothing is dispatched again, and only the full check runs.",
    ])


#: The word a batch named in the record left no scoped outcome under.
NOT_REPORTED = "not reported"

#: The order :func:`scoped_tally` names the outcomes in.
_TALLY_ORDER = (LISTED_PASSED, LISTED_FAILED, LISTED_NOT_RUN, NOT_REPORTED)


def scoped_outcomes(state: Any, batches: Sequence[str]) -> Dict[str, str]:
    """``{batch: passed|failed|not run|not reported}``: what each of
    *batches* recorded for its scoped run (``apply_fix_batch_checks[<id>]
    .scoped``, read from *state* by batch id, so a resume's earlier batches
    are named too)."""
    raw = _raw(state) or {}
    reports = raw.get(APPLY_FIX_BATCH_CHECKS_KEY)
    reports = reports if isinstance(reports, dict) else {}
    out: Dict[str, str] = {}
    for batch in batches:
        record = reports.get(str(batch))
        scoped = record.get("scoped") if isinstance(record, dict) else None
        words = [str(word) for word in scoped.values()] if isinstance(scoped, dict) else []
        out[str(batch)] = words[0] if words else NOT_REPORTED
    return out


def scoped_tally(outcomes: Mapping[str, str]) -> str:
    """*outcomes* (:func:`scoped_outcomes`) as one clause, grouped by word:
    ``passed in b0; not run in b1``; ``""`` for none."""
    groups: Dict[str, List[str]] = {}
    for batch, word in outcomes.items():
        groups.setdefault(word if word in _TALLY_ORDER else NOT_REPORTED, []).append(batch)
    return "; ".join(
        f"{word} in {', '.join(groups[word])}" for word in _TALLY_ORDER if word in groups
    )


def owed_stop_line(record: Mapping[str, Any], state: Any = None) -> str:
    """The line a stop carries while the full run is owed; with *state*, the
    scoped outcome each batch recorded too (:func:`scoped_tally`)."""
    batches = _batches(record)
    tally = scoped_tally(scoped_outcomes(state, batches)) if state is not None else ""
    return (
        f"{OWED_LEAD}: {len(batches)} batch(es) of this phase ran "
        f"{shown(record.get('command'))} scoped to their tests"
        + (f" (scoped: {tally})" if tally else "")
        + ", and the phase cannot complete until it passes in full; --resume "
        "runs it once every batch is done."
    )


def native_owed_line(record: Mapping[str, Any], state: Any = None) -> str:
    """The native emit's ``[SCOPED_CHECK_OWED]`` text: what is owed, and that
    ``--mark-completed`` runs it, so the host runs no verification of its
    own after the batch loop."""
    return (
        f"{owed_stop_line(record, state)} Do not run driver.verify_command (or "
        f"any check in its place) after the batch loop: --mark-completed runs "
        f"{shown(record.get('command'))} in full, only if driver.verify_command "
        f"still reads it, and its outcome is this phase's verification."
    )


def native_settled_line(verification: Mapping[str, Any]) -> str:
    """The ``[SCOPED_CHECK_SETTLED]`` text: an early completion (nothing
    handed out) ran the owed full check, it passed, and the phase is
    recorded completed, so the host runs no verification and no
    ``--mark-completed`` of its own (``instructions/apply-code-fixes.md``)."""
    batches = [str(item) for item in verification.get("scoped_batches") or []]
    return (
        f"The full check is settled: {shown(verification.get('command'))} "
        f"({verification.get('source')}) passed in full in "
        f"{verification.get('duration_seconds')}s, as "
        f"{scoped_note(batches, verification.get('scoped_outcomes'))}, and {PHASE} "
        f"is recorded completed with no batch handed out. It is this phase's "
        f"verification: do not run driver.verify_command (or any check in its "
        f"place), and do not run --mark-completed."
    )


def scoped_note(batches: Sequence[str], outcomes: Optional[Mapping[str, str]] = None) -> str:
    """What a full run that settled an owed record adds to the line that
    reports it (the summary's Verification line, ``status``); with
    *outcomes* (the record's ``scoped_outcomes``), what each batch's scoped
    run recorded, so a ``not run`` never counts as a ``passed``."""
    note = f"the full run {len(batches)} batch check(s) {SCOPED_LABEL} deferred to"
    tally = scoped_tally(outcomes) if isinstance(outcomes, Mapping) else ""
    return f"{note} (scoped: {tally})" if tally else note


def split_listed(
    listed: Mapping[str, str], command: Optional[str],
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """``(listed, scoped)``: a batch's ``listed`` outcomes with the command it
    was told to run narrowed (*command*) moved to their own map, so its
    outcome is never read as a run of the command as listed."""
    rest = dict(listed)
    if not command or command not in rest:
        return rest, {}
    return rest, {command: rest.pop(command)}


def with_scoped_failures(
    findings: Optional[List[str]], scoped: Mapping[str, str], failed_word: str,
) -> Optional[List[str]]:
    """*findings* with one added, named as a narrowed run, for each command
    in *scoped* reported *failed_word* that no finding names already."""
    failed = [command for command, word in scoped.items() if word == failed_word]
    if not failed:
        return findings
    current = list(findings or [])
    for command in failed:
        if not any(" ".join(command.split()) in " ".join(str(item).split()) for item in current):
            current.append(
                f"{command} ({SCOPED_LABEL}): failed (the batch's report lists it as failed)"
            )
    return current


@dataclass(frozen=True)
class OwedCheckSettled:
    """:func:`settle_owed_check`'s answer: whether the phase may complete,
    the lines to print (a failure's first), and the run's record."""

    ok: bool
    lines: List[str]
    verification: Optional[Dict[str, Any]] = None


def settle_owed_check(
    state: Any, *, plan_path: str, log: Callable[[str], Any],
) -> Optional[OwedCheckSettled]:
    """Settle the full run scoped batches deferred, for a completion the apply
    orchestrator records itself (``--mark-completed``, the no-items exit, the
    scope-deferral exit, the native emit with nothing to hand out); ``None``
    when none is owed, and the caller goes on exactly as before.

    The rule is ``write_verify.VerifyStep.run``'s (:func:`settle_action`):
    the configured command runs when it is exactly the one deferred to, from
    the repository root, announced before it starts, bounded by
    ``driver.verify_timeout_s``; a pass drops the record from *state* for the
    caller to save with the completion. Anything else leaves the record and
    answers ``ok=False``: the caller records no completion and exits 3
    (docs/development/checks.md#scoped-batch-checks).
    """
    record = owed(state)
    if record is None:
        return None
    settings = get_batch_check_settings(anchor=plan_path)
    settlement = settle_action(
        record, mode=settings.mode, command=settings.command,
        command_layer=settings.command_layer,
    )
    for note in settlement.notes:
        log(f"[{PHASE}] {note}")
    if not settlement.run:
        return OwedCheckSettled(False, list(settlement.lines))
    command = str(settings.command)
    # Imported here: both import this module.
    from .write_safety import resolve_repo_root
    from .write_verify import VERIFY_TAIL_CHARS, VerifyCommand

    try:
        repo_root = resolve_repo_root(plan_path)
    except Exception as exc:  # noqa: BLE001 - no pinned root runs nothing
        return OwedCheckSettled(False, [
            f"{OWED_LEAD}, and it did not run: the repository root "
            f"could not be resolved ({getattr(exc, 'message', exc)}).",
            f"ERROR: the {PHASE} phase is NOT marked completed.",
        ])
    context = SimpleNamespace(repo_root=repo_root, anchor=plan_path, log=log)
    log(
        f"[{PHASE}] the full check {len(settlement.batches)} scoped "
        f"batch(es) deferred ({settings.command_layer}): running "
        f"`{redact_text(command)}` (timeout {settings.timeout}s)"
    )
    started = time.monotonic()
    exit_code, output = VerifyCommand(context).run(command, settings.timeout)  # type: ignore[arg-type]
    duration = time.monotonic() - started
    verification = {
        "command": redact_text(command),
        "source": settings.command_layer,
        "exit_code": exit_code,
        "duration_seconds": round(duration, 1),
        "output_tail": redact_text(output).strip()[-VERIFY_TAIL_CHARS:],
        "scoped_batches": settlement.batches,
        "scoped_outcomes": scoped_outcomes(state, settlement.batches),
    }
    log(
        f"[{PHASE}] full check: `{verification['command']}` exited "
        f"{exit_code} in {duration:.1f}s"
    )
    if exit_code == 0:
        discharge(state, record)
        return OwedCheckSettled(True, [], verification)
    lines = [
        f"{OWED_LEAD}, and it failed: `{verification['command']}` "
        f"({verification['source']}) exited {exit_code} after {verification['duration_seconds']}s.",
        f"ERROR: the {PHASE} phase is NOT marked completed: it was "
        f"{scoped_note(settlement.batches, verification['scoped_outcomes'])}, and a later batch can "
        f"break a test an earlier batch's scoped run skipped.",
    ]
    tail = str(verification["output_tail"] or "").strip()
    if tail:
        lines.append("Last output:")
        lines += [f"  {line}" for line in tail.splitlines()[-20:]]
    lines.append(
        "Nothing was rolled back. Fix the repository (or the fixes the batches "
        f"applied), then re-run {PHASE} with --resume: nothing is "
        "dispatched again, and only the full check runs."
    )
    return OwedCheckSettled(False, lines, verification)
