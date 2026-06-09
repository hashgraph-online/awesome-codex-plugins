#!/usr/bin/env python3
"""
KiCad Schematic Analyzer — comprehensive single-pass extraction.

Parses a .kicad_sch file and outputs structured JSON with:
- Component inventory (BOM data, properties, positions)
- Net connectivity (wires, labels, junctions, no-connects, power symbols)
- Pin-level connectivity map (which pin connects to which net)
- Subcircuit identification hints
- Design statistics

Usage:
    python analyze_schematic.py <file.kicad_sch|file.kicad_pro|dir/> [--output file.json]

Output is JSON to stdout (or file if --output specified).
"""

import json
import math
import os
import re
import sys
from pathlib import Path

# Add scripts dir to path for sexp_parser and kicad_utils
sys.path.insert(0, str(Path(__file__).parent))
from sexp_parser import (
    find_all,
    find_deep,
    find_first,
    get_at,
    get_properties,
    get_property,
    get_value,
    has_flag,
    parse_file,
)
from kicad_utils import (
    COORD_EPSILON,
    _MIL_MM,
    _OUTPUT_DRIVE_KEYWORDS,
    classify_component,
    classify_connector,
    classify_ic_function,
    extract_pro_text_variables,
    format_frequency as _format_frequency,
    load_lib_tables,
    is_ground_name as _is_ground_name,
    is_power_net_name as _is_power_net_name,
    load_kicad_pro,
    parse_value,
    parse_voltage_from_net_name as _parse_voltage_from_net_name,
    snap_to_mil_grid as _snap_mil,
)
from kicad_types import AnalysisContext
from signal_detectors import (
    audit_power_pin_dc_paths,
    audit_rail_sources,
    detect_bridge_circuits,
    detect_crystal_circuits,
    detect_current_sense,
    detect_decoupling,
    detect_design_observations,
    detect_integrated_ldos,
    detect_label_aliases,
    detect_lc_filters,
    detect_led_drivers,
    detect_opamp_circuits,
    detect_power_regulators,
    detect_protection_devices,
    detect_rc_filters,
    detect_solder_jumpers,
    detect_transistor_circuits,
    detect_voltage_dividers,
    postfilter_vd_and_dedup,
    _merge_series_dividers,
)
from domain_detectors import (
    audit_connector_ground_distribution,
    audit_esd_protection,
    audit_led_circuits,
    detect_adc_circuits,
    detect_addressable_leds,
    detect_audio_circuits,
    detect_battery_chargers,
    detect_bms_systems,
    detect_buzzer_speakers,
    detect_clock_distribution,
    detect_debug_interfaces,
    detect_display_interfaces,
    detect_ethernet_interfaces,
    detect_hdmi_dvi_interfaces,
    detect_isolation_barriers,
    detect_key_matrices,
    detect_lvds_interfaces,
    detect_led_driver_ics,
    detect_level_shifters,
    detect_memory_interfaces,
    detect_motor_drivers,
    detect_power_path,
    detect_reset_supervisors,
    detect_rf_chains,
    detect_rf_matching,
    detect_rtc_circuits,
    detect_sensor_interfaces,
    detect_thermocouple_rtd,
    suggest_certifications,
    validate_power_sequencing,
    detect_wireless_modules,
    detect_transformer_feedback,
    detect_i2c_address_conflicts,
    detect_energy_harvesting,
    detect_pwm_led_dimming,
    detect_headphone_jack,
)
from validation_detectors import (
    validate_pullups,
    validate_voltage_levels,
    validate_i2c_bus,
    validate_spi_bus,
    validate_can_bus,
    validate_usb_bus,
    validate_power_sequencing as validate_power_seq_deps,
    validate_led_resistors,
    validate_feedback_stability,
)
from finding_schema import compute_trust_summary, sort_findings


# ---------------------------------------------------------------------------
# Case-insensitive distributor / MPN property helpers
# ---------------------------------------------------------------------------
_UUID_RE = re.compile(
    r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
    re.IGNORECASE,
)


def _clean_hierarchical_name(name: str) -> str:
    """Strip UUID path prefixes from hierarchical net/rail names.

    ``/201ab4ae-...-c6b37cf9a2b1/VIN`` → ``VIN``
    """
    if '/' in name and _UUID_RE.search(name):
        return name.rsplit('/', 1)[-1]
    return name


# KiCad lets users name fields however they like — "Digikey", "DigiKey",
# "DIGIKEY", "Digi-Key Part Number" are all common.  Rather than maintaining
# an ever-growing list of explicit variants, build a lowercase property dict
# once and match against normalised known aliases.

_MPN_KEYS = frozenset({
    "mpn", "mfg part", "partnumber", "part number", "part#",
    "manufacturer_part_number", "mfr no.", "mfr_no",
    "manufacturerpartnumber", "partno", "partno.", "mfr_part_number",
})
_MANUFACTURER_KEYS = frozenset({
    "manufacturer", "mfr", "mfg",
})
_DIGIKEY_KEYS = frozenset({
    "digikey", "digi-key", "digi-key part number", "digi-key_pn",
    "digikey part", "digikey part number", "digikey_part_number",
    "digi-key pn", "digikey part number", "dk",
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


def _pick(props: dict, keys: frozenset) -> str:
    """Return the first non-empty value whose lowercased key is in *keys*."""
    for k in keys:
        v = props.get(k)
        if v:
            return v
    return ""




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


def apply_rotation(px: float, py: float, angle_deg: float) -> tuple[float, float]:
    """Apply rotation to a pin offset. KiCad uses degrees, CCW positive."""
    # EQ-065: x'=x·cosθ-y·sinθ, y'=x·sinθ+y·cosθ (2D rotation)
    if angle_deg == 0:
        return px, py
    rad = math.radians(angle_deg)
    cos_a = round(math.cos(rad), 10)
    sin_a = round(math.sin(rad), 10)
    return (px * cos_a - py * sin_a, px * sin_a + py * cos_a)


def compute_pin_positions(component: dict, lib_symbols: dict) -> list[dict]:
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
            # KiCad 6+: decomposed angle + mirror
            if mirror_x:
                py = -py
            if mirror_y:
                px = -px
            rpx, rpy = apply_rotation(px, py, angle)

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
                       symbol_instances: dict | None = None) -> list[dict]:
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
        mpn = _pick(_props, _MPN_KEYS)
        manufacturer = _pick(_props, _MANUFACTURER_KEYS)
        digikey = _pick(_props, _DIGIKEY_KEYS)
        mouser = _pick(_props, _MOUSER_KEYS)
        lcsc = _pick(_props, _LCSC_KEYS)
        element14 = _pick(_props, _ELEMENT14_KEYS)

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
                                          description=description)
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


def _build_net_classifications(results: dict) -> dict[str, dict]:
    """Build net classification dict from existing detector results.

    Tags nets with signal type and characteristics for downstream PCB
    intelligence checks. Uses the 'nets' field from rich-format detections
    plus domain-specific fields where available.
    """
    classifications: dict[str, dict] = {}

    # Crystal circuits → clock nets (from load_cap nets and rich 'nets' field)
    for xc in results.get('crystal_circuits', []):
        freq = xc.get('frequency')
        # Rich format 'nets' field contains the crystal's connected nets
        for net in xc.get('nets', []):
            if net and net not in classifications:
                classifications[net] = {'type': 'clock', 'frequency_hz': freq, 'source': 'crystal_circuits'}
        # Load cap nets are clock-passive
        for lc in xc.get('load_caps', []):
            net = lc.get('net')
            if net and net not in classifications:
                classifications[net] = {'type': 'clock_passive', 'source': 'crystal_circuits'}

    # Power regulators → switching nodes and power rails
    for reg in results.get('power_regulators', []):
        sw_net = reg.get('sw_net')
        if sw_net:
            classifications[sw_net] = {'type': 'switching_node', 'frequency_hz': reg.get('switching_frequency_hz'), 'source': 'power_regulators'}
        output_rail = reg.get('output_rail')
        if output_rail and output_rail not in classifications:
            classifications[output_rail] = {'type': 'power_rail', 'source': 'power_regulators'}

    # Ethernet → differential nets (from rich 'nets' or domain-specific fields)
    for eth in results.get('ethernet_interfaces', []):
        # Try domain-specific differential net fields first
        for key in ('tx_p', 'tx_n', 'rx_p', 'rx_n', 'txp', 'txn', 'rxp', 'rxn'):
            net = eth.get(key)
            if net:
                classifications[net] = {'type': 'ethernet', 'differential': True, 'source': 'ethernet_interfaces'}
        # Fall back to rich 'nets' field
        for net in eth.get('nets', []):
            if net and net not in classifications:
                classifications[net] = {'type': 'ethernet', 'source': 'ethernet_interfaces'}

    # HDMI/DVI
    for hdmi in results.get('hdmi_dvi_interfaces', []):
        for net in hdmi.get('nets', []):
            if net and net not in classifications:
                classifications[net] = {'type': 'hdmi', 'differential': True, 'source': 'hdmi_dvi_interfaces'}

    # Memory interfaces
    for mem in results.get('memory_interfaces', []):
        for net in mem.get('nets', []):
            if net and net not in classifications:
                classifications[net] = {'type': 'memory', 'source': 'memory_interfaces'}

    # LVDS
    for lvds in results.get('lvds_interfaces', []):
        for net in lvds.get('nets', []):
            if net and net not in classifications:
                classifications[net] = {'type': 'lvds', 'differential': True, 'source': 'lvds_interfaces'}

    # RF chains
    for rf in results.get('rf_chains', []):
        for net in rf.get('nets', []):
            if net and net not in classifications:
                classifications[net] = {'type': 'rf', 'source': 'rf_chains'}

    # Clock distribution
    for clk in results.get('clock_distribution', []):
        freq = clk.get('frequency_hz')
        for net in clk.get('nets', []):
            if net and net not in classifications:
                classifications[net] = {'type': 'clock', 'frequency_hz': freq, 'source': 'clock_distribution'}

    # Validation findings → protocol nets (I2C, CAN, USB)
    for vf in results.get('validation_findings', []):
        rule = vf.get('rule_id', '')
        nets = vf.get('nets', [])
        if rule == 'PR-001':
            for net in nets:
                if net not in classifications:
                    classifications[net] = {'type': 'i2c', 'source': 'protocol_detection'}
        elif rule == 'PR-003':
            for net in nets:
                if net not in classifications:
                    classifications[net] = {'type': 'can', 'differential': True, 'source': 'protocol_detection'}
        elif rule == 'PR-004':
            for net in nets:
                if net not in classifications:
                    classifications[net] = {'type': 'usb', 'differential': True, 'source': 'protocol_detection'}

    return classifications


def analyze_signal_paths(ctx: AnalysisContext) -> dict:
    """Analyze signal processing circuits: filters, dividers, feedback networks.

    Orchestrator that calls individual detector functions from signal_detectors.py.
    Each detector takes an AnalysisContext and returns its detection results.
    """
    nets = ctx.nets

    # Run detectors in dependency order
    vd_result = detect_voltage_dividers(ctx)
    voltage_dividers = vd_result["voltage_dividers"]
    # KH-105/KH-115: Merge series resistors in divider chains
    voltage_dividers = _merge_series_dividers(voltage_dividers, ctx)
    feedback_networks = vd_result["feedback_networks"]

    lc_filters = detect_lc_filters(ctx)
    crystal_circuits = detect_crystal_circuits(ctx)
    # KH-145: Detect opamps BEFORE RC filters so feedback components can be excluded
    opamp_circuits = detect_opamp_circuits(ctx)
    # KH-107: Pass crystal_circuits to exclude crystal R/C from RC filter detection
    # KH-145: Pass opamp_circuits to exclude feedback R+C from RC filter detection
    rc_filters = detect_rc_filters(ctx, voltage_dividers, crystal_circuits, opamp_circuits)
    decoupling_analysis = detect_decoupling(ctx)
    current_sense = detect_current_sense(ctx)
    power_regulators = detect_power_regulators(ctx, voltage_dividers)
    integrated_ldos = detect_integrated_ldos(ctx, power_regulators)
    power_regulators.extend(integrated_ldos)

    # Build rail_voltages: net name → voltage from regulator outputs + power symbol names
    rail_voltages: dict[str, float] = {}
    for reg in power_regulators:
        out_rail = reg.get("output_rail")
        v_out = reg.get("estimated_vout")
        if out_rail and v_out is not None:
            rail_voltages[_clean_hierarchical_name(out_rail)] = v_out
    # Augment with voltages inferred from power symbol / net names
    for net_name in ctx.nets:
        clean = _clean_hierarchical_name(net_name)
        if clean not in rail_voltages:
            v = _estimate_rail_voltage(clean)
            if v is not None:
                rail_voltages[clean] = v

    protection_devices = detect_protection_devices(ctx)
    bridge_circuits, matched_fets, fet_pins = detect_bridge_circuits(ctx)
    transistor_circuits = detect_transistor_circuits(ctx, matched_fets, fet_pins)

    # Post-processing that needs cross-detector data
    voltage_dividers, feedback_networks = postfilter_vd_and_dedup(
        voltage_dividers, feedback_networks, transistor_circuits, nets=ctx.nets)
    detect_led_drivers(ctx, transistor_circuits)
    buzzer_speaker_circuits = detect_buzzer_speakers(ctx, transistor_circuits)
    key_matrices = detect_key_matrices(ctx)
    isolation_barriers = detect_isolation_barriers(ctx)
    ethernet_interfaces = detect_ethernet_interfaces(ctx)
    hdmi_dvi_interfaces = detect_hdmi_dvi_interfaces(ctx)
    lvds_interfaces = detect_lvds_interfaces(ctx)
    memory_interfaces = detect_memory_interfaces(ctx)
    rf_chains = detect_rf_chains(ctx)
    rf_matching = detect_rf_matching(ctx)
    bms_systems = detect_bms_systems(ctx)
    battery_chargers = detect_battery_chargers(ctx)
    motor_drivers = detect_motor_drivers(ctx)
    addressable_led_chains = detect_addressable_leds(ctx)
    debug_interfaces = detect_debug_interfaces(ctx)
    power_path = detect_power_path(ctx)
    esd_coverage_audit = audit_esd_protection(ctx, protection_devices)
    adc_circuits = detect_adc_circuits(ctx, rc_filters, protection_devices)
    reset_supervisors = detect_reset_supervisors(ctx)
    clock_distribution = detect_clock_distribution(ctx, crystal_circuits)
    display_interfaces = detect_display_interfaces(ctx)
    sensor_interfaces = detect_sensor_interfaces(ctx)
    level_shifters = detect_level_shifters(ctx)
    audio_circuits = detect_audio_circuits(ctx)
    led_driver_ics = detect_led_driver_ics(ctx)
    rtc_circuits = detect_rtc_circuits(ctx, crystal_circuits)
    led_audit = audit_led_circuits(ctx, transistor_circuits)
    thermocouple_rtd = detect_thermocouple_rtd(ctx)
    power_sequencing_validation = validate_power_sequencing(
        ctx, power_regulators, power_path, reset_supervisors)
    connector_ground_audit = audit_connector_ground_distribution(ctx)

    # Validation detectors (rich findings)
    pullup_findings = validate_pullups(ctx)
    voltage_level_findings = validate_voltage_levels(ctx, level_shifters)
    i2c_findings = validate_i2c_bus(ctx)
    spi_findings = validate_spi_bus(ctx)
    can_findings = validate_can_bus(ctx)
    usb_findings = validate_usb_bus(ctx)
    power_seq_dep_findings = validate_power_seq_deps(ctx, power_regulators)
    led_resistor_findings = validate_led_resistors(ctx)
    feedback_stability_findings = validate_feedback_stability(ctx, power_regulators)

    # New domain detectors (rich format)
    wireless_modules = detect_wireless_modules(ctx)
    transformer_feedback = detect_transformer_feedback(ctx)
    i2c_address_conflicts = detect_i2c_address_conflicts(ctx)
    energy_harvesting = detect_energy_harvesting(ctx)
    pwm_led_dimming = detect_pwm_led_dimming(ctx, transistor_circuits)
    headphone_jacks = detect_headphone_jack(ctx)
    solder_jumpers = detect_solder_jumpers(ctx)
    rail_source_audit = audit_rail_sources(
        ctx, power_regulators=power_regulators, solder_jumpers=solder_jumpers)
    label_aliases = detect_label_aliases(ctx)
    power_pin_dc_paths = audit_power_pin_dc_paths(
        ctx, solder_jumpers=solder_jumpers)

    # Remove R/C components that appear in crystal circuits from RC filter
    # results — prevents misclassifying crystal feedback resistors + load caps
    # as RC filters (e.g., "10M + 22pF = 723Hz RC filter").
    if crystal_circuits and rc_filters:
        xtal_refs = set()
        for xc in crystal_circuits:
            for lc in xc.get("load_caps", []):
                xtal_refs.add(lc["ref"])
            if "feedback_resistor" in xc:
                xtal_refs.add(xc["feedback_resistor"])
        if xtal_refs:
            rc_filters = [
                f for f in rc_filters
                if f.get("resistor", {}).get("reference") not in xtal_refs
                and f.get("capacitor", {}).get("reference") not in xtal_refs
            ]

    def _enrich_capacitor_data(results_dict, context):
        """Add package size, ESR, dielectric, and rated voltage to all cap entries.

        Walks through all detection dicts recursively, finds entries with a 'farads'
        key and a 'ref' key, and adds derived fields from the component's footprint
        and value string.
        """
        from kicad_utils import (extract_cap_package, estimate_cap_esr,
                                 classify_dielectric, parse_rated_voltage)

        def _enrich(obj):
            if isinstance(obj, dict):
                if "farads" in obj and "ref" in obj:
                    ref = obj["ref"]
                    comp = context.comp_lookup.get(ref)
                    if comp:
                        # Package and ESR (existing)
                        if "package" not in obj:
                            fp = comp.get("footprint", "")
                            pkg = extract_cap_package(fp)
                            if pkg:
                                obj["package"] = pkg
                                esr = estimate_cap_esr(obj["farads"], pkg)
                                if esr is not None:
                                    obj["esr_ohm"] = esr
                        # Dielectric classification (new)
                        if "dielectric" not in obj:
                            value_str = comp.get("value", "")
                            desc_str = comp.get("description", "")
                            obj["dielectric"] = classify_dielectric(value_str, desc_str)
                        # Rated voltage (new)
                        if "rated_voltage_V" not in obj:
                            value_str = comp.get("value", "")
                            rv = parse_rated_voltage(value_str)
                            if rv is not None:
                                obj["rated_voltage_V"] = rv
                for v in obj.values():
                    _enrich(v)
            elif isinstance(obj, list):
                for item in obj:
                    _enrich(item)

        _enrich(results_dict)

    def _apply_capacitor_derating(results_dict):
        """Apply DC bias derating to capacitor entries where applied voltage is known.

        Cross-references regulator output voltages with output_capacitors and
        decoupling_analysis to compute effective_farads after DC bias derating.
        Only adds derating fields when both package and applied voltage are known.
        """
        from kicad_utils import estimate_dc_bias_derating

        # Build rail → voltage map from power regulators
        rail_voltage = {}
        for reg in results_dict.get("power_regulators", []):
            vout = reg.get("vout_estimated") or reg.get("estimated_vout")
            rail = reg.get("output_rail", "")
            if vout and vout > 0 and rail:
                # Use the highest voltage seen for a rail (conservative)
                if rail not in rail_voltage or vout > rail_voltage[rail]:
                    rail_voltage[rail] = vout

        def _derate_cap(cap, applied_v):
            """Add derating fields to a single cap entry."""
            farads = cap.get("farads", 0)
            package = cap.get("package")
            dielectric = cap.get("dielectric")
            if not farads or farads <= 0 or not package or not dielectric:
                return

            # Determine rated voltage: from cap entry, or estimate from rail
            rated_v = cap.get("rated_voltage_V")
            if rated_v is None:
                # Conservative estimate based on typical voltage ratings
                if applied_v <= 1.8:
                    rated_v = 6.3
                elif applied_v <= 3.3:
                    rated_v = 6.3
                elif applied_v <= 5.0:
                    rated_v = 10.0
                elif applied_v <= 12.0:
                    rated_v = 25.0
                else:
                    rated_v = applied_v * 2  # assume 2:1 margin

            voltage_ratio = applied_v / rated_v
            remaining = estimate_dc_bias_derating(dielectric, package, voltage_ratio)

            cap["applied_voltage_V"] = applied_v
            cap["derating_factor"] = round(remaining, 3)
            cap["effective_farads"] = farads * remaining

        # Derate output and input capacitors on power regulators
        for reg in results_dict.get("power_regulators", []):
            vout = reg.get("vout_estimated") or reg.get("estimated_vout")
            if not vout or vout <= 0:
                continue
            for cap in reg.get("output_capacitors", []):
                _derate_cap(cap, vout)

        # Derate decoupling analysis capacitors
        for rail_entry in results_dict.get("decoupling_analysis", []):
            rail_name = rail_entry.get("rail", "")
            v = rail_voltage.get(rail_name)
            if not v:
                continue
            any_derated = False
            for cap in rail_entry.get("capacitors", []):
                _derate_cap(cap, v)
                if "effective_farads" in cap:
                    any_derated = True
            # Add total effective capacitance alongside nominal
            if any_derated:
                total_eff = sum(
                    c.get("effective_farads", c["farads"])
                    for c in rail_entry["capacitors"]
                )
                rail_entry["total_effective_capacitance_uF"] = round(total_eff * 1e6, 3)

        # Derate LC filter capacitors where rail voltage is known
        for filt in results_dict.get("lc_filters", []):
            rail = filt.get("rail", "")
            v = rail_voltage.get(rail)
            if v and "capacitor" in filt:
                cap = filt["capacitor"]
                if isinstance(cap, dict) and "farads" in cap:
                    _derate_cap(cap, v)

    results = {
        "rail_voltages": rail_voltages,
        "voltage_dividers": voltage_dividers,
        "rc_filters": rc_filters,
        "lc_filters": lc_filters,
        "feedback_networks": feedback_networks,
        "crystal_circuits": crystal_circuits,
        "snubbers": [],
        "decoupling_analysis": decoupling_analysis,
        "current_sense": current_sense,
        "power_regulators": power_regulators,
        "protection_devices": protection_devices,
        "opamp_circuits": opamp_circuits,
        "bridge_circuits": bridge_circuits,
        "transistor_circuits": transistor_circuits,
        "buzzer_speaker_circuits": buzzer_speaker_circuits,
        "key_matrices": key_matrices,
        "isolation_barriers": isolation_barriers,
        "ethernet_interfaces": ethernet_interfaces,
        "hdmi_dvi_interfaces": hdmi_dvi_interfaces,
        "lvds_interfaces": lvds_interfaces,
        "memory_interfaces": memory_interfaces,
        "rf_chains": rf_chains,
        "rf_matching": rf_matching,
        "bms_systems": bms_systems,
        "battery_chargers": battery_chargers,
        "motor_drivers": motor_drivers,
        "addressable_led_chains": addressable_led_chains,
        "debug_interfaces": debug_interfaces,
        "power_path": power_path,
        "esd_coverage_audit": esd_coverage_audit,
        "adc_circuits": adc_circuits,
        "reset_supervisors": reset_supervisors,
        "clock_distribution": clock_distribution,
        "display_interfaces": display_interfaces,
        "sensor_interfaces": sensor_interfaces,
        "level_shifters": level_shifters,
        "audio_circuits": audio_circuits,
        "led_driver_ics": led_driver_ics,
        "rtc_circuits": rtc_circuits,
        "led_audit": led_audit,
        "thermocouple_rtd": thermocouple_rtd,
        "power_sequencing_validation": power_sequencing_validation,
        "connector_ground_audit": connector_ground_audit,
        "wireless_modules": wireless_modules,
        "transformer_feedback": transformer_feedback,
        "i2c_address_conflicts": i2c_address_conflicts,
        "energy_harvesting": energy_harvesting,
        "pwm_led_dimming": pwm_led_dimming,
        "headphone_jacks": headphone_jacks,
        "solder_jumpers": solder_jumpers,
        "rail_source_audit": rail_source_audit,
        "label_aliases": label_aliases,
        "power_pin_dc_paths": power_pin_dc_paths,
        "validation_findings": (
            pullup_findings +
            voltage_level_findings +
            i2c_findings +
            spi_findings +
            can_findings +
            usb_findings +
            power_seq_dep_findings +
            led_resistor_findings +
            feedback_stability_findings
        ),
    }

    net_classifications = _build_net_classifications(results)
    if net_classifications:
        results["net_classifications"] = net_classifications

    # Certification suggestions cross-reference all domain detections
    cert_suggestions = suggest_certifications(ctx, results)
    if cert_suggestions:
        results["suggested_certifications"] = cert_suggestions

    results["design_observations"] = detect_design_observations(ctx, results)

    # Post-process: enrich capacitor entries with package size and estimated ESR
    _enrich_capacitor_data(results, ctx)
    _apply_capacitor_derating(results)

    return results


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
            if len(xys) >= 2:
                buses.append({
                    "x1": float(xys[0][1]), "y1": float(xys[0][2]),
                    "x2": float(xys[1][1]), "y2": float(xys[1][2]),
                })

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


