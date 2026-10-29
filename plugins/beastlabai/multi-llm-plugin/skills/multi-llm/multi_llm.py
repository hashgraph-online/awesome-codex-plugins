#!/usr/bin/env python3
"""multi_llm.py — the single entry point for every multi-llm mode.

    uv run --project <skill-dir> -- python <skill-dir>/multi_llm.py <mode> [args]

A host shim resolves *one* path, once, and routes nothing itself.

Grammar (one line, no shell preprocessing)::

    multi_llm.py <mode> [<positional>…] [--host <id>] [mode flags…]

* ``<mode>`` is a bare word and must be ``argv[1]``; unknown or missing is exit 3
  listing the valid modes. Users still type ``--review-plan``; the shim maps
  flag → mode word through the closed table in ``modes.py``, so this script never
  has to disambiguate a mode flag from an option.
* **Positionals are normalized into the flags the target already parses** — plan
  modes take ``<plan>`` → ``--plan-file``; ``ask`` takes ``<plan> <question>`` →
  ``--plan-file`` + ``--question`` (falling back to ``--question-file``, written
  *here* and never by the driving agent, when the question outgrows the argv
  budget); ``install-host`` takes ``<host>``; ``init`` takes none. An extra
  positional is exit 3, never silently dropped. The commit modes take an
  optional ``[<range>]`` instead, every leading bare word (``-N`` included)
  joined into one ``--revs`` value, or ``--plan-file`` for a commit brief's
  path; they refuse a typed ``--plan-file``, ``--base-ref`` or ``--head-ref``
  (``[COMMIT_FLAG_CONFLICT]``), which their front door synthesises.
* **Everything after the positionals is forwarded verbatim** to that mode's own
  argparse parser, which stays the single source of truth for its options.
  ``multi_llm.py <mode> --help`` prints that parser's help.
* **Dispatch is in-process**, never ``subprocess``: the target's
  ``main(argv) -> int`` is imported lazily and called, so one ``uv`` resolution
  covers the whole invocation, a plan path containing a space survives by
  construction (the hand-off is a Python list — ``shlex`` never runs on this
  path), stream setup happens once, and foreground Ctrl-C reaches the code that
  owns the phase dir with no forwarding layer.
* **Exit codes are uniform and never remapped**: 0 done, 1 unexpected error,
  2 nothing to do / phase already complete, 3 needs a human. Exit **3** is
  reserved across every mode for "unattended run cannot proceed" (missing
  tooling, unmet prerequisite, contradictory or empty decision flag), so a host
  can tell "needs a human" from "already done" (exit 2) without parsing prose.
  The only codes this script invents are the 3s it raises for an unknown mode, a
  bad positional, a rejected flag combination, an empty/unrecognized decision
  value (D6 row 15) and a missing ``uv`` (D6 row 1 / D6c layer 3) — plus the one
  code it *rewrites*: argparse's usage exit (2) out of a target's own parser
  becomes 3, because 2 already means "phase already complete" and a host must
  never read a typo'd flag as a finished phase.
* **Exactly one machine-readable last stdout line per invocation** —
  ``MULTI_LLM_RESULT: {"mode","phase","state","exit","artifacts":[…],"next":…}``
  — emitted even on a crash, so the contract holds for a host that cannot parse
  prose or is tailing a detached log. ``next`` is ``null`` whenever no follow-up
  is owed, which is the normal case. Optional keys join these only when set;
  one of them, ``user_next_step``, is the workflow's next phase as a command for
  the *user* to type — never a follow-up for the caller, which is ``next``.
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

# Absolute, symlinks preserved — see utils/cli_common.py for why never realpath.
sys.path.insert(0, str(Path(os.path.abspath(__file__)).parent))

import modes as mode_table
from utils.cli_common import (
    CONTINUATION_VERBS,
    EXIT_ERROR,
    EXIT_NEEDS_HUMAN,
    EXIT_NOTHING_TO_DO,
    EXIT_OK,
    INTERNAL_FLAG_PREFIX,
    ResultContext,
    activate_result,
    clear_invocation,
    deactivate_result,
    dispatcher_command,
    flag_present,
    flag_value,
    invocation,
    invocation_plan_arg,
    record_error,
    record_invocation,
    render_instruction_text,
    skill_dir,
)
from utils.stream_bootstrap import bootstrap_streams
from utils.unattended import (
    NeedsHuman,
    require_uv,
    validate_decision_flags,
)

#: Above this many characters the ``ask`` question is handed over as a file
#: instead of an argv value. Well under the tightest real ceiling (Windows caps a
#: whole command line at 32767 chars; POSIX caps a single argument at 128 KiB),
#: because the same normalization feeds the detached-worker re-exec later.
MAX_ARGV_QUESTION_CHARS = 4096

#: The hidden re-entry flags this script reserves under the ``--internal-*``
#: prefix. Excluded from ``--help``, never rendered into a follow-up command or a
#: ``MULTI_LLM_RESULT.next`` value (see ``ResultContext.set_next``), and not part
#: of the compatibility surface. Targets own further ``--internal-*`` names of
#: their own (e.g. ``--internal-revalidation``), which is why the dispatcher
#: forwards the prefix rather than validating against this list.
INTERNAL_FLAGS: Tuple[str, ...] = tuple(
    INTERNAL_FLAG_PREFIX + name for name in ("reaggregate", "consolidate", "worker")
)


# ---------------------------------------------------------------------------
# The `util` namespace
# ---------------------------------------------------------------------------
# Utility scripts the instruction layer used to shell out to directly, routed the
# same in-process ``main(argv)`` way as the modes with flags forwarded verbatim to
# each script's existing parser. This is what makes "one substitution site per
# command" true rather than aspirational.
#
# `util` is NOT a user-facing surface: it is excluded from `argument-hint` and
# from `--help`'s mode list, documented only under `multi_llm.py util --help`,
# and — like `--internal-*` — never rendered into a MULTI_LLM_RESULT.next value.
UTIL_COMMANDS: Dict[str, Tuple[Optional[str], str, str]] = {
    "metrics": ("utils.metrics", "main", "Record/report per-subagent metrics in state.json."),
    "prior-changes": ("utils.prior_changes", "main", "Read, append to or clear the prior-batch change log."),
    "report": ("utils.html_report_generator", "main", "Regenerate an HTML review report with decisions overlaid."),
    "decisions": ("display_decisions", "main", "Print the decision summary from an orchestrator output file."),
    "update-tasks": ("update_plan_tasks", "main", "Write generated tasks into a plan's Tasks section."),
    "prereq": ("check_workflow_prerequisites", "main", "Check, skip or report a workflow phase's prerequisites."),
    "finalize-tracking": ("finalize_tracking", "main",
                          "Record the files implementation changed, and link the "
                          "summary from the plan."),
    "backup": ("utils.backup", "main", "Back up a file before it is modified."),
    "restore-batch": ("utils.restore_batch", "main",
                      "Restore a failed write batch from its pre-batch snapshot."),
    "runs": ("utils.run_registry", "main", "List (or --sweep) this project's detached runs."),
    "report-check": ("utils.report_check", "main",
                     "Check a turn's final message copies the printed next "
                     "command (Claude Code Stop hook)."),
    "wakeup-check": ("utils.wakeup_check", "main",
                     "Refuse a scheduled wakeup or cron job while a phase "
                     "runs (Claude Code PreToolUse hook)."),
    "next-command": ("utils.next_phase", "main",
                     "Print a plan's next workflow command (read-only; "
                     "--after <mode>, --host <id>)."),
    "improve-steps": ("utils.improve_steps", "main",
                      "Plan an --improve-plan/--improve-code/--improve-commits "
                      "run: each step's decision and flags (read-only; the "
                      "native leg's planner)."),
    "commit-brief": ("utils.commit_review", "commit_brief_main",
                     "Resolve a commit range, print its commit block and write "
                     "or reuse its commit brief (a commit mode's preparation, "
                     "launching nothing)."),
    "check-tasks": ("utils.tasks_graph_check", "main",
                    "Report inconsistencies in a tasks.md's task graph (advisory)."),
    "check-reply": ("utils.check_reply", "main",
                    "Check the replies persisted for a task file's batches "
                    "parse and cover their groups."),
    "write-prompt": ("utils.write_prompt", "main",
                     "Write one write batch's prompt, prior-batch context "
                     "bound now and the result contract appended."),
    "batch-done": ("utils.batch_done", "main",
                   "Record one write batch's outcome in state.json (the "
                   "native leg's per-batch progress record)."),
    "instructions": (None, "", "Print a mode's core instruction file with every path resolved."),
}

#: The ``util`` command that is a commit front door's steps 1 to 6 on their
#: own (plans/review-commits.md §2.8): the native leg's preparation entrypoint.
COMMIT_BRIEF_UTIL = "commit-brief"


#: The instruction-refactor escape hatch. Set to ``1`` and ``util instructions``
#: serves the frozen pre-refactor core from ``legacy/`` instead of the host-neutral
#: one — a way back from the ~5k-line markdown rewrite that does **not** revert the
#: dispatcher, the executor or the unattended work with it. Read path only: same
#: modes, same flags, same exit codes. See ``legacy/README.md``.
LEGACY_INSTRUCTIONS_ENV = "MULTI_LLM_LEGACY_INSTRUCTIONS"

#: Where the frozen copies live, relative to the skill root.
LEGACY_INSTRUCTIONS_DIR = "legacy"


def _legacy_instruction_path(relative: str) -> Optional[Path]:
    """The frozen pre-refactor file for *relative*, when the hatch is open.

    ``None`` when the variable is unset (the overwhelmingly common case, and the
    only one that costs nothing) or when no frozen copy exists for that mode —
    a partial legacy tree falls back to the current core rather than failing,
    because the hatch is a mitigation and must not become a new failure mode.
    """
    if os.environ.get(LEGACY_INSTRUCTIONS_ENV) != "1":
        return None
    candidate = skill_dir() / LEGACY_INSTRUCTIONS_DIR / relative
    return candidate if candidate.exists() else None


class DispatchError(Exception):
    """A dispatcher-owned failure that maps to a fixed exit code."""

    def __init__(self, message: str, exit_code: int = EXIT_NEEDS_HUMAN):
        super().__init__(message)
        self.exit_code = exit_code


# ---------------------------------------------------------------------------
# Help rendering (from modes.py — never a hand-maintained second list)
# ---------------------------------------------------------------------------

def render_help() -> str:
    lines = [
        "usage: multi_llm.py <mode> [<positional>...] [--host <id>] [mode flags...]",
        "",
        "Run a multi-llm workflow phase. The mode is a bare word and must come first;",
        "every flag after it is forwarded verbatim to that mode's own parser, so",
        "`multi_llm.py <mode> --help` prints the authoritative flag list.",
        "",
        "modes:",
    ]
    width = max(len(m.name) for m in mode_table.MODES)
    for mode in mode_table.MODES:
        positionals = " ".join(mode.positionals)
        head = f"  {mode.name.ljust(width)}  {positionals}".rstrip()
        lines.append(f"{head.ljust(width + 22)}{mode.summary}")
        if mode.unavailable:
            lines.append(f"  {''.ljust(width)}  ({mode.unavailable.format(mode=mode.name)})")
    lines += [
        "",
        "aliases:",
    ]
    for alias in sorted(mode_table.ALIASES):
        lines.append(f"  {alias} -> {mode_table.alias_expansion(alias)}")
    revs_modes = [m.name for m in mode_table.MODES if _takes_revs(m)]
    if revs_modes:
        import textwrap

        lines.append("")
        lines += textwrap.wrap(
            f"The commit modes ({', '.join(revs_modes)}) take an optional "
            f"{mode_table.POS_REVS}, HEAD (the last commit) when omitted: git "
            "revision syntax (A..B, A...B, a commit), one phrase (last 2 "
            "commits, -2, this branch, since <rev>, last two days), a commit "
            "brief's path, or the pinned <base12>..<head12> a run printed. "
            "Its words are joined, so it needs no quotes; it goes right after "
            "the mode word, before any flag, and a run takes one range.",
            width=78,
        )
    lines += [
        "",
        "cross-cutting flags (accepted by every mode, and by each orchestrator",
        "directly): --host ID, --yes/-y/--non-interactive, --interactive/-i,",
        "--detach, --if-not-running, --max-detached N, --exec-subagents,",
        "--skip-prerequisites.",
        "",
        "Unattended is the default everywhere except Claude Code: --yes resolves",
        "every gate from config and flags and renders no question, --interactive",
        "is the opt-in to a rendered gate, and the two together are exit 3 (never",
        "a precedence rule). --yes never implies --skip-prerequisites.",
        "",
        "--detach self-daemonizes the long-running modes "
        f"({', '.join(mode_table.DETACH_MODES)}):",
        "it implies --yes, returns immediately with a log path plus a status",
        "command, and is stopped only by `status <plan> --abort`. Never wrap it in",
        "a host background primitive — pick one mechanism.",
        "",
        "exit codes: 0 done | 1 unexpected error | 2 nothing to do / phase already",
        "complete | 3 needs a human (an unattended run that cannot proceed:",
        "missing uv, unmet prerequisite, contradictory or empty decision flag, or",
        "a command line a parser refused).",
        "",
        "Every invocation ends with one machine-readable line:",
        '  MULTI_LLM_RESULT: {"mode","phase","state","exit","artifacts":[...],"next":...}',
        "Optional keys join these only when set. One is `user_next_step`: the",
        "workflow's next phase as a command for the user to type, never a",
        "follow-up for the caller (that is `next`).",
        "",
        "Utility scripts live under a separate namespace: `multi_llm.py util --help`.",
    ]
    return "\n".join(lines)


def render_util_help() -> str:
    lines = [
        "usage: multi_llm.py util <command> [flags...]",
        "",
        "Utility scripts, routed in-process with flags forwarded verbatim to each",
        "script's own parser. Not a user-facing surface: `util` never appears in the",
        "skill's argument-hint, in `multi_llm.py --help`'s mode list, or in a",
        "MULTI_LLM_RESULT.next value.",
        "",
        "commands:",
    ]
    width = max(len(name) for name in UTIL_COMMANDS)
    for name, (_module, _attr, summary) in UTIL_COMMANDS.items():
        lines.append(f"  {name.ljust(width)}  {summary}")
    lines += [
        "",
        "`util instructions <mode>` prints instructions/<mode>.md with every",
        "skill-dir placeholder replaced by the running skill dir, so the text a host",
        "agent reads contains no unexpanded token.",
        "",
        "`util next-command <plan> [--after <mode>] [--host <id>]` prints the",
        "workflow's next phase as the next-command block (or the workflow-complete",
        "line) and sets MULTI_LLM_RESULT.user_next_step: a command for the user to",
        "type, never a follow-up for the caller. It reads state.json as recorded.",
        "",
        "`util improve-steps <plan> --mode improve-plan|improve-code|improve-commits [flags...]`",
        "prints the steps a native --improve-plan, --improve-code or --improve-commits",
        "run takes, each step's run/skip decision and its exact flags, and the command",
        "that continues the run; exit 2 with [ALREADY_COMPLETE] when nothing is left",
        "to do. --json prints the same facts as one object. Read-only, like",
        "next-command. An --improve-commits run names the commit brief as its plan.",
        "",
        "`util commit-brief [<range>] [--focus \"<text>\"] [--context-plan <path>]",
        "[flags...]` takes the tokens a commit mode was typed with, range words",
        "included: it resolves the range, prints the commit block, writes or reuses",
        "the commit brief and records the range, then prints [COMMIT_BRIEF] <path>",
        "and [COMMIT_REMAINING_FLAGS] <the tokens it did not consume>. It launches",
        "nothing: the native leg's preparation before `util improve-steps <brief>`.",
    ]
    return "\n".join(lines)


def _unknown_mode_message(word: str) -> str:
    return (
        f"ERROR: unknown mode '{word}'.\n"
        f"Valid modes: {', '.join(mode_table.mode_names())}\n"
        f"Aliases: "
        + ", ".join(f"{a}={t}" for a, t in sorted(mode_table.ALIASES.items()))
        + "\nRun `multi_llm.py --help` for the full grammar."
    )


# ---------------------------------------------------------------------------
# Grammar
# ---------------------------------------------------------------------------

#: A ``-N`` range word (plans/review-commits.md §2.2): a hyphen and ASCII
#: digits, nothing else. ``-h``, ``-2h``, ``--2``, ``-2.5`` and a lone ``-``
#: are not one; they end the leading run as any flag does.
_RANGE_COUNT_WORD = re.compile(r"-[0-9]+")

#: What a commit brief's path ends in (:func:`_names_a_commit_brief` asks no
#: other word). Its one spelling: the generated CLI surface reads it as
#: ``revs.brief_suffix``, so a server keeps a ``revs`` value ending in it as
#: one argv element and a brief path holding a space reaches this dispatcher
#: as the one word it turns into ``--plan-file``.
_COMMIT_BRIEF_SUFFIX = ".md"


def _takes_revs(mode: Optional["mode_table.Mode"]) -> bool:
    """Whether *mode* takes the commit modes' range (``POS_REVS``)."""
    return mode is not None and mode_table.POS_REVS in mode.positionals


