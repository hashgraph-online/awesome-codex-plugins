#!/usr/bin/env python3
"""
Thermal hotspot estimator for KiCad designs.

Consumes schematic and PCB analyzer JSON outputs, models each power-dissipating
component as a point heat source, estimates junction temperatures, and flags
components approaching or exceeding rated limits.

Usage:
    python3 analyze_thermal.py --schematic analysis.json --pcb pcb.json
    python3 analyze_thermal.py -s analysis.json -p pcb.json --output thermal.json
    python3 analyze_thermal.py -s analysis.json -p pcb.json --text
    python3 analyze_thermal.py -s analysis.json -p pcb.json --ambient 40

Requires both schematic and PCB JSON (schematic for power data, PCB for copper
and thermal via data). Zero dependencies — Python 3.8+ stdlib only.
"""

import argparse
import json
import math
import os
import re
import sys
import time

from envelopes.thermal import ThermalEnvelope
from schema_codec import emit_schema
from inputs_builder import build_inputs, build_upstream_artifact, build_compat
from capability_mode import get_capability_mode_ref
from lookup_detectors import detect_tj_exceeds_max
from lookup_helpers import read_design_context

ANALYZER_SOURCE = "thermal"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_AMBIENT_C = 25.0
DEFAULT_TJ_MAX_C = 125.0
DEFAULT_RTHETA_JA = 150.0  # Conservative fallback °C/W
MIN_PDISS_W = 0.01  # 10mW threshold — below this, thermal is negligible

SEVERITY_WEIGHTS = {
    'error': 15, 'warning': 3, 'info': 0,
}
MAX_FINDINGS_PER_RULE = 5

# Switching regulator efficiency defaults by topology
SWITCHING_EFFICIENCY = {
    'buck': 0.87,
    'boost': 0.85,
    'buck-boost': 0.83,
    'switching': 0.85,  # generic
}

# ---------------------------------------------------------------------------
# Package thermal resistance lookup (Rθ_JA in °C/W)
# Values are JEDEC still-air conditions (no enhanced copper pour).
# PCB corrections applied separately.
# ---------------------------------------------------------------------------

PACKAGE_THERMAL_RESISTANCE = [
    # (regex pattern on footprint library string, Rθ_JA °C/W)
    # Order matters — first match wins. More specific patterns first.
    # Discrete power packages
    (r"TO-263|D2PAK", 30.0),
    (r"TO-252|DPAK", 40.0),
    (r"TO-220", 25.0),
    (r"TO-92", 200.0),
    (r"SOT-223", 60.0),
    (r"SOT-89", 100.0),
    (r"SOT-23", 250.0),  # SOT-23-3, SOT-23-5, SOT-23-6
    (r"SOT-363|SC-70", 300.0),
    # QFN/DFN — size matters
    (r"(?:QFN|DFN).*7[xX×]7", 20.0),
    (r"(?:QFN|DFN).*6[xX×]6", 22.0),
    (r"(?:QFN|DFN).*5[xX×]5", 25.0),
    (r"(?:QFN|DFN).*4[xX×]4", 35.0),
    (r"(?:QFN|DFN).*3[xX×]3", 50.0),
    (r"(?:QFN|DFN).*2[xX×]2", 70.0),
    (r"QFN|DFN", 40.0),  # generic QFN
    # TQFP/LQFP — pin count
    (r"[TL]QFP.*144", 30.0),
    (r"[TL]QFP.*100", 35.0),
    (r"[TL]QFP.*(?:64|80)", 40.0),
    (r"[TL]QFP.*48", 50.0),
    (r"[TL]QFP.*32", 60.0),
    (r"[TL]QFP", 50.0),
    # SOIC/SOP
    (r"SOIC.*16|SOP.*16", 80.0),
    (r"SOIC.*8|SOP.*8", 120.0),
    (r"SOIC|SOP", 100.0),
    # TSSOP/MSOP
    (r"TSSOP.*(?:20|24|28)", 80.0),
    (r"TSSOP.*(?:14|16)", 100.0),
    (r"TSSOP.*8", 150.0),
    (r"MSOP", 200.0),
    # BGA
    (r"BGA.*(?:256|324|400)", 20.0),
    (r"BGA", 25.0),
    # Passives — resistor packages
    (r"2512", 40.0),
    (r"2010", 60.0),
    (r"1210", 80.0),
    (r"1206", 100.0),
    (r"0805", 150.0),
    (r"0603", 200.0),
    (r"0402", 250.0),
    (r"0201", 350.0),
]

# Compiled patterns for performance
_COMPILED_PATTERNS = [(re.compile(pat, re.IGNORECASE), rtheta)
                      for pat, rtheta in PACKAGE_THERMAL_RESISTANCE]


# ---------------------------------------------------------------------------
# Package classification
# ---------------------------------------------------------------------------

def _classify_package(library_str: str) -> tuple:
    """Extract package type and Rθ_JA from PCB footprint library string.

    Returns (package_name, rtheta_ja). Falls back to ("unknown", DEFAULT_RTHETA_JA).
    """
    if not library_str:
        return ("unknown", DEFAULT_RTHETA_JA)

    # Use the footprint name (after the colon)
    name = library_str.split(":")[-1] if ":" in library_str else library_str

    for pattern, rtheta in _COMPILED_PATTERNS:
        if pattern.search(name):
            # Extract the matched portion as the package name
            m = pattern.search(name)
            return (m.group(0), rtheta)

    return ("unknown", DEFAULT_RTHETA_JA)


# ---------------------------------------------------------------------------
# Datasheet thermal data lookup
# ---------------------------------------------------------------------------

