"""Unified foreground/background runtime driver for run and loop execution."""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .io import _read_json
from .ledger import _append_event, fail_run, heartbeat_run
from .model import ACTIVE_STATUSES, RunHandle, utc_now
from .phases import PhaseDriver, next_phase_payload, submit_phase_output


class RuntimeEventSink(Protocol):
    def emit(self, event: dict[str, Any]) -> None:
        ...


@dataclass
class JsonlStdoutSink:
    stream: Any = sys.stdout

    def emit(self, event: dict[str, Any]) -> None:
        self.stream.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
        self.stream.flush()


class SilentSink:
    def emit(self, event: dict[str, Any]) -> None:
        return None


def _event(handle: RunHandle, event_type: str, **payload: Any) -> dict[str, Any]:
    event = {
        "type": event_type,
        "ts": utc_now(),
        "run_id": handle.run_id,
    }
    event.update({key: value for key, value in payload.items() if value is not None})
    return event


def _emit(handle: RunHandle, sink: RuntimeEventSink, event_type: str, **payload: Any) -> None:
    event = _event(handle, event_type, **payload)
    sink.emit(event)
    message = event_type
    phase = payload.get("phase")
    if isinstance(phase, str) and phase:
        message = f"{event_type} {phase}"
    _append_event(handle, message, kind="runtime", payload={"event": event})


def _strict_task_from_packet(phase_packet: dict[str, Any]) -> dict[str, Any]:
    task = phase_packet.get("strict_task")
    return task if isinstance(task, dict) else {}


def _eval_command(strict_task: dict[str, Any]) -> str:
    entrypoint = strict_task.get("eval_entrypoint")
    if isinstance(entrypoint, dict) and isinstance(entrypoint.get("command"), str):
        return entrypoint["command"].strip()
    return ""


def _fail_missing_eval(handle: RunHandle, sink: RuntimeEventSink, phase_packet: dict[str, Any]) -> int:
    strict_task = _strict_task_from_packet(phase_packet)
    command = _eval_command(strict_task)
    if command:
        return -1
    summary = "Plan failed: eval entrypoint missing."
    reason = "missing eval_entrypoint.command"
    _emit(handle, sink, "thoth.phase.failed", phase="plan", summary=summary, reason=reason)
    fail_run(
        handle.project_root,
        handle.run_id,
        summary=summary,
        reason=reason,
        result_payload={
            "phase_statuses": {"plan": "failed"},
            "validate_passed": False,
            "final_summary": summary,
            "artifacts": {},
            "next_hint": "add eval_entrypoint.command to the work item and rerun",
            "blocker": reason,
        },
    )
    _emit(handle, sink, "thoth.run.terminal", status="failed", summary=summary, reason=reason)
    return 1


def execute_runtime_controller(
    project_root: Path,
    run_id: str,
    *,
    driver: PhaseDriver,
    sink: RuntimeEventSink | None = None,
    heartbeat_interval_seconds: float = 300.0,
) -> int:
    """Run the mechanical controller until terminal state using one phase driver."""

    handle = RunHandle(project_root=project_root.resolve(), run_id=run_id)
    event_sink = sink or SilentSink()
    run = handle.run_json()
    _emit(
        handle,
        event_sink,
        "thoth.run.started",
        kind=run.get("kind"),
        work_id=run.get("work_id"),
        executor=run.get("executor"),
        dispatch_mode=run.get("dispatch_mode"),
    )
    last_heartbeat = 0.0
    while True:
        state = handle.state_json()
        if state.get("status") == "stopping":
            _emit(handle, event_sink, "thoth.run.terminal", status="stopped", summary="stop requested")
            return 0
        if state.get("status") not in ACTIVE_STATUSES:
            terminal_status = state.get("status")
            _emit(handle, event_sink, "thoth.run.terminal", status=terminal_status, summary="run already terminal")
            return 0 if terminal_status == "completed" else 1

        phase_packet = next_phase_payload(project_root, run_id)
        if phase_packet.get("terminal") is True:
            _emit(handle, event_sink, "thoth.run.terminal", status=state.get("status"), reason=phase_packet.get("reason"))
            return 0
        phase = str(phase_packet.get("phase") or "")
        parent_run_id = phase_packet.get("parent_run_id")
        iteration_index = phase_packet.get("iteration_index")
        if phase == "plan":
            missing_eval_result = _fail_missing_eval(handle, event_sink, phase_packet)
            if missing_eval_result >= 0:
                return missing_eval_result
        now = time.time()
        if now - last_heartbeat >= heartbeat_interval_seconds:
            heartbeat_run(project_root, run_id, phase=phase, progress_pct=int(state.get("progress_pct") or 1), note=f"runtime driver active: {phase}")
            _emit(handle, event_sink, "thoth.heartbeat", phase=phase, progress_pct=handle.state_json().get("progress_pct"))
            last_heartbeat = now
        _emit(
            handle,
            event_sink,
            "thoth.phase.started",
            phase=phase,
            parent_run_id=parent_run_id,
            iteration_index=iteration_index,
        )
        try:
            phase_output = driver.execute_phase(handle=handle, phase_packet=phase_packet)
            response = submit_phase_output(project_root, run_id, phase=phase, payload=phase_output)
        except Exception as exc:
            summary = f"{phase} phase failed."
            reason = str(exc)
            _emit(handle, event_sink, "thoth.phase.failed", phase=phase, summary=summary, reason=reason)
            fail_run(
                project_root,
                run_id,
                summary=summary,
                reason=reason,
                result_payload={
                    "phase_statuses": {phase: "failed"},
                    "validate_passed": False,
                    "final_summary": summary,
                    "artifacts": {},
                    "next_hint": None,
                },
            )
            _emit(handle, event_sink, "thoth.run.terminal", status="failed", summary=summary, reason=reason)
            return 1
        _emit(
            handle,
            event_sink,
            "thoth.phase.completed",
            phase=phase,
            summary=response.get("summary"),
            status=response.get("status"),
            terminal=response.get("terminal"),
            next_phase=response.get("next_phase"),
            iteration_index=response.get("iteration_index"),
        )
        if response.get("terminal") is True:
            status = str(response.get("status") or _read_json(handle.run_dir / "state.json").get("status") or "")
            _emit(handle, event_sink, "thoth.run.terminal", status=status, summary=response.get("summary"), reason=response.get("reason"))
            return 0 if status == "completed" else 1
