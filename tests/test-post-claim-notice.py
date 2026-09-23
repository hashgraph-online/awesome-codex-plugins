import importlib.util
import unittest
from pathlib import Path
from unittest.mock import mock_open, patch

SPEC = importlib.util.spec_from_file_location(
    "post_claim_notice", Path(__file__).resolve().parents[1] / "scripts/post-claim-notice.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ClaimNoticeTests(unittest.TestCase):
    def test_pending_repository_notice_does_not_claim_registry_is_ready(self):
        body = MODULE.build_comment_body("author", registry_ready=False)
        self.assertIn("Registry sync in progress", body)
        self.assertIn("No action is needed from you right now", body)
        self.assertNotIn("is now listed in the", body)
        self.assertNotIn('click **"Verify ownership"**', body)

    def test_live_repository_notice_retains_claim_steps(self):
        body = MODULE.build_comment_body("author", registry_ready=True)
        self.assertIn("is now listed in the", body)
        self.assertIn('click **"Verify ownership"**', body)

    def test_readme_only_repository_posts_pending_notice(self):
        with patch.multiple(
            MODULE,
            GH_TOKEN="fixture",
            PR_NUMBER="1",
            REPO_FULL="owner/catalog",
            PR_AUTHOR="author",
            PR_TITLE="Add plugin",
        ), patch.object(
            MODULE, "has_existing_claim_comment", return_value=False
        ), patch.object(
            MODULE, "parse_pr_diff_for_repos", return_value={"owner/pending"}
        ), patch.object(
            MODULE, "fetch_catalog_repos", return_value=set()
        ), patch(
            "builtins.open", mock_open(read_data="https://github.com/owner/pending")
        ), patch.object(MODULE, "post_comment", return_value=True) as post:
            self.assertEqual(MODULE.main(), 0)
            post.assert_called_once_with("author", registry_ready=False)

    def test_live_repository_posts_claim_ready_notice(self):
        with patch.multiple(
            MODULE,
            GH_TOKEN="fixture",
            PR_NUMBER="1",
            REPO_FULL="owner/catalog",
            PR_AUTHOR="author",
            PR_TITLE="Add plugin",
        ), patch.object(
            MODULE, "has_existing_claim_comment", return_value=False
        ), patch.object(
            MODULE, "parse_pr_diff_for_repos", return_value={"owner/live"}
        ), patch.object(
            MODULE, "fetch_catalog_repos", side_effect=[{"owner/live"}, set()]
        ), patch.object(MODULE, "post_comment", return_value=True) as post:
            self.assertEqual(MODULE.main(), 0)
            post.assert_called_once_with("author", registry_ready=True)


if __name__ == "__main__":
    unittest.main()
