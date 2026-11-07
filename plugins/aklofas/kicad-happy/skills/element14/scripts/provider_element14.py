"""element14 adapter: auth, search, response accessors, and the provider's sync_one_part strategy chain; the driver is distributor_core.sync. The adapter constants are the per-provider differences the driver reads."""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import _core_path  # noqa: F401
from distributor_core.download import (
    _USER_AGENT,
    normalize_url as _normalize_url,
    download_pdf as _download_pdf,
    note_transport_failure,
    try_alternative_sources,
)
from distributor_core.inputs import mpn_from_value
from distributor_core.verify import downloaded_entry, other_part, pick_requested
from distributor_core.manifest import friendly_filename

_DEFAULT_STORE = "www.newark.com"

NAME = "element14"
DEFAULT_DELAY = 0.5
ID_KEYS = ("element14", "digikey", "mouser", "lcsc")
KEY_PRIORITY = ("element14", "digikey", "mouser", "lcsc")
SEARCH_KEY = "element14"  # the one distributor-specific number this provider can search with
RENAME_PRESENT = False
FAILED_DETAIL_WITH_URL = False
LABELS = {
    "found": "Found {n} unique parts with identifiers ({k} skipped without an MPN or element14 part number)",
    "skipped_key": "skipped_no_identifier",
    "total_key": "total_identified_parts",
    "dry_skipped": "Skipped (no MPN or element14 part number): {k}",
    "summary_skipped": "  Skipped (no MPN or element14 part number): {k}",
}


def preflight(api_key="", store=_DEFAULT_STORE):
    if not api_key:
        api_key = os.environ.get("ELEMENT14_API_KEY", "")
    if not api_key:
        return {"error": "ELEMENT14_API_KEY not set"}
    return {"ctx": (api_key, store)}


def authenticate():
    return {"ctx": None}


def report_tail(out_dir, downloaded, already_present, failed):
    return None


# This provider's datasheet URLs are used as given (no manufacturer redirect unwrapping).
def normalize_url(url):
    return _normalize_url(url, resolve_redirects=False)


def download_pdf(url, output_path):
    return _download_pdf(url, output_path, resolve_redirects=False)


def search_element14(query: str, api_key: str, store: str = _DEFAULT_STORE,
                     allow_family: bool = False, accept=None) -> dict | None:
    """Search element14 API for a part. Returns first match with datasheet URL.

    Accepts MPN, Newark/Farnell SKU, or keyword search terms.
    Detects the query type automatically:
      - If it looks like a numeric/alphanumeric SKU (e.g., "94AK6874"), uses id: search
      - Otherwise uses manuPartNum: search, falling back to any: keyword search

    With ``accept``, a hit it rejects moves on to the next search mode; when no mode gives
    an accepted hit the first rejected one is returned.
    """
    # Determine search mode
    # Newark/Farnell SKUs are typically alphanumeric codes like "94AK6874"
    # MPNs usually have dashes, longer alphanumeric strings
    query = query.strip()

    # MPN search first (most common case), then as distributor SKU, then keyword search
    rejected = None
    for mode in ("manuPartNum", "id", "any"):
        result = _search_element14_raw(f"{mode}:{query}", api_key, store, allow_family)
        if result:
            if accept is None or accept(result):
                return result
            rejected = rejected or result
    return rejected


def _search_element14_raw(term: str, api_key: str, store: str, allow_family: bool = False) -> dict | None:
    """Execute a single element14 API search."""
    params = {
        "term": term,
        "storeInfo.id": store,
        "resultsSettings.offset": "0",
        "resultsSettings.numberOfResults": "5",
        "resultsSettings.responseGroup": "medium",
        "callInfo.responseDataFormat": "JSON",
        "callInfo.apiKey": api_key,
    }
    url = f"https://api.element14.com/catalog/products?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        note_transport_failure(e)
        print(f"[element14] Search failed: {e}", file=sys.stderr)
        return None

    # The response key depends on the search type
    for key in ("manufacturerPartNumberSearchReturn", "keywordSearchReturn",
                "skuSearchReturn", "premierFarnellPartNumberReturn"):
        result_block = data.get(key)
        if result_block:
            break
    else:
        return None

    products = result_block.get("products", [])
    if not products:
        return None

    # Prefer the requested part, then an exact MPN or SKU match
    query_part = term.split(":", 1)[-1].upper() if ":" in term else term.upper()
    hit = pick_requested(products, query_part, _get_mpn, allow_family=allow_family)
    if hit is not None:
        return hit
    for p in products:
        mpn = (p.get("translatedManufacturerPartNumber") or "").upper()
        sku = (p.get("sku") or "").upper()
        if mpn == query_part or sku == query_part:
            return p

    # Return first result
    return products[0]


