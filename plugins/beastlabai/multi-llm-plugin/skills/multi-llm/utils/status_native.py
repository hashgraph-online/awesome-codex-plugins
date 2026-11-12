"""The phases a native host ran, read back from ``state.json``.

A native leg leaves no run record, so ``status`` rebuilds its implement and
apply phases from ``state.json`` and the phase folders
(:func:`state_implement_view`, :func:`state_apply_views`), sets aside an
executor run the native leg went on from (:func:`set_aside_superseded_runs`),
tallies implement's tasks (:func:`implement_task_tally`) and renders those
blocks, with the clauses the run view's own text shares. Reads
``status_views`` and ``status_commands``
(docs/development/status.md#status-parity-across-execution-paths).
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from . import detach, run_record, status_views, task_ledger
from .advisory import note_swallowed
from .task_ledger import (
    TALLY_DONE as _TALLY_DONE,
    TALLY_LABELS as _TALLY_LABELS,
    VIEW_MERGE as _VIEW_MERGE,
    bucket_clauses as _bucket_clauses,
)
from .output_handler import phase_dir_path
from .text_clip import clip, plain_line, without_closing_mark
from .status_views import STOPPED_STEP, _IMPLEMENT_PHASE, _run_is_live, _stopped_for_the_user
from .status_commands import Speller, _RESUME_VERB_BY_MODE, _retry_command, why_line


_WRITE_REPORT = "write_batch_report.json"


def _implement_buckets(
    state: Any, *, merge: Optional[Mapping[str, str]] = None,
) -> Tuple[Dict[str, List[str]], Dict[str, str]]:
    """Every task of implement's decomposition in one bucket of
    :data:`task_ledger.TALLY_LABELS`, in decomposition order, and
    ``{dependent: manual task}`` for the ``deferred_dependents`` bucket: the
    one classifier :func:`implement_task_tally` and
    :func:`state_implement_view` share (``task_ledger.classify``, which the
    executor's write mirror names its skips by too). *merge* folds a bucket
    into another (the view's coarser ``accepted``). *state* is a read-only
    ``StateManager``; the decomposition must be on record.
    """
    ledger = task_ledger.classify(state)
    return ledger.buckets(merge), ledger.waits_on


def state_implement_view(
    plan_path: Path, views: Sequence[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Implement's tasks as ``state.json`` records them, when nothing else does.

    The native leg
    hands its batches to the host, which writes no ``write_batch_report.json``
    and no write mirror, so ``status --view run`` listed no implement task at
    all while ``state.json`` held every status, reason, check finding and
    answer. This reads them back — only when the implement phase dir has no
    report, no listed view carries a write mirror for it, and the plan has an
    implement decomposition on record that is started and not completed — as
    ``{tasks, titles, buckets, reasons, findings, answers}``. Read-only;
    ``None`` when it does not apply.

    A native implement the
    host completed is read back too (``completed: true``): `status --view
    run` printed "no run recorded for phase implement" after it, since the
    native leg leaves nothing else that view reads.
    """
    # Imported here to keep run_status, which loads this module, light.
    from .state_manager import StateManager

    implement_dir = phase_dir_path(plan_path, _IMPLEMENT_PHASE)
    if (implement_dir / _WRITE_REPORT).exists() and native_leg_stamp(implement_dir) is None:
        # An executor report beside a native emit's newer
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
    except Exception as exc:  # noqa: BLE001 - advisory: the run view is not
        note_swallowed("status: native implement state read", exc)
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
    # The workflow trailer's rule for both kinds of findings:
    # once implement completed, shown until a review-code that judged them
    # completed or was skipped.
    settled = completed and (
        state.is_phase_completed("code-review") or state.is_phase_skipped("code-review")
    )
    tally_buckets, _waits = _implement_buckets(state)
    # The workflow view's own
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
        # Imported here to keep run_status, which loads this module, light.
        from .stop_answers import native_resume_why, native_stop_answers

        stop_answers = native_stop_answers(record)
        # What the plain resume does, as `util next-command`
        # says it above the resume.
        stop_resume_why = native_resume_why(
            record, phase_dir=str(phase_dir_path(plan_path, _IMPLEMENT_PHASE)))
        # Every code task left
        # waits on a manual task the user can do now, so the resume records
        # it done; the run stopped for the user.
        gate_flags, gate_why, gate_answers = _native_manual_gate(state)
        if gate_flags:
            stop_resume_why = gate_why or stop_resume_why
            stopped = not in_progress_since
            # And the user's decline.
            stop_answers = list(stop_answers) + gate_answers
    return {
        "completed": completed,
        # Whether `--implement <plan> --resume` continues it,
        # and the `--human-task` answers its stop waits for, as the native
        # `util next-command` gives them (`{flags, why}`, `--resume` first).
        "resumable": resumable,
        "stop_answers": stop_answers,
        "stop_resume_why": stop_resume_why,
        # The flags the resume carries after the plan.
        "resume_flags": gate_flags,
        # Whether the
        # run ended short and waits for the user, as the executor routes'
        # "stopped and needs you" head says (:func:`native_run_stopped`).
        "stopped": stopped,
        # The tasks a stopped run's host could
        # still run, which the resume runs (:func:`native_still_runnable`).
        "still_runnable": native_still_runnable(record, statuses) if stopped else [],
        # When the host's loop
        # is between `util metrics start` and `finish`.
        "in_progress_since": in_progress_since,
        # When state.json last changed, so a loop that ended
        # without `util metrics finish` can be told from a live one.
        "state_changed_at": _state_changed_at(state.state_file),
        # The executor routes' `all tasks:` tally, every task in one bucket
        # (the native leg printed a coarser `tasks:` line).
        "tally": {
            "total": len(decomposition),
            "done": sum(len(tally_buckets[key]) for key in _TALLY_DONE),
            "buckets": tally_buckets,
            "waits_on": waits_on,
        },
        "tasks": [str(t) for t in decomposition],
        "titles": {str(k): str(v) for k, v in titles.items()},
        "buckets": buckets,
        # What each `deferred_dependents` task waits on.
        "waits_on": waits_on,
        "reasons": {
            task_id: str(reasons[task_id])
            for task_id in buckets["failed"] + buckets["not_run"]
            if reasons.get(task_id)
        },
        "findings": [] if settled else state.implementation_check_findings(),
        # A code task whose own check failed after its edits.
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
    host could still run without it, in task order: every
    task of the decomposition not recorded completed, skipped or failed that
    is not manual, not held by a check's findings and not after a failed
    task. ``[]`` when nothing waits for an answer, or the record cannot be
    read."""
    # Imported here to keep run_status, which loads this module, light.
    from .stop_answers import _native_stop_facts

    try:
        scope = [str(t) for t in record.get("implement_task_ids") or []]
        facts = _native_stop_facts(record)
        if facts is None:
            return []
        manual = {str(t) for t in (record.get("implement_human_task_ids") or [])}
        kept_out = set(facts["failed_ids"]) | set(facts["blocked"])
        for task_id in facts["failed_ids"]:
            kept_out.update(facts["undone_with"](task_id))
    except Exception as exc:  # noqa: BLE001 - advisory: the run view is not
        note_swallowed("status: native still runnable", exc)
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
    code task left waits on a manual task the user can do now, the words ``util
    next-command`` gives them — the answers being the
    user's decline of each such task — else
    ``([], None, [])``."""
    # Imported here to keep run_status, which loads this module, light.
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
    except Exception as exc:  # noqa: BLE001 - advisory: the plain resume stands
        note_swallowed("status: native manual gate", exc)
        return [], None, []


def native_run_stopped(
    record: Mapping[str, Any], statuses: Mapping[str, Any],
) -> bool:
    """Whether a native implement the host ran ended short and waits for the
    user: the run the executor routes head "stopped and needs you".

    The native head read
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
      (``stop_answers.native_stop_answers``);
    * and either no task is left that the host could still run without that
      answer (every task not completed, skipped or failed is a manual one,
      held by a check, or after a failed task), or the host closed the loop
      the last emit opened: its ``util metrics finish`` removed the emit's
      left-out record (``metrics_left_out``), or the emit left nothing out.

    A host that ended its turn right after a failed task,
    leaving an independent task pending, read "not finished on the host"
    while ``util next-command`` gave the resume and the answers. Its loop is
    closed and something waits, so it is stopped; the block names the tasks
    it could still run (:func:`native_still_runnable`), which the resume
    runs. Right after an emit that recorded a refusal (its left-out record
    still there), the tasks it handed out can still run, so the moments
    between the emit and the host's records never read as a stop. Advisory:
    an unreadable record is not a stop.
    """
    # Imported here to keep run_status, which loads this module, light.
    from .stop_answers import _native_stop_facts

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
    except Exception as exc:  # noqa: BLE001 - advisory: the run view is not
        note_swallowed("status: native run stopped", exc)
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

    return datetime.fromtimestamp(stamp).isoformat(timespec="seconds")


#: A native implement that stopped and waits for the user's answer
#: (:func:`native_run_stopped`): the executor routes' words
#: (:data:`STOPPED_FOR_THE_USER_VERDICT`), with no exit code to name, since
#: the native leg's phase exits 0 and the host closed it.
NATIVE_STOPPED_VERDICT = "stopped and needs you (not marked completed)"


def _native_head(
    dir_name: str, *, completed: bool, since: Optional[str], unit: str,
    changed: Optional[str] = None, stopped: bool = False,
) -> str:
    """A native write phase's head line: what state.json says it is doing.

    A running native implement read
    "no run record — the host ran these tasks itself" exactly as a stopped
    one did, so the view could not say whether anything was going on. One that stopped
    needing the user (*stopped*) reads
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
    """What an in-progress head may also mean, and the way on.

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
    whole answer (``--resume --human-task T005=skip``).

    On a commit review (a brief whose ``state.json`` holds ``commit_range``)
    the command reads as the commit mode with the pinned range, in either
    spelling: ``status``'s ``resume with:``
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
    """The way on from a native phase that stopped.

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
        # What the plain resume does, like each answer below.
        lines.append(why_line(why))
    for command, answer_why in answers:
        lines.append(f"      or answer the stop with: {command}")
        lines.append(why_line(answer_why))
    return lines


#: How many task ids the still-runnable line names before "and N more".
STILL_RUNNABLE_IDS_SHOWN = 8


def _still_runnable_clause(ids: Sequence[str]) -> str:
    """``T003 can still run: the resume runs it``."""
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

    Its tally line reads
    ``all tasks:``, in the executor routes' words (:func:`implement_tally_text`),
    and its head says whether the host's run is in progress. An in-progress head says
    when state.json last changed and, with
    *resume* (:func:`native_resume_command`), what it may also mean. A "not finished"
    one that a ``--resume`` continues
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
        # Stopped with tasks the host could run.
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
    the native emit, else ``None``.

    Every run of a write phase rewrites that file, on either leg, and only
    the native emit stamps it (``write_phase_bridge.NATIVE_LEG``), so the
    stamp says the phase's newest run is the host's own. Advisory: an
    unreadable file is no stamp."""
    try:
        document = json.loads((Path(directory) / _WRITE_TASKS).read_text(encoding="utf-8"))
    except FileNotFoundError:  # no emit on record: no stamp
        return None
    except Exception as exc:  # noqa: BLE001 - advisory
        note_swallowed("status: native leg stamp", exc)
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
    except FileNotFoundError:  # no emit on record: no time
        document = None
    except Exception as exc:  # noqa: BLE001 - advisory
        note_swallowed("status: native emit time", exc)
        document = None
    record = document.get("native_run") if isinstance(document, dict) else None
    emitted = run_record._parse_stamp(
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
    started = run_record._parse_stamp(run.get("started_at"))
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
    place; otherwise the record stays as it is."""
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

    The run view listed the native
    implement but none of the apply phases the same host had
    run, while on the tool routes, whose apply runs leave a run record, it
    listed every one. A phase is listed when its folder holds the batch list
    the native emit wrote (``write_tasks.json``) and neither a run view nor a
    ``write_batch_report.json`` (the executor's), and the workflow payload
    (*workflow*: ``get_workflow_status``, which already sets an earlier
    cycle's batches aside) shows it ``completed`` or ``in_progress``, or the
    host's loop is going. ``{phase, phase_dir, completed,
    in_progress_since, batches_recorded, batches_total}`` (plus
    ``declined_items`` / ``skipped_items`` when a batch's record names one,
    ``items_applied`` / ``items_total`` / ``applied_to`` once a record names
    one of its items, counted over the run, and ``failed_batches``) in
    workflow order;
    *only* limits it to one phase (``--phase``). Read-only.
    """
    # Imported here to keep status_native light.
    from .metrics import _current_run_id
    # Imported here to keep run_status, which loads this module, light.
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
            workflow = status_views._workflow_payload(plan_path, host_id=host_id)
    except Exception as exc:  # noqa: BLE001 - advisory: the run view is not
        note_swallowed("status: native apply state read", exc)
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
            # As on the native implement view.
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
            # The batches whose own check failed after their
            # edits, as `util batch-done` recorded them, named as the native
            # implement view names its tasks'.
            checks = _native_apply_batch_checks(record, directory)
            if checks:
                entry["batch_checks"] = checks
        # The items a batch declined or the user skipped;
        # And the items count they are left out of.
        entry.update(_native_apply_not_applied(record, directory, phase))
        out.append(entry)
    return out


#: The not-applied items a write mirror (and a native apply view) names, in
#: the order and words the progress line prints them: the
#: key, the words for one item and for several, and the words a recorded
#: reason may open with that the clause has already said.
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
    ``items applied`` count; the native apply view prints each on its own, so the two
    legs name a declined item in the same words.

    The clause read "not applied, declined by
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
    set of checks, from ``{task_id: [check ids]}``: the code
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
    checks, from ``{task_id: [check ids]}``: the code tasks
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
    mirror's shape. Read
    from ``processed_<phase dir>``: a record of the review the phase's
    ``write_tasks.json`` applies (its ``grouped_sha256``), or, for a record
    or a task without that stamp, one whose item the run handed out. ``{}``
    when nothing applies or either cannot be read.

    The block printed
    "1 declined by its batch (not applied): …" with no "2/3 items applied;"
    before it, which the executor's line has. ``items_applied`` counts the
    items a record of this run says ``applied`` (as the executor counts an
    applied batch's items less the ones it declined or skipped); both are
    left out until a record of this run names one of its items.
    ``applied_to`` is the one file a single-target phase's batches all
    declare, from the repository root, as the executor names it.

    The run is the file's ``native_run``
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
    # Imported here to keep run_status, which loads this module, light.
    from .state_manager import _parse_completion_time

    try:
        document = json.loads((directory / _WRITE_TASKS).read_text(encoding="utf-8"))
    except FileNotFoundError:  # no emit on record: nothing handed out
        return {}
    except Exception as exc:  # noqa: BLE001 - advisory
        note_swallowed("status: native apply not applied", exc)
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


#: The words of the clause naming a native apply phase's failed batches, for one and for several.
_FAILED_BATCH_WORDS = ("1 batch failed", "{n} batches failed")


def failed_batch_clause(view: Mapping[str, Any]) -> List[str]:
    """``1 batch failed: apply-batch-0 (<reason>)`` (``2 batches failed: …;
    …``) for a native apply view's ``failed_batches``, else ``[]``: the
    executor's line names its failed batches (``failed apply-batch-0``), and
    the native view's count read "0/4 items applied" beside one and named
    nothing."""
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
    # Imported here to keep run_status, which loads this module, light.
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
        # Imported here to keep run_status, which loads this module, light.
        from .known_checks import earlier_batch_check_failures

        document = json.loads((directory / _WRITE_TASKS).read_text(encoding="utf-8"))
        tasks = document.get("batches") or document.get("tasks") or []
        return [
            {"id": task_id, "findings": findings}
            for task_id, findings in earlier_batch_check_failures(record, tasks, "")
        ]
    except Exception as exc:  # noqa: BLE001 - advisory
        note_swallowed("status: native apply batch checks", exc)
        return []


def native_items_count(view: Mapping[str, Any]) -> str:
    """``2/3 items applied`` (``… applied to`` for a single-target
    phase) for a native apply view that counted its items, else ``""``:
    the executor's progress-line words."""
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
    # The items left out of the count follow it in the executor's progress-line
    # words, "2/3 items applied; 1 declined by …", then the batches recorded
    # failed, by name.
    not_applied = not_applied_item_clauses(view) + failed_batch_clause(view)
    count = native_items_count(view)
    if count:
        lines.append("      " + "; ".join([count, *not_applied]))
    else:
        lines += [f"      {clause}" for clause in not_applied]
    if since:
        lines += _native_resume_line(resume)
    elif not view.get("completed"):
        # Listed unfinished only while the workflow shows it
        # `in_progress` (`state_apply_views`), which a `--resume` continues.
        lines += _native_stop_lines(resume)
    return lines


def implement_task_tally(plan_path: Path) -> Optional[Dict[str, Any]]:
    """Every task of implement's decomposition as ``state.json`` records it.

    After a resume,
    ``status``'s implement run block counted only that run's batches ("2/2
    batches ok, 1/2 items applied", then "1/1" on the accept path) and never
    added up to the fixture's seven tasks, while summary.md and the stop's
    own account did. The run mirror holds one run; ``state.json`` holds the
    phase. ``{"total", "done", "buckets"}`` over ``task_ledger.TALLY_LABELS``, each
    task in exactly one bucket; ``None`` without a decomposition on record.
    Read-only.
    """
    # Imported here to keep run_status, which loads this module, light.
    from .state_manager import StateManager

    try:
        state = StateManager(plan_path, read_only=True)
    except Exception as exc:  # noqa: BLE001 - advisory: the run view is not
        note_swallowed("status: implement tally state read", exc)
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