def _split_positionals(
    rest: Sequence[str], mode: Optional["mode_table.Mode"] = None,
) -> Tuple[List[str], List[str]]:
    """Leading bare words are positionals; everything from the first flag on is
    forwarded verbatim.

    Deliberately not argparse: ``parse_known_args`` can reorder or swallow the
    residual argv, and the residual has to reach the target's own parser exactly
    as the user typed it.

    On a mode that takes a range (``POS_REVS``), a token that fully matches
    ``-[0-9]+`` continues the leading run instead of ending it: ``-2`` is the
    range ``last 2``, never a flag. Only the leading run is scanned, so in
    ``--review-commits --quick -2`` the ``-2`` is forwarded as typed (the front
    door refuses it as a range word after a flag), and every other mode splits
    as it always has: ``--review-code -2`` forwards ``-2``. This is the one
    place that decides what is positional, and it runs before any parser.
    """
    revs = _takes_revs(mode)
    index = 0
    while index < len(rest):
        token = rest[index]
        if token.startswith("-") and not (revs and _RANGE_COUNT_WORD.fullmatch(token)):
            break
        index += 1
    return list(rest[:index]), list(rest[index:])


def _normalize_positionals(
    mode: "mode_table.Mode",
    positionals: Sequence[str],
    cleanup: List[Path],
) -> List[str]:
    """Turn a mode's positionals into the flags its target already parses."""
    if _takes_revs(mode):
        # Ahead of the length check: `last 2 commits` is three words for the
        # range's one slot, and the extra-positional error never fires on a
        # commit mode (the range grammar is what refuses a bad range).
        return _revs_flags(positionals)
    if len(positionals) > len(mode.positionals):
        expected = " ".join(mode.positionals) or "(none)"
        raise DispatchError(
            f"ERROR: mode '{mode.name}' takes {len(mode.positionals)} positional "
            f"argument(s) {expected}, got {len(positionals)}: "
            f"{' '.join(positionals)}\n"
            "Flags must follow the positionals; an extra positional is never "
            "silently dropped."
        )

    normalized: List[str] = []
    for kind, value in zip(mode.positionals, positionals):
        if kind == mode_table.POS_PLAN:
            normalized += ["--plan-file", value]
        elif kind == mode_table.POS_QUESTION:
            normalized += _question_flags(value, cleanup)
        elif kind == mode_table.POS_HOST:
            # Forwarded verbatim as a positional: the install-host parser (and
            # with it the host-id vocabulary) is owned by the install design.
            normalized += [value]
        else:  # pragma: no cover - guarded by the table
            raise DispatchError(f"ERROR: unhandled positional kind {kind!r}")
    return normalized


