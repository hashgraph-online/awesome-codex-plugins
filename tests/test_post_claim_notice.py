import importlib.util
import io
import json
import os
import re
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from subprocess import CompletedProcess
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from unittest.mock import mock_open, patch

SPEC = importlib.util.spec_from_file_location(
    "post_claim_notice", Path(__file__).resolve().parents[1] / "scripts/post-claim-notice.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DeliveryRegressionTests(unittest.TestCase):
    def test_catalog_page_limit_cannot_block_a_merged_listing_notice(self):
        with patch.multiple(
            MODULE, GH_TOKEN="fixture", PR_NUMBER="993", REPO_FULL="owner/catalog",
            PR_AUTHOR="author", PR_TITLE="Add plugin",
        ), patch.object(MODULE, "has_existing_claim_comment", return_value=False), patch.object(
            MODULE, "parse_pr_diff_for_repos", return_value={"owner/plugin"}
        ), patch.object(
            MODULE, "fetch_catalog_repos",
            side_effect=MODULE.RegistryCatalogFetchError("registry catalog exceeded 100 pages"),
        ), patch(
            "builtins.open", mock_open(read_data="- [Plugin](https://github.com/owner/plugin) - Plugin")
        ), patch.object(MODULE, "post_comment", return_value=True) as post:
            self.assertEqual(MODULE.main(), 0)
            post.assert_called_once_with("author", {"owner/plugin"})


class RegistryLookupTests(unittest.TestCase):
    def setUp(self):
        self.sleep = patch.object(MODULE.time, "sleep").start()
        patch.object(MODULE.random, "uniform", return_value=0).start()
        patch.dict(MODULE.CATALOG_REPO_CACHE, clear=True).start()
        self.addCleanup(patch.stopall)

    @staticmethod
    def response(data):
        return io.BytesIO(json.dumps(data).encode())

    @staticmethod
    def http_error(code, retry_after=None):
        headers = {} if retry_after is None else {"Retry-After": retry_after}
        return HTTPError("https://registry.example/catalog", code, "failure", headers, None)

    def test_lookup_targets_exact_verified_repository_and_caches_result(self):
        data = {"items": [
            {"sourceRepo": "Owner/Plugin", "ownerVerified": True},
            {"sourceRepo": "owner/plugin-extra", "ownerVerified": True},
        ]}
        with patch.object(MODULE, "api_request", return_value=data) as fetch:
            self.assertEqual(MODULE.fetch_catalog_repos("Owner/Plugin"), {"owner/plugin"})
            self.assertEqual(MODULE.fetch_catalog_repos("owner/plugin"), {"owner/plugin"})
        fetch.assert_called_once()
        self.assertEqual(parse_qs(urlparse(fetch.call_args.args[0]).query),
                         {"q": ["owner/plugin"], "ownerVerified": ["true"], "limit": ["50"]})

    def test_vendored_repository_identity_takes_precedence(self):
        with patch.object(MODULE, "api_request", return_value={"items": [{
            "sourceRepo": "owner/catalog", "repository": "https://github.com/Author/Plugin.git",
            "ownerVerified": True,
        }]}):
            self.assertEqual(MODULE.fetch_catalog_repos("author/plugin"), {"author/plugin"})

    def test_unverified_or_incomplete_evidence_cannot_suppress_an_invitation(self):
        with patch.object(MODULE, "api_request", return_value={"items": [
            {"sourceRepo": "owner/plugin", "ownerVerified": False}, {"sourceRepo": "owner/plugin"},
        ]}):
            self.assertEqual(MODULE.fetch_catalog_repos("owner/plugin"), set())

    def test_filtered_pagination_and_rate_limit_retry_preserve_query(self):
        replies = [self.response({"items": [], "nextCursor": "50"}), self.http_error(429, "7"),
                   self.response({"items": [{"sourceRepo": "owner/plugin", "ownerVerified": True}]})]
        with patch.object(MODULE.urllib.request, "urlopen", side_effect=replies) as fetch:
            self.assertEqual(MODULE.fetch_catalog_repos("owner/plugin"), {"owner/plugin"})
        self.assertEqual(fetch.call_count, 3)
        self.assertEqual(fetch.call_args_list[-2].args[0].full_url, fetch.call_args.args[0].full_url)
        query = parse_qs(urlparse(fetch.call_args.args[0].full_url).query)
        self.assertEqual(query["q"], ["owner/plugin"])
        self.assertEqual(query["cursor"], ["50"])
        self.sleep.assert_called_once_with(7)

    def test_failed_or_incomplete_queries_are_not_cached(self):
        for replies in ([None], [{"items": [], "nextCursor": "next"}, None],
                        [{"items": [], "nextCursor": "next"}] * 2):
            with self.subTest(replies=replies), patch.object(MODULE, "api_request", side_effect=replies):
                with self.assertRaises(MODULE.RegistryCatalogFetchError):
                    MODULE.fetch_catalog_repos("owner/plugin")
            self.assertEqual(MODULE.CATALOG_REPO_CACHE, {})

    def test_search_is_bounded_even_if_the_server_ignores_the_query(self):
        pages = [{"items": [], "nextCursor": str(i)} for i in range(1, MODULE.MAX_CATALOG_PAGES + 1)]
        with patch.object(MODULE, "api_request", side_effect=pages) as fetch:
            with self.assertRaises(MODULE.RegistryCatalogFetchError):
                MODULE.fetch_catalog_repos("owner/plugin")
        self.assertEqual(fetch.call_count, MODULE.MAX_CATALOG_PAGES)
        self.assertEqual(MODULE.CATALOG_REPO_CACHE, {})

    def test_temporary_failures_exhaust_bounded_retries(self):
        for failure in (429, 500, 502, 503, 504, "network", "timeout"):
            with self.subTest(failure=failure):
                self.sleep.reset_mock()
                errors = [URLError("unavailable") if failure == "network" else
                          TimeoutError("timed out") if failure == "timeout" else
                          self.http_error(failure) for _ in range(MODULE.REGISTRY_MAX_ATTEMPTS)]
                with patch.object(MODULE.urllib.request, "urlopen", side_effect=errors):
                    with self.assertRaises(MODULE.RegistryTemporarilyUnavailable):
                        MODULE.fetch_catalog_repos("owner/plugin")
                self.assertEqual([c.args[0] for c in self.sleep.call_args_list], [2, 4, 8])

    def test_retry_after_http_date_and_invalid_header(self):
        with patch.object(MODULE, "datetime") as clock:
            clock.now.return_value = datetime(2026, 10, 24, tzinfo=timezone.utc)
            self.assertEqual(MODULE.registry_retry_delay(0, "Sat, 24 Oct 2026 00:00:12 GMT"), 12)
        self.assertEqual(MODULE.registry_retry_delay(0, "invalid"), 2)

    def test_long_retry_after_does_not_exceed_budget(self):
        with patch.object(MODULE.urllib.request, "urlopen", side_effect=self.http_error(429, "120")) as fetch:
            with self.assertRaises(MODULE.RegistryTemporarilyUnavailable):
                MODULE.fetch_catalog_repos("owner/plugin")
        fetch.assert_called_once()
        self.sleep.assert_not_called()

    def test_github_writes_are_not_retried_to_avoid_duplicate_comments(self):
        for method in ("POST", "PATCH"):
            with self.subTest(method=method), patch.object(MODULE.urllib.request, "urlopen", side_effect=self.http_error(429)) as fetch:
                self.assertIsNone(MODULE.api_request("https://api.github.com/example", method=method, data={"body": "notice"}))
                fetch.assert_called_once()
        self.sleep.assert_not_called()


class ClaimNoticeTests(unittest.TestCase):
    def setUp(self):
        patch.dict(os.environ, {}, clear=True).start()
        patch.multiple(MODULE, GH_TOKEN="fixture", PR_NUMBER="1", REPO_FULL="owner/catalog",
                       PR_AUTHOR="author", PR_TITLE="Add plugin").start()
        self.existing = patch.object(MODULE, "has_existing_claim_comment", return_value=False).start()
        patch.object(MODULE, "parse_pr_diff_for_repos", return_value={"owner/plugin"}).start()
        self.source = patch.object(MODULE, "catalog_source_repos", return_value={"owner/plugin"}).start()
        self.lookup = patch.object(MODULE, "fetch_catalog_repos", return_value=set()).start()
        self.post = patch.object(MODULE, "post_comment", return_value=True).start()
        self.update = patch.object(MODULE, "update_comment", return_value=True).start()
        self.addCleanup(patch.stopall)

    def test_unindexed_listing_gets_a_claim_link(self):
        self.assertEqual(MODULE.main(), 0)
        self.lookup.assert_called_once_with("owner/plugin")
        self.post.assert_called_once_with("author", {"owner/plugin"})

    def test_registry_outage_does_not_block_delivery(self):
        self.lookup.side_effect = MODULE.RegistryTemporarilyUnavailable("retry budget exhausted")
        self.assertEqual(MODULE.main(), 0)
        self.post.assert_called_once_with("author", {"owner/plugin"})

    def test_verified_owner_receives_a_dashboard_confirmation(self):
        self.lookup.return_value = {"owner/plugin"}
        self.assertEqual(MODULE.main(), 0)
        self.post.assert_called_once_with("author", set())

    def test_verified_owner_deferred_notice_is_replaced_with_dashboard_link(self):
        self.lookup.return_value = {"owner/plugin"}
        self.existing.return_value = {"id": 123, "deferred": True}
        self.assertEqual(MODULE.main(), 0)
        self.update.assert_called_once_with(123, "author", set())
        self.post.assert_not_called()

    def test_existing_notice_prevents_duplicate_delivery(self):
        self.existing.return_value = True
        self.assertEqual(MODULE.main(), 0)
        self.post.assert_not_called()
        self.lookup.assert_not_called()

    def test_old_pending_notice_is_updated_in_place(self):
        self.existing.return_value = {"id": 123, "deferred": True}
        self.assertEqual(MODULE.main(), 0)
        self.update.assert_called_once_with(123, "author", {"owner/plugin"})
        self.post.assert_not_called()

    def test_pending_notice_survives_a_later_title_change(self):
        self.existing.return_value = {"id": 123, "deferred": True}
        with patch.object(MODULE, "PR_TITLE", "fix: renamed contribution"):
            self.assertEqual(MODULE.main(), 0)
        self.update.assert_called_once_with(123, "author", {"owner/plugin"})

    def test_unlisted_diff_links_cannot_receive_claim_notices(self):
        self.source.return_value = {"owner/plugin-extra"}
        self.assertEqual(MODULE.main(), 0)
        self.post.assert_not_called()
        self.lookup.assert_not_called()

    def test_unreadable_catalog_is_reported_for_retry(self):
        self.source.side_effect = OSError("unavailable")
        self.assertEqual(MODULE.main(), 1)
        self.post.assert_not_called()

    def test_failed_duplicate_check_cannot_write_another_comment(self):
        self.existing.side_effect = MODULE.GitHubCommentsFetchError("unavailable")
        self.assertEqual(MODULE.main(), 1)
        self.post.assert_not_called()

    def test_failed_comment_write_is_reported_for_retry(self):
        self.post.return_value = False
        self.assertEqual(MODULE.main(), 1)


class NoticeEvidenceTests(unittest.TestCase):
    def test_source_accepts_exact_listing_links_only(self):
        readme = "\n".join([
            "- [Plugin](https://github.com/Owner/Plugin.git/tree/main) - Plugin",
            "Documentation mentions https://github.com/other/unlisted",
        ])
        with patch("builtins.open", mock_open(read_data=readme)):
            self.assertEqual(MODULE.catalog_source_repos(), {"owner/plugin"})

    def test_local_mirror_uses_trusted_upstream_identity_instead_of_folder_name(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("- [Mirror](./plugins/author/alias) - Plugin")
            manifest = root / "plugins" / "author" / "alias" / ".codex-plugin" / "plugin.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({"repository": "https://github.com/author/upstream.git"}))
            with patch.object(MODULE, "__file__", str(root / "scripts" / "post-claim-notice.py")):
                self.assertEqual(MODULE.catalog_source_repos(), {"author/upstream"})

    def test_local_listing_cannot_read_metadata_outside_the_catalog(self):
        with patch("builtins.open", mock_open(read_data="- [Bad](./plugins/../../outside) - Plugin")):
            with self.assertRaises(OSError):
                MODULE.catalog_source_repos()

    def test_manual_dispatch_requires_trusted_merged_metadata(self):
        for merged_at, expected in ((None, None), ("2026-10-26T00:00:00Z", ("Add plugin", "author"))):
            with self.subTest(merged_at=merged_at), patch.object(MODULE, "api_request", return_value={
                "merged_at": merged_at, "title": "Add plugin", "user": {"login": "author"},
            }):
                self.assertEqual(MODULE.fetch_merged_pr_metadata(), expected)

    def test_ready_notice_on_later_page_takes_precedence_over_old_pending_notice(self):
        first = [{"id": 1, "body": MODULE.MARKER + " Still syncing"}] * 100
        second = [{"id": 2, "body": MODULE.build_comment_body("author", {"owner/plugin"})}]
        with patch.object(MODULE, "api_request", side_effect=[first, second]):
            self.assertIs(MODULE.has_existing_claim_comment(), True)

    def test_comment_lookup_errors_are_not_treated_as_absence(self):
        with patch.object(MODULE, "api_request", return_value=None):
            with self.assertRaises(MODULE.GitHubCommentsFetchError):
                MODULE.has_existing_claim_comment()

    def test_notice_is_one_paragraph_with_attributed_repository_links(self):
        body = MODULE.build_comment_body("author", ["owner/second", "owner/first"])
        self.assertNotIn("\n", body)
        self.assertNotIn("\\n", body)
        self.assertIn("@author", body)
        self.assertIn("Claim your plugin", body)
        self.assertIn("Continue with GitHub", body)
        links = re.findall(r"https://hol.org/guard/plugins\?[^)]+", body)
        queries = [parse_qs(urlparse(link).query) for link in links]
        self.assertEqual([q["claim"][0] for q in queries], ["owner/first", "owner/second"])
        self.assertTrue(all(q["utm_campaign"] == ["plugin_claim"] for q in queries))
        self.assertNotIn("is now listed", body)

    def test_already_verified_notice_retains_dashboard_link(self):
        body = MODULE.build_comment_body("author")
        self.assertIn("[Open your plugin dashboard]", body)
        self.assertIn("already verified", body)
        self.assertNotIn("?claim=", body)

    def test_diff_ignores_moved_listing_lines(self):
        diff = "\n".join(["+++ b/README.md",
            "-- [Old](https://github.com/owner/existing) - Old",
            "+- [Old](https://github.com/owner/existing) - Old",
            "+- [New](https://github.com/owner/new) - New"])
        with patch.object(MODULE.subprocess, "run", return_value=CompletedProcess([], 0, stdout=diff)):
            self.assertEqual(MODULE.parse_pr_diff_for_repos(), {"owner/new"})


if __name__ == "__main__":
    unittest.main()
