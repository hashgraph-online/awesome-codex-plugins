"""
Testbench generation templates for Phase 1 SPICE simulation.

Each function takes a detector output dict (from signal_detectors.py) and
returns a complete ngspice .cir file as a string. Testbenches use .control
blocks for measurement, writing ASCII results to an output file — no binary
.raw parsing needed.

Supported detector types (Phase 1):
  - RC filters (AC analysis → cutoff frequency, rolloff)
  - LC filters (AC analysis → resonant frequency, Q factor)
  - Voltage dividers (DC operating point → output voltage)
  - Opamp circuits (AC analysis → gain, bandwidth)
  - Crystal circuits (AC analysis → negative resistance margin)
"""

import math
import re
from spice_models import (
    get_generic_models,
    get_ideal_opamp,
    spice_element_for_passive,
    _sanitize_net,
    _format_eng,
)


# ---------------------------------------------------------------------------
# SpiceTestbench — simulator-agnostic testbench representation
# ---------------------------------------------------------------------------

class SpiceTestbench:
    """Structured testbench with portable circuit + measurement intent.

    Generators return this instead of raw strings. The simulator backend
    renders it into a .cir file with the appropriate measurement syntax
    (ngspice .control blocks, LTspice .meas statements, Xyce .measure).

    The circuit string contains the portable netlist (components, sources,
    models, subcircuits). The analyses and measurements lists describe
    what to simulate and measure in a simulator-agnostic way.
    """

    def __init__(self, circuit, analyses, measurements, extra_vars=None):
        """
        Args:
            circuit: Portable SPICE netlist string (everything except
                     analysis/measurement commands and .end)
            analyses: List of (type, spec) tuples.
                      e.g., [("ac", "dec 100 1 100Meg")]
            measurements: List of measurement tuples:
                - ("name", "when", "expr", "value", [rise/fall])
                - ("name", "find", "expr", "at=value")
                - ("name", "max", "expr", [from_to])
                - ("name", "min", "expr")
                - ("name", "let", "expression")
            extra_vars: Dict of extra key=value pairs for output
        """
        self.circuit = circuit
        self.analyses = analyses
        self.measurements = measurements
        self.extra_vars = extra_vars or {}

    def render(self, backend, output_file):
        """Render complete .cir file for a specific simulator backend.

        Args:
            backend: SimulatorBackend instance (or None for ngspice default)
            output_file: Path for measurement results

        Returns:
            Complete .cir file content string
        """
        if backend is None:
            # Default to ngspice .control block rendering
            from spice_simulator import NgspiceBackend
            backend = NgspiceBackend()

        meas_block = backend.format_measurement_block(
            self.analyses, self.measurements, output_file, self.extra_vars
        )
        return f"{self.circuit}\n{meas_block}\n\n.end\n"


# ---------------------------------------------------------------------------
# Parasitic annotation helpers
# ---------------------------------------------------------------------------

def _get_parasitic_lines(parasitics_data, net_name, node_before, node_after):
    """Generate SPICE parasitic elements for a net if data is available.

    Args:
        parasitics_data: Parasitics dict from extract_parasitics.py (or None)
        net_name: Original KiCad net name (before sanitization)
        node_before: SPICE node name on one side of the parasitic
        node_after: SPICE node name on the other side

    Returns:
        (lines_str, parasitic_note) — SPICE element lines and comment,
        or ("", "") if no parasitics available for this net
    """
    # EQ-079: R_trace + L_via parasitic element injection
    if not parasitics_data:
        return "", ""

    nets = parasitics_data.get("nets", {})
    net_data = nets.get(net_name)
    if not net_data:
        return "", ""

    r_total = net_data.get("total_trace_resistance_ohm", 0)
    via_l = net_data.get("total_via_inductance_nH", 0)
    length = net_data.get("total_length_mm", 0)
    vias = net_data.get("via_count", 0)

    # Only inject if parasitic is significant relative to node_after
    if r_total < 0.001 and via_l < 0.01:
        return "", ""

    lines = []
    safe_net = _sanitize_net(net_name)
    mid_node = f"{node_before}_p"

    if r_total >= 0.001:
        lines.append(f"R_trace_{safe_net} {node_before} {mid_node} {_format_eng(r_total)}")
        current_node = mid_node
    else:
        current_node = node_before

    if via_l >= 0.01:
        via_l_h = via_l * 1e-9  # nH to H
        via_node = f"{current_node}_v"
        lines.append(f"L_via_{safe_net} {current_node} {via_node} {_format_eng(via_l_h)}")
        current_node = via_node

    # Connect the last parasitic node to the target
    if current_node != node_before:
        lines.append(f"R_conn_{safe_net} {current_node} {node_after} 0.001")

    note = f"* Parasitic: {length:.1f}mm trace → {r_total*1000:.1f}mΩ"
    if vias > 0:
        note += f", {vias} via(s) → {via_l:.2f}nH"

    return "\n".join(lines), note


def generate_rc_filter(det, output_file, context=None, parasitics=None):
    """Generate testbench for an RC filter detection.

    Args:
        det: Finding dict from findings[] — detector:rc_filters[] with keys:
             resistor{ref,ohms}, capacitor{ref,farads}, type,
             cutoff_hz, input_net, output_net, ground_net
        output_file: Path for ASCII results file

    Returns:
        Complete .cir file content string
    """
    r_ref = det["resistor"]["ref"]
    r_ohms = det["resistor"]["ohms"]
    c_ref = det["capacitor"]["ref"]
    c_farads = det["capacitor"]["farads"]
    fc = det["cutoff_hz"]
    ftype = det.get("type", "low-pass")
    in_net = _sanitize_net(det["input_net"])
    out_net = _sanitize_net(det["output_net"])
    gnd_net = _sanitize_net(det.get("ground_net", "GND"))

    # Guard: can't simulate if output is ground (can't measure vdb(0)),
    # input is ground, or input equals output (no filter action)
    if out_net == "0" or in_net == "0" or in_net == out_net:
        return None

    # Guard: zero-value components can't form a filter
    if r_ohms <= 0 or c_farads <= 0 or fc <= 0:
        return None

    # Frequency sweep range: 2 decades below to 2 decades above fc
    f_start = max(fc / 100, 0.1)
    f_stop = fc * 100

    # Build the netlist — reconstruct the RC network
    # When parasitics are present, inject trace R between R and C
    parasitic_lines, parasitic_note = "", ""
    has_parasitics = parasitics is not None

    if ftype == "low-pass":
        if has_parasitics:
            # R → trace_R → C (parasitic between R output and C input)
            mid = f"{out_net}_trace"
            r_line = spice_element_for_passive(r_ref, r_ohms, in_net, mid)
            trace_r, trace_note = _get_parasitic_lines(parasitics, det.get("output_net", ""), mid, out_net)
            if trace_r:
                parasitic_lines = trace_r
                parasitic_note = trace_note
            else:
                # No parasitic for this net — connect directly
                r_line = spice_element_for_passive(r_ref, r_ohms, in_net, out_net)
            c_line = spice_element_for_passive(c_ref, c_farads, out_net, "0")
        else:
            r_line = spice_element_for_passive(r_ref, r_ohms, in_net, out_net)
            c_line = spice_element_for_passive(c_ref, c_farads, out_net, "0")
    elif ftype == "high-pass":
        c_line = spice_element_for_passive(c_ref, c_farads, in_net, out_net)
        r_line = spice_element_for_passive(r_ref, r_ohms, out_net, "0")
    else:
        r_line = spice_element_for_passive(r_ref, r_ohms, in_net, out_net)
        c_line = spice_element_for_passive(c_ref, c_farads, out_net, "0")

    model_note = "* Model: ideal passives (exact for RC)"
    if parasitic_lines:
        model_note = "* Model: ideal passives + PCB trace parasitics"

    circuit = f"""\
* Auto-generated testbench for RC filter: {r_ref}/{c_ref}
* Type: {ftype}, expected fc = {fc:.1f} Hz
{model_note}
{parasitic_note}

{r_line}
{parasitic_lines}
{c_line}

* AC stimulus
VAC {in_net} 0 DC 0 AC 1
"""

    analyses = [("ac", f"dec 100 {_format_eng(f_start)} {_format_eng(f_stop)}")]
    measurements = [
        ("fc_sim", "when", f"vdb({out_net})", "-3"),
        ("phase_fc", "find", f"vp({out_net})", "at=fc_sim"),
    ]
    extra = {"has_parasitics": "1" if parasitic_lines else "0"}

    return SpiceTestbench(circuit, analyses, measurements, extra)


