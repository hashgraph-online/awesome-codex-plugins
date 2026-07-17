"""
Shared utility functions for KiCad schematic and PCB analyzers.

Contains component classification, value parsing, net name classification,
and other helpers extracted from analyze_schematic.py.
"""

import math
import os
import re


# Coordinate matching tolerance (mm) — used across net building and connectivity analysis
COORD_EPSILON = 0.01

# Legacy .sch files use integer mils (1/1000 inch).  The conversion pipeline
# (mil * 0.0254 → round(4) → rotate via trig → round(4)) accumulates
# floating-point error that can exceed COORD_EPSILON.  Snapping back to the
# nearest mil grid after all transforms eliminates the drift.
_MIL_MM = 0.0254  # 1 mil in mm

def snap_to_mil_grid(x_mm: float) -> float:
    """Snap a mm coordinate to the nearest mil grid point."""
    return round(x_mm / _MIL_MM) * _MIL_MM

# Regulator Vref lookup table — maps part number prefixes to their internal
# reference voltage.  Used by the feedback divider Vout estimator instead of
# guessing from a list.  Lookup uses longest-prefix-match so that specific
# entries (e.g. LMR51420=0.6V) beat broader ones (e.g. LMR514=0.8V).
# When a part isn't found here the analyzer falls back to the heuristic sweep.
# Sources: DigiKey parametric data + manufacturer datasheets (verified 2026-04-12) (KH-236 collision audit)
_REGULATOR_VREF: dict[str, float] = {
    # TI switching regulators — verified against TI datasheets + DigiKey 2026-04-12
    "TPS6100": 0.5,                                               # TPS61000/01 FB = 0.5V
    "TPS6102": 0.595,  "TPS6103": 0.595,                          # TPS61020/23/30 FB = 0.595V
    "TPS5430": 1.221,  "TPS5450": 1.221,  "TPS5410": 1.221,     # TPS5430/50/10 Vref = 1.221V
    "TPS54160": 0.8,   "TPS54260": 0.8,   "TPS54360": 0.8,      # TPS541x0/542x0/543x0 FB = 0.8V
    "TPS54040": 0.8,   "TPS54060": 0.8,                          # TPS54040/60 Vref = 0.8V
    "TPS54302": 0.596, "TPS54308": 0.596,                        # TPS54302/08 FB = 0.596V (KH-237 verified)
    # TPS56 family — split per DigiKey verification (was single 'TPS56': 0.6)
    "TPS56339": 0.8,   "TPS56637": 0.6,                          # TPS56339 = 0.8V, TPS56637 = 0.6V
    "TPS560200": 0.8,                                             # TPS560200 VSENSE = 0.8V
    "TPS560430": 1.0,                                             # TPS560430 VOUT accuracy (integrated FB)
    "TPS561": 0.6,                                                # TPS561201/243 = 0.6-0.76V, use 0.6
    "TPS562": 0.768,                                              # TPS562201/08 = 0.768V
    "TPS5632": 0.76,                                              # TPS563200 = 0.76V
    "TPS5633": 0.8,                                               # TPS563300 = 0.8V
    "TPS5652": 0.6,    "TPS5654": 0.6,                           # TPS565208/564247 = 0.6V
    "TPS566": 0.6,                                                # TPS566238 = 0.6V
    "TPS56A": 0.6,                                                # TPS56A37 = 0.6V
    # TPS63 buck-boost
    "TPS6300": 0.5,    "TPS6301": 0.5,                           # TPS63000/01 VFB = 0.5V
    "TPS6310": 0.5,                                               # TPS631000 VFB = 0.5V
    # TI LMR family
    "LMR51410": 0.6,   "LMR51420": 0.6,   "LMR51430": 0.6,       # LMR51410/20/30 Vref = 0.6V
    "LMR51440": 0.8,   "LMR51460": 0.8,                          # LMR51440/60 Vref = 0.8V
    "LMR51610": 0.6,   "LMR51620": 0.6,   "LMR51630": 0.6,       # LMR51610/20/30 Vref = 0.6V
    "LMR51640": 0.8,   "LMR51660": 0.8,                          # LMR51640/60 Vref = 0.8V
    "LMR336": 1.0,     "LMR338": 1.0,                            # LMR33630/60 Vref = 1.0V
    "LMR380": 1.0,                                                # LMR38010 VFB = 1.0V
    "LM258": 1.23,     "LM259": 1.23,                            # LM2596/LM2585 VFB = 1.23V (adj variants)
    "LMZ2": 0.795,                                                # LMZ23610 VFB = 0.795V
    "LM614": 1.0,      "LM619": 1.0,                             # LM61495 VFB = 1.0V
    # TI LDOs — TPS7A split per DigiKey verification (was single 'TPS7A': 1.19)
    "TPS7A49": 1.194,                                             # TPS7A4901 VFB = 1.194V
    "TPS7A45": 1.21,                                              # TPS7A4501 VFB = 1.21V
    "TPS7A47": 1.4,                                               # TPS7A4701 VFB = 1.4V
    "TPS7A25": 1.24,                                              # TPS7A25xx VFB = 1.24V
    "TPS7A26": 1.24,                                              # TPS7A2601 VFB = 1.24V
    "TPS7A92": 0.8,                                               # TPS7A92xx VFB = 0.8V
    "TPS7A70": 0.5,                                               # TPS7A7002 VFB = 0.5V
    "TPS7A73": 0.9,                                               # TPS7A7300 VFB = 0.9V
    "TPS7A30": 1.18,   "TPS7A33": 1.18,                          # TPS7A30xx/33xx negative, |Vref| = 1.18V
    "TPS7A16": 1.2,                                               # TPS7A1601 VFB = 1.2V
    "TLV759": 0.55,                                               # TLV759P (adjustable) FB = 0.55V
    "TPS736": 1.204,                                              # TPS73601/TPS736xx VFB = 1.204V
    # Analog Devices / Linear Tech
    "LT361": 0.6,      "LT362": 0.6,                             # LTC3610/3620 VFB = 0.6V
    "LT810": 0.97,     "LT811": 0.97,                            # LT8610/8614 VFB = 0.970V
    "LT860": 0.97,     "LT862": 0.97,                            # LT8640/8620 VFB = 0.970V
    "LT871": 1.213,                                               # LT8710 FBX = 1.213V
    "LTM46": 0.6,                                                 # LTM4600 VFB = 0.6V
    # Richtek
    "RT5": 0.6,         "RT6": 0.6,                              # RT5785/RT6150 VFB = 0.6V
    "RT2875": 0.6,                                                # RT2875 VFB = 0.6V
    # MPS — split per DigiKey verification (was single 'MP2': 0.8)
    "MP1": 0.8,                                                    # MP1584 VFB = 0.8V
    "MP2307": 0.925,                                               # MP2307 VFB = 0.925V (DigiKey verified)
    "MP2315": 0.8,                                                 # MP2315 VFB = 0.8V
    "MP2338": 0.5,                                                 # MP2338 VFB = 0.5V (DigiKey verified)
    "MP2359": 0.81,                                                # MP2359 VFB = 0.81V (DigiKey verified)
    "MP2384": 0.6,                                                 # MP2384 VFB = 0.6V (DigiKey verified)
    "MP2403": 0.8,                                                 # MP2403 VFB = 0.8V
    "MP2451": 0.8,                                                 # MP2451 VFB = 0.8V
    "MP2459": 0.81,                                                # MP2459 VFB = 0.81V
    "MP2236": 0.6,                                                 # MP2236 VFB = 0.6V
    "MP2143": 0.6,                                                 # MP2143 VFB = 0.6V
    "MP2162": 0.6,                                                 # MP2162 VFB = 0.6V
    "MP2303": 0.8,                                                 # MP2303 VFB = 0.8V
    "MP28167": 1.0,                                                # MP28167 VFB = 1.0V (DigiKey verified)
    # Microchip — MIC29 kept for adjustable variant only
    "MIC29": 1.24,                                                # MIC29150/29300 adj Vref = 1.24V
    # Diodes Inc — AP73 split (was 'AP73': 0.6, 'AP736': 0.8)
    "AP633": 0.8,                                                 # AP63356/AP63357 VFB = 0.8V
    "AP632": 0.8,                                                 # AP63200/AP63203/AP63205 VFB = 0.8V
    "AP7335": 0.8,                                                # AP7335 adjustable VFB = 0.8V
    "AP7362": 0.6,     "AP7363": 0.6,                            # AP7362/63 adjustable VFB = 0.6V
    "AP7365": 0.8,     "AP7366": 0.8,                            # AP7365/66 adjustable VFB = 0.8V
    "AP2112": 0.8,                                                # AP2112 adjustable Vref = 0.8V
    "AP3015": 1.23,                                               # AP3015A VFB = 1.23V
    # ST
    "LD1117": 1.25,    "LDL1117": 1.25,   "LD33": 1.25,         # LD1117 family Vref = 1.25V
    # ON Semi
    "NCP1117": 1.25,                                              # NCP1117 Vref = 1.25V
    # SY (Silergy) — kept as-is, SY8088/8113 all 0.6V (verified clean)
    "SY8": 0.6,                                                   # SY8089/8113 FB = 0.6V
    # Maxim
    "MAX5035": 1.22,    "MAX5033": 1.22,                          # MAX5035/33 VFB = 1.22V
    "MAX1771": 1.5,     "MAX1709": 1.25,                          # MAX1771 Vref = 1.5V, MAX1709 VFB = 1.25V
    "MAX17760": 0.8,                                               # MAX17760 FB = 0.8V
    # ISL (Renesas/Intersil)
    "ISL854": 0.6,      "ISL850": 0.8,                            # ISL85410 = 0.6V, ISL85003 = 0.8V
    # XL (XLSEMI)
    "XL70": 1.25,                                                  # XL7015 VFB = 1.25V
    # TI misc
    "TPS6291": 0.8,                                                # TPS62912 VFB = 0.8V
    "LM2267": 1.285,                                               # LM22676 VFB = 1.285V (adj variant)
    # Generic adjustable regulators
    "LM317": 1.25,     "LM337": 1.25,
    "AMS1117": 1.25,   "AMS1085": 1.25,
    "LM1117": 1.25,
    # REMOVED (KH-236): LM78, LM79 — fixed-output only, suffix parser handles them
    # REMOVED (KH-236): AP73 broad prefix — split into AP7335/AP7362/AP7363/AP7365/AP7366
    # REMOVED (KH-236): AP736 broad prefix — split into AP7365/AP7366
    # REMOVED (KH-236): MP2 broad prefix — split into per-MPN entries
    # REMOVED (KH-236): TPS7A broad prefix — split into per-sub-family entries
    # REMOVED (KH-236): TPS56 broad prefix — split into per-sub-family entries
}

