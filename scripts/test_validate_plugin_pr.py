from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


MODULE_PATH = Path(__file__).with_name("validate-plugin-pr.py")
SPEC = importlib.util.spec_from_file_location("validate_plugin_pr", MODULE_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VALIDATOR
SPEC.loader.exec_module(VALIDATOR)


class ReadmeEntryRegexTests(unittest.TestCase):
    def test_repository_urls_preserve_owner_repo_and_description_groups(self) -> None:
        for suffix in (
            "",
            "/",
            "/tree/main/plugins/example",
            "?tab=readme-ov-file#setup",
        ):
            with self.subTest(suffix=suffix):
                url = "https://github.com/example/plugin" + suffix
                entry = f"- [Example]({url}) - A useful plugin."

                match = VALIDATOR.README_ENTRY_RE.fullmatch(entry)

                self.assertIsNotNone(match)
                assert match is not None
                self.assertEqual(
                    match.groups(),
                    ("Example", url, "example", "plugin", "A useful plugin."),
                )

    def test_trailing_slash_before_query_is_not_a_new_repository(self) -> None:
        diff = "\n".join(
            (
                "diff --git a/README.md b/README.md",
                "- [Example](https://github.com/example/plugin?tab=readme) - Existing entry.",
                "+- [Example](https://github.com/example/plugin/?tab=readme) - Existing entry.",
            )
        )
        base_readme = "- [Example](https://github.com/example/plugin?tab=readme) - Existing entry."

        with patch.object(VALIDATOR, "git", side_effect=(diff, base_readme)):
            entries = VALIDATOR.get_new_readme_entries("origin/main")

        self.assertEqual(entries, [])

    def test_seen_urls_are_normalized_before_deduplication(self) -> None:
        diff = "\n".join(
            (
                "diff --git a/README.md b/README.md",
                "+- [Example](https://github.com/example/plugin?tab=readme) - First entry.",
                "+- [Example](https://github.com/example/plugin/?tab=readme) - Duplicate entry.",
            )
        )

        with patch.object(VALIDATOR, "git", side_effect=(diff, "")):
            entries = VALIDATOR.get_new_readme_entries("origin/main")

        self.assertEqual(len(entries), 1)

    def test_tree_ref_and_subpath_case_are_preserved(self) -> None:
        base_readme = (
            "- [Example](https://github.com/example/plugin/tree/Main/Plugins/Foo) "
            "- Existing entry."
        )
        diff = "\n".join(
            (
                "diff --git a/README.md b/README.md",
                "- " + base_readme,
                "+- [Example](https://github.com/example/plugin/tree/main/plugins/foo) "
                "- Updated entry.",
            )
        )

        with patch.object(VALIDATOR, "git", side_effect=(diff, base_readme)):
            entries = VALIDATOR.get_new_readme_entries("origin/main")

        self.assertEqual(len(entries), 1)


if __name__ == "__main__":
    unittest.main()
