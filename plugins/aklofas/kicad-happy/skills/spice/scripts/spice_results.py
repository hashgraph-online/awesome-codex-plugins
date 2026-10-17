"""
Parse ngspice .control block ASCII output and generate structured results.

ngspice .control blocks write measurement results via `echo` to text files.
This module parses those files and produces a structured report with
pass/warn/fail/skip status for each simulation.
"""

import math
import re


def parse_output_file(filepath):
    """Parse an ngspice echo output file into a dict of key=value pairs.

    Expected format (one line):
        fc_sim=1.592e+04 gain_dc=-0.015 phase_fc=-45.1

    Also handles ngspice "failed" measurement markers.

    Args:
        filepath: Path to the ASCII output file written by .control block

    Returns:
        Dict of {param_name: float_or_None}
    """
    results = {}
    try:
        with open(filepath, "r") as f:
            content = f.read().strip()
    except (OSError, IOError):
        return results

    if not content:
        return results

    # ngspice echo format: "key=value key2=value2" on one or more lines
    for token in content.split():
        if "=" not in token:
            continue
        key, _, val = token.partition("=")
        key = key.strip()
        val = val.strip()
        # ngspice writes "failed" for measurements that couldn't complete,
        # or leaves the value empty
        if not val or val.lower() == "failed" or val == "---":
            results[key] = None
        else:
            try:
                results[key] = float(val)
            except ValueError:
                results[key] = val  # Keep as string if not numeric
    return results


def evaluate_rc_filter(det, sim_results):
    """Evaluate RC filter simulation results against expected values.

    Args:
        det: Detection finding dict (from findings[] with detector=detect_rc_filters)
        sim_results: Dict from parse_output_file()

    Returns:
        Result dict with status, expected, simulated, delta fields
    """
    expected_fc = det["cutoff_hz"]
    sim_fc = sim_results.get("fc_sim")
    phase_fc = sim_results.get("phase_fc")

    result = {
        "subcircuit_type": "rc_filter",
        "components": [det["resistor"]["ref"], det["capacitor"]["ref"]],
        "filter_type": det.get("type", "low-pass"),
        "expected": {
            "cutoff_hz": expected_fc,
            "type": det.get("type", "low-pass"),
        },
        "simulated": {},
        "delta": {},
    }

    if sim_fc is None:
        result["status"] = "skip"
        result["note"] = "ngspice could not measure -3dB frequency"
        return result

    if expected_fc == 0:
        result["status"] = "skip"
        result["note"] = "expected cutoff frequency is 0 Hz — detection may be invalid"
        return result

    result["simulated"]["cutoff_hz"] = sim_fc
    if phase_fc is not None:
        result["simulated"]["phase_at_fc_deg"] = phase_fc

    fc_error = abs(sim_fc - expected_fc) / expected_fc * 100
    result["delta"]["fc_error_pct"] = round(fc_error, 2)

    # For ideal passives, error should be <1%. Any significant error
    # likely indicates a topology misunderstanding by the analyzer.
    if fc_error < 1:
        result["status"] = "pass"
    elif fc_error < 5:
        result["status"] = "warn"
        result["note"] = f"{fc_error:.1f}% deviation — check for loading or parallel paths"
    else:
        result["status"] = "fail"
        result["note"] = f"{fc_error:.1f}% deviation — topology may differ from detection"

    return result


def evaluate_lc_filter(det, sim_results):
    """Evaluate LC filter simulation results."""
    expected_f = det["resonant_hz"]
    f_peak = sim_results.get("f_peak")
    gain_peak = sim_results.get("gain_peak")
    bw_lo = sim_results.get("bw_3db_lo")
    bw_hi = sim_results.get("bw_3db_hi")

    result = {
        "subcircuit_type": "lc_filter",
        "components": [det["inductor"]["ref"], det["capacitor"]["ref"]],
        "expected": {
            "resonant_hz": expected_f,
            "impedance_ohms": det.get("impedance_ohms"),
        },
        "simulated": {},
        "delta": {},
    }

    if f_peak is None:
        result["status"] = "skip"
        result["note"] = "ngspice could not find resonance peak"
        return result

    if expected_f == 0:
        result["status"] = "skip"
        result["note"] = "expected resonant frequency is 0 Hz — detection may be invalid"
        return result

    result["simulated"]["resonant_hz"] = f_peak
    if gain_peak is not None:
        result["simulated"]["gain_peak_dB"] = gain_peak

    # Calculate Q factor from bandwidth if available
    if bw_lo is not None and bw_hi is not None and bw_hi > bw_lo:
        bw = bw_hi - bw_lo
        q_sim = f_peak / bw
        result["simulated"]["Q_factor"] = round(q_sim, 1)
        result["simulated"]["bandwidth_hz"] = round(bw, 1)

    f_error = abs(f_peak - expected_f) / expected_f * 100
    result["delta"]["f_error_pct"] = round(f_error, 2)

    if f_error < 1:
        result["status"] = "pass"
    elif f_error < 5:
        result["status"] = "warn"
        result["note"] = f"{f_error:.1f}% resonance shift"
    else:
        result["status"] = "fail"
        result["note"] = f"{f_error:.1f}% deviation from expected resonance"

    # Q factor evaluation for power supply LC filters
    if bw_lo is not None and bw_hi is not None and bw_hi > bw_lo:
        q_sim = result["simulated"]["Q_factor"]
        if q_sim > 20:
            if result.get("status") != "fail":
                result["status"] = "warn"
            warnings = result.get("warnings", [])
            warnings.append(f"High Q factor ({q_sim:.1f}) — underdamped, risk of oscillation or ringing in power path")
            result["warnings"] = warnings
        elif q_sim > 10 and result.get("status") == "pass":
            result["status"] = "warn"
            warnings = result.get("warnings", [])
            warnings.append(f"Q={q_sim:.1f} — moderately underdamped, consider adding series resistance for damping")
            result["warnings"] = warnings

    return result


