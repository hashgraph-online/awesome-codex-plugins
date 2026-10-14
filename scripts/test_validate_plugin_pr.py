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
    def test_standard_github_repository_entry(self) -> None:
        entry = "- [BringYour](https://github.com/unitedideas/bringyour-mcp) - Read-only project migration audit."

        match = VALIDATOR.README_ENTRY_RE.match(entry)

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.groups(), (
            "BringYour",
            "https://github.com/unitedideas/bringyour-mcp",
            "unitedideas",
            "bringyour-mcp",
            "Read-only project migration audit.",
        ))

    def test_tree_url_keeps_owner_and_repository_groups(self) -> None:
        entry = "- [Plugin](https://github.com/example/repo/tree/main/plugins/demo) – A plugin bundle."

        match = VALIDATOR.README_ENTRY_RE.match(entry)

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.group(3, 4, 5), ("example", "repo", "A plugin bundle."))


if __name__ == "__main__":
    unittest.main()
