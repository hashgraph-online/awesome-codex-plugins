"""Schematic reader: .kicad_sch symbols, pins, wires, labels, sheets → SheetData.

Reads only — the
net map is built by schematic.connectivity, the hierarchy walk by schematic.hierarchy.
"""
from __future__ import annotations

import os
from pathlib import Path

from kicad_core.sexp import (find_all, find_first, find_deep, get_value, get_property,
                             get_properties, get_at, has_flag, is_keyword, net_name_escape,
                             parse_file, raw_text, unescape_string)
from kicad_core.classify import classify_component, classify_connector, classify_ic_function
from kicad_core.fields import DIGIKEY_FIELD_ALIASES, MANDATORY_STRIP, pick_field, pick_mpn
from kicad_core.instances import (inline_instances, instance_variants, resolve_instance,
                                  tilde_is_empty, variant_overrides)
from kicad_core.project import expand_sheet_file
from kicad_core.model import Component, Pin, SheetData
from kicad_core.textvars import resolve_text_vars, unescape_text_vars


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


def _split_alnum(text: str) -> tuple[str, int]:
    """(prefix, numeric suffix) of a pin number; -1 when it has no trailing digits."""
    i = len(text)
    while i > 0 and text[i - 1] in "0123456789":
        i -= 1
    return (text[:i], int(text[i:])) if i < len(text) else (text, -1)


def _expand_stacked(num: str) -> list[str]:
    """Pin numbers of a KiCad stacked pin number such as "[1-5]" or "[6,7,9-11]".

    As KiCad's ExpandStackedPinNotation: a range needs one alphabetic prefix on both
    ends and start <= end; malformed notation is the literal text as one number.
    """
    if not (num.startswith("[") and num.endswith("]")):
        return [num]
    out = []
    for part in num[1:-1].split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = (t.strip() for t in part.split("-", 1))
            (sp, sv), (ep, ev) = _split_alnum(start), _split_alnum(end)
            if sp != ep or sv < 0 or ev < 0 or sv > ev:
                return [num]
            out.extend(f"{sp}{v}" for v in range(sv, ev + 1))
        else:
            out.append(part)
    return out or [num]