def _revs_flags(words: Sequence[str]) -> List[str]:
    """The range words of a commit mode, as the flag its front door parses.

    Zero words emit nothing, which means ``HEAD``. One word that is a commit
    brief's path (:func:`_names_a_commit_brief`) becomes ``--plan-file``: a
    root range's pinned spelling, and the re-attach a tool route builds, name
    the brief. Anything else is joined with single spaces into one ``--revs``
    value, since revisions never contain spaces (``last 2 commits`` needs no
    quotes). So a markdown path is never a plan on these modes: a plan or a
    README goes to the range grammar, which refuses it naming
    ``--context-plan`` (plans/review-commits.md §2.2).
    """
    if not words:
        return []
    if len(words) == 1 and _names_a_commit_brief(words[0]):
        return ["--plan-file", words[0]]
    return ["--revs", " ".join(words)]


def _names_a_commit_brief(word: str) -> bool:
    """Whether *word* is a commit brief's path: it ends in
    :data:`_COMMIT_BRIEF_SUFFIX` (``.md``), names an existing file and
    ``commit_review.is_commit_brief`` accepts it.

    One helper decides what a brief is (its marker on line 1, or a
    ``<commit_reviews_dir>/<slug>.md`` path); this only finds the file. A
    relative path that names nothing from here but a file at the root of the
    repository the cwd is in is asked about there: a brief path spelled from
    the root and typed in a subdirectory then becomes ``--plan-file``, and
    :func:`_run_from_repository_root` moves the command to the root as it
    would for a plan (live run 11's shape).
    """
    if not word.endswith(_COMMIT_BRIEF_SUFFIX):
        return False
    from utils import commit_review

    if os.path.isfile(word):
        return bool(commit_review.is_commit_brief(word))
    root = _root_holding(word)
    if root is None:
        return False
    return bool(commit_review.is_commit_brief(os.path.join(root, word), cwd=root))


def _root_holding(path: str) -> Optional[str]:
    """The root of the repository the cwd is in, when relative *path* names a
    file there and stays inside it; else ``None``."""
    if not _relative([path]):
        return None
    try:
        from utils.git_utils import pin_repo_root

        root, problem = pin_repo_root(os.getcwd())
    except Exception:  # noqa: BLE001 - a convenience: the word stays a range
        return None
    if root is None or problem:
        return None
    candidate = os.path.join(root, path)
    if not (
        os.path.isfile(candidate)
        and _inside(os.path.normpath(candidate), root)
        and _inside(os.path.realpath(candidate), root)
    ):
        return None
    return root


#: The flags a commit front door synthesises for the phase it fronts, which a
#: user may never type there (plans/review-commits.md §2.1, "Flags the front
#: doors own"), each with the commit spelling that replaces it.
COMMIT_OWNED_FLAGS: Tuple[Tuple[str, str], ...] = (
    ("--plan-file",
     "there is no plan by default: the commit messages are the stated intent. "
     "Add a plan as read-only context with `--context-plan <path>`, or name a "
     "commit brief by its path as the range (`{door} <brief>`)."),
    ("--base-ref",
     "the range names its base: type it right after the mode word, before any "
     "flag, as `{door} C..HEAD` (the commits after C up to HEAD) or "
     "`{door} A..B`."),
    ("--head-ref",
     "the range names its end: type it right after the mode word, before any "
     "flag, as `{door} A..B` (the commits after A up to B)."),
)

#: The hidden flag a detached worker carries; its argv is the plugin's own.
_WORKER_FLAG = INTERNAL_FLAG_PREFIX + "worker"


def _reject_commit_owned_flags(door: str, tokens: Sequence[str]) -> None:
    """``[COMMIT_FLAG_CONFLICT] <flag>`` for a typed ``--plan-file``,
    ``--base-ref`` or ``--head-ref`` on a commit front door, exit 3.

    A front door synthesises all three for the phase it fronts, so a typed
    one would be overridden silently or win by argparse's last-one rule.
    Checked on the tokens as typed, before :func:`_normalize_positionals`
    turns a brief path into the door's own ``--plan-file``, so a root range's
    printed command (a commit mode and its brief path) passes, and before the
    front door's step 1, so nothing is written. An argparse abbreviation
    (``--plan``) is refused like the full spelling, as the parser would bind
    it. *door* is how the user names the command (``--review-commits``,
    ``util commit-brief``). A detached worker's argv is skipped by the
    caller: the plugin built it, and a root range's brief is already
    ``--plan-file`` there.
    """
    for token in tokens:
        if token == "--":
            return
        head = token.split("=", 1)[0]
        for flag, instead in COMMIT_OWNED_FLAGS:
            if not flag_present([head], flag):
                continue
            typed = "" if head == flag else f" (typed as {head})"
            marker = f"[COMMIT_FLAG_CONFLICT] {flag}{typed}"
            print(marker)
            reason = f"{door} takes no {flag}: {instead.format(door=door)}"
            record_error(f"{marker}: {reason}")
            raise DispatchError(f"ERROR: {reason}")


def _question_flags(question: str, cleanup: List[Path]) -> List[str]:
    """``--question`` for a short question, else a dispatcher-written file.

    ``ask_orchestrator.py`` already accepts ``--question-file``; writing it here
    keeps user-controlled free text off every command line, and keeps the
    decision out of the driving agent's hands.
    """
    if len(question) <= MAX_ARGV_QUESTION_CHARS:
        return ["--question", question]
    handle, path = tempfile.mkstemp(prefix="multi_llm_question_", suffix=".txt")
    with os.fdopen(handle, "w", encoding="utf-8") as stream:
        stream.write(question)
    cleanup.append(Path(path))
    return ["--question-file", path]


def _host_capabilities():
    """Import the capability reader lazily (one yaml parse, only when needed)."""
    from utils import host_capabilities

    return host_capabilities


def resolve_host(argv: Sequence[str]) -> str:
    """The host id this invocation runs under: ``--host`` → env → ``claude-code``.

    An omitted flag resolves to the reference host, so a command that predates the
    capability data behaves exactly as it did. Never sniffed: a host is *declared*
    (by the shim that baked the flag in, or by the user), never guessed from the
    environment.
    """
    return _host_capabilities().resolve_host_id(argv)


def _validate_host(argv: Sequence[str]) -> None:
    """An unknown ``--host`` is exit 3 before anything is created (D5b)."""
    caps = _host_capabilities()
    caps.entry(caps.resolve_host_id(argv))


def _reject_incompatible_flags(mode: "mode_table.Mode", argv: Sequence[str]) -> None:
    """Reject contradictory combinations at parse time, never by precedence.

    Enforced here — before any phase dir is touched — because the alternative is
    each mode guessing which flag wins.
    """
    unattended = flag_present(argv, "--yes", "-y", "--non-interactive")
    if unattended and flag_present(argv, "--interactive", "-i"):
        raise DispatchError(
            "ERROR: --yes (or --non-interactive) and --interactive are "
            "contradictory: one forbids prompting, the other forces it. "
            "Pass exactly one."
        )
    if unattended and flag_value(argv, "--force-strategy") == "pause-and-ask":
        raise DispatchError(
            "ERROR: --force-strategy pause-and-ask requires a human at the "
            "per-task gate, which --yes forbids. Pass a non-interactive "
            "strategy (e.g. skip-dependents) or drop --yes."
        )
    _reject_capability_conflicts(mode, argv)


def _reject_capability_conflicts(mode: "mode_table.Mode", argv: Sequence[str]) -> None:
    """The foreground-only gates ``--detach`` is incompatible with.

    A detached worker has ``stdin`` at ``DEVNULL`` and no channel back to the
    host, so anything that would raise a question is a contradiction — and it is
    rejected **at parse time, in the foreground invoker, before the process
    daemonizes**, so the user sees it on their own terminal instead of finding it
    in a log by polling. ``--detach`` therefore implies ``--yes`` (every decision
    point auto-resolves from the documented defaults and the resolution is
    recorded in ``.status.json``), and any flag whose resolution needs a human is
    exit 3.

    ``--exec-subagents`` is rejected the same way, from the capability data rather
    than from a guess here — but in ``_require_executor_capability`` below, which
    runs *after* the implications so ``--detach``'s implied flag is gated exactly
    like a typed one.
    """
    if not flag_present(argv, "--detach"):
        return None
    if flag_present(argv, "--interactive", "-i"):
        raise DispatchError(
            "ERROR: --detach and --interactive are contradictory: a detached run "
            "has no terminal to prompt on (stdin is /dev/null and there is no "
            "channel back to the host), so --detach implies --yes. Pass exactly "
            "one."
        )
    if flag_value(argv, "--force-strategy") == "pause-and-ask":
        raise DispatchError(
            "ERROR: --force-strategy pause-and-ask requires a human at the "
            "per-task gate, which --detach forbids (it implies --yes). Pass a "
            "non-interactive strategy (e.g. skip-dependents) or drop --detach."
        )
    if not mode.supports_detach:
        # A flag that silently does nothing is worse than a refusal: the caller
        # would poll `status` forever for a run that was never detached.
        raise DispatchError(
            f"ERROR: --detach is not available for mode '{mode.name}'.\n"
            "       It covers the long-running fan-out modes today: "
            f"{', '.join(mode_table.DETACH_MODES)}.\n"
            "       Run this mode in the foreground (it emits task JSON and "
            "exits in seconds) or under your host's own background mechanism."
        )
    return None