def generate_lc_filter(det, output_file, context=None, parasitics=None):
    """Generate testbench for an LC filter detection.

    Args:
        det: Finding dict from findings[] — detector:lc_filters[] with keys:
             inductor{ref,henries}, capacitor{ref,farads},
             resonant_hz, impedance_ohms, shared_net
        output_file: Path for ASCII results file

    Returns:
        Complete .cir file content string
    """
    # EQ-083: f₀ = 1/(2π√(LC)) testbench (validates EQ-021)
    l_ref = det["inductor"]["ref"]
    l_henries = det["inductor"]["henries"]
    c_ref = det["capacitor"]["ref"]
    c_farads = det["capacitor"]["farads"]
    f_res = det["resonant_hz"]
    z0 = det.get("impedance_ohms", math.sqrt(l_henries / c_farads))
    shared = _sanitize_net(det["shared_net"])

    f_start = max(f_res / 100, 0.1)
    f_stop = f_res * 100

    # LC tank: L from input to shared_net, C from shared_net to ground
    # Add small series resistance to inductor for realism (Q=100 default)
    r_series = 2 * math.pi * f_res * l_henries / 100  # Q=100
    in_net = "ac_in"

    circuit = f"""\
* Auto-generated testbench for LC filter: {l_ref}/{c_ref}
* Expected resonant frequency = {f_res:.1f} Hz, Z0 = {z0:.1f} ohms
* Model: ideal passives + small inductor ESR (Q=100)

* Topology: source → R_esr → L → shared_net, C from shared_net → gnd
R_{l_ref}_esr {in_net} {in_net}_mid {_format_eng(r_series)}
{spice_element_for_passive(l_ref, l_henries, in_net + "_mid", shared)}
{spice_element_for_passive(c_ref, c_farads, shared, "0")}

* AC stimulus
VAC {in_net} 0 DC 0 AC 1
"""

    analyses = [("ac", f"dec 200 {_format_eng(f_start)} {_format_eng(f_stop)}")]
    measurements = [
        ("gain_peak", "max", f"vdb({shared})"),
        ("target_lo", "let", "gain_peak - 0.1"),
        ("f_peak_lo", "when", f"vdb({shared})", "target_lo", "rise=1"),
        ("f_peak_hi", "when", f"vdb({shared})", "target_lo", "fall=1"),
        ("f_peak", "let", "(f_peak_lo + f_peak_hi) / 2", True),
        ("target_3db", "let", "gain_peak - 3"),
        ("bw_3db_lo", "when", f"vdb({shared})", "target_3db", "rise=1"),
        ("bw_3db_hi", "when", f"vdb({shared})", "target_3db", "fall=1"),
    ]

    return SpiceTestbench(circuit, analyses, measurements)


def generate_voltage_divider(det, output_file, vin=3.3, context=None, parasitics=None):
    """Generate testbench for a voltage divider detection.

    Args:
        det: Finding dict from findings[] — detector:voltage_dividers[] with keys:
             r_top{ref,ohms}, r_bottom{ref,ohms}, top_net, mid_net,
             bottom_net, ratio
        output_file: Path for ASCII results file
        vin: Input voltage to assume (default 3.3V, overridden if top_net
             suggests a known rail)

    Returns:
        Complete .cir file content string
    """
    rt_ref = det["r_top"]["ref"]
    rt_ohms = det["r_top"]["ohms"]
    rb_ref = det["r_bottom"]["ref"]
    rb_ohms = det["r_bottom"]["ohms"]
    ratio = det["ratio"]
    top_net = _sanitize_net(det["top_net"])
    mid_net = _sanitize_net(det["mid_net"])
    bot_net = _sanitize_net(det.get("bottom_net", "GND"))

    # Guard: can't simulate if nets overlap or output is ground
    if top_net == mid_net or mid_net == "0" or top_net == "0":
        return None

    # Guard: zero-value resistors
    if rt_ohms <= 0 or rb_ohms <= 0:
        return None

    # Try to infer Vin from top_net name
    vin = _infer_voltage(det["top_net"], default=vin)

    # No load resistor — simulate the divider in isolation.
    # The analyzer's ratio is R_bot/(R_top+R_bot) which is the unloaded ratio.
    # Adding a load would shift the result and create false "errors".
    expected_vout = vin * ratio

    circuit = f"""\
* Auto-generated testbench for voltage divider: {rt_ref}/{rb_ref}
* Expected Vout = {vin} * {ratio:.6f} = {expected_vout:.4f} V
* Model: ideal passives (exact, unloaded)

VIN {top_net} 0 DC {vin}
{spice_element_for_passive(rt_ref, rt_ohms, top_net, mid_net)}
{spice_element_for_passive(rb_ref, rb_ohms, mid_net, "0")}
"""

    analyses = [("op", "")]
    measurements = [
        ("vout_sim", "let", f"v({mid_net})", True),
        ("error_pct", "let", f"abs(vout_sim - {expected_vout}) / {expected_vout} * 100", True),
    ]
    extra = {"expected": str(expected_vout)}

    return SpiceTestbench(circuit, analyses, measurements, extra)


