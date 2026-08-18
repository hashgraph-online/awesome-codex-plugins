#!/usr/bin/env python3
"""
Interactive "What-If" parameter sweep for KiCad designs.

Patches component values in analyzer JSON, re-runs affected subcircuit
calculations (and optionally SPICE simulations), and shows before/after
impact on circuit behavior.

Usage:
    python3 what_if.py analysis.json R5=4.7k
    python3 what_if.py analysis.json R5=4.7k C3=22n
    python3 what_if.py analysis.json R5=4.7k --spice
    python3 what_if.py analysis.json R5=4.7k --output patched.json
    python3 what_if.py analysis.json R5=4.7k --text

Zero dependencies — Python 3.8+ stdlib only.
"""

import argparse
import copy
import json
import math
import os
import sys
from dataclasses import dataclass

# Allow imports from same directory and spice scripts
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "spice", "scripts"))

from kicad_utils import parse_value
from finding_schema import group_findings_by_detection_type, is_old_schema


@dataclass
class Change:
    ref: str
    value: float
    value_str: str
    tolerance: float  # None = no tolerance specified; will be used in Task 3


@dataclass
class SweepSpec:
    ref: str
    values: list
    value_strs: list
    tolerance: float  # None = no tolerance; will be used in Task 3


# Value key -> unit name for display
_VALUE_UNITS = {"ohms": "ohms", "farads": "F", "henries": "H"}


# ---------------------------------------------------------------------------
# Parse change specifications
# ---------------------------------------------------------------------------

def _parse_changes(change_args: list) -> tuple:
    """Parse REF=VALUE pairs, detecting sweep syntax.

    Returns (changes_dict, sweep_or_none).
    Sweep: R5=1k,2.2k,4.7k (comma) or R5=1k..100k:10 (log range).
    Only one component may use sweep syntax.
    """
    changes = {}
    sweep = None

    for arg in change_args:
        if "=" not in arg:
            print(f"Error: invalid change '{arg}' — expected REF=VALUE", file=sys.stderr)
            sys.exit(1)
        ref, val_str = arg.split("=", 1)
        ref = ref.strip()
        val_str = val_str.strip()

        # Component type hint
        prefix = ref.rstrip("0123456789")
        ctype = None
        if prefix in ("C", "VC"):
            ctype = "capacitor"
        elif prefix in ("L",):
            ctype = "inductor"

        # Extract tolerance suffix before checking sweep syntax
        tolerance = None
        for tol_sep in ("\u00b1", "+-"):
            if tol_sep in val_str:
                main_part, tol_part = val_str.rsplit(tol_sep, 1)
                tol_str = tol_part.strip().rstrip("%")
                try:
                    tolerance = float(tol_str) / 100.0
                except ValueError:
                    tolerance = None
                    break
                val_str = main_part.strip()
                break

        if ".." in val_str and ":" in val_str:
            # Log sweep: R5=1k..100k:10
            if sweep is not None:
                print("Error: only one component may use sweep syntax", file=sys.stderr)
                sys.exit(1)
            range_part, n_str = val_str.rsplit(":", 1)
            start_str, stop_str = range_part.split("..", 1)
            start = parse_value(start_str, component_type=ctype)
            stop = parse_value(stop_str, component_type=ctype)
            try:
                n = int(n_str)
            except ValueError:
                print(f"Error: invalid step count '{n_str}'", file=sys.stderr)
                sys.exit(1)
            if start is None or stop is None or n < 2:
                print(f"Error: invalid sweep '{val_str}'", file=sys.stderr)
                sys.exit(1)
            n = min(n, 50)
            values = [start * (stop / start) ** (i / (n - 1)) for i in range(n)]
            strs = [start_str] + [f"{v:.4g}" for v in values[1:-1]] + [stop_str]
            sweep = SweepSpec(ref=ref, values=values, value_strs=strs, tolerance=tolerance)

        elif "," in val_str:
            # Comma list: R5=1k,2.2k,4.7k
            if sweep is not None:
                print("Error: only one component may use sweep syntax", file=sys.stderr)
                sys.exit(1)
            parts = [p.strip() for p in val_str.split(",")]
            values = []
            for p in parts:
                v = parse_value(p, component_type=ctype)
                if v is None:
                    print(f"Error: cannot parse '{p}' in sweep for {ref}", file=sys.stderr)
                    sys.exit(1)
                values.append(v)
            sweep = SweepSpec(ref=ref, values=values, value_strs=parts, tolerance=tolerance)

        else:
            # Single value
            parsed = parse_value(val_str, component_type=ctype)
            if parsed is None:
                print(f"Error: cannot parse value '{val_str}' for {ref}", file=sys.stderr)
                sys.exit(1)
            changes[ref] = Change(ref=ref, value=parsed, value_str=val_str, tolerance=tolerance)

    return changes, sweep


# ---------------------------------------------------------------------------
# Find affected detections
# ---------------------------------------------------------------------------

def _find_refs_in_det(det: dict) -> dict:
    """Walk a detection dict and find all component refs with their value paths.

    Returns {ref: [(key_path_to_value, value_key), ...]}
    where key_path_to_value is like ["resistor"] and value_key is "ohms".
    """
    refs = {}

    def _check(sub, path):
        if not isinstance(sub, dict) or "ref" not in sub:
            return
        ref = sub["ref"]
        for vkey in ("ohms", "farads", "henries"):
            if vkey in sub and isinstance(sub[vkey], (int, float)):
                refs.setdefault(ref, []).append((path, vkey))

    for key, val in det.items():
        if isinstance(val, dict):
            _check(val, [key])
            for subkey, subval in val.items():
                if isinstance(subval, dict):
                    _check(subval, [key, subkey])
        elif isinstance(val, list):
            for idx, item in enumerate(val):
                if isinstance(item, dict):
                    _check(item, [key, idx])

    return refs


def _find_affected(signal_analysis: dict, changes: dict) -> list:
    """Find all detections referencing any changed component.

    Returns list of (det_type, index, det_dict, matched_refs_with_paths).
    """
    affected = []
    change_refs = set(changes.keys())

    for det_type, detections in signal_analysis.items():
        if not isinstance(detections, list):
            continue
        for idx, det in enumerate(detections):
            if not isinstance(det, dict):
                continue
            refs = _find_refs_in_det(det)
            matched = {r: paths for r, paths in refs.items() if r in change_refs}
            if matched:
                affected.append((det_type, idx, det, matched))

    return affected


# ---------------------------------------------------------------------------
# Apply changes and recalculate
# ---------------------------------------------------------------------------

