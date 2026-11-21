"""Net-name heuristics: rail/ground/USB recognition and voltage-from-name (kicad_core). Each predicate is one named policy; do not union them with other skills' lists (see product review U2)."""
import re
from collections.abc import Iterable
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

    A leading '-', 'NEG' or '(-)' makes the rail negative.

    Examples: '+3V3' → 3.3, '+5V' → 5.0, '+12V' → 12.0, '+1V8' → 1.8,
    'VCC_3V3' → 3.3, '+2.5V' → 2.5, '-5V' → -5.0, 'NEG12V' → -12.0,
    '/Analog/-5V' → -5.0, '(-)5V' → -5.0, '/3v3_buck/SW' → None, 'VBAT' → None
    """
    if not net_name:
        return None
    net_name = unescape_string(net_leaf(net_name))
    sign = -1.0 if re.match(r'(-|NEG|\(-\))', net_name, re.IGNORECASE) else 1.0
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
RAIL_SIGNAL_SUFFIXES = _VOLTAGE_SIGNAL_SUFFIXES | frozenset({
    "PGOOD", "PWRGD", "PGD", "GOOD", "SNS", "MON", "DETECT", "CTRL", "CTL",
    "SHDN", "RESET", "RST", "NEN"})
# <control>_..._<supply-tail> (EN_VCC, EN_EXT_VDD) drives or senses the supply; it is not the supply.
_SUPPLY_TAIL_CONTROL_PREFIXES = frozenset({"EN", "ENA", "ENABLE", "PWM", "CTRL", "SENSE",
                                           "SNS", "VSNS"})
# V<number> followed directly by one of these is a rail (V5REG, V12SW, V7.5V) ...
_V_NUMBER_RAIL_WORDS = frozenset({"V", "REG", "SW", "USB", "BAT", "SB", "AUX"})
# ... and by one of these only after a voltage or two digits (V3P3D, V33IO, V36IN):
# V1A, V2OUT are channels.
_V_NUMBER_VOLTAGE_SUFFIXES = frozenset({"IO", "IN", "OUT", "O", "A", "D", "N", "P"})
_V_NUMBER = re.compile(r'^V(\d+)([VP]\d*|\.\d+)?')


def _is_v_number_rail(nu: str) -> bool:
    """V<number> rails: V12, V33, V3V3, V1P8, V3.3, V33IO, V3P3D, V1P8_SW, V3_3.

    A word that follows the number directly (V1AMP1, V2FREQ, V1OUT, V16F) or after
    '.' or ':' (V24.RX, V24:TX) names a signal, as does a signal word after a
    separator (V1_CLK1, V4_OUT, V36_MEASURE) or a bare index after a voltage (V2V_0)."""
    m = _V_NUMBER.match(nu)
    if not m:
        return False
    digits, volt, rest = m.group(1), m.group(2) or "", nu[m.end():]
    if not rest:
        return bool(volt) or len(digits) >= 2   # V1, V2 are node names
    if rest[0] in "_-":
        word = re.split(r'[_\-]', rest[1:])[0]
        if word.isdigit():
            return not volt and len(digits) == 1   # V3_3 is 3.3 V; V2V_0 is an index
        word = word.rstrip("0123456789")
        # After a voltage part (V3V3_OUT) the number is a voltage, not a channel (V4_OUT).
        return (bool(word) and word not in RAIL_SIGNAL_SUFFIXES and word not in _SIGNAL_PREFIXES
                and (bool(volt) or word not in ("OUT", "MEAS", "MEASURE")))
    letters = re.match(r'[A-Z]+', rest)
    if letters:
        tail = letters.group(0)
        if len(tail) < len(rest) and rest[len(tail)] not in "_-":
            return False
        return tail in _V_NUMBER_RAIL_WORDS or (
            (bool(volt) or len(digits) >= 2) and tail in _V_NUMBER_VOLTAGE_SUFFIXES)
    return False


# D+ / D- as the whole name or after a separator (USB_D+, MCU-D-, /USB/D+), or after USB<n>
# (USBD+, USB2D-); not the tail of a word (HOLD-, LED-, SPEED-, RTD+).
_USB_D_SUFFIX = re.compile(r"(?:^|[^A-Z0-9]|USB\d*)D[+-]$")


# USB_DTR, USB_DET: a USB_D marker followed by a letter that spells none of DP/DM/DN/DATA;
# USB_DP_PU, USB_DM_EN: a GPIO that controls a data line, not the line itself.
_USB_SIGNAL_NAME = re.compile(r"USB_D[B-LOQ-Z]|USB_D[PMN]_?(?:PU|PULLUP|PULL_UP|EN|CTRL)\b")


def is_usb_signal_net_name(name_upper: str) -> bool:
    """True if an upper-cased net name carries a USB marker but names a control or
    detect signal (USB_DTR, USB_DET, USB_DP_PU), neither a data line nor VBUS."""
    return bool(_USB_SIGNAL_NAME.search(name_upper))


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
    # Strip hierarchical sheet path prefix (e.g., "/Power Supply/VCC" → "VCC")
    # The rail set matches only by full name: a sheet-local label is its own net even
    # when its leaf names a power symbol elsewhere (KiCad joins local labels per sheet).
    # Split on a real '/' only, then read the shown name: an escaped {slash} is part of
    # the label (SDIO_CMD{slash}3V3).
    net_name = unescape_string(net_name.rsplit("/", 1)[-1])
    if "/" in net_name:
        # A label that pairs names with an escaped slash is a rail only when every part
        # is one (5V{slash}3V3); SDIO_CMD{slash}3V3 is a signal at 3.3 V.
        parts = [p for p in net_name.split("/") if p]
        return bool(parts) and all(is_power_net_name(p) for p in parts)
    nu = net_name.upper()
    # Zero-volt ground spellings (0V, 0VA, 0VANA, 0VCC, 0V_A, +0V, ...) are
    # never rails, no matter what pattern rule below would otherwise match.
    # Excludes 0V<digit> (0V9, 0V85, 0V95, 0V5) — those are
    # sub-1V rails under the nnVn convention, not ground.
    if re.match(r'^\+?0+(\.0+)?V(?!\d)', nu):
        return False
    if "_" in nu and nu.rsplit("_", 1)[-1] in RAIL_SIGNAL_SUFFIXES:
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
              "VEE", "VPP", "VM", "VNEG", "V-", "VMOT"):
        return True
    # Pattern-based detection
    if nu.startswith("+") or nu.startswith("V+"):
        return True
    # Vnn, VnnV patterns (V3V3, V1V8, V5V0, V33IO)
    if _is_v_number_rail(nu):
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
    if m and (m.group(1) or "") not in RAIL_SIGNAL_SUFFIXES and not (
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
    if m and m.group(1) not in _SIGNAL_PREFIXES and m.group(1) not in RAIL_SIGNAL_SUFFIXES:
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
        if last_seg in _SUPPLY_TAILS and first_seg not in _SUPPLY_TAIL_CONTROL_PREFIXES:
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
    if not net_name or unescape_string(net_name.rsplit("/", 1)[-1]).upper() not in PIN_GUARDED_RAIL_NAMES:
        return False
    kinds = [(str(t or "").split("+")[0], on_ic) for t, on_ic in pins]
    if any(t in ("power_in", "power_out") for t, _ in kinds):
        return False
    return any(t in IC_SIGNAL_PIN_TYPES and on_ic is not False for t, on_ic in kinds)


# A ground word as one token of a longer name: a domain ground (AGND_CODEC, PGND_3V3,
# CAN_GND_ISO) or a switched return (HEATER_GND_1, ESP_GND2). A VSS token is left out:
# DAC_VSS or SENSOR_VSS can name a negative supply or the signal that sets one.
_GROUND_TOKEN = re.compile(r'^[ADPSF]?GND[A-Z0-9]*$|^GROUND$')
# A virtual ground (VGND, HP_VGND, VIRTUAL_GND) sits at mid-rail, not at 0 V.
_VIRTUAL_GROUND_TOKEN = re.compile(r'^(?:VGND|VIRT)')


def _name_tokens(leaf_upper: str) -> list[str]:
    return [t for t in re.split(r'[_.\s]+', leaf_upper) if t]


def is_virtual_ground_name(net_name: str | None) -> bool:
    """True for a virtual ground (VGND, VGND1, HP_VGND, Virtual_Ground): a mid-rail node."""
    if not net_name:
        return False
    leaf = unescape_string(net_name.rsplit("/", 1)[-1]).upper()
    return any(_VIRTUAL_GROUND_TOKEN.match(t) for t in _name_tokens(leaf))


def is_ground_name(net_name: str | None, power_rails: set[str] | None = None) -> bool:
    """Check if a net name looks like a ground rail.

    A net named ``0`` or ``COM`` is ground only when a power symbol names it (``0`` is
    the SPICE ground symbol); a connector pin labelled ``0`` is a signal and ``COM`` is
    often a switch or transformer common. A virtual ground (VGND) is not ground.
    """
    if not net_name:
        return False
    if net_name == "0":
        return bool(power_rails) and "0" in power_rails
    full_name = net_name
    # Strip hierarchical sheet path prefix (e.g., "/Power Supply/GND" → "GND") on a real '/'
    # only: an escaped {slash} is part of the label (Net-(VR1-ADJ{slash}GND) is a pin net).
    net_name = unescape_string(net_name.rsplit("/", 1)[-1])
    nu = net_name.upper()
    if nu == "COM":
        return bool(power_rails) and full_name in power_rails
    tokens = _name_tokens(nu)
    if any(_VIRTUAL_GROUND_TOKEN.match(t) for t in tokens):
        return False
    # Exact matches
    if nu in ("GND", "VSS", "AGND", "DGND", "PGND", "GNDPWR", "GNDA", "GNDD",
              "SGND", "0V", "AVSS", "DVSS", "GROUND"):
        return True
    # Any zero-volt spelling (0VA, 0Vo, 0VANA, 0VCC, 0V_A, +0V, ...) is
    # ground, not just the literal "0V" — but 0V<digit> (0V9, 0V85, 0V95,
    # 0V5) is a sub-1V rail under the nnVn convention, not ground, and a
    # second voltage (0V_10V, 0V_32V) names a 0-10 V interface signal.
    m = re.match(r'^\+?0+V(?!\d)([A-Z_][A-Z0-9_]*)?$', nu)
    if m:
        return not re.search(r'\d(?:\.\d+)?V', m.group(1) or "")
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
    # A pin-named net (Net-(U1-GND), unconnected-(U1-GND-Pad3)) is not a ground.
    return "(" not in nu and any(_GROUND_TOKEN.match(t) for t in tokens)


def is_vss_name(net_name: str | None) -> bool:
    """True for a VSS-family net name (VSS*, AVSS, DVSS; sheet path stripped); VSS can be a
    negative supply."""
    if not net_name:
        return False
    return unescape_string(net_name.rsplit("/", 1)[-1]).upper().startswith(("VSS", "AVSS", "DVSS"))


_SPLIT_RAIL_N_LEAF = re.compile(r"(\d+V\d+)_N")


def negative_split_rails(net_names: Iterable[str]) -> set[str]:
    """The nets of *net_names* whose leaf is ``<n>V<n>_N`` (4V5_N) beside a ``<n>V<n>_P``
    twin: the negative half of a split supply. Alone, ``1V5_N`` is only a name."""
    by_leaf: dict[str, list[str]] = {}
    for name in net_names:
        by_leaf.setdefault(unescape_string(net_leaf(name)).upper().lstrip("+"), []).append(name)
    found: set[str] = set()
    for leaf, names in by_leaf.items():
        m = _SPLIT_RAIL_N_LEAF.fullmatch(leaf)
        if m and f"{m.group(1)}_P" in by_leaf:
            found.update(names)
    return found


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
