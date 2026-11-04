"""Schematic reader: .kicad_sch symbols, pins, wires, labels, sheets → SheetData.

Verbatim moves from analyze_schematic.py; no behaviour change. Reads only — the
net map is built by schematic.connectivity, the hierarchy walk by schematic.hierarchy.
"""
from __future__ import annotations

import os
from pathlib import Path

from kicad_core.sexp import (find_all, find_first, find_deep, get_value, get_property,
                             get_properties, get_at, has_flag, parse_file)
from kicad_core.classify import classify_component, classify_connector, classify_ic_function
from kicad_core.fields import DIGIKEY_FIELD_ALIASES, pick_field, pick_mpn
from kicad_core.model import Component, Pin, SheetData


# ---------------------------------------------------------------------------
# Case-insensitive distributor / MPN property helpers
# ---------------------------------------------------------------------------

# KiCad lets users name fields however they like — "Digikey", "DigiKey",
# "DIGIKEY", "Digi-Key Part Number" are all common.  Rather than maintaining
# an ever-growing list of explicit variants, build a lowercase property dict
# once and match against normalised known aliases.

_MANUFACTURER_KEYS = frozenset({
    "manufacturer", "mfr", "mfg",
})
_MOUSER_KEYS = frozenset({
    "mouser", "mouser part number", "mouser part", "mouser_pn", "mouser pn",
})
_LCSC_KEYS = frozenset({
    "lcsc", "lcsc part #", "lcsc part number", "lcsc part",
    "lcscstockcode", "jlcpcb", "jlcpcb part", "jlc",
})
_ELEMENT14_KEYS = frozenset({
    "newark", "newark part number", "newark_pn", "newark pn",
    "farnell", "farnell part number", "farnell_pn", "farnell pn",
    "element14", "element14 part number", "element14_pn",
})


