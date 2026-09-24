#!/usr/bin/env python3
"""
Post a "claim your plugin" comment on merged PRs that add plugins present in the
HOL registry but not yet owner-verified.

Triggers via GitHub Actions on pull_request closed (merged).
Checks the HOL registry catalog API for matching repos, then posts a comment
with claim instructions. If a newly merged repository is present only in the
catalog source and has not reached the live Registry yet, the notice says it is
still syncing and does not send the creator into a claim flow that cannot work.
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
PENDING_RETRY = os.environ.get("PENDING_RETRY") == "1"
PENDING_LABEL = "registry-claim-pending"

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


def build_comment_body(author: str, repositories=(), registry_ready: bool = True) -> str:
    """Invite the author to claim as soon as the catalog pull request merges."""
    del registry_ready
    from urllib.parse import urlencode

    repos = sorted({repo for repo in repositories if repo})
    if repos:
        claim_links = "\n".join(
            "- [Verify ownership of `{repo}`](https://hol.org/guard/plugins?{query})".format(
                repo=repo,
                query=urlencode(
                    {
                        "claim": repo,
                        "utm_source": "github",
                        "utm_medium": "pr_comment",
                        "utm_campaign": "plugin_claim",
                        "utm_content": "merge_notice",
                    }
                ),
            )
            for repo in repos
        )
    else:
        claim_links = "[Open the plugin dashboard](https://hol.org/guard/plugins)"

    return f"""<!-- hol-claim-notice -->
Hey @{author}, your plugin is merged into the HOL catalog and ready to claim.

## Claim your plugin

{claim_links}

Open the link and choose **"Continue with GitHub"**. Use the GitHub account that maintains the repository. HOL requests only `read:user` and `user:email`. It does not request write access to the repository.