def _sanitize_mpn(mpn: str) -> str:
    """Sanitize MPN for filesystem lookup."""
    return re.sub(r'[^\w\-.]', '_', mpn.strip())


def _get_datasheet_thermal(mpn: str, extract_dir: str) -> dict:
    """Look up thermal data from datasheet extraction cache.

    Returns dict with optional keys: tj_max_c, temp_max_c.
    Rejects extractions with quality score < 6.0 (matches the trust
    gate used by datasheet_verify.py and spice_spec_fetcher.py).
    """
    if not mpn or not extract_dir:
        return {}

    safe = _sanitize_mpn(mpn)
    path = os.path.join(extract_dir, f"{safe}.json")
    if not os.path.isfile(path):
        return {}

    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}

    # Trust gate: reject low-quality extractions (matches
    # datasheet_verify.py and spice_spec_fetcher.py threshold)
    meta = data.get("meta", {})
    if meta.get("extraction_score", 0) < 6.0:
        return {}

    result = {}
    abs_max = data.get("absolute_maximum_ratings", {})
    if isinstance(abs_max, dict):
        tj = abs_max.get("junction_temp_max_c")
        if isinstance(tj, (int, float)) and tj > 0:
            result["tj_max_c"] = float(tj)

    rec_op = data.get("recommended_operating_conditions", {})
    if isinstance(rec_op, dict):
        tmax = rec_op.get("temp_max_c")
        if isinstance(tmax, (int, float)) and tmax > 0:
            result["temp_max_c"] = float(tmax)

    return result


# ---------------------------------------------------------------------------
# Power dissipation estimators
# ---------------------------------------------------------------------------

def _estimate_all_power_dissipation(schematic: dict) -> list:
    """Build list of all components with estimated power dissipation.

    Returns list of dicts with ref, value, type, pdiss_w, pdiss_source, etc.
    Only includes components with P > MIN_PDISS_W.
    """
    results = []
    regulators = [f for f in schematic.get("findings", [])
                  if f.get("detector") == "detect_power_regulators"]
    power_budget = schematic.get("power_budget", {})
    seen_refs = set()

    # 1. Linear regulators (LDOs) — use pre-computed power_dissipation
    for reg in regulators:
        ref = reg.get("ref", "")
        topology = reg.get("topology", "").lower()
        pdiss = reg.get("power_dissipation", {})

        if topology in ("ldo", "linear") and isinstance(pdiss, dict):
            p_w = pdiss.get("estimated_pdiss_W", 0)
            if p_w and p_w > MIN_PDISS_W:
                results.append({
                    "ref": ref,
                    "value": reg.get("value", ""),
                    "type": "ldo",
                    "pdiss_w": round(p_w, 4),
                    "pdiss_source": (f"({pdiss.get('vin_estimated_V', '?')}V - "
                                     f"{pdiss.get('vout_V', '?')}V) × "
                                     f"{pdiss.get('estimated_iout_A', '?')}A"),
                    "pdiss_confidence": "heuristic",
                    "vin_v": pdiss.get("vin_estimated_V"),
                    "vout_v": pdiss.get("vout_V"),
                    "iout_a": pdiss.get("estimated_iout_A"),
                })
                seen_refs.add(ref)

    # 2. Switching regulators — estimate from efficiency
    for reg in regulators:
        ref = reg.get("ref", "")
        if ref in seen_refs:
            continue
        topology = reg.get("topology", "").lower()
        if topology in ("ldo", "linear", ""):
            continue

        # Get output current estimate from power_budget
        output_rail = reg.get("output_rail", "")
        iout_a = 0
        for rail_name, rail_data in power_budget.get("rails", {}).items():
            if isinstance(rail_data, dict) and rail_name == output_rail:
                iout_a = rail_data.get("estimated_load_mA", 0) / 1000.0
                break

        vout = reg.get("estimated_vout")
        if not vout or not iout_a or iout_a <= 0:
            continue

        eta = SWITCHING_EFFICIENCY.get(topology, 0.85)
        p_out = vout * iout_a
        p_in = p_out / eta
        p_loss = p_in - p_out

        if p_loss > MIN_PDISS_W:
            results.append({
                "ref": ref,
                "value": reg.get("value", ""),
                "type": "switching_reg",
                "pdiss_w": round(p_loss, 4),
                "pdiss_source": f"{vout}V × {iout_a:.3f}A × (1/{eta:.0%} - 1)",
                "pdiss_confidence": "heuristic",
                "vout_v": vout,
                "iout_a": iout_a,
            })
            seen_refs.add(ref)

    # 3. Current sense shunt resistors — P = I²R
    current_sense = [f for f in schematic.get("findings", [])
                     if f.get("detector") == "detect_current_sense"]
    for cs in current_sense:
        shunt = cs.get("shunt", {})
        if not isinstance(shunt, dict):
            continue
        ref = shunt.get("ref", "")
        if ref in seen_refs:
            continue
        r_ohms = shunt.get("ohms", 0)
        i_max = cs.get("max_current_100mV_A", 0)
        if not r_ohms or not i_max:
            continue

        p_w = i_max * i_max * r_ohms
        if p_w > MIN_PDISS_W:
            results.append({
                "ref": ref,
                "value": shunt.get("value", ""),
                "type": "shunt_resistor",
                "pdiss_w": round(p_w, 4),
                "pdiss_source": f"{i_max:.3f}A² × {r_ohms}Ω",
                "pdiss_confidence": "deterministic",
            })
            seen_refs.add(ref)

    return results


