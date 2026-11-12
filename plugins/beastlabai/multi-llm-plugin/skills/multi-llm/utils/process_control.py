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
import contextvars
import errno
import itertools
import json
import os
import select
import signal
import stat
import struct
import subprocess
import sys
import threading
import time
import weakref
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import (
    Any, Awaitable, Callable, Dict, Iterator, List, NamedTuple, Optional, Sequence,
    Set, Tuple, TypeVar,
)

from .process_state import process_cache

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
    reading = sourced_start_time(pid)
    return reading[1] if reading is not None else None


#: Where a :func:`sourced_start_time` reading came from. The three are different
#: representations of one instant, so two readings compare only when their
#: sources match: Linux falls back to ``ps`` text when ``/proc`` cannot be read.
START_SOURCE_PROC = "proc"  # /proc/<pid>/stat field 22, clock ticks since boot
START_SOURCE_PS = "ps"  # ps -o lstart= text
START_SOURCE_WINDOWS = "win"  # GetProcessTimes creation time, a FILETIME


def sourced_start_time(pid: int) -> Optional[Tuple[str, str]]:
    """:func:`process_start_time` with where it came from: ``(source, start
    time)``, the source one of the ``START_SOURCE_*`` words, or ``None`` if
    unknown. A start time recorded to be compared later is recorded with its
    source, and a reading from another source is inconclusive, never a
    mismatch."""
    if pid is None or pid <= 0:
        return None
    if IS_WINDOWS:
        value = _windows_start_time(pid)
        return (START_SOURCE_WINDOWS, value) if value is not None else None
    linux = _linux_start_time(pid)
    if linux is not None:
        return START_SOURCE_PROC, linux
    value = _ps_start_time(pid)
    return (START_SOURCE_PS, value) if value is not None else None


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
        # ctypes loads only on the platform path that calls it.
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


def process_liveness(pid: Optional[int]) -> str:
    """:data:`ALIVE` / :data:`DEAD` / :data:`UNKNOWN` for *pid*, where
    :func:`process_alive` folds a probe that failed into "not alive": only a
    pid the platform says does not exist is :data:`DEAD`, so a caller that
    deletes on death never acts on a query that merely failed."""
    if not pid or pid <= 0:
        return DEAD
    if IS_WINDOWS:  # pragma: no cover - Windows
        return _windows_liveness(pid)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return DEAD
    except PermissionError:
        return ALIVE  # alive but owned by another user
    except OSError:
        return UNKNOWN
    return ALIVE


def _windows_liveness(pid: int) -> str:  # pragma: no cover - Windows
    """``OpenProcess`` refusing an unknown pid (``ERROR_INVALID_PARAMETER``)
    is death; any other failure, of it or of ``GetExitCodeProcess``, is
    unknown."""
    try:
        # ctypes loads only on the platform path that calls it.
        import ctypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    except Exception:
        return UNKNOWN
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    STILL_ACTIVE = 259
    ERROR_INVALID_PARAMETER = 87
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return DEAD if ctypes.get_last_error() == ERROR_INVALID_PARAMETER else UNKNOWN
    try:
        code = ctypes.c_ulong()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
            return UNKNOWN
        return ALIVE if code.value == STILL_ACTIVE else DEAD
    finally:
        kernel32.CloseHandle(handle)


def _windows_alive(pid: int) -> bool:  # pragma: no cover - Windows
    try:
        # ctypes loads only on the platform path that calls it.
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


def pid_namespace() -> Optional[str]:
    """The PID namespace this process sees pids in, or ``None`` if unknown.

    Linux reads the ``/proc/self/ns/pid`` link (``pid:[4026531836]``). A
    recorded ``(pid, start time)`` means a process only in the namespace it was
    recorded in: two processes sharing a temp directory from different
    namespaces each see the other's pid as gone or reused. ``None`` elsewhere,
    and wherever the link cannot be read.
    """
    if IS_WINDOWS:  # pragma: no cover - Windows
        return None
    try:
        return os.readlink("/proc/self/ns/pid")
    except (OSError, AttributeError):
        return None


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
        # Windows only.
        import msvcrt

        os.lseek(fd, _WINDOWS_LOCK_OFFSET, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        os.lseek(fd, 0, os.SEEK_SET)
        return
    # POSIX only.
    import fcntl

    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)


def _drop_fd_lock(fd: int) -> None:
    """Release the exclusive OS lock on *fd*."""
    if IS_WINDOWS:  # pragma: no cover - Windows
        # Windows only.
        import msvcrt

        os.lseek(fd, _WINDOWS_LOCK_OFFSET, os.SEEK_SET)
        try:
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        return
    # POSIX only.
    import fcntl

    fcntl.flock(fd, fcntl.LOCK_UN)


def descriptor_owning_handle(handle: int) -> int:  # pragma: no cover - Windows
    """Windows: wrap the Win32 file *handle* in a non-inheritable C runtime
    descriptor that owns it (closing the descriptor closes the handle)."""
    # Windows only.
    import msvcrt

    return msvcrt.open_osfhandle(handle, os.O_NOINHERIT)


def handle_of_descriptor(fd: int) -> int:  # pragma: no cover - Windows
    """Windows: the Win32 handle behind C runtime descriptor *fd*."""
    # Windows only.
    import msvcrt

    return msvcrt.get_osfhandle(fd)


#: The buffer ``fcntl(F_GETPATH)`` fills: macOS's ``MAXPATHLEN``, the
#: terminating NUL included. Never smaller, as the kernel writes up to that.
_MAXPATHLEN = 1024


def descriptor_path(fd: int) -> str:
    """The path the kernel holds now for the open descriptor *fd*, through
    ``fcntl(2)``'s ``F_GETPATH`` (macOS, which has no ``/proc``); ``""``
    where Python offers no such call (Linux, which names a descriptor at
    ``/proc/self/fd`` instead; Windows) or it fails. The answer follows a
    folder that was moved, and spells the path as the kernel holds it (the
    link macOS keeps at the top of its temp folders resolved): fit for a
    message saying where something went (``held_folder._descriptor_path``),
    never for a containment check (docs/development/write-safety.md)."""
    try:
        import fcntl  # POSIX only; loaded on the path that calls it
    except ImportError:  # pragma: no cover - Windows
        return ""
    request = getattr(fcntl, "F_GETPATH", None)
    if request is None:
        return ""
    try:
        answer = fcntl.fcntl(fd, request, bytes(_MAXPATHLEN))
    except (OSError, ValueError):
        return ""
    return os.fsdecode(bytes(answer).split(b"\0", 1)[0])


class LockUnavailable(Exception):
    """Another process holds the lock. Carries the recorded holder, if any."""

    def __init__(self, path: str, holder: Optional[Dict[str, Any]]):
        super().__init__(f"lock held: {path}")
        self.path = path
        self.holder = holder or {}


#: The phase locks this process holds, by :func:`_phase_lock_key`. The OS
#: refuses a second take of a held lock on another descriptor even to the
#: process that holds it (``flock`` is per open file description), so code
#: that may run inside a holder (a phase main under a composite step's lock,
#: or under the detached worker's) asks :func:`held_phase_lock` first and
#: leaves the release to whoever took it.
_HELD_PHASE_LOCKS: Dict[str, "PhaseLock"] = {}


def _phase_lock_key(path: str) -> str:
    return os.path.normcase(os.path.realpath(str(path)))


def held_phase_lock(path: str) -> Optional["PhaseLock"]:
    """The :class:`PhaseLock` this process holds on *path*, or ``None``."""
    lock = _HELD_PHASE_LOCKS.get(_phase_lock_key(path))
    return lock if lock is not None and lock.held else None


class LockHandoffFailed(OSError):
    """A descriptor handed to this process is not the lock it was meant to be."""


class PhaseLock:
    """A non-blocking, advisory-on-POSIX / mandatory-on-Windows file lock.

    Held on an open fd for the whole run, so a crash releases it even though the
    file remains on disk — which is why "the file exists" is never treated as
    "someone holds it". While held it is listed for :func:`held_phase_lock`.

    The descriptor is never inherited by a child (close-on-exec): a provider
    CLI must not keep a phase locked after its run ends. The one deliberate
    crossing is a ``--detach`` launch handing the lock to its worker
    (:meth:`handoff_fd`, :meth:`adopt`, :meth:`disown`; POSIX only, where the
    ``flock`` belongs to the open file description both processes share).
    """

    def __init__(self, path: str):
        self.path = str(path)
        self._fd: Optional[int] = None
        self._until_exit = False

    # -- acquisition ----------------------------------------------------
    def acquire(self, payload: Optional[Dict[str, Any]] = None) -> None:
        """Take the lock, recording *payload* in the file. Raises on conflict."""
        flags = os.O_CREAT | os.O_RDWR
        if hasattr(os, "O_BINARY"):  # pragma: no cover - Windows
            flags |= os.O_BINARY
        fd = os.open(self.path, flags, 0o644)
        try:
            # PEP 446 already opens it non-inheritable; said here because the
            # rule is load-bearing (see the class docstring).
            os.set_inheritable(fd, False)
            self._lock_fd(fd)
        except (OSError, IOError) as exc:
            os.close(fd)
            raise LockUnavailable(self.path, read_lock_holder(self.path)) from exc
        self._fd = fd
        _HELD_PHASE_LOCKS[_phase_lock_key(self.path)] = self
        if payload is not None:
            self._write_payload(payload)

    @classmethod
    def adopt(cls, path: str, fd: int,
              payload: Optional[Dict[str, Any]] = None) -> "PhaseLock":
        """The lock a ``--detach`` launcher handed this process on the
        inherited descriptor *fd* (POSIX), held from here.

        *fd* must be *path* itself, the same file (``fstat`` against ``stat``),
        or nothing is adopted: :class:`LockHandoffFailed`, and *fd* is left
        alone (a number that names some other file here is not ours to
        close). The ``flock`` is then taken on *fd* again, which succeeds
        only because the open file description shared with the launcher
        already holds it, so a lock that was not handed over held is
        :class:`LockUnavailable` rather than adopted. The descriptor is made
        close-on-exec at once.
        """
        try:
            on_fd = os.fstat(fd)
            on_path = os.stat(path)
        except OSError as exc:
            raise LockHandoffFailed(
                exc.errno or errno.EBADF,
                f"the descriptor handed over ({fd}) is not {path}: {exc.strerror}",
            ) from None
        if (on_fd.st_dev, on_fd.st_ino) != (on_path.st_dev, on_path.st_ino):
            raise LockHandoffFailed(
                errno.ESTALE, f"the descriptor handed over ({fd}) is not {path}")
        os.set_inheritable(fd, False)
        lock = cls(path)
        try:
            lock._lock_fd(fd)
        except (OSError, IOError) as exc:
            raise LockUnavailable(path, read_lock_holder(path)) from exc
        lock._fd = fd
        _HELD_PHASE_LOCKS[_phase_lock_key(path)] = lock
        if payload is not None:
            lock._write_payload(payload)
        return lock

    def handoff_fd(self) -> int:
        """A duplicate of the held descriptor for a child to inherit (POSIX):
        numbered 3 or above, so a child's stdio set-up cannot clobber it, and
        close-on-exec until the spawn clears that for the one child it hands
        it to. The caller closes it once the spawn is done."""
        # POSIX only.
        import fcntl

        assert self._fd is not None
        return fcntl.fcntl(self._fd, fcntl.F_DUPFD_CLOEXEC, 3)

    def disown(self) -> None:
        """Close this process's descriptor **without** unlocking. Idempotent.

        After a hand-off the lock lives in the open file description the
        worker shares: an unlock here would drop it for the worker too, while
        a close only drops this process's reference, and the kernel releases
        the lock with the last one. So a worker that adopted it keeps it, and
        one that died took its copy with it.
        """
        fd, self._fd = self._fd, None
        if fd is None:
            return
        key = _phase_lock_key(self.path)
        if _HELD_PHASE_LOCKS.get(key) is self:
            del _HELD_PHASE_LOCKS[key]
        try:
            os.close(fd)
        except OSError:
            pass

    def hold_until_exit(self) -> None:
        """Keep the lock until this process exits: :meth:`release` does
        nothing from here on, and the kernel releases the lock when the
        process's last descriptor closes, after every thread has ended. For a
        run whose writers may outlive its main code path (a Ctrl-C, an abort);
        docs/development/runtime.md, "One writer per phase dir"."""
        self._until_exit = True

    def relabel(self, payload: Dict[str, Any]) -> None:
        """Rewrite the holder's label in a lock this object holds (a holder
        that takes a lock over from an earlier holder in its own process)."""
        if self._fd is not None:
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
        a holder displaced by an unlink would, on release, unlink the path its
        *successor* now owns.) So the file is durable and the lock is what is
        held: an empty ``{phase}/.lock`` left behind means nothing, exactly as
        it already does after a crash — see :func:`lock_is_free`, which probes
        rather than stats. Nothing at all after :meth:`hold_until_exit`.
        """
        if self._until_exit:
            return
        fd, self._fd = self._fd, None
        if fd is None:
            return
        key = _phase_lock_key(self.path)
        if _HELD_PHASE_LOCKS.get(key) is self:
            del _HELD_PHASE_LOCKS[key]
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


def break_lock(path: str) -> bool:
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

    **A live holder's lock is never broken**, ``--force`` included: a
    ``--detach --force`` launch asks the holder to stop through the abort path
    and then waits to take this same lock, so getting it is the proof the old
    writer is gone (``detach._stop_holder_and_take``).
    """
    if not os.path.exists(path):
        return True
    probe_lock = PhaseLock(path)
    try:
        probe_lock.acquire()
    except LockUnavailable:
        return False
    except OSError:
        # The file could not even be opened: inconclusive, unless it has since
        # vanished — in which case there is nothing left to hold.
        return not os.path.exists(path)
    probe_lock.release()
    return True


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
        be opened (a phase dir that does not exist), its file system cannot
        lock it, or the wait expired.
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
        try:
            taken = wait_for_fd_lock(fd, timeout_s=timeout_s, poll_interval_s=poll_interval_s)
        except OSError:
            taken = False  # the file system cannot lock it: never raised here
        if not taken:
            try:
                os.close(fd)
            except OSError:
                pass
            return False
        self._fd = fd
        return True

    def release(self) -> None:
        """Drop the lock, keeping the file. Idempotent, never raises."""
        fd, self._fd = self._fd, None
        if fd is None:
            return
        try:
            release_fd_lock(fd)
        finally:
            try:
                os.close(fd)
            except OSError:
                pass

    @property
    def held(self) -> bool:
        return self._fd is not None