def extract_lib_symbols(root: list) -> dict:
    """Extract library symbol definitions (pin positions, types).

    For multi-unit symbols (e.g., STM32 with separate GPIO and power units),
    pins are stored per unit so compute_pin_positions can use the correct
    offsets for each placed unit instance.
    """
    lib_symbols_node = find_first(root, "lib_symbols")
    if not lib_symbols_node:
        return {}

    def _parse_single_pin(pin):
        """Parse a single pin S-expression node into a dict."""
        pin_type = pin[1] if len(pin) > 1 else "unknown"
        pin_shape = pin[2] if len(pin) > 2 else "unknown"
        at = get_at(pin)
        pin_name_node = find_first(pin, "name")
        pin_num_node = find_first(pin, "number")
        pin_name = str(pin_name_node[1]) if pin_name_node and len(pin_name_node) > 1 and pin_name_node[1] is not None else ""
        pin_num = str(pin_num_node[1]) if pin_num_node and len(pin_num_node) > 1 and pin_num_node[1] is not None else ""
        # Detect hidden pins — KiCad uses (hide yes) inside pin node
        hidden = has_flag(pin, "hide")
        return {
            "number": pin_num, "name": pin_name,
            "type": pin_type, "shape": pin_shape,
            "offset": list(at) if at else None,
            "hidden": hidden,
        }

    def _extract_pins_from_node(node):
        """Extract pin definitions directly from a symbol node (not recursing into sub-symbols)."""
        return [_parse_single_pin(child) for child in node
                if isinstance(child, list) and len(child) >= 3 and child[0] == "pin"]

    symbols = {}
    for sym in find_all(lib_symbols_node, "symbol"):
        name = sym[1] if len(sym) > 1 else "unknown"
        # Skip sub-unit symbols (e.g., "Device:C_0_1", "Device:C_1_1")
        # Real sub-units have _U_V suffix where BOTH U and V are digits.
        parts = name.split(":")[-1].rsplit("_", 2)
        if len(parts) >= 3 and parts[-1].isdigit() and parts[-2].isdigit():
            continue

        # Collect pins from sub-unit symbols, keyed by unit number.
        # Sub-symbols named like "SymName_U_V" where U is the unit number.
        # Unit 0 sub-symbols (_0_1) contain pins/graphics shared by all units.
        unit_pins: dict[int, list] = {}
        all_pins = []

        for child in sym:
            if not isinstance(child, list) or len(child) < 2 or child[0] != "symbol":
                continue
            sub_name = child[1] if isinstance(child[1], str) else ""
            # Parse unit number from sub-symbol name: "Name_U_V"
            parts = sub_name.rsplit("_", 2)
            if len(parts) >= 3 and parts[-1].isdigit() and parts[-2].isdigit():
                unit_num = int(parts[-2])
                sub_pins = _extract_pins_from_node(child)
                if sub_pins:
                    unit_pins.setdefault(unit_num, []).extend(sub_pins)
                    all_pins.extend(sub_pins)

        # If no sub-unit pins found, fall back to find_deep on the whole symbol
        if not all_pins:
            all_pins = [_parse_single_pin(pin) for pin in find_deep(sym, "pin") if len(pin) >= 3]

        # Get symbol properties
        desc = get_property(sym, "Description") or ""
        ki_keywords = get_property(sym, "ki_keywords") or ""
        ki_fp_filters = get_property(sym, "ki_fp_filters") or ""
        lib_value = get_property(sym, "Value") or ""

        # Check for (power) flag — marks this as a power symbol regardless of lib name
        # KiCad 8+ writes (power global) or (power local); pre-8.0 writes bare (power)
        is_power = any(
            isinstance(child, list) and len(child) >= 1 and child[0] == "power"
            for child in sym
        )
        # Track global vs local power scope (default: global for bare (power))
        power_scope = "global"
        if is_power:
            for child in sym:
                if isinstance(child, list) and len(child) >= 2 and child[0] == "power":
                    power_scope = child[1] if child[1] in ("global", "local") else "global"
                    break

        # Extract alternate pin definitions (dual-function pins, e.g., GPIO/SPI/UART)
        alternates = {}
        for pin in find_deep(sym, "pin"):
            pin_num_node = find_first(pin, "number")
            pin_num = pin_num_node[1] if pin_num_node and len(pin_num_node) > 1 else ""
            alts = []
            for child in pin:
                if isinstance(child, list) and len(child) >= 2 and child[0] == "alternate":
                    alt_name = child[1] if len(child) > 1 else ""
                    alt_type = child[2] if len(child) > 2 else ""
                    alt_shape = child[3] if len(child) > 3 else ""
                    alts.append({"name": alt_name, "type": alt_type, "shape": alt_shape})
            if alts:
                alternates[pin_num] = alts

        symbols[name] = {
            "pins": all_pins,
            "unit_pins": unit_pins if unit_pins else None,
            "value": lib_value,
            "description": desc,
            "keywords": ki_keywords,
            "is_power": is_power,
            "power_scope": power_scope if is_power else None,
            "ki_fp_filters": ki_fp_filters,
            "alternates": alternates if alternates else None,
        }

    return symbols


# KiCad Y-down base TRANSFORM matrix (x1,y1,x2,y2) per (at .. angle),
# from sch_io_kicad_sexpr_parser.cpp:3490-3497 (parseSchematicSymbol T_at).
_ANGLE_TRANSFORM = {
    0:   (1, 0, 0, 1),
    90:  (0, 1, -1, 0),
    180: (-1, 0, 0, -1),
    270: (0, -1, 1, 0),
}