# ---------------------------------------------------------------------------
# PCB thermal correction
# ---------------------------------------------------------------------------

def _get_pcb_thermal_correction(ref: str, pcb: dict) -> dict:
    """Compute PCB-based correction factor for a component's Rθ_JA.

    Returns dict with correction_factor (0.4-1.0), has_thermal_pad, etc.
    """
    result = {
        "correction_factor": 1.0,
        "has_thermal_pad": False,
        "thermal_vias": 0,
        "notes": [],
    }

    # Check thermal_pad_vias findings for this component
    # (entries live in findings[] with detector="analyze_thermal_pad_vias")
    for tpv in pcb.get("findings", []):
        if not isinstance(tpv, dict):
            continue
        if tpv.get("detector") != "analyze_thermal_pad_vias":
            continue
        if tpv.get("component") != ref:
            continue

        result["has_thermal_pad"] = True
        result["thermal_vias"] = tpv.get("via_count", 0)
        adequacy = tpv.get("adequacy", "none")

        if adequacy == "good":
            result["correction_factor"] *= 0.50
            result["notes"].append(
                f"thermal pad with {tpv.get('via_count', 0)} vias (good)")
        elif adequacy == "adequate":
            result["correction_factor"] *= 0.65
            result["notes"].append(
                f"thermal pad with {tpv.get('via_count', 0)} vias (adequate)")
        elif adequacy == "insufficient":
            result["correction_factor"] *= 0.80
            result["notes"].append(
                f"thermal pad with {tpv.get('via_count', 0)} vias (insufficient)")
        else:
            result["notes"].append("thermal pad but no vias")
        break

    # Check thermal_pads findings for nearby via info
    # (entries from thermal_analysis also live in findings[])
    for tp in pcb.get("findings", []):
        if not isinstance(tp, dict):
            continue
        if tp.get("component") != ref:
            continue
        nearby = tp.get("nearby_thermal_vias", 0)
        if nearby > 4 and not result["has_thermal_pad"]:
            result["correction_factor"] *= 0.70
            result["notes"].append(f"{nearby} nearby thermal vias")
        break

    # Clamp to reasonable range
    result["correction_factor"] = max(0.40, min(1.0, result["correction_factor"]))
    return result


# ---------------------------------------------------------------------------
# Junction temperature computation
# ---------------------------------------------------------------------------

def _get_footprint_map(pcb: dict) -> dict:
    """Build ref -> footprint dict from PCB data."""
    fp_map = {}
    for fp in pcb.get("footprints", []):
        if isinstance(fp, dict) and "reference" in fp:
            fp_map[fp["reference"]] = fp
    return fp_map


def _compute_junction_temps(power_comps: list, pcb: dict,
                            extract_dir: str, ambient_c: float) -> list:
    """Compute estimated junction temperature for each power component."""
    fp_map = _get_footprint_map(pcb)
    assessments = []

    for comp in power_comps:
        ref = comp["ref"]
        fp = fp_map.get(ref, {})

        # Package Rθ_JA
        library = fp.get("library", fp.get("lib_id", ""))
        pkg_name, pkg_rtheta = _classify_package(library)
        rtheta_source = "package_table" if pkg_name != "unknown" else "default"

        # Datasheet lookup for Tj_max
        mpn = ""
        for c in pcb.get("footprints", []):
            if isinstance(c, dict) and c.get("reference") == ref:
                mpn = c.get("mpn", "") or c.get("value", "")
                break
        ds_thermal = _get_datasheet_thermal(mpn, extract_dir) if extract_dir else {}

        tj_max = ds_thermal.get("tj_max_c", DEFAULT_TJ_MAX_C)
        tj_max_source = "datasheet" if "tj_max_c" in ds_thermal else "default_125"

        # PCB correction
        pcb_corr = _get_pcb_thermal_correction(ref, pcb)
        rtheta_effective = pkg_rtheta * pcb_corr["correction_factor"]

        # Junction temperature: Tj = Ta + P × Rθ_JA
        pdiss = comp["pdiss_w"]
        tj = ambient_c + pdiss * rtheta_effective
        margin = tj_max - tj

        # Position from PCB
        position = None
        if "x" in fp and "y" in fp:
            position = {"x": fp["x"], "y": fp["y"]}

        assessments.append({
            "ref": ref,
            "value": comp.get("value", ""),
            "component_type": comp["type"],
            "pdiss_w": pdiss,
            "pdiss_source": comp.get("pdiss_source", ""),
            "pdiss_confidence": comp.get("pdiss_confidence", "heuristic"),
            "package": pkg_name,
            "rtheta_ja_raw": round(pkg_rtheta, 1),
            "rtheta_ja_source": rtheta_source,
            "pcb_correction": round(pcb_corr["correction_factor"], 2),
            "pcb_correction_notes": pcb_corr["notes"],
            "rtheta_ja_effective": round(rtheta_effective, 1),
            "ambient_c": ambient_c,
            "tj_estimated_c": round(tj, 1),
            "tj_max_c": tj_max,
            "tj_max_source": tj_max_source,
            "margin_c": round(margin, 1),
            "position": position,
            "detector": "analyze_thermal",
            "rule_id": "TH-DET",
            "category": "thermal",
            "severity": "info",
            "confidence": "heuristic" if rtheta_source == "default" else "deterministic",
            "evidence_source": "datasheet" if rtheta_source == "package_table" else "heuristic_rule",
            "summary": f"Thermal: {ref} Tj={round(tj, 1)}C (margin {round(margin, 1)}C)",
            "description": f"Component {ref} in {pkg_name} package: Tj={round(tj, 1)}C, margin {round(margin, 1)}C to Tj_max ({tj_max}C).",
            "components": [ref],
            "nets": [],
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "Thermal", "impact": "", "standard_ref": ""},
        })

    # Sort by Tj descending (hottest first)
    assessments.sort(key=lambda a: -a["tj_estimated_c"])
    return assessments


