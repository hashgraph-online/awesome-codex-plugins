"""The plugin-landlock rung's dispatch half: the grant, the wrap, the scratch
directory, and what the parent reads back after a jailed child exits.

Plan ``codex-sandbox-unavailable-findings-and-fixes`` §6 F1 and §7.1 (steps 2
and 3, 2026-09-30). When codex's own sandbox cannot start, and only then, a
codex child may run under ``utils/landlock_exec.py``: a stdlib-only wrapper that
applies a Landlock ruleset to itself and ``exec``s codex. This module is the
**only** place that adds that wrapper prefix to an argv (``wrap_argv``), the
one place the allow-list is computed (``allow_entries``), and the one place a
jailed attempt's scratch directory is made and removed (``slot_tmpdir``).

The flow at a spawn site, in both lanes (F1 "How a dispatch receives its
grant"):

1. ``with slot_tmpdir(repo_root) as tmpdir`` — one directory per attempt;
2. render the codex argv with ``JailContext(request, tmpdir)`` (the adapter
   splices ``-c developer_instructions=…``);
3. ``_resolve_executable``;
4. compose the child env, as today;
5. ``complete_context(request, tmpdir, env)`` reads ``$CODEX_HOME`` from that
   env and checks it (``JailRefused`` when missing — nothing is spawned);
6. ``wrap_argv(resolved_argv, rung, context, env)`` returns the wrapped argv
   and the env with ``TMPDIR`` set;
7. ``home_snapshot`` → spawn → wait or kill the group → ``home_snapshot``;
8. while the context is alive: ``is_jail_failure``, ``jail_denied_edits`` and
   ``compare_home`` — only paths, classes and counts travel back;
9. the ``with`` removes the directory.

Nothing here is kept on an adapter, in a module global or in a cache: a
context is an argument, dropped with the attempt. The grade is ``incidental``:
the jail stops stray and incidental content writes, not a model set on
escaping (pathname Unix sockets, ``$CODEX_HOME``, ``chmod``/``utimes`` and the
network are not confined — F1 Limits).
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple

try:  # pragma: no cover - import shim mirrors the rest of utils/
    from .providers.base import (
        CODEX_HOME_CHECK_MARKER,
        JailContext,
        JailRequest,
        SandboxRung,
        WRITE_SCOPE_REPO_WIDE,
        WRITE_SCOPE_TASKS,
        WRITE_SCOPES,
    )
    from . import process_control
    from . import landlock_exec
    from . import git_utils as _git_utils
    from . import codex_trust as _codex_trust
except ImportError:  # pragma: no cover - direct-script import shim
    from utils.providers.base import (  # type: ignore[no-redef]
        CODEX_HOME_CHECK_MARKER,
        JailContext,
        JailRequest,
        SandboxRung,
        WRITE_SCOPE_REPO_WIDE,
        WRITE_SCOPE_TASKS,
        WRITE_SCOPES,
    )
    from utils import process_control  # type: ignore[no-redef]
    from utils import landlock_exec  # type: ignore[no-redef]
    from utils import git_utils as _git_utils  # type: ignore[no-redef]
    from utils import codex_trust as _codex_trust  # type: ignore[no-redef]

# ---------------------------------------------------------------------------
# The wrapper and its launch
# ---------------------------------------------------------------------------

_HERE = os.path.dirname(os.path.abspath(__file__))

#: Wrapper id → absolute path, built from this module's own ``__file__`` (the
#: omp adapter finds its overlay the same way). Never from ``PATH`` or the cwd.
#: Tests monkeypatch this table to point at a fake wrapper.
WRAPPER_PATHS: Dict[str, str] = {
    "landlock_exec": os.path.join(_HERE, "landlock_exec.py"),
}

#: The interpreter flags the wrapper runs under: isolated mode (no
#: ``PYTHONPATH``, no user site, no script dir on ``sys.path``) and no ``site``
#: (the venv's ``.pth`` files — executed code — do not run before the ruleset).
#: They bind the wrapper's interpreter only; codex inherits the env untouched.
WRAPPER_INTERPRETER_FLAGS: Tuple[str, ...] = ("-I", "-S")

#: The wrapper's own exit codes, re-exported so callers need not import the
#: script module by name.
EXIT_UNAVAILABLE = landlock_exec.EXIT_UNAVAILABLE
EXIT_REQUIRED_ENTRY = landlock_exec.EXIT_REQUIRED_ENTRY
NOTE_PREFIX = landlock_exec.NOTE_PREFIX

#: The kinds an allow entry may declare (the wrapper's own vocabulary).
KIND_DIR = "dir"
KIND_FILE = "file"


class JailRefused(Exception):
    """A jailed dispatch or probe cannot be granted: a required allow entry is
    missing or unusable (``$CODEX_HOME`` absent or inside the repo, a write
    target gone), or the scope is one the rung does not serve. Nothing is
    spawned; the message names the path and what to do."""

    def __init__(self, message: str, *, path: Optional[str] = None, reason: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.path = path
        self.reason = reason


@dataclass(frozen=True)
class AllowEntry:
    """One ``--allow``/``--allow-optional`` argument: a ``realpath``-resolved
    path, its declared kind and whether a missing one refuses."""

    path: str
    kind: str
    required: bool
    why: str = ""

    def argv(self) -> List[str]:
        flag = "--allow" if self.required else "--allow-optional"
        return [flag, f"{self.kind}:{self.path}"]


def wrapper_path(rung: SandboxRung) -> str:
    """The absolute path of ``rung``'s wrapper; ``KeyError`` for an unknown id
    (a rung naming a wrapper nobody ships is a programming error)."""
    return WRAPPER_PATHS[str(rung.wrapper)]


def is_wrapped(argv: Sequence[str]) -> bool:
    """Whether ``argv`` is a wrapped dispatch or probe (``wrap_argv``'s shape)."""
    return unwrap_argv(argv) is not None


def unwrap_argv(argv: Sequence[str]) -> Optional[List[str]]:
    """The CLI argv inside a wrapped ``argv`` (everything after the wrapper's
    ``--``), or ``None`` when ``argv`` is not wrapped. Used by the suite's
    probe guard and by the ``_spawn_in_context`` backstop."""
    items = [str(a) for a in argv]
    known = {os.path.basename(p) for p in WRAPPER_PATHS.values()}
    for index, item in enumerate(items[:6]):
        if os.path.basename(item) in known and item.endswith(".py"):
            try:
                sep = items.index("--", index + 1)
            except ValueError:
                return None
            return items[sep + 1:]
    return None


# ---------------------------------------------------------------------------
# $CODEX_HOME, the context, the allow-list
# ---------------------------------------------------------------------------


def resolve_codex_home(env: Mapping[str, str]) -> str:
    """``$CODEX_HOME`` as the child will see it: ``CODEX_HOME`` from ``env``
    (``~`` expanded), else ``$HOME/.codex`` from the same env. Not resolved
    through symlinks and not checked — :func:`complete_context` does that."""
    home = (env.get("HOME") or "").strip() or os.path.expanduser("~")
    value = (env.get("CODEX_HOME") or "").strip()
    if value:
        if value == "~" or value.startswith("~/"):
            return os.path.join(home, value[2:]) if value != "~" else home
        return os.path.expanduser(value)
    return os.path.join(home, ".codex")


def _inside(path: str, root: str) -> bool:
    """Whether ``path`` is ``root`` or beneath it (both already ``realpath``'d).

    The filesystem root contains every absolute path: ``root + os.sep`` would
    be ``//`` there, which no real path starts with, so every check built on
    this (a ``$CODEX_HOME`` of ``/`` containing the repo, the repo-root guard,
    the denied-path class) would pass when it has to refuse."""
    root = root.rstrip(os.sep) or os.sep
    if root == os.sep:
        return path.startswith(os.sep)
    return path == root or path.startswith(root + os.sep)


def complete_context(request: JailRequest, tmpdir: str, env: Mapping[str, str]) -> JailContext:
    """The attempt's :class:`JailContext`: ``request`` plus ``tmpdir`` plus the
    checked ``$CODEX_HOME`` read from the child's composed ``env``.

    Raises :class:`JailRefused` — nothing spawned — when the home does not
    exist or is not a directory (codex itself refuses an explicit home that does
    not exist; the plugin never creates one), or resolves inside the repo root
    (its dir rule would grant part of the repo).
    """
    raw = resolve_codex_home(env)
    home = os.path.realpath(raw)
    if not os.path.isdir(home):
        raise JailRefused(
            f"codex's home {render_home(raw)} does not exist, so the plugin's "
            f"Landlock jail cannot grant it; run codex once outside multi-llm "
            f"(e.g. `codex login`) to create it. The plugin never creates it.",
            path=raw, reason="codex-home-missing",
        )
    repo_root = os.path.realpath(request.repo_root) if request.repo_root else ""
    if repo_root and (_inside(home, repo_root) or _inside(repo_root, home)):
        raise JailRefused(
            f"codex's home {render_home(home)} resolves inside the repository "
            f"({render_home(repo_root)}) or contains it; its dir rule would grant "
            f"part of the repository, so the plugin's Landlock jail does not take "
            f"this job",
            path=home, reason="codex-home-in-repo",
        )
    return JailContext(request=request, tmpdir=tmpdir, codex_home=home)


def default_tasks_dir(plan_file: str, tasks_file: str) -> Optional[str]:
    """The directory a ``tasks`` grant may be a dir rule on, or ``None``.

    The tasks file's directory, ``realpath``'d, **only** when it is the plan's
    default ``plans/<stem>/tasks/`` (``tasks_file.find_tasks_file``'s fallback
    location). A ``TASKS_FILE`` override may put the file in ``plans/`` itself
    or in the output folder, where a dir rule would grant sibling plans or
    ``state.json`` and the phase dirs — there the grant is a file rule on the
    tasks file.
    """
    try:
        from .output_handler import sanitize_prefix
    except ImportError:  # pragma: no cover - direct-script import shim
        from utils.output_handler import sanitize_prefix  # type: ignore[no-redef]
    plan_abs = os.path.abspath(plan_file)
    default = os.path.realpath(
        os.path.join(os.path.dirname(plan_abs), sanitize_prefix(os.path.basename(plan_abs)), "tasks")
    )
    actual = os.path.dirname(os.path.realpath(tasks_file))
    return actual if actual == default else None


#: Base entries every jailed dispatch gets besides ``$CODEX_HOME`` and its own
#: ``TMPDIR`` (F1 allow-list table, measured 2026-09-29): ``/dev/null`` for
#: shell redirects; ``/dev/ptmx`` and ``/dev/pts`` for ``tty: true`` exec
#: sessions (``failed to openpty`` without them; optional).
BASE_DEVICE_ENTRIES: Tuple[AllowEntry, ...] = (
    AllowEntry("/dev/null", KIND_FILE, True, "shell redirects"),
    AllowEntry("/dev/ptmx", KIND_FILE, False, "tty: true exec sessions"),
    AllowEntry("/dev/pts", KIND_DIR, False, "tty: true exec sessions"),
)


def allow_entries(context: JailContext) -> List[AllowEntry]:
    """The allow-list for ``context``, each entry ``realpath``-resolved with its
    kind and whether it is required (F1 "Allow-list entries at dispatch").

    Base: ``$CODEX_HOME`` (dir, required), the attempt's ``TMPDIR`` (dir,
    required), ``/dev/null`` (file, required), ``/dev/ptmx`` + ``/dev/pts``
    (optional). A write scope adds its target: ``plan-file`` one **file** rule
    on the plan; ``tasks`` a dir rule on ``target_dir`` when the lane set it
    (the default tasks directory), else a file rule on the tasks file;
    ``repo-wide`` (plan step 3b revised, 2026-10-05, a user decision) one
    **dir rule on the repository root** (:func:`repo_wide_entry`): the whole
    repository — ``.git``, ``.codex``, ``.multi-llm`` and the run's output
    folder included — is writable inside the jail, and the developer message
    tells the model to leave those alone. Only the two narrower scopes keep
    the root unruled.

    Raises :class:`JailRefused` for a missing home (checked again here, since a
    probe may call this without :func:`complete_context`), a missing target
    or repository root, or an unknown scope. Never creates a path.
    """
    if not context.codex_home:
        raise JailRefused(
            "the jail context carries no $CODEX_HOME (complete_context was not "
            "called); nothing is spawned",
            reason="codex-home-unresolved",
        )
    entries: List[AllowEntry] = [
        AllowEntry(os.path.realpath(context.codex_home), KIND_DIR, True,
                   "every codex-internal write"),
        AllowEntry(os.path.realpath(context.tmpdir), KIND_DIR, True,
                   "the model's scratch space (exported as TMPDIR)"),
    ]
    entries.extend(BASE_DEVICE_ENTRIES)
    entries.extend(extra_base_entries(context))
    scope = context.write_scope
    repo_root = os.path.realpath(context.repo_root) if context.repo_root else ""
    if scope == WRITE_SCOPE_REPO_WIDE:
        entries.append(repo_wide_entry(context.request))
        return entries
    if scope:
        if scope not in WRITE_SCOPES:
            raise JailRefused(
                f"the plugin's Landlock jail does not take the {scope!r} write "
                f"scope (known: {', '.join(WRITE_SCOPES)})",
                reason="scope-not-served",
            )
        if not context.target:
            raise JailRefused(
                f"the {scope!r} write scope names no target; the grant is "
                f"missing, so nothing is spawned",
                reason="grant-missing",
            )
        if scope == WRITE_SCOPE_TASKS and context.target_dir:
            path, kind = os.path.realpath(context.target_dir), KIND_DIR
            if not os.path.isdir(path):
                raise JailRefused(
                    f"the tasks directory {render_home(path)} is gone; the "
                    f"batch fails before any child starts",
                    path=path, reason="target-missing",
                )
        else:
            path, kind = os.path.realpath(context.target), KIND_FILE
            if not os.path.isfile(path):
                raise JailRefused(
                    f"the write target {render_home(path)} is gone or not a "
                    f"regular file; the batch fails before any child starts",
                    path=path, reason="target-missing",
                )
        if repo_root and _inside(repo_root, path):
            raise JailRefused(
                "a write grant never covers the repository root",
                path=path, reason="repo-root",
            )
        entries.append(AllowEntry(path, kind, True, f"the {scope} write target"))
    return entries


# ---------------------------------------------------------------------------
# The repo-wide grant: one dir rule on the repository root (plan step 3b,
# revised 2026-10-05 — a user decision)
# ---------------------------------------------------------------------------

#: The version-control directory names the post-run sweep prunes
#: (``write_batch_scheduler.SWEEP_PRUNED_DIR_NAMES``), kept here because the
#: scheduler imports this module; a test pins the two tuples equal.
VCS_DIR_NAMES: Tuple[str, ...] = (".git", ".hg", ".svn")

#: The repository-root names a repo-wide batch is told to leave alone
#: (``codex.JAIL_DEVELOPER_TARGET_REPO``), **instruction-level only**. Until
#: 2026-10-05 they were the protected set of a per-entry enumeration that
#: kept the root unruled, so a batch could not create a top-level entry: the
#: racing re-run's whole plan was one root-level ``index.html`` and Codex's
#: implement was refused before any dispatch (F6). Landlock is allow-only
#: and a rule inherits down the tree, so a root rule necessarily covers
#: ``.git`` and ``.multi-llm``; asked to choose between that, a
#: check-and-restore of the protected set around every batch, and a scratch
#: copy, the user chose the root rule ("Backing up directories before each
#: batch is too resource intensive"). The post-run sweep, ``driver.write_paths``
#: and the scheduler's ``[GIT_CONFIG_CHANGED]`` line are the detective checks
#: left, and the plugin's own git calls carry ``git_utils.GIT_HARDENING_ARGS``.
REPO_WIDE_HANDS_OFF_NAMES: Tuple[str, ...] = (".git", ".codex", ".multi-llm")


def repo_wide_root(request: JailRequest) -> str:
    """The repository root a ``repo-wide`` grant rules, ``realpath``'d.
    Raises :class:`JailRefused` (``repo-root-missing``) when it is not a
    directory: nothing is spawned under a grant on a path that is not there."""
    root = os.path.realpath(request.repo_root)
    if not os.path.isdir(root):
        raise JailRefused(
            f"the repository root {render_home(root)} is not a directory, so "
            f"a repo-wide grant has nothing to rule",
            path=root, reason="repo-root-missing",
        )
    # Review fixes 2026-10-05: the rule lands only on a root git agrees is
    # the top level of the tree whose `.git` entry it holds. A planted
    # `core.worktree` (writable under this very grant) used to move
    # `rev-parse --show-toplevel`, and so the next dispatch's one rule, to
    # any directory; `write_safety.resolve_repo_root` refuses it first, and
    # this is the same check at the grant itself.
    _pinned, problem = _git_utils.pin_repo_root(root)
    if problem:
        raise JailRefused(
            f"the repository root {render_home(root)} cannot be trusted for a "
            f"repo-wide grant: {problem}",
            path=root, reason="repo-root-redirected",
        )
    return root


def repo_wide_entry(request: JailRequest) -> AllowEntry:
    """The one allow entry of a ``repo-wide`` grant: a required dir rule on
    the repository root (the wrapper refuses a required entry it cannot
    grant before codex starts)."""
    return AllowEntry(
        repo_wide_root(request), KIND_DIR, True,
        "repo-wide: the whole repository (root grant, 2026-10-05)",
    )


def extra_base_entries(context: JailContext) -> List[AllowEntry]:
    """Base entries added by plan step 1c's decision (2026-09-30).

    Step 1c measured (codex 0.159.0 and 0.159.1, offline against the localhost
    stub) a plan edit whose commands also ran ``git status``, ``git diff``,
    ``npx`` and a ``python3`` import, plus a code-mode turn. Every path it found
    denied is either redirected under the attempt's ``TMPDIR``
    (:func:`child_env_redirects`) or left denied and named in the developer
    instructions (``/dev/tty`` and ``~/.bash_history`` are denied silently and
    harmlessly). None became an allow-list row, so this is empty; it stays a
    function so a later re-measurement adds a row here, with its "why", in one
    place.
    """
    return []


def child_env_redirects(context: JailContext) -> Dict[str, str]:
    """Env redirects into the attempt's ``TMPDIR`` for paths plan step 1c found
    a jailed turn writing outside the allow-list (measured 2026-09-30: with all
    three set, every command of the tool turn exited 0 and the only EACCES left
    was ``/dev/tty``).

    They widen nothing — every target is under the scratch directory the
    grant already covers — and they cost a cold cache per dispatch.
    ``~/.npm`` is not an allow-list row because it persists and is shared with
    unjailed runs.
    """
    base = context.tmpdir
    redirects = {
        # `python3` imports from the repo write __pycache__ beside the module;
        # under the jail that is a denied write in the repo. Redirected, the
        # bytecode lands in the attempt's scratch dir.
        "PYTHONPYCACHEPREFIX": os.path.join(base, "pycache"),
        # `npx`/`npm` write their cache under ~/.npm, outside the allow-list.
        "npm_config_cache": os.path.join(base, "npm-cache"),
        # `git status` tries to refresh .git/index (a denied write in the
        # repo); with optional locks off it reads without writing.
        "GIT_OPTIONAL_LOCKS": "0",
    }
    if context.write_scope == WRITE_SCOPE_REPO_WIDE:
        redirects.update(repo_wide_env_redirects(context))
    return redirects


def repo_wide_env_redirects(context: JailContext) -> Dict[str, str]:
    """Plan step 1b's decision (measured 2026-10-02 on codex 0.160.0, offline
    against the localhost stub: an ``implement`` turn in a scratch repo with a
    small Python and a small npm project, whose commands ran ``uv run --frozen
    pytest``, the same with ``-n 2`` (pytest-xdist), ``npm test``, a direct
    ``/tmp`` and ``/dev/shm`` write, plus the protected-path attempts). For
    the ``repo-wide`` scope only, on top of step 1c's redirects:

    * ``UV_CACHE_DIR``: ``uv run`` refuses to start when ``~/.cache/uv`` is
      not writable (``Failed to initialize cache … sdists-v9/.git: Permission
      denied``). Redirected under ``TMPDIR`` it starts cold, and with the
      project's venv already synced (as a real repo's is) both pytest runs
      completed with no download and no denial. Not an allow-list row: the
      cache is shared with every other project's builds and persists.
    * ``PYTEST_ADDOPTS=-o cache_dir=…``: pytest makes ``.pytest_cache`` through
      a temp directory at the rootdir and a rename, which needs ``MAKE_DIR`` on
      the repository root (never granted); without the redirect every run
      prints ``PytestCacheWarning: could not create cache path … [Errno 13]``
      beside its pass. Prepended, so a ``-o cache_dir`` the runner passes
      itself wins. Measured clean with it, ``-n 2`` included.

    Kept denied, and named in the developer instructions: ``/tmp`` (a dir
    rule there would grant every sibling slot's ``TMPDIR``; ``tempfile``
    honours ``TMPDIR``, measured) and ``/dev/shm`` (shared by every process of
    the user; xdist did not need it). ``npm test`` was already clean under
    step 1c's ``npm_config_cache``; node's compile cache lands under
    ``TMPDIR`` by itself. ``~/.cargo`` and ``~/.cache/go-build`` were not
    measured (no such project) and stay denied.
    """
    import shlex
    base = context.tmpdir
    return {
        "UV_CACHE_DIR": os.path.join(base, "uv-cache"),
        "PYTEST_ADDOPTS": "-o cache_dir=" + shlex.quote(os.path.join(base, "pytest-cache")),
    }


def wrap_argv(
    resolved_argv: Sequence[str],
    rung: SandboxRung,
    context: JailContext,
    env: Mapping[str, str],
) -> Tuple[List[str], Dict[str, str]]:
    """The one place an argv gets the wrapper prefix (F1 "Dispatch shape" item 3).

    Returns ``[sys.executable, -I, -S, <wrapper>, --allow <kind:path>…, --,
    *resolved_argv]`` and a copy of ``env`` with ``TMPDIR`` set to the attempt's
    scratch directory plus the step-1c redirects. Called after
    ``_resolve_executable`` and after the child env is composed, at both spawn
    sites and by the rung probe. Raises :class:`JailRefused` when the grant
    cannot be built; never renders the base entries alone for a write scope.
    """
    if not rung.wrapper:
        raise ValueError(f"rung {rung.name!r} names no wrapper; nothing to wrap")
    entries = allow_entries(context)
    argv: List[str] = [sys.executable, *WRAPPER_INTERPRETER_FLAGS, wrapper_path(rung)]
    for entry in entries:
        argv.extend(entry.argv())
    argv.append("--")
    argv.extend(str(a) for a in resolved_argv)
    child_env = dict(env)
    child_env["TMPDIR"] = context.tmpdir
    child_env.update(merge_env_redirects(env, child_env_redirects(context)))
    return argv, child_env


#: The redirects that are option *lists* rather than paths: the redirect is
#: prepended to an inherited value instead of replacing it.
_PREPENDED_REDIRECTS: Tuple[str, ...] = ("PYTEST_ADDOPTS",)


def merge_env_redirects(
    env: Mapping[str, str], redirects: Mapping[str, str]
) -> Dict[str, str]:
    """``redirects`` with each option-list variable prepended to the value
    ``env`` already carries (fix round 4, 2026-10-02).

    ``PYTEST_ADDOPTS`` is a list of options pytest reads ahead of argv, and
    the parent's value (``-p no:cacheprovider --import-mode=importlib`` in a
    CI job, say) used to be clobbered by the ``-o cache_dir=…`` redirect, so
    the jailed pytest ran without the options the project relies on. The
    redirect goes first and the inherited value keeps the last word, exactly
    as a ``-o cache_dir`` the runner passes on argv does. A path redirect
    (``UV_CACHE_DIR`` and the rest) replaces, as before.
    """
    merged = dict(redirects)
    for name in _PREPENDED_REDIRECTS:
        inherited = (env.get(name) or "").strip()
        if name in merged and inherited:
            merged[name] = f"{merged[name]} {inherited}"
    return merged


#: Placeholders a preview renders in place of per-attempt paths.
PLACEHOLDER_CODEX_HOME = "<CODEX_HOME>"
PLACEHOLDER_TMPDIR = "<SLOT_TMPDIR>"


def preview_wrap_argv(
    resolved_argv: Sequence[str],
    rung: SandboxRung,
    request: Optional[JailRequest] = None,
) -> List[str]:
    """The wrapped shape with placeholder paths, for previews and budgets
    (``_prompt_over_budget``, ``_preview_argv``, the scheduler's
    ``_render_argv``). Creates nothing and reads no env."""
    argv: List[str] = [sys.executable, *WRAPPER_INTERPRETER_FLAGS, wrapper_path(rung)]
    argv += ["--allow", f"{KIND_DIR}:{PLACEHOLDER_CODEX_HOME}"]
    argv += ["--allow", f"{KIND_DIR}:{PLACEHOLDER_TMPDIR}"]
    for entry in BASE_DEVICE_ENTRIES:
        argv.extend(entry.argv())
    if request is not None and request.write_scope == WRITE_SCOPE_REPO_WIDE:
        # The root grant names the request's root as given (no realpath: a
        # preview reads nothing); the scheduler already resolved it.
        argv += ["--allow", f"{KIND_DIR}:{request.repo_root}"]
    elif request is not None and request.write_scope and request.target:
        if request.write_scope == WRITE_SCOPE_TASKS and request.target_dir:
            argv += ["--allow", f"{KIND_DIR}:{request.target_dir}"]
        else:
            argv += ["--allow", f"{KIND_FILE}:{request.target}"]
    argv.append("--")
    argv.extend(str(a) for a in resolved_argv)
    return argv


def preview_context(request: JailRequest) -> JailContext:
    """A context with placeholder paths, for rendering a preview argv."""
    return JailContext(request=request, tmpdir=PLACEHOLDER_TMPDIR,
                       codex_home=PLACEHOLDER_CODEX_HOME)


#: The wrapper's reason words that say why it refused (exit 125/126), as
#: opposed to the ``optional-entry-skipped:`` notes it prints on its way to the
#: Landlock calls that can still fail after them.
_REFUSAL_NOTE_WORDS = ("required-entry:", "unavailable:")


def wrapper_note(stderr: str) -> str:
    """The wrapper's own diagnostic line (``landlock_exec: …``), or ``""``.

    The line naming the refusal (``required-entry:`` / ``unavailable:``) is
    preferred over any earlier note: the wrapper prints its
    ``optional-entry-skipped:`` notes *before* the Landlock setup calls that
    can exit 126, so the first note is not always the reason. With no refusal
    line, the first note.
    """
    first = ""
    for line in (stderr or "").splitlines():
        line = line.strip()
        if not line.startswith(NOTE_PREFIX):
            continue
        if line[len(NOTE_PREFIX):].startswith(_REFUSAL_NOTE_WORDS):
            return line
        if not first:
            first = line
    return first


# ---------------------------------------------------------------------------
# The attempt's scratch directory
# ---------------------------------------------------------------------------

#: ``multi-llm-slot-<pid>-<start>-<random>`` — the parent's identity in the
#: name, so a crashed parent's leftovers can be told apart from a live one's.
SLOT_PREFIX = "multi-llm-slot-"
_SLOT_NAME = re.compile(r"^multi-llm-slot-(\d+)-([^-]*)-[A-Za-z0-9_]+$")

_SWEPT_BASES: set = set()
_SWEEP_LOCK = threading.Lock()


def _slot_base(repo_root: Optional[str]) -> str:
    """The parent's temp dir, ``realpath``'d; refused when inside the repo."""
    base = os.path.realpath(tempfile.gettempdir())
    if repo_root:
        root = os.path.realpath(repo_root)
        if _inside(base, root):
            raise JailRefused(
                f"the temp directory {render_home(base)} is inside the "
                f"repository {render_home(root)}, so a jailed attempt's scratch "
                f"directory would grant part of the repository; set TMPDIR "
                f"outside it",
                path=base, reason="tmpdir-in-repo",
            )
    return base


def _start_token(start: Any) -> str:
    """The start time as a name-safe token (no ``-``, which splits the name)."""
    text = re.sub(r"[^A-Za-z0-9_.]", "_", str(start or "unknown"))
    return text.replace("-", "_") or "unknown"


def sweep_slot_leftovers(base: Optional[str] = None) -> List[str]:
    """Remove crash leftovers under ``base`` (F1 "The scratch directory's
    lifecycle"). An entry goes only when its name matches the pattern, it is a
    real directory (not a symlink) owned by this user, and its parent's
    ``(pid, start)`` probes ``dead``. ``alive`` and ``unknown`` are kept; there
    is no age threshold. Returns the removed paths."""
    base = base or os.path.realpath(tempfile.gettempdir())
    removed: List[str] = []
    try:
        names = os.listdir(base)
    except OSError:
        return removed
    uid = os.getuid() if hasattr(os, "getuid") else None
    for name in names:
        match = _SLOT_NAME.match(name)
        if not match:
            continue
        path = os.path.join(base, name)
        try:
            info = os.lstat(path)
        except OSError:
            continue
        if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
            continue
        if uid is not None and info.st_uid != uid:
            continue
        verdict = _slot_owner_verdict(int(match.group(1)), match.group(2))
        if verdict != process_control.DEAD:
            continue
        try:
            _remove_slot_tree(path)
            removed.append(path)
        except OSError:
            pass
    return removed


def _restore_dir_rights(path: str) -> bool:
    """``chmod 0700`` on ``path`` when it is a real directory this user owns
    whose mode is not already ``0700`` (``lstat`` — a symlink is never
    followed, so a link planted in the tree cannot redirect the chmod onto a
    file outside it). ``True`` when it changed the mode."""
    try:
        info = os.lstat(path)
    except OSError:
        return False
    if not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) == 0o700:
        return False
    if hasattr(os, "getuid") and info.st_uid != os.getuid():
        return False
    try:
        os.chmod(path, 0o700)
    except OSError:
        return False
    return True


