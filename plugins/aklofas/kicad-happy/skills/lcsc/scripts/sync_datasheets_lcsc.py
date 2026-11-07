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

import sys
from pathlib import Path

# Import from sibling script (same skill)
sys.path.insert(0, str(Path(__file__).parent))
import _core_path  # noqa: F401
import provider_lcsc
from distributor_core import sync as core_sync
from distributor_core.cli import sync_main


# ---------------------------------------------------------------------------
# Core sync logic
# ---------------------------------------------------------------------------


def sync_datasheets(**kwargs) -> dict:
    """Sync via the shared driver (distributor_core.sync) with the lcsc adapter. Returns summary dict."""
    return core_sync.sync_datasheets(provider_lcsc, **kwargs)


def main():
    sync_main(
        sync_datasheets,
        description=("Sync datasheets for a KiCad project via LCSC/jlcsearch (no API key needed). Parts with neither an MPN nor a part "
                     "number from this distributor are skipped."),
        vendor="LCSC",
        delay=0.5,
        delay_help="Seconds between API calls (default: 0.5)",
    )


if __name__ == "__main__":
    from kicad_core.cli import utf8_stdio
    utf8_stdio()
    main()
