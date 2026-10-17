"""Unified detection type schema for kicad-happy signal analysis.

Single source of truth for per-detection-type metadata consumed by:
- what_if.py (derived fields, recalculation, inverse solvers)
- spice_tolerance.py (recalculation, primary metric)
- diff_analysis.py (identity fields, value fields)

Adding a new detection type: add a DetectionSchema entry to SCHEMAS.
"""

import hashlib
import math
import os
import sys
from dataclasses import dataclass, field

# Allow importing kicad_utils from same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# Schema types
# ---------------------------------------------------------------------------

@dataclass
class DerivedField:
    """A computed field on a detection dict."""
    name: str                       # field key (e.g., "cutoff_hz")
    recalc: object                  # Callable[[dict], None] — mutates det in place
    inverse: object = None          # Callable[[dict, str, float], list] or None


@dataclass
class DetectionSchema:
    """Metadata for one detection type."""
    identity_fields: list           # dotpath fields for diffing (e.g., ["r_top.ref"])
    value_fields: list              # fields to compare in diffs (e.g., ["ratio"])
    derived: list = field(default_factory=list)  # DerivedField instances
    primary_metric: str = None      # for Monte Carlo sensitivity analysis


# ---------------------------------------------------------------------------
# Recalculation callables (relocated from spice_tolerance._recalc_derived)
# ---------------------------------------------------------------------------

_PI2 = 2.0 * math.pi


def _recalc_rc_cutoff(det: dict) -> None:
    """RC filter: cutoff_hz = 1 / (2*pi*R*C)."""
    r = det.get("resistor", {}).get("ohms")
    c = det.get("capacitor", {}).get("farads")
    if r and c and r > 0 and c > 0:
        det["cutoff_hz"] = round(1.0 / (_PI2 * r * c), 2)


def _recalc_divider_ratio(det: dict) -> None:
    """Voltage divider / feedback: ratio = R_bot / (R_top + R_bot)."""
    r_top = det.get("r_top", {}).get("ohms")
    r_bot = det.get("r_bottom", {}).get("ohms")
    if r_top and r_bot and (r_top + r_bot) > 0:
        det["ratio"] = round(r_bot / (r_top + r_bot), 6)


def _recalc_lc_filter(det: dict) -> None:
    """LC filter: resonant_hz and impedance_ohms."""
    l = det.get("inductor", {}).get("henries")
    c = det.get("capacitor", {}).get("farads")
    if l and c and l > 0 and c > 0:
        f0 = 1.0 / (_PI2 * math.sqrt(l * c))
        det["resonant_hz"] = round(f0, 2)
        det["impedance_ohms"] = round(math.sqrt(l / c), 2)


def _recalc_crystal_load(det: dict) -> None:
    """Crystal: effective_load_pF = (C1*C2)/(C1+C2) + stray."""
    caps = det.get("load_caps")
    if isinstance(caps, list) and len(caps) >= 2:
        c1 = caps[0].get("farads", 0)
        c2 = caps[1].get("farads", 0)
        if c1 > 0 and c2 > 0:
            c_series = (c1 * c2) / (c1 + c2)
            stray_pf = det.get("stray_capacitance_pF", 3.0)
            det["effective_load_pF"] = round(c_series * 1e12 + stray_pf, 2)


def _recalc_regulator_feedback(det: dict) -> None:
    """Regulator feedback divider: nested ratio."""
    fd = det.get("feedback_divider")
    if isinstance(fd, dict) and "r_top" in fd and "r_bottom" in fd:
        r_top = fd["r_top"].get("ohms")
        r_bot = fd["r_bottom"].get("ohms")
        if r_top and r_bot and (r_top + r_bot) > 0:
            fd["ratio"] = round(r_bot / (r_top + r_bot), 6)


