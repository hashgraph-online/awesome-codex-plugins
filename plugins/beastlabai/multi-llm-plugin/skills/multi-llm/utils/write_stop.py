"""How a write phase that stops says so.

:class:`StopAccount` words and records every ending of the executor leg that
is short of a finished phase: a failed batch (:meth:`StopAccount.record_stop`,
:meth:`StopAccount.stop_message`), a refusal before dispatch
(:meth:`StopAccount.refusal_message`), the tasks a check with findings holds
back (:meth:`StopAccount.record_check_block`,
:meth:`StopAccount.check_block_message`) and a manual task the run waits on
(:meth:`StopAccount.manual_gate`, :meth:`StopAccount.record_manual_gate`,
:meth:`StopAccount.manual_gate_message`). It records on the run's
``SchedulerResult`` the stop's headline, its ``--human-task`` answers and what
a plain ``--resume`` does (:meth:`StopAccount.stop_answers`,
:meth:`StopAccount.stop_resume_why`), in ``stop_answers``' and
``write_outcomes``' words, shared with the native leg
(docs/development/write-scheduler.md#where-the-schedulers-helpers-live). It
holds no state of its own: it reads the result, the tasks and ``state.json``,
and the refusals on the result (``result.refusals``).

``WriteBatchScheduler`` composes it with the run's ``RunContext``. Its one
``state.json`` write (:meth:`StopAccount.record_not_run_in_state`) goes through
``ctx.state`` under the scheduler's ``_effects_lock``, which it is handed.
"""

from __future__ import annotations

import copy
import json
import os
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from . import check_records as _check_records
from . import human_task_plan as _human_task_plan
from . import metrics as _metrics
from . import stop_answers as _stop_answers
from . import write_context as _write_context
from . import write_outcomes as _write_outcomes
from .retry_ladder import STATUS_OK
from .batch_reply import (
    WRITE_CLEAN_FAILURE,
    WRITE_PARTIAL,
    WRITE_POLICY_VIOLATION,
    row_check_findings,
)
from .task_outcome import (
    ExecutorError,
    ResultRejected,
    TaskOutcome,
)
from .task_result import resolve_output_target
from .subagent_tasks import APPLY_WRITE_KINDS, declared_file_set
from .task_ledger import ACCEPTED_WITH_FINDINGS_MARK, is_declined_reason
from .text_clip import clip
from .write_safety import policy_allow_clause, policy_outside_note, policy_skip_clause
from . import status_file as _status_file
from .manual_tasks import manual_gate_why, manual_gate_decline_answers