def compute_pin_positions(component: dict, lib_symbols: dict) -> list[Pin]:
    """Compute absolute pin positions for a placed component."""
    lib_id = component.get("lib_id", "")
    lib_name = component.get("lib_name", "")
    # KH-083: Try lib_name first (KiCad 7+ local name), then lib_id
    sym_def = (lib_symbols.get(lib_name) if lib_name else None) or lib_symbols.get(lib_id)
    if not sym_def:
        return []

    cx = component["x"]
    cy = component["y"]
    angle = component["angle"]
    mirror_x = component.get("mirror_x", False)
    mirror_y = component.get("mirror_y", False)

    # For multi-unit symbols, use pins from this unit PLUS unit 0 (shared pins).
    # In KiCad, sub-symbol _0_1 contains pins shared by all units (e.g., power pins).
    unit_num = component.get("unit")
    unit_pins_map = sym_def.get("unit_pins")
    if unit_num and unit_pins_map and unit_num in unit_pins_map:
        pins = list(unit_pins_map[unit_num])
        # Also include unit 0 (shared/common) pins if they exist
        if 0 in unit_pins_map:
            pins.extend(unit_pins_map[0])
    else:
        pins = sym_def["pins"]

    pin_positions = []
    for pin in pins:
        if not pin["offset"]:
            continue
        px, py = pin["offset"][0], pin["offset"][1]

        # Apply transform: prefer raw matrix (legacy KiCad 5) over decomposed angle/mirror
        transform_matrix = component.get("transform_matrix")
        if transform_matrix:
            a, b, c, d = transform_matrix
            rpx = a * px + b * py
            rpy = c * px + d * py
        else:
            # KiCad 6+: decomposed angle + mirror. Compose exactly as KiCad does
            # so rotation+mirror combos match (mirror inverts rotation handedness).
            # KiCad builds a Y-down 2x2 TRANSFORM: the (at .. angle) sets the base
            # rotation matrix, then (mirror x|y) is composed ON THE RIGHT via
            # new = old * mirror (sch_symbol.cpp:SetOrientation, lines 2937-2941).
            # TransformCoordinate(P)=(x1*Px+y1*Py, x2*Px+y2*Py) (kimath transform.cpp:40-43).
            # We work in math-up offsets (Py positive = up), so convert the Y-down
            # result back: rpx = x1*px - y1*py, rpy = -x2*px + y2*py.
            x1, y1, x2, y2 = _ANGLE_TRANSFORM.get(int(angle) % 360, (1, 0, 0, 1))
            if mirror_x:  # compose with SYM_MIRROR_X temp = (1,0,0,-1) on the right
                x1, y1, x2, y2 = x1, y1, -x2, -y2
            if mirror_y:  # compose with SYM_MIRROR_Y temp = (-1,0,0,1) on the right
                x1, y1, x2, y2 = -x1, -y1, x2, y2
            rpx = x1 * px - y1 * py
            rpy = -x2 * px + y2 * py

        # Absolute position: Y-axis inversion (symbol coords are math-up, schematic is screen-down)
        abs_x = round(cx + rpx, 4)
        abs_y = round(cy - rpy, 4)

        # Ensure pin number and name are never None — coerce to string with fallback
        pin_num = pin.get("number")
        pin_name = pin.get("name")
        if pin_num is None:
            pin_num = ""
        else:
            pin_num = str(pin_num)
        if pin_name is None:
            pin_name = ""
        else:
            pin_name = str(pin_name)

        entry = {
            "number": pin_num,
            "name": pin_name,
            "type": pin["type"],
            "x": abs_x,
            "y": abs_y,
        }
        if pin.get("hidden"):
            entry["hidden"] = True
        pin_positions.append(entry)

    return pin_positions


def extract_symbol_instances(root: list) -> dict:
    """Extract (symbol_instances ...) from root schematic.

    Returns a dict mapping path string -> {reference, unit, value, footprint}.
    Path format: "/sheet_uuid/symbol_uuid" or "/sheet_uuid/child_uuid/symbol_uuid".
    """
    result = {}
    si_node = find_first(root, "symbol_instances")
    if not si_node:
        return result
    for path_node in si_node[1:]:
        if not isinstance(path_node, list) or path_node[0] != "path":
            continue
        if len(path_node) < 2:
            continue
        path_str = path_node[1]
        ref = get_value(path_node, "reference") or ""
        unit_val = get_value(path_node, "unit")
        try:
            unit = int(unit_val) if unit_val else 1
        except (ValueError, TypeError):
            unit = 1
        result[path_str] = {
            "reference": ref,
            "unit": unit,
        }
    return result


