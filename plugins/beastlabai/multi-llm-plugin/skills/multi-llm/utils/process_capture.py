"""Bounded capture of a provider CLI's stdout and stderr, and a wait that ends
with the process rather than with its pipes.

Both spawn lanes read a CLI through :class:`PipeCapture`: the review fan-out's
``llm_client._run_provider_cli`` and the executor's
``dispatch_spawn._spawn_in_context``. Each lane keeps its own spawn
(``process_control.popen_tree``), process-group choice, timeout and teardown;
this module only replaces what ``Popen.communicate`` did with the CLI's pipes.
See ``docs/development/providers.md`` ("Capturing a CLI's streams").

The rules:

* **Bounded.** Each stream keeps its first ``max_bytes`` bytes. Bytes past the
  bound are still read, so the CLI never blocks on a full pipe, then dropped
  and counted; :attr:`PipeCapture.capped` names the streams that passed it and
  each lane decides what that means (both refuse to parse a capped stdout, and
  never count its head as a finished answer).
* **Same text below the bound.** The kept bytes are decoded once, with the
  stream's own encoding and error handler, and newlines are translated exactly
  as ``Popen.communicate`` does in text mode, so a parser sees the same string.
  Stdin is encoded as ``communicate`` encodes it.
* **Ends with the process.** ``communicate`` waits for the CLI to exit, then
  allows at most ``grace_s`` for its output pipes to reach end of file. Stdin
  is fed on a thread of its own and is not part of the wait: once the CLI has
  exited, what it did not read is not sent. A process the CLI started and did
  not wait for can hold an inherited pipe open for ever; after the grace the
  capture keeps what was read, with a ``[PIPE_HELD]`` line.
* **A held pipe is the lane's to stop.** A lane that passes ``on_held`` has it
  called once, after the grace, when a pipe is still held: the lane stops the
  run's own processes as its timeout does before the call returns. Until then
  the CLI is left unreaped where ``waitid`` can watch its exit without
  reaping it (POSIX), so its pid and the group it leads still name its tree
  for that stop, as at a timeout (docs/development/runtime.md#process-primitives).
  :attr:`PipeCapture.still_held` names the pipes still held once the stop
  returned: held by a process outside what the stop reached.
* **Stdin fails as communicate fails.** The input is checked and encoded in
  the caller's thread before any feed starts, so an input the stream cannot
  take raises there. A feed ignores what ``communicate`` ignores (a reader
  that went away) and hands any other write error to the caller's
  :meth:`PipeCapture.communicate`, unless that call already timed out.
* **The prompt goes with the process.** The encoded input belongs to the
  capture, and a feed takes it one chunk at a time: when the CLI exits the
  capture drops what is left, so a write stuck on a pipe nobody reads holds
  one chunk, never the prompt.
* **Nothing is cut off for a survivor.** A pipe still held after the grace is
  never closed under its writer (which would end it with ``SIGPIPE`` or
  ``EPIPE``): its drain keeps reading and drops what it reads until the last
  writer closes it. The capture itself stops nothing; only a lane's
  ``on_held`` does.
* **A closed capture is let go.** After :meth:`PipeCapture.close` a drain
  still running holds only its pipe and an end-of-file flag, never the capture,
  its buffers or the ``Popen``, so a caller that drops the capture frees them
  however long a survivor keeps the pipe.
* **A watch can end the wait early.** An adapter's
  :meth:`~utils.providers.base.LLMProvider.stream_watch` is fed every stdout
  chunk as the drain reads it. The first reason it returns makes
  :meth:`PipeCapture.communicate` raise :class:`StreamStopped`, a
  ``TimeoutExpired``, so the lane stops the CLI through its own timeout path
  (the process-tree kill, the Windows job) and collects the rest as after a
  deadline. Nothing here kills anything. A CLI that already exited when the
  stop would be acted on returns as it ended. A watch that raises is dropped
  and the wait runs to the deadline as before
  (docs/development/providers.md#a-cli-that-loops).

How: right after the spawn, the capture takes the real pipe objects off the
``Popen`` (its ``stdin``/``stdout``/``stderr`` become ``None``) and drains the
output pipes on a thread of its own. ``Popen.communicate`` is still the call
that waits, under the caller's timeout, but with no pipes left to serve it
returns when the process does. A ``Popen`` stand-in without real pipes (the
tests') has nothing to take, and its own ``communicate`` answers as before.

POSIX drains both output pipes on one thread with a poll selector and feeds
stdin from another, in pieces the pipe has room for, so the feed stops as soon
as it is told to. Windows cannot select on pipes, so each pipe gets a blocking
thread (one per output pipe, and one writing stdin in chunks of :data:`_CHUNK`,
checking for a stop between them). None is ever closed from another thread:
Windows' anonymous pipes are synchronous, and the C runtime holds a lock on the
descriptor for the whole of a pending read or write, so a close from elsewhere
waits for that write rather than ending it (``Popen.communicate`` on Windows
likewise leaves a writer the child never reads running with its descriptor
open). A blocking thread whose pipe is still held finishes when the last
process on the other end closes it.
"""