def extract_lib_symbols(root: list) -> dict:
    """Extract library symbol definitions (pin positions, types).

    For multi-unit symbols (e.g., STM32 with separate GPIO and power units),
    pins are stored per unit so compute_pin_positions can use the correct
    offsets for each placed unit instance.
    """
    lib_symbols_node = find_first(root, "lib_symbols")
    if not lib_symbols_node:
        return {}
    tilde_empty = tilde_is_empty(get_value(root, "version"))

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
        parsed = {
            "number": pin_num, "name": pin_name,
            "type": pin_type, "shape": pin_shape,
            "offset": list(at) if at else None,
            "hidden": hidden,
        }
        alts = {str(c[1]): (str(c[2]) if len(c) > 2 else "")
                for c in pin if isinstance(c, list) and len(c) >= 2 and c[0] == "alternate"}
        if alts:
            parsed["_alternates"] = alts
            # KiCad reads a "~" pin name as empty in files older than 20250318.
            parsed["_alt_base"] = "" if tilde_empty and pin_name == "~" else pin_name
        return parsed

    def _extract_pins_from_node(node):
        """Extract pin definitions directly from a symbol node (not recursing into sub-symbols)."""
        return [_parse_single_pin(child) for child in node
                if isinstance(child, list) and len(child) >= 3 and child[0] == "pin"]

    symbols = {}
    for sym in find_all(lib_symbols_node, "symbol"):
        # Every direct child is a symbol; only nested sub-symbols are units, so a name
        # such as "Connector:Raspberry_Pi_2_3" is a symbol of its own.
        name = sym[1] if len(sym) > 1 else "unknown"

        # Collect pins from sub-unit symbols, keyed by unit number.
        # Sub-symbols named like "SymName_U_V": U is the unit, V the body style.
        # Unit 0 sub-symbols (_0_1) contain pins/graphics shared by all units;
        # body style 0 is shared by both bodies, 2 is the De Morgan alternate.
        unit_pins: dict[int, list] = {}
        all_pins = []
        alt_unit_pins: dict[int, list] = {}
        alt_pins = []
        has_alt_body = False
        # Body style -> unit -> pins, for KiCad 10 body styles beyond the De Morgan pair.
        body_unit_pins: dict[int, dict[int, list]] = {}
        # KiCad's unit count is the highest unit number, with or without pins of its own.
        unit_count = 1

        for child in sym:
            if not isinstance(child, list) or len(child) < 2 or child[0] != "symbol":
                continue
            sub_name = child[1] if isinstance(child[1], str) else ""
            # Parse unit number from sub-symbol name: "Name_U_V"
            parts = sub_name.rsplit("_", 2)
            if len(parts) >= 3 and parts[-1].isdigit() and parts[-2].isdigit():
                unit_num = int(parts[-2])
                body_style = int(parts[-1])
                unit_count = max(unit_count, unit_num)
                sub_pins = _extract_pins_from_node(child)
                if sub_pins:
                    if body_style in (0, 1):
                        unit_pins.setdefault(unit_num, []).extend(sub_pins)
                        all_pins.extend(sub_pins)
                    if body_style in (0, 2):
                        alt_unit_pins.setdefault(unit_num, []).extend(sub_pins)
                        alt_pins.extend(sub_pins)
                    has_alt_body = has_alt_body or body_style == 2
                    body_unit_pins.setdefault(body_style, {}).setdefault(unit_num, []).extend(sub_pins)

        # If no sub-unit pins found, fall back to find_deep on the whole symbol
        if not all_pins and not has_alt_body:
            all_pins = [_parse_single_pin(pin) for pin in find_deep(sym, "pin") if len(pin) >= 3]

        # Get symbol properties
        desc = mandatory_field(get_property(sym, "Description"), tilde_empty)
        ki_keywords = _field(get_property(sym, "ki_keywords"), tilde_empty)
        ki_fp_filters = _field(get_property(sym, "ki_fp_filters"), tilde_empty)
        lib_value = mandatory_field(get_property(sym, "Value"), tilde_empty)

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

        # KiCad 10 jumper symbols: pins in one group, or sharing a number, are joined inside it.
        jumper_groups = []
        dup_pin_jumpers = False
        for child in sym:
            if isinstance(child, list) and child and child[0] == "jumper_pin_groups":
                jumper_groups = [{str(m) for m in g} for g in child[1:] if isinstance(g, list)]
            elif isinstance(child, list) and len(child) >= 2 and child[0] == "duplicate_pin_numbers_are_jumpers":
                dup_pin_jumpers = child[1] == "yes"

        symbols[name] = {
            "pins": all_pins,
            "unit_pins": unit_pins if unit_pins else None,
            "unit_count": unit_count,
            "value": lib_value,
            "description": desc,
            "keywords": ki_keywords,
            "is_power": is_power,
            "power_scope": power_scope if is_power else None,
            "ki_fp_filters": ki_fp_filters,
            "alternates": alternates if alternates else None,
        }
        if jumper_groups or dup_pin_jumpers:
            symbols[name]["_jumper_groups"] = jumper_groups
            symbols[name]["_dup_pin_jumpers"] = dup_pin_jumpers
        if any(b >= 3 for b in body_unit_pins):
            symbols[name]["_body_unit_pins"] = {b: m for b, m in body_unit_pins.items() if b == 0 or b >= 3}
        if has_alt_body:
            symbols[name]["alt_unit_pins"] = alt_unit_pins
            symbols[name]["alt_pins"] = alt_pins

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
    # Try lib_name first (KiCad 7+ local name), then lib_id
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
    # A symbol placed with body style 2 (De Morgan) takes the alternate body's pins.
    unit_num = component.get("unit")
    body_style = component.get("_body_style", 1)
    alt_body = body_style == 2 and "alt_pins" in sym_def
    unit_pins_map = sym_def.get("alt_unit_pins") if alt_body else sym_def.get("unit_pins")
    if body_style >= 3 and "_body_unit_pins" in sym_def:
        # KiCad keeps a library pin whose body style is 0 or the placed one.
        pins = []
        for unit_map in (sym_def["_body_unit_pins"].get(body_style, {}),
                         sym_def["_body_unit_pins"].get(0, {})):
            if unit_num:
                pins += list(unit_map.get(unit_num, [])) + list(unit_map.get(0, []))
            else:
                pins += [p for u in sorted(unit_map) for p in unit_map[u]]
    elif alt_body and unit_num and sym_def.get("unit_pins"):
        # KiCad draws this unit's body-0/2 items plus unit 0's; a unit with no
        # alternate-body pins of its own shows only the shared ones.
        unit_pins_map = unit_pins_map or {}
        pins = list(unit_pins_map.get(unit_num, [])) + list(unit_pins_map.get(0, []))
    elif unit_num and unit_pins_map and unit_num not in unit_pins_map:
        # KiCad's GetPins: a unit with no pins of its own has only the common unit-0 pins.
        pins = list(unit_pins_map.get(0, []))
    elif unit_num and unit_pins_map and unit_num in unit_pins_map:
        pins = list(unit_pins_map[unit_num])
        # Also include unit 0 (shared/common) pins if they exist
        if 0 in unit_pins_map:
            pins.extend(unit_pins_map[0])
    else:
        pins = sym_def["alt_pins"] if alt_body else sym_def["pins"]

    pin_positions = []
    for pin in pins:
        if not pin["offset"]:
            continue
        px, py = pin["offset"][0], pin["offset"][1]

        # Apply transform: prefer raw matrix (legacy KiCad 5) over decomposed angle/mirror
        transform_matrix = component.get("transform_matrix")
        if transform_matrix:
            # KiCad negates both the matrix's second column and the .lib pin Y
            # on load, so the file matrix maps the raw offset straight into
            # Y-down sheet space; rpy is negated to cancel the shared inversion.
            a, b, c, d = transform_matrix
            rpx = a * px + b * py
            rpy = -(c * px + d * py)
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

        pin_type = pin["type"]
        # KiCad's SetAlt: a placed alternate applies when it is not the base name and the
        # library pin defines it; the alternate's name and type replace the pin's.
        alt = (component.get("_pin_alternates") or {}).get(pin_num)
        if alt and "_alternates" in pin and alt != pin["_alt_base"] and alt in pin["_alternates"]:
            pin_name, pin_type = alt, pin["_alternates"][alt] or pin_type

        for number in _expand_stacked(pin_num):
            entry = {
                "number": number,
                "name": pin_name,
                "type": pin_type,
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
    tilde_empty = tilde_is_empty(get_value(root, "version"))
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
            "value": mandatory_field(get_value(path_node, "value"), tilde_empty),
            "footprint": mandatory_field(get_value(path_node, "footprint"), tilde_empty),
        }
    return result