def _get_datasheet_url(product: dict) -> str:
    """Extract the best datasheet URL from an element14 product."""
    for ds in product.get("datasheets") or []:
        url = ds.get("url", "") if isinstance(ds, dict) else ""
        if url:
            return url
    return ""


def _get_mpn(product: dict) -> str:
    """Extract MPN from product."""
    return product.get("translatedManufacturerPartNumber", "")


def _get_sku(product: dict) -> str:
    """Extract Newark/Farnell SKU from product."""
    return product.get("sku", "")


def _get_manufacturer(product: dict) -> str:
    """Extract manufacturer name from product."""
    return product.get("brandName", "")


def _get_description(product: dict) -> str:
    """Extract description from product."""
    return product.get("displayName", "")


def sync_one_part(
    part: dict,
    output_dir: Path,
    delay: float,
    ctx,
) -> dict:
    """Download datasheet for one part. Returns updated manifest entry."""
    api_key, store = ctx
    mpn = part["mpn"]
    element14_pn = part.get("element14", "")
    now = datetime.now(timezone.utc).isoformat()

    # Use MPN for display/filename if available, otherwise element14 PN
    display_pn = mpn or element14_pn

    desc = part.get("description", "")
    mfg = part.get("manufacturer", "")
    filename = friendly_filename(display_pn, desc, mfg) + ".pdf"
    output_path = output_dir / filename

    # Strategy 1: Try the datasheet URL from the schematic itself
    schematic_url = part.get("datasheet", "")
    if schematic_url and schematic_url != "~" and "://" in schematic_url:
        print(f"  Trying schematic URL...", file=sys.stderr)
        if download_pdf(schematic_url, str(output_path)):
            return downloaded_entry(part, output_path, filename, verify_pn=display_pn,
                                    manufacturer=mfg, description=desc, url=schematic_url,
                                    source="schematic", now=now)

    # Strategy 2: Search element14 API
    # Prefer MPN search (most reliable), fall back to element14 SKU
    search_term = mpn or element14_pn
    time.sleep(delay)
    print(f"  Searching element14 for '{search_term}'...", file=sys.stderr)
    family = mpn_from_value(part)

    def _other(hit, by_pn):
        if hit is None:
            return ""
        return other_part(element14_pn if by_pn else mpn, _get_mpn(hit), [_get_sku(hit)],
                          by_pn=by_pn, allow_family=family, part_mpn=mpn)

    product = search_element14(search_term, api_key, store, family and bool(mpn),
                               accept=lambda hit: not _other(hit, not mpn))
    closest = _other(product, not mpn)
    if closest:
        product = None

    # If MPN search failed but we have an element14 PN, try that
    if product is None and mpn and element14_pn:
        time.sleep(delay)
        print(f"  MPN not found, trying SKU '{element14_pn}'...", file=sys.stderr)
        product = search_element14(element14_pn, api_key, store,
                                   accept=lambda hit: not _other(hit, True))
        mismatch = _other(product, True)
        if mismatch:
            closest, product = mismatch, None

    if product is not None:
        ds_url = _get_datasheet_url(product)
        e14_mpn = _get_mpn(product)
        e14_mfg = _get_manufacturer(product) or mfg
        e14_desc = _get_description(product) or desc
        e14_sku = _get_sku(product)

        # Use the richer element14 data for filename
        effective_pn = e14_mpn or display_pn
        if e14_desc:
            filename = friendly_filename(effective_pn, e14_desc, e14_mfg) + ".pdf"
            output_path = output_dir / filename

        if ds_url:
            print(f"  Downloading from element14...", file=sys.stderr)
            if download_pdf(ds_url, str(output_path)):
                return downloaded_entry(part, output_path, filename, verify_pn=mpn or effective_pn,
                                        manufacturer=e14_mfg, description=e14_desc, url=ds_url,
                                        source="element14", now=now,
                                        vendor_id=("element14", e14_sku))

    # Strategy 3: Try alternative manufacturer sources
    if mpn:
        print(f"  Trying alternative sources...", file=sys.stderr)
        if try_alternative_sources(mpn, str(output_path)):
            return downloaded_entry(part, output_path, filename, verify_pn=mpn, manufacturer=mfg,
                                    description=desc, url="", source="alternative", now=now,
                                    warn=False)

    if product is None:
        return {
            "manufacturer": mfg,
            "description": desc,
            "value": part["value"],
            "references": part["references"],
            "status": "not_found",
            "error": (f"No matching element14 result for '{search_term}'" if closest
                      else f"No element14 results for '{search_term}'")
                     + (f" or '{element14_pn}'" if mpn and element14_pn else "")
                     + (f" (closest: '{closest}', a different part)" if closest else ""),
            "last_attempt": now,
        }

    return {
        "manufacturer": mfg,
        "description": desc,
        "value": part["value"],
        "references": part["references"],
        "status": "failed",
        "error": "No datasheet URL or all download methods failed",
        "last_attempt": now,
    }
