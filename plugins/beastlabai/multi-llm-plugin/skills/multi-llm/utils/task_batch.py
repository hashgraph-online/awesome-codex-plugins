"""A batch of tasks: :func:`run_tasks`, its concurrency and what it
records.

Every runner's preflight once (:func:`_preflight_batch_runners`), the
D3i ceiling (:func:`effective_ceiling`), the dispatch order, the
concurrent fan-out over ``task_dispatch.dispatch_task`` (:func:`_gather`,
with provider backpressure after a rate limit and the judge audit), the
runners and provenance a re-run keeps (:func:`_recorded_runners`,
:func:`_recorded_provenance`), and the ``.status.json`` mirror.

``utils.subagent_executor`` re-exports every name defined here for reading
only: patch one here, never through the executor
(docs/development/delegation.md#where-the-executors-helpers-live).
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from . import concurrency as _concurrency
from . import host_capabilities as caps
from .provider_registry import (
    SESSION_LAYER,
    get_max_concurrent_subagents,
    get_provider,
    get_provider_max_concurrent,
    get_subagent_timeout,
    parse_model_spec,
)
from . import status_file as _status_file
from . import subagent_tasks as _subagent_tasks
from .providers.base import JailRequest
from .retry_ladder import (
    FATAL_STATUSES,
    STATUS_INCOMPLETE,
    STATUS_OK,
    STATUS_RATE_LIMITED,
    STATUS_REJECTED,
    STATUS_SCHEMA_INVALID,
    STATUS_UNPARSEABLE,
)
from .review_round import record_batch_provenance
from .subagent_tasks import task_round
from .write_safety import AuditLog
from . import task_outcome as _task_outcome
from . import task_result as _task_result
from . import runner_selection as _runner_selection
from . import probe_state as _probe_state
from . import dispatch_spawn as _dispatch_spawn
from . import runner_preflight as _runner_preflight
from . import task_dispatch as _task_dispatch


#: Statuses mirrored into ``.status.json`` under ``progress`` (display only).
_STATUS_MIRROR_KEY = "subagents"


def _host_ceiling() -> Optional[int]:
    """This host's ``max_concurrent_subagents``, or ``None`` if it cannot be read.

    ``sys.argv[1:]`` is passed for the same reason :func:`_host_env_guards` and
    :func:`_host_nested_exec` pass it: a shim declares its host by baking
    ``--host <id>`` into the dispatcher line, and ``$MULTI_LLM_HOST`` is only the
    *fallback* for a host that calls ``multi_llm.py`` directly (D5b). Reading the
    env alone made every argv-declared host answer the reference host's ceiling —
    an ``opencode`` run recorded ``host_max_concurrent_subagents: 10`` against an
    entry that declares 4 — so the one leg of D3i's minimum that is a fact about
    the host was silently the wrong host's.

    Deliberately non-fatal: the ceiling is a *bound*, and a partial install that
    cannot answer must not turn a dispatch into a hard failure — the driver and
    provider legs of the minimum still apply.
    """
    try:
        return caps.max_concurrent_subagents(caps.resolve_host_id(sys.argv[1:]))
    except Exception:  # pragma: no cover - unknown host / missing data
        return None


def effective_ceiling(
    runners: Sequence[str],
    *,
    anchor: Optional[str] = None,
    host_max: Optional[int] = None,
) -> Dict[str, Any]:
    """The three-way minimum, computed per dispatch and logged once (D3i).

    ``driver.max_concurrent_subagents`` (user) × the runner provider's
    ``max_concurrent`` × the host's own ceiling from the capability data. Returned
    as a record rather than a bare int so the batch report and the log line can
    both say *which* ceiling bound the batch.

    Args:
        host_max: The host's ``max_concurrent_subagents``. ``None`` means "look it
            up from ``hosts/capabilities.yaml`` for the host this invocation
            declared" (D5b) — the seam is this parameter, not a second code path,
            and a caller that already knows the number still passes it directly.
    """
    if host_max is None:
        host_max = _host_ceiling()
    driver_gate = get_max_concurrent_subagents(anchor=anchor)
    provider_limits: Dict[str, Optional[int]] = {}
    for spec in dict.fromkeys(runners):
        provider_name, _ = parse_model_spec(spec, anchor=anchor)
        provider_limits[provider_name] = get_provider_max_concurrent(
            provider_name, anchor=anchor
        )

    candidates = [driver_gate]
    if host_max is not None:
        candidates.append(host_max)
    limits = [limit for limit in provider_limits.values() if limit is not None]
    if limits:
        candidates.append(max(limits))
    effective = max(1, min(candidates))
    return {
        "effective": effective,
        "driver_max_concurrent_subagents": driver_gate,
        "host_max_concurrent_subagents": host_max,
        "provider_max_concurrent": {
            name: limit for name, limit in provider_limits.items()
        },
    }


# ---------------------------------------------------------------------------
# Batch orchestration
# ---------------------------------------------------------------------------

def _preflight_batch_runners(
    resolved: Dict[str, Tuple[str, str, str]],
    task_by_id: Dict[str, Dict[str, Any]],
    *,
    profile: str,
    anchor: Optional[str] = None,
    recorded: Optional[Dict[str, str]] = None,
    jail_request: Optional[JailRequest] = None,
) -> Tuple[Dict[str, str], Optional[Dict[str, str]]]:
    """Preflight each DISTINCT runner once; return its versions and any fallback.

    Presence, profile, version, auth, the CLI's own catalog and the host's
    nested-exec verdict, paid once per spec rather than once per task. A refusal
    is exit 3 before any child is dispatched, and it names the layer that
    supplied the spec — the first task's source for each distinct spec — rather
    than a ``driver.*`` key the user may never have written (D3 step 3).

    **One rung is allowed to fall through, and only one**: ``session``. That spec
    is the model the host session happens to be running on — nobody typed it into
    a config file, so a refusal is not a config error and refusing the batch over
    it would make "I switched the session model" a way to break a run that worked
    a minute ago. Whatever the reason code (``invalid_model_catalog``,
    ``not_authenticated``, a denied ``nested_exec`` leg, ``sandbox_unavailable``
    …), every task that was going to run on it is re-resolved with the session
    rung skipped, one line says so on stdout, and the *next* rung is preflighted
    under the ordinary rule. Explicit layers keep refusing exactly as before: an
    opinion an operator really expressed and that cannot be served is a config
    error, and silently substituting something else is how "I set it and nothing
    changed" begins.

    ``resolved`` is mutated in place, so the caller's runner map is the map the
    fallback produced.

    ``jail_request`` (plan codex-sandbox-unavailable step 3, 2026-09-30) is a
    write batch's grant, handed to every preflight so the sandbox leg decides
    for that scope; a read batch passes none.

    Returns:
        ``({spec: version}, fallback)`` where *fallback* is ``None`` or
        ``{"from", "reason", "to", "layer"}`` — the record
        ``subagent_batch_report.json`` carries so a substitution is visible after
        the fact. Per-task truth stays in ``tasks[].runner``; this names the
        first substitution, which in a homogeneous batch is the only one.
    """
    versions: Dict[str, str] = {}
    fallback: Optional[Dict[str, str]] = None
    while True:
        sources: Dict[str, Tuple[str, str, str]] = {}
        for task_id, (spec, key, layer) in resolved.items():
            sources.setdefault(spec, (task_id, key, layer))
        pending = [
            (spec, meta) for spec, meta in sources.items() if spec not in versions
        ]
        if not pending:
            return versions, fallback
        spec, (task_id, key, layer) = pending[0]
        try:
            versions[spec] = _runner_preflight.preflight_runner(
                spec, profile=profile, anchor=anchor, key=key, layer=layer,
                **({"jail_request": jail_request} if jail_request is not None else {}),
            )["version"]
            continue
        except _task_outcome.RunnerRejected as exc:
            if layer != SESSION_LAYER:
                raise
            # Bound out of the `except` block, which deletes `exc` on the way
            # out: the refusal has to survive to the impossible-branch re-raise.
            rejection, reason = exc, exc.reason_code or STATUS_REJECTED
        # Re-resolve every task that was going to run on the refused spec, each
        # through its own tier, so a `cheap` task lands on the cheap rung rather
        # than on whatever the first task got.
        replacement: Optional[Tuple[str, str, str]] = None
        for other_id, source in list(resolved.items()):
            if source[0] != spec:
                continue
            new_source = _runner_selection._resolve_task_source(
                task_by_id[other_id], anchor=anchor, recorded=recorded,
                skip_session=True,
            )
            resolved[other_id] = new_source
            if replacement is None:
                replacement = new_source
        if replacement is None:  # pragma: no cover - spec came from `resolved`
            raise rejection
        print(
            f"[exec-subagents] session model {spec} failed preflight "
            f"({reason}); falling back to {replacement[0]} ({replacement[2]})"
        )
        if fallback is None:
            fallback = {
                "from": spec,
                "reason": reason,
                "to": replacement[0],
                "layer": replacement[2],
            }


def _estimated_cost(task: Dict[str, Any]) -> int:
    """How expensive this task looks *before* it runs, for dispatch order only.

    The prompt's length is the whole of it. A subagent turn is dominated by the
    tokens the runner has to read and reason over, and for every materialized
    kind the prompt is where those tokens are: a validation batch's prompt
    carries its grouped suggestions inline, an implement task's carries its step.
    Nothing here reads the clock or the provider, so the estimate is free, stable
    across resumes and identical on every host.

    ``groups_count`` is the fallback for a task whose prompt is absent or
    non-textual — a coarser proxy for the same quantity — and ``0`` (dispatch it
    last, order unchanged among its peers) when neither says anything. This is a
    *ranking*, never a prediction: it is wrong only by mis-ordering a batch that
    would otherwise have been ordered by an accident of file position.
    """
    prompt = task.get("prompt")
    if isinstance(prompt, str) and prompt:
        return len(prompt)
    groups = task.get("groups_count")
    if isinstance(groups, int) and not isinstance(groups, bool) and groups > 0:
        return groups
    return 0


def _dispatch_order(tasks: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The same tasks, longest-first, for **dispatch scheduling only** (D3i).

    Longest-processing-time-first is the classic answer to the tail this fixes.
    The batch runs as ``ceil(tasks / parallelism)`` waves, so whatever is
    dispatched last runs with the lanes beside it emptying out; dispatch in file
    order and the last task in the file gets that slot no matter how big it is.
    The 2026-09-13 review-plan run is the worked example: eleven validation
    batches at parallelism 4, per-batch 237/960/1123/895/671/811/610/486/478/545/
    1076 s, ideal packing 1973 s, actual 2594 s — the 621 s gap is almost exactly
    batch 10 (1076 s) running alone at the end because it happened to be last in
    ``validation_tasks.json``. Dispatching it first puts it in the first wave,
    where three lanes run beside it.

    **Only the dispatch order changes.** Task ids, ``batch_index``,
    ``output_path``, the merge, and ``tasks[]`` in ``subagent_batch_report.json``
    all keep the task file's own order — :func:`run_tasks` re-indexes the
    outcomes by ``task_id`` against its original ``selected`` list, so this
    function's return value never reaches an artifact. The tie-break is the
    original index, so a batch whose tasks all estimate the same (or that has one
    task) is dispatched in exactly the order it always was.
    """
    ordered = sorted(
        enumerate(tasks), key=lambda row: (-_estimated_cost(row[1]), row[0])
    )
    if [index for index, _ in ordered] != list(range(len(tasks))):
        print(
            "[exec-subagents] dispatch order (longest first): "
            + ", ".join(
                str(task.get("task_id", index)) for index, task in ordered
            )
        )
    return [task for _index, task in ordered]