#: What a non-blocking lock attempt fails with while another descriptor holds
#: the lock (``flock``'s ``EWOULDBLOCK``, ``fcntl``'s ``EACCES``/``EAGAIN``,
#: ``msvcrt``'s ``EACCES``/``EDEADLOCK``): worth waiting on. Any other errno
#: (an unsupported operation, no lock records left) is the file system's
#: answer, and waiting never changes it.
LOCK_CONTENTION_ERRNOS = frozenset(
    code for code in (
        errno.EAGAIN, errno.EWOULDBLOCK, errno.EACCES, errno.EINTR,
        getattr(errno, "EDEADLK", None),
    ) if code is not None
)


def wait_for_fd_lock(
    fd: int,
    *,
    timeout_s: float = DEFAULT_MUTEX_TIMEOUT_S,
    poll_interval_s: float = 0.005,
) -> bool:
    """:class:`FileMutex`'s bounded wait, on a descriptor the caller opened
    itself (for instance without following a link). ``True`` once the
    exclusive lock is taken, ``False`` when another holder kept it until the
    wait expired. Raises the ``OSError`` at once when the lock cannot be
    taken at all (an errno outside :data:`LOCK_CONTENTION_ERRNOS`, such as
    ``EOPNOTSUPP`` on a file system without locks). The caller drops it with
    :func:`release_fd_lock` and closes *fd*."""
    deadline = time.monotonic() + max(0.0, float(timeout_s))
    while True:
        try:
            _take_fd_lock(fd)
        except (OSError, IOError) as exc:
            if exc.errno not in LOCK_CONTENTION_ERRNOS:
                raise
            if time.monotonic() >= deadline:
                return False
            time.sleep(poll_interval_s)
            continue
        return True


def release_fd_lock(fd: int) -> None:
    """Drop the lock :func:`wait_for_fd_lock` took on *fd*. Never raises."""
    try:
        _drop_fd_lock(fd)
    except (OSError, IOError):
        pass


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
    teardown still covers the tree. Only a child spawned through
    :func:`popen_tree` with these kwargs is ever sent that break, and only as
    the ``child`` its own ``Popen`` is passed to :func:`kill_tree`
    (:func:`_leads_console_group`).
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
    child: Optional["subprocess.Popen[Any]"] = None,
    members: Sequence["Descendant"] = (),
    members_complete: bool = True,
    obligations: Optional["KillObligations"] = None,
) -> str:
    """Terminate *pid* and every process it spawned. Returns a verdict string.

    ``gone`` (was already dead, and nothing of its group survives), ``killed``
    (died, gracefully or after the escalation), ``survived`` (still alive after
    the SIGKILL window), ``skipped`` (identity could not be corroborated — the
    pid may have been recycled, so signalling it would hit an unrelated process)
    or ``unresolved`` (Linux with pidfds only: something may still run that
    could not be identified as the target's, so it was not signalled, or what
    the kill needed to know could not be read). ``skipped`` and ``unresolved``
    both mean not every process could be confirmed stopped.

    *members* are processes recorded as the target's besides *pid*, each with
    its pid, start time and the group it was started in (a detached worker's
    provider CLIs, read back from :func:`read_cli_record`): on Linux with
    pidfds each is signalled by its identity, and its group is read afterwards
    like the target's. *members_complete* false says the record they came from
    may be missing one (:attr:`CliRecord.complete`), which makes the verdict
    ``unresolved`` there. Both are ignored everywhere else. So is
    *obligations*, which on the kill by identity gets what the verdict leaves
    unconfirmed, by what names it (:class:`KillObligations`).

    *child* is the ``Popen`` this process holds for *pid*, not yet reaped. On
    Linux, where this process's children are known to become zombies (read in
    an ABI whose ``struct sigaction`` layout was checked, :func:`_sigaction_abi`,
    or established by this process's own SIGCHLD reset,
    :func:`restore_sigchld_default`), it takes a path of its own
    (:func:`_posix_kill_owned`): its zombie counts as exited, the grace ends
    once nothing of its group runs, and the group then always gets one SIGKILL
    by number before the kill confirms it gone, so members that joined late
    are included, seen or not. Nothing reaps the child there: its ``Popen``
    reads the real exit status afterwards. Everywhere else (macOS, the BSDs,
    a Linux whose retention is not established) *child* does not take that
    path (docs/development/runtime.md, "An owned child's kill"): on a Linux
    with pidfds it is then not signalled at all (``unresolved``).

    That path is safe only under a lifecycle contract its caller keeps (the
    same doc section). The caller holds the only waiter on *child* and does
    not wait on it until ``kill_tree`` returns. Nothing in the process reaps
    children it does not name (``os.wait``, ``waitpid(-1)`` and the like; a
    test fails the plugin's sources on them). Children become zombies: SIGCHLD
    is neither ``SIG_IGN`` nor ``SA_NOCLDWAIT``, read from the kernel. Then the
    child's pid and the number of the group it leads cannot be recycled during
    the kill. The kill rereads the child and the disposition right before each
    signal, which narrows a breach of the contract but cannot close it: once
    either is known to fail it sends nothing more, and once the disposition
    cannot be read the rest of the kill is the one below. A *child* that does
    not anchor *pid* on entry (reaped, another pid, a group it does not lead,
    children reaped at exit, a disposition that cannot be read) is ignored,
    and the kill is the one below.

    Two identity rules for every other target, and they are its whole contract:

    * ``start_time`` supplied and the probe cannot corroborate it ⇒ ``skipped``,
      **no signal**. ``kill_tree`` is reached by routine paths (``util runs
      --sweep`` over week-old entries whose ``/proc`` read failed), and a
      recycled pid's *process group* is an unrelated group.
    * an unverified kill is *requested*, never inferred: pass ``start_time=None``
      — which is how ``--force`` and a failed-handshake teardown spell it off
      the identity kill (below), which grants no such request.

    The worker is its own process-group leader and every provider CLI it spawns
    inherits that group, so a group signal takes the whole tree down and no
    provider is left burning quota against a run nobody is reading. That group
    outlives its leader, so a recorded *pgid* is still killed when the leader
    itself is gone (the crash case D4b's close-out has to clean up); it is only
    ever the recorded value, never one re-derived from a pid whose identity just
    failed.

    That is the kill by number, and it is what runs off Linux, or on a Linux
    without pidfds or ``/proc``. On Linux with both no number is signalled at
    all (:func:`_identity_kill`; docs/development/runtime.md, "A target known
    only by number"): only *pid* and *members* are signalled, each through a
    pidfd verified to hold it, and their groups are only read: what still runs
    there unidentified is reported (``unresolved``), never signalled. There an
    unverified kill cannot be requested: *pid* is held only by its recorded
    *start_time*, or, without one, through a *child* that still anchors it;
    with neither it is not signalled at all, and the verdict is
    ``unresolved`` unless no process has the pid any more.

    Windows has no groups. There *job* is the child's :class:`TreeJob` from
    :func:`popen_tree`, which plays the group's part: the escalation
    terminates it rather than running ``taskkill /T`` (which can reach an
    unrelated orphan, :func:`taskkill_tree`), and a leader already gone still
    has what it left in the job ended. A detached run's pid read off disk
    has one too, by name: :func:`kill_run_tree` opens it and passes it here
    (2026-10-25). Without one (a run whose job could not be opened, a child
    spawned without a job) the escalation is ``taskkill /T`` as before.

    The graceful phase there is a ``CTRL_BREAK_EVENT``, and it is sent only to
    a group this process is known to have made on its own console: *child* is
    a ``Popen`` :func:`popen_tree` started with ``CREATE_NEW_PROCESS_GROUP``
    (and no flag that leaves the console), it is not yet reaped, and *pid* is
    its pid (:func:`_leads_console_group`). Every other target, a pid read off
    disk above all, gets no break and no grace: its job, or ``taskkill /T``,
    is the whole kill. ``GenerateConsoleCtrlEvent`` takes any number, and one
    that is not the id of a process group on the caller's console reaches
    every process attached to that console. A detached worker's recorded pid
    is never one: ``DETACHED_PROCESS`` gives the worker no console, and the
    pid it records is the real interpreter's, a child of the venv's
    ``python.exe`` launcher or of uv's trampoline, which leads the group. So
    the break an abort used to send the worker never reached it, and reached
    instead whatever shared the aborter's console: the host CLI that ran
    ``status --abort``, or the test run that called it (2026-11-12).
    """
    if not pid and not pgid and not members and members_complete:
        # Nothing recorded to probe or signal, but a job still names a tree: a
        # run whose record lost its pid, found by its run id (`kill_run_tree`).
        if IS_WINDOWS and job is not None:  # pragma: no cover - Windows
            job.terminate()
        return "gone"
    if child is not None and not IS_WINDOWS:
        tree = _owned_tree(child, pid, pgid)
        if tree is not None:
            return _posix_kill_owned(
                tree, escalate_after_s, poll_interval_s,
                by_number=lambda grace: _kill_by_number(
                    pid, start_time, pgid, grace, poll_interval_s, job, members,
                    members_complete, child, obligations),
            )
    return _kill_by_number(pid, start_time, pgid, escalate_after_s, poll_interval_s, job,
                           members, members_complete, child, obligations)


#: Timeout-kill verdicts that confirm the runner stopped. Every other outcome
#: (``survived``, ``unresolved``, ``skipped``, ``None`` for a kill that
#: raised, any other word) is unconfirmed (:func:`unconfirmed_kill`). One rule
#: for every timeout kill: the executor's, the verify command's and the
#: provider client's sweep.
CONFIRMED_KILLS = ("killed", "gone")


def unconfirmed_kill(verdict: Optional[str]) -> Optional[str]:
    """Why a timeout kill that returned *verdict* did not confirm the runner
    stopped; ``None`` when it did."""
    if verdict in CONFIRMED_KILLS:
        return None
    if verdict == "survived":
        return "it was still running after the kill's SIGKILL window"
    if verdict in ("unresolved", "skipped"):
        return ("not every process could be identified as this run's child, and "
                "what could not was not signalled")
    if verdict is None:
        return "the kill itself failed"
    return f"the kill answered {verdict!r}, which confirms nothing"


def _kill_by_number(
    pid: int,
    start_time: Optional[str],
    pgid: Optional[int],
    escalate_after_s: float,
    poll_interval_s: float,
    job: Optional[TreeJob],
    members: Sequence["Descendant"] = (),
    members_complete: bool = True,
    child: Optional[Any] = None,
    obligations: Optional["KillObligations"] = None,
) -> str:
    """:func:`kill_tree` for a target known only by its numbers: its two
    identity rules, then the kill of the group or the pid. On Linux with
    pidfds and ``/proc``, :func:`_identity_kill` instead."""
    api = None if IS_WINDOWS else _pidfd_api()
    if api is not None:
        return _identity_kill(api, pid, start_time, pgid, members, members_complete,
                              escalate_after_s, poll_interval_s, child, obligations)
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
        return _windows_kill_tree(pid, escalate_after_s, job, child)
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


# ---------------------------------------------------------------------------
# Signals by identity: Linux with pidfds (docs/development/runtime.md,
# "A target known only by number")
# ---------------------------------------------------------------------------
#
# A number names whoever holds it when the signal lands. On Linux with pidfds
# and /proc, no process this one does not own is signalled by a number, and
# only processes identified one by one before the kill are signalled at all:
#
# * the target, by its pid and recorded start time, and the *members* the
#   caller recorded the same way (a detached worker's provider CLIs, a Lane A
#   CLI's snapshotted descendants). Each is *held* by a pidfd verified to name
#   it (`_hold_process`): opened, then its /proc row read, then the pidfd asked
#   whether its process is still there. Every signal goes through that pidfd,
#   which reaches its process or nothing, and whether it has exited is the
#   pidfd's answer too (`_held_state`). No identity, no signal: a target with
#   no recorded start time is held only through the owned child that anchors
#   its pid (`_hold_owned`), and otherwise not at all (``unresolved``);
# * a process group is never signalled, and nothing found in one is. The
#   groups the target and its members were in are only *read*, after the kill
#   (`_IdentityUnit.report`): a process still running there that is none of the
#   held ones may be the target's (a child nobody recorded) or a stranger's
#   (the group's number made again). The kill cannot tell them apart, sends it
#   nothing, and says ``unresolved``;
# * what cannot be read is not taken as gone. A held process whose exit its
#   pidfd cannot answer, a member whose identity cannot be read, a process
#   table that cannot be listed, a member record the caller knows to be
#   incomplete: each makes the verdict ``unresolved``.