# Keywords for classifying MOSFET/BJT load type from net names.
# Used by _classify_load() for transistor analysis and by net classification
# for the "output_drive" net class.  Keys are load type names, values are
# keyword tuples matched as substrings of the uppercased net name.
# Avoid short prefixes that appear inside unrelated words:
#   "SOL" matches MISO_LEVEL, ISOL → use SOLENOID only
#   "MOT" matches REMOTE → use MOTOR only
_LOAD_TYPE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "motor": ("MOTOR",),
    "heater": ("HEAT", "HTR", "HEATER"),
    "fan": ("FAN",),
    "solenoid": ("SOLENOID",),
    "valve": ("VALVE",),
    "pump": ("PUMP",),
    "relay": ("RELAY", "RLY"),
    "speaker": ("SPEAK", "SPK"),
    "buzzer": ("BUZZ", "BZR", "BUZZER"),
    "lamp": ("LAMP", "BULB"),
}

# Flattened keyword set for net classification (output_drive class).
# Includes LED/PWM which aren't load types but are output drive signals.
_OUTPUT_DRIVE_KEYWORDS: tuple[str, ...] = (
    "LED", "PWM",
    *{kw for kws in _LOAD_TYPE_KEYWORDS.values() for kw in kws},
)


def lookup_regulator_vref(value: str, lib_id: str) -> tuple[float | None, str]:
    """Look up a regulator's internal Vref from its value or lib_id.

    Returns (vref, source) where source is "lookup" if found, or (None, "")
    if not.  Tries the value field first (usually the part number), then the
    lib_id part name after the colon.
    """
    candidates = [value.upper()]
    if ":" in lib_id:
        candidates.append(lib_id.split(":")[-1].upper())
    # LM78xx/LM79xx fixed-output convention: voltage digits embedded without
    # separator. LM7805=5V, LM78L12=12V, LM78M05CT=5V, LM7805_TO220=5V.
    # These families ONLY exist as fixed-output — no adjustable variant.
    for candidate in candidates:
        m = re.match(r'LM7[89][A-Z]?(\d{2})', candidate)
        if m:
            v = int(m.group(1))
            if v in (5, 6, 8, 9, 10, 12, 15, 18, 24):
                return float(v), "fixed_suffix"
    # Check for fixed-output voltage suffix (e.g., LM2596S-12, AMS1117-3.3,
    # TLV1117LV-33, RT9013-18GV — patterns: -3.3, -33, -3V3, -1V8, -12)
    for candidate in candidates:
        m = re.search(r'[-_](\d+)V(\d+)', candidate)
        if m:
            return float(f"{m.group(1)}.{m.group(2)}"), "fixed_suffix"
        m = re.search(r'[-_](\d+\.\d+)(?:V)?(?=[^0-9]|$)', candidate)
        if m:
            fixed_v = float(m.group(1))
            if 0.5 <= fixed_v <= 60:
                return fixed_v, "fixed_suffix"
        m = re.search(r'[-_](\d{2})(?=[^0-9.]|$)', candidate)
        if m:
            # Two-digit suffix: could be implicit decimal (33→3.3V) or
            # integer voltage (12→12V, 15→15V). Check integer first for
            # common high-voltage rails.
            digits = m.group(1)
            int_v = int(digits)
            if int_v in (10, 12, 15, 24, 48):
                return float(int_v), "fixed_suffix"
            fixed_v = float(digits[0] + "." + digits[1])
            if 0.5 <= fixed_v <= 9.9:
                return fixed_v, "fixed_suffix"
    # Longest-prefix-match: collect all matching prefixes, pick the longest
    for candidate in candidates:
        best_prefix = ""
        best_vref = None
        for prefix, vref in _REGULATOR_VREF.items():
            if candidate.startswith(prefix.upper()) and len(prefix) > len(best_prefix):
                best_prefix = prefix
                best_vref = vref
        if best_vref is not None:
            return best_vref, "lookup"
    return None, ""


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


def format_frequency(hz: float) -> str:
    """Format a frequency in Hz to a human-readable string with SI prefix."""
    if hz >= 1e9:
        return f"{hz / 1e9:.2f} GHz"
    elif hz >= 1e6:
        return f"{hz / 1e6:.2f} MHz"
    elif hz >= 1e3:
        return f"{hz / 1e3:.2f} kHz"
    else:
        return f"{hz:.2f} Hz"


def parse_value(value_str: str, component_type: str | None = None) -> float | None:
    """Parse an engineering-notation component value to a float.

    Handles: 10K, 4.7u, 100n, 220p, 1M, 2.2m, 47R, 0R1, 4K7, 1R0, etc.
    Returns None if unparseable.

    If component_type is "capacitor" and the result is a bare integer >=1.0
    (no unit suffix), treat it as picofarads (KH-153: legacy KiCad 5 convention).
    """
    # EQ-068: SI prefix: p=1e-12 n=1e-9 u=1e-6 m=1e-3 k=1e3 M=1e6
    if not value_str:
        return None

    # Strip tolerance, voltage rating, package, and other suffixes
    # Common formats: "680K 1%", "220k/R0402", "22uF/6.3V/20%/X5R/C0603"
    # KiCad 9 uses space-separated units: "18 pF", "4.7 uF" — rejoin if
    # the second token starts with an SI prefix letter.
    parts = value_str.strip().split("/")[0].split()
    if len(parts) >= 2 and parts[1] and parts[1][0] in "pnuµmkKMGRr":
        s = parts[0] + parts[1]
    else:
        s = parts[0] if parts else ""
    # KH-112: Ferrite bead impedance notation (600R/200mA, 120R@100MHz)
    # is not a parseable component value — return None to avoid nonsensical results
    if re.search(r'\d+[Rr]\s*[/@]\s*\d', s):
        return None

    # Strip trailing unit words (mOhm, Ohm, ohm, ohms) before single-char stripping
    s = re.sub(r'[Oo]hms?$', '', s)
    s = s.rstrip("FHΩVfhv%")         # strip trailing unit letters

    if not s:
        return None

    # Multiplier map (SI prefixes used in EE)
    multipliers = {
        "p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "m": 1e-3,
        "k": 1e3, "K": 1e3, "M": 1e6, "G": 1e9,
        "R": 1, "r": 1,  # "R" as decimal point: 4R7 = 4.7, 0R1 = 0.1
    }

    # Handle prefix-first European notation: "u1" -> 0.1e-6, "p47" -> 0.47e-12
    # The letter replaces the decimal point; when it comes first, implied leading 0.
    if len(s) >= 2 and s[0] in multipliers and s[1:].isdigit():
        mult = multipliers[s[0]]
        try:
            return float(f"0.{s[1:]}") * mult
        except ValueError:
            pass

    # Handle embedded multiplier: "4K7" -> 4.7e3, "0R1" -> 0.1, "1R0" -> 1.0
    for suffix, mult in multipliers.items():
        if suffix in s and not s.endswith(suffix):
            idx = s.index(suffix)
            before = s[:idx]
            after = s[idx + 1:]
            if before.replace(".", "").isdigit() and after.isdigit():
                try:
                    return float(f"{before}.{after}") * mult
                except ValueError:
                    pass

    # Handle trailing multiplier: "10K", "100n", "4.7u"
    if s[-1] in multipliers:
        mult = multipliers[s[-1]]
        try:
            return float(s[:-1]) * mult
        except ValueError:
            return None

    # Plain number: "100", "47", "0.1"
    try:
        result = float(s)
        if component_type == "capacitor":
            # KH-153: Bare integers >= 1 are picofarads in legacy schematics.
            # KH-212: Bare decimals < 1 (0.1, 0.47, 0.22) are microfarads —
            # no real-world cap is 0.1 Farads in SMD packages.
            if result >= 1.0:
                result *= 1e-12
            else:
                result *= 1e-6
        return result
    except ValueError:
        return None


def parse_tolerance(value_str: str) -> float | None:
    """Extract tolerance percentage from a component value string.

    Returns tolerance as a fraction (0.01 for 1%, 0.05 for 5%, etc.),
    or None if no tolerance is found in the string.

    Examples:
        "680K 1%"                            -> 0.01
        "22uF/6.3V/20%/X5R"                 -> 0.20
        "10K 5%"                             -> 0.05
        "0.1uF/25V(10%)"                    -> 0.10
        ".1uF/X7R/+-10%"                    -> 0.10
        "0.02±1%"                            -> 0.01
        "02.0001_R0402_0R_1%"               -> 0.01
        "033uF_0603_Ceramic_Capacitor,_10%"  -> 0.10
        "100nF"                              -> None
    """
    if not value_str:
        return None
    # Split on all common delimiters: / space _ , ± - | and break on ( boundaries
    tokens = re.split(r'[/\s_,±|\-]+', value_str)
    for token in tokens:
        # Strip parentheses and +- prefixes
        cleaned = token.strip('()+-')
        m = re.match(r'^(\d*\.?\d+)\s*%$', cleaned)
        if m:
            return float(m.group(1)) / 100.0
        # Also try extracting from within parentheses: "25V(10%)" -> "10%"
        inner = re.search(r'\((\d*\.?\d+)\s*%\)', token)
        if inner:
            return float(inner.group(1)) / 100.0
    # Fallback: search entire string for number followed by %
    # Catches "20 %" (space-separated) and "5%T52" (no delimiter after %)
    m = re.search(r'(\d*\.?\d+)\s*%', value_str)
    if m:
        val = float(m.group(1)) / 100.0
        if 0.001 <= val <= 0.5:
            return val
    return None


# ---------------------------------------------------------------------------
# E-series standard component values (IEC 60063)
# ---------------------------------------------------------------------------

E12_DECADE = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]

E24_DECADE = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
              3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]

E96_DECADE = [1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18, 1.21, 1.24,
              1.27, 1.30, 1.33, 1.37, 1.40, 1.43, 1.47, 1.50, 1.54, 1.58,
              1.62, 1.65, 1.69, 1.74, 1.78, 1.82, 1.87, 1.91, 1.96, 2.00,
              2.05, 2.10, 2.15, 2.21, 2.26, 2.32, 2.37, 2.43, 2.49, 2.55,
              2.61, 2.67, 2.74, 2.80, 2.87, 2.94, 3.01, 3.09, 3.16, 3.24,
              3.32, 3.40, 3.48, 3.57, 3.65, 3.74, 3.83, 3.92, 4.02, 4.12,
              4.22, 4.32, 4.42, 4.53, 4.64, 4.75, 4.87, 4.99, 5.11, 5.23,
              5.36, 5.49, 5.62, 5.76, 5.90, 6.04, 6.19, 6.34, 6.49, 6.65,
              6.81, 6.98, 7.15, 7.32, 7.50, 7.68, 7.87, 8.06, 8.25, 8.45,
              8.66, 8.87, 9.09, 9.31, 9.53, 9.76]

_E_SERIES = {"E12": E12_DECADE, "E24": E24_DECADE, "E96": E96_DECADE}