def _remove_slot_tree(top: str) -> None:
    """``shutil.rmtree(top)`` that survives a jailed model's ``chmod``.

    Landlock does not mediate ``chmod``, so the model can leave a
    subdirectory of its ``TMPDIR`` at ``000`` (``rmtree`` cannot open it) or
    the ``TMPDIR`` itself at ``500`` (nothing in it can be unlinked). On a
    ``PermissionError`` the handler restores ``0700`` on the failing path and
    its parent — only directories inside ``top``, never ``top``'s own parent
    (the shared temp dir) — and retries once per path: the unlink or rmdir
    again, or the whole entry when ``rmtree`` never reached it (a directory
    it could not open or list is skipped, not removed). Any other error, a
    path whose rights were already ``0700``, or a second failure on the same
    path propagates as before.
    """
    top = os.path.abspath(top)
    retried: set = set()

    def on_error(func: Any, path: str, exc: BaseException) -> None:
        if not isinstance(exc, PermissionError) or path in retried:
            raise exc
        retried.add(path)
        changed = False
        parent = os.path.dirname(path)
        if path != top and _inside(parent, top):
            changed = _restore_dir_rights(parent)
        changed = _restore_dir_rights(path) or changed
        if not changed:
            raise exc
        if func in (os.unlink, os.rmdir):
            func(path)
        elif stat.S_ISDIR(os.lstat(path).st_mode):
            _rmtree(path, on_error)
        else:
            os.unlink(path)

    _rmtree(top, on_error)


