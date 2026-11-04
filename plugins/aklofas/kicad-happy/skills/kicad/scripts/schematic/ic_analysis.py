"""IC pinout and subcircuit analyses: verbatim move from analyze_schematic.py; no behaviour change."""
from __future__ import annotations

from kicad_types import (
    AnalysisContext,
)
from kicad_core.values import (
    COORD_EPSILON,
)
from schematic.connectivity import (
    get_net_neighbors,
)


# Static lookup tables for IC function classification (used by classify_ic_pinout_role)
_IC_LIB_PREFIX_MAP = {
    "regulator_linear": "linear regulator",
    "regulator_switching": "switching regulator",
    "regulator_controller": "regulator controller",
    "amplifier_operational": "operational amplifier",
    "amplifier_audio": "audio amplifier",
    "amplifier_instrumentation": "instrumentation amplifier",
    "amplifier_difference": "difference amplifier",
    "amplifier_current": "current sense amplifier",
    "amplifier_buffer": "buffer amplifier",
    "amplifier_video": "video amplifier",
    "analog_adc": "ADC",
    "analog_dac": "DAC",
    "analog_switch": "analog switch",
    "comparator": "comparator",
    "converter_dcdc": "DC-DC converter",
    "driver_motor": "motor driver",
    "driver_led": "LED driver",
    "driver_gate": "gate driver",
    "driver_display": "display driver",
    "driver_fet": "FET driver",
    "interface_can_lin": "CAN/LIN transceiver",
    "interface_ethernet": "Ethernet PHY",
    "interface_usb": "USB interface",
    "interface_uart": "UART interface",
    "interface_spi": "SPI interface",
    "interface_i2c": "I2C interface",
    "interface_rs485": "RS-485 transceiver",
    "interface_lvds": "LVDS interface",
    "interface_hdmi": "HDMI interface",
    "interface_optical": "optical interface",
    "logic_74xx": "logic IC (74xx)",
    "logic_4000": "logic IC (4000 series)",
    "logic_level": "level shifter",
    "memory_eeprom": "EEPROM",
    "memory_flash": "flash memory",
    "memory_ram": "RAM",
    "memory_rom": "ROM",
    "mcu": "microcontroller",
    "fpga": "FPGA",
    "cpld": "CPLD",
    "dsp": "DSP",
    "power_management": "power management IC",
    "power_supervisor": "voltage supervisor",
    "power_protection": "power protection IC",
    "rf_amplifier": "RF amplifier",
    "rf_mixer": "RF mixer",
    "rf_switch": "RF switch",
    "rf": "RF IC",
    "sensor_temperature": "temperature sensor",
    "sensor_pressure": "pressure sensor",
    "sensor_humidity": "humidity sensor",
    "sensor_current": "current sensor",
    "sensor_motion": "motion sensor",
    "sensor_magnetic": "magnetic sensor",
    "sensor_optical": "optical sensor",
    "sensor": "sensor IC",
    "timer": "timer IC",
    "reference_voltage": "voltage reference",
}