# ---------------------------------------------------------------------------
# Finding generation
# ---------------------------------------------------------------------------

def _thermal_confidence(assessment: dict) -> str:
    """Determine confidence level from assessment data sources."""
    if assessment.get("rtheta_ja_source") == "default":
        return "heuristic"
    if assessment.get("tj_max_source") == "default_125":
        return "heuristic"
    return "datasheet-backed"


def _generate_findings(assessments: list) -> list:
    """Generate thermal findings from assessments."""
    findings = []

    for a in assessments:
        ref = a["ref"]
        val = a["value"]
        tj = a["tj_estimated_c"]
        tj_max = a["tj_max_c"]
        margin = a["margin_c"]
        pdiss = a["pdiss_w"]
        pkg = a["package"]
        confidence = _thermal_confidence(a)
        ev_source = ("datasheet" if a.get("rtheta_ja_source") == "package_table"
                     else "heuristic_rule")

        label = f"{ref} ({val})" if val else ref

        if tj > tj_max:
            findings.append({
                "category": "thermal_safety",
                "severity": "error",
                "rule_id": "TS-001",
                "confidence": confidence,
                "title": f"{label} estimated Tj {tj:.0f}°C exceeds abs max {tj_max:.0f}°C",
                "description": (
                    f"{a['component_type']} dissipates {pdiss:.3f}W in {pkg} package "
                    f"(Rθ_JA={a['rtheta_ja_effective']:.0f}°C/W). "
                    f"Source: {a['pdiss_source']}."
                ),
                "components": [ref],
                "recommendation": (
                    "Reduce power dissipation (lower Vin, reduce load), improve "
                    "thermal path (add thermal vias, larger copper pour), or use "
                    "a more efficient topology (switching regulator instead of LDO)."
                ),
                "detector": "analyze_thermal",
                "summary": f"{label} estimated Tj {tj:.0f}°C exceeds abs max {tj_max:.0f}°C",
                "nets": [],
                "pins": [],
                "evidence_source": ev_source,
                "report_context": {"section": "Thermal Safety", "impact": "Component reliability", "standard_ref": ""},
            })
        elif margin < 15:
            findings.append({
                "category": "thermal_safety",
                "severity": "error",
                "rule_id": "TS-002",
                "confidence": confidence,
                "title": f"{label} estimated Tj {tj:.0f}°C — only {margin:.0f}°C margin to abs max",
                "description": (
                    f"{a['component_type']} dissipates {pdiss:.3f}W in {pkg} package "
                    f"(Rθ_JA={a['rtheta_ja_effective']:.0f}°C/W). "
                    f"Margin to {tj_max:.0f}°C abs max is {margin:.0f}°C — "
                    f"may exceed limit at elevated ambient."
                ),
                "components": [ref],
                "recommendation": (
                    "Verify thermal design at worst-case ambient temperature. "
                    "Consider improving thermal path or reducing input-output "
                    "voltage differential."
                ),
                "detector": "analyze_thermal",
                "summary": f"{label} estimated Tj {tj:.0f}°C — only {margin:.0f}°C margin to abs max",
                "nets": [],
                "pins": [],
                "evidence_source": ev_source,
                "report_context": {"section": "Thermal Safety", "impact": "Component reliability", "standard_ref": ""},
            })
        elif tj > 85:
            findings.append({
                "category": "thermal_safety",
                "severity": "warning",
                "rule_id": "TS-003",
                "confidence": confidence,
                "title": f"{label} estimated Tj {tj:.0f}°C may affect nearby components",
                "description": (
                    f"{a['component_type']} runs hot at {tj:.0f}°C "
                    f"({pdiss:.3f}W in {pkg}). "
                    f"Nearby MLCCs may lose capacitance due to temperature "
                    f"coefficient effects."
                ),
                "components": [ref],
                "recommendation": (
                    "Verify nearby ceramic capacitors maintain adequate "
                    "capacitance at this temperature. Consider spacing "
                    "temperature-sensitive components away from heat source."
                ),
                "detector": "analyze_thermal",
                "summary": f"{label} estimated Tj {tj:.0f}°C may affect nearby components",
                "nets": [],
                "pins": [],
                "evidence_source": ev_source,
                "report_context": {"section": "Thermal Safety", "impact": "Component reliability", "standard_ref": ""},
            })
        elif pdiss > 0.1:
            findings.append({
                "category": "thermal_safety",
                "severity": "info",
                "rule_id": "TS-005",
                "confidence": confidence,
                "title": f"{label} Tj {tj:.0f}°C, margin {margin:.0f}°C",
                "description": (
                    f"{a['component_type']} dissipates {pdiss:.3f}W in {pkg} — "
                    f"within safe thermal limits."
                ),
                "components": [ref],
                "recommendation": "",
                "detector": "analyze_thermal",
                "summary": f"{label} Tj {tj:.0f}°C, margin {margin:.0f}°C",
                "nets": [],
                "pins": [],
                "evidence_source": ev_source,
                "report_context": {"section": "Thermal Safety", "impact": "Component reliability", "standard_ref": ""},
            })

    # TS-004: High-power component with no thermal vias
    for a in assessments:
        if a["pdiss_w"] > 0.5 and a["pcb_correction"] >= 0.95:
            ref = a["ref"]
            val = a["value"]
            label = f"{ref} ({val})" if val else ref
            findings.append({
                "category": "thermal_safety",
                "severity": "warning",
                "rule_id": "TS-004",
                "confidence": "deterministic",
                "title": f"{label} dissipates {a['pdiss_w']:.2f}W with no thermal vias",
                "description": (
                    f"{a['component_type']} in {a['package']} package dissipates "
                    f"{a['pdiss_w']:.3f}W but no thermal pad vias were detected. "
                    f"Heat removal relies entirely on surface copper."
                ),
                "components": [ref],
                "recommendation": (
                    "Add thermal vias under the component's thermal pad or "
                    "exposed pad. Minimum 5 vias for QFN, more for larger pads."
                ),
                "detector": "analyze_thermal",
                "summary": f"{label} dissipates {a['pdiss_w']:.2f}W with no thermal vias",
                "nets": [],
                "pins": [],
                "evidence_source": "geometry",
                "report_context": {"section": "Thermal Safety", "impact": "Component reliability", "standard_ref": ""},
            })

    return findings