def _rmtree(path: str, on_error: Any) -> None:
    """``shutil.rmtree`` with an ``(func, path, exc)`` handler on every
    supported Python (``onexc`` from 3.12, ``onerror`` before it)."""
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=on_error)
    else:
        shutil.rmtree(path, onerror=lambda func, p, info: on_error(func, p, info[1]))


def _slot_owner_verdict(pid: int, token: str) -> str:
    """``alive`` / ``dead`` / ``unknown`` for a leftover's recorded parent —
    :func:`process_control.probe`'s rule, compared through the name's
    start-time token: a pid that is gone, or live under another start time
    (reused), is ``dead``; a live pid whose start time cannot be read, or a
    name recorded without one, is ``unknown`` and kept."""
    if not process_control.process_alive(pid):
        return process_control.DEAD
    if not token or token == "unknown":
        return process_control.UNKNOWN
    observed = process_control.process_start_time(pid)
    if observed is None:
        return process_control.UNKNOWN
    return process_control.ALIVE if _start_token(observed) == token else process_control.DEAD


@contextlib.contextmanager
def slot_tmpdir(repo_root: Optional[str] = None) -> Iterator[str]:
    """One scratch directory for one jailed attempt (or one rung probe).

    Made with ``tempfile.mkdtemp`` (mode 0700, never adopting an existing name)
    under the parent's ``gettempdir()``, named after the parent's pid and start
    time, **before** any rule is applied — a Landlock rule needs an existing
    inode. Removed with ``shutil.rmtree`` (fd-based, never follows a planted
    symlink; rights the model ``chmod``-ed away inside it are restored first,
    :func:`_remove_slot_tree`) when the ``with`` exits: after a clean exit, a timeout's group
    kill, an abort or an exception. A failed removal is a warning, never a
    failed slot. The first call per temp base in a process sweeps dead
    parents' leftovers. A temp base inside ``repo_root`` raises
    :class:`JailRefused` — a launch error, with nothing spawned.
    """
    base = _slot_base(repo_root)
    with _SWEEP_LOCK:
        first = base not in _SWEPT_BASES
        _SWEPT_BASES.add(base)
    if first:
        sweep_slot_leftovers(base)
    ident = process_control.identity()
    prefix = f"{SLOT_PREFIX}{ident.get('pid', os.getpid())}-{_start_token(ident.get('process_start_time'))}-"
    path = tempfile.mkdtemp(prefix=prefix, dir=base)
    try:
        yield path
    finally:
        try:
            _remove_slot_tree(path)
        except FileNotFoundError:
            pass
        except OSError as exc:
            print(
                f"multi-llm warning: could not remove the jailed attempt's "
                f"scratch directory {render_home(path)}: {exc}",
                file=sys.stderr,
            )


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render_home(path: Optional[str]) -> str:
    """``path`` with ``$HOME`` shown as ``~``, so a line can be pasted into an
    issue as it is."""
    if not path:
        return ""
    home = os.path.expanduser("~")
    text = str(path)
    if home and home != "~" and (text == home or text.startswith(home + os.sep)):
        return "~" + text[len(home):]
    return text


