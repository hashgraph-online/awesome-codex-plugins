"""
Lookup table of electrical specs for common electronic components.

Tier 1 model resolution: instant, offline, no API calls. Covers the
most frequently used opamps, LDOs, comparators, and voltage references.
Specs are verified against manufacturer datasheets.

MPN matching is prefix-based — "LM358" matches "LM358DR", "LM358DT",
"LM358N", "LM358BIDR", etc. Suffixes encode package/temperature/tape
variants that don't affect electrical specs.
"""

import re


# ---------------------------------------------------------------------------
# Opamp specs — sorted by frequency of appearance in KiCad designs
#
# Keys:
#   gbw_hz:     Gain-bandwidth product (Hz)
#   slew_vus:   Slew rate (V/µs)
#   vos_mv:     Input offset voltage, typical (mV)
#   aol_db:     Open-loop gain (dB)
#   rin_ohms:   Differential input impedance (ohms)
#   supply_min: Minimum supply voltage (V)
#   supply_max: Maximum supply voltage (V)
#   rro:        Rail-to-rail output (bool)
#   rri:        Rail-to-rail input (bool)
#   swing_v:    Output swing from rail (V) — 0 if rail-to-rail
# ---------------------------------------------------------------------------
OPAMP_SPECS = {
    # TI — general purpose
    "LM358":    {"gbw_hz": 1e6,   "slew_vus": 0.3,  "vos_mv": 2.0,  "aol_db": 100, "rin_ohms": 2e6,   "supply_min": 3,   "supply_max": 32,  "rro": False, "rri": False, "swing_v": 1.5},
    "LM324":    {"gbw_hz": 1e6,   "slew_vus": 0.5,  "vos_mv": 2.0,  "aol_db": 100, "rin_ohms": 2e6,   "supply_min": 3,   "supply_max": 32,  "rro": False, "rri": False, "swing_v": 1.5},
    # TL072/TL074 supply_min: TI SLOS080V Recommended Operating Conditions, VS 4.5 V min
    # (10 V for the NS/PS packages and TL07xM)
    "TL072":    {"gbw_hz": 3e6,   "slew_vus": 8,    "vos_mv": 3.0,  "aol_db": 106, "rin_ohms": 1e12,  "supply_min": 4.5, "supply_max": 36,  "rro": False, "rri": False, "swing_v": 2.0},
    "TL074":    {"gbw_hz": 3e6,   "slew_vus": 8,    "vos_mv": 3.0,  "aol_db": 106, "rin_ohms": 1e12,  "supply_min": 4.5, "supply_max": 36,  "rro": False, "rri": False, "swing_v": 2.0},
    "TL082":    {"gbw_hz": 4e6,   "slew_vus": 13,   "vos_mv": 3.0,  "aol_db": 106, "rin_ohms": 1e12,  "supply_min": 7,   "supply_max": 36,  "rro": False, "rri": False, "swing_v": 2.0},
    "TL084":    {"gbw_hz": 4e6,   "slew_vus": 13,   "vos_mv": 3.0,  "aol_db": 106, "rin_ohms": 1e12,  "supply_min": 7,   "supply_max": 36,  "rro": False, "rri": False, "swing_v": 2.0},
    "NE5532":   {"gbw_hz": 10e6,  "slew_vus": 9,    "vos_mv": 0.5,  "aol_db": 100, "rin_ohms": 300e3, "supply_min": 8,   "supply_max": 44,  "rro": False, "rri": False, "swing_v": 2.0},
    "OPA2134":  {"gbw_hz": 8e6,   "slew_vus": 20,   "vos_mv": 1.0,  "aol_db": 120, "rin_ohms": 1e13,  "supply_min": 5,   "supply_max": 36,  "rro": False, "rri": False, "swing_v": 2.0},
    "LM741":    {"gbw_hz": 1.5e6, "slew_vus": 0.5,  "vos_mv": 1.0,  "aol_db": 106, "rin_ohms": 2e6,   "supply_min": 10,  "supply_max": 36,  "rro": False, "rri": False, "swing_v": 2.0},

    # Microchip — low-power CMOS
    "MCP6002":  {"gbw_hz": 1e6,   "slew_vus": 0.6,  "vos_mv": 4.5,  "aol_db": 112, "rin_ohms": 1e13,  "supply_min": 1.8, "supply_max": 6,   "rro": True,  "rri": True,  "swing_v": 0.025},
    "MCP6004":  {"gbw_hz": 1e6,   "slew_vus": 0.6,  "vos_mv": 4.5,  "aol_db": 112, "rin_ohms": 1e13,  "supply_min": 1.8, "supply_max": 6,   "rro": True,  "rri": True,  "swing_v": 0.025},
    "MCP601":   {"gbw_hz": 2.8e6, "slew_vus": 2.3,  "vos_mv": 0.25, "aol_db": 120, "rin_ohms": 1e13,  "supply_min": 2.7, "supply_max": 6,   "rro": True,  "rri": False, "swing_v": 0.025},
    "MCP6022":  {"gbw_hz": 10e6,  "slew_vus": 7,    "vos_mv": 0.25, "aol_db": 120, "rin_ohms": 1e13,  "supply_min": 2.5, "supply_max": 5.5, "rro": True,  "rri": False, "swing_v": 0.025},

    # TI — precision / low-noise
    "OPA340":   {"gbw_hz": 5.5e6, "slew_vus": 6,    "vos_mv": 0.15, "aol_db": 126, "rin_ohms": 1e13,  "supply_min": 2.7, "supply_max": 5.5, "rro": True,  "rri": True,  "swing_v": 0.01},
    "OPA2340":  {"gbw_hz": 5.5e6, "slew_vus": 6,    "vos_mv": 0.15, "aol_db": 126, "rin_ohms": 1e13,  "supply_min": 2.7, "supply_max": 5.5, "rro": True,  "rri": True,  "swing_v": 0.01},
    "OPA2333":  {"gbw_hz": 0.35e6,"slew_vus": 0.16, "vos_mv": 0.01, "aol_db": 130, "rin_ohms": 100e9, "supply_min": 1.8, "supply_max": 5.5, "rro": True,  "rri": True,  "swing_v": 0.01},
    "OPA1612":  {"gbw_hz": 80e6,  "slew_vus": 27,   "vos_mv": 0.1,  "aol_db": 130, "rin_ohms": 36e6,  "supply_min": 9,   "supply_max": 36,  "rro": False, "rri": False, "swing_v": 2.0},

    # Analog Devices
    "AD8605":   {"gbw_hz": 10e6,  "slew_vus": 5,    "vos_mv": 0.02, "aol_db": 120, "rin_ohms": 1e12,  "supply_min": 2.7, "supply_max": 5.5, "rro": True,  "rri": True,  "swing_v": 0.02},
    "AD8607":   {"gbw_hz": 0.4e6, "slew_vus": 0.1,  "vos_mv": 0.02, "aol_db": 120, "rin_ohms": 1e12,  "supply_min": 2.7, "supply_max": 5.5, "rro": True,  "rri": True,  "swing_v": 0.02},
    "AD8099":   {"gbw_hz": 710e6, "slew_vus": 1350, "vos_mv": 0.2,  "aol_db": 92,  "rin_ohms": 6.5e6, "supply_min": 9,   "supply_max": 24,  "rro": False, "rri": False, "swing_v": 1.3},
    "OP07":     {"gbw_hz": 0.6e6, "slew_vus": 0.3,  "vos_mv": 0.06, "aol_db": 126, "rin_ohms": 33e6,  "supply_min": 6,   "supply_max": 36,  "rro": False, "rri": False, "swing_v": 2.0},
    "OP27":     {"gbw_hz": 8e6,   "slew_vus": 2.8,  "vos_mv": 0.03, "aol_db": 126, "rin_ohms": 6e6,   "supply_min": 8,   "supply_max": 36,  "rro": False, "rri": False, "swing_v": 2.0},
    "AD620":    {"gbw_hz": 1e6,   "slew_vus": 1.2,  "vos_mv": 0.03, "aol_db": 120, "rin_ohms": 10e9,  "supply_min": 5,   "supply_max": 24,  "rro": False, "rri": False, "swing_v": 1.2},

    # STMicroelectronics
    "LM2904":   {"gbw_hz": 0.7e6, "slew_vus": 0.3,  "vos_mv": 2.0,  "aol_db": 100, "rin_ohms": 2e6,   "supply_min": 3,   "supply_max": 32,  "rro": False, "rri": False, "swing_v": 1.5},
    "TSV912":   {"gbw_hz": 8e6,   "slew_vus": 4.5,  "vos_mv": 0.3,  "aol_db": 130, "rin_ohms": 1e12,  "supply_min": 1.5, "supply_max": 5.5, "rro": True,  "rri": True,  "swing_v": 0.01},

    # TI — current sense / instrumentation
    "INA219":   {"gbw_hz": 0.5e6, "slew_vus": 0.2,  "vos_mv": 0.04, "aol_db": 120, "rin_ohms": 1e9,   "supply_min": 3,   "supply_max": 5.5, "rro": True,  "rri": True,  "swing_v": 0.05},
    "INA226":   {"gbw_hz": 0.5e6, "slew_vus": 0.2,  "vos_mv": 0.01, "aol_db": 120, "rin_ohms": 1e9,   "supply_min": 2.7, "supply_max": 5.5, "rro": True,  "rri": True,  "swing_v": 0.05},

    # ON Semiconductor / others
    "LM833":    {"gbw_hz": 15e6,  "slew_vus": 7,    "vos_mv": 0.3,  "aol_db": 110, "rin_ohms": 300e3, "supply_min": 10,  "supply_max": 36,  "rro": False, "rri": False, "swing_v": 2.0},
    "MC4558":   {"gbw_hz": 5.5e6, "slew_vus": 1.7,  "vos_mv": 2.0,  "aol_db": 100, "rin_ohms": 5e6,   "supply_min": 8,   "supply_max": 36,  "rro": False, "rri": False, "swing_v": 2.0},
    "RC4558":   {"gbw_hz": 3e6,   "slew_vus": 1.7,  "vos_mv": 2.0,  "aol_db": 100, "rin_ohms": 5e6,   "supply_min": 8,   "supply_max": 36,  "rro": False, "rri": False, "swing_v": 2.0},
    "NJM4558":  {"gbw_hz": 3e6,   "slew_vus": 1.7,  "vos_mv": 2.0,  "aol_db": 100, "rin_ohms": 5e6,   "supply_min": 8,   "supply_max": 36,  "rro": False, "rri": False, "swing_v": 2.0},
    "OPA1678":  {"gbw_hz": 16e6,  "slew_vus": 9,    "vos_mv": 0.2,  "aol_db": 135, "rin_ohms": 1e13,  "supply_min": 4.5, "supply_max": 36,  "rro": False, "rri": False, "swing_v": 1.0},

    # Top coverage-gap parts from corpus analysis (2026-03-30)
    # TI — high-speed / wideband
    "OPA695":   {"gbw_hz": 1700e6,"slew_vus": 4300, "vos_mv": 1.5,  "aol_db": 70,  "rin_ohms": 160e3, "supply_min": 10,  "supply_max": 24,  "rro": False, "rri": False, "swing_v": 1.5},
    "OPA4991":  {"gbw_hz": 4.5e6, "slew_vus": 21,   "vos_mv": 0.025,"aol_db": 140, "rin_ohms": 100e9, "supply_min": 4.5, "supply_max": 40,  "rro": False, "rri": False, "swing_v": 1.5},
    "OPA1602":  {"gbw_hz": 35e6,  "slew_vus": 20,   "vos_mv": 0.1,  "aol_db": 130, "rin_ohms": 1e13,  "supply_min": 4.5, "supply_max": 36,  "rro": False, "rri": False, "swing_v": 2.0},
    "OPA1604":  {"gbw_hz": 35e6,  "slew_vus": 20,   "vos_mv": 0.1,  "aol_db": 130, "rin_ohms": 1e13,  "supply_min": 4.5, "supply_max": 36,  "rro": False, "rri": False, "swing_v": 2.0},
    "OPA4202":  {"gbw_hz": 1e6,   "slew_vus": 0.35, "vos_mv": 0.025,"aol_db": 142, "rin_ohms": 100e9, "supply_min": 4.5, "supply_max": 36,  "rro": False, "rri": False, "swing_v": 1.5},

    # TI — low-power / precision
    "TLV9151":  {"gbw_hz": 4.5e6, "slew_vus": 21,   "vos_mv": 0.7,  "aol_db": 114, "rin_ohms": 1e12,  "supply_min": 1.7, "supply_max": 5.5, "rro": True,  "rri": True,  "swing_v": 0.02},
    "LM6361":   {"gbw_hz": 50e6,  "slew_vus": 300,  "vos_mv": 2.0,  "aol_db": 80,  "rin_ohms": 1e12,  "supply_min": 10,  "supply_max": 36,  "rro": False, "rri": False, "swing_v": 2.0},

    # Analog Devices — precision / low-noise
    "ADA4528":  {"gbw_hz": 3.5e6, "slew_vus": 0.4,  "vos_mv": 0.003,"aol_db": 145, "rin_ohms": 200e6, "supply_min": 2.2, "supply_max": 5.5, "rro": True,  "rri": True,  "swing_v": 0.01},
    "ADA4898":  {"gbw_hz": 65e6,  "slew_vus": 55,   "vos_mv": 0.03, "aol_db": 120, "rin_ohms": 8e6,   "supply_min": 9,   "supply_max": 33,  "rro": False, "rri": False, "swing_v": 2.0},
    "ADA4610":  {"gbw_hz": 16e6,  "slew_vus": 25,   "vos_mv": 0.5,  "aol_db": 120, "rin_ohms": 1e13,  "supply_min": 10,  "supply_max": 36,  "rro": False, "rri": False, "swing_v": 2.0},
    "AD8512":   {"gbw_hz": 8e6,   "slew_vus": 20,   "vos_mv": 0.4,  "aol_db": 106, "rin_ohms": 1e13,  "supply_min": 8,   "supply_max": 36,  "rro": False, "rri": False, "swing_v": 2.0},
    "AD8676":   {"gbw_hz": 10e6,  "slew_vus": 2.5,  "vos_mv": 0.012,"aol_db": 130, "rin_ohms": 10e6,  "supply_min": 10,  "supply_max": 36,  "rro": False, "rri": False, "swing_v": 2.0},
    "AD817":    {"gbw_hz": 50e6,  "slew_vus": 350,  "vos_mv": 0.5,  "aol_db": 90,  "rin_ohms": 10e6,  "supply_min": 10,  "supply_max": 36,  "rro": False, "rri": False, "swing_v": 2.0},

    # Microchip — single-channel variants
    "MCP6001":  {"gbw_hz": 1e6,   "slew_vus": 0.6,  "vos_mv": 4.5,  "aol_db": 112, "rin_ohms": 1e13,  "supply_min": 1.8, "supply_max": 6,   "rro": True,  "rri": True,  "swing_v": 0.025},

    # JRC / NJR — common in audio
    "uPC324":   {"gbw_hz": 1e6,   "slew_vus": 0.4,  "vos_mv": 2.0,  "aol_db": 100, "rin_ohms": 2e6,   "supply_min": 3,   "supply_max": 32,  "rro": False, "rri": False, "swing_v": 1.5},
    "HA17558":  {"gbw_hz": 5.5e6, "slew_vus": 1.7,  "vos_mv": 2.0,  "aol_db": 100, "rin_ohms": 5e6,   "supply_min": 8,   "supply_max": 36,  "rro": False, "rri": False, "swing_v": 2.0},

    # Elantec / Intersil — high-speed
    "EL2018":   {"gbw_hz": 160e6, "slew_vus": 1500, "vos_mv": 2.0,  "aol_db": 80,  "rin_ohms": 1e6,   "supply_min": 10,  "supply_max": 36,  "rro": False, "rri": False, "swing_v": 2.0},
}

