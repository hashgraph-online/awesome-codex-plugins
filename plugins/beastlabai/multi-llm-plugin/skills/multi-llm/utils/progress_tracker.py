"""Per-model fan-out progress: the ``progress.models`` map and the ``[PROGRESS]`` ticker.

The fan-out is the longest stretch of a run — 435 s of a 516 s ``review-plan``,
measured 2026-09-16 — and until this module existed the only thing written
during it was a slot counter, so a poll mid-run read ``models 0/4`` beside
models that had already finished and a foreground run said nothing at all. This
is the object that makes that window honest: one in-memory map, keyed by model
spec, written into the checkpoint's reserved ``progress`` object on every
transition, plus a task that prints one greppable line per configured interval
so a host tailing the log sees movement without polling anything.

Three properties are load-bearing and each one is a bug that was reasoned about
rather than a preference:

* **The map is written whole.** ``update_status`` merges ``progress`` key by key
  at its *top* level only (``_MERGED_OBJECTS``), so the nested ``models`` value
  is a single key: a write carrying one model's entry would replace the stored
  map with that one entry and drop every other model. Every write from here
  therefore carries the whole map, and a write that is *not* about the map (the
  counters restatement, a ``step=``) carries no ``models`` key at all, which is
  what keeps the executor mirrors and ``step`` alive beside it.
* **Elapsed is computed at read time, not stored per tick.** The file carries
  ``started_at`` (admission), ``dispatched_at`` (the first dispatch) and
  ``timeout_s``; every renderer derives a live dispatched row's elapsed as
  ``now - dispatched_at`` clamped at ``timeout_s``, and a row still waiting for
  its dispatch has no elapsed at all, only a wait, ``now - started_at``
  (:func:`entry_elapsed_s` and :func:`entry_queued_s` are those rules, exported
  so the ticker and ``run_status`` cannot drift apart). So the ticker prints
  and writes **nothing** on the interval, the checkpoint stays event-driven,
  and ``checkpoint_lock`` gains no periodic contender. A stored per-tick
  ``elapsed_s`` would be a cache that is stale between ticks, frozen at
  ``interval_s: 0``, and rendered as truth by every reader. ``elapsed_s`` is
  written exactly once, at the terminal transition, from a
  :func:`time.monotonic` origin stamped at the **first dispatch**, and
  ``queued_s`` beside it holds the wait between admission and that dispatch —
  the two figures a reader cannot recompute afterwards. They are separate
  because they answer different questions: the per-model timeout clock starts
  inside the concurrency semaphores, so counting the queue wait as run time
  made a slot that waited for a sibling read as having spent its whole budget
  (measured 2026-09-27: pi recorded 1666.1 s, of which 464.7 s was the kimi
  slot it queued behind; plan: review-run-scope-salvage-and-failure-visibility
  §6). A slot that never dispatched freezes ``elapsed_s: 0`` with its whole
  wait in ``queued_s``.
* **Every ending retires every slot.** The lifecycle has two terminal states and
  nothing may outlive the fan-out in ``queued``/``staggering``/``running``/
  ``retrying``: :meth:`FanoutProgress.sweep` retires the rest with one of
  exactly two wordings — :data:`DEADLINE_ERROR` for the overall-deadline path
  (the same string ``backfill_deadline_losses`` writes into ``failed_models``,
  so the table and the report's failure list name one cause) and
  :data:`CANCELLED_ERROR` for every other abandonment. Terminal transitions are
  idempotent, which is what makes the fan-out's sweep, the ticker's own teardown
  sweep and F11's backfill safe against each other.

  **In-memory sweeps cover every ending that runs Python on the way out, and
  ``--abort`` is not one of them** (F1, 2026-09-20). ``status --abort`` signals
  the worker, and ``detach.RunHandle._on_signal`` ends in ``os._exit(3)``: no
  ``finally`` runs, no task is cancelled, so neither the fan-out's sweep nor the
  ticker's teardown is reached and the map on disk keeps whatever the last
  transition wrote — ``run.state: aborted`` beside rows still reading
  ``running``, with ``models_done`` frozen mid-count, rendered an hour later as
  ``codex:gpt-5.6-sol  running  30m00s/30m``. The only code that does run there
  is ``RunHandle.finish``, so that is where the retirement lives:
  :func:`retire_live_entries` does it as a read-modify-write of the map **on
  disk**, under the ``checkpoint_lock`` ``finish`` already takes, without
  reaching for an in-memory tracker from a signal handler.

Top-level imports stay light on purpose. ``utils.run_status`` reuses the
formatters below to render ``status --view run``, and ``status`` must stay a
sub-second command, so ``utils.detach``, ``utils.status_file`` and
``utils.provider_registry`` are imported lazily inside the functions that need
them rather than dragged in by every importer of this module.
"""

from __future__ import annotations

import asyncio
import sys
import time
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple, Union

# ---------------------------------------------------------------------------
# The lifecycle
# ---------------------------------------------------------------------------

STATE_QUEUED = "queued"
STATE_STAGGERING = "staggering"
STATE_RUNNING = "running"
STATE_RETRYING = "retrying"
STATE_DONE = "done"
STATE_FAILED = "failed"

#: The two states a slot may end in. There is deliberately no ``skipped``: a
#: model answered from disk is ``done`` — it has a usable result — and the
#: distinction lives in ``source`` (see :data:`RESUME_SOURCES`), so
#: ``models_done`` and ``models_succeeded`` stay derivable from ``state`` alone.
TERMINAL_STATES = frozenset({STATE_DONE, STATE_FAILED})

#: Render order for the live half of the map: **reverse** lifecycle, most
#: advanced state first, so a ticker line opens with the models that are really
#: working and ends with the ones still waiting, rather than following whatever
#: order a dict happened to grow in. (The comment here used to say "lifecycle
#: order", which is the tuple read backwards — a false comment is a defect.)
#: Read as a set it is also the complement of :data:`TERMINAL_STATES` — the
#: states :meth:`FanoutProgress.sweep` exists to retire — so a reader checking
#: "is anything still live?" has one list to consult rather than two.
LIVE_STATES: Tuple[str, ...] = (
    STATE_RUNNING, STATE_RETRYING, STATE_STAGGERING, STATE_QUEUED,
)

#: The live states that mean *admitted, not yet dispatched*: the slot is
#: sleeping out its stagger or parked on a concurrency semaphore. A row in one
#: of them has no run time yet — :func:`entry_elapsed_s` is ``None`` for it —
#: only a wait (:func:`entry_queued_s`). Read from ``state`` and never from the
#: absence of ``dispatched_at``, so a map written before that key existed reads
#: its queued rows the same way (plan: review-run-scope-salvage-and-failure-
#: visibility §6.2).
WAITING_STATES = frozenset({STATE_QUEUED, STATE_STAGGERING})

#: How many queued slots the ``[PROGRESS]`` line names, longest wait first,
#: before it counts the rest as ``+N more`` (decision 11.13 of that plan). A
#: bare ``queued 3`` said nothing about which models were waiting or for how
#: long, while eight named waits on one line is noise the count already carries.
QUEUED_NAMED_MAX = 3

#: The ``source`` values that mean "this row never dispatched, it was answered
#: from disk". A renderer that wants to label such a row *skipped* reads this
#: rather than inventing a state for it. ``salvage`` — a slot that *did*
#: dispatch and whose unparseable result was repaired in-process — is
#: deliberately outside this set; see
#: ``review_orchestrator_base.flip_map_entries_to_done``.
RESUME_SOURCES = frozenset({"existing_file", "resume"})

#: The wording ``backfill_deadline_losses`` (F11) writes into ``failed_models``,
#: so the per-model table and the report's failure list name one cause rather
#: than two. Set through :meth:`FanoutProgress.set_sweep_reason` by the fan-out's
#: ``except asyncio.TimeoutError`` branch.
DEADLINE_ERROR = "no result (cancelled at the fan-out deadline)"

#: Every other abandoned slot — the default sweep reason, and the wording
#: :func:`retire_live_entries` writes on the ``--abort`` path. Three endings
#: reach it and they are not the same mechanism: an owner that raised or
#: returned early (its own ``finally`` sweeps), asyncio shutdown's cancel-all
#: (a second Ctrl-C, where the ticker's teardown sweep is what is left running),
#: and ``status --abort``, which runs no Python in this process at all past
#: ``RunHandle.finish`` — see the module docstring. These two strings are the
#: *only* cancellation wordings; a third phrasing invented at a transition site
#: is a drift bug, because it splits one cause across two labels in the table
#: and the report.
CANCELLED_ERROR = "cancelled"

#: The greppable marker, in the style of the existing ``[SALVAGE_NEEDED]`` lines.
PROGRESS_PREFIX = "[PROGRESS]"


# ---------------------------------------------------------------------------
# Seams: the clock, the sleep and the print site
# ---------------------------------------------------------------------------
# Four module-level indirections rather than constructor arguments, because the
# constructors are a contract three orchestrators are wired against and because
# both tickers need the same seam. A unit test drives a whole 30 s fan-out over a
# fake clock in milliseconds by patching these; nothing in production does.

_monotonic: Callable[[], float] = time.monotonic

#: The *wall* clock, which is a second seam because the two answer different
#: questions: ``_monotonic`` freezes ``elapsed_s`` and ``queued_s`` at a
#: terminal transition, while this is the ``now`` a live row's elapsed and wait
#: are derived against (its ``dispatched_at`` and ``started_at`` are wall
#: stamps, so the arithmetic has to happen on the wall clock). Unpatched, a rendered-line test asserting ``(0m00s/30m)`` passes only
#: while its body runs inside one second — a latent flake that was in the suite
#: until 2026-09-20.
_wall_time: Callable[[], float] = time.time


async def _tick_sleep(delay: float) -> None:
    """The ticker's wait. Patched to a fake clock in the cadence tests."""
    await asyncio.sleep(delay)


def _emit(line: str) -> None:
    """The one print site for both tickers.

    ``flush=True`` because a host redirects the orchestrator's stdout to a file:
    ``bootstrap_streams`` sets line buffering in ``main()``, and this makes the
    marker land even in a process (or a test) that never called it.
    """
    print(line, flush=True)


