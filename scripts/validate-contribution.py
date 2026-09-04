#!/usr/bin/env python3
"""Validate new Awesome Codex Plugins README contributions.

The catalog stores links to source repositories rather than plugin code.  This
validator therefore checks the contribution at the same boundary a maintainer
reviews it:

* only newly added Community Plugins entries are considered;
* each source repository is public and exposes workflow-based scanner CI; and
* the workflow is triggered by a push or pull request and invokes the HOL AI
  Plugin Scanner action.

The workflow that calls this script emits a matrix of source repositories.  A
follow-up job scans each repository with the same 80-point/high-severity gate
documented in CONTRIBUTING.md.
"""

from __future__ import annotations

import argparse
import base64
from collections import Counter
import difflib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised in minimal runners
    yaml = None

REPO_ROOT = Path(__file__).resolve().parent.parent
README_PATH = REPO_ROOT / "README.md"
REQUEST_TIMEOUT_SECONDS = 30
MAX_WORKFLOW_BYTES = 512 * 1024
USER_AGENT = "awesome-codex-plugins-contribution-validator"

README_ENTRY_RE = re.compile(
    r"^- \[([^\]]+)\]\((https://github\.com/"
    r"([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)(?:/)?(?:[?#][^)]*)?)\)\s*[-\u2013\u2014]\s*(.+)$",
    re.MULTILINE,
)


@dataclass(frozen=True)
class Contribution:
    display_name: str
    url: str
    owner: str
    repo: str
    description: str


@dataclass(frozen=True)
class OpenPullRequest:
    number: int
    title: str
    head_repository: str
    head_ref: str
    head_sha: str
    base_ref: str
    base_sha: str
    author_login: str = ""


class ValidationError(Exception):
    """A user-facing contribution validation error."""


def workflow_has_ci_trigger(document: object) -> bool:
    """Return whether a parsed workflow runs on push or pull_request."""

    if not isinstance(document, dict):
        return False

    # PyYAML's YAML 1.1 resolver can load the key ``on`` as True.
    trigger = document.get("on", document.get(True))
    if isinstance(trigger, str):
        return trigger in {"push", "pull_request"}
    if isinstance(trigger, list):
        return any(item in {"push", "pull_request"} for item in trigger)
    if isinstance(trigger, dict):
        return any(key in {"push", "pull_request"} for key in trigger)
    return False


def scanner_steps(document: object) -> list[str]:
    """Return scanner action references from parsed workflow steps."""

    if not isinstance(document, dict):
        return []
    jobs = document.get("jobs")
    if not isinstance(jobs, dict):
        return []

    references: list[str] = []
    for job in jobs.values():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps")
        if not isinstance(steps, list):
            continue
        for step in steps:
            if not isinstance(step, dict):
                continue
            uses = step.get("uses")
            if not isinstance(uses, str):
                continue
            normalized = uses.strip()
            if normalized.lower().startswith("hashgraph-online/ai-plugin-scanner-action@"):
                references.append(normalized)
    return references


def reusable_workflow_references(document: object) -> list[str]:
    """Return local reusable workflow filenames referenced by jobs."""

    if not isinstance(document, dict):
        return []
    jobs = document.get("jobs")
    if not isinstance(jobs, dict):
        return []

    references: list[str] = []
    for job in jobs.values():
        if not isinstance(job, dict):
            continue
        uses = job.get("uses")
        if not isinstance(uses, str):
            continue
        workflow_ref = uses.split("@", 1)[0].strip().replace("\\", "/")
        if not workflow_ref.startswith(".github/workflows/") and not workflow_ref.startswith(
            "./.github/workflows/"
        ):
            continue
        references.append(workflow_ref.rsplit("/", 1)[-1])
    return references


def workflow_reaches_scanner(
    name: str,
    documents: dict[str, object],
    visiting: set[str] | None = None,
) -> bool:
    """Return whether a workflow directly or indirectly invokes the scanner."""

    document = documents.get(name)
    if document is None:
        return False
    if scanner_steps(document):
        return True

    active = set() if visiting is None else set(visiting)
    if name in active:
        return False
    active.add(name)
    names_by_lower = {workflow_name.lower(): workflow_name for workflow_name in documents}
    return any(
        workflow_reaches_scanner(names_by_lower.get(reference.lower(), ""), documents, active)
        for reference in reusable_workflow_references(document)
    )


def parse_workflow_document(name: str, text: str) -> object:
    """Parse workflow YAML with a safe loader and a clear dependency error."""

    if yaml is None:
        raise ValidationError(
            "PyYAML is required to inspect source workflows; install PyYAML before running validation"
        )
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as error:
        raise ValidationError(f"{name} is not valid workflow YAML: {error}") from error