# ---------------------------------------------------------------------------
# Text variables in symbol fields (KiCad's SCH_SYMBOL / SCH_SHEET / SCHEMATIC ResolveTextVar)
# ---------------------------------------------------------------------------

_MANDATORY_FIELDS = ("Reference", "Value", "Footprint", "Datasheet", "Description")
_SIM_FIELDS = frozenset({"SIM.DEVICE", "SIM.TYPE", "SIM.PINS", "SIM.PARAMS", "SIM.LIBRARY",
                         "SIM.NAME"})
_TITLE_BLOCK_KEYS = {"ISSUE_DATE": "date", "REVISION": "rev", "TITLE": "title",
                     "COMPANY": "company", **{f"COMMENT{n}": f"comment_{n}" for n in range(1, 10)}}
_SHEET_NAME_FIELDS = {"sheetname": "SHEETNAME", "sheet name": "SHEETNAME",
                      "sheetfile": "SHEETFILE", "sheet file": "SHEETFILE"}


def _has_text_vars(text: str) -> bool:
    return "${" in text or "@{" in text


def _raw_fields(node: list) -> list[tuple[str, str]]:
    """(name, text) of every property of *node*, in file order."""
    fields = []
    for child in node:
        if isinstance(child, list) and len(child) >= 3 and child[0] == "property":
            off = 1 if is_keyword(child[1], "private") else 0
            if len(child) >= 3 + off:
                fields.append((str(child[1 + off]), str(child[2 + off])))
    return fields


def sheet_property(sheet: list, name: str) -> str | None:
    """A (sheet ...) block's name or file property by its SHEETNAME / SHEETFILE role, matched
    in any case under either spelling as KiCad does, with mandatory-field trimming."""
    for key, text in sheet_block_fields(sheet, False)["fields"]:
        if key == name and text:
            return text
    return None


def sheet_block_fields(sheet: list, tilde_empty: bool, overrides: dict | None = None) -> dict:
    """A (sheet ...) block's fields (name and file fields named SHEETNAME / SHEETFILE, the
    names KiCad resolves them by) and its attribute flags; *overrides* are a design variant's
    (kicad_core.instances.variant_overrides)."""
    overrides = overrides or {}
    fields = []
    for name, text in _raw_fields(sheet):
        key = _SHEET_NAME_FIELDS.get(name.lower(), name)
        fields.append((key, overrides.get("fields", {}).get(
            name, mandatory_field(text, tilde_empty) if key in ("SHEETNAME", "SHEETFILE")
            else _field(text, tilde_empty))))
    flags = {"in_bom": get_value(sheet, "in_bom") != "no",
             "on_board": get_value(sheet, "on_board") != "no",
             "dnp": get_value(sheet, "dnp") == "yes",
             "exclude_from_sim": get_value(sheet, "exclude_from_sim") == "yes"}
    flags.update((k, v) for k, v in overrides.items() if k in flags)
    return dict(fields=fields, **flags)


def sheet_chain_node(uuid: str, fields: dict | None) -> dict:
    """One sheet of a text-variable sheet chain; its title block is set when its file is read."""
    fields = fields or {"fields": [], "in_bom": True, "on_board": True, "dnp": False,
                        "exclude_from_sim": False}
    name = next((text for key, text in fields["fields"] if key == "SHEETNAME"), "")
    return dict(fields, uuid=uuid, name=name, title_block={})


def _letter_sub_reference(unit: int, first: int) -> str:
    suffix = ""
    while True:
        u = (unit - 1) % 26
        suffix = chr(first + u) + suffix
        unit = (unit - u) // 26
        if unit <= 0:
            return suffix


def _sub_reference(unit: int, ctx: dict) -> str:
    """The unit suffix KiCad appends to a multi-unit reference (project subpart settings)."""
    if not unit or unit < 1:
        return ""
    sep = ctx.get("subpart_separator") or 0
    first = ctx.get("subpart_first_id") or ord("A")
    prefix = chr(sep) if sep else ""
    if ord("0") <= first <= ord("9"):
        return prefix + str(unit)
    return prefix + _letter_sub_reference(unit, first)


def _project_var(token: str, ctx: dict) -> str | None:
    if token == "PROJECTNAME":
        return ctx.get("project_name", "")
    value = ctx.get("project_vars", {}).get(token)
    return None if value is None else str(value)


def _title_block_var(token: str, title_block: dict, ctx: dict) -> str | None:
    """TITLE_BLOCK::TextVarResolver: a title block token resolves even when the field is empty."""
    key = _TITLE_BLOCK_KEYS.get(token)
    if key is None:
        return None
    value = resolve_text_vars(title_block.get(key, ""), lambda tok, _d: _project_var(tok, ctx))
    return None if value == "${" + token + "}" else value


def _sheet_path_text(nodes: list) -> str:
    """SCH_SHEET_PATH::PathHumanReadable for *nodes* (innermost sheet first, root last)."""
    return "/" + "".join(node["name"] + "/" for node in reversed(nodes[:-1]))


_FLAG_TEXT = {"EXCLUDE_FROM_BOM": "Excluded from BOM", "EXCLUDE_FROM_BOARD": "Excluded from board",
              "EXCLUDE_FROM_SIM": "Excluded from simulation", "DNP": "DNP"}


