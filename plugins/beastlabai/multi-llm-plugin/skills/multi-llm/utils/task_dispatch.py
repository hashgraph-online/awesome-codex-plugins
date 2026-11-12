"""One task's dispatch: :func:`dispatch_task`, its attempts and its
re-asks.

:func:`dispatch_task` is a loop over typed steps, each testable alone:
:func:`plan_dispatch` (a :class:`DispatchPlan`, or a :class:`Refusal` with
nothing spawned), then per attempt :func:`admit_attempt`,
:func:`spawn_attempt` and :func:`read_attempt` (an :class:`AttemptReading`),
then :func:`ask_about_reply` and :func:`finish_ok` for a schema-valid reply,
or :func:`check_moved_before_retry`, :func:`record_failed_attempt` and
:func:`decide_next` (a :class:`Next`) for any other, and
:func:`close_outcome`. What an attempt carries into the next is an
:class:`AttemptState`; every hook's context comes from :func:`hook_context`
and its one table, :data:`HOOK_CONTEXT_KEYS`
(docs/development/delegation.md#where-the-executors-helpers-live).

The kind tables the loop reads (:data:`SCHEMA_PHASE_BY_KIND`,
:data:`SCHEMA_REPAIRS_BY_KIND`, :data:`RESENDS_BY_KIND`,
:data:`RECLASSIFIABLE_STATUSES`), the D3g verification statuses
(:data:`STATUS_PARTIAL`, :data:`STATUS_POLICY_VIOLATION`,
:data:`STATUS_BATCH_FAILED`), and the loop's helpers: the write hooks
and the guards around them (:func:`_denied_write_turn`,
:func:`_moved_during_repair`), the report re-ask
(:func:`_incomplete_report_reask`, :func:`merge_restated_check`), the
prompt budget (:func:`_prompt_over_budget`) and each attempt's record.
It spawns through ``dispatch_spawn``, classifies through
``attempt_classifier``, and takes its retry policy from
``retry_ladder``.

``utils.subagent_executor`` re-exports every name defined here for reading
only: patch one here, never through the executor
(docs/development/delegation.md#where-the-executors-helpers-live).
"""

from __future__ import annotations

import copy
import hashlib
import os
import re
import sys
import time
from dataclasses import dataclass, replace
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

from . import concurrency as _concurrency
from . import structured_output
from .launch_limiter import attempt_turn_blocking
from .llm_client import (
    _CMD_UNSAFE_CHARS,
    _resolve_executable,
)
from .provider_registry import (
    get_provider,
    get_subagent_retries,
    get_subagent_timeout,
    parse_model_spec,
)
from . import landlock_dispatch
from .providers.base import (
    JailRequest,
    host_write_posture_consent,
    PROFILE_AGENT_WRITE,
    SANDBOX_RUNG_UNSANDBOXED,
    StructuredOutputUnavailable,
)
from .retry_ladder import (
    BACKOFF_STATUSES,
    RETRYABLE_STATUSES,
    STATUS_BUDGET_EXHAUSTED,
    STATUS_INCOMPLETE_REPORT,
    STATUS_OK,
    STATUS_REJECTED,
    STATUS_RUNNER_ERROR,
    STATUS_SCHEMA_INVALID,
    STATUS_SPAWN_FAILED,
    STATUS_TIMEOUT,
    STATUS_UNPARSEABLE,
    STOP_BUDGET,
    REPAIR_INCOMPLETE_REPORT,
    REPAIR_SCHEMA_INVALID,
    RESEND_NOTHING_CHANGED,
    RetryLadder,
    budget_exhausted_reason,
)
from .subagent_prompts import (
    build_nothing_changed_resend_prompt,
    build_schema_repair_prompt,
)
from . import subagent_tasks as _subagent_tasks
from .subagent_tasks import (
    WRITE_KINDS,
    declared_file_set,
    preferred_prompt_transport,
    refuse_reason,
)
from . import batch_reply as _batch_reply
from . import failure_capture as _failure_capture
from . import task_outcome as _task_outcome
from . import task_result as _task_result
from . import runner_selection as _runner_selection
from . import dispatch_spawn as _dispatch_spawn
from . import attempt_classifier as _attempt_classifier


#: The only statuses ``_classify_failed_run`` may reclassify (D3k). Rungs 4 and 5
#: mean "the run produced nothing usable", which is exactly the condition under
#: which a 429 or a login notice is the *real* explanation. Rung 6 is deliberately
#: absent: a ``schema_invalid`` result **parsed** — it is a deterministic
#: disagreement with the kind's result shape that is never retried — and its
#: streams carry the model's own prose, which routinely quotes "rate limit",
#: "429" or "unauthorized" straight out of the plan or diff under review. Matching
#: those substrings there would launder a schema disagreement into backoff retries
#: or, worse, into a batch-failing ``auth_failed``.
RECLASSIFIABLE_STATUSES = frozenset({STATUS_RUNNER_ERROR, STATUS_UNPARSEABLE})

#: Not a dispatch outcome either: the two D3g **verification** failures. They have
#: no D3k rung by design — the child ran, produced a schema-valid result and the
#: transport worked; what failed is the executor's own byte comparison, so
#: attaching a transport rung would be a category error (and would make a retry
#: look reasonable, which it never is for a half-applied file).
STATUS_PARTIAL = "partial_application"
STATUS_POLICY_VIOLATION = "policy_violation"
#: The third: the batch itself said ``failed`` (or its runner exited non-zero)
#: and the byte comparison agrees that nothing moved. Not ``ok`` — a runner that
#: reports it could not do the work has not done it, and continuing to the next
#: batch would build on the gap — and not retried either: the runner already
#: tried, and its own verdict, not a transport fault, is what is recorded.
#: Measured 2026-09-16: before this status a schema-valid ``{"status":
#: "failed"}`` with an empty diff was recorded as a *clean failure* with
#: ``status: ok``, the loop went on, and the phase completed at exit 0.
STATUS_BATCH_FAILED = "batch_failed"

#: The phase → schema table is keyed by **phase**; a Lane B dispatch's
#: document contract is its **kind**. The two are not interchangeable here: the
#: ``code-review`` phase dispatches ``validation`` tasks whose result is a
#: validation batch, not the phase's ``code_review_issues`` array, so handing a
#: subagent the phase's schema would constrain it to a document it was never
#: asked for — and then validate its answer against a second, different file.
#:
#: So the phase is derived from the kind, and the table is exactly the
#: intersection where the kind's own result schema (``validate_result``) and
#: ``structured_output.PHASE_SCHEMA_FILE`` resolve to the **same file**:
#: ``task_generation`` → ``generated_tasks.schema.json`` and ``consolidation``
#: → ``consolidation_batch.schema.json``. That identity is what lets the
#: recovery branch stay this lane's own (see :func:`_parse_with_schema_policy`)
#: instead of validating the same document twice against two files, and it is
#: asserted functionally in ``tests/test_lane_b_structured_output.py`` rather
#: than trusted.
#:
#: Every other kind maps to nothing, which is the off switch: no phase, no
#: schema resolve, no flag, and an argv byte-identical to the pre-M7 lane. The
#: write kinds are absent for the own reason — their product is a file
#: diff, and ``PHASE_SCHEMA_FILE`` puts every apply/implement phase at ``None``.
#:
#: **W1 disposition: DEFER — repository owner, 2026-08-20.** Emptying this table
#: to ``{}`` remains the one-line switch that returns the lane to dormant, and
#: it stays a switch rather than becoming the setting: Lane A's own callers are
#: not wired because its six shipped documents are array-rooted and claude-code
#: cannot natively carry an array-rooted schema. Object-rooting those six files
#: is a contract change for every consumer of them, so the decision is the
#: repository owner's and it has not been made.
#: **Re-check trigger:** claude-code accepts an array-rooted ``--json-schema``.
#: **Re-read date:** 2027-02-20. Where the verdict sits:
#: docs/development/providers.md#reading-a-capture (the schema verdict).
SCHEMA_PHASE_BY_KIND = {
    "task_generation": "generate-tasks",
    "consolidation": "consolidation",
}


#: The ladder's rule 7, granted per kind: how many schema-repair re-asks a
#: ``schema_invalid`` attempt of that kind gets before rung 6 is terminal.
#:
#: * ``task_generation``: the one kind whose prompt is the *only*
#:   contract on a runner with no structured output (opencode declares none),
#:   and the one whose rung-6 failure dead-ends a whole phase — measured
#:   2026-10-04, ``opencode/big-pickle`` answered the wrong shape twice and
#:   generate-tasks exited 3 both times.
#: * the three apply kinds: one big-pickle apply batch's
#:   report was unreadable and the whole phase stopped at exit 3 until a
#:   ``--resume`` re-ran the batch. A write kind's reply is the report of edits
#:   already on disk, so its re-ask is a different question
#:   (``subagent_prompts.build_schema_repair_prompt``'s write form): the
#:   original prompt is not re-sent, the runner restates its own previous
#:   reply without touching a file, and the dispatch fails as a partial
#:   application if any file moved during it (``tree_fingerprint``).
#: * ``implement``: T013 edited
#:   ``index.html`` for 442 s, replied in prose ("No valid JSON found in
#:   text"), and the stop called a finished edit a partial application. The
#:   same report re-ask, with the same guards: it restates the report and
#:   edits nothing, a file it moves makes the dispatch a partial application,
#:   and the byte comparison still decides what was applied.
#:
#: Validation and consolidation keep rung 6 terminal: a batch is one of many
#: and fails alone. A kind listed here must have a shape in
#: ``subagent_prompts.SCHEMA_REPAIR_SHAPES``.
SCHEMA_REPAIRS_BY_KIND = {
    "task_generation": 1,
    "apply_suggestions": 1,
    "apply_task_suggestions": 1,
    "apply_code_fixes": 1,
    "implement": 1,
}


def schema_phase_for_kind(kind: str) -> Optional[str]:
    """The phase whose schema governs ``kind``'s result, or ``None``."""
    return SCHEMA_PHASE_BY_KIND.get(kind)


#: The ladder's rule 9, granted per kind: how many times a write batch whose
#: reply said ``applied`` while not one byte moved is sent again, told so,
#: before it is recorded failed. Every write kind, because the classification
#: is shared; the scheduler's ``nothing_changed`` hook is what decides an
#: attempt qualifies (never a check task, which changes nothing by design).
RESENDS_BY_KIND = {
    "apply_suggestions": 1,
    "apply_task_suggestions": 1,
    "apply_code_fixes": 1,
    "implement": 1,
}

#: The token D3n substitutes late, per dispatch. Duplicated as a private constant
#: rather than imported at module scope only to keep this module's import graph
#: unchanged; ``tests/test_subagent_tasks.py`` pins the two spellings together.
#: A prompt-template placeholder, not an authentication credential.
_PRIOR_CHANGES_TOKEN: str = "{prior_changes_context}"


# ---------------------------------------------------------------------------
# One dispatch's typed steps: what it sends, what it carries, what it read
# ---------------------------------------------------------------------------

#: :class:`Next`'s two actions: another attempt, or close the outcome.
NEXT_RETRY = "retry"
NEXT_STOP = "stop"