_IC_VALUE_KEYWORDS = [
    # Microcontrollers
    (("esp32", "esp8266", "esp32s", "esp32c", "esp32h"), "microcontroller (ESP)"),
    (("stm32", "stm8"), "microcontroller (STM)"),
    (("atmega", "attiny", "at90", "atxmega"), "microcontroller (AVR)"),
    (("pic16", "pic18", "pic24", "pic32", "dspic"), "microcontroller (PIC)"),
    (("rp2040", "rp2350"), "microcontroller (RP)"),
    (("nrf51", "nrf52", "nrf53", "nrf91"), "microcontroller (nRF)"),
    (("samd", "same", "samg", "saml", "samr"), "microcontroller (SAM)"),
    (("msp430", "msp432"), "microcontroller (MSP)"),
    (("efm32", "efr32"), "microcontroller (EFx32)"),
    (("cy8c",), "microcontroller (Cypress)"),
    (("gd32",), "microcontroller (GD32)"),
    (("ch32",), "microcontroller (CH32)"),
    (("kb2040",), "microcontroller (RP dev board)"),
    # FPGAs
    (("ice40", "ecp5", "machxo", "nexus"), "FPGA (Lattice)"),
    (("xc7", "xc6", "xczu", "xc2", "xcku", "artix", "spartan", "kintex", "virtex", "zynq"), "FPGA (Xilinx)"),
    (("10cl", "10m0", "5cg", "max10", "cyclone"), "FPGA (Intel)"),
    # Regulators
    (("lm117", "lm317", "lm337", "lm78", "lm79", "ams1117", "ap2112",
          "mic5205", "mic5504", "xc6206", "xc6220", "tps73", "tps76", "rt9013",
          "ld1117", "mcp1700", "mcp1703", "mcp1826", "ht7333", "ht7350"), "linear regulator"),
    (("lm2596", "lm2576", "mc34063", "tps54", "tps56", "tps61", "tps62",
          "tps63", "tps65", "mp1584", "mp2307", "mp2315", "mp2359",
          "ap3012", "sy80", "mt3608"), "switching regulator"),
    # Shift registers / logic
    (("74hc", "74lvc", "74ahc", "74act", "74ac", "sn74"), "logic IC"),
    (("cd4", "hef4", "mc14"), "logic IC (CMOS)"),
    # Communication
    (("max232", "max3232", "sp3232"), "RS-232 transceiver"),
    (("max485", "max3485", "sn65hvd", "thvd1", "isl317"), "RS-485 transceiver"),
    (("mcp2515", "mcp2551", "mcp2562", "sn65hvd23", "tja1"), "CAN transceiver"),
    (("cp2102", "ch340", "ft232", "ft2232", "pl2303", "ch9102"), "USB-UART bridge"),
    (("usb3300", "usb3320", "usb2514", "tusb"), "USB IC"),
    (("lan87", "lan91", "lan8720", "lan8710", "ksz", "dp83", "rtl81", "ip101"), "Ethernet PHY"),
    (("w5500", "w5100", "enc28j60"), "Ethernet controller"),
    (("sx127", "sx126", "rfm9", "rfm6", "cc1101", "at86rf"), "radio transceiver"),
    # Audio
    (("max9", "ssm2", "tpa", "lm386", "tda", "pam8"), "audio amplifier"),
    (("wm8", "es8", "ak4", "pcm51", "pcm17", "cs42", "sgtl5", "tlv320"), "audio codec"),
    # Display / LED
    (("ssd1306", "ssd1309", "st7735", "st7789", "ili9", "hx8357",
          "uc1701", "nt35", "sharp_ls"), "display controller"),
    (("ws2812", "sk6812", "apa102", "ws2813", "ws2815"), "addressable LED"),
    (("pca9685", "tlc5940", "is31fl"), "LED driver IC"),
    # Sensors
    (("bme280", "bme680", "bmp280", "bmp390"), "environmental sensor"),
    (("mpu6", "mpu9", "icm20", "lsm6", "bno0", "lis3"), "IMU/motion sensor"),
    (("ina21", "ina22", "ina23", "ina18", "ina19"), "current sense amplifier"),
    (("ads1", "mcp33", "mcp34", "mcp35", "max114", "max119"), "ADC"),
    (("mcp47", "dac8", "ad56", "ad57"), "DAC"),
    # Power management
    (("bq24", "bq25", "bq40", "ltc40", "mcp738"), "battery management"),
    (("tps20", "tps21", "ap22"), "power switch/load switch"),
    # Miscellaneous
    (("drv8", "a4988", "tmc2", "tmc5"), "motor driver"),
    (("esd", "prtr", "usblc", "tpd", "pesd", "sp05"), "ESD protection"),
    (("ds1307", "ds3231", "pcf8523", "rv3028", "rv8803"), "RTC"),
    (("at24c", "24lc", "24aa", "m24c", "cat24"), "EEPROM"),
    (("w25q", "at25", "mx25", "gd25", "is25", "sst26"), "SPI flash"),
]


_IC_DESC_KEYWORDS = [
    ("microcontroller", "microcontroller"),
    ("mcu", "microcontroller"),
    ("fpga", "FPGA"),
    ("cpld", "CPLD"),
    ("voltage regulator", "voltage regulator"),
    ("ldo", "linear regulator"),
    ("buck converter", "switching regulator"),
    ("boost converter", "switching regulator"),
    ("dc-dc", "DC-DC converter"),
    ("operational amplifier", "operational amplifier"),
    ("op-amp", "operational amplifier"),
    ("opamp", "operational amplifier"),
    ("comparator", "comparator"),
    ("adc", "ADC"),
    ("dac", "DAC"),
    ("uart", "UART interface"),
    ("usart", "UART interface"),
    ("spi", "SPI interface"),
    ("i2c", "I2C interface"),
    ("can transceiver", "CAN transceiver"),
    ("rs-485", "RS-485 transceiver"),
    ("rs-232", "RS-232 transceiver"),
    ("ethernet", "Ethernet IC"),
    ("usb", "USB IC"),
    ("motor driver", "motor driver"),
    ("gate driver", "gate driver"),
    ("led driver", "LED driver"),
    ("audio", "audio IC"),
    ("codec", "audio codec"),
    ("sensor", "sensor IC"),
    ("eeprom", "EEPROM"),
    ("flash", "flash memory"),
    ("shift register", "shift register"),
    ("multiplexer", "multiplexer"),
    ("level shift", "level shifter"),
    ("voltage reference", "voltage reference"),
    ("timer", "timer IC"),
    ("rtc", "RTC"),
    ("real-time clock", "RTC"),
    ("power supervisor", "voltage supervisor"),
    ("watchdog", "watchdog timer"),
    ("battery", "battery management"),
    ("charger", "battery charger"),
    ("rf", "RF IC"),
]