def _flag_set(flags: dict, token: str) -> bool:
    return {"EXCLUDE_FROM_BOM": not flags["in_bom"], "EXCLUDE_FROM_BOARD": not flags["on_board"],
            "EXCLUDE_FROM_SIM": flags["exclude_from_sim"], "DNP": flags["dnp"]}[token]


def _chain_flag(nodes: list, token: str) -> str | None:
    """An attribute token: its text when any sheet of *nodes* sets the attribute, else ""."""
    if token not in _FLAG_TEXT:
        return None
    return _FLAG_TEXT[token] if any(_flag_set(n, token) for n in nodes) else ""


def _schematic_var(token: str, ctx: dict) -> str | None:
    """SCHEMATIC::ResolveTextVar on the root sheet (page numbers and FILEPATH stay unresolved)."""
    chain = ctx["sheet_chain"]
    if token == "SHEETPATH":
        return "/"
    if token == "SHEETNAME":
        return chain[-1]["name"]
    if token == "FILENAME":
        return ctx.get("filename", "")
    if token == "PROJECTNAME":
        return ctx.get("project_name", "")
    if token in ("VARIANTNAME", "VARIANT", "VARIANT_DESC"):
        return ""
    value = _title_block_var(token, chain[-1]["title_block"], ctx)
    if value is not None:
        return value
    return _project_var(token, ctx)


def _cross_reference(token: str, depth: int, ctx: dict) -> str | None:
    registry = ctx.get("registry")
    return registry.cross_reference(token, depth) if registry is not None else None


def _sheet_var(token: str, k: int, depth: int, ctx: dict) -> str | None:
    """SCH_SHEET::ResolveTextVar for sheet *k* of the chain, then its ancestors."""
    chain = ctx["sheet_chain"]
    if ":" in token:
        value = _cross_reference(token, depth + 1, ctx)
        if value is not None:
            return value
    node = chain[k]
    for name, text in node["fields"]:
        if token == name:
            if _has_text_vars(text):
                text = resolve_text_vars(text, lambda tok, d: _sheet_var(tok, k, d + 1, ctx),
                                         depth + 1)
            return unescape_text_vars(text)
    value = _title_block_var(token, node["title_block"], ctx)
    if value is not None:
        return value
    if token == "SHEETPATH":
        return _sheet_path_text(chain[k:])
    value = _chain_flag(chain[k:], token)
    if value is not None:
        return value
    if k + 1 < len(chain):
        return _sheet_var(token, k + 1, depth + 1, ctx)
    return _schematic_var(token, ctx)


class SymbolText:
    """Shown text of one placed symbol's fields on one sheet path (SCH_FIELD::GetShownText with
    SCH_SYMBOL::ResolveTextVar).  Operating points and pin / net functions stay unresolved."""

    def __init__(self, fields: list[tuple[str, str]], ref: str, unit, unit_count: int,
                 lib_id: str, lib_def: dict, flags: dict, ctx: dict):
        self.fields = fields
        self.ref = ref
        self.unit = unit or 1
        self.unit_count = unit_count
        self.lib_id = lib_id
        self.lib_def = lib_def
        self.flags = flags
        self.ctx = ctx

    def has_text_vars(self) -> bool:
        return any(_has_text_vars(text) for _, text in self.fields)

    def shown(self, text: str, depth: int = 0) -> str:
        if _has_text_vars(text):
            text = resolve_text_vars(text, lambda tok, d: self.var(tok, d + 1), depth)
        return unescape_text_vars(text)

    def _field_text(self, name: str) -> str:
        return next((text for key, text in self.fields if key == name), "")

    def var(self, token: str, depth: int) -> str | None:
        ctx = self.ctx
        if ":" in token:
            value = _cross_reference(token, depth + 1, ctx)
            if value is not None:
                return value
        low = token.lower()
        for name, text in self.fields:
            # a field whose text is just a reference to itself stops resolution
            if text.replace(" ", "").lower() == ("${" + name + "}").lower():
                return token
            if low == name.lower():
                if name == "Reference":
                    return self.ref + (_sub_reference(self.unit, ctx) if self.unit_count > 1 else "")
                return self.shown(text, depth + 1)
        if token in _SIM_FIELDS:
            return ""
        if any(token == t or token == t.upper() for t in ctx.get("template_fields", ())):
            return ""
        if token in ("FOOTPRINT_LIBRARY", "FOOTPRINT_NAME"):
            parts = self.shown(self._field_text("Footprint"), depth + 1).split(":")
            if token == "FOOTPRINT_LIBRARY":
                return parts[0]
            return parts[1] if len(parts) > 1 else ""
        if token == "UNIT":
            return _sub_reference(self.unit, ctx)
        if token == "SHORT_REFERENCE":
            return self.ref
        if token in ("SYMBOL_LIBRARY", "SYMBOL_NAME"):
            nick, sep, name = self.lib_id.partition(":")
            if not sep:
                nick, name = "", self.lib_id
            return nick if token == "SYMBOL_LIBRARY" else name
        if token == "SYMBOL_DESCRIPTION":
            return self.lib_def.get("description", "") or ""
        if token == "SYMBOL_KEYWORDS":
            return self.lib_def.get("keywords", "") or ""
        if token in _FLAG_TEXT:
            if _flag_set(self.flags, token):
                return _FLAG_TEXT[token]
            return _chain_flag(ctx["sheet_chain"], token)
        return _sheet_var(token, 0, depth + 1, ctx)