# ---------------------------------------------------------------------------
# LDO regulator specs
#
# Keys:
#   vref:       Internal reference voltage (V) — for adjustable parts
#   dropout_mv: Dropout voltage at typical load (mV)
#   iq_ua:      Quiescent current, typical (µA)
#   iout_max_ma: Maximum output current (mA)
#   vout_fixed: Dict mapping suffix → fixed Vout, if applicable
# ---------------------------------------------------------------------------
LDO_SPECS = {
    # 78xx family — all manufacturers (LM78xx, L78xx, MC78xx, uA78xx, KA78xx)
    # Same electrical specs regardless of manufacturer prefix
    "LM7805":   {"vref": 5.0,  "dropout_mv": 2000, "iq_ua": 5000,  "iout_max_ma": 1500, "fixed": True},
    "L7805":    {"vref": 5.0,  "dropout_mv": 2000, "iq_ua": 5000,  "iout_max_ma": 1500, "fixed": True},
    "MC7805":   {"vref": 5.0,  "dropout_mv": 2000, "iq_ua": 5000,  "iout_max_ma": 1500, "fixed": True},
    "KA7805":   {"vref": 5.0,  "dropout_mv": 2000, "iq_ua": 5000,  "iout_max_ma": 1500, "fixed": True},
    "LM7812":   {"vref": 12.0, "dropout_mv": 2000, "iq_ua": 5000,  "iout_max_ma": 1500, "fixed": True},
    "L7812":    {"vref": 12.0, "dropout_mv": 2000, "iq_ua": 5000,  "iout_max_ma": 1500, "fixed": True},
    "LM7833":   {"vref": 3.3,  "dropout_mv": 2000, "iq_ua": 5000,  "iout_max_ma": 1500, "fixed": True},
    "L7833":    {"vref": 3.3,  "dropout_mv": 2000, "iq_ua": 5000,  "iout_max_ma": 1500, "fixed": True},
    "LM7809":   {"vref": 9.0,  "dropout_mv": 2000, "iq_ua": 5000,  "iout_max_ma": 1500, "fixed": True},
    "L7809":    {"vref": 9.0,  "dropout_mv": 2000, "iq_ua": 5000,  "iout_max_ma": 1500, "fixed": True},
    "LM7815":   {"vref": 15.0, "dropout_mv": 2000, "iq_ua": 5000,  "iout_max_ma": 1500, "fixed": True},
    "L7815":    {"vref": 15.0, "dropout_mv": 2000, "iq_ua": 5000,  "iout_max_ma": 1500, "fixed": True},

    # 1117 family — multiple manufacturers
    "LM1117":   {"vref": 1.25, "dropout_mv": 1000, "iq_ua": 5000,  "iout_max_ma": 800,  "vout_fixed": {"-3.3": 3.3, "-5.0": 5.0, "-2.5": 2.5, "-1.8": 1.8}},
    "TLV1117":  {"vref": 1.25, "dropout_mv": 1000, "iq_ua": 5000,  "iout_max_ma": 800},
    "REG1117":  {"vref": 1.25, "dropout_mv": 1000, "iq_ua": 5000,  "iout_max_ma": 800,  "vout_fixed": {"-3.3": 3.3, "-5.0": 5.0, "-2.5": 2.5, "-1.8": 1.8}},

    # TI
    "TPS7A05":  {"vref": 0.5,  "dropout_mv": 110,  "iq_ua": 1,     "iout_max_ma": 100},
    "TPS7A20":  {"vref": 0.5,  "dropout_mv": 300,  "iq_ua": 6.5,   "iout_max_ma": 300},
    "TPS7230":  {"vref": 1.21, "dropout_mv": 300,  "iq_ua": 260,   "iout_max_ma": 200},

    # AMS
    "AMS1117":  {"vref": 1.25, "dropout_mv": 1300, "iq_ua": 5000,  "iout_max_ma": 1000, "vout_fixed": {"-3.3": 3.3, "-5.0": 5.0, "-2.5": 2.5, "-1.8": 1.8}},

    # Microchip
    "MCP1700":  {"vref": 1.2,  "dropout_mv": 178,  "iq_ua": 1.6,   "iout_max_ma": 250},
    "MCP1702":  {"vref": 1.2,  "dropout_mv": 625,  "iq_ua": 2,     "iout_max_ma": 250},
    "MCP1826":  {"vref": 0.8,  "dropout_mv": 250,  "iq_ua": 120,   "iout_max_ma": 1000},

    # Diodes Inc
    "AP2112":   {"vref": 0.8,  "dropout_mv": 250,  "iq_ua": 55,    "iout_max_ma": 600, "vout_fixed": {"-3.3": 3.3, "-2.5": 2.5, "-1.8": 1.8}},
    "AP2127":   {"vref": 0.8,  "dropout_mv": 275,  "iq_ua": 55,    "iout_max_ma": 300},
    "AP7361":   {"vref": 0.8,  "dropout_mv": 360,  "iq_ua": 40,    "iout_max_ma": 1000},

    # ON Semiconductor
    "NCP1117":  {"vref": 1.25, "dropout_mv": 1000, "iq_ua": 5000,  "iout_max_ma": 1000},

    # STMicroelectronics
    "LD1117":   {"vref": 1.25, "dropout_mv": 1100, "iq_ua": 5000,  "iout_max_ma": 800, "vout_fixed": {"-3.3": 3.3, "-5.0": 5.0, "-2.5": 2.5}},

    # Richtek
    "RT9080":   {"vref": 0.8,  "dropout_mv": 250,  "iq_ua": 2,     "iout_max_ma": 600, "vout_fixed": {"-3.3": 3.3, "-2.5": 2.5, "-1.8": 1.8, "-1.2": 1.2}},

    # TI — low-Iq
    "TPS7A02":  {"vref": 0.5,  "dropout_mv": 200,  "iq_ua": 0.025, "iout_max_ma": 50},
    "LP5907":   {"vref": 0.5,  "dropout_mv": 120,  "iq_ua": 12,    "iout_max_ma": 250},
    "TLV755":   {"vref": 0.6,  "dropout_mv": 200,  "iq_ua": 12,    "iout_max_ma": 500},
    "TPS709":   {"vref": 1.15, "dropout_mv": 300,  "iq_ua": 1,     "iout_max_ma": 150},
    "LP2985":   {"vref": 1.25, "dropout_mv": 280,  "iq_ua": 400,   "iout_max_ma": 150},

    # Torex
    "XC6220":   {"vref": 0.5,  "dropout_mv": 200,  "iq_ua": 8,     "iout_max_ma": 700},
    "XC6206":   {"vref": 0.9,  "dropout_mv": 250,  "iq_ua": 1,     "iout_max_ma": 200},
}