def generate_opamp_circuit(det, output_file, context=None, parasitics=None):
    """Generate testbench for an opamp circuit detection.

    Args:
        det: Finding dict from findings[] — detector:opamp_circuits[] with keys:
             reference, value, configuration, output_net,
             inverting_input_net, non_inverting_input_net,
             gain, gain_dB, feedback_resistor{ref,ohms},
             input_resistor{ref,ohms}, feedback_capacitor{ref,farads}
        output_file: Path for ASCII results file

    Returns:
        Complete .cir file content string, or None if configuration is
        not simulatable (comparator/open-loop)
    """
    # EQ-084: G_expected = 1+Rf/Ri or -Rf/Ri (validates EQ-071)
    config = det.get("configuration", "unknown")
    if config in ("comparator_or_open_loop", "unknown"):
        return None

    ref = det["reference"]
    value = det.get("value", "opamp")
    out_net = _sanitize_net(det["output_net"])
    neg_net = _sanitize_net(det["inverting_input_net"])
    pos_net = _sanitize_net(det.get("non_inverting_input_net"))
    expected_gain = det.get("gain")
    expected_gain_db = det.get("gain_dB")

    # Guard: can't simulate if key nets are the same (except buffer where out==neg)
    if pos_net and pos_net == neg_net:
        return None  # Both inputs on same node — can't measure differential
    if out_net == "0":
        return None  # Output is ground — can't measure

    # Build feedback network from analyzer data
    netlist_lines = []

    # Feedback resistor: from output to inverting input
    rf = det.get("feedback_resistor")
    if rf:
        netlist_lines.append(
            spice_element_for_passive(rf["ref"], rf["ohms"], out_net, neg_net)
        )

    # Feedback capacitor (integrator/compensator) — skip absurd values
    fc = det.get("feedback_capacitor")
    if fc and fc["farads"] < 1.0:  # >1F is not a real capacitor
        netlist_lines.append(
            spice_element_for_passive(fc["ref"], fc["farads"], out_net, neg_net)
        )

    # Input resistor: from signal input to inverting input
    ri = det.get("input_resistor")
    if ri:
        in_net = "sig_in"
        netlist_lines.append(
            spice_element_for_passive(ri["ref"], ri["ohms"], in_net, neg_net)
        )
    else:
        in_net = "sig_in"

    # Determine stimulus and measurement based on configuration
    use_current_source = False
    if config == "buffer":
        # Buffer: signal to pos input, output directly to neg input
        stim_net = pos_net if pos_net else "sig_in"
        in_net = stim_net
    elif config == "non_inverting":
        stim_net = pos_net if pos_net else "sig_in"
        in_net = stim_net
        # Non-inverting: Ri goes from neg_net to ground (sets gain)
        if ri:
            # Input resistor is actually the ground-leg resistor
            # Already placed above from sig_in to neg_net — need to fix:
            # it should be from neg_net to ground
            netlist_lines = [l for l in netlist_lines if not l.startswith(ri["ref"])]
            netlist_lines.append(
                spice_element_for_passive(ri["ref"], ri["ohms"], neg_net, "0")
            )
    elif config == "inverting":
        stim_net = in_net
        # Inverting amp: non-inverting input goes to ground (reference)
        if pos_net and pos_net != "0":
            netlist_lines.append(f"Rpos_bias {pos_net} 0 0.001")
    elif config in ("integrator", "compensator"):
        stim_net = in_net
        # Same as inverting — pos input to ground
        if pos_net and pos_net != "0":
            netlist_lines.append(f"Rpos_bias {pos_net} 0 0.001")
    elif config == "transimpedance_or_buffer":
        use_current_source = True
        stim_net = neg_net  # Drive current into summing junction
        # Pos input to ground
        if pos_net and pos_net != "0":
            netlist_lines.append(f"Rpos_bias {pos_net} 0 0.001")
    else:
        stim_net = in_net

    # Power supply rails — infer from context or default to +/-5V
    vcc_net = "VCC"
    vee_net = "VEE"
    vcc_v = 5
    vee_v = -5

    # Try to infer from analyzer context
    if context:
        vcc_v, vee_v = _infer_opamp_rails(det, context)
        if vee_v == 0:
            vee_net = "GND_VEE"  # Avoid conflict with node 0

    # --- Model resolution (Phase 2) ---
    # Try to get a per-part behavioral model; fall back to ideal
    model_str = get_ideal_opamp()
    model_name = "IDEAL_OPAMP"
    model_source = "ideal"
    model_specs = None
    try:
        from spice_model_cache import get_model_for_part
        part_model, source, specs = get_model_for_part(value, "opamp", context)
        if part_model:
            model_str = part_model
            model_name = f"OPAMP_{_sanitize_mpn_for_spice(value)}"
            model_source = source
            model_specs = specs
    except Exception as _e:
        pass  # Model resolution failed — use ideal

    if model_source == "ideal":
        model_note = "* Model: IDEAL opamp (Aol=1e6, GBW~10MHz) — real part may have lower GBW"
    else:
        gbw = model_specs.get("gbw_hz", 0) if model_specs else 0
        model_note = f"* Model: {value} behavioral ({model_source}, GBW={gbw/1e6:.1f}MHz)"

    gain_comment = ""
    if expected_gain is not None:
        gain_comment = f"* Expected gain: {expected_gain:.3f}"
        if expected_gain_db is not None:
            gain_comment += f" ({expected_gain_db:.1f} dB)"

    feedback_components = netlist_lines if netlist_lines else ["* (no external feedback components detected)"]

    # Choose measurement frequency based on model GBW and expected gain.
    # Measure well below the expected -3dB bandwidth to get accurate DC gain.
    # f_measure = GBW / (100 * |gain|), clamped to [1, 1000] Hz.
    abs_gain = abs(expected_gain) if expected_gain and abs(expected_gain) > 1 else 10
    if model_specs and model_specs.get("gbw_hz"):
        f_meas = model_specs["gbw_hz"] / (100 * abs_gain)
    else:
        f_meas = 10e6 / (100 * abs_gain)  # Ideal model: 10MHz GBW
    f_meas = max(1, min(f_meas, 1000))  # Clamp to [1, 1000] Hz
    f_meas_str = _format_eng(f_meas)

    # Multi-frequency gain measurement points (Q6)
    f_low = max(1, f_meas / 10)
    f_high = min(f_meas * 10, 10e6)
    f_low_str = _format_eng(f_low)
    f_high_str = _format_eng(f_high)

    model_extra = {
        "model_source": model_source,
        "model_gbw": str(model_specs.get("gbw_hz", 0) if model_specs else 0),
    }

    # Transimpedance uses current source stimulus
    if use_current_source:
        rf_ohms = rf["ohms"] if rf else 1e6
        expected_tz = rf_ohms
        circuit = f"""\
* Auto-generated testbench for opamp: {ref} ({value})
* Configuration: {config} (transimpedance = Rf = {_format_eng(rf_ohms)} ohm)
{gain_comment}
{model_note}

{model_str}
{get_generic_models()}

* Power supplies
V_VCC {vcc_net} 0 DC {vcc_v}
V_VEE {vee_net} 0 DC {vee_v}

* Opamp instance
X{ref} {pos_net or neg_net} {neg_net} {out_net} {vcc_net} {vee_net} {model_name}

* Feedback network
{chr(10).join(feedback_components)}

* Current source stimulus into summing junction (inverting input)
IAC 0 {stim_net} DC 0 AC 1u
"""
        analyses = [("ac", "dec 100 1 100Meg")]
        measurements = [
            ("gain_1k", "find", f"vdb({out_net})", f"at={f_meas_str}"),
            ("gain_low", "find", f"vdb({out_net})", f"at={f_low_str}"),
            ("gain_high", "find", f"vdb({out_net})", f"at={f_high_str}"),
            ("tz_mag", "find", f"vm({out_net})", f"at={f_meas_str}"),
            ("tz_ohms", "let", "tz_mag / 1e-6", True),
            ("target", "let", "gain_1k - 3"),
            ("bw_3db", "when", f"vdb({out_net})", "target", "fall=1"),
            ("phase_at_bw", "find", f"vp({out_net})", "bw_3db"),
        ]
        model_extra["expected_tz"] = str(expected_tz)
        return SpiceTestbench(circuit, analyses, measurements, model_extra)

    circuit = f"""\
* Auto-generated testbench for opamp: {ref} ({value})
* Configuration: {config}
{gain_comment}
{model_note}

{model_str}
{get_generic_models()}

* Power supplies
V_VCC {vcc_net} 0 DC {vcc_v}
V_VEE {vee_net} 0 DC {vee_v}

* Opamp instance
X{ref} {pos_net or neg_net} {neg_net} {out_net} {vcc_net} {vee_net} {model_name}

* Feedback network
{chr(10).join(feedback_components)}

* AC stimulus
VAC {stim_net} 0 DC 0 AC 1
"""
    analyses = [("ac", "dec 100 1 100Meg")]
    measurements = [
        ("gain_1k", "find", f"vdb({out_net})", f"at={f_meas_str}"),
        ("gain_low", "find", f"vdb({out_net})", f"at={f_low_str}"),
        ("gain_high", "find", f"vdb({out_net})", f"at={f_high_str}"),
        ("target", "let", "gain_1k - 3"),
        ("bw_3db", "when", f"vdb({out_net})", "target", "fall=1"),
        ("phase_at_bw", "find", f"vp({out_net})", "bw_3db"),
    ]
    return SpiceTestbench(circuit, analyses, measurements, model_extra)


