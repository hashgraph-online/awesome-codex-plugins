"""Consumer API entry point — lookup(mpn) -> DatasheetFacts | None.

Pure-read: lookup() never writes, extracts, or triggers LLM calls.
On cache miss, malformed JSON, or any error, lookup() returns None.

Consumers import:
    from datasheet_types import lookup, DatasheetFacts

    ds = lookup("LM2596-ADJ", cache_dir=Path("/path/to/datasheets/extracted"))
    if ds is None:
        ...  # no cache for this MPN
    if ds.stale:
        ...  # PDF on disk has changed since extraction
    if ds.quality is not None and ds.quality < 60:
        ...  # low-confidence extraction
    # Typed access:
    ds.base.pinout.find(name="EN")
    ds.regulator.topology  # if "regulator" in ds.categories
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .codec import from_dict
from .extraction import DatasheetFacts


# ---------------------------------------------------------------------------
# MPN sanitization + cache-path resolution
# ---------------------------------------------------------------------------

# Allowed characters in the sanitized filename component: letters, digits,
# '_', '.' and '-'; everything else is replaced with '_'. No hash suffix is
# appended (datasheet_extract_cache's legacy keys carry one).
_UNSAFE_CHAR = re.compile(r"[^A-Za-z0-9_.\-]")

# Stale-reason enum values — consumed by trust gating and by
# consumers that want to display a human-readable reason. Kept as module
# constants (not a real Enum) so CacheContext.stale_reason stays a plain
# string in the JSON/dataclass shape.
STALE_PDF_MISSING = "pdf_missing"
STALE_PDF_HASH_MISMATCH = "pdf_hash_mismatch"


# A cache file larger than this is treated as unreadable.
MAX_CACHE_BYTES = 10 * 1024 * 1024


def read_regular_bytes(path) -> Optional[bytes]:
    """The bytes of one cache file; None when it is missing, a symlink, not a regular file,
    oversized, or unreadable.

    The file is opened without following a link and checked as opened, so a link planted
    after any earlier check is still refused, and a named pipe is never waited on. Where
    ``os.O_NOFOLLOW`` does not exist (Windows) the opened file is compared with ``lstat`` of
    the path instead, which leaves a short window but still refuses a link that was there
    before the open."""
    try:
        flags = (os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
                 | getattr(os, "O_NONBLOCK", 0))
        fd = os.open(path, flags)
        with os.fdopen(fd, "rb") as f:
            st = os.fstat(f.fileno())
            if not stat.S_ISREG(st.st_mode) or st.st_size > MAX_CACHE_BYTES:
                return None
            if not hasattr(os, "O_NOFOLLOW") and not os.path.samestat(st, os.lstat(path)):
                return None
            raw = f.read(MAX_CACHE_BYTES + 1)
            return None if len(raw) > MAX_CACHE_BYTES else raw
    except OSError:
        return None


def read_json_object(path) -> Optional[dict]:
    """Read one cache JSON file; None when it is missing, a symlink, not a regular file,
    oversized, undecodable (not UTF-8), malformed, nested too deeply, or not a JSON object (see
    ``read_regular_bytes`` for how the file is opened)."""
    raw = read_regular_bytes(path)
    if raw is None:
        return None
    try:
        data = json.loads(raw.decode("utf-8"))
    except (ValueError, RecursionError):
        return None
    return data if isinstance(data, dict) else None


_WARNED_LINKED_DIRS: set = set()


def safe_extract_dir(extract_dir) -> Optional[Path]:
    """``extract_dir`` when neither it nor the ``datasheets`` folder holding it is a symlink,
    else None (with one stderr warning per directory). For a cache directory derived from a
    project folder, so a link in the project cannot send reads to another tree; a directory
    the user names explicitly needs no check."""
    p = Path(extract_dir)
    if p.is_symlink() or p.parent.is_symlink():
        if str(p) not in _WARNED_LINKED_DIRS:
            _WARNED_LINKED_DIRS.add(str(p))
            print(f"Warning: {p} is reached through a symlink; datasheet extraction cache "
                  f"ignored (replace the link with a real folder)", file=sys.stderr)
        return None
    return p


def sanitize_mpn(mpn: str) -> str:
    """Convert an MPN to a filename-safe component.

    Strips whitespace; replaces any non-[A-Za-z0-9_.-] character with '_'.
    Dots and hyphens are preserved because they appear in valid MPNs
    (crystals like `ABM8G-106-12.000MHZ-T`, hyphenated families like
    `LM2596-ADJ`). `plan_extraction.py` and `merge_results.py`
    name their files with this function too; stripping dots here would miss the cache for dot-containing MPNs. No
    hash suffix — rare collisions are acceptable.

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
    lookup() (e.g. in round-trip tests); properties default safely.
    """
    cache_path: Path
    pdf_path: Optional[Path] = None
    is_stale: bool = False
    stale_reason: Optional[str] = None  # STALE_PDF_HASH_MISMATCH | STALE_PDF_MISSING | None


# ---------------------------------------------------------------------------
# PDF staleness helpers
# ---------------------------------------------------------------------------


def _compute_pdf_sha256(pdf_path: Path) -> Optional[str]:
    """Return 'sha256:<hex>' for the regular file at pdf_path, or None.

    Reads in 64KB chunks, at most the file's size at open. None for a missing
    file, a device or pipe (never read to the end), or any OSError; the
    caller treats None as 'PDF unavailable' -> stale.
    """
    try:
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0)
        fd = os.open(pdf_path, flags)
        with os.fdopen(fd, "rb") as f:
            st = os.fstat(f.fileno())
            if not stat.S_ISREG(st.st_mode):
                return None
            h = hashlib.sha256()
            remaining = st.st_size
            while remaining > 0:
                chunk = f.read(min(65536, remaining))
                if not chunk:
                    break
                h.update(chunk)
                remaining -= len(chunk)
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

    Returns None when source_local_path is not a non-empty string
    (datasheet wasn't sourced locally) or when the path resolves outside
    cache_dir.parent — caller treats None as 'pdf_missing'.
    """
    if not isinstance(source_local_path, str) or not source_local_path:
        return None
    # local_path is stored relative; if it starts with "datasheets/" already
    # (a v1.3 convention), treat it as relative to cache_dir.parent.parent.
    base = cache_dir.parent
    candidate = base / source_local_path
    if not candidate.is_file() and source_local_path.startswith("datasheets/"):
        candidate = base.parent / source_local_path
    try:
        if not candidate.resolve().is_relative_to(base.resolve()):
            return None
    except (OSError, RuntimeError, ValueError):
        return None
    return candidate


# ---------------------------------------------------------------------------
# lookup — the consumer API entry point
# ---------------------------------------------------------------------------


def lookup(mpn: str, *, cache_dir: Path) -> Optional[DatasheetFacts]:
    """Read-only MPN → DatasheetFacts lookup.

    Resolves `cache_dir / <sanitize_mpn(mpn)>.json`, parses it into a
    typed DatasheetFacts via the codec, verifies PDF staleness
    by comparing sha256 of the on-disk PDF against cached source.sha256,
    attaches a CacheContext carrying (cache_path, pdf_path, is_stale,
    stale_reason), and returns the instance.

    Returns None when:
        - cache_dir does not exist
        - cache file for this MPN does not exist
        - cache file is malformed, not UTF-8, not a JSON object, a symlink
          or oversized
        - cache file is JSON but does not satisfy DatasheetFacts shape
          (required fields missing)

    A source.local_path that is not a string, or resolves outside the
    datasheets/ folder, or names something other than a regular file,
    reads as STALE_PDF_MISSING.

    Pure read: never writes, never extracts, never triggers an LLM call.
    On a cache miss the caller decides whether to run an extraction.

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

    data = read_json_object(cache_file)
    if data is None:
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
