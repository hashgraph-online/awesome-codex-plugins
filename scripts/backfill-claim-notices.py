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


def changes_plugin_files(repo, number):
    page = 1
    while True:
        files = gh_json("api", f"repos/{repo}/pulls/{number}/files?per_page=100&page={page}")
        if any(item["filename"] == "README.md" or item["filename"].startswith("plugins/") for item in files):
            return True
        if len(files) < 100:
            return False
        page += 1


def main():
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not repo:
        print("GITHUB_REPOSITORY is required", file=sys.stderr)
        return 1
    failures = 0
    pending = []
    page = 1
    while True:
        issues = gh_json(
            "api", f"repos/{repo}/issues?labels={PENDING_LABEL}&state=closed&per_page=100&page={page}"
        )
        pending.extend(issue for issue in issues if "pull_request" in issue)
        if len(issues) < 100:
            break
        page += 1
    for issue in pending:
        number = issue["number"]
        pr = gh_json(
            "pr", "view", str(number), "--repo", repo,
            "--json", "mergedAt,title,author",
        )
        if not pr.get("mergedAt") or not changes_plugin_files(repo, number):
            continue
        env = {**os.environ, "PENDING_RETRY": "1", "PR_NUMBER": str(number),
               "PR_TITLE": pr["title"], "PR_AUTHOR": pr["author"]["login"]}
        outcome = subprocess.run([sys.executable, "scripts/post-claim-notice.py"], env=env)
        if outcome.returncode != 0:
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
