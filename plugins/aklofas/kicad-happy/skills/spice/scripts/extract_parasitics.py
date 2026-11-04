#!/usr/bin/env python3
"""
Extract PCB parasitic R/L/C values from PCB analyzer output.

Reads the PCB analysis JSON (from analyze_pcb.py --full) and computes
parasitic trace resistance, via inductance, and inter-trace coupling
capacitance per net. Outputs a parasitics.json that the SPICE simulation
skill uses to annotate testbenches.

Usage:
    python3 extract_parasitics.py pcb_analysis.json
    python3 extract_parasitics.py pcb_analysis.json --output parasitics.json
    python3 extract_parasitics.py pcb_analysis.json --nets filter_out,fb_net

Requires: PCB analysis JSON generated with --full flag (for trace segments).
"""

import argparse
import json
import math
import sys

import _core_path  # noqa: F401
from kicad_core.cli import add_output_arg


# Physical constants
RHO_CU = 1.68e-8       # Copper resistivity at 20°C (Ω·m)
MU_0 = 4 * math.pi * 1e-7  # Permeability of free space (H/m)
EPS_0 = 8.854e-12      # Permittivity of free space (F/m)
VIA_PLATING_UM = 25     # Typical via plating thickness (µm)


def trace_resistance(length_mm, width_mm, copper_thickness_mm):
    """Calculate DC trace resistance.

    R = ρ × L / (W × T)

    Args:
        length_mm: Trace length in mm
        width_mm: Trace width in mm
        copper_thickness_mm: Copper thickness in mm (0.035 = 1oz)

    Returns:
        Resistance in ohms
    """
    if width_mm <= 0 or copper_thickness_mm <= 0 or length_mm <= 0:
        return 0.0
    l = length_mm * 1e-3   # → meters
    w = width_mm * 1e-3
    t = copper_thickness_mm * 1e-3
    # EQ-016: R = ρL/(WT) (DC trace resistance)
    return RHO_CU * l / (w * t)


def via_resistance(board_thickness_mm, drill_mm, plating_um=VIA_PLATING_UM):
    """Calculate via barrel resistance.

    R = ρ × H / (π × ((D/2)² - ((D-2T)/2)²))

    Args:
        board_thickness_mm: Board thickness in mm
        drill_mm: Via drill diameter in mm
        plating_um: Plating thickness in µm (default 25)

    Returns:
        Resistance in ohms
    """
    if drill_mm <= 0 or board_thickness_mm <= 0:
        return 0.0
    h = board_thickness_mm * 1e-3
    r_outer = (drill_mm / 2) * 1e-3
    r_inner = r_outer - plating_um * 1e-6
    if r_inner <= 0:
        r_inner = r_outer * 0.5  # Solid fill for small vias
    area = math.pi * (r_outer ** 2 - r_inner ** 2)
    # EQ-017: R = ρH/(π(r²outer-r²inner)) (via barrel resistance)
    return RHO_CU * h / area


def via_inductance(board_thickness_mm, drill_mm):
    """Calculate via self-inductance (approximate).

    L ≈ (µ₀ × H / (2π)) × ln(2H/D)

    This is the partial self-inductance of the via barrel. The actual
    loop inductance depends on the return current path (ground plane
    via nearby), which is not modeled here.

    Args:
        board_thickness_mm: Board thickness (via height) in mm
        drill_mm: Via drill diameter in mm

    Returns:
        Inductance in henries
    """
    if drill_mm <= 0 or board_thickness_mm <= 0:
        return 0.0
    h = board_thickness_mm * 1e-3
    d = drill_mm * 1e-3
    if 2 * h <= d:
        return 0.0  # Degenerate case
    # EQ-018: L = (µ₀H/2π)ln(2H/D) (via self-inductance)
    # Source: Goldfarb & Pucel, IEEE MGWL Vol.1 No.6 pp.135-137, June 1991
    # URL: https://www.semanticscholar.org/paper/a3f4614877b750e7b7eec1dfa5924d5ce8b99301
    return (MU_0 * h / (2 * math.pi)) * math.log(2 * h / d)


def coupling_capacitance(parallel_length_mm, trace_height_mm, spacing_mm, epsilon_r=4.5):
    """Estimate inter-trace coupling capacitance for parallel runs.

    Simplified parallel-plate model:
    C ≈ ε₀ × εᵣ × L × T / S

    This is a rough approximation — real coupling depends on trace
    geometry, ground plane distance, and fringing fields.

    Args:
        parallel_length_mm: Length of parallel run in mm
        trace_height_mm: Copper thickness in mm
        spacing_mm: Edge-to-edge spacing in mm
        epsilon_r: Dielectric constant (FR4 ≈ 4.5)

    Returns:
        Capacitance in farads
    """
    if spacing_mm <= 0 or parallel_length_mm <= 0 or trace_height_mm <= 0:
        return 0.0
    l = parallel_length_mm * 1e-3
    t = trace_height_mm * 1e-3
    s = spacing_mm * 1e-3
    # EQ-019: C = ε₀εrLT/S (inter-trace coupling capacitance, parallel-plate approx)
    return EPS_0 * epsilon_r * l * t / s


