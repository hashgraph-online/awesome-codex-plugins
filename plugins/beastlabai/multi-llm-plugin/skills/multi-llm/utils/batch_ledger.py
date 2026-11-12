"""A write phase's batch records, read together: the verdict a result file
carries and what a resume reads back from it, the files the phase changed, and
whether the records agree.

One batch's outcome is recorded in seven places, each for a reason
(docs/development/write-scheduler.md, "A batch's records"): the result file's
``verdict`` (:func:`verdict_record`), the audit log's ``completed`` line,
``state.json``'s ``task_status`` and ``processed_<phase>``, the scheduler's
``write_batch_report.json``, the executor's ``subagent_batch_report.json``
and the ``.status.json`` write mirror. Every one keeps being written, each at
its own time, because the crash windows depend on the order. This module is
where they are read together:

* :func:`verdict_record` and :func:`outcome_from_verdict`: the verdict stamp
  and the resume skip's reading of it back, one round trip
  (:data:`VERDICT_FIELDS` says what each ``TaskOutcome`` field does in it);
* :func:`touched_files`: what a phase's batches changed, with the filter in
  the call (``include_partial``);
* :class:`BatchLedger`: one phase's records on disk, and
  :meth:`BatchLedger.disagreements`, where they differ on whether a batch
  finished or what its checks reported, or one is missing (for tests).

No writes: the scheduler stamps, saves and appends.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional

from .state_manager import (
    TASK_BATCH_CHECK_ACCEPTED_KEY,
    TASK_BATCH_CHECK_KEY,
    TASK_BATCH_CHECK_REPEATS_KEY,
    TASK_CHECK_FINDINGS_KEY,
    stamp_or_mtime,
)
from .retry_ladder import STATUS_OK
from .batch_reply import (
    WRITE_APPLIED,
    WRITE_NO_OP,
    WRITE_PARTIAL,
    check_record,
    declined_record,
    row_batch_check_accepted,
    row_batch_check_findings,
    row_batch_check_note,
    row_batch_check_repeats,
    row_check_findings,
    row_declined,
)
from .task_outcome import (
    TaskOutcome,
    batch_report_path,
)
from .subagent_tasks import APPLY_WRITE_KINDS
from .task_ledger import MIRROR_ROW_LISTS, mirror_ids
from .status_file import read_status
from .write_safety import AuditLog

__all__ = [
    "VERDICT_FIELDS",
    "BatchLedger",
    "outcome_from_verdict",
    "read_verdict_checks",
    "touched_files",
    "verdict_record",
]

#: The scheduler's own report (``write_batch_scheduler.WRITE_BATCH_REPORT_FILENAME``).
_WRITE_REPORT = "write_batch_report.json"


# -- the verdict stamp and its reading back ------------------------------------

#: What the verdict stamp does with each ``TaskOutcome`` field: ``"stamped"``
#: (written by :func:`verdict_record` and read back by
#: :func:`outcome_from_verdict`), else why not. A field added to
#: ``TaskOutcome`` fails ``tests/test_batch_ledger.py`` until it has a row
#: here, and a ``"stamped"`` field fails it unless it survives the round trip.
VERDICT_FIELDS: Dict[str, str] = {
    "task_id": "stamped",
    "kind": "the phase's: the resume skip's scheduler supplies it",
    "runner": "the resume skip names this run's invoker, which did not run it",
    "status": "stamped; a resume skips only a batch whose verdict counts as done",
    "profile": "the phase's: derived from the kind",
    "attempts": "the dispatch's own, in subagent_batch_report.json",
    "output_path": "the result file itself",
    "reason": "stamped",
    "duration_seconds": "the dispatch's own; a skip ran nothing",
    "usage": "the dispatch's own; a skip ran nothing",
    "usage_reported": "the dispatch's own; a skip ran nothing",
    "skipped": "set by the resume skip itself",
    "result_sha256": "the dispatch's own, for subagent_batch_report.json's provenance",
    "write_outcome": "stamped",
    "files_touched": "stamped",
    "summary": "the reply's own `summary`, read from the result file beside the verdict",
    "snapshot_dir": "where the rollback point lives now: the safety dir decides",
    "expected_ids": "stamped as the batch's identity; read back from the task this run holds",
    "returned_ids": "the reply's own `ids`, read from the result file beside the verdict",
    "sha256_before": "stamped",
    "sha256_after": "stamped",
    "structured_output": "the dispatch's own schema marker",
    "verification_only": "stamped",
    "runner_notes": (
        "stamped for a kept-at-request batch and a stop to read; a resume skip "
        "leaves them on the earlier run's report row, which stands in for it"
    ),
    "not_rerun": "never stamped: a check not run again is this run's decision",
    "check_findings": "stamped",
    "batch_check": "stamped",
    "batch_check_accepted": "stamped",
    "batch_check_repeats": "stamped",
    "batch_check_note": "stamped",
    "applied_without_changes": (
        "never on a verdict a resume skips: the outcome is a clean failure"
    ),
    "unrestorable": (
        "the audit line's `observed` carries what moved; a resume skip reads "
        "the verdict's rollback set"
    ),
    "ran_out_of_time": "never on a verdict a resume skips: the outcome is a partial application",
    "declined": "stamped",
    "unapplied_ids": (
        "stamped for a `--human-task <id>=skip` answer to read; a resume never "
        "skips a partial application"
    ),
    "skipped_items": "stamped",
}


def verdict_record(
    outcome: TaskOutcome,
    *,
    task: Optional[Mapping[str, Any]],
    inputs_fingerprint: Callable[[Mapping[str, Any]], str],
    tree_fingerprint: Callable[[], Optional[str]],
    sandbox_rung: Optional[str] = None,
) -> Dict[str, Any]:
    """The ``verdict`` a batch's result file carries for *outcome*
    (``WriteBatchScheduler._stamp_verdict`` writes it back onto the file).

    Its ``ok`` is the one bit resume needs: the same bit that decides the
    task's ``completed``/``failed`` status and whether an inputs binding is
    recorded. A verification-only task carries its label and check, and the
    tree it ran on (*tree_fingerprint*, read only then) when it failed moving
    nothing or reported problems, so an unchanged ``--resume`` does not run it
    again. *task* (the batch this run holds, ``None`` when it holds none)
    adds the batch's identity beyond its positional name: its id, items and
    *inputs_fingerprint*, read only then. *sandbox_rung* names the rung it
    was reached on, when there was one. Every key past the first seven is
    additive and present only when it says something.
    """
    data: Dict[str, Any] = {
        "write_outcome": outcome.write_outcome,
        "status": outcome.status,
        "ok": outcome.ok,
        "files_touched": outcome.files_touched,
        "sha256_before": outcome.sha256_before,
        "sha256_after": outcome.sha256_after,
        "reason": outcome.reason,
    }
    if outcome.verification_only:
        # The same two keys the report rows carry; a resume skip reads them
        # back so its row keeps the label.
        data["verification_only"] = True
        data["outcome_label"] = outcome.outcome_label
        if outcome.check_findings is not None:
            # The bounded findings the label rests on (the reply's own
            # `check` stays above the verdict).
            data["check"] = check_record(outcome.check_findings)
        if (
            (not outcome.ok and not outcome.files_touched and not outcome.not_rerun)
            or (outcome.ok and outcome.check_findings)
        ):
            # `CheckHolds.unchanged_since_failure`, `CheckHolds.check_findings_rerun` (fix round 11).
            data["tree_fingerprint"] = tree_fingerprint()
    if outcome.batch_check is not None:
        data["batch_check"] = check_record(outcome.batch_check)
    if outcome.batch_check_accepted:
        # Fix round 22: what it reported again of accepted findings.
        data["batch_check_accepted"] = {
            check_id: list(found)
            for check_id, found in outcome.batch_check_accepted.items()
        }
    if outcome.batch_check_repeats:
        # Fix round 28: what it reported that a check task reported.
        data["batch_check_repeats"] = {
            check_id: list(found)
            for check_id, found in outcome.batch_check_repeats.items()
        }
    if outcome.batch_check_note:
        data["batch_check_note"] = outcome.batch_check_note
    if outcome.runner_notes:
        data["runner_notes"] = outcome.runner_notes
    # Fix round 18: the items it declined, the items a partial application
    # left out of both lists (what `--human-task <id>=skip` answers), and the
    # items such an answer recorded as skipped at the user's request.
    if outcome.declined:
        data["declined"] = declined_record(outcome.declined)
    if outcome.unapplied_ids:
        data["unapplied_ids"] = list(outcome.unapplied_ids)
    if outcome.skipped_items:
        data["skipped_items"] = declined_record(outcome.skipped_items)
    if task is not None:
        # So a resume whose selection renumbered the batch finds this result
        # by its items (`ResumeEvidence.done_evidence`) and still compares the inputs.
        data["task_id"] = outcome.task_id
        data["expected_ids"] = [str(i) for i in (task.get("expected_ids") or [])]
        data["inputs_fingerprint"] = inputs_fingerprint(task)
    if sandbox_rung:
        data["sandbox_rung"] = sandbox_rung
    return data


def read_verdict_checks(outcome: TaskOutcome, verdict: Mapping[str, Any]) -> None:
    """Put back on *outcome* what a code batch's own checks reported, as its
    verdict stamp recorded it: its ``batch_check`` (only when one was
    stamped), the findings it reported again that the user accepted (fix
    round 22) or that a check task reported (fix round 28), and its note."""
    if isinstance(verdict.get("batch_check"), dict):
        outcome.batch_check = row_batch_check_findings(verdict)
    outcome.batch_check_accepted = row_batch_check_accepted(verdict)
    outcome.batch_check_repeats = row_batch_check_repeats(verdict)
    outcome.batch_check_note = row_batch_check_note(verdict)


def outcome_from_verdict(
    data: Mapping[str, Any],
    recorded: Mapping[str, Any],
    task: Mapping[str, Any],
    *,
    kind: str,
    runner: str,
    profile: str,
    output_path: str,
    files_on_record: Callable[[], List[str]],
) -> TaskOutcome:
    """The ``ok`` outcome a resume skip records for a batch an earlier run
    finished, read back from its result file *data* (the reply, with the
    ``verdict`` :func:`verdict_record` stamped on it) and the audit log's
    completion line *recorded* (``{}`` without one).

    Each field comes from the verdict first, then the audit line, for a
    result file written before the verdict carried it: the write outcome (else
    the reply's own ``status`` word), the reason, the files it verified
    (else, last, *files_on_record*: the reply's own ``files_touched``) and
    the hashes. *task* (this run's batch) gives the items; *runner* and
    *profile* are this run's.
    """
    verdict = data.get("verdict")
    if not isinstance(verdict, dict):
        verdict = {}
    task_id = str(task.get("task_id", ""))
    outcome = TaskOutcome(
        task_id=task_id, kind=kind, runner=runner,
        status=STATUS_OK, profile=profile, skipped=True,
        write_outcome=(verdict.get("write_outcome")
                       or recorded.get("write_outcome")
                       or (WRITE_NO_OP if data.get("status") == "no-op"
                           else WRITE_APPLIED)),
        summary=data.get("summary"),
        reason=verdict.get("reason") or recorded.get("reason"),
        verification_only=bool(verdict.get("verification_only")),
    )
    if outcome.verification_only and isinstance(verdict.get("check"), dict):
        # The skip keeps the earlier run's `check-findings` label.
        outcome.check_findings = row_check_findings(verdict)
    read_verdict_checks(outcome, verdict)
    if kind in APPLY_WRITE_KINDS:
        # Fix round 18: an apply batch's declined items, and the ones an
        # answer recorded as skipped, so the resumed row still names them.
        outcome.declined = row_declined(verdict)
        outcome.skipped_items = row_declined(
            {"declined": verdict.get("skipped_items")}
        )
    outcome.output_path = output_path
    # The files the earlier run verified for this batch, so a resumed run's
    # finalization (`--touched`) and summary still name them.
    if "files_touched" in verdict:
        outcome.files_touched = list(verdict["files_touched"])
    elif "files_touched" in recorded:
        outcome.files_touched = list(recorded["files_touched"])
    else:
        outcome.files_touched = files_on_record()
    outcome.expected_ids = list(task.get("expected_ids") or [])
    outcome.returned_ids = list(data.get("ids") or [])
    observed = recorded.get("observed") or {}
    outcome.sha256_before = verdict.get("sha256_before") or {
        path: row.get("sha256_before") for path, row in observed.items()
    }
    outcome.sha256_after = verdict.get("sha256_after") or {
        path: row.get("sha256_after") for path, row in observed.items()
    }
    return outcome


# -- what a phase changed --------------------------------------------------------

def _field(row: Any, name: str) -> Any:
    if isinstance(row, Mapping):
        return row.get(name)
    return getattr(row, name, None)


def _row_finished(row: Any) -> bool:
    if isinstance(row, Mapping):
        return row.get("status") == STATUS_OK
    return bool(getattr(row, "ok", False))


def touched_files(rows: Iterable[Any], *, include_partial: bool) -> List[str]:
    """Every file the *rows* verifiably changed, de-duplicated in first-seen
    order: the ``files_touched`` (the post-run byte comparison, never the
    runner's claim) of each ``ok`` row, and with *include_partial* of each
    partial application too.

    A row is a report row (a mapping: ``status``, ``write_outcome``,
    ``files_touched``) or a ``TaskOutcome`` (``ok``). Which rows and which
    filter is the caller's: ``tracked_files`` takes the ``ok`` rows only, so
    a stopped batch's half-applied edits are never recorded as the phase's
    code; the files an apply hands back for inspection
    (``ApplyPhaseReport.touched_files``, the improve workflow's summary)
    include the partial ones, whose edits the stop keeps. A path that is not
    a non-empty string is skipped.
    """
    touched: List[str] = []
    for row in rows:
        if not (_row_finished(row) or (
            include_partial and _field(row, "write_outcome") == WRITE_PARTIAL
        )):
            continue
        paths = _field(row, "files_touched")
        for path in paths if isinstance(paths, (list, tuple)) else ():
            if isinstance(path, str) and path and path not in touched:
                touched.append(path)
    return touched


# -- one phase's records, read together ------------------------------------------

class BatchLedger:
    """A write phase's batch records on disk, read-only. Each file is read
    when first asked for and kept for this object's life."""

    def __init__(self, phase_dir: Any) -> None:
        self.phase_dir = Path(phase_dir)
        self._report: Any = None
        self._read = False

    @property
    def report_path(self) -> Path:
        return self.phase_dir / _WRITE_REPORT

    def report(self) -> Optional[Dict[str, Any]]:
        """``write_batch_report.json``, or ``None`` when it is missing or
        unreadable."""
        if not self._read:
            self._read = True
            try:
                self._report = json.loads(self.report_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                self._report = None
        return self._report if isinstance(self._report, dict) else None

    def rows(self) -> Optional[List[Any]]:
        """The report's task rows (earlier runs' first, each flagged
        ``from_earlier_run``), or ``None`` when there is no readable report
        with a row list."""
        report = self.report()
        rows = report.get("tasks") if report is not None else None
        return rows if isinstance(rows, list) else None

    def written_at(self) -> Any:
        """When the report was written: its ``written_at``, else the file's
        mtime (``state_manager.stamp_or_mtime``)."""

        report = self.report() or {}
        return stamp_or_mtime(report.get("written_at"), self.report_path)

    def touched(self, *, include_partial: bool) -> List[str]:
        """:func:`touched_files` over every report row."""
        return touched_files(self.rows() or [], include_partial=include_partial)

    # -- the agreement check ---------------------------------------------------

    def disagreements(self, state: Optional[Mapping[str, Any]] = None) -> List[str]:
        """Where this phase's records disagree, or one a batch should have is
        missing, one line each; ``[]`` when they agree.

        For tests: the records a characterisation run leaves when it ends
        must agree, which turns the claim "the records cannot disagree" into
        a check (a run killed mid-way can leave one behind the others; the
        crash windows are the scheduler's). The report's rows are the
        reference. Each of this run's rows has:

        * a row in ``subagent_batch_report.json`` and in the ``.status.json``
          write mirror, each with the row's status, and the mirror's row its
          check facts (:func:`_check_facts`): the check's findings and the
          code batch's own failing check on the row, the accepted and
          repeated findings' checks in the mirror's maps;
        * for a row a runner ran (``attempt_count`` above 0), the audit
          log's last ``completed`` line for the batch, with its status.

        Every row, this run's or an earlier run's, has the result file's
        verdict ``ok`` (a row with a result file) and, with *state* (the
        ``state.json`` dict), its ``task_status`` (``completed`` for a
        finished row, ``failed`` for any other; a task with no entry is one
        line), each of an apply batch's items a ``processed_<phase>`` record,
        ``failed`` exactly when the batch did not finish (an item another
        batch recorded last is that batch's), and an implement task's
        ``task_check_findings``, ``task_batch_check``,
        ``task_batch_check_accepted`` and ``task_batch_check_repeats`` its
        check facts. An older mirror (written while it carried the
        :data:`~utils.task_ledger.MIRROR_ROW_LISTS` lists beside its rows)
        has each list as its rows say it.

        Absent, and said so here: an earlier run's row has no row in this
        run's executor report or mirror (they hold the resume skip's row in
        its place, or nothing for a batch this run did not hold); a batch
        that never ran has no row anywhere, the report's included; a row not
        ``ok`` has no check facts (a record other than ``completed`` clears
        them), whatever its dispatch reported; a mirror written after the
        lists moved to its rows records none of them. A record missing whole
        is one line, not one per row.
        """

        report = self.report()
        rows = self.rows()
        if report is None or rows is None:
            return [f"{self.report_path.name}: missing or unreadable"]
        kind = str(report.get("kind") or "")
        found: List[str] = []

        def disagree(task_id: str, where: str, says: Any, ok: bool) -> None:
            found.append(
                f"{task_id}: {_WRITE_REPORT} says {'ok' if ok else 'not ok'}, "
                f"{where} says {says}"
            )

        def differ(task_id: str, fact: str, where: str, says: Any, expected: Any) -> None:
            found.append(
                f"{task_id}: {_WRITE_REPORT} says {fact} {expected!r}, "
                f"{where} says {says!r}"
            )

        executor_path = batch_report_path(str(self.phase_dir), kind)
        executor_name = Path(executor_path).name
        executor_document = _read_json(executor_path)
        executor_rows = (
            _rows_by_id(executor_document) if isinstance(executor_document, dict) else None
        )
        mirror_where = ".status.json write_subagents"
        mirror = ((read_status(str(self.phase_dir)).get("progress") or {})
                  .get("write_subagents"))
        mirror = mirror if isinstance(mirror, dict) else None
        mirror_rows = _rows_by_id(mirror) if mirror is not None else None
        audit = AuditLog(str(self.phase_dir))
        processed = (
            (state or {}).get(f"processed_{self.phase_dir.name}") or {}
        )
        statuses = (state or {}).get("task_status") or {}
        missing_whole: List[str] = []

        for row in rows:
            if not isinstance(row, dict):
                continue
            task_id = str(row.get("task_id") or "")
            ok = row.get("status") == STATUS_OK
            facts = _check_facts(row)
            this_run = not row.get("from_earlier_run")
            if this_run:
                for where, by_id in (
                    (executor_name, executor_rows), (mirror_where, mirror_rows),
                ):
                    if by_id is None:
                        if where not in missing_whole:
                            missing_whole.append(where)
                        continue
                    other = by_id.get(task_id)
                    if other is None:
                        found.append(f"{task_id}: {where} has no row")
                        continue
                    if (other.get("status") == STATUS_OK) != ok:
                        disagree(task_id, where, other.get("status"), ok)
                if mirror is not None and task_id in (mirror_rows or {}):
                    for fact, says in _mirror_check_facts(
                        mirror, mirror_rows[task_id], task_id,
                    ).items():
                        expected = facts[fact]
                        if fact in _MIRROR_BY_CHECK:
                            expected = sorted(expected)
                        if says != expected:
                            differ(task_id, fact, mirror_where, says, expected)
                if int(row.get("attempt_count") or 0) > 0:
                    line = audit.completion_for(
                        task_id, expected_ids=row.get("expected_ids") or None)
                    if line is None:
                        found.append(f"{task_id}: the audit has no completed line")
                    elif (line.get("status") == STATUS_OK) != ok:
                        disagree(task_id, "the audit's completed line", line.get("status"), ok)
            output_path = row.get("output_path")
            if output_path and os.path.isfile(str(output_path)):
                verdict = (_read_json(str(output_path)) or {}).get("verdict")
                if isinstance(verdict, dict) and verdict.get("ok") is not ok:
                    disagree(task_id, f"{Path(str(output_path)).name}'s verdict",
                             f"ok={verdict.get('ok')}", ok)
            if state is None:
                continue
            if task_id not in statuses:
                found.append(f"{task_id}: state.json task_status has no entry")
            elif statuses[task_id] != ("completed" if ok else "failed"):
                disagree(task_id, "state.json task_status", statuses[task_id], ok)
            if kind == "implement":
                for fact, key in _STATE_CHECK_KEYS.items():
                    recorded = (state.get(key) or {}).get(task_id)
                    says = recorded if recorded is not None else type(facts[fact])()
                    if says != facts[fact]:
                        differ(task_id, fact, f"state.json {key}", says, facts[fact])
            if kind in APPLY_WRITE_KINDS:
                for item in row.get("expected_ids") or []:
                    record = processed.get(str(item))
                    if not isinstance(record, dict):
                        found.append(f"{task_id}: processed item {item} has no record")
                        continue
                    details = record.get("details") or {}
                    if str(details.get("task_id") or task_id) != task_id:
                        continue
                    if (record.get("status") == "failed") == ok:
                        disagree(task_id, f"processed item {item}", record.get("status"), ok)
        found.extend(f"{where}: missing or unreadable" for where in missing_whole)
        mirror_tasks = mirror.get("tasks") if mirror is not None else None
        for key in MIRROR_ROW_LISTS:
            if mirror is None or key not in mirror:
                continue
            rebuilt = mirror_ids(
                {"tasks": mirror_tasks if isinstance(mirror_tasks, list) else []}, key)
            if [str(i) for i in mirror[key] or []] != [str(i) for i in rebuilt]:
                found.append(f"{mirror_where}: {key} {mirror[key]} against its rows' {rebuilt}")
        return found


#: A row's check facts and the ``state.json`` key each is recorded under for
#: an implement task (:meth:`BatchLedger.disagreements`).
_STATE_CHECK_KEYS: Dict[str, str] = {
    "check findings": TASK_CHECK_FINDINGS_KEY,
    "own-check findings": TASK_BATCH_CHECK_KEY,
    "accepted findings": TASK_BATCH_CHECK_ACCEPTED_KEY,
    "repeated findings": TASK_BATCH_CHECK_REPEATS_KEY,
}

#: The check facts the write mirror records by check, as ``{task_id: [check
#: id, ...]}`` beside its rows: the findings themselves are the report's and
#: ``state.json``'s.
_MIRROR_BY_CHECK: Dict[str, str] = {
    "accepted findings": "batch_check_accepted",
    "repeated findings": "batch_check_repeats",
}


def _check_facts(row: Mapping[str, Any]) -> Dict[str, Any]:
    """What a report row says its checks reported, as every other record
    keeps it: the check's findings, the code batch's own failing check, and
    the findings it reported again that the user accepted or a check task
    reported, by check. A row not ``ok`` has none."""
    if row.get("status") != STATUS_OK:
        return {"check findings": [], "own-check findings": [],
                "accepted findings": {}, "repeated findings": {}}
    return {
        "check findings": row_check_findings(dict(row)),
        "own-check findings": row_batch_check_findings(dict(row)),
        "accepted findings": row_batch_check_accepted(dict(row)),
        "repeated findings": row_batch_check_repeats(dict(row)),
    }


def _mirror_check_facts(
    mirror: Mapping[str, Any], row: Mapping[str, Any], task_id: str,
) -> Dict[str, Any]:
    """The write mirror's check facts for *task_id*: its row's
    ``check_findings`` and ``batch_check_findings`` (what the mirror's
    :data:`~utils.task_ledger.MIRROR_ROW_LISTS` lists are rebuilt from), and
    the checks its ``batch_check_accepted`` and ``batch_check_repeats`` maps
    name for it, sorted."""
    facts: Dict[str, Any] = {
        "check findings": list(row.get("check_findings") or []),
        "own-check findings": list(row.get("batch_check_findings") or []),
    }
    for fact, key in _MIRROR_BY_CHECK.items():
        by_task = mirror.get(key)
        named = by_task.get(task_id) if isinstance(by_task, dict) else None
        facts[fact] = sorted(str(c) for c in named) if isinstance(named, list) else []
    return facts


def _read_json(path: str) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _rows_by_id(document: Any) -> Dict[str, Dict[str, Any]]:
    """``{task_id: its last row}`` over a document's ``tasks`` (a report, a
    write mirror)."""
    rows = document.get("tasks") if isinstance(document, dict) else None
    return {
        str(row.get("task_id")): row
        for row in (rows if isinstance(rows, list) else [])
        if isinstance(row, dict) and row.get("task_id")
    }
