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
"""

from __future__ import annotations

import argparse
import io
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from . import (
    cli_common,
    detach,
    host_capabilities,
    metrics,
    process_control,
    status_file,
)
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
    record_answer_origins,
    record_artifact,
    record_commit_fixes_result,
    record_consolidation_recommended,
    record_mode_phase,
    record_validation_context,
    record_validation_counts,
    record_next,
    record_notice,
    record_progress,
    keep_state_word,
    record_error,
    record_progress_lines,
    record_state,
)
from .progress_tracker import (
    STATE_DONE,
    STATE_FAILED,
    STATE_QUEUED,
    STATE_RETRYING,
    TERMINAL_STATES,
    WAITING_STATES,
    entry_budget,
    entry_elapsed_s,
    entry_queued_s,
    entry_stagger_remaining_s,
    format_budget,
    format_elapsed,
    one_line_ascii,
    render_progress_line,
    render_roster_line,
)
from .output_handler import (
    PHASE_DIR_NAMES,
    PHASE_DIRECTORIES,
    output_dir_path,
    phase_dir_path,
    slugify_question,
)
from .stream_bootstrap import bootstrap_streams
from .text_clip import clip, drop_said_clauses, join_clauses, plain_line, without_closing_mark
from .validation_context import (
    pick_worst,
    validation_context_notice,
    validation_context_text,
)

#: ``--wait``'s default. Deliberately under the tightest surveyed host shell cap
#: (OpenCode's ~120 s): it compresses the poll loop into one turn, it never
#: replaces the terminal-state check, and it is never emitted for a host whose
#: shell cap is below its own timeout.
DEFAULT_WAIT_TIMEOUT_S = 90.0

#: How often ``--wait`` re-reads the status file. The heartbeat is 10 s, so a
#: faster cadence learns nothing; 5 s keeps the returned view fresh.
WAIT_POLL_INTERVAL_S = 5.0

#: How far *below* a host's ``timeout_ceiling_s`` a resolved ``--wait`` is
#: clamped. This is the number that explains :data:`DEFAULT_WAIT_TIMEOUT_S`:
#: OpenCode's ceiling is 120 s and 120 - 30 = 90.
#:
#: The margin is **startup, not slack**. A poll spends process start,
#: ``load_config`` and the checkpoint read before ``--wait`` begins sleeping, and
#: ``_wait_for_terminal`` re-checks on a :data:`WAIT_POLL_INTERVAL_S` grid, so it
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

#: ``progress.step``'s terminal values. ``progress_tracker.PhaseProgress``
#: owns the first pair and names them in its own docstring: ``complete``, and
#: the host-driven ``validation_pending`` early return where the process exits
#: and the agent's own subagents take over. ``stopped`` is the write
#: scheduler's mirror on a stop (``_mirror_status``), which a foreground
#: executor run that stopped read as "running in foreground" (fix round 22).
#: Anything else means the phase is still working.
CHECKPOINT_TERMINAL_STEPS = frozenset({"complete", "validation_pending", "stopped"})

#: The write scheduler's ``progress.step`` on a stop, and how a foreground
#: run that ended on it heads its block (fix round 23): a stop needs the
#: user, as a detached run's exit 3 does (:data:`STOPPED_FOR_THE_USER_VERDICT`).
STOPPED_STEP = "stopped"
STOPPED_IN_FOREGROUND = "stopped in foreground (needs you; no detached run record)"

#: The *phase* machine's terminal words — ``status_file``'s
#: ``models_running -> models_complete/grouping_complete -> validation_pending ->
#: complete`` ladder plus the ways a phase stops without reaching ``complete``
#: (``task_generation_pending``'s host hand-off, ``subagents_failed``, an
#: explicit failure or abort).
#:
#: **The ask lane ends on its own three words**, and they are not the review
#: lanes'. ``ask_orchestrator`` closes a finished fan-out with ``completed``
#: (every model answered), ``partial`` (some did) or ``failed`` (none did) — the
#: same words it reports as ``MULTI_LLM_RESULT.state``, which is why the lane is
#: widened into here rather than made to write ``complete``. Two of the three
#: were missing and ``failed`` was already present by coincidence, so
#: :func:`_checkpoint_in_flight` answered ``True`` for every ask that ever
#: *succeeded*: a finished foreground ask rendered ``running in foreground (5/5
#: models, no detached run record)`` for the rest of the phase dir's life, and
#: ``--wait --question …`` over a detached ask whose ``run.state`` was already
#: ``done`` spent the whole resolved ``poll_s`` on every poll before exiting 0.
#:
#: **A refusal close-out is an ending too**, and the two words it writes were
#: the same gap one lane further on. ``review_orchestrator_base``'s
#: ``_print_executor_refusal`` is the exit-3 block for a run that dispatched
#: nothing, and the one caller it has ``sys.exit``\ s on the very next line — so
#: ``runner_rejected`` (the runner spec itself was rejected) and
#: ``executor_refused`` (every other pre-dispatch refusal) are the last thing
#: that run will ever write. Missing from here, they read as "still going": the
#: head line called a refused phase ``running in foreground (…)`` for the rest
#: of the dir's life and ``--wait`` spent its whole resolved deadline before
#: exiting 2 with a ``next`` that polls it again — F2's loop, over a run that
#: cannot move. The document was already being read both ways at once:
#: :func:`_resume_shape` treats a top-level ``runner_rejected`` as the refusal's
#: durable classification and renders the repair off it.
#:
#: Everything else — including a word this set has never heard of — reads as
#: "still going", which is the safe direction: being wrong that way costs a
#: ``--wait`` its own timeout, never an unbounded loop.
CHECKPOINT_TERMINAL_STATES = frozenset({
    "complete", "completed", "partial", "validation_pending",
    "task_generation_pending", "subagents_failed", "failed", "aborted",
    "stopped", "runner_rejected", "executor_refused",
})


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


def _checkpoint_in_flight(view: Dict[str, Any]) -> bool:
    """Does the *checkpoint* say this phase is still working?

    Deliberately a different question from the ``run`` record's verdict, and
    asked of a different half of the file. ``run`` is the **process** machine and
    only a detached worker writes it; the top-level ``state`` and
    ``progress.step`` are the **phase** machine and every run writes them,
    foreground included. A phase dir is re-used across runs by design (the same
    ``{plan}/review-plan/`` every time), so the two halves can legitimately
    disagree — and the disagreement that matters is a *predecessor's* terminal
    ``run`` record sitting over a *successor's* live checkpoint.

    F1, 2026-09-20: nothing drops the old ``run`` record on the foreground path,
    so a host-background re-run over a dir an earlier ``--detach`` run used
    inherits ``run.state: done``. ``--wait`` read that as terminal and came back
    in **0.11 s** with exit 0, printing ``done`` directly above a table saying
    ``running``; the instruction then relays nothing and polls again, turning a
    120-300 s loop into a tight sequence of instant tool calls for the whole
    10-30 minute run. Re-running a phase is the common path, not an edge case.

    Evidence-based, never inference: a checkpoint carrying *neither* field is not
    "in flight", so a genuinely finished foreground checkpoint still returns at
    its own deadline with exit 2 (acceptance criterion 1) rather than waiting on
    something that was never there.
    """
    state = view.get("state")
    if isinstance(state, str) and state and state not in CHECKPOINT_TERMINAL_STATES:
        return True
    step = (view.get("progress") or {}).get("step")
    if isinstance(step, str) and step and step not in CHECKPOINT_TERMINAL_STEPS:
        return True
    return False


def _names_this_run(view: Dict[str, Any], run_id: Optional[str]) -> bool:
    """Did the caller pin this poll to *this view's own* ``run`` record?

    ``--run-id`` is the only selector that names a **run**. ``--phase`` and
    ``--question`` name a *directory*, and a phase dir is re-used run after run
    by design (``{plan}/review-plan/`` every time, one ask dir per question), so
    neither can say which run the checkpoint under it belongs to. This one can:
    the caller typed the id the record carries, so the terminal record in front
    of them is the run they asked about rather than a predecessor's.

    Prefix matching, exactly as :func:`_select` resolves the same flag — every
    printed banner truncates the id to eight characters, so a prefix is what a
    caller normally has to hand.
    """
    if not run_id:
        return False
    recorded = str((view.get("run") or {}).get("run_id") or "")
    return bool(recorded) and recorded.startswith(run_id)


# ---------------------------------------------------------------------------
# Phase-dir discovery (read-only: never creates a directory)
# ---------------------------------------------------------------------------

def _ask_dirs(plan_dir: Path) -> List[Path]:
    ask_root = plan_dir / "ask"
    if not ask_root.is_dir():
        return []
    return [
        child for child in sorted(ask_root.iterdir())
        if child.is_dir() and (child / status_file.STATUS_FILENAME).exists()
    ]


def discover_phase_dirs(
    plan_path: Path, *, phase: Optional[str] = None
) -> List[Path]:
    """Every phase dir under a plan that holds a ``.status.json``.

    There is deliberately no phase *auto-detection*: this lists what it found and
    a caller that wants one run names it (``--phase``/``--run-id``/``--question``).
    A shim's poll step is therefore determined by what that shim launched, never by
    directory shape.

    Only children named in ``output_handler.PHASE_DIR_NAMES`` are phase dirs
    (plan §7.4a): a hand-made backup that copied a ``.status.json`` showed up as
    a second, duplicate run. The skipped ones are reported by
    :func:`ignored_phase_dirs`, never silently dropped. Order stays
    alphabetical by directory name.
    """
    plan_dir = output_dir_path(plan_path)
    if not plan_dir.is_dir():
        return []
    if phase:
        if phase == "ask":
            return _ask_dirs(plan_dir)
        target = phase_dir_path(plan_path, phase)
        return [target] if (target / status_file.STATUS_FILENAME).exists() else []
    found: List[Path] = []
    for child in sorted(plan_dir.iterdir()):
        if not child.is_dir():
            continue
        if child.name not in PHASE_DIR_NAMES:
            continue
        if child.name == "ask":
            found.extend(_ask_dirs(plan_dir))
            continue
        if (child / status_file.STATUS_FILENAME).exists():
            found.append(child)
    return found


def ignored_phase_dirs(plan_path: Path) -> List[str]:
    """Children of the plan's output dir that hold a ``.status.json`` but are
    not phase dirs (not in ``PHASE_DIR_NAMES``), by name (plan §7.4a2).

    A child without a ``.status.json`` is not listed: it was never going to be
    mistaken for a run.
    """
    plan_dir = output_dir_path(plan_path)
    if not plan_dir.is_dir():
        return []
    return [
        child.name for child in sorted(plan_dir.iterdir())
        if child.is_dir()
        and child.name not in PHASE_DIR_NAMES
        and (child / status_file.STATUS_FILENAME).exists()
    ]


def _dedupe_run_ids(
    views: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Two views with one ``run.run_id`` are one run (plan §7.4b).

    Keeps the view whose directory is the run's own phase dir (its basename is
    the directory word of the view's ``phase``), else the first one listed, and
    returns the others as copies: ``{"dir", "run_id", "copy_of"}``. Views with no
    ``run_id`` (a foreground checkpoint, a ``full`` run's driven phase dirs) are
    never deduped.
    """
    by_id: Dict[str, List[Dict[str, Any]]] = {}
    for view in views:
        run_id = str((view.get("run") or {}).get("run_id") or "")
        if run_id:
            by_id.setdefault(run_id, []).append(view)
    dropped: Dict[int, Dict[str, Any]] = {}
    for run_id, group in by_id.items():
        if len(group) < 2:
            continue

        def _own(view: Dict[str, Any]) -> bool:
            phase = view.get("phase") or (view.get("run") or {}).get("mode")
            if not phase:
                return False
            return os.path.basename(view["phase_dir"]) == PHASE_DIRECTORIES.get(
                str(phase), str(phase)
            )

        keep = next((v for v in group if _own(v)), group[0])
        for view in group:
            if view is not keep:
                dropped[id(view)] = {
                    "dir": _view_dir_name(view),
                    "run_id": run_id,
                    "copy_of": _view_dir_name(keep),
                }
    kept = [v for v in views if id(v) not in dropped]
    copies = [dropped[id(v)] for v in views if id(v) in dropped]
    return kept, copies


def _view_dir_name(view: Dict[str, Any]) -> str:
    """A view's directory relative to the plan's output dir (``ask/<q>`` for ask)."""
    path = Path(view["phase_dir"])
    if path.parent.name == "ask":
        return f"ask/{path.name}"
    return path.name


def _ignored_text(ignored: Sequence[str], copies: Sequence[Dict[str, Any]]) -> List[str]:
    """The one-line reports for skipped non-phase dirs and duplicate-run copies."""
    lines: List[str] = []
    if ignored:
        lines.append(f"ignored (not a phase dir): {', '.join(ignored)}")
    for copy in copies:
        lines.append(
            f"ignored (copy of run {str(copy['run_id'])[:8]} in "
            f"{copy['copy_of']}): {copy['dir']}"
        )
    return lines


def _select(
    views: List[Dict[str, Any]],
    *,
    run_id: Optional[str],
    question: Optional[str],
    include_all: bool,
) -> List[Dict[str, Any]]:
    """Apply the selectors, then the ask listing rule."""
    if run_id:
        return [
            v for v in views
            if str(v["run"].get("run_id", "")).startswith(run_id)
        ]
    if question:
        slug = slugify_question(question)
        return [
            v for v in views
            if v.get("question") == question
            or os.path.basename(v["phase_dir"]).startswith(slug)
        ]
    if include_all:
        return views
    # Ask dirs multiply: report every non-terminal run plus the most recently
    # updated terminal one, so a poller sees what is live without a wall of
    # history. Non-ask phases are one dir each, so this is a no-op for them.
    ask_views = [v for v in views if _is_ask(v)]
    other = [v for v in views if not _is_ask(v)]
    live = [v for v in ask_views if v["verdict"] not in detach.TERMINAL_VERDICTS]
    terminal = [v for v in ask_views if v["verdict"] in detach.TERMINAL_VERDICTS]
    terminal.sort(key=lambda v: str(v.get("updated_at") or ""))
    return other + live + terminal[-1:]


def _is_ask(view: Dict[str, Any]) -> bool:
    return os.path.basename(os.path.dirname(view["phase_dir"])) == "ask"


# ---------------------------------------------------------------------------
# Exit codes
# ---------------------------------------------------------------------------

def exit_code_for(views: Sequence[Dict[str, Any]]) -> int:
    """``0`` terminal-done, ``2`` non-terminal, ``3`` terminal-needs-human.

    The exit code *is* the loop condition, so a shim never parses JSON just to
    decide whether to keep going. With several runs in view the worst case wins in
    poll-loop order: anything still moving is ``2`` (come back), then needs-human,
    then done. ``2`` keeps its documented "nothing for the caller to do (yet)"
    meaning rather than inventing a status-only code — including the "no run
    recorded" case, which must never be ``0`` (a poll loop would read that as
    finished; the loop's own ceiling is what bounds it).
    """
    if not views:
        return EXIT_NOTHING_TO_DO
    if any(v["verdict"] not in detach.TERMINAL_VERDICTS for v in views):
        return EXIT_NOTHING_TO_DO
    for view in views:
        if view["verdict"] in (detach.VERDICT_FAILED, detach.VERDICT_ABORTED):
            return EXIT_NEEDS_HUMAN
        if view["run"].get("exit_code") not in (EXIT_OK, EXIT_NOTHING_TO_DO, None):
            return EXIT_NEEDS_HUMAN
    return EXIT_OK


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _workflow_payload(
    plan_path: Path, *, host_id: Optional[str] = None
) -> Dict[str, Any]:
    """Today's ``--status`` JSON, from today's implementation.

    *host_id* is this poll's ``--host`` (:func:`_reader_host`): the early
    sandbox warning resolves the subagent runner for it, and the servers
    declare their host only there (adversarial review, 2026-10-02).
    """
    from .state_manager import StateManager

    try:
        import check_workflow_prerequisites as prereq  # type: ignore
    except ImportError:  # pragma: no cover - only when utils/ is sys.path[0]
        sys.path.insert(0, str(Path(os.path.abspath(__file__)).parent.parent))
        import check_workflow_prerequisites as prereq  # type: ignore

    # A poll: read-only, so it never rewrites the file a run is writing.
    state = StateManager(plan_path, read_only=True)
    return prereq.get_workflow_status(
        state, plan_path, output_dir_path(plan_path), host_id=host_id,
    )


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
    from . import next_phase

    if len(views) == 1 and (args.phase or args.question or args.run_id):
        recorded = next_phase.recorded_plan_spelling(
            (views[0].get("run") or {}).get("plan_arg"), str(plan_path),
        )
        if recorded:
            return recorded
    return str(args.plan_file)


def _document_word(plan_path: Path) -> str:
    """``commit brief`` when *plan_path*'s ``state.json`` records a
    ``commit_range``, else ``plan``: what a line ``status`` prints calls the
    document it reads (plans/review-commits.md §2.8, "'Commit brief', never
    'plan'"), through the one owner of the word, ``commit_review.document_label``.
    Read-only; an unreadable state is a plan."""
    try:
        from .commit_review import document_label, read_commit_range

        return document_label({"commit_range": read_commit_range(plan_path)})
    except Exception:  # noqa: BLE001 - advisory: the plan's word stands
        return "plan"


def _document_file_label(plan_path: Path) -> str:
    """``Plan file`` as today, or ``Commit brief`` (:func:`_document_word`)."""
    word = _document_word(plan_path)
    return "Plan file" if word == "plan" else word.capitalize()


def _recorded_route(
    args: argparse.Namespace, views: Sequence[Dict[str, Any]], plan_path: Path,
) -> Optional[str]:
    """The route the commands of this view's plan were started on (fix round
    24): a poll pinned to one run takes that run's record (:func:`_run_route`),
    anything else the newest run of the reader's host under the plan
    (``next_phase.recorded_route``). ``None`` when none is on record."""
    from . import next_phase

    host = _reader_host(args)
    if len(views) == 1 and (args.phase or args.question or args.run_id):
        return _run_route(views[0], host)
    return next_phase.recorded_route(plan_path, host)


def manual_close_note(
    payload: Dict[str, Any], plan_spelling: str, host_id: Optional[str],
    recorded_route: Optional[str] = None,
) -> Optional[str]:
    """How to record the deferred manual tasks done, in *host_id*'s spelling.

    ``next_phase.manual_close_note`` over the workflow payload's
    ``phases.implement.manual_tasks`` (fix round 14: Codex racing 06/08
    listed T007 and never said how to close it). ``None`` when nothing is
    owed or the host has no command template for this route.
    *recorded_route* is the route the plan's run was started on
    (:func:`_recorded_route`), for a reader that names none (fix round 24).
    """
    import io

    from . import next_phase

    # The manual tasks themselves, never a code task skipped with one
    # (`next_phase.manual_close_ids`, fix round 16); while a manual-task gate
    # holds, the gate's alone (`manual_note_ids`, fix round 29).
    implement = payload.get("phases", {}).get("implement") or {}
    ids = next_phase.manual_note_ids(implement)
    if not ids:
        return None

    try:
        host = host_capabilities.resolve_host_id(explicit=host_id)
        # The route's one stderr line, if any, is the emitter's to print.
        template = host_capabilities.next_command_template(
            host, next_phase.resolve_route(
                host, stderr=io.StringIO(), recorded=recorded_route),
        )
    except Exception:  # noqa: BLE001 - advisory: the list still stands
        return None
    return next_phase.manual_close_note(
        next_phase.close_command(template, plan_spelling, ids), len(ids),
        # Fix round 28: never "No later phase waits" beside code tasks that do.
        waiting=next_phase.manual_waiting_count(implement, ids),
        named=next_phase.manual_note_named(implement, ids),
    )


def _workflow_trailer_lines(
    payload: Dict[str, Any], *, prefix: str = "  ",
    close_note: Optional[str] = None,
    suggested: bool = True,
    carried: Optional[Any] = None,
) -> List[str]:
    """The workflow view's ``suggested next``/``notice`` lines, alone
    (without the ``suggested next`` line when *suggested* is false).

    Split out of ``render_workflow_text`` so the terminal ``--view run`` carry-
    over (F7, 2026-09-16, below) renders the identical text instead of a second
    hand-typed copy that could drift from it — the whole point is that the two
    channels can never say something different about the same ``state.json``.

    *carried* is the ``user_next_step`` answer (``next_phase.NextPhase``) the
    same result carries: a line its ``markdown`` already says is left out —
    a notice that is one of its optional entries' ``why`` and, when it lists
    manual tasks, the manual-tasks line (fix round 26, live run 11: Codex
    04/06/08 and OpenCode 03-08 relayed the notice above the copied section,
    so the user read the same sentence twice).
    """
    said_whys = {
        plain_line(getattr(step, "why", "") or "")
        for step in (getattr(carried, "optional_before", None) or ())
    } - {""}
    manual_said = bool(getattr(carried, "manual_tasks", None))
    lines: List[str] = []
    if suggested and payload.get("suggested_next"):
        # `suggested_next` already skips every optional phase in its way
        # (`check_workflow_prerequisites.get_workflow_status`'s own
        # `OPTIONAL_PHASES` walk), so the bare word reads as "nothing else is
        # outstanding" — a weak model given only this line, and the tool's own
        # `next: null` beside it, asserted exactly that (F8, 2026-09-16). Name
        # the optional phases it stepped over: the ones still `pending` that
        # sit *before* it in phase order (`payload["phases"]` preserves that
        # order), not every pending optional phase regardless of position — an
        # optional phase further down the table has not been skipped for this
        # suggestion, it just has not been reached yet.
        pending_optional = []
        for phase, info in payload.get("phases", {}).items():
            if phase == payload["suggested_next"]:
                break
            if info.get("optional") and info.get("status") == "pending":
                pending_optional.append(phase)
        suffix = (
            f"  ({' / '.join(pending_optional)} optional, not run)"
            if pending_optional else ""
        )
        from .next_phase import gate_resume_suggested

        gate = gate_resume_suggested(payload)
        if gate:
            # Fix round 29 (review of round 28 #4): implement finished with
            # code tasks waiting on a manual task the user can do now, and
            # every other surface leads with its resume, as this does.
            answers = " ".join(gate[1:])
            ids = ", ".join(
                flag.split("=", 1)[0] for flag in gate[2::2])
            lines.append(
                f"{prefix}suggested next: implement  (resume it with "
                f"{answers} once you have done {ids} by hand; or "
                f"{payload['suggested_next']}, over the code implement has "
                f"run so far)")
        else:
            lines.append(f"{prefix}suggested next: {payload['suggested_next']}{suffix}")
    for notice in payload.get("notices", []) or []:
        if plain_line(notice) in said_whys:
            continue
        lines.append(f"{prefix}notice: {notice}")
    # The implement tasks the run deferred (`phases.implement.manual_tasks`,
    # read from state.json). A workflow with nothing left to suggest printed
    # no trailer at all, so a finished plan with two manual playthroughs still
    # owed read as done (2026-10-04, OpenCode racing re-run).
    manual = (payload.get("phases", {}).get("implement") or {}).get("manual_tasks")
    manual_line: Optional[str] = None
    if isinstance(manual, list) and manual:
        from .next_phase import ManualTask

        # One rendering with the `[MANUAL_TASK]` line: a task skipped with a
        # manual one says what it waits on (fix round 17).
        named = "; ".join(
            ManualTask(
                str(entry["id"]), entry.get("title") or None,
                str(entry["waits_on"]) if entry.get("waits_on") else None,
                # Fix round 28: a later manual task names the code it comes after.
                tuple(str(t) for t in entry.get("after") or ()
                      if isinstance(entry.get("after"), list)),
            ).line()
            for entry in manual
            if isinstance(entry, dict) and entry.get("id")
        )
        if named:
            # Appended last, below: its note ends with the command that
            # records the tasks done, and a joined `notice` must not run on
            # past it (live run 8, Codex racing 08 fenced the text after it).
            manual_line = (
                f"{prefix}manual tasks left for you: {named}"
                + (f". {close_note}" if close_note else "")
            )
    # The implement check tasks that ran and reported problems
    # (`phases.implement.check_findings`, from state.json; racing re-run 4,
    # 2026-10-05). Shown while implement is unfinished — its findings are
    # newer than any review on record — and, once it has completed, until a
    # review-code that judged it has completed or the review was skipped.
    # Fix round 11 (review finding 5): keyed on review-code alone, an
    # `implement --resume` that recorded new findings beside an older
    # completed review hid them until implement finished, and a skipped
    # review kept them on screen for good.
    phases = payload.get("phases", {}) or {}
    findings = (phases.get("implement") or {}).get("check_findings")
    implement_done = (phases.get("implement") or {}).get("status") == "completed"
    review_settled = (phases.get("code-review") or {}).get("status") in (
        "completed", "skipped",
    )
    if isinstance(findings, list) and findings and not (implement_done and review_settled):
        named = "; ".join(
            f"{entry['id']} ({len(entry.get('findings') or [])} problem(s): "
            f"{clip((entry.get('findings') or [''])[0], 120)}"
            f"{', …' if len(entry.get('findings') or []) > 1 else ''})"
            for entry in findings
            if isinstance(entry, dict) and entry.get("id")
        )
        if named:
            lines.append(
                f"{prefix}check findings for review-code (see "
                f"implement/summary.md): {named}"
            )
    # The implement tasks whose own check failed after their edits
    # (`phases.implement.batch_check_findings`, fix round 15), shown by the
    # same rule as the check findings above.
    failing = (phases.get("implement") or {}).get("batch_check_findings")
    if isinstance(failing, list) and failing and not (implement_done and review_settled):
        # Fix round 16: the task's own report, quoted (Codex racing 06r).
        named = "; ".join(
            f"{entry['id']} (\"{clip((entry.get('findings') or [''])[0], 120)}\""
            f"{', …' if len(entry.get('findings') or []) > 1 else ''})"
            for entry in failing
            if isinstance(entry, dict) and entry.get("id")
        )
        if named:
            lines.append(
                f"{prefix}a task's own report says a check it ran fails (see "
                f"implement/summary.md): {named}"
            )
    # And those whose own check reported again only the findings the user
    # accepted for a check (`phases.implement.batch_check_accepted`, fix
    # round 23), by the same rule: not a failure, but on record.
    accepted_reruns = _accepted_reruns_by_task(
        (phases.get("implement") or {}).get("batch_check_accepted"))
    if accepted_reruns and not (implement_done and review_settled):
        lines += [
            f"{prefix}{clause} — not counted as a failure (see implement/summary.md)"
            for clause in accepted_rerun_clauses(accepted_reruns)
        ]
    # Fix round 28: and those whose own check reported only what a check
    # task of the run reported (`phases.implement.batch_check_repeats`).
    repeats = _accepted_reruns_by_task(
        (phases.get("implement") or {}).get("batch_check_repeats"))
    if repeats and not (implement_done and review_settled):
        lines += [
            f"{prefix}{clause} — not counted as its own failure (see implement/summary.md)"
            for clause in repeated_check_clauses(repeats)
        ]
    if manual_line and not manual_said:
        lines.append(manual_line)
    return lines


def render_workflow_text(
    payload: Dict[str, Any], *, close_note: Optional[str] = None,
) -> List[str]:
    lines = ["workflow (state.json) — which phases are done:"]
    width = max((len(p) for p in payload.get("phases", {})), default=0)
    for phase, info in payload.get("phases", {}).items():
        extra = []
        if info.get("optional"):
            extra.append("optional")
        if info.get("reason"):
            extra.append(str(info["reason"]))
        if info.get("tasks_total"):
            extra.append(f"{info.get('tasks_done', 0)}/{info['tasks_total']} tasks")
        if info.get("timestamp"):
            extra.append(str(info["timestamp"]))
        suffix = f"  ({', '.join(extra)})" if extra else ""
        lines.append(f"  {phase.ljust(width)}  {info.get('status', '?')}{suffix}")
    lines.extend(_workflow_trailer_lines(payload, close_note=close_note))
    return lines


