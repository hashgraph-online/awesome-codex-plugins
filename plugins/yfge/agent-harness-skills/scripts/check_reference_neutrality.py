#!/usr/bin/env python3
"""Check that public skill guidance stays repo-neutral."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sys


BANNED_SOURCE_PROJECTS = (
    "ai-shifu",
    "ai-video-studio",
    "talkreplay",
    "orion",
    "elab-system",
    "elabsystem",
    "elab",
)
BANNED_DOMAIN_MARKERS = (
    "test account",
    "username",
    "password",
)
ENGINEERING_FORM_TERMS = (
    "backend",
    "frontend",
    "browser",
    "device",
    "docker",
    "provider",
    "payment",
    "billing",
    "notification",
    "media",
    "rfid",
    "timeline",
    "wechat",
    "figma",
)
ABSOLUTE_LOCAL_PATH_RE = re.compile(
    r"(?i)(?:/Users/|/home/|/private/tmp/|[A-Z]:\\Users\\)"
)
CONCRETE_URL_RE = re.compile(r"https?://[^\s>)]+")
PLACEHOLDER_URL_RE = re.compile(r"^https?://(?:example\.(?:com|org|test)|localhost)")
DEFAULT_ASSUMPTION_RE = re.compile(
    r"\b(?:all|every|any)\s+(?:repo|repos|repository|repositories)\b|\b(?:always|must|required)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class NeutralityIssue:
    path: Path
    line_number: int
    message: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def public_surface_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for relative in (
        "AGENTS.md",
        "INDEX.md",
        "README.md",
        "README.zh-CN.md",
        "docs/scenario-tests.md",
    ):
        path = root / relative
        if path.exists():
            files.append(path)

    for pattern in (
        "references/*.json",
        "templates/*.md",
        "references/**/*.md",
        "skills/*/SKILL.md",
        "skills/*/references/*.md",
    ):
        files.extend(sorted(root.glob(pattern)))

    return sorted(set(files))


def _contains_term(line: str, term: str) -> bool:
    return re.search(rf"(?<![a-z0-9-]){re.escape(term)}(?![a-z0-9-])", line) is not None


def _allows_engineering_form_terms(path: Path) -> bool:
    normalized = path.as_posix()
    return (
        normalized.endswith("references/harness-profiles.json")
        or "/templates/" in normalized
        or normalized.startswith("templates/")
    )


def scan_file(path: Path) -> list[NeutralityIssue]:
    issues: list[NeutralityIssue] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        lower = line.lower()
        for term in BANNED_SOURCE_PROJECTS:
            if _contains_term(lower, term):
                issues.append(
                    NeutralityIssue(
                        path,
                        line_number,
                        f"source project name is not allowed: {term}",
                    )
                )
        for term in BANNED_DOMAIN_MARKERS:
            if _contains_term(lower, term):
                issues.append(
                    NeutralityIssue(
                        path,
                        line_number,
                        f"private account marker is not allowed: {term}",
                    )
                )
        for term in ENGINEERING_FORM_TERMS:
            if not _contains_term(lower, term):
                continue
            if _allows_engineering_form_terms(path):
                continue
            if DEFAULT_ASSUMPTION_RE.search(line):
                issues.append(
                    NeutralityIssue(
                        path,
                        line_number,
                        f"engineering-form default assumption is not allowed: {term}",
                    )
                )

        if ABSOLUTE_LOCAL_PATH_RE.search(line):
            issues.append(NeutralityIssue(path, line_number, "absolute local path is not allowed"))

        for match in CONCRETE_URL_RE.finditer(line):
            url = match.group(0).rstrip(".,")
            if not PLACEHOLDER_URL_RE.match(url):
                issues.append(
                    NeutralityIssue(path, line_number, f"private or concrete URL is not allowed: {url}")
                )

    return issues


def main() -> int:
    issues: list[NeutralityIssue] = []
    for path in public_surface_files(repo_root()):
        issues.extend(scan_file(path))

    if issues:
        print("Reference neutrality check FAILED:", file=sys.stderr)
        for issue in issues:
            print(
                f"  error: {issue.path}:{issue.line_number}: {issue.message}",
                file=sys.stderr,
            )
        return 1

    print("Reference neutrality check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
