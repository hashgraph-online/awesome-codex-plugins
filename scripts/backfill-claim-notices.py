#!/usr/bin/env python3
"""Retry claim notices for recent merges after registry ingestion completes."""

import datetime as dt
import json
import os
import subprocess
import sys


def main():
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not repo:
        print("GITHUB_REPOSITORY is required", file=sys.stderr)
        return 1
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=7)
    result = subprocess.run(
        ["gh", "pr", "list", "--repo", repo, "--state", "merged", "--limit", "100",
         "--json", "number,title,author,mergedAt"],
        check=True, capture_output=True, text=True,
    )
    failures = 0
    for pr in json.loads(result.stdout):
        merged_at = dt.datetime.fromisoformat(pr["mergedAt"].replace("Z", "+00:00"))
        if merged_at < cutoff:
            continue
        env = {**os.environ, "PR_NUMBER": str(pr["number"]),
               "PR_TITLE": pr["title"], "PR_AUTHOR": pr["author"]["login"]}
        outcome = subprocess.run([sys.executable, "scripts/post-claim-notice.py"], env=env)
        if outcome.returncode != 0:
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
