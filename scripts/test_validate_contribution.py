from __future__ import annotations

import difflib
import importlib.util
from pathlib import Path
import sys
import unittest


MODULE_PATH = Path(__file__).with_name("validate-contribution.py")
SPEC = importlib.util.spec_from_file_location("validate_contribution", MODULE_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VALIDATOR
SPEC.loader.exec_module(VALIDATOR)


def diff(base: str, head: str) -> str:
    return "".join(
        difflib.unified_diff(
            base.splitlines(keepends=True),
            head.splitlines(keepends=True),
            fromfile="README.md",
            tofile="README.md",
        )
    )


class ExistingLocalEntryMoveTests(unittest.TestCase):
    def test_exact_existing_local_entry_can_move_within_community_plugins(self) -> None:
        local = "- [Local Plugin](./plugins/local) - Local mirror.\n"
        external = "- [External](https://github.com/example/external) - External plugin.\n"
        base = "## Community Plugins\n\n" + local + external
        head = "## Community Plugins\n\n" + external + local

        self.assertEqual(
            VALIDATOR.get_new_readme_entries_from_diff(diff(base, head), base, head),
            [],
        )

    def test_duplicate_existing_local_entry_is_rejected(self) -> None:
        local = "- [Local Plugin](./plugins/local) - Local mirror.\n"
        base = "## Community Plugins\n\n" + local
        head = "## Community Plugins\n\n" + local + local

        with self.assertRaises(VALIDATOR.ValidationError):
            VALIDATOR.get_new_readme_entries_from_diff(diff(base, head), base, head)

    def test_line_copied_from_another_section_is_rejected(self) -> None:
        local = "- [Local Plugin](./plugins/local) - Local mirror.\n"
        base = "## Official Plugins\n\n" + local + "\n## Community Plugins\n"
        head = base + "\n" + local

        with self.assertRaises(VALIDATOR.ValidationError):
            VALIDATOR.get_new_readme_entries_from_diff(diff(base, head), base, head)


if __name__ == "__main__":
    unittest.main()