def extract_components(root: list, lib_symbols: dict, instance_uuid: str = "",
                       symbol_instances: dict | None = None) -> list[Component]:
    """Extract all placed component instances.

    If instance_uuid is provided, remap references from the (instances) block
    for the specified sheet instance (supports multi-instance hierarchical sheets).

    If symbol_instances is provided (from root schematic), use it as a fallback
    when a symbol has no inline (instances) block (common in older KiCad projects).
    """
    components = []

    # Placed symbols are direct children of root with (symbol (lib_id ...))
    for sym in root:
        if not isinstance(sym, list) or len(sym) == 0 or sym[0] != "symbol":
            continue
        # Skip if this is in lib_symbols (those have string name as [1], not a sub-list)
        if len(sym) > 1 and isinstance(sym[1], str):
            continue

        lib_id = get_value(sym, "lib_id")
        if not lib_id:
            continue
        # KH-083: KiCad 7+ uses (lib_name X) when the local symbol name
        # differs from the library's lib_id (e.g., after Eagle import)
        lib_name = get_value(sym, "lib_name") or ""

        at = get_at(sym)
        x, y, angle = at if at else (0, 0, 0)

        # Check for mirror
        mirror_node = find_first(sym, "mirror")
        mirror_x = "x" in mirror_node if mirror_node else False
        mirror_y = "y" in mirror_node if mirror_node else False

        # Extract unit number for multi-unit symbols
        unit_node = find_first(sym, "unit")
        unit_num = int(unit_node[1]) if unit_node and len(unit_node) > 1 else None

        ref = get_property(sym, "Reference") or ""
        value = get_property(sym, "Value")
        # KH-088: Eagle-imported schematics often have NO instance Value property.
        # Fall back to the lib_symbol's Value property only when the property is
        # missing entirely (None), not when it exists but is empty string (KH-230).
        if value is None:
            sym_def_val = lib_symbols.get(lib_id, {})
            value = sym_def_val.get("value", "") or ""
        else:
            value = value or ""
        footprint = get_property(sym, "Footprint") or ""
        datasheet = get_property(sym, "Datasheet") or ""
        description = get_property(sym, "Description") or ""
        uuid_val = get_value(sym, "uuid") or ""

        # Remap reference from (instances) block for multi-instance sheets.
        # Two sources: inline (instances) in each symbol (KiCad 7+), or
        # centralized (symbol_instances) in the root schematic (KiCad 6/older projects).
        if instance_uuid:
            remapped = False
            instances_node = find_first(sym, "instances")
            if instances_node:
                for proj in instances_node[1:]:
                    if not isinstance(proj, list) or proj[0] != "project":
                        continue
                    for path_node in proj[2:]:
                        if not isinstance(path_node, list) or path_node[0] != "path":
                            continue
                        path_str = path_node[1] if len(path_node) > 1 else ""
                        if instance_uuid in path_str:
                            inst_ref = get_value(path_node, "reference")
                            if inst_ref:
                                ref = inst_ref
                                remapped = True
                            inst_unit = get_value(path_node, "unit")
                            if inst_unit:
                                try:
                                    unit_num = int(inst_unit)
                                except (ValueError, TypeError):
                                    pass
                            break

            # Fallback: use centralized symbol_instances from root schematic
            if not remapped and symbol_instances and uuid_val:
                # Build the lookup path: instance_uuid is a full hierarchical
                # path like "/sheet1_uuid" or "/sheet1_uuid/sheet2_uuid".
                # Append the symbol's own UUID to form the full path.
                lookup_path = instance_uuid + "/" + uuid_val
                si_entry = symbol_instances.get(lookup_path)
                if si_entry:
                    if si_entry["reference"]:
                        ref = si_entry["reference"]
                    if si_entry.get("unit"):
                        unit_num = si_entry["unit"]
        _props = get_properties(sym)
        mpn = pick_mpn(_props)
        manufacturer = pick_field(_props, _MANUFACTURER_KEYS)
        digikey = pick_field(_props, DIGIKEY_FIELD_ALIASES)
        mouser = pick_field(_props, _MOUSER_KEYS)
        lcsc = pick_field(_props, _LCSC_KEYS)
        element14 = pick_field(_props, _ELEMENT14_KEYS)

        in_bom = get_value(sym, "in_bom") != "no"
        dnp = get_value(sym, "dnp") == "yes"
        if not dnp and value.upper() in ("DNP", "DO NOT POPULATE", "DO NOT PLACE", "NP"):
            dnp = True
        on_board = get_value(sym, "on_board") != "no"

        # Get pin UUIDs for connectivity
        pin_uuids = {}
        for pin_node in find_all(sym, "pin"):
            if len(pin_node) >= 2:
                pin_num = pin_node[1]
                pin_uuid_node = find_first(pin_node, "uuid")
                if pin_uuid_node and len(pin_uuid_node) > 1:
                    pin_uuids[pin_num] = pin_uuid_node[1]

        comp = {
            "reference": ref,
            "value": value,
            "lib_id": lib_id,
            "lib_name": lib_name,
            "footprint": footprint,
            "datasheet": datasheet,
            "description": description,
            "mpn": mpn,
            "manufacturer": manufacturer,
            "digikey": digikey,
            "mouser": mouser,
            "lcsc": lcsc,
            "element14": element14,
            "x": x,
            "y": y,
            "angle": angle,
            "mirror_x": mirror_x,
            "mirror_y": mirror_y,
            "unit": unit_num,
            "uuid": uuid_val,
            "in_bom": in_bom,
            "dnp": dnp,
            "on_board": on_board,
            "pin_uuids": pin_uuids,
        }

        # Determine component type from reference prefix, lib_id, and lib_symbol flags
        # KH-083: Try lib_name first for correct lib_symbol lookup
        sym_def = (lib_symbols.get(lib_name) if lib_name else None) or lib_symbols.get(lib_id, {})
        is_power_sym = sym_def.get("is_power", False)
        comp["type"] = classify_component(ref, lib_id, value, is_power_sym, footprint, in_bom=in_bom,
                                          description=description, pins=sym_def.get("pins"))
        # Store ki_keywords for downstream analysis (e.g., P-channel detection)
        comp["keywords"] = sym_def.get("keywords", "")
        # Track power scope (global vs local) for connectivity
        if is_power_sym:
            comp["_power_scope"] = sym_def.get("power_scope", "global")

        # Enrich ICs with functional classification
        if comp["type"] == "ic":
            comp["functional_class"] = classify_ic_function(lib_id, value, description)

        # Enrich connectors with external status and layout
        if comp["type"] == "connector":
            pin_count = len(sym_def.get("pins", [])) if sym_def else 0
            is_ext, conn_layout = classify_connector(lib_id, value, pin_count)
            comp["is_external_connector"] = is_ext
            comp["connector_layout"] = conn_layout

        # Compute absolute pin positions
        comp["pins"] = compute_pin_positions(comp, lib_symbols)
        # KH-216: Store unit-valid pin numbers for pin_nets filtering
        comp["_unit_pins"] = {p["number"] for p in comp["pins"]}

        components.append(comp)

    return components


