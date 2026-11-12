"""The run view and workflow section as ``status`` prints them.

:func:`render_run_text` (the head line, state lines, progress, the per-model
table, failure and resume blocks), the workflow section and its trailer
(:func:`render_workflow_text`, :func:`_workflow_trailer_lines`), the progress
lines a pinned poll's result carries (:func:`_progress_lines`), the executor
mirrors (:func:`_mirror_text`) and the notices a terminal poll records. Reads
``status_views``, ``status_commands`` and ``status_native``
(docs/development/status.md#status-views-and-run-selection).
"""

from __future__ import annotations

import io
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from . import detach, host_capabilities, metrics, run_record, status_file, task_ledger
from .advisory import note_swallowed
from .task_ledger import (
    MIRROR_ACCEPTED_LABELS as _MIRROR_ACCEPTED_LABELS,
    MIRROR_SKIP_LABELS as _MIRROR_SKIP_LABELS,
    bucket_clauses as _bucket_clauses,
    mirror_ids as _mirror_ids,
    ACCEPTED_AFTER_FAILING_LABEL,
    ACCEPTED_WITH_FINDINGS_LABEL,
    COMPLETED_BY_HAND_LABEL,
    KEPT_WITH_FINDINGS_LABEL,
)
from .cli_common import dispatcher_command
from .progress_tracker import (
    STATE_DONE,
    STATE_FAILED,
    STATE_QUEUED,
    STATE_RETRYING,
    TERMINAL_STATES,
    awaits_first_dispatch,
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
from .text_clip import clip, join_clauses, plain_line
from .validation_context import validation_context_notice, validation_context_text
from .status_views import (
    ENDED_IN_FOREGROUND,
    STOPPED_IN_FOREGROUND,
    STOPPED_STEP,
    _a_dispatch_failed,
    _checkpoint_in_flight,
    _died,
    _foreground_run_gone,
    _document_word,
    _failed_model_specs,
    _is_executor_implement_view,
    _result_state,
    _run_is_live,
    _stopped_for_the_user,
    _view_dir_name,
)
from .status_commands import (
    Speller,
    _abort_command,
    _rerun_command,
    _resume_lines,
    _stale_review_of,
    _view_speller,
    _write_mirror_as_counts,
)
from .status_native import (
    _accepted_reruns_by_task,
    accepted_rerun_clauses,
    implement_tally_text,
    not_applied_item_clauses,
    repeated_check_clauses,
)


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


def manual_close_note(
    payload: Dict[str, Any], plan_spelling: str, host_id: Optional[str],
    recorded_route: Optional[str] = None,
) -> Optional[str]:
    """How to record the deferred manual tasks done, in *host_id*'s spelling.

    ``next_phase.manual_close_note`` over the workflow payload's
    ``phases.implement.manual_tasks``. ``None`` when nothing is
    owed or the host has no command template for this route.
    *recorded_route* is the route the plan's run was started on
    (:func:`_recorded_route`), for a reader that names none.
    """

    # Imported here to keep run_status, which loads this module, light.
    from . import next_phase

    # The manual tasks themselves, never a code task skipped with one
    # (`next_phase.manual_close_ids`); while a manual-task gate
    # holds, the gate's alone (`manual_note_ids`).
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
    except Exception as exc:  # noqa: BLE001 - advisory: the list still stands
        note_swallowed("status: manual close note", exc)
        return None
    return next_phase.manual_close_note(
        next_phase.close_command(template, plan_spelling, ids), len(ids),
        # Never "No later phase waits" beside code tasks that do.
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
    manual tasks, the manual-tasks line.
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
        # `next: null` beside it, asserted exactly that. Name
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
        # Imported here to keep run_status, which loads this module, light.
        from .next_phase import gate_resume_suggested

        gate = gate_resume_suggested(payload)
        if gate:
            # Implement finished with
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
    # owed read as done.
    manual = (payload.get("phases", {}).get("implement") or {}).get("manual_tasks")
    manual_line: Optional[str] = None
    if isinstance(manual, list) and manual:
        # Imported here to keep run_status, which loads this module, light.
        from .next_phase import ManualTask

        # One rendering with the `[MANUAL_TASK]` line: a task skipped with a
        # manual one says what it waits on.
        named = "; ".join(
            ManualTask(
                str(entry["id"]), entry.get("title") or None,
                str(entry["waits_on"]) if entry.get("waits_on") else None,
                # A later manual task names the code it comes after.
                tuple(str(t) for t in entry.get("after") or ()
                      if isinstance(entry.get("after"), list)),
            ).line()
            for entry in manual
            if isinstance(entry, dict) and entry.get("id")
        )
        if named:
            # Appended last, below: its note ends with the command that
            # records the tasks done, and a joined `notice` must not run on
            # past it.
            manual_line = (
                f"{prefix}manual tasks left for you: {named}"
                + (f". {close_note}" if close_note else "")
            )
    # The implement check tasks that ran and reported problems
    # (`phases.implement.check_findings`, from state.json; racing re-run 4,
    # 2026-10-05). Shown while implement is unfinished — its findings are
    # newer than any review on record — and, once it has completed, until a
    # review-code that judged it has completed or the review was skipped.
    # Keyed on review-code alone, an
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
    # (`phases.implement.batch_check_findings`), shown by the
    # same rule as the check findings above.
    failing = (phases.get("implement") or {}).get("batch_check_findings")
    if isinstance(failing, list) and failing and not (implement_done and review_settled):
        # The task's own report, quoted.
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
    # accepted for a check (`phases.implement.batch_check_accepted`), by the same rule:
    # not a failure, but on record.
    accepted_reruns = _accepted_reruns_by_task(
        (phases.get("implement") or {}).get("batch_check_accepted"))
    if accepted_reruns and not (implement_done and review_settled):
        lines += [
            f"{prefix}{clause} — not counted as a failure (see implement/summary.md)"
            for clause in accepted_rerun_clauses(accepted_reruns)
        ]
    # And those whose own check reported only what a check
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
    # spelling; `None` keeps the dispatcher command.
    # The workflow payload the resume block may consult without rendering the
    # workflow lines above it (`--view run`'s terminal read); see `_resume_lines`.
    resume_workflow = workflow if workflow is not None else resume_workflow
    lines = ["runs ({phase}/.status.json) — is a launched run still alive:"]
    if not views:
        if not state_block:
            # A native implement read back from state.json follows instead
            # (`render_state_implement_lines`).
            lines.append(
                f"  no run recorded for {scope or 'this ' + _document_word(plan_path)}")
        return lines
    outer_spell = spell
    for view in views:
        run = view["run"]
        # Each run's commands in the route that started it.
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
        if detach.cleanup_incomplete(run):
            cleanup = run["cleanup"]
            lines.append(
                f"      cleanup:        {str(cleanup.get('state')).upper()} — not every "
                "process the run left could be confirmed stopped (kill verdict "
                f"{cleanup.get('verdict') or 'unknown'}, process group "
                f"{cleanup.get('pgid') or '?'}, checked {cleanup.get('checked_at') or '?'})"
            )
            lines.append(f"      try it again with: {_abort_command(plan_path, view)}")
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
                # The line above counts this run's batches; this
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


def _run_state_text(view: Dict[str, Any]) -> str:
    """``run.state``, annotated when the run's result was ``partial``.

    ``run.state`` keeps its process meaning (``done``); the note says what the
    exit code could not: ``done (partial — failed: codex:gpt-6-astra:xhigh)``.
    """
    word = (view.get("run") or {}).get("state") or "(none)"
    result = _result_state(view)
    if result is None:
        if _stopped_for_the_user(view):
            # What the record means is said. "nothing crashed" only when nothing
            # it ran failed. The text no
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
#: record says ``failed``.
STOPPED_FOR_THE_USER_VERDICT = "stopped and needs you (exit 3)"
#: The ``run.state:`` line of such a run (live run 11 #6:
#: "failed (exit 3: …)" under the head above). The record keeps ``failed``.
STOPPED_RUN_STATE_WORD = "stopped"
STOPPED_FOR_THE_USER_GLOSS = "exit 3: the run needs you"
#: Added to the gloss only when no runner and no model of the run failed
#: (:func:`_a_dispatch_failed`): a stop on a refusal, a check's
#: findings or an unanswered manual task.
NOTHING_CRASHED = "nothing crashed"


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
            # The write mirror's stop,
            # which read "finished in foreground" while the same ending
            # detached heads "stopped and needs you (exit 3)".
            return STOPPED_IN_FOREGROUND
        if progress:
            tense = "running" if _checkpoint_in_flight(view) else "finished"
            head = f"{tense} in foreground"
            if _foreground_run_gone(view):
                # Its checkpoint still reads in flight, but the lock its run
                # held for its whole life is free: that run has ended.
                head = ENDED_IN_FOREGROUND
            total = progress.get("models_total")
            if isinstance(total, int) and not isinstance(total, bool) and total:
                done = progress.get("models_done", 0)
                return f"{head} ({done}/{total} models, no detached run record)"
            return f"{head} (no detached run record)"
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
    """The phase's ``validation_context`` line, or ``None``.

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

    A code batch whose own check failed after its edits
    (``write_subagents.tasks[].batch_check_findings``) and the line saying
    nothing ran the repository's tests (``write_subagents.unverified``) —
    what the worker recorded on its own result line, which a detached caller
    never sees. Read from the run's own mirror, so it describes that run.
    """
    return clip(join_clauses(_write_result_notice_parts(views)), 1200) or None


def _write_result_notice_parts(views: Sequence[Dict[str, Any]]) -> List[str]:
    """:func:`_write_result_notice`'s parts, unjoined (a stop's
    poll leaves out a part its `error` already says)."""
    # Imported here to keep run_status, which loads this module, light.
    from .check_records import batch_check_summary
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
        # apply-task-suggestions split a task.
        parts.append(f"generated {generated} task{'' if generated == 1 else 's'}")
    elif progress.get("tasks_total"):
        parts.append(f"tasks {progress.get('tasks_done', 0)}/{progress['tasks_total']}")
    if progress.get("batches_total"):
        parts.append(
            f"batch {progress.get('batch_index', 0)}/{progress['batches_total']}"
        )
    if progress.get("failed_task_ids"):
        parts.append(f"failed {', '.join(map(str, progress['failed_task_ids']))}")
    # The executor's mirrors (`task_batch._mirror_status` under
    # `subagents`, `write_reports.WriteReports.mirror_status` under
    # `write_subagents`) are the only progress a dispatch-only phase such as
    # `generate-tasks` records — it never calls `report_progress(step=…)` before
    # the end — so a line that read only the step keys printed "(none recorded)"
    # beside a mirror that said `ok: 1`. Measured 2026-09-14.
    for key in ("subagents", "write_subagents"):
        parts.extend(_mirror_text(key, progress.get(key)))
    # D6 override: a detached fan-out records the slots it ran
    # without the runner's own sandbox under `progress.sandbox_bypassed`, and
    # a host polling `status` is told so here — the `[SANDBOX_BYPASSED]` line
    # is in a log a detached caller never reads.
    bypassed = progress.get("sandbox_bypassed")
    if isinstance(bypassed, list) and bypassed:
        parts.append(f"unsandboxed {', '.join(map(str, bypassed))}")
    # Landlock rung: a slot on a *contained* fallback rung is
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


#: The rung ids of an **incidental** grade. A closed set spelled here — `status` reads
#: recorded data and
#: imports no provider code — whose slots render as `stray-writes-only <rung>`:
#: the plugin's Landlock jail stops stray writes, not the model, so the one
#: word a real OS boundary earns (`sandbox-fallback`) is never its word. The
#: clause names no phase, so a read-only slot and a write dispatch share it.
INCIDENTAL_RUNG_IDS = frozenset({"plugin-landlock"})


def _fallback_clause_head(rung: str) -> str:
    """``stray-writes-only`` for an incidental rung, ``sandbox-fallback`` for a
    contained one (the legacy ``landlock`` renders exactly as before)."""
    return "stray-writes-only" if rung in INCIDENTAL_RUNG_IDS else "sandbox-fallback"


#: A jailed slot's recorded failure reason and the key carrying its denied path. The
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
    drift this file keeps testing against.
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

    A row still waiting for its first dispatch (``queued``/``staggering``,
    :func:`progress_tracker.awaits_first_dispatch`; a retry waiting for its
    launch turn renders its run time) renders
    ``waiting 7m45s`` and no budget: it has spent none, and ``7m30s/20m`` —
    what it rendered until the wait and the run were separated — read as budget
    spent. A
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

    F5, 2026-09-20: ``run_record._elapsed_since`` catches ``ValueError`` only, but
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
    if not terminal and awaits_first_dispatch(entry):
        try:
            wait = entry_queued_s(entry)
        except Exception as exc:
            note_swallowed("status: queued model wait", exc)
            return ""
        return f"waiting {format_elapsed(wait)}" if wait is not None else ""
    try:
        elapsed = entry_elapsed_s(entry)
    except Exception as exc:
        note_swallowed("status: model elapsed time", exc)
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
        except Exception as exc:
            note_swallowed("status: finished model queued time", exc)
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
    # `starts in 4s`: the launch ramp, named. Slots of a provider
    # dispatch its `LAUNCH_STAGGER_S` apart, and the launch-time poll — taken at
    # second zero on purpose, for the roster — met every row but the first
    # reading `staggering`, which a reader took for the fan-out running its
    # models one at a time. The state word is the lifecycle's and
    # stays; the clause says how long, in the shape `retry in 20s` already
    # has. Rounded *up*, so a slot 0.4 s from dispatch reads `1s`, never `0s`
    # — and `entry_stagger_remaining_s` is `None` once the stamp is past, so
    # a poll landing on the flip renders no clause rather than a countdown
    # that reached zero and stayed.
    remaining = entry_stagger_remaining_s(entry)
    if remaining is not None:
        details.append(f"starts in {math.ceil(remaining)}s")
    # A jailed slot's `jail-denied` row names the denied path.
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
    three launch writes drop the predecessor's ``progress`` outright, so a map surviving
    next to a *different* run's
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
        except Exception as exc:  # pragma: no cover - an unreadable dir renders the map
            note_swallowed("status: requested model order", exc)
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

    **An absent map is not an absent roster**. The child writes
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
      visibility).

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
    # A finished run's notes follow its counts, so a host that
    # relays these lines verbatim relays "1 not applied" beside "10/10 items
    # applied".
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
    many specs ended inside it. ``None`` now means only what the
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
    began, so nothing was observed about it either.

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
            except Exception as exc:
                # The `started_at: "...Z"` shape that used to take the whole
                # command down. A clause with no clock is worth
                # more than a traceback.
                note_swallowed("status: finished-during-wait elapsed time", exc)
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


def _run_notes(view: Dict[str, Any]) -> List[str]:
    """``progress.notes``: a finished apply phase's lines for the host — a consistency warning,
the items left unapplied and why."""
    progress = view.get("progress") if isinstance(view.get("progress"), dict) else {}
    notes = progress.get("notes")
    return [str(note).strip() for note in notes if str(note).strip()] if isinstance(
        notes, list) else []


def _id_list(value: Any) -> List[str]:
    """A mirror's id list as strings; anything that is not a list is none."""
    return [str(item) for item in value] if isinstance(value, list) else []


def _kept_labels(mirror: Mapping[str, Any], kept: Sequence[str]) -> Dict[str, str]:
    """What each task a write mirror kept is, in the ``resume: kept`` line's
    words: a check whose findings stand (its row carries
    them), an accepted task (``accepted_task_ids``, a check apart from a
    failed task) and a manual task completed by hand
    (``completed_by_hand_task_ids``). Plain kept tasks carry
    no label."""

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
    # A manual task kept on the user's `=done` answer.
    for task_id in _id_list(mirror.get("completed_by_hand_task_ids")):
        labels[task_id] = COMPLETED_BY_HAND_LABEL
    return labels


def _kept_text(kept: Sequence[str], labels: Mapping[str, str]) -> str:
    """The kept note's list: ``task_ledger.kept_named``, at most five plain
    ids as before."""
    return task_ledger.kept_named(kept, labels, limit=5)


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
        # printed `implement 0/9 ok`.
        counts = _write_mirror_as_counts(mirror)["counts"]
    ok = mirror.get("ok")
    if not isinstance(ok, int):
        ok = counts.get("ok", 0) if isinstance(counts.get("ok"), int) else 0
    accepted = mirror.get("accepted_task_ids") if isinstance(mirror.get("accepted_task_ids"), list) else []
    # An implement run's accepted tasks were kept
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
        # A resume that dispatched nothing read
        # "1/4 batches ok", the one being a check an earlier run finished.
        # Each kept task is named with what it is,
        # in the `resume: kept` line's words, an accepted one included.
        kept_note = (
            f" ({len(kept)} kept from an earlier run: "
            f"{_kept_text(kept, kept_labels)})"
            if kept else ""
        )
        if total == 0:
            # A resume that
            # dispatched nothing read "implement 0/0 batches ok (1 kept …),
            # 0/0 items applied" under "failed".
            parts = [f"{kind}: nothing dispatched{kept_note}"]
        elif kind == "implement":
            # Implement counts tasks, as its `[ETA]` lines say. An implement task is its
            # own one item, so "3/4 items
            # applied" beside "4/4 tasks ok" counted the same tasks a second
            # way; the outcome clauses below
            # say which applied an edit.
            parts = [f"{kind} {ok}/{total} tasks ok{kept_note}"]
        else:
            # A single-target
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
            # The items not applied follow
            # the count they are left out of, after a semicolon.
            counted_items = True
    else:
        parts = [f"{kind} {ok}/{total} ok"]
    # F10: `in_flight` (`write_reports.WriteReports.mirror_status`,
    # `write_batch_scheduler.WriteBatchScheduler._begin_sweep`) is what turns
    # "0 dispatched, heartbeat Ns ago" — indistinguishable from a stall — into
    # naming the task that is still running and for how long.
    in_flight = mirror.get("in_flight") if isinstance(mirror.get("in_flight"), list) else []
    entries = []
    for row in in_flight:
        if not isinstance(row, dict) or not row.get("task_id"):
            continue
        # Same defensive read as `_model_timing_text`, same reason: `dispatched_at` goes
        # through the same `ValueError`-only
        # parser, so one tz-aware stamp written by a future mirror would take
        # the whole poll down instead of costing this row its `(since …)`.
        try:
            elapsed = run_record._elapsed_since(row.get("dispatched_at"))
        except Exception as exc:
            note_swallowed("status: write mirror in-flight time", exc)
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
        # `verified` here as on every other surface.
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
    # The id lists the rows carry are read from them (`task_ledger.mirror_ids`;
    # an older mirror's own list as it recorded it).
    failed = _mirror_ids(mirror, "failed_task_ids") or []
    if failed:
        parts.append(f"failed {', '.join(map(str, failed))}")
    # Racing re-run 4: a check task that ran and reported
    # problems is named, never only counted under its label.
    flagged = _mirror_ids(mirror, "check_findings_task_ids")
    if isinstance(flagged, list) and flagged:
        parts.append(f"check findings {', '.join(map(str, flagged))}")
    # A code batch applied its edits, then a check it ran
    # failed — never only an `ok` count.
    failing = _mirror_ids(mirror, "batch_check_task_ids")
    if isinstance(failing, list) and failing:
        # A check that could not run is named so (the prefix is
        # `batch_reply.BATCH_CHECK_COULD_NOT_RUN`, spelled here so this
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
    # A task whose own check repeated only the findings the
    # user accepted for a check is named, never only counted `ok`.
    repeated = mirror.get("batch_check_accepted")
    if isinstance(repeated, dict) and repeated:
        parts += accepted_rerun_clauses({
            str(task_id): checks for task_id, checks in repeated.items()
            if isinstance(checks, list)
        })
    # And one whose own check repeated a check task's finding.
    echoed = mirror.get("batch_check_repeats")
    if isinstance(echoed, dict) and echoed:
        parts += repeated_check_clauses({
            str(task_id): checks for task_id, checks in echoed.items()
            if isinstance(checks, list)
        })
    # An item a finished batch declined (or one skipped at the
    # user's request) is named, never only left out of `items applied`.
    not_applied = not_applied_item_clauses(mirror)
    if not_applied and counted_items:
        parts[0] = "; ".join([parts[0], *not_applied])
    else:
        parts += not_applied
    # Racing re-run 3: the tasks a stop left undispatched were
    # on no surface at all; a failed task the user accepted is named too.
    not_run = mirror.get("not_run_task_ids") if isinstance(mirror.get("not_run_task_ids"), list) else []
    # A task a check with findings kept from running says so,
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
    # A check accepted with its
    # findings read "accepted after failing T002"; the mirror names those
    # apart (a mirror without the key reads as before). An implement mirror
    # names them in the kept note instead.
    with_findings = set(_id_list(mirror.get("accepted_with_findings_task_ids")))
    shown = set(folded) if isinstance(items_total, int) and isinstance(items_applied, int) else set()
    accepted_checks = [
        str(t) for t in accepted if str(t) in with_findings and str(t) not in shown
    ]
    accepted_failed = [
        str(t) for t in accepted if str(t) not in with_findings and str(t) not in shown
    ]
    # In the tally's words (`task_ledger.bucket_clauses`), label then ids.
    parts += _bucket_clauses(
        {"accepted_findings": accepted_checks, "accepted_failed": accepted_failed},
        {}, _MIRROR_ACCEPTED_LABELS, sep=" ",
    )
    # F9: `skipped_task_ids`/`human_task_strategy` (resolved before dispatch,
    # `write_reports.WriteReports.mirror_status`) were on `.status.json` already
    # but rendered nowhere, so the one task `--yes`'s default strategy defers
    # to a human was invisible in the finished run's own progress line.
    skipped_ids = mirror.get("skipped_task_ids") if isinstance(mirror.get("skipped_task_ids"), list) else []
    # A task the user skipped (`--human-task <id>=skip`), and
    # the tasks skipped with it, are not manual work left for the user, so
    # they are named apart from the deferral (Codex stop-path accept 02 read
    # "deferred manual: T005, T006" beside a summary saying "Skipped at your
    # request"). A mirror without the keys reads as before.
    declined = _id_list(mirror.get("declined_task_ids"))
    with_them = _id_list(mirror.get("declined_dependent_task_ids"))
    # A task skipped with a deferred manual task is named
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
    waiting = [
        str(task_id) for task_id in skipped_ids if str(task_id) in waits_on
    ]
    strategy = mirror.get("human_task_strategy")
    # The skip buckets in the words `status` names them by from state.json
    # (`task_ledger.bucket_clauses`); the deferral says its strategy.
    parts += _bucket_clauses(
        {"deferred": deferred, "deferred_dependents": waiting,
         "declined": declined, "declined_dependents": with_them},
        waits_on, _MIRROR_SKIP_LABELS,
        suffix={"deferred": f" ({strategy})" if strategy else ""},
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
