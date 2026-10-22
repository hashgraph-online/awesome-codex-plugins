import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "validate_plugin_pr", Path(__file__).resolve().parents[1] / "scripts/validate-plugin-pr.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BranchAwareValidationTests(unittest.TestCase):
    def test_readme_source_ref_link_extracts_repository_and_normalizes_identity(self):
        match = MODULE.README_ENTRY_RE.match(
            "- [WTFM](https://github.com/SupportPages-io/wtfm/tree/codex-plugin) - Published bundle."
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.group(3), "SupportPages-io")
        self.assertEqual(match.group(4), "wtfm")
        self.assertEqual(match.group(5), "codex-plugin")
        self.assertEqual(match.group(6), "Published bundle.")
        self.assertEqual(
            MODULE.normalize_github_repo_url(match.group(2)),
            "https://github.com/supportpages-io/wtfm/tree/codex-plugin",
        )

    def test_remote_validation_fetches_the_linked_branch(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return b"archive"

        with patch.object(MODULE, "urlopen", return_value=Response()) as urlopen, \
                patch.object(MODULE.zipfile, "ZipFile", return_value="archive"):
            self.assertEqual(
                MODULE.fetch_repo_archive("SupportPages-io", "wtfm", "codex-plugin"),
                "archive",
            )

        self.assertEqual(
            urlopen.call_args.args[0].full_url,
            "https://github.com/SupportPages-io/wtfm/archive/refs/heads/codex-plugin.zip",
        )

    def test_new_readme_entry_preserves_source_ref_for_validation(self):
        entry_line = (
            "- [WTFM](https://github.com/SupportPages-io/wtfm/tree/codex-plugin) "
            "- Published installable bundle."
        )
        with tempfile.TemporaryDirectory() as scratch:
            readme = Path(scratch) / "README.md"
            readme.write_text(f"## Community Plugins\n{entry_line}\n")
            with patch.object(MODULE, "README_PATH", readme), patch.object(
                MODULE,
                "git",
                side_effect=[f"diff --git a/README.md b/README.md\n+{entry_line}", "## Community Plugins\n"],
            ):
                entries = MODULE.get_new_readme_entries("origin/main")

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["owner"], "SupportPages-io")
        self.assertEqual(entries[0]["repo"], "wtfm")
        self.assertEqual(entries[0]["source_ref"], "codex-plugin")
        self.assertEqual(entries[0]["description"], "Published installable bundle.")


if __name__ == "__main__":
    unittest.main()
