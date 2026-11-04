#!/usr/bin/env python3
"""Sync a local datasheets directory for a KiCad project.

Extracts components with MPNs from a KiCad schematic (or pre-computed
analyzer JSON), searches DigiKey for datasheet URLs, downloads missing
PDFs, and maintains a manifest.json file (formerly index.json — the legacy name
is still read for backward compat on existing projects).

The manifest.json tracks download status so subsequent runs only fetch new
or changed parts. The kicad skill can read this index to cross-reference
datasheets during design review.

Usage:
    python3 sync_datasheets_digikey.py <file.kicad_sch>
    python3 sync_datasheets_digikey.py <analyzer_output.json> --output ./datasheets
    python3 sync_datasheets_digikey.py <file.kicad_sch> --force     # retry failures
    python3 sync_datasheets_digikey.py <file.kicad_sch> --dry-run   # preview only
    python3 sync_datasheets_digikey.py --mpn-list mpns.txt --dry-run
    python3 sync_datasheets_digikey.py --mpn-list mpns.txt --output ./datasheets

Requires DIGIKEY_CLIENT_ID and DIGIKEY_CLIENT_SECRET environment variables.

Dependencies:
    - requests (pip install requests) — strongly recommended
    - playwright (pip install playwright && playwright install chromium) — optional
"""

import argparse
import sys
from pathlib import Path

# Import download functions from sibling script
sys.path.insert(0, str(Path(__file__).parent))
import _core_path  # noqa: F401
import provider_digikey
from distributor_core import sync as core_sync


# ---------------------------------------------------------------------------
# Core sync logic
# ---------------------------------------------------------------------------


def sync_datasheets(**kwargs) -> dict:
    """Sync via the shared driver (distributor_core.sync) with the digikey adapter. Returns summary dict."""
    return core_sync.sync_datasheets(provider_digikey, **kwargs)


def main():
    parser = argparse.ArgumentParser(
        description="Sync datasheets for a KiCad project via DigiKey API",
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
        "--delay", type=float, default=1.0,
        help="Seconds between DigiKey API calls (default: 1.0)",
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
    if result.get("failed", 0) > 0:
        sys.exit(0)  # Partial success is still success
    sys.exit(0)


if __name__ == "__main__":
    main()