class _Pidfds:
    """The pidfd calls (Linux 5.3+): a handle on one process that no later
    process can take over, so a signal sent through it reaches that process or
    fails (``ESRCH`` once it has been reaped). :func:`_pidfd_api` builds it."""

    def __init__(self, open_call: Callable[[int], int],
                 send_call: Callable[..., Any]) -> None:
        self._open = open_call
        self._send = send_call

    def open(self, pid: int) -> Optional[int]:
        """A pidfd on *pid*; ``None`` where none can be had (no descriptor
        left, a sandbox that refuses the call). Raises ``ProcessLookupError``
        when *pid* names no process at all."""
        try:
            return int(self._open(pid))
        except ProcessLookupError:
            raise
        except (OSError, ValueError):
            return None

    def send(self, fd: int, sig: int) -> bool:
        """*sig* to the process *fd* holds; ``False`` when it was not sent."""
        try:
            self._send(fd, sig)
        except OSError:
            return False
        return True

    def exists(self, fd: int) -> bool:
        """Is the process *fd* holds still there (a zombie too)? Only its reap
        ends it, and a process this one may not signal still exists."""
        try:
            self._send(fd, 0)
        except ProcessLookupError:
            return False
        except OSError:
            return True
        return True

    def exited(self, fd: int) -> Optional[bool]:
        """Has the process *fd* holds exited (a zombie, or reaped)? A pidfd
        polls readable from the moment its process exits, on every kernel that
        has the calls (5.3+), so the answer needs no ``/proc`` row. ``None``
        where the poll cannot answer."""
        try:
            poller = select.poll()
            poller.register(fd, select.POLLIN)
            events = poller.poll(0)
        except (OSError, ValueError, AttributeError):
            return None
        for _fd, mask in events:
            if mask & (select.POLLNVAL | select.POLLERR):
                return None
            if mask & (select.POLLIN | select.POLLHUP):
                return True
        return False

    @staticmethod
    def close(fd: int) -> None:
        try:
            os.close(fd)
        except OSError:
            pass


#: :func:`_pidfd_api`'s answer once worked out.
_PIDFDS: List[Optional[_Pidfds]] = []

#: ``pidfd_open`` and ``pidfd_send_signal`` in the generic system-call table,
#: which x86_64, i386 and aarch64 programs share (x32 numbers them apart).
_NR_PIDFD_OPEN = 434
_NR_PIDFD_SEND_SIGNAL = 424


def _syscall_pidfds() -> Optional[Tuple[Callable[[int], int], Callable[..., Any]]]:
    """``pidfd_open`` and ``pidfd_send_signal`` through the C library's
    ``syscall()``, for a Python built without them: the standalone builds
    ``uv`` installs are compiled against kernel headers older than the calls,
    and have neither ``os.pidfd_open`` nor ``signal.pidfd_send_signal``. Only
    where :func:`_sigaction_abi` names the program's ABI, whose numbers are the
    generic table's; ``None`` anywhere else."""
    if _sigaction_abi() is None:
        return None
    try:
        # ctypes loads only on the platform path that calls it.
        import ctypes

        call = ctypes.CDLL(None, use_errno=True).syscall
        call.restype = ctypes.c_long
    except Exception:  # noqa: BLE001 - no syscall(): the kill by number runs
        return None

    def checked(*args: Any) -> int:
        result = call(*(ctypes.c_long(int(arg)) for arg in args))
        if result < 0:
            number = ctypes.get_errno()
            raise OSError(number, os.strerror(number))
        return int(result)

    def open_call(pid: int) -> int:
        return checked(_NR_PIDFD_OPEN, pid, 0)

    def send_call(fd: int, sig: int) -> int:
        return checked(_NR_PIDFD_SEND_SIGNAL, fd, sig, 0, 0)

    return open_call, send_call


def _working_pidfds(api: _Pidfds) -> bool:
    """Do the calls work here: a pidfd on this process opens and answers? A
    kernel older than 5.3 or a sandbox that refuses them fails this."""
    try:
        fd = api.open(os.getpid())
    except ProcessLookupError:
        return False
    if fd is None:
        return False
    try:
        return api.send(fd, 0)
    finally:
        api.close(fd)


def _pidfd_api() -> Optional[_Pidfds]:
    """The pidfd calls where the identity kill runs: Linux with ``/proc`` and
    working pidfds, Python's own (3.9+) whatever the ABI, or else
    :func:`_syscall_pidfds`, only in an ABI :func:`_sigaction_abi` names (its
    numbers are that table's). An undated owned child is held only through
    its anchor (:func:`_hold_owned`), and is otherwise ``unresolved``, never
    signalled by number. ``None`` anywhere else, where the kill by number
    runs. Worked out once."""
    if not _PIDFDS:
        built: Optional[_Pidfds] = None
        if sys.platform == "linux" and os.path.exists("/proc/self/stat"):
            open_call = getattr(os, "pidfd_open", None)
            send_call = getattr(signal, "pidfd_send_signal", None)
            if open_call is not None and send_call is not None:
                built = _Pidfds(open_call, send_call)
            else:
                calls = _syscall_pidfds()
                if calls is not None:
                    built = _Pidfds(*calls)
            if built is not None and not _working_pidfds(built):
                built = None
        _PIDFDS.append(built)
    return _PIDFDS[0]


def signals_by_identity() -> bool:
    """Does a kill of a target known by number go by identity here (Linux
    with pidfds and ``/proc``; the section below)? Where it does, a caller
    hands over every identity it has, since nothing it cannot identify is
    signalled; everywhere else the kill by number runs, as it always did."""
    return not IS_WINDOWS and _pidfd_api() is not None


def _linux_row(pid: int) -> Tuple[bool, Optional["_ProcRow"]]:
    """``(answered, row)``: *pid*'s ``/proc`` row read now, ``None`` when no
    such process is listed; ``answered`` is ``False`` where ``/proc`` cannot
    be read at all."""
    try:
        with open(f"/proc/{pid}/stat", "rb") as handle:
            raw = handle.read()
    except OSError:
        return os.path.exists("/proc/self/stat"), None
    return True, _parse_proc_stat(pid, raw)


@dataclass
class _HeldProc:
    """A process held by a pidfd verified to name it (:func:`_hold_process`)."""

    pid: int
    start_time: str
    fd: int
    #: The group its verified row showed.
    pgid: Optional[int]
    #: The last signal sent through the pidfd, 0 for none.
    sent: int = 0


#: :func:`_hold_process`'s answer for a pid with no identity to check it by.
_UNDATED = "undated"


def _hold_process(api: _Pidfds, pid: Optional[int], start_time: Optional[str],
                  into: List[_HeldProc], me: int) -> str:
    """Hold *pid*: ``held`` once its pidfd is verified and appended to *into*,
    which owns it from then on; ``gone`` when no process has the pid, when the
    pidfd's process was reaped before its row could be paired with it (the row
    may be its replacement's, and is not used), or when it is not the process
    recorded with *start_time*; ``unread`` when its row or a pidfd could not be
    had; :data:`_UNDATED` when there is no *start_time*: whatever has the pid
    now may be another process, so nothing is held (no identity, no signal).
    Every pidfd not handed to *into* is closed, whatever raises."""
    if not pid or pid <= 0 or pid == me:
        return "gone"
    try:
        fd = api.open(int(pid))
    except ProcessLookupError:
        return "gone"
    if fd is None:
        return "unread"
    kept = False
    try:
        if not start_time:
            return _UNDATED
        _answered, row = _linux_row(int(pid))
        if not api.exists(fd):
            return "gone"
        if row is None or not row.start_time:
            return "unread"
        if str(row.start_time) != str(start_time):
            return "gone"
        into.append(_HeldProc(int(pid), str(row.start_time), fd, row.pgid))
        kept = True
        return "held"
    finally:
        # Handed over the moment it is in *into*, whose owner closes it.
        if not kept and not (into and into[-1].fd == fd):
            api.close(fd)


def _hold_owned(api: _Pidfds, child: Optional[Any], pid: Optional[int],
                into: List[_HeldProc], me: int) -> str:
    """Hold *pid*, recorded with no start time, through *child*: the
    ``Popen`` this process holds for it. U74's anchor (an unreaped child's pid
    names that child and nothing else; docs/development/runtime.md, "An owned
    child's kill") is read before the pidfd opens and again after it, so the
    pidfd and the row read next are the child's. :func:`_hold_process`'s
    answers: ``gone`` too once *child* has its exit status (reaped through
    it); :data:`_UNDATED` when there is no such *child* or its anchor does not
    hold or cannot be read (zombie retention not established:
    :func:`_children_become_zombies`), and the pid is still some process's."""
    if (child is None or getattr(child, "pid", None) != pid or not pid or pid <= 0
            or pid == me):
        return _hold_process(api, pid, None, into, me)
    if getattr(child, "returncode", None) is not None:
        return "gone"
    if _owned_anchor(int(pid)) is not True:
        return _hold_process(api, pid, None, into, me)
    try:
        fd = api.open(int(pid))
    except ProcessLookupError:
        return "gone"
    if fd is None:
        return "unread"
    kept = False
    try:
        if _owned_anchor(int(pid)) is not True:
            return _UNDATED
        _answered, row = _linux_row(int(pid))
        if row is None or not row.start_time:
            return "unread"
        into.append(_HeldProc(int(pid), str(row.start_time), fd, row.pgid))
        kept = True
        return "held"
    finally:
        if not kept and not (into and into[-1].fd == fd):
            api.close(fd)


#: :func:`_held_state`'s answers.
_HELD_RUNNING = "running"
_HELD_EXITED = "exited"
_HELD_UNKNOWN = "unknown"


def _held_state(api: _Pidfds, held: _HeldProc,
                table: Optional[Dict[int, "_ProcRow"]]) -> str:
    """Whether *held* runs: its pidfd's answer (exited once it is a zombie or
    reaped). Where the poll cannot answer, a pidfd no longer there is exited,
    and otherwise its ``/proc`` row decides, a zombie being exited; a row that
    cannot be read is :data:`_HELD_UNKNOWN`, never exited."""
    answer = api.exited(held.fd)
    if answer is not None:
        return _HELD_EXITED if answer else _HELD_RUNNING
    if not api.exists(held.fd):
        return _HELD_EXITED
    row = table.get(held.pid) if table is not None else _linux_row(held.pid)[1]
    if row is None or str(row.start_time) != held.start_time:
        return _HELD_UNKNOWN
    return _HELD_EXITED if row.state == "Z" else _HELD_RUNNING


def _own_group() -> Optional[int]:
    try:
        return os.getpgid(0)
    except (OSError, AttributeError):  # pragma: no cover - getpgid(0) does not fail
        return None


class _IdentityUnit:
    """One target of :func:`_identity_run`: the processes held for it, and the
    groups read after the kill for what they still run.

    A group is read when a held process was seen in it during the kill, or
    when the pid of its number is free or belongs to a process recorded as
    the target's. A group's number is the pid of the process that made it and
    is not handed out again while the group has a member, so a group whose
    number is the pid of a live process that is none of the target's was made
    by that process, not by the target, and is not read.
    """

    def __init__(self, own: Optional[int]) -> None:
        self.own = own
        self.held: List[_HeldProc] = []
        #: The groups learned from records: read under the rule above.
        self.recorded_groups: Set[int] = set()
        #: The groups a held process was seen in: always read.
        self.seen_groups: Set[int] = set()
        #: Something of the target could not be read or held.
        self.unknown = False
        #: A recorded pid runs, but as another process (Lane A's ``skipped``).
        self.reused = False
        #: Whether a signal reached a held process while it ran.
        self.ran = False
        #: The last read of the groups: True something unidentified runs
        #: there, False nothing does, None the process table was not read.
        self.found: Optional[bool] = False
        #: The groups that read found running something unidentified (every
        #: group it would have read, when the table was not there).
        self.found_groups: Set[int] = set()
        #: Held processes the settled verdict did not confirm exited, by
        #: identity: ``survived`` (running) or ``unresolved`` (unknown).
        self.left: Dict[Tuple[int, str], str] = {}
        self.verdict: Optional[str] = None

    def _group(self, pgid: Optional[int]) -> Optional[int]:
        try:
            group = int(pgid) if pgid is not None else None
        except (TypeError, ValueError):
            return None
        if group is None or group <= 1 or group == self.own:
            return None
        return group

    def watch(self, pgid: Optional[int]) -> None:
        group = self._group(pgid)
        if group is not None:
            self.recorded_groups.add(group)

    def saw(self, pgid: Optional[int]) -> None:
        group = self._group(pgid)
        if group is not None:
            self.seen_groups.add(group)

    def note(self, table: Optional[Dict[int, "_ProcRow"]]) -> None:
        """The groups *table* shows each held process in (a member may move)."""
        if table is None:
            return
        for held in self.held:
            row = table.get(held.pid)
            if row is not None and str(row.start_time) == held.start_time:
                self.saw(row.pgid)

    def _send(self, api: _Pidfds, held: _HeldProc, sig: int) -> None:
        if api.send(held.fd, sig):
            held.sent = sig
            self.ran = True

    def signal(self, api: _Pidfds, sig: int,
               table: Optional[Dict[int, "_ProcRow"]]) -> None:
        """*sig* to every held process not known to have exited that has not
        had it yet (a pidfd reaches its process or nothing)."""
        for held in self.held:
            if held.sent == signal.SIGKILL or held.sent == sig:
                continue
            if _held_state(api, held, table) != _HELD_EXITED:
                self._send(api, held, sig)

    def pending(self, api: _Pidfds, table: Optional[Dict[int, "_ProcRow"]]) -> bool:
        """Is a held process running, or not known to have exited?"""
        return any(_held_state(api, held, table) != _HELD_EXITED for held in self.held)

    def read_groups(self, table: Dict[int, "_ProcRow"],
                    known: Set[Tuple[int, str]]) -> Set[int]:
        """The groups this unit reads in *table*: every group a held process
        was seen in, and each recorded group whose number is the pid of no
        live process or of a held or recorded one (the class docstring)."""
        groups = set(self.seen_groups)
        for group in self.recorded_groups - groups:
            leader = table.get(group)
            if leader is None or (leader.pid, str(leader.start_time)) in known:
                groups.add(group)
        return groups

    def report(self, table: Optional[Dict[int, "_ProcRow"]],
               known: Set[Tuple[int, str]], me: int) -> Optional[bool]:
        """Does a group of this unit run a process that is not a held or
        recorded one (zombies aside)? ``None`` when *table* is not there."""
        if table is None:
            self.found_groups = set(self.seen_groups) | self.recorded_groups
            self.found = None if self.found_groups else False
            return self.found
        groups = self.read_groups(table, known)
        self.found_groups = {
            row.pgid for row in table.values()
            if row.pgid in groups and row.state != "Z" and row.pid != me
            and (row.pid, str(row.start_time)) not in known}
        self.found = bool(self.found_groups)
        return self.found

    def settle(self, api: _Pidfds, table: Optional[Dict[int, "_ProcRow"]]) -> None:
        if self.verdict is not None:
            return
        states = [_held_state(api, held, table) for held in self.held]
        for held, state in zip(self.held, states):
            if state == _HELD_RUNNING:
                self.left[(held.pid, held.start_time)] = "survived"
            elif state == _HELD_UNKNOWN:
                self.left[(held.pid, held.start_time)] = "unresolved"
        if _HELD_RUNNING in states:
            self.verdict = "survived"
        elif self.unknown or _HELD_UNKNOWN in states or self.found is not False:
            self.verdict = "unresolved"
        elif self.ran:
            self.verdict = "killed"
        elif self.reused and not self.held:
            self.verdict = "skipped"
        else:
            self.verdict = "gone"

    def close(self, api: _Pidfds) -> None:
        for held in self.held:
            api.close(held.fd)
        self.held = []


