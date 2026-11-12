#!/usr/bin/env python3
"""``multi_llm.py status <plan>`` — two views, two files, one command word.

This *replaces* the instruction-only ``--status`` mode rather than sitting beside
it, and extends the surface that mode already exposed instead of inventing one.
Three distinct things existed before, and the distinction is load-bearing:

1. ``--status``, a **mode word** with no Python behind it, whose markdown wrapper
   shelled out to ``check_workflow_prerequisites.py --status`` →
   ``get_workflow_status``, printing a phase map built from **``state.json``**.
   That function survives here as the *workflow view's implementation*, unchanged
   and still directly callable by its existing tests: ``status <plan> --view
   workflow --json`` is byte-identical to what it prints today.
2. ``{phase}/.status.json``, the **orchestrator checkpoint**, whose top-level
   ``state`` is the in-phase machine and whose ``run`` object (added by
   ``--detach``) is the process machine. That is the *run view*.
3. ``state.json`` itself, the durable per-plan workflow record behind (1).

**Two questions, one word.** ``workflow`` answers *what phase comes next?* and
``run`` answers *is the run I launched still alive?*. Giving the heartbeat its own
command word was rejected: the two are read at the same moments (a poller checks
the run, then reads the workflow view to choose the next phase), a second word
would need its own plan/``--phase``/ask selectors and its own exit-code table, and
the pair would drift the first time one gained a selector the other lacked. What a
separate word buys — no ambiguity about which state you are being shown — is
bought instead by ``--view``: no output ever blends the two, and the three state
fields (workflow phase completion, in-phase ``state``, process ``run.state``) are
printed on three separate lines and never collapsed.

**Neither view is authoritative over the other; there is no precedence rule.**
Liveness comes only from the run view, phase completion only from the workflow
view. The one case that looks like a conflict — a finished run under a phase
``state.json`` still calls ``pending`` — is the normal post-run condition, and it
is reported as such rather than resolved by ranking one file over the other.

**This command takes no lock and writes nothing** (bar one exception, below), so
it works *while* another run owns the phase dir — which is the whole point of a
poll loop. The exception is the deliberate close-out of a run whose heartbeat
expired and whose process is provably gone: without it a phase dir would sit at
``running`` forever after a reboot. ``--abort`` and ``--sweep`` are verbs, and they
say so.

**One job per module.** This module is the command: its parser, the plan
value, ``main`` and its stages, ``--wait``, ``--abort`` and ``--sweep``. What
a view is and which ones a poll lists is ``status_views``; the commands it
prints, ``status_commands``; the phases a native host ran, ``status_native``;
the text, ``status_text`` (docs/development/status.md#how-status-is-built).
Every name that moved there is still readable here (:data:`_MOVED`), **for
reading only**: ``run_status.X`` and ``from .run_status import X`` return the
owner's current object, but a patch or assignment here only shadows the name
in this module and reaches no code. Patch a moved name where it lives;
``tests/test_run_status_moved_names.py`` fails any test that patches one here.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import (
    detach,
    host_capabilities,
    status_commands,
    status_file,
    status_native,
    status_text,
    status_views,
)
from .advisory import note_swallowed
from .cli_common import (
    ERROR_MAX_CHARS,
    EXIT_ERROR,
    EXIT_NEEDS_HUMAN,
    EXIT_NOTHING_TO_DO,
    EXIT_OK,
    STATE_DIED,
    STATE_RUNNING,
    build_parent_parser,
    dispatcher_command,
    keep_state_word,
    record_answer_origins,
    record_artifact,
    record_commit_fixes_result,
    record_consolidation_recommended,
    record_error,
    record_high_priority_groups,
    record_mode_phase,
    record_next,
    record_notice,
    record_progress,
    record_progress_lines,
    record_state,
    record_validation_context,
    record_validation_counts,
    _modes,
)
from .output_handler import PHASE_DIR_NAMES, output_dir_path
from .stream_bootstrap import bootstrap_streams
from .text_clip import clip, drop_said_clauses, join_clauses, plain_line
from .validation_context import pick_worst


#: ``--wait``'s default. Deliberately under the tightest surveyed host shell cap
#: (OpenCode's ~120 s): it compresses the poll loop into one turn, it never
#: replaces the terminal-state check, and it is never emitted for a host whose
#: shell cap is below its own timeout.
DEFAULT_WAIT_TIMEOUT_S = 90.0

#: How far *below* a host's ``timeout_ceiling_s`` a resolved ``--wait`` is
#: clamped. This is the number that explains :data:`DEFAULT_WAIT_TIMEOUT_S`:
#: OpenCode's ceiling is 120 s and 120 - 30 = 90.
#:
#: The margin is **startup, not slack**. A poll spends process start,
#: ``load_config`` and the checkpoint read before ``--wait`` begins sleeping, and
#: ``_wait_for_terminal`` re-checks on a ``status_file.WAIT_POLL_INTERVAL_S`` grid, so it
#: returns a little *after* its own deadline — clamping to the cap itself would
#: put the return on the wrong side of it. The same constant bounds the tool-call
#: ``timeout`` a Claude Code poll has to set (``interval + 30``).
#:
#: **Re-exported, not defined here** (F6, 2026-09-20). The comment this replaces
#: said the number was "named once here rather than twice so the two cannot
#: drift"; it was in fact typed out in six places — this constant, the ``native``
#: *run detached* sentence, ``SKILL.md``, ``references/host-capabilities.md`` and
#: four instruction cores — so "30" could have been moved here and left standing
#: on every surface an agent actually reads. It is owned by
#: :data:`host_capabilities.WAIT_CAP_MARGIN_S`, beside the ceilings it is
#: subtracted from; the verb sentence interpolates it (carrying ``SKILL.md`` and
#: the generated reference with it) and the four cores are pinned against it by
#: ``tests/test_instruction_portability.py``.
WAIT_CAP_MARGIN_S = host_capabilities.WAIT_CAP_MARGIN_S

VIEW_WORKFLOW = "workflow"
VIEW_RUN = "run"
VIEW_ALL = "all"


class _WaitTimeoutRefused(Exception):
    """``--wait`` cannot resolve a deadline it would be honest to wait on.

    Its one job is to reach :func:`main` as a *message*, so the refusal prints
    the ``ERROR:`` + exit 3 shape this codebase uses for "needs a human" instead
    of whatever the raising layer's own exception would have become. Raised for
    two unrelated causes with one disposition (F4/F7, 2026-09-20): a
    ``ConfigError`` from anywhere in the config document, and a ``--timeout``
    that is not a positive finite number. Both are a human's edit or a human's
    command line, neither says anything about the run being polled, and exit 1
    — which is what both used to produce — is read by the poll loop as "the run
    state is unreadable, stop and report".
    """


# ---------------------------------------------------------------------------
# The names that moved to the status modules beside this one
# ---------------------------------------------------------------------------

#: Every top-level name of the four modules split out of this one, by owner.
#: They are read-only re-exports (see the module docstring): reading one here
#: returns the owner's current binding, and ``dir()`` lists them. Nothing is
#: copied into this module, so a patch of the owner shows through here, and
#: this module's own code reaches each one through its owner at every call.
_MOVED: Dict[str, Tuple[str, ...]] = {
    "status_views": (
        "CHECKPOINT_TERMINAL_STATES",
        "CHECKPOINT_TERMINAL_STEPS",
        "ENDED_IN_FOREGROUND",
        "FOREGROUND_LOCKED_PHASES",
        "GENERIC_NEEDS_HUMAN_ERROR",
        "STOPPED_IN_FOREGROUND",
        "STOPPED_STEP",
        "_IMPLEMENT_PHASE",
        "_a_dispatch_failed",
        "_ask_dirs",
        "_checkpoint_in_flight",
        "_dedupe_run_ids",
        "_died",
        "_document_file_label",
        "_document_word",
        "_failed_model_specs",
        "_foreground_run_gone",
        "_is_ask",
        "_is_executor_implement_view",
        "_names_this_run",
        "_result_state",
        "_run_is_live",
        "_select",
        "_stopped_for_the_user",
        "_view_dir_name",
        "_workflow_payload",
        "discover_phase_dirs",
        "exit_code_for",
        "ignored_phase_dirs",
    ),
    "status_commands": (
        "NO_RESUME_BEFORE_DISPATCH",
        "Speller",
        "_REAGGREGATE_MODES",
        "_RESUME_VERB_BY_MODE",
        "_WRITE_MODES",
        "_abort_command",
        "_composite_resume_tokens",
        "_dispatched_nothing",
        "_failed_batches_moved_nothing",
        "_implement_tasks_done",
        "_manual_gate_answers",
        "_phase_in_progress",
        "_reason_explanation",
        "_rerun_command",
        "_resume_command",
        "_resume_lines",
        "_resume_shape",
        "_retry_command",
        "_run_route",
        "_run_runner_facts",
        "_stale_review_of",
        "_stop_resume_why",
        "_view_speller",
        "_write_mirror_as_counts",
        "render_runner_text",
        "user_speller",
        "why_line",
    ),
    "status_native": (
        "NATIVE_APPLY_PHASES",
        "NATIVE_PHASE_ORDER",
        "NATIVE_STOPPED_VERDICT",
        "STILL_RUNNABLE_IDS_SHOWN",
        "_FAILED_BATCH_WORDS",
        "_NOT_APPLIED_ITEM_WORDS",
        "_SINGLE_TARGET_APPLY_PHASES",
        "_WRITE_REPORT",
        "_WRITE_TASKS",
        "_accepted_reruns_by_task",
        "_earlier_run_lines",
        "_failed_batch_reason",
        "_host_run_started_at",
        "_implement_buckets",
        "_native_apply_batch_checks",
        "_native_apply_not_applied",
        "_native_emit_time",
        "_native_head",
        "_native_manual_gate",
        "_native_resume_line",
        "_native_single_target",
        "_native_stop_lines",
        "_reason_after",
        "_run_started_after_native_emit",
        "_state_changed_at",
        "_still_runnable_clause",
        "_write_phase_of",
        "accepted_rerun_clauses",
        "earlier_run_record",
        "failed_batch_clause",
        "implement_tally_text",
        "implement_task_tally",
        "native_items_count",
        "native_leg_stamp",
        "native_resume_command",
        "native_run_stopped",
        "native_still_runnable",
        "native_stop_answer_commands",
        "not_applied_item_clauses",
        "render_state_apply_lines",
        "render_state_implement_lines",
        "repeated_check_clauses",
        "set_aside_superseded_runs",
        "state_apply_views",
        "state_implement_view",
        "superseded_by_native",
    ),
    "status_text": (
        "INCIDENTAL_RUNG_IDS",
        "JAIL_DENIED_PATH_KEY",
        "JAIL_DENIED_REASON",
        "JUST_FINISHED_LABEL",
        "NOTHING_CRASHED",
        "NO_PROGRESS_RECORDED",
        "SKIPPED_SOURCES",
        "STOPPED_FOR_THE_USER_GLOSS",
        "STOPPED_FOR_THE_USER_VERDICT",
        "STOPPED_RUN_STATE_WORD",
        "_attach_finished_during_wait",
        "_consolidation_text",
        "_current_state_text",
        "_entry_error_text",
        "_fallback_clause_head",
        "_generated_count",
        "_has_live_row",
        "_high_priority_text",
        "_id_list",
        "_ignored_text",
        "_just_finished_text",
        "_kept_labels",
        "_kept_text",
        "_mirror_text",
        "_model_detail_text",
        "_model_row_specs",
        "_model_state_label",
        "_model_table_lines",
        "_model_timing_text",
        "_one_line",
        "_progress_lines",
        "_progress_text",
        "_run_notes",
        "_run_state_text",
        "_terminal_fingerprints",
        "_validation_context_notice",
        "_validation_context_text",
        "_verdict_text",
        "_workflow_trailer_lines",
        "_write_result_notice",
        "_write_result_notice_parts",
        "manual_close_note",
        "render_run_text",
        "render_workflow_text",
    ),
}
_MOVED_TO: Dict[str, str] = {
    name: module for module, names in _MOVED.items() for name in names
}


def __getattr__(name: str) -> Any:
    """A moved name, read from the module that defines it now."""
    owner = _MOVED_TO.get(name)
    if owner is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    try:
        return getattr(globals()[owner], name)
    except AttributeError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None


def __dir__() -> List[str]:
    """This module's own names and the moved ones it re-exports."""
    return sorted({*globals(), *_MOVED_TO})


