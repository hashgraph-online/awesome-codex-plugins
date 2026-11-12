"""Private config roots that adapters hand a provider CLI, one per spawn.

An adapter whose CLI writes state under the user's home (sessions, caches,
logs) points the CLI at a directory made here instead, so a fan-out never
writes into the user's own CLI state and two concurrent slots never share one
writable root (docs/development/providers.md#private-config-roots). Each
directory is:

* private: ``0700``, as ``mkdtemp`` makes it, asserted with ``chmod``;
* named after its owner: ``<prefix><pid>-<start>-<pidns>-<random>`` under
  ``TMPDIR``, the creating process's pid, start time (with where it was read)
  and PID namespace, so a root whose owner died without cleaning up can be told
  apart from a live process's;
* owned: tracked by the process that created it, and removed by that process
  only: when the dispatch that created it ends with every child it started
  confirmed stopped (:func:`dispatch_homes`, which both spawn sites enter),
  else at :meth:`PrivateHomes.cleanup` or at exit. A root the user pinned
  through the adapter's variable is never created here, so never removed; a
  forked child forgets the directories its parent created instead of removing
  them;
* swept when orphaned: the first root an adapter creates in a process removes
  that adapter's roots whose owner is dead, judged by pid and start time
  together and only within a PID namespace known to be this process's. An
  owner that is alive, that cannot be identified, or whose namespace is
  another or unknown keeps its roots, and so does a root named before owners
  were recorded.

This module writes nothing into a root; what lands there is the CLI's own
state, removed with the root.
"""

from __future__ import annotations

import atexit
import contextlib
import contextvars
import os
import re
import shutil
import stat
import sys
import tempfile
import threading
from typing import Iterator, List, Optional, Tuple

from .. import process_control


def _token(value: object, default: str) -> str:
    """*value* as one name-safe field: no ``-``, which separates the fields."""
    text = re.sub(r"[^A-Za-z0-9_.]", "_", str(value)) if value else ""
    return text or default


#: The name field of an owner whose start time or PID namespace is unknown.
_UNKNOWN = "unknown"

#: The PID namespace field where the platform has none: every process shares
#: one pid space. Only off Linux; there a missing namespace is :data:`_UNKNOWN`.
_NO_NAMESPACES = "na"

#: Every Linux process has a PID namespace, so one that cannot be read there is
#: unknown, never :data:`_NO_NAMESPACES`.
_PID_NAMESPACES = sys.platform.startswith("linux")


def _namespace_token(namespace: Optional[str]) -> str:
    """``pid:[4026531836]`` as ``4026531836``. Without one, :data:`_UNKNOWN`
    on Linux, where this one could not be read, and :data:`_NO_NAMESPACES`
    elsewhere."""
    match = re.search(r"\[(\d+)\]", namespace or "")
    if match:
        return match.group(1)
    return _UNKNOWN if _PID_NAMESPACES else _NO_NAMESPACES


def _start_token(reading: Optional[Tuple[str, str]]) -> str:
    """A :func:`process_control.sourced_start_time` reading as one name field,
    ``<source>.<start>`` (``proc.8812345``); :data:`_UNKNOWN` without one."""
    if reading is None:
        return _UNKNOWN
    source, value = reading
    return f"{source}.{_token(value, _UNKNOWN)}"


def _owner_fields() -> str:
    """This process's ``<pid>-<start>-<pidns>`` name fields."""
    pid = os.getpid()
    return "-".join((
        str(pid),
        _start_token(process_control.sourced_start_time(pid)),
        _namespace_token(process_control.pid_namespace()),
    ))


def _owner_verdict(pid: int, start: str, namespace: str) -> str:
    """``alive`` / ``dead`` / ``unknown`` for a root's recorded owner.

    :func:`process_control.probe`'s rule, through the name's tokens, and only
    once both PID namespaces are known and the same: a pid that is gone, or
    live under another start time read from the same source (reused), is
    ``dead``. A namespace unknown on either side, or another one, makes the pid
    mean nothing here; a live pid whose start time cannot be read, was read
    from another source, or was not recorded is ``unknown``.
    """
    here = _namespace_token(process_control.pid_namespace())
    if _UNKNOWN in (namespace, here) or namespace != here:
        return process_control.UNKNOWN
    liveness = process_control.process_liveness(pid)
    if liveness != process_control.ALIVE:
        return liveness  # dead only when the platform says the pid is gone
    source, dot, _ = start.partition(".")
    if not dot:
        return process_control.UNKNOWN
    observed = process_control.sourced_start_time(pid)
    if observed is None or observed[0] != source:
        return process_control.UNKNOWN
    if _start_token(observed) == start:
        return process_control.ALIVE
    # Only a clock-independent reading tells a reused pid apart: the kernel's ticks
    # and Windows' FILETIME are; `ps`'s text follows the reader's time zone and
    # locale, so a mismatch there proves nothing.
    exact = (process_control.START_SOURCE_PROC, process_control.START_SOURCE_WINDOWS)
    return process_control.DEAD if source in exact else process_control.UNKNOWN


class _DispatchScope:
    """The roots created inside one :func:`dispatch_homes` block."""

    __slots__ = ("pid", "created", "closed")

    def __init__(self) -> None:
        self.pid = os.getpid()
        self.created: List[Tuple["PrivateHomes", str]] = []
        self.closed = False


_SCOPE: "contextvars.ContextVar[Optional[_DispatchScope]]" = contextvars.ContextVar(
    "private_home_dispatch_scope", default=None
)