def _apply_changes(det: dict, changes: dict, matched_refs: dict,
                   det_type: str = None) -> dict:
    """Deep-copy detection, apply value changes, recalculate derived fields."""
    from detection_schema import recalc_derived

    patched = copy.deepcopy(det)

    for ref, paths in matched_refs.items():
        new_val, new_str = changes[ref]
        for path, vkey in paths:
            # Navigate to the component sub-dict
            obj = patched
            for key in path:
                obj = obj[key]
            obj[vkey] = new_val
            # Update the value string too
            if "value" in obj:
                obj["value"] = new_str

    if det_type:
        recalc_derived(patched, det_type)
    else:
        from spice_tolerance import _recalc_derived
        _recalc_derived(patched)
    return patched


# ---------------------------------------------------------------------------
# Before/after comparison
# ---------------------------------------------------------------------------

def _compare(original: dict, patched: dict, det_type: str) -> list:
    """Compare derived fields between original and patched detection.

    Returns list of {field, before, after, delta_pct} for changed fields.
    """
    from detection_schema import get_derived_field_names
    fields = get_derived_field_names(det_type)
    # Also check common fields not in the registry
    for extra in ("cutoff_hz", "ratio", "resonant_hz", "gain", "gain_dB",
                  "impedance_ohms", "effective_load_pF", "estimated_vout",
                  "max_current_50mV_A", "max_current_100mV_A"):
        if extra not in fields and extra in original:
            fields = list(fields) + [extra]

    deltas = []
    for field in fields:
        bv = original.get(field)
        av = patched.get(field)
        if bv is None or av is None:
            continue
        if not isinstance(bv, (int, float)) or not isinstance(av, (int, float)):
            if bv != av:
                deltas.append({"field": field, "before": bv, "after": av})
            continue
        if bv == av:
            continue
        pct = ((av - bv) / abs(bv) * 100) if bv != 0 else None
        entry = {"field": field, "before": round(bv, 6), "after": round(av, 6)}
        if pct is not None:
            entry["delta_pct"] = round(pct, 1)
        deltas.append(entry)

    return deltas


def _get_det_label(det: dict, det_type: str) -> str:
    """Build a human-readable label for a detection."""
    refs = []
    for key in ("resistor", "r_top", "inductor", "shunt"):
        if key in det and isinstance(det[key], dict) and "ref" in det[key]:
            refs.append(det[key]["ref"])
    for key in ("capacitor", "r_bottom"):
        if key in det and isinstance(det[key], dict) and "ref" in det[key]:
            refs.append(det[key]["ref"])
    if "reference" in det:
        refs.append(det["reference"])
    for key in ("feedback_resistor", "input_resistor"):
        if key in det and isinstance(det[key], dict) and "ref" in det[key]:
            refs.append(det[key]["ref"])

    type_label = det_type.replace("_", " ").rstrip("s")
    ref_str = "/".join(refs) if refs else f"#{det_type}"
    return f"{type_label} {ref_str}"


# ---------------------------------------------------------------------------
# Optional SPICE re-simulation
# ---------------------------------------------------------------------------

def _run_spice_comparison(affected: list, patched_dets: list,
                          analysis_json: dict) -> dict:
    """Run SPICE on original and patched detections, return simulated deltas.

    Returns {(det_type, idx): {metric: {before, after, delta_pct}}}
    """
    try:
        from simulate_subcircuits import simulate_subcircuits
        from spice_simulator import detect_simulator
    except ImportError:
        print("Warning: SPICE scripts not found, skipping --spice",
              file=sys.stderr)
        return {}

    backend = detect_simulator("auto")
    if not backend:
        print("Warning: no SPICE simulator found, skipping --spice",
              file=sys.stderr)
        return {}

    results = {}

    for (det_type, idx, original_det, _matched), patched_det in zip(affected, patched_dets):
        # Build minimal analysis JSON for each detection
        def _run_one(det):
            mini_json = copy.deepcopy(analysis_json)
            mini_json["signal_analysis"] = {det_type: [det]}
            report = simulate_subcircuits(
                mini_json, timeout=5, types=[det_type],
                simulator_backend=backend)
            sim_results = report.get("simulation_results", [])
            if sim_results and sim_results[0].get("status") != "skip":
                return sim_results[0].get("simulated", {})
            return {}

        sim_before = _run_one(original_det)
        sim_after = _run_one(patched_det)

        spice_deltas = {}
        all_keys = set(list(sim_before.keys()) + list(sim_after.keys()))
        for key in all_keys:
            bv = sim_before.get(key)
            av = sim_after.get(key)
            if bv is None or av is None:
                continue
            if not isinstance(bv, (int, float)) or not isinstance(av, (int, float)):
                continue
            if bv == av:
                continue
            pct = ((av - bv) / abs(bv) * 100) if bv != 0 else None
            entry = {"before": round(bv, 6), "after": round(av, 6)}
            if pct is not None:
                entry["delta_pct"] = round(pct, 1)
            spice_deltas[key] = entry

        if spice_deltas:
            results[(det_type, idx)] = spice_deltas

    return results


# ---------------------------------------------------------------------------
# Sweep execution
# ---------------------------------------------------------------------------

def _run_sweep(analysis: dict, sweep: SweepSpec, fixed_changes: dict,
               spice: bool = False) -> dict:
    """Run the what-if pipeline for each sweep value, collect tabular results."""
    signal = group_findings_by_detection_type(analysis)
    results_per_step = []

    for val, val_str in zip(sweep.values, sweep.value_strs):
        # Build changes dict for this step (legacy format for existing functions)
        step_changes = {ref: (c.value, c.value_str) for ref, c in fixed_changes.items()}
        step_changes[sweep.ref] = (val, val_str)

        affected = _find_affected(signal, step_changes)
        step_subcircuits = []
        for det_type, idx, det, matched in affected:
            patched = _apply_changes(det, step_changes, matched, det_type=det_type)
            deltas = _compare(det, patched, det_type)
            label = _get_det_label(det, det_type)
            step_subcircuits.append({
                "type": det_type, "label": label,
                "delta": deltas,
                "after": {d["field"]: d["after"] for d in deltas},
            })
        results_per_step.append({
            "value": val, "value_str": val_str,
            "affected_subcircuits": step_subcircuits,
        })

    return {
        "ref": sweep.ref,
        "values": sweep.values,
        "value_strs": sweep.value_strs,
        "results": results_per_step,
    }


# ---------------------------------------------------------------------------
# Tolerance corner-case engine
# ---------------------------------------------------------------------------

