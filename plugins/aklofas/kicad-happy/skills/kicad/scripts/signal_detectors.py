"""
Signal path detector functions extracted from analyze_signal_paths().

Each detector takes an AnalysisContext (ctx) and returns its detection results.
Some detectors also take prior results for cross-references.
"""

import math
import re

from kicad_utils import (
    _LOAD_TYPE_KEYWORDS,
    classify_jumper_default_state,
    format_frequency as _format_frequency,
    is_ground_name,
    is_power_net_name,
    lookup_regulator_vref as _lookup_regulator_vref,
    lookup_switching_freq,
    match_known_switching as _match_known_switching,
    parse_value,
    parse_voltage_from_net_name as _parse_voltage_from_net_name,
)
from kicad_types import AnalysisContext
from finding_schema import make_provenance
from detector_helpers import index_two_pin_components, get_components_by_type, get_unique_ics


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _default_switching_freq(topology: str) -> float | None:
    """Fallback switching frequency estimate when part is unrecognized.

    Based on typical ranges for each topology. Conservative (low end)
    to avoid underestimating harmonic reach.
    """
    defaults = {
        'buck': 500e3,
        'boost': 500e3,
        'buck-boost': 300e3,
        'inverting': 300e3,
        'sepic': 300e3,
    }
    return defaults.get(topology.lower()) if topology else None


def _get_net_components(ctx: AnalysisContext, net_name, exclude_ref):
    """Get components on a net excluding the given component."""
    if ctx.nq:
        return ctx.nq.components_on_net(net_name, exclude_refs={exclude_ref})
    if net_name not in ctx.nets:
        return []
    result_comps = []
    for p in ctx.nets[net_name]["pins"]:
        if p["component"] == exclude_ref:
            continue
        comp = ctx.comp_lookup.get(p["component"])
        if comp:
            result_comps.append({
                "reference": p["component"],
                "type": comp["type"],
                "value": comp["value"],
                "pin_name": p.get("pin_name", ""),
                "pin_number": p["pin_number"],
            })
    return result_comps


def _classify_load(ctx: AnalysisContext, net_name, exclude_ref):
    """Classify what's on a net as a load type.

    Checks net name keywords first (motor, heater, fan, solenoid, valve,
    pump, relay, speaker, buzzer, lamp) for cases where the net name
    reveals the load type better than the connected components.
    Falls back to component-type classification.
    """
    # Net name keyword classification — catches loads driven through
    # connectors or across sheet boundaries where component type alone
    # would just show "connector" or "other"
    if net_name:
        nu = net_name.upper()
        for load_type, keywords in _LOAD_TYPE_KEYWORDS.items():
            if any(kw in nu for kw in keywords):
                return load_type

    comps = _get_net_components(ctx, net_name, exclude_ref)
    types = {c["type"] for c in comps}
    if "inductor" in types:
        return "inductive"
    if "led" in types:
        return "led"
    if types == {"resistor"} or types == {"resistor", "capacitor"}:
        return "resistive"
    if "connector" in types:
        return "connector"
    if "ic" in types:
        return "ic"
    if "transistor" in types:
        return "transistor"  # cascaded
    return "other"


def _parse_crystal_frequency(value_str: str) -> float | None:
    """Parse crystal frequency from value string or part number.

    Tries parse_value() first, then regex for embedded MHz/kHz patterns
    like "YIC-12M20P2" → 12e6, "ABM8-25.000MHZ" → 25e6.
    """
    result = parse_value(value_str)
    if result is not None:
        return result
    if not value_str:
        return None
    # Explicit MHz/kHz in value
    m = re.search(r'(\d+\.?\d*)\s*[Mm][Hh][Zz]', value_str)
    if m:
        return float(m.group(1)) * 1e6
    m = re.search(r'(\d+\.?\d*)\s*[Kk][Hh][Zz]', value_str)
    if m:
        return float(m.group(1)) * 1e3
    # MPN patterns: "YIC-12M20P2" → 12MHz, "-25M000" → 25MHz
    m = re.search(r'[-_](\d+)[Mm]\d', value_str)
    if m:
        return float(m.group(1)) * 1e6
    return None


# Typical crystal load capacitance by frequency — used as fallback when the
# crystal value string doesn't include a pF specification.
# Sources: ECS crystal catalog (2024), Abracon AB series, Murata SA series.
_CRYSTAL_DEFAULT_CL = {
    32768: 12.5,         # Watch crystals: almost universally 12.5 pF
    100e3: 12.5,
    1e6: 12.5,
    2e6: 12.5,
    3.579545e6: 20.0,    # NTSC colorburst — historically 20 pF
    4e6: 12.5,
    8e6: 18.0,
    10e6: 20.0,
    12e6: 20.0,
    16e6: 20.0,
    20e6: 18.0,
    24e6: 10.0,           # 24 MHz: 10 pF (STM32 standard)
    25e6: 10.0,           # 25 MHz: 10 pF (Ethernet PHY standard)
    26e6: 10.0,           # 26 MHz: 10 pF (Bluetooth/WiFi common)
    27e6: 10.0,
    32e6: 10.0,
    48e6: 10.0,
}


def _crystal_default_cl(freq_hz: float) -> float | None:
    """Look up typical crystal load capacitance for a given frequency.

    Returns CL in pF or None if frequency is unknown. Uses exact match
    first (within 1% tolerance), then falls back to frequency-band default.
    """
    if not freq_hz or freq_hz <= 0:
        return None
    # Exact match (within 1% tolerance for frequency rounding)
    for table_freq, cl in _CRYSTAL_DEFAULT_CL.items():
        if abs(freq_hz - table_freq) / table_freq < 0.01:
            return cl
    # Broad frequency-band fallback
    if freq_hz <= 100e3:
        return 12.5
    elif freq_hz <= 4e6:
        return 12.5
    elif freq_hz <= 16e6:
        return 18.0
    elif freq_hz <= 30e6:
        return 10.0
    else:
        return 10.0


# ---------------------------------------------------------------------------
# Divider purpose classification
# ---------------------------------------------------------------------------

def _classify_divider_purpose(divider: dict) -> str:
    """Classify a voltage divider's purpose from connected pin names.

    Examines mid_point_connections pin names and the is_feedback flag to
    determine: adc_input, feedback, bias, reference, enable_threshold, or unknown.
    """
    if divider.get("is_feedback"):
        return "feedback"

    mid_pins = divider.get("mid_point_connections", [])
    for mp in mid_pins:
        pn = mp.get("pin_name", "").upper()
        if not pn:
            continue
        # ADC / analog input
        if any(k in pn for k in ("ADC", "AIN", "ANALOG")):
            return "adc_input"
        # Feedback
        if any(k in pn for k in ("FB", "FEEDBACK")):
            return "feedback"
        # Enable / shutdown threshold
        if any(k in pn for k in ("EN", "ENABLE", "SHDN")):
            return "enable_threshold"
        # Comparator / reference / threshold
        if any(k in pn for k in ("COMP", "REF", "THRESH")):
            return "reference"
        # Bias input (opamp, comparator non-inverting/inverting)
        if any(k in pn for k in ("IN+", "IN-", "INP", "INM")):
            return "bias"

    return "unknown"


# ---------------------------------------------------------------------------
# Detectors
# ---------------------------------------------------------------------------

def detect_voltage_dividers(ctx: AnalysisContext) -> dict:
    """Detect voltage dividers and feedback networks.

    Returns dict with keys ``voltage_dividers`` and ``feedback_networks``.
    """
    voltage_dividers: list[dict] = []
    feedback_networks: list[dict] = []

    # ---- Voltage Dividers ----
    # Two resistors in series between different nets, with a mid-point net
    resistors = get_components_by_type(ctx, "resistor", with_parsed_values=True)
    resistor_nets, net_to_resistors = index_two_pin_components(ctx, resistors)

    # Check pairs of resistors that share a net (potential dividers)
    vd_seen = set()  # track (r1, r2) pairs to avoid duplicates
    for net_name, refs in net_to_resistors.items():
        if len(refs) < 2:
            continue
        for i, r1_ref in enumerate(refs):
            r1_n1, r1_n2 = resistor_nets[r1_ref]
            r1 = ctx.comp_lookup[r1_ref]
            for r2_ref in refs[i + 1:]:
                pair_key = (min(r1_ref, r2_ref), max(r1_ref, r2_ref))
                if pair_key in vd_seen:
                    continue
                vd_seen.add(pair_key)

                r2_n1, r2_n2 = resistor_nets[r2_ref]
                r2 = ctx.comp_lookup[r2_ref]

                # Find shared net (mid-point)
                r1_nets = {r1_n1, r1_n2}
                r2_nets = {r2_n1, r2_n2}
                shared = r1_nets & r2_nets
                if len(shared) != 1:
                    continue

                mid_net = shared.pop()
                top_net = (r1_nets - {mid_net}).pop()
                bot_net = (r2_nets - {mid_net}).pop()

                # Reject if mid-point is a power rail with many connections —
                # that's a power bus, not a divider output. Real divider mid-points
                # connect to 2 resistors + maybe an IC input (≤4 connections).
                if ctx.is_power_net(mid_net) or ctx.is_ground(mid_net):
                    mid_pin_count = len(ctx.nets.get(mid_net, {}).get("pins", []))
                    if mid_pin_count > 4:
                        continue

                # KH-238: Normalize orientation FIRST so the ordering of
                # r1/r2 in the outer loop can't drop valid pairs. If
                # exactly one end is ground, ensure it's bot_net. This
                # subsumes the previous "is_ground(top) and is_power(bot)"
                # swap (a strict subset of this condition) and also
                # catches the unnamed-top-net case that was getting
                # dropped by the ordering-sensitive fall-through.
                if ctx.is_ground(top_net) and not ctx.is_ground(bot_net):
                    top_net, bot_net = bot_net, top_net
                    r1, r2 = r2, r1

                # One end should be power, other should be ground (or another power)
                if not (ctx.is_power_net(top_net) and (ctx.is_ground(bot_net) or ctx.is_power_net(bot_net))):
                    # Also catch feedback dividers: output -> mid -> ground.
                    # After the KH-238 normalization above, an unnamed
                    # top_net with ground bot_net reaches this branch
                    # and passes.
                    if not ctx.is_ground(bot_net):
                        continue

                r1_val = ctx.parsed_values[r1["reference"]]
                r2_val = ctx.parsed_values[r2["reference"]]
                if r1_val <= 0 or r2_val <= 0:
                    continue
                # Extreme ratio → pull-up/pull-down pair, not a real divider.
                # 1000:1 threshold accommodates HV sensing (mains voltage,
                # battery monitoring) where 10M/10K dividers are common.
                if max(r1_val, r2_val) / min(r1_val, r2_val) > 1000:
                    continue

                # Determine which is top/bottom based on net position
                if ctx.is_ground(bot_net):
                    # r_top connects top_net to mid, r_bot connects mid to gnd
                    # Re-derive nets from current r1/r2 (may have been swapped above)
                    r1_nets_cur = set(ctx.get_two_pin_nets(r1["reference"]))
                    if top_net in r1_nets_cur:
                        r_top, r_bot = r1_val, r2_val
                        r_top_ref, r_bot_ref = r1["reference"], r2["reference"]
                    else:
                        r_top, r_bot = r2_val, r1_val
                        r_top_ref, r_bot_ref = r2["reference"], r1["reference"]

                    ratio = r_bot / (r_top + r_bot)

                    divider = {
                        "r_top": {"ref": r_top_ref, "value": ctx.comp_lookup[r_top_ref]["value"], "ohms": r_top},
                        "r_bottom": {"ref": r_bot_ref, "value": ctx.comp_lookup[r_bot_ref]["value"], "ohms": r_bot},
                        "top_net": top_net,
                        "mid_net": mid_net,
                        "bottom_net": bot_net,
                        "ratio": round(ratio, 6),
                    }

                    # Check if mid-point connects to a known feedback pin
                    if mid_net in ctx.nets:
                        mid_pins = [p for p in ctx.nets[mid_net]["pins"]
                                    if p["component"] != r_top_ref
                                    and p["component"] != r_bot_ref
                                    and not p["component"].startswith("#")]
                        if mid_pins:
                            divider["mid_point_connections"] = mid_pins
                            # If connected to an IC FB pin, this is likely a feedback network
                            for mp in mid_pins:
                                if "FB" in mp.get("pin_name", "").upper():
                                    divider["is_feedback"] = True
                                    divider["detector"] = "detect_voltage_dividers"
                                    divider["rule_id"] = "VD-DET"
                                    divider["category"] = "voltage_dividers"
                                    divider["severity"] = "info"
                                    divider["confidence"] = "deterministic"
                                    divider["evidence_source"] = "topology"
                                    divider["summary"] = f"Voltage divider {r_top_ref}/{r_bot_ref}"
                                    divider["description"] = "Feedback network voltage divider detected"
                                    divider["components"] = [r_top_ref, r_bot_ref]
                                    divider["nets"] = []
                                    divider["pins"] = []
                                    divider["recommendation"] = ""
                                    divider["report_context"] = {"section": "Voltage Dividers", "impact": "", "standard_ref": ""}
                                    divider["provenance"] = make_provenance("vd_two_resistor", "deterministic", [r_top_ref, r_bot_ref])
                                    feedback_networks.append(divider)
                                    break

                    # Classify divider purpose from connected pin names
                    divider["purpose"] = _classify_divider_purpose(divider)
                    divider["detector"] = "detect_voltage_dividers"
                    divider["rule_id"] = "VD-DET"
                    divider["category"] = "voltage_dividers"
                    divider["severity"] = "info"
                    divider["confidence"] = "deterministic"
                    divider["evidence_source"] = "topology"
                    divider["summary"] = f"Voltage divider {r_top_ref}/{r_bot_ref}"
                    divider["description"] = "Resistive voltage divider detected"
                    divider["components"] = [r_top_ref, r_bot_ref]
                    divider["nets"] = []
                    divider["pins"] = []
                    divider["recommendation"] = ""
                    divider["report_context"] = {"section": "Voltage Dividers", "impact": "", "standard_ref": ""}
                    divider["provenance"] = make_provenance("vd_two_resistor", "deterministic", [r_top_ref, r_bot_ref])

                    voltage_dividers.append(divider)

    return {"voltage_dividers": voltage_dividers, "feedback_networks": feedback_networks}


def _merge_series_dividers(voltage_dividers: list[dict], ctx: AnalysisContext) -> list[dict]:
    """Merge series resistors in voltage divider chains (KH-105, KH-115).

    When a divider's top_net or bottom_net is a pass-through node (connects
    to exactly 2 resistors and no IC/active pins), extend the chain through
    it, combining series resistances.
    """
    # Build resistor-net index
    all_resistors = get_components_by_type(ctx, "resistor", with_parsed_values=True)
    resistor_nets, net_to_resistors = index_two_pin_components(ctx, all_resistors)

    def _is_passthrough(net_name):
        """A pass-through node connects exactly 2 resistors and no active components."""
        if ctx.is_power_net(net_name) or ctx.is_ground(net_name):
            return False
        r_at_net = net_to_resistors.get(net_name, [])
        if len(r_at_net) != 2:
            return False
        if net_name not in ctx.nets:
            return True
        for p in ctx.nets[net_name]["pins"]:
            comp = ctx.comp_lookup.get(p["component"])
            if comp and comp["type"] not in ("resistor",):
                return False
        return True

    def _extend_chain(start_ref, into_net):
        """Follow series resistors through pass-through nodes.
        Returns [(ref, ohms), ...] of additional resistors and the final net."""
        extra = []
        cur_ref = start_ref
        cur_net = into_net
        while _is_passthrough(cur_net):
            others = [r for r in net_to_resistors.get(cur_net, []) if r != cur_ref]
            if len(others) != 1:
                break
            nxt = others[0]
            if nxt not in ctx.parsed_values:
                break
            extra.append((nxt, ctx.parsed_values[nxt]))
            n1, n2 = resistor_nets[nxt]
            cur_net = n2 if n1 == cur_net else n1
            cur_ref = nxt
        return extra, cur_net

    result = []
    chain_member_refs = set()

    for vd in voltage_dividers:
        r_top_ref = vd["r_top"]["ref"]
        r_bot_ref = vd["r_bottom"]["ref"]

        # Extend top chain through top_net
        top_extra, new_top_net = _extend_chain(r_top_ref, vd["top_net"])
        # Extend bottom chain through bottom_net
        bot_extra, new_bot_net = _extend_chain(r_bot_ref, vd["bottom_net"])

        if not top_extra and not bot_extra:
            result.append(vd)
            continue

        new_vd = dict(vd)

        if top_extra:
            all_top = [(r_top_ref, vd["r_top"]["ohms"])] + top_extra
            total_top = sum(o for _, o in all_top)
            new_vd["r_top"] = dict(vd["r_top"])
            new_vd["r_top"]["ohms"] = total_top
            new_vd["r_top"]["chain_resistors"] = [
                {"ref": r, "ohms": o} for r, o in all_top
            ]
            new_vd["top_net"] = new_top_net
            for r, _ in all_top:
                chain_member_refs.add(r)

        if bot_extra:
            all_bot = [(r_bot_ref, vd["r_bottom"]["ohms"])] + bot_extra
            total_bot = sum(o for _, o in all_bot)
            new_vd["r_bottom"] = dict(vd["r_bottom"])
            new_vd["r_bottom"]["ohms"] = total_bot
            new_vd["r_bottom"]["chain_resistors"] = [
                {"ref": r, "ohms": o} for r, o in all_bot
            ]
            new_vd["bottom_net"] = new_bot_net
            for r, _ in all_bot:
                chain_member_refs.add(r)

        # Recalculate ratio
        r_t = new_vd["r_top"]["ohms"]
        r_b = new_vd["r_bottom"]["ohms"]
        if r_t + r_b > 0:
            new_vd["ratio"] = round(r_b / (r_t + r_b), 6)

        result.append(new_vd)

    # Mark sub-pair dividers whose resistors are all part of a chain
    for vd in result:
        if "chain_resistors" in vd.get("r_top", {}) or "chain_resistors" in vd.get("r_bottom", {}):
            continue  # This IS the chain divider
        if vd["r_top"]["ref"] in chain_member_refs and vd["r_bottom"]["ref"] in chain_member_refs:
            vd["suppressed_by_chain"] = True

    return result


def detect_rc_filters(ctx: AnalysisContext, voltage_dividers: list[dict],
                      crystal_circuits: list[dict] | None = None,
                      opamp_circuits: list[dict] | None = None) -> list[dict]:
    """Detect RC filters. Takes voltage_dividers/crystal_circuits/opamp_circuits to exclude."""
    results_rc: list[dict] = []

    resistors = get_components_by_type(ctx, "resistor", with_parsed_values=True)
    resistor_nets, _ = index_two_pin_components(ctx, resistors)

    # ---- RC Filters ----
    # R and C must share a SIGNAL net (not power/ground) to form a real filter.
    # If they only share GND, every R and C in the circuit would match.
    # Exclude resistors that are part of voltage dividers — pairing a feedback
    # divider resistor with an output decoupling cap is a common false positive.
    vd_resistor_refs = set()
    for vd in voltage_dividers:
        vd_resistor_refs.add(vd["r_top"]["ref"])
        vd_resistor_refs.add(vd["r_bottom"]["ref"])

    # KH-145: Exclude opamp feedback resistors, capacitors, and input resistors
    opamp_exclude_refs = set()
    for oa in (opamp_circuits or []):
        fb_r = oa.get("feedback_resistor")
        if isinstance(fb_r, dict):
            opamp_exclude_refs.add(fb_r.get("ref", ""))
        fb_c = oa.get("feedback_capacitor")
        if isinstance(fb_c, dict):
            opamp_exclude_refs.add(fb_c.get("ref", ""))
        inp_r = oa.get("input_resistor")
        if isinstance(inp_r, dict):
            opamp_exclude_refs.add(inp_r.get("ref", ""))
    opamp_exclude_refs.discard("")

    # KH-107: Exclude crystal circuit components (load caps + feedback resistors)
    crystal_refs = set()
    for xtal in (crystal_circuits or []):
        crystal_refs.add(xtal.get("reference", ""))
        for lc in xtal.get("load_caps", []):
            crystal_refs.add(lc["ref"])
        fb = xtal.get("feedback_resistor")
        if isinstance(fb, dict):
            crystal_refs.add(fb.get("ref", ""))
        elif isinstance(fb, str) and fb:
            crystal_refs.add(fb)

    capacitors = get_components_by_type(ctx, "capacitor", with_parsed_values=True)
    cap_nets, net_to_caps = index_two_pin_components(ctx, capacitors)

    # KH-121: Track seen R-C pairs to prevent bidirectional duplicates
    seen_rc_pairs: set[frozenset[str]] = set()

    for res in resistors:
        if res["reference"] in vd_resistor_refs:
            continue  # Skip voltage divider resistors
        if res["reference"] in crystal_refs:
            continue  # KH-107: Skip crystal circuit components
        if res["reference"] in opamp_exclude_refs:
            continue  # KH-145: Skip opamp feedback/input resistors
        if res["reference"] not in resistor_nets:
            continue
        r_n1, r_n2 = resistor_nets[res["reference"]]
        r_nets = {r_n1, r_n2}

        # Only check capacitors that share a net with this resistor
        candidate_caps = set()
        for rn in (r_n1, r_n2):
            if not ctx.is_power_net(rn) and not ctx.is_ground(rn):
                for cref in net_to_caps.get(rn, ()):
                    candidate_caps.add(cref)

        for cap_ref in candidate_caps:
            if cap_ref in crystal_refs:
                continue  # KH-107: Skip crystal circuit components
            if cap_ref in opamp_exclude_refs:
                continue  # KH-145: Skip opamp feedback capacitors

            # KH-121: Skip if this R-C pair was already found from the other direction
            rc_pair = frozenset((res["reference"], cap_ref))
            if rc_pair in seen_rc_pairs:
                continue

            c_n1, c_n2 = cap_nets[cap_ref]
            c_nets = {c_n1, c_n2}

            shared = r_nets & c_nets
            if len(shared) != 1:
                continue

            shared_net = shared.pop()

            # The shared net must NOT be a power/ground rail — those create
            # false matches between every R and C on the board.
            if ctx.is_power_net(shared_net) or ctx.is_ground(shared_net):
                continue

            # Reject if shared net has too many non-passive connections.
            # A real RC filter node typically has 2-3 connections (R + C +
            # maybe one IC pin).  On high-fanout nets, accept if most
            # connections are passives (filter node with parallel caps),
            # reject if many ICs are connected (bus/data line).
            shared_pin_count = len(ctx.nets.get(shared_net, {}).get("pins", []))
            if shared_pin_count > 6:
                if ctx.nq:
                    non_passive = sum(
                        1 for c in ctx.nq.components_on_net(shared_net)
                        if c["type"] not in ("resistor", "capacitor", "inductor"))
                    if non_passive > 3:
                        continue
                else:
                    continue

            r_other = (r_nets - {shared_net}).pop()
            c_other = (c_nets - {shared_net}).pop()

            # KH-116: Skip if R and C non-shared ends are the same net —
            # output==ground is logically impossible for a filter
            if r_other == c_other:
                continue

            r_val = ctx.parsed_values[res["reference"]]
            c_val = ctx.parsed_values[cap_ref]

            # Skip pairs where R or C has no valid value (None or zero) — a
            # 0-ohm resistor or unparsed capacitor is not a filter.
            if not r_val or not c_val:
                continue

            # EQ-020: f_c = 1/(2πRC) (RC filter cutoff frequency)
            if r_val > 0 and c_val > 0:
                fc = 1.0 / (2.0 * math.pi * r_val * c_val)
                tau = r_val * c_val

                # Classify filter type
                if ctx.is_ground(c_other):
                    filter_type = "low-pass"
                elif ctx.is_ground(r_other):
                    filter_type = "high-pass"
                else:
                    filter_type = "RC-network"

                # Skip if R is very small — likely series termination or current
                # sense shunt, not an intentional filter
                if r_val < 10:
                    continue

                rc_entry = {
                    "type": filter_type,
                    "resistor": {"ref": res["reference"], "value": ctx.comp_lookup[res["reference"]]["value"], "ohms": r_val},
                    "capacitor": {"ref": cap_ref, "value": ctx.comp_lookup[cap_ref]["value"], "farads": c_val},
                    "cutoff_hz": round(fc, 2),
                    "time_constant_s": tau,
                    "input_net": r_other if filter_type == "low-pass" else shared_net,
                    "output_net": shared_net if filter_type == "low-pass" else r_other,
                    # KH-116: Use c_other as ground if it IS ground, else use
                    # r_other only if it IS ground; otherwise report c_other
                    # (the capacitor's far end) to avoid output==ground
                    "ground_net": c_other if ctx.is_ground(c_other) else (
                        r_other if ctx.is_ground(r_other) else c_other),
                }

                rc_entry["cutoff_formatted"] = _format_frequency(fc)
                rc_entry["detector"] = "detect_rc_filters"
                rc_entry["rule_id"] = "RC-DET"
                rc_entry["category"] = "passive_filters"
                rc_entry["severity"] = "info"
                rc_entry["confidence"] = "deterministic"
                rc_entry["evidence_source"] = "topology"
                rc_entry["summary"] = f"RC filter {res['reference']}/{cap_ref} at {round(fc, 2)}Hz"
                rc_entry["description"] = f"{filter_type} RC filter"
                rc_entry["components"] = [res["reference"], cap_ref]
                rc_entry["nets"] = []
                rc_entry["pins"] = []
                rc_entry["recommendation"] = ""
                rc_entry["report_context"] = {"section": "Passive Filters", "impact": "", "standard_ref": ""}
                rc_entry["provenance"] = make_provenance("rc_topology", "deterministic", [res["reference"], cap_ref])

                seen_rc_pairs.add(rc_pair)
                results_rc.append(rc_entry)

    # Merge RC filters where the same resistor pairs with multiple caps on
    # the same shared net (parallel caps = one effective filter, not N filters).
    _rc_groups: dict[tuple[str, str, str], list[dict]] = {}
    for rc in results_rc:
        key = (rc["resistor"]["ref"], rc.get("input_net", ""), rc.get("output_net", ""))
        _rc_groups.setdefault(key, []).append(rc)
    merged_rc: list[dict] = []
    for key, entries in _rc_groups.items():
        if len(entries) == 1:
            merged_rc.append(entries[0])
        else:
            total_c = sum(e["capacitor"]["farads"] for e in entries)
            r_val = entries[0]["resistor"]["ohms"]
            fc = 1.0 / (2.0 * math.pi * r_val * total_c)
            tau = r_val * total_c
            cap_refs = [e["capacitor"]["ref"] for e in entries]
            base = entries[0].copy()
            base["capacitor"] = {
                "ref": cap_refs[0],
                "value": f"{len(entries)} caps parallel",
                "farads": total_c,
                "parallel_caps": cap_refs,
            }
            base["cutoff_hz"] = round(fc, 2)
            base["time_constant_s"] = tau
            base["cutoff_formatted"] = _format_frequency(fc)
            merged_rc.append(base)
    return merged_rc


