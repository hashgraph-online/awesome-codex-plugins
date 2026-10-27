#!/usr/bin/env python3
"""
Post a claim notice on merged PRs that add plugins to the HOL catalog source.

Merged catalog listings are enough to issue a claim link. Registry lookups only
suppress redundant invitations for repositories whose ownership is verified.
"""

import json
import os
import re
import sys
import subprocess
import random
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlencode, urlsplit

# --- Config ---
REGISTRY_API = os.environ.get("REGISTRY_API", "https://hol.org/api/v1")
REGISTRY_BROKER_API_KEY = os.environ.get("REGISTRY_BROKER_API_KEY", "")
GH_TOKEN = os.environ.get("GH_TOKEN", "")
PR_NUMBER = os.environ.get("PR_NUMBER", "")
PR_TITLE = os.environ.get("PR_TITLE", "")
PR_AUTHOR = os.environ.get("PR_AUTHOR", "")
REPO_FULL = os.environ.get("GITHUB_REPOSITORY", "")
MAX_CATALOG_PAGES = 5
MAX_COMMENT_PAGES = 20
CATALOG_REPO_CACHE = {}
REGISTRY_MAX_ATTEMPTS = 4
REGISTRY_MAX_RETRY_DELAY = 60
REGISTRY_RETRY_STATUSES = {429, 500, 502, 503, 504}
NOTICE_DEFERRED = 75

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


class RegistryCatalogFetchError(RuntimeError):
    """Raised when Registry catalog evidence is unavailable or incomplete."""


class RegistryTemporarilyUnavailable(RegistryCatalogFetchError):
    """Raised after bounded retries of a temporary Registry failure."""


class GitHubCommentsFetchError(RuntimeError):
    """Raised when existing claim comments cannot be checked completely."""


DEFERRED_NOTICE_MARKERS = (
    "Still syncing",
    "Registry sync in progress",
    "not live in the HOL Registry",
    "No action is needed yet",
)


def claim_link(repo: str) -> str:
    return (
        "https://hol.org/guard/plugins?"
        + urlencode(
            {
                "claim": repo,
                "utm_source": "github",
                "utm_medium": "pr_comment",
                "utm_campaign": "plugin_claim",
                "utm_content": "merge_notice",
            }
        )
    )


def build_comment_body(author: str, repositories=(), pending_repositories=()) -> str:
    """Invite the author to verify ownership as soon as the catalog PR merges.

    Registry indexing is not a gate. A repository merged into the catalog
    source can be claimed before its public listing finishes syncing.
    """

    claimable = sorted(set(repositories) | set(pending_repositories))
    if not claimable:
        return f"{MARKER} 🎉 Congrats @{author}, your plugin has been merged and ownership is already verified! [Open your plugin dashboard](https://hol.org/guard/plugins) to view its trust score, installs, and engagement."

    claim_links = "; ".join(
        f"[Claim your plugin `{repo}`]({claim_link(repo)})" for repo in claimable
    )

    return f'{MARKER} 🎉 Congrats @{author}, your plugin has been merged into the catalog! {claim_links}. Choose **"Continue with GitHub"** using the account that maintains the repository to verify ownership, view its trust score, and track installs and engagement. If you have already claimed it, the same link opens your plugin dashboard.'


MARKER = "<!-- hol-claim-notice -->"


def registry_retry_delay(attempt, retry_after=None):
    """Use exponential backoff with jitter and respect Retry-After when valid."""
    delay = 2 ** (attempt + 1) + random.uniform(0, 1)
    if retry_after is not None:
        try:
            seconds = int(retry_after)
        except (TypeError, ValueError):
            try:
                retry_at = parsedate_to_datetime(retry_after)
                seconds = (retry_at - datetime.now(timezone.utc)).total_seconds()
            except (TypeError, ValueError, OverflowError):
                seconds = 0
        delay = max(delay, seconds)
    return delay


