"""Trust-gating helpers — per-field tri-state filtering of SpecValue lists.

Provides module-level
functions that let detectors filter list[SpecValue] data by the evidence
confidence level declared at extraction time.

Three functions:

    has_data(specs) -> bool
        True when specs is a non-empty list. Distinguishes 'field not
        extracted' (None or []) from 'field populated with values'.

    best(specs, *, min_confidence) -> Optional[SpecValue]
        First SpecValue whose evidence.confidence meets min_confidence,
        or None. Returns None for missing (specs is None/[]) AND for
        below-gate (no value meets the gate) — pair with has_data() to
        get the tri-state signal.

    trusted(specs, *, min_confidence) -> list[SpecValue]
        All SpecValues whose evidence.confidence meets min_confidence,
        in input order. Returns [] for missing and below-gate.

Consumer pattern:

    from datasheet_types import best, trusted, has_data

    # Tri-state detector gating:
    specs = ds.regulator.vin_range
    if not has_data(specs):
        return                                # Field missing — skip.
    passing = trusted(specs, min_confidence="medium")
    if not passing:
        return emit(..., confidence="low")   # Below-gate — reduce finding confidence.
    use(passing[0])                          # Gate passed.

min_confidence is keyword-only and REQUIRED — detectors must declare
their trust level. Pass 'low' explicitly to accept any value.

No module-level state. Functions are pure. Thread-safe.
"""
from __future__ import annotations

import math
from typing import Literal, Optional, TypeAlias

from .spec_value import SpecValue


ConfidenceLevel: TypeAlias = Literal["low", "medium", "high"]

# Internal order — consumers use the string literals, not these integers.
_CONFIDENCE_ORDER = {"low": 0, "medium": 1, "high": 2}


def _check_min_confidence(min_confidence: str) -> int:
    """Validate + coerce min_confidence to its rank integer.

    Raises ValueError with a clear message on invalid input. Lets
    downstream callers skip isinstance/enum dance and just use the rank.
    """
    try:
        return _CONFIDENCE_ORDER[min_confidence]
    except KeyError:
        raise ValueError(
            f"min_confidence must be 'low', 'medium', or 'high'; got {min_confidence!r}"
        ) from None


def has_data(specs: Optional[list[SpecValue]]) -> bool:
    """True when specs is a non-empty list of SpecValues.

    False for None (field not extracted) AND for [] (extraction
    produced no values). Does not inspect evidence confidence — pair
    with trusted() or best() for trust-level gating.
    """
    return bool(specs)


def best(
    specs: Optional[list[SpecValue]],
    *,
    min_confidence: ConfidenceLevel,
) -> Optional[SpecValue]:
    """Return the first SpecValue meeting min_confidence, or None.

    First-match semantics preserve the extractor's intended ordering —
    the library does not re-rank by confidence, method, or any other
    field. Consumers that want custom ranking should call trusted()
    and sort the result themselves.

    Returns None when:
        - specs is None (field not extracted)
        - specs is [] (extraction produced no values)
        - no SpecValue in specs meets min_confidence

    Raises ValueError when min_confidence is not one of
    {'low', 'medium', 'high'}.
    """
    gate = _check_min_confidence(min_confidence)
    if not specs:
        return None
    for s in specs:
        if _CONFIDENCE_ORDER.get(s.evidence.confidence, -1) >= gate:
            return s
    return None


FACTS_MIN_SCORE = 60


def finite_score(value) -> Optional[float]:
    """Return ``value`` when it is a usable quality score, else None.

    A usable score is a finite int or float. A bool, NaN, an infinity, None or
    any other type is no score, so callers compare only real numbers against
    their threshold (``score is None or score < threshold`` means untrusted).
    The scale (0-10 or 0-100) is the caller's.
    """
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
        return value
    return None


def facts_trusted(facts) -> bool:
    """True when a DatasheetFacts extraction is fit for detectors to use: quality
    score at least FACTS_MIN_SCORE (0-100) and the source PDF unchanged."""
    q = finite_score(facts.quality)
    return q is not None and q >= FACTS_MIN_SCORE and not getattr(facts, "stale", False)


def trusted(
    specs: Optional[list[SpecValue]],
    *,
    min_confidence: ConfidenceLevel,
) -> list[SpecValue]:
    """Return all SpecValues meeting min_confidence, in input order.

    Returns [] when:
        - specs is None
        - specs is []
        - no SpecValue in specs meets min_confidence

    Raises ValueError when min_confidence is not one of
    {'low', 'medium', 'high'}.
    """
    gate = _check_min_confidence(min_confidence)
    if not specs:
        return []
    return [s for s in specs if _CONFIDENCE_ORDER.get(s.evidence.confidence, -1) >= gate]
