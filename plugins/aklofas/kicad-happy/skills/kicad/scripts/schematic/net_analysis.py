"""Connectivity, power-domain, cross-domain, bus-protocol and differential-pair analyses: verbatim move from analyze_schematic.py; no behaviour change."""
from __future__ import annotations

import re
from kicad_types import (
    AnalysisContext,
)
from kicad_core.values import (
    COORD_EPSILON,
)
from kicad_core.parts import (
    _OUTPUT_DRIVE_KEYWORDS,
)
from kicad_core.netnames import (
    parse_voltage_from_net_name as _parse_voltage_from_net_name,
    is_usb_data_net_name,
)


def analyze_connectivity(components: list[dict], nets: dict, no_connects: list[dict]) -> dict:
    """Analyze the connectivity graph for potential issues.

    Returns a dict with:
    - unconnected_pins: pins not on any net (and not marked no-connect)
    - single_pin_nets: nets with only one pin (likely unfinished connections)
    - multi_driver_nets: nets with multiple output/bidirectional drivers
    - power_net_summary: per power rail, which components connect
    """
    EPSILON = COORD_EPSILON

    # Build set of no-connect positions for quick lookup
    nc_positions = set()
    for nc in no_connects:
        nc_positions.add((nc.get("_sheet", 0),
                          round(nc["x"] / EPSILON) * EPSILON,
                          round(nc["y"] / EPSILON) * EPSILON))

    # Build set of all pins that appear in any net
    connected_pins = set()
    for net_info in nets.values():
        for p in net_info["pins"]:
            connected_pins.add((p["component"], p["pin_number"]))

    # Find unconnected pins
    unconnected_pins = []
    for comp in components:
        if comp["type"] in ("power_symbol", "power_flag", "flag"):
            continue
        for pin in comp.get("pins", []):
            pin_key = (comp["reference"], pin["number"])
            if pin_key not in connected_pins:
                # Check if there's a no-connect marker at this pin
                pin_pos = (comp.get("_sheet", 0),
                           round(pin["x"] / EPSILON) * EPSILON,
                           round(pin["y"] / EPSILON) * EPSILON)
                if pin_pos not in nc_positions:
                    unconnected_pins.append({
                        "component": comp["reference"],
                        "pin_number": pin["number"],
                        "pin_name": pin["name"],
                        "pin_type": pin["type"],
                    })

    # Find single-pin nets. Pin type determines severity — a floating
    # power_in / input / bidirectional pin is a real wiring bug, while a
    # lonely passive leg is usually mid-edit, and a no_connect pin is
    # documentation. Unnamed nets (__unnamed_N) count when the pin type
    # warrants it — KiCad lets users rely on the auto-generated name
    # for boot caps and flying caps that genuinely shouldn't be labelled.
    _SIGNAL_PIN_TYPES = {"power_in", "input", "bidirectional",
                         "output", "tri_state", "open_collector",
                         "open_emitter"}
    _SKIP_PIN_TYPES = {"no_connect", "free", "unspecified", "unconnected"}
    single_pin_nets = []
    single_pin_net_findings: list[dict] = []
    for net_name, net_info in nets.items():
        if len(net_info["pins"]) != 1 or net_info.get("no_connect"):
            continue
        pin = net_info["pins"][0]
        pin_type = (pin.get("pin_type") or "").lower()
        if pin_type in _SKIP_PIN_TYPES:
            continue
        # Retain the legacy summary shape for downstream consumers —
        # keep the pre-existing __unnamed_* guard on the legacy list so
        # format-report / diff_analysis don't surface mid-edit passive
        # stubs that the old code filtered out. The rich NT-001 finding
        # below still covers those cases for reviewers who want them.
        if not net_name.startswith("__unnamed_"):
            single_pin_nets.append({"net": net_name, "pin": pin})
        # Emit a weighted finding.
        if pin_type in _SIGNAL_PIN_TYPES:
            severity = "warning"
            impact = ("Likely unfinished wiring: a driven or powered pin "
                      "has no counterpart.")
        elif pin_type == "power_out":
            severity = "info"
            impact = ("Power source with no declared load — acceptable if "
                      "loads are on another sheet, otherwise suspicious.")
        else:
            severity = "info"
            impact = "Passive or unclassified pin lonely on its own net."
        display_ref = pin.get("component", "?")
        display_num = pin.get("pin_number", "?")
        display_name = pin.get("pin_name") or ""
        display_label = (f"{display_ref}.{display_num}"
                         + (f" ({display_name})" if display_name else ""))
        net_display = (f"{display_ref}.{display_name}"
                       if net_name.startswith("__unnamed_") and display_name
                       else net_name)
        single_pin_net_findings.append({
            "detector": "analyze_connectivity",
            "rule_id": "NT-001",
            "severity": severity,
            "confidence": "deterministic",
            "evidence_source": "topology",
            "category": "connectivity",
            "summary": (f"Single-pin net: {net_display} only connects to "
                        f"{display_label} ({pin_type or 'unknown'})"),
            "description": (f"Net {net_name!r} has exactly one pin: "
                            f"{display_label}, pin_type={pin_type!r}. "
                            "Verify the intended target — if this pin "
                            "should connect somewhere, the wire/label is "
                            "missing."),
            "components": [display_ref] if display_ref else [],
            "nets": [net_name],
            "pins": [f"{display_ref}.{display_num}"],
            "net_display_name": net_display,
            "pin_type": pin_type,
            "pin_name": display_name,
            "recommendation": (
                "Check the schematic at the referenced pin — add the "
                "missing wire or place a no-connect marker if the pin is "
                "intentionally floating."),
            "report_context": {
                "section": "Connectivity",
                "impact": impact,
                "standard_ref": "",
            },
        })

    # Find multi-driver nets (multiple outputs driving the same net)
    # Exclude power flags (#FLG, #PWR) — they're virtual, not real drivers
    multi_driver_nets = []
    output_types = {"output", "tri_state", "power_out"}
    for net_name, net_info in nets.items():
        drivers = [p for p in net_info["pins"]
                   if p["pin_type"] in output_types
                   and not p["component"].startswith("#")]
        if len(drivers) > 1:
            multi_driver_nets.append({
                "net": net_name,
                "drivers": drivers,
            })

    # Power net summary — for each named power rail, which real components connect
    power_net_summary = {}
    for net_name, net_info in nets.items():
        if net_name.startswith("__unnamed_"):
            continue
        is_power = any(p["pin_type"] in ("power_in", "power_out") for p in net_info["pins"])
        if is_power or net_name in ("GND", "VCC", "VDD", "+3V3", "+3.3V", "+5V", "+12V", "VBUS"):
            real_components = sorted(set(
                p["component"] for p in net_info["pins"]
                if not p["component"].startswith("#")
            ))
            power_net_summary[net_name] = {
                "pin_count": len([p for p in net_info["pins"] if not p["component"].startswith("#")]),
                "components": real_components,
            }

    return {
        "unconnected_pins": unconnected_pins,
        "single_pin_nets": single_pin_nets,
        "single_pin_net_findings": single_pin_net_findings,
        "multi_driver_nets": multi_driver_nets,
        "power_net_summary": power_net_summary,
    }