def detect_lc_filters(ctx: AnalysisContext) -> list[dict]:
    """Detect LC filters."""
    capacitors = get_components_by_type(ctx, "capacitor", with_parsed_values=True)
    inductors = get_components_by_type(ctx, ("inductor", "ferrite_bead"), with_parsed_values=True)

    # Collect LC pairs grouped by (inductor, shared_net). Multiple caps on
    # the same inductor output node are parallel decoupling, not separate
    # filters — merge them into one entry with summed capacitance.
    _lc_groups: dict[tuple[str, str], list[dict]] = {}

    for ind in inductors:
        # Skip ferrite beads — they're impedance devices, not filter inductors
        lib_id = ind.get("lib_id", "").lower()
        val_lower = ind.get("value", "").lower()
        if (ind.get("type") == "ferrite_bead"
                or "ferrite" in lib_id or "bead" in lib_id
                or "ferrite" in val_lower or "bead" in val_lower):
            continue
        l_n1, l_n2 = ctx.get_two_pin_nets(ind["reference"])
        if not l_n1 or not l_n2:
            continue

        for cap in capacitors:
            c_n1, c_n2 = ctx.get_two_pin_nets(cap["reference"])
            if not c_n1 or not c_n2:
                continue

            l_nets = {l_n1, l_n2}
            c_nets = {c_n1, c_n2}
            # Skip components with both pins on the same net (shorted)
            if len(l_nets) < 2 or len(c_nets) < 2:
                continue
            shared = l_nets & c_nets
            if len(shared) != 1:
                continue

            shared_net_lc = shared.pop()
            # Skip if shared net is power/ground (would match all L-C pairs)
            if ctx.is_power_net(shared_net_lc) or ctx.is_ground(shared_net_lc):
                continue

            # KH-119: Skip high-fanout shared nets — in RF designs, impedance
            # matching networks share nets with many L/C components. Real LC
            # filters have 2-4 connections at the junction node.
            shared_pin_count = len(ctx.nets.get(shared_net_lc, {}).get("pins", []))
            if shared_pin_count > 6:
                if ctx.nq:
                    non_passive = sum(
                        1 for c in ctx.nq.components_on_net(shared_net_lc)
                        if c["type"] not in ("resistor", "capacitor", "inductor"))
                    if non_passive > 3:
                        continue
                else:
                    continue

            # Skip bootstrap capacitors: cap between BST/BOOT pin and SW/LX node.
            # These are gate-drive charge pumps, not signal filters.
            cap_other_net = (c_nets - {shared_net_lc}).pop()
            is_bootstrap = False
            if cap_other_net and cap_other_net in ctx.nets:
                for p in ctx.nets[cap_other_net]["pins"]:
                    pn = p.get("pin_name", "").upper().rstrip("0123456789").rstrip("_")
                    pn_parts = {pp.strip() for pp in pn.split("/")}
                    if pn_parts & {"BST", "BOOT", "BOOTSTRAP", "CBST"}:
                        is_bootstrap = True
                        break
            if is_bootstrap:
                continue

            l_val = ctx.parsed_values[ind["reference"]]
            c_val = ctx.parsed_values[cap["reference"]]

            if l_val > 0 and c_val > 0:
                # EQ-021: f₀ = 1/(2π√(LC)) (LC resonant frequency)
                f0 = 1.0 / (2.0 * math.pi * math.sqrt(l_val * c_val))
                # EQ-022: Z₀ = √(L/C) (LC characteristic impedance)
                z0 = math.sqrt(l_val / c_val)  # characteristic impedance

                lc_entry = {
                    "inductor": {"ref": ind["reference"], "value": ctx.comp_lookup[ind["reference"]]["value"], "henries": l_val},
                    "capacitor": {"ref": cap["reference"], "value": ctx.comp_lookup[cap["reference"]]["value"], "farads": c_val},
                    "resonant_hz": round(f0, 2),
                    "impedance_ohms": round(z0, 2),
                    "shared_net": shared_net_lc,
                }

                lc_entry["resonant_formatted"] = _format_frequency(f0)
                lc_entry["detector"] = "detect_lc_filters"
                lc_entry["rule_id"] = "LC-DET"
                lc_entry["category"] = "passive_filters"
                lc_entry["severity"] = "info"
                lc_entry["confidence"] = "deterministic"
                lc_entry["evidence_source"] = "topology"
                lc_entry["summary"] = f"LC filter at {round(f0, 2)}Hz"
                lc_entry["description"] = "LC filter or resonant network detected"
                lc_entry["components"] = [ind["reference"], cap["reference"]]
                lc_entry["nets"] = []
                lc_entry["pins"] = []
                lc_entry["recommendation"] = ""
                lc_entry["report_context"] = {"section": "Passive Filters", "impact": "", "standard_ref": ""}
                lc_entry["provenance"] = make_provenance("lc_topology", "deterministic", [ind["reference"], cap["reference"]])

                cap_other_net_for_group = (c_nets - {shared_net_lc}).pop()
                _lc_groups.setdefault((ind["reference"], shared_net_lc, cap_other_net_for_group), []).append(lc_entry)

    # Merge parallel caps per inductor-net pair
    lc_filters: list[dict] = []
    for (_ind_ref, _shared_net, _other_net), entries in _lc_groups.items():
        # KH-198: Deduplicate caps by reference (multi-project schematics
        # can have multiple components sharing the same reference designator)
        seen_refs = set()
        deduped = []
        for e in entries:
            cref = e["capacitor"]["ref"]
            if cref not in seen_refs:
                seen_refs.add(cref)
                deduped.append(e)
        entries = deduped

        if len(entries) == 1:
            lc_filters.append(entries[0])
        else:
            total_c = sum(e["capacitor"]["farads"] for e in entries)
            l_val = entries[0]["inductor"]["henries"]
            f0 = 1.0 / (2.0 * math.pi * math.sqrt(l_val * total_c))
            z0 = math.sqrt(l_val / total_c)
            cap_refs = [e["capacitor"]["ref"] for e in entries]
            merged = {
                "inductor": entries[0]["inductor"],
                "capacitor": {
                    "ref": cap_refs[0],
                    "value": f"{len(entries)} caps parallel",
                    "farads": total_c,
                    "parallel_caps": cap_refs,
                },
                "resonant_hz": round(f0, 2),
                "impedance_ohms": round(z0, 2),
                "shared_net": _shared_net,
            }
            merged["resonant_formatted"] = _format_frequency(f0)
            merged["detector"] = "detect_lc_filters"
            merged["rule_id"] = "LC-DET"
            merged["category"] = "passive_filters"
            merged["severity"] = "info"
            merged["confidence"] = "deterministic"
            merged["evidence_source"] = "topology"
            merged["summary"] = f"LC filter at {round(f0, 2)}Hz"
            merged["description"] = "LC filter with parallel capacitors"
            merged["components"] = [entries[0]["inductor"]["ref"]] + cap_refs
            merged["nets"] = []
            merged["pins"] = []
            merged["recommendation"] = ""
            merged["report_context"] = {"section": "Passive Filters", "impact": "", "standard_ref": ""}
            merged["provenance"] = make_provenance("lc_topology", "deterministic", [entries[0]["inductor"]["ref"]] + cap_refs)
            lc_filters.append(merged)

    # KH-119: Suppress overcounting — if one inductor pairs with caps on BOTH
    # its nets, it's likely an RF impedance matching network, not separate LC
    # filters. Keep at most 1 entry per inductor net (the largest capacitance).
    from collections import defaultdict
    _ind_nets: dict[str, set[str]] = defaultdict(set)
    for f in lc_filters:
        _ind_nets[f["inductor"]["ref"]].add(f["shared_net"])
    # Inductors with caps on both nets → matching network
    _match_inductors = {ref for ref, nets in _ind_nets.items() if len(nets) >= 2}
    if _match_inductors:
        keep: list[dict] = []
        # Group by (inductor, shared_net), keep only the largest cap entry
        _best: dict[tuple[str, str], dict] = {}
        for f in lc_filters:
            iref = f["inductor"]["ref"]
            if iref not in _match_inductors:
                keep.append(f)
                continue
            key = (iref, f["shared_net"])
            if key not in _best or f["capacitor"]["farads"] > _best[key]["capacitor"]["farads"]:
                _best[key] = f
        keep.extend(_best.values())
        lc_filters = keep

    return lc_filters


def detect_crystal_circuits(ctx: AnalysisContext) -> list[dict]:
    """Detect crystal oscillator circuits."""
    crystal_circuits: list[dict] = []
    crystals = [c for c in ctx.components if c["type"] == "crystal"]
    for xtal in crystals:
        xtal_pins = xtal.get("pins", [])
        if len(xtal_pins) < 2:
            continue

        # KH-114: Skip active oscillators (>=4 pins with a VCC/VDD power pin)
        # They should be handled by the active oscillator section below
        if len(xtal_pins) >= 4:
            has_power_pin = False
            for pin in xtal_pins:
                pn_upper = pin.get("name", "").upper()
                if any(kw in pn_upper for kw in ("VCC", "VDD", "V+")):
                    has_power_pin = True
                    break
                net_name, _ = ctx.pin_net.get((xtal["reference"], pin["number"]), (None, None))
                if net_name and ctx.is_power_net(net_name) and not ctx.is_ground(net_name):
                    has_power_pin = True
                    break
            if has_power_pin:
                continue

        # Find capacitors connected to crystal signal pins (not power/ground)
        xtal_nets = set()
        for pin in xtal_pins:
            net_name, _ = ctx.pin_net.get((xtal["reference"], pin["number"]), (None, None))
            if net_name and not ctx.is_power_net(net_name) and not ctx.is_ground(net_name):
                xtal_nets.add(net_name)

        load_caps = []
        for net_name in xtal_nets:
            if net_name not in ctx.nets:
                continue
            for p in ctx.nets[net_name]["pins"]:
                if p["component"] != xtal["reference"] and ctx.comp_lookup.get(p["component"], {}).get("type") == "capacitor":
                    cap_ref = p["component"]
                    cap_val = ctx.parsed_values.get(cap_ref)
                    if cap_val:
                        # Check if other end of cap goes to ground
                        cap_n1, cap_n2 = ctx.get_two_pin_nets(cap_ref)
                        other_net = cap_n2 if cap_n1 == net_name else cap_n1
                        if ctx.is_ground(other_net):
                            load_caps.append({
                                "ref": cap_ref,
                                "value": ctx.comp_lookup[cap_ref]["value"],
                                "farads": cap_val,
                                "net": net_name,
                            })

        xtal_entry = {
            "reference": xtal["reference"],
            "value": xtal.get("value", ""),
            "frequency": _parse_crystal_frequency(xtal.get("value", "")),
            "load_caps": load_caps,
        }

        # Compute effective load capacitance: CL = (C1 * C2) / (C1 + C2) + C_stray
        if len(load_caps) >= 2:
            c1 = load_caps[0]["farads"]
            c2 = load_caps[1]["farads"]
            c_stray = 3e-12  # typical stray capacitance estimate
            cl_eff = (c1 * c2) / (c1 + c2) + c_stray
            xtal_entry["effective_load_pF"] = round(cl_eff * 1e12, 2)
            xtal_entry["note"] = f"CL_eff = ({load_caps[0]['value']} * {load_caps[1]['value']}) / ({load_caps[0]['value']} + {load_caps[1]['value']}) + ~3pF stray"

        # Crystal load capacitance validation
        target_load_pF = None
        target_load_source = None
        xtal_value = xtal.get("value", "")
        # Try parsing from value string: "16MHz/18pF", "8MHz 20pF"
        load_match = re.search(r'(\d+\.?\d*)\s*pF', xtal_value, re.IGNORECASE)
        if load_match:
            target_load_pF = float(load_match.group(1))
            target_load_source = "parsed_from_value"
        # Frequency-based defaults — use granular lookup table
        if target_load_pF is None:
            freq = xtal_entry.get("frequency")
            if freq:
                target_load_pF = _crystal_default_cl(freq)
                if target_load_pF is not None:
                    target_load_source = "frequency_default"
        xtal_entry["target_load_pF"] = target_load_pF
        xtal_entry["target_load_source"] = target_load_source
        if target_load_pF and "effective_load_pF" in xtal_entry:
            error_pct = (xtal_entry["effective_load_pF"] - target_load_pF) / target_load_pF * 100
            xtal_entry["load_cap_error_pct"] = round(error_pct, 1)
            if target_load_source == "frequency_default":
                # Target is a statistical default, not from the actual crystal
                # datasheet. Don't report as out_of_spec — the default itself
                # may be wrong for this specific crystal part.
                if abs(error_pct) <= 10:
                    xtal_entry["load_cap_status"] = "ok"
                else:
                    xtal_entry["load_cap_status"] = "unverified"
            else:
                # Target is parsed from the crystal value string or datasheet —
                # high confidence, use normal thresholds.
                if abs(error_pct) <= 10:
                    xtal_entry["load_cap_status"] = "ok"
                elif abs(error_pct) <= 25:
                    xtal_entry["load_cap_status"] = "marginal"
                else:
                    xtal_entry["load_cap_status"] = "out_of_spec"

        _xtal_freq = xtal_entry.get("frequency")
        _xtal_freq_str = f" at {_xtal_freq}Hz" if _xtal_freq else ""
        xtal_entry["detector"] = "detect_crystal_circuits"
        xtal_entry["rule_id"] = "XL-DET"
        xtal_entry["category"] = "timing"
        xtal_entry["severity"] = "info"
        xtal_entry["confidence"] = "deterministic"
        xtal_entry["evidence_source"] = "topology"
        xtal_entry["summary"] = f"Crystal {xtal['reference']}{_xtal_freq_str}"
        xtal_entry["description"] = "Crystal oscillator circuit detected"
        xtal_entry["components"] = [xtal["reference"]]
        xtal_entry["nets"] = []
        xtal_entry["pins"] = []
        xtal_entry["recommendation"] = ""
        xtal_entry["report_context"] = {"section": "Timing", "impact": "", "standard_ref": ""}
        xtal_entry["provenance"] = make_provenance(
            "xtal_passive_caps", "deterministic",
            [xtal["reference"]] + [lc["ref"] for lc in load_caps])

        crystal_circuits.append(xtal_entry)

    # Detect active oscillators (TCXO, VCXO, MEMS, etc.)
    _osc_keywords = ("oscillator", "tcxo", "vcxo", "mems_osc", "sit2", "sit8",
                     "dsc6", "dsc1", "sg-", "asfl", "asco", "asdm", "fox",
                     "ecs-", "abracon")
    for comp in ctx.components:
        if comp["type"] == "oscillator":
            pass  # always include
        elif comp["type"] in ("crystal", "ic"):
            val_lower = comp.get("value", "").lower()
            lib_lower = comp.get("lib_id", "").lower()
            if not any(kw in val_lower or kw in lib_lower for kw in _osc_keywords):
                continue
            # Exclude RF/analog ICs that happen to match oscillator keywords
            _osc_exclude = ("switch", "mux", "balun", "filter", "amplifier", "lna",
                            "driver", "mixer", "attenuator", "diplexer", "splitter",
                            "spdt", "sp3t", "sp4t", "74lvc", "74hc")
            if any(kw in val_lower or kw in lib_lower for kw in _osc_exclude):
                continue
            # Skip if already detected as a passive crystal
            if any(xc["reference"] == comp["reference"] for xc in crystal_circuits):
                continue
        else:
            continue

        ref = comp["reference"]
        # Find output net (clock output pin)
        out_net = None
        vcc_net = None
        for pin in comp.get("pins", []):
            net_name, _ = ctx.pin_net.get((ref, pin["number"]), (None, None))
            if not net_name:
                continue
            pname = pin.get("name", "").upper()
            if pname in ("OUT", "OUTPUT", "CLK", "CLKOUT"):
                out_net = net_name
            elif ctx.is_power_net(net_name) and not ctx.is_ground(net_name):
                vcc_net = net_name
        # If no named output pin, check for non-power non-ground pins
        if not out_net:
            for pin in comp.get("pins", []):
                net_name, _ = ctx.pin_net.get((ref, pin["number"]), (None, None))
                if net_name and not ctx.is_power_net(net_name) and not ctx.is_ground(net_name):
                    out_net = net_name
                    break

        _osc_freq = _parse_crystal_frequency(comp.get("value", ""))
        _osc_freq_str = f" at {_osc_freq}Hz" if _osc_freq else ""
        crystal_circuits.append({
            "reference": ref,
            "value": comp.get("value", ""),
            "frequency": _osc_freq,
            "type": "active_oscillator",
            "output_net": out_net,
            "load_caps": [],
            "detector": "detect_crystal_circuits",
            "rule_id": "XL-DET",
            "category": "timing",
            "severity": "info",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "summary": f"Crystal {ref}{_osc_freq_str}",
            "description": "Active oscillator detected",
            "components": [ref],
            "nets": [],
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "Timing", "impact": "", "standard_ref": ""},
            "provenance": make_provenance("xtal_active_oscillator", "deterministic", [ref]),
        })

    # IC pin-based crystal detection: find ICs with crystal-related pin names
    # (XTAL_IN/XTAL_OUT, XI/XO, OSC_IN/OSC_OUT) whose connected nets have small
    # caps (5-50pF) to ground.  Reports crystal circuits even without a classified
    # crystal component (common when crystal is in a generic footprint).
    _xtal_pin_re = re.compile(
        r'^(XTAL|OSC|XI|XO|XTAL_IN|XTAL_OUT|XTAL1|XTAL2|'
        r'OSC_IN|OSC_OUT|OSC1|OSC2|OSC32_IN|OSC32_OUT|'
        r'OSCI|OSCO|X_IN|X_OUT|XIN|XOUT|XT1|XT2|'
        r'XTALIN|XTALOUT|XTAL_P|XTAL_N|'
        r'RTC_XTAL|RTC_XI|RTC_XO|RTC32K_XP|RTC32K_XN)$', re.IGNORECASE)
    detected_refs = {xc["reference"] for xc in crystal_circuits}
    for ic in ctx.components:
        if ic["type"] != "ic":
            continue
        # Collect crystal-related pin nets for this IC
        xtal_pin_nets = []
        for pin in ic.get("pins", []):
            pname = pin.get("name", "")
            if _xtal_pin_re.match(pname):
                net_name, _ = ctx.pin_net.get((ic["reference"], pin["number"]), (None, None))
                if net_name and not ctx.is_power_net(net_name) and not ctx.is_ground(net_name):
                    xtal_pin_nets.append((pname, net_name))
        if len(xtal_pin_nets) < 2:
            continue
        # Check if these nets have small caps to ground (load caps)
        load_caps = []
        for _pname, net_name in xtal_pin_nets:
            if net_name not in ctx.nets:
                continue
            for p in ctx.nets[net_name]["pins"]:
                comp = ctx.comp_lookup.get(p["component"])
                if not comp or comp["type"] != "capacitor":
                    continue
                cap_ref = p["component"]
                if cap_ref in detected_refs:
                    continue
                cap_val = ctx.parsed_values.get(cap_ref)
                if cap_val and 5e-12 <= cap_val <= 50e-12:
                    cn1, cn2 = ctx.get_two_pin_nets(cap_ref)
                    other = cn2 if cn1 == net_name else cn1
                    if ctx.is_ground(other):
                        load_caps.append({
                            "ref": cap_ref,
                            "value": comp["value"],
                            "farads": cap_val,
                            "net": net_name,
                        })
        if len(load_caps) >= 2:
            # Check if any crystal component already covers these nets
            cap_nets = {lc["net"] for lc in load_caps}
            already_covered = False
            for xc in crystal_circuits:
                if any(lc["net"] in cap_nets for lc in xc.get("load_caps", [])):
                    already_covered = True
                    break
            if not already_covered:
                # Look for a feedback resistor bridging the two crystal nets
                fb_resistor = None
                net_list = list(cap_nets)
                if len(net_list) >= 2:
                    for r in ctx.components:
                        if r["type"] != "resistor":
                            continue
                        rn1, rn2 = ctx.get_two_pin_nets(r["reference"])
                        if rn1 in cap_nets and rn2 in cap_nets and rn1 != rn2:
                            rv = ctx.parsed_values.get(r["reference"])
                            if rv and rv >= 100e3:  # 100k+ = feedback resistor
                                fb_resistor = r["reference"]
                                break

                entry = {
                    "reference": ic["reference"],
                    "value": ic.get("value", ""),
                    "type": "ic_crystal_pins",
                    "ic_reference": ic["reference"],
                    "load_caps": load_caps,
                }
                if fb_resistor:
                    entry["feedback_resistor"] = fb_resistor
                if len(load_caps) >= 2:
                    c1 = load_caps[0]["farads"]
                    c2 = load_caps[1]["farads"]
                    cl_eff = (c1 * c2) / (c1 + c2) + 3e-12
                    entry["effective_load_pF"] = round(cl_eff * 1e12, 2)
                entry["detector"] = "detect_crystal_circuits"
                entry["rule_id"] = "XL-DET"
                entry["category"] = "timing"
                entry["severity"] = "info"
                entry["confidence"] = "deterministic"
                entry["evidence_source"] = "topology"
                entry["summary"] = f"Crystal {ic['reference']}"
                entry["description"] = "Crystal circuit inferred from IC XTAL pins"
                entry["components"] = [ic["reference"]]
                entry["nets"] = []
                entry["pins"] = []
                entry["recommendation"] = ""
                entry["report_context"] = {"section": "Timing", "impact": "", "standard_ref": ""}
                entry["provenance"] = make_provenance(
                    "xtal_ic_pin_inferred", "heuristic",
                    [ic["reference"]] + [lc["ref"] for lc in load_caps])
                crystal_circuits.append(entry)

    return crystal_circuits