def git(*args: str) -> str:
    """Run a read-only git command in the repository and return stdout."""

    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def normalize_url(url: str) -> str:
    """Normalize a GitHub repository URL for change-set comparison."""

    return url.rstrip("/").removesuffix(".git").lower()


def current_readme_section(readme_lines: list[str], line_number: int) -> str:
    """Return the nearest level-two heading before a 1-based line number."""

    heading = ""
    for index, line in enumerate(readme_lines, start=1):
        if index > line_number:
            break
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            heading = match.group(1).strip()
    return heading


def community_plugin_line_counts(readme: str) -> Counter[str]:
    """Count exact list lines already present in the Community Plugins section."""

    counts: Counter[str] = Counter()
    heading = ""
    for line in readme.splitlines():
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            heading = match.group(1).strip()
            continue
        if heading == "Community Plugins" and line.strip().startswith("- "):
            counts[line] += 1
    return counts


def get_new_readme_entries_from_diff(diff: str, base_readme: str, head_readme: str) -> list[Contribution]:
    """Find newly added Community Plugins entries in a README diff."""

    if not diff:
        return []

    base_urls = {
        normalize_url(match.group(2))
        for match in README_ENTRY_RE.finditer(base_readme)
    }
    base_community_lines = community_plugin_line_counts(base_readme)
    head_community_lines = community_plugin_line_counts(head_readme)
    readme_lines = head_readme.splitlines()

    entries: list[Contribution] = []
    invalid_entries: list[str] = []
    seen_urls: set[str] = set()
    added_line_number = 0
    for line in diff.splitlines():
        if line.startswith("@@"):
            hunk = re.search(r"\+(\d+)", line)
            added_line_number = int(hunk.group(1)) if hunk else 0
            continue
        if line.startswith("+") and not line.startswith("+++"):
            content = line[1:]
            match = README_ENTRY_RE.match(content.strip())
            in_community_plugins = (
                current_readme_section(readme_lines, added_line_number) == "Community Plugins"
            )
            if (
                in_community_plugins
                and content.strip().startswith("- ")
                and not match
                and not (
                    base_community_lines[content] > 0
                    and head_community_lines[content] <= base_community_lines[content]
                )
            ):
                invalid_entries.append(f"line {added_line_number}: {content.strip()}")
            if match and in_community_plugins:
                url = normalize_url(match.group(2))
                if url not in base_urls and url not in seen_urls:
                    seen_urls.add(url)
                    entries.append(
                        Contribution(
                            display_name=match.group(1).strip(),
                            url=match.group(2).strip(),
                            owner=match.group(3),
                            repo=match.group(4),
                            description=match.group(5).strip(),
                        )
                    )
            added_line_number += 1
            continue
        if not line.startswith("-"):
            added_line_number += 1

    if invalid_entries:
        details = "; ".join(invalid_entries[:3])
        suffix = "" if len(invalid_entries) <= 3 else f"; and {len(invalid_entries) - 3} more"
        raise ValidationError(
            "Community Plugins entries must use "
            "`- [Plugin Name](https://github.com/<owner>/<repo>) - Description`; "
            f"could not parse {details}{suffix}"
        )

    return entries


def get_new_readme_entries(base_ref: str) -> list[Contribution]:
    """Find newly added Community Plugins entries in the local README diff."""

    diff = git("diff", base_ref, "--", "README.md")
    if not diff or not README_PATH.exists():
        return []

    base_readme = git("show", f"{base_ref}:README.md")
    head_readme = README_PATH.read_text(encoding="utf-8")
    return get_new_readme_entries_from_diff(diff, base_readme, head_readme)


def request_bytes(url: str, *, max_bytes: int = MAX_WORKFLOW_BYTES) -> bytes:
    """Fetch a bounded GitHub API/raw response."""

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
    }
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > max_bytes:
                raise ValidationError(f"response is larger than {max_bytes} bytes")
            payload = response.read(max_bytes + 1)
    except HTTPError as error:
        if error.code == 404:
            raise ValidationError("source repository or workflow directory was not found") from error
        raise ValidationError(f"GitHub returned HTTP {error.code}") from error
    except (URLError, TimeoutError, OSError) as error:
        raise ValidationError(f"could not fetch GitHub metadata: {error}") from error

    if len(payload) > max_bytes:
        raise ValidationError(f"response is larger than {max_bytes} bytes")
    return payload


