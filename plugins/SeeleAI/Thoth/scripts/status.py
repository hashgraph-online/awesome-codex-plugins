#!/usr/bin/env python3
"""Compatibility-free thin wrapper over the canonical status module."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from thoth.observe.status import (
    is_task_completed,
    progress_bar,
    quick_health as _quick_health,
    render_status as _render_status,
)


def task_current_phase(task: dict[str, Any]) -> tuple[str, str]:
    work_result = task.get("work_result") if isinstance(task.get("work_result"), dict) else {}
    if work_result.get("updated_at"):
        source = str(work_result.get("source") or "recorded")
        return "work_result", f"work_result:{source}"
    return "runtime", str(task.get("ready_state") or "blocked")


def is_task_blocked(task: dict[str, Any], all_tasks: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    if task.get("ready_state") in {"blocked", "invalid"}:
        deps = task.get("depends_on")
        if isinstance(deps, list):
            return True, [str(dep.get("work_id")) for dep in deps if isinstance(dep, dict) and dep.get("type") == "hard"]
        return True, []
    completed_ids = {str(row.get("work_id") or row.get("id")) for row in all_tasks if is_task_completed(row)}
    blockers: list[str] = []
    for dep in task.get("depends_on", []):
        if isinstance(dep, dict) and dep.get("type") == "hard" and dep.get("work_id") not in completed_ids:
            blockers.append(str(dep["work_id"]))
    return bool(blockers), blockers


def quick_health() -> tuple[bool, str]:
    return _quick_health(Path.cwd())


def render_status(*, full: bool = False) -> str:
    return _render_status(Path.cwd(), full=full)


def main() -> int:
    from thoth.observe.status import main as canonical_main

    return canonical_main()


if __name__ == "__main__":
    raise SystemExit(main())
