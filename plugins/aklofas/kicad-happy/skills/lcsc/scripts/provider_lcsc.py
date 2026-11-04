"""LCSC adapter: auth, search, response accessors, and the provider's sync_one_part strategy chain — verbatim from fetch_datasheet_lcsc.py / sync_datasheets_lcsc.py; the driver is distributor_core.sync. Adapter constants are the thirteen measured per-provider differences of the old drivers."""

import json
import os
import re
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
from distributor_core.verify import verify_datasheet
from distributor_core.manifest import friendly_filename

NAME = "lcsc"
DEFAULT_DELAY = 0.5
ID_KEYS = ("lcsc", "digikey", "mouser")
KEY_PRIORITY = ("lcsc", "digikey", "mouser")
SKIPPED_COUNTS_IDS = ID_KEYS
RENAME_PRESENT = False
FAILED_DETAIL_WITH_URL = False
# Documentary today: the normalize_url/download_pdf wrappers hard-code the flag; a later version may read it.
NORMALIZE_REDIRECTS = False
LABELS = {
    "found": "Found {n} unique parts with identifiers ({k} skipped without any identifier)",
    "skipped_key": "skipped_no_identifier",
    "total_key": "total_identified_parts",
    "dry_skipped": "Skipped (no identifier): {k}",
    "summary_skipped": "  Skipped (no identifier): {k}",
}


def preflight(**kw):
    return {}


def authenticate():
    return {"ctx": None}


def report_tail(out_dir, downloaded, already_present, failed):
    return None


# This provider's datasheet URLs are used as given (no manufacturer redirect unwrapping).
def normalize_url(url):
    return _normalize_url(url, resolve_redirects=False)


def download_pdf(url, output_path):
    return _download_pdf(url, output_path, resolve_redirects=False)


def _parse_extra(component: dict) -> dict:
    """Parse the 'extra' field, which may be a JSON string or a dict."""
    extra = component.get("extra")
    if extra is None:
        return {}
    if isinstance(extra, str):
        try:
            parsed = json.loads(extra)
            component["extra"] = parsed
            return parsed
        except (json.JSONDecodeError, TypeError):
            return {}
    return extra if isinstance(extra, dict) else {}


def search_lcsc(query: str) -> dict | None:
    """Search jlcsearch API for a part. Returns first match with datasheet URL.

    Accepts MPN, LCSC code (Cxxxxx), or keyword search terms.
    """
    url = f"https://jlcsearch.tscircuit.com/api/search?q={urllib.parse.quote(query)}&limit=5&full=true"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        note_transport_failure(e)
        print(f"[LCSC] Search failed: {e}", file=sys.stderr)
        return None

    components = data.get("components", [])
    if not components:
        return None

    query_upper = query.upper()

    # Parse extra for all components
    for c in components:
        _parse_extra(c)

    # Prefer exact MPN or LCSC code match
    for c in components:
        mpn = c.get("mfr", "")
        extra = c.get("extra") or {}
        lcsc_num = extra.get("number", "") if isinstance(extra, dict) else ""
        if not lcsc_num:
            lcsc_num = f"C{c.get('lcsc', '')}"
        if mpn.upper() == query_upper or lcsc_num.upper() == query_upper:
            return c

    # For short queries (< 6 chars), fuzzy results are unreliable —
    # "1012C" might match "SI1012CR" which is a completely different part.
    # Only return fuzzy matches for longer, more specific queries.
    if len(query.strip()) < 6:
        return None

    # Return first result as fuzzy match
    return components[0]


