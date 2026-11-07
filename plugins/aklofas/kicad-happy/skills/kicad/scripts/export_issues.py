#!/usr/bin/env python3
"""Export analysis findings to GitHub Issues.

Reads analyzer JSON output and creates GitHub Issues via the ``gh`` CLI.
Dry-run by default — previews issues to stdout. Use ``--create`` to push.
Each issue body starts with a hidden ``finding_id`` marker and an open issue
carrying that marker is never exported again; issues without a marker are
matched once by exact title.

Usage:
    export_issues.py schematic.json --repo owner/repo
    export_issues.py schematic.json --repo owner/repo --severity warning
    export_issues.py schematic.json --repo owner/repo --rule-id RG-001,CP-001
    export_issues.py schematic.json --repo owner/repo --create

Python 3.10+ stdlib only. Requires ``gh`` CLI (https://cli.github.com/).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

from diff_engine import _canonical, _fid_stem, finding_key
from kicad_core.executables import find_executable

# ---------------------------------------------------------------------------
# Severity ranking: lower number = higher priority
# ---------------------------------------------------------------------------

_SEV_RANK: dict[str, int] = {
    "critical": 0,
    "high": 0,
    "error": 0,
    "warning": 1,
    "medium": 1,
    "info": 2,
    "low": 2,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _norm_severity(s: str) -> str:
    """Normalize a severity string to one of: high / warning / info."""
    s = (s or "").lower().strip()
    if s in ("critical", "high", "error"):
        return "high"
    if s in ("warning", "medium", "warn"):
        return "warning"
    return "info"


# One page of `gh issue list`; a full page may be truncated, which is refused.
LIST_LIMIT = 1000

_MARKER_RE = re.compile(
    r"^<!-- kicad-happy:finding_id=(.*?)(?: key=([0-9a-f]{16}))? -->$"
)


class IssueListError(Exception):
    """The open-issue listing is unavailable or may be incomplete."""


def _escape_html_comment(text: str) -> str:
    """Make text safe to place in a body without opening or closing a comment."""
    return text.replace("<!--", "&lt;!--").replace("-->", "--&gt;")


def _inert(text: str) -> str:
    """Escape comment delimiters and keep @mentions from notifying anyone."""
    return _escape_html_comment(text).replace("@", "@\u200b")


def finding_marker(finding: dict) -> str:
    """Return the hidden marker line for a finding, or '' when it has no id.

    The line carries the analyzer's id and a content key. A positional id
    (``X#1``) follows list order and an unnamed-net id follows wiring edits,
    so for those the key is what identifies the finding across runs.
    """
    fid = finding.get("finding_id")
    if not isinstance(fid, str) or not fid.strip():
        return ""
    fid = _escape_html_comment(" ".join(fid.split()))
    content = finding_key(finding, positional=True)
    key = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
    return f"<!-- kicad-happy:finding_id={fid} key={key} -->"


def parse_marker(line: str) -> "tuple[str, str | None] | None":
    """(finding id, content key or None) from a marker line, else None."""
    m = _MARKER_RE.match(line.strip())
    return (m.group(1), m.group(2)) if m else None


def marker_id(body: "str | None") -> "tuple[str, str | None] | None":
    """The marker in an issue body's first line, else None.

    Only the first line counts: the exporter writes the marker there and
    escapes comment delimiters in everything it interpolates.
    """
    first = (body or "").lstrip("\ufeff").split("\n", 1)[0]
    return parse_marker(first)


def positional_stems(findings: "list[dict]") -> set:
    """Id stems that follow list order in this run, as diff_engine.match_findings finds them.

    A stem is positional when two findings share it or any member carries a
    ``#N`` suffix; the unsuffixed member of such a group is positional too.
    """
    counts: dict[str, int] = {}
    positional: set = set()
    for f in findings:
        fid = f.get("finding_id")
        if isinstance(fid, str) and fid:
            stem = _fid_stem(fid)
            counts[stem] = counts.get(stem, 0) + 1
            if stem != fid:
                positional.add(stem)
    positional.update(stem for stem, n in counts.items() if n > 1)
    return positional


def _sig(finding: dict) -> str:
    return json.dumps(finding, sort_keys=True, default=str)


def _distinct(findings: "list[dict]") -> "list[dict]":
    """The findings with exact duplicates (the same object content) dropped."""
    seen: set = set()
    unique = []
    for f in findings:
        sig = _sig(f)
        if sig not in seen:
            seen.add(sig)
            unique.append(f)
    return unique


def load_findings(path: str) -> list[dict]:
    """Load an analyzer JSON file and return findings that have a rule_id."""
    if not os.path.isfile(path):
        raise SystemExit(f"error: file not found: {path!r}")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError, RecursionError) as exc:
        raise SystemExit(f"error: cannot read {path!r}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"error: {path!r} is not a JSON object")

    raw = data.get("findings", [])
    if not isinstance(raw, list):
        raise SystemExit(
            f"error: 'findings' key in {path!r} is not a list"
        )
    return [f for f in raw if isinstance(f, dict) and f.get("rule_id")]


def filter_findings(
    findings: list[dict],
    severity: "str | None",
    rule_ids: "list[str] | None",
) -> list[dict]:
    """Filter findings by severity threshold and/or explicit rule ID list.

    ``severity`` is the *minimum* severity — all findings at that level or
    more severe are included.  ``rule_ids`` is an exact-match whitelist (any
    case).
    """
    result = findings

    if severity:
        threshold_rank = _SEV_RANK.get(_norm_severity(severity), 2)
        result = [
            f for f in result
            if _SEV_RANK.get(_norm_severity(f.get("severity", "info")), 2)
            <= threshold_rank
        ]

    if rule_ids:
        upper = {r.upper() for r in rule_ids}
        result = [
            f for f in result
            if (f.get("rule_id") or "").upper() in upper
        ]

    return result


def format_issue_title(finding: dict, inert: bool = True) -> str:
    """Build an issue title: ``[{rule_id}] {summary}``.

    If the finding has exactly one component and its reference is not already
    mentioned in the summary, it is appended in parentheses.
    """
    rule_id: str = finding.get("rule_id", "")
    summary: str = (finding.get("summary") or "").strip()
    title = f"[{rule_id}] {summary}"

    components: list = finding.get("components") or []
    if len(components) == 1:
        ref = ""
        comp = components[0]
        if isinstance(comp, dict):
            ref = comp.get("ref") or comp.get("reference") or comp.get("name") or ""
        elif isinstance(comp, str):
            ref = comp
        if ref and ref not in summary:
            title = f"{title} ({ref})"

    return _inert(title) if inert else title


def format_issue_body(finding: dict) -> str:
    """Build a structured markdown body for a GitHub Issue.

    Sections included (in order):
      - Metadata table (Rule, Severity, Confidence, Evidence, Category, Detector)
      - ## Summary
      - ## Description
      - ## Components  (omitted if empty)
      - ## Nets        (omitted if empty)
      - ## Recommendation  (omitted if empty)
      - Footer attribution line
    """
    esc = _inert
    rule_id = esc(str(finding.get("rule_id", "")))
    severity = _norm_severity(finding.get("severity", "info"))
    confidence = esc(str(finding.get("confidence", "")))
    evidence = esc(str(finding.get("evidence_source", "")))
    category = esc(str(finding.get("category", "")))
    detector = esc(str(finding.get("detector", "")))

    lines: list[str] = []

    marker = finding_marker(finding)
    if marker:
        lines.append(marker)
        lines.append("")

    # --- Metadata table ---
    lines.append("| Field | Value |")
    lines.append("|-------|-------|")
    lines.append(f"| **Rule** | `{rule_id}` |")
    lines.append(f"| **Severity** | {severity} |")
    if confidence:
        lines.append(f"| **Confidence** | {confidence} |")
    if evidence:
        lines.append(f"| **Evidence** | {evidence} |")
    if category:
        lines.append(f"| **Category** | {category} |")
    if detector:
        lines.append(f"| **Detector** | `{detector}` |")
    lines.append("")

    # --- Summary ---
    summary = esc((finding.get("summary") or "").strip())
    if summary:
        lines.append("## Summary")
        lines.append("")
        lines.append(summary)
        lines.append("")

    # --- Description ---
    description = esc((finding.get("description") or "").strip())
    if description:
        lines.append("## Description")
        lines.append("")
        lines.append(description)
        lines.append("")

    # --- Components ---
    components: list = finding.get("components") or []
    if components:
        lines.append("## Components")
        lines.append("")
        for comp in components:
            if isinstance(comp, dict):
                ref = esc(str(comp.get("ref") or comp.get("reference") or comp.get("name") or ""))
                val = esc(str(comp.get("value") or ""))
                fp = esc(str(comp.get("footprint") or ""))
                parts = [f"`{ref}`" if ref else ""]
                if val:
                    parts.append(val)
                if fp:
                    parts.append(f"({fp})")
                lines.append(f"- {' '.join(p for p in parts if p)}")
            elif isinstance(comp, str):
                lines.append(f"- `{esc(comp)}`")
        lines.append("")

    # --- Nets ---
    nets: list = finding.get("nets") or []
    if nets:
        lines.append("## Nets")
        lines.append("")
        for net in nets:
            if isinstance(net, str):
                lines.append(f"- `{esc(net)}`")
            elif isinstance(net, dict):
                name = net.get("name") or net.get("net") or str(net)
                lines.append(f"- `{esc(str(name))}`")
        lines.append("")

    # --- Recommendation ---
    recommendation = esc((finding.get("recommendation") or "").strip())
    if recommendation:
        lines.append("## Recommendation")
        lines.append("")
        lines.append(recommendation)
        lines.append("")

    # --- Footer ---
    lines.append(
        "*Generated by [kicad-happy](https://github.com/aklofas/kicad-happy)*"
    )

    return "\n".join(lines)


def issue_labels(finding: dict, extra_labels: "list[str]") -> list[str]:
    """Return the label list for a finding.

    Always includes:
      - ``kicad-happy``
      - ``kicad-happy:{rule_id}``
      - ``severity:{severity}``
      - ``confidence:{confidence}``  (if present)
      - ``evidence:{evidence_source}``  (if present)

    Plus any caller-supplied extra labels.
    """
    rule_id = finding.get("rule_id", "")
    severity = _norm_severity(finding.get("severity", "info"))
    labels = [
        "kicad-happy",
        f"kicad-happy:{rule_id}",
        f"severity:{severity}",
    ]
    confidence = finding.get("confidence", "")
    if confidence:
        labels.append(f"confidence:{confidence}")
    evidence = finding.get("evidence_source", "")
    if evidence:
        labels.append(f"evidence:{evidence}")
    labels.extend(extra_labels or [])
    return labels


# ---------------------------------------------------------------------------
# GitHub CLI integration
# ---------------------------------------------------------------------------

def _gh() -> str:
    path = find_executable("gh")
    if path is None:
        raise FileNotFoundError("gh not found on PATH")
    return path


def check_gh_available() -> bool:
    """Return True if ``gh`` is installed and authenticated."""
    try:
        result = subprocess.run(
            [_gh(), "auth", "status"],
            capture_output=True,
            timeout=15,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def list_open_issues(repo: str) -> "list[dict]":
    """Return the open issues carrying the ``kicad-happy`` label.

    Each item has ``number``, ``title`` and ``body``. Raises IssueListError
    when the listing fails or fills the page, so nothing is exported against
    an unknown or truncated state.
    """
    try:
        result = subprocess.run(
            [
                _gh(), "issue", "list",
                f"--repo={repo}",
                "--label=kicad-happy",
                "--state=open",
                f"--limit={LIST_LIMIT}",
                "--json=number,title,body",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )
        data = None
        if result.returncode == 0:
            data = json.loads(result.stdout) if result.stdout.strip() else []
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        data = None
    if not isinstance(data, list):
        raise IssueListError(f"cannot list open issues in {repo!r}; nothing exported.")
    if len(data) >= LIST_LIMIT:
        raise IssueListError(
            f"{repo!r} has at least {LIST_LIMIT} open kicad-happy issues; the listing "
            "may be truncated, so nothing was exported."
        )
    return data


class IssueIndex:
    """Open issues: marked ones as (number, finding id, content key or None),
    unmarked ones by title."""

    def __init__(self, issues: "list[dict]"):
        self.marked: list = []
        self.legacy: dict[str, list] = {}
        self.used: set = set()
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            num = issue.get("number")
            m = marker_id(issue.get("body"))
            if m is not None:
                self.marked.append((num, m[0], m[1]))
            else:
                self.legacy.setdefault(issue.get("title") or "", []).append(num)

    def _take(self, nums) -> "object | None":
        for num in nums:
            if num not in self.used:
                self.used.add(num)
                return num
        return None

    def assign(self, findings: "list[dict]") -> dict:
        """Map each finding's JSON text to the open issue it already has.

        ``findings`` is every distinct finding of the run. A finding is stable
        when its id is not positional in this run (see ``positional_stems``;
        a stem an open marker carries with ``#N`` counts too, since that group
        has shrunk) and names no unnamed net. Claims run in a fixed order so
        input order never decides them:

        1. a stable finding takes the issue carrying its id;
        2. unstable findings sharing a content key take the remaining issues
           with that key in canonical content order, one each;
        3. a stable finding still without an issue takes one with its key,
           unless that issue carries the id of a finding present in this run;
        4. an unstable finding still without an issue takes one whose marker
           carries its exact id and no key (written before markers had keys).
        """
        stems = positional_stems(findings) | {
            _fid_stem(fid) for _, fid, _ in self.marked if _fid_stem(fid) != fid}
        marked_id = {num: fid for num, fid, _ in self.marked}
        by_id: dict[str, list] = {}
        by_key: dict[str, list] = {}
        keyless: dict[str, list] = {}
        for num, fid, key in self.marked:
            by_id.setdefault(fid, []).append(num)
            if key:
                by_key.setdefault(key, []).append(num)
            else:
                keyless.setdefault(fid, []).append(num)

        stable, unstable, present = [], [], set()
        for f in findings:
            parsed = parse_marker(finding_marker(f))
            if parsed is None:
                continue
            present.add(parsed[0])
            raw = f["finding_id"]
            is_stable = finding_key(f, positional=_fid_stem(raw) in stems) == raw
            (stable if is_stable else unstable).append((f, *parsed))
        for group in (stable, unstable):
            group.sort(key=lambda item: (_canonical(item[0]), item[1]))

        claims: dict = {}
        for f, fid, _ in stable:
            claims[_sig(f)] = self._take(by_id.get(fid, []))
        for f, _, key in unstable:
            claims[_sig(f)] = self._take(by_key.get(key, []))
        for f, fid, key in stable:
            if claims[_sig(f)] is None:
                claims[_sig(f)] = self._take(
                    n for n in by_key.get(key, []) if marked_id[n] not in present)
        for f, fid, _ in unstable:
            if claims[_sig(f)] is None:
                claims[_sig(f)] = self._take(keyless.get(fid, []))
        return {sig: num for sig, num in claims.items() if num is not None}

    def claim_title(self, titles: "list[str]") -> "object | None":
        """An unmarked open issue with one of these titles; each serves one finding."""
        for title in titles:
            num = self._take(self.legacy.get(title, []))
            if num is not None:
                return num
        return None

    def add_created(self, num, finding: dict, title: str) -> None:
        """Record an issue made this run for a finding without an id, so a
        later one with the same title is not filed twice."""
        if not finding_marker(finding):
            self.legacy.setdefault(title, []).append(num)


def create_issue(
    repo: str,
    title: str,
    body: str,
    labels: list[str],
    assignee: "str | None",
    milestone: "str | None",
) -> "str | None":
    """Create a GitHub Issue via ``gh``.

    Returns the new issue URL on success, or None on failure.
    Stderr from ``gh`` is forwarded to our stderr so the caller can see errors.
    """
    cmd = [
        "gh", "issue", "create",
        f"--repo={repo}",
        f"--title={title}",
        f"--body={body}",
    ]
    for label in labels:
        cmd.append(f"--label={label}")
    if assignee:
        cmd.append(f"--assignee={assignee}")
    if milestone:
        cmd.append(f"--milestone={milestone}")

    try:
        cmd[0] = _gh()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )
        if result.returncode == 0:
            return result.stdout.strip() or None
        # Forward gh's error output so the user understands what went wrong
        if result.stderr:
            print(f"  gh error: {result.stderr.strip()}", file=sys.stderr)
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        print(f"  subprocess error: {exc}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: "list[str] | None" = None) -> int:  # noqa: C901 (intentionally long)
    ap = argparse.ArgumentParser(
        description="Export analysis findings to GitHub Issues via gh CLI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument(
        "analysis_json",
        help="Path to analyzer JSON (schematic/PCB/EMC/thermal)",
    )
    ap.add_argument(
        "--repo",
        required=True,
        help="Target GitHub repository (owner/repo)",
    )
    ap.add_argument(
        "--create",
        action="store_true",
        help="Actually create issues (default: dry-run preview)",
    )
    ap.add_argument(
        "--severity",
        help="Minimum severity filter (high/warning/info)",
    )
    ap.add_argument(
        "--rule-id",
        dest="rule_id",
        help="Export specific rule IDs only (comma-separated)",
    )
    ap.add_argument(
        "--label",
        action="append",
        default=[],
        dest="labels",
        metavar="LABEL",
        help="Additional labels to apply (repeatable)",
    )
    ap.add_argument(
        "--assignee",
        help="Assign issues to this GitHub user",
    )
    ap.add_argument(
        "--milestone",
        help="Add issues to this milestone",
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="Output dry-run preview as JSON",
    )
    args = ap.parse_args(argv)

    # Validate --severity if provided
    if args.severity:
        known = {"critical", "high", "error", "warning", "medium", "warn", "info", "low"}
        if args.severity.lower() not in known:
            ap.error(
                f"unknown --severity {args.severity!r} — "
                "accepted: high/critical/error, warning/medium/warn, info/low"
            )

    rule_ids: "list[str] | None" = None
    if args.rule_id:
        rule_ids = [r.strip() for r in args.rule_id.split(",") if r.strip()]

    all_findings = load_findings(args.analysis_json)
    findings = filter_findings(all_findings, args.severity, rule_ids)

    if not findings:
        print(
            f"No findings match the given filters "
            f"(loaded {len(all_findings)} total from {args.analysis_json!r})."
        )
        return 2

    # --create mode requires gh
    if args.create and not check_gh_available():
        print(
            "error: gh CLI is not available or not authenticated.\n"
            "Install: https://cli.github.com/\n"
            "Authenticate: gh auth login",
            file=sys.stderr,
        )
        return 1

    # Sort findings by severity rank, then rule_id for stable output
    findings.sort(
        key=lambda f: (
            _SEV_RANK.get(_norm_severity(f.get("severity", "info")), 2),
            f.get("rule_id", ""),
        )
    )

    # -----------------------------------------------------------------------
    # Dry-run paths
    # -----------------------------------------------------------------------
    if not args.create:
        if args.json:
            # Machine-readable dry-run
            issues_out = []
            for finding in findings:
                title = format_issue_title(finding)
                body = format_issue_body(finding)
                labels = issue_labels(finding, args.labels)
                issues_out.append({
                    "rule_id": finding.get("rule_id"),
                    "severity": _norm_severity(finding.get("severity", "info")),
                    "title": title,
                    "body": body,
                    "labels": labels,
                    "assignee": args.assignee,
                    "milestone": args.milestone,
                })
            payload = {
                "schema": "export_issues/1",
                "repo": args.repo,
                "source": args.analysis_json,
                "dry_run": True,
                "count": len(issues_out),
                "issues": issues_out,
                "skipped": [],
            }
            json.dump(payload, sys.stdout, indent=2)
            sys.stdout.write("\n")
            return 0

        # Human-readable dry-run
        sep = "=" * 72
        print(sep)
        print(f"DRY-RUN: {len(findings)} issue(s) would be created in {args.repo!r}")
        print(f"Source: {args.analysis_json}")
        print(sep)
        for i, finding in enumerate(findings, 1):
            title = format_issue_title(finding)
            body = format_issue_body(finding)
            labels = issue_labels(finding, args.labels)
            print(f"\n[{i}/{len(findings)}] {title}")
            print(f"Labels: {', '.join(labels)}")
            if args.assignee:
                print(f"Assignee: {args.assignee}")
            if args.milestone:
                print(f"Milestone: {args.milestone}")
            print("-" * 72)
            print(body)
            print(sep)
        print(
            f"\nSummary: {len(findings)} issue(s) previewed. "
            "Run with --create to push."
        )
        return 0

    # -----------------------------------------------------------------------
    # --create mode
    # -----------------------------------------------------------------------

    try:
        index = IssueIndex(list_open_issues(args.repo))
    except IssueListError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    claims = index.assign(_distinct(all_findings))
    findings = _distinct(findings)

    created = 0
    skipped = 0
    errors = 0

    for finding in findings:
        rule_id = finding.get("rule_id", "")

        title = format_issue_title(finding)
        existing = claims.get(_sig(finding))
        if existing is None:
            existing = index.claim_title([title, format_issue_title(finding, inert=False)])
        if existing is not None:
            summary = (finding.get("summary") or "")[:60]
            print(f"SKIP  [{rule_id}] {summary}  (already open: #{existing})")
            skipped += 1
            continue

        body = format_issue_body(finding)
        labels = issue_labels(finding, args.labels)
        url = create_issue(
            args.repo, title, body, labels, args.assignee, args.milestone
        )
        if url:
            print(f"CREATED  {url}")
            created += 1
            tail = url.rstrip("/").rsplit("/", 1)[-1]
            index.add_created(int(tail) if tail.isdigit() else tail, finding, title)
        else:
            print(f"ERROR  [{rule_id}] {title[:60]}", file=sys.stderr)
            errors += 1

    print(
        f"\nDone: {created} created, {skipped} skipped (duplicate), "
        f"{errors} error(s)."
    )
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):  # UTF-8 on a cp1252 pipe (Windows)
        if (getattr(_stream, "encoding", "") or "").lower().replace("-", "") != "utf8" \
                and hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    sys.exit(main())