from __future__ import annotations

import errno
import io
import os
import select
import selectors
import subprocess
import sys
import threading
import time
from typing import Any, Callable, Dict, FrozenSet, Optional, Tuple

#: Per-stream capture bound. A real answer stays far below it: the largest
#: stream on record is about 6.25 MB.
MAX_STREAM_BYTES = 32 * 1024 * 1024

#: How long a capture waits for a CLI's pipes to reach end of file once the CLI
#: itself is gone, after an exit or after a stop, and the ceiling on a lane's
#: post-stop drain.
DRAIN_S = 5.0

#: Read size per ``os.read``, and write size per blocking ``os.write`` on stdin:
#: the most a feed stuck on an unread pipe holds.
_CHUNK = 64 * 1024

#: Write size per ``os.write`` on stdin: a pipe the selector reports writable
#: has room for this much, so a write never blocks (``Popen._communicate``'s
#: own rule).
_PIPE_BUF = getattr(select, "PIPE_BUF", 512)

#: How often the POSIX stdin feed checks for a stop while the pipe is full.
_POLL_S = 0.2

#: A pipe closing as the CLI exits needs a moment to deliver its last bytes and
#: its end of file, even when the caller's deadline has nearly run out.
_MIN_GRACE_S = 0.2

#: How long a held pipe gets to reach end of file once the lane's ``on_held``
#: stop returned. That stop waits until what it signalled is gone, and a dead
#: process's descriptors are already closed, so a pipe still held past this is
#: held by a process the stop did not reach.
_AFTER_STOP_S = 1.0

#: ``os.waitid`` where the platform has it: asked with ``WNOWAIT`` it says
#: whether a child exited without reaping it.
_waitid = getattr(os, "waitid", None)

#: The longest sleep between two looks at a CLI's exit while it is kept
#: unreaped (``Popen.wait``'s own ceiling when it polls).
_EXIT_POLL_S = 0.05

_STREAMS = ("stdout", "stderr")

#: A stdout watch: fed each chunk the drain reads (bytes, in order, cut
#: anywhere), it returns ``None`` to let the CLI run on or, once, the reason the
#: CLI should be stopped now (:meth:`LLMProvider.stream_watch`).
StreamWatch = Callable[[bytes], Optional[str]]

#: How often a watched wait checks whether its watch asked for a stop: the
#: longest a stop waits after the watch decided.
WATCH_POLL_S = 0.1


class StreamStopped(subprocess.TimeoutExpired):
    """The wait ended because the stdout watch asked for a stop, not because the
    deadline passed. A ``TimeoutExpired``, so each lane's timeout handler stops
    the CLI and drains it as after a deadline; :attr:`reason` is the watch's."""

    def __init__(self, cmd: Any, timeout: Optional[float], reason: str,
                 output: Any = None, stderr: Any = None) -> None:
        super().__init__(cmd, timeout, output=output, stderr=stderr)
        self.reason = reason

    def __str__(self) -> str:
        return f"Command '{self.cmd}' was stopped by its stream watch: {self.reason}"


def provider_watch(provider: Any) -> Optional[StreamWatch]:
    """A fresh stdout watch from *provider*'s ``stream_watch()``, or ``None``
    when it declares none or the call raises: a watch is never a reason for a
    dispatch to fail."""
    hook = getattr(provider, "stream_watch", None)
    if not callable(hook):
        return None
    try:
        watch = hook()
    except Exception:  # noqa: BLE001 - see the docstring
        return None
    return watch if callable(watch) else None


def stopped_early_text(reason: str, after_s: float, deadline: str) -> str:
    """The failure line both lanes give a CLI its stdout watch stopped: the
    watch's reason, then how soon it was stopped, against *deadline* (the
    lane's words for the limit it would otherwise have run to)."""
    return f"{reason}. Stopped after {after_s:.1f}s rather than at {deadline}"