def _classify_nets(ctx: AnalysisContext) -> dict:
    """Classify all nets by type (ground, power, clock, data, etc.)."""
    nets = ctx.nets
    is_ground = ctx.is_ground
    is_power_net = ctx.is_power_net

    net_classes = {}
    for net_name, net_info in nets.items():
        if net_name.startswith("__unnamed_"):
            # Classify unnamed nets by pin types
            pin_types = set(p["pin_type"] for p in net_info["pins"])
            has_power = bool(pin_types & {"power_in", "power_out"})
            if has_power:
                net_classes[net_name] = "power_internal"
            else:
                net_classes[net_name] = "signal"
            continue

        nu = net_name.upper()
        if is_ground(net_name):
            net_classes[net_name] = "ground"
        elif is_power_net(net_name):
            net_classes[net_name] = "power"
        elif any(kw in nu for kw in ("SCL", "SCK", "CLK", "MCLK", "SCLK", "XTAL", "OSC")):
            net_classes[net_name] = "clock"
        elif any(kw in nu for kw in ("SDA", "MOSI", "MISO", "SDI", "SDO", "UART", "TX", "RX")):
            net_classes[net_name] = "data"
        elif any(kw in nu for kw in ("USB", "CAN", "LVDS", "ETH")):
            net_classes[net_name] = "high_speed"
        elif any(kw in nu for kw in ("ADC", "AIN", "VREF", "VSENSE", "ISENSE")):
            net_classes[net_name] = "analog"
        elif any(kw in nu for kw in ("RESET", "NRST", "RST", "EN", "ENABLE")):
            net_classes[net_name] = "control"
        elif any(kw in nu for kw in ("CS", "SS", "NSS", "CE", "SEL")):
            # KH-097: Exclude video sync signals (CSYNC, HSYNC, VSYNC)
            if any(sync in nu for sync in ("CSYNC", "HSYNC", "VSYNC", "SYNC")):
                net_classes[net_name] = "signal"
            else:
                net_classes[net_name] = "chip_select"
        elif any(kw in nu for kw in ("INT", "IRQ", "ALERT", "DRDY")):
            net_classes[net_name] = "interrupt"
        elif any(kw in nu for kw in _OUTPUT_DRIVE_KEYWORDS):
            net_classes[net_name] = "output_drive"
        elif any(kw in nu for kw in ("SWD", "SWCLK", "SWDIO", "SWO", "JTAG", "TCK", "TMS", "TDI", "TDO")):
            net_classes[net_name] = "debug"
        elif any(kw in nu for kw in ("BOOT", "TEST")):
            net_classes[net_name] = "config"
        else:
            net_classes[net_name] = "signal"

    return net_classes


def _map_power_domains(ctx: AnalysisContext) -> dict:
    """Map each IC to its power domains.

    For each IC, determine which power rails it connects to.
    Track IO-level reference pins (VDDIO, VIO) separately from internal supplies
    (VCC, VDD) -- for cross-domain analysis, the IO rail determines signal levels.
    """
    components = ctx.components
    pin_net = ctx.pin_net
    known_power_rails = ctx.known_power_rails
    is_ground = ctx.is_ground
    is_power_net = ctx.is_power_net

    _io_pin_names = {"VDDIO", "VIO", "VCCA", "VCCB", "VREF", "VLOGIC",
                     "DVDD", "DVCC", "IOVDD", "IOVCC"}
    _sense_pin_names = {"IN+", "IN-", "INP", "INN", "SENSE", "VSENSE", "SNS",
                        "CSP", "CSN", "CS+", "CS-", "ISENSE", "IMON", "IOUT",
                        "SEN", "VS+", "VS-"}
    power_domains = {}
    # KH-224: Accumulate rails/io_rails across all units of multi-unit ICs
    _ref_rails: dict[str, set] = {}      # ref -> set of power rail nets
    _ref_io_rails: dict[str, set] = {}   # ref -> set of IO rail nets
    _ref_value: dict[str, str] = {}      # ref -> value (from first unit seen)
    ics = [c for c in components if c["type"] == "ic"]
    for ic in ics:
        ref = ic["reference"]
        if ref not in _ref_value:
            _ref_value[ref] = ic["value"]
        rails = _ref_rails.setdefault(ref, set())
        io_rails = _ref_io_rails.setdefault(ref, set())
        for pin in ic.get("pins", []):
            net_name, _ = pin_net.get((ref, pin["number"]), (None, None))
            if not net_name:
                continue
            pname_upper = pin["name"].upper()
            if pname_upper in _sense_pin_names:
                continue
            is_pwr = is_power_net(net_name) and not is_ground(net_name)
            is_named_pwr = pname_upper in ("VCC", "VDD", "AVCC", "AVDD", "VBUS",
                                           "VIN", "VOUT", "VDDIO", "VIO", "VCCA",
                                           "VCCB", "VREF", "VLOGIC", "DVDD", "DVCC",
                                           "IOVDD", "IOVCC", "VCCREG", "VREG")
            if is_pwr or is_named_pwr:
                rails.add(net_name)
                if pname_upper in _io_pin_names:
                    io_rails.add(net_name)
    for ref, rails in _ref_rails.items():
        if rails:
            io_rails = _ref_io_rails.get(ref, set())
            power_domains[ref] = {
                "value": _ref_value[ref],
                "power_rails": sorted(rails),
                "io_rails": sorted(io_rails) if io_rails else None,
            }

    # Fallback for legacy files where pin_net may be incomplete:
    # Match IC power pin NAMES (VCC, VDD, etc.) against known_power_rails by string.
    _pwr_pin_to_rail = {"VCC", "VDD", "AVCC", "AVDD", "DVCC", "DVDD",
                        "VDDIO", "VIO", "VCCA", "VCCB", "VBUS"}
    _fallback_rails: dict[str, set] = {}   # ref -> set of rails (aggregate across units)
    _fallback_value: dict[str, str] = {}
    for ic in ics:
        ref = ic["reference"]
        if ref in power_domains:
            continue
        if ref not in _fallback_value:
            _fallback_value[ref] = ic["value"]
        rails = _fallback_rails.setdefault(ref, set())
        for pin in ic.get("pins", []):
            pname = pin.get("name", "").upper()
            if pname not in _pwr_pin_to_rail:
                continue
            # Find a known power rail whose name matches this pin name
            for rail in known_power_rails:
                ru = rail.upper()
                if pname == ru or pname in ru or ru.startswith(pname):
                    rails.add(rail)
    for ref, rails in _fallback_rails.items():
        if rails:
            power_domains[ref] = {
                "value": _fallback_value[ref],
                "power_rails": sorted(rails),
                "io_rails": None,
                "_inferred_from": "pin_name_match",
            }

    # Group ICs by power domain
    domain_groups = {}
    for ref, info in power_domains.items():
        for rail in info["power_rails"]:
            domain_groups.setdefault(rail, []).append(ref)

    return {"ic_power_rails": power_domains, "domain_groups": domain_groups}


def _get_power_domains_for_refs(refs: set, power_domains: dict,
                                is_ground) -> set:
    """Get all power rail domains for a set of IC references."""
    domains = set()
    for r in refs:
        for rail in power_domains.get(r, {}).get("power_rails", []):
            if not is_ground(rail):
                domains.add(rail)
    return domains


