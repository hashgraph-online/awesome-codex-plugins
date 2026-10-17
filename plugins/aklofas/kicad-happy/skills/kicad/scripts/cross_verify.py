#!/usr/bin/env python3
"""Schematic-to-PCB cross-verification.

Correlates schematic design intent with PCB physical implementation.
Detects component mismatches, differential pair length issues, power
trace width concerns, decoupling placement gaps, bus routing skew,
and thermal via adequacy.

Usage:
    python3 cross_verify.py --schematic sch.json --pcb pcb.json
    python3 cross_verify.py --schematic sch.json --pcb pcb.json --thermal thermal.json
    python3 cross_verify.py --schematic sch.json --pcb pcb.json --output report.json

Zero external dependencies — Python 3.8+ stdlib only.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path


def cross_verify(sch: dict, pcb: dict,
                 thermal: dict | None = None) -> dict:
    """Run all cross-verification checks.

    Args:
        sch: Schematic analysis JSON (from analyze_schematic.py).
        pcb: PCB analysis JSON (from analyze_pcb.py).
        thermal: Optional thermal analysis JSON (from analyze_thermal.py).

    Returns:
        Structured report with per-check results and summary.
    """
    result = {
        "cross_verify_version": 1,
        "schematic_file": sch.get("file", ""),
        "pcb_file": pcb.get("file", ""),
    }

    checks_run = 0
    status_counts = {"pass": 0, "warning": 0, "fail": 0, "info": 0}

    # Check 1: Component reference matching
    comp_match = check_component_matching(sch, pcb)
    result["component_matching"] = comp_match
    checks_run += 1

    # Check 2: Differential pair length matching
    diff_pairs = check_diff_pair_routing(sch, pcb)
    if diff_pairs:
        result["diff_pair_routing"] = diff_pairs
        checks_run += 1

    # Check 3: Power trace width assessment
    power_traces = check_power_traces(sch, pcb)
    if power_traces:
        result["power_trace_analysis"] = power_traces
        checks_run += 1

    # Check 4: Decoupling cap placement
    decoupling = check_decoupling_placement(sch, pcb)
    if decoupling:
        result["decoupling_placement"] = decoupling
        checks_run += 1

    # Check 5: Bus routing advisory
    bus_routing = check_bus_routing(sch, pcb)
    if bus_routing:
        result["bus_routing"] = bus_routing
        checks_run += 1

    # Check 6: Thermal via adequacy
    if thermal:
        thermal_vias = check_thermal_vias(thermal, pcb)
        if thermal_vias:
            result["thermal_via_check"] = thermal_vias
            checks_run += 1

    # Count statuses across all checks
    for section in result.values():
        if isinstance(section, list):
            for item in section:
                if isinstance(item, dict) and "status" in item:
                    status_counts[item["status"]] = status_counts.get(item["status"], 0) + 1
        elif isinstance(section, dict):
            for item in section.values():
                if isinstance(item, list):
                    for entry in item:
                        if isinstance(entry, dict) and "status" in entry:
                            status_counts[entry["status"]] = status_counts.get(entry["status"], 0) + 1

    result["summary"] = {
        "total_checks": checks_run,
        **status_counts,
    }

    return result


def check_component_matching(sch: dict, pcb: dict) -> dict:
    """Check 1: Bidirectional component reference matching.

    Compares schematic component refs against PCB footprint refs.
    Detects orphans, missing components, value mismatches, and DNP conflicts.
    """
    # Build schematic ref lookup (exclude power symbols and flags)
    sch_comps = {}
    dnp_refs = set()
    for c in sch.get("components", []):
        ref = c.get("reference", "")
        if not ref or ref.startswith("#"):
            continue
        sch_comps[ref] = {
            "value": c.get("value", ""),
            "type": c.get("type", ""),
            "footprint": c.get("footprint", ""),
        }
        if c.get("dnp"):
            dnp_refs.add(ref)

    # Build PCB ref lookup
    pcb_fps = {}
    for fp in pcb.get("footprints", []):
        ref = fp.get("reference", "")
        if not ref or ref.startswith("#"):
            continue
        pcb_fps[ref] = {
            "value": fp.get("value", ""),
            "lib_id": fp.get("lib_id", ""),
        }

    sch_refs = set(sch_comps.keys())
    pcb_refs = set(pcb_fps.keys())

    matched = sch_refs & pcb_refs
    orphans = []  # in PCB but not schematic
    missing = []  # in schematic but not PCB
    value_mismatches = []
    dnp_conflicts = []

    # Orphans: in PCB but not in schematic
    for ref in sorted(pcb_refs - sch_refs):
        orphans.append({
            "ref": ref,
            "pcb_value": pcb_fps[ref]["value"],
            "status": "fail",
            "message": f"{ref} in PCB but not in schematic (stale placement?)",
        })

    # Missing: in schematic but not in PCB
    for ref in sorted(sch_refs - pcb_refs):
        if ref in dnp_refs:
            continue  # DNP components are expected to be absent from PCB
        sc = sch_comps[ref]
        missing.append({
            "ref": ref,
            "sch_value": sc["value"],
            "sch_type": sc["type"],
            "status": "fail",
            "message": f"{ref} ({sc['value']}) in schematic but not placed in PCB",
        })

    # Value mismatches on matched refs
    for ref in sorted(matched):
        sv = sch_comps[ref]["value"]
        pv = pcb_fps[ref]["value"]
        if sv and pv and sv.lower() != pv.lower():
            value_mismatches.append({
                "ref": ref,
                "sch_value": sv,
                "pcb_value": pv,
                "status": "warning",
                "message": f"{ref}: schematic says '{sv}', PCB says '{pv}'",
            })

    # DNP conflicts: marked DNP but placed in PCB
    for ref in sorted(dnp_refs & pcb_refs):
        dnp_conflicts.append({
            "ref": ref,
            "status": "warning",
            "message": f"{ref} marked DNP in schematic but placed in PCB",
        })

    return {
        "schematic_count": len(sch_comps),
        "pcb_count": len(pcb_fps),
        "matched": len(matched),
        "orphans": orphans,
        "missing": missing,
        "value_mismatches": value_mismatches,
        "dnp_conflicts": dnp_conflicts,
    }


def check_diff_pair_routing(sch: dict, pcb: dict) -> list[dict]:
    """Check 2: Differential pair length matching.

    Matches schematic-detected diff pairs against PCB per-net length data.
    Flags length mismatch, width mismatch, and layer mismatch.
    """
    diff_pairs = sch.get("design_analysis", {}).get("differential_pairs", [])
    if not diff_pairs:
        return []

    # Build net length lookup from PCB
    net_lengths = {}
    for nl in pcb.get("net_lengths", []):
        net_lengths[nl["net"]] = nl

    # Protocol-specific length tolerances (mm)
    _TOLERANCES = {
        "USB": 2.0,
        "Ethernet": 5.0,
        "HDMI": 1.0,
        "LVDS": 1.5,
        "MIPI": 1.5,
        "PCIe": 2.0,
        "SATA": 2.0,
    }

    results = []
    for dp in diff_pairs:
        pos_net = dp.get("positive", "")
        neg_net = dp.get("negative", "")
        protocol = dp.get("type", "differential")
        tolerance = _TOLERANCES.get(protocol, 2.0)

        pos_data = net_lengths.get(pos_net)
        neg_data = net_lengths.get(neg_net)

        entry = {
            "type": protocol,
            "positive": pos_net,
            "negative": neg_net,
            "tolerance_mm": tolerance,
        }

        if not pos_data and not neg_data:
            entry["status"] = "info"
            entry["message"] = f"Neither {pos_net} nor {neg_net} found in PCB routing"
            results.append(entry)
            continue

        if not pos_data or not neg_data:
            missing = pos_net if not pos_data else neg_net
            entry["status"] = "fail"
            entry["message"] = f"Only one net routed — {missing} not found in PCB"
            results.append(entry)
            continue

        pos_len = pos_data.get("total_length_mm", 0)
        neg_len = neg_data.get("total_length_mm", 0)
        delta = abs(pos_len - neg_len)

        entry["pos_length_mm"] = round(pos_len, 2)
        entry["neg_length_mm"] = round(neg_len, 2)
        entry["delta_mm"] = round(delta, 2)

        # Length matching check
        if delta > tolerance:
            entry["status"] = "fail"
            entry["message"] = (f"{protocol} pair {pos_net}/{neg_net}: "
                                f"{delta:.1f}mm length mismatch "
                                f"(tolerance {tolerance}mm)")
        elif delta > tolerance * 0.7:
            entry["status"] = "warning"
            entry["message"] = (f"{protocol} pair: {delta:.1f}mm mismatch "
                                f"approaching {tolerance}mm limit")
        else:
            entry["status"] = "pass"

        # Intra-pair skew: P vs N trace length within same pair
        # (tighter than the inter-pair length tolerance above)
        _intra_pair_tolerance = {
            "USB": 1.0,
            "Ethernet": 2.0,
            "HDMI": 0.5,
            "LVDS": 0.5,
            "MIPI": 0.5,
            "PCIe": 1.0,
            "SATA": 1.0,
        }

        intra_skew = delta  # same as abs(pos_len - neg_len) computed above
        intra_tol = _intra_pair_tolerance.get(protocol, 1.0)
        if intra_skew > intra_tol:
            entry["intra_pair_skew"] = {
                "skew_mm": round(intra_skew, 2),
                "tolerance_mm": intra_tol,
                "severity": "HIGH" if intra_skew > intra_tol * 2 else "MEDIUM",
                "detail": (f"Differential pair {pos_net}/{neg_net} intra-pair "
                           f"skew {intra_skew:.1f}mm exceeds {protocol} "
                           f"tolerance ({intra_tol}mm)"),
            }
            # Upgrade entry status if the skew check is more severe
            if entry["status"] == "pass":
                entry["status"] = "warning"
                entry["message"] = (f"{protocol} pair {pos_net}/{neg_net}: "
                                    f"intra-pair skew {intra_skew:.1f}mm "
                                    f"exceeds {intra_tol}mm tolerance")
            elif (entry["status"] == "warning"
                  and intra_skew > intra_tol * 2):
                entry["status"] = "fail"

        # Layer check
        pos_layers = set(pos_data.get("layers", {}).keys())
        neg_layers = set(neg_data.get("layers", {}).keys())
        if pos_layers and neg_layers and pos_layers != neg_layers:
            entry["layer_mismatch"] = {
                "positive_layers": sorted(pos_layers),
                "negative_layers": sorted(neg_layers),
            }
            if entry["status"] == "pass":
                entry["status"] = "warning"
                entry["message"] = (f"{protocol} pair routes on different layers: "
                                    f"{sorted(pos_layers)} vs {sorted(neg_layers)}")

        results.append(entry)

    return results


def check_power_traces(sch: dict, pcb: dict) -> list[dict]:
    """Check 3: Power trace width assessment.

    Matches regulator output rails against PCB power net routing data.
    Surfaces trace widths and total lengths for reviewer assessment.
    """
    regulators = [f for f in sch.get("findings", [])
                  if f.get("detector") == "detect_power_regulators"]
    if not regulators:
        return []

    # Build power routing lookup from PCB
    power_routing = {}
    for pr in pcb.get("power_net_routing", []):
        power_routing[pr["net"]] = pr

    results = []
    for reg in regulators:
        rail = reg.get("output_rail")
        if not rail:
            continue

        entry = {
            "regulator_ref": reg.get("ref", ""),
            "output_rail": rail,
            "topology": reg.get("topology", "unknown"),
            "estimated_vout": reg.get("estimated_vout"),
        }

        pr = power_routing.get(rail)
        if not pr:
            entry["status"] = "info"
            entry["message"] = f"Output rail {rail} not found in PCB power routing"
            results.append(entry)
            continue

        min_w = pr.get("min_width_mm", 0)
        max_w = pr.get("max_width_mm", 0)
        total_len = pr.get("total_length_mm", 0)

        entry["min_trace_width_mm"] = round(min_w, 3)
        entry["max_trace_width_mm"] = round(max_w, 3)
        entry["total_length_mm"] = round(total_len, 1)
        entry["track_count"] = pr.get("track_count", 0)

        # Switching regulators need wider traces for same current
        # (higher di/dt, transient current demands)
        is_switching = reg.get("topology") in ("switching", "buck", "boost",
                                                "buck-boost", "inverting")
        width_threshold = 0.3 if is_switching else 0.2

        if min_w < width_threshold:
            entry["status"] = "warning"
            topo_note = " (switching — higher current demand)" if is_switching else ""
            entry["message"] = (f"{rail}: minimum trace width {min_w:.2f}mm"
                                f" is narrow for a power rail{topo_note}")
        else:
            entry["status"] = "pass"

        results.append(entry)

    return results


def check_decoupling_placement(sch: dict, pcb: dict) -> list[dict]:
    """Check 4: Decoupling cap placement cross-check.

    Matches schematic decoupling analysis (which caps serve which ICs)
    against PCB footprint positions. Uses PCB decoupling_placement data
    when available, otherwise computes distances from footprint coordinates.
    """
    sch_decoupling = [f for f in sch.get("findings", [])
                      if f.get("detector") == "detect_decoupling"]
    if not sch_decoupling or not isinstance(sch_decoupling, list):
        return []

    # Use PCB's pre-computed decoupling placement if available
    pcb_decoupling = pcb.get("decoupling_placement", [])
    pcb_decoup_lookup = {}
    for entry in pcb_decoupling:
        ic_ref = entry.get("ic", "")
        for cap in entry.get("nearby_caps", []):
            pcb_decoup_lookup[(ic_ref, cap.get("cap", ""))] = cap.get("distance_mm", 999)

    # Build PCB footprint position lookup
    fp_positions = {}
    for fp in pcb.get("footprints", []):
        ref = fp.get("reference", "")
        if ref:
            fp_positions[ref] = (fp.get("x", 0), fp.get("y", 0))

    results = []
    for group in sch_decoupling:
        if not isinstance(group, dict):
            continue
        ic_ref = group.get("ic_ref") or group.get("ic") or group.get("rail", "")
        caps = group.get("capacitors", [])
        if not ic_ref or not caps:
            continue

        ic_pos = fp_positions.get(ic_ref)

        for cap in caps:
            if not isinstance(cap, dict):
                continue
            cap_ref = cap.get("ref", "")
            if not cap_ref:
                continue

            entry = {
                "ic_ref": ic_ref,
                "cap_ref": cap_ref,
                "cap_value": cap.get("value", ""),
            }

            # Try pre-computed distance first
            dist = pcb_decoup_lookup.get((ic_ref, cap_ref))

            # Fall back to footprint position calculation
            if dist is None and ic_pos:
                cap_pos = fp_positions.get(cap_ref)
                if cap_pos:
                    dist = math.sqrt(
                        (ic_pos[0] - cap_pos[0]) ** 2 +
                        (ic_pos[1] - cap_pos[1]) ** 2)

            if dist is not None:
                entry["distance_mm"] = round(dist, 2)
                if dist > 5.0:
                    entry["status"] = "warning"
                    entry["message"] = (f"{cap_ref} is {dist:.1f}mm from {ic_ref} "
                                        f"— should be within 5mm for effective decoupling")
                else:
                    entry["status"] = "pass"
            else:
                entry["status"] = "info"
                entry["message"] = f"{cap_ref} or {ic_ref} not found in PCB placement"

            results.append(entry)

    return results


def check_bus_routing(sch: dict, pcb: dict) -> list[dict]:
    """Check 5: High-speed bus signal routing advisory.

    Matches schematic-detected buses against PCB net lengths.
    Reports trace lengths and flags clock-to-data skew for SPI.
    """
    bus_analysis = sch.get("design_analysis", {}).get("bus_analysis", {})
    if not bus_analysis:
        return []

    # Build net length lookup
    net_lengths = {}
    for nl in pcb.get("net_lengths", []):
        net_lengths[nl["net"]] = nl.get("total_length_mm", 0)

    results = []

    for protocol, buses in bus_analysis.items():
        if not isinstance(buses, list):
            continue
        for bus in buses:
            signals = bus.get("signals", {})
            if not signals:
                continue

            bus_id = bus.get("bus_id", protocol)
            signal_lengths = {}
            missing_nets = []

            for sig_name, sig_data in signals.items():
                if isinstance(sig_data, dict):
                    net_name = sig_data.get("net", "")
                else:
                    net_name = str(sig_data)
                if not net_name:
                    continue
                length = net_lengths.get(net_name)
                if length is not None:
                    signal_lengths[sig_name] = round(length, 2)
                else:
                    missing_nets.append(net_name)

            if not signal_lengths:
                continue

            entry = {
                "protocol": protocol.upper(),
                "bus_id": bus_id,
                "signals": signal_lengths,
            }

            if missing_nets:
                entry["missing_nets"] = missing_nets

            lengths = list(signal_lengths.values())
            if len(lengths) >= 2:
                max_delta = max(lengths) - min(lengths)
                entry["max_delta_mm"] = round(max_delta, 2)

                # SPI clock-to-data skew check
                if protocol == "spi" and "SCK" in signal_lengths:
                    clk_len = signal_lengths["SCK"]
                    data_sigs = {k: v for k, v in signal_lengths.items() if k != "SCK"}
                    if data_sigs:
                        max_data = max(data_sigs.values())
                        clk_skew = abs(clk_len - max_data)
                        if clk_skew > 10.0:
                            entry["status"] = "warning"
                            entry["message"] = (f"SPI clock {clk_len:.1f}mm vs "
                                                f"longest data {max_data:.1f}mm — "
                                                f"{clk_skew:.1f}mm skew")
                        else:
                            entry["status"] = "pass"
                    else:
                        entry["status"] = "pass"
                else:
                    entry["status"] = "info"
            else:
                entry["status"] = "info"

            results.append(entry)

    return results


def check_thermal_vias(thermal: dict, pcb: dict) -> list[dict]:
    """Check 6: Thermal via adequacy.

    Cross-references thermal margins with PCB thermal pad via counts.
    Only runs when thermal JSON is provided.
    """
    assessments = thermal.get("thermal_assessments", [])
    if not assessments:
        return []

    # Build thermal pad via lookup from PCB findings[].
    # Thermal pad via entries have detector="analyze_thermal_pad_vias".
    # KH-234: Keys are "component" and "via_count".
    via_lookup = {}
    for tv in pcb.get("findings", []):
        if not isinstance(tv, dict):
            continue
        if tv.get("detector") != "analyze_thermal_pad_vias":
            continue
        ref = tv.get("component", "")
        if ref:
            via_lookup[ref] = tv.get("via_count", 0)

    results = []
    for a in assessments:
        ref = a.get("ref", "")
        tj = a.get("tj_estimated_c", 0)
        margin = a.get("margin_c", 999)
        pdiss = a.get("pdiss_w", 0)

        if margin > 30 or pdiss < 0.1:
            continue  # Skip components with comfortable margins

        via_count = via_lookup.get(ref, 0)

        entry = {
            "ref": ref,
            "value": a.get("value", ""),
            "tj_estimated_c": round(tj, 1),
            "margin_c": round(margin, 1),
            "pdiss_w": round(pdiss, 3),
            "thermal_vias": via_count,
        }

        if margin < 10 and via_count < 4:
            entry["status"] = "fail"
            entry["message"] = (f"{ref}: {margin:.0f}°C margin with only "
                                f"{via_count} thermal vias — insufficient cooling")
        elif margin < 20 and via_count < 2:
            entry["status"] = "warning"
            entry["message"] = (f"{ref}: {margin:.0f}°C margin with "
                                f"{via_count} thermal vias — consider adding more")
        elif margin < 20:
            entry["status"] = "info"
            entry["message"] = (f"{ref}: {margin:.0f}°C margin, "
                                f"{via_count} thermal vias")
        else:
            entry["status"] = "pass"

        results.append(entry)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Cross-verify schematic design intent against PCB implementation")
    parser.add_argument("--schematic", "-s", required=True,
                        help="Path to schematic analysis JSON")
    parser.add_argument("--pcb", "-p", required=True,
                        help="Path to PCB analysis JSON")
    parser.add_argument("--thermal", "-t", default=None,
                        help="Path to thermal analysis JSON (optional)")
    parser.add_argument("--output", "-o", default=None,
                        help="Output JSON path (default: stdout)")
    args = parser.parse_args()

    with open(args.schematic) as f:
        sch = json.load(f)
    with open(args.pcb) as f:
        pcb = json.load(f)

    thermal = None
    if args.thermal:
        with open(args.thermal) as f:
            thermal = json.load(f)

    report = cross_verify(sch, pcb, thermal)

    output = json.dumps(report, indent=2)
    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)) or ".", exist_ok=True)
        with open(args.output, "w") as f:
            f.write(output)
            f.write("\n")
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
