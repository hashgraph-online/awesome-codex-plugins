"""Swallowed exceptions you can ask to see: the advisory guard.

Advisory code (a status block, a hint line, a recorded route, a roster line)
must never fail the command it decorates, so it catches broadly and falls back.
That catch used to be silent in every case, which left a bug in, say, the
native implement view with no trace at all. Each such site now hands what it
caught to :func:`note_swallowed` (or wraps itself in :func:`advisory`), which
decides by the environment at the moment of the catch:

* default: silent, exactly as the bare ``except Exception`` it replaces;
* ``MULTI_LLM_DEBUG=1``: the site's label and the traceback go to stderr. Stdout
  and the ``MULTI_LLM_RESULT`` line are never touched;
* ``MULTI_LLM_STRICT_ADVISORY=1`` **inside a pytest process**: the exception
  is re-raised. The test suite sets it for the files that cover the converted
  modules (``tests/conftest.py``, ``STRICT_ADVISORY_FILES``), so a new failure
  there fails a test instead of vanishing. Anywhere else the variable is
  ignored and the default holds: a detached worker a test spawns inherits it
  but is a fresh interpreter that imports no pytest, and so is a host or a
  shell that has it exported. Strict mode never reaches a real run.

What a site expects (an absent or unreadable file, an unknown host id) is
caught by a narrower clause *before* the broad one and stays silent in every
mode: the guard is for what nobody expected. Signal handlers, ``atexit`` and
close-out paths keep their plain silent excepts: they must never raise, even
under strict mode, and must print only through ``stream_bootstrap._FdWriter``.
See docs/development/runtime.md#advisory-guards.

Stdlib plus the L0 ``stream_bootstrap``; layer L0 (``tests/test_import_layers.py``).
"""

from __future__ import annotations

import os
import sys
import traceback
from contextlib import contextmanager
from typing import Iterator, Optional

from .stream_bootstrap import _FdWriter

DEBUG_ENV = "MULTI_LLM_DEBUG"
STRICT_ENV = "MULTI_LLM_STRICT_ADVISORY"

_TRUE_WORDS = ("1", "true", "yes", "on")


def _switched_on(value: Optional[str]) -> bool:
    return value is not None and value.strip().lower() in _TRUE_WORDS


def debug_enabled() -> bool:
    """Whether ``MULTI_LLM_DEBUG`` asks for swallowed exceptions on stderr."""
    return _switched_on(os.environ.get(DEBUG_ENV))


def _in_a_test_process() -> bool:
    """Whether this process is a pytest run, read from its own ``sys.modules``.

    Never from the environment, which every child inherits: a worker spawned
    from a test ``execve``s a fresh interpreter, so it fails this test."""
    return "pytest" in sys.modules


def strict_enabled() -> bool:
    """Whether ``MULTI_LLM_STRICT_ADVISORY`` asks for them re-raised: only
    inside a pytest process (:func:`_in_a_test_process`), never in a run."""
    return _switched_on(os.environ.get(STRICT_ENV)) and _in_a_test_process()


def _report(label: str, exc: BaseException) -> None:
    """Write *label* and *exc*'s traceback to stderr. Never raises.

    Through ``sys.stderr`` first, so a test's capture and the order of the
    process's other stderr lines hold; if that stream fails (closed, or a
    reentrant buffered write), straight onto fd 2 through the lock-free
    writer signal handlers use."""
    try:
        text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        message = f"multi-llm debug: swallowed in {label}:\n{text}"
    except Exception:  # noqa: BLE001 - a broken __str__ still gets its label out
        message = f"multi-llm debug: swallowed in {label}: {type(exc).__name__}\n"
    try:
        sys.stderr.write(message)
        sys.stderr.flush()
        return
    except Exception:  # noqa: BLE001 - fall through to the raw descriptor
        pass
    try:
        _FdWriter(2).write(message)
    except Exception:  # noqa: BLE001 - nowhere left to say it
        pass


def note_swallowed(label: str, exc: BaseException) -> None:
    """Record that an advisory site swallowed *exc*; call it inside the ``except``.

    Silent by default; under ``MULTI_LLM_DEBUG`` writes *label* and the
    traceback to stderr; under ``MULTI_LLM_STRICT_ADVISORY`` in a pytest
    process re-raises *exc* (the caller's fallback then never runs). *label* names the site the way a
    reader would look for it: ``"status: native implement view"``."""
    if strict_enabled():
        raise exc
    if debug_enabled():
        _report(label, exc)


@contextmanager
def advisory(label: str) -> Iterator[None]:
    """``with advisory("status: roster line"):`` swallows any ``Exception``
    the block raises, through :func:`note_swallowed`. For a block whose
    fallback is "nothing happens"; a site that falls back to a value catches
    and calls :func:`note_swallowed` itself."""
    try:
        yield
    except Exception as exc:  # noqa: BLE001 - the advisory guard itself
        note_swallowed(label, exc)
