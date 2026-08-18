#!/usr/bin/env python3
"""EMC pre-compliance risk analyzer for KiCad designs.

Consumes schematic and/or PCB analyzer JSON output and produces a structured
EMC risk report. Operates entirely on geometric rule checks and analytical
formulas — no full-wave simulation required.

Usage:
    python3 analyze_emc.py --schematic schematic.json --pcb pcb.json
    python3 analyze_emc.py --pcb pcb.json --output emc.json
    python3 analyze_emc.py --schematic schematic.json --pcb pcb.json --severity high
    python3 analyze_emc.py --schematic schematic.json --pcb pcb.json --standard cispr-class-b

Zero external dependencies beyond Python 3.8+ stdlib.
"""

import argparse
import json
import os
import sys
import time

# Add this script's directory and kicad scripts to path for sibling imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_kicad_scripts = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              '..', '..', 'kicad', 'scripts')
if os.path.isdir(_kicad_scripts):
    sys.path.insert(0, os.path.abspath(_kicad_scripts))

from emc_rules import run_all_checks, generate_test_plan, analyze_regulatory_coverage
from emc_formulas import STANDARDS, MARKET_STANDARDS
from finding_schema import compute_trust_summary
from emc_envelope import EMCEnvelope
from schema_codec import emit_schema
from inputs_builder import build_inputs, build_upstream_artifact, build_compat
from capability_mode import get_capability_mode_ref

ANALYZER_SOURCE = "emc"

# Shared severity weights — used by both risk score and per-net scoring.
# Keyed on the v1.3 envelope vocabulary (error/warning/info); legacy
# EMC rule severities are normalized before reaching this map via
# _make_finding's _normalize_severity().
SEVERITY_WEIGHTS = {'error': 12, 'warning': 3, 'info': 0}

# Confidence discount — heuristic findings carry less weight because the
# underlying data is sampled or averaged, not exhaustively computed.
CONFIDENCE_WEIGHTS = {
    'deterministic': 1.0,
    'datasheet-backed': 1.0,
    'heuristic': 0.5,
}

# Maximum findings per rule_id that contribute to the risk score.
# Prevents per-net rules like GP-001 (which fires once per net) from
# saturating the score to 0 on 2-layer boards with many nets.
# All findings are still reported — only the score calculation is capped.
MAX_FINDINGS_PER_RULE = 3


def compute_risk_score(findings: list) -> int:
    """Compute overall EMC risk score from 0 (worst) to 100 (best).

    Each rule_id contributes at most MAX_FINDINGS_PER_RULE findings
    to the score, taking the worst (highest severity) ones. This prevents
    per-net rules from overwhelming the score while still penalizing
    boards with many different types of issues.

    All findings are still reported in the output — only the summary
    score is capped.
    """
    # Group findings by rule_id
    by_rule = {}
    for f in findings:
        rule = f.get('rule_id', '')
        by_rule.setdefault(rule, []).append(f)

    # For each rule, take the worst N findings
    penalty = 0
    sev_order = {'error': 0, 'warning': 1, 'info': 2}
    for rule, rule_findings in by_rule.items():
        # Sort by severity (worst first)
        rule_findings.sort(key=lambda f: sev_order.get(f.get('severity', 'info'), 3))
        for f in rule_findings[:MAX_FINDINGS_PER_RULE]:
            w = SEVERITY_WEIGHTS.get(f.get('severity', 'info'), 0)
            w *= CONFIDENCE_WEIGHTS.get(f.get('confidence', 'deterministic'), 1.0)
            penalty += w

    return max(0, min(100, 100 - penalty))


def compute_per_net_scores(findings: list) -> list:
    """Group findings by net name and compute per-net EMC risk scores.

    Returns a list of {net, score, finding_count, rules} sorted worst-first.
    """
    net_findings = {}
    for f in findings:
        for net in f.get('nets', []):
            if net:
                net_findings.setdefault(net, []).append(f)

    scores = []
    for net, net_f in net_findings.items():
        penalty = 0
        for f in net_f:
            w = SEVERITY_WEIGHTS.get(f['severity'], 0)
            w *= CONFIDENCE_WEIGHTS.get(f.get('confidence', 'deterministic'), 1.0)
            # SPICE-verified findings are more trustworthy — weight 1.5×
            if f.get('spice_verified'):
                w *= 1.5
            penalty += w
        score = max(0, min(100, 100 - penalty))
        rules = sorted(set(f['rule_id'] for f in net_f))
        scores.append({
            'net': net,
            'score': score,
            'finding_count': len(net_f),
            'rules': rules,
        })
    scores.sort(key=lambda s: s['score'])
    return scores


