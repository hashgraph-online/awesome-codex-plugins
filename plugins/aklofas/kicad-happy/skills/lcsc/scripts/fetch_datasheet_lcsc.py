#!/usr/bin/env python3
"""Download a datasheet PDF by searching LCSC/jlcsearch for the URL.

Uses the jlcsearch community API (no auth required) to find parts by
MPN or LCSC code (Cxxxxx), then downloads the datasheet PDF directly
from LCSC's CDN (wmsc.lcsc.com). LCSC PDFs download without bot
protection — no special headers or browser fallback needed.

Usage:
    python3 fetch_datasheet_lcsc.py --search <MPN_or_LCSC_code> [--output <path>]
    python3 fetch_datasheet_lcsc.py <url> [--output <path>]

Exit codes:
    0 = success (PDF downloaded)
    1 = download failed after all attempts
    2 = search failed (part not found)

Dependencies:
    - requests (pip install requests) — preferred
    - Falls back to urllib if requests is not installed
    - playwright (optional) — for JS-rendered datasheet pages
"""

import argparse
import json
import re
import sys
import _core_path  # noqa: F401
from distributor_core.download import try_alternative_sources
from distributor_core.verify import verify_datasheet
from distributor_core.manifest import _friendly_filename
from provider_lcsc import (
    download_pdf,
    search_lcsc,
    search_lcsc_direct,
    enrich_with_wmsc,
    _get_datasheet_url,
    _get_mpn,
    _get_lcsc_code,
    _get_manufacturer,
    _get_description,
)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Download a datasheet PDF via LCSC/jlcsearch")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("url", nargs="?", help="Direct URL to the PDF")
    group.add_argument("--search", metavar="QUERY",
                       help="Search by MPN or LCSC code (e.g., GRM155R71C104KA88D or C14663)")
    parser.add_argument("--output", "-o", help="Output file path (default: <MPN>.pdf)")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")
    args = parser.parse_args()

    if args.search:
        component = search_lcsc(args.search)
        component = enrich_with_wmsc(component)
        if not component and re.match(r"^C\d+$", args.search, re.IGNORECASE):
            print(f"jlcsearch returned no results for {args.search}, trying wmsc API...",
                  file=sys.stderr)
            component = search_lcsc_direct(args.search)
        if not component:
            if args.json:
                json.dump({"success": False, "error": "Part not found on LCSC"}, sys.stdout)
            else:
                print(f"No LCSC results for '{args.search}'", file=sys.stderr)
            sys.exit(2)

        mpn = _get_mpn(component)
        lcsc_code = _get_lcsc_code(component)
        desc = _get_description(component)
        mfg = _get_manufacturer(component)
        ds_url = _get_datasheet_url(component)

        display_pn = mpn or lcsc_code or args.search
        output_path = args.output or (_friendly_filename(display_pn, desc) + ".pdf")

        if args.json:
            result = {
                "mpn": mpn,
                "lcsc": lcsc_code,
                "manufacturer": mfg,
                "description": desc,
                "datasheet_url": ds_url,
                "in_stock": component.get("stock", 0),
                "price": component.get("price"),
            }

        if not ds_url:
            print(f"No datasheet URL for {display_pn}", file=sys.stderr)
            if args.json:
                result["success"] = False
                result["error"] = "No datasheet URL in LCSC listing"
                json.dump(result, sys.stdout)
            sys.exit(2)

        print(f"Downloading datasheet for {display_pn} ({lcsc_code})...", file=sys.stderr)
        if download_pdf(ds_url, output_path):
            vr = verify_datasheet(output_path, mpn or lcsc_code, desc, mfg)
            if vr["confidence"] == "wrong":
                print(f"WARNING: Downloaded PDF may be wrong datasheet for {display_pn}",
                      file=sys.stderr)
                print(f"  {vr['details']}", file=sys.stderr)
            if args.json:
                result["success"] = True
                result["output"] = output_path
                result["verification"] = vr
                json.dump(result, sys.stdout)
            sys.exit(0)

        # Try alternative sources
        if mpn:
            print(f"LCSC URL failed, trying alternatives for {mpn}...", file=sys.stderr)
            if try_alternative_sources(mpn, output_path):
                vr = verify_datasheet(output_path, mpn, desc, mfg)
                if args.json:
                    result["success"] = True
                    result["output"] = output_path
                    result["source"] = "alternative"
                    result["verification"] = vr
                    json.dump(result, sys.stdout)
                sys.exit(0)

        print(f"Failed to download datasheet for {display_pn}", file=sys.stderr)
        if args.json:
            result["success"] = False
            result["error"] = "All download methods failed"
            json.dump(result, sys.stdout)
        sys.exit(1)

    else:
        # Direct URL mode
        url = args.url
        output_path = args.output or "datasheet.pdf"

        if download_pdf(url, output_path):
            if args.json:
                json.dump({"success": True, "output": output_path, "url": url}, sys.stdout)
            sys.exit(0)
        else:
            print(f"Failed to download PDF from {url}", file=sys.stderr)
            if args.json:
                json.dump({"success": False, "url": url, "error": "Download failed"}, sys.stdout)
            sys.exit(1)


if __name__ == "__main__":
    main()