@contextlib.contextmanager
def dispatch_homes() -> Iterator[None]:
    """Remove every root created inside this block when it exits, once every
    child the block started is confirmed stopped.

    Both spawn sites enter it around one dispatch
    (``llm_client.provider_dispatch_context``), so a slot's home lives as long
    as the dispatch that made it and the CLI it lent the home to. The block
    holds a :func:`process_control.child_ledger`: the CLI ends there when it
    was seen to exit, or when its spawner confirmed the stop of the CLI and
    every process group it reached (``process_control.unconfirmed_kill``'s
    rule). Anything else, a stop that left a process running or could not be
    confirmed, keeps the roots, private and tracked, for
    :meth:`PrivateHomes.cleanup` at exit or, after a crash, the sweep of a dead
    owner's roots. Roots are attributed through a context variable, so
    concurrent slots on other threads never release each other's. A root that
    cannot be removed stays tracked the same way.
    """
    scope = _DispatchScope()
    token = _SCOPE.set(scope)
    children: Optional[process_control.ChildLedger] = None
    try:
        with process_control.child_ledger() as children:
            yield
    finally:
        scope.closed = True
        try:
            _SCOPE.reset(token)
        except ValueError:  # left in another context: the closed scope takes no more
            pass
        if children is not None and children.all_ended():
            for homes, path in reversed(scope.created):
                homes.release(path)


class PrivateHomes:
    """The private config roots one adapter creates, one per :meth:`create`.

    The adapter keeps one instance at module level and exposes its methods
    under the module names callers use (``isolated_home_dirs``,
    ``cleanup_home_dirs``, ``reset_home_dirs``).
    """

    def __init__(self, prefix: str) -> None:
        self.prefix = prefix
        self._lock = threading.Lock()
        self._dirs: List[str] = []
        self._pid = os.getpid()
        self._atexit_registered = False
        self._swept_pid: Optional[int] = None
        #: A root this adapter names: owner pid, start time, namespace, random.
        self._name = re.compile(
            rf"^{re.escape(prefix)}(\d+)-([A-Za-z0-9_.]+)-([A-Za-z0-9_.]+)-[A-Za-z0-9_]+$"
        )

    def _owned(self) -> List[str]:
        """The tracked directories, called with the lock held. A forked child
        starts with an empty list: its parent's directories are not its own."""
        if self._pid != os.getpid():
            self._dirs, self._pid = [], os.getpid()
        return self._dirs

    def create(self) -> str:
        """A fresh 0700 config root, owned and tracked by this process.

        Raises ``OSError`` when it cannot be made; the adapter then runs the
        slot without one, since containment must never fail a run. The
        ``atexit`` sweep is registered at the first creation, and the first
        creation in a process sweeps dead owners' roots first. Inside
        :func:`dispatch_homes` the root is also handed to that dispatch.
        """
        with self._lock:
            sweep = self._swept_pid != os.getpid()
            self._swept_pid = os.getpid()
        if sweep:
            self.sweep_orphans()
        with self._lock:
            path = tempfile.mkdtemp(prefix=f"{self.prefix}{_owner_fields()}-")
            try:
                os.chmod(path, 0o700)  # mkdtemp already does this; asserted, not assumed
            except BaseException:
                shutil.rmtree(path, ignore_errors=True)
                raise
            self._owned().append(path)
            if not self._atexit_registered:
                atexit.register(self.cleanup)
                self._atexit_registered = True
        scope = _SCOPE.get()
        if scope is not None and not scope.closed and scope.pid == os.getpid():
            scope.created.append((self, path))
        return path

    def isolated_home_dirs(self) -> Tuple[str, ...]:
        """Every config root this process created and has not yet removed."""
        with self._lock:
            return tuple(self._owned())

    def release(self, path: str) -> None:
        """Remove one root this process created, now. Never raises.

        A path this process does not track is left alone. One that cannot be
        removed stays tracked, so :meth:`cleanup` tries again at exit.
        """
        with self._lock:
            owned = self._owned()
            if path not in owned:
                return
            owned.remove(path)
        shutil.rmtree(path, ignore_errors=True)
        if os.path.lexists(path):
            with self._lock:
                self._owned().append(path)

    def cleanup(self) -> None:
        """Remove every config root this process created. Never raises.

        Containment must never be the thing that fails a run, and this runs
        from ``atexit``, so a directory that cannot be removed is left behind
        under its known prefix rather than raising.
        """
        with self._lock:
            paths = list(self._owned())
            self._dirs = []
        for path in paths:
            shutil.rmtree(path, ignore_errors=True)

    def sweep_orphans(self, base: Optional[str] = None) -> List[str]:
        """Remove this adapter's roots under *base* whose owner is dead.

        A root goes only when its name records an owner, it is a real
        directory (not a symlink) this user owns, and the owner probes ``dead``
        (:func:`_owner_verdict`). There is no age threshold. Never raises;
        returns the removed paths.
        """
        base = base or tempfile.gettempdir()
        removed: List[str] = []
        try:
            names = os.listdir(base)
        except OSError:
            return removed
        uid = os.getuid() if hasattr(os, "getuid") else None
        for name in names:
            match = self._name.match(name)
            if not match:
                continue
            path = os.path.join(base, name)
            try:
                info = os.lstat(path)
            except OSError:
                continue
            if not stat.S_ISDIR(info.st_mode):
                continue
            if uid is not None and info.st_uid != uid:
                continue
            try:
                verdict = _owner_verdict(int(match.group(1)), match.group(2), match.group(3))
            except Exception:  # noqa: BLE001 - an unreadable owner keeps its root
                continue
            if verdict != process_control.DEAD:
                continue
            shutil.rmtree(path, ignore_errors=True)
            if not os.path.lexists(path):
                removed.append(path)
        return removed

    def reset(self) -> None:
        """Forget the tracked roots without removing anything (tests)."""
        with self._lock:
            self._dirs = []
