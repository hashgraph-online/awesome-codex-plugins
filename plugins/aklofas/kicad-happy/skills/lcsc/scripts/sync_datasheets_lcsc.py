#!/usr/bin/env python3
"""Sync a local datasheets directory for a KiCad project via LCSC/jlcsearch.

Extracts components with MPNs or LCSC codes from a KiCad schematic (or
pre-computed analyzer JSON), searches jlcsearch for datasheet URLs,
downloads missing PDFs, and maintains a manifest.json file (legacy name index.json
still read for backward compat).

The manifest.json format matches across distributor skills so they can
contribute to the same datasheets directory. The source field
distinguishes which distributor provided the datasheet.

No API key required — uses the jlcsearch community API (free, no auth).
LCSC's CDN (wmsc.lcsc.com) serves PDFs directly without bot protection.

Download strategy per part:
  1. Try the datasheet URL from the schematic itself
  2. Search jlcsearch API → download from LCSC CDN (direct PDF URL)
  3. Try manufacturer-specific alternative URL patterns

Usage:
    python3 sync_datasheets_lcsc.py <file.kicad_sch>
    python3 sync_datasheets_lcsc.py <analyzer_output.json> --output ./datasheets
    python3 sync_datasheets_lcsc.py <file.kicad_sch> --force     # retry failures
    python3 sync_datasheets_lcsc.py <file.kicad_sch> --dry-run   # preview only
    python3 sync_datasheets_lcsc.py --mpn-list mpns.txt --dry-run
    python3 sync_datasheets_lcsc.py --mpn-list mpns.txt --output ./datasheets

Dependencies:
    - requests (pip install requests) — strongly recommended
    - playwright (pip install playwright && playwright install chromium) — optional
"""

import argparse
import sys
from pathlib import Path

# Import from sibling script (same skill)
sys.path.insert(0, str(Path(__file__).parent))
import _core_path  # noqa: F401
import provider_lcsc
from distributor_core import sync as core_sync


# ---------------------------------------------------------------------------
# Core sync logic
# ---------------------------------------------------------------------------


def sync_datasheets(**kwargs) -> dict:
    """Sync via the shared driver (distributor_core.sync) with the lcsc adapter. Returns summary dict."""
    return core_sync.sync_datasheets(provider_lcsc, **kwargs)


def main():
    parser = argparse.ArgumentParser(
        description="Sync datasheets for a KiCad project via LCSC/jlcsearch (no API key needed)",
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "input",
        nargs="?",
        help="Path to .kicad_sch file or pre-computed analyzer JSON",
    )
    input_group.add_argument(
        "--mpn-list",
        metavar="FILE",
        help=("Path to a text file with one MPN per line (KH-312 batch mode). "
              "Skips blank lines and '#' comments. Output defaults to "
              "./datasheets/ in cwd when --output is not given."),
    )
    parser.add_argument(
        "--output", "-o",
        help=("Output directory (default: datasheets/ next to input, "
              "or ./datasheets/ in cwd when --mpn-list is used)"),
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Retry previously failed downloads",
    )
    parser.add_argument(
        "--force-all", action="store_true",
        help="Re-download everything, including already-present files",
    )
    parser.add_argument(
        "--delay", type=float, default=0.5,
        help="Seconds between API calls (default: 0.5)",
    )
    parser.add_argument(
        "--parallel", type=int, default=1,
        help="Number of parallel download workers (default: 1)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be downloaded without doing it",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output summary as JSON",
    )
    args = parser.parse_args()

    result = sync_datasheets(
        input_path=args.input,
        output_dir=args.output,
        force=args.force,
        force_all=args.force_all,
        delay=args.delay,
        parallel=args.parallel,
        dry_run=args.dry_run,
        as_json=args.json,
        mpn_list=args.mpn_list,
    )

    if "error" in result:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
