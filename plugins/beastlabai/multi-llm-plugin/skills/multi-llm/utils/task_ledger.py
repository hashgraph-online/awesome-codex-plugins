"""What happened to a write phase's tasks: the one classifier both legs answer
through.

The executor leg answers from its run (``human_task_plan.HumanTaskPlan``
and the write mirror it writes to ``.status.json``); the native leg, and
``status`` after either, answer from ``state.json`` (``run_status``'s
``state_implement_view`` and ``implement_task_tally``, ``StateManager``'s
deferral readers). Both read a task's outcome through this module: the reason
words a record carries, the rule that reads a skip as the user's decline or
as a deferral, the walk to the manual task a skipped dependent waits on, the
bucket each task of the decomposition falls in, and the words each bucket and
kept task is named by (docs/development/status.md, "Status parity across
execution paths").

Pure: no I/O and no import from this package, so the low-level state module
and the scheduler can both build on it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

__all__ = [
    "USER_DECLINED_REASON",
    "ANSWERED_SKIP_PREFIX",
    "ACCEPTED_REASON_PREFIX",
    "ACCEPTED_WITH_FINDINGS_MARK",
    "COMPLETED_MANUAL_REASON",
    "ACCEPTED_WITH_FINDINGS_LABEL",
    "ACCEPTED_AFTER_FAILING_LABEL",
    "COMPLETED_BY_HAND_LABEL",
    "KEPT_WITH_FINDINGS_LABEL",
    "TALLY_LABELS",
    "BUCKET_LABELS",
    "VIEW_MERGE",
    "TALLY_DONE",
    "TaskFacts",
    "TaskLedger",
    "is_declined_reason",
    "skip_chain_root",
    "chain_declined",
    "skip_bucket",
    "classify",
    "bucket_clauses",
    "kept_named",
    "MIRROR_ACCEPTED_LABELS",
    "MIRROR_SKIP_LABELS",
    "MIRROR_ROW_LISTS",
    "mirror_ids",
]


# -- the reason words a task's record carries --------------------------------

#: The recorded reason of a human task the user declined at pause-and-ask.
#: A decline, not a deferral: nobody owes the task afterwards.
USER_DECLINED_REASON = "skipped by user during pause-and-ask"

#: The prefix of the recorded reason of a task the user answered
#: ``--human-task <id>=skip``: a failed code task (the sentence ends
#: ``<id>=skip after it failed``) or a manual task declined under a skip
#: strategy (``human_task_plan.MANUAL_DECLINED_TAIL``). A decline too.
ANSWERED_SKIP_PREFIX = "skipped — you answered --human-task "

#: The prefix of the recorded reason of a failed task the user answered
#: ``--human-task <id>=done`` (``human_task_plan.resolve_human_task_plan``
#: writes the whole sentence into ``HumanTaskPlan.accepted``).
ACCEPTED_REASON_PREFIX = "accepted — "

#: The words in the recorded reason of a check accepted with its findings
#: (``--human-task <id>=done`` on a check that reported problems): read apart
#: from a task accepted after failing.
ACCEPTED_WITH_FINDINGS_MARK = "after its check reported problems"

#: The recorded reason of a manual task answered ``--human-task <id>=done``
#: (``human_task_plan.persist_human_task_plan``; the ``<id>`` is literal).
COMPLETED_MANUAL_REASON = "answered --human-task <id>=done"


# -- the words a task's outcome is named by ----------------------------------

#: How a check the user accepted with its findings and a failed task the user
#: accepted read in a kept list, summary.md's rows and ``status``'s tally
#: (``human_task_plan.answered_done_label``: one spelling everywhere).
ACCEPTED_WITH_FINDINGS_LABEL = "accepted with its check findings"
ACCEPTED_AFTER_FAILING_LABEL = "accepted after failing"
#: How a manual task the user answered ``--human-task <id>=done`` reads.
COMPLETED_BY_HAND_LABEL = "completed by hand"

#: How a check kept from an earlier run with its findings standing reads in a
#: kept list: true while the run is still to decide (a continued run's opening
#: line: it runs again once the files changed) and once it decided (the closing
#: ``resume: kept`` line). An accepted check reads
#: :data:`ACCEPTED_WITH_FINDINGS_LABEL` instead.
KEPT_WITH_FINDINGS_LABEL = (
    "its check reported problems, not run again while the files are unchanged"
)

#: Every bucket a task of implement's decomposition falls in (:func:`classify`),
#: in the order ``status``'s tally names them, with their words. The first
#: five are done (:data:`TALLY_DONE`). A task skipped with a deferred manual
#: task reads "skipped (depends on manual T005)" (:func:`bucket_clauses`).
TALLY_LABELS: Tuple[Tuple[str, str], ...] = (
    ("completed", "completed"),
    ("check_findings", "completed, its check reported problems"),
    ("accepted_findings", ACCEPTED_WITH_FINDINGS_LABEL),
    ("accepted_failed", ACCEPTED_AFTER_FAILING_LABEL),
    ("completed_manual", COMPLETED_BY_HAND_LABEL),
    ("failed", "failed"),
    ("declined", "skipped at your request"),
    ("declined_dependents", "skipped (depend on a task you skipped)"),
    ("deferred", "deferred manual"),
    ("deferred_dependents", "skipped (depends on a manual task)"),
    ("not_run", "not run"),
)

#: :data:`TALLY_LABELS` by bucket: the write mirror's clauses name the skip
#: buckets in these words too (``run_status._mirror_text``).
BUCKET_LABELS: Dict[str, str] = dict(TALLY_LABELS)

#: ``status``'s native implement view folds the tally's buckets into coarser
#: ones (``run_status.state_implement_view``'s ``buckets``).
VIEW_MERGE: Dict[str, str] = {
    "check_findings": "completed",
    "accepted_findings": "accepted",
    "accepted_failed": "accepted",
}

#: The tally's buckets that count as done.
TALLY_DONE: Tuple[str, ...] = (
    "completed", "check_findings", "accepted_findings", "accepted_failed",
    "completed_manual",
)

#: The buckets the executor's write mirror names a run's answered and
#: skipped tasks in (``status_text._mirror_text``), in the order its line
#: names them, in the tally's words: the accepted ones as ``<label> <ids>``,
#: the skips as ``<label>: <ids>`` (:func:`bucket_clauses`).
MIRROR_ACCEPTED_LABELS: Tuple[Tuple[str, str], ...] = tuple(
    (key, BUCKET_LABELS[key]) for key in ("accepted_findings", "accepted_failed")
)
MIRROR_SKIP_LABELS: Tuple[Tuple[str, str], ...] = tuple(
    (key, BUCKET_LABELS[key])
    for key in ("deferred", "deferred_dependents", "declined", "declined_dependents")
)


# -- the classifier ----------------------------------------------------------

#: ``task id -> the skipped task its skip names``, or ``None``: one link of a
#: skip chain. The executor reads it from ``HumanTaskPlan.chain``, the
#: ``state.json`` readers from the ``skipped — depends on skipped task …``
#: reason the same walk recorded.
ParentOf = Callable[[str], Optional[str]]


def is_declined_reason(reason: Any) -> bool:
    """Whether a recorded skip reason is the user's own decline (a
    pause-and-ask "Skip", a ``--human-task <id>=skip`` answer), not a
    deferral. A task skipped because it depends on a declined one is declined
    too (:func:`chain_declined`)."""
    return str(reason or "").startswith((USER_DECLINED_REASON, ANSWERED_SKIP_PREFIX))


def skip_chain_root(task_id: str, parent_of: ParentOf) -> Optional[str]:
    """The end of *task_id*'s skip chain (the task its skip waits on, through
    every skipped task in between), or ``None`` when *task_id* was not skipped
    as a dependent. A cycle ends where it closes."""
    root: Optional[str] = None
    current = task_id
    seen: set = set()
    while current not in seen:
        seen.add(current)
        parent = parent_of(current)
        if parent is None:
            break
        root = current = parent
    return root


def chain_declined(
    task_id: str, parent_of: ParentOf, reason_of: Callable[[str], Any],
) -> bool:
    """Whether *task_id*'s skip is the user's decline: its own reason is one
    (:func:`is_declined_reason`), or its skip chain reaches a task whose
    reason is. A reason this does not recognise (none recorded, a state
    written before reasons were) is a deferral, as every skip used to be."""
    current = task_id
    seen: set = set()
    while True:
        if is_declined_reason(reason_of(current)):
            return True
        parent = parent_of(current)
        if parent is None or current in seen:
            return False
        seen.add(current)
        current = parent


def skip_bucket(
    task_id: str, reason: Any, *,
    declined: Callable[[], bool], root: Callable[[], Optional[str]],
) -> Tuple[str, Optional[str]]:
    """``(bucket, the manual task it waits on)`` for a skipped task, the rule
    both legs name a skip by: ``declined`` (the user's own decline),
    ``declined_dependents`` (skipped with one: *declined* says so),
    ``deferred_dependents`` (skipped with a deferred manual task, *root*), else
    ``deferred``. *declined* and *root* are asked only when the bucket needs
    them, in that order."""
    if is_declined_reason(reason):
        return "declined", None
    if declined():
        return "declined_dependents", None
    waits_on = root()
    if waits_on is not None and waits_on != task_id:
        return "deferred_dependents", waits_on
    return "deferred", None


@dataclass(frozen=True)
class TaskFacts:
    """One task's row of the ledger: its bucket (a :data:`TALLY_LABELS`
    key), its recorded reason, and the manual task a ``deferred_dependents``
    task waits on."""

    task_id: str
    bucket: str
    reason: str = ""
    waits_on: Optional[str] = None


@dataclass(frozen=True)
class TaskLedger:
    """Every task of implement's decomposition, one row each, in
    decomposition order (:func:`classify`)."""

    rows: Tuple[TaskFacts, ...] = ()

    def buckets(self, merge: Optional[Mapping[str, str]] = None) -> Dict[str, List[str]]:
        """``{bucket: [task id, ...]}`` over every :data:`TALLY_LABELS` key,
        each task in exactly one; *merge* folds a bucket into another
        (:data:`VIEW_MERGE`)."""
        merge = merge or {}
        out: Dict[str, List[str]] = {merge.get(key, key): [] for key, _ in TALLY_LABELS}
        for row in self.rows:
            out[merge.get(row.bucket, row.bucket)].append(row.task_id)
        return out

    @property
    def waits_on(self) -> Dict[str, str]:
        """``{dependent: manual task}`` for the ``deferred_dependents`` rows."""
        return {
            row.task_id: row.waits_on for row in self.rows
            if row.bucket == "deferred_dependents" and row.waits_on is not None
        }


def classify(state: Any) -> TaskLedger:
    """Every task of implement's decomposition as ``state.json`` records it.

    *state* is a read-only ``StateManager`` (``state.state`` the record, its
    ``implementation_task_statuses``, ``implementation_check_findings``,
    ``_deferred_to_user`` and ``deferral_root`` readers); the decomposition
    (``implement_task_ids``) must be on record. A completed task is accepted
    (with findings or after failing), completed by hand (a manual task
    answered ``done``), a check with findings, or plainly completed; a skipped
    one goes by :func:`skip_bucket`; one with no outcome is ``not_run``.
    """
    record = state.state
    statuses = state.implementation_task_statuses()
    reasons = record.get("task_status_reasons") or {}
    human = {str(t) for t in (record.get("implement_human_task_ids") or [])}
    findings = {entry["id"] for entry in state.implementation_check_findings()}
    rows: List[TaskFacts] = []
    for task_id in [str(t) for t in record.get("implement_task_ids") or []]:
        status = statuses.get(task_id)
        reason = str(reasons.get(task_id) or "")
        waits_on: Optional[str] = None
        if status == "completed":
            if reason.startswith(ACCEPTED_REASON_PREFIX):
                bucket = ("accepted_findings" if ACCEPTED_WITH_FINDINGS_MARK in reason
                          else "accepted_failed")
            elif task_id in human and "--human-task" in reason:
                bucket = "completed_manual"
            elif task_id in findings:
                bucket = "check_findings"
            else:
                bucket = "completed"
        elif status == "failed":
            bucket = "failed"
        elif status == "skipped":
            bucket, waits_on = skip_bucket(
                task_id, reason,
                declined=lambda task_id=task_id: not state._deferred_to_user(task_id),
                root=lambda task_id=task_id: state.deferral_root(task_id),
            )
        else:
            bucket = "not_run"
        rows.append(TaskFacts(task_id, bucket, reason, waits_on))
    return TaskLedger(tuple(rows))


# -- the words -----------------------------------------------------------------

def bucket_clauses(
    buckets: Mapping[str, Sequence[str]], waits_on: Mapping[str, str],
    labels: Sequence[Tuple[str, str]], *, live: bool = False,
    sep: str = ": ", suffix: Optional[Mapping[str, str]] = None,
) -> List[str]:
    """``<label><sep><ids><suffix>`` per non-empty bucket, in *labels*' order:
    the one place a task bucket is worded, on ``status``'s tally and the
    write mirror's line alike. The dependents of a deferred manual task read
    "skipped (depends on manual T005): T006", one clause per manual task; a
    task not run yet reads "pending" while the run is *live*; *suffix* adds
    a bucket's own tail (the mirror's deferral strategy)."""
    suffix = suffix or {}
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
        parts.append(f"{label}{sep}{', '.join(ids)}{suffix.get(key, '')}")
    return parts


def kept_named(ids: Sequence[str], labels: Mapping[str, str], *, limit: int = 8) -> str:
    """Kept tasks as every kept list names them: the plain ones first (at
    most *limit*, then ``…``), then each labelled one as ``<id> (<label>)``
    — the ``resume: kept`` lines of both legs and the progress line's
    ``(<n> kept from an earlier run: …)``."""
    plain = [str(t) for t in ids if str(t) not in labels]
    shown = ", ".join(plain[:limit]) + (", …" if len(plain) > limit else "")
    labelled = ", ".join(
        f"{t} ({labels[str(t)]})" for t in ids if str(t) in labels
    )
    return ", ".join(part for part in (shown, labelled) if part)


# -- the write mirror's rows -----------------------------------------------------

#: The per-task id lists of the executor's write mirror
#: (``write_reports.WriteReports.mirror_status``) that its own ``tasks`` rows
#: already carry, each with the row test it is read by: every row not ``ok``,
#: every row naming a check's findings, every row naming a code batch's own
#: failing check. The mirror stopped writing them; :func:`mirror_ids` reads
#: them from the rows, and a mirror written before that still has its list.
MIRROR_ROW_LISTS: Dict[str, Callable[[Mapping[str, Any]], bool]] = {
    "failed_task_ids": lambda row: row.get("status") != "ok",
    "check_findings_task_ids": lambda row: (
        isinstance(row.get("check_findings"), list) and bool(row["check_findings"])),
    "batch_check_task_ids": lambda row: (
        isinstance(row.get("batch_check_findings"), list)
        and bool(row["batch_check_findings"])),
}


def mirror_ids(mirror: Mapping[str, Any], key: str) -> Any:
    """A write mirror's *key* list (a :data:`MIRROR_ROW_LISTS` key): as the
    mirror records it, when it does (an older mirror), else the ids of its
    ``tasks`` rows that pass the key's test, in row order."""
    if key in mirror:
        return mirror[key]
    rows = mirror.get("tasks")
    test = MIRROR_ROW_LISTS[key]
    return [
        row.get("task_id") for row in (rows if isinstance(rows, list) else [])
        if isinstance(row, dict) and test(row)
    ]