def classify_ic_pinout_role(lib_id: str, value: str, description: str) -> str:
    """Classify IC function from library ID, value, and description.

    Returns the free-form label serialised as ic_pin_analysis[].function
    ("linear regulator", "microcontroller", ...). Disjoint from
    kicad_core.classify.classify_ic_function, which returns a fixed enum.

    Three-tier lookup:
    1. KiCad stdlib library prefix (most reliable)
    2. Value/part number keyword matching
    3. Description keyword fallback
    """
    lib_lower = lib_id.lower()
    val_lower = value.lower()
    desc_lower = description.lower()

    # Skip connectors — they're analyzed for pinout but not for IC function
    lib_prefix = lib_lower.split(":")[0] if ":" in lib_lower else ""
    if lib_prefix.startswith("connector"):
        return ""

    # Tier 1: KiCad standard library prefix mapping
    for prefix, func in _IC_LIB_PREFIX_MAP.items():
        if lib_prefix == prefix or lib_lower.startswith(prefix + ":"):
            return func

    # Tier 2: Value / part number keyword matching
    for keywords, func in _IC_VALUE_KEYWORDS:
        if any(val_lower.startswith(k) for k in keywords):
            return func

    # Also check lib_id part name (after colon)
    lib_part = lib_lower.split(":")[-1] if ":" in lib_lower else ""
    if lib_part:
        for keywords, func in _IC_VALUE_KEYWORDS:
            if any(lib_part.startswith(k) for k in keywords):
                return func

    # Tier 3: Description keyword fallback
    for keyword, func in _IC_DESC_KEYWORDS:
        if keyword in desc_lower:
            return func

    return ""