def _get_io_domains_for_refs(refs: set, power_domains: dict,
                             is_ground) -> set:
    """Get I/O-level domains for cross-domain comparison.

    When an IC has a dedicated IO-level pin (VDDIO, VIO, etc.),
    use that rail for signal-level comparison instead of all power
    rails.  This avoids false positives where internal supplies
    (VCC charge pump, analog VDD) differ but the actual I/O
    voltage matches the other IC.
    """
    domains = set()
    for r in refs:
        info = power_domains.get(r, {})
        io = info.get("io_rails")
        if io:
            for rail in io:
                domains.add(rail)
        else:
            # No dedicated IO pin -- use all power rails
            for rail in info.get("power_rails", []):
                if not is_ground(rail):
                    domains.add(rail)
    return domains


def _rails_voltage_compatible(rails_a: set, rails_b: set) -> bool:
    """Check if two sets of rails share a rail or voltage."""
    if rails_a & rails_b:
        return True
    # Parse voltages from net names and check overlap
    va = {_parse_voltage_from_net_name(r) for r in rails_a} - {None}
    vb = {_parse_voltage_from_net_name(r) for r in rails_b} - {None}
    return bool(va & vb)


def _detect_cross_domain_signals(ctx: AnalysisContext, power_domains: dict,
                                 results_in: dict | None = None) -> list:
    """Find signals crossing between different power domains."""
    components = ctx.components
    nets = ctx.nets
    is_ground = ctx.is_ground
    is_power_net = ctx.is_power_net

    if results_in is None:
        results_in = {}

    cross_domain = []
    # Build set of ESD protection IC references for cross-domain filtering
    esd_ic_refs = set()
    for pd in results_in.get("protection_devices", []):
        if pd.get("type") == "esd_ic":
            esd_ic_refs.add(pd["ref"])

    # Detect level translator ICs -- these bridge domains intentionally so
    # signals through them don't need additional level shifting.
    level_translator_keywords = (
        "leveltranslator", "level_translator", "levelshift", "level_shift",
        "txb0", "txs0", "tca9", "lsf0", "sn74lvc", "sn74avc",
        "sn74cb3", "sn74cbt", "nlsx", "nts0", "fxl", "adg320",
        "max395", "gtl2", "pca960", "tca641",
    )
    level_translator_desc_keywords = (
        "level translator", "level shifter", "level-shifting",
        "voltage translator", "voltage level",
    )
    level_translator_refs = set()
    for ic in components:
        if ic["type"] != "ic":
            continue
        val_low = ic.get("value", "").lower()
        lib_low = ic.get("lib_id", "").lower()
        desc_low = ic.get("description", "").lower()
        kw_low = ic.get("keywords", "").lower()
        if (any(k in val_low or k in lib_low for k in level_translator_keywords) or
                any(k in desc_low or k in kw_low for k in level_translator_desc_keywords)):
            level_translator_refs.add(ic["reference"])
    for net_name, net_info in nets.items():
        if is_power_net(net_name) or is_ground(net_name):
            continue
        # Find all ICs on this net
        ic_refs = set()
        for p in net_info["pins"]:
            if p["component"] in power_domains and not p["component"].startswith("#"):
                ic_refs.add(p["component"])
        if len(ic_refs) < 2:
            continue

        # Check if they're on different power domains
        domains_on_net = _get_power_domains_for_refs(ic_refs, power_domains, is_ground)
        if len(domains_on_net) > 1:
            # Don't flag as needing level shifter when the only cross-domain
            # connection is through an ESD/protection IC -- those clamp voltage
            # but don't change signal levels (e.g., USBLC6 on USB D+/D-)
            non_esd_refs = ic_refs - esd_ic_refs
            non_esd_domains = _get_power_domains_for_refs(non_esd_refs, power_domains, is_ground)

            # Check if a level translator is on this net -- if so, it already
            # handles the voltage translation
            translators_on_net = ic_refs & level_translator_refs
            has_translator = len(translators_on_net) > 0

            if len(non_esd_domains) > 1:
                if has_translator:
                    # Level translator present -- shifting is handled
                    needs_shifter = False
                else:
                    # Use IO-level domains for the level shifter decision.
                    # Check pairwise: every pair of ICs must share at least one
                    # common IO rail. A multi-rail SoC (e.g., +3.3V + VDDA)
                    # connecting to a simple IC on +3.3V shares +3.3V, so no
                    # level shifter is needed despite different rail counts.
                    # Also treat rails at the same voltage as equivalent (e.g.,
                    # +3V3 and VCC_3V3 are both 3.3V).
                    functional_refs = non_esd_refs - level_translator_refs
                    ic_list = sorted(functional_refs) if functional_refs else sorted(non_esd_refs)
                    needs_shifter = False
                    for i_idx in range(len(ic_list)):
                        for j_idx in range(i_idx + 1, len(ic_list)):
                            a_io = _get_io_domains_for_refs({ic_list[i_idx]}, power_domains, is_ground)
                            b_io = _get_io_domains_for_refs({ic_list[j_idx]}, power_domains, is_ground)
                            if not _rails_voltage_compatible(a_io, b_io):
                                needs_shifter = True
                                break
                        if needs_shifter:
                            break
            else:
                needs_shifter = False
            entry = {
                "net": net_name,
                "ics": sorted(ic_refs),
                "power_domains": sorted(domains_on_net),
                "needs_level_shifter": needs_shifter,
            }
            if has_translator:
                entry["level_translators"] = sorted(translators_on_net)
            cross_domain.append(entry)

    return cross_domain


def _enrich_device_ref(ref: str, comp_lookup: dict) -> dict:
    """Convert a bare component reference to {ref, value, lib_id} dict."""
    comp = comp_lookup.get(ref, {})
    return {
        "ref": ref,
        "value": comp.get("value", ""),
        "lib_id": comp.get("lib_id", ""),
    }


