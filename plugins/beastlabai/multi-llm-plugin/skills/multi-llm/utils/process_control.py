#!/usr/bin/env python3
"""The one import boundary for OS process control: locking, liveness, detach.

**Ownership note (cross-plan).** ``plans/windows-macos-portability.md`` owns this
file's POSIX/Windows selection and the "no Unix-only stdlib in runtime code"
invariant that keeps ``fcntl``/``msvcrt`` behind it. That plan had not landed when
``--detach`` shipped, and its sequencing rule says whichever plan lands first
creates the file and the second adopts it. So this module was typed here, by the
detach work, deliberately thin:

* Everything detach-specific — process-group / Job Object control,
  creation-time identity, the detached spawn — is contributed *back* to that
  plan and has no other caller.
* Everything generic — the POSIX/Windows split itself, the file lock, the
  liveness probe — is the seam that plan will take over. Signatures here are a
  cross-plan interface: changing one is a change to both plans.

No orchestrator imports ``fcntl`` or ``msvcrt``; they import this. Every
POSIX-only call below is guarded, because this project supports Windows today.

The three primitives and why each exists:

1. **Identity, not just liveness.** A ``.status.json`` left by a prior session can
   name a pid the OS has since recycled, so ``pid`` is corroboration and the
   *process creation time* is identity. ``probe()`` returns ``alive`` only when
   both agree; a mismatch is ``dead`` whatever the pid says.
2. **One writer per phase dir.** :class:`PhaseLock` is ``flock(LOCK_EX|LOCK_NB)``
   on POSIX and ``msvcrt.locking(LK_NBLCK)`` on Windows, held on an open fd for
   the run's lifetime — so a crashed process releases it even though the file
   remains. **The file is durable; only the lock is ever released** (see
   :meth:`PhaseLock.release`): unlock-then-unlink would let a second process take
   the inode in the gap and a third create a new file at the same path, which is
   two holders of one phase lock. The holder's identity is written *into* the
   file so a second launcher
   can name who owns the dir. **The lock is the authority; the payload is only a
   label.** It is written after the lock is taken, so it can legitimately be
   empty (a brand-new file), half-written, or still naming a dead predecessor
   while a live process holds the lock — which is why an unreadable payload is
   :data:`UNKNOWN` (see :func:`holder_verdict`) and why :func:`break_lock` proves
   the lock is free by *taking* it rather than by trusting what it read.
3. **Detachment that actually detaches.** POSIX needs two spawns (cut the
   terminal and the fds; then cut the parent, so the worker reparents to init and
   the invoker has no child to reap). Windows needs one
   (``DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP`` already removes the console),
   and the launcher must hand the log handle in because a console-less child has
   no valid stdout to inherit.

A fourth, for the Lane A fan-out: **a stopped provider CLI takes its detached
children with it.** :func:`descendants` snapshots a CLI's tree while it is alive,
:func:`terminate_timed_out` stops the CLI (SIGTERM first) and then every
snapshotted process group under :func:`kill_tree`'s identity rule, and
:data:`live_cli_registry` keeps a refreshed snapshot of every live CLI so an
abort or a Ctrl-C can do the same after the CLI itself has already died —
inside a budget that ends before the abort SIGKILLs the worker.
"""

from __future__ import annotations

import asyncio
import json
import os
import signal
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import (
    Any, Awaitable, Callable, Dict, Iterator, List, NamedTuple, Optional, Sequence,
    Tuple, TypeVar,
)

_T = TypeVar("_T")

IS_WINDOWS = os.name == "nt"

#: :func:`probe` verdicts.
ALIVE = "alive"
DEAD = "dead"
UNKNOWN = "unknown"

#: Byte offset the Windows lock is taken at. Windows file locks are *mandatory*,
#: so locking byte 0 would make the holder payload unreadable to anyone else —
#: including the ``status`` command, whose whole job is to report who holds the
#: dir. Locking a byte far past the payload keeps the file readable while the
#: lock stays exclusive.
_WINDOWS_LOCK_OFFSET = 1 << 30

#: How long :func:`kill_tree` waits between SIGTERM and SIGKILL.
DEFAULT_ESCALATE_AFTER_S = 10.0


# ---------------------------------------------------------------------------
# Identity + liveness
# ---------------------------------------------------------------------------

def process_start_time(pid: int) -> Optional[str]:
    """The process's creation time as a stable string, or ``None`` if unknown.

    Linux reads ``/proc/<pid>/stat`` field 22 (start time in clock ticks since
    boot); macOS/BSD shell out to ``ps -o lstart=``; Windows asks
    ``GetProcessTimes`` for the creation time. ``None`` means "this platform could
    not tell us", which callers must treat as *inconclusive*, never as a match.
    """
    if pid is None or pid <= 0:
        return None
    if IS_WINDOWS:
        return _windows_start_time(pid)
    linux = _linux_start_time(pid)
    if linux is not None:
        return linux
    return _ps_start_time(pid)


def _linux_start_time(pid: int) -> Optional[str]:
    try:
        with open(f"/proc/{pid}/stat", "r", encoding="utf-8", errors="replace") as f:
            raw = f.read()
    except (OSError, IOError):
        return None
    # comm (field 2) is parenthesised and may itself contain spaces and ')'.
    close = raw.rfind(")")
    if close == -1:
        return None
    fields = raw[close + 2:].split()
    # After comm the next field is 3, so field 22 is index 19.
    if len(fields) <= 19:
        return None
    return fields[19]


