#!/usr/bin/env python3
"""Wrapper for the canonical Thoth doctor command."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from thoth.plan.doctor import build_doctor_payload, render_doctor_text
from thoth.objects import Store


REQUIRED_AGENT_OS_FILES = [
    "project-index.md",
    "requirements.md",
    "architecture-milestones.md",
    "todo.md",
    "cross-repo-mapping.md",
    "acceptance-report.md",
    "lessons-learned.md",
    "run-log.md",
    "change-decisions.md",
]


def check_required_files() -> tuple[bool, str]:
    root = Path.cwd()
    missing = [name for name in REQUIRED_AGENT_OS_FILES if not (root / ".agent-os" / name).exists()]
    if missing:
        return False, "Missing required .agent-os files: " + ", ".join(missing)
    return True, "PASS required .agent-os files present"


def check_id_integrity() -> tuple[bool, str]:
    work_items = Store(Path.cwd()).list("work_item")
    ids: list[str] = []
    for item in work_items:
        object_id = item.get("object_id")
        if isinstance(object_id, str) and object_id.strip():
            ids.append(object_id.strip())
    if not ids:
        return True, "PASS no work items found"
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        return False, "Duplicate work item ids: " + ", ".join(duplicates)
    return True, f"PASS {len(ids)} unique work item ids"


def main() -> int:
    parser = argparse.ArgumentParser(description="Thoth doctor")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    payload = build_doctor_payload(Path.cwd())
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_doctor_text(payload), end="")
    return 0 if payload.get("overall_ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
