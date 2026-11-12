"""What a write dispatch's outcome becomes around the verdict table, and what a
resume does with it.

``write_verdict.decide`` is the table a schema-valid reply lands on. This
module holds the rest of the partial-application and resume rules, as pure
functions over ``TaskOutcome``:

* :func:`classify_attempt`: the write outcome of a dispatch the table never
  saw (a reply that was never schema-valid, the pre-retry check's partial
  application);
* :func:`partial_when_bytes_moved`: a failed dispatch that moved bytes is a
  partial application;
* :func:`check_partial_skips` and :func:`partial_skip_refusal`: whether a
  ``--human-task <batch>=skip`` answer can keep a stopped batch as it stands;
* :func:`resume_why`: what a stop's plain ``--resume`` does on an unchanged
  tree, from a :class:`ResumeContext`.

No I/O: ``WriteBatchScheduler`` reads what is on disk and passes it in, as a
callable where reading it costs I/O, so each fact is read only when a rule
needs it, in the order the rules ask. The rules and why:
docs/development/write-scheduler.md, "Declined items and partial
applications" and "Retry after edits".

``utils.write_batch_scheduler`` re-exports every name defined here for
reading only: patch one here, never through the scheduler
(docs/development/write-scheduler.md#where-the-schedulers-helpers-live).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Collection, Dict, List, Mapping, Optional, Sequence, Tuple

from . import stop_answers as _stop_answers
from .retry_ladder import (
    STATUS_OK,
    STATUS_REJECTED,
    STATUS_SCHEMA_INVALID,
    STATUS_UNPARSEABLE,
)
from .task_dispatch import STATUS_PARTIAL
from .batch_reply import (
    WRITE_PARTIAL,
    WRITE_POLICY_VIOLATION,
    WRITE_SCHEMA_REJECTED,
)
from .task_outcome import TaskOutcome
from .subagent_tasks import APPLY_WRITE_KINDS, declared_file_set


# -- a dispatch the verdict table never saw ----------------------------------

def classify_attempt(outcome: TaskOutcome, *, snapshot_dir: Any) -> None:
    """Give a failed dispatch that never reached the verdict table its write
    outcome, on *outcome* in place.

    The four-outcome axis is total, so a dispatch that never reached the
    classification still says which bucket it fell in. Rungs 5 and 6 are
    both "the runner did not return the batch result contract" (prose and a
    well-formed wrong object are the same failure to a consumer), so they
    share the schema-rejection outcome. ``dispatch_task``'s pre-retry check
    (T4.8) found bytes moved under an attempt it would have re-sent: the same
    outcome, and the same stop, as the table's partial application, with
    *snapshot_dir* (the pre-batch snapshot) named. Rungs 1 to 4 (no child, no
    auth, timeout, runner error) are transport failures, not write outcomes,
    and stay unlabelled; :func:`partial_when_bytes_moved` makes either a
    partial application when the batch moved bytes.
    """
    if outcome.write_outcome is not None or outcome.ok:
        return
    if outcome.status in (STATUS_SCHEMA_INVALID, STATUS_UNPARSEABLE):
        outcome.write_outcome = WRITE_SCHEMA_REJECTED
    elif outcome.status == STATUS_PARTIAL:
        outcome.write_outcome = WRITE_PARTIAL
        outcome.reason = (
            f"{outcome.reason} The pre-batch snapshot is kept at "
            f"{snapshot_dir}."
        )


def partial_when_bytes_moved(outcome: TaskOutcome, *, snapshot_dir: Any) -> None:
    """Make a failed dispatch that never reached the verdict table and moved
    bytes a partial application, on *outcome* in place.

    ``dispatch_task``'s pre-retry check makes one of an attempt that would
    have re-sent the batch, but not of the report re-ask's own failure (the
    re-ask is exempt from that check: its retry re-sends the re-ask) nor of a
    reply rung 6 never retries. So a re-ask that replied in prose again, or
    timed out on every try, ended ``unparseable_result`` / ``schema-rejection``
    or an unlabelled ``timeout`` beside the files the batch had changed (fix
    round 9). *outcome*'s ``files_touched`` is the byte comparison the
    scheduler just filled, ``unrestorable`` the moved files with no rollback
    point; when either names a file, the outcome becomes the same partial
    application the table records, with what failed kept in the reason and
    *snapshot_dir* named. A rung-7 refusal keeps its own verdict.
    """
    if outcome.ok or outcome.status in (STATUS_PARTIAL, STATUS_REJECTED):
        return
    if outcome.write_outcome not in (None, WRITE_SCHEMA_REJECTED):
        return
    moved = [str(path) for path in (outcome.files_touched or [])] + [
        str(path) for path in (outcome.unrestorable or [])
        if str(path) not in (outcome.files_touched or [])
    ]
    if not moved:
        return
    what = outcome.reason or outcome.status
    outcome.status = STATUS_PARTIAL
    outcome.write_outcome = WRITE_PARTIAL
    outcome.reason = (
        f"PARTIAL APPLICATION: {len(moved)} file(s) changed "
        f"({', '.join(moved[:5])}{', …' if len(moved) > 5 else ''}) but "
        f"the batch did not finish: {what}. The batch loop stops here, the "
        f"pre-batch snapshot is kept at {snapshot_dir}, and the phase "
        f"is NOT marked completed — an automatic revert would destroy the "
        f"half-applied state a human needs to inspect."
    )


# -- keeping a stopped batch at the user's request ----------------------------

#: What a refused ``--human-task <batch>=skip`` leaves the user (fix round
#: 18), on the refusal's printed block (:func:`check_partial_skips`) and its
#: stop headline alike.
REFUSED_SKIP_WAY_FORWARD = (
    "Resume without it to dispatch the batch again, or restore the batch "
    "first (util restore-batch) and then resume."
)


def check_partial_skips(
    answers: Sequence[str],
    *,
    kind: str,
    phase: str,
    tasks: Sequence[Mapping[str, Any]],
    evidence: Callable[[Mapping[str, Any]], Optional[str]],
) -> Tuple[Dict[str, str], List[str]]:
    """Check each ``--human-task <batch>=skip`` answer before any dispatch:
    ``({batch: why it is refused}, the refusal lines)``, both empty when
    every answer stands.

    Fix round 18 (Codex racing run 7, apply-code-fixes 08 and 08b): a batch
    applied one fix and left the other out of its report; the stop and its
    resume offered only ``--resume``, which dispatched the batch again and
    stopped the same way. The answer keeps such a batch as it stands and
    records the items it left out as skipped at the user's request. It
    applies only to an apply phase's batch of this run whose own result
    carries the stop's verdict (*evidence*: the batch's own check,
    :func:`partial_skip_refusal` over what is on disk), and anything else is
    refused (exit 3, nothing dispatched), never guessed at: keeping a batch
    the user since restored, or one that now holds other items, would
    record edits that are not there.
    """
    by_id = {str(task.get("task_id", "")): task for task in tasks}
    refused: Dict[str, str] = {}
    for task_id in answers:
        task = by_id.get(task_id)
        if kind not in APPLY_WRITE_KINDS:
            why: Optional[str] = "only an apply phase's batch takes this answer"
        elif task is None:
            why = (
                f"this run holds no batch {task_id} (its batches: "
                f"{', '.join(sorted(by_id)) or 'none'})"
            )
        else:
            why = evidence(task)
        if why:
            refused[task_id] = why
    if not refused:
        return refused, []
    return refused, [
        "",
        f"ERROR: {phase} cannot take the answer below, so nothing was "
        f"dispatched and no file was changed:",
        *(
            f"  - --human-task {task_id}=skip: {why}."
            for task_id, why in refused.items()
        ),
        REFUSED_SKIP_WAY_FORWARD,
    ]


def already_kept(verdict: Mapping[str, Any]) -> bool:
    """Whether a batch's verdict stamp is one an earlier ``=skip`` answer
    kept: ``ok`` with the items it recorded as skipped at the user's
    request."""
    return verdict.get("ok") is True and bool(verdict.get("skipped_items"))


def partial_skip_refusal(
    task_id: str,
    verdict: Any,
    *,
    result_name: str,
    expected_ids: Sequence[Any],
    fingerprint: Callable[[], str],
    counts_as_done: Callable[[], bool],
    current_digest: Callable[[str], Optional[str]],
) -> Optional[str]:
    """Why *task_id*'s stopped batch cannot be kept at the user's request, or
    ``None`` when it can (or an earlier answer already kept it,
    :func:`already_kept`).

    *verdict* is its result file's verdict stamp (anything else carries
    none); *result_name* the file's name; *expected_ids* the items this run
    holds the batch for. The rest is read only when a rule needs it, in this
    order: *fingerprint* (the batch's inputs fingerprint now), then for an
    already kept batch *counts_as_done* (whether the dispatch loop keeps
    that completion), else *current_digest* of each file the verdict
    stamped (its bytes now, against the bytes the batch left).

    A batch is kept only when it stopped as a partial application whose
    readable report left items out (``unapplied_ids``), for the same items,
    from the same inputs, with every file it moved still holding the bytes
    it left. A repeated answer belongs to the same batch, not merely the
    same positional result file: it is idempotent only when the loop will
    actually keep that completion. Its old file hashes are not compared:
    later completed batches may legitimately have edited the shared plan or
    task list.
    """
    if not isinstance(verdict, dict):
        return f"{task_id}'s result ({result_name}) carries no verdict"
    kept = already_kept(verdict)
    expected = sorted(str(i) for i in expected_ids)
    if not kept and (
        verdict.get("write_outcome") != WRITE_PARTIAL
        or not verdict.get("unapplied_ids")
    ):
        return (
            f"{task_id} did not stop as a partial application whose report "
            f"left items out (its last verdict: "
            f"{verdict.get('write_outcome') or 'none'}); only such a batch "
            f"can be kept as it stands"
        )
    recorded = verdict.get("expected_ids")
    if (
        str(verdict.get("task_id") or "") != task_id
        or not isinstance(recorded, list)
        or sorted(str(i) for i in recorded) != expected
    ):
        return (
            f"{task_id} now holds other items than the batch that stopped "
            f"(the selection changed since)"
        )
    stamped = str(verdict.get("inputs_fingerprint") or "")
    if stamped and stamped != fingerprint():
        return (
            f"the plan, the review or the batching {task_id} was made from "
            f"changed since it stopped"
        )
    if kept:
        if counts_as_done():
            return None
        return (
            f"{task_id}'s earlier kept result no longer counts as completed; "
            f"this answer cannot keep a batch that would be dispatched again"
        )
    after = verdict.get("sha256_after")
    moved = sorted(
        str(relative) for relative, digest in (
            after.items() if isinstance(after, dict) else ()
        )
        if current_digest(str(relative)) != digest
    )
    if moved:
        return (
            f"{', '.join(moved[:5])}{', …' if len(moved) > 5 else ''} "
            f"changed since {task_id} stopped (restored, or edited by "
            f"hand), so what it applied is no longer what is on disk"
        )
    return None


# -- what the plain --resume does ---------------------------------------------

@dataclass(frozen=True)
class ResumeContext:
    """What a stopped write phase knows beyond its outcomes, for
    :func:`resume_why`.

    The callables are read only when a rule needs them: *blocking_checks*
    (the checks that held tasks back, in task order) when a check held one;
    *implement_done* (the tasks ``state.json`` records done) for implement;
    *kept_on* (whether a resume on the tree as the stop leaves it keeps a
    check from running: its verdict carries that very tree) for each check
    the why judges, failed checks first.
    """

    kind: str
    #: The phase's materialized tasks.
    tasks: Sequence[Mapping[str, Any]] = ()
    #: The tasks the human-task plan skipped.
    skipped: Collection[str] = ()
    #: The tasks refused before any runner started.
    refused_before_dispatch: Collection[str] = ()
    #: The write-policy hits each refused task's paths drew.
    refused_policy_hits: Mapping[str, Sequence[Any]] = field(default_factory=dict)
    #: ``{task: the check task with findings it waits for}``.
    blocked: Mapping[str, str] = field(default_factory=dict)
    blocking_checks: Callable[[], List[str]] = list
    dependents_of: Callable[[str], List[str]] = lambda _task_id: []
    implement_done: Callable[[], int] = lambda: 0
    kept_on: Callable[..., bool] = lambda _task_id, *, failed_check: False

    def task(self, task_id: str) -> Optional[Mapping[str, Any]]:
        for task in self.tasks:
            if str(task.get("task_id", "")) == task_id:
                return task
        return None

    def undone_with(self, task_id: str) -> List[str]:
        """The tasks of this run that wait on *task_id* and are not skipped,
        manual, or outside the run."""
        manual = {
            str(t.get("task_id", "")) for t in self.tasks
            if t.get("executor_role") == "human" or t.get("is_human")
        }
        return [
            dep for dep in self.dependents_of(task_id)
            if dep not in self.skipped and dep not in manual
            and self.task(dep) is not None
        ]


def resume_why(
    outcomes: Sequence[TaskOutcome],
    failed: Sequence[TaskOutcome],
    ctx: ResumeContext,
) -> Optional[str]:
    """What a stop's plain ``--resume`` does on an unchanged tree
    (``stop_answers.compose_resume_why``, fix round 22), recorded on the stop
    as ``resume_why`` beside its ``answers``: every *failed* task, not only
    the answerable ones, since a resume dispatches a half-applied batch again
    too. A failed check task is not run again while the files are unchanged,
    and a check whose findings hold tasks back neither, each only when its
    verdict carries the tree it ran on, or the run already kept it
    (``ResumeContext.kept_on``; fix round 23: a timeout, a prose reply or a
    crash leaves no result file to stamp, and the resume runs it again).

    What the resume keeps is counted as ``status`` counted it before it moved
    here: the *outcomes* recorded ``ok``, for implement every task of the
    decomposition ``state.json`` records done, and whether a failed row moved
    bytes (fix round 23, review of round 22, relay #6).
    """
    implement = ctx.kind == "implement"
    refused = [o for o in failed if o.task_id in ctx.refused_before_dispatch]
    blocked = ctx.blocked if implement else {}
    checks = ctx.blocking_checks() if blocked else []
    kept = sum(1 for o in outcomes if o.status == STATUS_OK)
    if implement:
        kept = max(kept, ctx.implement_done())
    half_applied = any(
        o.files_touched or o.unrestorable or o.write_outcome == WRITE_PARTIAL
        for o in outcomes if not o.ok
    )
    return _stop_answers.compose_resume_why(
        refused=[o.task_id for o in refused],
        policy={
            o.task_id for o in refused
            if o.write_outcome == WRITE_POLICY_VIOLATION
        },
        outside={
            o.task_id for o in refused
            if any(getattr(hit, "outside", False)
                   for hit in ctx.refused_policy_hits.get(o.task_id) or [])
        },
        failed=[
            _stop_answers.FailedAnswerable(
                task_id=o.task_id, not_rerun=bool(o.not_rerun),
                check=implement and not declared_file_set(
                    ctx.task(o.task_id) or {})
                and (bool(o.not_rerun)
                     or ctx.kept_on(o.task_id, failed_check=True)),
            )
            for o in failed if o not in refused
        ],
        checks=checks,
        rerun_checks={
            check_id for check_id in checks
            if not ctx.kept_on(check_id, failed_check=False)
        },
        blocked=blocked,
        undone_with=ctx.undone_with,
        unit="tasks" if implement else "batches",
        kept=kept,
        half_applied=half_applied,
    )
