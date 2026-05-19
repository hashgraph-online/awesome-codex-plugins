"""Progress engine for work-item dashboard views."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

PHASE_WEIGHTS = {
    "survey": 0.20,
    "method_design": 0.20,
    "experiment": 0.40,
    "conclusion": 0.20,
}


def _phase_progress(phase: dict | None) -> float:
    if phase is None or not isinstance(phase, dict):
        return 0.0
    status = phase.get("status", "pending")
    if status in ("completed", "skipped"):
        return 100.0
    if status == "in_progress":
        criteria = phase.get("criteria")
        if criteria and isinstance(criteria, dict):
            threshold = criteria.get("threshold")
            current = criteria.get("current")
            if threshold is not None and threshold != 0 and current is not None:
                pct = (current / threshold) * 100.0
                return max(0.0, min(100.0, pct))
        return 50.0
    return 0.0


def _has_strict_shape(task: dict[str, Any]) -> bool:
    return "ready_state" in task or "work_id" in task


def _strict_task_progress(task: dict[str, Any]) -> float:
    work_result = task.get("work_result") if isinstance(task.get("work_result"), dict) else {}
    ready_state = str(task.get("ready_state") or "blocked")
    if work_result.get("updated_at"):
        return 100.0
    if ready_state == "validated":
        return 100.0
    if ready_state == "ready":
        return 15.0
    if ready_state == "blocked":
        return 5.0
    return 0.0


def calculate_task_progress(task: dict) -> float:
    if _has_strict_shape(task):
        return _strict_task_progress(task)
    phases = task.get("phases")
    if not phases or not isinstance(phases, dict):
        return 0.0
    total = 0.0
    for phase_name, weight in PHASE_WEIGHTS.items():
        phase_data = phases.get(phase_name)
        total += _phase_progress(phase_data) * weight
    return round(max(0.0, min(100.0, total)), 1)


def get_task_status(task: dict) -> str:
    if _has_strict_shape(task):
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

    phases = task.get("phases")
    if not phases or not isinstance(phases, dict):
        return "pending"
    all_phase_names = ("survey", "method_design", "experiment", "conclusion")
    statuses = []
    for pname in all_phase_names:
        p = phases.get(pname)
        if p and isinstance(p, dict):
            statuses.append(p.get("status", "pending"))
        else:
            statuses.append("pending")
    if all(s in ("completed", "skipped") for s in statuses):
        return "completed"
    if any(s in ("in_progress", "completed", "skipped") for s in statuses):
        return "in_progress"
    return "pending"


def calculate_module_progress(tasks_in_module: list[dict]) -> float:
    if not tasks_in_module:
        return 0.0
    total = sum(calculate_task_progress(t) for t in tasks_in_module)
    return round(total / len(tasks_in_module), 1)


def calculate_direction_progress(modules_data: list[dict[str, Any]]) -> float:
    if not modules_data:
        return 0.0
    progresses = []
    for mod in modules_data:
        tasks = mod.get("tasks", [])
        progresses.append(calculate_module_progress(tasks))
    return round(sum(progresses) / len(progresses), 1) if progresses else 0.0


def calculate_global_progress(all_tasks: list[dict]) -> float:
    if not all_tasks:
        return 0.0
    total = sum(calculate_task_progress(t) for t in all_tasks)
    return round(total / len(all_tasks), 1)


def find_blocked_tasks(all_tasks: list[dict]) -> list[dict]:
    blocked: list[dict] = []
    seen_ids: set[str] = set()
    completed_ids = {task.get("id") or task.get("work_id") for task in all_tasks if get_task_status(task) == "completed"}
    for task in all_tasks:
        tid = str(task.get("id") or task.get("work_id") or "")
        if not tid or tid in seen_ids:
            continue
        if _has_strict_shape(task):
            if get_task_status(task) in {"blocked", "invalid"}:
                blocked.append(task)
                seen_ids.add(tid)
            continue
        deps = task.get("depends_on", [])
        if not deps:
            continue
        for dep in deps:
            if dep.get("type") == "hard" and dep.get("work_id") not in completed_ids:
                blocked.append(task)
                seen_ids.add(tid)
                break
    return blocked


def find_blocked_work_items(all_tasks: list[dict]) -> list[dict]:
    return find_blocked_tasks(all_tasks)


def estimate_completion(all_tasks: list[dict]) -> Optional[dict]:
    if not all_tasks:
        return None
    earliest: Optional[datetime] = None
    completed_count = 0
    total_count = len(all_tasks)
    for task in all_tasks:
        created = task.get("created_at") or task.get("generated_at")
        if created:
            try:
                if isinstance(created, str):
                    created = created.replace(" ", "T")
                    if "+" not in created and "Z" not in created:
                        created += "+00:00"
                    dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                else:
                    dt = created
                if earliest is None or dt < earliest:
                    earliest = dt
            except (ValueError, TypeError):
                pass
        if get_task_status(task) == "completed":
            completed_count += 1
    if earliest is None or completed_count == 0:
        return {
            "total_work_items": total_count,
            "completed_work_items": completed_count,
            "elapsed_days": 0,
            "estimated_days_remaining": None,
            "message": "Insufficient data for estimation",
        }
    now = datetime.now(timezone.utc)
    elapsed = (now - earliest).total_seconds() / 86400.0
    if elapsed < 0.01:
        elapsed = 0.01
    rate = completed_count / elapsed
    remaining = total_count - completed_count
    est_days = remaining / rate if rate > 0 else None
    return {
        "total_work_items": total_count,
        "completed_work_items": completed_count,
        "elapsed_days": round(elapsed, 1),
        "rate_per_day": round(rate, 2),
        "estimated_days_remaining": round(est_days, 1) if est_days else None,
    }


def status_counts(tasks: list[dict]) -> dict[str, int]:
    counts = {
        "total": 0,
        "pending": 0,
        "in_progress": 0,
        "completed": 0,
        "blocked": 0,
        "ready": 0,
        "invalid": 0,
        "failed": 0,
    }
    blocked_ids = {task.get("id") or task.get("work_id") for task in find_blocked_tasks(tasks)}
    for task in tasks:
        counts["total"] += 1
        tid = task.get("id") or task.get("work_id")
        if tid in blocked_ids and not _has_strict_shape(task):
            counts["blocked"] += 1
            continue
        status = get_task_status(task)
        counts[status] = counts.get(status, 0) + 1
    return counts
