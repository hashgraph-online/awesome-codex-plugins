"""The executor's records: one attempt, one task's outcome, one batch's
report, and the errors a dispatch raises.

:class:`Attempt`, :class:`TaskOutcome` and :class:`BatchReport` (written to
``subagent_batch_report.json``, or the per-kind name
:func:`batch_report_path` gives), and :class:`ExecutorError` with its
subclasses :class:`RunnerRejected`, :class:`ResultRejected` and
:class:`BatchFailed`. It reads the reply words from ``batch_reply`` and
writes through ``failure_capture``.

``utils.subagent_executor`` re-exports every name defined here for reading
only: patch one here, never through the executor
(docs/development/delegation.md#where-the-executors-helpers-live).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .providers.base import PROFILE_AGENT_READONLY
from .retry_ladder import (  # noqa: F401 - re-exported, see below
    FATAL_STATUSES,
    RUNG_BY_STATUS,
    STATUS_OK,
)
from . import batch_reply as _batch_reply
from . import failure_capture as _failure_capture
from .redact import redact_text


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: The executor-owned bookkeeping file beside the immutable task JSON (D3i).
#: The task file stays a hash-bound snapshot, so attempt counts live here.
BATCH_REPORT_FILENAME = "subagent_batch_report.json"

#: The one READ_KINDS member whose dispatch can land in a phase dir a WRITE_KINDS
#: dispatch also writes to (F6, 2026-09-16): every apply phase's unattended
#: judging pass runs on this, the read-path executor, *before* the same phase's
#: own write batches ever touch the dir. Every other read kind (validation,
#: revalidation, consolidation, salvage, task_generation) owns its phase dir
#: alone, so the bare name below is unambiguous for them and stays their
#: report's name. Without this, a judged decision — the one subagent output a
#: human is most likely to want to re-examine — had its report silently
#: overwritten the moment the write phase ran (both write to the identical
#: path), and its argv/duration/usage survived nowhere.
KINDS_SHARING_A_WRITE_PHASE_DIR = frozenset({"human_decision_judge"})


def _batch_report_filename(kind: str) -> str:
    """Which filename this ``kind``'s :class:`BatchReport` writes to (F6).

    Every kind but the one in :data:`KINDS_SHARING_A_WRITE_PHASE_DIR` keeps the
    bare :data:`BATCH_REPORT_FILENAME` — byte-identical for every existing
    reader (``run_status``, ``_authoritative_validator_runner``, the
    reaggregation-glob exclude lists, every test that opens the file by name).
    Only a kind that can share a phase dir with a different dispatch's report
    gets a name that says which report it is.
    """
    if kind in KINDS_SHARING_A_WRITE_PHASE_DIR:
        return f"subagent_batch_report_{kind}.json"
    return BATCH_REPORT_FILENAME


def batch_report_path(phase_dir: str, kind: str) -> str:
    """Where ``kind``'s batch report lives under ``phase_dir`` — the public form.

    The naming rule belongs to this module (F6, 2026-09-17), so a reader
    outside it asks rather than spelling a filename out: ``apply_orchestrator_
    base`` hands the judge's report to the host through ``output_files``, and a
    hand-typed copy of the name would drop that key silently the day the rule
    moves.
    """
    return os.path.join(phase_dir, _batch_report_filename(kind))


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class ExecutorError(Exception):
    """Something the executor refuses to do. Exit 3 ("needs a human", D6)."""

    exit_code = 3

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class RunnerRejected(ExecutorError):
    """A configured runner spec cannot serve this phase (one rejection surface).

    Rendered by :func:`_render_runner_rejection` so the wording cannot drift per
    call site: the offending key, the spec as written, a reason code
    (``unknown_provider`` | ``missing_capability`` | ``missing_profile``), that
    code's explanation, the runners on this host that *would* satisfy the request,
    and the fix.
    """

    def __init__(self, message: str, *, key: str = "", spec: str = "",
                 reason_code: str = "", detail: str = "") -> None:
        super().__init__(message)
        self.key = key
        self.spec = spec
        self.reason_code = reason_code
        #: The provider's own words behind the refusal, already redacted — the
        #: probe tail carrying a "Did you mean" list, say — kept as a field so
        #: the exit-3 handler can print it as a line of its own (D4 step 5)
        #: rather than leaving the reader to find it inside ``message``.
        self.detail = detail


class ResultRejected(ExecutorError):
    """One task's result cannot be used. Carries the D3k status it lands on."""

    def __init__(self, message: str, status: str) -> None:
        super().__init__(message)
        self.status = status