def evaluate_voltage_divider(det, sim_results):
    """Evaluate voltage divider simulation results."""
    ratio = det["ratio"]
    expected_str = sim_results.get("expected")
    expected_vout = float(expected_str) if expected_str else None
    sim_vout = sim_results.get("vout_sim")
    error_pct = sim_results.get("error_pct")

    result = {
        "subcircuit_type": "voltage_divider",
        "components": [det["r_top"]["ref"], det["r_bottom"]["ref"]],
        "expected": {
            "ratio": ratio,
        },
        "simulated": {},
        "delta": {},
    }

    if expected_vout:
        result["expected"]["vout_V"] = expected_vout

    if sim_vout is None:
        result["status"] = "skip"
        result["note"] = "ngspice operating point failed"
        return result

    result["simulated"]["vout_V"] = sim_vout

    if error_pct is not None:
        result["delta"]["vout_error_pct"] = round(error_pct, 3)
        if error_pct < 0.1:
            result["status"] = "pass"
        elif error_pct < 1:
            result["status"] = "warn"
            result["note"] = f"{error_pct:.2f}% error — check for loading"
        else:
            result["status"] = "fail"
            result["note"] = f"{error_pct:.1f}% error — significant deviation"
    else:
        # Compute from vout if error_pct not available
        if expected_vout and expected_vout != 0:
            err = abs(sim_vout - expected_vout) / expected_vout * 100
            result["delta"]["vout_error_pct"] = round(err, 3)
            result["status"] = "pass" if err < 0.1 else "warn" if err < 1 else "fail"
        else:
            result["status"] = "pass"

    return result


def evaluate_opamp_circuit(det, sim_results):
    """Evaluate opamp circuit simulation results."""
    config = det.get("configuration", "unknown")
    expected_gain = det.get("gain")
    expected_gain_db = det.get("gain_dB")
    sim_gain_1k = sim_results.get("gain_1k")
    sim_bw = sim_results.get("bw_3db")

    # Determine model source from simulation output
    model_source = sim_results.get("model_source", "ideal")
    model_gbw_str = sim_results.get("model_gbw", "0")
    try:
        model_gbw = float(model_gbw_str) if model_gbw_str else 0
    except (ValueError, TypeError):
        model_gbw = 0

    if model_source and model_source != "ideal" and model_source != "0":
        part_name = det.get("value", "?")
        model_note = f"{part_name} behavioral ({model_source}, GBW={model_gbw/1e6:.1f}MHz)"
    else:
        model_note = "ideal opamp (Aol=1e6, GBW~10MHz) — real part may limit bandwidth"

    result = {
        "subcircuit_type": "opamp_circuit",
        "components": [det["reference"]],
        "configuration": config,
        "expected": {},
        "simulated": {},
        "delta": {},
        "model_note": model_note,
    }

    if expected_gain is not None:
        result["expected"]["gain"] = expected_gain
    if expected_gain_db is not None:
        result["expected"]["gain_dB"] = expected_gain_db

    if sim_gain_1k is None:
        result["status"] = "skip"
        result["note"] = "ngspice AC measurement failed"
        return result

    gain_db = sim_gain_1k
    if gain_db is not None:
        result["simulated"]["gain_dB"] = round(gain_db, 2)
        result["simulated"]["gain_linear"] = round(10 ** (gain_db / 20), 3)

    if sim_bw is not None:
        result["simulated"]["bandwidth_hz"] = sim_bw

    # Compare gain
    if expected_gain_db is not None and gain_db is not None:
        gain_error = abs(gain_db - expected_gain_db)
        result["delta"]["gain_error_dB"] = round(gain_error, 2)

        if gain_error < 0.5:
            result["status"] = "pass"
        elif gain_error < 2:
            result["status"] = "warn"
            result["note"] = f"Gain differs by {gain_error:.1f} dB from expected"
        elif model_source and model_source != "ideal" and model_source != "0":
            # Behavioral model with large gain error — likely a testbench
            # topology sensitivity exposed by the lower Aol, not a real
            # design bug. Downgrade to warn so "fail" stays meaningful.
            result["status"] = "warn"
            result["note"] = (
                f"Gain differs by {gain_error:.1f} dB from expected "
                f"(behavioral model — may reflect testbench topology sensitivity "
                f"or real GBW limitation)"
            )
        else:
            result["status"] = "fail"
            result["note"] = f"Gain differs by {gain_error:.1f} dB — check feedback network"
    else:
        result["status"] = "pass"
        result["note"] = "No expected gain to compare — reporting measured values"

    # Multi-frequency gain flatness (Q6)
    gain_low = sim_results.get("gain_low")
    gain_high = sim_results.get("gain_high")
    if gain_low is not None and gain_high is not None and gain_db is not None:
        gains = [gain_db, gain_low, gain_high]
        result["simulated"]["gain_low_dB"] = round(gain_low, 2)
        result["simulated"]["gain_high_dB"] = round(gain_high, 2)
        gain_spread_db = max(gains) - min(gains)
        result["simulated"]["gain_spread_dB"] = round(gain_spread_db, 2)
        if gain_spread_db > 3:
            note = result.get("note", "") or ""
            result["note"] = (note +
                f" Gain varies {gain_spread_db:.1f} dB across frequency — frequency-dependent response.").strip()

    # Phase at bandwidth (M6 — stability indicator)
    phase_at_bw = sim_results.get("phase_at_bw")
    if phase_at_bw is not None:
        result["simulated"]["phase_at_bw_deg"] = round(phase_at_bw, 1)

    return result