# ---------------------------------------------------------------------------
# Thermal proximity warnings
# ---------------------------------------------------------------------------

def _check_thermal_proximity(assessments: list, pcb: dict) -> list:
    """Check for temperature-sensitive components near hot spots."""
    findings = []
    fp_map = _get_footprint_map(pcb)

    # Find hot components (Tj > 70°C) with known positions
    hot_comps = [a for a in assessments
                 if a["tj_estimated_c"] > 70 and a.get("position")]

    if not hot_comps:
        return findings

    # Find capacitors in PCB footprints
    caps = []
    for fp in pcb.get("footprints", []):
        if not isinstance(fp, dict):
            continue
        ref = fp.get("reference", "")
        if not ref.startswith("C"):
            continue
        if "x" not in fp or "y" not in fp:
            continue
        value = fp.get("value", "").lower()
        is_elec = any(k in value for k in ("elec", "tant", "polar", "aluminum"))
        caps.append({
            "ref": ref, "x": fp["x"], "y": fp["y"],
            "value": fp.get("value", ""), "is_electrolytic": is_elec,
        })

    # Check proximity
    for hot in hot_comps:
        hx, hy = hot["position"]["x"], hot["position"]["y"]
        for cap in caps:
            dx = cap["x"] - hx
            dy = cap["y"] - hy
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 10.0:  # 10mm threshold
                continue

            hot_label = f"{hot['ref']} ({hot.get('value', '')})"
            if cap["is_electrolytic"]:
                findings.append({
                    "category": "thermal_proximity",
                    "severity": "warning",
                    "rule_id": "TP-002",
                    "confidence": "deterministic",
                    "title": (f"Electrolytic {cap['ref']} ({cap['value']}) "
                              f"is {dist:.1f}mm from {hot_label} "
                              f"(Tj={hot['tj_estimated_c']:.0f}°C)"),
                    "description": (
                        "Electrolytic and tantalum capacitors have reduced "
                        "lifetime at elevated temperatures. Every 10°C above "
                        "rated temperature halves expected lifetime."
                    ),
                    "components": [cap["ref"], hot["ref"]],
                    "recommendation": (
                        "Move capacitor away from heat source or use a "
                        "ceramic capacitor rated for higher temperature."
                    ),
                    "detector": "analyze_thermal",
                    "summary": (f"Electrolytic {cap['ref']} ({cap['value']}) "
                                f"is {dist:.1f}mm from {hot_label} "
                                f"(Tj={hot['tj_estimated_c']:.0f}°C)"),
                    "nets": [],
                    "pins": [],
                    "evidence_source": "geometry",
                    "report_context": {"section": "Thermal Proximity", "impact": "Component reliability", "standard_ref": ""},
                })
            else:
                findings.append({
                    "category": "thermal_proximity",
                    "severity": "info",
                    "rule_id": "TP-001",
                    "confidence": "deterministic",
                    "title": (f"MLCC {cap['ref']} is {dist:.1f}mm from "
                              f"{hot_label} (Tj={hot['tj_estimated_c']:.0f}°C)"),
                    "description": (
                        "Ceramic capacitors lose effective capacitance at "
                        "elevated temperatures. X7R loses ~15% at 85°C, "
                        "X5R loses ~30%."
                    ),
                    "components": [cap["ref"], hot["ref"]],
                    "recommendation": (
                        "Verify capacitor maintains adequate capacitance "
                        "at the elevated temperature, or use C0G/NP0 "
                        "dielectric for temperature-critical applications."
                    ),
                    "detector": "analyze_thermal",
                    "summary": (f"MLCC {cap['ref']} is {dist:.1f}mm from "
                                f"{hot_label} (Tj={hot['tj_estimated_c']:.0f}°C)"),
                    "nets": [],
                    "pins": [],
                    "evidence_source": "geometry",
                    "report_context": {"section": "Thermal Proximity", "impact": "Component reliability", "standard_ref": ""},
                })

    return findings


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def compute_thermal_score(findings: list) -> int:
    """Compute thermal safety score from 0 (worst) to 100 (best)."""
    by_rule = {}
    for f in findings:
        rule = f.get("rule_id", "")
        by_rule.setdefault(rule, []).append(f)

    penalty = 0
    sev_order = {'error': 0, 'warning': 1, 'info': 2}
    for rule, rule_findings in by_rule.items():
        rule_findings.sort(key=lambda f: sev_order.get(f.get('severity', 'info'), 3))
        for f in rule_findings[:MAX_FINDINGS_PER_RULE]:
            penalty += SEVERITY_WEIGHTS.get(f.get('severity', 'info'), 0)

    return max(0, min(100, 100 - penalty))