def snap_to_e_series(value: float, series: str = "E96") -> tuple:
    """Snap a value to the nearest standard E-series value.

    Returns (snapped_value, error_pct) where error_pct = (snapped - value) / value * 100.
    Works across any decade (mOhm to MOhm, pF to uF, etc.).
    """
    if value <= 0:
        return (0.0, 0.0)
    # EQ-107: Log-decade snapping — normalize v into [1, 10) via
    #   10^⌊log₁₀(v)⌋, find nearest neighbour in the canonical decade
    #   table, scale back by decade.
    # Source: Self-evident — standard E-series (IEC 60063) value selection.
    #   IEC 60063 defines the E6/E12/E24/E48/E96/E192 tables as
    #   tolerance-based geometric progressions; snapping is nearest-neighbour
    #   on the log scale.
    decade = 10 ** math.floor(math.log10(value))
    normalized = value / decade
    decade_list = _E_SERIES.get(series, E96_DECADE)
    best = min(decade_list, key=lambda e: abs(e - normalized))
    snapped = best * decade
    error_pct = (snapped - value) / value * 100 if value != 0 else 0.0
    return (snapped, round(error_pct, 2))


def classify_component(ref: str, lib_id: str, value: str, is_power: bool = False,
                       footprint: str = "", in_bom: bool = False,
                       description: str = "") -> str:
    """Classify component type from reference designator and library."""
    # Power symbols: trust the lib_symbol (power) flag unconditionally.
    # KH-080: Components in the power: library WITHOUT the (power) flag
    # (e.g., DD4012SA buck converter) are real parts, not power symbols —
    # only treat them as power symbols if they're not in BOM.
    if is_power:
        return "power_symbol"
    if lib_id.startswith("power:") and not in_bom:
        return "power_symbol"
    # Fallback: #PWR references are always power symbols even if the
    # (power) flag is missing from lib_symbols (can happen after KiCad
    # version upgrades that reorganize the symbol library structure).
    # KiCad uses #PWR for all power symbols including GND, VCC, +3V3, etc.
    if ref.startswith("#PWR"):
        return "power_symbol"

    prefix = ""
    for c in ref:
        if c.isalpha() or c == "#":
            prefix += c
        else:
            break

    type_map = {
        # Passive components
        "R": "resistor", "RS": "resistor", "RN": "resistor_network",
        "RM": "resistor_network", "RA": "resistor_network",
        "C": "capacitor", "VC": "capacitor", "L": "inductor",
        "D": "diode", "TVS": "diode", "CR": "diode", "V": "varistor",
        # Semiconductors
        "Q": "transistor", "FET": "transistor",
        "U": "ic", "IC": "ic",
        # Connectors and mechanical
        "J": "connector", "P": "connector",
        "SW": "switch", "S": "switch", "BUT": "switch", "BTN": "switch", "BUTTON": "switch",
        "K": "relay",
        "F": "fuse", "FUSE": "fuse",
        "Y": "crystal",
        # Connector prefixes that conflict with single-char fallback (LAN→L→inductor)
        "LAN": "connector", "CON": "connector", "USB": "connector",
        "HDMI": "connector", "RJ": "connector", "ANT": "connector",
        "BT": "battery",
        "BZ": "buzzer", "LS": "speaker", "SP": "speaker",
        "OK": "optocoupler", "OC": "optocoupler",
        "NTC": "thermistor", "TH": "thermistor", "RT": "thermistor",
        "PTC": "thermistor",
        "VAR": "varistor", "RV": "varistor",
        "SAR": "surge_arrester",
        "NT": "net_tie",
        "MOV": "varistor",
        "A": "ic",
        "TP": "test_point",
        "MH": "mounting_hole", "H": "mounting_hole",
        "FB": "ferrite_bead", "FL": "filter",
        "LED": "led",
        "T": "transformer", "TR": "transformer",
        # Mechanical/manufacturing
        "FID": "fiducial",
        "MK": "fiducial",
        "JP": "jumper", "SJ": "jumper",
        "LOGO": "graphic",
        "MP": "mounting_hole",
        "#PWR": "power_flag", "#FLG": "flag",
    }

    # --- Full prefix match: high confidence ---
    result = type_map.get(prefix)
    if result:
        val_low = value.lower() if value else ""
        lib_low = lib_id.lower() if lib_id else ""
        fp_low = footprint.lower() if footprint else ""
        if any(x in val_low or x in lib_low or x in fp_low
               for x in ("testpad", "test_pad", "testpoint", "test_point")):
            return "test_point"
        # KH-208: Unambiguous lib_id patterns override ref prefix.
        _lib_prefix = lib_low.split(":")[0] if ":" in lib_low else ""
        _lib_type_overrides = {
            "connector": "connector", "connector_audio": "connector",
            "connector_generic": "connector", "connector_generic_shielded": "connector",
            "sensor_temperature": "ic", "sensor": "ic",
            "motor": "motor",
        }
        _override = _lib_type_overrides.get(_lib_prefix)
        if _override:
            return _override
        if "circuitbreaker" in lib_low or "circuit_breaker" in lib_low:
            return "switch"
        # Crystal/oscillator override: Q-prefix crystals (Q for quartz),
        # CR-prefix oscillators, or any prefix where lib_id clearly says crystal/oscillator
        if result not in ("crystal", "oscillator"):
            has_xtal = any(x in lib_low for x in ("crystal", "xtal"))
            has_osc = "oscillator" in lib_low
            if has_xtal:
                return "crystal"
            if has_osc:
                return "oscillator"
        # KH-220: Description-based oscillator detection for custom lib symbols
        if result not in ("crystal", "oscillator"):
            _desc_low = description.lower() if description else ""
            if any(x in _desc_low for x in ("oscillator", "clock oscillator",
                                              "mems oscillator", "tcxo", "vcxo", "ocxo")):
                if "crystal" not in _desc_low:
                    return "oscillator"
        if result == "varistor":
            if ("r_pot" in lib_low or "pot" in lib_low or "potentiometer" in lib_low
                    or "potentiometer" in val_low):
                return "resistor"
            if ("regulator" in lib_low or "regulator" in fp_low
                    or any(x in val_low for x in ("ams1117", "lm78", "lm317",
                                                   "ld1117", "lm1117", "ap1117"))):
                return "ic"
        if result == "transformer":
            # KH-111: Common-mode chokes — classify as inductor, not transformer
            if any(x in val_low for x in ("cmc", "common mode", "common_mode",
                                           "rfcmf", "acm", "dlw")):
                return "inductor"
            if any(x in lib_low for x in ("common_mode", "cmc", "emi_filter")):
                return "inductor"
            if any(x in lib_low or x in val_low or x in fp_low
                   for x in ("mosfet", "fet", "transistor", "bjt",
                             "q_npn", "q_pnp", "q_nmos", "q_pmos")):
                return "transistor"
            if any(x in lib_low or x in val_low
                   for x in ("amplifier", "rf_amp", "mmic")):
                return "ic"
        if result == "thermistor" and any(x in lib_low or x in val_low
                                          for x in ("fuse", "polyfuse", "pptc",
                                                    "reset fuse", "ptc fuse")):
            return "fuse"
        if result == "thermistor" and any(x in lib_low or x in val_low
                                          for x in ("mov", "varistor")):
            return "varistor"
        if result == "diode" and re.search(r'(?<![a-z])led(?![a-z])', lib_low + " " + val_low):
            return "led"
        # KH-122: Addressable LEDs (SK6812, WS2812) with D prefix
        if result == "diode" and any(k in val_low or k in lib_low
                                     for k in ("ws2812", "ws2813", "ws2815",
                                               "sk6812", "apa102", "apa104",
                                               "sk9822", "ws2811", "neopixel")):
            return "led"
        if result == "inductor":
            if any(x in lib_low or x in val_low for x in ("ferrite", "bead")):
                return "ferrite_bead"
            # KH-112: Ferrite bead impedance notation (600R/200mA, 120R@100MHz)
            if re.search(r'\d+[Rr]\s*[/@]\s*\d', value):
                return "ferrite_bead"
        # KH-106: MX/Cherry/Kailh keyboard switches (K prefix maps to relay)
        if result == "relay":
            if any(x in lib_low for x in ("mx", "cherry", "kailh", "gateron",
                                           "alps_hybrid", "key_switch")):
                return "switch"
            if any(x in val_low for x in ("mx-", "cherry", "kailh", "gateron")):
                return "switch"
        return result

    # --- No full-prefix match.  Try lib_id / value before single-char fallback ---
    # This ordering ensures that DA1 with lib=Analog_DAC gets "ic" (not D→diode),
    # and PS1 with lib=Regulator_Linear gets "ic" (not P→connector).
    val_lower = value.lower() if value else ""
    lib_lower = lib_id.lower() if lib_id else ""

    if any(x in val_lower for x in ["mountinghole", "mounting_hole"]):
        return "mounting_hole"
    if any(x in val_lower for x in ["fiducial"]):
        return "fiducial"
    if any(x in val_lower for x in ["testpad", "test_pad"]):
        return "test_point"
    if any(x in lib_lower for x in ["mounting_hole", "mountinghole"]):
        return "mounting_hole"
    if any(x in lib_lower for x in ["fiducial"]):
        return "fiducial"
    if any(x in lib_lower for x in ["test_point", "testpoint", "testpad", "test_pad"]):
        return "test_point"

    # X prefix: crystal or oscillator if value/lib suggests it, otherwise connector
    # Distinguish passive crystals (need load caps) from active MEMS/IC oscillators
    if prefix == "X":
        desc_lower = description.lower() if description else ""
        # Active oscillator ICs (MEMS, TCXO, VCXO) — have VCC/GND/OUT, no load caps
        if any(x in lib_lower for x in ["oscillator"]) and not any(x in lib_lower for x in ["crystal", "xtal"]):
            return "oscillator"
        # KH-220: Custom lib symbols with oscillator in description
        if any(x in desc_lower for x in ("oscillator", "xo ", "xtal osc",
                                          "clock osc", "mems osc")):
            if "crystal" not in desc_lower:
                return "oscillator"
        if any(x in val_lower for x in ["dsc6", "si5", "sg-", "asfl", "sit8", "asco"]):
            return "oscillator"
        # Passive crystals
        # Also catch compact frequency notation like "8M", "12M", "32.768K"
        if any(x in val_lower for x in ["xtal", "crystal", "mhz", "khz", "osc"]):
            return "crystal"
        if re.match(r'^\d+\.?\d*[mkMK]$', value):
            return "crystal"
        if any(x in lib_lower for x in ["crystal", "xtal", "osc", "clock"]):
            return "crystal"
        return "connector"

    # MX key switches (keyboard projects)
    if prefix == "MX" or "cherry" in val_lower or "kailh" in val_lower:
        return "switch"

    # Common prefixes that are context-dependent
    if prefix in ("RST", "RESET", "PHYRST"):
        return "switch"  # reset buttons/circuits
    if prefix == "BAT" or prefix == "BATSENSE":
        return "connector"  # battery connector
    if prefix == "RGB" or prefix == "PWRLED":
        return "led"

    # Library-based fallback for non-standard reference prefixes
    if "circuitbreaker" in lib_lower or "circuit_breaker" in lib_lower:
        return "switch"
    if "thermistor" in lib_lower or "thermistor" in val_lower or "ntc" in val_lower:
        return "thermistor"
    if "varistor" in lib_lower or "varistor" in val_lower:
        return "varistor"
    if "optocoupler" in lib_lower or "opto" in lib_lower:
        return "optocoupler"
    lib_prefix = lib_lower.split(":")[0] if ":" in lib_lower else lib_lower
    if lib_prefix == "led" or val_lower.startswith("led/") or val_lower == "led":
        return "led"
    if "ws2812" in val_lower or "neopixel" in val_lower or "sk6812" in val_lower:
        return "led"
    if "jumper" in lib_lower or val_lower in ("opened", "closed") or val_lower.startswith("opened("):
        return "jumper"
    # Connector detection: lib names and common connector part number patterns
    if "connector" in lib_lower or "conn_" in val_lower:
        return "connector"
    # KH-110: Audio jack connectors
    if "connector_audio" in lib_lower or "audio_jack" in lib_lower:
        return "connector"
    if any(value.startswith(p) for p in ("PJ-3", "SJ-3", "MJ-3")):
        return "connector"
    if any(x in val_lower for x in ["usb_micro", "usb_c", "usb-c", "rj45", "rj11",
                                     "pin_header", "pin_socket", "barrel_jack"]):
        return "connector"
    # JST and similar connector part numbers in value
    if any(value.startswith(p) for p in ["S3B-", "S4B-", "S6B-", "S8B-", "SM0",
                                        "B2B-", "BM0", "MISB-", "ZL2", "ZL3",
                                        "HN1x", "NH1x", "NS(HN", "NS(NH",
                                        "FL40", "FL20", "FPV-", "SCJ3",
                                        "TFC-", "68020-", "RJP-", "RJ45"]):
        return "connector"
    # Common non-standard connector prefixes (OLIMEX, etc.)
    if prefix in ("CON", "USB", "USBUART", "MICROSD", "UEXT", "LAN",
                   "HDMI", "EXT", "GPIO", "CAN", "SWD", "JTAG",
                   "ANT", "RJ", "SUPPLY"):
        return "connector"
    # KH-106: Catch MX/Cherry/Kailh keyboard switches before relay detection
    if "switch" in lib_lower or "button" in lib_lower:
        return "switch"
    if any(x in lib_lower for x in ("cherry_mx", "mx_switch", "kailh", "gateron")):
        return "switch"
    if any(x in val_lower for x in ("button", "tact", "push", "t1102", "t1107", "yts-a",
                                     "cherry_mx", "mx_switch", "kailh", "gateron")):
        return "switch"
    if "relay" in lib_lower:
        return "relay"
    if "nettie" in lib_lower or "net_tie" in val_lower or "nettie" in val_lower:
        return "net_tie"
    if "led" in lib_lower and "diode" in lib_lower:
        return "led"
    # IC detection from KiCad stdlib library prefixes (Analog_ADC, MCU_*, Regulator_*, etc.)
    _ic_lib_prefixes = ("analog_", "audio", "battery_management",
                        "comparator", "converter_",
                        "driver_", "display_", "fpga_", "interface_",
                        "logic_", "mcu_", "memory_", "motor_",
                        "multiplexer", "power_management", "power_supervisor",
                        "regulator_", "sensor_", "timer", "rf_")
    if any(lib_prefix.startswith(p) for p in _ic_lib_prefixes):
        return "ic"
    if "transistor" in lib_lower or "mosfet" in lib_lower:
        return "transistor"
    if "diode" in lib_lower:
        return "diode"
    if "fuse" in lib_lower or "polyfuse" in lib_lower:
        return "fuse"
    if "ferritebead" in lib_lower or "ferrite_bead" in lib_lower:
        return "ferrite_bead"
    if "inductor" in lib_lower or "choke" in lib_lower:
        return "inductor"
    if "capacitor" in lib_lower:
        return "capacitor"
    if "resistor" in lib_lower:
        return "resistor"

    # --- Last resort: single-char prefix fallback ---
    # Only reached when lib_id/value didn't resolve the type.
    # Deliberately placed last so lib_id always takes priority.
    # KH-079: After single-char match, check lib_id/footprint/value for
    # contradicting evidence that overrides the single-char classification.
    if len(prefix) > 1:
        result = type_map.get(prefix[0])
        if result:
            fp_lower = footprint.lower() if footprint else ""
            if result == "transformer":
                if "tvs" in lib_lower or "tvs" in val_lower:
                    return "diode"
                if "test" in lib_lower or "tp" in fp_lower:
                    return "test_point"
                if any(x in lib_lower or x in val_lower or x in fp_lower
                       for x in ("mosfet", "fet", "transistor", "bjt",
                                 "q_npn", "q_pnp", "q_nmos", "q_pmos")):
                    return "transistor"
            if result == "fuse":
                if "fiducial" in lib_lower:
                    return "fiducial"
                if "filter" in lib_lower or "emi" in lib_lower:
                    return "filter"
                if "ferrite" in lib_lower or "bead" in lib_lower:
                    return "ferrite_bead"
            if result == "capacitor":
                if "shield" in lib_lower or "clip" in lib_lower:
                    return "mechanical"
            if result == "switch":
                if "standoff" in lib_lower or "smtso" in val_lower:
                    return "mounting_hole"
            if result == "varistor":
                if ("regulator" in lib_lower or "regulator" in fp_lower
                        or any(x in val_lower for x in ("ams1117", "lm78", "lm317",
                                                         "ld1117", "lm1117", "ap1117"))):
                    return "ic"
                if "pot" in lib_lower or "potentiometer" in lib_lower:
                    return "resistor"
            if result == "ic":
                if "bjt" in lib_lower or "transistor" in lib_lower:
                    return "transistor"
                if "transformer" in lib_lower:
                    return "transformer"
            return result

    return "other"