def _detect_i2c_buses(ctx: AnalysisContext) -> list[dict]:
    """Detect I2C buses by net name and pin name matching."""
    nets = ctx.nets
    pin_net = ctx.pin_net
    comp_lookup = ctx.comp_lookup
    parsed_values = ctx.parsed_values
    is_ground = ctx.is_ground
    is_power_net = ctx.is_power_net

    results = []

    # Look for SDA/SCL net pairs by net name
    i2c_nets = {}
    for net_name in nets:
        nu = net_name.upper()
        if "SDA" in nu or "SCL" in nu or "I2C" in nu:
            # Skip SPI signals (MISO contains no I2C keywords, but SCLK/SCK match SCL)
            # Skip I2S signals (I2S0_RX_SDA etc. contain SDA as substring)
            # KH-086: Also exclude MOSI/MISO nets (SPI data lines on dual-function ICs)
            if "SCLK" in nu or nu.endswith("SCK") or "SPI" in nu or "MOSI" in nu or "MISO" in nu:
                continue
            if "I2S" in nu:
                continue
            bus_id = nu.replace("SDA", "").replace("SCL", "").replace("I2C", "").replace("_", "").strip()
            i2c_nets.setdefault(bus_id, {})[nu] = net_name

    # Generate I2C bus entries from net-name matches
    i2c_seen_nets = set()
    for bus_id, net_map in i2c_nets.items():
        for nu_key, net_name in net_map.items():
            if net_name in i2c_seen_nets:
                continue
            i2c_seen_nets.add(net_name)
            net_info = nets.get(net_name, {})
            line = "SDA" if "SDA" in nu_key else "SCL"
            device_refs = [p["component"] for p in net_info.get("pins", [])
                           if comp_lookup.get(p["component"], {}).get("type") == "ic"]
            devices = [_enrich_device_ref(r, comp_lookup) for r in device_refs]
            # Find pull-up resistors
            pullups = []
            for p in net_info.get("pins", []):
                comp = comp_lookup.get(p["component"])
                if comp and comp["type"] == "resistor":
                    r_val = parsed_values.get(p["component"])
                    if r_val:
                        other_pin = "1" if p["pin_number"] == "2" else "2"
                        other_net, _ = pin_net.get((p["component"], other_pin), (None, None))
                        if other_net and is_power_net(other_net) and not is_ground(other_net):
                            pullups.append({
                                "ref": p["component"],
                                "value": comp["value"],
                                "ohms": r_val,
                                "to_rail": other_net,
                            })
            if devices:  # Skip connector-only routing with no ICs
                load_count = len(devices)
                # Typical I2C input capacitance: ~5pF per device pin
                estimated_cin_pF = load_count * 5
                # Electrical parameters from pull-ups
                pu_ohms_list = [pu["ohms"] for pu in pullups if pu.get("ohms")]
                min_pu_ohms = min(pu_ohms_list) if pu_ohms_list else None
                if min_pu_ohms is not None:
                    if min_pu_ohms <= 500:
                        speed_mode = "high_speed"
                    elif min_pu_ohms <= 1500:
                        speed_mode = "fast_plus"
                    elif min_pu_ohms <= 4700:
                        speed_mode = "fast"
                    else:
                        speed_mode = "standard"
                else:
                    speed_mode = None
                # Voltage level from pull-up rail
                voltage_level = None
                for pu in pullups:
                    v = _estimate_rail_voltage(pu.get("to_rail", ""))
                    if v is not None:
                        voltage_level = v
                        break
                # Controller: MCU or FPGA on the bus
                controller = None
                for ref in device_refs:
                    fc = comp_lookup.get(ref, {}).get("functional_class", "")
                    if fc in ("mcu", "fpga"):
                        controller = ref
                        break
                results.append({
                    "net": net_name,
                    "line": line,
                    "devices": devices,
                    "load_count": load_count,
                    "estimated_bus_capacitance_pF": estimated_cin_pF,
                    "pull_ups": pullups,
                    "has_pull_up": len(pullups) > 0,
                    "speed_mode": speed_mode,
                    "voltage_level_V": voltage_level,
                    "pull_up_ohms": min_pu_ohms,
                    "controller": controller,
                })

    # Also detect I2C from pin names (for nets without SDA/SCL in their name)
    for net_name, net_info in nets.items():
        if net_name in i2c_seen_nets:
            continue  # Already found by net name
        # KH-086: Exclude SPI nets -- sensors with dual-function SDA/SCL pin names
        nn_upper = net_name.upper()
        if "SPI" in nn_upper or "MOSI" in nn_upper or "MISO" in nn_upper:
            continue
        sda_pins = [p for p in net_info["pins"]
                    if "SDA" in p.get("pin_name", "").upper()
                    and "I2S" not in p.get("pin_name", "").upper()]
        # Exclude SPI clock pins (SCLK, SCK) which contain "SCL" as substring
        # Exclude I2S pins which may contain SCL as substring
        scl_pins = [p for p in net_info["pins"]
                    if "SCL" in p.get("pin_name", "").upper()
                    and "SCLK" not in p.get("pin_name", "").upper()
                    and "I2S" not in p.get("pin_name", "").upper()
                    and p.get("pin_name", "").upper() not in ("SCK",)]
        if sda_pins or scl_pins:
            # Find pull-up resistors on this net
            pullups = []
            for p in net_info["pins"]:
                comp = comp_lookup.get(p["component"])
                if comp and comp["type"] == "resistor":
                    r_val = parsed_values.get(p["component"])
                    if r_val:
                        # Check if other end goes to a power rail
                        other_pin = "1" if p["pin_number"] == "2" else "2"
                        other_net, _ = pin_net.get((p["component"], other_pin), (None, None))
                        if other_net and is_power_net(other_net) and not is_ground(other_net):
                            pullups.append({
                                "ref": p["component"],
                                "value": comp["value"],
                                "ohms": r_val,
                                "to_rail": other_net,
                            })

            bus_type = "SDA" if sda_pins else "SCL"
            device_refs = [p["component"] for p in net_info["pins"]
                           if comp_lookup.get(p["component"], {}).get("type") == "ic"]
            devices = [_enrich_device_ref(r, comp_lookup) for r in device_refs]

            if devices:  # Skip connector-only routing with no ICs
                load_count = len(devices)
                # Electrical parameters from pull-ups
                pu_ohms_list = [pu["ohms"] for pu in pullups if pu.get("ohms")]
                min_pu_ohms = min(pu_ohms_list) if pu_ohms_list else None
                if min_pu_ohms is not None:
                    if min_pu_ohms <= 500:
                        speed_mode = "high_speed"
                    elif min_pu_ohms <= 1500:
                        speed_mode = "fast_plus"
                    elif min_pu_ohms <= 4700:
                        speed_mode = "fast"
                    else:
                        speed_mode = "standard"
                else:
                    speed_mode = None
                voltage_level = None
                for pu in pullups:
                    v = _estimate_rail_voltage(pu.get("to_rail", ""))
                    if v is not None:
                        voltage_level = v
                        break
                controller = None
                for ref in device_refs:
                    fc = comp_lookup.get(ref, {}).get("functional_class", "")
                    if fc in ("mcu", "fpga"):
                        controller = ref
                        break
                entry = {
                    "net": net_name,
                    "line": bus_type,
                    "devices": devices,
                    "load_count": load_count,
                    "estimated_bus_capacitance_pF": load_count * 5,
                    "pull_ups": pullups,
                    "has_pull_up": len(pullups) > 0,
                    "speed_mode": speed_mode,
                    "voltage_level_V": voltage_level,
                    "pull_up_ohms": min_pu_ohms,
                    "controller": controller,
                }

                # I2C rise time validation
                # EQ-097: t_r = 0.8473 * R_pullup * C_bus (RC time constant to 70% VDD)
                # I2C spec limits: Standard 1000ns, Fast 300ns, Fast+ 120ns, HS 50ns
                if entry.get("pull_ups") and entry.get("estimated_bus_capacitance_pF"):
                    pullup_ohms = [pu["ohms"] for pu in entry["pull_ups"] if pu.get("ohms")]
                    if pullup_ohms:
                        # Parallel combination if multiple pull-ups on same line
                        if len(pullup_ohms) == 1:
                            r_eff = pullup_ohms[0]
                        else:
                            r_eff = 1.0 / sum(1.0 / r for r in pullup_ohms)

                        c_bus_f = entry["estimated_bus_capacitance_pF"] * 1e-12
                        rise_time_ns = 0.8473 * r_eff * c_bus_f * 1e9

                        entry["rise_time_ns"] = round(rise_time_ns, 1)
                        entry["effective_pullup_ohms"] = round(r_eff, 1)

                        # Determine maximum supported speed mode
                        _I2C_MODES = [
                            ("HS",         50),
                            ("Fast-mode+", 120),
                            ("Fast-mode",  300),
                            ("Standard",  1000),
                        ]
                        max_mode = "Standard"
                        for mode_name, limit_ns in _I2C_MODES:
                            if rise_time_ns <= limit_ns:
                                max_mode = mode_name
                                break

                        entry["max_speed_mode"] = max_mode

                        # Warning if rise time is marginal (within 20% of limit)
                        for mode_name, limit_ns in _I2C_MODES:
                            if rise_time_ns <= limit_ns:
                                margin_pct = (limit_ns - rise_time_ns) / limit_ns * 100
                                if margin_pct < 20:
                                    entry["rise_time_warning"] = (
                                        f"Rise time {rise_time_ns:.0f}ns is within 20% of "
                                        f"{mode_name} limit ({limit_ns}ns) — "
                                        f"margin {margin_pct:.0f}%"
                                    )
                                break

                results.append(entry)

    return results


