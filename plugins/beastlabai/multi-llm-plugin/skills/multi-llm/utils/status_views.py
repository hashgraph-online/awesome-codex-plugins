"""What ``status`` knows about a run view before it says anything.

Discovery and selection of the phase dirs under a plan, the predicates over
one ``detach.classify_run`` view (terminal, stopped for the user, died, live),
the exit code a list of views answers with, and the workflow read
(:func:`_workflow_payload`). The lowest of the ``status`` modules: the others
(``status_commands``, ``status_native``, ``status_text``) and ``run_status``
read from it, and it reads none of them.

**The workflow read is one seam.** Every reader calls
``status_views._workflow_payload`` on this module at each call, never a copy,
so a test that patches it here reaches all of them
(docs/development/status.md#how-status-is-built).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import detach, process_control, status_file
from .advisory import note_swallowed
from .cli_common import EXIT_NEEDS_HUMAN, EXIT_NOTHING_TO_DO, EXIT_OK
from .progress_tracker import STATE_FAILED
from .task_ledger import mirror_ids
from .output_handler import (
    PHASE_DIR_NAMES,
    PHASE_DIRECTORIES,
    output_dir_path,
    phase_dir_path,
    slugify_question,
)


#: ``progress.step``'s terminal values. ``progress_tracker.PhaseProgress``
#: owns the first pair and names them in its own docstring: ``complete``, and
#: the host-driven ``validation_pending`` early return where the process exits
#: and the agent's own subagents take over. ``stopped`` is the write
#: scheduler's mirror on a stop (``WriteReports.mirror_status``), which a foreground
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


#: The phases whose foreground run holds its phase dir's ``.lock`` from before
#: its first checkpoint write to its exit: the review fan-outs (``detach.PhaseRun``)
#: and ask (its question lock). Their checkpoint read as in flight under a
#: free lock, with no ``run`` record, was left by a run that is gone.
FOREGROUND_LOCKED_PHASES = frozenset({"review-plan", "review-tasks", "code-review", "ask"})

#: How such a run heads its block (:func:`_foreground_run_gone`).
ENDED_IN_FOREGROUND = "ended in foreground without a final state"


def _foreground_run_gone(view: Dict[str, Any]) -> bool:
    """Whether a foreground checkpoint that reads in flight
    (:func:`_checkpoint_in_flight`) was left by a run that has ended: no
    ``run`` record, a phase of :data:`FOREGROUND_LOCKED_PHASES`, and nobody
    holds the phase lock (``classify_run``'s ``lock_held``, probed). A fan-out
    whose every model failed exits 3 with ``state: models_running`` still on
    disk; this is what tells it from one still running. Text only: the
    verdict stays ``no_run`` (docs/development/status.md)."""
    return (
        view.get("verdict") == detach.VERDICT_NO_RUN
        and view.get("phase") in FOREGROUND_LOCKED_PHASES
        and view.get("lock_held") is False
        and _checkpoint_in_flight(view)
    )


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

    *host_id* is this poll's ``--host`` (``run_status._reader_host``): the early
    sandbox warning resolves the subagent runner for it, and the servers
    declare their host only there (adversarial review, 2026-10-02).
    """
    # Imported here to keep run_status, which loads this module, light.
    from .state_manager import StateManager

    # Imported here to keep run_status, which loads this module, light.
    import check_workflow_prerequisites as prereq  # type: ignore

    # A poll: read-only, so it never rewrites the file a run is writing.
    state = StateManager(plan_path, read_only=True)
    return prereq.get_workflow_status(
        state, plan_path, output_dir_path(plan_path), host_id=host_id,
    )


def _document_word(plan_path: Path) -> str:
    """``commit brief`` when *plan_path*'s ``state.json`` records a
    ``commit_range``, else ``plan``: what a line ``status`` prints calls the
    document it reads (plans/review-commits.md §2.8, "'Commit brief', never
    'plan'"), through the one owner of the word, ``commit_paths.document_label``.
    Read-only; an unreadable state is a plan."""
    try:
        # Imported here to keep run_status, which loads this module, light.
        from .commit_paths import document_label, read_commit_range

        return document_label({"commit_range": read_commit_range(plan_path)})
    except Exception as exc:  # noqa: BLE001 - advisory: the plan's word stands
        note_swallowed("status: document word", exc)
        return "plan"


def _document_file_label(plan_path: Path) -> str:
    """``Plan file`` as today, or ``Commit brief`` (:func:`_document_word`)."""
    word = _document_word(plan_path)
    return "Plan file" if word == "plan" else word.capitalize()


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
    except Exception as exc:  # advisory text only; never fail the poll over it
        note_swallowed("status: failed model specs", exc)
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


def _a_dispatch_failed(view: Dict[str, Any]) -> bool:
    """Whether something the run dispatched failed: a write task whose
    runner ran and failed (the write mirror's ``runner_failed_task_ids``;
    a mirror written before fix round 23 has only ``failed_task_ids``, read
    as is by ``task_ledger.mirror_ids``), a read task, or a fan-out model."""
    progress = view.get("progress") if isinstance(view.get("progress"), dict) else {}
    write = progress.get("write_subagents")
    if isinstance(write, dict):
        ran = write.get("runner_failed_task_ids")
        if ran if isinstance(ran, list) else mirror_ids(write, "failed_task_ids"):
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


#: The close-out's own word for a needs-human exit with no reason recorded
#: (`detach.RunHandle.finish`): not a "last line" worth relaying.
GENERIC_NEEDS_HUMAN_ERROR = "needs_human (exit 3)"


#: The phase whose tasks :func:`state_implement_view` reads back from
#: ``state.json``, and the report whose absence marks a run the host drove.
_IMPLEMENT_PHASE = "implement"


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