def detect_decoupling(ctx: AnalysisContext) -> list[dict]:
    """Detect decoupling capacitors per power rail."""
    # EQ-069: f_SRF = 1/(2π√(ESL×C)) (decoupling SRF)
    decoupling_analysis: list[dict] = []

    # For each power rail, compute total decoupling capacitance and frequency coverage
    power_nets = {}
    for net_name, net_info in ctx.nets.items():
        if net_name.startswith("__unnamed_"):
            continue
        if ctx.is_ground(net_name):
            continue
        if ctx.is_power_net(net_name):
            power_nets[net_name] = net_info

    for rail_name, rail_info in power_nets.items():
        rail_caps = []
        for p in rail_info["pins"]:
            comp = ctx.comp_lookup.get(p["component"])
            if comp and comp["type"] == "capacitor":
                cap_val = ctx.parsed_values.get(p["component"])
                if cap_val:
                    # Check if other pin goes to ground
                    c_n1, c_n2 = ctx.get_two_pin_nets(p["component"])
                    other = c_n2 if c_n1 == rail_name else c_n1
                    if ctx.is_ground(other):
                        self_resonant = 1.0 / (2.0 * math.pi * math.sqrt(1e-9 * cap_val))  # ~1nH ESL estimate
                        rail_caps.append({
                            "ref": p["component"],
                            "value": comp["value"],
                            "farads": cap_val,
                            "self_resonant_hz": round(self_resonant, 0),
                        })

        if rail_caps:
            total_cap = sum(c["farads"] for c in rail_caps)
            decoupling_analysis.append({
                "rail": rail_name,
                "capacitors": rail_caps,
                "total_capacitance_uF": round(total_cap * 1e6, 3),
                "cap_count": len(rail_caps),
                "detector": "detect_decoupling",
                "rule_id": "DC-DET",
                "category": "decoupling",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Decoupling on {rail_name}",
                "description": f"Decoupling capacitors on power rail {rail_name}",
                "components": [c["ref"] for c in rail_caps],
                "nets": [],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Decoupling", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("decoup_cap_near_ic", "deterministic", [c["ref"] for c in rail_caps]),
            })
    return decoupling_analysis


def detect_current_sense(ctx: AnalysisContext) -> list[dict]:
    """Detect current sense circuits."""
    current_sense: list[dict] = []
    shunt_candidates = [
        c for c in ctx.components
        if c["type"] == "resistor" and c["reference"] in ctx.parsed_values
        and 0 < ctx.parsed_values[c["reference"]] <= 0.5
    ]

    _SENSE_PIN_PREFIXES = frozenset({
        "CS", "CSP", "CSN", "ISNS", "ISENSE", "IMON", "IOUT",
        "SEN", "SENSE", "VSENSE", "VSEN", "VS", "INP", "INN",
        "IS", "IAVG", "ISET",
    })
    _SENSE_IC_KEYWORDS = frozenset({
        "ina", "acs7", "ad8210", "ad8217", "ad8218", "max9938",
        "max4080", "max4081", "max471", "ltc6101", "ltc6102",
        "ltc6103", "ltc4151", "ina226", "ina233", "ina180",
        "ina181", "ina190", "ina199", "ina200", "ina210",
        "ina240", "ina250", "ina260", "ina300", "ina381",
        "pam2401", "zxct", "acs71", "acs72", "asc",
    })
    # KH-081/KH-113: IC families that are never current sense amplifiers
    _SENSE_IC_EXCLUDE = frozenset({
        # Ethernet PHY / RJ45 / MagJack
        "w5500", "w5100", "w5200", "ksz", "dp83", "lan87", "lan91",
        "hr911", "rj45", "magjack", "enc28j", "8p8c", "hr601", "arjm",
        # RS-485/RS-232/UART transceivers
        "lt178", "max48", "sn65hvd", "st348", "rs485", "rs232",
        "adm281", "adm485", "adm491", "sp338", "sp339", "isl3", "iso15",
        "max23", "max31", "max32",
    })

    for shunt in shunt_candidates:
        # Support both 2-pin and 4-pin Kelvin shunts (R_Shunt: pins 1,4=current; 2,3=sense)
        sense_n1, sense_n2 = None, None
        # Check for 4-pin Kelvin first (pins 1,4=current path; 2,3=sense)
        n1, _ = ctx.pin_net.get((shunt["reference"], "1"), (None, None))
        n4, _ = ctx.pin_net.get((shunt["reference"], "4"), (None, None))
        n3, _ = ctx.pin_net.get((shunt["reference"], "3"), (None, None))
        if n1 and n4 and n3:
            # 4-pin Kelvin shunt
            n2, _ = ctx.pin_net.get((shunt["reference"], "2"), (None, None))
            s_n1, s_n2 = n1, n4
            sense_n1, sense_n2 = n2, n3
        else:
            s_n1, s_n2 = ctx.get_two_pin_nets(shunt["reference"])
            if not s_n1 or not s_n2:
                continue
        if s_n1 == s_n2:
            continue
        # Skip if both nets are power/ground (bulk decoupling, not sensing)
        s1_pwr_or_gnd = ctx.is_ground(s_n1) or ctx.is_power_net(s_n1)
        s2_pwr_or_gnd = ctx.is_ground(s_n2) or ctx.is_power_net(s_n2)
        if s1_pwr_or_gnd and s2_pwr_or_gnd:
            continue

        shunt_ohms = ctx.parsed_values[shunt["reference"]]

        # Find ICs connected to BOTH sides of the shunt.
        # Ground-net exclusion: GND connects to every IC on the board, so it
        # can't be used for "IC on both sides" matching.  When one side of the
        # shunt is GND, skip GND-side component collection entirely and instead
        # match only ICs on the non-GND side that are known sense parts or have
        # sense-related pin names on the shunt nets.

        # Treat power nets the same as GND — they connect to many ICs
        # through power pins and would cause the same false positive flood.
        side1_is_pwr = ctx.is_ground(s_n1) or ctx.is_power_net(s_n1)
        side2_is_pwr = ctx.is_ground(s_n2) or ctx.is_power_net(s_n2)
        has_pwr_side = side1_is_pwr or side2_is_pwr

        comps_on_n1 = set()
        comps_on_n2 = set()
        check_nets_1 = [s_n1] + ([sense_n1] if sense_n1 else [])
        check_nets_2 = [s_n2] + ([sense_n2] if sense_n2 else [])

        # Collect components on each side (skip power/GND side entirely)
        if not side1_is_pwr:
            for nn in check_nets_1:
                if nn in ctx.nets:
                    for p in ctx.nets[nn]["pins"]:
                        if p["component"] != shunt["reference"]:
                            comps_on_n1.add(p["component"])
        if not side2_is_pwr:
            for nn in check_nets_2:
                if nn in ctx.nets:
                    for p in ctx.nets[nn]["pins"]:
                        if p["component"] != shunt["reference"]:
                            comps_on_n2.add(p["component"])

        if has_pwr_side:
            # One side is a power/GND rail: use only the non-power side's
            # components.  Filter to ICs that are plausible current sense
            # monitors: either by part name or by having sense-related pin
            # names on the shunt nets.
            non_pwr_comps = comps_on_n1 if not side1_is_pwr else comps_on_n2
            non_pwr_nets = check_nets_1 if not side1_is_pwr else check_nets_2
            sense_ics_set = set()
            for cref in non_pwr_comps:
                ic_comp = ctx.comp_lookup.get(cref)
                if not ic_comp or ic_comp["type"] != "ic":
                    continue
                # Check if part is a known sense IC
                val_lower = (ic_comp.get("value", "") + " " + ic_comp.get("lib_id", "")).lower()
                # KH-081/KH-113: Skip excluded IC families
                if any(kw in val_lower for kw in _SENSE_IC_EXCLUDE):
                    continue
                if any(kw in val_lower for kw in _SENSE_IC_KEYWORDS):
                    sense_ics_set.add(cref)
                    continue
                # Check if the IC's pin on this net has a sense-related name
                for nn in non_pwr_nets:
                    if nn not in ctx.nets:
                        continue
                    for p in ctx.nets[nn]["pins"]:
                        if p["component"] == cref:
                            pn = p.get("pin_name", "").upper().rstrip("0123456789+-")
                            if pn in _SENSE_PIN_PREFIXES:
                                sense_ics_set.add(cref)
            sense_ics = sense_ics_set
        else:
            # Neither side is GND: use original "IC on both sides" algorithm
            sense_ics = comps_on_n1 & comps_on_n2
            # 1-hop: if no IC on both sides directly, look through filter resistors
            # (e.g., shunt -> R_filter -> sense IC is a common BMS pattern)
            if not any(ctx.comp_lookup.get(c, {}).get("type") == "ic" for c in sense_ics):
                for nn in check_nets_1:
                    if nn not in ctx.nets:
                        continue
                    for p in ctx.nets[nn]["pins"]:
                        r_comp = ctx.comp_lookup.get(p["component"])
                        if r_comp and r_comp["type"] == "resistor" and p["component"] != shunt["reference"]:
                            r_other = ctx.get_two_pin_nets(p["component"])
                            if r_other[0] and r_other[1]:
                                hop_net = r_other[1] if r_other[0] == nn else r_other[0]
                                if hop_net in ctx.nets:
                                    for hp in ctx.nets[hop_net]["pins"]:
                                        comps_on_n1.add(hp["component"])
                for nn in check_nets_2:
                    if nn not in ctx.nets:
                        continue
                    for p in ctx.nets[nn]["pins"]:
                        r_comp = ctx.comp_lookup.get(p["component"])
                        if r_comp and r_comp["type"] == "resistor" and p["component"] != shunt["reference"]:
                            r_other = ctx.get_two_pin_nets(p["component"])
                            if r_other[0] and r_other[1]:
                                hop_net = r_other[1] if r_other[0] == nn else r_other[0]
                                if hop_net in ctx.nets:
                                    for hp in ctx.nets[hop_net]["pins"]:
                                        comps_on_n2.add(hp["component"])
                sense_ics = comps_on_n1 & comps_on_n2
        for ic_ref in sense_ics:
            ic_comp = ctx.comp_lookup.get(ic_ref)
            if not ic_comp:
                continue
            # Only consider ICs (sense amplifiers, MCUs with ADC)
            if ic_comp["type"] not in ("ic",):
                continue

            current_sense.append({
                "shunt": {
                    "ref": shunt["reference"],
                    "value": shunt["value"],
                    "ohms": shunt_ohms,
                },
                "sense_ic": {
                    "ref": ic_ref,
                    "value": ic_comp.get("value", ""),
                    "type": ic_comp.get("type", ""),
                },
                "high_net": s_n1,
                "low_net": s_n2,
                "max_current_50mV_A": round(0.05 / shunt_ohms, 3) if shunt_ohms > 0 else None,
                "max_current_100mV_A": round(0.1 / shunt_ohms, 3) if shunt_ohms > 0 else None,
                "detector": "detect_current_sense",
                "rule_id": "CS-DET",
                "category": "current_measurement",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Current sense {shunt['reference']}",
                "description": "Current sense shunt with amplifier IC detected",
                "provenance": make_provenance("cs_ic_differential", "deterministic", [shunt["reference"], ic_ref]),
                "components": [shunt["reference"], ic_ref],
                "nets": [],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Current Measurement", "impact": "", "standard_ref": ""},
            })
    # Second pass: detect shunts with IC-integrated current sense amplifiers.
    # These ICs have sense pins (CSA, SEN, SNS, ISENSE, IMON, CSP, CSN, SH)
    # but weren't caught by the first pass because they may not be on both sides.
    matched_shunts = {entry["shunt"]["ref"] for entry in current_sense}
    _integrated_csa_pins = frozenset({
        "CSA", "CSB", "SEN", "SENP", "SENN", "SNS", "SNSP", "SNSN",
        "ISENSE", "IMON", "IOUT", "CSP", "CSN", "CS+", "CS-",
        "SH", "SHP", "SHN", "ISENP", "ISENN",
    })

    for shunt in shunt_candidates:
        if shunt["reference"] in matched_shunts:
            continue
        shunt_ohms = ctx.parsed_values.get(shunt["reference"])
        if not shunt_ohms or shunt_ohms > 1.0:
            continue

        s_n1, s_n2 = ctx.get_two_pin_nets(shunt["reference"])
        if not s_n1 or not s_n2 or s_n1 == s_n2:
            continue

        # Check each side's net for IC pins with CSA-related names
        for net_name in (s_n1, s_n2):
            if net_name not in ctx.nets:
                continue
            for p in ctx.nets[net_name]["pins"]:
                ic_comp = ctx.comp_lookup.get(p["component"])
                if not ic_comp or ic_comp["type"] != "ic":
                    continue
                # KH-081/KH-113: Skip excluded IC families
                _val_lower2 = (ic_comp.get("value", "") + " " + ic_comp.get("lib_id", "")).lower()
                if any(kw in _val_lower2 for kw in _SENSE_IC_EXCLUDE):
                    continue
                pn = p.get("pin_name", "").upper().rstrip("0123456789").rstrip("_")
                if pn in _integrated_csa_pins:
                    current_sense.append({
                        "shunt": {
                            "ref": shunt["reference"],
                            "value": shunt["value"],
                            "ohms": shunt_ohms,
                        },
                        "sense_ic": {
                            "ref": p["component"],
                            "value": ic_comp.get("value", ""),
                            "type": "integrated_csa",
                        },
                        "high_net": s_n1,
                        "low_net": s_n2,
                        "max_current_50mV_A": round(0.05 / shunt_ohms, 3) if shunt_ohms > 0 else None,
                        "max_current_100mV_A": round(0.1 / shunt_ohms, 3) if shunt_ohms > 0 else None,
                        "detector": "detect_current_sense",
                        "rule_id": "CS-DET",
                        "category": "current_measurement",
                        "severity": "info",
                        "confidence": "deterministic",
                        "evidence_source": "topology",
                        "summary": f"Current sense {shunt['reference']}",
                        "description": "Current sense shunt with integrated CSA detected",
                        "components": [shunt["reference"], p["component"]],
                        "nets": [],
                        "pins": [],
                        "recommendation": "",
                        "report_context": {"section": "Current Measurement", "impact": "", "standard_ref": ""},
                        "provenance": make_provenance("cs_integrated_pin", "heuristic", [shunt["reference"], p["component"]]),
                    })
                    matched_shunts.add(shunt["reference"])
                    break
            if shunt["reference"] in matched_shunts:
                break

    return current_sense


def _infer_rail_voltage(net_name):
    """Infer voltage from a power rail net name. Returns float or None."""
    if not net_name:
        return None
    name = net_name.upper().strip()
    # VxPy notation: V3P3 → 3.3, V1P8 → 1.8
    m = re.match(r'V(\d+)P(\d+)', name)
    if m:
        return float(f"{m.group(1)}.{m.group(2)}")
    m = re.match(r'[+]?(\d+)V(\d+)', name)
    if m:
        return float(f"{m.group(1)}.{m.group(2)}")
    m = re.match(r'[+]?(\d+\.?\d*)V', name)
    if m:
        return float(m.group(1))
    if "VBUS" in name or "USB" in name:
        return 5.0
    if "VBAT" in name:
        return 3.7
    return None


