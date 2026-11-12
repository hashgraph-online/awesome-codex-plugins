#!/usr/bin/env python3
"""The one writer of ``{phase}/.status.json``.

This module holds the primitives that were previously inline in
``utils/review_orchestrator_base.py`` (``write_status``/``update_status``, which
still re-exports them under the same names). They live in a
module of their own for one reason: ``status`` has to be a *sub-second* command
(a file read plus a liveness probe, polled by hosts with a 2-minute shell cap),
and importing the review orchestration base pulls in the provider client, the
HTML report generator and the validation stack. Nothing about the write path
changed in the move — same atomic temp+rename, same best-effort swallow, same
merge semantics — so every existing consumer and test keeps its meaning. One
rule was added since: a merge that cannot read the checkpoint skips its update
rather than writing the update alone over it (:func:`update_status`,
:func:`load_status`). And two writers replace a damaged checkpoint whole
(:func:`checkpoint_damage`, :func:`archive_damaged_checkpoint`,
:func:`publish_checkpoint`): a fresh run's recovery in a phase whose
checkpoint records withheld answers (:data:`WITHHELD_RECORD_PHASES`,
``review_lane.recover_damaged_checkpoint``), and the owning run's
replacement in every other phase (:func:`replace_damaged_checkpoint`,
called by ``detach``).

**The schema is additive, never forked.** ``{phase}/.status.json`` is the
orchestrator checkpoint: ``ask_orchestrator`` reads ``question`` byte-for-byte as
its slug-collision guard and ``plan_hash`` for the stale-answers warning, and
``build_unsanitize_map`` reads ``models_requested``/``models_completed`` to
restore colon-bearing model specs during reaggregation. The run machinery
therefore adds keys to the *same* document under two reserved objects rather than
writing a second file with a private shape — ``run`` only ever on a detached run,
``progress`` on **every** run:

* ``run``: ``{run_id, pid, process_start_time, pgid, detached, host, mode, cwd,
  log_path, heartbeat_at, heartbeat_interval_s, state, exit_code, error,
  resolutions}`` — the **process** state machine
  (``starting → running → {done, failed, aborted}``). ``pgid`` is the worker's
  process group, recorded at start because it cannot be re-derived once the
  worker dies — it is what the close-out signals to reap surviving provider
  CLIs (``None`` on Windows, where a Job Object does that). Plus the optional
  ``replay_flags`` list (D2): the *launcher's* selection flags
  (``cli_common.replay_flags``), which ``status`` splices back into the
  ``resume with:`` command so a ``--quick`` run is retried as one. It is
  **not** process state — ``update_run``'s successor-state guard does not
  apply to it, and ``claim_run`` writes it once at start and never again.
* ``progress``: ``{step, models, models_done, models_succeeded, models_total,
  interval_s, tasks_generated, notes, subagents, write_subagents,
  sandbox_bypassed, sandbox_fallback}`` — reporting only; no external actor advances it, and nothing
  resumes, reaggregates or branches on it. That is why it is the one reserved
  object a **foreground** run writes too, and why ``run_record.report_progress``
  writes on *every* path: the run handle it consults picks the **door**, never
  whether the write happens. It goes through ``handle.progress`` (which stamps
  that run's heartbeat with it) only when the handle owns the dir being written,
  and straight through :func:`update_progress` otherwise — both when there is no
  handle at all (the foreground) and when the handle owns a *different* dir, as
  ``full --detach`` does: it claims ``{plan}/full/`` and then runs each phase in
  process against ``{plan}/<phase>/``. This docstring used to say the fallback
  was "when no run handle owns the phase dir", which reads as covering that
  second case while the code silently dropped it — every phase of a detached
  ``full`` reported nothing at all (F3, 2026-09-20). So: a foreground
  ``.status.json`` gains a ``progress`` object and still no ``run`` object, and
  a phase dir written by a run that owns a different one gains the same.
  ``models`` is the per-model map the fan-out keeps, keyed by model spec —
  ``{state: queued|staggering|running|retrying|done|failed, started_at,
  dispatched_at, updated_at, ended_at, elapsed_s, queued_s, timeout_s,
  attempt, retry_after_s, stagger_until, error, source, warning,
  readonly_audit}`` — ``started_at`` is when the slot was admitted to the
  fan-out, ``dispatched_at`` its **first** dispatch (a retry does not move
  it), ``elapsed_s`` the run time frozen at the terminal transition and
  counted from that first dispatch (``0`` for a slot that never dispatched),
  and ``queued_s`` the wait between admission and dispatch — written at the
  dispatch, or at the terminal transition for a slot that never dispatched,
  and absent when the wait's end is unknown (a map written before the key
  existed, or a never-dispatched row a ``--reaggregate`` closed out) — plan
  review-run-scope-salvage-and-failure-visibility §6; ``warning`` is a
  non-fatal note on a slot that still counts (plan §4.3's
  ``[SANDBOX_BYPASSED] … not attributed``), ``readonly_audit`` the compact
  combined verdict of an uncontained slot's stream audit (``{clean, reason,
  actions}``, never the stream), and ``stagger_until`` is the stamp a
  ``staggering`` slot's launch sleep ends at, which ``status`` renders as
  ``starts in 4s`` and the slot drops the moment it moves on. ``models_done`` counts *finished* slots (``done`` + ``failed``,
  which is why it never walks backwards mid-run) and its sibling
  ``models_succeeded`` counts the slots that produced a usable result;
  ``models_total`` is the number of specs requested. ``interval_s`` is the
  ticker cadence the run resolved. ``notes`` is a finished apply phase's list
  of plain lines a host must relay beside its counts — a consistency warning,
  the items left unapplied and why (fix round 14), or a review phase's notes
  on its result files (``utils/result_files.py``, fix round 24) — which
  ``status`` renders and carries into a terminal poll's ``notice``. ``subagents``
  and ``write_subagents`` are the executor's and the write scheduler's batch
  mirrors, ``sandbox_bypassed`` the sorted specs whose runner sandbox was
  bypassed and ``sandbox_fallback`` ``{spec: rung}`` for the contained rungs.
  This enumeration is the prose contract for the object — a reader who finds a
  key missing from it concludes the key is not part of the schema and writes a
  second file for it, so a new ``progress`` key lands here in the same commit as
  its writer. ``schemas/status_file.schema.json`` declares every key of the
  file, ``run`` and ``progress`` included, and ``tests/test_result_contract.py``
  fails on a key a writer adds without declaring it there
  (docs/development/dispatcher.md, "Result schemas").

``run.state`` is **not** the top-level ``state``. The top-level field stays the
*phase* machine (``models_running`` → ``models_complete``/``grouping_complete`` →
``validation_pending`` → ``complete``) that resume and the published instruction
text match verbatim; a crashed fan-out is exactly the pair
``state: models_running`` + ``run.state: failed``, and no reader collapses one
into the other.

After the initial ``write_status`` a detached child only ever calls
``update_status`` (via :func:`update_run`): a heartbeat-shaped ``write_status``
would drop ``question``, ``plan_hash`` and ``models_requested`` and break both
ask resume and the unsanitize map.

**Every write in this module is one critical section** (:func:`checkpoint_lock`).
Both writers are read-modify-write — ``write_status`` carries the reserved
objects over from disk, ``update_status`` merges into what it read — and a
detached run has two writer *threads*: the orchestrator's main thread (phase
transitions, ``output_files``, the terminal record from ``RunHandle.finish``)
and ``RunHandle``'s daemon heartbeat, beating every 10 s. Unserialized, a
heartbeat that read the file just before a main-thread write and
``os.replace``\\ s just after it reverts that write wholesale — the ``done``
record back to ``running`` (later mis-closed as ``failed(heartbeat_timeout)``),
or a dropped ``validation_tasks_path``. The compare-and-set in
:func:`update_run` does not close that window on its own: it is check-then-act
against a *separate* read, so the lock has to span the read, the CAS and the
write.

**And the section has to be interprocess, not just interthread.** The writers of
one ``run`` record live in *different processes* by design: the worker (main
thread and heartbeat), ``status``'s ``failed(heartbeat_timeout)`` close-out,
``status --abort``, and ``--sweep``. ``{phase}/.lock`` cannot serialize them —
it is *ownership*, taken once by the worker and held for the run's lifetime, so
the very processes that have to interleave safely with it are the ones that can
never hold it (``status`` deliberately takes no lock, which is what lets it
report on a live run). With only a thread lock, an abort and a late completion
both read ``running``, both pass their expected-state check, and the second
``os.replace`` wins — a terminal ``aborted`` record silently replaced by
``done``, or a closed-out predecessor overwriting the run that displaced it. So
every read-modify-write here takes :func:`checkpoint_lock`: a
``threading.RLock`` (:data:`_WRITE_LOCK`, reentrant because the write path nests
``update_run`` → ``update_status`` → ``write_status``) **plus** a
``process_control.FileMutex`` over ``{phase}/.status.lock``, held across the
comparison *and* the atomic replace, by claims and terminal transitions alike.
The mutex file is separate from ``{phase}/.lock`` precisely because the two
locks answer different questions ("who owns this dir" vs "whose turn is it to
write"); it is created on demand, never unlinked, and its existence says nothing
about whether anyone holds it.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import stat
import sys
import threading
import time
from datetime import datetime
from typing import Any, Dict, Iterable, Iterator, NamedTuple, Optional, Tuple

from . import process_control
from .held_folder import write_in_plan_dir
from .clock import local_iso

#: The checkpoint file name. Dot-prefixed on purpose: reaggregation globs
#: ``{phase_dir}/*.json`` and Python's ``glob`` skips leading-dot names, which is
#: the only reason this file is not parsed as a model result.
STATUS_FILENAME = ".status.json"

#: The temp-file prefix of :func:`write_status` (``.status_<pid>.<random>.tmp``).
STATUS_TEMP_PREFIX = ".status_"

#: The interprocess mutex guarding every read-modify-write of the checkpoint.
#: A *second* lock file next to ``{phase}/.lock`` on purpose — that one is
#: ownership held for the whole run, this one is a turn taken for the length of
#: one merge (see the module docstring). Dot-prefixed like its sibling, so
#: reaggregation's ``*.json`` glob never sees it either.
STATUS_LOCK_FILENAME = ".status.lock"

#: Keys whose value is a dict that is *merged* rather than replaced wholesale, so
#: a writer that knows about one sub-key cannot erase another writer's.
#: ``output_files`` was already merged this way; ``run`` and ``progress`` join it
#: on the same path (D4a).
_MERGED_OBJECTS: Tuple[str, ...] = ("output_files", "run", "progress")

#: The objects a detach run owns. A plain ``write_status`` from the phase's own
#: checkpoint path must not erase them (see :func:`write_status`).
_RESERVED_OBJECTS: Tuple[str, ...] = ("run", "progress")

#: Top-level checkpoint keys that are one run's result, not the phase's state:
#: :func:`claim_run` drops them with the predecessor's ``run`` and ``progress``.
#: A pinned poll relays each one as the polled run's own, and nothing else on
#: the checkpoint (the claim keeps the top-level ``state``) tells a
#: predecessor's copy apart (docs/development/runtime.md, "Status file schema").
RUN_SCOPED_KEYS: Tuple[str, ...] = ("high_priority_groups", "validation_counts")

#: A pre-dispatch refusal's close-out (``review_orchestrator_base.
#: _print_executor_refusal``, the write scheduler's batch refusal): the top-level
#: ``state`` words it writes, and the keys it writes beside them. It is one
#: run's ending, not the phase's state, so :func:`claim_run` retires the whole
#: of it: ``status`` renders a ``runner_rejected`` state's repair off
#: ``reason_code`` (``run_status._resume_shape``), and a retry refused before
#: its own first write would otherwise be told to repair the previous run's
#: fault (docs/development/runtime.md, "Status file schema").
REFUSAL_STATES: Tuple[str, ...] = ("runner_rejected", "executor_refused")
REFUSAL_KEYS: Tuple[str, ...] = ("reason_code", "runner", "runner_key", "refused_batch")

#: How often ``status --wait`` re-reads the status file (``run_status``). The
#: heartbeat is 10 s, so a faster cadence learns nothing; 5 s keeps the
#: returned view fresh. Also the floor of the registry's ``progress.*`` keys
#: (``provider_registry._progress_floor_s``).
WAIT_POLL_INTERVAL_S = 5.0

#: A model slot's two end states in ``progress.models``, from the fan-out's
#: lifecycle (``progress_tracker``, which re-exports them with its live states):
#: the result-file reader counts them too.
STATE_DONE = "done"
STATE_FAILED = "failed"

#: The two states a slot may end in. There is deliberately no ``skipped``: a
#: model answered from disk is ``done`` — it has a usable result — and the
#: distinction lives in ``source`` (see ``progress_tracker.RESUME_SOURCES``), so
#: ``models_done`` and ``models_succeeded`` stay derivable from ``state`` alone.
TERMINAL_STATES = frozenset({STATE_DONE, STATE_FAILED})

#: The process state machine. ``stale`` is deliberately absent: it is a *view* of
#: a ``running`` record whose heartbeat expired, never a stored state.
RUN_STATE_STARTING = "starting"
RUN_STATE_RUNNING = "running"
RUN_STATE_DONE = "done"
RUN_STATE_FAILED = "failed"
RUN_STATE_ABORTED = "aborted"

TERMINAL_RUN_STATES = (RUN_STATE_DONE, RUN_STATE_FAILED, RUN_STATE_ABORTED)

#: Serializes every read-modify-write of the checkpoint within this process, so
#: the heartbeat thread cannot revert a main-thread write (see module docstring).
#: Reentrant because the write path nests; held only across local file I/O, so
#: nothing under it waits on another thread.
_WRITE_LOCK = threading.RLock()

#: The interprocess mutexes this process currently holds, keyed by lock path.
#: Only ever touched under :data:`_WRITE_LOCK`, which is also what makes the
#: entry a sufficient reentrancy record: while the RLock is held no *other*
#: thread can be inside :func:`checkpoint_lock` at all, so a key that is present
#: can only be this thread's own outer frame.
_HELD_MUTEXES: Dict[str, "process_control.FileMutex"] = {}

#: Legal transitions. Anything else is a bug and is refused loudly rather than
#: merged — including any transition *out of* a terminal state, which is what
#: keeps "exactly one terminal state per run" true.
_LEGAL_TRANSITIONS: Dict[Optional[str], Tuple[str, ...]] = {
    None: (RUN_STATE_STARTING, RUN_STATE_RUNNING),
    RUN_STATE_STARTING: (RUN_STATE_STARTING, RUN_STATE_RUNNING) + TERMINAL_RUN_STATES,
    RUN_STATE_RUNNING: (RUN_STATE_RUNNING,) + TERMINAL_RUN_STATES,
    RUN_STATE_DONE: (RUN_STATE_DONE,),
    RUN_STATE_FAILED: (RUN_STATE_FAILED,),
    RUN_STATE_ABORTED: (RUN_STATE_ABORTED,),
}


def status_path(phase_dir: str) -> str:
    """Absolute-or-relative path of a phase dir's checkpoint file."""
    return os.path.join(str(phase_dir), STATUS_FILENAME)


