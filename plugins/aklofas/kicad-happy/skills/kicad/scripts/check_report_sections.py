#!/usr/bin/env python3
"""Report completeness gate.

Reads a design-review run's analyzer JSON and derives the set of report
sections that a *full* review must contain — both the always-required base
sections and the conditional sections implied by present, non-empty analyzer
data (e.g. a populated `pdn_impedance` block means the report must carry a
"PDN Impedance" section).

Two modes:
  * default: print the required section list (grouped, with the trigger).
  * --report <file.md>: check that the finished report contains a header for
    each required section. Prints any that are missing and exits non-zero.

This converts the soft "read references/report-generation.md and write it all"
instruction into a checkable list — for the agent before it claims a review is
complete, or for CI. Stdlib-only, cross-platform.

Usage:
    python3 check_report_sections.py --analysis-dir analysis/
    python3 check_report_sections.py --analysis-dir analysis/ --report design-review.md
    python3 check_report_sections.py --run-dir analysis/2026-05-28_0058/
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

# Optional schematic keys -> required report section. Section is required only
# when the key is present AND non-empty in schematic.json. Aliases are the
# header substrings (normalized) accepted as satisfying the section.
SCHEMATIC_KEY_SECTIONS = [
    ("pdn_impedance",       "PDN Impedance",        ["pdn impedance", "pdn"]),
    ("power_budget",        "Power Budget",         ["power budget"]),
    ("power_sequencing",    "Power Sequencing",     ["power sequencing", "sequencing"]),
    ("sleep_current_audit", "Sleep Current Audit",  ["sleep current", "quiescent"]),
    ("inrush_analysis",     "Inrush Analysis",      ["inrush"]),
    ("voltage_derating",    "Voltage Derating",     ["voltage derating", "derating"]),
    ("usb_compliance",      "USB Compliance",       ["usb compliance", "usb"]),
    ("bus_topology",        "Bus Topology",         ["bus topology"]),
    ("test_coverage",       "Test Coverage",        ["test coverage", "testability", "test point"]),
    ("assembly_complexity", "Assembly Complexity",  ["assembly complexity", "assembly", "dfm"]),
    ("bom_optimization",    "BOM Optimization",     ["bom optimization", "bom optimisation"]),
]

# Always-required base sections for a full review (see references/
# report-generation.md "Required Sections for Full Reviews"). Independent of
# optional keys, but some are gated on the corresponding analyzer running.
BASE_SECTIONS = [
    ("Overview",                  ["overview"]),
    ("Critical Findings",         ["critical finding", "blockers", "critical issue"]),
    ("Component Summary",         ["component summary", "components"]),
    ("Power Tree",                ["power tree", "power architecture"]),
    ("Analyzer Verification",     ["analyzer verification", "verification"]),
    ("Signal Analysis Review",    ["signal analysis", "signal path"]),
    ("Not Performed / Review Limits", ["not performed", "review limits", "limitations"]),
    ("Final verdict / readiness", ["verdict", "readiness", "ready to fab", "ready for fab", "conclusion"]),
]

# Per-analyzer-envelope conditional sections (required when that analyzer ran).
ANALYZER_SECTIONS = {
    "pcb":            ("PCB Layout Analysis",        ["pcb layout", "layout analysis", "pcb analysis"]),
    "emc":            ("EMC / Cross-Domain Analysis", ["emc", "cross-domain", "cross domain", "emi"]),
    "thermal":        ("Thermal Analysis",            ["thermal"]),
    "gerber":         ("Gerber Verification",         ["gerber"]),
    "cross_analysis": ("EMC / Cross-Domain Analysis", ["cross-domain", "cross domain", "cross-reference", "cross reference"]),
}

ANALYZER_FILES = ["schematic", "pcb", "emc", "thermal", "gerber", "cross_analysis"]


def _normalize(s: str) -> str:
    """Lowercase, replace non-alphanumerics with spaces, collapse whitespace."""
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s.lower()).split())


def _resolve_run_dir(analysis_dir: str | None, run_dir: str | None) -> str:
    """Return a directory that directly contains the analyzer JSON files."""
    if run_dir:
        return run_dir
    if analysis_dir:
        # If the analyzer JSONs sit directly in analysis_dir, use it as-is.
        if os.path.isfile(os.path.join(analysis_dir, "schematic.json")):
            return analysis_dir
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from analysis_cache import get_current_run
            current = get_current_run(analysis_dir)
            if current is not None:
                return current[0]
        except Exception:
            pass
        return analysis_dir
    return "analysis"


def _load_envelopes(run_dir: str) -> dict:
    envs = {}
    for stem in ANALYZER_FILES:
        path = os.path.join(run_dir, f"{stem}.json")
        if os.path.isfile(path):
            try:
                envs[stem] = json.loads(open(path, encoding="utf-8").read())
            except (json.JSONDecodeError, OSError):
                pass
    return envs


def required_sections(envs: dict, analysis_dir: str | None = None) -> list[tuple[str, list[str], str]]:
    """Return [(section_label, header_aliases, trigger_reason)]."""
    out = []
    for label, aliases in BASE_SECTIONS:
        # Signal Analysis only required when a schematic ran.
        if label == "Signal Analysis Review" and "schematic" not in envs:
            continue
        out.append((label, aliases, "base"))

    for stem, (label, aliases) in ANALYZER_SECTIONS.items():
        if stem in envs and not any(o[0] == label for o in out):
            out.append((label, aliases, f"{stem}.json present"))

    sch = envs.get("schematic", {})
    for key, label, aliases in SCHEMATIC_KEY_SECTIONS:
        val = sch.get(key)
        if val:  # present and non-empty
            out.append((label, aliases, f"schematic.{key} present"))

    # Deep Review slot (v2.0 spec §3.E): required when the durable
    # findings file exists (flat, sibling of manifest.json).
    if analysis_dir and os.path.isfile(os.path.join(analysis_dir, "deep_review.json")):
        out.append(("Deep Review",
                    ["deep review", "unverified claims", "usage-vs-datasheet"],
                    "deep_review.json present"))
    return out


def check_report(report_path: str, sections) -> list[str]:
    """Return labels of required sections with no matching header in the report."""
    text = open(report_path, encoding="utf-8").read()
    headers = [_normalize(m.group(1))
               for m in re.finditer(r"^#{1,6}\s+(.*)$", text, re.MULTILINE)]
    missing = []
    for label, aliases, _ in sections:
        norm_aliases = [_normalize(a) for a in aliases]
        if not any(na and na in h for h in headers for na in norm_aliases):
            missing.append(label)
    return missing


def main() -> int:
    p = argparse.ArgumentParser(description="Report completeness gate for full design reviews.")
    p.add_argument("--analysis-dir", help="analysis/ dir (current run resolved via manifest)")
    p.add_argument("--run-dir", help="Directory directly containing schematic.json etc.")
    p.add_argument("--report", help="Markdown report to check for required section headers")
    args = p.parse_args()

    run_dir = _resolve_run_dir(args.analysis_dir, args.run_dir)
    envs = _load_envelopes(run_dir)
    if not envs:
        print(f"No analyzer JSON found under {run_dir!r}. "
              f"Pass --analysis-dir or --run-dir pointing at a completed run.",
              file=sys.stderr)
        return 2

    # Determine the flat analysis dir (sibling of manifest.json) for conditional
    # section triggers (e.g. deep_review.json). When --analysis-dir is given use
    # it directly; when only --run-dir is given, derive it as the parent.
    if args.analysis_dir:
        analysis_dir = args.analysis_dir
    elif args.run_dir:
        analysis_dir = os.path.dirname(os.path.abspath(args.run_dir))
    else:
        analysis_dir = "analysis"

    sections = required_sections(envs, analysis_dir=analysis_dir)
    print(f"Analyzers present: {', '.join(sorted(envs))}")
    print(f"Required report sections ({len(sections)}):")
    for label, _, trigger in sections:
        print(f"  - {label}   [{trigger}]")

    if args.report:
        if not os.path.isfile(args.report):
            print(f"\nReport not found: {args.report}", file=sys.stderr)
            return 2
        missing = check_report(args.report, sections)
        if missing:
            print(f"\nMISSING {len(missing)} required section(s) in {args.report}:")
            for m in missing:
                print(f"  - {m}")
            print("\nA full review must cover these. Add the section (with data) or, "
                  "if genuinely N/A, a one-line 'not applicable: <reason>' header.")
            return 1
        print(f"\nOK: all {len(sections)} required sections present in {args.report}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
