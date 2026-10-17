#!/usr/bin/env python3
"""Read-only structural health check for a Project Memory folder."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path


FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
PROPERTY = re.compile(r"^([A-Za-z_][\w-]*):\s*(.*)$")
CODE_PATH = re.compile(r"^\s+path:\s*['\"]?([^'\"\n]+)['\"]?\s*$", re.MULTILINE)
WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
WINDOWS_PATH = re.compile(r"(?<![\w-])[A-Za-z]:\\(?:[^\s<>:\"|?*]+\\)*[^\s<>:\"|?*]*")
UNIX_PATH = re.compile(r"(?<![\w.])/(?:home|Users|mnt|var|opt|srv)/[^\s)\]]+")
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[:=]\s*[^\s]+", re.I),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
)
REQUIRED = {
    "project": {"project_id", "status"},
    "current-state": {"project_id", "updated"},
    "decision": {"project_id", "status", "updated", "confidence"},
    "handoff": {"project_id", "updated"},
    "promotion-inbox": {"project_id", "updated"},
}


def scalar(value: str) -> str:
    value = value.strip()
    if value in {"", "null", "~", "[]"}:
        return ""
    return value.strip("'\"")


def properties(text: str) -> dict[str, str]:
    match = FRONTMATTER.search(text)
    if not match:
        return {}
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        item = PROPERTY.match(line)
        if item:
            result[item.group(1)] = scalar(item.group(2))
    return result


def add(findings: list[dict[str, str]], severity: str, code: str, path: Path, message: str) -> None:
    findings.append({"severity": severity, "code": code, "file": path.as_posix(), "message": message})


def resolve_wikilink(root: Path, source: Path, target: str, stems: dict[str, list[Path]]) -> bool:
    normalized = target.strip().replace("\\", "/")
    direct = source.parent / normalized
    root_direct = root / normalized
    return any(
        candidate.is_file()
        for candidate in (
            direct,
            direct.with_suffix(".md"),
            direct.with_suffix(".base"),
            root_direct,
            root_direct.with_suffix(".md"),
            root_direct.with_suffix(".base"),
        )
    ) or Path(normalized).name.casefold() in stems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_folder", type=Path)
    parser.add_argument("--repository-root", type=Path)
    args = parser.parse_args()
    root = args.project_folder.resolve()
    if not root.is_dir():
        parser.error(f"project folder does not exist: {root}")

    files = sorted(p for p in root.rglob("*.md") if ".obsidian" not in p.parts)
    team_enabled = any(properties(path.read_text(encoding="utf-8", errors="replace")).get("type") == "team" for path in files)
    stems: dict[str, list[Path]] = {}
    for path in files:
        stems.setdefault(path.stem.casefold(), []).append(path)

    findings: list[dict[str, str]] = []
    project_ids: list[str] = []
    decision_titles: list[str] = []
    knowledge_ids: list[str] = []
    today = date.today()

    for path in files:
        relative = path.relative_to(root)
        text = path.read_text(encoding="utf-8", errors="replace")
        props = properties(text)
        note_type = props.get("type", "")
        project_id = props.get("project_id", "")
        knowledge_id = props.get("knowledge_id", "")
        if knowledge_id:
            knowledge_ids.append(knowledge_id)
        if project_id:
            project_ids.append(project_id)
        elif note_type in REQUIRED:
            add(findings, "error", "missing-project-id", relative, "Managed note has no project_id property.")

        for required in REQUIRED.get(note_type, set()):
            if not props.get(required):
                add(findings, "error", "missing-property", relative, f"{note_type} note is missing {required}.")

        review_after = props.get("review_after")
        if review_after:
            try:
                if date.fromisoformat(review_after) < today:
                    add(findings, "warning", "review-overdue", relative, f"Review was due {review_after}.")
            except ValueError:
                add(findings, "warning", "invalid-review-date", relative, "review_after is not an ISO date.")

        if note_type == "current-state" and not review_after and props.get("updated"):
            try:
                age = (today - date.fromisoformat(props["updated"])).days
                if age > 90:
                    add(findings, "warning", "current-state-stale", relative, f"Current state was last updated {age} days ago and has no review_after date.")
            except ValueError:
                add(findings, "warning", "invalid-updated-date", relative, "updated is not an ISO date.")

        if props.get("status") == "superseded" and not props.get("superseded_by"):
            add(findings, "warning", "missing-superseding-link", relative, "Superseded note does not identify its replacement.")

        if team_enabled and note_type == "decision":
            if not knowledge_id:
                add(findings, "warning", "missing-knowledge-id", relative, "Team decision has no stable knowledge_id.")
            if not props.get("review_status"):
                add(findings, "warning", "missing-review-status", relative, "Team decision has no review_status.")

        implementation = props.get("implementation_status")
        if implementation in {"observed", "proposed", "implemented"} and not (props.get("applies_to_branch") or props.get("applies_to_revision")):
            add(findings, "warning", "unscoped-branch-state", relative, f"Implementation state {implementation} has no branch or revision scope.")

        if WINDOWS_PATH.search(text) or UNIX_PATH.search(text):
            add(findings, "warning", "absolute-path", relative, "Note may contain a machine-specific absolute path.")

        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            add(findings, "error", "possible-secret", relative, "Possible credential-like content detected; value withheld.")

        if args.repository_root and FRONTMATTER.search(text):
            frontmatter = FRONTMATTER.search(text).group(1)
            for code_path in CODE_PATH.findall(frontmatter):
                candidate = code_path.strip().replace("\\", "/")
                if Path(candidate).is_absolute():
                    continue
                if not (args.repository_root / Path(candidate)).exists():
                    add(findings, "warning", "missing-code-reference", relative, f"Referenced repository path does not exist: {code_path.strip()}")

        for target in sorted(set(WIKILINK.findall(text))):
            if not resolve_wikilink(root, path, target, stems):
                add(findings, "warning", "broken-wikilink", relative, f"Unresolved wikilink: {target}")

        if note_type == "decision":
            heading = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
            if heading:
                decision_titles.append(heading.group(1).strip().casefold())

    distinct_ids = sorted(set(project_ids))
    if len(distinct_ids) > 1:
        findings.append({"severity": "warning", "code": "mixed-project-ids", "file": ".", "message": "Folder contains multiple project IDs: " + ", ".join(distinct_ids)})

    for title, count in Counter(decision_titles).items():
        if count > 1:
            findings.append({"severity": "warning", "code": "duplicate-decision-title", "file": ".", "message": f"Decision title appears {count} times: {title}"})

    for knowledge_id, count in Counter(knowledge_ids).items():
        if count > 1:
            findings.append({"severity": "error", "code": "duplicate-knowledge-id", "file": ".", "message": f"knowledge_id appears {count} times: {knowledge_id}"})

    counts = Counter(item["severity"] for item in findings)
    print(json.dumps({
        "project_folder": str(root),
        "files_checked": len(files),
        "summary": {"errors": counts["error"], "warnings": counts["warning"], "information": counts["information"]},
        "findings": findings,
    }, indent=2))
    return 1 if counts["error"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
