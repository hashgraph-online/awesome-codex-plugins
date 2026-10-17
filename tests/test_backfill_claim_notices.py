import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "backfill_claim_notices", Path(__file__).resolve().parents[1] / "scripts/backfill-claim-notices.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BackfillClaimNoticeTests(unittest.TestCase):
    def test_plugin_file_can_be_on_later_changed_files_page(self):
        page_one = [{"filename": "docs/notes.md"}] * 100
        with patch.object(MODULE, "gh_json", side_effect=[page_one, [{"filename": "README.md"}]]) as gh:
            self.assertTrue(MODULE.changes_plugin_files("owner/catalog", 1))
            self.assertEqual(gh.call_count, 2)

    def test_pending_pages_are_collected_before_labels_can_be_removed(self):
        first = [{"number": n, "pull_request": {}} for n in range(1, 101)]
        seen_second_page = False

        def fake_gh(*args):
            nonlocal seen_second_page
            if args[0] == "api" and "/issues?" in args[1]:
                if args[1].endswith("page=1"):
                    return first
                seen_second_page = True
                return [{"number": 101, "pull_request": {}}]
            if args[0] == "pr":
                author = None if args[2] == "1" else {"login": "author"}
                return {"mergedAt": "2026-09-01T00:00:00Z", "title": "Add plugin", "author": author}
            return [{"filename": "README.md"}]

        def fake_run(*args, **kwargs):
            self.assertTrue(seen_second_page)
            return type("Result", (), {"returncode": 0})()

        with patch.dict(MODULE.os.environ, {"GITHUB_REPOSITORY": "owner/catalog"}), patch.object(
            MODULE, "gh_json", side_effect=fake_gh
        ), patch.object(MODULE.subprocess, "run", side_effect=fake_run) as run:
            self.assertEqual(MODULE.main(), 0)
            self.assertEqual(run.call_count, 100)
            self.assertTrue(all(call.args[0][:3] == ["gh", "workflow", "run"] for call in run.call_args_list))
            self.assertNotIn("pr_number=1", [arg for call in run.call_args_list for arg in call.args[0]])


if __name__ == "__main__":
    unittest.main()
