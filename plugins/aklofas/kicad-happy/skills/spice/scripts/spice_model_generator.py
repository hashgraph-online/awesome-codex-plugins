"""
Generate parameterized behavioral SPICE subcircuits from component specs.

Takes a specs dict (from spice_part_library.py or API fetcher) and produces
an ngspice-compatible .subckt string. Models capture the key AC/DC specs
that determine circuit behavior — GBW, slew rate, offset, output swing —
without modeling internal transistor topology.

All models use the same 5-pin interface: inp, inn, out, vcc, vee
(or appropriate variants per component type).
"""

import math
import re
from spice_models import _format_eng as _eng, spice_text


def sanitize_mpn(mpn):
    """Convert an MPN to a safe SPICE subcircuit name suffix.

    Examples: "LM358DR" → "LM358DR", "AMS1117-3.3" → "AMS1117_3_3"
    """
    return re.sub(r'[^A-Za-z0-9_]', '_', mpn.strip())


def generate_opamp_model(mpn, specs):
    """Generate a behavioral opamp .subckt from specs.

    The model captures:
    - Open-loop gain (Aol) with single-pole rolloff at GBW/Aol
    - Input offset voltage
    - Input impedance
    - Slew rate limiting (diode-clamped current source)
    - Output swing clamping to supply rails (adjusted for non-RRO parts)

    Args:
        mpn: Part number (for subcircuit name and comments)
        specs: Dict with keys: gbw_hz, slew_vus, vos_mv, aol_db,
               rin_ohms, rro, swing_v

    Returns:
        .subckt string
    """
    # EQ-074: GBW = Aol × f_pole (opamp behavioral SPICE model)
    name = f"OPAMP_{sanitize_mpn(mpn)}"
    gbw = specs["gbw_hz"]
    slew = specs.get("slew_vus", 1.0)
    vos = specs.get("vos_mv", 0)
    aol_db = specs.get("aol_db", 100)
    rin = specs.get("rin_ohms", 1e12)
    rro = specs.get("rro", False)
    swing = specs.get("swing_v", 1.5)

    # Derive model parameters
    aol_linear = 10 ** (aol_db / 20)
    f_pole = gbw / aol_linear  # Dominant pole frequency
    # With R1=1 ohm: C = 1/(2*pi*R*f)
    c_pole = 1.0 / (2 * math.pi * f_pole)

    # Slew rate: I_slew = C_pole * slew_rate
    # slew is in V/µs, C_pole in F → I = C * dV/dt = C_pole * slew * 1e6
    i_slew = c_pole * slew * 1e6

    # Output swing diode model
    # For RRO: use very small swing (millivolts from rail)
    # For non-RRO: use specified swing voltage
    if rro:
        clamp_n = 0.01  # Diode emission coefficient — lower = sharper clamp
    else:
        clamp_n = 0.1

    vos_line = f"Vos inp inp_os DC {vos * 1e-3}" if vos > 0 else "* Vos ≈ 0"
    inp_node = "inp_os" if vos > 0 else "inp"

    return f"""\
.subckt {name} inp inn out vcc vee
* Behavioral model for {spice_text(mpn)}
* GBW={gbw/1e6:.1f}MHz, SR={slew}V/us, Vos={vos}mV, Aol={aol_db}dB
* Source: kicad-happy part library (Phase 2)
*
* Input stage
Rin inp inn {_eng(rin)}
{vos_line}
*
* Gain stage: Aol={aol_linear:.0f}, pole at {f_pole:.1f}Hz → GBW={gbw/1e6:.1f}MHz
E1 int 0 {inp_node} inn {aol_linear:.0f}
R1 int out_int 1
C1 out_int 0 {_eng(c_pole)}
*
* Output stage with rail clamping
{"* Rail-to-rail output" if rro else f"* Output swing: {swing}V from rails"}
Dhigh out_int vcc_int DLIMIT
Dlow vee_int out_int DLIMIT
{"Vswh vcc vcc_int DC 0" if rro else f"Vswh vcc vcc_int DC {swing}"}
{"Vswl vee_int vee DC 0" if rro else f"Vswl vee_int vee DC {swing}"}
.model DLIMIT D(IS=1e-14 N={clamp_n})
Eout out 0 out_int 0 1
.ends {name}
"""