def _recalc_opamp_gain(det: dict) -> None:
    """Opamp: gain and gain_dB from feedback/input resistors."""
    rf = det.get("feedback_resistor", {}).get("ohms")
    ri = det.get("input_resistor", {}).get("ohms")
    if rf and ri and ri > 0:
        config = det.get("configuration", "")
        if "non-inverting" in config or "non_inverting" in config:
            det["gain"] = round(1.0 + rf / ri, 4)
        elif "inverting" in config:
            det["gain"] = round(-rf / ri, 4)
        else:
            det["gain"] = round(rf / ri, 4)
        gain = det["gain"]
        if gain != 0:
            det["gain_dB"] = round(20.0 * math.log10(abs(gain)), 2)


def _recalc_current_sense(det: dict) -> None:
    """Current sense: max current at sense voltages."""
    shunt = det.get("shunt")
    if isinstance(shunt, dict):
        r = shunt.get("ohms")
        if r and r > 0:
            det["max_current_50mV_A"] = round(0.050 / r, 4)
            det["max_current_100mV_A"] = round(0.100 / r, 4)


# ---------------------------------------------------------------------------
# Inverse solver callables (relocated from what_if._solve_fix)
# ---------------------------------------------------------------------------

def _inverse_divider_ratio(det: dict, target_field: str, target_value: float) -> list:
    """Solve for R_top or R_bottom given target ratio."""
    suggestions = []
    r_top = det.get("r_top", {})
    r_bot = det.get("r_bottom", {})
    rt = r_top.get("ohms", 0)
    rb = r_bot.get("ohms", 0)
    if rt > 0 and 0 < target_value < 1:
        ideal_rb = rt * target_value / (1 - target_value)
        suggestions.append({
            "ref": r_bot.get("ref", "R_bottom"), "field": "ohms",
            "current": rb, "ideal": ideal_rb,
            "anchor_ref": r_top.get("ref", "R_top"), "anchor_value": rt,
        })
    if rb > 0 and 0 < target_value < 1:
        ideal_rt = rb * (1 - target_value) / target_value
        suggestions.append({
            "ref": r_top.get("ref", "R_top"), "field": "ohms",
            "current": rt, "ideal": ideal_rt,
            "anchor_ref": r_bot.get("ref", "R_bottom"), "anchor_value": rb,
        })
    return suggestions


def _inverse_rc_cutoff(det: dict, target_field: str, target_value: float) -> list:
    """Solve for R or C given target cutoff_hz."""
    suggestions = []
    r = det.get("resistor", {})
    c = det.get("capacitor", {})
    rv = r.get("ohms", 0)
    cv = c.get("farads", 0)
    if rv > 0 and target_value > 0:
        ideal_c = 1.0 / (_PI2 * rv * target_value)
        suggestions.append({
            "ref": c.get("ref", "C"), "field": "farads",
            "current": cv, "ideal": ideal_c,
            "anchor_ref": r.get("ref", "R"), "anchor_value": rv,
        })
    if cv > 0 and target_value > 0:
        ideal_r = 1.0 / (_PI2 * cv * target_value)
        suggestions.append({
            "ref": r.get("ref", "R"), "field": "ohms",
            "current": rv, "ideal": ideal_r,
            "anchor_ref": c.get("ref", "C"), "anchor_value": cv,
        })
    return suggestions


def _inverse_lc_resonant(det: dict, target_field: str, target_value: float) -> list:
    """Solve for L or C given target resonant_hz."""
    suggestions = []
    l = det.get("inductor", {})
    c = det.get("capacitor", {})
    lv = l.get("henries", 0)
    cv = c.get("farads", 0)
    if lv > 0 and target_value > 0:
        ideal_c = 1.0 / ((_PI2 * target_value) ** 2 * lv)
        suggestions.append({
            "ref": c.get("ref", "C"), "field": "farads",
            "current": cv, "ideal": ideal_c,
            "anchor_ref": l.get("ref", "L"), "anchor_value": lv,
        })
    if cv > 0 and target_value > 0:
        ideal_l = 1.0 / ((_PI2 * target_value) ** 2 * cv)
        suggestions.append({
            "ref": l.get("ref", "L"), "field": "henries",
            "current": lv, "ideal": ideal_l,
            "anchor_ref": c.get("ref", "C"), "anchor_value": cv,
        })
    return suggestions


