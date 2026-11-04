"""Legacy schematic reader: KiCad 5 .sch / .lib → component and wire records.

Verbatim moves from analyze_schematic.py; no behaviour change.
"""
from __future__ import annotations

import re
from pathlib import Path

from kicad_core.sexp import find_all, parse_file
from kicad_core.values import COORD_EPSILON, _MIL_MM, snap_to_mil_grid as _snap_mil
from kicad_core.classify import classify_component
from kicad_core.fields import (
    MPN_FIELD_ALIASES_PRIMARY, MPN_FIELD_ALIASES_GENERIC,
    DIGIKEY_FIELD_ALIASES, normalize_field_name,
)
from schematic.reader import _MANUFACTURER_KEYS, _MOUSER_KEYS, _LCSC_KEYS, _ELEMENT14_KEYS


# KiCad 5 legacy .lib pin type codes → KiCad 6+ type strings
_LEGACY_PIN_TYPE_MAP = {
    "I": "input",
    "O": "output",
    "B": "bidirectional",
    "T": "tri_state",
    "P": "passive",
    "W": "power_in",
    "w": "power_out",
    "C": "open_collector",
    "E": "open_emitter",
    "N": "unconnected",
    "U": "unspecified",
}

# Built-in pin definitions for standard KiCad 4/5 library symbols that won't
# be found in project .lib files (power/device/conn libs).  Offsets are in mm
# at the connection endpoint (where wires attach), matching the output of
# _parse_legacy_lib() after mil→mm conversion.
#
# Values derived from the most common pin positions across 1292 KiCad 4/5
# cache libraries.  Different KiCad versions use slightly different offsets
# (e.g., R/C at ±100, ±150, ±200, or ±250 mils); the wire-snap fallback
# (_snap_pins_to_wires) handles version mismatches automatically.
_M = 0.0254  # 1 mil in mm — shorthand for readability

def _conn_1xN(n):
    """Generate pin list for CONN_01X{n} (single-row, n pins, x=-200 mils)."""
    half = (n - 1) * 50  # half-span in mils
    return [{"number": str(i + 1), "name": f"P{i + 1}", "type": "passive",
             "offset": [-200 * _M, (half - i * 100) * _M]} for i in range(n)]

def _conn_2xN(n):
    """Generate pin list for CONN_02X{n} (2-row, 2n pins, x=±250 mils)."""
    half = (n - 1) * 50
    pins = []
    for i in range(n):
        y = (half - i * 100) * _M
        pins.append({"number": str(2 * i + 1), "name": f"P{2*i+1}", "type": "passive",
                      "offset": [-250 * _M, y]})
        pins.append({"number": str(2 * i + 2), "name": f"P{2*i+2}", "type": "passive",
                      "offset": [250 * _M, y]})
    return pins

