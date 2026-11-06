"""Detector-side helpers for Phase 4 lookup() integration.

Used by 4b upgraded detectors and 4c new detectors to consume v1.4
datasheet facts via the Phase 2 Consumer API. Soft-fallback semantics
per Phase 4 spec §5.1: lookup() returning None falls back to heuristic.
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
    from datasheet_types import has_data, best
except ImportError:
    def has_data(specs):
        """Fallback when datasheet_types is unavailable. Returns False."""
        return False

    def best(specs, *, min_confidence):
        """Fallback when datasheet_types is unavailable. Returns None."""
        return None


def get_facts(mpn, cache_dir=None, *, diagnostics=None):
    """Return DatasheetFacts for mpn, or None on cache miss / stale / below-gate.

    Soft-fallback gate: detector callers check `if facts is None:` and fall
    back to heuristic. Trust-gate filtering happens at field level via
    facts.best(field, trust_gate=...). A lookup that raises is recorded into
    *diagnostics* (a list sink, usually ``ctx.diagnostics``) and returns None.
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
        return lookup(mpn, cache_dir=cache_dir)
    except Exception as exc:
        record(diagnostics, "lookup_helpers.get_facts", exc, f"datasheet facts unavailable for {mpn}")
        return None
