#!/usr/bin/env python3
"""Tests for the skill language checker."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPT_DIR = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "check_skill_language", SCRIPT_DIR / "check_skill_language.py"
)
assert SPEC is not None
assert SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)


def write_skill(root: Path, body: str) -> Path:
    skill_dir = root / "skills" / "sample-skill"
    skill_dir.mkdir(parents=True)
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(body, encoding="utf-8")
    return skill_path


class CheckSkillLanguageTest(unittest.TestCase):
    def test_english_skill_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_path = write_skill(Path(tmp), "# Sample\n\nEnglish only.\n")

            self.assertEqual([], checker.scan_file(skill_path))

    def test_cjk_text_fails_with_line_number(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_path = write_skill(Path(tmp), "# Sample\n\nChinese text: 中文\n")

            issues = checker.scan_file(skill_path)

            self.assertEqual(1, len(issues))
            self.assertEqual(3, issues[0].line_number)
            self.assertIn("CJK", issues[0].message)

    def test_finds_skill_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_path = write_skill(Path(tmp), "# Sample\n")

            self.assertEqual([skill_path], checker.find_skill_files(Path(tmp)))


if __name__ == "__main__":
    unittest.main()
