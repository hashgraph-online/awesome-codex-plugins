#!/usr/bin/env python3
"""Check explicit Project Memory verification tables against a local repository."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


HEADING = re.compile(r"^##\s+Verification checks\s*$", re.I)
ALLOWED = {"file-exists", "file-absent", "contains", "not-contains", "regex"}


def safe_target(root: Path, relative: str) -> Path | None:
    candidate = Path(relative.strip().replace("\\", "/"))
    if candidate.is_absolute():
        return None
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None
    return resolved


def rows(text: str) -> list[tuple[str, str, str, str]]:
    lines = text.splitlines()
    active = False
    found: list[tuple[str, str, str, str]] = []
    for line in lines:
        if HEADING.match(line.strip()):
            active = True
            continue
        if active and line.startswith("## "):
            break
        if not active or not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4 or cells[0].casefold() in {"repository path", "---"} or set(cells[0]) == {"-"}:
            continue
        found.append((cells[0], cells[1].casefold(), cells[2], cells[3]))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_folder", type=Path)
    parser.add_argument("repository_root", type=Path)
    args = parser.parse_args()
    project = args.project_folder.resolve()
    repository = args.repository_root.resolve()
    if not project.is_dir() or not repository.is_dir():
        parser.error("project_folder and repository_root must both exist")

    results: list[dict[str, object]] = []
    for note in sorted(project.rglob("*.md")):
        if any(part.casefold() in {".obsidian", "inbox"} for part in note.parts):
            continue
        text = note.read_text(encoding="utf-8", errors="replace")
        for relative_path, check, expected, purpose in rows(text):
            outcome = "pass"
            detail = "Evidence check passed."
            target = safe_target(repository, relative_path)
            if target is None:
                outcome, detail = "invalid", "Path is absolute or escapes the repository root."
            elif check not in ALLOWED:
                outcome, detail = "invalid", "Check type is not supported."
            elif check in {"contains", "not-contains", "regex"} and not expected:
                outcome, detail = "invalid", "This check type requires a non-empty Expected value."
            elif check == "file-exists":
                if not target.is_file():
                    outcome, detail = "needs-review", "Expected file does not exist."
            elif check == "file-absent":
                if target.exists():
                    outcome, detail = "needs-review", "Expected path to be absent, but it exists."
            elif not target.is_file():
                outcome, detail = "needs-review", "Evidence file does not exist."
            else:
                content = target.read_text(encoding="utf-8", errors="replace")
                if check == "contains" and expected not in content:
                    outcome, detail = "needs-review", "Expected text was not found."
                elif check == "not-contains" and expected in content:
                    outcome, detail = "needs-review", "Unexpected text was found."
                elif check == "regex":
                    try:
                        if not re.search(expected, content, re.MULTILINE):
                            outcome, detail = "needs-review", "Expected pattern did not match."
                    except re.error:
                        outcome, detail = "invalid", "Expected pattern is not a valid regular expression."
            results.append({
                "note": note.relative_to(project).as_posix(),
                "repository_path": relative_path,
                "check": check,
                "purpose": purpose,
                "outcome": outcome,
                "detail": detail,
            })

    counts = Counter(item["outcome"] for item in results)
    print(json.dumps({
        "project_folder": str(project),
        "repository_root": str(repository),
        "summary": {"checks": len(results), "passed": counts["pass"], "needs_review": counts["needs-review"], "invalid": counts["invalid"]},
        "results": results,
        "interpretation": "A failed check requires inspection; it does not prove that the durable note is wrong.",
    }, indent=2))
    return 1 if counts["invalid"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