def render_run_text(
    views: Sequence[Dict[str, Any]],
    *,
    plan_path: Path,
    workflow: Optional[Dict[str, Any]],
    scope: Optional[str] = None,
    resume_workflow: Optional[Dict[str, Any]] = None,
    implement_tally: Optional[Dict[str, Any]] = None,
    state_block: bool = False,
    spell: Optional[Speller] = None,
) -> List[str]:
    # *spell* (`user_speller`): the user's commands below in the host's
    # spelling (fix round 18); `None` keeps the dispatcher command.
    # The workflow payload the resume block may consult without rendering the
    # workflow lines above it (`--view run`'s terminal read); see `_resume_lines`.
    resume_workflow = workflow if workflow is not None else resume_workflow
    lines = ["runs ({phase}/.status.json) — is a launched run still alive:"]
    if not views:
        if not state_block:
            # A native implement read back from state.json follows instead
            # (`render_state_implement_lines`, fix round 16).
            lines.append(
                f"  no run recorded for {scope or 'this ' + _document_word(plan_path)}")
        return lines
    outer_spell = spell
    for view in views:
        run = view["run"]
        # Fix round 24: each run's commands in the route that started it.
        spell = _view_speller(outer_spell, view)
        name = os.path.basename(view["phase_dir"])
        head = f"  {name}"
        if run.get("run_id"):
            head += f"  run {str(run['run_id'])[:8]}"
        head += f"  {_verdict_text(view)}"
        lines.append(head)
        if view.get("question"):
            lines.append(f"      question: {view['question']}")
        # Three state fields, three lines, never collapsed.
        lines.append(f"      run.state:      {_run_state_text(view)}")
        lines.append(f"      phase state:    {view.get('state') or '(none)'}")
        if workflow is not None:
            phase_name = view.get("phase") or name
            wf = (workflow.get("phases") or {}).get(phase_name, {})
            wf_status = wf.get("status", "not tracked")
            # N7, 2026-09-16: `phases_completed` records that a phase finished
            # once — a `--resume` can reopen it (implement picking up tasks a
            # later review sent back), and a live run under an already-
            # `completed` phase is the resulting, entirely valid state. Printed
            # bare, "completed" sits beside `run.state: running` and is the one
            # word on screen a reader is likely to take at face value and stop
            # watching, so a live run under a completed phase says so rather
            # than reading like a stale cache.
            # F4, 2026-09-17: `stale` covers both "slow to beat" and "provably
            # gone but not yet closed out"; only the first is live. A dead run
            # printed "completed (re-running since …)" two lines under its own
            # `died (pid N gone, …)`, which reads as the opposite of the truth.
            live_verdict = view["verdict"] in (
                detach.VERDICT_STARTING, detach.VERDICT_RUNNING,
            ) or (view["verdict"] == detach.VERDICT_STALE and not _died(view))
            if wf_status == "completed" and live_verdict:
                started = run.get("started_at")
                suffix = f" (re-running since {started})" if started else " (re-running)"
                lines.append(f"      workflow phase: completed{suffix}")
            elif wf.get("stale"):
                # Completed, but before implement's latest completion
                # (`get_workflow_status` marks it `stale`): the done run under
                # it judged an earlier state of the code. Printed bare,
                # `pending` under a done run fell into the "not yet marked"
                # note below, whose `advance it with:` is the run's own
                # `--reaggregate` — which re-stamps the stale review
                # (adversarial review, 2026-10-02). The way forward is a plain
                # re-run of the phase, never the reaggregate.
                lines.append(
                    f"      workflow phase: pending (stale: completed "
                    f"{wf.get('completed_at') or '?'}, before implement's "
                    f"latest completion {wf.get('implemented_at') or '?'})"
                )
                if view["verdict"] == detach.VERDICT_DONE:
                    # Its own review stale too (apply-code-fixes under a stale
                    # code-review): the review is what to re-run, since the
                    # apply phase's gate refuses until it has.
                    review = _stale_review_of(phase_name, workflow)
                    lines.append(
                        "      note: run complete, but it judged the code "
                        "before the latest implement; re-run "
                        + (f"{review} first" if review else "it")
                    )
                    lines.append(
                        f"      re-run it with: "
                        f"{_rerun_command(view, plan_path, mode=review, spell=spell)}"
                    )
            else:
                lines.append(f"      workflow phase: {wf_status}")
            if (
                view["verdict"] == detach.VERDICT_DONE
                and wf_status == "pending"
                and not wf.get("stale")
            ):
                lines.append(
                    "      note: run complete; workflow phase not yet marked "
                    "completed"
                )
                advance = view.get("reaggregate_command") or dispatcher_command(
                    "status", str(plan_path), "--view", "workflow"
                )
                lines.append(f"      advance it with: {advance}")
        if view.get("progress"):
            lines.append(
                f"      progress:       "
                f"{_progress_text(view['progress'], phase=_view_dir_name(view))}"
            )
            if implement_tally is not None and _is_executor_implement_view(view):
                # Fix round 16: the line above counts this run's batches; this
                # one every task of the phase, every run (state.json).
                lines.append(
                    f"      all tasks:      "
                    f"{implement_tally_text(implement_tally, live=_run_is_live(view))}"
                )
            # Between the counts and the table, and INSIDE this guard by
            # decision rather than by accident: the delta is computed from
            # `progress.models` (see `_attach_finished_during_wait`), so a
            # non-empty one proves a non-empty `progress` and this guard can
            # never suppress a line that had something to say. Putting it
            # outside would be dead code that reads like a hedge. Its place in
            # the block is the reading order the answer needs — "3/5 done" then
            # "which three", then the roster they sit in.
            just_finished = _just_finished_text(view)
            if just_finished:
                lines.append(f"      {JUST_FINISHED_LABEL} {just_finished}")
            # ADDITIVE, and deliberately under the same guard: a models-only
            # table that *replaced* the line above would hide the validation and
            # write-phase mirrors, which are the only progress a dispatch-only
            # phase such as `generate-tasks` records. A view whose `progress`
            # carries no `models` map therefore renders exactly as it did before
            # this table existed.
            lines.extend(_model_table_lines(view))
        if run.get("host"):
            # The host that *launched* the run, which is not necessarily the one
            # reading this: without it nothing on screen said whose subagent
            # runner the block below is about (measured 2026-09-16, an opencode
            # run polled from Claude Code).
            lines.append(f"      host:           {run['host']}")
        if run.get("pid"):
            # The identity probe only runs for a non-terminal record — a finished
            # run's pid is history, and probing it would invite exactly the
            # recycled-pid confusion the probe exists to prevent.
            identity = view.get("identity")
            lines.append(
                f"      pid {run['pid']}"
                + (f" ({identity})" if identity else " (recorded)")
                + (f", cwd {run.get('cwd')}" if run.get("cwd") else "")
            )
        if run.get("log_path"):
            lines.append(f"      log: {run['log_path']}")
        if view["output_files"]:
            lines.append("      output_files:")
            for key in sorted(view["output_files"]):
                lines.append(f"        {key}: {view['output_files'][key]}")
        consolidation = _consolidation_text(view.get("consolidation_recommended"))
        if consolidation:
            lines.append(f"      {consolidation}")
        validation_context_line = _validation_context_text(
            view.get("validation_context")
        )
        if validation_context_line:
            lines.append(f"      {validation_context_line}")
        for note in _run_notes(view):
            lines.append(f"      note: {note}")
        # F4: recorded only for a finished code-review run — `high_priority_groups`
        # is written once, at the very end of main(), so a mid-run poll has
        # nothing to render yet, and the key exists on no other phase.
        if view.get("phase") == "code-review" and view["verdict"] == detach.VERDICT_DONE:
            high_priority = _high_priority_text(view.get("high_priority_groups"))
            if high_priority:
                lines.append(f"      {high_priority}")
        if run.get("resolutions"):
            lines.append("      auto-resolved while you were gone:")
            for entry in run["resolutions"]:
                lines.append(
                    f"        {entry.get('site')}: {entry.get('decision')} "
                    f"({entry.get('at')})"
                )
        if _died(view):
            # The exit-3 block a terminal failure gets, one heartbeat window
            # early: the run is over and no amount of polling will change that,
            # so the resume command is handed over now rather than after the
            # close-out. `reason` carries what the probe saw.
            lines.append(f"      {view.get('reason')}")
            lines.extend(_resume_lines(view, plan_path, resume_workflow, spell))
        if view["verdict"] in (detach.VERDICT_FAILED, detach.VERDICT_ABORTED):
            lines.append(f"      exit_code: {run.get('exit_code')}")
            # A worker that returned non-zero with no stop line and no crash
            # closes out with no `error`; printed raw, that read `error: None`
            # (Fable review 2026-10-09).
            if run.get("error"):
                lines.append(f"      error:     {run.get('error')}")
            tail = detach._log_tail(run.get("log_path") or "", 20)
            if tail:
                lines.append("      last log lines:")
                lines.append(tail)
            lines.extend(_resume_lines(view, plan_path, resume_workflow, spell))
    return lines


def _result_state(view: Dict[str, Any]) -> Optional[str]:
    """The run's carried result word (``partial``), or ``None``.

    Only a finished run that exited 0 carries one: ``run.result_state`` is
    written by the detached worker's close-out, bounded by
    ``detach.carried_result_state`` there and again here, so a missing, ``null``
    or hand-edited value reads as absent and a clean exit-0 run stays ``done``.
    """
    run = view.get("run") or {}
    if view.get("verdict") != detach.VERDICT_DONE:
        return None
    if run.get("exit_code") != EXIT_OK:
        return None
    return detach.carried_result_state(run.get("result_state"))


def _failed_model_specs(view: Dict[str, Any]) -> List[str]:
    """Which slots failed, for the text view's ``partial`` note.

    ``models_failed`` is the checkpoint's own record of the fan-out's losses
    (read from the file: the run view does not carry it); a phase that keeps
    no such key falls back to the ``failed`` rows of ``progress.models``.
    """
    try:
        failed = status_file.read_status(view["phase_dir"]).get("models_failed")
    except Exception:  # advisory text only; never fail the poll over it
        failed = None
    if isinstance(failed, dict) and failed:
        return sorted(str(spec) for spec in failed)
    if isinstance(failed, list) and failed:
        return [str(spec) for spec in failed]
    models = (view.get("progress") or {}).get("models")
    if isinstance(models, dict):
        return sorted(
            str(spec) for spec, entry in models.items()
            if isinstance(entry, dict) and entry.get("state") == STATE_FAILED
        )
    return []


def _run_state_text(view: Dict[str, Any]) -> str:
    """``run.state``, annotated when the run's result was ``partial`` (plan §5).

    ``run.state`` keeps its process meaning (``done``); the note says what the
    exit code could not: ``done (partial — failed: codex:gpt-6-astra:xhigh)``.
    """
    word = (view.get("run") or {}).get("state") or "(none)"
    result = _result_state(view)
    if result is None:
        if _stopped_for_the_user(view):
            # Fix round 22: what the record means is said. Fix round 23
            # (review of round 22, #4): "nothing crashed" only when nothing
            # it ran failed. Fix round 26 (live run 11 #6): the text no
            # longer says "failed" under the "stopped and needs you" head.
            # Only the text: the stored word stays `failed`, because
            # `TERMINAL_RUN_STATES`, `classify_run`'s verdict, `exit_code_for`,
            # the run registry's sweep, the close-out's retirement of a
            # non-`done` run's slots and `--json`'s `runs[].run.state` all key
            # on it, and the records already on disk say it.
            crashed = "" if _a_dispatch_failed(view) else f"; {NOTHING_CRASHED}"
            return f"{STOPPED_RUN_STATE_WORD} ({STOPPED_FOR_THE_USER_GLOSS}{crashed})"
        return str(word)
    failed = _failed_model_specs(view)
    detail = f" — failed: {', '.join(failed)}" if failed else ""
    return f"{word} ({result}{detail})"


#: How ``status`` reads a run that ended needing the user (exit 3), whose run
#: record says ``failed`` (fix round 22, live run 9 #5: Codex 01b's poll read
#: "run … failed" for a resume that stopped where the first run had, needing
#: the user's answer, as the stop's own text said).
STOPPED_FOR_THE_USER_VERDICT = "stopped and needs you (exit 3)"
#: The ``run.state:`` line of such a run (fix round 26, live run 11 #6:
#: "failed (exit 3: …)" under the head above). The record keeps ``failed``.
STOPPED_RUN_STATE_WORD = "stopped"
STOPPED_FOR_THE_USER_GLOSS = "exit 3: the run needs you"
#: Added to the gloss only when no runner and no model of the run failed
#: (:func:`_a_dispatch_failed`, fix round 23): a stop on a refusal, a check's
#: findings or an unanswered manual task.
NOTHING_CRASHED = "nothing crashed"


def _a_dispatch_failed(view: Dict[str, Any]) -> bool:
    """Whether something the run dispatched failed: a write task whose
    runner ran and failed (the write mirror's ``runner_failed_task_ids``;
    a mirror written before fix round 23 has only ``failed_task_ids``, read
    as is), a read task, or a fan-out model."""
    progress = view.get("progress") if isinstance(view.get("progress"), dict) else {}
    write = progress.get("write_subagents")
    if isinstance(write, dict):
        ran = write.get("runner_failed_task_ids")
        if ran if isinstance(ran, list) else write.get("failed_task_ids"):
            return True
    read = progress.get("subagents")
    if isinstance(read, dict) and read.get("failed_task_ids"):
        return True
    return bool(_failed_model_specs(view))


def _stopped_for_the_user(view: Dict[str, Any]) -> bool:
    """A terminal run record that ended with exit 3, the needs-a-human code
    every mode shares."""
    run = view.get("run") or {}
    return (
        view.get("verdict") == detach.VERDICT_FAILED
        and run.get("exit_code") == EXIT_NEEDS_HUMAN
    )


def _died(view: Dict[str, Any]) -> bool:
    """The run is non-terminal on paper and its process is provably gone.

    ``classify_run`` calls this ``stale`` and closes it out as
    ``failed(heartbeat_timeout)`` once the beat expires, which is right — but
    for up to ``HEARTBEAT_STALE_AFTER_S`` the only honest word for a pid the
    identity probe says is dead is "died", not "running (stale)". F2,
    2026-09-16: a write subagent's ``killall -9 … python3`` SIGKILLed the
    detached worker that dispatched it, and every poll for the next minute
    reported the dead run as running.
    """
    return (
        view.get("verdict") == detach.VERDICT_STALE
        and view.get("identity") == process_control.DEAD
    )


def _verdict_text(view: Dict[str, Any]) -> str:
    verdict = view["verdict"]
    age = view.get("heartbeat_age_s")
    if _died(view):
        pid = view["run"].get("pid")
        beat = f"last beat {age:.0f}s ago" if age is not None else "never beat"
        return f"died (pid {pid} gone, {beat})"
    if verdict == detach.VERDICT_STALE:
        return (
            f"running (stale, last beat {age:.0f}s ago)" if age is not None
            else "running (stale, never beat)"
        )
    if verdict == detach.VERDICT_RUNNING and age is not None:
        return f"running (last beat {age:.0f}s ago)"
    if verdict == detach.VERDICT_FAILED and view.get("reason") == "heartbeat_timeout":
        return "failed (heartbeat_timeout — the worker died without recording an outcome)"
    if _stopped_for_the_user(view):
        return STOPPED_FOR_THE_USER_VERDICT
    if verdict == detach.VERDICT_NO_RUN:
        # "Checkpoint but no run record" stopped being an oddity the moment a
        # foreground run started writing `progress`: it is the normal Claude
        # Code state, because that host is told never to pass `--detach` and
        # only the detached worker ever calls `claim_run`. The bare word
        # `no_run`, printed beside `run.state: (none)`, reads as "nothing
        # happened here" for a phase that is at that moment dispatching eight
        # models.
        #
        # ONLY THE TEXT CHANGES. The verdict constant stays `no_run`, so
        # `TERMINAL_VERDICTS`, `exit_code_for`'s exit 2 and F1's rule that a
        # `no_run` phase is never the `next` poll target are all untouched —
        # making it terminal is explicitly out of scope, and `status --wait`
        # terminating on a foreground checkpoint depends on it staying
        # non-terminal.
        #
        # F3, 2026-09-20: the gate was `if progress:` alone, so the word
        # "running" survived the phase it described. A finished foreground
        # checkpoint — `state: complete`, `progress.step: complete` — still
        # printed `running in foreground (2/2 models, no detached run record)`
        # with `phase state: complete` two lines below it, and rule 1 tells the
        # agent to relay that head line *verbatim*. Every completed Claude Code
        # phase, and every historical ask dir a bare `status` lists, reported
        # itself as running forever. The tense now comes from the checkpoint,
        # which is the only half of the file a foreground run writes.
        #
        # "finished" claims exactly one thing — this phase is no longer
        # working — and never that it succeeded: how it ended is the
        # `phase state:` line right below, which prints `complete`,
        # `subagents_failed` or whatever the phase wrote.
        progress = view.get("progress") or {}
        if progress.get("step") == STOPPED_STEP:
            # Fix round 23 (review of round 22, #2): the write mirror's stop,
            # which read "finished in foreground" while the same ending
            # detached heads "stopped and needs you (exit 3)".
            return STOPPED_IN_FOREGROUND
        if progress:
            tense = "running" if _checkpoint_in_flight(view) else "finished"
            total = progress.get("models_total")
            if isinstance(total, int) and not isinstance(total, bool) and total:
                done = progress.get("models_done", 0)
                return (
                    f"{tense} in foreground ({done}/{total} models, no detached "
                    "run record)"
                )
            return f"{tense} in foreground (no detached run record)"
    return str(verdict)


def _consolidation_text(recommendation: Any) -> Optional[str]:
    """The optional "you may want to consolidate" line, or ``None``.

    The `[CONSOLIDATION_RECOMMENDED]` marker is a log line, and nobody polling a
    detached run reads the log — so this one sentence is where a host learns the
    recommendation exists. It names the command and never *is* one: the phase is
    complete, and `--consolidate` is the caller's decision.
    """
    if not isinstance(recommendation, dict):
        return None
    groups = recommendation.get("valid_groups")
    threshold = recommendation.get("threshold")
    command = recommendation.get("command") or "--consolidate"
    if not isinstance(groups, int) or not isinstance(threshold, int):
        return None
    return (
        f"consolidation recommended: {groups} valid groups >= {threshold} "
        f"— run {command}"
    )


def _validation_context_text(obj: Any) -> Optional[str]:
    """The phase's ``validation_context`` line (plan §2.4), or ``None``.

    Rendered from the published object only — never recomputed — so the poll
    text, ``MULTI_LLM_RESULT`` and ``report.md`` say the same thing. A
    ``mode: path`` source reads "excerpt inline + full snapshot by path",
    never "inlined in full".
    """
    return validation_context_text(obj if isinstance(obj, dict) else None)


def _validation_context_notice(views: Sequence[Dict[str, Any]]) -> Optional[str]:
    """The truncation sentence(s) over every view, in discovery order, or ``None``."""
    sentences: List[str] = []
    for view in views:
        notice = validation_context_notice(view.get("validation_context"))
        if notice and notice not in sentences:
            sentences.append(notice)
    return join_clauses(sentences) or None


def _write_result_notice(views: Sequence[Dict[str, Any]]) -> Optional[str]:
    """The write mirror's own notice parts over every view, or ``None``.

    Fix round 14: a code batch whose own check failed after its edits
    (``write_subagents.tasks[].batch_check_findings``) and the line saying
    nothing ran the repository's tests (``write_subagents.unverified``) —
    what the worker recorded on its own result line, which a detached caller
    never sees. Read from the run's own mirror, so it describes that run.
    """
    return clip(join_clauses(_write_result_notice_parts(views)), 1200) or None


def _write_result_notice_parts(views: Sequence[Dict[str, Any]]) -> List[str]:
    """:func:`_write_result_notice`'s parts, unjoined (fix round 26: a stop's
    poll leaves out a part its `error` already says)."""
    try:
        from .write_batch_scheduler import batch_check_summary
    except ImportError:  # pragma: no cover - direct script runs
        from utils.write_batch_scheduler import batch_check_summary  # type: ignore
    parts: List[str] = []
    for view in views:
        mirror = (view.get("progress") or {}).get("write_subagents")
        if not isinstance(mirror, dict):
            continue
        found = {
            str(row.get("task_id")): [str(item) for item in row["batch_check_findings"]]
            for row in mirror.get("tasks") or []
            if isinstance(row, dict) and isinstance(row.get("batch_check_findings"), list)
            and row["batch_check_findings"]
        }
        if found:
            parts.append("not a clean finish: " + batch_check_summary(found))
        unverified = mirror.get("unverified")
        if isinstance(unverified, str) and unverified and unverified not in parts:
            parts.append(unverified)
    return parts


def _high_priority_text(high_priority: Any) -> Optional[str]:
    """The one line naming a finished code-review's distinct HIGH groups.

    F4: `[HIGH_PRIORITY_ISSUES] <n>` is a log line, and a detached caller never
    reads the log — this is where a host polling `status` actually learns the
    single most actionable fact a code review produces, the same way
    `_consolidation_text` surfaces `[CONSOLIDATION_RECOMMENDED]`.
    """
    if not isinstance(high_priority, dict):
        return None
    count = high_priority.get("count")
    if not isinstance(count, int):
        return None
    return f"high-priority groups: {count}"


#: What ``_progress_text`` says when the checkpoint's ``progress`` object holds
#: nothing it knows how to render. A sentinel rather than an empty string
#: because the human view prints this line unconditionally and a blank after
#: ``progress:`` reads as a renderer that failed; :func:`_current_state_text`
#: reads it back to mean "there is nothing to show", which is the one caller
#: that has somewhere else to go.
NO_PROGRESS_RECORDED = "(none recorded)"


def _generated_count(progress: Dict[str, Any], phase: Optional[str]) -> Optional[int]:
    """How many tasks a ``generate-tasks`` run produced, or ``None``.

    ``tasks_generated`` is what that phase writes; a checkpoint written before
    the key existed carried the same count as a ``tasks_total``/``tasks_done``
    pair, which is read the same way under that phase alone.
    """
    generated = progress.get("tasks_generated")
    if isinstance(generated, int) and not isinstance(generated, bool):
        return generated
    total = progress.get("tasks_total")
    if (phase == "generate-tasks" and isinstance(total, int) and total
            and progress.get("tasks_done") == total):
        return total
    return None


def _progress_text(progress: Dict[str, Any], *, phase: Optional[str] = None) -> str:
    """The ``progress:`` line; *phase* is the view's phase dir, when known."""
    parts = []
    if progress.get("step"):
        parts.append(str(progress["step"]))
    if progress.get("models_total"):
        # `models_done` counts *finished slots* (done + failed), so it only ever
        # moves forwards and reaches `models_total` even on a lossy run — which
        # is what a live line needs. `models_succeeded` carries the other half:
        # before it existed, the post-fan-out restatement recomputed successes
        # into the same key and a run that lost a model ended on `models 3/4`,
        # a numerator walking backwards at the very end. Rendered together the
        # information survives as `8/8 done, 7 ok, 1 failed`.
        #
        # This one line is what Layer 2's rule 1 tells an agent to relay
        # verbatim, so its shape is load-bearing; the clause degrades to today's
        # bare `models 8/8` when `models_succeeded` is absent, which is every
        # checkpoint written before the key existed.
        done = progress.get("models_done", 0)
        clause = f"models {done}/{progress['models_total']}"
        succeeded = progress.get("models_succeeded")
        if isinstance(succeeded, int) and not isinstance(succeeded, bool):
            failed = done - succeeded if isinstance(done, int) else 0
            clause += f" done, {succeeded} ok, {max(failed, 0)} failed"
        parts.append(clause)
    generated = _generated_count(progress, phase)
    if generated is not None:
        # What that run produced, labelled as such: a `tasks 10/10` pair read
        # as a live count of tasks.md and went stale the moment
        # apply-task-suggestions split a task (2026-10-04).
        parts.append(f"generated {generated} task{'' if generated == 1 else 's'}")
    elif progress.get("tasks_total"):
        parts.append(f"tasks {progress.get('tasks_done', 0)}/{progress['tasks_total']}")
    if progress.get("batches_total"):
        parts.append(
            f"batch {progress.get('batch_index', 0)}/{progress['batches_total']}"
        )
    if progress.get("failed_task_ids"):
        parts.append(f"failed {', '.join(map(str, progress['failed_task_ids']))}")
    # The executor's mirrors (`subagent_executor._mirror_status` under
    # `subagents`, `write_batch_scheduler._mirror_status` under
    # `write_subagents`) are the only progress a dispatch-only phase such as
    # `generate-tasks` records — it never calls `report_progress(step=…)` before
    # the end — so a line that read only the step keys printed "(none recorded)"
    # beside a mirror that said `ok: 1`. Measured 2026-09-14.
    for key in ("subagents", "write_subagents"):
        parts.extend(_mirror_text(key, progress.get(key)))
    # D6 override (2026-09-17): a detached fan-out records the slots it ran
    # without the runner's own sandbox under `progress.sandbox_bypassed`, and
    # a host polling `status` is told so here — the `[SANDBOX_BYPASSED]` line
    # is in a log a detached caller never reads.
    bypassed = progress.get("sandbox_bypassed")
    if isinstance(bypassed, list) and bypassed:
        parts.append(f"unsandboxed {', '.join(map(str, bypassed))}")
    # Landlock rung (2026-09-22): a slot on a *contained* fallback rung is
    # recorded under `progress.sandbox_fallback` as `{spec: rung}` and rendered
    # by rung name — never as "unsandboxed", which is the one thing it was not.
    contained = progress.get("sandbox_fallback")
    if isinstance(contained, dict) and contained:
        by_rung: Dict[str, List[str]] = {}
        for spec, rung in contained.items():
            by_rung.setdefault(str(rung), []).append(str(spec))
        for rung in sorted(by_rung):
            parts.append(
                f"{_fallback_clause_head(rung)} {rung} {', '.join(sorted(by_rung[rung]))}"
            )
    return ", ".join(parts) or NO_PROGRESS_RECORDED


#: The rung ids of an **incidental** grade (plan codex-sandbox-unavailable-
#: findings-and-fixes §7, "Step 2 subtask: messaging and markers", item 3;
#: 2026-09-30). A closed set spelled here — `status` reads recorded data and
#: imports no provider code — whose slots render as `stray-writes-only <rung>`:
#: the plugin's Landlock jail stops stray writes, not the model, so the one
#: word a real OS boundary earns (`sandbox-fallback`) is never its word. The
#: clause names no phase, so a read-only slot and a write dispatch share it.
INCIDENTAL_RUNG_IDS = frozenset({"plugin-landlock"})


def _fallback_clause_head(rung: str) -> str:
    """``stray-writes-only`` for an incidental rung, ``sandbox-fallback`` for a
    contained one (the legacy ``landlock`` renders exactly as before)."""
    return "stray-writes-only" if rung in INCIDENTAL_RUNG_IDS else "sandbox-fallback"


#: A jailed slot's recorded failure reason and the key carrying its denied path
#: (plan §6 F1 "Where it sits" item 6, "When the jail denies a turn"). The
#: fan-out records both on the slot's row, so this view says what failed after
#: the log that printed the `[JAIL_DENIED]` line is gone.
JAIL_DENIED_REASON = "jail-denied"
JAIL_DENIED_PATH_KEY = "jail_denied_path"


def _entry_error_text(entry: Any) -> Optional[str]:
    """The one failure text a model row carries: ``denied by the plugin's
    jail: <path>`` for a ``jail-denied`` row (``path not named`` when codex
    named none), else the row's own ``error``, else ``None``."""
    if not isinstance(entry, dict):
        return None
    if entry.get("failure_reason") == JAIL_DENIED_REASON:
        path = entry.get(JAIL_DENIED_PATH_KEY)
        return f"denied by the plugin's jail: {path or 'path not named'}"
    error = entry.get("error")
    return str(error) if error else None


