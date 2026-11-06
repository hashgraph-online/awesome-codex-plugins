"""Mouser adapter: auth, search, response accessors, and the provider's sync_one_part strategy chain — verbatim from fetch_datasheet_mouser.py / sync_datasheets_mouser.py; the driver is distributor_core.sync. Adapter constants are the thirteen measured per-provider differences of the old drivers."""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import _core_path  # noqa: F401
from distributor_core.download import (_USER_AGENT, _requests, download_pdf, note_transport_failure,
                                       try_alternative_sources)
from distributor_core.verify import verify_datasheet
from distributor_core.manifest import friendly_filename

NAME = "mouser"
DEFAULT_DELAY = 1.0
ID_KEYS = ("mouser", "digikey", "lcsc", "element14")
KEY_PRIORITY = ("mouser",)
SKIPPED_COUNTS_IDS = ()
RENAME_PRESENT = True
FAILED_DETAIL_WITH_URL = True
# Documentary today: the normalize_url/download_pdf wrappers hard-code the flag; a later version may read it.
NORMALIZE_REDIRECTS = True
LABELS = {
    "found": "Found {n} unique parts with MPNs ({k} skipped without MPN)",
    "skipped_key": "skipped_no_mpn",
    "total_key": "total_parts_with_mpn",
    "dry_skipped": "Skipped (no MPN): {k}",
    "summary_skipped": "  Skipped (no MPN): {k}",
}


def preflight(**kw):
    return {}


def authenticate():
    key = _get_api_key()
    return {"error": "MOUSER_SEARCH_API_KEY not set"} if not key else {"ctx": key}


def report_tail(out_dir, downloaded, already_present, failed):
    return None


def _get_api_key() -> str:
    """Get the Mouser Search API key from environment."""
    key = os.environ.get("MOUSER_SEARCH_API_KEY", "")
    if not key:
        print(
            "Error: MOUSER_SEARCH_API_KEY environment variable not set.\n"
            "  Get a free key at mouser.com → My Account → APIs → Search API\n"
            "  Then: export MOUSER_SEARCH_API_KEY=your-key-here",
            file=sys.stderr,
        )
    return key