def extract_wires(root: list) -> list[dict]:
    """Extract all wire segments."""
    wires = []
    for wire in find_all(root, "wire"):
        pts = find_first(wire, "pts")
        if not pts:
            continue
        xys = find_all(pts, "xy")
        if len(xys) >= 2:
            wires.append({
                "x1": float(xys[0][1]), "y1": float(xys[0][2]),
                "x2": float(xys[1][1]), "y2": float(xys[1][2]),
            })
    return wires


def extract_labels(root: list) -> list[dict]:
    """Extract all labels (local, global, hierarchical)."""
    labels = []

    for label_type in ["label", "global_label", "hierarchical_label", "directive_label"]:
        for lbl in find_all(root, label_type):
            name = lbl[1] if len(lbl) > 1 else ""
            # KH-078: Malformed s-expressions can yield a list instead of string
            if isinstance(name, list):
                name = str(name[0]) if name else ""
            at = get_at(lbl)
            x, y, angle = at if at else (0, 0, 0)
            # Shape field exists on global_label and hierarchical_label
            # Values: input, output, bidirectional, tri_state, passive
            shape = get_value(lbl, "shape") or ""
            entry = {
                "name": name,
                "type": label_type,
                "x": round(x, 4),
                "y": round(y, 4),
                "angle": angle,
            }
            if shape:
                entry["shape"] = shape
            labels.append(entry)

    return labels


