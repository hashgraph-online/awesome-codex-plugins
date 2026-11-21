"""Launch spacing: a minimum interval between two dispatches of one provider.

A CLI with a measured concurrent-start fault declares
``LLMProvider.LAUNCH_STAGGER_S`` (cursor-agent, 2 s); every other adapter
declares 0 and never meets this module. One :class:`LaunchLimiter` serves a
whole fan-out (every slot, and every attempt of every slot) and spaces the
*dispatches*, not the slots' admissions:

- a slot takes its turn only once it holds its semaphores (:meth:`LaunchLimiter.slot`),
  so slots that queued behind other providers cannot dispatch together;
- every dispatch takes its turn right before it starts (:func:`attempt_turn`,
  :func:`attempt_turn_blocking`): a slot's first dispatch confirms the slot's
  turn, after whatever preparation the lane did, or waits again when another
  slot of the provider took one meanwhile, and every ladder retry takes a fresh
  one, so a retry cannot land beside another slot's first attempt;
- the wait is charged to whatever deadline the caller is running against, and
  a turn is never granted once that deadline has passed.

A blocking waiter (Lane B's retry, on a worker thread) is not stopped when its
asyncio slot is cancelled, just as the dispatch it precedes is not: it keeps
its place and takes its turn. No adapter that declares a launch interval
serves the executor's profiles today.

See docs/development/delegation.md#read-and-analyze-executor.

Pure apart from the clock and the sleep: nothing here imports another skill
module, and the tracker transitions are callbacks.
"""

from __future__ import annotations

import asyncio
import contextlib
import contextvars
import threading
import time
from typing import AsyncIterator, Callable, Dict, List, Mapping, Optional

#: How early a woken waiter may claim its turn: event-loop timers fire up to
#: one clock resolution before the time they were set for.
_EPSILON = 1e-6

#: The launch turn of the fan-out slot this code runs in, or ``None`` outside
#: one (a direct call, or a provider that is not spaced). Set for the slot's
#: coroutine only; ``asyncio.to_thread`` copies it into the worker thread, which
#: is how Lane B's blocking retry loop finds it.
_CURRENT: contextvars.ContextVar[Optional["SlotLaunch"]] = contextvars.ContextVar(
    "multi_llm_slot_launch", default=None
)