def _detect_spi_buses(ctx: AnalysisContext) -> list[dict]:
    """Detect SPI buses by MOSI/MISO/SCK/CS patterns (and newer COPI/CIPO/SDI/SDO)."""
    nets = ctx.nets
    comp_lookup = ctx.comp_lookup

    _spi_net_kw = ("MOSI", "MISO", "SCK", "SCLK", "COPI", "CIPO", "SDI", "SDO")
    _spi_canon = {  # normalize alternative names to canonical SPI signals
        "COPI": "MOSI", "SDO": "MOSI", "SDI": "MISO", "CIPO": "MISO",
        "SCLK": "SCK",
    }
    spi_signals = {}
    for net_name, net_info in nets.items():
        nu = net_name.upper()
        for kw in _spi_net_kw:
            if kw in nu:
                canon = _spi_canon.get(kw, kw)
                bus_id = nu.replace(kw, "").replace("_", "").strip() or "0"
                spi_signals.setdefault(bus_id, {})[canon] = {
                    "net": net_name,
                    "devices": [p["component"] for p in net_info["pins"]
                                if comp_lookup.get(p["component"], {}).get("type") == "ic"],
                }
        # Also check pin names
        for p in net_info["pins"]:
            pn = p.get("pin_name", "").upper()
            for kw in _spi_net_kw:
                if pn == kw:
                    canon = _spi_canon.get(kw, kw)
                    bus_id = "pin_" + p["component"]
                    spi_signals.setdefault(bus_id, {})[canon] = {
                        "net": net_name,
                        "devices": [pp["component"] for pp in net_info["pins"]
                                    if comp_lookup.get(pp["component"], {}).get("type") == "ic"],
                    }

    results = []
    for bus_id, signals in spi_signals.items():
        if len(signals) >= 2:  # At least 2 SPI signals to count as a bus
            # Skip if no ICs on any signal net (connector-only routing)
            has_ic = any(s.get("devices") for s in signals.values())
            if not has_ic:
                continue
            # Count unique devices across all SPI signals
            all_spi_devs = set()
            for sig_data in signals.values():
                all_spi_devs.update(sig_data.get("devices", []))
            results.append({
                "bus_id": bus_id,
                "signals": signals,
                "load_count": len(all_spi_devs),
            })

    return results


def _detect_uart_buses(ctx: AnalysisContext) -> list[dict]:
    """Detect UART buses by TX/RX net name patterns."""
    nets = ctx.nets
    comp_lookup = ctx.comp_lookup

    _uart_exclude = ("CAN", "SPI", "I2C", "MOSI", "MISO", "SCL", "SDA",
                     "RMII", "MII", "EMAC", "ENET", "ETH",
                     "PCIE", "PCI_", "HDMI", "LVDS", "MIPI",
                     "CLK", "CLOCK", "USB_D", "USBDM", "USBDP", "I2S")
    uart_nets = {}
    for net_name, net_info in nets.items():
        nu = net_name.upper()
        # Skip nets that belong to other bus types
        if any(kw in nu for kw in _uart_exclude):
            continue
        if any(kw in nu for kw in ("UART", "TX", "RX", "TXD", "RXD")):
            # Identify which devices connect
            device_refs = [p["component"] for p in net_info["pins"]
                           if comp_lookup.get(p["component"], {}).get("type") == "ic"]
            uart_nets[net_name] = {
                "net": net_name,
                "devices": [_enrich_device_ref(r, comp_lookup) for r in device_refs],
                "pin_count": len(net_info["pins"]),
            }

    # UART TX→RX crossover verification
    # For each TX net, check if it connects to a pin named RX on the other device (correct)
    # or a pin named TX (incorrect — TX wired to TX)
    _tx_pins = {"TX", "TXD", "UART_TX", "UART_TXD", "U_TX", "TXD0", "TXD1"}
    _rx_pins = {"RX", "RXD", "UART_RX", "UART_RXD", "U_RX", "RXD0", "RXD1"}

    for entry in uart_nets.values():
        net_name = entry["net"]
        nu = net_name.upper()
        # Determine if this is a TX or RX net from its name
        is_tx_net = any(kw in nu for kw in ("_TX", "TXD", "UART_TX")) and not any(kw in nu for kw in ("_RX", "RXD"))
        is_rx_net = any(kw in nu for kw in ("_RX", "RXD", "UART_RX")) and not any(kw in nu for kw in ("_TX", "TXD"))

        if not (is_tx_net or is_rx_net) or net_name not in nets:
            continue

        # Check pin names of connected ICs
        tx_pin_count = 0
        rx_pin_count = 0
        for p in nets[net_name]["pins"]:
            comp = comp_lookup.get(p["component"])
            if not comp or comp["type"] != "ic":
                continue
            pname = p.get("pin_name", "").upper()
            if pname in _tx_pins:
                tx_pin_count += 1
            elif pname in _rx_pins:
                rx_pin_count += 1

        # A TX net should connect to at least one RX pin (crossover)
        # If it connects to 2+ TX pins and no RX pins, that's TX→TX (wrong)
        if is_tx_net and tx_pin_count >= 2 and rx_pin_count == 0:
            entry["crossover_warning"] = (
                f"TX net {net_name} connects to {tx_pin_count} TX pins and "
                f"no RX pins — possible missing TX→RX crossover"
            )
        elif is_rx_net and rx_pin_count >= 2 and tx_pin_count == 0:
            entry["crossover_warning"] = (
                f"RX net {net_name} connects to {rx_pin_count} RX pins and "
                f"no TX pins — possible missing TX→RX crossover"
            )

    return list(uart_nets.values())