@dataclass(frozen=True)
class DispatchHooks:
    """The callbacks one dispatch takes (each documented on
    :func:`dispatch_task`) and the sleep it backs off with. The last five are
    the write path's; a read dispatch passes none of them."""

    sleep: Callable[[float], None]
    before_attempt: Optional[Callable[[Dict[str, Any]], None]] = None
    after_result: Optional[Callable[[Dict[str, Any]], None]] = None
    after_attempt: Optional[Callable[[_task_outcome.Attempt], None]] = None
    changed_files: Optional[Callable[[Dict[str, Any]], Sequence[str]]] = None
    tree_fingerprint: Optional[Callable[[Dict[str, Any]], Any]] = None
    nothing_changed: Optional[Callable[[Dict[str, Any]], Optional[str]]] = None
    incomplete_report: Optional[Callable[[Dict[str, Any]], Optional[str]]] = None
    restate_findings: Optional[
        Callable[[Dict[str, Any]], Optional[Tuple[str, Sequence[str]]]]
    ] = None


@dataclass(frozen=True)
class Refusal:
    """A dispatch refused before its first attempt: nothing was spawned.

    ``status`` is rung 7 unless the runner has no adapter at all
    (``spawn_failed``); ``output_path`` is the result's target once it was
    resolved, which the outcome keeps.
    """

    reason: str
    status: str = STATUS_REJECTED
    output_path: Optional[str] = None


@dataclass(frozen=True)
class DispatchPlan:
    """What every attempt of one dispatch sends, resolved once by
    :func:`plan_dispatch`: the runner and its adapter, the profile and the
    grant replayed from the preflight, the result's target, the prompt, the
    budgets and the schema leg."""

    task: Dict[str, Any]
    task_id: str
    kind: str
    profile: str
    runner: str
    anchor: Optional[str]
    cwd: Optional[str]
    phase_dir: str
    provider: Any
    provider_name: str
    model: str
    transport: str
    fallback: Optional[str]
    wrapping: Any
    jail_request: Optional[JailRequest]
    write_consent: Any
    read_dirs: List[str]
    target: Any
    prompt: str
    prefer_arrays: bool
    salvage_failure: Any
    effective_timeout: Any
    retries: int
    schema: Any
    schema_phase: Optional[str]
    declined_marker: Optional[str]

    @property
    def budget_kwargs(self) -> Dict[str, Any]:
        """What :func:`_prompt_over_budget` measures a wrapped argv with: the
        rung and the grant on the plugin's jail, nothing otherwise."""
        return (
            {"sandbox_fallback": self.fallback, "jail_request": self.jail_request}
            if self.wrapping is not None else {}
        )


@dataclass
class AttemptState:
    """What one attempt carries into the next.

    The fields change only through the ``start_*`` methods and
    :meth:`refuse_resend`, one per rule, so a rule's resets live in one
    place.
    """

    #: What this attempt sends: the task's prompt, until a re-ask or a
    #: re-send replaces it. A transport retry after a re-ask re-sends the
    #: re-ask.
    prompt: str
    #: The re-ask this attempt carries (rule 7: ``REPAIR_SCHEMA_INVALID`` or
    #: ``REPAIR_INCOMPLETE_REPORT``), or ``None``.
    repair: Optional[str] = None
    #: Rule 9's re-send is the batch again, not a re-ask: it
    #: keeps every guard a first dispatch has (the pre-retry check included),
    #: so it is marked on the attempt it produced and nowhere else.
    resend: Optional[str] = None
    #: Why a re-send the classification would have wanted was not granted
    #: (the deadline), for ``after_result``'s wording.
    resend_note: Optional[str] = None
    #: A write kind's report re-ask: the files' state when it was granted,
    #: which the re-ask must leave exactly as it found it (``tree_fingerprint``).
    repair_baseline: Any = None
    #: A report-only turn cannot change what the original turn observed when
    #: it ran its checks. Applied before persisting the restated report so
    #: the result file and the scheduler's verdict read the same evidence.
    repair_check: Optional[Dict[str, Any]] = None
    #: A restatement of a check's findings, the first report's
    #: check and the accepted findings a changed finding may be cut down to.
    restate_check: Optional[Tuple[Dict[str, Any], List[str]]] = None
    #: The ``after_result`` context of a readable report that
    #: left items out, kept while its re-ask runs, so a re-ask that cannot
    #: restate it leaves this one to be classified.
    reask_fallback: Optional[Dict[str, Any]] = None

    @property
    def repair_tag(self) -> Optional[str]:
        """What an attempt's row and ``failed/`` capture say it carried."""
        return self.repair or self.resend

    def start_resend(self, prompt: str) -> None:
        """Rule 9: send the batch again, told nothing moved. A re-send is a
        first dispatch again, so every re-ask's leftovers are dropped."""
        self.prompt = prompt
        self.resend = RESEND_NOTHING_CHANGED
        self.repair = None
        self.repair_baseline = None
        self.repair_check = None
        self.restate_check = None

    def refuse_resend(self, note: Optional[str]) -> None:
        """Rule 9 wanted a re-send the ladder refused; keep its reason."""
        self.resend_note = note

    def start_report_reask(
        self,
        prompt: str,
        baseline: Any,
        *,
        repair_check: Optional[Dict[str, Any]],
        restate_check: Optional[Tuple[Dict[str, Any], List[str]]],
        fallback: Dict[str, Any],
    ) -> None:
        """Rule 7's second form: restate a readable
        report, guarded by the files' state *baseline*, with *fallback* to
        classify if the restatement fails."""
        self.repair_baseline = baseline
        self.repair_check = repair_check
        self.restate_check = restate_check
        self.reask_fallback = fallback
        self.prompt = prompt
        self.repair = REPAIR_INCOMPLETE_REPORT
        self.resend = None

    def start_schema_repair(
        self, prompt: str, guard: Optional[Tuple[Any, Optional[Dict[str, Any]]]] = None,
    ) -> None:
        """Rule 7: the one schema-repair re-ask. *guard* is a write kind's
        ``(files' state, check evidence)``; a read kind has none."""
        if guard is not None:
            self.repair_baseline, self.repair_check = guard
        self.prompt = prompt
        self.repair = REPAIR_SCHEMA_INVALID


@dataclass(frozen=True)
class AttemptReading:
    """What one spawned attempt produced, as far as it has been read: the
    rung its capture lands on (``status``, ``error``), the document it
    extracted, if any (what a schema-repair re-ask quotes the validator's
    errors about), its usage, and the runner's own reply text once a re-ask
    guard needed it."""

    index: int
    capture: _dispatch_spawn._Capture
    status: str
    error: Optional[str]
    data: Any = None
    usage: Optional[Dict[str, Any]] = None
    reply_text: Optional[str] = None


@dataclass(frozen=True)
class RetryGuard:
    """What the write path's pre-retry check decided: whether the batch may
    be sent again (``repeatable``), and the partial application to record
    if its one report re-ask is refused (``partial_if_refused``)."""

    repeatable: bool = True
    partial_if_refused: Optional[str] = None


@dataclass(frozen=True)
class Next:
    """What the loop does after an attempt: :data:`NEXT_RETRY` starts
    another (carrying this attempt's verdict, which an admission that takes
    the grant back keeps), :data:`NEXT_STOP` closes the outcome on it."""

    action: str
    status: str
    error: Optional[str]

    @classmethod
    def retry(cls, status: str, error: Optional[str]) -> "Next":
        return cls(NEXT_RETRY, status, error)

    @classmethod
    def stop(cls, status: str, error: Optional[str]) -> "Next":
        return cls(NEXT_STOP, status, error)


#: The keys of the context each hook receives, in order: one table, so every
#: reader knows its shape. ``*jail`` stands for
#: ``dispatch_spawn._jail_hook_context``'s keys (the rung, the stream's
#: denials, the jail evidence). ``nothing_changed``, ``incomplete_report`` and
#: ``restate_findings`` all receive one ``reply`` context, the same object,
#: so what one hook adds the next can read (``moved_outside``);
#: ``after_result`` receives ``result``, also when it classifies the report a
#: report re-ask could not restate.
HOOK_CONTEXT_KEYS: Dict[str, Tuple[str, ...]] = {
    "tree_fingerprint": ("task", "task_id", "kind", "cwd", "outcome"),
    "before_attempt": (
        "task", "task_id", "kind", "profile", "runner", "provider", "model",
        "cwd", "attempt", "prompt", "repair", "transport", "outcome",
    ),
    "reply": (
        "task", "task_id", "kind", "profile", "runner", "cwd", "attempt",
        "prompt", "result", "exit_code", "*jail",
    ),
    "result": (
        "task", "task_id", "kind", "profile", "runner", "cwd", "attempt",
        "prompt", "result", "exit_code", "stderr_tail", "usage",
        "duration_seconds", "outcome", "resent", "resend_note", "*jail",
    ),
    "changed_files": (
        "task", "task_id", "kind", "attempt", "cwd", "outcome", "*jail",
    ),
    # The ``result`` context a report re-ask remembers, without
    # ``duration_seconds`` and ``outcome``: :func:`close_outcome` appends those
    # last when it classifies the report the re-ask could not restate, so its
    # ``after_result`` keys come in the order they always did.
    "reask_fallback": (
        "task", "task_id", "kind", "profile", "runner", "cwd", "attempt",
        "prompt", "result", "exit_code", "stderr_tail", "usage",
        "resent", "resend_note", "*jail",
    ),
}


def hook_context(
    shape: str,
    plan: DispatchPlan,
    outcome: _task_outcome.TaskOutcome,
    *,
    state: Optional[AttemptState] = None,
    reading: Optional[AttemptReading] = None,
    attempt: Optional[int] = None,
) -> Dict[str, Any]:
    """The context a hook receives, with :data:`HOOK_CONTEXT_KEYS`' keys for
    *shape*, read now from the plan, the outcome, the carried state and the
    attempt's reading (whose index is ``attempt`` unless given)."""
    capture = reading.capture if reading is not None else None
    if attempt is None and reading is not None:
        attempt = reading.index
    values: Dict[str, Callable[[], Any]] = {
        "task": lambda: plan.task,
        "task_id": lambda: plan.task_id,
        "kind": lambda: plan.kind,
        "profile": lambda: plan.profile,
        "runner": lambda: plan.runner,
        "provider": lambda: plan.provider_name,
        "model": lambda: plan.model,
        "cwd": lambda: plan.cwd,
        "attempt": lambda: attempt,
        "prompt": lambda: state.prompt,  # type: ignore[union-attr]
        "repair": lambda: state.repair,  # type: ignore[union-attr]
        "transport": lambda: plan.transport,
        "outcome": lambda: outcome,
        "result": lambda: reading.data,  # type: ignore[union-attr]
        "exit_code": lambda: capture.exit_code,  # type: ignore[union-attr]
        # Not an `outcome` field: this one leaves the module through the
        # caller's callback, so no sink here can promise it is redacted on the
        # way out. Redacted at the source instead, fail-safe: a raising
        # redactor yields a placeholder, never the stream.
        "stderr_tail": lambda: _failure_capture._redact_probe_tail(
            capture.stderr, 2000  # type: ignore[union-attr]
        ),
        "usage": lambda: reading.usage,  # type: ignore[union-attr]
        "duration_seconds": lambda: outcome.duration_seconds,
        # Rule 9: whether this attempt was the re-send of a batch that changed
        # nothing, and why a re-send the classification would have wanted was
        # not granted (the deadline), for its wording.
        "resent": lambda: state.resend is not None,  # type: ignore[union-attr]
        "resend_note": lambda: state.resend_note,  # type: ignore[union-attr]
    }
    context: Dict[str, Any] = {}
    for key in HOOK_CONTEXT_KEYS[shape]:
        if key == "*jail":
            context.update(_dispatch_spawn._jail_hook_context(
                capture, plan.jail_request, plan.fallback
            ))
        else:
            context[key] = values[key]()
    return context


