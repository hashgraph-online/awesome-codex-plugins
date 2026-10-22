#!/usr/bin/env python3
"""BOM Manager — analyze KiCad schematic BOM properties and manage BOM files.

Reads KiCad 6+ .kicad_sch files, detects the project's part number convention,
classifies existing part numbers by distributor, identifies gaps, and outputs a
structured report. Can also export/merge BOM tracking CSV files.

Usage:
    # Analyze a schematic (human-readable output)
    python3 bom_manager.py analyze path/to/schematic.kicad_sch

    # JSON output for programmatic use
    python3 bom_manager.py analyze path/to/schematic.kicad_sch --json

    # Show only parts with missing fields
    python3 bom_manager.py analyze path/to/schematic.kicad_sch --gaps-only

    # Include all hierarchical sub-sheets
    python3 bom_manager.py analyze path/to/schematic.kicad_sch --recursive

    # Export BOM tracking CSV (creates or merges with existing)
    python3 bom_manager.py export path/to/schematic.kicad_sch -o bom/bom.csv

    # Export with recursive sub-sheets
    python3 bom_manager.py export path/to/schematic.kicad_sch -o bom/bom.csv --recursive
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

from kicad_sexp import find_matching_paren, find_sub_sheets

# Allow importing project_config from kicad skill
_kicad_scripts = Path(__file__).resolve().parent.parent.parent / 'kicad' / 'scripts'
if _kicad_scripts.is_dir() and str(_kicad_scripts) not in sys.path:
    sys.path.insert(0, str(_kicad_scripts))

from kicad_utils import (MPN_FIELD_ALIASES, MPN_FIELD_ALIASES_PRIMARY,
                         MPN_FIELD_ALIASES_GENERIC, DIGIKEY_FIELD_ALIASES,
                         normalize_field_name)


# ---------------------------------------------------------------------------
# Field name aliases — maps every known variant to a canonical name
# ---------------------------------------------------------------------------

FIELD_ALIASES: dict[str, list[str]] = {
    # KH-414: shared with analyze_schematic / analyze_pcb (kicad_utils), plus
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

# Build reverse lookup: NORMALIZED field name -> canonical name (KH-414:
# case- and whitespace-insensitive, so "Manufacturer  P/N" == "manufacturer p/n").
_ALIAS_LOOKUP: dict[str, str] = {}
for canonical, aliases in FIELD_ALIASES.items():
    for alias in aliases:
        _ALIAS_LOOKUP[normalize_field_name(alias)] = canonical


def _canonical_for(name: str):
    """Canonical BOM field for an actual KiCad property name, or None."""
    return _ALIAS_LOOKUP.get(normalize_field_name(name))


def _first_nonblank_stripped(props: dict, aliases: frozenset) -> str:
    """First value whose normalized key is in *aliases* and whose .strip() is
    non-empty, returned STRIPPED (final wave fix)."""
    for key, value in props.items():
        v = str(value).strip()
        if v and normalize_field_name(key) in aliases:
            return v
    return ""


def _pick_mpn_from_props(props: dict) -> str:
    """Alias-scan fallback for the mpn canonical (KH-418 tiers; bom-local
    `mp`/`mfn` count as generic). Whitespace-only values are skipped
    (final wave fix)."""
    return (_first_nonblank_stripped(props, MPN_FIELD_ALIASES_PRIMARY)
            or _first_nonblank_stripped(props, MPN_FIELD_ALIASES_GENERIC | frozenset({"mp", "mfn"})))

# Canonical field names to use when creating new properties
CANONICAL_NAMES = {
    "mpn": "MPN",
    "manufacturer": "Manufacturer",
    "digikey": "DigiKey",
    "mouser": "Mouser",
    "lcsc": "LCSC",
    "element14": "element14",
}

# Standard KiCad fields (not BOM-relevant custom fields)
STANDARD_FIELDS = {
    "Reference", "Value", "Footprint", "Datasheet", "Description",
    "Sim.Device", "Sim.Pins", "Sim.Type", "Sim.Name", "Sim.Library",
    "ki_fp_filters", "ki_keywords", "ki_description", "ki_locked",
    "Intersheetrefs",
}

# DNP field name variants
DNP_FIELDS = {"DNP", "dnp", "DONOTPLACE", "DNM", "POPULATE", "Do Not Populate"}

# BOM Comments field name variants — freeform per-component notes for ordering/assembly
# Ordered list for extraction priority (first match wins); set for fast membership checks
_BOM_COMMENT_NAMES = [
    "BOM Comments", "BOM_Comments", "BOM Comment", "BOM_Comment",
    "BOM Notes", "BOM_Notes", "BOM Note", "BOM_Note",
    "Ordering Notes", "Ordering_Notes", "Order Notes",
    "Assembly Notes", "Assembly_Notes",
    "Notes", "Remarks", "Comment",
]
BOM_COMMENT_FIELDS = set(_BOM_COMMENT_NAMES)

# Reference prefix patterns for component classification
_REF_TYPE = {
    "C": "capacitor", "R": "resistor", "L": "inductor", "D": "diode",
    "U": "ic", "Q": "transistor", "J": "connector", "P": "connector",
    "SW": "switch", "F": "fuse", "Y": "crystal", "X": "crystal",
    "BT": "battery", "LS": "speaker", "BZ": "buzzer", "M": "motor",
    "TP": "test_point", "MH": "mounting_hole", "H": "mounting_hole",
    "FL": "filter", "FB": "ferrite_bead", "T": "transformer",
    "K": "relay", "LED": "led",
}


# ---------------------------------------------------------------------------
# Schematic parsing
# ---------------------------------------------------------------------------

def extract_placed_symbols(text: str) -> list[tuple[int, int, str]]:
    """Find all placed symbol blocks (not lib_symbols) in a .kicad_sch file.

    Returns list of (start_pos, end_pos, block_text) tuples.
    """
    symbols = []

    # Find end of lib_symbols section to skip it
    lib_match = re.search(r'\(lib_symbols\b', text)
    search_start = 0
    if lib_match:
        lib_end = find_matching_paren(text, lib_match.start())
        search_start = lib_end + 1

    # Placed symbols have (lib_id ...) as first child; lib symbols have a
    # quoted name string instead. We look for the pattern:
    #   (symbol\n\t\t(lib_id   or   (symbol (lib_id
    pattern = re.compile(r'\(symbol\s*\n?\s*\(lib_id\s+')
    for match in pattern.finditer(text, search_start):
        sym_start = match.start()
        sym_end = find_matching_paren(text, sym_start)
        block = text[sym_start:sym_end + 1]
        symbols.append((sym_start, sym_end, block))

    return symbols


def extract_properties(symbol_block: str) -> dict[str, str]:
    """Extract all (property "name" "value" ...) from a symbol block."""
    props = {}
    for match in re.finditer(
        r'\(property\s+"((?:[^"\\]|\\.)*)"\s+"((?:[^"\\]|\\.)*)"',
        symbol_block,
    ):
        name = match.group(1)
        value = match.group(2)
        props[name] = value
    return props


def is_in_bom(symbol_block: str) -> bool:
    """Check if a symbol has (in_bom yes)."""
    match = re.search(r'\(in_bom\s+(yes|no)\)', symbol_block)
    return match is not None and match.group(1) == "yes"


def is_dnp(symbol_block: str, props: dict[str, str]) -> bool:
    """Check if a symbol is marked DNP."""
    # KiCad 9 built-in DNP flag
    match = re.search(r'\(dnp\s+(yes|no)\)', symbol_block)
    if match and match.group(1) == "yes":
        return True
    # Custom DNP fields
    for field in DNP_FIELDS:
        val = props.get(field, "").strip().upper()
        if val in ("YES", "TRUE", "1", "DNP"):
            return True
        # POPULATE field: "0" means DNP
        if field == "POPULATE" and val == "0":
            return True
    return False


def classify_reference(ref: str) -> str:
    """Classify component type from reference designator prefix."""
    if ref.startswith("#"):
        return "power_symbol"
    # Try longest prefix matches first
    for prefix in sorted(_REF_TYPE, key=len, reverse=True):
        if ref.startswith(prefix):
            return _REF_TYPE[prefix]
    return "other"


# ---------------------------------------------------------------------------
# Part number pattern detection
# ---------------------------------------------------------------------------

def classify_pn_by_pattern(value: str) -> str | None:
    """Try to classify a part number by its pattern. Returns canonical name or None."""
    value = value.strip()
    if not value or value == "~":
        return None

    # DigiKey: ends with -ND (sometimes with digits before ND)
    if re.search(r'-\d*-?ND$', value):
        return "digikey"

    # LCSC: C followed by 3-8 digits (exactly)
    if re.match(r'^C\d{3,8}$', value):
        return "lcsc"

    # Mouser: 2-3 digit numeric prefix + hyphen + alphanumeric manufacturer PN
    if re.match(r'^\d{2,3}-[A-Za-z0-9]', value):
        return "mouser"

    return None


# ---------------------------------------------------------------------------
# Convention detection
# ---------------------------------------------------------------------------

def detect_convention(
    all_symbols: list[dict],
) -> dict:
    """Detect the project's BOM field naming convention.

    Returns a dict describing which field names are used, how they map to
    canonical names, and which distributor appears to be preferred.
    """
    # Count occurrences of each property name across all symbols
    field_counts: Counter[str] = Counter()
    populated_counts: dict[str, int] = {}  # canonical -> count of non-empty values

    # Also detect "Supplier N" / "Supplier N Part #" pattern (KiCad field names)
    # Maps the value inside the Supplier field to canonical distributor names
    _SUPPLIER_NAME_MAP = {
        "digikey": "digikey", "digi-key": "digikey",
        "mouser": "mouser",
        "lcsc": "lcsc", "jlcpcb": "lcsc",
        "newark": "element14", "farnell": "element14", "element14": "element14",
        "arrow": "arrow",
    }
    # Track KiCad "Supplier N" slot mappings: slot_number -> (name_field, pn_field, canonical)
    supplier_slots: dict[int, dict] = {}  # "supplier" here refers to KiCad field names

    for sym in all_symbols:
        for name, value in sym["raw_properties"].items():
            if name in STANDARD_FIELDS:
                continue
            field_counts[name] += 1
            canonical = _canonical_for(name)
            if canonical and value.strip():
                populated_counts[canonical] = populated_counts.get(canonical, 0) + 1

            # Detect KiCad "Supplier N" field pattern
            sup_match = re.match(r'^Supplier\s+(\d+)$', name, re.IGNORECASE)
            if sup_match and value.strip():
                slot = int(sup_match.group(1))
                dist_name = value.strip().lower()
                canonical_sup = _SUPPLIER_NAME_MAP.get(dist_name)
                if canonical_sup and slot not in supplier_slots:
                    supplier_slots[slot] = {
                        "name_field": name,
                        "canonical": canonical_sup,
                    }

            # Detect KiCad "Supplier N Part #" or "Supplier N Part Number" field
            sup_pn_match = re.match(
                r'^Supplier\s+(\d+)\s+Part\s*(?:#|Number|No\.?)$', name, re.IGNORECASE
            )
            if sup_pn_match:
                slot = int(sup_pn_match.group(1))
                if slot in supplier_slots:
                    supplier_slots[slot]["pn_field"] = name
                    # Count this as a populated distributor field
                    can = supplier_slots[slot]["canonical"]
                    if value.strip():
                        populated_counts[can] = populated_counts.get(can, 0) + 1

    # Build field mapping: canonical -> actual field name used in this project
    field_mapping: dict[str, str] = {}
    for name in field_counts:
        canonical = _canonical_for(name)
        if canonical:
            # If multiple aliases map to same canonical, pick the most common
            if canonical not in field_mapping or field_counts[name] > field_counts.get(field_mapping[canonical], 0):
                field_mapping[canonical] = name

    # Add KiCad supplier slot mappings (only if not already mapped by direct field names)
    for slot_info in supplier_slots.values():
        can = slot_info["canonical"]
        if can not in field_mapping and "pn_field" in slot_info:
            field_mapping[can] = slot_info["pn_field"]

    # Determine preferred distributor by populated count
    distributor_counts = {
        k: v for k, v in populated_counts.items()
        if k in ("digikey", "mouser", "lcsc", "element14")
    }
    preferred_distributor = None
    if distributor_counts:
        preferred_distributor = max(distributor_counts, key=distributor_counts.get)

    # Check if field names are already canonical
    names_canonical = all(
        field_mapping.get(c) == CANONICAL_NAMES.get(c)
        for c in field_mapping
        if c in CANONICAL_NAMES
    )

    # What fields should be suggested for new parts
    # Always include MPN + Manufacturer, plus whatever distributors the project uses
    suggested = ["MPN", "Manufacturer"]
    for dist in ("digikey", "mouser", "lcsc", "element14"):
        if dist in field_mapping:
            suggested.append(field_mapping[dist])
        elif dist == preferred_distributor:
            suggested.append(CANONICAL_NAMES[dist])

    return {
        "field_mapping": field_mapping,         # canonical -> actual field name
        "field_counts": dict(field_counts),     # actual field name -> symbol count
        "populated_counts": populated_counts,   # canonical -> non-empty count
        "preferred_distributor": preferred_distributor,
        "names_canonical": names_canonical,
        "suggested_fields": suggested,
    }


# ---------------------------------------------------------------------------
# BOM grouping
# ---------------------------------------------------------------------------

def generate_bom(symbols: list[dict], convention: dict,
                 group_by: str = 'value+footprint') -> list[dict]:
    """Group symbols into BOM lines and identify gaps."""
    groups: dict[tuple, dict] = {}
    seen_refs = set()

    field_map = convention["field_mapping"]

    for sym in symbols:
        ref = sym["reference"]
        comp_type = sym["type"]

        # Skip power symbols and non-BOM components
        if comp_type == "power_symbol" or not sym["in_bom"]:
            continue
        if ref in seen_refs:
            continue
        seen_refs.add(ref)

        props = sym["raw_properties"]

        # Extract canonical field values using the project's actual field names
        def get_canonical(canonical_name: str) -> str:
            if canonical_name == "mpn":
                # KH-418 round 2: the project's declared MPN field is
                # authoritative among manufacturer-specific names when it is
                # itself primary-tier and populated on this symbol — file
                # order only breaks ties between OTHER primaries.
                mpn_field = field_map.get("mpn")
                if (mpn_field and normalize_field_name(mpn_field) in MPN_FIELD_ALIASES_PRIMARY
                        and props.get(mpn_field, "").strip()):
                    return props.get(mpn_field, "").strip()
                # KH-418: a manufacturer-specific field on THIS symbol always
                # outranks the project's convention-majority field when that
                # majority field is generic (El-Luhb: majority field is
                # `Part#`, but this symbol also carries `MPN`).
                primary = _first_nonblank_stripped(props, MPN_FIELD_ALIASES_PRIMARY)
                if primary:
                    return primary
            actual_name = field_map.get(canonical_name)
            if actual_name:
                val = props.get(actual_name, "").strip()
                if val:
                    return val
            # Try all known aliases as fallback (normalized match, KH-414).
            # Also reached when the convention-majority field is empty on
            # this symbol (final wave fix).
            if canonical_name == "mpn":
                return _pick_mpn_from_props(props)
            for actual, val in props.items():
                if _canonical_for(actual) == canonical_name and val.strip():
                    return val.strip()
            return ""

        mpn = get_canonical("mpn")
        manufacturer = get_canonical("manufacturer")
        digikey = get_canonical("digikey")
        mouser = get_canonical("mouser")
        lcsc = get_canonical("lcsc")
        element14 = get_canonical("element14")
        datasheet = props.get("Datasheet", "").strip()
        description = props.get("Description", "").strip()
        value = props.get("Value", "").strip()
        footprint = props.get("Footprint", "").strip()

        # Extract BOM comments — freeform per-component notes
        bom_comment = ""
        for field_name in _BOM_COMMENT_NAMES:
            val = props.get(field_name, "").strip()
            if val:
                bom_comment = val
                break

        if group_by == 'mpn':
            group_key = (mpn,) if mpn else (value, footprint, mpn)
        elif group_by == 'value':
            group_key = (value,)
        else:  # 'value+footprint' — current default
            group_key = (value, footprint, mpn)

        if group_key not in groups:
            groups[group_key] = {
                "value": value,
                "footprint": footprint,
                "mpn": mpn,
                "manufacturer": manufacturer,
                "digikey": digikey,
                "mouser": mouser,
                "lcsc": lcsc,
                "element14": element14,
                "datasheet": datasheet,
                "description": description,
                "bom_comments": [],
                "references": [],
                "quantity": 0,
                "dnp": sym["dnp"],
                "type": comp_type,
            }
        if bom_comment and bom_comment not in groups[group_key]["bom_comments"]:
            groups[group_key]["bom_comments"].append(bom_comment)

        groups[group_key]["references"].append(ref)
        groups[group_key]["quantity"] += 1

    # Sort by first reference
    bom = sorted(
        groups.values(),
        key=lambda g: _ref_sort_key(g["references"][0]) if g["references"] else ("", 0),
    )

    # Identify gaps for each BOM line
    for entry in bom:
        entry["gaps"] = _find_gaps(entry, convention)

    return bom


def _ref_sort_key(ref: str) -> tuple[str, int]:
    """Sort reference designators naturally: C1, C2, C10, R1, U1."""
    match = re.match(r'^([A-Za-z]+)(\d+)$', ref)
    if match:
        return (match.group(1), int(match.group(2)))
    return (ref, 0)


def _find_gaps(entry: dict, convention: dict) -> list[str]:
    """Identify which fields are missing that should be populated."""
    gaps = []
    comp_type = entry["type"]

    # Skip gap analysis for test points, mounting holes, etc.
    if comp_type in ("test_point", "mounting_hole", "power_symbol"):
        return gaps
    if entry["dnp"]:
        return gaps

    # MPN should always be present for real components
    if not entry["mpn"]:
        gaps.append("mpn")

    # Manufacturer is strongly recommended alongside MPN
    if entry["mpn"] and not entry["manufacturer"]:
        gaps.append("manufacturer")

    # Datasheet URL should be present for anything with an MPN
    ds = entry["datasheet"]
    if entry["mpn"] and (not ds or ds == "~" or "://" not in ds):
        gaps.append("datasheet")

    # Check distributor fields that this project uses
    field_map = convention["field_mapping"]
    for dist in ("digikey", "mouser", "lcsc", "element14"):
        if dist in field_map and not entry.get(dist):
            gaps.append(dist)

    return gaps


# ---------------------------------------------------------------------------
# Full analysis
# ---------------------------------------------------------------------------

def parse_schematic_file(filepath: Path) -> tuple[list[dict], str]:
    """Parse a single .kicad_sch file and return (symbols, text)."""
    text = filepath.read_text(encoding="utf-8")
    raw_symbols = extract_placed_symbols(text)

    symbols = []
    for start, end, block in raw_symbols:
        props = extract_properties(block)
        ref = props.get("Reference", "")
        comp_type = classify_reference(ref)

        symbols.append({
            "reference": ref,
            "type": comp_type,
            "in_bom": is_in_bom(block),
            "dnp": is_dnp(block, props),
            "raw_properties": props,
            "source_file": str(filepath),
        })

    return symbols, text


def analyze(
    input_path: Path,
    recursive: bool = False,
    group_by: str = 'value+footprint',
) -> dict:
    """Analyze a KiCad schematic and return full BOM report."""
    files_to_parse = [input_path]

    if recursive:
        # Discover all sub-sheets recursively
        visited = set()
        queue = [input_path]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            text = current.read_text(encoding="utf-8")
            sub_sheets = find_sub_sheets(text, current.parent)
            for ss in sub_sheets:
                if ss not in visited:
                    queue.append(ss)
                    files_to_parse.append(ss)

    # Parse all files
    all_symbols = []
    for fp in files_to_parse:
        syms, _ = parse_schematic_file(fp)
        all_symbols.extend(syms)

    # Detect convention
    convention = detect_convention(all_symbols)

    # Generate BOM
    bom = generate_bom(all_symbols, convention, group_by=group_by)

    # Compute stats
    real_parts = [e for e in bom if e["type"] not in ("power_symbol", "test_point", "mounting_hole")]
    dnp_parts = [e for e in real_parts if e["dnp"]]
    active_parts = [e for e in real_parts if not e["dnp"]]

    stats = {
        "schematic_files": [str(f) for f in files_to_parse],
        "total_bom_lines": len(real_parts),
        "total_components": sum(e["quantity"] for e in real_parts),
        "dnp_lines": len(dnp_parts),
        "active_lines": len(active_parts),
        "active_components": sum(e["quantity"] for e in active_parts),
        "with_mpn": sum(1 for e in active_parts if e["mpn"]),
        "without_mpn": sum(1 for e in active_parts if not e["mpn"]),
        "with_datasheet": sum(1 for e in active_parts if e["datasheet"] and e["datasheet"] != "~" and "://" in e["datasheet"]),
        "without_datasheet": sum(1 for e in active_parts if not e["datasheet"] or e["datasheet"] == "~" or "://" not in e["datasheet"]),
    }
    for dist in ("digikey", "mouser", "lcsc", "element14"):
        stats[f"with_{dist}"] = sum(1 for e in active_parts if e.get(dist))
        stats[f"without_{dist}"] = sum(1 for e in active_parts if not e.get(dist))

    # Detect any unrecognized PNs in generic fields
    unrecognized_fields: dict[str, list[str]] = {}
    for sym in all_symbols:
        for name, value in sym["raw_properties"].items():
            if name in STANDARD_FIELDS or name in DNP_FIELDS or name in BOM_COMMENT_FIELDS:
                continue
            canonical = _canonical_for(name)
            if not canonical and value.strip():
                guess = classify_pn_by_pattern(value)
                if guess:
                    unrecognized_fields.setdefault(name, []).append(
                        f"{value} (looks like {guess})"
                    )

    return {
        "schematic": str(input_path),
        "convention": {
            "field_mapping": convention["field_mapping"],
            "populated_counts": convention["populated_counts"],
            "preferred_distributor": convention["preferred_distributor"],
            "names_canonical": convention["names_canonical"],
            "suggested_fields": convention["suggested_fields"],
        },
        "stats": stats,
        "bom": bom,
        "unrecognized_fields": unrecognized_fields if unrecognized_fields else None,
    }


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_human(report: dict, gaps_only: bool = False) -> str:
    """Format report as human-readable text."""
    lines = []
    conv = report["convention"]
    stats = report["stats"]

    lines.append(f"BOM Analysis: {report['schematic']}")
    lines.append("=" * 60)

    # Convention
    lines.append(f"\nConvention:")
    fm = conv["field_mapping"]
    if fm:
        for canonical, actual in sorted(fm.items()):
            marker = " (canonical)" if actual == CANONICAL_NAMES.get(canonical) else f" -> {canonical}"
            lines.append(f"  {actual}{marker}")
    else:
        lines.append("  No BOM fields detected — this project has no part number tracking yet.")

    if conv["preferred_distributor"]:
        lines.append(f"  Preferred distributor: {conv['preferred_distributor']}")

    # Stats
    lines.append(f"\nStats:")
    lines.append(f"  BOM lines (active): {stats['active_lines']}  ({stats['active_components']} components)")
    lines.append(f"  DNP: {stats['dnp_lines']}")
    lines.append(f"  With MPN: {stats['with_mpn']}/{stats['active_lines']}")
    lines.append(f"  With datasheet URL: {stats['with_datasheet']}/{stats['active_lines']}")
    for dist in ("digikey", "mouser", "lcsc", "element14"):
        w = stats.get(f"with_{dist}", 0)
        if w > 0 or dist in fm:
            lines.append(f"  With {dist}: {w}/{stats['active_lines']}")

    # BOM table
    bom = report["bom"]
    if gaps_only:
        bom = [e for e in bom if e.get("gaps")]

    if bom:
        lines.append(f"\n{'Gaps' if gaps_only else 'BOM'}:")
        lines.append(f"  {'Ref':<12} {'Qty':>3}  {'Value':<20} {'MPN':<30} {'Gaps'}")
        lines.append(f"  {'-'*12} {'-'*3}  {'-'*20} {'-'*30} {'-'*20}")
        for entry in bom:
            if entry["type"] in ("power_symbol",):
                continue
            refs = ",".join(entry["references"][:5])
            if len(entry["references"]) > 5:
                refs += f"...(+{len(entry['references'])-5})"
            gaps_str = ", ".join(entry.get("gaps", []))
            if entry["dnp"]:
                gaps_str = "DNP"
            line = (
                f"  {refs:<12} {entry['quantity']:>3}  {entry['value']:<20} "
                f"{entry['mpn'] or '(none)':<30} {gaps_str}"
            )
            bom_comments = entry.get("bom_comments", [])
            if bom_comments:
                line += f"  [{'; '.join(bom_comments)}]"
            lines.append(line)

    # Unrecognized fields
    if report.get("unrecognized_fields"):
        lines.append(f"\nUnrecognized fields with part-number-like values:")
        for name, examples in report["unrecognized_fields"].items():
            lines.append(f"  '{name}': {examples[0]}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CSV export / merge
# ---------------------------------------------------------------------------

import csv

# Base columns (always present) and distributor column pairs (conditional)
_CSV_BASE_COLUMNS = [
    "Reference", "Qty", "Value", "Footprint", "MPN", "Manufacturer",
]
_CSV_TAIL_COLUMNS = [
    "Chosen_Distributor", "Datasheet", "Validated", "DNP", "Notes",
]

# Map canonical distributor names to CSV column name pairs (PN, Stock)
_DIST_CSV_MAP = {
    "digikey": ("DigiKey", "DK_Stock"),
    "mouser": ("Mouser", "MO_Stock"),
    "lcsc": ("LCSC", "LC_Stock"),
    "element14": ("element14", "E14_Stock"),
}

# Canonical ordering for distributor columns
_DIST_ORDER = ["digikey", "mouser", "lcsc", "element14"]


def _build_csv_columns(active_distributors: list[str]) -> list[str]:
    """Build the CSV column list including only the distributors the project uses."""
    cols = list(_CSV_BASE_COLUMNS)
    for dist in _DIST_ORDER:
        if dist in active_distributors:
            pn_col, stock_col = _DIST_CSV_MAP[dist]
            cols.extend([pn_col, stock_col])
    cols.extend(_CSV_TAIL_COLUMNS)
    return cols


def _detect_active_distributors(report: dict) -> list[str]:
    """Determine which distributors are actively used in a project.

    A distributor is active if:
    - The schematic has any parts with that distributor's PN populated, OR
    - The convention detected a field mapping for that distributor
    """
    active = []
    convention = report.get("convention", {})
    field_mapping = convention.get("field_mapping", {})
    stats = report.get("stats", {})

    for dist in _DIST_ORDER:
        has_mapping = dist in field_mapping
        has_parts = stats.get(f"with_{dist}", 0) > 0
        if has_mapping or has_parts:
            active.append(dist)
    return active


def _short_footprint(fp: str) -> str:
    """Shorten a KiCad footprint path for display: 'Resistor_SMD:R_0805_2012Metric' -> '0805'."""
    if not fp:
        return ""
    # Extract the part after the colon
    if ":" in fp:
        fp = fp.split(":", 1)[1]
    # Try to extract the package size (e.g., 0402, 0805, SOT-23, QFN-24)
    m = re.search(r'(\d{4})_\d{4}Metric', fp)
    if m:
        return m.group(1)
    # Return the whole name minus common prefixes
    for prefix in ("R_", "C_", "L_", "D_"):
        if fp.startswith(prefix):
            fp = fp[len(prefix):]
    return fp


def load_existing_csv(csv_path: Path) -> dict[str, dict]:
    """Load an existing BOM CSV and index by MPN (or Reference as fallback).

    Returns {key: row_dict} where key is MPN if available, else Reference.
    """
    if not csv_path.exists():
        return {}

    rows = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Use MPN as key if available, else first reference
            key = row.get("MPN", "").strip()
            if not key:
                key = row.get("Reference", "").strip().split(",")[0]
            if key:
                rows[key] = dict(row)
    return rows


def export_csv(report: dict, output_path: Path, extra_distributors: list[str] | None = None) -> dict:
    """Export BOM to a tracking CSV, merging with existing data if present.

    Preserves user-edited columns (Chosen_Distributor, Validated, Notes, stock
    counts) from an existing CSV while updating schematic-derived columns.
    Only includes distributor columns for distributors the project actually uses,
    plus any explicitly requested via extra_distributors.
    """
    bom = report["bom"]

    # Determine which suppliers this project uses
    active_distributors = _detect_active_distributors(report)
    # Add explicitly requested suppliers
    if extra_distributors:
        for s in extra_distributors:
            if s in _DIST_CSV_MAP and s not in active_distributors:
                active_distributors.append(s)
    csv_columns = _build_csv_columns(active_distributors)

    # Load existing CSV data to preserve user edits
    existing = load_existing_csv(output_path)

    # If an existing CSV has extra distributor columns (user added one manually),
    # include those too so we don't drop data
    if existing:
        sample = next(iter(existing.values()), {})
        for dist in _DIST_ORDER:
            if dist not in active_distributors:
                pn_col, stock_col = _DIST_CSV_MAP[dist]
                if sample.get(pn_col) or sample.get(stock_col):
                    active_distributors.append(dist)
        csv_columns = _build_csv_columns(active_distributors)

    # User-managed columns (preserved from existing CSV)
    user_columns = {"Chosen_Distributor", "Validated", "Notes"}
    for dist in active_distributors:
        user_columns.add(_DIST_CSV_MAP[dist][1])  # stock columns

    rows = []
    for entry in bom:
        if entry["type"] in ("power_symbol",):
            continue

        refs = ",".join(entry["references"])
        mpn = entry["mpn"]
        fp_short = _short_footprint(entry["footprint"])
        ds = entry["datasheet"] if entry["datasheet"] != "~" else ""

        # Seed Notes from schematic BOM comments (user CSV edits take priority in merge below)
        bom_comments = "; ".join(entry.get("bom_comments", []))

        row = {
            "Reference": refs,
            "Qty": str(entry["quantity"]),
            "Value": entry["value"],
            "Footprint": fp_short,
            "MPN": mpn,
            "Manufacturer": entry["manufacturer"],
            "Datasheet": ds,
            "DNP": "yes" if entry["dnp"] else "",
            "Notes": bom_comments,
        }

        # Only add distributor PN columns for active distributors
        for dist in active_distributors:
            pn_col = _DIST_CSV_MAP[dist][0]
            row[pn_col] = entry.get(dist, "")

        # Merge with existing data — preserve user-managed columns
        existing_row = existing.get(mpn) if mpn else None
        if not existing_row:
            # Try matching by first reference
            first_ref = entry["references"][0] if entry["references"] else ""
            for erow in existing.values():
                if first_ref and first_ref in erow.get("Reference", "").split(","):
                    existing_row = erow
                    break

        if existing_row:
            for col in user_columns:
                if col in existing_row and existing_row[col]:
                    row[col] = existing_row[col]
            # Also preserve distributor PNs from CSV if schematic has none
            for dist in active_distributors:
                dist_col = _DIST_CSV_MAP[dist][0]
                if not row.get(dist_col) and existing_row.get(dist_col):
                    row[dist_col] = existing_row[dist_col]

        # Fill missing columns with empty strings
        for col in csv_columns:
            row.setdefault(col, "")

        rows.append(row)

    # Write CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    active_rows = [r for r in rows if r.get("DNP") != "yes"]
    return {
        "output": str(output_path),
        "total_lines": len(rows),
        "active_lines": len(active_rows),
        "active_distributors": active_distributors,
        "merged_from_existing": sum(1 for _ in existing) if existing else 0,
    }


# ---------------------------------------------------------------------------
# Order file generation
# ---------------------------------------------------------------------------

# Distributor name normalization — map user-entered Chosen_Distributor values to canonical names
_DISTRIBUTOR_NORMALIZE = {
    "digikey": "digikey", "digi-key": "digikey", "dk": "digikey",
    "mouser": "mouser", "mo": "mouser",
    "lcsc": "lcsc", "jlcpcb": "lcsc", "jlc": "lcsc",
    "newark": "element14", "farnell": "element14", "element14": "element14", "e14": "element14",
}


def _normalize_distributor(name: str) -> str:
    """Normalize a distributor name to canonical form."""
    return _DISTRIBUTOR_NORMALIZE.get(name.strip().lower(), name.strip().lower())


def _split_comma_field(value: str) -> list[str]:
    """Split a comma-separated field, stripping whitespace. Returns [''] for empty."""
    if not value or not value.strip():
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def _write_digikey_order(f, lines: list[dict], split_log: list[str]) -> None:
    """Write DigiKey bulk-add paste format: qty, DK_PN, customer_reference."""
    for line in lines:
        refs_safe = line['refs'].replace(",", "/")
        f.write(f"{line['qty']}, {line['pn']}, {refs_safe}\n")
        if line["split"]:
            split_log.append(f"  {line['refs']}: split — {line['pn']} (qty {line['qty']})")


def _write_mouser_order(f, lines: list[dict], split_log: list[str]) -> None:
    """Write Mouser part list import format: Mouser_PN|qty."""
    for line in lines:
        f.write(f"{line['pn']}|{line['qty']}\n")
        if line["split"]:
            split_log.append(f"  {line['refs']}: split — {line['pn']} (qty {line['qty']})")


def _write_lcsc_order(f, lines: list[dict], split_log: list[str]) -> None:
    """Write JLCPCB/LCSC BOM CSV format: Comment,Designator,Footprint,LCSC Part #."""
    writer = csv.writer(f)
    writer.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
    for line in lines:
        writer.writerow([line["value"], line["refs"], line["footprint"], line["pn"]])
        if line["split"]:
            split_log.append(f"  {line['refs']}: split — {line['pn']} ({line['value']})")


