"""
Built-in SPICE behavioral models.

Provides subcircuit definitions that can be embedded directly in generated
.cir testbench files. These are ideal/generic models — no manufacturer
SPICE models are used. All models are ngspice-compatible.

Tier 1 only: passives are native SPICE elements (R, C, L) and need no
subcircuit. This module covers active components that require behavioral
modeling.
"""

import re
import unicodedata


# ---------------------------------------------------------------------------
# Ideal opamp — voltage-controlled voltage source with very high open-loop gain.
# Single-pole rolloff at 10 Hz gives realistic phase behavior for AC analysis
# without needing real GBW data.
#
# Pins: inp inn out vcc vee
# ---------------------------------------------------------------------------
IDEAL_OPAMP = """\
.subckt IDEAL_OPAMP inp inn out vcc vee
* Ideal opamp: Aol=1e6, single-pole at 10Hz (GBW ~10MHz)
* Output clamped to supply rails via diodes
Rin inp inn 1e12
E1 int 0 inp inn 1e6
R1 int out 1
C1 out 0 {cp}
Dhigh out vcc DLIMIT
Dlow vee out DLIMIT
.model DLIMIT D(N=1)
.ends IDEAL_OPAMP
"""

# Pole capacitor value: for Aol=1e6, R1=1, f_pole=10Hz → C = 1/(2*pi*1*10) ≈ 15.9mF
# This gives GBW = 1e6 * 10 = 10MHz — reasonable for a generic opamp.
IDEAL_OPAMP_PARAMS = {"cp": "15.9155m"}


def get_ideal_opamp():
    """Return the ideal opamp subcircuit definition string."""
    text = IDEAL_OPAMP
    for k, v in IDEAL_OPAMP_PARAMS.items():
        text = text.replace("{" + k + "}", v)
    return text


# ---------------------------------------------------------------------------
# Ideal LDO regulator — controlled source clamped to Vin - dropout.
# Models the DC behavior: Vout = Vref * (1 + Rtop/Rbot) with dropout limit.
# Does NOT model transient response, PSRR, or noise.
#
# This is used only when the analyzer detects a regulator AND we know Vref.
# The testbench places the feedback divider externally (from analyzer data),
# so this subcircuit just provides the error amplifier + pass element.
#
# Pins: vin vout gnd fb
# ---------------------------------------------------------------------------
IDEAL_LDO = """\
.subckt IDEAL_LDO vin vout gnd fb
* Ideal LDO: error amp compares FB to Vref, drives pass element
* Vref = {vref}V, dropout = 0.2V
Vref ref gnd DC {vref}
Eamp ctrl gnd ref fb 1e4
Rctrl ctrl gate 1k
Cctrl gate gnd 100n
Mpass vin gate vout vout PMOD L=1u W=100u
.model PMOD PMOS(VTO=-0.5 KP=1e-2)
Rdropout vin vout 1e9
.ends IDEAL_LDO
"""


def get_ideal_ldo(vref=0.8):
    """Return ideal LDO subcircuit with the given Vref."""
    return IDEAL_LDO.replace("{vref}", f"{vref}")


# ---------------------------------------------------------------------------
# Generic semiconductor model cards — these use ngspice built-in model
# equations with typical parameters. NOT manufacturer-accurate, but good
# enough for bias point and basic switching analysis.
# ---------------------------------------------------------------------------
GENERIC_MODELS = """\
* Generic semiconductor models for Phase 1 simulation
.model D_GENERIC D(IS=1e-14 N=1.05 BV=100 IBV=1e-10)
.model D_SCHOTTKY D(IS=1e-6 N=1.05 BV=40 IBV=1e-8 RS=0.5)
.model D_ZENER3V3 D(IS=1e-14 N=1.05 BV=3.3 IBV=5e-3)
.model D_ZENER5V1 D(IS=1e-14 N=1.05 BV=5.1 IBV=5e-3)
.model NPN_GENERIC NPN(IS=1e-14 BF=200 VAF=100 CJC=5p CJE=10p TF=0.3n)
.model PNP_GENERIC PNP(IS=1e-14 BF=200 VAF=100 CJC=5p CJE=10p TF=0.6n)
.model NMOS_GENERIC NMOS(VTO=1.5 KP=1e-2 LAMBDA=0.01)
.model PMOS_GENERIC PMOS(VTO=-1.5 KP=5e-3 LAMBDA=0.01)
"""


