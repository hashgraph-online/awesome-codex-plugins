#!/usr/bin/env python3
"""Download a datasheet PDF by searching Mouser for the URL.

Mouser's datasheet URLs (mouser.com/datasheet/...) sometimes block
automated downloads with bot protection. This script works around that
by trying multiple download methods and falling back to alternative
manufacturer URL patterns.

Download methods (tried in order):
  - requests library (HTTP/2, redirects, anti-bot headers)
  - Python urllib (HTTP/1.1 fallback)
  - Playwright headless browser (JS-rendered pages, last resort)

After download, the PDF is verified by extracting text and checking
for the MPN, manufacturer name, and description keywords.

Usage:
    python3 fetch_datasheet_mouser.py --search <MPN> [--output <path>]
    python3 fetch_datasheet_mouser.py <url> [--output <path>]

Environment:
    MOUSER_SEARCH_API_KEY — required for --search mode

Exit codes:
    0 = success (PDF downloaded)
    1 = download failed after all attempts
    2 = search failed (API error or part not found)

Dependencies:
    - requests (pip install requests) — preferred, handles all manufacturer sites
    - Falls back to urllib if requests is not installed (some sites may fail)
    - playwright (optional) — for JS-rendered datasheet pages
"""

import argparse
import json
import sys
import _core_path  # noqa: F401
from distributor_core.download import download_pdf, try_alternative_sources
from distributor_core.verify import verify_datasheet
from distributor_core.manifest import _friendly_filename
from provider_mouser import _get_api_key, search_mouser, scrape_product_page


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Download a datasheet via Mouser search",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("url", nargs="?", help="Direct URL to a PDF")
    group.add_argument("--search", metavar="MPN", help="Search Mouser by MPN")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    if args.url:
        # Direct URL mode
        output_path = args.output or "datasheet.pdf"
        if download_pdf(args.url, output_path):
            if args.json:
                json.dump({"success": True, "output": output_path, "source": "direct"}, sys.stdout)
            sys.exit(0)
        else:
            print(f"Failed to download PDF from {args.url}", file=sys.stderr)
            if args.json:
                json.dump({"success": False, "url": args.url, "error": "Download failed"}, sys.stdout)
            sys.exit(1)

    # --search mode
    mpn = args.search
    result = {"mpn": mpn} if args.json else None

    # Search Mouser for the datasheet URL
    api_key = _get_api_key()
    if not api_key:
        if result:
            result.update({"success": False, "error": "MOUSER_SEARCH_API_KEY not set"})
            json.dump(result, sys.stdout)
        sys.exit(2)

    print(f"[Mouser] Searching for {mpn}...", file=sys.stderr)
    mouser_part = search_mouser(mpn, api_key)

    if not mouser_part:
        print(f"[Mouser] No results for '{mpn}'", file=sys.stderr)
        if result:
            result.update({"success": False, "error": f"No Mouser results for '{mpn}'"})
            json.dump(result, sys.stdout)
        sys.exit(2)

    ds_url = mouser_part.get("DataSheetUrl", "")
    desc = mouser_part.get("Description", "")
    mfg = mouser_part.get("Manufacturer", "")

    if result:
        result["manufacturer"] = mfg
        result["description"] = desc
        result["datasheet_url"] = ds_url

    output_path = args.output or (_friendly_filename(mpn, desc) + ".pdf")

    def _finish_success(output_path: str, source: str):
        """Verify the downloaded PDF and output results."""
        vr = verify_datasheet(output_path, mpn, desc, mfg)
        if vr["confidence"] == "wrong":
            print(f"[Mouser] WARNING: Downloaded PDF may be wrong datasheet for {mpn}",
                  file=sys.stderr)
            print(f"  {vr['details']}", file=sys.stderr)
        elif vr["confidence"] == "unverified":
            print(f"[Mouser] Verification inconclusive for {mpn}: {vr['details']}",
                  file=sys.stderr)

        print(f"[Mouser] Success: {output_path}", file=sys.stderr)
        if result:
            result.update({
                "success": True, "output": output_path,
                "source": source, "verification": vr,
            })
            json.dump(result, sys.stdout)
        sys.exit(0)

    # Strategy 1: Try Mouser's datasheet URL
    if ds_url:
        print(f"[Mouser] Trying Mouser datasheet URL...", file=sys.stderr)
        if download_pdf(ds_url, output_path):
            _finish_success(output_path, "mouser")
        else:
            print(f"[Mouser] Mouser URL blocked or failed", file=sys.stderr)

    # Strategy 2: Scrape Mouser product page for datasheet link
    product_url = mouser_part.get("ProductDetailUrl", "")
    if product_url:
        print(f"[Mouser] Scraping product page for datasheet link...", file=sys.stderr)
        scraped_url = scrape_product_page(product_url)
        if scraped_url:
            print(f"[Mouser] Found datasheet link on product page", file=sys.stderr)
            if download_pdf(scraped_url, output_path):
                _finish_success(output_path, "mouser_scrape")

    # Strategy 3: Try alternative manufacturer sources
    print(f"[Mouser] Trying alternative sources...", file=sys.stderr)
    if try_alternative_sources(mpn, output_path):
        _finish_success(output_path, "alternative")

    # All methods failed — provide manual URL
    print(f"[Mouser] Failed to download datasheet for {mpn}", file=sys.stderr)
    if product_url:
        print(f"[Mouser] Manual download: {product_url}", file=sys.stderr)
    if result:
        result.update({"success": False, "error": "All download methods failed"})
        if product_url:
            result["manual_url"] = product_url
        json.dump(result, sys.stdout)
    sys.exit(1)


if __name__ == "__main__":
    main()