#: ``source`` values meaning "this model never dispatched on this run — its
#: result came off disk". There is deliberately no ``skipped`` *state*: the
#: terminal set stays ``done | failed`` so a resumed model counts in
#: ``models_done`` **and** ``models_succeeded`` (it has a usable result), and the
#: distinction lives in ``source``. This is the renderer reading it, which is
#: what ``source`` is for.
#:
#: ``salvage`` (``review_orchestrator_base.record_models_salvaged``) is
#: deliberately **not** in here: that slot dispatched, ran, failed to parse and
#: was repaired in-process, so it renders as the plain ``done`` it is.
SKIPPED_SOURCES = frozenset({"existing_file", "resume"})


def _one_line(text: str) -> str:
    """Collapse every run of whitespace, newlines included, into one space.

    Applied to the one field in the ``models`` map that carries provider-authored
    text: ``error``. Everything else in a row is a spec, a state word or a number
    this module produced. An adapter that puts a stderr excerpt or a wrapped
    provider message in there hands the renderers a string with ``\n`` in it, and
    both of them are *line* renderers whose output has a consumer that assumes it:
    Layer 2 rule 1 has the host agent relay ``just finished:`` **verbatim**, so a
    two-line value turns one rule-bound line into two, the second with no label on
    it, and the table's aligned columns come apart at the same time.

    One helper for both sites on purpose — folding it into only the newer
    renderer would leave the two spellings of one field disagreeing, which is the
    drift this file keeps testing against (2026-09-20).
    """
    return " ".join(str(text).split())


def _model_state_label(entry: Dict[str, Any]) -> str:
    """The word in the row's state column."""
    state = str(entry.get("state") or STATE_QUEUED)
    if state == STATE_DONE and str(entry.get("source") or "") in SKIPPED_SOURCES:
        return "skipped"
    return state


def _model_timing_text(entry: Dict[str, Any]) -> str:
    """``2m10s/30m``, ``waiting 7m45s``, or ``""`` when the entry has no clock.

    Two read-time rules, and :mod:`progress_tracker` owns both, so the ticker
    and this table cannot disagree:

    * run time, :func:`progress_tracker.entry_elapsed_s`: ``ended_at`` present
      -> the stored ``elapsed_s`` (a terminal row is frozen, so a table
      rendered an hour later still shows the slot's real duration); a live row
      -> ``now - dispatched_at`` clamped at ``timeout_s`` (``now -
      started_at`` for a map written before ``dispatched_at`` existed);
    * the wait before dispatch, :func:`progress_tracker.entry_queued_s`.

    A row still waiting for its dispatch (``queued``/``staggering``) renders
    ``waiting 7m45s`` and no budget: it has spent none, and ``7m30s/20m`` —
    what it rendered until the wait and the run were separated — read as budget
    spent (plan: review-run-scope-salvage-and-failure-visibility §6). A
    terminal row that waited at least a second before dispatching adds
    ``, queued 7m45s``, so the wait a slot paid is still on its row once the
    run is over; below a second there is nothing a ``0m00s`` would tell anyone
    (the first slot, a resume skip). Nothing stores a per-tick figure, so these
    are always fresh — including at ``progress.interval_s: 0``, where the
    ticker prints nothing at all.

    The denominator is the slot's **whole** budget, fixed for its life, never the
    shrinking slice a retry ladder hands back for the next attempt: ``2m10s/30m``
    against a shrinking denominator would overstate the budget left.

    **A clock that cannot be read renders as no clock, never as a crash** —
    and that covers the *denominator* too, which it did not until 2026-09-21:
    the ``try`` below wraps :func:`entry_elapsed_s` and nothing else, so a
    ``timeout_s: Infinity`` (a token ``json.loads`` accepts) sailed past it into
    ``format_budget`` and raised ``OverflowError`` out of the same command this
    paragraph promises will not crash. The budget now reads through
    :func:`progress_tracker.entry_budget`, the one guard the roster and the
    ticker also read, and an unrenderable one costs the denominator rather than
    the row.

    F5, 2026-09-20: ``detach._elapsed_since`` catches ``ValueError`` only, but
    ``datetime.now() - <aware datetime>`` raises ``TypeError``, so a single
    ``started_at: "2026-09-19T00:00:00Z"`` anywhere in the map took the *whole*
    ``status`` command down with a traceback and exit 1 — which rule 2 maps to
    "the run state is unreadable, stop and report", ending a poll loop over a
    perfectly healthy run. Everything else in the map already degrades (garbage
    strings, ints, ``None``, non-dict entries, a missing ``elapsed_s``); this is
    the one shape that did not. The `models` map is the least trustworthy part of
    the checkpoint — it is the only part written per slot, by whichever lane won
    the race — so the catch is deliberately broad and belongs on the *reader*:
    one malformed row costs its own column, never the command. The parser's own
    half of this (``heartbeat_at`` reads the same way) is ``detach``'s to harden.
    The wait is read under its own guard for the same reason: a wait that
    cannot be read costs the ``, queued`` clause, never the run time beside it.
    """
    terminal = bool(entry.get("ended_at"))
    if not terminal and str(entry.get("state") or "") in WAITING_STATES:
        try:
            wait = entry_queued_s(entry)
        except Exception:
            return ""
        return f"waiting {format_elapsed(wait)}" if wait is not None else ""
    try:
        elapsed = entry_elapsed_s(entry)
    except Exception:
        return ""
    if elapsed is None:
        return ""
    budget = entry_budget(entry)
    if budget is not None and budget > 0:
        text = f"{format_elapsed(elapsed)}/{format_budget(budget)}"
    else:
        text = format_elapsed(elapsed)
    if terminal:
        try:
            wait = entry_queued_s(entry)
        except Exception:
            wait = None
        if wait is not None and wait >= 1.0:
            text += f", queued {format_elapsed(wait)}"
    return text


def _model_detail_text(entry: Dict[str, Any]) -> str:
    """The trailing clause: the attempt, the pending backoff, the failure reason.

    ``attempt`` has no denominator on purpose — the ladder keeps transport
    retries and rate-limit backoffs as two independent counters, so an entry can
    never honestly render ``2/3`` — and it is only worth a column once it is past
    the first. ``error`` is terminal-only, so a row carrying one has already
    stopped.
    """
    details: List[str] = []
    attempt = entry.get("attempt")
    if isinstance(attempt, int) and not isinstance(attempt, bool) and attempt > 1:
        details.append(f"attempt {attempt}")
    if str(entry.get("state") or "") == STATE_RETRYING:
        retry_after = entry.get("retry_after_s")
        if isinstance(retry_after, (int, float)) and not isinstance(retry_after, bool):
            details.append(f"retry in {retry_after:.0f}s")
    # `starts in 4s`: the launch ramp, named. Slots dispatch
    # `index * PROVIDER_STAGGER_DELAY` apart, and the launch-time poll — taken at
    # second zero on purpose, for the roster — met every row but the first
    # reading `staggering`, which a reader took for the fan-out running its
    # models one at a time (2026-09-21). The state word is the lifecycle's and
    # stays; the clause says how long, in the shape `retry in 20s` already
    # has. Rounded *up*, so a slot 0.4 s from dispatch reads `1s`, never `0s`
    # — and `entry_stagger_remaining_s` is `None` once the stamp is past, so
    # a poll landing on the flip renders no clause rather than a countdown
    # that reached zero and stayed.
    remaining = entry_stagger_remaining_s(entry)
    if remaining is not None:
        details.append(f"starts in {math.ceil(remaining)}s")
    # A jailed slot's `jail-denied` row names the denied path (2026-09-30).
    error = _entry_error_text(entry)
    if error:
        details.append(_one_line(error))
    return ", ".join(details)


def _model_row_specs(view: Dict[str, Any], models: Dict[str, Any]) -> List[str]:
    """Which specs get a row, in the order the run requested them.

    The tracker seeds every requested spec ``queued`` *before* it creates the
    tasks, so in the normal case the map is already complete and its own keys are
    the answer. The exception is the window between a run's launch and that seed
    — and on a re-run of a phase dir, what a poll lands in that window reads is
    the *predecessor's* map. Dropping the specs that are missing from it would
    make the table quietly disagree with the ``models N/M`` count one line above,
    so they are rendered ``queued`` with no timings instead.

    That makes the row count **at least** ``models_total``, not exactly it: any
    key the map holds that ``models_requested`` does not is appended rather than
    hidden, because the one way a map grows such a key is
    ``FanoutProgress._entry`` seeding a spec some lane transitioned without
    requesting — a wiring mistake, and hiding it in the one table that could show
    it would be the wrong trade. The two lists agreeing is the normal state: the
    three launch writes drop the predecessor's ``progress`` outright (F1,
    2026-09-20), so a map surviving next to a *different* run's
    ``models_requested`` is no longer a shape this can meet.

    The checkpoint's top-level ``models_requested`` is the only record of the
    canonical spec list, and ``classify_run``'s view does not carry it (it is a
    top-level key, not a ``progress`` one), so it is read here — on the one path
    that needs it, gated on the map actually being short. ``render_run_text``
    already reads a file on a branch of its own (``detach._log_tail``), so the
    precedent for a read in the renderer is in the same function.
    """
    specs = [str(spec) for spec in models]
    total = (view.get("progress") or {}).get("models_total")
    if not isinstance(total, int) or isinstance(total, bool) or total <= len(specs):
        return specs
    requested = view.get("models_requested")
    if not isinstance(requested, list):
        try:
            requested = status_file.read_status(
                str(view.get("phase_dir") or "")
            ).get("models_requested")
        except Exception:  # pragma: no cover - an unreadable dir renders the map
            requested = None
    if not isinstance(requested, list):
        return specs
    ordered: List[str] = []
    for raw in requested:
        spec = str(raw)
        if spec not in ordered:
            ordered.append(spec)
    for spec in specs:
        if spec not in ordered:
            ordered.append(spec)
    return ordered


def _model_table_lines(view: Dict[str, Any]) -> List[str]:
    """The per-model rows beneath the one-line ``progress:`` summary.

    Rendered for **every** verdict, ``no_run`` included: a foreground run is the
    normal Claude Code state and holds no ``run`` record at all, so a table
    behind a "live run" guard would be invisible on the one host this feature is
    written for.

    ASCII only. Every host redirects the orchestrator's stdout to a file and a
    poll's output is read back through whatever codec that file took, so a
    separator that survives as ``?`` is worse than one that was ASCII to begin
    with.

    **An absent map is not an absent roster** (2026-09-20). The child writes
    ``models_requested`` and calls ``report_progress(step="fanout",
    models_total=N)`` *before* it constructs the tracker that seeds the map, so
    for the first seconds of every fan-out the view knows the whole roster and
    this rendered nothing at all: the launch-time poll printed ``running in
    foreground (1/5 models, no detached run record)`` over ``models 1/5 done``
    and never said which CLI was running which model — the question the user
    asked for after watching a real run. An absent or non-dict map is therefore
    read as ``{}`` rather than taken as a reason to return, and
    :func:`_model_row_specs` answers from ``models_requested``.

    The *empty* answer is still the empty table, and that is load-bearing in the
    other direction: a dispatch-only phase such as ``generate-tasks`` records no
    ``models_total`` (its only progress is the executor's mirror), so
    ``_model_row_specs`` returns nothing for it and it grows no bare ``models:``
    header — which is what it did before this table existed and what
    ``test_a_progress_object_with_no_models_map_renders_as_it_always_did``
    pins.
    """
    progress = view.get("progress") or {}
    models = progress.get("models")
    if not isinstance(models, dict):
        models = {}
    specs = _model_row_specs(view, models)
    if not specs:
        return []
    rows: List[Tuple[str, str, str, str]] = []
    for spec in specs:
        entry = models.get(spec)
        entry = entry if isinstance(entry, dict) else {}
        rows.append((
            spec,
            _model_state_label(entry),
            _model_timing_text(entry),
            _model_detail_text(entry),
        ))
    spec_width = max(len(row[0]) for row in rows)
    label_width = max(len(row[1]) for row in rows)
    timing_width = max(len(row[2]) for row in rows)
    lines = ["      models:"]
    for spec, label, timing, detail in rows:
        cells = f"{spec.ljust(spec_width)}  {label.ljust(label_width)}"
        if timing_width:
            cells = f"{cells}  {timing.ljust(timing_width)}"
        if detail:
            cells = f"{cells}  {detail}"
        lines.append(f"        {cells.rstrip()}")
    return lines


#: The label on the line that names what crossed the line during the wait.
#:
#: One spelling, two readers: :func:`render_run_text` prints it indented under
#: the ``progress:`` line, and :func:`_progress_lines` prefixes the same
#: renderer's output with it for a host that shows the line on its own, where a
#: bare list of specs and durations would not say what it was a list *of*.
JUST_FINISHED_LABEL = "just finished:"


