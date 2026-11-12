"""The one writer of a write batch's per-task record in ``state.json``.

Both write legs record a finished batch through :func:`record_batch_facts`:
the executor's scheduler (``WriteBatchScheduler._record_batch_effects``) and
the native leg's ``util batch-done`` (``batch_done.record_batch``). Each leg
reads its own evidence (a ``TaskOutcome``, the host's flags) into
:class:`BatchFacts`; this module turns the facts into the record, so a new
per-task fact is added once and both legs carry it
(docs/development/write-scheduler.md, "One record writer for both legs").

A pure mutation of the state dict: each leg keeps its own lock and its own
save (the scheduler mutates its in-memory ``StateManager`` dict under its
effects lock, ``util batch-done`` the file's dict under ``state_file_lock``),
and the status write goes through the caller's *set_status*, so the
executor's ``StateManager.update_task_status`` still journals it. What only
one leg does stays with that leg: the commit guard, the completion stamp,
held dependents and the ``[ETA]`` total, ``tracked_files`` on the native
leg; the verdict stamp, prior-changes line and metric on the executor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from . import known_checks as _known_checks
from .state_manager import (
    record_batch_items_in_state,
    set_task_batch_check_accepted_in_state,
    set_task_batch_check_in_state,
    set_task_batch_check_repeats_in_state,
    set_task_check_findings_in_state,
    set_task_check_tree_in_state,
    set_task_own_check_note_in_state,
    set_task_own_check_ran_in_state,
    set_task_own_text_in_state,
    update_task_status_in_state,
)
from .subagent_tasks import APPLY_WRITE_KINDS
from .check_records import move_check_repeats_in_state, task_own_text

__all__ = ["BatchFacts", "BatchRecord", "KEEP_CHECK_TREE", "record_batch_facts"]

#: :attr:`BatchFacts.check_tree`'s default: leave ``task_check_trees`` as it
#: is. The executor keeps a check's tree stamp on its verdict instead.
KEEP_CHECK_TREE: Any = object()


@dataclass(frozen=True)
class BatchFacts:
    """What one leg read about one finished batch, before it is recorded.

    *status* is ``completed`` or ``failed``. Every per-task fact is the
    leg's reading of a completed batch; for any other status
    :func:`record_batch_facts` clears the task's earlier verdict instead of
    writing them.
    """

    task_id: str
    #: The write kind (``implement``, ``apply_code_fixes``, ...).
    kind: str
    status: str
    reason: Optional[str]
    #: ``state_manager.PROCESSED_LEG_EXECUTOR`` or ``PROCESSED_LEG_NATIVE``.
    leg: str
    #: The phase dir word ``processed_<…>`` is keyed by.
    processed_phase: str = ""
    #: A check task's findings (``None``: no check verdict).
    check_findings: Optional[Sequence[str]] = None
    #: The files a check with findings left (native only), or
    #: :data:`KEEP_CHECK_TREE`.
    check_tree: Any = KEEP_CHECK_TREE
    #: A code batch's own failing check, after accepted and repeated
    #: findings were split out of it.
    batch_check: Optional[Sequence[str]] = None
    #: Whether its own check reported at all, a pass included.
    own_check_ran: bool = False
    batch_check_accepted: Mapping[str, Sequence[str]] = field(default_factory=dict)
    batch_check_repeats: Mapping[str, Sequence[str]] = field(default_factory=dict)
    #: Its own words about the checks it ran, never read as a finding.
    note: Optional[str] = None
    #: An apply-code-fixes batch's ``check.listed`` outcomes.
    listed: Optional[Mapping[str, str]] = None
    #: Whether an apply-code-fixes batch's check report is written. ``False``
    #: only for a batch the executor refused before dispatch that it reads as
    #: done (``dispatched or kept or not ok``): no runner reported on it.
    reports_checks: bool = True
    #: An apply batch's items not applied: ``{item: reason}``.
    declined: Mapping[str, str] = field(default_factory=dict)
    skipped: Mapping[str, str] = field(default_factory=dict)
    #: The executor read the batch as changing nothing (``processed_<…>``
    #: records ``no-op``); the native leg has no such reading.
    no_op: bool = False
    #: A batch an earlier run finished that this run does not dispatch again
    #: (the executor's resume skip): its status and items are recorded again,
    #: its verdict and check report stay as that run recorded them.
    resumed: bool = False

    @property
    def completed(self) -> bool:
        return self.status == "completed"


@dataclass
class BatchRecord:
    """What :func:`record_batch_facts` wrote that the leg reports on."""

    #: An apply batch's item ids recorded in ``processed_<…>``.
    items: List[str] = field(default_factory=list)
    #: ``{task: (own findings left, repeats by check)}`` for each code task a
    #: check's findings moved (``move_check_repeats_in_state``).
    repeats_moved: Dict[str, Tuple[List[str], Dict[str, List[str]]]] = field(
        default_factory=dict)


def record_batch_facts(
    state: Dict[str, Any],
    task: Mapping[str, Any],
    facts: BatchFacts,
    *,
    tasks: Sequence[Dict[str, Any]] = (),
    set_status: Optional[Callable[..., None]] = None,
) -> BatchRecord:
    """Record *facts* about *task*'s batch in the ``state.json`` dict *state*.

    In order: the task's status and reason (through *set_status*, called as
    ``set_status(task_id, status, reason=reason)``; the raw-dict writer by
    default); for an implement task its check findings, check tree, own
    failing check and its own text (``task_own_text``), that its own check ran, the accepted and
    repeated findings split out of it, the code tasks a check's new findings
    move (*tasks*: the phase's materialized tasks) and its note; an
    apply-code-fixes batch's check report; an apply batch's items in
    ``processed_<…>``. A :attr:`BatchFacts.resumed` batch gets its status and
    items only.

    Two rules hold whatever the leg read. A record other than ``completed``
    clears every earlier verdict of the task (each setter gets nothing). An
    apply-code-fixes check report is written unless
    :attr:`BatchFacts.reports_checks` is false.
    """
    task_id = facts.task_id
    completed = facts.completed

    def kept(value: Any) -> Any:
        return value if completed else None

    if set_status is None:
        def set_status(task_id: str, status: str, *, reason: Optional[str] = None) -> None:
            update_task_status_in_state(state, task_id, status, reason)
    set_status(task_id, facts.status, reason=facts.reason)
    record = BatchRecord()
    if facts.resumed:
        pass
    elif facts.kind == "implement":
        set_task_check_findings_in_state(state, task_id, kept(facts.check_findings))
        if facts.check_tree is not KEEP_CHECK_TREE:
            set_task_check_tree_in_state(state, task_id, kept(facts.check_tree))
        # Beside the check findings, never among them: a code task's own
        # failing check holds nothing back.
        set_task_batch_check_in_state(state, task_id, kept(facts.batch_check))
        # Its own words beside a failing own check, for a check that
        # reports the same finding in a later run.
        set_task_own_text_in_state(state, task_id, task_own_text(task))
        set_task_own_check_ran_in_state(state, task_id, completed and facts.own_check_ran)
        set_task_batch_check_accepted_in_state(
            state, task_id, kept(facts.batch_check_accepted))
        set_task_batch_check_repeats_in_state(
            state, task_id, kept(facts.batch_check_repeats))
        if completed and facts.check_findings:
            # A code task recorded earlier whose own check reported the
            # finding this check now has on record.
            record.repeats_moved = move_check_repeats_in_state(state, tasks, task_id)
        set_task_own_check_note_in_state(state, task_id, kept(facts.note))
    elif facts.kind == "apply_code_fixes" and facts.reports_checks:
        # What the batch's own checks reported, for the next batch's prompt
        # and the tests-not-run line.
        _known_checks.set_batch_check_report_in_state(
            state, task_id,
            prior_changes_id=str(task.get("prior_changes_id") or ""),
            grouped_sha256=_known_checks.review_stamp(task),
            findings=kept(facts.batch_check),
            listed=kept(facts.listed),
            note=kept(facts.note),
        )
    if facts.kind in APPLY_WRITE_KINDS:
        record.items = record_batch_items_in_state(
            state, facts.processed_phase, task,
            completed=completed, leg=facts.leg,
            declined=dict(facts.declined), skipped=dict(facts.skipped),
            no_op=facts.no_op,
        )
    return record
