#!/usr/bin/env python3
"""Build a local capability registry from SKILL.md and plugin.json files.

The builder is intentionally local and conservative:
- read-only scan of metadata files
- no network
- no connector content access
- no authorization checks
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "registry" / "capabilities.generated.json"
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*", re.DOTALL)


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    data: dict[str, str] = {}
    current_key: str | None = None
    current_value: list[str] = []
    for raw_line in match.group(1).splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if re.match(r"^[A-Za-z0-9_-]+:", line):
            if current_key:
                data[current_key] = " ".join(current_value).strip()
            key, value = line.split(":", 1)
            current_key = key.strip()
            current_value = [value.strip().strip('"').strip("'")]
        elif current_key:
            current_value.append(line.strip())
    if current_key:
        data[current_key] = " ".join(current_value).strip()
    return data


def categories_for(name: str, description: str, kind: str) -> list[str]:
    haystack = f"{name} {description}".lower()
    categories: set[str] = set()
    if kind == "plugin":
        categories.add("plugin")
    if kind == "skill":
        categories.add("skill")

    mapping = {
        "debug": ["process", "debugging"],
        "bug": ["process", "debugging"],
        "test": ["process", "testing"],
        "verify": ["process", "verification"],
        "review": ["process", "review"],
        "plan": ["process", "planning"],
        "routing": ["process", "routing"],
        "router": ["process", "routing"],
        "registry": ["process", "routing", "maintenance"],
        "orchestration": ["process", "orchestration", "multi_agent"],
        "subagent": ["process", "orchestration", "multi_agent"],
        "github": ["source", "github", "external_connector", "requires_auth"],
        "gmail": ["source", "gmail", "external_connector", "requires_auth"],
        "drive": ["source", "drive", "external_connector", "requires_auth"],
        "notion": ["source", "notion", "external_connector", "requires_auth"],
        "slack": ["source", "slack", "external_connector", "requires_auth"],
        "figma": ["source", "figma", "external_connector", "requires_auth", "design"],
        "linear": ["source", "linear", "external_connector", "requires_auth"],
        "canva": ["artifact", "visual", "external_connector", "requires_auth"],
        "pdf": ["artifact", "pdf", "local"],
        "docx": ["artifact", "document", "local"],
        "document": ["artifact", "document"],
        "spreadsheet": ["artifact", "spreadsheet"],
        "xlsx": ["artifact", "spreadsheet", "local"],
        "csv": ["artifact", "spreadsheet", "local"],
        "presentation": ["artifact", "presentation"],
        "ppt": ["artifact", "presentation", "local"],
        "frontend": ["artifact", "frontend", "web_app", "local"],
        "react": ["artifact", "frontend", "web_app", "local"],
        "image": ["artifact", "image", "visual"],
    }
    for token, values in mapping.items():
        if token in haystack:
            categories.update(values)
    if "external_connector" not in categories:
        categories.add("local")
    return sorted(categories)


def file_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def skill_card(path: Path) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None
    meta = parse_frontmatter(text)
    name = meta.get("name") or path.parent.name
    description = meta.get("description", "")
    return {
        "id": name.lower().replace(":", "-").replace("_", "-"),
        "name": name,
        "kind": "skill",
        "categories": categories_for(name, description, "skill"),
        "use_when": description,
        "avoid_when": [],
        "inputs": [],
        "outputs": [],
        "requires": [],
        "examples": [],
        "provenance": {
            "source_type": "skill",
            "path": str(path),
        },
        "updated_at": file_mtime(path),
    }


def plugin_card(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    name = data.get("name") or path.parent.parent.name
    description = data.get("description", "")
    return {
        "id": str(name).lower().replace("_", "-"),
        "name": name,
        "kind": "plugin",
        "categories": categories_for(str(name), str(description), "plugin"),
        "use_when": str(description),
        "avoid_when": [],
        "inputs": [],
        "outputs": [],
        "requires": ["connector_auth"] if "external_connector" in categories_for(str(name), str(description), "plugin") else [],
        "examples": [],
        "provenance": {
            "source_type": "plugin",
            "path": str(path),
        },
        "updated_at": file_mtime(path),
    }


def iter_files(root: Path, filename: str) -> list[Path]:
    if not root.exists():
        return []
    return [path for path in root.rglob(filename) if path.is_file()]


def default_roots() -> list[Path]:
    roots = [
        Path(os.path.expanduser("~/.codex/skills")),
        Path(os.path.expanduser("~/.codex/plugins/cache")),
        ROOT / "skills",
    ]
    return roots


def build_registry(roots: list[Path]) -> dict[str, Any]:
    cards: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for root in roots:
        for path in iter_files(root, "SKILL.md"):
            card = skill_card(path)
            if card:
                key = (card["kind"], card["id"])
                if key not in seen:
                    seen.add(key)
                    cards.append(card)
        for path in iter_files(root, "plugin.json"):
            if path.parent.name != ".codex-plugin":
                continue
            card = plugin_card(path)
            if card:
                key = (card["kind"], card["id"])
                if key not in seen:
                    seen.add(key)
                    cards.append(card)

    return {
        "schema_version": "1.0",
        "generated_at": iso_now(),
        "source_roots": [str(root) for root in roots],
        "capabilities": sorted(cards, key=lambda item: (item["kind"], item["id"])),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local Skill Routing Kit registry.")
    parser.add_argument("--root", action="append", type=Path, help="Additional root to scan. Can be repeated.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output registry JSON path.")
    parser.add_argument("--yes", action="store_true", help="Write without interactive confirmation.")
    parser.add_argument("--dry-run", action="store_true", help="Print summary without writing.")
    args = parser.parse_args(argv)

    roots = default_roots()
    if args.root:
        roots.extend(args.root)

    registry = build_registry(roots)
    print("Skill Routing Kit registry summary:")
    print(f"- source roots: {len(roots)}")
    print(f"- capabilities: {len(registry['capabilities'])}")
    print(f"- output: {args.output}")

    if args.dry_run:
        return 0

    should_write = args.yes
    if not should_write and sys.stdin.isatty():
        answer = input("Write registry? [y/N] ").strip().lower()
        should_write = answer in {"y", "yes"}

    if not should_write:
        print("Registry not written. Re-run with --yes to write non-interactively.")
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