def _warn_once(seen: set, key: str, message: str) -> None:
    """Say a failure once per tracker, on stderr, without the marker prefix.

    Once, because every condition these cover — an unwritable checkpoint, a
    renderer that cannot render — fails identically on every transition, and a
    line per transition would bury the run's real output in a repeat of the same
    sentence. Deliberately *not* prefixed ``[PROGRESS]``: Layer 2 tells an agent
    to relay the last ``[PROGRESS]`` line it sees, and a warning that matched
    that grep would be relayed to the user as progress.
    """
    if key in seen:
        return
    seen.add(key)
    print(f"multi-llm warning: {message}", file=sys.stderr)


def _now_iso() -> str:
    """The wall-clock stamp format the rest of the checkpoint uses.

    Single-sourced from ``status_file.now_iso`` — the same writer as
    ``heartbeat_at`` — so every ISO stamp in ``.status.json`` parses with one
    reader (``detach._elapsed_since``) rather than with two that disagree about
    the timezone suffix.
    """
    from . import status_file

    return status_file.now_iso()


def _stamp_after(delay_s: Any) -> Optional[str]:
    """The ISO stamp *delay_s* seconds from now, or ``None`` for no usable delay.

    The one writer of ``stagger_until``. It takes the same wall clock and format
    as :func:`_now_iso`, so the reader (:func:`entry_stagger_remaining_s`) needs
    no second parser. The delay is admitted by the *value-level* rule
    (:func:`_seconds`, the same one that decides what ``timeout_s`` is written
    as) rather than by :func:`_renderable`, the formatters' backstop, which
    converts a string and leaves the sign to a clamp: a countdown built from
    ``"4"``, a bool, NaN, an infinity or a negative is a number the fan-out
    never slept, and a writer has no ``?`` to print.
    """
    number = _seconds(delay_s)
    if number is None or number < 0:
        return None
    from datetime import datetime, timedelta

    try:
        when = datetime.fromisoformat(_now_iso()) + timedelta(seconds=number)
    except (ValueError, OverflowError):
        return None
    return when.isoformat()