def dispatch_task(
    task: Dict[str, Any],
    *,
    phase_dir: str,
    runner: str,
    anchor: Optional[str] = None,
    cwd: Optional[str] = None,
    retries: Optional[int] = None,
    timeout: Optional[int] = None,
    sleep: Optional[Callable[[float], None]] = None,
    prompt: Optional[str] = None,
    before_attempt: Optional[Callable[[Dict[str, Any]], None]] = None,
    after_result: Optional[Callable[[Dict[str, Any]], None]] = None,
    after_attempt: Optional[Callable[[_task_outcome.Attempt], None]] = None,
    changed_files: Optional[Callable[[Dict[str, Any]], Sequence[str]]] = None,
    jail_request: Optional[JailRequest] = None,
    tree_fingerprint: Optional[Callable[[Dict[str, Any]], Any]] = None,
    nothing_changed: Optional[Callable[[Dict[str, Any]], Optional[str]]] = None,
    incomplete_report: Optional[Callable[[Dict[str, Any]], Optional[str]]] = None,
    restate_findings: Optional[
        Callable[[Dict[str, Any]], Optional[Tuple[str, Sequence[str]]]]
    ] = None,
) -> _task_outcome.TaskOutcome:
    """Dispatch one task and return its :class:`TaskOutcome` (D3k classified).

    Synchronous by design: the concurrency lives in
    ``review_orchestrator_base.run_tasks_concurrent``, which runs this in a
    thread, so one dispatch is a straight line that is readable and unit-testable
    on its own.

    Retries are bounded and only for transport-shaped failures — a timeout, a run
    yielding no parsed text, or a ``parse_output`` failure. A result that parsed
    but failed schema validation is **never** retried: that is a deterministic
    disagreement a retry would only launder. A retried task keeps its ``task_id``,
    so the task-keyed result map and reaggregation are unaffected.

    ``timeout`` (or ``driver.subagent_timeout_s``) is the task's **total**
    wall-clock budget, not a per-attempt one: a monotonic deadline is fixed at
    entry, every attempt is spawned with what is left of it, backoff sleeps are
    spent from it, and a retry is refused once no usable slice remains. So a
    dispatch is bounded by the configured ceiling however many times it retries.

    The structured-output leg is read **here, before dispatch**, and it is
    the second of M7's two phase callers (``llm_client.invoke_with_provider`` is
    the first). The phase comes from the task's *kind*
    (:data:`SCHEMA_PHASE_BY_KIND`), the schema file is loaded once per dispatch,
    codex's sidecar is written per attempt inside :func:`_spawn`'s ``finally``,
    and the verdict lands on this lane's own rungs (see
    :func:`_parse_with_schema_policy`) plus ``TaskOutcome.structured_output``. A
    kind with no schema phase — every kind but ``task_generation`` and
    ``consolidation`` — takes none of it and renders the argv it always did.

    Args:
        prompt: The prompt to dispatch, overriding ``task["prompt"]``. This is the
            D3n seam: an apply prompt is complete except for
            ``{prior_changes_context}``, whose value is a function of the batches
            that already finished, so the scheduler substitutes it and hands the
            *dispatched* prompt in here. The task JSON stays the immutable
            hash-bound snapshot D2g made it — this never rewrites it.
        before_attempt: Called once per attempt, immediately **before** the spawn,
            with ``{task, profile, runner, cwd, attempt, argv, prompt}``. The write
            path's pre-batch snapshot, its pre-dispatch write-policy check and its
            ``dispatched`` audit line hang here. Raising :class:`ResultRejected`
            refuses the task with nothing spawned (D3l).
        after_result: Called **after** rung-6 validation passed and the result was
            persisted, with ``{task, outcome, result, capture, ...}``. This is the
            D3g seam: the snapshot/diff classification, the post-run policy
            recomputation and the ``completed`` audit line. It mutates
            ``outcome`` (``write_outcome``, ``files_touched``, ``summary``,
            ``status``) — the model's claim is never the verdict.
        after_attempt: Called with each :class:`Attempt` the moment it is
            recorded — before ``after_result``, ``ladder.record`` and any backoff
            sleep — so a caller can react to one attempt while the task is still
            retrying (rate-limit backpressure narrows on the attempt, not on
            the finished task). It runs on the dispatching thread. It is an
            observer: an exception it raises is reported on stderr and
            swallowed, never allowed to fail the attempt.
        changed_files: The write lane's pre-retry check. Called only for an
        ``agent-write`` attempt that the adapter's
            structural check classified ``runner_error`` (a turn ended by an
            auto-rejected permission, so no result exists and ``after_result``
            never runs), with ``{task, task_id, kind, attempt, cwd, outcome}``;
            it returns the paths whose bytes moved against the task's pre-batch
            snapshot. Any → the attempt is recorded ``partial_application`` and
            no further attempt starts: a retry on top of a half-applied edit is
            the unsafe case. None → it stays ``runner_error`` and is retried like
            any other. A hook that raises is read as "could not tell", which
            fails closed the same way as a non-empty answer.
        jail_request: The grant a dispatch on the plugin's Landlock jail
            carries. A read kind needs none — one is
            built from ``cwd`` — and is refused (rung 7, nothing spawned) if
            handed one that carries a write scope or target: a read kind never
            carries a grant. A write kind on the rung must carry one whose
            ``kind`` is the task's, whose ``write_scope`` is
            :data:`WRITE_SCOPE_BY_KIND`'s for it, and which names its target;
            anything else is refused on rung 7 naming the missing grant, never
            narrowed or widened. ``after_result`` and ``changed_files`` then
            see ``sandbox_rung``, ``jail_denials`` (a write dispatch on the
            rung) and ``jail_evidence``. A jail failure — a codex-internal
            EACCES the parent classifies as the jail's — is recorded rejected
            with one ``[JAIL_DENIED]`` line, never retried and never moved to
            another rung.
        tree_fingerprint: The write lane's guard on a report re-ask (the
            ladder's rule 7 for a write kind, :data:`SCHEMA_REPAIRS_BY_KIND`).
            Called with ``{task, task_id, kind, cwd, outcome}`` just before the
            re-ask and again after it; it returns a comparable value naming the
            current bytes of every file the batch may have moved (a dict keyed
            by path, so a difference can be named). Any difference — or a hook
            that raises — records the re-ask ``partial_application``: it was
            asked only to restate the batch's report, so a file it moved is an
            edit nobody verified. Without the hook a write kind gets no re-ask.
        nothing_changed: The write lane's question before ``after_result``
            (the ladder's rule 9, :data:`RESENDS_BY_KIND`),
            with the ``after_result`` context: why this schema-valid reply
            said ``applied`` while not one byte moved, or ``None`` when that
            is not the case (any byte moved, a check task, a crash, a jail
            denial — the classification decides those). A reason, while the
            allowance holds a re-send the deadline admits, sends the batch's
            own prompt once more with
            :func:`subagent_prompts.build_nothing_changed_resend_prompt`
            appended, instead of classifying the attempt; it is recorded
            ``batch_failed`` with that reason and a failure capture. A hook
            that raises is "no re-send": the classification decides.
        incomplete_report: The write lane's other question before
            ``after_result`` (an apply kind), with the same
            context: why this readable report, after edits that moved bytes,
            leaves some of the batch's items out of both ``ids`` and
            ``declined``, or ``None``. A reason, while the schema-repair
            allowance and the deadline admit it (:meth:`RetryLadder.
            record_report_reask`) and ``tree_fingerprint`` can guard it,
            sends the report re-ask (``incomplete=True``, the reason as its
            one problem) instead of classifying, so a batch that left an item
            out of its report on purpose does not stop as a partial application
            on every resume. The restated report is classified
            like any; a re-ask that cannot restate it (prose, a timeout)
            leaves the original reply to be classified, and one that moved a
            file is a partial application. A hook that raises is "no re-ask".
        restate_findings: The implement lane's third question before
            ``after_result``, with the same context:
            ``(problem, accepted findings)`` when the reply's own check holds
            an accepted finding verbatim with words added, or ``None``. It
            sends the same one report re-ask, the problem as its one problem
            and the check's findings open to restating
            (``restate_findings=True``), and nothing is recorded as accepted
            by it: the restated report is classified like any, and only its
            ``findings`` and ``note`` are taken, through
            :func:`merge_restated_check`, which keeps the first report's
            whole ``check`` unless every finding it changed was cut down to
            one of the accepted findings, word for word. A hook that raises
            is "no re-ask".
    """
    task_id = str(task.get("task_id", ""))
    kind = str(task.get("kind", ""))
    profile = _runner_selection.profile_for_kind(kind)
    outcome = _task_outcome.TaskOutcome(
        task_id=task_id, kind=kind, runner=runner, status=STATUS_REJECTED,
        profile=profile,
    )
    hooks = DispatchHooks(
        sleep=sleep or time.sleep,
        before_attempt=before_attempt,
        after_result=after_result,
        after_attempt=after_attempt,
        changed_files=changed_files,
        tree_fingerprint=tree_fingerprint,
        nothing_changed=nothing_changed,
        incomplete_report=incomplete_report,
        restate_findings=restate_findings,
    )
    plan = plan_dispatch(
        task, phase_dir=phase_dir, runner=runner, anchor=anchor, cwd=cwd,
        retries=retries, timeout=timeout, prompt=prompt, jail_request=jail_request,
    )
    if isinstance(plan, Refusal):
        outcome.status = plan.status
        outcome.reason = plan.reason
        if plan.output_path is not None:
            outcome.output_path = plan.output_path
        return outcome
    outcome.output_path = str(plan.target)

    # What the two invocation lanes share is the *policy*, not the loop.
    # `RetryLadder` owns D3i's single monotonic deadline — taken once, every
    # attempt spawned with what is LEFT of it, every backoff sleep charged to the
    # same deadline, so a task with N retries can never run for (N+1) × the
    # configured ceiling — plus D3k's two separate counters and the admission
    # tests. The only lane-specific lines below are the blocking `_spawn` and the
    # `sleep` call. `ladder.elapsed()` is D3j's wall clock: across *every*
    # attempt, including the backoff sleeps between them — not the sum of the
    # children's own runtimes, which would let a task that slept through four
    # exponential backoffs report only the seconds its children ran and never
    # reach `effective_timeout`. Monotonic, so a clock step cannot rewind it.
    #
    # The adapter's DECLARED vendor envelope  switches on the two
    # composition rules: rule 4's pre-dispatch admission test ("would one
    # worst-case attempt fit in what is left?", recorded `budget_exhausted` with
    # nothing spawned) and rule 6(b)'s refusal to re-issue an identical
    # rate-limit dispatch against a CLI that already exhausted its own 429 chain.
    # `getattr` rather than an attribute read: the eleven unmeasured adapters
    # declare `None`, which rule 6(c) reads as "assume one request" — never
    # "assume the worst".
    #
    # Rule 7 (the ladder's own): `SCHEMA_REPAIRS_BY_KIND` grants a kind its
    # schema-repair re-asks — `task_generation` one, every other kind none, so
    # rung 6 stays terminal for them exactly as before. A granted re-ask is an
    # attempt like any other: same deadline, its own `failed/` capture and its
    # own row in the batch report.
    ladder = RetryLadder(
        timeout=plan.effective_timeout,
        retries=plan.retries,
        envelope=getattr(plan.provider, "internal_retries", None),
        now=time.monotonic,
        schema_repairs=SCHEMA_REPAIRS_BY_KIND.get(kind, 0),
        resends=(
            RESENDS_BY_KIND.get(kind, 0)
            if nothing_changed is not None and after_result is not None else 0
        ),
    )
    state = AttemptState(prompt=plan.prompt)

    previous: Optional[Next] = None
    while True:
        stop = admit_attempt(plan, ladder, previous)
        if stop is not None:
            break
        attempt_index = ladder.attempt_index
        if hooks.before_attempt is not None:
            # The write path's snapshot / policy / audit leg. A refusal here means
            # nothing is spawned for this attempt — the whole point of enforcing
            # the policy pre-dispatch rather than only detecting it afterwards.
            try:
                hooks.before_attempt(hook_context(
                    "before_attempt", plan, outcome, state=state, attempt=attempt_index,
                ))
            except _task_outcome.ResultRejected as exc:
                outcome.status = exc.status
                outcome.reason = exc.message
                outcome.duration_seconds = ladder.elapsed()
                return outcome
        spawned = spawn_attempt(plan, hooks, state, ladder, outcome, attempt_index)
        if isinstance(spawned, Next):
            stop = spawned
            break
        reading = read_attempt(plan, hooks, state, outcome, spawned, attempt_index)
        if reading.status == STATUS_OK:
            reading, asked = ask_about_reply(plan, hooks, state, ladder, outcome, reading)
            if asked is not None:
                previous = asked
                continue
            if reading.status == STATUS_OK:
                return finish_ok(plan, hooks, state, ladder, outcome, reading)
        reading, guard = check_moved_before_retry(
            plan, hooks, state, ladder, outcome, reading
        )
        reading = record_failed_attempt(plan, hooks, state, outcome, reading)
        step = decide_next(plan, hooks, state, ladder, outcome, reading, guard)
        if step.action != NEXT_RETRY:
            stop = step
            break
        previous = step
    return close_outcome(plan, hooks, state, ladder, outcome, stop)