def detect_power_regulators(ctx: AnalysisContext, voltage_dividers: list[dict]) -> list[dict]:
    """Detect power regulator topology. Takes voltage_dividers for feedback matching."""
    power_regulators: list[dict] = []

    # KH-148: Deduplicate multi-unit ICs
    for ic in get_unique_ics(ctx):
        ref = ic["reference"]

        # KH-089: Skip components with no mapped pins (title blocks, graphics)
        # KH-124: Allow keyword-matched PMICs through even without pins (legacy format)
        _no_pins = not ic.get("pins")

        # KH-089: Skip known non-regulator IC families
        _lib_val_check = (ic.get("lib_id", "") + " " + ic.get("value", "")).lower()
        _non_reg_exclude = ("eeprom", "flash", "spi_flash", "rtc", "uart",
                            "usb_uart", "buffer", "logic_", "encoder",
                            "w25q", "at24c", "24c0", "pcf85", "ht42b", "ch340",
                            "cp210", "ft232", "74lvc", "74hc",
                            # KH-100: WiFi/BT modules with filter inductors
                            "ap6212", "ap6236", "ap6256", "esp32", "esp8266",
                            "cyw43", "wl18",
                            # KH-226: Dev board modules (not regulators)
                            "nucleo", "arduino", "raspberry", "teensy",
                            "feather", "pico")
        if any(k in _lib_val_check for k in _non_reg_exclude):
            continue

        ic_pins = {}  # pin_name -> (net_name, pin_number)
        for pin_num, (net_name, _) in ctx.ref_pins.get(ref, {}).items():
            pin_name = ""
            if net_name and net_name in ctx.nets:
                for p in ctx.nets[net_name]["pins"]:
                    if p["component"] == ref and p["pin_number"] == pin_num:
                        pin_name = p.get("pin_name", "").upper()
                        break
            ic_pins[pin_name] = (net_name, pin_num)

        # Look for regulator pin patterns
        fb_pin = None
        sw_pin = None
        en_pin = None
        vin_pin = None
        vout_pin = None
        boot_pin = None

        for pname, (net, pnum) in ic_pins.items():
            # Use startswith for pins that may have numeric suffixes (FB1, SW2, etc.)
            pn_base = pname.rstrip("0123456789").rstrip("_")  # Strip trailing digits and underscores (FB_1→FB)
            # Split composite pin names like "FB/VOUT" into parts
            pn_parts = {p.strip() for p in pname.split("/")} | {pn_base}
            if pn_parts & {"FB", "VFB", "ADJ", "VADJ"}:
                if not fb_pin:
                    fb_pin = (pname, net)
                # Composite names like "FB/VOUT" also set vout_pin
                if not vout_pin and pn_parts & {"VOUT", "VO", "OUT", "OUTPUT"}:
                    vout_pin = (pname, net)
            elif pn_parts & {"SW", "PH", "LX"}:
                if not sw_pin:
                    sw_pin = (pname, net)
            elif pname in ("EN", "ENABLE", "ON", "~{SHDN}", "SHDN", "~{EN}") or \
                 (pn_base == "EN" and len(pname) <= 4):
                en_pin = (pname, net)
            elif pn_parts & {"VIN", "VI", "IN", "PVIN", "AVIN", "INPUT"}:
                vin_pin = (pname, net)
            elif pn_parts & {"VOUT", "VO", "OUT", "OUTPUT"}:
                vout_pin = (pname, net)
            elif pn_parts & {"BOOT", "BST", "BOOTSTRAP", "CBST"}:
                boot_pin = (pname, net)

        if not fb_pin and not sw_pin and not vout_pin:
            # KH-124: For pin-less ICs (legacy format), check keywords before
            # giving up — PMICs like AXP803 won't have pin data
            if not _no_pins:
                continue  # Not a regulator
            _kw_check = (ic.get("lib_id", "") + " " + ic.get("value", "")).lower()
            _kw_pmic = ("regulator", "ldo", "buck", "boost", "converter", "pmic",
                        "axp", "mt36", "dd40", "tplp", "hx630", "ip51",
                        "ams1117", "lm317", "lm78", "lm79", "tps5", "tps6")
            if not any(k in _kw_check for k in _kw_pmic):
                continue
            # Add as minimal keyword-only entry
            power_regulators.append({
                "ref": ref,
                "value": ic.get("value", ""),
                "lib_id": ic.get("lib_id", ""),
                "topology": "unknown",
                "input_rail": None,
                "output_rail": None,
                "estimated_vout": None,
                "feedback_divider": None,
                "inductor": None,
                "detector": "detect_power_regulators",
                "rule_id": "PR-DET",
                "category": "power_management",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Regulator {ref} unknown",
                "description": "Power regulator detected by keyword match (no pin data)",
                "components": [ref],
                "nets": [],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Power Management", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("reg_keyword", "heuristic", [ref]),
            })
            continue

        # Early lib_id check
        lib_id_raw = ic.get("lib_id", "")
        lib_part_name = lib_id_raw.split(":")[-1] if ":" in lib_id_raw else ""
        desc_lower = ic.get("description", "").lower()
        lib_val_lower = (lib_id_raw + " " + ic.get("value", "") + " " + lib_part_name).lower()
        reg_lib_keywords = ("regulator", "regul", "ldo", "vreg", "buck", "boost",
                           "converter", "dc-dc", "dc_dc", "linear_regulator",
                           "switching_regulator",
                           "ams1117", "lm317", "lm78", "lm79", "ld1117", "ld33",
                           "ap6", "tps5", "tps6", "tlv7", "rt5", "mp1", "mp2",
                           "sy8", "max150", "max170", "ncp1", "xc6", "mcp170",
                           "mic29", "mic55", "ap2112", "ap2210", "ap73",
                           "ncv4", "lm26", "lm11", "78xx",
                           "79xx", "lt308", "lt36", "ltc36", "lt86", "ltc34",
                           # KH-118: Asian manufacturer LDOs
                           "tplp", "hx630",
                           # KH-124: PMICs and boost converters
                           "axp", "mt36", "pmic", "dd40", "ip51",
                           )
        has_reg_keyword = (any(k in lib_val_lower for k in reg_lib_keywords) or
                          any(k in desc_lower for k in ("regulator", "ldo", "vreg",
                                                        "voltage regulator")))

        # Exclude RF amplifiers/LNAs that have VIN/VOUT but aren't regulators
        _rf_exclude = ("lna", "mmic", "mga-", "bga-", "bgb7", "trf37",
                       "sga-", "tqp3", "sky67", "gali-", "bfp7", "bfr5")
        if any(k in lib_val_lower for k in _rf_exclude):
            continue

        # Exclude power multiplexers/load switches/ideal diode controllers
        _power_mux_exclude = ("power_mux", "load_switch", "tps211", "tps212",
                              "tps229", "tps205",  # KH-219: load switches
                              "ltc441", "ideal_diode",
                              # KH-108: Ideal diode OR controllers
                              "lm6620", "lm6610", "ltc435", "ltc430")
        if any(k in lib_val_lower for k in _power_mux_exclude):
            continue
        # KH-219: Exclude components with load/power switch descriptions
        if any(k in desc_lower for k in ("load switch", "power switch", "power distribution switch")):
            continue

        # Exclude op-amps, instrumentation amps, and ADCs with FB-like pins
        _opamp_adc_exclude = ("ada48", "ad8", "opa", "lm358", "lm324",
                              "lmv3", "tlv9", "mcp60", "mcp61",
                              "hx711", "ads1", "mcp3", "max11",
                              "ina21", "ina22", "ina23",
                              "comparator", "op_amp", "opamp")
        if any(k in lib_val_lower for k in _opamp_adc_exclude):
            continue

        if not fb_pin and not boot_pin:
            if not sw_pin and not has_reg_keyword:
                # Only VOUT pin, no regulator keywords → check if VIN+VOUT
                # both connect to distinct power nets (custom-lib LDOs like TC1185)
                if vin_pin and vout_pin:
                    in_net = vin_pin[1]
                    out_net = vout_pin[1]
                    if not (ctx.is_power_net(in_net) and ctx.is_power_net(out_net)
                            and in_net != out_net):
                        continue
                else:
                    continue
            if sw_pin and not has_reg_keyword:
                # SW pin but check if inductor is connected
                sw_net_name = sw_pin[1]
                sw_has_inductor = bool(ctx.nq and ctx.nq.inductors_on_net(sw_net_name, exclude_ref=ref))
                if not sw_has_inductor and ctx.nq:
                    # Try 1-hop through connectors/hierarchical pins
                    for other_net in ctx.nq.trace_through(sw_net_name, ref):
                        if ctx.nq.inductors_on_net(other_net):
                            sw_has_inductor = True
                            break
                if not sw_has_inductor:
                    continue

        reg_info = {
            "ref": ref,
            "value": ic["value"],
            "lib_id": ic.get("lib_id", ""),
        }

        # Determine topology
        if sw_pin:
            # Check if SW pin connects to an inductor
            sw_net = sw_pin[1]
            has_inductor = False
            inductor_ref = None
            inductors = ctx.nq.inductors_on_net(sw_net, exclude_ref=ref) if ctx.nq else []
            if not inductors and ctx.nq:
                # Try 1-hop through connectors for modular designs
                for other_net in ctx.nq.trace_through(sw_net, ref):
                    inductors = ctx.nq.inductors_on_net(other_net)
                    if inductors:
                        break
            if inductors:
                has_inductor = True
                inductor_ref = inductors[0]["reference"]
            if has_inductor:
                reg_info["topology"] = "switching"
                reg_info["inductor"] = inductor_ref
                reg_info["sw_net"] = sw_net
                if boot_pin:
                    reg_info["has_bootstrap"] = True
                # KH-084/KH-087: Trace through inductor to find output rail
                if inductor_ref and not vout_pin:
                    ind_n1, ind_n2 = ctx.get_two_pin_nets(inductor_ref)
                    out_rail = ind_n2 if ind_n1 == sw_net else ind_n1
                    if out_rail and out_rail != sw_net:
                        reg_info["output_rail"] = out_rail
            else:
                reg_info["topology"] = "switching"  # SW pin but no inductor found
        elif vout_pin and not sw_pin:
            # Check if description/lib_id suggests a switching regulator whose
            # SW pin wasn't found (e.g., pin in different unit or unusual name)
            _switching_kw = ("buck", "boost", "switching", "step-down", "step-up",
                             "step down", "step up", "dc-dc", "dc_dc", "smps",
                             "converter", "synchronous")
            if any(k in desc_lower for k in _switching_kw) or \
               any(k in lib_val_lower for k in _switching_kw):
                reg_info["topology"] = "switching"
            elif _match_known_switching(ic.get("value", ""), ic.get("lib_id", "")):
                reg_info["topology"] = "switching"
            else:
                reg_info["topology"] = "LDO"
            # KH-225: Charge pumps — voltage converters, not LDOs
            _charge_pump_kw = ("charge_pump", "charge pump", "voltage inverter",
                               "voltage converter", "switched capacitor")
            if any(k in desc_lower for k in _charge_pump_kw) or \
               any(k in lib_val_lower for k in ("lm2664", "max660", "icl7660",
                                                  "tc7660", "ltc1044", "ltc3261",
                                                  "ltc1144")):
                reg_info["topology"] = "charge_pump"
        elif fb_pin and not sw_pin:
            reg_info["topology"] = "unknown"

        # Check if this is a complex IC with an internal regulator rather than
        # a dedicated regulator.  If < 20% of pins are regulator-related, flag it.
        total_pins = len(ic.get("pins", []))
        reg_pin_count = sum(1 for pn in ic_pins if pn in (
            "VIN", "VOUT", "VO", "OUT", "FB", "VFB", "ADJ", "SW", "PH", "LX",
            "EN", "ENABLE", "BST", "BOOT", "PGOOD", "PG", "SS", "COMP",
            "INPUT", "OUTPUT",
        ))
        if total_pins > 10 and reg_pin_count < total_pins * 0.2:
            reg_info["topology"] = "ic_with_internal_regulator"

        # Detect inverting topology from part name/description or output net name
        inverting_kw = ("invert", "inv_", "_inv", "negative output", "neg_out")
        is_inverting = any(k in lib_val_lower for k in inverting_kw) or \
                       any(k in desc_lower for k in inverting_kw)

        # Extract input/output rails
        if vin_pin:
            reg_info["input_rail"] = vin_pin[1]
        if vout_pin:
            reg_info["output_rail"] = vout_pin[1]
            # Also check if output rail name suggests negative voltage
            out_net_u = vout_pin[1].upper()
            if re.search(r'[-](\d)', out_net_u) or "NEG" in out_net_u or out_net_u.startswith("-"):
                is_inverting = True
        if is_inverting:
            reg_info["inverting"] = True

        # KH-104: Sanity check — power rails should never be GND
        if reg_info.get("input_rail") and ctx.is_ground(reg_info["input_rail"]):
            reg_info["input_rail"] = None
        if reg_info.get("output_rail") and ctx.is_ground(reg_info["output_rail"]):
            reg_info["output_rail"] = None

        # KH-087: Trace output rail through inductor (retry after sanitization)
        if reg_info.get("topology") == "switching" and not reg_info.get("output_rail") and reg_info.get("inductor"):
            ind_ref = reg_info["inductor"]
            ind_n1, ind_n2 = ctx.get_two_pin_nets(ind_ref)
            sw_net_2 = sw_pin[1] if sw_pin else None
            out_rail = ind_n2 if ind_n1 == sw_net_2 else ind_n1
            if out_rail and not ctx.is_ground(out_rail):
                reg_info["output_rail"] = out_rail

        # KH-087: Trace input rail through ferrite bead
        if not reg_info.get("input_rail") and vin_pin:
            vin_net = vin_pin[1]
            if vin_net and vin_net in ctx.nets:
                for p in ctx.nets[vin_net]["pins"]:
                    fb_comp = ctx.comp_lookup.get(p["component"])
                    if (fb_comp and fb_comp["type"] in ("ferrite_bead", "inductor")
                            and p["component"] != reg_info.get("inductor")):
                        fb_n1, fb_n2 = ctx.get_two_pin_nets(p["component"])
                        other = fb_n2 if fb_n1 == vin_net else fb_n1
                        if other and ctx.is_power_net(other) and not ctx.is_ground(other):
                            reg_info["input_rail"] = other
                            break

        # Check for fixed-output regulator (voltage encoded in part number)
        fixed_vout, fixed_source = _lookup_regulator_vref(
            ic.get("value", ""), ic.get("lib_id", ""))
        if fixed_source == "fixed_suffix" and fixed_vout is not None:
            reg_info["estimated_vout"] = round(fixed_vout, 3)
            reg_info["vref_source"] = "fixed_suffix"
            reg_info["_estimated_vout_provenance"] = {
                "source": "fixed_suffix",
                "confidence": "deterministic",
            }
            if vout_pin:
                reg_info["output_rail"] = vout_pin[1]

        # Check feedback divider for output voltage estimation
        if fb_pin:
            fb_net = fb_pin[1]
            reg_info["fb_net"] = fb_net
            # Try part-specific Vref lookup first, fall back to heuristic sweep
            known_vref, vref_source = _lookup_regulator_vref(
                ic.get("value", ""), ic.get("lib_id", ""))
            # Skip feedback divider analysis for fixed-output parts
            if vref_source == "fixed_suffix":
                known_vref = None
            # Find matching voltage divider
            for vd in voltage_dividers:
                if vd["mid_net"] == fb_net:
                    ratio = vd["ratio"]
                    if known_vref is not None:
                        # Use the known Vref from the lookup table
                        v_out = known_vref / ratio if ratio > 0 else 0
                        if 0.5 < v_out < 60:
                            reg_info["estimated_vout"] = round(v_out, 3)
                            reg_info["_estimated_vout_provenance"] = {
                                "source": "divider_plus_" + reg_info.get("vref_source", "lookup"),
                                "confidence": "deterministic" if reg_info.get("vref_source") == "datasheet" else "heuristic",
                            }
                            reg_info["assumed_vref"] = known_vref
                            reg_info["vref_source"] = "lookup"
                            reg_info["feedback_divider"] = {
                                "r_top": {"ref": vd["r_top"]["ref"], "ohms": vd["r_top"]["ohms"], "value": vd["r_top"]["value"]},
                                "r_bottom": {"ref": vd["r_bottom"]["ref"], "ohms": vd["r_bottom"]["ohms"], "value": vd["r_bottom"]["value"]},
                                "ratio": ratio,
                            }
                    else:
                        # Heuristic: try common Vref values
                        for vref in [0.6, 0.8, 1.0, 1.22, 1.25]:
                            v_out = vref / ratio if ratio > 0 else 0
                            if 0.5 < v_out < 60:
                                reg_info["estimated_vout"] = round(v_out, 3)
                                reg_info["_estimated_vout_provenance"] = {
                                    "source": "divider_plus_" + reg_info.get("vref_source", "lookup"),
                                    "confidence": "deterministic" if reg_info.get("vref_source") == "datasheet" else "heuristic",
                                }
                                reg_info["assumed_vref"] = vref
                                reg_info["vref_source"] = "heuristic"
                                reg_info["feedback_divider"] = {
                                    "r_top": {"ref": vd["r_top"]["ref"], "ohms": vd["r_top"]["ohms"], "value": vd["r_top"]["value"]},
                                    "r_bottom": {"ref": vd["r_bottom"]["ref"], "ohms": vd["r_bottom"]["ohms"], "value": vd["r_bottom"]["value"]},
                                    "ratio": ratio,
                                }
                                break
                    break

        # KH-090: Fixed-output LDOs are never inverting
        if reg_info.get("inverting") and reg_info.get("topology") == "LDO" and not fb_pin:
            del reg_info["inverting"]

        # Negate Vout for inverting regulators
        if reg_info.get("inverting") and "estimated_vout" in reg_info:
            reg_info["estimated_vout"] = -abs(reg_info["estimated_vout"])

        # Estimate switching frequency for switching regulators
        if reg_info.get("topology") == "switching":
            sw_f = lookup_switching_freq(ic.get("value", ""))
            freq_source = "lookup_table" if sw_f else None
            if sw_f is None:
                # Try lib_id part name (after colon)
                lib_part = ic.get("lib_id", "").split(":")[-1] if ":" in ic.get("lib_id", "") else ""
                if lib_part:
                    sw_f = lookup_switching_freq(lib_part)
                    if sw_f:
                        freq_source = "lookup_table"
            if sw_f is None:
                sw_f = _default_switching_freq("buck")  # conservative default for switching
                freq_source = "topology_default"
            if sw_f is not None:
                reg_info["switching_frequency_hz"] = sw_f
                reg_info["freq_source"] = freq_source

        # Only add if we found meaningful regulator features
        is_regulator = False
        if fb_pin or sw_pin or boot_pin:
            is_regulator = True
        elif vin_pin or vout_pin:
            in_net = vin_pin[1] if vin_pin else ""
            out_net = vout_pin[1] if vout_pin else ""
            if ctx.is_power_net(in_net) or ctx.is_power_net(out_net):
                is_regulator = True
            if has_reg_keyword:
                is_regulator = True

        if is_regulator and any(k in reg_info for k in ("topology", "input_rail", "output_rail", "estimated_vout")):
            _reg_topo = reg_info.get("topology", "unknown")
            reg_info["detector"] = "detect_power_regulators"
            reg_info["rule_id"] = "PR-DET"
            reg_info["category"] = "power_management"
            reg_info["severity"] = "info"
            reg_info["confidence"] = "deterministic"
            reg_info["evidence_source"] = "topology"
            reg_info["summary"] = f"Regulator {ref} {_reg_topo}"
            reg_info["description"] = f"Power regulator ({_reg_topo}) detected"
            reg_info["components"] = [ref]
            reg_info["nets"] = []
            reg_info["pins"] = []
            reg_info["recommendation"] = ""
            reg_info["report_context"] = {"section": "Power Management", "impact": "", "standard_ref": ""}
            # Determine provenance evidence based on classification path
            if sw_pin and reg_info.get("inductor"):
                _prov_evidence = "reg_sw_pin_inductor"
                _prov_confidence = "deterministic"
            elif reg_info.get("vref_source") == "fixed_suffix":
                _prov_evidence = "reg_fixed_suffix"
                _prov_confidence = "deterministic"
            elif sw_pin:
                _prov_evidence = "reg_sw_pin_only"
                _prov_confidence = "heuristic"
            elif reg_info.get("feedback_divider"):
                _prov_evidence = "reg_divider_vref"
                _prov_confidence = "heuristic"
            elif has_reg_keyword:
                _prov_evidence = "reg_keyword"
                _prov_confidence = "heuristic"
            else:
                _prov_evidence = "reg_keyword"
                _prov_confidence = "heuristic"
            reg_info["provenance"] = make_provenance(_prov_evidence, _prov_confidence, [ref])
            power_regulators.append(reg_info)

    # KH-084: Cross-reference feedback dividers with regulators.
    # For dividers whose top_net matches a regulator's output_rail, mark as feedback.
    for reg in power_regulators:
        fb_net = reg.get("fb_net")
        if not fb_net or reg.get("feedback_divider"):
            continue
        # Check if FB net connects to divider top_net (FB-at-top topology)
        for vd in voltage_dividers:
            if vd["top_net"] == fb_net:
                ratio = vd["ratio"]
                # In FB-at-top, Vout = Vfb (the top of the divider IS the output)
                reg["feedback_divider"] = {
                    "r_top": {"ref": vd["r_top"]["ref"], "ohms": vd["r_top"]["ohms"], "value": vd["r_top"]["value"]},
                    "r_bottom": {"ref": vd["r_bottom"]["ref"], "ohms": vd["r_bottom"]["ohms"], "value": vd["r_bottom"]["value"]},
                    "ratio": ratio,
                    "topology": "fb_at_top",
                }
                if not reg.get("output_rail"):
                    reg["output_rail"] = fb_net
                break

    # Detect output capacitors on each regulator's output rail
    for reg in power_regulators:
        output_rail = reg.get("output_rail")
        reg_ref = reg.get("ref", "")
        if output_rail and output_rail in ctx.nets:
            output_caps = []
            seen_refs = set()
            for p in ctx.nets[output_rail]["pins"]:
                cref = p["component"]
                if cref == reg_ref or cref in seen_refs:
                    continue
                comp = ctx.comp_lookup.get(cref)
                if not comp or comp["type"] != "capacitor":
                    continue
                c_val = ctx.parsed_values.get(cref)
                if not c_val or c_val <= 0:
                    continue
                seen_refs.add(cref)
                cap_entry = {
                    "ref": cref,
                    "value": comp["value"],
                    "farads": c_val,
                }
                # Carry package from footprint for downstream rules (TH-001, PDN)
                fp = comp.get("footprint", "")
                if fp:
                    import re as _re
                    _pkg_m = _re.search(r'(\d{4})', fp)
                    if _pkg_m and _pkg_m.group(1) in (
                            '0201', '0402', '0603', '0805',
                            '1206', '1210', '1812', '2220'):
                        cap_entry["package"] = _pkg_m.group(1)
                output_caps.append(cap_entry)
            if output_caps:
                # Sort by value descending (bulk caps first)
                output_caps.sort(key=lambda c: -c["farads"])
                reg["output_capacitors"] = output_caps

        # Detect input capacitors on the input rail
        input_rail = reg.get("input_rail")
        if input_rail and input_rail in ctx.nets:
            input_caps = []
            seen_refs_in = set()
            for p in ctx.nets[input_rail]["pins"]:
                cref = p["component"]
                if cref == reg_ref or cref in seen_refs_in:
                    continue
                comp = ctx.comp_lookup.get(cref)
                if not comp or comp["type"] != "capacitor":
                    continue
                c_val = ctx.parsed_values.get(cref)
                if not c_val or c_val <= 0:
                    continue
                seen_refs_in.add(cref)
                cap_entry = {
                    "ref": cref,
                    "value": comp["value"],
                    "farads": c_val,
                }
                # Carry package from footprint for downstream rules (TH-001, PDN)
                fp = comp.get("footprint", "")
                if fp:
                    import re as _re
                    _pkg_m = _re.search(r'(\d{4})', fp)
                    if _pkg_m and _pkg_m.group(1) in (
                            '0201', '0402', '0603', '0805',
                            '1206', '1210', '1812', '2220'):
                        cap_entry["package"] = _pkg_m.group(1)
                input_caps.append(cap_entry)
            if input_caps:
                input_caps.sort(key=lambda c: -c["farads"])
                reg["input_capacitors"] = input_caps

        # Detect compensation caps on the FB net
        fb_net = reg.get("fb_net")
        if fb_net and fb_net in ctx.nets:
            comp_caps = []
            for p in ctx.nets[fb_net]["pins"]:
                cref = p["component"]
                if cref == reg_ref:
                    continue
                comp = ctx.comp_lookup.get(cref)
                if not comp or comp["type"] != "capacitor":
                    continue
                c_val = ctx.parsed_values.get(cref)
                if not c_val or c_val <= 0:
                    continue
                # Check what else this cap connects to (output rail = feed-forward, GND = compensation)
                n1, n2 = ctx.get_two_pin_nets(cref)
                other_net = n2 if n1 == fb_net else n1
                comp_caps.append({
                    "ref": cref,
                    "value": comp["value"],
                    "farads": c_val,
                    "other_net": other_net,
                    "role": "feed_forward" if other_net == output_rail else
                            "compensation" if ctx.is_ground(other_net) else "unknown",
                })
            if comp_caps:
                reg["compensation_capacitors"] = comp_caps

    # Estimate power dissipation for LDO regulators
    for reg in power_regulators:
        topology = reg.get("topology", "")
        vin_rail = reg.get("input_rail")
        vout = reg.get("estimated_vout")
        if topology == "LDO" and vin_rail and vout and vout > 0:
            vin = _infer_rail_voltage(vin_rail)
            if vin and vin > vout:
                dropout = vin - vout
                # Estimate load current from output cap total (heuristic:
                # ~100mA per 10µF of output capacitance is a rough proxy)
                output_caps = reg.get("output_capacitors", [])
                total_cout = sum(c.get("farads", 0) for c in output_caps)
                # Conservative estimate: assume typical load from cap sizing
                estimated_iout_a = min(total_cout * 1e4, 1.0) if total_cout > 0 else 0.1
                reg["power_dissipation"] = {
                    "vin_estimated_V": vin,
                    "vout_V": vout,
                    "dropout_V": round(dropout, 3),
                    "estimated_iout_A": round(estimated_iout_a, 3),
                    "estimated_pdiss_W": round(dropout * estimated_iout_a, 3),
                    "_iout_provenance": {
                        "source": "output_cap_proxy",
                        "confidence": "heuristic",
                        "basis": f"total_cout_{total_cout*1e6:.0f}uF",
                    },
                }
        elif topology == "switching" and vout and vout > 0:
            vin = _infer_rail_voltage(vin_rail)
            if vin and vin > 0:
                # Estimate load current from output cap total (same heuristic as LDO,
                # but cap at 2.0A for switching regulators)
                output_caps = reg.get("output_capacitors", [])
                total_cout = sum(c.get("farads", 0) for c in output_caps)
                estimated_iout_a = min(total_cout * 1e4, 2.0) if total_cout > 0 else 0.2

                # Determine sub-topology from part name/lib_id keywords
                lib_val_lower = (reg.get("lib_id", "") + " " + reg.get("value", "")).lower()
                if "buck-boost" in lib_val_lower or "buck_boost" in lib_val_lower \
                        or "sepic" in lib_val_lower or "inverting" in lib_val_lower:
                    sw_type = "buck-boost"
                    efficiency = 0.78
                elif "boost" in lib_val_lower or "step-up" in lib_val_lower \
                        or "step_up" in lib_val_lower or "step up" in lib_val_lower:
                    sw_type = "boost"
                    efficiency = 0.80
                elif "buck" in lib_val_lower or "step-down" in lib_val_lower \
                        or "step_down" in lib_val_lower or "step down" in lib_val_lower:
                    sw_type = "buck"
                    efficiency = 0.85
                else:
                    # Fall back to vin/vout relationship
                    if vin > vout:
                        sw_type = "buck"
                        efficiency = 0.85
                    elif vin < vout:
                        sw_type = "boost"
                        efficiency = 0.80
                    else:
                        sw_type = "buck-boost"
                        efficiency = 0.78

                pout = vout * estimated_iout_a
                pin = pout / efficiency
                pdiss = pin - pout

                reg["power_dissipation"] = {
                    "vin_estimated_V": round(vin, 3),
                    "vout_V": round(vout, 3),
                    "efficiency_assumed": efficiency,
                    "estimated_iout_A": round(estimated_iout_a, 3),
                    "estimated_pdiss_W": round(pdiss, 3),
                    "topology": "switching",
                    "sub_topology": sw_type,
                    "_iout_provenance": {
                        "source": "output_cap_proxy",
                        "confidence": "heuristic",
                        "basis": f"total_cout_{total_cout*1e6:.0f}uF",
                    },
                    "_pdiss_provenance": {
                        "source": "topology_default_efficiency",
                        "confidence": "heuristic",
                        "basis": f"efficiency_{efficiency:.0%}_assumed",
                    },
                }

    return power_regulators