def _reader_host(args) -> str:
    """The host this invocation reads as: ``--host``, else the usual ladder."""
    return host_capabilities.resolve_host_id(explicit=getattr(args, "host", None))


def _plan_spelling(
    args: argparse.Namespace, views: Sequence[Dict[str, Any]], plan_path: Path,
) -> str:
    """The plan as its user typed it, for a command this view prints.

    A poll pinned to one run takes that run's recorded ``plan_arg`` when
    ``next_phase.recorded_plan_spelling`` passes it (a tool route polls with
    the absolute path); anything else is the plan as this call received it.
    """
    # Imported here to keep run_status light.
    from . import next_phase

    pinned = _pinned_view(args, views)
    if pinned is not None:
        recorded = next_phase.recorded_plan_spelling(
            (pinned.get("run") or {}).get("plan_arg"), str(plan_path),
        )
        if recorded:
            return recorded
    return str(args.plan_file)


def _recorded_route(
    args: argparse.Namespace, views: Sequence[Dict[str, Any]], plan_path: Path,
) -> Optional[str]:
    """The route the commands of this view's plan were started on (fix round
    24): a poll pinned to one run takes that run's record (:func:`_run_route`),
    anything else the newest run of the reader's host under the plan
    (``next_phase.recorded_route``). ``None`` when none is on record."""
    # Imported here to keep run_status light.
    from . import next_phase

    host = _reader_host(args)
    pinned = _pinned_view(args, views)
    if pinned is not None:
        return status_commands._run_route(pinned, host)
    return next_phase.recorded_route(plan_path, host)