def plan_dispatch(
    task: Dict[str, Any],
    *,
    phase_dir: str,
    runner: str,
    anchor: Optional[str] = None,
    cwd: Optional[str] = None,
    retries: Optional[int] = None,
    timeout: Optional[int] = None,
    prompt: Optional[str] = None,
    jail_request: Optional[JailRequest] = None,
) -> Union[DispatchPlan, Refusal]:
    """What every attempt of *task* sends, or why nothing may be spawned.

    The D2 pre-dispatch refusals and D3f's output containment, the grant
    replayed from the preflight (never re-taken here), the directories a
    runner must be able to read, D3n's token check and D2d's argv budget;
    then the budgets and the schema leg, read once per dispatch.
    """
    task_id = str(task.get("task_id", ""))
    kind = str(task.get("kind", ""))
    profile = _runner_selection.profile_for_kind(kind)

    provider_name, model = parse_model_spec(runner, anchor=anchor)
    provider = get_provider(provider_name)
    if provider is None:
        return Refusal(
            f"runner {runner!r} has no built-in adapter", status=STATUS_SPAWN_FAILED,
        )

    # --- pre-dispatch refusals: nothing is spawned for these ----------------
    reason = refuse_reason(
        task,
        supports_workspace_reads=provider.supports_workspace_reads,
        runner=runner,
    )
    if reason is not None:
        return Refusal(reason)
    if not provider.supports_profile(profile):
        return Refusal(
            f"{provider_name} does not implement the {profile!r} profile; a "
            f"read/analyze task is never downgraded to a write-capable "
            f"invocation, so this fails dispatch"
        )
    # D6 override: replay the preflight's decision, never re-take
    # it here. A read kind reads the id of the rung its argv must render
    # (landlock rung); a write kind reads the decision taken for its own write
    # scope — the plugin's jail, the F5 floor, or
    # none, in which case its argv renders unchanged.
    grant_refusal, jail_request, fallback = _dispatch_spawn._dispatch_grant(
        task, kind=kind, profile=profile, runner=runner, cwd=cwd,
        provider=provider, jail_request=jail_request,
    )
    if grant_refusal is not None:
        return Refusal(grant_refusal)
    wrapping = _dispatch_spawn._wrapping_rung(provider, profile, fallback)
    # The consent carries the kind's own write scope down to the render and the
    # backstop, which both refuse a scope the jail does not serve.
    write_consent = (
        host_write_posture_consent(write_scope=_runner_selection.WRITE_SCOPE_BY_KIND.get(kind))
        if profile == PROFILE_AGENT_WRITE and fallback == SANDBOX_RUNG_UNSANDBOXED
        else None
    )
    # A snapshot named by path may sit in a
    # phase dir outside the runner's cwd. A runner that reads anywhere needs
    # nothing; one that can widen its read scope gets the flag for exactly
    # those directories; any other is refused here rather than handed a path
    # it cannot open (which reads as a confident, blind verdict).
    read_dirs = _dispatch_spawn._context_read_dirs(task, cwd)
    if read_dirs and getattr(provider, "reads_outside_cwd", False):
        read_dirs = []
    if read_dirs and not getattr(provider, "read_scope_flag", None):
        return Refusal(
            f"{kind} batch {task.get('batch_index', task_id)} names "
            f"{', '.join(read_dirs)} outside the runner's working directory; "
            f"runner {runner} cannot read files there; rematerialize with a "
            f"capable runner. Nothing was dispatched."
        )
    try:
        target = _task_result.resolve_output_target(task, phase_dir)
    except _task_outcome.ResultRejected as exc:
        return Refusal(exc.message)
    output_path = str(target)

    prompt = (task.get("prompt") if prompt is None else prompt) or ""
    if not prompt.strip():
        return Refusal(f"Task {task_id}: carries no prompt", output_path=output_path)
    # D3n: the literal token must never reach a runner. A write prompt that still
    # carries it means the scheduler's late substitution did not run, which would
    # silently drop every prior-batch summary — the exact context that keeps batch
    # N from re-applying or contradicting batch N-1. Contract error, not a warning.
    if kind in WRITE_KINDS and _PRIOR_CHANGES_TOKEN in prompt:
        return Refusal(
            f"Task {task_id}: the dispatched prompt still contains the literal "
            f"{_PRIOR_CHANGES_TOKEN} token, so the prior-batch context was never "
            f"substituted. A runner would receive the brace text and silently lose "
            f"every prior-batch summary. Nothing was dispatched.",
            output_path=output_path,
        )

    transport = preferred_prompt_transport(provider_name)
    # D2d/D3: refuse an over-budget prompt HERE rather than letting llm_client's
    # Windows command-line guard fail it late with PROMPT_TOO_LONG. A stdin/file
    # transport is unbounded, so this only ever fires for an argv-only runner.
    over_budget = _prompt_over_budget(
        provider, model, prompt, transport, profile,
        **({"sandbox_fallback": fallback, "jail_request": jail_request}
           if wrapping is not None else {}),
    )
    if over_budget is not None:
        return Refusal(f"Task {task_id}: {over_budget}", output_path=output_path)

    prefer_arrays = kind == "salvage"
    # D4.5: a salvage of a timed-out run may not persist `[]` (read once, here,
    # from the request the task is bound to; `None` for every other kind).
    salvage_failure = _task_result.salvage_failure_of(task, phase_dir)
    effective_timeout = timeout or get_subagent_timeout(provider_name, anchor=anchor)
    budget = retries if retries is not None else get_subagent_retries(anchor=anchor)

    # The "the caller reads the flag before dispatch", on this lane and once
    # per dispatch — the schema file is read here, not per attempt, and the
    # per-(provider, phase) WARN is emitted once per process by
    # `schema_for_dispatch`. The phase comes from the KIND (see
    # `SCHEMA_PHASE_BY_KIND`): `None` means no schema, no flag and an argv
    # byte-identical to the pre-M7 lane. A `None` schema with a phase means the
    # adapter declined — no `structured_output_support`, or a schema this CLI
    # provably cannot carry — which resolves exactly like a failed gate:
    # prompt-level JSON, marked `recovered`/`unvalidated`, never `native`.
    schema_phase = schema_phase_for_kind(kind)
    schema = None
    declined_marker = None
    if schema_phase:
        try:
            schema, resolved_marker = structured_output.schema_for_dispatch(
                provider, schema_phase
            )
        except structured_output.SchemaConfigError as exc:
            # Rung 7, not a rung 4/5 transport failure: no dispatch can produce a
            # schema file that is not there, so it is never retried and nothing
            # was spawned.
            return Refusal(f"structured output: {exc}", output_path=output_path)
        if schema is None:
            # The adapter declined, so the marker is already decided and only the
            # result is still open; when a schema IS dispatched the post-run
            # verdict decides between `native` and `recovered` instead.
            declined_marker = resolved_marker

    return DispatchPlan(
        task=task, task_id=task_id, kind=kind, profile=profile, runner=runner,
        anchor=anchor, cwd=cwd, phase_dir=phase_dir, provider=provider,
        provider_name=provider_name, model=model, transport=transport,
        fallback=fallback, wrapping=wrapping, jail_request=jail_request,
        write_consent=write_consent, read_dirs=read_dirs, target=target,
        prompt=prompt, prefer_arrays=prefer_arrays,
        salvage_failure=salvage_failure, effective_timeout=effective_timeout,
        retries=budget, schema=schema, schema_phase=schema_phase,
        declined_marker=declined_marker,
    )


def _never_started(plan: DispatchPlan, attempts_done: int) -> str:
    return (
        f"the per-task wall-clock budget of {plan.effective_timeout}s was "
        f"exhausted after {attempts_done} attempt(s); attempt "
        f"{attempts_done + 1} was never started"
    )


def admit_attempt(
    plan: DispatchPlan, ladder: RetryLadder, previous: Optional[Next],
) -> Optional[Next]:
    """Admit the next attempt (``None``), or stop with why not.

    *previous* is the attempt that earned this one (``None`` before the
    first): a grant the ladder takes back at the next start keeps that
    attempt's verdict.
    """
    # Launch spacing: inside `run_tasks_concurrent` every attempt takes its
    # provider's launch turn first, charged to this deadline
    # (`utils/launch_limiter.py`); a no-op anywhere else.
    attempt_turn_blocking(budget=max(0.0, ladder.remaining()))
    if ladder.next_attempt() is not None:
        return None
    #  rules 3 and 4: no attempt starts with less than
    # MIN_ATTEMPT_BUDGET_S of the deadline left, and none starts at all
    # when what is left cannot hold one worst-case attempt of this
    # adapter's *declared* vendor envelope — better a slot that spawned
    # nothing than a child killed part-way through a retry chain the
    # harness cannot see.
    if ladder.stop_reason == STOP_BUDGET and not ladder.attempt_index:
        return Next.stop(STATUS_BUDGET_EXHAUSTED, budget_exhausted_reason(
            ladder, target=plan.runner, timeout=plan.effective_timeout
        ))
    if ladder.stop_reason == STOP_BUDGET:
        # A grant taken back at the next start: `record()` applies the
        # same admission test to every grant, so only a clock that
        # moved in between (an overslept backoff) lands here. The last
        # attempt RAN, so its own status stands — `budget_exhausted`
        # means nothing was spawned. An attempt ran, so
        # *previous* is set.
        return Next.stop(previous.status, (  # type: ignore[union-attr]
            f"{previous.error} (no further attempt: "  # type: ignore[union-attr]
            f"{budget_exhausted_reason(ladder, target=plan.runner, timeout=plan.effective_timeout)})"
        ))
    return Next.stop(STATUS_TIMEOUT, _never_started(plan, ladder.attempt_index))