# ---------------------------------------------------------------------------
# Comparator specs
#
# Keys:
#   prop_delay_ns: Propagation delay, typical (ns)
#   output_type:   "open_collector", "open_drain", "push_pull", "totem_pole"
#   supply_min:    Minimum supply voltage (V)
#   supply_max:    Maximum supply voltage (V)
# ---------------------------------------------------------------------------
COMPARATOR_SPECS = {
    "LM393":    {"prop_delay_ns": 1300, "output_type": "open_collector", "supply_min": 2,   "supply_max": 36},
    "LM339":    {"prop_delay_ns": 1300, "output_type": "open_collector", "supply_min": 2,   "supply_max": 36},
    "LM311":    {"prop_delay_ns": 165,  "output_type": "open_collector", "supply_min": 3.5, "supply_max": 30},
    "LM2903":   {"prop_delay_ns": 1300, "output_type": "open_collector", "supply_min": 2,   "supply_max": 36},
    "TLV1805":  {"prop_delay_ns": 40,   "output_type": "push_pull",     "supply_min": 2.5, "supply_max": 5.5},
    "TLV3201":  {"prop_delay_ns": 40,   "output_type": "push_pull",     "supply_min": 2.7, "supply_max": 5.5},
    "MCP6561":  {"prop_delay_ns": 150,  "output_type": "push_pull",     "supply_min": 1.8, "supply_max": 5.5},
    "MAX9013":  {"prop_delay_ns": 80,   "output_type": "push_pull",     "supply_min": 2.5, "supply_max": 5.5},
    "AD8561":   {"prop_delay_ns": 7,    "output_type": "totem_pole",    "supply_min": 4.5, "supply_max": 10.5},
}