def _apply_flag_implications(argv: List[str]) -> List[str]:
    """Write ``--detach``'s implications out explicitly rather than leaving them.

    The detached child's argv is rebuilt from the invoker's, so an implication
    that stayed implicit would have to be re-derived in a second place. Making it
    explicit here means the worker's recorded argv says exactly what it ran with.

    Two implications, both D4c's, and both about there being nobody on the other
    end: ``--yes`` because no one is there to *answer*, and ``--exec-subagents``
    because no one is there to *continue* — a detached worker without it would
    print ``[VALIDATION_PENDING]``/``[SALVAGE_NEEDED]`` and exit 0 with the phase
    unfinished, which a poller reads as ``run.state: done``, and the write phases
    would decline the scheduler outright.
    """
    if flag_present(argv, "--detach"):
        if not flag_present(argv, "--yes", "-y", "--non-interactive"):
            argv = list(argv) + ["--yes"]
        if not flag_present(argv, "--exec-subagents"):
            argv = list(argv) + ["--exec-subagents"]
    return argv


def _require_executor_capability(argv: Sequence[str]) -> None:
    """Gate ``--exec-subagents`` on the host's capability data (D3e/D5b).

    Called *after* ``_apply_flag_implications``, so the flag ``--detach`` implies
    is checked exactly like one the caller typed: a host whose entry declares no
    executor-capable runner (the ``agent-readonly``/``agent-write`` profiles)
    would otherwise accept the run, stop at a dispatch marker and wait for a
    subagent nobody starts.
    """
    if flag_present(argv, "--exec-subagents"):
        _host_capabilities().require_executor_runner(resolve_host(argv))


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

def _load_target(module_path: str, attr: str) -> Callable[[Sequence[str]], int]:
    """Import a dispatch target lazily and return its ``main``.

    Import must be side-effect free: every target keeps argparse and all work
    inside ``main(argv)`` so two targets can safely run inside one interpreter
    (see tests/test_instruction_portability.py).
    """
    import importlib

    module = importlib.import_module(module_path)
    target = getattr(module, attr, None)
    if target is None:  # pragma: no cover - guarded by the table + tests
        raise DispatchError(
            f"ERROR: {module_path} has no '{attr}' entry point.",
            exit_code=EXIT_ERROR,
        )
    return target


def _call_target(target: Callable[[Sequence[str]], int], argv: Sequence[str]) -> int:
    """Call ``main(argv)``, awaiting it when the target is async.

    An async target runs under ``sweeping_live_clis_on_interrupt``, so a Ctrl-C
    stops its fan-out's CLIs from inside the cancellation, before ``asyncio.run``
    joins the worker threads waiting on them (decision 11.9).
    """
    import asyncio
    import inspect

    if inspect.iscoroutinefunction(target):
        from utils import process_control

        result = asyncio.run(
            process_control.sweeping_live_clis_on_interrupt(target(list(argv)))
        )
    else:
        result = target(list(argv))
    return EXIT_OK if result is None else int(result)


def _validate_skip_rung(mode_name: str) -> None:
    """Reject a bad ``MULTI_LLM_CODEX_SKIP_RUNG`` before any mode runs (plan
    codex-sandbox-unavailable-findings-and-fixes §6 F1 "Where it sits" item 6,
    2026-09-30): any value but ``plugin-landlock`` is exit 3 naming the
    variable and the accepted value, never silently ignored. ``doctor`` is
    exempt — it is where a user looks when something is wrong, so it reports
    the bad value on its ``plugin-landlock`` row instead of dying on it."""
    if mode_name == "doctor":
        return
    from utils.providers.base import skip_rung_requested

    try:
        skip_rung_requested()
    except ValueError as exc:
        raise DispatchError(f"ERROR: {exc}") from exc


def _run_mode(word: str, rest: Sequence[str], ctx: ResultContext) -> int:
    mode = mode_table.resolve(word)
    if mode is None:
        raise DispatchError(_unknown_mode_message(word))

    ctx.mode = mode.name
    ctx.phase = mode.phase

    if mode.unavailable:
        if flag_present(rest, "--help", "-h"):
            print(f"{mode.name}: {mode.summary}")
            print(f"  {mode.unavailable.format(mode=mode.name)}")
            return EXIT_OK
        raise DispatchError(
            f"ERROR: mode '{mode.name}' is {mode.unavailable.format(mode=mode.name)}."
        )

    assert mode.target_module is not None  # every available mode has a target
    cleanup: List[Path] = []
    try:
        positionals, flags = _split_positionals(rest, mode)
        if flag_present(flags, "--help", "-h"):
            # Forward to the target's own parser: it is the source of truth.
            return _call_target(
                _load_target(mode.target_module, mode.target_attr), list(flags)
            )
        # The host id first: every rejection below may consult its capability
        # entry, and an unknown id must fail as itself rather than as a confusing
        # consequence.
        _validate_host(flags)
        if _takes_revs(mode) and not flag_present(flags, _WORKER_FLAG):
            # On the tokens as typed, before the brief path becomes the
            # door's own `--plan-file` below.
            _reject_commit_owned_flags(f"--{mode.name}", flags)
        _reject_incompatible_flags(mode, flags)
        # D6 row 15 then row 1, both before anything is created: an empty or
        # unrecognized decision value and a missing `uv` are the two failures a
        # mode must never discover halfway through a phase dir.
        validate_decision_flags(flags)
        _validate_skip_rung(mode.name)
        if mode.requires_uv:
            # The two install modes opt out (modes.py): `install-host --check` is
            # layer 1 of the same uv bootstrap and reports a miss as one of its
            # five assertions, and `uninstall-host` must work on a machine whose
            # uv is already gone. Every other mode fails here, before anything is
            # created.
            require_uv()
        argv = (
            list(mode.injected_flags)
            + list(mode_table.alias_flags(word))
            + _normalize_positionals(mode, positionals, cleanup)
            + list(flags)
        )
        argv = _apply_flag_implications(argv)
        # After the implications: --detach's implied --exec-subagents faces the
        # same capability gate as an explicit one, so a host with no executor-
        # capable runner is exit 3 here rather than a marker nobody continues.
        _require_executor_capability(argv)
        # A plan spelled from the repository root, typed in a subdirectory of
        # it (live run 11): the whole command runs from the root, before
        # anything reads a path or records the invocation.
        _run_from_repository_root(
            [flag_value(argv, option) for option in _MODE_INPUT_PATH_OPTIONS],
            [flag_value(argv, option) for option in _MODE_OUTPUT_PATH_OPTIONS],
        )
        # What a detached child re-executes: the mode word plus this normalized
        # argv, never a remembered sys.argv (see utils/detach.build_child_command).
        # A continuation also carries the plan spelling its hand-off recorded.
        record_invocation(
            mode.name, argv, plan_arg=_continued_plan_arg(mode, argv)
        )
        return _call_target(
            _load_target(mode.target_module, mode.target_attr), argv
        )
    finally:
        for path in cleanup:
            try:
                path.unlink()
            except OSError:  # pragma: no cover - best-effort cleanup
                pass


def _run_util(rest: Sequence[str], ctx: ResultContext) -> int:
    ctx.mode = mode_table.UTIL_NAMESPACE
    if not rest or rest[0] in ("--help", "-h"):
        print(render_util_help())
        return EXIT_OK
    name, args = rest[0], list(rest[1:])
    if name not in UTIL_COMMANDS:
        raise DispatchError(
            f"ERROR: unknown util command '{name}'.\n"
            f"Valid commands: {', '.join(UTIL_COMMANDS)}\n"
            "Run `multi_llm.py util --help` for details."
        )
    ctx.mode = f"{mode_table.UTIL_NAMESPACE} {name}"
    if name == "instructions":
        return _run_util_instructions(args, ctx)
    module_path, attr, _summary = UTIL_COMMANDS[name]
    assert module_path is not None
    if name == COMMIT_BRIEF_UTIL and not flag_present(args, "--help", "-h"):
        # The front doors' preparation half takes the same typed tokens, so
        # it refuses the same three flags (plans/review-commits.md §2.8).
        _reject_commit_owned_flags(
            f"{mode_table.UTIL_NAMESPACE} {COMMIT_BRIEF_UTIL}", args)
    if not flag_present(args, "--help", "-h"):
        _run_from_repository_root(
            _util_input_paths(name, args),
            [flag_value(args, option) for option in _UTIL_OUTPUT_PATH_OPTIONS],
        )
    return _call_target(_load_target(module_path, attr), args)