def render_allow_list(entries: Iterable[AllowEntry]) -> str:
    """``dir:~/.codex, dir:/tmp/multi-llm-slot-…, file:/dev/null, …``"""
    return ", ".join(f"{e.kind}:{render_home(e.path)}" for e in entries)


# ---------------------------------------------------------------------------
# After the child: jail failure, denied edits
# ---------------------------------------------------------------------------

#: How a codex-internal EACCES reads when it names its errno: Rust's
#: ``io::Error`` display (``… (os error 13)``) and debug form (``Os { code: 13,
#: kind: PermissionDenied, … }``), and the errno spellings a Python or shell
#: tool prints.
_EACCES = re.compile(
    r"os error 13|\[errno 13\]|\beacces\b|code:\s*13,\s*kind:\s*permissiondenied",
    re.IGNORECASE,
)
#: A bare ``permission denied`` names no errno: it counts only on a line that
#: also names an absolute path (``… /x: Permission denied``). Tied to nothing,
#: it is as likely an approval or policy refusal as a filesystem one, and it
#: would otherwise be a path-less "probable" jail denial.
_PERMISSION_DENIED = re.compile(r"permission denied", re.IGNORECASE)
_ABS_PATH = re.compile(r"(?<![\w.-])(/(?:[^\s'\"`:,;()\[\]{}<>|]+))")

JAIL_CLASS_JAIL = "jail"
JAIL_CLASS_ORDINARY = "ordinary"
JAIL_CLASS_PROBABLE = "probable"

#: :func:`is_jail_failure`'s preference when several lines carry an EACCES:
#: a jail denial anywhere decides, then an unnamed one, then an ordinary one.
_CLASS_RANK = {JAIL_CLASS_JAIL: 2, JAIL_CLASS_PROBABLE: 1, JAIL_CLASS_ORDINARY: 0}


@dataclass(frozen=True)
class JailEvidence:
    """What :func:`is_jail_failure` found: where the EACCES was (``stderr`` or
    ``event``), the one line carrying it (≤300 chars), the absolute path when
    the line names one, the class (``jail`` / ``ordinary`` / ``probable``) and,
    for ``ordinary``, why it is not a jail denial."""

    where: str
    line: str
    path: Optional[str]
    klass: str
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "where": self.where, "line": self.line, "path": self.path,
            "class": self.klass, "reason": self.reason,
        }


def _events(stdout: str) -> Iterator[Dict[str, Any]]:
    for raw in (stdout or "").splitlines():
        raw = raw.strip()
        if not raw.startswith("{"):
            continue
        try:
            event = json.loads(raw)
        except ValueError:
            continue
        if isinstance(event, dict):
            yield event


def _top_level_error_texts(stdout: str) -> Iterator[str]:
    """Texts of top-level ``error``/``turn.failed`` events — codex's own
    reports, never a command's output or the model's prose."""
    for event in _events(stdout):
        kind = event.get("type")
        if kind == "error":
            yield str(event.get("message") or "")
        elif kind == "turn.failed":
            err = event.get("error")
            if isinstance(err, dict):
                yield str(err.get("message") or "")
            elif err:
                yield str(err)


def _nearest_existing(path: str) -> str:
    probe = path
    while probe and not os.path.lexists(probe):
        parent = os.path.dirname(probe)
        if parent == probe:
            break
        probe = parent
    return probe or path


def classify_denied_path(path: Optional[str], entries: Sequence[AllowEntry]) -> Tuple[str, str]:
    """``(class, reason)`` for a denied path the child named.

    The jail handles write rights only and the parent runs outside it, so:
    outside every allow entry and writable by the user (``os.access(W_OK)`` on
    the path, or its nearest existing ancestor) is a **jail** denial; inside an
    allow entry, or not writable by the user either, is an **ordinary**
    permission error; no path is a **probable** jail denial.
    """
    if not path:
        return JAIL_CLASS_PROBABLE, "Codex did not name the path"
    real = os.path.realpath(path)
    for entry in entries:
        if entry.kind == KIND_DIR and _inside(real, entry.path):
            return JAIL_CLASS_ORDINARY, f"{render_home(real)} is inside the allow entry {render_home(entry.path)}"
        if entry.kind == KIND_FILE and real == entry.path:
            return JAIL_CLASS_ORDINARY, f"{render_home(real)} is an allow entry"
    if not os.access(_nearest_existing(real), os.W_OK):
        return JAIL_CLASS_ORDINARY, f"{render_home(real)} is not writable by this user either"
    return JAIL_CLASS_JAIL, ""


def wrapper_evidence(returncode: Optional[int], stderr: str) -> Optional[JailEvidence]:
    """The wrapper's own refusal at dispatch, as jail evidence
    (``where="wrapper"``, class ``jail``), or ``None``.

    Exit :data:`EXIT_REQUIRED_ENTRY` (a required entry missing, or turned into
    a symlink, since the probe passed) or :data:`EXIT_UNAVAILABLE` (a Landlock
    call failing after a good ABI query) together with the wrapper's
    ``landlock_exec:`` note: never a model error, never retried on another
    rung (F1 "Between the probe and a dispatch"). Both lanes read it — the
    fan-out's classifier and the executor's jailed-outcome read — through
    :func:`is_jail_failure`'s ``returncode``.
    """
    if returncode not in (EXIT_REQUIRED_ENTRY, EXIT_UNAVAILABLE):
        return None
    note = wrapper_note(stderr)
    if not note:
        return None
    path: Optional[str] = None
    body = note[len(NOTE_PREFIX):]
    if body.startswith("required-entry: "):
        spec = body[len("required-entry: "):]
        spec = spec.rsplit(": ", 1)[0] if ": " in spec else spec
        path = spec.split(":", 1)[1] if ":" in spec else spec
    return JailEvidence(
        where="wrapper", line=note[:300], path=path or None, klass=JAIL_CLASS_JAIL,
    )


def is_jail_failure(
    stderr: str,
    stdout: str,
    context: Optional[JailContext],
    *,
    returncode: Optional[int] = None,
) -> Optional[JailEvidence]:
    """A codex-internal EACCES in a jailed child's output, with its evidence, or
    ``None`` (F1 "Where it sits" item 6).

    Reads codex's own channels only: stderr and the top-level ``error`` /
    ``turn.failed`` events — never ``item.completed`` command output, which is
    the jail stopping a stray write (counted by :func:`jail_denied_edits`),
    and never the model's prose. The wrapper's own ``landlock_exec:`` lines
    are skipped here; given the child's ``returncode``, the wrapper's refusal
    at dispatch (:func:`wrapper_evidence`) is read first and wins.

    A line counts when it names its errno (:data:`_EACCES`), or says a bare
    ``permission denied`` beside an absolute path. Every such line is
    classified and the strongest wins — ``jail`` over ``probable`` over
    ``ordinary``, the first of equals — so an ordinary denial printed first
    cannot hide a jail denial after it, nor the reverse. What a lane makes of
    the evidence is its own rule, and it is the same on both: a child killed
    at its deadline is a timeout, never a jail failure.
    """
    if returncode is not None:
        refused = wrapper_evidence(returncode, stderr)
        if refused is not None:
            return refused
    candidates: List[Tuple[str, str]] = []
    for line in (stderr or "").splitlines():
        if not line.strip().startswith(NOTE_PREFIX):
            candidates.append(("stderr", line))
    for text in _top_level_error_texts(stdout):
        for line in text.splitlines():
            candidates.append(("event", line))
    entries: Optional[List[AllowEntry]] = None
    best: Optional[JailEvidence] = None
    for where, raw in candidates:
        full = raw.strip()
        line = full[:300]
        match = _ABS_PATH.search(line)
        path = match.group(1).rstrip(".") if match else None
        if not _EACCES.search(full) and not (path and _PERMISSION_DENIED.search(full)):
            continue
        if entries is None:
            entries = []
            if context is not None:
                try:
                    entries = allow_entries(context)
                except JailRefused:
                    entries = []
        klass, reason = classify_denied_path(path, entries)
        if best is None or _CLASS_RANK[klass] > _CLASS_RANK[best.klass]:
            best = JailEvidence(where=where, line=line, path=path, klass=klass, reason=reason)
            if klass == JAIL_CLASS_JAIL:
                break
    return best


@dataclass
class JailDenials:
    """What :func:`jail_denied_edits` read off a jailed child's stream — paths,
    item kinds and counts only, never output text (F1 "A denied edit is never
    recorded as applied")."""

    failed_file_changes: List[List[str]] = field(default_factory=list)
    in_scope_paths: List[str] = field(default_factory=list)
    replacement_paths: List[str] = field(default_factory=list)
    out_of_scope_count: int = 0
    out_of_scope_paths: List[str] = field(default_factory=list)

    @property
    def any_in_scope(self) -> bool:
        return bool(self.failed_file_changes or self.in_scope_paths or self.replacement_paths)

    @property
    def total(self) -> int:
        return (
            len(self.failed_file_changes) + len(self.in_scope_paths)
            + len(self.replacement_paths) + self.out_of_scope_count
        )

    def denied_paths(self) -> List[str]:
        seen: List[str] = []
        for group in self.failed_file_changes:
            for path in group:
                if path not in seen:
                    seen.append(path)
        for path in [*self.in_scope_paths, *self.replacement_paths]:
            if path not in seen:
                seen.append(path)
        return seen

    def to_dict(self) -> Dict[str, Any]:
        return {
            "failed_file_changes": [list(g) for g in self.failed_file_changes],
            "in_scope_paths": list(self.in_scope_paths),
            "replacement_paths": list(self.replacement_paths),
            "out_of_scope_count": self.out_of_scope_count,
            "out_of_scope_paths": list(self.out_of_scope_paths[:3]),
        }