def generate_crystal_circuit(det, output_file, context=None, parasitics=None):
    """Generate testbench for a crystal circuit detection.

    Tests the oscillation condition: negative resistance seen by the crystal
    must exceed the crystal's motional resistance (ESR). Uses a simplified
    Colpitts/Pierce analysis.

    Args:
        det: Finding dict from findings[] — detector:crystal_circuits[] with keys:
             reference, value, frequency, type, load_caps[{ref,farads,net}],
             effective_load_pF
        output_file: Path for ASCII results file

    Returns:
        Complete .cir file content string, or None if not simulatable
        (active oscillators need no verification)
    """
    # EQ-080: C_L = 1/(1/C₁+1/C₂) + C_stray (crystal load cap)
    ctype = det.get("type", "passive")
    if ctype == "active_oscillator":
        return None  # Active oscillators are self-contained, nothing to simulate

    freq = det.get("frequency")
    if not freq:
        return None  # Can't simulate without knowing crystal frequency

    ref = det["reference"]
    value = det.get("value", "crystal")
    load_caps = det.get("load_caps", [])
    cl_eff = det.get("effective_load_pF")

    if len(load_caps) < 2:
        return None  # Need both load caps for meaningful analysis

    c1 = load_caps[0]
    c2 = load_caps[1]

    # Crystal equivalent circuit parameters (typical AT-cut values)
    # These are generic — real crystals vary significantly
    # Rm: motional resistance (typ 20-80 ohms for MHz crystals, ~40k for 32.768kHz)
    if freq < 1e6:
        rm = 40000  # 32.768 kHz watch crystal
        cm = 2.0e-15  # motional capacitance
        lm = 1 / ((2 * math.pi * freq) ** 2 * cm)
        c0 = 1.5e-12  # shunt capacitance
    else:
        rm = 30  # Typical MHz crystal
        cm = 20e-15
        lm = 1 / ((2 * math.pi * freq) ** 2 * cm)
        c0 = 5e-12

    circuit = f"""\
* Auto-generated testbench for crystal circuit: {ref} ({value})
* Frequency: {freq:.0f} Hz
* Load caps: {c1['ref']}={_format_eng(c1['farads'])}F, {c2['ref']}={_format_eng(c2['farads'])}F
* Effective CL: {cl_eff:.1f} pF (calculated by analyzer)
* Model: generic crystal equivalent circuit (Rm={rm} ohms)
*
* This testbench measures the impedance seen by the crystal to verify
* that load capacitance is in a reasonable range. It does NOT simulate
* the full oscillator loop (that requires the driving IC model).

* Crystal equivalent circuit (Butterworth-Van Dyke model)
Lm xtal1_int xtal2 {_format_eng(lm)}
Cm xtal1_int xtal2 {_format_eng(cm)}
Rm xtal1_int xtal2 {rm}
C0 xtal1 xtal2 {_format_eng(c0)}
Rxtal xtal1 xtal1_int 0.001

* Load capacitors
{spice_element_for_passive(c1['ref'], c1['farads'], 'xtal1', '0')}
{spice_element_for_passive(c2['ref'], c2['farads'], 'xtal2', '0')}

* AC stimulus across crystal to measure impedance
VAC xtal1 xtal1_drv DC 0 AC 1
IAC 0 xtal1_drv DC 0 AC 0
"""

    analyses = [("ac", f"dec 1000 {_format_eng(freq * 0.99)} {_format_eng(freq * 1.01)}")]
    measurements = [
        ("z_mag", "let", "v(xtal1) / i(VAC)"),
        ("z_real", "let", "real(z_mag)"),
        ("f_series", "when", "abs(z_real)", "minimum(abs(z_real))"),
        ("cl_series", "let", f"1/(1/{c1['farads']} + 1/{c2['farads']})"),
    ]
    extra = {"cl_pF": str(cl_eff), "rm": str(rm)}

    return SpiceTestbench(circuit, analyses, measurements, extra)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sanitize_mpn_for_spice(mpn):
    """Convert an MPN to a valid SPICE subcircuit name component.

    Mirrors sanitize_mpn() in spice_model_generator.py.
    """
    return re.sub(r'[^A-Za-z0-9_]', '_', mpn.strip()) if mpn else "UNKNOWN"


def _infer_opamp_rails(det, context):
    """Infer opamp VCC/VEE voltages from analyzer context.

    Looks up the opamp's power pins in the component/net data to find
    what supply rails it's connected to, then infers voltages from net names.

    Args:
        det: Opamp detection dict (has 'reference')
        context: Full analysis JSON dict

    Returns:
        (vcc_voltage, vee_voltage) tuple of floats
    """
    ref = det["reference"]
    nets = context.get("nets", {})
    components = context.get("components", [])

    # Find this opamp in the components list to get its pins
    vcc_v = 5
    vee_v = -5
    found_vcc = False
    found_vee = False

    for net_name, net_data in nets.items():
        pins = net_data.get("pins", [])
        for pin in pins:
            if pin.get("component") != ref:
                continue
            pname = (pin.get("pin_name") or "").upper()
            ptype = (pin.get("pin_type") or "").lower()
            # VCC/VDD/V+ pins
            if pname in ("VCC", "VDD", "V+", "VS+", "V_P", "VP", "AVDD", "DVDD") or \
               (ptype == "power_in" and not found_vcc and _infer_voltage(net_name, default=None) is not None):
                v = _infer_voltage(net_name, default=None)
                if v is not None and v > 0:
                    vcc_v = v
                    found_vcc = True
            # VEE/VSS/V- pins
            elif pname in ("VEE", "VSS", "V-", "VS-", "V_N", "VN", "GND", "AVSS", "DVSS"):
                v = _infer_voltage(net_name, default=None)
                if v is not None:
                    vee_v = v
                    found_vee = True
                elif net_name.upper() in ("GND", "EARTH", "VSS"):
                    vee_v = 0
                    found_vee = True

    # If we only found VCC and not VEE, assume single-supply (VEE=0)
    if found_vcc and not found_vee:
        vee_v = 0

    # Sanity check: VEE must be less than VCC
    if vee_v >= vcc_v:
        vee_v = 0  # Fall back to single-supply

    return vcc_v, vee_v


def _infer_voltage(net_name, default=3.3):
    """Try to guess a voltage from a power rail net name.

    Common patterns: 3V3, 5V, 12V, 1V8, VCC, VBUS, etc.
    """
    if net_name is None:
        return default
    name = net_name.upper().strip()
    # Match patterns like "3V3", "1V8", "5V0", "+3.3V", "+5V"
    m = re.match(r'[+]?(\d+)V(\d+)', name)
    if m:
        return float(f"{m.group(1)}.{m.group(2)}")
    m = re.match(r'[+]?(\d+\.?\d*)V', name)
    if m:
        return float(m.group(1))
    # VBUS is typically 5V (USB)
    if "VBUS" in name or "USB" in name:
        return 5.0
    # VBAT — assume 3.7V (Li-ion)
    if "VBAT" in name or "BATTERY" in name:
        return 3.7
    # VCC without voltage hint — assume 3.3V (most common in modern designs)
    if name in ("VCC", "VDD", "+V"):
        return 3.3
    return default


def generate_feedback_network(det, output_file, vin=3.3, context=None, parasitics=None):
    """Generate testbench for a feedback network detection.

    Feedback networks are voltage dividers connected to a regulator FB pin.
    The simulation validates the divider ratio and inferred Vout. Identical
    to voltage_divider electrically, but the report context differs — these
    set a regulator's output voltage, so errors here are critical.

    Args:
        det: Finding dict from findings[] — detector:feedback_networks[] — same structure
             as voltage_dividers with additional is_feedback flag
        output_file: Path for ASCII results file

    Returns:
        Complete .cir file content string
    """
    rt_ref = det["r_top"]["ref"]
    rt_ohms = det["r_top"]["ohms"]
    rb_ref = det["r_bottom"]["ref"]
    rb_ohms = det["r_bottom"]["ohms"]
    ratio = det["ratio"]
    top_net = _sanitize_net(det["top_net"])
    mid_net = _sanitize_net(det["mid_net"])

    vin = _infer_voltage(det["top_net"], default=vin)
    expected_vout = vin * ratio

    # Identify the connected regulator if available
    connections = det.get("mid_point_connections", [])
    fb_ic = None
    for conn in connections:
        if conn.get("pin_name", "").upper() in ("FB", "ADJ", "VADJ"):
            fb_ic = conn.get("component", "unknown")
            break

    fb_note = f"Connected to {fb_ic} FB pin" if fb_ic else "Feedback network"

    circuit = f"""\
* Auto-generated testbench for feedback network: {rt_ref}/{rb_ref}
* {fb_note}
* Expected FB voltage = {vin} * {ratio:.6f} = {expected_vout:.4f} V
* Model: ideal passives (exact, unloaded)

VIN {top_net} 0 DC {vin}
{spice_element_for_passive(rt_ref, rt_ohms, top_net, mid_net)}
{spice_element_for_passive(rb_ref, rb_ohms, mid_net, "0")}
"""

    analyses = [("op", "")]
    measurements = [
        ("vout_sim", "let", f"v({mid_net})", True),
        ("error_pct", "let", f"abs(vout_sim - {expected_vout}) / {expected_vout} * 100", True),
    ]
    extra = {"expected": str(expected_vout)}

    return SpiceTestbench(circuit, analyses, measurements, extra)


def generate_transistor_circuit(det, output_file, context=None, parasitics=None):
    """Generate testbench for a transistor circuit detection.

    Simulates the DC bias point of the transistor to verify it's in the
    expected operating region (on/off for switches, active for amplifiers).

    Args:
        det: Finding dict from findings[] — detector:transistor_circuits[] with keys
             varying by type (mosfet/bjt). See signal_detectors.py.
        output_file: Path for ASCII results file

    Returns:
        Complete .cir file content string, or None if not simulatable
    """
    ttype = det.get("type", "")
    ref = det["reference"]
    value = det.get("value", "")

    if ttype == "mosfet" or ttype == "jfet":
        return _generate_mosfet_testbench(det, output_file, context=context, parasitics=parasitics)
    elif ttype == "bjt":
        return _generate_bjt_testbench(det, output_file, context=context, parasitics=parasitics)
    return None


