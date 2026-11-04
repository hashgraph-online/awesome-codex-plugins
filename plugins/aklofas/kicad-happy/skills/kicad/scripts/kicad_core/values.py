"""Value parsing, E-series and coordinate units (kicad_core). Moved verbatim from kicad_utils.py."""
import math
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