def api_request(url, headers=None, method="GET", data=None, retry_registry=False):
    """Make an HTTP request and return parsed JSON."""
    req_headers = {"Accept": "application/json", "User-Agent": "hol-claim-notice/1.0"}
    if headers:
        req_headers.update(headers)
    if data is not None:
        data = json.dumps(data).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, headers=req_headers, method=method, data=data)
    if retry_registry and REGISTRY_BROKER_API_KEY:
        target = urlsplit(url)
        if (method != "GET" or target.scheme != "https" or target.netloc != "hol.org"
                or target.path != "/api/v1/plugins/catalog"):
            raise RegistryCatalogFetchError("Refusing to send the catalog key outside its read endpoint")
        # urllib does not copy unredirected headers into redirected requests.
        req.add_unredirected_header("x-api-key", REGISTRY_BROKER_API_KEY)
    attempts = REGISTRY_MAX_ATTEMPTS if retry_registry and method == "GET" else 1
    for attempt in range(attempts):
        retry_after = None
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            print(f"  HTTP {error.code} from {url}", file=sys.stderr)
            retry_after = error.headers.get("Retry-After") if error.headers else None
            error.close()
            if attempts == 1 or error.code not in REGISTRY_RETRY_STATUSES:
                return None
        except (urllib.error.URLError, TimeoutError) as error:
            print(f"  Error fetching {url}: {error}", file=sys.stderr)
            if attempts == 1:
                return None
        except Exception as error:
            print(f"  Error fetching {url}: {error}", file=sys.stderr)
            return None

        if attempt + 1 == attempts:
            raise RegistryTemporarilyUnavailable("Registry retries exhausted")
        delay = registry_retry_delay(attempt, retry_after)
        if delay > REGISTRY_MAX_RETRY_DELAY:
            raise RegistryTemporarilyUnavailable("Registry Retry-After exceeds retry budget")
        print(f"  Retrying Registry request in {delay:.1f}s ({attempt + 2}/{attempts})", file=sys.stderr)
        time.sleep(delay)


def fetch_merged_pr_metadata():
    """Load trusted metadata for a manually dispatched claim notice."""
    url = f"https://api.github.com/repos/{REPO_FULL}/pulls/{PR_NUMBER}"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    data = api_request(url, headers=headers)
    if not isinstance(data, dict):
        return None
    if not data.get("merged_at"):
        return None
    title = data.get("title")
    user = data.get("user")
    author = user.get("login") if isinstance(user, dict) else None
    if not isinstance(title, str) or not isinstance(author, str):
        return None
    return title, author


def should_skip_title(title: str) -> bool:
    """Return True if the PR title matches a non-plugin pattern."""
    # `docs: add <plugin>` is a common legitimate contribution title. Allow it
    # through the title gate, while retaining specific docs-only exclusions below.
    allow_docs_add = bool(re.match(r"^docs?:\s+add\b", title.strip(), re.IGNORECASE))
    for pattern in SKIP_PATTERNS:
        if pattern == r"^docs?:" and allow_docs_add:
            continue
        if re.search(pattern, title, re.IGNORECASE):
            return True
    return False


def fetch_catalog_repos(repository: str):
    """Look up verified ownership for one repository, never the full catalog."""
    cache_key = normalize_repo_url(repository)
    cached = CATALOG_REPO_CACHE.get(cache_key)
    if cached is not None:
        return cached

    repos = set()
    cursor = None
    seen_cursors = set()
    base_url = f"{REGISTRY_API}/plugins/catalog?" + urlencode(
        {"limit": 50, "q": cache_key, "ownerVerified": "true"}
    )

    for page_index in range(MAX_CATALOG_PAGES):
        url = base_url if not cursor else f"{base_url}&cursor={cursor}"
        data = api_request(url, retry_registry=True)
        if not isinstance(data, dict) or not isinstance(data.get("items"), list):
            raise RegistryCatalogFetchError(
                f"registry catalog page {page_index + 1} unavailable"
            )

        for plugin in data["items"]:
            if not isinstance(plugin, dict):
                continue
            repo = plugin.get("repository") or plugin.get("sourceRepo") or ""
            if not isinstance(repo, str):
                continue
            if (repo and normalize_repo_url(repo) == cache_key
                    and plugin.get("ownerVerified") is True):
                repos.add(cache_key)

        next_cursor = data.get("nextCursor")
        if not next_cursor:
            CATALOG_REPO_CACHE[cache_key] = repos
            return repos
        if not isinstance(next_cursor, str):
            raise RegistryCatalogFetchError(
                f"registry catalog page {page_index + 1} returned an invalid cursor"
            )
        if next_cursor in seen_cursors:
            raise RegistryCatalogFetchError(
                f"registry catalog repeated cursor {next_cursor!r}"
            )
        seen_cursors.add(next_cursor)
        cursor = next_cursor

    raise RegistryCatalogFetchError(
        f"registry catalog exceeded {MAX_CATALOG_PAGES} pages"
    )


