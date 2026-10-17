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
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request

_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"

# Try to import optional dependencies; graceful fallback if not installed
try:
    import requests as _requests
except ImportError:
    _requests = None

try:
    from playwright.sync_api import sync_playwright as _sync_playwright
except ImportError:
    _sync_playwright = None


def _friendly_filename(mpn: str, description: str = "") -> str:
    """Build a human-readable filename (no extension) from MPN + description."""
    def _sanitize(s):
        s = re.sub(r'[/\\:*?"<>|,;]', "_", s)
        s = re.sub(r"\s+", "_", s)
        return re.sub(r"_+", "_", s).strip("_")

    base = _sanitize(mpn)
    if not description:
        return base
    desc = description.strip()
    if len(desc) > 80:
        desc = desc[:77].rsplit(" ", 1)[0]
    desc = _sanitize(desc)
    return f"{base}_{desc}" if desc else base


# ---------------------------------------------------------------------------
# jlcsearch API
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# URL normalization
# ---------------------------------------------------------------------------

def normalize_url(url: str) -> str:
    """Normalize datasheet URL for download."""
    if url.startswith("//"):
        url = "https:" + url
    return url


# ---------------------------------------------------------------------------
# Download functions
# ---------------------------------------------------------------------------

def download_pdf(url: str, output_path: str) -> bool:
    """Download a PDF from a URL, trying multiple methods.

    Returns True if a valid PDF was downloaded.
    """
    url = normalize_url(url)

    methods = []
    if _requests is not None:
        methods.append(("requests", _download_requests))
    methods.append(("urllib", _download_urllib))
    if _sync_playwright is not None:
        methods.append(("playwright", _download_playwright))

    for name, fn in methods:
        try:
            if fn(url, output_path):
                with open(output_path, "rb") as f:
                    header = f.read(8)
                if header.startswith(b"%PDF"):
                    size = os.path.getsize(output_path)
                    print(f"Downloaded {size:,} bytes via {name}: {output_path}")
                    return True
                else:
                    os.remove(output_path)
        except Exception:
            if os.path.exists(output_path):
                os.remove(output_path)
            continue

    return False


def _download_requests(url: str, output_path: str) -> bool:
    """Download using the requests library."""
    resp = _requests.get(
        url,
        headers={"User-Agent": _USER_AGENT},
        timeout=20,
        allow_redirects=True,
    )
    resp.raise_for_status()
    if len(resp.content) == 0:
        return False
    with open(output_path, "wb") as f:
        f.write(resp.content)
    return True


def _download_urllib(url: str, output_path: str) -> bool:
    """Download using Python urllib (fallback)."""
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        with open(output_path, "wb") as f:
            shutil.copyfileobj(resp, f)
    return os.path.exists(output_path) and os.path.getsize(output_path) > 0


def _download_playwright(url: str, output_path: str) -> bool:
    """Download using Playwright headless browser (last resort)."""
    with _sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            try:
                with page.expect_download(timeout=15000) as dl_info:
                    page.goto(url, timeout=15000, wait_until="domcontentloaded")
                download = dl_info.value
                download.save_as(output_path)
                return os.path.exists(output_path) and os.path.getsize(output_path) > 0
            except Exception:
                pass

            resp = page.goto(url, timeout=20000, wait_until="domcontentloaded")
            if resp is None:
                return False
            body = resp.body()
            if body and body[:4] == b"%PDF":
                with open(output_path, "wb") as f:
                    f.write(body)
                return True
            return False
        finally:
            page.close()
            browser.close()


def try_alternative_sources(mpn: str, output_path: str) -> bool:
    """Try alternative datasheet sources when LCSC URL fails."""
    alternatives = []
    mpn_upper = mpn.upper()

    # Microchip direct URL pattern
    if any(x in mpn_upper for x in ("ATMEGA", "ATTINY", "PIC", "SAMD", "SAM")):
        alternatives.append(
            f"https://ww1.microchip.com/downloads/aemDocuments/documents/MCU08/ProductDocuments/DataSheets/{mpn}-DataSheet.pdf"
        )

    for alt_url in alternatives:
        if download_pdf(alt_url, output_path):
            return True

    return False


