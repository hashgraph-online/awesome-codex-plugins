"""The commit write policy's leg of a write phase (plans/review-commits.md §2.7).

:class:`CommitGuardLeg` is what an apply-code-fixes phase of a commit review
does with the apply guard ``state.json`` pins (``commit_write_guard.commit_guard_of``):
the guard's protected set and context plan join the run's write policy as its
exact-path deny layer (:meth:`CommitGuardLeg.protect`); each batch is re-checked
against the identities the guard saved before it is dispatched
(:meth:`CommitGuardLeg.recheck`), and the batches it stops are remembered for the
loop to go past (:attr:`CommitGuardLeg.stale`); the watched paths are read before
each dispatch and compared after it (:meth:`CommitGuardLeg.watch_begin`,
:meth:`CommitGuardLeg.watch_after`), put back when a batch changed them
(:meth:`CommitGuardLeg.restore_watched`,
:meth:`CommitGuardLeg.protected_unclassified`), and a completed batch's fix files
are re-pinned to the bytes it left (:meth:`CommitGuardLeg.repin`). Every method is
a no-op without a guard.

``WriteBatchScheduler`` composes it with the run's ``RunContext``
(docs/development/write-scheduler.md#where-the-schedulers-helpers-live). The
guard is the live dict inside ``ctx.state``, the run's one ``StateManager``: the
leg mutates it and saves it back under the scheduler's ``_effects_lock``, which it
is handed, and never reloads the state. A refused batch is recorded through the
scheduler's ``_refused``, looked up at each call.
"""

from __future__ import annotations

import copy
import os
import threading
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from . import commit_write_guard as _commit_write_guard
from . import write_context as _write_context
from .task_outcome import TaskOutcome
from .write_safety import CONTEXT_PLAN_RULE, TaskSnapshot
from .write_verdict import PolicyRestore