def _detect_sdio_buses(ctx: AnalysisContext) -> list[dict]:
    """Detect SDIO/SD/eMMC buses by CLK + CMD + D0 minimum."""
    nets = ctx.nets
    pin_net = ctx.pin_net
    comp_lookup = ctx.comp_lookup
    is_power_net = ctx.is_power_net

    _sdio_prefixes = ("SDIO", "SD_", "SD1_", "SD2_", "EMMC", "MMC", "WL_SDIO")
    sdio_signals = {}
    for net_name in nets:
        nu = net_name.upper()
        # Check if net matches an SDIO-related pattern
        matched_prefix = None
        for pfx in _sdio_prefixes:
            if pfx in nu:
                matched_prefix = pfx
                break
        if not matched_prefix:
            # Also match bare SD signal patterns like SDCLK, SDCMD
            if nu.startswith("SD") and any(nu.endswith(sig) for sig in ("CLK", "CMD", "D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7")):
                matched_prefix = "SD"
            else:
                continue

        # Classify the signal type
        sig_type = None
        if "CLK" in nu:
            sig_type = "CLK"
        elif "CMD" in nu:
            sig_type = "CMD"
        else:
            # Match data lines D0-D7
            dm = re.search(r'D(\d)', nu)
            if dm:
                sig_type = f"D{dm.group(1)}"

        if sig_type:
            # Group by bus prefix for multi-bus designs
            bus_key = matched_prefix.rstrip("_")
            sdio_signals.setdefault(bus_key, {})[sig_type] = net_name

    # Build SDIO bus entries
    results = []
    for bus_key, sigs in sdio_signals.items():
        if "CLK" not in sigs or "CMD" not in sigs or "D0" not in sigs:
            continue
        # Count data lines
        data_lines = sorted(k for k in sigs if k.startswith("D") and k[1:].isdigit())
        bus_width = len(data_lines)

        # Check for pull-ups on CMD and data lines
        pullup_nets = []
        for sig_name in ["CMD"] + data_lines:
            net_name = sigs.get(sig_name)
            if not net_name or net_name not in nets:
                continue
            for p in nets[net_name]["pins"]:
                comp = comp_lookup.get(p["component"])
                if comp and comp["type"] == "resistor":
                    r_n1, _ = pin_net.get((p["component"], "1"), (None, None))
                    r_n2, _ = pin_net.get((p["component"], "2"), (None, None))
                    other = r_n2 if r_n1 == net_name else r_n1
                    if other and is_power_net(other):
                        pullup_nets.append(sig_name)
                        break

        # Find connected devices
        all_devices = set()
        for sig_name, net_name in sigs.items():
            if net_name in nets:
                for p in nets[net_name]["pins"]:
                    if comp_lookup.get(p["component"], {}).get("type") == "ic":
                        all_devices.add(p["component"])

        results.append({
            "bus_id": bus_key,
            "bus_width": bus_width,
            "signals": {sig: net for sig, net in sigs.items()},
            "devices": sorted(all_devices),
            "has_pullups": len(pullup_nets) > 0,
            "pullup_signals": pullup_nets,
        })

    return results


def _detect_can_buses(ctx: AnalysisContext) -> list[dict]:
    """Detect CAN buses by net name keywords and transceiver IC presence."""
    components = ctx.components
    nets = ctx.nets
    comp_lookup = ctx.comp_lookup
    pin_net = ctx.pin_net
    parsed_values = ctx.parsed_values

    can_keywords = ("can_tx", "can_rx", "cantx", "canrx", "canh", "canl", "can_h", "can_l")
    # SN65HVD2xx/10xx are CAN; SN65HVD7x are RS-485 -- use specific prefixes
    can_transceiver_kw = ("sn65hvd2", "sn65hvd10", "mcp2551", "mcp2562", "mcp251",
                          "tja10", "tja11", "iso1050", "max3051", "ata6561",
                          "mcp2561", "iso1042")
    can_nets_found = {}
    for net_name, net_info in nets.items():
        nu = net_name.upper()
        if any(kw in nu.lower() for kw in can_keywords):
            device_refs = [p["component"] for p in net_info["pins"]
                           if comp_lookup.get(p["component"], {}).get("type") == "ic"]
            can_nets_found[net_name] = {
                "net": net_name,
                "devices": [_enrich_device_ref(r, comp_lookup) for r in device_refs],
            }
    # Also detect by CAN transceiver IC presence -- add transceiver info to bus
    for comp in components:
        if comp["type"] != "ic":
            continue
        val = comp.get("value", "").lower()
        lib = comp.get("lib_id", "").lower()
        if any(k in val or k in lib for k in can_transceiver_kw):
            if not can_nets_found:
                # No CAN nets found by name -- add a placeholder entry
                can_nets_found["__can_transceiver__"] = {
                    "net": "CAN",
                    "transceiver": comp["reference"],
                    "devices": [_enrich_device_ref(comp["reference"], comp_lookup)],
                }

    # CAN termination detection: look for 100-150 ohm resistors between CANH and CANL
    canh_nets = [n for n in can_nets_found if "CANH" in n.upper() or "CAN_H" in n.upper()]
    canl_nets = [n for n in can_nets_found if "CANL" in n.upper() or "CAN_L" in n.upper()]
    termination = None
    for canh_net in canh_nets:
        if canh_net not in nets:
            continue
        for p in nets[canh_net]["pins"]:
            comp = comp_lookup.get(p["component"])
            if not comp or comp["type"] != "resistor":
                continue
            r_val = parsed_values.get(p["component"])
            if r_val and 100 <= r_val <= 150:
                # Check if other end goes to a CANL net
                other_pin = "1" if p["pin_number"] == "2" else "2"
                other_net, _ = pin_net.get((p["component"], other_pin), (None, None))
                if other_net and any(other_net == cl for cl in canl_nets):
                    termination = f"{int(r_val)}\u03A9 ({p['component']})"
                    break
        if termination:
            break
    # Attach termination to all CAN bus entries
    for entry in can_nets_found.values():
        entry["termination"] = termination

    return list(can_nets_found.values())


def _detect_rs485_buses(ctx: AnalysisContext) -> list[dict]:
    """Detect RS-485/RS-422 buses by transceiver IC part number."""
    components = ctx.components
    pin_net = ctx.pin_net

    _rs485_kw = ("max485", "max3485", "max13485", "max14840", "max22500",
                 "sn65hvd7", "sn65hvd3", "sn75176", "sn75lbc",
                 "thvd14", "thvd15", "thvd16",
                 "isl317", "isl318", "isl319",
                 "sp3485", "sp3481", "sp3082", "sp485",
                 "adm485", "adm2485", "adm2587", "adm3485",
                 "ltc285", "ltc248", "ltc249",
                 "st3485", "st485")

    results = []
    for comp in components:
        if comp["type"] != "ic":
            continue
        val_lib = (comp.get("value", "") + " " + comp.get("lib_id", "")).lower()
        if not any(k in val_lib for k in _rs485_kw):
            continue
        ref = comp["reference"]
        # Map known pin functions
        a_net = b_net = di_net = ro_net = de_net = re_net = None
        for pin in comp.get("pins", []):
            pn = pin.get("name", "").upper()
            net_name, _ = pin_net.get((ref, pin["number"]), (None, None))
            if not net_name:
                continue
            if pn in ("A", "A/Y"):
                a_net = net_name
            elif pn in ("B", "B/Z"):
                b_net = net_name
            elif pn in ("DI", "D", "TXD", "DIN"):
                di_net = net_name
            elif pn in ("RO", "R", "RXD", "DOUT"):
                ro_net = net_name
            elif pn in ("DE",):
                de_net = net_name
            elif pn in ("RE", "~RE", "~{RE}", "/RE"):
                re_net = net_name
        entry = {
            "transceiver": ref,
            "value": comp.get("value", ""),
        }
        if a_net:
            entry["a_net"] = a_net
        if b_net:
            entry["b_net"] = b_net
        if di_net:
            entry["di_net"] = di_net
        if ro_net:
            entry["ro_net"] = ro_net
        if de_net:
            entry["de_net"] = de_net
        if re_net:
            entry["re_net"] = re_net
        results.append(entry)

    return results


