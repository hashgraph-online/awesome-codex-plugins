#!/usr/bin/env python3
"""CLI for the KiCad PCB layout analyzer; the analyzer lives in `pcb/`."""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pcb.pipeline import analyze_pcb, finalize_for_cli
from envelopes.pcb import PCBEnvelope
from schema_codec import emit_schema
from inputs_builder import build_inputs, build_compat
from capability_mode import get_capability_mode_ref
from kicad_core.cli import (add_compact_arg, add_config_arg, add_only_deterministic_arg,
                            add_output_arg, add_schema_arg, add_stage_audience_args, add_text_arg,
                            utf8_text_stdout)


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="KiCad PCB Layout Analyzer")
    parser.add_argument("pcb", nargs="?",
                        help="Path to .kicad_pcb, .kicad_pro, or project directory")
    add_output_arg(parser)
    add_compact_arg(parser)
    parser.add_argument("--full", action="store_true",
                        help="Include individual track/via coordinate data")
    parser.add_argument("--proximity", action="store_true",
                        help="Run trace proximity analysis for crosstalk assessment")
    add_schema_arg(parser)
    add_config_arg(parser)
    parser.add_argument("--analysis-dir", default=None,
                        help="Write output to analysis cache directory (timestamped runs)")
    parser.add_argument("--schematic",
                        help="Schematic analysis JSON for cross-analyzer enrichment")
    parser.add_argument('--power-rails', default=None,
                        help='Comma-separated power net names to treat as rails '
                             '(overrides name heuristics; normally auto-read from --schematic)')
    add_text_arg(parser, help="Print human-readable text report to stdout")
    add_stage_audience_args(parser)
    parser.add_argument('--return-path-radius-mm', type=float, default=0.5,
                        help='Radius (mm) for copper-presence in return-path analysis (default: 0.5)')
    parser.add_argument('--gp001-debug', action='store_true',
                        help='Emit per-sample diagnostic JSON to analysis dir')
    add_only_deterministic_arg(parser)
    args = parser.parse_args(argv)
    if args.text:
        utf8_text_stdout()

    if args.schema:
        emit_schema(PCBEnvelope)

    if not args.pcb:
        parser.error("the following arguments are required: pcb")

    # Resolve .kicad_pro or directory to the .kicad_pcb file
    from kicad_core.project import resolve_project_input, empty_input_error
    try:
        resolved, note = resolve_project_input(args.pcb, '.kicad_pcb')
        if note:
            print(f"Note: {note} → {os.path.basename(resolved)}",
                  file=sys.stderr)
        args.pcb = resolved
    except FileNotFoundError as e:
        parser.error(str(e))
    _empty_error = empty_input_error(args.pcb, 'kicad_pcb')
    if _empty_error:
        parser.error(_empty_error)

    # Load project config (for project settings — suppressions applied to
    # EMC/thermal findings, not PCB warnings which lack rule_ids)
    from project_config import resolve_config
    resolved_cfg = resolve_config(args.config, str(Path(args.pcb).parent))
    config = resolved_cfg.effective
    _acfg = config.get("analysis")
    analysis_cfg = _acfg if isinstance(_acfg, dict) else {}

    # Build inputs provenance block (Track 1.3).
    # Resolve canonical analysis_dir ONCE (used for capability_mode_ref).
    # Includes --analysis-dir, fixing audit Highest-Risk #4 (split with output).
    if args.analysis_dir:
        _analysis_dir = Path(args.analysis_dir)
    elif args.output:
        _analysis_dir = Path(args.output).parent
    else:
        _analysis_dir = Path(analysis_cfg.get("output_dir") or "analysis")

    # Resolve capability_mode_ref BEFORE build_inputs so inputs.run_id ==
    # capability_mode_ref.run_id (audit Highest-Risk #5).
    _capability_mode_ref = get_capability_mode_ref(_analysis_dir)

    _pcb_path = Path(args.pcb)
    _cfg_path = Path(resolved_cfg.hash_input) if resolved_cfg.hash_input else None
    inputs = build_inputs(
        source_files=[_pcb_path],
        config_path=_cfg_path,
        run_id=_capability_mode_ref["run_id"],
    )
    compat = build_compat()

    schematic_data = None
    if args.schematic:
        try:
            with open(args.schematic) as f:
                schematic_data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: cannot load schematic analysis: {e}", file=sys.stderr)
        if (schematic_data and 'signal_analysis' in schematic_data
                and 'findings' not in schematic_data):
            print(f'Warning: {args.schematic} uses the pre-v1.3 '
                  f'signal_analysis wrapper format — schematic cross-ref '
                  f'disabled. Re-run analyze_schematic.py for full '
                  f'analysis.', file=sys.stderr)
            schematic_data = None

    power_rails = None
    if args.power_rails:
        power_rails = {r.strip() for r in args.power_rails.split(",") if r.strip()}

    result = analyze_pcb(args.pcb, proximity=args.proximity,
                         include_trace_segments=args.full,
                         schematic_data=schematic_data,
                         return_path_radius_mm=args.return_path_radius_mm,
                         gp001_debug=args.gp001_debug,
                         power_rails=power_rails)
    # Inject provenance and drop legacy 'file' key (already removed from
    # internal result assembly, but belt-and-suspenders).
    diagnostics = result.pop("diagnostics", [])
    result["inputs"] = inputs
    result["compat"] = compat
    result["diagnostics"] = diagnostics
    result.pop("file", None)

    finalize_for_cli(result, config, pcb_path=args.pcb, analysis_dir_arg=args.analysis_dir,
                     return_path_radius_mm=args.return_path_radius_mm,
                     stage=args.stage, audience=args.audience)

    if args.text:
        from output_filters import format_text
        print(format_text(result.get('findings', []), args.audience or 'designer', args.stage))
        return 0

    # Wire capability_mode_ref (Phase 4 spec §3.3).
    # capability_mode_ref already resolved early — reuse to keep run_id stable.
    result["capability_mode_ref"] = _capability_mode_ref

    indent = None if args.compact else 2
    output = json.dumps(result, indent=indent, default=str)

    if args.analysis_dir:
        from output_io import write_primary_run
        write_primary_run(args.analysis_dir, output, analyzer="pcb", source_path=args.pcb,
                          script_name="analyze_pcb.py", track_in_git=False,
                          diff_threshold=analysis_cfg.get("diff_threshold", "major"),
                          retention=int(analysis_cfg.get("retention", 0) or 0))

    elif args.output:
        Path(args.output).write_text(output)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
