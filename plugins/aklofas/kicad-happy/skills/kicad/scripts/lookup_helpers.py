"""Detector-side helpers for lookup() integration.

Used by the detectors that consume datasheet facts via the Consumer API.
Soft-fallback semantics: lookup() returning None falls back to heuristic.
"""
from __future__ import annotations

import sys
from pathlib import Path

from kicad_core.diagnostics import record

# Resolve skills/datasheets package path so detectors can import
# `from lookup_helpers import has_data, best` without managing sys.path.
# Path math: lookup_helpers.py → parents[0]=scripts, parents[1]=kicad, parents[2]=skills
_DATASHEETS_PKG = Path(__file__).resolve().parents[2] / "datasheets"
if _DATASHEETS_PKG.is_dir() and str(_DATASHEETS_PKG) not in sys.path:
    sys.path.insert(0, str(_DATASHEETS_PKG))

try:
    from datasheet_types import has_data, best, facts_trusted
except ImportError:
    def facts_trusted(facts):
        """Fallback when datasheet_types is unavailable. Returns False."""
        return False

    def has_data(specs):
        """Fallback when datasheet_types is unavailable. Returns False."""
        return False

    def best(specs, *, min_confidence):
        """Fallback when datasheet_types is unavailable. Returns None."""
        return None


class StaleExtraction(LookupError):
    """An extraction whose PDF is missing or has changed since it was made."""


def get_facts(mpn, cache_dir=None, *, diagnostics=None):
    """Return DatasheetFacts for mpn, or None on a cache miss or unreadable cache.

    A stale extraction (PDF missing or changed) is still returned, with
    ``facts.stale`` set; each consumer decides whether to trust it. Fields are
    read with ``best(specs, min_confidence=...)`` and ``has_data(specs)``.
    A stale extraction is named once per MPN in *diagnostics* (a list sink,
    usually ``ctx.diagnostics``); a lookup that raises is recorded there too
    and returns None.
    """
    if not mpn:
        return None
    if cache_dir is None:
        # No cache configured is an expected condition, not a failure: no record (lookup() raises on Path(None)).
        return None
    try:
        from datasheet_types import lookup
    except ImportError:
        return None
    try:
        facts = lookup(mpn, cache_dir=cache_dir)
    except Exception as exc:
        record(diagnostics, "lookup_helpers.get_facts", exc, f"datasheet facts unavailable for {mpn}")
        return None
    ctx = getattr(facts, "_cache_context", None)
    if isinstance(diagnostics, list) and ctx is not None and ctx.is_stale:
        exc = StaleExtraction(f"{mpn}: {ctx.stale_reason}; source.local_path {facts.source.local_path!r}")
        message = str(exc)[:200]
        # Every detector asks for the same part; name it once.
        if not any(d.get("source") == "lookup_helpers.get_facts" and d.get("message") == message
                   for d in diagnostics if isinstance(d, dict)):
            record(diagnostics, "lookup_helpers.get_facts", exc,
                   "extraction not trusted: checks that require a current extraction skip its facts")
    return facts