def github_json(url: str) -> object:
    """Fetch a bounded GitHub API JSON response."""

    try:
        return json.loads(request_bytes(url, max_bytes=4 * 1024 * 1024).decode("utf-8"))
    except json.JSONDecodeError as error:
        raise ValidationError(f"GitHub returned invalid JSON for {url}") from error


def github_api_list(url: str) -> list[dict[str, object]]:
    """Fetch all pages from a GitHub API list endpoint."""

    values: list[dict[str, object]] = []
    page = 1
    while True:
        separator = "&" if "?" in url else "?"
        payload = github_json(f"{url}{separator}{urlencode({'per_page': 100, 'page': page})}")
        if not isinstance(payload, list):
            raise ValidationError(f"GitHub returned a non-list response for {url}")
        page_values = [item for item in payload if isinstance(item, dict)]
        values.extend(page_values)
        if len(payload) < 100:
            return values
        page += 1


def content_file(repository: str, path: str, ref: str) -> str:
    """Read a UTF-8 file from a public repository at an exact ref."""

    url = f"https://api.github.com/repos/{repository}/contents/{path}?{urlencode({'ref': ref})}"
    payload = github_json(url)
    if not isinstance(payload, dict):
        raise ValidationError(f"{repository}/{path} is not a file")
    encoded = payload.get("content")
    if not isinstance(encoded, str):
        raise ValidationError(f"GitHub did not return content for {repository}/{path}")
    try:
        return base64.b64decode(encoded, validate=False).decode("utf-8")
    except (ValueError, UnicodeDecodeError) as error:
        raise ValidationError(f"Could not decode {repository}/{path}") from error


def workflow_files(owner: str, repo: str) -> list[tuple[str, str]]:
    """Return (filename, text) pairs for a source repository's workflows."""

    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/.github/workflows"
    payload = json.loads(request_bytes(api_url).decode("utf-8"))
    if not isinstance(payload, list):
        raise ValidationError(".github/workflows is not a directory")

    files: list[tuple[str, str]] = []
    for item in payload:
        if not isinstance(item, dict) or item.get("type") != "file":
            continue
        name = str(item.get("name", ""))
        if not name.lower().endswith((".yml", ".yaml")):
            continue
        download_url = item.get("download_url")
        if not isinstance(download_url, str) or not download_url:
            continue
        text = request_bytes(download_url).decode("utf-8", errors="replace")
        files.append((name, text))
    return files


def validate_scanner_ci(contribution: Contribution) -> None:
    """Require a push/PR workflow that invokes the HOL scanner action."""

    try:
        files = workflow_files(contribution.owner, contribution.repo)
    except (ValidationError, json.JSONDecodeError) as error:
        raise ValidationError(
            f"{contribution.url} does not expose readable GitHub Actions workflows: {error}"
        ) from error

    documents: dict[str, object] = {}
    scanner_workflows: list[tuple[str, object, list[str]]] = []
    for name, text in files:
        document = parse_workflow_document(name, text)
        documents[name] = document
        references = scanner_steps(document)
        if references:
            scanner_workflows.append((name, document, references))

    if not scanner_workflows:
        raise ValidationError(
            f"{contribution.url} must invoke "
            "hashgraph-online/ai-plugin-scanner-action in .github/workflows"
        )

    triggered_scanner_workflows = [
        name
        for name, document in documents.items()
        if workflow_has_ci_trigger(document) and workflow_reaches_scanner(name, documents)
    ]
    if not triggered_scanner_workflows:
        names = ", ".join(name for name, _, _ in scanner_workflows)
        raise ValidationError(
            f"{contribution.url} scanner workflow ({names}) must run on push or pull_request "
            "or be called by a push/pull_request workflow"
        )


