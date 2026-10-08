"""
Cache manager for structured datasheet extractions.

Stores pre-extracted datasheet specs (pin tables, voltage ratings, operating
conditions, application circuits) as per-MPN JSON files in a project-local
`datasheets/extracted/` directory. The extraction itself is performed by
Claude reading selected PDF pages; this module provides the caching framework.

Directory structure:
    <project>/
      design.kicad_sch
      datasheets/
        manifest.json        # PDF manifest (legacy name: index.json)
        TPS61023DRLR.pdf
        extracted/
          manifest.json      # extraction cache index (legacy name: index.json)
          TPS61023DRLR.json  # full structured extraction
          BSS138LT1G.json

The extraction resolution during review:
    1. Check cache (datasheets/extracted/) — instant if fresh
    2. If stale or missing → the agent reads PDF pages and extracts
    3. Score extraction → cache if sufficient (score >= 6.0)

Schema v2 (EXTRACTION_VERSION=2, 2026-04-15):
  pins[].function: canonical pin category, one of:
    'VIN' | 'VOUT' | 'EN' | 'PG' | 'SW' | 'FB' | 'GND' | 'IO' |
    'CLK' | 'RESET' | 'OTHER' | None
  features.has_pg: bool | None — part has a power-good output pin
  features.has_soft_start: bool | None — integrated soft-start
  features.iss_time_us: float | None — soft-start time (microseconds)
  peripherals.usb: {speed, native_phy, series_r_required} | None (MCUs only)
    speed: 'FS' | 'HS' | 'SS' | None
    native_phy: bool | None
    series_r_required: bool | None
  topology: 'boost' | 'buck' | 'ldo' | 'mcu' | 'sensor' | 'adc' |
            'mosfet' | 'bjt' | 'other' | None

Per-pin V_IH/V_IL thresholds already live in pins[].threshold_high_v
and pins[].threshold_low_v (v1 schema, no change needed).

All v2 fields are nullable. None means 'datasheet didn't specify or
extraction couldn't verify', distinct from explicit False.
"""

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

# Bump this when the extraction schema changes to trigger re-extraction
# v2 (2026-04-15): added peripherals.usb, electrical.en_v_ih_max/en_v_il_min,
# electrical.iss_time_us, features.has_pg, features.has_soft_start,
# pins[].function (functional category) and top-level topology for
# structured consumer access via datasheet_features.py.
EXTRACTION_VERSION = 2

# Extractions older than this are considered stale (days)
DEFAULT_MAX_AGE_DAYS = 90

# Minimum acceptable score; below this, retry is attempted
MIN_SCORE = 6.0

# Maximum retry attempts for low-scoring extractions
MAX_RETRIES = 3


# ---------------------------------------------------------------------------
# Directory resolution
# ---------------------------------------------------------------------------

def resolve_extract_dir(analysis_json=None, project_dir=None, override_dir=None):
    """Determine the datasheets/extracted/ directory for this project.

    Derives the project directory from either an explicit path, the analyzer
    JSON's "file" field, or falls back to a temp directory.

    Args:
        analysis_json: Parsed analyzer JSON dict (uses "file" key)
        project_dir: Explicit project directory path
        override_dir: If set, use this directory directly

    Returns:
        Path to datasheets/extracted/ directory (may not exist yet)
    """
    if override_dir:
        return Path(override_dir)

    if project_dir:
        return Path(project_dir) / "datasheets" / "extracted"

    if analysis_json:
        source_file = analysis_json.get("file", "")
        if source_file:
            return Path(source_file).parent / "datasheets" / "extracted"

    # Fallback: temp directory
    import tempfile
    return Path(tempfile.gettempdir()) / "kicad-happy" / "datasheets" / "extracted"


def resolve_datasheets_dir(extract_dir):
    """Get the parent datasheets/ directory from an extracted/ path.

    Args:
        extract_dir: Path to datasheets/extracted/

    Returns:
        Path to datasheets/ directory
    """
    p = Path(extract_dir)
    if p.name == "extracted":
        return p.parent
    return p.parent  # best guess


# ---------------------------------------------------------------------------
# PDF hashing for cache invalidation
# ---------------------------------------------------------------------------

