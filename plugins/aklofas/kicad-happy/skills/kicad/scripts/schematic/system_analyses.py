"""System-level analyses (PDN impedance, sleep current, voltage derating, protocol compliance, power budget and sequencing, BOM optimization, test coverage, assembly complexity, USB compliance, inrush): verbatim move from analyze_schematic.py; no behaviour change."""
from __future__ import annotations

import json
import math
import re
from kicad_types import (
    AnalysisContext,
)
from pathlib import (
    Path,
)
from kicad_core.netnames import (
    _clean_hierarchical_name,
)
from schematic.net_analysis import (
    _estimate_rail_voltage,
)
from kicad_core.values import (
    format_frequency as _format_frequency,
    parse_value,
)
from finding_schema import (
    make_finding,
)
from kicad_core.parts import (
    MLCC_ESL,
    MLCC_ESR,
)


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
    # Typical MLCC parasitics — the tables EMC uses (kicad_core.parts)
    esl_by_pkg = MLCC_ESL
    # ESR for X5R/X7R at 1 MHz
    esr_base_by_pkg = MLCC_ESR

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


# KH-374: below this, a resistor bridging a rail to ground/a signal net is a
# current-shunt/sense element, not a pull or bleeder -- a 5 mOhm shunt on
# VBAT computed a nonsensical 740 A "worst-case" pull-up current pre-floor.
SLEEP_PULL_MIN_OHM = 100.0