def _identity_wait(api: _Pidfds, units: Sequence[_IdentityUnit], until: float,
                   poll_interval_s: float) -> Optional[Dict[int, "_ProcRow"]]:
    """Until no held process is pending, or *until*: one ``/proc`` pass per
    poll, which also notes where each held process is. The last pass."""
    while True:
        looked = time.monotonic()
        table = _linux_process_table()
        for unit in units:
            unit.note(table)
        if not any(unit.pending(api, table) for unit in units):
            return table
        now = time.monotonic()
        if now >= until:
            return table
        rest = max(poll_interval_s - (now - looked),
                   poll_interval_s * _POLL_SLEEP_FLOOR_SHARE)
        time.sleep(max(0.0, min(rest, until - now)))


def _identity_report(units: Sequence[_IdentityUnit], until: float,
                     poll_interval_s: float, known: Set[Tuple[int, str]],
                     me: int) -> Optional[Dict[int, "_ProcRow"]]:
    """Read every unit's groups until none runs anything unidentified, or
    *until* (at least once): what the held processes' own ends take with them
    gets that long to go. Signals nothing. The last pass."""
    while True:
        looked = time.monotonic()
        table = _linux_process_table()
        for unit in units:
            unit.note(table)
        if not [unit for unit in units if unit.report(table, known, me) is not False]:
            return table
        now = time.monotonic()
        if now >= until:
            return table
        rest = max(poll_interval_s - (now - looked),
                   poll_interval_s * _POLL_SLEEP_FLOOR_SHARE)
        time.sleep(max(0.0, min(rest, until - now)))


def _identity_run(api: _Pidfds, units: Sequence[_IdentityUnit], grace_s: float,
                  clock: "_SweepClock", poll_interval_s: float,
                  recorded: Set[Tuple[int, str]]) -> None:
    """SIGTERM, the grace, SIGKILL, the confirmation, for *units* at once, each
    held process through its own pidfd; then the read of their groups, until
    nothing unidentified runs there or the confirmation window ends; settles
    every unit's verdict. *recorded* are the identities known as the targets'
    (held or not), which the read does not count as unidentified."""
    me = os.getpid()
    known = set(recorded) | {(h.pid, h.start_time) for unit in units for h in unit.held}
    table = _linux_process_table()
    for unit in units:
        unit.note(table)
        unit.signal(api, signal.SIGTERM, table)
    table = _identity_wait(api, units, clock.grace_until(grace_s), poll_interval_s)
    until: Optional[float] = None
    if any(unit.pending(api, table) for unit in units):
        for unit in units:
            unit.signal(api, signal.SIGKILL, table)
        until = clock.confirm_until()
        _identity_wait(api, units, until, poll_interval_s)
    if until is None:
        until = clock.confirm_until()
    table = _identity_report(units, until, poll_interval_s, known, me)
    for unit in units:
        unit.settle(api, table)


class KillObligations:
    """What a kill by identity could not confirm stopped, each by what names
    it, so that a later look can re-check it on its own (:meth:`outstanding`):
    a teardown that kills again must not let the later verdict stand for what
    only the earlier kill saw (``detach.stop_recorded_run``;
    docs/development/runtime.md, "When not everything is confirmed stopped").
    :func:`kill_tree` fills one passed as *obligations* on the kill by
    identity; anywhere else it stays empty."""

    def __init__(self) -> None:
        #: Groups read after the kill and found running something not
        #: identified as the target's, or not read at all.
        self.groups: Set[int] = set()
        #: Identities not confirmed stopped, ``(pid, start time or None)``,
        #: with the verdict each owes: ``survived``, ``unresolved`` (not held
        #: or not read) or ``skipped`` (nothing sent: its row was unread).
        self.identities: Dict[Tuple[int, Optional[str]], str] = {}
        #: The record the kill was handed could not vouch for every launch;
        #: only a later read of that record re-checks it.
        self.record_incomplete = False

    def named(self) -> bool:
        """Does it name anything? A kill with an unconfirmed verdict and
        nothing named owes what its verdict says, unclearable."""
        return bool(self.groups or self.identities or self.record_incomplete)

    def owe(self, pid: int, start_time: Optional[str], verdict: str) -> None:
        key = (int(pid), str(start_time) if start_time else None)
        earlier = self.identities.get(key)
        if earlier is None or _OBLIGATION_ORDER.index(verdict) < _OBLIGATION_ORDER.index(earlier):
            self.identities[key] = verdict

    def take(self, unit: "_IdentityUnit") -> None:
        """What *unit*'s settled kill left."""
        for (pid, start), verdict in unit.left.items():
            self.owe(pid, start, verdict)
        self.groups |= unit.found_groups

    def outstanding(self) -> List[str]:
        """The verdict each named obligation still owes, re-checked now,
        read-only, from one ``/proc`` pass (the record's aside: the caller's
        later read re-checks it). A group is cleared once it runs nothing but
        zombies; an identity once no process runs as it (no row for its pid,
        another start time, a zombie), and one with no start time only once no
        process but a zombie has its pid. Nothing is cleared when the table
        cannot be read, or a row's start time is missing."""
        if not self.groups and not self.identities:
            return []
        table = _linux_process_table()
        if table is None:
            return ["unresolved"] * len(self.groups) + list(self.identities.values())
        me = os.getpid()
        owed = ["unresolved" for group in sorted(self.groups) if any(
            row.pgid == group and row.state != "Z" and row.pid != me
            for row in table.values())]
        for (pid, start), verdict in self.identities.items():
            row = table.get(pid)
            if row is None or row.state == "Z":
                continue
            if start is None or not row.start_time or str(row.start_time) == start:
                owed.append(verdict)
        return owed


#: :class:`KillObligations`' verdicts, worst first.
_OBLIGATION_ORDER = ("survived", "unresolved", "skipped")


def _own_session() -> Optional[int]:
    try:
        return os.getsid(0)
    except (OSError, AttributeError):  # pragma: no cover - getsid(0) does not fail
        return None


def _session_of(api: _Pidfds, held: _HeldProc) -> Optional[int]:
    """The session *held* is in now: its row's, read and then confirmed its
    own by the pidfd (the process is still there, so the row was its). A
    zombie still counts: until it is reaped its pid, group and session
    numbers stay taken. ``None`` when that cannot be read."""
    _answered, row = _linux_row(held.pid)
    if (row is None or str(row.start_time) != held.start_time or row.sid is None
            or not api.exists(held.fd)):
        return None
    return int(row.sid)


def _hold_session_members(api: _Pidfds, unit: _IdentityUnit,
                          recorded: Set[Tuple[int, str]], me: int) -> None:
    """Hold the processes nobody recorded that the unit's groups run, where a
    held recorded process proves them the run's: they are in its session.

    A session is never joined: a process is in one by being forked inside it,
    and leaves it only for a session of its own. So every process in a
    session descends from its creator, and a session's number stays taken
    while any process is in it (alive or a zombie). A held process seen in a
    session before the scan and again after it was in that session the whole
    time, so the number named that session throughout, and whatever the scan
    found in it is the run's: never a stranger's group made again under a
    recycled number (docs/development/runtime.md, "A target known only by
    number"). Each such process is held like any target, by its start time
    through a pidfd verified to name it; a process the scan found in a session
    whose anchor no longer proves it is let go. Never this process's own
    session, nor a process outside the groups the unit reads. Signals nothing.
    """
    own = _own_session()
    anchors: List[Tuple[_HeldProc, int]] = []
    for held in unit.held:
        sid = _session_of(api, held)
        if sid is not None and sid > 1 and sid != own:
            anchors.append((held, sid))
    sessions = {sid for _held, sid in anchors}
    if not sessions:
        return
    table = _linux_process_table()
    if table is None:
        return
    known = set(recorded) | {(h.pid, h.start_time) for h in unit.held}
    groups = unit.read_groups(table, known)
    added: List[Tuple[_HeldProc, int]] = []
    for row in table.values():
        if (row.pgid not in groups or row.sid not in sessions or row.state == "Z"
                or row.pid == me or not row.start_time
                or (row.pid, str(row.start_time)) in known):
            continue
        held = _hold_member_of(api, row)
        if held is not None:
            unit.held.append(held[0])
            added.append(held)
    if not added:
        return
    proven = {sid for held, sid in anchors if _session_of(api, held) == sid}
    for held, sid in added:
        if sid not in proven:
            unit.held.remove(held)
            api.close(held.fd)


def _hold_member_of(api: _Pidfds, row: "_ProcRow") -> Optional[Tuple[_HeldProc, int]]:
    """*row*'s process held by a pidfd, with the session its row showed:
    the pidfd opened, the row read again and the pidfd asked after it, so the
    row is the pidfd's process, and that row must show the start time and
    session *row* did. ``None`` otherwise (its pidfd closed)."""
    try:
        fd = api.open(row.pid)
    except ProcessLookupError:
        return None
    if fd is None:
        return None
    _answered, again = _linux_row(row.pid)
    if (not api.exists(fd) or again is None or not again.start_time
            or str(again.start_time) != str(row.start_time) or again.sid != row.sid
            or again.sid is None):
        api.close(fd)
        return None
    return _HeldProc(row.pid, str(again.start_time), fd, again.pgid), int(again.sid)


def _identity_kill(
    api: _Pidfds,
    pid: Optional[int],
    start_time: Optional[str],
    pgid: Optional[int],
    members: Sequence["Descendant"],
    members_complete: bool,
    escalate_after_s: float,
    poll_interval_s: float,
    child: Optional[Any] = None,
    obligations: Optional[KillObligations] = None,
) -> str:
    """:func:`kill_tree` by identity (the section above), for a target known
    by its numbers: *pid* and every member held and signalled, the recorded
    *pgid*, each member's recorded group and every group a held process is
    seen in read afterwards.

    *pid* is held by its recorded *start_time*; without one, only through
    *child* while it anchors the pid (:func:`_hold_owned`). With neither it is
    not held: nothing is sent to it, its members are still held by their own
    identities, and the verdict is ``unresolved`` unless no process has the
    pid at all.

    ``skipped`` when *pid* runs but its identity cannot be read, and nothing
    is sent at all; otherwise the unit's verdict
    (:meth:`_IdentityUnit.settle`): ``unresolved`` too when a member could not
    be held or read, or *members_complete* is false. *obligations*, when
    given, gets what that verdict leaves unconfirmed (:class:`KillObligations`).
    """
    me = os.getpid()
    unit = _IdentityUnit(_own_group())
    recorded: Set[Tuple[int, str]] = set()
    owed = obligations if obligations is not None else KillObligations()
    try:
        if not pid:
            target = "gone"
        elif start_time:
            target = _hold_process(api, pid, start_time, unit.held, me)
        else:
            target = _hold_owned(api, child, pid, unit.held, me)
        if target == "unread":
            owed.owe(int(pid), start_time, "skipped")
            return "skipped"
        if target == _UNDATED:
            unit.unknown = True
            owed.owe(int(pid), None, "unresolved")
        if pid and start_time:
            recorded.add((int(pid), str(start_time)))
        unit.watch(pgid)
        if target == "held":
            unit.saw(unit.held[0].pgid)
        for member in members:
            if not member.start_time:
                unit.unknown = True
                owed.owe(member.pid, None, "unresolved")
                continue
            recorded.add((int(member.pid), str(member.start_time)))
            unit.watch(member.pgid)
            if any((h.pid, h.start_time) == (member.pid, str(member.start_time))
                   for h in unit.held):
                continue
            outcome = _hold_process(api, member.pid, member.start_time, unit.held, me)
            if outcome == "unread":
                unit.unknown = True
                owed.owe(member.pid, member.start_time, "unresolved")
            elif outcome == "held":
                unit.saw(unit.held[-1].pgid)
        if not members_complete:
            unit.unknown = True
            owed.record_incomplete = True
        _hold_session_members(api, unit, recorded, me)
        _identity_run(api, [unit], escalate_after_s, _SweepClock(), poll_interval_s,
                      recorded)
        owed.take(unit)
        return str(unit.verdict)
    finally:
        unit.close(api)


#: ``os.waitid`` where the platform has it, else ``None``: the kernel's own
#: answer to "has this child exited", asked with ``WNOWAIT`` so it never reaps.
#: Every Linux Python has it; the owned kill does not run without it.
_waitid = getattr(os, "waitid", None)

#: ``SA_NOCLDWAIT`` on the machines below, under glibc and musl alike.
_SA_NOCLDWAIT = 0x2

_X86_MACHINES = frozenset({"x86_64", "i386", "i486", "i586", "i686"})