def _run_tolerance(analysis: dict, changes: dict, spice: bool = False) -> list:
    """Compute worst-case tolerance bounds for each derived field.

    Evaluates all 2^N corner combinations (each component at +tol and -tol).
    Capped at 6 components (64 corners).
    """
    signal = group_findings_by_detection_type(analysis)

    # Resolve tolerances (use defaults for components without explicit tolerance)
    _DEFAULT_TOL = {"C": 0.10, "VC": 0.10, "L": 0.20}  # everything else = 0.05

    tol_info = {}  # ref -> (value, value_str, tolerance)
    for ref, c in changes.items():
        tol = c.tolerance
        if tol is None:
            prefix = ref.rstrip("0123456789")
            tol = _DEFAULT_TOL.get(prefix, 0.05)
        tol_info[ref] = (c.value, c.value_str, tol)

    changes_legacy = {ref: (c.value, c.value_str) for ref, c in changes.items()}
    affected = _find_affected(signal, changes_legacy)
    if not affected:
        return []

    results = []
    for det_type, idx, det, matched in affected:
        # Nominal
        patched_nom = _apply_changes(det, changes_legacy, matched, det_type=det_type)
        nominal_deltas = _compare(det, patched_nom, det_type)
        label = _get_det_label(det, det_type)

        # Identify toleranced refs in this detection
        tol_refs = [(ref, tol_info[ref]) for ref in matched if ref in tol_info]
        if not tol_refs:
            results.append({"type": det_type, "label": label,
                           "delta": nominal_deltas, "tolerance": []})
            continue

        # Generate 2^N corners (cap at 6 components = 64 corners)
        n = min(len(tol_refs), 6)
        corners = []
        for bits in range(1 << n):
            corner_changes = dict(changes_legacy)
            for i in range(n):
                ref, (val, vstr, tol) = tol_refs[i]
                factor = (1 + tol) if (bits >> i) & 1 else (1 - tol)
                corner_changes[ref] = (val * factor, vstr)
            corner_patched = _apply_changes(det, corner_changes, matched, det_type=det_type)
            corners.append(corner_patched)

        # For each derived field, find worst-case bounds
        tol_results = []
        fields = [d["field"] for d in nominal_deltas]
        for field in fields:
            nom_val = patched_nom.get(field)
            if not isinstance(nom_val, (int, float)):
                continue
            corner_vals = [c.get(field) for c in corners
                          if isinstance(c.get(field), (int, float))]
            if not corner_vals:
                continue
            worst_low = min(corner_vals)
            worst_high = max(corner_vals)
            spread = worst_high - worst_low
            spread_pct = (spread / abs(nom_val) * 100) if nom_val != 0 else 0
            tol_results.append({
                "field": field,
                "nominal": round(nom_val, 6),
                "worst_low": round(worst_low, 6),
                "worst_high": round(worst_high, 6),
                "spread_pct": round(spread_pct, 1),
            })

        results.append({"type": det_type, "label": label,
                       "delta": nominal_deltas, "tolerance": tol_results})

    return results


# ---------------------------------------------------------------------------
# Patch full JSON for export
# ---------------------------------------------------------------------------

def _patch_full_json(analysis_json: dict, affected: list,
                     patched_dets: list, changes: dict) -> dict:
    """Create a patched copy of the full analysis JSON."""
    patched = copy.deepcopy(analysis_json)

    # Replace affected detections in flat findings[]
    # Build a lookup from detection_id to findings list index for O(1) patching.
    findings = patched.get("findings", [])
    id_to_fi = {f.get("detection_id"): fi for fi, f in enumerate(findings)
                if f.get("detection_id")}
    for (_det_type, _idx, orig_det, _matched), new_det in zip(affected, patched_dets):
        did = orig_det.get("detection_id")
        if did and did in id_to_fi:
            # Preserve detector metadata from original finding
            new_det.setdefault("detector", orig_det.get("detector", ""))
            new_det.setdefault("detection_id", did)
            findings[id_to_fi[did]] = new_det

    # Update components[] parsed_value
    for comp in patched.get("components", []):
        ref = comp.get("reference", "")
        if ref in changes:
            new_val, new_str = changes[ref]
            comp["value"] = new_str
            if "parsed_value" in comp and isinstance(comp["parsed_value"], dict):
                comp["parsed_value"]["value"] = new_val

    return patched


# ---------------------------------------------------------------------------
# PCB parasitic awareness
# ---------------------------------------------------------------------------

_RHO_CU = 1.72e-8  # Copper resistivity (Ω·m)
_CU_THICKNESS_1OZ = 35e-6  # 1oz copper thickness (m)

# Footprint -> typical max capacitance (ceramic MLCC)
_FOOTPRINT_MAX_CAP = {
    "0402": 100e-9, "0603": 1e-6, "0805": 10e-6,
    "1206": 22e-6, "1210": 47e-6,
}


def _find_pcb_analysis(schematic_json_path: str) -> str:
    """Try to find PCB analysis JSON in the same analysis folder."""
    sch_dir = os.path.dirname(os.path.abspath(schematic_json_path))
    parent = os.path.dirname(sch_dir)
    # Convention: analysis/schematic/foo.json -> analysis/pcb/foo.json
    if os.path.basename(sch_dir) == "schematic":
        pcb_dir = os.path.join(parent, "pcb")
    elif "schematic" in sch_dir:
        pcb_dir = sch_dir.replace("schematic", "pcb")
    else:
        return None
    if os.path.isdir(pcb_dir):
        for f in sorted(os.listdir(pcb_dir)):
            if f.endswith(".json"):
                return os.path.join(pcb_dir, f)
    return None


def _extract_parasitics(pcb_analysis: dict, det: dict, det_type: str) -> dict:
    """Extract trace parasitics for components in a detection."""
    parasitics = {}
    tracks = pcb_analysis.get("tracks", {})
    if not tracks:
        tracks = pcb_analysis.get("track_summary", {})

    refs_in_det = _find_refs_in_det(det)
    for ref in refs_in_det:
        # Find component's nets from pin_nets or detection context
        comp_nets = set()
        for path, vkey in refs_in_det.get(ref, []):
            obj = det
            for k in path:
                obj = obj[k]
            net = obj.get("net", "")
            if net:
                comp_nets.add(net)

        total_r = 0.0
        total_l = 0.0
        net_name = None
        for net in comp_nets:
            net_tracks = tracks.get(net, [])
            if isinstance(net_tracks, dict):
                net_tracks = [net_tracks]
            for t in net_tracks:
                length_m = t.get("length_mm", 0) * 1e-3
                width_m = t.get("width_mm", 0) * 1e-3
                if length_m > 0 and width_m > 0:
                    r = _RHO_CU * length_m / (width_m * _CU_THICKNESS_1OZ)
                    l = (2e-7 * length_m * math.log(2 * length_m / width_m)
                         if width_m > 0 and length_m > width_m else 0)
                    total_r += r
                    total_l += abs(l)
            if net_tracks:
                net_name = net

        if total_r > 0 or total_l > 0:
            parasitics[ref] = {
                "net": net_name,
                "R_trace_ohms": round(total_r, 6),
                "L_trace_H": round(total_l, 12),
            }

    return parasitics


