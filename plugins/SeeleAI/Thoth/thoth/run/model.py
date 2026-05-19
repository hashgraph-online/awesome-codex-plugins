"""Runtime constants and lightweight model objects."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ACTIVE_STATUSES = {"queued", "running", "paused", "waiting_input", "stopping"}
TERMINAL_STATUSES = {"completed", "failed", "stopped"}
LIVE_DISPATCH_MODE = "live_native"
SLEEP_DISPATCH_MODE = "external_worker"
PROTOCOL_VERSION = 1
WORKER_HEARTBEAT_INTERVAL_SECONDS = 15.0
WORKER_RETRY_LIMIT = 2
WORKER_RETRY_WINDOW_SECONDS = 90.0
DEFAULT_EXTERNAL_WORKER_TIMEOUT_SECONDS = 15 * 60
CLAUDE_EXTERNAL_WORKER_ALLOWED_TOOLS = "Read,Glob,Grep,Bash,Edit,Write,Task,Monitor"

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_iso8601(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _age_seconds(iso_utc: Any) -> float | None:
    dt = _parse_iso8601(iso_utc)
    if dt is None:
        return None
    return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds())


def default_executor() -> str:
    return "claude"


def dispatch_mode_for(sleep_requested: bool) -> str:
    return SLEEP_DISPATCH_MODE if sleep_requested else LIVE_DISPATCH_MODE


@dataclass
class RunHandle:
    project_root: Path
    run_id: str

    @property
    def run_dir(self) -> Path:
        return self.project_root / ".thoth" / "runs" / self.run_id

    @property
    def local_dir(self) -> Path:
        from .io import local_registry_root

        return local_registry_root(self.project_root) / "runs" / self.run_id

    def run_json(self) -> dict[str, Any]:
        from .io import _read_json

        return _read_json(self.run_dir / "run.json")

    def state_json(self) -> dict[str, Any]:
        from .io import _read_json

        return _read_json(self.run_dir / "state.json")

    def result_json(self) -> dict[str, Any]:
        from .io import _read_json

        return _read_json(self.run_dir / "result.json")


def _process_alive(pid: int | None) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True