def status_lock_path(phase_dir: str) -> str:
    """Path of the phase dir's checkpoint mutex (:data:`STATUS_LOCK_FILENAME`)."""
    return os.path.join(str(phase_dir), STATUS_LOCK_FILENAME)


#: Every stamp in the checkpoint (``heartbeat_at``, ``updated_at``, ...): local
#: time, to the microsecond (``utils/clock.py``); ``run_record._elapsed_since``
#: reads them.
now_iso = local_iso


class CheckpointLockUnavailable(Exception):
    """:func:`checkpoint_lock` with ``required=True`` could not take the mutex."""


@contextlib.contextmanager
def checkpoint_lock(phase_dir: str, *, required: bool = False) -> Iterator[None]:
    """Hold *phase_dir*'s checkpoint mutex — across threads and processes.

    Every read-modify-write in this module runs inside one of these, and so must
    any caller that has to span a read and a later compare-and-set as one step.
    Reentrant: the write path nests (``update_run`` → ``update_status`` →
    ``write_status``), and only the outermost frame takes and drops the
    interprocess lock. A nested frame must *not* take it a second time — an OS
    lock is held per open file description, so a second ``open`` of the same
    file is just another contender, even in the process that already holds it,
    and every nested write would stall until its wait expired.

    **Best-effort, exactly like the writes it guards.** A phase dir that does not
    exist (nothing to lock, and the write is about to fail anyway) or a holder
    that is stopped rather than dead leaves the mutex untaken after its bounded
    wait; the body then runs unserialized, which is what it did before this lock
    existed. It is never an exception, because a heartbeat that raises out of a
    checkpoint write kills a run over a lock file.

    ``required=True`` is the one exception, for a decision that is only sound
    serialized (a review round's ownership check, ``utils/review_round.py``):
    a mutex it cannot take raises :class:`CheckpointLockUnavailable` before
    the body runs, and so does a nested frame whose outer frame ran untaken.
    """
    with _WRITE_LOCK:
        # `realpath`, so one phase dir is one lock domain however a caller spells
        # it: a worker started through a symlinked plan path and a `status
        # --abort` started through the real one must contend for the same file.
        key = os.path.realpath(status_lock_path(phase_dir))
        if key in _HELD_MUTEXES:  # a nested write; the outer frame owns it
            if required and not _HELD_MUTEXES[key].held:
                raise CheckpointLockUnavailable(key)
            yield
            return
        mutex = process_control.FileMutex(key)
        if not mutex.acquire() and required:
            raise CheckpointLockUnavailable(key)
        _HELD_MUTEXES[key] = mutex
        try:
            yield
        finally:
            del _HELD_MUTEXES[key]
            mutex.release()