_STANDARD_LIB_PINS = {
    # --- Passives (most common: ±150 mils vertical) ---
    "R": [
        {"number": "1", "name": "~", "type": "passive", "offset": [0, 150 * _M]},
        {"number": "2", "name": "~", "type": "passive", "offset": [0, -150 * _M]},
    ],
    "C": [
        {"number": "1", "name": "~", "type": "passive", "offset": [0, 150 * _M]},
        {"number": "2", "name": "~", "type": "passive", "offset": [0, -150 * _M]},
    ],
    "L": [
        {"number": "1", "name": "~", "type": "passive", "offset": [0, 150 * _M]},
        {"number": "2", "name": "~", "type": "passive", "offset": [0, -150 * _M]},
    ],
    "CP": [
        {"number": "1", "name": "~", "type": "passive", "offset": [0, 150 * _M]},
        {"number": "2", "name": "~", "type": "passive", "offset": [0, -150 * _M]},
    ],
    "CP1": [
        {"number": "1", "name": "~", "type": "passive", "offset": [0, 150 * _M]},
        {"number": "2", "name": "~", "type": "passive", "offset": [0, -150 * _M]},
    ],
    "C_Polarized": [
        {"number": "1", "name": "~", "type": "passive", "offset": [0, 150 * _M]},
        {"number": "2", "name": "~", "type": "passive", "offset": [0, -150 * _M]},
    ],
    "INDUCTOR": [
        {"number": "1", "name": "~", "type": "passive", "offset": [0, 300 * _M]},
        {"number": "2", "name": "~", "type": "passive", "offset": [0, -300 * _M]},
    ],
    # --- Small passives (±100 mils vertical) ---
    "C_Small": [
        {"number": "1", "name": "~", "type": "passive", "offset": [0, 100 * _M]},
        {"number": "2", "name": "~", "type": "passive", "offset": [0, -100 * _M]},
    ],
    "R_Small": [
        {"number": "1", "name": "~", "type": "passive", "offset": [0, 100 * _M]},
        {"number": "2", "name": "~", "type": "passive", "offset": [0, -100 * _M]},
    ],
    "L_Small": [
        {"number": "1", "name": "~", "type": "passive", "offset": [0, 100 * _M]},
        {"number": "2", "name": "~", "type": "passive", "offset": [0, -100 * _M]},
    ],
    "INDUCTOR_SMALL": [
        {"number": "1", "name": "~", "type": "passive", "offset": [-250 * _M, 0]},
        {"number": "2", "name": "~", "type": "passive", "offset": [250 * _M, 0]},
    ],
    # --- Diodes (±150 mils horizontal, A=anode K=cathode) ---
    "D": [
        {"number": "1", "name": "K", "type": "passive", "offset": [-150 * _M, 0]},
        {"number": "2", "name": "A", "type": "passive", "offset": [150 * _M, 0]},
    ],
    "D_Schottky": [
        {"number": "1", "name": "K", "type": "passive", "offset": [-150 * _M, 0]},
        {"number": "2", "name": "A", "type": "passive", "offset": [150 * _M, 0]},
    ],
    "D_Zener": [
        {"number": "1", "name": "K", "type": "passive", "offset": [-150 * _M, 0]},
        {"number": "2", "name": "A", "type": "passive", "offset": [150 * _M, 0]},
    ],
    "DIODESCH": [
        {"number": "1", "name": "K", "type": "passive", "offset": [-200 * _M, 0]},
        {"number": "2", "name": "A", "type": "passive", "offset": [200 * _M, 0]},
    ],
    "LED": [
        {"number": "1", "name": "K", "type": "passive", "offset": [-200 * _M, 0]},
        {"number": "2", "name": "A", "type": "passive", "offset": [200 * _M, 0]},
    ],
    # --- Crystals ---
    "CRYSTAL": [
        {"number": "1", "name": "1", "type": "passive", "offset": [-300 * _M, 0]},
        {"number": "2", "name": "2", "type": "passive", "offset": [300 * _M, 0]},
    ],
    "Crystal": [
        {"number": "1", "name": "1", "type": "passive", "offset": [-150 * _M, 0]},
        {"number": "2", "name": "2", "type": "passive", "offset": [150 * _M, 0]},
    ],
    "Crystal_GND24": [
        {"number": "1", "name": "1", "type": "passive", "offset": [-150 * _M, 0]},
        {"number": "2", "name": "2", "type": "passive", "offset": [0, -200 * _M]},
        {"number": "3", "name": "3", "type": "passive", "offset": [150 * _M, 0]},
        {"number": "4", "name": "4", "type": "passive", "offset": [0, 200 * _M]},
    ],
    # --- Switches ---
    "SW_PUSH": [
        {"number": "1", "name": "1", "type": "passive", "offset": [-300 * _M, 0]},
        {"number": "2", "name": "2", "type": "passive", "offset": [300 * _M, 0]},
    ],
    "SW_Push": [
        {"number": "1", "name": "1", "type": "passive", "offset": [-300 * _M, 0]},
        {"number": "2", "name": "2", "type": "passive", "offset": [300 * _M, 0]},
    ],
    # --- Transistors ---
    "Q_NPN_BEC": [
        {"number": "1", "name": "B", "type": "input", "offset": [-200 * _M, 0]},
        {"number": "2", "name": "E", "type": "passive", "offset": [100 * _M, -200 * _M]},
        {"number": "3", "name": "C", "type": "passive", "offset": [100 * _M, 200 * _M]},
    ],
    "Q_PNP_BEC": [
        {"number": "1", "name": "B", "type": "input", "offset": [-200 * _M, 0]},
        {"number": "2", "name": "E", "type": "passive", "offset": [100 * _M, 200 * _M]},
        {"number": "3", "name": "C", "type": "passive", "offset": [100 * _M, -200 * _M]},
    ],
    "Q_NMOS_GSD": [
        {"number": "1", "name": "G", "type": "input", "offset": [-200 * _M, 0]},
        {"number": "2", "name": "S", "type": "passive", "offset": [100 * _M, -200 * _M]},
        {"number": "3", "name": "D", "type": "passive", "offset": [100 * _M, 200 * _M]},
    ],
    "Q_PMOS_GSD": [
        {"number": "1", "name": "G", "type": "input", "offset": [-200 * _M, 0]},
        {"number": "2", "name": "S", "type": "passive", "offset": [100 * _M, 200 * _M]},
        {"number": "3", "name": "D", "type": "passive", "offset": [100 * _M, -200 * _M]},
    ],
    "MOSFET_N": [
        {"number": "1", "name": "G", "type": "input", "offset": [-200 * _M, 0]},
        {"number": "2", "name": "S", "type": "passive", "offset": [100 * _M, -200 * _M]},
        {"number": "3", "name": "D", "type": "passive", "offset": [100 * _M, 200 * _M]},
    ],
    "MOSFET_P": [
        {"number": "1", "name": "G", "type": "input", "offset": [-200 * _M, 0]},
        {"number": "2", "name": "S", "type": "passive", "offset": [100 * _M, 200 * _M]},
        {"number": "3", "name": "D", "type": "passive", "offset": [100 * _M, -200 * _M]},
    ],
    # --- Resistor packs ---
    "R_PACK4": [
        {"number": str(i + 1), "name": f"P{i+1}", "type": "passive",
         "offset": [-200 * _M, (150 - i * 100) * _M]} for i in range(4)
    ] + [
        {"number": str(i + 5), "name": f"R{4-i}", "type": "passive",
         "offset": [200 * _M, (-150 + i * 100) * _M]} for i in range(4)
    ],
    "R_PACK8": [
        {"number": str(i + 1), "name": f"P{i+1}", "type": "passive",
         "offset": [-200 * _M, (350 - i * 100) * _M]} for i in range(8)
    ] + [
        {"number": str(i + 9), "name": f"R{8-i}", "type": "passive",
         "offset": [200 * _M, (-350 + i * 100) * _M]} for i in range(8)
    ],
    # --- Single-row connectors (CONN_01X01 through CONN_01X20) ---
    **{f"CONN_01X{n:02d}": _conn_1xN(n) for n in range(1, 21)},
    # --- Short-form single-row connectors (CONN_1 through CONN_20) ---
    **{f"CONN_{n}": _conn_1xN(n) for n in range(1, 21)},
    # --- Dual-row connectors (CONN_02Xnn format) ---
    **{f"CONN_02X{n:02d}": _conn_2xN(n) for n in range(2, 21)},
    # --- Short-form dual-row connectors (CONN_NX2 format) ---
    **{f"CONN_{n}X2": _conn_2xN(n) for n in range(2, 21)},
    "CONN_5X2": _conn_2xN(5),
}