def _check_footprint_fit(suggestions: list, pcb_analysis: dict) -> list:
    """Check if suggested cap values fit in current footprints."""
    warnings = []
    fp_map = {}
    for comp in pcb_analysis.get("footprints", []):
        ref = comp.get("reference", "")
        fp = comp.get("footprint", "")
        fp_map[ref] = fp

    for s in suggestions:
        ref = s.get("ref", "")
        if s.get("field") != "farads":
            continue
        fp = fp_map.get(ref, "")
        for size, max_cap in _FOOTPRINT_MAX_CAP.items():
            if size in fp:
                for series in ("E96", "E24", "E12"):
                    ev = s.get("e_series", {}).get(series, {}).get("value", 0)
                    if ev > max_cap:
                        warnings.append(
                            f"\u26a0 {ref}: suggested {_format_value(ev, 'farads')}"
                            f" may require larger package than current {size}"
                            f" (typical max {_format_value(max_cap, 'farads')})"
                        )
                break
    return warnings


# ---------------------------------------------------------------------------
# Text formatter
# ---------------------------------------------------------------------------

def _format_value(val, field):
    """Format a value with appropriate units."""
    if not isinstance(val, (int, float)):
        return str(val)
    if "hz" in field.lower():
        if val >= 1e6:
            return f"{val/1e6:.2f}MHz"
        if val >= 1e3:
            return f"{val/1e3:.2f}kHz"
        return f"{val:.2f}Hz"
    if "ohms" in field.lower():
        if val >= 1e6:
            return f"{val/1e6:.2f}MΩ"
        if val >= 1e3:
            return f"{val/1e3:.2f}kΩ"
        return f"{val:.2f}Ω"
    if "farad" in field.lower():
        if val >= 1e-3:
            return f"{val*1e3:.2f}mF"
        if val >= 1e-6:
            return f"{val*1e6:.2f}µF"
        if val >= 1e-9:
            return f"{val*1e9:.2f}nF"
        return f"{val*1e12:.2f}pF"
    if field.endswith("_pF"):
        return f"{val:.1f}pF"
    if field.endswith("_A"):
        if val < 1:
            return f"{val*1000:.1f}mA"
        return f"{val:.3f}A"
    if "ratio" in field:
        return f"{val:.4f}"
    if "gain" in field.lower() and "dB" not in field:
        return f"{val:.3f}"
    if "dB" in field:
        return f"{val:.1f}dB"
    if field.startswith("estimated_vout") or field.endswith("_V") or field.endswith("_v"):
        return f"{val:.3f}V"
    return f"{val:.4g}"


def format_text(result: dict) -> str:
    """Format what-if results as human-readable text."""
    lines = []

    # Header
    changes = result.get("changes", {})
    change_strs = []
    for ref, info in changes.items():
        before = info.get("before_str", str(info.get("before", "?")))
        after = info.get("after_str", str(info.get("after", "?")))
        change_strs.append(f"{ref} {before} -> {after}")
    lines.append(f"What-If Analysis: {', '.join(change_strs)}")
    lines.append("")

    subcircuits = result.get("affected_subcircuits", [])
    lines.append(f"Affected subcircuits: {len(subcircuits)}")
    if not subcircuits:
        lines.append("  No subcircuits reference the changed component(s).")
        return "\n".join(lines)

    lines.append("")

    for sc in subcircuits:
        label = sc.get("label", sc.get("type", "?"))
        lines.append(f"  {label}:")

        for d in sc.get("delta", []):
            field = d["field"]
            before = _format_value(d["before"], field)
            after = _format_value(d["after"], field)
            pct = d.get("delta_pct")
            pct_str = f" ({pct:+.1f}%)" if pct is not None else ""
            lines.append(f"    {field}: {before} -> {after}{pct_str}")

        for t in sc.get("tolerance", []):
            field = t["field"]
            low = _format_value(t["worst_low"], field)
            high = _format_value(t["worst_high"], field)
            spread = t["spread_pct"]
            lines.append(f"    {field} tolerance: {low} .. {high} (\u00b1{spread/2:.1f}%)")

        # SPICE results
        for key, d in sc.get("spice_delta", {}).items():
            before = _format_value(d["before"], key)
            after = _format_value(d["after"], key)
            pct = d.get("delta_pct")
            pct_str = f" ({pct:+.1f}%)" if pct is not None else ""
            lines.append(f"    SPICE {key}: {before} -> {after}{pct_str}")

        # PCB parasitics
        for ref, p in sc.get("parasitics", {}).items():
            r = p.get("R_trace_ohms", 0)
            l = p.get("L_trace_H", 0)
            net = p.get("net", "?")
            parts = []
            if r > 0:
                parts.append(f"R_trace={_format_value(r, 'ohms')}")
            if l > 0:
                parts.append(f"L_trace={l*1e9:.1f}nH")
            if parts:
                lines.append(f"    (PCB parasitics on {net}: {', '.join(parts)})")

        lines.append("")

    emc = result.get("emc_delta")
    if emc:
        lines.append("EMC impact preview:")
        lines.append(f"  Overall risk: {emc['before_risk']} \u2192 {emc['after_risk']}")
        for r in emc.get("resolved", []):
            lines.append(f"  {r['rule']}: RESOLVED \u2014 {r['detail']}")
        for r in emc.get("improved", []):
            lines.append(f"  {r['rule']}: IMPROVED \u2014 {r['before']} \u2192 {r['after']}")
        for r in emc.get("new_findings", []):
            lines.append(f"  {r['rule']}: NEW \u2014 {r['detail']}")
        if not emc.get("resolved") and not emc.get("improved") and not emc.get("new_findings"):
            lines.append("  No EMC findings changed.")
        lines.append("")

    return "\n".join(lines)


def _format_sweep_table(sweep_result: dict) -> str:
    """Format sweep results as markdown tables."""
    lines = []
    ref = sweep_result["ref"]
    strs = sweep_result["value_strs"]
    results = sweep_result["results"]
    lines.append(f"Sweep: {ref} = {', '.join(strs)}")
    lines.append("")

    if not results or not results[0].get("affected_subcircuits"):
        lines.append("  No subcircuits affected.")
        return "\n".join(lines)

    n_subs = len(results[0]["affected_subcircuits"])
    for si in range(n_subs):
        label = results[0]["affected_subcircuits"][si]["label"]
        lines.append(f"### {label}")
        lines.append("")

        # Collect all fields across all steps
        all_fields = []
        for step in results:
            if si < len(step["affected_subcircuits"]):
                for d in step["affected_subcircuits"][si].get("delta", []):
                    if d["field"] not in all_fields:
                        all_fields.append(d["field"])

        if not all_fields:
            continue

        # Build markdown table
        col_w = max(8, max(len(s) for s in strs) + 2)
        header = f"| {'Metric':<16}|"
        sep = f"|{'-' * 17}|"
        for s in strs:
            header += f" {s:>{col_w - 1}} |"
            sep += f"{'-' * (col_w + 1)}:|"
        lines.append(header)
        lines.append(sep)

        for field in all_fields:
            row = f"| {field:<16}|"
            for step in results:
                val = None
                if si < len(step["affected_subcircuits"]):
                    val = step["affected_subcircuits"][si].get("after", {}).get(field)
                cell = _format_value(val, field) if val is not None else "-"
                row += f" {cell:>{col_w - 1}} |"
            lines.append(row)

        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Inverse solver for --fix mode