def classify_ic_function(lib_id: str, value: str, description: str = "") -> str:
    """Classify an IC's functional role from its lib_id, value, and description.

    Returns one of: mcu, fpga, memory, communication, sensor, power_management,
    audio, display, motor_driver, adc, dac, clock, protection, interface, other_ic.
    """
    combined = (lib_id + " " + value + " " + description).lower()

    # Order matters: more specific matches first to avoid false positives.
    # MCU / microcontroller
    if any(k in combined for k in ("stm32", "esp32", "esp8266", "rp2040", "rp2350",
                                    "atmega", "attiny", "atsamd", "atsam", "pic16",
                                    "pic18", "pic32", "nrf5", "nrf9", "msp430",
                                    "cy8c", "efm32", "gd32", "ch32", "ch552",
                                    "microcontroller", "mcu_")):
        return "mcu"

    # FPGA / CPLD
    if any(k in combined for k in ("fpga", "cpld", "ice40", "ecp5", "spartan",
                                    "artix", "kintex", "zynq", "cyclone", "max10",
                                    "gowin", "lattice", "altera", "xilinx")):
        return "fpga"

    # Memory
    if any(k in combined for k in ("flash", "eeprom", "sram", "dram", "sdram",
                                    "w25q", "at24c", "25lc", "is62", "is66",
                                    "mt48", "as4c", "ly68", "memory_")):
        return "memory"

    # ADC (before sensor — some ADC ICs have "sensor" in description)
    if any(k in combined for k in ("analog_adc", "adc_", "_adc", "ads1", "mcp320",
                                    "mcp330", "max11", "ltc24")):
        return "adc"

    # DAC
    if any(k in combined for k in ("analog_dac", "dac_", "_dac", "mcp47", "mcp48",
                                    "dac81", "dac71")):
        return "dac"

    # Audio
    if any(k in combined for k in ("audio", "codec", "i2s", "pcm51", "pcm17",
                                    "wm8", "max98", "tas2", "tas5", "ssm2",
                                    "cs42", "cs43", "sgtl5", "tlv320")):
        return "audio"

    # Display driver
    if any(k in combined for k in ("display", "lcd_driver", "oled_driver", "ssd1306",
                                    "st7735", "st7789", "ili9", "hx8357",
                                    "max7219", "ht16k33")):
        return "display"

    # Motor driver
    if any(k in combined for k in ("motor_driver", "motor driver", "drv8", "a4988",
                                    "tmc2", "l298", "l293", "tb6612", "uln2003")):
        return "motor_driver"

    # Clock / oscillator / PLL
    if any(k in combined for k in ("clock", "pll", "si5351", "cdce", "lmk0",
                                    "ics5", "clock_generator", "clock_buffer",
                                    "timer_", "si544", "ds1085")):
        return "clock"

    # Sensor
    if any(k in combined for k in ("sensor", "accel", "gyro", "imu", "magneto",
                                    "bme2", "bme6", "bmp2", "bmp3", "bmp5",
                                    "sht3", "sht4", "hdc1", "tmp1", "lm75",
                                    "mpu6", "icm20", "lis3", "lsm6", "ina2",
                                    "ina3", "max31", "thermocouple", "rtd")):
        return "sensor"

    # Protection (ESD, TVS array, overvoltage, overcurrent)
    if any(k in combined for k in ("esd_protection", "tvs_array", "usblc",
                                    "tpd4e", "prtr5v", "sp0505", "pesd",
                                    "ip4220", "sn65220", "protection")):
        return "protection"

    # Communication (after MCU to avoid false positives on MCU descriptions)
    if any(k in combined for k in ("uart", "ethernet", "wifi", "bluetooth", "lora",
                                    "can_", "spi_", "i2c_", "rs232", "rs485",
                                    "rs-232", "rs-485", "phy_", "transceiver",
                                    "modem", "usb_hub", "usb_", "zigbee",
                                    "interface_uart", "interface_can",
                                    "ch340", "cp210", "ft232", "max232",
                                    "max485", "max3232", "sn65hvd")):
        return "communication"

    # Power management (regulators, PMICs, battery chargers, supervisors)
    if any(k in combined for k in ("regulator", "ldo", "buck", "boost", "pmic",
                                    "battery_management", "charger", "power_management",
                                    "power_supervisor", "supervisor", "voltage_reference",
                                    "ams1117", "lm317", "tps5", "tps6", "tps7",
                                    "mp1584", "mp2359", "lt308", "ltc36",
                                    "mcp1640", "mcp1603")):
        return "power_management"

    # Interface (level shifters, buffers, muxes, I/O expanders)
    if any(k in combined for k in ("interface_", "level_shift", "buffer", "mux",
                                    "multiplexer", "demux", "io_expander",
                                    "logic_level", "74hc", "74lvc", "74ahc",
                                    "txb0", "txs0", "pca953", "pca955",
                                    "mcp23", "pcf857", "tca6")):
        return "interface"

    return "other_ic"