def oversized_stream_message(stream: str, max_bytes: int) -> str:
    """The refusal both lanes give a capped stream they will not parse."""
    return (
        f"the runner produced more than {max_bytes} bytes on {stream}; "
        f"refusing to parse it rather than truncating a stream into a result"
    )


class _Sink:
    """One stream's kept bytes and its byte count."""

    def __init__(self, limit: int) -> None:
        self.limit = max(0, int(limit))
        self.data = bytearray()
        self.total = 0
        self.lock = threading.Lock()

    def add(self, chunk: bytes) -> None:
        with self.lock:
            self.total += len(chunk)
            room = self.limit - len(self.data)
            if room > 0:
                self.data += chunk[:room]

    def snapshot(self) -> bytes:
        with self.lock:
            return bytes(self.data)

    def decode(self, encoding: str, errors: str) -> str:
        """The kept bytes as text, decoded in place (no second copy)."""
        with self.lock:
            return self.data.decode(encoding, errors)

    @property
    def capped(self) -> bool:
        return self.total > self.limit


class _Tripwire:
    """A stdout watch and its verdict, shared by the drain that feeds it and the
    wait that reads it; it holds nothing of the capture."""

    __slots__ = ("watch", "reason", "tripped")

    def __init__(self, watch: StreamWatch) -> None:
        self.watch: Optional[StreamWatch] = watch
        self.reason: Optional[str] = None
        self.tripped = threading.Event()

    def feed(self, chunk: bytes) -> None:
        watch = self.watch
        if watch is None:
            return
        try:
            reason = watch(chunk)
        except Exception:  # noqa: BLE001 - a watch never stops the drain
            self.watch = None
            return
        if reason:
            self.watch = None
            self.reason = str(reason)
            self.tripped.set()


class _Outlet:
    """One output pipe as its drain sees it: the pipe, where its bytes go, and
    its end of file. A drain holds this and nothing else; :meth:`detach` drops
    the sink and the watch, after which what the drain reads is discarded."""

    __slots__ = ("stream", "fd", "sink", "eof", "tripwire")

    def __init__(self, stream: Any, fd: int, sink: _Sink) -> None:
        self.stream = stream
        self.fd = fd
        self.sink: Optional[_Sink] = sink
        self.eof = threading.Event()
        self.tripwire: Optional[_Tripwire] = None

    def take(self, chunk: bytes) -> None:
        sink = self.sink
        if sink is not None:
            sink.add(chunk)
        tripwire = self.tripwire
        if tripwire is not None:
            tripwire.feed(chunk)

    def detach(self) -> None:
        self.sink = None
        self.tripwire = None

    def finish(self) -> None:
        _close(self.stream)
        self.eof.set()


class _Feed:
    """The encoded stdin still to send, owned by the capture. A feed takes it
    one chunk at a time and holds nothing else of it, so :meth:`stop` frees the
    rest at once, even while that feed is stuck in a write. A write error the
    caller must see waits on :attr:`error`."""

    __slots__ = ("_data", "_offset", "_lock", "error")

    def __init__(self, data: bytes) -> None:
        self._data: Optional[bytes] = data
        self._offset = 0
        self._lock = threading.Lock()
        self.error: Optional[BaseException] = None

    @property
    def stopped(self) -> bool:
        return self._data is None

    def chunk(self, size: int) -> bytes:
        """The next unsent bytes, at most *size*, as bytes of their own (never a
        view that would keep the rest alive); empty once everything was sent or
        the feed was stopped."""
        with self._lock:
            data = self._data
            return b"" if data is None else data[self._offset:self._offset + size]

    def advance(self, count: int) -> None:
        with self._lock:
            self._offset += count
            if self._data is not None and self._offset >= len(self._data):
                self._data = None

    def stop(self) -> None:
        with self._lock:
            self._data = None


def _fileno(stream: Any) -> Optional[int]:
    try:
        return stream.fileno()
    except (AttributeError, OSError, ValueError):
        return None


def _close(stream: Any) -> None:
    try:
        stream.close()
    except (OSError, ValueError):
        pass


