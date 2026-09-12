#!/usr/bin/env python3
"""Rank local Project Memory notes for a task without uploading or indexing data."""

from __future__ import annotations

import argparse
from difflib import SequenceMatcher
import json
import re
from datetime import date
from pathlib import Path


FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
PROPERTY = re.compile(r"^([A-Za-z_][\w-]*):\s*(.*)$")
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{1,}")
HEADING = re.compile(r"^#\s+(.+)$", re.MULTILINE)
EXCLUDED = {"rejected", "deprecated", "superseded"}


def normalize(value: str) -> str:
    return value.strip().strip("'\"").casefold().replace("\\", "/")


def frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = FRONTMATTER.search(text)
    if not match:
        return {}, ""
    props: dict[str, str] = {}
    for line in match.group(1).splitlines():
        item = PROPERTY.match(line)
        if item:
            props[item.group(1)] = normalize(item.group(2))
    return props, match.group(1)


def terms(values: list[str]) -> set[str]:
    return {normalize(token) for value in values for token in TOKEN.findall(value) if len(token) > 2}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_folder", type=Path)
    parser.add_argument("--query", default="")
    parser.add_argument("--code-path", action="append", default=[])
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--include-history", action="store_true")
    args = parser.parse_args()
    root = args.project_folder.resolve()
    if not root.is_dir():
        parser.error(f"project folder does not exist: {root}")

    query_terms = terms([args.query, *args.code_path])
    requested_paths = {normalize(item) for item in args.code_path}
    foundational: list[dict[str, object]] = []
    candidates: list[dict[str, object]] = []

    for path in sorted(root.rglob("*.md")):
        if any(part.casefold() in {".obsidian", "inbox"} for part in path.parts):
            continue
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        props, yaml_text = frontmatter(text)
        status = props.get("status", "")
        title_match = HEADING.search(text)
        title = title_match.group(1).strip() if title_match else path.stem

        if path.name.casefold() in {"project home.md", "project.md", "current state.md"}:
            foundational.append({"file": relative, "title": title, "reason": "foundational project context"})
            continue
        if status in EXCLUDED and not args.include_history:
            continue

        searchable = normalize(f"{relative}\n{title}\n{yaml_text}\n{text}")
        note_terms = terms([relative, title, yaml_text, text])
        matched = sorted(query_terms & note_terms)
        score = min(len(matched) * 2, 16)
        reasons: list[str] = []
        if matched:
            reasons.append("matched task terms: " + ", ".join(matched[:5]))

        exact_paths = sorted(item for item in requested_paths if item and item in searchable)
        if exact_paths:
            score += 20
            reasons.insert(0, "references code path: " + ", ".join(exact_paths))

        fuzzy = SequenceMatcher(None, normalize(args.query), normalize(title)).ratio() if args.query and title else 0.0
        if fuzzy >= 0.5:
            score += round(fuzzy * 6)
            reasons.append(f"fuzzy title similarity {fuzzy:.2f}")

        if not matched and not exact_paths and fuzzy < 0.5:
            continue

        note_type = props.get("type", "")
        if note_type == "decision":
            score += 3
        if status in {"accepted", "active"}:
            score += 3
            reasons.append(f"status is {status}")
        if props.get("confidence") == "confirmed":
            score += 1
        updated = props.get("updated", "")
        if updated:
            try:
                age = (date.today() - date.fromisoformat(updated)).days
                if age <= 30:
                    score += 2
                    reasons.append("updated within 30 days")
                elif age > 180:
                    score -= 1
                    reasons.append("older than 180 days; verify currency")
            except ValueError:
                pass

        candidates.append({
            "file": relative,
            "title": title,
            "score": score,
            "status": status or None,
            "reason": "; ".join(reasons),
        })

    candidates.sort(key=lambda item: (-int(item["score"]), str(item["file"]).casefold()))
    selected = candidates[: max(0, args.limit)]
    print(json.dumps({
        "project_folder": str(root),
        "query": args.query,
        "code_paths": args.code_path,
        "foundational": foundational,
        "selected": selected,
        "candidate_count": len(candidates),
        "selection_note": "Ranking is a retrieval aid; inspect selected notes before relying on them.",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