def classify_connector(lib_id: str, value: str, pin_count: int = 0) -> tuple[bool, str]:
    """Classify a connector's external status and layout type.

    Returns (is_external, layout) where:
    - is_external: True if connector faces an external cable/user
    - layout: one of usb_c, barrel, rj45, rj11, screw_terminal, dual, single, other
    """
    combined = (lib_id + " " + value).lower()

    # Layout detection — order matters, most specific first
    if any(k in combined for k in ("usb_c", "usb-c", "type-c", "typec")):
        layout = "usb_c"
    elif any(k in combined for k in ("barrel_jack", "barrel jack", "dc_jack",
                                      "dc jack", "pj-", "pwrj")):
        layout = "barrel"
    elif "rj45" in combined or "8p8c" in combined:
        layout = "rj45"
    elif "rj11" in combined or "rj12" in combined or "6p6c" in combined or "4p4c" in combined:
        layout = "rj11"
    elif any(k in combined for k in ("screw_terminal", "screw terminal", "phoenix",
                                      "pluggable_terminal", "terminal_block")):
        layout = "screw_terminal"
    elif re.search(r'(?:conn_\d+x\d+|_2x\d+|\d+x2_)', combined) or \
         re.search(r'pin_header.*2x\d+|pin_socket.*2x\d+', combined):
        layout = "dual"
    elif re.search(r'(?:conn_01x\d+|conn_1x\d+|_1x\d+|\d+x1_)', combined) or \
         re.search(r'pin_header.*1x\d+|pin_socket.*1x\d+', combined):
        layout = "single"
    else:
        layout = "other"

    # External classification
    # Explicitly external connectors
    if any(k in combined for k in ("usb", "rj45", "rj11", "rj12", "barrel", "dc_jack",
                                    "hdmi", "displayport", "dvi", "vga",
                                    "audio_jack", "headphone", "line_in", "line_out",
                                    "sma", "sma_", "bnc", "f_conn", "n_conn",
                                    "db9", "db25", "dsub", "d-sub",
                                    "sd_card", "micro_sd", "sim_card")):
        is_external = True
    elif any(k in combined for k in ("screw_terminal", "screw terminal", "phoenix",
                                      "terminal_block", "pluggable_terminal",
                                      "molex", "jst", "jst_", "s3b-", "s4b-",
                                      "wire_to_board", "wire-to-board")):
        is_external = True
    elif any(k in combined for k in ("test", "debug", "tp_", "testpoint", "test_point",
                                      "tag_connect", "tag-connect", "cortex_debug",
                                      "swd", "jtag", "isp", "icsp")):
        is_external = False
    elif any(k in combined for k in ("pin_header", "pin_socket", "conn_01x", "conn_02x",
                                      "conn_1x", "conn_2x")):
        # Generic headers: small headers (<=6 pins) are typically internal
        is_external = pin_count > 6
    else:
        is_external = False

    return is_external, layout


def classify_jumper_default_state(value: str, lib_id: str = "",
                                  footprint: str = "") -> str:
    """Classify a jumper's default conduction state from its symbol/footprint.

    KiCad ships distinct symbol and footprint variants for solder jumpers,
    and whether a jumper starts closed or open is a design-intent fact the
    layout encodes — not something an analyzer should guess from the ref.

    Returns one of:
      'bridged'     — closed/conducting by default (e.g.
                      Jumper:SolderJumper_2_Bridged,
                      footprint ending *_Bridged*). The user has to score/
                      cut the bridge to break the connection.
      'open'        — open/non-conducting by default (e.g.
                      Jumper:Jumper_2_Open, footprint ending *_Open*). The
                      user has to solder the pads to close it.
      'switchable'  — a physical jumper (shunt/header) whose state is set
                      by a removable part (Conn_01x02, Jumper_3_Bridged12,
                      etc.). Treat as 'unknown' for conduction purposes —
                      the schematic can't tell you.
      'unknown'     — any other jumper-like component we can't classify.
    """
    val = (value or "").lower()
    lib = (lib_id or "").lower()
    fp = (footprint or "").lower()

    # Footprint wins when present — it's the physical reality.
    if "_bridged" in fp:
        # Mixed 3-pin cases like Bridged12 / Bridged23 are "partial" — treat
        # as bridged because at least some pins are connected.
        return "bridged"
    if "_open" in fp:
        return "open"

    # Symbol/value fallbacks when the footprint is absent or non-specific.
    if "bridged" in val or "bridged" in lib or val == "closed":
        return "bridged"
    if val in ("open", "opened") or val.startswith("opened(") or \
       "jumper_2_open" in lib or "_open" in lib.split(":", 1)[-1]:
        return "open"

    # A shorting block across a pin header is user-configurable.
    if "conn_01x" in lib or "pinheader" in lib.replace("_", ""):
        return "switchable"

    if "jumper" in lib or "jumper" in val:
        return "unknown"

    return "unknown"


# KH-343: USB data lines (D+/D-) must not inherit the 5V VBUS fallback —
# they're signal nets, not rails.
USB_DATA_NET_MARKERS = ("USB_D", "USBDP", "USBDM", "USBDN", "DPLUS", "DMINUS")


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


def get_two_pin_nets(pin_net: dict, ref: str) -> tuple[str | None, str | None]:
    """Get the two nets a 2-pin component connects to.

    Takes pin_net map explicitly instead of closing over it.
    Falls back to enumerating all pins when "1"/"2" aren't found.
    """
    n1, _ = pin_net.get((ref, "1"), (None, None))
    n2, _ = pin_net.get((ref, "2"), (None, None))
    if n1 is not None and n2 is not None:
        return n1, n2
    # Fallback for non-"1"/"2" pin numbering (Eagle imports, diodes A/K, etc.)
    ref_entries = {k[1]: v for k, v in pin_net.items() if k[0] == ref}
    if len(ref_entries) == 2:
        nets = [net for net, _ in ref_entries.values()]
        return nets[0], nets[1]
    return n1, n2


# ---------------------------------------------------------------------------
# Capacitor package extraction and ESR/ESL estimation
# ---------------------------------------------------------------------------

# Regex to extract package size from KiCad footprint strings
# Matches: C_0402_1005Metric, C_0805_2012Metric, CP_EIA-3216-18_Kemet-A, etc.
_CAP_PKG_RE = re.compile(r'C[P]?_(\d{4})_')
_CAP_PKG_EIA_RE = re.compile(r'EIA-(\d{4})')

# Typical MLCC ESR by package and capacitance range (X7R/X5R, 1kHz reference)
# Source: aggregate datasheet data from Murata, Samsung, TDK
# Format: (package, max_farads) → esr_ohm
# Checked in order — first match where farads <= max_farads wins
_CAP_ESR_TABLE = [
    # 0402 (1005 metric)
    ("0402", 1e-8,  5.0),    # ≤10nF
    ("0402", 1e-7,  1.0),    # ≤100nF
    ("0402", 1e-5,  0.5),    # ≤10µF
    # 0603 (1608 metric)
    ("0603", 1e-8,  2.0),
    ("0603", 1e-7,  0.5),
    ("0603", 1e-6,  0.15),
    ("0603", 1e-4,  0.1),
    # 0805 (2012 metric)
    ("0805", 1e-7,  0.3),
    ("0805", 1e-6,  0.08),
    ("0805", 1e-4,  0.03),
    # 1206 (3216 metric)
    ("1206", 1e-6,  0.1),
    ("1206", 1e-5,  0.03),
    ("1206", 1e-3,  0.01),
    # 1210 (3225 metric)
    ("1210", 1e-5,  0.02),
    ("1210", 1e-3,  0.008),
    # 2220 (5750 metric)
    ("2220", 1e-3,  0.005),
]

# Typical ESL by package (nH) — dominated by package geometry, not capacitance
_CAP_ESL = {
    "0402": 0.3,
    "0603": 0.5,
    "0805": 0.7,
    "1206": 1.0,
    "1210": 1.0,
    "1812": 1.2,
    "2220": 1.5,
}


def extract_cap_package(footprint):
    """Extract capacitor package size from KiCad footprint string.

    Examples:
        'Capacitor_SMD:C_0402_1005Metric' → '0402'
        'Capacitor_SMD:C_0805_2012Metric' → '0805'
        'Capacitor_SMD:CP_EIA-3216-18_Kemet-A' → '3216'
        'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P2.50mm' → None (THT, no standard package)
        '' → None

    Returns:
        Package designator string (e.g., '0402') or None
    """
    if not footprint:
        return None
    # Try standard "C_0402_..." pattern first
    m = _CAP_PKG_RE.search(footprint)
    if m:
        return m.group(1)
    # Try EIA pattern
    m = _CAP_PKG_EIA_RE.search(footprint)
    if m:
        # Convert EIA metric to imperial: 3216 → 1206, etc.
        eia = m.group(1)
        eia_to_imperial = {
            "1005": "0402", "1608": "0603", "2012": "0805",
            "3216": "1206", "3225": "1210", "4532": "1812",
            "5750": "2220",
        }
        return eia_to_imperial.get(eia, eia)
    return None


def estimate_cap_esr(farads, package):
    """Estimate ESR for an MLCC capacitor based on package and value.

    Very approximate — real ESR depends on manufacturer, voltage rating,
    dielectric type (X7R vs C0G), and measurement frequency. These are
    typical values at ~1kHz for X7R/X5R MLCCs.

    Args:
        farads: Capacitance in farads
        package: Package designator (e.g., '0402', '0805')

    Returns:
        Estimated ESR in ohms, or None if package not recognized
    """
    # EQ-067: ESR estimate from package size + capacitance (empirical)
    if not package or not farads or farads <= 0:
        return None
    pkg = package.upper()
    for tbl_pkg, max_f, esr in _CAP_ESR_TABLE:
        if pkg == tbl_pkg and farads <= max_f:
            return esr
    # No match — return a conservative default
    if farads < 1e-6:
        return 0.5
    elif farads < 1e-4:
        return 0.1
    else:
        return 0.05


def estimate_cap_esl(package):
    """Estimate parasitic inductance (ESL) for an MLCC.

    ESL is primarily driven by package geometry (current path length
    through the component), not by capacitance value.

    Args:
        package: Package designator (e.g., '0402', '0805')

    Returns:
        Estimated ESL in henries, or None if package not recognized
    """
    # EQ-066: ESL estimate from package size (empirical table)
    if not package:
        return None
    esl_nh = _CAP_ESL.get(package.upper())
    if esl_nh is None:
        return None
    return esl_nh * 1e-9  # Convert nH to H


# ---------------------------------------------------------------------------
# MLCC DC bias derating
# ---------------------------------------------------------------------------

