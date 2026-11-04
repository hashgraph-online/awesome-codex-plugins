"""Net-name heuristics: rail/ground/USB recognition and voltage-from-name (kicad_core). Each predicate is one named policy; do not union them with other skills' lists (see product review U2)."""
import re


def parse_voltage_from_net_name(net_name: str) -> float | None:
    """Try to extract a voltage value from a power net name.

    Examples: '+3V3' → 3.3, '+5V' → 5.0, '+12V' → 12.0, '+1V8' → 1.8,
    'VCC_3V3' → 3.3, '+2.5V' → 2.5, 'VBAT' → None
    """
    if not net_name:
        return None
    # Pattern: digits V digits  (e.g. 3V3 → 3.3, 1V8 → 1.8)
    m = re.search(r'(\d+)V(\d+)', net_name, re.IGNORECASE)
    if m:
        return float(f"{m.group(1)}.{m.group(2)}")
    # Pattern: digits.digits V  or  digits V  (e.g. 3.3V, 5V, 12V)
    m = re.search(r'(\d+\.?\d*)V', net_name, re.IGNORECASE)
    if m:
        return float(m.group(1))
    return None


# KH-343: USB data lines (D+/D-) must not inherit the 5V VBUS fallback —
# they're signal nets, not rails.
USB_DATA_NET_MARKERS = ("USB_D", "USBDP", "USBDM", "USBDN", "DPLUS", "DMINUS")

# is_power_net_name() vocabulary for descriptive rail names (PR #44).
# Control / monitor prefixes: <prefix>_<voltage> is a signal about a rail
# (PWM_5V, EN_5V, SENSE_12V), not the rail itself.
_SIGNAL_PREFIXES = frozenset({
    "PWM", "EN", "ENABLE", "GATE", "SENSE", "SNS", "LEVEL", "TX", "RX",
    "SDA", "SCL", "SCK", "MOSI", "MISO", "CS", "SS", "INT", "IRQ",
    "RST", "RESET", "DIR", "STEP", "CLK", "CLOCK", "ALERT", "FAULT",
    "FLAG", "IO", "GPIO", "INTR", "TRIG", "SYNC", "CTRL", "DATA", "SIG",
    "DRV", "FB", "COMP", "ADC", "DAC",
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
# <voltage><suffix> with these suffixes is a control/monitor line (5VEN,
# 12VPG, 5VOK), not a rail.
_VOLTAGE_SIGNAL_SUFFIXES = frozenset({"EN", "ENABLE", "ON", "OFF", "FB", "PG",
                                      "OK", "DET", "SENSE"})


def is_usb_data_net_name(name_upper: str) -> bool:
    """True if an upper-cased net name looks like a USB data line."""
    return (any(m in name_upper for m in USB_DATA_NET_MARKERS)
            or name_upper.endswith(("D+", "D-")))


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
    if "/" in net_name:
        net_name = net_name.rsplit("/", 1)[-1]
    nu = net_name.upper()
    # Zero-volt ground spellings (0V, 0VA, 0VANA, 0VCC, 0V_A, +0V, ...) are
    # never rails, no matter what pattern rule below would otherwise match
    # (KH-407). Excludes 0V<digit> (0V9, 0V85, 0V95, 0V5) — those are
    # sub-1V rails under the nnVn convention, not ground.
    if re.match(r'^\+?0+V(?!\d)', nu):
        return False
    # Explicit known names
    if nu in ("GND", "VSS", "AGND", "DGND", "PGND", "GNDPWR", "GNDA", "GNDD",
              "VCC", "VDD", "AVCC", "AVDD", "DVCC", "DVDD", "VBUS",
              "VAA", "VIO", "VMAIN", "VPWR", "VSYS", "VBAT", "VCORE",
              "VIN", "VOUT", "VREG", "VBATT",
              "V3P3", "V1P8", "V1P2", "V2P5", "V5P0", "V12P0",
              "VCCA", "VCCD", "VCCIO", "VDDA", "VDDD", "VDDIO"):
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
    # Negative voltage rails (Neg6v, NEG12V)
    if re.match(r'^NEG\d+V', nu):
        return True
    # VDDn, VCCn without underscore separator (VDD5, VDD12, VCC3)
    if re.match(r'^V[CD][CD]\d', nu):
        return True
    # nV_xxx patterns (5V_INT, 12V_SW, 3V_AUX)
    if "_" in nu and re.match(r'^\d+V', nu.split("_")[0]):
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


def is_ground_name(net_name: str | None) -> bool:
    """Check if a net name looks like a ground rail."""
    if not net_name:
        return False
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
    # 0V5) is a sub-1V rail under the nnVn convention, not ground (KH-407).
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
