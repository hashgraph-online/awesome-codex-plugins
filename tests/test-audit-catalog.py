import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("audit_catalog", ROOT / "scripts/audit-catalog.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class AuditCatalogTests(unittest.TestCase):
    def test_reads_only_community_plugin_entries(self):
        validator = type("Validator", (), {
            "README_ENTRY_RE": __import__("re").compile(
                r"^- \[([^\]]+)\]\((https://github\.com/([^/]+)/([^/?#)]+))\)\s*-\s*(.+)"
            )
        })
        readme = """## Contents
- [Index](https://github.com/example/index) - navigation

## Community Plugins
### Tools & Integrations
- [Example](https://github.com/example/plugin) - plugin
"""
        entries = MODULE.read_entries(readme, validator)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].subsection, "Tools & Integrations")

    def test_source_repo_url_removes_tree_ref(self):
        self.assertEqual(
            MODULE.source_repo_url("https://github.com/example/plugin/tree/main"),
            "https://github.com/example/plugin",
        )

    def test_report_lists_only_confirmed_findings(self):
        result = MODULE.Result(
            "Example", "https://github.com/example/plugin", "example", "plugin",
            "Tools", 12, "dead-source", error="Source repository is unreachable",
        )
        report = MODULE.report([result])
        self.assertIn("Confirmed findings", report)
        self.assertIn("dead-source", report)


if __name__ == "__main__":
    unittest.main()