def _inverse_opamp_gain(det: dict, target_field: str, target_value: float) -> list:
    """Solve for Rf given target gain (or gain_dB)."""
    target_gain = target_value
    if target_field == "gain_dB":
        target_gain = 10 ** (target_value / 20.0)
    rf = det.get("feedback_resistor", {})
    ri = det.get("input_resistor", {})
    rfv = rf.get("ohms", 0)
    riv = ri.get("ohms", 0)
    config = det.get("configuration", "")
    if riv > 0:
        if "non-inverting" in config or "non_inverting" in config:
            ideal_rf = riv * (abs(target_gain) - 1)
        else:
            ideal_rf = riv * abs(target_gain)
        if ideal_rf > 0:
            return [{
                "ref": rf.get("ref", "Rf"), "field": "ohms",
                "current": rfv, "ideal": ideal_rf,
                "anchor_ref": ri.get("ref", "Ri"), "anchor_value": riv,
            }]
    return []


def _inverse_crystal_load(det: dict, target_field: str, target_value: float) -> list:
    """Solve for symmetric load caps given target effective_load_pF."""
    caps = det.get("load_caps", [])
    stray = det.get("stray_capacitance_pF", 3.0)
    if len(caps) >= 2 and target_value > stray:
        ideal_pf = 2 * (target_value - stray)
        ideal_f = ideal_pf * 1e-12
        suggestions = []
        for cap in caps[:2]:
            suggestions.append({
                "ref": cap.get("ref", "C"), "field": "farads",
                "current": cap.get("farads", 0), "ideal": ideal_f,
                "anchor_ref": None, "anchor_value": None,
            })
        return suggestions
    return []


def _inverse_current_sense(det: dict, target_field: str, target_value: float) -> list:
    """Solve for shunt R given target max current."""
    shunt = det.get("shunt", {})
    rv = shunt.get("ohms", 0)
    if target_value > 0:
        if target_field == "max_current_100mV_A":
            ideal_r = 0.100 / target_value
        elif target_field == "max_current_50mV_A":
            ideal_r = 0.050 / target_value
        else:
            return []
        return [{
            "ref": shunt.get("ref", "R"), "field": "ohms",
            "current": rv, "ideal": ideal_r,
            "anchor_ref": None, "anchor_value": None,
        }]
    return []


# ---------------------------------------------------------------------------
# Schema registry
# ---------------------------------------------------------------------------

