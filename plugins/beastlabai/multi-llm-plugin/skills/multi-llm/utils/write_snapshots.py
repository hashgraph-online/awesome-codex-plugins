"""The pre-batch snapshots of one write phase and where they are stored (D3h).

Every write dispatch takes a mandatory pre-batch snapshot first: the bytes of
each file it declares, under ``{phase}/pre_batch/{task_id}/``, which is the
batch's rollback point (``util restore-batch``) and what its classification
compares the files against. :class:`PreBatchSnapshots` takes it
(:meth:`PreBatchSnapshots.take`), or reuses the one an earlier dispatch of the
same batch took, so the rollback point stays the bytes from before the batch's
FIRST dispatch (:meth:`PreBatchSnapshots.reusable`); and it decides, once per
admitted group and before any of its snapshots, whether a repo-wide phase's
snapshots, rollback store and audit log must live outside the phase dir because
a runner of the group runs on the plugin's jail, which grants the phase dir
too (:meth:`PreBatchSnapshots.decide_rollback_storage`). A snapshot is never
deleted: one that is another batch's, or a previous review cycle's, is set
aside.

``WriteBatchScheduler`` composes it with the run's ``RunContext``
(docs/development/write-scheduler.md#where-the-schedulers-helpers-live). The
snapshots this run took or reused (``taken``) and the ids of the reused ones
(``reused``, which the classification reads) are its own. It reads the runner
preflight through the run's :class:`write_grant.WriteGrant`, an earlier run's
results through its ``write_resume.ResumeEvidence``, and the runner a task
resolves to through the scheduler's ``_runner_for``, looked up at each call.
"""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Sequence

from . import batch_prompt as _batch_prompt
from . import write_context as _write_context
from .providers.base import SANDBOX_RUNG_PLUGIN_LANDLOCK, WRITE_SCOPE_REPO_WIDE
from .runner_selection import profile_for_kind
from .subagent_tasks import snapshot_file_set
from .write_safety import (
    PRE_BATCH_DIRNAME,
    TaskSnapshot,
    WriteSafetyError,
    claim_external_safety_dir,
    contain_under_root,
    relative_to_root,
)


