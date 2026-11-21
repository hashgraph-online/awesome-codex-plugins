"""What implement's checks hold back, and how a run says so (fix rounds 11 to 28).

:class:`CheckHolds` reads a check task's findings against the decomposition: the
tasks after it, transitively (:meth:`CheckHolds.dependents_of`), that a check
with findings holds back in this run (:meth:`CheckHolds.check_holds`,
:meth:`CheckHolds.block_dependents_of_checks`) or that a check recorded by an
earlier run still holds (:meth:`CheckHolds.hold_on_recorded_checks`); whether a
resumed check runs again, from the tree it was stamped with
(:meth:`CheckHolds.check_findings_rerun`, :meth:`CheckHolds.unchanged_since_failure`,
:meth:`CheckHolds.tree_fingerprint`), and the tree re-stamped on a stop
(:meth:`CheckHolds.restamp_check_trees`); and the ``[CHECK_FINDINGS]`` and
``[BATCH_CHECK_*]`` lines a run ends with (:meth:`CheckHolds.check_findings_lines`,
:meth:`CheckHolds.check_findings_fate`, :meth:`CheckHolds.batch_check_lines`),
in ``check_records``' words, shared with the native leg.

``WriteBatchScheduler`` composes it with the run's ``RunContext``
(docs/development/write-scheduler.md#where-the-schedulers-helpers-live). It
holds no state of its own: a hold is recorded on the run's result
(``result.blocked_by_check``), and a check's verdict is re-stamped in its own
result file, never in ``state.json``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

from . import check_records as _check_records
from . import git_utils as _git_utils
from . import write_context as _write_context
from .held_folder import write_in_plan_dir
from .task_dispatch import STATUS_BATCH_FAILED
from .retry_ladder import STATUS_OK
from .batch_reply import (
    WRITE_CLEAN_FAILURE,
    row_check_findings,
)
from .task_outcome import (
    ResultRejected,
    TaskOutcome,
)
from .runner_selection import profile_for_kind
from .task_result import resolve_output_target
from .subagent_tasks import declared_file_set
from .task_ledger import ACCEPTED_WITH_FINDINGS_MARK
from .check_tree import check_tree_exclusions


class CheckHolds:
    """What a run's checks hold back, whether a resumed one runs again, and
    the lines that say so.

    Built once per run by the scheduler. *invoker* names the run's dispatcher
    on an outcome no runner produced; *task_by_id* reaches the scheduler's
    ``_task_by_id``, looked up at each call.
    """

    def __init__(
        self,
        ctx: _write_context.RunContext,
        *,
        invoker: str,
        task_by_id: Callable[[str], Optional[Dict[str, Any]]],
    ) -> None:
        self._ctx = ctx
        self._invoker = invoker
        self._task_by_id = task_by_id

    def check_findings_lines(
        self, result: Any, *, stopped: bool = False,
    ) -> List[str]:
        """One ``[CHECK_FINDINGS]`` line per check task that reported
        problems, and one line on what happens to them (racing re-run 4:
        nothing on the run's own output named T007's two problems).

        *stopped*: the run ended on a stop (fix round 14), where the tasks
        after the stop did not go on whatever they depend on.
        """
        found = result.check_findings()
        if not found:
            return []
        lines = [
            _check_records.check_findings_line(task_id, findings)
            for task_id, findings in found.items()
        ]
        where = (
            f"; they are listed in {result.summary_file}"
            if result.summary_file else ""
        )
        went_on = "; ".join(self.check_findings_fate(result, found, stopped=stopped))
        lines.append(
            f"Check findings: {', '.join(found)} ran, changed no file and "
            f"reported problems; {went_on}{where}. Review-code is told about "
            f"them, and apply-code-fixes applies the fixes review-code "
            f"validates."
        )
        return lines

    def check_findings_fate(
        self, result: Any, found: Dict[str, List[str]], *,
        stopped: bool = False, see_below: bool = False,
    ) -> List[str]:
        """What became of the tasks after the checks in *found*, one clause
        per kind of check (lowercase, no closing stop), for the
        ``[CHECK_FINDINGS]`` summary line and summary.md's ``## Check
        Findings``.

        Fix round 18 (live run 7, accept path): a check whose findings the
        user accepted (``--human-task <id>=done``) read "No task waits for
        them, so implement went on", although T007 had waited on it and ran
        only because the findings were accepted. Such a check is named with
        the answer and the tasks after it that ran; the others keep the hold
        (*stopped*: the run ended on a stop) or "no task waits" wording.
        *see_below*: the summary, which lists the held tasks in a section of
        their own instead of by id.
        """
        reasons = getattr(result.human_plan, "accepted", None) or {}
        accepted = [
            check_id for check_id in found
            if ACCEPTED_WITH_FINDINGS_MARK in str(reasons.get(check_id) or "")
        ]
        others = [check_id for check_id in found if check_id not in accepted]
        clauses: List[str] = []
        if accepted:
            done = {
                str(row.get("task_id")) for row in result.report_rows()
                if row.get("status") == STATUS_OK
            }
            for check_id in accepted:
                ran = [dep for dep in self.dependents_of(check_id) if dep in done]
                clauses.append(
                    f"you accepted {check_id}'s findings (--human-task "
                    f"{check_id}=done), so "
                    + (
                        f"{', '.join(ran)}, which "
                        f"{'waits' if len(ran) == 1 else 'wait'} on it, ran, "
                        f"told that you accepted them"
                        if ran else
                        "the tasks that wait on it are no longer held back by it"
                    )
                )
        if not others:
            return clauses
        them = "them" if not accepted else (
            f"{', '.join(others)}'s findings" if len(others) == 1
            else f"the findings of {', '.join(others)}"
        )
        blocked = sorted(result.blocked_by_check)
        held = "(see below)" if see_below else f"({', '.join(blocked)})"
        if blocked and stopped:
            clauses.append(f"the tasks that depend on {them} are held {held}")
        elif blocked:
            clauses.append(
                f"the tasks that do not depend on {them} went on, and the ones "
                f"that do were not run {held}"
            )
        else:
            clauses.append(
                f"no task waits for {them}" + ("" if stopped else ", so implement went on")
            )
        return clauses

    def batch_check_lines(self, result: Any) -> List[str]:
        """One :data:`BATCH_CHECK_MARKER` line per code batch whose own check
        failed after its edits, and one line saying the run is not a clean
        finish (fix round 14); before them, one
        :data:`BATCH_CHECK_ACCEPTED_MARKER` line per code task whose own
        check reported again only findings the user accepted (fix round 22),
        which never makes the run unclean. Fix round 28: each with the
        task's own-check note, when it gave one."""
        notes = result.batch_check_notes()
        lines = [
            _check_records.batch_check_accepted_line(task_id, matched, note=notes.get(task_id))
            for task_id, matched in result.batch_check_accepted().items()
        ]
        # Fix round 28: what only repeats a check task's finding.
        lines += [
            _check_records.batch_check_repeated_line(task_id, matched, note=notes.get(task_id))
            for task_id, matched in result.batch_check_repeats().items()
        ]
        found = result.batch_check_findings()
        if not found:
            return lines
        lines += [
            _check_records.batch_check_line(task_id, findings, note=notes.get(task_id))
            for task_id, findings in found.items()
        ]
        where = (
            f" They are listed under Check Findings in {result.summary_file}."
            if result.summary_file else ""
        )
        lines.append(
            f"Not a clean finish: {_check_records.batch_check_summary(found)} The edits are "
            f"kept; look at the failure before you go on.{where}"
        )
        return lines

    def hold_on_recorded_checks(
        self, tasks: Sequence[Dict[str, Any]], result: Any,
    ) -> None:
        """Honor upstream findings even when their check is outside this run.

        Read at each dependency level: a check run earlier in this invocation
        can pass and release its dependents, while an omitted check (notably
        under ``--task``) cannot silently lose its hold.
        """
        if self._ctx.kind != "implement":
            return
        held = _check_records.rerunnable_checks(self._ctx.state)
        graph = _check_records.decomposition_graph(self._ctx.tasks, self._ctx.state)
        recorded = self._ctx.state.get("task_check_findings") or {}
        for task in tasks:
            task_id = str(task.get("task_id", ""))
            if (task.get("executor_role") == "human" or task.get("is_human")
                    or result.human_plan.is_skipped(task_id)
                    or task_id in result.human_plan.accepted):
                continue
            check_id = _check_records.upstream_held_check(graph, task_id, held)
            if check_id is not None:
                result.blocked_by_check[task_id] = check_id
                result.recorded_check_findings[check_id] = [
                    str(item) for item in recorded.get(check_id, [])
                ]

    def block_dependents_of_checks(
        self, outcomes: Sequence[TaskOutcome], result: Any,
    ) -> None:
        """Keep every task that depends on a check with findings from running.

        Fix round 11 (review of round 10, T1): a check task that reported
        problems was recorded ``check-findings`` and the loop dispatched the
        tasks that depend on it — on the code the check had just rejected.
        Its transitive dependents (``depends_on``, over the whole
        decomposition — fix round 12: over this run's tasks alone, a resume
        lost the ones whose chain ran through a finished task) that this run
        holds are now recorded in ``result.blocked_by_check`` and left out of every
        later batch; a task already skipped or accepted, and a manual task
        (never dispatched), are not. A resume skip and a check not run again
        because nothing changed carry the earlier findings, so they block
        the same tasks again. ``implement`` only: no other kind has checks.
        """
        for outcome in outcomes:
            for dependent in self.check_holds(outcome, result):
                result.blocked_by_check[dependent] = outcome.task_id

    def check_holds(
        self, outcome: TaskOutcome, result: Any,
    ) -> List[str]:
        """The tasks *outcome*, a check that reported findings, holds back
        and that nothing holds yet (:meth:`block_dependents_of_checks`);
        ``[]`` for any other outcome. Reads only: the check's own ``[ETA]``
        line asks it before its batch returns (fix round 21)."""
        if self._ctx.kind != "implement" or not (outcome.ok and outcome.check_findings):
            return []
        plan = result.human_plan
        held: List[str] = []
        for dependent in self.dependents_of(outcome.task_id):
            task = self._task_by_id(dependent)
            if task is None:
                # Not in this run (a finished task a resume did not
                # materialize): nothing to hold, but the walk went
                # through it to the tasks after it (fix round 12).
                continue
            if (
                dependent in result.blocked_by_check
                or dependent in held
                or plan.is_skipped(dependent)
                or dependent in plan.accepted
                or task.get("executor_role") == "human"
                or task.get("is_human")
            ):
                continue
            held.append(dependent)
        return held

    def check_findings_rerun(
        self, task: Dict[str, Any], output_path: str, result: Any,
    ) -> Optional[bool]:
        """Whether a resumed check whose findings stand is run again.

        ``None`` when the result *output_path* holds is not a check that
        reported problems (the ordinary resume skip applies). Otherwise the
        findings are treated as a failed stamp is (fix round 11, review T2:
        a check with findings was skipped as done on every ``--resume``, so
        the tasks it held could never run): ``True`` — dispatch it again —
        on ``--human-task <id>=retry``, or when the files git sees changed
        since it ran (``verdict.tree_fingerprint``), or when no fingerprint
        can be compared; ``False`` — keep its findings without a dispatch,
        so the tasks after it stay held — when nothing changed.
        """
        try:
            data = json.loads(Path(output_path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        verdict = data.get("verdict") if isinstance(data, dict) else None
        if not isinstance(verdict, dict) or not verdict.get("verification_only"):
            return None
        if not row_check_findings(verdict):
            return None
        task_id = str(task.get("task_id", ""))
        if task_id in result.human_plan.retry:
            self._ctx.log(
                f"[write-subagents] {task_id}: --human-task {task_id}=retry — "
                f"running its check again whether or not the repository changed."
            )
            return True
        recorded = verdict.get("tree_fingerprint")
        current = self.tree_fingerprint()
        if recorded and current is not None and current == recorded:
            self._ctx.log(
                f"[write-subagents] {task_id}: not run again — nothing in the "
                f"repository changed since its check reported problems; its "
                f"findings stand and the tasks after it stay held."
            )
            return False
        self._ctx.log(
            f"[write-subagents] {task_id}: its check reported problems and "
            f"the files changed since — running it again."
        )
        return True

    def unchanged_since_failure(
        self, task: Dict[str, Any], result: Any,
    ) -> Optional[TaskOutcome]:
        """The guard a resumed, failed, verification-only task passes first.

        Answers an outcome — not dispatched, ``batch_failed`` / clean failure,
        ``not_rerun`` — when all of: the task declares no files (a check), the
        state records it ``failed``, its result file's verdict carries the
        ``tree_fingerprint`` the failure was stamped with, that fingerprint
        still matches the worktree (``git_utils.worktree_fingerprint``: the
        files git sees, by size and mtime, the plugin's own output trees left
        out), and the user did not answer ``--human-task <id>=retry``. A
        read-only check on unchanged bytes fails the same way; the stop
        message then names the remedy again instead of a dispatch buying
        nothing. ``None`` (dispatch as usual) on any other answer: a changed
        tree, no fingerprint on record, a tree git cannot read.
        """
        task_id = str(task.get("task_id", ""))
        if self._ctx.kind != "implement" or declared_file_set(task):
            return None
        if task_id in result.human_plan.retry:
            self._ctx.log(
                f"[write-subagents] {task_id}: --human-task {task_id}=retry — "
                f"running the check again whether or not the repository changed."
            )
            return None
        if _write_context.has_state(self._ctx.state):
            # Without a state there is no status to go by: the result file
            # alone decides.
            try:
                if self._ctx.state.get_task_status(task_id) != "failed":
                    return None
            except Exception:  # noqa: BLE001 - advisory
                return None
        try:
            own = resolve_output_target(task, self._ctx.phase_dir)
        except ResultRejected:
            return None
        if own is None or not Path(own).is_file():
            return None
        try:
            data = json.loads(Path(own).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        verdict = data.get("verdict") if isinstance(data, dict) else None
        if not isinstance(verdict, dict) or verdict.get("ok"):
            return None
        recorded = verdict.get("tree_fingerprint")
        if not recorded or not verdict.get("verification_only"):
            return None
        current = self.tree_fingerprint()
        if current is None or current != recorded:
            return None
        summary = str(data.get("summary") or "").strip()
        outcome = TaskOutcome(
            task_id=task_id, kind=self._ctx.kind, runner=self._invoker,
            status=STATUS_BATCH_FAILED, profile=profile_for_kind(self._ctx.kind),
            write_outcome=WRITE_CLEAN_FAILURE, verification_only=True,
            not_rerun=True, summary=summary or None,
            runner_notes=(verdict.get("runner_notes") or None),
        )
        outcome.output_path = str(own)
        outcome.expected_ids = [str(i) for i in (task.get("expected_ids") or [])]
        outcome.returned_ids = [str(i) for i in (data.get("ids") or [])]
        outcome.reason = (
            f"NOT RE-RUN: nothing in the repository changed since {task_id} "
            f"failed (the files git sees have the same sizes and timestamps), "
            f"so the same check would fail the same way"
            + (f": {summary}" if summary else "")
            + ". Fix what it reported and resume, accept the failure with "
            f"--human-task {task_id}=done, or run it again anyway with "
            f"--human-task {task_id}=retry."
        )
        self._ctx.log(
            f"[write-subagents] {task_id}: not run again — nothing in the "
            f"repository changed since it failed; the stop below names the "
            f"way forward."
        )
        return outcome

    def tree_fingerprint(self) -> Optional[str]:
        """Fingerprint source files, including code beside workflow artifacts."""

        excluded = check_tree_exclusions(
            Path(self._ctx.phase_dir), self._ctx.repo_root, output_dir=self._ctx.output_dir,
        )
        try:
            return _git_utils.worktree_fingerprint(
                self._ctx.repo_root, exclude_prefixes=excluded,
            )
        except Exception:  # noqa: BLE001 - advisory, never fatal
            return None

    def dependents_of(self, task_id: str) -> List[str]:
        """Every task that depends on *task_id*, transitively, in id order.

        Over the whole decomposition (:func:`decomposition_graph`), not only
        this run's tasks: a resume does not materialize a finished task, and
        a walk over the rest stopped at it (fix round 12). A task this run
        does not hold is in the answer; callers that act on a task skip it.
        """
        if self._ctx.kind != "implement":
            return _check_records.transitive_dependents(self._ctx.tasks, task_id)
        return _check_records.transitive_dependents(
            _check_records.decomposition_graph(self._ctx.tasks, self._ctx.state), task_id,
        )

    def restamp_check_trees(self, result: Any) -> None:
        """Stamp the tree as this run left it on each check with findings.

        ``_stamp_verdict`` records the tree when the check ran, and the
        tasks that do not depend on it go on and edit files after it — so a
        ``--resume`` the user changed nothing for would read "the files
        changed" and run the check again. The run's own edits are not a
        change the user made: when the run ends needing a human, each
        check-findings verdict this run holds is re-stamped with the tree as
        the run leaves it, and a resume runs the check again only when
        something moved since (fix round 11). Best-effort.
        """
        if self._ctx.kind != "implement":
            return
        current: Optional[str] = None
        for outcome in result.outcomes:
            if not (outcome.ok and outcome.check_findings and outcome.output_path):
                continue
            path = Path(outcome.output_path)
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                verdict = data.get("verdict") if isinstance(data, dict) else None
                if not isinstance(verdict, dict):
                    continue
                if current is None:
                    current = self.tree_fingerprint()
                    if current is None:
                        return
                if verdict.get("tree_fingerprint") == current:
                    continue
                verdict["tree_fingerprint"] = current
                # Owner-only, as the executor wrote it (docs/development/
                # runtime.md#atomic-file-writes), through its folder held as
                # `persist_result` writes it
                # (docs/development/write-safety.md#plan-output-containment).
                write_in_plan_dir(path, json.dumps(data, indent=2).encode("utf-8"),
                                  mode=0o600)
            except (OSError, ValueError) as exc:  # noqa: BLE001 - bookkeeping
                self._ctx.log(
                    f"[write-subagents] warning: could not re-stamp the tree on "
                    f"{path.name} for {outcome.task_id}: {exc}"
                )
