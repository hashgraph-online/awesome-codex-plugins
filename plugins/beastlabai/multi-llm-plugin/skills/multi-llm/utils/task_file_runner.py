"""The executor's entry points: a task file, its dry run, and the
continuation past a marker.

:func:`run_task_file` (checks the file's recorded inputs, then
``task_batch.run_tasks``), :func:`dry_run_report` (D3l: what each task
would run, with nothing spawned) and :func:`continue_past_marker`
(D3b).

``utils.subagent_executor`` re-exports every name defined here for reading
only: patch one here, never through the executor
(docs/development/delegation.md#where-the-executors-helpers-live).
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, List, Optional, Tuple

from . import cli_common
from . import host_capabilities as caps
from . import structured_output
from .llm_client import provider_dispatch_context
from .provider_registry import (
    get_provider,
    parse_model_spec,
)
from . import landlock_dispatch
from .providers.base import (
    JailRequest,
    sandbox_rung_id,
)
from . import subagent_tasks as _subagent_tasks
from .subagent_tasks import (
    preferred_prompt_transport,
    refuse_reason,
    tasks_of,
)
from .redact import redact_argv
from .write_safety import DRY_RUN_FILENAME
from . import failure_capture as _failure_capture
from . import task_outcome as _task_outcome
from . import task_result as _task_result
from . import runner_selection as _runner_selection
from . import probe_state as _probe_state
from . import dispatch_spawn as _dispatch_spawn
from . import runner_preflight as _runner_preflight
from . import task_dispatch as _task_dispatch
from . import task_batch as _task_batch


#: The provenance a task file records about itself: the document key naming a
#: source file → the ``inputs`` key its hash was recorded under. This is what
#: makes the default read path able to re-bind a file nobody handed it: every
#: producer writes the source paths next to the hashes (validation and
#: consolidation their ``plan_file``/``grouped_file``, salvage its
#: ``salvage_request_path``). ``diff_sha256``/``items_sha256`` are deliberately
#: absent — their source is not a file on disk, so they stay unchecked rather
#: than spuriously refused (:func:`subagent_tasks.check_task_file_inputs`
#: compares only keys present in both blocks).
_INPUT_SOURCE_KEYS = {
    "plan_file": "plan_sha256",
    "grouped_file": "grouped_sha256",
    "tasks_file": "tasks_sha256",
    "salvage_request_path": "salvage_request_sha256",
}


def _recomputed_inputs(
    document: Dict[str, Any], phase_dir: str, anchor: Optional[str]
) -> Dict[str, str]:
    """Re-hash the inputs this task file's own recorded provenance still names.

    Freshly computed hashes are what turn ``read_task_file``'s inputs guard on —
    without them it version- and schema-checks the file and binds nothing. A
    caller that already knows its inputs passes them in; this is the fallback for
    one that only has the file, and it reads the sources *the document itself*
    names so a re-hash can never bind the file to something it was not
    materialized from.

    A source that cannot be read is skipped rather than hashed to ``""``: a
    missing file would compare as "changed" and refuse a phase dir that was
    merely moved, and an input nobody can recompute is exactly the case
    ``check_task_file_inputs`` documents as "simply does not check it". A
    recorded hash that is *already* ``""`` is skipped for the mirror-image
    reason — that is ``file_content_hash``'s "the producer had no such file"
    (every salvage task file records ``plan_sha256: ""``), so re-hashing
    something in its place would refuse a file that was never bound to it.
    """
    recorded = document.get("inputs")
    if not isinstance(recorded, dict):
        return {}
    sources: Dict[str, Any] = {
        key: document.get(key) for key in _INPUT_SOURCE_KEYS
    }
    # The salvage files record no `plan_file` (the request is what their prompt is
    # built from), but they do record `plan_sha256`, and the dispatching caller
    # already threads the plan path through as `anchor` — which is a plan file or
    # a repo directory, so it only stands in when it is really a file.
    if not sources.get("plan_file") and anchor and os.path.isfile(anchor):
        sources["plan_file"] = anchor

    current: Dict[str, str] = {}
    for source_key, input_key in _INPUT_SOURCE_KEYS.items():
        source = sources.get(source_key)
        if not recorded.get(input_key) or not isinstance(source, str) or not source:
            continue
        path = source if os.path.isabs(source) else os.path.join(phase_dir, source)
        if not os.path.isfile(path):
            continue
        current[input_key] = _subagent_tasks.file_content_hash(path)
    return current


def run_task_file(
    task_file: str,
    *,
    phase_dir: Optional[str] = None,
    phase: str = "",
    anchor: Optional[str] = None,
    cwd: Optional[str] = None,
    document: Optional[Dict[str, Any]] = None,
    current_inputs: Optional[Dict[str, str]] = None,
    host_max: Optional[int] = None,
    resume: bool = True,
    only_task_ids: Optional[Iterable[str]] = None,
) -> _task_outcome.BatchReport:
    """Dispatch every task in a materialized task file.

    ``document`` lets a caller that already read (and input-bound) the file hand
    it in rather than re-reading — the version/inputs guards belong to
    ``utils/subagent_tasks.read_task_file`` and must not be bypassed here.

    ``current_inputs`` is the freshly recomputed hash block for the read path.
    It is optional but the binding is **not**: ``read_task_file`` only enforces
    the inputs guard when it is given one, so passing nothing would silently
    downgrade the default read to a version-and-schema check — and a phase dir
    outlives the run that wrote it, so a plan or a salvage request edited between
    a crash and the resume would produce a confidently stale prompt against text
    nobody is reviewing any more (D2g). When it is omitted the hashes are
    recomputed from the provenance the document records (:func:`_recomputed_inputs`).

    Human tasks are filtered out rather than dispatched: ``executor_role: human``
    means no invoker ever runs them, and they route to the D6 human-task pause.

    Raises:
        ExecutorError: exit 3 — the file is the wrong version, the wrong shape,
            or was materialized from inputs that have since moved. Raised as the
            executor's own refusal so both invokers' handlers (which exit 3 on
            the fan-out path and skip the one non-fatal salvage dispatch) see it
            rather than a bare traceback. Nothing is dispatched either way.
    """
    resolved_dir = phase_dir or os.path.dirname(os.path.abspath(task_file))
    if document is None:
        try:
            document = _subagent_tasks.read_task_file(task_file, phase_dir=resolved_dir)
            bound = (
                current_inputs if current_inputs is not None
                else _recomputed_inputs(document, resolved_dir, anchor)
            )
            if bound:
                # Through the module, at each call: tests patch the binding check.
                _subagent_tasks.check_task_file_inputs(document, task_file, resolved_dir, bound)
        except _subagent_tasks.TaskFileError as exc:
            raise _task_outcome.ExecutorError(str(exc)) from exc

    # A frozen context plan is read by path even when the caller has already
    # materialized the document in memory. Bind it on both entry paths, and
    # treat a missing snapshot (or old task file lacking provenance) as stale.
    if (document.get("inputs") or {}).get("context_plan_sha256"):
        source = document.get("context_plan_file")
        path = os.path.join(resolved_dir, source) if isinstance(source, str) and source else None
        try:
            _subagent_tasks.check_task_file_inputs(document, task_file, resolved_dir, {
                "context_plan_sha256": _subagent_tasks.file_bytes_sha256(path),
            })
        except _subagent_tasks.TaskFileError as exc:
            raise _task_outcome.ExecutorError(str(exc)) from exc

    tasks = [
        task for task in tasks_of(document)
        if task.get("executor_role") != "human"
    ]
    return _task_batch.run_tasks(
        tasks,
        phase_dir=resolved_dir,
        phase=phase,
        kind=str(document.get("kind", "")),
        task_file=task_file,
        anchor=anchor,
        cwd=cwd,
        host_max=host_max,
        resume=resume,
        only_task_ids=only_task_ids,
    )


# ---------------------------------------------------------------------------
# The native invoker, simulated (D3a equivalence)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# D3l — --dry-run-subagents for the read half
# ---------------------------------------------------------------------------

def _preview_argv(
    provider: Any,
    *,
    prompt: str,
    model: str,
    profile: str,
    schema: Optional[Any],
    anchor: Optional[str] = None,
    sandbox_fallback: Optional[str] = None,
    jail_request: Optional[JailRequest] = None,
) -> Tuple[Optional[List[str]], Optional[str]]:
    """The argv a dispatch WOULD render, built the way a dispatch builds it.

    A preview whose argv differs from the real argv is worth less than its own
    output implies, so this is deliberately :func:`_spawn` / :func:`_spawn_child`
    minus the ``Popen``: the same two context managers, in the same order, around
    the same adapter call.

    * **The dispatch context first** (M4/§2.3). An adapter that contains its own
      config layering renders a flag and an env redirect that only mean anything
      together — opencode's ``--pure`` pairs with its ``XDG_CONFIG_HOME``
      redirect and neither is emitted outside an active context — so rendering
      here without entering it would preview an argv no dispatch ever runs. The
      ``with`` is also the ``finally`` half of that lifecycle: the context is
      refcounted and its shared temp directory is removed when the last user
      leaves, so a preview cleans up exactly as a dispatch does. A refusal comes
      back as a *reason*, not an argv — the same refusal the real spawn would
      have taken on its spawn rung, minus the child.
    * **The sidecar second** (§4.2.1), for the adapters whose structured-output
      transport is a file: codex refuses a schema whose file is unreadable
      *before* it returns any argv, so a preview that passed the unmaterialized
      schema would report "would not dispatch" for a task that dispatches fine.
      The directory is removed on the way out, here as there.

    ``schema=None`` — every kind with no schema phase, and every adapter that
    declined the flag — renders exactly what this preview rendered before.
    ``sandbox_fallback`` is the rung id the preflight just recorded (or
    ``None``): a dry run's argv has to show the rung a real dispatch would
    render — ``danger-full-access``, or ``read-only`` plus the landlock feature
    — or the preview would be the one artifact that hid it.

    On the plugin's Landlock jail (plan codex-sandbox-unavailable §6 F1,
    2026-09-30) the preview shows the wrapped shape — the interpreter, the
    wrapper, the ``--allow`` entries and ``-c developer_instructions=…`` —
    with placeholder paths, and creates nothing: no scratch directory, no
    home lookup. ``jail_request`` is the dispatch's grant; a read kind's is
    built from the process cwd when none is given.
    """
    rung = sandbox_rung_id(sandbox_fallback)
    wrap = _dispatch_spawn._wrapping_rung(provider, profile, rung)
    if wrap is not None and jail_request is None:
        jail_request = JailRequest(repo_root=os.path.realpath(os.getcwd()), kind=profile)

    def _render(materialized_schema: Optional[Any]) -> List[str]:
        argv = provider.build_agent_command(
            prompt, model, profile, schema=materialized_schema
        )
        if wrap is not None and jail_request is not None:
            argv = provider.apply_sandbox_fallback(
                argv, profile, rung,
                context=landlock_dispatch.preview_context(jail_request),
            )
            return landlock_dispatch.preview_wrap_argv(argv, wrap, jail_request)
        if rung:
            argv = provider.apply_sandbox_fallback(argv, profile, rung)
        return argv

    with provider_dispatch_context(
        provider, model, profile, anchor=anchor,
        runner_version=_dispatch_spawn._preflight_version(provider),
    ) as dispatch:
        if dispatch.refusal:
            return None, dispatch.refusal
        if schema is not None and getattr(
            provider, "structured_output_transport", "inline"
        ) == "file":
            with structured_output.schema_sidecar(schema) as materialized:
                return _render(materialized), None
        return _render(schema), None


def dry_run_report(
    task_file: str,
    *,
    phase_dir: str,
    phase: str = "",
    document: Optional[Dict[str, Any]] = None,
    anchor: Optional[str] = None,
    cwd: Optional[str] = None,
) -> str:
    """Render every read/analyze dispatch without starting one. Returns the path.

    The read-half twin of the scheduler's write dry run: resolve the runner, render
    the exact argv (prompt elided to its digest), check the transport and the
    prompt budget, apply the profile, probe runner presence and version — then write
    ``{phase}/subagent_dry_run.json`` and return, having spawned nothing but
    ``--version``.
    """
    resolved_dir = phase_dir or os.path.dirname(os.path.abspath(task_file))
    if document is None:
        document = _subagent_tasks.read_task_file(task_file, phase_dir=resolved_dir)

    kind = str(document.get("kind", ""))
    entries: List[Dict[str, Any]] = []
    runners: List[str] = []
    for task in tasks_of(document):
        task_id = str(task.get("task_id", ""))
        entry: Dict[str, Any] = {
            "task_id": task_id,
            "kind": str(task.get("kind", kind)),
            "cwd": cwd,
        }
        if task.get("executor_role") == "human":
            entry["would_dispatch"] = False
            entry["reason"] = "executor_role: human — never dispatched by any invoker"
            entries.append(entry)
            continue
        try:
            entry["profile"] = _runner_selection.profile_for_kind(str(task.get("kind", kind)))
        except _task_outcome.ExecutorError as exc:
            entry["would_dispatch"] = False
            entry["reason"] = exc.message
            entries.append(entry)
            continue
        runner = _runner_selection.resolve_task_runner(task, anchor=anchor)
        entry["runner"] = runner
        runners.append(runner)
        provider_name, model = parse_model_spec(runner, anchor=anchor)
        provider = get_provider(provider_name)
        transport = preferred_prompt_transport(provider_name)
        entry["prompt_transport"] = transport
        prompt = str(task.get("prompt") or "")
        entry["prompt_utf16_units"] = _subagent_tasks.utf16_units(prompt)
        reason = refuse_reason(
            task,
            supports_workspace_reads=bool(
                provider is not None and provider.supports_workspace_reads
            ),
            runner=runner,
        )
        if reason is None:
            try:
                _task_result.resolve_output_target(task, resolved_dir)
            except _task_outcome.ResultRejected as exc:
                reason = exc.message
        if reason is None and provider is not None:
            fallback = _probe_state.sandbox_rung(runner, entry["profile"])
            reason = _task_dispatch._prompt_over_budget(
                provider, model, prompt, transport, entry["profile"],
                **({"sandbox_fallback": fallback, "jail_request": JailRequest(
                    repo_root=os.path.realpath(cwd or os.getcwd()),
                    kind=entry["kind"],
                )} if _dispatch_spawn._wrapping_rung(provider, entry["profile"], fallback) else {}),
            )
        if reason is None:
            try:
                info = _runner_preflight.preflight_runner(
                    runner, profile=entry["profile"], anchor=anchor,
                    key="driver.subagent_runner",
                    # D3l: a dry run renders commands and starts no child, so the
                    # declared nested_exec verdict still refuses a `denied` host
                    # but the throwaway dispatch behind an `unknown` leg does not
                    # run — it is a real turn, and this flag promises none.
                    probe_nested=False,
                )
                entry["runner_version"] = info["version"]
                entry["nested_exec"] = info["nested_exec"]
            except _task_outcome.ExecutorError as exc:
                reason = exc.message
        if reason is not None:
            entry["would_dispatch"] = False
            entry["reason"] = reason
            entries.append(entry)
            continue
        # §4.2.2's pre-dispatch read, resolved from the KIND exactly as
        # `dispatch_task` resolves it (`schema_phase_for_kind` +
        # `schema_for_dispatch`) — never hard-coded here, or the preview would
        # be right for one schema-bearing kind and wrong for the other. `warn`
        # is off: the per-(provider, phase) WARN belongs to a dispatch that is
        # really taking the fallback, and a preview that emitted it would both
        # duplicate the line and consume the once-per-process budget the real
        # run needs.
        schema = None
        schema_phase = _task_dispatch.schema_phase_for_kind(str(task.get("kind", kind)))
        # `provider is not None` for the same reason the budget check above
        # carries it: a runner with no built-in adapter is normally refused by
        # `preflight_runner` before here, and a preflight may not raise on the
        # path where it was not.
        if schema_phase and provider is not None:
            try:
                schema, _marker = structured_output.schema_for_dispatch(
                    provider, schema_phase, warn=False
                )
            except structured_output.SchemaConfigError as exc:
                # Rung 7 in a dispatch, "would not dispatch" here: no run can
                # produce a schema file that is not there.
                entry["would_dispatch"] = False
                entry["reason"] = f"structured output: {exc}"
                entries.append(entry)
                continue
        try:
            fallback = _probe_state.sandbox_rung(runner, entry["profile"])
            argv, refusal = _preview_argv(
                provider, prompt=prompt, model=model, profile=entry["profile"],
                schema=schema, anchor=anchor,
                sandbox_fallback=fallback,
                **({"jail_request": JailRequest(
                    repo_root=os.path.realpath(cwd or os.getcwd()),
                    kind=entry["kind"],
                )} if _dispatch_spawn._wrapping_rung(provider, entry["profile"], fallback) else {}),
            )
        except Exception as exc:  # noqa: BLE001 - a preflight must not raise
            entry["would_dispatch"] = False
            entry["reason"] = str(exc)
            entries.append(entry)
            continue
        if refusal is not None or argv is None:
            entry["would_dispatch"] = False
            entry["reason"] = refusal or "the adapter rendered no command"
            entries.append(entry)
            continue
        entry["argv"] = redact_argv(argv, prompt)
        entry["would_dispatch"] = True
        entries.append(entry)

    path = os.path.join(resolved_dir, DRY_RUN_FILENAME)
    _failure_capture._atomic_write_json(path, {
        "dry_run_version": 1,
        "kind": kind,
        "phase": phase,
        "task_file": task_file,
        "cwd": cwd,
        "ceilings": _task_batch.effective_ceiling(runners, anchor=anchor) if runners
        else {"effective": 0},
        "tasks": entries,
    })
    return path


# ---------------------------------------------------------------------------
# D3b — the self-contained continuation past a marker
# ---------------------------------------------------------------------------

def _retry_instruction(
    args: Any, *, failed_ids: str, retry_command: Optional[str]
) -> List[str]:
    """The failed batch's recovery block, addressed to whoever can follow it.

    ``--host`` is already on this run's own namespace — a shim bakes it into
    every command it renders — so the addressee is resolved at the point host
    capability is *already known*, in Python, and the agent is handed a finished
    sentence. Nothing here asks an agent to consult the capability matrix
    mid-run (D5); the matrix stays off every agent read path.
    """
    host_id = caps.resolve_host_id(explicit=getattr(args, "host", None))
    return caps.retry_instruction(
        host_id, failed_ids=failed_ids, retry_command=retry_command
    )


def continue_past_marker(
    args: Any,
    *,
    task_file: str,
    phase_dir: str,
    phase: str = "",
    document: Optional[Dict[str, Any]] = None,
    anchor: Optional[str] = None,
    cwd: Optional[str] = None,
    label: str = "subagent",
    retry_command: Optional[str] = None,
    resume: bool = True,
) -> bool:
    """Should this phase continue in-process past the marker it just printed?

    Host-driven (the default, and today's behavior byte-for-byte): returns
    ``False`` immediately when ``--exec-subagents`` is off, so the caller prints
    its follow-up command and exits exactly as before. The executor is strictly
    additive until a host asks for it.

    Self-contained (``--exec-subagents``): dispatches the batch, and returns
    ``True`` when every task produced a schema-valid result file, so the caller
    falls through to reaggregation / verdict ingest / consolidation inline and the
    phase completes in one invocation. Markers are still printed — they are
    informational on this path, and the run is finished when the process exits.
    *resume* is :func:`run_task_file`'s: ``False`` dispatches every task, a
    result file already on disk counting for none.

    Raises:
        BatchFailed: exit 3 (even under ``--yes``) when any task failed or is
            incomplete. The phase does **not** reaggregate the short set and never
            falls back to salvage.
    """
    if not getattr(args, "exec_subagents", False):
        return False

    if getattr(args, "dry_run_subagents", False):
        # D3l: the flag means "start no child", and it means it on the read half
        # too. Without this branch a read phase would dispatch for real under a
        # flag whose whole promise is that it does not — the surprise being worse
        # here than on the write path precisely because nothing visibly changes.
        report = dry_run_report(
            task_file, phase_dir=phase_dir, phase=phase, document=document,
            anchor=anchor, cwd=cwd,
        )
        print(
            f"[dry-run-subagents] {report} — every {label} command rendered, no "
            f"child started, nothing else changed. This phase still prints its "
            f"marker and its follow-up command."
        )
        return False

    print(f"\n[exec-subagents] dispatching {label} tasks from {task_file}")
    report = run_task_file(
        task_file,
        phase_dir=phase_dir,
        phase=phase,
        document=document,
        anchor=anchor,
        cwd=cwd,
        **({"resume": False} if not resume else {}),
    )
    if report.ok:
        print(
            f"[exec-subagents] {len(report.outcomes)} {label} task(s) complete; "
            f"continuing in-process"
        )
        return True

    failed_ids = ", ".join(o.task_id for o in report.failed)
    lines = [
        f"\nERROR: {len(report.failed)} of {len(report.outcomes)} {label} task(s) "
        f"did not produce a usable result, so this phase refuses to reaggregate a "
        f"short set. Under --yes this is still exit 3: an unattended run may not "
        f"decide that a missing batch is acceptable.",
        *report.failure_summary(),
        # F6: names the file this dispatch's own kind actually wrote, not
        # always the bare name — a failed judging dispatch would otherwise
        # point at a report a later write dispatch may go on to overwrite.
        f"Report: {_task_outcome.batch_report_path(phase_dir, report.kind)}",
        f"Diagnostics: {os.path.join(phase_dir, _failure_capture.FAILED_CAPTURE_DIRNAME)}/",
        # Resume IS the retry-only-the-failures path: a task counts as done iff
        # its result file exists, parses and validates, so re-invoking the phase
        # skips every completed task and re-dispatches exactly the failed set
        # ({failed_ids}) under its original task_id. Who is being asked to
        # re-invoke is the host's `multi_turn` answer, not an assumption: a host
        # that ends its run with this command leaves no agent able to follow the
        # instruction, so it is addressed to the human instead.
        #
        # D2 step 4: the block is *shaped* from this call's own report — the
        # statuses of `report.failed`, and whether the fan-out's artifacts are
        # usable — never from a count. A fatal status names its repair above
        # the command; a transient one names the cost beneath it; unusable
        # artifacts make --force the command. Only one runnable string either
        # way, so a host's option scrape yields one retry tool call.
        *_shaped_retry_block(
            args, report, phase_dir=phase_dir, document=document,
            failed_ids=failed_ids, retry_command=retry_command,
        ),
    ]
    raise _task_outcome.BatchFailed("\n".join(lines), report)


def _artifacts_usable(document: Optional[Dict[str, Any]], phase_dir: str) -> bool:
    """Whether the fan-out's own artifacts this batch reads still parse.

    The grouped file the task document names (``grouped_file``, recorded
    beside its hash) is the one artifact a validation/consolidation batch is
    downstream of; when it is missing or unreadable the reviewer pass itself
    has to run again, and no ``--reaggregate`` can help. A document naming no
    such file has nothing to check and is usable by definition.
    """
    if not document:
        return True
    grouped = document.get("grouped_file")
    if not grouped:
        return True
    path = grouped if os.path.isabs(str(grouped)) else os.path.join(phase_dir, str(grouped))
    try:
        with open(path, "r", encoding="utf-8") as stream:
            json.load(stream)
    except (OSError, ValueError):
        return False
    return True


def _force_variant(command: Optional[str]) -> Optional[str]:
    """The same retry with ``--force`` as its verb (shape 3 only)."""
    if not command:
        return None
    for verb in ("--reaggregate", "--reaggregate-consolidation", "--yes"):
        if command.endswith(" " + verb):
            return command[: -len(verb)] + "--force"
    return command + " --force"


def _shaped_retry_block(
    args: Any,
    report: "_task_outcome.BatchReport",
    *,
    phase_dir: str,
    document: Optional[Dict[str, Any]],
    failed_ids: str,
    retry_command: Optional[str],
) -> List[str]:
    """`_retry_instruction` wrapped in the shape `cli_common.retry_shape` picks."""
    statuses = [o.status for o in report.failed]
    shape = cli_common.retry_shape(
        statuses=statuses, artifacts_ok=_artifacts_usable(document, phase_dir)
    )
    redispatch = len(report.failed)
    kept = sum(1 for o in report.outcomes if o.ok)
    if shape == cli_common.SHAPE_FORCE:
        return [
            "The fan-out's own artifacts are unusable (the grouped file this "
            "batch reads is missing or does not parse), so the reviewer pass "
            "has to run again — re-invoke with --force:",
            *_retry_instruction(
                args, failed_ids=failed_ids,
                retry_command=_force_variant(retry_command),
            ),
        ]
    lines: List[str] = []
    if shape == cli_common.SHAPE_REPAIR:
        counts: Dict[str, int] = {}
        for status in statuses:
            counts[status] = counts.get(status, 0) + 1
        lines.append(
            "Repair first: "
            + cli_common.repair_sentence(counts=counts, statuses=statuses)
            + "."
        )
    lines.extend(
        _retry_instruction(args, failed_ids=failed_ids, retry_command=retry_command)
    )
    lines.append(
        f"  (re-dispatches the {redispatch} failed task(s) and keeps the {kept} "
        f"valid result(s) already on disk; --force is not needed and would "
        f"re-run the reviewer panel)"
    )
    return lines
