#!/usr/bin/env python3
"""Export analysis findings to GitHub Issues.

Reads analyzer JSON output and creates GitHub Issues via the ``gh`` CLI.
Dry-run by default — previews issues to stdout. Use ``--create`` to push.
Label-based dedup prevents duplicates.

Usage:
    export_issues.py schematic.json --repo owner/repo
    export_issues.py schematic.json --repo owner/repo --severity warning
    export_issues.py schematic.json --repo owner/repo --rule-id RG-001,CP-001
    export_issues.py schematic.json --repo owner/repo --create

Python 3.8+ stdlib only. Requires ``gh`` CLI (https://cli.github.com/).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

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


def load_findings(path: str) -> list[dict]:
    """Load an analyzer JSON file and return findings that have a rule_id."""
    if not os.path.isfile(path):
        raise SystemExit(f"error: file not found: {path!r}")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"error: cannot read {path!r}: {exc}") from exc

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


def format_issue_title(finding: dict) -> str:
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

    return title


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
    rule_id = finding.get("rule_id", "")
    severity = _norm_severity(finding.get("severity", "info"))
    confidence = finding.get("confidence", "")
    evidence = finding.get("evidence_source", "")
    category = finding.get("category", "")
    detector = finding.get("detector", "")

    lines: list[str] = []

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
    summary = (finding.get("summary") or "").strip()
    if summary:
        lines.append("## Summary")
        lines.append("")
        lines.append(summary)
        lines.append("")

    # --- Description ---
    description = (finding.get("description") or "").strip()
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
                ref = comp.get("ref") or comp.get("reference") or comp.get("name") or ""
                val = comp.get("value") or ""
                fp = comp.get("footprint") or ""
                parts = [f"`{ref}`" if ref else ""]
                if val:
                    parts.append(val)
                if fp:
                    parts.append(f"({fp})")
                lines.append(f"- {' '.join(p for p in parts if p)}")
            elif isinstance(comp, str):
                lines.append(f"- `{comp}`")
        lines.append("")

    # --- Nets ---
    nets: list = finding.get("nets") or []
    if nets:
        lines.append("## Nets")
        lines.append("")
        for net in nets:
            if isinstance(net, str):
                lines.append(f"- `{net}`")
            elif isinstance(net, dict):
                name = net.get("name") or net.get("net") or str(net)
                lines.append(f"- `{name}`")
        lines.append("")

    # --- Recommendation ---
    recommendation = (finding.get("recommendation") or "").strip()
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

def check_gh_available() -> bool:
    """Return True if ``gh`` is installed and authenticated."""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            timeout=15,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def find_existing_issues(repo: str, rule_id: str) -> list[dict]:
    """Return open issues that carry the dedup label ``kicad-happy:{rule_id}``.

    Uses ``gh issue list --json number,title`` for machine-readable output.
    Returns an empty list on any error.
    """
    label = f"kicad-happy:{rule_id}"
    try:
        result = subprocess.run(
            [
                "gh", "issue", "list",
                "--repo", repo,
                "--label", label,
                "--state", "open",
                "--json", "number,title",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return []
        return json.loads(result.stdout) if result.stdout.strip() else []
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return []


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
        "--repo", repo,
        "--title", title,
        "--body", body,
    ]
    for label in labels:
        cmd += ["--label", label]
    if assignee:
        cmd += ["--assignee", assignee]
    if milestone:
        cmd += ["--milestone", milestone]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
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

    # Batch dedup: query once per unique rule_id, not once per finding
    unique_rule_ids = {f.get("rule_id", "") for f in findings}
    existing_by_rule = {
        rid: find_existing_issues(args.repo, rid) for rid in unique_rule_ids if rid
    }

    created = 0
    skipped = 0
    errors = 0

    for finding in findings:
        rule_id = finding.get("rule_id", "")

        # Dedup check (uses pre-fetched results)
        existing = existing_by_rule.get(rule_id, [])
        if existing:
            nums = ", ".join(f"#{e['number']}" for e in existing)
            summary = (finding.get("summary") or "")[:60]
            print(f"SKIP  [{rule_id}] {summary}  (already open: {nums})")
            skipped += 1
            continue

        title = format_issue_title(finding)
        body = format_issue_body(finding)
        labels = issue_labels(finding, args.labels)
        url = create_issue(
            args.repo, title, body, labels, args.assignee, args.milestone
        )
        if url:
            print(f"CREATED  {url}")
            created += 1
        else:
            print(f"ERROR  [{rule_id}] {title[:60]}", file=sys.stderr)
            errors += 1

    print(
        f"\nDone: {created} created, {skipped} skipped (duplicate), "
        f"{errors} error(s)."
    )
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
