"""Pure read model shared by status, report, and dashboard-facing views."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from thoth.plan.store import (
    load_work_items,
    load_compiler_state,
    load_project_manifest,
    load_work_result,
)
from thoth.run.auto import list_auto_controller_statuses
from thoth.run.service import list_active_runs


def load_config(project_root: Path) -> dict[str, Any]:
    manifest = load_project_manifest(project_root)
    return {"project": manifest.get("project", {}), "dashboard": manifest.get("dashboard", {})}


def load_tasks(project_root: Path) -> list[dict[str, Any]]:
    tasks = []
    for work in load_work_items(project_root):
        item = dict(work)
        work_id = item.get("work_id")
        if isinstance(work_id, str) and work_id:
            work_result = load_work_result(project_root, work_id)
            if work_result:
                item["work_result"] = work_result
        tasks.append(item)
    return tasks


def load_milestones(project_root: Path) -> list[dict[str, Any]]:
    path = project_root / ".agent-os" / "milestones.yaml"
    if not path.exists():
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return []
    return data.get("milestones", []) if isinstance(data, dict) else []


def load_run_log(project_root: Path) -> str:
    path = project_root / ".agent-os" / "run-log.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def load_run_log_recent(project_root: Path, n: int = 5) -> list[str]:
    content = load_run_log(project_root)
    entries = re.findall(r"^- (\d{4}-\d{2}-\d{2} \d{2}:\d{2}.*?)(?=\n- \d{4}-|\Z)", content, re.MULTILINE | re.DOTALL)
    return entries[-n:] if entries else []


def load_todo_next(project_root: Path) -> list[tuple[str, str, str]]:
    todo_path = project_root / ".agent-os" / "todo.md"
    if not todo_path.exists():
        return []
    content = todo_path.read_text(encoding="utf-8")
    return re.findall(r"^- `([^`]+)` `\[([^\]]+)\]`:\s*(.+)$", content, re.MULTILINE)[:5]


def is_task_completed(task: dict[str, Any]) -> bool:
    work_result = task.get("work_result") if isinstance(task.get("work_result"), dict) else {}
    return bool(work_result.get("updated_at"))


def task_completed_in_range(task: dict[str, Any], from_date: datetime, to_date: datetime) -> bool:
    work_result = task.get("work_result") if isinstance(task.get("work_result"), dict) else {}
    updated_at = work_result.get("updated_at")
    if not isinstance(updated_at, str) or not updated_at:
        return False
    try:
        dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    return from_date <= dt <= to_date


def active_runs(project_root: Path) -> list[dict[str, Any]]:
    return list_active_runs(project_root)


def active_auto_controllers(project_root: Path) -> list[dict[str, Any]]:
    return [
        row
        for row in list_auto_controller_statuses(project_root)
        if str(row.get("status") or "") in {"queued", "running", "idle"}
    ]


def completed_tasks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [task for task in tasks if is_task_completed(task)]


def blocking_tasks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [task for task in tasks if task.get("ready_state") in {"blocked", "invalid"}]


def quick_health(project_root: Path) -> tuple[bool, str]:
    manifest = project_root / ".thoth" / "objects" / "project" / "project.json"
    compiler = project_root / ".thoth" / "docs" / "object-graph-summary.json"
    if not manifest.exists() or not compiler.exists():
        return False, "Missing canonical Thoth object authority files"
    entries = load_run_log_recent(project_root, 1)
    if entries:
        match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2})", entries[-1])
        if match:
            return True, f"Last run-log update: {time_ago(match.group(1))}"
    return True, "Strict authority present"


def time_ago(iso_str: str | None) -> str:
    if not iso_str:
        return "unknown"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    except ValueError:
        return "unknown"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - dt
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return f"{seconds}s ago"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}min ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    return f"{hours // 24}d ago"


def parse_iso_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def task_updated_at(task: dict[str, Any]) -> str | None:
    work_result = task.get("work_result") if isinstance(task.get("work_result"), dict) else {}
    for key in ("updated_at", "last_closure_at", "last_attempt_at"):
        value = work_result.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def task_created_at(task: dict[str, Any]) -> str | None:
    for key in ("created_at", "generated_at"):
        value = task.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def task_runtime_status(task: dict[str, Any]) -> str:
    work_result = task.get("work_result") if isinstance(task.get("work_result"), dict) else {}
    if work_result.get("updated_at"):
        if work_result.get("usable") is True and work_result.get("meets_goal") is True:
            return "completed"
        return "failed"
    ready_state = str(task.get("ready_state") or "blocked")
    if ready_state == "ready":
        return "ready"
    if ready_state == "validated":
        return "completed"
    if ready_state == "invalid":
        return "invalid"
    return "blocked"


def task_progress_pct(task: dict[str, Any]) -> float:
    work_result = task.get("work_result") if isinstance(task.get("work_result"), dict) else {}
    if work_result.get("updated_at"):
        return 100.0
    ready_state = str(task.get("ready_state") or "blocked")
    if ready_state == "validated":
        return 100.0
    if ready_state == "ready":
        return 15.0
    if ready_state == "blocked":
        return 5.0
    return 0.0


def recent_work_result_summaries(tasks: list[dict[str, Any]], *, limit: int = 5) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task in tasks:
        work_result = task.get("work_result") if isinstance(task.get("work_result"), dict) else {}
        updated_at = task_updated_at(task)
        conclusion = (
            work_result.get("conclusion")
            or work_result.get("current_summary")
        )
        evidence_paths = work_result.get("evidence_paths")
        if not isinstance(evidence_paths, list):
            evidence_paths = []
        if not updated_at and not conclusion and not evidence_paths:
            continue
        rows.append(
            {
                "work_id": task.get("work_id") or task.get("id"),
                "title": task.get("title", ""),
                "module": task.get("module", ""),
                "direction": task.get("direction", ""),
                "status": task_runtime_status(task),
                "updated_at": updated_at,
                "source": work_result.get("source") or "work_result",
                "conclusion": conclusion,
                "evidence_paths": evidence_paths,
            }
        )
    rows.sort(
        key=lambda item: parse_iso_timestamp(item.get("updated_at")) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return rows[:limit]


def derive_gantt_rows(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task in tasks:
        phases = task.get("phases") if isinstance(task.get("phases"), dict) else {}
        timestamps: list[str] = []
        completed_timestamps: list[str] = []
        for phase in phases.values():
            if not isinstance(phase, dict):
                continue
            for key in ("started_at", "completed_at"):
                value = phase.get(key)
                if isinstance(value, str) and value:
                    timestamps.append(value)
                    if key == "completed_at":
                        completed_timestamps.append(value)

        start_date = None
        for candidate in sorted(timestamps, key=lambda value: parse_iso_timestamp(value) or datetime.max.replace(tzinfo=timezone.utc)):
            start_date = candidate
            break
        if start_date is None:
            start_date = task_created_at(task)

        end_date = None
        if completed_timestamps:
            end_date = max(
                completed_timestamps,
                key=lambda value: parse_iso_timestamp(value) or datetime.min.replace(tzinfo=timezone.utc),
            )
        elif task_runtime_status(task) in {"completed", "failed"}:
            end_date = task_updated_at(task)

        estimated_hours = task.get("estimated_total_hours")
        if not isinstance(estimated_hours, (int, float)):
            estimated_hours = 0

        dependency_rows = task.get("depends_on")
        dependencies: list[str] = []
        if isinstance(dependency_rows, list):
            for dep in dependency_rows:
                if isinstance(dep, dict):
                    work_id = dep.get("work_id")
                    if isinstance(work_id, str) and work_id:
                        dependencies.append(work_id)

        rows.append(
            {
                "id": task.get("work_id") or task.get("id"),
                "title": task.get("title", ""),
                "module": task.get("module", ""),
                "direction": task.get("direction", ""),
                "status": task_runtime_status(task),
                "start_date": start_date,
                "end_date": end_date,
                "estimated_hours": estimated_hours,
                "progress": task_progress_pct(task),
                "dependencies": dependencies,
            }
        )
    return rows


def overview_summary_read_model(project_root: Path) -> dict[str, Any]:
    work_items = load_tasks(project_root)
    config = load_config(project_root)
    compiler_state = load_compiler_state(project_root)
    healthy, health_message = quick_health(project_root)
    ready_count = sum(1 for item in work_items if str(item.get("ready_state") or "") == "ready")
    total_count = len(work_items)
    completed_count = len(completed_tasks(work_items))
    blocked_count = len(blocking_tasks(work_items))
    overall_progress = round((100 * completed_count / total_count), 1) if total_count else 0.0
    compiler_summary = compiler_state.get("summary", {}) if isinstance(compiler_state, dict) else {}
    decision_counts = compiler_summary.get("decision_counts", {}) if isinstance(compiler_summary.get("decision_counts"), dict) else {}
    return {
        "project": config.get("project", {}),
        "headline": {
            "total_work_items": total_count,
            "completed_work_items": completed_count,
            "blocked_work_items": blocked_count,
            "ready_work_items": ready_count,
            "overall_progress": overall_progress,
            "decision_queue_count": decision_counts.get("proposed", 0),
        },
        "compiler_summary": compiler_summary,
        "recent_conclusions": recent_work_result_summaries(work_items, limit=6),
        "recent_activity": load_run_log_recent(project_root, 6),
        "todo_next": [
            {"id": item_id, "status": item_status, "description": description}
            for item_id, item_status, description in load_todo_next(project_root)
        ],
        "healthy": healthy,
        "health_message": health_message,
        "active_run_count": len(active_runs(project_root)),
        "active_auto_count": len(active_auto_controllers(project_root)),
    }


def status_read_model(project_root: Path) -> dict[str, Any]:
    work_items = load_tasks(project_root)
    healthy, health_msg = quick_health(project_root)
    return {
        "project_root": str(project_root.resolve()),
        "config": load_config(project_root),
        "work_items": work_items,
        "work_item_count": len(work_items),
        "active_runs": active_runs(project_root),
        "active_auto_controllers": active_auto_controllers(project_root),
        "completed_work_item_count": len(completed_tasks(work_items)),
        "blocked_work_item_count": len(blocking_tasks(work_items)),
        "healthy": healthy,
        "health_message": health_msg,
        "todo_next": load_todo_next(project_root),
        "recent_run_log": load_run_log_recent(project_root),
    }