class PreBatchSnapshots:
    """One run's pre-batch snapshots and the decision where they live.

    Built once per run by the scheduler. *resume* is the run's ``--resume``
    (a snapshot is reused only then); *executor_dispatch* whether dispatches
    go through the executor, whose runners a rollback-storage preflight
    probes; *grant* the run's ``WriteGrant``; *evidence* its
    ``ResumeEvidence``; *runner_for* reaches the scheduler's ``_runner_for``.
    """

    def __init__(
        self,
        ctx: _write_context.RunContext,
        *,
        resume: bool,
        executor_dispatch: bool,
        grant: Any,
        evidence: Any,
        runner_for: Callable[[Dict[str, Any]], str],
    ) -> None:
        self._ctx = ctx
        self._resuming = resume
        self._executor_dispatch = executor_dispatch
        self._grant = grant
        self._evidence = evidence
        self._runner_for = runner_for
        #: Whether `decide_rollback_storage` ran for the admitted group, and
        #: that group (the loop sets both before the group's first dispatch).
        self.storage_decided = False
        self._storage_lock = threading.Lock()
        self.storage_candidates: Optional[Sequence[Dict[str, Any]]] = None
        #: ``task id -> the snapshot this run took or reused for it``.
        self.taken: Dict[str, TaskSnapshot] = {}
        #: Task ids whose pre-batch snapshot was REUSED from an earlier
        #: dispatch of this same batch (`take`/`reusable`), rather than taken
        #: fresh at the top of this dispatch. The classification reads this to
        #: tell "the diff is a killed attempt's, not this dispatch's" apart
        #: from "this dispatch's own snapshot disagrees with its no-op claim"
        #: (N2, 2026-09-16) — the two read identically from the bytes alone.
        self.reused: set = set()

    def decide_rollback_storage(self, task: Dict[str, Any], profile: str) -> None:
        """Choose storage for an admitted group's runners before snapshots start.

        The first task can use another runner than a later or co-scheduled
        jailed task. Resolving the group's runner set under this lock prevents
        promotion while a sibling is already writing its snapshot or audit.
        An inconclusive preflight conservatively requires external storage;
        its actual dispatch still reports its own refusal, and a later
        successful preflight cannot strand evidence inside a writable grant.
        """
        if self._ctx.dry_run or not self._executor_dispatch:
            return
        with self._storage_lock:
            if self.storage_decided:
                return
            if self._grant.write_scope != WRITE_SCOPE_REPO_WIDE:
                self.storage_decided = True
                return
            needs_external = False
            seen = set()
            candidates = self.storage_candidates
            for candidate in (candidates if candidates is not None else self._ctx.tasks or [task]):
                if candidate.get("is_human") or candidate.get("executor_role") == "human":
                    continue
                if (candidate is not task and self._resuming
                        and not _batch_prompt.is_check_task(self._ctx.kind, candidate)
                        and self._evidence.done_evidence(candidate) is not None):
                    continue
                try:
                    runner = self._runner_for(candidate)
                    candidate_profile = profile_for_kind(str(candidate.get("kind") or self._ctx.kind))
                    key = (runner, candidate_profile)
                    if key in seen:
                        continue
                    seen.add(key)
                    self._grant.preflight(runner, candidate_profile)
                    needs_external |= self._grant.recorded_rung(runner, candidate_profile) == SANDBOX_RUNG_PLUGIN_LANDLOCK
                except Exception:  # the task's own dispatch reports the preflight error
                    needs_external = True
            if needs_external:
                external = claim_external_safety_dir(self._ctx.phase_dir, self._ctx.repo_root)
                for snapshot in self.taken.values():
                    snapshot.directory = os.path.join(
                        external, PRE_BATCH_DIRNAME, Path(snapshot.directory).name,
                    )
                self._ctx.log(
                    f"[write-subagents] this repo-wide phase may run batches on the "
                    f"plugin's jail, which grants the phase dir too: pre-batch "
                    f"snapshots, the rollback store and the audit log live outside "
                    f"it, at {external} (a copy inside the phase dir is never read)."
                )
            self.storage_decided = True

    def take(self, task: Dict[str, Any]) -> TaskSnapshot:
        """Take (or reuse) this task's mandatory pre-batch snapshot (D3h).

        Mandatory, and refused when there is nothing to snapshot: a write task with
        no declared or snapshottable file gives the classification nothing to
        compare, which would make every outcome read as "clean failure".
        """
        task_id = str(task.get("task_id", ""))
        files = snapshot_file_set(task)
        if not files and self._ctx.kind == "implement":
            # A verification-only task: generate-tasks emits an agent task with
            # no files to create or modify when the work is a check ("Inline
            # module syntax gate", 2026-10-01, which this refusal used to dead-end
            # on at batch 12, with `--resume` hitting it again). The refusal's
            # reason does not apply to it: the byte comparison has nothing to
            # compare because the task is promised to change nothing, and the
            # undeclared-write sweep is then the whole verdict — see
            # `_verification_only` and `write_verdict.decide`. Only `implement`
            # materializes such a task; the three apply kinds always declare
            # their one artifact, so an empty set there is still a bug.
            self._ctx.log(
                f"[write-subagents] {task_id}: declares no files, so it runs as "
                f"a verification-only task: any file it changes is a partial "
                f"application, not an edit."
            )
        elif not files:
            raise WriteSafetyError(
                f"Refusing to dispatch write task {task_id}: it declares no files "
                f"to snapshot, so the post-run byte comparison would have nothing "
                f"to compare and every outcome would read as a clean failure. "
                f"Populate `declared_files`/`snapshot_files` on the materialized "
                f"task (D3h). Nothing was dispatched."
            )
        expected_ids = [str(i) for i in (task.get("expected_ids") or [])]
        reused = (
            self.reusable(task_id, files, expected_ids)
            if self._resuming else None
        )
        if reused is not None:
            self._ctx.log(
                f"[write-subagents] {task_id}: reusing the pre-batch snapshot a "
                f"previous run took at {reused.directory} — the rollback point "
                f"stays the bytes from before this batch's FIRST dispatch"
            )
            self.taken[task_id] = reused
            self.reused.add(task_id)
            return reused
        if not self._resuming:
            # `--fresh` (and implement's plain run) reuses no snapshot — but a
            # slot an earlier run filled is that run's rollback point, and
            # `TaskSnapshot.take` would copy today's bytes over it (adversarial review,
            # 2026-10-02: a `--fresh` on an un-reverted target left every
            # slot holding already-applied bytes). Set aside, never deleted.
            existing = TaskSnapshot.load(
                self._ctx.phase_dir, task_id, expected_root=self._ctx.repo_root,
            )
            if existing is not None:
                moved_to = existing.set_aside()
                self._ctx.log(
                    f"[write-subagents] {task_id}: an earlier run's pre-batch "
                    f"snapshot under that id is kept at {moved_to}; this run "
                    f"takes its own."
                )
        snapshot = TaskSnapshot.take(
            phase_dir=self._ctx.phase_dir, task_id=task_id, files=files,
            root=self._ctx.repo_root, expected_ids=expected_ids,
        )
        self.taken[task_id] = snapshot
        return snapshot

    def reusable(
        self, task_id: str, files: Sequence[str],
        expected_ids: Sequence[str] = (),
    ) -> Optional[TaskSnapshot]:
        """A previous run's snapshot for this batch, when it still applies.

        A batch reaching :meth:`take` under resume is one that has not
        succeeded yet (``ResumeEvidence.already_done`` skips the rest), and its half-applied
        edits are deliberately left on disk for a human to inspect. Retaking
        the snapshot over them would make *those* bytes the rollback point:
        measured 2026-09-15 across four resumed runs of one failed batch, each
        run re-snapshotted the previous run's partial edits, so ``util
        restore-batch`` could no longer reach the file as it was before the
        batch, and the "pre-batch snapshots are intact" line was untrue.

        Reused only when the manifest names the same declared set, byte for
        byte; a batch whose file set changed (the D2g resume guard should have
        refused it first) takes a fresh snapshot.

        And only when it was taken for the same items, the rule
        :func:`_same_batch_row` applies to report rows. An apply batch always
        declares its one artifact and its id is positional, so after a
        selection change the batch now holding ``apply-batch-1`` inherited the
        stopped ``apply-batch-1``'s rollback point, and ``util restore-batch``
        of the new batch also reverted the edits the stopped batch left in
        place (#28 follow-up). That snapshot is another batch's: it is set
        aside (renamed, never deleted) and this batch takes its own. A
        manifest that records no items (written before they were recorded)
        falls back to the id, as before.
        """
        existing = TaskSnapshot.load(
            self._ctx.phase_dir, task_id, expected_root=self._ctx.repo_root,
        )
        # The same cutoff `ResumeEvidence.earlier_report_rows` applies: a snapshot taken
        # before the review this phase applies completed belongs to the
        # previous cycle — the bytes before THAT cycle's batch, so restoring
        # from it would roll that cycle's applied edit back too (follow-up to
        # the 2026-10-02 adversarial review). Set aside, never deleted.
        # `taken_before` applies the rule to the second, as the manifest is
        # stamped.
        reviewed_at = self._evidence.review_completed_at()
        if existing is not None and existing.taken_before(reviewed_at):
            moved_to = existing.set_aside()
            self._ctx.log(
                f"[write-subagents] {task_id}: the pre-batch snapshot under "
                f"that id was taken at {existing.taken_at or 'an unknown time'}, "
                f"before this phase's review completed "
                f"({reviewed_at.isoformat(timespec='seconds')}), so it is a "
                f"previous review cycle's rollback point; kept at {moved_to}."
            )
            existing = None
        recorded_ids = (existing.expected_ids or []) if existing else []
        if existing is not None and recorded_ids and expected_ids and (
            sorted(recorded_ids) != sorted(str(i) for i in expected_ids)
        ):
            moved_to = existing.set_aside()
            self._ctx.log(
                f"[write-subagents] {task_id}: the pre-batch snapshot under "
                f"that id was taken for other items (an earlier run's batch); "
                f"kept at {moved_to}."
            )
            existing = None
        if existing is None and expected_ids and self._ctx.kind != "implement":
            # The items may have held this id before and been set aside when
            # the id went to others (B deselected, C takes `apply-batch-1`,
            # B re-selected): their own pre-first-dispatch snapshot comes
            # back into the slot rather than a fresh one being taken over
            # every run's edits since.
            existing = TaskSnapshot.reinstate(
                self._ctx.phase_dir, task_id, [str(i) for i in expected_ids],
                not_before=reviewed_at,
            )
            if existing is not None:
                self._ctx.log(
                    f"[write-subagents] {task_id}: the snapshot an earlier run "
                    f"took for these same items was set aside when the id "
                    f"went to other items; moved back to {existing.directory}."
                )
        if existing is None:
            return None
        try:
            wanted = sorted(
                relative_to_root(str(contain_under_root(
                    candidate, self._ctx.repo_root, what="snapshot target"
                )), self._ctx.repo_root)
                for candidate in files
            )
        except WriteSafetyError:  # a path outside the root: `take` refuses it
            return None
        recorded = sorted(e.relative for e in existing.declared_entries())
        if wanted != recorded:
            return None
        return existing
