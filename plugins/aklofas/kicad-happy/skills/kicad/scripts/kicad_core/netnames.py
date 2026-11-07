"""Net-name heuristics: rail/ground/USB recognition and voltage-from-name (kicad_core). Each predicate is one named policy; do not union them with other skills' lists (see product review U2)."""
import re
from fnmatch import fnmatch

from kicad_core.sexp import unescape_string


def net_leaf(name: str) -> str:
    """The net's own name: a sheet path (``/<sheet>/<label>``) names the sheet, not the net.

    Only a name starting with '/' carries a path, and an escaped ``{slash}`` is part of
    the label; a legacy root label such as ``1V/Oct`` is returned whole.
    """
    if name.startswith("/"):
        return name.rsplit("/", 1)[-1]
    return name


def configured_rail_voltage(overrides: dict, net: str | None) -> float | None:
    """The ``voltage_overrides`` entry for *net*: by full name, then its leaf, then the
    leaf as KiCad displays it (users write ``+3V3``, not ``/<uuid>/+3V3``)."""
    if not net or not overrides:
        return None
    leaf = net_leaf(net)
    for key in (net, leaf, unescape_string(leaf)):
        v = overrides.get(key)
        if v is not None:
            return v
    return None


def rail_matches(patterns, net: str | None) -> bool:
    """True if an ``ignore``/``flag`` glob matches *net*'s full name or its leaf."""
    if not net or not patterns:
        return False
    leaf = net_leaf(net)
    return any(fnmatch(net, pat) or fnmatch(leaf, pat) for pat in patterns)


def parse_voltage_from_net_name(net_name: str) -> float | None:
    """Try to extract a voltage value from a power net name's own name (its leaf).

    A leading '-' or 'NEG' makes the rail negative.

    Examples: '+3V3' → 3.3, '+5V' → 5.0, '+12V' → 12.0, '+1V8' → 1.8,
    'VCC_3V3' → 3.3, '+2.5V' → 2.5, '-5V' → -5.0, 'NEG12V' → -12.0,
    '/Analog/-5V' → -5.0, '/3v3_buck/SW' → None, 'VBAT' → None
    """
    if not net_name:
        return None
    net_name = unescape_string(net_leaf(net_name))
    sign = -1.0 if re.match(r'(-|NEG)', net_name, re.IGNORECASE) else 1.0
    # Pattern: digits V digits  (e.g. 3V3 → 3.3, 1V8 → 1.8)
    m = re.search(r'(\d+)V(\d+)', net_name, re.IGNORECASE)
    if m:
        return sign * float(f"{m.group(1)}.{m.group(2)}")
    # Pattern: digits.digits V  or  digits V  (e.g. 3.3V, 5V, 12V)
    m = re.search(r'(\d+(?:\.\d+)?)V', net_name, re.IGNORECASE)
    if m:
        return sign * float(m.group(1))
    return None


# USB data lines (D+/D-) must not inherit the 5V VBUS fallback —
# they're signal nets, not rails.
USB_DATA_NET_MARKERS = ("USB_D", "USBDP", "USBDM", "USBDN", "DPLUS", "DMINUS")

# is_power_net_name() vocabulary for descriptive rail names.
# Control / monitor prefixes: <prefix>_<voltage> is a signal about a rail
# (PWM_5V, EN_5V, SENSE_12V), not the rail itself.
_SIGNAL_PREFIXES = frozenset({
    "PWM", "EN", "ENABLE", "GATE", "SENSE", "SNS", "LEVEL", "TX", "RX",
    "SDA", "SCL", "SCK", "MOSI", "MISO", "CS", "SS", "INT", "IRQ",
    "RST", "RESET", "DIR", "STEP", "CLK", "CLOCK", "ALERT", "FAULT",
    "FLAG", "IO", "GPIO", "INTR", "TRIG", "SYNC", "CTRL", "DATA", "SIG",
    "DRV", "FB", "COMP", "ADC", "DAC", "ENA", "SWD", "SWDIO", "SWCLK", "VSNS",
})
# Prefixes that make <prefix>_<voltage> / <prefix>_VOUT a rail
# (RAW_5V, USB_5V, ISO_3V3, SYS_VOUT, BOOST_VOUT).
_POWER_PREFIXES = frozenset({
    "RAW", "FUSED", "SW", "SWITCHED", "FILT", "FILTERED", "USB", "SYS",
    "MAIN", "AUX", "BAT", "BATT", "DC", "EXT", "VREG", "REG", "CLEAN",
    "ISO", "BACKUP", "PWR", "BOARD", "MCU", "BOOST", "BUCK", "LDO",
})
# <anything>_<tail> is a supply regardless of prefix (SERVO_VCC, ADC_AVDD).
_SUPPLY_TAILS = frozenset({"VCC", "VDD", "AVCC", "AVDD", "DVCC", "DVDD",
                           "VCCIO", "VDDIO"})