def extract_board_info(schematic: dict = None, pcb: dict = None) -> dict:
    """Extract board-level info for the report."""
    info = {}

    if pcb:
        stats = pcb.get('statistics', {})
        info['board_width_mm'] = stats.get('board_width_mm')
        info['board_height_mm'] = stats.get('board_height_mm')
        info['layer_count'] = stats.get('copper_layers_used', 0)
        info['footprint_count'] = stats.get('footprint_count', 0)
        info['via_count'] = stats.get('via_count', 0)

        setup = pcb.get('setup', {})
        stackup = setup.get('stackup', [])
        if stackup:
            info['has_stackup'] = True
            info['board_thickness_mm'] = setup.get('board_thickness_mm')
        else:
            info['has_stackup'] = False

    if schematic:
        stats = schematic.get('statistics', {})
        info['total_components'] = stats.get('total_components', 0)
        info['total_nets'] = stats.get('total_nets', 0)

        # Extract highest frequencies
        freqs = []
        for xtal in [f for f in schematic.get('findings', []) if f.get('detector') == 'detect_crystal_circuits']:
            f = xtal.get('frequency') or 0
            if isinstance(f, (int, float)) and f > 0:
                freqs.append(f)
        if freqs:
            info['highest_frequency_hz'] = max(freqs)
            info['crystal_frequencies_hz'] = sorted(set(freqs))

        # Switching frequencies
        sw_freqs = []
        for reg in [f for f in schematic.get('findings', []) if f.get('detector') == 'detect_power_regulators']:
            if reg.get('topology') not in ('ldo', 'linear'):
                # Infer from part number via emc_rules helper
                from emc_rules import _estimate_switching_freq
                f = _estimate_switching_freq(reg.get('value', ''))
                if f:
                    sw_freqs.append(f)
        if sw_freqs:
            info['switching_frequencies_hz'] = sorted(set(sw_freqs))

    return info