def search_lcsc_direct(lcsc_code: str) -> dict | None:
    """Query LCSC's wmsc API directly for a part by LCSC code (Cxxxxx).

    This is a fallback when jlcsearch returns no results. The wmsc API
    is unauthenticated and returns product details including datasheet URLs.
    """
    if not re.match(r"^C\d+$", lcsc_code, re.IGNORECASE):
        return None

    url = f"https://wmsc.lcsc.com/ftps/wm/product/detail?productCode={lcsc_code.upper()}"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": _USER_AGENT,
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"[LCSC] Direct lookup failed for {lcsc_code}: {e}", file=sys.stderr)
        return None

    result = data.get("result") or data
    if not result or isinstance(result, str):
        return None

    # Normalize to jlcsearch-compatible dict format
    pdf_url = ""
    pdf_list = result.get("pdfUrl") or result.get("dataSheetUrl") or ""
    if isinstance(pdf_list, str) and pdf_list:
        pdf_url = pdf_list
    elif isinstance(pdf_list, list) and pdf_list:
        pdf_url = pdf_list[0] if isinstance(pdf_list[0], str) else ""

    component = {
        "mfr": result.get("productModel") or result.get("modelName") or "",
        "description": result.get("productDescEn") or result.get("description") or "",
        "datasheet": pdf_url,
        "stock": result.get("stockNumber") or result.get("stockCount") or 0,
        "price": result.get("productPriceList"),
        "lcsc": lcsc_code.lstrip("Cc"),
        "extra": {
            "number": lcsc_code.upper(),
            "mpn": result.get("productModel") or result.get("modelName") or "",
            "description": result.get("productDescEn") or result.get("description") or "",
            "manufacturer": {
                "name": result.get("brandNameEn") or result.get("manufacturer") or "",
            },
            "datasheet": {
                "pdf": pdf_url,
            },
        },
    }

    return component


def enrich_with_wmsc(component: dict) -> dict:
    """Fill datasheet URL / MPN / manufacturer from LCSC's product-detail
    endpoint when a jlcsearch hit lacks them (jlcsearch dropped its `extra`
    block in 2026-09 — KH-405). Keeps jlcsearch's stock/price."""
    if not component or _get_datasheet_url(component):
        return component
    code = _get_lcsc_code(component)
    if not code:
        return component
    direct = search_lcsc_direct(code)
    if not direct:
        return component
    merged = dict(component)
    direct_extra = direct.get("extra") or {}
    component_extra = _parse_extra(component) or {}
    merged_extra = {**direct_extra, **component_extra}
    # The shallow merge above lets component_extra['datasheet'] clobber
    # wmsc's — including an empty {} block a stale jlcsearch hit carries
    # (KH-405). Fall through to wmsc's datasheet block when the
    # component's own has no pdf URL.
    component_ds = component_extra.get("datasheet")
    if not (isinstance(component_ds, dict) and component_ds.get("pdf")):
        direct_ds = direct_extra.get("datasheet")
        if isinstance(direct_ds, dict) and direct_ds.get("pdf"):
            merged_extra["datasheet"] = direct_ds
    merged["extra"] = merged_extra
    if not merged.get("datasheet") and direct.get("datasheet"):
        merged["datasheet"] = direct["datasheet"]
    return merged


def _get_datasheet_url(component: dict) -> str:
    """Extract the best datasheet URL from a jlcsearch component.

    Prefers the direct PDF URL from extra.datasheet.pdf (wmsc.lcsc.com CDN),
    falls back to the top-level datasheet URL (lcsc.com redirect).
    """
    extra = component.get("extra") or {}
    ds = extra.get("datasheet") or {}
    if isinstance(ds, dict):
        pdf_url = ds.get("pdf", "")
        if pdf_url:
            return pdf_url
    # Fallback to top-level
    return component.get("datasheet", "")


def _get_mpn(component: dict) -> str:
    """Extract MPN from component."""
    extra = component.get("extra") or {}
    return extra.get("mpn", "") or component.get("mfr", "")


def _get_lcsc_code(component: dict) -> str:
    """Extract LCSC code (Cxxxxx) from component."""
    extra = component.get("extra") or {}
    num = extra.get("number", "")
    if num:
        return num
    lcsc_id = component.get("lcsc", "")
    return f"C{lcsc_id}" if lcsc_id else ""


