#!/usr/bin/env python3
"""Check that SKILL.md files use English-only body text.

The check intentionally looks for CJK characters instead of trying to prove
natural-language fluency. It gives the repository a stable gate for the
"SKILL.md files are English" rule without external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sys


CJK_RE = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]")


@dataclass(frozen=True)
class LanguageIssue:
    path: Path
    line_number: int
    message: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def find_skill_files(root: Path) -> list[Path]:
    skills_root = root / "skills"
    if not skills_root.exists():
        return []
    return sorted(skills_root.glob("*/SKILL.md"))


def scan_file(path: Path) -> list[LanguageIssue]:
    issues: list[LanguageIssue] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if CJK_RE.search(line):
            issues.append(
                LanguageIssue(
                    path=path,
                    line_number=line_number,
                    message="CJK characters are not allowed in SKILL.md files",
                )
            )
    return issues


def main() -> int:
    issues: list[LanguageIssue] = []
    for path in find_skill_files(repo_root()):
        issues.extend(scan_file(path))

    if issues:
        print("Skill language check FAILED:", file=sys.stderr)
        for issue in issues:
            print(
                f"  error: {issue.path}:{issue.line_number}: {issue.message}",
                file=sys.stderr,
            )
        return 1

    print("Skill language check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
