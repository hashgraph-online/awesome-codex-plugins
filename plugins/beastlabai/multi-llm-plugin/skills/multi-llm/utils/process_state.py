"""The process's module-level caches, held in one registry.

A module that memoises across calls declares its container through
:func:`process_cache` instead of as a bare literal::

    _VERSION_CACHE: Dict[str, str] = process_cache("utils.probe_state._VERSION_CACHE")

Caching per process is deliberate. One interpreter runs several dispatch
targets in turn, and a later one reuses what an earlier one measured: the
sandbox probe, for one, runs once per process (docs/development/status.md). So
nothing on a run path calls :func:`reset_all`. It exists for tests:
``tests/conftest.py`` calls it around every test, so no cache carries one
test's answer into the next, and a new cache needs no reset of its own.

The registry holds the very object the module's name is bound to. A cache is
emptied in place (``.clear()``) and never rebound, neither by its module nor by
a test; ``tests/test_process_state.py`` checks both, and that every
module-level cache in ``utils/`` is registered.
"""

from __future__ import annotations

import os
import sys
import threading
import time
from typing import Any, Callable, List, NamedTuple, Optional, Tuple

#: How long :func:`reset_all` waits for a cache's own lock, and for its
#: ``busy`` check to read False. Only a thread a test left running can hold
#: one that long; the reset then leaves that cache alone and fails.
LOCK_WAIT_S = 1.0

#: How often :func:`reset_all` re-reads a ``busy`` check while it waits.
_BUSY_POLL_S = 0.005


class CacheBusyError(RuntimeError):
    """:func:`reset_all` left a cache as it was: its owner held the cache's
    lock, or was still filling it, for :data:`LOCK_WAIT_S`."""


class _Entry(NamedTuple):
    name: str
    container: Any
    lock: Optional[Any]
    busy: Optional[Callable[[], bool]]
    #: The registering module's file, to find the thread that holds the lock.
    source: Optional[str]


_ENTRIES: List[_Entry] = []
_ENTRIES_LOCK = threading.Lock()


def process_cache(
    name: str,
    factory: Callable[[], Any] = dict,
    *,
    lock: Optional[Any] = None,
    busy: Optional[Callable[[], bool]] = None,
) -> Any:
    """A new empty container (a ``dict`` unless ``factory`` says otherwise),
    registered under ``name`` for :func:`reset_all`.

    ``name`` is ``<module>.<attribute>``, the module named from the skill
    directory (``utils.yaml_io._CACHE``). Names may repeat: a reloaded module,
    or one imported under two names, registers its new container beside the
    old one, and both are cleared.

    ``lock`` is the lock the module already holds around the cache; a cache
    that has one must pass it, and :func:`reset_all` clears only while holding
    it. ``busy`` (only with ``lock``) is read under that lock and is True while
    a worker computes an entry outside it (it holds a per-key lock of the
    module's) and will write the answer back when done; the reset waits for it
    to read False. A worker that has fetched its per-key lock but not yet taken
    it is invisible to it.
    """
    if busy is not None and lock is None:
        raise TypeError(f"process cache {name!r}: busy= needs the lock it is read under")
    container = factory()
    if not callable(getattr(container, "clear", None)):
        raise TypeError(f"process cache {name!r}: {type(container).__name__} has no clear()")
    source = sys._getframe(1).f_globals.get("__file__")
    with _ENTRIES_LOCK:
        _ENTRIES.append(_Entry(
            name, container, lock, busy, os.path.realpath(source) if source else None,
        ))
    return container


def reset_all() -> None:
    """Empty every registered cache in place (tests only, never a run path).

    A cache with a lock is emptied only under that lock and once its ``busy``
    check reads False. One that does not get there within :data:`LOCK_WAIT_S`
    is left as it was, since its owner is mid-update and relies on what it
    holds; after every other cache is emptied, :class:`CacheBusyError` names
    each one left and the thread found running its module's code.
    """
    with _ENTRIES_LOCK:
        entries = list(_ENTRIES)
    stuck = [entry for entry in entries if not _clear(entry)]
    if stuck:
        lines = "\n".join(f"  {entry.name}: {_holders(entry)}" for entry in stuck)
        raise CacheBusyError(
            f"process_state.reset_all left {len(stuck)} cache(s) as they were: "
            f"each one's lock stayed held, or its owner was still filling it, "
            f"for {LOCK_WAIT_S} s.\n{lines}\nA thread a test started is still "
            "running; the test must join it before it ends."
        )


def _clear(entry: _Entry) -> bool:
    """Empty ``entry`` under its lock; False if that did not happen in time."""
    lock = entry.lock
    if lock is None:
        entry.container.clear()
        return True
    deadline = time.monotonic() + LOCK_WAIT_S
    while True:
        if not lock.acquire(timeout=max(0.0, deadline - time.monotonic())):
            return False
        try:
            if entry.busy is None or not entry.busy():
                entry.container.clear()
                return True
        finally:
            lock.release()
        if time.monotonic() >= deadline:
            return False
        time.sleep(_BUSY_POLL_S)


def _holders(entry: _Entry) -> str:
    """The other threads running code of the module that registered ``entry``,
    with where: the likely holder, since a plain lock records no owner."""
    me = threading.get_ident()
    names = {thread.ident: thread.name for thread in threading.enumerate()}
    found = []
    for ident, frame in sys._current_frames().items():
        if ident == me:
            continue
        while frame is not None:
            if entry.source and os.path.realpath(frame.f_code.co_filename) == entry.source:
                found.append(
                    f"thread {names.get(ident, ident)!r} is in "
                    f"{frame.f_code.co_name}() at {os.path.basename(entry.source)}:"
                    f"{frame.f_lineno}"
                )
                break
            frame = frame.f_back
    if found:
        return "; ".join(found)
    others = sorted(name for ident, name in names.items() if ident != me)
    return (
        "no other thread is running its module's code; live threads: "
        + (", ".join(repr(name) for name in others) or "none")
    )


def is_registered(container: Any) -> bool:
    """Whether this very object is a registered cache (identity, not equality)."""
    with _ENTRIES_LOCK:
        return any(entry.container is container for entry in _ENTRIES)


def registered_names() -> Tuple[str, ...]:
    """Every registered name, in registration order (repeats included)."""
    with _ENTRIES_LOCK:
        return tuple(entry.name for entry in _ENTRIES)