def _pdf_hash(pdf_path):
    """Compute SHA-256 hash of a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        "sha256:<hex>" string, or None if file doesn't exist
    """
    try:
        h = hashlib.sha256()
        with open(pdf_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return f"sha256:{h.hexdigest()}"
    except OSError:
        return None


# ---------------------------------------------------------------------------
# MPN normalization (matches spice_model_generator.sanitize_mpn)
# ---------------------------------------------------------------------------

def _sanitize_mpn(mpn):
    """Convert an MPN to a safe filename component.

    Appends a short hash to avoid collisions when different MPNs
    sanitize to the same string (e.g., STM32F-103 vs STM32F/103).
    """
    import hashlib
    clean = re.sub(r'[^A-Za-z0-9_]', '_', mpn.strip())
    h = hashlib.md5(mpn.strip().encode()).hexdigest()[:6]
    return f"{clean}_{h}"


# ---------------------------------------------------------------------------
# In-memory cache for manifest.json (avoids re-reading on every call)
# ---------------------------------------------------------------------------

MANIFEST_FILENAME = "manifest.json"
LEGACY_MANIFEST_FILENAME = "index.json"

_index_cache = {}  # extract_dir_str → (mtime, parsed_index)


def _manifest_path_for(extract_dir):
    """Return the manifest path, preferring new manifest.json over legacy index.json."""
    d = Path(extract_dir)
    new = d / MANIFEST_FILENAME
    old = d / LEGACY_MANIFEST_FILENAME
    if new.exists() or not old.exists():
        return new
    return old


def _load_index(extract_dir):
    """Load the extraction manifest with mtime-based in-memory caching.

    Reads manifest.json preferentially; falls back to legacy index.json on
    projects that haven't been migrated yet.

    Args:
        extract_dir: Path to datasheets/extracted/

    Returns:
        Parsed manifest dict, or empty structure if not found
    """
    index_path = _manifest_path_for(extract_dir)
    cache_key = str(extract_dir)

    try:
        if not index_path.exists():
            return {"version": EXTRACTION_VERSION, "last_updated": "", "extractions": {}}

        mtime = index_path.stat().st_mtime
        cached = _index_cache.get(cache_key)
        if cached and cached[0] == mtime:
            return cached[1]

        with open(index_path) as f:
            index = json.load(f)
        _index_cache[cache_key] = (mtime, index)
        return index
    except (json.JSONDecodeError, OSError):
        return {"version": EXTRACTION_VERSION, "last_updated": "", "extractions": {}}


def _save_index(extract_dir, index):
    """Write the extraction manifest atomically. Always writes manifest.json;
    removes any legacy index.json after the new file is in place.

    Args:
        extract_dir: Path to datasheets/extracted/
        index: Manifest dict to save
    """
    extract_dir = Path(extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)

    index["last_updated"] = datetime.now().astimezone().isoformat(timespec='seconds')
    index["version"] = EXTRACTION_VERSION

    new_path = extract_dir / MANIFEST_FILENAME
    tmp = new_path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(index, f, indent=2)
    tmp.replace(new_path)

    old_path = extract_dir / LEGACY_MANIFEST_FILENAME
    if old_path.exists() and old_path != new_path:
        try:
            old_path.unlink()
        except OSError:
            pass

    # Invalidate in-memory cache
    _index_cache.pop(str(extract_dir), None)


# ---------------------------------------------------------------------------
# Cache read / write / invalidation
# ---------------------------------------------------------------------------

def get_cached_extraction(extract_dir, mpn):
    """Retrieve a cached extraction by MPN.

    Args:
        extract_dir: Path to datasheets/extracted/
        mpn: Manufacturer part number

    Returns:
        Parsed extraction dict, or None if not cached
    """
    index = _load_index(extract_dir)
    key = _sanitize_mpn(mpn)

    entry = index.get("extractions", {}).get(key)
    if not entry:
        # Try case-insensitive match
        for k, v in index.get("extractions", {}).items():
            if k.upper() == key.upper():
                entry = v
                break
    if not entry:
        return None

    json_file = Path(extract_dir) / entry.get("file", "")
    if not json_file.exists():
        return None

    try:
        with open(json_file) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def cache_extraction(extract_dir, mpn, extraction, source_pdf=None):
    """Save an extraction to the cache.

    Writes the extraction JSON file and updates the index. If source_pdf
    is provided, computes and stores its hash for invalidation.

    Args:
        extract_dir: Path to datasheets/extracted/
        mpn: Manufacturer part number
        extraction: Complete extraction dict (with extraction_metadata)
        source_pdf: Optional path to the source PDF file
    """
    extract_dir = Path(extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)

    key = _sanitize_mpn(mpn)
    filename = f"{key}.json"
    json_path = extract_dir / filename

    # Compute PDF hash if source provided
    if source_pdf:
        pdf_hash = _pdf_hash(source_pdf)
        if pdf_hash:
            extraction.setdefault("extraction_metadata", {})["source_pdf_hash"] = pdf_hash

    # Ensure metadata has required fields
    meta = extraction.setdefault("extraction_metadata", {})
    meta.setdefault("extraction_date", datetime.now(timezone.utc).isoformat())
    meta.setdefault("extraction_version", EXTRACTION_VERSION)
    meta.setdefault("retry_count", 0)

    # Write extraction file
    with open(json_path, "w") as f:
        json.dump(extraction, f, indent=2)

    # Update index
    index = _load_index(extract_dir)
    index.setdefault("extractions", {})[key] = {
        "file": filename,
        "mpn": mpn,
        "category": extraction.get("category", ""),
        "source_pdf": meta.get("source_pdf", ""),
        "source_pdf_hash": meta.get("source_pdf_hash", ""),
        "extraction_date": meta["extraction_date"],
        "extraction_score": meta.get("extraction_score", 0),
        "extraction_version": meta["extraction_version"],
        "pin_count": len(extraction.get("pins", [])),
    }
    _save_index(extract_dir, index)


def is_extraction_stale(extract_dir, mpn, datasheets_dir=None):
    """Check if an extraction needs to be refreshed.

    Stale conditions (any one triggers):
    1. Source PDF has changed (sha256 hash mismatch)
    2. Extraction version < current code version (schema upgrade)
    3. Score < MIN_SCORE and retry_count < MAX_RETRIES (worth retrying)
    4. Extraction older than DEFAULT_MAX_AGE_DAYS

    Args:
        extract_dir: Path to datasheets/extracted/
        mpn: Manufacturer part number
        datasheets_dir: Path to datasheets/ (for PDF hash comparison)

    Returns:
        (is_stale: bool, reason: str) — reason is "" if not stale
    """
    extraction = get_cached_extraction(extract_dir, mpn)
    if extraction is None:
        return True, "not_cached"

    meta = extraction.get("extraction_metadata", {})

    # Check version
    version = meta.get("extraction_version", 0)
    if version < EXTRACTION_VERSION:
        return True, f"schema_upgrade (v{version} < v{EXTRACTION_VERSION})"

    # Check PDF hash
    if datasheets_dir:
        source_pdf_name = meta.get("source_pdf", "")
        if source_pdf_name:
            pdf_path = Path(datasheets_dir) / source_pdf_name
            if pdf_path.exists():
                current_hash = _pdf_hash(pdf_path)
                stored_hash = meta.get("source_pdf_hash", "")
                if current_hash and stored_hash and current_hash != stored_hash:
                    return True, "pdf_changed"

    # Check score + retry budget
    score = meta.get("extraction_score", 0)
    retries = meta.get("retry_count", 0)
    if score < MIN_SCORE and retries < MAX_RETRIES:
        return True, f"low_score ({score:.1f} < {MIN_SCORE}, retry {retries+1}/{MAX_RETRIES})"

    # Check age
    date_str = meta.get("extraction_date", "")
    if date_str:
        try:
            # Handle both timezone-aware and naive datetime strings
            ext_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - ext_date).days
            if age_days > DEFAULT_MAX_AGE_DAYS:
                return True, f"age ({age_days} days > {DEFAULT_MAX_AGE_DAYS})"
        except (ValueError, TypeError):
            pass

    return False, ""


