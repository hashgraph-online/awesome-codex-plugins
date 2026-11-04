"""Known-part knowledge tables: regulator Vref and switching frequencies (kicad_core). Moved verbatim from kicad_utils.py; sources and verification dates are in the table comments. Typical MLCC ESL/ESR by package moved verbatim from emc_formulas.py."""
import re


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


def default_switching_freq(topology: str) -> float | None:
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


def match_known_switching(value: str, lib_id: str) -> bool:
    """Check if a part matches the known switching regulator table."""
    val_upper = value.upper()
    lib_part = lib_id.split(":")[-1].upper() if ":" in lib_id else ""
    for prefix in _KNOWN_FREQS:
        pu = prefix.upper()
        if val_upper.startswith(pu) or lib_part.startswith(pu):
            return True
    return False


# ---------------------------------------------------------------------------
# ESR/ESL lookup by package size (typical MLCC values) — moved verbatim from emc_formulas.py
# ---------------------------------------------------------------------------

# Typical ESL values for MLCC by package (Henries)
MLCC_ESL = {
    '0201': 0.3e-9,
    '0402': 0.5e-9,
    '0603': 0.7e-9,
    '0805': 0.9e-9,
    '1206': 1.1e-9,
    '1210': 1.2e-9,
    '1812': 1.5e-9,
    '2220': 1.8e-9,
}

# Typical ESR values for MLCC by package (Ohms) — X5R/X7R at 1 MHz
MLCC_ESR = {
    '0201': 0.5,
    '0402': 0.3,
    '0603': 0.1,
    '0805': 0.05,
    '1206': 0.03,
    '1210': 0.02,
    '1812': 0.02,
    '2220': 0.015,
}
