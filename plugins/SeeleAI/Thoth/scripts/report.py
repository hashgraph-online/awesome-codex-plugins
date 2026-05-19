#!/usr/bin/env python3
"""Compatibility-free thin wrapper over the canonical report module."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from thoth.observe.report import (
    generate_report as _generate_report,
    is_task_completed,
    parse_run_log_entries,
    task_completed_in_range,
)


def task_created_in_range(task: dict[str, Any], from_date: datetime, to_date: datetime) -> bool:
    created_at = task.get("generated_at") or task.get("created_at")
    if not isinstance(created_at, str) or not created_at:
        return False
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    return from_date <= dt <= to_date


def task_current_phase(task: dict[str, Any]) -> tuple[str, str]:
    work_result = task.get("work_result") if isinstance(task.get("work_result"), dict) else {}
    if work_result.get("updated_at"):
        return "work_result", str(work_result.get("source") or "recorded")
    return "runtime", str(task.get("ready_state") or "blocked")


def generate_report(from_date: datetime, to_date: datetime, output_path: Path) -> None:
    _generate_report(Path.cwd(), from_date, to_date, output_path)


def main() -> int:
    from thoth.observe.report import main as canonical_main

    return canonical_main()


if __name__ == "__main__":
    raise SystemExit(main())