def extract_power_symbols(components: list[dict]) -> list[dict]:
    """Extract power symbols from the component list (they define net names).

    Uses the computed pin positions (not the symbol placement point) so that
    power symbols connect to the correct wire endpoints in the net map.
    """
    power = []
    for comp in components:
        if comp["type"] == "power_symbol":
            # Use pin position if available (more accurate), fall back to symbol position
            pins = comp.get("pins", [])
            if pins:
                # Power symbols typically have one pin — use its position
                px, py = pins[0]["x"], pins[0]["y"]
            else:
                px, py = comp["x"], comp["y"]
            power.append({
                "net_name": comp["value"],
                "x": px,
                "y": py,
                "lib_id": comp["lib_id"],
                "_sheet": comp.get("_sheet", 0),
                "_power_scope": comp.get("_power_scope", "global"),
            })
    return power


def extract_junctions(root: list) -> list[dict]:
    """Extract junction points."""
    junctions = []
    for junc in find_all(root, "junction"):
        at = get_at(junc)
        if at:
            junctions.append({"x": round(at[0], 4), "y": round(at[1], 4)})
    return junctions


def extract_no_connects(root: list) -> list[dict]:
    """Extract no-connect markers."""
    ncs = []
    for nc in find_all(root, "no_connect"):
        at = get_at(nc)
        if at:
            ncs.append({"x": round(at[0], 4), "y": round(at[1], 4)})
    return ncs


def extract_text_annotations(root: list) -> list[dict]:
    """Extract text annotations (non-electrical notes placed on the schematic).

    These are designer notes, TODO comments, revision annotations, etc. placed
    on the schematic sheet as free text objects.  Includes both ``(text ...)``
    and ``(text_box ...)`` elements.
    """
    texts = []
    for txt in find_all(root, "text"):
        content = txt[1] if len(txt) > 1 and isinstance(txt[1], str) else ""
        if not content:
            continue
        at = get_at(txt)
        x, y, angle = at if at else (0, 0, 0)
        texts.append({
            "type": "text",
            "text": content,
            "x": round(x, 4),
            "y": round(y, 4),
            "angle": angle,
        })

    for tb in find_all(root, "text_box"):
        content = tb[1] if len(tb) > 1 and isinstance(tb[1], str) else ""
        if not content:
            continue
        at = get_at(tb)
        x, y, angle = at if at else (0, 0, 0)
        size_node = find_first(tb, "size")
        w = float(size_node[1]) if size_node and len(size_node) > 1 else 0
        h = float(size_node[2]) if size_node and len(size_node) > 2 else 0
        entry: dict = {
            "type": "text_box",
            "text": content,
            "x": round(x, 4),
            "y": round(y, 4),
            "angle": angle,
        }
        if w or h:
            entry["width"] = round(w, 4)
            entry["height"] = round(h, 4)
        texts.append(entry)

    return texts


