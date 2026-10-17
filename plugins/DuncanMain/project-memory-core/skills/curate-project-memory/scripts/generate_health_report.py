#!/usr/bin/env python3
"""Generate a portable Markdown Project Memory health report."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render(report: dict[str, object], project_id: str, generated_at: str) -> str:
    summary = report.get("summary", {})
    findings = report.get("findings", [])
    lines = [
        "---",
        "type: health-report",
        f'project_id: "{project_id}"',
        f'generated_at: "{generated_at}"',
        f"files_checked: {report.get('files_checked', 0)}",
        f"errors: {summary.get('errors', 0)}",
        f"warnings: {summary.get('warnings', 0)}",
        "---",
        "",
        "# Health Report",
        "",
        "This report contains deterministic structural signals. Inspect affected notes before changing durable knowledge.",
        "",
        "| Severity | Code | File | Finding |",
        "|---|---|---|---|",
    ]
    for item in findings:
        lines.append(f"| {escape(item.get('severity', ''))} | {escape(item.get('code', ''))} | {escape(item.get('file', ''))} | {escape(item.get('message', ''))} |")
    if not findings:
        lines.append("| information | healthy | . | No structural findings. |")
    lines.extend(["", "Generated locally. No vault content was uploaded.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_folder", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--repository-root", type=Path)
    args = parser.parse_args()
    checker = Path(__file__).with_name("check_vault_health.py")
    command = [sys.executable, str(checker), str(args.project_folder)]
    if args.repository_root:
        command.extend(["--repository-root", str(args.repository_root)])
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode not in {0, 1}:
        raise RuntimeError(completed.stderr.strip() or "health checker failed")
    report = json.loads(completed.stdout)
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(report, args.project_id, generated_at), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "summary": report["summary"]}, indent=2))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
