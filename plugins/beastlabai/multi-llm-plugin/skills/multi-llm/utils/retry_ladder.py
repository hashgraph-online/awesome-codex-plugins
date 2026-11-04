"""The one retry policy both invocation lanes obey (§7.1.b, §7.5).

Two lanes retry dispatches and until now they disagreed about everything that
matters. Lane B (``subagent_executor._dispatch_task``) had the D3k rung ladder,
a monotonic per-task deadline and two separate retry counters; Lane A
(``review_orchestrator_base.run_single_model``) had ``'429' in str(error)`` and
a *recursive self-call that handed every attempt a fresh full timeout*, so a
claude-code slot at ``default_timeout: 1800`` could run 4 × 1800 s + 35 s of
backoff ≈ **2 h** against a configured ceiling of 1800 s.

**What is shared is the policy, not the loop.** Lane B's loop is synchronous and
drives a blocking capture; Lane A's ``run_single_model`` is a coroutine awaited
inside ``asyncio.gather`` under two semaphores. Importing Lane B's loop into the
coroutine would block the event loop and serialize the whole fan-out, and hiding
it behind ``to_thread`` would put an already-async invocation behind a thread
boundary for no gain. So this module holds a **pure** decision object — no I/O,
no sleeping, no clock beyond an injected ``now`` — and each lane keeps its own
three-line loop:

    ladder = RetryLadder(timeout=resolved_timeout,
                         retries=get_subagent_retries(anchor=anchor),
                         envelope=provider.internal_retries,
                         now=time.monotonic)
    while (slice_s := ladder.next_attempt()) is not None:
        status = await dispatch(..., timeout=slice_s)   # Lane A awaits
        action = ladder.record(status)                  # Lane B blocks
        if action.delay:
            await asyncio.sleep(action.delay)           # Lane B: napper(delay)

``next_attempt()`` is where §7.5 rules 1, 3 and 4 live; ``record()`` is where
rule 2's two counters and rule 6's composition tests live, and it takes every
grant (a retry, a backoff, the re-ask below) against the same rules-3-and-4
admission test, so a granted attempt is one ``next_attempt()`` admits and a
refused one comes back as the attempt's own stop with ``Action.note`` saying
why. The only lane-specific lines are the dispatch call and the sleep.

Rule 7 is this module's own, not §7.5's (2026-10-05): a caller may grant
``schema_repairs`` — at most that many re-asks after a ``schema_invalid`` attempt,
each returned as ``Action(retry=True, repair=True)`` and charged to the same
deadline. The re-ask is a different request (the original prompt plus the
validator's errors), so it is not the identical retry rung 6 forbids; what the
caller sends is the caller's business, and the default of ``0`` leaves rung 6
exactly as terminal as it was. Lane B grants one, for ``task_generation`` and
the four write kinds (``subagent_executor.SCHEMA_REPAIRS_BY_KIND``; a write
kind's re-ask restates the batch's report and must move no file).

Rule 8 is this module's own too (fix round 8): ``record(..., repeatable=False)``
is the caller's word that the identical dispatch must not be sent again — a write
attempt that already changed files, which a retry would apply a second time on
top of its own edits. A transport or rate-limit status then earns no retry and no
backoff: the slot stops (``not_repeatable``), unless the attempt is
``repairable`` and the rule-7 allowance has a re-ask left, which is a different
request (the runner restates its report and edits nothing).

Rule 9 is this module's own as well (fix round 14): a caller may grant
``resends`` — at most that many re-sends of a write batch whose reply said
``applied`` while not one byte moved (``record_resend()``, returned as
``Action(retry=True, resend=True)``). Rule 8 forbids re-sending an attempt that
moved bytes; this one moved none, so the batch can be sent again, told that its
previous attempt changed no file. It spends neither the transport budget nor
the rule-7 allowance, and takes the same admission test as every other grant
(OpenCode racing run 5: T016 said ``applied``, named ``index.html``, and
``index.html`` was byte-for-byte unchanged).

The status vocabulary and the D3k rung table live here rather than in
``subagent_executor`` because the ladder is now their only consumer;
``subagent_executor`` re-exports every name it used to define, so nothing that
imported them from there has to change.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Optional, Protocol


# ---------------------------------------------------------------------------
# Status vocabulary and the D3k rung table (moved here from subagent_executor,
# which re-exports all of it).
# ---------------------------------------------------------------------------

STATUS_OK = "ok"
STATUS_TIMEOUT = "timeout"
STATUS_RATE_LIMITED = "rate_limited"
STATUS_RUNNER_ERROR = "runner_error"
STATUS_UNPARSEABLE = "unparseable_result"
STATUS_SCHEMA_INVALID = "schema_invalid"
STATUS_REJECTED = "rejected"
STATUS_SPAWN_FAILED = "spawn_failed"
STATUS_AUTH_FAILED = "auth_failed"
#: The runner rejected the model id itself (D4). Deliberately the same string
#: as the classifier's ``CATEGORY_INVALID_MODEL`` — an alias for a word already
#: in the vocabulary, not a second spelling — so the category reaches
#: :meth:`RetryLadder.record` under its own name on both lanes. A rejected id is
#: a property of the *spec*, not of the turn: the fix is a config edit, never a
#: retry, and every sibling resolving the same spec fails identically.
STATUS_INVALID_MODEL = "invalid_model"
#: The runner's own OS sandbox could not start (D6) — bubblewrap on a stock
#: Ubuntu 24.04, where ``kernel.apparmor_restrict_unprivileged_userns=1``
#: denies it the user namespace it needs. The same string as the classifier's
#: ``CATEGORY_SANDBOX_UNAVAILABLE`` on D4's reasoning: a property of the
#: *machine*, not of the turn, so every sibling on that runner fails
#: identically and a retry never changes it. The ways out are a non-Codex
#: runner (the refusal leads with it), the plugin's Landlock jail where the
#: kernel has one, or the system-level AppArmor/sysctl repair ``multi_llm.py
#: doctor`` prints, which needs sudo (plan codex-sandbox-unavailable §7 step 4,
#: reworded 2026-09-30: that repair is not "the fix" on a host that forbids it).
STATUS_SANDBOX_UNAVAILABLE = "sandbox_unavailable"
#: Not a dispatch outcome: a task with no result file at all (an orphan from a
#: run killed mid-batch). Defined by artifacts, never by memory (D3i).
STATUS_INCOMPLETE = "incomplete"
#: Terminal, and deliberately **not** retryable: re-sending an unchanged
#: oversized prompt is the one retry guaranteed to fail identically (§7.6(a)).
#: Splitting is a feature with its own design, not a line in a classifier table.
STATUS_CONTEXT_LENGTH_EXCEEDED = "context_length_exceeded"
#: Not a dispatch outcome either: rule 4 refused to *start* an attempt because
#: what is left of the deadline cannot hold one worst-case attempt of this
#: adapter's declared vendor envelope.
STATUS_BUDGET_EXHAUSTED = "budget_exhausted"

#: ``salvage`` only: the subagent read the raw output it was handed and reported
#: back that it holds no recoverable document
#: (``{"salvage_failed": true, "reason": ...}``, ``build_salvage_prompt``'s
#: fallback). Terminal, and in **none** of the three policy sets below: the
#: dispatch worked, the answer is a definite negative, and re-sending an
#: unchanged raw output to an unchanged prompt asks a question already answered.
#:
#: Deliberately absent from ``RUNG_BY_STATUS`` too. A rung is a position on the
#: *transport* failure ladder, and nothing about this dispatch failed — the child
#: spawned, replied and was understood. What is being recorded is the content of
#: the reply, so a rung here would be a category error in the same way it is for
#: ``budget_exhausted`` and the two D3g verification failures.
STATUS_SALVAGE_UNRECOVERABLE = "salvage_unrecoverable"

#: Not a failure: the attempt whose readable write report left some of the
#: batch's items out of both ``ids`` and ``declined``, which drew the report
#: re-ask (:data:`REPAIR_INCOMPLETE_REPORT`). Fix round 19 (review of round
#: 18, #4): it was recorded ``schema_invalid`` with a failure capture under
#: ``failed/``, so a batch that then completed read as a schema failure in
#: its attempt table. On no rung and in no policy set: nothing about the
#: dispatch failed, and the re-ask quotes the reply in its own prompt file.
STATUS_INCOMPLETE_REPORT = "incomplete_report"

#: The D3k ladder, first match wins. Every dispatch failure lands on exactly one
#: rung, and the status is what ``subagent_batch_report.json`` records verbatim.
RUNG_BY_STATUS = {
    STATUS_SPAWN_FAILED: 1,
    STATUS_AUTH_FAILED: 1,
    STATUS_INVALID_MODEL: 1,
    STATUS_SANDBOX_UNAVAILABLE: 1,
    STATUS_TIMEOUT: 2,
    STATUS_RATE_LIMITED: 3,
    STATUS_RUNNER_ERROR: 4,
    STATUS_UNPARSEABLE: 5,
    STATUS_SCHEMA_INVALID: 6,
    STATUS_REJECTED: 7,
}

#: Statuses that consume ``driver.subagent_retries``.
RETRYABLE_STATUSES = frozenset({STATUS_TIMEOUT, STATUS_RUNNER_ERROR, STATUS_UNPARSEABLE})

#: Rate limiting is retried with backoff+jitter and does **not** consume the
#: retry budget (D3i) — it is not a transport failure.
BACKOFF_STATUSES = frozenset({STATUS_RATE_LIMITED})

#: Rungs that fail the whole batch immediately: every sibling would fail
#: identically, so continuing would only burn the retry budget N times.
#: ``invalid_model`` qualifies because the failure is a property of the spec
#: (D4): a sibling on the *same* spec cannot do anything but fail again, and a
#: sibling on a different spec is settled by the dispatch gate, not predicted.
#: ``sandbox_unavailable`` qualifies because the failure is a property of the
#: machine (D6): bubblewrap cannot start for any sibling either.
FATAL_STATUSES = frozenset({
    STATUS_SPAWN_FAILED, STATUS_AUTH_FAILED, STATUS_INVALID_MODEL,
    STATUS_SANDBOX_UNAVAILABLE,
})

#: Statuses no re-run of the same phase can change: the fatal rung-1 set (a
#: property of the spec or the machine), ``rejected`` (rung 7, a configuration
#: refusal "never retried, because re-running produces the same" — e.g. a CLI
#: that refuses the schema file before any request),
#: ``context_length_exceeded`` (an unchanged oversized prompt fails
#: identically) and ``budget_exhausted`` (rule 4 refused the slot before
#: anything was spawned, because the configured timeout cannot hold one declared
#: worst-case attempt — a config refusal whose own reason says "Raise the slot
#: timeout", and an unchanged re-run is refused the same way). Read by
#: ``next_phase.resume_command``: a phase whose failed tasks all ended elsewhere
#: is handed back a re-invoke the user can type, and one with any of these gets
#: none, because the command would repeat the stop.
RERUN_FUTILE_STATUSES = FATAL_STATUSES | frozenset({
    STATUS_REJECTED, STATUS_CONTEXT_LENGTH_EXCEEDED, STATUS_BUDGET_EXHAUSTED,
})

#: The smallest slice of the per-slot budget worth *starting* an attempt with
#: (D3i). The timeout is the slot's total wall-clock budget, so a retry gets what
#: is left of it — and a runner handed under a second would spend it on process
#: start-up and be killed for the same reason the previous attempt was, having
#: added only a spawn and a kill to the batch.
MIN_ATTEMPT_BUDGET_S = 1.0

#: §7.5 rule 2: at most three rate-limit backoffs per slot, and they do not
#: consume the transport budget.
MAX_RATE_LIMIT_BACKOFFS = 3


def backoff_delay(attempt: int, jitter: Callable[[], float] = random.random) -> float:
    """Exponential backoff **plus jitter** for rate-limit rung 3.

    "Equal jitter": half the exponential step is deterministic and half is
    random, so a retry is never immediate and never longer than the step itself.
    Without the random half, the N sibling slots a shared provider throttled at
    the same moment re-attempt in lockstep and re-trip the same limit together,
    which is the failure the backoff exists to avoid.

    Pure: the caller supplies the randomness and applies any test fast-backoff
    hook to the result, so this module keeps no import of either.
    """
    step = min(2.0 ** attempt, 30.0)
    half = step / 2.0
    return half + jitter() * half


class InternalRetryEnvelopeLike(Protocol):
    """What the ladder reads off an adapter's ``internal_retries`` (§7.6(b)).

    Structural, not an import: the declaration lives on ``LLMProvider`` beside
    the adapters that populate it, and the ladder must stay free of provider
    imports to remain pure.
    """

    max_requests: Optional[int]
    max_wall_s: Optional[float]
    retries_rate_limit: bool


#: Why the ladder stopped. ``None`` while it is still willing to dispatch.
STOP_EXHAUSTED_ATTEMPTS = "attempts_exhausted"
STOP_BUDGET = "budget_exhausted"
STOP_DEADLINE = "deadline_reached"
STOP_FATAL = "fatal"
STOP_TERMINAL = "terminal_status"
STOP_VENDOR_ALREADY_RETRIED = "vendor_already_retried_rate_limit"
#: Rule 8: the caller said the identical dispatch must not be re-sent.
STOP_NOT_REPEATABLE = "not_repeatable"

#: The reason an :class:`Action` carries when it grants the schema-repair
#: re-ask, and the value a lane records on the attempt that re-ask produces.
REPAIR_SCHEMA_INVALID = "schema_invalid"

#: Rule 7's second form (fix round 18): the report re-ask granted to a write
#: report that reads but leaves some of the batch's items out of both ``ids``
#: and ``declined``, and the value a lane records on the attempt it produces.
#: It spends the same allowance as :data:`REPAIR_SCHEMA_INVALID`: one re-ask
#: per dispatch, whichever way the report fell short.
REPAIR_INCOMPLETE_REPORT = "incomplete_report"

#: Rule 9's word: the reason an :class:`Action` carries when it grants the
#: re-send of a write batch whose reply said ``applied`` while no byte moved,
#: and the value a lane records on the attempt that re-send produces.
RESEND_NOTHING_CHANGED = "nothing_changed"


@dataclass(frozen=True)
class Action:
    """What the caller does after reporting an attempt's status.

    ``delay`` is the only thing the caller *performs*; everything else is
    bookkeeping the ladder has already done. ``retry`` is False exactly when
    ``next_attempt()`` will return ``None``.
    """

    retry: bool
    delay: float = 0.0
    reason: Optional[str] = None
    #: The next attempt is the one schema-repair re-ask (rule 7 below): the
    #: caller re-sends the *same* runner its original prompt plus the
    #: validator's errors, rather than the identical dispatch.
    repair: bool = False
    #: Set when the status earned a retry, a backoff or the re-ask and the
    #: ladder refused it for want of budget (rule 3 or rule 4): the
    #: parenthetical a lane appends to the attempt's own error, so the record
    #: says why the slot stopped there instead of naming only the failure.
    note: Optional[str] = None
    #: The next attempt is rule 9's re-send: the batch's own prompt again,
    #: told that the previous attempt said ``applied`` and changed no file.
    resend: bool = False


class RetryLadder:
    """One slot's retry policy: a deadline, two counters, and an admission test.

    Pure by construction — it never sleeps, never spawns and never reads a
    clock other than the ``now`` it was handed. That is what lets Lane A's
    ``async`` loop and Lane B's blocking loop share it.
    """

    def __init__(
        self,
        timeout: float,
        retries: int,
        envelope: Optional[InternalRetryEnvelopeLike] = None,
        now: Callable[[], float] = None,
        jitter: Callable[[], float] = random.random,
        max_rate_limit_backoffs: int = MAX_RATE_LIMIT_BACKOFFS,
        min_attempt_budget_s: float = MIN_ATTEMPT_BUDGET_S,
        schema_repairs: int = 0,
        resends: int = 0,
    ) -> None:
        if now is None:  # pragma: no cover - the default is the real clock
            import time

            now = time.monotonic
        self._now = now
        self._jitter = jitter
        self.timeout = float(timeout)
        # §7.5 rule 1: ONE deadline per slot, taken once. Every attempt is
        # spawned with what is LEFT of it, never with a fresh copy — which is
        # precisely what Lane A's recursion did.
        self._started_at = now()
        self._deadline = self._started_at + self.timeout
        self.envelope = envelope
        self._min_attempt_budget_s = min_attempt_budget_s
        self._max_rate_limit_backoffs = max_rate_limit_backoffs

        # §7.5 rule 2: two SEPARATE counters. Transport-shaped failures consume
        # `driver.subagent_retries`; rate limiting backs off without consuming
        # it. Lane A's `retry_count < 3` recursion is replaced by these, never
        # added to them.
        self._transport_retries_left = int(retries)
        self._rate_limit_attempts = 0
        # Rule 7: a THIRD counter, zero unless the caller grants it. Rung 6 is
        # "a deterministic disagreement a retry would only launder" when the
        # retry is the identical dispatch; a re-ask that hands the runner the
        # validator's own errors is a different request. Granted per kind by the
        # lane (Lane B: `task_generation` and the write kinds), never by the ladder, and it
        # spends neither the transport budget nor the rate-limit allowance.
        self._schema_repairs_left = max(0, int(schema_repairs))
        self._schema_repairs_used = 0
        # Rule 9: a FOURTH counter, zero unless the caller grants it (Lane B:
        # the write kinds, `subagent_executor.RESENDS_BY_KIND`).
        self._resends_left = max(0, int(resends))
        self._resends_used = 0

        self.attempt_index = 0
        self.stop_reason: Optional[str] = None
        self._last_status: Optional[str] = None

    # -- clock ------------------------------------------------------------

    def elapsed(self) -> float:
        return self._now() - self._started_at

    def remaining(self) -> float:
        return self._deadline - self._now()

    # -- rules 1, 3 and 4 -------------------------------------------------

    def next_attempt(self) -> Optional[float]:
        """The slice the next attempt may run for, or ``None`` to stop.

        ``None`` always leaves :attr:`stop_reason` set, so a caller never has to
        infer *why* a slot ended.
        """
        if self.stop_reason is not None:
            return None

        left = self.remaining()
        refusal = self._admission_refusal(left=left)
        if refusal is not None:
            # Rule 3 before the first attempt is the slot's own ceiling being
            # under the minimum: nothing was spawned, so it is the budget's.
            self.stop_reason = (
                STOP_BUDGET if not self.attempt_index else refusal
            )
            return None

        self.attempt_index += 1
        return left

    def _declared_wall(self) -> Optional[float]:
        return getattr(self.envelope, "max_wall_s", None) if self.envelope else None

    def _admission_refusal(
        self, after: float = 0.0, left: Optional[float] = None
    ) -> Optional[str]:
        """Which rule would refuse an attempt started *after* seconds from now.

        ``None`` when it would be admitted. The one admission test, read by
        :meth:`next_attempt` and by every grant in :meth:`record` — a grant
        decided on rule 3 alone was taken back by rule 4 at the next start,
        and Lane B recorded a slot whose attempt 1 had run as
        ``budget_exhausted``, "Nothing was dispatched" (fix round 6).
        """
        left = (self.remaining() if left is None else left) - after
        # Rule 3: no attempt starts with less than MIN_ATTEMPT_BUDGET_S. A
        # runner handed a sliver spends it on process start-up and is killed for
        # the same reason the previous attempt was.
        if left < self._min_attempt_budget_s:
            return STOP_DEADLINE
        # Rule 4: vendor-internal retries are DECLARED, not discovered. If the
        # adapter's own worst-case wall for one attempt does not fit in what is
        # left, fail as `budget_exhausted` rather than spawn a child only to
        # kill it mid-retry. Strictly a pre-dispatch admission test — never a
        # second debit, because the deadline is already charged the awaited
        # subprocess's whole duration (rule 6(a)).
        bound = self._declared_wall()
        if bound is not None and left < bound:
            return STOP_BUDGET
        return None

    def _refusal_text(self, refusal: str, after: float = 0.0) -> str:
        """Why :meth:`_admission_refusal` said *refusal*, in one clause."""
        if refusal == STOP_BUDGET:
            left = max(0.0, self.remaining() - after)
            when = (
                f"would be left after the {after:.1f}s backoff" if after else "is left"
            )
            return (
                f"only {left:.1f}s of the slot's {self.timeout}s budget {when}, "
                f"under the {self._declared_wall():g}s one dispatch of this "
                f"runner declares it may take (§7.5 rule 4)"
            )
        return f"the per-slot wall-clock budget of {self.timeout}s is exhausted"

    # -- rule 2 and rule 6 ------------------------------------------------

    def record(
        self, status: str, *, repairable: bool = True, repeatable: bool = True
    ) -> Action:
        """Report an attempt's classified status; get the next move.

        ``repairable`` is the caller's word on whether a ``schema_invalid``
        attempt left anything a re-ask could quote (rule 7): ``False`` when no
        document came back at all — a CLI whose own structured-output budget ran
        out — keeps rung 6 terminal even inside a granted allowance.

        ``repeatable`` (rule 8) is the caller's word on whether the identical
        dispatch may be sent again. ``False`` — a write attempt that already
        changed files — turns a transport retry or a rate-limit backoff into a
        stop, or into the rule-7 re-ask when the attempt is ``repairable`` and
        the allowance has one left.
        """
        self._last_status = status

        if status == STATUS_OK:
            self.stop_reason = STOP_TERMINAL
            return Action(retry=False, reason="ok")

        if status in FATAL_STATUSES:
            # Every sibling would fail identically; continuing only burns the
            # retry budget N times.
            self.stop_reason = STOP_FATAL
            return Action(retry=False, reason=f"{status} is fatal to the batch")

        if not repeatable and (
            status in BACKOFF_STATUSES or status in RETRYABLE_STATUSES
        ):
            # Rule 8: never the identical dispatch again. The re-ask is a
            # different request, so it stays available inside the allowance.
            if repairable and self._schema_repairs_left > 0:
                return self._record_schema_repair(status)
            self.stop_reason = STOP_NOT_REPEATABLE
            return Action(
                retry=False,
                reason=(
                    f"{status}, and the attempt changed files, so the same "
                    f"dispatch is not sent again"
                ),
            )

        if status in BACKOFF_STATUSES:
            return self._record_rate_limited()

        if status in RETRYABLE_STATUSES:
            return self._record_transport(status)

        if (
            status == STATUS_SCHEMA_INVALID
            and repairable
            and self._schema_repairs_left > 0
        ):
            return self._record_schema_repair()

        # Rungs 6 and 7, and the terminal §7.6(a) status: never retried — rung 6
        # only once a caller's schema-repair allowance (rule 7) is spent or was
        # never granted.
        self.stop_reason = STOP_TERMINAL
        return Action(retry=False, reason=f"{status} is never retried")

    def _record_schema_repair(self, status: str = STATUS_SCHEMA_INVALID) -> Action:
        # Rules 3 and 4 again: the re-ask runs inside the SAME deadline as every
        # other attempt of this slot, never on a fresh copy of it, and is only
        # granted when `next_attempt()` will admit it.
        refusal = self._admission_refusal()
        if refusal is not None:
            self.stop_reason = refusal
            note = f"no schema-repair re-ask: {self._refusal_text(refusal)}"
            return Action(retry=False, reason=f"{status} ({note})", note=note)
        self._schema_repairs_left -= 1
        self._schema_repairs_used += 1
        return Action(retry=True, reason=REPAIR_SCHEMA_INVALID, repair=True)

    def record_resend(self) -> Action:
        """Rule 9: may the write batch whose reply said ``applied`` while no
        byte moved be sent once more?

        The attempt itself ran and its reply was read, so this is not a
        status the rung table knows: the caller asks only after it measured
        that nothing moved (rule 8's condition for a safe re-send). Granted
        at most ``resends`` times, inside the same deadline and under the
        same admission test as every other grant; a refusal for want of
        budget carries the ``note`` the caller records with the outcome.
        """
        if self._resends_left <= 0:
            return Action(retry=False, reason="the re-send was already spent")
        refusal = self._admission_refusal()
        if refusal is not None:
            note = f"no re-send: {self._refusal_text(refusal)}"
            return Action(retry=False, reason=note, note=note)
        self._resends_left -= 1
        self._resends_used += 1
        return Action(retry=True, reason=RESEND_NOTHING_CHANGED, resend=True)

    def record_report_reask(self) -> Action:
        """Rule 7, for a write report that reads but does not account for
        every item of its batch (fix round 18): may the runner be asked once
        to restate it?

        Like :meth:`record_resend`, asked for an attempt whose reply was read,
        so no status is recorded and no stop is decided here: a refusal
        leaves the reply to be classified as it stands. It spends the
        schema-repair allowance, never a counter of its own — a dispatch gets
        one report re-ask, whichever way its report fell short — inside the
        same deadline and admission test as every other grant.
        """
        if self._schema_repairs_left <= 0:
            return Action(retry=False, reason="the report re-ask was already spent")
        refusal = self._admission_refusal()
        if refusal is not None:
            note = f"no report re-ask: {self._refusal_text(refusal)}"
            return Action(retry=False, reason=note, note=note)
        self._schema_repairs_left -= 1
        self._schema_repairs_used += 1
        return Action(retry=True, reason=REPAIR_INCOMPLETE_REPORT, repair=True)

    def _record_rate_limited(self) -> Action:
        # Rule 6(b): a rate-limit rung may not re-issue an identical dispatch
        # the vendor already exhausted. If the adapter declares it retries 429s
        # internally (claude-code), an identical same-rung re-dispatch repeats a
        # chain that already ran `max_requests` times against the same upstream,
        # at the same price, for the same verdict — ≤ 3 backoffs would turn 4
        # requests into 20. A *rung-down* stays legitimate, because it changes
        # the request the upstream prices; that is the caller's move, not ours.
        if getattr(self.envelope, "retries_rate_limit", False):
            self.stop_reason = STOP_VENDOR_ALREADY_RETRIED
            requests = getattr(self.envelope, "max_requests", None)
            request_bound = (
                f"{requests} requests per dispatch"
                if requests is not None
                else "no finite request bound is known"
            )
            return Action(
                retry=False,
                reason=(
                    "rate_limited, and this adapter declares it already retries "
                    f"rate limits internally ({request_bound}); "
                    "an identical re-dispatch would repeat a chain that already ran"
                ),
            )

        self._rate_limit_attempts += 1
        if self._rate_limit_attempts > self._max_rate_limit_backoffs:
            self.stop_reason = STOP_EXHAUSTED_ATTEMPTS
            return Action(
                retry=False,
                reason=(
                    f"rate_limited after {self._max_rate_limit_backoffs} backoffs"
                ),
            )

        delay = backoff_delay(self._rate_limit_attempts, self._jitter)
        # Rules 3 and 4 again, for the sleep: the backoff is charged to the SAME
        # deadline as the spawns. Waiting past the ceiling only to dispatch one
        # more attempt spends the budget twice, and a slice the next attempt
        # could not use — or that rule 4 would refuse — is not worth waiting for.
        refusal = self._admission_refusal(after=delay)
        if refusal is not None:
            self.stop_reason = refusal
            if refusal == STOP_DEADLINE:
                note = "no backoff retry: the backoff would not fit in the budget"
                reason = "rate_limited, and the backoff would not fit in the budget"
            else:
                note = f"no backoff retry: {self._refusal_text(refusal, after=delay)}"
                reason = f"rate_limited ({note})"
            return Action(retry=False, reason=reason, note=note)
        return Action(retry=True, delay=delay, reason="rate_limited")

    def _record_transport(self, status: str) -> Action:
        if self._transport_retries_left <= 0:
            self.stop_reason = STOP_EXHAUSTED_ATTEMPTS
            return Action(retry=False, reason=f"{status}, retry budget spent")
        refusal = self._admission_refusal()
        if refusal is not None:
            # The retry budget is not the only budget: a retry runs inside the
            # slot's remaining wall clock, never on a fresh copy of it, and only
            # when rule 4 would admit it there.
            unused = self._transport_retries_left
            self.stop_reason = refusal
            note = (
                f"no retry: {self._refusal_text(refusal)}, {unused} retr"
                f"{'y' if unused == 1 else 'ies'} unused"
            )
            return Action(retry=False, reason=f"{status} ({note})", note=note)
        self._transport_retries_left -= 1
        return Action(retry=True, reason=status)

    # -- introspection ----------------------------------------------------

    @property
    def transport_retries_left(self) -> int:
        return self._transport_retries_left

    @property
    def rate_limit_attempts(self) -> int:
        return self._rate_limit_attempts

    @property
    def schema_repairs_used(self) -> int:
        """Schema-repair re-asks granted so far (rule 7)."""
        return self._schema_repairs_used

    @property
    def schema_repairs_left(self) -> int:
        """Schema-repair re-asks the allowance still holds (rule 7)."""
        return self._schema_repairs_left

    @property
    def resends_left(self) -> int:
        """Rule 9's re-sends the allowance still holds."""
        return self._resends_left

    @property
    def resends_used(self) -> int:
        """Rule 9's re-sends granted so far."""
        return self._resends_used

    @property
    def spawns(self) -> int:
        """Total dispatches admitted so far — the ≤ 5 of §7.5 rule 2."""
        return self.attempt_index


def budget_exhausted_reason(
    ladder: "RetryLadder", target: str, timeout: float
) -> str:
    """The one sentence a rule-4 refusal is recorded with, for **both** lanes.

    It has to say three things, because a slot that spawned nothing is the one
    failure with no captured streams to read: what the harness gave the slot,
    what the adapter *declared* one worst-case attempt costs, and that the
    refusal is a policy decision rather than a crash. The declared numbers are
    read structurally off the envelope (never imported), so this stays inside the
    provider-free boundary the AST guard enforces.
    """
    wall = getattr(ladder.envelope, "max_wall_s", None)
    requests = getattr(ladder.envelope, "max_requests", None)
    left = max(0.0, ladder.remaining())
    ran = ladder.attempt_index
    # The grants in `record()` apply the same admission test, so this lands
    # after an attempt ran only when the clock moved between a grant and the
    # next start (an overslept backoff). It must not then claim the slot
    # dispatched nothing.
    outcome = (
        "Nothing was dispatched"
        if not ran
        else f"{ran} attempt(s) ran; attempt {ran + 1} was not started"
    )
    if wall is None:
        # Rule 3, before the first attempt: the slot's own ceiling is already
        # under MIN_ATTEMPT_BUDGET_S, so no declared envelope is involved.
        return (
            f"{STATUS_BUDGET_EXHAUSTED}: {target} was given a {timeout}s slot and "
            f"{left:.1f}s of it is left, below the {ladder._min_attempt_budget_s}s "
            f"minimum an attempt is worth starting with. {outcome}."
        )
    return (
        f"{STATUS_BUDGET_EXHAUSTED}: {target} declares one dispatch may cost up to "
        f"{wall:g}s of wall clock inside the CLI"
        + (f" ({requests} upstream requests)" if requests is not None else "")
        + f", and only {left:.1f}s of this slot's {timeout}s budget is left. "
        f"{outcome} — §7.5 rule 4 refuses a child it would have to "
        f"kill part-way through a retry chain the harness cannot see. Raise the "
        f"slot timeout above {wall:g}s, or pick a runner with a smaller envelope."
    )
