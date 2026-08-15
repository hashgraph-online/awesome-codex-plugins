#!/usr/bin/env python3
"""Publish the result of an open-PR sweep on each pull request head commit."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

API_ROOT = "https://api.github.com"
CHECK_NAME = "Open Codex Plugin Contribution Gate"
COMMENT_MARKER = "<!-- awesome-codex-plugins-contribution-gate -->"
USER_AGENT = "awesome-codex-plugins-open-pr-sweep"
REQUEST_TIMEOUT_SECONDS = 30
SCAN_JOB_RE = re.compile(r"Scan PR (?:#(\d+) source|\((\d+),)")
GITHUB_LOGIN_RE = re.compile(r"^[A-Za-z0-9-]{1,39}$")


def github_api(repository: str, path: str, token: str, *, method: str = "GET", payload: object | None = None) -> object:
    """Call the GitHub REST API with a bounded, JSON-only request."""

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": USER_AGENT,
    }
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request = Request(
        f"{API_ROOT}/repos/{repository}{path}",
        headers=headers,
        method=method,
        data=data,
    )
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace").strip()
        suffix = f": {detail}" if detail else ""
        raise RuntimeError(f"GitHub API {method} {path} failed: HTTP {error.code}{suffix}") from error
    except (URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"GitHub API {method} {path} failed: {error}") from error


def scan_conclusions(repository: str, run_id: str, token: str) -> dict[int, list[str]]:
    """Return scanner job conclusions grouped by pull request number."""

    conclusions: dict[int, list[str]] = {}
    page = 1
    while True:
        payload = github_api(repository, f"/actions/runs/{run_id}/jobs?per_page=100&page={page}", token)
        if not isinstance(payload, dict):
            raise RuntimeError("GitHub returned an invalid jobs response")
        jobs = payload.get("jobs")
        if not isinstance(jobs, list):
            raise RuntimeError("GitHub returned no jobs list")
        for job in jobs:
            if not isinstance(job, dict):
                continue
            name = job.get("name")
            conclusion = job.get("conclusion")
            if not isinstance(name, str) or not isinstance(conclusion, str):
                continue
            match = SCAN_JOB_RE.search(name)
            if match:
                number = match.group(1) or match.group(2)
                conclusions.setdefault(int(number), []).append(conclusion)
        if len(jobs) < 100:
            return conclusions
        page += 1


def check_summary(result: dict[str, object], scanner_jobs: dict[int, list[str]]) -> tuple[str, str, str]:
    """Map validator/scan output to a check conclusion, title, and summary."""

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
        details = "\n".join(f"- {item}" for item in failure_lines if isinstance(item, str))
        return (
            "failure",
            "Contribution requirements failed",
            "Required scanner CI is missing or could not be validated.\n\n" + details,
        )

    if state == "scan":
        jobs = scanner_jobs.get(number, [])
        if jobs and all(conclusion == "success" for conclusion in jobs):
            return (
                "success",
                "Contribution scan passed",
                f"All {len(jobs)} source-repository scanner job(s) passed the contribution gate.",
            )
        job_details = ", ".join(jobs) if jobs else "no scanner job was recorded"
        return (
            "failure",
            "Contribution scan failed",
            f"One or more source-repository scanner jobs did not pass: {job_details}.",
        )

    raise RuntimeError(f"unknown validator result state: {state}")


def list_issue_comments(repository: str, number: int, token: str) -> list[dict[str, object]]:
    """Return all issue comments for a pull request."""

    comments: list[dict[str, object]] = []
    page = 1
    while True:
        payload = github_api(
            repository,
            f"/issues/{number}/comments?per_page=100&page={page}",
            token,
        )
        if not isinstance(payload, list):
            raise RuntimeError(f"GitHub returned an invalid comments response for PR #{number}")
        page_comments = [item for item in payload if isinstance(item, dict)]
        comments.extend(page_comments)
        if len(payload) < 100:
            return comments
        page += 1


def remediation_comment(
    result: dict[str, object],
    conclusion: str,
    check_title: str,
    summary: str,
    run_url: str,
) -> str:
    """Build an idempotent contributor-facing remediation comment."""

    author_login = result.get("author_login")
    mention = f"@{author_login}" if isinstance(author_login, str) and GITHUB_LOGIN_RE.fullmatch(author_login) else "the contributor"
    if conclusion == "success":
        return (
            f"{COMMENT_MARKER}\n\n"
            f"✅ **Contribution gate passed.** {mention}, no action is required.\n\n"
            f"The previous contribution-gate failure is resolved. "
            f"[View the latest sweep]({run_url})."
        )

    if result.get("state") == "failure":
        guidance = (
            "1. Add a workflow under `.github/workflows/` in the linked source repository.\n"
            "2. Trigger it on both `push` and `pull_request`, and invoke "
            "`hashgraph-online/ai-plugin-scanner-action`.\n"
            "3. Configure `plugin_dir: \".\"`, `mode: scan`, `min_score: 80`, and "
            "`fail_on_severity: high`.\n"
            "4. Keep `.codex-plugin/plugin.json`, `README.md`, `SECURITY.md`, "
            "`LICENSE`, and a dependency lockfile in the source repository."
        )
    else:
        guidance = (
            "1. Run `pipx run plugin-scanner lint .`.\n"
            "2. Run `pipx run plugin-scanner verify . --format text`.\n"
            "3. Fix all critical/high findings and reach a score of at least 80.\n"
            "4. Confirm the source repository workflow passes, then push the fixes "
            "and rerun the workflow."
        )

    return f"""{COMMENT_MARKER}