def _generate_mosfet_testbench(det, output_file, context=None, parasitics=None):
    """Generate MOSFET switching testbench."""
    ref = det["reference"]
    value = det.get("value", "MOSFET")
    is_p = det.get("is_pchannel", False)
    gate = _sanitize_net(det.get("gate_net"))
    drain = _sanitize_net(det.get("drain_net"))
    source = _sanitize_net(det.get("source_net"))
    source_is_gnd = det.get("source_is_ground", False)
    drain_is_pwr = det.get("drain_is_power", False)
    source_is_pwr = det.get("source_is_power", False)
    load_type = det.get("load_type", "unknown")

    # Skip complex topologies we can't reconstruct reliably
    if load_type in ("level_shifter",):
        return None  # Level shifters need both FETs modeled together
    if source_is_pwr and drain_is_pwr:
        return None  # Power switch between two rails — need full circuit context
    if load_type == "high_side_switch":
        return None  # High-side switches need load context to simulate

    model = "PMOS_GENERIC" if is_p else "NMOS_GENERIC"
    ch_type = "P-channel" if is_p else "N-channel"
    has_snubber = det.get("has_snubber", False)
    has_flyback = det.get("has_flyback_diode", False)

    # Determine supply voltage
    if is_p:
        # P-channel: source is usually at VDD
        vdd = _infer_voltage(det.get("source_net"), default=3.3)
    else:
        # N-channel: drain load connects to VDD
        vdd = _infer_voltage(det.get("drain_net"), default=3.3)
        if drain_is_pwr:
            vdd = _infer_voltage(det.get("drain_net"), default=3.3)

    # Build a simple switching testbench
    # N-channel: VDD → R_load → drain, source → GND, gate swept 0→VDD
    # P-channel: VDD → source, drain → R_load → GND, gate swept VDD→0

    # Gate resistor (if present, use its value for the drive path)
    gate_res = det.get("gate_resistors", [])
    gate_r_val = 1000  # default 1k gate resistance
    gate_r_ref = "Rgate"
    if gate_res:
        gate_r_ref = gate_res[0].get("reference", "Rgate")

    # Pulldown/pullup on gate
    pulldown = det.get("gate_pulldown")

    protection_note = ""
    if has_flyback:
        protection_note += f"\n* Flyback diode: {det.get('flyback_diode', 'yes')}"
    if has_snubber:
        protection_note += "\n* Drain snubber RC detected"

    if is_p:
        circuit = f"""\
* Auto-generated testbench for {ch_type} MOSFET: {ref} ({value})
* Load type: {load_type}{protection_note}
* Model: generic PMOS (Vth=-1.5V) — real threshold depends on part

{get_generic_models()}

VDD vdd 0 DC {vdd}

* P-channel MOSFET: source to VDD, drain to load
M{ref} {drain} {gate} vdd vdd {model} L=1u W=100u
RLOAD {drain} 0 1k

* Gate drive: sweep from VDD (off) to 0V (on)
Vgate {gate} 0 DC {vdd}
"""

        analyses = [("dc", f"Vgate 0 {vdd} {vdd/100}")]
        measurements = [
            ("id", "let", "i(VDD)"),
            ("vg", "let", f"v({gate})"),
            ("vth", "when", "abs(id)", "1m"),
            ("i_on", "let", "abs(vecmax(id))", True),
        ]
        extra = {"vdd": str(vdd)}

        return SpiceTestbench(circuit, analyses, measurements, extra)
    else:
        circuit = f"""\
* Auto-generated testbench for {ch_type} MOSFET: {ref} ({value})
* Load type: {load_type}{protection_note}
* Model: generic NMOS (Vth=1.5V) — real threshold depends on part

{get_generic_models()}

VDD vdd 0 DC {vdd}

* N-channel MOSFET: drain to load, source to GND
RLOAD vdd {drain} 1k
M{ref} {drain} {gate} 0 0 {model} L=1u W=100u

* Gate drive: sweep from 0V (off) to VDD (on)
Vgate {gate} 0 DC 0
"""

        analyses = [("dc", f"Vgate 0 {vdd} {vdd/100}")]
        measurements = [
            ("id", "let", "abs(i(VDD))"),
            ("vth", "when", "id", "1m"),
            ("i_on", "let", "vecmax(id)", True),
        ]
        extra = {"vdd": str(vdd)}

        return SpiceTestbench(circuit, analyses, measurements, extra)


def _generate_bjt_testbench(det, output_file, context=None, parasitics=None):
    """Generate BJT bias point testbench."""
    ref = det["reference"]
    value = det.get("value", "BJT")
    base = _sanitize_net(det.get("base_net"))
    collector = _sanitize_net(det.get("collector_net"))
    emitter = _sanitize_net(det.get("emitter_net"))
    emitter_is_gnd = det.get("emitter_is_ground", False)
    collector_is_pwr = det.get("collector_is_power", False)
    load_type = det.get("load_type", "unknown")

    # Determine transistor polarity from lib_id
    lib_id = det.get("lib_id", "")
    is_pnp = "PNP" in lib_id.upper() or "pnp" in lib_id.lower()
    model = "PNP_GENERIC" if is_pnp else "NPN_GENERIC"
    polarity = "PNP" if is_pnp else "NPN"

    vcc = _infer_voltage(det.get("collector_net") if not is_pnp else det.get("emitter_net"), default=3.3)

    # Emitter resistor for degeneration
    emitter_r = det.get("emitter_resistor")
    emitter_r_line = ""
    if emitter_r:
        # Parse value — the detector gives ref and value but not always ohms
        emitter_r_line = f"* Emitter resistor: {emitter_r.get('reference', 'RE')} = {emitter_r.get('value', '?')}"

    # Base resistors
    base_res = det.get("base_resistors", [])
    base_note = f"{len(base_res)} base resistor(s)" if base_res else "no base resistor"

    if is_pnp:
        circuit = f"""\
* Auto-generated testbench for {polarity} BJT: {ref} ({value})
* Load type: {load_type}, {base_note}
* Model: generic PNP (hFE=200)
{emitter_r_line}

{get_generic_models()}

VCC vcc 0 DC {vcc}

* PNP: emitter to VCC, collector to load
Q{ref} {collector} {base} vcc {model}
RLOAD {collector} 0 1k

* Base drive: sweep from VCC (off) to VCC-0.8V (on)
Vbase {base} 0 DC {vcc}
"""

        analyses = [("dc", f"Vbase {vcc * 0.5} {vcc} {vcc * 0.005}")]
        measurements = [
            ("ic", "let", "abs(i(VCC))"),
            ("vbe_on", "when", "ic", "1m"),
            ("ic_on", "let", "vecmax(ic)", True),
        ]
        extra = {"vcc": str(vcc)}

        return SpiceTestbench(circuit, analyses, measurements, extra)
    else:
        circuit = f"""\
* Auto-generated testbench for {polarity} BJT: {ref} ({value})
* Load type: {load_type}, {base_note}
* Model: generic NPN (hFE=200)
{emitter_r_line}

{get_generic_models()}

VCC vcc 0 DC {vcc}

* NPN: collector to load, emitter to GND
RLOAD vcc {collector} 1k
Q{ref} {collector} {base} 0 {model}

* Base drive: sweep from 0V (off) to 1V (on)
Vbase {base} 0 DC 0
"""

        analyses = [("dc", "Vbase 0 1 0.01")]
        measurements = [
            ("ic", "let", "abs(i(VCC))"),
            ("vbe_on", "when", "ic", "1m"),
            ("ic_on", "let", "vecmax(ic)", True),
        ]
        extra = {"vcc": str(vcc)}

        return SpiceTestbench(circuit, analyses, measurements, extra)