def format_text_report(result: dict) -> str:
    """Format findings as human-readable text."""
    lines = []
    summary = result.get('summary', {})
    findings = result.get('findings', [])

    lines.append('=' * 60)
    lines.append('EMC PRE-COMPLIANCE RISK ANALYSIS')
    lines.append('=' * 60)
    lines.append('')

    std = result.get('target_standard', 'fcc-class-b')
    lines.append(f'Target standard: {std}')
    score = summary.get('emc_risk_score', 0)
    lines.append(f'EMC risk score:  {score}/100')
    lines.append('')

    lines.append(f'Total findings:     {summary.get("total_findings", 0)}')
    lines.append(f'Categories checked: {summary.get("categories_checked", 0)}')
    by_sev = summary.get('by_severity', {}) or {}
    lines.append(f'  error:       {by_sev.get("error", 0)}')
    lines.append(f'  warning:     {by_sev.get("warning", 0)}')
    lines.append(f'  info:        {by_sev.get("info", 0)}')
    lines.append('')

    if not findings:
        lines.append('No EMC findings.')
        return '\n'.join(lines)

    # Group by category
    categories = {}
    for f in findings:
        cat = f.get('category', 'other')
        categories.setdefault(cat, []).append(f)

    cat_labels = {
        'ground_plane': 'Ground Plane Integrity',
        'decoupling': 'Decoupling Effectiveness',
        'io_filtering': 'I/O Interface Filtering',
        'switching_emc': 'Switching Regulator EMC',
        'clock_routing': 'Clock Routing Quality',
        'via_stitching': 'Via Stitching',
        'stackup': 'Stackup Quality',
        'diff_pair': 'Differential Pair EMC',
        'board_edge': 'Board Edge Analysis',
        'crosstalk': 'Crosstalk / Signal Integrity',
        'emi_filter': 'EMI Filter Verification',
        'esd_path': 'ESD Protection Path',
        'thermal_emc': 'Thermal-EMC Interaction',
        'shielding': 'Shielding / Enclosure',
        'pdn': 'PDN Impedance',
        'return_path': 'Return Path Analysis',
        'emission_estimate': 'Emission Estimates',
    }

    for cat, cat_findings in categories.items():
        lines.append('-' * 60)
        lines.append(cat_labels.get(cat, cat.replace('_', ' ').title()))
        lines.append('-' * 60)

        for f in cat_findings:
            sev = f['severity']
            lines.append(f'  [{sev}] {f["rule_id"]}: {f["title"]}')
            # Wrap description
            desc = f.get('description', '')
            for i in range(0, len(desc), 70):
                prefix = '    ' if i == 0 else '      '
                lines.append(prefix + desc[i:i+70])
            if f.get('components'):
                lines.append(f'    Components: {", ".join(f["components"])}')
            if f.get('nets'):
                lines.append(f'    Nets: {", ".join(f["nets"])}')
            if f.get('recommendation'):
                lines.append(f'    → {f["recommendation"]}')
            lines.append('')

    # Per-net scores (top 5 worst)
    per_net = result.get('per_net_scores', [])
    if per_net:
        worst = [n for n in per_net if n['score'] < 100][:5]
        if worst:
            lines.append('-' * 60)
            lines.append('Highest-Risk Nets')
            lines.append('-' * 60)
            for n in worst:
                lines.append(f'  {n["net"]}: score {n["score"]}/100 '
                             f'({n["finding_count"]} findings: {", ".join(n["rules"])})')
            lines.append('')

    # Test plan section
    tp = result.get('test_plan', {})
    if tp.get('frequency_bands'):
        lines.append('=' * 60)
        lines.append('PRE-COMPLIANCE TEST PLAN')
        lines.append('=' * 60)
        lines.append('')
        lines.append('Frequency band priority:')
        for band in tp['frequency_bands']:
            if band['source_count'] > 0:
                lines.append(f'  [{band["risk_level"].upper()}] {band["band"]}: '
                             f'{band["source_count"]} emission source(s)')
                for src in band['sources'][:3]:
                    lines.append(f'    - {src}')
        lines.append('')

    if tp.get('interface_risks'):
        lines.append('Interface risk ranking:')
        for iface in tp['interface_risks'][:5]:
            lines.append(f'  {iface["connector"]} ({iface["protocol"]}): '
                         f'risk {iface["risk_score"]}/10 — '
                         f'{", ".join(iface["reasons"])}')
        lines.append('')

    if tp.get('probe_points'):
        lines.append('Suggested near-field probe points:')
        for pt in tp['probe_points'][:10]:
            lines.append(f'  {pt["ref"]} at ({pt["x"]}, {pt["y"]})mm — {pt["reason"]}')
        lines.append('')

    # Regulatory coverage section
    reg = result.get('regulatory_coverage', {})
    if reg.get('coverage_matrix'):
        lines.append('-' * 60)
        lines.append(f'Regulatory Coverage (market: {reg.get("market", "?")})')
        lines.append('-' * 60)
        for entry in reg['coverage_matrix']:
            lines.append(f'  {entry["standard"]} ({entry["test_type"]}): '
                         f'{entry["coverage"]}')
            if entry.get('note'):
                lines.append(f'    {entry["note"]}')
        lines.append('')

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='EMC pre-compliance risk analyzer for KiCad designs')
    parser.add_argument('--schematic', '-s',
                        help='Schematic analyzer JSON. Auto-resolved from --analysis-dir current run when omitted.')
    parser.add_argument('--pcb', '-p',
                        help='PCB analyzer JSON. Auto-resolved from --analysis-dir current run when omitted.')
    parser.add_argument('--output', '-o', help='Output JSON file path')
    parser.add_argument('--severity', default='all',
                        choices=['all', 'low', 'medium', 'high', 'critical'],
                        help='Minimum severity to report (default: all)')
    parser.add_argument('--standard', default='fcc-class-b',
                        choices=list(STANDARDS.keys()),
                        help='Target EMC standard (default: fcc-class-b)')
    parser.add_argument('--text', action='store_true',
                        help='Print human-readable text report to stdout')
    parser.add_argument('--compact', action='store_true',
                        help='Omit INFO-level findings from output')
    parser.add_argument('--market', default=None,
                        choices=list(MARKET_STANDARDS.keys()),
                        help='Target market — sets applicable standards (us, eu, automotive, medical, military)')
    parser.add_argument('--spice-enhanced', action='store_true',
                        help='Use SPICE simulation for improved PDN/filter analysis (requires ngspice/LTspice/Xyce)')
    parser.add_argument('--config', default=None,
                        help='Path to .kicad-happy.json project config file')
    parser.add_argument('--analysis-dir', default=None,
                        help='Write output into analysis cache directory '
                             '(creates/updates manifest)')
    parser.add_argument('--schema', action='store_true',
                        help='Print JSON output schema and exit')
    parser.add_argument('--stage', default=None,
                        choices=['schematic', 'layout', 'pre_fab', 'bring_up'],
                        help='Filter findings by review stage')
    parser.add_argument('--audience', default=None,
                        choices=['designer', 'reviewer', 'manager'],
                        help='Audience level for summaries and --text output')
    parser.add_argument('--only-deterministic', action='store_true',
                        help='Accepted for consistency; analyzers never write llm_* fields. '
                             'Honored by downstream consumers (Phase 4 spec §3.4).')

    args = parser.parse_args()

    if args.schema:
        emit_schema(EMCEnvelope)

    if args.analysis_dir and (not args.schematic or not args.pcb):
        from analysis_cache import get_current_run
        from pathlib import Path as _AutoPath
        _current = get_current_run(args.analysis_dir)
        if _current is not None:
            _run_dir, _ = _current
            if not args.schematic:
                _sch = _AutoPath(_run_dir) / "schematic.json"
                if _sch.is_file():
                    args.schematic = str(_sch)
            if not args.pcb:
                _pcb = _AutoPath(_run_dir) / "pcb.json"
                if _pcb.is_file():
                    args.pcb = str(_pcb)

    if not args.schematic and not args.pcb:
        parser.error('At least one of --schematic or --pcb is required '
                     '(or pass --analysis-dir with a current run containing schematic.json or pcb.json)')

    # Load inputs
    schematic = None
    pcb = None

    if args.schematic:
        with open(args.schematic, 'r') as f:
            schematic = json.load(f)
        if 'signal_analysis' in schematic and 'findings' not in schematic:
            print(f'Error: {args.schematic} uses the pre-v1.3 '
                  f'signal_analysis wrapper format.\n'
                  f'Re-run analyze_schematic.py to produce the current '
                  f'findings[] format.', file=sys.stderr)
            sys.exit(1)

    if args.pcb:
        with open(args.pcb, 'r') as f:
            pcb = json.load(f)

    # Effective severity threshold
    severity = args.severity

    # SPICE-enhanced mode (optional)
    spice_backend = None
    if args.spice_enhanced:
        try:
            from emc_spice import detect_spice_simulator
            spice_backend = detect_spice_simulator()
            if spice_backend:
                print(f'SPICE-enhanced mode: {spice_backend.name}', file=sys.stderr)
            else:
                print('Warning: --spice-enhanced requested but no simulator found',
                      file=sys.stderr)
        except ImportError:
            print('Warning: SPICE skill not available for enhanced analysis',
                  file=sys.stderr)

    # Load project config (for suppressions and defaults)
    try:
        from project_config import load_config_from_path, load_config, apply_suppressions
        if args.config:
            config = load_config_from_path(args.config)
        elif args.schematic or args.pcb:
            # Auto-discover from the actual input file's directory
            input_path = args.schematic or args.pcb
            search = os.path.dirname(os.path.abspath(input_path))
            config = load_config(search)
        else:
            config = load_config('.')
    except ImportError:
        config = {'version': 1, 'project': {}, 'suppressions': []}

    # Apply config defaults to CLI args
    project = config.get('project', {})
    if args.standard == 'fcc-class-b' and project.get('emc_standard'):
        args.standard = project['emc_standard']
    if args.market is None and project.get('compliance_market'):
        args.market = project['compliance_market']

    # Build inputs provenance block (Track 1.3).
    from pathlib import Path as _Path
    _upstream_artifacts = {}
    _source_files = []
    if schematic is not None and args.schematic:
        _sch_path = _Path(args.schematic)
        _upstream_artifacts["schematic"] = build_upstream_artifact(_sch_path, schematic)
        _source_files.append(_sch_path)
    if pcb is not None and args.pcb:
        _pcb_path = _Path(args.pcb)
        _upstream_artifacts["pcb"] = build_upstream_artifact(_pcb_path, pcb)
        _source_files.append(_pcb_path)
    _cfg_path = _Path(args.config) if args.config else None
    if _cfg_path and not _cfg_path.is_file():
        _cfg_path = None

    # Resolve canonical analysis_dir ONCE (audit Highest-Risk #4).
    if args.analysis_dir:
        _analysis_dir = _Path(args.analysis_dir)
    elif args.output:
        _analysis_dir = _Path(args.output).parent
    else:
        _analysis_dir = _Path("analysis")

    # Resolve capability_mode_ref BEFORE build_inputs (audit Highest-Risk #5).
    _capability_mode_ref = get_capability_mode_ref(_analysis_dir)

    inputs = build_inputs(
        source_files=_source_files,
        upstream_artifacts=_upstream_artifacts,
        config_path=_cfg_path,
        run_id=_capability_mode_ref["run_id"],
    )
    compat = build_compat()

    # Run analysis
    t0 = time.time()
    findings = run_all_checks(schematic, pcb,
                              standard=args.standard,
                              severity_threshold=severity,
                              spice_backend=spice_backend)
    elapsed = time.time() - t0

    # Apply suppressions
    apply_suppressions(findings, config.get('suppressions', []))

    # Build summary over the standard v1.3 severity vocabulary.  EMC
    # findings go through _make_finding which normalizes legacy
    # CRITICAL/HIGH/MEDIUM/LOW/INFO to error/warning/info — we count the
    # normalized buckets directly.
    counts = {'error': 0, 'warning': 0, 'info': 0}
    active_counts = {'error': 0, 'warning': 0, 'info': 0}
    suppressed_count = 0
    for f in findings:
        sev = str(f.get('severity', 'info')).lower()
        if sev not in counts:
            sev = 'info'
        counts[sev] += 1
        if f.get('suppressed'):
            suppressed_count += 1
        else:
            active_counts[sev] += 1

    # Use only active (non-suppressed) findings for derived metrics
    active_findings = [f for f in findings if not f.get('suppressed')]

    risk_score = compute_risk_score(active_findings)

    # Generate test plan, per-net scores, and regulatory coverage
    test_plan = generate_test_plan(schematic, pcb, active_findings,
                                   standard=args.standard)
    per_net = compute_per_net_scores(active_findings)
    regulatory = analyze_regulatory_coverage(args.standard, args.market,
                                            active_findings)

    # Pre-rollup by category for downstream consumers
    _sev_order = {"error": 3, "warning": 2, "info": 1}
    category_summary = {}
    for f in findings:
        cat = f.get("category", "other")
        if cat not in category_summary:
            category_summary[cat] = {
                "count": 0,
                "max_severity": "info",
                "severities": {"error": 0, "warning": 0, "info": 0},
                "suppressed_count": 0,
            }
        cs = category_summary[cat]
        cs["count"] += 1
        sev = str(f.get("severity", "info")).lower()
        if sev not in cs["severities"]:
            sev = "info"
        cs["severities"][sev] += 1
        if f.get("suppressed"):
            cs["suppressed_count"] += 1
        if _sev_order.get(sev, 0) > _sev_order.get(cs["max_severity"], 0):
            cs["max_severity"] = sev

    result = {
        'analyzer_type': 'emc',
        'schema_version': '1.4.0',
        'inputs': inputs,
        'compat': compat,
        'summary': {
            'total_findings': len(findings),
            'categories_checked': len(category_summary),
            'active': len(findings) - suppressed_count,
            'suppressed': suppressed_count,
            # Standardized severity rollup — single source of truth.
            'by_severity': dict(counts),
            'emc_risk_score': risk_score,
        },
        'target_standard': args.standard,
        'findings': findings,
        'assessments': [],
        'per_net_scores': per_net,
        'test_plan': test_plan,
        'regulatory_coverage': regulatory,
        'category_summary': category_summary,
        'board_info': extract_board_info(schematic, pcb),
        'elapsed_s': round(elapsed, 3),
    }

    # --compact is presentation-only: strip info findings from output
    if args.compact:
        result['findings'] = [f for f in result['findings']
                              if str(f.get('severity', 'info')).lower() != 'info']

    from output_filters import apply_output_filters
    apply_output_filters(result, args.stage, args.audience)

    # Rebuild summary + trust_summary post-filter so the envelope matches
    # the final findings[] emitted to consumers. --compact and
    # apply_output_filters can both mutate findings after the initial
    # summary was built (KH-311 for trust_summary; same idea here for
    # total_findings + by_severity).
    _final = result.get('findings', []) if isinstance(result.get('findings'), list) else []
    _final_counts = {'error': 0, 'warning': 0, 'info': 0}
    for _f in _final:
        if not isinstance(_f, dict):
            continue
        _s = str(_f.get('severity', 'info')).lower()
        if _s not in _final_counts:
            _s = 'info'
        _final_counts[_s] += 1
    if isinstance(result.get('summary'), dict):
        result['summary']['total_findings'] = len(_final)
        result['summary']['by_severity'] = _final_counts
    result['trust_summary'] = compute_trust_summary(_final)

    # Wire capability_mode_ref (Phase 4 spec §3.3).
    from pathlib import Path as _Path
    # capability_mode_ref already resolved early — reuse to keep run_id stable.
    result['capability_mode_ref'] = _capability_mode_ref

    # Guarantee every finding carries a stable finding_id (Layer 2 merge keys
    # on it). MUST run before the cache block below writes the file, and after
    # --compact + output filters mutate findings.
    from finding_schema import assign_finding_ids
    assign_finding_ids(result.get('findings', []), 'emc')

    # Analysis cache integration
    if args.analysis_dir:
        import tempfile
        from pathlib import Path
        # analysis_cache lives in skills/kicad/scripts/ — already on sys.path
        from analysis_cache import (hash_source_file, should_create_new_run,
                                    create_run, overwrite_current,
                                    CANONICAL_OUTPUTS, MANIFEST_FILENAME,
                                    save_manifest, _empty_manifest, GITIGNORE_CONTENT,
                                    resolve_analysis_dir)

        # Keep analysis-dir semantics aligned with the core KiCad analyzers.
        analysis_dir = resolve_analysis_dir(args.analysis_dir)

        os.makedirs(analysis_dir, exist_ok=True)
        manifest_path = os.path.join(analysis_dir, MANIFEST_FILENAME)
        if not os.path.isfile(manifest_path):
            manifest = _empty_manifest()
            save_manifest(analysis_dir, manifest)
        gitignore_path = os.path.join(analysis_dir, '.gitignore')
        if not os.path.isfile(gitignore_path):
            with open(gitignore_path, 'w') as f:
                f.write(GITIGNORE_CONTENT)

        # Hash the schematic JSON that was consumed (primary input)
        source_hashes = {}
        if args.schematic:
            h = hash_source_file(os.path.abspath(args.schematic))
            if h:
                source_hashes[os.path.basename(args.schematic)] = h
        if args.pcb:
            h = hash_source_file(os.path.abspath(args.pcb))
            if h:
                source_hashes[os.path.basename(args.pcb)] = h

        # Write result to a temp dir, then let cache module decide
        with tempfile.TemporaryDirectory() as tmpdir:
            canonical = CANONICAL_OUTPUTS.get('emc', 'emc.json')
            tmp_out = os.path.join(tmpdir, canonical)
            with open(tmp_out, 'w') as f:
                json.dump(result, f, indent=2)

            if should_create_new_run(analysis_dir, tmpdir):
                run_id = create_run(analysis_dir, tmpdir,
                                    source_hashes=source_hashes,
                                    scripts={'emc': 'analyze_emc.py'})
                print(f'EMC analysis cached: new run {run_id}',
                      file=sys.stderr)
            else:
                overwrite_current(analysis_dir, tmpdir,
                                  source_hashes=source_hashes)
                print('EMC analysis cached: updated current run',
                      file=sys.stderr)

    # Output
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f'EMC analysis complete: {len(findings)} findings '
              f'(score {risk_score}/100) → {args.output}', file=sys.stderr)
    elif args.text:
        if args.audience:
            from output_filters import format_text
            print(format_text(result.get('findings', []), args.audience, args.stage))
        else:
            print(format_text_report(result))
    elif args.analysis_dir:
        # Already cached above (one-line confirmation printed to stderr). Don't
        # also dump the full JSON to stdout — match the core analyzers, whose
        # --analysis-dir mode is quiet.
        pass
    else:
        json.dump(result, sys.stdout, indent=2)
        print(file=sys.stdout)

    return 0


if __name__ == '__main__':
    main()
