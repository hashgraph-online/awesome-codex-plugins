#!/usr/bin/env python3
"""Tests for the skill closure checker."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPT_DIR = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "check_skill_closure", SCRIPT_DIR / "check_skill_closure.py"
)
assert SPEC is not None
assert SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)


VALID_SKILL = """---
name: sample-skill
description: Use when validating sample closure references in repository skills.
---

# Sample Skill

See `references/build-when-missing.md`.
"""

VALID_REFERENCE = """# Build When Missing

## Minimum Files

- `AGENTS.md`

## Bootstrap Steps

1. Create the smallest useful file.

## Validation

- Run the matching checker.

## Do Not Include

- Secrets or private URLs.
"""


def write_skill(root: Path, skill_body: str, reference_body: str | None) -> Path:
    skill_dir = root / "skills" / "sample-skill"
    references_dir = skill_dir / "references"
    references_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(skill_body, encoding="utf-8")
    if reference_body is not None:
        (references_dir / "build-when-missing.md").write_text(
            reference_body, encoding="utf-8"
        )
    return skill_dir


class CheckSkillClosureTest(unittest.TestCase):
    def test_valid_skill_closure_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            issues = checker.check_skill_dir(
                write_skill(Path(tmp), VALID_SKILL, VALID_REFERENCE)
            )

            self.assertEqual([], issues)

    def test_missing_reference_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            issues = checker.check_skill_dir(write_skill(Path(tmp), VALID_SKILL, None))

            self.assertTrue(
                any(
                    "missing references/build-when-missing.md" in issue.message
                    for issue in issues
                ),
                issues,
            )

    def test_missing_skill_link_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill = VALID_SKILL.replace("See `references/build-when-missing.md`.", "")
            issues = checker.check_skill_dir(
                write_skill(Path(tmp), skill, VALID_REFERENCE)
            )

            self.assertTrue(
                any(
                    "must link references/build-when-missing.md" in issue.message
                    for issue in issues
                ),
                issues,
            )

    def test_incomplete_reference_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            incomplete_reference = VALID_REFERENCE.replace(
                "\n## Validation\n\n- Run the matching checker.\n", "\n"
            )
            issues = checker.check_skill_dir(
                write_skill(Path(tmp), VALID_SKILL, incomplete_reference)
            )

            self.assertTrue(
                any(
                    "missing required section '## Validation'" in issue.message
                    for issue in issues
                ),
                issues,
            )


if __name__ == "__main__":
    unittest.main()