def analyze_sleep_current(ctx: AnalysisContext,
                          signal_analysis: dict | None = None,
                          power_sequencing: dict | None = None) -> dict:
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

    # KH-374: rail voltage resolution that also knows about battery rails
    # (VBAT/+BATT) and regulator estimated_vout, not just names
    # _estimate_rail_voltage() can parse a number out of.
    _battery_rail_re = re.compile(r'^\+?(BATT?|VBATT?|BATTERY|BAT\+)$', re.IGNORECASE)
    _reg_vout_by_rail: dict[str, float] = {}
    if signal_analysis:
        for _reg in signal_analysis.get("power_regulators", []):
            _out_rail = _reg.get("output_rail", "")
            _vout = _reg.get("estimated_vout")
            if _out_rail and _vout:
                _reg_vout_by_rail.setdefault(_out_rail, _vout)

    def _rail_voltage(name: str) -> float | None:
        v = _estimate_rail_voltage(name)
        if v is not None:
            return v
        if signal_analysis:
            v = signal_analysis.get("rail_voltages", {}).get(_clean_hierarchical_name(name))
            if v is not None:
                return v
        v = _reg_vout_by_rail.get(name)
        if v is not None:
            return v
        if name and _battery_rail_re.match(name):
            return 3.7
        return None

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
            if r_val < SLEEP_PULL_MIN_OHM:
                # KH-374: a sub-100 Ohm resistor bridging a rail straight
                # to ground is a shunt/sense element, not a bleeder --
                # don't guess a current for it.
                continue
            v_rail = _rail_voltage(pwr_net)
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
            pwr_net, sig_net = n1, n2
        elif is_power_net(n2) and not is_ground(n2) and not is_power_net(n1):
            pwr_net, sig_net = n2, n1
        else:
            continue

        v_rail = _rail_voltage(pwr_net)
        if not v_rail or v_rail <= 0:
            continue

        # KH-342: classify the signal side before assuming worst-case V/R.
        # A second resistor to ground makes this a divider (DC = V/(R1+R2));
        # a shunt cap with no other DC sink makes it an RC filter (DC ~ 0).
        divider_r2_ref = None
        divider_r2_ohm = None
        has_shunt_cap = False
        has_other_dc_sink = False
        if sig_net in nets:
            for p in nets[sig_net]["pins"]:
                if p["component"] == ref:
                    continue
                oc = comp_lookup.get(p["component"])
                if not oc:
                    continue
                o_type = oc.get("type")
                if o_type == "resistor":
                    o1, o2 = _get_two_pin_nets(oc["reference"])
                    o_other = o2 if o1 == sig_net else o1
                    o_val = parse_value(oc.get("value", ""))
                    if o_other and is_ground(o_other) and o_val and o_val > 0:
                        if divider_r2_ref is None:
                            divider_r2_ref = oc["reference"]
                            divider_r2_ohm = o_val
                    else:
                        has_other_dc_sink = True
                elif o_type == "capacitor":
                    o1, o2 = _get_two_pin_nets(oc["reference"])
                    o_other = o2 if o1 == sig_net else o1
                    if o_other and is_ground(o_other):
                        has_shunt_cap = True
                elif o_type in ("switch", "led", "diode", "transistor"):
                    has_other_dc_sink = True

        if divider_r2_ref:
            current_a = v_rail / (r_val + divider_r2_ohm)
            rail_currents.setdefault(pwr_net, []).append({
                "ref": ref,
                "value": comp["value"],
                "type": "divider",
                "resistance_ohm": r_val,
                "divider_partner": divider_r2_ref,
                "total_resistance_ohm": round(r_val + divider_r2_ohm, 1),
                "rail_voltage": v_rail,
                "current_uA": round(current_a * 1e6, 2),
                "note": f"divider with {divider_r2_ref}: I = V/(R1+R2)",
            })
        elif has_shunt_cap and not has_other_dc_sink:
            rail_currents.setdefault(pwr_net, []).append({
                "ref": ref,
                "value": comp["value"],
                "type": "rc_filter",
                "resistance_ohm": r_val,
                "rail_voltage": v_rail,
                "current_uA": 0.0,
                "note": "series-R + shunt-C, no DC load — steady-state ~ 0",
            })
        elif r_val < SLEEP_PULL_MIN_OHM:
            # KH-374: a sub-100 Ohm resistor here is a shunt/sense
            # element, not a pull -- don't guess a current for it.
            pass
        else:
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
                        v_rail = _rail_voltage(rn)
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

    # Build set of disableable rails. KH-374: when power_sequencing (real EN
    # connectivity from analyze_power_sequencing) is available, a rail is
    # only disableable if its regulator's EN pin is actually driven by
    # something (en_source == "controlled") — not merely because the part
    # happens to have an EN-named pin. Falls back to the old EN-pin-NAME
    # heuristic when power_sequencing wasn't supplied (back-compat).
    _controlled_rails: set[str] = set()
    _controlled_regs: set[str] = set()
    if power_sequencing:
        for d in power_sequencing.get("dependencies", []):
            if d.get("en_source") == "controlled":
                _controlled_rails.add(d.get("output_rail", ""))
                _controlled_regs.add(d.get("regulator", ""))

    if power_sequencing:
        _disableable_rails: set[str] = _controlled_rails
    else:
        _disableable_rails = set()
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
                # KH-374: with real EN connectivity available, only a
                # regulator whose EN is actually driven (en_source ==
                # "controlled") counts as disableable — having an
                # EN-named pin isn't enough on its own.
                if power_sequencing:
                    can_disable = e["ref"] in _controlled_regs
                else:
                    can_disable = bool(e.get("has_enable_pin"))
                if can_disable:
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
            elif etype == "divider":
                if rail in _disableable_rails:
                    e["likely_state"] = "rail disabled during sleep"
                    e["realistic_uA"] = 0.0
                else:
                    e["likely_state"] = "always conducting"
                    e["realistic_uA"] = e["current_uA"]
            elif etype == "rc_filter":
                e["likely_state"] = "no DC path (shunt cap only)"
                e["realistic_uA"] = 0.0

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
                             derating_profile: str = "commercial") -> list[dict]:
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
                    with open(idx_path, encoding="utf-8") as f:
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
            with open(extract_path, encoding="utf-8") as f:
                return json.load(f).get("absolute_maximum_ratings")
        except (json.JSONDecodeError, OSError):
            return None

    profile = _DERATING_PROFILES.get(derating_profile, _DERATING_PROFILES["commercial"])
    _CAP_DERATING = {"ceramic": profile["ceramic_cap"], "electrolytic": profile["electrolytic_cap"],
                     "tantalum": profile["tantalum_cap"], "unknown": profile["unknown_cap"]}
    _RESISTOR_POWER_RATING = {"0201": 0.05, "0402": 0.0625, "0603": 0.1, "0805": 0.125,
                              "1206": 0.25, "1210": 0.5, "2010": 0.75, "2512": 1.0}

    findings: list[dict] = []

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
        margin_pct = ((rated_v - v_rail) / rated_v) * 100 if rated_v > 0 else 0
        severity = derating_rule = None
        if v_rail > rated_v:
            severity, derating_rule = "critical", "exceeds_rated_voltage"
        elif v_rail > max_working_v:
            severity, derating_rule = "warning", f"{dielectric}_{int(derating_factor * 100)}pct"
        if severity:
            findings.append(make_finding(
                detector="analyze_voltage_derating", rule_id="VD-001",
                category="component_derating",
                summary=(f"{ref} ({comp['value']}) {'exceeds' if severity == 'critical' else 'has marginal'} "
                         f"voltage derating on {pwr_net} ({v_rail:.1f}V on {rated_v:.0f}V {dielectric} cap)"),
                description=(f"Applied {v_rail:.1f}V on {pwr_net}; {rated_v:.0f}V-rated {dielectric} capacitor. "
                             f"Derating rule: {derating_rule}. Margin {round(margin_pct, 1)}%."),
                severity="error" if severity == "critical" else "warning",
                confidence="heuristic", evidence_source="topology",
                components=[ref], nets=[pwr_net],
                recommendation=("Increase capacitor voltage rating." if severity == "critical"
                                else f"Consider a higher voltage rating — {dielectric} caps need derating margin."),
                impact="Capacitor may fail short under applied voltage." if severity == "critical" else "",
                derating_rule=derating_rule, rail=pwr_net, rail_voltage=v_rail,
                rated_voltage=rated_v, margin_pct=round(margin_pct, 1), dielectric=dielectric,
            schema_era="v3.0",
            ))
        elif margin_pct > profile["over_designed_cap_margin"] * 100:
            suggested_v = v_rail * 2.5
            suggested_ratings = [v for v in (6.3, 10, 16, 25, 50, 100) if v >= suggested_v]
            suggestion = ""
            if suggested_ratings and suggested_ratings[0] < rated_v:
                suggestion = (f"Consider {suggested_ratings[0]:.0f}V rating — "
                              f"{rated_v:.0f}V is significantly over-designed for a {v_rail:.1f}V rail")
            findings.append(make_finding(
                detector="analyze_voltage_derating", rule_id="VD-004",
                category="component_derating",
                summary=f"{ref} ({comp['value']}) is over-designed for {pwr_net} ({rated_v:.0f}V on {v_rail:.1f}V rail)",
                description=f"{rated_v:.0f}V-rated capacitor on a {v_rail:.1f}V rail — margin {round(margin_pct, 1)}%.",
                severity="info", confidence="heuristic", evidence_source="topology",
                components=[ref], nets=[pwr_net],
                recommendation=suggestion or "Consider a lower voltage rating to reduce cost/size.",
                derating_rule="over_designed", rail=pwr_net, rail_voltage=v_rail,
                rated_voltage=rated_v, margin_pct=round(margin_pct, 1),
            schema_era="v3.0",
            ))

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
        margin_pct = ((vin_max - max_rail_v) / vin_max) * 100 if vin_max > 0 else 0
        if max_rail_v > vin_max:
            findings.append(make_finding(
                detector="analyze_voltage_derating", rule_id="VD-002",
                category="component_derating",
                summary=f"{ref} exceeds datasheet absolute-max voltage on {max_rail_name} ({max_rail_v:.1f}V > {vin_max:.1f}V)",
                description=(f"{ref} ({comp['value']}) sees {max_rail_v:.1f}V on {max_rail_name}; datasheet "
                             f"absolute-max input is {vin_max:.1f}V. Margin {round(margin_pct, 1)}%."),
                severity="error", confidence="datasheet-backed", evidence_source="datasheet",
                components=[ref], nets=[max_rail_name],
                recommendation="Reduce the rail voltage or select a part rated for this rail.",
                impact="Operating beyond absolute maximum risks immediate device damage.",
                derating_rule="exceeds_abs_max", rail=max_rail_name, rail_voltage=max_rail_v,
                abs_max_vin=vin_max, margin_pct=round(margin_pct, 1),
            schema_era="v3.0",
            ))
        elif margin_pct < 10:
            findings.append(make_finding(
                detector="analyze_voltage_derating", rule_id="VD-002",
                category="component_derating",
                summary=f"{ref} operates near datasheet absolute-max voltage on {max_rail_name} ({round(margin_pct, 1)}% margin)",
                description=(f"{ref} ({comp['value']}) sees {max_rail_v:.1f}V on {max_rail_name}; datasheet "
                             f"absolute-max input is {vin_max:.1f}V. Only {round(margin_pct, 1)}% margin."),
                severity="warning", confidence="datasheet-backed", evidence_source="datasheet",
                components=[ref], nets=[max_rail_name],
                recommendation="Confirm worst-case rail tolerance leaves margin to absolute max.",
                derating_rule="ic_10pct_abs_max", rail=max_rail_name, rail_voltage=max_rail_v,
                abs_max_vin=vin_max, margin_pct=round(margin_pct, 1),
            schema_era="v3.0",
            ))

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
        max_working_power = rated_power * profile["resistor_power"]
        margin_pct = ((rated_power - power_w) / rated_power) * 100 if rated_power > 0 else 0
        severity = derating_rule = None
        if power_w > rated_power:
            severity, derating_rule = "critical", "exceeds_rated_power"
        elif power_w > max_working_power:
            severity, derating_rule = "warning", "resistor_50pct_power"
        if severity:
            findings.append(make_finding(
                detector="analyze_voltage_derating", rule_id="VD-003",
                category="component_derating",
                summary=(f"{ref} ({comp['value']}) {'exceeds' if severity == 'critical' else 'has marginal'} "
                         f"power derating ({power_w*1000:.0f}mW on {rated_power*1000:.0f}mW {pkg})"),
                description=(f"{ref} dissipates ~{power_w*1000:.0f}mW ({v_across:.1f}V across {pv:.0f}Ω); "
                             f"{pkg} package rated {rated_power*1000:.0f}mW. Derating rule: {derating_rule}. "
                             f"Margin {round(margin_pct, 1)}%."),
                severity="error" if severity == "critical" else "warning",
                confidence="heuristic", evidence_source="topology",
                components=[ref], nets=[pwr_net or n1] if (pwr_net or n1) else [],
                recommendation=("Use a larger package or higher power rating." if severity == "critical"
                                else "Consider a larger package for power derating margin."),
                impact="Resistor may overheat or fail open." if severity == "critical" else "",
                derating_rule=derating_rule, voltage_across=v_across, resistance_ohms=pv,
                estimated_power_w=round(power_w, 4), rated_power_w=rated_power, package=pkg,
                margin_pct=round(margin_pct, 1),
                schema_era="v3.0",
            ))
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
            findings.append(make_finding(
                detector="analyze_voltage_derating", rule_id="VD-004",
                category="component_derating",
                summary=f"{ref} ({comp['value']}) package is over-designed ({power_w*1000:.1f}mW in {pkg})",
                description=f"{ref} dissipates ~{power_w*1000:.1f}mW in a {pkg} ({rated_power*1000:.0f}mW rated) — margin {round(margin_pct, 1)}%.",
                severity="info", confidence="heuristic", evidence_source="topology",
                components=[ref], nets=[],
                recommendation=suggestion or "Consider a smaller package to reduce cost/size.",
                derating_rule="over_designed", estimated_power_w=round(power_w, 4),
                rated_power_w=rated_power, package=pkg, margin_pct=round(margin_pct, 1),
            schema_era="v3.0",
            ))

    # ---- Return findings ----
    return findings


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
    return {"protocols_checked": sorted({f["protocol"] for f in findings}), "findings": findings,
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

    # Map regulators to output rails (built first: candidate_rails below
    # needs it so a regulator's output rail counts even when its name
    # doesn't look power-y and carries no #PWR symbol -- KH-375).
    reg_by_rail: dict[str, dict] = {}
    for reg in signal_analysis.get("power_regulators", []):
        out_rail = reg.get("output_rail")
        if out_rail:
            reg_by_rail[out_rail] = reg

    # Rails of interest: power-named nets, plus regulator output rails.
    candidate_rails = {n for n in nets if is_power_net(n) and not is_ground(n)} | set(reg_by_rail)

    # Build power domain mapping: rail -> list of ICs
    rail_ics: dict[str, list[dict]] = {}
    for comp in components:
        if comp["type"] != "ic":
            continue
        ref = comp["reference"]
        for pnum, (net_name, _) in ref_pins.get(ref, {}).items():
            if net_name and net_name in candidate_rails:
                # Look up THE ITERATED PIN specifically -- KH-375: this used
                # to check the first pin `nets[net_name]["pins"]` listed for
                # this component and `break`, which could be a non-power pin
                # that happened to sort first (e.g. ~{SRCLR} before VCC).
                pin = next((p for p in nets[net_name]["pins"]
                           if p["component"] == ref
                           and str(p.get("pin_number")) == str(pnum)), None)
                if pin:
                    ptype = pin.get("pin_type", "")
                    pname = pin.get("pin_name", "").upper()
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

    # Deduplicate ICs per rail (an IC may have multiple power pins on same rail)
    for rail in rail_ics:
        seen_refs = set()
        deduped = []
        for ic in rail_ics[rail]:
            if ic["ref"] not in seen_refs:
                seen_refs.add(ic["ref"])
                deduped.append(ic)
        rail_ics[rail] = deduped

    # Resistor net index (built once): net -> [resistor refs with a pin
    # there]. Used below so an LED one hop behind a series resistor
    # (rail -> R -> LED -> GND, the common wiring on real boards) still
    # gets attributed to its rail.
    resistor_nets: dict[str, tuple[str | None, str | None]] = {}
    net_to_resistors: dict[str, list[str]] = {}
    for comp in components:
        if comp["type"] != "resistor":
            continue
        rref = comp["reference"]
        rn1, rn2 = ctx.get_two_pin_nets(rref)
        resistor_nets[rref] = (rn1, rn2)
        for n in (rn1, rn2):
            if n:
                net_to_resistors.setdefault(n, []).append(rref)

    # Non-IC loads (KH-375): LEDs draw real current; 5 mA nominal each.
    rail_other: dict[str, list[dict]] = {}
    for comp in components:
        if comp["type"] != "led":
            continue
        n1, n2 = ctx.get_two_pin_nets(comp["reference"])
        direct_rail = next((n for n in (n1, n2)
                            if n in candidate_rails and not is_ground(n)), None)
        if direct_rail:
            rail_other.setdefault(direct_rail, []).append(
                {"ref": comp["reference"], "type": "led", "estimated_mA": 5})
            continue
        # One resistor hop away: rail -> R -> LED (or LED -> R -> rail).
        # Neither LED pin sits on a candidate rail directly, so look past
        # the series resistor(s) tied to either LED pin for one that lands
        # on a candidate rail on its far end. The anchor net (the LED's own
        # pin) must NOT be ground or a candidate rail itself -- ground is a
        # shared bus, not a series element, so anchoring through it would
        # attribute the LED to any unrelated resistor that happens to sit
        # between GND and some rail (e.g. a bleeder resistor) even when the
        # LED has no series resistor of its own.
        reachable_via: dict[str, str] = {}
        for n in (n1, n2):
            if not n or is_ground(n) or n in candidate_rails:
                continue
            for rref in net_to_resistors.get(n, []):
                rn1, rn2 = resistor_nets[rref]
                other_net = rn2 if rn1 == n else rn1
                if other_net and other_net in candidate_rails and not is_ground(other_net):
                    reachable_via.setdefault(other_net, rref)
        if reachable_via:
            rail = sorted(reachable_via)[0]
            rail_other.setdefault(rail, []).append(
                {"ref": comp["reference"], "type": "led", "estimated_mA": 5,
                 "via": reachable_via[rail]})

    if not rail_ics and not reg_by_rail and not rail_other:
        return {}

    # All rails of interest
    all_rails = set(rail_ics.keys()) | set(reg_by_rail.keys()) | set(rail_other.keys())

    rails_result = {}
    observations = []

    for rail in sorted(all_rails):
        ics = rail_ics.get(rail, [])
        total_ic_mA = sum(ic["estimated_mA"] for ic in ics)
        other = rail_other.get(rail, [])

        rail_info: dict = {
            "ic_count": len(ics),
            "ics": ics,
            "estimated_load_mA": total_ic_mA + sum(o["estimated_mA"] for o in other),
        }
        if other:
            rail_info["other_loads"] = other

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

            # LDO thermal dissipation: uses the rail's total load (ICs +
            # other loads like LEDs) -- KH-375/KH-386 need the same number.
            if reg.get("topology") == "LDO" and v_in_rail and v_out:
                v_in = _estimate_rail_voltage(v_in_rail)
                if v_in and v_in > v_out:
                    total_load_mA = rail_info["estimated_load_mA"]
                    v_drop = v_in - v_out
                    power_w = v_drop * (total_load_mA / 1000.0)
                    rail_info["ldo_dissipation"] = {
                        "input_voltage": v_in,
                        "dropout": round(v_drop, 2),
                        "power_mW": round(power_w * 1000, 1),
                    }
                    if power_w > 0.5:
                        observations.append(
                            f"{rail}: LDO {reg['ref']} dissipates ~{power_w * 1000:.0f} mW "
                            f"({v_drop:.1f}V drop x {total_load_mA} mA) — verify thermal rating"
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
    usb_findings: list[dict] = []

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

        # Shared ESD-part keyword list: vbus_esd_protection credit (KH-338)
        # + the usb_esd_ic check below.
        esd_keywords = ("usblc", "prtr5v", "ip4", "sp0", "tpd", "esd", "pesd",
                        "rclamp", "nup", "lesd")

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
                elif pc["type"] == "ic":
                    # KH-338: ESD arrays (USBLC6 etc.) protect VBUS through
                    # their own VBUS pin — credit them even when the net is
                    # unnamed (resolution is by connector pin, not net name).
                    _combined = (pc.get("value", "") + " "
                                 + pc.get("lib_id", "")).lower()
                    if any(k in _combined for k in esd_keywords):
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

        # KH-338: promote failed checks to rich findings so they reach
        # findings[] / summaries instead of living only in this aux section.
        _uc_specs = {
            "vbus_decoupling": (
                "UC-001",
                f"No decoupling capacitor on VBUS at {ref}",
                f"USB connector {ref}: no capacitor found on the VBUS net. "
                f"USB 2.0 recommends >=1uF bulk + 100nF local decoupling on VBUS.",
                f"Add bulk (>=1uF) + 100nF decoupling on VBUS near {ref}.",
                [vbus_net] if vbus_net else [],
            ),
            "vbus_esd_protection": (
                "UC-002",
                f"No ESD/TVS protection on VBUS at {ref}",
                f"USB connector {ref}: no TVS diode or ESD array found on the "
                f"VBUS net. VBUS is exposed to external ESD/surge events.",
                f"Add a TVS diode or ESD array on VBUS at {ref}.",
                [vbus_net] if vbus_net else [],
            ),
            "cc1_pulldown_5k1": (
                "UC-003",
                f"CC1 missing 5.1k pull-down at {ref}",
                f"USB-C sink {ref}: CC1 has no 5.1k pull-down to GND and no "
                f"PD controller was found. A source will not present VBUS.",
                f"Add a 5.1k pull-down on CC1 (or a PD controller) at {ref}.",
                [],
            ),
            "cc2_pulldown_5k1": (
                "UC-003",
                f"CC2 missing 5.1k pull-down at {ref}",
                f"USB-C sink {ref}: CC2 has no 5.1k pull-down to GND and no "
                f"PD controller was found. A source will not present VBUS.",
                f"Add a 5.1k pull-down on CC2 (or a PD controller) at {ref}.",
                [],
            ),
        }
        for _check_name, _spec in _uc_specs.items():
            if conn_checks["checks"].get(_check_name) != "fail":
                continue
            _rid, _summary, _desc, _rec, _nets_f = _spec
            usb_findings.append(make_finding(
                detector="analyze_usb_compliance",
                rule_id=_rid,
                category="usb_compliance",
                summary=_summary,
                description=_desc,
                severity="warning",
                confidence="deterministic",
                evidence_source="topology",
                components=[ref],
                nets=[n for n in _nets_f if n],
                recommendation=_rec,
                report_section="USB Compliance",
                impact="USB functionality / robustness",
                check=_check_name,
                schema_era="v3.0",
            ))
        if conn_checks["checks"].get("vbus_capacitance") == "warning":
            _detail = conn_checks.get("vbus_capacitance_detail", {})
            usb_findings.append(make_finding(
                detector="analyze_usb_compliance",
                rule_id="UC-004",
                category="usb_compliance",
                summary=(f"VBUS decoupling may be undersized at {ref} "
                         f"({_detail.get('total_uf')}uF total)"),
                description=_detail.get(
                    "detail", "VBUS capacitance below recommended minimum."),
                severity="warning",
                confidence="deterministic",
                evidence_source="topology",
                components=[ref],
                nets=[vbus_net] if vbus_net else [],
                recommendation=(f"Increase VBUS bulk capacitance at {ref} "
                                f"to >=1uF (USB 2.0)."),
                report_section="USB Compliance",
                impact="VBUS droop on connect",
                check="vbus_capacitance",
                schema_era="v3.0",
            ))

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
    if usb_findings:
        result["findings"] = usb_findings
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