def spawn_attempt(
    plan: DispatchPlan,
    hooks: DispatchHooks,
    state: AttemptState,
    ladder: RetryLadder,
    outcome: _task_outcome.TaskOutcome,
    attempt_index: int,
) -> Union[_dispatch_spawn._Capture, Next]:
    """Spawn one admitted attempt with what is left of the deadline: its
    capture, or a stop when nothing was spawned."""
    attempt_budget = ladder.remaining()
    if attempt_budget <= 0:
        # The ladder already admitted this attempt, so what drained the
        # budget is the `before_attempt` leg (a large pre-batch snapshot)
        # spending what the attempt was admitted with. Spawning here would
        # hand a runner a budget it cannot use and record the kill as its
        # own timeout; the budget is the task's, so its exhaustion is the
        # task's outcome.
        return Next.stop(STATUS_TIMEOUT, _never_started(plan, attempt_index - 1))
    try:
        return _dispatch_spawn._spawn(
            provider=plan.provider,
            model=plan.model,
            prompt=state.prompt,
            profile=plan.profile,
            transport=plan.transport,
            timeout=attempt_budget,
            cwd=plan.cwd,
            schema=plan.schema,
            anchor=plan.anchor,
            sandbox_fallback=plan.fallback,
            read_dirs=plan.read_dirs,
            # The jail's grant reaches only a dispatch on the rung that
            # needs it.
            jail_request=plan.jail_request if plan.wrapping is not None else None,
            write_consent=plan.write_consent,
        )
    except (
        StructuredOutputUnavailable, structured_output.SchemaConfigError
    ) as exc:
        # The sixth acceptance case: raised while the sidecar was being
        # written or while the argv was being rendered, so **nothing was
        # spawned and no partial argv reached the CLI**. Rung 7 — a
        # configuration error, never retried, because re-running produces the
        # same missing file.
        return Next.stop(STATUS_REJECTED, f"structured output: {exc}")
    except _dispatch_spawn.SandboxBackstopViolation as exc:
        # Plan step 3's backstop: nothing was spawned. Rung 7, never retried.
        _record_unspawned_attempt(outcome, attempt_index, exc.message, hooks.after_attempt)
        return Next.stop(STATUS_REJECTED, exc.message)
    except ValueError as exc:
        if not plan.fallback:
            raise
        # An adapter refusing to render a rung without its grant (the
        # plugin's jail with no context): nothing was spawned. Rung 7.
        _record_unspawned_attempt(outcome, attempt_index, str(exc), hooks.after_attempt)
        return Next.stop(STATUS_REJECTED, str(exc))


def read_attempt(
    plan: DispatchPlan,
    hooks: DispatchHooks,
    state: AttemptState,
    outcome: _task_outcome.TaskOutcome,
    capture: _dispatch_spawn._Capture,
    attempt_index: int,
) -> AttemptReading:
    """Read one spawned attempt onto its rung: the jail's report, rungs 1-2
    or the jail's denial, a report re-ask that moved a file, then rungs 3-6
    through the adapter and the schema leg, and the one reclassification a
    run with no usable result may get."""
    usage = _safe_parse_usage(plan.provider, capture)
    _dispatch_spawn._report_jail_outcome(plan.task_id, capture)
    data = None
    denied_line = getattr(capture, "jail_denied_line", None)
    if denied_line:
        # A jail failure (plan F1 item 6): not a model error, never
        # retried, never moved to another rung.
        status, error = STATUS_REJECTED, denied_line
    else:
        status, error = _attempt_classifier._classify_pre_parse(capture)
        held = getattr(capture, "held_pipe_note", None)
        if status == STATUS_TIMEOUT and held:
            # A runner that exited while something outside its group held its
            # output ends as the timeout it was at the base, saying so
            # (dispatch_spawn._record_held_pipe).
            error = f"{error}. {held}"
    if state.repair_baseline is not None:
        moved = _moved_during_repair(
            hooks.tree_fingerprint, hook_context("tree_fingerprint", plan, outcome),
            state.repair_baseline,
        )
        if moved is not None:
            shown = ", ".join(moved[:5]) + (", …" if len(moved) > 5 else "")
            status, error = STATUS_PARTIAL, (
                f"PARTIAL APPLICATION: the report re-ask (attempt "
                f"{attempt_index}) was asked only to restate this batch's "
                f"report, but files changed while it ran ({shown}). Nothing "
                f"it did is recorded as applied, no further attempt is "
                f"started, the batch loop stops here and the phase is NOT "
                f"marked completed."
            )

    if status == STATUS_OK:
        status, error, data, marker = _attempt_classifier._parse_with_schema_policy(
            plan.provider, capture, kind=plan.kind, prefer_arrays=plan.prefer_arrays,
            schema=plan.schema, schema_phase=plan.schema_phase or "",
            model=f"{plan.provider_name}:{plan.model}",
            declined_marker=plan.declined_marker,
            failure=plan.salvage_failure,
        )
        if marker is not None:
            outcome.structured_output = marker
        if status in RECLASSIFIABLE_STATUSES:
            # Only a run with no usable result may be reclassified as
            # rate-limited or unauthenticated: the classifier matches on the
            # captured streams, and both a successful answer and a
            # schema-invalid one routinely quote plan text that would trip
            # those patterns. Rung 6 therefore never reaches this branch —
            # it is never retried (D3k), so laundering it into rung 3's
            # backoff or rung 1's batch-wide auth failure would be pure loss.
            reclassified = _attempt_classifier._classify_failed_run(
                plan.provider, capture, plan.model
            )
            if reclassified is not None:
                status, error = reclassified
    return AttemptReading(
        index=attempt_index, capture=capture, status=status, error=error,
        data=data, usage=usage,
    )


def ask_about_reply(
    plan: DispatchPlan,
    hooks: DispatchHooks,
    state: AttemptState,
    ladder: RetryLadder,
    outcome: _task_outcome.TaskOutcome,
    reading: AttemptReading,
) -> Tuple[AttemptReading, Optional[Next]]:
    """Persist a schema-valid reply, then put the write lane's three
    questions to it: rule 9's re-send, and rule 7's second form for a
    report that left items out or restated an accepted finding.

    Returns the reading with what was persisted and, when one question sent
    the batch or the report re-ask, the retry; with neither, the reply is
    accepted (:func:`finish_ok`). A reply persisting refused comes back with
    the refusal's status, to be recorded as a failed attempt.
    """
    data = reading.data
    if state.repair_check is not None and isinstance(data, dict):
        data = {**data, "check": copy.deepcopy(state.repair_check)}
    elif state.restate_check is not None and isinstance(data, dict):
        data = {**data, "check": merge_restated_check(
            state.restate_check[0], data.get("check"), state.restate_check[1],
        )}
    try:
        written, persisted = _task_result.persist_result_bytes(
            plan.task, plan.phase_dir, data)
    except _task_outcome.ResultRejected as exc:
        # The byte cap, not the shape: the document validated, so a
        # re-ask quoting "the validator's errors" would quote none
        # and tell the runner its reply has the wrong shape. Rung 6 stays terminal for it.
        return replace(reading, status=exc.status, error=exc.message, data=None), None
    outcome.output_path = written
    outcome.result_sha256 = (
        hashlib.sha256(persisted).hexdigest() if persisted is not None else None
    )
    reading = replace(reading, data=data)
    reply = hook_context("reply", plan, outcome, state=state, reading=reading)
    resend_why = (
        _ask_nothing_changed(hooks.nothing_changed, reply)
        if ladder.resends_left > 0 else None
    )
    if resend_why:
        resend = ladder.record_resend()
        if resend.retry:
            return reading, _start_resend(
                plan, hooks, state, outcome, reading, resend_why, reply
            )
        state.refuse_resend(resend.note)
    reask_why = (
        _ask_incomplete_report(hooks.incomplete_report, reply)
        if hooks.incomplete_report is not None and not resend_why
        and state.repair is None
        and ladder.schema_repairs_left > 0 else None
    )
    # Or its own check holds an accepted
    # finding with words added; the same one re-ask.
    restate = (
        _ask_restate_findings(hooks.restate_findings, reply)
        if hooks.restate_findings is not None and not reask_why
        and not resend_why and state.repair is None
        and ladder.schema_repairs_left > 0 else None
    )
    if restate is not None:
        reask_why = restate[0]
    reask = (
        _incomplete_report_reask(
            kind=plan.kind, prompt=plan.prompt, task=plan.task,
            why=reask_why, provider=plan.provider, model=plan.model,
            capture=reading.capture, transport=plan.transport,
            profile=plan.profile, ladder=ladder,
            tree_fingerprint=hooks.tree_fingerprint,
            fingerprint_context=hook_context("tree_fingerprint", plan, outcome),
            budget_kwargs=plan.budget_kwargs,
            restate_findings=restate is not None,
        ) if reask_why else None
    )
    if reask is None:
        return reading, None
    return reading, _start_report_reask(
        plan, hooks, state, outcome, reading, reask, reask_why, restate
    )


def _start_resend(
    plan: DispatchPlan,
    hooks: DispatchHooks,
    state: AttemptState,
    outcome: _task_outcome.TaskOutcome,
    reading: AttemptReading,
    resend_why: str,
    reply: Dict[str, Any],
) -> Next:
    """Rule 9: nothing moved, so the batch goes again, told so; this attempt
    is recorded ``batch_failed`` with a failure capture, not classified."""
    _record_attempt(outcome, hooks.after_attempt, _attempt_row(
        state, reading, STATUS_BATCH_FAILED, error=resend_why,
        capture_path=_capture_attempt(
            plan, state, reading, STATUS_BATCH_FAILED, resend_why
        ),
    ))
    outside = [str(path) for path in (reply.get("moved_outside") or [])]
    data = reading.data
    state.start_resend(build_nothing_changed_resend_prompt(
        plan.prompt,
        declared=_nothing_changed_files(plan.task, plan.cwd),
        named=[
            str(path) for path in
            (data.get("files_touched") or [])
            if isinstance(path, str)
        ] if isinstance(data, dict) else [],
        outside=outside,
    ))
    print(
        f"[exec-subagents] {plan.task_id}: the reply says the "
        f"batch was applied, but "
        f"{'none of the files it declares changed' if outside else 'no file changed'}; "
        f"sending the batch to {plan.runner} once more, "
        f"told so (attempt {reading.index + 1}). What "
        f"was applied is still decided by comparing "
        f"the files with the pre-batch snapshot."
    )
    return Next.retry(reading.status, reading.error)


def _start_report_reask(
    plan: DispatchPlan,
    hooks: DispatchHooks,
    state: AttemptState,
    outcome: _task_outcome.TaskOutcome,
    reading: AttemptReading,
    reask: Tuple[str, Any],
    reask_why: str,
    restate: Optional[Tuple[str, List[str]]],
) -> Next:
    """Rule 7, second form: the report read but left items
    out, or restated an accepted finding; the runner restates
    it once. The attempt keeps its own status and no failure capture (a readable report,
    which the re-ask's prompt file quotes)."""
    reask_prompt, baseline = reask
    data = reading.data
    restate_check = state.restate_check
    if restate is not None:
        # Only its findings and note may
        # change, and only as `merge_restated_check` lets.
        original = data.get("check") if isinstance(data, dict) else None
        restate_check = (
            (copy.deepcopy(original), [str(a) for a in restate[1]])
            if isinstance(original, dict) else None
        )
        repair_check = None
    else:
        repair_check = _batch_reply._report_check_evidence(data)
    _record_attempt(outcome, hooks.after_attempt, _attempt_row(
        state, reading, STATUS_INCOMPLETE_REPORT, error=reask_why,
    ))
    state.start_report_reask(
        reask_prompt, baseline, repair_check=repair_check,
        restate_check=restate_check,
        fallback=hook_context("reask_fallback", plan, outcome, state=state, reading=reading),
    )
    if restate is not None:
        print(
            f"[exec-subagents] {plan.task_id}: its own check "
            f"reports a finding the user accepted with "
            f"words added; asking {plan.runner} once to restate "
            f"its report without touching any file (report "
            f"re-ask, attempt {reading.index + 1}). Nothing "
            f"is recorded as accepted unless the restated "
            f"finding is the accepted one, word for word."
        )
        return Next.retry(reading.status, reading.error)
    print(
        f"[exec-subagents] {plan.task_id}: the batch's report "
        f"leaves some of its items out of both `ids` and "
        f"`declined`; asking {plan.runner} once to restate it "
        f"without touching any file (report re-ask, "
        f"attempt {reading.index + 1}). What was applied is "
        f"still decided by comparing the files with the "
        f"pre-batch snapshot."
    )
    return Next.retry(reading.status, reading.error)


