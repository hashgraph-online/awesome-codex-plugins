#!/usr/bin/env python3
"""
Post a "claim your plugin" comment on merged PRs that add plugins present in the
HOL registry but not yet owner-verified.

Triggers via GitHub Actions on pull_request closed (merged).
Checks the HOL registry catalog API for matching repos, then posts a comment
with claim instructions if the plugin hasn't been claimed yet.
"""

import json
import os
import re
import sys
import subprocess
import urllib.request
import urllib.error

# --- Config ---
REGISTRY_API = os.environ.get("REGISTRY_API", "https://hol.org/registry/api/v1")
GH_TOKEN = os.environ.get("GH_TOKEN", "")
PR_NUMBER = os.environ.get("PR_NUMBER", "")
PR_TITLE = os.environ.get("PR_TITLE", "")
PR_AUTHOR = os.environ.get("PR_AUTHOR", "")
REPO_FULL = os.environ.get("GITHUB_REPOSITORY", "")

# Skip titles that aren't new plugin additions
SKIP_PATTERNS = [
    r"^docs?:",
    r"^fix\b",
    r"^ci\b",
    r"^chore\b",
    r"^refactor\b",
    r"^test\b",
    r"^build\b",
    r"Add icon for",
    r"Add .* icon",
    r"Add .* marketplace icon",
    r"For praxis, add marketplace icon",
    r"Update .*(listing|plugin owner|description|to v|trust signals)",
    r"Sync ",
    r"#\d+ Fix ",
    r"Fix install_url",
    r"Fix Casefile README",
    r"Canvas-Apps-Plugin-Codex - Update",
    r"docs: reframe scanner",
    r"docs: add PANews",
    r"fix\(registry\)",
    r"fix\(readme\)",
    r"fix\(plugins\)",
    r"feat: Make HOL Plugin Scanner",
    r"feat: publish curated marketplace",
    r"feat: add HOL Guard Plugin",
    r"ci\(sync\)",
    r"ci\(workflows\)",
    r"Add HOL Guard scanner",
]

def build_comment_body(author: str) -> str:
    """Build the claim notice comment body, tagging the PR author."""
    return f"""<!-- hol-claim-notice -->
🎉 Hey @{author}, your plugin has been merged and is now listed in the [HOL Registry](https://hol.org/registry/plugins)!

## Claim your plugin

As the author, you can verify ownership of your plugin to unlock:

- **Owner-verified badge** on your plugin's registry listing
- **Trust score** visibility and analytics for your plugin
- **Direct claim link** to share with your community
- **Dashboard access** at [hol.org/guard/plugins](https://hol.org/guard/plugins) to track installs, trust, and engagement

### How to claim

1. Visit **[hol.org/guard/plugins](https://hol.org/guard/plugins)**
2. Find your plugin and click **"Verify ownership"**
3. Sign in with GitHub — we only request `read:user`, `user:email`, and `read:org` (no write access to your repos)
4. We verify you own the repository, and your plugin gets the ✅ owner-verified badge

The whole process takes under 30 seconds. No need to add any secrets or tokens to your repo — verification is done entirely through GitHub OAuth.

If you have any questions, feel free to ask here or reach out at [support@hol.org](mailto:support@hol.org)."""

MARKER = "<!-- hol-claim-notice -->"


def api_request(url, headers=None, method="GET", data=None):
    """Make an HTTP request and return parsed JSON."""
    req_headers = {"Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    if data is not None:
        data = json.dumps(data).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, headers=req_headers, method=method, data=data)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  HTTP {e.code} from {url}: {body[:200]}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  Error fetching {url}: {e}", file=sys.stderr)
        return None


def should_skip_title(title: str) -> bool:
    """Return True if the PR title matches a non-plugin pattern."""
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, title, re.IGNORECASE):
            return True
    return False


def fetch_catalog_repos(owner_verified: bool = False):
    """Fetch repos from the registry catalog, optionally filtered by owner verification.

    Returns a set of lowercase 'owner/repo' strings.
    """
    repos = set()
    cursor = None
    base_url = f"{REGISTRY_API}/plugins/catalog?limit=50"
    if owner_verified:
        base_url += "&ownerVerified=true"
    url = base_url
    for _ in range(10):
        if cursor:
            url = f"{base_url}&cursor={cursor}"
        data = api_request(url)
        if not data or "items" not in data:
            break
        for plugin in data["items"]:
            repo = plugin.get("sourceRepo") or plugin.get("repository") or ""
            repo = repo.replace("https://github.com/", "").strip()
            if repo:
                repos.add(repo.lower())
        cursor = data.get("nextCursor")
        if not cursor:
            break
    return repos