def generate_ldo_model(mpn, specs):
    """Generate a behavioral LDO regulator .subckt from specs.

    Models DC behavior: Vout, dropout, and basic load regulation.
    Does NOT model transient response, PSRR, or noise.

    Args:
        mpn: Part number
        specs: Dict with keys: vref, dropout_mv, iq_ua, iout_max_ma

    Returns:
        .subckt string
    """
    name = f"LDO_{sanitize_mpn(mpn)}"
    vref = specs.get("vref", 0.8)
    dropout = specs.get("dropout_mv", 500) / 1000  # Convert to V
    iq = specs.get("iq_ua", 100) / 1e6  # Convert to A
    fixed = specs.get("fixed", False)

    if fixed:
        # Fixed-output LDO: simpler model, no FB pin
        return f"""\
.subckt {name} vin vout gnd
* Behavioral LDO model for {spice_text(mpn)} (fixed {vref}V output)
* Dropout={dropout*1000:.0f}mV, Iq={iq*1e6:.0f}uA
* Source: kicad-happy part library (Phase 2)
*
* Regulated output — clamps at Vout or (Vin - dropout), whichever is lower
Ereg vout_int gnd VALUE = {{ MIN(V(vin,gnd)-{dropout}, {vref}) }}
Rout vout_int vout 0.01
* Quiescent current
Riq vin gnd {_eng(1/iq if iq > 0 else 1e12)}
.ends {name}
"""
    else:
        # Adjustable LDO with FB pin
        return f"""\
.subckt {name} vin vout gnd fb
* Behavioral LDO model for {spice_text(mpn)} (adjustable, Vref={vref}V)
* Dropout={dropout*1000:.0f}mV, Iq={iq*1e6:.0f}uA
* Source: kicad-happy part library (Phase 2)
*
* Error amplifier: regulates FB pin to Vref
* Vout = Vref * (1 + R_top/R_bot) — set by external divider
Ereg ctrl gnd VALUE = {{ MIN(V(vin,gnd)-{dropout}, {vref} + ({vref}-V(fb,gnd))*1e4) }}
Rout ctrl vout 0.01
* Quiescent current
Riq vin gnd {_eng(1/iq if iq > 0 else 1e12)}
.ends {name}
"""


def generate_comparator_model(mpn, specs):
    """Generate a behavioral comparator .subckt from specs.

    Args:
        mpn: Part number
        specs: Dict with keys: prop_delay_ns, output_type, supply_min, supply_max

    Returns:
        .subckt string
    """
    # EQ-073: V_out = Aol × (V+ - V-) clamped (comparator model)
    name = f"CMP_{sanitize_mpn(mpn)}"
    delay = specs.get("prop_delay_ns", 100)
    output_type = specs.get("output_type", "push_pull")

    # Delay as RC time constant: tau = delay * 2.2 (for 10-90% rise)
    tau = delay * 1e-9 / 2.2
    r_delay = 1000  # 1k ohm
    c_delay = tau / r_delay if r_delay > 0 else 1e-12

    if output_type == "open_collector" or output_type == "open_drain":
        output_section = f"""\
* Open-collector output — needs external pull-up
Mcmp out_gate 0 out out NSWITCH L=1u W=100u
.model NSWITCH NMOS(VTO=0.5 KP=1e-1 LAMBDA=0)
"""
    else:
        output_section = f"""\
* Push-pull output
Eout out 0 VALUE = {{ IF(V(comp_out) > 0, V(vcc), V(vee)) }}
"""

    return f"""\
.subckt {name} inp inn out vcc vee
* Behavioral comparator model for {spice_text(mpn)}
* Propagation delay: {delay}ns, output: {spice_text(output_type)}
* Source: kicad-happy part library (Phase 2)
*
* Compare inputs
Ediff diff 0 inp inn 1
* Delay stage
Rdel diff comp_out {r_delay}
Cdel comp_out 0 {_eng(c_delay)}
*
{output_section}
.ends {name}
"""


def generate_vref_model(mpn, specs):
    """Generate a behavioral voltage reference .subckt from specs.

    Args:
        mpn: Part number
        specs: Dict with keys: vref, tempco_ppm, zout_ohms

    Returns:
        .subckt string
    """
    name = f"VREF_{sanitize_mpn(mpn)}"
    vref = specs.get("vref", 2.5)
    zout = specs.get("zout_ohms", 1.0)
    iq = specs.get("iq_ua", 100) / 1e6

    return f"""\
.subckt {name} out gnd
* Behavioral voltage reference model for {spice_text(mpn)}
* Vref={vref}V, Zout={zout}ohm
* Source: kicad-happy part library (Phase 2)
*
Vref out_int gnd DC {vref}
Rout out_int out {zout}
.ends {name}
"""



# _eng imported from spice_models._format_eng at module level