def _parse_legacy_lib(path: str) -> dict:
    """Parse a KiCad 5 .lib file and return symbol definitions.

    Returns dict matching extract_lib_symbols() format:
    {symbol_name: {"pins": [...], "unit_pins": {unit: [...]}, ...}}
    """
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError:
        return {}

    if not lines or not lines[0].startswith("EESchema-LIBRARY"):
        return {}

    MIL_TO_MM = _MIL_MM
    symbols = {}
    current_name = None
    current_aliases = []  # KH-142: track ALIAS names
    current_pins = []
    current_unit_pins = {}
    current_datasheet = ""
    in_draw = False

    for line in lines:
        line = line.strip()

        if line.startswith("DEF "):
            parts = line.split()
            if len(parts) >= 2:
                current_name = parts[1].lstrip("~")
                current_aliases = []
                current_pins = []
                current_unit_pins = {}
                current_datasheet = ""
                in_draw = False

        elif line.startswith("ALIAS ") and current_name is not None:
            # KH-142: Parse ALIAS directives — alternate names for this symbol
            current_aliases.extend(line.split()[1:])

        elif line.startswith("F3 ") and current_name is not None:
            m = re.match(r'F3\s+"([^"]*)"', line)
            if m:
                current_datasheet = m.group(1)

        elif line == "DRAW":
            in_draw = True

        elif line == "ENDDRAW":
            in_draw = False

        elif line.startswith("X ") and in_draw and current_name is not None:
            # X name number x y length dir sz1 sz2 unit convert elec_type [shape]
            parts = line.split()
            if len(parts) >= 12:
                pin_name = parts[1]
                pin_number = parts[2]
                try:
                    px = int(parts[3]) * MIL_TO_MM
                    py = int(parts[4]) * MIL_TO_MM
                    unit_num = int(parts[9])
                except (ValueError, IndexError):
                    continue
                elec_code = parts[11]
                pin_type = _LEGACY_PIN_TYPE_MAP.get(elec_code, "unspecified")

                pin = {
                    "number": pin_number,
                    "name": pin_name if pin_name != "~" else "",
                    "type": pin_type,
                    "shape": "",
                    "offset": [round(px, 4), round(py, 4)],
                }
                current_pins.append(pin)
                current_unit_pins.setdefault(unit_num, []).append(pin)

        elif line == "ENDDEF" and current_name is not None:
            # Check if multi-unit: has pins in more than one non-zero unit
            non_zero_units = {u for u in current_unit_pins if u != 0}
            has_multi_unit = len(non_zero_units) > 1

            sym_def = {
                "pins": current_pins,
                "unit_pins": current_unit_pins if has_multi_unit else None,
                "description": "",
                "keywords": "",
                "is_power": False,
                "ki_fp_filters": "",
                "alternates": None,
            }
            if current_datasheet:
                sym_def["datasheet"] = current_datasheet
            symbols[current_name] = sym_def
            # KH-142: Register same definition under each alias name
            for alias in current_aliases:
                symbols[alias.lstrip("~")] = sym_def
            current_name = None

    return symbols