def _stdin_bytes(stream: Any, input: Any, *, selectable: bool) -> bytes:
    """*input* as the bytes ``Popen.communicate`` sends to *stream*. A text
    stream's input is encoded with the stream's encoding and error handler: on
    the selector path as ``Popen._save_input`` encodes it, on the reader-threads
    path as the stream's ``TextIOWrapper.write`` does for ``Popen._stdin_write``
    (``\\n`` turned into ``os.linesep`` first, and only ``str`` taken). Anything
    else must be bytes-like, or this raises ``TypeError``."""
    encoding = getattr(stream, "encoding", None)
    if isinstance(encoding, str):
        if isinstance(input, str):
            if not selectable and os.linesep != "\n":
                input = input.replace("\n", os.linesep)
            return input.encode(encoding, getattr(stream, "errors", None) or "strict")
        if not selectable:
            raise TypeError(f"write() argument must be str, not {type(input).__name__}")
    if isinstance(input, bytes):
        return input
    with memoryview(input) as view:
        return view.tobytes()


def _unbuffered(stream: Any) -> Any:
    """The raw file under a text or buffered *stream*, its wrappers detached
    (a feed writes the descriptor, never through them), so a feed holds a
    descriptor and not the write buffer, 128 KiB by default."""
    try:
        while not isinstance(stream, io.RawIOBase):
            stream = stream.detach()
    except (AttributeError, OSError, ValueError):
        pass  # keep the innermost layer reached; it still closes the pipe
    return stream


def _new_selector() -> selectors.BaseSelector:
    if hasattr(selectors, "PollSelector"):
        return selectors.PollSelector()
    return selectors.SelectSelector()


# -- the drains and feeds ------------------------------------------------------
# Module functions, not methods: a thread's target and arguments are all it
# keeps alive, and a survivor's drain must not keep the capture alive.

def _drain_selector(outlets: Tuple[_Outlet, ...]) -> None:
    """POSIX: every output pipe on one thread, until each reaches end of file.
    The only thread that closes them."""
    selector = _new_selector()
    live: Dict[int, _Outlet] = {}
    try:
        for outlet in outlets:
            selector.register(outlet.fd, selectors.EVENT_READ, outlet)
            live[outlet.fd] = outlet
        while live:
            try:
                ready = selector.select()
            except OSError:
                break  # the pipes are let go below; their end of file stays unset
            for key, _events in ready:
                outlet = key.data
                try:
                    chunk = os.read(key.fd, _CHUNK)
                except OSError:
                    chunk = b""
                if chunk:
                    outlet.take(chunk)
                    continue
                selector.unregister(key.fd)
                del live[key.fd]
                outlet.finish()
    finally:
        selector.close()
        for outlet in live.values():
            _close(outlet.stream)


def _drain_blocking(outlet: _Outlet) -> None:
    """Windows: one output pipe, blocking reads until end of file."""
    try:
        while True:
            try:
                chunk = os.read(outlet.fd, _CHUNK)
            except OSError:
                break
            if not chunk:
                break
            outlet.take(chunk)
    finally:
        outlet.finish()


def _feed_selector(stream: Any, feed: _Feed) -> None:
    """POSIX: write *feed* to the child's stdin whenever the pipe has room, until
    it is all written, the reading end is gone, or the feed is stopped (the CLI
    exited, or the capture closed). Then close the write end."""
    selector = _new_selector()
    try:
        fd = stream.fileno()
        try:
            os.set_blocking(fd, False)
        except OSError:
            pass  # the selector and _PIPE_BUF already keep a write from blocking
        selector.register(fd, selectors.EVENT_WRITE)
        while not feed.stopped:
            if not selector.select(_POLL_S):
                continue
            chunk = feed.chunk(_PIPE_BUF)
            try:
                feed.advance(os.write(fd, chunk))
            except BlockingIOError:
                continue
    except BrokenPipeError:
        pass  # nothing reads it any more: Popen._communicate ignores this too
    except Exception as exc:  # noqa: BLE001 - handed to communicate's caller
        feed.error = exc
    finally:
        selector.close()
        _close(stream)