def detect_integrated_ldos(ctx: AnalysisContext, power_regulators: list[dict]) -> list[dict]:
    """Detect ICs with integrated LDOs that output to power nets."""
    _ldo_pin_names = frozenset({
        "VREGOUT", "VREG", "LDO_OUT", "REGOUT", "REG_OUT",
        "VOUT_LDO", "VLDO", "V1P8OUT", "V3P3OUT", "VCOREOUT",
        "VDDOUT", "VREG18", "VREG33", "VREG_OUT",
    })
    existing_refs = {r["ref"] for r in power_regulators}
    integrated = []

    # KH-127: Non-regulator ICs with VREG decoupling pins
    _non_reg_ic_keywords = ("usb_hub", "hub", "cy7c65", "usb2512", "usb2514",
                            "tusb8", "usb3503", "fe1.1", "gl850",
                            "fpga", "cpld", "mcu", "microcontroller",
                            "stm32", "esp32", "nrf5", "atmega", "pic",
                            "ethernet", "phy", "codec", "audio")
    for ic in [c for c in ctx.components if c["type"] == "ic"]:
        ref = ic["reference"]
        if ref in existing_refs:
            continue
        lib_val_lower = (ic.get("lib_id", "") + " " + ic.get("value", "")).lower()
        if any(k in lib_val_lower for k in _non_reg_ic_keywords):
            continue
        for pnum, (net_name, _) in ctx.ref_pins.get(ref, {}).items():
            if not net_name:
                continue
            # Get pin name
            pin_name = ""
            if net_name in ctx.nets:
                for p in ctx.nets[net_name]["pins"]:
                    if p["component"] == ref and p["pin_number"] == pnum:
                        pin_name = p.get("pin_name", "").upper()
                        break
            # Check pin name against LDO output patterns
            pn_clean = pin_name.replace(" ", "").replace("/", "_")
            if pn_clean in _ldo_pin_names or pin_name in _ldo_pin_names:
                if ctx.is_power_net(net_name) and not ctx.is_ground(net_name):
                    integrated.append({
                        "ref": ref,
                        "value": ic.get("value", ""),
                        "lib_id": ic.get("lib_id", ""),
                        "topology": "integrated_ldo",
                        "output_rail": net_name,
                        "output_pin": pin_name,
                        "detector": "detect_integrated_ldos",
                        "rule_id": "IL-DET",
                        "category": "power_management",
                        "severity": "info",
                        "confidence": "deterministic",
                        "evidence_source": "topology",
                        "summary": f"Integrated LDO {ref}",
                        "description": f"IC with integrated LDO output ({pin_name} → {net_name})",
                        "components": [ref],
                        "nets": [],
                        "pins": [],
                        "recommendation": "",
                        "report_context": {"section": "Power Management", "impact": "", "standard_ref": ""},
                        "provenance": make_provenance("ildo_vreg_pin", "heuristic", [ref]),
                    })
                    existing_refs.add(ref)
                    break

    return integrated


def detect_protection_devices(ctx: AnalysisContext) -> list[dict]:
    """Detect protection devices (TVS, ESD, Schottky, fuses, etc.)."""
    protection_devices: list[dict] = []
    protection_types = ("diode", "varistor", "surge_arrester")
    tvs_keywords = ("tvs", "esd", "pesd", "prtr", "usblc", "sp0", "tpd", "ip4", "rclamp",
                     "smaj", "smbj", "p6ke", "1.5ke", "lesd", "nup")
    schottky_keywords = ("schottky", "d_schottky")

    for comp in ctx.components:
        if comp["type"] not in protection_types:
            continue
        val = comp.get("value", "").lower()
        lib = comp.get("lib_id", "").lower()
        desc = comp.get("description", "").lower()

        is_tvs = comp["type"] == "diode" and any(k in val or k in lib for k in tvs_keywords)
        is_schottky = comp["type"] == "diode" and any(k in lib or k in desc for k in schottky_keywords)
        is_non_diode_protection = comp["type"] in ("varistor", "surge_arrester")

        if comp["type"] == "diode" and not is_tvs and not is_schottky:
            continue

        # Multi-pin protection diodes (PRTR5V0U2X, etc.) — handle like ESD ICs
        comp_pins = comp.get("pins", [])
        if len(comp_pins) > 2 and is_tvs:
            if any(p["ref"] == comp["reference"] for p in protection_devices):
                continue
            protected = []
            for pin in comp_pins:
                net_name, _ = ctx.pin_net.get((comp["reference"], pin["number"]), (None, None))
                if net_name and not ctx.is_power_net(net_name) and not ctx.is_ground(net_name):
                    protected.append(net_name)
            # KH-126: One entry per component, collect all protected nets
            if protected:
                sorted_nets = sorted(set(protected))
                protection_devices.append({
                    "ref": comp["reference"],
                    "value": comp.get("value", ""),
                    "type": "esd_ic",
                    "protected_net": sorted_nets[0],
                    "protected_nets": sorted_nets,
                    "clamp_net": None,
                    "detector": "detect_protection_devices",
                    "rule_id": "PD-DET",
                    "category": "protection",
                    "severity": "info",
                    "confidence": "deterministic",
                    "evidence_source": "topology",
                    "summary": f"Protection {comp['reference']} esd_ic",
                    "description": "Multi-pin ESD protection array detected",
                    "components": [comp["reference"]],
                    "nets": [],
                    "pins": [],
                    "recommendation": "",
                    "report_context": {"section": "Protection", "impact": "", "standard_ref": ""},
                    "provenance": make_provenance("prot_esd_array", "deterministic", [comp["reference"]]),
                })
            continue

        d_n1, d_n2 = ctx.get_two_pin_nets(comp["reference"])
        if not d_n1 or not d_n2:
            continue

        protected_net = None
        prot_type = comp["type"]

        if is_schottky and not is_tvs:
            if ctx.is_power_net(d_n1) and (ctx.is_ground(d_n2) or ctx.is_power_net(d_n2)):
                protected_net = d_n1
                prot_type = "reverse_polarity"
            elif ctx.is_power_net(d_n2) and (ctx.is_ground(d_n1) or ctx.is_power_net(d_n1)):
                protected_net = d_n2
                prot_type = "reverse_polarity"
        else:
            if ctx.is_ground(d_n1) and not ctx.is_ground(d_n2):
                protected_net = d_n2
            elif ctx.is_ground(d_n2) and not ctx.is_ground(d_n1):
                protected_net = d_n1
            elif ctx.is_power_net(d_n1) and not ctx.is_power_net(d_n2):
                protected_net = d_n2
            elif ctx.is_power_net(d_n2) and not ctx.is_power_net(d_n1):
                protected_net = d_n1

        if protected_net:
            # KH-143: Deduplicate multi-unit TVS arrays (same ref, different units)
            if any(p["ref"] == comp["reference"] for p in protection_devices):
                continue
            protection_devices.append({
                "ref": comp["reference"],
                "value": comp.get("value", ""),
                "type": prot_type,
                "protected_net": protected_net,
                "clamp_net": d_n1 if protected_net == d_n2 else d_n2,
                "detector": "detect_protection_devices",
                "rule_id": "PD-DET",
                "category": "protection",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Protection {comp['reference']} {prot_type}",
                "description": f"Protection device ({prot_type}) on {protected_net}",
                "components": [comp["reference"]],
                "nets": [],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Protection", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("prot_tvs", "deterministic", [comp["reference"]]),
            })

    # Also detect varistors and surge arresters (already typed correctly)
    for comp in ctx.components:
        if comp["type"] in ("varistor", "surge_arrester"):
            # Avoid duplicates
            if any(p["ref"] == comp["reference"] for p in protection_devices):
                continue
            # KH-117: Try standard 2-pin first, then fall back to scanning
            # all pin_net entries (Eagle imports use P$1/P$2/P$3 pin names)
            d_n1, d_n2 = ctx.get_two_pin_nets(comp["reference"])
            if not d_n1 or not d_n2:
                comp_nets = {net for net, _ in ctx.ref_pins.get(comp["reference"], {}).values() if net}
                comp_nets = [n for n in comp_nets
                             if not ctx.is_ground(n) or len(comp_nets) <= 2]
                if len(comp_nets) >= 2:
                    nets_list = sorted(comp_nets)
                    d_n1, d_n2 = nets_list[0], nets_list[1]
                else:
                    continue
            protected_net = d_n1 if not ctx.is_ground(d_n1) else d_n2
            protection_devices.append({
                "ref": comp["reference"],
                "value": comp.get("value", ""),
                "type": comp["type"],
                "protected_net": protected_net,
                "clamp_net": d_n1 if protected_net == d_n2 else d_n2,
                "detector": "detect_protection_devices",
                "rule_id": "PD-DET",
                "category": "protection",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Protection {comp['reference']} {comp['type']}",
                "description": f"Protection device ({comp['type']}) on {protected_net}",
                "components": [comp["reference"]],
                "nets": [],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Protection", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("prot_varistor", "deterministic", [comp["reference"]]),
            })

    # PTC fuses / polyfuses used as overcurrent protection
    for comp in ctx.components:
        if comp["type"] != "fuse":
            continue
        if any(p["ref"] == comp["reference"] for p in protection_devices):
            continue
        d_n1, d_n2 = ctx.get_two_pin_nets(comp["reference"])
        if not d_n1 or not d_n2:
            continue
        protected_net = None
        if ctx.is_power_net(d_n1) and not ctx.is_power_net(d_n2) and not ctx.is_ground(d_n2):
            protected_net = d_n2
        elif ctx.is_power_net(d_n2) and not ctx.is_power_net(d_n1) and not ctx.is_ground(d_n1):
            protected_net = d_n1
        elif ctx.is_power_net(d_n1) and ctx.is_power_net(d_n2):
            protected_net = d_n2
        if protected_net:
            protection_devices.append({
                "ref": comp["reference"],
                "value": comp.get("value", ""),
                "type": "fuse",
                "protected_net": protected_net,
                "clamp_net": d_n1 if protected_net == d_n2 else d_n2,
                "detector": "detect_protection_devices",
                "rule_id": "PD-DET",
                "category": "protection",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Protection {comp['reference']} fuse",
                "description": f"Fuse/polyfuse protection on {protected_net}",
                "components": [comp["reference"]],
                "nets": [],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Protection", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("prot_fuse", "deterministic", [comp["reference"]]),
            })

    # ---- IC-based ESD Protection ----
    # KH-082: Expanded keywords + Power_Protection library check
    esd_ic_keywords = ("usblc", "tpd", "prtr", "ip42", "sp05", "esda",
                       "pesd", "nup4", "sn65220", "dtc11", "sp72",
                       "tvs18", "tvs1", "ecmf", "cdsot", "smda", "rclamp")
    for comp in ctx.components:
        if comp["type"] != "ic":
            continue
        val = comp.get("value", "").lower()
        lib = comp.get("lib_id", "").lower()
        is_protection_lib = "power_protection:" in lib
        if not (any(k in val or k in lib for k in esd_ic_keywords) or is_protection_lib):
            continue
        if any(p["ref"] == comp["reference"] for p in protection_devices):
            continue
        protected = []
        for pin in comp.get("pins", []):
            net_name, _ = ctx.pin_net.get((comp["reference"], pin["number"]), (None, None))
            if net_name and not ctx.is_power_net(net_name) and not ctx.is_ground(net_name):
                protected.append(net_name)
        # KH-126: One entry per component, collect all protected nets
        if protected:
            sorted_nets = sorted(set(protected))
            protection_devices.append({
                "ref": comp["reference"],
                "value": comp.get("value", ""),
                "type": "esd_ic",
                "protected_net": sorted_nets[0],
                "protected_nets": sorted_nets,
                "clamp_net": None,
                "detector": "detect_protection_devices",
                "rule_id": "PD-DET",
                "category": "protection",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Protection {comp['reference']} esd_ic",
                "description": "IC-based ESD protection device detected",
                "components": [comp["reference"]],
                "nets": [],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Protection", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("prot_ic_based", "deterministic", [comp["reference"]]),
            })

    return protection_devices


def detect_opamp_circuits(ctx: AnalysisContext) -> list[dict]:
    """Detect op-amp gain stage configurations."""
    # EQ-071: G = 1+Rf/Ri or -Rf/Ri; G_dB = 20log₁₀|G| (opamp gain)
    opamp_circuits: list[dict] = []
    opamp_lib_keywords = ("amplifier_operational", "op_amp", "opamp")
    opamp_value_keywords = ("opa", "lm358", "lm324", "mcp6", "ad8", "tl07", "tl08",
                            "ne5532", "lf35", "lt623", "ths", "ada4",
                            "ina10", "ina11", "ina12", "ina13",
                            "ncs3", "lmc7", "lmv3", "max40", "max44",
                            "tsc10", "mcp60", "mcp61", "mcp65")

    seen_opamp_units = set()  # (ref, unit) to avoid multi-unit duplicates
    for ic in [c for c in ctx.components if c["type"] == "ic"]:
        lib = ic.get("lib_id", "").lower()
        val = ic.get("value", "").lower()
        desc = ic.get("description", "").lower()
        lib_part = lib.split(":")[-1] if ":" in lib else ""
        match_sources = [val, lib_part]
        if not (any(k in lib for k in opamp_lib_keywords) or
                any(s.startswith(k) for k in opamp_value_keywords for s in match_sources) or
                any(k in desc for k in ("opamp", "op-amp", "op amp", "operational amplifier", "instrumentation"))):
            continue

        # KH-214: Exclude power/current monitors (INA2xx, INA8xx) that match
        # via description keywords like "instrumentation"
        _pm_val = (val + " " + lib_part).lower()
        if any(_pm_val.startswith(k) for k in ("ina2", "ina8", "ina90")):
            continue

        ref = ic["reference"]
        unit = ic.get("unit", 1)
        if (ref, unit) in seen_opamp_units:
            continue
        seen_opamp_units.add((ref, unit))

        # For multi-unit op-amps, restrict to this unit's pins.
        unit_pin_nums = None
        lib_id = ic.get("lib_id", "")
        sym_def = ctx.lib_symbols.get(lib_id)
        if sym_def and sym_def.get("unit_pins") and unit in sym_def["unit_pins"]:
            unit_pin_nums = {p["number"] for p in sym_def["unit_pins"][unit]}
            if 0 in sym_def["unit_pins"]:
                unit_pin_nums |= {p["number"] for p in sym_def["unit_pins"][0]}

        # Find op-amp pins: +IN, -IN, OUT
        pos_in = None
        neg_in = None
        out_pin = None
        for pnum, (net, _) in ctx.ref_pins.get(ref, {}).items():
            if not net:
                continue
            if unit_pin_nums is not None and pnum not in unit_pin_nums:
                continue
            pin_name = ""
            if net in ctx.nets:
                for p in ctx.nets[net]["pins"]:
                    if p["component"] == ref and p["pin_number"] == pnum:
                        pin_name = p.get("pin_name", "").upper()
                        break
            if not pin_name:
                continue
            pn = pin_name.replace(" ", "")
            if pn in ("+", "+IN", "IN+", "INP", "V+IN", "NONINVERTING",
                      "NON-INV", "NON-INVERTING", "NI") or \
               (pn.startswith("+") and "IN" in pn):
                pos_in = (pin_name, net, pnum)
            elif pn in ("-", "-IN", "IN-", "INM", "V-IN", "INVERTING",
                         "INV", "INV-IN") or \
                 (pn.startswith("-") and "IN" in pn):
                neg_in = (pin_name, net, pnum)
            elif pn in ("OUT", "OUTPUT", "VOUT", "VO"):
                out_pin = (pin_name, net, pnum)
            elif pn in ("V+", "V-", "VCC", "VDD", "VEE", "VSS", "VS+", "VS-"):
                continue
            else:
                pin_type = ""
                if net in ctx.nets:
                    for p in ctx.nets[net]["pins"]:
                        if p["component"] == ref and p["pin_number"] == pnum:
                            pin_type = p.get("pin_type", "")
                            break
                if pin_type == "output" and not out_pin:
                    out_pin = (pin_name, net, pnum)
                elif pin_type == "input":
                    if not pos_in:
                        pos_in = (pin_name, net, pnum)
                    elif not neg_in:
                        neg_in = (pin_name, net, pnum)

        # KH-125: Legacy format fallback — no pin data but keyword match confirmed
        if pos_in is None and neg_in is None and out_pin is None:
            opamp_circuits.append({
                "reference": ref,
                "value": ic.get("value", ""),
                "lib_id": ic.get("lib_id", ""),
                "configuration": "unknown",
                "unit": unit,
                "detector": "detect_opamp_circuits",
                "rule_id": "OA-DET",
                "category": "analog",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Op-amp {ref} unknown",
                "description": "Op-amp detected (no pin data available)",
                "components": [ref],
                "nets": [],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Analog", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("opamp_topology", "deterministic", [ref]),
            })
            continue

        if not out_pin or not neg_in:
            continue

        out_net = out_pin[1]
        neg_net = neg_in[1]
        pos_net = pos_in[1] if pos_in else None

        # Find feedback resistor
        rf_ref = None
        rf_val = None
        if out_net in ctx.nets and neg_net != out_net:
            out_comps = {p["component"] for p in ctx.nets[out_net]["pins"] if p["component"] != ref}
            neg_comps = {p["component"] for p in ctx.nets[neg_net]["pins"] if p["component"] != ref}
            fb_resistors = out_comps & neg_comps
            for fb_ref in fb_resistors:
                comp = ctx.comp_lookup.get(fb_ref)
                if comp and comp["type"] == "resistor" and fb_ref in ctx.parsed_values:
                    # KH-149: Verify direct connection — one pin on out_net, other on neg_net
                    fb_n1, fb_n2 = ctx.get_two_pin_nets(fb_ref)
                    if {fb_n1, fb_n2} == {out_net, neg_net}:
                        rf_ref = fb_ref
                        rf_val = ctx.parsed_values[fb_ref]
                        break

            # Capacitor feedback (integrator/compensator)
            cf_ref = None
            cf_val = None
            fb_caps = out_comps & neg_comps
            for fb_cref in fb_caps:
                comp = ctx.comp_lookup.get(fb_cref)
                if comp and comp["type"] == "capacitor" and fb_cref in ctx.parsed_values:
                    # KH-149: Verify direct connection
                    fb_n1, fb_n2 = ctx.get_two_pin_nets(fb_cref)
                    if {fb_n1, fb_n2} == {out_net, neg_net}:
                        cf_ref = fb_cref
                        cf_val = ctx.parsed_values[fb_cref]
                        break

            # 2-hop feedback
            if not rf_ref:
                for out_comp_ref in out_comps:
                    oc = ctx.comp_lookup.get(out_comp_ref)
                    if not oc or oc["type"] not in ("resistor", "capacitor"):
                        continue
                    o_n1, o_n2 = ctx.get_two_pin_nets(out_comp_ref)
                    if not o_n1 or not o_n2:
                        continue
                    mid = o_n2 if o_n1 == out_net else o_n1
                    # KH-149: Also skip if mid == neg_net (degenerate 2-hop = direct path)
                    if mid in (out_net, neg_net) or ctx.is_ground(mid) or ctx.is_power_net(mid):
                        continue
                    if mid in ctx.nets:
                        mid_comps = {p["component"] for p in ctx.nets[mid]["pins"]
                                    if p["component"] != out_comp_ref}
                        fb_via_mid = mid_comps & neg_comps
                        for fb2 in fb_via_mid:
                            c2 = ctx.comp_lookup.get(fb2)
                            if c2 and c2["type"] in ("resistor", "capacitor"):
                                if oc["type"] == "resistor" and out_comp_ref in ctx.parsed_values:
                                    rf_ref = out_comp_ref
                                    rf_val = ctx.parsed_values[out_comp_ref]
                                elif c2["type"] == "resistor" and fb2 in ctx.parsed_values:
                                    rf_ref = fb2
                                    rf_val = ctx.parsed_values[fb2]
                                break
                    if rf_ref:
                        break
        else:
            cf_ref = None
            cf_val = None

        # Find input resistor
        ri_ref = None
        ri_val = None
        if neg_net in ctx.nets:
            for p in ctx.nets[neg_net]["pins"]:
                if p["component"] == ref or p["component"] == rf_ref:
                    continue
                comp = ctx.comp_lookup.get(p["component"])
                if comp and comp["type"] == "resistor" and p["component"] in ctx.parsed_values:
                    r_n1, r_n2 = ctx.get_two_pin_nets(p["component"])
                    other = r_n2 if r_n1 == neg_net else r_n1
                    if other != out_net and not ctx.is_power_net(other) and not ctx.is_ground(other):
                        ri_ref = p["component"]
                        ri_val = ctx.parsed_values[p["component"]]
                        break

        # Determine configuration
        config = "unknown"
        gain = None
        if out_net == neg_net:
            config = "buffer"
            gain = 1.0
        elif rf_ref and ri_ref and ri_val and rf_val:
            if pos_net and pos_net != neg_net:
                pos_has_signal = pos_net and not ctx.is_power_net(pos_net) and not ctx.is_ground(pos_net)
                neg_has_signal = ri_ref is not None
                if pos_has_signal and not neg_has_signal:
                    config = "non_inverting"
                    gain = 1.0 + rf_val / ri_val
                else:
                    config = "inverting"
                    gain = -rf_val / ri_val
            else:
                config = "inverting"
                gain = -rf_val / ri_val
        elif cf_ref and not rf_ref and ri_ref:
            config = "integrator"
        elif cf_ref and rf_ref:
            # KH-221: Distinguish TIA from compensator.
            # TIA: feedback R >> input R (transimpedance gain = Rf)
            # Compensator: similar-value R+C for loop compensation
            if ri_ref and ri_val and rf_val and ri_val > 0 and rf_val / ri_val > 10:
                config = "transimpedance"
            elif not ri_ref:
                # No input resistor at all — classic TIA topology
                # (photodiode or sensor connected directly to inverting input)
                config = "transimpedance"
            else:
                config = "compensator"
        elif rf_ref and not ri_ref:
            config = "transimpedance_or_buffer"
        elif not rf_ref:
            config = "comparator_or_open_loop"

        entry = {
            "reference": ref,
            "unit": unit,
            "value": ic["value"],
            "lib_id": ic.get("lib_id", ""),
            "configuration": config,
            "output_net": out_net,
            "inverting_input_net": neg_net,
            "non_inverting_input_net": pos_net,
        }
        if gain is not None:
            entry["gain"] = round(gain, 3)
            entry["gain_dB"] = round(20 * math.log10(abs(gain)), 1) if gain != 0 else None
        if rf_ref:
            entry["feedback_resistor"] = {"ref": rf_ref, "ohms": rf_val}
        if cf_ref:
            entry["feedback_capacitor"] = {"ref": cf_ref, "farads": cf_val}
        if ri_ref:
            entry["input_resistor"] = {"ref": ri_ref, "ohms": ri_val}

        # ---- Advanced opamp checks ----
        warnings = []

        # Bias current path check
        if pos_net and config not in ("comparator_or_open_loop", "unknown"):
            pos_net_info = ctx.nets.get(pos_net, {})
            has_dc_path = False
            has_cap_only = False
            for p in pos_net_info.get("pins", []):
                if p["component"] == ref:
                    continue
                neighbor = ctx.comp_lookup.get(p["component"])
                if not neighbor:
                    continue
                if neighbor["type"] == "resistor":
                    has_dc_path = True
                    break
                elif neighbor["type"] in ("ic", "connector"):
                    has_dc_path = True
                    break
                elif neighbor["type"] == "capacitor":
                    has_cap_only = True
            if pos_net and (ctx.is_power_net(pos_net) or ctx.is_ground(pos_net)):
                has_dc_path = True
            if has_cap_only and not has_dc_path:
                warnings.append("Non-inverting input AC-coupled with no DC bias path — "
                                "input bias current has no return path")

        # Output capacitive loading check
        if out_net and config not in ("comparator_or_open_loop", "unknown"):
            out_net_info = ctx.nets.get(out_net, {})
            for p in out_net_info.get("pins", []):
                if p["component"] == ref:
                    continue
                neighbor = ctx.comp_lookup.get(p["component"])
                if not neighbor or neighbor["type"] != "capacitor":
                    continue
                cap_val = neighbor.get("parsed_value") or parse_value(neighbor.get("value", ""))
                if cap_val and cap_val > 100e-12:
                    formatted = f"{cap_val*1e9:.0f}nF" if cap_val >= 1e-9 else f"{cap_val*1e12:.0f}pF"
                    warnings.append(f"Capacitive load {neighbor['reference']} ({formatted}) on "
                                    f"output — verify opamp stability with this load")

        # High-impedance feedback warning
        if rf_ref and rf_val and rf_val > 1e6:
            formatted_r = f"{rf_val/1e6:.1f}MΩ" if rf_val >= 1e6 else f"{rf_val/1e3:.0f}kΩ"
            warnings.append(f"High-impedance feedback ({rf_ref}={formatted_r}) — "
                            f"sensitive to PCB leakage and parasitic capacitance")

        if warnings:
            entry["warnings"] = warnings

        # Dedup
        dedup_key = (ref, out_net, neg_net)
        if dedup_key not in seen_opamp_units:
            seen_opamp_units.add(dedup_key)
            entry["detector"] = "detect_opamp_circuits"
            entry["rule_id"] = "OA-DET"
            entry["category"] = "analog"
            entry["severity"] = "info"
            entry["confidence"] = "deterministic"
            entry["evidence_source"] = "topology"
            entry["summary"] = f"Op-amp {ref} {config}"
            entry["description"] = f"Op-amp circuit in {config} configuration"
            entry["components"] = [ref]
            entry["nets"] = []
            entry["pins"] = []
            entry["recommendation"] = ""
            entry["report_context"] = {"section": "Analog", "impact": "", "standard_ref": ""}
            entry["provenance"] = make_provenance("opamp_topology", "deterministic", [ref])
            opamp_circuits.append(entry)

    # ---- Unused channel detection for multi-channel opamps ----
    units_by_ref = {}
    for oa in opamp_circuits:
        units_by_ref.setdefault(oa["reference"], set()).add(oa.get("unit", 1))

    for ic in [c for c in ctx.components if c["type"] == "ic"]:
        ref = ic["reference"]
        if ref not in units_by_ref:
            continue
        lib = ic.get("lib_id", "").lower()
        val = ic.get("value", "").lower()
        expected_units = None
        if "quad" in lib or "quad" in val or any(q in val for q in ("lm324", "tl074", "tl084", "mcp6004", "opa4")):
            expected_units = 4
        elif "dual" in lib or "dual" in val or any(d in val for d in ("lm358", "tl072", "tl082", "ne5532", "mcp6002", "opa2")):
            expected_units = 2
        if expected_units is None:
            continue
        used_units = units_by_ref[ref]
        if len(used_units) < expected_units:
            unused = sorted(set(range(1, expected_units + 1)) - used_units)
            if unused:
                inputs_floating = False
                for u in unused:
                    for pin in ic.get("pins", []):
                        if pin.get("unit") == u:
                            pname = pin.get("name", "").upper()
                            if any(k in pname for k in ("+IN", "INP", "IN+", "NON_INV")):
                                net_name, _ = ctx.pin_net.get((ref, pin["number"]), (None, None))
                                if not net_name:
                                    inputs_floating = True
                for oa in opamp_circuits:
                    if oa["reference"] == ref:
                        oa["unused_channels"] = unused
                        oa["unused_channel_status"] = "inputs_floating" if inputs_floating else "inputs_terminated"
                        if inputs_floating:
                            oa.setdefault("warnings", []).append(
                                f"Unused opamp channel(s) {unused} have floating inputs — "
                                f"tie inputs to a defined potential")
                        break

    return opamp_circuits