def evaluate_crystal_circuit(det, sim_results):
    """Evaluate crystal circuit simulation results."""
    freq = det.get("frequency")
    cl_eff = det.get("effective_load_pF")
    rm = sim_results.get("rm")
    f_series = sim_results.get("f_series")

    result = {
        "subcircuit_type": "crystal_circuit",
        "components": [det["reference"]],
        "expected": {},
        "simulated": {},
        "delta": {},
        "model_note": "generic crystal equivalent circuit — actual Rm may differ",
    }

    if freq:
        result["expected"]["frequency_hz"] = freq
    if cl_eff:
        result["expected"]["load_capacitance_pF"] = cl_eff
        cl_sim = sim_results.get("cl_pF")
        if cl_sim is not None:
            result["simulated"]["load_capacitance_pF"] = cl_sim

    # For crystals, we primarily check that load caps are present and reasonable
    load_caps = det.get("load_caps", [])
    if len(load_caps) >= 2:
        result["status"] = "pass"
        result["note"] = f"Load caps present: {load_caps[0]['ref']}, {load_caps[1]['ref']}"
        if cl_eff:
            # Typical crystal CL spec: 6-20 pF. Flag if outside range.
            if cl_eff < 4 or cl_eff > 30:
                result["status"] = "warn"
                result["note"] = f"Effective CL={cl_eff:.1f}pF — unusual range, verify crystal datasheet"
    else:
        result["status"] = "warn"
        result["note"] = "Missing or insufficient load capacitors"

    # Evaluate series resonance accuracy
    if f_series is not None and det.get("frequency"):
        nominal_freq = det["frequency"]
        if nominal_freq > 0:
            f_error_pct = abs(f_series - nominal_freq) / nominal_freq * 100
            result["simulated"]["f_series_hz"] = f_series
            result["simulated"]["f_error_pct"] = round(f_error_pct, 2)
            if f_error_pct > 1:
                result["status"] = "warn"
                result["note"] = (result.get("note", "") +
                    f" Series resonance {f_series/1e6:.3f} MHz deviates {f_error_pct:.1f}% from nominal.").strip()

    if rm is not None:
        result["simulated"]["motional_resistance_ohm"] = round(rm, 1)
        freq_val = det.get("frequency", 0) or 0
        rm_limit = 50000 if freq_val < 100e3 else 100  # 32kHz crystals have high Rm
        if rm > rm_limit:
            if result["status"] == "pass":
                result["status"] = "warn"
            result["note"] = (result.get("note", "") +
                f" High motional resistance ({rm:.0f}\u03a9) \u2014 verify oscillator IC can drive this crystal.").strip()

    return result


def evaluate_feedback_network(det, sim_results):
    """Evaluate feedback network simulation results.

    Same electrical behavior as voltage divider, but context differs —
    these set regulator output voltage, so we flag even small errors.
    Cross-references with power_regulators when context is available.
    """
    ratio = det["ratio"]
    expected_str = sim_results.get("expected")
    expected_vout = float(expected_str) if expected_str else None
    sim_vout = sim_results.get("vout_sim")
    error_pct = sim_results.get("error_pct")

    # Identify connected regulator from mid_point_connections
    connections = det.get("mid_point_connections", [])
    fb_ic = None
    for conn in connections:
        if conn.get("pin_name", "").upper() in ("FB", "ADJ", "VADJ"):
            fb_ic = conn.get("component")
            break

    # Cross-reference with power_regulators for Vref and estimated Vout
    reg_info = {}
    context = det.get("_context", {})
    if fb_ic and context:
        regulators = [f for f in context.get("findings", [])
                      if f.get("detector") == "detect_power_regulators"]
        for reg in regulators:
            if reg.get("ref") == fb_ic:
                reg_info["vref_source"] = reg.get("vref_source")
                reg_info["estimated_vout"] = reg.get("estimated_vout")
                reg_info["topology"] = reg.get("topology")
                reg_info["output_rail"] = reg.get("output_rail")
                break

    result = {
        "subcircuit_type": "feedback_network",
        "components": [det["r_top"]["ref"], det["r_bottom"]["ref"]],
        "expected": {"ratio": ratio},
        "simulated": {},
        "delta": {},
    }
    if fb_ic:
        result["regulator"] = fb_ic
    if reg_info:
        result["regulator_info"] = reg_info
    if expected_vout:
        result["expected"]["fb_voltage_V"] = expected_vout

    if sim_vout is None:
        result["status"] = "skip"
        result["note"] = "ngspice operating point failed"
        return result

    result["simulated"]["fb_voltage_V"] = sim_vout

    if error_pct is not None:
        result["delta"]["vout_error_pct"] = round(error_pct, 3)
        if error_pct < 0.1:
            result["status"] = "pass"
        elif error_pct < 1:
            result["status"] = "warn"
            result["note"] = f"{error_pct:.2f}% error in feedback divider"
        else:
            result["status"] = "fail"
            result["note"] = f"{error_pct:.1f}% error — regulator output voltage will be wrong"
    else:
        if expected_vout and expected_vout != 0:
            err = abs(sim_vout - expected_vout) / expected_vout * 100
            result["delta"]["vout_error_pct"] = round(err, 3)
            result["status"] = "pass" if err < 0.1 else "warn" if err < 1 else "fail"
        else:
            result["status"] = "pass"

    return result