def _get_manufacturer(component: dict) -> str:
    """Extract manufacturer name from component."""
    extra = component.get("extra") or {}
    mfg = extra.get("manufacturer") or {}
    if isinstance(mfg, dict):
        return mfg.get("name", "")
    return ""


def _get_description(component: dict) -> str:
    """Extract description from component."""
    extra = component.get("extra") or {}
    return extra.get("description", "") or component.get("description", "")


def sync_one_part(
    part: dict,
    output_dir: Path,
    index: dict,
    delay: float,
    ctx,
) -> dict:
    """Download datasheet for one part. Returns updated manifest entry."""
    mpn = part["mpn"]
    lcsc_pn = part.get("lcsc", "")
    now = datetime.now(timezone.utc).isoformat()

    # Use MPN for display/filename if available, otherwise LCSC code
    display_pn = mpn or lcsc_pn

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

    # Strategy 2: Search jlcsearch API
    # Prefer LCSC code (exact match) over MPN keyword search
    search_term = lcsc_pn or mpn
    time.sleep(delay)
    print(f"  Searching LCSC for '{search_term}'...", file=sys.stderr)
    component = search_lcsc(search_term)
    component = enrich_with_wmsc(component)

    # If LCSC code search failed but we have an MPN, try that
    if component is None and lcsc_pn and mpn:
        time.sleep(delay)
        print(f"  LCSC code not found, trying MPN '{mpn}'...", file=sys.stderr)
        component = search_lcsc(mpn)
        component = enrich_with_wmsc(component)

    if component is not None:
        ds_url = _get_datasheet_url(component)
        lcsc_mpn = _get_mpn(component)
        lcsc_mfg = _get_manufacturer(component) or mfg
        lcsc_desc = _get_description(component) or desc
        lcsc_code = _get_lcsc_code(component)

        # Use the richer LCSC data for filename
        effective_pn = lcsc_mpn or display_pn
        if lcsc_desc:
            filename = friendly_filename(effective_pn, lcsc_desc, lcsc_mfg) + ".pdf"
            output_path = output_dir / filename

        if ds_url:
            print(f"  Downloading from LCSC CDN...", file=sys.stderr)
            if download_pdf(ds_url, str(output_path)):
                size = os.path.getsize(str(output_path))
                vr = verify_datasheet(str(output_path), effective_pn, lcsc_desc, lcsc_mfg)
                if vr["confidence"] == "wrong":
                    print(f"  WARNING: PDF may be wrong datasheet — {vr['details']}",
                          file=sys.stderr)
                result = {
                    "file": filename,
                    "manufacturer": lcsc_mfg,
                    "description": lcsc_desc,
                    "value": part["value"],
                    "datasheet_url": ds_url,
                    "downloaded_date": now,
                    "source": "lcsc",
                    "lcsc": lcsc_code,
                    "status": "ok",
                    "references": part["references"],
                    "size_bytes": size,
                    "verification": vr["confidence"],
                }
                if vr["confidence"] == "wrong":
                    result["verification_details"] = vr["details"]
                return result

    # Strategy 3: Try alternative manufacturer sources
    if mpn:
        print(f"  Trying alternative sources...", file=sys.stderr)
        if try_alternative_sources(mpn, str(output_path)):
            size = os.path.getsize(str(output_path))
            vr = verify_datasheet(str(output_path), mpn, desc, mfg)
            result = {
                "file": filename,
                "manufacturer": mfg,
                "description": desc,
                "value": part["value"],
                "datasheet_url": "",
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

    if component is None:
        return {
            "manufacturer": mfg,
            "description": desc,
            "value": part["value"],
            "references": part["references"],
            "status": "not_found",
            "error": f"No LCSC results for '{search_term}'" + (f" or '{mpn}'" if lcsc_pn and mpn else ""),
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
