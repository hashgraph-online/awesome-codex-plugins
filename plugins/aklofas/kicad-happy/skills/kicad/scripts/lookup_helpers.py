"""Detector-side helpers for Phase 4 lookup() integration + design_context reading.

Used by 4b upgraded detectors and 4c new detectors to consume v1.4
datasheet facts via the Phase 2 Consumer API. Soft-fallback semantics
per Phase 4 spec §5.1: lookup() returning None falls back to heuristic.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

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


def get_facts(mpn, cache_dir=None):
    """Return DatasheetFacts for mpn, or None on cache miss / stale / below-gate.

    Soft-fallback gate: detector callers check `if facts is None:` and fall
    back to heuristic. Trust-gate filtering happens at field level via
    facts.best(field, trust_gate=...).
    """
    if not mpn:
        return None
    try:
        from datasheet_types import lookup
    except ImportError:
        return None
    try:
        return lookup(mpn, cache_dir=cache_dir)
    except Exception:
        return None


def read_design_context(analysis_dir):
    """Return the design_context.json dict from analysis_dir, or None if absent."""
    analysis_dir = Path(analysis_dir)
    path = analysis_dir / "design_context.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