def build_net_map(components: list[dict], wires: list[dict], labels: list[dict],
                  power_symbols: list[dict], junctions: list[dict],
                  no_connects: list[dict] | None = None) -> dict:
    """Build a connectivity map using union-find on coordinates.

    Groups all electrically connected points into nets, then names them
    from labels and power symbols.
    """
    EPSILON = COORD_EPSILON

    # Collect all electrical points
    # Each point: (sheet, x, y, source_info)
    # The sheet index keeps each sheet's coordinate space separate so that
    # wires on different sheets at the same (x,y) don't falsely merge.
    parent = {}
    point_info = {}  # key -> list of info dicts

    def key(x, y, sheet=0):
        return (sheet, round(x / EPSILON) * EPSILON, round(y / EPSILON) * EPSILON)

    def find(p):
        while parent.get(p, p) != p:
            parent[p] = parent.get(parent[p], parent[p])
            p = parent[p]
        return p

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    def add_point(x, y, info, sheet=0):
        k = key(x, y, sheet)
        if k not in parent:
            parent[k] = k
        point_info.setdefault(k, []).append(info)
        return k

    # Add component pins (skip PWR_FLAG — it's an ERC marker, not a real connection)
    for comp in components:
        if comp.get("value") == "PWR_FLAG" or comp.get("type") == "power_flag":
            continue
        sheet = comp.get("_sheet", 0)
        for pin in comp.get("pins", []):
            add_point(pin["x"], pin["y"], {
                "source": "pin",
                "component": comp["reference"],
                "pin_number": pin["number"],
                "pin_name": pin["name"],
                "pin_type": pin["type"],
            }, sheet)

    # Add wire endpoints and union them.
    # Also build a list of wire segments so we can detect points that land
    # mid-wire (labels, pins, junctions, power symbols placed on a wire
    # between its endpoints).
    wire_segments = []  # list of (k1, k2, x1, y1, x2, y2, sheet)
    # Spatial grid index for fast wire segment lookup — avoids O(W*P) scans.
    # Grid cell size of 5mm captures typical KiCad schematic wire lengths.
    _WIRE_GRID_SIZE = 5.0
    wire_grid: dict[tuple, list[int]] = {}  # (sheet, gx, gy) -> [index into wire_segments]

    for wire in wires:
        sheet = wire.get("_sheet", 0)
        k1 = add_point(wire["x1"], wire["y1"], {"source": "wire"}, sheet)
        k2 = add_point(wire["x2"], wire["y2"], {"source": "wire"}, sheet)
        union(k1, k2)
        idx = len(wire_segments)
        wire_segments.append((k1, k2, wire["x1"], wire["y1"], wire["x2"], wire["y2"], sheet))
        # Index this segment in all grid cells its bounding box overlaps
        min_x, max_x = min(wire["x1"], wire["x2"]), max(wire["x1"], wire["x2"])
        min_y, max_y = min(wire["y1"], wire["y2"]), max(wire["y1"], wire["y2"])
        gx0 = int(min_x // _WIRE_GRID_SIZE)
        gx1 = int(max_x // _WIRE_GRID_SIZE)
        gy0 = int(min_y // _WIRE_GRID_SIZE)
        gy1 = int(max_y // _WIRE_GRID_SIZE)
        for gx in range(gx0, gx1 + 1):
            for gy in range(gy0, gy1 + 1):
                wire_grid.setdefault((sheet, gx, gy), []).append(idx)

    def point_on_segment(px, py, x1, y1, x2, y2):
        """Check if point (px,py) lies on the wire segment (x1,y1)-(x2,y2)."""
        # Quick bounding box check with tolerance
        tol = 0.05
        if px < min(x1, x2) - tol or px > max(x1, x2) + tol:
            return False
        if py < min(y1, y2) - tol or py > max(y1, y2) + tol:
            return False
        # Cross product to check collinearity
        cross = (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)
        seg_len_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
        if seg_len_sq < tol * tol:
            return False
        # Distance from point to line, squared
        if abs(cross) / (seg_len_sq ** 0.5) > tol:
            return False
        return True

    def union_with_overlapping_wires(k, px, py, sheet=0):
        """Union point k with any wire segment it lies on (same sheet only)."""
        gx = int(px // _WIRE_GRID_SIZE)
        gy = int(py // _WIRE_GRID_SIZE)
        candidates = wire_grid.get((sheet, gx, gy), ())
        for idx in candidates:
            wk1, wk2, wx1, wy1, wx2, wy2, ws = wire_segments[idx]
            if point_on_segment(px, py, wx1, wy1, wx2, wy2):
                union(k, wk1)
                return  # one match is enough since wire endpoints are already unioned

    # Add labels — in KiCad, labels can be placed anywhere on a wire,
    # not just at endpoints, so we must check for mid-wire placement.
    label_keys: dict[str, list] = {}  # label_name -> list of coordinate keys
    for lbl in labels:
        sheet = lbl.get("_sheet", 0)
        # KH-078: Defensive coercion — malformed labels can have list names
        lbl_name = lbl["name"]
        if isinstance(lbl_name, list):
            lbl_name = str(lbl_name[0]) if lbl_name else ""
        k = add_point(lbl["x"], lbl["y"], {
            "source": "label",
            "name": lbl_name,
            "label_type": lbl["type"],
        }, sheet)
        # Only global labels and power symbols connect across sheets.
        # Local labels only connect within the same sheet (handled by wire union).
        if lbl["type"] in ("global_label", "hierarchical_label"):
            label_keys.setdefault(lbl_name, []).append(k)
        else:
            # Local labels: union same-name labels within this sheet only
            local_key = (lbl_name, sheet)
            label_keys.setdefault(local_key, []).append(k)
        union_with_overlapping_wires(k, lbl["x"], lbl["y"], sheet)

    # Add power symbols — compute actual pin position from lib symbol.
    # PWR_FLAG is a DRC-only marker (tells ERC a net has a power source).
    # It doesn't create real connectivity, so exclude it entirely.
    for ps in power_symbols:
        if ps["net_name"] == "PWR_FLAG":
            continue
        sheet = ps.get("_sheet", 0)
        k = add_point(ps["x"], ps["y"], {
            "source": "power_symbol",
            "net_name": ps["net_name"],
        }, sheet)
        # Global power symbols connect across all sheets; local power symbols
        # only connect within the same sheet (isolated power domains).
        if ps.get("_power_scope") == "local":
            local_key = (ps["net_name"], sheet)
            label_keys.setdefault(local_key, []).append(k)
        else:
            label_keys.setdefault(ps["net_name"], []).append(k)
        union_with_overlapping_wires(k, ps["x"], ps["y"], sheet)

    # Legacy hidden power-in pins: in KiCad 4/5, ICs could have invisible
    # power-in pins (VCC, GND) that create implicit global net connections
    # by pin name.  These pins have no wires attached — they connect solely
    # by their name matching other hidden power pins or power symbols.
    for comp in components:
        if comp.get("type") == "power_symbol":
            continue
        sheet = comp.get("_sheet", 0)
        for pin in comp.get("pins", []):
            if pin.get("hidden") and pin["type"] == "power_in" and pin["name"]:
                k = key(pin["x"], pin["y"], sheet)
                label_keys.setdefault(pin["name"], []).append(k)

    # Union global/hierarchical labels and power symbols with the same name.
    # This is what connects nets across different parts of the schematic.
    for lbl_name, keys in label_keys.items():
        for j in range(1, len(keys)):
            union(keys[0], keys[j])

    # Add junctions — also check mid-wire placement
    for junc in junctions:
        sheet = junc.get("_sheet", 0)
        k = add_point(junc["x"], junc["y"], {"source": "junction"}, sheet)
        union_with_overlapping_wires(k, junc["x"], junc["y"], sheet)

    # Add no-connect markers to the union-find so NC'd pins are absorbed into
    # the same group and the resulting net gets tagged as intentional NC.
    # Without this, NC'd pins that have no wire create isolated __unnamed_N nets
    # that look like unfinished connections to downstream analysis.
    if no_connects:
        for nc in no_connects:
            sheet = nc.get("_sheet", 0)
            k = add_point(nc["x"], nc["y"], {"source": "no_connect"}, sheet)
            union_with_overlapping_wires(k, nc["x"], nc["y"], sheet)

    # Build net groups
    net_groups: dict[tuple, list[tuple]] = {}
    for k in parent:
        root_k = find(k)
        net_groups.setdefault(root_k, []).append(k)

    # Name the nets
    nets = {}
    net_id = 0
    for root_k, members in net_groups.items():
        # Collect all info for this net
        all_info = []
        for m in members:
            all_info.extend(point_info.get(m, []))

        # Find net name using KiCad's priority:
        # global_label > power_symbol > hierarchical_label > local label > pin
        _NET_NAME_PRIORITY = {
            "global_label": 0,
            "power_symbol": 1,
            "hierarchical_label": 2,
            "label": 3,
            "directive_label": 4,
        }
        best_name = None
        best_priority = 999

        # Accumulate every global / hierarchical / local label attached to
        # this net (LB-001 reads this; also useful for report annotations).
        # Dedup by (name, label_type).
        net_labels_seen: set[tuple[str, str]] = set()
        net_labels: list[dict] = []

        for info in all_info:
            if info["source"] == "power_symbol":
                p = _NET_NAME_PRIORITY["power_symbol"]
                if p < best_priority:
                    best_name = info["net_name"]
                    best_priority = p
            elif info["source"] == "label":
                lbl_name = info.get("name") or ""
                lbl_type = info.get("label_type") or "label"
                p = _NET_NAME_PRIORITY.get(lbl_type, 3)
                if p < best_priority:
                    best_name = lbl_name
                    best_priority = p
                key_tuple = (lbl_name, lbl_type)
                if lbl_name and key_tuple not in net_labels_seen:
                    net_labels_seen.add(key_tuple)
                    net_labels.append({"name": lbl_name, "type": lbl_type})
        net_name = best_name

        # Check if any member of this group is a no-connect marker OR a
        # library-defined NC pin (pin type "no_connect" in the symbol def).
        has_nc_marker = (
            any(i["source"] == "no_connect" for i in all_info)
            or any(i.get("pin_type") in ("no_connect", "unconnected")
                   for i in all_info if i["source"] == "pin")
        )

        if net_name is None:
            # Only create unnamed nets if they have component pins
            has_pins = any(i["source"] == "pin" for i in all_info)
            if not has_pins:
                continue
            net_name = f"__unnamed_{net_id}"
            net_id += 1

        # Collect pin connections
        pin_connections = []
        for info in all_info:
            if info["source"] == "pin":
                pin_connections.append({
                    "component": info["component"],
                    "pin_number": info["pin_number"],
                    "pin_name": info["pin_name"],
                    "pin_type": info["pin_type"],
                })

        # Keep nets that have pin connections, OR named nets (from labels/power symbols)
        # even without pins — this supports legacy files where pin positions aren't available
        if pin_connections or not net_name.startswith("__unnamed_"):
            if net_name in nets:
                # Merge into existing net (can happen when a local label shares a
                # name with a power symbol or global label on a disconnected wire
                # network — e.g., a "GND" label on a connector that isn't wired
                # to the main GND power symbol network).
                nets[net_name]["pins"].extend(pin_connections)
                nets[net_name]["point_count"] += len(members)
                if has_nc_marker:
                    nets[net_name]["no_connect"] = True
                existing_labels = nets[net_name].setdefault("labels", [])
                existing_seen = {(lbl["name"], lbl["type"]) for lbl in existing_labels}
                for nl in net_labels:
                    if (nl["name"], nl["type"]) not in existing_seen:
                        existing_labels.append(nl)
                        existing_seen.add((nl["name"], nl["type"]))
            else:
                nets[net_name] = {
                    "name": net_name,
                    "pins": pin_connections,
                    "point_count": len(members),
                    "no_connect": has_nc_marker,
                    "labels": net_labels,
                }

    return nets


def generate_bom(components: list[dict]) -> list[dict]:
    """Generate grouped BOM from components."""
    groups: dict[tuple, dict] = {}

    # Deduplicate multi-unit symbols — only count each reference once
    seen_refs = set()

    for comp in components:
        if comp["type"] in ("power_symbol", "power_flag", "flag"):
            continue
        if not comp["in_bom"]:
            continue
        if comp["reference"] in seen_refs:
            continue
        seen_refs.add(comp["reference"])

        # Group key: value + footprint + MPN (or just value + footprint if no MPN)
        group_key = (comp["value"], comp["footprint"], comp["mpn"])

        if group_key not in groups:
            groups[group_key] = {
                "value": comp["value"],
                "footprint": comp["footprint"],
                "mpn": comp["mpn"],
                "manufacturer": comp["manufacturer"],
                "digikey": comp["digikey"],
                "mouser": comp["mouser"],
                "lcsc": comp["lcsc"],
                "element14": comp["element14"],
                "datasheet": comp["datasheet"],
                "description": comp["description"],
                "references": [],
                "quantity": 0,
                "dnp": comp["dnp"],
                "type": comp["type"],
            }

        groups[group_key]["references"].append(comp["reference"])
        groups[group_key]["quantity"] += 1

    # Sort by reference
    bom = sorted(groups.values(), key=lambda g: g["references"][0] if g["references"] else "")
    return bom


def compute_statistics(components: list[dict], nets: dict, bom: list[dict],
                       wires: list[dict], no_connects: list[dict]) -> dict:
    """Compute summary statistics."""
    # Deduplicate multi-unit symbols by reference
    seen_refs = set()
    non_power = []
    for c in components:
        if c["type"] in ("power_symbol", "power_flag", "flag"):
            continue
        if c["reference"] in seen_refs:
            continue
        seen_refs.add(c["reference"])
        non_power.append(c)
    bom_items = [b for b in bom if not b["dnp"]]
    dnp_items = [b for b in bom if b["dnp"]]

    type_counts = {}
    for comp in non_power:
        t = comp["type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    # Build power rails with estimated voltages
    power_rail_names = sorted(set(
        comp["value"] for comp in components if comp["type"] == "power_symbol"
    ))
    for net_name in nets:
        if _is_power_net_name(net_name):
            clean = _clean_hierarchical_name(net_name)
            if clean not in power_rail_names:
                power_rail_names.append(clean)
    power_rail_names = sorted(set(power_rail_names))

    power_rails = []
    for name in power_rail_names:
        clean = _clean_hierarchical_name(name)
        v = _parse_voltage_from_net_name(clean)
        power_rails.append({"name": clean, "voltage": v})

    # Missing properties
    missing_mpn = [c["reference"] for c in non_power
                   if c["type"] not in ("test_point", "mounting_hole")
                   and not c["mpn"] and not c["dnp"] and c["in_bom"]]
    missing_footprint = [c["reference"] for c in non_power
                         if not c["footprint"] and c["in_bom"] and not c["dnp"]]

    return {
        "total_components": len(non_power),
        "unique_parts": len(bom_items),
        "dnp_parts": sum(b["quantity"] for b in dnp_items),
        "total_nets": len(nets),
        "total_wires": len(wires),
        "total_no_connects": len(no_connects),
        "component_types": type_counts,
        "power_rails": power_rails,
        "missing_mpn": missing_mpn,
        "missing_footprint": missing_footprint,
    }


def build_pin_to_net_map(nets: dict) -> dict:
    """Build a reverse map: (component, pin_number) -> (net_name, net_info)."""
    pin_net = {}
    for net_name, net_info in nets.items():
        for p in net_info["pins"]:
            pin_net[(p["component"], p["pin_number"])] = (net_name, net_info)
    return pin_net


def get_net_neighbors(net_info: dict, exclude_ref: str) -> list[dict]:
    """Get all components on a net except the given reference, with their details."""
    neighbors = []
    for p in net_info["pins"]:
        if p["component"] != exclude_ref and not p["component"].startswith("#"):
            neighbors.append({
                "component": p["component"],
                "pin_number": p["pin_number"],
                "pin_name": p["pin_name"],
                "pin_type": p["pin_type"],
            })
    return neighbors


# Static lookup tables for IC function classification (used by _classify_ic_function)
_IC_LIB_PREFIX_MAP = {
    "regulator_linear": "linear regulator",
    "regulator_switching": "switching regulator",
    "regulator_controller": "regulator controller",
    "amplifier_operational": "operational amplifier",
    "amplifier_audio": "audio amplifier",
    "amplifier_instrumentation": "instrumentation amplifier",
    "amplifier_difference": "difference amplifier",
    "amplifier_current": "current sense amplifier",
    "amplifier_buffer": "buffer amplifier",
    "amplifier_video": "video amplifier",
    "analog_adc": "ADC",
    "analog_dac": "DAC",
    "analog_switch": "analog switch",
    "comparator": "comparator",
    "converter_dcdc": "DC-DC converter",
    "driver_motor": "motor driver",
    "driver_led": "LED driver",
    "driver_gate": "gate driver",
    "driver_display": "display driver",
    "driver_fet": "FET driver",
    "interface_can_lin": "CAN/LIN transceiver",
    "interface_ethernet": "Ethernet PHY",
    "interface_usb": "USB interface",
    "interface_uart": "UART interface",
    "interface_spi": "SPI interface",
    "interface_i2c": "I2C interface",
    "interface_rs485": "RS-485 transceiver",
    "interface_lvds": "LVDS interface",
    "interface_hdmi": "HDMI interface",
    "interface_optical": "optical interface",
    "logic_74xx": "logic IC (74xx)",
    "logic_4000": "logic IC (4000 series)",
    "logic_level": "level shifter",
    "memory_eeprom": "EEPROM",
    "memory_flash": "flash memory",
    "memory_ram": "RAM",
    "memory_rom": "ROM",
    "mcu": "microcontroller",
    "fpga": "FPGA",
    "cpld": "CPLD",
    "dsp": "DSP",
    "power_management": "power management IC",
    "power_supervisor": "voltage supervisor",
    "power_protection": "power protection IC",
    "rf_amplifier": "RF amplifier",
    "rf_mixer": "RF mixer",
    "rf_switch": "RF switch",
    "rf": "RF IC",
    "sensor_temperature": "temperature sensor",
    "sensor_pressure": "pressure sensor",
    "sensor_humidity": "humidity sensor",
    "sensor_current": "current sensor",
    "sensor_motion": "motion sensor",
    "sensor_magnetic": "magnetic sensor",
    "sensor_optical": "optical sensor",
    "sensor": "sensor IC",
    "timer": "timer IC",
    "reference_voltage": "voltage reference",
}

_IC_VALUE_KEYWORDS = [
    # Microcontrollers
    (("esp32", "esp8266", "esp32s", "esp32c", "esp32h"), "microcontroller (ESP)"),
    (("stm32", "stm8"), "microcontroller (STM)"),
    (("atmega", "attiny", "at90", "atxmega"), "microcontroller (AVR)"),
    (("pic16", "pic18", "pic24", "pic32", "dspic"), "microcontroller (PIC)"),
    (("rp2040", "rp2350"), "microcontroller (RP)"),
    (("nrf51", "nrf52", "nrf53", "nrf91"), "microcontroller (nRF)"),
    (("samd", "same", "samg", "saml", "samr"), "microcontroller (SAM)"),
    (("msp430", "msp432"), "microcontroller (MSP)"),
    (("efm32", "efr32"), "microcontroller (EFx32)"),
    (("cy8c",), "microcontroller (Cypress)"),
    (("gd32",), "microcontroller (GD32)"),
    (("ch32",), "microcontroller (CH32)"),
    (("kb2040",), "microcontroller (RP dev board)"),
    # FPGAs
    (("ice40", "ecp5", "machxo", "nexus"), "FPGA (Lattice)"),
    (("xc7", "xc6", "xczu", "xc2", "xcku", "artix", "spartan", "kintex", "virtex", "zynq"), "FPGA (Xilinx)"),
    (("10cl", "10m0", "5cg", "max10", "cyclone"), "FPGA (Intel)"),
    # Regulators
    (("lm117", "lm317", "lm337", "lm78", "lm79", "ams1117", "ap2112",
          "mic5205", "mic5504", "xc6206", "xc6220", "tps73", "tps76", "rt9013",
          "ld1117", "mcp1700", "mcp1703", "mcp1826", "ht7333", "ht7350"), "linear regulator"),
    (("lm2596", "lm2576", "mc34063", "tps54", "tps56", "tps61", "tps62",
          "tps63", "tps65", "mp1584", "mp2307", "mp2315", "mp2359",
          "ap3012", "sy80", "mt3608"), "switching regulator"),
    # Shift registers / logic
    (("74hc", "74lvc", "74ahc", "74act", "74ac", "sn74"), "logic IC"),
    (("cd4", "hef4", "mc14"), "logic IC (CMOS)"),
    # Communication
    (("max232", "max3232", "sp3232"), "RS-232 transceiver"),
    (("max485", "max3485", "sn65hvd", "thvd1", "isl317"), "RS-485 transceiver"),
    (("mcp2515", "mcp2551", "mcp2562", "sn65hvd23", "tja1"), "CAN transceiver"),
    (("cp2102", "ch340", "ft232", "ft2232", "pl2303", "ch9102"), "USB-UART bridge"),
    (("usb3300", "usb3320", "usb2514", "tusb"), "USB IC"),
    (("lan87", "lan91", "lan8720", "lan8710", "ksz", "dp83", "rtl81", "ip101"), "Ethernet PHY"),
    (("w5500", "w5100", "enc28j60"), "Ethernet controller"),
    (("sx127", "sx126", "rfm9", "rfm6", "cc1101", "at86rf"), "radio transceiver"),
    # Audio
    (("max9", "ssm2", "tpa", "lm386", "tda", "pam8"), "audio amplifier"),
    (("wm8", "es8", "ak4", "pcm51", "pcm17", "cs42", "sgtl5", "tlv320"), "audio codec"),
    # Display / LED
    (("ssd1306", "ssd1309", "st7735", "st7789", "ili9", "hx8357",
          "uc1701", "nt35", "sharp_ls"), "display controller"),
    (("ws2812", "sk6812", "apa102", "ws2813", "ws2815"), "addressable LED"),
    (("pca9685", "tlc5940", "is31fl"), "LED driver IC"),
    # Sensors
    (("bme280", "bme680", "bmp280", "bmp390"), "environmental sensor"),
    (("mpu6", "mpu9", "icm20", "lsm6", "bno0", "lis3"), "IMU/motion sensor"),
    (("ina21", "ina22", "ina23", "ina18", "ina19"), "current sense amplifier"),
    (("ads1", "mcp33", "mcp34", "mcp35", "max114", "max119"), "ADC"),
    (("mcp47", "dac8", "ad56", "ad57"), "DAC"),
    # Power management
    (("bq24", "bq25", "bq40", "ltc40", "mcp738"), "battery management"),
    (("tps20", "tps21", "ap22"), "power switch/load switch"),
    # Miscellaneous
    (("drv8", "a4988", "tmc2", "tmc5"), "motor driver"),
    (("esd", "prtr", "usblc", "tpd", "pesd", "sp05"), "ESD protection"),
    (("ds1307", "ds3231", "pcf8523", "rv3028", "rv8803"), "RTC"),
    (("at24c", "24lc", "24aa", "m24c", "cat24"), "EEPROM"),
    (("w25q", "at25", "mx25", "gd25", "is25", "sst26"), "SPI flash"),
]

_IC_DESC_KEYWORDS = [
    ("microcontroller", "microcontroller"),
    ("mcu", "microcontroller"),
    ("fpga", "FPGA"),
    ("cpld", "CPLD"),
    ("voltage regulator", "voltage regulator"),
    ("ldo", "linear regulator"),
    ("buck converter", "switching regulator"),
    ("boost converter", "switching regulator"),
    ("dc-dc", "DC-DC converter"),
    ("operational amplifier", "operational amplifier"),
    ("op-amp", "operational amplifier"),
    ("opamp", "operational amplifier"),
    ("comparator", "comparator"),
    ("adc", "ADC"),
    ("dac", "DAC"),
    ("uart", "UART interface"),
    ("usart", "UART interface"),
    ("spi", "SPI interface"),
    ("i2c", "I2C interface"),
    ("can transceiver", "CAN transceiver"),
    ("rs-485", "RS-485 transceiver"),
    ("rs-232", "RS-232 transceiver"),
    ("ethernet", "Ethernet IC"),
    ("usb", "USB IC"),
    ("motor driver", "motor driver"),
    ("gate driver", "gate driver"),
    ("led driver", "LED driver"),
    ("audio", "audio IC"),
    ("codec", "audio codec"),
    ("sensor", "sensor IC"),
    ("eeprom", "EEPROM"),
    ("flash", "flash memory"),
    ("shift register", "shift register"),
    ("multiplexer", "multiplexer"),
    ("level shift", "level shifter"),
    ("voltage reference", "voltage reference"),
    ("timer", "timer IC"),
    ("rtc", "RTC"),
    ("real-time clock", "RTC"),
    ("power supervisor", "voltage supervisor"),
    ("watchdog", "watchdog timer"),
    ("battery", "battery management"),
    ("charger", "battery charger"),
    ("rf", "RF IC"),
]


def _classify_ic_function(lib_id: str, value: str, description: str) -> str:
    """Classify IC function from library ID, value, and description.

    Three-tier lookup:
    1. KiCad stdlib library prefix (most reliable)
    2. Value/part number keyword matching
    3. Description keyword fallback
    """
    lib_lower = lib_id.lower()
    val_lower = value.lower()
    desc_lower = description.lower()

    # Skip connectors — they're analyzed for pinout but not for IC function
    lib_prefix = lib_lower.split(":")[0] if ":" in lib_lower else ""
    if lib_prefix.startswith("connector"):
        return ""

    # Tier 1: KiCad standard library prefix mapping
    for prefix, func in _IC_LIB_PREFIX_MAP.items():
        if lib_prefix == prefix or lib_lower.startswith(prefix + ":"):
            return func

    # Tier 2: Value / part number keyword matching
    for keywords, func in _IC_VALUE_KEYWORDS:
        if any(val_lower.startswith(k) for k in keywords):
            return func

    # Also check lib_id part name (after colon)
    lib_part = lib_lower.split(":")[-1] if ":" in lib_lower else ""
    if lib_part:
        for keywords, func in _IC_VALUE_KEYWORDS:
            if any(lib_part.startswith(k) for k in keywords):
                return func

    # Tier 3: Description keyword fallback
    for keyword, func in _IC_DESC_KEYWORDS:
        if keyword in desc_lower:
            return func

    return ""


def analyze_ic_pinouts(ctx: AnalysisContext) -> list[dict]:
    """Analyze each IC's pinout for datasheet cross-referencing.

    For every IC, produces a detailed per-pin analysis showing:
    - What net each pin connects to
    - What other components are on that net (with their values)
    - Whether power pins have decoupling capacitors
    - Whether input pins have pull-up/pull-down resistors
    - Pins that are unconnected (and whether they should be)
    """
    EPSILON = COORD_EPSILON
    components = ctx.components
    nets = ctx.nets
    pin_net = ctx.pin_net
    no_connects = ctx.no_connects
    comp_lookup = ctx.comp_lookup

    # Build no-connect position set
    nc_positions = set()
    for nc in no_connects:
        nc_positions.add((nc.get("_sheet", 0),
                          round(nc["x"] / EPSILON) * EPSILON,
                          round(nc["y"] / EPSILON) * EPSILON))

    results = []

    # Analyze ICs and other complex components (connectors, crystals, oscillators, etc.)
    target_types = {"ic", "connector", "crystal", "oscillator"}
    target_components = [c for c in components if c["type"] in target_types]

    for ic in target_components:
        ref = ic["reference"]
        pin_analysis = []
        decap_summary = {}  # net_name -> list of capacitor refs
        unconnected = []
        power_pins_detail = []
        signal_pins_detail = []

        for pin in ic.get("pins", []):
            # Ensure pin number and name are never null in output
            pin_number = pin.get("number") or ""
            pin_name = pin.get("name") or ""
            if not pin_number:
                # Fallback: use pin UUID if available, otherwise "unknown"
                pin_number = ic.get("pin_uuids", {}).get("", "unknown") if not pin_number else pin_number
                if not pin_number or pin_number == "unknown":
                    pin_number = f"unknown_{pin.get('x', 0):.0f}_{pin.get('y', 0):.0f}"

            pin_key = (ref, pin_number)
            net_name, net_info = pin_net.get(pin_key, (None, None))

            # Check if pin has a no-connect marker (by position, net flag, or
            # library-defined NC pin type)
            pin_pos = (ic.get("_sheet", 0),
                       round(pin["x"] / EPSILON) * EPSILON,
                       round(pin["y"] / EPSILON) * EPSILON)
            has_no_connect = (
                pin_pos in nc_positions
                or bool(net_info and net_info.get("no_connect"))
                or pin.get("type") in ("no_connect", "unconnected")
            )

            # Get components sharing this net
            neighbors = []
            neighbor_summary = []
            if net_info:
                neighbors = get_net_neighbors(net_info, ref)
                for nb in neighbors:
                    nb_comp = comp_lookup.get(nb["component"])
                    if nb_comp:
                        neighbor_summary.append({
                            "ref": nb["component"],
                            "value": nb_comp.get("value", ""),
                            "type": nb_comp.get("type", ""),
                            "pin": nb["pin_number"],
                            "pin_name": nb["pin_name"],
                        })

            # Classify what's connected
            connected_caps = [n for n in neighbor_summary if n["type"] == "capacitor"]
            connected_resistors = [n for n in neighbor_summary if n["type"] == "resistor"]
            connected_inductors = [n for n in neighbor_summary if n["type"] == "inductor"]

            pin_entry = {
                "pin_number": pin_number,
                "pin_name": pin_name,
                "pin_type": pin["type"],
                "net": "NO_CONNECT" if has_no_connect else (net_name or "UNCONNECTED"),
                "connected_to": neighbor_summary,
            }

            # Determine if this is functionally a power pin based on type OR net name.
            # Many lib symbols mark power pins as "input" or "passive", so also check
            # if the net is a known power rail.
            is_power_pin = pin["type"] in ("power_in", "power_out")
            if not is_power_pin and net_name:
                # Check net name against common power rail patterns
                net_upper = net_name.upper()
                is_power_pin = (
                    net_upper in ("GND", "VSS", "AGND", "DGND", "PGND",
                                  "VCC", "VDD", "AVCC", "AVDD", "DVCC", "DVDD",
                                  "VBUS", "V_USB")
                    or net_upper.startswith("+")
                    or net_upper.startswith("V+")
                )
            # Also check pin name for power pin hints
            if not is_power_pin and pin["name"]:
                pname = pin["name"].upper()
                is_power_pin = pname in (
                    "VCC", "VDD", "VSS", "GND", "AVCC", "AVDD", "DVCC", "DVDD",
                    "VIN", "VOUT", "PGND", "AGND", "DGND", "VBUS",
                )

            if is_power_pin:
                # For decoupling cap detection, only list caps directly on THIS net
                # (not the entire GND net which connects everything)
                net_is_ground = net_name and net_name.upper() in (
                    "GND", "VSS", "AGND", "DGND", "PGND")
                if net_is_ground:
                    # Don't list decoupling caps for ground pins — they're shared globally
                    pin_entry["has_decoupling_cap"] = True  # ground is always decoupled
                    pin_entry["decoupling_caps"] = []
                    pin_entry["note"] = "Ground net — decoupling caps listed on VCC/VDD pins"
                else:
                    pin_entry["has_decoupling_cap"] = len(connected_caps) > 0
                    pin_entry["decoupling_caps"] = [
                        {"ref": c["ref"], "value": c["value"]} for c in connected_caps
                    ]
                    if net_name and connected_caps:
                        decap_summary.setdefault(net_name, []).extend(
                            {"ref": c["ref"], "value": c["value"]} for c in connected_caps
                        )
                power_pins_detail.append(pin_entry)

            elif pin["type"] in ("input", "bidirectional", "open_collector", "open_emitter"):
                # Check for pull-up/pull-down resistors
                pull_resistors = []
                for r in connected_resistors:
                    r_comp = comp_lookup.get(r["ref"])
                    if r_comp:
                        # Check where the other end of the resistor goes
                        other_pin = "1" if r["pin"] == "2" else "2"
                        other_key = (r["ref"], other_pin)
                        other_net, _ = pin_net.get(other_key, (None, None))
                        if other_net in ("GND", "VSS"):
                            pull_resistors.append({
                                "ref": r["ref"], "value": r_comp["value"],
                                "direction": "pull-down", "to_net": other_net,
                            })
                        elif other_net and any(kw in other_net.upper()
                                               for kw in ("VCC", "VDD", "+3", "+5", "VBUS")):
                            pull_resistors.append({
                                "ref": r["ref"], "value": r_comp["value"],
                                "direction": "pull-up", "to_net": other_net,
                            })
                        else:
                            pull_resistors.append({
                                "ref": r["ref"], "value": r_comp["value"],
                                "direction": "series", "to_net": other_net,
                            })
                if pull_resistors:
                    pin_entry["resistors"] = pull_resistors
                signal_pins_detail.append(pin_entry)

            else:
                signal_pins_detail.append(pin_entry)

            if not net_name and not has_no_connect:
                unconnected.append(pin_entry)

            pin_analysis.append(pin_entry)

        # Deduplicate decoupling caps per net
        unique_decaps = {}
        for net_name, caps in decap_summary.items():
            seen = set()
            unique = []
            for c in caps:
                if c["ref"] not in seen:
                    seen.add(c["ref"])
                    unique.append(c)
            unique_decaps[net_name] = unique

        # Build IC analysis summary
        ic_result = {
            "reference": ref,
            "value": ic["value"],
            "type": ic["type"],
            "lib_id": ic["lib_id"],
            "mpn": ic.get("mpn", ""),
            "description": ic.get("description", ""),
            "datasheet": ic.get("datasheet", ""),
            "function": _classify_ic_function(ic["lib_id"], ic["value"], ic.get("description", "")),
            "total_pins": len(pin_analysis),
            "unconnected_pins": len(unconnected),
            "pins": sorted(pin_analysis, key=lambda p: _pin_sort_key(p["pin_number"])),
            "power_pins": power_pins_detail,
            "signal_pins": signal_pins_detail,
            "decoupling_caps_by_rail": unique_decaps,
        }

        if unconnected:
            ic_result["unconnected_pin_list"] = unconnected

        results.append(ic_result)

    return results


def _pin_sort_key(pin_num: str):
    """Sort pin numbers numerically when possible, alphabetically otherwise."""
    try:
        return (0, int(pin_num))
    except ValueError:
        return (1, pin_num)


def identify_subcircuits(ctx: AnalysisContext) -> list[dict]:
    """Identify potential subcircuit groupings around ICs."""
    components = ctx.components
    nets = ctx.nets
    pin_net = ctx.pin_net
    comp_lookup = ctx.comp_lookup
    is_power_net = ctx.is_power_net
    is_ground = ctx.is_ground
    subcircuits = []

    ics = [c for c in components if c["type"] == "ic"]

    for ic in ics:
        ref = ic["reference"]

        # Find all nets this IC connects to
        ic_nets = set()
        for pin in ic.get("pins", []):
            net_name, _ = pin_net.get((ref, pin["number"]), (None, None))
            if net_name:
                ic_nets.add(net_name)

        # Find all components that share nets with this IC (1-hop neighbors)
        # Skip power/ground nets — every IC shares VCC/GND, inflating neighbors
        neighbors = set()
        for net_name in ic_nets:
            if is_power_net(net_name) or is_ground(net_name):
                continue
            if net_name in nets:
                for p in nets[net_name]["pins"]:
                    r = p["component"]
                    if r != ref and not r.startswith("#"):
                        neighbors.add(r)

        # Build neighbor details with values
        neighbor_details = []
        for nb_ref in sorted(neighbors):
            nb_comp = comp_lookup.get(nb_ref)
            if nb_comp:
                neighbor_details.append({
                    "ref": nb_ref,
                    "value": nb_comp.get("value", ""),
                    "type": nb_comp.get("type", ""),
                })

        subcircuits.append({
            "center_ic": ref,
            "ic_value": ic["value"],
            "ic_mpn": ic.get("mpn", ""),
            "ic_lib_id": ic["lib_id"],
            "neighbor_components": neighbor_details,
            "description": ic.get("description", ""),
        })

    return subcircuits


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
                                fl = fname.lower()
                                if fl in _MPN_KEYS:
                                    comp["mpn"] = field_val
                                elif fl in _MANUFACTURER_KEYS:
                                    comp["manufacturer"] = field_val
                                elif fl in _DIGIKEY_KEYS:
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


def parse_legacy_schematic(path: str) -> dict:
    """Parse a KiCad 5 legacy .sch file and return the same structure as analyze_schematic.

    Legacy format uses line-oriented text with $Comp/$EndComp blocks, coordinates
    in mils (1/1000 inch), and positional field numbering (F0=ref, F1=value, etc.).

    For hierarchical designs, recursively parses all subsheets referenced by
    $Sheet blocks and merges connectivity across sheets.

    Parses .lib files to populate component pin data for pin-to-net mapping
    and signal analysis.
    """
    all_components = []
    all_wires = []
    all_labels = []
    all_junctions = []
    all_no_connects = []
    sheets_parsed = []
    all_sch_lines = {}  # path -> LIBS: lines for lib resolution

    to_parse = [str(Path(path).resolve())]
    parsed = set()

    while to_parse:
        sheet_path = to_parse.pop(0)
        if sheet_path in parsed:
            continue
        parsed.add(sheet_path)

        components, wires, labels, junctions, no_connects, sub_sheets, lib_lines = \
            _parse_legacy_single_sheet(sheet_path)

        all_sch_lines[sheet_path] = lib_lines

        # Tag elements with sheet index to keep coordinate spaces separate
        sheet_idx = len(sheets_parsed)
        for c in components:
            c["_sheet"] = sheet_idx
        for w in wires:
            w["_sheet"] = sheet_idx
        for lbl in labels:
            lbl["_sheet"] = sheet_idx
        for j in junctions:
            j["_sheet"] = sheet_idx
        for nc in no_connects:
            nc["_sheet"] = sheet_idx

        all_components.extend(components)
        all_wires.extend(wires)
        all_labels.extend(labels)
        all_junctions.extend(junctions)
        all_no_connects.extend(no_connects)
        sheets_parsed.append(sheet_path)

        for sub_path in sub_sheets:
            if sub_path not in parsed:
                to_parse.append(sub_path)

    # Resolve .lib files and parse pin data
    root_path = str(Path(path).resolve())
    lib_symbols, legacy_resolution = _resolve_legacy_libs(root_path, all_sch_lines)

    # Build a reverse lookup for cache lib names: bare_symbol -> full cache name.
    # Cache libs store "Library_Symbol" while schematics reference bare "Symbol"
    # or "Library:Symbol".  This handles both forms.
    _cache_suffix_map: dict[str, str] = {}
    for sym_name in lib_symbols:
        if "_" in sym_name:
            bare = sym_name.rsplit("_", 1)[-1]
            # Only map if the bare name is unique (avoid ambiguity)
            if bare not in _cache_suffix_map:
                _cache_suffix_map[bare] = sym_name
            else:
                _cache_suffix_map[bare] = None  # ambiguous — don't use
        # Also try full name after last colon-like underscore
        # e.g., "OLIMEX_IC_BL4054B-42TPRN(SOT23-5)" → "BL4054B-42TPRN(SOT23-5)"
        parts = sym_name.split("_")
        if len(parts) >= 3:
            tail = "_".join(parts[2:])
            if tail and tail not in _cache_suffix_map:
                _cache_suffix_map[tail] = sym_name

    # Populate pin positions for each component using lib symbol data.
    # V2 format uses bare symbol names ("MIC5207-BM5"), V4 uses "Library:Symbol".
    # Cache libs use underscores ("Device_C") instead of colons ("Device:C").
    for comp in all_components:
        lib_id = comp.get("lib_id", "")
        sym_def = lib_symbols.get(lib_id)
        _pin_src = "parsed_lib"
        if not sym_def and ":" in lib_id:
            # V4: try underscore form (cache lib naming) and bare symbol name
            bare_name = lib_id.split(":", 1)[1]
            sym_def = (lib_symbols.get(lib_id.replace(":", "_"))
                       or lib_symbols.get(bare_name))
        else:
            bare_name = lib_id
        if not sym_def:
            # Bare name lookup via cache suffix map (handles cache libs
            # that store "Library_Symbol" while schematic uses bare "Symbol")
            cache_key = _cache_suffix_map.get(bare_name)
            if cache_key:
                sym_def = lib_symbols.get(cache_key)
                _pin_src = "suffix_match"
        if sym_def:
            comp["pins"] = compute_pin_positions(comp, {lib_id: sym_def})
            comp["_pin_source"] = _pin_src
            # KH-216: Store unit-valid pin numbers for pin_nets filtering
            comp["_unit_pins"] = {p["number"] for p in comp["pins"]}
            # Snap pin positions to mil grid — eliminates floating-point drift
            # from trig-based rotation so pins align with wire endpoints.
            for pin in comp["pins"]:
                pin["x"] = _snap_mil(pin["x"])
                pin["y"] = _snap_mil(pin["y"])

    # KH-016 fix: Snap component pins to nearby wire endpoints when the
    # computed pin positions don't match any wire (caused by KiCad version
    # differences in standard library pin offsets).  For each pin, if no wire
    # endpoint is within COORD_EPSILON, find the closest wire endpoint on the
    # same sheet within a generous radius and snap to it.
    _snap_pins_to_wires(all_components, all_wires)

    # Extract power symbols (preserve _sheet so build_net_map keeps coordinate
    # spaces separate — without it, power symbols from sub-sheets all land in
    # sheet 0's coordinate space and fail to connect to their actual wires).
    power_symbols = []
    for comp in all_components:
        if comp["type"] == "power_symbol":
            ps = {
                "net_name": comp["value"],
                "x": comp["x"],
                "y": comp["y"],
                "lib_id": comp["lib_id"],
            }
            if "_sheet" in comp:
                ps["_sheet"] = comp["_sheet"]
            ps["_power_scope"] = comp.get("_power_scope", "global")
            power_symbols.append(ps)

    # Generate BOM
    bom = generate_bom(all_components)

    # Build nets from wires + labels + power symbols + component pins
    nets = build_net_map(all_components, all_wires, all_labels, power_symbols, all_junctions,
                         all_no_connects)

    stats = compute_statistics(all_components, nets, bom, all_wires, all_no_connects)

    # Subcircuit detection (IC + 1-hop neighbors)
    pin_net = build_pin_to_net_map(nets)

    # Build shared analysis context for legacy path
    ctx = AnalysisContext(
        components=all_components,
        nets=nets,
        lib_symbols=lib_symbols,
        pin_net=pin_net,
        no_connects=all_no_connects,
    )
    from netlist_queries import NetlistQueries
    ctx.nq = NetlistQueries(ctx)

    subcircuits = identify_subcircuits(ctx)

    # Signal path and filter analysis
    signal_analysis = analyze_signal_paths(ctx)

    # Design rule analysis
    design_analysis = analyze_design_rules(ctx, results_in=signal_analysis)

    # Filter to real components (non-power) for annotation check
    real_components = [
        c for c in all_components
        if c["type"] not in ("power_symbol", "power_flag", "flag")
    ]
    annotation_issues = check_annotation_completeness(real_components)

    # Enrich components with pin-to-net mapping (legacy path)
    # KH-211: Include __unnamed_* nets so that connections through unlabelled
    # wires (common in hierarchical sub-sheets) appear in pin_nets.
    _pin_nets_l: dict[str, dict[str, str]] = {}
    for _net_name, _net_info in nets.items():
        if isinstance(_net_info, dict):
            for _p in _net_info.get('pins', []):
                _comp_ref = _p.get('component', '')
                _pin_num = _p.get('pin_number', '')
                if _comp_ref and _pin_num:
                    _pin_nets_l.setdefault(_comp_ref, {})[_pin_num] = _net_name
    for _comp in all_components:
        _all_pn = _pin_nets_l.get(_comp.get('reference', ''), {})
        _valid = _comp.get("_unit_pins")
        if _valid and len(_all_pn) > len(_valid):
            _comp['pin_nets'] = {k: v for k, v in _all_pn.items() if k in _valid}
        else:
            _comp['pin_nets'] = _all_pn
        _comp.pop("_unit_pins", None)

    # Add stable detection IDs for diff matching (legacy path)
    from detection_schema import compute_detection_id as _compute_det_id
    for _det_type, _dets in signal_analysis.items():
        if isinstance(_dets, list):
            for _det in _dets:
                if isinstance(_det, dict):
                    _det["detection_id"] = _compute_det_id(_det, _det_type)

    # Flatten signal_analysis: all list values become findings, dict values move to top level
    findings = []
    top_level_dicts = {}
    for key, value in signal_analysis.items():
        if isinstance(value, list):
            _det_name = f"detect_{key}"
            for _item in value:
                if isinstance(_item, dict) and "detector" not in _item:
                    _item["detector"] = _det_name
            findings.extend(value)
        elif isinstance(value, dict):
            # rail_voltages, net_classifications, etc. — promote to top level
            top_level_dicts[key] = value

    sev_counts = {"error": 0, "warning": 0, "info": 0}
    for f in findings:
        sev = f.get("severity", "info").lower() if isinstance(f, dict) else "info"
        if sev in ("critical", "high"):
            sev_counts["error"] += 1
        elif sev in ("medium", "warning"):
            sev_counts["warning"] += 1
        else:
            sev_counts["info"] += 1

    # Legacy analysis quality summary (KH-271)
    _pin_source_counts = {"parsed_lib": 0, "suffix_match": 0, "snapped_to_wire": 0, "unresolved": 0}
    for c in real_components:
        src = c.get("_pin_source", "unresolved")
        if src in _pin_source_counts:
            _pin_source_counts[src] += 1
        else:
            _pin_source_counts[src] = 1

    # Deterministic order for byte-identical repeated runs (KH-316).
    sort_findings(findings)

    result = {
        "analyzer_type": "schematic",
        "schema_version": "1.3.0",
        "summary": {"total_findings": len(findings), "by_severity": sev_counts},
        "trust_summary": compute_trust_summary(findings),
        "file": str(path),
        "kicad_version": "5 (legacy)",
        "file_version": "4",
        "sheets_parsed": len(sheets_parsed),
        "sheet_files": sheets_parsed,
        "statistics": stats,
        "bom": bom,
        "components": real_components,
        "nets": nets,
        "subcircuits": subcircuits,
        "findings": findings,
        "design_analysis": design_analysis,
        "labels": all_labels,
        "no_connects": all_no_connects,
        "power_symbols": power_symbols,
        "annotation_issues": annotation_issues,
        "legacy_analysis_quality": {
            "is_legacy_schematic": True,
            "library_resolution": legacy_resolution,
            "pin_source_coverage": _pin_source_counts,
        },
    }
    # Promote dict values from signal_analysis to top level (rail_voltages, etc.)
    result.update(top_level_dicts)
    return result


def parse_single_sheet(path: str, instance_uuid: str = "",
                       symbol_instances: dict | None = None) -> tuple:
    """Parse a single .kicad_sch file and return raw extracted data.

    If instance_uuid is provided, remap component references from the
    (instances) block for this specific sheet instance.

    If symbol_instances is provided, use it as fallback for remapping when
    inline (instances) blocks are absent.

    Returns: (root, components, wires, labels, junctions, no_connects,
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

    return (root, components, wires, labels, junctions, no_connects,
            sub_sheet_paths, lib_symbols, text_annotations, bus_elements, title_block)


def analyze_connectivity(components: list[dict], nets: dict, no_connects: list[dict]) -> dict:
    """Analyze the connectivity graph for potential issues.

    Returns a dict with:
    - unconnected_pins: pins not on any net (and not marked no-connect)
    - single_pin_nets: nets with only one pin (likely unfinished connections)
    - multi_driver_nets: nets with multiple output/bidirectional drivers
    - power_net_summary: per power rail, which components connect
    """
    EPSILON = COORD_EPSILON

    # Build set of no-connect positions for quick lookup
    nc_positions = set()
    for nc in no_connects:
        nc_positions.add((nc.get("_sheet", 0),
                          round(nc["x"] / EPSILON) * EPSILON,
                          round(nc["y"] / EPSILON) * EPSILON))

    # Build set of all pins that appear in any net
    connected_pins = set()
    for net_info in nets.values():
        for p in net_info["pins"]:
            connected_pins.add((p["component"], p["pin_number"]))

    # Find unconnected pins
    unconnected_pins = []
    for comp in components:
        if comp["type"] in ("power_symbol", "power_flag", "flag"):
            continue
        for pin in comp.get("pins", []):
            pin_key = (comp["reference"], pin["number"])
            if pin_key not in connected_pins:
                # Check if there's a no-connect marker at this pin
                pin_pos = (comp.get("_sheet", 0),
                           round(pin["x"] / EPSILON) * EPSILON,
                           round(pin["y"] / EPSILON) * EPSILON)
                if pin_pos not in nc_positions:
                    unconnected_pins.append({
                        "component": comp["reference"],
                        "pin_number": pin["number"],
                        "pin_name": pin["name"],
                        "pin_type": pin["type"],
                    })

    # Find single-pin nets. Pin type determines severity — a floating
    # power_in / input / bidirectional pin is a real wiring bug, while a
    # lonely passive leg is usually mid-edit, and a no_connect pin is
    # documentation. Unnamed nets (__unnamed_N) count when the pin type
    # warrants it — KiCad lets users rely on the auto-generated name
    # for boot caps and flying caps that genuinely shouldn't be labelled.
    _SIGNAL_PIN_TYPES = {"power_in", "input", "bidirectional",
                         "output", "tri_state", "open_collector",
                         "open_emitter"}
    _SKIP_PIN_TYPES = {"no_connect", "free", "unspecified", "unconnected"}
    single_pin_nets = []
    single_pin_net_findings: list[dict] = []
    for net_name, net_info in nets.items():
        if len(net_info["pins"]) != 1 or net_info.get("no_connect"):
            continue
        pin = net_info["pins"][0]
        pin_type = (pin.get("pin_type") or "").lower()
        if pin_type in _SKIP_PIN_TYPES:
            continue
        # Retain the legacy summary shape for downstream consumers —
        # keep the pre-existing __unnamed_* guard on the legacy list so
        # format-report / diff_analysis don't surface mid-edit passive
        # stubs that the old code filtered out. The rich NT-001 finding
        # below still covers those cases for reviewers who want them.
        if not net_name.startswith("__unnamed_"):
            single_pin_nets.append({"net": net_name, "pin": pin})
        # Emit a weighted finding.
        if pin_type in _SIGNAL_PIN_TYPES:
            severity = "warning"
            impact = ("Likely unfinished wiring: a driven or powered pin "
                      "has no counterpart.")
        elif pin_type == "power_out":
            severity = "info"
            impact = ("Power source with no declared load — acceptable if "
                      "loads are on another sheet, otherwise suspicious.")
        else:
            severity = "info"
            impact = "Passive or unclassified pin lonely on its own net."
        display_ref = pin.get("component", "?")
        display_num = pin.get("pin_number", "?")
        display_name = pin.get("pin_name") or ""
        display_label = (f"{display_ref}.{display_num}"
                         + (f" ({display_name})" if display_name else ""))
        net_display = (f"{display_ref}.{display_name}"
                       if net_name.startswith("__unnamed_") and display_name
                       else net_name)
        single_pin_net_findings.append({
            "detector": "analyze_connectivity",
            "rule_id": "NT-001",
            "severity": severity,
            "confidence": "deterministic",
            "evidence_source": "topology",
            "category": "connectivity",
            "summary": (f"Single-pin net: {net_display} only connects to "
                        f"{display_label} ({pin_type or 'unknown'})"),
            "description": (f"Net {net_name!r} has exactly one pin: "
                            f"{display_label}, pin_type={pin_type!r}. "
                            "Verify the intended target — if this pin "
                            "should connect somewhere, the wire/label is "
                            "missing."),
            "components": [display_ref] if display_ref else [],
            "nets": [net_name],
            "pins": [f"{display_ref}.{display_num}"],
            "net_display_name": net_display,
            "pin_type": pin_type,
            "pin_name": display_name,
            "recommendation": (
                "Check the schematic at the referenced pin — add the "
                "missing wire or place a no-connect marker if the pin is "
                "intentionally floating."),
            "report_context": {
                "section": "Connectivity",
                "impact": impact,
                "standard_ref": "",
            },
        })

    # Find multi-driver nets (multiple outputs driving the same net)
    # Exclude power flags (#FLG, #PWR) — they're virtual, not real drivers
    multi_driver_nets = []
    output_types = {"output", "tri_state", "power_out"}
    for net_name, net_info in nets.items():
        drivers = [p for p in net_info["pins"]
                   if p["pin_type"] in output_types
                   and not p["component"].startswith("#")]
        if len(drivers) > 1:
            multi_driver_nets.append({
                "net": net_name,
                "drivers": drivers,
            })

    # Power net summary — for each named power rail, which real components connect
    power_net_summary = {}
    for net_name, net_info in nets.items():
        if net_name.startswith("__unnamed_"):
            continue
        is_power = any(p["pin_type"] in ("power_in", "power_out") for p in net_info["pins"])
        if is_power or net_name in ("GND", "VCC", "VDD", "+3V3", "+3.3V", "+5V", "+12V", "VBUS"):
            real_components = sorted(set(
                p["component"] for p in net_info["pins"]
                if not p["component"].startswith("#")
            ))
            power_net_summary[net_name] = {
                "pin_count": len([p for p in net_info["pins"] if not p["component"].startswith("#")]),
                "components": real_components,
            }

    return {
        "unconnected_pins": unconnected_pins,
        "single_pin_nets": single_pin_nets,
        "single_pin_net_findings": single_pin_net_findings,
        "multi_driver_nets": multi_driver_nets,
        "power_net_summary": power_net_summary,
    }


def _classify_nets(ctx: AnalysisContext) -> dict:
    """Classify all nets by type (ground, power, clock, data, etc.)."""
    nets = ctx.nets
    is_ground = ctx.is_ground
    is_power_net = ctx.is_power_net

    net_classes = {}
    for net_name, net_info in nets.items():
        if net_name.startswith("__unnamed_"):
            # Classify unnamed nets by pin types
            pin_types = set(p["pin_type"] for p in net_info["pins"])
            has_power = bool(pin_types & {"power_in", "power_out"})
            if has_power:
                net_classes[net_name] = "power_internal"
            else:
                net_classes[net_name] = "signal"
            continue

        nu = net_name.upper()
        if is_ground(net_name):
            net_classes[net_name] = "ground"
        elif is_power_net(net_name):
            net_classes[net_name] = "power"
        elif any(kw in nu for kw in ("SCL", "SCK", "CLK", "MCLK", "SCLK", "XTAL", "OSC")):
            net_classes[net_name] = "clock"
        elif any(kw in nu for kw in ("SDA", "MOSI", "MISO", "SDI", "SDO", "UART", "TX", "RX")):
            net_classes[net_name] = "data"
        elif any(kw in nu for kw in ("USB", "CAN", "LVDS", "ETH")):
            net_classes[net_name] = "high_speed"
        elif any(kw in nu for kw in ("ADC", "AIN", "VREF", "VSENSE", "ISENSE")):
            net_classes[net_name] = "analog"
        elif any(kw in nu for kw in ("RESET", "NRST", "RST", "EN", "ENABLE")):
            net_classes[net_name] = "control"
        elif any(kw in nu for kw in ("CS", "SS", "NSS", "CE", "SEL")):
            # KH-097: Exclude video sync signals (CSYNC, HSYNC, VSYNC)
            if any(sync in nu for sync in ("CSYNC", "HSYNC", "VSYNC", "SYNC")):
                net_classes[net_name] = "signal"
            else:
                net_classes[net_name] = "chip_select"
        elif any(kw in nu for kw in ("INT", "IRQ", "ALERT", "DRDY")):
            net_classes[net_name] = "interrupt"
        elif any(kw in nu for kw in _OUTPUT_DRIVE_KEYWORDS):
            net_classes[net_name] = "output_drive"
        elif any(kw in nu for kw in ("SWD", "SWCLK", "SWDIO", "SWO", "JTAG", "TCK", "TMS", "TDI", "TDO")):
            net_classes[net_name] = "debug"
        elif any(kw in nu for kw in ("BOOT", "TEST")):
            net_classes[net_name] = "config"
        else:
            net_classes[net_name] = "signal"

    return net_classes


def _map_power_domains(ctx: AnalysisContext) -> dict:
    """Map each IC to its power domains.

    For each IC, determine which power rails it connects to.
    Track IO-level reference pins (VDDIO, VIO) separately from internal supplies
    (VCC, VDD) -- for cross-domain analysis, the IO rail determines signal levels.
    """
    components = ctx.components
    pin_net = ctx.pin_net
    known_power_rails = ctx.known_power_rails
    is_ground = ctx.is_ground
    is_power_net = ctx.is_power_net

    _io_pin_names = {"VDDIO", "VIO", "VCCA", "VCCB", "VREF", "VLOGIC",
                     "DVDD", "DVCC", "IOVDD", "IOVCC"}
    _sense_pin_names = {"IN+", "IN-", "INP", "INN", "SENSE", "VSENSE", "SNS",
                        "CSP", "CSN", "CS+", "CS-", "ISENSE", "IMON", "IOUT",
                        "SEN", "VS+", "VS-"}
    power_domains = {}
    # KH-224: Accumulate rails/io_rails across all units of multi-unit ICs
    _ref_rails: dict[str, set] = {}      # ref -> set of power rail nets
    _ref_io_rails: dict[str, set] = {}   # ref -> set of IO rail nets
    _ref_value: dict[str, str] = {}      # ref -> value (from first unit seen)
    ics = [c for c in components if c["type"] == "ic"]
    for ic in ics:
        ref = ic["reference"]
        if ref not in _ref_value:
            _ref_value[ref] = ic["value"]
        rails = _ref_rails.setdefault(ref, set())
        io_rails = _ref_io_rails.setdefault(ref, set())
        for pin in ic.get("pins", []):
            net_name, _ = pin_net.get((ref, pin["number"]), (None, None))
            if not net_name:
                continue
            pname_upper = pin["name"].upper()
            if pname_upper in _sense_pin_names:
                continue
            is_pwr = is_power_net(net_name) and not is_ground(net_name)
            is_named_pwr = pname_upper in ("VCC", "VDD", "AVCC", "AVDD", "VBUS",
                                           "VIN", "VOUT", "VDDIO", "VIO", "VCCA",
                                           "VCCB", "VREF", "VLOGIC", "DVDD", "DVCC",
                                           "IOVDD", "IOVCC", "VCCREG", "VREG")
            if is_pwr or is_named_pwr:
                rails.add(net_name)
                if pname_upper in _io_pin_names:
                    io_rails.add(net_name)
    for ref, rails in _ref_rails.items():
        if rails:
            io_rails = _ref_io_rails.get(ref, set())
            power_domains[ref] = {
                "value": _ref_value[ref],
                "power_rails": sorted(rails),
                "io_rails": sorted(io_rails) if io_rails else None,
            }

    # Fallback for legacy files where pin_net may be incomplete:
    # Match IC power pin NAMES (VCC, VDD, etc.) against known_power_rails by string.
    _pwr_pin_to_rail = {"VCC", "VDD", "AVCC", "AVDD", "DVCC", "DVDD",
                        "VDDIO", "VIO", "VCCA", "VCCB", "VBUS"}
    _fallback_rails: dict[str, set] = {}   # ref -> set of rails (aggregate across units)
    _fallback_value: dict[str, str] = {}
    for ic in ics:
        ref = ic["reference"]
        if ref in power_domains:
            continue
        if ref not in _fallback_value:
            _fallback_value[ref] = ic["value"]
        rails = _fallback_rails.setdefault(ref, set())
        for pin in ic.get("pins", []):
            pname = pin.get("name", "").upper()
            if pname not in _pwr_pin_to_rail:
                continue
            # Find a known power rail whose name matches this pin name
            for rail in known_power_rails:
                ru = rail.upper()
                if pname == ru or pname in ru or ru.startswith(pname):
                    rails.add(rail)
    for ref, rails in _fallback_rails.items():
        if rails:
            power_domains[ref] = {
                "value": _fallback_value[ref],
                "power_rails": sorted(rails),
                "io_rails": None,
                "_inferred_from": "pin_name_match",
            }

    # Group ICs by power domain
    domain_groups = {}
    for ref, info in power_domains.items():
        for rail in info["power_rails"]:
            domain_groups.setdefault(rail, []).append(ref)

    return {"ic_power_rails": power_domains, "domain_groups": domain_groups}


def _get_power_domains_for_refs(refs: set, power_domains: dict,
                                is_ground) -> set:
    """Get all power rail domains for a set of IC references."""
    domains = set()
    for r in refs:
        for rail in power_domains.get(r, {}).get("power_rails", []):
            if not is_ground(rail):
                domains.add(rail)
    return domains


def _get_io_domains_for_refs(refs: set, power_domains: dict,
                             is_ground) -> set:
    """Get I/O-level domains for cross-domain comparison.

    When an IC has a dedicated IO-level pin (VDDIO, VIO, etc.),
    use that rail for signal-level comparison instead of all power
    rails.  This avoids false positives where internal supplies
    (VCC charge pump, analog VDD) differ but the actual I/O
    voltage matches the other IC.
    """
    domains = set()
    for r in refs:
        info = power_domains.get(r, {})
        io = info.get("io_rails")
        if io:
            for rail in io:
                domains.add(rail)
        else:
            # No dedicated IO pin -- use all power rails
            for rail in info.get("power_rails", []):
                if not is_ground(rail):
                    domains.add(rail)
    return domains


def _rails_voltage_compatible(rails_a: set, rails_b: set) -> bool:
    """Check if two sets of rails share a rail or voltage."""
    if rails_a & rails_b:
        return True
    # Parse voltages from net names and check overlap
    va = {_parse_voltage_from_net_name(r) for r in rails_a} - {None}
    vb = {_parse_voltage_from_net_name(r) for r in rails_b} - {None}
    return bool(va & vb)


def _detect_cross_domain_signals(ctx: AnalysisContext, power_domains: dict,
                                 results_in: dict | None = None) -> list:
    """Find signals crossing between different power domains."""
    components = ctx.components
    nets = ctx.nets
    is_ground = ctx.is_ground
    is_power_net = ctx.is_power_net

    if results_in is None:
        results_in = {}

    cross_domain = []
    # Build set of ESD protection IC references for cross-domain filtering
    esd_ic_refs = set()
    for pd in results_in.get("protection_devices", []):
        if pd.get("type") == "esd_ic":
            esd_ic_refs.add(pd["ref"])

    # Detect level translator ICs -- these bridge domains intentionally so
    # signals through them don't need additional level shifting.
    level_translator_keywords = (
        "leveltranslator", "level_translator", "levelshift", "level_shift",
        "txb0", "txs0", "tca9", "lsf0", "sn74lvc", "sn74avc",
        "sn74cb3", "sn74cbt", "nlsx", "nts0", "fxl", "adg320",
        "max395", "gtl2", "pca960", "tca641",
    )
    level_translator_desc_keywords = (
        "level translator", "level shifter", "level-shifting",
        "voltage translator", "voltage level",
    )
    level_translator_refs = set()
    for ic in components:
        if ic["type"] != "ic":
            continue
        val_low = ic.get("value", "").lower()
        lib_low = ic.get("lib_id", "").lower()
        desc_low = ic.get("description", "").lower()
        kw_low = ic.get("keywords", "").lower()
        if (any(k in val_low or k in lib_low for k in level_translator_keywords) or
                any(k in desc_low or k in kw_low for k in level_translator_desc_keywords)):
            level_translator_refs.add(ic["reference"])
    for net_name, net_info in nets.items():
        if is_power_net(net_name) or is_ground(net_name):
            continue
        # Find all ICs on this net
        ic_refs = set()
        for p in net_info["pins"]:
            if p["component"] in power_domains and not p["component"].startswith("#"):
                ic_refs.add(p["component"])
        if len(ic_refs) < 2:
            continue

        # Check if they're on different power domains
        domains_on_net = _get_power_domains_for_refs(ic_refs, power_domains, is_ground)
        if len(domains_on_net) > 1:
            # Don't flag as needing level shifter when the only cross-domain
            # connection is through an ESD/protection IC -- those clamp voltage
            # but don't change signal levels (e.g., USBLC6 on USB D+/D-)
            non_esd_refs = ic_refs - esd_ic_refs
            non_esd_domains = _get_power_domains_for_refs(non_esd_refs, power_domains, is_ground)

            # Check if a level translator is on this net -- if so, it already
            # handles the voltage translation
            translators_on_net = ic_refs & level_translator_refs
            has_translator = len(translators_on_net) > 0

            if len(non_esd_domains) > 1:
                if has_translator:
                    # Level translator present -- shifting is handled
                    needs_shifter = False
                else:
                    # Use IO-level domains for the level shifter decision.
                    # Check pairwise: every pair of ICs must share at least one
                    # common IO rail. A multi-rail SoC (e.g., +3.3V + VDDA)
                    # connecting to a simple IC on +3.3V shares +3.3V, so no
                    # level shifter is needed despite different rail counts.
                    # Also treat rails at the same voltage as equivalent (e.g.,
                    # +3V3 and VCC_3V3 are both 3.3V).
                    functional_refs = non_esd_refs - level_translator_refs
                    ic_list = sorted(functional_refs) if functional_refs else sorted(non_esd_refs)
                    needs_shifter = False
                    for i_idx in range(len(ic_list)):
                        for j_idx in range(i_idx + 1, len(ic_list)):
                            a_io = _get_io_domains_for_refs({ic_list[i_idx]}, power_domains, is_ground)
                            b_io = _get_io_domains_for_refs({ic_list[j_idx]}, power_domains, is_ground)
                            if not _rails_voltage_compatible(a_io, b_io):
                                needs_shifter = True
                                break
                        if needs_shifter:
                            break
            else:
                needs_shifter = False
            entry = {
                "net": net_name,
                "ics": sorted(ic_refs),
                "power_domains": sorted(domains_on_net),
                "needs_level_shifter": needs_shifter,
            }
            if has_translator:
                entry["level_translators"] = sorted(translators_on_net)
            cross_domain.append(entry)

    return cross_domain


def _enrich_device_ref(ref: str, comp_lookup: dict) -> dict:
    """Convert a bare component reference to {ref, value, lib_id} dict."""
    comp = comp_lookup.get(ref, {})
    return {
        "ref": ref,
        "value": comp.get("value", ""),
        "lib_id": comp.get("lib_id", ""),
    }


def _detect_i2c_buses(ctx: AnalysisContext) -> list[dict]:
    """Detect I2C buses by net name and pin name matching."""
    nets = ctx.nets
    pin_net = ctx.pin_net
    comp_lookup = ctx.comp_lookup
    parsed_values = ctx.parsed_values
    is_ground = ctx.is_ground
    is_power_net = ctx.is_power_net

    results = []

    # Look for SDA/SCL net pairs by net name
    i2c_nets = {}
    for net_name in nets:
        nu = net_name.upper()
        if "SDA" in nu or "SCL" in nu or "I2C" in nu:
            # Skip SPI signals (MISO contains no I2C keywords, but SCLK/SCK match SCL)
            # Skip I2S signals (I2S0_RX_SDA etc. contain SDA as substring)
            # KH-086: Also exclude MOSI/MISO nets (SPI data lines on dual-function ICs)
            if "SCLK" in nu or nu.endswith("SCK") or "SPI" in nu or "MOSI" in nu or "MISO" in nu:
                continue
            if "I2S" in nu:
                continue
            bus_id = nu.replace("SDA", "").replace("SCL", "").replace("I2C", "").replace("_", "").strip()
            i2c_nets.setdefault(bus_id, {})[nu] = net_name

    # Generate I2C bus entries from net-name matches
    i2c_seen_nets = set()
    for bus_id, net_map in i2c_nets.items():
        for nu_key, net_name in net_map.items():
            if net_name in i2c_seen_nets:
                continue
            i2c_seen_nets.add(net_name)
            net_info = nets.get(net_name, {})
            line = "SDA" if "SDA" in nu_key else "SCL"
            device_refs = [p["component"] for p in net_info.get("pins", [])
                           if comp_lookup.get(p["component"], {}).get("type") == "ic"]
            devices = [_enrich_device_ref(r, comp_lookup) for r in device_refs]
            # Find pull-up resistors
            pullups = []
            for p in net_info.get("pins", []):
                comp = comp_lookup.get(p["component"])
                if comp and comp["type"] == "resistor":
                    r_val = parsed_values.get(p["component"])
                    if r_val:
                        other_pin = "1" if p["pin_number"] == "2" else "2"
                        other_net, _ = pin_net.get((p["component"], other_pin), (None, None))
                        if other_net and is_power_net(other_net) and not is_ground(other_net):
                            pullups.append({
                                "ref": p["component"],
                                "value": comp["value"],
                                "ohms": r_val,
                                "to_rail": other_net,
                            })
            if devices:  # Skip connector-only routing with no ICs
                load_count = len(devices)
                # Typical I2C input capacitance: ~5pF per device pin
                estimated_cin_pF = load_count * 5
                # Electrical parameters from pull-ups
                pu_ohms_list = [pu["ohms"] for pu in pullups if pu.get("ohms")]
                min_pu_ohms = min(pu_ohms_list) if pu_ohms_list else None
                if min_pu_ohms is not None:
                    if min_pu_ohms <= 500:
                        speed_mode = "high_speed"
                    elif min_pu_ohms <= 1500:
                        speed_mode = "fast_plus"
                    elif min_pu_ohms <= 4700:
                        speed_mode = "fast"
                    else:
                        speed_mode = "standard"
                else:
                    speed_mode = None
                # Voltage level from pull-up rail
                voltage_level = None
                for pu in pullups:
                    v = _estimate_rail_voltage(pu.get("to_rail", ""))
                    if v is not None:
                        voltage_level = v
                        break
                # Controller: MCU or FPGA on the bus
                controller = None
                for ref in device_refs:
                    fc = comp_lookup.get(ref, {}).get("functional_class", "")
                    if fc in ("mcu", "fpga"):
                        controller = ref
                        break
                results.append({
                    "net": net_name,
                    "line": line,
                    "devices": devices,
                    "load_count": load_count,
                    "estimated_bus_capacitance_pF": estimated_cin_pF,
                    "pull_ups": pullups,
                    "has_pull_up": len(pullups) > 0,
                    "speed_mode": speed_mode,
                    "voltage_level_V": voltage_level,
                    "pull_up_ohms": min_pu_ohms,
                    "controller": controller,
                })

    # Also detect I2C from pin names (for nets without SDA/SCL in their name)
    for net_name, net_info in nets.items():
        if net_name in i2c_seen_nets:
            continue  # Already found by net name
        # KH-086: Exclude SPI nets -- sensors with dual-function SDA/SCL pin names
        nn_upper = net_name.upper()
        if "SPI" in nn_upper or "MOSI" in nn_upper or "MISO" in nn_upper:
            continue
        sda_pins = [p for p in net_info["pins"]
                    if "SDA" in p.get("pin_name", "").upper()
                    and "I2S" not in p.get("pin_name", "").upper()]
        # Exclude SPI clock pins (SCLK, SCK) which contain "SCL" as substring
        # Exclude I2S pins which may contain SCL as substring
        scl_pins = [p for p in net_info["pins"]
                    if "SCL" in p.get("pin_name", "").upper()
                    and "SCLK" not in p.get("pin_name", "").upper()
                    and "I2S" not in p.get("pin_name", "").upper()
                    and p.get("pin_name", "").upper() not in ("SCK",)]
        if sda_pins or scl_pins:
            # Find pull-up resistors on this net
            pullups = []
            for p in net_info["pins"]:
                comp = comp_lookup.get(p["component"])
                if comp and comp["type"] == "resistor":
                    r_val = parsed_values.get(p["component"])
                    if r_val:
                        # Check if other end goes to a power rail
                        other_pin = "1" if p["pin_number"] == "2" else "2"
                        other_net, _ = pin_net.get((p["component"], other_pin), (None, None))
                        if other_net and is_power_net(other_net) and not is_ground(other_net):
                            pullups.append({
                                "ref": p["component"],
                                "value": comp["value"],
                                "ohms": r_val,
                                "to_rail": other_net,
                            })

            bus_type = "SDA" if sda_pins else "SCL"
            device_refs = [p["component"] for p in net_info["pins"]
                           if comp_lookup.get(p["component"], {}).get("type") == "ic"]
            devices = [_enrich_device_ref(r, comp_lookup) for r in device_refs]

            if devices:  # Skip connector-only routing with no ICs
                load_count = len(devices)
                # Electrical parameters from pull-ups
                pu_ohms_list = [pu["ohms"] for pu in pullups if pu.get("ohms")]
                min_pu_ohms = min(pu_ohms_list) if pu_ohms_list else None
                if min_pu_ohms is not None:
                    if min_pu_ohms <= 500:
                        speed_mode = "high_speed"
                    elif min_pu_ohms <= 1500:
                        speed_mode = "fast_plus"
                    elif min_pu_ohms <= 4700:
                        speed_mode = "fast"
                    else:
                        speed_mode = "standard"
                else:
                    speed_mode = None
                voltage_level = None
                for pu in pullups:
                    v = _estimate_rail_voltage(pu.get("to_rail", ""))
                    if v is not None:
                        voltage_level = v
                        break
                controller = None
                for ref in device_refs:
                    fc = comp_lookup.get(ref, {}).get("functional_class", "")
                    if fc in ("mcu", "fpga"):
                        controller = ref
                        break
                entry = {
                    "net": net_name,
                    "line": bus_type,
                    "devices": devices,
                    "load_count": load_count,
                    "estimated_bus_capacitance_pF": load_count * 5,
                    "pull_ups": pullups,
                    "has_pull_up": len(pullups) > 0,
                    "speed_mode": speed_mode,
                    "voltage_level_V": voltage_level,
                    "pull_up_ohms": min_pu_ohms,
                    "controller": controller,
                }

                # I2C rise time validation
                # EQ-097: t_r = 0.8473 * R_pullup * C_bus (RC time constant to 70% VDD)
                # I2C spec limits: Standard 1000ns, Fast 300ns, Fast+ 120ns, HS 50ns
                if entry.get("pull_ups") and entry.get("estimated_bus_capacitance_pF"):
                    pullup_ohms = [pu["ohms"] for pu in entry["pull_ups"] if pu.get("ohms")]
                    if pullup_ohms:
                        # Parallel combination if multiple pull-ups on same line
                        if len(pullup_ohms) == 1:
                            r_eff = pullup_ohms[0]
                        else:
                            r_eff = 1.0 / sum(1.0 / r for r in pullup_ohms)

                        c_bus_f = entry["estimated_bus_capacitance_pF"] * 1e-12
                        rise_time_ns = 0.8473 * r_eff * c_bus_f * 1e9

                        entry["rise_time_ns"] = round(rise_time_ns, 1)
                        entry["effective_pullup_ohms"] = round(r_eff, 1)

                        # Determine maximum supported speed mode
                        _I2C_MODES = [
                            ("HS",         50),
                            ("Fast-mode+", 120),
                            ("Fast-mode",  300),
                            ("Standard",  1000),
                        ]
                        max_mode = "Standard"
                        for mode_name, limit_ns in _I2C_MODES:
                            if rise_time_ns <= limit_ns:
                                max_mode = mode_name
                                break

                        entry["max_speed_mode"] = max_mode

                        # Warning if rise time is marginal (within 20% of limit)
                        for mode_name, limit_ns in _I2C_MODES:
                            if rise_time_ns <= limit_ns:
                                margin_pct = (limit_ns - rise_time_ns) / limit_ns * 100
                                if margin_pct < 20:
                                    entry["rise_time_warning"] = (
                                        f"Rise time {rise_time_ns:.0f}ns is within 20% of "
                                        f"{mode_name} limit ({limit_ns}ns) — "
                                        f"margin {margin_pct:.0f}%"
                                    )
                                break

                results.append(entry)

    return results


def _detect_spi_buses(ctx: AnalysisContext) -> list[dict]:
    """Detect SPI buses by MOSI/MISO/SCK/CS patterns (and newer COPI/CIPO/SDI/SDO)."""
    nets = ctx.nets
    comp_lookup = ctx.comp_lookup

    _spi_net_kw = ("MOSI", "MISO", "SCK", "SCLK", "COPI", "CIPO", "SDI", "SDO")
    _spi_canon = {  # normalize alternative names to canonical SPI signals
        "COPI": "MOSI", "SDO": "MOSI", "SDI": "MISO", "CIPO": "MISO",
        "SCLK": "SCK",
    }
    spi_signals = {}
    for net_name, net_info in nets.items():
        nu = net_name.upper()
        for kw in _spi_net_kw:
            if kw in nu:
                canon = _spi_canon.get(kw, kw)
                bus_id = nu.replace(kw, "").replace("_", "").strip() or "0"
                spi_signals.setdefault(bus_id, {})[canon] = {
                    "net": net_name,
                    "devices": [p["component"] for p in net_info["pins"]
                                if comp_lookup.get(p["component"], {}).get("type") == "ic"],
                }
        # Also check pin names
        for p in net_info["pins"]:
            pn = p.get("pin_name", "").upper()
            for kw in _spi_net_kw:
                if pn == kw:
                    canon = _spi_canon.get(kw, kw)
                    bus_id = "pin_" + p["component"]
                    spi_signals.setdefault(bus_id, {})[canon] = {
                        "net": net_name,
                        "devices": [pp["component"] for pp in net_info["pins"]
                                    if comp_lookup.get(pp["component"], {}).get("type") == "ic"],
                    }

    results = []
    for bus_id, signals in spi_signals.items():
        if len(signals) >= 2:  # At least 2 SPI signals to count as a bus
            # Skip if no ICs on any signal net (connector-only routing)
            has_ic = any(s.get("devices") for s in signals.values())
            if not has_ic:
                continue
            # Count unique devices across all SPI signals
            all_spi_devs = set()
            for sig_data in signals.values():
                all_spi_devs.update(sig_data.get("devices", []))
            results.append({
                "bus_id": bus_id,
                "signals": signals,
                "load_count": len(all_spi_devs),
            })

    return results


def _detect_uart_buses(ctx: AnalysisContext) -> list[dict]:
    """Detect UART buses by TX/RX net name patterns."""
    nets = ctx.nets
    comp_lookup = ctx.comp_lookup

    _uart_exclude = ("CAN", "SPI", "I2C", "MOSI", "MISO", "SCL", "SDA",
                     "RMII", "MII", "EMAC", "ENET", "ETH",
                     "PCIE", "PCI_", "HDMI", "LVDS", "MIPI",
                     "CLK", "CLOCK", "USB_D", "USBDM", "USBDP", "I2S")
    uart_nets = {}
    for net_name, net_info in nets.items():
        nu = net_name.upper()
        # Skip nets that belong to other bus types
        if any(kw in nu for kw in _uart_exclude):
            continue
        if any(kw in nu for kw in ("UART", "TX", "RX", "TXD", "RXD")):
            # Identify which devices connect
            device_refs = [p["component"] for p in net_info["pins"]
                           if comp_lookup.get(p["component"], {}).get("type") == "ic"]
            uart_nets[net_name] = {
                "net": net_name,
                "devices": [_enrich_device_ref(r, comp_lookup) for r in device_refs],
                "pin_count": len(net_info["pins"]),
            }

    # UART TX→RX crossover verification
    # For each TX net, check if it connects to a pin named RX on the other device (correct)
    # or a pin named TX (incorrect — TX wired to TX)
    _tx_pins = {"TX", "TXD", "UART_TX", "UART_TXD", "U_TX", "TXD0", "TXD1"}
    _rx_pins = {"RX", "RXD", "UART_RX", "UART_RXD", "U_RX", "RXD0", "RXD1"}

    for entry in uart_nets.values():
        net_name = entry["net"]
        nu = net_name.upper()
        # Determine if this is a TX or RX net from its name
        is_tx_net = any(kw in nu for kw in ("_TX", "TXD", "UART_TX")) and not any(kw in nu for kw in ("_RX", "RXD"))
        is_rx_net = any(kw in nu for kw in ("_RX", "RXD", "UART_RX")) and not any(kw in nu for kw in ("_TX", "TXD"))

        if not (is_tx_net or is_rx_net) or net_name not in nets:
            continue

        # Check pin names of connected ICs
        tx_pin_count = 0
        rx_pin_count = 0
        for p in nets[net_name]["pins"]:
            comp = comp_lookup.get(p["component"])
            if not comp or comp["type"] != "ic":
                continue
            pname = p.get("pin_name", "").upper()
            if pname in _tx_pins:
                tx_pin_count += 1
            elif pname in _rx_pins:
                rx_pin_count += 1

        # A TX net should connect to at least one RX pin (crossover)
        # If it connects to 2+ TX pins and no RX pins, that's TX→TX (wrong)
        if is_tx_net and tx_pin_count >= 2 and rx_pin_count == 0:
            entry["crossover_warning"] = (
                f"TX net {net_name} connects to {tx_pin_count} TX pins and "
                f"no RX pins — possible missing TX→RX crossover"
            )
        elif is_rx_net and rx_pin_count >= 2 and tx_pin_count == 0:
            entry["crossover_warning"] = (
                f"RX net {net_name} connects to {rx_pin_count} RX pins and "
                f"no TX pins — possible missing TX→RX crossover"
            )

    return list(uart_nets.values())


def _detect_sdio_buses(ctx: AnalysisContext) -> list[dict]:
    """Detect SDIO/SD/eMMC buses by CLK + CMD + D0 minimum."""
    nets = ctx.nets
    pin_net = ctx.pin_net
    comp_lookup = ctx.comp_lookup
    is_power_net = ctx.is_power_net

    _sdio_prefixes = ("SDIO", "SD_", "SD1_", "SD2_", "EMMC", "MMC", "WL_SDIO")
    sdio_signals = {}
    for net_name in nets:
        nu = net_name.upper()
        # Check if net matches an SDIO-related pattern
        matched_prefix = None
        for pfx in _sdio_prefixes:
            if pfx in nu:
                matched_prefix = pfx
                break
        if not matched_prefix:
            # Also match bare SD signal patterns like SDCLK, SDCMD
            if nu.startswith("SD") and any(nu.endswith(sig) for sig in ("CLK", "CMD", "D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7")):
                matched_prefix = "SD"
            else:
                continue

        # Classify the signal type
        sig_type = None
        if "CLK" in nu:
            sig_type = "CLK"
        elif "CMD" in nu:
            sig_type = "CMD"
        else:
            # Match data lines D0-D7
            dm = re.search(r'D(\d)', nu)
            if dm:
                sig_type = f"D{dm.group(1)}"

        if sig_type:
            # Group by bus prefix for multi-bus designs
            bus_key = matched_prefix.rstrip("_")
            sdio_signals.setdefault(bus_key, {})[sig_type] = net_name

    # Build SDIO bus entries
    results = []
    for bus_key, sigs in sdio_signals.items():
        if "CLK" not in sigs or "CMD" not in sigs or "D0" not in sigs:
            continue
        # Count data lines
        data_lines = sorted(k for k in sigs if k.startswith("D") and k[1:].isdigit())
        bus_width = len(data_lines)

        # Check for pull-ups on CMD and data lines
        pullup_nets = []
        for sig_name in ["CMD"] + data_lines:
            net_name = sigs.get(sig_name)
            if not net_name or net_name not in nets:
                continue
            for p in nets[net_name]["pins"]:
                comp = comp_lookup.get(p["component"])
                if comp and comp["type"] == "resistor":
                    r_n1, _ = pin_net.get((p["component"], "1"), (None, None))
                    r_n2, _ = pin_net.get((p["component"], "2"), (None, None))
                    other = r_n2 if r_n1 == net_name else r_n1
                    if other and is_power_net(other):
                        pullup_nets.append(sig_name)
                        break

        # Find connected devices
        all_devices = set()
        for sig_name, net_name in sigs.items():
            if net_name in nets:
                for p in nets[net_name]["pins"]:
                    if comp_lookup.get(p["component"], {}).get("type") == "ic":
                        all_devices.add(p["component"])

        results.append({
            "bus_id": bus_key,
            "bus_width": bus_width,
            "signals": {sig: net for sig, net in sigs.items()},
            "devices": sorted(all_devices),
            "has_pullups": len(pullup_nets) > 0,
            "pullup_signals": pullup_nets,
        })

    return results


def _detect_can_buses(ctx: AnalysisContext) -> list[dict]:
    """Detect CAN buses by net name keywords and transceiver IC presence."""
    components = ctx.components
    nets = ctx.nets
    comp_lookup = ctx.comp_lookup
    pin_net = ctx.pin_net
    parsed_values = ctx.parsed_values

    can_keywords = ("can_tx", "can_rx", "cantx", "canrx", "canh", "canl", "can_h", "can_l")
    # SN65HVD2xx/10xx are CAN; SN65HVD7x are RS-485 -- use specific prefixes
    can_transceiver_kw = ("sn65hvd2", "sn65hvd10", "mcp2551", "mcp2562", "mcp251",
                          "tja10", "tja11", "iso1050", "max3051", "ata6561",
                          "mcp2561", "iso1042")
    can_nets_found = {}
    for net_name, net_info in nets.items():
        nu = net_name.upper()
        if any(kw in nu.lower() for kw in can_keywords):
            device_refs = [p["component"] for p in net_info["pins"]
                           if comp_lookup.get(p["component"], {}).get("type") == "ic"]
            can_nets_found[net_name] = {
                "net": net_name,
                "devices": [_enrich_device_ref(r, comp_lookup) for r in device_refs],
            }
    # Also detect by CAN transceiver IC presence -- add transceiver info to bus
    for comp in components:
        if comp["type"] != "ic":
            continue
        val = comp.get("value", "").lower()
        lib = comp.get("lib_id", "").lower()
        if any(k in val or k in lib for k in can_transceiver_kw):
            if not can_nets_found:
                # No CAN nets found by name -- add a placeholder entry
                can_nets_found["__can_transceiver__"] = {
                    "net": "CAN",
                    "transceiver": comp["reference"],
                    "devices": [_enrich_device_ref(comp["reference"], comp_lookup)],
                }

    # CAN termination detection: look for 100-150 ohm resistors between CANH and CANL
    canh_nets = [n for n in can_nets_found if "CANH" in n.upper() or "CAN_H" in n.upper()]
    canl_nets = [n for n in can_nets_found if "CANL" in n.upper() or "CAN_L" in n.upper()]
    termination = None
    for canh_net in canh_nets:
        if canh_net not in nets:
            continue
        for p in nets[canh_net]["pins"]:
            comp = comp_lookup.get(p["component"])
            if not comp or comp["type"] != "resistor":
                continue
            r_val = parsed_values.get(p["component"])
            if r_val and 100 <= r_val <= 150:
                # Check if other end goes to a CANL net
                other_pin = "1" if p["pin_number"] == "2" else "2"
                other_net, _ = pin_net.get((p["component"], other_pin), (None, None))
                if other_net and any(other_net == cl for cl in canl_nets):
                    termination = f"{int(r_val)}\u03A9 ({p['component']})"
                    break
        if termination:
            break
    # Attach termination to all CAN bus entries
    for entry in can_nets_found.values():
        entry["termination"] = termination

    return list(can_nets_found.values())


def _detect_rs485_buses(ctx: AnalysisContext) -> list[dict]:
    """Detect RS-485/RS-422 buses by transceiver IC part number."""
    components = ctx.components
    pin_net = ctx.pin_net

    _rs485_kw = ("max485", "max3485", "max13485", "max14840", "max22500",
                 "sn65hvd7", "sn65hvd3", "sn75176", "sn75lbc",
                 "thvd14", "thvd15", "thvd16",
                 "isl317", "isl318", "isl319",
                 "sp3485", "sp3481", "sp3082", "sp485",
                 "adm485", "adm2485", "adm2587", "adm3485",
                 "ltc285", "ltc248", "ltc249",
                 "st3485", "st485")

    results = []
    for comp in components:
        if comp["type"] != "ic":
            continue
        val_lib = (comp.get("value", "") + " " + comp.get("lib_id", "")).lower()
        if not any(k in val_lib for k in _rs485_kw):
            continue
        ref = comp["reference"]
        # Map known pin functions
        a_net = b_net = di_net = ro_net = de_net = re_net = None
        for pin in comp.get("pins", []):
            pn = pin.get("name", "").upper()
            net_name, _ = pin_net.get((ref, pin["number"]), (None, None))
            if not net_name:
                continue
            if pn in ("A", "A/Y"):
                a_net = net_name
            elif pn in ("B", "B/Z"):
                b_net = net_name
            elif pn in ("DI", "D", "TXD", "DIN"):
                di_net = net_name
            elif pn in ("RO", "R", "RXD", "DOUT"):
                ro_net = net_name
            elif pn in ("DE",):
                de_net = net_name
            elif pn in ("RE", "~RE", "~{RE}", "/RE"):
                re_net = net_name
        entry = {
            "transceiver": ref,
            "value": comp.get("value", ""),
        }
        if a_net:
            entry["a_net"] = a_net
        if b_net:
            entry["b_net"] = b_net
        if di_net:
            entry["di_net"] = di_net
        if ro_net:
            entry["ro_net"] = ro_net
        if de_net:
            entry["de_net"] = de_net
        if re_net:
            entry["re_net"] = re_net
        results.append(entry)

    return results


def _analyze_bus_protocols(ctx: AnalysisContext) -> dict:
    """Detect I2C, SPI, UART, CAN, SDIO, RS-485 buses and check configuration."""
    nets = ctx.nets
    comp_lookup = ctx.comp_lookup

    buses: dict = {
        "i2c": _detect_i2c_buses(ctx),
        "spi": _detect_spi_buses(ctx),
        "uart": _detect_uart_buses(ctx),
        "can": _detect_can_buses(ctx),
    }

    sdio = _detect_sdio_buses(ctx)
    if sdio:
        buses["sdio"] = sdio

    rs485 = _detect_rs485_buses(ctx)
    if rs485:
        buses["rs485"] = rs485

    # SPI enrichment: add chip_select count and bus_mode
    for spi_entry in buses.get("spi", []):
        sigs = spi_entry.get("signals", {})
        # Count CS/SS nets for this bus
        cs_nets = []
        bus_id = spi_entry.get("bus_id", "")
        for net_name in nets:
            nu = net_name.upper()
            if any(kw in nu for kw in ("CS", "SS", "NSS", "SPI_CS", "SPI_SS",
                                       "CSN", "NCS", "SSEL", "CSEL")):
                if bus_id in ("0", "") or bus_id in nu.replace("_", ""):
                    cs_nets.append(net_name)
        spi_entry["chip_select_count"] = len(cs_nets)
        # SPI CS conflict: find cases where multiple ICs share the same CS net
        cs_device_map = {}  # net_name -> [device_refs]
        for net_name in cs_nets:
            if net_name not in nets:
                continue
            devices_on_cs = []
            for p in nets[net_name]["pins"]:
                comp = comp_lookup.get(p["component"])
                if comp and comp["type"] == "ic":
                    devices_on_cs.append(p["component"])
            if len(devices_on_cs) > 1:
                cs_device_map[net_name] = devices_on_cs

        if cs_device_map:
            spi_entry["cs_conflicts"] = [
                {
                    "net": net_name,
                    "devices": devices,
                    "message": (f"CS net {net_name} shared by {len(devices)} devices "
                                f"({', '.join(devices)}) — cannot address independently"),
                }
                for net_name, devices in cs_device_map.items()
            ]
        has_mosi = "MOSI" in sigs
        has_miso = "MISO" in sigs
        if has_mosi and has_miso:
            spi_entry["bus_mode"] = "full_duplex"
        elif has_mosi or has_miso:
            spi_entry["bus_mode"] = "half_duplex"

        # Add top-level devices list (aggregated from all signal entries)
        # for schema consistency with I2C/UART/CAN which have flat devices[]
        all_spi_devs: set[str] = set()
        for sig_info in sigs.values():
            if isinstance(sig_info, dict):
                all_spi_devs.update(sig_info.get('devices', []))
        spi_entry['devices'] = [_enrich_device_ref(r, comp_lookup) for r in sorted(all_spi_devs)]

        # Controller: MCU/FPGA driving SCK (clock master)
        sck_info = sigs.get("SCK")
        controller = None
        if isinstance(sck_info, dict):
            for ref in sck_info.get("devices", []):
                fc = comp_lookup.get(ref, {}).get("functional_class", "")
                if fc in ("mcu", "fpga"):
                    controller = ref
                    break
        spi_entry["controller"] = controller

    return buses


def _guess_diff_protocol(net_name: str) -> str:
    """Guess the protocol from a differential pair net name."""
    nu = net_name.upper()
    if "USB" in nu:
        return "USB"
    if "LVDS" in nu:
        return "LVDS"
    if "ETH" in nu or "MDIO" in nu or "RGMII" in nu or "SGMII" in nu:
        return "Ethernet"
    if "HDMI" in nu or "TMDS" in nu:
        return "HDMI"
    if "MIPI" in nu or "DSI" in nu or "CSI" in nu:
        return "MIPI"
    if "PCIE" in nu or "PCI" in nu:
        return "PCIe"
    if "SATA" in nu:
        return "SATA"
    if "CAN" in nu:
        return "CAN"
    if "RS485" in nu or "RS-485" in nu:
        return "RS-485"
    return "differential"


def _detect_differential_pairs(ctx: AnalysisContext) -> list:
    """Detect differential pairs by suffix matching."""
    components = ctx.components
    nets = ctx.nets
    pin_net = ctx.pin_net
    comp_lookup = ctx.comp_lookup
    parsed_values = ctx.parsed_values
    is_power_net = ctx.is_power_net
    is_ground = ctx.is_ground

    diff_pairs = []

    # Suffix pair table: (positive_suffix, negative_suffix) -> protocol guess
    _diff_suffix_pairs = [
        # USB
        ("_DP", "_DM"), ("_D+", "_D-"), ("_D_P", "_D_N"), ("DP", "DM"),
        # Generic differential
        ("_P", "_N"), ("+", "-"),
        # LVDS / Ethernet
        ("_TX+", "_TX-"), ("_RX+", "_RX-"),
        ("_TXP", "_TXN"), ("_RXP", "_RXN"),
        ("_TD+", "_TD-"), ("_RD+", "_RD-"),
        ("_TDP", "_TDN"), ("_RDP", "_RDN"),
    ]

    # Net-name-based detection: find matching suffix pairs
    net_names_upper = {n.upper(): n for n in nets}
    found_pairs: set[tuple[str, str]] = set()  # track to avoid duplicates

    for pos_sfx, neg_sfx in _diff_suffix_pairs:
        for nu, real_name in net_names_upper.items():
            if nu.endswith(pos_sfx.upper()):
                base = nu[:-len(pos_sfx)]
                neg_candidate = base + neg_sfx.upper()
                if neg_candidate in net_names_upper:
                    pos_real = real_name
                    neg_real = net_names_upper[neg_candidate]
                    pair_key = (min(pos_real, neg_real), max(pos_real, neg_real))
                    if pair_key in found_pairs:
                        continue
                    # Skip power/ground nets (V+/V-, IN+/IN- on power rails)
                    if is_power_net(pos_real) or is_power_net(neg_real):
                        continue
                    if is_ground(pos_real) or is_ground(neg_real):
                        continue
                    found_pairs.add(pair_key)

                    protocol = _guess_diff_protocol(pos_real)
                    entry: dict = {
                        "type": protocol,
                        "positive": pos_real,
                        "negative": neg_real,
                    }

                    # Find shared ICs (connected to both nets)
                    pos_comps = {p["component"] for p in nets[pos_real]["pins"]
                                 if not p["component"].startswith("#")}
                    neg_comps = {p["component"] for p in nets[neg_real]["pins"]
                                 if not p["component"].startswith("#")}
                    shared = pos_comps & neg_comps
                    if shared:
                        entry["shared_ics"] = sorted(shared)

                    # Check for ESD protection
                    esd_chips = [c for c in shared
                                 if comp_lookup.get(c, {}).get("type") == "ic"]
                    entry["has_esd"] = len(esd_chips) > 0
                    if esd_chips:
                        entry["esd_protection"] = esd_chips

                    # CAN-specific: check for termination resistor
                    if protocol == "CAN":
                        term_resistors = []
                        for c in components:
                            if c["type"] == "resistor":
                                r_n1 = pin_net.get((c["reference"], "1"), (None, None))[0]
                                r_n2 = pin_net.get((c["reference"], "2"), (None, None))[0]
                                if r_n1 and r_n2:
                                    if ({r_n1, r_n2} == {pos_real, neg_real}):
                                        term_resistors.append({
                                            "ref": c["reference"],
                                            "value": c["value"],
                                            "ohms": parsed_values.get(c["reference"]),
                                        })
                        entry["termination"] = term_resistors
                        entry["has_termination"] = len(term_resistors) > 0

                    # Series resistors on either net
                    series_res = []
                    for net_r in (pos_real, neg_real):
                        for p in nets[net_r]["pins"]:
                            comp = comp_lookup.get(p["component"])
                            if comp and comp["type"] == "resistor":
                                series_res.append(p["component"])
                    if series_res:
                        entry["series_resistors"] = sorted(set(series_res))

                    diff_pairs.append(entry)

    return diff_pairs


def _check_erc_warnings(ctx: AnalysisContext) -> list:
    """Check for ERC-style warnings (no driver, output conflicts)."""
    nets = ctx.nets
    is_ground = ctx.is_ground
    is_power_net = ctx.is_power_net

    erc_warnings = []

    for net_name, net_info in nets.items():
        if is_power_net(net_name) or is_ground(net_name):
            continue
        if net_name.startswith("__unnamed_"):
            continue

        pin_types = [p["pin_type"] for p in net_info["pins"] if not p["component"].startswith("#")]
        type_set = set(pin_types)

        # Input-only net: all pins are inputs, no driver
        outputs = {"output", "tri_state", "power_out", "open_collector", "open_emitter"}
        drivers = {"output", "tri_state", "power_out", "open_collector", "open_emitter", "bidirectional"}
        has_driver = bool(type_set & drivers)
        has_input = bool(type_set & {"input", "power_in"})

        if has_input and not has_driver and len(pin_types) > 1:
            erc_warnings.append({
                "type": "no_driver",
                "net": net_name,
                "message": f"Net '{net_name}' has input pins but no output driver",
                "pins": [p for p in net_info["pins"] if not p["component"].startswith("#")],
            })

        # Multiple outputs on same net (non-tristate)
        hard_outputs = [p for p in net_info["pins"]
                        if p["pin_type"] == "output" and not p["component"].startswith("#")]
        if len(hard_outputs) > 1:
            # Suppress when all drivers are from the same component (paralleled pins)
            driver_components = {p["component"] for p in hard_outputs}
            if len(driver_components) > 1:
                erc_warnings.append({
                    "type": "output_conflict",
                    "net": net_name,
                    "message": f"Net '{net_name}' has {len(hard_outputs)} output drivers (potential conflict)",
                    "drivers": hard_outputs,
                })

    return erc_warnings


def _check_passive_ratings(ctx: AnalysisContext) -> list:
    """Check passive component voltage ratings against rail voltages."""
    components = ctx.components
    pin_net = ctx.pin_net

    passive_warnings = []
    for c in components:
        if c["type"] == "capacitor" and c.get("value"):
            # Check if capacitor voltage rating is in the value string
            val_str = c["value"]
            # Common pattern: "100n/16V", "10u 25V", "22uF 6.3V"
            v_match = re.search(r'(\d+(?:\.\d+)?)\s*[Vv]', val_str)
            if v_match:
                rated_v = float(v_match.group(1))
                # Check which rails this cap connects to
                c_n1, _ = pin_net.get((c["reference"], "1"), (None, None))
                c_n2, _ = pin_net.get((c["reference"], "2"), (None, None))
                # Rough rail voltage estimation from name
                for net in [c_n1, c_n2]:
                    if net:
                        v_est = _estimate_rail_voltage(net)
                        if v_est and rated_v < v_est * 1.5:
                            passive_warnings.append({
                                "component": c["reference"],
                                "value": c["value"],
                                "rated_voltage": rated_v,
                                "rail": net,
                                "estimated_rail_v": v_est,
                                "warning": f"Voltage derating margin < 50% ({rated_v}V rated on ~{v_est}V rail)",
                            })

    return passive_warnings


def analyze_design_rules(ctx: AnalysisContext, results_in: dict | None = None) -> dict:
    """Deep EE analysis: power domains, bus protocols, differential pairs, ERC checks."""
    net_classes = _classify_nets(ctx)
    pd = _map_power_domains(ctx)
    cross_domain = _detect_cross_domain_signals(ctx, pd["ic_power_rails"], results_in)
    buses = _analyze_bus_protocols(ctx)
    diff_pairs = _detect_differential_pairs(ctx)
    erc = _check_erc_warnings(ctx)
    passive = _check_passive_ratings(ctx)
    return {
        "net_classification": net_classes,
        "power_domains": pd,
        "cross_domain_signals": cross_domain,
        "bus_analysis": buses,
        "differential_pairs": diff_pairs,
        "erc_warnings": erc,
        "passive_warnings": passive,
    }


def _estimate_rail_voltage(net_name: str) -> float | None:
    """Estimate voltage of a power rail from its name."""
    if not net_name:
        return None
    nu = net_name.upper()
    if nu in ("GND", "VSS", "AGND", "DGND"):
        return 0
    v = _parse_voltage_from_net_name(net_name)
    if v is not None:
        return v
    # Hardcoded fallbacks for common names without voltage numbers
    if "VBUS" in nu or "USB" in nu:
        return 5.0
    return None


def check_annotation_completeness(components: list[dict]) -> dict:
    """Check for annotation issues: duplicate references, unannotated ('?') refs, missing values.

    These are common pre-fabrication mistakes that KiCad's ERC should also catch,
    but detecting them in the script output helps catch them earlier in the workflow.
    """
    # Skip power symbols and flags
    real_components = [c for c in components
                       if c["type"] not in ("power_symbol", "power_flag", "flag")]

    # Duplicate references (same ref, different UUID — not multi-unit which share refs)
    ref_uuids: dict[str, list[str]] = {}
    for c in real_components:
        ref_uuids.setdefault(c["reference"], []).append(c["uuid"])
    # Multi-unit symbols legitimately share a reference, so only flag if the
    # UUIDs come from symbols with unit=None (single-unit) or if there are
    # more instances than expected units
    duplicates = []
    for ref, uuids in ref_uuids.items():
        if len(uuids) > 1:
            # Check if these are multi-unit instances (different unit numbers)
            units = [c.get("unit") for c in real_components if c["reference"] == ref]
            unique_units = set(u for u in units if u is not None)
            if len(unique_units) < len(uuids):
                duplicates.append(ref)

    # Unannotated references (contain '?')
    unannotated = sorted(set(
        c["reference"] for c in real_components if "?" in c["reference"]
    ))

    # Missing values (empty or "~" which KiCad uses as placeholder)
    missing_value = sorted(set(
        c["reference"] for c in real_components
        if c["type"] not in ("test_point", "mounting_hole", "fiducial", "graphic")
        and (not c["value"] or c["value"] == "~")
    ))

    # References that don't follow standard numbering (e.g., R0, C0 — unusual starting point)
    zero_indexed = sorted(set(
        c["reference"] for c in real_components
        if re.match(r'^[A-Z]+0$', c["reference"])
    ))

    result = {}
    if duplicates:
        result["duplicate_references"] = sorted(duplicates)
    if unannotated:
        result["unannotated"] = unannotated
    if missing_value:
        result["missing_value"] = missing_value
    if zero_indexed:
        result["zero_indexed_refs"] = zero_indexed
    return result


def validate_label_shapes(labels: list[dict], nets: dict) -> list[dict]:
    """Validate global/hierarchical label shapes against net signal direction.

    Label shapes (input, output, bidirectional, tri_state, passive) should be
    consistent for the same net name and should match the electrical direction
    of the signals on that net.
    """
    warnings = []

    # Group labels by net name
    net_labels: dict[str, list[dict]] = {}
    for lbl in labels:
        if lbl["type"] in ("global_label", "hierarchical_label") and lbl.get("shape"):
            net_labels.setdefault(lbl["name"], []).append(lbl)

    # Check for shape inconsistency within the same net
    for net_name, lbls in net_labels.items():
        shapes = set(l["shape"] for l in lbls)
        if len(shapes) > 1:
            warnings.append({
                "type": "inconsistent_shape",
                "net": net_name,
                "shapes": sorted(shapes),
                "message": f"Net '{net_name}' has labels with different shapes: {sorted(shapes)}",
            })

    # Check for input-shaped labels on nets driven only by other inputs (no source)
    for net_name, lbls in net_labels.items():
        shapes = set(l["shape"] for l in lbls)
        if shapes == {"input"} and net_name in nets:
            net_info = nets[net_name]
            pin_types = set(p["pin_type"] for p in net_info["pins"]
                           if not p["component"].startswith("#"))
            drivers = {"output", "tri_state", "power_out", "open_collector", "open_emitter", "bidirectional"}
            if not (pin_types & drivers):
                warnings.append({
                    "type": "undriven_input_label",
                    "net": net_name,
                    "message": f"Net '{net_name}' has input-shaped label(s) but no driver pins on the net",
                })

    return warnings


def audit_pwr_flags(components: list[dict], nets: dict, known_power_rails: set) -> list[dict]:
    """Audit power rails for missing PWR_FLAG symbols.

    KiCad requires PWR_FLAG on power nets that are only driven by power_in pins
    (e.g., a connector supplying power). Without PWR_FLAG, ERC reports "power pin
    not driven" errors.
    """
    warnings = []

    # Find nets with PWR_FLAG
    flagged_nets = set()
    for c in components:
        if c["type"] == "power_flag" or (c["type"] == "flag" and "PWR_FLAG" in c.get("lib_id", "")):
            # PWR_FLAG connects to whatever net its pin is on
            for pin in c.get("pins", []):
                px, py = pin["x"], pin["y"]
                # Find which net this pin is on
                for net_name, net_info in nets.items():
                    for p in net_info["pins"]:
                        if p["component"] == c["reference"]:
                            flagged_nets.add(net_name)

    # Check each power rail
    for net_name in known_power_rails:
        if net_name in flagged_nets:
            continue
        if net_name not in nets:
            continue
        net_info = nets[net_name]
        pin_types = set(p["pin_type"] for p in net_info["pins"])

        # If the net has only power_in pins (no power_out), it needs PWR_FLAG
        has_power_out = "power_out" in pin_types
        has_power_in = "power_in" in pin_types

        if has_power_in and not has_power_out:
            warnings.append({
                "net": net_name,
                "message": f"Power rail '{net_name}' has power_in pins but no power_out or PWR_FLAG — ERC will flag this",
                "pin_types": sorted(pin_types),
            })

    return warnings


def validate_footprint_filters(components: list[dict], lib_symbols: dict) -> list[dict]:
    """Validate assigned footprints against library symbol ki_fp_filters.

    If a symbol defines footprint filter patterns (ki_fp_filters), the assigned
    footprint should match at least one pattern. Mismatches suggest wrong footprint
    assignment (e.g., through-hole resistor assigned to SMD symbol).
    """
    import fnmatch
    warnings = []

    for c in components:
        if c["type"] in ("power_symbol", "power_flag", "flag", "test_point",
                          "mounting_hole", "fiducial", "graphic"):
            continue
        if not c["footprint"]:
            continue

        sym_def = lib_symbols.get(c["lib_id"], {})
        fp_filters_str = sym_def.get("ki_fp_filters", "")
        if not fp_filters_str:
            continue

        # ki_fp_filters is a space-separated list of glob patterns
        patterns = fp_filters_str.split()
        if not patterns:
            continue

        # Extract just the footprint name (after the library prefix)
        fp_name = c["footprint"].split(":")[-1] if ":" in c["footprint"] else c["footprint"]
        fp_full = c["footprint"]

        # Check if any pattern matches
        matched = False
        for pat in patterns:
            if fnmatch.fnmatch(fp_name, pat) or fnmatch.fnmatch(fp_full, pat):
                matched = True
                break

        if not matched:
            # Check if the footprint is from a custom/project-local library.
            # Standard KiCad libraries use well-known prefixes; anything else
            # is project-local and mismatches are intentional.
            _STANDARD_FP_LIBS = {
                "Capacitor_SMD", "Capacitor_THT", "Resistor_SMD", "Resistor_THT",
                "Inductor_SMD", "Inductor_THT", "Package_SO", "Package_QFP",
                "Package_DFN_QFN", "Package_BGA", "Package_TO_SOT_SMD",
                "Package_TO_SOT_THT", "Connector_PinHeader", "Connector_PinSocket",
                "Connector_USB", "Crystal", "LED_SMD", "LED_THT", "Diode_SMD",
                "Diode_THT", "RF_Module", "Button_Switch_SMD", "Button_Switch_THT",
                "Fuse", "TestPoint", "Buzzer_Beeper", "Relay_SMD", "Relay_THT",
                "Transformer_SMD", "Transformer_THT", "Varistor", "Jumper",
                "MountingHole", "Fiducial", "Heatsink",
            }
            sym_lib = c["lib_id"].split(":")[0] if ":" in c["lib_id"] else ""
            fp_lib = c["footprint"].split(":")[0] if ":" in c["footprint"] else ""
            custom_library = bool(fp_lib and (
                (sym_lib and sym_lib.lower() == fp_lib.lower())
                or fp_lib not in _STANDARD_FP_LIBS
            ))

            warnings.append({
                "component": c["reference"],
                "footprint": c["footprint"],
                "filters": patterns,
                "custom_library": custom_library,
                "message": f"{c['reference']}: footprint '{fp_name}' doesn't match any filter pattern {patterns}",
            })

    return warnings


def audit_datasheet_coverage(components: list[dict],
                             project_dir: str) -> list[dict]:
    """Emit a banner-level finding when datasheet evidence is absent.

    Datasheets are what separate a consistency check from a correctness
    check: without them, the reviewer can only confirm the design agrees
    with itself. When the project has no ``datasheets/`` directory AND
    none of its BOM components carry an MPN, any pin-level or electrical
    claim in a downstream review is guesswork. Surface that fact loudly
    instead of letting it slip into a footnote.

    Rule IDs: DS-001 (no datasheets dir + no MPNs — reviews cannot be
    grounded in manufacturer data), DS-002 (datasheets dir missing but
    MPNs are set — offer to sync).
    """
    findings: list[dict] = []
    real = [c for c in components
            if c.get("type") not in ("power_symbol", "power_flag", "flag",
                                     "test_point", "mounting_hole",
                                     "fiducial", "graphic")
            and c.get("in_bom") and not c.get("dnp")]
    # Deduplicate by reference (multi-unit symbols)
    seen = set()
    unique = []
    for c in real:
        ref = c.get("reference", "")
        if ref and ref not in seen:
            seen.add(ref)
            unique.append(c)
    total = len(unique)
    if total == 0:
        return findings

    with_mpn = [c for c in unique if c.get("mpn")]
    mpn_count = len(with_mpn)
    mpn_pct = (mpn_count / total * 100) if total else 0.0

    # Look for datasheets in conventional locations relative to the
    # project directory. extracted/ holds structured extractions from the
    # datasheet_extract_cache; its presence implies datasheets exist.
    import os as _os
    pd = project_dir or "."
    candidates = [
        _os.path.join(pd, "datasheets"),
        _os.path.join(pd, "datasheets", "extracted"),
        _os.path.join(pd, "docs", "datasheets"),
        _os.path.join(_os.path.dirname(pd), "datasheets"),
    ]
    ds_dir_found = next(
        (c for c in candidates if _os.path.isdir(c)), None)
    ds_file_count = 0
    if ds_dir_found:
        try:
            for _root, _dirs, _files in _os.walk(ds_dir_found):
                ds_file_count += sum(1 for f in _files
                                     if f.lower().endswith((".pdf", ".json")))
        except OSError:
            pass

    # Build finding.
    refs_without_mpn = sorted(c.get("reference", "")
                              for c in unique if not c.get("mpn"))[:20]

    if ds_dir_found and ds_file_count > 0:
        # Datasheets present — no banner needed. Emit info-only if coverage
        # is partial so the reviewer knows which refs are ungrounded.
        if mpn_pct < 90 and refs_without_mpn:
            findings.append({
                "detector": "audit_datasheet_coverage",
                "rule_id": "DS-003",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "bom",
                "category": "verification",
                "summary": (f"Datasheets present ({ds_file_count} files) but "
                            f"{total - mpn_count}/{total} BOM parts lack an "
                            "MPN — those parts can't be cross-referenced."),
                "components": refs_without_mpn,
                "nets": [],
                "pins": [],
                "datasheets_dir": ds_dir_found,
                "datasheet_file_count": ds_file_count,
                "bom_size": total,
                "mpn_coverage_percent": round(mpn_pct, 1),
                "recommendation": ("Set the MPN field on the listed parts "
                                   "and re-sync datasheets so every BOM "
                                   "entry has manufacturer evidence."),
                "report_context": {
                    "section": "Datasheet Coverage",
                    "impact": ("Partial coverage: pin mapping and electrical "
                               "claims for unmapped parts remain unverified."),
                    "standard_ref": "",
                },
            })
        return findings

    if mpn_count == 0:
        # DS-001: no datasheets dir AND no MPNs. Downstream review cannot
        # make any verified claim — this is a correctness-vs-consistency
        # gap the reviewer has to state up front.
        findings.append({
            "detector": "audit_datasheet_coverage",
            "rule_id": "DS-001",
            "severity": "error",
            "confidence": "deterministic",
            "evidence_source": "bom",
            "category": "verification",
            "summary": ("No datasheets directory found and no BOM parts "
                        "have MPNs. Review is a consistency check only — "
                        "manufacturer specs cannot be verified."),
            "components": [],
            "nets": [],
            "pins": [],
            "datasheets_dir": None,
            "datasheet_file_count": 0,
            "bom_size": total,
            "mpn_coverage_percent": 0.0,
            "recommendation": (
                "Before reporting 'verified' findings, (1) populate the MPN "
                "field on BOM parts, (2) run the datasheet sync skill "
                "(digikey, mouser, lcsc, or element14) to download PDFs "
                "into ./datasheets/, then re-run analysis. If datasheets "
                "are unreachable, state every pin-level and electrical "
                "claim as 'per symbol/library' (consistency), not "
                "'verified against datasheet' (correctness)."),
            "report_context": {
                "section": "Datasheet Coverage",
                "impact": ("Report wording must avoid 'verified' / "
                           "'datasheet-confirmed' language for every BOM "
                           "part — none have manufacturer evidence "
                           "attached."),
                "standard_ref": "",
            },
        })
    else:
        # DS-002: MPNs exist but no datasheets dir. Low-friction fix — tell
        # the reviewer to run sync.
        findings.append({
            "detector": "audit_datasheet_coverage",
            "rule_id": "DS-002",
            "severity": "warning",
            "confidence": "deterministic",
            "evidence_source": "bom",
            "category": "verification",
            "summary": (f"No datasheets directory found ({mpn_count}/{total}"
                        " parts have MPNs). Sync datasheets before making "
                        "pin-level claims."),
            "components": sorted(c.get("reference", "")
                                 for c in with_mpn)[:20],
            "nets": [],
            "pins": [],
            "datasheets_dir": None,
            "datasheet_file_count": 0,
            "bom_size": total,
            "mpn_coverage_percent": round(mpn_pct, 1),
            "recommendation": (
                "Run datasheet sync via the digikey / mouser / lcsc / "
                "element14 skill (which one depends on the user's "
                "distributor access and API credentials). A ./datasheets/ "
                "directory with PDFs and a manifest.json enables pin-level "
                "verification in the next analyzer run."),
            "report_context": {
                "section": "Datasheet Coverage",
                "impact": ("Review claims must stay at consistency level "
                           "until datasheets land."),
                "standard_ref": "",
            },
        })
    return findings


def audit_sourcing_fields(components: list[dict]) -> dict:
    """Audit component sourcing completeness: MPN, distributor part numbers.

    For manufacturing readiness, every BOM component needs at minimum an MPN.
    Distributor PNs (DigiKey, Mouser, LCSC) accelerate ordering.
    """
    real = [c for c in components
            if c["type"] not in ("power_symbol", "power_flag", "flag", "test_point",
                                  "mounting_hole", "fiducial", "graphic")
            and c["in_bom"] and not c["dnp"]]

    # Deduplicate by reference (multi-unit symbols)
    seen = set()
    unique = []
    for c in real:
        if c["reference"] not in seen:
            seen.add(c["reference"])
            unique.append(c)

    missing_mpn = [c["reference"] for c in unique if not c.get("mpn")]
    missing_digikey = [c["reference"] for c in unique if not c.get("digikey")]
    missing_mouser = [c["reference"] for c in unique if not c.get("mouser")]
    missing_lcsc = [c["reference"] for c in unique if not c.get("lcsc")]

    total = len(unique)
    result = {
        "total_bom_components": total,
        "mpn_coverage": f"{total - len(missing_mpn)}/{total}",
    }
    if missing_mpn:
        result["missing_mpn"] = sorted(missing_mpn)
    if missing_digikey:
        result["missing_digikey"] = sorted(missing_digikey)
    if missing_lcsc:
        result["missing_lcsc"] = sorted(missing_lcsc)

    # Compute readiness score
    if total > 0:
        mpn_pct = (total - len(missing_mpn)) / total * 100
        result["mpn_percent"] = round(mpn_pct, 1)
    return result


def audit_sourcing_gate(components: list[dict]) -> list[dict]:
    """Emit rich findings that gate fabrication on BOM completeness.

    `audit_sourcing_fields()` returns a numeric summary; this surfaces
    the gap as findings so the stage filter and severity rollups see
    it. Rule tiers:
      SS-001  mpn_percent < 50        severity=high   (pre-fab blocker)
      SS-002  50 <= mpn_percent < 80  severity=warning
      SS-003  80 <= mpn_percent < 100 severity=info
    mpn_percent == 100 emits nothing.
    """
    findings: list[dict] = []
    real = [c for c in components
            if c.get("type") not in ("power_symbol", "power_flag", "flag",
                                     "test_point", "mounting_hole",
                                     "fiducial", "graphic")
            and c.get("in_bom") and not c.get("dnp")]
    if not real:
        return findings

    # Group by BOM line (value + footprint).  A BOM line has coverage if any
    # instance carries an MPN — the user can propagate it to siblings.
    # Counting references instead inflates the denominator: a single generic
    # 10 K resistor shared across 5 refs would register as 5 misses.
    bom_lines: dict[tuple, dict] = {}
    for c in real:
        key = (c.get("value", ""), c.get("footprint", ""))
        line = bom_lines.setdefault(key, {"refs": [], "has_mpn": False})
        r = c.get("reference", "")
        if r:
            line["refs"].append(r)
        if c.get("mpn"):
            line["has_mpn"] = True

    total = len(bom_lines)
    if total == 0:
        return findings
    missing_lines = [line for line in bom_lines.values()
                     if not line["has_mpn"]]
    # Collect refs from missing lines for the description, sorted naturally.
    missing = sorted({r for line in missing_lines for r in line["refs"]})
    covered = total - len(missing_lines)
    pct = covered / total * 100.0

    if pct >= 100.0:
        return findings
    if pct < 50.0:
        rid, sev = "SS-001", "error"
        headline = ("Sourcing blocker: BOM has <50% MPN coverage "
                    f"({covered}/{total} unique parts). Board is not pre-fab ready.")
    elif pct < 80.0:
        rid, sev = "SS-002", "warning"
        headline = (f"Sourcing gap: {covered}/{total} unique BOM parts have an MPN "
                    f"({pct:.0f}%). Populate before fab.")
    else:
        rid, sev = "SS-003", "info"
        headline = (f"Sourcing nearly complete: {covered}/{total} unique parts "
                    f"have MPNs ({pct:.0f}%). Fill in remaining lines.")

    findings.append({
        "detector": "audit_sourcing_gate",
        "rule_id": rid,
        "severity": sev,
        "confidence": "deterministic",
        "evidence_source": "bom",
        "category": "sourcing",
        "summary": headline,
        "description": (f"Sourcing audit: {covered} of {total} unique BOM "
                        f"lines (grouped by value + footprint) carry a "
                        f"manufacturer part number ({pct:.1f}%). Pre-fab "
                        f"readiness requires 100% coverage; production "
                        f"assembly requires all parts sourceable via one of "
                        f"the supported distributors."),
        "components": missing[:50],
        "nets": [],
        "pins": [],
        "mpn_coverage_percent": round(pct, 1),
        "missing_mpn_lines": len(missing_lines),
        "missing_mpn_refs": len(missing),
        "total_bom_lines": total,
        "recommendation": (
            "Populate the MPN field on the listed refs (use the digikey / "
            "mouser / lcsc / element14 skill to search by value/footprint "
            "when the MPN isn't already known)."),
        "report_context": {
            "section": "Sourcing",
            "impact": ("Pre-fab gate: board cannot be ordered until MPN "
                       "coverage reaches 100%."),
            "standard_ref": "",
        },
    })
    return findings


# Generic transistor symbol prefixes that encode assumed pin order
_GENERIC_TRANSISTOR_PREFIXES = ("Q_NPN_", "Q_PNP_", "Q_NMOS_", "Q_PMOS_")

# Map prefix to human-readable type
_GENERIC_TYPE_LABELS = {
    "Q_NPN_": "NPN",
    "Q_PNP_": "PNP",
    "Q_NMOS_": "NMOS",
    "Q_PMOS_": "PMOS",
}

# Map single-letter pin abbreviations to full names
_PIN_LETTER_NAMES = {
    "B": "Base", "C": "Collector", "E": "Emitter",
    "G": "Gate", "S": "Source", "D": "Drain",
}


def check_generic_transistor_symbols(components: list[dict],
                                     schematic_path: str = "") -> list[dict]:
    """Flag transistors using generic KiCad symbols instead of device-specific ones.

    Generic symbols (Q_NPN_BCE, Q_NMOS_GSD, etc.) encode an assumed pin order
    that may not match the actual part. SOT-23 pin mapping varies by manufacturer:
    BCE vs BEC vs CBE for BJTs, GSD vs GDS vs SGD for MOSFETs. Using a generic
    symbol with the wrong pin order produces a board that silently doesn't work.

    Device-specific symbols (MMBT3904, AO3400A) encode the correct pinout for
    that particular part and are always safer.

    If a datasheets/manifest.json (or legacy index.json) exists next to the schematic, the check also notes
    whether a datasheet is available for manual pinout verification.
    """
    warnings = []

    # Load datasheet manifest if available (prefer new manifest.json, fall
    # back to legacy index.json for projects that haven't been migrated).
    ds_index: dict[str, dict] = {}
    if schematic_path:
        sch_dir = Path(schematic_path).parent
        ds_dir = sch_dir / "datasheets"
        idx_path = ds_dir / "manifest.json"
        if not idx_path.is_file():
            idx_path = ds_dir / "index.json"
        if idx_path.is_file():
            try:
                ds_index = json.loads(idx_path.read_text())
            except (json.JSONDecodeError, OSError):
                pass

    # Deduplicate by reference (multi-unit symbols)
    seen: set[str] = set()

    for c in components:
        if c["type"] != "transistor":
            continue
        ref = c["reference"]
        if ref in seen:
            continue
        seen.add(ref)

        lib_id = c.get("lib_id", "")
        # Extract symbol name (part after the colon)
        sym_name = lib_id.split(":")[-1] if ":" in lib_id else lib_id

        # Check if this is a generic transistor symbol
        matched_prefix = None
        for prefix in _GENERIC_TRANSISTOR_PREFIXES:
            if sym_name.startswith(prefix):
                matched_prefix = prefix
                break

        if matched_prefix is None:
            continue

        # Extract pin order suffix (e.g., "GSD" from "Q_NMOS_GSD")
        pin_suffix = sym_name[len(matched_prefix):]
        sym_type = _GENERIC_TYPE_LABELS.get(matched_prefix, "transistor")

        # Expand pin abbreviations for the message
        pin_names = "-".join(
            _PIN_LETTER_NAMES.get(ch, ch) for ch in pin_suffix
        ) if pin_suffix else pin_suffix

        mpn = c.get("mpn", "")
        value = c.get("value", "")
        footprint = c.get("footprint", "")
        fp_name = footprint.split(":")[-1] if ":" in footprint else footprint

        # Check datasheet availability by MPN
        has_datasheet = False
        if mpn and ds_index:
            # index.json keys may be MPN strings or nested under "components"
            if isinstance(ds_index, dict):
                if mpn in ds_index:
                    has_datasheet = True
                elif "components" in ds_index:
                    comps = ds_index["components"]
                    if isinstance(comps, dict) and mpn in comps:
                        has_datasheet = True
                    elif isinstance(comps, list):
                        has_datasheet = any(
                            e.get("mpn") == mpn for e in comps
                            if isinstance(e, dict)
                        )

        # Build human-readable part identifier
        part_id = mpn or value or "unknown part"

        # Build message
        if has_datasheet:
            action = f"Verify pinout against the {part_id} datasheet (available in datasheets/) or switch to a device-specific symbol."
        elif mpn:
            action = f"Verify pinout against the {part_id} datasheet or switch to a device-specific symbol."
        else:
            action = "Add an MPN and verify pinout against the datasheet, or switch to a device-specific symbol."

        msg = (
            f"{ref}: Generic {sym_type} symbol ({sym_name}) used"
            f"{' for ' + part_id if part_id != 'unknown part' else ''}"
            f"{' in ' + fp_name if fp_name else ''}."
            f" Pin order ({pin_names}) may not match the actual part."
            f" {action}"
        )

        warnings.append({
            "component": ref,
            "lib_id": lib_id,
            "value": value,
            "mpn": mpn,
            "footprint": footprint,
            "symbol_pin_order": pin_suffix,
            "symbol_type": sym_type,
            "has_datasheet": has_datasheet,
            "severity": "warning",
            "message": msg,
        })

    return warnings


def summarize_alternate_pins(lib_symbols: dict) -> list[dict]:
    """Summarize symbols that have alternate pin definitions (dual-function pins).

    Alternate pins are common on MCUs where GPIO pins can serve as SPI/I2C/UART/PWM
    peripherals. This summary helps understand the pin multiplexing capabilities.
    """
    results = []
    for name, sym in lib_symbols.items():
        alts = sym.get("alternates")
        if not alts:
            continue

        pin_summary = []
        for pin_num, alt_list in sorted(alts.items()):
            # Find the primary pin name
            primary_name = ""
            for p in sym["pins"]:
                if p["number"] == pin_num:
                    primary_name = p["name"]
                    break
            pin_summary.append({
                "pin": pin_num,
                "primary": primary_name,
                "alternates": [a["name"] for a in alt_list],
            })

        results.append({
            "symbol": name,
            "pins_with_alternates": len(alts),
            "total_pins": len(sym["pins"]),
            "details": pin_summary,
        })

    return results


def classify_ground_domains(nets: dict, components: list[dict]) -> dict:
    """Classify ground nets into domains: signal, analog, digital, earth, chassis, power.

    Multiple ground domains in a design need careful management — star grounding,
    proper domain separation, and single-point connections between domains.
    """
    ground_nets = {}
    for net_name, net_info in nets.items():
        if not _is_ground_name(net_name):
            continue

        nu = net_name.upper()
        if any(x in nu for x in ("AGND", "GNDA", "VSS_A", "VSSA")):
            domain = "analog"
        elif any(x in nu for x in ("DGND", "GNDD", "VSS_D", "VSSD")):
            domain = "digital"
        elif any(x in nu for x in ("PGND", "GNDPWR", "VSS_P")):
            domain = "power"
        elif any(x in nu for x in ("EARTH", "PE", "FG", "CHASSIS", "SHIELD")):
            domain = "earth/chassis"
        else:
            domain = "signal"

        pin_count = len([p for p in net_info["pins"] if not p["component"].startswith("#")])
        connected_components = sorted(set(
            p["component"] for p in net_info["pins"] if not p["component"].startswith("#")
        ))
        ground_nets[net_name] = {
            "domain": domain,
            "connections": pin_count,
            "components": connected_components,
        }

    domains = {}
    for net_name, info in ground_nets.items():
        d = info["domain"]
        domains.setdefault(d, []).append(net_name)

    result = {"ground_nets": ground_nets}
    if len(domains) > 1:
        result["multiple_domains"] = True
        result["domains"] = domains
        result["note"] = "Multiple ground domains detected — verify proper star/single-point connection between domains"
    else:
        result["multiple_domains"] = False
    return result


def analyze_bus_topology(bus_elements: dict, labels: list[dict], nets: dict) -> dict:
    """Analyze bus structure: which signals are grouped, naming consistency, member coverage.

    Checks that bus aliases have corresponding labels for all members, and that
    bus naming follows consistent patterns (e.g., D[0..7] has labels D0..D7).
    """
    result = {
        "bus_wire_count": len(bus_elements.get("bus_wires", [])),
        "bus_entry_count": len(bus_elements.get("bus_entries", [])),
    }

    aliases = bus_elements.get("bus_aliases", [])
    if aliases:
        alias_info = []
        all_label_names = set(l["name"] for l in labels)
        for alias in aliases:
            members = alias["members"]
            present = [m for m in members if m in all_label_names]
            missing = [m for m in members if m not in all_label_names]
            # Check which member names resolve to actual nets
            resolved = [m for m in members if m in nets]
            entry = {
                "name": alias["name"],
                "member_count": len(members),
                "present_labels": len(present),
                "resolved_nets": len(resolved),
            }
            if missing:
                entry["missing_labels"] = missing
            unresolved = [m for m in members if m not in nets]
            if unresolved:
                entry["unresolved_members"] = unresolved
            alias_info.append(entry)
        result["aliases"] = alias_info

    # Detect bus-like label patterns (D0..D7, ADDR0..ADDR15, etc.)
    bus_patterns: dict[str, list[str]] = {}
    for lbl in labels:
        m = re.match(r'^([A-Za-z_]+)(\d+)$', lbl["name"])
        if m:
            prefix = m.group(1)
            bus_patterns.setdefault(prefix, []).append(lbl["name"])

    detected_buses = []
    for prefix, members in sorted(bus_patterns.items()):
        if len(members) >= 3:  # At least 3 signals to be bus-like
            nums = sorted(int(re.search(r'\d+$', m).group()) for m in members)
            expected = list(range(nums[0], nums[-1] + 1))
            missing_nums = [n for n in expected if n not in nums]
            entry = {
                "prefix": prefix,
                "width": len(members),
                "range": f"{prefix}{nums[0]}..{prefix}{nums[-1]}",
            }
            if missing_nums:
                entry["missing"] = [f"{prefix}{n}" for n in missing_nums]
            detected_buses.append(entry)

    if detected_buses:
        result["detected_bus_signals"] = detected_buses

    return result


def analyze_wire_geometry(wires: list[dict]) -> dict:
    """Analyze wire routing geometry for schematic cleanliness.

    Flags non-orthogonal wires (diagonal), very short wires (possible stubs),
    and computes overall wire statistics.
    """
    # EQ-064: L = √(Δx²+Δy²) (wire segment length)
    if not wires:
        return {"total_wires": 0}

    diagonal = []
    short_wires = []
    total_length = 0.0

    for w in wires:
        dx = abs(w["x2"] - w["x1"])
        dy = abs(w["y2"] - w["y1"])
        length = math.sqrt(dx * dx + dy * dy)
        total_length += length

        # Non-orthogonal: neither horizontal nor vertical (with tolerance)
        is_h = dy < 0.01
        is_v = dx < 0.01
        if not is_h and not is_v and length > 0.1:
            diagonal.append({
                "from": [round(w["x1"], 2), round(w["y1"], 2)],
                "to": [round(w["x2"], 2), round(w["y2"], 2)],
                "length": round(length, 2),
            })

        # Very short wires (< 1mm) — possible stubs or misclicks
        if 0 < length < 1.0:
            short_wires.append({
                "from": [round(w["x1"], 2), round(w["y1"], 2)],
                "to": [round(w["x2"], 2), round(w["y2"], 2)],
                "length": round(length, 3),
            })

    result = {
        "total_wires": len(wires),
        "total_length_mm": round(total_length, 1),
        "avg_length_mm": round(total_length / len(wires), 1) if wires else 0,
    }
    if diagonal:
        result["diagonal_wires"] = diagonal[:20]  # Cap output
        result["diagonal_count"] = len(diagonal)
    if short_wires:
        result["short_wires"] = short_wires[:20]
        result["short_wire_count"] = len(short_wires)
    return result


def check_simulation_readiness(components: list[dict], lib_symbols: dict) -> dict:
    """Check if components have SPICE simulation models assigned.

    KiCad's built-in NGSPICE simulator requires each component to have a
    simulation model (Sim.Type, Sim.Params, etc.) for the circuit to simulate.
    """
    real = [c for c in components
            if c["type"] not in ("power_symbol", "power_flag", "flag",
                                  "test_point", "mounting_hole", "fiducial", "graphic")]

    # Check for Sim_* properties which indicate SPICE model assignment
    # These are stored as component properties but we extracted only standard ones.
    # We can at least check lib_symbol descriptions for SPICE-related keywords.
    has_model_hint = []
    no_model = []

    for c in real:
        sym = lib_symbols.get(c["lib_id"], {})
        desc = (sym.get("description", "") + " " + sym.get("keywords", "")).lower()
        ctype = c["type"]

        # Passives (R, C, L) have built-in SPICE models
        if ctype in ("resistor", "capacitor", "inductor"):
            has_model_hint.append(c["reference"])
        elif "spice" in desc or "simulation" in desc or "sim_" in desc:
            has_model_hint.append(c["reference"])
        elif ctype in ("diode", "led", "transistor"):
            # Common discrete parts — may have models
            has_model_hint.append(c["reference"])
        else:
            no_model.append(c["reference"])

    total = len(real)
    modeled = len(has_model_hint)

    result = {
        "total_components": total,
        "likely_simulatable": modeled,
        "needs_model": len(no_model),
    }
    if no_model:
        result["components_without_model"] = sorted(set(no_model))[:30]
    if total > 0:
        result["simulatable_percent"] = round(modeled / total * 100, 1)
    return result


def audit_property_patterns(components: list[dict]) -> dict:
    """Audit property naming consistency across components.

    Checks that MPN, manufacturer, and distributor fields use consistent
    property names (e.g., not a mix of "MPN" vs "Mfg Part" vs "Part Number").
    Also checks for common data entry issues.
    """
    real = [c for c in components
            if c["type"] not in ("power_symbol", "power_flag", "flag")]

    issues = []

    # Check for value field anomalies
    for c in real:
        val = c.get("value", "")
        ref = c["reference"]

        # Reference designator accidentally used as value
        if val == ref:
            issues.append({
                "component": ref,
                "issue": "value_equals_reference",
                "message": f"{ref}: value is same as reference designator (likely placeholder)",
            })

        # Lib_id used as value (forgot to set value)
        if val and ":" in val and val == c.get("lib_id", ""):
            issues.append({
                "component": ref,
                "issue": "value_is_lib_id",
                "message": f"{ref}: value appears to be the library ID '{val}' (not a real value)",
            })

        # Footprint in the value field
        if val and ("_SMD:" in val or "_THT:" in val or "Resistor_SMD" in val):
            issues.append({
                "component": ref,
                "issue": "value_looks_like_footprint",
                "message": f"{ref}: value '{val}' looks like a footprint, not a component value",
            })

    # Check for MPN/value inconsistency within same BOM group
    # (same value + footprint should have same MPN)
    bom_groups: dict[tuple, list] = {}
    for c in real:
        if c["in_bom"] and not c["dnp"] and c.get("value"):
            key = (c["value"], c["footprint"])
            bom_groups.setdefault(key, []).append(c)

    for key, group in bom_groups.items():
        mpns = set(c["mpn"] for c in group if c["mpn"])
        if len(mpns) > 1:
            refs = sorted(c["reference"] for c in group)
            issues.append({
                "components": refs,
                "issue": "inconsistent_mpn",
                "message": f"Components with value '{key[0]}' / footprint '{key[1]}' have different MPNs: {sorted(mpns)}",
            })

    result = {}
    if issues:
        result["issues"] = issues
        result["issue_count"] = len(issues)
    return result


def spatial_clustering(components: list[dict]) -> dict:
    """Analyze component placement clustering to identify functional groups.

    Groups components by proximity to help identify subcircuit boundaries
    and check for spatial organization of the schematic.
    """
    real = [c for c in components
            if c["type"] not in ("power_symbol", "power_flag", "flag")]

    if not real:
        return {"clusters": []}

    # Simple grid-based clustering: divide the schematic into regions
    xs = [c["x"] for c in real]
    ys = [c["y"] for c in real]

    if not xs or not ys:
        return {"clusters": []}

    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    x_range = x_max - x_min or 1
    y_range = y_max - y_min or 1

    # Use quadrant-based grouping (4x4 grid)
    grid_cols = min(4, max(1, int(x_range / 40)))
    grid_rows = min(4, max(1, int(y_range / 30)))

    cell_w = x_range / grid_cols if grid_cols > 1 else x_range + 1
    cell_h = y_range / grid_rows if grid_rows > 1 else y_range + 1

    grid: dict[tuple, list] = {}
    for c in real:
        col = min(int((c["x"] - x_min) / cell_w), grid_cols - 1)
        row = min(int((c["y"] - y_min) / cell_h), grid_rows - 1)
        grid.setdefault((row, col), []).append(c)

    clusters = []
    for (row, col), members in sorted(grid.items()):
        type_counts: dict[str, int] = {}
        for c in members:
            type_counts[c["type"]] = type_counts.get(c["type"], 0) + 1

        refs = sorted(c["reference"] for c in members)
        clusters.append({
            "region": f"row{row}_col{col}",
            "component_count": len(members),
            "types": type_counts,
            "references": refs if len(refs) <= 20 else refs[:20] + [f"... +{len(refs)-20} more"],
        })

    # Component density and spread statistics
    result = {
        "bounding_box": {
            "x_min": round(x_min, 1), "y_min": round(y_min, 1),
            "x_max": round(x_max, 1), "y_max": round(y_max, 1),
            "width_mm": round(x_range, 1), "height_mm": round(y_range, 1),
        },
        "clusters": clusters,
        "grid_size": f"{grid_rows}x{grid_cols}",
    }
    return result


def verify_pin_coverage(components: list[dict], lib_symbols: dict) -> list[dict]:
    """Verify that all non-NC library pins are accounted for on placed symbols.

    Checks if a placed symbol has fewer pins connected than the library definition
    expects, which could indicate missing connections or wrong unit placement.
    """
    warnings = []

    # Group components by reference (multi-unit symbols)
    ref_components: dict[str, list[dict]] = {}
    for c in components:
        if c["type"] in ("power_symbol", "power_flag", "flag"):
            continue
        ref_components.setdefault(c["reference"], []).append(c)

    for ref, comp_list in ref_components.items():
        c = comp_list[0]  # Use first instance for lib_id lookup
        sym_def = lib_symbols.get(c["lib_id"])
        if not sym_def:
            continue

        lib_pins = sym_def["pins"]
        if not lib_pins:
            continue

        # Count placed pins across all units
        placed_pin_nums = set()
        for comp in comp_list:
            for pin in comp.get("pins", []):
                placed_pin_nums.add(pin.get("number", ""))

        # Count expected pins from library (excluding no-connect type pins)
        expected_pins = set()
        for p in lib_pins:
            if p["type"] != "no_connect":
                expected_pins.add(p["number"])

        missing = expected_pins - placed_pin_nums
        if missing and len(missing) > len(expected_pins) * 0.3:
            # More than 30% of pins missing — likely a real issue
            warnings.append({
                "component": ref,
                "lib_id": c["lib_id"],
                "expected_pins": len(expected_pins),
                "placed_pins": len(placed_pin_nums),
                "missing_count": len(missing),
                "message": f"{ref}: {len(missing)}/{len(expected_pins)} library pins not placed (may need more units or check symbol)",
            })

    return warnings


def check_instance_consistency(components: list[dict]) -> list[dict]:
    """Check multi-unit and multi-instance symbol consistency.

    For multi-unit symbols (e.g., quad op-amp), verify all expected units are placed.
    For multi-instance sheets, verify reference numbering doesn't collide.
    """
    warnings = []

    # Group by lib_id to find multi-unit symbols
    lib_groups: dict[str, list[dict]] = {}
    for c in components:
        if c["type"] in ("power_symbol", "power_flag", "flag"):
            continue
        lib_groups.setdefault(c["lib_id"], []).append(c)

    # Check for partial unit placement
    for lib_id, comp_list in lib_groups.items():
        # Group by reference
        ref_units: dict[str, set[int]] = {}
        for c in comp_list:
            if c["unit"] is not None:
                ref_units.setdefault(c["reference"], set()).add(c["unit"])

        for ref, units in ref_units.items():
            if not units:
                continue
            max_unit = max(units)
            expected = set(range(1, max_unit + 1))
            missing = expected - units
            if missing:
                warnings.append({
                    "component": ref,
                    "lib_id": lib_id,
                    "placed_units": sorted(units),
                    "missing_units": sorted(missing),
                    "message": f"{ref}: units {sorted(missing)} not placed (of {max_unit} total)",
                })

    # Check for reference collisions across sheets
    ref_sheets: dict[str, set] = {}
    for c in components:
        if c["type"] in ("power_symbol", "power_flag", "flag"):
            continue
        sheet = c.get("_sheet", 0)
        ref_sheets.setdefault(c["reference"], set()).add(sheet)

    for ref, sheets in ref_sheets.items():
        if len(sheets) > 1:
            # Same reference on different sheets with different UUIDs
            instances = [c for c in components if c["reference"] == ref]
            uuids = set(c["uuid"] for c in instances)
            units = set(c["unit"] for c in instances if c["unit"] is not None)
            # Multi-unit on different sheets is OK (unit != None and different units)
            if len(uuids) > len(units) and len(units) > 0:
                pass  # Multi-unit, different units — fine
            elif len(uuids) > 1 and not units:
                warnings.append({
                    "component": ref,
                    "sheets": sorted(sheets),
                    "message": f"{ref}: appears on {len(sheets)} sheets with different UUIDs (reference collision?)",
                })

    return warnings


def validate_hierarchical_labels(labels: list[dict], nets: dict) -> dict:
    """Validate hierarchical label usage for cross-sheet connectivity.

    Checks for orphaned hierarchical labels (no matching sheet pin), hierarchical
    labels that don't connect to any net, and naming consistency.
    """
    hier_labels = [l for l in labels if l["type"] == "hierarchical_label"]
    global_labels = [l for l in labels if l["type"] == "global_label"]

    result = {
        "hierarchical_label_count": len(hier_labels),
        "global_label_count": len(global_labels),
    }

    # Check for hierarchical labels that don't appear in any net
    hier_names = set(l["name"] for l in hier_labels)
    global_names = set(l["name"] for l in global_labels)
    net_names = set(nets.keys())

    unconnected_hier = sorted(hier_names - net_names)
    if unconnected_hier:
        result["unconnected_hierarchical"] = unconnected_hier

    # Check for naming conflicts between global and hierarchical labels
    conflicts = sorted(hier_names & global_names)
    if conflicts:
        result["global_hier_name_conflicts"] = conflicts
        result["conflict_warning"] = "Same name used as both global and hierarchical label — may cause unexpected connections"

    # Group global labels by name and check for single-instance labels
    # (a global label used only once is suspicious — it should connect to something)
    global_name_counts: dict[str, int] = {}
    for l in global_labels:
        global_name_counts[l["name"]] = global_name_counts.get(l["name"], 0) + 1

    single_use = sorted(n for n, c in global_name_counts.items() if c == 1)
    if single_use:
        result["single_use_global_labels"] = single_use

    return result


# ---------------------------------------------------------------------------
# Tier 3: High-level design analysis functions
# ---------------------------------------------------------------------------


def analyze_pdn_impedance(ctx: AnalysisContext, signal_analysis: dict | None = None) -> dict:
    """PDN impedance profiling per power rail.

    Groups all capacitors by power rail, estimates ESR/ESL from package size,
    computes combined impedance at frequency points (1 kHz to 1 GHz), and flags
    frequency gaps and anti-resonances.
    """
    components = ctx.components
    nets = ctx.nets
    pin_net = ctx.pin_net
    comp_lookup = ctx.comp_lookup
    ref_pins = ctx.ref_pins
    is_power_net = ctx.is_power_net
    is_ground = ctx.is_ground
    # EQ-062: |Z| = √(ESR²+(ωL-1/ωC)²) swept over frequency
    # Package-dependent parasitics
    # Typical MLCC parasitics — aligned with emc_formulas.py values
    esl_by_pkg = {
        "0201": 0.3e-9, "0402": 0.5e-9, "0603": 0.7e-9,
        "0805": 0.9e-9, "1206": 1.1e-9, "1210": 1.2e-9,
        "1812": 1.5e-9, "2220": 1.8e-9,
    }
    # ESR for X5R/X7R at 1 MHz — aligned with emc_formulas.py values
    esr_base_by_pkg = {
        "0201": 0.5, "0402": 0.3, "0603": 0.1,
        "0805": 0.05, "1206": 0.03, "1210": 0.02,
        "1812": 0.02, "2220": 0.015,
    }

    def _extract_package_code(footprint: str) -> str | None:
        if not footprint:
            return None
        # Match common patterns like C_0402_1005Metric, R_0805_...
        m = re.search(r'(\d{4})_\d{4}Metric', footprint)
        if m:
            return m.group(1)
        # Direct 4-digit codes
        m = re.search(r'\b(0201|0402|0603|0805|1206|1210|1812|2220)\b', footprint)
        if m:
            return m.group(1)
        return None

    def _is_electrolytic_or_tantalum(comp: dict) -> bool:
        fp = comp.get("footprint", "").lower()
        val = comp.get("value", "").lower()
        lib = comp.get("lib_id", "").lower()
        combined = fp + " " + val + " " + lib
        if any(k in combined for k in ("electrolytic", "tantalum", "cp_", "c_radial", "c_axial")):
            return True
        # Large THT caps or large values without SMD footprint
        if "tht" in fp or "radial" in fp or "axial" in fp:
            return True
        return False

    def _cap_impedance(f: float, c_farads: float, esr: float, esl: float) -> float:
        # EQ-061: |Z| = √(ESR²+(2πfL-1/(2πfC))²) at given frequency
        x_c = 1.0 / (2.0 * math.pi * f * c_farads) if c_farads > 0 else 1e12
        x_l = 2.0 * math.pi * f * esl
        return math.sqrt(esr ** 2 + (x_l - x_c) ** 2)

    # Build power rail -> caps mapping
    rail_caps: dict[str, list[dict]] = {}
    for net_name, net_info in nets.items():
        if net_name.startswith("__unnamed_"):
            continue
        if is_ground(net_name):
            continue
        if not is_power_net(net_name):
            continue

        for p in net_info["pins"]:
            comp = comp_lookup.get(p["component"])
            if not comp or comp["type"] != "capacitor":
                continue
            # KH-196: Use pre-computed parsed_values (has component_type context)
            cap_val = ctx.parsed_values.get(comp["reference"])
            if not cap_val or cap_val <= 0:
                continue
            # Check other pin goes to ground
            n1, _ = pin_net.get((p["component"], "1"), (None, None))
            n2, _ = pin_net.get((p["component"], "2"), (None, None))
            other = n2 if n1 == net_name else n1
            if not is_ground(other):
                continue

            pkg = _extract_package_code(comp.get("footprint", ""))
            is_elec = _is_electrolytic_or_tantalum(comp)
            if is_elec:
                esr = max(0.1, 0.5 / math.sqrt(cap_val * 1e6)) if cap_val > 0 else 0.5
                esl = 7.5e-9  # typical 5-10 nH
            elif pkg and pkg in esl_by_pkg:
                esl = esl_by_pkg[pkg]
                base_esr = esr_base_by_pkg.get(pkg, 0.015)
                # ESR scales roughly with 1/sqrt(C in uF), clamped
                c_uf = cap_val * 1e6
                esr = max(0.005, base_esr / math.sqrt(max(c_uf, 0.001)))
            else:
                # Unknown package — assume 0603 MLCC defaults
                esl = 0.5e-9
                c_uf = cap_val * 1e6
                esr = max(0.005, 0.012 / math.sqrt(max(c_uf, 0.001)))

            srf = 1.0 / (2.0 * math.pi * math.sqrt(esl * cap_val)) if esl > 0 and cap_val > 0 else 0

            cap_entry = {
                "ref": p["component"],
                "value": comp["value"],
                "farads": cap_val,
                "package": pkg,
                "esr_ohm": round(esr, 4),
                "esl_nH": round(esl * 1e9, 2),
                "srf_hz": round(srf),
                "srf_formatted": _format_frequency(srf) if srf > 0 else "N/A",
            }
            cap_entry["type"] = "electrolytic/tantalum" if is_elec else "MLCC"

            rail_caps.setdefault(net_name, []).append(cap_entry)

    if not rail_caps:
        return {}

    # Frequency sweep points: 1 kHz to 1 GHz, 10 points per decade
    freq_points = []
    f = 1e3
    while f <= 1.01e9:
        freq_points.append(f)
        f *= 10 ** 0.1  # 10 points per decade

    rails_result = {}
    observations = []

    for rail_name, caps in rail_caps.items():
        # Find VRM driving this rail (from signal_analysis)
        vrm_r_out = None
        vrm_bw = None
        if signal_analysis:
            for reg in signal_analysis.get("power_regulators", []):
                out_rail = reg.get("output_rail", "")
                if out_rail == rail_name:
                    topo = (reg.get("topology") or "").lower()
                    if topo in ("ldo", "linear"):
                        vrm_r_out = 0.05   # 50mΩ typical LDO output impedance
                        vrm_bw = 100e3     # 100kHz LDO bandwidth
                    else:
                        vrm_r_out = 0.1    # 100mΩ typical switching reg output impedance
                        vrm_bw = 50e3      # 50kHz switching reg bandwidth
                    break

        # Compute combined impedance at each frequency point
        impedance_profile = []
        for f in freq_points:
            z_parallel_inv = 0.0
            for cap in caps:
                z_i = _cap_impedance(f, cap["farads"], cap["esr_ohm"], cap["esl_nH"] * 1e-9)
                if z_i > 0:
                    z_parallel_inv += 1.0 / z_i
            z_total = 1.0 / z_parallel_inv if z_parallel_inv > 0 else 1e12
            if vrm_r_out is not None:
                # VRM output impedance: flat R_out below BW, rising at +20dB/decade above
                z_vrm = vrm_r_out * max(1.0, f / vrm_bw)
                z_total = 1.0 / (1.0 / z_total + 1.0 / z_vrm) if z_total < 1e12 else z_vrm
            impedance_profile.append({
                "freq_hz": round(f),
                "freq_formatted": _format_frequency(f),
                "impedance_ohm": round(z_total, 6),
            })

        # Find anti-resonance peaks (local maxima in impedance)
        anti_resonances = []
        for i in range(1, len(impedance_profile) - 1):
            z_prev = impedance_profile[i - 1]["impedance_ohm"]
            z_curr = impedance_profile[i]["impedance_ohm"]
            z_next = impedance_profile[i + 1]["impedance_ohm"]
            if z_curr > z_prev and z_curr > z_next:
                anti_resonances.append({
                    "freq_formatted": impedance_profile[i]["freq_formatted"],
                    "freq_hz": impedance_profile[i]["freq_hz"],
                    "impedance_ohm": z_curr,
                })

        # Find min impedance
        min_z = min(impedance_profile, key=lambda x: x["impedance_ohm"])

        rail_result = {
            "capacitors": caps,
            "cap_count": len(caps),
            "total_capacitance_uF": round(sum(c["farads"] for c in caps) * 1e6, 3),
            "impedance_profile": impedance_profile,
            "min_impedance": {
                "freq_formatted": min_z["freq_formatted"],
                "impedance_ohm": min_z["impedance_ohm"],
            },
        }
        if anti_resonances:
            rail_result["anti_resonances"] = anti_resonances
            for ar in anti_resonances:
                if ar["impedance_ohm"] > 1.0:
                    observations.append(
                        f"{rail_name}: anti-resonance at {ar['freq_formatted']} "
                        f"({ar['impedance_ohm']:.3f} ohm) — consider adding cap with SRF near this frequency"
                    )

        # Check for frequency gaps: if all cap SRFs are below 100 MHz,
        # high-frequency decoupling may be lacking
        max_srf = max((c["srf_hz"] for c in caps), default=0)
        if max_srf < 100e6 and len(caps) > 0:
            observations.append(
                f"{rail_name}: highest SRF is {_format_frequency(max_srf)} — "
                f"consider adding small (100pF-1nF) MLCC for >100 MHz coverage"
            )

        rails_result[rail_name] = rail_result

    result = {"rails": rails_result}
    if observations:
        result["observations"] = observations
    return result


def analyze_sleep_current(ctx: AnalysisContext,
                          signal_analysis: dict | None = None) -> dict:
    """Sleep/quiescent current audit.

    Finds all always-on current paths: resistive dividers between power and
    ground, pull-up/pull-down resistors to power rails, LED indicators, and
    regulator quiescent currents (estimated from part family).
    """
    components = ctx.components
    nets = ctx.nets
    pin_net = ctx.pin_net
    comp_lookup = ctx.comp_lookup
    ref_pins = ctx.ref_pins
    is_power_net = ctx.is_power_net
    is_ground = ctx.is_ground
    rail_currents: dict[str, list[dict]] = {}
    _get_two_pin_nets = ctx.get_two_pin_nets

    # --- Resistors between power and ground ---
    _seen_refs = set()
    for comp in components:
        if comp["type"] != "resistor":
            continue
        ref = comp["reference"]
        if ref in _seen_refs:
            continue
        _seen_refs.add(ref)
        r_val = parse_value(comp.get("value", ""))
        if not r_val or r_val <= 0:
            continue
        n1, n2 = _get_two_pin_nets(ref)
        if not n1 or not n2:
            continue

        pwr_net = None
        gnd_net = None
        if is_power_net(n1) and not is_ground(n1) and is_ground(n2):
            pwr_net, gnd_net = n1, n2
        elif is_power_net(n2) and not is_ground(n2) and is_ground(n1):
            pwr_net, gnd_net = n2, n1

        if pwr_net and gnd_net:
            v_rail = _estimate_rail_voltage(pwr_net)
            if v_rail and v_rail > 0:
                current_a = v_rail / r_val
                entry = {
                    "ref": ref,
                    "value": comp["value"],
                    "type": "resistor_to_gnd",
                    "resistance_ohm": r_val,
                    "rail_voltage": v_rail,
                    "current_uA": round(current_a * 1e6, 2),
                }
                # Check if this is part of a voltage divider (second resistor on the non-gnd side)
                if pwr_net in nets:
                    other_resistors = [
                        p["component"] for p in nets[pwr_net]["pins"]
                        if p["component"] != ref
                        and comp_lookup.get(p["component"], {}).get("type") == "resistor"
                    ]
                    if other_resistors:
                        entry["note"] = f"part of divider with {', '.join(other_resistors)}"
                rail_currents.setdefault(pwr_net, []).append(entry)
            continue

        # Pull-up resistor: one side to power rail, other side to a signal net
        if is_power_net(n1) and not is_ground(n1) and not is_power_net(n2):
            pwr_net = n1
        elif is_power_net(n2) and not is_ground(n2) and not is_power_net(n1):
            pwr_net = n2
        else:
            continue

        v_rail = _estimate_rail_voltage(pwr_net)
        if v_rail and v_rail > 0:
            # Pull-up: worst case current is V/R (pin driven low)
            current_a = v_rail / r_val
            rail_currents.setdefault(pwr_net, []).append({
                "ref": ref,
                "value": comp["value"],
                "type": "pull_up",
                "resistance_ohm": r_val,
                "rail_voltage": v_rail,
                "current_uA": round(current_a * 1e6, 2),
                "note": "worst-case (signal driven low)",
            })

    # --- LEDs with series resistors ---
    _seen_led_refs = set()
    for comp in components:
        if comp["type"] != "led":
            continue
        ref = comp["reference"]
        if ref in _seen_led_refs:
            continue
        _seen_led_refs.add(ref)
        # Find nets connected to LED pins
        led_nets = [net for net, _ in ref_pins.get(ref, {}).values()]

        for net_name in led_nets:
            if not net_name or net_name not in nets:
                continue
            # Find series resistor on same net
            for p in nets[net_name]["pins"]:
                if p["component"] == ref:
                    continue
                r_comp = comp_lookup.get(p["component"])
                if not r_comp or r_comp["type"] != "resistor":
                    continue
                r_val = parse_value(r_comp.get("value", ""))
                if not r_val or r_val <= 0:
                    continue
                # Find what power rail this LED circuit connects to
                r_n1, r_n2 = _get_two_pin_nets(r_comp["reference"])
                for rn in (r_n1, r_n2):
                    if rn and rn != net_name and is_power_net(rn) and not is_ground(rn):
                        v_rail = _estimate_rail_voltage(rn)
                        if v_rail and v_rail > 0:
                            # LED forward voltage ~2V typical
                            v_led = 2.0
                            if v_rail > v_led:
                                current_a = (v_rail - v_led) / r_val
                                rail_currents.setdefault(rn, []).append({
                                    "ref": ref,
                                    "value": comp.get("value", "LED"),
                                    "type": "led_indicator",
                                    "series_resistor": r_comp["reference"],
                                    "resistance_ohm": r_val,
                                    "rail_voltage": v_rail,
                                    "current_uA": round(current_a * 1e6, 2),
                                    "note": "assuming ~2V forward drop, always-on if no switch",
                                })

    # KH-239: Drop pull_up entries that are actually LED current-limit
    # resistors. The LED loop above already emitted led_indicator entries
    # with series_resistor pointing at these refs, and the LED arithmetic
    # (V_rail - V_f)/R is the correct one. The pull_up branch's V_rail/R
    # arithmetic over-states the current by ~50% per LED. Symmetric with
    # the detection criterion: drop any ref that appears as BOTH a
    # pull_up entry AND an led_indicator's series_resistor on the same
    # rail.
    for _rail_name, _entries in rail_currents.items():
        _led_series = {e.get("series_resistor") for e in _entries
                       if e.get("type") == "led_indicator" and e.get("series_resistor")}
        if _led_series:
            rail_currents[_rail_name] = [
                e for e in _entries
                if not (e.get("type") == "pull_up" and e.get("ref") in _led_series)
            ]

    # --- Regulator quiescent current estimates ---
    # Use detected regulators from signal analysis to estimate Iq per output rail.
    # These are rough estimates based on part family — actual values depend on
    # load current, switching frequency, and mode (PFM vs PWM).
    _iq_estimates_uA: dict[str, float] = {
        # Part prefix → typical Iq in uA (from datasheets, sleep/shutdown mode)
        "TPS6": 15,      # TPS61xxx/62xxx — ~15-25 uA typical
        "TPS5": 100,     # TPS54xxx — ~100-300 uA typical (not ultra-low-power)
        "LMR51": 24,     # LMR514xx — 24 uA typical
        "LMR33": 25,     # LMR336xx — 24-30 uA
        "RT5": 20,       # Richtek RT56xx — ~20-40 uA
        "AP2112": 55,    # Diodes AP2112 LDO — 55 uA
        "AP6": 20,       # Diodes AP6xxx — ~20 uA
        "MIC29": 500,    # Microchip MIC29xxx — ~500 uA (older LDO)
        "MIC55": 100,    # Microchip MIC55xx — ~100 uA
        "LM317": 5000,   # LM317 — ~5 mA Iq
        "AMS1117": 5000, # AMS1117 — ~5 mA Iq
        "LD1117": 5000,  # LD1117 — ~5 mA Iq
        "XC6": 1,        # Torex XC6xxx — ~0.5-8 uA (ultra low power)
        "TLV71": 3.4,    # TI TLV713/715 — ~3.4 uA
        "TLV75": 18,     # TI TLV757 — ~18 uA
        "NCP1": 50,      # ON Semi NCP1xxx — ~50 uA
    }
    if signal_analysis:
        for reg in signal_analysis.get("power_regulators", []):
            out_rail = reg.get("output_rail", "")
            if not out_rail:
                continue
            # Look up Iq by part prefix
            reg_value = reg.get("value", "").upper()
            reg_lib = reg.get("lib_id", "").split(":")[-1].upper() if ":" in reg.get("lib_id", "") else ""
            iq_ua = None
            for prefix, iq in _iq_estimates_uA.items():
                if reg_value.startswith(prefix.upper()) or reg_lib.startswith(prefix.upper()):
                    iq_ua = iq
                    break
            if iq_ua is None:
                # Default estimate based on topology
                topo = reg.get("topology", "")
                if topo == "LDO":
                    iq_ua = 100  # generic LDO
                elif topo == "switching":
                    iq_ua = 50  # generic switcher
                else:
                    continue

            # Check if regulator has an EN pin that could disable it
            has_en = False
            for comp in components:
                if comp["reference"] == reg["ref"]:
                    for pin in comp.get("pins", []):
                        pn_upper = pin.get("name", "").upper()
                        if pn_upper in ("EN", "ENABLE", "ON/OFF", "ON", "SHDN", "CE"):
                            has_en = True
                            break
                    break

            rail_currents.setdefault(out_rail, []).append({
                "ref": reg["ref"],
                "value": reg.get("value", ""),
                "type": "regulator_iq",
                "current_uA": round(iq_ua, 2),
                "has_enable_pin": has_en,
                "note": f"estimated Iq ({'can be disabled via EN' if has_en else 'always-on, no EN pin detected'})",
            })

    if not rail_currents:
        return {}

    # Build set of disableable rails (output of regulators with EN pins)
    _disableable_rails: set[str] = set()
    if signal_analysis:
        for reg in signal_analysis.get("power_regulators", []):
            out_rail = reg.get("output_rail", "")
            if not out_rail:
                continue
            for comp in components:
                if comp["reference"] == reg.get("ref", ""):
                    for pin in comp.get("pins", []):
                        if pin.get("name", "").upper() in (
                                "EN", "ENABLE", "ON/OFF", "ON", "SHDN", "CE"):
                            _disableable_rails.add(out_rail)
                    break

    # Add realistic state estimation to each entry
    for rail, entries in rail_currents.items():
        for e in entries:
            etype = e["type"]
            if etype == "pull_up":
                # Check if signal net connects to a pin powered by the same
                # rail (both ends at rail voltage → ~0µA)
                e["likely_state"] = "worst-case (signal driven low)"
                e["realistic_uA"] = e["current_uA"]
            elif etype == "led_indicator":
                # LEDs are typically GPIO-controlled
                e["likely_state"] = "GPIO off during sleep"
                e["realistic_uA"] = 0.0
            elif etype == "regulator_iq":
                if e.get("has_enable_pin"):
                    e["likely_state"] = "can be disabled via EN"
                    e["realistic_uA"] = 0.0
                else:
                    e["likely_state"] = "always-on"
                    e["realistic_uA"] = e["current_uA"]
            elif etype == "resistor_to_gnd":
                if rail in _disableable_rails:
                    e["likely_state"] = "rail disabled during sleep"
                    e["realistic_uA"] = 0.0
                else:
                    e["likely_state"] = "always conducting"
                    e["realistic_uA"] = e["current_uA"]

    # Summarize per rail — split always-on vs conditional (pull-ups)
    result_rails = {}
    always_on_uA = 0.0
    conditional_uA = 0.0
    realistic_uA = 0.0
    for rail, entries in rail_currents.items():
        rail_always = sum(e["current_uA"] for e in entries if e["type"] != "pull_up")
        rail_cond = sum(e["current_uA"] for e in entries if e["type"] == "pull_up")
        rail_realistic = sum(e.get("realistic_uA", e["current_uA"]) for e in entries)
        always_on_uA += rail_always
        conditional_uA += rail_cond
        realistic_uA += rail_realistic
        result_rails[rail] = {
            "current_paths": entries,
            "total_uA": round(rail_always + rail_cond, 2),
            "always_on_uA": round(rail_always, 2),
            "conditional_uA": round(rail_cond, 2),
            "realistic_uA": round(rail_realistic, 2),
        }

    observations = [
        f"Always-on current: {always_on_uA:.1f} uA ({always_on_uA / 1000:.2f} mA)"
    ]
    if conditional_uA > 0:
        observations.append(
            f"Conditional current (pull-ups, worst-case): {conditional_uA:.1f} uA ({conditional_uA / 1000:.2f} mA)"
        )
    observations.append(
        f"Realistic sleep estimate: {realistic_uA:.1f} uA ({realistic_uA / 1000:.2f} mA)"
    )

    return {
        "rails": result_rails,
        "total_estimated_sleep_uA": round(always_on_uA, 2),
        "conditional_pull_up_uA": round(conditional_uA, 2),
        "realistic_total_uA": round(realistic_uA, 2),
        "observations": observations,
    }


_DERATING_PROFILES = {
    "commercial": {
        "ceramic_cap": 0.50, "electrolytic_cap": 0.80, "tantalum_cap": 0.80, "unknown_cap": 0.50,
        "ic_abs_max": 0.90, "resistor_power": 0.50,
        "over_designed_cap_margin": 0.80, "over_designed_res_margin": 0.90,
    },
    "military": {
        "ceramic_cap": 0.40, "electrolytic_cap": 0.60, "tantalum_cap": 0.50, "unknown_cap": 0.40,
        "ic_abs_max": 0.80, "resistor_power": 0.50,
        "over_designed_cap_margin": 0.85, "over_designed_res_margin": 0.95,
    },
    "automotive": {
        "ceramic_cap": 0.50, "electrolytic_cap": 0.70, "tantalum_cap": 0.60, "unknown_cap": 0.50,
        "ic_abs_max": 0.85, "resistor_power": 0.50,
        "over_designed_cap_margin": 0.80, "over_designed_res_margin": 0.90,
    },
}


def analyze_voltage_derating(ctx: AnalysisContext, signal_analysis: dict,
                             project_dir: str | None = None,
                             derating_profile: str = "commercial") -> dict:
    """Check component voltage/power ratings against applied conditions.

    Checks capacitors (voltage derating by dielectric type), IC absolute
    max voltage (from datasheet extraction cache), and resistor power
    dissipation (from footprint package size). Also flags over-designed
    components as cost/size optimization opportunities.

    Derating profiles: 'commercial' (default), 'military', 'automotive'.
    """
    components = ctx.components
    nets = ctx.nets
    pin_net = ctx.pin_net
    is_power_net = ctx.is_power_net
    is_ground = ctx.is_ground

    def _parse_voltage_rating(value_str: str) -> float | None:
        if not value_str:
            return None
        for part in re.split(r'[/\s]+', value_str):
            m = re.match(r'^(\d+\.?\d*)\s*[Vv]$', part.strip())
            if m:
                return float(m.group(1))
        return None

    def _classify_cap_dielectric(comp: dict) -> str:
        text = " ".join([comp.get("value", ""), comp.get("footprint", ""),
                         comp.get("description", "")]).upper()
        if any(kw in text for kw in ("X5R", "X7R", "X6S", "X8R", "C0G", "NP0", "COG", "Y5V", "Z5U", "MLCC")):
            return "ceramic"
        if any(kw in text for kw in ("ELECTROLYTIC", "ELCO", "POLAR")) or "CP_ELEC" in text or "CP_" in text:
            return "electrolytic"
        if any(kw in text for kw in ("TANTALUM", "TANT")):
            return "tantalum"
        if "Capacitor_SMD:C_" in comp.get("footprint", ""):
            return "ceramic"
        return "unknown"

    def _get_rail_voltage(net_name):
        for reg in signal_analysis.get("power_regulators", []):
            if reg.get("output_rail") == net_name:
                v = reg.get("estimated_vout")
                if v:
                    return v
        return _estimate_rail_voltage(net_name)

    def _find_power_net(ref):
        n1, _ = pin_net.get((ref, "1"), (None, None))
        n2, _ = pin_net.get((ref, "2"), (None, None))
        pwr_net = gnd_net = None
        if n1 and is_power_net(n1) and not is_ground(n1):
            pwr_net = n1
        if n2 and is_power_net(n2) and not is_ground(n2):
            pwr_net = pwr_net or n2
        if n1 and is_ground(n1):
            gnd_net = n1
        if n2 and is_ground(n2):
            gnd_net = gnd_net or n2
        return pwr_net, gnd_net, n1, n2

    def _read_ic_abs_max(mpn: str) -> dict | None:
        if not project_dir or not mpn:
            return None
        sanitized = re.sub(r'[^A-Za-z0-9_]', '_', mpn.strip())
        extract_path = Path(project_dir) / "datasheets" / "extracted" / f"{sanitized}.json"
        if not extract_path.exists():
            # Prefer manifest.json, fall back to legacy index.json
            extracted_dir = Path(project_dir) / "datasheets" / "extracted"
            idx_path = extracted_dir / "manifest.json"
            if not idx_path.exists():
                idx_path = extracted_dir / "index.json"
            if idx_path.exists():
                try:
                    with open(idx_path) as f:
                        idx = json.load(f)
                    for k, v in idx.get("extractions", {}).items():
                        if k.upper() == sanitized.upper():
                            extract_path = extracted_dir / v.get("file", "")
                            break
                except (json.JSONDecodeError, OSError):
                    pass
            if not extract_path.exists():
                return None
        try:
            with open(extract_path) as f:
                return json.load(f).get("absolute_maximum_ratings")
        except (json.JSONDecodeError, OSError):
            return None

    profile = _DERATING_PROFILES.get(derating_profile, _DERATING_PROFILES["commercial"])
    _CAP_DERATING = {"ceramic": profile["ceramic_cap"], "electrolytic": profile["electrolytic_cap"],
                     "tantalum": profile["tantalum_cap"], "unknown": profile["unknown_cap"]}
    _RESISTOR_POWER_RATING = {"0201": 0.05, "0402": 0.0625, "0603": 0.1, "0805": 0.125,
                              "1206": 0.25, "1210": 0.5, "2010": 0.75, "2512": 1.0}

    derating_issues = []
    over_designed = []
    caps_checked = ics_checked = resistors_checked = 0

    # ---- Capacitor voltage derating ----
    for comp in components:
        if comp["type"] != "capacitor":
            continue
        rated_v = _parse_voltage_rating(comp.get("value", ""))
        if not rated_v:
            continue
        ref = comp["reference"]
        pwr_net, gnd_net, n1, n2 = _find_power_net(ref)
        if not pwr_net:
            continue
        v_rail = _get_rail_voltage(pwr_net)
        if v_rail is None or v_rail <= 0:
            continue
        dielectric = _classify_cap_dielectric(comp)
        derating_factor = _CAP_DERATING.get(dielectric, 0.50)
        max_working_v = rated_v * derating_factor
        caps_checked += 1
        margin_pct = ((rated_v - v_rail) / rated_v) * 100 if rated_v > 0 else 0
        severity = derating_rule = None
        if v_rail > rated_v:
            severity, derating_rule = "critical", "exceeds_rated_voltage"
        elif v_rail > max_working_v:
            severity, derating_rule = "warning", f"{dielectric}_{int(derating_factor * 100)}pct"
        if severity:
            derating_issues.append({"ref": ref, "value": comp["value"], "component_type": "capacitor",
                                    "rail": pwr_net, "rail_voltage": v_rail, "rated_voltage": rated_v,
                                    "margin_pct": round(margin_pct, 1), "dielectric": dielectric,
                                    "derating_rule": derating_rule, "severity": severity})
        elif margin_pct > profile["over_designed_cap_margin"] * 100:
            suggested_v = v_rail * 2.5
            suggested_ratings = [v for v in (6.3, 10, 16, 25, 50, 100) if v >= suggested_v]
            suggestion = ""
            if suggested_ratings and suggested_ratings[0] < rated_v:
                suggestion = (f"Consider {suggested_ratings[0]:.0f}V rating — "
                              f"{rated_v:.0f}V is significantly over-designed for a {v_rail:.1f}V rail")
            over_designed.append({"ref": ref, "value": comp["value"], "component_type": "capacitor",
                                  "rail": pwr_net, "rail_voltage": v_rail, "rated_voltage": rated_v,
                                  "margin_pct": round(margin_pct, 1), "suggestion": suggestion})

    # ---- IC absolute max voltage check ----
    for comp in components:
        if comp["type"] != "ic":
            continue
        mpn = comp.get("mpn", "").strip()
        if not mpn or len(mpn) < 3:
            continue
        abs_max = _read_ic_abs_max(mpn)
        if not abs_max:
            continue
        ref = comp["reference"]
        vin_max = None
        for key in ("vin_max_v", "vcc_max_v", "supply_max_v", "vdd_max_v"):
            if abs_max.get(key) is not None:
                vin_max = abs_max[key]
                break
        if vin_max is None:
            continue
        max_rail_v = 0
        max_rail_name = ""
        for pin in comp.get("pins", []):
            net_name, _ = pin_net.get((ref, pin["number"]), (None, None))
            if not net_name or is_ground(net_name):
                continue
            if is_power_net(net_name):
                v = _get_rail_voltage(net_name)
                if v is not None and v > max_rail_v:
                    max_rail_v, max_rail_name = v, net_name
        if max_rail_v <= 0:
            continue
        ics_checked += 1
        margin_pct = ((vin_max - max_rail_v) / vin_max) * 100 if vin_max > 0 else 0
        if max_rail_v > vin_max:
            derating_issues.append({"ref": ref, "value": comp["value"], "component_type": "ic",
                                    "rail": max_rail_name, "rail_voltage": max_rail_v,
                                    "abs_max_vin": vin_max, "margin_pct": round(margin_pct, 1),
                                    "derating_rule": "exceeds_abs_max", "data_source": "extraction_cache",
                                    "severity": "critical"})
        elif margin_pct < 10:
            derating_issues.append({"ref": ref, "value": comp["value"], "component_type": "ic",
                                    "rail": max_rail_name, "rail_voltage": max_rail_v,
                                    "abs_max_vin": vin_max, "margin_pct": round(margin_pct, 1),
                                    "derating_rule": "ic_10pct_abs_max", "data_source": "extraction_cache",
                                    "severity": "warning"})

    # ---- Resistor power dissipation check ----
    for comp in components:
        if comp["type"] != "resistor":
            continue
        pv = comp.get("parsed_value") or parse_value(comp.get("value", ""))
        if not pv or pv <= 0:
            continue
        ref = comp["reference"]
        pwr_net, gnd_net, n1, n2 = _find_power_net(ref)
        if not pwr_net or not gnd_net:
            v1 = _get_rail_voltage(n1) if n1 and is_power_net(n1) else None
            v2 = _get_rail_voltage(n2) if n2 and is_power_net(n2) else None
            if v1 is not None and v2 is not None and v1 != v2:
                v_across = abs(v1 - v2)
            elif pwr_net and gnd_net:
                v_across = _get_rail_voltage(pwr_net)
            else:
                continue
        else:
            v_across = _get_rail_voltage(pwr_net)
        if v_across is None or v_across <= 0:
            continue
        power_w = (v_across ** 2) / pv
        fp = comp.get("footprint", "")
        pkg_match = re.search(r'(\d{4})_\d{4}Metric', fp)
        if not pkg_match:
            continue
        pkg = pkg_match.group(1)
        rated_power = _RESISTOR_POWER_RATING.get(pkg)
        if not rated_power:
            continue
        resistors_checked += 1
        max_working_power = rated_power * profile["resistor_power"]
        margin_pct = ((rated_power - power_w) / rated_power) * 100 if rated_power > 0 else 0
        severity = derating_rule = None
        if power_w > rated_power:
            severity, derating_rule = "critical", "exceeds_rated_power"
        elif power_w > max_working_power:
            severity, derating_rule = "warning", "resistor_50pct_power"
        if severity:
            derating_issues.append({"ref": ref, "value": comp["value"], "component_type": "resistor",
                                    "rail": pwr_net or n1, "voltage_across": v_across,
                                    "resistance_ohms": pv, "estimated_power_w": round(power_w, 4),
                                    "rated_power_w": rated_power, "package": pkg,
                                    "margin_pct": round(margin_pct, 1), "derating_rule": derating_rule,
                                    "severity": severity})
        elif margin_pct > profile["over_designed_res_margin"] * 100:
            pkg_sizes = ["0201", "0402", "0603", "0805", "1206", "1210", "2010", "2512"]
            suggested_pkg = None
            for p in pkg_sizes:
                p_rated = _RESISTOR_POWER_RATING.get(p, 0)
                if p_rated > 0 and power_w <= p_rated * profile["resistor_power"]:
                    suggested_pkg = p
                    break
            suggestion = ""
            if suggested_pkg and suggested_pkg != pkg:
                suggestion = (f"Consider {suggested_pkg} package — {pkg} is significantly "
                              f"over-designed ({power_w*1000:.1f}mW vs {rated_power*1000:.0f}mW rated)")
            over_designed.append({"ref": ref, "value": comp["value"], "component_type": "resistor",
                                  "package": pkg, "estimated_power_w": round(power_w, 4),
                                  "rated_power_w": rated_power, "margin_pct": round(margin_pct, 1),
                                  "suggestion": suggestion})

    # ---- Build result ----
    total_checked = caps_checked + ics_checked + resistors_checked
    if not derating_issues and not over_designed and total_checked == 0:
        return {}

    result: dict = {
        "derating_profile": derating_profile,
        "caps_checked": caps_checked, "ics_checked": ics_checked, "resistors_checked": resistors_checked,
        "issues": derating_issues,
    }
    observations = []
    cap_critical = [i for i in derating_issues if i.get("component_type") == "capacitor" and i["severity"] == "critical"]
    cap_warnings = [i for i in derating_issues if i.get("component_type") == "capacitor" and i["severity"] == "warning"]
    ic_issues = [i for i in derating_issues if i.get("component_type") == "ic"]
    res_issues = [i for i in derating_issues if i.get("component_type") == "resistor"]
    if cap_critical:
        observations.append(f"{len(cap_critical)} cap(s) exceed rated voltage — risk of failure")
    if cap_warnings:
        observations.append(f"{len(cap_warnings)} cap(s) have insufficient voltage derating margin")
    if ic_issues:
        observations.append(f"{len(ic_issues)} IC(s) operating near or beyond absolute maximum voltage")
    if res_issues:
        observations.append(f"{len(res_issues)} resistor(s) exceed power derating limit")
    if over_designed:
        result["over_designed"] = over_designed
        observations.append(f"{len(over_designed)} component(s) significantly over-designed — potential cost/size optimization")
    if observations:
        result["observations"] = observations
    return result


def analyze_protocol_compliance(components: list[dict], nets: dict,
                                design_analysis: dict, signal_analysis: dict,
                                pin_net: dict) -> dict:
    """Validate electrical characteristics of detected communication buses."""
    # EQ-063: t_rise = 0.8473 × R × C (I2C rise time estimation)
    buses = design_analysis.get("bus_analysis", {})
    cross_domain = design_analysis.get("cross_domain_signals", [])
    power_domains = design_analysis.get("power_domains", {}).get("ic_power_rails", {})
    findings = []

    # ---- I2C validation ----
    i2c_buses = buses.get("i2c", [])
    if i2c_buses:
        sda_entries = [b for b in i2c_buses if b.get("line") == "SDA"]
        scl_entries = [b for b in i2c_buses if b.get("line") == "SCL"]
        for sda in sda_entries:
            checks, issues, obs = {}, [], []
            sda_net = sda["net"]
            sda_devs = set(d["ref"] if isinstance(d, dict) else d for d in sda.get("devices", []))
            scl = scl_net = None
            for s in scl_entries:
                if set(d["ref"] if isinstance(d, dict) else d for d in s.get("devices", [])) & sda_devs:
                    scl, scl_net = s, s["net"]
                    break
            sda_pullups = sda.get("pull_ups", [])
            scl_pullups = scl.get("pull_ups", []) if scl else []
            checks["pull_ups_present"] = {"sda": len(sda_pullups) > 0, "scl": len(scl_pullups) > 0,
                                          "status": "pass" if sda_pullups and scl_pullups else "fail"}
            if not sda_pullups:
                issues.append("SDA line missing pull-up resistor")
            if scl and not scl_pullups:
                issues.append("SCL line missing pull-up resistor")
            pullup_checks = {}
            for line_name, pullups in [("sda", sda_pullups), ("scl", scl_pullups)]:
                for pu in pullups:
                    ohms = pu.get("ohms", 0)
                    if ohms <= 0:
                        continue
                    valid_100k, valid_400k = 1000 <= ohms <= 10000, 1000 <= ohms <= 4700
                    pullup_checks[line_name] = {"ref": pu["ref"], "ohms": ohms,
                                                "valid_100khz": valid_100k, "valid_400khz": valid_400k}
                    if not valid_100k:
                        issues.append(f"{line_name.upper()} pull-up {pu['ref']}={pu['value']} "
                                      f"({ohms:.0f}Ω) outside valid range for standard mode (1K-10K)")
                    elif not valid_400k:
                        obs.append(f"{line_name.upper()} pull-up {pu['ref']}={pu['value']} valid for "
                                   f"standard mode but too high for fast mode (max 4.7K)")
            if pullup_checks:
                all_100k = all(v.get("valid_100khz", False) for v in pullup_checks.values())
                checks["pull_up_value"] = {**pullup_checks, "status": "pass" if all_100k else "fail"}
            rise_checks = {}
            for line_name, pullups, entry in [("sda", sda_pullups, sda), ("scl", scl_pullups, scl)]:
                if not pullups or not entry:
                    continue
                ohms = pullups[0].get("ohms", 0)
                if ohms <= 0:
                    continue
                c_bus_pf = entry.get("estimated_bus_capacitance_pF", 10) + 10
                t_rise_ns = 0.8473 * ohms * c_bus_pf * 1e-3
                rise_checks[line_name] = {"rise_time_ns": round(t_rise_ns, 1), "bus_capacitance_pF": c_bus_pf,
                                          "max_100khz_ns": 1000, "max_400khz_ns": 300,
                                          "valid_100khz": t_rise_ns <= 1000, "valid_400khz": t_rise_ns <= 300}
                if t_rise_ns > 1000:
                    issues.append(f"{line_name.upper()} rise time {t_rise_ns:.0f}ns exceeds standard mode max (1000ns)")
                elif t_rise_ns > 300:
                    obs.append(f"{line_name.upper()} rise time {t_rise_ns:.0f}ns OK for standard mode but exceeds fast mode max (300ns)")
            if rise_checks:
                checks["rise_time"] = rise_checks
            if sda_pullups:
                pu_rail = sda_pullups[0].get("to_rail", "")
                pu_voltage = _estimate_rail_voltage(pu_rail) if pu_rail else None
                device_voltages = set()
                for dev in sda.get("devices", []):
                    dev_ref = dev["ref"] if isinstance(dev, dict) else dev
                    for rail_info in power_domains.get(dev_ref, {}).get("power_rails", []):
                        v = _estimate_rail_voltage(rail_info) if isinstance(rail_info, str) else None
                        if v:
                            device_voltages.add(v)
                if pu_voltage and device_voltages:
                    mismatched = [v for v in device_voltages if abs(v - pu_voltage) > 0.5]
                    status = "fail" if mismatched else "pass"
                    checks["voltage_compatibility"] = {"pull_up_rail": pu_rail, "pull_up_voltage": pu_voltage,
                                                       "device_voltages": sorted(device_voltages), "status": status}
                    if mismatched:
                        issues.append(f"Pull-up rail {pu_rail} ({pu_voltage}V) but device(s) on "
                                      f"{', '.join(f'{v}V' for v in mismatched)} — voltage mismatch")
            # KH: I2C open-drain VOL compatibility
            # I2C spec: VOL_max = 0.4V for standard/fast mode
            # With pull-up R and sink current I_OL: VOL = I_OL × R_on
            # If pull-up too strong (low R) relative to device sink current,
            # VOL may exceed 0.4V threshold
            if sda_pullups:
                min_pu_ohms = min(pu.get("ohms", 10000) for pu in sda_pullups)
                # I2C spec sink current: 3mA standard, 6mA fast, 20mA fast+
                # Derive speed mode from rise time checks
                speed = "standard"
                if "rise_time" in checks:
                    rt = checks["rise_time"]
                    sda_rt = rt.get("sda", {})
                    if sda_rt.get("valid_400khz"):
                        speed = "fast"
                iol_ma = {"standard": 3, "fast": 6, "fast_plus": 20,
                          "high_speed": 20}.get(speed, 3)
                # Max pull-up for VOL < 0.4V: R_max = 0.4V / I_OL
                r_max_for_vol = 0.4 / (iol_ma * 1e-3) if iol_ma > 0 else 10000
                if min_pu_ohms > r_max_for_vol:
                    issues.append(
                        f"Pull-up {min_pu_ohms:.0f}\u03a9 may not meet VOL<0.4V spec "
                        f"at {speed} mode ({iol_ma}mA sink): max {r_max_for_vol:.0f}\u03a9")
                    checks["vol_compatibility"] = {
                        "status": "warning",
                        "pull_up_ohms": min_pu_ohms,
                        "max_for_vol": round(r_max_for_vol),
                        "iol_ma": iol_ma,
                        "speed_mode": speed,
                    }

            # I2C bus current budget
            # Each device on the bus contributes leakage current (typically 1-10µA)
            # Total must not exceed pull-up sourcing capability
            n_devices = len(sda_devs)
            if n_devices > 0 and sda_pullups:
                # Conservative: 10µA leakage per device
                total_leakage_ua = n_devices * 10
                min_pu = min(pu.get("ohms", 10000) for pu in sda_pullups)
                pu_voltage = checks.get("voltage_compatibility", {}).get("pull_up_voltage")
                if pu_voltage:
                    pull_up_current_ua = (pu_voltage / min_pu) * 1e6
                    if total_leakage_ua > pull_up_current_ua * 0.1:
                        # Leakage exceeds 10% of pull-up current
                        checks["bus_current_budget"] = {
                            "status": "warning",
                            "device_count": n_devices,
                            "estimated_leakage_ua": total_leakage_ua,
                            "pull_up_current_ua": round(pull_up_current_ua),
                        }
                        issues.append(
                            f"I2C bus has {n_devices} devices with ~{total_leakage_ua}\u00b5A "
                            f"total leakage vs {pull_up_current_ua:.0f}\u00b5A pull-up capacity")

            if checks:
                # Merge SDA + SCL device lists, deduplicate by ref
                _all_devs = sda.get("devices", []) + (scl.get("devices", []) if scl else [])
                _seen_refs: set[str] = set()
                _merged_devs: list = []
                for _d in _all_devs:
                    _r = _d["ref"] if isinstance(_d, dict) else _d
                    if _r not in _seen_refs:
                        _seen_refs.add(_r)
                        _merged_devs.append(_d)
                _merged_devs.sort(key=lambda d: d["ref"] if isinstance(d, dict) else d)
                entry_result = {"protocol": "i2c", "sda_net": sda_net, "scl_net": scl_net,
                                "devices": _merged_devs,
                                "checks": checks}
                if issues:
                    entry_result["issues"] = issues
                if obs:
                    entry_result["observations"] = obs
                findings.append(entry_result)

    # ---- SPI validation ----
    for spi in buses.get("spi", []):
        issues = []
        spi_checks: dict = {}
        load_count = spi.get("load_count", 0)
        cs_count = spi.get("chip_select_count", 0)
        if load_count > 1 and cs_count < load_count - 1:
            issues.append(f"{load_count} SPI devices but only {cs_count} CS line(s) — need {load_count - 1}")

        # SPI clock frequency advisory
        # High device counts (>4 devices) increase capacitive loading on SCK
        spi_sigs = spi.get("signals", {})
        sck_sig = spi_sigs.get("SCK", {})
        n_spi_devs = len(sck_sig.get("devices", [])) if isinstance(sck_sig, dict) else 0
        if n_spi_devs == 0:
            n_spi_devs = load_count
        if n_spi_devs > 4:
            issues.append(
                f"SPI bus has {n_spi_devs} devices — capacitive loading may "
                f"limit maximum clock frequency. Consider buffered clock.")
            spi_checks["device_loading"] = {
                "status": "warning",
                "device_count": n_spi_devs,
            }

        # SPI signal integrity advisory for high-speed designs
        # Flag when SPI bus has >2 devices and no series termination detected
        if n_spi_devs > 2:
            has_series_r = False
            for sig_name in ("MOSI", "MISO", "SCK"):
                sig = spi_sigs.get(sig_name, {})
                if isinstance(sig, dict):
                    for dev_ref in sig.get("devices", []):
                        comp = next((c for c in components if c["reference"] == dev_ref), None)
                        if comp and comp.get("type") == "resistor":
                            has_series_r = True
                            break
                if has_series_r:
                    break
            if not has_series_r:
                spi_checks["signal_integrity"] = {
                    "status": "advisory",
                    "detail": "No series termination detected on multi-device SPI bus",
                }

        if issues or spi_checks:
            entry: dict = {"protocol": "spi", "bus_id": spi.get("bus_id", ""),
                           "load_count": load_count, "chip_select_count": cs_count}
            if issues:
                entry["issues"] = issues
            if spi_checks:
                entry["checks"] = spi_checks
            findings.append(entry)

    # ---- UART validation ----
    uart_buses = buses.get("uart", [])
    if uart_buses and cross_domain:
        uart_nets = {u["net"] for u in uart_buses}
        for xd in cross_domain:
            if xd.get("net", "") in uart_nets:
                domains = xd.get("power_domains", [])
                if len(domains) >= 2:
                    findings.append({"protocol": "uart", "net": xd["net"],
                                     "issues": [f"UART signal crosses voltage domains ({', '.join(domains)}) — level shifter may be needed"]})

    # RS-232 transceiver detection and swing validation
    if uart_buses:
        _rs232_keywords = ("max232", "sp232", "sp3232", "max3232", "st3232",
                           "icl232", "adm232", "sipex", "rs232", "rs-232",
                           "max202", "max211", "max213")
        # Build quick lookup from components list
        _comp_by_ref: dict = {c["reference"]: c for c in components}
        rs232_xcvrs: list[str] = []
        for uart_entry in uart_buses:
            for dev in uart_entry.get("devices", []):
                dev_ref = dev["ref"] if isinstance(dev, dict) else dev
                c = _comp_by_ref.get(dev_ref, {})
                val_lib = (c.get("value", "") + " " + c.get("lib_id", "")).lower()
                if any(k in val_lib for k in _rs232_keywords):
                    if dev_ref not in rs232_xcvrs:
                        rs232_xcvrs.append(dev_ref)

        if rs232_xcvrs:
            uart_checks: dict = {}
            uart_issues: list[str] = []
            uart_checks["rs232_transceiver"] = {
                "status": "pass",
                "transceivers": rs232_xcvrs,
                "detail": f"RS-232 transceiver(s) detected: {', '.join(rs232_xcvrs)}",
            }
            # Check for charge pump capacitors (RS-232 transceivers need external caps)
            cap_count = 0
            _seen_caps: set[str] = set()
            for xcvr_ref in rs232_xcvrs:
                for (pref, _pnum), (net_name, _) in pin_net.items():
                    if pref != xcvr_ref:
                        continue
                    if net_name and net_name in nets:
                        for p in nets[net_name]["pins"]:
                            pc = _comp_by_ref.get(p.get("component", ""), {})
                            if pc.get("type") == "capacitor" and pc["reference"] not in _seen_caps:
                                _seen_caps.add(pc["reference"])
                                cap_count += 1
            if cap_count < 4:  # Most RS-232 transceivers need 4-5 charge pump caps
                uart_issues.append(
                    f"RS-232 transceiver {rs232_xcvrs[0]} may have insufficient "
                    f"charge pump capacitors (found ~{cap_count}, typical: 4-5)")
                uart_checks["rs232_charge_pump_caps"] = {
                    "status": "warning",
                    "caps_found": cap_count,
                    "typical_required": 4,
                }
            uart_finding: dict = {"protocol": "uart", "checks": uart_checks}
            if uart_issues:
                uart_finding["issues"] = uart_issues
            findings.append(uart_finding)

    # ---- CAN validation ----
    diff_pairs = design_analysis.get("differential_pairs", [])
    for can in buses.get("can", []):
        issues, obs = [], []
        has_term = can.get("has_termination", False)
        term_value = can.get("termination_ohms")
        if not has_term:
            for dp in diff_pairs:
                if dp.get("type") == "CAN" or "CAN" in dp.get("name", "").upper():
                    if dp.get("has_termination"):
                        has_term, term_value = True, dp.get("termination_ohms")
        if not has_term:
            issues.append("CAN bus missing 120Ω termination resistor")
        elif term_value and abs(term_value - 120) > 12:
            issues.append(f"CAN termination is {term_value}Ω (expected 120Ω ±10%)")
        elif term_value:
            obs.append("CAN 120Ω termination present (verify remote end has matching termination)")
        if issues or obs:
            findings.append({"protocol": "can", "nets": [can.get("canh_net", ""), can.get("canl_net", "")],
                             "has_termination": has_term, "termination_ohms": term_value,
                             "issues": issues or None, "observations": obs or None})

    if not findings:
        return {}
    return {"protocols_checked": list({f["protocol"] for f in findings}), "findings": findings,
            "total_issues": sum(len(f.get("issues", []) or []) for f in findings)}


def analyze_power_budget(ctx: AnalysisContext,
                         signal_analysis: dict) -> dict:
    """Power budget estimation per rail.

    Identifies each rail's regulator and max current, counts ICs per rail with
    rough current estimation by type, and estimates thermal dissipation for LDOs.
    """
    components = ctx.components
    nets = ctx.nets
    pin_net = ctx.pin_net
    comp_lookup = ctx.comp_lookup
    ref_pins = ctx.ref_pins
    is_power_net = ctx.is_power_net
    is_ground = ctx.is_ground

    # Rough current estimates by IC type keywords (mA)
    ic_current_estimates = {
        "esp32": 240, "esp8266": 170, "esp": 200,
        "nrf52": 15, "nrf51": 12, "nrf53": 20, "nrf91": 50,
        "stm32f4": 100, "stm32f1": 50, "stm32l4": 20, "stm32l0": 10,
        "stm32h7": 200, "stm32f7": 150, "stm32": 80,
        "atmega": 20, "attiny": 10, "atsamd": 30, "samd": 30,
        "rp2040": 50, "rp2350": 60,
        "wifi": 250, "wlan": 250, "bluetooth": 50, "ble": 15,
        "lora": 120, "sx127": 120, "sx126": 50,
        "ethernet": 150, "phy": 100, "lan87": 80, "ksz": 100,
        "sensor": 5, "bme": 3, "bmp": 3, "lis": 2, "mpu": 5,
        "flash": 25, "eeprom": 5, "sram": 10,
        "adc": 10, "dac": 10,
        "codec": 30, "amplifier": 20, "opamp": 5,
        "usb": 50, "uart": 5, "spi": 5, "i2c": 5,
    }

    # Build power domain mapping: rail -> list of ICs
    rail_ics: dict[str, list[dict]] = {}
    for comp in components:
        if comp["type"] != "ic":
            continue
        ref = comp["reference"]
        for pnum, (net_name, _) in ref_pins.get(ref, {}).items():
            if net_name and is_power_net(net_name) and not is_ground(net_name):
                # Check if this is a power pin (by pin type or name)
                if net_name in nets:
                    for p in nets[net_name]["pins"]:
                        if p["component"] == ref:
                            ptype = p.get("pin_type", "")
                            pname = p.get("pin_name", "").upper()
                            if ptype == "power_in" or pname in (
                                "VCC", "VDD", "AVCC", "AVDD", "VDDIO", "DVDD",
                                "VIN", "VCCA", "VCCB", "VDDQ", "VBUS"
                            ):
                                ic_entry = {
                                    "ref": ref,
                                    "value": comp["value"],
                                }
                                # Estimate current
                                val_lower = comp.get("value", "").lower()
                                lib_lower = comp.get("lib_id", "").lower()
                                search_str = val_lower + " " + lib_lower
                                est_ma = 10  # default
                                for kw, ma in ic_current_estimates.items():
                                    if kw in search_str:
                                        est_ma = ma
                                        break
                                ic_entry["estimated_mA"] = est_ma
                                rail_ics.setdefault(net_name, []).append(ic_entry)
                            break

    # Deduplicate ICs per rail (an IC may have multiple power pins on same rail)
    for rail in rail_ics:
        seen_refs = set()
        deduped = []
        for ic in rail_ics[rail]:
            if ic["ref"] not in seen_refs:
                seen_refs.add(ic["ref"])
                deduped.append(ic)
        rail_ics[rail] = deduped

    # Map regulators to output rails
    reg_by_rail: dict[str, dict] = {}
    for reg in signal_analysis.get("power_regulators", []):
        out_rail = reg.get("output_rail")
        if out_rail:
            reg_by_rail[out_rail] = reg

    if not rail_ics and not reg_by_rail:
        return {}

    # All rails of interest
    all_rails = set(rail_ics.keys()) | set(reg_by_rail.keys())

    rails_result = {}
    observations = []

    for rail in sorted(all_rails):
        ics = rail_ics.get(rail, [])
        total_ic_mA = sum(ic["estimated_mA"] for ic in ics)

        rail_info: dict = {
            "ic_count": len(ics),
            "ics": ics,
            "estimated_load_mA": total_ic_mA,
        }

        reg = reg_by_rail.get(rail)
        if reg:
            rail_info["regulator"] = {
                "ref": reg["ref"],
                "value": reg["value"],
                "topology": reg.get("topology", "unknown"),
            }
            v_out = reg.get("estimated_vout")
            v_in_rail = reg.get("input_rail")
            if v_out:
                rail_info["regulator"]["output_voltage"] = v_out

            # LDO thermal dissipation
            if reg.get("topology") == "LDO" and v_in_rail and v_out:
                v_in = _estimate_rail_voltage(v_in_rail)
                if v_in and v_in > v_out:
                    v_drop = v_in - v_out
                    power_w = v_drop * (total_ic_mA / 1000.0)
                    rail_info["ldo_dissipation"] = {
                        "input_voltage": v_in,
                        "dropout": round(v_drop, 2),
                        "power_mW": round(power_w * 1000, 1),
                    }
                    if power_w > 0.5:
                        observations.append(
                            f"{rail}: LDO {reg['ref']} dissipates ~{power_w * 1000:.0f} mW "
                            f"({v_drop:.1f}V drop x {total_ic_mA} mA) — verify thermal rating"
                        )

        rails_result[rail] = rail_info

    result: dict = {"rails": rails_result}
    if observations:
        result["observations"] = observations
    return result


def analyze_power_sequencing(ctx: AnalysisContext,
                             signal_analysis: dict) -> dict:
    """Power sequencing dependency analysis.

    For each regulator, finds what drives its EN pin and PG (power-good) output,
    builds a dependency graph, and flags floating EN pins.
    """
    components = ctx.components
    nets = ctx.nets
    pin_net = ctx.pin_net
    comp_lookup = ctx.comp_lookup
    ref_pins = ctx.ref_pins
    is_power_net = ctx.is_power_net
    is_ground = ctx.is_ground
    regulators = signal_analysis.get("power_regulators", [])
    if not regulators:
        return {}

    dependencies = []
    floating_en = []
    pg_connections = []

    for reg in regulators:
        ref = reg["ref"]
        out_rail = reg.get("output_rail", "")
        ic = comp_lookup.get(ref)
        if not ic:
            continue

        # Gather all pins for this IC
        ic_pins: dict[str, tuple[str, str]] = {}  # pin_name -> (net_name, pin_number)
        for pin_num, (net_name, _) in ref_pins.get(ref, {}).items():
            pin_name = ""
            if net_name in nets:
                for p in nets[net_name]["pins"]:
                    if p["component"] == ref and p["pin_number"] == pin_num:
                        pin_name = p.get("pin_name", "").upper()
                        break
            ic_pins[pin_name] = (net_name, pin_num)

        # Find EN pin
        en_net = None
        en_pin_name = None
        for pname, (net, pnum) in ic_pins.items():
            pn_base = pname.rstrip("0123456789")
            if pname in ("EN", "ENABLE", "ON", "~{SHDN}", "SHDN", "~{EN}",
                         "CE", "CHIP_ENABLE") or pn_base == "EN":
                en_net = net
                en_pin_name = pname
                break

        if en_net:
            dep_entry: dict = {
                "regulator": ref,
                "output_rail": out_rail,
                "en_pin": en_pin_name,
                "en_net": en_net,
            }

            # Determine what drives EN
            if is_power_net(en_net):
                dep_entry["en_source"] = "always_on"
                dep_entry["en_driven_by"] = en_net
            elif is_ground(en_net):
                dep_entry["en_source"] = "disabled"
                dep_entry["en_driven_by"] = en_net
            elif en_net in nets:
                en_pins = nets[en_net]["pins"]
                # Filter out power symbols and the regulator itself
                drivers = [
                    p for p in en_pins
                    if p["component"] != ref
                    and not p["component"].startswith("#")
                ]
                if not drivers:
                    dep_entry["en_source"] = "floating"
                    floating_en.append({
                        "regulator": ref,
                        "output_rail": out_rail,
                        "en_pin": en_pin_name,
                        "warning": f"{ref} EN pin ({en_pin_name}) appears unconnected",
                    })
                else:
                    # Check if driven by another regulator's output rail or PG
                    driver_refs = [d["component"] for d in drivers]
                    driver_types = []
                    for dr in drivers:
                        dc = comp_lookup.get(dr["component"])
                        if dc:
                            driver_types.append(dc["type"])
                    # Check if EN is connected to a power rail via resistor
                    has_pull_up = any(
                        comp_lookup.get(d["component"], {}).get("type") == "resistor"
                        for d in drivers
                    )
                    dep_entry["en_source"] = "controlled"
                    dep_entry["en_driven_by"] = driver_refs
                    if has_pull_up:
                        dep_entry["has_pull_up"] = True

            dependencies.append(dep_entry)

        # Find PG/PGOOD pin (exclude ground pads like PGND, AGND, EP/GND)
        for pname, (net, pnum) in ic_pins.items():
            pn_upper = pname.upper()
            # Skip ground/pad pins that false-match on "PG" substring
            if any(g in pn_upper for g in ("GND", "GROUND", "PAD", "EP")):
                continue
            if any(k in pn_upper for k in ("PG", "PGOOD", "POWER_GOOD", "POK")):
                pg_entry: dict = {
                    "regulator": ref,
                    "output_rail": out_rail,
                    "pg_pin": pname,
                    "pg_net": net,
                }
                # Find what PG connects to
                if net in nets:
                    pg_targets = [
                        p["component"] for p in nets[net]["pins"]
                        if p["component"] != ref
                        and not p["component"].startswith("#")
                    ]
                    if pg_targets:
                        pg_entry["connected_to"] = pg_targets
                        # Check if PG drives another regulator's EN
                        for dep in dependencies:
                            if dep.get("en_net") == net:
                                dep["sequenced_after"] = ref
                                dep["sequence_signal"] = "power_good"
                pg_connections.append(pg_entry)
                break

    if not dependencies and not floating_en and not pg_connections:
        return {}

    result: dict = {}
    if dependencies:
        result["dependencies"] = dependencies
    if floating_en:
        result["floating_en_warnings"] = floating_en
    if pg_connections:
        result["power_good_signals"] = pg_connections

    observations = []
    always_on = [d for d in dependencies if d.get("en_source") == "always_on"]
    controlled = [d for d in dependencies if d.get("en_source") == "controlled"]
    if always_on:
        observations.append(
            f"{len(always_on)} regulator(s) always enabled: "
            + ", ".join(d["regulator"] for d in always_on)
        )
    if controlled:
        observations.append(
            f"{len(controlled)} regulator(s) with controlled enable"
        )
    if floating_en:
        observations.append(
            f"{len(floating_en)} regulator(s) with floating EN pin — may not start"
        )
    if observations:
        result["observations"] = observations

    return result


def analyze_bom_optimization(components: list[dict]) -> dict:
    """BOM consolidation and optimization suggestions.

    Groups components by type, finds near-value resistors that could be
    consolidated, identifies capacitors with same value but different footprints,
    and flags single-use values.
    """
    # Filter to real components
    real = [c for c in components
            if c["type"] not in ("power_symbol", "power_flag", "flag")]

    if not real:
        return {}

    # Group by type
    by_type: dict[str, list[dict]] = {}
    for c in real:
        by_type.setdefault(c["type"], []).append(c)

    unique_counts: dict[str, int] = {}
    consolidation_suggestions = []

    # --- Resistors: find values within 5% of each other ---
    resistors = by_type.get("resistor", [])
    r_values: dict[float, list[str]] = {}  # parsed_value -> [refs]
    for r in resistors:
        val = parse_value(r.get("value", ""))
        if val and val > 0:
            r_values.setdefault(val, []).append(r["reference"])

    unique_counts["resistor"] = len(r_values)

    sorted_r_vals = sorted(r_values.keys())
    for i, v1 in enumerate(sorted_r_vals):
        for v2 in sorted_r_vals[i + 1:]:
            if v2 > v1 * 1.06:
                break  # sorted, so no more within 5%
            pct_diff = abs(v2 - v1) / v1 * 100
            if pct_diff <= 5.0 and pct_diff > 0:
                # Only suggest if consolidating saves a unique value
                refs1 = r_values[v1]
                refs2 = r_values[v2]
                # Suggest the more commonly used value
                keep_val = v1 if len(refs1) >= len(refs2) else v2
                replace_val = v2 if keep_val == v1 else v1
                replace_refs = refs2 if keep_val == v1 else refs1
                consolidation_suggestions.append({
                    "type": "resistor",
                    "suggestion": f"Consolidate {len(replace_refs)} resistor(s) "
                                  f"({', '.join(replace_refs)}) from "
                                  f"{replace_val:.4g} to {keep_val:.4g} ohm "
                                  f"({pct_diff:.1f}% difference)",
                    "current_values": [v1, v2],
                    "refs_to_change": replace_refs,
                })

    # --- Capacitors: same value, different footprints ---
    capacitors = by_type.get("capacitor", [])
    cap_by_value: dict[str, dict[str, list[str]]] = {}  # value_str -> {footprint -> [refs]}
    c_values: dict[float, list[str]] = {}
    for c in capacitors:
        val_str = c.get("value", "")
        fp = c.get("footprint", "") or "unknown"
        cap_by_value.setdefault(val_str, {}).setdefault(fp, []).append(c["reference"])
        val = parse_value(val_str, component_type="capacitor")
        if val and val > 0:
            c_values.setdefault(val, []).append(c["reference"])

    unique_counts["capacitor"] = len(c_values)

    for val_str, fp_map in cap_by_value.items():
        if len(fp_map) > 1:
            total_refs = sum(len(refs) for refs in fp_map.values())
            if total_refs > 1:
                fp_summary = {fp: len(refs) for fp, refs in fp_map.items()}
                consolidation_suggestions.append({
                    "type": "capacitor",
                    "suggestion": f"Capacitor value '{val_str}' used with "
                                  f"{len(fp_map)} different footprints — consider standardizing",
                    "value": val_str,
                    "footprint_breakdown": fp_summary,
                })

    # --- Single-use values (across all passive types) ---
    single_use_values = []
    for comp_type in ("resistor", "capacitor", "inductor"):
        vals: dict[str, int] = {}
        for c in by_type.get(comp_type, []):
            v = c.get("value", "")
            if v:
                vals[v] = vals.get(v, 0) + 1
        for v, count in vals.items():
            if count == 1:
                single_use_values.append({"type": comp_type, "value": v})

    # --- Count unique footprints ---
    all_footprints = set()
    for c in real:
        fp = c.get("footprint", "")
        if fp:
            all_footprints.add(fp)

    result: dict = {
        "unique_value_counts": unique_counts,
        "total_unique_footprints": len(all_footprints),
        "single_use_passive_values": len(single_use_values),
    }
    if consolidation_suggestions:
        result["consolidation_suggestions"] = consolidation_suggestions
    observations = []
    if len(single_use_values) > 5:
        observations.append(
            f"{len(single_use_values)} single-use passive values — "
            f"consider standardizing to reduce BOM line items"
        )
    if consolidation_suggestions:
        observations.append(
            f"{len(consolidation_suggestions)} potential consolidation(s) identified"
        )
    if observations:
        result["observations"] = observations
    return result


def analyze_test_coverage(ctx: AnalysisContext) -> dict:
    """Test point and debug interface coverage analysis.

    Finds test points, checks which key nets have them, and identifies
    debug connectors (SWD, JTAG, UART headers).
    """
    components = ctx.components
    nets = ctx.nets
    pin_net = ctx.pin_net
    comp_lookup = ctx.comp_lookup
    ref_pins = ctx.ref_pins
    is_power_net = ctx.is_power_net
    is_ground = ctx.is_ground

    # Find test points
    test_points = []
    tp_nets = set()
    for comp in components:
        ref = comp["reference"]
        fp = comp.get("footprint", "").lower()
        is_tp = (ref.startswith("TP") or
                 "testpoint" in fp or "test_point" in fp or
                 "testpad" in fp or "test_pad" in fp or
                 comp.get("value", "").lower() in ("testpoint", "test_point", "tp",
                                                    "testpad", "test_pad"))
        if is_tp:
            # Find what net it's on
            for pnum, (net_name, _) in ref_pins.get(ref, {}).items():
                if net_name:
                    test_points.append({
                        "ref": ref,
                        "net": net_name,
                        "value": comp.get("value", ""),
                    })
                    tp_nets.add(net_name)
                    break

    # Find debug connectors
    debug_connectors = []
    debug_keywords = {
        "swd": ["SWDIO", "SWCLK", "SWO", "NRST"],
        "jtag": ["TDI", "TDO", "TCK", "TMS", "TRST"],
        "uart": ["TX", "RX", "TXD", "RXD"],
    }
    for comp in components:
        if comp["type"] != "connector":
            continue
        ref = comp["reference"]
        val = comp.get("value", "").lower()
        fp = comp.get("footprint", "").lower()
        lib = comp.get("lib_id", "").lower()
        combined = val + " " + fp + " " + lib

        # Collect connected net names for this connector (try pin_net first, fall back to nets dict)
        conn_nets = [net for net, _ in ref_pins.get(ref, {}).values() if net]
        # Fallback: if pin_net gave few results (e.g., pin number collisions with "?"),
        # also scan the nets dict for this connector's connections
        if len(conn_nets) < 3:
            for net_name, net_info in nets.items():
                for p in net_info.get("pins", []):
                    if p["component"] == ref and net_name not in conn_nets:
                        conn_nets.append(net_name)
        conn_nets_upper = [n.upper() for n in conn_nets]

        for iface, expected_pins in debug_keywords.items():
            # Match on connector name/footprint/lib_id OR on connected net names
            name_match = iface in combined or any(p.lower() in combined for p in expected_pins)
            net_match = sum(1 for p in expected_pins if any(p in n for n in conn_nets_upper)) >= 2
            if name_match or net_match:
                debug_connectors.append({
                    "ref": ref,
                    "value": comp.get("value", ""),
                    "interface": iface,
                    "connected_nets": conn_nets,
                })
                break

    # Check key nets without test points
    key_net_patterns = {
        "power_rails": [],
        "i2c": ["SDA", "SCL"],
        "spi": ["MOSI", "MISO", "SCK", "SCLK", "SDI", "SDO"],
        "uart": ["TX", "RX", "TXD", "RXD", "UART"],
        "reset": ["RESET", "RST", "NRST", "~{RST}", "~{RESET}"],
    }

    uncovered_key_nets = []
    for net_name in nets:
        if net_name.startswith("__unnamed_"):
            continue
        if net_name in tp_nets:
            continue

        is_key = False
        category = ""

        # Power rails
        if is_power_net(net_name) and not is_ground(net_name):
            is_key = True
            category = "power_rail"

        # Signal patterns
        if not is_key:
            nu = net_name.upper()
            for cat, patterns in key_net_patterns.items():
                if cat == "power_rails":
                    continue
                for pat in patterns:
                    if pat in nu:
                        is_key = True
                        category = cat
                        break
                if is_key:
                    break

        if is_key:
            uncovered_key_nets.append({
                "net": net_name,
                "category": category,
            })

    result: dict = {
        "test_points": test_points,
        "test_point_count": len(test_points),
        "covered_nets": sorted(tp_nets),
    }
    if debug_connectors:
        result["debug_connectors"] = debug_connectors
    if uncovered_key_nets:
        result["uncovered_key_nets"] = uncovered_key_nets

    observations = []
    if not test_points:
        observations.append("No test points found in design")
    else:
        observations.append(f"{len(test_points)} test point(s) covering {len(tp_nets)} net(s)")
    if not debug_connectors:
        observations.append("No debug connectors (SWD/JTAG/UART) identified")
    if uncovered_key_nets:
        by_cat: dict[str, int] = {}
        for u in uncovered_key_nets:
            by_cat[u["category"]] = by_cat.get(u["category"], 0) + 1
        parts = [f"{count} {cat}" for cat, count in sorted(by_cat.items())]
        observations.append(f"Key nets without test points: {', '.join(parts)}")
    if observations:
        result["observations"] = observations
    return result


def analyze_assembly_complexity(components: list[dict]) -> dict:
    """Assembly complexity scoring.

    Counts components by package type, scores difficulty, and flags
    fine-pitch components.
    """
    real = [c for c in components
            if c["type"] not in ("power_symbol", "power_flag", "flag")]
    if not real:
        return {}

    # Package classification
    hard_smd = {"0201", "01005"}
    medium_hard_smd = {"0402"}
    medium_smd = {"0603", "0805"}
    easy_smd = {"1206", "1210", "1812", "2220", "2512"}

    # IC package patterns
    hard_ic_patterns = ["bga", "wlcsp", "ucsp", "flip_chip"]
    medium_hard_ic_patterns = ["qfn", "dfn", "mlp", "son", "vson", "wson", "udfn"]
    medium_ic_patterns = ["tssop", "msop", "ssop", "lqfp", "tqfp", "qfp"]
    easy_ic_patterns = ["soic", "sop", "sot-23", "sot23", "sot-223", "sot223",
                        "sot-89", "sot89", "sc-70", "sc70", "to-252", "dpak",
                        "to-263", "d2pak", "to-220", "to-92"]

    difficulty_counts: dict[str, int] = {"hard": 0, "medium": 0, "easy": 0}
    package_breakdown: dict[str, int] = {}
    fine_pitch_components = []
    tht_count = 0
    smd_count = 0

    def _extract_package_info(footprint: str) -> tuple[str, str]:
        """Returns (package_name, difficulty)."""
        if not footprint:
            return ("unknown", "medium")
        fp_lower = footprint.lower()

        # Check for THT
        if any(k in fp_lower for k in ("tht", "through_hole", "dip", "to-220", "to-92")):
            return ("THT", "easy")

        # Check SMD passive packages
        m = re.search(r'(\d{4,5})_\d{4,5}Metric', footprint)
        if m:
            pkg = m.group(1)
            if pkg in hard_smd:
                return (pkg, "hard")
            elif pkg in medium_hard_smd:
                return (pkg, "hard")
            elif pkg in medium_smd:
                return (pkg, "medium")
            elif pkg in easy_smd:
                return (pkg, "easy")
            return (pkg, "medium")

        # Check IC packages
        for pat in hard_ic_patterns:
            if pat in fp_lower:
                return (pat.upper(), "hard")
        for pat in medium_hard_ic_patterns:
            if pat in fp_lower:
                return (pat.upper(), "hard")
        for pat in medium_ic_patterns:
            if pat in fp_lower:
                return (pat.upper(), "medium")
        for pat in easy_ic_patterns:
            if pat in fp_lower:
                return (pat.upper(), "easy")

        return ("other_SMD", "medium")

    for comp in real:
        fp = comp.get("footprint", "")
        pkg_name, difficulty = _extract_package_info(fp)

        package_breakdown[pkg_name] = package_breakdown.get(pkg_name, 0) + 1
        difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1

        if pkg_name == "THT":
            tht_count += 1
        else:
            smd_count += 1

        # Check for fine pitch (<= 0.5mm)
        if fp:
            fp_lower = fp.lower()
            m = re.search(r'pitch[_\-]?(\d+\.?\d*)', fp_lower)
            if m:
                pitch = float(m.group(1))
                if pitch <= 0.5:
                    fine_pitch_components.append({
                        "ref": comp["reference"],
                        "value": comp.get("value", ""),
                        "footprint": fp,
                        "pitch_mm": pitch,
                    })
            # BGA/QFN often fine pitch
            elif any(k in fp_lower for k in ("bga", "wlcsp")):
                fine_pitch_components.append({
                    "ref": comp["reference"],
                    "value": comp.get("value", ""),
                    "footprint": fp,
                    "pitch_mm": None,
                    "note": "BGA/WLCSP — likely fine pitch",
                })

    # Compute complexity score (0-100)
    total = len(real)
    if total == 0:
        return {}
    score = 0
    score += (difficulty_counts["hard"] / total) * 80
    score += (difficulty_counts["medium"] / total) * 40
    score += (difficulty_counts["easy"] / total) * 10
    # Unique footprint penalty
    unique_fps = len(package_breakdown)
    if unique_fps > 15:
        score += min(20, (unique_fps - 15) * 2)
    score = min(100, round(score))

    result: dict = {
        "total_components": total,
        "smd_count": smd_count,
        "tht_count": tht_count,
        "complexity_score": score,
        "difficulty_breakdown": difficulty_counts,
        "package_breakdown": dict(sorted(package_breakdown.items(), key=lambda x: -x[1])),
        "unique_footprints": unique_fps,
    }
    if fine_pitch_components:
        result["fine_pitch_components"] = fine_pitch_components

    observations = []
    if score >= 70:
        observations.append(f"High assembly complexity (score {score}/100) — professional assembly recommended")
    elif score >= 40:
        observations.append(f"Moderate assembly complexity (score {score}/100)")
    else:
        observations.append(f"Low assembly complexity (score {score}/100) — hand assembly feasible")
    if difficulty_counts["hard"] > 0:
        observations.append(f"{difficulty_counts['hard']} hard-to-solder component(s) (0201/0402/BGA/QFN)")
    if fine_pitch_components:
        observations.append(f"{len(fine_pitch_components)} fine-pitch component(s) requiring stencil/reflow")
    if observations:
        result["observations"] = observations
    return result


def analyze_usb_compliance(ctx: AnalysisContext,
                           signal_analysis: dict) -> dict:
    """USB spec compliance checks.

    Checks USB-C CC pull-downs, D+/D- series resistors, VBUS protection
    and decoupling, and ESD protection ICs.
    """
    components = ctx.components
    nets = ctx.nets
    pin_net = ctx.pin_net
    comp_lookup = ctx.comp_lookup
    ref_pins = ctx.ref_pins
    is_ground = ctx.is_ground

    # Find USB connectors
    usb_connectors = []
    _seen_refs = set()
    for comp in components:
        if comp["type"] != "connector":
            continue
        ref = comp["reference"]
        if ref in _seen_refs:
            continue
        _seen_refs.add(ref)
        val = comp.get("value", "").upper()
        fp = comp.get("footprint", "").upper()
        lib = comp.get("lib_id", "").upper()
        combined = val + " " + fp + " " + lib
        if "USB" in combined:
            is_type_c = any(k in combined for k in ("USB_C", "USBC", "TYPE-C", "TYPE_C", "TYPEC"))
            usb_connectors.append({
                "ref": ref,
                "value": comp.get("value", ""),
                "is_type_c": is_type_c,
            })

    if not usb_connectors:
        return {}

    checklist = []

    for conn in usb_connectors:
        ref = conn["ref"]
        conn_checks: dict = {
            "connector": ref,
            "value": conn["value"],
            "is_type_c": conn["is_type_c"],
            "checks": {},
        }

        # Gather connector pin nets
        conn_pin_nets: dict[str, str] = {}  # pin_name -> net_name
        for pin_num, (net_name, _) in ref_pins.get(ref, {}).items():
            if net_name:
                # Find pin name
                if net_name in nets:
                    for p in nets[net_name]["pins"]:
                        if p["component"] == ref and p["pin_number"] == pin_num:
                            pname = p.get("pin_name", "").upper()
                            conn_pin_nets[pname] = net_name
                            break

        # --- CC1/CC2 pull-down check (Type-C only) ---
        if conn["is_type_c"]:
            _PD_CONTROLLER_KEYWORDS = (
                "fusb302", "stusb4500", "cypd3177", "husb238",
                "tps65987", "tps65988", "ccg3", "ccg6",
                "max77958", "max20342",
            )

            cc1_net = None
            cc2_net = None
            cc1_resistor = None  # {ref, ohms, to_ground, to_power}
            cc2_resistor = None
            pd_controller = None

            for pname, net_name in conn_pin_nets.items():
                if "CC1" not in pname and "CC2" not in pname:
                    continue
                is_cc1 = "CC1" in pname
                if is_cc1:
                    cc1_net = net_name
                else:
                    cc2_net = net_name

                if net_name not in nets:
                    continue

                # Check for PD controller on this CC net
                if not pd_controller:
                    for p in nets[net_name]["pins"]:
                        ic = comp_lookup.get(p["component"])
                        if not ic or ic["type"] != "ic":
                            continue
                        ic_combined = (ic.get("value", "") + " " + ic.get("lib_id", "")).lower()
                        if any(kw in ic_combined for kw in _PD_CONTROLLER_KEYWORDS):
                            pd_controller = p["component"]
                            break

                # Check for resistors on CC net
                for p in nets[net_name]["pins"]:
                    rc = comp_lookup.get(p["component"])
                    if not rc or rc["type"] != "resistor":
                        continue
                    r_val = parse_value(rc.get("value", ""))
                    if not r_val:
                        continue
                    rn1, _ = pin_net.get((rc["reference"], "1"), (None, None))
                    rn2, _ = pin_net.get((rc["reference"], "2"), (None, None))
                    other = rn2 if rn1 == net_name else rn1
                    r_info = {
                        "ref": rc["reference"],
                        "ohms": r_val,
                        "to_ground": is_ground(other),
                        "to_power": ctx.is_power_net(other) if not is_ground(other) else False,
                    }
                    if is_cc1:
                        cc1_resistor = r_info
                    else:
                        cc2_resistor = r_info

            # Determine role and status
            issues: list[str] = []
            if pd_controller:
                role = "pd_controlled"
            else:
                # Check for sink (5.1k pull-down) vs source (56k pull-up)
                cc1_sink = (cc1_resistor and 4800 <= cc1_resistor["ohms"] <= 5600
                            and cc1_resistor["to_ground"])
                cc2_sink = (cc2_resistor and 4800 <= cc2_resistor["ohms"] <= 5600
                            and cc2_resistor["to_ground"])
                cc1_source = (cc1_resistor and 50000 <= cc1_resistor["ohms"] <= 62000
                              and cc1_resistor["to_power"])
                cc2_source = (cc2_resistor and 50000 <= cc2_resistor["ohms"] <= 62000
                              and cc2_resistor["to_power"])

                if cc1_source or cc2_source:
                    role = "source"
                elif cc1_sink or cc2_sink:
                    role = "sink"
                else:
                    role = "unknown"

                # Validate
                if role == "sink":
                    if not cc1_sink:
                        issues.append("missing_cc1_resistor")
                    if not cc2_sink:
                        issues.append("missing_cc2_resistor")
                    if cc1_sink and cc2_sink:
                        if abs(cc1_resistor["ohms"] - cc2_resistor["ohms"]) > 200:
                            issues.append("asymmetric_cc")
                elif role == "source":
                    if not cc1_source:
                        issues.append("missing_cc1_resistor")
                    if not cc2_source:
                        issues.append("missing_cc2_resistor")
                    if cc1_source and cc2_source:
                        if abs(cc1_resistor["ohms"] - cc2_resistor["ohms"]) > 5000:
                            issues.append("asymmetric_cc")
                elif role == "unknown":
                    # Check for partial/wrong values
                    if cc1_resistor and not cc2_resistor:
                        issues.append("missing_cc2_resistor")
                        issues.append("asymmetric_cc")
                    elif cc2_resistor and not cc1_resistor:
                        issues.append("missing_cc1_resistor")
                        issues.append("asymmetric_cc")
                    elif not cc1_resistor and not cc2_resistor:
                        issues.append("missing_cc1_resistor")
                        issues.append("missing_cc2_resistor")
                    if cc1_resistor and not (4800 <= cc1_resistor["ohms"] <= 5600 or
                                             50000 <= cc1_resistor["ohms"] <= 62000):
                        issues.append("wrong_cc_value")
                    if cc2_resistor and not (4800 <= cc2_resistor["ohms"] <= 5600 or
                                             50000 <= cc2_resistor["ohms"] <= 62000):
                        issues.append("wrong_cc_value")

            cc_status = "pass" if not issues else "fail"
            cc_detail: dict = {
                "cc1_net": cc1_net,
                "cc2_net": cc2_net,
                "cc1_resistor": cc1_resistor,
                "cc2_resistor": cc2_resistor,
                "role": role,
                "pd_controller": pd_controller,
                "status": cc_status,
                "issues": issues,
            }
            conn_checks["usb_c_cc_status"] = cc_detail

            # Legacy check keys for summary compatibility
            if pd_controller:
                conn_checks["checks"]["cc1_pulldown_5k1"] = "pass"
                conn_checks["checks"]["cc2_pulldown_5k1"] = "pass"
            elif role == "source":
                # Source uses pull-ups, not pull-downs — not a failure
                conn_checks["checks"]["cc1_pulldown_5k1"] = "info"
                conn_checks["checks"]["cc2_pulldown_5k1"] = "info"
            else:
                cc1_ok = (cc1_resistor and 4800 <= cc1_resistor["ohms"] <= 5600
                          and cc1_resistor["to_ground"])
                cc2_ok = (cc2_resistor and 4800 <= cc2_resistor["ohms"] <= 5600
                          and cc2_resistor["to_ground"])
                conn_checks["checks"]["cc1_pulldown_5k1"] = "pass" if cc1_ok else "fail"
                conn_checks["checks"]["cc2_pulldown_5k1"] = "pass" if cc2_ok else "fail"

        # --- D+/D- series resistors ---
        dp_net = None
        dm_net = None
        for pname, net_name in conn_pin_nets.items():
            if pname in ("D+", "DP", "D_P", "USB_DP"):
                dp_net = net_name
            elif pname in ("D-", "DM", "D_M", "USB_DM", "DN", "D_N"):
                dm_net = net_name

        dp_series_r = False
        dm_series_r = False
        for data_net, is_dp in [(dp_net, True), (dm_net, False)]:
            if not data_net or data_net not in nets:
                continue
            for p in nets[data_net]["pins"]:
                rc = comp_lookup.get(p["component"])
                if not rc or rc["type"] != "resistor":
                    continue
                r_val = parse_value(rc.get("value", ""))
                if r_val and 20 <= r_val <= 33:
                    if is_dp:
                        dp_series_r = True
                    else:
                        dm_series_r = True

        if dp_net or dm_net:
            conn_checks["checks"]["dp_series_resistor"] = "pass" if dp_series_r else "info"
            conn_checks["checks"]["dm_series_resistor"] = "pass" if dm_series_r else "info"

        # --- VBUS protection and decoupling ---
        vbus_net = None
        for pname, net_name in conn_pin_nets.items():
            if pname in ("VBUS", "V+", "VCC", "VUSB"):
                vbus_net = net_name
                break

        if vbus_net and vbus_net in nets:
            # ESD/TVS on VBUS
            has_esd = False
            has_decoupling = False
            vbus_caps: list[dict] = []
            for p in nets[vbus_net]["pins"]:
                pc = comp_lookup.get(p["component"])
                if not pc:
                    continue
                if pc["type"] == "diode":
                    val_lower = pc.get("value", "").lower()
                    lib_lower = pc.get("lib_id", "").lower()
                    if any(k in val_lower or k in lib_lower
                           for k in ("tvs", "esd", "smaj", "smbj", "p6ke")):
                        has_esd = True
                if pc["type"] == "capacitor":
                    has_decoupling = True
                    cap_val = parse_value(pc.get("value", ""), component_type="capacitor")
                    if cap_val and cap_val > 0:
                        vbus_caps.append({
                            "ref": pc["reference"],
                            "value": pc.get("value", ""),
                            "farads": cap_val,
                        })

            conn_checks["checks"]["vbus_esd_protection"] = "pass" if has_esd else "fail"
            conn_checks["checks"]["vbus_decoupling"] = "pass" if has_decoupling else "fail"

            # USB VBUS capacitor sizing
            # USB 2.0: 1-10µF bulk + 100nF local recommended
            # USB 3.x: 10-120µF for higher power
            # USB PD: up to 100µF for 100W
            if vbus_caps:
                total_uf = sum(c["farads"] for c in vbus_caps) * 1e6
                if total_uf < 1.0:
                    conn_checks["checks"]["vbus_capacitance"] = "warning"
                    conn_checks["vbus_capacitance_detail"] = {
                        "total_uf": round(total_uf, 2),
                        "recommended_min_uf": 1.0,
                        "detail": (f"VBUS decoupling may be insufficient: {total_uf:.1f}\u00b5F total "
                                   f"(recommended \u22651\u00b5F for USB 2.0, \u226510\u00b5F for USB 3.x)"),
                    }
                else:
                    conn_checks["checks"]["vbus_capacitance"] = "pass"
                    conn_checks["vbus_capacitance_detail"] = {
                        "total_uf": round(total_uf, 2),
                    }

        # --- USB ESD protection ICs ---
        esd_ic_found = False
        esd_keywords = ("usblc", "prtr5v", "ip4", "sp0", "tpd", "esd", "pesd",
                        "rclamp", "nup", "lesd")
        for comp_c in components:
            if comp_c["type"] not in ("ic", "diode"):
                continue
            combined_lower = (comp_c.get("value", "") + " " + comp_c.get("lib_id", "")).lower()
            if any(k in combined_lower for k in esd_keywords):
                # Check if it's connected to a USB data net
                for pnum, (net_name, _) in ref_pins.get(comp_c["reference"], {}).items():
                    if net_name in (dp_net, dm_net, vbus_net):
                            esd_ic_found = True
                            break
                if esd_ic_found:
                    break

        conn_checks["checks"]["usb_esd_ic"] = "pass" if esd_ic_found else "info"

        checklist.append(conn_checks)

    # Summarize
    all_checks: dict[str, int] = {"pass": 0, "fail": 0, "info": 0}
    for conn_c in checklist:
        for status in conn_c["checks"].values():
            all_checks[status] = all_checks.get(status, 0) + 1

    observations = []
    if all_checks["fail"] > 0:
        observations.append(f"{all_checks['fail']} USB compliance check(s) failed")
    if all_checks["pass"] > 0:
        observations.append(f"{all_checks['pass']} USB compliance check(s) passed")
    if all_checks["info"] > 0:
        observations.append(f"{all_checks['info']} USB check(s) informational (optional)")

    result: dict = {
        "connectors": checklist,
        "summary": all_checks,
    }
    if observations:
        result["observations"] = observations
    return result


def analyze_inrush_current(ctx: AnalysisContext,
                           signal_analysis: dict) -> dict:
    """Inrush current estimation.

    For each regulator, finds total output capacitance and estimates inrush
    current. Flags rails where output capacitance may cause startup issues.
    """
    components = ctx.components
    nets = ctx.nets
    pin_net = ctx.pin_net
    comp_lookup = ctx.comp_lookup
    ref_pins = ctx.ref_pins
    is_ground = ctx.is_ground
    regulators = signal_analysis.get("power_regulators", [])
    if not regulators:
        return {}

    rails_result = []
    observations = []

    for reg in regulators:
        out_rail = reg.get("output_rail")
        if not out_rail or out_rail not in nets:
            continue

        # Find total output capacitance on this rail
        total_cap_f = 0.0
        output_caps = []
        for p in nets[out_rail]["pins"]:
            comp = comp_lookup.get(p["component"])
            if not comp or comp["type"] != "capacitor":
                continue
            # KH-196: Use pre-computed parsed_values (has component_type context)
            cap_val = ctx.parsed_values.get(comp["reference"])
            if not cap_val or cap_val <= 0:
                continue
            # Check other pin goes to ground
            n1, _ = pin_net.get((comp["reference"], "1"), (None, None))
            n2, _ = pin_net.get((comp["reference"], "2"), (None, None))
            other = n2 if n1 == out_rail else n1
            if is_ground(other):
                total_cap_f += cap_val
                output_caps.append({
                    "ref": comp["reference"],
                    "value": comp["value"],
                    "farads": cap_val,
                })

        if not output_caps:
            continue

        v_out = reg.get("estimated_vout") or _estimate_rail_voltage(out_rail)
        if not v_out or v_out <= 0:
            continue

        rail_entry: dict = {
            "regulator": reg["ref"],
            "output_rail": out_rail,
            "output_voltage": v_out,
            "topology": reg.get("topology", "unknown"),
            "output_caps": output_caps,
            "total_output_capacitance_uF": round(total_cap_f * 1e6, 2),
        }

        # Estimate inrush: I = C * dV/dt
        # For a typical soft-start time of ~1ms for switching regs, ~0.5ms for LDOs
        if reg.get("topology") == "LDO":
            soft_start_s = 0.5e-3
        else:
            soft_start_s = 1.0e-3

        inrush_a = total_cap_f * v_out / soft_start_s
        rail_entry["estimated_inrush_A"] = round(inrush_a, 3)
        rail_entry["assumed_soft_start_ms"] = round(soft_start_s * 1e3, 1)

        # Flag if inrush is high
        if inrush_a > 1.0:
            rail_entry["concern"] = "high_inrush"
            observations.append(
                f"{out_rail}: estimated inrush {inrush_a:.2f}A with "
                f"{total_cap_f * 1e6:.0f}uF output capacitance — "
                f"verify regulator can handle, consider soft-start"
            )
        elif inrush_a > 0.5:
            rail_entry["concern"] = "moderate_inrush"
            observations.append(
                f"{out_rail}: moderate inrush {inrush_a:.2f}A with "
                f"{total_cap_f * 1e6:.0f}uF output capacitance"
            )

        rails_result.append(rail_entry)

    if not rails_result:
        return {}

    result: dict = {"rails": rails_result}
    if observations:
        result["observations"] = observations
    return result


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
            from kicad_utils import is_referenced_as_child
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


def parse_all_sheets(root_path: str, root_tree: list | None = None,
                     symbol_instances_override: dict | None = None):
    """Parse a root schematic and all sub-sheets recursively.

    Performs Phase A of schematic analysis: recursive sheet traversal,
    component extraction with reference remapping, hierarchical label
    namespacing, and sheet coordinate isolation.

    Args:
        root_path: Path to the root .kicad_sch file.
        root_tree: Pre-parsed S-expression tree (avoids re-parsing if caller
            already has it). Parsed from root_path if None.
        symbol_instances_override: If provided, use these symbol_instances
            instead of extracting from root_tree. Required when parsing a
            sub-sheet that lacks (symbol_instances) — pass the root's
            symbol_instances obtained from build_hierarchy_context().

    Returns:
        dict with keys:
            components, wires, labels, junctions, no_connects, lib_symbols,
            text_annotations, bus_elements, title_block, sheets_parsed,
            power_symbols, root_symbol_instances, generator_version,
            file_version
    """
    if root_tree is None:
        root_tree = parse_file(root_path)

    if symbol_instances_override is not None:
        root_symbol_instances = symbol_instances_override
    else:
        root_symbol_instances = extract_symbol_instances(root_tree)

    generator_version = get_value(root_tree, "generator_version") or "unknown"
    file_version = get_value(root_tree, "version") or "unknown"

    all_components = []
    all_wires = []
    all_labels = []
    all_junctions = []
    all_no_connects = []
    all_lib_symbols = {}
    all_text_annotations = []
    all_bus_elements = []
    root_title_block = {}
    sheets_parsed = []

    to_parse = [(str(Path(root_path).resolve()), "")]
    parsed = set()

    while to_parse:
        sheet_path, inst_path = to_parse.pop(0)
        parse_key = (sheet_path, inst_path)
        if parse_key in parsed:
            continue
        parsed.add(parse_key)

        (root, components, wires, labels, junctions, no_connects,
         sub_sheets, lib_symbols, text_annotations, bus_elements, title_block) = \
            parse_single_sheet(sheet_path, instance_uuid=inst_path,
                               symbol_instances=root_symbol_instances)

        sheet_idx = len(sheets_parsed)
        for c in components:
            c["_sheet"] = sheet_idx
        for w in wires:
            w["_sheet"] = sheet_idx
        for l in labels:
            l["_sheet"] = sheet_idx
        for j in junctions:
            j["_sheet"] = sheet_idx
        for nc in no_connects:
            nc["_sheet"] = sheet_idx

        if inst_path:
            for lbl in labels:
                if lbl["type"] == "hierarchical_label":
                    suuid = lbl.pop("_sheet_uuid", None)
                    if suuid:
                        lbl["name"] = inst_path + "/" + suuid + "/" + lbl["name"]
                    else:
                        lbl["name"] = inst_path + "/" + lbl["name"]
        else:
            for lbl in labels:
                if lbl["type"] == "hierarchical_label":
                    suuid = lbl.pop("_sheet_uuid", None)
                    if suuid:
                        lbl["name"] = "/" + suuid + "/" + lbl["name"]

        all_components.extend(components)
        all_wires.extend(wires)
        all_labels.extend(labels)
        all_junctions.extend(junctions)
        all_no_connects.extend(no_connects)
        all_lib_symbols.update(lib_symbols)
        all_text_annotations.extend(text_annotations)
        all_bus_elements.append(bus_elements)
        if sheet_idx == 0:
            root_title_block = title_block
        sheets_parsed.append(sheet_path)

        for sub_path, sub_uuid in sub_sheets:
            sub_resolved = str(Path(sub_path).resolve())
            child_path = inst_path + "/" + sub_uuid if sub_uuid else inst_path
            if (sub_resolved, child_path) not in parsed:
                to_parse.append((sub_resolved, child_path))

    merged_bus = {"bus_wires": [], "bus_entries": [], "bus_aliases": []}
    for be in all_bus_elements:
        merged_bus["bus_wires"].extend(be.get("bus_wires", []))
        merged_bus["bus_entries"].extend(be.get("bus_entries", []))
        merged_bus["bus_aliases"].extend(be.get("bus_aliases", []))

    power_symbols = extract_power_symbols(all_components)

    return {
        "components": all_components,
        "wires": all_wires,
        "labels": all_labels,
        "junctions": all_junctions,
        "no_connects": all_no_connects,
        "lib_symbols": all_lib_symbols,
        "text_annotations": all_text_annotations,
        "bus_elements": merged_bus,
        "title_block": root_title_block,
        "sheets_parsed": sheets_parsed,
        "power_symbols": power_symbols,
        "root_symbol_instances": root_symbol_instances,
        "generator_version": generator_version,
        "file_version": file_version,
    }


def build_hierarchy_context(target_path: str, root_path: str) -> tuple:
    """Build cross-sheet context for a sub-sheet file.

    Parses the full project from root_path, builds the unified net map,
    and extracts cross-sheet component/net information visible through
    the target sheet's hierarchical labels.

    Args:
        target_path: Absolute path to the sub-sheet being analyzed.
        root_path: Absolute path to the root .kicad_sch file.

    Returns:
        (hierarchy_context_dict, root_symbol_instances_dict)

        hierarchy_context_dict contains:
            root_schematic, target_sheet, sheets_in_project,
            cross_sheet_nets, project_power_rails,
            reference_corrections_applied

        root_symbol_instances_dict is used by the caller to fix
        component references on the target sheet.
    """
    from kicad_utils import is_power_net_name

    target_abs = str(Path(target_path).resolve())
    root_abs = str(Path(root_path).resolve())

    # Phase A: parse entire project
    parsed = parse_all_sheets(root_abs)
    all_components = parsed["components"]
    all_labels = parsed["labels"]
    power_symbols = parsed["power_symbols"]
    sheets_parsed = parsed["sheets_parsed"]
    root_symbol_instances = parsed["root_symbol_instances"]

    # Build unified net map for the full project
    nets = build_net_map(
        all_components, parsed["wires"], all_labels,
        power_symbols, parsed["junctions"], parsed["no_connects"])

    # Identify which sheet index corresponds to the target file
    target_sheet_idx = None
    for idx, sp in enumerate(sheets_parsed):
        if str(Path(sp).resolve()) == target_abs:
            target_sheet_idx = idx
            break

    if target_sheet_idx is None:
        # Target file not found in the hierarchy — return minimal context
        return {
            "root_schematic": Path(root_abs).name,
            "target_sheet": Path(target_abs).name,
            "sheets_in_project": [Path(s).name for s in sheets_parsed],
            "cross_sheet_nets": {},
            "project_power_rails": [],
            "reference_corrections_applied": 0,
            "warning": "Target file not found in project hierarchy",
        }, root_symbol_instances

    # Find hierarchical labels belonging to the target sheet
    target_hier_label_names = set()
    for lbl in all_labels:
        if (lbl.get("_sheet") == target_sheet_idx
                and lbl["type"] == "hierarchical_label"):
            target_hier_label_names.add(lbl["name"])

    # Collect known power rails from power symbols
    known_power_rails = set()
    for net_name, net_info in nets.items():
        for p in net_info.get("pins", []):
            if p["component"].startswith("#PWR") or p["component"].startswith("#FLG"):
                known_power_rails.add(net_name)
                break

    # Map component reference -> sheet index
    comp_sheet = {}
    for c in all_components:
        comp_sheet[c["reference"]] = c.get("_sheet", 0)

    # For each hierarchical label net, find components on OTHER sheets
    cross_sheet_nets = {}

    for label_name in sorted(target_hier_label_names):
        # Find which net this label ended up in
        matching_net = None
        for net_name in nets:
            if net_name == label_name:
                matching_net = net_name
                break
        if matching_net is None:
            continue

        net_info = nets[matching_net]
        external_components = []
        connected_sheets = set()

        for pin in net_info.get("pins", []):
            comp_ref = pin["component"]
            if comp_ref.startswith("#PWR") or comp_ref.startswith("#FLG"):
                continue
            sheet_idx = comp_sheet.get(comp_ref, 0)
            if sheet_idx == target_sheet_idx:
                continue  # skip components on the target sheet itself

            comp_data = None
            for c in all_components:
                if c["reference"] == comp_ref:
                    comp_data = c
                    break
            if comp_data is None:
                continue

            sheet_file = (Path(sheets_parsed[sheet_idx]).name
                          if sheet_idx < len(sheets_parsed) else "unknown")
            connected_sheets.add(sheet_file)
            external_components.append({
                "reference": comp_ref,
                "value": comp_data.get("value", ""),
                "lib_id": comp_data.get("lib_id", ""),
                "type": comp_data.get("type", ""),
                "sheet": sheet_file,
            })

        if external_components or connected_sheets:
            # Strip instance path prefix for the display name
            display_name = label_name
            parts = label_name.rsplit("/", 1)
            if len(parts) == 2 and parts[1]:
                display_name = parts[1]

            cross_sheet_nets[display_name] = {
                "external_components": external_components,
                "is_power_rail": is_power_net_name(matching_net, known_power_rails),
                "connected_sheets": sorted(connected_sheets),
                "_namespaced_net": matching_net,
            }

    # Collect project-wide power rails
    project_power_rails = sorted(known_power_rails)

    # Count reference corrections
    correction_count = 0
    si_refs = {si.get("reference", "") for si in root_symbol_instances.values()}
    for c in all_components:
        if c.get("_sheet") == target_sheet_idx and c.get("reference") in si_refs:
            correction_count += 1

    hierarchy_context = {
        "root_schematic": Path(root_abs).name,
        "target_sheet": Path(target_abs).name,
        "target_instance_path": "",
        "sheets_in_project": [Path(s).name for s in sheets_parsed],
        "cross_sheet_nets": cross_sheet_nets,
        "project_power_rails": project_power_rails,
        "reference_corrections_applied": correction_count,
    }

    return hierarchy_context, root_symbol_instances


def enrich_from_hierarchy(signal_analysis: dict, design_analysis: dict,
                          ctx: AnalysisContext) -> None:
    """Annotate detector results with cross-sheet context.

    Called after all detectors run. Adds cross_sheet_* fields to existing
    detections. Modifies signal_analysis and design_analysis dicts in place.
    Tagged with _enriched_from_hierarchy: true for consumer disambiguation.

    Only runs when ctx.hierarchy_context is not None.
    """
    hctx = ctx.hierarchy_context
    if not hctx:
        return

    cross_nets = hctx.get("cross_sheet_nets", {})
    if not cross_nets:
        return

    # Build a lookup: net_name -> cross-sheet info
    # Map the namespaced net names back to local display names
    net_lookup = {}
    for display_name, info in cross_nets.items():
        namespaced = info.get("_namespaced_net", display_name)
        net_lookup[namespaced] = (display_name, info)
        net_lookup[display_name] = (display_name, info)

    # --- Power regulators: add cross-sheet loads ---
    for reg in signal_analysis.get("power_regulators", []):
        output_rail = reg.get("output_rail") or reg.get("output_net")
        if not output_rail:
            continue
        entry = net_lookup.get(output_rail)
        if entry:
            display_name, info = entry
            loads = [
                f"{c['reference']} ({c['value']}, {c['sheet']})"
                for c in info["external_components"]
            ]
            if loads:
                reg["cross_sheet_loads"] = loads
                reg["_enriched_from_hierarchy"] = True

    # --- Bus protocols: add cross-sheet pull-ups ---
    buses = design_analysis.get("buses", {})
    for bus_type in ("i2c", "spi"):
        for bus in buses.get(bus_type, []):
            for signal_key in ("sda_net", "scl_net", "mosi_net", "miso_net", "sck_net"):
                net_name = bus.get(signal_key)
                if not net_name:
                    continue
                entry = net_lookup.get(net_name)
                if entry:
                    display_name, info = entry
                    pullups = [
                        {"reference": c["reference"], "value": c["value"], "sheet": c["sheet"]}
                        for c in info["external_components"]
                        if c.get("type") == "resistor"
                    ]
                    if pullups:
                        bus.setdefault("cross_sheet_pull_ups", []).extend(pullups)
                        bus["_enriched_from_hierarchy"] = True

    # --- Voltage dividers: add cross-sheet load on midpoint ---
    for vd in signal_analysis.get("voltage_dividers", []):
        output_net = vd.get("output_net") or vd.get("mid_net")
        if not output_net:
            continue
        entry = net_lookup.get(output_net)
        if entry:
            display_name, info = entry
            loads = [
                {"reference": c["reference"], "value": c["value"],
                 "type": c["type"], "sheet": c["sheet"]}
                for c in info["external_components"]
            ]
            if loads:
                vd["cross_sheet_load"] = loads
                vd["_enriched_from_hierarchy"] = True

    # --- ESD coverage: add cross-sheet protection ---
    for entry in signal_analysis.get("esd_coverage_audit", []):
        for pin_net in entry.get("unprotected_nets", []):
            xnet = net_lookup.get(pin_net)
            if xnet:
                display_name, info = xnet
                esd_devices = [
                    {"reference": c["reference"], "value": c["value"], "sheet": c["sheet"]}
                    for c in info["external_components"]
                    if c.get("type") in ("tvs", "esd", "protection")
                ]
                if esd_devices:
                    entry.setdefault("cross_sheet_protection", []).extend(esd_devices)
                    entry["_enriched_from_hierarchy"] = True


def analyze_schematic(path: str, project_root: str | None = None,
                      no_hierarchy: bool = False) -> dict:
    """Main analysis function. Returns complete structured data.

    For hierarchical designs (multi-sheet), recursively parses all sub-sheets
    and merges connectivity. Global and hierarchical labels connect nets across
    sheets.

    If *path* is a sub-sheet (not the root), the function auto-discovers the
    root schematic via ``.kicad_pro`` and redirects to a full-project analysis.
    The result includes ``_redirected_from`` with the original filename.  If the
    file is not part of any active sheet tree, ``_stale_file_warning`` is set.

    Args:
        path: Path to .kicad_sch file to analyze.
        project_root: Optional path to root .kicad_sch for hierarchy context.
            Auto-discovered from .kicad_pro if not provided.
        no_hierarchy: If True, skip hierarchy auto-discovery entirely.
            Useful when analysing a sub-sheet in isolation.
    """
    # Detect legacy format
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        first_line = f.readline().strip()

    if first_line.startswith("EESchema"):
        return parse_legacy_schematic(path)

    # Parse root sheet and all sub-sheets recursively via parse_all_sheets().
    root_tree = parse_file(path)

    is_sub = detect_sub_sheet(root_tree, file_path=path)
    hierarchy_ctx = None
    hierarchy_warning = None

    if is_sub and not no_hierarchy:
        from kicad_utils import discover_root_schematic
        root_path = project_root or discover_root_schematic(path)
        if root_path:
            # Redirect: analyze the full project from the root schematic.
            # This gives a complete picture (all sheets, all components)
            # instead of analyzing a sub-sheet in isolation.
            original_basename = os.path.basename(path)
            root_basename = os.path.basename(root_path)
            print(f"Note: {original_basename} is a sub-sheet — analyzing "
                  f"full project from root {root_basename}",
                  file=sys.stderr)
            result = analyze_schematic(root_path, no_hierarchy=True)
            result["_redirected_from"] = original_basename

            # Stale file check: is the original file in the project tree?
            target_abs = str(Path(path).resolve())
            in_project = any(
                str(Path(s).resolve()) == target_abs
                for s in result.get("sheets", []))
            if not in_project:
                result["_stale_file_warning"] = (
                    f"{original_basename} is not referenced by any sheet "
                    f"in the project ({root_basename}). It may be a stale "
                    f"or abandoned child schematic.")
                print(f"Warning: {original_basename} is not part of the "
                      f"active project sheet tree", file=sys.stderr)

            return result
        else:
            hierarchy_warning = (
                "File appears to be a sub-sheet (has hierarchical labels but "
                "no symbol_instances). No root schematic found. Component "
                "references may be incomplete. Use --project-root for full "
                "hierarchy analysis."
            )
    elif is_sub and no_hierarchy:
        hierarchy_warning = (
            "File appears to be a sub-sheet but hierarchy discovery is "
            "disabled (--no-hierarchy). Component references may be incomplete."
        )

    parsed = parse_all_sheets(path, root_tree=root_tree)

    # --- top_level_sheets support (Altium flat multi-page imports) ---
    # KiCad's Altium importer registers all pages as top_level_sheets in
    # .kicad_pro instead of creating (sheet ...) hierarchy references.
    # Trigger only when the root has zero (sheet ...) nodes — checking
    # len(sheets_parsed) alone is fragile because parse_all_sheets silently
    # drops (sheet ...) refs whose files are missing, which would otherwise
    # cause us to mix in unrelated top_level_sheets. Runs regardless of
    # no_hierarchy so the sub-sheet redirect path still picks up peers.
    if (len(parsed.get("sheets_parsed", [])) <= 1
            and find_first(root_tree, "sheet") is None):
        pro = load_kicad_pro(path)
        if pro:
            tls = pro.get("schematic", {}).get("top_level_sheets", [])
            if len(tls) > 1:
                root_abs = str(Path(path).resolve())
                extra_sheets = []
                seen = {root_abs}
                for entry in tls:
                    fn = entry.get("filename", "")
                    if not fn:
                        continue
                    sheet_path = os.path.join(os.path.dirname(path), fn)
                    if not os.path.isfile(sheet_path):
                        continue
                    abs_path = str(Path(sheet_path).resolve())
                    if abs_path in seen:
                        continue
                    seen.add(abs_path)
                    extra_sheets.append(abs_path)

                if extra_sheets:
                    print(f"Note: discovered {len(extra_sheets)} additional "
                          f"top-level sheets from .kicad_pro",
                          file=sys.stderr)
                    sym_inst = parsed.get("root_symbol_instances", {})
                    base_idx = len(parsed["sheets_parsed"])
                    for sheet_path in extra_sheets:
                        try:
                            (_, comps, wires, labels, junctions,
                             no_connects, _, lib_syms, text_annot,
                             bus_elems, title_blk) = \
                                parse_single_sheet(
                                    sheet_path,
                                    symbol_instances=sym_inst)
                        except Exception as exc:
                            print(f"Warning: failed to parse "
                                  f"{os.path.basename(sheet_path)}: {exc}",
                                  file=sys.stderr)
                            continue
                        sheet_idx = base_idx
                        base_idx += 1
                        for c in comps:
                            c["_sheet"] = sheet_idx
                        for w in wires:
                            w["_sheet"] = sheet_idx
                        for lb in labels:
                            lb["_sheet"] = sheet_idx
                        for j in junctions:
                            j["_sheet"] = sheet_idx
                        for nc in no_connects:
                            nc["_sheet"] = sheet_idx
                        parsed["components"].extend(comps)
                        parsed["wires"].extend(wires)
                        parsed["labels"].extend(labels)
                        parsed["junctions"].extend(junctions)
                        parsed["no_connects"].extend(no_connects)
                        parsed["lib_symbols"].update(lib_syms)
                        parsed["text_annotations"].extend(text_annot)
                        for bk, bv in bus_elems.items():
                            if isinstance(bv, list):
                                parsed["bus_elements"].setdefault(bk, []).extend(bv)
                            elif isinstance(bv, dict):
                                parsed["bus_elements"].setdefault(bk, {}).update(bv)
                        parsed["sheets_parsed"].append(sheet_path)
                    # Power symbols were extracted from root-sheet components
                    # only; refresh from the merged list so peer-sheet ones are
                    # included.
                    parsed["power_symbols"] = extract_power_symbols(
                        parsed["components"])

    all_components = parsed["components"]
    all_wires = parsed["wires"]
    all_labels = parsed["labels"]
    all_junctions = parsed["junctions"]
    all_no_connects = parsed["no_connects"]
    all_lib_symbols = parsed["lib_symbols"]
    all_text_annotations = parsed["text_annotations"]
    merged_bus = parsed["bus_elements"]
    root_title_block = parsed["title_block"]
    sheets_parsed = parsed["sheets_parsed"]
    power_symbols = parsed["power_symbols"]
    root_symbol_instances = parsed["root_symbol_instances"]
    generator_version = parsed["generator_version"]
    file_version = parsed["file_version"]

    # Build net map across all sheets
    nets = build_net_map(all_components, all_wires, all_labels, power_symbols, all_junctions,
                         all_no_connects)

    # Generate BOM
    bom = generate_bom(all_components)

    # Build pin-to-net map once, shared by all analysis functions
    pin_net = build_pin_to_net_map(nets)

    # Build shared analysis context (replaces repeated comp_lookup / parsed_values / known_power_rails)
    ctx = AnalysisContext(
        components=all_components,
        nets=nets,
        lib_symbols=all_lib_symbols,
        pin_net=pin_net,
        no_connects=all_no_connects,
        generator_version=generator_version,
        hierarchy_context=hierarchy_ctx,
    )
    from netlist_queries import NetlistQueries
    ctx.nq = NetlistQueries(ctx)

    # Identify subcircuits
    subcircuits = identify_subcircuits(ctx)

    # Detailed IC pinout analysis for datasheet cross-referencing
    ic_analysis = analyze_ic_pinouts(ctx)

    # Analyze connectivity for issues
    connectivity_issues = analyze_connectivity(all_components, nets, all_no_connects)

    # Signal path and filter analysis
    signal_analysis = analyze_signal_paths(ctx)

    # Deep EE analysis: power domains, buses, differential pairs, ERC
    design_analysis = analyze_design_rules(ctx, results_in=signal_analysis)

    # Cross-sheet enrichment (no-op when hierarchy_context is None)
    enrich_from_hierarchy(signal_analysis, design_analysis, ctx)

    # ---- New Tier 1 + Tier 2 analyses ----

    # Reuse known_power_rails from context for PWR_FLAG audit
    known_power_rails = ctx.known_power_rails

    annotation_issues = check_annotation_completeness(all_components)
    label_shape_warnings = validate_label_shapes(all_labels, nets)
    pwr_flag_warnings = audit_pwr_flags(all_components, nets, known_power_rails)
    fp_filter_warnings = validate_footprint_filters(all_components, all_lib_symbols)
    sourcing_audit = audit_sourcing_fields(all_components)
    datasheet_coverage_findings = audit_datasheet_coverage(
        all_components, str(Path(path).parent))
    sourcing_gate_findings = audit_sourcing_gate(all_components)
    alternate_pins = summarize_alternate_pins(all_lib_symbols)
    ground_domains = classify_ground_domains(nets, all_components)
    bus_topology = analyze_bus_topology(merged_bus, all_labels, nets)
    wire_geometry = analyze_wire_geometry(all_wires)
    sim_readiness = check_simulation_readiness(all_components, all_lib_symbols)
    property_issues = audit_property_patterns(all_components)
    placement = spatial_clustering(all_components)
    pin_coverage = verify_pin_coverage(all_components, all_lib_symbols)
    instance_issues = check_instance_consistency(all_components)
    hier_label_analysis = validate_hierarchical_labels(all_labels, nets)
    generic_sym_warnings = check_generic_transistor_symbols(all_components, str(path))

    # ---- Tier 3: High-level design analyses ----
    pdn_analysis = analyze_pdn_impedance(ctx, signal_analysis)
    sleep_current = analyze_sleep_current(ctx, signal_analysis)
    voltage_derating = analyze_voltage_derating(ctx, signal_analysis,
                                                 project_dir=str(Path(path).parent))
    power_budget = analyze_power_budget(ctx, signal_analysis)
    power_sequencing = analyze_power_sequencing(ctx, signal_analysis)
    bom_optimization = analyze_bom_optimization(all_components)
    test_coverage = analyze_test_coverage(ctx)
    assembly_complexity = analyze_assembly_complexity(all_components)
    usb_compliance = analyze_usb_compliance(ctx, signal_analysis)
    inrush_analysis = analyze_inrush_current(ctx, signal_analysis)
    protocol_compliance = analyze_protocol_compliance(all_components, nets, design_analysis, signal_analysis, pin_net)

    # Add parsed numeric values to all passive components and category field
    for comp in all_components:
        comp["category"] = comp.get("type")
        if comp["type"] in ("resistor", "capacitor", "inductor", "ferrite_bead", "crystal"):
            pv = parse_value(comp.get("value", ""), component_type=comp["type"])
            if pv is not None:
                comp["parsed_value"] = pv

    # Statistics
    stats = compute_statistics(all_components, nets, bom, all_wires, all_no_connects)

    # Annotate __unnamed_N nets with a human-readable display_name when
    # exactly one named IC pin is on them. Does NOT rename the net —
    # only adds a display hint consumers can use in reports.
    _IC_TYPES = {"ic", "regulator", "opamp", "microcontroller", "memory",
                 "connector_ic", "analog_ic", "mixed_signal",
                 "power_management", "interface"}
    _comp_by_ref = {c.get("reference"): c for c in all_components}
    for _net_name, _info in nets.items():
        if not _net_name.startswith("__unnamed_"):
            continue
        if _info.get("display_name"):
            continue
        _named_ic_pin = None
        for _p in _info.get("pins", []) or []:
            _pname = (_p.get("pin_name") or "").strip()
            if not _pname or _pname in ("~", "NC"):
                continue
            _ref = _p.get("component") or ""
            _comp = _comp_by_ref.get(_ref)
            if not _comp:
                continue
            _ctype = (_comp.get("type") or _comp.get("category") or "").lower()
            if _ctype not in _IC_TYPES:
                continue
            if _named_ic_pin is None:
                _named_ic_pin = (_ref, _pname)
            else:
                # Multiple named IC pins — ambiguous, skip annotation.
                _named_ic_pin = None
                break
        if _named_ic_pin:
            _info["display_name"] = f"{_named_ic_pin[0]}.{_named_ic_pin[1]}"

    # Load .kicad_pro for project metadata (KiCad 6+)
    pro = load_kicad_pro(str(path))
    project_settings = {}
    if pro:
        text_vars = extract_pro_text_variables(pro)
        if text_vars:
            project_settings['text_variables'] = text_vars
            # Enrich title block with text variables where empty
            if root_title_block:
                for tb_key, var_name in (('title', 'TITLE'),
                                          ('company', 'COMPANY'),
                                          ('revision', 'REVISION')):
                    if not root_title_block.get(tb_key) and var_name in text_vars:
                        root_title_block[tb_key] = text_vars[var_name]

    # Library tables
    lib_tables = load_lib_tables(str(path))
    if lib_tables.get('symbol_libs'):
        project_settings['symbol_libs'] = lib_tables['symbol_libs']

    # Enrich components with pin-to-net mapping for downstream consumers
    # KH-211: Include __unnamed_* nets so that connections through unlabelled
    # wires (common in hierarchical sub-sheets) appear in pin_nets.
    _pin_nets: dict[str, dict[str, str]] = {}
    for _net_name, _net_info in nets.items():
        if isinstance(_net_info, dict):
            for _p in _net_info.get('pins', []):
                _comp_ref = _p.get('component', '')
                _pin_num = _p.get('pin_number', '')
                if _comp_ref and _pin_num:
                    _pin_nets.setdefault(_comp_ref, {})[_pin_num] = _net_name
    for _comp in all_components:
        _all_pn = _pin_nets.get(_comp.get('reference', ''), {})
        _valid = _comp.get("_unit_pins")
        if _valid and len(_all_pn) > len(_valid):
            _comp['pin_nets'] = {k: v for k, v in _all_pn.items() if k in _valid}
        else:
            _comp['pin_nets'] = _all_pn
        _comp.pop("_unit_pins", None)

    # Flatten signal_analysis: all list values become findings, dict values promote to top level
    findings = []
    for _sa_key, _sa_value in signal_analysis.items():
        if isinstance(_sa_value, list):
            _det_name = f"detect_{_sa_key}"
            for _item in _sa_value:
                if isinstance(_item, dict) and "detector" not in _item:
                    _item["detector"] = _det_name
            findings.extend(_sa_value)

    # Datasheet-coverage audit findings (DS-001 / DS-002 / DS-003) surface
    # up front so reviewers can't miss the "this is a consistency-only
    # check" banner when no manufacturer evidence is available.
    if datasheet_coverage_findings:
        findings.extend(datasheet_coverage_findings)

    if sourcing_gate_findings:
        findings.extend(sourcing_gate_findings)

    # NT-001 — single-pin nets weighted by pin type (Task 3)
    nt_findings = connectivity_issues.get("single_pin_net_findings", [])
    if nt_findings:
        findings.extend(nt_findings)

    # Build severity summary
    sev_counts = {"error": 0, "warning": 0, "info": 0}
    for _f in findings:
        _sev = _f.get("severity", "info").lower() if isinstance(_f, dict) else "info"
        if _sev in ("critical", "high"):
            sev_counts["error"] += 1
        elif _sev in ("medium", "warning"):
            sev_counts["warning"] += 1
        else:
            sev_counts["info"] += 1

    # Deterministic order so repeated runs produce byte-identical output
    # (KH-316).  Sort key: (rule_id, detector, first_component, first_net, summary).
    sort_findings(findings)

    result = {
        "analyzer_type": "schematic",
        "schema_version": "1.3.0",
        "summary": {"total_findings": len(findings), "by_severity": sev_counts},
        "trust_summary": compute_trust_summary(findings, bom=bom),
        "file": str(path),
        "kicad_version": generator_version,
        "file_version": file_version,
        "title_block": root_title_block,
        "statistics": stats,
        "findings": findings,
        "bom": bom,
        "components": [
            {k: v for k, v in c.items() if k != "pins"}
            for c in all_components
            if c["type"] not in ("power_symbol", "power_flag", "flag")
        ],
        "nets": nets,
        "subcircuits": subcircuits,
        "ic_pin_analysis": ic_analysis,
        "design_analysis": design_analysis,
        "connectivity_issues": connectivity_issues,
        "labels": all_labels,
        "no_connects": all_no_connects,
        "power_symbols": power_symbols,
        "annotation_issues": annotation_issues,
        "label_shape_warnings": label_shape_warnings,
        "pwr_flag_warnings": pwr_flag_warnings,
        "footprint_filter_warnings": fp_filter_warnings,
        "sourcing_audit": sourcing_audit,
        "ground_domains": ground_domains,
        "bus_topology": bus_topology,
        "wire_geometry": wire_geometry,
        "simulation_readiness": sim_readiness,
        "property_issues": property_issues,
        "placement_analysis": placement,
        "hierarchical_labels": hier_label_analysis,
    }

    # Promote dict values from signal_analysis to top level (rail_voltages, net_classifications, etc.)
    for _sa_key, _sa_value in signal_analysis.items():
        if isinstance(_sa_value, dict):
            result[_sa_key] = _sa_value

    # Only include non-empty optional sections
    if all_text_annotations:
        result["text_annotations"] = all_text_annotations
    if alternate_pins:
        result["alternate_pin_summary"] = alternate_pins
    if pin_coverage:
        result["pin_coverage_warnings"] = pin_coverage
    if instance_issues:
        result["instance_consistency_warnings"] = instance_issues
    if generic_sym_warnings:
        result["generic_symbol_warnings"] = generic_sym_warnings
    if pdn_analysis:
        result["pdn_impedance"] = pdn_analysis
    if sleep_current:
        result["sleep_current_audit"] = sleep_current
    if voltage_derating:
        result["voltage_derating"] = voltage_derating
    if power_budget:
        result["power_budget"] = power_budget
    if power_sequencing:
        result["power_sequencing"] = power_sequencing
    if bom_optimization:
        result["bom_optimization"] = bom_optimization
    if test_coverage:
        result["test_coverage"] = test_coverage
    if assembly_complexity:
        result["assembly_complexity"] = assembly_complexity
    if usb_compliance:
        result["usb_compliance"] = usb_compliance
    if inrush_analysis:
        result["inrush_analysis"] = inrush_analysis
    if protocol_compliance:
        result["protocol_compliance"] = protocol_compliance

    if len(sheets_parsed) > 1:
        result["sheets"] = sheets_parsed
    if project_settings:
        result["project_settings"] = project_settings
    if hierarchy_ctx:
        result["hierarchy_context"] = hierarchy_ctx
    if hierarchy_warning:
        result["hierarchy_warning"] = hierarchy_warning

    # --- Missing information section ---
    # Aggregates data gaps so downstream consumers can separate
    # "missing data" from "actual design issues"
    missing_info = {}
    # Missing MPNs and footprints (from statistics)
    missing_mpn = stats.get("missing_mpn", [])
    if missing_mpn:
        missing_info["missing_mpn"] = missing_mpn
    missing_fp = stats.get("missing_footprint", [])
    if missing_fp:
        missing_info["missing_footprint"] = missing_fp
    # Components with MPN but no datasheet URL
    missing_ds = [c["reference"] for c in all_components
                  if c.get("mpn") and not c.get("datasheet")
                  and c["type"] not in ("power_symbol", "power_flag", "flag")]
    if missing_ds:
        missing_info["missing_datasheet"] = sorted(missing_ds)
    # Regulators with heuristic Vref (no datasheet lookup available)
    sig = signal_analysis or {}
    heuristic_vref = [r["ref"] for r in sig.get("power_regulators", [])
                      if r.get("vref_source") == "heuristic"]
    if heuristic_vref:
        missing_info["heuristic_vref"] = heuristic_vref
    if missing_info:
        result["missing_info"] = missing_info

    # BOM lock verification (production readiness)
    _bom_real = [c for c in all_components
                 if c.get("type") not in ("power_symbol", "power_flag", "flag",
                                           "mounting_hole", "fiducial",
                                           "test_point", "graphic")
                 and not c.get("reference", "").startswith("#")
                 and c.get("in_bom", True) and not c.get("dnp", False)]
    # Deduplicate multi-unit symbols
    _bom_seen = set()
    _bom_dedup = []
    for _bc in _bom_real:
        if _bc["reference"] not in _bom_seen:
            _bom_seen.add(_bc["reference"])
            _bom_dedup.append(_bc)
    _bom_real = _bom_dedup
    _bom_no_mpn = [c["reference"] for c in _bom_real if not c.get("mpn")]
    _bom_generic = [c["reference"] for c in _bom_real
                    if c.get("value", "") in ("", "~", "DNP", "DNF", "NC")
                    or c.get("value", "").startswith("?")]
    _bom_lock_pct = round((1 - len(_bom_no_mpn) / max(len(_bom_real), 1)) * 100)
    result["bom_lock"] = {
        "total_bom_components": len(_bom_real),
        "components_with_mpn": len(_bom_real) - len(_bom_no_mpn),
        "missing_mpn": _bom_no_mpn[:20],
        "missing_mpn_count": len(_bom_no_mpn),
        "generic_values": _bom_generic[:10],
        "lock_pct": _bom_lock_pct,
        "status": "pass" if _bom_lock_pct >= 95 else
                  "warning" if _bom_lock_pct >= 70 else "fail",
    }

    # Add stable detection IDs for diff matching
    from detection_schema import compute_detection_id as _compute_det_id
    for _det_type, _dets in signal_analysis.items():
        if isinstance(_dets, list):
            for _det in _dets:
                if isinstance(_det, dict):
                    _det["detection_id"] = _compute_det_id(_det, _det_type)

    return result


def _get_schema():
    """Return JSON output schema description for --schema flag."""
    return {
        "analyzer_type": "string — always 'schematic'",
        "schema_version": "string — semver (currently '1.3.0')",
        "summary": {"total_findings": "int", "by_severity": {"error": "int", "warning": "int", "info": "int"}},
        "trust_summary": {
            "total_findings": "int",
            "trust_level": "string — 'high' | 'mixed' | 'low'",
            "by_confidence": "{deterministic: int, heuristic: int, datasheet-backed: int}",
            "by_evidence_source": "{datasheet|topology|heuristic_rule|symbol_footprint|bom|geometry|api_lookup: int}",
            "provenance_coverage_pct": "float — % of findings with provenance metadata",
            "bom_coverage": "{mpn_pct: float, datasheet_pct: float} — MPN/datasheet coverage excluding power symbols",
        },
        "file": "string — input file path",
        "kicad_version": "string — generator version",
        "file_version": "string",
        "title_block": {"title": "string", "date": "string", "rev": "string",
                        "company": "string", "comments": "{number: string}"},
        "statistics": {
            "total_components": "int", "unique_parts": "int", "dnp_parts": "int",
            "total_nets": "int", "total_wires": "int", "total_no_connects": "int",
            "component_types": "{type_name: count}", "power_rails": "[string]",
            "missing_mpn": "[reference_string]", "missing_footprint": "[reference_string]",
        },
        "findings": "[{detector, rule_id, severity, confidence, evidence_source, summary, category, components, nets, pins, recommendation, ...detection-specific fields}] — flat list of all findings",
        "bom": "[{value, footprint, mpn, manufacturer, digikey, mouser, lcsc, element14, datasheet, description, references: [string], quantity: int, dnp: bool, type}]",
        "components": "[{reference, value, lib_id, footprint, datasheet, description, mpn, manufacturer, digikey, mouser, lcsc, element14, x: float, y: float, angle: float, mirror_x: bool, mirror_y: bool, unit: int|null, uuid, in_bom: bool, dnp: bool, on_board: bool, type, keywords, pins: [{number, name, type}], parsed_value: {value: float, unit: string}}]",
        "nets": "{net_name: {name, pins: [{component, pin_number, pin_name, pin_type}], point_count: int}}",
        "subcircuits": "[{reference, path, sheet_name, sheet_file, instances: int}]",
        "ic_pin_analysis": "[{reference, value, pin_summary: {pin_number: {name, type, connected: bool, net}}, function, notes: [string]}]",
        "rail_voltages": "{net_name: voltage_float} — promoted from signal_analysis",
        "net_classifications": "{net_name: {type, ...}} — promoted from signal_analysis",
        "design_analysis": {
            "net_classification": "{net: {type: 'power'|'ground'|'data'|...}}",
            "power_domains": "{ic_power_rails: {ref: {voltage, rail_net}}, ...}",
            "cross_domain_signals": "[signals crossing voltage domains]",
            "bus_analysis": "{i2c|spi|uart|can|sdio|usb: [bus_instances]}",
            "differential_pairs": "[{positive, negative, type: 'USB'|'LVDS'|'Ethernet'|'CAN'|'generic', shared_ics: [ref], has_esd: bool, series_resistors: [ref], termination: [{ref,value,ohms}]}]",
            "erc_warnings": "[string]",
            "passive_warnings": "[string]",
        },
        "connectivity_issues": {"single_pin_nets": "[net_name]", "multi_driver_nets": "[net_name]", "floating_nets": "[net_name]"},
        "_optional_sections": "power_budget, power_sequencing, pdn_impedance, sleep_current_audit, usb_compliance, inrush_analysis, bom_optimization, test_coverage, assembly_complexity, sheets (multi-sheet only), missing_info, bom_lock, project_settings",
        "hierarchy_context": "OPTIONAL — only present when analyzing a sub-sheet with hierarchy context resolved. Shape: {root_schematic, target_sheet, sheets_in_project: [string], cross_sheet_nets: {label: {external_components, is_power_rail, connected_sheets}}, project_power_rails: [string], reference_corrections_applied: int}",
        "hierarchy_warning": "OPTIONAL string — present when sub-sheet detected without root",
        "_redirected_from": "OPTIONAL string — original filename when sub-sheet was redirected to root",
        "_stale_file_warning": "OPTIONAL string — present when input file is not in the project sheet tree",
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="KiCad Schematic Analyzer")
    parser.add_argument("schematic", nargs="?",
                        help="Path to .kicad_sch, .kicad_pro, or project directory")
    parser.add_argument("--output", "-o", help="Output JSON file (default: stdout)")
    parser.add_argument("--compact", action="store_true", help="Compact JSON output")
    parser.add_argument("--schema", action="store_true",
                        help="Print JSON output schema and exit")
    parser.add_argument("--config", default=None,
                        help="Path to .kicad-happy.json project config file")
    parser.add_argument("--project-root", default=None,
                        help="Root .kicad_sch for hierarchy context (auto-discovered if omitted)")
    parser.add_argument("--no-hierarchy", action="store_true",
                        help="Disable hierarchy auto-discovery (treat file as standalone root)")
    parser.add_argument("--lifecycle", action="store_true",
                        help="Run lifecycle/obsolescence audit (requires network + API keys)")
    parser.add_argument("--analysis-dir", default=None,
                        help="Write output to analysis cache directory (timestamped runs)")
    parser.add_argument("--text", action="store_true",
                        help="Print human-readable text report to stdout")
    parser.add_argument('--stage', default=None,
                        choices=['schematic', 'layout', 'pre_fab', 'bring_up'],
                        help='Filter findings by review stage')
    parser.add_argument('--audience', default=None,
                        choices=['designer', 'reviewer', 'manager'],
                        help='Audience level for summaries and --text output')
    args = parser.parse_args()

    if args.schema:
        print(json.dumps(_get_schema(), indent=2))
        sys.exit(0)

    if not args.schematic:
        parser.error("the following arguments are required: schematic")

    # Resolve .kicad_pro or directory to the root .kicad_sch
    from kicad_utils import resolve_project_input
    try:
        resolved, note = resolve_project_input(args.schematic, '.kicad_sch')
        if note:
            print(f"Note: {note} → {os.path.basename(resolved)}",
                  file=sys.stderr)
        args.schematic = resolved
    except FileNotFoundError as e:
        parser.error(str(e))

    # Load project config (for project settings — suppressions applied to
    # EMC/thermal findings, not schematic warnings which lack rule_ids)
    try:
        from project_config import load_config_from_path, load_config
        if args.config:
            config = load_config_from_path(args.config)
        else:
            config = load_config(str(Path(args.schematic).parent))
    except ImportError:
        config = {"version": 1, "project": {}, "suppressions": []}

    result = analyze_schematic(args.schematic,
                               project_root=args.project_root,
                               no_hierarchy=args.no_hierarchy)

    # Attach project config summary to output for downstream consumers
    project = config.get("project", {})
    if project:
        result["project_config"] = project

    # Resolve design intent for downstream consumers
    try:
        from project_config import resolve_design_intent
        sch_data_for_intent = {
            'components': result.get('components', []),
            'title_block': result.get('title_block', {}),
        }
        intent = resolve_design_intent(config,
                                        schematic_data=sch_data_for_intent)
        result['design_intent'] = intent

        # Gate CERT-001 blanket certification suggestions on target_market.
        # For hobby projects, "EU EMC compliance required" and the fallback
        # FCC Part 15 Subpart B fire as noise on every board.  Keep specific
        # triggers (RF, wireless, battery, USB, ethernet, HV) — those
        # represent real circuit hazards regardless of market.
        target_market = (intent or {}).get('target_market', 'hobby')
        if target_market == 'hobby':
            _blanket_cert_prefixes = (
                'FCC Part 15 Subpart B',
                'CISPR 32 / CE EMC Directive',
            )
            result['findings'] = [
                f for f in result.get('findings', [])
                if not (isinstance(f, dict)
                        and f.get('rule_id') == 'CERT-001'
                        and any(str(f.get('standard', '')).startswith(p)
                                for p in _blanket_cert_prefixes))
            ]
    except ImportError:
        pass

    # Apply power_rails config (ignore/flag/voltage_overrides)
    try:
        from project_config import apply_power_rails_config
        stats = result.get('statistics', {})
        rv = result.get('rail_voltages', {})
        pr = stats.get('power_rails', [])
        if rv or pr:
            filtered_rv, filtered_pr, flagged = apply_power_rails_config(
                rv, pr, config)
            result['rail_voltages'] = filtered_rv
            stats['power_rails'] = filtered_pr
            if flagged:
                result['flagged_rails'] = flagged
    except (ImportError, Exception):
        pass

    if args.lifecycle:
        try:
            from lifecycle_audit import audit_bom
            project_dir = str(Path(args.schematic).parent)
            lifecycle = audit_bom(result, project_dir=project_dir)
            if lifecycle and lifecycle.get("components_checked", 0) > 0:
                result["lifecycle_audit"] = lifecycle
                print(f"Lifecycle: {lifecycle.get('lifecycle_summary', {})}", file=sys.stderr)
            else:
                print("Lifecycle: no components with MPNs to check", file=sys.stderr)
        except ImportError:
            print("Warning: lifecycle_audit.py not found", file=sys.stderr)
        except (OSError, ValueError, TypeError, KeyError) as e:
            print(f"Warning: lifecycle audit failed: {e}", file=sys.stderr)

    # Datasheet verification — cross-check extracted datasheet data against schematic
    try:
        # Import datasheet_verify from the datasheets skill
        import os as _os, sys as _sys
        _ds_scripts = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                                    '..', '..', 'datasheets', 'scripts')
        if _os.path.isdir(_ds_scripts):
            _sys.path.insert(0, _os.path.abspath(_ds_scripts))
        from datasheet_verify import run_datasheet_verification
        project_dir = str(Path(args.schematic).parent)
        ds_verify = run_datasheet_verification(result, project_dir=project_dir)
        if ds_verify.get("findings") or ds_verify.get("summary", {}).get("ics_with_extractions", 0) > 0:
            result["datasheet_verification"] = ds_verify
    except ImportError:
        pass
    except (OSError, ValueError, TypeError, KeyError) as e:
        result["datasheet_verification"] = {
            "findings": [],
            "summary": {"error": str(e)},
        }

    from output_filters import apply_output_filters
    apply_output_filters(result, args.stage, args.audience)

    # Recompute summary + trust_summary from the final findings list — post-
    # filters (CERT-001 hobby gating, power_rails config, lifecycle audit,
    # datasheet verification, output_filters stage filter) can mutate
    # findings[] after the initial summary was built. Keep the envelope
    # consistent with what actually ships in findings[].
    _final_findings = result.get('findings', []) if isinstance(result.get('findings'), list) else []
    _sev_counts = {"error": 0, "warning": 0, "info": 0}
    for _f in _final_findings:
        if not isinstance(_f, dict):
            continue
        _s = str(_f.get('severity', 'info')).lower()
        if _s in _sev_counts:
            _sev_counts[_s] += 1
        else:
            _sev_counts['info'] += 1
    if isinstance(result.get('summary'), dict):
        result['summary']['total_findings'] = len(_final_findings)
        result['summary']['by_severity'] = _sev_counts
    try:
        from finding_schema import compute_trust_summary
        result['trust_summary'] = compute_trust_summary(_final_findings, bom=result.get('bom'))
    except (ImportError, Exception):
        pass

    if args.text:
        from output_filters import format_text
        print(format_text(result.get('findings', []), args.audience or 'designer', args.stage))
        sys.exit(0)

    indent = None if args.compact else 2
    output = json.dumps(result, indent=indent, default=str)

    if args.analysis_dir:
        import tempfile
        from analysis_cache import (ensure_analysis_dir, hash_source_file,
                                     should_create_new_run, create_run,
                                     overwrite_current, CANONICAL_OUTPUTS,
                                     resolve_analysis_dir)

        project_dir = str(Path(args.schematic).parent)
        analysis_dir = resolve_analysis_dir(args.analysis_dir)

        # Find .kicad_pro for manifest
        pro_file = ""
        try:
            for f in os.listdir(project_dir):
                if f.endswith(".kicad_pro"):
                    pro_file = f
                    break
        except OSError:
            pass

        # Ensure the target directory exists with manifest
        os.makedirs(analysis_dir, exist_ok=True)
        from analysis_cache import MANIFEST_FILENAME, save_manifest, _empty_manifest, GITIGNORE_CONTENT
        manifest_path = os.path.join(analysis_dir, MANIFEST_FILENAME)
        if not os.path.isfile(manifest_path):
            manifest = _empty_manifest()
            manifest['project'] = pro_file
            save_manifest(analysis_dir, manifest)
        # Respect track_in_git config — skip .gitignore if user wants git tracking
        _track_in_git = False
        try:
            _track_in_git = config.get('analysis', {}).get('track_in_git', False)
        except (NameError, AttributeError):
            pass
        gitignore_path = os.path.join(analysis_dir, '.gitignore')
        if not _track_in_git and not os.path.isfile(gitignore_path):
            with open(gitignore_path, 'w') as f:
                f.write(GITIGNORE_CONTENT)

        source_hashes = {os.path.basename(args.schematic): hash_source_file(args.schematic)}

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = os.path.join(tmp_dir, CANONICAL_OUTPUTS.get("schematic", "schematic.json"))
            Path(out_file).write_text(output)

            if should_create_new_run(analysis_dir, tmp_dir):
                run_id = create_run(
                    analysis_dir=analysis_dir,
                    outputs_dir=tmp_dir,
                    source_hashes=source_hashes,
                    scripts={"schematic": f"analyze_schematic.py {os.path.basename(args.schematic)}"},
                )
                print(f"Analysis cached: {os.path.join(analysis_dir, run_id, 'schematic.json')}", file=sys.stderr)
            else:
                overwrite_current(analysis_dir, tmp_dir, source_hashes=source_hashes)
                print(f"Analysis cache updated (current run)", file=sys.stderr)

    elif args.output:
        Path(args.output).write_text(output)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