def _write_element14_order(f, lines: list[dict], split_log: list[str]) -> None:
    """Write Newark quick order format: PN, qty."""
    for line in lines:
        f.write(f"{line['pn']}, {line['qty']}\n")
        if line["split"]:
            split_log.append(f"  {line['refs']}: split — {line['pn']} (qty {line['qty']})")


def generate_order_files(
    csv_path: Path,
    output_dir: Path,
    boards: int = 1,
    spares: int = 0,
    distributor_filter: str | None = None,
) -> dict:
    """Read a BOM tracking CSV and generate per-distributor order files.

    Args:
        csv_path: Path to BOM tracking CSV
        output_dir: Directory for output order files
        boards: Number of boards being assembled (multiplies all quantities)
        spares: Extra components per line (added after board multiplication)
        distributor_filter: If set, auto-assign this distributor for all parts that
                        have a PN for it, ignoring the Chosen_Distributor column.

    Returns a summary dict with per-distributor stats and any errors.
    """
    if not csv_path.exists():
        return {"error": f"BOM CSV not found: {csv_path}"}

    # Read the BOM CSV
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Distributor PN column mapping: canonical name -> CSV column name
    distributor_pn_col = {
        "digikey": "DigiKey",
        "mouser": "Mouser",
        "lcsc": "LCSC",
        "element14": "element14",
    }

    # Collect order lines per distributor
    orders: dict[str, list[dict]] = {}  # distributor -> [order_line, ...]
    errors = []
    skipped_dnp = []
    skipped_no_distributor = []

    for row in rows:
        refs = row.get("Reference", "").strip()
        qty_str = row.get("Qty", "1").strip()
        qty_per_board = int(qty_str) if qty_str.isdigit() else 1
        qty = qty_per_board * boards + spares

        # Skip DNP
        if row.get("DNP", "").strip().lower() in ("yes", "true", "1", "dnp"):
            skipped_dnp.append(refs)
            continue

        # Determine distributor: use filter override if set, else Chosen_Distributor
        if distributor_filter:
            distributor = _normalize_distributor(distributor_filter)
            pn_col = distributor_pn_col.get(distributor)
            if not pn_col:
                errors.append(f"Unknown distributor filter: '{distributor_filter}'")
                break
            pn_raw = row.get(pn_col, "").strip()
            if not pn_raw:
                skipped_no_distributor.append(refs)
                continue
        else:
            chosen = row.get("Chosen_Distributor", "").strip()
            if not chosen:
                skipped_no_distributor.append(refs)
                continue

            distributor = _normalize_distributor(chosen)
            pn_col = distributor_pn_col.get(distributor)
            if not pn_col:
                errors.append(f"{refs}: unknown distributor '{chosen}'")
                continue

            pn_raw = row.get(pn_col, "").strip()
        value = row.get("Value", "").strip()
        footprint = row.get("Footprint", "").strip()
        mpn = row.get("MPN", "").strip()

        # Split comma-separated PNs (accessory/cable bundled with main part)
        pns = _split_comma_field(pn_raw)
        mpns = _split_comma_field(mpn)

        if not pns:
            label = distributor_filter if distributor_filter else row.get("Chosen_Distributor", "").strip()
            errors.append(f"{refs}: distributor is '{label}' but {pn_col} column is empty")
            continue

        for i, pn in enumerate(pns):
            line_mpn = mpns[i] if i < len(mpns) else (mpns[0] if mpns else "")
            order_line = {
                "pn": pn,
                "qty": qty,
                "refs": refs,
                "value": value,
                "footprint": footprint,
                "mpn": line_mpn,
                "split": len(pns) > 1,
            }
            orders.setdefault(distributor, []).append(order_line)

    # Generate output files
    output_dir.mkdir(parents=True, exist_ok=True)
    files_written = {}
    split_log = []

    _distributor_writers = {
        "digikey": _write_digikey_order,
        "mouser": _write_mouser_order,
        "lcsc": _write_lcsc_order,
        "element14": _write_element14_order,
    }

    for distributor, lines in orders.items():
        writer_fn = _distributor_writers.get(distributor)
        if not writer_fn:
            errors.append(f"No order format defined for distributor '{distributor}', skipping")
            continue

        filename = f"order_{distributor}.csv"
        filepath = output_dir / filename

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer_fn(f, lines, split_log)

        total_components = sum(l["qty"] for l in lines)
        files_written[distributor] = {
            "file": str(filepath),
            "lines": len(lines),
            "components": total_components,
        }

    return {
        "orders": files_written,
        "errors": errors,
        "skipped_dnp": skipped_dnp,
        "skipped_no_distributor": skipped_no_distributor,
        "split_log": split_log,
        "boards": boards,
        "spares": spares,
        "distributor_filter": distributor_filter,
    }