# ---------------------------------------------------------------------------
# Voltage reference specs
#
# Keys:
#   vref:       Reference voltage (V) — or dict for selectable parts
#   tempco_ppm: Temperature coefficient (ppm/°C), typical
#   zout_ohms:  Dynamic output impedance (ohms), typical
#   iq_ua:      Quiescent current (µA)
# ---------------------------------------------------------------------------
VREF_SPECS = {
    "TL431":    {"vref": 2.5,   "tempco_ppm": 50,  "zout_ohms": 0.2,  "iq_ua": 1000},
    "TLV431":   {"vref": 1.24,  "tempco_ppm": 50,  "zout_ohms": 0.22, "iq_ua": 80},
    "LM4040":   {"vref": {"": 2.5, "-2.5": 2.5, "-3.0": 3.0, "-3.3": 3.3, "-4.1": 4.096, "-5.0": 5.0}, "tempco_ppm": 100, "zout_ohms": 0.5, "iq_ua": 60},
    "LM385":    {"vref": 1.235, "tempco_ppm": 20,  "zout_ohms": 0.6,  "iq_ua": 20},
    "REF3033":  {"vref": 3.3,   "tempco_ppm": 50,  "zout_ohms": 0.05, "iq_ua": 200},
    "REF3025":  {"vref": 2.5,   "tempco_ppm": 50,  "zout_ohms": 0.05, "iq_ua": 200},
    "REF5050":  {"vref": 5.0,   "tempco_ppm": 3,   "zout_ohms": 0.01, "iq_ua": 1200},
    "REF5025":  {"vref": 2.5,   "tempco_ppm": 3,   "zout_ohms": 0.01, "iq_ua": 1200},
    "MCP1541":  {"vref": 4.096, "tempco_ppm": 50,  "zout_ohms": 1.0,  "iq_ua": 120},
    "ADR3412":  {"vref": 1.2,   "tempco_ppm": 10,  "zout_ohms": 0.2,  "iq_ua": 90},
}

