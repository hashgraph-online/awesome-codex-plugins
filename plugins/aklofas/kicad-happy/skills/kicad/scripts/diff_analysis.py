#!/usr/bin/env python3
"""
Diff-aware design review for KiCad analysis outputs.

Compares two analysis JSON files (base vs head) and reports changes:
new/removed/modified components, signal parameter shifts, EMC finding
deltas, and SPICE status transitions.

Usage:
    python3 diff_analysis.py base.json head.json
    python3 diff_analysis.py base.json head.json --text
    python3 diff_analysis.py base.json head.json --output diff.json
    python3 diff_analysis.py base.json head.json --threshold 2.0

Supports: schematic, PCB, EMC, and SPICE analyzer outputs (auto-detected).
Zero dependencies — Python 3.8+ stdlib only.
"""

import argparse
import json
import os
import sys

from finding_schema import group_findings_by_detection_type
from kicad_core.render import fmt_g4, fmt_signed, summary_or_title
from kicad_core.cli import add_only_deterministic_arg, add_output_arg, add_text_arg, utf8_text_stdout
from diff_engine import (
    SIGNAL_REGISTRY, _resolve, _identity_key, _generic_identity, detect_type, diff_schematic,
    diff_pcb, diff_emc, diff_spice, diff_thermal, diff_deep_review, classify_regressions,
    build_summary,
)


# ---------------------------------------------------------------------------
# Text formatter
# ---------------------------------------------------------------------------

MAX_TEXT_ITEMS = 20