def analyze_ic_pinouts(ctx: AnalysisContext,
                       target_types: set[str] | None = None) -> list[dict]:
    """Analyze each IC's pinout for datasheet cross-referencing.

    For every IC, produces a detailed per-pin analysis showing:
    - What net each pin connects to
    - What other components are on that net (with their values)
    - Whether power pins have decoupling capacitors
    - Whether input pins have pull-up/pull-down resistors
    - Pins that are unconnected (and whether they should be)
    """
    EPSILON = COORD_EPSILON
    components = ctx.components
    nets = ctx.nets
    pin_net = ctx.pin_net
    no_connects = ctx.no_connects
    comp_lookup = ctx.comp_lookup

    # Build no-connect position set
    nc_positions = set()
    for nc in no_connects:
        nc_positions.add((nc.get("_sheet", 0),
                          round(nc["x"] / EPSILON) * EPSILON,
                          round(nc["y"] / EPSILON) * EPSILON))

    results = []

    # Analyze ICs and other complex components (connectors, crystals, oscillators, etc.).
    # target_types is parameterised so the same code path can build a parallel
    # transistor_pin_analysis[] (F4) — verifying gate/source/drain wiring on
    # half-bridges is one of the highest-value review tasks and previously
    # required reconstructing the pin map from nets[].pins[] by hand.
    if target_types is None:
        target_types = {"ic", "connector", "crystal", "oscillator"}
    target_components = [c for c in components if c["type"] in target_types]

    for ic in target_components:
        ref = ic["reference"]
        pin_analysis = []
        decap_summary = {}  # net_name -> list of capacitor refs
        unconnected = []
        power_pins_detail = []
        signal_pins_detail = []

        for pin in ic.get("pins", []):
            # Ensure pin number and name are never null in output
            pin_number = pin.get("number") or ""
            pin_name = pin.get("name") or ""
            if not pin_number:
                # Fallback: use pin UUID if available, otherwise "unknown"
                pin_number = ic.get("pin_uuids", {}).get("", "unknown") if not pin_number else pin_number
                if not pin_number or pin_number == "unknown":
                    pin_number = f"unknown_{pin.get('x', 0):.0f}_{pin.get('y', 0):.0f}"

            pin_key = (ref, pin_number)
            net_name, net_info = pin_net.get(pin_key, (None, None))

            # Check if pin has a no-connect marker (by position, net flag, or
            # library-defined NC pin type).
            pin_pos = (ic.get("_sheet", 0),
                       round(pin["x"] / EPSILON) * EPSILON,
                       round(pin["y"] / EPSILON) * EPSILON)
            # The net-level no_connect flag is set when *any* point in a net's
            # union-find group is an NC marker (extract_nets line ~1490). On a
            # genuinely-connected multi-pin net it must NOT mark every pin as
            # NO_CONNECT — e.g. a stray NC marker absorbed into VBUS/GND would
            # otherwise flip all of that rail's IC pins to NO_CONNECT. Only honor
            # the net flag for single-pin nets, which covers the real case where
            # the marker sits on a short wire stub rather than exactly on the pin.
            net_pin_count = len(net_info.get("pins", [])) if net_info else 0
            has_no_connect = (
                pin_pos in nc_positions
                or pin.get("type") in ("no_connect", "unconnected")
                or bool(net_info and net_info.get("no_connect") and net_pin_count <= 1)
            )

            # Get components sharing this net
            neighbors = []
            neighbor_summary = []
            if net_info:
                neighbors = get_net_neighbors(net_info, ref)
                for nb in neighbors:
                    nb_comp = comp_lookup.get(nb["component"])
                    if nb_comp:
                        neighbor_summary.append({
                            "ref": nb["component"],
                            "value": nb_comp.get("value", ""),
                            "type": nb_comp.get("type", ""),
                            "pin": nb["pin_number"],
                            "pin_name": nb["pin_name"],
                        })

            # Classify what's connected
            connected_caps = [n for n in neighbor_summary if n["type"] == "capacitor"]
            connected_resistors = [n for n in neighbor_summary if n["type"] == "resistor"]
            connected_inductors = [n for n in neighbor_summary if n["type"] == "inductor"]

            pin_entry = {
                "pin_number": pin_number,
                "pin_name": pin_name,
                "pin_type": pin["type"],
                "net": "NO_CONNECT" if has_no_connect else (net_name or "UNCONNECTED"),
                "connected_to": neighbor_summary,
            }

            # Determine if this is functionally a power pin based on type OR net name.
            # Many lib symbols mark power pins as "input" or "passive", so also check
            # if the net is a known power rail.
            is_power_pin = pin["type"] in ("power_in", "power_out")
            if not is_power_pin and net_name:
                # Check net name against common power rail patterns
                net_upper = net_name.upper()
                is_power_pin = (
                    net_upper in ("GND", "VSS", "AGND", "DGND", "PGND",
                                  "VCC", "VDD", "AVCC", "AVDD", "DVCC", "DVDD",
                                  "VBUS", "V_USB")
                    or net_upper.startswith("+")
                    or net_upper.startswith("V+")
                )
            # Also check pin name for power pin hints
            if not is_power_pin and pin["name"]:
                pname = pin["name"].upper()
                is_power_pin = pname in (
                    "VCC", "VDD", "VSS", "GND", "AVCC", "AVDD", "DVCC", "DVDD",
                    "VIN", "VOUT", "PGND", "AGND", "DGND", "VBUS",
                )

            if is_power_pin:
                # For decoupling cap detection, only list caps directly on THIS net
                # (not the entire GND net which connects everything)
                net_is_ground = net_name and net_name.upper() in (
                    "GND", "VSS", "AGND", "DGND", "PGND")
                if net_is_ground:
                    # Don't list decoupling caps for ground pins — they're shared globally
                    pin_entry["has_decoupling_cap"] = True  # ground is always decoupled
                    pin_entry["decoupling_caps"] = []
                    pin_entry["note"] = "Ground net — decoupling caps listed on VCC/VDD pins"
                else:
                    pin_entry["has_decoupling_cap"] = len(connected_caps) > 0
                    pin_entry["decoupling_caps"] = [
                        {"ref": c["ref"], "value": c["value"]} for c in connected_caps
                    ]
                    if net_name and connected_caps:
                        decap_summary.setdefault(net_name, []).extend(
                            {"ref": c["ref"], "value": c["value"]} for c in connected_caps
                        )
                power_pins_detail.append(pin_entry)

            elif pin["type"] in ("input", "bidirectional", "open_collector", "open_emitter"):
                # Check for pull-up/pull-down resistors
                pull_resistors = []
                for r in connected_resistors:
                    r_comp = comp_lookup.get(r["ref"])
                    if r_comp:
                        # Check where the other end of the resistor goes
                        other_pin = "1" if r["pin"] == "2" else "2"
                        other_key = (r["ref"], other_pin)
                        other_net, _ = pin_net.get(other_key, (None, None))
                        if other_net in ("GND", "VSS"):
                            pull_resistors.append({
                                "ref": r["ref"], "value": r_comp["value"],
                                "direction": "pull-down", "to_net": other_net,
                            })
                        elif other_net and any(kw in other_net.upper()
                                               for kw in ("VCC", "VDD", "+3", "+5", "VBUS")):
                            pull_resistors.append({
                                "ref": r["ref"], "value": r_comp["value"],
                                "direction": "pull-up", "to_net": other_net,
                            })
                        else:
                            pull_resistors.append({
                                "ref": r["ref"], "value": r_comp["value"],
                                "direction": "series", "to_net": other_net,
                            })
                if pull_resistors:
                    pin_entry["resistors"] = pull_resistors
                signal_pins_detail.append(pin_entry)

            else:
                signal_pins_detail.append(pin_entry)

            if not net_name and not has_no_connect:
                unconnected.append(pin_entry)

            pin_analysis.append(pin_entry)

        # Deduplicate decoupling caps per net
        unique_decaps = {}
        for net_name, caps in decap_summary.items():
            seen = set()
            unique = []
            for c in caps:
                if c["ref"] not in seen:
                    seen.add(c["ref"])
                    unique.append(c)
            unique_decaps[net_name] = unique

        # Build IC analysis summary
        ic_result = {
            "reference": ref,
            "value": ic["value"],
            "type": ic["type"],
            "lib_id": ic["lib_id"],
            "mpn": ic.get("mpn", ""),
            "description": ic.get("description", ""),
            "datasheet": ic.get("datasheet", ""),
            "function": classify_ic_pinout_role(ic["lib_id"], ic["value"], ic.get("description", "")),
            "total_pins": len(pin_analysis),
            "unconnected_pins": len(unconnected),
            "pins": sorted(pin_analysis, key=lambda p: _pin_sort_key(p["pin_number"])),
            "power_pins": power_pins_detail,
            "signal_pins": signal_pins_detail,
            "decoupling_caps_by_rail": unique_decaps,
        }

        if unconnected:
            ic_result["unconnected_pin_list"] = unconnected

        results.append(ic_result)

    return results