class BatchFailed(ExecutorError):
    """A batch had failed or incomplete tasks, so the phase must not reaggregate."""

    def __init__(self, message: str, report: "BatchReport") -> None:
        super().__init__(message)
        self.report = report


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

@dataclass
class Attempt:
    """One dispatch attempt of one task."""

    index: int
    status: str
    exit_code: Optional[int] = None
    duration_seconds: float = 0.0
    error: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    capture_path: Optional[str] = None
    #: Set on an attempt that carried the schema-repair re-ask (the ladder's
    #: rule 7) — :data:`REPAIR_SCHEMA_INVALID` — so the batch report says which
    #: attempt was the second question rather than a second try of the first.
    repair: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "attempt": self.index,
            "status": self.status,
            "duration_seconds": round(self.duration_seconds, 3),
        }
        if self.exit_code is not None:
            out["exit_code"] = self.exit_code
        if self.error:
            out["error"] = self.error
        if self.usage:
            out["usage"] = dict(self.usage)
        if self.capture_path:
            out["capture"] = self.capture_path
        if self.repair:
            out["repair"] = self.repair
        return out


@dataclass
class TaskOutcome:
    """The row ``subagent_batch_report.json`` records for one ``task_id``."""

    task_id: str
    kind: str
    runner: str
    status: str
    profile: str = PROFILE_AGENT_READONLY
    attempts: List[Attempt] = field(default_factory=list)
    output_path: Optional[str] = None
    reason: Optional[str] = None
    duration_seconds: float = 0.0
    usage: Optional[Dict[str, Any]] = None
    usage_reported: bool = False
    skipped: bool = False
    #: The sha256 of the result bytes this dispatch persisted for the reply it
    #: accepted, or of those a skipped task was found complete with; ``None``
    #: when it holds none. Never serialized: it is the hash ``batch_provenance``
    #: records, never the file hashed again (docs/development/review-results.md,
    #: "Consuming checked bytes").
    result_sha256: Optional[str] = None
    #: D3g, write kinds only: which of the four outcomes the snapshot/diff
    #: classification landed on. Its own axis rather than a status, because
    #: the status says whether the loop goes on and this says what the bytes did.
    write_outcome: Optional[str] = None
    #: The files the post-run byte comparison actually observed as changed — the
    #: set the write policy is enforced against, never the runner's own claim.
    files_touched: List[str] = field(default_factory=list)
    #: The `summary` line lifted from the batch result JSON, for the prior-changes
    #: append. Never a compressed chat message.
    summary: Optional[str] = None
    #: Where this task's pre-batch snapshot lives, so an exit-3 message can name
    #: the restore command instead of describing it.
    snapshot_dir: Optional[str] = None
    #: F9: write kinds only, alongside `write_outcome` — the batch's own
    #: declared item ids and the ids the runner's reply actually returned, so
    #: `write_batch_report.json` and this row's own `subagent_batch_report.json`
    #: (they serialize the same `TaskOutcome`) can answer "did every item come
    #: back?" without re-deriving it from `subagent_audit.jsonl` or the
    #: per-batch result file.
    expected_ids: List[str] = field(default_factory=list)
    returned_ids: List[str] = field(default_factory=list)
    #: F9: the pre-batch snapshot's own before/after hashes for every file the
    #: post-run sweep observed (declared or not), keyed by repo-relative path —
    #: the same evidence `subagent_audit.jsonl`'s `observed.<file>.sha256_*`
    #: carries, so the hash chain's contiguity is checkable from this report
    #: alone.
    sha256_before: Dict[str, Optional[str]] = field(default_factory=dict)
    sha256_after: Dict[str, Optional[str]] = field(default_factory=dict)
    #: §4.2.1's marker for a schema-carrying dispatch: ``native`` (the CLI's own
    #: ``structured_output`` key, conformant), ``recovered`` (the document came
    #: out of the prose answer and validated against the same schema file) or
    #: ``unvalidated`` (no schema was in play). ``None`` — and therefore absent
    #: from the report row — for every kind with no schema phase, which is what
    #: keeps ``subagent_batch_report.json`` byte-identical off this path.
    structured_output: Optional[str] = None
    #: An ``implement`` dispatch that declared no files (the scheduler's
    #: ``_verification_only``): its write outcome reads as
    #: :func:`write_outcome_label` says — ``verified`` for a ``no-op``.
    verification_only: bool = False
    #: The runner's own ``notes`` for a write batch (what a check reported:
    #: the validator's lines, the failing command), bounded. Carried so the
    #: stop message and a later ``--resume`` can say what failed rather than
    #: only that it did (racing re-run 3, 2026-10-05).
    runner_notes: Optional[str] = None
    #: A resumed verification-only task that was NOT dispatched again because
    #: nothing in the repository changed since it failed (the scheduler's
    #: unchanged-tree guard). No child ran, so no metric is recorded for it.
    not_rerun: bool = False
    #: A verification-only task's structured check result
    #: (:func:`check_findings_from`): ``None`` when its reply carried none,
    #: ``[]`` when the check passed, else what the check found. Non-empty on a
    #: ``no-op`` makes the label ``check-findings`` (racing re-run 4).
    check_findings: Optional[List[str]] = None
    #: A code-writing batch's own ``check`` (:func:`batch_check_findings`):
    #: the checks it ran on its edits. ``None`` when its reply reported none,
    #: ``[]`` when they passed, else what failed. Its own axis, never
    #: ``check_findings``: a write task whose test fails holds nothing back,
    #: but an ``ok`` row carrying findings is never reported as a plain
    #: success (fix round 14).
    batch_check: Optional[List[str]] = None
    #: The own-check findings of an implement task that only repeat what the
    #: user accepted for a check (``--human-task <check>=done``), by check id
    #: (``check_records.split_accepted_findings``, fix round 22): taken
    #: out of ``batch_check``, so they never make the task's own failure, and
    #: named beside that check's accepted findings instead. Empty otherwise.
    batch_check_accepted: Dict[str, List[str]] = field(default_factory=dict)
    #: The own-check findings of an implement task that are the same
    #: findings a check task of the run reported (the strict comparison of
    #: ``check_records.split_repeated_findings``), by that check's id
    #: (``check_records.repeated_findings_for``, fix round 28, live
    #: run 12 OpenCode accept 01: T001 ran T002's release check and was
    #: blamed for T002's finding). Taken out of ``batch_check`` whichever of
    #: the two finished first, and named beside that check's findings.
    batch_check_repeats: Dict[str, List[str]] = field(default_factory=dict)
    #: The code batch's own words about its checks (its ``check.note``,
    #: :func:`batch_check_note`, fix round 28): recorded and shown beside
    #: the check, never a finding. ``None`` when it gave none.
    batch_check_note: Optional[str] = None
    #: A write batch whose reply said ``applied`` while no byte moved, after
    #: its one re-send (the ladder's rule 9): a ``clean-failure`` that is
    #: never ``ok``, worded on the stop as a change that did not land (fix
    #: round 14). ``False`` for every other outcome.
    applied_without_changes: bool = False
    #: The files this dispatch moved that have no rollback point: observed by
    #: the post-run sweep outside the declared set, with no pre-run bytes in
    #: the rollback store (a path the write policy denies, a file over the
    #: per-file cap or past the store's budget, one unreadable before the
    #: run). Never in ``files_touched``, which ``util restore-batch`` reads,
    #: but moved all the same (fix round 15: a partial application that moved
    #: only such a file was announced "Nothing was half-applied").
    unrestorable: List[str] = field(default_factory=list)
    #: Killed at its time limit (``driver.subagent_timeout_s``, else the
    #: runner's ``default_timeout``) after its edits landed: a partial
    #: application whose stop says the edits are kept (fix round 16).
    ran_out_of_time: bool = False
    #: An apply batch's items it deliberately left unapplied, ``{id: reason}``
    #: in the batch's order (:func:`declined_items`, fix round 18). Never
    #: counted as applied, named on every surface, and a batch whose every
    #: item is applied or declined is complete.
    declined: Dict[str, str] = field(default_factory=dict)
    #: A partial application whose readable report attests some items and
    #: leaves these out of both ``ids`` and ``declined`` (fix round 18): the
    #: items ``--human-task <id>=skip`` records as skipped at the user's
    #: request, keeping what the batch applied. Empty for every other outcome,
    #: and so the stop offers that answer only here.
    unapplied_ids: List[str] = field(default_factory=list)
    #: The items a ``--human-task <id>=skip`` answer recorded as skipped at
    #: the user's request when it kept the batch as it stood, ``{id:
    #: reason}`` (fix round 18). Never counted as applied.
    skipped_items: Dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status == STATUS_OK

    @property
    def bytes_moved(self) -> bool:
        """Whether this dispatch left any file changed: the rollback set
        (``files_touched``) or a moved file with no rollback point."""
        return bool(self.files_touched or self.unrestorable)

    @property
    def outcome_label(self) -> Optional[str]:
        """The word every surface shows for this outcome (:func:`write_outcome_label`)."""
        return _batch_reply.write_outcome_label(
            self.write_outcome, self.verification_only, self.check_findings,
        )

    @property
    def stops_the_loop(self) -> bool:
        """Whether this outcome forbids dispatching the next batch (D3g/D3n)."""
        return self.write_outcome in _batch_reply.WRITE_STOP_OUTCOMES

    @property
    def rung(self) -> Optional[int]:
        return RUNG_BY_STATUS.get(self.status)

    @property
    def repair(self) -> Optional[str]:
        """The re-ask this task's dispatch sent (the ladder's rule 7), if any.

        The attempt that carried it already says so; the row says it too, so a
        reader of ``subagent_batch_report.json`` sees ``repair:
        schema_invalid`` beside the task's final status without walking its
        attempts (2026-10-05: only ``attempt_count: 2`` showed it).
        """
        for attempt in self.attempts:
            if attempt.repair:
                return attempt.repair
        return None

    @property
    def fatal(self) -> bool:
        return self.status in FATAL_STATUSES

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "task_id": self.task_id,
            "kind": self.kind,
            "runner": self.runner,
            "profile": self.profile,
            "status": self.status,
            "attempt_count": len(self.attempts),
            "duration_seconds": round(self.duration_seconds, 3),
        }
        if self.repair:
            out["repair"] = self.repair
        if self.rung is not None:
            out["rung"] = self.rung
        if self.output_path:
            out["output_path"] = self.output_path
        if self.reason:
            out["reason"] = self.reason
        if self.skipped:
            out["skipped"] = True
        if self.structured_output:
            out["structured_output"] = self.structured_output
        if self.write_outcome:
            out["write_outcome"] = self.write_outcome
            if self.verification_only:
                # Additive and only here, so every other row is unchanged.
                out["verification_only"] = True
                out["outcome_label"] = self.outcome_label
                if self.check_findings is not None:
                    out["check"] = _batch_reply.check_record(self.check_findings)
            if self.batch_check is not None:
                # Additive and only here, so a row whose reply ran no check
                # is unchanged.
                out["batch_check"] = _batch_reply.check_record(self.batch_check)
            if self.batch_check_accepted:
                # Additive and only here (fix round 22).
                out["batch_check_accepted"] = {
                    str(check_id): list(found)
                    for check_id, found in self.batch_check_accepted.items()
                }
            if self.batch_check_repeats:
                # Additive and only here (fix round 28).
                out["batch_check_repeats"] = {
                    str(check_id): list(found)
                    for check_id, found in self.batch_check_repeats.items()
                }
            if self.batch_check_note:
                # Additive and only here (fix round 28).
                out["batch_check_note"] = self.batch_check_note
            if self.runner_notes:
                out["runner_notes"] = self.runner_notes
            if self.not_rerun:
                out["not_rerun"] = True
            if self.applied_without_changes:
                out["applied_without_changes"] = True
            out["files_touched"] = list(self.files_touched)
            if self.unrestorable:
                # Additive and only here (fix round 15).
                out["unrestorable"] = list(self.unrestorable)
            if self.declined:
                # Additive and only here (fix round 18).
                out["declined"] = _batch_reply.declined_record(self.declined)
            if self.unapplied_ids:
                out["unapplied_ids"] = list(self.unapplied_ids)
            if self.skipped_items:
                out["skipped_items"] = _batch_reply.declined_record(self.skipped_items)
            if self.summary:
                out["summary"] = self.summary
            if self.snapshot_dir:
                out["snapshot_dir"] = self.snapshot_dir
            # F9: verification evidence, present on every write outcome
            # (`expected_ids`/`sha256_*` even when empty — an empty pair is
            # itself evidence, e.g. an `implement` task with no declared file).
            out["expected_ids"] = list(self.expected_ids)
            out["returned_ids"] = list(self.returned_ids)
            out["sha256_before"] = dict(self.sha256_before)
            out["sha256_after"] = dict(self.sha256_after)
        if self.usage_reported:
            out["usage"] = dict(self.usage or {})
        else:
            out["usage_reported"] = False
        if self.attempts:
            out["attempts"] = [a.to_dict() for a in self.attempts]
        return out


