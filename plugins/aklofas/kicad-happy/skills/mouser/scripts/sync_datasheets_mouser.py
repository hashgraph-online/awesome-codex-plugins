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

import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

# Import from sibling script (same skill)
sys.path.insert(0, str(Path(__file__).parent))
from fetch_datasheet_mouser import (
    download_pdf,
    normalize_url,
    scrape_product_page,
    try_alternative_sources,
    verify_datasheet,
    search_mouser,
    _get_api_key,
)


# ---------------------------------------------------------------------------
# MPN filtering — distinguish real manufacturer part numbers from generic values
# ---------------------------------------------------------------------------

_GENERIC_VALUE_RE = re.compile(
    r"^[\d.]+\s*[pnuμmkMGR]?[FHΩRfhω]?$"
    r"|^[\d.]+\s*[kKmM]?[Ωω]?$"
    r"|^[\d.]+\s*[pnuμm]?[Ff]$"
    r"|^[\d.]+\s*[pnuμm]?[Hh]$"
    r"|^[\d.]+%$"
    r"|^DNP$|^NC$|^N/?A$",
    re.IGNORECASE,
)

_SKIP_TYPES = {
    "test_point", "mounting_hole", "fiducial", "graphic",
    "jumper", "net_tie", "mechanical",
}


def is_real_mpn(mpn: str) -> bool:
    """Return True if the string looks like a real manufacturer part number."""
    mpn = mpn.strip()
    if not mpn or len(mpn) < 3:
        return False
    if _GENERIC_VALUE_RE.match(mpn):
        return False
    has_letter = any(c.isalpha() for c in mpn)
    has_digit = any(c.isdigit() for c in mpn)
    return has_letter and has_digit


# ---------------------------------------------------------------------------
# Filename sanitization — matches convention across distributor skills
# ---------------------------------------------------------------------------

def sanitize_filename(name: str) -> str:
    """Convert a string to a safe filename component (without extension)."""
    name = re.sub(r'[/\\:*?"<>|,;]', "_", name)
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    if len(name) > 200:
        name = name[:200]
    return name


def friendly_filename(mpn: str, description: str = "", manufacturer: str = "") -> str:
    """Build a human-readable filename from MPN and description.

    Examples:
        TPS61023DRLR_Boost_Converter.pdf
        BSS138LT1G_MOSFET_N-CH_50V_200mA.pdf
    """
    base = sanitize_filename(mpn)
    if not description:
        return base
    desc = description.strip()
    if manufacturer and desc.lower().endswith(manufacturer.lower()):
        desc = desc[: -len(manufacturer)].strip().rstrip(",").strip()
    if len(desc) > 80:
        desc = desc[:77].rsplit("_", 1)[0].rsplit(" ", 1)[0]
    desc = sanitize_filename(desc)
    return f"{base}_{desc}" if desc else base


# ---------------------------------------------------------------------------
# Manifest management (manifest.json; legacy index.json read for backward compat)
# ---------------------------------------------------------------------------

MANIFEST_FILENAME = "manifest.json"
LEGACY_MANIFEST_FILENAME = "index.json"


def _manifest_path(out_dir: Path) -> Path:
    new = out_dir / MANIFEST_FILENAME
    old = out_dir / LEGACY_MANIFEST_FILENAME
    if new.exists() or not old.exists():
        return new
    return old


def load_index(path: Path) -> dict:
    """Load existing manifest.json (or legacy index.json) or return empty."""
    path = _manifest_path(path.parent) if path.name in (MANIFEST_FILENAME, LEGACY_MANIFEST_FILENAME) else path
    if path.exists():
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"schematic": "", "last_sync": "", "parts": {}}


def save_index(path: Path, index: dict):
    """Write manifest atomically. Always writes manifest.json; removes any
    legacy index.json sibling after a successful write."""
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    new_path = parent / MANIFEST_FILENAME
    tmp = new_path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(index, f, indent=2)
    tmp.rename(new_path)
    old_path = parent / LEGACY_MANIFEST_FILENAME
    if old_path.exists() and old_path != new_path:
        try:
            old_path.unlink()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Schematic analysis — run analyzer or load pre-computed JSON
