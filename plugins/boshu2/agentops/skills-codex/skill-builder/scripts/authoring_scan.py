#!/usr/bin/env python3
"""authoring_scan.py — advisory prose-quality findings for one skill package.

Emits the deep audit's `authoring` block: mechanical suspects for the three
detectable failure modes named in references/authoring-doctrine.md.

    noop-phrase                — phrasing the model already obeys by default
    negation-without-positive  — a prohibition with no positive counterpart
                                 in the same bullet/paragraph
    step-missing-done-condition — a workflow subphase with no checkable
                                 done-condition phrasing

Advisory-only by design: findings never gate a verdict or exit code. The
doctrine explains why (the no-op test is model-relative; prohibitions are
sometimes correct guardrails). Output is JSON on stdout; exit 0 on any
successful scan, 2 on usage/read errors.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

NOOP_PHRASES = [
    r"be thorough(?:ly)?\b",
    r"be careful\b",
    r"make sure to\b",
    r"\bcarefully\b",
    r"do your best\b",
    r"as appropriate\b",
    r"remember to\b",
    r"be diligent\b",
]

NEGATION_START = re.compile(r"^\s*(?:do not|don't|never|avoid)\b", re.IGNORECASE)
NEGATION_TOKEN = re.compile(r"\b(?:do not|don't|never|avoid)\b", re.IGNORECASE)
POSITIVE_MARKER = re.compile(
    r"\b(?:instead|corrective:|prefer|rather,)\s*", re.IGNORECASE
)

DONE_CONDITION = re.compile(
    r"(?:done when|checkpoint:|stop after|complete when|finished when|"
    r"until\b[^\n]*exit 0|exit 0|verify before|confirm before|wait for|"
    r"at most \d+)",
    re.IGNORECASE,
)

WORKFLOW_HEADING = re.compile(
    r"^##\s+.*(?:workflow|process|methodology|execution)", re.IGNORECASE
)


def strip_non_prose(text: str) -> str:
    """Blank out frontmatter, fenced code blocks, and HTML comments while
    preserving line numbering."""
    lines = text.splitlines()
    out: list[str] = []
    in_front = False
    in_fence = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if i == 0 and stripped == "---":
            in_front = True
            out.append("")
            continue
        if in_front:
            out.append("")
            if stripped == "---":
                in_front = False
            continue
        if stripped.startswith("```"):
            in_fence = not in_fence
            out.append("")
            continue
        if in_fence:
            out.append("")
            continue
        out.append(re.sub(r"<!--.*?-->", "", line))
    body = "\n".join(out)
    # multi-line HTML comments
    return re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), body, flags=re.DOTALL)


def find_noop_phrases(prose: str) -> list[dict]:
    findings = []
    for lineno, line in enumerate(prose.splitlines(), start=1):
        for pat in NOOP_PHRASES:
            if re.search(pat, line, re.IGNORECASE):
                findings.append(
                    {
                        "id": "noop-phrase",
                        "line": lineno,
                        "evidence": line.strip()[:160],
                    }
                )
                break
    return findings


def units_with_lines(prose: str):
    """Yield (start_line, unit_text) for paragraph/bullet units."""
    lines = prose.splitlines()
    unit: list[str] = []
    start = 1
    for i, line in enumerate(lines, start=1):
        is_bullet = bool(re.match(r"^\s*[-*] ", line))
        if not line.strip():
            if unit:
                yield start, "\n".join(unit)
                unit = []
            continue
        if is_bullet and unit:
            yield start, "\n".join(unit)
            unit = []
        if not unit:
            start = i
        unit.append(line)
    if unit:
        yield start, "\n".join(unit)


def find_negation_without_positive(prose: str) -> list[dict]:
    findings = []
    for start, unit in units_with_lines(prose):
        if unit.lstrip().startswith("#"):
            continue
        if not NEGATION_TOKEN.search(unit):
            continue
        if POSITIVE_MARKER.search(unit):
            continue
        clauses = [c.strip() for c in re.split(r"[.;]", unit) if c.strip()]
        # A clause free of negation tokens is treated as the positive
        # counterpart; the unit is flagged only when no such clause exists.
        if any(not NEGATION_TOKEN.search(c) for c in clauses):
            continue
        findings.append(
            {
                "id": "negation-without-positive",
                "line": start,
                "evidence": unit.strip().replace("\n", " ")[:160],
            }
        )
    return findings


def find_steps_missing_done_condition(prose: str) -> list[dict]:
    findings = []
    lines = prose.splitlines()
    in_workflow = False
    sub_name = None
    sub_start = 0
    sub_buf: list[str] = []

    def flush():
        if sub_name is None:
            return
        text = "\n".join(sub_buf)
        if not DONE_CONDITION.search(text):
            findings.append(
                {
                    "id": "step-missing-done-condition",
                    "line": sub_start,
                    "evidence": f"subphase '{sub_name}' has no checkable done condition",
                }
            )

    for i, line in enumerate(lines, start=1):
        if line.startswith("## "):
            flush()
            sub_name = None
            sub_buf = []
            in_workflow = bool(WORKFLOW_HEADING.match(line))
            continue
        if in_workflow and line.startswith("### "):
            flush()
            sub_name = line[4:].strip()
            sub_start = i
            sub_buf = []
            continue
        if sub_name is not None:
            sub_buf.append(line)
    flush()
    return findings


def scan(skill_md: Path) -> dict:
    prose = strip_non_prose(skill_md.read_text(encoding="utf-8"))
    findings = (
        find_noop_phrases(prose)
        + find_negation_without_positive(prose)
        + find_steps_missing_done_condition(prose)
    )
    counts = {
        "noop-phrase": 0,
        "negation-without-positive": 0,
        "step-missing-done-condition": 0,
    }
    for f in findings:
        counts[f["id"]] += 1
    return {
        "advisory": True,
        "findings": findings,
        "counts": counts,
        "summary": "authoring: %d advisory finding(s) (%s)"
        % (
            len(findings),
            ", ".join(f"{k}={v}" for k, v in counts.items()),
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="skill package directory containing SKILL.md")
    parser.add_argument("--audit-block", action="store_true", help="emit the audit report block (default output shape)")
    args = parser.parse_args()

    skill_md = Path(args.target) / "SKILL.md"
    if not skill_md.is_file():
        print(f"authoring_scan: no SKILL.md at {skill_md}", file=sys.stderr)
        return 2
    try:
        report = scan(skill_md)
    except OSError as exc:
        print(f"authoring_scan: {exc}", file=sys.stderr)
        return 2
    json.dump(report, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