# <tail>s that can also name a sense tap (ADC_VBUS, SNS_VIN) — gated on the
# prefix not being a signal prefix.
_RAIL_TAILS_GATED = frozenset({"VBUS", "VIN", "VBAT", "VBATT", "VSYS", "VREG"})
# -<name> with one of these is a negative supply (-BATT, -VIN), not an active-low signal.
_NEGATIVE_SUPPLY_NAMES = frozenset({"BAT", "BATT", "VBAT", "VBATT", "VIN", "VCC",
                                    "VDD", "VEE", "VS"})
# <voltage><suffix> with these suffixes is a control/monitor line (5VEN,
# 12VPG, 5VOK), not a rail.
_VOLTAGE_SIGNAL_SUFFIXES = frozenset({"EN", "ENABLE", "ON", "OFF", "FB", "PG",
                                      "OK", "DET", "SENSE"})
# A rail name followed by one of these after an underscore (VCC_EN, 3V3_PG,
# VBUS_SENSE) is a signal about the rail. INT is left out: 5V_INT is a rail.
_RAIL_SIGNAL_SUFFIXES = _VOLTAGE_SIGNAL_SUFFIXES | frozenset({
    "PGOOD", "PWRGD", "PGD", "GOOD", "SNS", "MON", "DETECT", "CTRL", "CTL",
    "SHDN", "RESET", "RST", "NEN"})


# D+ / D- as the whole name or after a separator (USB_D+, MCU-D-, /USB/D+), or after USB<n>
# (USBD+, USB2D-); not the tail of a word (HOLD-, LED-, SPEED-, RTD+).
_USB_D_SUFFIX = re.compile(r"(?:^|[^A-Z0-9]|USB\d*)D[+-]$")


def is_usb_data_net_name(name_upper: str) -> bool:
    """True if an upper-cased net name looks like a USB data line."""
    if any(m in name_upper for m in USB_DATA_NET_MARKERS):
        return True
    if not name_upper.endswith(("D+", "D-")):
        return False
    return "USB" in name_upper or bool(_USB_D_SUFFIX.search(name_upper))


