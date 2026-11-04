#!/usr/bin/env python3
"""Download a datasheet PDF from a manufacturer URL.

Handles manufacturer-specific quirks:
- TI: DigiKey returns JS-redirect URLs; this script extracts the direct PDF URL
- Protocol-relative URLs (//mm.digikey.com/...): adds https: prefix
- Microchip: Redirects to login; uses alternative URL patterns as fallback
- Various manufacturers that block bare urllib: uses requests library with
  proper User-Agent (handles HTTP/2, redirects, and anti-bot checks)

Usage:
    python3 fetch_datasheet_digikey.py <url> [--output <path>]
    python3 fetch_datasheet_digikey.py --search <MPN> [--output <path>]

The --search mode requires DIGIKEY_CLIENT_ID and DIGIKEY_CLIENT_SECRET
environment variables.

Dependencies:
    - requests (pip install requests) — preferred, handles all manufacturer sites
    - Falls back to urllib if requests is not installed (some sites may fail)

Exit codes:
    0 = success (PDF downloaded)
    1 = download failed after all attempts
    2 = search failed (API error or part not found)
"""

import argparse
import json
import sys
import _core_path  # noqa: F401
from distributor_core.download import download_pdf, try_alternative_sources
from distributor_core.verify import verify_datasheet
from distributor_core.manifest import _friendly_filename
from provider_digikey import search_digikey


def main():
    parser = argparse.ArgumentParser(description="Download a datasheet PDF")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("url", nargs="?", help="Direct URL to the PDF")
    group.add_argument("--search", metavar="MPN", help="Search DigiKey by MPN and download the datasheet")
    parser.add_argument("--output", "-o", help="Output file path (default: <MPN>.pdf in current directory)")
    parser.add_argument("--json", action="store_true", help="Output result as JSON (for script integration)")
    args = parser.parse_args()

    if args.search:
        product = search_digikey(args.search)
        if not product:
            if args.json:
                json.dump({"success": False, "error": "Part not found"}, sys.stdout)
            sys.exit(2)

        mpn = product.get("ManufacturerProductNumber", args.search)
        desc = product.get("Description", {}).get("ProductDescription", "")
        ds_url = product.get("DatasheetUrl", "")
        output_path = args.output or (_friendly_filename(mpn, desc) + ".pdf")

        if args.json:
            result = {
                "mpn": mpn,
                "manufacturer": product.get("Manufacturer", {}).get("Name", ""),
                "description": product.get("Description", {}).get("ProductDescription", ""),
                "datasheet_url": ds_url,
            }

        if not ds_url:
            print(f"No datasheet URL for {mpn}", file=sys.stderr)
            if args.json:
                result["success"] = False
                result["error"] = "No datasheet URL in DigiKey listing"
                json.dump(result, sys.stdout)
            sys.exit(2)

        if download_pdf(ds_url, output_path):
            vr = verify_datasheet(output_path, mpn, desc,
                                  product.get("Manufacturer", {}).get("Name", ""))
            if vr["confidence"] == "wrong":
                print(f"WARNING: Downloaded PDF may be wrong datasheet for {mpn}",
                      file=sys.stderr)
                print(f"  {vr['details']}", file=sys.stderr)
            elif vr["confidence"] == "unverified":
                print(f"  Verification inconclusive for {mpn}: {vr['details']}",
                      file=sys.stderr)
            if args.json:
                result["success"] = True
                result["output"] = output_path
                result["verification"] = vr
                json.dump(result, sys.stdout)
            sys.exit(0)

        # Try alternative sources
        print(f"Primary URL failed, trying alternatives for {mpn}...", file=sys.stderr)
        if try_alternative_sources(mpn, output_path):
            vr = verify_datasheet(output_path, mpn, desc,
                                  product.get("Manufacturer", {}).get("Name", ""))
            if vr["confidence"] == "wrong":
                print(f"WARNING: Downloaded PDF may be wrong datasheet for {mpn}",
                      file=sys.stderr)
                print(f"  {vr['details']}", file=sys.stderr)
            if args.json:
                result["success"] = True
                result["output"] = output_path
                result["source"] = "alternative"
                result["verification"] = vr
                json.dump(result, sys.stdout)
            sys.exit(0)

        print(f"Failed to download datasheet for {mpn}", file=sys.stderr)
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