def _analyze_bus_protocols(ctx: AnalysisContext) -> dict:
    """Detect I2C, SPI, UART, CAN, SDIO, RS-485 buses and check configuration."""
    nets = ctx.nets
    comp_lookup = ctx.comp_lookup

    buses: dict = {
        "i2c": _detect_i2c_buses(ctx),
        "spi": _detect_spi_buses(ctx),
        "uart": _detect_uart_buses(ctx),
        "can": _detect_can_buses(ctx),
    }

    sdio = _detect_sdio_buses(ctx)
    if sdio:
        buses["sdio"] = sdio

    rs485 = _detect_rs485_buses(ctx)
    if rs485:
        buses["rs485"] = rs485

    # SPI enrichment: add chip_select count and bus_mode
    for spi_entry in buses.get("spi", []):
        sigs = spi_entry.get("signals", {})
        # Count CS/SS nets for this bus
        cs_nets = []
        bus_id = spi_entry.get("bus_id", "")
        for net_name in nets:
            nu = net_name.upper()
            if any(kw in nu for kw in ("CS", "SS", "NSS", "SPI_CS", "SPI_SS",
                                       "CSN", "NCS", "SSEL", "CSEL")):
                if bus_id in ("0", "") or bus_id in nu.replace("_", ""):
                    cs_nets.append(net_name)
        spi_entry["chip_select_count"] = len(cs_nets)
        # SPI CS conflict: find cases where multiple ICs share the same CS net
        cs_device_map = {}  # net_name -> [device_refs]
        for net_name in cs_nets:
            if net_name not in nets:
                continue
            devices_on_cs = []
            for p in nets[net_name]["pins"]:
                comp = comp_lookup.get(p["component"])
                if comp and comp["type"] == "ic":
                    devices_on_cs.append(p["component"])
            if len(devices_on_cs) > 1:
                cs_device_map[net_name] = devices_on_cs

        if cs_device_map:
            spi_entry["cs_conflicts"] = [
                {
                    "net": net_name,
                    "devices": devices,
                    "message": (f"CS net {net_name} shared by {len(devices)} devices "
                                f"({', '.join(devices)}) — cannot address independently"),
                }
                for net_name, devices in cs_device_map.items()
            ]
        has_mosi = "MOSI" in sigs
        has_miso = "MISO" in sigs
        if has_mosi and has_miso:
            spi_entry["bus_mode"] = "full_duplex"
        elif has_mosi or has_miso:
            spi_entry["bus_mode"] = "half_duplex"

        # Add top-level devices list (aggregated from all signal entries)
        # for schema consistency with I2C/UART/CAN which have flat devices[]
        all_spi_devs: set[str] = set()
        for sig_info in sigs.values():
            if isinstance(sig_info, dict):
                all_spi_devs.update(sig_info.get('devices', []))
        spi_entry['devices'] = [_enrich_device_ref(r, comp_lookup) for r in sorted(all_spi_devs)]

        # Controller: MCU/FPGA driving SCK (clock master)
        sck_info = sigs.get("SCK")
        controller = None
        if isinstance(sck_info, dict):
            for ref in sck_info.get("devices", []):
                fc = comp_lookup.get(ref, {}).get("functional_class", "")
                if fc in ("mcu", "fpga"):
                    controller = ref
                    break
        spi_entry["controller"] = controller

    return buses


def _guess_diff_protocol(net_name: str) -> str:
    """Guess the protocol from a differential pair net name."""
    nu = net_name.upper()
    if "USB" in nu:
        return "USB"
    if "LVDS" in nu:
        return "LVDS"
    if "ETH" in nu or "MDIO" in nu or "RGMII" in nu or "SGMII" in nu:
        return "Ethernet"
    if "HDMI" in nu or "TMDS" in nu:
        return "HDMI"
    if "MIPI" in nu or "DSI" in nu or "CSI" in nu:
        return "MIPI"
    if "PCIE" in nu or "PCI" in nu:
        return "PCIe"
    if "SATA" in nu:
        return "SATA"
    if "CAN" in nu:
        return "CAN"
    if "RS485" in nu or "RS-485" in nu:
        return "RS-485"
    return "differential"