def _seconds(value: Any) -> Optional[Union[int, float]]:
    """A duration as the checkpoint should carry it: a bare int when integral.

    ``get_provider_timeout`` returns ``1800``; writing ``1800.0`` into a file a
    human reads (and a golden test diffs) buys nothing.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if number != number or number in (float("inf"), float("-inf")):  # NaN / inf
        return None
    return int(number) if number.is_integer() else round(number, 1)


# ---------------------------------------------------------------------------
# Formatters — exported, because `run_status` renders the same map
# ---------------------------------------------------------------------------


def _renderable(seconds: Any) -> Optional[float]:
    """*seconds* as a float a duration can be built from, or ``None``.

    ``int(max(0.0, float(x)))`` is what both formatters below reduce a duration
    to, and it is a **partial** function over the values ``json.loads`` can hand
    back from a checkpoint a human may edit: ``float("inf")`` and a 400-digit
    integer each raise ``OverflowError`` at that ``int()``/``float()``, and
    ``NaN`` silently renders ``0s``. These are leaf formatters on the ``status``
    path — the command a poll loop runs, whose exit 1 rule 2 reads as "the run
    state is unreadable, stop and report" — so the honest answer to a value that
    is not a duration is the ``?`` they already print for ``None``, never a
    traceback. :func:`entry_budget` is the *value-level* rule one layer up (it
    is what decides whether a denominator is shown at all); this is the backstop
    under every caller of these two, including the ``elapsed_s`` half, which no
    entry guard ever passes through.

    ``bool`` is excluded because it is an ``int``: a duration of ``True`` is a
    flag misfiled, not one second.
    """
    if seconds is None or isinstance(seconds, bool):
        return None
    try:
        number = float(seconds)
    except (OverflowError, TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):  # NaN / inf
        return None
    return number


def format_elapsed(seconds: Optional[float]) -> str:
    """``2m10s``, and ``1h04m10s`` once an hour is on the clock.

    Zero-padded past the hour so a column of rows stays aligned; not padded
    below it, because ``0m40s`` is the common case and ``00m40s`` reads as a
    field width rather than a duration. Anything that is not a finite number
    renders ``?`` rather than raising — see :func:`_renderable`.
    """
    number = _renderable(seconds)
    if number is None:
        return "?"
    total = int(max(0.0, number))
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}h{minutes:02d}m{secs:02d}s"
    return f"{minutes}m{secs:02d}s"


def format_budget(seconds: Optional[float]) -> str:
    """``30m`` — the slot's whole budget, rendered as the denominator.

    Coarser than :func:`format_elapsed` by design: a budget is a configured
    round number (``default_timeout: 1800``) and rendering it as ``30m00s``
    would invite reading it as a second live clock. Same total-function rule as
    its sibling: anything that is not a finite number renders ``?``.
    """
    number = _renderable(seconds)
    if number is None:
        return "?"
    total = int(max(0.0, number))
    if total < 60:
        return f"{total}s"
    hours, rest = divmod(total, 3600)
    minutes = rest // 60
    if hours and minutes:
        return f"{hours}h{minutes:02d}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"


def entry_elapsed_s(
    entry: Mapping[str, Any], now: Optional[float] = None
) -> Optional[float]:
    """How long this slot has been *running*, by the one read-time rule.

    Four rules, in order:

    1. ``ended_at`` present -> the stored ``elapsed_s``, frozen at the terminal
       transition and never touched again, so a table rendered an hour later
       shows the slot's real duration rather than a clock that kept running.
    2. A row still waiting for its dispatch (``state`` in
       :data:`WAITING_STATES`) -> ``None``. It has no run time yet; what it
       has is a wait, and :func:`entry_queued_s` is the rule for that. Keyed on
       ``state`` rather than on a missing ``dispatched_at``, so a map written
       before that key existed reads its queued rows the same way.
    3. A live row carrying ``dispatched_at`` -> ``now - dispatched_at``,
       clamped at ``timeout_s``. Always fresh, which is why no writer has to
       tick.
    4. A live row with no ``dispatched_at`` (a map written before the key
       existed) -> ``now - started_at``, clamped the same way — today's rule,
       so an old map renders as it always did.

    Rule 3 counts from the *first* dispatch, the origin the per-model timeout
    clock is taken from (it starts inside the concurrency semaphores). Counting
    from admission instead charged a slot's queue wait to its run: measured
    2026-09-27, pi's first live row read ``8m00s/20m`` the moment it
    dispatched, because it had queued eight minutes behind kimi (plan:
    review-run-scope-salvage-and-failure-visibility §6). A retry does not move
    the origin, so a retried slot's elapsed covers every attempt and the backoff
    between them — the same deadline the ladder charges them to.

    The clamp stays: now that the origin is the dispatch, a row pinned at its
    budget really does mean the slot's kill is due.

    *now* is a POSIX timestamp (``None`` = the real clock), matching
    ``detach.heartbeat_age`` and the rest of the status surface.
    """
    if not isinstance(entry, Mapping):
        return None
    if entry.get("ended_at"):
        stored = entry.get("elapsed_s")
        if isinstance(stored, bool) or not isinstance(stored, (int, float)):
            return None
        return float(stored)
    if _entry_state(entry) in WAITING_STATES:
        return None

    # One ISO parser for the whole checkpoint (`heartbeat_at`, `dispatched_at`,
    # `started_at`), imported lazily so `status` does not pay for the detach
    # subtree just to format a row.
    from . import detach

    dispatched = entry.get("dispatched_at")
    live = detach._elapsed_since(
        dispatched if dispatched else entry.get("started_at"), now
    )
    if live is None:
        return None
    # Through the one guard rather than a fourth inline type check: the clamp is
    # arithmetic on the stored budget, so it inherits every shape that makes the
    # renderers raise (``float()`` on a 400-digit integer is ``OverflowError``
    # here too).
    budget = entry_budget(entry)
    if budget is not None and budget > 0:
        return min(live, float(budget))
    return live


def _stored_duration(value: Any) -> Optional[float]:
    """A stored duration as a float, or ``None`` when it is not one.

    :func:`_renderable`'s shapes (a bool, a string, NaN, an infinity, an
    integer too large for a float) plus a negative number, which no clock this
    module reads can produce.
    """
    number = _renderable(value) if isinstance(value, (int, float)) else None
    if number is None or number < 0:
        return None
    return number


def entry_queued_s(
    entry: Mapping[str, Any], now: Optional[float] = None
) -> Optional[float]:
    """How long this slot waited between admission and dispatch, or ``None``.

    The companion of :func:`entry_elapsed_s`: that one is run time, this is the
    wait in front of it — the stagger sleep plus the time parked on the
    concurrency semaphores. The two were one number until 2026-09-27, when a
    slot that queued behind a sibling recorded the sibling's run as its own
    (plan: review-run-scope-salvage-and-failure-visibility §6).

    * A terminal row (``ended_at`` present) -> the stored ``queued_s``, frozen
      beside ``elapsed_s``, or ``None`` when none was stored (a map written
      before the key existed, or a slot a ``--reaggregate`` closed out without
      knowing when its wait would have ended).
    * A row still waiting (:data:`WAITING_STATES`) -> ``now - started_at``: the
      wait so far, **unclamped**, because a wait is not charged to the slot's
      budget.
    * A live dispatched row -> the stored ``queued_s`` the first dispatch
      wrote, measured on the monotonic clock; failing that, ``dispatched_at -
      started_at``, since both stamps are exact.
    * A live row with no ``dispatched_at`` in any other state (a map written
      before the key existed) -> ``None``: its wait was never recorded.

    Total over what ``json.loads`` accepts, for the reason every reader of this
    map is: one malformed row costs its own clause, never the ``status``
    command. *now* follows :func:`entry_elapsed_s`'s convention.
    """
    if not isinstance(entry, Mapping):
        return None
    if entry.get("ended_at"):
        return _stored_duration(entry.get("queued_s"))

    from . import detach

    if _entry_state(entry) in WAITING_STATES:
        return detach._elapsed_since(entry.get("started_at"), now)
    dispatched = entry.get("dispatched_at")
    if not dispatched:
        return None
    stored = _stored_duration(entry.get("queued_s"))
    if stored is not None:
        return stored
    start = detach._parse_stamp(entry.get("started_at"))
    end = detach._parse_stamp(dispatched)
    if start is None or end is None:
        return None
    try:
        return max((end - start).total_seconds(), 0.0)
    except (ValueError, TypeError, OverflowError):
        return None


def entry_stagger_remaining_s(
    entry: Mapping[str, Any], now: Optional[float] = None
) -> Optional[float]:
    """Seconds until this ``staggering`` slot dispatches, or ``None``.

    Reads ``stagger_until``, the stamp :meth:`FanoutProgress.staggering` writes
    for the sleep it is about to take, against *now* (a POSIX timestamp;
    ``None`` = the real clock — the same convention as :func:`entry_elapsed_s`).
    ``None`` covers every case with nothing honest to count down: a row in any
    state but ``staggering`` (a stale stamp on a row that moved on is not a
    countdown), no stamp, a stamp that does not parse, and a stamp already in
    the past — the slot is flipping to ``queued`` at that instant and a poll
    that lands on the write is better served by no clause than by ``starts in
    0s``. Total over what ``json.loads`` accepts, for the reason every reader of
    this map is: one malformed row costs its own clause, never the ``status``
    command.
    """
    if not isinstance(entry, Mapping) or _entry_state(entry) != STATE_STAGGERING:
        return None
    from datetime import datetime

    from . import detach

    when = detach._parse_stamp(entry.get("stagger_until"))
    if when is None:
        return None
    try:
        reference = datetime.now() if now is None else datetime.fromtimestamp(now)
        remaining = (when - reference).total_seconds()
    except (ValueError, TypeError, OverflowError, OSError):
        return None
    if remaining <= 0:
        return None
    return remaining


def one_line_ascii(text: str) -> str:
    """One line, ASCII — the scrub every rendered ``[PROGRESS]``-class line takes.

    Two halves, and both are about a reader that counts lines.

    **ASCII**, because every host redirects the orchestrator's stdout to a file,
    so these lines are always written to a non-TTY pipe and a redirected stream
    takes the locale codec (cp1252 on Windows) — the reason
    ``utils/stream_bootstrap.py`` exists at all. The separators here are ``|``
    and ``,`` precisely so nothing in the line *can* be lossy; this scrub only
    covers a model spec that arrived from a config file carrying something
    exotic, and it degrades it the same way the stream's own
    ``errors="replace"`` would.

    **One line**, because a *line* renderer whose output contains a newline is
    two lines, and the second one is forgeable. Every field these renderers
    interpolate is either a number this module produced or a string from
    outside it — a model spec is a **config key** (``providers.yaml``, a project
    override, a typed ``--models`` value), a ``step`` is whatever a phase
    wrote — so a newline inside one puts a line with no ``[PROGRESS]`` prefix
    and no context into the log, and on the OpenCode package route, where
    ``toastMessage`` joins the dispatcher's supplied lines with a newline, that
    second line is indistinguishable from one the dispatcher composed. Nothing
    downstream can tell them apart afterwards, so folding here is the only
    defence. ``run_status._one_line`` is the field-level spelling of the same
    rule (it covers ``error`` in the human table, which is deliberately not
    ASCII-scrubbed); this is the whole-line one, and **both** renderers that
    feed ``progress_lines`` take it.

    Idempotent on well-formed lines: the separators this module composes with
    are single spaces, so a second pass is a no-op.
    """
    return " ".join(str(text).split()).encode("ascii", "replace").decode("ascii")


def render_roster_line(models: Mapping[str, Any]) -> str:
    """The one line that says what a fan-out is *over*, from the map alone.

    ``[PROGRESS] fan-out over 3 models: codex:gpt-6-astra:xhigh (30m),
    pi:openrouter/deepseek/deepseek-v4-flash-0731 (20m), opencode:auto (?)``

    A model spec already **is** the CLI and the model — ``codex:gpt-6-astra
    :xhigh`` is the codex CLI running gpt-6-astra at xhigh effort — so this
    derives nothing; it names the seeded map in seed order and renders each
    slot's whole budget beside it, which is the one figure a reader needs to
    know how long the ticker's line may stay unchanged.

    It is **not** a progress line and carries no counts: it states the roster,
    where until it existed a detached run's log opened at whatever the first
    interval happened to catch and never said which models the run was fanning
    out over at all. :meth:`FanoutProgress.render_line` is the line that reports
    movement.

    Budgets go through :func:`format_budget`, so a slot whose budget could not
    be resolved (:meth:`FanoutProgress._budget_for` leaves the key absent or
    ``None`` rather than failing the fan-out) renders ``(?)`` rather than a
    blank pair of parentheses that reads as "no budget".

    An empty map renders ``""`` — "fan-out over 0 models:" with nothing after
    the colon is not a shorter roster, it is a line with no content, and the
    caller drops it rather than printing a dangling separator.

    **A module function rather than only a method**, because two processes want
    the same sentence and only one of them owns a tracker. The fan-out emits it
    at :meth:`FanoutProgress.seed` from the in-memory map; ``status`` renders it
    for the OpenCode package route from ``progress.models`` read back off
    ``.status.json``, which is the same map, in the same key order, carrying the
    same ``timeout_s`` — so the two are one spelling and cannot drift into two.
    An entry that is not a mapping (a hand-edited checkpoint, or a row
    :func:`retire_live_entries` copied through untouched) renders ``(?)`` like
    any other unresolved budget rather than taking the line down.
    """
    if not isinstance(models, Mapping):
        return ""
    count = len(models)
    if not count:
        return ""
    rows = ", ".join(
        f"{spec} ({format_budget(entry_budget(entry))})"
        for spec, entry in models.items()
    )
    noun = "model" if count == 1 else "models"
    return one_line_ascii(
        f"{PROGRESS_PREFIX} fan-out over {count} {noun}: {rows}"
    )


def entry_budget(entry: Any) -> Optional[Union[int, float]]:
    """This entry's ``timeout_s`` if it is a *renderable* duration, else ``None``.

    The on-disk map is not guaranteed to hold what the tracker wrote — the same
    reason :func:`entry_elapsed_s` type-checks what it reads — and every
    consumer of this value ends in ``int(max(0.0, float(x)))``, which is a
    **partial** function over what ``json.loads`` accepts. Four shapes either
    take a renderer down or make it lie, and all four reach here from a file a
    human may edit:

    * ``Infinity`` / ``-Infinity`` — bare tokens Python's ``json.loads``
      accepts; ``int(float("inf"))`` is ``OverflowError``;
    * an integer with no float to convert to (a 400-digit literal is valid
      JSON): ``float()`` itself raises ``OverflowError``;
    * ``NaN`` — also accepted by ``json.loads``, and it renders ``0s``, a
      budget of nothing claimed about a slot that has one;
    * a negative number, which clamps to the same false ``0s``.

    A raise here is not a cosmetic failure. The caller is ``status``, the
    command a poll loop runs, and rule 2 reads its exit 1 as "the run state is
    unreadable, stop and report" — so one malformed row must cost its own
    ``(?)`` and never the poll, which is the rule :func:`_model_timing_text`
    was given for ``started_at`` (F5, 2026-09-20) and the same one this guard
    only half-kept: the docstring said "anything that is not a plain number is
    ``None``" while the code passed every ``int``/``float`` straight through.

    The ``isinstance`` check is what keeps a *string* out — ``"30"`` converts
    cleanly and would render ``30s``, which is a number the tracker never wrote
    — while ``bool`` is excluded one level down, by :func:`_renderable`, because
    it *is* an ``int`` in Python and ``timeout_s: true`` would otherwise render
    ``(1s)``: a plausible duration invented out of a flag. Both halves are
    needed and neither subsumes the other.

    One guard for the three renderers that read this field (the roster, the
    ticker's live rows, ``run_status``'s table) plus :func:`entry_elapsed_s`'s
    clamp, so a shape one of them survives cannot take another one down. The
    value is returned unconverted, so an ``int`` budget stays an ``int`` for the
    caller that compares it.
    """
    if not isinstance(entry, Mapping):
        return None
    budget = entry.get("timeout_s")
    if not isinstance(budget, (int, float)):
        return None
    number = _renderable(budget)
    if number is None or number < 0:
        return None
    return budget


def _entry_state(entry: Any) -> str:
    """This row's ``state`` word, or ``""`` for a row that is not a mapping.

    The in-memory map always holds dicts; the one read back off
    ``.status.json`` is not guaranteed to. A row with no readable state matches
    no live state and no terminal one, so it is counted in the total and named
    nowhere — which is the same degradation :func:`render_roster_line` gives it.
    """
    if not isinstance(entry, Mapping):
        return ""
    return str(entry.get("state") or "")


def _row_text(spec: str, entry: Mapping[str, Any], now: float) -> str:
    """``codex:gpt-5.6-sol (2m10s/30m, attempt 2)`` — one live row.

    The attempt is shown only past the first, and with no denominator (see
    :meth:`FanoutProgress.running`). The elapsed is computed here, never read
    from the entry, which is the same rule every other renderer applies.

    A module function rather than a method for the same reason
    :func:`render_roster_line` is one: ``status`` renders this row for the
    OpenCode package route out of ``progress.models`` read back off disk, and
    only the fan-out's own process owns a tracker.
    """
    elapsed = format_elapsed(entry_elapsed_s(entry, now))
    # The same guard the roster and `run_status`'s table read, so the three
    # spellings of one row's denominator cannot disagree.
    budget = format_budget(entry_budget(entry))
    extra = ""
    attempt = entry.get("attempt")
    if isinstance(attempt, int) and not isinstance(attempt, bool) and attempt > 1:
        extra += f", attempt {attempt}"
    backoff = entry.get("retry_after_s")
    if isinstance(backoff, (int, float)) and not isinstance(backoff, bool):
        extra += f", retry in {int(backoff)}s"
    return f"{spec} ({elapsed}/{budget}{extra})"


def render_progress_line(
    models: Any,
    *,
    total: Optional[int] = None,
    now: Optional[float] = None,
) -> str:
    """The ``[PROGRESS]`` line — counts, then the live rows — from a map alone.

    ``[PROGRESS] 4/8 done (3 ok, 1 failed) | running: codex:gpt-5.6-sol
    (2m10s/30m), opencode:auto (0m40s/30m) | queued: pi:openrouter/kimi
    (waiting 7m45s), gemini:pro (waiting 7m05s)``

    Running and retrying rows are named with their elapsed and their budget.
    Queued rows are named with their wait, longest first, up to
    :data:`QUEUED_NAMED_MAX` of them, then ``+N more`` (:func:`_queued_clause`):
    a bare ``queued 2`` said nothing about which models were waiting or for how
    long, and a wait read as run time is how a queued slot came to look as if
    it had spent its budget (plan: review-run-scope-salvage-and-failure-
    visibility §6). Staggering rows are counted — their wait is seconds long
    and the table's ``starts in`` clause already names it. Empty clauses are
    dropped, so a line never ends in a dangling separator, and an empty or
    unreadable map renders ``""`` rather than ``0/0 done``, which states
    nothing about a phase that has no fan-out.

    **A module function rather than only a method**, and for the reason
    :func:`render_roster_line` already is: two processes want this sentence and
    only one of them owns a tracker. The fan-out's ticker prints it into the log
    every interval; ``status`` renders it for the OpenCode package route out of
    ``progress.models`` read back off ``.status.json``. That route has no agent
    in its poll loop and its plugin may author no sentence, so without this it
    had nothing per-poll to show but a serialized object — measured 2026-09-21,
    a poll whose window happened to contain no completion relayed a multi-KB
    ``JSON.stringify`` of the whole payload, which is the ordinary case and not
    an edge one.

    It is also the line that **differs between two polls of a live fan-out**,
    which is what the package route's shown-once memory needs: every live row's
    elapsed (from ``dispatched_at``) and every queued row's wait (from
    ``started_at``) is derived at read time, so ninety seconds apart is ninety
    seconds of difference. A map whose rows are *all* terminal is
    genuinely unchanged and renders the same string twice — that window is the
    phase's, not the fan-out's, and ``run_status`` answers it with the phase's
    own ``progress:`` text instead.

    *total* is the denominator when the caller knows a requested spec the map
    has not grown yet (:meth:`FanoutProgress.counts` keeps that ``max``);
    without it the map is the whole roster, which is what a reader off disk has.
    """
    if not isinstance(models, Mapping) or not models:
        return ""
    rows = [
        (str(spec), entry, _entry_state(entry)) for spec, entry in models.items()
    ]
    done = sum(1 for _s, _e, state in rows if state in TERMINAL_STATES)
    ok = sum(1 for _s, _e, state in rows if state == STATE_DONE)
    count = len(rows) if total is None else total
    parts = [f"{PROGRESS_PREFIX} {done}/{count} done ({ok} ok, {done - ok} failed)"]
    reference = _wall_time() if now is None else float(now)
    for state in LIVE_STATES:
        live = [(spec, entry) for spec, entry, own in rows if own == state]
        if not live:
            continue
        if state in (STATE_RUNNING, STATE_RETRYING):
            parts.append(
                f"{state}: "
                + ", ".join(_row_text(spec, entry, reference) for spec, entry in live)
            )
        elif state == STATE_QUEUED:
            parts.append(_queued_clause(live, reference))
        else:
            parts.append(f"{state} {len(live)}")
    return one_line_ascii(" | ".join(parts))


def _queued_clause(
    live: Sequence[Tuple[str, Any]], now: float
) -> str:
    """``queued: pi:… (waiting 7m45s), fable:… (waiting 7m05s) +2 more``.

    Longest wait first, because the slot that has waited longest is the one a
    reader is asking about, and ties keep seed order so two polls of one map
    print one line. A row whose wait cannot be read sorts last and renders
    ``(waiting ?)`` rather than dropping out of a clause whose ``+N more`` count
    would then be wrong. Only the first :data:`QUEUED_NAMED_MAX` are named
    (decision 11.13 of plan review-run-scope-salvage-and-failure-visibility).
    """
    waits = [
        (index, spec, entry_queued_s(entry, now))
        for index, (spec, entry) in enumerate(live)
    ]
    waits.sort(key=lambda row: (row[2] is None, -(row[2] or 0.0), row[0]))
    named = ", ".join(
        f"{spec} (waiting {format_elapsed(wait)})"
        for _index, spec, wait in waits[:QUEUED_NAMED_MAX]
    )
    clause = f"{STATE_QUEUED}: {named}"
    rest = len(waits) - QUEUED_NAMED_MAX
    if rest > 0:
        clause += f" +{rest} more"
    return clause


def budget_for_spec(
    spec: str,
    *,
    anchor: Optional[Union[str, Any]] = None,
    timeout: Optional[float] = None,
) -> Optional[Union[int, float]]:
    """A slot's **whole** budget, resolved from config. The seed's own rule.

    Lifted out of :meth:`FanoutProgress._budget_for` because two processes have
    to agree about this number and only one of them owns a tracker: the fan-out
    seeds the map from it, and ``detach.launch`` — the invoker, which resolves
    the selection during pre-flight and then forks — renders the launch roster
    from it (see :func:`roster_line_for_specs`). A second resolution written at
    the second site is a second answer the day a default moves.

    Not the slice ``RetryLadder.next_attempt()`` hands back, which is what
    *remains* and shrinks every round. A config that cannot be read must not
    kill a fan-out at seed time or a launch at its banner, so a failure here is
    ``None`` and every renderer falls back to ``?``.
    """
    if timeout is not None:
        return _seconds(timeout)
    try:
        from .provider_registry import get_provider_timeout, parse_model_spec

        provider, _model = parse_model_spec(spec, anchor=anchor)
        return _seconds(get_provider_timeout(provider, anchor=anchor))
    except Exception:  # noqa: BLE001 - observability must not fail a fan-out
        return None


def roster_line_for_specs(
    specs: Optional[Sequence[str]],
    *,
    anchor: Optional[Union[str, Any]] = None,
    timeout: Optional[float] = None,
) -> str:
    """The roster line from a *selection*, for a caller that has no map yet.

    :func:`render_roster_line` renders a seeded map; this renders the same
    sentence from the list that map is about to be seeded from — for
    ``detach.launch``, which knows the resolved specs (it already refuses a
    launch whose CLIs are all missing) and forks before anything seeds.

    Why that caller needs the line at all: on the OpenCode package route the
    launch's own ``MULTI_LLM_RESULT`` is the **first** thing the plugin can
    relay, and the next one is a poll that costs a whole ``--wait`` (~83 s, the
    host cap less a margin). Rendered only from the checkpoint, the roster
    reaches the user a poll late on every run — and *never* on a run that goes
    terminal inside that first wait, because the terminal poll is deliberately
    not relayed. The requirement the line exists for is that a fan-out says
    what it is over when it **starts**.

    It is the same sentence and not a second one: the budgets go through
    :func:`budget_for_spec`, which is what :meth:`FanoutProgress._budget_for`
    now is, against the same anchor and the same per-run override — so the
    string the launcher renders and the one the worker's :meth:`seed` emits a
    moment later are byte-identical, and the package route's own "shown once"
    memory drops the duplicate instead of saying the roster twice. There is no
    race to lose: the two processes read config, not each other, so the worker's
    seed can neither be waited for nor contradicted. A config edited between the
    two reads costs one repeated line, never a wrong one — each is honest about
    what its own process resolved.

    Duplicate specs collapse exactly as they do in the seeded map, and an empty
    or absent selection renders ``""``: a ``--reaggregate`` launch, a write
    phase and ``generate-tasks`` have no fan-out to be over, and they reach here
    with no specs rather than with a special case.
    """
    return render_roster_line({
        str(spec): {
            "timeout_s": budget_for_spec(spec, anchor=anchor, timeout=timeout)
        }
        for spec in (specs or ())
    })


def _caller_is_being_cancelled() -> bool:
    """Is the task running *this* code itself under cancellation? (3.11+)

    Both tickers cancel their own task and then await it, which means the
    ``CancelledError`` that comes back is ambiguous: it is either the one we
    asked for (swallow it — a fan-out that succeeded must not fail on its own
    teardown) or our caller's, arriving while we were parked on that await
    (re-raise it — a swallowed cancellation is a run that keeps working after
    something asked it to stop). ``task.cancelled()`` cannot tell them apart: we
    called ``cancel()`` ourselves, so it is ``True`` in both.

    ``Task.cancelling()`` can: it counts the cancel requests outstanding against
    the *current* task, which is exactly "was I cancelled?", and it is the same
    question ``asyncio.timeout`` and ``TaskGroup`` ask of themselves.

    **Below 3.11 the distinction is not available** (this project's floor is
    3.10) and there is no safe substitute, so we answer ``False``: swallowing is
    what the code did before, while the other default would raise
    ``CancelledError`` out of *every* successful teardown, since awaiting a task
    we just cancelled always lands here. Say so rather than asserting a
    distinction the runtime cannot make.
    """
    try:
        current = asyncio.current_task()
    except RuntimeError:  # no running loop - not reachable from an await
        return False
    cancelling = getattr(current, "cancelling", None)
    if cancelling is None:  # < 3.11
        return False
    try:
        return bool(cancelling())
    except Exception:  # noqa: BLE001 - observability must not fail a fan-out
        return False


# ---------------------------------------------------------------------------
# The fan-out's tracker
# ---------------------------------------------------------------------------


class FanoutProgress:
    """The per-model map for one fan-out, plus the ticker that narrates it.

    One instance per fan-out, held in memory by the coroutine that owns the
    slots, and constructed against the directory whose ``.status.json`` the run
    writes — the *phase* dir on three lanes and ``ask``'s ``question_dir`` on the
    fourth, which is one level below the phase dir its siblings use.

    Every method that touches the map is synchronous — :meth:`stop_ticker` is
    the one coroutine here, and it awaits a task rather than the map — and every
    one of them is called on the fan-out's own event loop, so there is no lock:
    the writes serialize inside ``checkpoint_lock`` one level down, beside the
    heartbeat thread's.

    Args:
        phase_dir: the directory holding ``.status.json``.
        model_specs: every requested spec, in dispatch order. The map is seeded
            from this list *before* the tasks are created, so a poller sees a
            complete map from the first read instead of one that fills in as
            models start — and the write that claims the phase dir drops the
            predecessor's ``progress`` wholesale, so a model missing from the map
            is a bug, never a leftover. (``claim_run`` does that on the detached
            lane; on the foreground one, which is the lane Claude Code runs, the
            launch write does it — nothing did until F1, 2026-09-20.)
        anchor: the plan path (§9.3.c), threaded into ``parse_model_spec``,
            ``get_provider_timeout`` and ``get_progress_interval`` so a run
            started from a foreign CWD resolves the *project's* config.
        timeout: the fan-out's per-model override; when ``None`` each spec's
            budget comes from ``get_provider_timeout``.
        interval_s: the ticker cadence; when ``None`` it is read once here from
            ``progress.interval_s``. ``0`` means no ticker at all — the lines
            stop, every event-driven transition is still written.
    """

    def __init__(
        self,
        phase_dir: Union[str, Any],
        model_specs: Sequence[str],
        *,
        anchor: Optional[Union[str, Any]] = None,
        timeout: Optional[float] = None,
        interval_s: Optional[float] = None,
    ) -> None:
        self.phase_dir = str(phase_dir)
        self.model_specs: List[str] = [str(spec) for spec in model_specs]
        self.anchor = anchor
        self.timeout = timeout
        if interval_s is None:
            from .provider_registry import get_progress_interval

            interval_s = get_progress_interval(anchor=anchor)
        self.interval_s = float(interval_s)

        #: spec -> entry, in seed order. The whole of what gets written.
        self._models: Dict[str, Dict[str, Any]] = {}
        #: spec -> the monotonic reading stamped beside ``started_at``. Kept out
        #: of the entry because it is meaningless to a reader (an arbitrary
        #: process-local origin) and is only ever used to measure ``queued_s``.
        self._origins: Dict[str, float] = {}
        #: spec -> the monotonic reading stamped beside ``dispatched_at``, at
        #: the slot's *first* dispatch only. The origin ``elapsed_s`` is frozen
        #: from, for the same reason as ``_origins``: an NTP step or a suspended
        #: laptop cannot corrupt a monotonic difference. A spec absent here
        #: never dispatched.
        self._dispatch_origins: Dict[str, float] = {}
        self._sweep_reason = CANCELLED_ERROR
        self._ticker: Optional[asyncio.Task] = None
        #: Conditions already reported (see :func:`_warn_once`).
        self._warned: set = set()

    # -- the map ----------------------------------------------------------

    def seed(self) -> None:
        """Write every requested spec as ``queued``, with its budget and origin.

        Called *before* the tasks are created. A spec seeded here and never
        transitioned still ends terminal, because the sweep walks the map rather
        than the tasks.

        It is also the one place the roster is emitted (:meth:`render_roster`),
        directly after the write: seed runs exactly once per fan-out, so the
        line cannot repeat, and by this point every entry carries the budget the
        roster renders.
        """
        for spec in self.model_specs:
            self._seed_one(spec)
        self._write()
        self._emit_roster()

    def _seed_one(self, spec: str) -> Dict[str, Any]:
        stamp = _now_iso()
        self._origins[spec] = _monotonic()
        # A re-seeded spec starts a new admission, so nothing about a previous
        # dispatch may carry into it.
        self._dispatch_origins.pop(spec, None)
        entry: Dict[str, Any] = {
            "state": STATE_QUEUED,
            "started_at": stamp,
            "updated_at": stamp,
            "timeout_s": self._budget_for(spec),
            "attempt": 0,
            # Meaningful only after a completed attempt, so it is `null` here
            # rather than carrying a stale value into the next attempt.
            "source": None,
        }
        self._models[spec] = entry
        return entry

    def _budget_for(self, spec: str) -> Optional[Union[int, float]]:
        """The slot's *whole* budget, fixed for its life.

        Not the slice ``RetryLadder.next_attempt()`` hands back, which is what
        *remains* and shrinks every round: ``2m10s/30m`` rendered against a
        shrinking denominator would overstate the budget left. Seeding it from
        the same ``get_provider_timeout`` call the fan-out already makes to size
        its own deadline is what lets the roster name ``(30m)`` for a slot that
        has not dispatched yet instead of a blank, and it is what Layer 2's
        ceiling rule reads before any model has started.

        A config that cannot be read must not kill a fan-out at seed time, so a
        failure here leaves the key absent and every renderer falls back to
        ``?``.

        The rule itself lives in :func:`budget_for_spec`, because the launch
        renders the roster from the same specs before this object exists.
        """
        return budget_for_spec(spec, anchor=self.anchor, timeout=self.timeout)

    def _entry(self, spec: str) -> Dict[str, Any]:
        """This spec's entry, seeding one if a lane transitioned an unseeded slot.

        A missing entry is a wiring mistake, but the middle of a fan-out is the
        worst possible place to raise about one: an honest row written late beats
        a ``KeyError`` that loses seven other models' findings.
        """
        entry = self._models.get(spec)
        if entry is None:
            entry = self._seed_one(spec)
        return entry

    def _live_entry(self, spec: str) -> Optional[Dict[str, Any]]:
        """The entry to advance, or ``None`` when the slot is already frozen.

        Terminal is final in both directions: a resumed slot seeded ``done``
        must not be dragged back to ``running`` by a lane that transitions
        unconditionally, and a slot the sweep has retired must not start ticking
        again after the fan-out ended. The same one-way rule that makes
        :meth:`_freeze` idempotent.
        """
        entry = self._entry(spec)
        return None if entry["state"] in TERMINAL_STATES else entry

    def staggering(self, spec: str, *, delay_s: Optional[float] = None) -> None:
        """The slot is waiting out its stagger delay before dispatch.

        **Only the stagger sleep**, not the semaphore wait that follows it —
        see :meth:`queued`, which is where the slot goes next.

        *delay_s* is the sleep the caller is about to take, and it is what the
        row renders (2026-09-21): a fan-out launches its slots
        ``index * PROVIDER_STAGGER_DELAY`` apart, so the launch-time ``status``
        call — made on purpose at second zero, because the roster is the one
        thing worth relaying before the loop — finds every row but the first
        reading ``staggering``, which a reader took for the models being run one
        at a time. The word was true and said nothing about *how long*. The
        entry therefore carries ``stagger_until``, the wall-clock stamp the sleep
        ends at, and the table's detail column reads it back as ``starts in
        4s`` — the same shape ``retry in 20s`` already has for a backoff. A
        caller with no delay to name (``None``, or anything that is not a
        finite number) writes no stamp and the row reads as it did before.
        """
        entry = self._live_entry(spec)
        if entry is None:
            return
        entry["state"] = STATE_STAGGERING
        entry["updated_at"] = _now_iso()
        until = _stamp_after(delay_s)
        if until is None:
            entry.pop("stagger_until", None)
        else:
            entry["stagger_until"] = until
        self._write()

    def queued(self, spec: str) -> None:
        """The stagger is over; the slot is waiting for a concurrency slot.

        The other half of :meth:`staggering`, and the seeded state read back
        (2026-09-21). ``max_parallel`` — and a provider's own
        ``max_concurrent`` — park a slot *after* its stagger sleep has elapsed
        and *before* the per-model coroutine that calls :meth:`running` is
        entered, and nothing marked that boundary: five models at
        ``max_parallel: 2`` rendered three rows as ``staggering`` for as long
        as they waited, minutes after every stagger delay had run out, which
        the lifecycle does not describe. Index 0 never staggers and never calls
        this — it reads ``queued`` from the seed until it runs — so the two
        waits are one state either way.

        Not a step backwards: ``queued`` is *admitted, not yet dispatched*, and
        that is exactly what a slot parked on a semaphore is. :meth:`_live_entry`
        keeps it off a terminal row, and no caller reaches here after
        :meth:`running`.
        """
        entry = self._live_entry(spec)
        if entry is None:
            return
        entry["state"] = STATE_QUEUED
        # The countdown it advertised has run out; a `queued` row that kept it
        # would render a dispatch time already in the past.
        entry.pop("stagger_until", None)
        entry["updated_at"] = _now_iso()
        self._write()

    def running(
        self,
        spec: str,
        *,
        attempt: Optional[int] = None,
        timeout_s: Optional[float] = None,
    ) -> None:
        """A dispatch has started — the first one, or the one after a backoff.

        *attempt* is ``ladder.attempt_index``: 1-based, incremented by
        ``next_attempt()``, never reset, and with **no denominator** — the ladder
        keeps two independent counters (transport retries and rate-limit
        backoffs), so the entry can never honestly render ``2/3``.

        *timeout_s* is accepted for the one case the seed cannot know about: a
        per-slot override that gave this model a different budget from its
        provider default.

        The **first** call stamps the dispatch (:meth:`_mark_dispatched`):
        ``dispatched_at``, ``queued_s`` and the monotonic origin ``elapsed_s`` is
        later frozen from. A later call — the dispatch after a backoff — moves
        none of them, because the retry is charged to the same slot deadline.
        """
        entry = self._live_entry(spec)
        if entry is None:
            return
        stamp = _now_iso()
        entry["state"] = STATE_RUNNING
        entry["updated_at"] = stamp
        entry.pop("stagger_until", None)
        self._mark_dispatched(spec, entry, stamp)
        if attempt is not None:
            entry["attempt"] = int(attempt)
        if timeout_s is not None:
            entry["timeout_s"] = _seconds(timeout_s)
        # Present only while `retrying`: a running row that still advertised a
        # backoff would read as "waiting" in the table.
        entry.pop("retry_after_s", None)
        self._write()

    def _mark_dispatched(self, spec: str, entry: Dict[str, Any], stamp: str) -> None:
        """Stamp this slot's first dispatch, once, and the wait that preceded it.

        ``dispatched_at`` is the wall stamp a reader counts a live row's elapsed
        from; ``queued_s`` is dispatch minus admission on the monotonic clock,
        written here because it is final the moment the slot dispatches. The
        name ``dispatched_at`` already means exactly this on the write
        scheduler's ``in_flight`` rows, so a reader of the checkpoint learns one
        word, not two.

        Idempotent: the first dispatch is the origin the per-model timeout clock
        is taken from, and a retry's dispatch is charged to that same deadline.
        """
        if spec in self._dispatch_origins:
            return
        reading = _monotonic()
        self._dispatch_origins[spec] = reading
        entry["dispatched_at"] = stamp
        origin = self._origins.get(spec)
        if origin is not None:
            entry["queued_s"] = _seconds(round(max(0.0, reading - origin), 1))

    def retrying(
        self,
        spec: str,
        *,
        attempt: Optional[int] = None,
        retry_after_s: Optional[float] = None,
    ) -> None:
        """The ladder handed back a retry or a rate-limit backoff.

        The entry stays ``retrying`` for the sleep and returns to ``running``
        when the next attempt is dispatched. ``elapsed_s`` is *not* reset by
        this: the backoff is charged to the same slot deadline, so a reset would
        claim budget the slot does not have, and the dispatch origin stays at
        the first dispatch.

        A retry follows an attempt, so a slot that reaches here is dispatched
        whether or not its lane called :meth:`running` first; the dispatch is
        stamped here when nothing stamped it, rather than leaving a live
        ``retrying`` row that reads like a map written before ``dispatched_at``
        existed.
        """
        entry = self._live_entry(spec)
        if entry is None:
            return
        stamp = _now_iso()
        entry["state"] = STATE_RETRYING
        entry["updated_at"] = stamp
        self._mark_dispatched(spec, entry, stamp)
        if attempt is not None:
            entry["attempt"] = int(attempt)
        if retry_after_s is None:
            entry.pop("retry_after_s", None)
        else:
            entry["retry_after_s"] = _seconds(retry_after_s)
        self._write()

    def done(self, spec: str, *, source: Optional[str] = None) -> None:
        """The slot produced a usable result. Terminal, frozen, idempotent.

        A model answered from disk by a resume skip is ``done`` the moment it is
        seeded (``source: existing_file`` / ``resume``, ``attempt: 0``,
        ``elapsed_s: 0`` and no wait to speak of in ``queued_s``), because it
        has a usable result and no attempt is ever dispatched — so a resumed run
        of four models that finds three on disk reads ``3/4`` at the *first*
        poll rather than ``0/4``.
        """
        self._freeze(spec, STATE_DONE, source=source)

    def failed(
        self, spec: str, *, error: Any, source: Optional[str] = None
    ) -> None:
        """The slot ended without a usable result. Terminal, frozen, idempotent.

        *error* is the reason string that lane already has — ``failed_models``'
        value, ``ask_one``'s error text, or one of the two cancellation
        wordings. It is absent on every non-terminal entry and on every ``done``
        entry, so its presence is itself the signal that something is wrong here.
        """
        self._freeze(spec, STATE_FAILED, error=error, source=source)

    def warn(self, spec: str, warning: str) -> None:
        """Record a non-fatal warning on this slot's entry (``warning`` key).

        Plan §4.3: an uncontained slot whose porcelain check saw a change its
        own audited stream could not have made keeps its findings, and the
        ``[SANDBOX_BYPASSED] … not attributed`` line lands here. It does not
        change the slot's state, and a terminal transition keeps it.
        """
        entry = self._entry(spec)
        entry["warning"] = str(warning)
        entry["updated_at"] = _now_iso()
        self._write()

    def record_readonly_audit(self, spec: str, verdict: Mapping[str, Any]) -> None:
        """Record an uncontained slot's combined stream-audit verdict (plan §4.3).

        The compact ``{clean, reason, actions}`` dict — never the stream. Kept
        across the terminal transition like ``warning``.
        """
        entry = self._entry(spec)
        entry["readonly_audit"] = dict(verdict)
        self._write()

    def record_result(self, spec: str, result: Any) -> None:
        """The terminal transition derived from a lane's returned result dict.

        ``{"success": ..., "source": ..., "error": ...}`` is the shape
        ``run_single_model``, ``ask_one`` and both skip predicates already
        return, so a call site that has the result in hand does not have to
        re-derive which of :meth:`done` / :meth:`failed` it means — and cannot
        get the ``source`` pass-through wrong, which is the value the resume and
        salvage renderers read.
        """
        if not isinstance(result, Mapping):
            # A lane that returned `None` (or a bare tuple) still has to retire
            # its slot; leaving it live would strand it until the sweep.
            self.failed(spec, error="no result recorded", source=None)
            return
        source = result.get("source")
        if result.get("success"):
            self.done(spec, source=source)
        else:
            self.failed(
                spec,
                error=result.get("error") or "failed with no error recorded",
                source=source,
            )

    def _freeze(
        self,
        spec: str,
        state: str,
        *,
        error: Any = None,
        source: Optional[str] = None,
        write: bool = True,
    ) -> bool:
        """Stamp a terminal state, once. Returns whether anything changed.

        **Idempotent on purpose.** A second terminal transition for the same spec
        is ignored, and that is what makes the fan-out's ``finally`` sweep, the
        ticker's own teardown sweep and F11's ``backfill_deadline_losses`` safe
        against each other: they all touch only non-terminal entries, so whoever
        arrives first records the real ending and the belt-and-braces passes
        behind it can never overwrite it with ``cancelled``.

        **The dispatch-origin rule**, shared with the two close-out writers that
        cannot reach this tracker (:func:`retire_live_entries` and
        ``review_orchestrator_base.flip_map_entries_to_done``), so the three
        cannot drift apart:

        * a slot that dispatched freezes ``elapsed_s`` from its **first**
          dispatch — the origin the per-model timeout clock is taken from — and
          keeps the ``queued_s`` that dispatch wrote;
        * a slot that never dispatched freezes ``elapsed_s: 0``, and its whole
          wait, admission to now, goes in ``queued_s`` (decision 11.14 of plan
          review-run-scope-salvage-and-failure-visibility).

        This used to freeze from the *seed* origin, so a terminal row could not
        shrink below the live number it replaced while the live number counted
        the queue wait too. Nothing shrinks under the dispatch rule either: a
        live row counts from ``dispatched_at`` as well (:func:`entry_elapsed_s`),
        and a never-dispatched row renders a wait, not a number. What changed
        is that a slot which queued behind a sibling no longer records the
        sibling's run as its own. A monotonic difference is also what an NTP
        step or a suspended laptop cannot corrupt.
        """
        entry = self._entry(spec)
        if entry["state"] in TERMINAL_STATES:
            return False
        stamp = _now_iso()
        reading = _monotonic()
        origin = self._origins.get(spec)
        dispatch = self._dispatch_origins.get(spec)
        entry["state"] = state
        entry["updated_at"] = stamp
        entry["ended_at"] = stamp
        if dispatch is not None:
            entry["elapsed_s"] = _seconds(round(max(0.0, reading - dispatch), 1))
            if origin is not None:
                # Already written at the dispatch; restated so a terminal row
                # always carries it, and it is the same figure.
                entry["queued_s"] = _seconds(round(max(0.0, dispatch - origin), 1))
        else:
            entry["elapsed_s"] = 0
            if origin is not None:
                entry["queued_s"] = _seconds(round(max(0.0, reading - origin), 1))
        entry["source"] = source
        if state == STATE_FAILED:
            entry["error"] = str(error) if error is not None else CANCELLED_ERROR
        else:
            entry.pop("error", None)
        entry.pop("retry_after_s", None)
        if write:
            self._write()
        return True

    def set_sweep_reason(self, reason: str) -> None:
        """Name the cause *both* sweeps will write (:data:`DEADLINE_ERROR`).

        Called in the fan-out's ``except asyncio.TimeoutError`` branch, before
        the ticker is cancelled. The reason is stored rather than passed to
        :meth:`sweep` because there are two sweepers — the fan-out's ``finally``
        and the ticker's own — and a reason passed at one call site would let
        them disagree about the wording for the same run.
        """
        self._sweep_reason = str(reason)

    def sweep(self) -> None:
        """Retire every slot that is still live, with the stored reason.

        After this, no entry reads ``queued``, ``staggering``, ``running`` or
        ``retrying`` — which is the whole point: an abandoned slot does not
        retire itself. A **cancelled** one reaches no transition site at all —
        ``CancelledError`` is raised at whichever ``await`` it was parked on, and
        every ``tracker.done()``/``failed()`` call on that lane sits *below* that
        await — and a slot that **raised** is printed as ``Task exception:`` and
        dropped without ever being keyed into ``results``. So the map cannot be
        left to the slots to close out; this walks the map instead of the tasks.

        The reason is not "the overall-timeout branch cancels without awaiting
        them", which this docstring used to claim: ``asyncio.wait_for`` awaits
        the gather it cancelled before it raises ``TimeoutError`` on 3.10–3.12,
        so every child really is done by the time that handler runs. It is
        *still* what the children never recorded that makes the sweep load-bearing
        (F5, 2026-09-20).

        One write for the whole sweep, and **no write at all when nothing was
        live** — so a fan-out that ended cleanly leaves the map exactly as its
        last transition wrote it and a reader never sees a redundant rewrite of a
        frozen map.
        """
        changed = False
        for spec in list(self._models):
            if self._models[spec]["state"] in TERMINAL_STATES:
                continue
            changed |= self._freeze(
                spec, STATE_FAILED, error=self._sweep_reason, source=None, write=False
            )
        if changed:
            self._write()

    # -- reading ----------------------------------------------------------

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        """A copy of the map. Entries hold only scalars, so one level is deep."""
        return {spec: dict(entry) for spec, entry in self._models.items()}

    def counts(self) -> Tuple[int, int, int]:
        """``(models_done, models_succeeded, models_total)``, derived from the map.

        ``models_done`` counts **finished slots, not successful ones** — exactly
        ``fanout_slot_counter``'s documented meaning ("a failed or skipped model
        has finished its slot"), which the retired helper and this share so the
        mid-run number is unchanged. A live progress line cannot use the other
        meaning: under it the counter walks backwards at the end of a lossy run
        and can never reach ``8/8``. ``models_succeeded`` is what the
        post-fan-out restatements compute today, so "3 of 4 worked" survives as
        ``8/8 done, 7 ok, 1 failed`` rather than as a shrinking numerator.
        """
        done = sum(
            1 for e in self._models.values() if e["state"] in TERMINAL_STATES
        )
        succeeded = sum(
            1 for e in self._models.values() if e["state"] == STATE_DONE
        )
        # The map is seeded from `model_specs`, so these agree; the max keeps a
        # lane that transitioned a spec it never requested from reporting `9/8`.
        total = max(len(self.model_specs), len(self._models))
        return done, succeeded, total

    def render_line(self) -> str:
        """This fan-out's ``[PROGRESS]`` line. See :func:`render_progress_line`.

        The rendering rules live there rather than here, exactly as
        :meth:`render_roster` defers to :func:`render_roster_line` and for the
        same reason: ``status`` renders this line for the OpenCode package route
        out of the map this one is written from, and a second spelling of the
        sentence is a second sentence the day one of them moves.

        The denominator is :meth:`counts`' — ``max(len(model_specs), len(map))``
        — rather than the map's own length, so a lane that transitioned a spec
        it never requested still cannot report ``9/8`` and a spec requested but
        never seeded is still counted. A reader off disk has only the map and
        passes nothing.
        """
        return render_progress_line(self._models, total=self.counts()[2])

    def render_roster(self) -> str:
        """This fan-out's roster line, at launch. See :func:`render_roster_line`.

        The rendering rules live there rather than here because ``status``
        renders the same line for the OpenCode package route out of
        ``progress.models`` — the map this one is written from — and a second
        spelling of the sentence is a second sentence the day one of them moves.
        """
        return render_roster_line(self._models)

    def _emit_roster(self) -> str:
        """Print the roster once, respecting the ticker's own silence switch.

        Gated on ``interval_s > 0`` because ``progress.interval_s: 0`` is the
        documented "print no ``[PROGRESS]`` lines at all" switch — the same one
        :meth:`start_ticker` answers by returning ``None`` — and a roster that
        ignored it would break that contract by printing the run's whole model
        list into a log the operator asked to keep quiet.

        Guarded like :meth:`_tick`, and for a sharper reason than the ticker
        has: :meth:`seed` runs *before* the tasks are created, so anything
        raising out of here would lose the entire fan-out before a single model
        was dispatched — the worst possible trade for a line of narration.
        Returns what it emitted (``""`` when it stayed quiet), for the caller
        that wants to know without re-deriving the gate.
        """
        if self.interval_s <= 0:
            return ""
        try:
            line = self.render_roster()
            if line:
                _emit(line)
        except Exception as exc:  # noqa: BLE001 - see the docstring
            _warn_once(self._warned, "roster", f"progress roster failed ({exc})")
            return ""
        return line

    # -- writing ----------------------------------------------------------

    def _write(self) -> None:
        """Push the whole map and both counters into ``progress``.

        Whole, every time: ``update_status`` merges ``progress`` one level deep,
        so ``models`` is a single key and a patch carrying one entry would drop
        the other seven. ``report_progress`` picks the door — the detached
        worker's handle, or ``update_progress`` straight through on a foreground
        run — and both end inside ``checkpoint_lock``.

        Never raises. The status file is observability: an unwritable checkpoint
        must not take down a fan-out that is otherwise working, and the layers
        below already treat their writes as best-effort. The first failure says
        so once on stderr; the rest stay quiet rather than printing a line per
        transition for a condition that will not have changed.
        """
        done, succeeded, total = self.counts()
        try:
            from . import detach

            detach.report_progress(
                self.phase_dir,
                models=self.snapshot(),
                models_done=done,
                models_succeeded=succeeded,
                models_total=total,
                # Through `_seconds` for the same reason a budget is: the field
                # is read by humans and diffed by the golden tests, and the
                # cadence is a configured round number. It was written raw, so a
                # `30` in `providers.yaml` reached the file as `30.0` while
                # `timeout_s: 1800` beside it stayed an int (F5, 2026-09-20).
                interval_s=_seconds(self.interval_s),
            )
        except Exception as exc:  # noqa: BLE001 - see the docstring
            _warn_once(
                self._warned,
                "write",
                f"progress write failed ({exc}); continuing without it",
            )

    # -- the ticker -------------------------------------------------------

    def start_ticker(self) -> Optional[asyncio.Task]:
        """Start the line-per-interval task, or return ``None`` at ``interval_s: 0``.

        Created alongside the ``gather`` and cancelled in the fan-out's
        ``finally``. ``0`` is the documented disable form and costs a reader
        nothing: the status file still gets every event-driven transition and
        every elapsed and wait figure is computed from ``dispatched_at`` /
        ``started_at`` at read time, so silencing the ticker silences the *log*
        and nothing else.
        """
        if self.interval_s <= 0:
            return None
        if self._ticker is not None and not self._ticker.done():
            return self._ticker
        self._ticker = asyncio.ensure_future(self._tick_forever())
        return self._ticker

    async def stop_ticker(self) -> None:
        """Cancel the ticker **and await it** before the caller prints anything.

        Awaiting is the point, not politeness: the fan-out's per-model summary
        follows immediately, and a ticker merely cancelled could still emit one
        more line into the middle of it — or, worse, land a write after the
        sweep and resurrect a ``running`` entry the sweep had just retired.
        Idempotent, so the ``finally`` can call it on a path that already did.
        """
        task = self._ticker
        self._ticker = None
        if task is None:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            # Whose cancellation was it? Not a question `task.cancelled()` can
            # answer: we called `task.cancel()` one line up, so it is `True` in
            # *both* of the cases the check used to claim to tell apart, and a
            # sibling cancelling this caller mid-`await` had its cancellation
            # swallowed — the fan-out then walked on into grouping as if nothing
            # had happened, which is the exact failure the check was written to
            # prevent (F2, 2026-09-20). The question is about *this* task, so ask
            # this task: `cancelling()` counts the cancel requests outstanding
            # against it.
            if _caller_is_being_cancelled():
                raise
        except Exception:  # noqa: BLE001 - the ticker never fails a fan-out
            pass

    async def _tick_forever(self) -> None:
        """Print one line per interval; write nothing until teardown.

        The interval body is print-only — every row's elapsed and wait is
        computed from its stamps — so this task adds no contender on
        ``checkpoint_lock`` and no stale ``elapsed_s`` cache to the file.

        Its ``finally`` sweeps, and what that covers is **asyncio shutdown's
        cancel-all**: a second Ctrl-C, or anything else that cancels every task
        on the loop at once, reaches this task directly rather than through the
        fan-out's teardown. The first Ctrl-C is not that case — under
        ``asyncio.run``, 3.11's ``Runner._on_sigint`` cancels the *main* task, so
        the fan-out's own ``finally`` runs, calls :meth:`stop_ticker`, and this
        sweep is reached *through* it. Nor is ``--abort``, which reaches no
        Python here at all (``os._exit``); :func:`retire_live_entries`, called
        from ``RunHandle.finish``, is what closes the map out there.

        A final line is emitted after that sweep so the log's last ``[PROGRESS]``
        states the run's real totals (``8/8 done (7 ok, 1 failed)``) rather than
        whatever the last interval happened to catch.
        """
        try:
            while True:
                await _tick_sleep(self.interval_s)
                self._tick()
        finally:
            self.sweep()
            self._tick()

    def _tick(self) -> None:
        """One line, swallowing anything it raises.

        The ticker is its own task, so an exception here would surface only at
        the ``await`` in the fan-out's teardown and would take down a run that
        had already succeeded — matching ``update_status``'s best-effort
        contract, which falls back once and then passes rather than propagating.
        """
        try:
            _emit(self.render_line())
        except Exception as exc:  # noqa: BLE001 - see the docstring
            _warn_once(self._warned, "line", f"progress line failed ({exc})")


# ---------------------------------------------------------------------------
# The phase-scoped second ticker
# ---------------------------------------------------------------------------


class PhaseProgress:
    """The ticker for the part of a phase that is not the fan-out.

    ``run_models_concurrent`` returns the moment the last slot does, and the
    phase then keeps working for minutes: grouping, validation-batch
    preparation, and on the lanes that validate in-process the whole validation
    dispatch and merge — plus a ``--reaggregate`` pass, which has no fan-out at
    all. The fan-out's ticker cannot cover that window, because lifetime rule 1
    requires it to die *before* the per-model summary is printed. So the caller
    starts this one after that, and cancels *and awaits* it in a ``finally``
    when the phase writes its terminal ``progress.step`` — of which there are
    two: ``complete``, and the host-driven ``validation_pending`` early return,
    where the process exits and the agent's own subagents take over.

    It has no per-model map. Each tick re-reads ``{phase}/.status.json`` and
    renders the step, the in-process elapsed since it started, and whatever
    counters the current step already publishes::

        [PROGRESS] step: validation | 2m30s | subagents 5/8 done (5 ok)

    Those counters are **read**, never recomputed into a second key:
    ``subagent_executor._mirror_status`` already writes ``progress.subagents``
    (and ``write_batch_scheduler._mirror_status`` ``write_subagents``) on every
    outcome, straight through ``update_status``, so they reach a foreground
    checkpoint today. A ``progress.validation`` beside them would be the
    two-writers-for-one-fact failure the plan forbids.

    It prints and does not write, which is also what keeps the fan-out's
    terminal map frozen exactly as the sweep left it: a table rendered while
    validation runs shows each model's real duration rather than a clock that
    kept ticking after the model finished.
    """

    #: The executor mirrors this reads, in render order. The label is the *key*,
    #: not the mirror's ``kind``: the step clause already names the work
    #: ("step: validation"), so repeating it as "validation 5/8" reads as a
    #: second, unrelated quantity.
    MIRROR_KEYS: Tuple[str, ...] = ("subagents", "write_subagents")

    def __init__(
        self,
        phase_dir: Union[str, Any],
        *,
        interval_s: Optional[float] = None,
        anchor: Optional[Union[str, Any]] = None,
    ) -> None:
        self.phase_dir = str(phase_dir)
        self.anchor = anchor
        if interval_s is None:
            from .provider_registry import get_progress_interval

            interval_s = get_progress_interval(anchor=anchor)
        self.interval_s = float(interval_s)
        self._origin = _monotonic()
        self._ticker: Optional[asyncio.Task] = None
        self._warned: set = set()
        #: Whether the teardown tick prints. Cleared by
        #: ``stop_ticker(final_line=False)`` — see there.
        self._final_line = True

    def elapsed_s(self) -> float:
        """Seconds since the ticker started. In-process on purpose.

        The window this narrates begins when the fan-out *returned*, and nothing
        in the checkpoint records that instant — ``progress.step`` changes at its
        own pace and a step that has not changed yet would date the clock wrong.
        """
        return max(0.0, _monotonic() - self._origin)

    def render_line(self) -> str:
        """``[PROGRESS] step: validation | 2m30s | subagents 5/8 done (5 ok)``."""
        from . import status_file

        progress = status_file.read_status(self.phase_dir).get("progress")
        if not isinstance(progress, Mapping):
            progress = {}
        step = progress.get("step") or "(none recorded)"
        parts = [
            f"{PROGRESS_PREFIX} step: {step}",
            format_elapsed(self.elapsed_s()),
        ]
        for key in self.MIRROR_KEYS:
            clause = _mirror_clause(key, progress.get(key))
            if clause:
                parts.append(clause)
        return one_line_ascii(" | ".join(parts))

    def start_ticker(self) -> Optional[asyncio.Task]:
        """Same API and same ``interval_s: 0`` silence as the fan-out's ticker."""
        if self.interval_s <= 0:
            return None
        if self._ticker is not None and not self._ticker.done():
            return self._ticker
        # Re-stamped here rather than only in __init__ so a tracker constructed
        # early (beside the fan-out's, say) does not report a head start.
        self._origin = _monotonic()
        self._ticker = asyncio.ensure_future(self._tick_forever())
        return self._ticker

    async def stop_ticker(self, *, final_line: bool = True) -> None:
        """Cancel and await, so the last line lands before the phase's report.

        ``final_line=False`` drops the teardown line, for an invocation that
        wrote no terminal ``progress.step`` of its own. The line reads the
        checkpoint, so without this a ``--reaggregate`` that refused (exit 3 on
        a changed snapshot) or returned having dispatched nothing re-printed
        the *previous* run's ending — measured 2026-09-25 as
        ``[PROGRESS] step: complete | subagents 16/16 done (16 ok)`` after a
        refusal — a completion this process never reached.
        """
        task = self._ticker
        self._ticker = None
        if task is None:
            return
        self._final_line = bool(final_line)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            # See `FanoutProgress.stop_ticker`: swallow our own cancellation,
            # re-raise the caller's — and ask the *caller* which it was, because
            # `task.cancelled()` is `True` either way once we have cancelled it.
            if _caller_is_being_cancelled():
                raise
        except Exception:  # noqa: BLE001 - the ticker never fails a phase
            pass

    async def _tick_forever(self) -> None:
        """One line per interval, and one at teardown carrying the terminal step.

        The teardown line is why the caller stops this *after* writing
        ``progress.step`` to its terminal value: the last ``[PROGRESS]`` in the
        log then reads ``step: complete`` rather than trailing off at whatever
        step the last interval caught.
        """
        try:
            while True:
                await _tick_sleep(self.interval_s)
                self._tick()
        finally:
            if self._final_line:
                self._tick()

    def _tick(self) -> None:
        """One line, swallowing anything it raises (see :meth:`FanoutProgress._tick`)."""
        try:
            _emit(self.render_line())
        except Exception as exc:  # noqa: BLE001 - observability must not fail a phase
            _warn_once(self._warned, "line", f"progress line failed ({exc})")