def format_text(output):
    """Format diff output as human-readable text."""
    lines = []
    atype = output.get("analyzer_type", "?")
    summary = output.get("summary", {})
    severity = summary.get("severity", "none")
    total = summary.get("total_changes", 0)

    lines.append(f"Design Changes: {atype} ({severity}) — {total} changes")

    regressions = output.get("regressions", [])

    if total == 0 and not regressions:
        lines.append("  No changes detected.")
        return "\n".join(lines)

    s = summary
    lines.append(f"  +{s['added']} added, -{s['removed']} removed, ~{s['modified']} modified")

    if regressions:
        lines.append("")
        lines.append(f"\u26a0 {len(regressions)} regression(s) detected:")
        for r in regressions:
            lines.append(f"  [{r['severity'].upper()}] {r['detail']}")

    lines.append("")

    diff = output.get("diff", {})
    shown = 0

    # Components (schematic)
    comp = diff.get("components", {})
    if comp:
        lines.append("Components:")
        for c in comp.get("added", [])[:5]:
            lines.append(f"  + {c.get('reference', '?')} {c.get('value', '')} {c.get('footprint', '')}")
            shown += 1
        for c in comp.get("removed", [])[:5]:
            lines.append(f"  - {c.get('reference', '?')} {c.get('value', '')} {c.get('footprint', '')}")
            shown += 1
        for c in comp.get("modified", [])[:5]:
            ref = c.get("reference", "?")
            for ch in c.get("changes", []):
                lines.append(f"  ~ {ref}: {ch['field']} {ch.get('base', '?')} → {ch.get('head', '?')}")
            shown += 1
        lines.append("")

    # Signal analysis (schematic)
    sa = diff.get("signal_analysis", {})
    if sa:
        lines.append("Signal Analysis:")
        for det_type, det_diff in sa.items():
            label = det_type.replace("_", " ").title()
            for item in det_diff.get("added", [])[:3]:
                desc = " ".join(f"{k}={v}" for k, v in item.items())
                lines.append(f"  + New {label}: {desc}")
                shown += 1
            for item in det_diff.get("removed", [])[:3]:
                desc = " ".join(f"{k}={v}" for k, v in item.items())
                lines.append(f"  - Removed {label}: {desc}")
                shown += 1
            for item in det_diff.get("modified", [])[:3]:
                identity = item.get("identity", "?")
                changes = ", ".join(
                    f"{ch['field']} {ch.get('base', '?')} → {ch.get('head', '?')}"
                    for ch in item.get("changes", [])
                )
                lines.append(f"  ~ {label} {identity}: {changes}")
                attr = item.get("attributed_to", [])
                if attr:
                    causes = ", ".join(
                        f"{a['ref']} {a['base_value']}\u2192{a['head_value']}" for a in attr)
                    lines.append(f"      caused by: {causes}")
                shown += 1
            if shown >= MAX_TEXT_ITEMS:
                break
        lines.append("")

    # Footprints (PCB)
    fp = diff.get("footprints", {})
    if fp:
        lines.append("Footprints:")
        for f in fp.get("added", [])[:5]:
            lines.append(f"  + {f.get('reference', '?')} {f.get('value', '')} ({f.get('layer', '')})")
        for f in fp.get("removed", [])[:5]:
            lines.append(f"  - {f.get('reference', '?')} {f.get('value', '')} ({f.get('layer', '')})")
        for f in fp.get("modified", [])[:5]:
            ref = f.get("reference", "?")
            for ch in f.get("changes", []):
                lines.append(f"  ~ {ref}: {ch['field']} {ch.get('base', '?')} → {ch.get('head', '?')}")
        lines.append("")

    # EMC findings
    findings = diff.get("findings", {})
    if findings:
        lines.append("EMC Findings:")
        for f in findings.get("new", [])[:5]:
            lines.append(f"  NEW: {f.get('rule_id', '?')} ({f.get('severity', '?')}) {summary_or_title(f)}")
        for f in findings.get("resolved", [])[:5]:
            lines.append(f"  RESOLVED: {f.get('rule_id', '?')} ({f.get('severity', '?')}) {summary_or_title(f)}")
        for f in findings.get("changed_severity", [])[:3]:
            lines.append(f"  CHANGED: {f.get('rule_id', '?')} {f.get('base_severity', '?')} → {f.get('head_severity', '?')}")
        lines.append("")

    # SPICE status changes
    status_changes = diff.get("status_changes", [])
    if status_changes:
        lines.append("SPICE:")
        for sc in status_changes[:5]:
            direction = "REGRESSION" if sc.get("head_status") == "fail" else "FIXED" if sc.get("head_status") == "pass" else "CHANGED"
            comps = ", ".join(sc.get("components", []))
            lines.append(f"  {direction}: {sc.get('subcircuit_type', '?')} {comps}: "
                         f"{sc.get('base_status', '?')} → {sc.get('head_status', '?')}")
        lines.append("")

    # Assessments (informational measurements — present on all analyzer types)
    assessments = diff.get("assessments", {})
    if assessments and (assessments.get("added")
                        or assessments.get("removed")
                        or assessments.get("unchanged_count")):
        lines.append("Assessments:")
        added = assessments.get("added", [])
        removed = assessments.get("removed", [])
        if added:
            lines.append(f"  + Added ({len(added)}):")
            for a in added[:5]:
                refs = a.get("components") or []
                refs_str = "[" + ", ".join(refs) + "]" if refs else "[]"
                lines.append(f"    - {a.get('rule_id', '?')} on {refs_str}")
            if len(added) > 5:
                lines.append(f"    ... and {len(added) - 5} more")
        if removed:
            lines.append(f"  - Removed ({len(removed)}):")
            for a in removed[:5]:
                refs = a.get("components") or []
                refs_str = "[" + ", ".join(refs) + "]" if refs else "[]"
                lines.append(f"    - {a.get('rule_id', '?')} on {refs_str}")
            if len(removed) > 5:
                lines.append(f"    ... and {len(removed) - 5} more")
        unchanged = assessments.get("unchanged_count", 0)
        lines.append(f"  Unchanged: {unchanged}")
        lines.append("")

    # Risk score
    risk = diff.get("risk_score", {})
    if risk:
        lines.append(f"EMC Risk Score: {risk.get('base', '?')} → {risk.get('head', '?')} "
                      f"(delta {fmt_signed(risk.get('delta', 0))})")
        lines.append("")

    remaining = total - shown
    if remaining > 0:
        lines.append(f"  ... and {remaining} more changes")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Deep review text formatter