# Approximate remaining capacitance fraction at given voltage ratio
# (applied_V / rated_V). Class II ceramics (X5R, X7R) lose significant
# capacitance under DC bias; smaller packages derate more aggressively.
# Source: Murata/TDK DC bias characteristic data, Analog Devices MT-101.
# Format: [(voltage_ratio, remaining_fraction), ...]  — interpolate linearly.
_DC_BIAS_DERATING = {
    'X5R_0402': [(0.0, 1.0), (0.25, 0.85), (0.5, 0.50), (0.75, 0.25), (1.0, 0.10)],
    'X5R_0603': [(0.0, 1.0), (0.25, 0.90), (0.5, 0.60), (0.75, 0.35), (1.0, 0.15)],
    'X5R_0805': [(0.0, 1.0), (0.25, 0.92), (0.5, 0.70), (0.75, 0.45), (1.0, 0.20)],
    'X5R_1206': [(0.0, 1.0), (0.25, 0.94), (0.5, 0.78), (0.75, 0.55), (1.0, 0.30)],
    'X7R_0402': [(0.0, 1.0), (0.25, 0.90), (0.5, 0.65), (0.75, 0.40), (1.0, 0.15)],
    'X7R_0603': [(0.0, 1.0), (0.25, 0.93), (0.5, 0.75), (0.75, 0.50), (1.0, 0.25)],
    'X7R_0805': [(0.0, 1.0), (0.25, 0.95), (0.5, 0.80), (0.75, 0.55), (1.0, 0.30)],
    'X7R_1206': [(0.0, 1.0), (0.25, 0.96), (0.5, 0.85), (0.75, 0.65), (1.0, 0.40)],
    'Y5V_0402': [(0.0, 1.0), (0.25, 0.60), (0.5, 0.25), (0.75, 0.10), (1.0, 0.05)],
    'Y5V_0603': [(0.0, 1.0), (0.25, 0.65), (0.5, 0.30), (0.75, 0.15), (1.0, 0.08)],
    'C0G_any':  [(0.0, 1.0), (0.5, 1.0), (1.0, 1.0)],
}


def classify_dielectric(value_str, desc_str=''):
    """Extract MLCC dielectric type from component value/description string.

    Checks for C0G/NP0, X7R/X7S/X6S, X5R/X5S, Y5V/Z5U in that order.
    Returns 'X7R' as default for unmarked MLCCs (most common general-purpose).

    Args:
        value_str: Component value string (e.g., '100nF/16V/X7R')
        desc_str: Optional description field

    Returns:
        Dielectric code string: 'C0G', 'X7R', 'X5R', or 'Y5V'
    """
    text = ((value_str or '') + ' ' + (desc_str or '')).upper()
    for d in ('C0G', 'NP0', 'COG'):
        if d in text:
            return 'C0G'
    for d in ('X7R', 'X7S', 'X6S'):
        if d in text:
            return 'X7R'
    for d in ('X5R', 'X5S'):
        if d in text:
            return 'X5R'
    for d in ('Y5V', 'Z5U', 'X7T'):
        if d in text:
            return 'Y5V'
    return 'X7R'


# ---------------------------------------------------------------------------
# Inductor shielding classification
# ---------------------------------------------------------------------------

# Known shielded inductor families by MPN prefix or footprint keyword.
# Sources: Coilcraft, Wurth, TDK, Vishay, Murata product catalogs.
_SHIELDED_PATTERNS = (
    # Coilcraft composite/metal alloy (fully shielded)
    'XAL', 'XFL', 'XGL', 'XEL', 'XPL',
    # Wurth metal alloy power inductor
    'WE-MAPI', 'WE-LHMI', 'WE-MASH',
    # TDK shielded power inductors
    'SPM', 'SLF', 'VLF', 'CLF',
    # Vishay IHLP (integrated high-current low-profile, shielded)
    'IHLP',
    # Murata shielded
    'LQM', 'DFE',
)

_SEMI_SHIELDED_PATTERNS = (
    # Coilcraft semi-shielded
    'MSS', 'MSD',
    # Bourns semi-shielded
    'SRR', 'SRN', 'SRP',
    # Wurth semi-shielded
    'WE-PD', 'WE-TPC',
    # Murata semi-shielded
    'LQH',
)

_UNSHIELDED_PATTERNS = (
    # Bourns open wire-wound
    'SDR', 'SLR',
    # Coilcraft open
    'DO', 'DT',
)


def classify_inductor_shielding(footprint_lib='', value_str='', mpn=''):
    """Classify inductor shielding type from footprint, value, or MPN.

    Checks for known manufacturer family patterns. Through-hole inductors
    are assumed unshielded. Generic SMD without recognizable family returns
    'unknown'.

    Args:
        footprint_lib: KiCad footprint library string
            (e.g., 'Inductor_SMD:L_Coilcraft_XGL4020')
        value_str: Component value string
        mpn: Manufacturer part number

    Returns:
        One of: 'shielded', 'semi-shielded', 'unshielded', 'unknown'
    """
    # Combine all available text for pattern matching.
    # Normalize hyphens to underscores — KiCad footprint libraries use
    # underscores (WE_MAPI) while manufacturer names use hyphens (WE-MAPI).
    text = ((footprint_lib or '') + ' ' + (value_str or '') + ' ' + (mpn or '')).upper().replace('-', '_')

    if not text.strip():
        return 'unknown'

    # Explicit keywords in footprint name
    if 'SHIELDED' in text and 'UNSHIELDED' not in text:
        return 'shielded'
    if 'UNSHIELDED' in text:
        return 'unshielded'

    # Check known manufacturer families (normalize hyphens in patterns too)
    for pat in _SHIELDED_PATTERNS:
        if pat.upper().replace('-', '_') in text:
            return 'shielded'
    for pat in _SEMI_SHIELDED_PATTERNS:
        if pat.upper().replace('-', '_') in text:
            return 'semi-shielded'
    for pat in _UNSHIELDED_PATTERNS:
        if pat.upper().replace('-', '_') in text:
            return 'unshielded'

    # Through-hole inductors are typically unshielded drum/toroid cores
    fp_upper = (footprint_lib or '').upper()
    if 'THT' in fp_upper or 'THROUGH' in fp_upper:
        return 'unshielded'

    return 'unknown'


# Regex for rated voltage in value strings: "100nF/16V", "10uF 6.3V", etc.
_RATED_V_RE = re.compile(r'(\d+\.?\d*)\s*V(?:DC)?(?:\b|[^a-zA-Z0-9])', re.IGNORECASE)


def parse_rated_voltage(value_str):
    """Extract rated voltage from a capacitor value string.

    Looks for patterns like '16V', '6.3V', '50 V' in the value string.
    Ignores implausible values (less than 1V or greater than 100V for standard MLCCs).

    Args:
        value_str: Component value string (e.g., '100nF/16V/X7R')

    Returns:
        Rated voltage in volts (float), or None if not found
    """
    if not value_str:
        return None
    m = _RATED_V_RE.search(value_str)
    if m:
        v = float(m.group(1))
        if 1.0 <= v <= 100:
            return v
    return None


def estimate_dc_bias_derating(dielectric, package, voltage_ratio):
    """Estimate remaining capacitance fraction under DC bias.

    Class II ceramic capacitors (X5R, X7R, Y5V) lose capacitance when
    DC bias approaches rated voltage. Smaller packages derate more.
    C0G/NP0 has negligible DC bias effect.

    Args:
        dielectric: Dielectric code ('X7R', 'X5R', 'C0G', 'Y5V')
        package: Package code ('0402', '0603', '0805', '1206')
        voltage_ratio: Applied voltage / rated voltage (0.0 to 1.0+)

    Returns:
        Remaining fraction (0.0 to 1.0). 1.0 = no derating.
    """
    if voltage_ratio <= 0:
        return 1.0
    voltage_ratio = min(voltage_ratio, 1.0)

    key = '{0}_{1}'.format(dielectric, package)
    if key not in _DC_BIAS_DERATING:
        # Try generic fallback for this dielectric (use 0603 as reference)
        key_generic = '{0}_0603'.format(dielectric)
        if key_generic in _DC_BIAS_DERATING:
            key = key_generic
        elif 'C0G' in dielectric.upper() or 'NP0' in dielectric.upper():
            return 1.0
        else:
            # Unknown dielectric — moderate default derating
            return max(0.1, 1.0 - voltage_ratio * 0.7)

    curve = _DC_BIAS_DERATING[key]
    for i in range(len(curve) - 1):
        v0, f0 = curve[i]
        v1, f1 = curve[i + 1]
        if v0 <= voltage_ratio <= v1:
            t = (voltage_ratio - v0) / (v1 - v0) if v1 > v0 else 0
            return f0 + t * (f1 - f0)
    return curve[-1][1]


# ======================================================================
# .kicad_pro project file parsing
# ======================================================================

def load_kicad_pro(file_path: str) -> dict | None:
    """Load .kicad_pro from the same directory as a .kicad_sch or .kicad_pcb file.

    Scans the directory for a ``*.kicad_pro`` file (there should be exactly one).
    Returns the parsed JSON dict, or None if not found, not valid JSON, or a
    KiCad 5 ``.pro`` file (which uses a different, non-JSON format).
    """
    import json as _json
    parent = os.path.dirname(os.path.abspath(file_path))
    try:
        entries = os.listdir(parent)
    except OSError:
        return None
    for fname in entries:
        if fname.endswith('.kicad_pro'):
            pro_path = os.path.join(parent, fname)
            try:
                with open(pro_path) as f:
                    return _json.load(f)
            except (ValueError, OSError):
                return None
    return None


def is_referenced_as_child(file_path: str) -> bool:
    """Check if a .kicad_sch is referenced as a child sheet by a sibling.

    Scans sibling .kicad_sch files in the same directory for Sheetfile
    properties containing this file's basename.  Used by detect_sub_sheet()
    to distinguish intermediate hierarchy nodes from the root (KH-304).

    Reads the full file because sheet blocks can appear after large
    lib_symbols sections (e.g. 680KB root with sheets at byte 681K).
    """
    abs_path = os.path.abspath(file_path)
    basename = os.path.basename(abs_path)
    parent_dir = os.path.dirname(abs_path)

    try:
        for fname in os.listdir(parent_dir):
            if fname.endswith('.kicad_sch') and fname != basename:
                sibling = os.path.join(parent_dir, fname)
                try:
                    with open(sibling, 'r', encoding='utf-8',
                              errors='replace') as f:
                        content = f.read()
                    if basename in content:
                        return True
                except OSError:
                    continue
    except OSError:
        pass
    return False


