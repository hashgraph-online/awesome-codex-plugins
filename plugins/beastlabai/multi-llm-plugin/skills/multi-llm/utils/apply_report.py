"""The executor leg's closing report of one apply phase.

What an apply phase prints, writes and hands back once its write batches
ran: the outcome block, ``{phase}/summary.md``, the notes a host relays,
the artifact record, the ``summary_file`` patch of the batch report and the
decisions overlay on the review report. :class:`ApplyPhaseReport` reads only
the data it is built with (``ApplyOrchestratorBase.phase_report`` gathers
it), so it changes nothing on the phase that built it. See
docs/development/write-scheduler.md and docs/development/review-results.md.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from .cli_common import record_artifacts
from .human_decisions import (
    is_judge_source,
    judge_outcome,
    judge_source_label,
    judge_status_label,
)
from . import scope_apply as _scope
from .state_manager import StateManager
from .text_clip import join_clauses
from .unattended import AGENT_DECIDE_FLAG
from . import detach as _detach
from . import cli_common as _cli
from . import run_record as _run_record
from . import failure_capture
from .git_utils import find_git_entry_root
from .batch_ledger import touched_files
from .write_safety import repo_root_for_report
from .task_outcome import batch_report_path
from .batch_reply import (
    batch_check_could_not_run,
    row_batch_check_findings,
    row_declined,
    DECLINED_SECTION_HEADING,
    SKIPPED_SECTION_HEADING,
)
from .check_records import batch_check_summary, batch_check_section
from .verification_lines import verification_line
from .batch_prompt import CODE_WRITE_KINDS
from .commit_spelling import commit_view
from .commit_apply import guard_record
from .html_report_generator import (
    regenerate_report_with_human_decisions,
    scope_regeneration_needed,
)


def applied_to_label(target: Optional[str], plan_path: str) -> Optional[str]:
    """The single file a phase edits (*target*), relative to the repository
    root above *plan_path*, or ``None`` without one."""
    if not target:
        return None
    try:
        # The `.git` holder above the plan, walked (no git runs here).
        start = os.path.dirname(os.path.realpath(plan_path))
        root = os.path.realpath(find_git_entry_root(start) or start)
        relative = os.path.relpath(os.path.realpath(target), root)
    except (OSError, ValueError):
        return target
    # A label in prose and in the result line: `/` on every platform.
    return target if relative.startswith(os.pardir) else relative.replace(os.sep, "/")


def _no_warnings() -> List[str]:
    return []


def _no_base_ref() -> str:
    return ""


def _plan_word() -> str:
    return "Plan"


@dataclass
class ApplyPhaseReport:
    """One apply phase's closing report, over the data it is built with.

    The phase's configuration, its work sets, the write executor's result
    and materialized tasks, its scope deferrals, and three answers the phase
    gives through its own hooks (``consistency_warnings``,
    ``resolve_base_ref`` and the document's title), read when a report
    needs them.
    """

    phase_name: str
    write_kind: str
    item_noun: str
    item_noun_plural: str
    plan_path: str
    out_dir: str
    review_subdir: str = ""
    #: The write scheduler's ``SchedulerResult``, or ``None`` before it ran.
    write_result: Optional[Any] = None
    #: The materialized write tasks, in batch order.
    write_tasks: List[Dict[str, Any]] = field(default_factory=list)
    #: The batch dicts the tasks were materialized from.
    batches: List[Any] = field(default_factory=list)
    batching_stats: Dict[str, Any] = field(default_factory=dict)
    formatted_valid: List[Dict[str, Any]] = field(default_factory=list)
    formatted_human: List[Dict[str, Any]] = field(default_factory=list)
    formatted_skipped: List[Dict[str, Any]] = field(default_factory=list)
    #: This run's scope deferrals and the earlier ones an ``expand`` released.
    scope_deferred: Sequence[Dict[str, Any]] = ()
    scope_released: Sequence[str] = ()
    state: Optional[StateManager] = None
    #: The reviewed endpoints state pins (``commit_range.Resolved``), if any.
    pinned: Optional[Any] = None
    #: The review report :meth:`regenerate_decisions_overlay` rewrote, once it has.
    decisions_overlay_path: Optional[str] = None
    #: The single file the phase overwrites (``write_target_file``), if any.
    target_file: Optional[str] = None
    consistency_warnings: Callable[[], List[str]] = _no_warnings
    resolve_base_ref: Callable[[], str] = _no_base_ref
    #: ``Plan``, or ``Commit brief`` on a commit review.
    document_title: Callable[[], str] = _plan_word
    logger: logging.Logger = field(
        default_factory=lambda: logging.getLogger("orchestrator.apply_report"))

    def _scope_summary_lines(self, *, markdown: bool = False) -> List[str]:
        return _scope.summary_lines(
            self.scope_deferred, self.scope_released, markdown=markdown)

    def touched_files(self) -> List[str]:
        """The files the write batches actually verified changed (F7).

        The observed post-run byte comparison, not the runner's own claim — the
        same set each applied or partially applied outcome's ``files_touched``
        carries. Partial application stops the run but preserves its edits,
        so those files must remain visible for inspection. Repo-root-
        relative, order-preserving, de-duplicated across every outcome; empty
        before the write executor has run, or when every batch was a no-op /
        clean failure. This is the only "what did this phase change" answer for
        a phase with no single write target (``has_single_write_target`` False —
        apply-code-fixes partitions by ``file_key``), and it is honest for the
        single-target phases too since it reflects what actually moved rather
        than the phase's own convention.

        Read from :meth:`_phase_rows`, so a ``--resume`` still names the files
        an earlier run of this phase changed (``batch_ledger.touched_files``,
        partial applications included).
        """

        return touched_files(self._phase_rows(), include_partial=True)

    def _phase_rows(self) -> List[Dict[str, Any]]:
        """Every batch row of this phase, earlier runs' first (#28).

        The scheduler's own ``report_rows()``, the rows
        ``write_batch_report.json`` carries, so ``summary.md``, the result
        block and the report cannot disagree. On a ``--resume`` they include
        the rows an interrupted run of this review cycle recorded, flagged
        ``from_earlier_run``, and never rows of an earlier cycle (the
        scheduler drops a report that predates the review). Built from this
        run's outcomes when the result has no rows of its own.
        """
        result = self.write_result
        report_rows = getattr(result, "report_rows", None)
        if callable(report_rows):
            return [dict(row) for row in report_rows()]
        rows: List[Dict[str, Any]] = []
        for outcome in getattr(result, "outcomes", None) or []:
            rows.append({
                "task_id": str(getattr(outcome, "task_id", "")),
                "status": getattr(outcome, "status", None),
                "write_outcome": getattr(outcome, "write_outcome", None),
                "runner": getattr(outcome, "runner", None),
                "duration_seconds": getattr(outcome, "duration_seconds", 0.0),
                "reason": getattr(outcome, "reason", None),
                "files_touched": list(getattr(outcome, "files_touched", None) or []),
                "output_path": getattr(outcome, "output_path", None),
                "expected_ids": list(getattr(outcome, "expected_ids", None) or []),
                "skipped": bool(getattr(outcome, "skipped", False)),
                **(
                    {"batch_check": {
                        "passed": not outcome.batch_check,
                        "findings": list(outcome.batch_check),
                    }}
                    if getattr(outcome, "batch_check", None) is not None else {}
                ),
            })
        return rows

    @staticmethod
    def _row_ok(row: Dict[str, Any]) -> bool:
        return row.get("status") == "ok"

    def _row_item_ids(self, row: Dict[str, Any]) -> List[str]:
        """The items a row's batch carried: the row's own ``expected_ids``,
        else this run's materialized task of the same id."""
        own = row.get("expected_ids")
        if own:
            return [str(item) for item in own]
        for task in self.write_tasks:
            if str(task.get("task_id", "")) == str(row.get("task_id", "")):
                return [str(item) for item in task.get("expected_ids") or []]
        return []

    @staticmethod
    def _row_provenance(row: Dict[str, Any]) -> str:
        """The marker a row from before this run carries, else ``""``."""
        if row.get("from_earlier_run"):
            return " (earlier run)"
        if row.get("skipped"):
            # A resume skip whose earlier row the scheduler could not supply
            # (that run left no report, or its report belonged to an earlier
            # review): this run reused the result file and dispatched nothing.
            return " (earlier result, not dispatched again)"
        return ""

    def _rows_provenance_note(self, rows: List[Dict[str, Any]]) -> str:
        """`` (N from an earlier run of this phase, …)`` for a count line."""
        earlier = sum(1 for row in rows if row.get("from_earlier_run"))
        reused = sum(
            1 for row in rows
            if row.get("skipped") and not row.get("from_earlier_run")
        )
        parts = []
        if earlier:
            parts.append(f"{earlier} from an earlier run of this phase")
        if reused:
            parts.append(f"{reused} earlier result(s) reused")
        if not parts:
            return ""
        return f" ({', '.join(parts)}, not dispatched again)"

    def _items_by_member_id(self) -> Dict[str, Dict[str, Any]]:
        """``member id -> formatted item`` over this run's batches.

        Each materialized task's ``expected_ids`` are its batch's items in
        order (``write_phase_bridge``), so an earlier run's row, whose
        positional id may now name another batch, still finds its own items.
        """
        items: Dict[str, Dict[str, Any]] = {}
        for task, batch in zip(self.write_tasks, self.batches):
            if not isinstance(batch, dict):
                continue
            members = self._batch_member_items(batch)
            for member_id, item in zip(task.get("expected_ids") or [], members):
                items.setdefault(str(member_id), item)
        return items

    def record_write_artifacts(self, output_path: str) -> None:
        """Hand back the files this phase produced, on the executor leg.

        A fully successful detached run reported ``artifacts: []`` and no
        ``output_files``: the phase that rewrote the plan never named the plan,
        its own output JSON, its batch report or the prior-changes log, so the
        host was left to glob a phase dir or mine a log it cannot see. Same two
        channels the review base writes — ``record_output_files`` feeds
        ``.status.json`` for ``status``, ``record_artifacts`` feeds the terminal
        ``MULTI_LLM_RESULT`` line every host is told to trust — and both drop
        paths that do not exist, so a stopped run names only what it produced.

        F7: also names every file the batches verified changed
        (``touched_file_{n}``, resolved against the same
        ``write_safety.resolve_repo_root`` anchor the scheduler pins the write
        path to — mirrors ``implement_orchestrator._record_implement_write_
        artifacts``), plus the judge's own dispatch report and the review report
        this run's decisions overlay rewrote, when either exists.
        """
        phase_dir = os.path.join(self.out_dir, self.phase_name)
        paths: Dict[str, str] = {}
        target = self.target_file
        if target:
            paths["applied_to"] = target
        paths["orchestrator_output"] = output_path
        report_path = getattr(self.write_result, "report_path", None)
        paths["write_batch_report"] = report_path or os.path.join(
            phase_dir, "write_batch_report.json"
        )
        paths["prior_changes"] = os.path.join(self.out_dir, "prior_changes.jsonl")
        # The summary report this leg writes itself (F3). Dropped like every
        # other path when absent, so `--dry-run-subagents` names no report.
        paths["summary"] = os.path.join(phase_dir, "summary.md")

        repo_root = repo_root_for_report(self.plan_path)
        for index, touched_path in enumerate(self.touched_files(), start=1):
            resolved = (
                touched_path if os.path.isabs(touched_path)
                else os.path.join(repo_root, touched_path)
            )
            paths[f"touched_file_{index}"] = resolved

        # The judge's own dispatch report, kind-qualified because a judge
        # dispatch can share this phase dir with the later write dispatch
        # (KINDS_SHARING_A_WRITE_PHASE_DIR) — otherwise invisible to a host
        # that only reads this run's `output_files`. Asked of the executor
        # rather than spelled out here (F6, 2026-09-17): it owns the naming
        # rule, and a hand-typed copy would drop this key on the day it moves.
        judge_report = batch_report_path(phase_dir, "human_decision_judge")
        if os.path.exists(judge_report):
            paths["human_decision_judge_report"] = judge_report

        # The review report this phase's own decisions overlay just rewrote,
        # if any (`regenerate_decisions_overlay`, called just before this).
        overlay_path = self.decisions_overlay_path
        if overlay_path:
            paths["decisions_overlay"] = overlay_path

        _detach.record_output_files(phase_dir, **paths)
        record_artifacts(
            path for path in paths.values() if path and os.path.exists(path)
        )

    def _write_item_counts(self, rows: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count items by the scheduler's verdict, rather than dispatch success.

        An ``ok`` dispatch may be a no-op or a clean failure. Neither is
        evidence that its requested changes were applied. Counted over
        :meth:`_phase_rows`, the rows the report lists, so the count lines
        agree with the table under them.
        """
        counts = {
            "applied": 0, "no-op": 0, "clean-failure": 0,
            "declined": 0, "skipped": 0,
        }
        for row in rows:
            verdict = row.get("write_outcome")
            if self._row_ok(row) and verdict in counts:
                # Fix round 18: an item its batch declined, or one skipped at
                # the user's request, is never counted under the batch's
                # verdict (an `applied` batch did not apply it).
                declined, skipped = self._row_not_applied(row)
                counts[verdict] += len([
                    item for item in self._row_item_ids(row)
                    if item not in declined and item not in skipped
                ])
                counts["declined"] += len(declined)
                counts["skipped"] += len(skipped)
        return counts

    def _not_applied_lines(self, rows: List[Dict[str, Any]]) -> List[str]:
        """One plain line per item a finished batch did not apply on purpose
        (fix round 18): ``<title> [<id8>] (fix 2 of apply-fix-batch-1) not
        applied: the batch declined it — <reason>``, and the same for an item
        skipped at the user's request. Over the finished (``ok``) rows only:
        a stopped batch is dispatched again."""
        word = "fix" if self.write_kind == "apply_code_fixes" else "suggestion"
        lines: List[str] = []
        for row in rows:
            if not self._row_ok(row):
                continue
            declined, skipped = self._row_not_applied(row)
            if not declined and not skipped:
                continue
            item_ids = self._row_item_ids(row)
            titles = {
                member: str(item.get("title") or item.get("theme") or "").strip()
                for member, item in self._row_items_with_ids(row, item_ids)
                if member
            }
            for member in item_ids:
                # Fix round 26: the record keeps the reason's closing stop.
                # Fix round 28 (live run 12 #7): so does this line, which
                # ends with it; the notice's join (`join_clauses`) drops it
                # only where another clause follows (OpenCode decline's
                # notice lost it as its last clause).
                if member in declined:
                    why = f"the batch declined it — {str(declined[member] or '').strip()}"
                elif member in skipped:
                    why = f"skipped at your request — {str(skipped[member] or '').strip()}"
                else:
                    continue
                title = titles.get(member) or "Untitled"
                lines.append(
                    f"{title} [{member[:8]}] ({word} {item_ids.index(member) + 1} "
                    f"of {row.get('task_id')}) not applied: {why}"
                )
        return lines

    def print_write_outcome_summary(self) -> None:
        """Report what the batch loop DID, plus the decision summary.

        Two gaps close here. The first is tense: the log's 12 KB tail described
        batches that had already run, and carried no outcome, duration or runner
        anywhere in it. The second is reach: ``util decisions`` (step 3 of the
        apply instructions) is the only surface for the applied/skipped
        breakdown, and on the ``--exec-subagents`` leg the phase finishes in one
        invocation, so that step never runs — the per-item reasons, which are the
        good part, existed only inside ``orchestrator_output.json``.
        """

        result = self.write_result
        rows = self._phase_rows()
        ok = [row for row in rows if self._row_ok(row)]
        item_counts = self._write_item_counts(rows)
        target = self.target_file
        touched = self.touched_files()

        print(f"\n{'=' * 60}")
        print(f"{self.phase_name.upper()}: RESULT")
        print(f"{'=' * 60}")
        # F7: a phase with no single write target (has_single_write_target False —
        # apply-code-fixes partitions by file_key) used to fall back to
        # `self.plan_path` here, which the phase never opens, so every run named
        # the plan as what it changed. The files the batches actually verified
        # changed are the honest answer, and they exist for every phase.
        if target:
            print(f"File: {target}")
        else:
            print(f"Files changed: {', '.join(touched) if touched else '(none)'}")
        print(
            f"Batches: {len(ok)}/{len(rows)} ok"
            + self._rows_provenance_note(rows)
        )
        print(f"{self.item_noun_plural.capitalize()} applied: {item_counts['applied']}")
        if item_counts["declined"]:
            print(
                f"{self.item_noun_plural.capitalize()} declined by their batch "
                f"(not applied): {item_counts['declined']}"
            )
        if item_counts["skipped"]:
            print(
                f"{self.item_noun_plural.capitalize()} skipped at your request "
                f"(not applied): {item_counts['skipped']}"
            )
        if item_counts["no-op"]:
            print(f"{self.item_noun_plural.capitalize()} needing no changes: {item_counts['no-op']}")
        if item_counts["clean-failure"]:
            print(f"{self.item_noun_plural.capitalize()} without verified changes: {item_counts['clean-failure']}")
        print(f"Skipped: {len(self.formatted_skipped)}")
        if getattr(result, "stopped_at_batch", None) is not None:
            print(f"Stopped at batch: {result.stopped_at_batch}")
        failing = {
            str(row.get("task_id")): row_batch_check_findings(row)
            for row in rows
            if self._row_ok(row) and row_batch_check_findings(row)
        }
        if failing:
            # Fix round 14: applied, but not a clean finish.
            print(f"Not a clean finish: {batch_check_summary(failing)}")
        if getattr(result, "unverified", None):
            print(result.unverified)

        if rows:
            print("\nBatches:")
            for row in rows:
                count = len(self._row_item_ids(row))
                # `batch_reply.row_outcome_label`'s reading order.
                verdict = row.get("outcome_label") or row.get("write_outcome") or "-"
                if self._row_ok(row) and row_batch_check_findings(row):
                    verdict += (
                        ", its check could not run"
                        if batch_check_could_not_run(row_batch_check_findings(row))
                        else ", its check fails"
                    )
                print(
                    f"  {row.get('task_id')}{self._row_provenance(row)}: "
                    f"{row.get('status')} ({verdict}), "
                    f"{count} {self.item_noun}(s), "
                    f"{float(row.get('duration_seconds') or 0.0):.1f}s, "
                    f"runner {row.get('runner') or '(none)'}"
                )
                reason = row.get("reason")
                if reason:
                    print(f"      reason: {reason}")
            not_applied = self._not_applied_lines(rows)
            if not_applied:
                print(f"\n{self.item_noun_plural.capitalize()} not applied:")
                for line in not_applied:
                    print(f"  - {line}")

        for warning in self.consistency_warnings():
            print(f"\n[CONSISTENCY_WARNING] {warning}")

        # The decision summary, folded in: every skip with the status and the
        # specific reason validation gave it, plus its group id so the skip can
        # be looked up in the review report.
        if self.formatted_skipped:
            print(f"\nSkipped {self.item_noun_plural} (not applied):")
            for item in self.formatted_skipped:
                gid = str(item.get("group_id") or "")
                label = f" [{gid[:8]}]" if gid else ""
                print(
                    f"  - [{judge_status_label(item.get('status'))}] "
                    f"{item.get('title', 'Unknown')}{label}"
                )
                if item.get("reason"):
                    print(f"      reason: {item['reason']}")
        # What the judge decided, on the leg where nothing else reports it. The
        # instructions put a `## Decided by the judge agent` section in the summary
        # report, but that step lives on the native leg only, so before
        # this the one decision a `--yes --exec-subagents` run actually *made*
        # reached no output the phase wrote (measured 2026-09-16).
        decided = self.judge_decisions()
        if decided:
            print(f"\nDecided by the judge agent ({len(decided)}):")
            print(f"  judge: {', '.join(self._judges_of(decided))}")
            titles = self._titles_by_group_id()
            for group_id, record in decided.items():
                title = titles.get(group_id, group_id)
                context = record.get("batch_context") or {}
                print(
                    f"  - [{judge_outcome(record)}] {title} "
                    f"[{group_id[:8]}]"
                )
                print(f"      source: {judge_source_label(context.get('decision_source'))}")
                if record.get("reason"):
                    print(f"      reason: {record['reason']}")

        if self.formatted_human:
            print(f"\nStill needing a human ({len(self.formatted_human)}):")
            for item in self.formatted_human:
                print(f"  - {item.get('title', 'Unknown')}")

        for line in self._scope_summary_lines():
            print(line)

    def run_notes(self) -> List[str]:
        """The lines a host must relay beside this run's counts (fix round 14).

        Codex racing re-run 5, apply-task-suggestions: the log carried
        ``[CONSISTENCY_WARNING] T003 depends on T004, listed after it`` and
        "Skipped: 1" (a suggestion the judge skipped), while the result the
        host read said "10/10 items applied" and nothing else, so the host
        reported "Applied 10 of 10". One line per consistency warning, and one
        naming every item left unapplied with why, its title and group id —
        the RESULT block's own facts, in plain words.
        """
        notes = [
            f"consistency warning: {warning}" for warning in self.consistency_warnings()
        ]
        # Fix round 18: an item a batch declined (or one skipped at the
        # user's request) is named with its reason, never only counted.
        notes.extend(self._not_applied_lines(self._phase_rows()))
        skipped = list(self.formatted_skipped or [])
        if skipped:
            applied = self._write_item_counts(self._phase_rows())["applied"]
            noun = self.item_noun if len(skipped) == 1 else self.item_noun_plural
            by_label: Dict[str, List[str]] = {}
            for item in skipped:
                gid = str(item.get("group_id") or "")
                title = str(item.get("title") or "Unknown").strip()
                by_label.setdefault(judge_status_label(item.get("status")), []).append(
                    f"{title}{f' [{gid[:8]}]' if gid else ''}"
                )
            shown = "; ".join(
                f"{label}: {', '.join(titles[:5])}"
                + (f" (+{len(titles) - 5} more)" if len(titles) > 5 else "")
                for label, titles in by_label.items()
            )
            # Fix round 26 (live run 11, OpenCode 05: the host said the task
            # suggestions went "to plans/racing-game.md"): the file they went to.
            target = applied_to_label(self.target_file, self.plan_path)
            notes.append(
                f"{len(skipped)} {noun} not applied, beside the {applied} "
                f"applied{f' to {target}' if target else ''} — {shown} "
                "(reasons in summary.md)"
            )
        scope_note = _scope.deferral_note(self.scope_deferred, self.item_noun_plural)
        if scope_note:
            notes.append(scope_note)
        return notes

    def publish_run_notes(self) -> None:
        """Hand :meth:`run_notes` to the result line and to ``status``.

        The run's own ``notice`` (appended, never replacing one) for a
        foreground caller, and ``progress.notes`` in the phase's
        ``.status.json``, which a detached run's terminal poll carries into
        its ``notice`` — the poll is the only result line a tool route reads.
        """
        notes = self.run_notes()
        if not notes:
            return

        _run_record.report_progress(
            os.path.join(self.out_dir, self.phase_name), notes=notes,
        )
        _cli.add_notice(join_clauses(notes))

    def judge_decisions(self) -> Dict[str, Dict[str, Any]]:
        """This phase's recorded decisions that a judge subagent made.

        The same filter the instructions' ``## Decided by the judge agent`` section
        specifies: ``human_decisions_{phase}`` entries whose
        ``batch_context.decision_source`` is ``judge_auto_decide`` or
        ``judge_auto_decide_salvage`` (or the ``claude_*`` spelling of either
        that a run started before the rename recorded).
        """
        if self.state is None:
            return {}
        try:
            recorded = self.state.get_all_human_decisions(self.phase_name)
        except Exception:  # noqa: BLE001 - reporting must not fail a run
            return {}
        return {
            group_id: record
            for group_id, record in (recorded or {}).items()
            if is_judge_source(
                ((record or {}).get("batch_context") or {}).get("decision_source")
            )
        }

    @staticmethod
    def _judge_breakdown(decided: Dict[str, Dict[str, Any]]) -> str:
        """`` (N approved, N salvaged, N skipped)`` for the summary's count line.

        The same three counts the ingest line prints, so one run never reports
        a salvage as "salvaged" in one place and "approved" in another.
        """
        if not decided:
            return ""
        outcomes = [judge_outcome(record) for record in decided.values()]
        return (
            f" ({outcomes.count('approved')} approved, "
            f"{outcomes.count('salvaged')} salvaged, "
            f"{outcomes.count('skipped')} skipped)"
        )

    @staticmethod
    def _judges_of(decided: Dict[str, Dict[str, Any]]) -> List[str]:
        """The distinct judges named by *decided*'s records, in first-seen order."""
        judges: List[str] = []
        for record in decided.values():
            judge = str(((record or {}).get("batch_context") or {}).get("judge")
                        or "unrecorded")
            if judge not in judges:
                judges.append(judge)
        return judges

    def _titles_by_group_id(self) -> Dict[str, str]:
        """``group_id -> title`` over every work set, for decision reporting."""
        titles: Dict[str, str] = {}
        for formatted in (
            self.formatted_valid,
            self.formatted_human,
            self.formatted_skipped,
        ):
            for item in formatted or []:
                gid = str(item.get("group_id") or "")
                if gid:
                    titles[gid] = str(item.get("title") or gid)
        return titles

    @staticmethod
    def _batch_member_items(batch: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """The formatted items a batch dict carries (F10).

        ``fixes`` for a ``CodeFixBatch``, ``suggestions`` for the two sibling
        phases' ``SuggestionBatch`` — whichever key the batch's own
        ``to_dict()`` used, so this reads all three phases' batches without a
        subclass override.
        """
        if not batch:
            return []
        return list(batch.get("fixes") or batch.get("suggestions") or [])

    @staticmethod
    def _read_batch_result_notes(
        output_path: Optional[str], item_ids: Optional[List[str]] = None
    ) -> Optional[str]:
        """Best-effort read of a write batch's own ``notes`` field (F10).

        ``notes`` (``schemas/write_batch_result.schema.json``) is the runner's
        free-text detail beyond the structured ``status``/``ids``/``summary``
        fields ``TaskOutcome`` already carries — on a real run, the only place a
        batch's own account of *why* (e.g. "Fix 1: car.accel 32->28 per plan
        §8.") survives past verification. Silent on any read/parse failure —
        the field is optional and this is reporting, never gating.

        With ``item_ids``, a file whose own ``ids`` name none of them is
        another batch's: an apply result file is named by position, and a
        resumed run may have rewritten it for the batch that now holds it.
        """
        if not output_path or not os.path.isfile(output_path):
            return None
        try:
            with open(output_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(data, dict):
            return None
        returned = [str(i) for i in data.get("ids") or []]
        if item_ids and returned and not set(returned) & set(item_ids):
            return None
        notes = data.get("notes")
        return notes if isinstance(notes, str) and notes.strip() else None

    def _row_items(
        self, row: Dict[str, Any], item_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """The formatted items (titles, files) a report row's batch carried.

        This run's batch of the same id when it holds the same items — task
        and batch are materialized from the same ``self.batches`` list, in the
        same order (``run_write_executor``), so a positional zip joins them —
        else the items found by member id: an earlier run's row whose
        positional id now names another batch.
        """
        return [item for _member, item in self._row_items_with_ids(row, item_ids)]

    def _row_items_with_ids(
        self, row: Dict[str, Any], item_ids: List[str]
    ) -> List[Tuple[Optional[str], Dict[str, Any]]]:
        """:meth:`_row_items` with each item's own id beside it (fix round 18:
        a declined item is named by its id on the row). ``None`` for an item
        whose id cannot be told."""
        task_id = str(row.get("task_id", ""))
        for task, batch in zip(self.write_tasks, self.batches):
            if str(task.get("task_id", "")) != task_id or not isinstance(batch, dict):
                continue
            task_ids = [str(i) for i in task.get("expected_ids") or []]
            if not row.get("expected_ids") or sorted(task_ids) == sorted(item_ids):
                members = self._batch_member_items(batch)
                return [
                    (task_ids[index] if index < len(task_ids) else None, item)
                    for index, item in enumerate(members)
                ]
            break
        by_id = self._items_by_member_id()
        return [(i, by_id[i]) for i in item_ids if i in by_id]

    @staticmethod
    def _row_not_applied(row: Dict[str, Any]) -> Tuple[Dict[str, str], Dict[str, str]]:
        """``(declined, skipped)``: a row's items its batch declined and the
        items a ``--human-task <id>=skip`` answer recorded as skipped at the
        user's request, each ``{id: reason}`` (fix round 18). Never applied."""

        return (
            row_declined(row),
            row_declined({"declined": row.get("skipped_items")}),
        )

    @staticmethod
    def _item_file_lines(item: Dict[str, Any]) -> List[str]:
        """An item's ``   - File: <path>[:<a>-<b>]`` line, when it names one."""
        file_path = item.get("file")
        if not file_path:
            return []
        line_range = item.get("line_range") or []
        if len(line_range) >= 2:
            return [f"   - File: {file_path}:{line_range[0]}-{line_range[1]}"]
        return [f"   - File: {file_path}"]

    def _not_applied_item_lines(
        self, member: str, item: Optional[Dict[str, Any]], task_id: str, why: str,
    ) -> List[str]:
        """One item of a not-applied section (fix round 22): ``- **<title>**
        (`<id>`, <batch>) — <reason>``, then its file; the id alone when this
        run's batches no longer hold the item."""
        if item is None:
            return [f"- `{member}` ({task_id}) — {why}"]
        title = item.get("title") or item.get("theme") or "Untitled"
        return [f"- **{title}** (`{member}`, {task_id}) — {why}"] + self._item_file_lines(item)

    def write_apply_summary_report(self) -> Optional[str]:
        """Write ``{phase}/summary.md`` — the report the instructions promise (F3).

        Their *Output Files* block lists this file for all three apply phases,
        and their *Generate Summary Report* step describes its sections; both
        live on the native leg, which ``--exec-subagents`` never reaches ("the phase
        finishes in that one invocation"). So the executor leg writes the same
        document itself, from the data it already has: the batch outcomes, the
        skip list rebuilt after judging, and the judge's own decisions.

        F10 extends it with the per-fix detail the instructions' own template
        promises and that was sitting unread on disk: each batch's own items
        (title, file:lines when the item has them, applied/not-applied) from
        ``self.batches``, the runner's free-text ``notes`` from its result file,
        plus ``Base ref`` / batching-efficiency lines when the orchestrator
        computed them (empty for the two sibling phases, which is why both are
        conditional rather than assumed present).

        Best-effort and never fatal — a report is not worth failing an applied
        run over. Returns the path written, or ``None``.
        """
        phase_dir = os.path.join(self.out_dir, self.phase_name)
        result = self.write_result
        # #28: the phase's rows, not this run's outcomes — a `--resume` keeps
        # the batches an interrupted run of this review cycle finished, marked
        # "(earlier run)" with that run's runner, duration and verdict. The
        # count lines below are computed from the same rows as the table.
        rows = self._phase_rows()
        ok = [row for row in rows if self._row_ok(row)]
        item_counts = self._write_item_counts(rows)
        decided = self.judge_decisions()
        titles = self._titles_by_group_id()
        nouns = self.item_noun_plural

        lines = [
            f"# Applied {nouns.title()} Report",
            "",
            # `**Commit brief**:` on a commit review (plans/review-commits.md §2.8).
            f"**{self.document_title()}**: {self.plan_path}",
        ]
        target = self.target_file
        touched = self.touched_files()
        if target:
            lines.append(f"**Applied to**: {target}")
        elif touched:
            # F7: apply-code-fixes has no single write target — the files the
            # batches verified changed is the honest "what did this phase
            # change" answer, where before nothing named it at all.
            lines.append(f"**Files changed**: {', '.join(touched)}")
        base_ref = self.resolve_base_ref()
        if base_ref:
            lines.append(f"**Base ref**: {base_ref}")
        lines += [
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            f"- Batches processed: {len(ok)}/{len(rows)}"
            + self._rows_provenance_note(rows),
            f"- {nouns.capitalize()} applied: {item_counts['applied']}",
            *(
                [f"- {nouns.capitalize()} declined by their batch (not "
                 f"applied): {item_counts['declined']}"]
                if item_counts["declined"] else []
            ),
            *(
                [f"- {nouns.capitalize()} skipped at your request (not "
                 f"applied): {item_counts['skipped']}"]
                if item_counts["skipped"] else []
            ),
            f"- {nouns.capitalize()} skipped: {len(self.formatted_skipped)}",
            f"- Decided by the judge agent: {len(decided)}"
            + self._judge_breakdown(decided),
        ]
        if item_counts["no-op"]:
            lines.append(f"- {nouns.capitalize()} needing no changes: {item_counts['no-op']}")
        if item_counts["clean-failure"]:
            lines.append(f"- {nouns.capitalize()} without verified changes: {item_counts['clean-failure']}")
        # F4: the instructions' own report template requires a verification line
        # and this leg had none, so a phase that applied seven code fixes without
        # running any check read exactly like one that had. Only for the
        # code-editing phase — a typecheck has nothing to say about a plan file.
        if self.write_kind in CODE_WRITE_KINDS:
            lines.append(f"- Verification: {verification_line(result)}")
        if self.batching_stats.get("batching_enabled"):
            lines.append(
                f"- Batching efficiency: "
                f"{self.batching_stats.get('subagent_calls_saved', 0)} "
                f"subagent call(s) saved "
                f"({self.batching_stats.get('efficiency_gain_percent', 0)}%)"
            )
        lines += [
            "",
            "## Applied Changes",
            "",
        ]
        # Fix round 22 (live run 9): an item its batch declined, or that a
        # `=skip` answer recorded as skipped at your request, is listed in a
        # section of its own below, never under this applied heading.
        not_applied_sections: Dict[str, List[str]] = {
            DECLINED_SECTION_HEADING: [], SKIPPED_SECTION_HEADING: [],
        }
        if rows:
            for row in rows:
                item_ids = self._row_item_ids(row)
                # `batch_reply.row_outcome_label`'s reading order.
                verdict = row.get("outcome_label") or row.get("write_outcome") or "-"
                failing = (
                    (", its check could not run"
                     if batch_check_could_not_run(row_batch_check_findings(row))
                     else ", its check fails")
                    if self._row_ok(row) and row_batch_check_findings(row) else ""
                )
                lines.append(
                    f"### {row.get('task_id')}{self._row_provenance(row)} — "
                    f"{row.get('status')} ({verdict}{failing})"
                )
                lines.append(
                    f"**{nouns.capitalize()}**: {len(item_ids)}  "
                    f"**Duration**: {float(row.get('duration_seconds') or 0.0):.1f}s  "
                    f"**Runner**: {row.get('runner') or '(none)'}"
                )
                members = self._row_items_with_ids(row, item_ids)
                items = [item for _member, item in members]
                declined, skipped = self._row_not_applied(row)
                if not items and item_ids and row.get("from_earlier_run"):
                    # An earlier batch whose items this run no longer selects:
                    # its ids are all that is left to name them by.
                    lines.append(
                        "**Items**: " + ", ".join(f"`{i}`" for i in item_ids)
                    )
                titles_by_member = {member: item for member, item in members}
                for kept, heading in (
                    (declined, DECLINED_SECTION_HEADING),
                    (skipped, SKIPPED_SECTION_HEADING),
                ):
                    for member, why in kept.items():
                        not_applied_sections[heading] += self._not_applied_item_lines(
                            member, titles_by_member.get(member),
                            str(row.get("task_id")), why,
                        )
                if declined or skipped:
                    told = [
                        f'{len(kept)} {words} (listed under "{heading}" below)'
                        for kept, words, heading in (
                            (declined, "declined by the batch", DECLINED_SECTION_HEADING),
                            (skipped, "skipped at your request", SKIPPED_SECTION_HEADING),
                        ) if kept
                    ]
                    lines.append(f"**Not applied**: {'; '.join(told)}")
                listed = [
                    (member, item) for member, item in members
                    if member not in declined and member not in skipped
                ]
                if listed:
                    item_status = {
                        "applied": "Applied",
                        "no-op": "No changes needed",
                        "clean-failure": "No verified changes",
                        "partial-application": "Partial application; inspect batch",
                    }.get(verdict, "Not applied")
                    for item_index, (member, item) in enumerate(listed, 1):
                        item_title = item.get("title") or item.get("theme") or "Untitled"
                        lines.append(f"{item_index}. **{item_title}** - {item_status}")
                        lines += self._item_file_lines(item)
                notes = self._read_batch_result_notes(
                    row.get("output_path"), item_ids
                )
                if notes:
                    lines.append(f"**Notes**: {notes}")
                reason = row.get("reason")
                if reason:
                    lines.append(f"**Reason**: {reason}")
                lines.append("")
            # Fix round 14: the batches whose own check failed, whole, in the
            # commit modes' words on a commit review (§2.8).
            section = batch_check_section(
                rows, commit_review=commit_view(self.plan_path) is not None)
            if section:
                lines += section[1:] + [""]
            for heading, entries in not_applied_sections.items():
                if entries:
                    lines += [f"## {heading}", ""] + entries + [""]
        else:
            lines += ["(no batches were dispatched)", ""]

        if decided:
            lines += [
                f"## Decided by the judge agent ({len(decided)})",
                "",
                f"judge: {', '.join(self._judges_of(decided))}",
                "",
                f"{nouns.capitalize()} whose decision was offloaded to a judge "
                f"subagent (`{AGENT_DECIDE_FLAG}`, or a per-item \"Let the agent "
                "decide\" selection).",
                "",
            ]
            for group_id, record in decided.items():
                context = record.get("batch_context") or {}
                lines.append(
                    f"### {titles.get(group_id, group_id)} "
                    f"({context.get('importance_at_decision', 'MEDIUM')}) — "
                    f"{judge_outcome(record).capitalize()}"
                )
                lines.append(f"**Group**: `{group_id}`")
                lines.append(f"**Source**: {judge_source_label(context.get('decision_source'))}")
                if context.get("salvaged_description"):
                    lines.append(f"**Kept**: {context['salvaged_description']}")
                if context.get("dropped"):
                    lines.append(f"**Dropped**: {context['dropped']}")
                if record.get("reason"):
                    lines.append(f"**Reason**: {record['reason']}")
                lines.append("")

        warnings = self.consistency_warnings()
        if warnings:
            lines += ["## Consistency warnings", ""]
            lines += [f"- {warning}" for warning in warnings]
            lines.append("")

        if self.formatted_skipped:
            lines += [f"## Skipped {nouns.title()}", ""]
            for item in self.formatted_skipped:
                lines.append(
                    f"### {item.get('title', 'Unknown')} "
                    f"[{judge_status_label(item.get('status'))}]"
                )
                gid = str(item.get("group_id") or "")
                if gid:
                    lines.append(f"**Group**: `{gid}`")
                if item.get("reason"):
                    lines.append(f"**Reason**: {item['reason']}")
                if item.get("files"):
                    # A commit guard skip (§2.7): the files that caused it.
                    lines.append(
                        "**Files**: " + ", ".join(f"`{f}`" for f in item["files"])
                    )
                lines.append("")

        # The scope policy's deferrals (plan §5): their own section, never
        # under a skipped or applied heading.
        lines += self._scope_summary_lines(markdown=True)

        path = os.path.join(phase_dir, "summary.md")
        try:
            os.makedirs(phase_dir, exist_ok=True)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("\n".join(lines).rstrip() + "\n")
        except OSError as exc:  # noqa: BLE001 - a report must not fail a run
            self.logger.warning("summary report not written: %s", exc)
            return None
        print(f"[write-subagents] summary report: {path}")
        return path

    def patch_write_batch_report_summary_file(self, summary_path: str) -> None:
        """Fill in ``write_batch_report.json``'s ``summary_file`` after the fact (F11).

        ``WriteBatchScheduler`` serializes that report inside
        ``run_write_executor()``, before this base ever calls
        ``write_apply_summary_report()`` — the scheduler only fills
        ``summary_file`` itself when constructed with its own ``summary_file``
        argument, which the apply phases never pass (they write their own
        summary here, on this leg). So the report on disk said
        ``summary_file: null`` for a run that went on to write one a few lines
        later. Patched here, once the apply phase's own path is known, rather
        than by changing the scheduler (owned elsewhere — see AGENTS.md).

        Best-effort: a read/parse/write failure is logged and never raised, the
        same posture as the report it patches.
        """
        if self.write_result is not None:
            self.write_result.summary_file = summary_path
        report_path = getattr(self.write_result, "report_path", None)
        if not report_path or not os.path.isfile(report_path):
            return
        try:
            with open(report_path, "r", encoding="utf-8") as handle:
                report = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:  # noqa: BLE001 - best-effort
            self.logger.warning("write_batch_report.json not patched: %s", exc)
            return
        if not isinstance(report, dict) or report.get("summary_file") == summary_path:
            return
        report["summary_file"] = summary_path
        try:
            failure_capture._atomic_write_json(report_path, report)
        except OSError as exc:  # noqa: BLE001 - best-effort
            self.logger.warning("write_batch_report.json not patched: %s", exc)

    def regenerate_decisions_overlay(self) -> Optional[str]:
        """Badge the review report's findings with this phase's decisions (F3).

        The in-process twin of ``util report regenerate-decisions --apply-phase
        {phase}``, which the instructions run on the native leg only.
        Called as a function rather than shelled out: the executor leg is
        already inside the process that holds the decisions, and a subprocess
        would re-resolve the skill dir it is running from.

        Best-effort by design — the command it mirrors exits 0 with a notice
        when the review predates the ``report_data.json`` sidecar.
        """
        if self.state is None:
            return None
        review_dir = Path(self.out_dir) / self.review_subdir
        if not (review_dir / "report_data.json").exists():
            return None
        decisions = self.state.get_all_human_decisions(self.phase_name)
        # The commit guard's skips badge their groups beside the decisions
        # (plans/review-commits.md §2.10): read from the saved guard.
        guard = None
        if self.pinned is not None:
            guard = guard_record(self.state.state)
        # A recorded scope-policy change (an apply override, its deferrals)
        # refreshes the report's eligibility even with no decision to badge.
        if (not decisions and not (guard and guard.get("skipped"))
                and not scope_regeneration_needed(review_dir, self.state.state)):
            return None
        try:
            report_path, matched = regenerate_report_with_human_decisions(
                review_dir, decisions, **({"guard": guard} if guard else {}),
                scope_state=self.state.state,
            )
        except Exception as exc:  # noqa: BLE001 - an overlay must not fail a run
            self.logger.warning("decision overlay not regenerated: %s", exc)
            return None
        if report_path is None:
            return None
        print(
            f"[write-subagents] decisions overlaid on {report_path} "
            f"({matched} of {len(decisions)} decision(s) matched)"
        )
        if matched < len(decisions):
            self.logger.warning(
                "decision overlay matched %d of %d decision(s) on %s — the "
                "rest joined no group (no groupHash, or a stale group id)",
                matched, len(decisions), report_path,
            )
        return str(report_path)


__all__ = ["ApplyPhaseReport", "applied_to_label"]
