"""What a write phase's ``--resume`` finds on disk from its earlier runs (D2g, D3i).

:class:`ResumeEvidence` reads what an earlier run of the phase left: whether a
task's result counts as done (:meth:`ResumeEvidence.done_evidence`,
:meth:`ResumeEvidence.result_counts_as_done`), found under its own name or, for a
renumbered apply batch, beside it (:meth:`ResumeEvidence.sibling_results`,
:meth:`ResumeEvidence.retire_foreign_result`); the inputs binding each result is
compared with (:meth:`ResumeEvidence.task_fingerprint`,
:meth:`ResumeEvidence.record_fingerprint`); the earlier report's rows of this
review cycle (:meth:`ResumeEvidence.earlier_report_rows`,
:meth:`ResumeEvidence.review_completed_at`); the ``--human-task <batch>=skip``
answers it can keep (:meth:`ResumeEvidence.check_partial_skips`,
:meth:`ResumeEvidence.partial_skip_evidence`), and the ``resume: kept`` line and
the mirror's kept tasks (:meth:`ResumeEvidence.report_resume_tally`,
:meth:`ResumeEvidence.resume_kept_rows`, :meth:`ResumeEvidence.resume_answered_ids`).
It never writes ``state.json``: its one file of its own is the inputs binding,
``WRITE_FINGERPRINT_FILENAME``, beside the results.

``WriteBatchScheduler`` composes it with the run's ``RunContext``
(docs/development/write-scheduler.md#where-the-schedulers-helpers-live). A batch
kept at the user's request is read here (:meth:`ResumeEvidence.kept_outcome`)
and recorded by the scheduler's ``_keep_at_request``, a step of the dispatch.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from . import check_records as _check_records
from . import human_task_plan as _human_task_plan
from . import write_context as _write_context
from . import write_outcomes as _write_outcomes
from . import write_reports as _write_reports
from .held_folder import write_in_plan_dir
from .batch_ledger import read_verdict_checks
from .state_manager import _parse_completion_time, predates_review, stamp_or_mtime
from .task_result import (
    OUTPUT_NAME_PATTERN_BY_KIND,
    resolve_output_target,
    validate_result,
)
from .retry_ladder import STATUS_OK
from .batch_reply import (
    WRITE_APPLIED,
    WRITE_CLEAN_FAILURE,
    WRITE_NO_OP,
    row_declined,
)
from .task_outcome import (
    ResultRejected,
    TaskOutcome,
)
from .runner_selection import profile_for_kind
from .subagent_tasks import declared_file_set, write_output_name
from .task_ledger import KEPT_WITH_FINDINGS_LABEL
from .text_clip import with_closing_mark
from .write_safety import TaskSnapshot, file_sha256
from .code_fix_batcher import without_protected_clause


#: The D2g inputs binding for the results already on disk, kept beside them.
#: A **leading dot** on purpose: reaggregation globs ``{phase_dir}/*.json`` and
#: treats every file it matches as a per-model result list, and ``glob`` skips
#: leading-dot names — the same reason ``.status.json`` is invisible to it.
WRITE_FINGERPRINT_FILENAME = ".write_task_inputs.json"

#: The review each apply kind applies — the first entry of
#: ``check_workflow_prerequisites.PHASE_PREREQUISITES`` for that phase, which
#: is the prerequisite ``_apply_batches_predate_review`` dates a batch
#: against. Spelled here so the scheduler does not import the prerequisite
#: script (a top-level module) from inside ``utils/``; a test holds the two in
#: agreement. ``implement`` has no entry: its ``T###`` ids are the plan's.
REVIEW_PHASE_BY_WRITE_KIND: Dict[str, str] = {
    "apply_suggestions": "review-plan",
    "apply_task_suggestions": "review-tasks",
    "apply_code_fixes": "code-review",
}

#: The index token of a positional write result's filename — bare
#: (``apply_batch_1.json``) or retired beside the slot by
#: ``retire_foreign_result`` (``apply_batch_1.items-<sha8>[-N].json``).
_RESULT_TOKEN = re.compile(r"^(\d+)(?:\.items-[0-9a-f]{8}(?:-\d+)?)?$")


def review_completed_at(recorded: Any, write_kind: Any) -> Optional[datetime]:
    """When the review *write_kind* applies last completed, or None.

    The cutoff between review cycles (:func:`state_manager.predates_review`),
    read from a ``state.json`` dict (*recorded*): the review is
    :data:`REVIEW_PHASE_BY_WRITE_KIND`'s entry. None for ``implement`` (its
    ``T###`` ids are the plan's, not a cycle's), for anything that is not a
    state dict, and for a review with no parseable completion.
    """
    review = REVIEW_PHASE_BY_WRITE_KIND.get(write_kind or "")
    if review is None or not isinstance(recorded, dict):
        return None
    completed = recorded.get("phases_completed")
    if not isinstance(completed, dict):
        return None
    return _parse_completion_time(completed.get(review))


class ResumeEvidence:
    """What an earlier run of the phase left, as this run's resume reads it.

    Built once per run by the scheduler. *resume* and *partial_skips* are the
    scheduler's (``--resume``/``--fresh`` and the ``--human-task <batch>=skip``
    answers); *eta* is the run's ``EtaLines``, whose dispatch scope a kept task
    is never in; *commit_guard* reaches ``CommitGuardLeg.guard``, looked up at
    each call.
    """

    def __init__(
        self,
        ctx: _write_context.RunContext,
        *,
        resume: bool,
        partial_skips: Sequence[str],
        eta: Any,
        commit_guard: Callable[[], Optional[Dict[str, Any]]],
    ) -> None:
        self._ctx = ctx
        self._resuming = resume
        self._partial_skips = partial_skips
        self._eta = eta
        self._commit_guard = commit_guard
        #: The batches answered ``--human-task <id>=skip`` that
        #: :meth:`partial_skip_evidence` found can be kept as they stand
        #: (``task id -> its result's path, data and verdict``), which the
        #: scheduler's ``_keep_at_request`` takes.
        self.kept_at_request: Dict[str, Dict[str, Any]] = {}
        #: The answers :meth:`check_partial_skips` refused, with why (fix
        #: round 19: recorded as a stop, ``StopAccount.record_answer_refusal``).
        self.refused_skips: Dict[str, str] = {}

    def report_resume_tally(self, result: Any) -> None:
        """One line on a run that kept earlier batches: what it kept and what
        it dispatched.

        Only this loop knows which batches an earlier run finished (their
        result file, ``done_evidence``); the apply base's own ``[resume]``
        line is printed before any batch exists, and on this leg it used to
        say "0 already processed, 12 remaining" while the run then kept
        batch 0 as an earlier run's (OpenCode racing run 4).
        """
        # Every apply run resumes unless `--fresh`, so a first run (nothing
        # kept) says nothing here; its batch lines already say what ran.
        if not self._resuming or self._ctx.dry_run:
            return
        kept = self.resume_kept_rows(result, result.outcomes)
        # Fix round 16 (Codex stop-path accept 02): a task answered
        # `--human-task <id>=done` is kept too, and the line says how — the
        # accepted check T002 was missing from "kept 3 … T001, T003, T004".
        answered_kept = [
            f"{task_id} ({_human_task_plan.answered_done_label(result.human_plan, task_id)})"
            for task_id in self.resume_answered_ids(result, result.outcomes, kept)
        ]
        if not kept and not answered_kept:
            return
        # Dispatched: the tasks a runner was started for. A task refused
        # before dispatch and a check not run again started none (fix round
        # 14: the stop fixture's 01b counted the refused T005 as dispatched).
        refused = [
            o for o in result.outcomes
            if not o.skipped and o.task_id in result.refusals.before_dispatch
        ]
        not_rerun = [o for o in result.outcomes if not o.skipped and o.not_rerun]
        dispatched = [
            o for o in result.outcomes
            if not o.skipped and o not in refused and o not in not_rerun
        ]
        items = {
            str(task.get("task_id", "")): len(task.get("expected_ids") or [])
            for task in self._ctx.tasks
        }

        def counted(ids: Sequence[str], rows: Sequence[Dict[str, Any]] = ()) -> str:
            # An implement task is one item; the count would only repeat it.
            if self._ctx.kind == "implement":
                return ""
            by_row = {
                str(row.get("task_id")): len(row.get("expected_ids") or [])
                for row in rows
            }
            total = sum(by_row.get(i, items.get(i, 0)) for i in ids)
            return f" ({total} item(s))"

        def named(ids: Sequence[str]) -> str:
            return ", ".join(ids[:5]) + (", …" if len(ids) > 5 else "")

        kept_ids = [str(row.get("task_id")) for row in kept]
        dispatched_ids = [o.task_id for o in dispatched]
        # Fix round 20 (live run 8 #6): a check kept with its findings
        # standing says so, as an accepted one does — 01b read "T001, T002,
        # T003, T004" as if T002 had passed.
        with_findings = (
            {o.task_id for o in result.outcomes if o.skipped and o.check_findings}
            | set(_check_records.rerunnable_checks(self._ctx.state))
        ) if self._ctx.kind == "implement" else set()
        plain_ids = [i for i in kept_ids if i not in with_findings]
        kept_named = ", ".join(
            part for part in (
                named(plain_ids) + counted(plain_ids, kept) if plain_ids else "",
                ", ".join(
                    f"{i} ({KEPT_WITH_FINDINGS_LABEL})"
                    for i in kept_ids if i in with_findings
                ),
                ", ".join(answered_kept),
            ) if part
        )
        self._ctx.log(
            f"[write-subagents] resume: kept {len(kept_ids) + len(answered_kept)} "
            f"task(s) an earlier run finished — {kept_named}; "
            f"dispatched {len(dispatched_ids)}{counted(dispatched_ids)}"
            + (
                f"; refused before dispatch {len(refused)} "
                f"({named([o.task_id for o in refused])})" if refused else ""
            )
            + (
                f"; not run again {len(not_rerun)} "
                f"({named([o.task_id for o in not_rerun])})" if not_rerun else ""
            )
            + (f"; not reached {len(result.not_run)}" if result.not_run else "")
        )

    def resume_kept_rows(
        self, result: Any, outcomes: Sequence[TaskOutcome],
    ) -> List[Dict[str, Any]]:
        """The report rows of the tasks a resume kept: every task an earlier
        run finished that this run did not dispatch — a resume skip, and
        (fix round 14) a task the resume never materialized because
        ``state.json`` records it completed: implement materializes only the
        unfinished tasks, so its skips were empty and OpenCode racing 06b,
        which kept 14, printed no line at all. Read off the phase's report
        rows (this run's and the earlier runs'), the account the stop's
        "Done and kept" line is built from; a task answered ``--human-task
        <id>=done`` is its own bucket. ``[]`` on a run that is not a resume.

        The ``resume: kept`` line and the write mirror's ``kept_task_ids``
        (``status``'s ``(<n> kept from an earlier run: …)``) both read it,
        then :meth:`resume_answered_ids`, so the two name the same tasks:
        fix round 22 (live run 9 #5) — Codex 01b's line kept four, its
        ``status`` said "1 kept". *outcomes* is
        what finished so far (the mirror passes a batch's finished tasks
        before they reach ``result``); a task the run's dispatch walk will
        dispatch is never kept, though an earlier run finished it (a check
        run again once the files changed).
        """
        if not self._resuming or self._ctx.dry_run:
            return []
        this_run = {o.task_id for o in outcomes if not o.skipped}
        if self._eta.scope is not None:
            this_run |= set(self._eta.scope)
        answered = set(result.human_plan.accepted) | set(result.human_plan.completed)
        kept: List[Dict[str, Any]] = []
        seen: set = set()
        for row in result.report_rows():
            task_id = str(row.get("task_id") or "")
            if (
                not task_id or task_id in seen or task_id in this_run
                or task_id in answered or row.get("status") != STATUS_OK
            ):
                continue
            seen.add(task_id)
            kept.append(row)
        return kept

    def resume_answered_ids(
        self, result: Any, outcomes: Sequence[TaskOutcome],
        kept_rows: Sequence[Dict[str, Any]],
    ) -> List[str]:
        """The tasks a resume keeps on the user's ``--human-task <id>=done``
        answer — an accepted check or failed task, a manual task completed by
        hand — that this run did not dispatch and *kept_rows* do not hold, in
        id order: the last part of the ``resume: kept`` line, and of the write
        mirror's ``kept_task_ids`` (fix round 23, review of round 22 #3: the
        mirror left them out, so ``--json`` read three kept beside the line's
        four). ``[]`` on a run that is not a resume."""
        if not self._resuming or self._ctx.dry_run:
            return []
        this_run = {o.task_id for o in outcomes if not o.skipped}
        seen = {str(row.get("task_id")) for row in kept_rows}
        answered = set(result.human_plan.accepted) | set(result.human_plan.completed)
        return [
            task_id for task_id in sorted(answered)
            if task_id not in this_run and task_id not in seen
        ]

    def warn_stale_result_files(self) -> None:
        """Name — never delete — result files no current task owns.

        ``implement``'s rename from the positional ``implement_batch_N.json``
        to the task-id-keyed ``implement_batch_T006.json`` (F1) left the old
        files on disk: nothing reads them any more
        (``resolve_output_target`` derives the name from ``output_name``), but
        a human opening the phase dir sees both namings side by side with no
        way to tell which are live (N6, 2026-09-16). Scoped to ``implement``,
        the one write kind whose ``output_name`` is keyed by the task id
        rather than a batch position: a positional kind's filenames have
        never been renamed, and without an id to key on there is no way to
        tell "an earlier run's now-completed batch" apart from "orphaned by a
        renumbering" — flagging those would be noise, not a finding. An
        id-keyed orphan (``implement_batch_T011.json`` from a run whose plan
        had eleven tasks) is the other way a file ends up here, so the
        warning does not call every one of them "an earlier naming".
        """
        if self._ctx.kind not in _write_context._ID_KEYED_WRITE_KINDS:
            return
        pattern = OUTPUT_NAME_PATTERN_BY_KIND.get(self._ctx.kind)
        if pattern is None:
            return
        current_names = {
            str(task.get("output_name") or "") for task in self._ctx.tasks
        }
        # "any task id" (D3n's own resume contract): every id this phase has
        # EVER recorded a status for, completed or not — `task_status` is one
        # flat map never trimmed across runs sharing `state.json` — union the
        # ids this run still has materialized, for a state-less caller (e.g.
        # a dry run with no `state=`).
        known_ids = {str(task.get("task_id") or "") for task in self._ctx.tasks}
        if hasattr(self._ctx.state, "get_all_task_statuses"):
            try:
                known_ids |= set(self._ctx.state.get_all_task_statuses())
            except Exception:  # noqa: BLE001 - advisory only, never fatal
                pass
        known_ids.discard("")
        try:
            candidates = sorted(os.listdir(self._ctx.phase_dir))
        except OSError:
            return
        stale = [
            name for name in candidates
            if pattern.match(name)
            and name not in current_names
            and not any(task_id in name for task_id in known_ids)
        ]
        if stale:
            self._ctx.log(
                f"[write-subagents] result files no current task owns (an "
                f"earlier naming, or a task the plan no longer has), ignored: "
                f"{', '.join(stale)}"
            )

    def check_partial_skips(self) -> List[str]:
        """Check each ``--human-task <batch>=skip`` answer before any dispatch
        (``write_outcomes.check_partial_skips``, each batch's evidence read by
        :meth:`partial_skip_evidence`): the refusal lines, or ``[]``. A
        refused answer is kept in ``refused_skips`` for the stop record."""
        if not self._partial_skips:
            return []
        self.refused_skips, lines = _write_outcomes.check_partial_skips(
            self._partial_skips, kind=self._ctx.kind, phase=self._ctx.phase,
            tasks=self._ctx.tasks, evidence=self.partial_skip_evidence,
        )
        return lines

    def partial_skip_evidence(self, task: Dict[str, Any]) -> Optional[str]:
        """Why *task* cannot be kept at the user's request, or ``None`` when it
        can (recorded in ``kept_at_request``) or already was: its result file
        read here, the rules in ``write_outcomes.partial_skip_refusal``."""
        task_id = str(task.get("task_id", ""))
        try:
            path = resolve_output_target(task, self._ctx.phase_dir)
        except ResultRejected:
            path = None
        if path is None or not path.is_file():
            return (
                f"{task_id} has no result on disk, so it did not stop as a "
                f"partial application this answer could keep"
            )
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return f"{task_id}'s result ({path.name}) cannot be read"
        verdict = data.get("verdict") if isinstance(data, dict) else None
        why = _write_outcomes.partial_skip_refusal(
            task_id, verdict, result_name=path.name,
            expected_ids=task.get("expected_ids") or [],
            fingerprint=lambda: self.task_fingerprint(task),
            counts_as_done=lambda: self.result_counts_as_done(
                task, path, task_id, int(task.get("batch_index", 0)), sibling=False,
            ),
            current_digest=lambda relative: file_sha256(
                os.path.join(self._ctx.repo_root, relative)),
        )
        if why is None and not _write_outcomes.already_kept(verdict):
            self.kept_at_request[task_id] = {
                "path": str(path), "data": data, "verdict": verdict,
            }
        return why

    def kept_outcome(
        self, task: Dict[str, Any], *, invoker: str,
        item_words: Callable[[Dict[str, str]], str],
    ) -> TaskOutcome:
        """The outcome of a batch kept as it stands at the user's request
        (fix round 18), taken out of ``kept_at_request``; writes nothing.

        Answered ``--human-task <id>=skip`` and checked by
        :meth:`partial_skip_evidence`. The outcome is the batch's own,
        ``applied``, with every item its report left out recorded as skipped
        at the user's request (``skipped_items``, never counted as applied)
        beside the items it declined, and its pre-batch snapshot, should one
        stand, as its rollback point. *invoker* is the run's, *item_words*
        the scheduler's wording of an item map (``_declined_words``). The scheduler's
        ``_keep_at_request`` records it: the audit's completion, the verdict
        stamp and the batch's effects.
        """
        task_id = str(task.get("task_id", ""))
        kept = self.kept_at_request.pop(task_id)
        data, verdict = kept["data"], kept["verdict"]
        expected = [str(i) for i in (task.get("expected_ids") or [])]
        unapplied = [
            str(i) for i in (verdict.get("unapplied_ids") or []) if str(i) in expected
        ]
        outcome = TaskOutcome(
            task_id=task_id, kind=self._ctx.kind, runner=invoker,
            status=STATUS_OK, profile=profile_for_kind(self._ctx.kind),
            write_outcome=WRITE_APPLIED,
            summary=(str(data.get("summary") or "").strip() or None),
            runner_notes=(verdict.get("runner_notes") or None),
        )
        outcome.output_path = kept["path"]
        outcome.files_touched = [str(p) for p in (verdict.get("files_touched") or [])]
        outcome.expected_ids = expected
        outcome.returned_ids = [str(i) for i in (data.get("ids") or [])]
        outcome.sha256_before = dict(verdict.get("sha256_before") or {})
        outcome.sha256_after = dict(verdict.get("sha256_after") or {})
        outcome.declined = row_declined(verdict)
        outcome.skipped_items = {
            item: (
                f"--human-task {task_id}=skip: the batch did not report it "
                f"applied, and you chose to keep the batch as it stood"
            )
            for item in unapplied
        }
        read_verdict_checks(outcome, verdict)
        snapshot = os.path.join(self._ctx.safety_dir, "pre_batch", task_id)
        if os.path.isdir(snapshot):
            outcome.snapshot_dir = snapshot
        # Fix round 27: the stop after the last reason only where it has no
        # mark of its own (`with_closing_mark`).
        outcome.reason = with_closing_mark(
            f"KEPT AT YOUR REQUEST (--human-task {task_id}=skip): what it "
            f"applied stays as it left it"
            + (f" ({', '.join(outcome.files_touched)})" if outcome.files_touched else "")
            + f"; not applied, skipped at your request: "
            f"{item_words(outcome.skipped_items)}"
            + (
                f"; declined by the batch: "
                f"{item_words(outcome.declined)}"
                if outcome.declined else ""
            )
        ) + " It was not dispatched again."
        return outcome

    def task_fingerprint(self, task: Dict[str, Any]) -> str:
        """The D2g binding for one materialized write task, as one hash.

        Over the **materialized task**, deliberately not over its ``inputs``
        block. D2g's hashes name upstream artifacts, and a write phase *writes*
        the artifacts its own hashes cover: ``apply-suggestions`` rewrites the
        plan ``inputs.plan_sha256`` binds to, ``apply-code-fixes`` invalidates
        the ``inputs.diff_sha256`` its own edits were derived from, and
        ``implement`` inserts the summary reference into the plan. Comparing
        those on resume would make a *successful* batch look like changed
        inputs and re-dispatch it — applying it twice, which is the failure the
        resume guard exists to prevent.

        The prompt, the expected ids and the declared set are the derived data
        that actually moves when the plan, the suggestions or the batching
        changed: under ``context_mode: inline`` the payload travels *inside*
        ``prompt``, so an edited suggestion changes the prompt directly.
        ``prompt`` is the **raw** prompt — ``{prior_changes_context}`` is bound
        late and per dispatch — so the text hashed here is stable across runs
        of the same inputs.

        Under a commit review's apply guard (:meth:`CommitGuardLeg.guard`) the
        prompt's protected-path clause is left out
        (``code_fix_batcher.without_protected_clause``). That clause lists
        the guard's protected set, and a ``--resume`` grows the set whenever
        its re-check protects a file edited by hand since the stop
        (plans/review-commits.md §2.7, §2.8). Every prompt then changes, and a
        batch the stopped run had completed would read as made from changed
        inputs and be applied a second time. The list only forbids later
        writes, so the batches still to run get it in their prompts and from
        the deny layer. The rest of the prompt is hashed as before.
        """
        prompt = str(task.get("prompt") or "")
        if self._commit_guard() is not None:
            prompt = without_protected_clause(prompt)
        payload = json.dumps(
            {
                "kind": self._ctx.kind,
                "prompt": prompt,
                "expected_ids": [str(i) for i in (task.get("expected_ids") or [])],
                "declared_files": sorted(declared_file_set(task)),
                "batch_index": int(task.get("batch_index", 0)),
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def fingerprint_path(self) -> Path:
        return Path(self._ctx.phase_dir) / WRITE_FINGERPRINT_FILENAME

    def load_fingerprints(self) -> Dict[str, str]:
        try:
            data = json.loads(self.fingerprint_path().read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return {}
        recorded = data.get("tasks") if isinstance(data, dict) else None
        if not isinstance(recorded, dict):
            return {}
        return {str(key): str(value) for key, value in recorded.items()}

    def record_fingerprint(self, task: Dict[str, Any]) -> None:
        """Persist one task's inputs binding beside its result file."""
        recorded = self.load_fingerprints()
        recorded[str(task.get("task_id", ""))] = self.task_fingerprint(task)
        path = self.fingerprint_path()
        try:
            # A new file's mode each time, as it always had (docs/development/
            # runtime.md#atomic-file-writes); its folder made and held below
            # the plan's directory
            # (docs/development/write-safety.md#plan-output-containment).
            write_in_plan_dir(path, json.dumps({
                "fingerprint_version": 1,
                "kind": self._ctx.kind,
                "tasks": recorded,
            }, indent=2, sort_keys=True).encode("utf-8"), make=True, keep_mode=False)
        except OSError as exc:  # noqa: BLE001 - bookkeeping must not fail a phase
            self._ctx.log(
                f"[write-subagents] warning: could not record the inputs binding "
                f"for {task.get('task_id')}: {exc}"
            )

    @staticmethod
    def recorded_files_touched(output_path: str) -> List[str]:
        """``files_touched`` as the batch's result file on disk records it."""
        try:
            data = json.loads(Path(output_path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        raw = data.get("files_touched") if isinstance(data, dict) else None
        if not isinstance(raw, list):
            return []
        seen: List[str] = []
        for item in raw:
            text = str(item).strip()
            if text and text not in seen:
                seen.append(text)
        return seen

    def sibling_results(
        self, task: Dict[str, Any]
    ) -> List[Tuple[Path, str, int]]:
        """Other result files of this kind that attest to this task's items.

        An apply kind's ids and result names are positional, so a resume
        whose selection changed can hand a batch that already landed as
        ``apply-batch-1`` the id ``apply-batch-2``, with no
        ``apply_batch_2.json`` to find — and re-apply it (adversarial review,
        2026-10-02). The verdict stamp names the items a result was produced
        for; a file naming exactly this task's items is this batch's, under
        the id and index it ran as. ``implement`` keys results by the plan
        task's own id and has no such case.
        """
        if self._ctx.kind == "implement":
            return []
        expected = sorted(str(i) for i in (task.get("expected_ids") or []))
        if not expected:
            return []
        try:
            own = resolve_output_target(task, self._ctx.phase_dir)
        except ResultRejected:
            own = None
        template = write_output_name(self._ctx.kind, 0)
        prefix, suffix = template.split("0", 1)
        found: List[Tuple[Path, str, int]] = []
        for path in sorted(Path(self._ctx.phase_dir).glob(f"{prefix}*{suffix}")):
            token = path.name[len(prefix):len(path.name) - len(suffix)]
            index = _RESULT_TOKEN.match(token)
            if index is None or (own is not None and path == own):
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            verdict = data.get("verdict") if isinstance(data, dict) else None
            if not isinstance(verdict, dict):
                continue
            recorded = verdict.get("expected_ids")
            if not isinstance(recorded, list) or sorted(map(str, recorded)) != expected:
                continue
            recorded_id = str(verdict.get("task_id") or "")
            if not recorded_id:
                continue
            found.append((path, recorded_id, int(index.group(1))))
        return found

    def retire_foreign_result(self, task: Dict[str, Any]) -> None:
        """Move another batch's result out from under this task's positional name.

        A result file is named by batch index, so a resume whose selection
        renumbered the batches dispatches B as ``apply-batch-1`` over the
        ``apply_batch_1.json`` C landed under that id in the earlier run —
        and C's only evidence of being done was gone before its own turn
        came (adversarial review, 2026-10-02). A result whose verdict names
        other items is kept beside the slot as ``<stem>.items-<sha8>.json``
        (``-2``, ``-3`` … when taken), where :meth:`sibling_results` reads
        it; a result for the same items is overwritten as before.
        """
        if self._ctx.kind == "implement":
            return
        try:
            target = resolve_output_target(task, self._ctx.phase_dir)
        except ResultRejected:
            return
        if not target.is_file():
            return
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        verdict = data.get("verdict") if isinstance(data, dict) else None
        recorded = verdict.get("expected_ids") if isinstance(verdict, dict) else None
        if not isinstance(recorded, list):
            return
        expected = sorted(str(i) for i in (task.get("expected_ids") or []))
        if sorted(map(str, recorded)) == expected:
            return
        stem = target.name[:-len(".json")]
        base = f"{stem}.items-{TaskSnapshot.items_digest(recorded)}"
        kept = target.with_name(f"{base}.json")
        counter = 2
        while kept.exists():
            kept = target.with_name(f"{base}-{counter}.json")
            counter += 1
        try:
            os.replace(str(target), str(kept))
        except OSError as exc:  # noqa: BLE001 - bookkeeping must not fail a phase
            self._ctx.log(
                f"[write-subagents] warning: could not keep {target.name} "
                f"(another batch's result) aside before {task.get('task_id')} "
                f"reuses the name: {exc}"
            )
            return
        self._ctx.log(
            f"[write-subagents] {task.get('task_id')}: {target.name} holds the "
            f"result of other items (an earlier run's batch under this id); "
            f"kept at {kept.name}."
        )

    def already_done(self, task: Dict[str, Any]) -> bool:
        """Whether :meth:`done_evidence` finds a result to resume from."""
        return self.done_evidence(task) is not None

    def done_evidence(
        self, task: Dict[str, Any]
    ) -> Optional[Tuple[str, str, Dict[str, Any]]]:
        """The result file, the id it was produced under and the audit log's
        completion record for its items (``{}`` when there is none), when the
        task is done.

        The task's own positional result first; for an apply kind, a sibling
        result naming the same items next (:meth:`sibling_results`), judged
        by the same clauses with the id and batch index it ran as — the
        audit, the verdict and the inputs binding are read for THAT batch,
        never for whatever this run put under the renumbered id.

        The audit log is read at most once per call, when a result file
        first needs it, and never kept for another task: it is resume
        evidence, and a sibling of a disjoint group may be writing it.
        """
        task_id = str(task.get("task_id", ""))
        expected = [str(item) for item in (task.get("expected_ids") or [])]
        read: List[List[Dict[str, Any]]] = []

        def audit_records() -> List[Dict[str, Any]]:
            if not read:
                read.append(self._ctx.audit.records())
            return read[0]

        def completion(recorded_id: str) -> Dict[str, Any]:
            return self._ctx.audit.completion_for(
                recorded_id, expected_ids=expected, records=audit_records(),
            ) or {}

        try:
            own = resolve_output_target(task, self._ctx.phase_dir)
        except ResultRejected:
            own = None
        if own is not None and self.result_counts_as_done(
            task, own, task_id, int(task.get("batch_index", 0)), sibling=False,
            audit_records=audit_records,
        ):
            return str(own), task_id, completion(task_id)
        for path, recorded_id, index in self.sibling_results(task):
            if self.result_counts_as_done(
                task, path, recorded_id, index, sibling=True,
                audit_records=audit_records,
            ):
                self._ctx.log(
                    f"[write-subagents] {task_id}: its items already landed as "
                    f"{recorded_id} ({path.name}) in an earlier run of this "
                    f"phase — the batch was renumbered by a selection change, "
                    f"not re-applied."
                )
                return str(path), recorded_id, completion(recorded_id)
        return None

    def result_counts_as_done(
        self, task: Dict[str, Any], target: Path, task_id: str,
        batch_index: int, *, sibling: bool,
        audit_records: Optional[Callable[[], List[Dict[str, Any]]]] = None,
    ) -> bool:
        """Resume's definition of done (D3i), all five clauses of it.

        ``task_id``/``batch_index`` are the ones the result was produced
        under (the task's own, or a renumbered sibling's); ``sibling`` says
        the file was found by its items, in which case the clauses keyed by
        positional id alone (``state.json``'s task status, the fingerprint
        file) are read from the verdict stamp instead, since this run may
        already have put another batch under that id. ``audit_records``
        returns the audit log's records as :meth:`done_evidence` read them;
        without it the log is read now.

        The result file must exist, parse and validate — **and** the task it was
        produced from must not have moved (D2g). The bridge rewrites
        ``write_tasks.json`` before the scheduler runs, so the previous run's own
        hashes are gone by the time resume asks; the binding therefore lives
        beside the results in ``.write_task_inputs.json`` and is compared against
        the *freshly materialized* task (see :meth:`task_fingerprint`). A
        recorded binding that moved means the plan, the suggestions or the
        batching changed between the partial run and the resume, and the stale
        batch result is re-dispatched rather than silently accepted as current.

        A task with **no** recorded binding keeps the previous behaviour: absence
        of evidence that the inputs moved is not evidence that they did, and
        re-dispatching an apply batch that already landed would apply it twice.

        The fifth clause reads the file's **own** ``ids``: a result that attests
        to none of this task's ``expected_ids`` was produced for a different
        task, whatever its name says. Measured 2026-09-16 — a resumed implement
        phase re-pointed T006 at an ``implement_batch_0.json`` whose ``ids`` said
        ``["T001"]``, and because T006 had never finished it had no recorded
        binding either, so the fourth clause had nothing to compare and five
        never-dispatched tasks were declared complete. The evidence was on disk
        and simply never read. It is a *defence in depth* beside the naming fix
        in ``subagent_tasks.implement_output_name``: neither alone is why the
        skip is safe.
        """
        if not target.is_file() or target.stat().st_size == 0:
            return False
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return False
        if validate_result(self._ctx.kind, data):
            return False
        verdict = data.get("verdict")
        if (
            str(data.get("status") or "") not in (WRITE_APPLIED, WRITE_NO_OP)
            and not _check_records._findings_from_a_failed_claim(data)
            and not _check_records._declined_from_a_failed_claim(data)
        ):
            # A schema-valid `{"status": "failed"}` is a batch the previous run
            # recorded as NOT done; resuming past it on the strength of the
            # file existing would skip exactly the batch --resume is for —
            # unless the verdict stamped on it read it as a check's findings
            # (fix round 13), whose re-run `CheckHolds.check_findings_rerun` decides.
            return False
        if isinstance(verdict, dict) and (
            not verdict.get("ok", True)
            or verdict.get("write_outcome") == WRITE_CLEAN_FAILURE
        ):
            # The scheduler's own classification, stamped by `_stamp_verdict`
            # once `_classify` decided (F1): the file reads `applied` because
            # that is what the runner printed before it died, and the loop
            # stopped on it promising a re-dispatch. A `clean-failure` stamped
            # `ok` is a run before fix round 14 reading an `applied` claim that
            # moved nothing as done: nothing moved, so it is dispatched again.
            self._ctx.log(
                f"[write-subagents] {task_id}: {target.name} claims "
                f"{data.get('status')!r} but the previous run classified it "
                f"{verdict.get('write_outcome')} — re-dispatching it rather "
                f"than resuming it (F1)."
            )
            return False
        if sibling and not isinstance(verdict, dict):
            return False
        if (
            not sibling
            and hasattr(self._ctx.state, "get_task_status")
        ):
            # The same fact from `state.json`, for a result file that predates
            # the verdict stamp: `_record_batch_effects` wrote `failed` for
            # every outcome that was not ok, and that record outlives the
            # optimistic claim in the file.
            try:
                recorded_status = self._ctx.state.get_task_status(task_id)
            except Exception:  # noqa: BLE001 - advisory, never fatal
                recorded_status = None
            if recorded_status == "failed":
                self._ctx.log(
                    f"[write-subagents] {task_id}: state.json records it "
                    f"`failed` although {target.name} claims "
                    f"{data.get('status')!r} — re-dispatching it rather than "
                    f"resuming it (F1)."
                )
                return False
        # A crash can occur after persist_result but before classification (or
        # before a new result replaces an older successful one). The last
        # dispatch then has no completion: neither file is evidence of success.
        # Un-audited legacy/native results retain their compatibility behavior.
        if audit_records is None:
            audit_records = self._ctx.audit.records
        expected = [str(item) for item in (task.get("expected_ids") or [])]
        if sibling:
            # Found by its verdict stamp, which only `_classify` writes, so
            # the crash-before-classification shape cannot apply; the audit's
            # own record for these items has to agree it succeeded.
            recorded = self._ctx.audit.completion_for(
                task_id, expected_ids=expected, records=audit_records())
            if not recorded or recorded.get("status") != STATUS_OK:
                return False
        else:
            latest = next((
                row for row in reversed(audit_records())
                if row.get("task_id") == task_id
                and row.get("event") in ("dispatched", "completed")
            ), None)
            if latest and (
                latest.get("event") == "dispatched"
                or latest.get("status") != STATUS_OK
            ):
                self._ctx.log(
                    f"[write-subagents] {task_id}: the last dispatch has no "
                    "successful classification — re-dispatching rather than "
                    "trusting its result."
                )
                return False
        returned = [
            str(item) for item in (data.get("ids") or [])
            if isinstance(data.get("ids"), list)
        ]
        if expected and returned and not (set(expected) & set(returned)):
            self._ctx.log(
                f"[write-subagents] {task_id}: {target.name} attests to "
                f"{', '.join(sorted(returned))} and not to "
                f"{', '.join(expected)} — it is another task's result, so this "
                f"one is re-dispatched rather than resumed (D3i)."
            )
            return False
        if sibling:
            recorded_fp = str(verdict.get("inputs_fingerprint") or "")
            current_fp = self.task_fingerprint({**task, "batch_index": batch_index})
        else:
            recorded_fp = self.load_fingerprints().get(task_id)
            current_fp = self.task_fingerprint(task)
        if recorded_fp and recorded_fp != current_fp:
            self._ctx.log(
                f"[write-subagents] {task_id}: the inputs it was materialized "
                f"from have changed since {target.name} was written — "
                f"re-dispatching it instead of resuming it (D2g)."
            )
            return False
        return True

    def earlier_report_rows(self) -> List[Dict[str, Any]]:
        """The task rows the previous run left in ``write_batch_report.json``.

        Read before this run writes its own. Anything unreadable is simply no
        earlier rows: the report is evidence, never an input the loop obeys.

        Only rows of *this review cycle*: an apply phase's batch ids
        (``apply-batch-N``) are per cycle and the phase dir outlives the
        review, so a ``--resume`` typed after a ``--force`` review re-run
        carried the previous review's rows as "(earlier run)" rows of a
        different review (adversarial review, 2026-10-02). The rule is
        :func:`state_manager.predates_review`: a report written (its
        ``written_at``, else its mtime) before its review's latest
        completion belongs to the earlier cycle, and a missing date on
        either side keeps the rows.
        """
        path = os.path.join(self._ctx.phase_dir, _write_reports.WRITE_BATCH_REPORT_FILENAME)
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError):
            return []
        if not isinstance(data, dict):
            return []
        written_at = stamp_or_mtime(data.get("written_at"), path)
        reviewed_at = self.review_completed_at()
        if predates_review(written_at, reviewed_at):
            self._ctx.log(
                f"[write-subagents] the earlier {_write_reports.WRITE_BATCH_REPORT_FILENAME} "
                f"(written {written_at.isoformat(timespec='seconds')}) predates "
                f"this phase's review (completed "
                f"{reviewed_at.isoformat(timespec='seconds')}); its rows belong "
                f"to the previous review cycle and are not carried."
            )
            return []
        rows = data.get("tasks")
        return [
            row for row in (rows or [])
            if isinstance(row, dict) and row.get("task_id")
        ]

    def review_completed_at(self) -> Optional[datetime]:
        """When the review this apply phase applies last completed, or None
        (:func:`review_completed_at`)."""
        return review_completed_at(getattr(self._ctx.state, "state", None), self._ctx.kind)