# ---------------------------------------------------------------------------
# A command run from a subdirectory of the repository
# ---------------------------------------------------------------------------
# Live run 11 (Claude Code racing 03, 2026-10-08): the host had `cd`'d into the
# phase folder to look at its files, then ran `generate-tasks
# plans/racing-game.md --reaggregate` there, and the plan "was not found" at
# plans/racing-game/generate-tasks/plans/racing-game.md. Every path a workflow
# command names (the plan, its folder, state.json, a phase folder, tasks.md) is
# spelled from the repository root, so when the relative ones name nothing from
# the cwd and each names something inside the root of the repository the cwd is
# in, the command runs from that root, exactly as it would have there, and says
# so on one line.

#: A mode's options whose value is an existing file the command reads (a plan
#: positional is ``--plan-file`` by now, and so is a commit brief's path; a
#: commit mode's ``--context-plan`` is a plan read as context, and the hidden
#: ``--commit-stage`` the staged header a detached worker applies).
_MODE_INPUT_PATH_OPTIONS: Tuple[str, ...] = (
    "--plan-file", "--question-file", "--tasks-file", "--files-from",
    "--context-plan", "--commit-stage",
)

#: A mode's options whose value is a path the command creates, so it need not
#: exist yet (fix round 27, the Fable review of round 26: review-plan's
#: ``--out-dir`` was read by nothing, so ``--out-dir out`` beside a ``sub/out``
#: moved with the plan and wrote ``<root>/out``): review-plan's output folder
#: and implement's task JSON. ``--files`` and ``--touched`` are
#: repository-relative wherever they are typed, and init's ``--dir`` is its
#: target as typed; none of them is read here.
_MODE_OUTPUT_PATH_OPTIONS: Tuple[str, ...] = ("--out-dir", "--output")

#: A ``util`` command's options whose value names something the workflow keeps
#: in the repository (``--output-file`` is the orchestrator output
#: ``util decisions`` reads, and ``--output-dir`` the plan folder
#: ``prior-changes`` reads and appends to; ``--files-from`` is the scope list
#: ``improve-steps`` reads, as the mode route reads review-code's;
#: ``--context-plan`` is the plan ``commit-brief`` reads as context).
_UTIL_INPUT_PATH_OPTIONS: Tuple[str, ...] = (
    "--plan-file", "--state-file", "--phase-dir", "--output-dir", "--tasks-file",
    "--output-file", "--project-root", "--files-from", "--context-plan",
)

#: A ``util`` command's options whose value is a path it creates:
#: ``write-prompt``'s prompt file (fix round 27).
_UTIL_OUTPUT_PATH_OPTIONS: Tuple[str, ...] = ("--output",)

#: The ``util`` commands whose first positional is such a path, with their
#: options that take a value (whose value is not that positional).
_UTIL_PATH_POSITIONAL: Dict[str, Tuple[str, ...]] = {
    "next-command": ("--after", "--blocked", "--host"),
    "improve-steps": ("--mode", "--host", "--models", "--files", "--files-from",
                      "--base-ref", "--head-ref", "--max-detached",
                      "--internal-run-id"),
    "check-tasks": (),
    "backup": (),
}

#: Of those options, the ones that take one or more values (``nargs="+"``):
#: argparse hands such an option every token up to the next option, so none
#: of them is the positional (``util improve-steps --models m1 m2 --mode
#: improve-plan <plan>`` names the plan last, not ``m2``).
_UTIL_VARIADIC_OPTIONS: Dict[str, Tuple[str, ...]] = {
    "improve-steps": ("--models",),
}

#: The cwd :func:`_run_from_repository_root` moved away from, which ``main``
#: moves back to on its way out (an in-process caller keeps its own cwd).
_CWD_BEFORE_ROOT: List[str] = []


def _is_option_token(token: str) -> bool:
    return token.startswith("-") and token != "-"


def _first_positional(
    args: Sequence[str], value_options: Sequence[str],
    variadic_options: Sequence[str] = (),
) -> Optional[str]:
    index = 0
    while index < len(args):
        token = args[index]
        if token == "--":
            return args[index + 1] if index + 1 < len(args) else None
        if _is_option_token(token):
            index += 1
            if "=" in token:
                continue
            if token in variadic_options:
                while index < len(args) and not _is_option_token(args[index]):
                    index += 1
            elif token in value_options:
                index += 1
            continue
        return token
    return None


def _util_input_paths(name: str, args: Sequence[str]) -> List[Optional[str]]:
    paths = [flag_value(args, option) for option in _UTIL_INPUT_PATH_OPTIONS]
    if name in _UTIL_PATH_POSITIONAL:
        paths.append(_first_positional(
            args, _UTIL_PATH_POSITIONAL[name], _UTIL_VARIADIC_OPTIONS.get(name, ()),
        ))
    return paths


def _inside(path: str, root: str) -> bool:
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


def _relative(paths: Sequence[Optional[str]]) -> List[str]:
    return [
        path for path in paths
        if path and path != "-" and not path.startswith("~") and not os.path.isabs(path)
    ]


def _names_something_here(output: str) -> bool:
    """Whether an output path, or the first folder it names, exists from the
    cwd: then it is spelled from here (``out/new`` beside an ``out``, ``..``)."""
    first = os.path.normpath(output).split(os.sep, 1)[0]
    return os.path.lexists(output) or os.path.lexists(first)


def _run_from_repository_root(
    paths: Sequence[Optional[str]], outputs: Sequence[Optional[str]] = (),
) -> None:
    """Move to the repository root when the command's relative paths name
    nothing from here and each names something inside that root.

    The root is the one the write path pins (``git_utils.pin_repo_root``: the
    nearest ``.git`` entry above the cwd, which git must confirm; nothing is
    pinned while ``GIT_DIR`` and the like redirect git). Nothing moves when no
    path is relative, when any of them names something from the cwd (so a
    spelling that works here keeps working, and a mixed one is not guessed at),
    when the cwd is the root already, or when a path is missing from the root
    too or resolves outside it (a ``..`` or a link out of the repository).

    *outputs* are paths the command creates (fix round 27): one need not
    exist at the root, but it keeps the command here when it, or the first
    folder it names, exists from the cwd, and it must stay inside the root as
    spelled and resolved. Outputs alone never move a command: only a path it
    reads says it was spelled from the root.
    """
    relative = _relative(paths)
    made = _relative(outputs)
    if (
        not relative
        or any(os.path.lexists(path) for path in relative)
        or any(_names_something_here(path) for path in made)
    ):
        return
    try:
        cwd = os.getcwd()
        from utils.git_utils import pin_repo_root

        root, problem = pin_repo_root(cwd)
    except Exception:  # noqa: BLE001 - a convenience: the command runs as typed
        return
    if root is None or problem or os.path.realpath(cwd) == root:
        return
    for path in relative + made:
        candidate = os.path.join(root, path)
        if not (
            (path in made or os.path.exists(candidate))
            and _inside(os.path.normpath(candidate), root)
            and _inside(os.path.realpath(candidate), root)
        ):
            return
    os.chdir(root)
    _CWD_BEFORE_ROOT.append(cwd)
    # Fix round 27: on the result line too, so a tool server names the plan
    # the way this command reads it, never by a `.git` walk of its own.
    from utils.cli_common import record_ran_from_root

    record_ran_from_root(root)
    print(
        f"multi-llm: running from the repository root {root}, where "
        f"{relative[0]} is (it is not under the current directory {cwd}).",
        file=sys.stderr,
    )


def _back_to_the_callers_cwd() -> None:
    if not _CWD_BEFORE_ROOT:
        return
    cwd = _CWD_BEFORE_ROOT[0]
    del _CWD_BEFORE_ROOT[:]
    try:
        os.chdir(cwd)
    except OSError:  # pragma: no cover - the folder went away meanwhile
        pass