def extract_bus_elements(root: list) -> dict:
    """Extract bus wires, bus entries, and bus aliases.

    Buses in KiCad group related signals (e.g., D[0..7]) into a single
    graphical wire. Bus entries connect individual signals to/from the bus.
    Bus aliases define named groups of signals.
    """
    buses = []
    for bus in find_all(root, "bus"):
        pts = find_first(bus, "pts")
        if pts:
            xys = find_all(pts, "xy")
            coords = [(float(p[1]), float(p[2])) for p in xys if len(p) > 2]
            for (x1, y1), (x2, y2) in zip(coords, coords[1:]):
                buses.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2})

    bus_entries = []
    for entry in find_all(root, "bus_entry"):
        at = get_at(entry)
        if at:
            size = find_first(entry, "size")
            dx = float(size[1]) if size and len(size) > 1 else 0
            dy = float(size[2]) if size and len(size) > 2 else 0
            bus_entries.append({
                "x": round(at[0], 4), "y": round(at[1], 4),
                "dx": dx, "dy": dy,
            })

    bus_aliases = []
    for alias in find_all(root, "bus_alias"):
        name = alias[1] if len(alias) > 1 and isinstance(alias[1], str) else ""
        members_node = find_first(alias, "members")
        members = []
        if members_node:
            members = [m for m in members_node[1:] if isinstance(m, str)]
        if name:
            bus_aliases.append({"name": name, "members": members})

    return {
        "bus_wires": buses,
        "bus_entries": bus_entries,
        "bus_aliases": bus_aliases,
    }


def extract_title_block(root: list) -> dict:
    """Extract title block metadata (title, date, revision, company, comments).

    The title block is stored in a (title_block ...) node at the top level
    of each schematic sheet.
    """
    tb = find_first(root, "title_block")
    if not tb:
        return {}

    result = {}
    for field in ("title", "date", "rev", "company"):
        val = get_value(tb, field)
        if val:
            result[field] = val

    # Comments are numbered: (comment 1 "text"), (comment 2 "text"), ...
    for child in tb:
        if isinstance(child, list) and len(child) >= 3 and child[0] == "comment":
            try:
                num = int(child[1])
                text = child[2] if isinstance(child[2], str) else ""
                if text:
                    result[f"comment_{num}"] = text
            except (ValueError, TypeError):
                pass

    return result


def parse_single_sheet(path: str, instance_uuid: str = "",
                       symbol_instances: dict | None = None) -> SheetData:
    """Parse a single .kicad_sch file and return raw extracted data.

    If instance_uuid is provided, remap component references from the
    (instances) block for this specific sheet instance.

    If symbol_instances is provided, use it as fallback for remapping when
    inline (instances) blocks are absent.

    Returns: a SheetData (root, components, wires, labels, junctions, no_connects,
              sub_sheet_paths, lib_symbols, text_annotations, bus_elements, title_block)
    """
    root = parse_file(path)
    lib_symbols = extract_lib_symbols(root)
    components = extract_components(root, lib_symbols, instance_uuid=instance_uuid,
                                    symbol_instances=symbol_instances)
    wires = extract_wires(root)
    labels = extract_labels(root)
    junctions = extract_junctions(root)
    no_connects = extract_no_connects(root)
    text_annotations = extract_text_annotations(root)
    bus_elements = extract_bus_elements(root)
    title_block = extract_title_block(root)

    # Find sub-sheet references, including UUIDs for multi-instance support.
    # Also extract sheet pin stubs — these are the parent-side endpoints of
    # hierarchical connections.  Each (pin "NAME" direction (at X Y ANGLE))
    # inside a (sheet) block acts like a hierarchical_label at that position,
    # connecting the parent sheet's wires to the child sheet's matching
    # hierarchical_label via the label name union in build_net_map().
    sub_sheet_paths = []
    base_dir = Path(path).parent
    for sheet in find_all(root, "sheet"):
        # Sheet file property name varies by KiCad version:
        # KiCad 6+: (property "Sheetfile" "filename.kicad_sch")
        # KiCad 7+: (property "Sheet file" "filename.kicad_sch")
        sheet_file = get_property(sheet, "Sheetfile") or get_property(sheet, "Sheet file")
        if sheet_file:
            sub_path = base_dir / sheet_file
            if sub_path.exists():
                sheet_uuid = get_value(sheet, "uuid") or ""
                sub_sheet_paths.append((str(sub_path), sheet_uuid))

        # Extract sheet pin stubs as hierarchical labels so parent-sheet wires
        # connecting to the sheet symbol get unioned with the child sheet's nets.
        # Tag with _sheet_uuid so the traversal loop can namespace them per
        # instance (KH-026: multi-instance hierarchical net isolation).
        sheet_uuid_for_pins = get_value(sheet, "uuid") or ""
        for pin in find_all(sheet, "pin"):
            if len(pin) < 2:
                continue
            pin_name = pin[1]
            at = get_at(pin)
            if at:
                labels.append({
                    "name": pin_name,
                    "type": "hierarchical_label",
                    "x": round(at[0], 4),
                    "y": round(at[1], 4),
                    "angle": at[2] if len(at) > 2 else 0,
                    "_sheet_uuid": sheet_uuid_for_pins,
                })

    return SheetData(root, components, wires, labels, junctions, no_connects,
                     sub_sheet_paths, lib_symbols, text_annotations, bus_elements, title_block)