def finish_ok(
    plan: DispatchPlan,
    hooks: DispatchHooks,
    state: AttemptState,
    ladder: RetryLadder,
    outcome: _task_outcome.TaskOutcome,
    reading: AttemptReading,
) -> _task_outcome.TaskOutcome:
    """Accept a schema-valid, persisted reply: its row (the observer sees it
    before its usage is counted), ``after_result``, and the exit-code note."""
    capture = reading.capture
    _record_attempt(
        outcome, hooks.after_attempt, _attempt_row(state, reading, STATUS_OK),
        notify_first=True,
    )
    outcome.status = STATUS_OK
    outcome.duration_seconds = ladder.elapsed()
    if hooks.after_result is not None:
        # D3g: the model's claim is never the verdict. The
        # snapshot/diff classification runs HERE — after rung 6, so
        # a prose result has already failed as `schema_invalid` and
        # can never be classified as "applied".
        hooks.after_result(hook_context(
            "result", plan, outcome, state=state, reading=reading,
        ))
        if not outcome.ok:
            _note_held_pipe(outcome, capture)
            return outcome
    if capture.exit_code not in (0, None):
        # Exit code is evidence, never the verdict: for a read
        # task a schema-valid result wins over a non-zero exit
        # (several CLIs exit non-zero on a warning while still
        # printing the answer), and the anomaly stays visible
        # here rather than being either fatal or invisible.
        outcome.reason = (
            f"runner exited {capture.exit_code} but produced a "
            f"schema-valid result; stderr tail: "
            f"{_failure_capture._tail(capture.stderr, 2000)!r}"
        )
    _note_held_pipe(outcome, capture)
    return outcome


def _note_held_pipe(outcome: _task_outcome.TaskOutcome, capture: Any) -> None:
    """The runner's own answer stands once what it left holding its output
    was stopped with its group before the checks; the row says so
    (``dispatch_spawn.pipe_held_note``;
    docs/development/runtime.md#process-primitives)."""
    held = _dispatch_spawn.pipe_held_note(capture)
    if held:
        outcome.reason = f"{outcome.reason}; {held}" if outcome.reason else held


def check_moved_before_retry(
    plan: DispatchPlan,
    hooks: DispatchHooks,
    state: AttemptState,
    ladder: RetryLadder,
    outcome: _task_outcome.TaskOutcome,
    reading: AttemptReading,
) -> Tuple[AttemptReading, RetryGuard]:
    """The write path's pre-retry check (T4.8, widened).

    A write attempt the ladder could answer by sending the batch's own
    prompt again — a timeout, a runner error, a prose reply, a rate limit —
    is asked first whether it already moved bytes. If it did, the batch is
    never sent again on top of its own edits: the attempt is a partial
    application, or, for a write kind whose reply could not be read, the one
    report re-ask (rule 7), which restates the report and edits nothing. A
    re-ask in flight is exempt: its retry re-sends the re-ask, and
    :func:`read_attempt` already fails one that moved a file. Anything else
    passes through unchanged.
    """
    status, error = reading.status, reading.error
    if not (
        (status in RETRYABLE_STATUSES or status in BACKOFF_STATUSES)
        and plan.profile == PROFILE_AGENT_WRITE
        and hooks.changed_files is not None
        and state.repair is None
    ):
        return reading, RetryGuard()
    checked_status, checked_error = _denied_write_turn(
        hooks.changed_files, error,
        hook_context("changed_files", plan, outcome, reading=reading),
        status=status,
    )
    if checked_status != STATUS_PARTIAL:
        return reading, RetryGuard()
    partial_if_refused: Optional[str] = None
    reply_text: Optional[str] = None
    if status == STATUS_UNPARSEABLE and ladder.schema_repairs_left > 0:
        reply_text = _attempt_classifier._reply_text(plan.provider, reading.capture.stdout)
        if _write_report_repairable(reading.capture, reply_text, hooks.tree_fingerprint):
            partial_if_refused = checked_error
    if partial_if_refused is None:
        # A batch killed at its time limit after its
        # edits landed is said so on the stop, edits kept.
        outcome.ran_out_of_time = status == STATUS_TIMEOUT
        status, error = checked_status, checked_error
    return (
        replace(reading, status=status, error=error, reply_text=reply_text),
        RetryGuard(repeatable=False, partial_if_refused=partial_if_refused),
    )


def record_failed_attempt(
    plan: DispatchPlan,
    hooks: DispatchHooks,
    state: AttemptState,
    outcome: _task_outcome.TaskOutcome,
    reading: AttemptReading,
) -> AttemptReading:
    """Record an attempt that did not succeed: why an ordinary permission
    error is not the jail's, its ``failed/`` capture and its row. Returns
    the reading with the error the row recorded."""
    capture = reading.capture
    error = reading.error
    evidence = getattr(capture, "jail_evidence", None) or {}
    if (
        reading.status != STATUS_OK
        and not getattr(capture, "jail_denied_line", None)
        and evidence.get("class") == landlock_dispatch.JAIL_CLASS_ORDINARY
    ):
        # An EACCES the parent classified as an ordinary permission error
        # (inside an allow entry, or unwritable by the user too): the
        # attempt fails as it always did, and says why it is not the jail.
        error = (
            f"{error} (not a jail denial: "
            f"{evidence.get('reason') or 'ordinary permission error'})"
        )
    reading = replace(reading, error=error)
    _record_attempt(outcome, hooks.after_attempt, _attempt_row(
        state, reading, reading.status, error=error,
        capture_path=_capture_attempt(plan, state, reading, reading.status, error),
    ))
    return reading


def decide_next(
    plan: DispatchPlan,
    hooks: DispatchHooks,
    state: AttemptState,
    ladder: RetryLadder,
    outcome: _task_outcome.TaskOutcome,
    reading: AttemptReading,
    guard: RetryGuard,
) -> Next:
    """The ladder's decision on a recorded attempt, and what it costs: the
    schema-repair re-ask's prompt, or the backoff sleep."""
    status, error = reading.status, reading.error
    capture = reading.capture
    data = reading.data
    reply_text = reading.reply_text
    # One `record` call is the whole decision (D3k rules 2/3/6): rung 1
    # is fatal to the batch; rung 3 backs off with jitter, at most three
    # times, without consuming the transport budget; rungs 2/4/5 spend
    # `driver.subagent_retries`; rungs 6/7 are never retried — rung 6 only
    # once the kind's schema-repair allowance (rule 7) is spent or was never
    # granted. Every one of those decisions is taken against the same
    # deadline the spawns are charged to, which is what keeps the counters a
    # ceiling the wall clock usually reaches first.
    # A schema-invalid attempt with no extracted document is the CLI's own
    # exhausted structured-output budget (the CLI already spent the
    # pinned re-ask), so it is not repairable here either; nor is a valid
    # document `persist_result` refused for its size (`data` dropped).
    repairable = data is not None
    if repairable and status == STATUS_SCHEMA_INVALID and plan.kind in WRITE_KINDS:
        # A write kind's re-ask restates the runner's own previous reply, so
        # it needs that reply, the hook that proves it moved nothing, and an
        # attempt the jail denied nothing in (its verdict would otherwise
        # be read off the re-ask's clean stream instead).
        reply_text = _attempt_classifier._reply_text(plan.provider, capture.stdout)
        repairable = _write_report_repairable(
            capture, reply_text, hooks.tree_fingerprint
        )
    if guard.partial_if_refused is not None:
        # A prose reply after edits (the pre-retry check): the same
        # re-ask an unreadable report gets, never the batch again.
        repairable = True
    # A stop the adapter's stdout watch asked for is never sent again
    # (rule 10; docs/development/providers.md#a-cli-that-loops).
    action = ladder.record(
        status, repairable=repairable, repeatable=guard.repeatable,
        stream_stopped=bool(getattr(capture, "stream_stop", None)),
    )
    if guard.partial_if_refused is not None and not action.retry:
        # The re-ask was refused for want of budget: the edits stay
        # unverified, so the attempt ends as the partial application the
        # check found, with the ladder's reason appended.
        error = guard.partial_if_refused
        if action.note:
            error = f"{error} ({action.note})"
        return Next.stop(STATUS_PARTIAL, error)
    if action.retry and action.repair:
        return _start_schema_repair(
            plan, hooks, state, outcome, reading, guard, reply_text
        )
    if action.retry:
        if action.delay:
            # The ladder computes the delay — it is pure, so the test switch
            # cannot live there. Applying the hook *here*, at the one place
            # this lane really sleeps, keeps MULTI_LLM_TEST_FAST_BACKOFF=1 an
            # exact 10 ms without putting an env read in the policy object.
            hooks.sleep(_apply_backoff_hook(action.delay))
        return Next.retry(status, error)
    if action.note:
        # A retry, backoff or schema-repair re-ask the status earned and the
        # budget refused (rule 3's deadline or rule 4's declared envelope):
        # the retry budget is not the only budget, and without the note the
        # recorded reason names a failure the harness had, and did not
        # spend, an attempt for. The unused counts are the ladder's own.
        error = f"{error} ({action.note})"
    return Next.stop(status, error)


def _start_schema_repair(
    plan: DispatchPlan,
    hooks: DispatchHooks,
    state: AttemptState,
    outcome: _task_outcome.TaskOutcome,
    reading: AttemptReading,
    guard: RetryGuard,
    reply_text: Optional[str],
) -> Next:
    """The one schema-repair re-ask the ladder granted: same runner, same
    deadline, or a stop when its prompt or its write guard cannot go out.

    A read kind gets the original prompt plus what was wrong and the reply
    shape; a write kind gets only its own previous reply to restate, never
    the batch's instructions again. The errors are re-read from the
    extracted document, because the status line keeps only five, and a
    reply that is not valid JSON is told so instead of being handed the
    errors of a fragment from inside it. A prose reply has no document: its
    own error is the one problem. A write kind's re-ask lists the batch's
    ids in prompt order, so a reply that numbered its items ("Suggestion 1:
    …") restates them by id.
    """
    status, error = reading.status, reading.error
    kind = plan.kind
    data = reading.data
    problems = _task_result.validate_result(kind, data) if data is not None else []
    syntax = reading.capture.reply_syntax_error
    repair_prompt = build_schema_repair_prompt(
        kind, plan.prompt, problems or [error], syntax_error=syntax,
        **({
            "previous_reply": reply_text,
            "expected_ids": [
                str(item) for item in plan.task.get("expected_ids") or []
            ],
        } if kind in WRITE_KINDS else {}),
    )
    too_long = _prompt_over_budget(
        plan.provider, plan.model, repair_prompt, plan.transport, plan.profile,
        **plan.budget_kwargs,
    )
    if too_long is not None:
        if guard.partial_if_refused is not None:
            status, error = STATUS_PARTIAL, guard.partial_if_refused
        return Next.stop(status, f"{error} (no schema-repair re-ask: {too_long})")
    write_guard = None
    if kind in WRITE_KINDS:
        try:
            baseline = hooks.tree_fingerprint(  # type: ignore[misc]
                hook_context("tree_fingerprint", plan, outcome)
            )
        except Exception as exc:  # noqa: BLE001 - fail closed: no re-ask
            if guard.partial_if_refused is not None:
                status, error = STATUS_PARTIAL, guard.partial_if_refused
            return Next.stop(status, (
                f"{error} (no report re-ask: the files' state before it "
                f"could not be recorded, {type(exc).__name__})"
            ))
        write_guard = (baseline, _batch_reply._report_check_evidence(data))
    state.start_schema_repair(repair_prompt, write_guard)
    if kind in WRITE_KINDS:
        print(
            f"[exec-subagents] {plan.task_id}: the batch's closing report "
            f"could not be read; asking {plan.runner} once to restate it "
            f"without touching any file (report re-ask, attempt "
            f"{reading.index + 1}). What was applied is still decided "
            f"by comparing the files with the pre-batch snapshot."
        )
    else:
        print(
            f"[exec-subagents] {plan.task_id}: the reply "
            + ("is not valid JSON" if syntax else
               f"does not match the {kind} result shape "
               f"({len(problems) or 1} problem(s))")
            + f"; re-asking {plan.runner} once with what was wrong "
            f"(schema repair, attempt {reading.index + 1})."
        )
    return Next.retry(status, error)