def _run_util_instructions(args: Sequence[str], ctx: ResultContext) -> int:
    """Serve a mode's core instruction file with every placeholder resolved.

    The instruction markdown is static and no installer rewrites it, so a host
    that reads the file directly would have to apply the skill-dir binding by
    hand — an instruction-following step across a 5k-line corpus. Serving the
    rendered text from ``__file__`` removes that step and cannot go stale.
    """
    if not args or args[0] in ("--help", "-h"):
        served = [m.name for m in mode_table.MODES if m.instruction_file]
        print("usage: multi_llm.py util instructions <mode> [--host <id>]")
        print(f"modes with a core instruction file: {', '.join(served)}")
        print(
            "  --host <id>  append this host's three resolved capability-verb "
            "sentences"
        )
        return EXIT_OK
    positional, host_id = _split_instructions_host(args)
    if len(positional) > 1:
        raise DispatchError(
            "ERROR: `util instructions` takes exactly one mode word, got: "
            + " ".join(positional)
        )
    if not positional:
        raise DispatchError(
            "ERROR: `util instructions` needs a mode word before --host."
        )
    word = positional[0]
    mode = mode_table.resolve(word)
    if mode is None:
        raise DispatchError(_unknown_mode_message(word))
    relative = mode_table.instruction_path(mode.name)
    if relative is None:
        # Dispatcher-driven by design (`status`, `install-host`,
        # `uninstall-host`): there is no workflow to narrate, only flags. Every
        # shim names this command as its unconditional read step, so erroring
        # here would hand a host agent a failure before it had done anything —
        # observed on OpenCode, where the agent had to improvise past an exit 3.
        # Answer with the one useful thing instead and exit 0; a mode that
        # *declares* a core file which is missing is still a hard error below.
        print(
            f"Mode '{mode.name}' has no core instruction file: it is driven "
            "entirely by the dispatcher, so there are no workflow steps to "
            "follow. Its flags are the whole interface:"
        )
        print()
        print(f"  {dispatcher_command(mode.name)} --help")
        if mode.name == "status":
            # 2026-10-04 (Claude Code racing re-run): a host reading `status`
            # only to report it showed "Exit code 2" as a tool error. The code
            # is the poll contract and never moves; the read step says so.
            print()
            print(
                "Read its output, not its exit code: exit code 2 is not a "
                "failure — it means no run is recorded (every phase a host ran "
                "in the foreground) or one is still running, the poll "
                "contract; 0 and 3 are a finished run's verdict, and only 1 is "
                "an error (the phase dir could not be read). To report it to "
                "the user on a host that shows any non-zero exit as an error, "
                "add --exit-zero: the call then exits 0 whenever the status was "
                "read, and the run's state is still in its text. Keep that flag "
                "off a poll whose loop reads the exit code."
            )
        # The end marker is unconditional across `util instructions`, so "search
        # for the end line" is a rule with no exception for a reader to hold. This
        # branch's answer is a few hundred characters and can never be truncated;
        # it carries the marker anyway, because a check that is sometimes
        # inapplicable is a check an agent has to decide about.
        print(f"{CORE_END_MARKER} {mode.name}")
        return EXIT_OK
    path = skill_dir() / relative
    legacy = _legacy_instruction_path(relative)
    if legacy is not None:
        # Announced on stderr, never stdout: `util instructions` writes the core
        # itself to stdout and a host may be piping it straight into a prompt.
        print(
            f"[LEGACY_INSTRUCTIONS] serving the pre-refactor core from "
            f"{legacy.parent.name}/{legacy.name} because "
            f"{LEGACY_INSTRUCTIONS_ENV}=1 (see legacy/README.md; Claude Code "
            "only, frozen, unmaintained).",
            file=sys.stderr,
        )
        path = legacy
    if not path.exists():
        raise DispatchError(
            f"ERROR: core instruction file missing: {path}\n"
            "The plugin install looks corrupt or partial; reinstall the skill.",
            exit_code=EXIT_ERROR,
        )
    core = render_instruction_text(path.read_text(encoding="utf-8"), skill_dir())
    sys.stdout.write(_truncation_notice(mode.name, core))
    sys.stdout.write(core)
    if not core.endswith("\n"):
        sys.stdout.write("\n")
    # The sentinel closes the *core*, before the optional verb appendix, because
    # `--host` has always appended to an unchanged core and a marker that moved
    # depending on the flag would be a second thing to reason about. Every shim
    # host runs the plain form, where this is the last line of content.
    sys.stdout.write(f"{CORE_END_MARKER} {mode.name}\n")
    if host_id is not None:
        sys.stdout.write(_verb_section(host_id))
    ctx.add_artifact(path)
    return EXIT_OK


#: Closes the served core. Its whole job is to be *checkable*: an agent does not
#: have to judge whether it received the whole document, it searches for a literal
#: string. Never printed anywhere else, so a match means the tail arrived.
CORE_END_MARKER = "MULTI_LLM_CORE_END:"

#: How :func:`_truncation_notice`'s head banner opens. A constant rather than
#: a literal inside the banner because a package route's server reads the
#: ``util instructions`` stdout through a pipe and *drops* the banner before it
#: attaches the runbook (its character count describes the unscrubbed core):
#: it finds the banner by this prefix, read off the generated surface, never
#: by a spelling of its own.
TRUNCATION_BANNER_OPENING = "=== READ THIS FIRST"


def _truncation_notice(mode_name: str, core: str) -> str:
    """The head banner that survives a host truncating this command's output.

    MEASURED, not hypothetical. Claude Code persists any Bash result over ~30 000
    characters to a file and replaces it with a ~2.2 KB stub: a pointer line plus
    the output's **first 2 KB** and nothing else. Seven of the eleven cores are
    over that cap. On 2026-09-22 an `apply-suggestions` row read that stub, did not
    follow the pointer, never saw the per-batch loop that lives in the second half,
    and finished the turn reporting four batches applied with zero edits made.

    Two facts decide the shape. The surviving region is the **head**, so a footer
    would be the first thing lost — a notice can only live here. And the host's own
    stub already names the byte count and the path, and was ignored; so this does
    not repeat the pointer, it gives the reader a *test* — one literal string, at a
    known place — that turns "did I get all of it?" from a judgement into a lookup.
    """
    return (
        f"{TRUNCATION_BANNER_OPENING} · multi-llm core instructions · "
        f"{mode_name} ===\n"
        f"The core below is {len(core):,} characters. Its last line is exactly:\n"
        "\n"
        f"    {CORE_END_MARKER} {mode_name}\n"
        "\n"
        "Search what you just received for that line. If it is not there, your host\n"
        "truncated this command's output and saved the whole of it to a file; the\n"
        "host's own wrapper around this text names that file's path. Stop there:\n"
        "read that file to the end before your next tool call and follow it, not\n"
        "this excerpt.\n"
        "\n"
        "Truncation keeps the head and drops the tail. The head is what the mode is\n"
        "and how it is invoked; the tail is the loop that does the work. So a cut\n"
        "core reads like a complete overview, and the usage line you can still see\n"
        "runs cleanly — it starts the orchestrator, which reports success, and you\n"
        "end the turn having applied nothing. Do not run any command from a core\n"
        "you have not seen the end of.\n"
        "=== the core begins on the next line ===\n"
    )


#: Heading the ``--host`` verb block is served under. The core files name the
#: three capability verbs abstractly and it has always been the *shim's* section 4
#: that resolved them; a host with no prose left to carry that section — the
#: OpenCode npm plugin, whose command body is one line — needs the resolution to
#: arrive with the core instead. Same single owner either way:
#: ``caps.verb_block()``.
_VERB_HEADING = "## Capability verbs — how this host answers each one"


def _verb_section(host_id: str) -> str:
    """The three resolved verb sentences, as the section a shim used to carry."""
    from utils import host_capabilities as caps

    return (
        f"\n{_VERB_HEADING}\n\n"
        "The core above names three capability verbs and never a tool. These are "
        "their one concrete resolution here, so nothing is left to decide "
        f"mid-run:\n\n{caps.verb_block(host_id)}\n"
    )


def _split_instructions_host(
    args: Sequence[str],
) -> "tuple[list[str], Optional[str]]":
    """Split ``util instructions`` argv into positionals and a ``--host`` value.

    Hand-parsed rather than argparse'd because this command's whole contract is
    that its stdout **is** the core text: an argparse error would print a usage
    block a host may be piping straight into a prompt, and the surrounding
    dispatcher already owns the exit-3 wording for a bad argument.
    """
    positional: list = []
    host_id: Optional[str] = None
    index = 0
    while index < len(args):
        token = args[index]
        head, separator, inline = token.partition("=")
        if head == "--host":
            if separator:
                value = inline
            else:
                index += 1
                if index >= len(args):
                    raise DispatchError(
                        "ERROR: `util instructions --host` needs a host id."
                    )
                value = args[index]
            if not value:
                raise DispatchError(
                    "ERROR: `util instructions --host` needs a host id."
                )
            host_id = value
        elif token.startswith("-"):
            raise DispatchError(
                f"ERROR: `util instructions` does not take {token!r}. Its only "
                "option is `--host <id>`."
            )
        else:
            positional.append(token)
        index += 1
    return positional, host_id


def _dispatch(argv: Sequence[str], ctx: ResultContext) -> int:
    if not argv:
        raise DispatchError(
            "ERROR: no mode given. The mode is a bare word and must be the first "
            f"argument.\nValid modes: {', '.join(mode_table.mode_names())}\n"
            "Run `multi_llm.py --help` for the full grammar."
        )
    word = argv[0]
    if word in ("--help", "-h", "help"):
        print(render_help())
        return EXIT_OK
    if word == mode_table.UTIL_NAMESPACE:
        return _run_util(argv[1:], ctx)
    if word.startswith("-"):
        raise DispatchError(
            f"ERROR: '{word}' is not a mode. The mode is a bare word and must be "
            "the first argument (e.g. `multi_llm.py review-plan plans/x.md "
            f"{word}`).\n" + _unknown_mode_message(word)
        )
    return _run_mode(word, argv[1:], ctx)


def _exit_code_of(exc: SystemExit) -> int:
    """A target's ``sys.exit`` is its return value; never remap 0/1/2/3.

    The one exception is argparse's usage exit — see ``_is_argparse_usage_exit``,
    which the caller consults; that code was never the target's to spend.
    """
    code = exc.code
    if code is None:
        return EXIT_OK
    if isinstance(code, int):
        return code
    print(str(code), file=sys.stderr)
    return EXIT_ERROR


def _is_argparse_usage_exit(exc: SystemExit) -> bool:
    """True when this ``SystemExit`` came out of argparse's usage-error path.

    ``ArgumentParser.error`` exits **2**, which is the one code this skill has
    already spent: 2 means "nothing to do / phase already complete" (the
    orchestrators' phase-complete guards, which raise it with a plain
    ``sys.exit(2)``). Passing argparse's 2 through would put
    ``state: nothing-to-do`` on the MULTI_LLM_RESULT line for a typo'd flag or a
    missing ``--plan-file``, and a host reading only the machine contract would
    conclude the phase was done and skip it — the worst possible reading of a
    command that never ran.

    The two are distinguishable only by origin, so the traceback is the
    discriminator: argparse raises from its own module frames, a phase guard from
    the orchestrator's. Matching on frames rather than on the message keeps this
    independent of argparse's (localized, version-dependent) wording.
    """
    tb = exc.__traceback__
    while tb is not None:
        if tb.tb_frame.f_globals.get("__name__") == "argparse":
            return True
        tb = tb.tb_next
    return False