def detect_bridge_circuits(ctx: AnalysisContext) -> tuple[list[dict], set, dict]:
    """Detect gate driver / bridge topology.

    Returns (bridge_circuits, matched_fets, fet_pins).
    """
    bridge_circuits: list[dict] = []
    transistors = [c for c in ctx.components if c["type"] == "transistor"]

    # Build transistor pin map: ref -> {GATE: net, DRAIN: net, SOURCE: net}
    fet_pins = {}
    for t in transistors:
        ref = t["reference"]
        pins = {}
        for pnum, (net, _) in ctx.ref_pins.get(ref, {}).items():
            # Find pin name
            if net and net in ctx.nets:
                for p in ctx.nets[net]["pins"]:
                    if p["component"] == ref and p["pin_number"] == pnum:
                        pn = p.get("pin_name", "").upper()
                        pn_base = pn.rstrip("0123456789").rstrip("_")  # G1→G, D2→D, G_1→G
                        if "GATE" in pn or pn_base == "G":
                            pins["gate"] = net
                        elif "DRAIN" in pn or pn_base == "D":
                            pins.setdefault("drain", net)
                        elif "SOURCE" in pn or pn_base == "S":
                            pins.setdefault("source", net)
                        break
        if "gate" in pins and "drain" in pins and "source" in pins:
            fet_pins[ref] = {**pins, "value": t["value"], "lib_id": t.get("lib_id", "")}

    # Find half-bridge pairs
    matched = set()
    half_bridges = []
    for hi_ref, hi in fet_pins.items():
        if hi_ref in matched:
            continue
        for lo_ref, lo in fet_pins.items():
            if lo_ref == hi_ref or lo_ref in matched:
                continue
            if hi["source"] == lo["drain"]:
                mid_net = hi["source"]
                if ctx.is_power_net(hi["drain"]) or ctx.is_ground(lo["source"]):
                    half_bridges.append({
                        "high_side": hi_ref,
                        "low_side": lo_ref,
                        "output_net": mid_net,
                        "power_net": hi["drain"],
                        "ground_net": lo["source"],
                        "high_gate": hi["gate"],
                        "low_gate": lo["gate"],
                    })
                    matched.add(hi_ref)
                    matched.add(lo_ref)
                    break

    if half_bridges:
        n = len(half_bridges)
        if n == 1:
            topology = "half_bridge"
        elif n == 2:
            topology = "h_bridge"
        elif n == 3:
            topology = "three_phase"
        else:
            topology = f"{n}_phase"

        gate_nets = set()
        for hb in half_bridges:
            gate_nets.add(hb["high_gate"])
            gate_nets.add(hb["low_gate"])
        driver_ics = set()
        for gn in gate_nets:
            if gn in ctx.nets:
                for p in ctx.nets[gn]["pins"]:
                    comp = ctx.comp_lookup.get(p["component"])
                    if comp and comp["type"] == "ic":
                        driver_ics.add(p["component"])

        # Enrich half-bridge dicts with FET type info
        for hb in half_bridges:
            hi_info = fet_pins.get(hb["high_side"], {})
            lo_info = fet_pins.get(hb["low_side"], {})
            hi_lib = hi_info.get("lib_id", "").lower()
            lo_lib = lo_info.get("lib_id", "").lower()
            hb["high_side_type"] = "PMOS" if ("pmos" in hi_lib or "pch" in hi_lib) else "NMOS"
            hb["low_side_type"] = "PMOS" if ("pmos" in lo_lib or "pch" in lo_lib) else "NMOS"
            # Add gate resistor values if available
            for gate_key, gate_net in [("high_gate", hb["high_gate"]), ("low_gate", hb["low_gate"])]:
                if gate_net in ctx.nets:
                    for p in ctx.nets[gate_net]["pins"]:
                        comp = ctx.comp_lookup.get(p["component"])
                        if comp and comp["type"] == "resistor":
                            r_val = ctx.parsed_values.get(p["component"])
                            if r_val:
                                hb[gate_key + "_resistor"] = {"ref": p["component"], "ohms": r_val}
                                break

        _bridge_refs = [hb["high_side"] for hb in half_bridges] + [hb["low_side"] for hb in half_bridges]
        _bridge_driver_ref = next(iter(driver_ics), None)
        _bridge_summary_ref = _bridge_driver_ref or (_bridge_refs[0] if _bridge_refs else "")
        bridge_circuits.append({
            "topology": topology,
            "half_bridges": half_bridges,
            "driver_ics": list(driver_ics),
            "driver_values": {ref: ctx.comp_lookup[ref]["value"] for ref in driver_ics if ref in ctx.comp_lookup},
            "fet_values": {hb["high_side"]: fet_pins[hb["high_side"]]["value"] for hb in half_bridges},
            "detector": "detect_bridge_circuits",
            "rule_id": "BR-DET",
            "category": "power_switching",
            "severity": "info",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "summary": f"Bridge/gate driver {_bridge_summary_ref}",
            "description": f"{topology} bridge circuit detected",
            "components": _bridge_refs + list(driver_ics),
            "nets": [],
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "Power Switching", "impact": "", "standard_ref": ""},
            "provenance": make_provenance("bridge_matched_fets", "deterministic", _bridge_refs),
        })

    return bridge_circuits, matched, fet_pins


def detect_transistor_circuits(ctx: AnalysisContext, matched_fets: set, fet_pins: dict) -> list[dict]:
    """Detect transistor circuit configurations (MOSFETs and BJTs)."""
    transistor_circuits: list[dict] = []
    transistors = [c for c in ctx.components if c["type"] == "transistor"]

    # Build BJT pin map too (base/collector/emitter)
    bjt_pins = {}
    for t in transistors:
        ref = t["reference"]
        if ref in fet_pins:
            continue  # Already mapped as FET
        pins = {}
        for pnum, (net, _) in ctx.ref_pins.get(ref, {}).items():
            if net and net in ctx.nets:
                for p in ctx.nets[net]["pins"]:
                    if p["component"] == ref and p["pin_number"] == pnum:
                        pn = p.get("pin_name", "").upper()
                        if pn in ("B", "BASE"):
                            pins["base"] = net
                        elif pn in ("C", "COLLECTOR"):
                            pins["collector"] = net
                        elif pn in ("E", "EMITTER"):
                            pins["emitter"] = net
                        break
        if len(pins) >= 2:
            bjt_pins[ref] = {**pins, "value": t["value"], "lib_id": t.get("lib_id", "")}

    # Analyze each FET
    for ref, pins in fet_pins.items():
        if ref in matched_fets:
            continue  # Skip bridge FETs, handled above
        comp = ctx.comp_lookup.get(ref, {})
        gate_net = pins.get("gate")
        drain_net = pins.get("drain")
        source_net = pins.get("source")

        # Detect P-channel vs N-channel from lib_id, ki_keywords, and value
        lib_lower = comp.get("lib_id", "").lower()
        val_lower = comp.get("value", "").lower()
        kw_lower = comp.get("keywords", "").lower()
        is_pchannel = any(k in lib_lower for k in
                         ("pmos", "p-channel", "p_channel", "pchannel", "q_pmos", "p_jfet"))
        if not is_pchannel:
            is_pchannel = any(k in kw_lower for k in
                             ("p-channel", "pchannel", "pmos", "p-mos", "p-mosfet"))
        if not is_pchannel:
            is_pchannel = any(k in val_lower for k in
                             ("pmos", "p-channel", "p_channel", "pchannel", "dmp"))
        if not is_pchannel:
            desc_lower = comp.get("description", "").lower()
            is_pchannel = any(k in desc_lower for k in
                             ("p-channel", "p-mosfet", "pmos", "p-mos"))

        # Gate drive analysis
        gate_comps = _get_net_components(ctx, gate_net, ref) if gate_net else []
        gate_ics = [c for c in gate_comps if c["type"] == "ic"]

        # KH-139: When gate is on a power rail, don't enumerate all resistors
        # on that rail — only include resistors connecting to drain/source/ground.
        if gate_net and ctx.is_power_net(gate_net):
            gate_resistors = []
            for gc in gate_comps:
                if gc["type"] != "resistor":
                    continue
                r_n1, r_n2 = ctx.get_two_pin_nets(gc["reference"])
                other = r_n2 if r_n1 == gate_net else r_n1
                if other in (drain_net, source_net) or ctx.is_ground(other):
                    gate_resistors.append(gc)
        else:
            gate_resistors = [c for c in gate_comps if c["type"] == "resistor"]

        if not gate_resistors and gate_net and gate_net in ctx.nets:
            gate_pin_count = len(ctx.nets[gate_net].get("pins", []))
            if gate_pin_count <= 3:
                for gc in gate_comps:
                    if gc["type"] == "resistor":
                        gate_resistors.append(gc)

        gate_pulldown = None
        for gr in gate_resistors:
            r_n1, r_n2 = ctx.get_two_pin_nets(gr["reference"])
            other_net = r_n2 if r_n1 == gate_net else r_n1
            if ctx.is_ground(other_net) or (is_pchannel and ctx.is_power_net(other_net)):
                gate_pulldown = {
                    "reference": gr["reference"],
                    "value": gr["value"],
                }
                break

        # Drain load analysis
        drain_comps = _get_net_components(ctx, drain_net, ref) if drain_net else []

        if is_pchannel and ctx.is_power_net(source_net):
            load_type = _classify_load(ctx, drain_net, ref) if drain_net else "unknown"
            if load_type == "other" and drain_net:
                load_type = "high_side_switch"
        else:
            load_type = _classify_load(ctx, drain_net, ref) if drain_net else "unknown"

        # Flyback diode check
        has_flyback = False
        flyback_ref = None
        for dc in drain_comps:
            if dc["type"] == "diode":
                d_n1, d_n2 = ctx.get_two_pin_nets(dc["reference"])
                # Drain-to-source topology
                if (d_n1 == source_net and d_n2 == drain_net) or \
                   (d_n1 == drain_net and d_n2 == source_net):
                    has_flyback = True
                    flyback_ref = dc["reference"]
                    break
                # KH-098: Drain-to-supply topology (low-side switch flyback)
                d_other = d_n2 if d_n1 == drain_net else (d_n1 if d_n2 == drain_net else None)
                if d_other and ctx.is_power_net(d_other) and not ctx.is_ground(d_other):
                    has_flyback = True
                    flyback_ref = dc["reference"]
                    break

        # Snubber check — detect R+C from drain to source via intermediate net
        has_snubber = False
        snubber_data = None
        for dc in drain_comps:
            if dc["type"] == "resistor":
                r_n1, r_n2 = ctx.get_two_pin_nets(dc["reference"])
                other = r_n2 if r_n1 == drain_net else r_n1
                if other and other != source_net and not ctx.is_power_net(other):
                    for sc in _get_net_components(ctx, other, dc["reference"]):
                        if sc["type"] == "capacitor":
                            c_n1, c_n2 = ctx.get_two_pin_nets(sc["reference"])
                            c_other = c_n2 if c_n1 == other else c_n1
                            if c_other == source_net:
                                has_snubber = True
                                r_ohms = ctx.parsed_values.get(dc["reference"])
                                c_farads = ctx.parsed_values.get(sc["reference"])
                                if r_ohms and c_farads and r_ohms > 0 and c_farads > 0:
                                    snubber_data = {
                                        "resistor_ref": dc["reference"],
                                        "resistor_ohms": r_ohms,
                                        "capacitor_ref": sc["reference"],
                                        "capacitor_farads": c_farads,
                                    }
                                break
            if has_snubber:
                break

        # Source sense resistor
        source_sense = None
        if source_net and not ctx.is_ground(source_net):
            source_comps = _get_net_components(ctx, source_net, ref)
            for sc in source_comps:
                if sc["type"] == "resistor":
                    r_n1, r_n2 = ctx.get_two_pin_nets(sc["reference"])
                    other = r_n2 if r_n1 == source_net else r_n1
                    if ctx.is_ground(other):
                        pv = parse_value(sc["value"])
                        if pv is not None and pv <= 1.0:
                            source_sense = {
                                "reference": sc["reference"],
                                "value": sc["value"],
                                "ohms": pv,
                            }
                            break

        # Level shifter detection: N-channel with gate→power, pull-ups on
        # both source and drain to different power rails
        topology = None
        if not is_pchannel and gate_net and ctx.is_power_net(gate_net):
            source_comps_ls = _get_net_components(ctx, source_net, ref) if source_net else []
            drain_comps_ls = drain_comps
            src_pullup_rail = None
            drn_pullup_rail = None
            for sc in source_comps_ls:
                if sc["type"] == "resistor":
                    r_n1, r_n2 = ctx.get_two_pin_nets(sc["reference"])
                    other = r_n2 if r_n1 == source_net else r_n1
                    if ctx.is_power_net(other):
                        src_pullup_rail = other
                        break
            for dc in drain_comps_ls:
                if dc["type"] == "resistor":
                    r_n1, r_n2 = ctx.get_two_pin_nets(dc["reference"])
                    other = r_n2 if r_n1 == drain_net else r_n1
                    if ctx.is_power_net(other):
                        drn_pullup_rail = other
                        break
            if src_pullup_rail and drn_pullup_rail and src_pullup_rail != drn_pullup_rail:
                topology = "level_shifter"
                load_type = "level_shifter"

        # KH-146: Detect JFET from lib_id/value
        _jfet_kw = ("jfet", "n_jfet", "p_jfet", "q_jfet",
                     "j310", "j271", "j270", "j174", "j175", "j176",
                     "mmbfj", "bf545", "bf546", "bf244", "bf256",
                     "2n5457", "2n5458", "2n5459", "2n3819", "2n4416")
        is_jfet = any(k in lib_lower or k in val_lower for k in _jfet_kw)

        _tr_type = "jfet" if is_jfet else "mosfet"
        circuit = {
            "reference": ref,
            "value": comp.get("value", ""),
            "lib_id": comp.get("lib_id", ""),
            "type": _tr_type,
            "is_pchannel": is_pchannel,
            "gate_net": gate_net,
            "drain_net": drain_net,
            "source_net": source_net,
            "drain_is_power": ctx.is_power_net(drain_net) or (is_pchannel and ctx.is_power_net(source_net)),
            "source_is_ground": ctx.is_ground(source_net),
            "source_is_power": ctx.is_power_net(source_net),
            "load_type": load_type,
            "gate_resistors": [{"reference": r["reference"], "value": r["value"]} for r in gate_resistors],
            "gate_driver_ics": [{"reference": ic["reference"], "value": ic["value"]} for ic in gate_ics],
            "gate_pulldown": gate_pulldown,
            "has_flyback_diode": has_flyback,
            "flyback_diode": flyback_ref,
            "has_snubber": has_snubber,
            "snubber_data": snubber_data,
            "source_sense_resistor": source_sense,
            "detector": "detect_transistor_circuits",
            "rule_id": "TR-DET",
            "category": "discrete_semiconductors",
            "severity": "info",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "summary": f"Transistor {ref} {_tr_type}",
            "description": f"Transistor circuit ({_tr_type}) detected",
            "components": [ref],
            "nets": [],
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "Discrete Semiconductors", "impact": "", "standard_ref": ""},
            "provenance": make_provenance("transistor_mosfet", "deterministic", [ref]),
        }
        if topology:
            circuit["topology"] = topology
        transistor_circuits.append(circuit)

    # Analyze each BJT
    for ref, pins in bjt_pins.items():
        comp = ctx.comp_lookup.get(ref, {})
        base_net = pins.get("base")
        collector_net = pins.get("collector")
        emitter_net = pins.get("emitter")

        # Base drive analysis
        base_comps = _get_net_components(ctx, base_net, ref) if base_net else []
        base_resistors = [c for c in base_comps if c["type"] == "resistor"]
        base_ics = [c for c in base_comps if c["type"] == "ic"]
        base_pulldown = None
        for br in base_resistors:
            r_n1, r_n2 = ctx.get_two_pin_nets(br["reference"])
            other_net = r_n2 if r_n1 == base_net else r_n1
            if ctx.is_ground(other_net) or other_net == emitter_net:
                base_pulldown = {
                    "reference": br["reference"],
                    "value": br["value"],
                }
                break

        # Collector load
        load_type = _classify_load(ctx, collector_net, ref) if collector_net else "unknown"

        # Emitter resistor (degeneration)
        emitter_resistor = None
        if emitter_net and not ctx.is_ground(emitter_net):
            emitter_comps = _get_net_components(ctx, emitter_net, ref)
            for ec in emitter_comps:
                if ec["type"] == "resistor":
                    r_n1, r_n2 = ctx.get_two_pin_nets(ec["reference"])
                    other = r_n2 if r_n1 == emitter_net else r_n1
                    if ctx.is_ground(other):
                        emitter_resistor = {
                            "reference": ec["reference"],
                            "value": ec["value"],
                        }
                        break

        circuit = {
            "reference": ref,
            "value": comp.get("value", ""),
            "lib_id": comp.get("lib_id", ""),
            "type": "bjt",
            "base_net": base_net,
            "collector_net": collector_net,
            "emitter_net": emitter_net,
            "collector_is_power": ctx.is_power_net(collector_net),
            "emitter_is_ground": ctx.is_ground(emitter_net),
            "load_type": load_type,
            "base_resistors": [{"reference": r["reference"], "value": r["value"]} for r in base_resistors],
            "base_driver_ics": [{"reference": ic["reference"], "value": ic["value"]} for ic in base_ics],
            "base_pulldown": base_pulldown,
            "emitter_resistor": emitter_resistor,
            "detector": "detect_transistor_circuits",
            "rule_id": "TR-DET",
            "category": "discrete_semiconductors",
            "severity": "info",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "summary": f"Transistor {ref} bjt",
            "description": "BJT transistor circuit detected",
            "components": [ref],
            "nets": [],
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "Discrete Semiconductors", "impact": "", "standard_ref": ""},
            "provenance": make_provenance("transistor_bjt", "deterministic", [ref]),
        }
        transistor_circuits.append(circuit)

    return transistor_circuits