def _detect_differential_pairs(ctx: AnalysisContext) -> list:
    """Detect differential pairs by suffix matching."""
    components = ctx.components
    nets = ctx.nets
    pin_net = ctx.pin_net
    comp_lookup = ctx.comp_lookup
    parsed_values = ctx.parsed_values
    is_power_net = ctx.is_power_net
    is_ground = ctx.is_ground

    diff_pairs = []

    # Suffix pair table: (positive_suffix, negative_suffix) -> protocol guess
    _diff_suffix_pairs = [
        # USB
        ("_DP", "_DM"), ("_D+", "_D-"), ("_D_P", "_D_N"), ("DP", "DM"),
        # Generic differential
        ("_P", "_N"), ("+", "-"),
        # LVDS / Ethernet
        ("_TX+", "_TX-"), ("_RX+", "_RX-"),
        ("_TXP", "_TXN"), ("_RXP", "_RXN"),
        ("_TD+", "_TD-"), ("_RD+", "_RD-"),
        ("_TDP", "_TDN"), ("_RDP", "_RDN"),
    ]

    # Net-name-based detection: find matching suffix pairs. Key by
    # (sheet_prefix, display_name.upper()) so a KH-359 sheet-qualified net
    # (e.g. /s1/USB_P, display_name "USB_P") still pairs by name, but two
    # same-named nets on *different* sheets never cross-pair. Plain
    # assignment (not setdefault) preserves the pre-KH-359 comprehension's
    # last-wins semantics on a case-insensitive collision: unqualified
    # boards must resolve a collision identically to the old
    # `{n.upper(): n for n in nets}` one-liner.
    net_names_upper: dict[tuple[str, str], str] = {}
    for k, v in nets.items():
        disp = v.get("display_name", k)
        prefix = k[: -len(disp)] if k.endswith(disp) else ""
        net_names_upper[(prefix, disp.upper())] = k
    found_pairs: set[tuple[str, str]] = set()  # track to avoid duplicates

    for pos_sfx, neg_sfx in _diff_suffix_pairs:
        for (prefix, nu), real_name in net_names_upper.items():
            if nu.endswith(pos_sfx.upper()):
                base = nu[:-len(pos_sfx)]
                neg_candidate = base + neg_sfx.upper()
                neg_key = (prefix, neg_candidate)
                if neg_key in net_names_upper:
                    pos_real = real_name
                    neg_real = net_names_upper[neg_key]
                    pair_key = (min(pos_real, neg_real), max(pos_real, neg_real))
                    if pair_key in found_pairs:
                        continue
                    # Skip power/ground nets (V+/V-, IN+/IN- on power rails)
                    if is_power_net(pos_real) or is_power_net(neg_real):
                        continue
                    if is_ground(pos_real) or is_ground(neg_real):
                        continue
                    found_pairs.add(pair_key)

                    protocol = _guess_diff_protocol(pos_real)
                    entry: dict = {
                        "type": protocol,
                        "positive": pos_real,
                        "negative": neg_real,
                    }

                    # Find shared ICs (connected to both nets)
                    pos_comps = {p["component"] for p in nets[pos_real]["pins"]
                                 if not p["component"].startswith("#")}
                    neg_comps = {p["component"] for p in nets[neg_real]["pins"]
                                 if not p["component"].startswith("#")}
                    shared = pos_comps & neg_comps
                    if shared:
                        entry["shared_ics"] = sorted(shared)

                    # Check for ESD protection
                    esd_chips = [c for c in sorted(shared)
                                 if comp_lookup.get(c, {}).get("type") == "ic"]
                    entry["has_esd"] = len(esd_chips) > 0
                    if esd_chips:
                        entry["esd_protection"] = esd_chips

                    # CAN-specific: check for termination resistor
                    if protocol == "CAN":
                        term_resistors = []
                        for c in components:
                            if c["type"] == "resistor":
                                r_n1 = pin_net.get((c["reference"], "1"), (None, None))[0]
                                r_n2 = pin_net.get((c["reference"], "2"), (None, None))[0]
                                if r_n1 and r_n2:
                                    if ({r_n1, r_n2} == {pos_real, neg_real}):
                                        term_resistors.append({
                                            "ref": c["reference"],
                                            "value": c["value"],
                                            "ohms": parsed_values.get(c["reference"]),
                                        })
                        entry["termination"] = term_resistors
                        entry["has_termination"] = len(term_resistors) > 0

                    # Series resistors on either net
                    series_res = []
                    for net_r in (pos_real, neg_real):
                        for p in nets[net_r]["pins"]:
                            comp = comp_lookup.get(p["component"])
                            if comp and comp["type"] == "resistor":
                                series_res.append(p["component"])
                    if series_res:
                        entry["series_resistors"] = sorted(set(series_res))

                    diff_pairs.append(entry)

    return diff_pairs


def _check_erc_warnings(ctx: AnalysisContext) -> list:
    """Check for ERC-style warnings (no driver, output conflicts)."""
    nets = ctx.nets
    is_ground = ctx.is_ground
    is_power_net = ctx.is_power_net

    erc_warnings = []

    for net_name, net_info in nets.items():
        if is_power_net(net_name) or is_ground(net_name):
            continue
        if net_name.startswith("__unnamed_"):
            continue

        pin_types = [p["pin_type"] for p in net_info["pins"] if not p["component"].startswith("#")]
        type_set = set(pin_types)

        # Input-only net: all pins are inputs, no driver
        outputs = {"output", "tri_state", "power_out", "open_collector", "open_emitter"}
        drivers = {"output", "tri_state", "power_out", "open_collector", "open_emitter", "bidirectional"}
        has_driver = bool(type_set & drivers)
        has_input = bool(type_set & {"input", "power_in"})

        if has_input and not has_driver and len(pin_types) > 1:
            erc_warnings.append({
                "type": "no_driver",
                "net": net_name,
                "message": f"Net '{net_name}' has input pins but no output driver",
                "pins": [p for p in net_info["pins"] if not p["component"].startswith("#")],
            })

        # Multiple outputs on same net (non-tristate)
        hard_outputs = [p for p in net_info["pins"]
                        if p["pin_type"] == "output" and not p["component"].startswith("#")]
        if len(hard_outputs) > 1:
            # Suppress when all drivers are from the same component (paralleled pins)
            driver_components = {p["component"] for p in hard_outputs}
            if len(driver_components) > 1:
                erc_warnings.append({
                    "type": "output_conflict",
                    "net": net_name,
                    "message": f"Net '{net_name}' has {len(hard_outputs)} output drivers (potential conflict)",
                    "drivers": hard_outputs,
                })

    return erc_warnings


def _check_passive_ratings(ctx: AnalysisContext) -> list:
    """Check passive component voltage ratings against rail voltages."""
    components = ctx.components
    pin_net = ctx.pin_net

    passive_warnings = []
    for c in components:
        if c["type"] == "capacitor" and c.get("value"):
            # Check if capacitor voltage rating is in the value string
            val_str = c["value"]
            # Common pattern: "100n/16V", "10u 25V", "22uF 6.3V"
            v_match = re.search(r'(\d+(?:\.\d+)?)\s*[Vv]', val_str)
            if v_match:
                rated_v = float(v_match.group(1))
                # Check which rails this cap connects to
                c_n1, _ = pin_net.get((c["reference"], "1"), (None, None))
                c_n2, _ = pin_net.get((c["reference"], "2"), (None, None))
                # Rough rail voltage estimation from name
                for net in [c_n1, c_n2]:
                    if net:
                        v_est = _estimate_rail_voltage(net)
                        if v_est and rated_v < v_est * 1.5:
                            passive_warnings.append({
                                "component": c["reference"],
                                "value": c["value"],
                                "rated_voltage": rated_v,
                                "rail": net,
                                "estimated_rail_v": v_est,
                                "warning": f"Voltage derating margin < 50% ({rated_v}V rated on ~{v_est}V rail)",
                            })

    return passive_warnings


def analyze_design_rules(ctx: AnalysisContext, results_in: dict | None = None) -> dict:
    """Deep EE analysis: power domains, bus protocols, differential pairs, ERC checks."""
    net_classes = _classify_nets(ctx)
    pd = _map_power_domains(ctx)
    cross_domain = _detect_cross_domain_signals(ctx, pd["ic_power_rails"], results_in)
    buses = _analyze_bus_protocols(ctx)
    diff_pairs = _detect_differential_pairs(ctx)
    erc = _check_erc_warnings(ctx)
    passive = _check_passive_ratings(ctx)
    return {
        "net_classification": net_classes,
        "power_domains": pd,
        "cross_domain_signals": cross_domain,
        "bus_analysis": buses,
        "differential_pairs": diff_pairs,
        "erc_warnings": erc,
        "passive_warnings": passive,
    }


def _estimate_rail_voltage(net_name: str) -> float | None:
    """Estimate voltage of a power rail from its name."""
    if not net_name:
        return None
    nu = net_name.upper()
    if nu in ("GND", "VSS", "AGND", "DGND"):
        return 0
    v = _parse_voltage_from_net_name(net_name)
    if v is not None:
        return v
    # Hardcoded fallbacks for common names without voltage numbers
    if "VBUS" in nu:
        return 5.0
    # KH-343: only non-data USB nets (VBUS-ish) default to 5V
    if "USB" in nu and not is_usb_data_net_name(nu):
        return 5.0
    return None