def _sweep_live_clis_on_interrupt() -> None:
    """Stop every Lane A CLI still registered when Ctrl-C reached the dispatcher.

    A fan-out's slots wait on their CLIs from worker threads, where
    ``KeyboardInterrupt`` is never raised, and an agent CLI's tool shells run in
    sessions of their own that a terminal SIGINT does not reach (plan
    review-run-scope-salvage-and-failure-visibility D3.3, decision 11.9). The
    registry holds each live CLI with a refreshed snapshot of its descendants,
    so this reaps what those slots started before the process exits.

    The backstop, not the main path: an async target's fan-out is swept inside
    its own cancellation (``_call_target``), because by the time
    ``asyncio.run`` lets a ``KeyboardInterrupt`` reach this handler it has
    already joined every worker thread. What is left for here is a sync
    target's CLI. A no-op when nothing is registered, and it never raises: the
    interrupt's own exit and result line must still happen.
    """
    try:
        from utils import process_control
    except Exception as exc:  # noqa: BLE001 - see above
        print(f"[INTERRUPT_SWEEP] failed: {exc}", file=sys.stderr)
        return
    process_control.sweep_live_clis("INTERRUPT_SWEEP")


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if _WORKER_FLAG in argv:
        from utils.detach import prepare_worker_output

        prepare_worker_output()
    # Line buffering + UTF-8/replace stream encoding, once per invocation: there
    # is exactly one process per invocation, so this covers every mode and every
    # in-process continuation.
    bootstrap_streams()
    ctx = activate_result(ResultContext())
    crash: Optional[str] = None
    exit_code = EXIT_ERROR
    previous_sigterm = _install_foreground_sigterm()
    try:
        try:
            exit_code = _dispatch(argv, ctx)
        except DispatchError as exc:
            print(str(exc), file=sys.stderr)
            exit_code = exc.exit_code
        except NeedsHuman as exc:
            # Every unattended gate that cannot resolve lands here with the same
            # code, whether it was raised by the dispatcher's own pre-checks or
            # by the mode it dispatched to.
            print(exc.message, file=sys.stderr)
            ctx.state = "needs-human"
            exit_code = exc.exit_code
        except SystemExit as exc:
            exit_code = _exit_code_of(exc)
            if exit_code == EXIT_NOTHING_TO_DO and _is_argparse_usage_exit(exc):
                # A parser refused the command line: that is a broken invocation
                # a human has to retype, so it lands on exit 3 with every other
                # "cannot proceed" — never on 2, which the phase-complete guards
                # own. argparse has already named the offending token on stderr.
                print(
                    "ERROR: that command line did not parse (see the usage error "
                    "above). Fix the invocation and re-run.\nExit 3, not 2: exit 2 "
                    "is reserved for 'nothing to do / phase already complete', and "
                    "nothing about this phase ran.",
                    file=sys.stderr,
                )
                exit_code = EXIT_NEEDS_HUMAN
        except KeyboardInterrupt:
            print("\nInterrupted.", file=sys.stderr)
            _sweep_live_clis_on_interrupt()
            exit_code = EXIT_ERROR
        except Exception:
            # The machine-readable contract has to hold on a crash too, so the
            # traceback goes to stderr and the result line is still the last
            # stdout line before this returns 1.
            traceback.print_exc()
            crash = _crash_summary()
            exit_code = EXIT_ERROR
        try:
            _remember_plan_spelling(ctx)
        except Exception as exc:  # noqa: BLE001 - advisory, never the exit code
            print(
                f"multi-llm: could not save the plan path as you typed it ({exc}); "
                "the next command may name the plan by its absolute path.",
                file=sys.stderr,
            )
        try:
            _emit_user_next_step(ctx, exit_code)
        except Exception as exc:  # noqa: BLE001 - advisory, never the exit code
            from utils.next_phase import lookup_failure_line

            print(lookup_failure_line(exc), file=sys.stderr)
        ctx.emit(exit_code)
        return exit_code
    finally:
        # Plan codex-sandbox-unavailable I12 (option B, 2026-09-30): every codex
        # child of this run has exited by now, so remove the
        # `[projects."<repo>"] trust_level = "trusted"` tables they added to the
        # user's codex config — and nothing else. A detached worker's `--abort`
        # and heartbeat-lost endings `os._exit` without reaching this line, so
        # `utils/detach.py` restores on those two paths itself.
        _restore_codex_trust()
        _uninstall_foreground_sigterm(previous_sigterm)
        # If this process is a detached worker, it is the only thing that can
        # ever observe its own exit status (after the double-spawn nothing is its
        # parent), so it records its own outcome before exiting. A no-op in every
        # other invocation.
        _close_detached_run(exit_code, crash or ctx.error, ctx.state)
        deactivate_result()
        clear_invocation()
        _back_to_the_callers_cwd()


def _write_phases() -> "frozenset":
    """The phases whose batch loop is the invoker's without ``--exec-subagents``.

    From the executor's own table (``subagent_tasks.PHASE_BY_WRITE_KIND``, the
    mode/``state.json`` spelling), never a hand-kept list.
    """
    from utils.subagent_tasks import PHASE_BY_WRITE_KIND

    return frozenset(PHASE_BY_WRITE_KIND.values())


def _emit_user_next_step(ctx: ResultContext, exit_code: int) -> None:
    """Set ``user_next_step`` and print its block (plans/next-phase-command.md §2.2(1)).

    Only for the recorded invocation of a workflow-phase mode or a
    review-then-apply composite (``improve-plan``, ``improve-code``) that exits
    0 or 2, or ``full`` on 0, with no ``next`` owed — and never for a write phase that
    handed its batch loop to the invoker (no ``--exec-subagents`` and not the
    closing ``--mark-completed`` call) or for the invoker of a ``--detach``
    launch, whose run's terminal poll answers instead.
    That last exclusion is the ``next`` test itself: ``detach.launch`` records
    the run's poll command as ``next`` on both of its success paths (a fresh
    launch and an ``--if-not-running`` re-attach) and fails every other way
    with exit 1 or 3. A ``--detach`` invocation that ended before the boundary
    — the completed-phase guard's exit 2, which the tool routes hit on every
    re-run because they always append ``--detach`` — launched nothing, so no
    poll will ever answer for it, and it goes through the builder like any
    foreground exit. The builder's gate decides the rest. ``plan_arg`` is the
    ``--plan-file`` value as received — or, for a continuation, the spelling its
    hand-off recorded (:func:`_continued_plan_arg`); a detached worker, whose
    argv holds it absolute, takes the run record's ``plan_arg`` (else its
    ``plan_file``). The block goes to stderr when the invocation asked for JSON
    output.

    A commit review's front doors record the phase they front (``review-code``,
    ``apply-code-fixes``) or ``improve-commits`` with its pinned range
    (plans/review-commits.md §2.1, "What step 7 records"), so the gate below
    passes as for any phase, and the builder spells the answer back in the
    commit spelling (§2.8): after ``review-commits``, ``--apply-commit-fixes
    <base12>..<head12>`` under a why naming both reports.
    """
    record = invocation()
    if not record or ctx.next:
        return
    mode = mode_table.resolve(str(record.get("mode") or ""))
    if mode is None:
        return
    if mode.runs_workflow:
        if exit_code != EXIT_OK:
            return
    elif not (
        (mode.is_workflow_phase or mode.is_composite)
        and exit_code in (EXIT_OK, EXIT_NOTHING_TO_DO)
    ):
        # A review-then-apply composite answers on 0 and on 2 too
        # (plans/improve-plan-and-improve-code.md §2.6): its exit 2 is
        # `[ALREADY_COMPLETE]`, returned before its detach boundary, so a tool
        # route's `--detach` re-run of a finished composite carries the next
        # step like any foreground exit 2. The builder answers as the phase
        # it ends on, gate included.
        return
    argv = list(record.get("argv") or [])
    # No `--detach` test here: a launched or re-attached run already returned
    # above on its recorded `next`, and keying on the flag instead silenced a
    # completed phase's exit 2 that launched no run and so has no poll to
    # carry the answer.
    #
    # The native write leg's EMIT call is excluded (the batches are the
    # host's now, and the builder would answer `--resume` for the phase
    # being run); its closing `--mark-completed` call is not — that call
    # records the phase completed and is the one dispatcher invocation on
    # the native apply leg that can carry the answer (until 2026-10-05 the
    # exclusion swallowed it too, and only the report step's `util
    # next-command` ever answered). implement's closing step is `util
    # finalize-tracking --mark-completed`, a util, so that leg still reads
    # its answer from the report step's lookup.
    if (
        mode.phase in _write_phases()
        and not flag_present(argv, "--exec-subagents")
        and not flag_present(argv, "--mark-completed")
    ):
        return
    plan_arg, plan_path = _typed_plan(argv)
    if not plan_arg:
        return
    from utils import next_phase

    as_json = flag_value(argv, "--output-format") == "json"
    next_phase.emit_answer(
        plan_arg,
        resolve_host(argv),
        mode.name,
        plan_path=plan_path,
        stream=sys.stderr if as_json else sys.stdout,
    )