_NO_COMPONENTS_REASON = (
    "No components had quantifiable power dissipation data "
    "(missing MPNs or no datasheet extraction cache)"
)


def _resolve_score(findings: list, assessments: list):
    """Return (score, skipped_reason). Score is None when no components were
    assessable — a 100/100 default in that case would falsely suggest a clean
    thermal pass when the analyzer had no data to evaluate (F3)."""
    if not assessments:
        return None, _NO_COMPONENTS_REASON
    return compute_thermal_score(
        [f for f in findings if not f.get("suppressed")]), None


# ---------------------------------------------------------------------------
# Board thermal summary
# ---------------------------------------------------------------------------

def _board_summary(assessments: list, ambient_c: float) -> dict:
    """Generate board-level thermal statistics."""
    if not assessments:
        return {
            "total_board_dissipation_w": 0,
            "components_analyzed": 0,
            "components_above_85c": 0,
            "components_above_tjmax": 0,
            "ambient_c": ambient_c,
        }

    total_p = sum(a["pdiss_w"] for a in assessments)
    above_85 = sum(1 for a in assessments if a["tj_estimated_c"] > 85)
    above_max = sum(1 for a in assessments if a["margin_c"] < 0)
    hottest = max(assessments, key=lambda a: a["tj_estimated_c"])

    return {
        "total_board_dissipation_w": round(total_p, 3),
        "hottest_component": {
            "ref": hottest["ref"],
            "tj_estimated_c": hottest["tj_estimated_c"],
        },
        "components_analyzed": len(assessments),
        "components_above_85c": above_85,
        "components_above_tjmax": above_max,
        "ambient_c": ambient_c,
    }


# ---------------------------------------------------------------------------
# Text report formatter
# ---------------------------------------------------------------------------

