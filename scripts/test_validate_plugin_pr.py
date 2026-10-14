from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location(
    "validate_plugin_pr", Path(__file__).with_name("validate-plugin-pr.py")
)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class ReadmeEntryTests(unittest.TestCase):
    def test_repository_and_nested_plugin_urls(self) -> None:
        for suffix in ("", "/tree/main/plugins/example", "?tab=readme-ov-file#setup"):
            with self.subTest(suffix=suffix):
                url = "https://github.com/example/plugin" + suffix
                match = VALIDATOR.README_ENTRY_RE.fullmatch(
                    f"- [Example]({url}) - A useful plugin."
                )
                self.assertIsNotNone(match)
                self.assertEqual(
                    match.groups(),
                    ("Example", url, "example", "plugin", "A useful plugin."),
                )


if __name__ == "__main__":
    unittest.main()
