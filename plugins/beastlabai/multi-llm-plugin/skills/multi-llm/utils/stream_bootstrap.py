"""Shared stdout/stderr bootstrap for orchestrator entry points.

Every top-level script (orchestrators, display/apply helpers, init) should
call :func:`bootstrap_streams` at the start of ``main()`` so all entry points
get consistent stream behavior for free.
"""

import os
import sys


class _FdWriter:
    """A text stream straight onto one file descriptor: no buffer, no lock.

    What a signal handler may print through (see :func:`streams_for_a_signal_handler`).
    Nothing it writes can be interrupted half-way into a state a nested handler
    would trip over, because there is no shared state to trip over.
    """

    encoding = "utf-8"
    errors = "replace"

    def __init__(self, fd: int) -> None:
        self._fd = fd

    def write(self, text) -> int:
        data = str(text).encode("utf-8", "replace")
        view = memoryview(data)
        while view:
            try:
                written = os.write(self._fd, view)
            except InterruptedError:  # pragma: no cover - PEP 475 retries it
                continue
            except OSError:
                break  # a closed log must never cost the abort its record
            view = view[written:]
        return len(text)

    def flush(self) -> None:
        return None

    def fileno(self) -> int:
        return self._fd

    def isatty(self) -> bool:
        return False

    def writable(self) -> bool:
        return True


def streams_for_a_signal_handler() -> None:
    """Point ``sys.stdout``/``sys.stderr`` at lock-free writers on fds 1 and 2.

    Called first thing by a signal handler that prints and then ends the
    process. A Python handler runs on the main thread between bytecodes,
    which includes the inside of ``BufferedWriter``'s flush: it checks for
    signals after every raw write while it holds the buffer's lock. A handler
    that prints through that same object then raises ``RuntimeError:
    reentrant call inside <_io.BufferedWriter name='<stderr>'>`` (Codex racing
    run 6, 2026-10-06: the second SIGTERM ``uv run`` forwards to its child
    landed inside the first handler's own ``print``). Whatever the interrupted
    write left in the old buffer is abandoned with it; the caller ends the
    process with ``os._exit``, which flushes nothing anyway.
    """
    sys.stdout = _FdWriter(1)
    sys.stderr = _FdWriter(2)


def bootstrap_streams() -> None:
    """Reconfigure sys.stdout/sys.stderr for portable streaming output.

    - ``line_buffering=True``: backgrounded runs (stdout redirected to a
      file, i.e. non-TTY) stream progress/validation/salvage markers instead
      of block-buffering for minutes. Defense-in-depth alongside
      PYTHONUNBUFFERED.
    - ``encoding="utf-8", errors="replace"``: when piped or redirected,
      Python on Windows defaults the streams to the locale codec (cp1252),
      so printing non-cp1252 characters (provider/model output, em dashes,
      smart quotes) raises UnicodeEncodeError. ``replace`` is lossy for
      unencodable characters but guarantees output always succeeds — the
      standard choice for tool/LLM text output. Rejected alternatives:
      surrogateescape (lone surrogates blow up on downstream UTF-8
      re-encode), backslashreplace (noisier in model-visible output).

    - stdin reads UTF-8 too, with its own error handler kept. A host pipes
      UTF-8 in (``util prior-changes append --summary-stdin`` takes a model's
      summary from a heredoc, ``--files-from -`` a path list), and a Windows
      pipe decodes with cp1252: an em dash was recorded as ``â€”`` for the
      next batch to read, and a byte cp1252 leaves undefined (``ō`` is
      ``C5 8D``) raised UnicodeDecodeError.

    Safe to call unconditionally: streams without ``reconfigure`` (tests or
    embedders replacing sys.stdout with non-TextIOWrapper objects) are left
    untouched.
    """
    for _stream in (sys.stdout, sys.stderr):
        if not hasattr(_stream, "reconfigure"):
            continue
        try:
            _stream.reconfigure(
                line_buffering=True, encoding="utf-8", errors="replace"
            )
        except (AttributeError, ValueError, OSError):
            # Non-reconfigurable stream — best effort only.
            pass
    if hasattr(sys.stdin, "reconfigure"):
        try:
            sys.stdin.reconfigure(encoding="utf-8", errors=sys.stdin.errors)
        except (AttributeError, ValueError, OSError):
            # Already read from, or not a text stream: left as it is.
            pass
