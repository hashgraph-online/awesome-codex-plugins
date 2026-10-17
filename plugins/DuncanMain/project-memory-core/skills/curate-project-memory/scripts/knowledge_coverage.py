#!/usr/bin/env python3
"""Summarize navigation-oriented knowledge coverage by project workstream."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path


FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
KEY = re.compile(r"^([A-Za-z_][\w-]*):\s*(.*)$")
LIST_ITEM = re.compile(r"^\s+-\s+(.+?)\s*$")


def clean(value: str) -> str:
    return value.strip().strip("'\"")


def metadata(text: str) -> dict[str, object]:
    match = FRONTMATTER.search(text)
    if not match:
        return {}
    result: dict[str, object] = {}
    active_list: str | None = None
    for line in match.group(1).splitlines():
        item = KEY.match(line)
        if item:
            key, value = item.groups()
            value = clean(value)
            if value == "[]":
                result[key] = []
                active_list = None
            elif value:
                result[key] = value
                active_list = None
            else:
                result[key] = []
                active_list = key
            continue
        listed = LIST_ITEM.match(line)
        if listed and active_list:
            cast = result.setdefault(active_list, [])
            if isinstance(cast, list):
                cast.append(clean(listed.group(1)))
    return result


def as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).casefold() for item in value if str(item).strip()]
    if isinstance(value, str) and value:
        return [value.casefold()]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_folder", type=Path)
    parser.add_argument("--area", action="append", default=[])
    args = parser.parse_args()
    root = args.project_folder.resolve()
    if not root.is_dir():
        parser.error(f"project folder does not exist: {root}")

    notes: list[tuple[Path, dict[str, object]]] = []
    declared = {area.casefold() for area in args.area}
    for path in sorted(root.rglob("*.md")):
        if any(part.casefold() in {".obsidian", "inbox"} for part in path.parts):
            continue
        props = metadata(path.read_text(encoding="utf-8", errors="replace"))
        if props.get("type") == "project":
            declared.update(as_list(props.get("coverage_areas", [])))
        if props.get("type") != "coverage":
            notes.append((path, props))

    stats: dict[str, dict[str, object]] = defaultdict(lambda: {"notes": 0, "accepted_decisions": 0, "current_state": 0, "owned_notes": 0, "overdue_reviews": 0, "files": []})
    today = date.today()
    for path, props in notes:
        for area in as_list(props.get("workstreams", [])):
            declared.add(area)
            item = stats[area]
            item["notes"] = int(item["notes"]) + 1
            if props.get("type") == "decision" and props.get("status") == "accepted":
                item["accepted_decisions"] = int(item["accepted_decisions"]) + 1
            if props.get("type") == "current-state":
                item["current_state"] = int(item["current_state"]) + 1
            if props.get("owner"):
                item["owned_notes"] = int(item["owned_notes"]) + 1
            review_after = str(props.get("review_after", ""))
            try:
                if review_after and date.fromisoformat(review_after) < today:
                    item["overdue_reviews"] = int(item["overdue_reviews"]) + 1
            except ValueError:
                pass
            cast_files = item["files"]
            if isinstance(cast_files, list):
                cast_files.append(path.relative_to(root).as_posix())

    areas: list[dict[str, object]] = []
    for area in sorted(declared):
        item = dict(stats[area])
        if int(item["notes"]) == 0:
            state = "uncovered"
        elif int(item["notes"]) >= 2 and (int(item["accepted_decisions"]) > 0 or int(item["current_state"]) > 0):
            state = "covered"
        else:
            state = "thin"
        areas.append({"workstream": area, "state": state, **item})

    print(json.dumps({
        "project_folder": str(root),
        "summary": {
            "areas": len(areas),
            "covered": sum(item["state"] == "covered" for item in areas),
            "thin": sum(item["state"] == "thin" for item in areas),
            "uncovered": sum(item["state"] == "uncovered" for item in areas),
        },
        "areas": areas,
        "interpretation": "Coverage is a navigation signal, not a measure of project or staff performance.",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
