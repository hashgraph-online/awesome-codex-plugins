"""Consumer API entry point — lookup(mpn) -> DatasheetFacts | None.

Track 2.3 of the v1.4 datasheet extraction work. Pure-read: lookup()
never writes, extracts, or triggers LLM calls (spec §11 Rules 1 & 2).
On cache miss, malformed JSON, or any error, lookup() returns None.

Consumers import:
    from datasheet_lookup import lookup
    from datasheet_types import DatasheetFacts

    ds = lookup("LM2596-ADJ", cache_dir=Path("/path/to/datasheets/extracted"))
    if ds is None:
        ...  # no cache for this MPN
    if ds.stale:
        ...  # PDF on disk has changed since extraction
    if ds.quality is not None and ds.quality < 60:
        ...  # low-confidence extraction
    # Typed access via Track 2.2:
    ds.base.pinout.find(name="EN")
    ds.regulator.topology  # if "regulator" in ds.categories
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# datasheet_types is a sibling package under skills/datasheets/.
# The consumer is expected to add skills/datasheets/ to sys.path so
# `import datasheet_types` resolves — but in case this module is loaded
# directly (e.g. from scripts dir only), add the parent dir once.
_TYPES_PARENT = str(Path(__file__).resolve().parent.parent)
if _TYPES_PARENT not in sys.path:
    sys.path.insert(0, _TYPES_PARENT)

from datasheet_types.codec import from_dict  # noqa: E402
from datasheet_types.extraction import DatasheetFacts  # noqa: E402


# ---------------------------------------------------------------------------
# MPN sanitization + cache-path resolution
# ---------------------------------------------------------------------------

# Allowed characters in the sanitized filename component.
# Matches [A-Za-z0-9_-]; everything else is replaced with _.
# Simpler than v1.3's scheme (which appended an MD5 suffix to avoid
# collisions) — the MPN character set is narrow enough in practice.
_UNSAFE_CHAR = re.compile(r"[^A-Za-z0-9_.\-]")

# Stale-reason enum values — consumed by Track 2.4 trust gating and by
# consumers that want to display a human-readable reason. Kept as module
# constants (not a real Enum) so CacheContext.stale_reason stays a plain
# string in the JSON/dataclass shape.
STALE_PDF_MISSING = "pdf_missing"
STALE_PDF_HASH_MISMATCH = "pdf_hash_mismatch"


def sanitize_mpn(mpn: str) -> str:
    """Convert an MPN to a filename-safe component.

    Strips whitespace; replaces any non-[A-Za-z0-9_.-] character with '_'.
    Dots and hyphens are preserved because they appear in valid MPNs
    (crystals like `ABM8G-106-12.000MHZ-T`, hyphenated families like
    `LM2596-ADJ`). This MUST match the planner/merger which write
    literal MPN-named files via `plan_extraction.py` and `merge_results.py`
    — earlier divergence (dot-stripping here) caused silent cache misses
    for dot-containing MPNs (audit C1, LOG entry 63). No hash suffix —
    rare collisions are acceptable for v1.4.

    Examples:
        sanitize_mpn("LM2596-ADJ")             -> "LM2596-ADJ"
        sanitize_mpn("ABM8G-106-12.000MHZ-T")  -> "ABM8G-106-12.000MHZ-T"
        sanitize_mpn("STM32/F103")             -> "STM32_F103"
        sanitize_mpn(" ACME 1234 ")            -> "ACME_1234"
    """
    return _UNSAFE_CHAR.sub("_", mpn.strip())


def cache_path_for(mpn: str, cache_dir: Path) -> Path:
    """Return the cache-file path for an MPN.

    Composes <cache_dir>/<sanitize_mpn(mpn)>.json. Does not check
    existence; does not resolve symlinks.
    """
    return Path(cache_dir) / f"{sanitize_mpn(mpn)}.json"


# ---------------------------------------------------------------------------
# Cache context (attached to DatasheetFacts by lookup())
# ---------------------------------------------------------------------------

@dataclass
class CacheContext:
    """Operational metadata attached to a DatasheetFacts by lookup().

    Not a dataclass field on DatasheetFacts itself — DatasheetFacts.stale
    and DatasheetFacts.cache_path properties read this via getattr on an
    instance attribute. Absent for DatasheetFacts constructed outside
    lookup() (Track 2.2 round-trip tests); properties default safely.
    """
    cache_path: Path
    pdf_path: Optional[Path] = None
    is_stale: bool = False
    stale_reason: Optional[str] = None  # STALE_PDF_HASH_MISMATCH | STALE_PDF_MISSING | None


# ---------------------------------------------------------------------------
# PDF staleness helpers
# ---------------------------------------------------------------------------


def _compute_pdf_sha256(pdf_path: Path) -> Optional[str]:
    """Return 'sha256:<hex>' for the file at pdf_path, or None if missing.

    Reads in 64KB chunks to avoid loading large PDFs into memory at once.
    Any OSError (permission denied, IO error, etc.) returns None, which
    the caller treats as 'PDF unavailable' → stale.
    """
    try:
        h = hashlib.sha256()
        with pdf_path.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return f"sha256:{h.hexdigest()}"
    except OSError:
        return None


def _resolve_pdf_path(cache_dir: Path, source_local_path: Optional[str]) -> Optional[Path]:
    """Resolve source.local_path against the parent of cache_dir.

    The conventional layout is:
        datasheets/
            extracted/        <-- cache_dir
                LM2596-ADJ.json
            LM2596-ADJ.pdf    <-- source.local_path == "LM2596-ADJ.pdf"

    So the PDF lives at cache_dir.parent / source.local_path.

    Returns None when source_local_path is None (datasheet wasn't sourced
    locally) — caller treats None as 'pdf_missing'.
    """
    if source_local_path is None:
        return None
    # local_path is stored relative; if it starts with "datasheets/" already
    # (a v1.3 convention), treat it as relative to cache_dir.parent.parent.
    base = cache_dir.parent
    candidate = base / source_local_path
    if not candidate.is_file() and source_local_path.startswith("datasheets/"):
        candidate = base.parent / source_local_path
    return candidate


# ---------------------------------------------------------------------------
# lookup — the consumer API entry point
# ---------------------------------------------------------------------------


def lookup(mpn: str, *, cache_dir: Path) -> Optional[DatasheetFacts]:
    """Read-only MPN → DatasheetFacts lookup.

    Resolves `cache_dir / <sanitize_mpn(mpn)>.json`, parses it into a
    typed DatasheetFacts via the Track 2.2 codec, verifies PDF staleness
    by comparing sha256 of the on-disk PDF against cached source.sha256,
    attaches a CacheContext carrying (cache_path, pdf_path, is_stale,
    stale_reason), and returns the instance.

    Returns None when:
        - cache_dir does not exist
        - cache file for this MPN does not exist
        - cache file contains malformed JSON
        - cache file is JSON but does not satisfy DatasheetFacts shape
          (required fields missing)

    Per spec §11: pure read — never writes, never extracts, never
    triggers an LLM call. On cache miss, caller is responsible for
    triggering `datasheets sync` or equivalent.

    Args:
        mpn: Manufacturer part number. Sanitized for filename lookup.
        cache_dir: Path to the datasheets/extracted/ directory.

    Returns:
        A DatasheetFacts instance with attached _cache_context, or None.
    """
    cache_dir = Path(cache_dir)
    if not cache_dir.is_dir():
        return None

    cache_file = cache_path_for(mpn, cache_dir)
    if not cache_file.is_file():
        return None

    try:
        data = json.loads(cache_file.read_bytes())
    except (json.JSONDecodeError, OSError):
        return None

    try:
        facts = from_dict(DatasheetFacts, data)
    except (KeyError, TypeError, ValueError):
        # Missing required fields, wrong shape, invalid unit string, etc.
        return None

    # Attach cache context with staleness detection.
    pdf_path = _resolve_pdf_path(cache_dir, facts.source.local_path)
    if pdf_path is None:
        ctx = CacheContext(
            cache_path=cache_file,
            pdf_path=None,
            is_stale=True,
            stale_reason=STALE_PDF_MISSING,
        )
    else:
        current_sha = _compute_pdf_sha256(pdf_path)
        if current_sha is None:
            ctx = CacheContext(
                cache_path=cache_file,
                pdf_path=pdf_path,
                is_stale=True,
                stale_reason=STALE_PDF_MISSING,
            )
        elif current_sha != facts.source.sha256:
            ctx = CacheContext(
                cache_path=cache_file,
                pdf_path=pdf_path,
                is_stale=True,
                stale_reason=STALE_PDF_HASH_MISMATCH,
            )
        else:
            ctx = CacheContext(
                cache_path=cache_file,
                pdf_path=pdf_path,
                is_stale=False,
                stale_reason=None,
            )
    facts._cache_context = ctx
    return facts
