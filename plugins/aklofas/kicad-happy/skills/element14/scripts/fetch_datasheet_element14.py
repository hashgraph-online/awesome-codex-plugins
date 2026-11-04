#!/usr/bin/env python3
"""Download a datasheet PDF by searching element14 (Newark/Farnell) for the URL.

Uses the element14 Product Search API to find parts by MPN or distributor PN,
then downloads the datasheet PDF from farnell.com's CDN. PDFs download directly
without bot protection — no browser fallback needed in most cases.

Usage:
    python3 fetch_datasheet_element14.py --search <MPN_or_SKU> [--output <path>]
    python3 fetch_datasheet_element14.py <url> [--output <path>]

Exit codes:
    0 = success (PDF downloaded)
    1 = download failed after all attempts
    2 = search failed (part not found or no API key)

Environment:
    ELEMENT14_API_KEY — required for search (free from partner.element14.com)

Dependencies:
    - requests (pip install requests) — preferred
    - Falls back to urllib if requests is not installed
    - playwright (optional) — for JS-rendered datasheet pages
"""

import argparse
import json
import os
import sys
import _core_path  # noqa: F401
from distributor_core.download import try_alternative_sources
from distributor_core.verify import verify_datasheet
from distributor_core.manifest import _friendly_filename
from provider_element14 import (
    download_pdf,
    _DEFAULT_STORE,
    search_element14,
    _get_datasheet_url,
    _get_mpn,
    _get_sku,
    _get_manufacturer,
    _get_description,
)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Download a datasheet PDF via element14 (Newark/Farnell)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("url", nargs="?", help="Direct URL to the PDF")
    group.add_argument("--search", metavar="QUERY",
                       help="Search by MPN or Newark/Farnell part number")
    parser.add_argument("--output", "-o", help="Output file path (default: <MPN>.pdf)")
    parser.add_argument("--store", default=_DEFAULT_STORE,
                        help=f"element14 store ID (default: {_DEFAULT_STORE})")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")
    args = parser.parse_args()

    if args.search:
        api_key = os.environ.get("ELEMENT14_API_KEY", "")
        if not api_key:
            if args.json:
                json.dump({"success": False, "error": "ELEMENT14_API_KEY not set"}, sys.stdout)
            else:
                print("Error: ELEMENT14_API_KEY environment variable not set", file=sys.stderr)
                print("Get a free key at https://partner.element14.com/member/register",
                      file=sys.stderr)
            sys.exit(2)

        product = search_element14(args.search, api_key, args.store)
        if not product:
            if args.json:
                json.dump({"success": False, "error": "Part not found on element14"},
                          sys.stdout)
            else:
                print(f"No element14 results for '{args.search}'", file=sys.stderr)
            sys.exit(2)

        mpn = _get_mpn(product)
        sku = _get_sku(product)
        desc = _get_description(product)
        mfg = _get_manufacturer(product)
        ds_url = _get_datasheet_url(product)

        display_pn = mpn or sku or args.search
        output_path = args.output or (_friendly_filename(display_pn, desc) + ".pdf")

        if args.json:
            result = {
                "mpn": mpn,
                "sku": sku,
                "manufacturer": mfg,
                "description": desc,
                "datasheet_url": ds_url,
            }

        if not ds_url:
            print(f"No datasheet URL for {display_pn}", file=sys.stderr)
            if args.json:
                result["success"] = False
                result["error"] = "No datasheet URL in element14 listing"
                json.dump(result, sys.stdout)
            sys.exit(2)

        print(f"Downloading datasheet for {display_pn} ({sku})...", file=sys.stderr)
        if download_pdf(ds_url, output_path):
            vr = verify_datasheet(output_path, mpn or sku, desc, mfg)
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
            print(f"element14 URL failed, trying alternatives for {mpn}...",
                  file=sys.stderr)
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
                json.dump({"success": False, "url": url, "error": "Download failed"},
                          sys.stdout)
            sys.exit(1)


if __name__ == "__main__":
    main()