# ---------------------------------------------------------------------------
# Discrete MOSFET specs — common SOT-23 FETs for behavioral model generation
#
# Keys:
#   vth_v:      Gate threshold voltage, typical (V)
#   rdson_ohm:  On-resistance at rated Vgs (ohms)
#   ciss_pf:    Input capacitance (pF)
#   vds_max:    Maximum drain-source voltage (V)
#   id_max_a:   Maximum continuous drain current (A)
#   type:       "nmos" or "pmos"
# ---------------------------------------------------------------------------
MOSFET_SPECS = {
    # N-channel SOT-23 — verified against downloaded datasheets 2026-03-31
    "BSS138":    {"vth_v": 1.1,  "rdson_ohm": 2.5,   "ciss_pf": 27,  "vds_max": 50,  "id_max_a": 0.22, "type": "nmos"},  # ON Semi, max Rdson@Vgs=10V
    "2N7002":    {"vth_v": 1.8,  "rdson_ohm": 5.0,   "ciss_pf": 50,  "vds_max": 60,  "id_max_a": 0.28, "type": "nmos"},  # Nexperia, max Rdson@Vgs=10V
    "AO3400":    {"vth_v": 1.05, "rdson_ohm": 0.027, "ciss_pf": 630, "vds_max": 30,  "id_max_a": 5.7,  "type": "nmos"},  # AOS AO3400A, max Rdson@Vgs=10V
    "SI2302":    {"vth_v": 0.63, "rdson_ohm": 0.057, "ciss_pf": 340, "vds_max": 20,  "id_max_a": 2.9,  "type": "nmos"},  # Vishay SI2302CDS, max Rdson@Vgs=4.5V
    "IRLML2502": {"vth_v": 0.9,  "rdson_ohm": 0.045, "ciss_pf": 740, "vds_max": 20,  "id_max_a": 4.2,  "type": "nmos"},  # Infineon, max Rdson@Vgs=4.5V
    "IRLML6344": {"vth_v": 0.8,  "rdson_ohm": 0.029, "ciss_pf": 650, "vds_max": 30,  "id_max_a": 5.0,  "type": "nmos"},  # Infineon, max Rdson@Vgs=4.5V
    "DMN3150":   {"vth_v": 0.92, "rdson_ohm": 0.072, "ciss_pf": 305, "vds_max": 30,  "id_max_a": 3.8,  "type": "nmos"},  # Diodes DMN3150L, max Rdson@Vgs=4.5V
    # P-channel SOT-23 — verified against downloaded datasheets 2026-03-31
    "BSS84":     {"vth_v": -1.6, "rdson_ohm": 7.5,   "ciss_pf": 24,  "vds_max": -50, "id_max_a": -0.15,"type": "pmos"},  # Nexperia BSS84AKW, max Rdson@Vgs=-10V
    "SI2301":    {"vth_v": -0.7, "rdson_ohm": 0.112, "ciss_pf": 405, "vds_max": -20, "id_max_a": -2.3, "type": "pmos"},  # Vishay SI2301CDS, max Rdson@Vgs=-4.5V
    "AO3401":    {"vth_v": -0.9, "rdson_ohm": 0.06,  "ciss_pf": 645, "vds_max": -30, "id_max_a": -4.0, "type": "pmos"},  # AOS AO3401A, max Rdson@Vgs=-4.5V
    # NOTE: DMP3150 removed — not a real part number (no Diodes Inc product).
    # NOTE: NTR4101 removed — datasheet unavailable for verification (ON Semi blocks download).
}


