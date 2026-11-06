"""DigiKey adapter: auth, search, response accessors, and the provider's sync_one_part strategy chain — verbatim from fetch_datasheet_digikey.py / sync_datasheets_digikey.py; the driver is distributor_core.sync. Adapter constants are the thirteen measured per-provider differences of the old drivers."""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import _core_path  # noqa: F401
from distributor_core.download import download_pdf, note_transport_failure, try_alternative_sources
from distributor_core.verify import verify_datasheet
from distributor_core.manifest import friendly_filename

NAME = "digikey"
DEFAULT_DELAY = 1.0
ID_KEYS = ("digikey", "mouser", "lcsc")
KEY_PRIORITY = ("digikey", "mouser", "lcsc")
SKIPPED_COUNTS_IDS = ID_KEYS
RENAME_PRESENT = True
FAILED_DETAIL_WITH_URL = True
# Documentary today: the normalize_url/download_pdf wrappers hard-code the flag; a later version may read it.
NORMALIZE_REDIRECTS = True
LABELS = {
    "found": "Found {n} unique parts with part numbers ({k} skipped without any identifier)",
    "skipped_key": "skipped_no_identifier",
    "total_key": "total_identified_parts",
    "dry_skipped": "Skipped (no identifier): {k}",
    "summary_skipped": "  Skipped (no identifier): {k}",
}


def preflight(**kw):
    return {}


def authenticate():
    auth = get_oauth_token()
    return {"error": "Failed to authenticate with DigiKey API"} if auth is None else {"ctx": auth}


def report_tail(out_dir, downloaded, already_present, failed):
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


def _get_digikey_token() -> str | None:
    """Get a DigiKey OAuth token, using a cached version if still valid.

    Caches the token to a temp file with a 9-minute TTL (tokens last 10 minutes).
    """
    import tempfile
    import time

    client_id = os.environ.get("DIGIKEY_CLIENT_ID", "")
    client_secret = os.environ.get("DIGIKEY_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        print("Error: DIGIKEY_CLIENT_ID and DIGIKEY_CLIENT_SECRET required", file=sys.stderr)
        return None

    cache_path = os.path.join(tempfile.gettempdir(), "digikey_token_cache.json")

    # Check cache
    try:
        if os.path.exists(cache_path):
            with open(cache_path) as f:
                cached = json.load(f)
            if (cached.get("client_id") == client_id
                    and cached.get("expires_at", 0) > time.time()):
                return cached["token"]
    except (json.JSONDecodeError, OSError):
        pass

    # Fetch new token
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

        # Cache with 9-minute TTL (token lasts 10 min, 1 min safety margin)
        try:
            with open(cache_path, "w") as f:
                json.dump({
                    "token": token,
                    "client_id": client_id,
                    "expires_at": time.time() + 540,
                }, f)
            os.chmod(cache_path, 0o600)
        except OSError:
            pass  # caching is best-effort

        return token
    except Exception as e:
        print(f"Error: OAuth failed: {e}", file=sys.stderr)
        return None


def search_digikey(mpn: str) -> dict | None:
    """Search DigiKey API for a part, return first match with datasheet URL."""
    client_id = os.environ.get("DIGIKEY_CLIENT_ID", "")
    token = _get_digikey_token()
    if not token:
        return None

    # Search for the part
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
    except Exception as e:
        print(f"Error: Search failed: {e}", file=sys.stderr)
        return None

    products = data.get("Products", [])
    if not products:
        print(f"No results for '{mpn}'", file=sys.stderr)
        return None

    # Prefer exact MPN match
    for p in products:
        if p.get("ManufacturerProductNumber", "").upper().startswith(mpn.upper()):
            return p
    return products[0]


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
        note_transport_failure(e)
        if e.code == 401:
            return None  # Token expired — caller should refresh
        print(f"  Search failed for '{mpn}': HTTP {e.code}", file=sys.stderr)
        return None
    except Exception as e:
        note_transport_failure(e)
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


def sync_one_part(
    part: dict,
    output_dir: Path,
    index: dict,
    delay: float,
    ctx,
) -> dict:
    """Download datasheet for one part. Returns updated manifest entry."""
    token, client_id = ctx
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