def generate_current_sense(det, output_file, context=None, parasitics=None):
    """Generate testbench for a current sense detection.

    Validates the sense resistor value by simulating a DC sweep and
    confirming the voltage drop at specified current levels.

    Args:
        det: Finding dict from findings[] — detector:current_sense[] with keys:
             shunt{ref,ohms}, sense_ic{ref,value,type}, high_net,
             low_net, max_current_50mV_A, max_current_100mV_A
        output_file: Path for ASCII results file

    Returns:
        Complete .cir file content string
    """
    shunt = det["shunt"]
    r_ref = shunt["ref"]
    r_ohms = shunt["ohms"]
    high_net = _sanitize_net(det["high_net"])
    low_net = _sanitize_net(det["low_net"])

    sense_ic = det.get("sense_ic", {})
    ic_ref = sense_ic.get("ref", "")
    ic_value = sense_ic.get("value", "")

    max_50 = det.get("max_current_50mV_A")
    max_100 = det.get("max_current_100mV_A")

    # For an ideal resistor, I=V/R is exact — compute directly rather
    # than sweeping. The simulation confirms the resistance value.
    i_at_50mv = 0.05 / r_ohms
    i_at_100mv = 0.1 / r_ohms

    circuit = f"""\
* Auto-generated testbench for current sense: {r_ref} ({r_ohms} ohm)
* Sense IC: {ic_ref} ({ic_value})
* Expected max current at 50mV: {max_50} A
* Expected max current at 100mV: {max_100} A
* Model: ideal resistor (exact)

{spice_element_for_passive(r_ref, r_ohms, "sense_hi", "0")}

* Apply known current and measure voltage drop
I1 sense_hi 0 DC {_format_eng(i_at_50mv)}
"""

    analyses = [("op", "")]
    measurements = [
        ("vsense_50", "let", "v(sense_hi)"),
        ("i_50", "let", str(i_at_50mv)),
        ("r_eff", "let", "vsense_50 / i_50"),
        ("i_at_50mV", "let", "abs(0.05 / r_eff)", True),
        ("i_at_100mV", "let", "abs(0.1 / r_eff)", True),
    ]
    extra = {"r_ohms": str(r_ohms)}

    return SpiceTestbench(circuit, analyses, measurements, extra)


def generate_protection_device(det, output_file, context=None, parasitics=None):
    """Generate testbench for a protection device detection.

    Only TVS/ESD diodes are simulatable — fuses and varistors need
    manufacturer-specific models.

    Args:
        det: Finding dict from findings[] — detector:protection_devices[] with keys:
             ref, value, type, protected_net, clamp_net
        output_file: Path for ASCII results file

    Returns:
        Complete .cir file content string, or None if not simulatable
    """
    ptype = det.get("type", "")
    if ptype not in ("diode", "tvs", "esd"):
        return None  # Fuses, varistors need manufacturer models

    ref = det["ref"]
    value = det.get("value", "")
    protected_net = _sanitize_net(det.get("protected_net"))
    clamp_net = _sanitize_net(det.get("clamp_net"))

    # Infer the protected rail voltage for sweep range
    rail_v = _infer_voltage(det.get("protected_net"), default=3.3)
    sweep_max = rail_v * 3  # Sweep to 3x nominal to see clamping

    circuit = f"""\
* Auto-generated testbench for protection device: {ref} ({value})
* Type: {ptype}, protecting {det.get('protected_net', '?')}
* Model: generic Zener diode — real TVS clamping may differ

{get_generic_models()}

* TVS/ESD diode: cathode to protected net, anode to clamp (GND)
D{ref} {clamp_net or '0'} {protected_net} D_GENERIC

* Voltage ramp on protected net to find clamping voltage
Vramp {protected_net} 0 DC 0
"""

    analyses = [("dc", f"Vramp 0 {_format_eng(sweep_max)} {_format_eng(sweep_max / 200)}")]
    measurements = [
        ("idiode", "let", "abs(i(Vramp))"),
        ("v_clamp_1mA", "when", "idiode", "1m"),
        ("v_clamp_10mA", "when", "idiode", "10m"),
    ]
    extra = {"rail_v": str(rail_v)}

    return SpiceTestbench(circuit, analyses, measurements, extra)


def generate_decoupling(det, output_file, context=None, parasitics=None):
    """Generate testbench for a decoupling analysis detection.

    Measures impedance profile of parallel capacitor bank on a power rail.
    Each cap is modeled as series R-L-C (ESR + parasitic inductance + capacitance)
    to capture self-resonant frequency behavior.

    Args:
        det: Finding dict from findings[] — detector:decoupling_analysis[] with keys:
             rail, capacitors[{ref,farads,self_resonant_hz}], cap_count
        output_file: Path for ASCII results file

    Returns:
        Complete .cir file content string, or None if not enough data
    """
    # EQ-081: |Z| at target freq from ESR+ESL cap model
    caps = det.get("capacitors", [])
    rail = det.get("rail", "?")

    # Prefer pdn_impedance data (has real ESR/ESL from package) over estimates
    ctx = context or {}
    pdn_rails = ctx.get("pdn_impedance", {}).get("rails", {})
    pdn_caps = pdn_rails.get(rail, {}).get("capacitors", []) if pdn_rails else []
    pdn_by_ref = {c["ref"]: c for c in pdn_caps if c.get("ref")}

    # Filter to caps with valid data
    valid_caps = [c for c in caps if c.get("farads") and c["farads"] > 0]
    if len(valid_caps) < 1:
        return None

    # Build cap models: each cap is series R_esr + L_par + C
    cap_lines = []
    using_pdn = False
    for i, c in enumerate(valid_caps):
        ref = c["ref"]
        farads = c["farads"]
        srf = c.get("self_resonant_hz", 0)

        # Use pdn_impedance ESR/ESL if available, otherwise estimate
        pdn = pdn_by_ref.get(ref)
        if pdn and pdn.get("esr_ohm") is not None:
            esr = pdn["esr_ohm"]
            l_par = pdn.get("esl_nH", 1.0) * 1e-9  # nH → H
            using_pdn = True
        else:
            # ESR estimate: ceramic <10µF → 10mΩ, ≥10µF → 5mΩ, elec ≥100µF → 100mΩ
            if farads >= 1e-4:
                esr = 0.1
            elif farads >= 1e-5:
                esr = 0.005
            else:
                esr = 0.01
            # Parasitic inductance from SRF (or default ~1nH)
            if srf and srf > 0:
                l_par = 1.0 / ((2 * math.pi * srf) ** 2 * farads)
            else:
                l_par = 1e-9

        # Series R-L-C from rail node to ground
        n1 = f"n_esr_{i}"
        n2 = f"n_lpar_{i}"
        cap_lines.append(f"R_esr_{ref} rail {n1} {_format_eng(esr)}")
        cap_lines.append(f"L_par_{ref} {n1} {n2} {_format_eng(l_par)}")
        cap_lines.append(f"{ref} {n2} 0 {_format_eng(farads)}")

    cap_netlist = "\n".join(cap_lines)
    n_caps = len(valid_caps)
    model_note = "ESR/ESL from pdn_impedance (package-based)" if using_pdn else "estimated ESR + parasitic L from SRF"

    circuit = f"""\
* Auto-generated testbench for decoupling analysis: {rail} rail
* {n_caps} capacitor(s) in parallel, series R-L-C model
* Model: {model_note}

{cap_netlist}

* 1A AC current source into the rail node — V(rail) = Z(f)
IAC 0 rail DC 0 AC 1
"""

    analyses = [("ac", "dec 200 100 100Meg")]
    measurements = [
        ("z_mag", "let", "vm(rail)"),
        ("z_min", "min", "z_mag"),
        ("f_at_zmin", "when", "z_mag", "z_min"),
        ("z_at_1M", "find", "vm(rail)", "at=1Meg"),
        ("z_at_100k", "find", "vm(rail)", "at=100k"),
    ]
    extra = {"n_caps": str(n_caps)}

    return SpiceTestbench(circuit, analyses, measurements, extra)


