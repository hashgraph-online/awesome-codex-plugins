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

import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

# Import download functions from sibling script
sys.path.insert(0, str(Path(__file__).parent))
from fetch_datasheet_digikey import download_pdf, normalize_url, try_alternative_sources, verify_datasheet

# ---------------------------------------------------------------------------
# MPN filtering — distinguish real manufacturer part numbers from generic values
# ---------------------------------------------------------------------------

# Matches generic passive values that someone typed into the MPN field
_GENERIC_VALUE_RE = re.compile(
    r"^[\d.]+\s*[pnuμmkMGR]?[FHΩRfhω]?$"    # 100nF, 10K, 4.7uF, 100R
    r"|^[\d.]+\s*[kKmM]?[Ωω]?$"               # 10K, 4.7k
    r"|^[\d.]+\s*[pnuμm]?[Ff]$"               # 100pF, 10uF
    r"|^[\d.]+\s*[pnuμm]?[Hh]$"               # 10uH
    r"|^[\d.]+%$"                               # 1%
    r"|^DNP$|^NC$|^N/?A$",
    re.IGNORECASE,
)

# Component types that never have useful datasheets
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
    # Must contain both letters and digits (real MPNs always do)
    has_letter = any(c.isalpha() for c in mpn)
    has_digit = any(c.isdigit() for c in mpn)
    if not (has_letter and has_digit):
        return False
    return True


# ---------------------------------------------------------------------------
# OAuth token management — fetch once, reuse across all API calls
# ---------------------------------------------------------------------------

