#!/usr/bin/env python3
"""Validate agent-harness skill repository structure.

This intentionally uses only the Python standard library so it can run in CI
without bootstrapping project dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
import sys


RE_KEBAB_CASE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RE_XML_TAG = re.compile(r"[<>]")
RE_HEADING = re.compile(r"^## (.+)$")

MAX_DESCRIPTION_LEN = 1024
MIN_DESCRIPTION_LEN = 80
REQUIRED_SECTIONS = (
    "Overview",
    "When To Use",
    "Inputs Needed",
    "Execution Order",
    "Step-by-Step Process",
    "Checks",
    "Output Format",
    "Common Mistakes",
    "Example Prompts",
)


@dataclass
class Issues:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_frontmatter(path: Path, issues: Issues) -> dict[str, str] | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        issues.error(f"{path}: missing YAML frontmatter")
        return None

    end = text.find("\n---\n", 4)
    if end == -1:
        issues.error(f"{path}: malformed YAML frontmatter")
        return None

    data: dict[str, str] = {}
    for raw in text[4:end].splitlines():
        if not raw.strip() or raw.startswith(" "):
            continue
        key, sep, value = raw.partition(":")
        if not sep:
            continue
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def required_section_positions(text: str) -> dict[str, int]:
    positions: dict[str, int] = {}
    required = set(REQUIRED_SECTIONS)

    for line_number, raw in enumerate(text.splitlines(), start=1):
        match = RE_HEADING.fullmatch(raw.strip())
        if not match:
            continue
        heading = match.group(1)
        if heading in required and heading not in positions:
            positions[heading] = line_number

    return positions


def validate_skill_dir(path: Path, issues: Issues) -> None:
    slug = path.name
    if not RE_KEBAB_CASE.fullmatch(slug):
        issues.error(f"{path}: skill directory must be kebab-case")

    skill_md = path / "SKILL.md"
    if not skill_md.exists():
        issues.error(f"{path}: missing SKILL.md")
        return

    frontmatter = parse_frontmatter(skill_md, issues)
    if not frontmatter:
        return

    name = frontmatter.get("name", "")
    description = frontmatter.get("description", "")

    if name != slug:
        issues.error(f"{skill_md}: name '{name}' must match directory '{slug}'")
    if not RE_KEBAB_CASE.fullmatch(name):
        issues.error(f"{skill_md}: name must be kebab-case")
    if not description:
        issues.error(f"{skill_md}: description is required")
    elif not description.startswith("Use when "):
        issues.error(f"{skill_md}: description must start with 'Use when '")
    elif len(description) < MIN_DESCRIPTION_LEN:
        issues.warning(
            f"{skill_md}: description is short ({len(description)} chars); "
            "include concrete trigger terms"
        )
    if len(description) > MAX_DESCRIPTION_LEN:
        issues.error(f"{skill_md}: description exceeds {MAX_DESCRIPTION_LEN} chars")
    if RE_XML_TAG.search(description):
        issues.error(f"{skill_md}: description must not contain XML tags")

    text = skill_md.read_text(encoding="utf-8")
    section_positions = required_section_positions(text)
    for section in REQUIRED_SECTIONS:
        if section not in section_positions:
            issues.error(f"{skill_md}: missing required section '## {section}'")

    ordered_positions = [
        section_positions[section]
        for section in REQUIRED_SECTIONS
        if section in section_positions
    ]
    if (
        len(ordered_positions) == len(REQUIRED_SECTIONS)
        and ordered_positions != sorted(ordered_positions)
    ):
        issues.error(
            f"{skill_md}: required sections must appear in order: "
            + ", ".join(REQUIRED_SECTIONS)
        )

    if "- First:" not in text or "- Then:" not in text or "- Finally:" not in text:
        issues.error(
            f"{skill_md}: Execution Order must include First, Then, and Finally bullets"
        )

    if "```markdown" not in text:
        issues.error(f"{skill_md}: Output Format must include a markdown code block")
    if "## Detected Mapping" not in text:
        issues.error(f"{skill_md}: Output Format must include Detected Mapping")


def main() -> int:
    root = repo_root()
    skills_root = root / "skills"
    issues = Issues()

    if not skills_root.exists():
        issues.error(f"{skills_root}: missing skills directory")
    else:
        skill_dirs = sorted(p for p in skills_root.iterdir() if p.is_dir())
        if not skill_dirs:
            issues.error(f"{skills_root}: no skill directories found")
        for skill_dir in skill_dirs:
            validate_skill_dir(skill_dir, issues)

    if issues.warnings:
        print("Warnings:")
        for warning in issues.warnings:
            print(f"  warning: {warning}")
        print()

    if issues.errors:
        print("Validation FAILED:", file=sys.stderr)
        for error in issues.errors:
            print(f"  error: {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(list(skills_root.iterdir()))} skills -- all passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