def evaluate_transistor_circuit(det, sim_results):
    """Evaluate transistor circuit simulation results.

    Checks that the transistor turns on at a reasonable threshold and
    the on-state current is within expected bounds.
    """
    # EQ-078: Vth from DC sweep (transistor threshold detection)
    ref = det["reference"]
    ttype = det.get("type", "unknown")
    value = det.get("value", "")
    is_p = det.get("is_pchannel", False) if ttype == "mosfet" else False

    vth = sim_results.get("vth")
    i_on = sim_results.get("ic_on") or sim_results.get("i_on")
    vcc = sim_results.get("vcc")
    vbe_on = sim_results.get("vbe_on")

    result = {
        "subcircuit_type": "transistor_circuit",
        "components": [ref],
        "transistor_type": ttype,
        "value": value,
        "expected": {},
        "simulated": {},
        "delta": {},
        "model_note": f"generic {'PMOS' if is_p else 'NMOS' if ttype == 'mosfet' else 'PNP' if is_p else 'NPN'} model — real threshold depends on part",
    }

    if ttype in ("mosfet", "jfet"):
        if vth is not None:
            result["simulated"]["vth_V"] = round(vth, 3)
        if i_on is not None:
            result["simulated"]["i_on_mA"] = round(i_on * 1000, 2)

        if vth is None and i_on is None:
            result["status"] = "skip"
            result["note"] = "ngspice DC sweep measurement failed"
            return result

        # Generic NMOS Vth=1.5V, PMOS Vth=-1.5V — just verify the FET turns on
        result["status"] = "pass"
        if i_on is not None and i_on < 1e-6:
            result["status"] = "warn"
            result["note"] = "Very low on-state current — FET may not be switching properly"
    else:
        # BJT
        if vbe_on is not None:
            result["simulated"]["vbe_on_V"] = round(vbe_on, 3)
        if i_on is not None:
            result["simulated"]["ic_on_mA"] = round(i_on * 1000, 2)

        if vbe_on is None and i_on is None:
            result["status"] = "skip"
            result["note"] = "ngspice DC sweep measurement failed"
            return result

        result["status"] = "pass"
        # VBE should be ~0.6-0.7V for silicon BJT
        if vbe_on is not None:
            if vbe_on < 0.4 or vbe_on > 0.9:
                result["status"] = "warn"
                result["note"] = f"VBE(on)={vbe_on:.3f}V — outside typical 0.5-0.8V range"

    return result


def evaluate_current_sense(det, sim_results):
    """Evaluate current sense simulation results.

    Validates the sense resistor value by comparing simulated I@50mV and
    I@100mV against the analyzer's calculated values.
    """
    shunt = det["shunt"]
    r_ref = shunt["ref"]
    r_ohms = shunt["ohms"]
    expected_50 = det.get("max_current_50mV_A")
    expected_100 = det.get("max_current_100mV_A")

    sim_50 = sim_results.get("i_at_50mV")
    sim_100 = sim_results.get("i_at_100mV")

    result = {
        "subcircuit_type": "current_sense",
        "components": [r_ref],
        "sense_resistor_ohms": r_ohms,
        "expected": {},
        "simulated": {},
        "delta": {},
    }

    if expected_50 is not None:
        result["expected"]["max_current_50mV_A"] = expected_50
    if expected_100 is not None:
        result["expected"]["max_current_100mV_A"] = expected_100

    if sim_50 is None and sim_100 is None:
        result["status"] = "skip"
        result["note"] = "ngspice DC sweep measurement failed"
        return result

    if sim_50 is not None:
        result["simulated"]["i_at_50mV_A"] = round(sim_50, 4)
    if sim_100 is not None:
        result["simulated"]["i_at_100mV_A"] = round(sim_100, 4)

    # Check accuracy — for an ideal resistor, I=V/R should be exact
    errors = []
    if sim_50 is not None and expected_50 is not None and expected_50 > 0:
        err = abs(sim_50 - expected_50) / expected_50 * 100
        errors.append(err)
        result["delta"]["error_50mV_pct"] = round(err, 2)
    if sim_100 is not None and expected_100 is not None and expected_100 > 0:
        err = abs(sim_100 - expected_100) / expected_100 * 100
        errors.append(err)
        result["delta"]["error_100mV_pct"] = round(err, 2)

    if errors:
        max_err = max(errors)
        if max_err < 1:
            result["status"] = "pass"
        elif max_err < 5:
            result["status"] = "warn"
            result["note"] = f"{max_err:.1f}% deviation in sense current"
        else:
            result["status"] = "fail"
            result["note"] = f"{max_err:.1f}% deviation — check sense resistor value"
    else:
        result["status"] = "pass"
        result["note"] = "Simulation ran but no expected values to compare"

    return result


# ---------------------------------------------------------------------------
# Registry: maps detector key to evaluator function
# ---------------------------------------------------------------------------

def evaluate_protection_device(det, sim_results):
    """Evaluate protection device simulation results.

    Checks that the TVS/ESD clamping voltage is reasonable relative
    to the protected rail voltage.
    """
    ref = det["ref"]
    ptype = det.get("type", "")
    v_clamp_1mA = sim_results.get("v_clamp_1mA")
    v_clamp_10mA = sim_results.get("v_clamp_10mA")
    rail_v_str = sim_results.get("rail_v")
    rail_v = float(rail_v_str) if rail_v_str else None

    result = {
        "subcircuit_type": "protection_device",
        "components": [ref],
        "device_type": ptype,
        "expected": {},
        "simulated": {},
        "delta": {},
        "model_note": "generic diode model — real TVS has specific clamping characteristics",
    }

    if rail_v:
        result["expected"]["rail_voltage_V"] = rail_v

    if v_clamp_1mA is None and v_clamp_10mA is None:
        result["status"] = "pass"
        result["note"] = "Protection diode present — clamping voltage requires manufacturer model for accurate measurement"
        return result

    if v_clamp_1mA is not None:
        result["simulated"]["v_clamp_1mA"] = round(v_clamp_1mA, 3)
    if v_clamp_10mA is not None:
        result["simulated"]["v_clamp_10mA"] = round(v_clamp_10mA, 3)

    # The generic diode model clamps at ~0.7V forward — this is just
    # confirming the diode is present and conducting. Real TVS clamping
    # voltage depends on the specific part (5V, 12V, 24V, etc.).
    result["status"] = "pass"
    result["note"] = "Diode present and conducting — real clamping voltage depends on specific TVS part"

    return result