def close_outcome(
    plan: DispatchPlan,
    hooks: DispatchHooks,
    state: AttemptState,
    ladder: RetryLadder,
    outcome: _task_outcome.TaskOutcome,
    stop: Next,
) -> _task_outcome.TaskOutcome:
    """The outcome a stopped dispatch ends with: the report a report re-ask
    could not restate, classified as it stands, or the stop's own verdict."""
    status, error = stop.status, stop.error
    if (
        state.reask_fallback is not None and hooks.after_result is not None
        and status != STATUS_PARTIAL
    ):
        # The re-ask of a report that left items out could not
        # restate it (prose, a timeout, a refused runner) and moved nothing,
        # so the report the batch did send is classified as it stands.
        outcome.status = STATUS_OK
        outcome.duration_seconds = ladder.elapsed()
        hooks.after_result({
            **state.reask_fallback,
            "duration_seconds": outcome.duration_seconds,
            "outcome": outcome,
        })
        outcome.reason = (
            f"{outcome.reason or ''} (its report re-ask did not restate the "
            f"report: {error})"
        ).strip()
        return outcome
    if state.repair and status in (STATUS_SCHEMA_INVALID, STATUS_UNPARSEABLE):
        error = f"{error} (after the one schema-repair re-ask)"
    outcome.status = status
    outcome.reason = error
    outcome.duration_seconds = ladder.elapsed()
    return outcome


def _attempt_row(
    state: AttemptState,
    reading: AttemptReading,
    status: str,
    *,
    error: Optional[str] = None,
    capture_path: Optional[str] = None,
) -> _task_outcome.Attempt:
    """One spawned attempt's row in the batch report."""
    capture = reading.capture
    return _task_outcome.Attempt(
        index=reading.index,
        status=status,
        exit_code=capture.exit_code,
        duration_seconds=capture.duration,
        error=error,
        usage=reading.usage,
        capture_path=capture_path,
        repair=state.repair_tag,
    )


def _capture_attempt(
    plan: DispatchPlan,
    state: AttemptState,
    reading: AttemptReading,
    status: str,
    error: Optional[str],
) -> Optional[str]:
    """Write one unaccepted attempt's ``failed/`` capture; its path."""
    capture = reading.capture
    return _failure_capture._write_failure_capture(
        phase_dir=plan.phase_dir,
        task=plan.task,
        attempt_index=reading.index,
        argv=capture.argv,
        # The prompt this attempt really sent, so the argv elision below
        # still finds it on an argv-transport runner's re-ask.
        prompt=state.prompt,
        stdout=capture.stdout,
        stderr=capture.stderr,
        exit_code=capture.exit_code,
        duration=capture.duration,
        status=status,
        error=error,
        repair=state.repair_tag,
    )


def _record_attempt(
    outcome: _task_outcome.TaskOutcome,
    after_attempt: Optional[Callable[[_task_outcome.Attempt], None]],
    attempt: _task_outcome.Attempt,
    *,
    notify_first: bool = False,
) -> None:
    """Add *attempt*'s row, count its usage (D3j) and hand it to the
    observer, before the ladder decides and before any backoff sleep, so
    a caller that narrows on a rate limit reacts while this task is still
    retrying.

    The observer sees the outcome's usage with this attempt counted, except
    for the accepted attempt (*notify_first*), which it sees before.
    """
    outcome.attempts.append(attempt)
    if notify_first:
        _notify_after_attempt(after_attempt, attempt)
        _accumulate_usage(outcome, attempt.usage)
        return
    _accumulate_usage(outcome, attempt.usage)
    _notify_after_attempt(after_attempt, attempt)


def _denied_write_turn(
    changed_files: Callable[[Dict[str, Any]], Sequence[str]],
    error: str,
    context: Dict[str, Any],
    *,
    status: str = STATUS_RUNNER_ERROR,
) -> Tuple[str, str]:
    """``(status, reason)`` for a failed write attempt a retry would re-send.

    T4.8 asked it for a turn a denial ended (``runner_error``); it is asked for every
    write attempt whose ``status`` the ladder
    could answer with the batch's own prompt again (a timeout, a prose reply,
    a rate limit). With changed files, ``partial_application`` in the
    scheduler's own words (``PARTIAL APPLICATION: …``, stop the loop, keep the
    snapshot, do not complete the phase), never retried because the status is
    on no rung. With none, ``status`` and ``error`` unchanged, retried as
    before.
    """
    try:
        changed = [str(path) for path in (changed_files(context) or ())]
    except Exception as exc:  # noqa: BLE001 - fail closed, never retry blind
        return STATUS_PARTIAL, (
            f"PARTIAL APPLICATION (unverified): the attempt failed ({error}), "
            f"and the working tree could not be compared with the pre-batch "
            f"snapshot ({type(exc).__name__}), so no further attempt is "
            f"started — a retry would send the whole batch again on top of "
            f"whatever it already edited. The batch loop stops here and the "
            f"phase is NOT marked completed."
        )
    if not changed:
        return status, error
    shown = ", ".join(changed[:5]) + (", …" if len(changed) > 5 else "")
    return STATUS_PARTIAL, (
        f"PARTIAL APPLICATION: {len(changed)} file(s) changed ({shown}), but "
        f"the attempt failed ({error}). No further attempt is started — a "
        f"retry would send the whole batch again on top of those edits. The "
        f"batch loop stops here and the phase is NOT marked completed."
    )


def _ask_write_hook(
    hook: Optional[Callable[[Dict[str, Any]], Any]],
    context: Dict[str, Any],
    what: str,
) -> Any:
    """A write-lane hook's answer, or ``None`` when there is no hook or it raised.

    Fail closed: a re-send or a report re-ask is sent only on an answer, never
    on "could not tell", so a hook that raises leaves the reply to be
    classified as it stands. *what* finishes the warning's "could not tell
    whether <task id>…".
    """
    if hook is None:
        return None
    try:
        return hook(context)
    except Exception as exc:  # noqa: BLE001 - no re-send or re-ask without an answer
        print(
            f"[exec-subagents] warning: could not tell whether "
            f"{context.get('task_id')}{what} "
            f"({type(exc).__name__}); its reply is classified as it stands.",
            file=sys.stderr,
        )
        return None


def _ask_nothing_changed(
    hook: Optional[Callable[[Dict[str, Any]], Optional[str]]],
    context: Dict[str, Any],
) -> Optional[str]:
    """Rule 9's question to the write lane's ``nothing_changed`` hook: a
    re-send is granted only on a measured "not one byte moved"."""
    answer = _ask_write_hook(hook, context, " changed any file")
    return str(answer) if answer else None


def _nothing_changed_files(task: Dict[str, Any], cwd: Optional[str]) -> List[str]:
    """The batch's declared files, relative to *cwd* when they lie under it,
    for the rule-9 re-send's prompt."""
    names: List[str] = []
    for path in declared_file_set(task):
        if cwd and os.path.isabs(path):
            try:
                relative = os.path.relpath(path, cwd)
            except ValueError:  # pragma: no cover - another drive on Windows
                relative = path
            if not relative.startswith(".."):
                path = relative
        names.append(path.replace(os.sep, "/"))
    return names


def _ask_incomplete_report(
    hook: Optional[Callable[[Dict[str, Any]], Optional[str]]],
    context: Dict[str, Any],
) -> Optional[str]:
    """The ``incomplete_report`` hook's answer: why a readable write report
    leaves items out, or ``None``."""
    answer = _ask_write_hook(
        hook, context, "'s report accounts for every item"
    )
    return str(answer) if answer else None


def _ask_restate_findings(
    hook: Optional[Callable[[Dict[str, Any]], Optional[Tuple[str, Sequence[str]]]]],
    context: Dict[str, Any],
) -> Optional[Tuple[str, List[str]]]:
    """The ``restate_findings`` hook's answer: ``(problem,
    accepted findings)``, or ``None`` (no hook, no answer or a malformed one)."""
    answer = _ask_write_hook(
        hook, context, "'s check findings need restating"
    )
    if not answer or len(answer) != 2 or not str(answer[0] or "").strip():
        return None
    allowed = [str(item) for item in (answer[1] or []) if str(item).strip()]
    return (str(answer[0]), allowed) if allowed else None


def merge_restated_check(
    original: Dict[str, Any], restated: Any, allowed: Sequence[str],
) -> Dict[str, Any]:
    """The ``check`` a restated report is classified with:
    the first report's whole ``check`` — ``passed``, ``ran``, ``listed``,
    everything its checks observed, as :func:`_report_check_evidence` keeps
    it across any report-only turn — with only two things taken from the
    restatement:

    * its ``findings``, when every finding of the first report it changed
      was cut down to one of *allowed* (the accepted findings the re-ask
      named), whitespace aside, that the changed finding held word for word,
      and the words cut are in its ``note`` (case and punctuation aside), so
      nothing a finding said leaves the record. A restatement that drops a
      finding, rewords one, turns the check into a pass or cuts words it
      does not move to its note keeps the first report's findings: a
      report-only turn ran no check, so it can say less about one only by
      moving the words the re-ask named to the note. A finding it adds is
      kept.
    * its ``note``, when it is a non-blank string.

    Never a classification: what is accepted is still decided by
    ``check_records.split_accepted_findings`` on what this returns.
    """
    merged = copy.deepcopy(original)
    if not isinstance(restated, dict):
        return merged

    def plain(text: Any) -> str:
        return " ".join(str(text or "").split())

    def words(text: Any) -> str:
        return " ".join(re.findall(r"[a-z0-9]+", str(text or "").lower()))

    note = restated.get("note")
    note_words = words(note) if isinstance(note, str) else ""

    def moved_to_note(old: str, new: str) -> bool:
        head, _, tail = plain(old).partition(plain(new))
        return all(words(part) in note_words for part in (head, tail) if words(part))

    before = _batch_reply.batch_check_findings({"check": original}) or []
    candidate = copy.deepcopy(original)
    candidate["findings"] = copy.deepcopy(restated.get("findings"))
    after = _batch_reply.batch_check_findings({"check": candidate}) or []
    accepted = {plain(item) for item in allowed if plain(item)}
    changed = [finding for finding in before if finding not in after]
    added = [finding for finding in after if finding not in before]
    cut_down = all(
        any(
            plain(new) in accepted and plain(new) in plain(old)
            and moved_to_note(old, new)
            for new in added
        )
        for old in changed
    )
    if after and cut_down:
        merged["findings"] = candidate["findings"]
    if isinstance(note, str) and note.strip():
        merged["note"] = note
    return merged