SCHEMAS = {
    # --- Detections with derived fields (what-if, tolerance, fix) ---
    "rc_filters": DetectionSchema(
        identity_fields=["resistor.ref", "capacitor.ref"],
        value_fields=["cutoff_hz"],
        derived=[DerivedField("cutoff_hz", _recalc_rc_cutoff, _inverse_rc_cutoff)],
        primary_metric="cutoff_hz",
    ),
    "lc_filters": DetectionSchema(
        identity_fields=["inductor.ref", "capacitor.ref"],
        value_fields=["resonant_hz"],
        derived=[
            DerivedField("resonant_hz", _recalc_lc_filter, _inverse_lc_resonant),
            DerivedField("impedance_ohms", _recalc_lc_filter),
        ],
        primary_metric="resonant_hz",
    ),
    "voltage_dividers": DetectionSchema(
        identity_fields=["r_top.ref", "r_bottom.ref"],
        value_fields=["ratio", "vout_V"],
        derived=[DerivedField("ratio", _recalc_divider_ratio, _inverse_divider_ratio)],
        primary_metric="vout_V",
    ),
    "feedback_networks": DetectionSchema(
        identity_fields=["r_top.ref", "r_bottom.ref"],
        value_fields=["ratio"],
        derived=[DerivedField("ratio", _recalc_divider_ratio, _inverse_divider_ratio)],
        primary_metric="fb_voltage_V",
    ),
    "opamp_circuits": DetectionSchema(
        identity_fields=["reference"],
        value_fields=["gain", "gain_dB", "configuration"],
        derived=[
            DerivedField("gain", _recalc_opamp_gain, _inverse_opamp_gain),
            DerivedField("gain_dB", _recalc_opamp_gain),
        ],
        primary_metric="gain_dB",
    ),
    "crystal_circuits": DetectionSchema(
        identity_fields=["reference"],
        value_fields=["frequency", "effective_load_pF"],
        derived=[DerivedField("effective_load_pF", _recalc_crystal_load, _inverse_crystal_load)],
        primary_metric="load_capacitance_pF",
    ),
    "current_sense": DetectionSchema(
        identity_fields=["shunt.ref"],
        value_fields=["max_current_50mV_A", "max_current_100mV_A"],
        derived=[
            DerivedField("max_current_50mV_A", _recalc_current_sense, _inverse_current_sense),
            DerivedField("max_current_100mV_A", _recalc_current_sense),
        ],
        primary_metric="i_at_100mV_A",
    ),
    "power_regulators": DetectionSchema(
        identity_fields=["ref"],
        value_fields=["estimated_vout", "topology"],
        derived=[DerivedField("estimated_vout", _recalc_regulator_feedback)],
        primary_metric=None,
    ),
    # --- Detections without derived fields (diff/SPICE only) ---
    "transistor_circuits": DetectionSchema(
        identity_fields=["reference"],
        value_fields=["type"],
        primary_metric="vth_V",
    ),
    "protection_devices": DetectionSchema(
        identity_fields=["reference", "type"],
        value_fields=["protected_net"],
    ),
    "bridge_circuits": DetectionSchema(
        identity_fields=["topology"],
        value_fields=[],
        primary_metric="vth_low_side_V",
    ),
    "rf_matching": DetectionSchema(
        identity_fields=["antenna_ref"],
        value_fields=[],
        primary_metric="z_min_ohms",
    ),
    "bms_systems": DetectionSchema(
        identity_fields=["bms_reference"],
        value_fields=["cell_count"],
        primary_metric="i_balance_mA",
    ),
    "decoupling_analysis": DetectionSchema(
        identity_fields=["rail_net"],
        value_fields=[],
        primary_metric="z_min_ohms",
    ),
    "rf_chains": DetectionSchema(
        identity_fields=[],
        value_fields=[],
        primary_metric="z_min_ohms",
    ),
    "ethernet_interfaces": DetectionSchema(
        identity_fields=["phy_ref"],
        value_fields=[],
    ),
    "memory_interfaces": DetectionSchema(
        identity_fields=["type"],
        value_fields=[],
    ),
    "isolation_barriers": DetectionSchema(
        identity_fields=["isolator_ref"],
        value_fields=[],
    ),
    "snubbers": DetectionSchema(
        identity_fields=[],
        value_fields=[],
        primary_metric="z_min_ohms",
    ),
    # --- Detections added for KH-233 (identity-only, no derived fields) ---
    "rail_voltages": DetectionSchema(
        identity_fields=[],
        value_fields=[],
    ),
    "addressable_led_chains": DetectionSchema(
        identity_fields=["first_led"],
        value_fields=["chain_length", "protocol"],
    ),
    "adc_circuits": DetectionSchema(
        identity_fields=["ref"],
        value_fields=["type", "interface"],
    ),
    "audio_circuits": DetectionSchema(
        identity_fields=["ref"],
        value_fields=["type", "amplifier_class"],
    ),
    "battery_chargers": DetectionSchema(
        identity_fields=["reference"],
        value_fields=["charger_type", "charger_family"],
    ),
    "buzzer_speaker_circuits": DetectionSchema(
        identity_fields=["reference"],
        value_fields=["type"],
    ),
    "clock_distribution": DetectionSchema(
        identity_fields=["ref"],
        value_fields=["type"],
    ),
    "connector_ground_audit": DetectionSchema(
        identity_fields=["ref"],
        value_fields=["status", "signal_per_ground"],
    ),
    "debug_interfaces": DetectionSchema(
        identity_fields=["connector"],
        value_fields=["interface_type"],
    ),
    "display_interfaces": DetectionSchema(
        identity_fields=["ref"],
        value_fields=["display_type", "interface"],
    ),
    "hdmi_dvi_interfaces": DetectionSchema(
        identity_fields=["reference"],
        value_fields=["type"],
    ),
    "key_matrices": DetectionSchema(
        identity_fields=[],
        value_fields=["rows", "columns", "estimated_keys"],
    ),
    "led_driver_ics": DetectionSchema(
        identity_fields=["ref"],
        value_fields=["type", "interface", "channels"],
    ),
    "level_shifters": DetectionSchema(
        identity_fields=["ref"],
        value_fields=["type", "direction", "channel_count"],
    ),
    "lvds_interfaces": DetectionSchema(
        identity_fields=["reference"],
        value_fields=["role"],
    ),
    "motor_drivers": DetectionSchema(
        identity_fields=["reference"],
        value_fields=["type"],
    ),
    "reset_supervisors": DetectionSchema(
        identity_fields=["ref"],
        value_fields=["type", "threshold_voltage"],
    ),
    "rtc_circuits": DetectionSchema(
        identity_fields=["ref"],
        value_fields=["type", "interface"],
    ),
    "sensor_interfaces": DetectionSchema(
        identity_fields=["ref"],
        value_fields=["type", "interface"],
    ),
    "suggested_certifications": DetectionSchema(
        identity_fields=["standard"],
        value_fields=["region", "reason"],
    ),
    "thermocouple_rtd": DetectionSchema(
        identity_fields=["ref"],
        value_fields=["type", "interface"],
    ),
    "validation_findings": DetectionSchema(
        identity_fields=["rule_id", "components"],
        value_fields=["severity", "summary"],
    ),
    "wireless_modules": DetectionSchema(
        identity_fields=["reference"],
        value_fields=["wireless_type", "antenna_net"],
    ),
    "transformer_feedback": DetectionSchema(
        identity_fields=["reference"],
        value_fields=["controller_type", "optocoupler"],
    ),
    "i2c_address_conflicts": DetectionSchema(
        identity_fields=["rule_id", "components"],
        value_fields=["severity"],
    ),
    "energy_harvesting": DetectionSchema(
        identity_fields=["reference"],
        value_fields=["harvester_type"],
    ),
    "pwm_led_dimming": DetectionSchema(
        identity_fields=["reference"],
        value_fields=["leds", "switch_type"],
    ),
    "headphone_jacks": DetectionSchema(
        identity_fields=["reference"],
        value_fields=["associated_codec"],
    ),
    "connectivity_graph": DetectionSchema(
        identity_fields=["net_name"],
        value_fields=["islands", "disconnected_pads"],
    ),
    "net_classifications": DetectionSchema(
        identity_fields=["net_name"],
        value_fields=["type", "frequency_hz"],
    ),
    # --- PCB rich format + assembly/DFM checks (PCB-R8) ---
    "dfm_violations": DetectionSchema(
        identity_fields=["parameter"],
        value_fields=["actual_mm", "tier_required"],
    ),
    "placement_overlaps": DetectionSchema(
        identity_fields=["component_a", "component_b"],
        value_fields=["overlap_mm2"],
    ),
    "tombstoning_risk": DetectionSchema(
        identity_fields=["component"],
        value_fields=["risk_level", "package"],
    ),
    "thermal_pad_vias": DetectionSchema(
        identity_fields=["component", "pad_number"],
        value_fields=["adequacy", "via_count"],
    ),
    "fiducial_check": DetectionSchema(
        identity_fields=["side"],
        value_fields=["fiducial_count"],
    ),
    "test_point_coverage": DetectionSchema(
        identity_fields=[],
        value_fields=["coverage_pct", "nets_with_test_points"],
    ),
    "orientation_consistency": DetectionSchema(
        identity_fields=["side"],
        value_fields=["deviator_count", "majority_angle"],
    ),
    "silkscreen_pad_overlaps": DetectionSchema(
        identity_fields=["component"],
        value_fields=["silk_layer"],
    ),
    "via_in_pad_issues": DetectionSchema(
        identity_fields=["component", "pad"],
        value_fields=["tented"],
    ),
    "keepout_violations": DetectionSchema(
        identity_fields=["component", "keepout_name"],
        value_fields=["severity"],
    ),
    "board_edge_via_clearance": DetectionSchema(
        identity_fields=["via_x", "via_y"],
        value_fields=["edge_clearance_mm"],
    ),
    # Batch 8: Remaining analyzer rich format
    "thermal_assessments": DetectionSchema(
        identity_fields=["ref"],
        value_fields=["tj_estimated_c", "margin_c"],
    ),
    "gerber_findings": DetectionSchema(
        identity_fields=["rule_id", "summary"],
        value_fields=["severity"],
    ),
    "lifecycle_findings": DetectionSchema(
        identity_fields=["mpn"],
        value_fields=["status", "severity"],
    ),
    "temperature_findings": DetectionSchema(
        identity_fields=["mpn"],
        value_fields=["component_grade"],
    ),
}