class TextVarRegistry:
    """Every placed symbol (and sheet) of one schematic, for ``${REF:FIELD}`` cross references.

    References met before the whole schematic is read count in ``pending``; the hierarchy
    walk reads those sheets again once ``ready`` is set."""

    def __init__(self):
        self.refs: list = []
        self.by_uuid: dict = {}
        self.sheets: dict = {}
        self.ready = False
        self.pending = 0

    def add_symbol(self, ref: str, uuid: str, instance_path: str, text: SymbolText) -> None:
        if self.ready:
            return
        self.refs.append((ref, text))
        if uuid:
            self.by_uuid.setdefault(uuid.lower(), []).append((instance_path.rstrip("/").lower(), text))

    def add_sheet(self, uuid: str, ctx: dict) -> None:
        if uuid and not self.ready:
            self.sheets.setdefault(uuid.lower(), ctx)

    def cross_reference(self, token: str, depth: int) -> str | None:
        """SCHEMATIC::ResolveCrossReference."""
        if not self.ready:
            self.pending += 1
            return None
        ref, _, remainder = token.partition(":")
        field_name = remainder.partition(":")[0]
        parts = [p for p in ref.split("/") if p]
        key = parts[-1].lower() if parts else ""
        hits = self.by_uuid.get(key)
        if hits:
            want = ("/" + "/".join(parts[:-1])).lower()
            text = hits[0][1]
            if len(parts) > 1:
                text = next((t for path, t in hits if path == want or path.endswith(want)), text)
            value = text.var(field_name, depth + 1)
            return value if value is not None else f"<Unresolved: {text.ref}:{field_name}>"
        sheet_ctx = self.sheets.get(key)
        if sheet_ctx is not None:
            value = _sheet_var(remainder, 0, depth + 1, sheet_ctx)
            return value if value is not None else token
        found = None
        for sym_ref, text in self.refs:
            if sym_ref == ref:
                found = text
                break
            if len(sym_ref) == len(ref) + 1 and sym_ref.startswith(ref) and "A" <= sym_ref[-1] <= "Z":
                found = text
        if found is None:
            return f"<Unresolved: {ref}>"
        value = found.var(field_name, depth + 1)
        return value if value is not None else f"<Unresolved: {found.ref}:{field_name}>"


def text_context(pro: dict | None, project_name: str, filename: str,
                 registry: TextVarRegistry | None) -> dict:
    """The schematic-wide part of a text-variable context (the caller adds ``sheet_chain``)."""
    sch = (pro or {}).get("schematic") or {}
    drawing = sch.get("drawing") if isinstance(sch.get("drawing"), dict) else {}
    templates = [f.get("name") for f in drawing.get("field_names") or ()
                 if isinstance(f, dict) and isinstance(f.get("name"), str) and f.get("name")]
    variables = (pro or {}).get("text_variables")

    def setting(key, default):
        value = sch.get(key, default)
        return value if isinstance(value, int) and not isinstance(value, bool) else default

    return {"project_vars": variables if isinstance(variables, dict) else {},
            "project_name": project_name, "filename": filename,
            "template_fields": templates,
            "subpart_separator": setting("subpart_id_separator", 0),
            "subpart_first_id": setting("subpart_first_id", ord("A")),
            "registry": registry}


def _field(text, tilde_empty: bool) -> str:
    """A field's text, "" when absent; "~" is empty in files older than 20250318."""
    if text is None or (tilde_empty and text == "~"):
        return ""
    return text


def mandatory_field(text, tilde_empty: bool) -> str:
    """A mandatory field's text as KiCad's SetText keeps it: "~" is tested on the raw token,
    then both ends lose whitespace (space, \t, \n, \v, \f, \r)."""
    return _field(text, tilde_empty).strip(MANDATORY_STRIP)


def _symbol_fields(sym: list, value: str, footprint: str, tilde_empty: bool) -> list[tuple[str, str]]:
    """A placed symbol's fields in KiCad's order: the five mandatory fields (Value and
    Footprint as resolved from the instance), then the others as written."""
    raw = [(name, mandatory_field(text, tilde_empty) if name in _MANDATORY_FIELDS
            else _field(text, tilde_empty)) for name, text in _raw_fields(sym)]
    given = dict(reversed(raw))
    fields = [(name, value if name == "Value" else footprint if name == "Footprint"
               else given.get(name, "")) for name in _MANDATORY_FIELDS]
    seen = set(_MANDATORY_FIELDS)
    for name, text in raw:
        if name not in seen:
            seen.add(name)
            fields.append((name, text))
    return fields