def list_open_pull_requests(repository: str, pull_request_number: int | None) -> list[OpenPullRequest]:
    """Return open pull requests without checking out untrusted fork code."""

    if pull_request_number is not None:
        url = f"https://api.github.com/repos/{repository}/pulls/{pull_request_number}"
        payload = github_json(url)
        payloads = [payload]
    else:
        url = f"https://api.github.com/repos/{repository}/pulls?state=open"
        payloads = github_api_list(url)

    pull_requests: list[OpenPullRequest] = []
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        number = payload.get("number")
        title = payload.get("title")
        head = payload.get("head")
        base = payload.get("base")
        if not isinstance(number, int) or not isinstance(title, str):
            continue
        if not isinstance(head, dict) or not isinstance(base, dict):
            continue
        head_repository_payload = head.get("repo")
        user_payload = payload.get("user")
        head_ref = head.get("ref")
        head_sha = head.get("sha")
        base_ref = base.get("ref")
        base_sha = base.get("sha")
        if not isinstance(head_repository_payload, dict):
            continue
        head_repository = head_repository_payload.get("full_name")
        if not isinstance(head_repository, str):
            continue
        if not isinstance(head_ref, str) or not isinstance(base_ref, str):
            continue
        if not isinstance(head_sha, str) or not isinstance(base_sha, str):
            continue
        author_login = user_payload.get("login", "") if isinstance(user_payload, dict) else ""
        if not isinstance(author_login, str):
            author_login = ""
        pull_requests.append(
            OpenPullRequest(
                number=number,
                title=title,
                head_repository=head_repository,
                head_ref=head_ref,
                head_sha=head_sha,
                base_ref=base_ref,
                base_sha=base_sha,
                author_login=author_login,
            )
        )
    return pull_requests


def entries_for_open_pull_request(repository: str, pull_request: OpenPullRequest) -> list[Contribution]:
    """Extract new Community Plugin entries from a PR's exact base/head refs."""

    head_owner = pull_request.head_repository.split("/", maxsplit=1)[0]
    compare_ref = quote(
        f"{pull_request.base_ref}...{head_owner}:{pull_request.head_ref}",
        safe=".../:",
    )
    compare_url = f"https://api.github.com/repos/{repository}/compare/{compare_ref}"
    compare_payload = github_json(compare_url)
    if not isinstance(compare_payload, dict):
        raise ValidationError("GitHub returned an invalid merge-base comparison")
    merge_base_commit = compare_payload.get("merge_base_commit")
    if not isinstance(merge_base_commit, dict) or not isinstance(merge_base_commit.get("sha"), str):
        raise ValidationError("GitHub did not return a merge base for this pull request")
    merge_base_sha = merge_base_commit["sha"]

    base_readme = content_file(repository, "README.md", merge_base_sha)
    head_readme = content_file(pull_request.head_repository, "README.md", pull_request.head_sha)
    diff = "".join(
        difflib.unified_diff(
            base_readme.splitlines(keepends=True),
            head_readme.splitlines(keepends=True),
            fromfile="README.md",
            tofile="README.md",
        )
    )
    return get_new_readme_entries_from_diff(diff, base_readme, head_readme)