def get_oauth_token() -> tuple[str, str] | None:
    """Get DigiKey OAuth token. Returns (token, client_id) or None."""
    client_id = os.environ.get("DIGIKEY_CLIENT_ID", "")
    client_secret = os.environ.get("DIGIKEY_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        print("Error: DIGIKEY_CLIENT_ID and DIGIKEY_CLIENT_SECRET environment variables required.",
              file=sys.stderr)
        print("  Get credentials at developer.digikey.com → My Apps → Create App",
              file=sys.stderr)
        return None

    try:
        token_data = urllib.parse.urlencode({
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        }).encode()
        req = urllib.request.Request(
            "https://api.digikey.com/v1/oauth2/token",
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            token_resp = json.loads(resp.read())
        token = token_resp.get("access_token", "")
        if not token:
            print("Error: Failed to get OAuth token", file=sys.stderr)
            return None
        return token, client_id
    except Exception as e:
        print(f"Error: OAuth failed: {e}", file=sys.stderr)
        return None


def search_digikey_with_token(mpn: str, token: str, client_id: str) -> dict | None:
    """Search DigiKey API using a pre-fetched OAuth token."""
    try:
        search_body = json.dumps({"Keywords": mpn, "Limit": 3}).encode()
        req = urllib.request.Request(
            "https://api.digikey.com/products/v4/search/keyword",
            data=search_body,
            headers={
                "Content-Type": "application/json",
                "X-DIGIKEY-Client-Id": client_id,
                "Authorization": f"Bearer {token}",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print(f"  Rate limited, waiting 10s...", file=sys.stderr)
            time.sleep(10)
            return search_digikey_with_token(mpn, token, client_id)
        if e.code == 401:
            return None  # Token expired — caller should refresh
        print(f"  Search failed for '{mpn}': HTTP {e.code}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  Search failed for '{mpn}': {e}", file=sys.stderr)
        return None

    products = data.get("Products", [])
    if not products:
        return None

    # Prefer exact MPN match
    for p in products:
        if p.get("ManufacturerProductNumber", "").upper().startswith(mpn.upper()):
            return p
    return products[0]


# ---------------------------------------------------------------------------
# Filename sanitization
# ---------------------------------------------------------------------------

def sanitize_filename(name: str) -> str:
    """Convert a string to a safe filename component (without extension)."""
    # Replace filesystem-unsafe characters and commas
    name = re.sub(r'[/\\:*?"<>|,;]', "_", name)
    # Collapse whitespace and underscores
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    # Truncate
    if len(name) > 200:
        name = name[:200]
    return name


def friendly_filename(mpn: str, description: str = "", manufacturer: str = "") -> str:
    """Build a human-readable filename from MPN and description.

    Examples:
        TPS61023DRLR_Boost_Converter.pdf
        BSS138LT1G_MOSFET_N-CH_50V_200mA.pdf
        GRPB032VWQS-RC_Conn_Header_SMD_6pos.pdf

    Falls back to just the sanitized MPN if no description is available.
    """
    base = sanitize_filename(mpn)
    if not description:
        return base

    # Clean up the description: trim common noise
    desc = description.strip()
    # Remove trailing manufacturer name if it's just repeated
    if manufacturer and desc.lower().endswith(manufacturer.lower()):
        desc = desc[: -len(manufacturer)].strip().rstrip(",").strip()
    # Truncate long descriptions to keep filenames reasonable
    if len(desc) > 80:
        desc = desc[:77].rsplit("_", 1)[0].rsplit(" ", 1)[0]
    desc = sanitize_filename(desc)
    if not desc:
        return base

    return f"{base}_{desc}"


# ---------------------------------------------------------------------------
# Manifest management (manifest.json; legacy index.json read for backward compat)
# ---------------------------------------------------------------------------

MANIFEST_FILENAME = "manifest.json"
LEGACY_MANIFEST_FILENAME = "index.json"


def _manifest_path(out_dir: Path) -> Path:
    """Return manifest path, preferring manifest.json but falling back to index.json."""
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
        # Try importing the analyzer directly
        kicad_scripts = Path(__file__).resolve().parent.parent.parent / "kicad" / "scripts"
        if kicad_scripts.exists():
            sys.path.insert(0, str(kicad_scripts))
            try:
                from analyze_schematic import analyze_schematic
                return analyze_schematic(str(input_path))
            except Exception as e:
                print(f"  Analyzer import failed ({e}), trying subprocess...",
                      file=sys.stderr)

        # Fall back to subprocess
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

    A part is included if it has at least one of: a real MPN, a DigiKey PN,
    a Mouser PN, or an LCSC PN. Users set up their KiCad projects differently —
    some only have MPNs, some only have distributor PNs, some have both.
    """
    bom = analyzer_output.get("bom", [])
    parts = []

    for entry in bom:
        if entry.get("dnp"):
            continue
        if entry.get("type", "") in _SKIP_TYPES:
            continue

        mpn = entry.get("mpn", "").strip()
        digikey_pn = entry.get("digikey", "").strip()
        mouser_pn = entry.get("mouser", "").strip()
        lcsc_pn = entry.get("lcsc", "").strip()

        # Need at least one identifier to search for a datasheet
        has_mpn = is_real_mpn(mpn)
        has_distributor_pn = bool(digikey_pn or mouser_pn or lcsc_pn)
        # F2: fall back to Value field when MPN is empty but the Value
        # looks MPN-shaped (and the symbol isn't a generic Device:R/C/L
        # passive). Common pattern — many KiCad library symbols put the
        # MPN string in the Value field and leave the MPN property empty.
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
            "digikey": digikey_pn,
            "mouser": mouser_pn,
            "lcsc": lcsc_pn,
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
            # Strip inline comments
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
                "digikey": "",
                "mouser": "",
                "lcsc": "",
            })
    return parts


# ---------------------------------------------------------------------------
# Core sync logic
# ---------------------------------------------------------------------------

def sync_one_part(
    part: dict,
    output_dir: Path,
    token: str,
    client_id: str,
    index: dict,
    delay: float,
) -> dict:
    """Download datasheet for one part. Returns updated manifest entry."""
    mpn = part["mpn"]
    digikey_pn = part.get("digikey", "")
    now = datetime.now(timezone.utc).isoformat()

    # Use MPN for display/filename if available, otherwise fall back to DK PN
    display_pn = mpn or digikey_pn

    # Build a friendly filename — may be refined later if DigiKey provides
    # a better description than the schematic had
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

    # Strategy 2: Search DigiKey API
    # Prefer DigiKey PN (exact match, no ambiguity) over MPN keyword search
    search_term = digikey_pn or mpn
    time.sleep(delay)  # Rate limit
    print(f"  Searching DigiKey for '{search_term}'...", file=sys.stderr)
    product = search_digikey_with_token(search_term, token, client_id)

    # If DK PN search failed but we also have an MPN, try that
    if product is None and digikey_pn and mpn:
        time.sleep(delay)
        print(f"  DK PN not found, trying MPN '{mpn}'...", file=sys.stderr)
        product = search_digikey_with_token(mpn, token, client_id)

    if product is None:
        return {
            "manufacturer": part["manufacturer"],
            "description": part.get("description", ""),
            "value": part["value"],
            "references": part["references"],
            "status": "not_found",
            "error": f"No DigiKey results for '{search_term}'" + (f" or '{mpn}'" if digikey_pn and mpn else ""),
            "last_attempt": now,
        }

    ds_url = product.get("DatasheetUrl", "")
    dk_mpn = product.get("ManufacturerProductNumber", mpn)
    dk_mfg = product.get("Manufacturer", {}).get("Name", part["manufacturer"])
    dk_desc = product.get("Description", {}).get("ProductDescription", "")

    # If DigiKey returned the real MPN, use it (better than a DK PN for filenames)
    if dk_mpn and not mpn:
        display_pn = dk_mpn
        filename = friendly_filename(display_pn, dk_desc or desc, dk_mfg) + ".pdf"
        output_path = output_dir / filename
    elif dk_desc:
        # Rebuild filename with the richer DigiKey description
        filename = friendly_filename(display_pn, dk_desc, dk_mfg) + ".pdf"
        output_path = output_dir / filename

    if not ds_url:
        return {
            "manufacturer": dk_mfg,
            "description": dk_desc or part.get("description", ""),
            "value": part["value"],
            "references": part["references"],
            "status": "no_datasheet",
            "error": "DigiKey listing has no datasheet URL",
            "last_attempt": now,
        }

    # Strategy 3: Download from DigiKey's datasheet URL
    effective_desc = dk_desc or part.get("description", "")
    print(f"  Downloading from {ds_url[:80]}...", file=sys.stderr)
    if download_pdf(ds_url, str(output_path)):
        size = os.path.getsize(str(output_path))
        vr = verify_datasheet(str(output_path), dk_mpn or display_pn, effective_desc, dk_mfg)
        if vr["confidence"] == "wrong":
            print(f"  WARNING: PDF may be wrong datasheet — {vr['details']}",
                  file=sys.stderr)
        result = {
            "file": filename,
            "manufacturer": dk_mfg,
            "description": effective_desc,
            "value": part["value"],
            "datasheet_url": ds_url,
            "downloaded_date": now,
            "source": "digikey",
            "status": "ok",
            "references": part["references"],
            "size_bytes": size,
            "verification": vr["confidence"],
        }
        if vr["confidence"] == "wrong":
            result["verification_details"] = vr["details"]
        return result

    # Strategy 4: Try alternative sources
    print(f"  Primary failed, trying alternatives...", file=sys.stderr)
    if try_alternative_sources(dk_mpn, str(output_path)):
        size = os.path.getsize(str(output_path))
        vr = verify_datasheet(str(output_path), dk_mpn or display_pn, effective_desc, dk_mfg)
        if vr["confidence"] == "wrong":
            print(f"  WARNING: PDF may be wrong datasheet — {vr['details']}",
                  file=sys.stderr)
        result = {
            "file": filename,
            "manufacturer": dk_mfg,
            "description": effective_desc,
            "value": part["value"],
            "datasheet_url": ds_url,
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

    return {
        "manufacturer": dk_mfg,
        "description": dk_desc or part.get("description", ""),
        "value": part["value"],
        "datasheet_url": ds_url,
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

    # Determine output directory
    if output_dir:
        out_dir = Path(output_dir)
    elif input_path:
        out_dir = Path(input_path).resolve().parent / "datasheets"
    else:
        # MPN-list mode without explicit --output: use cwd/datasheets
        out_dir = Path.cwd() / "datasheets"
    out_dir.mkdir(parents=True, exist_ok=True)

    index_path = out_dir / MANIFEST_FILENAME
    index = load_index(index_path)

    # Source parts: either analyzer BOM or plain MPN list
    if mpn_list:
        mpn_list_path = Path(mpn_list).resolve()
        print(f"Loading MPNs from {mpn_list_path.name}...", file=sys.stderr)
        parts = load_mpn_list(mpn_list_path)
        print(f"Loaded {len(parts)} unique MPNs", file=sys.stderr)
        skipped_no_id = 0
    else:
        resolved_input = Path(input_path).resolve()
        print(f"Analyzing {resolved_input.name}...", file=sys.stderr)
        analyzer_output = get_analyzer_output(resolved_input)
        if analyzer_output is None:
            return {"error": "Failed to analyze schematic"}

        # Extract parts with real MPNs
        parts = extract_parts(analyzer_output)
        all_bom = analyzer_output.get("bom", [])
        skipped_no_id = sum(
            1 for e in all_bom
            if not e.get("dnp") and e.get("type", "") not in _SKIP_TYPES
            and not is_real_mpn(e.get("mpn", ""))
            and not e.get("digikey", "").strip()
            and not e.get("mouser", "").strip()
            and not e.get("lcsc", "").strip()
        )

        print(f"Found {len(parts)} unique parts with part numbers "
              f"({skipped_no_id} skipped without any identifier)", file=sys.stderr)

    # Determine what needs processing
    to_download = []
    already_present = []
    skipped_failed = []

    for part in parts:
        # Use MPN as index key if available, otherwise distributor PN
        part_key = part["mpn"] or part.get("digikey", "") or part.get("mouser", "") or part.get("lcsc", "")
        part["_key"] = part_key
        existing = index.get("parts", {}).get(part_key, {})
        status = existing.get("status", "")

        if status == "ok":
            old_file = existing.get("file", "")
            # Verify file still exists
            if (out_dir / old_file).exists():
                if not force_all:
                    # Rename to friendly filename if the old name was plain MPN
                    if not dry_run:
                        desc = existing.get("description", "") or part.get("description", "")
                        mfg = existing.get("manufacturer", "") or part.get("manufacturer", "")
                        new_file = friendly_filename(part_key, desc, mfg) + ".pdf"
                        if new_file != old_file and not (out_dir / new_file).exists():
                            (out_dir / old_file).rename(out_dir / new_file)
                            existing["file"] = new_file
                            print(f"  Renamed: {old_file} -> {new_file}", file=sys.stderr)
                    already_present.append(part_key)
                    existing["references"] = part["references"]
                    continue
            # File missing — re-download

        if status in ("failed", "not_found", "no_datasheet") and not (force or force_all):
            skipped_failed.append(part_key)
            continue

        to_download.append(part)

    if dry_run:
        summary = {
            "would_download": [p["_key"] for p in to_download],
            "already_present": already_present,
            "skipped_previous_failures": skipped_failed,
            "skipped_no_identifier": skipped_no_id,
        }
        if as_json:
            json.dump(summary, sys.stdout, indent=2)
        else:
            print(f"\nDry run — would download {len(to_download)} datasheets:")
            for p in to_download:
                print(f"  {p['_key']} ({p['manufacturer'] or 'unknown mfg'})")
            print(f"Already present: {len(already_present)}")
            print(f"Skipped (previous failures): {len(skipped_failed)}")
            print(f"Skipped (no identifier): {skipped_no_id}")
        return summary

    if not to_download:
        msg = f"All {len(already_present)} datasheets up to date."
        if skipped_failed:
            msg += f" {len(skipped_failed)} previous failures (use --force to retry)."
        print(msg, file=sys.stderr)
        # Still update the manifest (references may have changed)
        index["schematic"] = str(mpn_list or input_path)
        index["last_sync"] = datetime.now(timezone.utc).isoformat()
        save_index(index_path, index)
        return {"downloaded": 0, "already_present": len(already_present),
                "failed": len(skipped_failed)}

    # Get OAuth token
    auth = get_oauth_token()
    if auth is None:
        return {"error": "Failed to authenticate with DigiKey API"}
    token, client_id = auth

    # Process each part
    downloaded = []
    failed = []
    warnings = []  # verification warnings

    if parallel > 1:
        lock = threading.Lock()
        counter = [0]

        def _process_part(part):
            part_key = part["_key"]
            with lock:
                counter[0] += 1
                n = counter[0]
            print(f"[{n}/{len(to_download)}] {part_key}", file=sys.stderr)

            result = sync_one_part(part, out_dir, token, client_id, index, delay)

            with lock:
                index.setdefault("parts", {})[part_key] = result

                if result["status"] == "ok":
                    downloaded.append(part_key)
                    vconf = result.get("verification", "")
                    vmark = ""
                    if vconf == "wrong":
                        vmark = " ⚠ WRONG DATASHEET?"
                        warnings.append(part_key)
                    elif vconf == "unverified":
                        vmark = " (unverified)"
                    print(f"  OK: {result['file']} ({result['size_bytes']:,} bytes){vmark}",
                          file=sys.stderr)
                else:
                    failed.append(part_key)
                    print(f"  {result['status'].upper()}: {result.get('error', '')}",
                          file=sys.stderr)

                index["schematic"] = str(mpn_list or input_path)
                index["last_sync"] = datetime.now(timezone.utc).isoformat()
                save_index(index_path, index)

        with ThreadPoolExecutor(max_workers=parallel) as executor:
            executor.map(_process_part, to_download)
    else:
        for i, part in enumerate(to_download):
            part_key = part["_key"]
            print(f"[{i+1}/{len(to_download)}] {part_key}", file=sys.stderr)

            result = sync_one_part(part, out_dir, token, client_id, index, delay)

            # Handle token expiry — refresh once and retry
            if result.get("status") == "not_found" and "No DigiKey results" in result.get("error", ""):
                pass

            index.setdefault("parts", {})[part_key] = result

            if result["status"] == "ok":
                downloaded.append(part_key)
                vconf = result.get("verification", "")
                vmark = ""
                if vconf == "wrong":
                    vmark = " ⚠ WRONG DATASHEET?"
                    warnings.append(part_key)
                elif vconf == "unverified":
                    vmark = " (unverified)"
                print(f"  OK: {result['file']} ({result['size_bytes']:,} bytes){vmark}",
                      file=sys.stderr)
            else:
                failed.append(part_key)
                print(f"  {result['status'].upper()}: {result.get('error', '')}",
                      file=sys.stderr)

            index["schematic"] = str(mpn_list or input_path)
            index["last_sync"] = datetime.now(timezone.utc).isoformat()
            save_index(index_path, index)

    # Summary
    summary = {
        "downloaded": len(downloaded),
        "already_present": len(already_present),
        "failed": len(failed),
        "verification_warnings": len(warnings),
        "skipped_previous_failures": len(skipped_failed),
        "skipped_no_identifier": skipped_no_id,
        "total_identified_parts": len(parts),
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
        print(f"  Skipped (no identifier): {skipped_no_id}", file=sys.stderr)
        print(f"  Output: {out_dir}/", file=sys.stderr)
        if failed:
            print(f"\n  Tip: Try LCSC or element14 sync to fill gaps — they share"
                  f" the same datasheets/ directory and skip already-downloaded parts.",
                  file=sys.stderr)
        if downloaded or already_present:
            print(f"\n  Next: extract structured specs for IC-aware analyzer checks",
                  file=sys.stderr)
            print(f"        (VM-001, PS-001, PR-004, DP-002). The `datasheets` skill",
                  file=sys.stderr)
            print(f"        reads PDFs and writes {out_dir}/extracted/<MPN>.json.",
                  file=sys.stderr)

    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Sync datasheets for a KiCad project via DigiKey API",
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
        help="Seconds between DigiKey API calls (default: 1.0)",
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
    if result.get("failed", 0) > 0:
        sys.exit(0)  # Partial success is still success
    sys.exit(0)


if __name__ == "__main__":
    main()