#: The programs whose ``struct sigaction`` is laid out as a handler, a 1024-bit
#: mask, an ``int`` of flags and a restorer, with ``SA_NOCLDWAIT`` at ``0x2``:
#: read in both libraries' sources (glibc's generic ``bits/sigaction.h``,
#: overridden for none of these; musl's ``signal.h`` and its per-machine
#: ``bits/signal.h``). Each is known by the dynamic loader it names, which is
#: the C library's and the ABI's own (musl's, ``ld-musl-$(ARCH).so.1``, is its
#: C library too), paired with the kernel machines that run it,
#: since Alpha, SPARC and SuperH name their glibc loader ``ld-linux.so.2`` as
#: i386 does. Loader name -> (C library, machines). Not here: x32, 32-bit Arm
#: (on an aarch64 kernel too), MIPS (flags first), RISC-V, PowerPC, s390x and
#: every other ABI not read.
_CHECKED_LOADERS: Dict[str, Tuple[str, frozenset]] = {
    "ld-linux-x86-64.so.2": ("glibc", _X86_MACHINES),
    "ld-linux.so.2": ("glibc", _X86_MACHINES),
    "ld-linux-aarch64.so.1": ("glibc", frozenset({"aarch64"})),
    "ld-musl-x86_64.so.1": ("musl", _X86_MACHINES),
    "ld-musl-i386.so.1": ("musl", _X86_MACHINES),
    "ld-musl-aarch64.so.1": ("musl", frozenset({"aarch64"})),
}

#: :func:`_sigaction_abi`'s answer once worked out.
_SIGACTION_ABI: List[Optional[str]] = []

#: The built ``sigaction`` call and its struct, once :func:`_sigchld_action`
#: has built them (``[None]`` when they cannot be).
_SIGACTION: List[Optional[Tuple[Any, Any]]] = []


def _glibc_version() -> Optional[str]:
    """glibc's name for itself (``glibc 2.39``), from
    ``confstr(_CS_GNU_LIBC_VERSION)``; ``None`` under any other C library, which
    has no such name or refuses it (musl: ``EINVAL``)."""
    try:
        version = os.confstr("CS_GNU_LIBC_VERSION")
    except (AttributeError, ValueError, OSError):
        return None
    if isinstance(version, str) and version.startswith("glibc "):
        return version
    return None


def _program_interpreter(path: str = "/proc/self/exe") -> Optional[str]:
    """The dynamic loader the ELF file at *path* names (its ``PT_INTERP``): for
    this process's own executable, the loader the kernel started it with.
    ``None`` for a static executable, a file that is not ELF, or one that
    cannot be read."""

    try:
        with open(path, "rb") as exe:
            header = exe.read(64)
            if len(header) < 52 or header[:4] != b"\x7fELF":
                return None
            if header[4] not in (1, 2) or header[5] not in (1, 2):
                return None
            wide = header[4] == 2
            order = "<" if header[5] == 1 else ">"
            if wide:
                (table_at,) = struct.unpack_from(order + "Q", header, 32)
                size, count = struct.unpack_from(order + "HH", header, 54)
            else:
                (table_at,) = struct.unpack_from(order + "I", header, 28)
                size, count = struct.unpack_from(order + "HH", header, 42)
            if size < (56 if wide else 32) or size * count > 65536:
                return None
            exe.seek(table_at)
            table = exe.read(size * count)
            for index in range(len(table) // size):
                entry = table[index * size:(index + 1) * size]
                if struct.unpack_from(order + "I", entry, 0)[0] != 3:  # PT_INTERP
                    continue
                if wide:
                    (offset,) = struct.unpack_from(order + "Q", entry, 8)
                    (length,) = struct.unpack_from(order + "Q", entry, 32)
                else:
                    (offset,) = struct.unpack_from(order + "I", entry, 4)
                    (length,) = struct.unpack_from(order + "I", entry, 16)
                exe.seek(offset)
                name = exe.read(min(length, 4096)).split(b"\0", 1)[0]
                return name.decode("ascii") or None
    except (OSError, ValueError, struct.error, UnicodeDecodeError):
        return None
    return None


def _identify_sigaction_abi() -> Optional[str]:
    """See :func:`_sigaction_abi`."""
    if sys.platform != "linux" or hasattr(sys, "getandroidapilevel"):
        return None  # another kernel, or Android's Bionic (Python < 3.13)
    interpreter = _program_interpreter()
    if interpreter is None:
        return None  # static, or not read: no loader names the ABI
    library, machines = _CHECKED_LOADERS.get(interpreter.rsplit("/", 1)[-1], (None, ()))
    try:
        machine = os.uname().machine
    except (AttributeError, OSError):
        return None
    if library is None or machine not in machines:
        return None
    # glibc names itself and musl refuses the name: each must agree with its loader.
    if (_glibc_version() is not None) != (library == "glibc"):
        return None
    return library


def _sigaction_abi() -> Optional[str]:
    """``glibc`` or ``musl`` when this process runs on one under Linux, in an
    ABI whose ``struct sigaction`` layout was checked (:data:`_CHECKED_LOADERS`),
    identified positively: its executable names that ABI's loader, the kernel's
    machine runs it, and glibc names itself (musl does not). There
    :func:`_sigchld_action` knows the layout, and the owned kill's proof holds
    (docs/development/runtime.md, "An owned child's kill"). ``None`` anywhere
    else: another kernel, Bionic, any other C library, a statically linked
    program (no loader to name it), an ABI not checked. Worked out once.
    """
    if not _SIGACTION_ABI:
        _SIGACTION_ABI.append(_identify_sigaction_abi())
    return _SIGACTION_ABI[0]


def _sigchld_action() -> Optional[Tuple[int, int]]:
    """SIGCHLD's handler and flags as the kernel holds them, read with
    ``sigaction(SIGCHLD, NULL, &old)``; ``None`` where that cannot be read,
    which includes every platform :func:`_sigaction_abi` does not name: there
    the struct's layout is not known, and no call is made.

    ``signal.getsignal`` answers from Python's own record of the handlers set
    through the ``signal`` module: it misses ``SA_NOCLDWAIT``, a flag, and any
    disposition a native library set.
    """
    if _sigaction_abi() is None:
        return None
    try:
        if not _SIGACTION:
            # ctypes loads only on the platform path that calls it.
            import ctypes

            words = 1024 // (8 * ctypes.sizeof(ctypes.c_ulong))

            class _SigAction(ctypes.Structure):
                _fields_ = [
                    ("handler", ctypes.c_void_p),
                    ("mask", ctypes.c_ulong * words),
                    ("flags", ctypes.c_int),
                    ("restorer", ctypes.c_void_p),
                ]

            call = ctypes.CDLL(None, use_errno=True).sigaction
            call.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(_SigAction)]
            call.restype = ctypes.c_int
            _SIGACTION.append((call, _SigAction))
        built = _SIGACTION[0]
        if built is None:
            return None
        call, struct = built
        old = struct()
        if call(int(signal.SIGCHLD), None, old) != 0:
            return None
        return int(old.handler or 0), int(old.flags)
    except Exception:  # noqa: BLE001 - unread: the owned kill does not run on it
        if not _SIGACTION:
            _SIGACTION.append(None)
        return None


def _children_become_zombies() -> Optional[bool]:
    """Does a child of this process stay a zombie until it is waited for?

    ``False`` with SIGCHLD set to ``SIG_IGN`` or flagged ``SA_NOCLDWAIT``: the
    kernel then reaps every child at its exit. Where the kernel's answer can
    be read (:func:`_sigchld_action`) it decides. Elsewhere on Linux it is
    ``True`` once this process reset SIGCHLD itself
    (:func:`restore_sigchld_default`) and Python still holds no ``SIG_IGN``:
    ``signal.signal`` installs a fresh ``sigaction`` whose only flag is
    ``SA_ONSTACK``, which clears an ``SA_NOCLDWAIT`` set before it, and every
    later change made through the ``signal`` module goes the same way.
    ``None`` otherwise (no reset made, or another kernel, whose ``killpg``
    the owned kill's proof does not cover). ``signal.getsignal`` alone only
    ever refuses: a ``SIG_IGN`` set through the ``signal`` module is a
    ``no``, but its default handler proves nothing, since it never sees a
    flag or a native library's setting.
    """
    if signal.getsignal(signal.SIGCHLD) == signal.SIG_IGN:
        return False
    action = _sigchld_action()
    if action is None:
        return True if _SIGCHLD_RESET and sys.platform == "linux" else None
    handler, flags = action
    return handler != int(signal.SIG_IGN) and not flags & _SA_NOCLDWAIT


#: ``[True]`` once :func:`restore_sigchld_default` reset SIGCHLD in this
#: process, which clears any ``SA_NOCLDWAIT`` set before it: what
#: :func:`_children_become_zombies` rests on where it cannot read the flags.
_SIGCHLD_RESET: List[bool] = []


def restore_sigchld_default() -> None:
    """At a process entry (the CLI's, the detached worker's, an orchestrator
    run directly): SIGCHLD back to ``SIG_DFL`` through ``signal.signal``,
    unless a handler is installed (a Python one, or a native one Python
    reports as ``None``). That clears an inherited
    ``SIG_IGN``, which an ``exec`` keeps, and an ``SA_NOCLDWAIT`` a native
    library set before it (CPython's ``PyOS_setsig`` installs a fresh
    ``sigaction``, flags ``SA_ONSTACK`` only; measured with ``SA_NOCLDWAIT``
    set natively, 2026-11-10). Either has the kernel reap every child at its
    exit, so a ``Popen`` whose ``returncode`` is ``None`` no longer reserves
    its pid, and every kill of a child this process holds rests on that
    reservation (docs/development/runtime.md, "An owned child's kill"). A
    reset made is recorded (:data:`_SIGCHLD_RESET`): zombie retention is then
    known, ABI or not. POSIX only, from the main thread only (elsewhere
    nothing is reset or recorded); never raises."""
    if IS_WINDOWS:
        return
    try:
        if signal.getsignal(signal.SIGCHLD) not in (signal.SIG_DFL, signal.SIG_IGN):
            return  # someone's handler, Python's or native: left alone, nothing claimed
        # subprocess needs it anyway: under SIG_IGN every Popen reads its child's exit as 0.
        signal.signal(signal.SIGCHLD, signal.SIG_DFL)
    except (ValueError, OSError, AttributeError):  # not the main thread; no SIGCHLD
        return
    _SIGCHLD_RESET[:] = [True]


class _OwnedTree(NamedTuple):
    """A child of this process that :func:`kill_tree` was handed, unreaped."""

    pid: int
    #: The group the child leads (its number is the child's pid), or ``None``:
    #: the child is then signalled alone.
    group: Optional[int]


