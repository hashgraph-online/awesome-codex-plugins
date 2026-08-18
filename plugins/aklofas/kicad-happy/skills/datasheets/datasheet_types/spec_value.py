"""SpecValue + Evidence dataclasses — the atomic primitives.

Mirrors spec_value.schema.json. Every numeric datasheet fact in the
v2 cache is a list of SpecValue; every SpecValue carries an Evidence
block (page + confidence + method).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Evidence:
    """Provenance for a single fact.

    Mirrors the inline evidence block shape used across every schema.
    """
    page: int = field(metadata={
        "description": "PDF page number (1-based) where the fact was sourced."})
    confidence: str = field(metadata={
        "description": "'high' | 'medium' | 'low' — extractor confidence. Pivots trust gating."})
    method: str = field(metadata={
        "description": "'table' | 'prose' | 'curve' | 'calculated' | 'derived'."})
    section: Optional[str] = field(default=None, metadata={
        "description": "Datasheet section label when available."})


@dataclass
class SpecValue:
    """One electrical/physical specification value with provenance.

    Numeric fields (min/typ/max) are all Optional[float] — the datasheet
    may publish any subset. unit is always populated (canonical SI).
    evidence is always populated (no fact without provenance).
    """
    unit: str = field(metadata={
        "description": "Canonical SI unit (V, A, s, Hz, Ω, F, H, K, W, °C, %, ppm, K/W, °C/W). "
                       "Extraction converts prefixed units (mV, kHz, µF, ...) before caching."})
    evidence: Evidence = field(metadata={
        "description": "Provenance for this value. Never null — every fact carries evidence."})
    min: Optional[float] = field(default=None, metadata={
        "description": "Minimum published value. None when datasheet doesn't specify."})
    typ: Optional[float] = field(default=None, metadata={
        "description": "Typical published value. None when datasheet doesn't specify."})
    max: Optional[float] = field(default=None, metadata={
        "description": "Maximum published value. None when datasheet doesn't specify."})
    condition: Optional[str] = field(default=None, metadata={
        "description": "Test conditions (e.g. 'VIN=5V, IL=100mA, TJ=25°C')."})
    notes: Optional[str] = field(default=None, metadata={
        "description": "Additional notes or original symbolic form if resolved at extraction."})