# ---------------------------------------------------------------------------
# Convenience functions for consumers
# ---------------------------------------------------------------------------

def recalc_derived(det: dict, det_type: str) -> None:
    """Recalculate all derived fields for a detection of the given type.

    Drop-in replacement for spice_tolerance._recalc_derived(), but uses
    schema-driven dispatch instead of hard-coded if/elif chains.
    """
    schema = SCHEMAS.get(det_type)
    if not schema:
        return
    seen = set()
    for df in schema.derived:
        # Avoid calling the same recalc twice (e.g., lc_filter has two fields
        # sharing _recalc_lc_filter)
        fn_id = id(df.recalc)
        if fn_id not in seen:
            df.recalc(det)
            seen.add(fn_id)


def get_derived_field_names(det_type: str) -> list:
    """Return list of derived field names for a detection type."""
    schema = SCHEMAS.get(det_type)
    if not schema:
        return []
    return [df.name for df in schema.derived]


def get_inverse_solver(det_type: str, field_name: str):
    """Return the inverse solver callable for a field, or None."""
    schema = SCHEMAS.get(det_type)
    if not schema:
        return None
    for df in schema.derived:
        if df.name == field_name and df.inverse is not None:
            return df.inverse
    # If exact field not found, try first derived field with an inverse
    for df in schema.derived:
        if df.inverse is not None:
            return df.inverse
    return None