# ---------------------------------------------------------------------------

def _solve_fix(det: dict, det_type: str, target_field: str,
               target_value: float) -> list:
    """Compute ideal component values to achieve target.

    Uses inverse solver from detection schema. Returns suggestions with
    E-series snapped alternatives.
    """
    from detection_schema import get_inverse_solver
    from kicad_utils import snap_to_e_series

    inverse = get_inverse_solver(det_type, target_field)
    if inverse is None:
        return []

    suggestions = inverse(det, target_field, target_value)

    # Add E-series snapped values
    for s in suggestions:
        s["e_series"] = {}
        for series in ("E12", "E24", "E96"):
            snapped, err = snap_to_e_series(s["ideal"], series)
            s["e_series"][series] = {"value": snapped, "error_pct": err}

    return suggestions


# ---------------------------------------------------------------------------
# Auto-fix scanner — identify out-of-spec detections with known targets
# ---------------------------------------------------------------------------

def _scan_fixable(signal_analysis: dict) -> list:
    """Scan signal analysis for detections that are out-of-spec with known targets.

    Returns list of dicts, each describing a fixable issue:
      {detection_type, index, det, target_field, target_value,
       issue, confidence, category}

    Categories:
      'value_fix' — component value change via inverse solver
      'derating'  — package or voltage rating recommendation
    """
    from kicad_utils import parse_voltage_from_net_name

    issues = []

    # --- 1. Feedback divider Vout mismatch ---
    # Check if regulator estimated_vout differs from voltage in rail name
    for i, reg in enumerate(signal_analysis.get("power_regulators", [])):
        fb = reg.get("feedback_divider")
        if not fb:
            continue
        vout = reg.get("estimated_vout")
        vref = reg.get("assumed_vref")
        if not vout or not vref or vref <= 0:
            continue
        rail = reg.get("output_rail", "")
        rail_v = parse_voltage_from_net_name(rail)
        if rail_v is None or rail_v <= 0:
            continue
        # Compare estimated_vout with voltage parsed from rail name
        error_pct = abs(vout - rail_v) / rail_v * 100
        if error_pct < 2.0:
            continue  # Close enough — not fixable
        # Target ratio: Vref / desired_Vout
        target_ratio = vref / rail_v
        if target_ratio <= 0 or target_ratio >= 1:
            continue
        # Find this divider in voltage_dividers or feedback_networks
        fb_r_top_ref = fb.get("r_top", {}).get("ref", "")
        fb_r_bot_ref = fb.get("r_bottom", {}).get("ref", "")
        det_type = None
        det_idx = None
        det_obj = None
        for dtype in ("feedback_networks", "voltage_dividers"):
            for j, vd in enumerate(signal_analysis.get(dtype, [])):
                if (vd.get("r_top", {}).get("ref") == fb_r_top_ref and
                        vd.get("r_bottom", {}).get("ref") == fb_r_bot_ref):
                    det_type, det_idx, det_obj = dtype, j, vd
                    break
            if det_type:
                break
        if not det_type:
            continue
        ref_reg = reg.get("ref", reg.get("reference", ""))
        confidence = "deterministic" if reg.get("vref_source") == "lookup" else "heuristic"
        issues.append({
            "detection_type": det_type,
            "index": det_idx,
            "det": det_obj,
            "target_field": "ratio",
            "target_value": target_ratio,
            "issue": (
                "{ref} feedback divider: Vout={vout:.3g}V but rail "
                "'{rail}' implies {rail_v}V (error {err:.1f}%)"
            ).format(ref=ref_reg, vout=vout, rail=rail,
                     rail_v=rail_v, err=error_pct),
            "confidence": confidence,
            "category": "value_fix",
        })

    # --- 2. Crystal load capacitance mismatch ---
    for i, xtal in enumerate(signal_analysis.get("crystal_circuits", [])):
        status = xtal.get("load_cap_status")
        if status in ("ok", None):
            continue
        source = xtal.get("target_load_source")
        if source == "frequency_default":
            continue  # Low confidence target — skip auto-fix
        target = xtal.get("target_load_pF")
        actual = xtal.get("effective_load_pF")
        if not target or not actual:
            continue
        error_pct = abs(actual - target) / target * 100
        if error_pct < 10:
            continue
        xref = xtal.get("reference", "Y?")
        issues.append({
            "detection_type": "crystal_circuits",
            "index": i,
            "det": xtal,
            "target_field": "effective_load_pF",
            "target_value": target,
            "issue": (
                "{ref} load capacitance: {actual:.1f}pF vs {target:.1f}pF "
                "target ({err:.0f}% error, status={status})"
            ).format(ref=xref, actual=actual, target=target,
                     err=error_pct, status=status),
            "confidence": "deterministic",
            "category": "value_fix",
        })

    # --- 3. Output capacitor DC bias derating ---
    for i, reg in enumerate(signal_analysis.get("power_regulators", [])):
        ref_reg = reg.get("ref", reg.get("reference", ""))
        vout = reg.get("vout_estimated") or reg.get("estimated_vout")
        rail = reg.get("output_rail", "")
        for cap in reg.get("output_capacitors", []):
            df = cap.get("derating_factor")
            if df is None or df >= 0.5:
                continue
            cap_ref = cap.get("ref", "?")
            package = cap.get("package", "?")
            dielectric = cap.get("dielectric", "?")
            nominal_uf = cap.get("farads", 0) * 1e6
            effective_uf = cap.get("effective_farads", 0) * 1e6
            issues.append({
                "detection_type": "power_regulators",
                "index": i,
                "det": None,  # Not a value fix — recommendation only
                "target_field": None,
                "target_value": None,
                "issue": (
                    "{cap_ref} ({nominal:.1f}uF {dielectric} {pkg}) on "
                    "{rail_or_reg}: {df:.0f}% effective capacitance "
                    "({eff:.1f}uF of {nom:.1f}uF)"
                ).format(cap_ref=cap_ref, nominal=nominal_uf,
                         dielectric=dielectric, pkg=package,
                         rail_or_reg=rail or ref_reg,
                         df=df * 100, eff=effective_uf, nom=nominal_uf),
                "confidence": "medium",
                "category": "derating",
                "cap_ref": cap_ref,
                "cap_package": package,
                "cap_dielectric": dielectric,
                "derating_factor": df,
            })

    return issues


