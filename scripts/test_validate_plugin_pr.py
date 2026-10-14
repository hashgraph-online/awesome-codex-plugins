from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


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


if __name__ == "__main__":
    unittest.main()