_DENIAL_LINE = re.compile(r"permission denied|\[errno 13\]|os error 13|eacces", re.IGNORECASE)
_PATH_TOKEN = re.compile(r"([^\s'\"`:,;()\[\]{}<>|]+)")
#: The one shape every measured denial takes: the tool that was denied names
#: itself at column 0, then a colon (``/bin/bash: line 1: f.txt: Permission
#: denied``, ``sh: 1: cannot create f.txt: …``, ``rm: cannot remove 'x': …``,
#: ``fatal: Unable to create '.git/index.lock': …``, ``sed: couldn't open
#: temporary file ./sedAbC: …``, ``tee: x: …``, Python's terminal
#: ``PermissionError: [Errno 13] …`` and node's ``Error: EACCES: permission
#: denied, open 'x'``, bracketed when logged). A test suite's own report of
#: a ``PermissionError`` has none of it: pytest indents the exception with
#: ``E   ``, the short summary starts ``FAILED <id> - ``, a test id carries
#: the words inside brackets, and a printed ``str(exc)`` starts with
#: ``[Errno 13]`` (fix round 4, 2026-10-02: such a line used to resolve to a
#: declared path or a new root name, and a nothing-moved batch read FAILED).
_DENIAL_TOOL_PREFIX = re.compile(r"^\[?[\w./+-]+: ")
#: perl's ``-i`` denial names no tool: ``Can't do inplace edit on f.txt:
#: Cannot make temp name: Permission denied.`` (measured 2026-10-02, perl
#: 5.38 against an unwritable directory), the temp-file-and-rename shape
#: the plan-file grant denies, so it is read by its own shape.
_PERL_INPLACE_DENIAL = re.compile(r"^Can't do inplace edit on (?P<path>.+?): .*permission denied", re.IGNORECASE)


def _denied_paths_in(output: str) -> List[str]:
    """The paths named on ``Permission denied`` / ``[Errno 13]`` lines of one
    command's output, in the shapes the measured denials take (a tool naming
    itself at column 0, :data:`_DENIAL_TOOL_PREFIX`): ``sh: 1: cannot create
    f.txt: Permission denied``, ``PermissionError: [Errno 13] Permission
    denied: 'p.txt'``. A line of test output that merely quotes such an
    error names nothing."""
    found: List[str] = []
    for line in (output or "").splitlines():
        perl = _PERL_INPLACE_DENIAL.match(line)
        if perl is not None:
            if perl.group("path") not in found:
                found.append(perl.group("path"))
            continue
        if not _DENIAL_TOOL_PREFIX.match(line) or not _DENIAL_LINE.search(line):
            continue
        quoted = re.findall(r"'([^']+)'|\"([^\"]+)\"", line)
        candidates = [a or b for a, b in quoted]
        # A quoted error message is not a path (codex's Rust debug form:
        # `Os { code: 13, kind: PermissionDenied, message: "Permission denied" }`).
        candidates = [c for c in candidates if not _DENIAL_LINE.search(c)]
        if not candidates:
            head = _DENIAL_LINE.split(line)[0]
            parts = [p.strip() for p in head.split(":") if p.strip()]
            if parts:
                last = parts[-1]
                for prefix in ("cannot create ", "can't create ", "cannot open ", "cannot remove ",
                               "cannot touch ", "cannot move ", "cannot stat "):
                    if last.startswith(prefix):
                        last = last[len(prefix):]
                tokens = _PATH_TOKEN.findall(last)
                if tokens:
                    candidates = [tokens[-1]]
        for candidate in candidates:
            candidate = candidate.strip().strip("‘’")
            if candidate and candidate not in found:
                found.append(candidate)
    return found


def _resolve_against(path: str, cwd: Optional[str]) -> str:
    if not os.path.isabs(path):
        path = os.path.join(cwd or os.getcwd(), path)
    return os.path.realpath(path)


def jail_denied_edits(
    stdout: str,
    context: Optional[JailContext],
    *,
    cwd: Optional[str] = None,
) -> JailDenials:
    """Walk a jailed child's ``item.completed`` events for denials.

    * every ``file_change`` item with ``status: "failed"``, with its
      ``changes[].path`` list (the whole patch, not the one that was refused —
      the bytes decide what landed);
    * every ``command_execution`` item whose ``aggregated_output`` carries a
      denial for a path that resolves (against ``cwd``, symlinks resolved) to
      the write scope's target — the file, or a path under the tasks directory
      — counted in scope;
    * under a file-only grant (``plan-file``, the ``tasks`` file-rule
      fallback), a denial naming a **new** path in the target's directory (the
      temp file of ``sed -i`` or an editor's save) is a ``replacement`` denial;
      in-place writes to the target are granted, so a denial naming the target
      itself is one too;
    * every other command denial is counted out of scope (the first three paths
      kept).

    Under ``repo-wide`` (root grant, 2026-10-05) the scope is the whole
    repository: a denial naming a path inside the root is in scope — the
    grant covers it, so the jail should never have refused it — and every
    denial outside the root (``/tmp``, ``~/.cache``, a sibling slot's
    scratch) is the jail working, counted out of scope. There is no
    ``replacement`` reading: a dir rule on the root admits every write shape.

    With no write scope (a read-only slot) every command denial is out of scope
    and every failed ``file_change`` is still reported, for the slot's line.
    """
    result = JailDenials()
    scope = context.write_scope if context is not None else None
    target = os.path.realpath(context.target) if context is not None and context.target else None
    target_dir = (
        os.path.realpath(context.target_dir)
        if context is not None and context.target_dir else None
    )
    file_only = bool(scope) and target is not None and target_dir is None
    root = ""
    if scope == WRITE_SCOPE_REPO_WIDE and context is not None:
        root = os.path.realpath(context.repo_root)
    for event in _events(stdout):
        if event.get("type") != "item.completed":
            continue
        item = event.get("item")
        if not isinstance(item, dict):
            continue
        kind = item.get("type")
        if kind == "file_change" and item.get("status") == "failed":
            paths: List[str] = []
            for change in item.get("changes") or ():
                if isinstance(change, dict) and change.get("path"):
                    paths.append(_resolve_against(str(change["path"]), cwd))
            result.failed_file_changes.append(paths)
            continue
        if kind != "command_execution":
            continue
        for raw in _denied_paths_in(str(item.get("aggregated_output") or "")):
            resolved = _resolve_against(raw, cwd)
            if scope == WRITE_SCOPE_REPO_WIDE:
                if root and _inside(resolved, root):
                    if resolved not in result.in_scope_paths:
                        result.in_scope_paths.append(resolved)
                else:
                    result.out_of_scope_count += 1
                    if len(result.out_of_scope_paths) < 3:
                        result.out_of_scope_paths.append(resolved)
                continue
            if scope and target_dir and _inside(resolved, target_dir):
                if resolved not in result.in_scope_paths:
                    result.in_scope_paths.append(resolved)
            elif file_only and resolved == target:
                if resolved not in result.replacement_paths:
                    result.replacement_paths.append(resolved)
            elif file_only and os.path.dirname(resolved) == os.path.dirname(target) and not os.path.exists(resolved):
                if resolved not in result.replacement_paths:
                    result.replacement_paths.append(resolved)
            else:
                result.out_of_scope_count += 1
                if len(result.out_of_scope_paths) < 3:
                    result.out_of_scope_paths.append(resolved)
    return result


# ---------------------------------------------------------------------------
# The home check (F1 Limits, "$CODEX_HOME is writable…")
# ---------------------------------------------------------------------------

#: Files at the home's root that codex loads as configuration or instructions
#: in a later session (hashed whole). ``.env`` is one: codex's start-up
#: (codex-rs arg0 ``load_dotenv``) exports every variable in
#: ``$CODEX_HOME/.env`` not prefixed ``CODEX_``, so a jailed turn writing
#: ``OPENAI_BASE_URL`` there would redirect later unjailed sessions' API
#: traffic, key included. Like every entry here it is compared by hash only;
#: its bytes are never kept or logged.
HOME_FILES: Tuple[str, ...] = ("AGENTS.md", "AGENTS.override.md", ".env")
#: Trees codex loads as configuration, instructions or code in a later session
#: (compared by :func:`_tree_entry`: inode, size, mode and mtime, plus each
#: regular file's content hash and each symlink's destination — a link to a
#: directory, or the tree's root itself, included), each with the names under
#: it a normal turn rewrites (preflight step 1's write set), which the check
#: skips.
#:
#: ``ctime`` is deliberately **not** compared. ``link(2)``/``unlink(2)`` on
#: *any* name of an inode move that inode's ctime, and a plugin's uv ``.venv``
#: under ``plugins/cache/`` holds its packages as hardlinks into the uv cache
#: (15 names per inode, measured 2026-09-30), so every ``uv run``/``uv sync``
#: elsewhere on the machine that links from or prunes the cache moved the
#: ctime of watched files that no one wrote: a review-plan codex slot failed
#: closed on 23 pyyaml files whose bytes and mtime were untouched. The content
#: hash is what catches the write ctime used to stand in for — a same-size
#: rewrite with its mtime reset by ``utime``.
HOME_TREES: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("rules", ()),
    ("skills", (".system",)),
    ("plugins", (".codex-remote-plugin-install.json", ".remote-plugin-install-staging")),
    ("prompts", ()),
    ("memories", ()),
    ("hooks", ()),
)
#: Left out by classification (codex 0.158/0.159 home): `packages/` is codex's
#: own self-updating app-server daemon (2 GB here, rewritten by auto-update);
#: sqlite databases, `shell_snapshots/`, `tmp/`, `.tmp/`, `cache/`, `log/`,
#: `sessions/`, `history.jsonl` and `installation_id` are written by a normal
#: turn and are not loaded as instructions or code.
HOME_CONFIG = "config.toml"
HOME_AUTH = "auth.json"

#: One trust-only ``[projects."…"]`` table, mirroring
#: ``codex_trust._remove_table``: the header, the trust line and at most the
#: one blank line codex's writer puts before the table — never the whitespace
#: after it, which is the next table's separator (a greedy trailing ``\s*``
#: swallowed it, so an entry inserted mid-file after a kept table stripped to
#: text one blank line short of the file it was inserted into). The lookahead
#: admits only a table that ends there: a key before the next header is still
#: this table's in TOML, and stripping the header would hand it to the table
#: above, hiding the move.
_TRUST_TABLE = re.compile(
    r'^\n?\[projects\."((?:[^"\\]|\\.)*)"\]\s*\n'
    r'trust_level\s*=\s*"trusted"[ \t]*\r?(?:\n|\Z)'
    r'(?=(?:[ \t]*(?:#[^\n]*)?\r?\n)*[ \t]*(?:\[|(?:#[^\n]*)?\Z))',
    re.MULTILINE,
)