def _suggest_all_fixes(issues: list, pcb_analysis: dict = None) -> dict:
    """Compute fix suggestions for all scanned issues.

    For 'value_fix' issues: runs inverse solver + E-series snapping.
    For 'derating' issues: generates package/voltage recommendations.

    Returns dict with 'fix_suggestions' and 'derating_recommendations' lists.
    """
    fix_suggestions = []
    derating_recs = []

    for issue in issues:
        if issue["category"] == "value_fix":
            det = issue["det"]
            det_type = issue["detection_type"]
            target_field = issue["target_field"]
            target_value = issue["target_value"]

            suggestions = _solve_fix(det, det_type, target_field, target_value)
            if not suggestions:
                continue

            # Compute before/after for the best suggestion (first one)
            best = suggestions[0]
            best_e24 = best.get("e_series", {}).get("E24", {}).get("value")
            if best_e24 and best_e24 > 0:
                # Simulate fix with E24 value
                changes = {best["ref"]: (best_e24, _format_value(best_e24, best["field"]))}
                matched = {best["ref"]: _find_refs_in_det(det).get(best["ref"], [])}
                if matched[best["ref"]]:
                    patched = _apply_changes(det, changes, matched, det_type=det_type)
                    delta = _compare(det, patched, det_type)
                else:
                    delta = []
            else:
                delta = []

            entry = {
                "detection_type": det_type,
                "detection_index": issue["index"],
                "issue": issue["issue"],
                "confidence": issue["confidence"],
                "target_field": target_field,
                "target_value": target_value,
                "suggestions": suggestions,
                "delta_with_e24": delta,
            }
            if pcb_analysis:
                fp_warnings = _check_footprint_fit(suggestions, pcb_analysis)
                if fp_warnings:
                    entry["footprint_warnings"] = fp_warnings
            fix_suggestions.append(entry)

        elif issue["category"] == "derating":
            cap_ref = issue.get("cap_ref", "?")
            package = issue.get("cap_package", "?")
            dielectric = issue.get("cap_dielectric", "?")
            df = issue.get("derating_factor", 0)

            recs = []
            # Suggest larger package
            pkg_upgrade = {
                "0402": "0603", "0603": "0805", "0805": "1206",
            }
            next_pkg = pkg_upgrade.get(package)
            if next_pkg:
                recs.append(
                    "Upgrade {ref} from {pkg} to {next_pkg} — larger "
                    "package has less DC bias derating".format(
                        ref=cap_ref, pkg=package, next_pkg=next_pkg))
            # Suggest higher voltage rating
            recs.append(
                "Use higher voltage rating for {ref} — reduces voltage "
                "ratio and derating".format(ref=cap_ref))
            # Suggest C0G if small value
            if dielectric != "C0G":
                recs.append(
                    "Consider C0G/NP0 dielectric for {ref} — no DC bias "
                    "derating (available up to ~100nF)".format(ref=cap_ref))

            derating_recs.append({
                "issue": issue["issue"],
                "confidence": issue["confidence"],
                "cap_ref": cap_ref,
                "recommendations": recs,
            })

    return {
        "fix_suggestions": fix_suggestions,
        "derating_recommendations": derating_recs,
        "summary": {
            "fixable_issues": len(fix_suggestions),
            "derating_issues": len(derating_recs),
            "total_scanned": len(issues),
        },
    }


def _format_fix(fix_result: dict) -> str:
    """Format fix suggestion results as text."""
    lines = []
    for fix in fix_result.get("fix_suggestions", []):
        det_type = fix["detection_type"]
        target = fix["target_value"]
        field = fix["target_field"]
        lines.append(f"Fix suggestion for {det_type}[{fix['detection_index']}]"
                     f" \u2014 target {field}={_format_value(target, field)}")
        lines.append("")
        for s in fix.get("suggestions", []):
            ref = s["ref"]
            current = s["current"]
            ideal = s["ideal"]
            vkey = s["field"]
            anchor = s.get("anchor_ref")
            anchor_note = f" (keeping {anchor})" if anchor else ""
            lines.append(f"  {ref}{anchor_note}:")
            lines.append(f"    Ideal:  {_format_value(ideal, vkey)}")
            for series in ("E96", "E24", "E12"):
                e = s["e_series"].get(series, {})
                ev = e.get("value", 0)
                err = e.get("error_pct", 0)
                lines.append(f"    {series}:    {_format_value(ev, vkey):>10}  ({err:+.1f}%)")
            lines.append("")
    for fix in fix_result.get("fix_suggestions", []):
        for w in fix.get("footprint_warnings", []):
            lines.append(f"  {w}")
    return "\n".join(lines)