# ---------------------------------------------------------------------------
# Write / merge (moved verbatim from review_orchestrator_base)
# ---------------------------------------------------------------------------

def write_status(phase_dir: str, data: dict) -> None:
    """Write a .status.json checkpoint file atomically. Best-effort.

    The reserved ``run``/``progress`` objects are carried over from disk when the
    caller does not mention them: they belong to the process that *owns* the phase
    dir, not to the phase checkpoint being written, and a fan-out phase writing its
    opening ``state: models_running`` must not erase the heartbeat of the very run
    performing it. Passing the key explicitly (including as ``None``) still wins,
    which is how :func:`claim_run` replaces a predecessor's record.

    The carry-over read and the rename are one critical section (thread *and*
    process): a concurrent writer between them would either lose its own
    reserved objects or be reverted by this one.

    The write is ``atomic_io``'s, owner-only (0600), without ``fsync``: the
    heartbeat rewrites the file every few seconds under the checkpoint lock
    (docs/development/runtime.md#atomic-file-writes). It is published through
    the phase folder held below the plan's directory
    (``held_folder.write_in_plan_dir``): a link swapped in for that folder
    during the run is refused, never written through, and the checkpoint is
    then not written, as any failed write leaves it
    (docs/development/write-safety.md#plan-output-containment).
    """
    path = status_path(phase_dir)
    with checkpoint_lock(phase_dir):
        try:
            if any(key not in data for key in _RESERVED_OBJECTS):
                existing = read_status(phase_dir)
                for key in _RESERVED_OBJECTS:
                    if key not in data and key in existing:
                        data[key] = existing[key]
        except Exception:
            pass
        try:
            data["updated_at"] = now_iso()
            write_in_plan_dir(path, json.dumps(data, indent=2).encode("utf-8"),
                              mode=0o600, fsync=False, temp_prefix=STATUS_TEMP_PREFIX)
        except Exception:
            pass


