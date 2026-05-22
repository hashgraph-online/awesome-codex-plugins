#!/usr/bin/env python3
import os
import tempfile
import textwrap
import unittest
from pathlib import Path

from check_must_coverage import main, validate_must_coverage


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")


class CheckMustCoverageTests(unittest.TestCase):
    def test_passes_when_must_mapping_is_complete(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_file = root / "SKILL.md"
            mapping_file = root / "references" / "must-rules-map.yaml"
            rules_file = root / "references" / "rules-registry.yaml"

            write_file(
                skill_file,
                """
                ## MUST Rules (Condensed)
                - Do not use `:latest`.
                - `revisionHistoryLimit: 1`
                ## Validation Commands
                """,
            )
            write_file(
                mapping_file,
                """
                version: 1
                must_rules:
                  - must: "Do not use `:latest`."
                    enforcement:
                      type: rule
                      target: R001
                  - must: "`revisionHistoryLimit: 1`"
                    enforcement:
                      type: rule
                      target: R009
                """,
            )
            write_file(
                rules_file,
                """
                version: 1
                rules:
                  - id: R001
                    description: test
                    severity: error
                  - id: R009
                    description: test
                    severity: error
                """,
            )

            errors = validate_must_coverage(skill_file, mapping_file, rules_file)
            self.assertEqual([], errors)

    def test_fails_when_must_mapping_missing_entry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_file = root / "SKILL.md"
            mapping_file = root / "references" / "must-rules-map.yaml"
            rules_file = root / "references" / "rules-registry.yaml"

            write_file(
                skill_file,
                """
                ## MUST Rules (Condensed)
                - Do not use `:latest`.
                - `revisionHistoryLimit: 1`
                ## Validation Commands
                """,
            )
            write_file(
                mapping_file,
                """
                version: 1
                must_rules:
                  - must: "Do not use `:latest`."
                    enforcement:
                      type: rule
                      target: R001
                """,
            )
            write_file(
                rules_file,
                """
                version: 1
                rules:
                  - id: R001
                    description: test
                    severity: error
                  - id: R009
                    description: test
                    severity: error
                """,
            )

            errors = validate_must_coverage(skill_file, mapping_file, rules_file)
            self.assertTrue(any("missing MUST mappings:" in item for item in errors))

    def test_fails_when_mapping_targets_unknown_rule(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_file = root / "SKILL.md"
            mapping_file = root / "references" / "must-rules-map.yaml"
            rules_file = root / "references" / "rules-registry.yaml"

            write_file(
                skill_file,
                """
                ## MUST Rules (Condensed)
                - Do not use `:latest`.
                ## Validation Commands
                """,
            )
            write_file(
                mapping_file,
                """
                version: 1
                must_rules:
                  - must: "Do not use `:latest`."
                    enforcement:
                      type: rule
                      target: R999
                """,
            )
            write_file(
                rules_file,
                """
                version: 1
                rules:
                  - id: R001
                    description: test
                    severity: error
                """,
            )

            errors = validate_must_coverage(skill_file, mapping_file, rules_file)
            self.assertTrue(any("undefined rule id: R999" in item for item in errors))

    def test_main_resolves_default_paths_relative_to_skill_file(self):
        with tempfile.TemporaryDirectory() as temp_dir, tempfile.TemporaryDirectory() as cwd_dir:
            root = Path(temp_dir)
            skill_file = root / "SKILL.md"
            mapping_file = root / "references" / "must-rules-map.yaml"
            rules_file = root / "references" / "rules-registry.yaml"

            write_file(
                skill_file,
                """
                ## MUST Rules (Condensed)
                - Do not use `:latest`.
                ## Validation Commands
                """,
            )
            write_file(
                mapping_file,
                """
                version: 1
                must_rules:
                  - must: "Do not use `:latest`."
                    enforcement:
                      type: rule
                      target: R001
                """,
            )
            write_file(
                rules_file,
                """
                version: 1
                rules:
                  - id: R001
                    description: test
                    severity: error
                """,
            )

            original_cwd = Path.cwd()
            try:
                os.chdir(cwd_dir)
                exit_code = main(["--skill", str(skill_file)])
            finally:
                os.chdir(original_cwd)

            self.assertEqual(0, exit_code)


if __name__ == "__main__":
    unittest.main()
