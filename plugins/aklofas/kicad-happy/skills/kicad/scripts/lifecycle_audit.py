#!/usr/bin/env python3
"""Component lifecycle and temperature audit.

Reads analyzer JSON output (BOM section) and queries distributor APIs for
lifecycle status and operating temperature data. Flags obsolete, NRND, and
EOL components, and checks temperature range coverage against a design target.

This is a standalone script (not part of the analyzer) because it requires
network access for distributor API queries. The analyzer must remain
zero-dependency and offline.

Usage:
    python3 lifecycle_audit.py analysis.json
    python3 lifecycle_audit.py analysis.json --temp-range "industrial"
    python3 lifecycle_audit.py analysis.json --temp-range="-40,85"  # use = for negative min
    python3 lifecycle_audit.py analysis.json --output lifecycle.json
    python3 lifecycle_audit.py analysis.json --only digikey

Environment:
    DIGIKEY_CLIENT_ID, DIGIKEY_CLIENT_SECRET — DigiKey OAuth 2.0
    MOUSER_SEARCH_API_KEY — Mouser API key
    ELEMENT14_API_KEY — element14/Newark API key
    (LCSC requires no credentials)
"""

import argparse
import json
import sys
from pathlib import Path

from analysis_cache import reviewed_overlay
from kicad_core.project import extraction_project_dir
from kicad_core.cli import add_only_deterministic_arg, add_output_arg
from lifecycle_engine import _TEMP_PRESETS, audit_bom


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Component lifecycle and temperature audit",
    )
    parser.add_argument(
        "input",
        help="Path to analyzer JSON output",
    )
    parser.add_argument(
        "--temp-range",
        help="Design temperature range: preset name (commercial, industrial, "
             "extended, automotive, military) or 'min,max' in °C. When the min "
             "is negative, use the = form so argparse doesn't read it as a flag: "
             "--temp-range=\"-40,85\"",
    )
    add_output_arg(parser, help="Output file path (default: stdout)")
    parser.add_argument(
        "--analysis-dir",
        help="Write lifecycle.json to this directory (analysis folder convention). "
             "Routes the output through the current run via the manifest, matching "
             "every other analyzer. Ignored if --output is also passed.",
    )
    parser.add_argument(
        "--only",
        help="Query only specific sources (comma-separated: digikey,mouser,lcsc,element14)",
    )
    parser.add_argument(
        "--delay", type=float, default=1.0,
        help="Seconds between API calls (default: 1.0)",
    )
    parser.add_argument(
        "--suggest-alternatives", action="store_true",
        help="Search for replacement parts when EOL/NRND/obsolete (extra API calls)",
    )
    add_only_deterministic_arg(parser, consumer=True)
    args = parser.parse_args(argv)

    # Load analyzer JSON (honor --only-deterministic: skip merged/ overlay)
    input_path = Path(args.input)
    if not args.only_deterministic:
        overlay = reviewed_overlay(str(input_path))
        if overlay:
            input_path = Path(overlay)
    expected = "expected the JSON file written by analyze_schematic.py"
    if not input_path.is_file():
        what = "is a directory" if input_path.is_dir() else "no such file"
        parser.error(f"input {input_path}: {what}; {expected}")
    try:
        with open(input_path, encoding="utf-8") as f:
            analysis = json.load(f)
    except ValueError as e:
        parser.error(f"input {input_path}: not JSON ({e}); {expected}")
    except OSError as e:
        parser.error(f"input {input_path}: cannot read ({e}); {expected}")

    # Extraction temperatures come only from the project the analysis names;
    # the JSON's own folder may be a shared directory such as /tmp.
    found = extraction_project_dir(analysis)
    project_dir = str(found) if found is not None else None

    # Parse temperature range
    temp_range = None
    if args.temp_range:
        if args.temp_range in _TEMP_PRESETS:
            temp_range = _TEMP_PRESETS[args.temp_range]
        else:
            parts = args.temp_range.split(",")
            if len(parts) == 2:
                try:
                    temp_range = (float(parts[0]), float(parts[1]))
                except ValueError:
                    print(f"Error: Invalid temp range '{args.temp_range}'. "
                          f"Use preset name or 'min,max'.", file=sys.stderr)
                    sys.exit(1)
            else:
                print(f"Error: Invalid temp range '{args.temp_range}'. "
                      f"Presets: {', '.join(_TEMP_PRESETS.keys())}", file=sys.stderr)
                sys.exit(1)

    # Parse sources
    sources = args.only.split(",") if args.only else []

    # Run audit
    result = audit_bom(analysis, project_dir=project_dir, temp_range=temp_range,
                       sources=sources, delay=args.delay,
                       suggest_alternatives=args.suggest_alternatives)

    # Output
    output_json = json.dumps(result, indent=2)
    output_path = args.output
    analysis_dir_mode = (not output_path
                         and hasattr(args, "analysis_dir")
                         and args.analysis_dir)

    if analysis_dir_mode:
        from output_io import write_derived_output
        out_path = write_derived_output(args.analysis_dir, output_json, analyzer="lifecycle")
        if out_path:
            print(f"Audit written to {out_path}", file=sys.stderr)
    elif output_path:
        with open(output_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(output_json)
        print(f"Audit written to {output_path}", file=sys.stderr)
    else:
        print(output_json)

    # Summary to stderr
    summary = result.get("lifecycle_summary", {})
    total = result.get("components_checked", 0)
    print(f"\nLifecycle audit: {total} components checked", file=sys.stderr)
    for status_key in ("active", "nrnd", "last_time_buy", "obsolete", "discontinued", "unknown"):
        count = summary.get(status_key, 0)
        if count:
            print(f"  {status_key}: {count}", file=sys.stderr)

    if result.get("temperature_summary"):
        ts = result["temperature_summary"]
        print(f"Temperature audit: {ts['components_checked']} checked, "
              f"{ts['components_failing_spec']} failing "
              f"({ts['design_target']['grade']} range)", file=sys.stderr)

    for obs in result.get("observations", []):
        print(f"  ! {obs}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    from kicad_core.cli import utf8_stdio
    utf8_stdio()
    sys.exit(main())
