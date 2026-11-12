"""The post-run containment sweep and its rollback store (D3l), for one write phase.

:class:`ContainmentSweep` is what makes the post-run write-policy check see what a
runner wrote **outside** what it declared. Before each dispatch it takes a census
of the tree under the pinned root, retains the bytes of every censused file in a
content-addressed rollback store, and registers the dispatch's declared set
(:meth:`ContainmentSweep.begin`). After it, it takes a second census and returns
the paths that moved outside any in-flight declared set, adopted into the task's
snapshot so they can be restored (:meth:`ContainmentSweep.undeclared_writes`,
which consumes the dispatch's census exactly once). A sibling running beside it
is accounted for: its declared paths are ignored, and a path both windows saw
move is ``shared`` (fix round 15). The audit line's rows for what it observed,
reversible or not, are built here too (:meth:`ContainmentSweep.observed_with_undeclared`).

Census registration and closing happen under the sweep's one lock, so a sibling
cannot start writing between a read and its removal. A path ``driver.write_paths``
denies is never copied into the store. ``WriteBatchScheduler`` composes one per
run with the run's ``RunContext``; the store's directory comes from
``write_safety.safety_dir`` at each copy
(docs/development/write-safety.md, docs/development/write-scheduler.md#where-the-schedulers-helpers-live).
"""

from __future__ import annotations

import hashlib
import os
import stat
import subprocess
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Collection, Dict, List, Optional, Sequence, Tuple

from . import git_utils as _git_utils
from . import prior_changes as _prior_changes
from . import write_context as _write_context
from .write_safety import (
    MAX_SNAPSHOT_BYTES,
    CopyNotContained,
    TaskSnapshot,
    WriteSafetyError,
    file_sha256,
    read_capped,
    write_copy,
    remove_tree,
    restore_leftovers,
)
from . import detach
from . import status_file

#: Directory *names* the post-run containment sweep never descends into. A VCS
#: metadata dir churns on anything the runner happens to run — ``git status``
#: alone rewrites ``.git/index`` — so attributing that churn to the batch would
#: stop the loop on a violation the runner never committed. They are denied by
#: ``driver.write_paths`` out of the box, which is where the *preventive* half
#: (the runner's own sandbox) applies; the sweep is the detective half and does
#: not guess at VCS internals.
SWEEP_PRUNED_DIR_NAMES = (".git", ".hg", ".svn")

#: Above this many regular files the sweep is abandoned rather than run: it
#: walks the tree twice per dispatch (three times when a reply says
#: ``applied`` and no declared file moved), and a control that silently doubles a
#: phase's wall clock is a control that gets switched off. The degradation is
#: announced once per run, never silent.
SWEEP_MAX_FILES = 60000

#: Where the sweep's rollback bytes live: ``{phase}/rollback_store/ab/<sha256>``,
#: content-addressed so a file that survives ten dispatches is stored once and a
#: reverted edit costs nothing. Under the phase dir like every other executor
#: artifact, which is also what keeps it out of the sweep's own census.
ROLLBACK_STORE_DIRNAME = "rollback_store"

#: The rollback store's byte budget for a whole run. Detection is cheap (a stat
#: per file); *reversibility* costs a read and a copy, so it is bounded and the
#: bound is announced. Past it the sweep still observes, checks and audits an
#: undeclared write — it just cannot undo it, which is the state every release
#: before this one was in for all of them.
SWEEP_RETAIN_MAX_BYTES = 64 * 1024 * 1024

#: The most undeclared paths one dispatch adopts into its snapshot. A runner that
#: ran a package install can touch tens of thousands of files, and a manifest
#: with one entry each helps nobody. Every observed path is still reported and
#: policy-checked; only the rollback points are capped.
SWEEP_ADOPT_MAX_FILES = 1000


@dataclass
class UndeclaredWrites:
    """What one dispatch's containment sweep saw outside the declared set.

    Two lists rather than one, because "observed" and "reversible" are different
    facts about the same path and collapsing them is how a rollback point that
    does not exist gets promised. ``paths`` is the whole observed set — it is what
    the post-run ``WritePolicy`` check runs on and what the audit records.
    ``restorable`` is the subset whose pre-run bytes (or recorded absence) made it
    into the task's snapshot, and therefore the only part that may join
    ``files_touched``, which is what ``util restore-batch`` reverts.
    """

    paths: List[str] = field(default_factory=list)
    restorable: List[str] = field(default_factory=list)
    #: Whether a census was taken on BOTH sides of the dispatch. ``False`` is
    #: "the sweep could not look", which is not the same fact as an empty
    #: ``paths`` (adversarial review, 2026-10-02: a verification-only task
    #: read the sweep-off case as "no file changed" and was VERIFIED).
    observed: bool = True
    #: Fix round 15: the subset of ``paths`` a task running at the same time
    #: also saw move (``task_id -> paths``), so the sweep cannot say whose
    #: change each is. Still observed, policy-checked and restorable; never
    #: counted as this task's own change when its declared files did not move.
    shared: Dict[str, List[str]] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return bool(self.paths)

    @property
    def own(self) -> List[str]:
        """``paths`` minus every path a sibling's window also saw move."""
        seen = {path for paths in self.shared.values() for path in paths}
        return [path for path in self.paths if path not in seen]

    def __len__(self) -> int:
        return len(self.paths)

    @property
    def unrecoverable(self) -> List[str]:
        keepable = set(self.restorable)
        return [path for path in self.paths if path not in keepable]