def lookup_mosfet_specs(mpn):
    """Look up discrete MOSFET specs by MPN prefix."""
    _, specs = _prefix_match(mpn, MOSFET_SPECS)
    return specs


# ---------------------------------------------------------------------------
# Crystal oscillator driver specs — MCU/IC transconductance for startup margin
#
# Keys:
#   gm_uA_V:   Oscillator driver transconductance (µA/V)
#   max_esr:    Maximum crystal ESR the driver can sustain (ohms)
#   drive_level_uW: Maximum crystal drive level (µW)
#   freq_range: (min_hz, max_hz) supported crystal frequency range
# Sources: MCU datasheets, app notes (AN2867, AN12061, etc.)
# ---------------------------------------------------------------------------
CRYSTAL_DRIVER_SPECS = {
    # STM32 families — from AN2867 "Oscillator design guide for STM8/STM32"
    "STM32F0":  {"gm_uA_V": 1000, "max_esr": 200,  "drive_level_uW": 1,   "freq_range": (4e6, 32e6)},
    "STM32F1":  {"gm_uA_V": 2000, "max_esr": 500,  "drive_level_uW": 1,   "freq_range": (4e6, 16e6)},
    "STM32F4":  {"gm_uA_V": 2500, "max_esr": 500,  "drive_level_uW": 1,   "freq_range": (4e6, 26e6)},
    "STM32L0":  {"gm_uA_V": 500,  "max_esr": 100,  "drive_level_uW": 0.5, "freq_range": (1e6, 25e6)},
    "STM32L4":  {"gm_uA_V": 1500, "max_esr": 300,  "drive_level_uW": 1,   "freq_range": (4e6, 48e6)},
    "STM32H7":  {"gm_uA_V": 3000, "max_esr": 500,  "drive_level_uW": 1,   "freq_range": (4e6, 48e6)},
    "STM32G0":  {"gm_uA_V": 1000, "max_esr": 200,  "drive_level_uW": 1,   "freq_range": (4e6, 48e6)},
    "STM32G4":  {"gm_uA_V": 2000, "max_esr": 500,  "drive_level_uW": 1,   "freq_range": (4e6, 48e6)},
    "STM32U5":  {"gm_uA_V": 1500, "max_esr": 300,  "drive_level_uW": 1,   "freq_range": (4e6, 48e6)},
    "STM32WB":  {"gm_uA_V": 1500, "max_esr": 300,  "drive_level_uW": 1,   "freq_range": (32e6, 32e6)},
    # 32.768kHz LSE on STM32 — separate oscillator with lower gm
    "STM32_LSE":{"gm_uA_V": 5,    "max_esr": 40000,"drive_level_uW": 0.5, "freq_range": (32768, 32768)},

    # Nordic nRF — from product specs
    "NRF52":    {"gm_uA_V": 1000, "max_esr": 200,  "drive_level_uW": 1,   "freq_range": (32e6, 32e6)},
    "NRF52_LSE":{"gm_uA_V": 5,    "max_esr": 50000,"drive_level_uW": 0.25,"freq_range": (32768, 32768)},
    "NRF53":    {"gm_uA_V": 1500, "max_esr": 300,  "drive_level_uW": 1,   "freq_range": (32e6, 32e6)},

    # Espressif ESP32
    "ESP32":    {"gm_uA_V": 2000, "max_esr": 500,  "drive_level_uW": 1,   "freq_range": (26e6, 40e6)},
    "ESP32S3":  {"gm_uA_V": 2000, "max_esr": 500,  "drive_level_uW": 1,   "freq_range": (26e6, 40e6)},
    "ESP32C3":  {"gm_uA_V": 2000, "max_esr": 500,  "drive_level_uW": 1,   "freq_range": (26e6, 40e6)},

    # Atmel/Microchip AVR — from AN2519
    "ATMEGA":   {"gm_uA_V": 800,  "max_esr": 200,  "drive_level_uW": 1,   "freq_range": (0.4e6, 20e6)},
    "ATTINY":   {"gm_uA_V": 500,  "max_esr": 150,  "drive_level_uW": 0.5, "freq_range": (0.4e6, 20e6)},
    "SAMD21":   {"gm_uA_V": 1000, "max_esr": 200,  "drive_level_uW": 1,   "freq_range": (0.4e6, 32e6)},
    "SAMD51":   {"gm_uA_V": 1500, "max_esr": 300,  "drive_level_uW": 1,   "freq_range": (8e6, 48e6)},

    # Raspberry Pi RP2040/RP2350
    "RP2040":   {"gm_uA_V": 1000, "max_esr": 200,  "drive_level_uW": 1,   "freq_range": (1e6, 15e6)},
    "RP2350":   {"gm_uA_V": 1500, "max_esr": 300,  "drive_level_uW": 1,   "freq_range": (1e6, 15e6)},

    # TI MSP430
    "MSP430":   {"gm_uA_V": 500,  "max_esr": 200,  "drive_level_uW": 1,   "freq_range": (4e6, 25e6)},
}