def _resolve_legacy_libs(sch_path: str, all_sch_lines: dict) -> tuple:
    """Find and parse .lib files for legacy schematics.

    Args:
        sch_path: Path to the root .sch file.
        all_sch_lines: Dict mapping sheet paths to their lines (for LIBS: extraction).

    Strategy:
    1. Look for *-cache.lib alongside the root .sch file (self-contained, preferred)
    2. Parse LIBS: directives, search for each .lib in project directory tree
    3. Fall back to built-in defaults for standard KiCad symbols

    Returns:
        (symbols, resolution_info) where resolution_info describes which strategy
        was used and how many symbols came from parsed vs built-in sources.
    """
    base = Path(sch_path)
    base_dir = base.parent
    stem = base.stem

    resolution_info = {
        "cache_lib_found": False,
        "sym_lib_table_used": False,
        "libs_directive_used": False,
        "builtin_fallback_count": 0,
        "parsed_lib_count": 0,
    }

    # Strategy 1: cache lib — if present, it contains ALL symbols
    cache_path = base_dir / f"{stem}-cache.lib"
    if cache_path.exists():
        symbols = _parse_legacy_lib(str(cache_path))
        # Also add standard library fallbacks for anything missing
        for name, pins in _STANDARD_LIB_PINS.items():
            if name not in symbols:
                symbols[name] = {
                    "pins": pins, "unit_pins": None, "description": "",
                    "keywords": "", "is_power": False, "ki_fp_filters": "",
                    "alternates": None,
                }
        resolution_info["cache_lib_found"] = True
        resolution_info["parsed_lib_count"] = max(0, len(symbols) - len(_STANDARD_LIB_PINS))
        resolution_info["builtin_fallback_count"] = len(_STANDARD_LIB_PINS)
        return symbols, resolution_info

    # Strategy 2.5: Parse sym-lib-table for legacy library paths (KH-141)
    # KiCad 5 file version 4 uses sym-lib-table instead of LIBS: header directives
    sym_lib_table = base_dir / "sym-lib-table"
    if sym_lib_table.exists():
        slt_symbols = {}
        try:
            slt_root = parse_file(str(sym_lib_table))
            for lib_entry in find_all(slt_root, "lib"):
                lib_type = ""
                lib_uri = ""
                for child in lib_entry:
                    if isinstance(child, list) and len(child) >= 2:
                        if child[0] == "type":
                            lib_type = str(child[1])
                        elif child[0] == "uri":
                            lib_uri = str(child[1])
                if lib_type != "Legacy" or not lib_uri:
                    continue
                # Resolve ${KIPRJMOD} to project directory
                lib_uri = lib_uri.replace("${KIPRJMOD}", str(base_dir))
                lib_path = Path(lib_uri)
                if lib_path.exists():
                    parsed = _parse_legacy_lib(str(lib_path))
                    slt_symbols.update(parsed)
        except (ValueError, IndexError, KeyError, OSError):
            pass  # Don't crash on malformed sym-lib-table
        if slt_symbols:
            # Add standard library fallbacks
            for name, pins in _STANDARD_LIB_PINS.items():
                if name not in slt_symbols:
                    slt_symbols[name] = {
                        "pins": pins, "unit_pins": None, "description": "",
                        "keywords": "", "is_power": False, "ki_fp_filters": "",
                        "alternates": None,
                    }
            resolution_info["sym_lib_table_used"] = True
            resolution_info["parsed_lib_count"] = max(0, len(slt_symbols) - len(_STANDARD_LIB_PINS))
            resolution_info["builtin_fallback_count"] = len(_STANDARD_LIB_PINS)
            return slt_symbols, resolution_info

    # Strategy 2: collect LIBS: directives from all parsed sheets
    lib_names = []
    seen_lib_names = set()
    for sheet_lines in all_sch_lines.values():
        for line in sheet_lines:
            if line.startswith("LIBS:"):
                name = line[5:].strip()
                # Skip cache lib references (they reference the missing cache)
                if name.endswith("-cache") or name.endswith("-rescue"):
                    continue
                # Skip standard KiCad libs we handle with built-in defaults
                if name in ("power", "device", "conn", "transistors",
                            "linear", "regul", "74xx", "cmos4000",
                            "adc-dac", "memory", "xilinx", "microcontrollers",
                            "dsp", "microchip", "analog_switches",
                            "motorola", "texas", "intel", "audio",
                            "interface", "digital-audio", "philips",
                            "display", "cypress", "siliconi", "opto",
                            "atmel", "contrib", "valves"):
                    continue
                if name not in seen_lib_names:
                    lib_names.append(name)
                    seen_lib_names.add(name)

    # Search for each .lib file
    # Build search dirs: from .sch dir, walk up to 4 levels
    search_dirs = []
    d = base_dir
    for _ in range(5):
        search_dirs.append(d)
        # Also check lib/ subdirectory
        lib_subdir = d / "lib"
        if lib_subdir.is_dir():
            search_dirs.append(lib_subdir)
        parent = d.parent
        if parent == d:
            break
        d = parent

    symbols = {}
    for lib_name in lib_names:
        lib_file = f"{lib_name}.lib"
        for search_dir in search_dirs:
            candidate = search_dir / lib_file
            if candidate.exists():
                parsed = _parse_legacy_lib(str(candidate))
                symbols.update(parsed)
                break

    # Add standard library fallbacks
    for name, pins in _STANDARD_LIB_PINS.items():
        if name not in symbols:
            symbols[name] = {
                "pins": pins, "unit_pins": None, "description": "",
                "keywords": "", "is_power": False, "ki_fp_filters": "",
                "alternates": None,
            }

    resolution_info["libs_directive_used"] = bool(lib_names)
    resolution_info["parsed_lib_count"] = max(0, len(symbols) - len(_STANDARD_LIB_PINS))
    resolution_info["builtin_fallback_count"] = len(_STANDARD_LIB_PINS)
    return symbols, resolution_info