def get_extraction_for_review(mpn, extract_dir, datasheets_dir=None):
    """High-level: get extraction for a review, checking freshness.

    Resolution:
    1. Check cache — if fresh, return cached extraction
    2. If stale or missing — return None (caller should trigger extraction)

    Args:
        mpn: Manufacturer part number
        extract_dir: Path to datasheets/extracted/
        datasheets_dir: Path to datasheets/ (for staleness check)

    Returns:
        (extraction_dict, status) where status is one of:
        - "cached" — fresh extraction returned
        - "stale:<reason>" — extraction exists but is stale, needs refresh
        - "missing" — no extraction exists
    """
    extraction = get_cached_extraction(extract_dir, mpn)

    if extraction is None:
        return None, "missing"

    stale, reason = is_extraction_stale(extract_dir, mpn, datasheets_dir)
    if stale:
        return extraction, f"stale:{reason}"

    return extraction, "cached"


def list_extractions(extract_dir):
    """List all cached extractions with their metadata.

    Args:
        extract_dir: Path to datasheets/extracted/

    Returns:
        List of dicts with mpn, category, score, date, version, pin_count
    """
    index = _load_index(extract_dir)
    results = []
    for key, entry in index.get("extractions", {}).items():
        results.append({
            "mpn": entry.get("mpn", key),
            "category": entry.get("category", ""),
            "score": entry.get("extraction_score", 0),
            "date": entry.get("extraction_date", ""),
            "version": entry.get("extraction_version", 0),
            "pin_count": entry.get("pin_count", 0),
            "file": entry.get("file", ""),
        })
    return results