def _root_references_target(root_sch: str, target: str) -> bool:
    """Check if root_sch's sheet tree references target (by relative path).

    Handles both same-directory and sub-directory layouts by computing the
    relative path from the root's directory to the target.  Reads the full
    file because sheet blocks can appear after large lib_symbols sections.
    """
    try:
        root_dir = os.path.dirname(os.path.abspath(root_sch))
        target_abs = os.path.abspath(target)
        # Compute the relative path the root would use in Sheetfile property
        rel_path = os.path.relpath(target_abs, root_dir)
        # Also try just the basename (same-directory case)
        basename = os.path.basename(target_abs)

        with open(root_sch, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        # Check for relative path or basename in content
        # KiCad uses forward slashes in Sheetfile even on Windows
        for needle in (rel_path, rel_path.replace(os.sep, '/'), basename):
            if needle in content:
                return True
    except OSError:
        pass
    return False


def discover_root_schematic(target_path: str) -> str | None:
    """Find the root .kicad_sch for a sub-sheet file.

    Returns the root schematic path, or None if the target appears to be
    the root or no root can be found.

    Strategy (KH-305, KH-306 hardened):
    1. Same directory: look for .kicad_pro, derive root .kicad_sch.
       When multiple .kicad_pro exist (KH-306), verify each candidate's
       sheet tree references the target.
    2. Same directory: scan sibling .kicad_sch files for references.
    3. Parent directories (KH-305): walk up to 5 levels looking for
       .kicad_pro whose root .kicad_sch references the target via a
       relative path (handles sheets/ subdirectory layouts).
    4. Return None if nothing found.
    """
    target = os.path.abspath(target_path)
    parent_dir = os.path.dirname(target)
    target_basename = os.path.basename(target)

    try:
        entries = os.listdir(parent_dir)
    except OSError:
        entries = []

    # Tier 1: .kicad_pro stem match (same directory)
    # KH-306: when multiple .kicad_pro exist, verify sheet-tree membership
    pro_files = [f for f in entries if f.endswith('.kicad_pro')]

    if len(pro_files) == 1:
        stem = pro_files[0][:-len('.kicad_pro')]
        candidate = os.path.join(parent_dir, stem + '.kicad_sch')
        if os.path.isfile(candidate) and os.path.abspath(candidate) != target:
            return candidate
    elif len(pro_files) > 1:
        # Multiple projects — check which one's sheet tree references us
        for pro in pro_files:
            stem = pro[:-len('.kicad_pro')]
            candidate = os.path.join(parent_dir, stem + '.kicad_sch')
            if (os.path.isfile(candidate)
                    and os.path.abspath(candidate) != target
                    and _root_references_target(candidate, target)):
                return candidate

    # Tier 2: scan sibling .kicad_sch files for (sheet ...) blocks
    siblings = [f for f in entries
                if f.endswith('.kicad_sch') and f != target_basename]
    for fname in siblings:
        candidate = os.path.join(parent_dir, fname)
        try:
            with open(candidate, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            if target_basename in content:
                return candidate
        except OSError:
            continue

    # Tier 3 (KH-305): walk up parent directories looking for .kicad_pro
    # Handles sub-directory layouts (e.g., sheets/video.kicad_sch)
    search_dir = parent_dir
    for _ in range(5):
        search_dir = os.path.dirname(search_dir)
        if search_dir == os.path.dirname(search_dir):
            break  # Hit filesystem root
        try:
            parent_entries = os.listdir(search_dir)
        except OSError:
            continue
        for fname in parent_entries:
            if fname.endswith('.kicad_pro'):
                stem = fname[:-len('.kicad_pro')]
                candidate = os.path.join(search_dir, stem + '.kicad_sch')
                if (os.path.isfile(candidate)
                        and _root_references_target(candidate, target)):
                    return candidate

    return None


def resolve_project_input(path: str, target_ext: str = '.kicad_sch') -> tuple:
    """Resolve a CLI input path to the correct project file.

    Accepts:
      - A ``.kicad_sch`` / ``.kicad_pcb`` file (returned as-is)
      - A ``.kicad_pro`` file (derives the matching target_ext file)
      - A directory (finds ``.kicad_pro`` inside, then derives)

    Args:
        path: User-supplied path (file or directory).
        target_ext: The extension to resolve to (``.kicad_sch`` or
            ``.kicad_pcb``).

    Returns:
        ``(resolved_path, note)`` where *resolved_path* is the absolute
        path to the target file and *note* is a human-readable string
        describing any resolution that occurred (empty when the input
        was already the target type).

    Raises:
        FileNotFoundError: When the input cannot be resolved.
    """
    path = os.path.abspath(path)

    # --- Input is a directory: look for .kicad_pro inside ---
    if os.path.isdir(path):
        pro_files = [f for f in os.listdir(path) if f.endswith('.kicad_pro')]
        if not pro_files:
            raise FileNotFoundError(
                f"No .kicad_pro file found in directory: {path}")
        if len(pro_files) > 1:
            raise FileNotFoundError(
                f"Multiple .kicad_pro files in {path}: {pro_files}")
        pro_stem = pro_files[0][:-len('.kicad_pro')]
        candidate = os.path.join(path, pro_stem + target_ext)
        if not os.path.isfile(candidate):
            raise FileNotFoundError(
                f"Project '{pro_stem}' found but {pro_stem}{target_ext} "
                f"does not exist in {path}")
        return candidate, f"Resolved from directory via {pro_files[0]}"

    # --- Input is a .kicad_pro file ---
    if path.endswith('.kicad_pro'):
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Project file not found: {path}")
        pro_stem = os.path.basename(path)[:-len('.kicad_pro')]
        parent_dir = os.path.dirname(path)
        candidate = os.path.join(parent_dir, pro_stem + target_ext)
        if not os.path.isfile(candidate):
            raise FileNotFoundError(
                f"Project '{pro_stem}' found but {pro_stem}{target_ext} "
                f"does not exist in {parent_dir}")
        return candidate, f"Resolved from {os.path.basename(path)}"

    # --- Input already has the target extension ---
    if path.endswith(target_ext):
        if not os.path.isfile(path):
            raise FileNotFoundError(f"File not found: {path}")
        return path, ""

    # --- Fallback: unrecognised extension ---
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")
    return path, ""


def extract_pro_net_classes(pro: dict) -> list[dict]:
    """Extract net classes from .kicad_pro ``net_settings``.

    Returns list of dicts with: name, clearance, track_width, via_diameter,
    via_drill, diff_pair_width, diff_pair_gap.  Net assignments are merged
    from both ``netclass_patterns`` and ``netclass_assignments``.
    """
    ns = pro.get('net_settings', {})
    raw_classes = ns.get('classes', [])
    patterns = ns.get('netclass_patterns') or []
    assignments = ns.get('netclass_assignments') or {}

    # Build pattern-based net lists per class
    class_nets: dict[str, list[str]] = {}
    for p in patterns:
        nc_name = p.get('netclass', '')
        pattern = p.get('pattern', '')
        if nc_name and pattern:
            class_nets.setdefault(nc_name, []).append(pattern)

    # Add direct assignments.
    # KH-235: nc_value can be a list when a net belongs to multiple
    # classes (newer .kicad_pro format). Harness corpus audit confirmed
    # 139 files with list-valued netclass_assignments, 0 files with
    # list-valued netclass_patterns — so only the assignments loop
    # needs coercion. Two list-format variants observed: single-class
    # wrapped in a 1-element list ("+BATT": ["+BATT"]) and explicit
    # class-name-as-list ("Net-...": ["Power"]). Both crash the same
    # way via setdefault() hashing a list. Coerce to iterable and
    # register the net under each class.
    for net_name, nc_value in assignments.items():
        if not nc_value:
            continue
        nc_names = nc_value if isinstance(nc_value, list) else [nc_value]
        for nc_name in nc_names:
            if nc_name:
                class_nets.setdefault(nc_name, []).append(net_name)

    result = []
    for c in raw_classes:
        name = c.get('name', '')
        entry = {
            'name': name,
            'clearance': c.get('clearance'),
            'track_width': c.get('track_width'),
            'via_diameter': c.get('via_diameter'),
            'via_drill': c.get('via_drill'),
            'diff_pair_width': c.get('diff_pair_width'),
            'diff_pair_gap': c.get('diff_pair_gap'),
        }
        # Remove None values
        entry = {k: v for k, v in entry.items() if v is not None}
        nets = class_nets.get(name, [])
        if nets:
            entry['nets'] = nets
        result.append(entry)
    return result


def extract_pro_design_rules(pro: dict) -> dict:
    """Extract board design rules from .kicad_pro.

    Returns dict with min_clearance, min_track_width, min_via_diameter, etc.
    Values are in mm (KiCad native unit).
    """
    rules = pro.get('board', {}).get('design_settings', {}).get('rules', {})
    if not rules:
        return {}
    # Extract the most useful rules
    return {k: v for k, v in rules.items()
            if isinstance(v, (int, float)) and k.startswith('min_')}


def extract_pro_text_variables(pro: dict) -> dict:
    """Extract text variables from .kicad_pro.

    Text variables are user-defined key-value pairs used in schematic and
    PCB text fields via ``${VARIABLE_NAME}`` syntax.
    """
    return pro.get('text_variables', {}) or {}


def load_kicad_dru(file_path: str) -> list[dict] | None:
    """Load custom design rules from ``.kicad_dru`` adjacent to a KiCad file.

    Returns list of rule dicts::

        {"name": "Track width, outer",
         "layer": "outer",
         "condition": "A.Type == 'track'",
         "constraints": [{"type": "track_width", "min": 0.127}]}

    Conditions are kept as raw strings — not evaluated.
    Returns None if no ``.kicad_dru`` found.
    """
    from sexp_parser import parse as _sexp_parse, find_all, find_first, get_value

    parent = os.path.dirname(os.path.abspath(file_path))
    dru_path = None
    try:
        for fname in os.listdir(parent):
            if fname.endswith('.kicad_dru'):
                dru_path = os.path.join(parent, fname)
                break
    except OSError:
        return None
    if not dru_path:
        return None

    try:
        with open(dru_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except OSError:
        return None

    # .kicad_dru has multiple top-level forms — wrap in synthetic root
    try:
        tree = _sexp_parse(f'(dru_root {content})')
    except (ValueError, IndexError):
        return None

    rules = []
    for r in find_all(tree, 'rule'):
        name = r[1] if len(r) > 1 and isinstance(r[1], str) else ''

        layer_node = find_first(r, 'layer')
        layer = (layer_node[1]
                 if layer_node and len(layer_node) > 1
                 else None)

        condition = get_value(r, 'condition')

        constraints = []
        for c in find_all(r, 'constraint'):
            if len(c) < 2:
                continue
            ctype = c[1]
            entry: dict = {'type': ctype}
            for key in ('min', 'max', 'opt'):
                val = get_value(c, key)
                if val is not None:
                    # Strip 'mm' suffix if present
                    val_str = str(val).rstrip('m').rstrip('m')
                    try:
                        entry[key] = float(val_str)
                    except ValueError:
                        entry[key] = val
            constraints.append(entry)

        rule_dict: dict = {'name': name}
        if layer:
            rule_dict['layer'] = layer
        if condition:
            rule_dict['condition'] = condition
        if constraints:
            rule_dict['constraints'] = constraints
        rules.append(rule_dict)

    return rules if rules else None


def load_lib_tables(file_path: str) -> dict:
    """Load ``fp-lib-table`` and ``sym-lib-table`` from a KiCad project directory.

    Scans the directory containing *file_path* for library table files.

    Returns ``{'symbol_libs': [...], 'footprint_libs': [...]}``.
    Each lib entry is ``{'name': str, 'type': str, 'uri': str, 'descr': str}``.
    """
    from sexp_parser import parse_file as _sexp_parse_file, find_all, get_value

    parent = os.path.dirname(os.path.abspath(file_path))
    result: dict = {'symbol_libs': [], 'footprint_libs': []}

    for table_file, key in (('sym-lib-table', 'symbol_libs'),
                             ('fp-lib-table', 'footprint_libs')):
        table_path = os.path.join(parent, table_file)
        if not os.path.isfile(table_path):
            continue
        try:
            tree = _sexp_parse_file(table_path)
        except (ValueError, OSError):
            continue

        for lib in find_all(tree, 'lib'):
            entry = {
                'name': get_value(lib, 'name') or '',
                'type': get_value(lib, 'type') or '',
                'uri': get_value(lib, 'uri') or '',
            }
            descr = get_value(lib, 'descr')
            if descr:
                entry['descr'] = descr
            result[key].append(entry)

    return result


# ---------------------------------------------------------------------------
# Switching frequency lookup table — single source of truth for both
# signal_detectors.py and emc_rules.py.  See KH-237 for collision audit.
# Sources: DigiKey parametric data + manufacturer datasheets (verified 2026-04-12).
# ~100 entries: 8 broad collision prefixes replaced with per-sub-family entries.
# ---------------------------------------------------------------------------
_KNOWN_FREQS = {
    # --- TPS54 family (was single 'TPS54': 570e3, now split per DigiKey) ---
    'TPS54331': 570e3,     # TPS54331/54531: 570kHz
    'TPS54531': 570e3,
    'TPS5430': 500e3,      # TPS5430: 500kHz (note: overlaps TPS54302 below)
    'TPS54302': 400e3,     # TPS54302: 400kHz
    'TPS54308': 350e3,     # TPS54308: 350kHz
    'TPS54202': 500e3,     # TPS54202: 500kHz
    'TPS5410': 500e3,      # TPS5410: 500kHz
    'TPS5450': 500e3,      # TPS5450: 500kHz
    'TPS5405': 500e3,      # TPS5405: 500kHz
    'TPS54560': 500e3,     # TPS54560: 500kHz
    'TPS54226': 700e3,     # TPS54226: 700kHz
    'TPS54294': 700e3,     # TPS54294: 700kHz
    'TPS54227': 700e3,     # TPS54227: 700kHz
    'TPS542951': 700e3,    # TPS542951: 700kHz
    'TPS54527': 650e3,     # TPS54527: 650kHz
    'TPS546D': 550e3,      # TPS546D24S: 550kHz
    # --- TPS62 family (was single 'TPS62': 2.5e6, now split) ---
    'TPS62130': 2.5e6,     # TPS62130/33/40 family: 2.5MHz
    'TPS62140': 2.5e6,
    'TPS62133': 2.5e6,
    'TPS62150': 2.5e6,
    'TPS62160': 2.25e6,    # TPS62160: 2.25MHz typ (differs from TPS62130/140/150 family at 2.5MHz)
    'TPS62203': 1.0e6,     # TPS62203/77: 1MHz
    'TPS62175': 1.0e6,
    'TPS62177': 1.0e6,
    'TPS62840': 1.8e6,     # TPS62840/42: 1.8MHz
    'TPS62842': 1.8e6,
    'TPS62823': 2.2e6,     # TPS6282x: 2.2MHz
    'TPS62826': 2.2e6,
    'TPS62824': 2.2e6,
    'TPS62827': 2.2e6,
    'TPS62410': 2.25e6,    # TPS62410/290/170 family: 2.25MHz
    'TPS62290': 2.25e6,
    'TPS62170': 2.25e6,
    'TPS62A01': 2.4e6,     # TPS62A01/A02: 2.4MHz
    'TPS62A02': 2.4e6,
    'TPS62065': 3.0e6,     # TPS62065: 3MHz
    'TPS62088': 4.0e6,     # TPS62088: 4MHz
    'TPS62237': 2.0e6,     # TPS62237: 2MHz
    # --- TPS61 family (was single 'TPS61': 1.0e6, now split) ---
    'TPS61023': 1.0e6,     # TPS61023: 1MHz
    'TPS61235': 1.0e6,     # TPS61235: 1MHz
    'TPS61090': 600e3,     # TPS61090/030/032: 600kHz
    'TPS61030': 600e3,
    'TPS61032': 600e3,
    'TPS61070': 1.2e6,     # TPS61070/170: 1.2MHz
    'TPS61170': 1.2e6,
    'TPS61021': 2.0e6,     # TPS61021A: 2MHz
    'TPS61230': 2.0e6,     # TPS61230: 2MHz
    'TPS61253': 3.5e6,     # TPS61253: 3.5MHz
    'TPS61240': 3.5e6,     # TPS61240: 3.5MHz
    'TPS61288': 500e3,     # TPS61288: 500kHz
    'TPS61391': 700e3,     # TPS61391: 700kHz
    # --- TPS56 family (was single 'TPS56': 500e3, now split) ---
    'TPS56339': 500e3,     # TPS56339/637: 500kHz
    'TPS56637': 500e3,
    'TPS563300': 500e3,    # TPS563300: 500kHz
    'TPS565208': 500e3,    # TPS565208/201: 500kHz
    'TPS565201': 500e3,
    'TPS562201': 580e3,    # TPS562201/563201/563202/562208: 580kHz
    'TPS563201': 580e3,
    'TPS563202': 580e3,
    'TPS562208': 580e3,
    'TPS566238': 600e3,    # TPS566238: 600kHz
    'TPS560200': 600e3,    # TPS560200: 600kHz
    'TPS565242': 600e3,    # TPS565242: 600kHz
    'TPS563200': 650e3,    # TPS563200: 650kHz
    'TPS562200': 650e3,    # TPS562200: 650kHz
    'TPS560430': 1.1e6,    # TPS560430: 1.1MHz
    'TPS562212': 1.2e6,    # TPS562212: 1.2MHz
    'TPS564247': 1.2e6,    # TPS564247: 1.2MHz
    'TPS564208': 560e3,    # TPS564208: 560kHz
    'TPS561243': 1.28e6,   # TPS561243: 1.28MHz
    'TPS563240': 1.4e6,    # TPS563240: 1.4MHz
    # --- TPS63 family (was single 'TPS63': 2.4e6, now split) ---
    'TPS63020': 2.4e6,     # TPS63020/070/etc: 2.4MHz
    'TPS63070': 2.4e6,
    'TPS63060': 2.4e6,
    'TPS63000': 1.5e6,     # TPS63000: 1.5MHz max (differs from TPS63020/60/70 family at 2.4MHz)
    'TPS63802': 2.1e6,     # TPS63802: 2.1MHz
    'TPS631000': 2.0e6,    # TPS631000/011: 2MHz
    'TPS631011': 2.0e6,
    'TPS630250': 2.5e6,    # TPS630250: 2.5MHz
    # --- TPS629 family (was single 'TPS629': 2.2e6, now split) ---
    'TPS62912': 2.2e6,     # TPS62912: 2.2MHz
    'TPS62913': 2.2e6,     # TPS62913: dual 1/2.2MHz, use typical
    'TPS629203': 2.5e6,    # TPS629203: 2.5MHz
    'TPS629206': 2.5e6,    # TPS629206: 2.5MHz
    'TPS629210': 2.5e6,    # TPS629210: 2.5MHz
    'TPS62932': 2.2e6,     # TPS62932/33: adjustable 200k-2.2MHz, use typical
    'TPS62933': 2.2e6,
    # --- ADP2 family (was single 'ADP2': 700e3, now split) ---
    'ADP2302': 700e3,      # ADP2302/03: 700kHz
    'ADP2303': 700e3,
    'ADP2301': 1.4e6,      # ADP2301: 1.4MHz
    'ADP2503': 2.5e6,      # ADP2503: 2.5MHz
    # --- LTC36 family (was single 'LTC36': 1.0e6, now split) ---
    'LTC3600': 1.0e6,      # LTC3600: 1MHz typ
    'LTC3601': 2.0e6,      # LTC3601: 2MHz
    # LTC3631/3632/3638/3642: DigiKey returned no freq param — keep unmatched
    # --- Clean families (no collisions, kept as-is) ---
    'LM259': 150e3,    # LM2596/2594: 150kHz (verified clean)
    'LM257': 52e3,     # LM2575/2576: 52kHz (verified clean)
    'MP2307': 340e3,   # MP2307: 340kHz
    'MP1584': 1.5e6,   # MP1584: 1.5MHz
    'MP2359': 1.4e6,   # MP2359: 1.4MHz
    'AP3012': 1.5e6,   # AP3012: 1.5MHz
    'RT8059': 1.5e6,   # RT8059: 1.5MHz
    'SY8208': 800e3,   # SY8208: 800kHz (prefix narrowed from 'SY820' to avoid matching SY8200 family at 500kHz)
    'MCP1640': 500e3,  # MCP1640: 500kHz
    'MCP1603': 2.0e6,  # MCP1603: 2MHz
    'XL6009': 400e3,   # XL6009: 400kHz
    'XL4015': 180e3,   # XL4015: 180kHz
    'MT3608': 1.2e6,   # MT3608: 1.2MHz
}


def lookup_switching_freq(part_value: str) -> float | None:
    """Look up switching frequency from known regulator part numbers.

    Uses longest-prefix-first matching via startswith to avoid substring
    false positives (KH-237). Returns frequency in Hz or None if unknown.
    """
    if not part_value:
        return None
    val = part_value.upper()
    # Sort prefixes longest-first so 'TPS54331' matches before 'TPS54'
    for prefix in sorted(_KNOWN_FREQS, key=len, reverse=True):
        if val.startswith(prefix.upper()):
            return _KNOWN_FREQS[prefix]
    return None


def match_known_switching(value: str, lib_id: str) -> bool:
    """Check if a part matches the known switching regulator table."""
    val_upper = value.upper()
    lib_part = lib_id.split(":")[-1].upper() if ":" in lib_id else ""
    for prefix in _KNOWN_FREQS:
        pu = prefix.upper()
        if val_upper.startswith(pu) or lib_part.startswith(pu):
            return True
    return False


def build_net_id_map(pcb):
    """Return {net_id (int): net_name (str)} from PCB JSON.

    Handles both the current flat form pcb['nets'] = {"6": "GND", ...}
    and the legacy nested form pcb['nets']['net_info'] = [{"id": 6, ...}, ...].
    """
    nets = pcb.get('nets', {})
    out = {}
    if isinstance(nets, dict):
        for k, v in nets.items():
            if isinstance(v, str):
                try:
                    out[int(k)] = v
                except (ValueError, TypeError):
                    continue
        if out:
            return out
        for ni in nets.get('net_info', []) or []:
            try:
                out[int(ni.get('id', -1))] = ni.get('name', '')
            except (ValueError, TypeError):
                continue
    return out