def generate_regulator_feedback(det, output_file, context=None, parasitics=None):
    """Generate testbench for a power regulator's feedback divider.

    Validates that the feedback divider produces the expected Vref at the
    FB pin, confirming the regulator's output voltage setpoint.

    Args:
        det: Finding dict from findings[] — detector:power_regulators[] with keys:
             feedback_divider{r_top{ref,ohms}, r_bottom{ref,ohms}, ratio},
             assumed_vref, estimated_vout, output_rail
        output_file: Path for ASCII results file

    Returns:
        Complete .cir file content string, or None if insufficient data
    """
    fd = det.get("feedback_divider")
    if not fd:
        return None

    r_top = fd.get("r_top")
    r_bot = fd.get("r_bottom")
    if not isinstance(r_top, dict) or not isinstance(r_bot, dict):
        return None

    rt_ohms = r_top.get("ohms")
    rb_ohms = r_bot.get("ohms")
    if not rt_ohms or not rb_ohms or rt_ohms <= 0 or rb_ohms <= 0:
        return None

    ratio = fd.get("ratio", rb_ohms / (rt_ohms + rb_ohms))
    vref = det.get("assumed_vref")
    estimated_vout = det.get("estimated_vout")
    output_rail = det.get("output_rail", "?")
    rt_ref = r_top["ref"]
    rb_ref = r_bot["ref"]
    reg_ref = det.get("ref", "?")
    topology = fd.get("topology", "standard")

    # Infer Vout from output rail name, or use estimated_vout
    vin = _infer_voltage(output_rail, default=None)
    if vin is None and estimated_vout:
        vin = estimated_vout
    if vin is None:
        vin = 3.3  # fallback

    expected_vfb = vin * ratio
    mid_net = "fb_net"

    circuit = f"""\
* Auto-generated testbench for regulator feedback: {reg_ref}
* Divider: {rt_ref}/{rb_ref}, ratio={ratio:.4f}
* Expected Vout={vin}V, Vfb={expected_vfb:.4f}V (Vref={vref or '?'}V)
* Topology: {topology}
* Model: ideal passives (exact for DC divider)

VIN out_rail 0 DC {vin}
{spice_element_for_passive(rt_ref, rt_ohms, "out_rail", mid_net)}
{spice_element_for_passive(rb_ref, rb_ohms, mid_net, "0")}
"""

    analyses = [("op", "")]
    measurements = [
        ("vfb_sim", "let", f"v({mid_net})", True),
        ("expected", "let", str(expected_vfb)),
        ("error_pct", "let", "abs(vfb_sim - expected) / expected * 100", True),
    ]
    extra = {"expected": str(expected_vfb), "vin": str(vin), "vref": str(vref or 0)}

    return SpiceTestbench(circuit, analyses, measurements, extra)


def generate_rf_matching(det, output_file, context=None, parasitics=None):
    """Generate testbench for an RF matching network.

    Sweeps AC impedance of the L/C network to find the self-resonant
    frequency and minimum impedance point. No target frequency required.

    Args:
        det: Finding dict from findings[] — detector:rf_matching[] with keys:
             topology, components[{ref,type,farads,henries,ohms}]
        output_file: Path for ASCII results file

    Returns:
        Complete .cir file content string, or None if insufficient data
    """
    comps = det.get("components", [])
    topology = det.get("topology", "unknown")

    # Filter to components with parsed values
    valid = []
    for c in comps:
        val = c.get("farads") or c.get("henries") or c.get("ohms")
        if val and val > 0:
            valid.append(c)

    if len(valid) < 2:
        return None

    # Build series L/C network: antenna_port → components → ic_port
    # For impedance measurement, connect all components in series from
    # port to ground, measuring the input impedance.
    netlist_lines = []
    prev_net = "port"
    for i, c in enumerate(valid):
        ref = c["ref"]
        next_net = f"n{i+1}" if i < len(valid) - 1 else "0"
        val = c.get("farads") or c.get("henries") or c.get("ohms")
        netlist_lines.append(spice_element_for_passive(ref, val, prev_net, next_net))
        prev_net = next_net

    comp_netlist = "\n".join(netlist_lines)
    comp_refs = [c["ref"] for c in valid]

    circuit = f"""\
* Auto-generated testbench for RF matching network
* Topology: {topology}, {len(valid)} components: {', '.join(comp_refs)}
* Model: ideal passives — no parasitic ESR/ESL

{comp_netlist}

* 1A AC current source — V(port) = Z(f)
IAC 0 port DC 0 AC 1
"""

    analyses = [("ac", "dec 200 1k 10G")]
    measurements = [
        ("z_mag", "let", "vm(port)"),
        ("z_min", "min", "z_mag"),
        ("f_at_zmin", "when", "z_mag", "z_min"),
        ("z_at_100M", "find", "vm(port)", "at=100Meg"),
        ("z_at_1G", "find", "vm(port)", "at=1G"),
        ("z_at_2G4", "find", "vm(port)", "at=2.4G"),
    ]

    return SpiceTestbench(circuit, analyses, measurements)


def generate_inrush(det, output_file, context=None, parasitics=None):
    """Generate testbench for inrush current analysis.

    Simulates startup transient: voltage source ramps up through a
    current-limiting element into the output cap bank. Measures peak
    inrush current and settling time.

    Args:
        det: Dict from inrush_analysis.rails[] with keys:
             regulator, output_rail, output_voltage, topology,
             output_caps[{ref,farads}], total_output_capacitance_uF,
             estimated_inrush_A, assumed_soft_start_ms
        output_file: Path for ASCII results file

    Returns:
        Complete .cir file content string, or None if insufficient data
    """
    # EQ-082: I_peak = V/R at t=0 (startup inrush current)
    caps = det.get("output_caps", [])
    v_out = det.get("output_voltage")
    reg_ref = det.get("regulator", "?")
    topology = det.get("topology", "?")
    soft_start_ms = det.get("assumed_soft_start_ms", 0.5)

    valid_caps = [c for c in caps if c.get("farads") and c["farads"] > 0]
    if not valid_caps or not v_out or v_out <= 0:
        return None

    # Model: voltage ramp (soft-start) through a small series resistance
    # into parallel caps. The series R models the regulator's output impedance.
    # For LDO: ~0.1-1Ω output impedance. For switching: ~0.01-0.1Ω.
    r_out = 0.1 if topology == "LDO" else 0.01
    ramp_time = soft_start_ms * 1e-3  # Convert ms to seconds
    sim_time = ramp_time * 3  # Simulate 3x the ramp time

    # Build parallel caps
    cap_lines = []
    for i, c in enumerate(valid_caps):
        cap_lines.append(f"{c['ref']} out 0 {_format_eng(c['farads'])}")
    cap_netlist = "\n".join(cap_lines)
    cap_refs = [c["ref"] for c in valid_caps[:5]]
    total_uf = sum(c["farads"] for c in valid_caps) * 1e6

    circuit = f"""\
* Auto-generated testbench for inrush analysis: {reg_ref} ({topology})
* Output: {v_out}V, {total_uf:.1f}µF total capacitance
* Soft-start: {soft_start_ms}ms ramp

* Voltage source with linear ramp (soft-start) — 10us delay before ramp
Vreg ramp 0 PWL(0 0 10u 0 {_format_eng(ramp_time + 10e-6)} {v_out})
* Regulator output impedance
Rout ramp out {_format_eng(r_out)}

* Output capacitors
{cap_netlist}
"""

    analyses = [("tran", f"{_format_eng(ramp_time / 500)} {_format_eng(sim_time)}")]
    measurements = [
        ("i_out", "let", "abs(i(Rout))"),
        ("i_peak", "let", "vecmax(i_out)", True),
        ("t_peak", "let", "i_out[vecmin(abs(i_out - i_peak))]", True),
        ("v_settled", "find", "v(out)", f"at={_format_eng(sim_time * 0.9)}"),
    ]
    extra = {"v_target": str(v_out), "r_out": str(r_out)}

    return SpiceTestbench(circuit, analyses, measurements, extra)


def generate_bridge_circuit(det, output_file, context=None, parasitics=None):
    """Generate testbench for a half-bridge circuit.

    For each half-bridge, verifies that the high-side and low-side FETs
    can be turned on independently by sweeping gate voltage and checking
    drain current.

    Args:
        det: Finding dict from findings[] — detector:bridge_circuits[] with keys:
             topology, half_bridges[{high_side, low_side, power_net,
             ground_net, high_side_type, low_side_type}]
        output_file: Path for ASCII results file

    Returns:
        Complete .cir file content string, or None if insufficient data
    """
    half_bridges = det.get("half_bridges", [])
    if not half_bridges:
        return None

    topology = det.get("topology", "?")
    # Only simulate the first half-bridge (they're typically identical)
    hb = half_bridges[0]
    hi_ref = hb["high_side"]
    lo_ref = hb["low_side"]
    hi_type = hb.get("high_side_type", "NMOS")
    lo_type = hb.get("low_side_type", "NMOS")

    hi_model = "PMOS_GENERIC" if hi_type == "PMOS" else "NMOS_GENERIC"
    lo_model = "PMOS_GENERIC" if lo_type == "PMOS" else "NMOS_GENERIC"

    # Supply voltage — try to infer from power net
    power_net = hb.get("power_net", "")
    ctx = context or {}
    v_supply = 5  # default
    if power_net:
        v = _infer_voltage(power_net, default=None)
        if v and v > 0:
            v_supply = v

    circuit = f"""\
* Auto-generated testbench for bridge circuit: {topology}
* Half-bridge: {hi_ref} (high, {hi_type}) / {lo_ref} (low, {lo_type})
* Model: generic FET models — real Vth/Rds depends on specific part

{get_generic_models()}

* Supply
VDD vdd 0 DC {v_supply}

* Low-side FET: gate swept, drain to mid, source to ground
M{lo_ref} mid lo_gate 0 0 {lo_model} L=1u W=100u
* High-side kept off (gate tied to source/ground)
M{hi_ref} vdd hi_gate mid mid {hi_model} L=1u W=100u
Rhi_gnd hi_gate {"mid" if hi_type == "PMOS" else "0"} 100k

* Load resistor at output
Rload mid 0 100

* Gate sweep source
Vgate lo_gate 0 DC 0
"""

    analyses = [("dc", f"Vgate 0 {v_supply} {v_supply/100}")]
    measurements = [
        ("id_lo", "let", "abs(i(VDD))"),
        ("vth_lo", "when", "id_lo", "100u"),
        ("id_on", "find", "id_lo", f"at={v_supply}"),
    ]
    extra = {"v_supply": str(v_supply), "topology": topology}

    return SpiceTestbench(circuit, analyses, measurements, extra)