def _format_suggestions(result: dict) -> str:
    """Format batch fix suggestion results as human-readable text."""
    lines = []
    fixes = result.get("fix_suggestions", [])
    derecs = result.get("derating_recommendations", [])
    summary = result.get("summary", {})

    lines.append("=== Fix Suggestions ===")
    lines.append("{total} issues found: {fix} fixable, {derate} derating".format(
        total=summary.get("total_scanned", 0),
        fix=summary.get("fixable_issues", 0),
        derate=summary.get("derating_issues", 0)))
    lines.append("")

    for i, fix in enumerate(fixes, 1):
        lines.append("--- Fix {i}: {issue} ---".format(i=i, issue=fix["issue"]))
        lines.append("  Confidence: {conf}".format(conf=fix["confidence"]))
        lines.append("  Target: {field} = {val}".format(
            field=fix["target_field"],
            val=_format_value(fix["target_value"], fix["target_field"])))
        lines.append("")
        for s in fix.get("suggestions", []):
            ref = s["ref"]
            current = s["current"]
            ideal = s["ideal"]
            vkey = s["field"]
            anchor = s.get("anchor_ref")
            anchor_note = " (keeping {a})".format(a=anchor) if anchor else ""
            lines.append("  {ref}{note}:".format(ref=ref, note=anchor_note))
            lines.append("    Current: {cur}".format(
                cur=_format_value(current, vkey)))
            lines.append("    Ideal:   {ideal}".format(
                ideal=_format_value(ideal, vkey)))
            for series in ("E96", "E24", "E12"):
                e = s.get("e_series", {}).get(series, {})
                ev = e.get("value", 0)
                err = e.get("error_pct", 0)
                lines.append("    {ser}:     {val:>10}  ({err:+.1f}%)".format(
                    ser=series, val=_format_value(ev, vkey), err=err))
            lines.append("")
        delta = fix.get("delta_with_e24", [])
        if delta:
            lines.append("  Impact (with E24 value):")
            for d in delta:
                lines.append("    {field}: {before} -> {after} ({pct:+.1f}%)".format(
                    field=d["field"],
                    before=_format_value(d["before"], d["field"]),
                    after=_format_value(d["after"], d["field"]),
                    pct=d.get("delta_pct", 0) or 0))
            lines.append("")
        for w in fix.get("footprint_warnings", []):
            lines.append("  Warning: {w}".format(w=w))

    if derecs:
        lines.append("")
        lines.append("=== Derating Recommendations ===")
        for i, rec in enumerate(derecs, 1):
            lines.append("")
            lines.append("--- Derating {i}: {issue} ---".format(
                i=i, issue=rec["issue"]))
            for r in rec.get("recommendations", []):
                lines.append("  * {r}".format(r=r))

    if not fixes and not derecs:
        lines.append("No fixable issues found.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# EMC impact preview
# ---------------------------------------------------------------------------

def _run_emc_preview(analysis: dict, patched_json: dict,
                     pcb_path: str = None) -> dict:
    """Run EMC analysis on original and patched JSON, return delta."""
    import subprocess
    import tempfile

    emc_script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "..", "..", "emc", "scripts", "analyze_emc.py")
    if not os.path.exists(emc_script):
        print("Warning: analyze_emc.py not found, skipping EMC preview", file=sys.stderr)
        return None

    def _run_emc(schematic_json: dict) -> dict:
        fd, sch_path = tempfile.mkstemp(suffix=".json")
        out_path = sch_path + ".emc.json"
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(schematic_json, f, indent=2)
            cmd = [sys.executable, emc_script, "--schematic", sch_path, "--output", out_path]
            if pcb_path:
                cmd.extend(["--pcb", pcb_path])
            subprocess.run(cmd, capture_output=True, timeout=30, check=False)
            if os.path.exists(out_path):
                with open(out_path) as f:
                    return json.load(f)
        except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError) as e:
            print(f"Warning: EMC analysis failed: {e}", file=sys.stderr)
        finally:
            for p in (sch_path, out_path):
                try:
                    os.unlink(p)
                except OSError:
                    pass
        return None

    before = _run_emc(analysis)
    after = _run_emc(patched_json)
    if not before or not after:
        return None

    before_risk = before.get("overall_risk", "UNKNOWN")
    after_risk = after.get("overall_risk", "UNKNOWN")
    before_findings = {f.get("rule_id", ""): f for f in before.get("findings", [])}
    after_findings = {f.get("rule_id", ""): f for f in after.get("findings", [])}

    resolved = []
    improved = []
    new_findings = []
    for rule_id, bf in before_findings.items():
        af = after_findings.get(rule_id)
        if af is None:
            resolved.append({"rule": rule_id, "detail": bf.get("summary", "")})
        elif af.get("risk_level") != bf.get("risk_level"):
            improved.append({"rule": rule_id,
                           "before": bf.get("risk_level"),
                           "after": af.get("risk_level")})
    for rule_id, af in after_findings.items():
        if rule_id not in before_findings:
            new_findings.append({"rule": rule_id, "detail": af.get("summary", "")})

    return {
        "before_risk": before_risk, "after_risk": after_risk,
        "resolved": resolved, "improved": improved,
        "new_findings": new_findings,
        "unchanged": len(before_findings) - len(resolved) - len(improved),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="What-if parameter sweep for KiCad designs"
    )
    parser.add_argument("input", help="Analyzer JSON (from analyze_schematic.py)")
    parser.add_argument("changes", nargs="*", default=[],
                        help="REF=VALUE pairs (e.g., R5=4.7k C3=22n)")
    parser.add_argument("--spice", action="store_true",
                        help="Re-run SPICE simulations on affected subcircuits")
    parser.add_argument("--output", "-o",
                        help="Write patched analysis JSON to file")
    parser.add_argument("--text", action="store_true",
                        help="Human-readable text output")
    parser.add_argument("--emc", action="store_true",
                        help="Show EMC impact preview (runs analyze_emc.py)")
    parser.add_argument("--pcb",
                        help="PCB analysis JSON for parasitic awareness")
    parser.add_argument("--fix",
                        help="Detection to fix (e.g., voltage_dividers[0])")
    parser.add_argument("--target", type=float,
                        help="Target value for --fix (e.g., 3.3 for Vout, 1000 for Hz)")
    parser.add_argument("--suggest-fixes", action="store_true",
                        help="Scan analysis for fixable issues and suggest component changes")
    parser.add_argument("--only-deterministic", action="store_true",
                        help="Read raw analysis/<run>/<analyzer>.json instead of "
                             "analysis/merged/<run>/<analyzer>.json. "
                             "Strips Layer 2 overlays for CI/offline use (Phase 4 spec §3.4).")
    args = parser.parse_args()

    if not args.changes and not args.fix and not args.suggest_fixes:
        parser.error("at least one REF=VALUE change, --fix, or --suggest-fixes is required")

    # Load analysis JSON (honor --only-deterministic: skip merged/ overlay)
    def _resolve_input_path(path):
        from pathlib import Path
        p = Path(path)
        if not args.only_deterministic:
            candidate = p.parent.parent / "merged" / p.parent.name / p.name
            if candidate.exists():
                return candidate
        return p

    try:
        with open(_resolve_input_path(args.input)) as f:
            analysis = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error reading {args.input}: {e}", file=sys.stderr)
        sys.exit(1)

    if is_old_schema(analysis):
        print("Error: this JSON uses the pre-v1.3 signal_analysis wrapper "
              "format.\nRe-run analyze_schematic.py to produce the current "
              "findings[] format.", file=sys.stderr)
        sys.exit(1)

    signal = group_findings_by_detection_type(analysis)
    if not signal:
        print("Error: no subcircuit findings in input JSON", file=sys.stderr)
        sys.exit(1)

    # Load PCB analysis if available
    pcb_path = args.pcb
    pcb_analysis = None
    if pcb_path:
        try:
            with open(pcb_path) as f:
                pcb_analysis = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: cannot load PCB analysis: {e}", file=sys.stderr)
    else:
        auto_pcb = _find_pcb_analysis(args.input)
        if auto_pcb:
            try:
                with open(auto_pcb) as f:
                    pcb_analysis = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

    # --- Suggest-fixes branch ---
    if args.suggest_fixes:
        issues = _scan_fixable(signal)
        result = _suggest_all_fixes(issues, pcb_analysis)
        if args.text:
            print(_format_suggestions(result))
        else:
            json.dump(result, sys.stdout, indent=2)
            print()
        sys.exit(0)

    # --- Fix branch ---
    if args.fix:
        import re as _re
        m = _re.match(r'(\w+)\[(\d+)\]', args.fix)
        if not m:
            print(f"Error: invalid --fix target '{args.fix}' \u2014 use type[index] "
                  f"(e.g., voltage_dividers[0])", file=sys.stderr)
            sys.exit(1)
        fix_det_type = m.group(1)
        fix_idx = int(m.group(2))
        dets = signal.get(fix_det_type, [])
        if fix_idx >= len(dets):
            print(f"Error: {fix_det_type}[{fix_idx}] does not exist "
                  f"(have {len(dets)} detections)", file=sys.stderr)
            sys.exit(1)
        det = dets[fix_idx]

        if args.target is not None:
            from detection_schema import get_derived_field_names
            fields = get_derived_field_names(fix_det_type)
            target_field = fields[0] if fields else "ratio"
            target_value = args.target
        else:
            # Try to infer target from context
            target_field, target_value = None, None
            if fix_det_type in ("voltage_dividers", "feedback_networks"):
                vref = det.get("regulator_vref")
                vout = det.get("target_vout")
                if vref and vout and vout > 0:
                    target_field, target_value = "ratio", vref / vout
            elif fix_det_type == "crystal_circuits":
                tl = det.get("target_load_pF")
                if tl:
                    target_field, target_value = "effective_load_pF", tl
            if target_field is None:
                print(f"Error: cannot infer target for {fix_det_type} \u2014 use --target",
                      file=sys.stderr)
                sys.exit(1)

        suggestions = _solve_fix(det, fix_det_type, target_field, target_value)
        result = {"fix_suggestions": [{
            "detection_type": fix_det_type,
            "detection_index": fix_idx,
            "target_field": target_field,
            "target_value": target_value,
            "suggestions": suggestions,
        }]}
        if pcb_analysis:
            fp_warnings = _check_footprint_fit(suggestions, pcb_analysis)
            if fp_warnings:
                result["fix_suggestions"][0]["footprint_warnings"] = fp_warnings
        if args.text:
            print(_format_fix(result))
        else:
            json.dump(result, sys.stdout, indent=2)
            print()
        sys.exit(0)

    # Parse changes — returns (dict of Change, optional SweepSpec)
    changes, sweep = _parse_changes(args.changes)

    # Verify refs exist in the analysis
    all_refs = set()
    for comp in analysis.get("components", []):
        if "reference" in comp:
            all_refs.add(comp["reference"])
    for ref in changes:
        if ref not in all_refs:
            print(f"Warning: {ref} not found in component list", file=sys.stderr)
    if sweep and sweep.ref not in all_refs:
        print(f"Warning: {sweep.ref} not found in component list", file=sys.stderr)

    # --- Sweep branch ---
    if sweep is not None:
        sweep_result = _run_sweep(analysis, sweep, changes, spice=args.spice)
        if args.text:
            print(_format_sweep_table(sweep_result))
        else:
            json.dump(sweep_result, sys.stdout, indent=2)
            print()
        sys.exit(0)

    # --- Single-value branch ---
    # Convert Change objects to legacy (value, str) tuples for downstream functions
    changes_legacy = {ref: (c.value, c.value_str) for ref, c in changes.items()}

    # Find affected detections
    affected = _find_affected(signal, changes_legacy)
    if not affected:
        print(f"No subcircuits reference {', '.join(changes_legacy.keys())}",
              file=sys.stderr)
        result = {
            "changes": {ref: {"before": None, "after": val, "after_str": vstr}
                        for ref, (val, vstr) in changes_legacy.items()},
            "affected_subcircuits": [],
            "summary": {"components_changed": len(changes_legacy),
                        "subcircuits_affected": 0, "spice_verified": False},
        }
        if args.text:
            print(format_text(result))
        else:
            json.dump(result, sys.stdout, indent=2)
            print()
        sys.exit(0)

    # Apply changes to each affected detection
    patched_dets = []
    for det_type, idx, det, matched in affected:
        patched = _apply_changes(det, changes_legacy, matched, det_type=det_type)
        patched_dets.append(patched)

    # Build before/after comparisons
    subcircuit_results = []
    for (det_type, idx, det, matched), patched in zip(affected, patched_dets):
        deltas = _compare(det, patched, det_type)
        label = _get_det_label(det, det_type)
        comps = []
        refs_in_det = _find_refs_in_det(det)
        for r in refs_in_det:
            comps.append(r)

        entry = {
            "type": det_type,
            "label": label,
            "components": comps,
            "delta": deltas,
            "before": {d["field"]: d["before"] for d in deltas},
            "after": {d["field"]: d["after"] for d in deltas},
        }
        subcircuit_results.append(entry)

    # PCB parasitics
    if pcb_analysis:
        for (det_type, idx, det, matched), sc in zip(affected, subcircuit_results):
            paras = _extract_parasitics(pcb_analysis, det, det_type)
            if paras:
                sc["parasitics"] = paras

    # Tolerance analysis
    has_tolerance = any(c.tolerance is not None for c in changes.values())
    if has_tolerance:
        tol_results = _run_tolerance(analysis, changes, spice=args.spice)
        for tr in tol_results:
            for sc in subcircuit_results:
                if sc["type"] == tr["type"] and sc["label"] == tr["label"]:
                    sc["tolerance"] = tr.get("tolerance", [])

    # Optional SPICE
    spice_results = {}
    if args.spice:
        spice_results = _run_spice_comparison(affected, patched_dets, analysis)
        for i, (det_type, idx, _det, _matched) in enumerate(affected):
            key = (det_type, idx)
            if key in spice_results:
                subcircuit_results[i]["spice_delta"] = spice_results[key]

    # Build change info with before values
    change_info = {}
    for ref, (new_val, new_str) in changes_legacy.items():
        # Find the original value
        old_val = None
        old_str = ""
        for comp in analysis.get("components", []):
            if comp.get("reference") == ref:
                old_str = comp.get("value", "")
                pv = comp.get("parsed_value", {})
                if isinstance(pv, dict):
                    old_val = pv.get("value")
                break
        change_info[ref] = {
            "before": old_val,
            "after": new_val,
            "before_str": old_str,
            "after_str": new_str,
            "unit": "ohms" if ref.startswith("R") else
                    "farads" if ref.startswith("C") else
                    "henries" if ref.startswith("L") else "unknown",
        }

    result = {
        "changes": change_info,
        "affected_subcircuits": subcircuit_results,
        "summary": {
            "components_changed": len(changes_legacy),
            "subcircuits_affected": len(affected),
            "spice_verified": bool(spice_results),
        },
    }

    # EMC impact preview
    if args.emc:
        patched_json = _patch_full_json(analysis, affected, patched_dets, changes_legacy)
        pcb = getattr(args, "pcb", None)
        emc_delta = _run_emc_preview(analysis, patched_json, pcb_path=pcb)
        if emc_delta:
            result["emc_delta"] = emc_delta

    # Export patched JSON if requested
    if args.output:
        patched_json = _patch_full_json(analysis, affected, patched_dets, changes_legacy)
        with open(args.output, "w") as f:
            json.dump(patched_json, f, indent=2)
        print(f"Patched JSON written to {args.output}", file=sys.stderr)

    # Output results
    if args.text:
        print(format_text(result))
    elif not args.output:
        json.dump(result, sys.stdout, indent=2)
        print()


if __name__ == "__main__":
    main()
