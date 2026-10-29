#!/usr/bin/env python3
"""The one writer of ``{phase}/.status.json``.

This module holds the primitives that were previously inline in
``utils/review_orchestrator_base.py`` (``write_status``/``update_status``, which
still re-exports them under the same names, as do
``review_plan_orchestrator._write_status``/``_update_status``). They live in a
module of their own for one reason: ``status`` has to be a *sub-second* command
(a file read plus a liveness probe, polled by hosts with a 2-minute shell cap),
and importing the review orchestration base pulls in the provider client, the
HTML report generator and the validation stack. Nothing about the write path
changed in the move — same atomic temp+rename, same best-effort swallow, same
merge semantics — so every existing consumer and test keeps its meaning.

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
* ``progress``: ``{step, batch_index, batches_total, tasks_done, tasks_total,
  tasks_generated, failed_task_ids, models, models_done, models_succeeded,
  models_total, interval_s, notes}`` — reporting only; no external actor advances it, and nothing
  resumes, reaggregates or branches on it. That is why it is the one reserved
  object a **foreground** run writes too, and why ``detach.report_progress``
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
  ``status`` renders and carries into a terminal poll's ``notice``. This enumeration is the in-code contract for
  the object — a reader who finds a key missing from it concludes the key is not
  part of the schema and writes a second file for it, so a new ``progress`` key
  lands here in the same commit as its writer.

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
import json
import os
import sys
import tempfile
import threading
from datetime import datetime
from typing import Any, Dict, Iterable, Iterator, Optional, Tuple

from . import process_control

#: The checkpoint file name. Dot-prefixed on purpose: reaggregation globs
#: ``{phase_dir}/*.json`` and Python's ``glob`` skips leading-dot names, which is
#: the only reason this file is not parsed as a model result.
STATUS_FILENAME = ".status.json"

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


def now_iso() -> str:
    return datetime.now().isoformat()


@contextlib.contextmanager
def checkpoint_lock(phase_dir: str) -> Iterator[None]:
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
    """
    with _WRITE_LOCK:
        # `realpath`, so one phase dir is one lock domain however a caller spells
        # it: a worker started through a symlinked plan path and a `status
        # --abort` started through the real one must contend for the same file.
        key = os.path.realpath(status_lock_path(phase_dir))
        if key in _HELD_MUTEXES:  # a nested write; the outer frame owns it
            yield
            return
        mutex = process_control.FileMutex(key)
        mutex.acquire()
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
    """
    temp_path = None
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
            temp_fd, temp_path = tempfile.mkstemp(
                dir=phase_dir, suffix='.tmp', prefix='.status_'
            )
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            os.replace(temp_path, path)
        except Exception:
            try:
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)
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
    """
    path = status_path(phase_dir)
    with checkpoint_lock(phase_dir):
        try:
            existing = {}
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            if not isinstance(existing, dict):
                existing = {}
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
            try:
                write_status(phase_dir, updates)
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
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, IOError, ValueError):
        return {}


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
    with checkpoint_lock(phase_dir):
        update_status(phase_dir, {"run": None, "progress": None})
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
