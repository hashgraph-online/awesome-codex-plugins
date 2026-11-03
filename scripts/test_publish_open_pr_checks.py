"""Regression tests for the centralized catalog gate and contributor comments."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location(
    "awesome_codex_centralized_publisher",
    SCRIPTS / "publish-open-pr-checks-centralized.py",
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not load centralized publisher")
PUBLISHER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PUBLISHER
SPEC.loader.exec_module(PUBLISHER)


class CentralizedPublisherTests(unittest.TestCase):
    def test_centralized_scans_use_the_inclusive_75_point_minimum(self) -> None:
        root = SCRIPTS.parent
        for workflow in ("sweep-open-prs.yml", "validate-contribution.yml"):
            with self.subTest(workflow=workflow):
                text = (root / ".github/workflows" / workflow).read_text()
                self.assertIn("min_score: 75", text)
                self.assertIn("fail_on_severity: none", text)
                self.assertNotIn("min_score: 80", text)

    def setUp(self) -> None:
        self.scan_result = {
            "pr_number": 12,
            "head_sha": "a" * 40,
            "title": "Example plugin",
            "author_login": "contributor",
            "state": "scan",
            "failure_reasons": [],
            "contributions": [{"owner": "example", "repo": "plugin"}],
        }

    def test_completed_scan_meeting_score_gate_passes_with_advisories(self) -> None:
        conclusion, title, summary = PUBLISHER.check_summary(
            self.scan_result, {12: ["success"]}
        )
        self.assertEqual(conclusion, "success")
        self.assertIn("threshold passed", title)
        self.assertIn("severities are advisory", summary)

    def test_missing_or_failed_scan_does_not_pass(self) -> None:
        for jobs in ({}, {12: ["failure"]}, {12: ["success", "failure"]}):
            with self.subTest(jobs=jobs):
                conclusion, title, summary = PUBLISHER.check_summary(self.scan_result, jobs)
                self.assertEqual(conclusion, "failure")
                self.assertIn("score not established", title.lower())
                self.assertIn("at least 75/100", summary)

    def test_scan_comments_are_single_paragraphs_and_recommend_optional_source_ci(self) -> None:
        for jobs in ({12: ["success"]}, {12: ["failure"]}):
            conclusion, title, summary = PUBLISHER.check_summary(self.scan_result, jobs)
            comment = PUBLISHER.remediation_comment(
                self.scan_result, conclusion, title, summary, "https://example.test/run"
            )
            self.assertNotIn("\n", comment)
            self.assertNotIn("\\n", comment)
            self.assertTrue(comment.endswith(" " + PUBLISHER.PUBLISHER.COMMENT_MARKER))
            self.assertFalse(comment.startswith("<!--"))
            if conclusion == "failure":
                self.assertIn("recommended, not required", comment)
                self.assertIn("score is below 75", comment)
                self.assertIn("source repository does not already run the scanner", comment)
                self.assertIn(f"[scanner guide]({PUBLISHER.PUBLISHER.SCANNER_GUIDE_URL})", comment)
                self.assertIn("project's documented toolchain", comment)

    def test_no_new_entry_success_comment_does_not_claim_a_score(self) -> None:
        result = {**self.scan_result, "state": "success"}
        comment = PUBLISHER.remediation_comment(
            result,
            "success",
            "Contribution requirements passed",
            "No new Community Plugins entries require validation.",
            "https://example.test/run",
        )
        self.assertNotIn("\n", comment)
        self.assertTrue(comment.endswith(" " + PUBLISHER.PUBLISHER.COMMENT_MARKER))
        self.assertFalse(comment.startswith("<!--"))
        self.assertIn("No new Community Plugins entries", comment)
        self.assertNotIn("score threshold", comment)

    def test_catalog_failure_comment_is_single_paragraph(self) -> None:
        result = {
            **self.scan_result,
            "state": "failure",
            "failure_reasons": ["README entry is not alphabetical", "Missing repository metadata"],
        }
        comment = PUBLISHER.remediation_comment(
            result,
            "failure",
            "Catalog validation failed",
            "Catalog validation failed: README entry is not alphabetical",
            "https://example.test/run",
        )
        self.assertNotIn("\n", comment)
        self.assertNotIn("\\n", comment)
        self.assertTrue(comment.endswith(" " + PUBLISHER.PUBLISHER.COMMENT_MARKER))
        self.assertFalse(comment.startswith("<!--"))
        self.assertIn("README entry is not alphabetical", comment)

    def test_base_publisher_keeps_scanner_failure_separate_from_catalog_failure(self) -> None:
        base = PUBLISHER.PUBLISHER
        conclusion, title, summary = base.check_summary(self.scan_result, {12: ["failure"]})
        self.assertEqual(conclusion, "failure")
        self.assertIn("Centralized score not established", title)
        self.assertNotIn("Required scanner CI is missing", summary)
        comment = base.remediation_comment(
            self.scan_result, conclusion, title, summary, "https://example.test/run"
        )
        self.assertNotIn("\n", comment)
        self.assertIn("Source-repository scanner CI is optional", comment)
        self.assertIn("source repository does not already run the scanner", comment)


class OwnerHandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base = PUBLISHER.PUBLISHER
        self.scan_result = {
            "pr_number": 12,
            "head_sha": "a" * 40,
            "title": "Example plugin",
            "author_login": "contributor",
            "state": "scan",
            "failure_reasons": [],
            "contributions": [{"owner": "example", "repo": "plugin"}],
        }

    def fake_api(self, calls, comments=None):
        def fake(_repository, path, _token, *, method="GET", payload=None):
            calls.append((method, path, payload))
            if "/comments?" in path:
                return comments or []
            if path.startswith("/commits/"):
                return {"check_runs": []}
            return {}
        return fake

    def test_listing_comment_keeps_single_paragraph_verdict_then_handoff(self) -> None:
        calls = []
        with patch.object(self.base, "github_api", side_effect=self.fake_api(calls)):
            self.base.upsert_remediation_comment(
                "example/repo", self.scan_result, "success", "t", "s", "https://example.test/run", "token")

        posts = [payload["body"] for method, path, payload in calls if method == "POST"]
        self.assertEqual(len(posts), 1)
        body = posts[0]
        verdict = body.split("\n\n", 1)[0]
        self.assertNotIn("\n", verdict)
        self.assertIn(self.base.HANDOFF_HEADING, body)
        self.assertIn("https://hol.org/guard/plugins?claim=example%2Fplugin&utm_source=github&utm_medium=pr_comment"
                      "&utm_campaign=agent_handoff&utm_content=pr_open", body)
        self.assertIn("**Optional, paid:**", body)
        self.assertIn(self.base.HANDOFF_PAID_NOTE, body)
        self.assertTrue(body.endswith("\n\n" + self.base.COMMENT_MARKER))

    def test_passing_pr_without_new_listing_stays_quiet(self) -> None:
        calls = []
        with patch.object(self.base, "github_api", side_effect=self.fake_api(calls)):
            self.base.upsert_remediation_comment(
                "example/repo", {**self.scan_result, "state": "success"}, "success", "t", "s",
                "https://example.test/run", "token")

        self.assertFalse([path for method, path, _ in calls if method == "POST"])

    def test_catalog_failure_has_no_handoff(self) -> None:
        self.assertEqual(self.base.owner_handoff_section({**self.scan_result, "state": "failure"}), "")
        self.assertEqual(self.base.owner_handoff_section({**self.scan_result, "contributions": [{"owner": "a b", "repo": "x"}]}), "")

    def test_check_summary_carries_handoff_tagged_as_check_run(self) -> None:
        calls = []
        with patch.object(self.base, "github_api", side_effect=self.fake_api(calls)), \
                patch.object(self.base, "upsert_remediation_comment"):
            self.base.publish_check("example/repo", self.scan_result, {12: ["success"]}, "https://example.test/run", "token")

        summary = next(payload for method, path, payload in calls if path == "/check-runs")["output"]["summary"]
        self.assertIn(self.base.HANDOFF_HEADING, summary)
        self.assertIn("utm_medium=check_run&utm_campaign=agent_handoff&utm_content=check_summary", summary)

    def test_contributor_docs_carry_the_same_handoff(self) -> None:
        for name in ("AGENTS.md", "CONTRIBUTING.md"):
            with self.subTest(name=name):
                text = (SCRIPTS.parent / name).read_text(encoding="utf-8")
                self.assertIn(self.base.HANDOFF_HEADING, text)
                self.assertIn(self.base.HANDOFF_PAID_NOTE, text)
                self.assertIn("utm_campaign=agent_handoff", text)


if __name__ == "__main__":
    unittest.main()