def _owned_child_exited(pid: int) -> Optional[bool]:
    """Has *pid*, an unreaped child of this process, exited? ``None`` when it is
    no such child (never this process's, or reaped already), or when there is
    no ``waitid`` to ask. ``WNOWAIT`` leaves the zombie to its ``Popen``."""
    if _waitid is None:
        return None
    try:
        exited = _waitid(os.P_PID, pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
    except OSError:
        return None
    return exited is not None


def own_child_stopped(child: Any, pgid: Optional[int]) -> bool:
    """Has *child*, this process's ``Popen``, exited (its zombie, unreaped,
    has), with no process of group *pgid* still running? The kill by number
    reports such a child ``survived``: its zombie still answers
    ``kill(pid, 0)``. Asked once that kill has returned, read-only where
    ``waitid`` answers (``WNOWAIT``), else through the ``Popen``'s own
    ``poll``, which the caller's drain would make anyway. ``False`` wherever
    it cannot be confirmed: a group that cannot be read, a row whose state is
    unknown, Windows."""
    pid = getattr(child, "pid", None)
    if IS_WINDOWS or not isinstance(pid, int) or pid <= 0:
        return False
    if getattr(child, "returncode", None) is None:
        exited = _owned_child_exited(pid)
        if exited is None:
            try:
                exited = child.poll() is not None
            except Exception:  # noqa: BLE001 - unconfirmed
                return False
        if not exited:
            return False
    if not pgid:
        return True
    table = _process_table()
    if not table:
        return False
    me = os.getpid()
    return not any(row.pgid == pgid and row.pid != me and row.state != "Z"
                   for row in table.values())


def _owned_anchor(pid: int) -> Optional[bool]:
    """Does *pid* anchor the owned kill right now? ``True`` while it is this
    process's unreaped child in a process whose children become zombies,
    ``False`` once either is known not to hold, ``None`` when zombie retention
    is not established (:func:`_children_become_zombies`). A reading, taken right
    before each signal: it cannot stop a reap that follows it
    (docs/development/runtime.md, "An owned child's kill")."""
    zombies = _children_become_zombies()
    if zombies is False or _owned_child_exited(pid) is None:
        return False
    return zombies


def _owned_tree(child: Any, pid: int, pgid: Optional[int]) -> Optional[_OwnedTree]:
    """*pid*'s tree when *child* anchors it, else ``None``.

    The anchor (docs/development/runtime.md, "An owned child's kill"): a pid is
    not reused until its process is reaped, only its parent reaps it, and this
    process does so through *child* once :func:`kill_tree` has returned. Until
    then the pid names that child and nothing else, and so does the number of
    the group it leads, since no new process can take that number to lead a
    group or a session of its own. That holds only under the contract the doc
    states: nothing else in this process waits on *child* or reaps children it
    does not name, and children become zombies (SIGCHLD neither ``SIG_IGN`` nor
    ``SA_NOCLDWAIT``: read from the kernel where :func:`_sigaction_abi` names
    the C library, or established by this process's reset,
    :func:`_children_become_zombies`). Only the group the child leads is
    anchored: a group of any other number is not.
    """
    if getattr(child, "pid", None) != pid or getattr(child, "returncode", 0) is not None:
        return None
    if _owned_anchor(int(pid)) is not True:
        return None
    group = _resolve_pgid(pgid, pid)
    if group is not None and group != pid:
        return None
    return _OwnedTree(int(pid), group)


def _signal_owned(tree: _OwnedTree, sig: int) -> Optional[bool]:
    """*sig* to the child's group, else to the child alone, each only while
    the anchor holds (:func:`_owned_anchor`, read right before it). ``True``
    once sent; nothing sent and ``False`` once the anchor is known to fail,
    ``None`` once it cannot be read."""
    anchor = _owned_anchor(tree.pid)
    if anchor is not True:
        return anchor
    if tree.group is not None:
        try:
            os.killpg(tree.group, sig)
            return True
        except OSError:
            pass
        anchor = _owned_anchor(tree.pid)
        if anchor is not True:
            return anchor
    try:
        os.kill(tree.pid, sig)
    except OSError:
        pass
    return True


def _owned_tree_runs(tree: _OwnedTree, not_before: float, max_age_s: float) -> bool:
    """Does anything of *tree* run: the child until it has exited (a zombie
    has), then any process in its group that is not a zombie, whenever it
    joined. A waiting look (:func:`_waiting_process_table`).

    ``False`` only means one look saw nothing run. A look is not atomic: a
    member can fork a child after the table's names were read and exit before
    its own row was, leaving the child unlisted. So ``False`` is proof only
    once every member has its SIGKILL (:func:`_posix_kill_owned`).
    """
    if _owned_child_exited(tree.pid) is False:
        return True
    if tree.group is None:
        return False
    return _Liveness(not_before, max_age_s).group_running(tree.group)


def _await_owned_tree(tree: _OwnedTree, until: float, poll_interval_s: float) -> bool:
    """Poll until nothing of *tree* runs (``True``) or *until* passes
    (``False``), never sleeping past *until*."""
    began = time.monotonic()
    while True:
        if not _owned_tree_runs(tree, began, poll_interval_s):
            return True
        now = time.monotonic()
        if now >= until:
            return False
        time.sleep(max(0.0, min(poll_interval_s, until - now)))


def _posix_kill_owned(
    tree: _OwnedTree,
    escalate_after_s: float,
    poll_interval_s: float,
    *,
    by_number: Callable[[float], str],
) -> str:
    """SIGTERM, the grace, then always one SIGKILL to the group, confirm.

    The grace ends early once a look sees nothing of *tree* run, but no look
    alone proves the tree gone (:func:`_owned_tree_runs`), so the SIGKILL goes
    out either way: by the group's number, which stays the child's while the
    anchor holds, and with only the child's zombie left it changes nothing. On
    Linux a process that has its SIGKILL can fork no other (the fork is
    abandoned), so a look after it that sees nothing run does prove the group
    gone: ``killed``. ``survived`` when something still runs
    :data:`_KILL_CONFIRM_S` after the SIGKILL, or when the anchor was known to
    fail before the SIGKILL (:func:`_owned_anchor`) and it was not sent;
    ``skipped`` when it was known to fail before the SIGTERM, and nothing was
    sent. Once the anchor cannot be read, the rest of the kill is *by_number*
    (:func:`_kill_by_number`, given the grace still owed): the owned path
    sends nothing it has not verified.
    """
    sent = _signal_owned(tree, signal.SIGTERM)
    if sent is None:
        return by_number(max(escalate_after_s, 0.0))
    if not sent:
        return "skipped"
    _await_owned_tree(tree, time.monotonic() + max(escalate_after_s, 0.0), poll_interval_s)
    sent = _signal_owned(tree, signal.SIGKILL)
    if sent is None:
        return by_number(0.0)
    if not sent:
        return "survived"
    if _await_owned_tree(tree, time.monotonic() + _KILL_CONFIRM_S, poll_interval_s):
        return "killed"
    return "survived"


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
        # ctypes loads only on the platform path that calls it.
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


class ChildLedger:
    """The children :func:`popen_tree` started inside one :func:`child_ledger`
    block, and what their spawner recorded about stopping them.

    A child has *ended* when its spawner recorded a confirmed stop
    (:func:`note_stop`), or when it was seen to exit and no unconfirmed stop
    was recorded for it. An unconfirmed stop sticks: a CLI that exited while a
    process group it started survived the sweep has not ended. A child still
    running, or one whose exit cannot be read, has not ended either.
    """

    def __init__(self, parent: Optional["ChildLedger"] = None) -> None:
        self.parent = parent
        self.closed = False
        self._lock = threading.Lock()
        #: ``[child, stop]``: stop is ``None`` (none recorded), True or False.
        self._children: List[List[Any]] = []

    def _entry(self, child: Any) -> List[Any]:
        """*child*'s entry, added when missing; called with the lock held."""
        for entry in self._children:
            if entry[0] is child:
                return entry
        entry = [child, None]
        self._children.append(entry)
        return entry

    def add(self, child: Any) -> None:
        with self._lock:
            self._entry(child)

    def stopped(self, child: Any, confirmed: bool) -> None:
        with self._lock:
            entry = self._entry(child)
            entry[1] = bool(confirmed) and entry[1] is not False

    def all_ended(self) -> bool:
        """Has every child recorded here ended? True when there is none."""
        with self._lock:
            entries = [tuple(entry) for entry in self._children]
        for child, stop in entries:
            if stop is False:
                return False
            if stop is None and not _child_exited(child):
                return False
        return True


def _child_exited(child: Any) -> bool:
    """Was *child* seen to exit? Its ``Popen`` exit status, read without waiting."""
    if getattr(child, "returncode", None) is not None:
        return True
    try:
        return child.poll() is not None
    except Exception:  # noqa: BLE001 - an unreadable exit is not an exit
        return False


_CHILD_LEDGER: "contextvars.ContextVar[Optional[ChildLedger]]" = contextvars.ContextVar(
    "process_control_child_ledger", default=None
)


@contextmanager
def child_ledger() -> Iterator[ChildLedger]:
    """Record every child :func:`popen_tree` starts in this block's context.

    Blocks nest: a child started in an inner block is in every open ledger
    around it too. Each context has its own, so concurrent threads never
    record each other's children.
    """
    ledger = ChildLedger(_CHILD_LEDGER.get())
    token = _CHILD_LEDGER.set(ledger)
    try:
        yield ledger
    finally:
        ledger.closed = True
        try:
            _CHILD_LEDGER.reset(token)
        except ValueError:  # left in another context: the closed ledger takes no more
            pass


def _open_ledgers() -> Iterator[ChildLedger]:
    ledger = _CHILD_LEDGER.get()
    while ledger is not None:
        if not ledger.closed:
            yield ledger
        ledger = ledger.parent


def note_stop(child: Any, confirmed: bool) -> None:
    """Record how *child*'s spawner stopped it, in every open ledger.

    *confirmed* is the spawner's verdict on its own stop: True only when the
    child and everything the stop reached were confirmed gone. Never raises.
    """
    try:
        for ledger in _open_ledgers():
            ledger.stopped(child, confirmed)
    except Exception:  # noqa: BLE001 - bookkeeping never fails a teardown
        pass


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

    Every provider run comes through here (Lane A's CLI, the executor's
    task, in a session of its own or not), so this is also where a detached
    worker records each process it starts, by pid, start time and group
    (:func:`record_cli_identities`): :class:`LaunchRefused` (an ``OSError``)
    before anything is started when that record cannot be written, or when an
    abort has closed the run's launch gate (:func:`close_launch_gate`). The
    bounded version, help and auth probes run through ``subprocess.run`` and
    are not recorded. The child also goes into every open
    :func:`child_ledger`.
    """
    token = _record_launch()
    flags = kwargs.get("creationflags")
    try:
        proc, job = _popen_tree(args, kwargs)
    except BaseException:
        _record_failed(token)
        raise
    _note_console_group(proc, flags)
    _record_spawned(token, proc)
    for ledger in _open_ledgers():
        ledger.add(proc)
    return proc, job


def _popen_tree(args: Any, kwargs: Dict[str, Any]) -> Tuple[Any, Optional[TreeJob]]:
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


#: ``CreateProcess`` flags (WinBase.h). The first makes the child a console
#: process group of its own, whose id is its pid; each of the others leaves it
#: no place on its parent's console (none at all, a new one, a hidden new one),
#: so a break sent on the parent's console cannot reach its group.
_CREATE_NEW_PROCESS_GROUP = 0x00000200
_LEAVES_THE_CONSOLE = (
    0x00000008      # DETACHED_PROCESS
    | 0x00000010    # CREATE_NEW_CONSOLE
    | 0x08000000    # CREATE_NO_WINDOW
)

#: The ``Popen`` objects :func:`popen_tree` started as the leader of a console
#: process group on this process's console (:func:`_note_console_group`): the
#: only targets a ``CTRL_BREAK_EVENT`` is ever sent to. Weak, so a child let go
#: of leaves the set with its object.
_CONSOLE_GROUP_LEADERS: "weakref.WeakSet[Any]" = weakref.WeakSet()


def _note_console_group(proc: Any, creationflags: Any) -> None:
    """Remember *proc* as a console group leader when *creationflags* made it
    one on this console. Never raises: a test double that cannot be weakly
    referenced is simply not remembered, and so never sent a break."""
    try:
        flags = int(creationflags or 0)
    except (TypeError, ValueError):
        return
    if not flags & _CREATE_NEW_PROCESS_GROUP or flags & _LEAVES_THE_CONSOLE:
        return
    try:
        _CONSOLE_GROUP_LEADERS.add(proc)
    except TypeError:
        pass


def _leads_console_group(child: Any, pid: int) -> bool:
    """May a ``CTRL_BREAK_EVENT`` go to *pid*? Only when it is the pid of
    *child*, a ``Popen`` :func:`popen_tree` started as a console group leader
    (:data:`_CONSOLE_GROUP_LEADERS`) and that is not yet reaped.

    ``GenerateConsoleCtrlEvent`` checks nothing: an id that is not a process
    group on the caller's console sends the event to every process attached
    to it, the caller and its host included. Held unreaped, the child keeps
    its pid from being recycled (``Popen`` holds its process handle), and the
    group it leads is the one it was created with. Only a definite yes counts.
    """
    if child is None or not pid:
        return False
    try:
        if child not in _CONSOLE_GROUP_LEADERS:
            return False
        return int(child.pid) == int(pid) and child.returncode is None
    except Exception:  # noqa: BLE001 - not a Popen this module made
        return False


def _send_ctrl_break(pid: int) -> bool:  # pragma: no cover - Windows
    """``CTRL_BREAK_EVENT`` to the console process group *pid* leads; whether
    it was sent (a process with no console of its own, a detached worker,
    cannot send one).

    Called only once :func:`_leads_console_group` said yes: any other number
    reaches every process on this console (:func:`kill_tree`)."""
    try:
        # ctypes loads only on the platform path that calls it.
        import ctypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        CTRL_BREAK_EVENT = 1
        return bool(kernel32.GenerateConsoleCtrlEvent(CTRL_BREAK_EVENT, pid))
    except Exception:
        return False


def _windows_kill_tree(
    pid: int, escalate_after_s: float, job: Optional[TreeJob] = None,
    child: Optional[Any] = None,
) -> str:  # pragma: no cover
    """Windows' kill by number: a break and its grace for a group this
    process made (:func:`_leads_console_group`), then the job, or
    ``taskkill /T`` without one. Any other target goes straight to the job:
    no break can be aimed at it, so a grace would only be a wait. So does a
    group whose break could not be sent (this process has no console)."""
    if _leads_console_group(child, pid) and _send_ctrl_break(pid) is not False:
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
        row = _parse_proc_stat(int(name), raw)
        if row is not None:
            table[row.pid] = row
    return table


def _parse_proc_stat(pid: int, raw: bytes) -> Optional[_ProcRow]:
    """*pid*'s row from the bytes of its ``/proc/<pid>/stat``."""
    # comm (field 2) is parenthesised and may itself contain ')'.
    close = raw.rfind(b")")
    fields = raw[close + 2:].split() if close != -1 else []
    if len(fields) <= 19:
        return None
    try:
        # After comm: state(3) ppid(4) pgrp(5) session(6) … starttime(22).
        return _ProcRow(
            pid=pid,
            ppid=int(fields[1]),
            pgid=int(fields[2]),
            sid=int(fields[3]),
            start_time=fields[19].decode("ascii", "replace"),
            state=fields[0].decode("ascii", "replace"),
        )
    except ValueError:
        return None


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
_SHARED_PS_TABLE_LOCK = threading.Lock()
_SHARED_PS_TABLE: List[Tuple[float, float, Dict[int, _ProcRow]]] = process_cache(
    "utils.process_control._SHARED_PS_TABLE", list, lock=_SHARED_PS_TABLE_LOCK
)


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
    ``survived``, ``skipped``, ``unresolved``), in the order the snapshot met
    them.

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

    @property
    def unresolved(self) -> List[int]:
        return [pgid for pgid, verdict in self.groups.items() if verdict == "unresolved"]

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
        if self.unresolved:
            line += (" — UNRESOLVED: " + ", ".join(str(pgid) for pgid in self.unresolved)
                     + " still running something not identified as the cli's,"
                     " left unsignalled")
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
    for verdict in ("survived", "unresolved", "killed", "skipped"):
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

    On Linux with pidfds and ``/proc`` no group is signalled by its number:
    :func:`_identity_sweep` instead.

    A snapshot whose CLI could not be verified when it was taken
    (:attr:`CliSnapshot.unverified_root`) also maps ``-pid`` to
    ``unresolved``: nothing under it was adopted, so nothing was signalled.
    """
    results = _sweep_snapshot_groups(snapshots, grace_s, poll_interval_s, clock)
    for snapshot, groups in zip(snapshots, results):
        root = getattr(snapshot, "unverified_root", None)
        if root:
            groups[-int(root)] = "unresolved"
    return results


def _sweep_snapshot_groups(
    snapshots: Sequence[Sequence[Descendant]],
    grace_s: float,
    poll_interval_s: float,
    clock: _SweepClock,
) -> List[Dict[int, str]]:
    """:func:`_sweep_snapshots`' sweep of the groups the snapshots name."""
    try:
        own: Optional[int] = os.getpgid(0)
    except (OSError, AttributeError):  # pragma: no cover - Windows; never in practice
        own = None
    api = None if IS_WINDOWS else _pidfd_api()
    if api is not None:
        return _identity_sweep(api, snapshots, grace_s, poll_interval_s, clock, own)
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