def update_status(phase_dir: str, updates: dict) -> None:
    """Merge updates into existing .status.json. Best-effort.

    ``output_files``, ``run`` and ``progress`` are merged key-by-key rather than
    replaced, so a heartbeat that carries only ``heartbeat_at`` cannot erase
    ``run.run_id`` and a progress update cannot erase a sibling counter. Every
    other key is replaced, exactly as before.

    The read, the merge and the nested :func:`write_status` are one critical
    section — held against other processes as well as other threads — so a
    concurrent writer's document can neither be read stale nor be reverted by
    the rename that follows.

    No checkpoint yet: the update is the whole new document. A checkpoint that
    exists but cannot be read now, or holds something other than a JSON object
    (:func:`load_status`), is kept as it is and the update is skipped: written
    over it, the update alone would replace every key it does not name, the
    records of withheld slot answers among them
    (docs/development/review-results.md, "Withheld slot answers"). A damaged
    one is replaced whole only at a run's start, by the run that owns the
    dir (:func:`replace_damaged_checkpoint`, ``review_lane.recover_damaged_checkpoint``).
    """
    with checkpoint_lock(phase_dir):
        try:
            existing = load_status(phase_dir) or {}
        except CheckpointUnreadable:
            return
        try:
            for key in _MERGED_OBJECTS:
                incoming = updates.get(key)
                current = existing.get(key)
                if isinstance(incoming, dict) and isinstance(current, dict):
                    merged = dict(current)
                    merged.update(incoming)
                    updates = dict(updates)
                    updates[key] = merged
            existing.update(updates)
            write_status(phase_dir, existing)
        except Exception:
            pass