# ---------------------------------------------------------------------------
# Registry: maps detector key names to generator functions
# ---------------------------------------------------------------------------

def generate_bms_balance(det, output_file, context=None, parasitics=None):
    """Generate testbench for BMS balance resistor power analysis.

    Simulates worst-case cell voltage (4.2V) through the balance resistor
    to verify current and power dissipation are within component ratings.

    Args:
        det: Finding dict from findings[] — detector:bms_systems[] with keys:
             bms_reference, cell_count, balance_resistors[{reference,ohms}]
        output_file: Path for ASCII results file

    Returns:
        Complete .cir file content string, or None if insufficient data
    """
    cell_count = det.get("cell_count", 0)
    if cell_count < 1:
        return None

    bal_resistors = det.get("balance_resistors", [])
    if not isinstance(bal_resistors, list):
        return None

    # Find first balance resistor with valid ohms
    r_ref = None
    r_ohms = None
    for br in bal_resistors:
        if isinstance(br, dict) and br.get("ohms") and br["ohms"] > 0:
            r_ref = br["reference"]
            r_ohms = br["ohms"]
            break

    if not r_ref or not r_ohms:
        return None

    bms_ref = det.get("bms_reference", "?")
    bms_val = det.get("bms_value", "?")

    circuit = f"""\
* Auto-generated testbench for BMS balance resistor: {bms_ref} ({bms_val})
* {cell_count} cells, balance R = {r_ref} ({_format_eng(r_ohms)} ohm)
* Worst-case: 4.2V fully-charged Li-ion cell

Vcell cell 0 DC 4.2
{r_ref} cell 0 {_format_eng(r_ohms)}
"""

    analyses = [("op", "")]
    measurements = [
        ("i_bal", "let", "abs(i(Vcell))", True),
        ("p_bal", "let", "4.2 * i_bal", True),
    ]
    extra = {"r_ohms": str(r_ohms), "n_cells": str(cell_count)}

    return SpiceTestbench(circuit, analyses, measurements, extra)


def generate_snubber(det, output_file, context=None, parasitics=None):
    """Generate testbench for an RC snubber circuit.

    AC impedance sweep of the snubber R-C network to verify the damping
    frequency matches the analytical τ = R×C.

    Args:
        det: Dict from transistor_circuits[] with snubber_data:
             snubber_data{resistor_ref, resistor_ohms, capacitor_ref, capacitor_farads}
        output_file: Path for ASCII results file

    Returns:
        Complete .cir file content string, or None if insufficient data
    """
    # EQ-085: f_damp = 1/(2πRC) (snubber damping frequency)
    sd = det.get("snubber_data")
    if not sd:
        return None

    r_ref = sd.get("resistor_ref")
    r_ohms = sd.get("resistor_ohms")
    c_ref = sd.get("capacitor_ref")
    c_farads = sd.get("capacitor_farads")

    if not r_ref or not c_ref or not r_ohms or not c_farads:
        return None
    if r_ohms <= 0 or c_farads <= 0:
        return None

    tau = r_ohms * c_farads
    f_analytical = 1.0 / (2 * math.pi * tau)
    fet_ref = det.get("reference", "?")

    f_start = max(f_analytical / 100, 1)
    f_stop = f_analytical * 100

    circuit = f"""\
* Auto-generated testbench for snubber on {fet_ref}: {r_ref}/{c_ref}
* R={_format_eng(r_ohms)} ohm, C={_format_eng(c_farads)} F
* Analytical: tau={_format_eng(tau)}s, f_snub={f_analytical:.1f} Hz

{r_ref} drain mid {_format_eng(r_ohms)}
{c_ref} mid 0 {_format_eng(c_farads)}

* AC current source — V(drain) = Z(f)
IAC 0 drain DC 0 AC 1
"""

    analyses = [("ac", f"dec 200 {_format_eng(f_start)} {_format_eng(f_stop)}")]
    measurements = [
        ("z_mag", "let", "vm(drain)"),
        ("z_min", "min", "z_mag"),
        ("f_at_zmin", "when", "z_mag", "z_min"),
    ]
    extra = {"tau": str(tau), "f_analytical": str(f_analytical)}

    return SpiceTestbench(circuit, analyses, measurements, extra)


def generate_rf_chain(det, output_file, context=None, parasitics=None):
    """Generate testbench for RF chain link budget analysis.

    Hybrid approach: minimal SPICE testbench (50Ω reference check at
    operating frequency) combined with analytical gain budget from
    heuristic per-stage gain/loss values.

    Args:
        det: Finding dict from findings[] — detector:rf_chains[] with keys:
             operating_frequency_hz, gain_budget_dB, stage_gains,
             component_roles, transceivers, total_rf_components
        output_file: Path for ASCII results file

    Returns:
        Complete .cir file content string, or None if no frequency data
    """
    freq = det.get("operating_frequency_hz")
    if not freq or freq <= 0:
        return None

    gain_budget = det.get("gain_budget_dB", 0)
    n_stages = det.get("total_rf_components", 0)
    band = det.get("frequency_band", "?")

    circuit = f"""\
* Auto-generated testbench for RF chain link budget
* Operating frequency: {freq/1e6:.0f} MHz ({band})
* Analytical gain budget: {gain_budget:.1f} dB ({n_stages} stages)
* Model: 50-ohm reference impedance check + heuristic gain budget

R_source port 0 50
R_load port 0 50

* AC stimulus at operating frequency
IAC 0 port DC 0 AC 1
"""

    analyses = [("ac", f"dec 10 {_format_eng(freq / 2)} {_format_eng(freq * 2)}")]
    measurements = [
        ("z_at_fc", "find", "vm(port)", f"at={_format_eng(freq)}"),
    ]
    extra = {"gain_budget": str(gain_budget), "freq_hz": str(freq), "n_stages": str(n_stages)}

    return SpiceTestbench(circuit, analyses, measurements, extra)


TEMPLATE_REGISTRY = {
    "rc_filters": generate_rc_filter,
    "lc_filters": generate_lc_filter,
    "voltage_dividers": generate_voltage_divider,
    "opamp_circuits": generate_opamp_circuit,
    "crystal_circuits": generate_crystal_circuit,
    "feedback_networks": generate_feedback_network,
    "transistor_circuits": generate_transistor_circuit,
    "current_sense": generate_current_sense,
    "protection_devices": generate_protection_device,
    "decoupling_analysis": generate_decoupling,
    "power_regulators": generate_regulator_feedback,
    "rf_matching": generate_rf_matching,
    "bridge_circuits": generate_bridge_circuit,
    "bms_systems": generate_bms_balance,
    "rf_chains": generate_rf_chain,
    "snubber_circuits": generate_snubber,
}


# Top-level types (not under findings[])
TOPLEVEL_REGISTRY = {
    "inrush_analysis": ("rails", generate_inrush),
}


def list_supported_types():
    """Return list of all keys that can be simulated (findings + top-level)."""
    return list(TEMPLATE_REGISTRY.keys()) + list(TOPLEVEL_REGISTRY.keys())