def format_order_summary(result: dict) -> str:
    """Format order generation results for human display."""
    lines = []

    if "error" in result:
        return f"Error: {result['error']}"

    boards = result.get("boards", 1)
    spares = result.get("spares", 0)
    if boards > 1 or spares > 0:
        qty_desc = f"{boards} board{'s' if boards != 1 else ''}"
        if spares > 0:
            qty_desc += f" + {spares} spare{'s' if spares != 1 else ''}/line"
        lines.append(f"Quantity: {qty_desc}")
        lines.append("")

    if result.get("distributor_filter"):
        lines.append(f"Distributor filter: {result['distributor_filter']} (auto-selected from PN columns)")
        lines.append("")

    orders = result.get("orders", {})
    if orders:
        lines.append("Order files generated:")
        for dist, info in orders.items():
            label = {"digikey": "DigiKey", "mouser": "Mouser", "lcsc": "LCSC", "element14": "Newark/element14"}.get(dist, dist)
            lines.append(f"  {label:<20} {info['lines']:>3} lines, {info['components']:>4} components  → {info['file']}")
    else:
        lines.append("No order files generated.")

    if result.get("split_log"):
        lines.append("\nSplit entries (multi-part BOM lines):")
        lines.extend(result["split_log"])

    if result.get("skipped_dnp"):
        lines.append(f"\nDNP (excluded): {', '.join(result['skipped_dnp'])}")

    if result.get("skipped_no_distributor"):
        lines.append(f"\nNo distributor chosen: {', '.join(result['skipped_no_distributor'])}")

    if result.get("errors"):
        lines.append("\nErrors:")
        for err in result["errors"]:
            lines.append(f"  ✗ {err}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Analyze KiCad schematic BOM properties and manage BOM files"
    )
    subparsers = parser.add_subparsers(dest="command")

    # analyze subcommand
    p_analyze = subparsers.add_parser("analyze", help="Analyze schematic BOM properties")
    p_analyze.add_argument("schematic", type=Path, help="Path to .kicad_sch file")
    p_analyze.add_argument("--json", action="store_true", help="Output as JSON")
    p_analyze.add_argument("--gaps-only", action="store_true", help="Show only parts with missing fields")
    p_analyze.add_argument("--recursive", action="store_true", help="Include hierarchical sub-sheets")

    # export subcommand
    p_export = subparsers.add_parser("export", help="Export BOM tracking CSV")
    p_export.add_argument("schematic", type=Path, help="Path to .kicad_sch file")
    p_export.add_argument("-o", "--output", type=Path, required=True, help="Output CSV path")
    p_export.add_argument("--recursive", action="store_true", help="Include hierarchical sub-sheets")
    p_export.add_argument("--add-distributor", action="append", default=[],
                         help="Add distributor columns even if not detected (e.g., --add-distributor mouser)")

    # order subcommand
    p_order = subparsers.add_parser("order", help="Generate per-distributor order files from BOM CSV")
    p_order.add_argument("csv", type=Path, help="Path to BOM tracking CSV")
    p_order.add_argument("-o", "--output-dir", type=Path, default=None,
                         help="Output directory for order files (default: orders/ next to CSV)")
    p_order.add_argument("--boards", type=int, default=1,
                         help="Number of boards (multiplies all quantities, default: 1)")
    p_order.add_argument("--spares", type=int, default=0,
                         help="Extra components per line (added after board multiplication, default: 0)")
    p_order.add_argument("--distributor", type=str, default=None,
                         help="Auto-select distributor for all parts that have its PN (bypasses Chosen_Distributor)")
    p_order.add_argument("--json", action="store_true", help="Output result as JSON")

    # Backwards compat: if first arg is a .kicad_sch file with no subcommand, assume "analyze"
    if len(sys.argv) > 1 and sys.argv[1].endswith(".kicad_sch"):
        sys.argv.insert(1, "analyze")

    args = parser.parse_args()

    # Load project config for BOM preferences
    bom_config: dict = {}
    preferred_suppliers_cfg: list = []
    try:
        from project_config import load_config, get_preferred_suppliers
        sch_dir = str(getattr(args, 'schematic', Path('.')).parent)
        cfg = load_config(sch_dir)
        bom_config = cfg.get('bom', {})
        preferred_suppliers_cfg = get_preferred_suppliers(cfg)
    except (ImportError, Exception):
        pass

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "order":
        # Order subcommand takes a CSV, not a schematic
        if not args.csv.exists():
            print(f"Error: {args.csv} not found", file=sys.stderr)
            sys.exit(1)
        output_dir = args.output_dir or (args.csv.parent / "orders")
        result = generate_order_files(
            args.csv, output_dir,
            boards=args.boards,
            spares=args.spares,
            distributor_filter=args.distributor,
        )
        if args.json:
            json.dump(result, sys.stdout, indent=2)
            print()
        else:
            print(format_order_summary(result), file=sys.stderr)
    else:
        # analyze and export both need a schematic
        if not args.schematic.exists():
            print(f"Error: {args.schematic} not found", file=sys.stderr)
            sys.exit(1)
        if args.schematic.suffix != ".kicad_sch":
            print(f"Error: expected a .kicad_sch file, got {args.schematic.suffix}", file=sys.stderr)
            sys.exit(1)

        if args.command == "analyze":
            group_by = bom_config.get('group_by', 'value+footprint')
            report = analyze(args.schematic, recursive=args.recursive,
                             group_by=group_by)
            # Config override: preferred_suppliers takes precedence
            if preferred_suppliers_cfg:
                report['convention']['preferred_distributor'] = (
                    preferred_suppliers_cfg[0])
                report['convention']['preferred_suppliers'] = (
                    preferred_suppliers_cfg)
            if args.json:
                json.dump(report, sys.stdout, indent=2)
                print()
            else:
                print(format_human(report, gaps_only=args.gaps_only))

        elif args.command == "export":
            group_by = bom_config.get('group_by', 'value+footprint')
            report = analyze(args.schematic, recursive=args.recursive,
                             group_by=group_by)
            extra_distributors = [_normalize_distributor(s)
                                  for s in args.add_distributor]
            # Config-preferred suppliers always get CSV columns
            for s in preferred_suppliers_cfg:
                ns = _normalize_distributor(s)
                if ns not in extra_distributors:
                    extra_distributors.append(ns)
            result = export_csv(report, args.output, extra_distributors=extra_distributors)
            print(f"Exported {result['total_lines']} BOM lines to {result['output']}", file=sys.stderr)
            dist_names = [_DIST_CSV_MAP[s][0] for s in result.get("active_distributors", []) if s in _DIST_CSV_MAP]
            if dist_names:
                print(f"  Distributors: {', '.join(dist_names)}", file=sys.stderr)
            if result["merged_from_existing"]:
                print(f"  Merged with {result['merged_from_existing']} existing rows (preserved stock/distributor/notes)", file=sys.stderr)
            print(f"  Active: {result['active_lines']}, DNP: {result['total_lines'] - result['active_lines']}", file=sys.stderr)


if __name__ == "__main__":
    main()