def _pin_sort_key(pin_num: str):
    """Sort pin numbers numerically when possible, alphabetically otherwise."""
    try:
        return (0, int(pin_num))
    except ValueError:
        return (1, pin_num)


def identify_subcircuits(ctx: AnalysisContext) -> list[dict]:
    """Identify potential subcircuit groupings around ICs."""
    components = ctx.components
    nets = ctx.nets
    pin_net = ctx.pin_net
    comp_lookup = ctx.comp_lookup
    is_power_net = ctx.is_power_net
    is_ground = ctx.is_ground
    subcircuits = []

    ics = [c for c in components if c["type"] == "ic"]

    for ic in ics:
        ref = ic["reference"]

        # Find all nets this IC connects to
        ic_nets = set()
        for pin in ic.get("pins", []):
            net_name, _ = pin_net.get((ref, pin["number"]), (None, None))
            if net_name:
                ic_nets.add(net_name)

        # Find all components that share nets with this IC (1-hop neighbors)
        # Skip power/ground nets — every IC shares VCC/GND, inflating neighbors
        neighbors = set()
        for net_name in ic_nets:
            if is_power_net(net_name) or is_ground(net_name):
                continue
            if net_name in nets:
                for p in nets[net_name]["pins"]:
                    r = p["component"]
                    if r != ref and not r.startswith("#"):
                        neighbors.add(r)

        # Build neighbor details with values
        neighbor_details = []
        for nb_ref in sorted(neighbors):
            nb_comp = comp_lookup.get(nb_ref)
            if nb_comp:
                neighbor_details.append({
                    "ref": nb_ref,
                    "value": nb_comp.get("value", ""),
                    "type": nb_comp.get("type", ""),
                })

        subcircuits.append({
            "center_ic": ref,
            "ic_value": ic["value"],
            "ic_mpn": ic.get("mpn", ""),
            "ic_lib_id": ic["lib_id"],
            "neighbor_components": neighbor_details,
            "description": ic.get("description", ""),
        })

    return subcircuits