def _incomplete_report_reask(
    *,
    kind: str,
    prompt: str,
    task: Dict[str, Any],
    why: str,
    provider: Any,
    model: str,
    capture: Any,
    transport: str,
    profile: str,
    ladder: RetryLadder,
    tree_fingerprint: Optional[Callable[[Dict[str, Any]], Any]],
    fingerprint_context: Dict[str, Any],
    budget_kwargs: Dict[str, Any],
    restate_findings: bool = False,
) -> Optional[Tuple[str, Any]]:
    """``(re-ask prompt, files' state)`` when the report re-ask for an
    incomplete report may go out, else ``None``.

    The same guards as the rule-7 re-ask of an unreadable report: a reply to
    quote, the hook that proves the re-ask moved nothing, no jail denial on
    the attempt's stream, a prompt the transport carries — and then the
    ladder's grant, which spends the schema-repair allowance. Any guard that
    does not hold leaves the reply to be classified as it stands.
    *restate_findings* asks for the restatement of a check
    finding instead of the items' account (the re-ask prompt's
    ``restate_findings`` form); the guards and the grant are the same.
    """
    reply_text = _attempt_classifier._reply_text(provider, capture.stdout)
    if not _write_report_repairable(capture, reply_text, tree_fingerprint):
        return None
    reask_prompt = build_schema_repair_prompt(
        kind, prompt, [why], previous_reply=reply_text,
        expected_ids=[str(item) for item in task.get("expected_ids") or []],
        incomplete=not restate_findings, restate_findings=restate_findings,
    )
    if _prompt_over_budget(
        provider, model, reask_prompt, transport, profile, **budget_kwargs,
    ) is not None:
        return None
    try:
        baseline = tree_fingerprint(fingerprint_context)  # type: ignore[misc]
    except Exception:  # noqa: BLE001 - fail closed: no re-ask
        return None
    if not ladder.record_report_reask().retry:
        return None
    return reask_prompt, baseline


def _write_report_repairable(
    capture: Any,
    reply_text: Optional[str],
    tree_fingerprint: Optional[Callable[[Dict[str, Any]], Any]],
) -> bool:
    """Whether a write attempt's unreadable report may be re-asked (rule 7).

    All three, or rung 6 stays terminal exactly as before: a previous reply to
    restate, the hook that proves the re-ask moved nothing, and a stream the
    plugin's jail recorded no denial on — the jail's verdict is read off the
    attempt's own stream, so a re-ask with a clean stream would launder it.
    """
    if tree_fingerprint is None or not (reply_text or "").strip():
        return False
    denials = getattr(capture, "jail_denials", None)
    if denials is not None and getattr(denials, "total", 0):
        return False
    return True


def _moved_during_repair(
    tree_fingerprint: Optional[Callable[[Dict[str, Any]], Any]],
    context: Dict[str, Any],
    baseline: Any,
) -> Optional[List[str]]:
    """The paths a report re-ask moved, or ``None`` when it moved nothing.

    A hook that raises is "could not tell", which fails closed as a move.
    """
    if tree_fingerprint is None:  # pragma: no cover - a baseline needs the hook
        return ["<the files could not be compared>"]
    try:
        after = tree_fingerprint(context)
    except Exception as exc:  # noqa: BLE001 - fail closed
        return [f"<the files could not be compared: {type(exc).__name__}>"]
    if after == baseline:
        return None
    if isinstance(after, dict) and isinstance(baseline, dict):
        moved = sorted(
            str(path) for path in set(after) | set(baseline)
            if after.get(path) != baseline.get(path)
        )
        return moved or ["<the files could not be compared>"]
    return ["<the files could not be compared>"]


def _prompt_over_budget(
    provider: Any,
    model: str,
    prompt: str,
    transport: str,
    profile: str,
    *,
    sandbox_fallback: Optional[str] = None,
    jail_request: Optional[JailRequest] = None,
) -> Optional[str]:
    """Why ``prompt`` cannot travel this runner's argv, or ``None`` (D2d).

    The budget is a Windows command-line constraint, so a ``stdin``/``file``
    transport is unbounded and this is a no-op there. For an argv-only runner it
    measures the *rendered* non-prompt argv too, because that is what Windows
    actually limits — and it resolves ``argv[0]`` exactly as :func:`_spawn` does,
    because an npm ``.cmd``/``.bat`` shim is run by cmd.exe and therefore carries
    the 8,191-unit cap rather than ``CreateProcess``'s 32,767. The same resolution
    answers the second cmd.exe hazard: the shim's command line is *reparsed*, so a
    metacharacter-bearing prompt is refused here rather than handed to that
    reparse (BatBadBut / CVE-2024-24576 class), mirroring ``llm_client``'s guard
    on the fan-out path.

    On the plugin's Landlock jail (``sandbox_fallback`` a wrapping rung; plan
    codex-sandbox-unavailable F1 "Dispatch shape" item 4, 2026-09-30) the
    argv measured is the WRAPPED one — the interpreter, the wrapper, the
    ``--allow`` entries and the rung's in-CLI atoms — rendered with
    placeholder paths, creating nothing: ``dispatch_spawn.render_audit_argv``,
    the renderer the audit record uses, with the executable resolved where the
    spawn resolves it.
    """
    if transport in ("stdin", "file"):
        return None
    shim = {"batch": False}

    def resolve(executable: str) -> List[str]:
        try:
            launcher, shim["batch"] = _resolve_executable(executable)
        except OSError:  # pragma: no cover - PATH probe failure is not a refusal
            launcher, shim["batch"] = [executable], False
        return launcher

    # Only a wrapping rung is measured: the callers hand one over for the jail
    # alone (`DispatchPlan.budget_kwargs`).
    wrapping = _dispatch_spawn._wrapping_rung(provider, profile, sandbox_fallback)
    try:
        rendered = _dispatch_spawn.render_audit_argv(
            provider, model, profile, prompt,
            sandbox_fallback if wrapping is not None else None, jail_request,
            launcher=resolve,
        )
    except Exception:  # noqa: BLE001 - a budget probe must not mask a refusal
        return None
    is_batch_shim = shim["batch"]
    if is_batch_shim:
        unsafe = sorted(set(prompt) & _CMD_UNSAFE_CHARS)
        if unsafe:
            chars = ", ".join(repr(ch) for ch in unsafe)
            return (
                f"{provider.name} resolves to a cmd.exe batch shim "
                f"({rendered[0]}) and delivers the prompt on argv, but the "
                f"prompt contains cmd.exe metacharacters ({chars}). cmd.exe "
                f"reparses the shim's command line, so these characters could "
                f"corrupt the prompt or escape into executed commands "
                f"(BatBadBut / CVE-2024-24576 class). Install a native "
                f"executable for this runner, or configure a runner with a "
                f"stdin/file prompt transport (driver.subagent_runner). "
                f"Nothing was dispatched."
            )
    # Measure the argv `_spawn` will actually run: the resolved launcher, not the
    # adapter's bare command name.
    non_prompt = [arg for arg in rendered if arg != prompt]
    # Through the module, at each call: tests patch `subagent_tasks.prompt_budget_utf16`.
    ceiling = _subagent_tasks.prompt_budget_utf16(
        transport=transport,
        non_prompt_argv=non_prompt,
        is_batch_shim=is_batch_shim,
    )
    if ceiling is None:
        return None
    units = _subagent_tasks.utf16_units(prompt)
    if units <= ceiling:
        return None
    launcher_kind = (
        "a .cmd/.bat shim run via cmd.exe (8,191-unit command-line cap)"
        if is_batch_shim
        else "a native executable (32,767-unit CreateProcess cap)"
    )
    return (
        f"its prompt is {units} UTF-16 code units but {provider.name} delivers "
        f"the prompt on argv through {launcher_kind}, where this platform allows "
        f"{ceiling}. Configure a runner with a stdin/file prompt transport "
        f"(driver.subagent_runner). The prompt is never truncated. Nothing was "
        f"dispatched."
    )


def _apply_backoff_hook(delay: float) -> float:
    """Apply the ``MULTI_LLM_TEST_FAST_BACKOFF`` switch to a computed delay.

    The rung-3 arithmetic and its jitter belong to
    :func:`utils.retry_ladder.backoff_delay` — "equal jitter", half the
    exponential step deterministic and half random, so the N sibling tasks a
    shared provider throttled at the same moment never re-attempt in lockstep
    and re-trip the same limit together. That function is **pure**, which is the
    point: it reads no environment and keeps no import of this package, so the
    test switch cannot live inside it.

    It lives here instead, wrapping the delay at the one place this lane really
    sleeps. ``get_backoff_delay`` returns its argument unchanged outside
    ``MULTI_LLM_TEST_FAST_BACKOFF`` and an exact 10 ms under it — a jittered test
    suite would be both slower and nondeterministic.
    """
    return _concurrency.get_backoff_delay(delay)


def _safe_parse_usage(provider: Any, capture: _dispatch_spawn._Capture) -> Optional[Dict[str, Any]]:
    """``parse_usage`` that can never fail a dispatch (D3j)."""
    try:
        usage = provider.parse_usage(capture.stdout, capture.stderr)
    except Exception:  # noqa: BLE001 - metrics must not break the run
        return None
    if not isinstance(usage, dict) or not usage:
        return None
    return usage


def _notify_after_attempt(
    callback: Optional[Callable[[_task_outcome.Attempt], None]], attempt: _task_outcome.Attempt
) -> None:
    """Hand one recorded attempt to ``dispatch_task``'s observer.

    An observer can never fail the attempt it observes: whatever it raises is
    reported on stderr and dropped, and the attempt loop carries on exactly as
    if no callback had been passed.
    """
    if callback is None:
        return
    try:
        callback(attempt)
    except Exception as exc:  # noqa: BLE001 - an observer never fails a dispatch
        print(
            f"multi-llm warning: after_attempt callback failed on attempt "
            f"{attempt.index} ({type(exc).__name__}: {exc})",
            file=sys.stderr,
        )


def _record_unspawned_attempt(
    outcome: _task_outcome.TaskOutcome,
    attempt_index: int,
    error: str,
    after_attempt: Optional[Callable[[_task_outcome.Attempt], None]],
) -> None:
    """Record a rejected attempt that ``before_attempt`` admitted but that
    spawned nothing (the step-3 backstop, or a rung refused for want of its
    grant).

    ``before_attempt`` has already written the audit's ``dispatched`` line by
    then, and the write scheduler's ``_audit_terminal`` closes that line only
    when ``outcome.attempts`` is non-empty — its early return reads an empty
    list as "refused before the first ``before_attempt``". Without this row the
    ``dispatched`` entry would stay open for good, breaking D3l's one line
    before dispatch, one line after. ``exit_code`` is ``None``: no child ran.
    """
    _record_attempt(outcome, after_attempt, _task_outcome.Attempt(
        index=attempt_index,
        status=STATUS_REJECTED,
        exit_code=None,
        duration_seconds=0.0,
        error=error,
    ))


def _accumulate_usage(outcome: _task_outcome.TaskOutcome, usage: Optional[Dict[str, Any]]) -> None:
    """Accumulate usage across every attempt of one ``task_id`` (D3j).

    A timed-out or rate-limited attempt still burned tokens, so it counts. Absent
    stays absent: a runner that reports nothing records duration only.
    """
    if not usage:
        return
    outcome.usage_reported = True
    totals = dict(outcome.usage or {})
    for key, value in usage.items():
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            totals[key] = totals.get(key, 0) + value
    outcome.usage = totals