def normalize_repo_url(raw: str) -> str:
    """Normalize a GitHub URL or 'owner/repo' string to lowercase 'owner/repo'.

    Strips trailing slashes, .git suffix, and extra path segments.
    """
    s = raw.strip().rstrip("/")
    s = re.sub(r"\.git$", "", s, flags=re.IGNORECASE)
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

    added_line_repos = {}
    removed_line_repos = {}
    # Match https://github.com/owner/repo on diff lines. A re-sorted README
    # line appears on both a `-` and a `+` side with the same content, so it
    # must not count as the PR adding that repository. Bodies are compared
    # case- and punctuation-insensitively so a moved line that is re-indented
    # or re-punctuated still nets, while a real addition survives an unrelated
    # removal of the same URL. Netting is keyed per repository: the removed
    # line must mention the same repo, so distinct repos whose listing text
    # differs only in punctuation (acme/foo-bar vs acme/foobar) never alias.
    repo_url_re = re.compile(
        r"https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)", re.IGNORECASE
    )

    def normalize_body(text):
        # Canonicalize repo URLs inside the body so .git suffixes, trailing
        # slashes, and host casing do not defeat the move comparison.
        text = repo_url_re.sub(lambda m: " repo/" + normalize_repo_url(m.group(1)), text)
        return re.sub(r"[^a-z0-9]+", "", text.lower())

    current_file = None
    for line in diff.split("\n"):
        if line.startswith("+++ "):
            path = line[4:].strip()
            current_file = path[2:] if path.startswith("b/") else path
            continue
        if line.startswith("--- "):
            continue
        is_added = line.startswith("+")
        is_removed = line.startswith("-")
        if not is_added and not is_removed:
            continue
        body = normalize_body(line[1:])
        repos = {normalize_repo_url(m) for m in repo_url_re.findall(line)}
        # Skip hashgraph-online repos (our own)
        repos = {repo for repo in repos if not repo.startswith("hashgraph-online/")}
        # Netting is scoped per file: a removal in a vendored or unrelated
        # file must not suppress a genuine catalog README addition.
        if is_removed:
            for repo in repos:
                removed_line_repos.setdefault((repo, current_file), set()).add(body)
            continue
        for repo in repos:
            added_line_repos.setdefault((repo, current_file), set()).add(body)

    return {
        repo
        for (repo, filename), bodies in added_line_repos.items()
        if bodies - removed_line_repos.get((repo, filename), set())
    }


def catalog_source_repos():
    """Read repository identities from listings in the trusted base checkout."""
    root = Path(__file__).resolve().parents[1]
    with open(root / "README.md", encoding="utf-8") as readme:
        content = readme.read()
    links = re.findall(
        r"^\s*-\s+\[[^\]]+\]\((https://github\.com/|\./plugins/)"
        r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)",
        content, re.MULTILINE | re.IGNORECASE,
    )
    repos = set()
    for prefix, repo in links:
        if prefix.lower().startswith("https://"):
            repos.add(normalize_repo_url(repo))
            continue
        manifest_path = (root / "plugins" / repo / ".codex-plugin" / "plugin.json").resolve()
        if not manifest_path.is_relative_to((root / "plugins").resolve()):
            raise OSError("Local plugin listing points outside the plugin catalog")
        try:
            with open(manifest_path, encoding="utf-8") as manifest_file:
                manifest = json.load(manifest_file)
        except (ValueError, TypeError) as error:
            raise OSError(f"Invalid local plugin metadata for {repo}") from error
        upstream = manifest.get("repository") if isinstance(manifest, dict) else None
        if not isinstance(upstream, str) or not re.fullmatch(
            r"(?:https://github\.com/)?[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?",
            upstream, re.IGNORECASE,
        ):
            raise OSError(f"Local plugin listing has no GitHub repository identity: {repo}")
        repos.add(normalize_repo_url(upstream))
    return repos


def has_existing_claim_comment():
    """Check if the PR already has a claim-notice or manual claim comment."""
    headers = {"Authorization": f"token {GH_TOKEN}"}
    deferred_notice = None
    for page in range(1, MAX_COMMENT_PAGES + 1):
        url = (
            f"https://api.github.com/repos/{REPO_FULL}/issues/{PR_NUMBER}/comments"
            f"?per_page=100&page={page}"
        )
        comments = api_request(url, headers=headers)
        if not isinstance(comments, list):
            raise GitHubCommentsFetchError(
                f"comments page {page} is unavailable"
            )
        for comment in comments:
            if not isinstance(comment, dict):
                continue
            body = comment.get("body") or ""
            if MARKER in body:
                if any(marker in body for marker in DEFERRED_NOTICE_MARKERS):
                    deferred_notice = {"id": comment.get("id"), "deferred": True}
                    continue
                return True
            # Also detect manual claim comments posted before automation
            if "Claim your plugin" in body and "hol.org/guard/plugins" in body:
                return True
        if len(comments) < 100:
            return deferred_notice or False

    raise GitHubCommentsFetchError(
        f"comments exceeded {MAX_COMMENT_PAGES} pages"
    )


