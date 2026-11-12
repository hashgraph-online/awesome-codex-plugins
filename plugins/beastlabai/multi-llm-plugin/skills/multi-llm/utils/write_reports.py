"""What a write phase leaves for people and tools to read (D3n, F7, F9, F10).

:class:`WriteReports` writes the run's records as the loop reaches them: the
``write_subagents`` mirror in ``.status.json`` after every batch and at every
ending (:meth:`WriteReports.mirror_status`) and its in-flight patch when a
dispatch starts (:meth:`WriteReports.publish_in_flight`), the scheduler's
``write_batch_report.json`` with the executor's own per-dispatch report beside
it (:meth:`WriteReports.write_report`), the phase's ``summary.md``
(:meth:`WriteReports.write_summary`) and its reference in the plan
(:meth:`WriteReports.insert_plan_reference`). Every writer is read-only over
the run's ``SchedulerResult`` and the scheduler's records: none decides what
the run does next. The mirror's writers never raise.

``WriteBatchScheduler`` composes it with the run's ``RunContext`` and the
records it reads (the containment sweep, the ``[ETA]`` counts, the runners the
run preflighted and the rung each dispatch ran on), and hands it the scheduler
methods it calls back, bound at each call
(docs/development/write-scheduler.md#where-the-schedulers-helpers-live).
"""

from __future__ import annotations

import copy
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from . import batch_prompt as _batch_prompt
from . import check_records as _check_records
from . import human_task_plan as _human_task_plan
from . import metrics as _metrics
from . import stop_answers as _stop_answers
from . import verification_lines as _verification_lines
from . import write_context as _write_context
from .retry_ladder import STATUS_OK
from .batch_reply import (
    WRITE_APPLIED,
    batch_check_could_not_run,
    row_batch_check_findings,
    row_outcome_label,
)
from .task_outcome import (
    BatchReport,
    ExecutorError,
    RunnerRejected,
    TaskOutcome,
)
from .failure_capture import _atomic_write_json
from .subagent_tasks import SHARED_ARTIFACT_WRITE_KINDS
from .task_ledger import (
    ACCEPTED_WITH_FINDINGS_MARK,
    COMPLETED_BY_HAND_LABEL,
    is_declined_reason,
)
from .text_clip import clip
from .write_phase_bridge import WRITE_TASK_FILENAME
from . import status_file as _status_file
from .manual_tasks import manual_close_note
from .plan_updater import insert_implementation_summary_reference

#: The scheduler's own report, beside the executor's per-dispatch one. A separate
#: file because it records the *loop*: batch order, the stopping batch, the skip
#: set, the override records and whether finalization ran.
WRITE_BATCH_REPORT_FILENAME = "write_batch_report.json"