def search_mouser(mpn: str, api_key: str) -> dict | None:
    """Search Mouser API for a part by MPN. Returns first match."""
    url = f"https://api.mouser.com/api/v1/search/partnumber?apiKey={api_key}"
    body = json.dumps({
        "SearchByPartRequest": {
            "mouserPartNumber": mpn,
            "partSearchOptions": "Exact",
        }
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        note_transport_failure(e)
        print(f"[Mouser] Search failed: {e}", file=sys.stderr)
        return None

    errors = data.get("Errors", [])
    if errors:
        for err in errors:
            print(f"[Mouser] API error: {err.get('Message', err)}", file=sys.stderr)
        return None

    parts = (data.get("SearchResults") or {}).get("Parts", [])
    if not parts:
        return None

    # Prefer exact MPN match
    mpn_upper = mpn.upper()
    for p in parts:
        if p.get("ManufacturerPartNumber", "").upper() == mpn_upper:
            return p
    return parts[0]


def scrape_product_page(product_url: str) -> str:
    """Try to extract a datasheet PDF URL from a Mouser product page.

    Mouser product pages contain datasheet links in the HTML. This tries
    to fetch the page and extract the link without requiring JS rendering.
    Returns the datasheet URL or empty string on failure.
    """
    if not product_url:
        return ""

    # Normalize URL
    if not product_url.startswith("http"):
        product_url = "https://www.mouser.com" + product_url

    headers = {
        "User-Agent": _USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }

    html = ""

    # Try requests first
    if _requests is not None:
        try:
            resp = _requests.get(product_url, headers=headers, timeout=20,
                                 allow_redirects=True)
            if resp.status_code == 200:
                html = resp.text
        except Exception:
            pass

    # Fallback to urllib
    if not html:
        try:
            req = urllib.request.Request(product_url, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
        except Exception:
            pass

    if not html:
        return ""

    # Look for datasheet PDF links in the HTML
    # Mouser uses patterns like href="/datasheet/..." or data-href with PDF URLs
    patterns = [
        r'href="(https?://www\.mouser\.com/datasheet/[^"]+\.pdf[^"]*)"',
        r'href="(/datasheet/[^"]+\.pdf[^"]*)"',
        r'href="(https?://[^"]+\.pdf)"[^>]*>[^<]*[Dd]ata\s*[Ss]heet',
        r'"(https?://www\.mouser\.com/pdfDocs/[^"]+\.pdf)"',
    ]

    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            url = match.group(1)
            if url.startswith("/"):
                url = "https://www.mouser.com" + url
            return url

    return ""


def sync_one_part(
    part: dict,
    output_dir: Path,
    index: dict,
    delay: float,
    ctx,
) -> dict:
    """Download datasheet for one part. Returns updated manifest entry."""
    mouser_api_key = ctx
    mpn = part["mpn"]
    mouser_pn = part.get("mouser", "")
    now = datetime.now(timezone.utc).isoformat()

    # Use MPN for display/filename if available, otherwise fall back to Mouser PN
    display_pn = mpn or mouser_pn

    desc = part.get("description", "")
    mfg = part.get("manufacturer", "")
    filename = friendly_filename(display_pn, desc, mfg) + ".pdf"
    output_path = output_dir / filename

    # Strategy 1: Try the datasheet URL from the schematic itself
    schematic_url = part.get("datasheet", "")
    if schematic_url and schematic_url != "~" and "://" in schematic_url:
        print(f"  Trying schematic URL...", file=sys.stderr)
        if download_pdf(schematic_url, str(output_path)):
            size = os.path.getsize(str(output_path))
            vr = verify_datasheet(str(output_path), display_pn, desc, mfg)
            if vr["confidence"] == "wrong":
                print(f"  WARNING: PDF may be wrong datasheet — {vr['details']}",
                      file=sys.stderr)
            result = {
                "file": filename,
                "manufacturer": mfg,
                "description": desc,
                "value": part["value"],
                "datasheet_url": schematic_url,
                "downloaded_date": now,
                "source": "schematic",
                "status": "ok",
                "references": part["references"],
                "size_bytes": size,
                "verification": vr["confidence"],
            }
            if vr["confidence"] == "wrong":
                result["verification_details"] = vr["details"]
            return result

    # Strategy 2: Search Mouser API — try MPN first, then Mouser PN
    time.sleep(delay)  # Rate limit
    search_query = mpn or mouser_pn
    print(f"  Searching Mouser for '{search_query}'...", file=sys.stderr)
    mouser_part = search_mouser(search_query, mouser_api_key)

    # If MPN search failed but we have a Mouser PN, try that
    if not mouser_part and mpn and mouser_pn:
        time.sleep(delay)
        print(f"  MPN not found, trying Mouser PN '{mouser_pn}'...", file=sys.stderr)
        mouser_part = search_mouser(mouser_pn, mouser_api_key)

    mouser_ds_url = ""
    if mouser_part:
        mouser_ds_url = mouser_part.get("DataSheetUrl", "")
        mouser_mfg = mouser_part.get("Manufacturer", mfg)
        mouser_desc = mouser_part.get("Description", "")
        if mouser_desc:
            filename = friendly_filename(display_pn, mouser_desc, mouser_mfg) + ".pdf"
            output_path = output_dir / filename
            desc = mouser_desc
            mfg = mouser_mfg

    # Try Mouser's datasheet URL
    if mouser_ds_url:
        print(f"  Trying Mouser datasheet URL...", file=sys.stderr)
        if download_pdf(mouser_ds_url, str(output_path)):
            size = os.path.getsize(str(output_path))
            vr = verify_datasheet(str(output_path), display_pn, desc, mfg)
            if vr["confidence"] == "wrong":
                print(f"  WARNING: PDF may be wrong datasheet — {vr['details']}",
                      file=sys.stderr)
            result = {
                "file": filename,
                "manufacturer": mfg,
                "description": desc,
                "value": part["value"],
                "datasheet_url": mouser_ds_url,
                "downloaded_date": now,
                "source": "mouser",
                "status": "ok",
                "references": part["references"],
                "size_bytes": size,
                "verification": vr["confidence"],
            }
            if vr["confidence"] == "wrong":
                result["verification_details"] = vr["details"]
            return result

    # Strategy 3: Scrape Mouser product page for datasheet link
    if mouser_part:
        product_url = mouser_part.get("ProductDetailUrl", "")
        if product_url:
            print(f"  Scraping product page for datasheet link...", file=sys.stderr)
            scraped_url = scrape_product_page(product_url)
            if scraped_url:
                print(f"  Found datasheet link on product page", file=sys.stderr)
                if download_pdf(scraped_url, str(output_path)):
                    size = os.path.getsize(str(output_path))
                    vr = verify_datasheet(str(output_path), display_pn, desc, mfg)
                    if vr["confidence"] == "wrong":
                        print(f"  WARNING: PDF may be wrong datasheet — {vr['details']}",
                              file=sys.stderr)
                    result = {
                        "file": filename,
                        "manufacturer": mfg,
                        "description": desc,
                        "value": part["value"],
                        "datasheet_url": scraped_url,
                        "downloaded_date": now,
                        "source": "mouser_scrape",
                        "status": "ok",
                        "references": part["references"],
                        "size_bytes": size,
                        "verification": vr["confidence"],
                    }
                    if vr["confidence"] == "wrong":
                        result["verification_details"] = vr["details"]
                    return result

    # Strategy 4: Try alternative manufacturer sources
    if display_pn:
        print(f"  Trying alternative sources...", file=sys.stderr)
    if display_pn and try_alternative_sources(display_pn, str(output_path)):
        size = os.path.getsize(str(output_path))
        vr = verify_datasheet(str(output_path), display_pn, desc, mfg)
        result = {
            "file": filename,
            "manufacturer": mfg,
            "description": desc,
            "value": part["value"],
            "datasheet_url": mouser_ds_url,
            "downloaded_date": now,
            "source": "alternative",
            "status": "ok",
            "references": part["references"],
            "size_bytes": size,
            "verification": vr["confidence"],
        }
        if vr["confidence"] == "wrong":
            result["verification_details"] = vr["details"]
        return result

    if not mouser_part:
        return {
            "manufacturer": mfg,
            "description": desc,
            "value": part["value"],
            "references": part["references"],
            "status": "not_found",
            "error": f"No Mouser results for '{display_pn}'",
            "last_attempt": now,
        }

    return {
        "manufacturer": mfg,
        "description": desc,
        "value": part["value"],
        "datasheet_url": mouser_ds_url,
        "references": part["references"],
        "status": "failed",
        "error": "All download methods failed",
        "last_attempt": now,
    }
