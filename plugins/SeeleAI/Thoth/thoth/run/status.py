"""Canonical runtime status read payload."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from thoth.plan.compiler import compile_task_authority

from .io import local_registry_root
from .model import LIVE_DISPATCH_MODE, SLEEP_DISPATCH_MODE, default_executor
from .service import list_active_runs

def build_status_payload(project_root: Path) -> dict[str, Any]:
    active_runs = list_active_runs(project_root)
    return {
        "project_root": str(project_root.resolve()),
        "active_run_count": len(active_runs),
        "active_runs": active_runs,
        "local_registry": str(local_registry_root(project_root)),
        "compiler": compile_task_authority(project_root).get("summary", {}),
        "runtime_defaults": {
            "default_executor": default_executor(),
            "live_dispatch_mode": LIVE_DISPATCH_MODE,
            "sleep_dispatch_mode": SLEEP_DISPATCH_MODE,
        },
    }