def update_datasheets_index(datasheets_dir, mpn, extraction):
    """Add an extraction pointer to the main datasheets/manifest.json.

    Adds an "extraction" field to the part's entry in the datasheets
    manifest, so any code reading it can quickly check whether a
    pre-extraction exists and its quality.

    Reads manifest.json preferentially, falling back to legacy index.json
    for projects that haven't been migrated. Writes back to whichever file
    was loaded (in-place update only — migration to manifest.json happens
    when the distributor sync script re-runs).

    Args:
        datasheets_dir: Path to datasheets/
        mpn: Manufacturer part number
        extraction: The extraction dict (reads metadata from it)
    """
    datasheets_dir = Path(datasheets_dir)
    new_path = datasheets_dir / "manifest.json"
    old_path = datasheets_dir / "index.json"
    if new_path.exists():
        index_path = new_path
    elif old_path.exists():
        index_path = old_path
    else:
        return

    try:
        with open(index_path) as f:
            index = json.load(f)
    except (json.JSONDecodeError, OSError):
        return

    parts = index.get("parts", {})
    entry = parts.get(mpn)
    if not entry:
        # Try case-insensitive match
        for k, v in parts.items():
            if k.upper() == mpn.upper():
                entry = v
                mpn = k  # use the original key
                break
    if not entry:
        return

    meta = extraction.get("extraction_metadata", {})
    entry["extraction"] = {
        "file": f"extracted/{_sanitize_mpn(mpn)}.json",
        "score": meta.get("extraction_score", 0),
        "date": meta.get("extraction_date", ""),
    }

    # Write back atomically
    tmp = index_path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(index, f, indent=2)
    tmp.replace(index_path)


# ---------------------------------------------------------------------------
# v2 schema validation
# ---------------------------------------------------------------------------

_V2_STRUCTURE = {
    'topology': ('boost', 'buck', 'ldo', 'mcu', 'sensor', 'adc',
                 'mosfet', 'bjt', 'other', None),
    'pin_function': ('VIN', 'VOUT', 'EN', 'PG', 'SW', 'FB', 'GND',
                     'IO', 'CLK', 'RESET', 'OTHER', None),
    'usb_speed': ('FS', 'HS', 'SS', None),
}


def validate_v2_extraction(extraction):
    """Check that a v2 extraction has well-formed optional fields.

    Returns a list of issues (strings). Empty list = valid. Does not
    complain about missing fields (all are nullable) — only about
    wrong types or out-of-range values.
    """
    issues = []
    topo = extraction.get('topology')
    if topo is not None and topo not in _V2_STRUCTURE['topology']:
        issues.append(f"topology: unexpected value {topo!r}")
    for pin in extraction.get('pins', []) or []:
        fn = pin.get('function')
        if fn is not None and fn not in _V2_STRUCTURE['pin_function']:
            issues.append(
                f"pins[{pin.get('number')}].function: unexpected {fn!r}"
            )
    peripherals = extraction.get('peripherals') or {}
    usb = peripherals.get('usb')
    if isinstance(usb, dict):
        speed = usb.get('speed')
        if speed is not None and speed not in _V2_STRUCTURE['usb_speed']:
            issues.append(
                f"peripherals.usb.speed: unexpected {speed!r}"
            )
    return issues