def detect_sub_sheet(root_tree: list, file_path: str = None) -> bool:
    """Detect whether a parsed schematic is a sub-sheet (not the root).

    Uses a multi-tier heuristic (KH-228, refined KH-304/306):
      1. symbol_instances present → ROOT (KiCad 7+ roots always have this)
      2. sheet blocks present AND not referenced by sibling → ROOT
         (KH-304: intermediate nodes also have sheet blocks; check
         whether a sibling file references us as a child.)
      3. .kicad_pro stem matches file stem → ROOT
         (KH-306: when multiple .kicad_pro exist, only match if ANY
         stem matches; don't blindly pick the first.)
      4. hierarchical_label presence → SUB-SHEET (original heuristic)
      5. Default: not a sub-sheet (standalone single-sheet design)
    """
    # Tier 1: symbol_instances is definitive for KiCad 7+ roots
    has_symbol_instances = find_first(root_tree, "symbol_instances") is not None
    if has_symbol_instances:
        return False

    # Tier 2: Files with (sheet ...) blocks reference other sheets → root
    # KH-304: intermediate sub-sheets also have sheet blocks (they have
    # children). Check if any sibling file references US as a child —
    # if so, we're an intermediate node, not the root.
    has_sheet_blocks = len(find_all(root_tree, "sheet")) > 0
    if has_sheet_blocks:
        if file_path:
            from kicad_core.project import is_referenced_as_child
            if is_referenced_as_child(file_path):
                return True  # Intermediate node — has children but IS a child
        return False  # Has children, not referenced → root

    # Tier 3: .kicad_pro stem matching (reliable across all KiCad versions)
    # KH-306: when multiple .kicad_pro exist, check ALL of them.
    if file_path:
        parent_dir = os.path.dirname(os.path.abspath(file_path))
        file_stem = os.path.splitext(os.path.basename(file_path))[0]
        try:
            pro_stems = [fname[:-len('.kicad_pro')]
                         for fname in os.listdir(parent_dir)
                         if fname.endswith('.kicad_pro')]
            if pro_stems:
                if file_stem in pro_stems:
                    return False  # This file IS a root
                else:
                    return True   # Project(s) exist but this isn't any of them
        except OSError:
            pass

    # Tier 4: hierarchical_label presence (original heuristic)
    has_hier_labels = any(True for _ in find_all(root_tree, "hierarchical_label"))
    if has_hier_labels:
        return True

    # Tier 5: Ambiguous — default to not a sub-sheet
    return False
