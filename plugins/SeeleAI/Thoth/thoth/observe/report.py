"""Canonical progress report generator backed by the observe read model."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from thoth.observe.read_model import (
    blocking_tasks,
    completed_tasks,
    is_task_completed,
    load_config,
    load_run_log,
    load_tasks,
    task_completed_in_range,
)


def parse_run_log_entries(content: str, from_date: datetime, to_date: datetime) -> list[str]:
    entries: list[str] = []
    current: list[str] = []
    current_dt: datetime | None = None
    for line in content.splitlines():
        if line.startswith("- "):
            if current and current_dt is not None and from_date <= current_dt <= to_date:
                entries.append("\n".join(current))
            current = [line]
            current_dt = None
            header = line[2:18]
            try:
                current_dt = datetime.strptime(header, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except ValueError:
                current_dt = None
            continue
        if current:
            current.append(line)
    if current and current_dt is not None and from_date <= current_dt <= to_date:
        entries.append("\n".join(current))
    return entries


def generate_report(project_root: Path, from_date: datetime, to_date: datetime, output_path: Path) -> Path:
    config = load_config(project_root)
    project_name = config.get("project", {}).get("name", "Unknown Project")
    tasks = load_tasks(project_root)
    run_log_entries = parse_run_log_entries(load_run_log(project_root), from_date, to_date)

    completed_in_range = [task for task in tasks if task_completed_in_range(task, from_date, to_date)]
    in_progress = [task for task in tasks if task.get("ready_state") == "ready"]
    blocked = blocking_tasks(tasks)
    total_completed = len(completed_tasks(tasks))
    total = len(tasks)
    overall_pct = int(round((100 * total_completed / total), 0)) if total else 0

    lines: list[str] = []
    lines.append(f"# Progress Report: {from_date.strftime('%Y-%m-%d')} -- {to_date.strftime('%Y-%m-%d')}")
    lines.append("")
    lines.append(f"**Project:** {project_name}")
    lines.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Work items completed in period: {len(completed_in_range)}")
    lines.append(f"- Work items in progress: {len(in_progress)}")
    lines.append(f"- Work items blocked or invalid: {len(blocked)}")
    lines.append(f"- Overall progress: {overall_pct}% ({total_completed}/{total})")
    lines.append("")
    lines.append("## Completed")
    lines.append("")
    if completed_in_range:
        for task in completed_in_range:
            work_result = task.get("work_result", {})
            lines.append(f"### [{task.get('work_id')}] {task.get('title', '')}")
            lines.append(f"- Status: {task.get('ready_state')}")
            lines.append(f"- Result source: {work_result.get('source', 'unknown')}")
            lines.append(f"- Conclusion: {work_result.get('conclusion') or 'No conclusion text'}")
            for evidence in work_result.get("evidence_paths", []):
                lines.append(f"- Evidence: [{evidence}]({evidence})")
    else:
        lines.append("No work items completed in the selected range.")
    lines.append("")
    lines.append("## In Progress")
    lines.append("")
    if in_progress:
        for task in in_progress:
            lines.append(f"- `{task.get('work_id')}` {task.get('title', '')}")
    else:
        lines.append("No ready work items at the moment.")
    lines.append("")
    lines.append("## Blockers & Risks")
    lines.append("")
    if blocked:
        for task in blocked:
            lines.append(f"- `{task.get('work_id')}` {task.get('blocking_reason') or task.get('ready_state')}")
    else:
        lines.append("No blocked work items.")
    lines.append("")
    lines.append("## Run Log Highlights")
    lines.append("")
    lines.extend(run_log_entries[:10] if run_log_entries else ["No run-log entries in the selected range."])
    lines.append("")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def generate_default_report(project_root: Path, date_from: str, date_to: str, *, fmt: str = "md") -> Path:
    from_date = datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc)
    to_date = datetime.fromisoformat(date_to).replace(tzinfo=timezone.utc)
    suffix = ".json.md" if fmt == "json" else ".md"
    output_path = project_root / "reports" / f"{date_to}-report{suffix}"
    return generate_report(project_root, from_date, to_date, output_path)


def render_report_summary(path: Path) -> str:
    return f"Report written to {path}"


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Thoth report generator")
    parser.add_argument("--from", dest="date_from", required=True)
    parser.add_argument("--to", dest="date_to", required=True)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    project_root = Path.cwd()
    if not load_config(project_root).get("project"):
        print("Not a Thoth project. Run /thoth:init to set up.")
        return 1
    output_path = Path(args.output) if args.output else (project_root / "reports" / f"{args.date_to}-report.md")
    generate_report(project_root, datetime.fromisoformat(args.date_from).replace(tzinfo=timezone.utc), datetime.fromisoformat(args.date_to).replace(tzinfo=timezone.utc), output_path)
    print(render_report_summary(output_path))
    return 0
