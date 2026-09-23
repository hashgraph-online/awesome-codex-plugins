#!/usr/bin/env python3
"""Retry pending claim notices until their registry entries are live."""

import json
import os
import subprocess
import sys

PENDING_LABEL = "registry-claim-pending"


def gh_json(*args):
    result = subprocess.run(["gh", *args], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def main():
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not repo:
        print("GITHUB_REPOSITORY is required", file=sys.stderr)
        return 1
    failures = 0
    page = 1
    while True:
        issues = gh_json(
            "api", f"repos/{repo}/issues?labels={PENDING_LABEL}&state=closed&per_page=100&page={page}"
        )
        for issue in issues:
            if "pull_request" not in issue:
                continue
            pr = gh_json(
                "pr", "view", str(issue["number"]), "--repo", repo,
                "--json", "mergedAt,title,author,files",
            )
            if not pr.get("mergedAt"):
                continue
            paths = {item["path"] for item in pr.get("files", [])}
            if "README.md" not in paths and not any(path.startswith("plugins/") for path in paths):
                continue
            env = {**os.environ, "PENDING_RETRY": "1", "PR_NUMBER": str(issue["number"]),
                   "PR_TITLE": pr["title"], "PR_AUTHOR": pr["author"]["login"]}
            outcome = subprocess.run([sys.executable, "scripts/post-claim-notice.py"], env=env)
            if outcome.returncode != 0:
                failures += 1
        if len(issues) < 100:
            break
        page += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
