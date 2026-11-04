"""Component, IC-function, connector and jumper classification policies (kicad_core). Moved verbatim from kicad_utils.py."""
import re


# Component types that are not physical BOM parts (symbols, markers, mechanicals).
NON_COMPONENT_TYPES = frozenset({"power_symbol", "power_flag", "flag", "test_point",
                                 "mounting_hole", "fiducial", "graphic"})


def classify_component(ref: str, lib_id: str, value: str, is_power: bool = False,
                       footprint: str = "", in_bom: bool = False,
                       description: str = "", pins: list | None = None) -> str:
    """Classify component type from reference designator and library.

    pins: optional list of pin dicts (as produced by extract_lib_symbols,
    each with a "name" key) for the KH-370 oscillator corroboration check.
    None means pin data wasn't available to the caller (e.g. legacy .sch
    parsing) — corroboration is skipped and prior (permissive) behavior
    is preserved.
    """
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
                    # KH-370: bare "oscillator" substring over-fires on bus
                    # peripherals (ADC/MCU/sensor ICs) whose datasheet
                    # description merely mentions a built-in reference/timing
                    # oscillator. Exclude that phrasing, then require pin
                    # evidence of an actual clock-output part.
                    _osc_internal_phrases = ("internal oscillator", "on-chip oscillator",
                                              "internal reference", "with oscillator")
                    if not any(x in _desc_low for x in _osc_internal_phrases):
                        _clock_pin_names = {"OUT", "OUTPUT", "CLK", "CLKOUT", "XOUT", "FOUT"}
                        _has_clock_pin = pins is not None and any(
                            (p.get("name") or "").strip().upper() in _clock_pin_names
                            for p in pins)
                        if pins is None or _has_clock_pin or len(pins) <= 4:
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
        # An F-prefixed logic/analog IC (74LS32 as F1, seen in the corpus) is
        # an IC, not a fuse — PP-001 must not bridge it.
        if result == "fuse":
            if (lib_low.startswith(("74xx", "4xxx", "logic", "amplifier", "interface"))
                    or re.match(r'^(sn|mc|cd|hef|hc|hd|m)?(74|40|45)[a-z]{0,3}\d{2,}(?!\s*m?a\b)', val_low)):
                return "ic"
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
                # An F-prefixed logic/analog IC (74LS32 as F1, seen in the
                # corpus) is an IC, not a fuse — PP-001 must not bridge it.
                if (lib_lower.startswith(("74xx", "4xxx", "logic", "amplifier", "interface"))
                        or re.match(r'^(sn|mc|cd|hef|hc|hd|m)?(74|40|45)[a-z]{0,3}\d{2,}(?!\s*m?a\b)', val_lower)):
                    return "ic"
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