# ---------------------------------------------------------------------------

def _format_deep_review_text(output):
    """Compact text block for a deep_review diff output."""
    dr = output.get("deep_review", {})
    fixed = dr.get("fixed", [])
    new = dr.get("new", [])
    still_open = dr.get("still_open", [])
    reworded = dr.get("reworded_candidates", [])
    quarantined_head = dr.get("quarantined_head", 0)

    lines = [
        f"Deep Review Changes: {len(fixed)} fixed, {len(new)} new, "
        f"{len(still_open)} still open, {quarantined_head} quarantined in head",
    ]
    if fixed:
        lines.append("")
        lines.append("Fixed:")
        for f in fixed[:MAX_TEXT_ITEMS]:
            lines.append(f"  - {f.get('finding_id', '?')} — {f.get('summary', '')}")
    if new:
        lines.append("")
        lines.append("New:")
        for f in new[:MAX_TEXT_ITEMS]:
            lines.append(f"  + {f.get('finding_id', '?')} — {f.get('summary', '')}")
    if still_open:
        lines.append("")
        lines.append(f"Still open: {len(still_open)} finding(s) unchanged")
    if reworded:
        lines.append("")
        lines.append("Reworded candidates (advisory):")
        for r in reworded:
            lines.append(
                f"  ~ {r.get('base_finding_id', '?')} → {r.get('head_finding_id', '?')}"
                f" [{r.get('category', '?')}]"
            )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Multi-run trend extraction
# ---------------------------------------------------------------------------