class LaunchLimiter:
    """Per-provider minimum spacing between dispatches, shared by one fan-out.

    A turn is taken at the moment it is claimed, never reserved ahead: a waiter
    sleeps until its estimated turn (its place in the line times the interval)
    and claims only when it has waited longest for that provider and the
    interval since the last claim has passed. So waiters are served in arrival
    order, and one that stops waiting (a cancelled slot, a spent budget) takes
    no turn: it wakes every waiter behind it, which then works its turn out
    again from its new place in the line. The state sits behind a thread lock
    because Lane B's retries wait on worker threads, and a wake reaches either
    kind of waiter (an event-loop task or a worker thread).
    """

    def __init__(
        self,
        intervals: Mapping[str, float],
        *,
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        self._intervals: Dict[str, float] = {
            name: float(seconds)
            for name, seconds in intervals.items()
            if seconds and float(seconds) > 0
        }
        self._clock = clock
        self._lock = threading.Lock()
        self._last: Dict[str, float] = {}
        self._holder: Dict[str, object] = {}
        self._waiting: Dict[str, List[_Waiter]] = {}

    def spaces(self, provider: str) -> bool:
        """Whether *provider* has a launch interval at all."""
        return provider in self._intervals

    def now(self) -> float:
        """The limiter's clock: the injected one, else the clock the sleep counts in.

        On the event loop's thread that is the loop's own clock (what
        ``asyncio.sleep`` waits on), on any other thread ``time.monotonic``;
        a stock loop's clock *is* ``time.monotonic``.
        """
        if self._clock is not None:
            return self._clock()
        try:
            return asyncio.get_running_loop().time()
        except RuntimeError:
            return time.monotonic()

    def _next_wait(
        self,
        provider: str,
        waiter: object,
        give_up: Optional[float],
        wake: Callable[[], None],
    ) -> Optional[float]:
        """Claim *provider*'s turn for *waiter* (``0.0``), the seconds to sleep
        before asking again, or ``None`` once *give_up* has passed.

        *wake* is how a departing waiter ahead of this one cuts its sleep short.
        Expiry is checked before the turn: a turn granted at the deadline is one
        no dispatch can use, and it would still push every waiter behind it
        back by an interval.
        """
        interval = self._intervals[provider]
        with self._lock:
            now = self.now()
            if give_up is not None and now + _EPSILON >= give_up:
                return None
            queue = self._waiting.setdefault(provider, [])
            position = _index(queue, waiter)
            if position is None:
                queue.append(_Waiter(waiter, wake))
                position = len(queue) - 1
            last = self._last.get(provider)
            ready_at = now if last is None else last + interval
            if position == 0 and now + _EPSILON >= ready_at:
                queue.pop(0)
                self._last[provider] = now
                self._holder[provider] = waiter
                return 0.0
            wait = max(0.0, ready_at - now) + position * interval
            return wait if give_up is None else min(wait, give_up - now)

    def _leave(self, provider: str, waiter: object) -> None:
        """Take *waiter* out of the line (a no-op once it claimed), and wake
        everyone behind it: each of them is now one place closer."""
        with self._lock:
            queue = self._waiting.get(provider) or []
            position = _index(queue, waiter)
            if position is None:
                return
            queue.pop(position)
            behind = [entry.wake for entry in queue[position:]]
        for wake in behind:
            wake()

    def confirm(self, provider: str, holder: object) -> bool:
        """Move *holder*'s turn to now, its actual dispatch; ``False`` when
        another waiter claimed a turn since, and *holder* must wait again."""
        with self._lock:
            if self._holder.get(provider) is not holder:
                return False
            self._last[provider] = max(self._last[provider], self.now())
            return True

    async def wait_turn(
        self,
        provider: str,
        waiter: object,
        *,
        budget: Optional[float] = None,
        on_wait: Optional[Callable[[float], None]] = None,
    ) -> bool:
        """Wait for and claim *provider*'s turn; ``False`` when *budget*
        seconds ran out first. An unspaced provider returns at once."""
        if not self.spaces(provider):
            return True
        give_up = None if budget is None else self.now() + max(0.0, budget)
        loop = asyncio.get_running_loop()
        woken = asyncio.Event()

        def wake() -> None:
            # From any thread: the departing waiter may be a worker thread's.
            with contextlib.suppress(RuntimeError):  # the loop has closed
                loop.call_soon_threadsafe(woken.set)

        try:
            while True:
                woken.clear()
                wait = self._next_wait(provider, waiter, give_up, wake)
                if not wait:
                    return wait is not None
                if on_wait is not None:
                    on_wait(wait)
                with contextlib.suppress(asyncio.TimeoutError):
                    await asyncio.wait_for(woken.wait(), wait)
        finally:
            self._leave(provider, waiter)

    def wait_turn_blocking(
        self,
        provider: str,
        waiter: object,
        *,
        budget: Optional[float] = None,
        on_wait: Optional[Callable[[float], None]] = None,
        pause: Callable[[threading.Event, float], object] = threading.Event.wait,
    ) -> bool:
        """:meth:`wait_turn` for a worker thread.

        *pause* sleeps for at most the seconds given, or until the event is
        set (a waiter ahead left the line): ``threading.Event.wait``.
        """
        if not self.spaces(provider):
            return True
        give_up = None if budget is None else self.now() + max(0.0, budget)
        woken = threading.Event()
        try:
            while True:
                woken.clear()
                wait = self._next_wait(provider, waiter, give_up, woken.set)
                if not wait:
                    return wait is not None
                if on_wait is not None:
                    on_wait(wait)
                pause(woken, wait)
        finally:
            self._leave(provider, waiter)

    @contextlib.asynccontextmanager
    async def slot(
        self,
        provider: str,
        *,
        label: str,
        on_wait: Optional[Callable[[float], None]] = None,
        after_wait: Optional[Callable[[], None]] = None,
    ) -> AsyncIterator[Optional["SlotLaunch"]]:
        """One fan-out slot's launch turn, entered once its semaphores are held.

        Waits for and claims *provider*'s turn, then installs the slot's
        :class:`SlotLaunch` for the coroutine run inside, where a ladder's
        attempts confirm or renew it. *on_wait* gets every wait (the tracker's
        ``staggering``, with the seconds), *after_wait* runs once a wait has
        ended (the row back to ``queued`` until the dispatch). An unspaced
        provider enters at once and installs nothing.
        """
        if not self.spaces(provider):
            yield None
            return
        launch = SlotLaunch(self, provider, label=label, on_wait=on_wait)
        if await launch.claim() and after_wait is not None:
            after_wait()
        token = _CURRENT.set(launch)
        try:
            yield launch
        finally:
            _CURRENT.reset(token)


class SlotLaunch:
    """One fan-out slot's place in its provider's launch spacing."""

    def __init__(
        self,
        limiter: LaunchLimiter,
        provider: str,
        *,
        label: str,
        on_wait: Optional[Callable[[float], None]] = None,
    ) -> None:
        self.limiter = limiter
        self.provider = provider
        self.label = label
        self._on_wait = on_wait
        # The slot holds a turn that no dispatch has used yet.
        self._unconfirmed = False

    def _announcer(self, what: str, *, tracked: bool) -> Callable[[float], None]:
        """One line per wait, the first time it sleeps; the tracker every time."""
        said = []

        def announce(seconds: float) -> None:
            if not said:
                said.append(True)
                print(
                    f"[{self.label}] Waiting {seconds:.1f}s {what} "
                    f"(staggered launch)..."
                )
            if tracked and self._on_wait is not None:
                self._on_wait(seconds)

        return announce

    async def claim(self) -> bool:
        """The slot's own turn; ``True`` when it had to wait for it."""
        waited = []
        announce = self._announcer("before starting", tracked=True)

        def on_wait(seconds: float) -> None:
            waited.append(seconds)
            announce(seconds)

        await self.limiter.wait_turn(self.provider, self, on_wait=on_wait)
        self._unconfirmed = True
        return bool(waited)

    def _confirmed(self) -> bool:
        if not self._unconfirmed:
            return False
        self._unconfirmed = False
        return self.limiter.confirm(self.provider, self)

    async def attempt(self, budget: Optional[float]) -> bool:
        """The turn for the slot's next dispatch, within *budget* seconds."""
        if self._confirmed():
            return True
        return await self.limiter.wait_turn(
            self.provider, self, budget=budget,
            on_wait=self._announcer("for its launch turn", tracked=True),
        )

    def attempt_blocking(self, budget: Optional[float]) -> bool:
        """:meth:`attempt` on a worker thread, where no tracker is written."""
        if self._confirmed():
            return True
        return self.limiter.wait_turn_blocking(
            self.provider, self, budget=budget,
            on_wait=self._announcer("for its launch turn", tracked=False),
        )


async def attempt_turn(budget: Optional[float] = None) -> bool:
    """The current slot's launch turn for its next dispatch, if it is spaced.

    Called right before every attempt a ladder dispatches, with what is left
    of the slot's deadline as *budget*; ``True`` outside a spaced slot.
    """
    launch = _CURRENT.get()
    return True if launch is None else await launch.attempt(budget)


def attempt_turn_blocking(budget: Optional[float] = None) -> bool:
    """:func:`attempt_turn` for a ladder that runs on a worker thread."""
    launch = _CURRENT.get()
    return True if launch is None else launch.attempt_blocking(budget)


class _Waiter:
    """One place in a provider's line: who waits, and how to wake them."""

    __slots__ = ("who", "wake")

    def __init__(self, who: object, wake: Callable[[], None]) -> None:
        self.who = who
        self.wake = wake


def _index(queue: List[_Waiter], waiter: object) -> Optional[int]:
    for position, queued in enumerate(queue):
        if queued.who is waiter:
            return position
    return None
