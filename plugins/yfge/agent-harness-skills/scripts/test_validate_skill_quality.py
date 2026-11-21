#!/usr/bin/env python3
"""Tests for the skill quality validator."""

from __future__ import annotations

from pathlib import Path
import importlib.util
import sys
import tempfile
import unittest

SCRIPT_DIR = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "validate_skill_quality", SCRIPT_DIR / "validate_skill_quality.py"
)
assert SPEC is not None
assert SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


VALID_BODY = """---
name: sample-skill
description: Use when validating sample repository skills with concrete trigger terms and predictable structure.
---

# Sample Skill

## Overview

English overview.

## When To Use

- Use this in tests.

## Inputs Needed

- A temporary skill directory.

## Execution Order

- First: Read the skill.
- Then: Validate the sections.
- Finally: Report issues.

## Step-by-Step Process

1. Inspect.

## Checks

- Check structure.

## Output Format

```markdown
# Sample

## Detected Mapping
- entrypoint: `AGENTS.md`
```

## Common Mistakes

- Skipping validation.

## Example Prompts

- "Validate this sample skill."
"""


def make_skill(root: Path, body: str) -> Path:
    skill_dir = root / "sample-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")
    return skill_dir


class ValidateSkillQualityTest(unittest.TestCase):
    def test_valid_skill_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            issues = validator.Issues()

            validator.validate_skill_dir(make_skill(Path(tmp), VALID_BODY), issues)

            self.assertEqual([], issues.errors)

    def test_missing_required_section_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            issues = validator.Issues()
            body = VALID_BODY.replace("\n## Checks\n\n- Check structure.\n", "\n")

            validator.validate_skill_dir(make_skill(Path(tmp), body), issues)

            self.assertTrue(
                any(
                    "missing required section '## Checks'" in error
                    for error in issues.errors
                ),
                issues.errors,
            )

    def test_out_of_order_required_section_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            issues = validator.Issues()
            body = VALID_BODY.replace(
                "## Inputs Needed\n\n- A temporary skill directory.\n\n## Execution Order",
                "## Execution Order",
            ).replace(
                "## Step-by-Step Process",
                "## Inputs Needed\n\n- A temporary skill directory.\n\n## Step-by-Step Process",
            )

            validator.validate_skill_dir(make_skill(Path(tmp), body), issues)

            self.assertTrue(
                any(
                    "required sections must appear in order" in error
                    for error in issues.errors
                ),
                issues.errors,
            )

    def test_missing_detected_mapping_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            issues = validator.Issues()
            body = VALID_BODY.replace(
                "\n## Detected Mapping\n- entrypoint: `AGENTS.md`\n",
                "\n",
            )

            validator.validate_skill_dir(make_skill(Path(tmp), body), issues)

            self.assertTrue(
                any("Output Format must include Detected Mapping" in error for error in issues.errors),
                issues.errors,
            )


if __name__ == "__main__":
    unittest.main()