def post_comment(author: str, repositories=(), pending_repositories=()):
    """Post the claim notice comment on the PR, tagging the author."""
    url = f"https://api.github.com/repos/{REPO_FULL}/issues/{PR_NUMBER}/comments"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    body = build_comment_body(author, repositories, pending_repositories)
    result = api_request(url, headers=headers, method="POST", data={"body": body})
    return result is not None


def update_comment(comment_id, author: str, repositories=()) -> bool:
    """Replace a deferred sync notice with a claim link."""
    if not isinstance(comment_id, int):
        return False
    url = f"https://api.github.com/repos/{REPO_FULL}/issues/comments/{comment_id}"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    body = build_comment_body(author, repositories)
    result = api_request(url, headers=headers, method="PATCH", data={"body": body})
    return result is not None


def main():
    global PR_AUTHOR, PR_TITLE

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

    if os.environ.get("VERIFY_MERGED_PR") == "true":
        metadata = fetch_merged_pr_metadata()
        if metadata is None:
            print("Error: PR metadata is unavailable or the PR is not merged", file=sys.stderr)
            return 1
        PR_TITLE, PR_AUTHOR = metadata

    print(f'PR #{PR_NUMBER}: "{PR_TITLE}" by @{PR_AUTHOR}')

    if PR_AUTHOR in ("kantorcodes", "github-actions[bot]"):
        print("  Skipping: bot/owner PR")
        return 0

    # 2. Check for existing claim comment. A deferred "still syncing"
    # notice is replaced once we know which repositories to claim.
    existing_notice = False
    try:
        existing_notice = has_existing_claim_comment()
        if existing_notice is True:
            print("  Skipping: claim notice already posted")
            return 0
    except GitHubCommentsFetchError as error:
        print(f"  Existing claim comment check failed: {error}", file=sys.stderr)
        return 1

    # Recover an existing deferred notice even if its PR title was later edited.
    if not existing_notice and should_skip_title(PR_TITLE):
        print("  Skipping: non-plugin PR title pattern")
        return 0

    # 3. Parse PR diff for GitHub repo URLs
    try:
        pr_repos = parse_pr_diff_for_repos()
    except subprocess.CalledProcessError as e:
        print(f"  Failed to get PR diff (exit {e.returncode}): {e.stderr}", file=sys.stderr)
        return 1
    except subprocess.TimeoutExpired:
        print("  Failed to get PR diff: timed out", file=sys.stderr)
        return 1

    if not pr_repos:
        print("  Skipping: no GitHub repo URLs found in PR diff")
        return 0

    print(f"  Found repos in diff: {', '.join(pr_repos)}")

    # Only invite repositories present in the trusted, merged catalog source.
    try:
        matched = pr_repos & catalog_source_repos()
    except OSError as error:
        print(f"  Could not read merged catalog source: {error}", file=sys.stderr)
        return 1
    if not matched:
        print("  Skipping: none of the PR repos are listed in the merged catalog source")
        return 0

    # Ownership is enforced by the claim flow. This optional query only avoids
    # redundant invitations; unavailable Registry evidence must not drop notices.
    already_verified = set()
    for repo in sorted(matched):
        try:
            already_verified |= fetch_catalog_repos(repo)
        except RegistryCatalogFetchError as error:
            print(f"::warning::Owner verification lookup unavailable for {repo}: {error}; including its claim/dashboard link.")

    claimable_repos = matched - already_verified
    if already_verified:
        print(f"  Already verified: {', '.join(sorted(already_verified))}")

    if not claimable_repos:
        if isinstance(existing_notice, dict) and existing_notice.get("deferred"):
            print("  Clearing deferred notice; repositories are already verified")
            if update_comment(existing_notice.get("id"), PR_AUTHOR, set()):
                print("  ✅ Deferred notice cleared")
                return 0
            print("  ❌ Failed to clear deferred notice")
            return 1
        print("  Posting verified-owner dashboard notice...")
        if post_comment(PR_AUTHOR, set()):
            print("  ✅ Dashboard notice posted successfully")
            return 0
        print("  ❌ Failed to post dashboard notice")
        return 1

    # 7. Post or replace the comment. Catalog-source repos are claimable
    # before the public Registry listing finishes indexing.
    if isinstance(existing_notice, dict) and existing_notice.get("deferred"):
        print("  Replacing deferred claim notice...")
        if update_comment(existing_notice.get("id"), PR_AUTHOR, claimable_repos):
            print("  ✅ Comment updated successfully")
            return 0
        print("  ❌ Failed to update comment")
        return 1

    print("  Posting claim notice comment...")
    if post_comment(PR_AUTHOR, claimable_repos):
        print("  ✅ Comment posted successfully")
        return 0

    print("  ❌ Failed to post comment")
    return 1


if __name__ == "__main__":
    result = main()
    sys.exit(0 if result == NOTICE_DEFERRED else result)