def normalize_repo_url(raw: str) -> str:
    """Normalize a GitHub URL or 'owner/repo' string to lowercase 'owner/repo'.

    Strips trailing slashes, .git suffix, and extra path segments.
    """
    s = raw.strip().rstrip("/")
    if s.endswith(".git"):
        s = s[:-4]
    # If it's a full URL, extract owner/repo
    match = re.match(r"https?://github\.com/([^/]+/[^/]+)", s, re.IGNORECASE)
    if match:
        s = match.group(1)
    else:
        # Handle bare 'owner/repo/extra/path' — take first two segments
        parts = s.split("/")
        if len(parts) >= 2:
            s = f"{parts[0]}/{parts[1]}"
    return s.lower()


def parse_pr_diff_for_repos():
    """Get the PR diff and extract GitHub repo URLs from added lines."""
    result = subprocess.run(
        ["gh", "pr", "diff", PR_NUMBER, "--repo", REPO_FULL],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "GH_TOKEN": GH_TOKEN},
        check=True,
    )
    diff = result.stdout

    repos = set()
    # Match https://github.com/owner/repo in added lines (starting with +)
    for line in diff.split("\n"):
        if not line.startswith("+"):
            continue
        matches = re.findall(r"https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)", line)
        for match in matches:
            normalized = normalize_repo_url(match)
            # Skip hashgraph-online repos (our own)
            if not normalized.startswith("hashgraph-online/"):
                repos.add(normalized)

    return repos


def has_existing_claim_comment():
    """Check if the PR already has a claim-notice comment."""
    url = f"https://api.github.com/repos/{REPO_FULL}/issues/{PR_NUMBER}/comments"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    comments = api_request(url, headers=headers)
    if not isinstance(comments, list):
        return False
    for comment in comments:
        body = comment.get("body") or ""
        if MARKER in body:
            return True
    return False


def post_comment(author: str):
    """Post the claim notice comment on the PR, tagging the author."""
    url = f"https://api.github.com/repos/{REPO_FULL}/issues/{PR_NUMBER}/comments"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    body = build_comment_body(author)
    result = api_request(url, headers=headers, method="POST", data={"body": body})
    return result is not None


def main():
    # Validate required environment variables
    missing = []
    if not GH_TOKEN:
        missing.append("GH_TOKEN")
    if not PR_NUMBER:
        missing.append("PR_NUMBER")
    if not PR_AUTHOR:
        missing.append("PR_AUTHOR")
    if not REPO_FULL:
        missing.append("GITHUB_REPOSITORY")
    if missing:
        print(f"Error: missing required environment variables: {', '.join(missing)}", file=sys.stderr)
        return 1

    print(f'PR #{PR_NUMBER}: "{PR_TITLE}" by @{PR_AUTHOR}')

    # 1. Skip non-plugin PRs
    if should_skip_title(PR_TITLE):
        print("  Skipping: non-plugin PR title pattern")
        return 0

    if PR_AUTHOR in ("kantorcodes", "github-actions[bot]"):
        print("  Skipping: bot/owner PR")
        return 0

    # 2. Check for existing claim comment
    if has_existing_claim_comment():
        print("  Skipping: claim notice already posted")
        return 0

    # 3. Parse PR diff for GitHub repo URLs
    try:
        pr_repos = parse_pr_diff_for_repos()
    except subprocess.CalledProcessError as e:
        print(f"  Failed to get PR diff (exit {e.returncode}): {e.stderr}", file=sys.stderr)
        return 0
    except subprocess.TimeoutExpired:
        print("  Failed to get PR diff: timed out", file=sys.stderr)
        return 0

    if not pr_repos:
        print("  Skipping: no GitHub repo URLs found in PR diff")
        return 0

    print(f"  Found repos in diff: {', '.join(pr_repos)}")

    # 4. Fetch all registry plugins
    print("  Fetching registry catalog...")
    registry_repos = fetch_catalog_repos(owner_verified=False)
    print(f"  Registry has {len(registry_repos)} plugins")

    # 5. Check which PR repos are in the registry
    matched = pr_repos & registry_repos
    if not matched:
        print("  Skipping: none of the PR repos are in the registry")
        return 0

    print(f"  Matched in registry: {', '.join(matched)}")

    # 6. Check if already owner-verified
    print("  Checking owner verification status...")
    verified_repos = fetch_catalog_repos(owner_verified=True)
    already_verified = matched & verified_repos
    if already_verified and len(already_verified) == len(matched):
        print("  Skipping: all matched repos already owner-verified")
        return 0

    if already_verified:
        print(f"  Some already verified: {', '.join(already_verified)}")

    # 7. Post the comment
    print("  Posting claim notice comment...")
    if post_comment(PR_AUTHOR):
        print("  ✅ Comment posted successfully")
        return 0
    else:
        print("  ❌ Failed to post comment")
        return 1


if __name__ == "__main__":
    sys.exit(main())