def lookup_crystal_driver_specs(ic_mpn):
    """Look up crystal oscillator driver specs for an IC.

    Args:
        ic_mpn: IC part number (e.g., "STM32F411CEU6", "ESP32-S3-WROOM")

    Returns:
        specs dict or None
    """
    _, specs = _prefix_match(ic_mpn, CRYSTAL_DRIVER_SPECS)
    return specs


# ---------------------------------------------------------------------------
# Lookup functions
# ---------------------------------------------------------------------------

def _prefix_match(mpn, table):
    """Match an MPN against a table using longest prefix.

    Returns (matched_key, specs_dict) or (None, None).
    MPN comparison is case-insensitive for the prefix.
    """
    if not mpn:
        return None, None

    mpn_upper = mpn.upper().strip()

    # Try exact match first (fastest)
    for key in table:
        if mpn_upper.startswith(key.upper()):
            return key, table[key]

    # Try without common distributor prefixes
    # e.g., "296-16557-1-ND" is a DigiKey PN, not an MPN
    if re.match(r'^\d{3}-', mpn):
        return None, None  # Distributor PN

    return None, None


def lookup_opamp_specs(mpn):
    """Look up opamp specs by MPN prefix.

    Returns specs dict or None.
    """
    _, specs = _prefix_match(mpn, OPAMP_SPECS)
    return specs


