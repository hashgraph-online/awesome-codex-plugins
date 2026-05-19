"""Runtime repository lease helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .io import _read_json, _write_json, local_registry_root
from .model import ACTIVE_STATUSES, _age_seconds, utc_now
from .supervisor import supervisor_process_alive

def _supervisor_payload(project_root: Path, run_id: str) -> dict[str, Any]:
    local_dir = local_registry_root(project_root) / "runs" / run_id
    return _read_json(local_dir / "supervisor.json")


def _lease_stale_after_seconds() -> int:
    raw = os.environ.get("THOTH_LEASE_STALE_SECONDS", "120")
    try:
        return max(30, int(raw))
    except ValueError:
        return 120


def _lease_holder_is_stale(project_root: Path, lease_payload: dict[str, Any]) -> bool:
    if not lease_payload or lease_payload.get("status") not in ACTIVE_STATUSES:
        return False
    run_id = lease_payload.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        return True
    run_dir = project_root / ".thoth" / "runs" / run_id
    state = _read_json(run_dir / "state.json")
    heartbeat_age = _age_seconds(state.get("last_heartbeat_at"))
    supervisor = _supervisor_payload(project_root, run_id)
    supervisor_alive = supervisor_process_alive(
        supervisor,
        project_root=project_root,
        run_id=run_id,
    )
    if supervisor_alive:
        return False
    if heartbeat_age is None:
        return True
    return heartbeat_age >= _lease_stale_after_seconds()


def acquire_repo_lease(project_root: Path, run_id: str, host: str, executor: str, *, dispatch_mode: str | None = None) -> Path:
    lease_path = local_registry_root(project_root) / "lease.json"
    current = _read_json(lease_path)
    if current and current.get("run_id") != run_id and current.get("status") in ACTIVE_STATUSES:
        if _lease_holder_is_stale(project_root, current):
            current["status"] = "released"
            current["released_reason"] = "stale_runtime"
            current["updated_at"] = utc_now()
            _write_json(lease_path, current)
        else:
            raise RuntimeError(f"Active lease already held by {current.get('run_id')}")
    payload = {
        "run_id": run_id,
        "host": host,
        "executor": executor,
        "dispatch_mode": dispatch_mode,
        "status": "running",
        "updated_at": utc_now(),
        "project_root": str(project_root.resolve()),
    }
    _write_json(lease_path, payload)
    return lease_path


def release_repo_lease(project_root: Path, run_id: str) -> None:
    lease_path = local_registry_root(project_root) / "lease.json"
    current = _read_json(lease_path)
    if current.get("run_id") == run_id:
        current["status"] = "released"
        current["updated_at"] = utc_now()
        _write_json(lease_path, current)