# ---------------------------------------------------------------------------
# Retiring a map whose process is about to stop running Python
# ---------------------------------------------------------------------------

#: Conditions :func:`retire_live_entries` has already reported (:func:`_warn_once`).
_RETIRE_WARNED: set = set()


def retire_live_entries(
    phase_dir: Union[str, Any],
    *,
    reason: str = CANCELLED_ERROR,
    now: Optional[float] = None,
) -> int:
    """Close out every still-live row of the map **on disk**. Returns how many.

    The sweep's counterpart for the one ending that runs no Python on its way
    out. ``status --abort`` signals the worker; ``RunHandle._on_signal`` records
    the terminal ``run`` record and calls ``os._exit(3)``, which runs no
    ``finally``, raises no ``CancelledError`` and gives neither the fan-out's
    sweep nor the ticker's teardown a chance to execute. Before this existed the
    checkpoint was left with ``run.state: aborted`` beside rows still reading
    ``running``/``staggering``/``queued`` and ``models_done`` frozen mid-count —
    a poll an hour later rendering ``codex:gpt-5.6-sol  running  30m00s/30m``
    under a run that had been over since (F1, 2026-09-20).

    So this is deliberately **not** a method on :class:`FanoutProgress` and it
    never looks for one: reaching a live tracker from a signal handler means
    touching an object the interrupted frame may be halfway through mutating,
    and a run may have any number of trackers (``full`` calls each phase in
    process) or none at all. The map is already on disk; the honest operation is
    a read-modify-write of it, under the same :func:`status_file.checkpoint_lock`
    the caller is already holding — reentrant, so nesting costs nothing and the
    ``run`` record and the map close out inside one critical section, which is
    what stops a poller catching the pair disagreeing.

    It applies :meth:`FanoutProgress._freeze`'s dispatch-origin rule, which is
    the rule all three close-out writers share (the third is
    ``review_orchestrator_base.flip_map_entries_to_done``): a row that
    dispatched freezes ``elapsed_s`` as ``now - dispatched_at`` and keeps its
    ``queued_s``; a row still waiting (``queued``/``staggering``) freezes
    ``elapsed_s: 0`` and ``queued_s`` as ``now - started_at``, because this
    runs at the real end of the run, so *now* is when that wait ended. Without
    the ``queued_s`` half, every row an abort retired would lose the wait the
    table exists to show. The figures come from the persisted wall stamps
    rather than from :func:`time.monotonic`, unlike ``_freeze``: the monotonic
    origins live in the tracker we are not allowed to touch, and the read-time
    rules (:func:`entry_elapsed_s`, clamped at the slot's own budget, and
    :func:`entry_queued_s`) are the ones every renderer would have applied to
    this row a moment earlier. A row with no ``dispatched_at`` in a running
    state (a map written before the key existed) keeps today's
    ``now - started_at`` and gains no ``queued_s``, since its wait was never
    recorded.

    Never raises, and returns ``0`` when nothing was live — so the file is not
    rewritten on the ordinary path, where the fan-out's own sweep has already
    retired everything and only the ``run`` record is left to write.
    """
    from . import status_file

    directory = str(phase_dir)
    reference = _wall_time() if now is None else float(now)
    try:
        with status_file.checkpoint_lock(directory):
            progress = status_file.read_status(directory).get("progress")
            if not isinstance(progress, Mapping):
                return 0
            models = progress.get("models")
            if not isinstance(models, Mapping) or not models:
                return 0
            stamp = _now_iso()
            retired: Dict[str, Any] = {}
            changed = 0
            for spec, entry in models.items():
                # A hand-edited or foreign entry is copied through untouched
                # rather than dropped: this is a close-out, not a validator, and
                # losing a row here would lose the only record of that model.
                if not isinstance(entry, Mapping):
                    retired[str(spec)] = entry
                    continue
                row = dict(entry)
                if row.get("state") in TERMINAL_STATES:
                    retired[str(spec)] = row
                    continue
                # Both read before `ended_at` is stamped, because the read-time
                # rules key on it.
                elapsed = entry_elapsed_s(row, reference)
                queued = entry_queued_s(row, reference)
                row["state"] = STATE_FAILED
                row["updated_at"] = stamp
                row["ended_at"] = stamp
                row["elapsed_s"] = (
                    _seconds(round(elapsed, 1)) if elapsed is not None else 0
                )
                if queued is not None:
                    row["queued_s"] = _seconds(round(queued, 1))
                row["error"] = str(reason)
                # Nothing produced this row, so it carries no source, and a
                # backoff it will never wake from is noise in the table.
                row["source"] = None
                row.pop("retry_after_s", None)
                retired[str(spec)] = row
                changed += 1
            if not changed:
                return 0
            rows = [e for e in retired.values() if isinstance(e, Mapping)]
            status_file.update_progress(directory, {
                "models": retired,
                # Recomputed, because the counters were frozen wherever the last
                # transition left them: an aborted 1/4 run really finished four
                # slots, three of them by being abandoned.
                "models_done": sum(
                    1 for e in rows if e.get("state") in TERMINAL_STATES
                ),
                "models_succeeded": sum(
                    1 for e in rows if e.get("state") == STATE_DONE
                ),
            })
            return changed
    except Exception as exc:  # noqa: BLE001 - a close-out never raises
        _warn_once(
            _RETIRE_WARNED,
            "retire",
            f"could not retire the per-model map in {directory} ({exc})",
        )
        return 0