def is_power_net_name(net_name: str | None, power_rails: set[str] | None = None) -> bool:
    """Check if a net name looks like a power rail by naming convention.

    Covers both power-symbol-defined rails (via power_rails set) and nets that
    look like power from their name alone — including local/hierarchical labels
    like VDD_nRF, VBATT_MCU, V_BATT that lack an explicit power: symbol.
    """
    if not net_name:
        return False
    if power_rails and net_name in power_rails:
        return True
    # Name heuristics read the shown name: an escaped {slash} is not a sheet separator
    # to KiCad, but the rules below were written against the decoded name.
    net_name = unescape_string(net_name)
    # Strip hierarchical sheet path prefix (e.g., "/Power Supply/VCC" → "VCC")
    # The rail set matches only by full name: a sheet-local label is its own net even
    # when its leaf names a power symbol elsewhere (KiCad joins local labels per sheet).
    if "/" in net_name:
        net_name = net_name.rsplit("/", 1)[-1]
    nu = net_name.upper()
    # Zero-volt ground spellings (0V, 0VA, 0VANA, 0VCC, 0V_A, +0V, ...) are
    # never rails, no matter what pattern rule below would otherwise match.
    # Excludes 0V<digit> (0V9, 0V85, 0V95, 0V5) — those are
    # sub-1V rails under the nnVn convention, not ground.
    if re.match(r'^\+?0+(\.0+)?V(?!\d)', nu):
        return False
    if "_" in nu and nu.rsplit("_", 1)[-1] in _RAIL_SIGNAL_SUFFIXES:
        return False
    # Negative rails (-12V, -2V5, -5V_F, -BATT, -VIN). A leading '-' also marks an
    # active-low signal (-RESET, -CS), so the rest must be a voltage or a supply name.
    if nu.startswith("-"):
        rest = nu[1:]
        if rest.split("_")[0] in _NEGATIVE_SUPPLY_NAMES or (
                re.match(r'^\d', rest) and is_power_net_name(rest)):
            return True
    # Explicit known names
    if nu in ("GND", "VSS", "AGND", "DGND", "PGND", "GNDPWR", "GNDA", "GNDD",
              "VCC", "VDD", "AVCC", "AVDD", "DVCC", "DVDD", "VBUS",
              "VAA", "VIO", "VMAIN", "VPWR", "VSYS", "VBAT", "VCORE",
              "VIN", "VOUT", "VREG", "VBATT",
              "V3P3", "V1P8", "V1P2", "V2P5", "V5P0", "V12P0",
              "VCCA", "VCCD", "VCCIO", "VDDA", "VDDD", "VDDIO",
              "VEE", "VPP", "VM", "VNEG"):
        return True
    # Pattern-based detection
    if nu.startswith("+") or nu.startswith("V+"):
        return True
    # Vnn, VnnV patterns (V3V3, V1V8, V5V0)
    if len(nu) >= 3 and nu[0] == "V" and nu[1].isdigit():
        return True
    # nnVn patterns (3V3, 5V0, 12V0, 1V8) — industry-standard voltage naming
    if re.match(r'^\d+V\d', nu):
        return True
    # Plain and letter-suffixed voltages (5V, 12V, 24V, 5VSB, 12VIN, 5VUSB).
    # 0V is a ground name (is_ground_name); a control suffix (5VEN, 12VPG,
    # 5VOK) names a signal about the rail, not the rail.
    m = re.match(r'^(\d+)V([A-Z][0-9A-Z]*)?$', nu)
    if m and int(m.group(1)) != 0 and (m.group(2) or "") not in _VOLTAGE_SIGNAL_SUFFIXES:
        return True
    # Decimal voltages (3.3V, 5.5V, 3.3V_OUT, 1.25V_REF). 3.3VPG and 3.3V_SDA are
    # signals at or about the rail.
    m = re.match(r'^\d+\.\d+V([A-Z][0-9A-Z]*)?(_.*)?$', nu)
    if m and (m.group(1) or "") not in _RAIL_SIGNAL_SUFFIXES and not (
            m.group(2) and any(seg in _SIGNAL_PREFIXES for seg in m.group(2).split("_"))):
        return True
    # Negative voltage rails (Neg6v, NEG12V)
    if re.match(r'^NEG\d+V', nu):
        return True
    # VDDn, VCCn without underscore separator (VDD5, VDD12, VCC3)
    if re.match(r'^V[CD][CD]\d', nu):
        return True
    # nV_xxx patterns (5V_INT, 12V_SW, 3V_AUX)
    if "_" in nu and re.match(r'^\d+V', nu.split("_")[0]):
        return True
    # A voltage behind a domain prefix (MCU3V3, AVDD1V8_PLL, D+5V, CAN+5V); a control
    # prefix (PWM3V3, EN1V8, PWRGD1V2, SWDIO1V8, TX+5V) names a signal at or about the rail.
    m = (re.match(r'^([A-Z]{2,5})\d+V\d+$', nu.split("_")[0])
         or re.match(r'^([A-Z]{1,4})\+\d+(\.\d+)?V\d*$', nu))
    if m and m.group(1) not in _SIGNAL_PREFIXES and m.group(1) not in _RAIL_SIGNAL_SUFFIXES:
        return True
    # PWRnVn patterns (PWR3V3, PWR1V8, PWR5V0)
    if re.match(r'^PWR\d', nu):
        return True
    # VDD_xxx, VCC_xxx, VBAT_xxx, VBATT_xxx variants (local label power nets)
    # Split on _ and check if first segment is a known power prefix
    first_seg = nu.split("_")[0] if "_" in nu else ""
    if first_seg in ("VDD", "VCC", "AVDD", "AVCC", "DVDD", "DVCC", "VBAT",
                      "VBATT", "VSYS", "VBUS", "VMAIN", "VPWR", "VCORE",
                      "VDDIO", "VCCIO", "VIN", "VOUT", "VREG", "POW",
                      "PWR", "VMOT", "VHEAT", "REGIN", "REGOUT"):
        return True
    # Descriptive rails: <power-prefix>_<voltage> (RAW_5V, USB_5V, ISO_3V3),
    # <anything>_<supply-tail> (USB_VBUS, SERVO_VCC, LED_VIN) and
    # <power-prefix>_VOUT (SYS_VOUT, BOOST_VOUT). Signal prefixes (PWM_5V,
    # EN_5V, SENSE_12V, ADC_VBUS) stay signals so PU-001 & co. still see them;
    # _VOUT needs the power prefix because about half the corpus's *_VOUT nets
    # are op-amp / sensor outputs (OPAMP1_VOUT, MIC_VOUT, CURRENTSENSE_VOUT).
    if first_seg:
        last_seg = nu.rsplit("_", 1)[-1]
        if last_seg in _SUPPLY_TAILS:
            return True
        if first_seg not in _SIGNAL_PREFIXES:
            if last_seg in _RAIL_TAILS_GATED:
                return True
            if first_seg in _POWER_PREFIXES and (
                    last_seg == "VOUT" or re.match(r'^\d+V[0-9A-Z]*$', last_seg)):
                return True
    return False


