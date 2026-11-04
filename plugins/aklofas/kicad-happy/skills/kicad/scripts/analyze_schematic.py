#!/usr/bin/env python3
"""CLI for the KiCad schematic analyzer; the analyzer lives in `schematic/`."""

import json
import os
import sys
from pathlib import Path

# Add scripts dir to path for kicad_core
sys.path.insert(0, str(Path(__file__).parent))
from schematic.pipeline import analyze_schematic, finalize_for_cli
from envelopes.schematic import SchematicEnvelope
from schema_codec import emit_schema
from inputs_builder import build_inputs, build_compat
from capability_mode import get_capability_mode_ref
from kicad_core.cli import (add_compact_arg, add_config_arg, add_only_deterministic_arg,
                            add_output_arg, add_schema_arg, add_stage_audience_args, add_text_arg,
                            utf8_text_stdout)


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="KiCad Schematic Analyzer")
    parser.add_argument("schematic", nargs="?",
                        help="Path to .kicad_sch, .kicad_pro, or project directory")
    add_output_arg(parser)
    add_compact_arg(parser)
    add_schema_arg(parser)
    add_config_arg(parser)
    parser.add_argument("--project-root", default=None,
                        help="Root .kicad_sch for hierarchy context (auto-discovered if omitted)")
    parser.add_argument("--no-hierarchy", action="store_true",
                        help="Disable hierarchy auto-discovery (treat file as standalone root)")
    parser.add_argument("--lifecycle", action="store_true",
                        help="Run lifecycle/obsolescence audit (requires network + API keys)")
    parser.add_argument("--analysis-dir", default=None,
                        help="Write output to analysis cache directory (timestamped runs)")
    add_text_arg(parser, help="Print human-readable text report to stdout")
    add_stage_audience_args(parser)
    add_only_deterministic_arg(parser)
    args = parser.parse_args(argv)
    if args.text:
        utf8_text_stdout()

    if args.schema:
        emit_schema(SchematicEnvelope)

    if not args.schematic:
        parser.error("the following arguments are required: schematic")

    # Resolve .kicad_pro or directory to the root .kicad_sch
    from kicad_core.project import resolve_project_input, empty_input_error
    try:
        resolved, note = resolve_project_input(args.schematic, '.kicad_sch')
        if note:
            print(f"Note: {note} → {os.path.basename(resolved)}",
                  file=sys.stderr)
        args.schematic = resolved
    except FileNotFoundError as e:
        parser.error(str(e))
    _empty_error = empty_input_error(args.schematic, 'kicad_sch')
    if _empty_error:
        parser.error(_empty_error)

    # Load project config (for project settings — suppressions applied to
    # EMC/thermal findings, not schematic warnings which lack rule_ids)
    from project_config import resolve_config
    resolved_cfg = resolve_config(args.config, str(Path(args.schematic).parent))
    config = resolved_cfg.effective
    _acfg = config.get("analysis")
    analysis_cfg = _acfg if isinstance(_acfg, dict) else {}

    # Resolve canonical analysis_dir ONCE — used for both AnalysisContext
    # (Phase 4d-active) and capability_mode_ref (Phase 4 §3.3). This must
    # be the same path so `--analysis-dir X` writes outputs AND capability
    # mode to the same X, not to ./analysis (audit Highest-Risk #4).
    if args.analysis_dir:
        _analysis_dir_for_ctx = Path(args.analysis_dir)
    elif args.output:
        _analysis_dir_for_ctx = Path(args.output).parent
    else:
        _analysis_dir_for_ctx = Path(analysis_cfg.get("output_dir") or "analysis")

    # Resolve capability_mode_ref BEFORE build_inputs so inputs.run_id ==
    # capability_mode_ref.run_id (Phase 4 spec §3.3, audit Highest-Risk #5).
    # First-writer-wins side effect: creates capability_mode.json if absent.
    _capability_mode_ref = get_capability_mode_ref(_analysis_dir_for_ctx)

    # Build inputs provenance block (Track 1.3).
    _sch_path = Path(args.schematic)
    _cfg_path = Path(resolved_cfg.hash_input) if resolved_cfg.hash_input else None
    inputs = build_inputs(
        source_files=[_sch_path],
        config_path=_cfg_path,
        run_id=_capability_mode_ref["run_id"],
    )
    compat = build_compat()

    result = analyze_schematic(args.schematic,
                               project_root=args.project_root,
                               no_hierarchy=args.no_hierarchy,
                               analysis_dir=_analysis_dir_for_ctx)
    # Inject provenance and drop the legacy 'file' key (already removed
    # from internal result assembly, but belt-and-suspenders).
    diagnostics = result.pop("diagnostics", [])
    result["inputs"] = inputs
    result["compat"] = compat
    result["diagnostics"] = diagnostics
    result.pop("file", None)

    finalize_for_cli(result, config, schematic_path=args.schematic, lifecycle=args.lifecycle,
                     stage=args.stage, audience=args.audience, diagnostics=diagnostics)

    if args.text:
        from output_filters import format_text
        print(format_text(result.get('findings', []), args.audience or 'designer', args.stage))
        return 0

    # Wire capability_mode_ref (Phase 4 spec §3.3). Already resolved early
    # so inputs.run_id and capability_mode_ref.run_id match.
    result["capability_mode_ref"] = _capability_mode_ref

    indent = None if args.compact else 2
    output = json.dumps(result, indent=indent, default=str)

    if args.analysis_dir:
        from output_io import write_primary_run
        write_primary_run(args.analysis_dir, output, analyzer="schematic", source_path=args.schematic,
                          script_name="analyze_schematic.py",
                          track_in_git=bool(analysis_cfg.get("track_in_git", False)),
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