@dataclass
class HomeSnapshot:
    """A fingerprint of ``$CODEX_HOME``'s security-relevant set. Hashes and
    lstat fields only; ``config_text`` is kept in memory for the key-name diff
    and never logged or persisted."""

    home: str
    files: Dict[str, str] = field(default_factory=dict)
    #: home-relative path → ``(ino, size, mode, mtime_ns)``, with the content's
    #: sha256 appended for a regular file and the ``readlink`` destination for
    #: a symlink (never ctime — see :data:`HOME_TREES`).
    trees: Dict[str, Tuple[Any, ...]] = field(default_factory=dict)
    config_sha: str = ""
    config_text: str = ""
    foreign_trust: Tuple[str, ...] = ()
    auth_identity: str = ""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


#: Read size for hashing a watched file (memory stays bounded whatever its size).
_HASH_CHUNK = 1 << 20


def _content_sha(path: str, info: os.stat_result) -> str:
    """sha256 of the regular file ``info`` lstat'ed at ``path``.

    Opened ``O_NOFOLLOW | O_NONBLOCK``, so a path swapped for a symlink or a
    FIFO after the lstat neither follows the link nor blocks the snapshot;
    the descriptor must be the very inode lstat'ed (``"replaced"`` otherwise,
    which compares unequal to any hash, so a swap mid-snapshot is a change).
    ``"unreadable"`` when it cannot be opened or read."""
    flags = os.O_RDONLY
    for name in ("O_NOFOLLOW", "O_NONBLOCK", "O_CLOEXEC"):
        flags |= getattr(os, name, 0)
    try:
        fd = os.open(path, flags)
    except OSError:
        return "unreadable"
    try:
        opened = os.fstat(fd)
        if (not stat.S_ISREG(opened.st_mode)
                or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino)):
            return "replaced"
        digest = hashlib.sha256()
        while True:
            chunk = os.read(fd, _HASH_CHUNK)
            if not chunk:
                break
            digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return "unreadable"
    finally:
        os.close(fd)


#: Largest watched home file read whole (AGENTS.md, config.toml, auth.json);
#: one larger reads as ``"unreadable"``, which is a change from any real state.
_WATCHED_READ_LIMIT = 8 << 20


def _read_watched(path: str) -> Tuple[str, bytes]:
    """Safely read one watched ``$CODEX_HOME`` file: ``(status, data)``.

    ``status`` is ``"ok"`` (``data`` holds the bytes), ``"absent"`` (nothing
    there), or a marker that never equals another state: ``"symlink:<dest>"``
    for a link (``<dest>|sha256:<hex>`` of the target read through it, or
    ``<dest>|absent``/``replaced``/``unreadable``), ``"replaced"`` for anything else that is not
    the regular file lstat'ed (a FIFO, a device, a swapped inode), and
    ``"unreadable"`` for an open/read failure or an over-limit file.

    Opened ``O_NOFOLLOW | O_NONBLOCK`` and checked with fstat, so a jailed
    turn replacing the file with a FIFO or a link can neither block the
    snapshot nor redirect it."""
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return "absent", b""
    except OSError:
        return "unreadable", b""
    if stat.S_ISLNK(info.st_mode):
        try:
            dest = os.readlink(path)
        except OSError:
            return "unreadable", b""
        # Record the destination AND the target's content (read through the
        # link, same safeguards), so a retarget and an edit of the target are
        # both changes. Only a hash goes in the marker, never the bytes.
        tstatus, tdata = _open_and_read(path, follow=True)
        tail = ("sha256:" + _sha(tdata)) if tstatus == "ok" else tstatus
        return f"symlink:{dest}|{tail}", b""
    if not stat.S_ISREG(info.st_mode):
        return "replaced", b""
    return _open_and_read(path, info=info)


def _open_and_read(path: str, info: Optional[os.stat_result] = None,
                   follow: bool = False) -> Tuple[str, bytes]:
    """Bounded non-blocking read of ``path``. With ``follow`` the path is
    opened through a symlink and any regular file is accepted; otherwise
    ``O_NOFOLLOW`` and the descriptor must be the ``info`` inode."""
    flags = os.O_RDONLY
    for name in (("O_NONBLOCK", "O_CLOEXEC") if follow
                 else ("O_NOFOLLOW", "O_NONBLOCK", "O_CLOEXEC")):
        flags |= getattr(os, name, 0)
    try:
        fd = os.open(path, flags)
    except FileNotFoundError:
        return "absent", b""
    except OSError:
        return "unreadable", b""
    try:
        opened = os.fstat(fd)
        if (not stat.S_ISREG(opened.st_mode)
                or (info is not None
                    and (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino))):
            return "replaced", b""
        chunks: List[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, _HASH_CHUNK)
            if not chunk:
                break
            total += len(chunk)
            if total > _WATCHED_READ_LIMIT:
                return "unreadable", b""
            chunks.append(chunk)
        return "ok", b"".join(chunks)
    except OSError:
        return "unreadable", b""
    finally:
        os.close(fd)


def _tree_entry(path: str, *, links_only: bool = False) -> Optional[Tuple[Any, ...]]:
    """One watched-tree entry's fingerprint: ``(ino, size, mode, mtime_ns)``,
    plus the content's sha256 for a regular file or the destination for a
    symlink. ``None`` when it cannot be lstat'ed, or when ``links_only`` and
    it is not a symlink.

    No ctime: a hardlink made or removed anywhere else on the machine moves
    it without touching this file (:data:`HOME_TREES`). A content write that
    resets its mtime still changes the hash, and a rename-over still changes
    the inode."""
    try:
        info = os.lstat(path)
    except OSError:
        return None
    is_link = stat.S_ISLNK(info.st_mode)
    if links_only and not is_link:
        return None
    entry: Tuple[Any, ...] = (info.st_ino, info.st_size, info.st_mode, info.st_mtime_ns)
    if is_link:
        try:
            entry += (os.readlink(path),)
        except OSError:
            entry += ("unreadable",)
    elif stat.S_ISREG(info.st_mode):
        entry += (_content_sha(path, info),)
    return entry


def _strip_expected_trust(text: str, run_cwds: Sequence[str]) -> Tuple[str, Tuple[str, ...]]:
    """Remove every trust-only table (a ``[projects."<path>"]`` table holding
    exactly ``trust_level = "trusted"``) from the compared text, and return the
    remaining text plus the paths of every such table other than the run's
    own cwds (named in the run's closing summary, never a failure).

    The table for a cwd this run's children use is I12's expected entry. Any
    other one is stripped too, so a concurrent codex session's entry (run 6,
    #11a: sibling runs in other repositories sharing ``$CODEX_HOME``) never
    fails the check — but it is still named: ``$CODEX_HOME`` is on every jailed
    dispatch's allow list, so a batch of this run can add ``[projects."/"]``
    or ``[projects."~"]`` itself, and that table, which makes the next codex
    session there skip its trust prompt, is indistinguishable from another
    session's (fix round 17; round 16 named only tables inside the run's
    cwds, which hid exactly those). Which of them reach the summary is
    decided there (:class:`TrustEntriesNote`)."""
    cwds = {os.path.realpath(c) for c in run_cwds if c}
    raw = {str(c) for c in run_cwds if c}
    # The keys codex itself records for a session in a run cwd — its git
    # toplevel and, in a linked worktree, the main repository's root — which
    # `codex_trust` removes at the run's end (I12): expected, never named.
    # Asked of git only once a table outside the cwds turns up.
    codex_keys: List[set] = []
    foreign: List[str] = []

    def keep(match: "re.Match[str]") -> str:
        path = match.group(1).replace('\\"', '"').replace("\\\\", "\\")
        real = os.path.realpath(path)
        if real in cwds or path in cwds or path in raw:
            return ""
        if not codex_keys:
            codex_keys.append({
                key for cwd in cwds for key in _codex_trust.repo_keys(cwd)
            })
        if real in codex_keys[0]:
            return ""
        foreign.append(path)
        return ""

    stripped = _TRUST_TABLE.sub(keep, text)
    return stripped, tuple(sorted(foreign))


def home_snapshot(codex_home: Optional[str], run_cwds: Sequence[str] = ()) -> Optional[HomeSnapshot]:
    """Fingerprint ``codex_home``'s security-relevant set, or ``None`` when
    there is no home to read (the check is then skipped, never failed)."""
    if not codex_home or not os.path.isdir(codex_home):
        return None
    snap = HomeSnapshot(home=codex_home)
    for name in HOME_FILES:
        status, data = _read_watched(os.path.join(codex_home, name))
        snap.files[name] = _sha(data) if status == "ok" else status
    status, data = _read_watched(os.path.join(codex_home, HOME_CONFIG))
    if status == "ok":
        text = data.decode("utf-8", errors="replace")
        stripped, foreign = _strip_expected_trust(text, run_cwds)
        snap.config_sha = _sha(stripped.encode("utf-8"))
        snap.config_text = stripped
        snap.foreign_trust = foreign
    elif status == "absent":
        # codex creates the file holding only the trust table on a fresh home;
        # a missing file therefore compares as empty, not as its own state.
        snap.config_sha = _sha(b"")
    else:
        snap.config_sha = status
    status, data = _read_watched(os.path.join(codex_home, HOME_AUTH))
    if status == "ok":
        try:
            auth = json.loads(data.decode("utf-8"))
            tokens = auth.get("tokens") if isinstance(auth, dict) else None
            identity = json.dumps([
                auth.get("auth_mode") if isinstance(auth, dict) else None,
                auth.get("OPENAI_API_KEY") if isinstance(auth, dict) else None,
                tokens.get("account_id") if isinstance(tokens, dict) else None,
            ], sort_keys=True)
            snap.auth_identity = _sha(identity.encode("utf-8"))
        except ValueError:
            snap.auth_identity = "unreadable"
    else:
        snap.auth_identity = status
    for tree, skipped in HOME_TREES:
        root = os.path.join(codex_home, tree)
        # A root that is itself a link (`skills -> elsewhere`, dangling or
        # not) is recorded with its destination: os.walk follows it, so a
        # retarget onto another empty tree would otherwise show nothing.
        root_link = _tree_entry(root, links_only=True)
        if root_link is not None:
            snap.trees[tree] = root_link
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            # A skipped directory name counts only at the tree's top level
            # (`skills/.system/` is codex's own re-extraction; a `.system/`
            # planted inside a user skill is watched).
            dirnames[:] = sorted(
                d for d in dirnames if not (dirpath == root and d in skipped)
            )
            # os.walk lists a symlink to a directory in dirnames and never
            # descends into it, so `skills/x -> ../tmp/x` (a skill kept in an
            # unwatched part of the home) or a retargeted skill link is
            # recorded here with its destination. A real directory is covered
            # by the files under it.
            for name in dirnames:
                path = os.path.join(dirpath, name)
                link = _tree_entry(path, links_only=True)
                if link is not None:
                    snap.trees[os.path.relpath(path, codex_home)] = link
            for name in sorted(filenames):
                if name in skipped:
                    continue
                path = os.path.join(dirpath, name)
                entry = _tree_entry(path)
                if entry is None:
                    continue
                snap.trees[os.path.relpath(path, codex_home)] = entry
    return snap


