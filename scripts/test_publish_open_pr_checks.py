"""Regression tests for the centralized catalog gate and contributor comments."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


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
            if conclusion == "failure":
                self.assertIn("recommended, not required", comment)
                self.assertIn("score is below 75", comment)
                self.assertIn("source repository does not already run the scanner", comment)

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


if __name__ == "__main__":
    unittest.main()