{mention} — this pull request needs updates before it can be merged.

### {check_title}
{summary}

### How to fix it
{guidance}

See the repository's [contribution requirements](https://github.com/hashgraph-online/awesome-codex-plugins/blob/main/CONTRIBUTING.md) and [scanner guide](https://github.com/hashgraph-online/awesome-codex-plugins/blob/main/SCANNER_GUIDE.md).

After pushing the changes, this check and comment will update automatically: {run_url}
"""


def upsert_remediation_comment(
    repository: str,
    result: dict[str, object],
    conclusion: str,
    check_title: str,
    summary: str,
    run_url: str,
    token: str,
) -> None:
    """Create or update the single contribution-gate comment for a PR."""

    number = result.get("pr_number")
    if not isinstance(number, int):
        raise RuntimeError("validator returned an invalid PR number")
    comments = list_issue_comments(repository, number, token)
    existing = next(
        (
            comment
            for comment in comments
            if isinstance(comment.get("body"), str) and COMMENT_MARKER in comment["body"]
        ),
        None,
    )
    if conclusion == "success" and existing is None:
        return

    body = remediation_comment(result, conclusion, check_title, summary, run_url)
    if existing is not None and isinstance(existing.get("id"), int):
        github_api(
            repository,
            f"/issues/comments/{existing['id']}",
            token,
            method="PATCH",
            payload={"body": body},
        )
        print(f"Updated contribution-gate comment for PR #{number}")
        return

    github_api(
        repository,
        f"/issues/{number}/comments",
        token,
        method="POST",
        payload={"body": body},
    )
    print(f"Posted contribution-gate comment for PR #{number}")


def publish_check(
    repository: str,
    result: dict[str, object],
    scanner_jobs: dict[int, list[str]],
    run_url: str,
    token: str,
) -> None:
    """Create or update the check run for one pull request head commit."""

    head_sha = result.get("head_sha")
    number = result.get("pr_number")
    title = result.get("title")
    if not isinstance(head_sha, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", head_sha):
        raise RuntimeError(f"PR #{number} has an invalid head SHA")
    if not isinstance(number, int) or not isinstance(title, str):
        raise RuntimeError("validator returned an invalid PR identity")

    conclusion, check_title, summary = check_summary(result, scanner_jobs)
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    payload = {
        "name": CHECK_NAME,
        "head_sha": head_sha,
        "status": "completed",
        "conclusion": conclusion,
        "started_at": now,
        "completed_at": now,
        "details_url": run_url,
        "output": {
            "title": check_title,
            "summary": f"PR #{number} — {title}\n\n{summary}",
        },
    }
    update_payload = {key: value for key, value in payload.items() if key != "head_sha"}

    existing = github_api(
        repository,
        f"/commits/{quote(head_sha, safe='')}/check-runs?check_name={quote(CHECK_NAME)}&per_page=100",
        token,
    )
    check_runs = existing.get("check_runs", []) if isinstance(existing, dict) else []
    matching = [
        item for item in check_runs if isinstance(item, dict) and item.get("name") == CHECK_NAME
    ]
    if matching and isinstance(matching[-1].get("id"), int):
        github_api(
            repository,
            f"/check-runs/{matching[-1]['id']}",
            token,
            method="PATCH",
            payload=update_payload,
        )
    else:
        github_api(repository, "/check-runs", token, method="POST", payload=payload)
    print(f"Published {CHECK_NAME} for PR #{number}: {conclusion}")
    upsert_remediation_comment(repository, result, conclusion, check_title, summary, run_url, token)


def main() -> int:
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    run_id = os.environ.get("GITHUB_RUN_ID", "").strip()
    run_url = os.environ.get("SWEEP_RUN_URL", "").strip()
    results_json = os.environ.get("OPEN_PR_RESULTS", "[]")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        print("ERROR: GITHUB_REPOSITORY must be an owner/repository pair", file=sys.stderr)
        return 1
    if not token or not run_id or not run_url:
        print("ERROR: GITHUB_TOKEN, GITHUB_RUN_ID, and SWEEP_RUN_URL are required", file=sys.stderr)
        return 1
    try:
        results = json.loads(results_json)
        if not isinstance(results, list):
            raise RuntimeError("OPEN_PR_RESULTS must be a JSON array")
        scanner_jobs = scan_conclusions(repository, run_id, token)
        for result in results:
            if not isinstance(result, dict):
                raise RuntimeError("validator returned a non-object PR result")
            publish_check(repository, result, scanner_jobs, run_url, token)
    except (RuntimeError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