def get_identity_and_value_fields(det_type: str) -> tuple:
    """Return (identity_fields, value_fields) for a detection type.

    Returns (["reference"], []) for unknown types (backward compat with
    diff_analysis.py fallback).
    """
    schema = SCHEMAS.get(det_type)
    if not schema:
        return (["reference"], [])
    return (schema.identity_fields, schema.value_fields)


def get_primary_metric(det_type: str) -> str:
    """Return the primary metric name for Monte Carlo, or None."""
    schema = SCHEMAS.get(det_type)
    return schema.primary_metric if schema else None


def compute_detection_id(det, det_type):
    """Compute a stable hash ID for a detection based on identity fields.

    Deterministic: same detection -> same ID across runs.  List-valued
    identity fields are sorted before hashing so upstream set/dict
    iteration order doesn't affect the ID (KH-316).

    Format: det_type:xxxxxxxxxxxx (12-char SHA-256 prefix).
    """
    schema = SCHEMAS.get(det_type)
    if not schema:
        return ""

    parts = [det_type]
    for field in schema.identity_fields:
        val = det
        for key in field.split("."):
            if isinstance(val, dict) and key in val:
                val = val[key]
            else:
                val = None
                break
        if isinstance(val, list):
            val = sorted(val, key=str)
        parts.append(str(val) if val is not None else "")

    raw = "::".join(parts)
    h = hashlib.sha256(raw.encode()).hexdigest()[:12]
    return f"{det_type}:{h}"