def _mirror_clause(key: str, mirror: Any) -> Optional[str]:
    """``subagents 5/8 done (5 ok)`` from an executor mirror, or ``None``.

    Reads only what the mirror already carries: ``total`` is the batch's task
    count, ``counts`` the outcomes recorded so far (so their sum is "done"), and
    ``ok`` the successes. A mirror that records rows instead of a counts table
    (the write lane) falls back to its row count, and one with neither is
    rendered from ``ok`` alone rather than dropped — the alternative is a phase
    ticker that goes quiet exactly while a batch is in flight.
    """
    if not isinstance(mirror, Mapping):
        return None
    total = mirror.get("total")
    if isinstance(total, bool) or not isinstance(total, int):
        return None
    counts = mirror.get("counts") if isinstance(mirror.get("counts"), Mapping) else {}
    ok = mirror.get("ok")
    if isinstance(ok, bool) or not isinstance(ok, int):
        ok = counts.get("ok") if isinstance(counts.get("ok"), int) else 0
    if counts:
        finished = sum(v for v in counts.values() if isinstance(v, int) and not isinstance(v, bool))
    elif isinstance(mirror.get("tasks"), list):
        finished = len(mirror["tasks"])
    else:
        finished = ok
    return f"{key} {finished}/{total} done ({ok} ok)"