def _toml_names(text: str) -> Dict[str, Any]:
    try:
        import tomllib  # Python 3.11+
    except ImportError:  # pragma: no cover - 3.10 fallback
        return {}
    try:
        return tomllib.loads(text)
    except Exception:  # noqa: BLE001 - a malformed file is reported as changed
        return {}


def _changed_keys(before: Any, after: Any, prefix: str = "") -> List[str]:
    """Dotted names of keys/tables that differ, never values."""
    names: List[str] = []
    if isinstance(before, dict) and isinstance(after, dict):
        for key in sorted(set(before) | set(after)):
            dotted = f"{prefix}{key}"
            if key not in before or key not in after:
                present = after.get(key) if key in after else before.get(key)
                children = (
                    [k for k, v in present.items() if isinstance(v, dict)]
                    if isinstance(present, dict) else []
                )
                # A table added or removed whole is named down to its
                # sub-tables (`[mcp_servers.x]` reads `mcp_servers.x`), never
                # with a value.
                if children:
                    names.extend(f"{dotted}.{child}" for child in sorted(children))
                else:
                    names.append(dotted)
            elif before[key] != after[key]:
                if isinstance(before[key], dict) and isinstance(after[key], dict):
                    names.extend(_changed_keys(before[key], after[key], dotted + "."))
                else:
                    names.append(dotted)
    elif before != after:
        names.append(prefix.rstrip(".") or "(file)")
    return names


@dataclass
class HomeChange:
    """What :func:`compare_home` found: changed files (home-relative), and for
    ``config.toml`` the changed table or key names — never values."""

    changed: List[str] = field(default_factory=list)
    config_keys: List[str] = field(default_factory=list)
    foreign_trust: List[str] = field(default_factory=list)

    @property
    def any(self) -> bool:
        return bool(self.changed)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "changed": list(self.changed),
            "config_keys": list(self.config_keys),
            "foreign_trust": list(self.foreign_trust),
        }

    def describe(self) -> str:
        return describe_changed(self.changed, self.config_keys)


#: A ``[CODEX_HOME_CHECK]`` line names at most this many changed paths. A
#: longer change is summarized — the count, the directory they share, the first
#: :data:`HOME_CHANGE_EXAMPLES` — and listed in full in a file under the state
#: directory, which the line names. Racing re-run 3 (opencode 01, 2026-10-05):
#: one line listed the ~40 files of a newly created uv ``.venv``, and the slot's
#: progress warning carried it into a 9 700-character tool result.
HOME_CHANGE_LISTED = 5
HOME_CHANGE_EXAMPLES = 3

#: Where :func:`describe_changed` writes a full list, under the state home.
HOME_CHANGE_LIST_DIR = "codex-home-check"

#: How many lists that directory keeps: writing one more removes the oldest
#: (fix round 8: nothing pruned it, and every render wrote another file).
HOME_CHANGE_LIST_KEEP = 50

_LIST_SEQ = {"n": 0}
_LIST_LOCK = threading.Lock()


def render_name(name: Any) -> str:
    """A changed name as one printable token: as found when every character
    is printable, else its ``repr`` (quoted, control characters, lone
    surrogates and line separators escaped). A jailed turn chooses the names
    under a watched tree, and a raw newline put a forged ``[CODEX_HOME_CHECK]``
    line on stderr and in the list file (fix round 8); a non-UTF-8 name made
    the list write raise."""
    text = str(name)
    return text if text.isprintable() else repr(text)


def _private_dir(directory: str) -> bool:
    """Create ``directory`` 0700, or make an existing one 0700; ``False`` when
    it is not a real directory of this user's."""
    os.makedirs(directory, mode=0o700, exist_ok=True)
    info = os.lstat(directory)
    if not stat.S_ISDIR(info.st_mode) or (hasattr(os, "getuid") and info.st_uid != os.getuid()):
        return False
    if stat.S_IMODE(info.st_mode) != 0o700:
        os.chmod(directory, 0o700)
    return True


def _prune_lists(directory: str, keep_name: str) -> None:
    """Remove the oldest lists beyond :data:`HOME_CHANGE_LIST_KEEP`, never
    ``keep_name``; best effort."""
    try:
        rows = []
        for entry in os.scandir(directory):
            if entry.name.endswith(".txt") and entry.is_file(follow_symlinks=False):
                rows.append((entry.stat(follow_symlinks=False).st_mtime_ns, entry.name))
    except OSError:
        return
    rows.sort()
    for _mtime, name in rows[:max(0, len(rows) - HOME_CHANGE_LIST_KEEP)]:
        if name != keep_name:
            with contextlib.suppress(OSError):
                os.unlink(os.path.join(directory, name))


def _write_change_list(lines: Sequence[str]) -> Optional[str]:
    """Write *lines* (already rendered by :func:`render_name`) to
    ``<state home>/codex-home-check/<record hash>.txt``; its path, or ``None``
    when it cannot be written (the line then says so).

    One file per record: rendering the same change again names the same file
    and does not rewrite it. The file is 0600 and the directory 0700 whatever
    the umask, and the directory keeps the newest
    :data:`HOME_CHANGE_LIST_KEEP` lists."""
    try:
        from .write_safety import state_home
    except ImportError:  # pragma: no cover - direct-script import shim
        from utils.write_safety import state_home  # type: ignore[no-redef]
    body = ("\n".join(lines) + "\n").encode("utf-8", "backslashreplace")
    name = hashlib.sha256(body).hexdigest()[:24] + ".txt"
    directory = os.path.join(state_home(), HOME_CHANGE_LIST_DIR)
    path = os.path.join(directory, name)
    with _LIST_LOCK:
        _LIST_SEQ["n"] += 1
        seq = _LIST_SEQ["n"]
    temp = os.path.join(directory, f".{name}.{os.getpid()}-{seq}.tmp")
    try:
        if not _private_dir(directory):
            return None
        status, current = _read_watched(path)
        if (status == "ok" and current == body
                and stat.S_IMODE(os.lstat(path).st_mode) == 0o600):
            return path
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        for extra in ("O_NOFOLLOW", "O_CLOEXEC"):
            flags |= getattr(os, extra, 0)
        fd = os.open(temp, flags, 0o600)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(body)
            os.replace(temp, path)
        finally:
            with contextlib.suppress(OSError):
                os.unlink(temp)
    except OSError:
        return None
    _prune_lists(directory, name)
    return path


def describe_changed(names: Sequence[str], config_keys: Sequence[str] = ()) -> str:
    """The changed-file part of a ``[CODEX_HOME_CHECK]`` line.

    Each home-relative name, with ``config.toml``'s changed key names after it
    (never a value), while there are at most :data:`HOME_CHANGE_LISTED`;
    otherwise ``N paths under <shared dir>/, e.g. a, b, c and K more (full
    list: <file>)``. Every name and key is rendered by :func:`render_name`, on
    the line and in the file. Only the line is shortened: the check's verdict
    and the record it returns are unchanged.
    """
    raw = [str(name) for name in names]
    keys = ", ".join(render_name(key) for key in config_keys)

    def entry(name: str, shown: str) -> str:
        if name == HOME_CONFIG and config_keys:
            return f"{render_name(shown)} ({keys})"
        return render_name(shown)

    parts = [entry(name, name) for name in raw]
    if len(parts) <= HOME_CHANGE_LISTED:
        return ", ".join(parts)
    try:
        shared = os.path.commonpath(raw)
    except ValueError:
        shared = ""
    if shared in raw:
        shared = os.path.dirname(shared)
    prefix = shared + os.sep if shared else ""
    examples = [
        entry(name, name[len(prefix):] if prefix and name.startswith(prefix) else name)
        for name in raw[:HOME_CHANGE_EXAMPLES]
    ]
    where = _write_change_list(parts)
    head = f"{len(parts)} paths" + (f" under {render_name(shared)}{os.sep}" if prefix else "")
    tail = (f"full list: {render_home(where)}" if where
            else "the full list could not be written")
    return (f"{head}, e.g. {', '.join(examples)} and "
            f"{len(parts) - len(examples)} more ({tail})")


def own_trust_entries_line(
    paths: Sequence[str], *, home: Optional[str] = None,
    provider: Optional[str] = None,
) -> str:
    """The closing-summary note for :attr:`HomeChange.foreign_trust`, both lanes.

    It names every trust table that appeared during the run besides the
    run's own cwds, and says who could have added one without blaming
    anyone: this run (a jailed batch can write ``$CODEX_HOME``) or another
    codex session running at the same time — the check cannot tell them
    apart, and it reads no other process's state to try (fix round 23: any
    process can be named codex, so a running "codex" in ``/`` explained a
    planted ``[projects."/"]``). Removing a table is offered as the user's
    own call, never as an order (live run 9: a host turned "delete its
    table" into advice to edit the config). Each path is a name a jailed
    turn could have written into the config, so it goes through
    :func:`render_name` and can never start a line of its own."""
    who = f"{provider}: " if provider else ""
    where = f"{render_home(home)}/config.toml" if home else "$CODEX_HOME/config.toml"
    names = ", ".join(render_name(render_home(path)) for path in paths)
    which = names if len(paths) == 1 else "one of them"
    return (
        f"{CODEX_HOME_CHECK_MARKER} {who}{where} gained trust entries during "
        f"this run, added by this run or by another codex session running at "
        f"the same time (not a failure): {names}. Codex trusts a listed "
        f"directory in later sessions without asking and loads its "
        f".codex/config.toml; if you never ran codex in {which}, removing its "
        f"[projects.\"<path>\"] table from {where} is your call."
    )


#: A ``[projects."<key>"]`` or ``[projects.'<key>']`` header, any table body.
_PROJECT_HEADER = re.compile(
    r'^[ \t]*\[projects\.(?:"((?:[^"\\]|\\.)*)"|\'([^\']*)\')\][ \t]*(?:#.*)?$',
    re.MULTILINE,
)


def project_table_keys(text: str) -> set:
    """The paths of every ``[projects."<path>"]`` table in a codex config."""
    keys = set()
    for match in _PROJECT_HEADER.finditer(text):
        if match.group(1) is not None:
            keys.add(match.group(1).replace('\\"', '"').replace("\\\\", "\\"))
        else:
            keys.add(match.group(2))
    return keys


@dataclass(frozen=True)
class TrustEntriesNote:
    """A closing-summary note for trust tables that appeared during a run,
    rendered when the summary is printed (fix round 17).

    Only the tables still in ``home``'s ``config.toml`` by then are named:
    a table that was gone again is another codex session's that removed its
    own entry when it finished (run 6, #11a: concurrent sibling runs, whose
    own clean-up removes what they added), and it left nothing behind to
    inspect, while one this run's batch planted stays until someone deletes
    it. A config that cannot be read keeps every path named. ``str()`` is the
    line, or ``""`` when none is left."""

    home: Optional[str]
    paths: Tuple[str, ...]
    provider: Optional[str] = None

    def remaining(self) -> Tuple[str, ...]:
        if not self.home:
            return tuple(self.paths)
        status, data = _read_watched(os.path.join(self.home, HOME_CONFIG))
        if status == "absent":
            return ()
        if status != "ok":
            return tuple(self.paths)
        present = project_table_keys(data.decode("utf-8", errors="replace"))
        return tuple(path for path in self.paths if path in present)

    def __str__(self) -> str:
        left = self.remaining()
        if not left:
            return ""
        return own_trust_entries_line(left, home=self.home, provider=self.provider)