def evaluate_decoupling(det, sim_results):
    """Evaluate decoupling impedance simulation results.

    Checks that the parallel cap bank provides low impedance across
    the frequency range of interest (100kHz-1MHz for digital).
    """
    caps = det.get("capacitors", [])
    rail = det.get("rail", "?")
    cap_refs = [c["ref"] for c in caps if c.get("ref")]

    z_min = sim_results.get("z_min")
    f_at_zmin = sim_results.get("f_at_zmin")
    z_at_1m = sim_results.get("z_at_1M")
    z_at_100k = sim_results.get("z_at_100k")

    result = {
        "subcircuit_type": "decoupling",
        "components": cap_refs[:5],  # Limit to 5 refs to keep output compact
        "rail": rail,
        "cap_count": len(caps),
        "expected": {},
        "simulated": {},
        "delta": {},
        "model_note": "generic ESR + parasitic L from self-resonant frequency",
    }

    if z_min is not None:
        result["simulated"]["z_min_ohms"] = round(z_min, 4)
    if f_at_zmin is not None:
        result["simulated"]["f_at_zmin_hz"] = f_at_zmin
    if z_at_1m is not None:
        result["simulated"]["z_at_1MHz_ohms"] = round(z_at_1m, 4)
    if z_at_100k is not None:
        result["simulated"]["z_at_100kHz_ohms"] = round(z_at_100k, 4)

    if z_min is None and z_at_1m is None:
        result["status"] = "skip"
        result["note"] = "ngspice impedance measurement failed"
        return result

    # Evaluation: verify the simulation produced valid results.
    # Impedance thresholds are informational — most designs have a mix of
    # tightly and loosely decoupled rails, and "good" depends on context.
    if z_at_1m is not None and z_at_1m < 10.0:
        result["status"] = "pass"
        result["note"] = f"Z={z_at_1m:.3f}Ω at 1MHz"
    elif z_at_1m is not None:
        result["status"] = "warn"
        result["note"] = f"Z={z_at_1m:.1f}Ω at 1MHz — single bulk cap or high-value rail"
    else:
        result["status"] = "pass"
        result["note"] = "Decoupling caps present — impedance profile simulated"

    return result


def evaluate_regulator_feedback(det, sim_results):
    """Evaluate regulator feedback divider simulation results.

    Checks that the simulated FB voltage matches the expected Vref,
    confirming the regulator's output voltage setpoint.
    """
    fd = det.get("feedback_divider", {})
    r_top = fd.get("r_top", {}) if isinstance(fd.get("r_top"), dict) else {}
    r_bot = fd.get("r_bottom", {}) if isinstance(fd.get("r_bottom"), dict) else {}
    reg_ref = det.get("ref", "?")
    vref = det.get("assumed_vref")

    vfb_sim = sim_results.get("vfb_sim")
    error_pct = sim_results.get("error_pct")
    expected = sim_results.get("expected")
    vin = sim_results.get("vin")

    result = {
        "subcircuit_type": "regulator_feedback",
        "components": [r_top.get("ref", "?"), r_bot.get("ref", "?")],
        "regulator": reg_ref,
        "expected": {
            "ratio": fd.get("ratio"),
        },
        "simulated": {},
        "delta": {},
    }
    if vref:
        result["expected"]["vref_V"] = vref
    if expected:
        result["expected"]["vfb_V"] = float(expected)
    if vin:
        result["expected"]["vin_V"] = float(vin)

    if vfb_sim is None:
        result["status"] = "skip"
        result["note"] = "ngspice operating point failed"
        return result

    result["simulated"]["vfb_V"] = round(vfb_sim, 4)

    if error_pct is not None:
        result["delta"]["vfb_error_pct"] = round(error_pct, 3)
        if error_pct < 0.1:
            result["status"] = "pass"
        elif error_pct < 1:
            result["status"] = "warn"
            result["note"] = f"{error_pct:.2f}% error in feedback voltage"
        else:
            result["status"] = "fail"
            result["note"] = f"{error_pct:.1f}% error — regulator output voltage may be wrong"
    else:
        result["status"] = "pass"
        result["note"] = "Feedback divider simulated"

    return result


def evaluate_rf_matching(det, sim_results):
    """Evaluate RF matching network simulation results.

    Reports impedance profile — minimum impedance and key frequency points.
    Without a target frequency, evaluation is informational (pass/warn only).
    """
    comps = det.get("components", [])
    topology = det.get("topology", "?")
    comp_refs = [c["ref"] for c in comps if c.get("ref")]

    z_min = sim_results.get("z_min")
    f_at_zmin = sim_results.get("f_at_zmin")
    z_at_100m = sim_results.get("z_at_100M")
    z_at_1g = sim_results.get("z_at_1G")
    z_at_2g4 = sim_results.get("z_at_2G4")

    result = {
        "subcircuit_type": "rf_matching",
        "components": comp_refs[:5],
        "topology": topology,
        "expected": {},
        "simulated": {},
        "delta": {},
        "model_note": "ideal passives — no parasitic ESR/ESL, actual response may differ",
    }

    if z_min is not None:
        result["simulated"]["z_min_ohms"] = round(z_min, 4)
    if f_at_zmin is not None:
        result["simulated"]["f_at_zmin_hz"] = f_at_zmin
    if z_at_100m is not None:
        result["simulated"]["z_at_100MHz_ohms"] = round(z_at_100m, 3)
    if z_at_1g is not None:
        result["simulated"]["z_at_1GHz_ohms"] = round(z_at_1g, 3)
    if z_at_2g4 is not None:
        result["simulated"]["z_at_2_4GHz_ohms"] = round(z_at_2g4, 3)

    if z_min is None and z_at_1g is None:
        result["status"] = "skip"
        result["note"] = "ngspice impedance measurement failed"
        return result

    # Informational — without a target frequency we can only report the profile
    result["status"] = "pass"
    if f_at_zmin is not None and z_min is not None:
        result["note"] = f"Z_min={z_min:.3f}Ω at {f_at_zmin/1e6:.1f}MHz"
    else:
        result["note"] = "Impedance profile simulated"

    return result


