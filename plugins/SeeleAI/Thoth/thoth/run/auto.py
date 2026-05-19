"""Auto controller execution and watch streams for unattended ready work."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from time import sleep, time
from typing import Any, Callable

from thoth.objects import Store, utc_now
from thoth.plan.store import load_work_for_execution
from thoth.run.controllers import list_auto_actionable_work
from thoth.run.driver import JsonlStdoutSink, RuntimeEventSink, SilentSink, execute_runtime_controller
from thoth.run.io import _read_json, _write_json, local_registry_root
from thoth.run.ledger import _append_event
from thoth.run.model import ACTIVE_STATUSES, RunHandle
from thoth.run.packets import prepare_execution
from thoth.run.service import attach_run, list_active_runs
from thoth.run.supervisor import supervisor_process_alive, write_controller_supervisor


DriverFactory = Callable[[RunHandle], Any]
AUTO_CONTROLLER_ACTIVE_STATUSES = {"queued", "running", "idle"}
AUTO_CONTROLLER_TERMINAL_STATUSES = {"completed", "paused", "stopped", "cancelled", "failed"}


def auto_heartbeat_interval_seconds() -> float:
    raw = os.environ.get("THOTH_AUTO_HEARTBEAT_SECONDS", "120")
    try:
        return max(1.0, float(raw))
    except ValueError:
        return 120.0


def _emit(sink: RuntimeEventSink, controller_id: str, event_type: str, **payload: Any) -> None:
    event = {"type": event_type, "ts": utc_now(), "controller_id": controller_id}
    event.update({key: value for key, value in payload.items() if value is not None})
    sink.emit(event)


def _update_controller(project_root: Path, controller: dict[str, Any], *, status: str, payload_updates: dict[str, Any]) -> dict[str, Any]:
    store = Store(project_root)
    payload = dict(controller.get("payload") if isinstance(controller.get("payload"), dict) else {})
    payload.update(payload_updates)
    return store.update(
        "controller",
        str(controller["object_id"]),
        expected_revision=int(controller.get("revision", 0)),
        updates={"status": status, "payload": payload},
        history_summary=f"auto controller -> {status}",
        source="auto",
    )


def _controller_local_dir(project_root: Path, controller_id: str) -> Path:
    return local_registry_root(project_root) / "controllers" / controller_id


def _controller_supervisor_path(project_root: Path, controller_id: str) -> Path:
    return _controller_local_dir(project_root, controller_id) / "supervisor.json"


def _write_controller_supervisor(project_root: Path, controller_id: str, *, pid: int, state: str) -> None:
    path = _controller_supervisor_path(project_root, controller_id)
    write_controller_supervisor(project_root, controller_id, path, pid=pid, state=state, runtime="auto_worker")


def _controller_worker_alive(project_root: Path, controller_id: str) -> bool:
    supervisor = _read_json(_controller_supervisor_path(project_root, controller_id))
    return supervisor_process_alive(
        supervisor,
        project_root=project_root,
        runtime="auto_worker",
        controller_id=controller_id,
    )


def spawn_auto_worker(project_root: Path, controller_id: str) -> int:
    cmd = [
        sys.executable,
        "-m",
        "thoth.cli",
        "auto-worker",
        "--project-root",
        str(project_root.resolve()),
        "--controller-id",
        controller_id,
    ]
    local_dir = _controller_local_dir(project_root, controller_id)
    local_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = local_dir / "auto-worker.stdout.log"
    stderr_path = local_dir / "auto-worker.stderr.log"
    stdout_handle = stdout_path.open("w", encoding="utf-8")
    stderr_handle = stderr_path.open("w", encoding="utf-8")
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(project_root),
            env=dict(os.environ),
            stdout=stdout_handle,
            stderr=stderr_handle,
            start_new_session=True,
        )
    finally:
        stdout_handle.close()
        stderr_handle.close()
    _write_controller_supervisor(project_root, controller_id, pid=proc.pid, state="running")
    return proc.pid


def _auto_controllers(project_root: Path) -> list[dict[str, Any]]:
    store = Store(project_root)
    rows: list[dict[str, Any]] = []
    for controller in store.list("controller"):
        payload = controller.get("payload") if isinstance(controller.get("payload"), dict) else {}
        if payload.get("controller_type") == "auto":
            rows.append(controller)
    rows.sort(key=lambda item: str(item.get("created_at") or item.get("updated_at") or ""), reverse=True)
    return rows


def find_reusable_auto_controller(project_root: Path) -> dict[str, Any] | None:
    for controller in _auto_controllers(project_root):
        status = str(controller.get("status") or "")
        if status in AUTO_CONTROLLER_ACTIVE_STATUSES:
            return controller
    return None


def auto_controller_fingerprint(controller: dict[str, Any]) -> dict[str, Any]:
    payload = controller.get("payload") if isinstance(controller.get("payload"), dict) else {}
    fingerprint = payload.get("request_fingerprint")
    return fingerprint if isinstance(fingerprint, dict) else {}


def auto_fingerprint_differences(existing: dict[str, Any], requested: dict[str, Any]) -> dict[str, dict[str, Any]]:
    diffs: dict[str, dict[str, Any]] = {}
    keys = sorted(set(existing) | set(requested))
    for key in keys:
        if existing.get(key) != requested.get(key):
            diffs[key] = {
                "existing": existing.get(key),
                "requested": requested.get(key),
            }
    return diffs


def list_auto_controller_statuses(project_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for controller in _auto_controllers(project_root):
        payload = controller.get("payload") if isinstance(controller.get("payload"), dict) else {}
        cursor = payload.get("cursor") if isinstance(payload.get("cursor"), dict) else {}
        controller_id = str(controller.get("object_id") or "")
        rows.append(
            {
                "controller_id": controller_id,
                "status": controller.get("status"),
                "state": payload.get("state"),
                "host": payload.get("host"),
                "executor": payload.get("executor"),
                "scope": payload.get("scope"),
                "fixed_queue": bool(payload.get("fixed_queue")),
                "elapsed_seconds": payload.get("elapsed_seconds"),
                "min_runtime_seconds": payload.get("min_runtime_seconds"),
                "rounds": payload.get("rounds"),
                "rounds_attempted": cursor.get("rounds_attempted"),
                "active_run_id": cursor.get("active_run_id"),
                "queue_count": len(payload.get("queue")) if isinstance(payload.get("queue"), list) else 0,
                "attempted_count": len(payload.get("attempted_work_ids")) if isinstance(payload.get("attempted_work_ids"), list) else 0,
                "completed_count": len(payload.get("completed_work_ids")) if isinstance(payload.get("completed_work_ids"), list) else 0,
                "failed_count": len(payload.get("failed_work_ids")) if isinstance(payload.get("failed_work_ids"), list) else 0,
                "worker_alive": _controller_worker_alive(project_root, controller_id),
                "updated_at": controller.get("updated_at"),
            }
        )
    return rows


def ensure_auto_worker(project_root: Path, controller_id: str) -> tuple[bool, int | None]:
    if _controller_worker_alive(project_root, controller_id):
        supervisor = _read_json(_controller_supervisor_path(project_root, controller_id))
        pid = supervisor.get("pid")
        return False, pid if isinstance(pid, int) else None
    return True, spawn_auto_worker(project_root, controller_id)


def _active_run_for_work(project_root: Path, work_id: str) -> str | None:
    for row in list_active_runs(project_root):
        if row.get("work_id") == work_id:
            return str(row.get("run_id"))
    runs_root = project_root / ".thoth" / "runs"
    if not runs_root.is_dir():
        return None
    for run_dir in sorted(runs_root.iterdir()):
        if not run_dir.is_dir():
            continue
        handle = RunHandle(project_root=project_root, run_id=run_dir.name)
        state = handle.state_json()
        run = handle.run_json()
        if state.get("status") in ACTIVE_STATUSES and run.get("work_id") == work_id:
            return handle.run_id
    return None


def _should_stop(controller: dict[str, Any]) -> bool:
    status = str(controller.get("status") or "")
    payload = controller.get("payload") if isinstance(controller.get("payload"), dict) else {}
    state = str(payload.get("state") or "")
    return status in {"stopped", "cancelled"} or state in {"stopped", "cancelled"}


def _controller_elapsed_seconds(payload: dict[str, Any], started_at: float) -> int:
    started = payload.get("started_at_epoch")
    if isinstance(started, (int, float)) and started > 0:
        return int(time() - float(started))
    return int(time() - started_at)


def _min_runtime_reached(payload: dict[str, Any], started_at: float) -> bool:
    min_runtime_seconds = int(payload.get("min_runtime_seconds") or 0)
    return _controller_elapsed_seconds(payload, started_at) >= max(0, min_runtime_seconds)


def _rounds_reached_after_min_runtime(payload: dict[str, Any], cursor: dict[str, Any], started_at: float) -> bool:
    rounds = payload.get("rounds")
    if not isinstance(rounds, int) or rounds <= 0:
        return False
    if not _min_runtime_reached(payload, started_at):
        return False
    return int(cursor.get("rounds_attempted") or 0) >= rounds


def _fixed_queue_actionable(project_root: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    refs = payload.get("work_refs") or payload.get("queue")
    if not isinstance(refs, list):
        return []
    rows: list[dict[str, Any]] = []
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        work_id = ref.get("work_id")
        if not isinstance(work_id, str) or not work_id:
            continue
        try:
            work = load_work_for_execution(project_root, work_id, require_ready=False)
        except Exception:
            continue
        status = str(work.get("ready_state") or work.get("status") or "")
        if status in {"ready", "active", "failed"}:
            rows.append(work)
    return rows


def _controller_actionable(project_root: Path, payload: dict[str, Any], *, scope: str) -> list[dict[str, Any]]:
    if payload.get("fixed_queue") is True:
        rows = _fixed_queue_actionable(project_root, payload)
    else:
        rows = list_auto_actionable_work(project_root, scope=scope)
    attempted = payload.get("attempted_work_ids")
    attempted_set = {item for item in attempted if isinstance(item, str)} if isinstance(attempted, list) else set()
    failed = payload.get("failed_work_ids")
    failed_set = {item for item in failed if isinstance(item, str)} if isinstance(failed, list) else set()
    return [
        row
        for row in rows
        if str(row.get("work_id") or "") not in attempted_set
        and str(row.get("work_id") or "") not in failed_set
    ]


def _queue_snapshot(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "work_id": row.get("work_id"),
            "revision": row.get("revision"),
            "title": row.get("title"),
            "status": row.get("ready_state") or row.get("status"),
            "priority": row.get("priority"),
        }
        for row in rows
    ]


def _append_unique(values: Any, item: str) -> list[str]:
    rows = [value for value in values if isinstance(value, str)] if isinstance(values, list) else []
    if item not in rows:
        rows.append(item)
    return rows


def _controller_snapshot(project_root: Path, controller: dict[str, Any]) -> dict[str, Any]:
    payload = controller.get("payload") if isinstance(controller.get("payload"), dict) else {}
    cursor = payload.get("cursor") if isinstance(payload.get("cursor"), dict) else {}
    controller_id = str(controller.get("object_id") or "")
    return {
        "type": "thoth.auto.snapshot",
        "ts": utc_now(),
        "controller_id": controller_id,
        "status": controller.get("status"),
        "state": payload.get("state"),
        "elapsed_seconds": payload.get("elapsed_seconds"),
        "min_runtime_seconds": payload.get("min_runtime_seconds"),
        "rounds_attempted": cursor.get("rounds_attempted"),
        "active_run_id": cursor.get("active_run_id"),
        "queue_count": len(payload.get("queue")) if isinstance(payload.get("queue"), list) else 0,
        "completed_count": len(payload.get("completed_work_ids")) if isinstance(payload.get("completed_work_ids"), list) else 0,
        "failed_count": len(payload.get("failed_work_ids")) if isinstance(payload.get("failed_work_ids"), list) else 0,
        "worker_alive": _controller_worker_alive(project_root, controller_id),
    }


def execute_auto_controller(
    project_root: Path,
    controller_id: str,
    *,
    driver_factory: DriverFactory,
    sink: RuntimeEventSink | None = None,
) -> int:
    event_sink = sink or SilentSink()
    store = Store(project_root)
    controller = store.read("controller", controller_id)
    if not controller:
        raise FileNotFoundError(f"controller:{controller_id} not found")
    payload = controller.get("payload") if isinstance(controller.get("payload"), dict) else {}
    if payload.get("controller_type") != "auto":
        raise ValueError(f"controller:{controller_id} is not an auto controller")
    _write_controller_supervisor(project_root, controller_id, pid=os.getpid(), state="running")

    started_at = time()
    rounds = payload.get("rounds")
    rounds_limit = rounds if isinstance(rounds, int) and rounds > 0 else None
    scope = str(payload.get("scope") or "all-open")
    host = str(payload.get("host") or "codex")
    executor = str(payload.get("executor") or "codex")
    controller = _update_controller(
        project_root,
        controller,
        status="running",
        payload_updates={
            "started_at": payload.get("started_at") or utc_now(),
            "started_at_epoch": payload.get("started_at_epoch") or time(),
            "state": "running",
            "last_heartbeat_at": utc_now(),
        },
    )
    _emit(event_sink, controller_id, "thoth.auto.started", scope=scope, rounds=rounds_limit)

    rounds_attempted = 0
    completed_work_ids = [item for item in payload.get("completed_work_ids", []) if isinstance(item, str)] if isinstance(payload.get("completed_work_ids"), list) else []
    last_idle_emit = 0.0
    heartbeat_interval = auto_heartbeat_interval_seconds()
    while True:
        controller = store.read("controller", controller_id) or controller
        if _should_stop(controller):
            _emit(event_sink, controller_id, "thoth.auto.stopped", reason="stop_requested")
            _write_controller_supervisor(project_root, controller_id, pid=os.getpid(), state="stopped")
            return 130
        payload = controller.get("payload") if isinstance(controller.get("payload"), dict) else {}
        cursor = payload.get("cursor") if isinstance(payload.get("cursor"), dict) else {}
        rounds_attempted = int(cursor.get("rounds_attempted") or rounds_attempted)
        if _rounds_reached_after_min_runtime(payload, cursor, started_at):
            controller = _update_controller(
                project_root,
                controller,
                status="paused",
                payload_updates={
                    "state": "budget_exhausted",
                    "budget_exhausted_by": "rounds_after_min_runtime",
                    "finished_at": utc_now(),
                    "elapsed_seconds": _controller_elapsed_seconds(payload, started_at),
                    "cursor": {**cursor, "rounds_attempted": rounds_attempted},
                },
            )
            _emit(event_sink, controller_id, "thoth.auto.paused", reason="rounds", rounds_attempted=rounds_attempted)
            _write_controller_supervisor(project_root, controller_id, pid=os.getpid(), state="paused")
            return 2

        actionable = _controller_actionable(project_root, payload, scope=scope)
        payload["queue"] = _queue_snapshot(actionable)
        if not actionable:
            elapsed = int(time() - started_at)
            if not _min_runtime_reached(payload, started_at):
                now = time()
                payload.update(
                    {
                        "state": "idle",
                        "elapsed_seconds": elapsed,
                        "last_heartbeat_at": utc_now(),
                        "queue": [],
                    }
                )
                controller = _update_controller(project_root, controller, status="idle", payload_updates=payload)
                if now - last_idle_emit >= heartbeat_interval:
                    _emit(
                        event_sink,
                        controller_id,
                        "thoth.auto.idle",
                        elapsed_seconds=elapsed,
                        min_runtime_seconds=payload.get("min_runtime_seconds"),
                    )
                    last_idle_emit = now
                sleep(min(5.0, heartbeat_interval))
                continue
            controller = _update_controller(
                project_root,
                controller,
                status="completed",
                payload_updates={
                    "state": "completed",
                    "finished_at": utc_now(),
                    "elapsed_seconds": elapsed,
                    "completed_work_ids": completed_work_ids,
                    "queue": [],
                },
            )
            _emit(event_sink, controller_id, "thoth.auto.terminal", status="completed", elapsed_seconds=elapsed)
            _write_controller_supervisor(project_root, controller_id, pid=os.getpid(), state="completed")
            return 0

        work = actionable[0]
        work_id = str(work.get("work_id") or "")
        work_status = str(work.get("ready_state") or "")
        active_run_id = _active_run_for_work(project_root, work_id) if work_status == "active" else None
        if active_run_id:
            _emit(event_sink, controller_id, "thoth.auto.monitor", work_id=work_id, run_id=active_run_id)
            attach_output = attach_run(project_root, active_run_id, watch=True, timeout_seconds=5.0)
            _emit(event_sink, controller_id, "thoth.auto.monitor.tick", work_id=work_id, run_id=active_run_id, summary=attach_output)
            controller = store.read("controller", controller_id)
            continue

        strict_task = load_work_for_execution(project_root, work_id, require_ready=False)
        if strict_task.get("runnable") is not True:
            _emit(event_sink, controller_id, "thoth.auto.skipped", work_id=work_id, reason="non_runnable")
            payload["attempted_work_ids"] = _append_unique(payload.get("attempted_work_ids"), work_id)
            payload["skipped_work_ids"] = _append_unique(payload.get("skipped_work_ids"), work_id)
            controller = _update_controller(project_root, controller, status="running", payload_updates=payload)
            controller = store.read("controller", controller_id)
            continue
        handle, _packet = prepare_execution(
            project_root,
            command_id="loop",
            title=str(strict_task.get("title") or work_id),
            work_id=work_id,
            host=host,
            executor=executor,
            sleep_requested=False,
            strict_task=strict_task,
            goal=str(strict_task.get("goal_statement") or strict_task.get("title") or work_id),
        )
        rounds_attempted += 1
        cursor = {
            "index": rounds_attempted - 1,
            "active_run_id": handle.run_id,
            "completed_work_ids": completed_work_ids,
            "rounds_attempted": rounds_attempted,
        }
        controller = _update_controller(project_root, controller, status="running", payload_updates={"cursor": cursor})
        _emit(event_sink, controller_id, "thoth.auto.child.started", work_id=work_id, run_id=handle.run_id, round=rounds_attempted)
        child_status = execute_runtime_controller(project_root, handle.run_id, driver=driver_factory(handle), sink=event_sink)
        if child_status == 0:
            completed_work_ids.append(work_id)
            payload["completed_work_ids"] = _append_unique(payload.get("completed_work_ids"), work_id)
        else:
            payload["failed_work_ids"] = _append_unique(payload.get("failed_work_ids"), work_id)
            _emit(event_sink, controller_id, "thoth.auto.risk", work_id=work_id, run_id=handle.run_id, child_status=child_status)
        payload["attempted_work_ids"] = _append_unique(payload.get("attempted_work_ids"), work_id)
        child_handle = RunHandle(project_root=project_root, run_id=handle.run_id)
        _append_event(child_handle, f"auto controller {controller_id} observed child exit {child_status}", kind="auto")
        controller = store.read("controller", controller_id)
        if controller and _should_stop(controller):
            _emit(event_sink, controller_id, "thoth.auto.stopped", reason="stop_requested")
            _write_controller_supervisor(project_root, controller_id, pid=os.getpid(), state="stopped")
            return 130
        current_payload = controller.get("payload") if isinstance(controller.get("payload"), dict) else {}
        current_payload.update(payload)
        current_payload["cursor"] = {
            "index": rounds_attempted,
            "active_run_id": None,
            "completed_work_ids": current_payload.get("completed_work_ids", completed_work_ids),
            "rounds_attempted": rounds_attempted,
        }
        current_payload["elapsed_seconds"] = _controller_elapsed_seconds(current_payload, started_at)
        controller = _update_controller(project_root, controller, status="running", payload_updates=current_payload)


def watch_auto_controller(
    project_root: Path,
    controller_id: str,
    *,
    sink: RuntimeEventSink | None = None,
    follow: bool = False,
    poll_seconds: float | None = None,
) -> int:
    event_sink = sink or JsonlStdoutSink()
    interval = poll_seconds if isinstance(poll_seconds, (int, float)) and poll_seconds > 0 else 1.0
    heartbeat_interval = auto_heartbeat_interval_seconds()
    seen_child_runs: set[str] = set()
    last_snapshot_emit = 0.0
    last_status = ""
    while True:
        controller = Store(project_root).read("controller", controller_id)
        if not controller:
            event_sink.emit({"type": "thoth.auto.watch.failed", "ts": utc_now(), "controller_id": controller_id, "reason": "not_found"})
            return 1
        status = str(controller.get("status") or "")
        now = time()
        if not follow or status != last_status or now - last_snapshot_emit >= heartbeat_interval:
            event_sink.emit(_controller_snapshot(project_root, controller))
            last_snapshot_emit = now
            last_status = status
        payload = controller.get("payload") if isinstance(controller.get("payload"), dict) else {}
        cursor = payload.get("cursor") if isinstance(payload.get("cursor"), dict) else {}
        active_run_id = cursor.get("active_run_id")
        if isinstance(active_run_id, str) and active_run_id and active_run_id not in seen_child_runs:
            event_sink.emit({"type": "thoth.auto.child.event", "ts": utc_now(), "controller_id": controller_id, "run_id": active_run_id, "summary": attach_run(project_root, active_run_id, watch=False)})
            seen_child_runs.add(active_run_id)
        if status in AUTO_CONTROLLER_TERMINAL_STATUSES:
            event_sink.emit({"type": "thoth.auto.terminal", "ts": utc_now(), "controller_id": controller_id, "status": status})
            return 0 if status == "completed" else 2 if status == "paused" else 1
        if not follow:
            return 0
        sleep(interval)


def stdout_sink() -> JsonlStdoutSink:
    return JsonlStdoutSink()