#: Row statuses whose recorded runner is not a pin for a re-run (fix round 8):
#: the reply-quality failures, rungs 5 and 6. See :func:`_recorded_runners`.
UNPINNED_ROW_STATUSES = frozenset({STATUS_SCHEMA_INVALID, STATUS_UNPARSEABLE})


def _pinned_runner_note(key: str, kind: str = "") -> str:
    """The dispatch line's reason when the runner is a recorded pin, else ``""``.

    A pin outranks every rung of the ladder — the session model and
    ``driver.subagent_runner`` included — so without this the line named a
    runner the user had just tried to move away from and gave no reason
    (2026-10-05, run 3: generate-tasks re-run after a host-model switch stayed
    on ``opencode/big-pickle``, the runner its failed first run recorded).
    The file it names is the one :func:`_recorded_runners` read for ``kind``
    (the judge's is kind-qualified, :func:`_batch_report_filename`).
    """
    if not key.endswith(_runner_selection._RECORDED_RUNNER_SUFFIX):
        return ""
    return (
        "; the runner this task's earlier attempt used, kept from "
        f"{_task_outcome._batch_report_filename(kind)} so a re-run repeats it — the session "
        "model and driver.subagent_runner do not change it"
    )


def run_tasks(
    tasks: Sequence[Dict[str, Any]],
    *,
    phase_dir: str,
    phase: str = "",
    kind: str = "",
    task_file: Optional[str] = None,
    anchor: Optional[str] = None,
    cwd: Optional[str] = None,
    host_max: Optional[int] = None,
    resume: bool = True,
    only_task_ids: Optional[Iterable[str]] = None,
    write_report: bool = True,
) -> _task_outcome.BatchReport:
    """Dispatch a materialized batch and return its report (D3i).

    Runners are resolved **once per task at batch start** and pinned into the
    report, so a re-dispatch under ``--resume`` or ``--retry-failed-subagents``
    uses the runner the first attempt did rather than re-resolving against a
    config that may have changed mid-run — except a task whose attempt failed
    fatally or on its reply's shape (:func:`_recorded_runners`). The effective
    ceilings are logged once
    at batch start alongside each task's runner, so a slow batch is diagnosable
    from the log rather than inferred.

    Tasks are *dispatched* longest-first (:func:`_dispatch_order`) so the biggest
    one never runs alone in the final wave. Everything the caller can observe
    stays in the task file's order: ``report.outcomes`` below is rebuilt by
    walking ``selected``, so ``tasks[]`` in the report, the merge that reads it
    and the per-task runner listing on stdout are all in the order the tasks were
    materialized.
    """
    selected = list(tasks)
    if only_task_ids is not None:
        wanted = set(only_task_ids)
        selected = [t for t in selected if str(t.get("task_id", "")) in wanted]

    report = _task_outcome.BatchReport(
        phase=phase, kind=kind, phase_dir=phase_dir, task_file=task_file,
    )
    if not selected:
        report.ceilings = {"effective": 0}
        if write_report:
            report.write()
        return report

    pin_sha256 = _pin_sha256(tasks)
    report.pin_sha256 = pin_sha256
    recorded = _recorded_runners(phase_dir, kind, pin_sha256=pin_sha256)
    # §7.3a: read before this dispatch overwrites the report, so a resumed
    # (skipped) task keeps the provenance its original dispatch recorded.
    previous_provenance = _recorded_provenance(phase_dir, kind) or {}
    task_by_id: Dict[str, Dict[str, Any]] = {
        str(task.get("task_id", index)): task
        for index, task in enumerate(selected)
    }
    resolved = {
        task_id: _runner_selection._resolve_task_source(task, anchor=anchor, recorded=recorded)
        for task_id, task in task_by_id.items()
    }

    profile = _runner_selection.profile_for_kind(str(selected[0].get("kind") or kind))
    versions, fallback = _preflight_batch_runners(
        resolved, task_by_id, profile=profile, anchor=anchor, recorded=recorded,
    )
    report.runner_versions.update(versions)
    report.runner_fallback = fallback
    runners = {task_id: spec for task_id, (spec, _key, _layer) in resolved.items()}

    report.ceilings = effective_ceiling(
        list(runners.values()), anchor=anchor, host_max=host_max
    )
    print(
        f"[exec-subagents] {len(selected)} task(s), effective parallelism "
        f"{report.ceilings['effective']} "
        f"(driver={report.ceilings['driver_max_concurrent_subagents']}, "
        f"host={report.ceilings['host_max_concurrent_subagents']}, "
        f"provider={report.ceilings['provider_max_concurrent']})"
    )
    # Listed in the task file's own order — this is the batch's runner map, not
    # its schedule, and a reader matching it against `validation_tasks.json` or
    # against `tasks[]` in the report must find the same sequence in all three.
    # The schedule is the separate line `_dispatch_order` prints when it differs.
    for task_id, spec in runners.items():
        version = report.runner_versions.get(spec, "unknown")
        print(
            f"[exec-subagents]   {task_id} -> {spec} (version {version}"
            f"{_pinned_runner_note(resolved[task_id][1], kind)})"
        )

    # D4a, the *during* half: a batch of eleven validation tasks ran for a
    # minute behind a status line that said nothing had started, because the
    # mirror below this call was the only one (measured 2026-09-16). Each
    # completion writes the counts so far against the batch's full size, so a
    # poll reads `validation 3/11 ok` while it is happening. Display only, and
    # deliberately not the batch report: that file is the batch's *record* and
    # stays a single write after the last task.
    finished: List[_task_outcome.TaskOutcome] = []

    def task_finished(outcome: _task_outcome.TaskOutcome) -> None:
        # Called from the dispatch loop's own event loop, one at a time, so the
        # list needs no lock; `update_status` holds the inter-process one.
        finished.append(outcome)
        _mirror_status(
            phase_dir, replace(report, outcomes=list(finished)),
            total=len(selected),
        )

    # Plan codex-sandbox-unavailable §6 F1 item 6 / Limits (2026-09-30): the
    # `[JAIL_DENIED]` and `[CODEX_HOME_CHECK]` lines this batch prints are
    # repeated at its close, because a home change outlives the run.
    jail_lines_before = _probe_state.jail_summary_count()
    outcomes = _run_sync(_gather(
        _dispatch_order(selected),
        runners=runners,
        phase_dir=phase_dir,
        anchor=anchor,
        cwd=cwd,
        max_parallel=report.ceilings["effective"],
        resume=resume,
        on_task_finished=task_finished,
    ))
    # The batch deadline cancels the gather, and its result map comes back
    # empty: a task that settled before it is still in `finished`, with its
    # runner, attempts and usage, and `.status.json` already counted it.
    settled_by_id = {outcome.task_id: outcome for outcome in finished}
    report.outcomes = []
    for index, task in enumerate(selected):
        task_id = str(task.get("task_id", index))
        outcome = outcomes.get(task_id)
        if outcome is None:
            outcome = settled_by_id.get(task_id)
        if outcome is None:
            outcome = _unsettled_outcome(
                task, task_id, runners[task_id], phase_dir, resume=resume,
            )
        report.outcomes.append(outcome)

    report.batch_provenance = _batch_provenance(
        report.outcomes, tasks, kind=kind, previous=previous_provenance,
    )
    # The credit belongs to the bytes this dispatch holds: a round bound to it
    # merges from these rows, never from the report file.
    record_batch_provenance(phase_dir, kind, report.batch_provenance)

    if write_report:
        report.write()
    _mirror_status(phase_dir, report)
    for line in _probe_state.jail_summary_lines(jail_lines_before):
        print(f"[exec-subagents] closing summary: {line}")
    return report