def _snap_pins_to_wires(components: list[dict], wires: list[dict]) -> None:
    """Snap component pins to nearby wire endpoints when positions don't match.

    Legacy KiCad standard library pin offsets vary between versions (±100, ±150,
    ±200, ±250 mils for R/C/L/D).  When the built-in fallback positions don't
    match the actual wire endpoints, this function finds the closest wire
    endpoint for each pin and snaps to it.

    Only snaps when the computed position has no wire endpoint within
    COORD_EPSILON, and a wire endpoint exists within _MAX_SNAP_DIST of the
    component center (generous enough for the largest standard symbols).
    """
    _MAX_SNAP_DIST = 12.0  # mm (~470 mils) — covers all standard symbols
    EPS = COORD_EPSILON

    # Build per-sheet wire endpoint set for fast lookup, and list for snapping
    wire_eps_by_sheet: dict[int, set[tuple[float, float]]] = {}
    wire_pts_by_sheet: dict[int, list[tuple[float, float]]] = {}
    for w in wires:
        sheet = w.get("_sheet", 0)
        for x, y in ((w["x1"], w["y1"]), (w["x2"], w["y2"])):
            sx = round(x / EPS) * EPS
            sy = round(y / EPS) * EPS
            wire_eps_by_sheet.setdefault(sheet, set()).add((sx, sy))
            wire_pts_by_sheet.setdefault(sheet, []).append((x, y))

    for comp in components:
        if comp.get("type") in ("power_symbol", "power_flag", "flag"):
            continue
        pins = comp.get("pins")
        if not pins:
            continue

        sheet = comp.get("_sheet", 0)
        wire_set = wire_eps_by_sheet.get(sheet, set())
        wire_list = wire_pts_by_sheet.get(sheet, [])
        cx, cy = comp["x"], comp["y"]

        # Check which pins are already matched to wire endpoints
        unmatched = []
        for pin in pins:
            sk = (round(pin["x"] / EPS) * EPS, round(pin["y"] / EPS) * EPS)
            if sk not in wire_set:
                unmatched.append(pin)

        if not unmatched:
            continue  # all pins already matched

        # Collect nearby wire endpoints (not already claimed by another pin)
        claimed = set()
        for pin in pins:
            if pin not in unmatched:
                claimed.add((round(pin["x"] / EPS) * EPS, round(pin["y"] / EPS) * EPS))

        for pin in unmatched:
            best_dist = _MAX_SNAP_DIST
            best_pt = None
            for wx, wy in wire_list:
                sk = (round(wx / EPS) * EPS, round(wy / EPS) * EPS)
                if sk in claimed:
                    continue
                dx = wx - cx
                dy = wy - cy
                dist = (dx * dx + dy * dy) ** 0.5
                if dist < best_dist:
                    # Prefer wire endpoints roughly in the direction of the
                    # original computed pin (relative to component center)
                    opx, opy = pin["x"] - cx, pin["y"] - cy
                    dot = dx * opx + dy * opy
                    if dot > 0 or (opx == 0 and opy == 0):
                        best_dist = dist
                        best_pt = (wx, wy)
            if best_pt is not None:
                pin["x"] = _snap_mil(best_pt[0])
                pin["y"] = _snap_mil(best_pt[1])
                comp["_pin_source"] = "snapped_to_wire"
                claimed.add((round(pin["x"] / EPS) * EPS, round(pin["y"] / EPS) * EPS))