def postfilter_vd_and_dedup(voltage_dividers: list[dict], feedback_networks: list[dict],
                            transistor_circuits: list[dict],
                            nets: dict | None = None) -> tuple[list[dict], list[dict]]:
    """Post-filter: remove VDs on transistor gate/base nets and deduplicate."""
    # ---- Post-filter: remove voltage dividers on transistor gate/base nets ----
    _gate_base_nets = set()
    for tc in transistor_circuits:
        if tc["type"] == "mosfet" and tc.get("gate_net"):
            _gate_base_nets.add(tc["gate_net"])
        elif tc["type"] == "bjt" and tc.get("base_net"):
            _gate_base_nets.add(tc["base_net"])

    # Also exclude VDs whose mid_net connects to an opamp inverting input
    if nets:
        for vd in voltage_dividers:
            mid = vd["mid_net"]
            if mid in nets:
                for p in nets[mid]["pins"]:
                    pname = p.get("pin_name", "").upper()
                    if any(x in pname for x in ("IN-", "INV", "INN")):
                        _gate_base_nets.add(mid)
                        break

    if _gate_base_nets:
        voltage_dividers = [
            vd for vd in voltage_dividers
            if vd["mid_net"] not in _gate_base_nets
        ]
        feedback_networks = [
            fn for fn in feedback_networks
            if fn["mid_net"] not in _gate_base_nets
        ]

    # ---- Post-filter: deduplicate voltage dividers by network topology ----
    _vd_groups: dict[tuple[str, str, str], list[dict]] = {}
    for vd in voltage_dividers:
        key = (vd["top_net"], vd["mid_net"], vd["bottom_net"])
        _vd_groups.setdefault(key, []).append(vd)
    deduped_vds: list[dict] = []
    for key, entries in _vd_groups.items():
        rep = entries[0]
        if len(entries) > 1:
            rep["parallel_count"] = len(entries)
        deduped_vds.append(rep)

    # Also deduplicate feedback_networks the same way
    _fn_groups: dict[tuple[str, str, str], list[dict]] = {}
    for fn in feedback_networks:
        key = (fn["top_net"], fn["mid_net"], fn["bottom_net"])
        _fn_groups.setdefault(key, []).append(fn)
    deduped_fns: list[dict] = []
    for key, entries in _fn_groups.items():
        rep = entries[0]
        if len(entries) > 1:
            rep["parallel_count"] = len(entries)
        deduped_fns.append(rep)

    return deduped_vds, deduped_fns


def detect_led_drivers(ctx: AnalysisContext, transistor_circuits: list[dict]) -> None:
    """Enrich transistor circuits with LED driver info. Modifies transistor_circuits in-place."""
    for tc in transistor_circuits:
        is_mosfet = tc.get("type") == "mosfet"
        is_bjt = tc.get("type") == "bjt"
        if not is_mosfet and not is_bjt:
            continue
        load_net = tc.get("drain_net") if is_mosfet else tc.get("collector_net")
        if not load_net:
            continue
        # Look at components on the load net for a resistor
        load_comps = _get_net_components(ctx, load_net, tc["reference"])
        for dc in load_comps:
            if dc["type"] != "resistor":
                continue
            # KH-147: Reject resistors that are too large for current limiting,
            # or whose value field can't be parsed (e.g. "215k_0402_C0123XYZ"
            # from importers that append package/MPN suffixes). Without a
            # parseable value we can't confirm current-limiting role, so skip
            # to avoid false-positive LED driver findings.
            r_ohms = ctx.parsed_values.get(dc["reference"])
            if r_ohms is None or r_ohms > 100e3:
                continue
            # Follow the resistor to its other net
            r_n1, r_n2 = ctx.get_two_pin_nets(dc["reference"])
            other_net = r_n2 if r_n1 == load_net else r_n1
            if not other_net or other_net == load_net:
                continue
            # Check if an LED is on that net
            other_comps = _get_net_components(ctx, other_net, dc["reference"])
            for oc in other_comps:
                if oc["type"] == "led":
                    # KH-147: Verify LED actually has a pin on other_net
                    led_n1, led_n2 = ctx.get_two_pin_nets(oc["reference"])
                    if led_n1 != other_net and led_n2 != other_net:
                        continue
                    led_comp = ctx.comp_lookup.get(oc["reference"], {})
                    # Find what power rail the LED's other pin connects to
                    led_other = led_n2 if led_n1 == other_net else led_n1
                    led_power = led_other if led_other and ctx.is_power_net(led_other) else None
                    tc["led_driver"] = {
                        "led_ref": oc["reference"],
                        "led_value": led_comp.get("value", ""),
                        "current_resistor": dc["reference"],
                        "current_resistor_value": dc.get("value", ""),
                        "power_rail": led_power,
                    }
                    ohms = ctx.parsed_values.get(dc["reference"])
                    if ohms and led_power:
                        tc["led_driver"]["resistor_ohms"] = ohms
                    # Update envelope fields on the transistor circuit dict
                    tc["detector"] = "detect_led_drivers"
                    tc["rule_id"] = "LD-DET"
                    tc["category"] = "led_control"
                    tc["severity"] = "info"
                    tc["confidence"] = "deterministic"
                    tc["evidence_source"] = "topology"
                    tc["summary"] = f"LED driver {tc['reference']}"
                    tc["description"] = f"Transistor {tc['reference']} driving LED {oc['reference']}"
                    tc["components"] = [tc["reference"], oc["reference"], dc["reference"]]
                    tc["nets"] = []
                    tc["pins"] = []
                    tc["recommendation"] = ""
                    tc["report_context"] = {"section": "LED Control", "impact": "", "standard_ref": ""}
                    tc["provenance"] = make_provenance("led_driver_transistor", "deterministic", [tc["reference"], oc["reference"], dc["reference"]])
                    break
            if "led_driver" in tc:
                break



def detect_design_observations(ctx: AnalysisContext, results: dict) -> list[dict]:
    """Generate structured design observations for higher-level analysis."""
    # EQ-070: Threshold comparisons for design quality metrics
    design_observations: list[dict] = []

    # Build helper sets
    decoupled_rails = {d["rail"] for d in results.get("decoupling_analysis", [])}
    connector_nets = set()
    for net_name, net_info in ctx.nets.items():
        for p in net_info["pins"]:
            comp = ctx.comp_lookup.get(p["component"])
            if comp and comp["type"] in ("connector", "test_point"):
                connector_nets.add(net_name)
    protected_nets = {p["protected_net"] for p in results.get("protection_devices", [])}

    # KH-148: Deduplicate multi-unit ICs (same ref, different units)
    unique_ics = get_unique_ics(ctx)

    # 1. IC power pin decoupling status
    for ic in unique_ics:
        ref = ic["reference"]
        ic_power_nets = {net for net, _ in ctx.ref_pins.get(ref, {}).values()
                         if net and ctx.is_power_net(net) and not ctx.is_ground(net)}
        undecoupled = [r for r in ic_power_nets if r not in decoupled_rails]
        if undecoupled:
            design_observations.append({
                "category": "decoupling",
                "component": ref,
                "value": ic["value"],
                "rails_without_caps": undecoupled,
                "rails_with_caps": [r for r in ic_power_nets if r in decoupled_rails],
                "detector": "detect_design_observations",
                "rule_id": "DO-DET",
                "severity": "info",
                "confidence": "heuristic",
                "evidence_source": "topology",
                "summary": f"IC {ref} missing decoupling on {', '.join(undecoupled)}",
                "description": "IC power pin(s) without decoupling capacitors",
                "components": [ref],
                "nets": [],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Design Observations", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("obs_topology", "heuristic", [ref]),
            })

    # 2. Regulator capacitor status
    for reg in results.get("power_regulators", []):
        in_rail = reg.get("input_rail")
        out_rail = reg.get("output_rail")
        missing = {}
        if in_rail and in_rail not in decoupled_rails:
            missing["input"] = in_rail
        if out_rail and out_rail not in decoupled_rails:
            missing["output"] = out_rail
        if missing:
            design_observations.append({
                "category": "regulator_caps",
                "component": reg["ref"],
                "value": reg["value"],
                "topology": reg.get("topology"),
                "missing_caps": missing,
                "detector": "detect_design_observations",
                "rule_id": "DO-DET",
                "severity": "info",
                "confidence": "heuristic",
                "evidence_source": "topology",
                "summary": f"Regulator {reg['ref']} missing capacitors",
                "description": "Regulator missing input or output capacitors",
                "components": [reg["ref"]],
                "nets": [],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Design Observations", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("obs_topology", "heuristic", [reg["ref"]]),
            })

    # 3. Single-pin signal nets
    single_pin_nets = []
    for net_name, net_info in ctx.nets.items():
        if net_name.startswith("__unnamed_"):
            continue
        if net_info.get("no_connect"):
            continue
        if ctx.is_power_net(net_name) or ctx.is_ground(net_name):
            continue
        if net_name in connector_nets:
            continue
        real_pins = [p for p in net_info["pins"] if not p["component"].startswith("#")]
        if len(real_pins) == 1:
            p = real_pins[0]
            comp = ctx.comp_lookup.get(p["component"])
            if comp and comp["type"] == "ic":
                pin_name = p.get("pin_name", p["pin_number"])
                pn_upper = pin_name.upper()
                if re.match(r'^P[A-K]\d', pn_upper) or re.match(r'^GPIO', pn_upper):
                    continue
                single_pin_nets.append({
                    "component": p["component"],
                    "pin": pin_name,
                    "net": net_name,
                })
    if single_pin_nets:
        design_observations.append({
            "category": "single_pin_nets",
            "count": len(single_pin_nets),
            "nets": single_pin_nets,
            "detector": "detect_design_observations",
            "rule_id": "DO-DET",
            "severity": "info",
            "confidence": "heuristic",
            "evidence_source": "topology",
            "summary": f"Single-pin nets ({len(single_pin_nets)} nets)",
            "description": "Signal nets connected to only one pin",
            "components": [n["component"] for n in single_pin_nets],
            "nets": [],
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "Design Observations", "impact": "", "standard_ref": ""},
            "provenance": make_provenance("obs_topology", "heuristic", [n["component"] for n in single_pin_nets]),
        })

    # 4. I2C bus pull-up status
    for net_name, net_info in ctx.nets.items():
        nn = net_name.upper()
        if "I2S" in nn:
            continue
        # KH-099: Exclude I2S audio pins (SDAT, LRCK, BCLK, WSEL)
        if any(kw in nn for kw in ("SDAT", "LRCK", "BCLK", "WSEL")):
            continue
        # KH-086: Exclude SPI nets — sensors with dual-function SDA/SCL pin names
        if "SPI" in nn or "MOSI" in nn or "MISO" in nn:
            continue
        # KH-099: Tighten SDA regex to exclude SDAT (I2S serial data)
        is_sda = bool(re.search(r'\bSDA\b(?!T)', nn) or re.search(r'I2C.*SDA|SDA.*I2C', nn))
        is_scl = bool(re.search(r'\bSCL\b', nn) or re.search(r'I2C.*SCL|SCL.*I2C', nn))
        if "SCLK" in nn or "SCK" in nn:
            is_scl = False
        if not (is_sda or is_scl):
            continue
        line = "SDA" if is_sda else "SCL"
        has_pullup = False
        pullup_ref = None
        pullup_to = None
        for p in net_info["pins"]:
            comp = ctx.comp_lookup.get(p["component"])
            if comp and comp["type"] == "resistor":
                r_n1, r_n2 = ctx.get_two_pin_nets(p["component"])
                other = r_n2 if r_n1 == net_name else r_n1
                if other and ctx.is_power_net(other):
                    has_pullup = True
                    pullup_ref = p["component"]
                    pullup_to = other
                    break
        ic_refs = [p["component"] for p in net_info["pins"]
                   if ctx.comp_lookup.get(p["component"], {}).get("type") == "ic"]
        if ic_refs:
            design_observations.append({
                "category": "i2c_bus",
                "net": net_name,
                "line": line,
                "devices": ic_refs,
                "has_pullup": has_pullup,
                "pullup_resistor": pullup_ref,
                "pullup_rail": pullup_to,
                "detector": "detect_design_observations",
                "rule_id": "DO-DET",
                "severity": "info",
                "confidence": "heuristic",
                "evidence_source": "topology",
                "summary": f"I2C {line} bus on {net_name}",
                "description": f"I2C {line} bus detected with {len(ic_refs)} device(s)",
                "components": ic_refs,
                "nets": [],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Design Observations", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("obs_topology", "heuristic", ic_refs),
            })

    # 5. Reset pin configuration
    for ic in unique_ics:
        ref = ic["reference"]
        for pnum, (net, _) in ctx.ref_pins.get(ref, {}).items():
            if not net or net.startswith("__unnamed_") or (net in ctx.nets and ctx.nets[net].get("no_connect")):
                continue
            pin_name = ""
            if net in ctx.nets:
                for p in ctx.nets[net]["pins"]:
                    if p["component"] == ref and p["pin_number"] == pnum:
                        pin_name = p.get("pin_name", "").upper()
                        break
            if pin_name not in ("NRST", "~{RESET}", "RESET", "~{RST}", "RST", "~{NRST}", "MCLR", "~{MCLR}"):
                continue
            has_resistor = False
            has_capacitor = False
            connected_to = []
            if net in ctx.nets:
                for p in ctx.nets[net]["pins"]:
                    comp = ctx.comp_lookup.get(p["component"])
                    if not comp or p["component"] == ref:
                        continue
                    if comp["type"] == "resistor":
                        has_resistor = True
                    elif comp["type"] == "capacitor":
                        has_capacitor = True
                    connected_to.append({"ref": p["component"], "type": comp["type"]})
            design_observations.append({
                "category": "reset_pin",
                "component": ref,
                "value": ic["value"],
                "pin": pin_name,
                "net": net,
                "has_pullup": has_resistor,
                "has_filter_cap": has_capacitor,
                "connected_components": connected_to,
                "detector": "detect_design_observations",
                "rule_id": "DO-DET",
                "severity": "info",
                "confidence": "heuristic",
                "evidence_source": "topology",
                "summary": f"Reset pin on {ref} ({pin_name})",
                "description": f"Reset pin configuration for {ref}",
                "components": [ref],
                "nets": [],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Design Observations", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("obs_topology", "heuristic", [ref]),
            })

    # 6. Regulator feedback voltage estimation
    for reg in results.get("power_regulators", []):
        if "estimated_vout" in reg:
            obs = {
                "category": "regulator_voltage",
                "component": reg["ref"],
                "value": reg["value"],
                "topology": reg.get("topology"),
                "estimated_vout": reg["estimated_vout"],
                "assumed_vref": reg.get("assumed_vref"),
                "vref_source": reg.get("vref_source", "heuristic"),
                "feedback_divider": reg.get("feedback_divider"),
                "input_rail": reg.get("input_rail"),
                "output_rail": reg.get("output_rail"),
            }
            out_rail = reg.get("output_rail", "")
            rail_v = _parse_voltage_from_net_name(out_rail)
            if rail_v is not None and reg["estimated_vout"] > 0:
                pct_diff = abs(reg["estimated_vout"] - rail_v) / rail_v
                if pct_diff > 0.15:
                    obs["vout_net_mismatch"] = {
                        "net_name": out_rail,
                        "net_voltage": rail_v,
                        "estimated_vout": reg["estimated_vout"],
                        "percent_diff": round(pct_diff * 100, 1),
                    }
            obs["detector"] = "detect_design_observations"
            obs["rule_id"] = "DO-DET"
            obs["severity"] = "info"
            obs["confidence"] = "heuristic"
            obs["evidence_source"] = "topology"
            obs["summary"] = f"Regulator {reg['ref']} estimated Vout={reg['estimated_vout']}V"
            obs["description"] = "Regulator output voltage estimated from feedback divider"
            obs["components"] = [reg["ref"]]
            obs["nets"] = []
            obs["pins"] = []
            obs["recommendation"] = ""
            obs["report_context"] = {"section": "Design Observations", "impact": "", "standard_ref": ""}
            obs["provenance"] = make_provenance("obs_topology", "heuristic", [reg["ref"]])
            design_observations.append(obs)

    # 7. Switching regulator bootstrap status
    for reg in results.get("power_regulators", []):
        if reg.get("topology") == "switching" and reg.get("inductor"):
            design_observations.append({
                "category": "switching_regulator",
                "component": reg["ref"],
                "value": reg["value"],
                "inductor": reg.get("inductor"),
                "has_bootstrap": reg.get("has_bootstrap", False),
                "input_rail": reg.get("input_rail"),
                "output_rail": reg.get("output_rail"),
                "detector": "detect_design_observations",
                "rule_id": "DO-DET",
                "severity": "info",
                "confidence": "heuristic",
                "evidence_source": "topology",
                "summary": f"Switching regulator {reg['ref']}",
                "description": f"Switching regulator with inductor {reg.get('inductor')}",
                "components": [reg["ref"]],
                "nets": [],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Design Observations", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("obs_topology", "heuristic", [reg["ref"]]),
            })

    # 8. USB data line protection status
    for net_name in ctx.nets:
        nn = net_name.upper()
        is_usb = any(x in nn for x in ("USB_D", "USBDP", "USBDM", "USB_DP", "USB_DM"))
        if not is_usb and nn in ("D+", "D-", "DP", "DM"):
            if net_name in ctx.nets:
                for p in ctx.nets[net_name]["pins"]:
                    comp = ctx.comp_lookup.get(p["component"])
                    if comp:
                        cv = (comp.get("value", "") + " " + comp.get("lib_id", "")).upper()
                        if "USB" in cv:
                            is_usb = True
                            break
        if is_usb:
            _usb_devices = [p["component"] for p in ctx.nets[net_name]["pins"]
                            if not ctx.comp_lookup.get(p["component"], {}).get("type") in (None,)]
            design_observations.append({
                "category": "usb_data",
                "net": net_name,
                "has_esd_protection": net_name in protected_nets,
                "devices": _usb_devices,
                "detector": "detect_design_observations",
                "rule_id": "DO-DET",
                "severity": "info",
                "confidence": "heuristic",
                "evidence_source": "topology",
                "summary": f"USB data line {net_name}",
                "description": f"USB data net {net_name} detected",
                "components": _usb_devices,
                "nets": [],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Design Observations", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("obs_topology", "heuristic", _usb_devices),
            })

    # 9. Crystal load capacitance
    for xtal in results.get("crystal_circuits", []):
        if "effective_load_pF" in xtal:
            design_observations.append({
                "category": "crystal",
                "component": xtal["reference"],
                "value": xtal.get("value"),
                "effective_load_pF": xtal["effective_load_pF"],
                "load_caps": xtal.get("load_caps", []),
                "in_typical_range": 4 <= xtal["effective_load_pF"] <= 30,
                "detector": "detect_design_observations",
                "rule_id": "DO-DET",
                "severity": "info",
                "confidence": "heuristic",
                "evidence_source": "topology",
                "summary": f"Crystal load cap {xtal['reference']} = {xtal['effective_load_pF']}pF",
                "description": "Crystal load capacitance observation",
                "components": [xtal["reference"]],
                "nets": [],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Design Observations", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("obs_topology", "heuristic", [xtal["reference"]]),
            })

    # 10. Decoupling frequency coverage per rail
    for decoup in results.get("decoupling_analysis", []):
        caps = decoup.get("capacitors", [])
        farads_list = [c.get("farads", 0) for c in caps]
        has_bulk = any(f >= 1e-6 for f in farads_list)
        has_bypass = any(10e-9 <= f <= 1e-6 for f in farads_list)
        has_hf = any(f < 10e-9 for f in farads_list)
        design_observations.append({
            "category": "decoupling_coverage",
            "rail": decoup["rail"],
            "cap_count": len(caps),
            "total_uF": decoup.get("total_capacitance_uF"),
            "has_bulk": has_bulk,
            "has_bypass": has_bypass,
            "has_high_freq": has_hf,
            "detector": "detect_design_observations",
            "rule_id": "DO-DET",
            "severity": "info",
            "confidence": "heuristic",
            "evidence_source": "topology",
            "summary": f"Decoupling coverage on {decoup['rail']}",
            "description": f"Decoupling frequency coverage for rail {decoup['rail']}",
            "components": [c["ref"] for c in caps],
            "nets": [],
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "Design Observations", "impact": "", "standard_ref": ""},
            "provenance": make_provenance("obs_topology", "heuristic", [c["ref"] for c in caps]),
        })

    return design_observations


# ---------------------------------------------------------------------------
# Solder Jumper Inventory (SJ-DET)
# ---------------------------------------------------------------------------