def extract_parasitics(pcb_json, net_filter=None):
    """Extract parasitic values from PCB analysis JSON.

    Args:
        pcb_json: Parsed PCB analysis JSON dict (from analyze_pcb.py --full)
        net_filter: Optional set of net names to process (None = all)

    Returns:
        Parasitics dict with per-net R, L, C values
    """
    # EQ-072: Orchestrates EQ-016..019 per net from PCB data
    # Extract stackup info
    setup = pcb_json.get("setup", {})
    stackup = setup.get("stackup", [])
    board_thickness = setup.get("board_thickness_mm", 1.6)

    # Find copper thickness from stackup (default 1oz = 0.035mm)
    copper_thickness = 0.035
    dielectric_er = 4.5
    for layer in stackup:
        if layer.get("type") == "copper" and layer.get("thickness"):
            copper_thickness = layer["thickness"]
            break
    for layer in stackup:
        if layer.get("type") in ("core", "prepreg") and layer.get("epsilon_r"):
            dielectric_er = layer["epsilon_r"]
            break

    result = {
        "stackup": {
            "copper_thickness_mm": copper_thickness,
            "board_thickness_mm": board_thickness,
            "dielectric_er": dielectric_er,
        },
        "nets": {},
        "coupling": [],
    }

    # Process net lengths (needs trace_segments from --full mode)
    net_lengths = pcb_json.get("net_lengths", [])
    for nl in net_lengths:
        net_name = nl.get("net", "")
        if net_filter and net_name not in net_filter:
            continue

        trace_segments = nl.get("trace_segments", [])
        via_details = nl.get("via_details", [])

        if not trace_segments and not via_details:
            continue

        # Compute trace resistance per segment
        total_trace_r = 0.0
        segment_parasitics = []
        for seg in trace_segments:
            r = trace_resistance(seg["length_mm"], seg["width_mm"], copper_thickness)
            total_trace_r += r
            if r > 0:
                segment_parasitics.append({
                    "layer": seg["layer"],
                    "length_mm": seg["length_mm"],
                    "width_mm": seg["width_mm"],
                    "resistance_ohm": round(r, 6),
                })

        # Compute via parasitics
        total_via_r = 0.0
        total_via_l = 0.0
        via_parasitics = []
        for via in via_details:
            drill = via.get("drill_mm", 0)
            if drill <= 0:
                continue
            r = via_resistance(board_thickness, drill)
            l = via_inductance(board_thickness, drill)
            total_via_r += r
            total_via_l += l
            via_parasitics.append({
                "drill_mm": drill,
                "resistance_ohm": round(r, 6),
                "inductance_nH": round(l * 1e9, 3),
            })

        net_entry = {
            "total_trace_resistance_ohm": round(total_trace_r, 6),
            "total_via_resistance_ohm": round(total_via_r, 6),
            "total_via_inductance_nH": round(total_via_l * 1e9, 3),
            "total_length_mm": nl.get("total_length_mm", 0),
            "via_count": nl.get("via_count", 0),
        }

        # Only include segment/via detail if there are significant parasitics
        if total_trace_r > 0.001:  # > 1mΩ
            net_entry["trace_segments"] = segment_parasitics
        if via_parasitics:
            net_entry["via_details"] = via_parasitics

        result["nets"][net_name] = net_entry

    # Process trace proximity for coupling capacitance
    proximity = pcb_json.get("trace_proximity", {})
    for pair in proximity.get("proximity_pairs", []):
        coupling_len = pair.get("approx_coupling_mm", 0)
        if coupling_len <= 0:
            continue
        net_a = pair.get("net_a", "")
        net_b = pair.get("net_b", "")
        if net_filter and net_a not in net_filter and net_b not in net_filter:
            continue

        # Estimate spacing from grid size (rough — the proximity analyzer
        # uses a grid, so actual spacing is grid_size ± half grid)
        grid_size = proximity.get("grid_size_mm", 0.5)
        estimated_spacing = grid_size  # Conservative — actual may be tighter

        c = coupling_capacitance(coupling_len, copper_thickness,
                                 estimated_spacing, dielectric_er)
        if c > 1e-15:  # > 1fF
            result["coupling"].append({
                "net_a": net_a,
                "net_b": net_b,
                "coupling_length_mm": round(coupling_len, 2),
                "estimated_spacing_mm": round(estimated_spacing, 2),
                "capacitance_pF": round(c * 1e12, 3),
            })

    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract PCB parasitic R/L/C from PCB analysis JSON"
    )
    parser.add_argument(
        "input",
        help="Path to PCB analysis JSON (from analyze_pcb.py --full)",
    )
    add_output_arg(parser, help="Path to write parasitics JSON (default: stdout)")
    parser.add_argument(
        "--nets",
        help="Comma-separated list of net names to process (default: all)",
    )
    args = parser.parse_args(argv)

    try:
        with open(args.input) as f:
            pcb_json = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error reading {args.input}: {e}", file=sys.stderr)
        return 1

    # Check for trace segment data
    net_lengths = pcb_json.get("net_lengths", [])
    has_segments = any("trace_segments" in nl for nl in net_lengths)
    if not has_segments:
        print("Warning: PCB JSON has no trace segment data.", file=sys.stderr)
        print("Re-run analyze_pcb.py with --full flag for parasitic extraction.",
              file=sys.stderr)

    net_filter = None
    if args.nets:
        net_filter = set(n.strip() for n in args.nets.split(","))

    result = extract_parasitics(pcb_json, net_filter)

    # Summary
    nets_with_data = sum(1 for v in result["nets"].values()
                         if v["total_trace_resistance_ohm"] > 0)
    total_r = sum(v["total_trace_resistance_ohm"] for v in result["nets"].values())
    total_via_l = sum(v["total_via_inductance_nH"] for v in result["nets"].values())
    print(f"Extracted parasitics for {nets_with_data} nets "
          f"(total trace R={total_r:.3f}Ω, total via L={total_via_l:.1f}nH, "
          f"{len(result['coupling'])} coupling pairs)", file=sys.stderr)

    output = json.dumps(result, indent=2)
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
    else:
        print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