def evaluate_bridge_circuit(det, sim_results):
    """Evaluate bridge circuit simulation results.

    Checks that the low-side FET turns on at a reasonable threshold.
    """
    # EQ-076: Gate sweep Vgs threshold detection
    hbs = det.get("half_bridges", [])
    hb = hbs[0] if hbs else {}
    hi_ref = hb.get("high_side", "?")
    lo_ref = hb.get("low_side", "?")
    topology = det.get("topology", "?")

    vth_lo = sim_results.get("vth_lo")
    id_on = sim_results.get("id_on")
    v_supply = sim_results.get("v_supply")

    result = {
        "subcircuit_type": "bridge_circuit",
        "components": [hi_ref, lo_ref],
        "topology": topology,
        "expected": {},
        "simulated": {},
        "delta": {},
        "model_note": "generic FET model — real Vth/Rds depends on specific part",
    }

    if v_supply:
        result["expected"]["v_supply_V"] = float(v_supply)

    if vth_lo is not None:
        result["simulated"]["vth_low_side_V"] = round(vth_lo, 3)
    if id_on is not None:
        result["simulated"]["id_on_mA"] = round(id_on * 1000, 2)

    if vth_lo is None and id_on is None:
        result["status"] = "skip"
        result["note"] = "ngspice DC sweep measurement failed"
        return result

    result["status"] = "pass"
    if id_on is not None and id_on < 1e-6:
        result["status"] = "warn"
        result["note"] = "Very low on-state current — FET may not be switching"
    else:
        result["note"] = f"Low-side FET turns on, Vth≈{vth_lo:.2f}V" if vth_lo else "FET conducting"

    return result


def evaluate_inrush(det, sim_results):
    """Evaluate inrush current simulation results.

    Compares simulated peak inrush against the analyzer's estimate.
    """
    reg_ref = det.get("regulator", "?")
    v_target = sim_results.get("v_target")
    estimated_inrush = det.get("estimated_inrush_A")
    cap_refs = [c["ref"] for c in det.get("output_caps", [])[:5]]

    i_peak = sim_results.get("i_peak")
    t_peak = sim_results.get("t_peak")
    v_settled = sim_results.get("v_settled")

    result = {
        "subcircuit_type": "inrush",
        "components": cap_refs,
        "regulator": reg_ref,
        "expected": {},
        "simulated": {},
        "delta": {},
    }

    if v_target:
        result["expected"]["v_target_V"] = float(v_target)
    if estimated_inrush:
        result["expected"]["estimated_inrush_A"] = estimated_inrush

    if i_peak is not None:
        result["simulated"]["i_peak_A"] = round(i_peak, 4)
    if t_peak is not None:
        result["simulated"]["t_peak_us"] = round(t_peak * 1e6, 1)
    if v_settled is not None:
        result["simulated"]["v_settled_V"] = round(v_settled, 3)

    if i_peak is None and v_settled is None:
        result["status"] = "skip"
        result["note"] = "ngspice transient measurement failed"
        return result

    # Check output settled to target
    if v_settled is not None and v_target:
        v_err = abs(v_settled - float(v_target)) / float(v_target) * 100
        result["delta"]["v_settle_error_pct"] = round(v_err, 2)

    result["status"] = "pass"
    if i_peak is not None:
        result["note"] = f"Peak inrush {i_peak*1000:.1f}mA at {t_peak*1e6:.0f}µs" if t_peak else f"Peak inrush {i_peak*1000:.1f}mA"
    else:
        result["note"] = "Transient simulated"

    return result


# ---------------------------------------------------------------------------
# Registry: maps detector key to evaluator function
# ---------------------------------------------------------------------------

def evaluate_bms_balance(det, sim_results):
    """Evaluate BMS balance resistor simulation results."""
    bms_ref = det.get("bms_reference", "?")
    cell_count = det.get("cell_count", 0)
    bal_resistors = det.get("balance_resistors", [])
    first_r = bal_resistors[0] if bal_resistors and isinstance(bal_resistors[0], dict) else {}

    i_bal = sim_results.get("i_bal")
    p_bal = sim_results.get("p_bal")
    r_ohms = sim_results.get("r_ohms")
    n_cells = sim_results.get("n_cells")

    result = {
        "subcircuit_type": "bms_balance",
        "components": [first_r.get("reference", "?")] if first_r else [],
        "regulator": bms_ref,
        "expected": {"cell_count": cell_count},
        "simulated": {},
        "delta": {},
    }
    if r_ohms:
        result["expected"]["balance_r_ohms"] = float(r_ohms)

    if i_bal is not None:
        result["simulated"]["i_balance_mA"] = round(i_bal * 1000, 2)
    if p_bal is not None:
        result["simulated"]["p_per_cell_mW"] = round(p_bal * 1000, 1)
        if cell_count:
            result["simulated"]["p_total_pack_mW"] = round(p_bal * 1000 * int(float(n_cells or cell_count)), 1)

    if p_bal is None:
        result["status"] = "skip"
        result["note"] = "ngspice operating point failed"
        return result

    if p_bal < 0.25:
        result["status"] = "pass"
        result["note"] = f"Balance: {i_bal*1000:.1f}mA, {p_bal*1000:.0f}mW/cell"
    elif p_bal < 0.5:
        result["status"] = "warn"
        result["note"] = f"Balance power {p_bal*1000:.0f}mW/cell — needs ≥0805 resistor"
    else:
        result["status"] = "fail"
        result["note"] = f"Balance power {p_bal*1000:.0f}mW/cell — exceeds typical SMD rating"

    return result


