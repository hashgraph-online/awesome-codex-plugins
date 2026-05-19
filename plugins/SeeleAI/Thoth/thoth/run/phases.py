"""Mechanical phase engine for strict run/loop orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import time
from typing import Any, Protocol

from thoth.prompt_specs import command_prompt_authority, phase_prompt_authority
from thoth.prompt_validators import PHASE_REQUIRED_FIELDS, validate_phase_output
from thoth.objects import Store

from .io import _read_json, _write_json
from .ledger import (
    _append_event,
    _update_run,
    _update_state,
    complete_run,
    fail_run,
    heartbeat_run,
    record_artifact,
)
from .model import RunHandle, utc_now
from .review_context import latest_fresh_review_context

DEFAULT_LOOP_MAX_ITERATIONS = 10
DEFAULT_LOOP_MAX_RUNTIME_SECONDS = 8 * 60 * 60
RUN_PHASE_ORDER = ("plan", "execute", "validate", "reflect")
RUN_PHASE_PROGRESS = {
    "plan": 20,
    "execute": 45,
    "validate": 80,
    "reflect": 95,
}


class PhaseDriver(Protocol):
    """Execute one phase and return the produced JSON object."""

    def execute_phase(self, *, handle: RunHandle, phase_packet: dict[str, Any]) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class PhaseOutcome:
    terminal: bool
    status: str
    summary: str
    next_phase: str | None
    result_payload: dict[str, Any] | None = None
    reason: str | None = None


def default_validate_output_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["summary", "passed", "metric_name", "metric_value", "threshold", "checks"],
        "properties": {
            "summary": {"type": "string"},
            "passed": {"type": "boolean"},
            "metric_name": {"type": "string"},
            "metric_value": {},
            "threshold": {},
            "checks": {"type": "array"},
        },
        "additionalProperties": True,
    }


def normalize_runtime_contract(value: Any) -> dict[str, Any]:
    runtime = value if isinstance(value, dict) else {}
    loop = runtime.get("loop") if isinstance(runtime.get("loop"), dict) else {}
    max_iterations = loop.get("max_iterations")
    max_runtime_seconds = loop.get("max_runtime_seconds")
    if not isinstance(max_iterations, int) or max_iterations <= 0:
        max_iterations = DEFAULT_LOOP_MAX_ITERATIONS
    if not isinstance(max_runtime_seconds, int) or max_runtime_seconds <= 0:
        max_runtime_seconds = DEFAULT_LOOP_MAX_RUNTIME_SECONDS
    return {
        "loop": {
            "max_iterations": max_iterations,
            "max_runtime_seconds": max_runtime_seconds,
        }
    }


def normalize_validate_output_schema(value: Any) -> dict[str, Any]:
    schema = value if isinstance(value, dict) else {}
    if not schema:
        return {}
    return schema


def phase_state_path(handle: RunHandle) -> Path:
    return handle.run_dir / "phase_state.json"


def phase_artifact_path(handle: RunHandle, phase: str) -> Path:
    return handle.run_dir / f"{phase}.json"


def load_phase_state(handle: RunHandle) -> dict[str, Any]:
    return _read_json(phase_state_path(handle))


def _write_phase_state(handle: RunHandle, payload: dict[str, Any]) -> dict[str, Any]:
    payload = dict(payload)
    payload["updated_at"] = utc_now()
    _write_json(phase_state_path(handle), payload)
    return payload


def _upsert_loop_controller_object(handle: RunHandle, payload: dict[str, Any]) -> None:
    run = handle.run_json()
    work_id = run.get("work_id")
    store = Store(handle.project_root)
    work_links = [{"type": "spawned_by", "target": f"work_item:{work_id}"}] if isinstance(work_id, str) and work_id and store.read("work_item", work_id) else []
    store.upsert(
        kind="controller",
        object_id=f"controller-{handle.run_id}",
        status=str(handle.state_json().get("status") or "running"),
        title=str(run.get("title") or handle.run_id),
        summary=str(payload.get("goal") or run.get("title") or handle.run_id),
        source="loop",
        links=work_links,
        payload={
            "run_id": handle.run_id,
            "work_id": work_id,
            "work_revision": run.get("work_revision"),
            "controller_type": "loop",
            "phase_state_path": str(phase_state_path(handle)),
            "child_run_ids": payload.get("loop", {}).get("child_run_ids", []),
            "active_child_run_id": payload.get("loop", {}).get("active_child_run_id"),
        },
    )


def minimal_task_authority(strict_task: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "work_id": strict_task.get("work_id"),
        "work_revision": strict_task.get("revision"),
        "title": strict_task.get("title"),
        "goal_statement": strict_task.get("goal_statement"),
        "constraints": strict_task.get("constraints", []),
        "implementation_recipe": strict_task.get("implementation_recipe", []),
        "eval_entrypoint": strict_task.get("eval_entrypoint", {}),
        "primary_metric": strict_task.get("primary_metric", {}),
        "failure_classes": strict_task.get("failure_classes", []),
        "runtime_contract": normalize_runtime_contract(strict_task.get("runtime_contract")),
        "validate_output_schema": normalize_validate_output_schema(strict_task.get("validate_output_schema")),
        "review_binding": strict_task.get("review_binding", {}),
        "authority_context": strict_task.get("authority_context", {}),
    }
    if isinstance(strict_task.get("review_expectation"), dict):
        payload["review_expectation"] = strict_task.get("review_expectation")
    return payload


def initialize_run_phase_state(
    handle: RunHandle,
    *,
    strict_task: dict[str, Any],
    goal: str,
    target: str | None = None,
    prior_reflect: dict[str, Any] | None = None,
    review_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    phase_state = {
        "schema_version": 1,
        "mode": "run_once",
        "goal": goal,
        "target": target,
        "strict_task": minimal_task_authority(strict_task),
        "current_phase": "plan",
        "phase_statuses": {},
        "artifacts": {},
        "validate_passed": False,
        "final_summary": None,
        "next_hint": None,
        "prior_reflect": prior_reflect or {},
        "review_context": review_context or {},
        "command_authority": command_prompt_authority("run"),
        "created_at": utc_now(),
    }
    _update_state(handle, status="running", phase="plan", progress_pct=1)
    _append_event(handle, "run phase state initialized", kind="prepare")
    return _write_phase_state(handle, phase_state)


def initialize_loop_controller(
    handle: RunHandle,
    *,
    strict_task: dict[str, Any],
    goal: str,
    target: str | None = None,
) -> dict[str, Any]:
    runtime_contract = normalize_runtime_contract(strict_task.get("runtime_contract"))
    review_binding = strict_task.get("review_binding") if isinstance(strict_task.get("review_binding"), dict) else {}
    review_target = review_binding.get("target") if isinstance(review_binding.get("target"), str) else None
    controller = {
        "schema_version": 1,
        "mode": "loop_parent",
        "goal": goal,
        "target": target,
        "strict_task": minimal_task_authority(strict_task),
        "loop": {
            "max_iterations": runtime_contract["loop"]["max_iterations"],
            "max_runtime_seconds": runtime_contract["loop"]["max_runtime_seconds"],
            "started_at_epoch": time(),
            "iterations_attempted": 0,
            "child_run_ids": [],
            "active_child_run_id": None,
            "last_failure_summary": None,
            "last_reflect": {},
            "budget_exhausted_by": None,
            "final_outcome": None,
            "review_context": latest_fresh_review_context(
                handle.project_root,
                work_id=str(handle.run_json().get("work_id") or "") or None,
                target=review_target,
            ),
        },
        "command_authority": command_prompt_authority("loop"),
        "created_at": utc_now(),
    }
    _update_state(handle, status="running", phase="plan", progress_pct=1)
    _append_event(handle, "loop controller initialized", kind="prepare")
    payload = _write_phase_state(handle, controller)
    _upsert_loop_controller_object(handle, payload)
    return payload


def build_live_packet(handle: RunHandle) -> dict[str, Any]:
    run = handle.run_json()
    controller = load_phase_state(handle)
    packet = {
        "schema_version": 1,
        "protocol": "thoth-runtime/v2",
        "packet_kind": "phase_execution",
        "prepared_at": utc_now(),
        "project_root": str(handle.project_root.resolve()),
        "run_id": handle.run_id,
        "kind": run.get("kind"),
        "command_id": run.get("kind"),
        "work_id": run.get("work_id"),
        "work_revision": run.get("work_revision"),
        "title": run.get("title"),
        "goal": controller.get("goal"),
        "target": controller.get("target"),
        "host": run.get("host"),
        "executor": run.get("executor"),
        "dispatch_mode": run.get("dispatch_mode"),
        "sleep_requested": bool(run.get("sleep_requested")),
        "strict_task": controller.get("strict_task", {}),
        "command_authority": controller.get("command_authority", command_prompt_authority(str(run.get("kind") or "run"))),
        "phase_state": {
            "current_phase": controller.get("current_phase"),
            "phase_statuses": controller.get("phase_statuses", {}),
        },
        "paths": {
            "run_dir": str(handle.run_dir),
            "state": str(handle.run_dir / "state.json"),
            "events": str(handle.run_dir / "events.jsonl"),
            "result": str(handle.run_dir / "result.json"),
            "phase_state": str(phase_state_path(handle)),
        },
    }
    if controller.get("mode") == "loop_parent":
        packet["loop"] = controller.get("loop", {})
    return packet


def _phase_input_for_run(handle: RunHandle, controller: dict[str, Any]) -> dict[str, Any]:
    phase = str(controller.get("current_phase") or "plan")
    strict_task = controller.get("strict_task") if isinstance(controller.get("strict_task"), dict) else {}
    packet = {
        "schema_version": 1,
        "run_id": handle.run_id,
        "work_id": handle.run_json().get("work_id"),
        "work_revision": handle.run_json().get("work_revision"),
        "phase": phase,
        "goal": controller.get("goal"),
        "target": controller.get("target"),
        "strict_task": strict_task,
        "prior_artifacts": controller.get("artifacts", {}),
        "prior_reflect": controller.get("prior_reflect", {}),
        "review_context": controller.get("review_context", {}),
        "budget": {
            "remaining_exec_attempts": 1,
        },
        "command_authority": controller.get("command_authority", command_prompt_authority("run")),
        "phase_authority": phase_prompt_authority(phase),
        "output_contract": {
            "required_fields": list(PHASE_REQUIRED_FIELDS[phase]),
            "summary_budget_utf8": phase_prompt_authority(phase)["summary_budget_utf8"],
            "validate_output_schema": strict_task.get("validate_output_schema") if phase == "validate" else None,
            "plan_artifact_required": phase == "execute",
        },
    }
    if phase == "execute":
        packet["required_plan_artifact"] = controller.get("artifacts", {}).get("plan") if isinstance(controller.get("artifacts"), dict) else None
    return packet


def _maybe_activate_next_child(handle: RunHandle, controller: dict[str, Any]) -> dict[str, Any]:
    loop = controller.get("loop") if isinstance(controller.get("loop"), dict) else {}
    active_child_id = loop.get("active_child_run_id")
    if isinstance(active_child_id, str) and active_child_id.strip():
        return controller
    if _loop_budget_exhausted(controller):
        return controller
    loop["iterations_attempted"] = int(loop.get("iterations_attempted") or 0) + 1
    iteration_index = int(loop["iterations_attempted"])
    child_handle = create_child_run(
        handle,
        strict_task=controller.get("strict_task", {}),
        goal=str(controller.get("goal") or handle.run_json().get("title") or handle.run_id),
        iteration_index=iteration_index,
        prior_reflect=loop.get("last_reflect") if isinstance(loop.get("last_reflect"), dict) else {},
        review_context=loop.get("review_context") if isinstance(loop.get("review_context"), dict) else {},
    )
    loop["active_child_run_id"] = child_handle.run_id
    child_ids = loop.get("child_run_ids") if isinstance(loop.get("child_run_ids"), list) else []
    loop["child_run_ids"] = [*child_ids, child_handle.run_id]
    controller["loop"] = loop
    _update_state(handle, phase="plan", progress_pct=max(1, int(handle.state_json().get("progress_pct") or 1)))
    _append_event(
        handle,
        f"loop iteration {iteration_index} started",
        kind="loop",
        payload={"child_run_id": child_handle.run_id, "iteration_index": iteration_index},
    )
    payload = _write_phase_state(handle, controller)
    _upsert_loop_controller_object(handle, payload)
    return payload


def _phase_input_for_loop_parent(handle: RunHandle, controller: dict[str, Any]) -> dict[str, Any]:
    controller = _maybe_activate_next_child(handle, controller)
    loop = controller.get("loop") if isinstance(controller.get("loop"), dict) else {}
    active_child_id = str(loop.get("active_child_run_id") or "").strip()
    if not active_child_id:
        reason = str(loop.get("budget_exhausted_by") or "loop_finished")
        return {
            "schema_version": 1,
            "run_id": handle.run_id,
            "terminal": True,
            "reason": reason,
            "loop": loop,
        }
    child_handle = RunHandle(project_root=handle.project_root, run_id=active_child_id)
    child_controller = load_phase_state(child_handle)
    payload = _phase_input_for_run(child_handle, child_controller)
    payload["parent_run_id"] = handle.run_id
    payload["iteration_index"] = child_handle.run_json().get("iteration_index")
    payload["loop"] = {
        "max_iterations": loop.get("max_iterations"),
        "max_runtime_seconds": loop.get("max_runtime_seconds"),
        "iterations_attempted": loop.get("iterations_attempted"),
    }
    return payload


def next_phase_payload(project_root: Path, run_id: str) -> dict[str, Any]:
    handle = RunHandle(project_root=project_root.resolve(), run_id=run_id)
    controller = load_phase_state(handle)
    if not controller:
        raise FileNotFoundError(f"Run {run_id} is missing phase_state.json")
    mode = controller.get("mode")
    if mode == "loop_parent":
        return _phase_input_for_loop_parent(handle, controller)
    return _phase_input_for_run(handle, controller)


def _require_phase_payload(phase: str, payload: dict[str, Any], *, validate_schema: dict[str, Any] | None = None) -> dict[str, Any]:
    return validate_phase_output(phase, payload, validate_schema=validate_schema)


def _write_phase_artifact(handle: RunHandle, phase: str, payload: dict[str, Any]) -> str:
    path = phase_artifact_path(handle, phase)
    _write_json(path, payload)
    record_artifact(handle.project_root, handle.run_id, path=str(path), label=path.name, artifact_kind="phase")
    run = handle.run_json()
    Store(handle.project_root).upsert(
        kind="phase_result",
        object_id=f"{handle.run_id}-{phase}",
        status="completed",
        title=f"{handle.run_id} {phase}",
        summary=str(payload.get("summary") or phase),
        source="run",
        links=[{"type": "produced_by", "target": f"run:{handle.run_id}"}],
        payload={
            "run_id": handle.run_id,
            "work_id": run.get("work_id"),
            "work_revision": run.get("work_revision"),
            "phase": phase,
            "artifact_path": str(path),
            "output": payload,
        },
    )
    return str(path)


def _build_run_result_payload(controller: dict[str, Any]) -> dict[str, Any]:
    strict_task = controller.get("strict_task") if isinstance(controller.get("strict_task"), dict) else {}
    validate_payload = {}
    validate_artifact = controller.get("artifacts", {}).get("validate")
    if isinstance(validate_artifact, str):
        validate_payload = _read_json(Path(validate_artifact))
    metric_name = validate_payload.get("metric_name")
    metric_value = validate_payload.get("metric_value")
    metrics = {}
    if isinstance(metric_name, str) and metric_name:
        metrics[metric_name] = metric_value
    return {
        "phase_statuses": controller.get("phase_statuses", {}),
        "validate_passed": bool(controller.get("validate_passed")),
        "final_summary": controller.get("final_summary"),
        "artifacts": controller.get("artifacts", {}),
        "next_hint": controller.get("next_hint"),
        "metrics": metrics,
        "primary_metric": strict_task.get("primary_metric", {}),
    }


def _plan_has_authority_gaps(payload: dict[str, Any]) -> bool:
    if payload.get("authority_complete") is not True:
        return True
    open_gaps = payload.get("open_gaps")
    if isinstance(open_gaps, list) and any(isinstance(item, str) and item.strip() for item in open_gaps):
        return True
    forbidden = payload.get("forbidden_assumptions_used")
    if isinstance(forbidden, list) and any(isinstance(item, str) and item.strip() for item in forbidden):
        return True
    return False


def _phase_outcome_for_run(handle: RunHandle, controller: dict[str, Any], phase: str, payload: dict[str, Any]) -> PhaseOutcome:
    phase_statuses = controller.get("phase_statuses") if isinstance(controller.get("phase_statuses"), dict) else {}
    phase_statuses[phase] = "completed"
    controller["phase_statuses"] = phase_statuses
    controller.setdefault("artifacts", {})
    controller["artifacts"][phase] = _write_phase_artifact(handle, phase, payload)
    controller["final_summary"] = str(payload.get("summary") or controller.get("final_summary") or "").strip() or None
    controller["next_hint"] = payload.get("next_plan_hint") if phase == "reflect" else controller.get("next_hint")
    _write_phase_state(handle, controller)
    if phase == "plan":
        if _plan_has_authority_gaps(payload):
            phase_statuses["plan"] = "failed"
            controller["phase_statuses"] = phase_statuses
            controller["next_hint"] = "return to discuss and close authority gaps"
            _write_phase_state(handle, controller)
            return PhaseOutcome(
                True,
                "failed",
                str(payload.get("summary") or "plan needs input"),
                None,
                result_payload=_build_run_result_payload(controller),
                reason="needs_input",
            )
        _update_state(handle, phase="execute", progress_pct=RUN_PHASE_PROGRESS["plan"])
        return PhaseOutcome(False, "running", str(payload.get("summary") or "plan complete"), "execute")
    if phase == "execute":
        _update_state(handle, phase="validate", progress_pct=RUN_PHASE_PROGRESS["execute"])
        return PhaseOutcome(False, "running", str(payload.get("summary") or "execute complete"), "validate")
    if phase == "validate":
        passed = bool(payload.get("passed"))
        controller["validate_passed"] = passed
        phase_statuses["validate"] = "completed" if passed else "failed"
        controller["phase_statuses"] = phase_statuses
        controller["next_hint"] = "reflect on validation evidence" if passed else "reflect before deciding next iteration"
        _write_phase_state(handle, controller)
        _update_state(handle, phase="reflect", progress_pct=RUN_PHASE_PROGRESS["validate"])
        return PhaseOutcome(False, "running", str(payload.get("summary") or "validation complete"), "reflect")
    if phase == "reflect":
        phase_statuses["reflect"] = "completed"
        controller["phase_statuses"] = phase_statuses
        if payload.get("next_plan_hint"):
            controller["next_hint"] = payload.get("next_plan_hint")
        elif payload.get("next_recommendation"):
            controller["next_hint"] = payload.get("next_recommendation")
        _write_phase_state(handle, controller)
        result_payload = _build_run_result_payload(controller)
        if bool(controller.get("validate_passed")):
            return PhaseOutcome(True, "completed", str(payload.get("summary") or "reflection complete"), None, result_payload=result_payload)
        reason = str(payload.get("failure_class") or "validation_failed")
        return PhaseOutcome(True, "failed", str(payload.get("summary") or "reflection complete"), None, result_payload=result_payload, reason=reason)
    raise ValueError(f"unsupported phase: {phase}")


def submit_phase_output(project_root: Path, run_id: str, *, phase: str, payload: dict[str, Any]) -> dict[str, Any]:
    handle = RunHandle(project_root=project_root.resolve(), run_id=run_id)
    controller = load_phase_state(handle)
    if not controller:
        raise FileNotFoundError(f"Run {run_id} is missing phase_state.json")
    if controller.get("mode") == "loop_parent":
        return _submit_phase_to_loop_parent(handle, phase=phase, payload=payload)
    current_phase = str(controller.get("current_phase") or "")
    if current_phase != phase:
        raise ValueError(f"run {run_id} expects phase {current_phase}, not {phase}")
    strict_task = controller.get("strict_task") if isinstance(controller.get("strict_task"), dict) else {}
    validate_schema = strict_task.get("validate_output_schema") if phase == "validate" else None
    normalized_payload = _require_phase_payload(
        phase,
        payload,
        validate_schema=validate_schema if isinstance(validate_schema, dict) else None,
    )
    heartbeat_run(project_root, run_id, phase=phase, progress_pct=RUN_PHASE_PROGRESS.get(phase, 50), note=f"{phase} output received")
    outcome = _phase_outcome_for_run(handle, controller, phase, normalized_payload)
    if outcome.terminal and outcome.status == "completed":
        complete_run(project_root, run_id, summary=outcome.summary, result_payload=outcome.result_payload)
        return {"terminal": True, "status": "completed", "summary": outcome.summary, "result": outcome.result_payload}
    if outcome.terminal and outcome.status == "failed":
        fail_run(project_root, run_id, summary=outcome.summary, reason=outcome.reason, result_payload=outcome.result_payload)
        return {"terminal": True, "status": "failed", "summary": outcome.summary, "result": outcome.result_payload, "reason": outcome.reason}
    controller = load_phase_state(handle)
    controller["current_phase"] = outcome.next_phase
    _write_phase_state(handle, controller)
    return {"terminal": False, "status": "running", "next_phase": outcome.next_phase, "summary": outcome.summary}


def _loop_budget_exhausted(controller: dict[str, Any]) -> bool:
    loop = controller.get("loop") if isinstance(controller.get("loop"), dict) else {}
    max_iterations = int(loop.get("max_iterations") or DEFAULT_LOOP_MAX_ITERATIONS)
    iterations_attempted = int(loop.get("iterations_attempted") or 0)
    started_at_epoch = float(loop.get("started_at_epoch") or time())
    max_runtime_seconds = int(loop.get("max_runtime_seconds") or DEFAULT_LOOP_MAX_RUNTIME_SECONDS)
    if iterations_attempted >= max_iterations and not loop.get("active_child_run_id"):
        loop["budget_exhausted_by"] = "max_iterations"
        controller["loop"] = loop
        return True
    if (time() - started_at_epoch) >= max_runtime_seconds and not loop.get("active_child_run_id"):
        loop["budget_exhausted_by"] = "max_runtime_seconds"
        controller["loop"] = loop
        return True
    return False


def create_child_run(
    parent_handle: RunHandle,
    *,
    strict_task: dict[str, Any],
    goal: str,
    iteration_index: int,
    prior_reflect: dict[str, Any] | None = None,
    review_context: dict[str, Any] | None = None,
) -> RunHandle:
    from .ledger import create_run

    run = parent_handle.run_json()
    child = create_run(
        parent_handle.project_root,
        kind="run",
        title=str(strict_task.get("title") or run.get("title") or run.get("work_id") or "run"),
        work_id=str(run.get("work_id") or strict_task.get("work_id") or "") or None,
        work_revision=int(run.get("work_revision") or strict_task.get("revision") or 0) or None,
        host=str(run.get("host") or "codex"),
        executor=str(run.get("executor") or "claude"),
        dispatch_mode=str(run.get("dispatch_mode") or "live_native"),
        sleep_requested=bool(run.get("sleep_requested")),
        max_runtime_seconds=int(
            normalize_runtime_contract(strict_task.get("runtime_contract"))["loop"]["max_runtime_seconds"]
        ),
        target=run.get("target"),
        parent_run_id=parent_handle.run_id,
        iteration_index=iteration_index,
    )
    initialize_run_phase_state(
        child,
        strict_task=strict_task,
        goal=goal,
        target=run.get("target"),
        prior_reflect=prior_reflect,
        review_context=review_context,
    )
    return child


def _submit_phase_to_loop_parent(handle: RunHandle, *, phase: str, payload: dict[str, Any]) -> dict[str, Any]:
    controller = load_phase_state(handle)
    loop = controller.get("loop") if isinstance(controller.get("loop"), dict) else {}
    active_child_id = str(loop.get("active_child_run_id") or "").strip()
    if not active_child_id:
        raise ValueError(f"loop {handle.run_id} has no active child run")
    child_result = submit_phase_output(handle.project_root, active_child_id, phase=phase, payload=payload)
    if child_result.get("terminal") is not True:
        child_handle = RunHandle(project_root=handle.project_root, run_id=active_child_id)
        child_controller = load_phase_state(child_handle)
        _update_state(handle, phase=str(child_controller.get("current_phase") or phase), progress_pct=int(child_handle.state_json().get("progress_pct") or 1))
        return {
            "terminal": False,
            "status": "running",
            "active_child_run_id": active_child_id,
            "next_phase": child_result.get("next_phase"),
            "iteration_index": loop.get("iterations_attempted"),
        }

    child_result_payload = child_result.get("result") if isinstance(child_result.get("result"), dict) else {}
    loop["active_child_run_id"] = None
    if child_result.get("status") == "completed" and child_result_payload.get("validate_passed") is True:
        loop["final_outcome"] = "validated"
        loop["budget_exhausted_by"] = None
        controller["loop"] = loop
        _write_phase_state(handle, controller)
        _upsert_loop_controller_object(handle, controller)
        result_payload = {
            "phase_statuses": {"loop": "completed"},
            "validate_passed": True,
            "final_summary": child_result.get("summary"),
            "artifacts": {
                "child_run_ids": loop.get("child_run_ids", []),
                "last_child_run_id": active_child_id,
            },
            "next_hint": None,
            "iterations_attempted": loop.get("iterations_attempted"),
            "child_run_ids": loop.get("child_run_ids", []),
            "last_failure_summary": loop.get("last_failure_summary"),
            "budget_exhausted_by": None,
            "final_outcome": "validated",
        }
        complete_run(handle.project_root, handle.run_id, summary=str(child_result.get("summary") or "loop completed"), result_payload=result_payload)
        return {"terminal": True, "status": "completed", "summary": child_result.get("summary"), "result": result_payload}

    loop["last_failure_summary"] = child_result.get("summary")
    child_controller = load_phase_state(RunHandle(project_root=handle.project_root, run_id=active_child_id))
    reflect_path = child_controller.get("artifacts", {}).get("reflect") if isinstance(child_controller.get("artifacts"), dict) else None
    loop["last_reflect"] = _read_json(Path(reflect_path)) if isinstance(reflect_path, str) and reflect_path else {}
    controller["loop"] = loop
    controller = _write_phase_state(handle, controller)
    _upsert_loop_controller_object(handle, controller)
    if _loop_budget_exhausted(controller):
        loop = controller.get("loop") if isinstance(controller.get("loop"), dict) else {}
        loop["final_outcome"] = "budget_exhausted"
        controller["loop"] = loop
        _write_phase_state(handle, controller)
        _upsert_loop_controller_object(handle, controller)
        result_payload = {
            "phase_statuses": {"loop": "failed"},
            "validate_passed": False,
            "final_summary": child_result.get("summary"),
            "artifacts": {"child_run_ids": loop.get("child_run_ids", [])},
            "next_hint": loop.get("last_reflect", {}).get("next_plan_hint"),
            "iterations_attempted": loop.get("iterations_attempted"),
            "child_run_ids": loop.get("child_run_ids", []),
            "last_failure_summary": loop.get("last_failure_summary"),
            "budget_exhausted_by": loop.get("budget_exhausted_by"),
            "final_outcome": "budget_exhausted",
        }
        fail_run(
            handle.project_root,
            handle.run_id,
            summary=str(child_result.get("summary") or "loop exhausted budget"),
            reason=str(loop.get("budget_exhausted_by") or "budget_exhausted"),
            result_payload=result_payload,
        )
        return {
            "terminal": True,
            "status": "failed",
            "summary": child_result.get("summary"),
            "reason": loop.get("budget_exhausted_by"),
            "result": result_payload,
        }
    _append_event(
        handle,
        "loop iteration failed; next iteration may start",
        kind="loop",
        level="warning",
        payload={"failed_child_run_id": active_child_id},
    )
    _update_state(handle, phase="plan", progress_pct=max(1, int(handle.state_json().get("progress_pct") or 1)))
    return {
        "terminal": False,
        "status": "running",
        "next_phase": "plan",
        "summary": child_result.get("summary"),
        "iteration_index": loop.get("iterations_attempted"),
    }


def execute_background_controller(
    project_root: Path,
    run_id: str,
    *,
    driver: PhaseDriver,
) -> int:
    handle = RunHandle(project_root=project_root.resolve(), run_id=run_id)
    while True:
        state = handle.state_json()
        if state.get("status") == "stopping":
            return 0
        phase_packet = next_phase_payload(project_root, run_id)
        if phase_packet.get("terminal") is True:
            return 0
        phase = str(phase_packet.get("phase") or "")
        phase_output = driver.execute_phase(handle=handle, phase_packet=phase_packet)
        response = submit_phase_output(project_root, run_id, phase=phase, payload=phase_output)
        if response.get("terminal") is True:
            return 0 if response.get("status") == "completed" else 1
