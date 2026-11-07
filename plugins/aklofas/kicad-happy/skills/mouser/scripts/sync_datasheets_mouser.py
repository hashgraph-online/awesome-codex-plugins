#!/usr/bin/env python3
"""Sync a local datasheets directory for a KiCad project via Mouser.

Extracts components with MPNs from a KiCad schematic (or pre-computed
analyzer JSON), searches Mouser for datasheet URLs, downloads missing
PDFs, and maintains a manifest.json file (legacy name index.json still read).

The manifest.json format matches across distributor skills so they can
contribute to the same datasheets directory. The source field
distinguishes which distributor provided the datasheet.

Download strategy per part:
  1. Try the datasheet URL from the schematic itself
  2. Search Mouser API for the part → try Mouser's datasheet URL
  3. Try manufacturer-specific alternative URL patterns

Download methods (per URL, tried in order):
  - requests library (HTTP/2, redirects, anti-bot headers)
  - Python urllib (HTTP/1.1 fallback)
  - Playwright headless browser (JS-rendered pages, last resort)

Usage:
    python3 sync_datasheets_mouser.py <file.kicad_sch>
    python3 sync_datasheets_mouser.py <analyzer_output.json> --output ./datasheets
    python3 sync_datasheets_mouser.py <file.kicad_sch> --force     # retry failures
    python3 sync_datasheets_mouser.py <file.kicad_sch> --dry-run   # preview only
    python3 sync_datasheets_mouser.py --mpn-list mpns.txt --dry-run
    python3 sync_datasheets_mouser.py --mpn-list mpns.txt --output ./datasheets

Requires MOUSER_SEARCH_API_KEY environment variable.

Dependencies:
    - requests (pip install requests) — strongly recommended
    - playwright (pip install playwright && playwright install chromium) — optional
"""

import sys
from pathlib import Path

# Import from sibling script (same skill)
sys.path.insert(0, str(Path(__file__).parent))
import _core_path  # noqa: F401
import provider_mouser
from distributor_core import sync as core_sync
from distributor_core.cli import sync_main


# ---------------------------------------------------------------------------
# Core sync logic
# ---------------------------------------------------------------------------


def sync_datasheets(**kwargs) -> dict:
    """Sync via the shared driver (distributor_core.sync) with the mouser adapter. Returns summary dict."""
    return core_sync.sync_datasheets(provider_mouser, **kwargs)


def main():
    sync_main(
        sync_datasheets,
        description=("Sync datasheets for a KiCad project via Mouser API. Parts with neither an MPN nor a part "
                     "number from this distributor are skipped."),
        vendor="Mouser",
        delay=1.0,
        delay_help="Seconds between API calls (default: 1.0)",
    )


if __name__ == "__main__":
    from kicad_core.cli import utf8_stdio
    utf8_stdio()
    main()