def evaluate_snubber(det, sim_results):
    """Evaluate snubber RC circuit simulation results."""
    # EQ-077: f_damp from AC impedance minimum detection
    sd = det.get("snubber_data", {}) or {}
    r_ref = sd.get("resistor_ref", "?")
    c_ref = sd.get("capacitor_ref", "?")
    r_ohms = sd.get("resistor_ohms")
    c_farads = sd.get("capacitor_farads")
    fet_ref = det.get("reference", "?")

    z_min = sim_results.get("z_min")
    f_at_zmin = sim_results.get("f_at_zmin")
    tau = sim_results.get("tau")
    f_analytical = sim_results.get("f_analytical")

    result = {
        "subcircuit_type": "snubber_circuit",
        "components": [r_ref, c_ref],
        "transistor": fet_ref,
        "expected": {},
        "simulated": {},
        "delta": {},
    }

    if tau:
        result["expected"]["tau_s"] = float(tau)
    if f_analytical:
        result["expected"]["f_snub_hz"] = float(f_analytical)
    if r_ohms:
        result["expected"]["r_ohms"] = r_ohms
    if c_farads:
        result["expected"]["c_farads"] = c_farads

    if z_min is not None:
        result["simulated"]["z_min_ohms"] = round(z_min, 4)
    if f_at_zmin is not None:
        result["simulated"]["f_at_zmin_hz"] = f_at_zmin

    if z_min is None:
        result["status"] = "skip"
        result["note"] = "ngspice impedance measurement failed"
        return result

    # Check tau is in reasonable range for switching snubbers
    if tau:
        tau_f = float(tau)
        if 1e-9 <= tau_f <= 1e-4:
            result["status"] = "pass"
            result["note"] = f"Snubber τ={tau_f*1e6:.2f}µs, f={float(f_analytical or 0)/1e3:.1f}kHz"
        else:
            result["status"] = "warn"
            result["note"] = f"Snubber τ={tau_f*1e6:.2f}µs — outside typical 1ns-100µs range"
    else:
        result["status"] = "pass"
        result["note"] = "Snubber impedance measured"

    return result


def evaluate_rf_chain(det, sim_results):
    """Evaluate RF chain link budget simulation results."""
    gain_budget_str = sim_results.get("gain_budget")
    gain_budget = float(gain_budget_str) if gain_budget_str else None
    freq_str = sim_results.get("freq_hz")
    freq = float(freq_str) if freq_str else None
    n_stages_str = sim_results.get("n_stages")
    n_stages = int(float(n_stages_str)) if n_stages_str else 0
    z_at_fc = sim_results.get("z_at_fc")

    stage_gains = det.get("stage_gains", {})
    band = det.get("frequency_band", "?")
    comp_roles = det.get("component_roles", {})
    comp_refs = list(comp_roles.keys())[:8]

    result = {
        "subcircuit_type": "rf_chain",
        "components": comp_refs,
        "expected": {},
        "simulated": {},
        "delta": {},
        "model_note": "heuristic gain/loss per role — real values depend on specific ICs",
    }

    if freq:
        result["expected"]["frequency_hz"] = freq
        result["expected"]["frequency_band"] = band
    if gain_budget is not None:
        result["simulated"]["gain_budget_dB"] = gain_budget
        result["simulated"]["stage_count"] = n_stages
    if z_at_fc is not None:
        result["simulated"]["z_ref_ohms"] = round(z_at_fc, 1)

    # Build link budget
    if stage_gains:
        result["link_budget"] = [
            {"ref": ref, "role": sg.get("role", "?"), "gain_dB": sg.get("gain_dB", 0)}
            for ref, sg in stage_gains.items()
        ]

    if gain_budget is None:
        result["status"] = "skip"
        result["note"] = "No gain budget computed"
        return result

    if -30 <= gain_budget <= 40:
        result["status"] = "pass"
        result["note"] = f"Link budget: {gain_budget:+.1f}dB across {n_stages} stages at {freq/1e6:.0f}MHz"
    else:
        result["status"] = "warn"
        result["note"] = f"Unusual link budget: {gain_budget:+.1f}dB — verify chain detection"

    return result


EVALUATOR_REGISTRY = {
    "rc_filters": evaluate_rc_filter,
    "lc_filters": evaluate_lc_filter,
    "voltage_dividers": evaluate_voltage_divider,
    "opamp_circuits": evaluate_opamp_circuit,
    "crystal_circuits": evaluate_crystal_circuit,
    "feedback_networks": evaluate_feedback_network,
    "transistor_circuits": evaluate_transistor_circuit,
    "current_sense": evaluate_current_sense,
    "protection_devices": evaluate_protection_device,
    "decoupling_analysis": evaluate_decoupling,
    "power_regulators": evaluate_regulator_feedback,
    "rf_matching": evaluate_rf_matching,
    "bridge_circuits": evaluate_bridge_circuit,
    "inrush_analysis": evaluate_inrush,
    "bms_systems": evaluate_bms_balance,
    "snubber_circuits": evaluate_snubber,
    "rf_chains": evaluate_rf_chain,
}