def _identity_sweep(
    api: _Pidfds,
    snapshots: Sequence[Sequence[Descendant]],
    grace_s: float,
    poll_interval_s: float,
    clock: _SweepClock,
    own: Optional[int],
) -> List[Dict[int, str]]:
    """:func:`_sweep_snapshots` by identity (:func:`_identity_run`).

    Each snapshotted group is one unit, and its snapshotted members are what
    it signals: each held by its recorded start time, through its own pidfd,
    wherever it is now (GNU ``timeout``'s ``setpgid`` and a ``setsid`` move a
    member out of the group it was snapshotted in). The group itself, and every
    group a held member is seen in, is only read afterwards: a process running
    there that the snapshot did not record gets no signal and makes the group
    ``unresolved``. None held: ``skipped`` (no signal at all) if one of the
    members' pids runs as another process, else ``gone``, as the kill by number
    rules, unless the read finds something. A key that is this process's own
    group, or no group, is never read, as the kill by number signals only the
    members there.
    """
    me = os.getpid()
    plans: List[List[Tuple[int, _IdentityUnit]]] = []
    units: List[_IdentityUnit] = []
    recorded: Set[Tuple[int, str]] = set()
    try:
        table = _linux_process_table()
        for snapshot in snapshots:
            by_group: Dict[int, List[Descendant]] = {}
            for entry in snapshot or ():
                key = entry.pgid if entry.pgid is not None else -entry.pid
                by_group.setdefault(key, []).append(entry)
            plan: List[Tuple[int, _IdentityUnit]] = []
            for key, members in by_group.items():
                unit = _IdentityUnit(own)
                units.append(unit)
                plan.append((key, unit))
                try:
                    unit.watch(key)
                    for member in members:
                        if not member.start_time:
                            unit.reused = unit.reused or _table_pid_running(table, member.pid)
                            continue
                        recorded.add((int(member.pid), str(member.start_time)))
                        outcome = _hold_process(api, member.pid, member.start_time,
                                                unit.held, me)
                        if outcome == "held":
                            unit.saw(unit.held[-1].pgid)
                        elif outcome == "unread":
                            unit.unknown = True
                        elif _table_pid_running(table, member.pid):
                            unit.reused = True
                except Exception:  # noqa: BLE001 - one group must not stop the sweep
                    unit.verdict = "unresolved"
            plans.append(plan)
        live = [unit for unit in units if unit.verdict is None]
        if live:
            try:
                _identity_run(api, live, grace_s, clock, poll_interval_s, recorded)
            except Exception:  # noqa: BLE001 - a teardown never raises; unknown is unresolved
                for unit in live:
                    if unit.verdict is None:
                        unit.verdict = "unresolved"
    finally:
        for unit in units:
            unit.close(api)
    return [{key: str(unit.verdict) for key, unit in plan} for plan in plans]


def _table_pid_running(table: Optional[Dict[int, _ProcRow]], pid: int) -> bool:
    """*pid* runs (not a zombie), whoever it is, in *table* or read alone."""
    if table is None:
        return _running(pid)
    row = table.get(pid)
    return row is not None and row.state != "Z"


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


class CliSnapshot(list):
    """:meth:`LiveCliRegistry.snapshot_for`'s answer: the descendants, and in
    :attr:`unverified_root` the CLI's pid when its fresh walk was refused (its
    row was not the process registered), ``None`` otherwise. A sweep reports
    such a snapshot ``unresolved`` under that pid's key, ``-pid``, the key of
    a member with no group (:func:`_sweep_snapshots`): what runs below it now
    was not identified as the CLI's, and nothing was sent to it."""

    def __init__(self, entries: Sequence[Descendant] = (), *,
                 unverified_root: Optional[int] = None) -> None:
        super().__init__(entries)
        self.unverified_root = unverified_root


def _verified_root(table: Dict[int, "_ProcRow"], pid: int,
                   registered: Optional[str]) -> bool:
    """Is *pid*'s row in *table* the process registered with start time
    *registered*? ``False`` with no such row, no start time on either side,
    or another one."""
    row = table.get(pid) if table else None
    return (row is not None and bool(registered) and bool(row.start_time)
            and str(row.start_time) == str(registered))


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
        # Worked out here, not first inside the abort's signal handler that
        # sweeps: off Python's own calls it imports ctypes.
        if not IS_WINDOWS:
            _pidfd_api()
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
        """Re-snapshot every entry from one scan. Identity-checked per entry:
        only under a root whose row in that scan has the start time it was
        registered with (:func:`_verified_root`)."""
        entries = self.entries()
        if not entries:
            return
        table = _process_table()
        for entry in entries:
            if not _verified_root(table, entry.pid, entry.start_time):
                # Gone (keep the last snapshot it had), someone else's pid
                # now, or not dated: nothing is adopted under it.
                continue
            if table[entry.pid].state == "Z":
                # Exited, not yet reaped: its children are another parent's
                # now, so a walk finds none, and the snapshot taken while it
                # ran is what still names them for the sweep.
                continue
            fresh = _descendants_in(table, entry.pid)
            with self._lock:
                if id(entry.proc) in self._entries:
                    entry.snapshot = fresh

    def snapshot_for(self, proc: Any) -> "CliSnapshot":
        """The last refreshed snapshot of *proc*'s tree, merged with a fresh one.

        The fresh walk runs only while *proc* is un-reaped (``returncode`` still
        ``None``), and only under a root verified in the walk's own scan: its
        row has the start time *proc* was registered with
        (:func:`_verified_root`). ``returncode`` alone proves nothing where the
        kernel reaps children itself (SIGCHLD ignored), and the pid may then
        name another process, whose children are not the CLI's. A root that
        cannot be verified (another start time, no row, none registered)
        adopts nothing, and the snapshot says so
        (:attr:`CliSnapshot.unverified_root`), which its sweep reports
        ``unresolved``. Once *proc* is reaped only the stored snapshot, taken
        under a verified root and protected by its start times, is used.
        """
        with self._lock:
            entry = self._entries.get(id(proc))
            stored = list(entry.snapshot) if entry else []
            registered = entry.start_time if entry else None
        fresh: List[Descendant] = []
        unverified: Optional[int] = None
        pid = getattr(proc, "pid", None)
        if (getattr(proc, "returncode", 0) is None and not IS_WINDOWS
                and isinstance(pid, int) and pid > 0):
            table = _process_table()
            if _verified_root(table, pid, registered):
                fresh = _descendants_in(table, pid)
            else:
                unverified = pid
        return CliSnapshot(_merge_snapshots(fresh, stored), unverified_root=unverified)

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

#: The run whose record :func:`popen_tree` writes, once
#: :func:`record_cli_identities` has named one: ``(phase_dir, run_id)``.
_CLI_RECORD: List[Tuple[str, str]] = []

#: The run in :data:`_CLI_RECORD` whose launches this process refuses for the
#: rest of its life (:func:`refuse_launches`): its worker's teardown began.
_LAUNCHES_REFUSED: List[str] = []

#: The run in :data:`_CLI_RECORD` whose phase dir could not be held as its
#: own (:class:`_PhaseDirNotHeld`): its launches start unrecorded, for the
#: rest of the run, after one warning (:func:`_record_launch`).
_RECORD_UNHELD: List[str] = []

#: Each launch's token in the record: this process's pid and a count.
_LAUNCH_COUNT = itertools.count(1)

#: How long a launch or an abort waits for a record's lock, which is held for
#: one read and one append.
_RECORD_LOCK_TIMEOUT_S = DEFAULT_MUTEX_TIMEOUT_S


class CliRecord(NamedTuple):
    """What :func:`read_cli_record` found: every process recorded by pid,
    start time and group (as :class:`Descendant` entries, no session), and
    whether the record is *complete*: every launch it announced has its
    process's identity or its failure, and every line is whole."""

    members: List[Descendant]
    complete: bool
    #: Lines naming another run: never members; the caller reports them.
    foreign: int = 0
    #: An abort closed the run's launch gate (:func:`close_launch_gate`).
    closed: bool = False


class LaunchRefused(OSError):
    """:func:`popen_tree` refused a launch before starting anything: its run's
    launch gate is closed (an abort is under way), or its run's record could
    not take the launch's line."""


class _PhaseDirNotHeld(OSError):
    """:func:`_open_record` could not hold the phase dir as the run's own: a
    link, not a directory, or another user's. Every reader then reads the
    record as incomplete; a launch starts unrecorded (:func:`_record_launch`)."""


def cli_record_name(run_id: str) -> str:
    """The name of run *run_id*'s record of the processes its worker starts,
    in its phase dir."""
    return f"orchestrator-run.{run_id}.clis"


def record_cli_identities(phase_dir: Optional[str], run_id: Optional[str] = None) -> None:
    """From now on, record every process :func:`popen_tree` starts in run
    *run_id*'s record in *phase_dir* (``None``: stop recording). Only where
    the identity kill runs (:func:`signals_by_identity`), the one kill that
    reads it: everywhere else a spawn stays exactly what it was, and Windows
    ends the run's job instead.

    The detached worker names its run, so a close-out after the worker died
    without its handler still knows the provider CLIs it started, Lane A's and
    the executor's alike, by pid, start time and group (:func:`read_cli_record`,
    then :func:`kill_tree`'s *members*; docs/development/runtime.md, "A target
    known only by number").

    A launch is written twice: an intent before the spawn, and the process's
    identity (or the spawn's failure) after it. The intent goes first because a
    process cannot be recorded before it exists: a worker that dies between the
    spawn and the second line leaves an intent with no identity, and the record
    reads as incomplete rather than as a run that started nothing. The intent
    is written under the record's lock, after reading that no abort closed the
    run's launch gate (:func:`close_launch_gate`): an intent that cannot be
    written, or a closed gate, stops the launch (:class:`LaunchRefused`), so
    nothing is started that the record would not know about. A short write is
    ended by a newline, leaving a torn line that reads as incomplete.

    Every line carries the run id, and the record is reached only through
    :func:`_open_record`, so a record is its run's alone: a link to another
    run's file, or another run's line, is never read as this run's.

    The identity line is written only for a process verified as this one's
    child (:func:`_record_spawned`); one that is not is written as
    unverified, which leaves the record incomplete and names nothing to
    signal.
    """
    _LAUNCHES_REFUSED[:] = []
    _RECORD_UNHELD[:] = []
    _CLI_RECORD[:] = (
        [(str(phase_dir), str(run_id))]
        if phase_dir and run_id and signals_by_identity() else [])


def refuse_launches(run_id: Any) -> None:
    """From now until this process exits, :func:`popen_tree` refuses every
    launch of run *run_id* (:class:`LaunchRefused`, nothing started), when it
    is the run this process records for: its worker's teardown has begun
    (``RunHandle.finish``, its signal handler). The record stays named, so a
    launch whose intent got in before this still writes its identity there,
    for the abort's second read; nothing else may start once the worker is
    ending. A later :func:`record_cli_identities` names a new run."""
    if _CLI_RECORD and _CLI_RECORD[0][1] == str(run_id):
        _LAUNCHES_REFUSED[:] = [str(run_id)]


def _record_name(run_id: Any) -> str:
    """:func:`cli_record_name`, for a run id that is one plain file name."""
    text = str(run_id or "")
    if (not text or text.startswith(".") or "/" in text or "\\" in text
            or "\0" in text):
        raise OSError(errno.EINVAL, f"not a run id a record can be named by: {text!r}")
    return cli_record_name(text)


def _records_bound_here() -> bool:
    """Can a record be opened relative to its dir without following a link?"""
    return (not IS_WINDOWS and bool(getattr(os, "O_NOFOLLOW", 0))
            and bool(getattr(os, "O_DIRECTORY", 0)) and os.open in os.supports_dir_fd)


def _open_record(phase_dir: str, run_id: Any, *, write: bool, create: bool = True) -> int:
    """A descriptor on run *run_id*'s record in *phase_dir*, bound to that run.

    The phase dir is opened without following a link and must be a directory
    this user owns; the record is opened relative to that descriptor, without
    following a link (for *write* append-only, and created when *create*), and
    must be a regular file this user owns with exactly one link: a symlink or a
    hard link to another run's record is refused, so is a file another user
    planted. Both opens are non-blocking, so a FIFO or a device in the
    record's place is refused by the check that follows rather than waited on;
    the record's descriptor is made blocking again once it passed. ``OSError``
    otherwise (``FileNotFoundError`` for no dir or no record,
    :class:`_PhaseDirNotHeld` for a phase dir that cannot be held)."""
    name = _record_name(run_id)
    if not _records_bound_here():
        raise OSError(errno.ENOTSUP, "a record cannot be opened without following links here")
    cloexec = getattr(os, "O_CLOEXEC", 0)
    nonblock = getattr(os, "O_NONBLOCK", 0)
    try:
        dir_fd = os.open(os.path.abspath(str(phase_dir)),
                         os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | nonblock | cloexec)
    except OSError as exc:
        if exc.errno in (errno.ELOOP, errno.ENOTDIR):
            raise _PhaseDirNotHeld(
                exc.errno, f"{phase_dir} is a link or not a directory") from None
        raise
    try:
        info = os.fstat(dir_fd)
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid():
            raise _PhaseDirNotHeld(errno.EPERM, f"{phase_dir} is not a directory this user owns")
        flags = os.O_RDONLY
        if write:
            flags = os.O_RDWR | os.O_APPEND | (os.O_CREAT if create else 0)
        fd = os.open(name, flags | os.O_NOFOLLOW | nonblock | cloexec, 0o600,
                     dir_fd=dir_fd)
    finally:
        os.close(dir_fd)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                or info.st_uid != os.geteuid()):
            raise OSError(errno.EPERM, f"{name} in {phase_dir} is not a regular file "
                                       "of this user's with one link")
        if nonblock:
            os.set_blocking(fd, True)
    except BaseException:
        os.close(fd)
        raise
    return fd


@contextmanager
def _locked_record(phase_dir: str, run_id: Any, *, create: bool = True) -> Iterator[int]:
    """Run *run_id*'s record (:func:`_open_record`, for writing) under its
    exclusive lock: what a launch's check-then-intent and an abort's
    gate-then-read each hold, so neither lands inside the other."""
    fd = _open_record(phase_dir, run_id, write=True, create=create)
    try:
        if not wait_for_fd_lock(fd, timeout_s=_RECORD_LOCK_TIMEOUT_S):
            raise OSError(errno.EAGAIN, f"the record of run {run_id} stayed locked")
        try:
            yield fd
        finally:
            release_fd_lock(fd)
    finally:
        os.close(fd)


