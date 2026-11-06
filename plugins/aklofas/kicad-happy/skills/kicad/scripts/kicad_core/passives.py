"""Passive-component electrical models: capacitor package/ESR/ESL, dielectric, DC-bias derating, inductor shielding (kicad_core). Moved verbatim from kicad_utils.py."""
import re


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