def detect_solder_jumpers(ctx: AnalysisContext) -> list[dict]:
    """Enumerate every solder jumper in the design and report its default state.

    Emits one INFO finding per jumper so downstream rules and LLM reviewers
    can tell at a glance whether a net is bridged-by-default (works without
    any user action) or open-by-default (requires soldering to function).
    KiCad encodes this in the library symbol and footprint name — e.g.
    ``Jumper:SolderJumper_2_Bridged`` with footprint
    ``SolderJumper-2_P1.3mm_Bridged_*`` is closed until the bridge is
    scored, while ``Jumper:Jumper_2_Open`` with ``*_Open_*`` is a pair of
    pads that must be soldered.

    The finding records the two nets the jumper straddles and which of
    them (if any) look like power rails by name. Rule ID ``SJ-DET``.
    """
    findings: list[dict] = []
    nets = ctx.nets or {}

    # Build ref → [(pin_number, net_name)] map from the nets side so we
    # handle implicit power-symbol nets (+3.3V, GND) the same as ordinary
    # wired nets.
    ref_pins: dict[str, list[tuple[str, str]]] = {}
    for net_name, net_info in nets.items():
        if not isinstance(net_info, dict):
            continue
        for pin in net_info.get("pins", []) or []:
            ref = pin.get("component") or pin.get("ref")
            pnum = pin.get("pin_number") or pin.get("pin") or ""
            if ref:
                ref_pins.setdefault(ref, []).append((str(pnum), net_name))

    for comp in ctx.components:
        if comp.get("type") != "jumper" and comp.get("category") != "jumper":
            continue
        ref = comp.get("reference")
        if not ref:
            continue
        value = comp.get("value", "") or ""
        lib_id = comp.get("lib_id", "") or ""
        footprint = comp.get("footprint", "") or ""
        state = classify_jumper_default_state(value, lib_id, footprint)

        # A 2-pin jumper is the common case; 3-pin selector jumpers exist
        # but carry multiple bridge variants (Bridged12, Bridged23). We
        # report them but don't attempt per-pin state inference here.
        pins = sorted(set(ref_pins.get(ref, [])))
        net_list = []
        for pnum, net in pins:
            if net and net not in net_list:
                net_list.append(net)

        power_nets = [n for n in net_list if is_power_net_name(n, None)]
        ground_nets = [n for n in net_list if is_ground_name(n)]

        if state == "bridged":
            severity = "info"
            if len(net_list) >= 2:
                summary = (f"{ref} ({value or lib_id}) — closed by default, "
                           f"connecting {' ↔ '.join(net_list[:2])}")
            else:
                summary = f"{ref} ({value or lib_id}) — closed by default"
            recommendation = ("Bridged solder jumper conducts without user "
                              "action. Scoring/cutting the bridge isolates "
                              "the two nets. Treat as a normal connection "
                              "unless the design-intent note says otherwise.")
            impact = "Connection is live out of the box; no user action required."
        elif state == "open":
            severity = "warning" if power_nets or ground_nets else "info"
            summary = (f"{ref} ({value or lib_id}) — open by default"
                       + (f", between {' ↔ '.join(net_list[:2])}" if len(net_list) >= 2 else ""))
            recommendation = ("Open solder jumper is non-conducting until "
                              "the pads are soldered. If either side is a "
                              "power rail or required signal, the board "
                              "won't function without the solder step.")
            impact = ("Connection requires soldering; board won't pass "
                      "bring-up if left unpopulated."
                      if power_nets or ground_nets else
                      "Optional / configuration jumper.")
        elif state == "switchable":
            severity = "info"
            summary = (f"{ref} ({value or lib_id}) — physical shunt (state "
                       "set at assembly/board-bring-up)")
            recommendation = ("Shunt-block configuration — actual conduction "
                              "depends on whether the shunt is installed.")
            impact = "Runtime-configurable; state not visible in schematic."
        else:
            severity = "info"
            summary = (f"{ref} ({value or lib_id}) — jumper with unknown "
                       "default state")
            recommendation = ("Unable to determine default conduction from "
                              "symbol/footprint. Inspect manually.")
            impact = ""

        findings.append({
            "detector": "detect_solder_jumpers",
            "rule_id": "SJ-DET",
            "severity": severity,
            "confidence": "deterministic",
            "evidence_source": "symbol_footprint",
            "category": "topology",
            "summary": summary,
            "reference": ref,
            "value": value,
            "lib_id": lib_id,
            "footprint": footprint,
            "default_state": state,
            "nets": net_list,
            "power_nets": power_nets,
            "ground_nets": ground_nets,
            "pin_count": len(pins),
            "components": [ref],
            "pins": [f"{ref}.{pn}" for pn, _ in pins],
            "recommendation": recommendation,
            "report_context": {
                "section": "Solder Jumpers",
                "impact": impact,
                "standard_ref": "",
            },
            "provenance": make_provenance("sj_symbol_footprint", "deterministic", [ref]),
        })

    return findings


# ---------------------------------------------------------------------------
# Rail source audit (RS-001 / RS-002)
# ---------------------------------------------------------------------------

def audit_rail_sources(ctx: AnalysisContext,
                       power_regulators: list[dict] | None = None,
                       solder_jumpers: list[dict] | None = None) -> list[dict]:
    """Audit every power-classified net for a declared source.

    A rail with no `power_out` pin, no `PWR_FLAG` / `#FLG`, and no
    regulator output mapping is source-less on paper. The solder-jumper
    aware trace: a bridged-by-default jumper joins two nets electrically;
    if the other side has a source, the audited rail is sourced via the
    jumper (INFO). A rail reached only through an *open* jumper is a HIGH
    — the board won't power up until the user closes the jumper.

    Rule tiers:
      RS-001  rail has no source path at all                    severity=warning
      RS-002  only source path is through an open jumper        severity=high
              (board needs a solder action to function)
      info    sourced directly OR via a bridged jumper         (recorded for audit)
    """
    findings: list[dict] = []
    nets = ctx.nets or {}

    # Regulator output nets (from the regulator detector) are sources
    # even when the regulator symbol uses power_in on its OUT pin.
    reg_output_nets: set[str] = set()
    for reg in (power_regulators or []):
        out = reg.get("output_rail") or reg.get("vout_net")
        if out:
            reg_output_nets.add(out)

    # Build a quick map of net → list of (neighbour, state, jumper_ref) tuples
    # for solder jumpers that straddle the net.
    jumper_bridges: dict[str, list[tuple[str, str, str]]] = {}
    for sj in (solder_jumpers or []):
        state = sj.get("default_state")
        nets_straddled = sj.get("nets") or []
        # Only 2-net jumpers (standard SolderJumper_2_Bridged / _Open) are
        # amenable to one-hop traversal. 3-pin selector jumpers (e.g.
        # SolderJumper_3_Bridged12 / _Bridged23) encode the actual shorted
        # pair in the footprint suffix — picking any two of the three nets
        # would misidentify which are bridged. Skip until per-pin state
        # resolution is available.
        if len(nets_straddled) != 2 or state not in ("bridged", "open"):
            continue
        a, b = nets_straddled[0], nets_straddled[1]
        jumper_bridges.setdefault(a, []).append((b, state, sj.get("reference", "")))
        jumper_bridges.setdefault(b, []).append((a, state, sj.get("reference", "")))

    def _has_direct_source(net_info: dict, net_name: str) -> bool:
        # Direct power_out pin anywhere on the net, OR an explicit PWR_FLAG
        # (#FLG) tied to it, OR the rail is a regulator output.
        # NOTE: #PWR symbols are KiCad power port instances; they appear as
        # power_in in the analyzer and are NOT treated as sources here.
        for p in net_info.get("pins", []):
            if p.get("pin_type") == "power_out":
                return True
            comp = p.get("component") or ""
            if comp.startswith("#FLG"):
                # PWR_FLAG explicit declaration — ERC source marker.
                return True
        return net_name in reg_output_nets

    def _power_rail(net_name: str, net_info: dict) -> bool:
        # "Power rail" = named like a rail OR has any power_in pin on it.
        if net_name.startswith("__unnamed_"):
            return False
        if is_power_net_name(net_name, None):
            return True
        return any(p.get("pin_type") == "power_in"
                   for p in net_info.get("pins", []))

    for net_name, net_info in nets.items():
        if not _power_rail(net_name, net_info):
            continue
        if is_ground_name(net_name):
            continue  # ground handled elsewhere
        if _has_direct_source(net_info, net_name):
            continue  # sourced directly, nothing to report

        # No direct source. Trace one hop through jumpers.
        jumper_paths = jumper_bridges.get(net_name, [])
        bridged_sources: list[tuple[str, str]] = []   # (neighbour, jumper_ref)
        open_sources: list[tuple[str, str]] = []
        for neighbour, state, jref in jumper_paths:
            neighbour_info = nets.get(neighbour, {})
            if not neighbour_info:
                continue
            if _has_direct_source(neighbour_info, neighbour):
                if state == "bridged":
                    bridged_sources.append((neighbour, jref))
                else:  # open
                    open_sources.append((neighbour, jref))

        if bridged_sources:
            # Rail has an upstream source via a closed-by-default jumper.
            # That's functional out of the box; record it as info.
            neighbours = ", ".join(f"{n} via {j}" for n, j in bridged_sources)
            findings.append({
                "detector": "audit_rail_sources",
                "rule_id": "RS-001",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "category": "power",
                "summary": (f"{net_name} sourced via bridged solder jumper "
                            f"({neighbours})"),
                "description": (f"Net {net_name} has no direct power_out "
                                f"pin or PWR_FLAG, but reaches a sourced "
                                f"net through a bridged-by-default solder "
                                f"jumper. Functional out of the box."),
                "components": [j for _, j in bridged_sources],
                "nets": [net_name] + [n for n, _ in bridged_sources],
                "pins": [],
                "source_path": "bridged_jumper",
                "bridged_neighbours": [n for n, _ in bridged_sources],
                "recommendation": (
                    "No action. If you later score the jumper, this rail "
                    "will lose its source."),
                "report_context": {
                    "section": "Power — Rail Sources",
                    "impact": ("Rail functions without user action; "
                               "dependent on bridged jumper."),
                    "standard_ref": "",
                },
                "provenance": make_provenance("rs_rail_audit", "deterministic", [j for _, j in bridged_sources]),
            })
            continue

        if open_sources:
            neighbours = ", ".join(f"{n} via {j}" for n, j in open_sources)
            findings.append({
                "detector": "audit_rail_sources",
                "rule_id": "RS-002",
                "severity": "error",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "category": "power",
                "summary": (f"{net_name} has no source unless user solders "
                            f"a jumper ({neighbours})"),
                "description": (f"Net {net_name} has no power_out pin and "
                                f"no PWR_FLAG; the only potential source "
                                f"lies across an OPEN-by-default solder "
                                f"jumper. Board will not power up on this "
                                f"rail until the user solders the jumper "
                                f"pads."),
                "components": [j for _, j in open_sources],
                "nets": [net_name] + [n for n, _ in open_sources],
                "pins": [],
                "source_path": "open_jumper",
                "open_neighbours": [n for n, _ in open_sources],
                "recommendation": (
                    "Confirm that leaving this jumper open is the intended "
                    "factory-default. If the rail should be live out of "
                    "the box, swap the jumper symbol/footprint to a "
                    "bridged variant or add a direct connection."),
                "report_context": {
                    "section": "Power — Rail Sources",
                    "impact": ("Board will not function on this rail until "
                               "user closes the solder jumper."),
                    "standard_ref": "",
                },
                "provenance": make_provenance("rs_rail_audit", "deterministic", [j for _, j in open_sources]),
            })
            continue

        # No source at all — direct or through any jumper.
        findings.append({
            "detector": "audit_rail_sources",
            "rule_id": "RS-001",
            "severity": "warning",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "category": "power",
            "summary": f"{net_name} has no declared source",
            "description": (f"Net {net_name} carries power_in pins but has "
                            "no power_out pin, no PWR_FLAG, no regulator "
                            "output mapping, and no bridged solder jumper "
                            "path to a sourced net."),
            "components": [],
            "nets": [net_name],
            "pins": [p.get("component", "") + "." + p.get("pin_number", "")
                     for p in net_info.get("pins", [])
                     if p.get("pin_type") == "power_in"][:10],
            "source_path": "none",
            "recommendation": (
                "Add a PWR_FLAG to declare the rail as externally powered "
                "(e.g. from a connector) or trace the rail back to a "
                "regulator output. If the source lives on another sheet, "
                "promote the net name to a global label."),
            "report_context": {
                "section": "Power — Rail Sources",
                "impact": ("Rail has no source visible to the analyser; "
                           "likely a wiring gap or missing PWR_FLAG."),
                "standard_ref": "",
            },
            "provenance": make_provenance("rs_rail_audit", "deterministic", []),
        })

    return findings


# ---------------------------------------------------------------------------
# Global label aliases (LB-001)
# ---------------------------------------------------------------------------

def detect_label_aliases(ctx: AnalysisContext) -> list[dict]:
    """Flag nets carrying two or more distinct global / hierarchical labels.

    KiCad happily lets you place both ``SLS1`` and ``RS1P`` on the same
    physical wire. The net-name resolution picks one, but the other is
    still 'real' in the sense that a human reading the schematic sees
    both — and a future refactor that renames one silently decouples
    them. Severity stays INFO because it's a maintainability risk, not
    a functional defect.

    Reads ``nets[name].labels`` populated by ``build_net_map`` — each entry
    is ``{name, type}`` where ``type`` is one of
    ``global_label / hierarchical_label / label / directive_label``.
    """
    findings: list[dict] = []
    nets = ctx.nets or {}
    for net_name, net_info in nets.items():
        applied = net_info.get("labels") or []
        # Only global and hierarchical labels cross sheets — local labels
        # are by design wire-scoped and not aliased outside their sheet.
        cross_sheet = [lbl for lbl in applied
                       if lbl.get("type") in
                           ("global_label", "hierarchical_label")]
        names = sorted({str(lbl.get("name", "")) for lbl in cross_sheet
                        if lbl.get("name")})
        if len(names) < 2:
            continue
        # Skip power-rail aliases: labels on GND / VCC / +3.3V / etc. are
        # almost always documentation tags for subnodes of the power net
        # (e.g. Kelvin-shunt returns labelled at the star point), not
        # namespace collisions. The LB-001 rule targets *maintainability*
        # risk — renaming a power rail label is a deliberate act, not a
        # silent decoupling. If the user genuinely needs to audit
        # power-net label entropy, a separate rule (LB-002) could be
        # added later; for now we treat this as noise.
        if is_power_net_name(net_name, None) or is_ground_name(net_name):
            continue
        findings.append({
            "detector": "detect_label_aliases",
            "rule_id": "LB-001",
            "severity": "info",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "category": "labels",
            "summary": (f"Net {net_name} has multiple global/hierarchical "
                        f"labels: {', '.join(names)}"),
            "description": (f"Net {net_name!r} is labelled with multiple "
                            f"names: {', '.join(names)}. KiCad treats this "
                            f"as one electrical net, but a future refactor "
                            f"that renames one label without the other "
                            f"silently decouples the two halves."),
            "components": [],
            "nets": [net_name],
            "pins": [],
            "aliases": names,
            "label_count": len(cross_sheet),
            "recommendation": (
                "Pick the canonical name and remove the other labels, OR "
                "document the alias intentionally (e.g. an expressly named "
                "test point). If this is a cross-sheet connection via both "
                "global and hierarchical labels, prefer one or the other "
                "style consistently."),
            "report_context": {
                "section": "Labels",
                "impact": "Maintainability — silent alias across future edits.",
                "standard_ref": "",
            },
            "provenance": make_provenance("lb_multi_label", "deterministic", []),
        })
    return findings


# ---------------------------------------------------------------------------
# IC power pin DC path audit (PP-001)
# ---------------------------------------------------------------------------

def audit_power_pin_dc_paths(ctx: AnalysisContext,
                             solder_jumpers: list[dict] | None = None
                             ) -> list[dict]:
    """For every IC power_in pin, prove a DC path to a power rail exists.

    A power_in pin that only reaches ground through a capacitor is
    AC-coupled — the IC's supply floats DC, ERC is silent, and the
    board behaves unpredictably. Walk the net graph starting at each
    power_in pin, crossing:
      - wires on the same net                           (free)
      - resistors with parsed value <= 1 Ω              (bridge)
      - inductors / ferrite beads                       (bridge)
      - solder jumpers with default_state='bridged'    (bridge)
    and REJECT crossing capacitors. If no named power rail is reachable
    within 2 hops, emit PP-001 at severity=high.
    """
    findings: list[dict] = []
    nets = ctx.nets or {}
    components = {c.get("reference"): c for c in (ctx.components or [])}

    # Map component ref -> list of (pin_number, net_name, pin_type) for net hops.
    ref_pins: dict[str, list[tuple[str, str, str]]] = {}
    for net_name, net_info in nets.items():
        for p in net_info.get("pins", []):
            ref = p.get("component") or ""
            if not ref:
                continue
            ref_pins.setdefault(ref, []).append(
                (str(p.get("pin_number", "")), net_name,
                 str(p.get("pin_type", ""))))

    # Component-type-based bridge predicate.
    def _bridges_dc(ref: str) -> bool:
        c = components.get(ref) or {}
        t = (c.get("type") or c.get("category") or "").lower()
        if t in ("inductor", "ferrite_bead"):
            return True
        if t == "resistor":
            # Small value resistors count as DC-conductive.
            v = parse_value(c.get("value", ""), component_type="resistor")
            if v is None:
                # 0R / DNP heuristic
                val = (c.get("value") or "").strip().lower().replace(" ", "")
                if val in ("0", "0r", "0ohm", "0ohms"):
                    return True
                return False
            return v <= 1.0
        if t == "jumper":
            for sj in (solder_jumpers or []):
                if sj.get("reference") == ref:
                    return sj.get("default_state") == "bridged"
            return False
        return False

    def _is_capacitor(ref: str) -> bool:
        c = components.get(ref) or {}
        return (c.get("type") or "").lower() == "capacitor"

    def _is_connector(ref: str) -> bool:
        """Return True if ref looks like a connector (external supply entry point)."""
        c = components.get(ref) or {}
        t = (c.get("type") or "").lower()
        if t in ("connector",):
            return True
        # J<digit> / P<digit> reference prefixes are conservative connector
        # heuristics; other connector refs must carry type="connector" in the
        # component dict (caught by the preceding check).
        return bool(ref and ref[0] in ("J", "P") and ref[1:2].isdigit())

    # Build per-net connector presence set — nets with connectors may have
    # external DC supply; suppress PP-001 for those nets to avoid false
    # positives on boards where the power comes in from a header.
    nets_with_connector: set[str] = set()
    for net_name_c, net_info_c in nets.items():
        for p in net_info_c.get("pins", []):
            cref = p.get("component") or ""
            if _is_connector(cref):
                nets_with_connector.add(net_name_c)
                break

    MAX_HOPS = 2
    # Track (ref, pin) pairs already checked to avoid duplicate findings.
    seen: set[tuple[str, str]] = set()

    for net_name, net_info in nets.items():
        for p in net_info.get("pins", []):
            if p.get("pin_type") != "power_in":
                continue
            ref = p.get("component") or ""
            pin_num = str(p.get("pin_number", ""))
            pin_name = p.get("pin_name") or ""
            if not ref or ref.startswith("#"):
                continue  # PWR_FLAG / power symbol virtuals

            # Ground pins (VSS, GND, AGND, SGND, VSSA, etc.) are already
            # at the ground reference — they don't need a path to a positive
            # power rail. Flagging them would be a false positive.
            if ctx.is_ground(net_name):
                continue

            # If a connector is on this net, external DC supply is plausible.
            # Suppress — the RS-001 rule handles "no declared source" separately.
            if net_name in nets_with_connector:
                continue

            key = (ref, pin_num)
            if key in seen:
                continue
            seen.add(key)

            frontier: set[str] = {net_name}
            visited: set[str] = {net_name}
            # A power_in pin directly on a named power rail already has DC.
            reached_rail = (ctx.is_power_net(net_name)
                            and not ctx.is_ground(net_name))
            # Track whether any capacitor blocked the walk — only emit PP-001
            # when a cap-only path exists (not just "no source declared").
            # That distinguishes the AC-coupling bug from missing-PWR_FLAG
            # which RS-001 already covers.
            saw_capacitor_on_path: bool = False
            for _hop in range(MAX_HOPS):
                if reached_rail:
                    break
                next_frontier: set[str] = set()
                for cur_net in frontier:
                    cur_info = nets.get(cur_net, {})
                    for cp in cur_info.get("pins", []):
                        cref = cp.get("component") or ""
                        if not cref or cref == ref:
                            continue
                        if _is_capacitor(cref):
                            saw_capacitor_on_path = True
                            continue
                        if not _bridges_dc(cref):
                            continue
                        for _other_pn, other_net, _pt in ref_pins.get(cref, []):
                            if other_net == cur_net:
                                continue
                            if other_net in visited:
                                continue
                            visited.add(other_net)
                            next_frontier.add(other_net)
                            if (ctx.is_power_net(other_net)
                                    and not ctx.is_ground(other_net)):
                                reached_rail = True
                frontier = next_frontier
                if not frontier:
                    break

            if reached_rail:
                continue
            # Only emit if a capacitor was present on the path — this is the
            # specific "AC-coupled supply" wiring bug PP-001 targets. Pins on
            # nets with no source at all (no PWR_FLAG, no regulator output)
            # are already flagged by RS-001 and don't need a second finding.
            if not saw_capacitor_on_path:
                continue

            pin_label = f"{ref}.{pin_num}"
            if pin_name:
                pin_label += f" ({pin_name})"
            findings.append({
                "detector": "audit_power_pin_dc_paths",
                "rule_id": "PP-001",
                "severity": "error",
                "confidence": "heuristic",
                "evidence_source": "topology",
                "category": "power",
                "summary": (f"IC power pin {pin_label} has no DC path to a "
                            f"power rail (net {net_name!r})"),
                "description": (f"Pin {pin_label} is type=power_in on net "
                                f"{net_name!r}. Graph walk (≤{MAX_HOPS} "
                                f"hops, rejecting capacitor edges, "
                                f"accepting resistors≤1Ω, inductors, "
                                f"ferrite beads, bridged solder jumpers) "
                                f"did not reach a named power rail. The pin "
                                f"is likely AC-coupled to ground only — "
                                f"the IC will not power up reliably."),
                "components": [ref],
                "nets": sorted(visited)[:10],
                "pins": [pin_label],
                "start_net": net_name,
                "visited_nets": sorted(visited),
                "source_path": "none",
                "recommendation": (
                    "Verify the schematic for this pin: the DC route must "
                    "go through a conducting element (direct wire, 0Ω "
                    "resistor, inductor, ferrite bead, or bridged solder "
                    "jumper) — not a capacitor. If the intent was to tie "
                    "VCC through an LC filter, add the missing inductor "
                    "or 0Ω in series."),
                "report_context": {
                    "section": "Power — DC Continuity",
                    "impact": "IC supply floats DC; board will not run.",
                    "standard_ref": "",
                },
                "provenance": make_provenance("pp_dc_path_audit", "deterministic", [ref]),
            })

    return findings