def _pinned_view(
    args: argparse.Namespace, views: Sequence[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """The one run this poll names: the single listed view under ``--phase``,
    ``--question`` or ``--run-id``, else ``None`` (a listing has no single
    run to answer for). A pinned poll carries that run's own fields on its
    result line (docs/development/status.md#how-status-is-built)."""
    if len(views) == 1 and (args.phase or args.question or args.run_id):
        return views[0]
    return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="multi_llm.py status",
        description=(
            "Report a plan's workflow phases (state.json) and its detached runs "
            "({phase}/.status.json). One command, two named views, one vocabulary."
        ),
        parents=[build_parent_parser(include_interactive=False)],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "exit codes: 0 = terminal and successful | 2 = non-terminal (still "
            "running, or no run recorded) | 3 = terminal and needs a human | 1 = "
            "the phase dir could not be read.\n\n"
            "The exit code IS the poll-loop condition; with --wait the waiting "
            "is already in the call, so poll again on 2 from your own turn loop "
            "and never put `sleep` and `status` in the same shell call."
        ),
    )
    parser.add_argument("--plan-file", required=True, help="Path to the plan file")
    parser.add_argument(
        "--view", choices=[VIEW_WORKFLOW, VIEW_RUN, VIEW_ALL], default=VIEW_ALL,
        help="Which layer to report (default: all)",
    )
    parser.add_argument(
        "--phase", "--mode", dest="phase", default=None,
        help="Scope the run view to one phase dir. Accepts a mode word or a "
             "phase name (review-code and code-review both work).",
    )
    parser.add_argument(
        "--question", default=None,
        help="Select one ask run by its exact question text",
    )
    parser.add_argument(
        "--run-id", dest="run_id", default=None,
        help="Select one run by id (a unique prefix is enough)",
    )
    parser.add_argument(
        "--all", dest="include_all", action="store_true",
        help="Include historical terminal runs (ask dirs list only the latest by default)",
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    parser.add_argument(
        "--wait", action="store_true",
        help=f"Poll internally until the run is terminal or --timeout elapses "
             f"(default {DEFAULT_WAIT_TIMEOUT_S:.0f}s, deliberately under the "
             "tightest host shell cap), then return the non-terminal view with exit 2",
    )
    parser.add_argument(
        # A SENTINEL, not a value: `None` is what lets `main` tell "the caller
        # asked for this many seconds" from "the caller said nothing", which is
        # the whole of the resolution order below (and of which of the two
        # clamps is loud). Carrying `DEFAULT_WAIT_TIMEOUT_S` here instead would
        # make `progress.poll_s` unreachable — argparse would have already
        # answered the question.
        "--timeout", type=float, default=None,
        help=f"--wait timeout in seconds (default: progress.poll_s, else "
             f"{DEFAULT_WAIT_TIMEOUT_S:.0f}s; clamped under the host's shell cap)",
    )
    parser.add_argument(
        "--abort", action="store_true",
        help="Stop the selected detached run(s): identity probe, process-group "
             "SIGTERM, 10s, SIGKILL, then run.state: aborted. It reaches a run "
             "that recorded one: a foreground run holds no run record, so there "
             "it answers `nothing was running` and the kill path is the host's "
             "own background job handle.",
    )
    parser.add_argument(
        "--sweep", action="store_true",
        help="Close out every run under this plan whose process is gone",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="With --abort: stop a run whose identity probe is inconclusive",
    )
    parser.add_argument(
        # Fix round 7: Claude Code shows any non-zero exit as a tool error, and
        # on that host every phase runs in the foreground, so a plain report
        # is exit 2 ("no run recorded") every time. Opt-in, so the exit code
        # stays the poll-loop condition for every caller that does not ask.
        "--exit-zero", dest="exit_zero", action="store_true",
        help="Exit 0 whenever the status was read, whatever the run's state "
             "(still exit 1 when it could not be read, and 3 for a bad flag): "
             "for a call that reports and does not poll, on a host that shows "
             "any non-zero exit as an error. The run's state stays in the text "
             "and in the result line's `state`. Never on a poll whose loop "
             "reads the exit code.",
    )
    # Accepted so the pre-dispatcher spelling (`--status`) keeps working; the
    # views make it redundant.
    parser.add_argument("--status", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args(list(argv) if argv is not None else None)


def _resolve_phase(word: Optional[str]) -> Optional[str]:
    """Resolve ``--phase``/``--mode`` through the mode table (mode word or phase).

    Also accepts the on-disk phase-*directory* word for a phase whose directory
    name differs from its ``modes.py`` phase name (``apply-code-fixes`` is the
    only one today, dir ``apply-fixes``) — a human polling by eye reads the
    directory, not the phase table, and ``PHASE_DIRECTORIES`` is the one place
    that mapping is recorded. Returned as-is: ``phase_dir_path``'s own identity
    fallback resolves a dir word that is already a ``PHASE_DIRECTORIES`` key.

    An unknown selector is a *usage* error, so it exits **3** like every other
    "this run cannot proceed without a human" case (D1a, and this command's own
    epilog) rather than the exit 1 a string-valued ``SystemExit`` would be mapped
    to — a shim must be able to tell a mistyped ``--phase`` from a status command
    that genuinely failed to read the phase dir. The message goes to stderr
    because ``--json``'s stdout has to stay parseable.
    """
    if not word:
        return None

    modes = _modes()
    resolved = modes.phase_from_selector(word)
    # The directory words read the same tuple discovery does
    # (`PHASE_DIR_NAMES`, plan §7.4a), so the two cannot drift.
    if resolved is None and word in PHASE_DIR_NAMES:
        resolved = word
    if resolved is None:
        valid = list(modes.phase_names()) + sorted(
            set(PHASE_DIR_NAMES) - set(modes.phase_names())
        )
        print(
            f"ERROR: unknown phase or mode '{word}'. Valid phases: "
            + ", ".join(valid),
            file=sys.stderr,
        )
        raise SystemExit(EXIT_NEEDS_HUMAN)
    return resolved


def _scope_label(args: argparse.Namespace) -> Optional[str]:
    """What the caller asked about, so "nothing found" names it."""
    if args.run_id:
        return f"run {args.run_id}"
    if args.question:
        return f"question {args.question!r}"
    if args.phase:
        return f"phase {args.phase}"
    return None


def _discovery_report(plan_path: Path, args: argparse.Namespace) -> Dict[str, Any]:
    """What discovery skipped (plan §7.4a2/b), for the text line and ``--json``.

    ``ignored_dirs``: non-phase children holding a ``.status.json``, listed only
    when no ``--phase`` pins one directory. ``copies``: dirs whose run id another
    phase dir already carries (:func:`_dedupe_run_ids`). Reads the checkpoints
    directly — no classification, no close-out — so it never writes.
    """
    phase = _resolve_phase(args.phase)
    stubs: List[Dict[str, Any]] = []
    for directory in status_views.discover_phase_dirs(plan_path, phase=phase):
        try:
            status = status_file.read_status(str(directory))
        except Exception as exc:
            note_swallowed("status: discovery report", exc)
            continue
        run = status.get("run") if isinstance(status.get("run"), dict) else {}
        stubs.append(
            {"phase_dir": str(directory), "phase": status.get("phase"), "run": run}
        )
    return {
        "ignored_dirs": [] if phase else status_views.ignored_phase_dirs(plan_path),
        "copies": status_views._dedupe_run_ids(stubs)[1],
    }


def _collect(plan_path: Path, args: argparse.Namespace) -> List[Dict[str, Any]]:
    phase = _resolve_phase(args.phase)
    views = [
        detach.classify_run(str(directory))
        for directory in status_views.discover_phase_dirs(plan_path, phase=phase)
    ]
    # Plan §7.4b: two views with one run id are one run.
    views = status_views._dedupe_run_ids(views)[0]
    return status_views._select(
        views,
        run_id=args.run_id,
        question=args.question,
        include_all=args.include_all,
    )


#: What ``status`` takes for a commit review, said in its refusal of any other
#: range text (plans/review-commits.md §2.2, "``status`` takes the pinned
#: spelling").
_STATUS_TAKES_PINNED = (
    "status takes a commit review only by its pinned range <base12>..<head12> "
    "or by its commit brief's path, as the commit block, [COMMIT_BRIEF] and "
    "the result line print them. It never resolves a range: a phrase or a "
    "revision would name today's range, not the one the run reviewed."
)


class StatusSpellingRefused(Exception):
    """A ``status`` plan value that names a commit range ``status`` will not
    resolve; ``message`` is printed whole, its first line starting with the
    marker."""

    def __init__(self, message: str, exit_code: int = EXIT_NEEDS_HUMAN):
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code


def _holds_range_dots(text: str) -> bool:
    """Whether *text* holds ``..`` as range syntax rather than as a path
    segment: ``HEAD~2..HEAD``, ``A..``, ``..B`` and the displayed
    ``root..<head7>`` do, ``../plans/x.md`` does not (that is a plan path that
    is missing, and keeps ``Plan file not found``)."""
    return any(
        ".." in segment and segment != ".."
        for segment in text.replace("\\", "/").split("/")
    )


def status_plan_value(value: str) -> str:
    """The plan path ``status`` reads for *value*, its one positional as typed.

    ``status`` keeps its ``POS_PLAN`` row, so none of the commit modes'
    range rules run for it; it maps the value here, before the existence
    check, and resolves nothing (plans/review-commits.md §2.2):

    * an existing path is taken as it is, as before: a plan, or a commit
      brief, which is also a root range's pinned spelling;
    * the pinned ``<base12>..<head12>`` names its brief by name
      (``commit_paths.brief_for_pinned``, no git call), so every view,
      ``--abort`` and ``--sweep`` see the brief; with no brief there it is
      exit 3 ``[COMMIT_REVIEW_NOT_FOUND]``, naming the review that makes one;
    * other range text, ``..`` syntax or a phrase the pure phrase matcher
      recognizes (``commit_range.match_phrase``), is exit 3
      ``[RANGE_UNRECOGNIZED]``;
    * anything else comes back unchanged, for ``Plan file not found``.

    Raises :class:`StatusSpellingRefused` for the two refusals.
    """
    if os.path.exists(value):
        return value
    # Imported here to keep run_status light.
    from . import commit_paths, commit_range

    try:
        brief = commit_paths.brief_for_pinned(value)
    except Exception as exc:  # noqa: BLE001 - no folder to find it in
        raise StatusSpellingRefused(
            f"[COMMIT_REVIEW_NOT_FOUND] {value}: {' '.join(str(exc).split())}"
        ) from exc
    if brief is not None:
        if Path(brief).exists():
            return str(brief)
        raise StatusSpellingRefused(
            f"[COMMIT_REVIEW_NOT_FOUND] {value}: no commit brief at {brief}\n"
            f"No review of that range is on record here; review it with: "
            f"--review-commits {value}"
        )
    if _holds_range_dots(value) or commit_range.match_phrase(value) is not None:
        raise StatusSpellingRefused(
            f"[RANGE_UNRECOGNIZED] {value}\n{_STATUS_TAKES_PINNED}"
        )
    return value


def _refuse_status_spelling(exc: StatusSpellingRefused, *, as_json: bool) -> int:
    """Print a :class:`StatusSpellingRefused` and return its exit code: the
    marker lines on stdout (one JSON object under ``--json``, so the stream
    stays parseable), and the line the result carries as ``error``."""
    if as_json:
        print(json.dumps({"error": exc.message}, indent=2))
    else:
        print(exc.message)
    record_error(" ".join(exc.message.split("\n")))
    return exc.exit_code


#: The ``--phase`` selectors under which ``status`` shows a commit review's
#: ``[COMMIT_FIXES]`` block: none, or the apply phase's own words.
_COMMIT_FIXES_PHASES = (None, "apply-fixes", "apply-code-fixes")


def _commit_fixes_view(
    plan_path: Path, args: argparse.Namespace, views: Sequence[Dict[str, Any]],
    terminal: bool,
) -> Optional[Tuple[List[str], Dict[str, Any]]]:
    """``([COMMIT_FIXES] lines, commit_fixes)`` from the apply guard saved in
    the plan's ``state.json`` (``commit_apply.fixes_from_state``), or None.

    Only for a settled poll (every listed run done, failed, aborted or
    finished in the foreground with no run record; or no run record at all, a
    native apply's case), and not when ``--question`` or
    a ``--phase`` other than the apply phase narrows the poll. Read-only and
    advisory: an unreadable state file costs the block, never the poll.
    """
    if getattr(args, "question", None) or not (terminal or not views):
        return None
    try:
        if _resolve_phase(args.phase) not in _COMMIT_FIXES_PHASES:
            return None
        # Imported here to keep run_status light.
        from .commit_apply import fixes_from_state

        state_file = output_dir_path(plan_path) / "state.json"
        if not state_file.is_file():
            return None
        state = json.loads(state_file.read_text(encoding="utf-8"))
        return fixes_from_state(state) if isinstance(state, dict) else None
    except Exception as exc:  # noqa: BLE001 - advisory: the run view is not
        note_swallowed("status: commit fixes view", exc)
        return None


# ---------------------------------------------------------------------------
# main and its stages (docs/development/status.md#how-status-is-built)
# ---------------------------------------------------------------------------

@dataclass
class StatusFacts:
    """What one poll read before it decides anything (:func:`_gather`)."""

    plan_path: Path
    args: argparse.Namespace
    #: ``--view all``'s workflow read; ``None`` under ``--view run``.
    workflow: Optional[Dict[str, Any]]
    views: List[Dict[str, Any]]
    #: What discovery skipped (:func:`_discovery_report`), read before any wait.
    discovery: Dict[str, Any]
    #: Phase -> the executor run a native leg of that phase went on from.
    superseded: Dict[str, Dict[str, Any]]
    #: Implement's whole task account, when an executor implement run is listed.
    implement_tally: Optional[Dict[str, Any]]
    #: The one run the caller's selector names (:func:`_pinned_view`).
    pinned: Optional[Dict[str, Any]]
    #: Every listed run is done, failed or aborted.
    terminal: bool
    #: Every listed run is terminal or has no run record: nothing is writing.
    settled: bool


@dataclass
class StatusAnswer:
    """What the poll answers (:func:`_decide`), for the render and the result
    fields recorded after it."""

    exit_code: int
    #: The pinned run's own stop line, which the notice does not repeat.
    stop_error: Optional[str] = None
    #: ``([COMMIT_FIXES] lines, commit_fixes)`` (:func:`_commit_fixes_view`).
    commit_fixes: Optional[Tuple[List[str], Dict[str, Any]]] = None
    #: A terminal ``--view run`` poll's own workflow read, and what it carries.
    terminal_workflow: Optional[Dict[str, Any]] = None
    workflow_trailer: List[str] = field(default_factory=list)
    terminal_notice: Optional[str] = None
    #: The phases a native host ran (``status_native``).
    implement_tasks: Optional[Dict[str, Any]] = None
    apply_tasks: List[Dict[str, Any]] = field(default_factory=list)
    #: ``user_next_step`` and its block, printed after the text.
    step: Optional[Any] = None
    step_block: io.StringIO = field(default_factory=io.StringIO)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """``status <plan>``: read the views, decide the answer (recording each
    result field it settles as it settles it), print it, record the rest of
    the result line. ``--abort``, ``--sweep`` and ``--view workflow`` answer
    before any of that."""
    bootstrap_streams()
    args = parse_args(argv)
    try:
        plan_value = status_plan_value(args.plan_file)
    except StatusSpellingRefused as exc:
        return _refuse_status_spelling(exc, as_json=args.json)
    plan_path = Path(os.path.abspath(plan_value))

    if not plan_path.exists():
        payload = {"error": f"{status_views._document_file_label(plan_path)} not found: {plan_path}"}
        print(json.dumps(payload, indent=2))
        return EXIT_ERROR

    if args.abort:
        return _run_abort(plan_path, args)
    if args.sweep:
        return _run_sweep(plan_path, args)

    workflow = None
    if args.view in (VIEW_WORKFLOW, VIEW_ALL):
        try:
            workflow = status_views._workflow_payload(plan_path, host_id=_reader_host(args))
        except Exception as exc:  # unreadable state.json is exit 1, not a crash
            print(json.dumps({"error": f"{type(exc).__name__}: {exc}"}, indent=2))
            return EXIT_ERROR

    if args.view == VIEW_WORKFLOW:
        # Byte-identical to `check_workflow_prerequisites.py --status`, exit 0 included.
        print(json.dumps(workflow, indent=2))
        return EXIT_OK

    try:
        facts = _gather(plan_path, args, workflow)
    except _WaitTimeoutRefused as exc:
        # Exit 3 names the fix; stderr, so `--json`'s stdout stays parseable.
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_NEEDS_HUMAN
    answer = _decide(facts)
    _render(facts, answer)
    _record_result(facts, answer)
    if args.exit_zero and answer.exit_code in (EXIT_NOTHING_TO_DO, EXIT_NEEDS_HUMAN):
        # Only the code moves: the verdict's word stays on the result line,
        # and everything above was decided on the real verdict.
        keep_state_word(answer.exit_code)
        return EXIT_OK
    return answer.exit_code


def _gather(
    plan_path: Path, args: argparse.Namespace, workflow: Optional[Dict[str, Any]],
) -> StatusFacts:
    """Read the views (:func:`_collect`) and what discovery skipped, then
    ``--wait`` on them, then set aside the executor runs a native leg went on
    from (never under ``--run-id`` / ``--question``, which name a run) and
    tally implement's tasks beside an executor implement run. Raises
    :class:`_WaitTimeoutRefused` for a ``--wait`` with no honest deadline."""
    views = _collect(plan_path, args)
    discovery = _discovery_report(plan_path, args)
    if args.wait:
        # `--timeout` is a sentinel until here, and resolved only under
        # `--wait`, so a plain poll reads no config.
        args.timeout = _resolve_wait_timeout(args, plan_path)
        views = _wait_for_terminal(plan_path, args, views)

    superseded: Dict[str, Dict[str, Any]] = {}
    if not args.run_id and not args.question:
        try:
            views, superseded = status_native.set_aside_superseded_runs(
                plan_path, views, host_id=_reader_host(args))
        except Exception as exc:  # noqa: BLE001 - advisory: the run view is not
            note_swallowed("status: superseded runs", exc)
            superseded = {}

    implement_tally = None
    if any(status_views._is_executor_implement_view(view) for view in views):
        try:
            implement_tally = status_native.implement_task_tally(plan_path)
        except Exception as exc:  # noqa: BLE001 - advisory: the run view is not
            note_swallowed("status: implement task tally", exc)
            implement_tally = None

    return StatusFacts(
        plan_path=plan_path, args=args, workflow=workflow, views=views,
        discovery=discovery, superseded=superseded, implement_tally=implement_tally,
        pinned=_pinned_view(args, views),
        terminal=bool(views) and all(
            view["verdict"] in detach.TERMINAL_VERDICTS for view in views),
        settled=bool(views) and all(
            view["verdict"] in detach.TERMINAL_VERDICTS
            or view["verdict"] == detach.VERDICT_NO_RUN
            for view in views),
    )


def _decide(facts: StatusFacts) -> StatusAnswer:
    """The answer, in this order: the pinned run's own fields, the exit code,
    a pinned exit-0 run's result word, the commit-fixes block, a terminal
    ``--view run`` poll's workflow trailer, the phases a native host ran, and
    the next step. Each result field is recorded as soon as it is known, so a
    raise or an interrupt later in the poll still leaves it on the result line
    (docs/development/status.md#how-status-is-built). Reads ``state.json``
    again for the last four; prints nothing but a failed next-step lookup's
    one stderr line."""
    stop_error = (
        _record_pinned_run(facts.pinned, facts.implement_tally)
        if facts.pinned is not None else None
    )
    answer = StatusAnswer(
        exit_code=status_views.exit_code_for(facts.views), stop_error=stop_error)
    if facts.pinned is not None and answer.exit_code == EXIT_OK:
        result_state = status_views._result_state(facts.pinned)
        if result_state:
            record_state(result_state)
    answer.commit_fixes = _commit_fixes_view(
        facts.plan_path, facts.args, facts.views, facts.settled)
    if answer.commit_fixes is not None:
        record_commit_fixes_result(answer.commit_fixes[1])
    _terminal_trailer(facts, answer)
    _native_views(facts, answer)
    _next_step(facts, answer)
    return answer


def _record_pinned_run(
    watched: Dict[str, Any], implement_tally: Optional[Dict[str, Any]],
) -> Optional[str]:
    """Record the pinned run's own ``mode`` (its record's, else its phase
    dir) and ``phase`` (a composite's from its worker's line), its progress
    map whole, its rendered progress lines (implement's whole tally beside an
    executor implement), and its stop line as ``error``: ``run.error`` of a
    failed run unless it is the close-out's generic word. Each is recorded
    before the next is read. Returns the stop line, or ``None``."""
    run = watched.get("run") or {}
    mode = str(run.get("mode") or watched.get("phase") or "") or None
    phase = str(
        watched.get("phase")
        or detach.recorded_step_results(watched).get("phase") or ""
    ) or None
    record_mode_phase(mode, phase)
    record_progress(watched.get("progress"))
    lines = status_text._progress_lines(watched)
    if (implement_tally is not None
            and status_views._is_executor_implement_view(watched)):
        lines.append(
            "implement tasks: "
            + status_native.implement_tally_text(
                implement_tally, live=status_views._run_is_live(watched))
        )
    record_progress_lines(lines)
    recorded_error = run.get("error")
    if (
        isinstance(recorded_error, str) and recorded_error.strip()
        and recorded_error.strip() != status_views.GENERIC_NEEDS_HUMAN_ERROR
        and watched.get("verdict") in (detach.VERDICT_FAILED,)
    ):
        record_error(recorded_error.strip())
        return recorded_error.strip()
    return None


def _close_note(facts: StatusFacts, workflow: Dict[str, Any]) -> Optional[str]:
    """The workflow section's manual-tasks close note, spelled for this reader."""
    args, views, plan_path = facts.args, facts.views, facts.plan_path
    return status_text.manual_close_note(
        workflow, _plan_spelling(args, views, plan_path),
        _reader_host(args), _recorded_route(args, views, plan_path),
    )


def _terminal_trailer(facts: StatusFacts, answer: StatusAnswer) -> None:
    """A terminal ``--view run`` poll of a workflow step's run reads the
    workflow and carries its trailer: ``suggested next:`` only on exit 0, the
    rest always. A tool route's text and the notice leave out the resume a
    manual-task gate's stop already gives; a shell's text keeps every line.
    An ask is no workflow step. A failed read costs the trailer (advisory)."""
    args = facts.args
    if not (args.view == VIEW_RUN and facts.terminal
            and any(_is_workflow_step_run(view) for view in facts.views)):
        return
    try:
        answer.terminal_workflow = status_views._workflow_payload(
            facts.plan_path, host_id=_reader_host(args))
    except Exception as exc:
        note_swallowed("status: terminal workflow", exc)
        answer.terminal_workflow = None
    workflow = answer.terminal_workflow
    if not workflow:
        return
    close_note = _close_note(facts, workflow)
    trailer = status_text._workflow_trailer_lines(
        workflow, prefix="", close_note=close_note,
        suggested=answer.exit_code == EXIT_OK,
    )
    # Imported here to keep run_status light.
    from .next_phase import gate_resume_closes_the_manual_tasks

    told = trailer
    if (close_note and answer.exit_code != EXIT_OK
            and gate_resume_closes_the_manual_tasks(
                (workflow.get("phases") or {}).get("implement") or {})):
        told = status_text._workflow_trailer_lines(workflow, prefix="", suggested=False)
    if trailer:
        answer.workflow_trailer = [
            f"workflow {line}" for line in (
                told if _read_by_a_tool_route(args) else trailer)]
        answer.terminal_notice = join_clauses(told)


def _native_views(facts: StatusFacts, answer: StatusAnswer) -> None:
    """The phases a native host ran, which leave no run record, read back
    from ``state.json``: implement (no ``--phase``, or ``--phase implement``)
    and the apply phases. Never under ``--run-id`` / ``--question``, which
    name a run. Each block names the executor run it superseded. Advisory."""
    args, plan_path, views = facts.args, facts.plan_path, facts.views
    if (not args.run_id and not args.question
            and _resolve_phase(args.phase) in (None, status_views._IMPLEMENT_PHASE)):
        try:
            answer.implement_tasks = status_native.state_implement_view(plan_path, views)
        except Exception as exc:  # noqa: BLE001 - advisory: the run view is not
            note_swallowed("status: native implement view", exc)
            answer.implement_tasks = None
    if not args.run_id and not args.question:
        try:
            answer.apply_tasks = status_native.state_apply_views(
                plan_path, views, facts.workflow or answer.terminal_workflow,
                only=_resolve_phase(args.phase), host_id=_reader_host(args),
            )
        except Exception as exc:  # noqa: BLE001 - advisory: the run view is not
            note_swallowed("status: native apply views", exc)
            answer.apply_tasks = []
    for phase, record in facts.superseded.items():
        entry = answer.implement_tasks if phase == status_views._IMPLEMENT_PHASE else next(
            (item for item in answer.apply_tasks if item.get("phase") == phase), None)
        if isinstance(entry, dict):
            entry["earlier_run"] = record


def _next_step(facts: StatusFacts, answer: StatusAnswer) -> None:
    """A terminal poll pinned to one run that exits 0 carries the next phase
    (``user_next_step``; its block prints after the text, on stderr under
    ``--json``), whatever ``--view``. On a tool route the trailer then leaves
    out what the step's own markdown says."""
    if not (answer.exit_code == EXIT_OK and facts.terminal
            and facts.pinned is not None):
        return
    answer.step = _emit_user_next_step(
        facts.plan_path, facts.args, facts.pinned,
        workflow=answer.terminal_workflow, stream=answer.step_block,
    )
    if (answer.step is not None and answer.terminal_workflow
            and answer.workflow_trailer and _read_by_a_tool_route(facts.args)):
        answer.workflow_trailer = [
            f"workflow {line}" for line in status_text._workflow_trailer_lines(
                answer.terminal_workflow, prefix="", suggested=False,
                carried=answer.step,
                close_note=_close_note(facts, answer.terminal_workflow),
            )
        ]


def _render(facts: StatusFacts, answer: StatusAnswer) -> None:
    """Print the answer: the ``--json`` document or the text, then the next
    step's block (stderr under ``--json``, whose document gains no key)."""
    if facts.args.json:
        print(json.dumps(_render_json(facts, answer), indent=2, default=str))
    else:
        print("\n".join(_render_text(facts, answer)))
    block = answer.step_block.getvalue()
    if block:
        block_stream = sys.stderr if facts.args.json else sys.stdout
        block_stream.write(block)
        block_stream.flush()


def _render_json(facts: StatusFacts, answer: StatusAnswer) -> Dict[str, Any]:
    """The run document (schemas/status_json.schema.json); a key with
    nothing to say is left out, so a plan with none keeps its payload."""
    payload: Dict[str, Any] = {"runs": facts.views}
    if facts.args.view == VIEW_ALL:
        payload = {"workflow": facts.workflow, "runs": facts.views}
    if answer.implement_tasks is not None:
        payload["implement_tasks"] = answer.implement_tasks
    if answer.apply_tasks:
        payload["apply_phases"] = answer.apply_tasks
    if facts.implement_tally is not None:
        payload["implement_tally"] = facts.implement_tally
    if facts.discovery.get("ignored_dirs"):
        payload["ignored_dirs"] = list(facts.discovery["ignored_dirs"])
    if facts.discovery.get("copies"):
        payload["copied_runs"] = list(facts.discovery["copies"])
    if answer.commit_fixes is not None:
        payload["commit_fixes"] = answer.commit_fixes[1]
    return payload


def _render_text(facts: StatusFacts, answer: StatusAnswer) -> List[str]:
    """The text, in this order: the workflow section (``--view all``), the
    run view, the native phases' blocks in workflow order, what discovery
    skipped, the runner, the commit fixes, the terminal workflow trailer."""
    args, views, plan_path, workflow = facts.args, facts.views, facts.plan_path, facts.workflow
    lines: List[str] = []
    if args.view == VIEW_ALL and workflow is not None:
        lines += status_text.render_workflow_text(
            workflow, close_note=_close_note(facts, workflow))
        lines.append("")
    spell = status_commands.user_speller(
        _reader_host(args), _plan_spelling(args, views, plan_path),
        plan_path=plan_path)
    lines += status_text.render_run_text(
        views, plan_path=plan_path, workflow=workflow,
        scope=_scope_label(args), resume_workflow=answer.terminal_workflow,
        implement_tally=facts.implement_tally,
        state_block=answer.implement_tasks is not None or bool(answer.apply_tasks),
        spell=spell,
    )
    native: List[Tuple[str, List[str]]] = [
        (entry["phase"], status_native.render_state_apply_lines(
            entry, resume=status_native.native_resume_command(entry["phase"], plan_path, spell)))
        for entry in answer.apply_tasks
    ]
    implement_tasks = answer.implement_tasks
    if implement_tasks is not None:
        native.append((status_views._IMPLEMENT_PHASE, status_native.render_state_implement_lines(
            implement_tasks,
            resume=status_native.native_resume_command(
                status_views._IMPLEMENT_PHASE, plan_path, spell,
                flags=implement_tasks.get("resume_flags") or ()),
            answers=status_native.native_stop_answer_commands(implement_tasks, plan_path, spell))))
    for _phase, block in sorted(
            native, key=lambda item: status_native.NATIVE_PHASE_ORDER.index(item[0])):
        lines += block
    lines += status_text._ignored_text(
        facts.discovery.get("ignored_dirs") or [], facts.discovery.get("copies") or []
    )
    runner = status_commands.render_runner_text(
        plan_path, host_id=getattr(args, "host", None), views=views
    )
    if runner:
        lines.append("")
        lines += runner
    if answer.commit_fixes is not None:
        lines.append("")
        lines += answer.commit_fixes[0]
    if answer.workflow_trailer:
        lines.append("")
        lines += answer.workflow_trailer
    return lines


def _record_result(facts: StatusFacts, answer: StatusAnswer) -> None:
    """Record the rest of the result line, after the render, in this order:
    the notice; the artifacts; then the fields a detached worker recorded on
    a line no host saw; and on exit 2 the poll to run next. (:func:`_decide`
    recorded the pinned run's own fields, its result word and the commit
    fixes.)"""
    views, pinned = facts.views, facts.pinned
    # The workflow trailer as the notice says it beside `user_next_step`,
    # which says the rest itself.
    terminal_notice = answer.terminal_notice
    if answer.step is not None and answer.terminal_workflow:
        terminal_notice = join_clauses(status_text._workflow_trailer_lines(
            answer.terminal_workflow, prefix="", suggested=False,
            carried=answer.step)) or None
    # A composite's steps ran in its process: what each recorded reaches its
    # run dir only through its report, under this run's id.
    carried = (
        detach.recorded_step_results(pinned)
        if facts.terminal and pinned is not None else {}
    )
    steps = [step for step in carried.get("steps") or [] if isinstance(step, dict)]
    notice = _notice(facts, answer, steps, terminal_notice)
    if notice:
        record_notice(notice)

    for path in carried.get("artifacts") or []:
        if isinstance(path, str):
            record_artifact(path)
    for view in views:
        for path in view["output_files"].values():
            if isinstance(path, str):
                record_artifact(path)
        if view["run"].get("log_path"):
            record_artifact(view["run"]["log_path"])
    # One field each, so the first view holding one wins; the worst `mode`
    # wins for the validation context, first in discovery order on a tie.
    recommended = next(
        (v["consolidation_recommended"] for v in views
         if v.get("consolidation_recommended")),
        None,
    )
    if recommended:
        record_consolidation_recommended(recommended)
    validation_context = pick_worst(
        [v.get("validation_context") for v in [*views, *steps]]
    )
    if validation_context:
        record_validation_context(validation_context)
    if pinned is not None:
        _record_pinned_fields(facts, pinned, steps)
    if answer.exit_code == EXIT_NOTHING_TO_DO and views:
        _record_poll_again(facts)


def _notice(
    facts: StatusFacts, answer: StatusAnswer, steps: Sequence[Dict[str, Any]],
    terminal_notice: Optional[str],
) -> Optional[str]:
    """A terminal poll's notice, one join of: a truncated validation source,
    the write run's not-clean parts, the runs' own notes, a composite's steps'
    notices (each clause said once), and the workflow trailer
    (*terminal_notice*), leaving out what the stop line already says."""
    views = facts.views
    truncation_notice = (
        status_text._validation_context_notice(views) if facts.terminal else None
    )
    write_parts = status_text._write_result_notice_parts(views) if facts.terminal else []
    note_parts = [
        note for view in views for note in status_text._run_notes(view)
    ] if facts.terminal else []
    step_parts = [str(step["notice"]) for step in steps if step.get("notice")]
    stop_error = answer.stop_error
    if stop_error:
        said = plain_line(clip(stop_error, ERROR_MAX_CHARS))
        write_parts = [part for part in write_parts if plain_line(part) not in said]
        note_parts = [part for part in note_parts if plain_line(part) not in said]
    write_notice = clip(join_clauses(write_parts), 1200) or None
    notes_notice = join_clauses(note_parts)
    steps_notice = ""
    for part in step_parts:
        earlier = join_clauses((
            clip(stop_error, ERROR_MAX_CHARS) if stop_error else None,
            write_notice, notes_notice, steps_notice))
        steps_notice = join_clauses((steps_notice, drop_said_clauses(part, earlier)))
    return join_clauses((
        truncation_notice, write_notice, notes_notice, steps_notice,
        terminal_notice)) or None


def _record_pinned_fields(
    facts: StatusFacts, pinned: Dict[str, Any], steps: Sequence[Dict[str, Any]],
) -> None:
    """The fields a pinned poll re-records from its run (an unselected one
    lists every phase, so no run's would be the answer): the verdict counts
    (a composite's last review's), the distinct-HIGH-group count of a
    finished run whose phase is complete, and an ask's answer origins.
    ``claim_run`` drops a predecessor's, so a run that stopped short of its
    own report relays none."""
    counts = next(
        (v["validation_counts"] for v in reversed([*facts.views, *steps])
         if v.get("validation_counts")),
        None,
    )
    if counts:
        record_validation_counts(counts)
    high_priority = (
        pinned.get("high_priority_groups")
        if facts.terminal and pinned.get("state") == "complete" else None
    )
    if isinstance(high_priority, dict):
        record_high_priority_groups(high_priority)
    origins = pinned.get("answer_origins")
    if isinstance(origins, dict):
        record_answer_origins(origins)


def _record_poll_again(facts: StatusFacts) -> None:
    """Exit 2's ``next``: a poll of the first live run (non-terminal and
    holding a run record), else of the first view with a run record, else
    none; and ``state: running`` (``died`` when every live run is) when a
    live run is why the poll exits 2."""
    views = facts.views
    live_views = [
        v for v in views
        if v["verdict"] not in detach.TERMINAL_VERDICTS
        and v["verdict"] != detach.VERDICT_NO_RUN
    ]
    candidates = live_views or [
        v for v in views if v["verdict"] != detach.VERDICT_NO_RUN
    ]
    if candidates:
        first = candidates[0]
        record_next(
            detach.status_command_for(
                str(facts.plan_path),
                phase=first.get("phase"),
                run_id=str(first["run"].get("run_id") or "") or None,
                # The run's own host, so the poll reports the run's runner.
                host=str(first["run"].get("host") or "") or None,
            )
        )
    if live_views:
        record_state(
            STATE_DIED if all(status_views._died(v) for v in live_views) else STATE_RUNNING
        )


def _is_workflow_step_run(view: Dict[str, Any]) -> bool:
    """Whether *view*'s run is a step of the plan's workflow: a phase or a
    composite (``modes.Mode.is_workflow_phase`` / ``is_composite``), read from
    its record's ``mode``, else its phase dir. An ``ask`` is not, nor a view
    with no mode on record, so nothing a poll of one prints is the
    workflow's next phase (docs/development/status.md, "Only a workflow
    step's run carries them").
    A commit front door's run is recorded under the phase it fronts."""

    run = view.get("run") or {}
    finished_mode = str(run.get("mode") or view.get("phase") or "") or None
    mode = _modes().resolve(finished_mode) if finished_mode else None
    return mode is not None and (mode.is_workflow_phase or mode.is_composite)


def _emit_user_next_step(
    plan_path: Path,
    args: argparse.Namespace,
    view: Dict[str, Any],
    *,
    workflow: Optional[Dict[str, Any]] = None,
    stream=None,
) -> Optional[Any]:
    """The terminal poll's ``user_next_step`` and block (next-phase-command §2.2(1)).

    Inputs per §2.1 "Where each emitter gets its inputs": ``finished_mode`` is
    the pinned run's own mode (its record's ``mode``, else its phase dir — the
    pair ``record_mode_phase`` reports); ``plan_arg`` is the record's
    ``plan_arg`` — the plan as the launcher typed it — when
    ``next_phase.recorded_plan_spelling`` passes it (the record sits in a
    folder every jailed batch can write), else this poll's absolute plan path,
    never the record's ``plan_file`` and never this poll's argv spelling;
    the host is this poll's (``--host``, ``$MULTI_LLM_HOST``, the default). The
    workflow is read now, after any ``--wait``; *workflow* is such a read when
    the caller already took one. A failed read or builder raise prints one
    stderr line and sets nothing. Returns the answer it emitted, or ``None``.
    A composite's run (``full``, ``improve-plan``, ``improve-code``) answers
    too: the builder walks on from the phase a review-then-apply composite
    ends on (plans/improve-plan-and-improve-code.md §2.6), and from
    ``suggested_next`` for ``full``.
    """
    # Imported here to keep run_status light.
    from . import next_phase

    run = view.get("run") or {}
    finished_mode = str(run.get("mode") or view.get("phase") or "") or None
    if not _is_workflow_step_run(view):
        return None  # an ask, or no mode on record: no phase finished, no answer
    plan_arg = next_phase.recorded_plan_spelling(
        run.get("plan_arg"), str(plan_path)
    ) or str(plan_path)
    try:
        if workflow is None:
            workflow = status_views._workflow_payload(plan_path, host_id=_reader_host(args))
    except Exception as exc:  # noqa: BLE001 - advisory: the run view is not
        print(next_phase.lookup_failure_line(exc), file=sys.stderr)
        return None
    return next_phase.emit_answer(
        plan_arg,
        _reader_host(args),
        finished_mode,
        plan_path=plan_path,
        workflow=workflow,
        stream=stream if stream is not None else (
            sys.stderr if args.json else sys.stdout),
        # Fix round 24: the route the pinned run was started on.
        recorded_route=status_commands._run_route(view, _reader_host(args)),
    )


def _read_by_a_tool_route(args: argparse.Namespace) -> bool:
    """Whether a tool server is the reader of this poll's text: the route
    this process spells commands for (``next_phase.resolve_route``, its one
    reader, from the environment the servers set; never a run's recorded
    route, which a shell reads too) is a tool route (fix round 26)."""

    # Imported here to keep run_status light.
    from . import next_phase

    try:
        route = next_phase.resolve_route(_reader_host(args), stderr=io.StringIO())
    except Exception as exc:  # noqa: BLE001 - advisory: the text stays whole
        note_swallowed("status: tool route reader", exc)
        return False
    return route in _modes().TOOL_ROUTES


def _wait_clamp_ceiling(host_id: Optional[str]) -> Optional[Tuple[str, int]]:
    """``(host, its foreground command cap)`` a ``--wait`` is clamped against.

    ``None`` means *do not clamp*, and there are exactly two ways to get it:
    the named host declares ``timeout_ceiling_s: 0``, which is the documented
    "no documented cap" value rather than a cap of zero (codex ships it), and
    the capability data could not be read at all. The second follows
    ``render_runner_text`` and ``effective_ceiling``: unreadable capability data
    bounds nothing rather than failing, because ``status`` is the command a poll
    loop runs and a capability read is not what a poll is about.

    With no host *declared at all* — neither ``--host`` nor ``$MULTI_LLM_HOST``,
    see :func:`_declared_host_id` — the clamp falls back to the tightest declared
    cap rather than being skipped: an unrouted poll could be running under any
    host, and overshooting one of their caps by accident is the failure the
    clamp exists for.
    """
    try:
        if host_id:
            ceiling = host_capabilities.timeout_ceiling_s(host_id)
            return (host_id, ceiling) if ceiling else None
        return host_capabilities.tightest_timeout_ceiling()
    except Exception as exc:
        note_swallowed("status: wait clamp ceiling", exc)
        return None


def _declared_host_id(args: argparse.Namespace) -> Optional[str]:
    """The host this invocation *declared*, or ``None`` when neither channel did.

    :func:`host_capabilities.resolve_host_id` owns the ladder — ``--host`` →
    ``$MULTI_LLM_HOST`` → :data:`DEFAULT_HOST` — and it is what
    :func:`render_runner_text` resolves in this same invocation and what the
    dispatcher validates ``--host`` against. The clamp asks it the same question
    and differs only in the last rung: a host nobody named is not a host to
    clamp against, so the default is *not* substituted here and the caller falls
    back to the tightest declared cap instead.

    F3, 2026-09-21: the clamp read ``args.host`` alone, so a poll routed entirely
    through the env var — which is how an installer routes one — was clamped
    against the tightest ceiling on record (90 s) instead of its own host's, and
    the stderr note explaining the clamp told the caller no ``--host`` had been
    given when a host had in fact been declared.
    """

    explicit = getattr(args, "host", None)
    if not explicit and not os.environ.get(host_capabilities.HOST_ENV):
        return None
    return host_capabilities.resolve_host_id(explicit=explicit)


def _resolve_wait_timeout(args: argparse.Namespace, plan_path: Path) -> float:
    """``--wait``'s deadline: resolve the source, then clamp the *resolved value*.

    Order, and nothing else reads ``progress.interval_s`` on the way through:

    1. an explicit ``--timeout`` wins;
    2. else ``progress.poll_s`` — anchored on the plan, so a poll issued from a
       foreign CWD still resolves the *project's* cadence;
    3. else :data:`DEFAULT_WAIT_TIMEOUT_S`. ``poll_s`` itself ships at 90 s, so a
       project that configures nothing keeps exactly today's wait.

    ``interval_s`` is the ticker knob and is deliberately not consulted:
    silencing the ticker lines must not turn a poll into an instant return.

    **The clamp binds whichever source won, an explicit ``--timeout`` included.**
    "Wins" settles precedence, not the ceiling. The rendered poll command Layer 2
    tells an agent to run always passes ``--timeout <interval>``, so a clamp
    guarding only the ``poll_s`` path would leave the one command the
    instructions actually emit unguarded: a ``--timeout 300`` on OpenCode asks
    for a 300 s foreground command under a documented 120 s cap and is killed
    mid-wait with no view rendered at all.

    The two paths differ only in **loudness**. A clamped ``poll_s`` is silent —
    the user configured a cadence, not a deadline, and shortening a cadence
    costs them one extra poll. A clamped explicit ``--timeout`` prints one
    stderr line naming the requested value, the clamped value and the host,
    because that caller asked for a specific number and is getting another.
    Stderr, not stdout, so ``--json``'s output stays parseable.

    **Two ways this refuses, and both wear the same clean exit-3 shape.**

    A ``ConfigError`` — from a rejected ``progress.poll_s`` (``0``, or below the
    5 s floor), *or* from any unrelated block in the same override file, because
    ``load_config`` validates the whole document — is caught and re-raised as
    :class:`_WaitTimeoutRefused` for ``main`` to print. F4, 2026-09-20: it used
    to propagate, and the dispatcher turned it into a traceback plus **exit 1**.
    Measured with ``MULTI_LLM_PROVIDERS_CONFIG`` pointing at a config carrying a
    bogus ``driver:`` key: plain ``status`` exited 2 normally while ``status
    --wait --json`` exited 1 with a stack trace on stderr and no JSON on stdout.
    Rule 2 reads exit 1 as "the run state is unreadable — stop and report", so a
    config edit made *during* a run ended the poll loop on a misdiagnosis of the
    run. Exit 3 is this codebase's "needs a human", which is exactly what a
    rejected config key is; the rejection still surfaces, named, which was the
    point of validating at load.

    And a non-finite or negative explicit ``--timeout`` is refused here rather
    than obeyed. ``--timeout nan``/``inf``/``-1`` all parse as floats, and with
    ``--host codex`` (``timeout_ceiling_s: 0``, so no clamp) they reach
    ``_wait_for_terminal`` intact: ``time.time() >= nan`` is ``False`` forever
    and the poll never returns. ``validate_progress_block`` rejects ``.nan`` and
    ``.inf`` for ``poll_s`` **precisely** to prevent "a ``--wait`` that never
    returns", and the CLI path was undoing that one layer up (F7, 2026-09-20).
    """
    # Imported here to keep run_status light.
    from .provider_registry import ConfigError, get_progress_poll

    explicit = args.timeout is not None
    if explicit:
        requested = float(args.timeout)
        if requested != requested or requested in (float("inf"), float("-inf")):
            raise _WaitTimeoutRefused(
                f"--timeout {args.timeout!r} is not a finite number of seconds. "
                "A non-finite deadline is never reached, so `--wait` would poll "
                "forever with nothing to hand back. Pass a positive number of "
                "seconds, or drop `--timeout` and let `progress.poll_s` answer."
            )
        if requested <= 0:
            raise _WaitTimeoutRefused(
                f"--timeout {requested:g} is not a positive number of seconds. "
                "A zero or negative deadline returns before the first re-read, "
                "which is the instant-return failure `progress.poll_s: 0` is "
                "rejected for. Pass a positive number of seconds, or drop "
                "`--timeout` and let `progress.poll_s` answer."
            )
    try:
        resolved = (
            float(args.timeout) if explicit
            else float(get_progress_poll(anchor=str(plan_path)))
        )
    except ConfigError as exc:
        raise _WaitTimeoutRefused(
            f"{exc}\n`--wait` resolves its deadline through the config layer, so "
            "a config this run cannot read stops the poll rather than guessing a "
            "cadence. Fix the config and poll again; the run itself is untouched "
            "(`status` without `--wait` still reports it)."
        ) from exc

    host_id = _declared_host_id(args)
    ceiling = _wait_clamp_ceiling(host_id)
    if ceiling is None:
        return resolved
    capped_host, cap_s = ceiling
    # A margin below the cap, never the cap itself: the poll spends process
    # start, `load_config` and the checkpoint read before `--wait` begins
    # sleeping, and `_wait_for_terminal` re-checks on a 5 s grid, so it returns a
    # little after its own deadline. The floor is arithmetic hygiene for a
    # hypothetical host whose cap is under the margin — a wait clamped to zero
    # would return instantly, which is exactly what `poll_s: 0`'s rejection
    # exists to prevent.
    clamped = max(float(cap_s) - WAIT_CAP_MARGIN_S, status_file.WAIT_POLL_INTERVAL_S)
    if resolved <= clamped:
        return resolved
    if explicit:
        unrouted = (
            "" if host_id
            else " (no --host and no $MULTI_LLM_HOST, so the clamp used the "
                 "tightest declared cap)"
        )
        print(
            f"NOTE: --timeout {resolved:.0f}s is above host {capped_host}'s "
            f"{cap_s}s foreground command cap{unrouted}; waiting "
            f"{clamped:.0f}s instead (the cap less the "
            f"{WAIT_CAP_MARGIN_S:.0f}s startup margin). Poll again to keep "
            "watching.",
            file=sys.stderr,
        )
    return clamped


def _wait_for_terminal(
    plan_path: Path, args: argparse.Namespace, views: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """The one convenience, and it is bounded.

    Compresses the poll loop into a single turn for hosts that would rather spend
    one turn than ten; it never replaces the terminal-state check, and at timeout
    it returns the non-terminal view (exit 2) so the caller simply calls again.

    **A view is "still going" when either half of the file says so.** The
    ``run`` record is the process machine and the checkpoint is the phase
    machine, and on a re-used phase dir the two belong to *different runs*: a
    host-background run over a dir an earlier ``--detach`` run used inherits that
    predecessor's terminal ``run`` record, because nothing drops it on the
    foreground path. Keying the loop on the verdict alone therefore returned in
    0.11 s with exit 0 over a live fan-out — see :func:`_checkpoint_in_flight`
    for the incident (F1, 2026-09-20). Erring toward waiting cannot spin: the
    deadline is checked on every pass and a wait that guessed wrong costs its own
    timeout and exits 2, which is the caller's normal "poll again".

    It also takes the **before** picture that ``just finished:`` is a difference
    against. This is the only place that can: ``--wait`` is the one invocation
    that spans two readings of the same file, so it is the one invocation that
    can prove a spec finished *recently* rather than merely that it is finished.
    A loop that exits without iterating (everything was already terminal) leaves
    the views it was handed untouched, the difference is empty, and no key is
    attached — which is the right answer, not a missed case: nothing finished
    during a wait that never waited.

    **The checkpoint's vote is a vote about a *successor*, so a poll that names
    the run does not get it.** The phase half of a failed or aborted run is
    routinely left wherever the failure found it — ``state: models_running``,
    ``progress.step: fanout``, because nothing walks those fields back — so a
    caller polling ``--run-id <that run> --wait`` was held for the whole resolved
    timeout (90 s by default) before being told about an outcome that had been on
    disk since before the call. That is the mirror image of F1, not a softening
    of it: there the terminal record belonged to a *predecessor* and the live
    checkpoint to the run being watched, and the checkpoint deserved the vote
    precisely because the two halves described different runs. Here the caller
    has named the record's own id, so there is no second run left for the stale
    phase fields to be describing. Only an identified run is excused
    (:func:`_names_this_run`) — ``--phase`` and ``--question`` name a re-used
    directory rather than a run, and a bare poll names nothing at all, so every
    shape F1 covers keeps waiting exactly as it did.

    **``no_run`` is not a vote either way, so the checkpoint casts the only one.**
    The verdict is non-terminal purely because there is nothing to be terminal
    about — every foreground phase (all of them on Claude Code) leaves a
    checkpoint and no ``run`` record — and reading that as "still going" made a
    *finished* foreground phase hold every poll for its whole deadline and then
    exit 2 with a ``next`` that polls it again: a loop nothing in it can ever
    end (F2, 2026-09-21). Asking :func:`_checkpoint_in_flight` instead loses
    nothing, because on this lane the checkpoint is the only half of the file
    that was ever written: a live foreground fan-out still holds the wait to its
    deadline (acceptance criterion 1), and a completed one now comes back at
    once.
    """
    baseline = {
        str(view.get("phase_dir") or ""): status_text._terminal_fingerprints(view)
        for view in views
    }
    deadline = time.time() + max(args.timeout, 0.0)

    def _live(view: Dict[str, Any]) -> bool:
        verdict = view["verdict"]
        if (verdict not in detach.TERMINAL_VERDICTS
                and verdict != detach.VERDICT_NO_RUN):
            return True
        if status_views._names_this_run(view, getattr(args, "run_id", None)):
            return False
        if status_native.superseded_by_native(plan_path, view) is not None:
            # Fix round 26: an executor checkpoint the native leg went on
            # from is not a run anyone is waiting for.
            return False
        return status_views._checkpoint_in_flight(view)

    # `not views` is a waiting state, not a terminal one. A poll issued before
    # the run has written its checkpoint — the first poll of every launch —
    # selects nothing, and a loop keyed on "any view is live" exits instantly
    # over an empty list. Both the exit code and the documented reading of it say
    # otherwise: `2` explicitly covers "no run recorded yet, poll again", so
    # returning in 0.13 s turned the one call that exists to hold a turn into a
    # spin the agent repeats as fast as its host will let it (F4, 2026-09-20).
    # Waiting costs at most this call's own deadline and then still exits 2.
    while not views or any(_live(v) for v in views):
        if time.time() >= deadline:
            break
        time.sleep(min(status_file.WAIT_POLL_INTERVAL_S, max(deadline - time.time(), 0.05)))
        views = _collect(plan_path, args)
    status_text._attach_finished_during_wait(baseline, views)
    return views


def _abort_selector_given(args: argparse.Namespace) -> bool:
    """Did the caller name what to abort? (D4h: ``--phase``/``--run-id``/``--all``)."""
    return bool(args.phase or args.question or args.run_id or args.include_all)


def _run_abort(plan_path: Path, args: argparse.Namespace) -> int:
    """``status <plan> --abort`` — idempotent, and it says which case it hit.

    D4h spells the verb with an explicit selector and D4b's rule for a plan whose
    runs are ambiguous is that the candidates are *listed*, never silently
    resolved. A bare ``--abort`` therefore kills a single live run (the case a
    shim's cleanup step means) but refuses to fan out over several: the phase dirs
    under one plan can hold runs a different shim, or a different session,
    launched, and "stop the run I started" must not become "stop everything".
    """
    views = _collect(plan_path, args)
    if not views:
        print(f"Nothing to abort: no run recorded for this {status_views._document_word(plan_path)}.")
        return EXIT_NOTHING_TO_DO
    live = [v for v in views if v["verdict"] not in detach.TERMINAL_VERDICTS]
    if len(live) > 1 and not _abort_selector_given(args):
        print(
            f"{len(live)} live runs under this {status_views._document_word(plan_path)} and no "
            "selector: naming which "
            "one to abort is the caller's job. Candidates:"
        )
        for view in live:
            name = os.path.basename(view["phase_dir"])
            run_id = str(view["run"].get("run_id") or "")
            head = f"  {name}"
            if run_id:
                head += f"  run {run_id[:8]}"
            print(f"{head}  {status_text._verdict_text(view)}")
            if view.get("question"):
                print(f"      question: {view['question']}")
            print(f"      abort it with: {status_commands._abort_command(plan_path, view)}")
        print(
            "  abort every one of them with: "
            + dispatcher_command("status", str(plan_path), "--abort", "--all")
        )
        return EXIT_NEEDS_HUMAN
    aborted = 0
    survived = 0
    needs_force = 0
    for view in views:
        result = detach.abort_run(view["phase_dir"], force=args.force)
        name = os.path.basename(view["phase_dir"])
        run_id = str(view["run"].get("run_id") or "?")
        if result["result"] == "aborted":
            aborted += 1
            print(f"aborted {name} run {run_id[:8]} (process group terminated)")
        elif result["result"] == "survived":
            survived += 1
            print(
                f"REFUSED TO DIE: {name} run {run_id} pid "
                f"{view['run'].get('pid')} survived SIGKILL — "
                f"log: {view['run'].get('log_path')}"
            )
        elif result["result"] == "incomplete":
            survived += 1
            print(
                f"INCOMPLETE: {name} run {run_id} pid {view['run'].get('pid')}: "
                "not every process it left could be confirmed stopped (kill "
                f"verdict {result.get('verdict') or 'unknown'}"
                + (f"; {result['detail']}" if result.get("detail") else "")
                + "); what could not be identified as the run's was not "
                "signalled. Check its process group "
                f"{view['run'].get('pgid') or '?'} by hand, or abort again to "
                f"retry — log: {view['run'].get('log_path')}"
            )
        elif result["result"] == "needs_force":
            needs_force += 1
            print(
                f"{name} run {run_id[:8]}: identity probe inconclusive; re-run "
                "with --force to abort it anyway"
            )
        else:
            print(f"{name} run {run_id[:8]}: nothing was running "
                  f"({result.get('detail', view['verdict'])})")
    if survived:
        return EXIT_NEEDS_HUMAN
    if needs_force:
        return EXIT_NEEDS_HUMAN
    return EXIT_OK if aborted else EXIT_NOTHING_TO_DO


def _run_sweep(plan_path: Path, args: argparse.Namespace) -> int:
    """Close out orphans across every phase dir under this plan, deliberately."""
    phase = _resolve_phase(args.phase)
    closed: List[str] = []
    incomplete: List[str] = []
    for directory in status_views.discover_phase_dirs(plan_path, phase=phase):
        before = status_file.read_run(str(directory)).get("state")
        view = detach.classify_run(str(directory), close_out=True)
        after = view["run"].get("state")
        if before != after:
            closed.append(f"{os.path.basename(str(directory))}: {before} -> {after}")
        # A close-out whose kill could not confirm every process stopped, now
        # or before: the same verdict and recovery `--abort` prints, exit 3.
        run = status_file.read_run(str(directory))
        if detach.cleanup_incomplete(run):
            cleanup = run["cleanup"]
            incomplete.append(
                f"INCOMPLETE: {os.path.basename(str(directory))} run "
                f"{run.get('run_id') or '?'} pid {run.get('pid')}: not every process "
                "it left could be confirmed stopped (kill verdict "
                f"{cleanup.get('verdict') or 'unknown'}); what could not be identified "
                f"as the run's was not signalled. Check its process group "
                f"{cleanup.get('pgid') or run.get('pgid') or '?'} by hand, or retry with: "
                f"{status_commands._abort_command(plan_path, dict(view, run=run))} — log: "
                f"{run.get('log_path')}")
    if closed:
        print("swept:")
        for line in closed:
            print(f"  {line}")
    else:
        print("swept: nothing to close out")
    for line in incomplete:
        print(line)
    return EXIT_NEEDS_HUMAN if incomplete else EXIT_OK


if __name__ == "__main__":  # pragma: no cover - direct invocation
    sys.exit(main(sys.argv[1:]))