After verification, the listing gets an owner-verified badge, and the plugin dashboard shows its trust score, installs, and engagement."""


MARKER = "<!-- hol-claim-notice -->"


def api_request(url, headers=None, method="GET", data=None):
    """Make an HTTP request and return parsed JSON."""
    req_headers = {"Accept": "application/json", "User-Agent": "hol-claim-notice/1.0"}
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
    seen_cursors = set()
    while True:
        url = f"{base_url}&cursor={cursor}" if cursor else base_url
        data = api_request(url)
        if not data or "items" not in data:
            raise RuntimeError("Registry catalog is unavailable; claim notice will be retried")
        for plugin in data["items"]:
            # Vendored marketplace plugins have a catalog sourceRepo of
            # awesome-codex-plugins; ownership belongs to the author repo.
            repo = plugin.get("repository") or plugin.get("sourceRepo") or ""
            repo = normalize_repo_url(repo) if repo else ""
            if repo:
                repos.add(repo.lower())
        cursor = data.get("nextCursor")
        if not cursor:
            break
        if cursor in seen_cursors:
            raise RuntimeError("Registry catalog cursor repeated; claim notice will be retried")
        seen_cursors.add(cursor)
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


def readme_contains_repo(readme: str, repo: str) -> bool:
    """Match owner/repo as its own token, not as a prefix of a longer name."""
    pattern = (
        r"(?<![A-Za-z0-9_.-])"
        + re.escape(repo.lower())
        + r"(?![A-Za-z0-9_.-])"
    )
    return re.search(pattern, readme.lower()) is not None


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
    """Check if the PR already has a claim-notice or manual claim comment."""
    headers = {"Authorization": f"token {GH_TOKEN}"}
    page = 1
    state = None
    while True:
        url = f"https://api.github.com/repos/{REPO_FULL}/issues/{PR_NUMBER}/comments?per_page=100&page={page}"
        comments = api_request(url, headers=headers)
        if not isinstance(comments, list):
            raise RuntimeError("Cannot check existing claim notices; retry later")
        for comment in comments:
            body = comment.get("body") or ""
            if MARKER in body:
                if (
                    "Registry sync in progress" in body
                    or "Still syncing" in body
                    or "not live in the HOL Registry" in body
                ):
                    state = "pending"
                else:
                    return "ready"
            # Also detect manual claim comments posted before automation
            if "Claim your plugin" in body and "hol.org/guard/plugins" in body:
                return "ready"
        if len(comments) < 100:
            break
        page += 1
    return state


def set_pending_label(pending: bool):
    """Keep an indefinite retry queue on the merged PR itself."""
    subprocess.run(
        ["gh", "pr", "edit", PR_NUMBER, "--repo", REPO_FULL,
         "--add-label" if pending else "--remove-label", PENDING_LABEL],
        check=True, timeout=30, env={**os.environ, "GH_TOKEN": GH_TOKEN},
    )


def post_comment(author: str, repositories=(), registry_ready: bool = True):
    """Post the claim notice comment on the PR, tagging the author."""
    url = f"https://api.github.com/repos/{REPO_FULL}/issues/{PR_NUMBER}/comments"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    body = build_comment_body(author, repositories, registry_ready=registry_ready)
    result = api_request(url, headers=headers, method="POST", data={"body": body})
    return result is not None


def main():
    # Validate required environment variables
    missing = []
    if not GH_TOKEN:
        missing.append("GH_TOKEN")
    if not PR_NUMBER:
        missing.append("PR_NUMBER")
    if not REPO_FULL:
        missing.append("GITHUB_REPOSITORY")
    if missing:
        print(f"Error: missing required environment variables: {', '.join(missing)}", file=sys.stderr)
        return 1

    print(f'PR #{PR_NUMBER}: "{PR_TITLE}" by @{PR_AUTHOR}')

    # 1. Skip non-plugin PRs
    if not PENDING_RETRY and should_skip_title(PR_TITLE):
        print("  Skipping: non-plugin PR title pattern")
        return 0

    if PR_AUTHOR in ("kantorcodes", "github-actions[bot]"):
        print("  Skipping: bot/owner PR")
        return 0

    # 2. Parse PR diff for GitHub repo URLs
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

    set_pending_label(True)
    existing_notice = has_existing_claim_comment()
    if existing_notice and existing_notice != "pending":
        set_pending_label(False)
        print("  Skipping: claim-ready notice already posted")
        return 0

    # 4. Fetch all registry plugins
    print("  Fetching registry catalog...")
    registry_repos = fetch_catalog_repos(owner_verified=False)
    print(f"  Registry has {len(registry_repos)} plugins")

    # 5. Check which PR repos are in the live registry. If they only appear in
    # the merged README source, keep the notice informational until ingestion finishes.
    matched = set(pr_repos & registry_repos)
    missing = pr_repos - matched
    if missing:
        print("  Checking README for repositories the Registry has not indexed...")
        readme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "README.md")
        if os.path.exists(readme_path):
            readme_content = open(readme_path, encoding="utf-8").read().lower()
            readme_matched = {
                repo for repo in missing if readme_contains_repo(readme_content, repo)
            }
            if readme_matched:
                print(f"  Claimable from catalog source: {', '.join(sorted(readme_matched))}")
                matched |= readme_matched
    registry_ready = bool(pr_repos & registry_repos)
    if not matched:
        set_pending_label(False)
        print("  Skipping: none of the PR repos are in the registry or README")
        return 0

    if registry_ready:
        print(f"  Matched in registry: {', '.join(matched)}")
    else:
        print(f"  Pending registry sync: {', '.join(matched)}")

    already_verified = set()
    # 6. Check if already owner-verified only when the repository is actually live.
    if registry_ready:
        print("  Checking owner verification status...")
        verified_repos = fetch_catalog_repos(owner_verified=True)
        already_verified = matched & verified_repos
        if already_verified and len(already_verified) == len(matched):
            set_pending_label(False)
            print("  Skipping: all matched repos already owner-verified")
            return 0

        if already_verified:
            print(f"  Some already verified: {', '.join(already_verified)}")

    # A deferred sync notice is replaced by a claim link. Registry indexing
    # is not required before the author can verify ownership.
    claimable = matched - already_verified
    if not claimable:
        set_pending_label(False)
        print("  Skipping: all matched repos already owner-verified")
        return 0

    print("  Posting claim notice comment...")
    if post_comment(PR_AUTHOR, claimable, registry_ready=registry_ready):
        if registry_ready:
            set_pending_label(False)
        print("  ✅ Comment posted successfully")
        return 0
    else:
        print("  ❌ Failed to post comment")
        return 1


if __name__ == "__main__":
    sys.exit(main())
