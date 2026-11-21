#!/usr/bin/env python3
"""Validate that every skill explains how to build missing harness files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys


REFERENCE_REL = Path("references") / "build-when-missing.md"
REFERENCE_LINK = "references/build-when-missing.md"
REQUIRED_REFERENCE_SECTIONS = (
    "Minimum Files",
    "Bootstrap Steps",
    "Validation",
    "Do Not Include",
)


@dataclass(frozen=True)
class ClosureIssue:
    path: Path
    message: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def find_skill_dirs(root: Path) -> list[Path]:
    skills_root = root / "skills"
    if not skills_root.exists():
        return []
    return sorted(path for path in skills_root.iterdir() if path.is_dir())


def check_skill_dir(skill_dir: Path) -> list[ClosureIssue]:
    issues: list[ClosureIssue] = []
    skill_md = skill_dir / "SKILL.md"
    reference = skill_dir / REFERENCE_REL

    if not skill_md.exists():
        issues.append(ClosureIssue(skill_dir, "missing SKILL.md"))
        return issues

    skill_text = skill_md.read_text(encoding="utf-8")
    if REFERENCE_LINK not in skill_text:
        issues.append(ClosureIssue(skill_md, f"SKILL.md must link {REFERENCE_LINK}"))

    if not reference.exists():
        issues.append(ClosureIssue(skill_dir, f"missing {REFERENCE_LINK}"))
        return issues

    reference_text = reference.read_text(encoding="utf-8")
    for section in REQUIRED_REFERENCE_SECTIONS:
        marker = f"## {section}"
        if marker not in reference_text:
            issues.append(
                ClosureIssue(reference, f"missing required section '{marker}'")
            )

    return issues


def main() -> int:
    issues: list[ClosureIssue] = []
    for skill_dir in find_skill_dirs(repo_root()):
        issues.extend(check_skill_dir(skill_dir))

    if issues:
        print("Skill closure check FAILED:", file=sys.stderr)
        for issue in issues:
            print(f"  error: {issue.path}: {issue.message}", file=sys.stderr)
        return 1

    print("Skill closure check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