def lookup_ldo_specs(mpn):
    """Look up LDO specs by MPN prefix.

    Returns specs dict or None. For parts with fixed output variants,
    also checks for voltage suffix matching.
    """
    key, specs = _prefix_match(mpn, LDO_SPECS)
    if not specs:
        return None

    # Check for fixed-output suffix (e.g., AMS1117-3.3, AP2112-3.3)
    result = dict(specs)  # copy
    vout_fixed = specs.get("vout_fixed", {})
    if vout_fixed and mpn:
        mpn_upper = mpn.upper()
        for suffix, vout in vout_fixed.items():
            if suffix and suffix.upper() in mpn_upper:
                result["vref"] = vout
                result["fixed"] = True
                break

    return result


def lookup_comparator_specs(mpn):
    """Look up comparator specs by MPN prefix."""
    _, specs = _prefix_match(mpn, COMPARATOR_SPECS)
    return specs


def lookup_vref_specs(mpn):
    """Look up voltage reference specs by MPN prefix."""
    key, specs = _prefix_match(mpn, VREF_SPECS)
    if not specs:
        return None

    result = dict(specs)
    # Resolve selectable vref
    vref = specs.get("vref")
    if isinstance(vref, dict) and mpn:
        mpn_upper = mpn.upper()
        for suffix, v in vref.items():
            if suffix and suffix.upper() in mpn_upper:
                result["vref"] = v
                break
        else:
            # Default (no suffix match) — use the bare-key value
            result["vref"] = vref.get("", list(vref.values())[0])

    return result


def lookup_part_specs(mpn, component_type=None):
    """Look up specs for any component type.

    Args:
        mpn: Manufacturer part number (or KiCad value field)
        component_type: Optional hint — "opamp", "ldo", "comparator", "vref"

    Returns:
        (specs_dict, component_type_str) or (None, None)
    """
    if not mpn:
        return None, None

    # If type is specified, only search that table
    if component_type == "opamp":
        specs = lookup_opamp_specs(mpn)
        return (specs, "opamp") if specs else (None, None)
    if component_type == "ldo":
        specs = lookup_ldo_specs(mpn)
        return (specs, "ldo") if specs else (None, None)
    if component_type == "comparator":
        specs = lookup_comparator_specs(mpn)
        return (specs, "comparator") if specs else (None, None)
    if component_type == "vref":
        specs = lookup_vref_specs(mpn)
        return (specs, "vref") if specs else (None, None)

    # No type hint — try all tables in order
    for lookup_fn, type_name in [
        (lookup_opamp_specs, "opamp"),
        (lookup_ldo_specs, "ldo"),
        (lookup_comparator_specs, "comparator"),
        (lookup_vref_specs, "vref"),
    ]:
        specs = lookup_fn(mpn)
        if specs:
            return specs, type_name

    return None, None