def extract_components(root: list, lib_symbols: dict, instance_uuid: str = "",
                       symbol_instances: dict | None = None, *,
                       instance_path: str | None = None, root_kiid: str = "",
                       project_name: str = "", text_ctx: dict | None = None,
                       variant: str | None = None) -> list[Component]:
    """Extract all placed component instances.

    With *instance_path* (the sheet's full KIID path, root sheet uuid first) each symbol's
    reference and unit come from the instance KiCad 10 uses on that path (see
    kicad_core.instances.resolve_instance); candidates are the root's KiCad 6
    *symbol_instances* entries for the symbol (keyed without the root uuid, so *root_kiid* is
    prefixed) and its inline (instances).  The KiCad 6 entry for this exact path also sets the
    symbol's value and footprint when non-empty; an inline instance's value / footprint sets
    them whichever path carries it.  The caller passes *symbol_instances* only for roots older
    than 20221002, already settled across repeated sheets (schematic.hierarchy).

    Without *instance_path*, *instance_uuid* remaps references from the inline instance whose
    path contains it, falling back to *symbol_instances*.

    With *text_ctx* (see text_context; ``sheet_chain`` lists this sheet first, the root last)
    text variables in the fields expand as KiCad shows them, after the instance values and
    before classification; each symbol is added to the context's registry.

    With *variant* (a KiCad 10 design variant name) the instance's variant block overrides
    the attributes and fields it names; None is the default variant.
    """
    components = []
    file_version = get_value(root, "version")
    tilde_empty = tilde_is_empty(file_version)
    si_by_uuid: dict = {}
    if instance_path is not None and symbol_instances:
        for si_path, entry in symbol_instances.items():
            sheet_path, _, sym_uuid = si_path.rpartition("/")
            si_by_uuid.setdefault(sym_uuid.lower(), []).append((sheet_path, entry))

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
        # KiCad 7+ uses (lib_name X) when the local symbol name
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
        # KiCad 6-9 write (convert N) only when N != 1; KiCad 10 always writes (body_style N)
        body_node = find_first(sym, "body_style") or find_first(sym, "convert")
        try:
            body_style = int(body_node[1]) if body_node and len(body_node) > 1 else 1
        except (ValueError, TypeError):
            body_style = 1

        ref = mandatory_field(get_property(sym, "Reference"), tilde_empty)
        value = get_property(sym, "Value")
        if tilde_empty and value == "~":
            value = ""
        # Eagle-imported schematics often have NO instance Value property.
        # Fall back to the lib_symbol's Value property only when the property is
        # missing entirely (None), not when it exists but is empty string.
        if value is None:
            sym_def_val = (lib_symbols.get(lib_name) if lib_name else None) or lib_symbols.get(lib_id, {})
            value = sym_def_val.get("value", "") or ""
        else:
            value = (value or "").strip(MANDATORY_STRIP)
        footprint = mandatory_field(get_property(sym, "Footprint"), tilde_empty)
        datasheet = mandatory_field(get_property(sym, "Datasheet"), tilde_empty)
        description = mandatory_field(get_property(sym, "Description"), tilde_empty)
        uuid_val = get_value(sym, "uuid") or ""
        overrides = {}

        if instance_path is not None:
            candidates = []
            here = instance_path.rstrip("/").lower()
            for sheet_path, entry in si_by_uuid.get(uuid_val.lower(), ()) if uuid_val else ():
                candidates.append({"path": root_kiid + sheet_path, "project": "",
                                   "reference": entry["reference"], "unit": entry["unit"]})
                if (root_kiid + sheet_path).rstrip("/").lower() == here:
                    if entry["value"]:
                        value = entry["value"]
                    if entry["footprint"]:
                        footprint = entry["footprint"]
            for entry in inline_instances(sym, tilde_empty):
                candidates.append(entry)
                if "value" in entry:
                    value = entry["value"]
                if "footprint" in entry:
                    footprint = entry["footprint"]
            hit = resolve_instance(candidates, instance_path, project_name)
            if hit is not None:
                if hit["reference"]:
                    ref = hit["reference"]
                if hit["unit"]:
                    unit_num = hit["unit"]
                overrides = variant_overrides(hit.get("variants"), variant, file_version)
        elif instance_uuid:
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
        if tilde_empty:
            _props = {k: _field(v, True) for k, v in _props.items()}
        sym_def = (lib_symbols.get(lib_name) if lib_name else None) or lib_symbols.get(lib_id, {})
        # A power symbol keeps its own Value: KiCad names its net without the variant
        var_fields = {} if sym_def.get("is_power") else overrides.get("fields", {})
        if var_fields:
            value = var_fields.get("Value", value)
            footprint = var_fields.get("Footprint", footprint)
            datasheet = var_fields.get("Datasheet", datasheet)
            description = var_fields.get("Description", description)
            # _props keys are lower-cased; a variant names its fields as the symbol does
            var_props = {k.lower(): v for k, v in var_fields.items()}
            _props = {k: var_props.get(k, v) for k, v in _props.items()}
        in_bom = overrides.get("in_bom", get_value(sym, "in_bom") != "no")
        dnp_token = get_value(sym, "dnp")
        if "dnp" in overrides:
            dnp_token = "yes" if overrides["dnp"] else "no"
        on_board = overrides.get("on_board", get_value(sym, "on_board") != "no")
        unit_count = sum(1 for u in (sym_def.get("unit_pins") or {}) if u > 0)
        if text_ctx is not None:
            fields = [(name, var_fields.get(name, text))
                      for name, text in _symbol_fields(sym, value, footprint, tilde_empty)]
            flags = {"in_bom": in_bom, "on_board": on_board, "dnp": dnp_token == "yes",
                     "exclude_from_sim": overrides.get(
                         "exclude_from_sim", get_value(sym, "exclude_from_sim") == "yes")}
            text = SymbolText(fields, ref, unit_num, unit_count, lib_id, sym_def, flags, text_ctx)
            registry = text_ctx.get("registry")
            if registry is not None:
                registry.add_symbol(ref, uuid_val, instance_path or "", text)
            if text.has_text_vars():
                value = text.shown(value)
                footprint = text.shown(footprint)
                datasheet = text.shown(datasheet)
                description = text.shown(description)
                _props = {k: text.shown(v) for k, v in _props.items()}
        mpn = pick_mpn(_props)
        manufacturer = pick_field(_props, _MANUFACTURER_KEYS)
        digikey = pick_field(_props, DIGIKEY_FIELD_ALIASES)
        mouser = pick_field(_props, _MOUSER_KEYS)
        lcsc = pick_field(_props, _LCSC_KEYS)
        element14 = pick_field(_props, _ELEMENT14_KEYS)

        dnp = dnp_token == "yes"
        # KiCad reads only the attribute; the Value guess remains for files without one (KiCad 6)
        if dnp_token is None and value.upper() in ("DNP", "DO NOT POPULATE", "DO NOT PLACE", "NP"):
            dnp = True

        # Get pin UUIDs for connectivity
        pin_uuids = {}
        pin_alternates = {}
        for pin_node in find_all(sym, "pin"):
            if len(pin_node) >= 2:
                pin_num = pin_node[1]
                pin_uuid_node = find_first(pin_node, "uuid")
                if pin_uuid_node and len(pin_uuid_node) > 1:
                    pin_uuids[pin_num] = pin_uuid_node[1]
                alt_node = find_first(pin_node, "alternate")
                if alt_node and len(alt_node) > 1 and alt_node[1]:
                    pin_alternates[str(pin_num)] = str(alt_node[1])

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
            "_body_style": body_style,
            "_pin_alternates": pin_alternates,
            "_unit_count": unit_count,
        }

        # Determine component type from reference prefix, lib_id, and lib_symbol flags
        # lib_name is tried first for the lib_symbol lookup (sym_def above)
        is_power_sym = sym_def.get("is_power", False)
        # A stacked pin ("[1-5]") counts once per contact, as in KiCad's netlist.
        lib_pins = sym_def.get("pins")
        if lib_pins is not None:
            lib_pins = [p for p in lib_pins for _ in _expand_stacked(p["number"])]
        comp["type"] = classify_component(ref, lib_id, value, is_power_sym, footprint, in_bom=in_bom,
                                          description=description, pins=lib_pins)
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
            pin_count = len(lib_pins or [])
            is_ext, conn_layout = classify_connector(lib_id, value, pin_count)
            comp["is_external_connector"] = is_ext
            comp["connector_layout"] = conn_layout

        if sym_def.get("_jumper_groups") or sym_def.get("_dup_pin_jumpers"):
            comp["_jumper_groups"] = (sym_def.get("_jumper_groups", []),
                                      sym_def.get("_dup_pin_jumpers", False))
        # Compute absolute pin positions
        comp["pins"] = compute_pin_positions(comp, lib_symbols)
        # Store unit-valid pin numbers for pin_nets filtering
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
            # Malformed s-expressions can yield a list instead of string
            if isinstance(name, list):
                name = str(name[0]) if name else ""
            else:
                name = label_net_name(name)
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