def scan_open_pull_requests(
    repository: str,
    pull_request_number: int | None,
    matrix_output: Path | None,
    report_output: Path | None,
    status_output: Path | None,
) -> int:
    """Validate open PR source repositories and emit a scanner matrix/report."""

    pull_requests = list_open_pull_requests(repository, pull_request_number)
    matrix: list[dict[str, object]] = []
    report_lines = [
        "## Open contribution sweep",
        "",
        f"Repository: `{repository}`",
        f"Open pull requests checked: {len(pull_requests)}",
        "",
    ]
    failures: list[dict[str, object]] = []
    results: list[dict[str, object]] = []

    for pull_request in pull_requests:
        prefix = f"PR #{pull_request.number} — {pull_request.title}"
        try:
            entries = entries_for_open_pull_request(repository, pull_request)
        except ValidationError as error:
            failures.append({"pr_number": pull_request.number, "error": str(error)})
            results.append(
                {
                    "pr_number": pull_request.number,
                    "title": pull_request.title,
                    "head_sha": pull_request.head_sha,
                    "author_login": pull_request.author_login,
                    "state": "failure",
                    "contributions": [],
                    "failure_reasons": [str(error)],
                }
            )
            report_lines.append(f"- **{prefix}: FAIL** — {error}")
            continue

        if not entries:
            results.append(
                {
                    "pr_number": pull_request.number,
                    "title": pull_request.title,
                    "head_sha": pull_request.head_sha,
                    "author_login": pull_request.author_login,
                    "state": "success",
                    "contributions": [],
                    "failure_reasons": [],
                }
            )
            report_lines.append(f"- **{prefix}: PASS** — no new Community Plugins entries")
            continue

        report_lines.append(f"- **{prefix}**")
        scanner_contributions: list[dict[str, str]] = []
        scanner_failures: list[str] = []
        for entry in entries:
            contribution = f"{entry.owner}/{entry.repo}"
            try:
                validate_scanner_ci(entry)
            except ValidationError as error:
                failures.append(
                    {
                        "pr_number": pull_request.number,
                        "repository": contribution,
                        "error": str(error),
                    }
                )
                scanner_failures.append(f"{contribution}: {error}")
                report_lines.append(f"  - `{contribution}`: **FAIL** — {error}")
                continue

            scanner_contributions.append({"owner": entry.owner, "repo": entry.repo})
            matrix.append(
                {
                    "pr_number": pull_request.number,
                    "owner": entry.owner,
                    "repo": entry.repo,
                }
            )
            report_lines.append(f"  - `{contribution}`: scanner CI present; queued for score scan")

        results.append(
            {
                "pr_number": pull_request.number,
                "title": pull_request.title,
                "head_sha": pull_request.head_sha,
                "author_login": pull_request.author_login,
                "state": "failure" if scanner_failures else "scan",
                "contributions": scanner_contributions,
                "failure_reasons": scanner_failures,
            }
        )

    if not pull_requests:
        report_lines.append("No open pull requests found.")
    elif failures:
        report_lines.extend(
            [
                "",
                f"Scanner CI validation failures: {len(failures)}",
                "Source repositories must add the HOL AI Plugin Scanner workflow before merge.",
            ]
        )
    else:
        report_lines.extend(["", "All open contribution entries passed scanner CI validation."])

    report = "\n".join(report_lines) + "\n"
    if matrix_output:
        matrix_output.parent.mkdir(parents=True, exist_ok=True)
        matrix_output.write_text(json.dumps(matrix, separators=(",", ":")), encoding="utf-8")
    if report_output:
        report_output.parent.mkdir(parents=True, exist_ok=True)
        report_output.write_text(report, encoding="utf-8")
    if status_output:
        status_output.parent.mkdir(parents=True, exist_ok=True)
        status_output.write_text(
            json.dumps(
                {
                    "has_failures": bool(failures),
                    "failures": failures,
                    "results": results,
                },
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as summary:
            summary.write(report)

    print(report, end="")
    return 0


def write_matrix(path: Path, entries: list[Contribution]) -> None:
    """Write the scanner job matrix as compact JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    matrix = [
        {"owner": entry.owner, "repo": entry.repo}
        for entry in entries
    ]
    path.write_text(json.dumps(matrix, separators=(",", ":")), encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--open-prs",
        action="store_true",
        help="Validate open pull requests through the GitHub API without checking out fork code",
    )
    parser.add_argument(
        "--repository",
        default=os.environ.get("GITHUB_REPOSITORY", ""),
        help="owner/repository to inspect in --open-prs mode",
    )
    parser.add_argument(
        "--pr-number",
        type=int,
        help="Limit --open-prs mode to one pull request",
    )
    parser.add_argument(
        "--base-ref",
        default=os.environ.get("GITHUB_BASE_REF", "origin/main"),
        help="Git ref to compare against (default: GITHUB_BASE_REF or origin/main)",
    )
    parser.add_argument(
        "--matrix-output",
        type=Path,
        help="Write the scanner job matrix JSON to this path",
    )
    parser.add_argument(
        "--report-output",
        type=Path,
        help="Write the open-PR Markdown report to this path",
    )
    parser.add_argument(
        "--status-output",
        type=Path,
        help="Write open-PR validation status JSON to this path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.open_prs:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository):
            print("ERROR: --repository must be an owner/repository pair", file=sys.stderr)
            return 1
        return scan_open_pull_requests(
            args.repository,
            args.pr_number,
            args.matrix_output,
            args.report_output,
            args.status_output,
        )

    if not git("rev-parse", "--verify", args.base_ref):
        print(f"ERROR: base ref '{args.base_ref}' is not available", file=sys.stderr)
        return 1

    try:
        entries = get_new_readme_entries(args.base_ref)
    except ValidationError as error:
        print(f"Contribution validation failed: {error}", file=sys.stderr)
        if args.matrix_output:
            write_matrix(args.matrix_output, [])
        return 1
    if not entries:
        print("No new Community Plugins entries found; contribution checks are complete.")
        if args.matrix_output:
            write_matrix(args.matrix_output, [])
        return 0

    failures = 0
    for entry in entries:
        print(f"Checking {entry.display_name} ({entry.owner}/{entry.repo})...")
        try:
            validate_scanner_ci(entry)
        except ValidationError as error:
            failures += 1
            print(f"  FAIL: {error}", file=sys.stderr)
        else:
            print("  PASS: scanner CI is present and push/PR-triggered")

    if failures:
        print(f"\nContribution validation failed for {failures} entr{'y' if failures == 1 else 'ies'}.", file=sys.stderr)
        return 1

    print(f"\nAll {len(entries)} contribution entr{'y' if len(entries) == 1 else 'ies'} passed.")
    if args.matrix_output:
        write_matrix(args.matrix_output, entries)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