class CommitGuardLeg:
    """One run's commit write policy: the guard's deny layer, its pre-dispatch
    re-check, the watched paths of each dispatch and the re-pin after it.

    Built once per run by the scheduler. *effects_lock* is the scheduler's
    ``_effects_lock``, under which the guard is mutated and saved; *refused*
    reaches the scheduler's ``_refused``, which records a batch refused before
    dispatch.
    """

    def __init__(
        self,
        ctx: _write_context.RunContext,
        *,
        effects_lock: threading.Lock,
        refused: Callable[..., TaskOutcome],
    ) -> None:
        self._ctx = ctx
        self._effects_lock = effects_lock
        self._refused = refused
        #: plans/review-commits.md §2.7: the batches the pre-dispatch
        #: re-check stopped (``task id -> their batch line``), which the loop
        #: goes past instead of stopping on, and this phase's
        #: ``orchestrator_output.json`` batches, whose fixes name every file
        #: their groups do (read once, on the first batch a guard governs).
        self.stale: Dict[str, str] = {}
        self.batches: Optional[List[Any]] = None
        #: The watched paths' disk ids read just before each dispatch
        #: (``task id -> {path: id}``), for its post-run protected check.
        self.watch_before: Dict[str, Dict[str, Optional[str]]] = {}

    def guard(self) -> Optional[Dict[str, Any]]:
        """The live apply guard of the state this run holds, or ``None`` (no
        pinned record with a guard, or not an apply-code-fixes phase)."""
        return _commit_write_guard.commit_guard_of(
            getattr(self._ctx.state, "state", None), self._ctx.kind,
        )

    def protect(self, guard: Optional[Mapping[str, Any]]) -> None:
        """Add the guard's protected set to the run's policy as its exact-path
        deny layer (``write_safety.WritePolicy.deny_exact``), with the rule
        text ``changed since reviewed commit <head7>``, and the context plan
        (``guard["context_plan"]``, §2.7: read-only in this review whether or
        not it changed) with :data:`write_safety.CONTEXT_PLAN_RULE`, so a
        batch that declares or writes it fails like a protected write. A
        symlinked context plan's in-repository targets
        (``guard["context_plan_targets"]``, ``commit_apply.
        context_plan_paths``) hold its text, so they get the same rule: the
        layer matches a path by its own name, never through the link.
        Idempotent: run at construction and again whenever a re-check adds
        files to the set."""
        if guard is None:
            return
        protected = guard.get("protected")
        if isinstance(protected, Mapping) and protected:
            self._ctx.policy.deny_exact(
                [str(path) for path in protected], _commit_write_guard.commit_protected_rule(guard),
            )
        targets = guard.get("context_plan_targets")
        names = [guard.get("context_plan")] + (
            list(targets) if isinstance(targets, Mapping) else [])
        plan_names = [
            name for name in names
            if isinstance(name, str) and name and not os.path.isabs(name)
            and name != ".." and not name.startswith("../")
        ]
        if plan_names:
            self._ctx.policy.deny_exact(plan_names, CONTEXT_PLAN_RULE)

    def watch_begin(self, task_id: str) -> None:
        """Read the disk ids of every path no batch may change (the
        protected set and the context plan, ``commit_apply.watched_ids``)
        just before *task_id* is dispatched, so its post-run check
        (:meth:`watch_after`) counts only what moved during its own
        window. No-op without a guard. Cost: one ``git hash-object`` call
        over that set, whatever the tree's size."""
        guard = self.guard()
        if guard is None:
            return
        commit_apply = _commit_write_guard.load_commit_apply()
        with self._effects_lock:
            watched = list(commit_apply.watched_ids(guard))
        if watched:
            self.watch_before[task_id] = commit_apply.disk_blob_ids(
                watched, cwd=self._ctx.repo_root,
            )

    def watch_after(self, task_id: str) -> Tuple[List[str], Any, Optional[Dict[str, Any]]]:
        """The watched paths *task_id*'s window changed: ``(paths,
        commit_apply, guard copy)``, ``([], None, None)`` without a guard.

        plans/review-commits.md §2.7, "Every observed write, after each
        batch": the protected set's (and the context plan's) current disk
        ids against the ones read before the batch (``commit_apply.
        protected_violations``), on its own, so the check never depends on
        the undeclared-write sweep. That sweep is abandoned on a tree over
        ``SWEEP_MAX_FILES`` (a large repository) and keeps no bytes past
        ``SWEEP_RETAIN_MAX_BYTES``; this one costs only the watched set. The
        deny layer gains every watched path first, so ``policy.check`` names
        each hit with its rule."""
        guard = self.guard()
        if guard is None:
            return [], None, None
        commit_apply = _commit_write_guard.load_commit_apply()
        with self._effects_lock:
            # A co-scheduled sibling's re-check can grow the protected set.
            frozen = copy.deepcopy(guard)
            self.protect(guard)
        hits = commit_apply.protected_violations(
            frozen, cwd=self._ctx.repo_root,
            baseline=self.watch_before.get(task_id),
        )
        return [str(path) for path in hits or ()], commit_apply, frozen

    def restore_watched(
        self, task_id: str, report: Dict[str, str], commit_apply: Any,
        guard: Optional[Mapping[str, Any]],
    ) -> Dict[str, str]:
        """*report* (``TaskSnapshot.restore``'s) with each watched path the
        snapshot held no bytes for put back from what the guard kept
        (``commit_apply.restore_watched``: deleted when it was absent before
        the batch, else the guard's copy when that copy is what it held)."""
        if commit_apply is None or guard is None:
            return report
        missing = [
            path for path, state in report.items()
            if state == "skipped: not in this task's snapshot"
        ]
        if not missing:
            return report
        fallback = commit_apply.restore_watched(
            guard, missing, cwd=self._ctx.repo_root,
            baseline=self.watch_before.get(task_id),
        )
        return {**report, **fallback}

    def groups(self, task: Mapping[str, Any]) -> Dict[str, List[str]]:
        """``{group id: [fix files]}`` for *task* (:func:`commit_group_files`
        over its batch's fixes in this phase's ``orchestrator_output.json``,
        which the apply phase writes before the scheduler runs)."""
        if self.batches is None:
            self.batches = _commit_write_guard.load_orchestrator_batches(self._ctx.phase_dir) or []
        return _commit_write_guard.commit_group_files(
            task, repo_root=self._ctx.repo_root,
            fixes=_commit_write_guard.batch_fixes_for(task, self.batches),
        )

    def save_guard(self, commit_apply: Any, guard: Mapping[str, Any]) -> None:
        """Save *guard* back to ``state.json`` under ``state_file_lock``
        (``commit_apply.save_guard``). The guard is also this run's live
        dict, so the state's next ``save()`` writes the same decision; a
        failed save is named and the run goes on with it in memory."""
        path = getattr(self._ctx.state, "state_file", None)
        if not path:
            return
        try:
            commit_apply.save_guard(path, guard)
        except Exception as exc:  # noqa: BLE001 - the in-memory guard still holds
            self._ctx.log(
                f"[write-subagents] could not save the apply guard to {path}: "
                f"{exc}; it is saved with the next state write instead."
            )

    def recheck(
        self, task: Dict[str, Any], batch_index: int, result: Any,
    ) -> Optional[TaskOutcome]:
        """The pre-dispatch re-check of one batch, or ``None`` when it passes
        (or no guard exists).

        Every fix file the batch declares (each group's, not only the
        primary one) is checked against the identity the guard saved for it
        (``commit_apply.recheck_files``: ``head`` by git's three reads,
        ``batch`` by the bytes' sha256), and against the protected set. A
        batch that fails is not dispatched:

        * its groups that name a failing file are skipped with ``file changed
          since reviewed commit <head7>`` (``commit_apply.mark_stale``, which
          also adds the failing files to the protected set), the guard is
          saved back, and the deny layer gains the files before the next
          batch;
        * its other groups are held back: the batch is recorded ``failed``
          with ``held back: batched with <file>`` through
          :meth:`_refuse_before_dispatch`, which a ``--resume`` re-checks
          and re-batches without the skipped groups (a batch every group of
          which is skipped is recorded the same way, with the skip as its
          reason). Every item of the batch is ``failed`` in
          ``processed_<phase>``, which keeps it in a resume's work set; the
          guard's saved skips then take the skipped ones out again and count
          them (``commit_apply.take_guard``);
        * its batch line is the ``[COMMIT_FIXES_STALE]`` line, and the loop
          goes on to the next batch (:meth:`_run` does not stop on it).
        """
        guard = self.guard()
        if guard is None:
            return None
        commit_apply = _commit_write_guard.load_commit_apply()
        task_id = str(task.get("task_id", ""))
        groups = self.groups(task)
        # Under the bookkeeping lock throughout: a co-scheduled sibling's
        # completion re-pins (mutates) the same guard, and its `state.save()`
        # serializes it, both under this lock.
        with self._effects_lock:
            self.protect(guard)
            failing = _commit_write_guard.commit_recheck_failing(
                guard, groups, repo_root=self._ctx.repo_root, commit_apply=commit_apply,
            )
            if not failing:
                return None
            skipped, held = _commit_write_guard.commit_stale_split(groups, failing)
            commit_apply.mark_stale(guard, groups, failing, cwd=self._ctx.repo_root)
            self.save_guard(commit_apply, guard)
            self.protect(guard)
        line = _commit_write_guard.commit_stale_line(
            task_id, failing, guard,
            marker=getattr(commit_apply, "STALE_MARKER", "[COMMIT_FIXES_STALE]"),
        )
        tail = [f"{len(skipped)} fix(es) skipped"] if skipped else []
        if held:
            tail.append(
                f"{len(held)} held back, recorded failed (a --resume applies "
                f"{'it' if len(held) == 1 else 'them'} in a new batch)"
            )
        self.stale[task_id] = f"{line} — not dispatched: {', '.join(tail)}"
        return self._refused(
            task, _commit_write_guard.commit_stale_reason(failing, guard, held=bool(held)),
            batch_index, result,
        )

    def repin(self, task: Dict[str, Any], outcome: TaskOutcome) -> None:
        """Re-pin a completed batch's fix files to the bytes it left
        (``commit_apply.repin_after_batch``, from the ``sha256_after`` of its
        audit record), so a later batch on the same file, or a ``--resume``,
        accepts them by their ``batch`` identity, and a hand edit made after
        it fails. Only the batch's own fix files: a file another batch
        declares that moved during this one's window (an edit made while it
        ran) keeps its expectation, so its own batch is still re-checked
        against it. Caller holds ``_effects_lock``; no-op without a guard."""
        if not outcome.ok:
            return
        guard = self.guard()
        if guard is None:
            return
        own = {path for files in self.groups(task).values() for path in files}
        after = {
            str(path): digest for path, digest in (outcome.sha256_after or {}).items()
            if str(path) in own
        }
        if not after:
            return
        commit_apply = _commit_write_guard.load_commit_apply()
        if commit_apply.repin_after_batch(
            guard, str(task.get("task_id", "")), after, cwd=self._ctx.repo_root,
        ):
            self.save_guard(commit_apply, guard)

    def protected_unclassified(
        self, outcome: TaskOutcome, snapshot: TaskSnapshot
    ) -> None:
        """plans/review-commits.md §2.7 on a dispatch that never reached
        ``_classify`` (a timeout, a runner error, a reply that never parsed):
        each watched path its window changed (:meth:`watch_after`) is
        put back as ``_classify``'s policy branch puts it back, from the
        pre-batch snapshot or else from what the guard kept, and its reason
        names them. Its verdict stays its own: the loop stops on it either
        way. No-op without a guard."""
        watched, commit_apply, guard = self.watch_after(outcome.task_id)
        if not watched or guard is None:
            return
        report = self.restore_watched(
            outcome.task_id, snapshot.restore(watched), commit_apply, guard,
        )
        back = sorted(p for p, state in report.items() if not state.startswith("skipped:"))
        many = len(watched) != 1
        outcome.reason = (
            f"{outcome.reason or outcome.status} It also changed "
            f"{', '.join(watched)}, which the commit review protects (this apply "
            f"never writes {'them' if many else 'it'})."
            + (f" Put back as before the batch: {', '.join(back)}." if back else "")
            # No rollback point, or the restore's own reason: never one for the other.
            + PolicyRestore.from_report(report).not_restored()
        )
        self._ctx.audit.restored(task_id=outcome.task_id, report=report, force=False)