@dataclass
class BatchReport:
    """Every ``task_id`` in a batch with its status, attempts and runner (D3i)."""

    phase: str = ""
    kind: str = ""
    phase_dir: str = ""
    task_file: Optional[str] = None
    outcomes: List[TaskOutcome] = field(default_factory=list)
    ceilings: Dict[str, Any] = field(default_factory=dict)
    runner_versions: Dict[str, str] = field(default_factory=dict)
    #: The one substitution the resolution ladder is allowed to make silently at
    #: dispatch time, recorded so it is not silent after the fact:
    #: ``{"from", "reason", "to", "layer"}`` when the host session's own model
    #: failed preflight and the batch fell through to the next rung (see
    #: :func:`_preflight_batch_runners`). ``None`` on every ordinary run.
    runner_fallback: Optional[Dict[str, str]] = None
    #: §7.3a: per-output provenance, ``{task_id: {task_id, kind, round, runner,
    #: sha256}}`` for every result file this batch (or, carried forward, an
    #: earlier dispatch of the same round) persisted. ``sha256`` is over the
    #: file's bytes at the moment the executor recorded it, and ``round`` is
    #: :func:`subagent_tasks.task_round` of the batch's task list, so the merge
    #: can tell a file the executor's runner wrote from one rewritten by hand or
    #: by another host since — by content, never by mtime. Empty (and absent
    #: from the report) when nothing was persisted.
    batch_provenance: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    #: :func:`_pin_sha256` of the task list this report dispatched. A recorded
    #: runner is a pin only for a re-dispatch of the *same* round and inputs
    #: (:func:`_recorded_runners`); a report that carries no digest (written before
    #: it existed) pins as it always did. Empty means "not recorded".
    pin_sha256: str = ""
    invoker: str = "executor"

    @property
    def ok(self) -> bool:
        """True only when every task produced a schema-valid result file."""
        return bool(self.outcomes) and all(o.ok for o in self.outcomes)

    @property
    def failed(self) -> List[TaskOutcome]:
        return [o for o in self.outcomes if not o.ok]

    def counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for outcome in self.outcomes:
            counts[outcome.status] = counts.get(outcome.status, 0) + 1
        return counts

    def usage_totals(self) -> Dict[str, Any]:
        """Partial sum **plus** the count of tasks with no usage data (D3j).

        Never a total that pretends to be complete: a batch mixing a
        usage-reporting runner with a duration-only one reports both numbers.
        """
        totals: Dict[str, Any] = {}
        missing = 0
        for outcome in self.outcomes:
            if not outcome.usage_reported or not outcome.usage:
                missing += 1
                continue
            for key, value in outcome.usage.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    totals[key] = totals.get(key, 0) + value
        result: Dict[str, Any] = dict(totals)
        result["tasks_without_usage"] = missing
        result["attempts"] = sum(len(o.attempts) for o in self.outcomes)
        return result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_version": 1,
            "invoker": self.invoker,
            "phase": self.phase,
            "kind": self.kind,
            "task_file": self.task_file,
            "ceilings": dict(self.ceilings),
            "runner_versions": dict(self.runner_versions),
            **({"runner_fallback": dict(self.runner_fallback)}
               if self.runner_fallback else {}),
            # Always present, even empty: `_recorded_provenance` reads an absent
            # key as a pre-§7.3a report and falls back to the legacy per-row
            # runners, so `{}` (no provenance survives) must stay distinguishable.
            "batch_provenance": {
                task_id: dict(row) for task_id, row in self.batch_provenance.items()
            },
            **({"pin_sha256": self.pin_sha256} if self.pin_sha256 else {}),
            "counts": self.counts(),
            "usage": self.usage_totals(),
            "tasks": [o.to_dict() for o in self.outcomes],
        }

    def write(self, phase_dir: Optional[str] = None) -> str:
        """Write this report atomically (F6: :func:`_batch_report_filename`
        picks the name); return its path.

        The third of §4.5.3's four sinks — six planted shapes × fifteen rows,
        carried in the ``reason`` and per-attempt ``error`` strings that quote a
        provider's stream. Redaction sits on the write rather than on
        :meth:`to_dict`, so it covers every field a failure record grows without
        a per-field list to keep in step.
        """
        target_dir = phase_dir or self.phase_dir
        path = os.path.join(target_dir, _batch_report_filename(self.kind))
        _failure_capture._atomic_write_json(path, _failure_capture._redact_json(self.to_dict()))
        return path

    def failure_summary(self) -> List[str]:
        """One line per failure, for the phase's stdout summary (D3i).

        This is the *rendering* half of §4.5.3's fourth sink — the exit-3 block
        prints these lines, and under ``--detach`` they are
        ``orchestrator-run.log``. ``_classify_failed_run`` redacts the reason it
        builds, but rungs 4–6 take theirs from an adapter's own error string,
        which is provider output like any other; redacting here covers every rung
        rather than the two that quote a stream by name.
        """
        lines = []
        for outcome in self.failed:
            rung = outcome.rung
            rung_text = f"rung {rung}" if rung is not None else "no rung"
            lines.append(redact_text(
                f"  - {outcome.task_id}: {outcome.status} ({rung_text}, "
                f"{len(outcome.attempts)} attempt(s), runner {outcome.runner}) "
                f"{outcome.reason or ''}".rstrip()
            ))
        return lines