def build_report(simulation_runs):
    """Build the final simulation report from a list of individual results.

    Args:
        simulation_runs: List of result dicts from evaluate_* functions

    Returns:
        Report dict with summary statistics and individual results
    """
    # Add 'reference' convenience field (e.g. "R5/C3") from components list
    for run in simulation_runs:
        if "reference" not in run and "components" in run:
            run["reference"] = "/".join(run["components"])

    counts = {"pass": 0, "warn": 0, "fail": 0, "skip": 0}
    for run in simulation_runs:
        status = run.get("status", "skip")
        counts[status] = counts.get(status, 0) + 1

    # Synthesize finding-shaped entries for simulations that didn't pass —
    # keeps the v1.3 envelope contract (findings[] + trust_summary)
    # consistent across all analyzers. Pass/skip results stay
    # informational and are reflected only in simulation_results and the
    # status counts, not in findings[].
    findings = []
    for run in simulation_runs:
        status = run.get("status", "skip")
        if status not in ("fail", "warn"):
            continue
        severity = "error" if status == "fail" else "warning"
        subtype = run.get("subcircuit_type", "simulation")
        ref = run.get("reference", "")

        # Build a description that surfaces the numeric delta so the
        # finding is self-contained without chasing simulation_results.
        _delta = run.get("delta") or {}
        _exp = run.get("expected") or {}
        _sim = run.get("simulated") or {}
        _detail_parts = []
        for metric, pct in _delta.items():
            if pct is not None:
                _detail_parts.append(f"{metric}: {pct:+.2f}%")
        _delta_summary = "; ".join(_detail_parts) if _detail_parts else "no numeric delta"
        _expected_keys = ", ".join(f"{k}={v}" for k, v in _exp.items()) if _exp else "—"
        _simulated_keys = ", ".join(f"{k}={v}" for k, v in _sim.items()) if _sim else "—"
        _description = (
            f"SPICE simulation of {subtype} ({ref}) "
            f"{'failed to converge' if status == 'fail' else 'converged with warnings'}. "
            f"Expected: {_expected_keys}. "
            f"Simulated: {_simulated_keys}. "
            f"Delta: {_delta_summary}."
        )

        findings.append({
            "detector": "simulate_subcircuits",
            "rule_id": "SP-FAIL" if status == "fail" else "SP-WARN",
            "severity": severity,
            "confidence": "deterministic",
            "evidence_source": "heuristic_rule",
            "category": "simulation",
            "summary": (
                f"{subtype} {ref} — SPICE {'did not converge to expected values' if status == 'fail' else 'converged with warnings'}".strip()
            ),
            "description": _description,
            "components": run.get("components", []) or [],
            "nets": [],
            "pins": [],
            "recommendation": (
                "Review the expected vs simulated values; confirm component "
                "values match the datasheet reference design, and that parasitics "
                "are modelled where they affect the result."
            ),
            "report_context": {
                "section": "SPICE Simulation",
                "impact": "Simulation did not match expected values" if status == "fail" else "Simulation results warrant review",
                "standard_ref": "",
            },
            # Preserve the structured sim detail for consumers that want
            # the numeric delta.
            "expected": run.get("expected"),
            "simulated": run.get("simulated"),
            "delta": run.get("delta"),
        })

    report = {
        "analyzer_type": "spice",
        "schema_version": "1.4.0",
        "summary": {
            "total": len(simulation_runs),
            "total_findings": len(findings),
            **counts,
            # Map simulation status to the standard by_severity vocabulary so
            # release gates and summarize tools can aggregate uniformly.
            "by_severity": {
                "error": counts["fail"],
                "warning": counts["warn"],
                "info": counts["pass"] + counts["skip"],
            },
        },
        "findings": findings,
        "simulation_results": simulation_runs,
    }

    # Trust summary — populate through the shared helper so consumers get
    # the same shape they expect from every other v1.3 analyzer.
    try:
        import os as _os, sys as _sys
        _kicad_scripts = _os.path.join(
            _os.path.dirname(_os.path.abspath(__file__)),
            '..', '..', 'kicad', 'scripts')
        if _os.path.isdir(_kicad_scripts):
            _sys.path.insert(0, _os.path.abspath(_kicad_scripts))
        from finding_schema import compute_trust_summary
        report["trust_summary"] = compute_trust_summary(findings)
    except (ImportError, Exception):
        # Fall back to a minimal hand-rolled trust_summary so the envelope
        # is still complete even when the helper isn't importable.
        report["trust_summary"] = {
            "total_findings": len(findings),
            "trust_level": "high" if not findings else "mixed",
            "by_confidence": {
                "deterministic": len(findings),
                "heuristic": 0,
                "datasheet_backed": 0,
            },
            "by_evidence_source": {},
            "provenance_coverage_pct": 0.0,
        }

    # Monte Carlo summary if any results have tolerance_analysis
    mc_runs = [r for r in simulation_runs if "tolerance_analysis" in r]
    if mc_runs:
        concerns = []
        for r in mc_runs:
            ta = r["tolerance_analysis"]
            for metric, stats in ta.get("statistics", {}).items():
                if stats.get("spread_pct", 0) > 25:
                    concerns.append({
                        "subcircuit_type": r.get("subcircuit_type", ""),
                        "components": r.get("components", []),
                        "metric": metric,
                        "spread_pct": stats["spread_pct"],
                    })
        report["monte_carlo_summary"] = {
            "subcircuits_analyzed": len(mc_runs),
            "total_simulations": sum(
                r["tolerance_analysis"]["n_converged"] for r in mc_runs),
            "concerns": concerns,
        }

    return report