# ---------------------------------------------------------------------------

def get_analyzer_output(input_path: Path) -> dict | None:
    """Get analyzer output, either by running the analyzer or loading JSON."""
    if input_path.suffix == ".json":
        with open(input_path, "r") as f:
            return json.load(f)

    if input_path.suffix in (".kicad_sch", ".sch"):
        kicad_scripts = Path(__file__).resolve().parent.parent.parent / "kicad" / "scripts"
        if kicad_scripts.exists():
            sys.path.insert(0, str(kicad_scripts))
            try:
                from analyze_schematic import analyze_schematic
                return analyze_schematic(str(input_path))
            except Exception as e:
                print(f"  Analyzer import failed ({e}), trying subprocess...",
                      file=sys.stderr)

        analyzer = kicad_scripts / "analyze_schematic.py"
        if not analyzer.exists():
            print(f"Error: Cannot find analyze_schematic.py at {analyzer}",
                  file=sys.stderr)
            return None
        try:
            result = subprocess.run(
                [sys.executable, str(analyzer), str(input_path), "--compact"],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                print(f"Error: Analyzer failed: {result.stderr[:500]}",
                      file=sys.stderr)
                return None
            return json.loads(result.stdout)
        except Exception as e:
            print(f"Error: Failed to run analyzer: {e}", file=sys.stderr)
            return None

    print(f"Error: Unsupported input file type: {input_path.suffix}",
          file=sys.stderr)
    return None


# ---------------------------------------------------------------------------
# MPN extraction from BOM
# ---------------------------------------------------------------------------

def extract_parts(analyzer_output: dict) -> list[dict]:
    """Extract unique parts with real MPNs or distributor PNs from analyzer BOM output.

    A part is included if it has at least one of: a real MPN, a Mouser PN,
    a DigiKey PN, an LCSC PN, or an element14 PN. Users set up their KiCad
    projects differently — some only have MPNs, some only have distributor PNs,
    some have both.
    """
    bom = analyzer_output.get("bom", [])
    parts = []

    for entry in bom:
        if entry.get("dnp"):
            continue
        if entry.get("type", "") in _SKIP_TYPES:
            continue

        mpn = entry.get("mpn", "").strip()
        mouser_pn = entry.get("mouser", "").strip()
        digikey_pn = entry.get("digikey", "").strip()
        lcsc_pn = entry.get("lcsc", "").strip()
        element14_pn = entry.get("element14", "").strip()

        # Need at least one identifier to search for a datasheet
        has_mpn = is_real_mpn(mpn)
        has_distributor_pn = bool(mouser_pn or digikey_pn or lcsc_pn or element14_pn)
        # F2: fall back to Value field when MPN is empty but the Value
        # looks MPN-shaped (and the symbol isn't a generic Device:R/C/L).
        mpn_from_value = ""
        if not has_mpn and not has_distributor_pn:
            value = entry.get("value", "").strip()
            lib_id = entry.get("lib_id", "")
            if is_real_mpn(value) and not lib_id.startswith("Device:"):
                mpn_from_value = value
                mpn = value
                has_mpn = True
        if not has_mpn and not has_distributor_pn:
            continue

        parts.append({
            "mpn": mpn if has_mpn else "",
            "manufacturer": entry.get("manufacturer", ""),
            "value": entry.get("value", ""),
            "description": entry.get("description", ""),
            "datasheet": entry.get("datasheet", ""),
            "references": entry.get("references", []),
            "type": entry.get("type", ""),
            "mouser": mouser_pn,
            "digikey": digikey_pn,
            "lcsc": lcsc_pn,
            "element14": element14_pn,
        })

    return parts


def load_mpn_list(path: Path) -> list[dict]:
    """Read MPNs from a text file, one per line (KH-312).

    Skips blank lines, full-line comments (``# ...``), and inline
    ``# ...`` comments. Filters non-MPN strings via ``is_real_mpn()``
    and de-duplicates. Returns minimal part dicts compatible with
    ``extract_parts()`` output — distributor PN fields are empty since
    MPN-list mode drives searches via MPN lookup only.

    Intended for batch workflows (harness, bulk datasheet seeding)
    that don't have a KiCad project to point at.

    Note: MPNs containing a literal ``#`` character are not supported
    (they would be silently truncated by the inline-comment stripper).
    Use the positional schematic/JSON input for such parts instead.
    """
    parts: list[dict] = []
    seen: set[str] = set()
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "#" in line:
                line = line.split("#", 1)[0].strip()
                if not line:
                    continue
            if not is_real_mpn(line):
                print(f"  Skipping '{line}': doesn't look like a real MPN",
                      file=sys.stderr)
                continue
            if line in seen:
                continue
            seen.add(line)
            parts.append({
                "mpn": line,
                "manufacturer": "",
                "value": "",
                "description": "",
                "datasheet": "",
                "references": [],
                "type": "",
                "mouser": "",
                "digikey": "",
                "lcsc": "",
                "element14": "",
            })
    return parts


# ---------------------------------------------------------------------------
# Core sync logic
# ---------------------------------------------------------------------------

def sync_one_part(
    part: dict,
    output_dir: Path,
    mouser_api_key: str,
    index: dict,
    delay: float,
) -> dict:
    """Download datasheet for one part. Returns updated manifest entry."""
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


def sync_datasheets(
    input_path: str | None = None,
    output_dir: str | None = None,
    force: bool = False,
    force_all: bool = False,
    delay: float = 1.0,
    parallel: int = 1,
    dry_run: bool = False,
    as_json: bool = False,
    mpn_list: str | None = None,
) -> dict:
    """Main sync function. Returns summary dict."""
    if input_path is None and mpn_list is None:
        return {"error": "Must provide either input_path or mpn_list"}
    if input_path is not None and mpn_list is not None:
        return {"error": "Cannot provide both input_path and mpn_list"}

    if output_dir:
        out_dir = Path(output_dir)
    elif input_path:
        out_dir = Path(input_path).resolve().parent / "datasheets"
    else:
        out_dir = Path.cwd() / "datasheets"
    out_dir.mkdir(parents=True, exist_ok=True)

    index_path = out_dir / MANIFEST_FILENAME
    index = load_index(index_path)

    if mpn_list:
        mpn_list_path = Path(mpn_list).resolve()
        print(f"Loading MPNs from {mpn_list_path.name}...", file=sys.stderr)
        parts = load_mpn_list(mpn_list_path)
        print(f"Loaded {len(parts)} unique MPNs", file=sys.stderr)
        skipped_no_mpn = 0
    else:
        resolved_input = Path(input_path).resolve()
        print(f"Analyzing {resolved_input.name}...", file=sys.stderr)
        analyzer_output = get_analyzer_output(resolved_input)
        if analyzer_output is None:
            return {"error": "Failed to analyze schematic"}

        parts = extract_parts(analyzer_output)
        all_bom = analyzer_output.get("bom", [])
        skipped_no_mpn = sum(
            1 for e in all_bom
            if not e.get("dnp") and e.get("type", "") not in _SKIP_TYPES
            and not is_real_mpn(e.get("mpn", ""))
        )

        print(f"Found {len(parts)} unique parts with MPNs "
              f"({skipped_no_mpn} skipped without MPN)", file=sys.stderr)

    to_download = []
    already_present = []
    skipped_failed = []

    for part in parts:
        mpn = part["mpn"]
        mouser_pn = part.get("mouser", "")
        display_pn = mpn or mouser_pn
        existing = index.get("parts", {}).get(display_pn, {})
        status = existing.get("status", "")

        if status == "ok":
            old_file = existing.get("file", "")
            if (out_dir / old_file).exists():
                if not force_all:
                    if not dry_run:
                        desc = existing.get("description", "") or part.get("description", "")
                        mfg_name = existing.get("manufacturer", "") or part.get("manufacturer", "")
                        new_file = friendly_filename(display_pn, desc, mfg_name) + ".pdf"
                        if new_file != old_file and not (out_dir / new_file).exists():
                            (out_dir / old_file).rename(out_dir / new_file)
                            existing["file"] = new_file
                            print(f"  Renamed: {old_file} -> {new_file}", file=sys.stderr)
                    already_present.append(display_pn)
                    existing["references"] = part["references"]
                    continue

        if status in ("failed", "not_found", "no_datasheet") and not (force or force_all):
            skipped_failed.append(display_pn)
            continue

        to_download.append(part)

    if dry_run:
        summary = {
            "would_download": [p["mpn"] or p.get("mouser", "") for p in to_download],
            "already_present": already_present,
            "skipped_previous_failures": skipped_failed,
            "skipped_no_mpn": skipped_no_mpn,
        }
        if as_json:
            json.dump(summary, sys.stdout, indent=2)
        else:
            print(f"\nDry run — would download {len(to_download)} datasheets:")
            for p in to_download:
                pn = p["mpn"] or p.get("mouser", "")
                print(f"  {pn} ({p['manufacturer'] or 'unknown mfg'})")
            print(f"Already present: {len(already_present)}")
            print(f"Skipped (previous failures): {len(skipped_failed)}")
            print(f"Skipped (no MPN): {skipped_no_mpn}")
        return summary

    if not to_download:
        msg = f"All {len(already_present)} datasheets up to date."
        if skipped_failed:
            msg += f" {len(skipped_failed)} previous failures (use --force to retry)."
        print(msg, file=sys.stderr)
        index["schematic"] = str(mpn_list or input_path)
        index["last_sync"] = datetime.now(timezone.utc).isoformat()
        save_index(index_path, index)
        return {"downloaded": 0, "already_present": len(already_present),
                "failed": len(skipped_failed)}

    mouser_api_key = _get_api_key()
    if not mouser_api_key:
        return {"error": "MOUSER_SEARCH_API_KEY not set"}

    downloaded = []
    failed = []
    warnings = []

    if parallel > 1:
        lock = threading.Lock()
        counter = [0]

        def _process_part(part):
            display_pn = part["mpn"] or part.get("mouser", "")
            with lock:
                counter[0] += 1
                n = counter[0]
            print(f"[{n}/{len(to_download)}] {display_pn}", file=sys.stderr)

            result = sync_one_part(part, out_dir, mouser_api_key, index, delay)

            with lock:
                index.setdefault("parts", {})[display_pn] = result

                if result["status"] == "ok":
                    downloaded.append(display_pn)
                    vconf = result.get("verification", "")
                    vmark = ""
                    if vconf == "wrong":
                        vmark = " ⚠ WRONG DATASHEET?"
                        warnings.append(display_pn)
                    elif vconf == "unverified":
                        vmark = " (unverified)"
                    print(f"  OK: {result['file']} ({result['size_bytes']:,} bytes){vmark}",
                          file=sys.stderr)
                else:
                    failed.append(display_pn)
                    print(f"  {result['status'].upper()}: {result.get('error', '')}",
                          file=sys.stderr)

                index["schematic"] = str(mpn_list or input_path)
                index["last_sync"] = datetime.now(timezone.utc).isoformat()
                save_index(index_path, index)

        with ThreadPoolExecutor(max_workers=parallel) as executor:
            executor.map(_process_part, to_download)
    else:
        for i, part in enumerate(to_download):
            display_pn = part["mpn"] or part.get("mouser", "")
            print(f"[{i+1}/{len(to_download)}] {display_pn}", file=sys.stderr)

            result = sync_one_part(part, out_dir, mouser_api_key, index, delay)

            index.setdefault("parts", {})[display_pn] = result

            if result["status"] == "ok":
                downloaded.append(display_pn)
                vconf = result.get("verification", "")
                vmark = ""
                if vconf == "wrong":
                    vmark = " ⚠ WRONG DATASHEET?"
                    warnings.append(display_pn)
                elif vconf == "unverified":
                    vmark = " (unverified)"
                print(f"  OK: {result['file']} ({result['size_bytes']:,} bytes){vmark}",
                      file=sys.stderr)
            else:
                failed.append(display_pn)
                print(f"  {result['status'].upper()}: {result.get('error', '')}",
                      file=sys.stderr)

            index["schematic"] = str(mpn_list or input_path)
            index["last_sync"] = datetime.now(timezone.utc).isoformat()
            save_index(index_path, index)

    summary = {
        "downloaded": len(downloaded),
        "already_present": len(already_present),
        "failed": len(failed),
        "verification_warnings": len(warnings),
        "skipped_previous_failures": len(skipped_failed),
        "skipped_no_mpn": skipped_no_mpn,
        "total_parts_with_mpn": len(parts),
        "output_dir": str(out_dir),
        "index_path": str(index_path),
    }

    if as_json:
        json.dump(summary, sys.stdout, indent=2)
    else:
        print(f"\nDatasheet sync complete:", file=sys.stderr)
        print(f"  Downloaded: {len(downloaded)}", file=sys.stderr)
        if downloaded:
            for m in downloaded:
                print(f"    {m}", file=sys.stderr)
        if warnings:
            print(f"  Verification warnings: {len(warnings)}", file=sys.stderr)
            for m in warnings:
                entry = index["parts"].get(m, {})
                detail = entry.get("verification_details", "")
                print(f"    {m}: {detail}", file=sys.stderr)
        print(f"  Already present: {len(already_present)}", file=sys.stderr)
        print(f"  Failed: {len(failed)}", file=sys.stderr)
        if failed:
            for m in failed:
                entry = index["parts"].get(m, {})
                url = entry.get("datasheet_url", "")
                err = entry.get("error", "")
                detail = f" — {url}" if url else f" — {err}"
                print(f"    {m}{detail}", file=sys.stderr)
        if skipped_failed:
            print(f"  Skipped (previous failures, use --force): "
                  f"{len(skipped_failed)}", file=sys.stderr)
        print(f"  Skipped (no MPN): {skipped_no_mpn}", file=sys.stderr)
        print(f"  Output: {out_dir}/", file=sys.stderr)

    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Sync datasheets for a KiCad project via Mouser API",
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "input",
        nargs="?",
        help="Path to .kicad_sch file or pre-computed analyzer JSON",
    )
    input_group.add_argument(
        "--mpn-list",
        metavar="FILE",
        help=("Path to a text file with one MPN per line (KH-312 batch mode). "
              "Skips blank lines and '#' comments. Output defaults to "
              "./datasheets/ in cwd when --output is not given."),
    )
    parser.add_argument(
        "--output", "-o",
        help=("Output directory (default: datasheets/ next to input, "
              "or ./datasheets/ in cwd when --mpn-list is used)"),
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Retry previously failed downloads",
    )
    parser.add_argument(
        "--force-all", action="store_true",
        help="Re-download everything, including already-present files",
    )
    parser.add_argument(
        "--delay", type=float, default=1.0,
        help="Seconds between API calls (default: 1.0)",
    )
    parser.add_argument(
        "--parallel", type=int, default=1,
        help="Number of parallel download workers (default: 1)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be downloaded without doing it",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output summary as JSON",
    )
    args = parser.parse_args()

    result = sync_datasheets(
        input_path=args.input,
        output_dir=args.output,
        force=args.force,
        force_all=args.force_all,
        delay=args.delay,
        parallel=args.parallel,
        dry_run=args.dry_run,
        as_json=args.json,
        mpn_list=args.mpn_list,
    )

    if "error" in result:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