def remove_status_keys(phase_dir: str, keys: Iterable[str]) -> None:
    """Delete top-level ``keys`` from ``.status.json``. Best-effort (§7.2a).

    The explicit deletion :func:`update_status` cannot express: its merge is
    ``existing.update(updates)``, so ``update_status(d, {"k": None})`` writes
    ``"k": null`` rather than removing ``k``. Read, ``pop`` and rewrite are one
    critical section under :func:`checkpoint_lock`, exactly like
    :func:`update_status`; the reserved ``run``/``progress`` objects and every
    other sibling survive untouched. A no-op when the file or a key is absent
    (nothing is written at all when no key was present).
    """
    keys = [str(key) for key in keys]
    path = status_path(phase_dir)
    with checkpoint_lock(phase_dir):
        try:
            if not os.path.exists(path):
                return
            with open(path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
            if not isinstance(existing, dict):
                return
            if not any(key in existing for key in keys):
                return
            for key in keys:
                existing.pop(key, None)
            write_status(phase_dir, existing)
        except Exception:
            pass


def read_status(phase_dir: str) -> Dict[str, Any]:
    """Read a phase dir's checkpoint, or ``{}`` when absent/unreadable.

    Never raises: a torn or hand-edited file must not make ``status`` crash, and
    the write path is temp+rename so a torn read is only possible if something
    else wrote the file.
    """
    path = status_path(phase_dir)
    try:
        with _open_checkpoint(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, IOError, ValueError):
        return {}


def _nonblocking(path: str, flags: int) -> int:
    return os.open(path, flags | getattr(os, "O_NONBLOCK", 0))


def _open_checkpoint(path: str, mode: str, **kwargs: Any) -> Any:
    """*path* opened for reading as ``open`` opens it, but never blocking (a
    FIFO at the name, or at a link's end, opens at once) and only when the
    descriptor is a regular file (``fstat``, so a name swapped after any
    earlier ``lstat`` cannot slip a FIFO or a device in): ``OSError``
    otherwise, which every reader takes for a read that failed. Links are
    followed, as the readers always followed them."""
    handle = open(path, mode, opener=_nonblocking, **kwargs)
    try:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise OSError(f"{path} is not a regular file")
    except BaseException:
        handle.close()
        raise
    return handle


class CheckpointUnreadable(Exception):
    """:func:`load_status`: the checkpoint exists, but could not be read or
    is not a JSON object."""


#: How often a reader that stops the run over an unreadable checkpoint reads
#: it before it gives up (:func:`load_status`'s *attempts*): a read failure
#: that passes (a descriptor limit, a flaky mount) is not damage.
CHECKPOINT_READ_ATTEMPTS = 3

#: The pause before the second read, doubled before each one after it.
_CHECKPOINT_RETRY_DELAY = 0.05


def load_status(phase_dir: str, *, attempts: int = 1) -> Optional[Dict[str, Any]]:
    """A phase dir's checkpoint for a reader that decides something on it.

    ``None`` when there is none; raises :class:`CheckpointUnreadable` when one
    exists but cannot be opened or parsed, or holds something other than a
    JSON object, on each of *attempts* reads. :func:`read_status` folds both
    into ``{}``, which is right for a view but not for a merge, nor for a
    reader that would take a missing key for permission
    (docs/development/review-results.md, "Withheld slot answers").
    """
    path = status_path(phase_dir)
    for attempt in range(max(1, attempts)):
        if attempt:
            time.sleep(_CHECKPOINT_RETRY_DELAY * 2 ** (attempt - 1))
        try:
            with _open_checkpoint(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            return None
        except (OSError, ValueError) as exc:
            failure: BaseException = exc
            continue
        if isinstance(data, dict):
            return data
        failure = CheckpointUnreadable(path)
    raise CheckpointUnreadable(path) from failure


#: The phases whose checkpoint records which model answers are withheld
#: (``result_files``: ``models_rejected``, ``models_unchecked``,
#: ``checkpoint_recovered``): the review fan-outs (review-plan, review-tasks,
#: review-code and review-commits, whose phase is ``code-review``) and ask.
#: Only a fresh run of the phase recovers their damaged checkpoint, every
#: earlier answer set aside and every model withheld after
#: (``review_lane.recover_damaged_checkpoint``). Every other phase's
#: checkpoint holds run, progress and display records only, so the run that
#: owns the dir replaces a damaged one (:func:`replace_damaged_checkpoint`)
#: (docs/development/review-results.md, "Recovering a damaged one").
WITHHELD_RECORD_PHASES: Tuple[str, ...] = ("review-plan", "review-tasks", "code-review", "ask")


def records_withheld_answers(phase: Optional[str]) -> bool:
    """Whether *phase*'s checkpoint can record withheld answers
    (:data:`WITHHELD_RECORD_PHASES`). A phase that cannot be named
    (``None``) is taken to, so nothing is replaced over it."""
    return phase is None or phase in WITHHELD_RECORD_PHASES


def unreadable_checkpoint_advice(phase_dir: str, *, phase: Optional[str] = None) -> str:
    """What every stop over a phase checkpoint that cannot be read tells the
    user to do, the same everywhere (docs/development/review-results.md,
    "Withheld slot answers").

    In a phase whose checkpoint records withheld answers
    (:func:`records_withheld_answers`, the default when *phase* is not
    given) the checkpoint is what withholds answers whose safety checks
    failed or never finished: moved aside alone, it would leave their files
    beside a phase that no longer records them, and they would be read as
    results. A fresh run of the phase, a review fan-out or ask, recovers a
    damaged one in that order: every earlier result set aside or withheld
    first, its bytes copied aside and a fresh checkpoint renamed over it
    after (``review_lane.recover_damaged_checkpoint``). Every other phase's
    run replaces a damaged one at its start
    (:func:`replace_damaged_checkpoint`), and its checkpoint may be moved
    aside alone."""
    if not records_withheld_answers(phase):
        return (
            f"If the read failure has passed, running again is enough. If the file "
            f"is damaged, run the phase again: its run keeps the damaged file as "
            f"{STATUS_FILENAME}{UNREADABLE_ARCHIVE_INFIX}<time> and starts a fresh "
            f"one (this phase's checkpoint holds run and progress records only). "
            f"If the file cannot be opened at all, or that replacement stops, move "
            f"{status_path(phase_dir)} aside, or delete it, and run the phase again."
        )
    return (
        f"If the read failure has passed, running again is enough. If the file "
        f"is damaged, run the phase again without --reaggregate once no run of "
        f"this phase is live (`status`): a fresh run (a review fan-out, or the "
        f"same ask question) keeps the damaged file as "
        f"{STATUS_FILENAME}{UNREADABLE_ARCHIVE_INFIX}<time> and reuses no earlier "
        f"result in the folder: every model runs again. If the file cannot be "
        f"opened at all, or that recovery stops, move the whole phase folder "
        f"{phase_dir} aside, or delete it, and run the phase again. Never move "
        f".status.json aside on its own: the result files left beside it would "
        f"then be read as results, answers whose safety checks failed among them."
    )


# ---------------------------------------------------------------------------
# A damaged checkpoint: told apart from a read that failed, archived, replaced
# ---------------------------------------------------------------------------

#: What a damaged checkpoint's bytes are kept as (:func:`archive_damaged_checkpoint`):
#: ``.status.json.unreadable-<stamp>``. Dot-prefixed and no longer ending in
#: ``.json``, so no reader of the phase dir takes it for a checkpoint or a result.
UNREADABLE_ARCHIVE_INFIX = ".unreadable-"


class CheckpointDamage(NamedTuple):
    """A checkpoint read whole whose bytes are not a JSON object
    (:func:`checkpoint_damage`): its path, the SHA-256 of the bytes, their
    length and what they are instead."""

    path: str
    digest: str
    size: int
    detail: str


def _not_an_object(data: bytes) -> Optional[str]:
    """What *data* is instead of a JSON object, or ``None`` when it is one."""
    if not data:
        return "empty"
    try:
        document = json.loads(data.decode("utf-8"))
    except UnicodeDecodeError:
        return "not UTF-8 text"
    except (ValueError, RecursionError):
        return "not JSON"
    if isinstance(document, dict):
        return None
    return f"a JSON {type(document).__name__}, not an object"


def checkpoint_damage(
    phase_dir: str, *, attempts: int = CHECKPOINT_READ_ATTEMPTS,
) -> Optional[CheckpointDamage]:
    """Whether *phase_dir*'s checkpoint is **damaged**, as opposed to absent,
    readable, or unread.

    ``None`` when there is none, or when a read finds a JSON object. A
    :class:`CheckpointDamage` only when each of *attempts* reads got the same
    bytes, from a regular file, and they are not a JSON object: the file is
    there and wrong, and reading it again will not change that. Raises
    :class:`CheckpointUnreadable` otherwise: a read that failed (a descriptor
    limit, a permission, a flaky mount), a link or anything but a file at the
    name, or bytes that changed between reads. Those are not proven damage,
    and nothing may be done to the file over them
    (docs/development/review-results.md, "Withheld slot answers"). Nothing
    blocks: a name that is no file is never opened, and every open is
    :func:`_open_checkpoint`'s, so a FIFO behind a link, or swapped in after
    the ``lstat``, is a failed read too."""
    path = status_path(phase_dir)
    failure: Optional[BaseException] = None
    found: Optional[CheckpointDamage] = None
    stable = True
    for attempt in range(max(1, attempts)):
        if attempt:
            time.sleep(_CHECKPOINT_RETRY_DELAY * 2 ** (attempt - 1))
        try:
            info = os.lstat(path)
        except FileNotFoundError:
            return None
        except OSError as exc:
            failure, stable = exc, False
            continue
        link = stat.S_ISLNK(info.st_mode)
        if not (link or stat.S_ISREG(info.st_mode)):
            failure, stable = CheckpointUnreadable(f"{path} is not a file"), False
            continue
        try:
            with _open_checkpoint(path, "rb") as handle:
                data = handle.read()
        except FileNotFoundError:
            return None
        except OSError as exc:
            failure, stable = exc, False
            continue
        detail = _not_an_object(data)
        if detail is None:
            return None
        if link:
            failure, stable = CheckpointUnreadable(f"{path} is a link"), False
            continue
        seen = CheckpointDamage(path, hashlib.sha256(data).hexdigest(), len(data), detail)
        if found is not None and found.digest != seen.digest:
            failure, stable = CheckpointUnreadable(f"{path} changed between reads"), False
        found = seen
    if stable and found is not None:
        return found
    raise CheckpointUnreadable(path) from failure


def _still_damaged(path: str, damage: CheckpointDamage, *, doing: str) -> bytes:
    """The bytes at *path*, read again: ``OSError`` unless they are the ones
    *damage* found, in a regular file (a link is refused, never followed)."""
    try:
        if not stat.S_ISREG(os.lstat(path).st_mode):
            raise OSError(f"{path} is not a regular file")
        with _open_checkpoint(path, "rb") as handle:
            data = handle.read()
    except OSError as exc:
        raise OSError(f"{path} could not be read again before it was {doing} "
                      f"({exc})") from exc
    if hashlib.sha256(data).hexdigest() != damage.digest:
        raise OSError(f"{path} changed after it was found damaged, so it was not {doing}")
    return data


def archive_damaged_checkpoint(phase_dir: str, damage: CheckpointDamage, stamp: str) -> str:
    """Copy the damaged checkpoint's bytes to ``.status.json.unreadable-<stamp>``
    (:data:`UNREADABLE_ARCHIVE_INFIX`, ``-2``... on a collision); the copy's path.

    The checkpoint itself is left in place, so it keeps refusing the folder
    until :func:`publish_checkpoint` replaces it in one rename: no moment
    leaves the phase without one. Under the checkpoint mutex, which must be
    taken (:class:`CheckpointLockUnavailable`), and only while the file still
    holds the bytes *damage* read; the copy is written through the phase
    folder held below the plan's directory and flushed. ``OSError`` when no
    copy was written."""
    path = status_path(phase_dir)
    with checkpoint_lock(phase_dir, required=True):
        data = _still_damaged(path, damage, doing="archived")
        name = f"{STATUS_FILENAME}{UNREADABLE_ARCHIVE_INFIX}{stamp}"
        suffix = 2
        while os.path.lexists(os.path.join(str(phase_dir), name)):
            name = f"{STATUS_FILENAME}{UNREADABLE_ARCHIVE_INFIX}{stamp}-{suffix}"
            suffix += 1
        target = os.path.join(str(phase_dir), name)
        write_in_plan_dir(target, data, mode=0o600, fsync=True, temp_prefix=STATUS_TEMP_PREFIX)
        return target


def publish_checkpoint(
    phase_dir: str, document: Dict[str, Any], *, replacing: Optional[CheckpointDamage] = None,
) -> Dict[str, Any]:
    """Write *document* as *phase_dir*'s whole checkpoint, and read it back;
    the document as read.

    Unlike :func:`write_status`, nothing is carried over and nothing is
    swallowed: the write (published through the phase folder held below the
    plan's directory, flushed, renamed over the old file in one step) raises
    ``OSError`` when it fails, a read-back that cannot be read raises
    :class:`CheckpointUnreadable`, and one that differs raises ``OSError``.
    With *replacing*, only over the damaged bytes it found (``OSError``
    otherwise, nothing written). Under the checkpoint mutex, which must be
    taken (:class:`CheckpointLockUnavailable`). For the one writer that
    replaces a damaged checkpoint (``review_lane.recover_damaged_checkpoint``)."""
    data = dict(document)
    path = status_path(phase_dir)
    with checkpoint_lock(phase_dir, required=True):
        if replacing is not None:
            _still_damaged(path, replacing, doing="replaced")
        data["updated_at"] = now_iso()
        write_in_plan_dir(path, json.dumps(data, indent=2).encode("utf-8"),
                          mode=0o600, fsync=True, temp_prefix=STATUS_TEMP_PREFIX)
        back = load_status(phase_dir)
        if back != data:
            raise OSError(f"{path} does not read back as written")
        return back


def replace_damaged_checkpoint(
    phase_dir: str, damage: CheckpointDamage, *, phase: Optional[str],
) -> str:
    """Replace *damage*, a damaged checkpoint of a phase whose checkpoint
    records no withheld answers, with a fresh one; the path of the damaged
    bytes' copy.

    For the run that owns *phase_dir*, at its start, before its first
    checkpoint write. Nothing of the damaged file is read: its bytes are
    copied to ``.status.json.unreadable-<stamp>``
    (:func:`archive_damaged_checkpoint`), then ``{"phase": phase}`` is
    renamed over it in one step, only while it still holds those bytes, and
    read back (:func:`publish_checkpoint`), under one hold of the checkpoint
    mutex. What is lost is the run, progress and display records an earlier
    run wrote there, which no later run decides on.

    Refused with ``ValueError``, nothing written, for a phase in
    :data:`WITHHELD_RECORD_PHASES` or one not named: only a fresh run of such
    a phase recovers its checkpoint, every earlier answer set aside first
    (``review_lane.recover_damaged_checkpoint``). Raises
    :class:`CheckpointLockUnavailable` when the mutex cannot be taken,
    ``OSError`` when the copy or the replacement fails or the bytes changed,
    and :class:`CheckpointUnreadable` when the fresh one cannot be read back
    (docs/development/review-results.md, "Recovering a damaged one")."""
    if records_withheld_answers(phase):
        raise ValueError(
            f"{status_path(phase_dir)} records withheld answers ({phase or 'phase not named'}): "
            f"only a fresh run of the phase recovers it")
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    with checkpoint_lock(phase_dir, required=True):
        archived = archive_damaged_checkpoint(phase_dir, damage, stamp)
        publish_checkpoint(phase_dir, {"phase": phase}, replacing=damage)
    return archived


def read_run(phase_dir: str) -> Dict[str, Any]:
    """The ``run`` object of a phase dir's checkpoint, or ``{}``."""
    run = read_status(phase_dir).get("run")
    return run if isinstance(run, dict) else {}


# ---------------------------------------------------------------------------
# The reserved `run` object: compare-and-set on run_id
# ---------------------------------------------------------------------------

class RunConflict(Exception):
    """A ``run`` write was refused: wrong ``run_id``, a closed-out (terminal)
    record, or an illegal transition."""


def claim_run(phase_dir: str, record: Dict[str, Any]) -> None:
    """Install a brand-new ``run`` record, replacing any predecessor's.

    The *only* place the whole ``run`` object is replaced. Called once, by the
    worker, immediately after it takes ``{phase}/.lock`` — which is what makes
    the replacement safe: the lock holder is by definition the single writer, and
    a predecessor record can only be a terminal run or one whose holder failed
    the liveness+identity probe. Every write after this one is a compare-and-set
    (:func:`update_run`), so a stale process that wakes up later cannot resurrect
    itself over the new run.
    """
    # Drop the predecessor's `run` *and* `progress` wholesale: inheriting either
    # would report another run's exit code or another run's step as this one's.
    # Both writes are one critical section — the same one `update_run`'s
    # compare-and-set takes — so no writer, in this process or another, can
    # observe (or write into) the momentary run-less document between them and
    # mistake it for a dir with no owner.
    # The run-scoped results go with them (`RUN_SCOPED_KEYS`): the top-level
    # `state` this keeps would let a poll relay them as the new run's. So does
    # a refusal close-out, its `state` word included (`REFUSAL_STATES`,
    # `REFUSAL_KEYS`): kept, it is read as this run's refusal
    # (docs/development/runtime.md, "Status file schema").
    with checkpoint_lock(phase_dir):
        update_status(phase_dir, {"run": None, "progress": None})
        retired = [*RUN_SCOPED_KEYS, *REFUSAL_KEYS]
        if read_status(phase_dir).get("state") in REFUSAL_STATES:
            retired.append("state")
        remove_status_keys(phase_dir, retired)
        update_status(phase_dir, {"run": dict(record)})


def update_run(
    phase_dir: str,
    updates: Dict[str, Any],
    *,
    expect_run_id: str,
    extra: Optional[Dict[str, Any]] = None,
    quiet: bool = False,
) -> bool:
    """Compare-and-set merge into ``run``; ``True`` when the write happened.

    Refuses (returning ``False``) when the on-disk ``run.run_id`` is neither
    absent nor equal to ``expect_run_id``, when the recorded ``run.state`` is
    already terminal and the update does not carry a ``state`` of its own, or
    when the requested ``run.state`` is not a legal successor of the recorded
    one. All three refusals are the same guarantee from three directions: a run
    that was closed out (by ``status``'s heartbeat-timeout sweep, or by
    ``--abort``) stays closed, and a second writer cannot interleave its
    heartbeat with the holder's.

    The middle refusal is the one that stops a *zombie*. A worker that was
    paused past its heartbeat window (SIGSTOP, a suspended laptop) and closed
    out keeps the **same** ``run_id``, so the identity check alone lets it
    through, and a heartbeat carries no ``state`` for the transition table to
    judge. Left to write, it would go on beating — and therefore go on
    dispatching providers and interleaving result files with a foreground
    ``--resume`` — with only its final ``finish()`` refused. So a terminal
    record accepts nothing but a legal restatement of its own terminal state
    (``_LEGAL_TRANSITIONS`` allows the self-loop and nothing else), which is
    what turns ``update_run``'s ``False`` into the heartbeat loop's stop
    signal (``RunHandle._beat_loop``).

    The comparison and the set share one :func:`checkpoint_lock`, because a CAS
    whose check happens against one read and whose act happens against a later
    write is not a CAS at all: the heartbeat thread would re-open a record
    ``finish()`` closed a moment after it read it — and, since that lock is
    interprocess, so would ``--abort`` and the stale-cleanup sweep, which run in
    processes of their own and would otherwise both pass the expected-state
    check and let the slower ``os.replace`` win.
    """
    with checkpoint_lock(phase_dir):
        current = read_run(phase_dir)
        disk_id = current.get("run_id")
        if disk_id is not None and disk_id != expect_run_id:
            if not quiet:
                print(
                    f"NOTE: refusing to update run {expect_run_id} — {phase_dir} is "
                    f"now owned by run {disk_id}",
                    file=sys.stderr,
                )
            return False
        disk_state = current.get("state")
        new_state = updates.get("state")
        if new_state is None and disk_state in TERMINAL_RUN_STATES:
            if not quiet:
                print(
                    f"NOTE: refusing to update run {expect_run_id} — {phase_dir} "
                    f"recorded a terminal run.state ({disk_state!r}); the record "
                    "is closed",
                    file=sys.stderr,
                )
            return False
        if new_state is not None:
            allowed = _LEGAL_TRANSITIONS.get(disk_state, ())
            if new_state not in allowed:
                if not quiet:
                    print(
                        f"NOTE: refusing illegal run transition "
                        f"{disk_state!r} -> {new_state!r} for run "
                        f"{expect_run_id} in {phase_dir}",
                        file=sys.stderr,
                    )
                return False
        payload: Dict[str, Any] = dict(extra or {})
        merged = dict(updates)
        merged.setdefault("run_id", expect_run_id)
        payload["run"] = merged
        update_status(phase_dir, payload)
        return True


def append_resolution(
    phase_dir: str, *, run_id: str, site: str, decision: str
) -> bool:
    """Record one auto-resolved decision point (D4c) on the run.

    ``site`` is a D6 table row identifier, so the table stays the single source
    of truth for what the default *was*.

    Append-to-a-list is itself a read-modify-write, so it takes the same lock:
    two resolutions recorded from different threads — or different processes —
    must not lose one.
    """
    with checkpoint_lock(phase_dir):
        current = read_run(phase_dir)
        resolutions = list(current.get("resolutions") or [])
        resolutions.append({"site": site, "decision": decision, "at": now_iso()})
        return update_run(
            phase_dir, {"resolutions": resolutions}, expect_run_id=run_id, quiet=True
        )


def update_progress(phase_dir: str, updates: Dict[str, Any]) -> None:
    """Merge into the reserved ``progress`` object (display only)."""
    update_status(phase_dir, {"progress": dict(updates)})


def is_terminal(run: Optional[Dict[str, Any]]) -> bool:
    return bool(run) and run.get("state") in TERMINAL_RUN_STATES