def _just_finished_text(view: Dict[str, Any]) -> str:
    """``codex:gpt-6-astra:xhigh (4m12s, done)``, or ``""`` when nothing did.

    Renders ``view["finished_during_wait"]``, which only ``--wait`` ever writes
    (see :func:`_attach_finished_during_wait`): the specs that crossed into a
    terminal state *while this very command was waiting*. That window is the
    whole claim — ``just`` is a tense, and a plain poll can prove a row is
    finished but not that it finished since anyone last looked.

    Why it exists at all: the ``progress:`` line one row above carries counts
    (``models 3/5 done, 3 ok, 0 failed``) and Layer 2 rule 1 forbids relaying
    anything else mid-run, so a user watching a fan-out was told *how many* had
    finished and never *which*. A spec is the CLI and the model — nothing has to
    be derived to answer it.

    Three shape decisions, all deliberate:

    * Clauses are joined with ``; `` and **not** ``, ``, because the clause's own
      interior is comma-separated (``4m12s, done``); a comma join would render
      two models as four indistinguishable fields.
    * The state word is :func:`_model_state_label`'s, so this line and the table
      under it use one vocabulary for one row: ``done``, ``failed``, or
      ``skipped`` for a resume that landed mid-wait. ``ok`` is deliberately not
      in it — that is the *counting* line's word for a slot that produced a
      usable result, and a row labelled ``ok`` here would sit directly above the
      same row labelled ``skipped`` in the table.
    * The elapsed is the frozen duration with **no** ``/budget`` denominator.
      Every table row carries one because a live row needs the comparison; a row
      that has stopped does not, and ``4m12s/30m`` invites reading the budget as
      time still available. It is run time, counted from the slot's first
      dispatch, so a slot that never dispatched reads ``0m00s``; the wait in
      front of the run stays on the ``models:`` row (``, queued 7m45s``) rather
      than being added here (plan: review-run-scope-salvage-and-failure-
      visibility §6.2).

    One line and ASCII, through the **same** scrub the roster takes
    (:func:`progress_tracker.one_line_ascii`), applied to the whole composed
    line rather than to one field of it. That claim used to be made here and
    not kept: ``_one_line`` covered ``error`` alone, no ASCII scrub ran at all,
    so ``codex:gpt–5`` (en dash, out of a config file) and ``café`` went
    through, and a spec key carrying a newline put a second, unlabelled line
    into a renderer whose whole contract is one line — which on the OpenCode
    package route, where ``toastMessage`` joins the supplied lines with a
    newline, is a line forged in a display the user reads as the dispatcher's
    own. The two renderers that feed ``progress_lines`` now scrub identically;
    that is the point of the shared helper, since a spec reaches both of them
    by the same route.

    ``_one_line`` still runs on ``error`` here, where it also runs in the table
    (one spelling of one field), and the whole-line pass behind it is what
    covers the spec and every separator this function composes.

    A clause that cannot be built is dropped rather than raising — same rule as
    :func:`_model_timing_text`, for the same reason: ``status`` is the command a
    poll loop runs, so one malformed entry costs its own clause and never the
    command. The elapsed was already reduced to a plain number by the attach
    side, so the only raising left here would be a caller-supplied entry that is
    not a dict.
    """
    entries = view.get("finished_during_wait")
    if not isinstance(entries, list):
        return ""
    clauses: List[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        spec = str(entry.get("spec") or "")
        if not spec:
            continue
        label = str(entry.get("state") or "") or STATE_DONE
        error = entry.get("error")
        if label == STATE_FAILED and error:
            label = f"{label}: {_one_line(error)}"
        fields: List[str] = []
        elapsed = entry.get("elapsed_s")
        if isinstance(elapsed, (int, float)) and not isinstance(elapsed, bool):
            fields.append(format_elapsed(elapsed))
        fields.append(label)
        clauses.append(f"{spec} ({', '.join(fields)})")
    return one_line_ascii("; ".join(clauses))


def _progress_lines(view: Dict[str, Any]) -> List[str]:
    """The run's progress as **rendered text**, for a reader that cannot render.

    The `progress` object rides the result line whole (`record_progress`), which
    is the right shape for a reader that can turn a map into a sentence. The
    OpenCode **package** route cannot: there is no agent in its poll loop at all
    — the plugin's `execute` supervises the run and the model makes one blocking
    tool call — so nothing there reads `instructions/*.md`, nothing relays a
    `[PROGRESS]` line out of a log the plugin never opens, and the plugin's own
    rule forbids it to compose a sentence about a run. Measured 2026-09-21: a
    5 m 40 s four-model fan-out reached the user as silence and then one
    compressed line, with a complete `progress.models` map and twelve ticker
    lines sitting in artifacts nobody on that route reads.

    So the lines are composed here, by the renderers that already own their
    wording, and shipped ready to display:

    * the fan-out roster (:func:`render_roster_line`) — what the run is *over*,
      which never changes, so a reader that shows it once has said it;
    * the current state (:func:`_current_state_text`) — the fan-out ticker's own
      ``[PROGRESS]`` line while a slot is live, the ``progress:`` line the human
      view prints once they are all terminal. It is the line that is there on
      **every** poll, changed or not, which is what keeps a host from falling
      back to a serialized object on the ordinary poll where nothing finished;
    * the ``just finished:`` line (:func:`_just_finished_text`) — what crossed
      into terminal *during this call's own wait*, which is the one thing the
      counts structurally cannot say and the only news a poll carries.

    Order is roster, state, news — what the run is over, what it is doing, what
    moved — which is the reading order and the order they are composed in below.
    The last two are also the order the human view prints them in
    (``progress:`` then ``just finished:``).

    The **roster** is the one this list adds. It used to be claimed that all of
    this was "the order `render_run_text` prints them in", which was false:
    that renderer prints the counts line, then `just finished:`, then the
    per-model table, and it never prints the roster at all —
    `render_roster_line` occurs in this module at its import and in this
    function, and nowhere else. The roster's
    own homes are the orchestrator log (`FanoutProgress.seed` emits it there)
    and the `--detach` launch's result line (`detach.launch` renders it from the
    resolved selection) — both surfaces this route cannot read, which is the
    whole reason the line is composed here as well. So only the second of these
    two lines is also a line a human reading `status` sees; the first is one
    that view never had.

    Nothing is invented for this surface either way: both strings come from
    renderers that exist independently of it, and neither is reworded here.

    The two renderers are called bare, which is the same decision
    :func:`render_run_text` makes two inches away: both answer a checkpoint they
    do not control, so each one type-checks what it reads
    (:func:`render_roster_line` per budget, :func:`_just_finished_text` per
    clause) and a caller that wrapped a second hedge around them would be
    hedging against a defence it can see. A view with no map — ``generate-tasks``,
    an apply phase, a run predating the tracker — simply renders nothing, and
    the key never reaches the result line at all.

    The one thing that **is** checked here is that ``progress`` is a mapping,
    and that check is about the *caller*, not about the file:
    :func:`detach.classify_run` coerces a torn ``progress`` to ``{}`` while it
    builds the view (pinned by
    ``test_the_view_carries_a_mapping_whatever_the_file_says``), so no view this
    module assembles can fail it. It is kept because this is a plain module
    function over a dict and the result-line site calls it *outside* the
    ``if view.get("progress")`` guard the text renderer sits behind — an
    ``AttributeError`` here is exit 1, which rule 2 reads as "the run state is
    unreadable, stop and report", paid for a key that is display-only. Pinned at
    that level, directly, rather than through a checkpoint that can no longer
    produce the shape.
    """
    progress = view.get("progress")
    if not isinstance(progress, dict):
        return []
    lines: List[str] = []
    roster = render_roster_line(progress.get("models"))
    if roster:
        lines.append(roster)
    current = _current_state_text(
        progress, phase=_view_dir_name(view) if view.get("phase_dir") else None,
    )
    if current:
        lines.append(current)
    just_finished = _just_finished_text(view)
    if just_finished:
        lines.append(f"{JUST_FINISHED_LABEL} {just_finished}")
    # Fix round 14: a finished run's notes follow its counts, so a host that
    # relays these lines verbatim relays "1 not applied" beside "10/10 items
    # applied" (Codex racing re-run 5 reported "Applied 10 of 10").
    lines.extend(f"note: {note}" for note in _run_notes(view))
    return lines


def _has_live_row(models: Any) -> bool:
    """Is any slot still queued, staggering, running or retrying?

    The boundary between the two tickers the orchestrator log already switches
    between: :class:`progress_tracker.FanoutProgress` narrates while this is
    true and :class:`progress_tracker.PhaseProgress` takes over when it is not.
    :func:`_current_state_text` picks the same way, from the checkpoint, so the
    package route sees the same changeover a log reader does.

    A row that is not a mapping is not live — it is a row nothing can be said
    about, which is how every other renderer treats it — and a mapping with no
    ``state`` is, matching :func:`_model_state_label`'s ``queued`` default.
    """
    if not isinstance(models, dict):
        return False
    return any(
        isinstance(entry, dict)
        and str(entry.get("state") or "") not in TERMINAL_STATES
        for entry in models.values()
    )


def _current_state_text(
    progress: Dict[str, Any], *, phase: Optional[str] = None,
) -> str:
    """One line saying what the run is doing *now*, or ``""`` when nothing is.

    The third thing a reader with no agent in the loop needs, beside the roster
    ("what is this over") and the news ("what just moved"): **the state**, on
    every poll, whether or not anything changed. Without it the plugin's toast
    fell back to ``JSON.stringify(update)`` on any poll whose window contained
    no completion — measured 2026-09-21 on a 363 s run, a multi-KB blob, and
    that is the ordinary case rather than an edge one, since a 90 s window
    containing a completion is the exception.

    Two renderers, picked by the boundary the log already switches at
    (:func:`_has_live_row`) and neither of them new:

    * while a slot is still live, :func:`progress_tracker.render_progress_line`
      — the fan-out ticker's own ``[PROGRESS]`` line, counts plus the live rows
      with their elapsed. That elapsed is derived at read time from
      ``started_at``, so two polls ninety seconds apart really do render
      different strings, which is what the host's shown-once memory needs to
      keep showing it;
    * once every slot is terminal — validation, grouping, a write phase, a
      dispatch-only phase like ``generate-tasks`` that has no map at all —
      :func:`_progress_text`, the ``progress:`` line the human view prints and
      the one Layer 2 rule 1 already has an agent relay verbatim. It carries the
      step and the executor mirrors, which is what moves in that window.

    Neither is reworded here and no third spelling is introduced; ``status``
    simply says which of its own two lines answers the question right now.
    ``(none recorded)`` is a renderer with nothing to say, not a state, so it is
    dropped rather than displayed — that is the one case that still leaves a
    poll with no line of its own.
    """
    models = progress.get("models")
    if _has_live_row(models):
        line = render_progress_line(models)
        if line:
            return line
    text = _progress_text(progress, phase=phase)
    return "" if text == NO_PROGRESS_RECORDED else text


def _terminal_fingerprints(view: Dict[str, Any]) -> Optional[Dict[str, tuple]]:
    """Per terminal spec, *which* ending it is — not merely that it has one.

    ``done | failed`` is the whole terminal set (there is no ``skipped`` state,
    see :data:`SKIPPED_SOURCES`), and a row that is not a dict or whose ``state``
    is a word nothing has ever written reads as not terminal.

    The value is ``(state, ended_at, elapsed_s)`` rather than the bare spec, and
    that is the whole point of this function. A phase dir is re-used run after
    run, so "this spec was already terminal when the wait began" does **not**
    mean "it did not finish during the wait": a re-review of the same plan finds
    the predecessor's finished rows on disk, the new run seeds the same specs
    ``queued``, and each one finishes again with a *new* ``ended_at``. Keyed on
    the spec alone, every one of those completions was swallowed — it was in the
    baseline before this run seeded it, and in the next poll's baseline after it
    really finished, so no poll ever announced it (F1, 2026-09-20; the source of
    the stale map is fixed at the three launch writes, and this is the half that
    still holds when a poll lands in the window *before* one of them).

    ``None`` — distinct from an empty mapping — means the map could not be read
    at all. The caller treats that as "no baseline", because an unreadable map
    that heals into a healthy one mid-wait would otherwise announce every row in
    it as having just finished.

    **A ``models`` key that is simply absent is the honest empty baseline**, not
    an unreadable one, and the two used to collapse into the same ``None``. The
    window is real and it is the launch window: the claim write drops the
    predecessor's ``progress`` outright and ``seed()`` writes this run's roster a
    moment later, so a poll landing between them reads a checkpoint carrying no
    map at all. Nothing had finished yet — which is exactly what ``{}`` says, and
    every row that turns terminal afterwards really did turn terminal during this
    wait. Read as ``None`` the whole first wait was skipped instead, so a
    ``--wait`` that spanned the launch printed no ``just finished:`` line however
    many specs ended inside it (F1, 2026-09-21). ``None`` now means only what the
    paragraph above describes: a ``models`` that is *present and not a dict*.
    """
    progress = view.get("progress") or {}
    if not isinstance(progress, dict):
        return None
    models = progress.get("models")
    if models is None:
        return {}
    if not isinstance(models, dict):
        return None
    fingerprints: Dict[str, tuple] = {}
    for raw_spec, entry in models.items():
        if not isinstance(entry, dict):
            continue
        state = str(entry.get("state") or "")
        if state not in TERMINAL_STATES:
            continue
        fingerprints[str(raw_spec)] = (
            state, str(entry.get("ended_at") or ""), str(entry.get("elapsed_s")),
        )
    return fingerprints


def _attach_finished_during_wait(
    baseline: Dict[str, Optional[Dict[str, tuple]]], views: Sequence[Dict[str, Any]]
) -> None:
    """Record, on each returned view, which specs went terminal during the wait.

    *baseline* is what :func:`_wait_for_terminal` saw when it was entered, keyed
    by ``phase_dir`` — per phase dir and not one flat set, because a poll with no
    selector lists every phase under the plan and two of them can legitimately be
    running the same spec; one flat set would let one phase's model silence the
    other's.

    Order is the map's own key order, which is the tracker's seed order (the
    order the run requested the models in), matching the table below it. It is
    deliberately *not* sorted by ``ended_at``: the stamps are written by whichever
    lane won the race and two rows finishing in the same second would reorder a
    line whose only job is to be read next to the table.

    A view whose ``phase_dir`` is not in the baseline is skipped rather than
    treated as an empty baseline. Such a view was discovered *during* the wait
    (another process opened a phase dir under this plan), so nothing here saw its
    "before" — and every terminal row in it would be announced as having just
    finished on no evidence at all. A dir that appeared mid-wait gets its roster
    from the table like any other first sighting. A dir whose baseline is
    ``None`` is skipped for the same reason: its map was unreadable when the wait
    began, so nothing was observed about it either (F4, 2026-09-20).

    A spec is announced when its terminal *fingerprint* differs from the one the
    baseline holds — a different ending, not merely a second sighting of the same
    one. That is what makes the line survive a re-used phase dir, where the specs
    that finish during the wait are exactly the specs a predecessor already left
    terminal on disk; see :func:`_terminal_fingerprints`.

    **The key is set only when the list is non-empty**, and that is a
    compatibility constraint, not tidiness: ``--json`` serializes these view
    dicts raw (``payload = {"runs": views}``), so an always-present key — even
    ``[]`` — would change the bytes of every JSON poll ever made. Every value
    written here is a ``str``, a ``float`` or ``None`` for the same reason.

    **The key rides ``--json`` like every other view key.** The paragraph two
    above says why — ``payload = {"runs": views}`` serializes these dicts raw —
    so a poll run with ``--wait --json`` really does hand back
    ``runs[0]["finished_during_wait"]``. This paragraph used to claim the
    opposite ("this key itself still never leaves the view"), contradicting its
    own neighbour and in the one direction that costs something: a consumer told
    a key cannot reach it does not handle the day it does.

    What is true is narrower, and it is about ``MULTI_LLM_RESULT`` rather than
    about ``--json``: **these dicts are not put on the result line**. The
    OpenCode package route — the one host with no agent in the loop to read a
    rendered line — gets the *rendered* line there instead:
    :func:`_progress_lines` runs
    :func:`_just_finished_text` over this key and puts the result on the
    ``MULTI_LLM_RESULT`` line beside the roster, through
    :func:`cli_common.record_progress_lines`. That is deliberate and is not the
    same thing as carrying the key: the route has no renderer, so handing it
    these dicts would leave it composing the sentence itself — which the
    plugin's own rule forbids — while handing it the sentence costs it nothing
    but a display. The structured half is still there too: ``progress.models``
    rides the same line whole, states and stamps included, so a consumer that
    wants to compute rather than display never has to parse the text.
    """
    for view in views:
        key = str(view.get("phase_dir") or "")
        if key not in baseline:
            continue
        before = baseline[key]
        if before is None:
            continue
        models = (view.get("progress") or {}).get("models")
        if not isinstance(models, dict):
            continue
        finished: List[Dict[str, Any]] = []
        for raw_spec, raw_entry in models.items():
            spec = str(raw_spec)
            entry = raw_entry if isinstance(raw_entry, dict) else {}
            state = str(entry.get("state") or "")
            if state not in TERMINAL_STATES:
                continue
            now = (
                state, str(entry.get("ended_at") or ""), str(entry.get("elapsed_s")),
            )
            if before.get(spec) == now:
                continue
            try:
                elapsed = entry_elapsed_s(entry)
            except Exception:
                # The `started_at: "...Z"` shape that used to take the whole
                # command down (F5, 2026-09-20). A clause with no clock is worth
                # more than a traceback.
                elapsed = None
            if isinstance(elapsed, bool) or not isinstance(elapsed, (int, float)):
                elapsed = None
            error = _entry_error_text(entry)
            finished.append({
                "spec": spec,
                "state": _model_state_label(entry),
                "elapsed_s": float(elapsed) if elapsed is not None else None,
                "error": error,
            })
        if finished:
            view["finished_during_wait"] = finished


#: The close-out's own word for a needs-human exit with no reason recorded
#: (`detach.RunHandle.finish`): not a "last line" worth relaying.
GENERIC_NEEDS_HUMAN_ERROR = "needs_human (exit 3)"


#: The phase whose tasks :func:`state_implement_view` reads back from
#: ``state.json``, and the report whose absence marks a run the host drove.
_IMPLEMENT_PHASE = "implement"
_WRITE_REPORT = "write_batch_report.json"


def _implement_buckets(
    state: Any, *, merge: Optional[Mapping[str, str]] = None,
) -> Tuple[Dict[str, List[str]], Dict[str, str]]:
    """Every task of implement's decomposition in one bucket of
    :data:`_TALLY_LABELS`, in decomposition order, and ``{dependent: manual
    task}`` for the ``deferred_dependents`` bucket: the one classifier
    :func:`implement_task_tally` and :func:`state_implement_view` share
    (fix round 17: they kept two copies, and both listed a code task skipped
    with a manual one as "deferred manual"). *merge* folds a bucket into
    another (the view's coarser ``accepted``). *state* is a read-only
    ``StateManager``; the decomposition must be on record.
    """
    from .write_batch_scheduler import (
        ACCEPTED_REASON_PREFIX,
        ACCEPTED_WITH_FINDINGS_MARK,
    )

    record = state.state
    statuses = state.implementation_task_statuses()
    reasons = record.get("task_status_reasons") or {}
    human = {str(t) for t in (record.get("implement_human_task_ids") or [])}
    findings = {entry["id"] for entry in state.implementation_check_findings()}
    merge = merge or {}
    buckets: Dict[str, List[str]] = {
        merge.get(key, key): [] for key, _ in _TALLY_LABELS
    }
    waits_on: Dict[str, str] = {}
    for task_id in [str(t) for t in record.get("implement_task_ids") or []]:
        status = statuses.get(task_id)
        reason = str(reasons.get(task_id) or "")
        if status == "completed":
            if reason.startswith(ACCEPTED_REASON_PREFIX):
                key = ("accepted_findings" if ACCEPTED_WITH_FINDINGS_MARK in reason
                       else "accepted_failed")
            elif task_id in human and "--human-task" in reason:
                key = "completed_manual"
            elif task_id in findings:
                key = "check_findings"
            else:
                key = "completed"
        elif status == "failed":
            key = "failed"
        elif status == "skipped":
            if reason.startswith((state._USER_DECLINED_REASON, state._ANSWERED_SKIP_PREFIX)):
                key = "declined"
            elif not state._deferred_to_user(task_id):
                key = "declined_dependents"
            else:
                root = state.deferral_root(task_id)
                if root is not None and root != task_id:
                    key = "deferred_dependents"
                    waits_on[task_id] = root
                else:
                    key = "deferred"
        else:
            key = "not_run"
        buckets[merge.get(key, key)].append(task_id)
    return buckets, waits_on


def _bucket_clauses(
    buckets: Mapping[str, Sequence[str]], waits_on: Mapping[str, str],
    labels: Sequence[Tuple[str, str]], *, live: bool = False,
) -> List[str]:
    """``<label>: <ids>`` per non-empty bucket, in *labels*' order. The
    dependents of a deferred manual task read "skipped (depends on manual
    T005): T006", one clause per manual task (fix round 17)."""
    parts: List[str] = []
    for key, label in labels:
        ids = list(buckets.get(key) or [])
        if not ids:
            continue
        if key == "deferred_dependents":
            for root in sorted({str(waits_on.get(tid) or "") for tid in ids}):
                waiting = [tid for tid in ids if str(waits_on.get(tid) or "") == root]
                named = f"skipped (depends on manual {root})" if root else label
                parts.append(f"{named}: {', '.join(waiting)}")
            continue
        if key == "not_run" and live:
            label = "pending"
        parts.append(f"{label}: {', '.join(ids)}")
    return parts


def state_implement_view(
    plan_path: Path, views: Sequence[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Implement's tasks as ``state.json`` records them, when nothing else does.

    Fix round 14 (live run 5, the stop path on Claude Code): the native leg
    hands its batches to the host, which writes no ``write_batch_report.json``
    and no write mirror, so ``status --view run`` listed no implement task at
    all while ``state.json`` held every status, reason, check finding and
    answer. This reads them back — only when the implement phase dir has no
    report, no listed view carries a write mirror for it, and the plan has an
    implement decomposition on record that is started and not completed — as
    ``{tasks, titles, buckets, reasons, findings, answers}``. Read-only;
    ``None`` when it does not apply.

    Fix round 16 (live run 6, Claude Code racing 06): a native implement the
    host completed is read back too (``completed: true``): `status --view
    run` printed "no run recorded for phase implement" after it, since the
    native leg leaves nothing else that view reads.
    """
    from .state_manager import StateManager

    implement_dir = phase_dir_path(plan_path, _IMPLEMENT_PHASE)
    if (implement_dir / _WRITE_REPORT).exists() and native_leg_stamp(implement_dir) is None:
        # Fix round 26: an executor report beside a native emit's newer
        # `write_tasks.json` is an earlier run's (`superseded_by_native`).
        return None
    for view in views:
        if (view.get("phase") or os.path.basename(str(view.get("phase_dir") or ""))) \
                != _IMPLEMENT_PHASE:
            continue
        progress = view.get("progress") if isinstance(view.get("progress"), dict) else {}
        if isinstance(progress.get("write_subagents"), dict):
            return None
    try:
        state = StateManager(plan_path, read_only=True)
    except Exception:  # noqa: BLE001 - advisory: the run view is not
        return None
    record = state.state
    decomposition = record.get("implement_task_ids")
    statuses = state.implementation_task_statuses()
    if not isinstance(decomposition, list) or not decomposition:
        return None
    completed = state.is_phase_completed(_IMPLEMENT_PHASE)
    if not (completed or state.is_phase_started(_IMPLEMENT_PHASE) or statuses):
        return None
    reasons = record.get("task_status_reasons") or {}
    titles = record.get("task_titles") or {}
    buckets, waits_on = _implement_buckets(state, merge=_VIEW_MERGE)
    answers = record.get("human_task_decisions")
    # The workflow trailer's rule for both kinds of findings (fix round 11):
    # once implement completed, shown until a review-code that judged them
    # completed or was skipped.
    settled = completed and (
        state.is_phase_completed("code-review") or state.is_phase_skipped("code-review")
    )
    tally_buckets, _waits = _implement_buckets(state)
    # Fix round 20 (live run 8, Claude Code stop): the workflow view's own
    # test for an implement a `--resume` continues (`get_workflow_status`:
    # started on the host, or a task of its decomposition recorded done).
    resumable = not completed and (
        state.is_phase_started(_IMPLEMENT_PHASE)
        or any(statuses.get(str(t)) == "completed" for t in decomposition)
    )
    in_progress_since = None if completed else _host_run_started_at(
        record, _IMPLEMENT_PHASE)
    stop_answers: List[Dict[str, Any]] = []
    stop_resume_why: Optional[str] = None
    stopped = bool(
        resumable and not in_progress_since and native_run_stopped(record, statuses))
    gate_flags: List[str] = []
    if resumable:
        from .write_batch_scheduler import native_resume_why, native_stop_answers

        stop_answers = native_stop_answers(record)
        # Fix round 22: what the plain resume does, as `util next-command`
        # says it above the resume.
        stop_resume_why = native_resume_why(
            record, phase_dir=str(phase_dir_path(plan_path, _IMPLEMENT_PHASE)))
        # Fix round 28 (live run 12, Codex racing 06): every code task left
        # waits on a manual task the user can do now, so the resume records
        # it done; the run stopped for the user.
        gate_flags, gate_why, gate_answers = _native_manual_gate(state)
        if gate_flags:
            stop_resume_why = gate_why or stop_resume_why
            stopped = not in_progress_since
            # Fix round 29 (review of round 28 #1): and the user's decline.
            stop_answers = list(stop_answers) + gate_answers
    return {
        "completed": completed,
        # Fix round 20: whether `--implement <plan> --resume` continues it,
        # and the `--human-task` answers its stop waits for, as the native
        # `util next-command` gives them (`{flags, why}`, `--resume` first).
        "resumable": resumable,
        "stop_answers": stop_answers,
        "stop_resume_why": stop_resume_why,
        # Fix round 28: the flags the resume carries after the plan.
        "resume_flags": gate_flags,
        # Fix round 24 (live run 10, Claude Code stop 01/01b): whether the
        # run ended short and waits for the user, as the executor routes'
        # "stopped and needs you" head says (:func:`native_run_stopped`).
        "stopped": stopped,
        # Fix round 25 (stops #3): the tasks a stopped run's host could
        # still run, which the resume runs (:func:`native_still_runnable`).
        "still_runnable": native_still_runnable(record, statuses) if stopped else [],
        # Fix round 18 (Claude Code racing 06, mid-run): when the host's loop
        # is between `util metrics start` and `finish`.
        "in_progress_since": in_progress_since,
        # Fix round 19: when state.json last changed, so a loop that ended
        # without `util metrics finish` can be told from a live one.
        "state_changed_at": _state_changed_at(state.state_file),
        # The executor routes' `all tasks:` tally, every task in one bucket
        # (fix round 18: the native leg printed a coarser `tasks:` line).
        "tally": {
            "total": len(decomposition),
            "done": sum(len(tally_buckets[key]) for key in _TALLY_DONE),
            "buckets": tally_buckets,
            "waits_on": waits_on,
        },
        "tasks": [str(t) for t in decomposition],
        "titles": {str(k): str(v) for k, v in titles.items()},
        "buckets": buckets,
        # Fix round 17: what each `deferred_dependents` task waits on.
        "waits_on": waits_on,
        "reasons": {
            task_id: str(reasons[task_id])
            for task_id in buckets["failed"] + buckets["not_run"]
            if reasons.get(task_id)
        },
        "findings": [] if settled else state.implementation_check_findings(),
        # A code task whose own check failed after its edits (fix round 15).
        "batch_checks": [] if settled else state.implementation_batch_check_findings(),
        # And one whose own check repeated the accepted findings (round 23).
        "batch_check_accepted": [] if settled else state.implementation_batch_check_accepted(),
        # And one whose own check repeated a check task's finding (round 28).
        "batch_check_repeats": [] if settled else state.implementation_batch_check_repeats(),
        "answers": dict(answers) if isinstance(answers, dict) else {},
    }


def native_still_runnable(
    record: Mapping[str, Any], statuses: Mapping[str, Any],
) -> List[str]:
    """The tasks of a native implement that waits for an answer which the
    host could still run without it, in task order (fix round 25): every
    task of the decomposition not recorded completed, skipped or failed that
    is not manual, not held by a check's findings and not after a failed
    task. ``[]`` when nothing waits for an answer, or the record cannot be
    read."""
    from .write_batch_scheduler import _native_stop_facts

    try:
        scope = [str(t) for t in record.get("implement_task_ids") or []]
        facts = _native_stop_facts(record)
        if facts is None:
            return []
        manual = {str(t) for t in (record.get("implement_human_task_ids") or [])}
        kept_out = set(facts["failed_ids"]) | set(facts["blocked"])
        for task_id in facts["failed_ids"]:
            kept_out.update(facts["undone_with"](task_id))
    except Exception:  # noqa: BLE001 - advisory: the run view is not
        return []
    return [
        task_id for task_id in scope
        if statuses.get(task_id) not in ("completed", "skipped", "failed")
        and task_id not in manual and task_id not in kept_out
    ]


def _native_manual_gate(
    state: Any,
) -> Tuple[List[str], Optional[str], List[Dict[str, Any]]]:
    """``(resume flags, why, answers)`` of a native implement whose every
    code task left waits on a manual task the user can do now (fix round
    28), the words ``util next-command`` gives them — the answers being the
    user's decline of each such task (fix round 29) — else
    ``([], None, [])``."""
    from . import next_phase

    try:
        deferred = state.deferred_implementation_tasks()
        gates = state.manual_task_gates(deferred)
        if not gates or not gates.get("gated"):
            return [], None, []
        entry = {
            "manual_gate": True,
            "manual_tasks": deferred,
            "manual_close_ids": state.manual_tasks_to_close(deferred),
            "manual_waiting": gates.get("waiting") or {},
        }
        flags = next_phase.manual_gate_flags(entry)
        if not flags:
            return [], None, []
        return (flags, next_phase.manual_gate_why(entry),
                next_phase.manual_gate_decline_answers(entry))
    except Exception:  # noqa: BLE001 - advisory: the plain resume stands
        return [], None, []


def native_run_stopped(
    record: Mapping[str, Any], statuses: Mapping[str, Any],
) -> bool:
    """Whether a native implement the host ran ended short and waits for the
    user: the run the executor routes head "stopped and needs you".

    Fix round 24 (live run 10, Claude Code stop 01/01b): the native head read
    "not finished on the host" for a stop, since that leg leaves no run
    record and "not finished" also covers a host still working. The caller
    has already ruled out a completed phase and an open loop (``util metrics
    start`` without its ``finish``, the "in progress on the host" head).
    *record* is ``state.json``'s dict and *statuses* its implement task
    statuses (``StateManager.implementation_task_statuses``). True when:

    * no task is recorded ``in_progress``;
    * something waits for an answer: a task of the decomposition recorded
      ``failed`` (a refusal before dispatch included, which the emit records
      itself) or a check whose findings hold tasks back — what the stop's
      answers are composed from
      (``write_batch_scheduler.native_stop_answers``);
    * and either no task is left that the host could still run without that
      answer (every task not completed, skipped or failed is a manual one,
      held by a check, or after a failed task), or the host closed the loop
      the last emit opened: its ``util metrics finish`` removed the emit's
      left-out record (``metrics_left_out``), or the emit left nothing out.

    Fix round 25 (review of round 24, stops #3; the coordinator's decision,
    permissive): a host that ended its turn right after a failed task,
    leaving an independent task pending, read "not finished on the host"
    while ``util next-command`` gave the resume and the answers. Its loop is
    closed and something waits, so it is stopped; the block names the tasks
    it could still run (:func:`native_still_runnable`), which the resume
    runs. Right after an emit that recorded a refusal (its left-out record
    still there), the tasks it handed out can still run, so the moments
    between the emit and the host's records never read as a stop. Advisory:
    an unreadable record is not a stop.
    """
    from .write_batch_scheduler import _native_stop_facts

    try:
        scope = [str(t) for t in record.get("implement_task_ids") or []]
        if any(statuses.get(task_id) == "in_progress" for task_id in scope):
            return False
        if _native_stop_facts(record) is None:
            return False
        if not native_still_runnable(record, statuses):
            return True
        left = record.get("metrics_left_out")
        return not (isinstance(left, Mapping) and left.get(_IMPLEMENT_PHASE))
    except Exception:  # noqa: BLE001 - advisory: the run view is not
        return False


def _host_run_started_at(record: Mapping[str, Any], phase: str) -> Optional[str]:
    """When the host's own loop over *phase*'s batches started, or ``None``.

    The native leg's instructions open the loop with ``util metrics start``
    and close it with ``util metrics finish`` (finished or stopped), so a
    ``metrics_progress`` entry for the phase is a host run still in progress
    (or one that died without its finish). Seconds precision.
    """
    progress = record.get("metrics_progress")
    entry = progress.get(phase) if isinstance(progress, dict) else None
    started = entry.get("started_at") if isinstance(entry, dict) else None
    if not isinstance(started, str) or not started.strip():
        return None
    return started.strip()[:19]


def _state_changed_at(state_file: Path) -> Optional[str]:
    """When *state_file* was last written, local time to the second, or
    ``None``. Every record a host's loop makes (``util batch-done``, ``util
    metrics record``) rewrites it."""
    try:
        stamp = os.stat(state_file).st_mtime
    except OSError:
        return None
    from datetime import datetime

    return datetime.fromtimestamp(stamp).isoformat(timespec="seconds")


#: A native implement that stopped and waits for the user's answer
#: (:func:`native_run_stopped`, fix round 24): the executor routes' words
#: (:data:`STOPPED_FOR_THE_USER_VERDICT`), with no exit code to name, since
#: the native leg's phase exits 0 and the host closed it.
NATIVE_STOPPED_VERDICT = "stopped and needs you (not marked completed)"


def _native_head(
    dir_name: str, *, completed: bool, since: Optional[str], unit: str,
    changed: Optional[str] = None, stopped: bool = False,
) -> str:
    """A native write phase's head line: what state.json says it is doing.

    Fix round 18 (Claude Code racing 06): a running native implement read
    "no run record — the host ran these tasks itself" exactly as a stopped
    one did, so the view could not say whether anything was going on. Fix
    round 24: one that stopped needing the user (*stopped*) reads
    :data:`NATIVE_STOPPED_VERDICT`.
    """
    if completed:
        verdict = "done on the host (marked completed)"
        tense = "ran"
    elif since:
        last = f"; state.json last changed {changed}" if changed else ""
        verdict = f"in progress on the host (started {since}{last})"
        tense = "runs"
    elif stopped:
        verdict = NATIVE_STOPPED_VERDICT
        tense = "ran"
    else:
        verdict = "not finished on the host (not marked completed)"
        tense = "ran"
    return (
        f"  {dir_name}  {verdict} — no run record, since the host {tense} "
        f"these {unit} itself; read from state.json"
    )


def _native_resume_line(resume: Optional[str]) -> List[str]:
    """What an in-progress head may also mean, and the way on (fix round 19).

    ``util metrics start`` with no ``finish`` is all that says a host's loop
    is running, so a loop that crashed or whose session ended reads the same
    forever; nothing on disk tells the two apart.
    """
    if not resume:
        return []
    return [
        "      if no host session is running it now, its loop ended without "
        f"`util metrics finish`; continue it with: {resume}"
    ]


def native_resume_command(
    mode: str, plan_path: Path, spell: Optional["Speller"] = None,
    flags: Sequence[str] = (),
) -> str:
    """``--<mode> <plan> --resume`` in the host's spelling (:func:`user_speller`),
    else the dispatcher's: the way on for a native phase whose loop ended
    without its finish, or that stopped. *flags* replace the bare verb with a
    whole answer (``--resume --human-task T005=skip``, fix round 20).

    On a commit review (a brief whose ``state.json`` holds ``commit_range``)
    the command reads as the commit mode with the pinned range, in either
    spelling (plans/review-commits.md §2.8): ``status``'s ``resume with:``
    line for a native apply that stopped."""
    tokens = [str(flag) for flag in flags] or [_RESUME_VERB_BY_MODE.get(mode, "--resume")]
    if spell is not None:
        spelled = spell(mode, [], tokens)
        if spelled:
            return spelled
    return _retry_command(mode, plan_path, *tokens)


def native_stop_answer_commands(
    view: Mapping[str, Any], plan_path: Path, spell: Optional["Speller"] = None,
) -> List[Tuple[str, str]]:
    """``(command, why)`` for each answer *view*'s stop waits for
    (``stop_answers``), spelled as :func:`native_resume_command` spells the
    resume beside them."""
    out: List[Tuple[str, str]] = []
    for entry in view.get("stop_answers") or []:
        flags = entry.get("flags") if isinstance(entry, Mapping) else None
        why = entry.get("why") if isinstance(entry, Mapping) else None
        if not isinstance(flags, list) or not flags or not why:
            continue
        out.append((native_resume_command(
            _IMPLEMENT_PHASE, plan_path, spell, flags=flags), str(why)))
    return out


def _native_stop_lines(
    resume: Optional[str], answers: Sequence[Tuple[str, str]] = (),
    why: Optional[str] = None,
) -> List[str]:
    """The way on from a native phase that stopped (fix round 20).

    Live run 8 (Claude Code stop path): a native implement the host closed
    without ``--mark-completed`` read "not finished on the host" with no
    command at all, where the tool routes' view says ``resume with:``; round
    19 had added a way on only to the "in progress on the host" head. The
    ``resume with:`` line, then each answer the stop waits for, in the words
    and order ``util next-command`` gives them on that leg and the tool
    routes' ``resume_answers`` on theirs.
    """
    if not resume:
        return []
    lines = [f"      resume with: {resume}"]
    if why:
        # Fix round 22: what the plain resume does, like each answer below.
        lines.append(why_line(why))
    for command, answer_why in answers:
        lines.append(f"      or answer the stop with: {command}")
        lines.append(why_line(answer_why))
    return lines


def why_line(why: str) -> str:
    """A command's why on the line under it, as plain text two columns in,
    as the ready section prints it above its command. Fix round 28 (live
    run 12 #7, Claude Code status): it was bracketed, and a why that ends
    in a bracket of its own ("… depend on it (T006)", a quoted finding)
    read "(T006))"."""
    return f"        {why}"


#: How many task ids the still-runnable line names before "and N more".
STILL_RUNNABLE_IDS_SHOWN = 8


def _still_runnable_clause(ids: Sequence[str]) -> str:
    """``T003 can still run: the resume runs it`` (fix round 25)."""
    shown = list(ids[:STILL_RUNNABLE_IDS_SHOWN])
    rest = len(ids) - len(shown)
    if rest:
        named = ", ".join(shown) + f" and {rest} more"
    elif len(shown) == 1:
        named = shown[0]
    else:
        named = ", ".join(shown[:-1]) + f" and {shown[-1]}"
    return f"{named} can still run: the resume runs {'it' if len(ids) == 1 else 'them'}"


def render_state_implement_lines(
    view: Dict[str, Any], *, resume: Optional[str] = None,
    answers: Sequence[Tuple[str, str]] = (),
) -> List[str]:
    """:func:`state_implement_view` as the run view's text: one block.

    Fix round 18 (Claude Code racing 06 and stop path): its tally line reads
    ``all tasks:``, in the executor routes' words (:func:`implement_tally_text`),
    and its head says whether the host's run is in progress. Fix round 19:
    an in-progress head says when state.json last changed and, with
    *resume* (:func:`native_resume_command`), what it may also mean. Fix
    round 20: a "not finished" one that a ``--resume`` continues
    (``resumable``) ends with *resume* and each of *answers*
    (:func:`native_stop_answer_commands`), :func:`_native_stop_lines`.
    """
    since = view.get("in_progress_since")
    lines = [_native_head(
        _IMPLEMENT_PHASE, completed=bool(view.get("completed")), since=since,
        unit="tasks", changed=view.get("state_changed_at"),
        stopped=bool(view.get("stopped")),
    )]
    lines += _earlier_run_lines(view.get("earlier_run"))
    lines.append(
        f"      all tasks:      {implement_tally_text(view['tally'], live=bool(since))}"
    )
    runnable = [str(t) for t in (view.get("still_runnable") or [])]
    if runnable:
        # Fix round 25 (stops #3): stopped with tasks the host could run.
        lines.append(f"      {_still_runnable_clause(runnable)}")
    if since:
        lines += _native_resume_line(resume)
    for task_id, reason in view["reasons"].items():
        lines.append(f"      {task_id}: {reason}")
    for entry in view["findings"]:
        findings = entry.get("findings") or []
        lines.append(
            f"      check findings {entry['id']}: {clip('; '.join(findings), 300)}"
        )
    for entry in view.get("batch_checks") or []:
        findings = entry.get("findings") or []
        lines.append(
            f"      own check fails {entry['id']}: {clip('; '.join(findings), 300)}"
        )
    lines += [
        f"      {clause}" for clause in accepted_rerun_clauses(
            _accepted_reruns_by_task(view.get("batch_check_accepted")))
    ]
    lines += [
        f"      {clause}" for clause in repeated_check_clauses(
            _accepted_reruns_by_task(view.get("batch_check_repeats")))
    ]
    if view["answers"]:
        lines.append(
            "      answers on record: "
            + ", ".join(f"--human-task {task_id}={action}"
                        for task_id, action in sorted(view["answers"].items()))
        )
    if not since and view.get("resumable"):
        lines += _native_stop_lines(resume, answers, view.get("stop_resume_why"))
    return lines


def native_leg_stamp(directory: Path) -> Optional[Dict[str, str]]:
    """``{leg, host}`` when *directory*'s ``write_tasks.json`` was written by
    the native emit, else ``None`` (fix round 26).

    Every run of a write phase rewrites that file, on either leg, and only
    the native emit stamps it (``write_phase_bridge.NATIVE_LEG``), so the
    stamp says the phase's newest run is the host's own. Advisory: an
    unreadable file is no stamp."""
    try:
        document = json.loads((Path(directory) / _WRITE_TASKS).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - advisory
        return None
    if not isinstance(document, dict) or document.get("leg") != "native":
        return None
    return {"leg": "native", "host": str(document.get("host") or "")}


def _write_phase_of(plan_path: Path, view: Mapping[str, Any]) -> Optional[str]:
    """The write phase (implement or an apply phase) whose folder *view* is
    the run record of, else ``None``."""
    where = os.path.realpath(str(view.get("phase_dir") or ""))
    for phase in NATIVE_PHASE_ORDER:
        if os.path.realpath(str(phase_dir_path(plan_path, phase))) == where:
            return phase
    return None


def superseded_by_native(
    plan_path: Path, view: Mapping[str, Any],
) -> Optional[Dict[str, str]]:
    """The native stamp that makes *view* an earlier run, else ``None``.

    The commit review of 2026-10-08 ("stale executor status after switching
    to native execution", reproduced, its guards older than 5025463): an
    executor run of a write phase (a tool route or ``--exec-subagents``)
    leaves ``{phase}/.status.json`` and ``write_batch_report.json`` behind,
    and when the user went on with the same phase on the Claude Code native
    leg, ``status`` kept heading the phase with that run ("stopped in
    foreground (needs you; …)" over a native run that had finished) because
    ``state_implement_view`` and ``state_apply_views`` stood back for any
    executor record. A record whose phase folder the native emit wrote last
    (:func:`native_leg_stamp`) is that earlier run, unless it is a detached
    run still going, which is never set aside, or a run recorded as started
    after that emit (:func:`_run_started_after_native_emit`): a detached
    executor attempt that failed or was aborted before it rewrote
    ``write_tasks.json`` leaves the stamp behind, and the stamp alone does not
    say which run is newer."""
    if _write_phase_of(plan_path, view) is None or _run_is_live(view):
        return None
    directory = Path(str(view.get("phase_dir") or ""))
    stamp = native_leg_stamp(directory)
    if stamp is None or _run_started_after_native_emit(view, directory):
        return None
    return stamp


def _native_emit_time(directory: Path) -> Optional[float]:
    """When the native emit wrote *directory*'s ``write_tasks.json``, as
    epoch seconds, or ``None``: the ``native_run.emitted_at`` the apply emit
    records (``write_phase_bridge.native_run_record``), else the file's
    modification time (implement's emit records no time; only
    ``write_phase_bridge.write_task_file_for_phase`` writes the file)."""
    path = Path(directory) / _WRITE_TASKS
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - advisory
        document = None
    record = document.get("native_run") if isinstance(document, dict) else None
    emitted = detach._parse_stamp(
        record.get("emitted_at") if isinstance(record, dict) else None)
    if emitted is not None:
        try:
            return emitted.timestamp()
        except (OverflowError, OSError, ValueError):
            pass
    try:
        return os.stat(path).st_mtime
    except OSError:
        return None


def _run_started_after_native_emit(view: Mapping[str, Any], directory: Path) -> bool:
    """Whether *view*'s run record began after the native emit last wrote
    *directory*'s ``write_tasks.json`` (:func:`_native_emit_time`).

    Every executor run rewrites that file and drops the native stamp, but a
    detached attempt that failed or was aborted before its rewrite leaves the
    stamp of the native run before it; its terminal record is then the newer
    run, and setting it aside hid that failure behind the native block's
    "this run … is newer". The run's own ``started_at`` (written once, by the
    worker's claim) against the emit's time decides. A record with no
    readable start (a foreground run records none) keeps the stamp's
    reading, as does an emit with no readable time."""
    run = view.get("run") if isinstance(view.get("run"), Mapping) else {}
    started = detach._parse_stamp(run.get("started_at"))
    if started is None:
        return False
    emitted = _native_emit_time(directory)
    if emitted is None:
        return False
    try:
        return started.timestamp() > emitted
    except (OverflowError, OSError, ValueError):
        return False


def set_aside_superseded_runs(
    plan_path: Path, views: Sequence[Dict[str, Any]], *,
    host_id: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """``(views, {phase: earlier_run})``: *views* without the executor runs a
    newer native run of their phase went on from (:func:`superseded_by_native`),
    and each one's :func:`earlier_run_record` for that native block to name.

    Set aside only when the native view of that phase is there to show in its
    place; otherwise the record stays as it is (fix round 26)."""
    kept: List[Dict[str, Any]] = []
    candidates: Dict[str, Tuple[Dict[str, Any], Dict[str, str]]] = {}
    for view in views:
        stamp = superseded_by_native(plan_path, view)
        phase = _write_phase_of(plan_path, view) if stamp else None
        if stamp is None or phase is None or phase in candidates:
            kept.append(view)
            continue
        candidates[phase] = (view, stamp)
    if not candidates:
        return list(views), {}
    shown: set = set()
    if _IMPLEMENT_PHASE in candidates and state_implement_view(plan_path, kept) is not None:
        shown.add(_IMPLEMENT_PHASE)
    if any(phase != _IMPLEMENT_PHASE for phase in candidates):
        shown.update(
            entry.get("phase") for entry in state_apply_views(
                plan_path, kept, None, host_id=host_id)
        )
    superseded: Dict[str, Dict[str, Any]] = {}
    for phase, (view, stamp) in candidates.items():
        if phase in shown:
            superseded[phase] = earlier_run_record(view, stamp)
        else:
            kept.append(view)
    # The caller's order, which sorts the blocks.
    order = {id(view): index for index, view in enumerate(views)}
    kept.sort(key=lambda view: order.get(id(view), len(order)))
    return kept, superseded


def earlier_run_record(view: Mapping[str, Any], stamp: Mapping[str, str]) -> Dict[str, Any]:
    """What a native block says of the executor run it superseded:
    ``{leg, phase_dir, run_id, verdict, host, ended, native_host}``."""
    run = view.get("run") if isinstance(view.get("run"), dict) else {}
    progress = view.get("progress") if isinstance(view.get("progress"), dict) else {}
    verdict = view.get("verdict")
    if run.get("run_id"):
        if verdict == detach.VERDICT_DONE:
            ended = "finished"
        elif _stopped_for_the_user(dict(view)):
            ended = "stopped and needed you (exit 3)"
        elif verdict == detach.VERDICT_ABORTED:
            ended = "was aborted"
        elif verdict == detach.VERDICT_FAILED:
            ended = f"failed (exit {run.get('exit_code')})"
        else:
            ended = "ended without a recorded outcome"
    else:
        step = progress.get("step")
        ended = {
            STOPPED_STEP: "stopped and needed you",
            "complete": "finished",
        }.get(step, "did not finish")
    return {
        "leg": "executor",
        "phase_dir": os.path.basename(str(view.get("phase_dir") or "")),
        "run_id": run.get("run_id"),
        "verdict": verdict,
        "host": run.get("host"),
        "ended": ended,
        "native_host": stamp.get("host") or None,
    }


def _earlier_run_lines(record: Any) -> List[str]:
    """The native block's line naming the executor run it superseded."""
    if not isinstance(record, Mapping):
        return []
    ref = (
        f"run {str(record['run_id'])[:8]}" if record.get("run_id")
        else "a foreground run"
    )
    launched = f", launched on {record['host']}" if record.get("host") else ""
    host = f" ({record['native_host']})" if record.get("native_host") else ""
    return [
        f"      earlier run:    {ref} (its subagents dispatched by the "
        f"plugin{launched}) {record.get('ended')}; this run, on the "
        f"host{host}, is newer"
    ]


#: The apply phases a native host drives itself, in workflow order: no run
#: record, no report, only ``state.json`` and the batch list the emit wrote.
NATIVE_APPLY_PHASES: Tuple[str, ...] = (
    "apply-suggestions", "apply-task-suggestions", "apply-code-fixes",
)
#: Implement's place among them, for the order the blocks print in.
NATIVE_PHASE_ORDER: Tuple[str, ...] = (
    "apply-suggestions", "apply-task-suggestions", _IMPLEMENT_PHASE,
    "apply-code-fixes",
)
_WRITE_TASKS = "write_tasks.json"


def state_apply_views(
    plan_path: Path, views: Sequence[Dict[str, Any]],
    workflow: Optional[Dict[str, Any]], *, only: Optional[str] = None,
    host_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """The apply phases a native host ran, read back from ``state.json``.

    Fix round 18 (Claude Code racing run 7): the run view listed the native
    implement (fix round 14) but none of the apply phases the same host had
    run, while on the tool routes, whose apply runs leave a run record, it
    listed every one. A phase is listed when its folder holds the batch list
    the native emit wrote (``write_tasks.json``) and neither a run view nor a
    ``write_batch_report.json`` (the executor's), and the workflow payload
    (*workflow*: ``get_workflow_status``, which already sets an earlier
    cycle's batches aside) shows it ``completed`` or ``in_progress``, or the
    host's loop is going. ``{phase, phase_dir, completed,
    in_progress_since, batches_recorded, batches_total}`` (plus
    ``declined_items`` / ``skipped_items`` when a batch's record names one,
    fix round 22, ``items_applied`` / ``items_total`` / ``applied_to``
    once a record names one of its items, fix round 28, counted over the
    run, and ``failed_batches``, fix round 29) in workflow order;
    *only* limits it to one phase (``--phase``). Read-only.
    """
    from .metrics import _current_run_id
    from .state_manager import StateManager

    listed = {
        os.path.basename(str(view.get("phase_dir") or "")) for view in views
    }
    candidates = []
    for phase in NATIVE_APPLY_PHASES:
        if only is not None and only not in (phase, os.path.basename(
                str(phase_dir_path(plan_path, phase)))):
            continue
        directory = phase_dir_path(plan_path, phase)
        if (directory.name in listed
                or ((directory / _WRITE_REPORT).exists()
                    and native_leg_stamp(directory) is None)
                or not (directory / _WRITE_TASKS).is_file()):
            continue
        candidates.append((phase, directory))
    if not candidates:
        return []
    try:
        manager = StateManager(plan_path, read_only=True)
        record = manager.state
        if workflow is None:
            workflow = _workflow_payload(plan_path, host_id=host_id)
    except Exception:  # noqa: BLE001 - advisory: the run view is not
        return []
    changed = _state_changed_at(manager.state_file)
    phases = (workflow or {}).get("phases") or {}
    out: List[Dict[str, Any]] = []
    for phase, directory in candidates:
        status = (phases.get(phase) or {}).get("status")
        since = _host_run_started_at(record, phase)
        completed = status == "completed"
        if not (completed or status == "in_progress" or since):
            continue
        entry: Dict[str, Any] = {
            "phase": phase,
            "phase_dir": directory.name,
            "completed": completed,
            "in_progress_since": None if completed else since,
            "batches_recorded": None,
            "batches_total": None,
            # Fix round 19, as on the native implement view.
            "state_changed_at": changed,
        }
        if entry["in_progress_since"]:
            # This host run's own count: the entries `util metrics record`
            # stamped with the run id `util metrics start` gave it. A batch
            # id is reused across a native resume, so the ids say less.
            run_id = _current_run_id(record, phase)
            progress = (record.get("metrics_progress") or {}).get(phase) or {}
            metrics = (record.get("metrics") or {}).get(phase)
            if run_id and isinstance(metrics, list):
                entry["batches_recorded"] = sum(
                    1 for item in metrics
                    if isinstance(item, dict) and item.get("run_id") == run_id
                )
            total = progress.get("total_batches")
            if isinstance(total, int) and not isinstance(total, bool) and total > 0:
                entry["batches_total"] = total
        if phase == "apply-code-fixes":
            # Fix round 20: the batches whose own check failed after their
            # edits, as `util batch-done` recorded them, named as the native
            # implement view names its tasks'.
            checks = _native_apply_batch_checks(record, directory)
            if checks:
                entry["batch_checks"] = checks
        # Fix round 22: the items a batch declined or the user skipped;
        # fix round 28: and the items count they are left out of.
        entry.update(_native_apply_not_applied(record, directory, phase))
        out.append(entry)
    return out


#: The not-applied items a write mirror (and a native apply view) names, in
#: the order and words the progress line prints them (fix round 18): the
#: key, the words for one item and for several, and the words a recorded
#: reason may open with that the clause has already said (fix round 26).
_NOT_APPLIED_ITEM_WORDS: Tuple[Tuple[str, str, str, str], ...] = (
    ("declined_items", "declined by its batch (not applied)",
     "declined by their batch (not applied)", ""),
    ("skipped_items", "skipped at your request (not applied)",
     "skipped at your request (not applied)", "skipped at your request: "),
)


def not_applied_item_clauses(source: Mapping[str, Any]) -> List[str]:
    """``1 declined by its batch (not applied): <id8> in <batch> (<reason>)``
    and its skipped twin, one clause per kind *source* carries
    (``declined_items`` / ``skipped_items``: ``[{task_id, id, reason}]``, a
    write mirror's keys). The executor's progress line puts them after its
    ``items applied`` count; the native apply view prints each on its own
    (fix round 22), so the two legs name a declined item in the same words.

    Fix round 26 (live run 11 #7): the clause read "not applied, declined by
    its batch: …" after "2/3 items applied, ", two clauses run together by
    commas; it now counts the items and says "not applied" once, in
    parentheses."""
    clauses: List[str] = []
    for key, one, several, said in _NOT_APPLIED_ITEM_WORDS:
        raw = source.get(key)
        entries = [
            entry for entry in raw
            if isinstance(entry, dict) and entry.get("id")
        ] if isinstance(raw, list) else []
        if entries:
            words = one if len(entries) == 1 else several
            clauses.append(f"{len(entries)} {words}: " + "; ".join(
                f"{str(entry['id'])[:8]} in {entry.get('task_id')} "
                f"({clip(without_closing_mark(_reason_after(entry.get('reason') or '', said)), 120)})"
                for entry in entries[:5]
            ) + (f" (+{len(entries) - 5} more)" if len(entries) > 5 else ""))
    return clauses


def _reason_after(reason: str, said: str) -> str:
    """*reason* without the opening words *said* the clause already printed
    (``skipped at your request: …``), when more remains."""
    text = str(reason)
    if said and text.lower().startswith(said.lower()) and text[len(said):].strip():
        return text[len(said):].strip()
    return text


def accepted_rerun_clauses(by_task: Mapping[str, Sequence[str]]) -> List[str]:
    """``completed, its check repeated T002's accepted findings: T007`` per
    set of checks, from ``{task_id: [check ids]}`` (fix round 23): the code
    tasks whose own check reported again only what the user accepted for a
    check (``--human-task <check>=done``), named on every ``status`` surface
    of both legs where a failing own check is named, never as a failure."""
    groups: Dict[str, List[str]] = {}
    for task_id, checks in sorted(by_task.items()):
        names = sorted({str(check) for check in (checks or []) if str(check)})
        if not names:
            continue
        named = " and ".join(f"{check}'s" for check in names)
        groups.setdefault(named, []).append(str(task_id))
    return [
        f"completed, its check repeated {named} accepted findings: {', '.join(ids)}"
        for named, ids in groups.items()
    ]


def repeated_check_clauses(by_task: Mapping[str, Sequence[str]]) -> List[str]:
    """``completed, its check repeated T002's findings: T001`` per set of
    checks, from ``{task_id: [check ids]}`` (fix round 28): the code tasks
    whose own check reported only what a check task of the run reported
    (``task_batch_check_repeats``), named on the ``status`` surfaces
    :func:`accepted_rerun_clauses` names its tasks on, never as a failure
    of their own."""
    groups: Dict[str, List[str]] = {}
    for task_id, checks in sorted(by_task.items()):
        names = sorted({str(check) for check in (checks or []) if str(check)})
        if not names:
            continue
        named = " and ".join(f"{check}'s" for check in names)
        groups.setdefault(named, []).append(str(task_id))
    return [
        f"completed, its check repeated {named} findings: {', '.join(ids)}"
        for named, ids in groups.items()
    ]


def _accepted_reruns_by_task(entries: Any) -> Dict[str, List[str]]:
    """``{task_id: [check ids]}`` from
    ``StateManager.implementation_batch_check_accepted``'s entries."""
    return {
        str(entry["id"]): list(entry.get("checks") or {})
        for entry in (entries if isinstance(entries, list) else [])
        if isinstance(entry, dict) and entry.get("id")
        and isinstance(entry.get("checks"), dict)
    }


#: The native apply phases with one write target, which the items count
#: names as the executor's progress line does (``applied_to``).
_SINGLE_TARGET_APPLY_PHASES = ("apply-suggestions", "apply-task-suggestions")


def _native_apply_not_applied(
    record: Dict[str, Any], directory: Path, phase: str = "",
) -> Dict[str, Any]:
    """``{declined_items, skipped_items, failed_batches, items_applied,
    items_total, applied_to}`` for a native apply phase, in the write
    mirror's shape (fix round 22, live run 9: the decline the host recorded
    with ``util batch-done --declined`` was on no ``status`` surface). Read
    from ``processed_<phase dir>``: a record of the review the phase's
    ``write_tasks.json`` applies (its ``grouped_sha256``), or, for a record
    or a task without that stamp, one whose item the run handed out. ``{}``
    when nothing applies or either cannot be read.

    Fix round 28 (live run 12 #4, Claude Code decline): the block printed
    "1 declined by its batch (not applied): …" with no "2/3 items applied;"
    before it, which the executor's line has. ``items_applied`` counts the
    items a record of this run says ``applied`` (as the executor counts an
    applied batch's items less the ones it declined or skipped); both are
    left out until a record of this run names one of its items.
    ``applied_to`` is the one file a single-target phase's batches all
    declare, from the repository root, as the executor names it.

    Fix round 29 (review of round 28): the run is the file's ``native_run``
    (``write_phase_bridge.native_run_record``), not the file's batches,
    which a native ``--resume`` cuts down to the ones still to run: right
    after a resume's emit the count was gone, and once its batch was
    recorded it read "1/1 items applied" for a phase that applied 3 of 4.
    ``items_total`` is every item the run handed out (with any item a
    record of this run names), and a record written before the run started
    (``started_at``) is an earlier run's: a bare re-run of a completed
    phase read the earlier run's "4/4 items applied" before it recorded
    anything. A file without ``native_run`` reads as before: its batches'
    items, every record of the review. ``failed_batches`` (``[{task_id,
    reason}]``) are the batches recorded ``failed`` since this file was
    written (``emitted_at``; an earlier part's failure is handed out again
    by the resume that wrote it), each with the reason its record gave: a
    failed batch alone read "0/4 items applied" and named nothing."""
    from .state_manager import _parse_completion_time

    try:
        document = json.loads((directory / _WRITE_TASKS).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - advisory
        return {}
    processed = record.get(f"processed_{directory.name}")
    tasks = document.get("batches") or document.get("tasks") if isinstance(
        document, dict) else None
    if not isinstance(processed, dict) or not isinstance(tasks, list):
        return {}
    holder: Dict[str, str] = {}
    stamp = ""
    for task in tasks:
        if not isinstance(task, dict):
            continue
        inputs = task.get("inputs") if isinstance(task.get("inputs"), dict) else {}
        stamp = stamp or str(inputs.get("grouped_sha256") or "")
        for item in task.get("expected_ids") or []:
            holder.setdefault(str(item), str(task.get("task_id") or ""))
    run = document.get("native_run")
    run = run if isinstance(run, dict) else {}
    run_items = [str(i) for i in run.get("items") or [] if str(i)] if isinstance(
        run.get("items"), list) else []
    items: Dict[str, None] = dict.fromkeys([*run_items, *holder])
    started = _parse_completion_time(run.get("started_at"))
    emitted = _parse_completion_time(run.get("emitted_at"))

    def _before(entry: Dict[str, Any], when: Any) -> bool:
        written = _parse_completion_time(entry.get("timestamp"))
        return when is not None and written is not None and written < when

    out: Dict[str, Any] = {}
    applied = 0
    on_record = False
    failed: Dict[str, str] = {}
    for item, entry in processed.items():
        if not isinstance(entry, dict) or _before(entry, started):
            continue
        details = entry.get("details") if isinstance(entry.get("details"), dict) else {}
        recorded = str(details.get("grouped_sha256") or "")
        if stamp and recorded:
            if recorded != stamp:
                continue
        elif str(item) not in items:
            continue
        status = entry.get("status")
        task_id = str(details.get("task_id") or holder.get(str(item)) or "")
        if status == "failed":
            if _before(entry, emitted):
                continue
            failed.setdefault(task_id, _failed_batch_reason(record, task_id, details))
        items.setdefault(str(item), None)
        on_record = True
        applied += status == "applied"
        key = {"declined": "declined_items", "skipped": "skipped_items"}.get(status)
        if key is None:
            continue
        out.setdefault(key, []).append({
            "task_id": task_id,
            "id": str(item),
            "reason": str(details.get("reason") or ""),
        })
    if failed:
        out["failed_batches"] = [
            {"task_id": task_id, "reason": reason} for task_id, reason in failed.items()
        ]
    if on_record:
        out["items_applied"] = applied
        out["items_total"] = len(items)
        target = _native_single_target(tasks, directory) if (
            phase in _SINGLE_TARGET_APPLY_PHASES) else None
        if target:
            out["applied_to"] = target
    return out


def _failed_batch_reason(
    record: Mapping[str, Any], task_id: str, details: Mapping[str, Any],
) -> str:
    """The reason a native apply batch's ``failed`` record gave: its own
    ``details.reason`` when it carries one, else ``task_status_reasons``
    while ``task_status`` still says that batch failed; ``""`` otherwise."""
    if details.get("reason"):
        return str(details["reason"])
    statuses = record.get("task_status") if isinstance(record.get("task_status"), dict) else {}
    reasons = record.get("task_status_reasons") if isinstance(
        record.get("task_status_reasons"), dict) else {}
    if statuses.get(task_id) == "failed" and reasons.get(task_id):
        return str(reasons[task_id])
    return ""


#: The words of the clause naming a native apply phase's failed batches
#: (fix round 29), for one and for several.
_FAILED_BATCH_WORDS = ("1 batch failed", "{n} batches failed")


def failed_batch_clause(view: Mapping[str, Any]) -> List[str]:
    """``1 batch failed: apply-batch-0 (<reason>)`` (``2 batches failed: …;
    …``) for a native apply view's ``failed_batches``, else ``[]``: the
    executor's line names its failed batches (``failed apply-batch-0``), and
    the native view's count read "0/4 items applied" beside one and named
    nothing (fix round 29)."""
    raw = view.get("failed_batches")
    entries = [
        entry for entry in raw
        if isinstance(entry, dict) and entry.get("task_id")
    ] if isinstance(raw, list) else []
    if not entries:
        return []
    one, several = _FAILED_BATCH_WORDS
    head = one if len(entries) == 1 else several.format(n=len(entries))
    named = []
    for entry in entries[:5]:
        reason = plain_line(str(entry.get("reason") or ""))
        why = f" ({clip(without_closing_mark(reason), 120)})" if reason else ""
        named.append(f"{plain_line(str(entry['task_id']))}{why}")
    more = f" (+{len(entries) - 5} more)" if len(entries) > 5 else ""
    return [f"{head}: " + "; ".join(named) + more]


def _native_single_target(tasks: Sequence[Any], directory: Path) -> Optional[str]:
    """The one file every batch of *tasks* declares, from the root of the
    repository holding *directory* (the ``.git`` holder above it, walked;
    as given when it lies outside), else ``None``."""
    from .git_utils import find_git_entry_root
    from .subagent_tasks import declared_file_set

    declared = {
        tuple(declared_file_set(task)) for task in tasks if isinstance(task, dict)
    }
    if len(declared) != 1:
        return None
    (files,) = declared
    if len(files) != 1:
        return None
    target = files[0]
    try:
        start = os.path.realpath(str(directory))
        root = os.path.realpath(find_git_entry_root(start) or start)
        resolved = target if os.path.isabs(target) else os.path.join(root, target)
        relative = os.path.relpath(os.path.realpath(resolved), root)
    except (OSError, ValueError):
        return target
    # Printed beside the count and carried in the JSON view: `/` on every platform.
    return target if relative.startswith(os.pardir) else relative.replace(os.sep, "/")


def _native_apply_batch_checks(record: Dict[str, Any], directory: Path) -> List[Dict[str, Any]]:
    """``[{id, findings}]`` for the native apply-code-fixes batches whose own
    check failed (``known_checks.earlier_batch_check_failures`` over the
    phase's ``write_tasks.json``); ``[]`` when either cannot be read."""
    try:
        from .known_checks import earlier_batch_check_failures

        document = json.loads((directory / _WRITE_TASKS).read_text(encoding="utf-8"))
        tasks = document.get("batches") or document.get("tasks") or []
        return [
            {"id": task_id, "findings": findings}
            for task_id, findings in earlier_batch_check_failures(record, tasks, "")
        ]
    except Exception:  # noqa: BLE001 - advisory
        return []


def native_items_count(view: Mapping[str, Any]) -> str:
    """``2/3 items applied`` (``… applied to plans/p.md`` for a single-target
    phase) for a native apply view that counted its items, else ``""``:
    the executor's progress-line words (fix round 28)."""
    applied, total = view.get("items_applied"), view.get("items_total")
    if not (isinstance(applied, int) and isinstance(total, int)
            and not isinstance(applied, bool) and total > 0):
        return ""
    target = view.get("applied_to")
    to = (
        f" to {clip(plain_line(target), 200)}"
        if isinstance(target, str) and plain_line(target) else ""
    )
    return f"{applied}/{total} items applied{to}"


def render_state_apply_lines(
    view: Dict[str, Any], *, resume: Optional[str] = None,
) -> List[str]:
    """:func:`state_apply_views`' entry as the run view's text: one block
    (*resume* as on :func:`render_state_implement_lines`)."""
    since = view.get("in_progress_since")
    lines = [_native_head(
        view["phase_dir"], completed=bool(view.get("completed")),
        since=since, unit="batches", changed=view.get("state_changed_at"),
    )]
    lines += _earlier_run_lines(view.get("earlier_run"))
    recorded, total = view.get("batches_recorded"), view.get("batches_total")
    if isinstance(recorded, int) and isinstance(total, int):
        lines.append(f"      batches:        {recorded}/{total} recorded by this run")
    for entry in view.get("batch_checks") or []:
        findings = entry.get("findings") or []
        lines.append(
            f"      own check fails {entry['id']}: {clip('; '.join(findings), 300)}"
        )
    # Fix round 22: in the executor's progress-line words. Fix round 28
    # (live run 12 #4): after the items count they are left out of, as the
    # executor's line puts them, "2/3 items applied; 1 declined by …".
    # Fix round 29: and the batches recorded failed, by name.
    not_applied = not_applied_item_clauses(view) + failed_batch_clause(view)
    count = native_items_count(view)
    if count:
        lines.append("      " + "; ".join([count, *not_applied]))
    else:
        lines += [f"      {clause}" for clause in not_applied]
    if since:
        lines += _native_resume_line(resume)
    elif not view.get("completed"):
        # Fix round 20: listed unfinished only while the workflow shows it
        # `in_progress` (`state_apply_views`), which a `--resume` continues.
        lines += _native_stop_lines(resume)
    return lines


def _run_notes(view: Dict[str, Any]) -> List[str]:
    """``progress.notes``: a finished apply phase's lines for the host (fix
    round 14) — a consistency warning, the items left unapplied and why."""
    progress = view.get("progress") if isinstance(view.get("progress"), dict) else {}
    notes = progress.get("notes")
    return [str(note).strip() for note in notes if str(note).strip()] if isinstance(
        notes, list) else []


def _id_list(value: Any) -> List[str]:
    """A mirror's id list as strings; anything that is not a list is none."""
    return [str(item) for item in value] if isinstance(value, list) else []


#: The buckets of :func:`implement_task_tally`, in the order the line names
#: them, with their words. The first five are done. A task skipped with a
#: deferred manual task reads "skipped (depends on manual T005)"
#: (:func:`_bucket_clauses`, fix round 17).
_TALLY_LABELS: Tuple[Tuple[str, str], ...] = (
    ("completed", "completed"),
    ("check_findings", "completed, its check reported problems"),
    # Fix round 20 (run 8 #6): in the words of the `resume: kept` line and
    # the progress line's kept note (`answered_done_label`).
    ("accepted_findings", "accepted with its check findings"),
    ("accepted_failed", "accepted after failing"),
    ("completed_manual", "completed by hand"),
    ("failed", "failed"),
    ("declined", "skipped at your request"),
    ("declined_dependents", "skipped (depend on a task you skipped)"),
    ("deferred", "deferred manual"),
    ("deferred_dependents", "skipped (depends on a manual task)"),
    ("not_run", "not run"),
)
#: :func:`state_implement_view`'s coarser buckets, folded from the tally's.
_VIEW_MERGE: Dict[str, str] = {
    "check_findings": "completed",
    "accepted_findings": "accepted",
    "accepted_failed": "accepted",
}
_VIEW_LABELS: Tuple[Tuple[str, str], ...] = (
    ("completed", "completed"),
    ("accepted", "accepted with its check findings or after failing"),
    ("completed_manual", "completed by hand"),
    ("failed", "failed"),
    ("declined", "skipped at your request"),
    ("declined_dependents", "skipped (depend on a task you skipped)"),
    ("deferred", "deferred manual"),
    ("deferred_dependents", "skipped (depends on a manual task)"),
    ("not_run", "not run"),
)
_TALLY_DONE = (
    "completed", "check_findings", "accepted_findings", "accepted_failed",
    "completed_manual",
)


def implement_task_tally(plan_path: Path) -> Optional[Dict[str, Any]]:
    """Every task of implement's decomposition as ``state.json`` records it.

    Fix round 16 (run 6, Codex and OpenCode stop paths): after a resume,
    ``status``'s implement run block counted only that run's batches ("2/2
    batches ok, 1/2 items applied", then "1/1" on the accept path) and never
    added up to the fixture's seven tasks, while summary.md and the stop's
    own account did. The run mirror holds one run; ``state.json`` holds the
    phase. ``{"total", "done", "buckets"}`` over :data:`_TALLY_LABELS`, each
    task in exactly one bucket; ``None`` without a decomposition on record.
    Read-only.
    """
    from .state_manager import StateManager

    try:
        state = StateManager(plan_path, read_only=True)
    except Exception:  # noqa: BLE001 - advisory: the run view is not
        return None
    decomposition = state.state.get("implement_task_ids")
    if not isinstance(decomposition, list) or not decomposition:
        return None
    buckets, waits_on = _implement_buckets(state)
    return {
        "total": len(decomposition),
        "done": sum(len(buckets[key]) for key in _TALLY_DONE),
        "buckets": buckets,
        "waits_on": waits_on,
    }


def implement_tally_text(tally: Dict[str, Any], *, live: bool = False) -> str:
    """:func:`implement_task_tally` as one clause list: ``5/7 done;
    completed: …; accepted with its check findings: …``. A task not run
    yet reads "pending" while the run is *live*, "not run" once it ended."""
    parts = [f"{tally['done']}/{tally['total']} done"] + _bucket_clauses(
        tally["buckets"], tally.get("waits_on") or {}, _TALLY_LABELS, live=live,
    )
    return "; ".join(parts)


def _run_is_live(view: Dict[str, Any]) -> bool:
    """Whether *view*'s run is still going: starting, running, or slow to
    beat but not provably gone (the reading ``render_run_text`` gives
    ``re-running since``). A foreground run (no record) is not."""
    verdict = view.get("verdict")
    return verdict in (detach.VERDICT_STARTING, detach.VERDICT_RUNNING) or (
        verdict == detach.VERDICT_STALE and not _died(view)
    )


def _is_executor_implement_view(view: Dict[str, Any]) -> bool:
    """An implement view whose run record carries the executor's mirror (the
    tool routes and ``--exec-subagents``): the run whose own counts
    :func:`implement_task_tally` completes. The native leg's run is read by
    :func:`state_implement_view` instead."""
    phase = view.get("phase") or os.path.basename(str(view.get("phase_dir") or ""))
    if phase != _IMPLEMENT_PHASE:
        return False
    progress = view.get("progress") if isinstance(view.get("progress"), dict) else {}
    return isinstance(progress.get("write_subagents"), dict)


def _kept_labels(mirror: Mapping[str, Any], kept: Sequence[str]) -> Dict[str, str]:
    """What each task a write mirror kept is, in the ``resume: kept`` line's
    words (fix round 20): a check whose findings stand (its row carries
    them), an accepted task (``accepted_task_ids``, a check apart from a
    failed task) and a manual task completed by hand
    (``completed_by_hand_task_ids``, fix round 23). Plain kept tasks carry
    no label."""
    from .write_batch_scheduler import (
        ACCEPTED_AFTER_FAILING_LABEL,
        ACCEPTED_WITH_FINDINGS_LABEL,
        COMPLETED_BY_HAND_LABEL,
        KEPT_WITH_FINDINGS_LABEL,
    )

    kept_ids = {str(t) for t in kept}
    labels = {
        str(row.get("task_id")): KEPT_WITH_FINDINGS_LABEL
        for row in (mirror.get("tasks") or [])
        if isinstance(row, dict) and str(row.get("task_id")) in kept_ids
        and isinstance(row.get("check_findings"), list) and row["check_findings"]
    }
    with_findings = set(_id_list(mirror.get("accepted_with_findings_task_ids")))
    for task_id in _id_list(mirror.get("accepted_task_ids")):
        labels[task_id] = (
            ACCEPTED_WITH_FINDINGS_LABEL if task_id in with_findings
            else ACCEPTED_AFTER_FAILING_LABEL
        )
    # Fix round 23: a manual task kept on the user's `=done` answer.
    for task_id in _id_list(mirror.get("completed_by_hand_task_ids")):
        labels[task_id] = COMPLETED_BY_HAND_LABEL
    return labels


def _kept_text(kept: Sequence[str], labels: Mapping[str, str]) -> str:
    """The kept note's list: ``write_batch_scheduler.kept_named``, at most
    five plain ids as before."""
    from .write_batch_scheduler import kept_named

    return kept_named(kept, labels, limit=5)


def _mirror_text(key: str, mirror: Any) -> List[str]:
    """One clause per executor mirror: ``<kind> <ok>/<total> ok`` and, when any
    task did not end ``ok``, the non-ok statuses and the failed ids."""
    if not isinstance(mirror, dict) or not isinstance(mirror.get("total"), int):
        return []
    kind = mirror.get("kind") or key
    total = mirror["total"]
    counts = mirror.get("counts") if isinstance(mirror.get("counts"), dict) else {}
    tasks = mirror.get("tasks") if isinstance(mirror.get("tasks"), list) else []
    if not counts and tasks:
        # The write mirror records one row per task and no `counts`/`ok`
        # summary; read only the summary keys and a finished nine-task run
        # printed `implement 0/9 ok` (measured 2026-09-16).
        counts = _write_mirror_as_counts(mirror)["counts"]
    ok = mirror.get("ok")
    if not isinstance(ok, int):
        ok = counts.get("ok", 0) if isinstance(counts.get("ok"), int) else 0
    accepted = mirror.get("accepted_task_ids") if isinstance(mirror.get("accepted_task_ids"), list) else []
    # Fix round 20 (run 8 #6): an implement run's accepted tasks were kept
    # from an earlier run, not dispatched, so they are named in the kept note
    # ("T002 (accepted with its check findings)"), not in a clause of their
    # own; OpenCode accept 02 read "accepted with their check findings T002".
    folded = [str(t) for t in accepted if t] if kind == "implement" else []
    items_total = mirror.get("items_total")
    items_applied = mirror.get("items_applied")
    counted_items = False
    if isinstance(items_total, int) and isinstance(items_applied, int):
        # F9: `ok`/`total` count batches, not the items inside them — a
        # write mirror that recorded both (`write_batch_scheduler`) says so
        # explicitly rather than leaving "ok" to be read as "items applied".
        # "batches" appears only here, precisely because there is now an
        # item count to contrast it with; the read path's `subagents` mirror
        # carries neither key and keeps the plain `<kind> <ok>/<total> ok`.
        kept = [
            str(task_id) for task_id in (mirror.get("kept_task_ids") or [])
            if task_id
        ] if isinstance(mirror.get("kept_task_ids"), list) else []
        kept_labels = _kept_labels(mirror, kept) if kept or folded else {}
        kept += [task_id for task_id in folded if task_id not in kept]
        # Fix round 18 (run 7 #3): a resume that dispatched nothing read
        # "1/4 batches ok", the one being a check an earlier run finished.
        # Fix round 20 (run 8 #6): each kept task is named with what it is,
        # in the `resume: kept` line's words, an accepted one included.
        kept_note = (
            f" ({len(kept)} kept from an earlier run: "
            f"{_kept_text(kept, kept_labels)})"
            if kept else ""
        )
        if total == 0:
            # Fix round 22 (live run 9 #5, Codex 01b): a resume that
            # dispatched nothing read "implement 0/0 batches ok (1 kept …),
            # 0/0 items applied" under "failed".
            parts = [f"{kind}: nothing dispatched{kept_note}"]
        elif kind == "implement":
            # Implement counts tasks, as its `[ETA]` lines say (fix round
            # 22). An implement task is its own one item, so "3/4 items
            # applied" beside "4/4 tasks ok" counted the same tasks a second
            # way (fix round 24, live run 10 #7); the outcome clauses below
            # say which applied an edit.
            parts = [f"{kind} {ok}/{total} tasks ok{kept_note}"]
        else:
            # Fix round 26 (live run 11, OpenCode 05 said the task
            # suggestions went "to plans/racing-game.md"): a single-target
            # phase's line names the file its items were applied to.
            applied_to = mirror.get("applied_to")
            target = (
                f" to {clip(plain_line(applied_to), 200)}"
                if isinstance(applied_to, str) and plain_line(applied_to) else ""
            )
            parts = [
                f"{kind} {ok}/{total} batches ok{kept_note}, "
                f"{items_applied}/{items_total} items applied{target}"
            ]
            # Fix round 26 (live run 11 #7): the items not applied follow
            # the count they are left out of, after a semicolon.
            counted_items = True
    else:
        parts = [f"{kind} {ok}/{total} ok"]
    # F10: `in_flight` (`write_batch_scheduler._mirror_status`/`_begin_sweep`)
    # is what turns "0 dispatched, heartbeat Ns ago" — indistinguishable from
    # a stall — into naming the task that is still running and for how long.
    in_flight = mirror.get("in_flight") if isinstance(mirror.get("in_flight"), list) else []
    entries = []
    for row in in_flight:
        if not isinstance(row, dict) or not row.get("task_id"):
            continue
        # Same defensive read as `_model_timing_text`, same reason (F5,
        # 2026-09-20): `dispatched_at` goes through the same `ValueError`-only
        # parser, so one tz-aware stamp written by a future mirror would take
        # the whole poll down instead of costing this row its `(since …)`.
        try:
            elapsed = detach._elapsed_since(row.get("dispatched_at"))
        except Exception:
            elapsed = None
        since = (
            f" (since {metrics.format_duration(int(elapsed * 1000))})"
            if elapsed is not None else ""
        )
        entries.append(f"{row['task_id']}{since}")
    if entries:
        parts.append(f"in flight: {', '.join(entries)}")
    for status, count in sorted(counts.items()):
        if status != "ok" and count:
            parts.append(f"{status} {count}")
    outcomes: Dict[str, int] = {}
    for row in tasks:
        # `outcome_label` first: a verification-only task's `no-op` reads
        # `verified` here as on every other surface (2026-10-04).
        row = row if isinstance(row, dict) else {}
        outcome = str(row.get("outcome_label") or row.get("write_outcome") or "")
        if outcome:
            outcomes[outcome] = outcomes.get(outcome, 0) + 1
    # F14: when every batch's outcome is `applied` the breakdown collapses to
    # a single `applied N` where N is exactly the `ok` count already stated
    # earlier in the line (`<kind> <ok>/<total> [batches] ok`) — printing it
    # again under a different label read as a third, smaller quantity rather
    # than a restatement, and an opencode agent once repeated it verbatim as
    # such. A breakdown with more than one outcome (`applied 7, no-op 2`)
    # still tells the reader something the `ok` count alone does not, so that
    # case is unchanged.
    if not (len(outcomes) == 1 and outcomes.get("applied") == ok):
        for outcome, count in sorted(outcomes.items()):
            parts.append(f"{outcome} {count}")
    failed = mirror.get("failed_task_ids") or []
    if failed:
        parts.append(f"failed {', '.join(map(str, failed))}")
    # Racing re-run 4 (2026-10-05): a check task that ran and reported
    # problems is named, never only counted under its label.
    flagged = mirror.get("check_findings_task_ids")
    if isinstance(flagged, list) and flagged:
        parts.append(f"check findings {', '.join(map(str, flagged))}")
    # Fix round 14: a code batch applied its edits, then a check it ran
    # failed — never only an `ok` count.
    failing = mirror.get("batch_check_task_ids")
    if isinstance(failing, list) and failing:
        # Fix round 15: a check that could not run is named so (the prefix is
        # `subagent_executor.BATCH_CHECK_COULD_NOT_RUN`, spelled here so this
        # sub-second path imports nothing heavy).
        could_not = {
            str(row.get("task_id")) for row in (mirror.get("tasks") or [])
            if isinstance(row, dict)
            and isinstance(row.get("batch_check_findings"), list)
            and row["batch_check_findings"]
            and str(row["batch_check_findings"][0]).startswith(
                "its check could not run")
        }
        fails = [str(t) for t in failing if str(t) not in could_not]
        if fails:
            parts.append(f"own check fails {', '.join(fails)}")
        unrun = [str(t) for t in failing if str(t) in could_not]
        if unrun:
            parts.append(f"own check could not run {', '.join(unrun)}")
    # Fix round 23: a task whose own check repeated only the findings the
    # user accepted for a check is named, never only counted `ok`.
    repeated = mirror.get("batch_check_accepted")
    if isinstance(repeated, dict) and repeated:
        parts += accepted_rerun_clauses({
            str(task_id): checks for task_id, checks in repeated.items()
            if isinstance(checks, list)
        })
    # Fix round 28: and one whose own check repeated a check task's finding.
    echoed = mirror.get("batch_check_repeats")
    if isinstance(echoed, dict) and echoed:
        parts += repeated_check_clauses({
            str(task_id): checks for task_id, checks in echoed.items()
            if isinstance(checks, list)
        })
    # Fix round 18: an item a finished batch declined (or one skipped at the
    # user's request) is named, never only left out of `items applied`.
    not_applied = not_applied_item_clauses(mirror)
    if not_applied and counted_items:
        parts[0] = "; ".join([parts[0], *not_applied])
    else:
        parts += not_applied
    # Racing re-run 3 (2026-10-05): the tasks a stop left undispatched were
    # on no surface at all; a failed task the user accepted is named too.
    not_run = mirror.get("not_run_task_ids") if isinstance(mirror.get("not_run_task_ids"), list) else []
    # Fix round 11: a task a check with findings kept from running says so,
    # naming the check (from the run's first such check on, not only at its end).
    blocked = mirror.get("blocked_by_check") if isinstance(mirror.get("blocked_by_check"), dict) else {}
    stopped = [task_id for task_id in not_run if str(task_id) not in blocked]
    if stopped:
        parts.append(f"not run {', '.join(map(str, stopped))}")
    for check_id in sorted({str(value) for value in blocked.values()}):
        waiting = sorted(str(t) for t, c in blocked.items() if str(c) == check_id)
        parts.append(
            f"not run (upstream check {check_id} reported problems) {', '.join(waiting)}"
        )
    # Fix round 16 (Codex stop-path accept 02): a check accepted with its
    # findings read "accepted after failing T002"; the mirror names those
    # apart (a mirror without the key reads as before). An implement mirror
    # names them in the kept note instead (fix round 20).
    with_findings = set(_id_list(mirror.get("accepted_with_findings_task_ids")))
    shown = set(folded) if isinstance(items_total, int) and isinstance(items_applied, int) else set()
    accepted_checks = [
        str(t) for t in accepted if str(t) in with_findings and str(t) not in shown
    ]
    accepted_failed = [
        str(t) for t in accepted if str(t) not in with_findings and str(t) not in shown
    ]
    if accepted_checks:
        parts.append(f"accepted with its check findings {', '.join(accepted_checks)}")
    if accepted_failed:
        parts.append(f"accepted after failing {', '.join(accepted_failed)}")
    # F9: `skipped_task_ids`/`human_task_strategy` (resolved before dispatch,
    # `write_batch_scheduler._mirror_status`) were on `.status.json` already
    # but rendered nowhere, so the one task `--yes`'s default strategy defers
    # to a human was invisible in the finished run's own progress line.
    skipped_ids = mirror.get("skipped_task_ids") if isinstance(mirror.get("skipped_task_ids"), list) else []
    # Fix round 14: a task the user skipped (`--human-task <id>=skip`), and
    # the tasks skipped with it, are not manual work left for the user, so
    # they are named apart from the deferral (Codex stop-path accept 02 read
    # "deferred manual: T005, T006" beside a summary saying "Skipped at your
    # request"). A mirror without the keys reads as before.
    declined = _id_list(mirror.get("declined_task_ids"))
    with_them = _id_list(mirror.get("declined_dependent_task_ids"))
    # Fix round 17: a task skipped with a deferred manual task is named
    # apart, as the phase tally names it (`deferred_waits_on`; a mirror
    # without the key reads as before).
    raw_waits = mirror.get("deferred_waits_on")
    waits_on = {
        str(task_id): str(root) for task_id, root in raw_waits.items()
    } if isinstance(raw_waits, dict) else {}
    deferred = [
        str(task_id) for task_id in skipped_ids
        if str(task_id) not in declined and str(task_id) not in with_them
        and str(task_id) not in waits_on
    ]
    if deferred:
        strategy = mirror.get("human_task_strategy")
        suffix = f" ({strategy})" if strategy else ""
        parts.append(f"deferred manual: {', '.join(deferred)}{suffix}")
    waiting = [
        str(task_id) for task_id in skipped_ids if str(task_id) in waits_on
    ]
    if waiting:
        parts.extend(_bucket_clauses(
            {"deferred_dependents": waiting}, waits_on,
            (("deferred_dependents", "skipped (depends on a manual task)"),),
        ))
    if declined:
        parts.append(f"skipped at your request: {', '.join(declined)}")
    if with_them:
        parts.append(
            f"skipped (depend on a task you skipped): {', '.join(with_them)}"
        )
    # F4: `driver.verify_command`'s outcome. Without it a run that applied every
    # batch and then failed the repository's own check renders as
    # `apply_code_fixes 3/3 batches ok` with no failed id anywhere — the only
    # sign of the failure being a phase state the counts contradict.
    verification = mirror.get("verification")
    if isinstance(verification, dict) and verification.get("command"):
        verdict = "passed" if verification.get("exit_code") == 0 else (
            f"FAILED (exit {verification.get('exit_code')})"
        )
        parts.append(f"verification {verdict}: `{verification['command']}`")
    return parts


#: The modes whose ``--reaggregate`` is the retry-only-the-failures verb a
#: failed run resumes with (D2 step 4): it re-dispatches the failed batches and
#: re-reads the rest. Every mode in neither table keeps ``--force``, the only
#: resume verb it accepts. ``status`` cannot afford to import each
#: orchestrator's parser to derive this, so these are the two tables in this
#: module that are typed rather than read. ``review-commits`` forwards every
#: flag it does not own to review-code (plans/review-commits.md §2.1), so its
#: retry verb is review-code's.
_REAGGREGATE_MODES = ("review-plan", "review-tasks", "review-code",
                      "review-commits")

#: Modes whose retry verb is neither. ``generate-tasks`` has a ``--reaggregate``
#: too, but there it is the native host's second half — it only ever *consumes*
#: an existing ``task_generation_result.json`` and refuses when there is none —
#: so it never re-dispatches a failed task. The plain re-invoke does both:
#: re-dispatches what failed, consumes a valid result if one is on disk. This is
#: the verb that phase's own retry hint prints, and the ``resume with:`` line
#: has to agree with it: measured 2026-09-14, the two lines disagreed, the
#: session model followed this one, and the run ended on ``--reaggregate found
#: no task_generation_result.json`` with nothing re-dispatched.
#:
#: The four write phases resume with ``--resume``, the flag their own exit-3
#: block names ("re-invoke with --resume, which re-dispatches only the
#: unfinished batches and replays the prior-changes log from disk"). ``--force``
#: is not their resume verb at all — the apply parsers define it as an alias
#: for ``--yes`` (bulk approval), and under it the apply base re-ingests every
#: human decision instead of replaying the recorded ones. Measured 2026-09-15
#: on a failed ``apply-task-suggestions``: the log said ``--resume``, this line
#: said ``--force``, and the session model ran ``--claude-decide --force`` twice
#: before a human typed ``--resume`` by hand.
#:
#: ``full`` resumes with ``--resume`` too, the verb its own row-14 stop names
#: (``full <plan> --resume``, continue from the first phase not recorded). Under
#: ``full`` ``--force`` re-enters every recorded phase, so a stopped ``full`` run
#: told to re-run with it started over instead of continuing.
#:
#: The two review-then-apply composites resume with ``--resume`` as well, and
#: ``--force`` would start a new review round. Their line is not built from
#: this verb and the recorded flags but from the composite's own continuation
#: (:func:`_composite_resume_tokens`); the entries say what that ends with.
#:
#: The commit modes (plans/review-commits.md §2.8) take their fronted
#: phase's verb: ``apply-commit-fixes`` is apply-code-fixes' ``--resume``,
#: and ``improve-commits`` resumes like the other composites.
_RESUME_VERB_BY_MODE = {
    "generate-tasks": "--yes",
    "apply-suggestions": "--resume",
    "apply-task-suggestions": "--resume",
    "apply-code-fixes": "--resume",
    "implement": "--resume",
    "full": "--resume",
    "improve-plan": "--resume",
    "improve-code": "--resume",
    "apply-commit-fixes": "--resume",
    "improve-commits": "--resume",
}

#: The modes whose progress mirror is ``write_subagents``
#: (``write_batch_scheduler._mirror_status``) rather than ``subagents``.
_WRITE_MODES = ("apply-suggestions", "apply-task-suggestions",
                "apply-code-fixes", "implement")


#: Spells one retry the way the host's user types it: ``(mode, positionals
#: after the plan, flags and verbs) -> command``, or ``None`` to keep the
#: dispatcher command (:func:`user_speller`).
Speller = Any


def user_speller(
    host_id: Optional[str], plan_arg: str,
    *, plan_path: Optional[Path] = None,
) -> Optional[Speller]:
    """The run view's commands in *host_id*'s spelling, or ``None``.

    Fix round 18 (Codex racing run 7): ``resume with:`` printed the raw ``uv
    run … multi_llm.py … --host codex --detach --resume`` while every other
    next-step line of the same view (the manual-task note, the next phase) was
    the host's own spelling. Built from the same ``next_command`` template and
    quoting as ``next_phase.phase_command``, with the plan as typed and only
    the flags the user typed (:func:`cli_common.drop_host_composed_flags`
    over what this host's own skill or shim composes, fix round 19:
    :func:`cli_common.file_route_composed_flags`).

    ``None`` on a tool route (``modes.TOOL_ROUTES``): there the tool's server
    re-spells every dispatcher command in the output itself and also hands it
    back as a tool call in ``options``, which it can only do from the
    dispatcher command. ``None`` too when the host has no template for its
    route; the dispatcher command stands then.

    Fix round 24 (live run 10, Codex): a reader whose environment names no
    route — a shell's ``status`` — spells a run in the route that run was
    started on, passed per call as *route* (its record's ``run.route``,
    :func:`_view_speller`): that route's template and the flags it composes
    (the tool routes' reserved set). A shell's ``status --host codex`` used
    to print the file shim's sentence for a run the plugin's tool started.

    On a commit review (plans/review-commits.md §2.8: the ``state.json`` at
    *plan_path*, else at *plan_arg*, holds ``commit_range``) a command naming
    review-code, apply-code-fixes or improve-commits reads as the commit mode
    with the pinned range, and leaves out every flag a front door synthesises
    or consumes (``next_phase.commit_view_for``).
    """
    import io

    from . import next_phase

    try:
        modes = next_phase._skill_module("modes")
        host = host_capabilities.resolve_host_id(explicit=host_id)
        if next_phase.resolve_route(host, stderr=io.StringIO()) in modes.TOOL_ROUTES:
            return None
    except Exception:  # noqa: BLE001 - advisory: the dispatcher command stands
        return None
    brief = next_phase.brief_view(plan_arg, plan_path)

    def spell(
        mode: str, extra: Sequence[str], tokens: Sequence[str],
        route: Optional[str] = None,
    ) -> Optional[str]:
        resolved = modes.resolve(mode)
        if resolved is None:
            return None
        view = next_phase.spelled_view(resolved.name, brief)
        if view is not None:
            from .commit_spelling import strip_fronted_flags

            tokens = strip_fronted_flags(tokens)
        try:
            chosen = next_phase.resolve_route(
                host, stderr=io.StringIO(), recorded=route)
            template = host_capabilities.next_command_template(host, chosen)
            # A tool route composes the reserved set the servers refuse in
            # a call's flags (`cli_common._HOST_COMPOSED`); a file route its
            # skill's or shim's own.
            composed = (
                cli_common._HOST_COMPOSED if chosen in modes.TOOL_ROUTES
                else cli_common.file_route_composed_flags(host)
            )
        except Exception:  # noqa: BLE001 - advisory: the dispatcher command stands
            return None
        # What the run's own host composed too, when another host reads it
        # (its `--host` is in the replay): never something the user typed.
        table = dict(composed)
        run_host = cli_common.replay_host(tokens)
        if run_host and run_host != host:
            try:
                table.update(cli_common.file_route_composed_flags(run_host))
            except Exception:  # noqa: BLE001 - an unknown id adds nothing
                pass
        kept = [str(token) for token in [
            *extra, *cli_common.drop_host_composed_flags(tokens, table)]]
        # A token this one-line spelling cannot carry as it is — an `ask`
        # question with a newline or a tab, an empty value — keeps the
        # dispatcher command, which quotes it whole. Fix round 19: those
        # tokens were dropped, so a two-line question vanished from the
        # line and the command printed did not parse.
        if any(not token or not token.isprintable() for token in kept):
            return None
        if view is not None:
            return template.replace(
                next_phase.ARGS_SLOT,
                next_phase.commit_spelled_args(resolved.name, view, kept))
        words = [f"--{resolved.name}", next_phase.quote_plan_arg(plan_arg)]
        words += [next_phase.quote_plan_arg(token) for token in kept]
        return template.replace(next_phase.ARGS_SLOT, " ".join(words))

    spell.host = host  # type: ignore[attr-defined]
    return spell


def _retry_command(
    mode: str, plan_path: Path, *args: str, flags: Optional[Sequence[str]] = None,
) -> str:
    """``cli_common.retry_command(mode, plan_path, *args, flags=flags)``, the
    dispatcher spelling of a retry this view prints, in the commit spelling
    on a commit review (plans/review-commits.md §2.8, "Spelling of
    commands"): the commit mode, the pinned range (the brief path on a root
    range) and none of the flags a front door synthesises or consumes, in
    *args* or in the replayed *flags*. A plan's run, and a direct
    ``--head-ref`` run, keep the command byte for byte."""
    from . import next_phase

    view = next_phase.commit_view_for(mode, str(plan_path))
    if view is None:
        return cli_common.retry_command(mode, str(plan_path), *args, flags=flags)
    from .commit_spelling import strip_fronted_flags

    return cli_common.retry_command(
        next_phase.commit_mode_word(mode, view), view.pinned,
        *strip_fronted_flags(args),
        flags=strip_fronted_flags(flags) if flags is not None else None,
    )


def _run_route(view: Mapping[str, Any], host: Optional[str]) -> Optional[str]:
    """The route *view*'s run recorded (``run.route``, fix round 24) when
    that run is *host*'s, else ``None``: another host's route says nothing
    of how this host's user types a command."""
    run = view.get("run") if isinstance(view.get("run"), Mapping) else {}
    route = run.get("route")
    if not isinstance(route, str) or not host or run.get("host") != host:
        return None
    return route


def _view_speller(spell: Optional[Speller], view: Mapping[str, Any]) -> Optional[Speller]:
    """*spell* for one run view: its commands in the route that run was
    started on (:func:`_run_route`), else *spell* as it is."""
    route = _run_route(view, getattr(spell, "host", None)) if spell else None
    if route is None:
        return spell
    import functools

    return functools.partial(spell, route=route)


def _resume_command(
    view: Dict[str, Any], plan_path: Path, spell: Optional[Speller] = None,
    extra: Sequence[str] = (),
) -> str:
    """The ``resume with:`` command, with the run's own flags spliced back in.

    Flags come from the run record's ``replay_flags`` (the launcher's list,
    D2) through :func:`cli_common.current_replay_flags`, whose live-source rule
    never lets ``status``'s own ``--view run`` argv win here (a different
    mode). ``ask`` re-derives its question positional from the checkpoint's
    ``question`` field — the one place it is stored — and falls back to the
    questionless string when the key is missing. With *spell*
    (:func:`user_speller`) the same retry in the host's spelling.

    A review-then-apply composite (``improve-plan``, ``improve-code``) takes
    its tokens from its own continuation instead (:func:`_composite_resume_tokens`,
    plans/improve-plan-and-improve-code.md §2.6): the selectors its launcher
    typed, never ``--force``, then ``--resume``. A run launched with ``--force``
    is then not told to start another round, and the line names the command
    ``util next-command --blocked <composite>`` names when no inner phase has a
    resume of its own.
    """
    run = view["run"]
    mode = str(run.get("mode") or view.get("phase") or "review-plan")
    positionals = [str(plan_path)]
    row = cli_common._modes().resolve(mode)
    if row is not None and row.is_composite and not row.runs_workflow:
        flags: List[str] = []
        verbs = _composite_resume_tokens(row.name, run.get("replay_flags"))
    else:
        flags = cli_common.current_replay_flags(run.get("replay_flags"), mode=mode)
        if mode == "ask" and view.get("question"):
            positionals.append(str(view["question"]))
        verb = _RESUME_VERB_BY_MODE.get(mode) or (
            "--reaggregate" if mode in _REAGGREGATE_MODES else "--force"
        )
        # *extra*: the answers the resume carries (fix round 28: a manual task
        # every code task left waits on, `_manual_gate_answers`).
        verbs = [verb, *[str(token) for token in extra]]
    if spell is not None:
        _positionals, tokens = cli_common.retry_tokens(*positionals, *verbs, flags=flags)
        spelled = spell(mode, positionals[1:], tokens)
        if spelled:
            return spelled
    # On a commit review the commit spelling (plans/review-commits.md §2.8).
    return _retry_command(mode, plan_path, *positionals[1:], *verbs, flags=flags)


def _composite_resume_tokens(mode: str, replay_flags: Any) -> List[str]:
    """A composite run's ``resume with:`` tokens after the plan (§2.6).

    ``improve_workflow.recorded_continuation`` of the run record's own
    ``replay_flags``, the list ``util next-command --blocked`` reads, so the
    two name one command. A list that is not a list reads as no record
    (``--resume`` alone). Flags the composite's parser rejects (a record from
    an older parser, or one a batch rewrote) cost one stderr line and fall
    back to ``--resume`` alone: replayed as recorded they would not parse
    either, and their ``--force`` would start another round. ``--blocked``
    refuses the same record (exit 3), since it hands its command back as a
    tool call.

    On a composite whose positional is a range (``improve-commits``) the
    tokens never carry a flag its front door synthesises or consumes
    (``--plan-file``, ``--base-ref``, ``--head-ref``, ``--focus``,
    ``--context-plan``; plans/review-commits.md §2.8): the front door refuses
    the first three, and the brief inherits the rest.
    """
    from . import improve_workflow

    recorded = replay_flags if isinstance(replay_flags, list) else None
    try:
        tokens = improve_workflow.recorded_continuation(mode, recorded)
        row = cli_common._modes().resolve(mode)
        if row is not None and cli_common._modes().POS_REVS in tuple(row.positionals):
            from .commit_spelling import strip_fronted_flags

            tokens = strip_fronted_flags(tokens)
        return tokens
    except improve_workflow.ContinuationError as exc:
        detail = " ".join(str(exc).split())
        print(
            f"multi-llm: {mode}'s run recorded flags its parser rejects "
            f"({detail}); resume with: names --resume alone",
            file=sys.stderr,
        )
        return [_RESUME_VERB_BY_MODE.get(mode, "--resume")]


def _manual_gate_answers(
    mode: str, plan_path: Path, workflow: Optional[Dict[str, Any]],
) -> List[str]:
    """``--human-task <id>=done …`` an implement's resume carries while every
    code task it left waits on a manual task the user can do now
    (``next_phase._resume_flags``, fix round 28), else ``[]``."""
    if mode != _IMPLEMENT_PHASE:
        return []
    try:
        if workflow is None:
            workflow = _workflow_payload(plan_path)
        from . import next_phase

        return next_phase._resume_flags(workflow.get("phases") or {}, _IMPLEMENT_PHASE)[1:]
    except Exception:  # noqa: BLE001 - advisory: the plain resume stands
        return []


def _stale_review_of(phase_name: str, workflow: Dict[str, Any]) -> Optional[str]:
    """The phase name of *phase_name*'s prerequisite review when it is stale too."""
    try:
        import check_workflow_prerequisites as prereq  # type: ignore
    except ImportError:  # pragma: no cover - only when utils/ is sys.path[0]
        sys.path.insert(0, str(Path(os.path.abspath(__file__)).parent.parent))
        import check_workflow_prerequisites as prereq  # type: ignore
    for review in prereq.PHASE_PREREQUISITES.get(phase_name, ()):
        if ((workflow.get("phases") or {}).get(review) or {}).get("stale"):
            return review
    return None


def _rerun_command(
    view: Dict[str, Any], plan_path: Path, *, mode: Optional[str] = None,
    spell: Optional[Speller] = None,
) -> str:
    """The plain re-run of a done run whose phase went stale: no verb at all.

    :func:`_resume_command`'s sibling for the stale case (2026-10-02). A
    ``--reaggregate`` re-stamps the stale completion from the artifacts the
    old run left, and ``--force`` is the apply parsers' ``--yes`` alias; the
    plain command is what each phase answers with on a stale record
    (``code_review_orchestrator`` takes its ``--force`` path itself). The run's
    own ``replay_flags`` ride along, as on every retry line — unless *mode*
    names another phase (its stale review), whose run this view has no flags
    for.
    """
    run = view["run"]
    if mode is not None:
        resolved = cli_common._modes().resolve(mode)
        word = resolved.name if resolved is not None else mode
        flags: List[str] = []
    else:
        word = str(run.get("mode") or view.get("phase") or "review-code")
        flags = cli_common.current_replay_flags(run.get("replay_flags"), mode=word)
    if spell is not None:
        # Fix round 18: in the host's spelling, as `resume with:` is.
        spelled = spell(word, [], cli_common.retry_tokens(str(plan_path), flags=flags)[1])
        if spelled:
            return spelled
    return _retry_command(word, plan_path, flags=flags)


def _resume_shape(view: Dict[str, Any]) -> "tuple":
    """``(shape, repair, redispatch, kept)`` from the document, in two reads.

    1. the run record's close-out — D4's ``{"state": "runner_rejected",
       "reason_code": …}``, written at the checkpoint's top level and mirrored
       into the view — is the refusal's classification made durable and, after
       a refusal, the only thing on disk ⇒ shape 1;
    2. otherwise ``progress.subagents`` (``_mirror_status``), whose ``counts``
       split by ``FATAL_STATUSES`` ⇒ shape 1 or 2. Its freshness is the
       writer's property: ``claim_run`` drops the predecessor's ``run`` **and**
       ``progress`` together, so a mirror beside a run record is that run's.
    3. neither ⇒ shape 2, the transient default.

    Never ``subagent_batch_report.json``: the report in the phase dir may be
    the previous run's, and it is an arbitrarily large read on a command that
    must stay sub-second.
    """
    run = view["run"]
    reason_code = None
    if run.get("state") == "runner_rejected" or view.get("state") == "runner_rejected":
        reason_code = run.get("reason_code") or view.get("reason_code") or "runner_rejected"
    progress = view.get("progress") or {}
    mirror = progress.get("subagents") or {}
    if not mirror and isinstance(progress.get("write_subagents"), dict):
        # A write phase mirrors per-batch outcomes instead of a counts table
        # (`write_batch_scheduler._mirror_status`); its shape is the transient
        # default and its cost line counts batches.
        mirror = _write_mirror_as_counts(progress["write_subagents"])
    counts = mirror.get("counts") if isinstance(mirror.get("counts"), dict) else {}
    shape = cli_common.retry_shape(reason_code=reason_code, statuses=counts.keys())
    repair = None
    if shape == cli_common.SHAPE_REPAIR:
        repair = cli_common.repair_sentence(
            reason_code=reason_code, explanation=_reason_explanation(reason_code),
            counts=counts,
        )
    redispatch = len(mirror.get("failed_task_ids") or []) or None
    kept = mirror.get("ok") if isinstance(mirror.get("ok"), int) else None
    return shape, repair, redispatch, kept


def _write_mirror_as_counts(mirror: Dict[str, Any]) -> Dict[str, Any]:
    """``progress.write_subagents`` in the shape ``_resume_shape`` reads.

    ``ok`` counts every batch the mirror records as ``ok`` — the ones this run
    applied and the ones a resume skipped because their result file was already
    on disk — and ``failed_task_ids`` is carried as recorded.
    """
    tasks = mirror.get("tasks") if isinstance(mirror.get("tasks"), list) else []
    counts: Dict[str, int] = {}
    for row in tasks:
        status = str((row or {}).get("status") or "")
        if status:
            counts[status] = counts.get(status, 0) + 1
    return {
        "counts": counts,
        "ok": counts.get("ok", 0),
        "failed_task_ids": list(mirror.get("failed_task_ids") or []),
    }


def _stop_resume_why(view: Dict[str, Any]) -> Optional[str]:
    """The write run's stop's ``resume_why`` (fix round 22), from its mirror,
    under ``next_phase.stop_resume_why_on_record``'s rule: one plain line of
    a sane length, since a jailed batch can write the folder it lives in."""
    from .next_phase import recorded_why

    progress = view.get("progress") or {}
    mirror = progress.get("write_subagents") if isinstance(progress, dict) else None
    stop = mirror.get("stop") if isinstance(mirror, dict) else None
    return recorded_why(stop.get("resume_why") if isinstance(stop, dict) else None)


def _failed_batches_moved_nothing(view: Dict[str, Any]) -> bool:
    """Whether every failed row of a write run's mirror records that no file
    moved (``files_touched`` present and empty). A row without the key — an
    older mirror — says nothing, so the answer is ``False`` and the status
    line keeps its "half-applied" wording.

    ``files_touched`` is the rollback set, so a row also has to name no
    ``unrestorable`` file (moved, with no rollback point) and must not be a
    partial application, which moved bytes by definition (fix round 15)."""
    progress = view.get("progress") or {}
    mirror = progress.get("write_subagents") if isinstance(progress, dict) else None
    if not isinstance(mirror, dict):
        return False
    failed_ids = set(mirror.get("failed_task_ids") or [])
    rows = [
        row for row in (mirror.get("tasks") or [])
        if isinstance(row, dict) and row.get("task_id") in failed_ids
    ]
    if not rows:
        return False
    return all(
        isinstance(row.get("files_touched"), list) and not row["files_touched"]
        and not row.get("unrestorable")
        and row.get("write_outcome") != "partial-application"
        for row in rows
    )


def _reason_explanation(reason_code: Optional[str]) -> Optional[str]:
    """``_REASON_EXPLANATION[reason_code]``, imported only on this failed path."""
    if not reason_code:
        return None
    try:
        from .subagent_executor import _REASON_EXPLANATION
    except Exception:  # pragma: no cover - a broken install still prints the code
        return None
    return _REASON_EXPLANATION.get(reason_code)


#: What a write run refused before its first batch gets in place of a
#: ``resume with:`` command (racing re-run 2026-10-04, codex #5: implement
#: refused on the jail before batch 1 offered ``--resume``, which repeats the
#: refusal). No command: the way forward is the remedy the refusal names.
NO_RESUME_BEFORE_DISPATCH = (
    "no resume: nothing was dispatched and the phase has no progress on record, "
    "so a resume would only repeat this stop; fix what the error above names "
    "first, then run the phase again"
)


def _dispatched_nothing(view: Dict[str, Any]) -> bool:
    """A write run whose own mirror records no dispatched and no ``ok`` batch.

    ``progress.write_subagents.batches_dispatched`` is appended per dispatched
    batch (``write_batch_scheduler``), and ``claim_run`` drops a predecessor's
    ``progress`` with its ``run``, so an empty list beside this run record
    means this run sent nothing. A mirror without the key says nothing.
    """
    progress = view.get("progress") or {}
    mirror = progress.get("write_subagents") if isinstance(progress, dict) else None
    if not isinstance(mirror, dict):
        return False
    dispatched = mirror.get("batches_dispatched")
    if not isinstance(dispatched, list) or dispatched:
        return False
    rows = mirror.get("tasks") if isinstance(mirror.get("tasks"), list) else []
    return not any((row or {}).get("status") == "ok" for row in rows)


def _phase_in_progress(
    view: Dict[str, Any], plan_path: Path, workflow: Optional[Dict[str, Any]],
) -> bool:
    """Whether the workflow view shows *view*'s phase ``in_progress``.

    Read from *workflow* when the caller has it, else from ``state.json`` once
    (this is the failure path only). A read that fails answers ``True``, which
    keeps the ``resume with:`` line this predicate would otherwise remove.
    """
    if workflow is None:
        try:
            workflow = _workflow_payload(plan_path)
        except Exception:  # noqa: BLE001 - advisory: keep the old line
            return True
    phase = view.get("phase") or cli_common._modes().phase_for(
        str((view.get("run") or {}).get("mode") or ""))
    entry = (workflow.get("phases") or {}).get(phase) or {}
    return entry.get("status") == "in_progress"


def _resume_lines(
    view: Dict[str, Any], plan_path: Path,
    workflow: Optional[Dict[str, Any]] = None,
    spell: Optional[Speller] = None,
) -> List[str]:
    """The shaped resume block: the repair first when there is one, then the
    single ``resume with:`` command, then what it costs.

    A write run that dispatched nothing, under a phase with no progress on
    record, gets :data:`NO_RESUME_BEFORE_DISPATCH` instead: its ``--resume``
    would repeat the refusal, and a tool route scrapes every command printed
    here into an option.
    """
    mode = str(view["run"].get("mode") or view.get("phase") or "")
    if (
        mode in _WRITE_MODES and _dispatched_nothing(view)
        and not _phase_in_progress(view, plan_path, workflow)
    ):
        return [f"      {NO_RESUME_BEFORE_DISPATCH}"]
    shape, repair, redispatch, kept = _resume_shape(view)
    if mode == _IMPLEMENT_PHASE and redispatch:
        # Fix round 14: the mirror holds only this run's rows, so a resume
        # that kept T001/T003/T004 from an earlier run (and T002's findings)
        # read "keeps the 1 already applied". state.json counts every task
        # of the decomposition on record as done.
        done = _implement_tasks_done(plan_path, workflow)
        if done is not None and done > (kept or 0):
            kept = done
    lines: List[str] = []
    if shape == cli_common.SHAPE_REPAIR:
        lines.append(f"      repair first: {repair}")
    resume = _resume_command(
        view, plan_path, spell, extra=_manual_gate_answers(mode, plan_path, workflow))
    lines.append(f"      resume with: {resume}")
    # Fix round 22 (live run 9): a write run's stop says what its plain
    # resume does on an unchanged tree; that replaces the cost line, which
    # read "re-dispatches the 1 failed batch(es)" of a task the write policy
    # refuses again.
    # Fix round 23 (review of round 22, relay #6): printed as recorded,
    # which ends with what the resume keeps and whether a failed batch is
    # half-applied, so it reads word for word as the tool routes'
    # `resume_why` and `util next-command --blocked` relay it.
    why = _stop_resume_why(view) if mode in _WRITE_MODES else None
    if why:
        # Fix round 28: under the command, unbracketed (`why_line`).
        lines.append(why_line(why))
    elif redispatch:
        mode = str(view["run"].get("mode") or view.get("phase") or "")
        if mode in _WRITE_MODES:
            # The write loop stops at the failed batch, so what a resume
            # re-dispatches is that batch and everything after it; the kept
            # count is the batches whose result files it skips over.
            cost = f"re-dispatches the {redispatch} failed batch(es) and the ones never reached"
            if kept:
                cost += f", keeps the {kept} already applied"
            if _failed_batches_moved_nothing(view):
                # Fix round 14 (stop fixture 01b): a task refused before
                # dispatch, a clean failure, a timeout that wrote nothing —
                # no byte moved, so nothing is half-applied. Fix round 18
                # (live run 7): the stop's own block says so, and this view
                # shows its last lines, so the line no longer says it again.
                lines.append(f"      ({cost})")
            else:
                lines.append(
                    f"      ({cost}; the half-applied state is left in place — inspect "
                    f"it, or `util restore-batch` the failed batch, before resuming)"
                )
        else:
            cost = f"re-dispatches the {redispatch} failed task(s)"
            if kept is not None:
                cost += f" and keeps the {kept} valid result(s) already on disk"
            lines.append(f"      ({cost}; --force is not needed and would re-run the reviewer panel)")
    return lines


def _implement_tasks_done(
    plan_path: Path, workflow: Optional[Dict[str, Any]],
) -> Optional[int]:
    """``phases.implement.tasks_done`` from the workflow view, read once if
    the caller has none; ``None`` when it is not on record or unreadable."""
    if workflow is None:
        try:
            workflow = _workflow_payload(plan_path)
        except Exception:  # noqa: BLE001 - advisory: the mirror count stands
            return None
    done = ((workflow.get("phases") or {}).get(_IMPLEMENT_PHASE) or {}).get("tasks_done")
    return done if isinstance(done, int) and not isinstance(done, bool) else None


def _abort_command(plan_path: Path, view: Dict[str, Any]) -> str:
    """The one selector-carrying ``--abort`` spelling for a single listed run."""
    run_id = str(view["run"].get("run_id") or "")
    if run_id:
        return detach.abort_command_for(str(plan_path), run_id=run_id)
    phase = view.get("phase") or os.path.basename(view["phase_dir"])
    return dispatcher_command("status", str(plan_path), "--abort", "--phase", str(phase))


def _run_runner_facts(
    views: Sequence[Dict[str, Any]]
) -> "tuple":
    """``(host, specs, source)`` the listed runs recorded about their own
    subagents.

    The host is the first one any listed run wrote into ``.status.json``
    (``RunHandle`` records the launcher's ``--host``); the specs are the runner
    keys that same run's executor mirror pinned, i.e. what its dispatches
    actually ran on rather than what a fresh resolution would pick now. Checked
    under both mirror keys — ``subagents`` (the read path) and
    ``write_subagents`` (`write_batch_scheduler._mirror_status`, F7) — a write
    phase carries only the second, and until it recorded a runner at all
    `status` polled outside the launching session fell through to a fresh
    resolution and named the *polling* host's model instead of the run's.

    **A host-bearing view that recorded no spec must not win outright** (F6,
    2026-09-16): with several phases listed, the first one carrying a host can
    be a run whose executor mirror is empty (a failed-before-dispatch run, a
    stale pre-fix record, ``--dry-run-subagents``) while a *later* view holds
    the real answer. Measured on a `generate-tasks` run: the default view's
    ``apply-suggestions`` row sorted first, its mirror had recorded nothing,
    and the search stopped there instead of reaching the `generate-tasks` row
    one below it that had. So an empty-spec view is skipped rather than
    returned, and its host is kept only as the fallback for when no view in
    the whole list ever recorded a spec.

    **Among the views that DID record a spec, the most recently updated one
    wins — not whichever sorts first** (F4, 2026-09-16): ``discover_phase_dirs``
    lists phases in alphabetical directory order, so a `generate-tasks` run's
    pre-`--variant low` record outranked `review-tasks`' own `:low` record
    directly below it, under a line that claimed to be "recorded by this run's
    own dispatches". Every view carries ``updated_at``, so the candidates are
    collected first and the freshest one answers. ``source`` names which run
    the winning spec came from — ``None`` when only one view ever recorded a
    spec, so the caller's existing "this run's own dispatches" wording stays
    exactly as specific as it always was; a phase name, when more than one
    view recorded one, so the line stops asserting an ownership it cannot back.
    """
    fallback_host: Optional[str] = None
    candidates: List[Dict[str, Any]] = []
    for view in views or ():
        run = view.get("run") or {}
        host = run.get("host")
        if not isinstance(host, str) or not host.strip():
            continue
        progress = view.get("progress") or {}
        mirror = progress.get("subagents")
        versions = mirror.get("runner_versions") if isinstance(mirror, dict) else None
        if not isinstance(versions, dict) or not versions:
            mirror = progress.get("write_subagents")
            versions = mirror.get("runner_versions") if isinstance(mirror, dict) else None
        specs = sorted(str(spec) for spec in versions) if isinstance(versions, dict) else []
        if specs:
            name = view.get("phase") or os.path.basename(str(view.get("phase_dir") or "")) or None
            candidates.append({
                "host": host.strip(),
                "specs": specs,
                "name": name,
                "updated_at": str(view.get("updated_at") or ""),
            })
            continue
        if fallback_host is None:
            fallback_host = host.strip()
    if candidates:
        candidates.sort(key=lambda c: c["updated_at"])
        winner = candidates[-1]
        source = winner["name"] if len(candidates) > 1 else None
        return winner["host"], winner["specs"], source
    return fallback_host, [], None


def render_runner_text(
    plan_path: Path,
    host_id: Optional[str] = None,
    *,
    views: Sequence[Dict[str, Any]] = (),
) -> List[str]:
    """The resolved subagent runner, its layer of origin, and who consults it (D3o).

    **The run's host wins over the invoking one.** A poll is routinely typed
    from a different host than the one that launched the run — measured
    2026-09-16, three ``status`` calls on an ``opencode`` run whose eleven
    batches all dispatched to ``opencode:openrouter/…`` each printed
    ``claude-code:sonnet``, because the host came from *this* invocation's argv
    while the run's own sat unread in ``.status.json``. So the run's host is
    what this reports, and with it:

    * the specs the run's executor mirror recorded, when it has dispatched
      anything — the only account on disk of what its subagents really ran on,
      and, when more than one listed view recorded one, the most recently
      updated view's (F4, 2026-09-16), named in the printed line rather than
      claimed as "this run's own";
    * otherwise a fresh resolution for that host, with the **session** rung
      skipped whenever the run was launched elsewhere: that rung reads
      ``MULTI_LLM_HOST_SESSION_MODEL`` off *this* process, which is the polling
      session's model and not the run's. The plugin's own poll passes
      ``--host opencode`` from inside the session that launched the run, so
      there the rung still applies and still answers ``(supplied by session)``.

    "I set ``driver.subagent_runner`` and nothing changed" has three different
    answers — a higher layer won, no layer expressed an opinion so the running
    host's own ``default_subagent_runner`` answered, or this host dispatches
    subagents natively and never consults the key outside ``--exec-subagents`` —
    and a merged value printed on its own distinguishes none of them. So the
    layer is printed with the value, resolved through the *same*
    ``resolve_subagent_runner`` a dispatch takes rather than re-derived here.

    It is reported, never resolved: ``status`` writes nothing, takes no lock and
    must stay sub-second, so a config layer that cannot be read (a ``ConfigError``
    from a broken override, an unknown ``--host``, a partial install) prints
    nothing at all rather than failing a poll. Text only — the ``--json`` views
    stay exactly two keys, ``workflow`` and ``runs``, because this is a config
    fact and blending it into either state view is what ``--view`` exists to
    prevent.
    """
    try:
        from . import host_capabilities as caps
        from .provider_registry import resolve_subagent_runner

        invoking_host = caps.resolve_host_id(sys.argv[1:], explicit=host_id)
        run_host, recorded, recorded_by = _run_runner_facts(views)
        resolved_host = run_host or invoking_host
        if recorded:
            spec = ", ".join(recorded)
            source = (
                f"recorded by {recorded_by}'s own dispatches" if recorded_by
                else "recorded by this run's own dispatches"
            )
        else:
            spec, layer = resolve_subagent_runner(
                "full", anchor=str(plan_path), host_id=resolved_host,
                skip_session=resolved_host != invoking_host,
            )
            source = f"supplied by {layer}"
        native = str(caps.entry(resolved_host).get("subagents")) == "native"
    except Exception:
        return []
    scope = (
        f"{resolved_host} dispatches subagents natively, so it is consulted "
        "only under --exec-subagents"
        if native
        else f"every subagent {resolved_host} dispatches runs through it"
    )
    return [
        "driver.subagent_runner — what a dispatched subagent would run:",
        f"  {spec}  ({source})",
        f"  {scope}",
    ]


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
    from .cli_common import _modes

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
    for directory in discover_phase_dirs(plan_path, phase=phase):
        try:
            status = status_file.read_status(str(directory))
        except Exception:
            continue
        run = status.get("run") if isinstance(status.get("run"), dict) else {}
        stubs.append(
            {"phase_dir": str(directory), "phase": status.get("phase"), "run": run}
        )
    return {
        "ignored_dirs": [] if phase else ignored_phase_dirs(plan_path),
        "copies": _dedupe_run_ids(stubs)[1],
    }


def _collect(plan_path: Path, args: argparse.Namespace) -> List[Dict[str, Any]]:
    phase = _resolve_phase(args.phase)
    views = [
        detach.classify_run(str(directory))
        for directory in discover_phase_dirs(plan_path, phase=phase)
    ]
    # Plan §7.4b: two views with one run id are one run.
    views = _dedupe_run_ids(views)[0]
    return _select(
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
      (``commit_review.brief_for_pinned``, no git call), so every view,
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
    from . import commit_range, commit_review

    try:
        brief = commit_review.brief_for_pinned(value)
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
        from .commit_apply import fixes_from_state

        state_file = output_dir_path(plan_path) / "state.json"
        if not state_file.is_file():
            return None
        state = json.loads(state_file.read_text(encoding="utf-8"))
        return fixes_from_state(state) if isinstance(state, dict) else None
    except Exception:  # noqa: BLE001 - advisory: the run view is not
        return None


def main(argv: Optional[Sequence[str]] = None) -> int:
    bootstrap_streams()
    args = parse_args(argv)
    try:
        plan_value = status_plan_value(args.plan_file)
    except StatusSpellingRefused as exc:
        return _refuse_status_spelling(exc, as_json=args.json)
    plan_path = Path(os.path.abspath(plan_value))

    if not plan_path.exists():
        payload = {"error": f"{_document_file_label(plan_path)} not found: {plan_path}"}
        print(json.dumps(payload, indent=2))
        return EXIT_ERROR

    if args.abort:
        return _run_abort(plan_path, args)
    if args.sweep:
        return _run_sweep(plan_path, args)

    workflow = None
    if args.view in (VIEW_WORKFLOW, VIEW_ALL):
        try:
            workflow = _workflow_payload(plan_path, host_id=_reader_host(args))
        except Exception as exc:  # unreadable state.json is exit 1, not a crash
            print(json.dumps({"error": f"{type(exc).__name__}: {exc}"}, indent=2))
            return EXIT_ERROR

    if args.view == VIEW_WORKFLOW:
        # Byte-identical to `check_workflow_prerequisites.py --plan-file X
        # --status`, so a caller that only ever wanted today's phase map keeps
        # today's behavior — including its exit 0.
        print(json.dumps(workflow, indent=2))
        return EXIT_OK

    views = _collect(plan_path, args)
    discovery = _discovery_report(plan_path, args)
    if args.wait:
        # `--timeout` is a sentinel out of argparse, and this is the one place
        # it becomes a number: between `parse_args` and the `--wait` branch,
        # where the resolution can see both the flag and the config. Resolved
        # only under `--wait`, so a plain `status` still pays no `load_config`
        # on a path that would never use the answer.
        try:
            args.timeout = _resolve_wait_timeout(args, plan_path)
        except _WaitTimeoutRefused as exc:
            # Exit 3, and nothing on stdout: rule 2 stops the loop on a `3` and
            # relays the message verbatim because it names the fix, while exit 1
            # would have the agent report the *run* as unreadable. Stderr keeps
            # `--json`'s stdout parseable — what there is of it, which is
            # nothing, because no view was resolved to print (F4/F7, 2026-09-20).
            print(f"ERROR: {exc}", file=sys.stderr)
            return EXIT_NEEDS_HUMAN
        views = _wait_for_terminal(plan_path, args, views)

    # Fix round 26 (the commit review of 2026-10-08, "stale executor status
    # after switching to native execution"): an executor run a native run of
    # the same phase went on from is not this phase's run any more.
    superseded: Dict[str, Dict[str, Any]] = {}
    if not args.run_id and not args.question:
        try:
            views, superseded = set_aside_superseded_runs(
                plan_path, views, host_id=_reader_host(args))
        except Exception:  # noqa: BLE001 - advisory: the run view is not
            superseded = {}

    # Fix round 16 (run 6): an executor implement run's own counts are that
    # run's; every task of the phase is tallied from state.json beside them.
    implement_tally = None
    if any(_is_executor_implement_view(view) for view in views):
        try:
            implement_tally = implement_task_tally(plan_path)
        except Exception:  # noqa: BLE001 - advisory: the run view is not
            implement_tally = None

    # N5, 2026-09-16: the dispatcher stamped `ctx.mode = "status"`,
    # `ctx.phase = None` before this ever ran (`status` is a command, not a
    # phase) — right for a plain multi-run listing, but the opencode plugin's
    # supervised poll pins one run (`--run-id`, sometimes also `--phase`) and
    # reads this leg's own MULTI_LLM_RESULT verbatim. That payload said
    # `{"mode": "status", "phase": null, …}` for a finished `implement` run,
    # and a weaker model than the one that hit this had to infer its phase had
    # finished from `state: done` alone. The watched run already knows both —
    # `.status.json.run.mode`, falling back to the phase dir it lives in — so a
    # poll pinned to exactly one run carries them into its own result.
    # Ambiguous (more than one view, or no selector at all) keeps
    # `status`/`None`: no single run is "the" answer there. F3, 2026-09-17:
    # what makes a poll "the watched run's" is the selector, not whether it
    # also waited, so this sits outside `if args.wait` — a single-view poll
    # without `--wait` was still emitting the old `status`/`null` pair. F8a,
    # 2026-09-20: `--question` joined the pair. The selector list `status`
    # documents is `--phase`/`--question`/`--run-id`, and `ask` is the one mode
    # whose instruction core forbids `--phase` outright (`--phase ask` selects
    # every question ever asked under the plan), so the ask lane polls by
    # `--question` and by nothing else — leaving the one mode that always pins
    # exactly one run as the one mode whose result line carried no `progress`.
    # The rule the test below is written to is "did the caller name one run?",
    # and all three selectors answer it.
    # The stop's own line as the result carries it, when this poll records
    # one: a notice part it already says is left out below (fix round 26).
    stop_error: Optional[str] = None
    if len(views) == 1 and (args.phase or args.question or args.run_id):
        watched = views[0]
        watched_run = watched.get("run") or {}
        watched_mode = str(
            watched_run.get("mode") or watched.get("phase") or ""
        ) or None
        # A composite's run dir holds no phase of its own; its report
        # records the one its worker's line says (D2).
        watched_phase = str(
            watched.get("phase")
            or detach.recorded_step_results(watched).get("phase") or ""
        ) or None
        record_mode_phase(watched_mode, watched_phase)
        # Same selector, same reason one step further: a supervised poll that
        # pins one run reads its own `MULTI_LLM_RESULT` verbatim and never opens
        # the rendered text, so the per-model map has to ride the result line or
        # that caller would have to regex a human table to relay anything
        # mid-run. Whole and unreworded — the numbers come from the status file,
        # which is the point of producing them there.
        record_progress(watched.get("progress"))
        # And beside it, the same run rendered (`_progress_lines`). The map
        # alone was only half an answer for the one caller that has no agent in
        # its loop: it could relay nothing without composing a sentence about
        # the run, which is precisely what the OpenCode plugin may not do. A
        # separate key rather than one more key inside `progress`, so that
        # object stays what the status file wrote.
        progress_lines = _progress_lines(watched)
        if implement_tally is not None and _is_executor_implement_view(watched):
            # Fix round 16: the OpenCode route shows these lines and nothing
            # else, so the whole phase's tally rides them too.
            progress_lines.append(
                "implement tasks: "
                + implement_tally_text(implement_tally, live=_run_is_live(watched))
            )
        record_progress_lines(progress_lines)
        # The run's own stop line (`run.error`, written by the worker from
        # the result context's `error`): the hosts read a terminal poll's
        # `payload.error` as "the last line it left", so a stopped implement's
        # reason and remedy reach the message (racing re-run 3, 2026-10-05).
        # The generic close-out word is not a reason and is left off.
        recorded_error = watched_run.get("error")
        if (
            isinstance(recorded_error, str) and recorded_error.strip()
            and recorded_error.strip() != GENERIC_NEEDS_HUMAN_ERROR
            and watched.get("verdict") in (detach.VERDICT_FAILED,)
        ):
            record_error(recorded_error.strip())
            stop_error = recorded_error.strip()

    exit_code = exit_code_for(views)

    # Plan §5: a detached run whose result was `partial` exits 0, and
    # `cli_common.emit` would turn exit 0 into `done` — the word the host then
    # relays. The worker carried the word across the process boundary as
    # `run.result_state`; a poll pinned to that one run restates it. The failed
    # specs and reasons are already on `progress.models`, recorded above. Only
    # on exit 0: any other exit already has its own word. `--json`'s
    # `runs[].run.state` stays the process word `done`.
    if (
        exit_code == EXIT_OK
        and len(views) == 1
        and (args.phase or args.question or args.run_id)
    ):
        carried = _result_state(views[0])
        if carried:
            record_state(carried)

    # F7, 2026-09-16: the opencode plugin polls only `--view run`, so a
    # terminal run's real follow-up — the workflow view's `notice:`/`suggested
    # next:` line — lived in text that channel never read. The model saw
    # `next: null`, said "nothing further to run", then invented
    # `--apply-task-suggestions` from general knowledge instead of the notice
    # already sitting one view over. Carried only for a TERMINAL run (every
    # listed view done/failed/aborted) and only on `--view run` itself —
    # `--view all` already renders the workflow section in full, and a
    # still-running poll has nothing to say about what comes after a run that
    # has not finished. A workflow-read failure here is swallowed rather than
    # failing the poll: this line is advisory, the run view is not.
    terminal_run = bool(views) and not any(
        v["verdict"] not in detach.TERMINAL_VERDICTS for v in views
    )
    # plans/review-commits.md §2.3/§2.8: a detached apply prints its
    # `[COMMIT_FIXES]` block into the worker's log, which no host reads, so a
    # terminal poll whose state holds the apply guard renders the block from
    # that saved decision and carries `commit_fixes` on its result line.
    # A phase that ran in the foreground has no run record (`no_run`): on
    # Claude Code the review core runs detached and the apply core in the
    # foreground, so the hand-typed `status <pinned>` is always that mixed
    # shape. Nothing is still writing either way, so the block is rendered
    # when every listed run is settled, not only when every one is terminal.
    commit_fixes_settled = bool(views) and not any(
        v["verdict"] not in detach.TERMINAL_VERDICTS
        and v["verdict"] != detach.VERDICT_NO_RUN
        for v in views
    )
    commit_fixes = _commit_fixes_view(plan_path, args, views, commit_fixes_settled)
    if commit_fixes is not None:
        record_commit_fixes_result(commit_fixes[1])
    workflow_trailer: List[str] = []
    terminal_notice: Optional[str] = None
    terminal_workflow: Optional[Dict[str, Any]] = None
    if args.view == VIEW_RUN and terminal_run:
        try:
            terminal_workflow = _workflow_payload(plan_path, host_id=_reader_host(args))
        except Exception:
            terminal_workflow = None
        if terminal_workflow:
            close_note = manual_close_note(
                terminal_workflow, _plan_spelling(args, views, plan_path),
                _reader_host(args), _recorded_route(args, views, plan_path),
            )
            trailer = _workflow_trailer_lines(
                terminal_workflow, prefix="",
                close_note=close_note,
                # Fix round 26 (live run 11, Codex stop 01b): a run that
                # stopped or failed has no next phase, and the hosts relayed
                # "suggested next: implement (review-tasks /
                # apply-task-suggestions optional, not run)" beside the
                # stop's own ways forward. The line is left out of a
                # non-zero poll's text and notice alike.
                suggested=exit_code == EXIT_OK,
            )
            # The merge of fix round 28: a stop whose section leads with
            # the resume recording the manual tasks done (implement's
            # manual-task gate) gives that command once, there; the notice,
            # and the text a tool route reads beside the section, name the
            # tasks and leave it out. A shell's text keeps every line.
            from .next_phase import gate_resume_closes_the_manual_tasks

            told = trailer
            if (close_note and exit_code != EXIT_OK
                    and gate_resume_closes_the_manual_tasks(
                        (terminal_workflow.get("phases") or {}).get("implement") or {})):
                told = _workflow_trailer_lines(
                    terminal_workflow, prefix="", suggested=False)
            if trailer:
                workflow_trailer = [
                    f"workflow {line}" for line in (
                        told if _read_by_a_tool_route(args) else trailer)]
                terminal_notice = join_clauses(told)

    # Fix round 14: a native-leg implement leaves no run record and no
    # report, so its tasks are read back from state.json (`--run-id` and
    # `--question` name a run, which this is not).
    implement_tasks = None
    if (not args.run_id and not args.question
            and _resolve_phase(args.phase) in (None, _IMPLEMENT_PHASE)):
        try:
            implement_tasks = state_implement_view(plan_path, views)
        except Exception:  # noqa: BLE001 - advisory: the run view is not
            implement_tasks = None
    # Fix round 18: and the apply phases the same native host ran.
    apply_tasks: List[Dict[str, Any]] = []
    if not args.run_id and not args.question:
        try:
            apply_tasks = state_apply_views(
                plan_path, views, workflow or terminal_workflow,
                only=_resolve_phase(args.phase), host_id=_reader_host(args),
            )
        except Exception:  # noqa: BLE001 - advisory: the run view is not
            apply_tasks = []
    for phase, record in superseded.items():
        entry = implement_tasks if phase == _IMPLEMENT_PHASE else next(
            (item for item in apply_tasks if item.get("phase") == phase), None)
        if isinstance(entry, dict):
            entry["earlier_run"] = record

    # plans/next-phase-command.md §2.2(1): a TERMINAL poll pinned to exactly one
    # run that exits 0 — a worker that ended 0 or 2 — carries the next phase as
    # `user_next_step`, beside F7's notice but without F7's view guard: the key
    # is machine-readable, and `--view all`'s result line carries no parsed
    # workflow step either (`--view workflow` returned above). The block follows
    # the text on stdout, or goes to stderr under `--json`, whose payload stays
    # exactly what it was. Never on exit 2 (still moving, or nothing recorded)
    # or 3 (failed/aborted). Advisory: a failed read or builder costs one
    # stderr line and nothing else. Built before the text and printed after
    # it (fix round 26), so the text can leave out what the step says.
    step = None
    step_block = io.StringIO()
    if (
        exit_code == EXIT_OK
        and terminal_run
        and len(views) == 1
        and (args.phase or args.question or args.run_id)
    ):
        step = _emit_user_next_step(
            plan_path, args, views[0], workflow=terminal_workflow,
            stream=step_block,
        )
        if (step is not None and terminal_workflow and workflow_trailer
                and _read_by_a_tool_route(args)):
            # Fix round 26 (live run 11, Codex 08: "No later phase waits for
            # it" beside the copied section): a tool route hands this text to
            # its model as `output`, beside `user_next_step`, so the trailer
            # there leaves out what the step's markdown says, as the notice
            # does. A shell's text view keeps every line.
            workflow_trailer = [
                f"workflow {line}" for line in _workflow_trailer_lines(
                    terminal_workflow, prefix="", suggested=False, carried=step,
                    close_note=manual_close_note(
                        terminal_workflow, _plan_spelling(args, views, plan_path),
                        _reader_host(args), _recorded_route(args, views, plan_path),
                    ),
                )
            ]

    if args.json:
        payload: Dict[str, Any] = {"runs": views}
        if args.view == VIEW_ALL:
            payload = {"workflow": workflow, "runs": views}
        if implement_tasks is not None:
            payload["implement_tasks"] = implement_tasks
        if apply_tasks:
            payload["apply_phases"] = apply_tasks
        if implement_tally is not None:
            payload["implement_tally"] = implement_tally
        # Plan §7.4a2/b: what discovery skipped, only when there is something
        # to say, so a plan with none keeps today's payload byte for byte.
        if discovery.get("ignored_dirs"):
            payload["ignored_dirs"] = list(discovery["ignored_dirs"])
        if discovery.get("copies"):
            payload["copied_runs"] = list(discovery["copies"])
        if commit_fixes is not None:
            payload["commit_fixes"] = commit_fixes[1]
        print(json.dumps(payload, indent=2, default=str))
    else:
        lines: List[str] = []
        if args.view == VIEW_ALL and workflow is not None:
            lines += render_workflow_text(
                workflow,
                close_note=manual_close_note(
                    workflow, _plan_spelling(args, views, plan_path),
                    _reader_host(args), _recorded_route(args, views, plan_path),
                ),
            )
            lines.append("")
        spell = user_speller(
            _reader_host(args), _plan_spelling(args, views, plan_path),
            plan_path=plan_path)
        lines += render_run_text(
            views, plan_path=plan_path, workflow=workflow,
            scope=_scope_label(args), resume_workflow=terminal_workflow,
            implement_tally=implement_tally,
            state_block=implement_tasks is not None or bool(apply_tasks),
            spell=spell,
        )
        # The phases a native host ran (no run record), in workflow order.
        native: List[Tuple[str, List[str]]] = [
            (entry["phase"], render_state_apply_lines(
                entry, resume=native_resume_command(entry["phase"], plan_path, spell)))
            for entry in apply_tasks
        ]
        if implement_tasks is not None:
            native.append((_IMPLEMENT_PHASE, render_state_implement_lines(
                implement_tasks,
                resume=native_resume_command(
                    _IMPLEMENT_PHASE, plan_path, spell,
                    flags=implement_tasks.get("resume_flags") or ()),
                answers=native_stop_answer_commands(implement_tasks, plan_path, spell))))
        for _phase, block in sorted(
                native, key=lambda item: NATIVE_PHASE_ORDER.index(item[0])):
            lines += block
        # Plan §7.4a2: after the phase views, never silently dropped.
        lines += _ignored_text(
            discovery.get("ignored_dirs") or [], discovery.get("copies") or []
        )
        runner = render_runner_text(
            plan_path, host_id=getattr(args, "host", None), views=views
        )
        if runner:
            lines.append("")
            lines += runner
        if commit_fixes is not None:
            lines.append("")
            lines += commit_fixes[0]
        if workflow_trailer:
            lines.append("")
            lines += workflow_trailer
        print("\n".join(lines))

    if step_block.getvalue():
        block_stream = sys.stderr if args.json else sys.stdout
        block_stream.write(step_block.getvalue())
        block_stream.flush()
    if step is not None and terminal_workflow:
        # Fix round 22 (live run 9, Codex 07, OpenCode 06-08): the
        # notice said how to close the manual tasks, command and all,
        # beside `user_next_step`, which says it with the command fenced;
        # the hosts relayed both, the command folded into prose. The
        # notice keeps naming the tasks and leaves the rest to the step.
        # Fix round 24 (live run 10, OpenCode 03, Codex 01): so with the
        # `suggested next` line, which the hosts relayed beside the
        # step's markdown and reordered the step after.
        # Fix round 26 (live run 11: Codex 04/06/08, OpenCode 03-08):
        # and with what the step's `markdown` says itself, the optional
        # entry's why and the manual tasks, which the hosts pasted above
        # the copied section. The text view a person reads keeps them.
        terminal_notice = join_clauses(_workflow_trailer_lines(
            terminal_workflow, prefix="", suggested=False,
            carried=step)) or None

    # D2 (live test 2026-10-26): a composite's steps ran in its process, so
    # what each recorded on the result line (its notice, counts, validation
    # context) and the line's artifacts reach its run dir only as its report
    # recorded them, under this run's id (`detach.recorded_step_results`). A
    # run that never got that far is read as before, from its own dir alone.
    carried = (
        detach.recorded_step_results(views[0])
        if terminal_run and len(views) == 1
        and (args.phase or args.question or args.run_id)
        else {}
    )
    steps = [step for step in carried.get("steps") or [] if isinstance(step, dict)]
    # Plan §2.4: a `mode: truncated` validation source sets the notice on any
    # terminal poll (every view, not only `--view run`); it qualifies the
    # verdicts the workflow step acts on, so it comes first and joins the
    # workflow trailer in ONE record. Either part alone is recorded unchanged;
    # a `mode: path` source sets none.
    truncation_notice = (
        _validation_context_notice(views) if terminal_run else None
    )
    # Fix round 14: a terminal write run's own not-clean parts, first among
    # the workflow's, since they qualify the run the poll is about; then a
    # finished run's own notes (a consistency warning, the items left
    # unapplied) — the log was the only place that carried them.
    write_parts = _write_result_notice_parts(views) if terminal_run else []
    note_parts = [
        note for view in views for note in _run_notes(view)
    ] if terminal_run else []
    # Then a composite's steps' own notices, in step order, each as its phase
    # recorded and bounded it: one clip over the lot would cut the last
    # step's (a `full` run's implement and apply-code-fixes each carry up to
    # the 1200 characters one phase's notice is sized to). A review's
    # truncation sentence is in its own.
    step_parts = [str(step["notice"]) for step in steps if step.get("notice")]
    if stop_error:
        # Fix round 26 (live run 11, Codex stop 01b): a stop's own line, the
        # result's `error` the hosts relay whole, already ends with what ran
        # the repository's tests; the notice said it again and the host
        # restated it. A part the error carries word for word is left out.
        said = plain_line(clip(stop_error, ERROR_MAX_CHARS))
        write_parts = [part for part in write_parts if plain_line(part) not in said]
        note_parts = [part for part in note_parts if plain_line(part) not in said]
    # Fix round 28 (live run 12 #7): one join for every clause, so a part
    # gives up its closing stop to the separator ("….; …" no more) and keeps
    # it where it ends the notice.
    write_notice = clip(join_clauses(write_parts), 1200) or None
    notes_notice = join_clauses(note_parts)
    # The steps' clause by clause, each said once (Fable review of D2): a
    # `full` run's implement and apply-code-fixes word "Nothing ran this
    # repository's tests: …" alike, and a stop's error may end with it.
    steps_notice = ""
    for part in step_parts:
        earlier = join_clauses((
            clip(stop_error, ERROR_MAX_CHARS) if stop_error else None,
            write_notice, notes_notice, steps_notice))
        steps_notice = join_clauses((steps_notice, drop_said_clauses(part, earlier)))
    combined_notice = join_clauses((
        truncation_notice, write_notice, notes_notice, steps_notice,
        terminal_notice))
    if combined_notice:
        record_notice(combined_notice)

    for path in carried.get("artifacts") or []:
        if isinstance(path, str):
            record_artifact(path)
    for view in views:
        for path in view["output_files"].values():
            if isinstance(path, str):
                record_artifact(path)
        if view["run"].get("log_path"):
            record_artifact(view["run"]["log_path"])
    # The worker recorded this on its own result line, which a detached caller
    # never saw; a poll is the route it reaches the host by, so the poll's line
    # carries it too. One field, so the first view holding one wins — the text
    # above already rendered every phase's.
    recommended = next(
        (v["consolidation_recommended"] for v in views
         if v.get("consolidation_recommended")),
        None,
    )
    if recommended:
        record_consolidation_recommended(recommended)
    # Plan §2.4 step 3: one field, so the view whose object has the worst
    # top-level `mode` wins, first in discovery order on a tie (its `phase`
    # says which); the text above rendered every phase's line.
    validation_context = pick_worst(
        [v.get("validation_context") for v in [*views, *steps]]
    )
    if validation_context:
        record_validation_context(validation_context)
    # §6 T6.1: the worker's verdict counts, re-recorded for the same reason as
    # `consolidation_recommended` above — a detached caller never saw the
    # worker's own result line. Recorded only when the caller pinned exactly
    # one run — the condition `record_mode_phase` uses above: an unselected
    # `--view run` lists every phase alphabetically while `mode`/`phase` stay
    # `status`/null, so the first view's counts would read as whichever run the
    # host was watching. A composite's are its last review's, the counts its
    # worker's line kept (D2).
    counts = (
        next((v["validation_counts"] for v in reversed([*views, *steps])
              if v.get("validation_counts")), None)
        if len(views) == 1 and (args.phase or args.question or args.run_id)
        else None
    )
    if counts:
        record_validation_counts(counts)
    # plans/ask-answer-recovery-and-false-success.md D7.2: a finished ask's
    # answer counts by origin, re-recorded under the same pinned-run rule and
    # for the same reason — a detached ask's own result line never reached the
    # host, and its all-fallback `[WARN]` is prose the poll does not relay.
    # Only an ask dir carries the key, so every other view's line is unchanged.
    origins = (
        views[0].get("answer_origins")
        if len(views) == 1 and (args.phase or args.question or args.run_id)
        else None
    )
    if isinstance(origins, dict):
        record_answer_origins(origins)
    if exit_code == EXIT_NOTHING_TO_DO and views:
        # `views[0]` is `discover_phase_dirs`' alphabetical order, not "the run
        # that made the exit code 2" — with several phases listed, a finished
        # one can sort first while a different one is the live reason for the
        # exit code (F3, 2026-09-16: `apply-suggestions` sorted ahead of the
        # still-running `generate-tasks`, and the poll command handed back
        # polled the finished run straight back to exit 0). Pick the first
        # non-terminal view; only when none is live does the finished one
        # answer, which is the genuine "nothing to do" case.
        # F1, 2026-09-17: "live" is non-terminal *and* actually holding a run.
        # `no_run` is non-terminal only because there is nothing to be terminal
        # about — a phase run in the foreground (every Claude Code host phase)
        # leaves a checkpoint with no `run` record — and counting it live told
        # a host `state: running` about a phase nothing ever launched, and
        # handed back a poll command for it that can never leave exit 2.
        live_views = [
            v for v in views
            if v["verdict"] not in detach.TERMINAL_VERDICTS
            and v["verdict"] != detach.VERDICT_NO_RUN
        ]
        # F2, 2026-09-21: the fallback was a bare `views[0]`, so on a plan whose
        # every phase ran in the foreground it handed back a poll of a `no_run`
        # view — F1's rule broken through the back door, because the guard above
        # only ever chose *between* views. It used to break cheaply
        # (`status_command_for` returned an instant poll); now that the command
        # carries `--wait`, following it spends the whole clamped `poll_s` and
        # still returns exit 2 with the identical `next`, forever. So the
        # fallback skips `no_run` as well, leaving the already-finished run this
        # branch means by "nothing to do" — whose poll exits 0 or 3 and ends the
        # loop. When that leaves nothing at all, *no* `next` is handed back: a
        # plan with no run recorded anywhere has nothing to poll, and a host
        # following `next` mechanically is owed a command that can change its
        # own answer.
        candidates = live_views or [
            v for v in views if v["verdict"] != detach.VERDICT_NO_RUN
        ]
        if candidates:
            first = candidates[0]
            record_next(
                detach.status_command_for(
                    str(plan_path),
                    phase=first.get("phase"),
                    run_id=str(first["run"].get("run_id") or "") or None,
                    # The run's own host, so the poll this hands back reports
                    # the run's runner rather than the reader's (F6,
                    # 2026-09-16).
                    host=str(first["run"].get("host") or "") or None,
                )
            )
        # The exit code stays 2 — the poll loops key off it, never off this
        # word — but "nothing-to-do" is a false alarm when the reason is a run
        # still in flight rather than an already-finished or unrecorded one
        # (F11, 2026-09-16: the payload said `nothing-to-do` on the same
        # screen whose text said `generate-tasks run … running`).
        if live_views:
            # `died` only when every live view is one: a plan holding a dead run
            # beside a genuinely running one is, on the whole, still running.
            record_state(
                STATE_DIED if all(_died(v) for v in live_views) else STATE_RUNNING
            )
    if getattr(args, "exit_zero", False) and exit_code in (
        EXIT_NOTHING_TO_DO, EXIT_NEEDS_HUMAN,
    ):
        # Only the verdict's code moves: the word it means stays on the result
        # line, and everything above (`next`, the notice, `user_next_step`'s
        # exit-0 gate) was decided on the real verdict.
        keep_state_word(exit_code)
        return EXIT_OK
    return exit_code


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
    from . import host_capabilities, next_phase
    from .cli_common import _modes

    run = view.get("run") or {}
    finished_mode = str(run.get("mode") or view.get("phase") or "") or None
    mode = _modes().resolve(finished_mode) if finished_mode else None
    if mode is None or not (mode.is_workflow_phase or mode.is_composite):
        return None  # an ask, or no mode on record: no phase finished, no answer
    plan_arg = next_phase.recorded_plan_spelling(
        run.get("plan_arg"), str(plan_path)
    ) or str(plan_path)
    try:
        if workflow is None:
            workflow = _workflow_payload(plan_path, host_id=_reader_host(args))
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
        recorded_route=_run_route(view, _reader_host(args)),
    )


def _read_by_a_tool_route(args: argparse.Namespace) -> bool:
    """Whether a tool server is the reader of this poll's text: the route
    this process spells commands for (``next_phase.resolve_route``, its one
    reader, from the environment the servers set; never a run's recorded
    route, which a shell reads too) is a tool route (fix round 26)."""
    import io

    from . import next_phase
    from .cli_common import _modes

    try:
        route = next_phase.resolve_route(_reader_host(args), stderr=io.StringIO())
    except Exception:  # noqa: BLE001 - advisory: the text stays whole
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
        from . import host_capabilities as caps

        if host_id:
            ceiling = caps.timeout_ceiling_s(host_id)
            return (host_id, ceiling) if ceiling else None
        return caps.tightest_timeout_ceiling()
    except Exception:
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
    from . import host_capabilities as caps

    explicit = getattr(args, "host", None)
    if not explicit and not os.environ.get(caps.HOST_ENV):
        return None
    return caps.resolve_host_id(explicit=explicit)


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
    clamped = max(float(cap_s) - WAIT_CAP_MARGIN_S, WAIT_POLL_INTERVAL_S)
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
        str(view.get("phase_dir") or ""): _terminal_fingerprints(view)
        for view in views
    }
    deadline = time.time() + max(args.timeout, 0.0)

    def _live(view: Dict[str, Any]) -> bool:
        verdict = view["verdict"]
        if (verdict not in detach.TERMINAL_VERDICTS
                and verdict != detach.VERDICT_NO_RUN):
            return True
        if _names_this_run(view, getattr(args, "run_id", None)):
            return False
        if superseded_by_native(plan_path, view) is not None:
            # Fix round 26: an executor checkpoint the native leg went on
            # from is not a run anyone is waiting for.
            return False
        return _checkpoint_in_flight(view)

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
        time.sleep(min(WAIT_POLL_INTERVAL_S, max(deadline - time.time(), 0.05)))
        views = _collect(plan_path, args)
    _attach_finished_during_wait(baseline, views)
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
        print(f"Nothing to abort: no run recorded for this {_document_word(plan_path)}.")
        return EXIT_NOTHING_TO_DO
    live = [v for v in views if v["verdict"] not in detach.TERMINAL_VERDICTS]
    if len(live) > 1 and not _abort_selector_given(args):
        print(
            f"{len(live)} live runs under this {_document_word(plan_path)} and no "
            "selector: naming which "
            "one to abort is the caller's job. Candidates:"
        )
        for view in live:
            name = os.path.basename(view["phase_dir"])
            run_id = str(view["run"].get("run_id") or "")
            head = f"  {name}"
            if run_id:
                head += f"  run {run_id[:8]}"
            print(f"{head}  {_verdict_text(view)}")
            if view.get("question"):
                print(f"      question: {view['question']}")
            print(f"      abort it with: {_abort_command(plan_path, view)}")
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
    for directory in discover_phase_dirs(plan_path, phase=phase):
        before = status_file.read_run(str(directory)).get("state")
        view = detach.classify_run(str(directory), close_out=True)
        after = view["run"].get("state")
        if before != after:
            closed.append(f"{os.path.basename(str(directory))}: {before} -> {after}")
    if closed:
        print("swept:")
        for line in closed:
            print(f"  {line}")
    else:
        print("swept: nothing to close out")
    return EXIT_OK


if __name__ == "__main__":  # pragma: no cover - direct invocation
    sys.exit(main(sys.argv[1:]))
