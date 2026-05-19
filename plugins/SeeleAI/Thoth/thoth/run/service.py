"""User-facing runtime service operations."""

from __future__ import annotations

import json
import os
import signal
import time
from pathlib import Path
from typing import Any

from .io import _read_json
from .lease import acquire_repo_lease, release_repo_lease
from .ledger import _append_event, _update_run, _update_state, _write_heartbeat, _write_stopped_result
from .model import ACTIVE_STATUSES, LIVE_DISPATCH_MODE, SLEEP_DISPATCH_MODE, TERMINAL_STATUSES, RunHandle
from .supervisor import supervisor_process_alive

def stop_run(project_root: Path, run_id: str) -> None:
    handle = RunHandle(project_root=project_root.resolve(), run_id=run_id)
    run_payload = handle.run_json()
    _append_event(handle, "stop requested")
    dispatch_mode = run_payload.get("dispatch_mode")
    terminalize_immediately = dispatch_mode in {LIVE_DISPATCH_MODE, SLEEP_DISPATCH_MODE}
    _update_state(handle, status="stopping", phase="stopping", supervisor_state="stopping")
    supervisor = _read_json(handle.local_dir / "supervisor.json")
    pid = supervisor.get("pid")
    if isinstance(pid, int) and supervisor_process_alive(supervisor, project_root=project_root, run_id=run_id):
        if terminalize_immediately:
            _update_state(handle, status="stopped", phase="stopped", progress_pct=100, supervisor_state="stopped")
            _write_stopped_result(handle)
            _update_run(handle, attachable=False)
            release_repo_lease(project_root, run_id)
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        return
    if handle.state_json().get("status") in TERMINAL_STATUSES:
        release_repo_lease(project_root, run_id)
        return
    if terminalize_immediately:
        _update_state(handle, status="stopped", phase="stopped", progress_pct=100, supervisor_state="stopped")
        _write_stopped_result(handle)
        _update_run(handle, attachable=False)
        release_repo_lease(project_root, run_id)


def resume_run(project_root: Path, run_id: str) -> RunHandle:
    handle = RunHandle(project_root=project_root.resolve(), run_id=run_id)
    run_payload = handle.run_json()
    if not run_payload:
        raise FileNotFoundError(f"Run {run_id} not found")
    state = handle.state_json()
    if state.get("status") in ACTIVE_STATUSES and run_payload.get("dispatch_mode") == LIVE_DISPATCH_MODE:
        return handle

    acquire_repo_lease(
        project_root,
        run_id,
        str(run_payload.get("host") or "unknown"),
        str(run_payload.get("executor") or "unknown"),
        dispatch_mode=str(run_payload.get("dispatch_mode") or LIVE_DISPATCH_MODE),
    )
    _append_event(handle, "resume requested")
    _update_state(handle, status="running", phase="prepared", supervisor_state="resumed", progress_pct=max(1, int(state.get("progress_pct", 0))))
    _write_heartbeat(handle)
    return handle


def attach_run(project_root: Path, run_id: str, *, watch: bool = False, timeout_seconds: float = 5.0) -> str:
    handle = RunHandle(project_root=project_root.resolve(), run_id=run_id)
    deadline = time.time() + timeout_seconds
    last_seen = 0
    lines: list[str] = []
    while True:
        events_path = handle.run_dir / "events.jsonl"
        if events_path.exists():
            for raw in events_path.read_text(encoding="utf-8").splitlines():
                if not raw.strip():
                    continue
                payload = json.loads(raw)
                seq = int(payload.get("seq", 0))
                if seq <= last_seen:
                    continue
                last_seen = seq
                lines.append(f"[{payload.get('ts')}] {payload.get('message')}")
        state = handle.state_json()
        run = handle.run_json()
        if not watch or state.get("status") not in ACTIVE_STATUSES or time.time() >= deadline:
            lines.append(
                "status={status} phase={phase} progress={progress} dispatch={dispatch}".format(
                    status=state.get("status"),
                    phase=state.get("phase"),
                    progress=state.get("progress_pct"),
                    dispatch=run.get("dispatch_mode"),
                )
            )
            return "\n".join(lines).strip()
        time.sleep(0.2)


def list_active_runs(project_root: Path) -> list[dict[str, Any]]:
    runs_dir = project_root / ".thoth" / "runs"
    rows: list[dict[str, Any]] = []
    if not runs_dir.is_dir():
        return rows
    for run_dir in sorted(runs_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        run = _read_json(run_dir / "run.json")
        state = _read_json(run_dir / "state.json")
        if state.get("status") in ACTIVE_STATUSES:
            rows.append(
                {
                    "run_id": run.get("run_id", run_dir.name),
                    "kind": run.get("kind"),
                    "parent_run_id": run.get("parent_run_id"),
                    "iteration_index": run.get("iteration_index"),
                    "host": run.get("host"),
                    "executor": run.get("executor"),
                    "dispatch_mode": run.get("dispatch_mode"),
                    "attachable": bool(run.get("attachable", True)),
                    "status": state.get("status"),
                    "phase": state.get("phase"),
                    "progress_pct": state.get("progress_pct"),
                    "last_heartbeat_at": state.get("last_heartbeat_at"),
                }
            )
    return rows
