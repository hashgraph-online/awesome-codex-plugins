"""Supervisor identity helpers for durable runtime workers."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

from .io import _write_json
from .model import _process_alive, utc_now


def _proc_cmdline(pid: int) -> list[str]:
    path = Path("/proc") / str(pid) / "cmdline"
    try:
        raw = path.read_bytes()
    except OSError:
        return []
    return [part.decode("utf-8", errors="replace") for part in raw.split(b"\0") if part]


def _proc_start_ticks(pid: int) -> int | None:
    path = Path("/proc") / str(pid) / "stat"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    parts = text.rsplit(") ", 1)
    if len(parts) != 2:
        return None
    fields = parts[1].split()
    if len(fields) < 20:
        return None
    try:
        return int(fields[19])
    except ValueError:
        return None


def _command_hash(command: list[str]) -> str | None:
    if not command:
        return None
    encoded = json.dumps(command, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def supervisor_payload(
    *,
    project_root: Path,
    pid: int | None,
    state: str,
    runtime: str,
    run_id: str | None = None,
    controller_id: str | None = None,
    command: list[str] | None = None,
) -> dict[str, Any]:
    resolved_pid = int(pid or os.getpid())
    command_line = list(command or _proc_cmdline(resolved_pid) or [sys.executable, *sys.argv])
    payload: dict[str, Any] = {
        "pid": resolved_pid,
        "state": state,
        "runtime": runtime,
        "project_root": str(project_root.resolve()),
        "updated_at": utc_now(),
        "process_start_ticks": _proc_start_ticks(resolved_pid),
        "command_hash": _command_hash(command_line),
    }
    if run_id:
        payload["run_id"] = run_id
    if controller_id:
        payload["controller_id"] = controller_id
    return payload


def write_run_supervisor(handle, *, state: str, runtime: str, pid: int | None = None, command: list[str] | None = None) -> None:
    _write_json(
        handle.local_dir / "supervisor.json",
        supervisor_payload(
            project_root=handle.project_root,
            pid=pid,
            state=state,
            runtime=runtime,
            run_id=handle.run_id,
            command=command,
        ),
    )


def write_controller_supervisor(
    project_root: Path,
    controller_id: str,
    path: Path,
    *,
    state: str,
    runtime: str,
    pid: int | None = None,
    command: list[str] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(
        path,
        supervisor_payload(
            project_root=project_root,
            pid=pid,
            state=state,
            runtime=runtime,
            controller_id=controller_id,
            command=command,
        ),
    )


def supervisor_process_alive(
    supervisor: dict[str, Any],
    *,
    project_root: Path,
    runtime: str | None = None,
    run_id: str | None = None,
    controller_id: str | None = None,
) -> bool:
    pid = supervisor.get("pid")
    if not isinstance(pid, int) or not _process_alive(pid):
        return False
    if supervisor.get("project_root") != str(project_root.resolve()):
        return False
    if runtime and supervisor.get("runtime") != runtime:
        return False
    if run_id and supervisor.get("run_id") != run_id:
        return False
    if controller_id and supervisor.get("controller_id") != controller_id:
        return False
    start_ticks = supervisor.get("process_start_ticks")
    if isinstance(start_ticks, int):
        current_ticks = _proc_start_ticks(pid)
        if current_ticks is None or current_ticks != start_ticks:
            return False
    command_hash = supervisor.get("command_hash")
    if isinstance(command_hash, str) and command_hash:
        current_hash = _command_hash(_proc_cmdline(pid))
        if current_hash is not None and current_hash != command_hash:
            return False
    return True