def _extract_trends(analysis_dir, output_type, n_runs):
    """Extract metric values across the last N runs.

    Returns {det_type: {identity: {field: [(run_id, value), ...]}}}
    """
    from analysis_cache import list_runs, CANONICAL_OUTPUTS

    runs = list_runs(analysis_dir, limit=n_runs)
    if len(runs) < 2:
        return {}

    filename = CANONICAL_OUTPUTS.get(output_type, f"{output_type}.json")
    trends = {}

    for run_id, _meta in runs:
        path = os.path.join(analysis_dir, run_id, filename)
        if not os.path.isfile(path):
            continue
        try:
            with open(path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        sa = group_findings_by_detection_type(data)
        for det_type, detections in sa.items():
            if not isinstance(detections, list):
                continue
            if det_type not in SIGNAL_REGISTRY:
                continue
            id_fields, val_fields = SIGNAL_REGISTRY[det_type]
            for det in detections:
                key = _identity_key(det, id_fields)
                if not key:
                    key = _generic_identity(det)
                if not key:
                    continue
                bucket = trends.setdefault(det_type, {}).setdefault(key, {})
                for field in val_fields:
                    val = _resolve(det, field)
                    if isinstance(val, (int, float)):
                        bucket.setdefault(field, []).append((run_id, val))

    return trends


def _format_trends(trends, n_runs):
    """Format trend data as human-readable text."""
    lines = []
    lines.append(f"Metric Trends (last {n_runs} runs)")
    lines.append("")

    if not trends:
        lines.append("  No tracked metrics found across runs.")
        return "\n".join(lines)

    for det_type in sorted(trends):
        lines.append(f"  {det_type}:")
        for identity in sorted(trends[det_type]):
            fields = trends[det_type][identity]
            for field, datapoints in sorted(fields.items()):
                if len(datapoints) < 2:
                    continue
                # Reverse to chronological (list_runs returns newest-first)
                datapoints = list(reversed(datapoints))
                vals = [fmt_g4(v) for _, v in datapoints]
                first_val = datapoints[0][1]
                last_val = datapoints[-1][1]
                val_chain = " \u2192 ".join(vals)
                if first_val != 0:
                    pct = (last_val - first_val) / abs(first_val) * 100
                    arrow = "\u2191" if pct > 1 else "\u2193" if pct < -1 else "\u2192"
                    lines.append(f"    {identity} {field}: {val_chain} ({arrow}{abs(pct):.1f}%)")
                else:
                    lines.append(f"    {identity} {field}: {val_chain}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare two KiCad analysis JSON files and report changes"
    )
    parser.add_argument("base", nargs="?", help="Path to base (old) analysis JSON")
    parser.add_argument("head", nargs="?", help="Path to head (new) analysis JSON")
    parser.add_argument("--analysis-dir", "-d",
                        help="Analysis directory — auto-resolve runs from manifest")
    parser.add_argument("--run", action="append", default=[],
                        help="Run ID to compare (use twice: --run OLD --run NEW). "
                             "Special: 'current', 'previous', or YYYY-MM-DD_HHMM")
    parser.add_argument("--type", dest="output_type",
                        help="Output type to diff (schematic, pcb, emc, spice, "
                             "deep_review). Default: auto-detect first common output")
    add_output_arg(parser, help="Write output JSON to file (default: stdout)")
    add_text_arg(parser, help="Output human-readable text instead of JSON")
    parser.add_argument("--threshold", type=float, default=1.0,
                        help="Ignore numeric deltas below this percentage (default: 1.0%%)")
    parser.add_argument("--trend", type=int, metavar="N",
                        help="Show metric trends across last N runs (requires --analysis-dir)")
    add_only_deterministic_arg(parser, consumer=True)
    args = parser.parse_args(argv)
    if args.text:
        utf8_text_stdout()

    # Resolve runs from analysis cache if --analysis-dir is provided
    if args.analysis_dir:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from analysis_cache import list_runs, CANONICAL_OUTPUTS

        analysis_dir = args.analysis_dir
        if not os.path.isdir(analysis_dir):
            print(f"Error: analysis directory not found: {analysis_dir}", file=sys.stderr)
            return 1

        # Determine which runs to compare
        if len(args.run) == 2:
            run_ids = args.run
        elif len(args.run) == 1:
            run_ids = [args.run[0], "current"]
        else:
            run_ids = ["previous", "current"]

        # Resolve special names
        all_runs = list_runs(analysis_dir)
        if not all_runs:
            print("Error: no runs found in analysis directory", file=sys.stderr)
            return 1

        resolved = []
        for rid in run_ids:
            if rid == "current":
                resolved.append(all_runs[0][0])
            elif rid == "previous":
                if len(all_runs) < 2:
                    print("Error: only one run exists — nothing to diff", file=sys.stderr)
                    return 1
                resolved.append(all_runs[1][0])
            else:
                # Exact run ID
                found = False
                for r_id, _ in all_runs:
                    if r_id == rid:
                        found = True
                        break
                if not found:
                    print(f"Error: run '{rid}' not found in manifest", file=sys.stderr)
                    return 1
                resolved.append(rid)

        # Determine output type
        out_type = args.output_type
        if not out_type:
            # Auto-detect: find first common output between the two runs
            for otype in ("schematic", "pcb", "emc", "spice"):
                fname = CANONICAL_OUTPUTS.get(otype, f"{otype}.json")
                if (os.path.isfile(os.path.join(analysis_dir, resolved[0], fname)) and
                    os.path.isfile(os.path.join(analysis_dir, resolved[1], fname))):
                    out_type = otype
                    break
            if not out_type:
                print("Error: no common output files between runs", file=sys.stderr)
                return 1

        filename = CANONICAL_OUTPUTS.get(out_type, f"{out_type}.json")
        args.base = os.path.join(analysis_dir, resolved[0], filename)
        args.head = os.path.join(analysis_dir, resolved[1], filename)

    elif not args.base or not args.head:
        if not args.trend:
            parser.error("provide base and head paths, or use --analysis-dir")

    if args.trend:
        if not args.analysis_dir:
            parser.error("--trend requires --analysis-dir")
        out_type = args.output_type or "schematic"
        trends = _extract_trends(args.analysis_dir, out_type, args.trend)
        if args.text:
            print(_format_trends(trends, args.trend))
        else:
            json.dump({"trends": trends, "n_runs": args.trend}, sys.stdout, indent=2)
            print()
        return 0

    # Load inputs (honor --only-deterministic: skip merged/ overlay)
    def _load_input(path, label):
        from pathlib import Path
        p = Path(path)
        if not args.only_deterministic:
            candidate = p.parent.parent / "merged" / p.parent.name / p.name
            if candidate.exists():
                p = candidate
        try:
            with open(p) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error reading {label} file {path}: {e}", file=sys.stderr)
            sys.exit(1)

    base = _load_input(args.base, "base")
    head = _load_input(args.head, "head")

    # Detect types
    base_type = detect_type(base)
    head_type = detect_type(head)
    if not base_type or not head_type:
        print("Error: could not detect analyzer type from JSON", file=sys.stderr)
        return 1
    # Check for pre-v1.3 format
    old_files = []
    if base_type == "schematic_old":
        old_files.append(f"base ({args.base})")
    if head_type == "schematic_old":
        old_files.append(f"head ({args.head})")
    if old_files:
        print(f"Error: {' and '.join(old_files)} use the pre-v1.3 "
              f"signal_analysis wrapper format.\n"
              f"Re-run analyze_schematic.py to produce the current "
              f"findings[] format, then re-run this diff.",
              file=sys.stderr)
        return 1
    if base_type != head_type:
        print(f"Error: type mismatch — base is {base_type}, head is {head_type}", file=sys.stderr)
        return 1

    # Run diff
    # Note: deep_review is NOT in the dispatch table below because it has a
    # bespoke output envelope ({"deep_review": ...}) — it's handled by the
    # early-exit block immediately following. If the early-exit were removed,
    # the dict path would wrap the result under "diff" instead, breaking the
    # contract.
    diff_funcs = {
        "schematic": diff_schematic,
        "pcb": diff_pcb,
        "emc": diff_emc,
        "spice": diff_spice,
        "thermal": diff_thermal,
    }
    if base_type not in diff_funcs and base_type != "deep_review":
        print(f"Error: no diff function for analyzer type '{base_type}'",
              file=sys.stderr)
        return 1

    if base_type == "deep_review":
        dr_result = diff_deep_review(base, head)
        output = {
            "diff_version": "1.0",
            "analyzer_type": base_type,
            "base_file": args.base,
            "head_file": args.head,
            "deep_review": dr_result,
        }
        if args.text:
            text = _format_deep_review_text(output)
            if args.output:
                with open(args.output, "w") as f:
                    f.write(text)
            else:
                print(text)
        else:
            output_json = json.dumps(output, indent=2)
            if args.output:
                with open(args.output, "w") as f:
                    f.write(output_json)
            else:
                print(output_json)
        return 0

    diff_result = diff_funcs[base_type](base, head, args.threshold)
    summary = build_summary(base_type, diff_result)

    output = {
        "diff_version": "1.0",
        "analyzer_type": base_type,
        "base_file": args.base,
        "head_file": args.head,
        "has_changes": summary["total_changes"] > 0,
        "summary": summary,
        "diff": diff_result,
    }

    regressions = classify_regressions(base_type, diff_result)
    if regressions:
        output["regressions"] = regressions
        output["summary"]["regressions"] = len(regressions)

    if args.text:
        text = format_text(output)
        if args.output:
            with open(args.output, "w") as f:
                f.write(text)
        else:
            print(text)
    else:
        output_json = json.dumps(output, indent=2)
        if args.output:
            with open(args.output, "w") as f:
                f.write(output_json)
        else:
            print(output_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
