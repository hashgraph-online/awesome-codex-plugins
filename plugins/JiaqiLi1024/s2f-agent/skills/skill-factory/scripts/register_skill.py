#!/usr/bin/env python3
"""Append a skill entry to registry/skills.yaml (append-only)."""

from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path
from typing import List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append skill to registry/skills.yaml")
    parser.add_argument("--repo-root", default=None, help="Repository root override")
    parser.add_argument("--registry-file", default=None, help="Registry file override")
    parser.add_argument("--skill-id", required=True)
    parser.add_argument("--path", required=True)
    parser.add_argument("--family", required=True)
    parser.add_argument("--task", action="append", default=[])
    parser.add_argument("--trigger", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def as_list(values: List[str], name: str) -> List[str]:
    items = [v.strip() for v in values if isinstance(v, str) and v.strip()]
    if not items:
        raise SystemExit(f"At least one --{name} is required")
    return items


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[3]
    registry_file = Path(args.registry_file).resolve() if args.registry_file else repo_root / "registry" / "skills.yaml"

    if not registry_file.exists():
        raise SystemExit(f"Registry file not found: {registry_file}")

    tasks = as_list(args.task, "task")
    triggers = as_list(args.trigger, "trigger")
    skill_id = args.skill_id.strip()
    path_value = args.path.strip()
    family = args.family.strip()

    content = registry_file.read_text()

    if f"- id: {skill_id}" in content:
        print(f"[skip] skill already present in registry: {skill_id}")
        return 0

    if "skills:" not in content:
        raise SystemExit("Invalid registry format: missing 'skills:' root key")

    updated_at = dt.date.today().isoformat()
    content = re.sub(
        r'^updated_at:\s*"[0-9]{4}-[0-9]{2}-[0-9]{2}"\s*$',
        f'updated_at: "{updated_at}"',
        content,
        count=1,
        flags=re.MULTILINE,
    )

    lines = [
        f"  - id: {skill_id}",
        f"    path: {path_value}",
        "    enabled: true",
        f"    family: {family}",
        "    tasks:",
    ]
    lines.extend(f"      - {task}" for task in tasks)
    lines.append("    triggers:")
    lines.extend(f"      - {trigger}" for trigger in triggers)

    if not content.endswith("\n"):
        content += "\n"
    content += "\n" + "\n".join(lines) + "\n"

    if args.dry_run:
        print("[dry-run] would append registry entry:")
        print("\n".join(lines))
        return 0

    registry_file.write_text(content)
    print(f"[ok] appended {skill_id} to {registry_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