def label_net_name(token) -> str:
    """The net name KiCad gives a label or sheet pin: its shown text escaped as a net name
    (sch_label.cpp, EscapeString(GetShownText(), CTX_NETNAME))."""
    return net_name_escape(unescape_string(raw_text(token)))


def rename_legacy_power_symbols(components: list[dict]) -> None:
    """Set each global power symbol's Value to the name of its first pin when that pin is a
    hidden power input, as KiCad 10 does on loading a file older than 20230221 or a KiCad 5
    schematic (SCH_SCREEN::FixLegacyPowerSymbolMismatches). A visible pin keeps the Value."""
    for comp in components:
        if comp.get("type") != "power_symbol" or comp.get("_power_scope") == "local":
            continue
        pins = comp.get("pins") or []
        first = pins[0] if pins else None
        if first and first.get("type") == "power_in" and first.get("hidden") and first.get("name"):
            comp["value"] = first["name"]


def power_symbol_drives(comp: dict) -> bool:
    """True when a power symbol names and joins its net by its Value.

    KiCad drives a net name only from a power-input pin, so a PWR_FLAG (power output) never
    joins anything by name.  A symbol without parsed pins (missing library) keeps its Value.
    """
    pins = comp.get("pins") or []
    return not pins or pins[0].get("type") == "power_in"


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
                # sch_pin.cpp: EscapeString(shown Value, CTX_NETNAME)
                "net_name": net_name_escape(comp["value"]),
                "x": px,
                "y": py,
                "lib_id": comp["lib_id"],
                "_sheet": comp.get("_sheet", 0),
                "_power_scope": comp.get("_power_scope", "global"),
                "_drives": power_symbol_drives(comp),
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
            # sch_connection.cpp escapes each member as written (EscapeString, CTX_NETNAME).
            members = [net_name_escape(raw_text(m)) for m in members_node[1:] if isinstance(m, str)]
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
                       symbol_instances: dict | None = None, *,
                       instance_path: str | None = None, root_kiid: str = "",
                       project_name: str = "", text_ctx: dict | None = None,
                       variant: str | None = None) -> SheetData:
    """Parse a single .kicad_sch file and return raw extracted data.

    If instance_uuid is provided, remap component references from the
    (instances) block for this specific sheet instance.

    If symbol_instances is provided, use it as fallback for remapping when
    inline (instances) blocks are absent.

    instance_path / root_kiid / project_name / text_ctx / variant: see extract_components;
    this file's title block becomes the first sheet of text_ctx's chain.  A sub-sheet's
    variant block is the one of its instance on *instance_path*.

    Returns: a SheetData (root, components, wires, labels, junctions, no_connects,
              sub_sheet_paths, lib_symbols, text_annotations, bus_elements, title_block)
    """
    root = parse_file(path)
    lib_symbols = extract_lib_symbols(root)
    title_block = extract_title_block(root)
    if text_ctx is not None:
        text_ctx["sheet_chain"][0]["title_block"] = title_block
    components = extract_components(root, lib_symbols, instance_uuid=instance_uuid,
                                    symbol_instances=symbol_instances,
                                    instance_path=instance_path, root_kiid=root_kiid,
                                    project_name=project_name, text_ctx=text_ctx,
                                    variant=variant)
    wires = extract_wires(root)
    labels = extract_labels(root)
    junctions = extract_junctions(root)
    no_connects = extract_no_connects(root)
    text_annotations = extract_text_annotations(root)
    bus_elements = extract_bus_elements(root)
    file_version = get_value(root, "version")
    tilde_empty = tilde_is_empty(file_version)

    # Find sub-sheet references, including UUIDs for multi-instance support.
    # Also extract sheet pin stubs — these are the parent-side endpoints of
    # hierarchical connections.  Each (pin "NAME" direction (at X Y ANGLE))
    # inside a (sheet) block acts like a hierarchical_label at that position,
    # connecting the parent sheet's wires to the child sheet's matching
    # hierarchical_label via the label name union in build_net_map().
    sub_sheet_paths = []
    sheet_fields = {}
    base_dir = Path(path).parent
    for sheet in sorted(find_all(root, "sheet"), key=_sheet_order_key):
        overrides = {}
        if variant is not None and instance_path is not None:
            overrides = variant_overrides(instance_variants(sheet, instance_path), variant,
                                          file_version)
        sheet_fields.setdefault(get_value(sheet, "uuid") or "",
                                sheet_block_fields(sheet, tilde_empty, overrides))
        # Sheet file property name varies by KiCad version:
        # KiCad 6+: (property "Sheetfile" "filename.kicad_sch")
        # KiCad 7+: (property "Sheet file" "filename.kicad_sch")
        sheet_file = sheet_property(sheet, "SHEETFILE")
        if sheet_file:
            sub_path = base_dir / expand_sheet_file(sheet_file, path)
            if sub_path.exists():
                sheet_uuid = get_value(sheet, "uuid") or ""
                sub_sheet_paths.append((str(sub_path), sheet_uuid))

        # Extract sheet pin stubs as hierarchical labels so parent-sheet wires
        # connecting to the sheet symbol get unioned with the child sheet's nets.
        # Tag with _sheet_uuid so the traversal loop can namespace them per
        # instance (multi-instance hierarchical net isolation).
        sheet_uuid_for_pins = get_value(sheet, "uuid") or ""
        for pin in find_all(sheet, "pin"):
            if len(pin) < 2:
                continue
            pin_name = pin[1] if isinstance(pin[1], list) else label_net_name(pin[1])
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
                     sub_sheet_paths, lib_symbols, text_annotations, bus_elements, title_block,
                     sheet_fields)


