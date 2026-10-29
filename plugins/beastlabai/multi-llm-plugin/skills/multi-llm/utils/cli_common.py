#!/usr/bin/env python3
"""The CLI surface every multi-llm entry point shares.

Four cross-cutting concerns live here so no entry point re-implements them:

* **The cross-cutting flag set.** ``--host``, ``--yes``/``--non-interactive``,
  ``--interactive``, ``--detach``, ``--exec-subagents`` and
  ``--skip-prerequisites`` are defined exactly
  once, as an ``add_help=False`` *parent* parser that ``multi_llm.py`` and every
  orchestrator parser mix in via ``parents=[...]``. Each orchestrator keeps its
  own parser as the source of truth for its own flags (the dispatcher forwards
  argv verbatim), so a direct
  ``python review_plan_orchestrator.py --plan-file … --host codex`` accepts the
  same flags with the same semantics as the dispatcher route. Sharing the
  definitions is what keeps "direct invocation is supported" from decaying into
  "works until it doesn't".

* **Skill-dir resolution.** Absolute, *symlinks preserved*
  (``os.path.abspath``, never ``realpath``): the dev workflow symlinks the Claude
  plugin-cache entry at a checkout, so resolving would rewrite a user's plugin
  invocation into a path they never named and move ``uv run --project`` off the
  ``pyproject.toml``/``uv.lock`` the host actually loaded. ``realpath`` belongs on
  *both* sides of a containment comparison and nowhere else.

* **Command building.** A follow-up command a host is expected to copy must be
  fully resolved — a ``${CLAUDE_SKILL_DIR}`` or ``{SKILL_DIR}`` token no shell
  expands is the bug this replaces — and it must keep its **allow-rule prefix**:
  Claude Code matches ``Bash(...)`` permissions as glob prefixes, so every
  command built here still starts with ``uv run`` (or
  ``PYTHONUNBUFFERED=1 uv``). Reshaping a printed command so it starts with
  something else (a wrapper script, a leading ``cd``, a shell ``&&`` chain)
  silently turns every follow-up into a permission prompt and must ship its own
  allow rule in the same commit.

* **The ``MULTI_LLM_RESULT`` line.** The single machine-readable last stdout line
  every ``multi_llm.py`` invocation ends with, so a host that cannot reliably
  parse prose (or is tailing a detached log) recovers mode, outcome, artifact
  paths and the one next command without regex-mining the transcript.

Absolute paths built here are **session-scoped, not artifacts**: the Claude
plugin cache is keyed by commit hash, so a skill-dir-absolute command saved in a
transcript or a state file can silently point at a directory that no longer
exists. Print them; never persist them.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import (
    Any, Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple, Union,
)

# Absolute, symlinks preserved. Module-level because it is a pure string
# computation on ``__file__`` — no I/O at import. Tests that need a fixture skill
# dir (e.g. one containing a space) monkeypatch this attribute.
_SKILL_DIR = Path(os.path.abspath(__file__)).parent.parent

#: Prefix reserved for hidden re-entry flags. Excluded from ``--help``, never
#: rendered into a user-facing follow-up command or a ``MULTI_LLM_RESULT.next``
#: value, and not part of the compatibility surface.
INTERNAL_FLAG_PREFIX = "--internal-"

#: The marker every dispatcher invocation ends its stdout with.
RESULT_MARKER = "MULTI_LLM_RESULT:"

# `plain_line` and its control-character set live in `text_clip` (fix round
# 22), beside the one rule for cutting a preview short; re-exported here, the
# name every caller has always imported.
try:
    from .text_clip import _CONTROL_CHARACTERS, clip, join_clauses, plain_line  # noqa: E402,F401
except ImportError:  # pragma: no cover - direct script runs with utils/ on path
    from text_clip import _CONTROL_CHARACTERS, clip, join_clauses, plain_line  # type: ignore # noqa: E402,F401

#: Uniform exit codes across every mode. The dispatcher never remaps a target's
#: code and invents one of its own only for an unknown mode or a rejected flag
#: combination.
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_NOTHING_TO_DO = 2
EXIT_NEEDS_HUMAN = 3

_STATE_BY_EXIT = {
    EXIT_OK: "done",
    EXIT_ERROR: "error",
    EXIT_NOTHING_TO_DO: "nothing-to-do",
    EXIT_NEEDS_HUMAN: "needs-human",
}

#: The one override word on ``EXIT_NOTHING_TO_DO`` that is not "nothing to
#: do": ``status`` reuses exit 2 for "come back later" as well as "already
#: complete" / "no run recorded" (F11, 2026-09-16), and a poll loop's own
#: contract is the exit code, never the word — ``run_status.py``'s poll
#: command and the opencode plugin's loop (``poll.code !== nothing_to_do``)
#: both key off ``EXIT_NOTHING_TO_DO`` itself. So a live run gets this word
#: instead of ``_STATE_BY_EXIT[EXIT_NOTHING_TO_DO]`` without touching the exit
#: code, added here (not special-cased at the call site) because this table is
#: the one place a host — or ``packaging/opencode/build.py``'s generated
#: ``dispatcher.states`` — looks to learn the vocabulary.
STATE_RUNNING = "running"

#: The second override word on ``EXIT_NOTHING_TO_DO``, and the narrower one:
#: ``status`` proved the run's recorded pid is gone while its last heartbeat is
#: still inside the window, so the run is not terminal yet (``detach`` closes it
#: out as ``failed(heartbeat_timeout)`` once the beat expires) but calling it
#: ``running`` is a lie — measured 2026-09-16, a write subagent's
#: ``killall -9 … python3`` SIGKILLed the detached worker and every poll in the
#: next minute reported the dead run as running (F2). Same exit code, same poll
#: contract; only the word changes, and it lives here beside ``STATE_RUNNING``
#: for the same reason: this table is where a host learns the vocabulary.
STATE_DIED = "died"

#: The one terminal result word the exit code cannot express: a run that
#: produced usable output with at least one model slot failed exits 0 (D6 row
#: 3) and says ``partial`` instead of ``done``. ``unattended.report_partial_results``
#: sets it on the live result context; a detached run carries it across the
#: process boundary as ``run.result_state`` (``detach.finish_active_run``) so a
#: ``status`` poll can restate it. Terminal, ``next: null`` — a host owes no
#: further instructions, it names the failed models from ``progress.models``.
STATE_PARTIAL = "partial"


# ---------------------------------------------------------------------------
# Skill-dir resolution and command building
# ---------------------------------------------------------------------------

def skill_dir() -> Path:
    """The running skill directory: absolute, symlinks preserved (see module doc)."""
    return _SKILL_DIR


def _quote(text: Union[str, Path]) -> str:
    """Encode one argument for the POSIX shell every rendered command targets.

    ``shlex.quote``, never hand-written double quotes: a double-quoted string
    still expands ``$VAR``, a backtick substitution and ``$(cmd)``, and every
    string quoted here is *filesystem-derived* — the skill dir, a plan path, a
    question. A checkout under ``/tmp/$(id).d`` would turn a printed follow-up
    into arbitrary command execution the moment a user ran it, which is not a
    thing a copy-pasteable command may do. Single quotes are inert in every
    POSIX shell, and POSIX is the *only* shell these commands are written for:
    every rendered shim and follow-up is a POSIX-shell command block, which is
    exactly why Git Bash is a hard install-time prerequisite on Windows
    (``host_install.GIT_BASH_MISSING`` — "there is no PowerShell instruction
    path"). So there is no second, ``cmd.exe``-flavoured renderer
    here to keep in sync; adding a native-Windows command surface means adding
    its encoder next to this one, not loosening this one.

    An argument with no shell-special character comes back bare, so an ordinary
    command still reads the way a user would type it.
    """
    return shlex.quote(str(text))


def dispatcher_prefix(base: Optional[Path] = None) -> str:
    """The invariant ``uv run … multi_llm.py`` prefix, fully resolved.

    This is the *one* substitution site a command needs: ``multi_llm.py``
    self-locates via ``__file__``, so the skill dir is needed only for
    ``uv run --project`` and the script path, and both live here.

    The uv flags come from :func:`utils.unattended.uv_run_args`, the single
    owner, rather than being spelled here — so a printed follow-up, a
    ``MULTI_LLM_RESULT.next`` string and the detached worker's re-exec cannot
    disagree about them. They used to: this prefix carried neither ``--frozen``
    nor ``--no-dev``, so every command it rendered was one a user could paste and
    have pull the whole dev group.
    """
    base = Path(base) if base is not None else skill_dir()
    # Imported here, not at module scope: ``unattended`` imports this module.
    from .unattended import uv_run_args
    flags = "".join(f" {flag}" for flag in uv_run_args())
    return (
        f"uv run{flags} --project {_quote(base)} -- "
        f"python {_quote(base / 'multi_llm.py')}"
    )


def dispatcher_command(
    mode: str,
    *args: Union[str, Path],
    base: Optional[Path] = None,
) -> str:
    """Build ``uv run … multi_llm.py <mode> <args…>`` with every path resolved.

    **Every** element goes through ``_quote`` — the mode word included. A bare
    flag and a plain mode word carry no shell-special character, so they come
    back unchanged and the result still reads the way a user would type it;
    what the uniform encoding removes is the "looks like a flag, so pass it
    through raw" branch, which handed a shell whatever a caller had (an ``ask``
    question, a ``--force-strategy`` value) with no encoding at all.
    """
    parts = [dispatcher_prefix(base), _quote(mode)]
    for arg in args:
        parts.append(_quote(arg))
    return " ".join(parts)


def reaggregate_command(
    mode: str,
    plan_file: Union[str, Path],
    *,
    base: Optional[Path] = None,
) -> str:
    """The one follow-up command a native-subagent host is ever handed.

    Everything downstream of it happens inside that single invocation, which is
    what keeps the staleness window of a printed absolute path to one turn.
    """
    return dispatcher_command(mode, plan_file, "--reaggregate", base=base)


#: The judge flag (D6 row 10): the spelling every emitted command uses, and the
#: legacy spellings the apply parsers still accept and older runs recorded.
AGENT_DECIDE_FLAG = "--agent-decide"
LEGACY_AGENT_DECIDE_FLAGS: Tuple[str, ...] = ("--claude-decide", "--let-claude-decide")
AGENT_DECIDE_SPELLINGS: Tuple[str, ...] = (AGENT_DECIDE_FLAG,) + LEGACY_AGENT_DECIDE_FLAGS


def canonical_flag(token: str) -> str:
    """*token* with a legacy judge-flag spelling folded onto :data:`AGENT_DECIDE_FLAG`."""
    return AGENT_DECIDE_FLAG if token in LEGACY_AGENT_DECIDE_FLAGS else token


def fold_judge_flag(tokens: Iterable[str]) -> List[str]:
    """*tokens* with every judge-flag spelling emitted once, as ``--agent-decide``."""
    out: List[str] = []
    for token in tokens:
        token = canonical_flag(str(token))
        if token == AGENT_DECIDE_FLAG and token in out:
            continue
        out.append(token)
    return out


#: The verbs a retry adds to a recorded invocation. ``retry_command`` strips
#: every spelling of these out of the replayed flag list before appending the
#: one(s) the caller asked for, so a recorded ``--force`` cannot double and a
#: ``--reaggregate`` run that failed is not replayed as ``--reaggregate
#: --reaggregate``.
#:
#: The two consolidation pass selectors ride along for the same reason: the
#: review-plan main tries ``--consolidate`` before ``--reaggregate-consolidation``
#: (``review_orchestrator_base.main``), so a replay that kept the recorded
#: ``--consolidate`` beside the new verb would re-prepare the batch it means to
#: merge.
RETRY_VERBS: FrozenSet[str] = frozenset({
    "--force", "--reaggregate", "--rerun-all",
    "--consolidate", "--consolidate-dry-run", "--reaggregate-consolidation",
})

#: The verbs of a *continuation*: the follow-up a native leg hands back (the
#: phase's ``next``) so the invoker can finish the same phase after its
#: subagents wrote their replies. That command names the plan absolutely, like
#: every printed follow-up, so the plan spelling the user typed survives it only
#: through the phase dir's ``.status.json`` (``multi_llm._remember_plan_spelling``
#: writes it, ``multi_llm._continued_plan_arg`` reads it back).
CONTINUATION_VERBS: FrozenSet[str] = frozenset({
    "--reaggregate", "--reaggregate-consolidation",
})


def retry_command(
    mode: str,
    *args: Union[str, Path],
    flags: Optional[Sequence[str]] = None,
    base: Optional[Path] = None,
) -> str:
    """``dispatcher_command`` with the caller's recorded flags spliced in (D2).

    *args* are the positionals (the plan, an ``ask`` question) followed by the
    retry verb(s) — ``--force``, ``--reaggregate``, ``--rerun-all``,
    ``--reaggregate-consolidation``. *flags* is the replay list
    (:func:`replay_flags`, or a document's stored ``replay_flags``); it is
    spliced in **behind the positionals and ahead of the verbs**, verbatim
    except for two edits: every retry verb it already carried is stripped, so
    ``--quick`` survives a retry and ``--force`` never doubles; and every judge
    spelling (``--claude-decide``, ``--let-claude-decide``) is folded onto
    ``--agent-decide`` and emitted once (:func:`fold_judge_flag`). A verb that
    is itself a judge spelling is canonicalized the same way, and drops every
    recorded spelling from the replay list so the flag appears only among the
    verbs. With no flags the output is byte-identical to
    ``dispatcher_command(mode, *args)``, which is what every pre-D2 test pins.

    The name deliberately matches the ``retry_command=`` keyword argument of
    ``dispatch_subagent_tasks``/``continue_past_marker``/``retry_instruction``
    — this function's return value is what that argument should carry — so
    import it as ``cli_common.retry_command`` and never bind the bare name in a
    module that also takes the kwarg.

    **Never sanitized.** A stored flag today's parser no longer knows is emitted
    as recorded: argparse then names it on stderr and the dispatcher maps that
    to exit 3, which is a better failure than the silently widened panel that
    dropping a selector produces.
    """
    positionals, tokens = retry_tokens(*args, flags=flags)
    return dispatcher_command(mode, *positionals, *tokens, base=base)


def retry_tokens(
    *args: Union[str, Path],
    flags: Optional[Sequence[str]] = None,
) -> Tuple[List[str], List[str]]:
    """:func:`retry_command`'s ``(positionals, flags and verbs)``, unrendered.

    The same edits as that command (recorded verbs stripped, ``--fresh``
    dropped under ``--resume``, judge spellings folded) without the
    dispatcher prefix, so ``status`` can spell the same retry the way a
    host's user types it (fix round 18).
    """
    positionals: List[str] = []
    verbs: List[str] = []
    for arg in args:
        if verbs or str(arg).startswith("-"):
            verbs.append(str(arg))
        else:
            positionals.append(str(arg))
    drop = set(RETRY_VERBS) | {v.split("=", 1)[0] for v in verbs}
    if "--resume" in verbs:
        # A retry continues the failed run. Replaying its original --fresh
        # would erase decisions, processed items and the prior-changes log
        # before the apply orchestrator has a chance to resume them.
        drop.add("--fresh")
    if any(canonical_flag(v) == AGENT_DECIDE_FLAG for v in verbs):
        drop.update(AGENT_DECIDE_SPELLINGS)
    kept = fold_judge_flag(
        str(token) for token in (flags or [])
        if str(token).split("=", 1)[0] not in drop
    )
    return positionals, kept + [canonical_flag(v) for v in verbs]


def durable_reaggregate_fields(
    orchestrator_script: str, plan_file: Union[str, Path]
) -> Dict[str, Any]:
    """What a *persisted* checkpoint may store about its follow-up command.

    Never the resolved command: the Claude plugin cache is keyed by commit hash,
    so a skill-dir-absolute command written into ``.status.json`` points at a
    directory that no longer exists after the next plugin update. Skill-dir
    movement is **rebindable** — unlike a content hash — so the durable form is the
    mode word plus the plan path, and the reader rebuilds the command from the
    *running* skill dir (``utils/detach.resolved_reaggregate_command``).

    The third element, ``replay_flags``, is the caller's own selection flags
    (:func:`replay_flags` over this process's :func:`invocation`), stored as a
    **list** — never a resolved command — so a reader in some later process can
    splice them back in through :func:`retry_command` and a ``--quick`` review
    stays a ``--quick`` review across the retry (D2).
    """
    mode = _modes().mode_for_script(orchestrator_script) or orchestrator_script
    return {
        "reaggregate_mode": mode,
        "plan_file": str(plan_file),
        "replay_flags": current_replay_flags(mode=mode),
    }


def reaggregate_command_for_script(
    orchestrator_script: str,
    plan_file: Union[str, Path],
    *,
    base: Optional[Path] = None,
) -> str:
    """``reaggregate_command`` keyed by a legacy ``*_orchestrator.py`` filename.

    The orchestrators pass their own filename around as ``orchestrator_script``;
    the mode word is looked up in ``modes.py`` so the printed command names the
    single entry point rather than a second, unadvertised one.
    """
    mode = _modes().mode_for_script(orchestrator_script) or orchestrator_script
    return reaggregate_command(mode, plan_file, base=base)


def modes_table():
    """The ``modes`` module, for callers under ``utils/`` (public alias)."""
    return _modes()


def _modes():
    """Import the top-level ``modes`` table, tolerating direct script runs."""
    try:
        import modes  # type: ignore
    except ImportError:  # pragma: no cover - only when utils/ is sys.path[0]
        sys.path.insert(0, str(skill_dir()))
        import modes  # type: ignore
    return modes


# ---------------------------------------------------------------------------
# Instruction rendering (the token-free core `util instructions <mode>` serves)
# ---------------------------------------------------------------------------

#: Every spelling of the skill-dir placeholder that may appear in the corpus,
#: longest first so a substitution cannot eat part of another token.
#: ``${SKILL_DIR}`` and ``$SKILL_DIR`` are deliberately absent: they are never
#: defined and are a test failure wherever they appear, so the brace token can
#: never be mistaken for a variable that merely was not set.
_SKILL_DIR_TOKENS = (
    "${CLAUDE_SKILL_DIR}",
    "${MULTI_LLM_SKILL_DIR}",
    "$MULTI_LLM_SKILL_DIR",
    "{SKILL_DIR}",
)

#: The second template token the corpus carries: the ``uv run`` flag list.
#:
#: The commands in ``instructions/*.md`` and in each ``hosts/*/shim.md.tmpl`` are
#: verbatim model-facing text on the file route, so a hand-typed ``uv run
#: --project`` there is a *dispatch* that omits the flags — and ``--no-dev`` is
#: the load-bearing one: without it a first run syncs the whole dev group (17
#: packages measured against this tree) and every offline posture fails on a
#: package it never needed. Rendering the flags from the one owner,
#: :func:`utils.unattended.uv_run_args`, is what stops the runbook text and
#: :func:`dispatcher_prefix` from disagreeing about them.
UV_RUN_FLAGS_PLACEHOLDER = "{UV_RUN_FLAGS}"

#: The third template token: the mode a bare argument text resolves to.
#:
#: "No mode flag means ``review-plan``" is a *rule*, and :data:`modes.DEFAULT_MODE`
#: owns it. Every shim template states that rule twice — once in its step 2 prose
#: and once in its worked examples — so without a token those are hand-typed
#: copies that a change to the constant leaves behind. Rendering them here is what
#: makes the constant's "every surface renders from it" true of the file route as
#: well as of ``dist/cli-surface.json``.
DEFAULT_MODE_PLACEHOLDER = "{DEFAULT_MODE}"

#: The fourth template token: the decision rule for exit 3.
#:
#: "Exit 3 means stop, report, and never do the phase's work by hand" is a
#: *rule* the same way the default mode is, and :data:`modes.NEEDS_HUMAN_RULE`
#: owns it. Every shim template and the plugin's command body state it once —
#: through this token, never as a literal — so the file routes cannot drift
#: from the plugin's own exit-3 message, which is composed from the same
#: constant's sibling.
NEEDS_HUMAN_RULE_PLACEHOLDER = "{NEEDS_HUMAN_RULE}"


def render_instruction_text(text: str, base: Union[str, Path]) -> str:
    """Substitute every template placeholder in instruction/shim text.

    Four tokens, one rule: ``{SKILL_DIR}`` (and its host-expanded spellings)
    becomes *base*, :data:`UV_RUN_FLAGS_PLACEHOLDER` becomes the ``uv run`` flag list,
    :data:`DEFAULT_MODE_PLACEHOLDER` becomes ``modes.DEFAULT_MODE`` and
    :data:`NEEDS_HUMAN_RULE_PLACEHOLDER` becomes ``modes.NEEDS_HUMAN_RULE``. The skill
    dir is an argument so a test can render against a fixture path containing a
    space; the others are read from their owners rather than passed, for the
    same reason :func:`dispatcher_prefix` reads the flag list — a caller given
    the chance to supply one is a caller that can supply a different one.
    Substituting at read time from the *running* skill dir and the *running* flag
    list is also why the served core cannot go stale: there is no rendered copy
    to keep in sync.
    """
    # Imported here, not at module scope: ``unattended`` imports this module.
    from .unattended import uv_run_args

    rendered = text
    for token in _SKILL_DIR_TOKENS:
        rendered = rendered.replace(token, str(base))
    rendered = rendered.replace(UV_RUN_FLAGS_PLACEHOLDER, " ".join(uv_run_args()))
    rendered = rendered.replace(DEFAULT_MODE_PLACEHOLDER, _modes().DEFAULT_MODE)
    return rendered.replace(NEEDS_HUMAN_RULE_PLACEHOLDER, _modes().NEEDS_HUMAN_RULE)


# ---------------------------------------------------------------------------
# The shared parent parser
# ---------------------------------------------------------------------------

def build_parent_parser(
    *,
    include_yes: bool = True,
    include_interactive: bool = True,
) -> argparse.ArgumentParser:
    """The cross-cutting flags, defined once.

    Mixed into a child parser with ``parents=[build_parent_parser()]``. The two
    toggles exist only for a parser that must *not* offer a flag at all (e.g. a
    utility with no notion of interactivity); they are not an invitation to
    redefine one locally.

    ``--detach`` now has behaviour for the long-running fan-out modes (see
    ``utils/detach.py``); ``--exec-subagents`` is still accepted and stored only.
    The two hidden ``--internal-*`` re-entry flags are defined here rather than
    per orchestrator because the detached worker is re-executed through
    ``multi_llm.py`` and every mode's parser has to accept them.
    """
    parent = argparse.ArgumentParser(add_help=False)
    group = parent.add_argument_group("cross-cutting options")
    group.add_argument(
        "--host",
        metavar="ID",
        default=None,
        help="Host harness driving this run (e.g. claude-code, codex, opencode). "
             "Recorded for capability resolution; does not change orchestration.",
    )
    if include_yes:
        group.add_argument(
            "--yes",
            "-y",
            "--non-interactive",
            dest="yes",
            action="store_true",
            help="Run unattended: never prompt, resolve every gate from config "
                 "and flags. Confirms bulk approval operations.",
        )
    if include_interactive:
        group.add_argument(
            "--interactive",
            "-i",
            action="store_true",
            help="Force interactive model selection (ignores YAML defaults)",
        )
    group.add_argument(
        "--detach",
        action="store_true",
        help="Run the phase in a self-daemonized process (fan-out modes only) "
             "and return immediately with its log path and a status command to "
             "poll. Implies --yes. Never combine with a host's own background "
             "primitive.",
    )
    group.add_argument(
        "--if-not-running",
        action="store_true",
        help="With --detach: if a run for this phase is already in flight, print "
             "its run_id/log/status command and exit 0 instead of failing.",
    )
    group.add_argument(
        "--max-detached",
        type=int,
        default=None,
        metavar="N",
        help="Ceiling on concurrent detached runs for this project "
             "(default 4, or $MULTI_LLM_MAX_DETACHED).",
    )
    group.add_argument(
        "--exec-subagents",
        action="store_true",
        help="Run materialized subagent prompts through the provider executor "
             "instead of a host's native subagent tool, and continue past each "
             "marker in the same process (read/analyze phases: validation, "
             "revalidation, consolidation, salvage, judging). Runner and limits "
             "come from providers.yaml `driver:`.",
    )
    # D3l: the recommended first unattended run on a new host, and what CI uses to
    # assert a shim's write path is sane without touching a real repo. Deliberately
    # NOT implied by anything: it changes a run into a preflight.
    group.add_argument(
        "--dry-run-subagents",
        action="store_true",
        help="Preflight every subagent dispatch and start no child: resolve the "
             "runner, render the exact argv, check prompt transport and size, "
             "apply the invocation profile, the write-concurrency admission check "
             "and driver.write_paths — then write "
             "{phase}/subagent_dry_run.json and exit 0 having changed nothing.",
    )
    # D6a: consent to run unattended is not consent to stale input, so this is a
    # separate flag and `--yes` never implies it. Defined here rather than per
    # orchestrator because the two gated modes plus
    # `check_workflow_prerequisites.py` all need the same spelling and the same
    # semantics (loud, recorded, non-fatal).
    group.add_argument(
        "--skip-prerequisites",
        action="store_true",
        help="Proceed even though a prerequisite phase's output was never "
             "applied. Loud and recorded (the skip lands in state.json and in "
             "every later report); never implied by --yes.",
    )
    # Hidden re-entry flags: the detached worker is re-executed as
    # `multi_llm.py <mode> … --internal-worker --internal-run-id <uuid>`, so every
    # mode's parser must accept them. Suppressed from --help, never rendered into
    # a follow-up command or a MULTI_LLM_RESULT.next value.
    group.add_argument(
        INTERNAL_FLAG_PREFIX + "worker",
        dest="internal_worker",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    group.add_argument(
        INTERNAL_FLAG_PREFIX + "run-id",
        dest="internal_run_id",
        default=None,
        help=argparse.SUPPRESS,
    )
    return parent


# ---------------------------------------------------------------------------
# The MULTI_LLM_RESULT line
# ---------------------------------------------------------------------------

#: The result-line key naming the repository root a command typed in a
#: subdirectory ran from (fix round 27). The tool servers read it off a
#: launch's line to name a plan typed from that root for their polls, their
#: abort and the resume lookup, instead of walking to a ``.git`` themselves
#: (the walk named the root's plan where the dispatcher refused to move:
#: ``GIT_DIR`` set, a planted ``core.worktree``, a planted nested ``.git``).
RAN_FROM_ROOT_KEY = "ran_from_root"


class ResultContext:
    """Collects the one machine-readable line an invocation ends with.

    A target that wants to contribute reaches the *active* context through the
    module-level helpers below rather than being handed one, so adding a recorded
    artifact never changes a ``main(argv)`` signature.
    """

    def __init__(self, mode: Optional[str] = None, phase: Optional[str] = None):
        self.mode = mode
        self.phase = phase
        self.state: Optional[str] = None
        self.artifacts: List[str] = []
        self.next: Optional[str] = None
        self.consolidation_recommended: Optional[Dict[str, Any]] = None
        self.high_priority_groups: Optional[Dict[str, Any]] = None
        self.validation_context: Optional[Dict[str, Any]] = None
        self.validation_counts: Optional[Dict[str, int]] = None
        self.answer_origins: Optional[Dict[str, Any]] = None
        self.notice: Optional[str] = None
        self.progress: Optional[Dict[str, Any]] = None
        self.progress_lines: Optional[List[str]] = None
        self.user_next_step: Optional[Dict[str, Any]] = None
        self.user_resume: Optional[Dict[str, Any]] = None
        #: One plain line saying why a run stopped, for a needs-human or
        #: failed exit: both package servers read ``payload.error`` as "the
        #: last line it left" and put it in the message the host relays, and
        #: the detached close-out records it as ``run.error`` so a terminal
        #: poll carries it too (racing re-run 3, 2026-10-05: a stopped
        #: implement's result line named no error and the host said so).
        self.error: Optional[str] = None
        #: The repository root a command typed in a subdirectory ran from
        #: (``multi_llm._run_from_repository_root``, fix round 27), so a tool
        #: server names the plan the way the dispatcher read it; ``None`` when
        #: the command ran where it was typed.
        self.ran_from_root: Optional[str] = None
        #: The commit range a commit front door acts on, as the tool routes
        #: render the commit block from it (plans/review-commits.md §2.3,
        #: "Relay"): ``{brief, base, head, commits, more, full_list, window,
        #: drifted, size}`` plus ``selected`` on a no-argument apply, built by
        #: ``commit_range.result_payload``. ``None`` on every other run.
        self.commit_range: Optional[Dict[str, Any]] = None
        #: The apply guard's decision as the ``[COMMIT_FIXES]`` block shows
        #: it, read from the saved ``commit_range.guard`` (§2.3), so a
        #: detached apply's terminal ``status`` poll carries it too. ``None``
        #: on every run that applied no commit review.
        self.commit_fixes: Optional[Dict[str, Any]] = None
        self._emitted = False

    # -- recording ------------------------------------------------------
    def add_artifact(self, path: Union[str, Path]) -> None:
        text = str(path)
        if text and text not in self.artifacts:
            self.artifacts.append(text)

    def set_next(self, command: Optional[str]) -> None:
        """Record the single follow-up command, if one is genuinely owed.

        Silently drops a command carrying an ``--internal-*`` flag: those are
        re-entry plumbing and are never handed to a host.
        """
        if command and INTERNAL_FLAG_PREFIX in command:
            return
        self.next = command or None

    def set_consolidation_recommended(
        self, recommendation: Optional[Dict[str, Any]]
    ) -> None:
        """Record the optional consolidation recommendation.

        Deliberately **not** a ``next``: ``--consolidate`` is one of the
        dispatcher's mechanical continuations, which a host such as the opencode
        plugin auto-follows without asking — a recommendation would become an
        unrequested extra phase. It is a *fact about the finished phase*, and it
        rides the result line so a host reads it where it reads everything else.
        """
        self.consolidation_recommended = (
            dict(recommendation) if recommendation else None
        )

    def set_high_priority_groups(self, data: Optional[Dict[str, Any]]) -> None:
        """Record the distinct-HIGH-group count (F4), if there is one.

        Mirrors ``set_consolidation_recommended``: a bare ``print`` never
        reaches a detached caller, and the count a CI gate or `--fail-on-high`
        would act on is the single most actionable fact a code review
        produces. Present only when there is something to report, so every
        other invocation's line is byte-for-byte what it was.
        """
        self.high_priority_groups = dict(data) if data else None

    def set_validation_context(self, obj: Optional[Dict[str, Any]]) -> None:
        """Record the published ``validation_context`` object (§2.4), if any.

        Mirrors ``set_consolidation_recommended``: the one writer,
        ``utils.validation.publish_validation_context``, puts the same object
        in ``.status.json`` and here, so the result line and the checkpoint
        cannot disagree. ``None`` (a round whose context fit inline) leaves the
        line byte-for-byte what it was.
        """
        self.validation_context = dict(obj) if obj else None

    def set_validation_counts(self, counts: Optional[Dict[str, int]]) -> None:
        """Record the per-verdict group counts (§6 T6.1), if validation ran.

        ``{valid, invalid, needs_human_decision, validation_failed}`` — one key
        per group ``validation_status``, snake_case. Mirrors
        ``set_high_priority_groups``: the counts lived only in ``report.md`` and
        ``validation.json``, so a host summarising a finished run from the
        result line alone left the needs-human-decision groups out (run
        b38de8bb, 2026-09-24: 3 of 57 groups went unmentioned). ``None`` (no
        validation ran) leaves the line byte-for-byte what it was.
        """
        self.validation_counts = dict(counts) if counts else None

    def set_answer_origins(self, origins: Optional[Dict[str, Any]]) -> None:
        """Record an ask run's answer counts by origin (plans/ask-answer-
        recovery-and-false-success.md D7.2), if this is one.

        ``{answered, file, stdout, fallback, accepted, unrecorded, kept,
        warn_all_fallback}`` — the numbers of the ask closing report's
        ``answered: …`` line and its ``[WARN]``'s predicate, computed once by
        ``ask_orchestrator.answer_origins`` so the prose and this field cannot
        disagree. It follows ``set_validation_counts``' route (``.status.json``,
        ``detach.classify_run``, a pinned ``status --view run``) because the
        ``[WARN]`` is prose and a host reading only the result line would miss
        an all-fallback run. Unlike the counts above it is present on a
        zero-answer run too (all zeros, flag ``false``), so only ``None`` — every
        other mode — leaves the line byte-for-byte what it was.
        """
        self.answer_origins = dict(origins) if origins is not None else None

    def set_notice(self, text: Optional[str]) -> None:
        """Record the workflow-level notice a terminal ``status`` run carries.

        Deliberately **not** ``next``: ``next`` is what the opencode plugin
        auto-follows without asking, and a workflow notice is advisory prose
        ("run --apply-task-suggestions, or skip to --implement"), not a
        continuation the plugin should run unattended. It exists because
        ``--view run`` — the only channel that plugin polls — used to omit the
        workflow view entirely, so a terminal run's real follow-up lived only
        in text nothing read: the model saw `next: null`, said "nothing
        further to run", then invented `--apply-task-suggestions` from general
        knowledge instead of the notice already sitting in `--view all`
        (F7, 2026-09-16).
        """
        self.notice = text or None

    def set_progress(self, progress: Optional[Dict[str, Any]]) -> None:
        """Record the watched run's whole ``progress`` object, if it has one.

        Mirrors :meth:`set_high_priority_groups`: present only when there is
        something to report, so every other invocation's line stays
        byte-for-byte what it was.

        It exists because the fan-out's per-model map had exactly one surface —
        ``render_run_text``'s human table — and the OpenCode *package* route has
        no agent in the loop to read it: the ``multi_llm`` tool supervises the
        poll itself and would have had to regex a rendered line to relay
        anything mid-run. A regex over human text would also be the first break
        in the rule that the JS holds no mode word, flag or message of its own,
        so the structured object rides the result line instead and the plugin
        reads ``poll.result.progress``.

        Copied one level deep rather than deep-copied: the nested ``models`` map
        is handed to ``json.dumps`` immediately and the caller (a read-only
        ``status`` poll) never mutates it afterwards.

        It is the status file's object **whole and unreworded** — no key is
        added to it here, which is why the rendered lines its one agent-less
        reader needs ride beside it in :meth:`set_progress_lines` rather than
        inside it.
        """
        self.progress = dict(progress) if progress else None

    def set_progress_lines(self, lines: Optional[Sequence[str]]) -> None:
        """Record the already-rendered progress line(s) a host may show verbatim.

        The sibling of :meth:`set_progress`, and the reason the two are separate
        keys: ``progress`` is the checkpoint's own object, carried through
        unreworded so a reader gets the numbers where they were computed, while
        this is *text* — ``run_status`` rendering that same object through the
        renderers the human view already uses (the fan-out roster, and the
        ``just finished:`` line ``--wait`` alone can honestly write).

        It exists for the OpenCode **package** route, which is the one host with
        no agent in the poll loop: the plugin's ``execute`` supervises the run
        itself and the model makes exactly one blocking tool call, so every
        instruction telling an agent to announce the roster and relay what just
        finished is structurally unreachable there — nothing reads
        ``instructions/*.md`` on that route, and the orchestrator's own
        ``[PROGRESS]`` lines go to a log the plugin never opens. The plugin's
        one live channel is a toast whose ``message`` is a string, and the rule
        that file is held to is that it composes no sentence of its own. So the
        sentence is composed here, by the renderers that already own its
        wording, and the plugin passes it through verbatim.

        Rendered strings and not a structure to render: a host that had to
        compose the line would be a second author of it, which is exactly the
        drift this key removes. Present only when there is something to show, so
        every other invocation's line stays byte-for-byte what it was, and empty
        entries are dropped rather than carried as blanks a reader must filter.
        """
        kept = [str(line) for line in lines if line] if lines else []
        self.progress_lines = kept or None

    def set_user_next_step(self, obj: Optional[Dict[str, Any]]) -> None:
        """Record the workflow's next phase, as the command the *user* types.

        ``{"phase", "command", "optional_before": [{"phase", "command",
        "why"}], "complete": false}`` (``optional_before`` omitted when empty),
        or exactly ``{"phase": null, "command": null, "complete": true}`` when
        the workflow is complete (plans/next-phase-command.md §2.1).

        Deliberately **not** ``next``: ``next`` is a follow-up for the *caller*,
        and a tool route (the opencode plugin, the codex MCP server)
        auto-follows it without asking. This is the next *phase*, a command
        for the user to type in a fresh context; followed by a tool route it
        would start an unrequested phase. So the two never share a key, and
        :meth:`payload` never carries this one beside a non-null ``next``.

        Stored as a copy, so a caller that keeps mutating its dict cannot move
        the line after the fact. A completed answer (``command`` null) is an
        answer and is kept; only ``None`` clears the key. ``None`` — the
        builder had no answer — leaves the line byte-for-byte what it was, and
        "absent" always means "no answer", never "workflow complete".
        """
        self.user_next_step = copy.deepcopy(obj) if obj is not None else None

    def set_error(self, text: Optional[str]) -> None:
        """Record the one-line reason the run stopped (``MULTI_LLM_RESULT.error``),
        as a :func:`plain_line`: every host shows it, and it carries text a
        runner or a task file wrote."""
        # One line the hosts quote inside their message: bounded, so a long
        # refusal cannot bury the message it decorates; cut at a word, marked
        # (fix round 22).
        self.error = clip(text, ERROR_MAX_CHARS) or None

    def set_user_resume(self, obj: Optional[Dict[str, Any]]) -> None:
        """Record the command that *resumes* a stopped write phase, for the user.

        ``{"phase", "command", "flags"}``: the same phase, in the host's own
        spelling (``utils.next_phase.resume_command``), and the flags it
        carries after the plan; plus, when the phase's last stop named
        ``--human-task`` answers, ``answers`` (``[{command, flags, why}]``)
        and ``answers_text`` (them as one run of text), so a tool route offers
        each as an option and names each in its message (fix round 14). Not
        ``user_next_step``, which
        names the *next* phase and is never set on a failed run, and never
        ``next``, which a tool route auto-follows: a needs-human stop is where a
        person decides, so this is for the user to type and nothing may run it.
        Set only by ``util next-command --blocked``, which the tool routes ask
        after an exit 3 (2026-10-02: both routes ended a blocked ``implement``
        with tool-call JSON or a raw ``uv run`` argv, and no command the user
        could type). ``None`` leaves the line byte-for-byte what it was.
        """
        self.user_resume = copy.deepcopy(obj) if obj is not None else None

    def set_commit_range(self, payload: Optional[Dict[str, Any]]) -> None:
        """Record the commit range a commit front door acts on.

        ``MULTI_LLM_RESULT`` is one JSON line a host parses, and a tool route
        has no agent reading the printed ``[COMMIT_RANGE]`` block, so its
        server renders the block from this key instead
        (plans/review-commits.md §2.3, "Relay"). The commit list is capped
        as the block is (``commits`` holds the 20 newest, ``more`` counts the
        rest, ``full_list`` names where they are), so ``this branch`` over
        hundreds of commits stays one readable line. Stored as a copy;
        ``None`` leaves every other run's line byte-for-byte what it was.
        """
        self.commit_range = copy.deepcopy(payload) if payload is not None else None

    def set_commit_fixes(self, payload: Optional[Dict[str, Any]]) -> None:
        """Record the ``[COMMIT_FIXES]`` decision of a commit review's apply.

        Read from the saved guard decision rather than from the printed
        block, so a foreground apply, improve-commits' apply step and the
        terminal ``status`` poll of a detached apply all carry the same
        object (plans/review-commits.md §2.3). Stored as a copy; ``None``
        leaves every other run's line byte-for-byte what it was.
        """
        self.commit_fixes = copy.deepcopy(payload) if payload is not None else None

    # -- emitting -------------------------------------------------------
    def payload(self, exit_code: int) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "mode": self.mode,
            "phase": self.phase,
            "state": self.state or _STATE_BY_EXIT.get(exit_code, "error"),
            "exit": exit_code,
            "artifacts": list(self.artifacts),
            "next": self.next,
        }
        # Present only when there is something to recommend, so every other
        # invocation's line is byte-for-byte what it was — and so "absent" and
        # "not recommended" cannot be told apart by a reader that should treat
        # them the same.
        if self.consolidation_recommended:
            payload["consolidation_recommended"] = dict(
                self.consolidation_recommended
            )
        if self.high_priority_groups:
            payload["high_priority_groups"] = dict(self.high_priority_groups)
        if self.validation_context:
            payload["validation_context"] = dict(self.validation_context)
        if self.validation_counts:
            payload["validation_counts"] = dict(self.validation_counts)
        if self.answer_origins is not None:
            payload["answer_origins"] = dict(self.answer_origins)
        if self.notice:
            payload["notice"] = self.notice
        if self.progress:
            payload["progress"] = dict(self.progress)
        if self.progress_lines:
            payload["progress_lines"] = list(self.progress_lines)
        # `is not None`, never truthiness: the completed answer
        # (`command: null`) is an answer and must ride the line. The second
        # guard is defensive — the emitters' gate already keeps the key off
        # these runs — so the key can never sit beside a follow-up the caller
        # owes (`next`), or on a failed or needs-human run, whose `next` /
        # `options` own what happens instead.
        if (
            self.user_next_step is not None
            and not self.next
            and exit_code not in (EXIT_ERROR, EXIT_NEEDS_HUMAN)
        ):
            payload["user_next_step"] = copy.deepcopy(self.user_next_step)
        if self.user_resume is not None:
            payload["user_resume"] = copy.deepcopy(self.user_resume)
        # The commit modes' two blocks, for the tool routes to render
        # (plans/review-commits.md §2.3): present only when set, on any exit,
        # since a refusal after resolution still printed the commit block.
        if self.commit_range is not None:
            payload["commit_range"] = copy.deepcopy(self.commit_range)
        if self.commit_fixes is not None:
            payload["commit_fixes"] = copy.deepcopy(self.commit_fixes)
        # Gated on the word the line carries, not the exit code: under
        # `status --exit-zero` the verdict's word stays (`keep_state_word`)
        # while the code is 0, and the stop's headline the poll relays as
        # "the last line it left" used to drop off exactly that line
        # (reviewer repro, fix round 8).
        if self.error and payload["state"] in (
            _STATE_BY_EXIT[EXIT_ERROR], _STATE_BY_EXIT[EXIT_NEEDS_HUMAN],
        ):
            payload["error"] = self.error
        # Present only when the command moved, so every other line is
        # byte-for-byte what it was.
        if self.ran_from_root:
            payload[RAN_FROM_ROOT_KEY] = self.ran_from_root
        return payload

    def emit(self, exit_code: int, stream=None) -> None:
        """Write the terminal line. Idempotent: exactly one line per invocation."""
        if self._emitted:
            return
        self._emitted = True
        out = stream if stream is not None else sys.stdout
        out.write(f"{RESULT_MARKER} {json.dumps(self.payload(exit_code))}\n")
        try:
            out.flush()
        except (AttributeError, ValueError):  # pragma: no cover - closed stream
            pass


_ACTIVE: Optional[ResultContext] = None


def activate_result(context: ResultContext) -> ResultContext:
    """Make ``context`` the one the recording helpers below reach."""
    global _ACTIVE
    _ACTIVE = context
    return context


def deactivate_result() -> None:
    global _ACTIVE
    _ACTIVE = None


def active_result() -> Optional[ResultContext]:
    return _ACTIVE


def record_artifact(path: Union[str, Path]) -> None:
    """Record an artifact path if a dispatcher run is active; else a no-op.

    A no-op under direct invocation is deliberate: an orchestrator run outside
    the dispatcher has no ``MULTI_LLM_RESULT`` line to contribute to, and must
    behave identically either way.
    """
    if _ACTIVE is not None:
        _ACTIVE.add_artifact(path)


def record_artifacts(paths: Iterable[Union[str, Path]]) -> None:
    for path in paths:
        record_artifact(path)


def record_ran_from_root(root: str) -> None:
    """The active result's :data:`RAN_FROM_ROOT_KEY` (fix round 27)."""
    if _ACTIVE is not None:
        _ACTIVE.ran_from_root = root


def record_next(command: Optional[str]) -> None:
    """Record the single follow-up command, if a dispatcher run is active."""
    if _ACTIVE is not None:
        _ACTIVE.set_next(command)


def record_mode_phase(mode: Optional[str], phase: Optional[str]) -> None:
    """Override ``MULTI_LLM_RESULT.mode``/``.phase``, if a dispatcher run is active.

    A no-op under direct invocation, same as every other ``record_*`` helper.
    ``status``'s own dispatcher mode stamps ``ctx.mode = "status"``,
    ``ctx.phase = None`` before ``run_status.main`` ever runs (``multi_llm.py``
    sets both from the mode table, and ``status`` is not a phase) — right for a
    plain multi-run listing, but a ``--wait`` poll pinned to one run already
    knows that run's own mode/phase from its ``.status.json`` and reports them
    literally to a host that reads the result verbatim without opening the
    rendered text (N5, 2026-09-16: the opencode plugin handed a model
    ``{"mode": "status", "phase": null, "state": "done", …}`` for a finished
    ``implement`` run, which a weaker model than the one that hit this would
    have to infer its phase from state alone).
    """
    if _ACTIVE is not None:
        if mode:
            _ACTIVE.mode = mode
        if phase:
            _ACTIVE.phase = phase


def record_state(word: Optional[str]) -> None:
    """Override ``MULTI_LLM_RESULT.state``, if a dispatcher run is active.

    A no-op under direct invocation, same as every other ``record_*`` helper.
    Left unset, ``payload()`` falls back to ``_STATE_BY_EXIT[exit_code]`` — this
    is for the override cases (``STATE_RUNNING``, ``mark_needs_human``'s
    ``"needs-human"``) where the exit code alone does not say which word fits.
    """
    if _ACTIVE is not None:
        _ACTIVE.state = word


def keep_state_word(exit_code: int) -> None:
    """Pin the word *exit_code* would give ``MULTI_LLM_RESULT.state``.

    For a mode about to return a different exit code than the one its answer
    means (``status --exit-zero``): an override already recorded
    (``STATE_RUNNING``, ``STATE_DIED``) stays, otherwise the word the exit
    code maps to is recorded, so the line still says ``nothing-to-do`` or
    ``needs-human`` under its ``exit: 0``. A no-op under direct invocation.
    """
    if _ACTIVE is not None and _ACTIVE.state is None:
        _ACTIVE.state = _STATE_BY_EXIT.get(exit_code, "error")


def record_consolidation_recommended(
    recommendation: Optional[Dict[str, Any]]
) -> None:
    """Record the consolidation recommendation, if a dispatcher run is active."""
    if _ACTIVE is not None:
        _ACTIVE.set_consolidation_recommended(recommendation)


def record_high_priority_groups(data: Optional[Dict[str, Any]]) -> None:
    """Record the distinct-HIGH-group count (F4), if a dispatcher run is active."""
    if _ACTIVE is not None:
        _ACTIVE.set_high_priority_groups(data)


def record_validation_context(obj: Optional[Dict[str, Any]]) -> None:
    """Record the ``validation_context`` object, if a dispatcher run is active."""
    if _ACTIVE is not None:
        _ACTIVE.set_validation_context(obj)


def record_validation_counts(counts: Optional[Dict[str, int]]) -> None:
    """Record the per-verdict group counts, if a dispatcher run is active."""
    if _ACTIVE is not None:
        _ACTIVE.set_validation_counts(counts)


def record_answer_origins(origins: Optional[Dict[str, Any]]) -> None:
    """Record an ask run's ``answer_origins``, if a dispatcher run is active."""
    if _ACTIVE is not None:
        _ACTIVE.set_answer_origins(origins)


def record_notice(text: Optional[str]) -> None:
    """Record the workflow notice, if a dispatcher run is active."""
    if _ACTIVE is not None:
        _ACTIVE.set_notice(text)


def add_notice(text: Optional[str]) -> None:
    """Append *text* to the notice already recorded (``; ``-joined), if any.

    For a phase's own notes (fix round 14: a consistency warning, the items
    a judge skipped), which must not replace a notice another site set.
    Joined by ``text_clip.join_clauses`` (fix round 28), so the notice
    before it gives up its closing stop to the separator.
    """
    if _ACTIVE is None or not text:
        return
    current = _ACTIVE.notice
    _ACTIVE.set_notice(join_clauses([current, text]) if current else text)


def record_progress(progress: Optional[Dict[str, Any]]) -> None:
    """Record the watched run's ``progress`` object, if a dispatcher run is active."""
    if _ACTIVE is not None:
        _ACTIVE.set_progress(progress)


def record_progress_lines(lines: Optional[Sequence[str]]) -> None:
    """Record the rendered progress line(s), if a dispatcher run is active."""
    if _ACTIVE is not None:
        _ACTIVE.set_progress_lines(lines)


def record_user_next_step(obj: Optional[Dict[str, Any]]) -> None:
    """Record ``user_next_step``, if a dispatcher run is active; else a no-op.

    The command for the *user* to type, never a ``next`` — see
    :meth:`ResultContext.set_user_next_step`.
    """
    if _ACTIVE is not None:
        _ACTIVE.set_user_next_step(obj)


#: How long the result line's ``error`` may be (:meth:`set_error`). A stop's
#: headline is fitted to it by one rule (``write_batch_scheduler.
#: fit_stop_headline``, fix round 19): the model's quoted words give way
#: first, then the not-run list and the task titles, never the remedy, the
#: answers or the line saying nothing ran the repository's tests.
ERROR_MAX_CHARS = 1200


def record_error(text: Optional[str]) -> None:
    """Record the run's one-line stop reason, if a dispatcher run is active."""
    if _ACTIVE is not None:
        _ACTIVE.set_error(text)


def record_user_resume(obj: Optional[Dict[str, Any]]) -> None:
    """Record ``user_resume``, if a dispatcher run is active; else a no-op."""
    if _ACTIVE is not None:
        _ACTIVE.set_user_resume(obj)


def record_commit_range_result(payload: Optional[Dict[str, Any]]) -> None:
    """Record the result line's ``commit_range``, if a dispatcher run is
    active; else a no-op (:meth:`ResultContext.set_commit_range`)."""
    if _ACTIVE is not None:
        _ACTIVE.set_commit_range(payload)


def record_commit_fixes_result(payload: Optional[Dict[str, Any]]) -> None:
    """Record the result line's ``commit_fixes``, if a dispatcher run is
    active; else a no-op (:meth:`ResultContext.set_commit_fixes`)."""
    if _ACTIVE is not None:
        _ACTIVE.set_commit_fixes(payload)


# ---------------------------------------------------------------------------
# The invocation record (what a detached child re-executes)
# ---------------------------------------------------------------------------

_INVOCATION: Optional[Dict[str, Any]] = None


def record_invocation(
    mode: str, argv: Sequence[str], *, plan_arg: Optional[str] = None
) -> None:
    """Remember the mode word and the **normalized** argv the dispatcher built.

    ``--detach`` rebuilds the child's command line from this rather than echoing
    ``sys.argv``, which is what keeps the detached worker identical whether the
    invoker was reached through a rendered shim, the ``"$MULTI_LLM_SKILL_DIR"``
    spelling or a direct call. Recording it here (instead of threading argv
    through every orchestrator signature) also means a direct
    ``python review_plan_orchestrator.py`` still works — it simply falls back to
    the argv its own ``main`` received.

    *plan_arg* is the plan as the user typed it, when that is not the argv's own
    ``--plan-file`` value (:func:`invocation_plan_arg`).
    """
    global _INVOCATION
    _INVOCATION = {"mode": mode, "argv": list(argv)}
    if plan_arg:
        _INVOCATION["plan_arg"] = str(plan_arg)


def clear_invocation() -> None:
    global _INVOCATION
    _INVOCATION = None


def invocation() -> Optional[Dict[str, Any]]:
    return _INVOCATION


def invocation_plan_arg() -> Optional[str]:
    """The plan as the user typed it, for this invocation, or ``None``.

    The record's ``plan_arg`` when the dispatcher recovered one — a
    continuation (:data:`CONTINUATION_VERBS`) whose ``--plan-file`` is the
    absolute path its hand-off printed, while the spelling the user typed is
    what the next-phase command must carry — else the ``--plan-file`` value the
    dispatcher received, verbatim.
    """
    record = _INVOCATION
    if not record:
        return None
    recovered = record.get("plan_arg")
    if recovered:
        return str(recovered)
    return flag_value(list(record.get("argv") or []), "--plan-file") or None


def typed_plan_for(plan: Union[str, Path]) -> str:
    """*plan* as this invocation's user typed it, when that spelling names it.

    What a native leg's printed hand-off names the plan with (fix round 14,
    racing run 5, Claude Code 03): generate-tasks' "then continue with: …
    generate-tasks /tmp/…/plans/racing-game.md --reaggregate" and its
    ``MULTI_LLM_RESULT.next`` carried the absolute path although the user
    typed ``plans/racing-game.md``, and the host ran and quoted it. The typed
    spelling (:func:`invocation_plan_arg`) is used only when
    ``next_phase.recorded_plan_spelling`` passes it — it resolves from this
    cwd to the same existing file and holds no character a shell would act
    on — else *plan* as given. Session-scoped like every printed command:
    nothing durable stores it.
    """
    typed = invocation_plan_arg()
    if typed:
        from .next_phase import recorded_plan_spelling

        spelling = recorded_plan_spelling(typed, str(plan))
        if spelling is not None:
            return spelling
    return str(plan)


# ---------------------------------------------------------------------------
# The replay-argv contract (D2): what a retry carries forward
# ---------------------------------------------------------------------------

def _option_table(dests: Iterable[str]) -> Dict[str, "Tuple[Tuple[str, ...], bool]"]:
    """``dest → (every option spelling, takes a value)`` off the parent parser.

    Derived, never hand-typed: ``--yes`` is also ``-y`` and ``--non-interactive``
    (one action, three spellings), and whether a token swallows the one after
    it is what argparse says its action does. A literal list here would be
    wrong the day it was written and wrong again at the next alias.
    """
    wanted = set(dests)
    table: Dict[str, Tuple[Tuple[str, ...], bool]] = {}
    for action in build_parent_parser()._actions:
        if action.dest in wanted:
            table[action.dest] = (tuple(action.option_strings), action.nargs != 0)
    missing = wanted - set(table)
    if missing:  # pragma: no cover - guarded by the parser definition
        raise RuntimeError(f"replay drop set names unknown dests: {sorted(missing)}")
    return table


#: The re-entry flags, dropped from every replay: the worker is re-executed with
#: them and a follow-up command must never carry one (``INTERNAL_FLAG_PREFIX``).
_REPLAY_DROP_ALWAYS = _option_table(("internal_worker", "internal_run_id"))

#: Dropped only when *implied*: ``--detach`` writes ``--yes`` and
#: ``--exec-subagents`` out explicitly (``multi_llm._apply_flag_implications``),
#: and ``build_worker_argv`` does the same under ``--internal-worker``, so in an
#: argv carrying either implier a typed spelling and an implied one are the same
#: token. The replay keeps the implier, whose re-dispatch re-implies both, and
#: drops the pair; without an implier every spelling is the caller's and stays.
_REPLAY_DROP_IMPLIED = _option_table(("yes", "exec_subagents"))
_REPLAY_IMPLIERS = _option_table(("detach", "internal_worker"))

#: What ``--internal-worker`` is replayed as: the ``--detach`` it replaced
#: (``detach.build_worker_argv`` swaps one for the other). Dropping it like the
#: other re-entry flag dropped the implier *and* the pair it implies, so a
#: detached worker's own retry line lost both ``--detach`` and
#: ``--exec-subagents`` — racing re-run 2026-10-04: a failed ``generate-tasks``
#: printed ``… generate-tasks <plan> --host codex --yes``, which run as printed
#: stops at ``[TASK_GENERATION_PENDING]`` and exits 0 having dispatched nothing,
#: while ``status``'s line (the launcher's list) said ``--detach``.
_REPLAY_WORKER = _option_table(("internal_worker",))
_DETACH_SPELLING = _REPLAY_IMPLIERS["detach"][0][0]
_REPLAY_YES = _option_table(("yes",))

#: The modes whose ``--yes`` already means ``--agent-decide`` (D6 row 10): the
#: apply phases set it in ``apply_orchestrator_base.apply_unattended_defaults``,
#: ``full`` hands it to them under ``--yes`` (``apply_flags``), and the
#: review-then-apply composites give their apply step ``--agent-decide``
#: always (``improve_workflow.step_flags``). The commit modes join under the
#: same rules (plans/review-commits.md §2.8): ``apply-commit-fixes`` runs
#: apply-code-fixes, and ``improve-commits`` is a review-then-apply composite.
YES_IMPLIES_JUDGE_MODES: FrozenSet[str] = frozenset({
    "apply-suggestions", "apply-task-suggestions", "apply-code-fixes", "full",
    "improve-plan", "improve-code", "apply-commit-fixes", "improve-commits",
})


def drop_implied_judge_flag(mode: str, tokens: Iterable[str]) -> List[str]:
    """*tokens* without the judge flag where ``--yes`` already implies it.

    In a *mode* of :data:`YES_IMPLIES_JUDGE_MODES`, a replay carrying ``--yes``
    — or ``--detach``/``--internal-worker``, which write it out — runs the
    same phase with ``--agent-decide`` as without it, and the decisions an
    earlier run recorded are replayed by ``--resume`` from ``state.json``,
    not by the flag. Kept, it made the two commands one needs-human result
    hands back disagree (OpenCode racing run 4): ``status``'s ``resume with:``
    line, offered as a tool call, read ``--agent-decide --resume`` while the
    result's ``resume_command`` read ``--resume``. Without ``--yes`` the flag is
    the caller's own choice and stays.
    """
    out = [str(token) for token in tokens]
    if mode not in YES_IMPLIES_JUDGE_MODES:
        return out
    heads = [token.split("=", 1)[0] for token in out]
    if not any(
        _matches_any(head, _REPLAY_YES) is not None
        or _matches_any(head, _REPLAY_IMPLIERS) is not None
        for head in heads
    ):
        return out
    return [token for token in out if canonical_flag(token) != AGENT_DECIDE_FLAG]

#: The positional-derived flags. Not parent-parser options, so named here next
#: to the derived half, pointing at their single producer:
#: ``multi_llm._normalize_positionals`` turns ``POS_PLAN`` into ``--plan-file``
#: and ``POS_QUESTION`` into ``--question``/``--question-file``
#: (``multi_llm._question_flags``). Every replay re-emits the plan from its own
#: argument; ``ask`` re-emits the question from ``.status.json``'s ``question``
#: field, never from the argv — the long form names a temp file the dispatcher
#: already unlinked, and the short form would make free text durable.
#: ``POS_HOST`` is forwarded as a positional and is not a flag at all.
#:
#: ``POS_REVS`` becomes ``--revs "<joined words>"`` (or ``--plan-file`` for a
#: commit brief's path), and a replay never carries the words as typed: a
#: phrase such as ``last two days`` names another range tomorrow, so every
#: record and command carries the pinned ``<base12>..<head12>`` instead
#: (plans/review-commits.md §2.2, "Ranges are pinned once resolved"). The
#: hidden ``--commit-stage <file>`` names one detached launch's staged brief
#: header and ``commit_range``, which the worker applies once and deletes
#: (§2.1, "Under ``--detach``"), so it is dropped the same way. Both take one
#: value.
_REPLAY_DROP_POSITIONAL: Dict[str, Tuple[Tuple[str, ...], bool]] = {
    "plan_file": (("--plan-file",), True),
    "question": (("--question",), True),
    "question_file": (("--question-file",), True),
    "revs": (("--revs",), True),
    "commit_stage": (("--commit-stage",), True),
}


#: The answers a replay never carries: ``implement``'s ``--human-task
#: <id>=done|skip|retry`` (its own parser, ``action='append'``, one value). A
#: ``done``/``skip`` is recorded in ``state.json``'s ``human_task_decisions``
#: and a plain ``--resume`` applies it again
#: (``implement_orchestrator._applicable_task_decisions``), and a ``retry`` is
#: one-shot. Replayed, the answer was both redundant and wrong (fix round 14,
#: live run 5): ``status``'s ``resume with:`` line, offered as the tool
#: route's first option, read ``--human-task T002=done --human-task T005=skip
#: --resume`` beside a ``resume_command`` of plain ``--resume`` — and run as
#: printed it is refused, since T005 is ``skipped`` by then and an answer is
#: taken only for a task still ``failed`` or held by a check.
_REPLAY_DROP_ANSWERS: Dict[str, Tuple[Tuple[str, ...], bool]] = {
    "human_task": (("--human-task",), True),
}


def drop_answer_flags(tokens: Iterable[str]) -> List[str]:
    """*tokens* without any ``--human-task`` answer (:data:`_REPLAY_DROP_ANSWERS`).

    For a stored replay list recorded before the answers were dropped at
    record time, so an older run's ``resume with:`` line reads the same.
    """
    out: List[str] = []
    items = [str(token) for token in tokens]
    index = 0
    while index < len(items):
        token = items[index]
        takes_value = _matches_any(token.split("=", 1)[0], _REPLAY_DROP_ANSWERS)
        if takes_value is None:
            out.append(token)
            index += 1
            continue
        index += 2 if (takes_value and "=" not in token) else 1
    return out


#: The flags a tool route composes on every call it makes, which a command
#: printed for its user never carries: exactly the ones the tool routes
#: reserve (``packaging/common/surface.py``'s ``reserved_flags``: ``exact``,
#: the ``named_exception`` and the ``--internal-`` prefix; a test holds the two
#: lists together). Fix round 18 (Codex racing run 7): ``status``'s
#: ``resume with:`` line was the raw ``uv run … --host codex --detach
#: --resume`` while every other next-step line was the host's spelling. A file
#: route composes less (:func:`file_route_composed_flags`).
_HOST_COMPOSED = _option_table((
    "host", "yes", "exec_subagents", "detach", "if_not_running",
    "max_detached", "interactive", "internal_worker", "internal_run_id",
))


def file_route_composed_flags(
    host_id: str,
) -> Dict[str, Tuple[Tuple[str, ...], bool]]:
    """The flags *host_id*'s own skill or shim composes on its file route.

    Read off the host's capability entry, the data its shim's dispatcher
    command and verb sentences are rendered from: ``--host`` (every one bakes
    it), ``--yes`` (an installable shim bakes it; Claude Code's SKILL.md does
    not, and offers ``--yes`` and ``--interactive`` to the user),
    ``--exec-subagents`` (the *spawn subagents* verb of an ``executor`` host)
    and ``--detach`` (the *run detached* verb of a host that is not
    ``native``: Claude Code never passes it). Fix round 19: the tool routes'
    reserved set was dropped on every route, so a Claude Code run the user
    started with ``--exec-subagents --yes`` printed a resume without them,
    which ran on the other leg, and the shims lost ``--interactive``, the one
    flag that replaces their baked ``--yes``. A test holds this to each
    host's template.
    """
    from . import host_capabilities

    entry = host_capabilities.entry(host_id)
    dests = ["host"]
    if entry.get("installable") is True:
        dests.append("yes")
    if entry.get("subagents") == "executor":
        dests.append("exec_subagents")
    if entry.get("detach") != "native":
        dests.append("detach")
    return _option_table(dests)


def replay_host(tokens: Iterable[str]) -> Optional[str]:
    """The ``--host`` value a replay list carries (any spelling argparse
    binds to it), or ``None``: the host whose skill or shim composed it."""
    items = [str(token) for token in tokens]
    table = _option_table(("host",))
    for index, token in enumerate(items):
        head, sep, value = token.partition("=")
        if _matches_any(head, table) is None:
            continue
        if sep:
            return value or None
        return items[index + 1] if index + 1 < len(items) else None
    return None


def drop_host_composed_flags(
    tokens: Iterable[str],
    composed: Optional[Dict[str, Tuple[Tuple[str, ...], bool]]] = None,
) -> List[str]:
    """*tokens* without the flags a host composes itself, each with its value,
    and without any ``--internal-`` flag: what is left is what the user typed,
    for a command spelled the way they type it. *composed* is the host's own
    set (:func:`file_route_composed_flags`); ``None`` is the tool routes'
    (:data:`_HOST_COMPOSED`)."""
    table = _HOST_COMPOSED if composed is None else composed
    out: List[str] = []
    items = [str(token) for token in tokens]
    index = 0
    while index < len(items):
        token = items[index]
        head = token.split("=", 1)[0]
        takes_value = _matches_any(head, table)
        if takes_value is None and head.startswith(INTERNAL_FLAG_PREFIX):
            takes_value = False
        if takes_value is None:
            out.append(token)
            index += 1
            continue
        index += 2 if (takes_value and "=" not in token) else 1
    return out


def _matches_any(head: str, table: Dict[str, Tuple[Tuple[str, ...], bool]]) -> Optional[bool]:
    """``takes_value`` for the table entry ``head`` binds to, else ``None``."""
    for names, takes_value in table.values():
        for name in names:
            if _flag_matches(head, name):
                return takes_value
    return None


def replay_flags(mode: str, argv: Sequence[str]) -> List[str]:
    """The flags a retry of *argv* carries forward, verbatim (D2 step 1).

    ``invocation()["argv"]`` is the dispatcher's **normalized** argv — the plan
    positional already spelled ``--plan-file <abs>``, ``--detach``'s
    implications written out — and, in a detached worker, the re-entry flags
    ``build_worker_argv`` appended. A naive slice yields a command with the plan
    named twice and an internal flag left in. This drops exactly:

    * the two re-entry flags (``--internal-run-id`` with its value), with
      ``--internal-worker`` replayed as the ``--detach`` it stands for;
    * the positional-derived flags, which every replay re-emits from its own
      arguments (``--plan-file``, ``--question``, ``--question-file``, the
      commit modes' ``--revs``), and the hidden ``--commit-stage``;
    * the dispatcher's own injections for this mode (``modes.injected_flags``
      and every alias's ``alias_flags``), which the replay's mode word
      re-derives;
    * ``--yes``/``--exec-subagents`` when an implier is present (see
      :data:`_REPLAY_DROP_IMPLIED`);
    * ``--agent-decide`` where ``--yes`` already means it
      (:func:`drop_implied_judge_flag`);
    * ``implement``'s ``--human-task`` answers, which ``state.json`` keeps
      (:data:`_REPLAY_DROP_ANSWERS`).

    Everything else stays, in the spelling it was typed, values with spaces
    included: ``--quick``, ``-q``, ``--models=a,b``, ``--host``, ``--detach``.
    Matching goes through :func:`_flag_matches`, so an argparse abbreviation is
    recognized rather than passed through as an unknown token. **Flags only**:
    no positional is ever recorded, by construction.
    """
    modes = _modes()
    injected = set(getattr(modes.resolve(mode), "injected_flags", ()) or ())
    for word, flags in getattr(modes, "ALIAS_FLAGS", {}).items():
        target = modes.resolve(word)
        if target is not None and target.name == mode:
            injected.update(flags)
    tokens = [str(t) for t in argv]
    implied = any(
        _matches_any(t.split("=", 1)[0], _REPLAY_IMPLIERS) is not None
        for t in tokens
    )
    out: List[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        head = token.split("=", 1)[0]
        if _matches_any(head, _REPLAY_WORKER) is not None:
            # The worker's stand-in for the launcher's `--detach`: replayed as
            # that flag, which re-implies the dropped pair (see _REPLAY_WORKER).
            if _DETACH_SPELLING not in out:
                out.append(_DETACH_SPELLING)
            index += 1
            continue
        takes_value = _matches_any(head, _REPLAY_DROP_ALWAYS)
        if takes_value is None:
            takes_value = _matches_any(head, _REPLAY_DROP_POSITIONAL)
        if takes_value is None:
            takes_value = _matches_any(head, _REPLAY_DROP_ANSWERS)
        if takes_value is None and implied:
            takes_value = _matches_any(head, _REPLAY_DROP_IMPLIED)
        if takes_value is None and head in injected:
            takes_value = False
        if takes_value is None:
            out.append(token)
            index += 1
            continue
        index += 2 if (takes_value and "=" not in token) else 1
    return drop_implied_judge_flag(mode, fold_judge_flag(out))


def current_replay_flags(
    stored: Any = None, *, mode: Optional[str] = None
) -> List[str]:
    """The replay flags this producer should print: **the live source wins**.

    When :func:`invocation` is populated *for the mode being replayed* the
    printing process is the run whose retry is being named, and its own argv is
    the truth — a ``--models a,b`` run resuming a phase whose document was
    written by yesterday's ``--quick`` run prints ``--models a,b``. Only a
    reader in some other process or mode (the file route; ``status`` on a run
    it did not launch, whose own ``--view run`` argv must never win; ``full``
    driving a phase in-process) falls through to *stored*, a document's
    ``replay_flags`` list, which is emitted as recorded and never sanitized
    against today's parser. Absent or malformed decodes to ``[]``.
    """
    record = invocation()
    if record and record.get("mode") and (mode is None or record["mode"] == mode):
        return replay_flags(str(record["mode"]), record.get("argv") or [])
    if isinstance(stored, (list, tuple)):
        folded = fold_judge_flag(drop_answer_flags(stored))
        # A list recorded before the judge flag was dropped from `--yes`
        # replays reads the same as one recorded after.
        return drop_implied_judge_flag(mode, folded) if mode else folded
    return []


# ---------------------------------------------------------------------------
# The retry's shape (D2 step 4): classification, never a count
# ---------------------------------------------------------------------------

#: A config or credential fault — a ``RunnerRejected`` reason code, or a fatal
#: per-task status such as ``invalid_model``. The repair is named first; the
#: single tool call (recorded flags + ``--reaggregate``) is offered *after* it.
SHAPE_REPAIR = "repair"
#: Transient or retryable — timeout, rate limit, spawn failure, an unclassified
#: parse failure. Nothing to edit: the same ``--reaggregate`` call, plus its cost.
SHAPE_REAGGREGATE = "reaggregate"
#: The fan-out's own artifacts are unusable — the one shape in which ``--force``
#: is a *command* rather than a sentence, because the reviewer pass really is
#: what has to run again.
SHAPE_FORCE = "force"


def retry_shape(
    *,
    reason_code: Optional[str] = None,
    statuses: Iterable[str] = (),
    artifacts_ok: bool = True,
) -> str:
    """Which of the three exit-3 shapes a failure gets. Takes values, never paths.

    It opens no file, so no producer can quietly acquire a classification by
    going to look for a document — the stale-report hazard D4 step 5 names.
    Each site supplies what it legitimately holds: ``continue_past_marker`` the
    statuses of the report *it* was returned plus artifact validity; the
    ``except ExecutorError`` handler the refusal's ``reason_code``; ``status``
    the run record's close-out or the ``progress.subagents`` mirror. Neither a
    success count nor ``report.ok`` decides anything here: both are equally
    consistent with a dead model id and a rate limit.
    """
    from .retry_ladder import FATAL_STATUSES

    if not artifacts_ok:
        return SHAPE_FORCE
    if reason_code:
        return SHAPE_REPAIR
    if set(statuses) & FATAL_STATUSES:
        return SHAPE_REPAIR
    return SHAPE_REAGGREGATE


#: What a fatal per-task status asks to be repaired, in one clause each. Keyed
#: by the ``retry_ladder.FATAL_STATUSES`` spellings; an unknown fatal status
#: falls back to naming itself.
_FATAL_STATUS_REPAIR: Dict[str, str] = {
    "invalid_model": "the runner's model id is not one its CLI accepts — fix "
                     "driver.subagent_runner (or the provider's model list)",
    "auth_failed": "the runner's CLI is installed but not logged in — no retry "
                   "can supply a missing credential",
    "spawn_failed": "the runner's CLI could not be started — check the binary "
                    "is on PATH and executable",
    "sandbox_unavailable": "the runner's own sandbox cannot write on this "
                           "machine — run `multi_llm.py doctor` for the repair",
}


def repair_sentence(
    *,
    reason_code: Optional[str] = None,
    explanation: Optional[str] = None,
    counts: Optional[Dict[str, int]] = None,
    statuses: Iterable[str] = (),
) -> str:
    """Shape 1's lead sentence: what must change before the retry is worth it.

    A reason code names the refusal (with ``_REASON_EXPLANATION``'s sentence
    when the caller supplies it); otherwise the fatal statuses present are
    named, with their counts when known. Takes values, never paths.
    """
    from .retry_ladder import FATAL_STATUSES

    if reason_code:
        return f"{reason_code}: {explanation}" if explanation else str(reason_code)
    tally: Dict[str, int] = dict(counts or {})
    for status in statuses:
        tally.setdefault(status, 0)
    parts = []
    for status in sorted(s for s in tally if s in FATAL_STATUSES):
        n = tally.get(status) or 0
        head = f"{n} task(s) ended {status}" if n else f"tasks ended {status}"
        parts.append(f"{head} — {_FATAL_STATUS_REPAIR.get(status, 'fix the runner it names')}")
    return "; ".join(parts) or "fix what the message names"


def retry_options(
    shape: str,
    *,
    reaggregate: str,
    force: str,
    repair: Optional[str] = None,
    redispatch: Optional[int] = None,
    kept: Optional[int] = None,
) -> List[str]:
    """The numbered option sentences one shape prints, in rank order.

    One renderer for every in-process site, so the two shapes that demote
    ``--force`` to a sentence do so in the same words. *reaggregate* and
    *force* are the two commands already built through :func:`retry_command`;
    *repair* is the sentence shape 1 leads with (``_REASON_EXPLANATION`` for a
    reason code, or the fatal status by name). Only the ranked-first command
    is spelled as a runnable string in shapes 1 and 2, which is what keeps a
    host's option scrape (``toolCallsFor``) to one retry tool call.
    """
    cost = ""
    if redispatch is not None:
        cost = f" — it re-dispatches {redispatch} task(s)"
        if kept is not None:
            cost += f" and keeps the {kept} valid result(s) already on disk"
    options: List[str] = []
    if shape == SHAPE_FORCE:
        options.append(
            f"The fan-out's own results are unusable, so the reviewer pass has "
            f"to run again: re-invoke with `{force}`."
        )
        return options
    if shape == SHAPE_REPAIR:
        options.append(f"Repair first: {repair or 'fix what the message names'}.")
        options.append(
            f"Then re-invoke with `{reaggregate}`{cost}; --force is not needed "
            f"and would re-run the reviewer panel."
        )
        return options
    options.append(f"Re-invoke with `{reaggregate}`{cost}.")
    options.append(
        "Add --force only if you also want the reviewer panel re-run; the "
        "existing reviewer results are fine."
    )
    return options


def parse_result_line(text: str) -> Optional[Dict[str, Any]]:
    """Parse the ``MULTI_LLM_RESULT`` line out of captured stdout, if present."""
    for line in reversed(text.splitlines()):
        stripped = line.strip()
        if stripped.startswith(RESULT_MARKER):
            return json.loads(stripped[len(RESULT_MARKER):].strip())
    return None


# ---------------------------------------------------------------------------
# argv inspection (used by the dispatcher's parse-time rejection rules)
# ---------------------------------------------------------------------------

#: Every long option this skill registers that is a **strict prefix** of another
#: one — i.e. the only tokens whose exact spelling an abbreviation scan can
#: misread. argparse resolves an exact match *before* it considers any
#: abbreviation, so ``--force`` on a command line is ``--force`` and never a
#: shorter way of typing ``--force-strategy``; without this set the scan bound the
#: token after ``--force`` as the strategy value. Derived mechanically from every
#: ``add_argument`` in the runtime tree (``tests/test_unattended.py`` recomputes it
#: and fails on drift), and deliberately a union across parsers rather than the one
#: parser argparse will really use: a name missing here just keeps the old
#: over-reporting, which leaves a guard closed rather than open.
_EXACT_OPTIONS: FrozenSet[str] = frozenset({
    "--all", "--approve-all", "--consolidate", "--dry-run", "--files", "--force",
    "--host", "--mode", "--output", "--phase", "--project", "--question",
    "--reaggregate", "--revalidate", "--skip", "--summary", "--task",
})


def _flag_matches(head: str, name: str) -> bool:
    """Whether the option-name token ``head`` would bind to option ``name``.

    Exact spelling **or an argparse abbreviation**: no parser in the skill passes
    ``allow_abbrev=False``, so argparse resolves ``--y``, ``--intera`` and
    ``--det`` to their full options — and a dispatcher rule that scanned for the
    exact spelling only was therefore bypassable by typing three fewer
    characters. ``--det`` on a mode that does not support ``--detach`` sailed
    past the D6b rejection and ran the mode with a flag that does nothing, which
    is precisely the outcome that rejection exists to prevent.

    ``allow_abbrev`` cannot be fixed from *this* side of the call: it is a
    property of the parser doing the parsing (and is **not** inherited through
    ``parents=[...]``), so the scan is what is taught argparse's rule instead —
    one place rather than one per parser, and it stays correct for the
    orchestrator parsers a direct invocation reaches too.

    Abbreviation is long-option only (argparse never abbreviates a short flag),
    and a token is only ever matched against a *longer* name, so a real
    ``--host-something`` never reads as ``--host``. A prefix that is ambiguous
    across the target's real options (``--d`` for ``--detach`` and
    ``--dry-run-subagents``) is reported present here where argparse would
    instead refuse the whole command line: both end the run at exit 3, and
    over-reporting keeps the guard closed rather than open.

    An **exact spelling of a different real option is not an abbreviation** —
    argparse binds it to itself and never considers the longer name, so a command
    line carrying ``--force`` must not read as ``--force-strategy <next token>``
    (see :data:`_EXACT_OPTIONS`). Where the token really *is* the abbreviation
    argparse resolves — ``--force`` on ``implement``, whose parser registers
    ``--force-strategy`` and no ``--force`` — the mode's own post-parse check is
    the layer that refuses it (``implement_orchestrator.main``), so nothing is
    left ungated by scanning it the argparse way here.
    """
    if head == name:
        return True
    if not name.startswith("--"):
        return False  # short options never abbreviate
    if not head.startswith("--") or len(head) <= 2:
        return False  # bare `--`, a short flag, or a positional
    if head in _EXACT_OPTIONS:
        return False  # a real option spelled in full, not a prefix of this one
    return name.startswith(head)


def flag_present(argv: Sequence[str], *names: str) -> bool:
    """True if any of ``names`` appears in ``argv``, bare or as ``--flag=value``.

    Matches the way argparse would — see ``_flag_matches`` for why an
    abbreviation counts.
    """
    for token in argv:
        head = token.split("=", 1)[0]
        for name in names:
            if _flag_matches(head, name):
                return True
    return False


def flag_value(argv: Sequence[str], name: str) -> Optional[str]:
    """The value of ``--name value`` or ``--name=value``, else ``None``.

    The **last** occurrence wins, because that is what a ``store`` action does:
    reading the first meant ``--force-strategy skip-dependents --force-strategy
    pause-and-ask`` scanned as ``skip-dependents`` while the run really got
    ``pause-and-ask``. Abbreviations bind here too (``--force-strat=…``); a
    trailing occurrence with no value left to take is argparse's error to report
    and never erases a value an earlier one supplied.
    """
    found: Optional[str] = None
    for index, token in enumerate(argv):
        head, separator, inline = token.partition("=")
        if not _flag_matches(head, name):
            continue
        if separator:
            found = inline
        elif index + 1 < len(argv):
            found = argv[index + 1]
    return found