def format_text_report(result: dict) -> str:
    """Format thermal analysis as human-readable text."""
    lines = []
    summary = result.get("summary", {})
    findings = result.get("findings", [])
    assessments = result.get("thermal_assessments", [])

    lines.append("=" * 60)
    lines.append("THERMAL HOTSPOT ANALYSIS")
    lines.append("=" * 60)
    lines.append("")

    score = summary.get("thermal_score")
    if score is None:
        reason = summary.get("skipped_reason") or "no components analyzed"
        lines.append(f"Thermal score:   SKIPPED ({reason})")
    else:
        lines.append(f"Thermal score:   {score}/100")
    lines.append(f"Ambient temp:    {summary.get('ambient_c', 25)}°C")
    total_p = summary.get("total_board_dissipation_w", 0)
    lines.append(f"Total dissipation: {total_p:.3f}W")
    lines.append("")

    lines.append(f"Total findings:      {summary.get('total_findings', 0)}")
    lines.append(f"Components assessed: {summary.get('components_assessed', 0)}")
    lines.append(f"  CRITICAL:    {summary.get('critical', 0)}")
    lines.append(f"  HIGH:        {summary.get('high', 0)}")
    lines.append(f"  MEDIUM:      {summary.get('medium', 0)}")
    lines.append(f"  LOW:         {summary.get('low', 0)}")
    lines.append(f"  INFO:        {summary.get('info', 0)}")
    lines.append("")

    # Component thermal table
    if assessments:
        lines.append("-" * 60)
        lines.append("Component Thermal Summary")
        lines.append("-" * 60)
        lines.append(f"{'Ref':<8} {'Type':<14} {'P(W)':<8} {'Rθ_JA':<8} "
                     f"{'Tj(°C)':<8} {'Tj_max':<8} {'Margin':<8}")
        lines.append("-" * 60)
        for a in assessments:
            lines.append(
                f"{a['ref']:<8} {a['component_type']:<14} "
                f"{a['pdiss_w']:<8.3f} {a['rtheta_ja_effective']:<8.1f} "
                f"{a['tj_estimated_c']:<8.1f} {a['tj_max_c']:<8.0f} "
                f"{a['margin_c']:<8.1f}"
            )
        lines.append("")

    # Findings by severity
    if findings:
        lines.append("-" * 60)
        lines.append("Findings")
        lines.append("-" * 60)

        for f in findings:
            sev = f["severity"]
            lines.append(f"  [{sev}] {f['rule_id']}: {f['title']}")
            desc = f.get("description", "")
            for i in range(0, len(desc), 70):
                prefix = "    " if i == 0 else "      "
                lines.append(prefix + desc[i:i + 70])
            if f.get("recommendation"):
                lines.append(f"    -> {f['recommendation']}")
            lines.append("")
    else:
        lines.append("No thermal findings.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Thermal hotspot estimator for KiCad designs"
    )
    parser.add_argument("--schematic", "-s",
                        help="Schematic analyzer JSON (from analyze_schematic.py). "
                             "Auto-resolved from --analysis-dir current run when omitted.")
    parser.add_argument("--pcb", "-p",
                        help="PCB analyzer JSON (from analyze_pcb.py). "
                             "Auto-resolved from --analysis-dir current run when omitted.")
    parser.add_argument("--output", "-o",
                        help="Output JSON file path (default: stdout)")
    parser.add_argument("--text", action="store_true",
                        help="Print human-readable text report")
    parser.add_argument("--ambient", type=float, default=DEFAULT_AMBIENT_C,
                        help=f"Ambient temperature in °C (default: {DEFAULT_AMBIENT_C})")
    parser.add_argument("--datasheets", "-d",
                        help="Path to datasheets/extracted/ directory")
    parser.add_argument("--config", default=None,
                        help="Path to .kicad-happy.json project config file")
    parser.add_argument("--analysis-dir",
                        help="Write thermal.json to this directory (analysis folder convention)")
    parser.add_argument("--schema", action="store_true",
                        help="Print JSON output schema and exit")
    parser.add_argument('--stage', default=None,
                        choices=['schematic', 'layout', 'pre_fab', 'bring_up'],
                        help='Filter findings by review stage')
    parser.add_argument('--audience', default=None,
                        choices=['designer', 'reviewer', 'manager'],
                        help='Audience level for summaries and --text output')
    parser.add_argument('--only-deterministic', action='store_true',
                        help='Accepted for consistency; analyzers never write llm_* fields. '
                             'Honored by downstream consumers (Phase 4 spec §3.4).')
    args = parser.parse_args()

    if args.schema:
        emit_schema(ThermalEnvelope)

    if args.analysis_dir and (not args.schematic or not args.pcb):
        from analysis_cache import get_current_run
        from pathlib import Path as _AutoPath
        _current = get_current_run(args.analysis_dir)
        if _current is not None:
            _run_dir, _ = _current
            if not args.schematic:
                _sch = _AutoPath(_run_dir) / "schematic.json"
                if _sch.is_file():
                    args.schematic = str(_sch)
            if not args.pcb:
                _pcb = _AutoPath(_run_dir) / "pcb.json"
                if _pcb.is_file():
                    args.pcb = str(_pcb)

    if not args.schematic or not args.pcb:
        parser.error("the --schematic and --pcb arguments are required "
                     "(or pass --analysis-dir with a current run containing schematic.json and pcb.json)")

    # Load inputs
    try:
        with open(args.schematic) as f:
            schematic = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error reading schematic: {e}", file=sys.stderr)
        sys.exit(1)

    if 'signal_analysis' in schematic and 'findings' not in schematic:
        print(f'Error: {args.schematic} uses the pre-v1.3 '
              f'signal_analysis wrapper format.\n'
              f'Re-run analyze_schematic.py to produce the current '
              f'findings[] format.', file=sys.stderr)
        sys.exit(1)

    try:
        with open(args.pcb) as f:
            pcb = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error reading PCB: {e}", file=sys.stderr)
        sys.exit(1)

    # Resolve datasheets directory
    extract_dir = args.datasheets
    if not extract_dir:
        # Prefer directory of actual input file over path stored inside JSON
        input_path = args.schematic if hasattr(args, 'schematic') and args.schematic else None
        search_base = os.path.dirname(os.path.abspath(input_path)) if input_path else None
        if not search_base:
            sch_file = schematic.get("file", "")
            search_base = os.path.dirname(sch_file) if sch_file else None
        if search_base:
            candidate = os.path.join(search_base, "datasheets", "extracted")
            if os.path.isdir(candidate):
                extract_dir = candidate

    # Load project config
    try:
        from project_config import load_config_from_path, load_config, apply_suppressions
        if args.config:
            config = load_config_from_path(args.config)
        else:
            input_path = args.schematic if hasattr(args, 'schematic') and args.schematic else None
            if input_path:
                search = os.path.dirname(os.path.abspath(input_path))
            else:
                sch_file = schematic.get("file", "")
                search = os.path.dirname(sch_file) if sch_file else "."
            config = load_config(search)
    except ImportError:
        config = {"version": 1, "project": {}, "suppressions": []}

    # Apply config defaults
    project = config.get("project", {})
    if args.ambient == DEFAULT_AMBIENT_C and project.get("ambient_temperature_c"):
        args.ambient = project["ambient_temperature_c"]

    # Build inputs provenance block (Track 1.3).
    from pathlib import Path as _Path
    _sch_path = _Path(args.schematic)
    _pcb_path = _Path(args.pcb)
    _upstream_artifacts = {
        "schematic": build_upstream_artifact(_sch_path, schematic),
        "pcb": build_upstream_artifact(_pcb_path, pcb),
    }
    _cfg_path = _Path(args.config) if args.config else None
    if _cfg_path and not _cfg_path.is_file():
        _cfg_path = None

    # Resolve canonical analysis_dir ONCE (audit Highest-Risk #4) — include
    # --analysis-dir branch so capability mode lands with outputs, not in
    # ./analysis fallback.
    if hasattr(args, "analysis_dir") and args.analysis_dir:
        _analysis_dir = _Path(args.analysis_dir)
    elif args.output:
        _analysis_dir = _Path(args.output).parent
    else:
        _analysis_dir = _Path("analysis")

    # Resolve capability_mode_ref BEFORE build_inputs so inputs.run_id ==
    # capability_mode_ref.run_id (audit Highest-Risk #5).
    _capability_mode_ref = get_capability_mode_ref(_analysis_dir)

    inputs = build_inputs(
        source_files=[_sch_path, _pcb_path],
        upstream_artifacts=_upstream_artifacts,
        config_path=_cfg_path,
        run_id=_capability_mode_ref["run_id"],
    )
    compat = build_compat()

    t0 = time.monotonic()

    # Estimate power dissipation
    power_comps = _estimate_all_power_dissipation(schematic)

    # Compute junction temperatures
    assessments = _compute_junction_temps(
        power_comps, pcb, extract_dir, args.ambient)

    # Generate findings
    findings = _generate_findings(assessments)
    findings.extend(_check_thermal_proximity(assessments, pcb))

    # TJ-001 (Phase 4c): recompute TJ via v1.4 facts.base.thermal[theta_ja]
    # and compare to facts.base.absolute_max[TJ_SYNONYMS]. Soft-skip when
    # cache miss or below trust gate.
    _design_ctx = None
    if args.output:
        _design_ctx = read_design_context(_Path(args.output).parent)
    elif hasattr(args, "analysis_dir") and args.analysis_dir:
        _design_ctx = read_design_context(args.analysis_dir)
    findings.extend(detect_tj_exceeds_max(
        assessments,
        source=ANALYZER_SOURCE,
        cache_dir=extract_dir,
        design_context=_design_ctx,
    ))

    # Apply suppressions
    try:
        apply_suppressions(findings, config.get("suppressions", []))
    except NameError:
        pass  # project_config not available

    # Score (only active findings). Returns (None, reason) when no components
    # were assessable, so a missing-data run reports "skipped" rather than a
    # misleading 100/100 (F3).
    score, skipped_reason = _resolve_score(findings, assessments)

    # Severity counts over the rule findings (thermal_assessments are
    # merged into findings[] further down and contribute info-level
    # entries — a final recompute below keeps summary in sync with the
    # merged list).
    counts = {"error": 0, "warning": 0, "info": 0}
    suppressed_count = 0
    for f in findings:
        sev = str(f.get("severity", "info")).lower()
        if sev in counts:
            counts[sev] += 1
        else:
            counts["info"] += 1
        if f.get("suppressed"):
            suppressed_count += 1

    # Board summary
    board = _board_summary(assessments, args.ambient)

    elapsed = time.monotonic() - t0

    # Missing information — components with default thermal parameters.
    # Always include both keys (with [] when nothing missing) so the
    # ThermalMissingInfo schema is satisfied whenever the block is
    # emitted (TH-043). The outer `if missing_info:` guard below still
    # gates whether to emit the block at all.
    default_rtheta = [a["ref"] for a in assessments
                      if a.get("rtheta_ja_source") == "default"]
    default_tjmax = [a["ref"] for a in assessments
                     if a.get("tj_max_source") == "default_125"]
    missing_info = {}
    if default_rtheta or default_tjmax:
        missing_info["default_rtheta_ja"] = default_rtheta
        missing_info["default_tj_max"] = default_tjmax

    result = {
        "analyzer_type": "thermal",
        "schema_version": "1.4.0",
        "inputs": inputs,
        "compat": compat,
        "summary": {
            "total_findings": len(findings),
            "components_assessed": len(assessments),
            "active": len(findings) - suppressed_count,
            "suppressed": suppressed_count,
            # Standardized severity rollup (single source — raw
            # per-severity aliases were removed in v1.3 Batch 20).
            "by_severity": dict(counts),
            "thermal_score": score,
            **({"skipped_reason": skipped_reason} if skipped_reason else {}),
            **board,
        },
        "findings": findings,
        "assessments": assessments,
        "elapsed_s": round(elapsed, 3),
    }
    if missing_info:
        result["missing_info"] = missing_info

    from finding_schema import compute_trust_summary
    result["trust_summary"] = compute_trust_summary(result["findings"])

    from output_filters import apply_output_filters
    apply_output_filters(result, args.stage, args.audience)

    # Guarantee every finding carries a stable finding_id (Layer 2 merge keys
    # on it). Runs after filtering; before any output branch.
    from finding_schema import assign_finding_ids
    assign_finding_ids(result.get("findings", []), "thermal")

    # Wire capability_mode_ref (Phase 4 spec §3.3).
    from pathlib import Path as _Path
    # capability_mode_ref already resolved early — reuse to keep run_id stable.
    result["capability_mode_ref"] = _capability_mode_ref

    # Determine output path
    output_path = args.output
    analysis_dir_mode = (not output_path
                         and hasattr(args, "analysis_dir")
                         and args.analysis_dir)

    # Output
    if analysis_dir_mode:
        # Route into the current run folder via the manifest. Falls back to
        # writing at the analysis-dir root if nothing is tracked yet (first
        # ever run — shouldn't happen since schematic/pcb precede thermal,
        # but be defensive).
        import tempfile
        from analysis_cache import overwrite_current, CANONICAL_OUTPUTS, get_current_run
        analysis_dir = args.analysis_dir
        if not os.path.isabs(analysis_dir):
            analysis_dir = os.path.abspath(analysis_dir)
        filename = CANONICAL_OUTPUTS.get("thermal", "thermal.json")
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_out = os.path.join(tmp_dir, filename)
            with open(tmp_out, "w") as f:
                json.dump(result, f, indent=2)
            overwrite_current(analysis_dir, tmp_dir, source_hashes=None)
        current = get_current_run(analysis_dir)
        if current:
            out_path = os.path.join(current[0], filename)
        else:
            out_path = os.path.join(analysis_dir, filename)
        score_str = "SKIPPED" if score is None else f"{score}/100"
        print(f"Thermal analysis complete: {len(findings)} findings "
              f"(score {score_str}) -> {out_path}", file=sys.stderr)
    elif output_path:
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        score_str = "SKIPPED" if score is None else f"{score}/100"
        print(f"Thermal analysis complete: {len(findings)} findings "
              f"(score {score_str}) -> {output_path}", file=sys.stderr)
    elif args.text:
        if args.audience:
            from output_filters import format_text
            print(format_text(result.get('findings', []), args.audience, args.stage))
        else:
            print(format_text_report(result))
    else:
        json.dump(result, sys.stdout, indent=2)
        print(file=sys.stdout)


if __name__ == "__main__":
    main()