def _unsettled_outcome(
    task: Dict[str, Any], task_id: str, runner: str, phase_dir: str, *, resume: bool,
) -> _task_outcome.TaskOutcome:
    """The outcome of a task that never reached its verdict in this batch
    (cancelled by the batch deadline, or its dispatch raised).

    Cancelling the wait does not stop a dispatch already in its thread, so its
    result file can land after the deadline. Under ``resume`` a file that passes
    :func:`task_is_complete` counts, as it would on the next ``--resume``: it
    was not there at batch start, or the task would have been skipped. It is
    ``ok`` and ``skipped``, so :func:`_batch_provenance` credits no runner with
    bytes this batch never recorded it writing. Without ``resume`` such a file
    may be an earlier run's. Anything else is ``incomplete`` and the batch must
    not reaggregate.
    """
    kind = str(task.get("kind", ""))
    incomplete = (
        "the dispatch did not complete (cancelled by the batch timeout or "
        "the run was killed); "
    )
    complete = _task_result.complete_result_bytes(task, phase_dir)
    if complete is not None:
        if resume:
            return _task_outcome.TaskOutcome(
                task_id=task_id,
                kind=kind,
                runner=runner,
                status=STATUS_OK,
                output_path=str(_task_result.resolve_output_target(task, phase_dir)),
                reason=(
                    "its result file exists and validates; the batch ended "
                    "before its dispatch reported an outcome"
                ),
                skipped=True,
                result_sha256=hashlib.sha256(complete).hexdigest(),
            )
        found = (
            "a valid result file is on disk, but this batch ran without resume, "
            "so it is not taken as this dispatch's"
        )
    else:
        try:
            present = _task_result.resolve_output_target(task, phase_dir).exists()
        except _task_outcome.ResultRejected:
            present = False
        found = (
            "its result file does not validate" if present
            else "no result file exists"
        )
    return _task_outcome.TaskOutcome(
        task_id=task_id,
        kind=kind,
        runner=runner,
        status=STATUS_INCOMPLETE,
        reason=incomplete + found,
    )


