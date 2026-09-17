#!/usr/bin/env python3
"""Validate catalog entries without requiring scanner CI in source repositories.

The catalog owns the admission scan. Source-repository scanner CI is useful for
contributors, but it is not a prerequisite for entering the centralized scan
matrix.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path


VALIDATOR_PATH = Path(__file__).with_name("validate-contribution.py")
SPEC = importlib.util.spec_from_file_location("awesome_codex_validator", VALIDATOR_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"could not load {VALIDATOR_PATH}")
VALIDATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VALIDATOR
SPEC.loader.exec_module(VALIDATOR)


def scan_open_pull_requests(
    repository: str,
    pull_request_number: int | None,
    matrix_output: Path | None,
    report_output: Path | None,
    status_output: Path | None,
) -> int:
    """Parse open catalog PRs and queue every new contribution for central scan."""

    pull_requests = VALIDATOR.list_open_pull_requests(repository, pull_request_number)
    matrix: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    results: list[dict[str, object]] = []
    report_lines = [
        "## Open contribution sweep",
        "",
        f"Repository: `{repository}`",
        f"Open pull requests checked: {len(pull_requests)}",
        "",
    ]

    for pull_request in pull_requests:
        prefix = f"PR #{pull_request.number} - {pull_request.title}"
        try:
            entries = VALIDATOR.entries_for_open_pull_request(repository, pull_request)
        except VALIDATOR.ValidationError as error:
            reason = str(error)
            failures.append({"pr_number": pull_request.number, "error": reason})
            results.append(
                {
                    "pr_number": pull_request.number,
                    "title": pull_request.title,
                    "head_sha": pull_request.head_sha,
                    "author_login": pull_request.author_login,
                    "state": "failure",
                    "contributions": [],
                    "failure_reasons": [reason],
                }
            )
            report_lines.append(f"- **{prefix}: FAIL** - {reason}")
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
            report_lines.append(f"- **{prefix}: PASS** - no new Community Plugins entries")
            continue

        contributions: list[dict[str, str]] = []
        report_lines.append(f"- **{prefix}**")
        for entry in entries:
            contribution = {"owner": entry.owner, "repo": entry.repo}
            contributions.append(contribution)
            matrix.append({"pr_number": pull_request.number, **contribution})
            report_lines.append(
                f"  - `{entry.owner}/{entry.repo}`: queued for centralized scanner"
            )

        results.append(
            {
                "pr_number": pull_request.number,
                "title": pull_request.title,
                "head_sha": pull_request.head_sha,
                "author_login": pull_request.author_login,
                "state": "scan",
                "contributions": contributions,
                "failure_reasons": [],
            }
        )

    if not pull_requests:
        report_lines.append("No open pull requests found.")
    elif failures:
        report_lines.extend(
            [
                "",
                f"Catalog validation failures: {len(failures)}",
                "Malformed catalog changes or PR discovery failures still block merge.",
            ]
        )
    else:
        report_lines.extend(
            [
                "",
                "Catalog validation passed. Source scanner CI is optional; centralized scans are queued.",
            ]
        )

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

    print(report, end="")
    return 0


def main() -> int:
    args = VALIDATOR.parse_args()
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

    if not VALIDATOR.git("rev-parse", "--verify", args.base_ref):
        print(f"ERROR: base ref '{args.base_ref}' is not available", file=sys.stderr)
        return 1

    try:
        entries = VALIDATOR.get_new_readme_entries(args.base_ref)
    except VALIDATOR.ValidationError as error:
        print(f"Contribution validation failed: {error}", file=sys.stderr)
        if args.matrix_output:
            VALIDATOR.write_matrix(args.matrix_output, [])
        return 1

    if not entries:
        print("No new Community Plugins entries found; contribution checks are complete.")
        if args.matrix_output:
            VALIDATOR.write_matrix(args.matrix_output, [])
        return 0

    for entry in entries:
        print(f"Queueing {entry.display_name} ({entry.owner}/{entry.repo}) for centralized scan")

    if args.matrix_output:
        VALIDATOR.write_matrix(args.matrix_output, entries)
    print(
        f"Queued {len(entries)} contribution entr{'y' if len(entries) == 1 else 'ies'} for centralized scan."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
