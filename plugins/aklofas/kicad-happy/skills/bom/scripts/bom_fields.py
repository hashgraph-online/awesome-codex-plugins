#!/usr/bin/env python3
"""Field-name aliases and per-symbol part-number lookups shared by the BOM scripts."""

from __future__ import annotations

import re

import _core_path  # noqa: F401
from kicad_core.fields import (MPN_FIELD_ALIASES, MPN_FIELD_ALIASES_PRIMARY,
                               MPN_FIELD_ALIASES_GENERIC, DIGIKEY_FIELD_ALIASES,
                               normalize_field_name)


# Values of a population column (POPULATE, Populate, Fitted) that mean the part
# is not fitted, compared lower-case against the whole stripped cell.
POPULATE_UNFITTED = frozenset({"0", "no", "false", "n", "dnp", "dnf", "do not fit",
                               "do not populate", "not fitted", "unfitted"})


# ---------------------------------------------------------------------------
# Field name aliases — maps every known variant to a canonical name
# ---------------------------------------------------------------------------

FIELD_ALIASES: dict[str, list[str]] = {
    # Shared with analyze_schematic / analyze_pcb (kicad_core.fields), plus
    # the bom-local ambiguous extras the analyzers deliberately exclude.
    "mpn": sorted(MPN_FIELD_ALIASES | {"mp", "mfn"}),
    "manufacturer": [
        "Manufacturer", "Manufacturer_Name", "Manufacturer Name",
        "Mfr", "MFR", "MF", "Mfg", "MANUFACTURER",
    ],
    "digikey": sorted(DIGIKEY_FIELD_ALIASES),
    "mouser": [
        "Mouser", "Mouser Part Number", "Mouser Part", "Mouser_PN",
        "Mouser PN",
    ],
    "lcsc": [
        "LCSC", "LCSC Part #", "LCSC Part Number", "LCSC Part",
        "LCSCStockCode", "LCSC_PN", "LCSC PN", "JLCPCB", "JLCPCB Part",
        "JLC",
    ],
    "element14": [
        "Newark", "Newark Part Number", "Newark_PN", "Newark PN",
        "Farnell", "Farnell Part Number", "Farnell_PN", "Farnell PN",
        "element14", "element14 Part Number", "element14_PN",
    ],
}

# Build reverse lookup: NORMALIZED field name -> canonical name (case- and
# whitespace-insensitive, so "Manufacturer  P/N" == "manufacturer p/n").
_ALIAS_LOOKUP: dict[str, str] = {}
for canonical, aliases in FIELD_ALIASES.items():
    for alias in aliases:
        _ALIAS_LOOKUP[normalize_field_name(alias)] = canonical


def _canonical_for(name: str):
    """Canonical BOM field for an actual KiCad property name, or None."""
    return _ALIAS_LOOKUP.get(normalize_field_name(name))


def _first_nonblank_stripped(props: dict, aliases: frozenset) -> str:
    """First value whose normalized key is in *aliases* and whose .strip() is
    non-empty, returned stripped."""
    for key, value in props.items():
        v = str(value).strip()
        if v and normalize_field_name(key) in aliases:
            return v
    return ""


def _pick_mpn_from_props(props: dict) -> str:
    """Alias-scan fallback for the mpn canonical (manufacturer-specific aliases
    before generic ones; bom-local `mp`/`mfn` count as generic). Whitespace-only
    values are skipped."""
    return (_first_nonblank_stripped(props, MPN_FIELD_ALIASES_PRIMARY)
            or _first_nonblank_stripped(props, MPN_FIELD_ALIASES_GENERIC | frozenset({"mp", "mfn"})))


# KiCad "Supplier N" slots: a name field (`Supplier 1` = "DigiKey") and a part number field whose
# spelling varies between projects; the slot number ties the two together.
_SUPPLIER_NAME_MAP = {
    "digikey": "digikey", "digi-key": "digikey",
    "mouser": "mouser",
    "lcsc": "lcsc", "jlcpcb": "lcsc",
    "newark": "element14", "farnell": "element14", "element14": "element14",
    "arrow": "arrow",
}
_SLOT_NAME_RE = re.compile(r'^Supplier[\s_]*(\d+)$', re.IGNORECASE)
_PN_WORD = r'(?:#|number|num|no\.?|p/n|pn)'
_SLOT_PN_RE = re.compile(
    rf'^Supplier[\s_]*(?:(\d+)[\s_]*(?:part[\s_]*)?{_PN_WORD}|part[\s_]*{_PN_WORD}[\s_]*(\d+))$',
    re.IGNORECASE)


def _slot_pn_number(name: str):
    """Slot number of a `Supplier N` part number field name, or None."""
    m = _SLOT_PN_RE.match(name.strip())
    return int(m.group(1) or m.group(2)) if m else None


def _symbol_slots(props: dict) -> dict[str, str]:
    """Distributor -> part number from this symbol's own `Supplier N` fields (lowest slot wins)."""
    names = {}
    for name, value in props.items():
        m = _SLOT_NAME_RE.match(name.strip())
        if m and str(value).strip():
            names[int(m.group(1))] = _SUPPLIER_NAME_MAP.get(str(value).strip().lower())
    out: dict[str, str] = {}
    pns = sorted((_slot_pn_number(n), n) for n in props if _slot_pn_number(n) is not None)
    for slot, name in pns:
        dist = names.get(slot)
        pn = str(props[name]).strip()
        if dist in ("digikey", "mouser", "lcsc", "element14") and pn and pn != "~":
            out.setdefault(dist, pn)
    return out