def _batch_provenance(
    outcomes: Sequence[_task_outcome.TaskOutcome],
    tasks: Sequence[Dict[str, Any]],
    *,
    kind: str,
    previous: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """Per-output provenance for :attr:`BatchReport.batch_provenance` (§7.3a).

    A task this dispatch ran to a persisted result file records its runner and
    the sha256 of the bytes it persisted (:attr:`TaskOutcome.result_sha256`),
    never of the file hashed now. A task it did *not* run — skipped under
    ``--resume``, or outside ``only_task_ids`` — keeps the row an earlier
    dispatch recorded, but only while that row is still true: same round, and
    the bytes the skip found complete (outside ``only_task_ids``, the file's
    bytes) still hash to the recorded value. Anything else records nothing, so
    the merge falls back to the batch's own ``metadata.model`` rather than
    crediting this executor with a file it never wrote
    (docs/development/review-results.md, "Consuming checked bytes").
    """
    round_id = task_round(tasks)
    task_kinds = {
        str(task.get("task_id", index)): str(task.get("kind") or kind)
        for index, task in enumerate(tasks)
    }
    held_by_id: Dict[str, Optional[str]] = {}
    provenance: Dict[str, Dict[str, Any]] = {}
    for outcome in outcomes:
        if outcome.ok and outcome.output_path:
            held_by_id[outcome.task_id] = outcome.result_sha256
        if not outcome.ok or outcome.skipped or not outcome.output_path:
            continue
        if not outcome.result_sha256:
            continue
        provenance[outcome.task_id] = {
            "task_id": outcome.task_id,
            "kind": outcome.kind or task_kinds.get(outcome.task_id, kind),
            "round": round_id,
            "runner": outcome.runner,
            "sha256": outcome.result_sha256,
        }
    for task_id, row in previous.items():
        if task_id in provenance or not isinstance(row, dict):
            continue
        if task_id not in task_kinds or row.get("round") != round_id:
            continue
        if task_id in held_by_id:
            digest = held_by_id[task_id]
        else:
            task = next(
                (t for i, t in enumerate(tasks)
                 if str(t.get("task_id", i)) == task_id),
                None,
            )
            # Through the module, at each call: tests patch `subagent_tasks.file_bytes_sha256`.
            digest = _subagent_tasks.file_bytes_sha256(
                task.get("output_path") if isinstance(task, dict) else None
            )
        if row.get("sha256") and digest == row["sha256"]:
            provenance[task_id] = dict(row)
    return provenance


def _run_sync(coro):
    """Run ``coro`` to completion whether or not a loop is already running.

    :func:`run_tasks` is a **synchronous** façade on purpose — it is called from
    an async review orchestrator (`run_review_orchestration`), from a sync
    consolidation handler and from the sync apply base, and threading
    async/await through all three call chains would be a much larger change than
    the executor itself. Inside an existing loop the batch runs on a worker
    thread with its own loop; ``asyncio.run`` from within a running loop is a
    ``RuntimeError``, and the concurrency this schedules is subprocess work in
    threads either way.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


class _ProviderBackpressure:
    """D3i's rate-limit backpressure, applied at the provider's in-flight slots.

    A 429 belongs to the *provider*, not to the task that happened to draw it:
    every sibling dispatched into the same limit will hit it too, burn its own
    (budget-free but bounded) rate-limit attempts and then fail. D3i's answer is
    to degrade the batch instead — "the executor narrows that provider's
    in-flight slots for the rest of the batch instead of failing sibling tasks".

    This is a *narrowing* gate, never a second dispatch pool: it is acquired
    inside ``run_tasks_concurrent``'s per-provider and global semaphores, so the
    effective concurrency is the minimum of the two layers and the D3i three-way
    ceiling still bounds the batch from above. Acquisition order is therefore the
    same for every task (provider semaphore → global semaphore → this gate) and a
    holder always already owns the outer two, so narrowing can queue tasks but
    cannot deadlock them.
    """

    #: A throttled provider is halved, never closed: one in-flight slot is the
    #: floor, because zero would strand the rest of the batch behind a provider
    #: whose only way back is a successful attempt.
    MIN_SLOTS = 1

    def __init__(self, limits: Dict[str, int]) -> None:
        self._limits = dict(limits)
        self._in_flight: Dict[str, int] = {}
        self._condition = asyncio.Condition()

    async def acquire(self, provider: str) -> None:
        if provider not in self._limits:
            return
        async with self._condition:
            while self._in_flight.get(provider, 0) >= self._limits[provider]:
                await self._condition.wait()
            self._in_flight[provider] = self._in_flight.get(provider, 0) + 1

    async def release(self, provider: str) -> None:
        if provider not in self._limits:
            return
        async with self._condition:
            self._in_flight[provider] = max(0, self._in_flight.get(provider, 0) - 1)
            self._condition.notify_all()

    def can_narrow(self, provider: str) -> bool:
        """Would :meth:`narrow` still change ``provider``'s slots right now?

        A snapshot for the event-loop thread (the only one that mutates the
        limits): it decides whether a dispatch needs the per-attempt narrowing
        hook at all, never whether a narrowing happens — :meth:`narrow` re-checks
        under the condition.
        """
        current = self._limits.get(provider)
        return current is not None and current > self.MIN_SLOTS

    async def narrow(self, provider: str) -> Optional[int]:
        """Halve ``provider``'s slots. Returns the new count, or ``None`` at the floor."""
        async with self._condition:
            current = self._limits.get(provider)
            if current is None or current <= self.MIN_SLOTS:
                return None
            self._limits[provider] = max(self.MIN_SLOTS, current // 2)
            # Nothing to wake: narrowing only ever removes capacity.
            return self._limits[provider]


def _saw_rate_limit(outcome: _task_outcome.TaskOutcome) -> bool:
    """Did any attempt of this task draw a 429/quota response (D3i)?

    A task that was throttled and then *succeeded* on a later attempt still
    proves the provider is throttling this batch, so it narrows the slots too.
    """
    if outcome.status == STATUS_RATE_LIMITED:
        return True
    return any(attempt.status == STATUS_RATE_LIMITED for attempt in outcome.attempts)


def _narrow_on_rate_limited_attempt(
    backpressure: _ProviderBackpressure,
    provider: str,
    loop: asyncio.AbstractEventLoop,
    task_id: str,
    state: Dict[str, bool],
) -> Callable[[_task_outcome.Attempt], None]:
    """The ``after_attempt`` hook that narrows ``provider`` on a 429 attempt (§5).

    ``dispatch_task`` runs under ``asyncio.to_thread``, so this fires on that
    worker thread, never on the event loop: ``loop`` is captured on the loop
    thread beforehand, and the narrowing is submitted to it with
    ``run_coroutine_threadsafe``. The hook never waits on that future — blocking
    here would stall the attempt loop, backoff sleep included — so the outcome
    is reported from the future's done-callback: the exception if ``narrow()``
    raised, otherwise the usual log line with the attempt number added.

    At most one narrowing per task: ``state["done"]`` is set before the
    submission, so it holds even when ``narrow()`` later fails, and the task
    wrapper's post-return check skips a task that already narrowed. Nothing in
    here may propagate into ``dispatch_task`` — every failure is logged and the
    attempt stands as recorded.
    """

    def report(future: Any, attempt_index: int) -> None:
        try:
            exc = future.exception()
            if exc is not None:
                print(
                    f"multi-llm warning: narrowing {provider} after a rate limit "
                    f"on {task_id} attempt {attempt_index} failed "
                    f"({type(exc).__name__}: {exc})",
                    file=sys.stderr,
                )
                return
            narrowed = future.result()
            if narrowed is not None:
                print(
                    f"[exec-subagents] {provider} reported a rate limit "
                    f"({task_id}, attempt {attempt_index}) — narrowing it to "
                    f"{narrowed} in-flight slot(s) for the rest of the batch"
                )
        except Exception as report_exc:  # noqa: BLE001 - reporting never raises
            print(
                f"multi-llm warning: narrowing {provider} after a rate limit on "
                f"{task_id}: {type(report_exc).__name__}: {report_exc}",
                file=sys.stderr,
            )

    def on_attempt(attempt: _task_outcome.Attempt) -> None:
        try:
            if state["done"] or attempt.status != STATUS_RATE_LIMITED:
                return
            state["done"] = True
            coro = backpressure.narrow(provider)
            try:
                future = asyncio.run_coroutine_threadsafe(coro, loop)
            except BaseException:
                coro.close()  # never scheduled: no "never awaited" warning
                raise
            future.add_done_callback(
                lambda done, index=attempt.index: report(done, index)
            )
        except Exception as exc:  # noqa: BLE001 - an observer never fails a dispatch
            print(
                f"multi-llm warning: could not narrow {provider} after a rate "
                f"limit on {task_id} attempt {attempt.index} "
                f"({type(exc).__name__}: {exc})",
                file=sys.stderr,
            )

    return on_attempt


def _judge_dispatch_argv_preview(
    runner: str, prompt: str, profile: str, anchor: Optional[str],
    *, task: Optional[Dict[str, Any]] = None, kind: str = "human_decision_judge",
    cwd: Optional[str] = None,
) -> List[str]:
    """A best-effort argv for the F6 audit line — never the real dispatch's own.

    Rendered as ``write_batch_scheduler.WriteBatchScheduler._render_argv``
    renders its own (``dispatch_spawn.audit_argv``): the provider's own command
    builder, called directly and never executed, on the rung the dispatch
    takes. The judge is a read kind dispatched with no grant, so its rung and
    request are the ones ``dispatch_spawn._dispatch_grant`` replays for it
    (the recorded rung, a request built from ``cwd``): the audit line never
    shows a sandbox the child did not get. Deliberately not
    :func:`_preview_argv` (the
    ``--dry-run-subagents`` renderer), which enters the full dispatch context
    and materializes a schema sidecar per call — a judge task carries no
    schema, so that machinery would only double the per-attempt setup this
    hook runs beside for no more accurate an argv. A render failure falls back
    to naming the runner: an audit hook must never fail the dispatch it is
    watching.
    """
    provider_name, model = parse_model_spec(runner, anchor=anchor)
    provider = get_provider(provider_name)
    if provider is None:
        return [runner]
    try:
        refusal, request, rung = _dispatch_spawn._dispatch_grant(
            task or {}, kind=kind, profile=profile, runner=runner, cwd=cwd,
            provider=provider, jail_request=None,
        )
    except Exception:  # noqa: BLE001 - an audit preview must never fail a dispatch
        refusal, request, rung = None, None, None
    if refusal is not None:
        request, rung = None, None
    return _dispatch_spawn.audit_argv(
        provider, provider_name, model, profile, prompt, rung=rung, jail_request=request,
    )


def _judge_audit_before_attempt(
    phase_dir: str, anchor: Optional[str]
) -> Callable[[Dict[str, Any]], None]:
    """F6: give the judging dispatch the same ``subagent_audit.jsonl`` trail
    the write executor gives every write dispatch.

    Built only for ``human_decision_judge`` (see :func:`_gather`'s call site),
    never for the other read kinds: ``AuditLog`` is this repo's write-safety
    control (D3l) — reversibility for a dispatch that edits a file — and a
    validation or consolidation batch touches nothing to roll back. A judged
    human decision is different: it is the one subagent output a human is most
    likely to want to re-examine, and until now its dispatch left no argv, no
    prompt hash and no duration anywhere durable — ``subagent_batch_report.json``
    was the only record, and (before the filename split above) the write phase
    that follows it in the same phase dir promptly overwrote that file.
    """
    audit = AuditLog(phase_dir)

    def before_attempt(context: Dict[str, Any]) -> None:
        audit.dispatched(
            task_id=context["task_id"], kind=context["kind"],
            attempt=context["attempt"], runner=context["runner"],
            profile=context["profile"], cwd=context["cwd"],
            sandbox_root=str(context["cwd"] or ""),
            argv=_judge_dispatch_argv_preview(
                context["runner"], context["prompt"], context["profile"], anchor,
                task=context["task"], kind=context["kind"], cwd=context["cwd"],
            ),
            prompt=context["prompt"], declared_files=[],
        )

    return before_attempt


def _judge_audit_completed(phase_dir: str, outcome: _task_outcome.TaskOutcome) -> None:
    """The judging dispatch's terminal audit line, written once ``dispatch_task``
    returns — success or failure alike, unlike ``dispatch_task``'s own
    ``after_result`` hook, which only fires on the schema-valid success path.

    Skipped when no attempt was ever made (a pre-dispatch refusal): a
    ``completed`` line with no matching ``dispatched`` line would claim a run
    that never started, the same guard
    ``write_batch_scheduler.WriteBatchScheduler._audit_terminal`` applies.
    """
    if not outcome.attempts:
        return
    last = outcome.attempts[-1]
    AuditLog(phase_dir).completed(
        task_id=outcome.task_id, kind=outcome.kind, attempt=last.index,
        runner=outcome.runner, profile=outcome.profile, status=outcome.status,
        write_outcome=None, exit_code=last.exit_code, files_touched=[],
        observed={}, duration_seconds=outcome.duration_seconds,
        reason=outcome.reason,
        usage=outcome.usage if outcome.usage_reported else None,
    )


async def _gather(
    tasks: Sequence[Dict[str, Any]],
    *,
    runners: Dict[str, str],
    phase_dir: str,
    anchor: Optional[str],
    cwd: Optional[str],
    max_parallel: int,
    resume: bool,
    on_task_finished: Optional[Callable[[_task_outcome.TaskOutcome], None]] = None,
) -> Dict[str, _task_outcome.TaskOutcome]:
    """Run the batch through the task-keyed concurrency helper.

    ``on_task_finished`` is called once per task as it settles — dispatched,
    skipped or refused by the fatal gate alike — from this loop and nowhere
    else, which is what lets :func:`run_tasks` mirror progress without a lock.
    """
    # One flag for the whole batch, consulted at slot-acquisition time — so a
    # task already inside `dispatch_task` when it flips runs to its own verdict,
    # and everything that reaches it afterwards spawns nothing. `spec` is the
    # runner the fatal row resolved: the gate is batch-wide, the claim an
    # undispatched row is allowed to print is per-spec (D4 step 1).
    fatal: Dict[str, Any] = {"hit": False, "spec": None}

    # The starting slot count per provider: its own `max_concurrent`, bounded by
    # the batch's effective ceiling (a provider limit above it could never be
    # reached through the global gate anyway). Passed to `run_tasks_concurrent` as
    # the explicit `provider_limits` it takes for exactly this purpose, and used to
    # seed the gate that narrows them from there.
    provider_limits: Dict[str, int] = {}
    per_task_budget = 0.0
    for spec in dict.fromkeys(runners.values()):
        provider_name, _ = parse_model_spec(spec, anchor=anchor)
        declared = get_provider_max_concurrent(provider_name, anchor=anchor)
        provider_limits[provider_name] = max(
            1, min(declared or max_parallel, max_parallel)
        )
        per_task_budget = max(
            per_task_budget, get_subagent_timeout(provider_name, anchor=anchor)
        )
    backpressure = _ProviderBackpressure(provider_limits)

    # The batch cap must be derived from the budget a dispatch actually runs on.
    # Left to itself, `run_tasks_concurrent` computes it from
    # `get_provider_timeout` — the *model-call* timeout, which says nothing about
    # `driver.subagent_timeout_s`. Configure a subagent budget above the
    # provider's model timeout (agentic runners routinely need one) and the
    # batch-level `wait_for` cancels tasks that are still healthily inside their
    # own deadline; they come back with no result file, are recorded
    # `incomplete` by `run_tasks` and fail the phase with exit 3 while every
    # runner was behaving. `dispatch_task` bounds one task by
    # `get_subagent_timeout(provider)` **in total** — retries and rate-limit
    # backoff are spent inside that same deadline, so the retry budget no longer
    # multiplies it. The gate can run a provider's tasks one at a time: its
    # slots start at its own `max_concurrent` (below the batch's parallelism
    # when another runner's is higher) and `_ProviderBackpressure` narrows them
    # to one on a rate limit, mid-batch. So one budget per task is the only
    # ceiling that holds whatever the slots do; sized by the starting
    # parallelism's waves, it cancelled healthy tasks queued behind a narrowed
    # provider. `run_tasks_concurrent` still doubles it and adds the stagger,
    # which is the headroom for queueing, kill grace and drain.
    batch_timeout = per_task_budget * len(tasks) if per_task_budget > 0 else None

    def settled(outcome: _task_outcome.TaskOutcome) -> _task_outcome.TaskOutcome:
        """One task has reached its verdict — tell the caller, then hand it back."""
        if on_task_finished is not None:
            try:
                on_task_finished(outcome)
            except Exception:  # noqa: BLE001 - observability never fails a batch
                pass
        return outcome

    async def per_task(task: Dict[str, Any], runner: str, index: int) -> _task_outcome.TaskOutcome:
        if fatal["hit"]:
            failed_spec = fatal["spec"]
            if runner == failed_spec:
                reason = (
                    f"not dispatched: {failed_spec} failed on a rung that fails "
                    f"the whole batch; every task on that runner would fail "
                    f"identically"
                )
            else:
                # Predicts nothing: a rejected id on one spec says nothing
                # about a sibling `model_hint` pinned to another.
                reason = (
                    f"not dispatched: the batch stopped after {failed_spec} "
                    f"failed fatally; this task's runner {runner} was never tried"
                )
            return settled(_task_outcome.TaskOutcome(
                task_id=str(task.get("task_id", index)),
                kind=str(task.get("kind", "")),
                runner=runner,
                status=STATUS_INCOMPLETE,
                reason=reason,
            ))
        provider_name, _ = parse_model_spec(runner, anchor=anchor)
        await backpressure.acquire(provider_name)
        # F6: route the judging dispatch through `subagent_audit.jsonl` too —
        # see `_judge_audit_before_attempt`. Every other kind passes `None` and
        # dispatches exactly as it always has.
        is_judge = str(task.get("kind", "")) == "human_decision_judge"
        # §5: narrow on the rate-limited *attempt*, not on the finished task —
        # a task that backs off and retries can hold its verdict for many
        # minutes, and every sibling acquiring meanwhile should already see the
        # narrower gate. Only when narrowing can still change something; a
        # dispatch without it still narrows below, after it returns.
        narrowing = {"done": False}
        try:
            outcome = await asyncio.to_thread(
                _task_dispatch.dispatch_task,
                task,
                phase_dir=phase_dir,
                runner=runner,
                anchor=anchor,
                cwd=cwd,
                before_attempt=(
                    _judge_audit_before_attempt(phase_dir, anchor)
                    if is_judge else None
                ),
                after_attempt=(
                    _narrow_on_rate_limited_attempt(
                        backpressure, provider_name, asyncio.get_running_loop(),
                        str(task.get("task_id", index)), narrowing,
                    )
                    if backpressure.can_narrow(provider_name) else None
                ),
            )
        finally:
            await backpressure.release(provider_name)
        if is_judge:
            _judge_audit_completed(phase_dir, outcome)
        if outcome.fatal and not fatal["hit"]:
            fatal["hit"] = True
            fatal["spec"] = runner
        # At most once per task: a task whose attempt already narrowed (or
        # tried to — the flag is set before `narrow()` is submitted) is skipped.
        if not narrowing["done"] and _saw_rate_limit(outcome):
            narrowed = await backpressure.narrow(provider_name)
            if narrowed is not None:
                print(
                    f"[exec-subagents] {provider_name} reported a rate limit — "
                    f"narrowing it to {narrowed} in-flight slot(s) for the rest "
                    f"of the batch"
                )
        return settled(outcome)

    def skip_done(task: Dict[str, Any], runner: str, index: int) -> Optional[_task_outcome.TaskOutcome]:
        found = _task_result.complete_result_bytes(task, phase_dir) if resume else None
        if found is None:
            return None
        target = _task_result.resolve_output_target(task, phase_dir)
        print(f"[exec-subagents] {task.get('task_id')} already complete — skipping")
        return settled(_task_outcome.TaskOutcome(
            task_id=str(task.get("task_id", index)),
            kind=str(task.get("kind", "")),
            runner=runner,
            status=STATUS_OK,
            output_path=str(target),
            skipped=True,
            result_sha256=hashlib.sha256(found).hexdigest(),
        ))

    return await _concurrency.run_tasks_concurrent(
        list(tasks),
        per_task,
        runner_for_task=lambda task: runners[str(task.get("task_id", ""))],
        timeout=batch_timeout,
        max_parallel=max_parallel,
        skip_predicate=skip_done,
        provider_limits=provider_limits,
        # §9.3.c: the helper has no plan path of its own; this batch's is the
        # anchor its per-provider bounds and timeouts must resolve against.
        anchor=anchor,
    )


def _pin_sha256(tasks: Sequence[Dict[str, Any]]) -> str:
    """What a recorded runner is a pin *for*: the round plus the batch inputs.

    :func:`subagent_tasks.task_round` fingerprints which groups each output
    answers; the first task's ``inputs`` (plan, grouped file, diff base, reviewed
    code) say what they were judged against. A forced re-review that changes
    either is a new dispatch, not a re-dispatch.
    """
    first_inputs = next(
        (t.get("inputs") for t in tasks if isinstance(t, dict) and t.get("inputs")),
        None,
    )
    canonical = json.dumps(
        [task_round(tasks), first_inputs], sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _recorded_runners(
    phase_dir: str, kind: str = "", *, pin_sha256: str = ""
) -> Dict[str, str]:
    """Runners pinned by a previous batch report, for a re-dispatch (D3o).

    **A recorded runner whose recorded status is fatal is not a pin, it is a
    rejected assignment** (D4 step 6) — and neither is the same spec on a row
    the fatal gate stopped before it could be tried. One rule, keyed on the spec
    rather than the row: every row whose runner equals a spec that *any* row in
    the same report recorded with a status in ``FATAL_STATUSES`` is dropped, so
    ``resolve_task_runner`` falls through to the current configuration for
    exactly the tasks the rejected spec touched, and a config repair takes
    effect on re-invocation. Rows on a spec that never failed keep their pin.
    The spec-keyed half is load-bearing: the concurrent gate records
    undispatched siblings ``incomplete`` (not fatal) while still writing the
    spec they were about to use, and preflight runs once per *distinct* spec —
    so one surviving pin would re-refuse the whole batch, repaired config and
    all.

    ``kind`` (F6): a re-dispatch must read *this* dispatch's own report back,
    not whichever kind's report happens to sit at the bare filename — see
    :func:`_batch_report_filename`. Omitted by the one caller that can never
    collide (``_authoritative_validator_runner``, always a validation-family
    kind), where it defaults to the bare name exactly as before.

    **A row whose own status is a reply-quality failure is not a pin either**
    (:data:`UNPINNED_ROW_STATUSES`, fix round 8): the runner was reached and
    answered, in a shape nobody could use, so a re-run is the moment to try
    another runner — the session model the host switched to, or a repaired
    ``driver.subagent_runner`` — not to repeat it. Row-level, unlike the fatal
    rule: the spec itself works. A transport failure (timeout, rate limit,
    runner error) or an ``incomplete`` row keeps its pin, so a re-run of a
    batch that merely ran out of time stays on the runner its siblings used.
    Measured 2026-10-05, OpenCode run 3: generate-tasks failed twice on
    ``opencode/big-pickle``'s reply shape, the host switched model, and the
    re-run dispatched big-pickle again on the strength of that failed row.

    ``pin_sha256`` (2026-10-02, #29): the current batch's :func:`_pin_sha256`. A
    report that recorded a *different* digest was written for another round or other
    inputs, and its runners are not pins for this batch. Measured on a Codex
    ``review-code --force``: the previous day's validation report recorded the
    session model (``codex:gpt-6-astra``, before the project set
    ``driver.subagent_runner: claude-code:sonnet``), and the forced re-review
    re-used that pin instead of the configured runner. A report with no digest, or a
    caller that passes none, pins exactly as before.
    """
    path = Path(phase_dir) / _task_outcome._batch_report_filename(kind)
    if not path.exists():
        return {}
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    recorded_sha256 = document.get("pin_sha256") if isinstance(document, dict) else None
    if pin_sha256 and recorded_sha256 and recorded_sha256 != pin_sha256:
        return {}
    rows = [
        row for row in document.get("tasks", [])
        if isinstance(row, dict) and row.get("task_id") and row.get("runner")
    ]
    rejected_specs = {
        str(row["runner"]) for row in rows if row.get("status") in FATAL_STATUSES
    }
    recorded = {}
    for row in rows:
        spec = str(row["runner"])
        if spec in rejected_specs or row.get("status") in UNPINNED_ROW_STATUSES:
            continue
        recorded[str(row["task_id"])] = spec
    return recorded


def _recorded_provenance(
    phase_dir: str, kind: str = ""
) -> Optional[Dict[str, Dict[str, Any]]]:
    """The ``batch_provenance`` block of ``kind``'s batch report (§7.3a).

    ``None`` when there is no report, or the report predates the block (no
    ``batch_provenance`` key at all) — the caller then falls back to the legacy
    per-row ``runner`` (:func:`_recorded_runners`). ``{}`` is a report that
    recorded provenance and has none to offer.
    """
    path = Path(phase_dir) / _task_outcome._batch_report_filename(kind)
    if not path.exists():
        return None
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(document, dict) or "batch_provenance" not in document:
        return None
    block = document.get("batch_provenance")
    if not isinstance(block, dict):
        return {}
    return {
        str(task_id): row for task_id, row in block.items() if isinstance(row, dict)
    }


def _mirror_status(
    phase_dir: str, report: _task_outcome.BatchReport, *, total: Optional[int] = None
) -> None:
    """Mirror the batch counts into ``.status.json`` (D4a). Best-effort.

    ``total`` is the batch's task count, which while the batch is in flight is
    larger than the number of outcomes recorded so far; it defaults to the
    outcomes present, so the mirror a finished batch writes is byte-identical to
    the one this wrote before it took the argument.
    """
    try:
        _status_file.update_status(phase_dir, {
            "progress": {
                _STATUS_MIRROR_KEY: {
                    "kind": report.kind,
                    "invoker": report.invoker,
                    "total": total if isinstance(total, int) else len(report.outcomes),
                    "ok": sum(1 for o in report.outcomes if o.ok),
                    "counts": report.counts(),
                    "failed_task_ids": [o.task_id for o in report.failed],
                    "runner_versions": dict(report.runner_versions),
                    "effective_parallelism": report.ceilings.get("effective"),
                }
            }
        })
    except Exception:  # noqa: BLE001 - observability must not fail a phase
        pass