class ContainmentSweep:
    """One run's containment sweep: censuses, retained bytes and the in-flight sets.

    Its state is its own and lives under its lock (``_sweep_lock``); the
    scheduler reaches it only through the methods below.
    """

    def __init__(self, ctx: _write_context.RunContext) -> None:
        self._ctx = ctx
        #: The sweep's own state: the pre-dispatch census
        #: per in-flight task, and each in-flight task's OWN declared set —
        #: added on dispatch (`begin`), removed on classification
        #: (`undeclared_writes`). A co-scheduled sibling writes its OWN
        #: declared files while this task is being classified, so those paths
        #: are subtracted before the sweep's result reaches the policy —
        #: otherwise a disjoint group would report each other's legitimate
        #: writes as undeclared. F13: this used to be one set unioned for the
        #: whole PHASE and never pruned, so once any task declared a path, a
        #: LATER task's undeclared write to that same path was invisible for
        #: the rest of the run — the justification above only ever needed the
        #: in-flight sets.
        self._sweep_lock = threading.Lock()
        self._census_before: Dict[str, Optional[Dict[str, Tuple[int, int]]]] = {}
        self._declared_by_task: Dict[str, set] = {}
        # Each census spans the whole dispatch, so a sibling's legitimate
        # writes remain attributable to that sibling even if it finishes first.
        # Keep overlap declarations per census, never for the entire phase.
        self._sweep_ignored: Dict[str, set] = {}
        #: Fix round 15: ``task_id -> ids of the tasks whose dispatch window
        #: overlapped this one's`` (registered in `begin`), and, for a
        #: finished task such a sibling is still running beside, its window
        #: — ``(census before, census after, retained digests)``. A path a
        #: sibling's window also saw move cannot be told apart from that
        #: sibling's stray write, so it never makes a code task applied
        #: (`UndeclaredWrites.shared`).
        self._sweep_overlap: Dict[str, set] = {}
        self._finished_windows: Dict[str, Tuple[Dict[str, Tuple[int, int]],
                                                Dict[str, Tuple[int, int]],
                                                Dict[str, str]]] = {}
        self._sweep_warned = False
        #: The ignore rules in force when each in-flight dispatch started:
        #: ``source path -> sha256 | None (absent)`` over every `.gitignore`
        #: the census saw, `.git/info/exclude`, `.git/config` and the global
        #: excludes file. `_ignored_and_harmless` drops a path from the sweep
        #: only while these are what they were at dispatch — the runner can
        #: write any of them, and a drop decided on post-run rules hid
        #: everything a runner-written `*` covered (adversarial review,
        #: 2026-10-02).
        self._ignore_sources_before: Dict[str, Dict[str, Optional[str]]] = {}
        self._global_excludes_path: Optional[str] = None
        self._global_excludes_resolved = False
        #: The rollback half of the same sweep. Observing an undeclared write is
        #: worth little if it cannot be undone, and the snapshot only ever held
        #: the declared set, so the pre-run bytes of everything else the runner
        #: could reach are retained here before dispatch:
        #: `_retained` is the run-wide `relative -> (stamp, digest|None)` cache
        #: that keeps a file from being re-hashed while its (size, mtime_ns) is
        #: unchanged, `_retained_before` is the per-in-flight-task view a sibling
        #: dispatch cannot overwrite, and `_retained_bytes` accounts the store
        #: against `SWEEP_RETAIN_MAX_BYTES`. `_counted_digests` is what keeps
        #: that accounting honest across an inherited store (F12): a blob
        #: already on disk — this run's own earlier copy, or one a killed run
        #: left behind — costs real bytes on disk whether or not `_store_blob`
        #: copies anything this call, so each digest is counted once, on
        #: whichever call finds it first, rather than only on the call that
        #: wrote it.
        self._retained: Dict[str, Tuple[Tuple[int, int], Optional[str]]] = {}
        self._retained_before: Dict[str, Dict[str, str]] = {}
        self._retained_bytes = 0
        self._counted_digests: set = set()
        self._retain_warned = False
        #: ``relative -> denied by driver.write_paths?`` for every path the
        #: sweep kept no bytes for (the policy does not change during a run,
        #: so each path is asked once). The denied ones are named once, on the
        #: closing utilisation line, rather than in a warning of their own
        #: (see :meth:`_retain`).
        self._unretained_denied: Dict[str, bool] = {}
        #: ``relative -> path`` for each file whose copy the retention pass
        #: refused and could not clean up (:meth:`_report_copy_left`), and
        #: the paths already counted against the budget.
        self._copies_left: Dict[str, str] = {}
        self._copies_left_counted: set = set()
        #: ``task_id -> dispatched_at`` (ISO, `begin`'s own clock) for a
        #: dispatch that has started and not yet been classified (F10) — what
        #: lets the mirror report "in flight since Ns" through a batch that
        #: runs for minutes instead of reading `dispatched: 0` the whole time,
        #: indistinguishable from a stall. Popped in step with
        #: `_declared_by_task`/`_census_before` in `undeclared_writes`, so a
        #: task that never reaches classification (an exception raised before
        #: `_classify`) is the one case this can go stale — the run's next
        #: mirror write self-heals it, or the process is gone and the
        #: heartbeat says so.
        self._dispatch_started: Dict[str, str] = {}

    def abandon(self, task_id: str) -> None:
        """Drop *task_id*'s census, retained-byte index and in-flight entry, for
        a dispatch that neither classification nor the terminal audit closed
        (it raised out, or was refused before its runner started)."""
        with self._sweep_lock:
            self._census_before.pop(task_id, None)
            self._retained_before.pop(task_id, None)
            self._dispatch_started.pop(task_id, None)
            self._declared_by_task.pop(task_id, None)
            self._sweep_ignored.pop(task_id, None)
            self._ignore_sources_before.pop(task_id, None)
            self._sweep_overlap.pop(task_id, None)

    def has_census(self, task_id: str) -> bool:
        """Whether *task_id*'s pre-run census was taken and is still open."""
        with self._sweep_lock:
            return self._census_before.get(task_id) is not None

    def in_flight(self) -> List[Tuple[str, str]]:
        """``(task_id, dispatched_at)`` for each dispatch begun and not yet
        classified, sorted."""
        with self._sweep_lock:
            return sorted(self._dispatch_started.items())

    def clear_in_flight(self) -> None:
        """Forget every in-flight entry (a refusal ended the run)."""
        with self._sweep_lock:
            self._dispatch_started.clear()

    def report_store_utilization(self) -> None:
        """One line naming how much of the reversibility budget this run used.

        The sweep is deliberately generous (F15) — anything under the pinned
        root the run could have touched, not just the phase's declared set,
        because narrowing it would make its *detective* half (catching an
        undeclared write outside that set) vacuous — so on a large enough repo
        it can spend a real share of ``SWEEP_RETAIN_MAX_BYTES`` on files the
        phase never intended to touch. Until now the only visible signal was
        the warning in :meth:`_retain` for the files *already* denied a
        rollback point; this prints once the run is done retaining, so the
        trend toward that budget is visible before it happens rather than
        only once it already has. Skipped when nothing was ever censused
        (``--dry-run-subagents``, or a run that dispatched no batch).
        """
        if not self._retained:
            return
        digests = {digest for _stamp, digest in self._retained.values() if digest}
        shards = {digest[:2] for digest in digests}
        # The files the deny list kept out, named here once rather than in a
        # warning at the start of every write phase (see `_retain`).
        denied = sorted(
            path for path, is_denied in self._unretained_denied.items() if is_denied)
        kept_out = (
            f"; never copied, as driver.write_paths denies "
            f"{'it' if len(denied) == 1 else 'them'} (a write to "
            f"{'it' if len(denied) == 1 else 'one'} fails the batch and "
            f"cannot be undone): {', '.join(denied[:5])}"
            f"{f', … {len(denied) - 5} more' if len(denied) > 5 else ''}"
            if denied else ""
        )
        # The snapshot directory named in full: a jailed repo-wide batch keeps
        # its snapshots under the state home, not the phase dir (Codex racing
        # run 4: "restore points live in pre_batch/" read as the phase dir's
        # copy, which the line before says is never read).
        self._ctx.log(
            f"[write-subagents] rollback store peaked at "
            f"{self._retained_bytes / (1024 * 1024):.1f} MB of the "
            f"{SWEEP_RETAIN_MAX_BYTES // (1024 * 1024)} MB budget "
            f"({len(digests)} files, {len(shards)} shards{kept_out}); discarded now "
            f"— the restore points are the pre-batch snapshots in "
            f"{os.path.join(self._ctx.safety_dir, 'pre_batch')}/"
        )

    def discard_store(self) -> None:
        """Drop the sweep's staging bytes and the index that describes them.

        Each entry is removed itself, never what a link there leads to
        (``write_safety.remove_tree``). One whose removal is refused (on
        Windows a read-only blob: ``CopyFile2`` keeps the attribute) is never
        tried again and stays in the store, which costs disk space alone: a
        blob becomes a rollback point only once its bytes hash to its name
        (``TaskSnapshot.adopt``), as a killed run's leftover store does. What
        is left is named in a warning, never left silently
        (docs/development/write-safety.md, the store's discard).
        """

        store = os.path.join(self._ctx.safety_dir, ROLLBACK_STORE_DIRNAME)
        left = remove_tree(store)
        if left:
            shown = "; ".join(left[:5])
            more = f"; … {len(left) - 5} more" if len(left) > 5 else ""
            self._ctx.log(
                f"[write-subagents] WARNING: the rollback store {store} could not "
                f"be removed whole: {shown}{more}. It was not tried again; left "
                f"there it costs disk space only. It holds the retention pass's "
                f"copies of files under {self._ctx.repo_root}, or a copy it refused, "
                f"which can hold another file's bytes: check it and delete it by "
                f"hand."
            )
        with self._sweep_lock:
            self._retained.clear()
            self._retained_bytes = 0

    def begin(
        self, task_id: str, declared: Sequence[str], *,
        verification_only: bool = False,
    ) -> None:
        """Take this dispatch's pre-run census, retain its bytes, register its set.

        The census is what makes the post-run policy check non-vacuous; the
        retention pass is what makes its verdict *actionable*. Both happen before
        the runner starts, because neither can be reconstructed afterwards.

        Raises :class:`WriteSafetyError` for a ``verification_only`` task when
        the census is unusable. Every other task still has its declared set to
        compare; this one has nothing but the sweep, and "the sweep could not
        look" read as "nothing moved" (adversarial review, 2026-10-02: with
        the tree over ``SWEEP_MAX_FILES`` — an untracked ``node_modules/`` is
        enough — a file-less task edited ``index.html`` and was VERIFIED at
        exit 0). Never VERIFIED without a census.
        """
        dispatched_at = datetime.now().isoformat()
        with self._sweep_lock:
            census = self.census()
            if census is None and verification_only:
                raise WriteSafetyError(
                    f"Refusing to dispatch write task {task_id}: it declares no "
                    f"files, so the post-run containment sweep would be its "
                    f"whole verdict, and the tree under {self._ctx.repo_root} holds "
                    f"more than {SWEEP_MAX_FILES} files, which turns the sweep "
                    f"off (D3l). A verification-only task cannot be verified "
                    f"here. List the files it may change under `Files to "
                    f"modify` in the tasks file and re-run with --resume, or "
                    f"take the untracked trees (node_modules/, build output) "
                    f"out of the checkout. Nothing was dispatched."
                )
            # Fix round 15: every dispatch still in flight overlaps this one.
            running = set(self._declared_by_task) - {task_id}
            self._sweep_overlap[task_id] = set(running)
            for other in running:
                self._sweep_overlap.setdefault(other, set()).add(task_id)
            self._census_before[task_id] = census
            self._retained_before[task_id] = self.retain(census)
            self._ignore_sources_before[task_id] = self._ignore_rule_sources(census)
            self._declared_by_task[task_id] = set(declared)
            for ignored in self._sweep_ignored.values():
                ignored.update(declared)
            self._sweep_ignored[task_id] = set().union(
                *self._declared_by_task.values()
            )
            self._dispatch_started[task_id] = dispatched_at
            if census is None and not self._sweep_warned:
                self._sweep_warned = True
                self._ctx.log(
                    f"[write-subagents] the tree under {self._ctx.repo_root} holds more "
                    f"than {SWEEP_MAX_FILES} files — the post-run containment sweep "
                    f"is skipped for this run and driver.write_paths is enforced "
                    f"against the declared set only (D3l)."
                )

    def exclusions(self) -> Tuple[str, ...]:
        """Absolute paths the sweep must never attribute to the runner.

        The phase dir is the *executor's* own artifact tree (results, snapshots,
        the audit log, ``.status.json``), and the two output-dir bookkeeping
        files are written by :meth:`_record_batch_effects` — for a co-scheduled
        sibling, while this task is being classified. The detached-run registry
        is the same story one level up: ``status --sweep`` or a second run's
        claim can rewrite it at any moment. Every one of them would otherwise
        read as an undeclared write, and ``.multi-llm/**`` is denied by default,
        so the sweep would fail batches on the tool's own bookkeeping. Only the
        ``runs/`` subtree is excluded, never all of ``.multi-llm/`` — a runner
        rewriting ``.multi-llm/providers.yaml`` is exactly what the deny rule is
        for and stays observable.
        """
        excluded = [
            os.path.abspath(self._ctx.phase_dir),
            os.path.abspath(os.path.join(self._ctx.output_dir, _prior_changes.FILENAME)),
            os.path.abspath(os.path.join(self._ctx.repo_root, ".multi-llm", "runs")),
        ]
        state_file = getattr(self._ctx.state, "state_file", None)
        if state_file:
            excluded.append(os.path.abspath(str(state_file)))
        if self._ctx.summary_file:
            excluded.append(os.path.abspath(self._ctx.summary_file))
        # A detached composite (full/improve-*) owns a different phase dir.
        # Its heartbeat and redirected stdout continue while this write batch
        # runs, including during report-only re-asks. Exempt just those runtime
        # files, not the composite's whole tree or unrelated phase artifacts.
        active = detach.active_run()
        if active is not None:
            excluded.extend(os.path.abspath(path) for path in (
                status_file.status_path(active.phase_dir),
                status_file.status_lock_path(active.phase_dir),
                detach.log_path(active.phase_dir),
            ))
        return tuple(excluded)

    def census(
        self, kept: Optional["set[str]"] = None,
    ) -> Optional[Dict[str, Tuple[int, int]]]:
        """``repo-relative -> (size, mtime_ns)`` for every file under the root.

        ``None`` means *not usable* — the tree is over :data:`SWEEP_MAX_FILES` —
        and a ``None`` on either side of the comparison makes the sweep a no-op
        rather than a guess. The walk starts at the pinned root (``realpath``'d)
        and follows no link, so every entry's path is that root, a separator and
        its relative path, already normalized: the relative path is sliced off,
        and an entry is excluded when it is an excluded path or lies beneath
        one, separator-aware (a bare ``startswith`` would also swallow a
        sibling whose name only shares the prefix, ``plans-old/`` beside
        ``plans/``). A per-file ``Path.resolve()`` (``relative_to_root``) would
        put syscalls on every entry of a tree this size.

        A staged file a rollback restore kept for the user is left out too,
        exactly that file at its path (``write_safety.restore_leftovers``):
        never adopted, deleted or attributed to a batch; a file of the same
        name that is not that file is censused as any other. Its relative
        path goes into ``kept`` when given, for :meth:`_swept_moves` to leave
        out of both sides of the difference.
        """

        leftovers = restore_leftovers(self._ctx.repo_root)
        excluded = self.exclusions()
        excluded_paths = frozenset(excluded)
        excluded_trees = tuple(path + os.sep for path in excluded)
        root = self._ctx.repo_root
        prefix = len(root if root.endswith(os.sep) else root + os.sep)
        census: Dict[str, Tuple[int, int]] = {}
        stack = [root]
        while stack:
            try:
                entries = list(os.scandir(stack.pop()))
            except OSError:
                continue
            for entry in entries:
                path = entry.path
                if path in excluded_paths or path.startswith(excluded_trees):
                    continue
                if leftovers and leftovers.holds(path):
                    if kept is not None:
                        kept.add(path[prefix:].replace(os.sep, "/"))
                    continue
                try:
                    if entry.is_dir(follow_symlinks=False):
                        if entry.name not in SWEEP_PRUNED_DIR_NAMES:
                            stack.append(entry.path)
                        continue
                    if not entry.is_file(follow_symlinks=False):
                        continue
                    info = entry.stat(follow_symlinks=False)
                except OSError:
                    continue
                census[path[prefix:].replace(os.sep, "/")] = (
                    info.st_size, info.st_mtime_ns
                )
                if len(census) > SWEEP_MAX_FILES:
                    return None
        return census

    def blob_path(self, digest: str) -> str:
        """Where the rollback store keeps ``digest``'s bytes."""
        return os.path.join(
            self._ctx.safety_dir, ROLLBACK_STORE_DIRNAME, digest[:2], digest
        )

    def retain(self, census: Optional[Dict[str, Tuple[int, int]]]) -> Dict[str, str]:
        """Copy every censused file's current bytes into the rollback store.

        ``relative -> sha256`` for what was retained. Three exclusions, each for
        a reason the alternative makes worse:

        * **A path ``driver.write_paths`` denies** (``.env``, ``**/*.pem``,
          ``**/.ssh/**``) is never copied. The deny list exists precisely to keep
          that material out of executor-owned artifacts — it is why the
          pre-dispatch policy check runs *before* the snapshot
          (``write_snapshots.PreBatchSnapshots.take``) — and a rollback
          store that quietly mirrors every secret in the repo into the phase dir
          would be a new vulnerability rather than a control. Such a write is
          still observed, still fails the post-run check and still stops the loop;
          it just gets no automatic undo.
        * **A file over ``MAX_SNAPSHOT_BYTES``**, the same per-file cap a declared
          snapshot refuses to dispatch over.
        * **Anything past ``SWEEP_RETAIN_MAX_BYTES``**, so insurance cannot cost
          more than the run.

        The ``(size, mtime_ns)`` cache is what keeps this from being a full-tree
        read per dispatch: only a file whose stamp moved since the last dispatch
        is hashed again, and the store is content-addressed, so re-storing a
        reverted edit is a no-op.
        """
        if census is None:
            return {}
        kept: Dict[str, str] = {}
        skipped: List[str] = []
        for relative, stamp in sorted(census.items()):
            cached = self._retained.get(relative)
            if cached is None or cached[0] != stamp:
                cached = (stamp, self.store_blob(relative, stamp))
                self._retained[relative] = cached
            if cached[1]:
                kept[relative] = cached[1]
            else:
                skipped.append(relative)
        # A path the deny list keeps out is out by design, and a write to it
        # fails the batch (the post-run policy check) whose reason says it
        # could not be restored. Announced up front it was the same line on
        # every write phase of a run (Codex racing run 4: `.multi-llm/
        # providers.yaml` four times), so it is named once, on the closing
        # utilisation line, and the warning keeps the gaps that are not by
        # design: a file over the per-file cap or past the budget.
        for path in skipped:
            if path not in self._unretained_denied:
                self._unretained_denied[path] = self._ctx.policy.violation(
                    os.path.join(self._ctx.repo_root, path), exact=False) is not None
        skipped = [path for path in skipped if not self._unretained_denied[path]]
        if skipped and not self._retain_warned:
            self._retain_warned = True
            # Named, with the reason each one was skipped: a count alone
            # ("3 file(s) … have no rollback point") left the reader guessing
            # which files and whether that was a problem (measured 2026-09-16:
            # it was the three under `.multi-llm/`, which the deny list keeps
            # out of executor artifacts by design).
            named = ", ".join(
                f"{path} ({self._skip_reason(path)})" for path in skipped[:5]
            ) + (f", … {len(skipped) - 5} more" if len(skipped) > 5 else "")
            self._ctx.log(
                f"[write-subagents] {len(skipped)} file(s) under {self._ctx.repo_root} "
                f"have no rollback point in "
                f"{os.path.join(self._ctx.safety_dir, ROLLBACK_STORE_DIRNAME)}: {named}. "
                f"An undeclared write to one of them is still detected, "
                f"policy-checked and audited — `util restore-batch` just cannot "
                f"undo it (D3l)."
            )
        return kept

    def _skip_reason(self, relative: str) -> str:
        """Why :meth:`_store_blob` kept no bytes for ``relative``."""
        if relative in self._copies_left:
            return f"its refused copy is left at {self._copies_left[relative]}"
        absolute = os.path.join(self._ctx.repo_root, relative)
        if self._ctx.policy.violation(absolute, exact=False) is not None:
            return "denied by driver.write_paths"
        try:
            size = os.stat(absolute).st_size
        except OSError:
            return "unreadable"
        if size > MAX_SNAPSHOT_BYTES:
            return f"over the {MAX_SNAPSHOT_BYTES}-byte per-file cap"
        if self._retained_bytes + size > SWEEP_RETAIN_MAX_BYTES:
            return f"past the {SWEEP_RETAIN_MAX_BYTES}-byte store budget"
        return "unreadable"

    def store_blob(
        self, relative: str, stamp: Tuple[int, int]
    ) -> Optional[str]:
        """Put one file's bytes in the store, or ``None`` when it is not retained.

        The file is read once, through the descriptor the policy was asked
        about, so the bytes stored are the bytes hashed and never bytes from
        wherever a link swapped in since leads; Windows' ``CopyFile2`` copy is
        checked against them (docs/development/write-safety.md, the rollback
        store's reads).
        """
        size = stamp[0]
        if size > MAX_SNAPSHOT_BYTES:
            return None
        absolute = os.path.join(self._ctx.repo_root, relative)
        # `driver.write_paths` alone (`exact=False`): the commit review's
        # protected files (plans/review-commits.md §2.7) are ordinary code,
        # and their retained bytes are what the post-run check restores them
        # from when a batch writes one. Resolved for each file, as the
        # store's location is read for each copy (`_blob_path`): a link or a
        # phase path swapped mid-pass is refused at the next file, never
        # trusted from an earlier look (docs/development/write-safety.md).
        if self._ctx.policy.violation(absolute, exact=False) is not None:
            return None
        opened = self._ctx.policy.open_permitted(absolute)
        if opened is None:
            return None
        source, info = opened
        try:
            return self._store_opened(source, info, relative, absolute)
        finally:
            os.close(source)

    def _store_opened(
        self, source: int, info: os.stat_result, relative: str, absolute: str
    ) -> Optional[str]:
        """:meth:`_store_blob` for the file open as *source* (``fstat`` *info*),
        opened by the name *absolute*."""
        try:
            data = read_capped(source, MAX_SNAPSHOT_BYTES, size_hint=info.st_size)
        except OSError:
            return None
        if data is None:
            return None
        size = len(data)
        digest = hashlib.sha256(data).hexdigest()
        blob = self.blob_path(digest)
        if os.path.isfile(blob):
            # F12: the blob may be this run's own earlier copy (a second
            # `relative` with identical content) or one a killed run's store
            # left behind — either way its bytes are already on disk, and the
            # budget/utilisation line are both about bytes on disk, not bytes
            # THIS call copied. Returning here without counting is the bug: a
            # run that inherited a 47 MB store from a killed predecessor
            # reported "0.1 MB of 64 MB retained" and the cap went unenforced
            # for the rest of the run. Content-addressed, so it is counted
            # once per digest no matter how many relative paths reach it.
            if digest not in self._counted_digests:
                self._counted_digests.add(digest)
                self._retained_bytes += size
            return digest
        if self._retained_bytes + size > SWEEP_RETAIN_MAX_BYTES:
            return None
        try:
            os.makedirs(os.path.dirname(blob), exist_ok=True)
            # Same temp-then-replace shape every other executor write uses, so a
            # crash mid-copy can never leave a truncated blob that a later
            # restore would write over a good file.
            pending = f"{blob}.{os.getpid()}.{threading.get_ident()}.tmp"
            write_copy(pending, data, source, path=absolute)
            os.replace(pending, blob)
        except CopyNotContained as left:
            self._report_copy_left(relative, left)
            return None
        except OSError:
            return None
        self._counted_digests.add(digest)
        self._retained_bytes += size
        return digest

    def _report_copy_left(self, relative: str, left: CopyNotContained) -> None:
        """Say, every time, that the store could not clean up after a copy
        of ``relative`` it refused, and count what is left against the budget.

        A refused copy is refused because it may hold bytes other than the
        file's, another file's from outside the repository included, so one
        left behind is named for the user to check and delete, never dropped
        like an ordinary failed copy (docs/development/write-safety.md, the
        rollback store's reads).
        """
        self._copies_left[relative] = left.pending
        if left.pending not in self._copies_left_counted:
            self._copies_left_counted.add(left.pending)
            try:
                named = os.lstat(left.pending)
            except OSError:
                named = None
            if named is not None and stat.S_ISREG(named.st_mode):
                self._retained_bytes += named.st_size
        self._ctx.log(
            f"[write-subagents] WARNING: {relative} has no rollback point: {left}. "
            f"A copy the rollback store refused can hold another file's bytes, "
            f"one from outside {self._ctx.repo_root} included: check what is left "
            f"there and delete it by hand."
        )

    def undeclared_writes(
        self, task_id: str, snapshot: TaskSnapshot
    ) -> UndeclaredWrites:
        """Paths this dispatch moved *outside* any declared set, made reversible.

        This is what makes the post-run policy check non-vacuous.
        ``snapshot.changed()`` can only ever report files the task declared —
        ``write_phase_bridge`` leaves ``snapshot_files`` equal to
        ``declared_files`` — and that exact list already passed the identical
        ``policy.check(..., when="pre-dispatch")``, so enforcing the policy on it
        alone can never raise. A runner is nevertheless free to write anywhere
        its own sandbox allows (the claude-code write profile permits ``Bash``),
        and "it wrote outside what it declared" is precisely the containment
        failure D3l's detective layer exists to observe.

        Observing it is only half the control, so each observed path is adopted
        into this task's snapshot — the retained pre-run bytes for a file that
        existed, the recorded absence for one the runner created — which is what
        lets ``_classify``'s policy-violation branch really restore it and
        ``util restore-batch`` revert it later. A path with no retained bytes
        (denied, oversized, past the budget, or unreadable before the run) stays
        out of ``restorable`` and therefore out of ``files_touched``: promising a
        rollback point that does not exist is the failure this method's caller
        would otherwise ship.

        Deletions count: a declared-set-external file that disappeared was
        touched just as surely as one that grew.
        """
        with self._sweep_lock:
            before = self._census_before.pop(task_id, None)
            retained = self._retained_before.pop(task_id, None) or {}
            sources = self._ignore_sources_before.pop(task_id, None) or {}
            # Include every sibling that overlapped this census, even one
            # already classified. Its edits are still in the before/after
            # difference and must never enter this task's rollback snapshot.
            ignored = self._sweep_ignored.pop(task_id, set())
            # Registering a new census and closing this one share the lock,
            # so a sibling cannot start writing between this read and removal
            # from the overlap bookkeeping.
            kept: "set[str]" = set()
            after = self.census(kept) if before is not None else None
            self._declared_by_task.pop(task_id, None)
            self._dispatch_started.pop(task_id, None)
            # Fix round 15: the windows of the siblings that overlapped this
            # one — a finished one's as it closed, a running one's from its
            # census to now — and this window kept for any still running.
            siblings = self._sweep_overlap.pop(task_id, set())
            windows: Dict[str, Tuple[Dict[str, Tuple[int, int]],
                                     Optional[Dict[str, Tuple[int, int]]],
                                     Dict[str, str]]] = {}
            for sibling in sorted(siblings):
                if sibling in self._finished_windows:
                    windows[sibling] = self._finished_windows[sibling]
                elif self._census_before.get(sibling) is not None:
                    windows[sibling] = (
                        self._census_before[sibling], None,
                        dict(self._retained_before.get(sibling) or {}),
                    )
            if (before is not None and after is not None
                    and siblings & set(self._declared_by_task)):
                self._finished_windows[task_id] = (before, after, dict(retained))
            referenced = set().union(*self._sweep_overlap.values()) \
                if self._sweep_overlap else set()
            for finished in list(self._finished_windows):
                if finished not in referenced:
                    del self._finished_windows[finished]
        if before is None:
            return UndeclaredWrites(observed=False)
        if after is None:
            # The tree grew past the cap DURING the run (an `npm install`):
            # not "nothing moved", the sweep could not look (W1).
            return UndeclaredWrites(observed=False)
        moved = self._swept_moves(before, after, ignored, retained, kept)
        moved -= self._ignored_and_harmless(task_id, moved, sources, after)
        observed = UndeclaredWrites(paths=sorted(moved))
        for sibling, (sib_before, sib_after, sib_retained) in windows.items():
            seen = [
                path for path in observed.paths
                if self._moved_in_window(
                    path, sib_before, sib_after if sib_after is not None else after,
                    sib_retained,
                )
            ]
            if seen:
                observed.shared[sibling] = seen
        adopted = 0
        for relative in observed.paths:
            if adopted >= SWEEP_ADOPT_MAX_FILES:
                break
            stamp = before.get(relative)
            digest = retained.get(relative)
            try:
                entry = snapshot.adopt(
                    relative,
                    existed=stamp is not None,
                    sha256=digest,
                    size=stamp[0] if stamp else 0,
                    payload_source=self.blob_path(digest) if digest else None,
                    save=False,
                )
            except (WriteSafetyError, OSError):
                entry = None
            if entry is not None:
                observed.restorable.append(relative)
                adopted += 1
        if adopted:
            snapshot.save()
        return observed

    def _moved_in_window(
        self,
        relative: str,
        before: Dict[str, Tuple[int, int]],
        after: Dict[str, Tuple[int, int]],
        retained: Dict[str, str],
    ) -> bool:
        """Whether *relative* moved between one window's two censuses, by the
        rule :meth:`_swept_moves` applies: the stamps say where to look, the
        bytes decide (fix round 15, a sibling's window)."""
        previous = before.get(relative)
        current = after.get(relative)
        if previous == current:
            return False
        digest = retained.get(relative) if previous is not None else None
        if digest and current is not None and file_sha256(
            os.path.join(self._ctx.repo_root, relative)
        ) == digest:
            return False
        return True

    def _swept_moves(
        self,
        before: Dict[str, Tuple[int, int]],
        after: Dict[str, Tuple[int, int]],
        ignored: "set[str]",
        retained: Dict[str, str],
        kept: Collection[str] = (),
    ) -> "set[str]":
        """The paths outside ``ignored`` whose BYTES moved between two censuses.

        The stamps say which files to look at; the bytes decide. A path whose
        ``(size, mtime_ns)`` moved but whose content hashes to the digest the
        retention pass stored is not a write: a formatter no-op, a ``touch``,
        or a checkout of an unchanged file read as a partial application and
        stopped the loop (adversarial review, 2026-10-02; the declared set was
        already judged by sha256 in ``TaskSnapshot.changed``, so this is the
        same rule on the undeclared side). A path with no retained digest —
        denied, oversized, past the budget — stays moved: no bytes to compare
        is no reason to look away.

        ``kept`` holds the staged files a rollback restore kept for the user
        that the final census found (:meth:`_census`), left out on both
        sides: one the first census saw before the restore recorded it is
        neither a new file nor a deletion of the batch's
        (docs/development/write-safety.md, restore).
        """
        moved: set = set()
        for relative, stamp in after.items():
            if relative in ignored or relative in kept:
                continue
            previous = before.get(relative)
            if previous == stamp:
                continue
            digest = retained.get(relative) if previous is not None else None
            if digest and file_sha256(
                os.path.join(self._ctx.repo_root, relative)
            ) == digest:
                continue
            moved.add(relative)
        moved.update(
            relative for relative in before
            if relative not in after and relative not in ignored
            and relative not in kept
        )
        return moved

    def _ignore_rule_sources(
        self, census: Optional[Dict[str, Tuple[int, int]]]
    ) -> Dict[str, Optional[str]]:
        """``source -> sha256 | None`` for every file that decides what git ignores.

        Every ``.gitignore`` the census saw (repo-relative), plus the three
        sources the census never covers: ``.git/info/exclude`` and
        ``.git/config`` (``.git`` is pruned from the walk) and the global
        excludes file (outside the repo). ``None`` records an absent file, so
        a source the runner *creates* reads as moved too. Hashed, not stamped,
        because a stamp is what a runner can put back.
        """
        if census is None:
            return {}
        sources = [
            relative for relative in census
            if relative == ".gitignore" or relative.endswith("/.gitignore")
        ]
        sources += [".git/info/exclude", ".git/config"]
        global_excludes = self._global_excludes()
        if global_excludes:
            sources.append(global_excludes)
        out: Dict[str, Optional[str]] = {}
        for source in sources:
            absolute = (
                source if os.path.isabs(source)
                else os.path.join(self._ctx.repo_root, source)
            )
            out[source] = file_sha256(absolute) if os.path.isfile(absolute) else None
        return out

    def _global_excludes(self) -> Optional[str]:
        """The absolute path of ``core.excludesFile``, resolved once per run."""
        if self._global_excludes_resolved:
            return self._global_excludes_path
        self._global_excludes_resolved = True
        path = ""
        try:
            result = subprocess.run(
                _git_utils.git_argv(
                    "config", "--path", "--get", "core.excludesFile", cwd=self._ctx.repo_root,
                ),
                cwd=self._ctx.repo_root, capture_output=True, text=True,
                encoding="utf-8", errors="replace",
            )
            if result.returncode == 0:
                path = result.stdout.strip()
        except OSError:
            path = ""
        if not path:
            config_home = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
                os.path.expanduser("~"), ".config"
            )
            path = os.path.join(config_home, "git", "ignore")
        self._global_excludes_path = os.path.abspath(path) if path else None
        return self._global_excludes_path

    def _ignored_and_harmless(
        self,
        task_id: str,
        moved: "set[str]",
        sources_before: Dict[str, Optional[str]],
        after: Optional[Dict[str, Tuple[int, int]]],
    ) -> "set[str]":
        """The moved paths git ignored *at dispatch* and the policy does not deny.

        A gitignored path is not part of the repository's change set: the host's
        own transcript (``logs/*.jsonl``), build output and caches moved during a
        dispatch were read as "changed outside this task's declared set", were
        handed to ``finalize-tracking`` as touched implementation files and from
        there became ``review-code``'s scope (2026-10-02, Codex run). They leave
        the sweep, with two exceptions:

        * a path ``driver.write_paths`` **denies** stays observable even when
          ignored, because the deny list's usual subjects (``.env``,
          ``**/*.pem``) are exactly what ``.gitignore`` hides, and dropping them
          would make the post-run policy check vacuous again. The deny side
          alone (:meth:`WritePolicy.denied`): asking :meth:`violation` also
          failed every ignored path a narrow ``allow`` did not list, which is
          how the fix only ever applied under ``allow: ["**"]`` (adversarial
          review, 2026-10-02);
        * **nothing** is dropped when the ignore rules themselves moved during
          the run. ``git check-ignore`` runs after the run, on rules the runner
          can write — a new ``.gitignore`` holding ``*``, or ``.git/info/exclude``
          (pruned from the census, so never "moved") — and read that way the
          drop hid every file the runner created, and its rule file with them
          (adversarial review, 2026-10-02). The rules in force at dispatch are
          hashed by :meth:`_ignore_rule_sources`; a moved source keeps the
          whole set in the sweep, which is the pre-#22 verdict and the safe one.
        """
        if not moved:
            return set()
        sources_after = self._ignore_rule_sources(after)
        if sources_after != sources_before:
            changed = sorted(
                source for source in set(sources_before) | set(sources_after)
                if sources_before.get(source) != sources_after.get(source)
            )
            self._ctx.log(
                f"[write-subagents] {task_id}: the ignore rules changed during "
                f"the run ({', '.join(changed[:5])}"
                f"{', …' if len(changed) > 5 else ''}), so no gitignored path "
                f"leaves the containment sweep for this task — the rules a "
                f"runner can write cannot decide what it hid (D3l)."
            )
            return set()
        ignored = _git_utils.ignored_paths(sorted(moved), cwd=self._ctx.repo_root)
        return {path for path in ignored if self._ctx.policy.denied(path) is None}

    def moved_since_dispatch(
        self, task_id: str, snapshot: TaskSnapshot
    ) -> List[str]:
        """Every path this dispatch moved so far, declared or not. Read-only.

        ``snapshot.changed()`` (the declared set, by byte comparison) plus the
        paths the pre-run census says moved outside it — the same two sources
        :meth:`_classify` decides on, but **peeked**, not consumed: the census
        and its retained bytes stay registered for the terminal
        :meth:`_undeclared_writes` that still has to adopt them into the
        rollback snapshot. Siblings' declared paths are ignored exactly as
        there. Raises nothing it can avoid; a raise is read by the caller as
        "could not tell", which fails closed.
        """
        moved = set(snapshot.changed())
        with self._sweep_lock:
            before = self._census_before.get(task_id)
            retained = dict(self._retained_before.get(task_id) or {})
            sources = dict(self._ignore_sources_before.get(task_id) or {})
            ignored = set(self._sweep_ignored.get(task_id, ()))
            kept: "set[str]" = set()
            after = self.census(kept) if before is not None else None
        if before is not None and after is not None:
            swept = self._swept_moves(before, after, ignored, retained, kept)
            moved.update(
                swept - self._ignored_and_harmless(task_id, swept, sources, after)
            )
        return sorted(moved)

    def observed_with_undeclared(
        self, snapshot: TaskSnapshot, undeclared: UndeclaredWrites
    ) -> Dict[str, Any]:
        """``snapshot.observed()`` plus a row per undeclared write, for the audit.

        Every observed path is in the audit line whether or not it could be made
        reversible, and each says which it is: an operator reading this log has to
        be able to tell "restore-batch will undo this" from "this one needs a
        human", and silence on the second is how the first gets assumed.
        """
        observed = snapshot.observed()
        restorable = set(undeclared.restorable)
        for relative in undeclared.paths:
            row = observed.get(relative)
            if row is None:
                row = {
                    "sha256_before": None,
                    "sha256_after": file_sha256(
                        os.path.join(self._ctx.repo_root, relative)
                    ),
                }
                observed[relative] = row
            row["declared"] = False
            row["rollback"] = "retained" if relative in restorable else "unavailable"
            row["note"] = (
                "observed by the post-run sweep, outside any declared set"
                if relative in restorable else
                "observed by the post-run sweep, outside any declared set; no "
                "pre-run bytes were retained for it, so it cannot be restored"
            )
        return observed