# ---------------------------------------------------------------------------
# PDF verification
# ---------------------------------------------------------------------------

def _extract_pdf_text(pdf_path: str, max_pages: int = 3) -> str:
    """Extract text from the first few pages of a PDF."""
    try:
        result = subprocess.run(
            ["pdftotext", "-l", str(max_pages), pdf_path, "-"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    try:
        with open(pdf_path, "rb") as f:
            raw = f.read(200_000)
        strings = re.findall(rb"[\x20-\x7e]{4,}", raw)
        return " ".join(s.decode("ascii", errors="ignore") for s in strings)
    except Exception:
        return ""


def verify_datasheet(
    pdf_path: str,
    mpn: str,
    description: str = "",
    manufacturer: str = "",
) -> dict:
    """Verify a downloaded PDF is the correct datasheet."""
    text = _extract_pdf_text(pdf_path)
    if not text or len(text) < 50:
        return {
            "verified": False, "confidence": "unverified",
            "mpn_found": False, "manufacturer_found": False,
            "keyword_hits": 0, "keyword_total": 0,
            "details": "Could not extract text from PDF",
        }

    text_upper = text.upper()
    mpn_upper = mpn.upper()
    mpn_found = mpn_upper in text_upper

    if not mpn_found:
        base_mpn = re.sub(
            r"(DRLR|DRL|DGKR|DGK|DCKR|DCK|DBVR|DBV|PWPR|PWP|RGER|RGE|"
            r"RGTR|RGT|NRND|TR|CT|ND|LT1G|LT3G|BK|PBF|-ND)$",
            "", mpn_upper,
        )
        if base_mpn and len(base_mpn) >= 4 and base_mpn != mpn_upper:
            mpn_found = base_mpn in text_upper

    mfg_found = False
    if manufacturer:
        mfg_upper = manufacturer.upper()
        mfg_found = mfg_upper in text_upper
        if not mfg_found:
            first_word = mfg_upper.split()[0] if " " in mfg_upper else ""
            if first_word and len(first_word) >= 4:
                mfg_found = first_word in text_upper

    keywords = []
    if description:
        skip = {"the", "a", "an", "for", "and", "or", "with", "in", "to",
                "of", "at", "by", "on", "no", "w", "smd", "smt"}
        for word in re.split(r"[\s/,_-]+", description):
            w = word.strip().upper()
            if len(w) >= 3 and w not in skip and not re.match(r"^\d+$", w):
                keywords.append(w)

    keyword_hits = sum(1 for kw in keywords if kw in text_upper) if keywords else 0
    keyword_total = len(keywords)

    if mpn_found:
        confidence = "verified"
        details = f"MPN '{mpn}' found in PDF text"
    elif mfg_found and keyword_hits >= max(1, keyword_total // 2):
        confidence = "likely"
        details = (f"MPN not found but manufacturer '{manufacturer}' present "
                   f"with {keyword_hits}/{keyword_total} description keywords")
    elif keyword_hits >= max(2, keyword_total * 2 // 3):
        confidence = "likely"
        details = f"{keyword_hits}/{keyword_total} description keywords found"
    elif keyword_hits == 0 and keyword_total >= 3 and not mfg_found:
        confidence = "wrong"
        details = (f"No MPN, manufacturer, or description keywords found in PDF "
                   f"(0/{keyword_total} keywords)")
    else:
        confidence = "unverified"
        details = (f"MPN not found; {keyword_hits}/{keyword_total} keywords, "
                   f"manufacturer {'found' if mfg_found else 'not found'}")

    return {
        "verified": mpn_found, "confidence": confidence,
        "mpn_found": mpn_found, "manufacturer_found": mfg_found,
        "keyword_hits": keyword_hits, "keyword_total": keyword_total,
        "details": details,
    }


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
