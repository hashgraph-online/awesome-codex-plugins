"""BOM generation and statistics: verbatim move from analyze_schematic.py; no behaviour change."""
from __future__ import annotations

from kicad_core.netnames import (
    _clean_hierarchical_name,
    is_power_net_name as _is_power_net_name,
    parse_voltage_from_net_name as _parse_voltage_from_net_name,
)


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
        # Skip PWR_FLAG — it's an ERC directive, not a physical rail.
        if clean == "PWR_FLAG":
            continue
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