def _typed_plan(argv: Sequence[str]) -> Tuple[Optional[str], Optional[str]]:
    """``(plan as the user typed it, absolute plan path)`` for this invocation.

    The typed spelling is :func:`utils.cli_common.invocation_plan_arg` (the
    ``--plan-file`` value as received, or a continuation's recovered one); a
    detached worker, whose argv holds the plan absolute, takes its run record's
    ``plan_arg`` (else its ``plan_file``) instead.

    ``improve-commits`` is recorded with its pinned range, not a plan
    (``--revs <base12>..<head12>``, plans/review-commits.md §2.1, "What step
    7 records"): the plan is the brief that spelling names
    (``commit_review.brief_for_pinned``), and the typed spelling is the
    pinned range itself, which every command printed for it carries (§2.8).
    """
    plan_file = flag_value(argv, "--plan-file")
    plan_arg = invocation_plan_arg() or plan_file
    plan_path = os.path.abspath(plan_file) if plan_file else None
    if plan_file is None:
        pinned = flag_value(argv, "--revs")
        brief = _brief_for_pinned(pinned) if pinned else None
        if brief is not None:
            plan_arg, plan_path = plan_arg or pinned, brief
    worker = flag_present(argv, "--internal-worker")
    detach = sys.modules.get("utils.detach") if worker else None
    handle = detach.active_run() if detach is not None else None
    if handle is not None:
        plan_path = handle.plan_file
        plan_arg = handle.plan_arg or handle.plan_file
    return plan_arg, plan_path


def _brief_for_pinned(text: str) -> Optional[str]:
    """The brief a commit review's pinned ``<base12>..<head12>`` names
    (``commit_review.brief_for_pinned``: by name, no git call beyond the
    root), absolute, or ``None`` for any other text or outside a repository."""
    try:
        from utils.commit_review import brief_for_pinned

        brief = brief_for_pinned(str(text))
    except Exception:  # noqa: BLE001 - not a pinned range here
        return None
    return os.path.abspath(str(brief)) if brief is not None else None


def _continuation_target(command: str) -> Optional[Tuple["mode_table.Mode", str]]:
    """``(mode, plan)`` of a printed continuation command, else ``None``.

    A continuation is a dispatcher command (``… multi_llm.py <mode> <plan> …``,
    or ``--plan-file <plan>``) carrying one of
    :data:`utils.cli_common.CONTINUATION_VERBS`; its *mode* is a workflow phase.

    A continuation in the commit spelling (plans/review-commits.md §2.8:
    ``review-commits <base12>..<head12> --reaggregate``, or the brief path on
    a root range) names the phase its front door fronts
    (``Mode.commit_view_of``) and the brief its range names.
    """
    import shlex

    try:
        tokens = shlex.split(command)
    except ValueError:
        return None
    if not CONTINUATION_VERBS.intersection(t.split("=", 1)[0] for t in tokens):
        return None
    script = next(
        (i for i, token in enumerate(tokens)
         if os.path.basename(token) == "multi_llm.py"),
        None,
    )
    if script is None or script + 1 >= len(tokens):
        return None
    mode = mode_table.resolve(tokens[script + 1])
    fronts = mode.commit_view_of if mode is not None else None
    if fronts:
        mode = mode_table.resolve(fronts)
    if mode is None or not mode.is_workflow_phase or not mode.phase:
        return None
    rest = tokens[script + 2:]
    plan = flag_value(rest, "--plan-file")
    if plan is None and rest and not rest[0].startswith("-"):
        plan = rest[0]
        if fronts and not os.path.isfile(plan):
            plan = _brief_for_pinned(plan) or ""
    if not plan:
        return None
    return mode, plan


def _continued_phase_dir(mode: "mode_table.Mode", plan: str) -> Path:
    from utils.output_handler import phase_dir_path

    return phase_dir_path(Path(os.path.abspath(plan)), str(mode.phase))


def _remember_plan_spelling(ctx: ResultContext) -> None:
    """Record, for the continuation this run hands back, how its plan was typed.

    A native leg's ``next`` (``generate-tasks <plan> --reaggregate``, a review's
    ``--reaggregate``) names the plan absolutely, like every printed follow-up,
    and the host runs it verbatim — so the run that finishes the phase would
    otherwise print its next-phase command with the absolute path although the
    user typed a relative one (racing re-run 4, Claude Code phase 03). This
    writes the plan as this invocation received it into the continued phase's
    ``.status.json`` as ``plan_arg``, beside the ``plan_file`` the checkpoint
    already holds; :func:`_continued_plan_arg` reads it back. Only when the
    command names the same file and its phase dir exists; best-effort.
    """
    record = invocation()
    if not record or not ctx.next:
        return
    target = _continuation_target(str(ctx.next))
    if target is None:
        return
    mode, plan = target
    typed, _plan_path = _typed_plan(list(record.get("argv") or []))
    if not typed or os.path.realpath(typed) != os.path.realpath(plan):
        return
    phase_dir = _continued_phase_dir(mode, plan)
    if not phase_dir.is_dir():
        return
    from utils import status_file

    status_file.update_status(str(phase_dir), {"plan_arg": str(typed)})


def _continued_plan_arg(
    mode: "mode_table.Mode", argv: Sequence[str]
) -> Optional[str]:
    """The typed plan a continuation's hand-off recorded, when it names this plan.

    For a workflow-phase invocation carrying a continuation verb: the
    ``plan_arg`` :func:`_remember_plan_spelling` wrote into the phase dir's
    ``.status.json`` — else, when the hand-off recorded none (or one that does
    not pass), the phase's detached run record's ``plan_arg``, the plan as its
    launcher typed it: a detached launch records no hand-off spelling, and its
    status read's "advance it with: … --reaggregate" names the plan absolutely
    (hooks review of fix round 10). Either is printed only when
    ``next_phase.recorded_plan_spelling`` passes it — the folder is writable by
    every jailed batch, so a spelling that does not resolve strictly to this
    plan from this cwd, or that holds a character a shell would act on, is
    never printed. A passing spelling equal to the ``--plan-file`` received is
    ``None`` too, and the plan is printed as received.
    """
    if not mode.is_workflow_phase or not mode.phase:
        return None
    if not flag_present(argv, *sorted(CONTINUATION_VERBS)):
        return None
    plan = flag_value(argv, "--plan-file")
    if not plan:
        return None
    from utils import next_phase, status_file

    status = status_file.read_status(str(_continued_phase_dir(mode, plan)))
    run = status.get("run")
    for recorded in (
        status.get("plan_arg"),
        run.get("plan_arg") if isinstance(run, dict) else None,
    ):
        spelling = next_phase.recorded_plan_spelling(recorded, plan)
        if spelling is not None:
            return None if spelling == plan else spelling
    return None


def _raise_on_sigterm(signum, frame):  # pragma: no cover - exercised in a subprocess
    """SIGTERM → ``SystemExit(128 + signum)``, so ``main``'s ``finally`` runs.

    Once: later SIGTERMs are ignored before raising. A group kill reaches this
    process twice — directly and as the copy ``uv run`` forwards to its child —
    and the second ``SystemExit`` would be raised inside that ``finally``,
    cutting short the config restore and the result line it exists to run.
    Nothing is printed here: a handler can land inside a buffered write.
    """
    import signal

    try:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    except (ValueError, OSError):
        pass
    raise SystemExit(128 + signum)


def _install_foreground_sigterm():
    """Make a foreground SIGTERM run ``main``'s ``finally`` (plan I12).

    A foreground run had no SIGTERM handler, so the default action killed the
    process with no cleanup — and the trust entries its codex children wrote
    stayed in the user's config. Installed only when nothing else owns the
    signal (the default disposition) and only on the main thread; the detached
    worker installs its own handler later, which takes precedence. Returns the
    previous handler for :func:`_uninstall_foreground_sigterm`, or ``None``
    when nothing was installed.
    """
    try:
        import signal
        import threading

        if threading.current_thread() is not threading.main_thread():
            return None
        if signal.getsignal(signal.SIGTERM) is not signal.SIG_DFL:
            return None
        signal.signal(signal.SIGTERM, _raise_on_sigterm)
        return signal.SIG_DFL
    except (ImportError, ValueError, OSError, AttributeError):  # pragma: no cover
        return None


def _uninstall_foreground_sigterm(previous) -> None:
    """Put back the disposition :func:`_install_foreground_sigterm` replaced,
    only if our handler is still the one installed."""
    if previous is None:
        return
    try:
        import signal

        if signal.getsignal(signal.SIGTERM) is _raise_on_sigterm:
            signal.signal(signal.SIGTERM, previous)
    except (ValueError, OSError):  # pragma: no cover
        pass


def _restore_codex_trust() -> None:
    """Remove the codex trust entries this run's children added (plan I12).
    Never raises: close-out must never mask the run's result."""
    try:
        from utils import codex_trust
    except Exception:  # noqa: BLE001 - see above
        return
    try:
        codex_trust.restore_all()
    except Exception:  # noqa: BLE001 - see above  # pragma: no cover
        traceback.print_exc()


def _crash_summary(limit: int = 2000) -> str:
    """Message + traceback tail, for ``run.error`` on a crashed detached run."""
    text = traceback.format_exc()
    return text[-limit:]


def _close_detached_run(
    exit_code: Optional[int],
    error: Optional[str],
    result_state: Optional[str] = None,
) -> None:
    """Write the terminal ``run`` record when this process owns a detached run.

    *result_state* is the result context's state; ``detach`` records it as
    ``run.result_state`` only when the exit code cannot express it
    (``partial``), so a ``status`` poll can restate it (plan §5).
    """
    detach = sys.modules.get("utils.detach")
    if detach is None:
        return  # nothing detached ran; do not pay the import
    try:
        detach.finish_active_run(exit_code, error=error, result_state=result_state)
    except Exception:  # pragma: no cover - close-out must never mask the result
        traceback.print_exc()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