def _read_fd(fd: int) -> bytes:
    chunks: List[bytes] = []
    offset = 0
    while True:
        chunk = os.pread(fd, 1 << 16, offset)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)
        offset += len(chunk)


def _write_line(fd: int, line: Dict[str, Any]) -> bool:
    """One line through *fd*; ``False`` when it was not written whole (a short
    write is ended by a newline, so only that line is torn)."""
    data = (json.dumps(line, separators=(",", ":")) + "\n").encode("utf-8")
    written = os.write(fd, data)
    if written != len(data):
        os.write(fd, b"\n")
        return False
    return True


def _append_record(line: Dict[str, Any]) -> bool:
    """One line, with the recording run's id, into its record under the
    record's lock; ``False`` when it was not written whole. It answers an
    intent, so it never creates the record: one gone since was retired by a
    teardown that no longer reads it."""
    if not _CLI_RECORD:
        return False
    phase_dir, run_id = _CLI_RECORD[0]
    try:
        with _locked_record(phase_dir, run_id, create=False) as fd:
            return _write_line(fd, dict(line, run=run_id))
    except OSError:
        return False


def _record_launch() -> Optional[str]:
    """The intent line before a spawn, written only while the run's launch
    gate is open; its token, ``None`` when nothing is recorded. Raises
    :class:`LaunchRefused` when the gate is closed, when this process's
    worker is ending (:func:`refuse_launches`), or when the line cannot be
    written: nothing may be started then.

    A phase dir that cannot be held as the run's own (a symlink, not a
    directory, another user's: root in a container working in a phase dir an
    earlier host run made) is no reason to refuse: what the record serves is
    a later kill's proof, never the CLI's containment. One warning, and from
    then on the run's launches start unrecorded. Every reader opens the record
    under the same rule, so it reads incomplete, and a later abort or
    close-out says it could not confirm the cleanup instead of calling it done
    (docs/development/runtime.md, "What a detached worker records")."""
    if not _CLI_RECORD:
        return None
    phase_dir, run_id = _CLI_RECORD[0]
    if _LAUNCHES_REFUSED:
        raise LaunchRefused(
            errno.ECANCELED,
            f"run {run_id} is ending (its worker's teardown has begun), so nothing "
            "was started")
    if _RECORD_UNHELD:
        return None
    token = f"{os.getpid()}.{next(_LAUNCH_COUNT)}"
    try:
        with _locked_record(phase_dir, run_id) as fd:
            if _parse_record(_read_fd(fd), run_id).closed:
                raise LaunchRefused(
                    errno.ECANCELED,
                    f"run {run_id} is being aborted (its launch gate is closed), so "
                    "nothing was started")
            if _write_line(fd, {"run": run_id, "launch": token}):
                return token
            reason = "a short write"
    except LaunchRefused:
        raise
    except _PhaseDirNotHeld as exc:
        _RECORD_UNHELD[:] = [run_id]
        print(
            f"WARNING: run {run_id}'s phase dir cannot hold its record of the processes "
            f"it starts ({exc.strerror}); starting them unrecorded. A later abort or "
            "close-out cannot confirm they stopped and will say so: check by hand "
            "after one.",
            file=sys.stderr, flush=True,
        )
        return None
    except OSError as exc:
        reason = str(exc)
    raise LaunchRefused(
        errno.EIO,
        f"the run's record of the processes it starts "
        f"({os.path.join(phase_dir, cli_record_name(run_id))}) could not be written "
        f"({reason}), so nothing was started",
    )


def _record_spawned(token: Optional[str], proc: Any) -> None:
    """The started process's identity, for the intent *token*: its start time
    and group from one ``/proc`` row, kept only while that row shows the
    process is still this one's child. ``popen_tree`` returns before anything
    waits on it, so its pid can have been handed out again only if it was
    reaped behind its ``Popen`` (SIGCHLD ignored, ``SA_NOCLDWAIT``), and a
    process that took it then is another parent's. A row that is not this
    process's child, or that cannot be read, is written as unverified: the
    intent stays unanswered, the record incomplete, and nothing is signalled
    by it (the detached worker's start time is read under the same rule,
    :func:`_note_worker_start`). Never raises: a line not written leaves the
    intent unanswered too."""
    if token is None:
        return
    try:
        pid = int(proc.pid)
        _answered, row = _linux_row(pid)
        if row is None or row.ppid != os.getpid() or not row.start_time:
            _append_record({"cli": token, "pid": pid, "start": None, "unverified": True})
            return
        _append_record({"cli": token, "pid": pid, "start": str(row.start_time),
                        "pgid": row.pgid})
    except Exception:  # noqa: BLE001 - the record stays incomplete
        pass


def _record_failed(token: Optional[str]) -> None:
    if token is not None:
        try:
            _append_record({"failed": token})
        except Exception:  # noqa: BLE001 - the record stays incomplete
            pass


def close_launch_gate(phase_dir: str, run_id: str) -> Optional[CliRecord]:
    """Close run *run_id*'s launch gate, before an abort stops its worker:
    a ``gate: closed`` line in its record, written under the record's lock,
    after which :func:`popen_tree` in that worker refuses every launch
    (:class:`LaunchRefused`, nothing started). Returns the record as it reads
    under that same lock: every launch whose intent got in first is there,
    with or without its identity yet. ``complete`` is false when the gate
    could not be closed (the record cannot be opened as the run's own, its
    lock was not had, the line was not written whole): a launch may then still
    slip past. A phase dir that no longer exists reads as closed with nothing
    recorded: no launch can write its intent there either. ``None`` where
    nothing is recorded (off the identity kill, :func:`signals_by_identity`),
    the kill by number's ground as before."""
    if not signals_by_identity():
        return None
    try:
        with _locked_record(phase_dir, run_id) as fd:
            closed = _write_line(fd, {"run": str(run_id), "gate": "closed"})
            record = _parse_record(_read_fd(fd), str(run_id))
    except FileNotFoundError:
        if _no_phase_dir(phase_dir):
            return CliRecord([], True, 0, True)
        return read_cli_record(phase_dir, run_id)._replace(complete=False)
    except OSError:
        return read_cli_record(phase_dir, run_id)._replace(complete=False)
    return record if closed else record._replace(complete=False)


def _no_phase_dir(phase_dir: str) -> bool:
    """Is there nothing at all at *phase_dir* (not even a dangling link)?"""
    return not os.path.lexists(os.path.abspath(str(phase_dir)))


def read_cli_record(phase_dir: str, run_id: Any) -> CliRecord:
    """The processes :func:`record_cli_identities` recorded for run *run_id*
    in *phase_dir*, in order, read through :func:`_open_record`. No record:
    nothing recorded, complete (and closed when there is no phase dir either:
    no launch can be recorded there). A record that cannot be opened as the run's
    own (a link, another user's, not a regular file), cannot be read, a line
    that is not whole or names no run, or an intent with neither an identity
    nor a failure: incomplete (a process may have been started that the
    record does not name). Lines of another run are counted in ``foreign``
    and otherwise ignored."""
    try:
        name = _record_name(run_id)
    except OSError:
        return CliRecord([], False)
    if not _records_bound_here():
        # Nothing records here (Windows; no O_NOFOLLOW): a file there is
        # one this kill cannot vouch for.
        return CliRecord([], not os.path.lexists(os.path.join(str(phase_dir), name)))
    try:
        fd = _open_record(phase_dir, run_id, write=False)
    except FileNotFoundError:
        # No record: nothing was started. No phase dir either: nothing can
        # be (no intent can be written there), which is a closed gate.
        return CliRecord([], True, 0, _no_phase_dir(phase_dir))
    except OSError:
        return CliRecord([], False)
    try:
        raw = _read_fd(fd)
    except OSError:
        return CliRecord([], False)
    finally:
        os.close(fd)
    return _parse_record(raw, str(run_id))


def _parse_record(raw: bytes, run_id: str) -> CliRecord:
    """:func:`read_cli_record`'s reading of a record's bytes."""
    complete = not raw or raw.endswith(b"\n")
    launched: Set[str] = set()
    answered: Set[str] = set()
    identified: Set[str] = set()
    found: List[Descendant] = []
    foreign = 0
    closed = False
    for text in raw.split(b"\n"):
        if not text.strip():
            continue
        try:
            line = json.loads(text.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            complete = False
            continue
        if not isinstance(line, dict) or not isinstance(line.get("run"), str):
            complete = False
            continue
        if line["run"] != run_id:
            foreign += 1
            continue
        if "gate" in line:
            if line["gate"] == "closed":
                closed = True
            else:
                complete = False
        elif isinstance(line.get("launch"), str):
            launched.add(line["launch"])
        elif isinstance(line.get("failed"), str):
            answered.add(line["failed"])
        elif isinstance(line.get("cli"), str):
            pid, start, pgid = line.get("pid"), line.get("start"), line.get("pgid")
            if not isinstance(pid, int) or pid <= 0 or not isinstance(start, str) or not start:
                complete = False
                continue
            if line["cli"] not in launched or line["cli"] in identified:
                # An identity answers its own intent, written before it, once:
                # any other names nothing, and the record cannot vouch for
                # itself any more (docs/development/runtime.md, "What a
                # detached worker records").
                complete = False
                continue
            identified.add(line["cli"])
            answered.add(line["cli"])
            found.append(Descendant(pid, pgid if isinstance(pgid, int) else None, None, start))
        else:
            complete = False
    if launched - answered:
        complete = False
    return CliRecord(found, complete, foreign, closed)


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
    keep_fds: Sequence[int] = (),
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

    *keep_fds* (POSIX): descriptors the worker inherits at the same numbers,
    past the sweep that closes everything else (the phase lock a launcher
    hands its worker, ``detach.launch``). A replaced ``spawn_detached`` starts
    no process and is handed none.
    """
    spawn = spawn_detached
    if keep_fds and not IS_WINDOWS and spawn is _REAL_SPAWN_DETACHED:
        return _spawn_detached_posix(
            [str(a) for a in argv], cwd=cwd, env=env, log_path=log_path,
            keep_fds=keep_fds,
        ), None
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


def _close_inherited_fds(keep: Sequence[int] = ()) -> None:
    """Close every descriptor above stdio but *keep*. Call in a forked child,
    pre-``exec``.

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
            if fd < 3 or fd in keep:
                continue
            try:
                os.close(fd)
            except OSError:
                pass
        return
    low = 3  # pragma: no cover - no fd directory
    for fd in sorted(f for f in keep if f >= 3):  # pragma: no cover
        os.closerange(low, fd)
        low = fd + 1
    os.closerange(low, _fd_sweep_limit())  # pragma: no cover


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
    argv: List[str], *, cwd: str, env: Dict[str, str], log_path: Optional[str],
    keep_fds: Sequence[int] = (),
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
                # pipe waiting on an EOF that never comes. *keep_fds* stay,
                # inheritable across the exec for this one child only.
                _close_inherited_fds(keep_fds)
                for kept in keep_fds:
                    os.set_inheritable(kept, True)
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
    # Before the intermediate is reaped: its pid, held by its zombie, is what
    # proves the row read is the worker's (`_note_worker_start`).
    _note_worker_start(raw, intermediate)
    try:
        os.waitpid(intermediate, 0)
    except OSError:
        pass
    try:
        return int(raw.decode("ascii").strip())
    except (UnicodeDecodeError, ValueError) as exc:
        raise SpawnFailed(
            "the detach intermediate did not report a worker pid"
        ) from exc


#: The last detached worker's ``{pid: start time}``, read the moment its pid
#: was known (:func:`detached_worker_start_time`).
_DETACHED_START: Dict[int, str] = {}


def _note_worker_start(raw: bytes, intermediate: int) -> None:
    """Record the start time of the worker whose pid *raw* carries, read while
    *intermediate* (the spawn that made its session and forked it) is still
    this process's unreaped child. Its pid is then held by it, so no other
    session can have that number: a row whose session is *intermediate* is
    the worker's, or a process the worker started that took its pid after
    it. Only where the identity kill runs (:func:`signals_by_identity`), and
    only under U74's anchor; anything else records nothing. Never raises."""
    _DETACHED_START.clear()
    try:
        pid = int(raw.decode("ascii").strip())
        if not signals_by_identity() or _owned_anchor(intermediate) is not True:
            return
        _answered, row = _linux_row(pid)
        if (row is None or row.sid != intermediate or not row.start_time
                or _owned_anchor(intermediate) is not True):
            return
        _DETACHED_START[pid] = str(row.start_time)
    except Exception:  # noqa: BLE001 - a spawn never fails for its record
        _DETACHED_START.clear()


def detached_worker_start_time(pid: int) -> Optional[str]:
    """The start time of the detached worker *pid* that :func:`spawn_detached`
    started last, read the moment its pid was known; ``None`` when it could
    not be proved the worker's (and everywhere the identity kill does not
    run). What the launcher's teardown of a failed handshake kills it by:
    without it, on Linux with pidfds, it is not signalled at all."""
    return _DETACHED_START.get(int(pid)) if pid else None


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

    POSIX: SIGCHLD goes back to its default if it was inherited ignored
    (:func:`restore_sigchld_default`), as at every process entry.
    """
    redirect_output_to_log(log_path)
    if IS_WINDOWS:  # pragma: no cover - Windows
        if run_id is not None:
            # First, so a job the worker creates itself holds the reaper's.
            _hold_run_job(run_id)
        _assign_own_job_object()
    # Imported here to keep resume_state, which loads this module, light.
    from .stream_bootstrap import bootstrap_streams

    bootstrap_streams()
    restore_sigchld_default()


def _assign_own_job_object() -> None:  # pragma: no cover - Windows
    """Best-effort Job Object with KILL_ON_JOB_CLOSE around this process."""
    try:
        # ctypes loads only on the platform path that calls it.
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