# Supply-pin names that also name signals: a PIC's MCLR/VPP line, a measured node "VM".
PIN_GUARDED_RAIL_NAMES = frozenset({"VPP", "VM"})
IC_SIGNAL_PIN_TYPES = frozenset({"input", "output", "bidirectional", "tri_state",
                                 "open_collector", "open_emitter"})


def is_pin_guarded_signal(net_name: str | None, pins) -> bool:
    """True when *net_name* is power only by its VPP/VM name and its pins say it is a
    signal: an IC signal pin on it and no power_in/power_out pin. *pins* holds
    ``(pin_type, on_ic)`` per pin, ``on_ic`` None where the part kind is unknown (a board
    pad; KiCad 7+ pads carry the pin type). Callers skip nets in the rail set first."""
    if not net_name or unescape_string(net_name).rsplit("/", 1)[-1].upper() not in PIN_GUARDED_RAIL_NAMES:
        return False
    kinds = [(str(t or "").split("+")[0], on_ic) for t, on_ic in pins]
    if any(t in ("power_in", "power_out") for t, _ in kinds):
        return False
    return any(t in IC_SIGNAL_PIN_TYPES and on_ic is not False for t, on_ic in kinds)


def is_ground_name(net_name: str | None, power_rails: set[str] | None = None) -> bool:
    """Check if a net name looks like a ground rail.

    A net named ``0`` is ground only when a power symbol names it (the SPICE ground
    symbol); a connector pin labelled ``0`` is a signal.
    """
    if not net_name:
        return False
    if net_name == "0":
        return bool(power_rails) and "0" in power_rails
    net_name = unescape_string(net_name)
    # Strip hierarchical sheet path prefix (e.g., "/Power Supply/GND" → "GND")
    if "/" in net_name:
        net_name = net_name.rsplit("/", 1)[-1]
    nu = net_name.upper()
    # Exact matches
    if nu in ("GND", "VSS", "AGND", "DGND", "PGND", "GNDPWR", "GNDA", "GNDD",
              "SGND", "COM", "0V"):
        return True
    # Any zero-volt spelling (0VA, 0Vo, 0VANA, 0VCC, 0V_A, +0V, ...) is
    # ground, not just the literal "0V" — but 0V<digit> (0V9, 0V85, 0V95,
    # 0V5) is a sub-1V rail under the nnVn convention, not ground.
    if re.match(r'^\+?0+V(?!\d)([A-Z_][A-Z0-9_]*)?$', nu):
        return True
    # Battery-negative rails used as circuit ground in single-supply designs.
    # Narrow exact-match set — deliberately excludes V-/VEE which are
    # legitimate bipolar negative supply rails, not ground.
    if nu in ("BATT-", "BAT-", "VBAT-", "VBATT-", "BATTERY-",
              "BATT_N", "BAT_N", "VBAT_N"):
        return True
    # Prefix/suffix patterns: GND_ISO, GND_SEC, GNDISO, etc.
    if nu.startswith("GND") or nu.endswith("GND"):
        return True
    # VSS variants
    if nu.startswith("VSS"):
        return True
    return False



def is_vss_name(net_name: str | None) -> bool:
    """True for a VSS-prefixed net name (sheet path stripped); VSS can be a negative supply."""
    if not net_name:
        return False
    return unescape_string(net_name).rsplit("/", 1)[-1].upper().startswith("VSS")


_UUID_RE = re.compile(
    r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
    re.IGNORECASE,
)


def _clean_hierarchical_name(name: str) -> str:
    """Strip UUID path prefixes from hierarchical net/rail names.

    ``/201ab4ae-...-c6b37cf9a2b1/VIN`` → ``VIN``
    """
    if '/' in name and _UUID_RE.search(name):
        return name.rsplit('/', 1)[-1]
    return name