class WriteReports:
    """The run's mirror, report, summary and plan reference.

    Built once per run by the scheduler. *sweep* and *eta* are the run's
    ``ContainmentSweep`` and ``EtaLines``; *runner_versions* and
    *dispatch_rungs* are the scheduler's own dictionaries, filled as it
    dispatches. The callables reach the scheduler (or a collaborator of it),
    looked up at each call.
    """

    def __init__(
        self,
        ctx: _write_context.RunContext,
        *,
        plan_file: Optional[str],
        summary_file_relative: Optional[str],
        write_target: Optional[str],
        invoker: str,
        host_max: Optional[int],
        user_commands: Dict[str, str],
        sweep: Any,
        eta: Any,
        runner_versions: Dict[str, str],
        dispatch_rungs: Dict[str, Optional[str]],
        resume_answered_ids: Callable[..., Any],
        resume_kept_rows: Callable[..., Any],
        ceiling_record: Callable[[], Any],
        check_findings_fate: Callable[..., Any],
        task_by_id: Callable[[str], Optional[Dict[str, Any]]],
        started_a_runner: Callable[..., bool],
        accounting: Callable[..., Any],
        manual_gates: Callable[[], Any],
    ) -> None:
        self._ctx = ctx
        self._plan_file = plan_file
        self._summary_file_relative = summary_file_relative
        self._write_target = write_target
        self._invoker = invoker
        self._host_max = host_max
        self._user_commands = user_commands
        self._sweep = sweep
        self._eta = eta
        self._runner_versions = runner_versions
        self._dispatch_rungs = dispatch_rungs
        self._resume_answered_ids = resume_answered_ids
        self._resume_kept_rows = resume_kept_rows
        self._ceiling_record = ceiling_record
        self._check_findings_fate = check_findings_fate
        self._task_by_id = task_by_id
        self._started_a_runner = started_a_runner
        self._accounting = accounting
        self._manual_gates = manual_gates

    def publish_in_flight(self) -> None:
        """Patch ``progress.write_subagents.in_flight`` alone. Best-effort.

        Reads back whatever :meth:`mirror_status` last wrote and patches only
        the one key this owns, so a dispatch starting mid-batch can never race
        that fuller write for the other fields — at worst this reads a
        `write_subagents` object one write stale, and the next real
        :meth:`mirror_status` call (or the next dispatch's own call here)
        corrects it.
        """
        try:
            existing = _status_file.read_status(self._ctx.phase_dir)
            mirror = dict(
                ((existing.get("progress") or {}).get("write_subagents")) or {}
            )
            in_flight = self._sweep.in_flight()
            mirror["in_flight"] = [
                {"task_id": task_id, "dispatched_at": started}
                for task_id, started in in_flight
            ]
            _status_file.update_status(self._ctx.phase_dir, {
                "progress": {"write_subagents": mirror}
            })
        except Exception:  # noqa: BLE001 - observability must not fail a phase
            pass

    def mirror_snapshot(self) -> Dict[str, Any]:
        """The ``write_subagents`` mirror as last written, for a patch."""
        try:
            existing = _status_file.read_status(self._ctx.phase_dir)
        except Exception:  # noqa: BLE001 - a missing file is an empty mirror
            return {}
        progress = existing.get("progress") if isinstance(existing, dict) else None
        mirror = (progress or {}).get("write_subagents") if isinstance(progress, dict) else None
        return dict(mirror) if isinstance(mirror, dict) else {}

    def applied_to_label(self) -> Optional[str]:
        """The phase's single write target relative to the repository root
        (the plan for apply-suggestions, the task list for
        apply-task-suggestions), or ``None`` for a phase without one."""
        if not self._write_target:
            return None
        try:
            # A label in prose and in the result line: `/` on every platform.
            return os.path.relpath(
                self._write_target, os.path.realpath(self._ctx.repo_root)).replace(os.sep, "/")
        except ValueError:  # pragma: no cover - another drive (Windows)
            return self._write_target

    def manual_close_note(
        self, deferred: Dict[str, str], plan: Optional[_human_task_plan.HumanTaskPlan] = None,
        stop: Optional[Mapping[str, Any]] = None,
    ) -> Optional[str]:
        """How to record the deferred manual tasks done, in the host's
        spelling (``user_commands["answers"]``), or ``None``.

        The how-to-close note rode implement's
        result only, never its summary.md, on either leg. The manual tasks
        only: a code task skipped with one is not answerable ``done`` and
        runs on that resume. Only the ones the user can do now
        (:meth:`StopAccount.manual_gates`), and the note says what waits on them. A run
        that stopped on a manual-task
        gate (*stop*) gives the gate's resume alone, the one command its stop
        names, and the note names the task(s) it records when the list above
        holds another manual task, which stays listed.
        """
        template = self._user_commands.get("answers")
        if self._ctx.kind != "implement" or not template or "{answers}" not in template:
            return None
        manual = sorted(
            task_id for task_id in deferred
            if (self._task_by_id(task_id) or {}).get("executor_role") == "human"
            or (self._task_by_id(task_id) or {}).get("is_human")
        )
        listed = list(manual)
        named: Optional[List[str]] = None
        if (stop or {}).get("kind") == "manual-gate":
            gating = [str(t) for t in (stop or {}).get("manual_task_ids") or []]
            manual = [task_id for task_id in gating if task_id in listed]
            waiting = len(set((stop or {}).get("held_task_ids") or []))
            if set(listed) - set(manual):
                named = list(manual)
        else:
            gates = self._manual_gates(plan) if plan is not None else None
            waiting = 0
            if gates is not None:
                manual = [task_id for task_id in manual if task_id in gates["closable"]]
                waiting = len({
                    code for task_id in manual
                    for code in gates["waiting"].get(task_id, ())
                })
        if not manual:
            return None

        return manual_close_note(template.replace(
            "{answers}", " ".join(f"--human-task {task_id}=done" for task_id in manual)),
            len(manual), waiting=waiting, named=named)

    def dispatched_sentence(self, result: Any) -> str:
        """summary.md's count of what this run dispatched: the tasks a
        runner was started for and the batches they ran in, then the ones
        it handled without a runner (live run 10 #7: the stop
        fixture's summary said "5 batch task(s) dispatched across 4
        batch(es)" beside "Organized into 3 execution batches" and "task
        4/4", counting T005, refused before dispatch, and its batch). An
        apply phase's task is its batch."""
        ran = [o for o in result.outcomes if self._started_a_runner(o, result.refusals)]

        def unit_ids(outcomes: Sequence[TaskOutcome]) -> str:
            return ", ".join(sorted({o.task_id for o in outcomes}, key=_metrics._id_key))

        if not ran:
            sentence = "Nothing was dispatched in this run."
        elif self._ctx.kind == "implement":
            batches = {
                int((self._task_by_id(o.task_id) or {}).get("batch_index", 0))
                for o in ran
            }
            sentence = (
                f"{len(ran)} task(s) dispatched across {len(batches)} batch(es), "
                f"in order; each was checked against its pre-batch snapshot "
                f"before the next was dispatched."
            )
        else:
            sentence = (
                f"{len(ran)} batch(es) dispatched, in order; each was checked "
                f"against its pre-batch snapshot before the next was dispatched."
            )
        refused = [
            o for o in result.outcomes
            if not o.skipped and o.task_id in result.refusals.before_dispatch
        ]
        not_rerun = [o for o in result.outcomes if not o.skipped and o.not_rerun]
        kept = [
            o for o in result.outcomes
            if not o.skipped and o.skipped_items
            and o.task_id not in result.refusals.before_dispatch
        ]
        if refused:
            sentence += f" Refused before dispatch (no runner started): {unit_ids(refused)}."
        if not_rerun:
            sentence += (
                f" Not run again (nothing in the repository changed since it "
                f"failed): {unit_ids(not_rerun)}."
            )
        if kept:
            sentence += f" Kept as it stood at your request: {unit_ids(kept)}."
        return sentence

    @staticmethod
    def answered_this_run(result: Any) -> Dict[str, Tuple[str, str]]:
        """``{task_id: (label, reason)}`` for the tasks this run's answers
        settled without a runner: accepted (``=done`` on a failed task or a
        check), completed by hand (``=done`` on a manual task), and skipped
        at the user's request with the tasks skipped with them — in the
        accounting line's words."""
        plan = result.human_plan
        out: Dict[str, Tuple[str, str]] = {}
        for task_id, reason in (plan.declined() or {}).items():
            seed = is_declined_reason(reason)
            out[str(task_id)] = (
                "skipped at your request" if seed else "skipped with a skipped task",
                str(reason),
            )
        for task_id, reason in (plan.accepted or {}).items():
            out[str(task_id)] = (_human_task_plan.answered_done_label(plan, task_id), str(reason))
        for task_id in plan.completed or ():
            out[str(task_id)] = (
                COMPLETED_BY_HAND_LABEL, f"answered --human-task {task_id}=done")
        return out

    def write_summary(self, result: Any) -> str:
        """The implementation summary, with the three conditional sections (D3n)."""
        plan_name = Path(self._plan_file).name if self._plan_file else "(plan)"
        lines = [
            f"# Implementation Summary: {plan_name}",
            "",
            f"*Generated: {datetime.now().isoformat()}*",
            "",
            f"**Plan**: {plan_name}",
            f"**Phase**: {self._ctx.phase}",
            f"**Invoker**: {self._invoker}",
        ]
        # F4: the template the instructions publish has always promised a
        # `Typecheck status` line, and on this leg nothing filled it. Only for
        # the code-editing kinds — a plan-text phase has no check to report.
        if self._ctx.kind in _batch_prompt.CODE_WRITE_KINDS:
            lines.append(f"**Verification**: {_verification_lines.verification_line(result)}")
        rows = result.report_rows()
        answered = self.answered_this_run(result)
        earlier = [
            row for row in rows
            if row.get("from_earlier_run") and str(row.get("task_id")) not in answered
        ]
        account = self._accounting(result)
        lines += [
            "",
            "## Summary",
            "",
            self.dispatched_sentence(result)
            + (
                f" The table below also carries {len(earlier)} task(s) "
                f"recorded by earlier run(s) of this phase (marked), which this "
                f"`--resume` did not dispatch again."
                if earlier else ""
            ),
            "",
            _stop_answers._accounting_line(account),
            "",
            "## Task Results",
            "",
            "| Task | Outcome | Files touched | Notes |",
            "|------|---------|---------------|-------|",
        ]
        folded: Set[str] = set()
        for row in rows:
            # `reason` first: it is `_classify`'s own diagnostic (why a
            # partial/clean-failure/no-op-with-bytes-moved outcome landed
            # where it did) and, unlike `summary`, is only ever set when there
            # is something worth explaining beyond the runner's own claim — a
            # plain applied batch has none, so `summary` still carries the
            # row. Before this a self-contradicting `no-op` claim printed its
            # own rosy summary ("T006 already implemented: …") with no sign
            # the bytes disagreed (N2, 2026-09-16).
            task_cell = f"{row['task_id']}" + (
                " (earlier run)" if row.get("from_earlier_run") else ""
            )
            outcome_cell = row_outcome_label(row) or row.get("status")
            if row.get("status") == STATUS_OK and row_batch_check_findings(row):
                # Never a plain success.
                outcome_cell = f"{outcome_cell}, " + (
                    "its check could not run"
                    if batch_check_could_not_run(row_batch_check_findings(row))
                    else "its check fails"
                )
            notes = (row.get("reason") or row.get("summary") or "").replace("|", "/")
            answer = answered.get(str(row.get("task_id")))
            if answer is not None and row.get("from_earlier_run"):
                # A task you
                # answered on this run reads as your answer, its earlier
                # run's outcome named as what the answer was about; it read
                # "(earlier run) policy-violation" here beside "## Skipped
                # at your request" below.
                label, why = answer
                folded.add(str(row["task_id"]))
                lines.append(
                    f"| {row['task_id']} | {label} | — | "
                    f"{clip(why.replace('|', '/'), 120)} (earlier run: "
                    f"{outcome_cell}: {clip(notes, 160)}) |"
                )
                continue
            lines.append(
                f"| {task_cell} | {outcome_cell} | "
                f"{', '.join(row.get('files_touched') or []) or '—'} | "
                f"{clip(notes, 160)} |"
            )
        for task_id, reason in sorted(result.human_plan.accepted.items()):
            if task_id in folded:
                continue
            label = _human_task_plan.answered_done_label(result.human_plan, task_id)
            lines.append(f"| {task_id} | {label} | — | {clip(reason.replace('|', '/'), 160)} |")
        for task_id in sorted(result.human_plan.completed):
            if task_id in folded:
                continue
            lines.append(f"| {task_id} | completed by hand | — | answered --human-task {task_id}=done |")
        for task_id, reason in sorted(result.not_run.items()):
            lines.append(f"| {task_id} | not run | — | {clip(reason.replace('|', '/'), 160)} |")
        findings_by_task = result.check_findings()
        if findings_by_task:
            # Racing re-run 4: T007's two html-validate problems
            # read VERIFIED here and lived only in the runner's notes. They
            # are listed whole, for the reader and for review-code, which is
            # given this file and state.json's record of them.
            fate = "; ".join(self._check_findings_fate(
                result, findings_by_task,
                # A check-findings stop is the end of a run whose other
                # tasks went on; a failed task's stop is not.
                stopped=bool(result.stop)
                and (result.stop or {}).get("kind") != "check-findings",
                see_below=True,
            ))
            lines += [
                "", "## Check Findings", "",
                "These checks ran and changed no file, but reported problems. "
                + fate[:1].upper() + fate[1:] + ". "
                + "Review-code is told about them, and apply-code-fixes "
                "applies the fixes review-code validates.", "",
            ]
            # A code task whose own check reported again only
            # what you accepted for a check is named under that check.
            again: Dict[str, List[str]] = {}
            for task_id, matched in result.batch_check_accepted().items():
                for check_id in matched:
                    again.setdefault(check_id, []).append(task_id)
            notes = result.batch_check_notes()
            # A code task whose own check reported only what a
            # check task reported is named under that check too.
            repeated: Dict[str, List[str]] = {}
            repeated_found: Dict[Tuple[str, str], List[str]] = {}
            for task_id, matched in result.batch_check_repeats().items():
                for check_id, found in matched.items():
                    repeated.setdefault(check_id, []).append(task_id)
                    repeated_found[(task_id, check_id)] = [str(item) for item in found]
            for task_id, findings in findings_by_task.items():
                lines.append(f"### {task_id}")
                lines.append("")
                lines += [f"- {finding}" for finding in findings]
                lines.append("")
                for rerun in again.get(task_id, []):
                    lines += [
                        f"{rerun} ran this check again, and its own report says "
                        f"only what you accepted: not counted as {rerun}'s own "
                        f"failure.{_check_records._note_sentence(notes.get(rerun))}", "",
                    ]
                for rerun in repeated.get(task_id, []):
                    # The record
                    # is what the task's run saw. A check that ran again and
                    # no longer lists what it repeated has the repeat quoted,
                    # never set under findings the task never reported.
                    found = repeated_found.get((rerun, task_id)) or []
                    left, _same = _check_records.split_repeated_findings(found, {task_id: findings})
                    if found and left:
                        lines += [
                            f"{rerun} ran this check too, and its own report "
                            f"said only what {task_id} reported then: "
                            f"{_check_records.quoted_findings(found, 300)} — not what "
                            f"{task_id} reports now, and not counted as "
                            f"{rerun}'s own failure."
                            f"{_check_records._note_sentence(notes.get(rerun))}", "",
                        ]
                        continue
                    lines += [
                        f"{rerun} ran this check too, and its own report says "
                        f"only what {task_id} reported: it repeats {task_id}'s "
                        f"finding, not counted as {rerun}'s own failure."
                        f"{_check_records._note_sentence(notes.get(rerun))}", "",
                    ]
            lines.pop()
        lines += _check_records.batch_check_section(rows, heading=not findings_by_task)
        touched: List[str] = []
        for row in rows:
            for path in row.get("files_touched") or []:
                if path not in touched:
                    touched.append(path)
        lines += ["", "## Files Modified", ""]
        lines += [f"- `{path}`" for path in touched] or ["- (none)"]

        plan = result.human_plan
        deferred = plan.deferred()
        declined = plan.declined()
        if deferred:
            lines += ["", "## Manual Tasks (Deferred)", ""]
            lines += ["| Task | Reason |", "|------|--------|"]
            for task_id, reason in sorted(deferred.items()):
                lines.append(f"| {task_id} | {reason} |")
            note = self.manual_close_note(deferred, plan, stop=result.stop)
            if note:
                lines += ["", note]
        if declined:
            # The user's own decision, not work left for them: a pause-and-ask
            # "Skip", a failed task answered `--human-task <id>=skip`, and the
            # tasks skipped with them. Listed apart so the summary and the
            # workflow's `[MANUAL_TASK]` lines (which leave these out) agree.
            lines += ["", "## Skipped at your request", ""]
            lines += ["| Task | Reason |", "|------|--------|"]
            for task_id, reason in sorted(declined.items()):
                lines.append(f"| {task_id} | {reason} |")
        if plan.overrides:
            lines += [
                "", "## Dependency Override Warnings", "",
                "The following tasks ran with skipped human-task dependencies "
                "(skip-continue strategy):", "",
                "| Task | Overridden Dependencies | Risk |",
                "|------|------------------------|------|",
            ]
            for task_id, deps in sorted(plan.overrides.items()):
                lines.append(
                    f"| {task_id} | {', '.join(deps)} | ran against an unmet "
                    f"manual precondition |"
                )
        blocked = result.blocked_by_check
        if blocked:
            # The tasks a check with findings kept from
            # running, apart from a stop's own not-run list.
            lines += [
                "", "## Not Run: Upstream Check Reported Problems", "",
                "These tasks depend on a check that reported problems (listed "
                "under Check Findings), so they were not run; they stay "
                "`pending`. Fix what the check reported and resume this phase "
                "(the check runs again, and once it passes they run), or "
                "accept the check's findings with `--human-task <check id>=done` "
                "on the resume (they run, told that you accepted the findings, "
                "which stay listed for review-code), or leave the check and them "
                "undone with "
                "`--human-task <check id>=skip`.", "",
                "| Task | Waits for check |", "|------|-----------------|",
            ]
            for task_id, check_id in sorted(blocked.items()):
                lines.append(f"| {task_id} | {check_id} |")
        if (result.stop or {}).get("kind") == "manual-gate":
            # Nothing ran, and
            # the summary says why rather than reading as a finished run.
            lines += [
                "", "## Not Finished: Waiting On A Manual Task", "",
                str(result.stop.get("headline") or ""),
            ]
        if result.stopped_at_batch is not None:
            stop = result.stop or {}
            lines += ["", "## Cancelled", ""]
            if stop.get("headline"):
                lines.append(stop["headline"])
            else:
                lines.append(
                    f"The write loop stopped at batch {result.stopped_at_batch}."
                )
            lines.append("")
            stopped = sorted(t for t in result.not_run if t not in blocked)
            if stopped:
                lines.append(
                    "Not run (the stop came before they were dispatched; they "
                    "stay `pending` and a `--resume` dispatches them after the "
                    "failed task passes or is accepted):"
                )
                lines.append("")
                lines += [f"- {task_id}" for task_id in stopped]
            elif blocked:
                lines.append(
                    "Every other task of the decomposition had run, or waits "
                    "for a check (above)."
                )
            else:
                lines.append("Every other task of the decomposition had run.")
            lines += [
                "",
                f"Snapshots are intact under "
                f"`{os.path.join(self._ctx.safety_dir, 'pre_batch')}/`.",
            ]
        text = "\n".join(lines) + "\n"
        target = Path(self._ctx.summary_file)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return str(target)

    def insert_plan_reference(self, summary_file: Optional[str]) -> None:
        """``insert_implementation_summary_reference`` on the plan (D3n)."""
        if not (self._plan_file and summary_file):
            return
        # `/`-spelled like `get_relative_output_path`'s: a link in the plan.
        relative = self._summary_file_relative or os.path.relpath(
            summary_file, str(Path(self._plan_file).parent)
        ).replace(os.sep, "/")
        try:
            path = Path(self._plan_file)
            content = path.read_text(encoding="utf-8")
            path.write_text(
                insert_implementation_summary_reference(content, relative),
                encoding="utf-8",
            )
        except OSError as exc:  # pragma: no cover
            self._ctx.log(f"[write-subagents] warning: plan reference failed: {exc}")

    def write_report(self, result: Any) -> str:
        path = os.path.join(self._ctx.phase_dir, WRITE_BATCH_REPORT_FILENAME)
        # D3l: a scheduler artifact is written under the same rules as any other
        # executor write — same-directory temp, 0600, ``os.replace`` — so a run
        # killed mid-write leaves either the old report or the new one, never a
        # truncated JSON for `status`/CI to parse, and never a umask-wide mode.
        _atomic_write_json(path, result.to_dict())
        # The executor's own per-dispatch report, so `--status` and the D3k rung
        # accounting look identical on both halves of the executor.
        effective, configured, provider_limits = self._ceiling_record()
        report = BatchReport(
            phase=self._ctx.phase, kind=self._ctx.kind, phase_dir=self._ctx.phase_dir,
            # N9: the read path fills this from the `task_file` argument
            # `run_task_file` was handed; the write path never takes one —
            # `WriteBatchScheduler` is constructed from an already-materialized
            # task LIST — but `write_task_file_for_phase` always persists that
            # same list at exactly this path (every write orchestrator passes
            # it the identical `phase_dir`), so it is not a guess.
            task_file=os.path.join(self._ctx.phase_dir, WRITE_TASK_FILENAME),
            outcomes=list(result.outcomes), invoker=self._invoker,
            # F12: filled the same way the read path fills it
            # (`_preflight_batch_runners`) — every distinct runner this run
            # actually preflighted, with the version it reported.
            runner_versions=dict(self._runner_versions),
            ceilings={"effective": effective,
                      "driver_max_concurrent_write_subagents": configured,
                      "provider_max_concurrent": provider_limits,
                      "host_max_concurrent_subagents": self._host_max,
                      "shared_artifact_phase":
                          self._ctx.kind in SHARED_ARTIFACT_WRITE_KINDS},
        )
        report.write()
        return path

    def mirror_status(
        self, result: Any, *,
        finished_in_batch: Sequence[TaskOutcome] = ()
    ) -> None:
        """Per-task write progress in ``.status.json`` (D3g/D4a). Best-effort.

        ``finished_in_batch`` is the current batch's finished tasks, which are
        not on ``result.outcomes`` until the batch returns; passing them is
        what makes the counts advance *during* a batch instead of at its
        boundary. The rows are appended, never merged, so a task cannot be
        counted twice. (Named to leave ``in_flight`` — the JSON key below —
        for tasks that are the opposite: dispatched and NOT yet finished.)
        """
        try:
            outcomes = list(result.outcomes) + list(finished_in_batch)
            if result.finalized:
                phase_state = "complete"
            elif result.stopped_at_batch is not None or result.exit_code:
                phase_state = "subagents_failed"
            else:
                phase_state = "running"
            # F4: `progress.step` is set before a dispatch and never replaced, so
            # a write phase whose last `report_progress` came from the judging
            # dispatch printed `dispatching human-decision judging` for the whole
            # 288 s of batch application AND in the terminal payload, beside
            # `run.state: done`. The mirror already writes
            # `progress` on every advance, so it is the one place that can move
            # the step with the work; it is written key-by-key, so every sibling
            # counter survives.
            step = {
                "complete": "complete",
                "subagents_failed": "stopped",
            }.get(phase_state, "applying")
            # F9: the mirror's `total`/`ok` count BATCHES, not the suggestions
            # or fixes inside them — a 15-batch, 29-suggestion apply-suggestions
            # run mirrored (and the model then reported) "15/15 ok, applied 15",
            # 14 suggestions short. `expected_ids` is every write task's own
            # declared item list (`write_phase_bridge`: suggestion/fix member
            # ids for the three apply kinds, the task id itself for implement),
            # so both counts are already on hand with no new bookkeeping.
            #
            # F9: both denominators also used to include the human
            # task(s) `human_task_strategy` skips — they never dispatch, so a
            # clean 14-task run with one deferred manual task mirrored
            # `13/14 batches ok`, a run that did everything it could reading as
            # one short. `result.human_plan.skipped` is resolved before this is
            # ever called (`_run`'s step 1), so it is on hand the same way.
            #
            # And over the same tasks
            # the `[ETA]` line counts (`EtaLines.task_ids`): not a manual task,
            # nor one a check with findings holds back — the line names that
            # one as not run, with the check. Counted over the materialized
            # tasks: an answered task an earlier run recorded
            # (`answered_done_on_record`) is in `accepted` without being one
            # of them.
            counted_ids = self._eta.task_ids(result)
            counted = set(counted_ids)
            expected_ids_by_task = {
                str(task.get("task_id", "")):
                    [str(i) for i in (task.get("expected_ids") or [])]
                for task in self._ctx.tasks
                if str(task.get("task_id", "")) in counted
            }
            total = len(counted_ids)
            # The `ok` of `<ok>/<total> batches ok`, over the
            # same tasks, so a task an implement run kept from an earlier one
            # (never dispatched, never in `total`) is not counted as one of
            # its batches; the progress line names it as kept instead.
            ok_count = sum(1 for o in outcomes if o.ok and o.task_id in counted)
            items_total = sum(len(ids) for ids in expected_ids_by_task.values())
            items_applied = sum(
                len([
                    # An item its batch declined, or one
                    # skipped at the user's request, was not applied.
                    item for item in expected_ids_by_task.get(o.task_id, [])
                    if item not in o.declined and item not in o.skipped_items
                ])
                for o in outcomes if o.write_outcome == WRITE_APPLIED
            )
            declined_rows = [
                {"task_id": o.task_id, "id": item, "reason": reason}
                for o in outcomes if o.ok
                for item, reason in o.declined.items()
            ]
            skipped_rows = [
                {"task_id": o.task_id, "id": item, "reason": reason}
                for o in outcomes if o.ok
                for item, reason in o.skipped_items.items()
            ]
            # F10: a dispatch that has started and not yet been classified —
            # `_dispatch_started`, added in `_begin_sweep` and removed in
            # `_undeclared_writes`. Read under the same lock those methods take,
            # since a disjoint group dispatches on threads.
            in_flight = self._sweep.in_flight()
            kept_rows = self._resume_kept_rows(result, outcomes)
            kept_ids = (
                [str(row.get("task_id")) for row in kept_rows]
                + self._resume_answered_ids(result, outcomes, kept_rows)
            ) or [o.task_id for o in outcomes if o.skipped]
            _status_file.update_status(self._ctx.phase_dir, {
                # The read phases record a phase-level `state` beside the run
                # record; without one here `status` printed `phase state: (none)`
                # for every finished write phase.
                "state": phase_state,
                "phase": self._ctx.phase,
                "progress": {
                    "step": step,
                    "write_subagents": {
                        "kind": self._ctx.kind,
                        "invoker": self._invoker,
                        # F9: excludes tasks `human_task_strategy` skipped —
                        # they will never dispatch, so counting them here read
                        # a clean run as short by exactly its deferred tasks.
                        "total": total,
                        "ok": ok_count,
                        # F10: the tasks dispatched and NOT yet finished, so
                        # an 11-minute single-task batch never reads as a
                        # stall. (The finished count is the `tasks` rows.)
                        "in_flight": [
                            {"task_id": task_id, "dispatched_at": started}
                            for task_id, started in in_flight
                        ],
                        "items_total": items_total,
                        "items_applied": items_applied,
                        # The one
                        # file a single-target phase edits, repo-relative,
                        # so `status` says where the items were applied
                        # ("applied to" was the host's guess).
                        **({"applied_to": self.applied_to_label()}
                           if self.applied_to_label() else {}),
                        # What finished batches did not apply
                        # on purpose, and why — `status` names each one.
                        **({"declined_items": declined_rows}
                           if declined_rows else {}),
                        **({"skipped_items": skipped_rows}
                           if skipped_rows else {}),
                        # F7: the run's own resolved runner, so `status` polled
                        # outside the session that launched it names what the
                        # batches actually dispatched to — `render_runner_text`
                        # prefers this over a fresh resolution the same way it
                        # already prefers the read path's `subagents` mirror.
                        "runner_versions": dict(self._runner_versions),
                        "batches_dispatched": list(result.batches_dispatched),
                        "stopped_at_batch": result.stopped_at_batch,
                        # F4: written only once the command really ran, so the
                        # key's presence means "a check happened" rather than
                        # "this version knows about checks". The mirror is
                        # rewritten on every advance and verification is the
                        # last thing a run does, so an absent key on a finished
                        # run is the "not configured" notice in the log.
                        **({"verification": result.verification}
                           if result.verification else {}),
                        "human_task_strategy": result.human_plan.strategy,
                        "skipped_task_ids": sorted(result.human_plan.skipped),
                        # Which of those the user skipped
                        # (`--human-task <id>=skip`, a pause-and-ask "Skip")
                        # and which went with them, so `status` no longer
                        # lists them as "deferred manual" — work owed by hand
                        # — beside a summary that says "skipped at your
                        # request" (Codex stop-path accept 02).
                        **_human_task_plan._declined_split(result.human_plan),
                        # Which of the rest wait on a deferred
                        # manual task, named apart from it on `status`.
                        **_human_task_plan._deferred_split(result.human_plan),
                        # One row per finished task. The id lists its rows
                        # already carry (the tasks not `ok`, the checks with
                        # findings, the code batches whose own check failed)
                        # are read from them (`task_ledger.mirror_ids`), never
                        # written beside them.
                        "tasks": [
                            {
                                "task_id": o.task_id,
                                "batch_index": self.batch_index_of(o.task_id),
                                "status": o.status,
                                "write_outcome": o.write_outcome,
                                **({"verification_only": True,
                                    "outcome_label": o.outcome_label}
                                   if o.verification_only else {}),
                                # Racing re-run 4: what a check found, only on
                                # the row of a check that found something.
                                **({"check_findings": list(o.check_findings)}
                                   if o.ok and o.check_findings else {}),
                                # A code batch whose own check
                                # failed after its edits.
                                **({"batch_check_findings": list(o.batch_check)}
                                   if o.ok and o.batch_check else {}),
                                "files_touched": list(o.files_touched),
                                # Moved, with no rollback point.
                                **({"unrestorable": list(o.unrestorable)}
                                   if o.unrestorable else {}),
                                # The rung, only when there was one.
                                **({"sandbox_rung": self._dispatch_rungs[o.task_id]}
                                   if self._dispatch_rungs.get(o.task_id) else {}),
                            }
                            for o in outcomes
                        ],
                        # Which of
                        # the failed tasks a runner ran in this run — not one
                        # refused before dispatch, nor a failed check not run
                        # again — so `status` says "nothing crashed" only of
                        # a stop no runner failed. Always written: an older
                        # mirror without it is read by `failed_task_ids`.
                        "runner_failed_task_ids": [
                            o.task_id for o in outcomes
                            if not o.ok and not o.skipped and not o.not_rerun
                            and o.task_id not in result.refusals.before_dispatch
                        ],
                        # The tasks this run kept
                        # from an earlier one instead of dispatching them, so
                        # `status` does not read them as this run's batches.
                        # Every task the
                        # resume kept, as its `resume: kept` line names
                        # them, not only the ones it materialized again.
                        # The line's whole set — the tasks an
                        # earlier run finished and this one did not
                        # dispatch, then the ones kept on the user's
                        # `--human-task <id>=done` (an accepted check or
                        # failed task, a manual task completed by hand).
                        **({"kept_task_ids": kept_ids} if kept_ids else {}),
                        # Which of them the user completed by hand, so
                        # `status` names them in the line's words.
                        **({"completed_by_hand_task_ids": sorted(
                            set(result.human_plan.completed) & set(kept_ids)
                        )} if set(result.human_plan.completed) & set(kept_ids)
                           else {}),
                        # A task whose own check repeated only
                        # the findings the user accepted, by the checks.
                        **({"batch_check_accepted": {
                            o.task_id: sorted(o.batch_check_accepted)
                            for o in outcomes if o.ok and o.batch_check_accepted
                        }} if any(o.ok and o.batch_check_accepted for o in outcomes)
                           else {}),
                        # One whose own check repeated only a
                        # check task's finding, by the checks.
                        **({"batch_check_repeats": {
                            o.task_id: sorted(o.batch_check_repeats)
                            for o in outcomes if o.ok and o.batch_check_repeats
                        }} if any(o.ok and o.batch_check_repeats for o in outcomes)
                           else {}),
                        # Nothing ran the repository's tests.
                        **({"unverified": result.unverified}
                           if result.unverified else {}),
                        # Racing re-run 3: the tasks a stop left
                        # undispatched, and the failed tasks the user accepted,
                        # so `status` and a terminal poll account for every
                        # task rather than only the dispatched ones.
                        "not_run_task_ids": sorted(result.not_run),
                        # Which of them wait for a check that
                        # reported problems, and for which one.
                        **({"blocked_by_check": dict(sorted(result.blocked_by_check.items()))}
                           if result.blocked_by_check else {}),
                        "accepted_task_ids": sorted(result.human_plan.accepted),
                        # Which of them are checks accepted with
                        # their findings, so `status` does not read them
                        # "accepted after failing" (Codex accept 02).
                        **({"accepted_with_findings_task_ids": sorted(
                            task_id for task_id, reason
                            in result.human_plan.accepted.items()
                            if ACCEPTED_WITH_FINDINGS_MARK in str(reason or "")
                        )} if any(
                            ACCEPTED_WITH_FINDINGS_MARK in str(reason or "")
                            for reason in result.human_plan.accepted.values()
                        ) else {}),
                        **({"stop": copy.deepcopy(result.stop)}
                           if result.stop else {}),
                    }
                }
            })
        except Exception:  # noqa: BLE001 - observability must not fail a phase
            pass

    def batch_index_of(self, task_id: str) -> Optional[int]:
        for task in self._ctx.tasks:
            if str(task.get("task_id", "")) == task_id:
                return int(task.get("batch_index", 0))
        return None

    def record_refusal(self, exc: ExecutorError, batch_index: int) -> None:
        """I11: name the refusal in ``.status.json``, with nothing in flight.

        Fixes I11:
        after a batch-0 refusal the status file still listed ``apply-batch-0``
        as "in flight (since 0m 9s)". The in-flight entry is closed by
        ``_dispatch_one``'s ``finally`` before the mirror above is written;
        this records what ended the run in the read path's own close-out
        words (``review_orchestrator_base._print_executor_refusal``):
        ``runner_rejected`` for a refused runner, ``executor_refused`` for any
        other pre-dispatch refusal — both terminal to ``status``, which renders
        the repair off ``reason_code``. Best-effort, like every mirror write.
        """
        rejected = isinstance(exc, RunnerRejected)
        try:
            self._sweep.clear_in_flight()
            _status_file.update_status(self._ctx.phase_dir, {
                "state": "runner_rejected" if rejected else "executor_refused",
                "reason_code": (
                    (getattr(exc, "reason_code", "") or "") if rejected else ""
                ) or type(exc).__name__,
                "runner": (getattr(exc, "spec", "") or "") if rejected else "",
                "runner_key": (getattr(exc, "key", "") or "") if rejected else "",
                "refused_batch": batch_index,
                "progress": {"write_subagents": {
                    **self.mirror_snapshot(),
                    "in_flight": [],
                }},
            })
        except Exception:  # noqa: BLE001 - observability must not fail a phase
            pass
