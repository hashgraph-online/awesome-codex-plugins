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

import sys
from pathlib import Path

# Import download functions from sibling script
sys.path.insert(0, str(Path(__file__).parent))
import _core_path  # noqa: F401
import provider_digikey
from distributor_core import sync as core_sync
from distributor_core.cli import sync_main


# ---------------------------------------------------------------------------
# Core sync logic
# ---------------------------------------------------------------------------


def sync_datasheets(**kwargs) -> dict:
    """Sync via the shared driver (distributor_core.sync) with the digikey adapter. Returns summary dict."""
    return core_sync.sync_datasheets(provider_digikey, **kwargs)


def main():
    sync_main(
        sync_datasheets,
        description=("Sync datasheets for a KiCad project via DigiKey API. Parts with neither an MPN nor a part "
                     "number from this distributor are skipped."),
        vendor="DigiKey",
        delay=1.0,
        delay_help="Seconds between DigiKey API calls (default: 1.0)",
    )


if __name__ == "__main__":
    from kicad_core.cli import utf8_stdio
    utf8_stdio()
    main()
