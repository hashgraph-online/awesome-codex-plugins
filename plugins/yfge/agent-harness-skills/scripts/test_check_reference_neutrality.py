#!/usr/bin/env python3
"""Tests for the reference neutrality checker."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPT_DIR = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "check_reference_neutrality", SCRIPT_DIR / "check_reference_neutrality.py"
)
assert SPEC is not None
assert SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)


def write_surface(root: Path, relative_path: str, text: str) -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class CheckReferenceNeutralityTest(unittest.TestCase):
    def test_valid_neutral_content_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_surface(
                Path(tmp),
                "skills/sample-skill/references/policy.md",
                "Use a generic run artifact and validation report.\n",
            )

            issues = checker.scan_file(path)

            self.assertEqual([], issues)

    def test_project_name_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_surface(
                Path(tmp),
                "references/harness-patterns.md",
                "Distilled from ai-shifu and other source repositories.\n",
            )

            issues = checker.scan_file(path)

            self.assertTrue(
                any("source project name" in issue.message for issue in issues),
                issues,
            )

    def test_absolute_private_path_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_surface(
                Path(tmp),
                "skills/sample-skill/SKILL.md",
                "Read /Users/example/dev/private-repo/AGENTS.md first.\n",
            )

            issues = checker.scan_file(path)

            self.assertTrue(
                any("absolute local path" in issue.message for issue in issues),
                issues,
            )

    def test_private_url_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_surface(
                Path(tmp),
                "docs/scenario-tests.md",
                "Use https://internal.example.test/runbooks as the source.\n",
            )

            issues = checker.scan_file(path)

            self.assertTrue(
                any("private or concrete URL" in issue.message for issue in issues),
                issues,
            )

    def test_engineering_form_terms_pass_in_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_surface(
                Path(tmp),
                "references/harness-profiles.json",
                '{"archetypes":[{"id":"service","notes":"backend and frontend surfaces may exist"}]}\n',
            )

            issues = checker.scan_file(path)

            self.assertEqual([], issues)

    def test_engineering_form_default_assumption_fails_in_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_surface(
                Path(tmp),
                "skills/sample-skill/SKILL.md",
                "All repositories must run browser smoke tests before review.\n",
            )

            issues = checker.scan_file(path)

            self.assertTrue(
                any("engineering-form default assumption" in issue.message for issue in issues),
                issues,
            )

    def test_public_surface_files_include_profiles_and_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = write_surface(root, "references/harness-profiles.json", "{}\n")
            template = write_surface(root, "templates/validation-matrix.md", "# Template\n")

            files = checker.public_surface_files(root)

            self.assertIn(profile, files)
            self.assertIn(template, files)


if __name__ == "__main__":
    unittest.main()