def get_generic_models():
    """Return generic semiconductor model definitions."""
    return GENERIC_MODELS


# ---------------------------------------------------------------------------
# Netlist text and element helpers
# ---------------------------------------------------------------------------


def spice_text(s):
    """Text for a netlist comment line: control characters become spaces."""
    return "".join(" " if unicodedata.category(ch).startswith("C") else ch
                   for ch in str(s))


def spice_echo(s):
    """Text for a value inside a quoted control-block echo.

    Control characters become spaces; characters that close the quote, redirect
    the output, end the command or expand a variable become _.
    """
    return "".join("_" if ch in '"<>;$`\\' else ch for ch in spice_text(s))


def spice_ident(s):
    """Text for an element-name suffix.

    Whitespace, control characters and the characters SPICE uses to split or
    group tokens (= ( ) , ; { }) become _; ordinary references such as R1-A
    or U1.2 are unchanged.
    """
    return "".join("_" if ch.isspace() or ch in "=(),;{}"
                   or unicodedata.category(ch).startswith("C") else ch
                   for ch in str(s))


def spice_passive_name(ref, kind):
    """Element name for a passive of *kind* ('R', 'C' or 'L').

    SPICE reads the element type from the name's first letter, so a
    designator that starts with another letter is prefixed by the kind
    ('VR1' -> 'R_VR1'); 'R5' stays 'R5'.
    """
    name = spice_ident(ref)
    return name if name[:1].upper() == kind else f"{kind}_{name}"


def spice_element_for_passive(ref, value_si, net1, net2, kind):
    """Generate a SPICE line for a passive component (R, C, or L).

    Args:
        ref: Component reference (e.g., 'R5', 'C3', 'L1', 'VR1')
        value_si: Value in SI base units (ohms, farads, henries)
        net1: First net name
        net2: Second net name
        kind: 'R', 'C' or 'L'

    Returns:
        SPICE element string, e.g., 'R5 net_in net_out 10k'
    """
    return (f"{spice_passive_name(ref, kind)} {_sanitize_net(net1)} {_sanitize_net(net2)} "
            f"{_format_eng(value_si)}")


def _sanitize_net(name):
    """Make a net name safe for SPICE.

    SPICE net names cannot contain spaces, parentheses, or special chars.
    Replace problematic characters with underscores.
    """
    if name is None:
        return "0"  # default to ground
    # Ground detection — common KiCad ground net names
    low = name.lower()
    if low in ("gnd", "earth", "vss", "0"):
        return "0"
    # Replace characters that confuse ngspice
    result = name
    for ch in " (){}[]!@#$%^&*=+|\\;:'\",<>?/":
        result = result.replace(ch, "_")
    result = "".join("_" if unicodedata.category(ch).startswith("C") else ch
                     for ch in result)
    # Net names starting with a digit need a prefix
    if result and result[0].isdigit():
        result = "n" + result
    return result


def _format_eng(value):
    """Format a float in engineering notation for SPICE.

    Examples: 10000 → '10k', 1e-9 → '1n', 4.7e-6 → '4.7u'
    """
    # EQ-075: SI engineering notation formatting
    if value == 0:
        return "0"
    abs_val = abs(value)
    suffixes = [
        (1e12, "T"), (1e9, "G"), (1e6, "Meg"), (1e3, "k"),
        (1, ""), (1e-3, "m"), (1e-6, "u"), (1e-9, "n"), (1e-12, "p"),
        (1e-15, "f"),
    ]
    for threshold, suffix in suffixes:
        if abs_val >= threshold * 0.999:
            scaled = value / threshold
            # Clean up trailing zeros
            if scaled == int(scaled):
                return f"{int(scaled)}{suffix}"
            return f"{scaled:.4g}{suffix}"
    # Very small — use raw scientific notation
    return f"{value:.4e}"