def _feed_blocking(stream: Any, feed: _Feed) -> None:
    """Windows: ``Popen._stdin_write``'s write, on a thread of its own so the
    wait is not behind it, in chunks of :data:`_CHUNK` with a stop check
    between them. A write the CLI's survivors never read stays blocked holding
    one chunk (see the module docstring for why nothing closes it)."""
    try:
        fd = stream.fileno()
        while True:
            chunk = feed.chunk(_CHUNK)
            if not chunk:
                break
            feed.advance(os.write(fd, chunk))
    except BrokenPipeError:
        pass  # Popen._stdin_write ignores a reader that went away ...
    except OSError as exc:
        # ... and EINVAL, Windows' word for it (bpo-19612, bpo-30418).
        if exc.errno != errno.EINVAL:
            feed.error = exc
    except Exception as exc:  # noqa: BLE001 - handed to communicate's caller
        feed.error = exc
    finally:
        _close(stream)


class PipeCapture:
    """Drain *proc*'s stdout and stderr pipes into bounded buffers, and feed its
    stdin.

    Construct it right after the spawn and before anything else can fail, and
    call :meth:`close` in a ``finally``. Its :meth:`communicate` has
    ``Popen.communicate``'s contract (``input`` on the first call only, a
    ``TimeoutExpired`` carrying the output so far, a second call after a stop
    to collect the rest and reap the process), and it returns once the process
    has exited and its output pipes reached end of file, or once ``grace_s`` has
    passed since the exit.

    *selectable* picks the drain: ``True`` the POSIX selector threads, ``False``
    one blocking thread per pipe (the only kind Windows supports). ``None``
    picks by platform.

    *watch* (a :data:`StreamWatch`, or ``None``) is fed every stdout chunk the
    drain reads; once it returns a reason, :meth:`communicate` raises
    :class:`StreamStopped` and :attr:`stream_stop` keeps the reason.

    *on_held* (a callable taking this capture, or ``None``) is the lane's stop
    for what the CLI left holding a pipe: called at most once, by the first
    :meth:`communicate` that sees the CLI exit, when a pipe is still held after
    the grace. What it returns
    is kept as :attr:`held_stop`; an exception it raises leaves
    :attr:`held_stop` ``None`` and is not passed on. With it given, that call
    keeps the CLI unreaped until the stop has returned wherever ``waitid`` can
    watch the exit (POSIX, a real child), and reaps it before returning.
    Without it nothing is stopped, as before.
    """

    def __init__(
        self,
        proc: Any,
        *,
        max_bytes: int = MAX_STREAM_BYTES,
        grace_s: float = DRAIN_S,
        selectable: Optional[bool] = None,
        watch: Optional[StreamWatch] = None,
        on_held: Optional[Callable[["PipeCapture"], Any]] = None,
    ) -> None:
        self.proc = proc
        self.max_bytes = max_bytes
        self.grace_s = grace_s
        self.pipe_held = False
        #: What *on_held* returned, ``None`` when it was not called or raised.
        self.held_stop: Any = None
        #: Whether *on_held* was called (a held pipe, after the grace).
        self.held_stopped = False
        #: The pipes still held once *on_held* returned: their holder is
        #: outside what the lane's stop reached. Empty when it let go of them,
        #: or when there was no stop.
        self.still_held: FrozenSet[str] = frozenset()
        self._on_held = on_held
        self._called = False
        self._selectable = (os.name != "nt") if selectable is None else selectable
        self._outlets: Dict[str, _Outlet] = {}
        self._sinks: Dict[str, _Sink] = {}
        self._stdin: Any = None
        self._input_sent = False
        self._feed: Optional[_Feed] = None
        self._timed_out = False
        self._announced: set = set()
        self._tripwire: Optional[_Tripwire] = None
        self._stream_stop: Optional[str] = None
        for name in _STREAMS:
            stream = getattr(proc, name, None)
            fd = None if stream is None else _fileno(stream)
            if fd is None:
                continue
            sink = _Sink(max_bytes)
            self._sinks[name] = sink
            self._outlets[name] = _Outlet(stream, fd, sink)
            # Popen.communicate no longer reads this pipe, so it stops waiting
            # for the pipe's end of file and waits for the process instead.
            setattr(proc, name, None)
        if watch is not None and "stdout" in self._outlets:
            # Before the drain starts, so the watch sees the first byte.
            self._tripwire = _Tripwire(watch)
            self._outlets["stdout"].tripwire = self._tripwire
        stdin = getattr(proc, "stdin", None)
        if stdin is not None and _fileno(stdin) is not None:
            # Nor writes stdin: a survivor holding it unread would keep it
            # writing until the deadline.
            self._stdin = stdin
            proc.stdin = None
        self._passthrough = not self._outlets and self._stdin is None
        if self._outlets:
            try:
                self._start()
            except BaseException:
                # No drain: hand the pipes back, so the caller's fallback to
                # the bare process still reads and closes them.
                for name, outlet in self._outlets.items():
                    setattr(proc, name, outlet.stream)
                if self._stdin is not None:
                    proc.stdin, self._stdin = self._stdin, None
                self._outlets.clear()
                self._sinks.clear()
                self._input_sent = True
                raise

    # -- Popen's surface, for the lanes' drains -------------------------------

    @property
    def stdin(self) -> Any:
        return getattr(self.proc, "stdin", None)

    @property
    def stdout(self) -> Any:
        return getattr(self.proc, "stdout", None)

    @property
    def stderr(self) -> Any:
        return getattr(self.proc, "stderr", None)

    @property
    def capped(self) -> FrozenSet[str]:
        """The streams that passed :attr:`max_bytes`."""
        return frozenset(name for name, sink in self._sinks.items() if sink.capped)

    @property
    def stream_stop(self) -> Optional[str]:
        """The watch's reason when :meth:`communicate` ended the wait on it
        (raising :class:`StreamStopped`), else ``None``: a watch that decided
        after the CLI had already exited stopped nothing."""
        return self._stream_stop

    def communicate(self, input: Any = None, timeout: Optional[float] = None) -> Tuple[Any, Any]:
        """``proc.communicate(input=input, timeout=timeout)``, with the output
        from this capture for the pipes it drains and stdin fed by it.

        Raises ``TimeoutExpired`` carrying the output read so far when the
        process outlives *timeout*, or :class:`StreamStopped` (one) as soon as
        the stdout watch asks for a stop; the pipes stay open and drained, so a
        later call (after a stop) collects the rest. Raises what encoding
        *input* raised before anything is sent, and, once, a write error on
        stdin that ``communicate`` would not have ignored, unless a call already
        timed out (the run has failed; its drain must still collect the output).
        """
        if self._passthrough:
            return self.proc.communicate(input=input, timeout=timeout)
        started = time.monotonic()
        # The lane's stop belongs to the first call only: a later one collects
        # what is left after the lane's own stop (a timeout, a failed feed).
        hook, self._on_held = self._on_held, None
        unreaped = hook is not None and not self._called and self._can_hold_unreaped()
        self._called = True
        self._send(input)
        try:
            out, err = self._wait(timeout, unreaped=unreaped)
        except subprocess.TimeoutExpired as exc:
            self._timed_out = True
            output = self._text("stdout", exc.output)
            stderr = self._text("stderr", exc.stderr)
            if isinstance(exc, StreamStopped):
                expired: subprocess.TimeoutExpired = StreamStopped(
                    exc.cmd, exc.timeout, exc.reason, output=output, stderr=stderr,
                )
            else:
                expired = subprocess.TimeoutExpired(
                    exc.cmd, exc.timeout, output=output, stderr=stderr,
                )
            self._announce_caps()
            raise expired from None
        # The CLI is gone: what it did not read of its stdin, nothing will.
        feed = self._feed
        if feed is not None:
            feed.stop()
            # Recorded before the feed closed stdin, so before an exit that
            # end of file caused.
            error, feed.error = feed.error, None
            if error is not None and not self._timed_out:
                raise error
        if timeout is None:
            grace = self.grace_s
        else:
            grace = max(min(self.grace_s, timeout - (time.monotonic() - started)),
                        _MIN_GRACE_S)
        self._settle(grace, hook, unreaped)
        self._announce_caps()
        return self._text("stdout", out), self._text("stderr", err)

    def close(self) -> None:
        """Stop feeding stdin and let go of the buffers. Safe to call more than
        once. A pipe that has not reached end of file is not closed: its drain
        keeps reading it and drops what it reads, holding nothing of this
        capture."""
        if self._feed is not None:
            self._feed.stop()
        if not self._input_sent:
            self._input_sent = True
            stream, self._stdin = self._stdin, None
            if stream is not None:
                _close(stream)
        for outlet in self._outlets.values():
            outlet.detach()

    def _wait(self, timeout: Optional[float], *, unreaped: bool = False) -> Tuple[Any, Any]:
        """``proc.communicate(timeout=timeout)``, in slices of
        :data:`WATCH_POLL_S` while a watch is live, so a stop the watch asks
        for ends the wait within one slice. The first wait only: once a call
        has timed out (the lane is stopping the CLI), the watch has no say.
        *unreaped* waits for the exit without reaping the CLI
        (:meth:`_wait_exit`).

        A CLI that has already exited when the stop would be acted on returns
        as it ended: its exit decides, not the watch's verdict on steps it went
        on to finish (docs/development/providers.md#a-cli-that-loops).
        """
        tripwire = self._tripwire
        if tripwire is None or self._timed_out:
            return self._wait_exit(timeout, unreaped)
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            # An exited CLI makes the slice below return at once.
            if tripwire.tripped.is_set() and not self._exited(unreaped):
                self._stream_stop = tripwire.reason or "the stream watch asked for a stop"
                self._announce_stop(timeout)
                raise StreamStopped(getattr(self.proc, "args", None), timeout,
                                    self._stream_stop)
            step = WATCH_POLL_S
            if deadline is not None:
                step = max(0.0, min(step, deadline - time.monotonic()))
            try:
                return self._wait_exit(step, unreaped)
            except subprocess.TimeoutExpired as exc:
                if deadline is not None and time.monotonic() >= deadline:
                    raise subprocess.TimeoutExpired(
                        exc.cmd, timeout, output=exc.output, stderr=exc.stderr,
                    ) from None

    def _can_hold_unreaped(self) -> bool:
        """Can the CLI's exit be watched without reaping it? A real child of
        this process on POSIX, with ``waitid``, whose pipes this capture all
        took (``communicate`` would otherwise still read one)."""
        proc = self.proc
        pid = getattr(proc, "pid", None)
        return (
            os.name != "nt" and _waitid is not None
            and isinstance(pid, int) and pid > 0
            and getattr(proc, "returncode", 0) is None
            and all(getattr(proc, name, None) is None for name in ("stdin",) + _STREAMS)
        )

    def _unreaped_exit(self) -> Optional[bool]:
        """Has the CLI exited, asked without reaping it (``WNOWAIT``)? ``None``
        when that cannot be asked: no longer an unreaped child of this process
        (reaped elsewhere), or the call failed."""
        pid = getattr(self.proc, "pid", None)
        if _waitid is None or getattr(self.proc, "returncode", 0) is not None:
            return None
        try:
            return _waitid(os.P_PID, pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None
        except (OSError, TypeError, ValueError):
            return None

    def _exited(self, unreaped: bool) -> bool:
        """Has the CLI exited? Read without reaping it under *unreaped*,
        else through ``poll()``, which reaps it."""
        if unreaped:
            state = self._unreaped_exit()
            if state is not None:
                return state
        return self.proc.poll() is not None

    def _wait_exit(self, timeout: Optional[float], unreaped: bool) -> Tuple[Any, Any]:
        """``proc.communicate(timeout=timeout)``; under *unreaped* the same
        wait, with no pipes left for ``communicate`` to read, but leaving the
        CLI's zombie unreaped for :meth:`_settle` (``None`` for both streams,
        which this capture drains). Falls back to ``communicate`` once the
        exit can no longer be watched that way."""
        if not unreaped:
            return self.proc.communicate(timeout=timeout)
        deadline = None if timeout is None else time.monotonic() + timeout
        delay = 0.0005
        while True:
            state = self._unreaped_exit()
            if state is None:
                rest = None if deadline is None else max(0.0, deadline - time.monotonic())
                return self.proc.communicate(timeout=rest)
            if state:
                return None, None
            now = time.monotonic()
            if deadline is not None and now >= deadline:
                raise subprocess.TimeoutExpired(getattr(self.proc, "args", None), timeout)
            delay = min(delay * 2, _EXIT_POLL_S)
            if deadline is not None:
                delay = min(delay, deadline - now)
            time.sleep(max(0.0, delay))

    def _reap(self, unreaped: bool) -> None:
        """Reap a CLI :meth:`_wait_exit` left unreaped (it has exited, so this
        returns at once; the lane's stop may have reaped it already), through
        ``communicate``, which with no pipes left is the wait as everywhere
        else in this capture."""
        if unreaped and getattr(self.proc, "returncode", 0) is None:
            self.proc.communicate()

    def _announce_stop(self, timeout: Optional[float]) -> None:
        deadline = f"its {timeout}s deadline" if timeout else "an exit it will not make"
        print(
            f"[STREAM_STOP] pid {getattr(self.proc, 'pid', None)}: "
            f"{self._stream_stop}. Stopping it now rather than waiting for {deadline}.",
            file=sys.stderr, flush=True,
        )

    # -- the drain -------------------------------------------------------------

    def _start(self) -> None:
        if self._selectable:
            _spawn_thread(_drain_selector, (tuple(self._outlets.values()),),
                          "multi-llm-pipe-drain")
            return
        for name, outlet in self._outlets.items():
            _spawn_thread(_drain_blocking, (outlet,), f"multi-llm-pipe-drain-{name}")

    def _send(self, input: Any) -> None:
        """Start feeding *input* to stdin (first call only), as communicate
        would: nothing to send closes stdin at once."""
        if self._input_sent:
            return
        self._input_sent = True
        stream, self._stdin = self._stdin, None
        if stream is None:
            return
        if not input:
            _close(stream)
            return
        try:
            # Encoded here, so a type or encoding error is the caller's.
            self._feed = _Feed(_stdin_bytes(stream, input, selectable=self._selectable))
            stream = _unbuffered(stream)
            feeder = _feed_selector if self._selectable else _feed_blocking
            _spawn_thread(feeder, (stream, self._feed), "multi-llm-stdin-feed")
        except BaseException:
            _close(stream)
            raise

    def _settle(self, grace: float, hook: Optional[Callable[["PipeCapture"], Any]] = None,
                unreaped: bool = False) -> None:
        """Wait up to *grace* for every output pipe's end of file; past it, the
        pipe is held by something the CLI started: the capture lets go of what
        arrives, and the lane's *hook* stops what the CLI left running while
        the CLI, *unreaped*, still anchors its pid and group. Then the CLI is
        reaped. Anything raised here (an interrupt) leaves it unreaped for the
        lane's own stop, whose second call reaps it."""
        deadline = time.monotonic() + grace
        held = [name for name, outlet in self._outlets.items()
                if not outlet.eof.wait(max(0.0, deadline - time.monotonic()))]
        if not held:
            self._reap(unreaped)
            return
        self.pipe_held = True
        self.close()
        if hook is not None:
            self.held_stopped = True
            try:
                self.held_stop = hook(self)
            except Exception:  # noqa: BLE001 - the lane's stop reports its own failure
                self.held_stop = None
            until = time.monotonic() + min(self.grace_s, _AFTER_STOP_S)
            self.still_held = frozenset(
                name for name in held
                if not self._outlets[name].eof.wait(max(0.0, until - time.monotonic())))
        self._reap(unreaped)
        pid = getattr(self.proc, "pid", None)
        pipes = " and ".join(held)
        line = (f"[PIPE_HELD] pid {pid} exited (code {getattr(self.proc, 'returncode', None)}) "
                f"while a process it started still held its {pipes} open; kept what was "
                f"read after a {grace:.1f}s drain, and what arrives later is dropped. ")
        if hook is None:
            line += "Nothing was stopped for it: the pipe is still read."
        elif self.still_held:
            line += (f"The lane stopped what it left running, but its "
                     f"{' and '.join(sorted(self.still_held))} is still held by a "
                     f"process that stop did not reach.")
        else:
            line += "The lane stopped what it left running, and the pipe was let go."
        print(line, file=sys.stderr, flush=True)

    def _announce_caps(self) -> None:
        for name in sorted(self.capped - self._announced):
            self._announced.add(name)
            sink = self._sinks[name]
            print(
                f"[STREAM_CAP] pid {getattr(self.proc, 'pid', None)} wrote "
                f"{sink.total} bytes on {name}, more than the {sink.limit}-byte "
                f"bound; the first {sink.limit} were kept and the rest dropped.",
                file=sys.stderr, flush=True,
            )

    def _text(self, name: str, fallback: Any) -> Any:
        """The drained stream's capture as ``communicate`` would have returned
        it, or *fallback* for a stream this capture does not drain."""
        outlet = self._outlets.get(name)
        if outlet is None:
            return fallback
        sink = self._sinks[name]
        encoding = getattr(outlet.stream, "encoding", None)
        if not isinstance(encoding, str):
            return sink.snapshot()
        errors = getattr(outlet.stream, "errors", None) or "strict"
        # Popen.communicate's own text-mode translation (_translate_newlines).
        return sink.decode(encoding, errors).replace("\r\n", "\n").replace("\r", "\n")


def _spawn_thread(target: Any, args: Tuple[Any, ...], name: str) -> None:
    threading.Thread(target=target, args=args, name=name, daemon=True).start()
