"""Canonical status renderer backed by the observe read model."""

from __future__ import annotations

from pathlib import Path

from thoth.observe.read_model import (
    blocking_tasks,
    completed_tasks,
    is_task_completed,
    load_config,
    load_tasks,
    quick_health,
    status_read_model,
    time_ago,
)


def progress_bar(pct: int, width: int = 10) -> str:
    filled = int(round(pct * width / 100))
    filled = max(0, min(width, filled))
    return "[" + "■" * filled + "□" * (width - filled) + "]"


def status_snapshot(project_root: Path) -> dict:
    payload = status_read_model(project_root)
    payload.pop("tasks", None)
    return payload


def render_status(project_root: Path, *, full: bool = False) -> str:
    config = load_config(project_root)
    project_name = config.get("project", {}).get("name", "Unknown Project")
    tasks = load_tasks(project_root)
    lines: list[str] = []
    lines.append(f"═══ Thoth Status: {project_name} ═══")
    lines.append("")

    if not tasks:
        lines.append("  No ready work items found.")
        lines.append("")
        healthy, health_msg = quick_health(project_root)
        lines.append(f"▸ Health: {'●' if healthy else '○'} {'ALL CHECKS PASSED' if healthy else 'ISSUES DETECTED'} | {health_msg}")
        return "\n".join(lines)

    active_runs = status_read_model(project_root)["active_runs"]
    active_auto = status_read_model(project_root).get("active_auto_controllers", [])
    lines.append("▸ Running:")
    if active_runs:
        for run in active_runs:
            lines.append(f"  {progress_bar(int(run.get('progress_pct', 0) or 0))} {int(run.get('progress_pct', 0) or 0):>3}%  {run.get('run_id')} {run.get('kind')} ({run.get('phase')})")
    else:
        lines.append("  (none)")
    if active_auto:
        lines.append("")
        lines.append("▸ Auto:")
        for controller in active_auto[:5]:
            lines.append(
                "  {controller_id} {state} elapsed={elapsed}s queue={queue} active={active}".format(
                    controller_id=controller.get("controller_id"),
                    state=controller.get("state") or controller.get("status"),
                    elapsed=controller.get("elapsed_seconds") or 0,
                    queue=controller.get("queue_count") or 0,
                    active=controller.get("active_run_id") or "none",
                )
            )
    lines.append("")

    completed = completed_tasks(tasks)
    lines.append("▸ Recent:")
    if completed:
        for task in completed[-3:]:
            work_result = task.get("work_result", {})
            lines.append(f"  ✓ {task.get('work_id')} {task.get('title', '')} -- {work_result.get('source', 'recorded')} {time_ago(work_result.get('updated_at'))}")
    else:
        lines.append("  (none)")
    lines.append("")

    blocked = blocking_tasks(tasks)
    lines.append("▸ Next:")
    if blocked:
        for task in blocked[:5]:
            lines.append(f"  - {task.get('work_id')} {task.get('blocking_reason') or task.get('ready_state')}")
    else:
        lines.append("  - No blocked work items.")
    lines.append("")

    healthy, health_msg = quick_health(project_root)
    lines.append(f"▸ Health: {'●' if healthy else '○'} {'ALL CHECKS PASSED' if healthy else 'ISSUES DETECTED'} | {health_msg}")

    if full:
        lines.append("")
        lines.append("▸ Todo:")
        todo_entries = status_read_model(project_root)["todo_next"]
        if todo_entries:
            for entry_id, entry_status, description in todo_entries:
                lines.append(f"  - {entry_id} [{entry_status}] {description}")
        else:
            lines.append("  (none)")
    return "\n".join(lines)


def main() -> int:
    import sys
    project_root = Path.cwd()
    if not (project_root / ".thoth" / "objects" / "project" / "project.json").exists():
        print("Not a Thoth project. Run /thoth:init to set up.")
        return 1
    print(render_status(project_root, full="--full" in sys.argv))
    return 0