def _ps_start_time(pid: int) -> Optional[str]:
    try:
        result = subprocess.run(
            ["ps", "-o", "lstart=", "-p", str(pid)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def _windows_start_time(pid: int) -> Optional[str]:  # pragma: no cover - Windows
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    except Exception:
        # A locked-down Windows sandbox can deny the DLL or the API. Unknown is a
        # defined answer here (the caller renders it as `stale`); a crash is not.
        return None
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return None
    try:
        creation = wintypes.FILETIME()
        exit_time = wintypes.FILETIME()
        kernel_time = wintypes.FILETIME()
        user_time = wintypes.FILETIME()
        ok = kernel32.GetProcessTimes(
            handle,
            ctypes.byref(creation), ctypes.byref(exit_time),
            ctypes.byref(kernel_time), ctypes.byref(user_time),
        )
        if not ok:
            return None
        return str((creation.dwHighDateTime << 32) | creation.dwLowDateTime)
    finally:
        kernel32.CloseHandle(handle)


def process_alive(pid: Optional[int]) -> bool:
    """Is *pid* a live process? ``os.kill(pid, 0)`` is not a probe on Windows."""
    if not pid or pid <= 0:
        return False
    if IS_WINDOWS:  # pragma: no cover - Windows
        return _windows_alive(pid)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Alive but owned by another user.
        return True
    except OSError:
        return False
    return True


def _windows_alive(pid: int) -> bool:  # pragma: no cover - Windows
    try:
        import ctypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    except Exception:
        return False
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    STILL_ACTIVE = 259
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return False
    try:
        code = ctypes.c_ulong()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
            return False
        return code.value == STILL_ACTIVE
    finally:
        kernel32.CloseHandle(handle)


def probe(pid: Optional[int], start_time: Optional[str]) -> str:
    """``alive`` / ``dead`` / ``unknown`` for a recorded (pid, start time) pair.

    ``unknown`` is the honest answer when the pid is live but the platform could
    not corroborate identity: the caller renders that as ``stale`` and waits for a
    human (``--abort``) rather than closing the run out on a guess.
    """
    if not pid:
        return DEAD
    if not process_alive(pid):
        return DEAD
    observed = process_start_time(pid)
    if not start_time or not observed:
        return UNKNOWN
    return ALIVE if str(observed) == str(start_time) else DEAD


def identity() -> Dict[str, Any]:
    """This process's own ``(pid, process_start_time)`` pair."""
    pid = os.getpid()
    return {"pid": pid, "process_start_time": process_start_time(pid)}


def process_group_id(pid: Optional[int] = None) -> Optional[int]:
    """The process group *pid* belongs to (this process by default), or ``None``.

    Recorded at worker start because it cannot be recovered later: after the
    POSIX double spawn the worker's group leader is the *intermediate*, which has
    already exited, so ``os.getpgid(worker_pid)`` is the only way to read it —
    and that call fails the moment the worker itself dies, which is exactly when
    the close-out needs the group to kill the provider children it left behind.
    ``None`` on Windows, where the tree is a Job Object (D4d) rather than a group.
    """
    if IS_WINDOWS:  # pragma: no cover - Windows
        return None
    try:
        return os.getpgid(os.getpid() if pid is None else int(pid))
    except (OSError, TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# The phase-dir lock
# ---------------------------------------------------------------------------

def _take_fd_lock(fd: int) -> None:
    """Take the exclusive OS lock on *fd*, **non-blocking**. Raises on conflict.

    The one place the platform split for locking lives; both lock shapes below
    (ownership and mutex) are built out of it, so a Windows fix is one edit.
    """
    if IS_WINDOWS:  # pragma: no cover - Windows
        import msvcrt

        os.lseek(fd, _WINDOWS_LOCK_OFFSET, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        os.lseek(fd, 0, os.SEEK_SET)
        return
    import fcntl

    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)


def _drop_fd_lock(fd: int) -> None:
    """Release the exclusive OS lock on *fd*."""
    if IS_WINDOWS:  # pragma: no cover - Windows
        import msvcrt

        os.lseek(fd, _WINDOWS_LOCK_OFFSET, os.SEEK_SET)
        try:
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        return
    import fcntl

    fcntl.flock(fd, fcntl.LOCK_UN)


class LockUnavailable(Exception):
    """Another process holds the lock. Carries the recorded holder, if any."""

    def __init__(self, path: str, holder: Optional[Dict[str, Any]]):
        super().__init__(f"lock held: {path}")
        self.path = path
        self.holder = holder or {}


class PhaseLock:
    """A non-blocking, advisory-on-POSIX / mandatory-on-Windows file lock.

    Held on an open fd for the whole run, so a crash releases it even though the
    file remains on disk — which is why "the file exists" is never treated as
    "someone holds it".
    """

    def __init__(self, path: str):
        self.path = str(path)
        self._fd: Optional[int] = None

    # -- acquisition ----------------------------------------------------
    def acquire(self, payload: Optional[Dict[str, Any]] = None) -> None:
        """Take the lock, recording *payload* in the file. Raises on conflict."""
        flags = os.O_CREAT | os.O_RDWR
        if hasattr(os, "O_BINARY"):  # pragma: no cover - Windows
            flags |= os.O_BINARY
        fd = os.open(self.path, flags, 0o644)
        try:
            self._lock_fd(fd)
        except (OSError, IOError):
            os.close(fd)
            raise LockUnavailable(self.path, read_lock_holder(self.path))
        self._fd = fd
        if payload is not None:
            self._write_payload(payload)

    def _lock_fd(self, fd: int) -> None:
        _take_fd_lock(fd)

    def _write_payload(self, payload: Dict[str, Any]) -> None:
        # Write first, *then* truncate to the bytes just written: truncating to
        # zero first would open a window in which a concurrent reader sees an
        # empty file while this process already holds the lock. It cannot be
        # closed entirely (a reader can still catch a short read), which is why
        # no caller is allowed to read "no payload" as "no holder".
        assert self._fd is not None
        body = json.dumps(payload, indent=2).encode("utf-8")
        os.lseek(self._fd, 0, os.SEEK_SET)
        os.write(self._fd, body)
        os.truncate(self._fd, len(body))
        try:
            os.fsync(self._fd)
        except OSError:  # pragma: no cover - filesystem without fsync
            pass

    # -- release --------------------------------------------------------
    def release(self) -> None:
        """Drop the OS lock. The file itself is **never** deleted. Idempotent.

        Unlinking here would split the lock into two domains. Unlock-then-unlink
        cannot be made atomic: between them another process legitimately takes
        the lock on this inode, the unlink then removes that holder's *pathname*,
        and a third process ``O_CREAT``s a fresh file at the same path and locks
        that — two workers, two inodes, both believing they own the phase dir,
        interleaving ``.status.json`` merges. (The mirror image is just as bad:
        a holder displaced by ``break_lock(force=True)`` would, on release,
        unlink the path its *successor* now owns.) So the file is durable and the
        lock is what is held: an empty ``{phase}/.lock`` left behind means
        nothing, exactly as it already does after a crash — see
        :func:`lock_is_free`, which probes rather than stats.
        """
        fd, self._fd = self._fd, None
        if fd is None:
            return
        try:
            _drop_fd_lock(fd)
        finally:
            try:
                os.close(fd)
            except OSError:
                pass

    @property
    def held(self) -> bool:
        return self._fd is not None

    def __enter__(self) -> "PhaseLock":
        return self

    def __exit__(self, *exc_info) -> None:
        self.release()


def read_lock_holder(path: str) -> Optional[Dict[str, Any]]:
    """The identity recorded in a lock file, or ``None``.

    On Windows the payload sits before the locked byte range precisely so this
    read works while the lock is held. ``None`` means *the label is unreadable*
    — never *nobody holds this lock*; :func:`holder_verdict` is the rule.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, IOError, ValueError):
        return None


def holder_verdict(holder: Optional[Dict[str, Any]]) -> str:
    """The identity verdict for a *recorded* lock holder.

    A missing, empty or half-written payload is :data:`UNKNOWN`, never
    :data:`DEAD`. The payload is written after the lock is taken, so "I could not
    read it" is indistinguishable from "the holder is one instruction younger
    than my read" — and every caller treats ``DEAD`` as a licence to break the
    lock. Only a payload that was actually read *and* whose (pid, creation-time)
    pair probes dead earns that.
    """
    if not holder:
        return UNKNOWN
    return probe(holder.get("pid"), holder.get("process_start_time"))


def lock_is_free(path: str) -> bool:
    """True when nobody currently holds *path* (probed, not inferred).

    Used by the ``status`` read path, which must not create the file: a missing
    lock file is free by definition, and an existing one is tested by trying to
    take it and immediately releasing it. The file is never deleted, so "free"
    is always a probe result and never inferred from the file's absence.
    """
    if not os.path.exists(path):
        return True
    probe_lock = PhaseLock(path)
    try:
        probe_lock.acquire()
    except LockUnavailable:
        return False
    except OSError:
        return False
    probe_lock.release()
    return True


def break_lock(path: str, *, force: bool = False) -> bool:
    """Free a lock whose holder is gone. ``True`` when nobody holds it now.

    The proof that the holder is gone is *the lock itself*: this takes it, so a
    file whose payload is unreadable or names a dead predecessor while a live
    process still holds it is **refused** (``False``) instead of broken.
    Breaking a held lock is the one failure the lock exists to prevent — it puts
    two runs on two inodes of "the" phase lock, interleaving ``.status.json``
    merges.

    A stale lock is therefore broken by *acquiring and releasing* it, never by
    unlinking: a crashed holder's lock is already free (the OS dropped it), and
    the leftover file is inert — the next acquirer overwrites its payload.

    ``force=True`` is the deliberate ``--force`` path, which the plan defines as
    taking the dir over from a **live** holder — the one case an unlink is the
    only available mechanism, since no process can drop another's lock. It still
    tries the non-destructive path first, so forcing a lock nobody holds does
    not needlessly unlink an inode a concurrent launcher may be acquiring.
    """
    if not os.path.exists(path):
        return True
    probe_lock = PhaseLock(path)
    try:
        probe_lock.acquire()
    except LockUnavailable:
        pass
    except OSError:
        # The file could not even be opened: inconclusive, unless it has since
        # vanished — in which case there is nothing left to hold.
        if not os.path.exists(path):
            return True
    else:
        probe_lock.release()
        return True
    if not force:
        return False
    # `--force` against a genuinely held lock. The displaced holder keeps its
    # (now unnamed) inode and cannot unlink the successor's file, because
    # `release` no longer unlinks anything.
    try:
        os.unlink(path)
        return True
    except FileNotFoundError:
        return True
    except OSError:
        return False


# ---------------------------------------------------------------------------
# The short-held mutex (serialization, not ownership)
# ---------------------------------------------------------------------------

#: How long :meth:`FileMutex.acquire` waits for its turn. Generous by three
#: orders of magnitude — a holder does a JSON read plus a temp+rename — because
#: the only thing this bound exists for is to keep a *stopped* holder from
#: hanging a heartbeat thread forever.
DEFAULT_MUTEX_TIMEOUT_S = 10.0


class FileMutex:
    """A **blocking**, briefly-held interprocess mutex over one path.

    :class:`PhaseLock` and this are the same OS primitive in two different
    shapes, kept as two classes because they mean opposite things to a caller:

    * A phase lock is **ownership** — taken once, held for the whole run, and a
      conflict is an error a human is told about (exit 3 naming the holder).
    * A mutex is **serialization** — taken for the microseconds of one
      read-modify-write, and a conflict is the *normal* case: the caller waits
      its turn. Using ``PhaseLock`` for this would turn every concurrent
      checkpoint write into a spurious "someone else owns this phase dir", and
      the run that owns the dir already holds the phase lock for its lifetime,
      so it could never take it a second time.

    The wait is bounded rather than infinite. A holder that *dies* releases the
    lock (the OS drops it with the fd), but one that is *stopped* — SIGSTOP, a
    suspended laptop — never does, and a worker's heartbeat thread blocked
    forever on a checkpoint write is a worse failure than the interleaving the
    lock prevents. :meth:`acquire` therefore reports ``False`` on timeout and
    lets its caller decide; it never raises.

    The file is created on demand and, like every lock file here, is **never
    unlinked**: unlock-then-unlink would put two processes on two inodes of
    "the" mutex (see :meth:`PhaseLock.release`). An existing file means nothing
    about whether anyone holds it.
    """

    def __init__(self, path: str):
        self.path = str(path)
        self._fd: Optional[int] = None

    def acquire(
        self,
        *,
        timeout_s: float = DEFAULT_MUTEX_TIMEOUT_S,
        poll_interval_s: float = 0.005,
    ) -> bool:
        """Wait for the lock; ``True`` when it was taken. Never raises.

        ``False`` means *proceed unserialized or give up* — the file could not
        be opened (a phase dir that does not exist) or the wait expired.
        """
        if self._fd is not None:
            return True
        flags = os.O_CREAT | os.O_RDWR
        if hasattr(os, "O_BINARY"):  # pragma: no cover - Windows
            flags |= os.O_BINARY
        try:
            fd = os.open(self.path, flags, 0o644)
        except (OSError, IOError, ValueError):
            return False
        deadline = time.monotonic() + max(0.0, float(timeout_s))
        while True:
            try:
                _take_fd_lock(fd)
            except (OSError, IOError):
                if time.monotonic() >= deadline:
                    try:
                        os.close(fd)
                    except OSError:
                        pass
                    return False
                time.sleep(poll_interval_s)
                continue
            self._fd = fd
            return True

    def release(self) -> None:
        """Drop the lock, keeping the file. Idempotent, never raises."""
        fd, self._fd = self._fd, None
        if fd is None:
            return
        try:
            _drop_fd_lock(fd)
        except (OSError, IOError):
            pass
        finally:
            try:
                os.close(fd)
            except OSError:
                pass

    @property
    def held(self) -> bool:
        return self._fd is not None


# ---------------------------------------------------------------------------
# Process-tree teardown
# ---------------------------------------------------------------------------

def new_process_group_kwargs() -> Dict[str, Any]:
    """``Popen`` kwargs that make a child the root of its own process group.

    The precondition for :func:`kill_tree`, and the reason it is a facade call
    rather than a literal at each spawn site: an agentic runner is not a leaf.
    It spawns tool children of its own (a shell, a nested provider CLI), which
    inherit the parent's group *and* the parent's stdout pipe — so a signal to
    the direct child alone leaves them running, still burning quota, still
    holding the pipe open, and an unbounded post-kill ``communicate()`` blocks
    forever on the writer that never went away.

    POSIX: ``start_new_session`` (a real ``setsid`` in the forked child, so it
    is safe to use from a thread), which makes the child a session and group
    leader — its group id *is* its pid, and ``os.killpg`` on it never reaches
    back into the caller's own group. Windows: ``CREATE_NEW_PROCESS_GROUP``,
    which is what makes the child a valid ``CTRL_BREAK_EVENT`` target; it does
    **not** break the child out of the worker's Job Object (D4d), so job
    teardown still covers the tree.
    """
    if IS_WINDOWS:  # pragma: no cover - Windows
        return {
            "creationflags": getattr(
                subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200
            )
        }
    return {"start_new_session": True}


def kill_tree(
    pid: int,
    *,
    start_time: Optional[str] = None,
    pgid: Optional[int] = None,
    escalate_after_s: float = DEFAULT_ESCALATE_AFTER_S,
    poll_interval_s: float = 0.1,
    job: Optional[TreeJob] = None,
) -> str:
    """Terminate *pid* and every process it spawned. Returns a verdict string.

    ``gone`` (was already dead, and nothing of its group survives), ``killed``
    (died, gracefully or after the escalation), ``survived`` (still alive after
    the SIGKILL window) or ``skipped`` (identity could not be corroborated — the
    pid may have been recycled, so signalling it would hit an unrelated process).

    Two identity rules, and they are the whole contract:

    * ``start_time`` supplied and the probe cannot corroborate it ⇒ ``skipped``,
      **no signal**. ``kill_tree`` is reached by routine paths (``util runs
      --sweep`` over week-old entries whose ``/proc`` read failed), and a
      recycled pid's *process group* is an unrelated group.
    * an unverified kill is *requested*, never inferred: pass ``start_time=None``
      — which is how ``--force`` and the failed-handshake teardown spell it.

    The worker is its own process-group leader and every provider CLI it spawns
    inherits that group, so a group signal takes the whole tree down and no
    provider is left burning quota against a run nobody is reading. That group
    outlives its leader, so a recorded *pgid* is still killed when the leader
    itself is gone (the crash case D4b's close-out has to clean up); it is only
    ever the recorded value, never one re-derived from a pid whose identity just
    failed.

    Windows has no groups. There *job* is the child's :class:`TreeJob` from
    :func:`popen_tree`, which plays the group's part: the escalation
    terminates it rather than running ``taskkill /T`` (which can reach an
    unrelated orphan, :func:`taskkill_tree`), and a leader already gone still
    has what it left in the job ended. A detached run's pid read off disk
    has one too, by name: :func:`kill_run_tree` opens it and passes it here
    (2026-10-25). Without one (a run whose job could not be opened, a child
    spawned without a job) the escalation is ``taskkill /T`` as before.
    """
    if not pid and not pgid:
        # Nothing recorded to probe or signal, but a job still names a tree: a
        # run whose record lost its pid, found by its run id (`kill_run_tree`).
        if IS_WINDOWS and job is not None:  # pragma: no cover - Windows
            job.terminate()
        return "gone"
    verdict = probe(pid, start_time) if pid else DEAD
    if verdict == UNKNOWN and start_time:
        return "skipped"
    if verdict == DEAD:
        if pgid and not IS_WINDOWS:
            return _posix_kill_group(pgid, escalate_after_s, poll_interval_s)
        if IS_WINDOWS and job is not None:  # pragma: no cover - Windows
            job.terminate()
        return "gone"
    if IS_WINDOWS:  # pragma: no cover - Windows
        return _windows_kill_tree(pid, escalate_after_s, job)
    return _posix_kill_tree(pid, escalate_after_s, poll_interval_s, pgid=pgid)


def _resolve_pgid(recorded: Optional[int], pid: Optional[int]) -> Optional[int]:
    """The group to signal: the recorded one, else the live leader's own.

    Never this process's own group (a self-kill) and never init's.
    """
    candidate: Optional[int] = None
    if recorded:
        try:
            candidate = int(recorded)
        except (TypeError, ValueError):
            candidate = None
    if candidate is None and pid:
        try:
            candidate = os.getpgid(int(pid))
        except (OSError, TypeError, ValueError):
            candidate = None
    if candidate is None or candidate <= 1:
        return None
    try:
        if candidate == os.getpgid(0):
            return None
    except OSError:  # pragma: no cover - getpgid(0) does not fail in practice
        return None
    return candidate


def _group_has_members(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _posix_kill_group(pgid: int, escalate_after_s: float, poll_interval_s: float) -> str:
    """SIGTERM → SIGKILL a recorded process group whose leader is already gone."""
    group = _resolve_pgid(pgid, None)
    if group is None:
        return "skipped"
    if not _group_has_members(group):
        return "gone"

    def send(sig: int) -> None:
        try:
            os.killpg(group, sig)
        except OSError:
            pass

    send(signal.SIGTERM)
    deadline = time.time() + max(escalate_after_s, 0.0)
    while time.time() < deadline:
        if not _group_has_members(group):
            return "killed"
        time.sleep(poll_interval_s)
    if not _group_has_members(group):
        return "killed"
    send(signal.SIGKILL)
    deadline = time.time() + 5.0
    while time.time() < deadline:
        if not _group_has_members(group):
            return "killed"
        time.sleep(poll_interval_s)
    return "survived" if _group_has_members(group) else "killed"


def _signal_tree(pid: Optional[int], pgid: Optional[int], sig: int) -> None:
    """*sig* to the group :func:`_resolve_pgid` picks, else to *pid* alone.

    A ``None`` *pid* means no pid is safe to signal (its identity was not just
    corroborated), so a group that cannot be signalled gets nothing at all.
    """
    group = _resolve_pgid(pgid, pid)
    if group is not None:
        try:
            os.killpg(group, sig)
            return
        except OSError:
            pass
    if pid:
        try:
            os.kill(pid, sig)
        except OSError:
            pass


def _posix_kill_tree(
    pid: int,
    escalate_after_s: float,
    poll_interval_s: float,
    pgid: Optional[int] = None,
) -> str:
    def signal_target(sig: int) -> None:
        _signal_tree(pid, pgid, sig)

    signal_target(signal.SIGTERM)
    deadline = time.time() + max(escalate_after_s, 0.0)
    while time.time() < deadline:
        if not process_alive(pid):
            return "killed"
        time.sleep(poll_interval_s)
    if not process_alive(pid):
        return "killed"
    signal_target(signal.SIGKILL)
    deadline = time.time() + 5.0
    while time.time() < deadline:
        if not process_alive(pid):
            return "killed"
        time.sleep(poll_interval_s)
    return "survived" if process_alive(pid) else "killed"


def taskkill_tree(pid: int, *, timeout: float = 30.0) -> None:  # pragma: no cover
    """``taskkill /T /F`` on *pid*: Windows' kill of a process and every process
    it spawned, at once.

    :func:`kill_tree`'s escalation there when the child has no
    :class:`TreeJob`, and the whole kill of a child that was started in no
    group of its own, which a ``CTRL_BREAK_EVENT`` cannot target:
    ``Popen.kill`` is ``TerminateProcess`` on the direct child alone.
    Best-effort: a ``taskkill`` that is missing or overruns *timeout* is let go.

    Prefer :func:`end_tree` with the child's job. ``taskkill /T`` finds the
    tree by parent pid, and Windows keeps a dead parent's pid on its orphans,
    so an unrelated orphan whose dead parent's pid was recycled to *pid* dies
    with it. It is also a process of its own, which can overrun *timeout* on
    a loaded machine and then kill nothing past the direct child.
    """
    try:
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True, timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError):
        pass


# ---------------------------------------------------------------------------
# Windows: one Job Object per spawned child (round-8 review, 2026-10-24)
# ---------------------------------------------------------------------------
#
# Windows has no process groups to signal, and `taskkill /T` walks parent pids
# (see `taskkill_tree`). A Job Object holds exactly a tree: `popen_tree` creates
# the child suspended, puts it in a job of its own and only then resumes it, so
# nothing the child starts runs outside the job, and `TerminateJobObject` ends
# exactly those processes in one call, with no process of its own to time out.
#
# Why everything the child starts stays in the job. A child is created in every
# job its parent is in, unless the parent's own job lets it break away. The
# venv's `python.exe` launcher, uv's trampolines and libuv (node) each put their
# child in a job of their own with SILENT_BREAKAWAY_OK, so *their* children
# leave that job, and keep leaving up the chain of jobs above it until they
# reach one that does not permit breakaway. A `TreeJob` sets no limit at all,
# so it permits none, and that is where they stop.

#: ``CreateProcess`` flag: the child's first thread starts suspended.
_CREATE_SUSPENDED = 0x00000004

#: The spawn :func:`popen_tree` puts in a job: the real one, which creates a
#: process. A replaced ``subprocess.Popen`` (a test double) creates none, so
#: there is nothing to put in a job and it is called as it is.
_REAL_POPEN = subprocess.Popen

#: The exit code ``TerminateJobObject`` gives each process; ``taskkill /F``'s.
_JOB_KILL_EXIT_CODE = 1

#: ``GetLastError`` after a ``CreateJobObjectW`` that opened an existing job
#: of that name instead of creating one (WinError.h: 183).
_ERROR_ALREADY_EXISTS = 183

#: Job access rights (winnt.h). An aborter asks for these two and no more:
#: ``TerminateJobObject`` needs TERMINATE, ``IsProcessInJob`` needs QUERY.
_JOB_OBJECT_QUERY = 0x0004
_JOB_OBJECT_TERMINATE = 0x0008


class TreeJob:
    """A Job Object holding one spawned child and every process it starts.

    No limit is set, ``KILL_ON_JOB_CLOSE`` included: :meth:`close` lets go of
    the handle and kills nothing, so what a child leaves running after a
    normal exit keeps running, as a process group's members do on POSIX. Only
    :meth:`terminate` kills. Made by :func:`popen_tree`; for a detached run's
    named job, by :func:`spawn_detached_run` (the launcher's handle) and
    :func:`open_run_job` (an aborter's).
    """

    def __init__(self, api: Any, handle: int) -> None:
        self._api = api
        self._handle: Optional[int] = handle

    def terminate(self) -> bool:
        """End every process in the job now. ``False`` when that failed or
        the handle is already closed, which leaves the caller its fallback."""
        handle = self._handle
        if handle is None:
            return False
        try:
            return bool(self._api.terminate(handle, _JOB_KILL_EXIT_CODE))
        except Exception:  # noqa: BLE001 - the caller falls back to taskkill
            return False

    def close(self) -> None:
        """Let go of the handle (never a kill). Idempotent."""
        handle, self._handle = self._handle, None
        if handle is not None:
            try:
                self._api.close(handle)
            except Exception:  # noqa: BLE001 - a leaked handle is all it costs
                pass


class _JobApi:  # pragma: no cover - Windows
    """The kernel32 and ntdll calls behind :func:`popen_tree`,
    :class:`TreeJob` and a detached run's named job (:func:`open_run_job`),
    typed, so a 64-bit handle is never cut to a C ``int``."""

    #: ``PROCESS_TERMINATE | PROCESS_SET_QUOTA | PROCESS_SUSPEND_RESUME``: what
    #: ``AssignProcessToJobObject`` and ``NtResumeProcess`` need.
    _PROCESS_RIGHTS = 0x0001 | 0x0100 | 0x0800

    #: ``PROCESS_QUERY_LIMITED_INFORMATION``: all ``IsProcessInJob`` needs of
    #: the process it tests, and the least an aborter can ask of a pid it
    #: read off disk.
    _PROCESS_QUERY = 0x1000

    def __init__(self) -> None:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        ntdll = ctypes.WinDLL("ntdll")
        handle, boolean, dword = wintypes.HANDLE, wintypes.BOOL, wintypes.DWORD
        for name, argtypes, restype in (
            ("CreateJobObjectW", [ctypes.c_void_p, wintypes.LPCWSTR], handle),
            ("OpenJobObjectW", [dword, boolean, wintypes.LPCWSTR], handle),
            ("AssignProcessToJobObject", [handle, handle], boolean),
            ("IsProcessInJob", [handle, handle, ctypes.POINTER(boolean)], boolean),
            ("TerminateJobObject", [handle, wintypes.UINT], boolean),
            ("OpenProcess", [dword, boolean, dword], handle),
            ("GetCurrentProcess", [], handle),
            ("CloseHandle", [handle], boolean),
        ):
            function = getattr(kernel32, name)
            function.argtypes, function.restype = argtypes, restype
        # Undocumented but stable since XP; psutil resumes processes with it.
        # Popen keeps no handle of the child's first thread, so ResumeThread
        # has nothing to resume.
        ntdll.NtResumeProcess.argtypes = [handle]
        ntdll.NtResumeProcess.restype = ctypes.c_long
        self._ctypes = ctypes
        self._bool = boolean
        self._kernel32 = kernel32
        self._resume = ntdll.NtResumeProcess

    def create(self) -> Optional[int]:
        return self._kernel32.CreateJobObjectW(None, None) or None

    def create_named(self, name: str) -> Tuple[Optional[int], bool]:
        """``CreateJobObjectW(NULL, name)``: the handle (``JOB_OBJECT_ALL_ACCESS``),
        and whether the name already existed, in which case the handle is the
        *existing* job's and the caller decides whether it may use it.

        The last error is cleared first: the documented signal for an existing
        object is a *successful* call whose last error is
        ``ERROR_ALREADY_EXISTS``, and a fresh creation is not documented to
        clear a stale value. ``use_last_error`` swaps the ctypes copy in before
        the call and out after it, so the zero is what the call starts from.
        """
        self._ctypes.set_last_error(0)
        handle = self._kernel32.CreateJobObjectW(None, name) or None
        existed = (
            handle is not None
            and self._ctypes.get_last_error() == _ERROR_ALREADY_EXISTS
        )
        return handle, existed

    def open_named(self, name: str, access: int) -> Optional[int]:
        return self._kernel32.OpenJobObjectW(access, False, name) or None

    def open_process(self, pid: int) -> Optional[int]:
        # Our own child, which Popen's handle keeps from being reused.
        return self._kernel32.OpenProcess(self._PROCESS_RIGHTS, False, pid) or None

    def query_process(self, pid: int) -> Optional[int]:
        return self._kernel32.OpenProcess(self._PROCESS_QUERY, False, pid) or None

    def current_process(self) -> int:
        # A pseudo handle, (HANDLE)-1 today: never closed, valid wherever a
        # process handle is, with PROCESS_ALL_ACCESS.
        return self._kernel32.GetCurrentProcess()

    def in_job(self, process: int, job: int) -> Optional[bool]:
        """``IsProcessInJob``; ``None`` when the call itself failed."""
        result = self._bool()
        if not self._kernel32.IsProcessInJob(process, job, self._ctypes.byref(result)):
            return None
        return bool(result.value)

    def assign(self, job: int, process: int) -> bool:
        return bool(self._kernel32.AssignProcessToJobObject(job, process))

    def resume(self, process: int) -> bool:
        return self._resume(process) == 0  # STATUS_SUCCESS

    def terminate(self, job: int, exit_code: int) -> bool:
        return bool(self._kernel32.TerminateJobObject(job, exit_code))

    def close(self, handle: int) -> None:
        self._kernel32.CloseHandle(handle)


_JOB_API: List[Any] = []


def _job_api() -> Optional[Any]:
    """The Windows job calls, loaded once; ``None`` where they cannot be
    (another OS, a sandbox that denies the DLL), which spawns as before."""
    if not _JOB_API:
        try:
            _JOB_API.append(_JobApi())
        except Exception:  # noqa: BLE001 - no job: taskkill is the kill
            _JOB_API.append(None)
    return _JOB_API[0]


def popen_tree(args: Any, **kwargs: Any) -> Tuple[Any, Optional[TreeJob]]:
    """``subprocess.Popen(args, **kwargs)``, and on Windows the
    :class:`TreeJob` that holds the child's whole tree.

    The job is ``None`` off Windows, and on Windows where no job could be made
    or the child could not be put in one; the caller then kills as before
    (:func:`end_tree` falls back to :func:`taskkill_tree`). With a job, the
    child is created suspended (``CREATE_SUSPENDED`` is added to any
    *creationflags*), put in the job, and resumed: a job assigned after the
    child started could miss a grandchild it had already spawned. A child that
    cannot be resumed is killed and ``OSError`` is raised, so no spawn is ever
    left suspended. The caller owns the job and closes it once the child is
    done with (:meth:`TreeJob.close`).
    """
    spawn = subprocess.Popen
    api = _job_api() if IS_WINDOWS and spawn is _REAL_POPEN else None
    job_handle: Optional[int] = None
    if api is not None:
        try:
            job_handle = api.create()
        except Exception:  # noqa: BLE001 - no job: spawn as before
            job_handle = None
    if api is None or job_handle is None:
        return spawn(args, **kwargs), None
    return _popen_in_job(api, job_handle, spawn, args, kwargs)


class _NotResumed(OSError):
    """A child created suspended for its job could not be resumed, and was
    killed before it ran an instruction (:func:`_popen_in_job`)."""


def _popen_in_job(
    api: Any, job_handle: int, spawn: Callable[..., Any], args: Any,
    kwargs: Dict[str, Any],
) -> Tuple[Any, Optional[TreeJob]]:
    """*spawn* the child suspended, put it in the job *job_handle* names, and
    resume it: :func:`popen_tree`'s spawn, and the detached run's
    (:func:`_spawn_detached_windows`).

    The job handle is the callee's from here on: closed when the spawn fails
    or the child cannot join (the job is then ``None`` and the child runs
    without one), else handed back in the :class:`TreeJob`. A child that
    cannot be resumed is killed and :class:`_NotResumed` raised.
    """
    flags = int(kwargs.pop("creationflags", 0) or 0) | _CREATE_SUSPENDED
    try:
        proc = spawn(args, creationflags=flags, **kwargs)
    except BaseException:
        api.close(job_handle)
        raise
    job: Optional[TreeJob] = TreeJob(api, job_handle)
    resumed = False
    # Popen's own handle has every right CreateProcess grants; opening another
    # is only for a Popen that keeps none, and that one is closed again.
    process: Optional[int] = getattr(proc, "_handle", None)
    opened = process is None
    try:
        if opened:
            process = api.open_process(proc.pid)
        if process is not None:
            if not api.assign(job_handle, process):
                # Already in a job that cannot nest one (Windows 7, a job with
                # UI limits): the child runs, and taskkill stays its kill.
                job.close()
                job = None
            resumed = api.resume(process)
    except Exception:  # noqa: BLE001 - settled below: resumed, or killed
        pass
    finally:
        if opened and process is not None:
            try:
                api.close(process)
            except Exception:  # noqa: BLE001
                pass
    if not resumed:
        _discard_suspended(proc)
        if job is not None:
            job.close()
        raise _NotResumed(
            f"pid {proc.pid} was created suspended to enter its Job Object, and "
            "could not be resumed; it was killed"
        )
    return proc, job


def _discard_suspended(proc: Any) -> None:
    """Kill and reap a child that never ran, and close its pipes."""
    try:
        proc.kill()
    except OSError:
        pass
    for stream in (proc.stdin, proc.stdout, proc.stderr):
        try:
            if stream is not None:
                stream.close()
        except (OSError, ValueError):
            pass
    try:
        proc.wait(timeout=5.0)
    except Exception:  # noqa: BLE001 - killed; the handle goes with the object
        pass


def end_tree(pid: int, job: Optional[TreeJob] = None, *, timeout: float = 30.0) -> None:
    """Kill *pid*'s whole tree now: its *job* when it has one that can still
    be terminated, else :func:`taskkill_tree` with *timeout*."""
    if job is not None and job.terminate():
        return
    taskkill_tree(pid, timeout=timeout)


# ---------------------------------------------------------------------------
# Windows: one named Job Object per detached run (2026-10-25)
# ---------------------------------------------------------------------------
#
# A `TreeJob` is a handle, and a handle does not cross processes. The kills of
# a detached run are made by whoever reads its `.status.json` or registry entry
# (`status --abort`, a close-out, `util runs --sweep`), so they all still ended
# in `taskkill /T`, with its unrelated-orphan risk. A run's job therefore has a
# name, derived from its run id, the uuid4 the launcher mints just before the
# spawn: `Local\multi-llm-run-<run_id>` (`run_job_name`).
#
# * The launcher creates the job and spawns the worker into it from its first
#   instruction, as `popen_tree` does (`spawn_detached_run`): `uv`, its `.cmd`
#   shim or trampoline, the worker python and everything under them are in it.
#   It holds its handle until the handshake resolves, so a failed handshake
#   ends exactly that tree, then closes it, which never kills.
# * The worker opens the job and holds the handle for life (`_hold_run_job`,
#   from `enter_detached_worker`). That handle is what keeps the job findable:
#   a temporary kernel object has a name only while its handle count is above
#   zero (the WDK, `ZwMakeTemporaryObject`), and processes in a job hold no
#   handle to it. With the launcher's handle closed and no worker handle, the
#   job lives on, nameless. The run's job sets no limit; the worker's reaper
#   stays the anonymous KILL_ON_JOB_CLOSE job of `_assign_own_job_object`,
#   which nests inside it. So a worker's normal exit kills nothing past what it
#   always did, and `uv` ends on its own.
# * An aborter opens the job by name for TERMINATE and QUERY only, trusts it
#   only if a live recorded pid is in it (`open_run_job`), and kills through it
#   (`kill_run_tree`). A dead recorded pid trusts the name: a job by that name
#   still exists only while some process holds a handle to it.
#
# `Local\`, not `Global\`. The session namespace holds the launcher, its worker
# (a child keeps its parent's session) and the user's `status`; a job's
# processes must all run in one session anyway. A sweep from another session
# (a service, a second logon) cannot see the name and kills by `taskkill` as
# before. `Global\` would let any session see it, and squat it.
#
# Squatting. The run id is unguessable before the launch, and still: a name
# that exists when the launcher creates it is never used (`ERROR_ALREADY_
# EXISTS`), and the worker uses an existing job only if it is already in it.
#
# No job here ever sets JOB_OBJECT_LIMIT_BREAKAWAY_OK, for the reason in the
# section above: the SILENT_BREAKAWAY_OK jobs of the venv launcher, uv's
# trampolines and libuv let their children leave only up to the first job that
# does not permit it, which is ours. Nesting needs Windows 8.

#: The run job's name is this prefix and the run id.
_RUN_JOB_PREFIX = "Local\\multi-llm-run-"

#: What a run id may hold to name a job. A uuid4 always does; a name may not
#: hold a backslash after its prefix, and is capped at MAX_PATH characters.
_RUN_ID_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
)
_RUN_ID_MAX = 128

#: The worker's own handles on its run job, by name: held for its lifetime,
#: like ``_JOB_HANDLE``, because the job's name lasts only while one is open.
_RUN_JOB_HANDLES: Dict[str, int] = {}


def run_job_name(run_id: Any) -> Optional[str]:
    """``Local\\multi-llm-run-<run_id>``, or ``None`` for a run id that cannot
    name a job (empty, too long, or holding anything but ASCII letters,
    digits, ``.``, ``_`` and ``-``)."""
    text = str(run_id) if run_id else ""
    if not text or len(text) > _RUN_ID_MAX or not set(text) <= _RUN_ID_CHARS:
        return None
    return _RUN_JOB_PREFIX + text


def _create_run_job(api: Any, run_id: Any) -> Optional[int]:
    """The launcher's half: a new job named for *run_id*, or ``None``.

    A name that already exists is someone else's job (the run id is minted
    just before this call), and is never used: its handle is closed and the
    worker spawns as before, with no job.
    """
    name = run_job_name(run_id)
    if name is None:
        return None
    try:
        handle, existed = api.create_named(name)
    except Exception:  # noqa: BLE001 - no job: spawn as before
        return None
    if handle is not None and existed:
        try:
            api.close(handle)
        except Exception:  # noqa: BLE001
            pass
        return None
    return handle


def _hold_run_job(run_id: Any) -> bool:
    """The worker's half: open (or create) its run's job and hold it for life.

    ``True`` when this process now holds a handle on a job named for *run_id*
    that it is in. The launcher's job is normally there already, with this
    process in it since its first instruction; an existing job this process
    is *not* in is a squatter's, and is let go of. With no job of that name
    (a worker launched some other way, or one whose launcher could not make
    the job) the worker creates it and joins it, so its tree is in it from
    here on. Never raises: ``False`` leaves the worker as it was, and an
    abort then kills by ``taskkill``.
    """
    name = run_job_name(run_id)
    if name is None:
        return False
    if name in _RUN_JOB_HANDLES:
        return True
    api = _job_api()
    if api is None:
        return False
    handle: Optional[int] = None
    held = False
    try:
        handle, existed = api.create_named(name)
        if handle is not None:
            me = api.current_process()
            if existed:
                held = api.in_job(me, handle) is True
            else:
                held = api.assign(handle, me)
    except Exception:  # noqa: BLE001 - not held: as before
        held = False
    if not held:
        if handle is not None:
            try:
                api.close(handle)
            except Exception:  # noqa: BLE001
                pass
        return False
    _RUN_JOB_HANDLES[name] = handle
    return True


def open_run_job(run_id: Any, pid: Optional[int] = None) -> Optional[TreeJob]:
    """An aborter's handle on a detached run's job, or ``None``.

    ``None`` off Windows (no call is made at all), for a run id that names no
    job, when no job of that name can be opened (the worker never held one,
    or it is gone, or the caller is in another session), and when the
    recorded *pid* is alive but not in the job: a live pid that is not the
    run's is a recycled one, or the job is a squatter's. A recorded pid that
    is already dead trusts the name. The caller closes the job
    (:meth:`TreeJob.close`, never a kill) when the kill is done; ``None``
    leaves it the ``taskkill`` it had.
    """
    if not IS_WINDOWS:
        return None
    try:
        name = run_job_name(run_id)
        api = _job_api() if name is not None else None
        if api is None:
            return None
        handle = api.open_named(name, _JOB_OBJECT_TERMINATE | _JOB_OBJECT_QUERY)
    except Exception:  # noqa: BLE001 - no job: taskkill
        return None
    if handle is None:
        return None
    job = TreeJob(api, handle)
    try:
        alive = bool(pid) and process_alive(int(pid))
        # A "no" is re-checked: a worker that exits between the two looks fails
        # the membership query only because it is gone, and a dead pid trusts
        # the name. One still alive and not in the job is not the run's.
        trusted = (not alive or _pid_in_job(api, int(pid), handle)
                   or not process_alive(int(pid)))
    except Exception:  # noqa: BLE001
        trusted = False
    if not trusted:
        job.close()
        return None
    return job


def _pid_in_job(api: Any, pid: int, job_handle: int) -> bool:
    """Is *pid* in the job? Only a definite yes counts."""
    try:
        process = api.query_process(pid)
    except Exception:  # noqa: BLE001
        return False
    if process is None:
        return False
    try:
        return api.in_job(process, job_handle) is True
    except Exception:  # noqa: BLE001
        return False
    finally:
        try:
            api.close(process)
        except Exception:  # noqa: BLE001
            pass


def kill_run_tree(run_id: Any, pid: int, **kwargs: Any) -> str:
    """:func:`kill_tree` for a detached run known by its record, through the
    run's named job when one opens (:func:`open_run_job`).

    *kwargs* go to :func:`kill_tree` as they are, and without a job (always,
    off Windows) the call is exactly the ``kill_tree(pid, **kwargs)`` it
    replaces. With one, the graceful phase is unchanged and only the
    escalation's kill is the job's; the job is closed afterwards either way.
    """
    try:
        job = open_run_job(run_id, pid)
    except Exception:  # noqa: BLE001 - a kill path never raises for its job
        job = None
    if job is None:
        return kill_tree(pid, **kwargs)
    try:
        return kill_tree(pid, job=job, **kwargs)
    finally:
        job.close()


def _send_ctrl_break(pid: int) -> None:  # pragma: no cover - Windows
    """``CTRL_BREAK_EVENT`` to the console process group *pid* leads."""
    try:
        import ctypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        CTRL_BREAK_EVENT = 1
        kernel32.GenerateConsoleCtrlEvent(CTRL_BREAK_EVENT, pid)
    except Exception:
        pass


def _windows_kill_tree(
    pid: int, escalate_after_s: float, job: Optional[TreeJob] = None,
) -> str:  # pragma: no cover
    _send_ctrl_break(pid)
    deadline = time.time() + max(escalate_after_s, 0.0)
    while time.time() < deadline:
        if not process_alive(pid):
            # The leader took the break; the job takes what it left running,
            # which is only ever its own tree.
            if job is not None:
                job.terminate()
            return "killed"
        time.sleep(0.1)
    # A group-less kill would strand the provider CLIs, so escalate to the whole
    # child tree.
    end_tree(pid, job)
    deadline = time.time() + 5.0
    while time.time() < deadline:
        if not process_alive(pid):
            return "killed"
        time.sleep(0.1)
    return "survived" if process_alive(pid) else "killed"


# ---------------------------------------------------------------------------
# A stopped CLI's detached descendants (plan: review-run-scope-salvage-and-
# failure-visibility D3.3)
# ---------------------------------------------------------------------------
#
# A Lane A provider CLI stays in the orchestrator's own process group — moving it
# into a session of its own would stop a terminal Ctrl-C from reaching it — so
# `kill_tree` on its group is not an option, and a signal to the CLI alone misses
# every child that left the group. pi's bash tool is the measured case: each
# shell is spawned `detached: true` (a session and group of its own), and GNU
# `timeout` inside it moves into yet another group. Once the CLI dies those
# children reparent to init and nothing links them to the slot any more, so the
# tree is SNAPSHOTTED (pid, pgid, sid, start time) while the CLI is still alive,
# and every snapshotted group is swept afterwards under `kill_tree`'s identity
# rule: a member's recorded start time is re-checked before anything is sent,
# so a recycled pid is never signalled. The groups are signalled together and
# share one grace and one SIGKILL window — a sweep's cost does not grow with
# the number of groups, which is what lets an abort bound it (below).
#
# Windows (2026-10-25). There are no groups or sessions to snapshot, so
# `descendants` is `[]` there, and a stop used to reach the CLI alone: its
# `TerminateProcess`. That is enough under a detached worker, whose own
# KILL_ON_JOB_CLOSE job reaps the tree when the worker exits, and nowhere else:
# a foreground run's CLI left its children running past the timeout, holding the
# inherited pipes until the drain's cap. So the CLI now starts in a `TreeJob` of
# its own (`popen_tree`, from `llm_client._run_provider_cli`), and every stop —
# the timeout, an interrupt, a stop from outside, the registry's sweep — ends
# that job right after the CLI's own stop (`_end_job`): one `TerminateJobObject`,
# which reaches exactly what the CLI started and nothing else. A job changes
# nothing about a terminal Ctrl-C: the console delivers that to every process
# attached to it, and only CREATE_NEW_PROCESS_GROUP (which disables Ctrl-C for
# the new group) or the process's own handler list decide who acts on it.
# `popen_tree` adds CREATE_SUSPENDED and no group, so the CLI still gets it. A
# CLI that exits on its own keeps its job untouched (closing it is never a
# kill), as a POSIX CLI's groups are left alone.

#: :attr:`TreeSweep.job`'s verdicts (2026-10-25): ``TerminateJobObject``
#: succeeded, so every process still in the CLI's job was ended — its whole
#: tree, the CLI included; or it did not (the call failed, or the handle was
#: already closed), and what the CLI started may still run.
JOB_TERMINATED = "terminated"
JOB_FAILED = "failed"

#: How long :func:`terminate_timed_out` waits between the CLI's SIGTERM and its
#: SIGKILL, and between each snapshotted group's. SIGTERM first is the point:
#: pi reaps its own tracked shells only from its SIGTERM/SIGHUP handler, which a
#: bare SIGKILL never runs. Short, because the slot has already spent its budget.
DEFAULT_TERMINATE_GRACE_S = 2.0

#: How long the CLI gets to die after its SIGKILL before it is reported
#: ``survived`` (a process in uninterruptible sleep can outlast a SIGKILL).
_KILL_CONFIRM_S = 5.0

#: The whole wall clock :meth:`LiveCliRegistry.sweep` may spend by default. The
#: abort's sweep runs inside the detached worker's SIGTERM handler while
#: ``detach.abort_run``'s :func:`kill_tree` counts :data:`DEFAULT_ESCALATE_AFTER_S`
#: down to the SIGKILL that ends the worker, and every signal the sweep still
#: owes a detached group dies with it — so the sweep has to be *finished*, not
#: merely started, well inside that window. What is left over is the worker's
#: own close-out (``RunHandle.finish``) after the sweep returns.
LIVE_SWEEP_BUDGET_S = DEFAULT_ESCALATE_AFTER_S - 3.0

#: The least a sweep's poll sleeps, as a share of its interval, however long
#: its look at the process table took (:func:`_wait_targets`).
_POLL_SLEEP_FLOOR_SHARE = 0.2

#: The share of a bounded sweep's budget the SIGTERM graces may use. The SIGKILL
#: that follows goes out by then at the latest, leaving the rest of the budget
#: for it to land and be confirmed.
_SWEEP_TERM_SHARE = 0.75

#: How often :data:`live_cli_registry` re-snapshots every live CLI's tree. The
#: registry's snapshot is what an abort or a terminal Ctrl-C sweeps, and both of
#: those signal the CLI at the same moment they signal this process — so by the
#: time a handler here runs, the CLI may already be dead and its children
#: reparented. One ``/proc`` scan serves every live CLI (~10 ms for ~1300
#: processes, measured 2026-09-28); a child started less than one interval
#: before the signal is the residual gap.
LIVE_SNAPSHOT_INTERVAL_S = 1.0


class Descendant(NamedTuple):
    """One process below a CLI, as it was when the snapshot was taken."""

    pid: int
    pgid: Optional[int]
    sid: Optional[int]
    #: The same string :func:`process_start_time` returns, so :func:`probe` can
    #: corroborate it later; ``None`` when the platform could not say.
    start_time: Optional[str]


class _ProcRow(NamedTuple):
    pid: int
    ppid: int
    pgid: Optional[int]
    sid: Optional[int]
    start_time: Optional[str]
    #: The state letter (``/proc``'s, or the first of ``ps``'s ``stat``); ``Z``
    #: is a zombie (dead, not yet reaped). ``None`` where ``ps`` could not say.
    state: Optional[str] = None


def _linux_process_table() -> Optional[Dict[int, _ProcRow]]:
    """Every process from one pass over ``/proc/*/stat``, or ``None`` without /proc."""
    try:
        names = os.listdir("/proc")
    except OSError:
        return None
    if "self" not in names:
        return None
    table: Dict[int, _ProcRow] = {}
    for name in names:
        if not name.isdigit():
            continue
        try:
            with open(f"/proc/{name}/stat", "rb") as handle:
                raw = handle.read()
        except OSError:
            continue  # exited between listdir and open
        # comm (field 2) is parenthesised and may itself contain ')'.
        close = raw.rfind(b")")
        fields = raw[close + 2:].split() if close != -1 else []
        if len(fields) <= 19:
            continue
        try:
            # After comm: state(3) ppid(4) pgrp(5) session(6) … starttime(22).
            table[int(name)] = _ProcRow(
                pid=int(name),
                ppid=int(fields[1]),
                pgid=int(fields[2]),
                sid=int(fields[3]),
                start_time=fields[19].decode("ascii", "replace"),
                state=fields[0].decode("ascii", "replace"),
            )
        except ValueError:
            continue
    return table


#: The ``ps`` columns :func:`_ps_process_table` asks for, each as its own ``-o``
#: (POSIX reads everything after a ``name=`` as that column's header, commas
#: included). ``lstart`` is last because it is several words.
_PS_TABLE_COLUMNS = ("pid", "ppid", "pgid", "stat", "lstart")


def _ps_process_table() -> Dict[int, _ProcRow]:
    """The ``ps`` walk for POSIX without /proc (macOS, the BSDs).

    ONE ``ps -A`` gives the tree and every start time. :data:`live_cli_registry`
    re-walks this table every :data:`LIVE_SNAPSHOT_INTERVAL_S` for as long as a
    CLI runs, so nothing here may cost a spawn per process: the start time used
    to come from a ``ps -o lstart= -p <pid>`` per descendant, every second, for
    the whole of a fan-out. ``lstart`` is the column :func:`_ps_start_time`
    reads, so a row's start time is the string :func:`process_start_time`
    returns for that pid — its internal spacing kept, since ``%e`` pads a
    one-digit day — and :func:`probe` can corroborate it at sweep time. ``stat``
    gives the state a sweep needs to tell a zombie from a process that runs
    (``kill(pid, 0)`` and ``killpg`` answer for both, here as on Linux). The
    session id is left to :func:`_complete_row` (``os.getsid``, a system call,
    not a spawn), because ``ps`` spells it differently on every platform. A
    ``ps`` that rejects ``lstart`` still yields the tree, undated.
    """
    for columns in (_PS_TABLE_COLUMNS, _PS_TABLE_COLUMNS[:4], _PS_TABLE_COLUMNS[:3]):
        argv = ["ps", "-A"]
        for column in columns:
            argv += ["-o", f"{column}="]
        try:
            result = subprocess.run(
                argv, capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=10,
            )
        except (OSError, subprocess.SubprocessError):
            return {}
        if result.returncode == 0:
            return _parse_ps_table(result.stdout, columns)
    return {}


def _parse_ps_table(
    stdout: str, columns: Sequence[str] = _PS_TABLE_COLUMNS
) -> Dict[int, _ProcRow]:
    table: Dict[int, _ProcRow] = {}
    for line in stdout.splitlines():
        parts = line.split(None, len(columns) - 1)
        if len(parts) < 3:
            continue
        try:
            pid, ppid, pgid = (int(part) for part in parts[:3])
        except ValueError:
            continue
        extra = dict(zip(columns[3:], parts[3:]))
        state = extra.get("stat", "")[:1] or None
        start = extra.get("lstart", "").strip()
        table[pid] = _ProcRow(pid, ppid, pgid, None, start or None, state)
    return table


def _process_table() -> Dict[int, _ProcRow]:
    """Every process: ``/proc`` on Linux, one ``ps -A`` elsewhere, ``{}`` on
    Windows or when neither could be read."""
    if IS_WINDOWS:  # pragma: no cover - Windows
        return {}
    table = _linux_process_table()
    if table is None:
        table = _ps_process_table()
    return table


#: The last ``ps`` table a waiting poll read, with the monotonic times its read
#: began and ended (round-8 review, 2026-10-24). Off Linux a look at the process table is
#: a ``ps -A`` spawn, tens of milliseconds once hundreds of processes run, and
#: sweeps that wait at the same time (a fan-out's slots timing out together)
#: each spawned their own on every poll. :func:`_waiting_process_table` shares
#: one read between them; nothing that decides a signal or a verdict reads it.
_SHARED_PS_TABLE: List[Tuple[float, float, Dict[int, _ProcRow]]] = []
_SHARED_PS_TABLE_LOCK = threading.Lock()


def _waiting_process_table(not_before: float, max_age_s: float) -> Dict[int, _ProcRow]:
    """:func:`_process_table` for a poll that only waits for processes to end.

    Linux reads ``/proc`` as always. Off Linux the last shared ``ps`` table is
    reused when its read began at or after *not_before* (the wait's own start,
    so it never predates the signals being waited on) and ended less than
    *max_age_s* ago (the poll interval: a reused table is no staler than the
    poll that would have read it). One read at a time, so a poll that waited
    for another's read takes that table instead of spawning a second ``ps``:
    its age counts from the read's end, or a ``ps`` slower than the interval
    would be stale on arrival and every waiter behind it would spawn its own.
    """
    if IS_WINDOWS:  # pragma: no cover - Windows
        return {}
    table = _linux_process_table()
    if table is not None:
        return table
    with _SHARED_PS_TABLE_LOCK:
        if _SHARED_PS_TABLE:
            began, ended, shared = _SHARED_PS_TABLE[0]
            if began >= not_before and ended >= time.monotonic() - max_age_s:
                return shared
        began = time.monotonic()
        table = _ps_process_table()
        if table:
            _SHARED_PS_TABLE[:] = [(began, time.monotonic(), table)]
        return table


def _complete_row(row: _ProcRow) -> Descendant:
    # Both tables date their rows, so this per-pid start-time probe (a spawn off
    # Linux) is reached only for a row the table could not date.
    sid = row.sid
    if sid is None:
        try:
            sid = os.getsid(row.pid)
        except (OSError, AttributeError):
            sid = None
    start = row.start_time if row.start_time is not None else process_start_time(row.pid)
    return Descendant(row.pid, row.pgid, sid, start)


def _descendants_in(table: Dict[int, _ProcRow], pid: int) -> List[Descendant]:
    children: Dict[int, List[int]] = {}
    for row in table.values():
        children.setdefault(row.ppid, []).append(row.pid)
    found: List[Descendant] = []
    seen = {pid}
    queue = sorted(children.get(pid, ()))
    while queue:
        child = queue.pop(0)
        if child in seen or child not in table:
            continue
        seen.add(child)
        found.append(_complete_row(table[child]))
        queue.extend(sorted(children.get(child, ())))
    return found


def descendants(pid: int) -> List[Descendant]:
    """(pid, pgid, sid, start time) for every live descendant of *pid*.

    Linux reads ``/proc/*/stat`` once; other POSIX platforms run one ``ps -A``
    for pid, ppid, pgid and ``lstart``; Windows returns an empty list (its tree
    is a Job Object: a Lane A CLI's own :class:`TreeJob`, which every stop ends,
    and under a detached worker the worker's job too, D4d). Breadth-first,
    *pid* itself excluded. The walk follows parent links, which is exactly why
    it must run **before** the CLI dies: afterwards its children belong to init.
    """
    if IS_WINDOWS or not pid or pid <= 0:  # pragma: no cover - Windows leg
        return []
    return _descendants_in(_process_table(), int(pid))


def _merge_snapshots(*snapshots: Sequence[Descendant]) -> List[Descendant]:
    """One entry per (pid, start time), first-seen order."""
    merged: List[Descendant] = []
    seen = set()
    for snapshot in snapshots:
        for entry in snapshot or ():
            key = (entry.pid, entry.start_time)
            if key in seen:
                continue
            seen.add(key)
            merged.append(entry)
    return merged


@dataclass
class TreeSweep:
    """What :func:`terminate_timed_out` did, for the log line that names it.

    ``cli`` is the CLI's own verdict: ``exited`` (already gone, nothing sent),
    ``terminated`` (exited within the grace after SIGTERM), ``killed`` (needed
    the SIGKILL) or ``survived``. ``groups`` maps each snapshotted process group
    to its verdict, in :func:`kill_tree`'s vocabulary (``gone``, ``killed``,
    ``survived``, ``skipped``), in the order the snapshot met them.

    ``job`` is what ending the CLI's Windows Job Object did (2026-10-25):
    :data:`JOB_TERMINATED` or :data:`JOB_FAILED`, and ``None`` where there was
    no job to end — every POSIX run (:func:`popen_tree` makes one only on
    Windows) and a Windows CLI that could not be put in one. ``None`` leaves
    :meth:`describe` word for word what it was, so a POSIX log line does not
    change.
    """

    cli: str
    groups: Dict[int, str] = field(default_factory=dict)
    job: Optional[str] = None

    @property
    def survived(self) -> List[int]:
        return [pgid for pgid, verdict in self.groups.items() if verdict == "survived"]

    def describe(self) -> str:
        line = f"cli {self.cli}"
        if self.job is not None:
            line += f"; job {self.job}"
        if self.groups:
            verdicts = ", ".join(f"{pgid} {verdict}" for pgid, verdict in self.groups.items())
            line += f"; process groups: {verdicts}"
        elif self.job is None:
            # Windows snapshots no groups, so with a job to name this would only
            # repeat what the job's verdict already says.
            line += "; no descendant process groups"
        if self.survived:
            line += (" — SURVIVED: " + ", ".join(str(pgid) for pgid in self.survived)
                     + " still running")
        if self.job == JOB_FAILED:
            line += " — JOB NOT ENDED: what the cli started may still be running"
        return line


def _exited(proc: Any) -> bool:
    try:
        return proc.poll() is not None
    except OSError:  # pragma: no cover - reaped behind Popen's back
        return True


def _wait_exit(proc: Any, timeout_s: float, poll_interval_s: float) -> bool:
    deadline = time.monotonic() + max(timeout_s, 0.0)
    while True:
        if _exited(proc):
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(poll_interval_s)


def _signal_cli(proc: Any) -> bool:
    """SIGTERM the CLI alone (never its group: that group is this process's).

    ``False`` when it had already exited, so nothing was sent.
    """
    try:
        if proc.poll() is not None:
            return False
        proc.terminate()
    except OSError:
        return False
    return True


def _await_cli(proc: Any, signalled: bool, grace_s: float, poll_interval_s: float) -> str:
    if not signalled:
        return "exited"
    if _wait_exit(proc, grace_s, poll_interval_s):
        return "terminated"
    try:
        proc.kill()
    except OSError:
        pass
    return "killed" if _wait_exit(proc, _KILL_CONFIRM_S, poll_interval_s) else "survived"


def _end_job(job: Optional[TreeJob]) -> Optional[str]:
    """Terminate a stopped CLI's :class:`TreeJob`; its :attr:`TreeSweep.job` verdict.

    ``None`` when there is none (POSIX, or a Windows CLI that got no job), so
    the stop is exactly what it was without one. Never raises, and never
    closes the job: the call that spawned the CLI owns the handle and closes it
    once it is done waiting (2026-10-25).
    """
    if job is None:
        return None
    try:
        return JOB_TERMINATED if job.terminate() else JOB_FAILED
    except Exception:  # noqa: BLE001 - a teardown step never raises
        return JOB_FAILED


def _worst(verdicts: Sequence[str]) -> str:
    for verdict in ("survived", "killed", "skipped"):
        if verdict in verdicts:
            return verdict
    return "gone"


def _linux_state(pid: int) -> Optional[str]:
    try:
        with open(f"/proc/{pid}/stat", "rb") as handle:
            raw = handle.read()
    except OSError:
        return None
    close = raw.rfind(b")")
    fields = raw[close + 2:].split() if close != -1 else []
    return fields[0].decode("ascii", "replace") if fields else None


def _running(pid: int) -> bool:
    """Alive and not a zombie (a zombie keeps its pid and group, runs nothing).

    The per-pid answer, for a sweep whose process table could not be read
    (:class:`_Liveness`); it needs ``/proc`` to see a zombie.
    """
    return process_alive(pid) and _linux_state(pid) != "Z"


def _group_running(pgid: int) -> bool:
    """Does any process that is not a zombie still belong to *pgid*?

    ``killpg(pgid, 0)`` succeeds for a group of zombies too, so the answer comes
    from ``/proc``; where that cannot be read, membership is the best available.
    """
    if not _group_has_members(pgid):
        return False
    table = _linux_process_table()
    if table is None:  # pragma: no cover - non-Linux POSIX
        return True
    return any(row.pgid == pgid and row.state != "Z" for row in table.values())


class _SweepClock:
    """When a sweep's SIGTERM graces must end, and when the sweep itself must.

    Unbounded (``budget_s=None``) is the timeout path's clock: every grace runs
    in full and a SIGKILL gets :data:`_KILL_CONFIRM_S` to land. Bounded, every
    wait is clipped — the graces to :data:`_SWEEP_TERM_SHARE` of the budget, so
    the SIGKILLs still go out with time to land, and the confirmations to the
    budget itself.
    """

    def __init__(self, budget_s: Optional[float] = None):
        now = time.monotonic()
        self.term_by: Optional[float] = None
        self.deadline: Optional[float] = None
        if budget_s is not None:
            budget = max(float(budget_s), 0.0)
            self.term_by = now + budget * _SWEEP_TERM_SHARE
            self.deadline = now + budget

    def grace_until(self, grace_s: float) -> float:
        end = time.monotonic() + max(grace_s, 0.0)
        return end if self.term_by is None else min(end, self.term_by)

    def confirm_until(self) -> float:
        end = time.monotonic() + _KILL_CONFIRM_S
        return end if self.deadline is None else min(end, self.deadline)


class _Liveness:
    """One look at what still runs, shared by every group a poll checks.

    One process-table scan per poll however many groups are waited on — the
    ``/proc`` pass, or off Linux one ``ps -A`` — and each question falls back to
    its own per-pid probe only where neither could be read. "Running" never
    counts a zombie: an unreaped leader still answers ``kill(pid, 0)`` (macOS
    too), and a wait that trusted that would sit out its whole window on a
    process already dead.

    *not_before* marks a look that only waits (:func:`_wait_targets`): off
    Linux it may share a ``ps`` table read since then and within *max_age_s*
    (:func:`_waiting_process_table`). Every other look reads a fresh one.
    """

    def __init__(self, not_before: Optional[float] = None, max_age_s: float = 0.0) -> None:
        try:
            table = (_process_table() if not_before is None
                     else _waiting_process_table(not_before, max_age_s))
            self.table: Optional[Dict[int, _ProcRow]] = table or None
        except Exception:  # noqa: BLE001 - the per-pid probes still answer
            self.table = None
        self._groups = None if self.table is None else {
            row.pgid for row in self.table.values() if row.state != "Z"
        }

    def pid_running(self, pid: int) -> bool:
        """Running, whoever it is now."""
        if self.table is None:
            return _running(pid)
        row = self.table.get(pid)
        return row is not None and row.state != "Z"

    def corroborated(self, member: Descendant) -> bool:
        """Running, and still the process the snapshot recorded (start time)."""
        if self.table is None:
            return probe(member.pid, member.start_time) == ALIVE and _running(member.pid)
        row = self.table.get(member.pid)
        return (row is not None and row.state != "Z" and bool(member.start_time)
                and str(row.start_time) == str(member.start_time))

    def group_running(self, pgid: int) -> bool:
        if self._groups is None:
            return _group_running(pgid)
        return pgid in self._groups

    def pgid_of(self, pid: int) -> Optional[int]:
        """The group *pid* is in now, or ``None`` when that cannot be read."""
        if self.table is None:
            try:
                return os.getpgid(pid)
            except (OSError, AttributeError):
                return None
        row = self.table.get(pid)
        return row.pgid if row is not None else None


@dataclass
class _GroupTarget:
    """One snapshotted process group's part in :func:`_sweep_snapshots`.

    A member is *corroborated* when its pid is running (not a zombie) with the
    start time the snapshot recorded. None corroborated: ``skipped`` (no signal
    at all) if a pid is running but is not the process the snapshot saw — a
    recycled pid's group is an unrelated group — else ``gone``: every member is
    dead, or dead and not yet reaped, which is the same thing to a signal.

    A signalled group's corroborated members are also watched one by one
    (``watched``), because the group a member was snapshotted in need not be
    the group it is in now: GNU ``timeout`` calls ``setpgid`` right after exec,
    and the registry's snapshot that an abort or an outside kill sweeps can be
    up to :data:`LIVE_SNAPSHOT_INTERVAL_S` old. A signal to the recorded group
    never reaches such a member, so it is stopped by pid and start time the way
    :func:`kill_tree` stops a pid (its live group, never ours), and its verdict
    folds into the group's: a recorded group swept empty while a member runs on
    elsewhere is ``survived``, never ``killed``.
    """

    key: int
    members: List[Descendant]
    #: The group signalled whole, or ``None`` when each corroborated member is
    #: stopped on its own (``alone``): a child that stayed in the CLI's group
    #: stayed in OURS, which is never signalled (a self-kill) — and
    #: :func:`_resolve_pgid` resolves no group for it for the same reason.
    pgid: Optional[int] = None
    leader: Optional[Descendant] = None
    alone: List[Descendant] = field(default_factory=list)
    #: The corroborated members of a group signalled whole (see above).
    watched: List[Descendant] = field(default_factory=list)
    verdict: Optional[str] = None

    def terminate(self, look: _Liveness, own: Optional[int]) -> None:
        """Corroborate, then SIGTERM — or settle a verdict that owes no signal."""
        corroborated = [m for m in self.members if look.corroborated(m)]
        if not corroborated:
            running = any(look.pid_running(m.pid) for m in self.members)
            self.verdict = "skipped" if running else "gone"
            return
        if self.key > 1 and self.key != own:
            self.pgid = self.key
            self.watched = corroborated
            self.leader = next((m for m in corroborated if m.pid == self.key),
                               corroborated[0])
            _signal_tree(self.leader.pid, self.pgid, signal.SIGTERM)
            for member in self.watched:
                if look.pgid_of(member.pid) != self.pgid:
                    _signal_tree(member.pid, None, signal.SIGTERM)
            return
        self.alone = corroborated
        for member in self.alone:
            _signal_tree(member.pid, None, signal.SIGTERM)

    def _group_or_watched_running(self, look: _Liveness, pgid: int) -> bool:
        """The group, else any watched member that runs outside it.

        The members are asked only once the group is empty, so off Linux a
        group that still runs costs no per-pid probe on each poll.
        """
        if look.group_running(pgid):
            return True
        return any(look.corroborated(m) for m in self.watched)

    def running(self, look: _Liveness) -> bool:
        try:
            if self.pgid is not None:
                return self._group_or_watched_running(look, self.pgid)
            return any(look.corroborated(m) for m in self.alone)
        except Exception:  # noqa: BLE001 - unknown is treated as still running
            return True

    def kill(self, look: _Liveness) -> None:
        """SIGKILL whatever still runs, sending nothing to a pid that moved on.

        The whole group goes, not just the member the grace watched: a member
        that shrugged off the SIGTERM its leader died of still gets it. So does
        a watched member that runs outside the group, by pid and start time.
        """
        if self.pgid is not None:
            if look.group_running(self.pgid):
                leader = self.leader if self.leader and look.corroborated(self.leader) else None
                _signal_tree(leader.pid if leader else None, self.pgid, signal.SIGKILL)
            for member in self.watched:
                if look.pgid_of(member.pid) != self.pgid and look.corroborated(member):
                    _signal_tree(member.pid, None, signal.SIGKILL)
            return
        for member in self.alone:
            if look.corroborated(member):
                _signal_tree(member.pid, None, signal.SIGKILL)

    def settle(self, look: _Liveness) -> str:
        if self.verdict is None:
            if self.pgid is not None:
                self.verdict = ("survived" if self._group_or_watched_running(look, self.pgid)
                                else "killed")
            else:
                self.verdict = _worst(["survived" if look.corroborated(m) else "killed"
                                       for m in self.alone])
        return self.verdict

    def fallback(self) -> str:
        """The verdict when one of this group's own steps raised."""
        return "survived" if any(
            probe(m.pid, m.start_time) == ALIVE for m in self.members
        ) else "gone"


def _wait_targets(
    targets: Sequence[_GroupTarget], until: float, poll_interval_s: float
) -> List[_GroupTarget]:
    """Poll until none of *targets* runs or *until* passes; return those still running.

    Each poll sleeps only what its look left of *poll_interval_s*, never less
    than :data:`_POLL_SLEEP_FLOOR_SHARE` of it: off Linux the look is a ``ps``
    spawn, and a whole interval slept after it sampled the grace about half
    as often as asked (round-8 review). The floor keeps a look that costs more
    than the interval from spawning ``ps`` back to back.
    """
    still = list(targets)
    began = time.monotonic()
    while still:
        looked = time.monotonic()
        look = _Liveness(not_before=began, max_age_s=poll_interval_s)
        still = [target for target in still if target.running(look)]
        now = time.monotonic()
        if not still or now >= until:
            break
        rest = max(poll_interval_s - (now - looked),
                   poll_interval_s * _POLL_SLEEP_FLOOR_SHARE)
        time.sleep(max(0.0, min(rest, until - now)))
    return still


def _sweep_snapshots(
    snapshots: Sequence[Sequence[Descendant]],
    grace_s: float,
    poll_interval_s: float,
    clock: _SweepClock,
) -> List[Dict[int, str]]:
    """Stop every group of every snapshot on one shared clock.

    Every group gets its SIGTERM before any is waited on; one grace covers them
    all; whatever still runs gets its SIGKILL in one pass; one confirmation
    window covers those. So a sweep costs one grace plus one confirmation however
    many groups there are. Swept one at a time, each group paid both — and a
    zombie leader could make one pay its confirmation in full — so an abort with
    enough detached groups ran past the SIGKILL that ends the worker and left the
    groups it had not reached yet running. Every wait is clipped by *clock*.
    Returns one ``{group: verdict}`` map per snapshot, in order.
    """
    try:
        own: Optional[int] = os.getpgid(0)
    except (OSError, AttributeError):  # pragma: no cover - Windows; never in practice
        own = None
    plans: List[List[_GroupTarget]] = []
    for snapshot in snapshots:
        by_group: Dict[int, List[Descendant]] = {}
        for entry in snapshot or ():
            key = entry.pgid if entry.pgid is not None else -entry.pid
            by_group.setdefault(key, []).append(entry)
        plans.append([_GroupTarget(key, members) for key, members in by_group.items()])
    targets = [target for plan in plans for target in plan]
    if targets:
        look = _Liveness()
        for target in targets:
            try:
                target.terminate(look, own)
            except Exception:  # noqa: BLE001 - one group must not stop the sweep
                target.verdict = target.fallback()
        live = [target for target in targets if target.verdict is None]
        live = _wait_targets(live, clock.grace_until(grace_s), poll_interval_s)
        if live:
            look = _Liveness()
            for target in live:
                try:
                    target.kill(look)
                except Exception:  # noqa: BLE001 - one group must not stop the sweep
                    pass
            _wait_targets(live, clock.confirm_until(), poll_interval_s)
        look = _Liveness()
        for target in targets:
            try:
                target.settle(look)
            except Exception:  # noqa: BLE001 - one group must not stop the sweep
                target.verdict = target.fallback()
    return [{target.key: str(target.verdict) for target in plan} for plan in plans]


def _sweep_groups(
    snapshot: Sequence[Descendant], grace_s: float, poll_interval_s: float
) -> Dict[int, str]:
    return _sweep_snapshots([snapshot], grace_s, poll_interval_s, _SweepClock())[0]


def terminate_timed_out(
    proc: Any,
    snapshot: Sequence[Descendant],
    grace_s: float = DEFAULT_TERMINATE_GRACE_S,
    *,
    poll_interval_s: float = 0.05,
    job: Optional[TreeJob] = None,
) -> TreeSweep:
    """Stop a Lane A CLI and every process group its snapshot recorded.

    *proc* is the CLI's ``subprocess.Popen`` (``poll``/``terminate``/``kill``);
    *snapshot* is :func:`descendants` of it, taken **before** anything was
    signalled. SIGTERM to the CLI alone (it shares this process's group), the
    grace, SIGKILL if it is still alive; then every distinct snapshotted group
    together — SIGTERM, one shared *grace_s*, SIGKILL (:func:`_sweep_snapshots`)
    — under :func:`kill_tree`'s identity rule, each member's recorded start time
    re-checked, so a pid recycled since the snapshot is ``skipped`` and never
    signalled. Several groups, not one: pi's shell and a ``timeout`` inside it
    each lead their own. The Ctrl-C and abort paths run the same steps for every
    live CLI at once (:meth:`LiveCliRegistry.sweep`, decision 11.9). Never raises
    for a process that is already gone.

    *job* is the CLI's Windows :class:`TreeJob` (:func:`popen_tree`; ``None``
    elsewhere), the stand-in there for the snapshot Windows cannot take
    (2026-10-25). It is terminated right after the CLI's own stop, not after
    the grace, and whether or not the CLI was still running. The grace exists
    for a CLI that cleans up after itself on SIGTERM (pi reaps its shells from
    that handler); Windows has no SIGTERM, ``Popen.terminate`` is
    ``TerminateProcess``, and a CLI ended that way runs no cleanup at all. So a
    grace there would buy the CLI nothing and give its children two more
    seconds of quota and of holding the pipes the drain is waiting on. The
    verdict is :attr:`TreeSweep.job`; a job that fails to terminate leaves the
    stop what it was without one.
    """
    signalled = _signal_cli(proc)
    ended = _end_job(job)
    cli = _await_cli(proc, signalled, grace_s, poll_interval_s)
    return TreeSweep(cli=cli, groups=_sweep_groups(snapshot, grace_s, poll_interval_s),
                     job=ended)


@dataclass
class LiveCli:
    """One Lane A CLI this process is waiting on."""

    pid: int
    start_time: Optional[str]
    proc: Any
    snapshot: List[Descendant] = field(default_factory=list)
    #: The CLI's Windows :class:`TreeJob` (2026-10-25), what a sweep ends there
    #: in place of the snapshot; ``None`` elsewhere. The registry only ever
    #: terminates it, and only while the entry is registered: the call that
    #: spawned the CLI closes it, after :meth:`LiveCliRegistry.unregister`.
    job: Optional[TreeJob] = None


class LiveCliRegistry:
    """Every live Lane A CLI in this process, with its latest tree snapshot.

    Entries are added right before ``communicate()`` and removed in its
    ``finally``; a daemon thread re-snapshots every entry's descendants each
    :data:`LIVE_SNAPSHOT_INTERVAL_S` from ONE process-table scan, and exits when
    the registry is empty. The detached worker's SIGTERM handler calls
    :meth:`sweep` before it exits, so an abort takes the CLIs' detached children
    with it instead of leaving them to ``kill_tree`` on the worker's group, which
    never reaches a child in a session of its own.

    Safe to read from a signal handler: the lock is re-entrant (the handler runs
    on the main thread, which may already hold it) and never held across a scan.

    On Windows each entry carries its CLI's :class:`TreeJob` (``job``), and
    :meth:`sweep` ends those (2026-10-25). Each is terminated under the lock,
    and only while its entry is still registered. The spawning call closes its
    job only after it has unregistered, so a job is never terminated through a
    handle already closed, whose value Windows may since have handed to another
    slot's job. The lock is held across that one call, never a scan.
    """

    def __init__(self, interval_s: float = LIVE_SNAPSHOT_INTERVAL_S):
        self.interval_s = interval_s
        self._lock = threading.RLock()
        self._wake = threading.Condition(self._lock)
        self._entries: Dict[int, LiveCli] = {}
        self._thread: Optional[threading.Thread] = None

    def register(self, proc: Any, job: Optional[TreeJob] = None) -> LiveCli:
        entry = LiveCli(pid=int(proc.pid), start_time=process_start_time(proc.pid),
                        proc=proc, job=job)
        with self._lock:
            self._entries[id(proc)] = entry
            if not IS_WINDOWS and (self._thread is None or not self._thread.is_alive()):
                self._thread = threading.Thread(
                    target=self._refresh_loop, name="multi-llm-cli-tree-snapshot",
                    daemon=True,
                )
                self._thread.start()
        return entry

    def unregister(self, proc: Any) -> None:
        with self._lock:
            self._entries.pop(id(proc), None)
            self._wake.notify_all()

    @contextmanager
    def tracking(self, proc: Any, job: Optional[TreeJob] = None) -> Iterator[LiveCli]:
        """Registered, with *job*, for the ``with`` body; close *job* only after it."""
        entry = self.register(proc, job)
        try:
            yield entry
        finally:
            self.unregister(proc)

    def entries(self) -> List[LiveCli]:
        with self._lock:
            return list(self._entries.values())

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)

    def refresh(self) -> None:
        """Re-snapshot every entry from one scan. Identity-checked per entry."""
        entries = self.entries()
        if not entries:
            return
        table = _process_table()
        for entry in entries:
            row = table.get(entry.pid)
            if row is None:
                continue  # already gone: keep the last snapshot it had
            if entry.start_time and row.start_time and row.start_time != entry.start_time:
                continue  # the pid names someone else now
            fresh = _descendants_in(table, entry.pid)
            with self._lock:
                if id(entry.proc) in self._entries:
                    entry.snapshot = fresh

    def snapshot_for(self, proc: Any) -> List[Descendant]:
        """The last refreshed snapshot of *proc*'s tree, merged with a fresh one.

        The fresh walk runs only while *proc* is un-reaped (``returncode`` still
        ``None``): until then its pid cannot be recycled, so its children are
        still its own. Afterwards only the stored snapshot, whose start times
        protect every later signal, is used.
        """
        with self._lock:
            entry = self._entries.get(id(proc))
            stored = list(entry.snapshot) if entry else []
        fresh: List[Descendant] = []
        if getattr(proc, "returncode", 0) is None:
            fresh = descendants(proc.pid)
        return _merge_snapshots(fresh, stored)

    def sweep(
        self,
        grace_s: float = DEFAULT_TERMINATE_GRACE_S,
        *,
        poll_interval_s: float = 0.05,
        budget_s: Optional[float] = LIVE_SWEEP_BUDGET_S,
    ) -> List[Tuple[LiveCli, TreeSweep]]:
        """Terminate every registered CLI and sweep its snapshotted groups, on one clock.

        The abort that calls this is itself counting down to the SIGKILL that
        ends the worker, and a signal this sweep has not sent by then is never
        sent — so nothing here is paid per CLI or per group. All CLIs are
        signalled first and share one grace; the survivors are SIGKILLed in one
        pass; then every group of every snapshot is signalled before any is
        waited on, and they share one grace and one SIGKILL window
        (:func:`_sweep_snapshots`). Every wait is clipped to *budget_s*
        (:data:`LIVE_SWEEP_BUDGET_S`, inside the abort's window), the graces
        early enough that the SIGKILLs still go out within it; ``None`` leaves
        the sweep unbounded.

        On Windows every entry's :class:`TreeJob` is terminated right after the
        CLIs are signalled, before anything is waited on, for the reason
        :func:`terminate_timed_out` gives (2026-10-25): one call per job and no
        wait of its own, so the jobs cost the clock nothing, and every CLI's
        job is ended whether its CLI was still running or not.
        """
        clock = _SweepClock(budget_s)
        entries = self.entries()
        snapshots = [self.snapshot_for(entry.proc) for entry in entries]
        signalled = [_signal_cli(entry.proc) for entry in entries]
        jobs = [self._end_registered_job(entry) for entry in entries]
        waiting = [entry.proc for entry, sent in zip(entries, signalled) if sent]
        until = clock.grace_until(grace_s)
        for proc in waiting:
            _wait_exit(proc, until - time.monotonic(), poll_interval_s)
        killed: List[Any] = []
        for proc in waiting:
            if _exited(proc):
                continue
            try:
                proc.kill()
            except OSError:
                pass
            killed.append(proc)
        groups = _sweep_snapshots(snapshots, grace_s, poll_interval_s, clock)
        until = clock.confirm_until()
        for proc in killed:
            _wait_exit(proc, until - time.monotonic(), poll_interval_s)
        results: List[Tuple[LiveCli, TreeSweep]] = []
        for entry, sent, swept, ended in zip(entries, signalled, groups, jobs):
            if not sent:
                cli = "exited"
            elif not any(proc is entry.proc for proc in killed):
                cli = "terminated"
            else:
                cli = "killed" if _exited(entry.proc) else "survived"
            results.append((entry, TreeSweep(cli=cli, groups=swept, job=ended)))
        return results

    def _end_registered_job(self, entry: LiveCli) -> Optional[str]:
        """:func:`_end_job` on *entry*'s job, if *entry* is still registered.

        Under the lock, so the spawning call cannot unregister — and then close
        the handle — between the check and the terminate. An entry gone since
        :meth:`sweep` listed it belongs to a call that already returned; that
        call owns its job, and has closed it or is about to, so the verdict is
        ``None``: nothing was done to it here.
        """
        if entry.job is None:
            return None
        with self._lock:
            if self._entries.get(id(entry.proc)) is not entry:
                return None
            return _end_job(entry.job)

    def _refresh_loop(self) -> None:
        while True:
            with self._lock:
                if not self._entries:
                    self._thread = None
                    return
                self._wake.wait(self.interval_s)
                if not self._entries:
                    self._thread = None
                    return
            try:
                self.refresh()
            except Exception:  # noqa: BLE001 - a snapshot is best-effort
                pass


#: The process-wide registry every Lane A call registers its CLI in.
live_cli_registry = LiveCliRegistry()


def sweep_live_clis(tag: str) -> None:
    """Sweep :data:`live_cli_registry`, one ``[<tag>] cli pid N: …`` stderr line per CLI.

    A no-op when nothing is registered. Never raises: the interrupt that asked
    for it must still end the run and its result line must still be written.
    """
    try:
        swept = live_cli_registry.sweep()
    except Exception as exc:  # noqa: BLE001 - see above
        print(f"[{tag}] failed: {exc}", file=sys.stderr)
        return
    for entry, result in swept:
        print(f"[{tag}] cli pid {entry.pid}: {result.describe()}", file=sys.stderr)


async def sweeping_live_clis_on_interrupt(awaitable: Awaitable[_T]) -> _T:
    """Await *awaitable*; if a cancellation or Ctrl-C ends it, sweep the registry first.

    What ``asyncio.run`` is handed wherever a dispatch target's fan-out runs
    (decision 11.9). A slot waits on its CLI from an ``asyncio.to_thread`` worker,
    and ``asyncio.run`` raises its ``KeyboardInterrupt`` only after the runner
    has shut the default executor down, which joins every such worker. So a
    sweep left to the caller's ``except KeyboardInterrupt`` waits for each CLI to
    reach its own deadline whenever the SIGINT reached the orchestrator alone,
    or a CLI handled it without exiting. Here it runs on the way out of the
    coroutine, while the runner is still cancelling the main task: the CLIs are
    stopped, their workers return, and the executor shutdown that follows has
    nothing left to wait for.

    Both endings are caught: the first Ctrl-C arrives as the main task's
    cancellation (3.11+'s runner), a later one — or any Ctrl-C on 3.10 — as a
    ``KeyboardInterrupt`` raised wherever the main thread is, after which the
    runner's cancel-all reaches this frame as a cancellation too.
    """
    try:
        return await awaitable
    except (asyncio.CancelledError, KeyboardInterrupt):
        sweep_live_clis("INTERRUPT_SWEEP")
        raise


# ---------------------------------------------------------------------------
# Detached spawn
# ---------------------------------------------------------------------------

class SpawnFailed(Exception):
    """The detached spawn itself failed (before the worker ran)."""


def spawn_detached(
    argv: Sequence[str],
    *,
    cwd: str,
    env: Dict[str, str],
    log_path: Optional[str] = None,
) -> int:
    """Start *argv* fully detached and return the worker's pid.

    POSIX: two spawns. The first cuts the controlling terminal
    (``setsid``) and every inherited descriptor (stdin to ``/dev/null``,
    stdout/stderr to *log_path*, everything above them closed outright by
    :func:`_close_inherited_fds`, so the host's stdout pipe sees EOF at once);
    the second cuts the parent, so the worker reparents to ``init`` and this
    process returns with no child to wait on and no zombie for the host to reap.

    ``log_path`` is handed in as the child's stdout/stderr on **both** platforms,
    and that is the point: the worker prints its setup lines (inputs loaded,
    models resolved, backup written, "no user preferences detected") long before
    it reaches ``maybe_detach`` and calls :func:`enter_detached_worker`, so a
    worker that only reopened its own log there sent every one of them to
    ``/dev/null`` — and with them the only durable record of what a detached run
    decided and on what inputs. It also means a worker that dies *before* the
    handshake (a bad re-exec, a failed ``uv`` sync) leaves its reason in the log
    the launcher's failure message tails, rather than an empty file.

    Windows: one spawn. ``DETACHED_PROCESS`` already removes the console, so
    there is no intermediate and nothing to reap — but a console-less child has no
    valid stdout, so the launcher opens the log and hands that one handle in as
    both stdout and stderr.
    """
    argv = [str(a) for a in argv]
    if IS_WINDOWS:  # pragma: no cover - Windows
        return _spawn_detached_windows(argv, cwd=cwd, env=env, log_path=log_path)[0]
    return _spawn_detached_posix(argv, cwd=cwd, env=env, log_path=log_path)


#: The spawn :func:`spawn_detached_run` adds a job to: this module's own. A
#: replaced ``spawn_detached`` (a test double) starts no process, so there is
#: nothing to put in a job and it is called as it is, as ``_REAL_POPEN`` is.
_REAL_SPAWN_DETACHED = spawn_detached


def spawn_detached_run(
    argv: Sequence[str],
    *,
    cwd: str,
    env: Dict[str, str],
    log_path: Optional[str] = None,
    run_id: str,
) -> Tuple[int, Optional[TreeJob]]:
    """:func:`spawn_detached` for run *run_id*: its pid, and on Windows the
    launcher's handle on the run's named Job Object (2026-10-25).

    The worker is created suspended, put in the job ``run_job_name(run_id)``
    names and only then resumed, as :func:`popen_tree` does, so ``uv``, the
    shim or trampoline behind it, the worker python and everything they start
    are in the job from the first instruction. The launcher keeps the handle
    until the handshake resolves: a failed one is killed through it, and either
    way it is closed after (:meth:`TreeJob.close` never kills). By then the
    worker holds its own handle (:func:`enter_detached_worker`), which is what
    keeps the job's name, and so the job, reachable by an abort.

    ``None`` for the job off Windows (the call is :func:`spawn_detached`
    unchanged), for a run id that names no job, when the name already exists
    (never used: see :func:`_create_run_job`), and whenever the job route
    fails: the spawn is then the one it always was.
    """
    spawn = spawn_detached
    if not IS_WINDOWS or spawn is not _REAL_SPAWN_DETACHED:
        return spawn(argv, cwd=cwd, env=env, log_path=log_path), None
    return _spawn_detached_windows(
        [str(a) for a in argv], cwd=cwd, env=env, log_path=log_path, run_id=run_id,
    )


#: Bounds for :func:`_fd_sweep_limit`, which only runs where the kernel does not
#: publish the open descriptors as a directory (see :func:`_close_inherited_fds`).
_FD_SWEEP_FALLBACK = 4096
_FD_SWEEP_CEILING = 1 << 16


def _fd_sweep_limit() -> int:
    """Exclusive upper bound for a blind ``closerange`` sweep.

    The soft ``RLIMIT_NOFILE`` is the number the kernel enforced when every
    descriptor this process holds was opened, so nothing can sit above it;
    ``SC_OPEN_MAX`` is the fallback. Both are clamped, because "unlimited" is a
    legal answer (``RLIM_INFINITY``, and on Linux a soft limit of 2^20 is a
    common container default) and a sweep to infinity is not a sweep:
    :func:`os.closerange` is one ``close_range`` syscall where the platform has
    it, but degrades to a per-descriptor loop where it does not.
    """
    limit = 0
    try:  # POSIX-only, and absent from some locked-down builds.
        import resource

        for candidate in resource.getrlimit(resource.RLIMIT_NOFILE):
            # RLIM_INFINITY is -1 here, so "unlimited" fails the > 0 test too.
            if candidate is not None and candidate > 0:
                limit = int(candidate)
                break
    except Exception:
        limit = 0
    if limit <= 0:
        try:
            limit = int(os.sysconf("SC_OPEN_MAX"))
        except (AttributeError, ValueError, OSError):
            limit = 0
    if limit <= 0:
        limit = _FD_SWEEP_FALLBACK
    return min(max(limit, 3), _FD_SWEEP_CEILING)


def _close_inherited_fds() -> None:
    """Close every descriptor above stdio. Call in a forked child, pre-``exec``.

    D4's spawn recipe requires the worker to hold *nothing* belonging to the
    host: fds 0/1/2 are replaced, and everything above them has to go, or the
    host's pipe never sees EOF and a harness waiting on the invoking command
    blocks on a run that intends to outlive it. PEP 446 covers only descriptors
    *Python* opened — it makes those non-inheritable, so ``execve`` drops them —
    but a descriptor the invoker itself **inherited** from the host (a harness
    status pipe on fd 3, a shell's redirection) arrives already inheritable and
    would survive into the worker untouched. ``close_fds=True`` would cover it if
    this were a :class:`subprocess.Popen`, but the double spawn is a raw
    ``fork``/``execve``, so the sweep is ours to do.

    Where the kernel publishes the open set (``/proc/self/fd``, ``/dev/fd``) that
    is both exact and cheap; otherwise fall back to a blind
    :func:`os.closerange` over :func:`_fd_sweep_limit`. Errors are ignored
    throughout: a descriptor that cannot be closed is one already closed.
    """
    for fd_dir in ("/proc/self/fd", "/dev/fd"):
        try:
            # `listdir` reads the whole directory and closes its own descriptor
            # before returning, so nothing here is iterating over a handle it is
            # about to invalidate.
            names = os.listdir(fd_dir)
        except OSError:
            continue
        for name in names:
            try:
                fd = int(name)
            except ValueError:  # pragma: no cover - non-numeric entry
                continue
            if fd < 3:
                continue
            try:
                os.close(fd)
            except OSError:
                pass
        return
    os.closerange(3, _fd_sweep_limit())  # pragma: no cover - no fd directory


def _open_worker_log(log_path: Optional[str]) -> Optional[int]:
    """Append-only descriptor for the worker's stdout/stderr, or ``None``.

    Append, never truncate: the launcher rotated any predecessor aside already,
    and a worker that re-enters :func:`enter_detached_worker` must find its own
    earlier bytes still there. Best effort — a log that cannot be opened falls
    back to ``/dev/null`` (the pre-2026-09 behaviour) rather than sinking a
    launch whose phase dir was already proved writable.
    """
    if not log_path:
        return None
    try:
        return os.open(str(log_path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    except OSError:
        return None


def _spawn_detached_posix(
    argv: List[str], *, cwd: str, env: Dict[str, str], log_path: Optional[str]
) -> int:
    # Opened here, in the invoker, so the descriptor exists before the fork and
    # the child has nothing to fail at: it only dup2s what it was handed.
    log_fd = _open_worker_log(log_path)
    read_fd, write_fd = os.pipe()
    try:
        intermediate = os.fork()
    except OSError:
        for spare in (log_fd, read_fd, write_fd):
            if spare is not None:
                try:
                    os.close(spare)
                except OSError:
                    pass
        raise
    if intermediate == 0:
        # --- spawn one: new session, no controlling terminal, no host fds ---
        try:
            os.close(read_fd)
            os.setsid()
            devnull = os.open(os.devnull, os.O_RDWR)
            # stdout/stderr onto the phase log from the first byte the worker
            # writes — not from `enter_detached_worker`, which the orchestrators
            # reach only after their setup output is already on the floor.
            # Duplicated before stdin, so that a log that landed on a low
            # descriptor (an invoker whose own stdin was closed) is copied up to
            # 1 and 2 before /dev/null overwrites 0.
            out_fd = devnull if log_fd is None else log_fd
            os.dup2(out_fd, 1)
            os.dup2(out_fd, 2)
            os.dup2(devnull, 0)
            for spare in (devnull, log_fd):
                if spare is not None and spare > 2:
                    try:
                        os.close(spare)
                    except OSError:
                        pass
            worker = os.fork()
            if worker == 0:
                # --- spawn two: the real worker, reparented to init on exit ---
                try:
                    os.close(write_fd)
                except OSError:
                    pass
                # Everything above the three fds replaced above goes with it —
                # including whatever the *invoker* inherited from the host, which
                # `execve` alone would carry into the worker and leave the host's
                # pipe waiting on an EOF that never comes.
                _close_inherited_fds()
                try:
                    os.chdir(cwd)
                except OSError:
                    pass
                try:
                    if os.path.isabs(argv[0]):
                        os.execve(argv[0], argv, env)
                    else:
                        os.execvpe(argv[0], argv, env)
                except BaseException:
                    os._exit(127)
                os._exit(127)  # unreachable
            os.write(write_fd, str(worker).encode("ascii"))
            os.close(write_fd)
        except BaseException:
            os._exit(127)
        os._exit(0)
    # --- invoker: read the worker pid, reap the intermediate, return ---
    # The log belongs to the worker now; holding a second descriptor open here
    # would keep the invoker attached to a file it never writes.
    if log_fd is not None:
        try:
            os.close(log_fd)
        except OSError:
            pass
    os.close(write_fd)
    try:
        raw = os.read(read_fd, 32)
    finally:
        os.close(read_fd)
    try:
        os.waitpid(intermediate, 0)
    except OSError:
        pass
    try:
        return int(raw.decode("ascii").strip())
    except (UnicodeDecodeError, ValueError):
        raise SpawnFailed(
            "the detach intermediate did not report a worker pid"
        )


def _spawn_detached_windows(  # pragma: no cover - Windows
    argv: List[str],
    *,
    cwd: str,
    env: Dict[str, str],
    log_path: Optional[str],
    run_id: Optional[str] = None,
) -> Tuple[int, Optional[TreeJob]]:
    """The one Windows spawn, and with a *run_id* the run's named job.

    The job route is all-or-nothing and never fails a launch: no job API, a
    replaced ``Popen``, a name that cannot be made or is already taken, or a
    worker that cannot join all spawn without one, and a worker that was
    created suspended but could not be resumed (killed before it ran an
    instruction) is spawned again, as it always was.
    """
    DETACHED_PROCESS = 0x00000008
    CREATE_NEW_PROCESS_GROUP = 0x00000200
    flags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    handle = None
    if log_path:
        handle = open(log_path, "ab", buffering=0)
    try:
        kwargs: Dict[str, Any] = dict(
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=handle if handle is not None else subprocess.DEVNULL,
            stderr=handle if handle is not None else subprocess.DEVNULL,
            close_fds=True,
        )
        spawn = subprocess.Popen
        api = _job_api() if run_id is not None and spawn is _REAL_POPEN else None
        job_handle = _create_run_job(api, run_id) if api is not None else None
        if job_handle is None:
            return spawn(argv, creationflags=flags, **kwargs).pid, None
        try:
            proc, job = _popen_in_job(
                api, job_handle, spawn, argv, dict(kwargs, creationflags=flags))
        except _NotResumed:
            proc, job = spawn(argv, creationflags=flags, **kwargs), None
        return proc.pid, job
    finally:
        if handle is not None:
            handle.close()


def _stdio_already_on(log_path: str) -> bool:
    """True when fds 1 **and** 2 already name the file at *log_path*."""
    try:
        target = os.stat(str(log_path))
    except OSError:
        return False
    for fd in (1, 2):
        try:
            current = os.fstat(fd)
        except OSError:
            return False
        if (current.st_dev, current.st_ino) != (target.st_dev, target.st_ino):
            return False
    return True


def _rebind_std_streams() -> None:
    """``sys.stdout``/``sys.stderr`` as fresh text streams over fds 1 and 2.

    For Windows, after :func:`enter_detached_worker` pointed the descriptors
    at the log: the streams Python opened at start may not follow a ``dup2``
    there (see that function). :func:`~utils.stream_bootstrap.bootstrap_streams`
    sets them up as usual afterwards.
    """
    sys.stdout = open(1, "w", encoding="utf-8", errors="replace", closefd=False)
    sys.stderr = open(2, "w", encoding="utf-8", errors="replace", closefd=False)


def redirect_output_to_log(log_path: Optional[str]) -> None:
    """Restore a worker's log descriptors without taking run ownership.

    The dispatcher calls this before pre-flight if a launcher supplied the log
    path. It is also the late fallback in :func:`enter_detached_worker`.
    """
    if log_path and not _stdio_already_on(log_path):
        try:
            fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        except OSError:
            fd = None
        if fd is not None:
            try:
                sys.stdout.flush()
                sys.stderr.flush()
            except (AttributeError, ValueError):
                pass
            os.dup2(fd, 1)
            os.dup2(fd, 2)
            if fd > 2:
                os.close(fd)
            if IS_WINDOWS:
                _rebind_std_streams()


def enter_detached_worker(log_path: Optional[str], run_id: Optional[str] = None) -> None:
    """Worker-side setup: own the log, own the process group, own the tree.

    Idempotent with the launcher, and that is now the normal case: since the
    POSIX spawn hands the log in as the child's stdout/stderr (so the setup lines
    printed *before* the detach boundary are recorded too), fds 1 and 2 usually
    already name it and there is nothing to reopen. Reopening anyway would be
    worse than redundant — a second file description means a second buffer over
    one file — so the descriptors are compared by ``(st_dev, st_ino)`` first.
    Nothing here ever truncates: the open is ``O_APPEND``, so a second call
    cannot drop the bytes the first one wrote.

    Where the comparison fails (a worker launched some other way, or one whose
    log was rotated out from under it) fds 1 and 2 are reopened onto *log_path*,
    so no application output — the worker's own or any provider subprocess's —
    passes through a descriptor the host handed us. Either way the stream
    bootstrap is re-run so the log gets line-buffered UTF-8 with
    ``errors="replace"``. **Both** settings matter: without line buffering a
    detached log stays empty for minutes, and without the encoding a
    Windows-piped stream defaults to cp1252 and raises ``UnicodeEncodeError`` on
    the first em dash a model emits.

    Windows: the launcher hands the log in as stdout/stderr too, but nothing
    makes every process between it and the worker pass the handle on: behind a
    ``uv`` that is a ``.cmd`` shim (cmd.exe, node, then python, under
    ``DETACHED_PROCESS``) the worker's stdout was not the log (Windows CI,
    2026-10-23: the run reached ``done``, its log stayed empty). So the same
    comparison and reopen run there, and
    ``sys.stdout``/``sys.stderr`` are rebuilt over the new descriptors: the
    old ones may be ``None`` (no valid handle at start) or console streams,
    which write through ``WriteConsoleW`` and a file handle refuses. The worker
    also joins a Job Object with ``KILL_ON_JOB_CLOSE`` so the OS reaps provider
    children even if the worker crashes without running a handler.

    With *run_id* (the run's, which the launcher minted: ``begin_worker_run``
    passes it) the worker first takes its handle on the run's named job and
    keeps it for life (:func:`_hold_run_job`, 2026-10-25): that is what keeps
    the job an abort opens by name. The reaper job then nests inside it, as it
    nests inside any job the worker is already in. Without a *run_id* (a
    worker started some other way) nothing about the jobs changes.
    """
    redirect_output_to_log(log_path)
    if IS_WINDOWS:  # pragma: no cover - Windows
        if run_id is not None:
            # First, so a job the worker creates itself holds the reaper's.
            _hold_run_job(run_id)
        _assign_own_job_object()
    from .stream_bootstrap import bootstrap_streams

    bootstrap_streams()


def _assign_own_job_object() -> None:  # pragma: no cover - Windows
    """Best-effort Job Object with KILL_ON_JOB_CLOSE around this process."""
    try:
        import ctypes
        from ctypes import wintypes
    except ImportError:
        return
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        job = kernel32.CreateJobObjectW(None, None)
        if not job:
            return

        class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", wintypes.LARGE_INTEGER),
                ("PerJobUserTimeLimit", wintypes.LARGE_INTEGER),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_ulonglong),
                ("WriteOperationCount", ctypes.c_ulonglong),
                ("OtherOperationCount", ctypes.c_ulonglong),
                ("ReadTransferCount", ctypes.c_ulonglong),
                ("WriteTransferCount", ctypes.c_ulonglong),
                ("OtherTransferCount", ctypes.c_ulonglong),
            ]

        class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
                ("IoInfo", IO_COUNTERS),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
        JobObjectExtendedLimitInformation = 9
        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        kernel32.SetInformationJobObject(
            job, JobObjectExtendedLimitInformation,
            ctypes.byref(info), ctypes.sizeof(info),
        )
        kernel32.AssignProcessToJobObject(job, kernel32.GetCurrentProcess())
        # The handle is deliberately leaked for the process's lifetime: the job
        # dies (killing the tree) when the last handle closes, i.e. on exit.
        globals()["_JOB_HANDLE"] = job
    except Exception:
        return


def install_worker_signal_handlers(on_abort: Callable[[int], None]) -> None:
    """Route cancellation signals to the abort path; ignore hangups.

    SIGHUP is explicitly *not* an abort trigger: the worker is a session leader
    with no controlling terminal so a host shell's exit cannot deliver one, and
    ignoring it means a host that kills its whole process tree on session
    teardown cannot take the run down silently either.

    One abort per process: the first signal ignores every later one before
    *on_abort* runs. ``status --abort`` signals the worker's process group,
    which holds ``uv run`` and its python child, and ``uv run`` forwards the
    SIGTERM it gets to that child, so the worker always receives the signal
    twice (Codex racing run 6: the copy re-entered the handler mid-``print``
    and the run ended in a traceback instead of its ``aborted`` record).
    """
    names = ["SIGTERM", "SIGINT", "SIGBREAK"]
    handling = []

    def handler(signum, _frame):
        if handling:
            return  # a copy, or a repeat: the abort is already under way
        handling.append(signum)
        for other in names:
            sig = getattr(signal, other, None)
            if sig is None:
                continue
            try:
                signal.signal(sig, signal.SIG_IGN)
            except (OSError, ValueError):  # pragma: no cover
                pass
        on_abort(signum)

    for name in names:
        sig = getattr(signal, name, None)
        if sig is None:
            continue
        try:
            signal.signal(sig, handler)
        except (OSError, ValueError):  # pragma: no cover - non-main thread
            pass
    sighup = getattr(signal, "SIGHUP", None)
    if sighup is not None:
        try:
            signal.signal(sighup, signal.SIG_IGN)
        except (OSError, ValueError):  # pragma: no cover
            pass