def _parse_legacy_single_sheet(path: str) -> tuple:
    """Parse a single legacy .sch file and return raw extracted data.

    Returns: (components, wires, labels, junctions, no_connects, sub_sheet_paths, lib_lines)
    where sub_sheet_paths is a list of resolved Path strings for $Sheet references,
    and lib_lines is a list of raw 'LIBS:...' lines from the file header.
    """
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    components = []
    wires = []
    labels = []
    junctions = []
    no_connects = []
    sub_sheet_paths = []

    MIL_TO_MM = _MIL_MM
    base_dir = Path(path).parent

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Component block
        if line == "$Comp":
            comp = {
                "reference": "", "value": "", "lib_id": "", "footprint": "",
                "datasheet": "", "description": "", "mpn": "", "manufacturer": "",
                "digikey": "", "mouser": "", "lcsc": "", "element14": "",
                "x": 0, "y": 0, "angle": 0,
                "mirror_x": False, "mirror_y": False,
                "uuid": "", "in_bom": True, "dnp": False, "on_board": True,
                "pin_uuids": {}, "pins": [], "type": "other",
            }
            i += 1
            while i < len(lines) and lines[i].strip() != "$EndComp":
                cl = lines[i].strip()

                # L Library:Symbol Reference
                if cl.startswith("L "):
                    parts = cl.split()
                    if len(parts) >= 3:
                        comp["lib_id"] = parts[1]
                        comp["reference"] = parts[2]

                # U unit mm_part timestamp
                elif cl.startswith("U "):
                    parts = cl.split()
                    if len(parts) >= 4:
                        comp["uuid"] = parts[3]
                        try:
                            comp["unit"] = int(parts[1])
                        except (ValueError, IndexError):
                            pass

                # P x y
                elif cl.startswith("P "):
                    parts = cl.split()
                    if len(parts) >= 3:
                        comp["x"] = _snap_mil(int(parts[1]) * MIL_TO_MM)
                        comp["y"] = _snap_mil(int(parts[2]) * MIL_TO_MM)

                # F N "value" orientation x y size flags visibility hjustify [font [italic bold]]
                elif cl.startswith("F "):
                    # Parse field: F N "value" ...
                    fm = re.match(r'F\s+(\d+)\s+"([^"]*)"', cl)
                    if fm:
                        field_num = int(fm.group(1))
                        field_val = fm.group(2)
                        if field_num == 0:
                            comp["reference"] = field_val
                        elif field_num == 1:
                            comp["value"] = field_val
                        elif field_num == 2:
                            comp["footprint"] = field_val
                        elif field_num == 3:
                            comp["datasheet"] = field_val
                        # Fields 4+ are custom — try to capture them
                        elif field_num >= 4 and field_val:
                            # Check if the field has a name after the positional data
                            # Format: F N "value" H x y size flags visibility hjustify "FieldName"
                            name_match = re.search(r'"([^"]*)"[^"]*$', cl[fm.end():])
                            fname = name_match.group(1) if name_match else f"Field{field_num}"
                            if name_match:
                                fl = normalize_field_name(fname)
                                if fl in MPN_FIELD_ALIASES_PRIMARY:
                                    # Final wave fix: a blank primary may still SET
                                    # an unset mpn (old last-wins behaviour for
                                    # blank-only symbols) but may not OVERWRITE a
                                    # populated one.
                                    if field_val.strip() or not comp.get("mpn"):
                                        comp["mpn"] = field_val
                                elif fl in MPN_FIELD_ALIASES_GENERIC:
                                    if not (comp.get("mpn") or "").strip():
                                        comp["mpn"] = field_val
                                elif fl in _MANUFACTURER_KEYS:
                                    comp["manufacturer"] = field_val
                                elif fl in DIGIKEY_FIELD_ALIASES:
                                    comp["digikey"] = field_val
                                elif fl in _MOUSER_KEYS:
                                    comp["mouser"] = field_val
                                elif fl in _LCSC_KEYS:
                                    comp["lcsc"] = field_val
                                elif fl in _ELEMENT14_KEYS:
                                    comp["element14"] = field_val
                                elif fl == "dnp":
                                    comp["dnp"] = field_val.strip() not in ("", "0", "false")
                                elif fl in ("note", "notes", "comment"):
                                    if any(dnp_kw in field_val.upper() for dnp_kw in ("DNP", "DO NOT POPULATE", "DO NOT PLACE")):
                                        comp["dnp"] = True
                                elif fl in ("description", "desc"):
                                    comp["description"] = field_val
                            # Track generic-named fields for positional fallback
                            if re.match(r'^Field\d+$', fname):
                                comp.setdefault("_generic_fields", {})[fname] = field_val

                # Orientation matrix line (after position line)
                # Format: a b c d  (2x2 transform matrix [a b; c d])
                # det = a*d - b*c: +1 = no mirror, -1 = mirrored (X axis)
                elif cl and cl[0].isdigit() and len(cl.split()) == 4:
                    parts = cl.split()
                    try:
                        a, b, c, d = [int(p) for p in parts]
                        comp["transform_matrix"] = (a, b, c, d)
                        det = a * d - b * c
                        if det < 0:
                            comp["mirror_x"] = True
                            # Remove mirror to extract pure rotation
                            c, d = -c, -d
                        if (a, b) == (1, 0):
                            comp["angle"] = 0
                        elif (a, b) == (0, 1):
                            comp["angle"] = 90
                        elif (a, b) == (-1, 0):
                            comp["angle"] = 180
                        elif (a, b) == (0, -1):
                            comp["angle"] = 270
                    except ValueError:
                        pass

                i += 1
            # Positional fallback for generic field names (Field1=manufacturer, Field2=MPN)
            gf = comp.pop("_generic_fields", {})
            if not comp.get("mpn") and gf:
                if "Field2" in gf and gf["Field2"]:
                    comp["mpn"] = gf["Field2"]
                if not comp.get("manufacturer") and "Field1" in gf and gf["Field1"]:
                    comp["manufacturer"] = gf["Field1"]

            # Legacy power symbol detection: #PWR/#FLG refs or library named "power"
            lib_prefix = comp["lib_id"].split(":")[0].lower()
            is_power = (comp["reference"].startswith("#")
                        or lib_prefix == "power"
                        or lib_prefix.endswith("_power"))
            # Check value field for DNP indication
            if not comp["dnp"] and comp["value"].upper() in ("DNP", "DO NOT POPULATE", "DO NOT PLACE", "NP"):
                comp["dnp"] = True
            comp["type"] = classify_component(comp["reference"], comp["lib_id"], comp["value"], is_power, comp.get("footprint", ""),
                                              description=comp.get("description", ""))
            components.append(comp)

        # Hierarchical sheet block — extract subsheet filename
        elif line == "$Sheet":
            sheet_file = None
            i += 1
            while i < len(lines) and lines[i].strip() != "$EndSheet":
                sl = lines[i].strip()
                # F1 "filename.sch" size — the sheet filename field
                sm = re.match(r'F1\s+"([^"]+\.sch)"', sl)
                if sm:
                    sheet_file = sm.group(1)
                i += 1
            if sheet_file:
                sub_path = base_dir / sheet_file
                if sub_path.exists():
                    sub_sheet_paths.append(str(sub_path.resolve()))

        # Wire
        elif line == "Wire Wire Line":
            i += 1
            if i < len(lines):
                parts = lines[i].strip().split()
                if len(parts) >= 4:
                    wires.append({
                        "x1": _snap_mil(int(parts[0]) * MIL_TO_MM),
                        "y1": _snap_mil(int(parts[1]) * MIL_TO_MM),
                        "x2": _snap_mil(int(parts[2]) * MIL_TO_MM),
                        "y2": _snap_mil(int(parts[3]) * MIL_TO_MM),
                    })

        # Junction / Connection
        elif line.startswith("Connection ~"):
            parts = line.split()
            if len(parts) >= 4:
                junctions.append({
                    "x": _snap_mil(int(parts[2]) * MIL_TO_MM),
                    "y": _snap_mil(int(parts[3]) * MIL_TO_MM),
                })

        # No-connect
        elif line.startswith("NoConn ~"):
            parts = line.split()
            if len(parts) >= 4:
                no_connects.append({
                    "x": _snap_mil(int(parts[2]) * MIL_TO_MM),
                    "y": _snap_mil(int(parts[3]) * MIL_TO_MM),
                })

        # Labels
        elif line.startswith("Text Label "):
            parts = line.split()
            if len(parts) >= 5:
                x = _snap_mil(int(parts[2]) * MIL_TO_MM)
                y = _snap_mil(int(parts[3]) * MIL_TO_MM)
                # Next line is the label text
                i += 1
                if i < len(lines):
                    name = lines[i].strip()
                    labels.append({"name": name, "type": "label", "x": x, "y": y, "angle": 0})

        elif line.startswith("Text GLabel "):
            parts = line.split()
            if len(parts) >= 5:
                x = _snap_mil(int(parts[2]) * MIL_TO_MM)
                y = _snap_mil(int(parts[3]) * MIL_TO_MM)
                i += 1
                if i < len(lines):
                    name = lines[i].strip()
                    labels.append({"name": name, "type": "global_label", "x": x, "y": y, "angle": 0})

        elif line.startswith("Text HLabel "):
            parts = line.split()
            if len(parts) >= 5:
                x = _snap_mil(int(parts[2]) * MIL_TO_MM)
                y = _snap_mil(int(parts[3]) * MIL_TO_MM)
                i += 1
                if i < len(lines):
                    name = lines[i].strip()
                    labels.append({"name": name, "type": "hierarchical_label", "x": x, "y": y, "angle": 0})

        i += 1

    # Collect LIBS: directives from header for lib resolution
    lib_lines = [l.strip() for l in lines if l.strip().startswith("LIBS:")]

    return components, wires, labels, junctions, no_connects, sub_sheet_paths, lib_lines