class StopAccount:
    """The words and records of a write phase's stop.

    Built once per run by the scheduler. *effects_lock* is the scheduler's
    ``_effects_lock``; *user_commands* the host's own spelling of the ways
    forward. The callables reach the scheduler's methods and the mirror's
    (``WriteReports.mirror_snapshot``, ``WriteReports.mirror_status``), looked
    up at each call.
    """

    def __init__(
        self,
        ctx: _write_context.RunContext,
        *,
        effects_lock: threading.Lock,
        user_commands: Dict[str, str],
        task_by_id: Callable[[str], Optional[Dict[str, Any]]],
        dependents_of: Callable[[str], List[str]],
        keep_partial_clause: Callable[..., str],
        unapplied_words: Callable[..., str],
        restamp_check_trees: Callable[..., Any],
        tree_fingerprint: Callable[[], Optional[str]],
        started_a_runner: Callable[..., bool],
        mirror_snapshot: Callable[[], Dict[str, Any]],
        mirror_status: Callable[..., None],
    ) -> None:
        self._ctx = ctx
        self._effects_lock = effects_lock
        self._user_commands = user_commands
        self._task_by_id = task_by_id
        self._dependents_of = dependents_of
        self._keep_partial_clause = keep_partial_clause
        self._unapplied_words = unapplied_words
        self._restamp_check_trees = restamp_check_trees
        self._tree_fingerprint = tree_fingerprint
        self._started_a_runner = started_a_runner
        self._mirror_snapshot = mirror_snapshot
        self._mirror_status = mirror_status

    def stop_message(
        self, batch_index: int, outcomes: Sequence[TaskOutcome],
        result: Optional[Any] = None,
    ) -> List[str]:
        """The exit-3 block after a failed batch, in plain words.

        Names the task that failed and what it reported, every task the stop
        left unrun, the tasks that ran, and a way forward that works (racing
        re-run 3, 2026-10-05: a failed read-only check stopped implement, the
        message named only the deferred manual tasks, and ``--resume`` re-ran
        the same check on unchanged code). The commands are the host's own
        spelling when the orchestrator supplied them (``user_commands``), the
        bare flags otherwise.
        """
        failed = [o for o in outcomes if not o.ok]
        stop = (result.stop if result is not None else None) or {}
        refusals = _write_context.refusals_of(result)
        lines = [""]
        for outcome in failed:
            what = self.failure_sentence(outcome, refusals)
            lines.append(
                f"ERROR: {self._ctx.phase} stopped at {outcome.task_id}"
                f"{self.task_label(outcome.task_id)}: {what}"
            )
            if outcome.runner_notes:
                lines.append(f"      what it reported: {outcome.runner_notes}")
            lines.append(f"      details: {outcome.reason or outcome.status}")
            if outcome.snapshot_dir and outcome.files_touched:
                lines.append(
                    f"      restore: multi_llm.py util restore-batch --phase-dir "
                    f'"{self._ctx.phase_dir}" --task-id {outcome.task_id}'
                )
            if outcome.unrestorable:
                # Moved, and outside every rollback point.
                lines.append(
                    f"      no rollback point: {', '.join(outcome.unrestorable[:5])}"
                    f"{', …' if len(outcome.unrestorable) > 5 else ''} changed "
                    f"and util restore-batch cannot undo "
                    f"{'it' if len(outcome.unrestorable) == 1 else 'them'} (no "
                    f"pre-run copy was kept); inspect "
                    f"{'it' if len(outcome.unrestorable) == 1 else 'them'} by hand"
                )
        if not failed:
            lines.append(
                f"ERROR: the write loop stopped at batch {batch_index}; no later "
                f"batch was dispatched and the {self._ctx.phase} phase is NOT marked "
                f"completed."
            )
        lines.extend(self.account_lines(result))
        lines.extend(self.way_forward_lines(
            failed, stop, plan=result.human_plan if result is not None else None,
            refusals=refusals,
        ))
        lines.extend(self.held_by_checks_lines(result, failed))
        lines += [
            f"Audit log: {self._ctx.audit.path}",
            f"Snapshots: {os.path.join(self._ctx.safety_dir, 'pre_batch')}/",
        ]
        if failed and all(
            o.task_id in refusals.before_dispatch for o in failed
        ):
            lines.append(
                "Nothing was half-applied: the stopped task never started, and "
                "the tasks before it keep what they changed."
            )
        elif failed and not any(o.bytes_moved for o in failed):
            # A clean failure, a
            # timeout or a prose reply that moved no byte left nothing
            # half-applied either. "moved" is what the sweep
            # observed, a file with no rollback point included.
            lines.append(
                "Nothing was half-applied: the stopped task changed no file, "
                "and the tasks before it keep what they changed."
            )
        else:
            lines.append(
                "The half-applied state is deliberately left in place: what the "
                "stop left on disk stays until you restore the batch or resume."
            )
        return lines

    def task_label(self, task_id: str) -> str:
        """`` (check: <title>)`` for a verification-only task, `` (<title>)`` otherwise."""
        task = self._task_by_id(task_id) or {}
        title = str(task.get("task_title") or "").strip()
        check = self._ctx.kind == "implement" and not declared_file_set(task)
        if check and title:
            return f" (check: {title})"
        if check:
            return " (a check)"
        return f" ({title})" if title else ""

    def failure_sentence(
        self, outcome: TaskOutcome, refusals: _write_context.Refusals,
    ) -> str:
        """What failed, in one clause: the runner's own summary when it gave one."""
        summary = (outcome.summary or "").strip()
        if outcome.not_rerun:
            return (
                "not run again — nothing in the repository changed since this "
                "check failed, so it would fail the same way"
                + (f" ({summary})" if summary else "")
            )
        if outcome.task_id in refusals.before_dispatch:
            return "refused before it was dispatched" + (
                " — the write policy (driver.write_paths) does not allow a "
                "file it declares"
                if outcome.write_outcome == WRITE_POLICY_VIOLATION else ""
            )
        if outcome.applied_without_changes:
            return (
                "its change did not land — the reply said it was applied, but "
                + ("none of the files it declares changed" if outcome.bytes_moved
                   else "no file changed")
            )
        check = self._task_by_id(outcome.task_id) or {}
        is_check = self._ctx.kind == "implement" and not declared_file_set(check)
        label = outcome.outcome_label or outcome.write_outcome or outcome.status
        if is_check and outcome.write_outcome == WRITE_CLEAN_FAILURE:
            return "the check failed" + (f" — {summary}" if summary else "")
        if outcome.write_outcome == WRITE_PARTIAL:
            return (
                "partial application (bytes moved, the batch did not finish)"
                + (
                    ": its runner ran past its time limit and was stopped, and "
                    "what it changed is kept in place"
                    if self.ran_out_of_time(outcome) else ""
                )
                + (f" — {summary}" if summary else "")
            )
        return f"{label}" + (f" — {summary}" if summary else "")

    @staticmethod
    def ran_out_of_time(outcome: TaskOutcome) -> bool:
        """Whether the batch was killed at its time limit after its edits
        landed (``TaskOutcome.ran_out_of_time``)."""
        return bool(getattr(outcome, "ran_out_of_time", False))

    def account_lines(self, result: Optional[Any]) -> List[str]:
        """Every task of the decomposition, by what became of it."""
        if result is None:
            return []
        account = self.accounting(result)
        lines = []
        done = account["done"]
        if done:
            lines.append(
                f"Done and kept: {len(done)} task(s) ({_check_records._id_range(done)})."
            )
        if account.get("check_findings"):
            lines.append(
                f"Of those, checks that reported problems (listed in the "
                f"implementation summary): {', '.join(account['check_findings'])}."
            )
        if account["not_run"]:
            blocked = account.get("blocked") or {}
            for check_id in sorted(set(blocked.values())):
                waiting = [t for t in account["not_run"] if blocked.get(t) == check_id]
                lines.append(
                    f"Not run (they depend on check {check_id}, which reported "
                    f"problems): {', '.join(waiting)}."
                )
            stopped = [t for t in account["not_run"] if t not in blocked]
            if stopped:
                lines.append(
                    f"Not run (the stop came before they were dispatched): "
                    f"{', '.join(stopped)}."
                )
        with_findings = account.get("accepted_with_findings") or []
        after_failing = [t for t in account["accepted"] if t not in with_findings]
        if after_failing:
            lines.append(
                f"Accepted after failing (--human-task <id>=done): "
                f"{', '.join(after_failing)}."
            )
        if with_findings:
            lines.append(
                f"Accepted with their check findings (--human-task <id>=done): "
                f"{', '.join(with_findings)}."
            )
        if account["completed_manual"]:
            lines.append(
                f"Completed by hand (--human-task <id>=done): "
                f"{', '.join(account['completed_manual'])}."
            )
        if account["declined"]:
            lines.append(
                f"Skipped at your request (--human-task <id>=skip): "
                f"{', '.join(account['declined'])}."
            )
        if account["skipped_dependents"]:
            lines.append(
                f"Skipped (depend on a skipped task): "
                f"{', '.join(account['skipped_dependents'])}."
            )
        if account["deferred"]:
            lines.append(f"Deferred manual: {', '.join(account['deferred'])}.")
        lines.append(
            f"That is every one of the {account['total']} task(s) in this "
            f"decomposition; the {self._ctx.phase} phase is NOT marked completed."
        )
        return lines

    def way_forward_lines(
        self, failed: Sequence[TaskOutcome], stop: Dict[str, Any],
        plan: Optional[_human_task_plan.HumanTaskPlan] = None,
        *, refusals: _write_context.Refusals,
    ) -> List[str]:
        """The remedy, with the host's own command spellings when known.

        The dependents a ``skip`` answer would leave undone are the ones a
        skip can still change: a manual task (never dispatched) and a task
        the run already skipped are not listed, so the sentence does not name
        a deferred manual task as if the answer decided it.
        """
        cmds = self._user_commands
        already = set(plan.skipped) if plan is not None else set()
        manual = {
            str(t.get("task_id", "")) for t in self._ctx.tasks
            if t.get("executor_role") == "human" or t.get("is_human")
        }
        resume = cmds.get("resume") or "re-invoke this phase with --resume"
        lines = ["To go on:"]
        acceptable = [
            o for o in failed
            if o.write_outcome == WRITE_CLEAN_FAILURE and not o.bytes_moved
        ]
        checks = [
            o for o in acceptable
            if self._ctx.kind == "implement"
            and not declared_file_set(self._task_by_id(o.task_id) or {})
        ]
        refused = [o for o in failed if o.task_id in refusals.before_dispatch]
        if refused and not acceptable:
            policy = any(o.write_outcome == WRITE_POLICY_VIOLATION for o in refused)
            # That nothing is half-applied is the
            # block's closing line, said once; the bullet is the remedy. The policy's,
            # worded as the user's own call. Per rule (a deny hit names the deny rule),
            # and none
            # for a file outside the repository, which no rule can allow.
            def hits_of(outcome: TaskOutcome) -> List[Any]:
                return list(
                    refusals.policy_hits.get(outcome.task_id)
                    or refusals.policy_paths.get(outcome.task_id) or []
                )

            outside = [
                o for o in refused
                if any(getattr(hit, "outside", False) for hit in hits_of(o))
            ]
            fixable = [o for o in refused if o not in outside]
            if outside:
                lines[0] = (
                    f"To go on ({policy_outside_note([h for o in outside for h in hits_of(o)])}):"
                )
            clause = policy_allow_clause(
                [hit for o in fixable for hit in hits_of(o)]
            ) if policy and fixable else None
            offered = bool(fixable or self._ctx.kind != "implement")
            if offered:
                lines.append(
                    "  - "
                    + (f"your call: {clause}" if clause else "fix what the details name")
                    + ", then resume this phase; it is checked again before it is "
                    "dispatched, and the tasks after it follow:"
                )
                lines.append(f"        {resume}")
            for outcome in (refused if self._ctx.kind == "implement" else ()):
                task_id = outcome.task_id
                dependents = [
                    dep for dep in self._dependents_of(task_id)
                    if dep not in already and dep not in manual
                    and self._task_by_id(dep) is not None
                ]
                accept = cmds.get("accept", "").replace("{task_id}", task_id) or (
                    f"add --human-task {task_id}=done to the resume command"
                )
                skip = cmds.get("skip", "").replace("{task_id}", task_id) or (
                    f"add --human-task {task_id}=skip to the resume command"
                )
                lines.append(
                    f"  - {'or go on without it' if offered else f'go on without {task_id}'}"
                    f": {skip} ({task_id}"
                    + (f" and the tasks that depend on it, {', '.join(dependents)},"
                       if dependents else "")
                    + f" stay undone), or, once you have made its change "
                    f"yourself, {accept} ({task_id} is treated as done and the "
                    f"tasks after it run)."
                )
            return lines
        if checks:
            lines.append(
                "  - fix what the check reported in the code — by hand, or run "
                "the review-code phase and then apply-code-fixes"
                + (":" if cmds.get("review") and cmds.get("fix") else "")
            )
            if cmds.get("review") and cmds.get("fix"):
                lines.append(f"        {cmds['review']}")
                lines.append(f"        {cmds['fix']}")
            lines.append(
                "    then resume this phase; the check runs again and the "
                "tasks after it follow:"
            )
            lines.append(f"        {resume}")
        elif acceptable and all(o.applied_without_changes for o in acceptable):
            lines.append(
                "  - resume this phase and it is dispatched again, then the "
                "tasks after it (if its runner again says it made the change "
                "without making it, run the phase on another model, or make "
                "the change yourself and answer as below):"
            )
            lines.append(f"        {resume}")
        elif acceptable:
            lines.append(
                "  - fix what the task reported, then resume this phase; it is "
                "dispatched again and the tasks after it follow:"
            )
            lines.append(f"        {resume}")
        elif stop.get("timed_out") and any(o.files_touched for o in failed):
            lines.append(
                "  - its edits are kept in place: resume this phase and it is "
                "dispatched again on top of them to finish what is left, then "
                "the ones never reached follow (or restore the batch with the "
                "command above first, to start it over; if it runs out of time "
                "again, raise driver.subagent_timeout_s or run it on a faster "
                "model):"
            )
            lines.append(f"        {resume}")
        elif any(o.files_touched for o in failed):
            lines.append(
                "  - inspect the half-applied state (restore the batch with the "
                "command above, or keep it), fix the cause, then resume this "
                "phase; the failed batch is dispatched again and the ones never "
                "reached follow:"
            )
            lines.append(f"        {resume}")
        elif any(o.bytes_moved for o in failed):
            # It moved only files with no rollback point, so
            # there is no restore command to name.
            lines.append(
                "  - inspect the files it changed that cannot be restored "
                "automatically (named above) and put them right by hand, fix "
                "the cause, then resume this phase; the failed batch is "
                "dispatched again and the ones never reached follow:"
            )
            lines.append(f"        {resume}")
        else:
            # No byte moved (a timeout, a prose reply, a
            # refused runner), so there is nothing half-applied to inspect —
            # which the block's closing line says (once).
            lines.append(
                "  - fix the cause the details name, then resume this phase; "
                "the failed batch is dispatched again and the ones never "
                "reached follow:"
            )
            lines.append(f"        {resume}")
        if self._ctx.kind != "implement":
            # `--human-task` is implement's flag, save the one
            # answer an apply phase's partial application takes when its
            # report left items out: keep it and go on.
            for outcome in failed:
                if self._ctx.kind in APPLY_WRITE_KINDS and outcome.unapplied_ids:
                    skip = cmds.get("skip", "").replace(
                        "{task_id}", outcome.task_id
                    ) or (
                        f"add --human-task {outcome.task_id}=skip to the "
                        f"resume command"
                    )
                    lines.append(
                        f"  - or {self._keep_partial_clause(outcome)}: {skip}"
                    )
            return lines
        for outcome in acceptable:
            task_id = outcome.task_id
            dependents = [
                dep for dep in self._dependents_of(task_id)
                if dep not in already and dep not in manual
                and self._task_by_id(dep) is not None
            ]
            after = sorted(stop.get("not_run") or [])
            accept = cmds.get("accept", "").replace("{task_id}", task_id) or (
                f"add --human-task {task_id}=done to the resume command"
            )
            skip = cmds.get("skip", "").replace("{task_id}", task_id) or (
                f"add --human-task {task_id}=skip to the resume command"
            )
            undone = (
                f" and the tasks that depend on it, {', '.join(dependents)}, "
                f"stay undone)." if dependents else " stays undone)."
            )
            if outcome.applied_without_changes:
                # Going on without it first, as the recorded
                # answers order them (`stop_answers`).
                lines.append(
                    f"  - or go on without it: {skip} ({task_id}"
                    + undone[:-1]
                    + f", or, once you have made its change yourself: {accept} "
                    f"({task_id} is treated as done"
                    + (f"; {', '.join(after)} then run" if after else "")
                    + ")."
                )
            else:
                lines.append(
                    f"  - or accept the failure and go on without it: {accept} "
                    f"({task_id} is treated as satisfied"
                    + (f"; {', '.join(after)} then run" if after else "")
                    + f"), or {skip} ({task_id}" + undone
                )
            if outcome.not_rerun:
                retry = cmds.get("retry", "").replace("{task_id}", task_id) or (
                    f"add --human-task {task_id}=retry to the resume command"
                )
                lines.append(
                    f"  - or run the check again anyway (after installing a tool "
                    f"it needs, say): {retry}."
                )
        return lines

    def held_by_checks_lines(
        self, result: Optional[Any], failed: Sequence[TaskOutcome],
    ) -> List[str]:
        """The answers of each check with findings that holds tasks back, for
        any stop's way forward.

        A stop is not where those tasks wait: a ``--resume`` that changes no
        file leaves the check's findings standing and the tasks held, so a
        stop that offered only ``--resume`` left the user one stop away from
        the next. Each check gets the three answers the end-of-run check
        hold names (:meth:`check_block_message`), and when the stop leaves
        more than one task to answer, one resume command carrying them all.
        """
        if result is None or not result.blocked_by_check:
            return []
        cmds = self._user_commands
        found = result.check_findings()
        blocked = result.blocked_by_check
        checks = self.blocking_checks(result)
        lines: List[str] = []
        for check_id in checks:
            waiting = sorted(tid for tid, cid in blocked.items() if cid == check_id)
            findings = found.get(check_id) or []
            accept = cmds.get("accept", "").replace("{task_id}", check_id) or (
                f"add --human-task {check_id}=done to the resume command"
            )
            skip = cmds.get("skip", "").replace("{task_id}", check_id) or (
                f"add --human-task {check_id}=skip to the resume command"
            )
            retry = cmds.get("retry", "").replace("{task_id}", check_id) or (
                f"add --human-task {check_id}=retry to the resume command"
            )
            lines.append(
                f"  - {check_id}'s check reported problems and holds back "
                f"{', '.join(waiting)}"
                + (f" ({clip('; '.join(findings), 300)})" if findings else "")
                + ": a resume runs it again only once the files changed, so "
                f"fix what it reported (by hand, or review-code then "
                f"apply-code-fixes) and resume; or accept its findings: "
                f"{accept} ({', '.join(waiting)} then run, told that you "
                f"accepted the findings, which stay listed for review-code), "
                f"or {skip} ({check_id} and "
                f"{', '.join(waiting)} stay undone), or run its check again on "
                f"unchanged files: {retry}."
            )
        answers = [f"--human-task {check_id}=done" for check_id in checks] + [
            f"--human-task {o.task_id}=skip" for o in failed
            if o.task_id in _write_context.refusals_of(result).before_dispatch
            or (o.write_outcome == WRITE_CLEAN_FAILURE and not o.bytes_moved)
        ]
        if len(answers) > 1:
            combined = " ".join(answers)
            example = cmds.get("answers", "").replace("{answers}", combined) or (
                f"the resume command with {combined}"
            )
            lines.append(
                f"  - one resume command takes several answers, for example: "
                f"{example}"
            )
        return lines

    def accounting(self, result: Any) -> Dict[str, Any]:
        """Every task of the decomposition in exactly one bucket.

        ``done`` is this run's ``ok`` outcomes (resume skips included) plus the
        earlier runs' ``ok`` rows; ``failed`` this run's failed outcomes;
        ``not_run`` the tasks the stop left undispatched; ``accepted`` the
        failed tasks answered ``done``; ``completed_manual`` the human tasks
        answered ``done`` (they counted in ``total`` and sat in
        no bucket, so a five-task line summed to four); ``deferred`` the human
        tasks the strategy skipped and ``skipped_dependents`` the tasks
        skipped with a skipped one. The buckets add up to ``total``, which is
        the test ``summary.md``'s accounting line is written to. ``accepted``
        and ``completed_manual`` include the answers an earlier run recorded
        for tasks this resume did not materialize (``answered_done_on_record``).
        """
        rows = result.report_rows()
        plan = result.human_plan
        by_id = {str(t.get("task_id", "")): t for t in self._ctx.tasks}
        failed = sorted({o.task_id for o in result.outcomes if not o.ok})
        answered = set(plan.accepted) | set(plan.completed)
        done = sorted({
            str(row.get("task_id"))
            for row in rows
            if row.get("status") == STATUS_OK and str(row.get("task_id")) not in failed
            and str(row.get("task_id")) not in answered
        })
        # A skip the user chose (a pause-and-ask "Skip", `--human-task
        # <id>=skip` on a failed task) is its own bucket: the seed is neither
        # deferred work nor "skipped with a skipped task".
        declined = sorted(
            tid for tid, reason in plan.skipped.items() if is_declined_reason(reason)
        )
        deferred = sorted(
            tid for tid in plan.skipped
            if tid not in declined
            and ((by_id.get(tid) or {}).get("executor_role") == "human"
                 or (by_id.get(tid) or {}).get("is_human"))
        )
        skipped_dependents = sorted(
            tid for tid in plan.skipped if tid not in deferred and tid not in declined
        )
        accepted = sorted(plan.accepted)
        completed_manual = sorted(plan.completed)
        not_run = sorted(result.not_run)
        ids = set(done) | set(failed) | set(deferred) | set(skipped_dependents) \
            | set(declined) | set(accepted) | set(completed_manual) | set(not_run) \
            | set(by_id)
        check_findings = sorted({
            str(row.get("task_id"))
            for row in rows
            if str(row.get("task_id")) in done and row_check_findings(row)
        })
        return {
            "total": len(ids),
            "done": done,
            "check_findings": check_findings,
            "failed": failed,
            "not_run": not_run,
            "blocked": {
                tid: cid for tid, cid in result.blocked_by_check.items()
                if tid in result.not_run
            },
            "accepted_with_findings": sorted(
                tid for tid in accepted
                if ACCEPTED_WITH_FINDINGS_MARK in str(plan.accepted.get(tid) or "")
            ),
            "accepted": accepted,
            "completed_manual": completed_manual,
            "declined": declined,
            "deferred": deferred,
            "skipped_dependents": skipped_dependents,
        }

    def record_stop(
        self, result: Any, batch_index: int,
        failed: Sequence[TaskOutcome], *, refusal: Optional[str] = None,
    ) -> None:
        """Account for every task the stop left unrun, and keep the stop record.

        Called on both stop paths before the message is built: every
        materialized task that is not human, not skipped, not accepted and has
        no outcome in this run was never dispatched. Each gets a reason on its
        ``pending`` status (``task_status_reasons``), so the implementation
        record review-code reads says why it is pending rather than leaving it
        indistinguishable from a task nobody has looked at.
        """
        failed_ids = [o.task_id for o in failed]
        seen = {o.task_id for o in result.outcomes}
        plan = result.human_plan
        cause = (
            f"{', '.join(failed_ids)} failed" if failed_ids
            else (f"batch {batch_index} was refused" if refusal else
                  f"the loop stopped at batch {batch_index}")
        )
        # A task a check with findings already kept from running keeps that
        # reason: the stop is not why it did not run.
        for task_id, check_id in result.blocked_by_check.items():
            result.not_run[task_id] = _check_records.blocked_by_check_reason(check_id)
        for task in self._ctx.tasks:
            task_id = str(task.get("task_id", ""))
            if (not task_id or task_id in seen or plan.is_skipped(task_id)
                    or task_id in plan.accepted
                    or task_id in result.not_run
                    or task.get("executor_role") == "human"):
                continue
            result.not_run[task_id] = (
                f"not run — {self._ctx.phase} stopped at batch {batch_index} "
                f"({cause}) before this task was dispatched"
            )
        self.record_not_run_in_state(result)
        self._restamp_check_trees(result)
        first = failed[0] if failed else None
        is_check = bool(
            first is not None and self._ctx.kind == "implement"
            and not declared_file_set(self._task_by_id(first.task_id) or {})
        )
        acceptable = bool(
            first is not None and first.write_outcome == WRITE_CLEAN_FAILURE
            and not first.bytes_moved
        )
        result.stop = {
            "batch_index": batch_index,
            "failed_task_ids": failed_ids,
            "task_id": first.task_id if first else None,
            "kind": "check" if is_check else ("task" if first else "refusal"),
            "what": (
                self.failure_sentence(first, result.refusals) if first
                else (refusal or "")
            ),
            "reported": (first.runner_notes if first else None),
            "not_run": sorted(result.not_run),
            "acceptable": acceptable,
            "not_rerun": bool(first is not None and first.not_rerun),
        }
        if first is not None and first.task_id in result.refusals.before_dispatch:
            # Nothing was dispatched, so there is nothing
            # half-applied, and the task can be skipped or accepted.
            result.stop["refused_before_dispatch"] = True
            result.stop["policy"] = first.write_outcome == WRITE_POLICY_VIOLATION
            if result.stop["policy"]:
                # The files its way forward names. And the rule that refused each, which words it.
                result.stop["policy_paths"] = list(
                    result.refusals.policy_paths.get(first.task_id) or [])
                result.stop["policy_rules"] = [
                    hit.to_dict()
                    for hit in result.refusals.policy_hits.get(first.task_id) or []
                ]
        if first is not None and first.applied_without_changes:
            # It said `applied` and changed nothing, twice.
            result.stop["applied_without_changes"] = True
        # Whether the stop left bytes a human has to look at ("the half-applied state is
        # left in place" followed a refusal before
        # dispatch and a clean failure, where nothing was half-applied). What the sweep
        # observed, not what the rollback store holds,
        # so a file with no rollback point counts — and is named.
        result.stop["bytes_moved"] = any(o.bytes_moved for o in failed)
        if (
            self._ctx.kind in APPLY_WRITE_KINDS and first is not None
            and first.unapplied_ids
        ):
            # The items its readable report left out of both
            # `ids` and `declined` — what `--human-task <id>=skip` answers.
            result.stop["unapplied_ids"] = list(first.unapplied_ids)
        # A batch killed at its time
        # limit after its edits landed. The edits stay; the plain way forward
        # is the resume, which dispatches it again on top of them.
        if first is not None and first.write_outcome == WRITE_PARTIAL and (
            self.ran_out_of_time(first)
        ):
            result.stop["timed_out"] = True
        unrestorable = sorted({p for o in failed for p in o.unrestorable})
        if unrestorable:
            result.stop["unrestorable"] = unrestorable
        if result.blocked_by_check:
            # The tasks a check with findings holds, which this stop's own
            # remedy does not release.
            result.stop["blocked"] = dict(sorted(result.blocked_by_check.items()))
            result.stop["check_task_ids"] = self.blocking_checks(result)
        answers = self.stop_answers(result, failed)
        if answers:
            result.stop["answers"] = answers
        why = self.stop_resume_why(result, failed)
        if why:
            result.stop["resume_why"] = why
        self.set_stop_headline(result.stop)

    def stop_answers(
        self, result: Any, failed: Sequence[TaskOutcome] = (),
    ) -> List[Dict[str, Any]]:
        """The ``--human-task`` answers this stop offers, as data.

        ``[{"flags": [...], "why": ...}]``, each a resume command's flags
        (``--resume`` first) and one plain clause saying what it does, in the
        order a user weighs them: the one combined command that goes on
        without fixing anything (when more than one task needs an answer),
        then each task's own answers — a task refused before dispatch
        (``skip``, ``done``), a clean failure (``done``, ``skip``, ``retry``
        when it was not run again) and each check whose findings hold tasks
        back (``done``, ``skip``, ``retry``). The same answers the stop
        message names (:meth:`way_forward_lines`,
        :meth:`held_by_checks_lines`, :meth:`check_block_message`); a
        partial application offers none, since it is inspected first.

        Recorded on the stop (``write_batch_report.json``, the mirror) so
        ``util next-command --blocked implement`` can hand the tool routes
        each one as a command the user types and an ``options`` entry: on
        live run 5 the answers lived only in the result's ``error`` and the
        hosts relayed them in two of four first stops. On an apply phase
         the one answer is ``--human-task <batch>=skip`` for a
        partial application whose report left items out (``unapplied_ids``):
        keep what it applied and go on without them — Codex racing run 7's
        08b resumed into the same stop with nothing else to offer.
        """
        if self._ctx.kind != "implement":
            first = failed[0] if failed else None
            if (
                self._ctx.kind in APPLY_WRITE_KINDS and first is not None
                and first.unapplied_ids
            ):
                return [{
                    "flags": ["--resume", "--human-task", f"{first.task_id}=skip"],
                    "why": self._keep_partial_clause(first),
                }]
            return []
        already = set(result.human_plan.skipped)
        manual = {
            str(t.get("task_id", "")) for t in self._ctx.tasks
            if t.get("executor_role") == "human" or t.get("is_human")
        }

        def undone_with(task_id: str) -> List[str]:
            return [
                dep for dep in self._dependents_of(task_id)
                if dep not in already and dep not in manual
                and self._task_by_id(dep) is not None
            ]

        refused = [o for o in failed if o.task_id in result.refusals.before_dispatch]
        acceptable = [
            o for o in failed
            if o.task_id not in result.refusals.before_dispatch
            and o.write_outcome == WRITE_CLEAN_FAILURE and not o.bytes_moved
        ]
        blocked = result.blocked_by_check
        return _stop_answers.compose_stop_answers(
            refused=[o.task_id for o in refused],
            failed=[
                _stop_answers.FailedAnswerable(
                    task_id=o.task_id,
                    unlanded=bool(o.applied_without_changes),
                    not_rerun=bool(o.not_rerun),
                )
                for o in acceptable
            ],
            checks=self.blocking_checks(result) if blocked else [],
            blocked=blocked,
            findings=result.check_findings(),
            undone_with=undone_with,
        )

    def stop_resume_why(
        self, result: Any, failed: Sequence[TaskOutcome] = (),
    ) -> Optional[str]:
        """What this stop's plain ``--resume`` does on an unchanged tree
        (``write_outcomes.resume_why``), recorded on the stop as
        ``resume_why`` beside its ``answers``. A check is judged on the tree
        as the stop leaves it, taken once and only when a check needs
        judging (:meth:`verdict_holds_tree`, the comparison
        :meth:`CheckHolds.unchanged_since_failure` and :meth:`CheckHolds.check_findings_rerun`
        make)."""
        tree: List[Optional[str]] = []

        def kept_on(task_id: str, *, failed_check: bool) -> bool:
            if not tree:
                tree.append(self._tree_fingerprint())
            return self.verdict_holds_tree(task_id, tree[0], failed=failed_check)

        return _write_outcomes.resume_why(
            result.outcomes, failed, _write_outcomes.ResumeContext(
                kind=self._ctx.kind,
                tasks=self._ctx.tasks,
                skipped=set(result.human_plan.skipped),
                refused_before_dispatch=result.refusals.before_dispatch,
                refused_policy_hits=result.refusals.policy_hits,
                blocked=result.blocked_by_check,
                blocking_checks=lambda: self.blocking_checks(result),
                dependents_of=self._dependents_of,
                implement_done=lambda: _stop_answers.implement_tasks_done(self._ctx.state),
                kept_on=kept_on,
            ),
        )

    def verdict_holds_tree(
        self, task_id: str, tree: Optional[str], *, failed: bool,
    ) -> bool:
        """Whether a resume on *tree* keeps *task_id*'s check from running:
        its result file holds a check's verdict (a failed one under
        *failed*, as :meth:`CheckHolds.unchanged_since_failure` reads it) stamped with
        that very tree (``verdict.tree_fingerprint``), the comparison
        :meth:`CheckHolds.unchanged_since_failure` and :meth:`CheckHolds.check_findings_rerun`
        make. No file, no stamp, another tree or a tree git cannot measure:
        the resume dispatches it again."""
        if tree is None:
            return False
        task = self._task_by_id(task_id)
        if task is None:
            return False
        try:
            own = resolve_output_target(task, self._ctx.phase_dir)
        except ResultRejected:
            return False
        if own is None:
            return False
        try:
            data = json.loads(Path(own).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return False
        verdict = data.get("verdict") if isinstance(data, dict) else None
        return (
            isinstance(verdict, dict) and bool(verdict.get("verification_only"))
            and (not failed or not verdict.get("ok"))
            and verdict.get("tree_fingerprint") == tree
        )

    def record_not_run_in_state(self, result: Any) -> None:
        """Give each ``result.not_run`` task its reason on a ``pending`` status.

        Only a task with no status or a ``pending`` one: a status an earlier
        run recorded (completed, failed, skipped) is never overwritten.
        """
        if not result.not_run:
            return
        with self._effects_lock:
            for task_id, reason in result.not_run.items():
                current = None
                try:
                    current = self._ctx.state.get_task_status(task_id)
                except Exception:  # noqa: BLE001 - advisory
                    current = None
                if current in (None, "pending"):
                    self._ctx.state.update_task_status(task_id, "pending", reason=reason)
            try:
                self._ctx.state.save()
            except Exception as exc:  # noqa: BLE001 - bookkeeping must not fail a phase
                self._ctx.log(f"[write-subagents] warning: could not record the not-run tasks: {exc}")

    def blocking_checks(self, result: Any) -> List[str]:
        """The check tasks that kept a task from running, in task order."""
        blocking = set(result.blocked_by_check.values())
        order = [str(t.get("task_id", "")) for t in self._ctx.tasks]
        return sorted(
            blocking, key=lambda tid: (order.index(tid) if tid in order else len(order), tid),
        )

    def record_check_block(self, result: Any) -> None:
        """Account for the tasks a check with findings kept from running.

        The end-of-loop counterpart of :meth:`record_stop`:
        every task that could run has run, and the ones in
        ``result.blocked_by_check`` were left out. Each is ``not run`` with
        :func:`blocked_by_check_reason` on its ``pending`` status, and the
        stop record (``kind: "check-findings"``) names the checks, what they
        reported and the tasks waiting for them — the record the summary,
        ``write_batch_report.json``, the mirror and the result line's
        ``error`` render from.
        """
        for task_id, check_id in result.blocked_by_check.items():
            result.not_run[task_id] = _check_records.blocked_by_check_reason(check_id)
        self.record_not_run_in_state(result)
        self._restamp_check_trees(result)
        checks = self.blocking_checks(result)
        found = result.check_findings()
        first = checks[0]
        findings = found.get(first) or []
        result.stop = {
            "batch_index": None,
            "failed_task_ids": [],
            "task_id": first,
            "kind": "check-findings",
            "check_task_ids": checks,
            "blocked": dict(sorted(result.blocked_by_check.items())),
            "what": (
                f"its check reported {len(findings)} problem(s)"
                if findings else "its check reported problems"
            ),
            "reported": clip("; ".join(findings), 600) or None,
            "not_run": sorted(result.not_run),
            "acceptable": True,
            "not_rerun": False,
        }
        answers = self.stop_answers(result)
        if answers:
            result.stop["answers"] = answers
        why = self.stop_resume_why(result)
        if why:
            result.stop["resume_why"] = why
        self.set_stop_headline(result.stop)

    def manual_gate(self, result: Any) -> Optional[Dict[str, Any]]:
        """The manual-task gates (:func:`plan_manual_gates`) when this run
        must stop on them, else ``None``: an implement run
        that started no runner, on an implement not on record completed (a
        resume of a completed one that runs nothing keeps it completed), whose every
        code task left waits on a manual task not
        recorded done, one the user can do now among them."""
        if (self._ctx.kind != "implement" or self._ctx.dry_run
                or not _write_context.has_state(self._ctx.state)):
            # Without a state there is no record to gate on.
            return None
        if any(self._started_a_runner(o, result.refusals) for o in result.outcomes):
            return None
        try:
            if self._ctx.state.is_phase_completed(self._ctx.phase):
                return None
        except Exception:  # noqa: BLE001 - a state fake without the record
            return None
        gates = self.manual_gates(result.human_plan)
        if not gates or not gates.get("gated") or not gates.get("waiting"):
            return None
        return gates

    def record_manual_gate(
        self, result: Any, gates: Dict[str, Any],
    ) -> None:
        """The stop record of a run a manual task gates (``kind:
        "manual-gate"``): the gating manual tasks (the ones the user can do
        now that code tasks wait on), the code tasks waiting on each, the
        resume that records them done (``resume_flags``) and what it does
        (``resume_why``), and the headline the result line's ``error``
        carries."""
        waiting = {
            manual: list(codes) for manual, codes in sorted(gates["waiting"].items())
            if codes
        }
        gating = sorted(waiting, key=_metrics._id_key)
        flags: List[str] = ["--resume"]
        for manual in gating:
            flags += ["--human-task", f"{manual}=done"]
        held = sorted({code for codes in waiting.values() for code in codes},
                      key=_metrics._id_key)
        result.stop = {
            "batch_index": None,
            "failed_task_ids": [],
            "task_id": gating[0],
            "kind": "manual-gate",
            "manual_task_ids": gating,
            "waiting": waiting,
            "what": (
                f"every code task left waits on "
                f"{'manual task' if len(gating) == 1 else 'manual tasks'} "
                f"{', '.join(gating)}, not recorded done"
            ),
            "reported": None,
            "not_run": [],
            "acceptable": True,
            "not_rerun": False,
            "resume_flags": flags,
            "held_task_ids": held,
        }
        why = self.manual_gate_why(gating, waiting)
        if why:
            result.stop["resume_why"] = why
        # The user's decline beside
        # that resume, as an answer the section lists.
        answers = self.manual_gate_answers(gating, waiting)
        if answers:
            result.stop["answers"] = answers
        # The: and beside it the line without the way
        # on the section carries (its resume records the gate done), which
        # the tool routes relay in the `error`'s place.
        self.set_stop_headline(result.stop)

    def manual_gate_entry(
        self, gating: Sequence[str], waiting: Mapping[str, Sequence[str]],
    ) -> Dict[str, Any]:
        """The gate as the workflow payload's ``implement`` entry gives it
        to ``next_phase``'s gate words, over this run's titles."""
        return {
            "manual_close_ids": list(gating),
            "manual_waiting": {k: list(v) for k, v in waiting.items()},
            "manual_tasks": [
                {"id": manual, "title": self.task_title(manual)}
                for manual in gating
            ],
        }

    def manual_gate_why(
        self, gating: Sequence[str], waiting: Mapping[str, Sequence[str]],
    ) -> Optional[str]:
        """What the gate's resume does, in ``manual_tasks.manual_gate_why``'s
        words, over this run's titles."""

        try:
            return manual_gate_why(self.manual_gate_entry(gating, waiting))
        except Exception:  # noqa: BLE001 - advisory wording
            return None

    def manual_gate_answers(
        self, gating: Sequence[str], waiting: Mapping[str, Sequence[str]],
    ) -> List[Dict[str, Any]]:
        """The gate's other ways on, ``manual_tasks.manual_gate_decline_answers``
        The user's ``--human-task <id>=skip`` for each
        gating manual task, recorded on the stop as its ``answers``."""

        try:
            return manual_gate_decline_answers(self.manual_gate_entry(gating, waiting))
        except Exception:  # noqa: BLE001 - advisory: the resume stands
            return []

    def task_title(self, task_id: str) -> Optional[str]:
        """*task_id*'s title from this run's tasks, else ``state.json``'s
        ``task_titles``, else ``None``."""
        task = self._task_by_id(task_id) or {}
        title = task.get("task_title") or task.get("title")
        if not title:
            try:
                title = (self._ctx.state.get("task_titles") or {}).get(task_id)
            except Exception:  # noqa: BLE001 - a state fake without the map
                title = None
        return str(title) if title else None

    def manual_gate_message(self, result: Any) -> List[str]:
        """The exit-3 block of a run a manual task gates: nothing ran and
        why, each gating manual task with the code tasks waiting on it, the
        account of every task, and the one way on."""
        stop = result.stop or {}
        gating = list(stop.get("manual_task_ids") or [])
        waiting = stop.get("waiting") or {}
        lines = [
            "",
            f"ERROR: {self._ctx.phase} ran nothing: every code task left waits on "
            f"{'a manual task' if len(gating) == 1 else 'manual tasks'} not "
            f"recorded done, and implement does not do a manual task:",
        ]
        for manual in gating:
            codes = sorted(waiting.get(manual) or [], key=_metrics._id_key)
            lines.append(
                f"  {manual}{self.task_label(manual)}: {len(codes)} code "
                f"task(s) wait on it ({_check_records._id_range(codes)})"
            )
        lines.extend(self.account_lines(result))
        flags = list(stop.get("resume_flags") or [])
        answers = " ".join(flags[1:])
        template = self._user_commands.get("answers") or ""
        command = template.replace("{answers}", answers) if "{answers}" in template else ""
        it = "it" if len(gating) == 1 else "them"
        lines.append("To go on:")
        lines.append(
            f"  - do {', '.join(gating)} by hand, then resume this phase "
            f"recording {it} done; the code tasks that wait on {it} then run:"
        )
        lines.append(f"        {command or 'add ' + answers + ' to the resume command'}")
        # Or the user's decline.
        for entry in stop.get("answers") or []:
            skips = " ".join(list(entry.get("flags") or [])[1:])
            spelled = (
                template.replace("{answers}", skips) if "{answers}" in template else "")
            lines.append(f"  - or, {entry.get('why')}:")
            lines.append(f"        {spelled or 'add ' + skips + ' to the resume command'}")
        return lines

    def check_block_message(self, result: Any) -> List[str]:
        """The exit-3 block after a run whose checks kept tasks from running.

        Names each check, what it reported and the tasks waiting for it, the
        account of every task, and the three ways forward: fix and resume
        (the check runs again), accept the findings (``=done``: the waiting
        tasks run, the findings stay listed for review-code) or skip.
        """
        cmds = self._user_commands
        found = result.check_findings()
        blocked = result.blocked_by_check
        checks = self.blocking_checks(result)
        lines = [
            "",
            f"ERROR: {self._ctx.phase} did not run {len(blocked)} task(s) that depend "
            f"on a check that reported problems:",
        ]
        for check_id in checks:
            findings = found.get(check_id) or []
            waiting = sorted(tid for tid, cid in blocked.items() if cid == check_id)
            lines.append(
                f"  {check_id}{self.task_label(check_id)} reported "
                f"{len(findings)} problem(s): {clip('; '.join(findings), 600)}"
            )
            lines.append(f"      not run: {', '.join(waiting)}")
        lines.extend(self.account_lines(result))
        resume = cmds.get("resume") or "re-invoke this phase with --resume"
        lines.append("To go on:")
        lines.append(
            "  - fix what the check reported in the code — by hand, or run the "
            "review-code phase and then apply-code-fixes"
            + (":" if cmds.get("review") and cmds.get("fix") else "")
        )
        if cmds.get("review") and cmds.get("fix"):
            lines.append(f"        {cmds['review']}")
            lines.append(f"        {cmds['fix']}")
        lines.append(
            "    then resume this phase; the check runs again and, once it "
            "passes, the tasks after it follow (a resume that changes no file "
            "does not run it again):"
        )
        lines.append(f"        {resume}")
        for check_id in checks:
            waiting = sorted(tid for tid, cid in blocked.items() if cid == check_id)
            accept = cmds.get("accept", "").replace("{task_id}", check_id) or (
                f"add --human-task {check_id}=done to the resume command"
            )
            skip = cmds.get("skip", "").replace("{task_id}", check_id) or (
                f"add --human-task {check_id}=skip to the resume command"
            )
            retry = cmds.get("retry", "").replace("{task_id}", check_id) or (
                f"add --human-task {check_id}=retry to the resume command"
            )
            lines.append(
                f"  - or accept {check_id}'s findings and run the tasks after "
                f"it: {accept} ({', '.join(waiting)} then run, told that you "
                f"accepted the findings, which stay listed for review-code), "
                f"or {skip} ({check_id} and "
                f"{', '.join(waiting)} stay undone)."
            )
            lines.append(
                f"  - or run {check_id}'s check again on unchanged files: {retry}."
            )
        return lines

    def set_stop_headline(
        self, stop: Dict[str, Any], *, tail: Optional[str] = None,
    ) -> None:
        """Record *stop*'s ``headline`` and, beside it, the same line
        without the ways forward its resume section carries
        (``headline_beside_section``, :data:`HEADLINE_BESIDE_SECTION_KEY`).

        At a stop the Codex host relayed the
        whole ``error`` line, whose "To go on (your call): … add --human-task
        T005=skip … --human-task T002=done …" restated every answer the
        ready section then gave as commands. ``util next-command --blocked``
        hands the tool routes this second line beside the section, and the
        servers relay it in the ``error``'s place: what stopped, what it
        reported, what did not run, the fixes only the user can make (a
        ``driver.write_paths`` change, fixing what a check reported), and
        the tests line, never an answer. Recorded only when it differs and
        every ``--human-task`` answer it leaves out is one of the stop's own
        ``answers``, which the section lists; else the key is dropped, and
        the full line stays the only one.
        """
        stop["headline"] = self.stop_headline(stop, tail=tail)
        beside = self.stop_headline(stop, tail=tail, beside_section=True)
        if beside != stop["headline"] and _stop_answers.answers_cover(
                stop["headline"], beside, stop):
            stop[_stop_answers.HEADLINE_BESIDE_SECTION_KEY] = beside
        else:
            stop.pop(_stop_answers.HEADLINE_BESIDE_SECTION_KEY, None)

    def stop_headline(
        self, stop: Dict[str, Any], *, tail: Optional[str] = None,
        beside_section: bool = False,
    ) -> str:
        """One plain line for the result line's ``error``: what the hosts relay
        as "the last line it left", ending with *tail* (the line saying nothing
        ran the repository's tests) when one is owed.

        The
        line is bounded (``cli_common.ERROR_MAX_CHARS``), and the bound used
        to cut its end — the ``--human-task <batch>=skip`` sentence of an
        apply stop, the remedy and the ``--human-task T002=done`` answer of a
        check-findings stop — while the model's quoted words were kept whole.
        One rule now fits every stop headline (:func:`fit_stop_headline`):
        the model's quoted words give way first, then the list of tasks not
        run, then the task titles named in it (shorter, then none), and only
        then the head itself; the remedy, the answers and *tail* stay whole.
        """
        caps = (None,) + _stop_answers.STOP_HEADLINE_LABEL_CAPS
        for cap in caps:
            parts = self.stop_headline_parts(
                stop, label_cap=cap, beside_section=beside_section)
            fitted = _stop_answers.fit_stop_headline(
                *parts, tail=tail, last_resort=cap == caps[-1],
            )
            if fitted is not None:
                return fitted
        raise AssertionError("unreachable: the last resort always fits")

    def stop_headline_parts(
        self, stop: Dict[str, Any], *, label_cap: Optional[int] = None,
        beside_section: bool = False,
    ) -> Tuple[str, Optional[str], List[str], List[str], str]:
        """``(head, reported, not_run, body, terminator)`` of a stop's
        headline (:meth:`stop_headline`): *head* says what stopped and
        names the task, *reported* is the model's own words, *not_run* the
        tasks the stop left, *body* the remedy and the answers, in order.
        A task title in *head* is cut to *label_cap* characters (``0``: left
        out). *beside_section*: *body* without the ways
        forward a resume section carries — every ``--human-task`` answer
        and a bare "resume this phase" — keeping each fix only the user can
        make before the resume (:meth:`set_stop_headline`)."""

        def label(task_id: str) -> str:
            text = self.task_label(task_id)
            if label_cap is None or not text:
                return text
            if label_cap <= 0:
                return ""
            inner = text[2:-1]
            if len(inner) <= label_cap:
                return text
            return f" ({clip(inner, label_cap + 1)})"

        task_id = stop.get("task_id")
        reported = stop.get("reported") or None
        if stop.get("kind") == "answer-refused":
            # A `--human-task <batch>=skip` this run refused.
            return (
                f"{self._ctx.phase} {stop.get('what')}", None, [],
                ["Nothing was dispatched and no file was changed.",
                 _write_outcomes.REFUSED_SKIP_WAY_FORWARD],
                ".",
            )
        if stop.get("kind") == "manual-gate":
            gating = list(stop.get("manual_task_ids") or [task_id])
            waiting = {
                mid: list((stop.get("waiting") or {}).get(mid) or [])
                for mid in gating
            }
            held = sorted(
                {code for codes in waiting.values() for code in codes},
                key=_metrics._id_key)
            head = _human_task_plan.manual_gate_head(
                self._ctx.phase, {mid: label(mid) for mid in gating}, waiting)
            # Beside the section, what stopped and why: its one way on is
            # the section's resume.
            return head, None, held, (
                [] if beside_section else [_human_task_plan.manual_gate_way_on(gating)]), "."
        if stop.get("kind") == "check-findings":
            checks = stop.get("check_task_ids") or [task_id]
            named = ", ".join(f"{cid}{label(cid)}" for cid in checks)
            head = (
                f"{self._ctx.phase} did not run {', '.join(sorted(stop.get('blocked') or {}))}: "
                f"they depend on {named}, whose check reported problems"
            )
            answer = (
                f"--human-task {task_id}=done" if len(checks) == 1
                else "--human-task <check id>=done for each check"
            )
            fix = (
                "To go on: fix what the check reported (by hand, or "
                "review-code then apply-code-fixes), then resume this phase — "
                "the check runs again"
            )
            return head, reported, [], [
                f"{fix}." if beside_section else
                f"{fix}; or accept its findings by adding "
                f"{answer} to the resume command (the tasks after it then run, "
                f"told that you accepted the findings)."
            ], "."
        if not task_id:
            return (
                f"{self._ctx.phase} stopped at batch {stop.get('batch_index')}: "
                f"{stop.get('what') or 'the batch was refused'}",
                None, [], [], "",
            )
        head = f"{self._ctx.phase} stopped at {task_id}{label(task_id)}: {stop.get('what')}"
        body: List[str] = []
        if stop.get("kind") == "check" and stop.get("acceptable"):
            fix = (
                "To go on: fix what the check reported (by hand, or review-code "
                "then apply-code-fixes), then resume this phase"
            )
            body.append(
                f"{fix}." if beside_section else
                f"{fix}; or accept the "
                f"failure by adding --human-task {task_id}=done to the resume "
                f"command (the tasks after it then run)."
            )
        elif stop.get("applied_without_changes") and stop.get("bytes_moved"):
            # The files it declares did not change, others did
            # (a plan or task-list batch is judged on its declared file).
            body.append(
                "Files outside the ones it declares changed: inspect them "
                "(restore the batch, or keep them), then resume this phase "
                "and it is dispatched again."
            )
        elif stop.get("applied_without_changes") and beside_section:
            # Its only way forward is the section's: the resume (which
            # dispatches it again) and the answers.
            body.append("Nothing changed, so there is nothing to restore.")
        elif stop.get("applied_without_changes"):
            body.append(
                "Nothing changed, so there is nothing to restore. To go on: "
                "resume this phase and it is dispatched again"
                + (
                    # Going on without it first, and `done`
                    # only for a change made by hand; implement's flag only.
                    f"; or leave it and the tasks after it undone with "
                    f"--human-task {task_id}=skip, or make its change "
                    f"yourself and add --human-task {task_id}=done to the "
                    f"resume command."
                    if self._ctx.kind == "implement" else "."
                )
            )
        elif stop.get("acceptable"):
            body.append(
                "To go on: fix what it reported, then resume this phase"
                + (
                    f"; or accept the failure by adding --human-task "
                    f"{task_id}=done to the resume command."
                    if self._ctx.kind == "implement" and not beside_section else "."
                )
            )
        elif stop.get("refused_before_dispatch") and stop.get("policy"):
            # Allowing the file stays a way forward, worded as the user's own
            # call and naming the file, beside the skip answer.
            # Worded per rule from `policy_rules` (a deny hit
            # names the deny rule; the paths alone, from a record that kept
            # no rule, get the wording right for either), and no policy
            # change at all for a file outside the repository.
            refused_rules = stop.get("policy_rules") or stop.get("policy_paths") or []
            clause = policy_allow_clause(refused_rules)
            if clause is not None:
                body.append(
                    "To go on (your call): " + clause + ", then resume this phase"
                    + (f"; {policy_skip_clause(task_id)}."
                       if self._ctx.kind == "implement" and not beside_section else ".")
                )
            elif self._ctx.kind == "implement" and beside_section:
                # Its one way forward, the skip, is the section's.
                note = policy_outside_note(refused_rules)
                body.append(f"{note[0].upper()}{note[1:]}.")
            else:
                note = policy_outside_note(refused_rules)
                body.append(
                    f"{note[0].upper()}{note[1:]}. To go on: "
                    + (f"{policy_skip_clause(task_id, alone=True)}."
                       if self._ctx.kind == "implement"
                       else "fix what refused it, then resume this phase.")
                )
        elif stop.get("refused_before_dispatch"):
            body.append(
                "To go on: fix what refused it"
                + (
                    ", then resume this phase; or leave it and the tasks after "
                    f"it undone by adding --human-task {task_id}=skip to the "
                    "resume command."
                    if self._ctx.kind == "implement" and not beside_section
                    else ", then resume this phase."
                )
            )
        elif stop.get("bytes_moved", True) and stop.get("timed_out"):
            body.append(
                f"Its edits are kept in place. To go on: resume this phase, "
                f"and {task_id} is dispatched again on top of them to finish "
                f"what is left (or restore the batch first to start it over); "
                f"if it runs out of time again, raise driver.subagent_timeout_s "
                f"or run it on a faster model."
            )
        elif stop.get("bytes_moved", True):
            body.append(
                "To go on: inspect the half-applied state, restore or keep it, "
                "fix the cause, then resume this phase."
            )
            if stop.get("unrestorable"):
                # A moved file with no rollback point.
                names = stop["unrestorable"]
                body.append(
                    f"{', '.join(names[:5])}{', …' if len(names) > 5 else ''} "
                    f"changed and cannot be restored automatically: inspect "
                    f"{'it' if len(names) == 1 else 'them'} by hand."
                )
        else:
            body.append(
                "Nothing changed, so there is nothing to restore. To go on: "
                "fix the cause, then resume this phase."
            )
        if stop.get("unapplied_ids") and not beside_section:
            # The way out of a stop a resume only repeats.
            body.append(
                f"Or keep what it applied and go on without "
                f"{self._unapplied_words(stop['unapplied_ids'])}: add "
                f"--human-task {task_id}=skip to the resume command (recorded "
                f"as not applied, skipped at your request; the batches after "
                f"it run)."
            )
        blocked = stop.get("blocked") or {}
        for check_id in stop.get("check_task_ids") or []:
            waiting = sorted(t for t, c in blocked.items() if c == check_id)
            held = (
                f"{check_id}'s check reported problems and holds back "
                f"{', '.join(waiting)}: fix them and resume (a resume runs it "
                f"again only once the files changed)"
            )
            body.append(
                f"{held}." if beside_section else
                f"{held}, or accept its findings "
                f"by adding --human-task {check_id}=done to the resume command "
                f"({', '.join(waiting)} then run, told that you accepted them)."
            )
        return head, reported, list(stop.get("not_run") or []), body, "."

    def refusal_message(
        self, exc: ExecutorError, batch_index: int, result: Any
    ) -> List[str]:
        """A refused batch, worded like :meth:`stop_message` (D3k rung 1).

        The refusal's own text already names the offending key, the spec as
        written and the fix (one rejection formatter, ``_render_runner_rejection``),
        so this frames it rather than restating it: which batch was refused, that
        no child started for it, and what the batches before it left behind.
        """
        lines = [
            "",
            f"ERROR: batch {batch_index} was refused before any child started. No "
            f"later batch was dispatched and the {self._ctx.phase} phase is NOT marked "
            f"completed.",
            f"  - {exc.message}",
        ]
        if result.batches_dispatched:
            lines += [
                f"Batches already applied this run: "
                f"{', '.join(str(i) for i in result.batches_dispatched)} — their "
                f"pre-batch snapshots are intact under "
                f"{os.path.join(self._ctx.safety_dir, 'pre_batch')}/, and re-invoking "
                f"with --resume re-dispatches only the unfinished batches.",
                f"Audit log: {self._ctx.audit.path}",
            ]
        else:
            lines.append(
                "Nothing was dispatched and no file was modified."
            )
        lines.extend(self.account_lines(result))
        return lines

    def manual_gates(self, plan: Optional[_human_task_plan.HumanTaskPlan]) -> Optional[Dict[str, Any]]:
        """:func:`plan_manual_gates` over this run's decomposition and
        ``state.json`` as recorded, or ``None`` when it cannot be read."""
        try:
            statuses = dict(self._ctx.state.get_all_task_statuses())
        except Exception:  # noqa: BLE001 - a state fake without the map
            statuses = {}
        try:
            return _human_task_plan.plan_manual_gates(
                plan, _check_records.decomposition_graph(self._ctx.tasks, self._ctx.state), statuses)
        except Exception:  # noqa: BLE001 - advisory wording, never fatal
            return None

    def record_answer_refusal(
        self, result: Any, refused_skips: Mapping[str, str],
    ) -> None:
        """Keep a refused ``--human-task <batch>=skip`` where the tool routes
        read a stop.

        Review: the refusal was printed and nothing else, so
        the result line named no ``error`` (the tool's needs-human message
        said "Its result line names no error", run 7's #4 shape) and the
        mirror still held the stop the answer was refused for, whose
        ``answers`` ``util next-command --blocked`` handed back as the way
        forward — the answer just refused. The stop record now says the
        answer was refused, in a headline the orchestrator records as the
        result line's ``error``; it keeps the answers of the earlier stop
        that name no refused batch (an answer typed for the wrong batch
        leaves the right one standing), and the mirror's other rows are the
        earlier run's, untouched: this run dispatched nothing. *refused_skips*
        is ``ResumeEvidence.refused_skips``: each refused task id and why.
        """
        refused = dict(refused_skips)
        earlier = self._mirror_snapshot()
        before = earlier.get("stop") if isinstance(earlier.get("stop"), dict) else {}
        refused_flags = {f"{task_id}=skip" for task_id in refused}
        kept = [
            dict(entry) for entry in (before.get("answers") or [])
            if isinstance(entry, dict)
            and not refused_flags.intersection(entry.get("flags") or [])
        ]
        named = "; ".join(
            f"--human-task {task_id}=skip: {why}" for task_id, why in refused.items()
        )
        result.stop = {
            "batch_index": None,
            "failed_task_ids": [],
            "task_id": None,
            "kind": "answer-refused",
            "what": f"cannot take {named}",
            "refused_answers": [
                ["--human-task", f"{task_id}=skip"] for task_id in refused
            ],
            "not_run": [],
            "acceptable": False,
            "not_rerun": False,
            **({"answers": kept} if kept else {}),
        }
        self.set_stop_headline(result.stop)
        if not earlier:
            # No earlier run left a mirror to patch: this run's own.
            self._mirror_status(result)
            return
        try:
            # The phase-level `state` stays the earlier run's: this run
            # changed nothing a status reader would count.
            _status_file.update_status(self._ctx.phase_dir, {
                "progress": {"write_subagents": {
                    **earlier,
                    "in_flight": [],
                    "stop": copy.deepcopy(result.stop),
                }},
            })
        except Exception:  # noqa: BLE001 - observability must not fail a phase
            pass
