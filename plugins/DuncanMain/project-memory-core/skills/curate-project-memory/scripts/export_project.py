#!/usr/bin/env python3
"""Create a portable Project Memory snapshot without network access."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
PROPERTY = re.compile(r"^([A-Za-z_][\w-]*):\s*(.*)$")
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[:=]\s*[^\s]+", re.I),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
)


def properties(text: str) -> dict[str, str]:
    match = FRONTMATTER.search(text)
    if not match:
        return {}
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        item = PROPERTY.match(line)
        if item:
            result[item.group(1)] = item.group(2).strip().strip("'\"")
    return result


def safe_include(root: Path, value: str) -> Path:
    relative = Path(value.replace("\\", "/"))
    if relative.is_absolute():
        raise ValueError("include paths must be project-relative")
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError("include path escapes the project folder") from error
    if not resolved.is_file() or resolved.suffix.casefold() != ".md":
        raise ValueError(f"included note does not exist: {value}")
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_folder", type=Path)
    parser.add_argument("output_file", type=Path)
    parser.add_argument("--mode", required=True, choices=("onboarding", "decision-log", "audit", "context"))
    parser.add_argument("--include", action="append", default=[])
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    root = args.project_folder.resolve()
    output = args.output_file.resolve()
    if not root.is_dir():
        parser.error(f"project folder does not exist: {root}")
    if output.exists() and not args.force:
        parser.error(f"output already exists: {output}")

    available = [
        path for path in sorted(root.rglob("*.md"))
        if output != path.resolve() and not any(part.casefold() in {".obsidian", "inbox"} for part in path.parts)
    ]
    records = [(path, path.read_text(encoding="utf-8", errors="replace")) for path in available]
    if any(pattern.search(text) for _, text in records for pattern in SECRET_PATTERNS):
        parser.error("possible credential-like content detected; run the health review before exporting")

    selected: list[tuple[Path, str]] = []
    if args.mode == "audit":
        selected = records
    elif args.mode == "decision-log":
        selected = [(path, text) for path, text in records if properties(text).get("type") == "decision" and properties(text).get("status") in {"accepted", "superseded"}]
    elif args.mode == "onboarding":
        for path, text in records:
            props = properties(text)
            if path.name.casefold() in {"project.md", "current state.md", "handoff.md"} or (props.get("type") == "decision" and props.get("status") == "accepted"):
                selected.append((path, text))
    else:
        if not args.include:
            parser.error("context mode requires at least one inspected --include note")
        wanted = {safe_include(root, value) for value in args.include}
        wanted.update(path for path, _ in records if path.name.casefold() in {"project.md", "current state.md"})
        selected = [(path, text) for path, text in records if path in wanted]

    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    output.parent.mkdir(parents=True, exist_ok=True)
    if args.mode == "audit":
        manifest = {
            "format": "project-memory-audit-v1",
            "created_at": created_at,
            "snapshot": True,
            "notes": [
                {
                    "path": path.relative_to(root).as_posix(),
                    "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    "type": properties(text).get("type") or None,
                    "project_id": properties(text).get("project_id") or None,
                    "knowledge_id": properties(text).get("knowledge_id") or None,
                    "status": properties(text).get("status") or None,
                    "updated": properties(text).get("updated") or None,
                }
                for path, text in selected
            ],
        }
        output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    else:
        lines = [
            f"# Project Memory {args.mode.replace('-', ' ').title()} Export",
            "",
            f"Created: {created_at}",
            "",
            "> Snapshot only. Canonical knowledge remains in the Project Memory vault.",
            "",
        ]
        for path, text in selected:
            lines.extend(["---", "", f"Source: `{path.relative_to(root).as_posix()}`", "", text.rstrip(), ""])
        output.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({"mode": args.mode, "output_file": str(output), "notes_exported": len(selected), "snapshot": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
