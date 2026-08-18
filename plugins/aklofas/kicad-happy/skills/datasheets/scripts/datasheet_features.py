"""Consumer helper API for datasheet extractions.

Thin wrapper over datasheet_extract_cache. Provides field-level accessors for
IC-aware detectors in kicad, emc, spice, and thermal skills.

Contract:
  - Returns a dict of feature fields on cache hit, with a `quality` flag
    describing score/staleness/version status. Quality gate is applied by each
    caller (v2.0 spec §3.A.1), not by _load.
  - Returns None only on cache miss or wrong part category (e.g., not a regulator).
  - Individual fields within the dict may be None (datasheet didn't specify).
  - Consumers MUST distinguish None (unknown) from False (explicitly no).

Zero external dependencies — stdlib only.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from datasheet_extract_cache import (
    resolve_extract_dir,
    get_cached_extraction,
    EXTRACTION_VERSION,
    MIN_SCORE,
)

# Add datasheet_types to sys.path for direct import of DatasheetFacts etc.
# This module lives at skills/datasheets/scripts/; the types package is a
# sibling under skills/datasheets/datasheet_types/.
_TYPES_PARENT = str(Path(__file__).resolve().parent.parent)
if _TYPES_PARENT not in sys.path:
    sys.path.insert(0, _TYPES_PARENT)

from datasheet_types.extraction import DatasheetFacts  # noqa: E402


_REGULATOR_TOPOLOGIES = ('boost', 'buck', 'ldo')
_MCU_TOPOLOGIES = ('mcu',)

# v1.3 pin-function name → v1.4 Pin.name patterns. Used by the derivation
# helper to map a pin to its v1.3 functional category. Includes verbose
# datasheet variants ("Output", "Ground", etc.) — TI's family datasheets
# print the long forms verbatim, and the v1.4 pipeline lifts pin names
# verbatim from the source.
_PIN_NAME_TO_FUNCTION: dict[str, str] = {
    "VIN": "VIN",
    "VIN+": "VIN",
    "Input": "VIN",
    "OUT": "VOUT",
    "VOUT": "VOUT",
    "VOUT+": "VOUT",
    "Output": "VOUT",
    "GND": "GND",
    "VSS": "GND",
    "AGND": "GND",
    "DGND": "GND",
    "Ground": "GND",
}


def _load(mpn, extract_dir=None, analysis_json=None, project_dir=None):
    """Resolve extract dir and load the cached extraction for mpn.

    Returns the extraction dict on any cache hit (quality is described by
    `_quality_v13`, never gated here — v2.0 spec §3.A.1). Returns None only
    on cache miss.
    """
    import json as _json
    if extract_dir is None:
        extract_dir = resolve_extract_dir(
            analysis_json=analysis_json, project_dir=project_dir
        )
    ext = get_cached_extraction(extract_dir, mpn)
    if ext:
        return ext
    # Direct-file fallback: allows test fixtures (and simple single-file drops)
    # that write {mpn}.json directly without a manifest index.
    direct = Path(extract_dir) / f"{mpn}.json"
    if direct.exists():
        try:
            with direct.open() as f:
                return _json.load(f)
        except (OSError, ValueError):
            pass
    return None


def _quality_v13(ext):
    """Quality flag for a v1.3-format extraction. Describes — never gates."""
    meta = (ext or {}).get('extraction_metadata') or {}
    score = meta.get('extraction_score')
    version = meta.get('extraction_version') or 0
    reasons = []
    if version < EXTRACTION_VERSION:
        reasons.append(f'stale_version ({version} < {EXTRACTION_VERSION})')
    if not isinstance(score, (int, float)) or score < MIN_SCORE:
        reasons.append(f'low_score ({score} < {MIN_SCORE})')
    return {
        'score': score if isinstance(score, (int, float)) else None,
        'scale': '0-10',
        'trusted': not reasons,
        'reasons': reasons,
    }


def _quality_v14(facts):
    """Quality flag for a v1.4 DatasheetFacts. Describes — never gates."""
    score = facts.quality
    reasons = []
    if not isinstance(score, (int, float)) or score < 60:
        reasons.append(f'low_score ({score} < 60)')
    if getattr(facts, 'stale', False):
        reasons.append('stale_pdf')
    return {
        'score': score if isinstance(score, (int, float)) else None,
        'scale': '0-100',
        'trusted': not reasons,
        'reasons': reasons,
    }


def _pin_with_function(pins, target_function):
    """Return the first pin whose function matches target_function, or None."""
    for pin in pins or []:
        if pin.get('function') == target_function:
            return pin
    return None


# ---------------------------------------------------------------------------
# v1.4 derivation helpers — translate DatasheetFacts → v1.3 dict shape.
# Used by the public wrappers in Task 2. Pure functions, no filesystem.
# ---------------------------------------------------------------------------

def _derive_regulator_features_v14(facts: DatasheetFacts) -> Optional[dict]:
    """Translate a v1.4 DatasheetFacts into a v1.3 regulator-features dict.

    Returns None when facts has no regulator category (v1.4 MVP scope is
    regulator only; MCU / opamp / etc. land in v1.5).

    Fields derived from v1.4:
      topology:  facts.regulator.topology (already v1.3-compatible enum
                 for ldo/buck/boost; other topologies pass through verbatim,
                 so a v1.3 detector checking `topology in ('boost','buck','ldo')`
                 gets the same behavior it always had).
      has_pg:    True iff facts.regulator.power_good_pin is not None.
      en_pin:    facts.regulator.enable_pin.
      pg_pin:    facts.regulator.power_good_pin.
      vin_pin:   pin number of the Pin named VIN (or VIN+) in base.pinout.
      vout_pin:  pin number of the Pin named OUT / VOUT / VOUT+.

    Fields with no v1.4 schema v1.0 equivalent (has_soft_start, iss_time_us,
    en_v_ih_max, en_v_il_min) return None. v1.3 contract explicitly allows
    this: None means "datasheet didn't specify."
    """
    if facts.regulator is None:
        return None

    topo = facts.regulator.topology

    # Find VIN / VOUT pins by name via the Pinout wrapper (Track 2.2).
    # Try short forms first, then verbose datasheet variants used by TI etc.
    vin_pin_obj = (facts.base.pinout.find(name="VIN")
                   or facts.base.pinout.find(name="VIN+")
                   or facts.base.pinout.find(name="Input"))
    vout_pin_obj = (facts.base.pinout.find(name="OUT")
                    or facts.base.pinout.find(name="VOUT")
                    or facts.base.pinout.find(name="VOUT+")
                    or facts.base.pinout.find(name="Output"))

    def _first_number(pin) -> Optional[str]:
        return pin.numbers[0] if pin is not None and pin.numbers else None

    return {
        'topology': topo,
        'has_pg': facts.regulator.power_good_pin is not None,
        'has_soft_start': None,      # No v1.4 equivalent.
        'iss_time_us': None,         # No v1.4 equivalent.
        'en_v_ih_max': None,         # No v1.4 equivalent (per-pin VIH/VIL not in schema v1.0).
        'en_v_il_min': None,
        'vin_pin': _first_number(vin_pin_obj),
        'vout_pin': _first_number(vout_pin_obj),
        'en_pin': facts.regulator.enable_pin,
        'pg_pin': facts.regulator.power_good_pin,
    }


def _derive_mcu_features_v14(facts: DatasheetFacts) -> Optional[dict]:
    """Translate a v1.4 DatasheetFacts into a v1.3 mcu-features dict.

    v1.4 MVP has no mcu category — this always returns None. The public
    get_mcu_features wrapper falls through to the v1.3 cache read path
    when this returns None.

    v1.5 adds the mcu category extension; this function will grow real
    derivation logic then.
    """
    # categories is a list[str]; 'mcu' is not in v1.4 MVP scope.
    return None


def _derive_pin_function_v14(facts: DatasheetFacts, pin_id: str) -> Optional[str]:
    """Translate a pin identifier → v1.3-style function string.

    Derivation order:
      1. Check regulator pin refs (enable_pin → 'EN', power_good_pin → 'PG',
         feedback_pin → 'FB') — these give definitive function hits for
         regulator parts.
      2. Find the Pin in base.pinout by number (exact) or name (case-insensitive).
         Map Pin.name → v1.3 function via _PIN_NAME_TO_FUNCTION.
      3. Fall back to None if no match.

    Returns None when the pin_id does not resolve to any known pin, OR
    when the resolved pin's name is not in _PIN_NAME_TO_FUNCTION (unknown
    function category — caller gets the same None signal v1.3 gave for
    unmapped pins).
    """
    target = str(pin_id).strip()

    # 1. Regulator pin refs (strongest signal for regulator parts).
    if facts.regulator is not None:
        if facts.regulator.enable_pin == target:
            return "EN"
        if facts.regulator.power_good_pin == target:
            return "PG"
        if facts.regulator.feedback_pin == target:
            return "FB"

    # 2. Pinout name-based map.
    pin = facts.base.pinout.find(pin=target)
    if pin is None:
        pin = facts.base.pinout.find(name=target)
    if pin is None:
        return None

    return _PIN_NAME_TO_FUNCTION.get(pin.name)


def _try_v14_facts(mpn, *, extract_dir=None, analysis_json=None, project_dir=None):
    """Common v1.4 probe. Returns DatasheetFacts or None.

    Resolves extract_dir the same way _load does (via resolve_extract_dir)
    so callers that passed analysis_json / project_dir get the same behavior.
    """
    from datasheet_lookup import lookup  # Lazy import — scripts-dir sibling.

    if extract_dir is None:
        extract_dir = resolve_extract_dir(
            analysis_json=analysis_json, project_dir=project_dir
        )
    return lookup(mpn, cache_dir=Path(extract_dir))


def get_regulator_features(mpn, *, extract_dir=None,
                            analysis_json=None, project_dir=None) -> Optional[dict]:
    """Return regulator-specific features for mpn, or None if not available.

    Dual-cache-read: tries the v1.4 cache first via Track 2.3's lookup();
    falls back to the v1.3 (extraction_version=2) cache if no v1.4 cache
    exists. When both exist for the same MPN (mid-migration), v1.4 wins.

    Returns None when:
      - No v1.4 cache AND no v1.3 cache for the MPN
      - v1.4 cache parses but has no regulator category (v1.5 MCU/opamp/etc.
        extensions are not regulator)
      - v1.3 cache exists but topology not in ('boost', 'buck', 'ldo')

    Returned dict fields (any may be None individually):
      topology:          'boost' | 'buck' | 'ldo' (v1.3 enum preserved)
      has_pg:            bool | None
      has_soft_start:    bool | None — always None on v1.4 path (no schema equiv)
      iss_time_us:       float | None — always None on v1.4 path
      en_v_ih_max:       float (V) | None — always None on v1.4 path
      en_v_il_min:       float (V) | None — always None on v1.4 path
      vin_pin:           str | None — pin number of the VIN pin
      vout_pin:          str | None
      en_pin:            str | None
      pg_pin:            str | None
      quality:           {score, scale, trusted, reasons} — always present
    """
    # ---- v1.4 path ----
    facts = _try_v14_facts(mpn, extract_dir=extract_dir,
                           analysis_json=analysis_json, project_dir=project_dir)
    if facts is not None:
        derived = _derive_regulator_features_v14(facts)
        if derived is not None and derived.get('topology') in _REGULATOR_TOPOLOGIES:
            derived['quality'] = _quality_v14(facts)
            return derived
        # v1.4 facts present but not a regulator (or topology outside the
        # v1.3 enum). Fall through to v1.3 below.

    # ---- v1.3 fallback ----
    ext = _load(mpn, extract_dir=extract_dir,
                analysis_json=analysis_json, project_dir=project_dir)
    if not ext:
        return None
    topo = ext.get('topology')
    if topo not in _REGULATOR_TOPOLOGIES:
        return None
    pins = ext.get('pins') or []
    features = ext.get('features') or {}
    en_pin = _pin_with_function(pins, 'EN')
    vin_pin = _pin_with_function(pins, 'VIN')
    vout_pin = _pin_with_function(pins, 'VOUT')
    pg_pin = _pin_with_function(pins, 'PG')

    def _pin_number(p):
        if not p:
            return None
        n = p.get('number')
        return str(n) if n is not None else p.get('name')

    return {
        'topology': topo,
        'has_pg': features.get('has_pg'),
        'has_soft_start': features.get('has_soft_start'),
        'iss_time_us': features.get('iss_time_us'),
        'en_v_ih_max': (en_pin or {}).get('threshold_high_v'),
        'en_v_il_min': (en_pin or {}).get('threshold_low_v'),
        'vin_pin': _pin_number(vin_pin),
        'vout_pin': _pin_number(vout_pin),
        'en_pin': _pin_number(en_pin),
        'pg_pin': _pin_number(pg_pin),
        'quality': _quality_v13(ext),
    }


def get_mcu_features(mpn, *, extract_dir=None,
                     analysis_json=None, project_dir=None) -> Optional[dict]:
    """Return MCU-specific features for mpn, or None if not available.

    Dual-cache-read: tries v1.4 first (but v1.4 MVP has no mcu category
    extension yet — this path always returns None), then falls back to
    v1.3 (extraction_version=2) cache. Once v1.5 ships the mcu category
    schema, _derive_mcu_features_v14 gains real logic and the v1.4 path
    starts returning values.

    Returns None when neither cache has data for mpn.

    Returned dict fields (any may be None individually):
      usb_speed:              'FS' | 'HS' | 'SS' | None
      has_native_usb_phy:     bool | None
      usb_series_r_required:  bool | None
      quality:                {score, scale, trusted, reasons} — always present
    """
    # ---- v1.4 path ----
    facts = _try_v14_facts(mpn, extract_dir=extract_dir,
                           analysis_json=analysis_json, project_dir=project_dir)
    if facts is not None:
        derived = _derive_mcu_features_v14(facts)
        if derived is not None:
            return derived
        # v1.4 facts present but no mcu category (v1.4 MVP scope).
        # Fall through to v1.3 for legacy MCU caches.

    # ---- v1.3 fallback ----
    ext = _load(mpn, extract_dir=extract_dir,
                analysis_json=analysis_json, project_dir=project_dir)
    if not ext:
        return None
    if ext.get('topology') not in _MCU_TOPOLOGIES:
        return None
    peripherals = ext.get('peripherals') or {}
    usb = peripherals.get('usb') or {}
    return {
        'usb_speed': usb.get('speed'),
        'has_native_usb_phy': usb.get('native_phy'),
        'usb_series_r_required': usb.get('series_r_required'),
        'quality': _quality_v13(ext),
    }


def get_pin_function(mpn, pin_identifier, *, extract_dir=None,
                      analysis_json=None, project_dir=None) -> Optional[str]:
    """Return the functional category of a pin ('EN', 'VIN', etc.), or None.

    `pin_identifier` matches against pins[].number (exact) OR pins[].name
    (case-insensitive).

    The trusted gate is applied explicitly here: untrusted extractions return
    None (v2.0 spec §3.A.1 — gate moves from _load into each consumer).

    Dual-cache-read: v1.4 cache preferred, v1.3 fallback.
    """
    # ---- v1.4 path ----
    facts = _try_v14_facts(mpn, extract_dir=extract_dir,
                           analysis_json=analysis_json, project_dir=project_dir)
    if facts is not None:
        fn = _derive_pin_function_v14(facts, pin_identifier)
        if fn is not None:
            return fn
        # v1.4 facts present but pin not resolved — fall through to v1.3
        # (may have richer pin data with explicit function labels).

    # ---- v1.3 fallback ----
    ext = _load(mpn, extract_dir=extract_dir,
                analysis_json=analysis_json, project_dir=project_dir)
    if not ext or not _quality_v13(ext)['trusted']:
        return None
    target = str(pin_identifier).strip()
    target_lower = target.lower()
    for p in ext.get('pins') or []:
        if str(p.get('number', '')).strip() == target:
            return p.get('function')
        if str(p.get('name', '')).strip().lower() == target_lower:
            return p.get('function')
    return None


def is_extraction_available(mpn, *, extract_dir=None,
                             analysis_json=None, project_dir=None) -> bool:
    """True iff a usable extraction exists for mpn (v1.4 OR v1.3 cache)."""
    # v1.4 path: any non-None DatasheetFacts counts as available.
    if _try_v14_facts(mpn, extract_dir=extract_dir,
                      analysis_json=analysis_json, project_dir=project_dir) is not None:
        return True
    # v1.3 fallback: trusted gate applied explicitly here (v2.0 spec §3.A.1 —
    # gate moves from _load into each consumer that needs a binary usable/not answer).
    ext = _load(mpn, extract_dir=extract_dir,
                analysis_json=analysis_json, project_dir=project_dir)
    return bool(ext) and _quality_v13(ext)['trusted']