def _sheet_order_key(sheet: list) -> tuple:
    """A stable order for the child sheets of one sheet: by uuid, the order KiCad saves
    them in, then position, so a hand-reordered file reads the same as the saved one."""
    at = get_at(sheet) or (0, 0, 0)
    return ((get_value(sheet, "uuid") or "").lower(), at[0], at[1])


def detect_sub_sheet(root_tree: list, file_path: str = None) -> bool:
    """Detect whether a parsed schematic is a sub-sheet (not the root).

    Uses a multi-tier heuristic:
      1. symbol_instances present → ROOT (KiCad 7+ roots always have this)
      2. sheet blocks present AND not referenced by sibling → ROOT
         (intermediate nodes also have sheet blocks; check
         whether a sibling file references us as a child.)
      3. .kicad_pro stem matches file stem, or the project declares the file
         as a top-level sheet → ROOT
         (when multiple .kicad_pro exist, only match if ANY
         stem matches; don't blindly pick the first.)
      4. hierarchical_label presence → SUB-SHEET (original heuristic)
      5. Default: not a sub-sheet (standalone single-sheet design)
    """
    # Tier 1: symbol_instances is definitive for KiCad 7+ roots
    has_symbol_instances = find_first(root_tree, "symbol_instances") is not None
    if has_symbol_instances:
        return False

    # Tier 2: Files with (sheet ...) blocks reference other sheets → root
    # intermediate sub-sheets also have sheet blocks (they have
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
    # when multiple .kicad_pro exist, check ALL of them.
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
                from kicad_core.project import declared_top_level_sheets
                me = os.path.abspath(file_path)
                for stem in pro_stems:
                    pro_path = os.path.join(parent_dir, stem + '.kicad_pro')
                    if any(d["path"] == me for d in declared_top_level_sheets(pro_path)):
                        return False  # a top-level sheet the project declares
                return True   # Project(s) exist but this isn't any of them
        except OSError:
            pass

    # Tier 4: hierarchical_label presence (original heuristic)
    has_hier_labels = any(True for _ in find_all(root_tree, "hierarchical_label"))
    if has_hier_labels:
        return True

    # Tier 5: Ambiguous — default to not a sub-sheet
    return False