def render_summary_entries(entries: Sequence[Any]) -> List[str]:
    """A closing summary's lines: each string as it is, and the
    :class:`TrustEntriesNote` entries of one home and provider merged into
    one line, at the first one's place, naming what is left of them now."""
    merged: Dict[Tuple[Optional[str], Optional[str]], List[str]] = {}
    order: List[Any] = []
    for entry in entries:
        if isinstance(entry, TrustEntriesNote):
            key = (entry.home, entry.provider)
            if key not in merged:
                merged[key] = []
                order.append(key)
            for path in entry.paths:
                if path not in merged[key]:
                    merged[key].append(path)
        else:
            order.append(entry)
    lines: List[str] = []
    for item in order:
        if isinstance(item, tuple):
            home, provider = item
            text = str(TrustEntriesNote(home, tuple(sorted(merged[item])), provider))
        else:
            text = str(item)
        if text:
            lines.append(text)
    return lines


def compare_home(before: Optional[HomeSnapshot], after: Optional[HomeSnapshot]) -> Optional[HomeChange]:
    """The difference between two snapshots of one home, or ``None`` when
    either side is missing (nothing to compare — never a failure)."""
    if before is None or after is None:
        return None
    change = HomeChange()
    for name in sorted(set(before.files) | set(after.files)):
        if before.files.get(name) != after.files.get(name):
            change.changed.append(name)
    if before.config_sha != after.config_sha:
        change.changed.append(HOME_CONFIG)
        change.config_keys = _changed_keys(
            _toml_names(before.config_text), _toml_names(after.config_text)
        ) or ["(unparsed change)"]
    if before.auth_identity != after.auth_identity:
        change.changed.append(f"{HOME_AUTH} (account identity)")
    for rel in sorted(set(before.trees) | set(after.trees)):
        if before.trees.get(rel) != after.trees.get(rel):
            change.changed.append(rel)
    change.foreign_trust = sorted(set(after.foreign_trust) - set(before.foreign_trust))
    return change


# ---------------------------------------------------------------------------
# The rung probe's setup (outside the jail)
# ---------------------------------------------------------------------------

#: The seeded file's bytes for the truncation control.
TRUNCATION_SEED = b"multi-llm truncation canary: these bytes must survive\n"


class ProbeSetupFailed(Exception):
    """The parent could not prepare what the rung probe needs outside the jail
    (the seeded file or the probe's TMPDIR): the walk records ``unknown`` and
    stops, exactly as a failed ``_prepare_probe_workdir`` does."""


@dataclass
class RungProbe:
    """A prepared rung probe: the wrapped argv, its env, and the seeded file
    whose bytes the parent compares afterwards."""

    argv: List[str]
    env: Dict[str, str]
    seeded: str
    entries: List[AllowEntry]

    def seed_intact(self) -> bool:
        try:
            with open(self.seeded, "rb") as handle:
                return handle.read() == TRUNCATION_SEED
        except OSError:
            return False


def canary_env(context: JailContext) -> Dict[str, str]:
    """The env keys the rung's canary reads for a write profile's controls:
    the plan or tasks file under a file rule, the tasks dir under a dir rule
    — each the dispatch's own declared target. A ``repo-wide`` grant hands
    over **no target in the tree**: the canary's ``$TMPDIR`` write is its one
    positive control (every entry is the same kind of rule, rendered by the
    same :func:`allow_entries` and taken by the same wrapper, a required
    entry it cannot grant is the wrapper's own refusal before anything runs,
    and a write the jail wrongly denies at dispatch is a ``[JAIL_DENIED]``
    failure naming the path; a control on the first sorted directory failed
    on plain permissions where the jail was fine and wrote into the user's
    tree on every ``status`` poll — adversarial review, 2026-10-02), and its
    negative controls live outside the repository (:func:`rung_probe` moves
    the canary's workdir there, since the root grant makes ``.multi-llm/tmp``
    writable). Empty for a read-only probe."""
    try:
        from .providers.codex import CANARY_ENV_WRITE_DIR, CANARY_ENV_WRITE_FILE
    except ImportError:  # pragma: no cover - direct-script import shim
        from utils.providers.codex import (  # type: ignore[no-redef]
            CANARY_ENV_WRITE_DIR, CANARY_ENV_WRITE_FILE,
        )
    if context.write_scope == WRITE_SCOPE_REPO_WIDE:
        return {}
    if not context.write_scope or not context.target:
        return {}
    if context.write_scope == WRITE_SCOPE_TASKS and context.target_dir:
        return {CANARY_ENV_WRITE_DIR: os.path.realpath(context.target_dir)}
    return {CANARY_ENV_WRITE_FILE: os.path.realpath(context.target)}


@contextlib.contextmanager
def rung_probe(
    rung: SandboxRung,
    request: JailRequest,
    resolved_probe_argv: Sequence[str],
    *,
    cwd: Optional[str],
    env: Optional[Mapping[str, str]] = None,
) -> Iterator[RungProbe]:
    """Prepare a wrapped rung's probe outside the jail, then clean it up.

    The walk has already made ``<cwd>/<rung.probe_workdir>`` and proven it
    writable. This seeds the truncation file there, makes the probe's own
    ``TMPDIR`` through :func:`slot_tmpdir`, completes the context from the
    probe child's env (``$CODEX_HOME`` read the same way a dispatch reads it)
    and wraps the pinned ``resolved_probe_argv``. Raises
    :class:`ProbeSetupFailed` (walk: ``unknown``) when the seed or the
    ``TMPDIR`` cannot be made — a temp base inside the repo (``slot_tmpdir``'s
    ``tmpdir-in-repo`` refusal) included, since that is a preparation failure
    and not a measurement of the rung — and :class:`JailRefused` (walk:
    ``absent``, with the note) when a required entry is missing — the same
    allow entries the dispatch it gates would get.

    A ``repo-wide`` probe (root grant, 2026-10-05) cannot use the in-repo
    workdir for its negative controls: the root rule makes ``.multi-llm/tmp``
    writable, so a canary there would read "not denied" on a working jail.
    Its workdir is a fresh directory under the parent's temp base instead
    (a sibling of the slot ``TMPDIR``, outside every allow entry), handed to
    the canary as ``$MULTI_LLM_CANARY_WORKDIR`` and removed afterwards; the
    positive control stays the ``$TMPDIR`` write.
    """
    try:
        from .providers.codex import CANARY_ENV_PYTHON, CANARY_ENV_SEEDED, CANARY_ENV_WORKDIR
    except ImportError:  # pragma: no cover - direct-script import shim
        from utils.providers.codex import (  # type: ignore[no-redef]
            CANARY_ENV_PYTHON, CANARY_ENV_SEEDED, CANARY_ENV_WORKDIR,
        )
    base_env = dict(os.environ if env is None else env)
    outside: Optional[str] = None
    if request.write_scope == WRITE_SCOPE_REPO_WIDE:
        try:
            outside = tempfile.mkdtemp(
                prefix="plugin-landlock-probe-", dir=_slot_base(request.repo_root),
            )
        except JailRefused as exc:
            raise ProbeSetupFailed(
                f"could not make the probe's negative-control directory: {exc.message}"
            ) from exc
        except OSError as exc:
            raise ProbeSetupFailed(
                f"could not make the probe's negative-control directory: {exc}"
            ) from exc
        workdir = outside
    else:
        workdir = os.path.join(os.path.abspath(cwd or os.getcwd()), rung.probe_workdir or "")
    try:
        fd, seeded = tempfile.mkstemp(prefix="plugin-landlock-seed-", dir=workdir)
        with os.fdopen(fd, "wb") as handle:
            handle.write(TRUNCATION_SEED)
    except OSError as exc:
        if outside is not None:
            shutil.rmtree(outside, ignore_errors=True)
        raise ProbeSetupFailed(f"could not seed the truncation file: {exc}") from exc
    try:
        try:
            tmp_cm = slot_tmpdir(request.repo_root)
            tmpdir = tmp_cm.__enter__()
        except JailRefused as exc:
            # The parent could not prepare the probe's TMPDIR (its temp base
            # resolves inside the repo): ``unknown``, which stops the walk
            # with no rung, exactly like a failed ``_prepare_probe_workdir``.
            # Propagated as JailRefused it read as ``absent`` and let ``auto``
            # fall through to the uncontained rung.
            raise ProbeSetupFailed(f"could not make the probe's TMPDIR: {exc.message}") from exc
        except OSError as exc:
            raise ProbeSetupFailed(f"could not make the probe's TMPDIR: {exc}") from exc
        try:
            context = complete_context(request, tmpdir, base_env)
            entries = allow_entries(context)
            argv, child_env = wrap_argv(resolved_probe_argv, rung, context, base_env)
            child_env[CANARY_ENV_SEEDED] = seeded
            child_env[CANARY_ENV_PYTHON] = sys.executable
            if outside is not None:
                child_env[CANARY_ENV_WORKDIR] = outside
            child_env.update(canary_env(context))
            yield RungProbe(argv=argv, env=child_env, seeded=seeded, entries=entries)
        finally:
            tmp_cm.__exit__(None, None, None)
    finally:
        try:
            os.unlink(seeded)
        except OSError:
            pass
        if outside is not None:
            shutil.rmtree(outside, ignore_errors=True)


__all__ = [
    "AllowEntry",
    "TrustEntriesNote",
    "project_table_keys",
    "render_summary_entries",
    "BASE_DEVICE_ENTRIES",
    "EXIT_REQUIRED_ENTRY",
    "EXIT_UNAVAILABLE",
    "HomeChange",
    "HomeSnapshot",
    "JailDenials",
    "JailEvidence",
    "JailRefused",
    "NOTE_PREFIX",
    "ProbeSetupFailed",
    "REPO_WIDE_HANDS_OFF_NAMES",
    "RungProbe",
    "TRUNCATION_SEED",
    "VCS_DIR_NAMES",
    "WRAPPER_PATHS",
    "allow_entries",
    "canary_env",
    "child_env_redirects",
    "merge_env_redirects",
    "repo_wide_env_redirects",
    "repo_wide_entry",
    "repo_wide_root",
    "classify_denied_path",
    "compare_home",
    "complete_context",
    "default_tasks_dir",
    "home_snapshot",
    "is_jail_failure",
    "is_wrapped",
    "jail_denied_edits",
    "preview_context",
    "preview_wrap_argv",
    "render_allow_list",
    "render_home",
    "rung_probe",
    "slot_tmpdir",
    "sweep_slot_leftovers",
    "unwrap_argv",
    "wrap_argv",
    "wrapper_evidence",
    "wrapper_note",
]
