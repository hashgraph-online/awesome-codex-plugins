#!/usr/bin/env python3
"""Publish open-PR checks for the centralized catalog scanner policy.

Catalog-format and discovery failures remain blocking. Centralized scanner job
status is reported separately because the maintainer merge policy is based on
the numeric scanner score, not the action conclusion alone.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


PUBLISHER_PATH = Path(__file__).with_name("publish-open-pr-checks.py")
SPEC = importlib.util.spec_from_file_location("awesome_codex_publisher", PUBLISHER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"could not load {PUBLISHER_PATH}")
PUBLISHER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PUBLISHER
SPEC.loader.exec_module(PUBLISHER)


def check_summary(result: dict[str, object], scanner_jobs: dict[int, list[str]]) -> tuple[str, str, str]:
    number = result.get("pr_number")
    state = result.get("state")
    reasons = result.get("failure_reasons")
    if not isinstance(number, int) or not isinstance(state, str):
        raise RuntimeError("validator returned an invalid PR result")

    if state == "success":
        return (
            "success",
            "Contribution requirements passed",
            "No new Community Plugins entries require validation in this pull request.",
        )

    if state == "failure":
        failure_lines = reasons if isinstance(reasons, list) else []
        details = "; ".join(item for item in failure_lines if isinstance(item, str))
        return (
            "failure",
            "Catalog validation failed",
            PUBLISHER.one_paragraph(
                f"Catalog validation failed: {details or 'the catalog change could not be validated against the pull request source.'}"
            ),
        )

    if state == "scan":
        jobs = scanner_jobs.get(number, [])
        if jobs and all(conclusion == "success" for conclusion in jobs):
            return (
                "success",
                "Centralized score threshold passed",
                f"All {len(jobs)} centralized scanner job(s) met the score threshold of 75/100; finding severities are advisory.",
            )
        job_details = ", ".join(jobs) if jobs else "no scanner job conclusion was recorded"
        return (
            "failure",
            "Centralized score not established",
            f"The centralized scan did not establish a score of at least 75/100 ({job_details}); keep the contribution blocked until a passing score is available.",
        )

    raise RuntimeError(f"unknown validator result state: {state}")


def remediation_comment(
    result: dict[str, object],
    conclusion: str,
    check_title: str,
    summary: str,
    run_url: str,
) -> str:
    marker = PUBLISHER.COMMENT_MARKER
    if conclusion == "success":
        if result.get("state") == "scan":
            message = "Contribution gate passed. The centralized score threshold of 75/100 was met; finding severities are advisory."
        else:
            message = "Contribution gate passed. No new Community Plugins entries require validation in this pull request."
        return PUBLISHER.one_paragraph(
            f"{marker} {message} No action is required. [Latest sweep]({run_url})."
        )

    reasons = result.get("failure_reasons")
    failure_lines = [item for item in reasons if isinstance(item, str)] if isinstance(reasons, list) else []
    details = " ".join(failure_lines) if failure_lines else summary
    if result.get("state") == "scan":
        guidance = "Resolve the scan failure and rerun the centralized scan; listing requires a completed score of at least 75/100."
        guidance += " If the completed score is below 75/100 and your source repository does not already run the scanner, source-repository scanner CI is recommended, not required: use the SHA-pinned workflow in the scanner guide, reproduce locally, run the same pinned scanner in CI, fix or document rule-level findings, link the source run, rerun the catalog scan, and request review."
        return PUBLISHER.one_paragraph(
            f"{marker} {details} {guidance} Source-repository scanner CI is optional. [Latest sweep]({run_url})."
        )
    return PUBLISHER.one_paragraph(
        f"{marker} The catalog change could not be validated: {details} Fix the catalog format/source discovery problem and push the correction. [Latest sweep]({run_url})."
    )


PUBLISHER.check_summary = check_summary
PUBLISHER.remediation_comment = remediation_comment


if __name__ == "__main__":
    raise SystemExit(PUBLISHER.main())
