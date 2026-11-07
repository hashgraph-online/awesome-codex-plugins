"""Connectivity, power-domain, cross-domain, bus-protocol and differential-pair analyses."""
from __future__ import annotations

import re
from kicad_types import (
    AnalysisContext,
)
from kicad_core.classify import classify_ic_function
from kicad_core.coords import to_iu
from detector_helpers import is_protection_part
from kicad_core.sexp import unescape_string
from schematic import erc_pins
from kicad_core.parts import (
    _OUTPUT_DRIVE_KEYWORDS,
)
from kicad_core.netnames import (
    parse_voltage_from_net_name as _parse_voltage_from_net_name,
    is_usb_data_net_name,
    net_leaf,
)


def analyze_connectivity(components: list[dict], nets: dict, no_connects: list[dict]) -> dict:
    """Analyze the connectivity graph for potential issues.

    Returns a dict with:
    - unconnected_pins: pins not on any net (and not marked no-connect)
    - single_pin_nets: nets with only one pin (likely unfinished connections)
    - multi_driver_nets: nets where two driving pins conflict at KiCad's error level
    - power_net_summary: per power rail, which components connect
    """

    # Build set of no-connect positions for quick lookup
    nc_positions = set()
    for nc in no_connects:
        nc_positions.add((nc.get("_sheet", 0),
                          to_iu(nc["x"]),
                          to_iu(nc["y"])))

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
                           to_iu(pin["x"]),
                           to_iu(pin["y"]))
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
        # stubs. The rich NT-001 finding
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

    # Driving pins whose pair is an error in KiCad's pin map. Power symbols and
    # flags (#PWR, #FLG) are virtual, not real drivers.
    multi_driver_nets = []
    positions = erc_pins.pin_positions(components)
    for net_name, net_info in nets.items():
        drivers = [p for p in net_info["pins"]
                   if not p["component"].startswith("#")
                   and erc_pins.pin_kind(p.get("pin_type")) in erc_pins.DRIVERS]
        hit = set()
        for i, j, level in erc_pins.net_pin_conflicts(drivers, positions):
            if level == erc_pins.ERROR:
                hit.update((i, j))
        if hit:
            multi_driver_nets.append({
                "net": net_name,
                "drivers": [drivers[k] for k in sorted(hit)],
                "severity": "error",
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


# Net-class keywords, checked in order; the first class with a hit wins.
_NET_CLASS_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("clock", ("SCL", "SCK", "CLK", "MCLK", "SCLK", "XTAL", "OSC")),
    ("data", ("SDA", "MOSI", "MISO", "SDI", "SDO", "UART", "TXD", "RXD",
              "TXP", "TXN", "TXM", "RXP", "RXN", "RXM", "TX", "RX")),
    ("high_speed", ("USB", "CAN", "LVDS", "ETH")),
    ("analog", ("ADC", "AIN", "VREF", "VSENSE", "ISENSE")),
    ("control", ("RESET", "NRST", "RST", "EN", "ENABLE")),
    ("chip_select", ("CS", "SS", "NSS", "CE", "SEL")),
    ("interrupt", ("INT", "IRQ", "ALERT", "DRDY")),
    ("output_drive", _OUTPUT_DRIVE_KEYWORDS),
    ("debug", ("SWD", "SWCLK", "SWDIO", "SWO", "JTAG", "TCK", "TMS", "TDI", "TDO")),
    ("config", ("BOOT", "TEST")),
)
# video sync signals are not chip selects
_SYNC_KEYWORDS = ("CSYNC", "HSYNC", "VSYNC", "SYNC")
# A token starting with a supply stem (VCCINT, VDDIO, AVDD_ADC) names a rail, never a keyword
_SUPPLY_STEMS = ("VCC", "VDD", "AVCC", "AVDD", "DVCC", "DVDD", "PVDD", "IOVDD")
# Supply-input pin names besides the stems above (V+, VIN, PVIN, IN, VBAT, BAT, VS, VM, ...)
_SUPPLY_PIN_NAMES = frozenset({
    "V", "VIN", "PVIN", "AVIN", "IN", "VBAT", "BAT", "VS", "VM", "VBUS", "VSUP", "VSYS",
    "VPWR", "PWR"})
# Pins typed power_in that are not supply inputs: grounds, switch nodes, regulator caps, references
_NOT_SUPPLY_PIN_NAMES = frozenset({"GND", "VSS", "L", "LX", "SW", "AREF"})
_NOT_SUPPLY_PIN_PREFIXES = ("GND", "VSS", "VLX", "VCAP", "VREF")
# The return of an isolated module's input (VIN-, -VIN, VIN_N)
_SUPPLY_RETURN_PIN = re.compile(r'-VIN\d*|VIN\d*-|VIN\d*_N')


def _name_tokens(name: str) -> list[str]:
    """Upper-case tokens of *name*: split on non-alphanumerics and letter/digit boundaries,
    with active-low markers (``nINT``, ``INTn``, ``_N``) removed."""
    tokens = []
    for part in re.split(r'[^0-9A-Za-z]+', unescape_string(name)):
        for t in re.findall(r'[A-Za-z]+|[0-9]+', part):
            if len(t) > 2 and t[0] == "n" and t[1].isupper():
                t = t[1:]
            elif len(t) > 2 and t[-1] == "n" and t[-2].isupper():
                t = t[:-1]
            t = t.upper()
            if t != "N":
                tokens.append(t)
    return tokens


def _keyword_hit(tokens: list[str], keywords: tuple[str, ...]) -> bool:
    """A keyword of three or more letters hits anywhere in a token; a two-letter one (TX, EN,
    CS) only as the whole token, its start or its end, also before an active-low B/N (ROMCSB).
    A supply-stem token hits only as that rail's enable (VCCOEN)."""
    for t in tokens:
        if t.startswith(_SUPPLY_STEMS):
            if any(k in ("EN", "ENABLE") and t.endswith(k) for k in keywords):
                return True
            continue
        forms = (t, t[:-1]) if len(t) > 2 and t[-1] in "BN" else (t,)
        for k in keywords:
            if len(k) > 2:
                if k in t:
                    return True
            elif any(f == k or f.startswith(k) or f.endswith(k) for f in forms):
                return True
    return False


def _keyword_class(net_name: str) -> str:
    tokens = _name_tokens(net_name)
    for cls, keywords in _NET_CLASS_KEYWORDS:
        if _keyword_hit(tokens, keywords):
            if cls == "chip_select" and _keyword_hit(tokens, _SYNC_KEYWORDS):
                return "signal"
            return cls
    return "signal"


def _is_supply_pin_name(pin_name: str) -> bool:
    tokens = _name_tokens(pin_name or "")
    compact = "".join(tokens)
    # "0V" is a ground reference
    if not tokens or compact == "0V" or compact.startswith(_NOT_SUPPLY_PIN_PREFIXES) or any(
            t in _NOT_SUPPLY_PIN_NAMES or t.startswith(_NOT_SUPPLY_PIN_PREFIXES) for t in tokens):
        return False
    if _SUPPLY_RETURN_PIN.fullmatch(re.sub(r'\s+', '', unescape_string(pin_name).upper())):
        return False
    # "3V3" and "V+" tokenise to a bare "V"
    return any("VCC" in t or "VDD" in t or t in _SUPPLY_PIN_NAMES for t in tokens)


def _has_bootstrap_pin(ref: str, ref_pins: dict) -> bool:
    """True when IC *ref* has a VB pin: its VS is a high-side driver's switch node."""
    for num, (_net, info) in ref_pins.get(ref, {}).items():
        for p in info.get("pins", []):
            if (p.get("component") == ref and p.get("pin_number") == num
                    and "".join(_name_tokens(p.get("pin_name") or "")) == "VB"):
                return True
    return False


def _is_ic_supply_input_net(net_info: dict, comp_lookup: dict, ref_pins: dict) -> bool:
    """True when the net has IC pins and every non-passive one is a power_in supply input."""
    ic_pins = [p for p in net_info.get("pins", [])
               if (comp_lookup.get(p.get("component")) or {}).get("type") == "ic"
               and str(p.get("pin_type") or "").split("+")[0] != "passive"]
    return bool(ic_pins) and all(
        str(p.get("pin_type") or "").split("+")[0] == "power_in"
        and _is_supply_pin_name(p.get("pin_name", ""))
        and not ("".join(_name_tokens(p.get("pin_name") or "")) == "VS"
                 and _has_bootstrap_pin(p.get("component"), ref_pins))
        for p in ic_pins)


# A passive-typed IC pin is a supply by its whole name only (VCC, AVDD_PLL, VIN2, V+);
# a token match would take OSC_IN or V1.
_SUPPLY_PIN_FULL_NAME = re.compile(
    r'(?:[ADP]|IO)?V(?:CC|DD)[A-Z0-9]*|[AP]?VIN\d*|V(?:BAT|BATT|BUS|SUP|SYS|PWR|S|M)\d*|V\+')

# Bridge outputs KiCad types power_out (DRV8833 AOUT1, A4950 OUT1, STSPIN OUTA1/OUTU,
# DRV8800 OUT+): two of them on one IC drive a load between them, not a rail.
_BRIDGE_OUTPUT_PIN = re.compile(r'[A-D]?OUT(?:[A-D]?\d+[A-D]?|[A-D]|[UVW])?[+-]?')


def _bridge_output_name(pin_name: str) -> bool:
    compact = re.sub(r'[^0-9A-Z+-]', '', unescape_string(pin_name).upper())
    return compact != "OUT" and bool(_BRIDGE_OUTPUT_PIN.fullmatch(compact))


def _has_sibling_bridge_output(ref: str, net: str, ref_pins: dict) -> bool:
    """True when IC *ref* has a bridge-named power_out pin on a net other than *net*."""
    for num, (other_net, info) in ref_pins.get(ref, {}).items():
        if other_net == net:
            continue
        for p in info.get("pins", []):
            if (p.get("component") == ref and p.get("pin_number") == num
                    and str(p.get("pin_type") or "").split("+")[0] == "power_out"
                    and _bridge_output_name(p.get("pin_name") or "")):
                return True
    return False


def topology_rail_nets(nets: dict[str, dict], comp_lookup: dict[str, dict], ref_pins: dict,
                       is_rail, is_ground) -> frozenset[str]:
    """Named nets that are supply rails by their pins, whatever their name.

    Every IC pin on the net is a supply input or a power output, and a capacitor goes to
    ground. A pin typed passive counts as a supply by its name (VCC, VDD, VIN); other
    passive pins are allowed only beside a pin KiCad types as power (a load-switch FET
    drawn as an IC). A reference node (REF in the name), a net with a resistor to
    ground (a divider midpoint) and a motor-driver output stay signals. A bridge-named
    output (OUT1 beside an OUT2 on another net) of a part not classed as power
    management makes a rail only beside a supply input it feeds (a PMIC's OUT1), not
    alone (an H-bridge's motor lead)."""
    def far_net(ref: str, net: str) -> str | None:
        others = {n for n, _ in ref_pins.get(ref, {}).values() if n != net}
        return next(iter(others)) if len(others) == 1 else None

    found = set()
    for name, info in nets.items():
        if (name.startswith("__unnamed_") or is_rail(name) or is_ground(name)
                or any("REF" in t for t in _name_tokens(name.rsplit("/", 1)[-1]))):
            continue
        typed_supply = named_supply = untyped_other = 0
        cap_to_ground = False
        for p in info.get("pins", []):
            ref = p.get("component") or ""
            kind = (comp_lookup.get(ref) or {}).get("type")
            if kind == "ic":
                ptype = str(p.get("pin_type") or "").split("+")[0]
                pname = p.get("pin_name") or ""
                tokens = _name_tokens(pname)
                excluded = ("".join(tokens).startswith(_NOT_SUPPLY_PIN_PREFIXES)
                            or any(t in _NOT_SUPPLY_PIN_NAMES for t in tokens))
                if ptype == "power_out" and not excluded:
                    function = _ic_function(comp_lookup.get(ref) or {})
                    if function == "motor_driver":
                        break
                    if (function != "power_management" and _bridge_output_name(pname)
                            and _has_sibling_bridge_output(ref, name, ref_pins)):
                        continue   # not a supply by itself: needs a supply input beside it
                    typed_supply += 1
                elif "".join(tokens) == "VS" and _has_bootstrap_pin(ref, ref_pins):
                    break
                elif ptype == "power_in" and _is_supply_pin_name(pname):
                    typed_supply += 1
                elif (ptype in ("passive", "unspecified", "") and _SUPPLY_PIN_FULL_NAME.fullmatch(
                        re.sub(r'[^0-9A-Z+]', '', unescape_string(pname).upper()))):
                    named_supply += 1
                elif ptype in ("passive", "unspecified", "") and not excluded:
                    untyped_other += 1
                else:
                    break
            elif kind in ("capacitor", "resistor"):
                far = far_net(ref, name)
                if kind == "capacitor" and far and is_ground(far):
                    cap_to_ground = True
                elif kind == "resistor" and far and is_ground(far):
                    break
        else:
            if (cap_to_ground and (typed_supply or named_supply)
                    and (typed_supply or not untyped_other)):
                found.add(name)
    return frozenset(found)


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

        if is_ground(net_name):
            net_classes[net_name] = "ground"
        elif is_power_net(net_name):
            net_classes[net_name] = "power"
        else:
            cls = _keyword_class(net_name)
            if cls == "signal" and _is_ic_supply_input_net(net_info, ctx.comp_lookup, ctx.ref_pins):
                cls = "power"
            net_classes[net_name] = cls

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
    # Accumulate rails/io_rails across all units of multi-unit ICs
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
            # Also exclude MOSI/MISO nets (SPI data lines on dual-function ICs)
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
                    v = ctx.rail_voltage_or(pu.get("to_rail", ""), _estimate_rail_voltage)
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
        # Exclude SPI nets -- sensors with dual-function SDA/SCL pin names
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
                    v = ctx.rail_voltage_or(pu.get("to_rail", ""), _estimate_rail_voltage)
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
                        max_mode = None
                        for mode_name, limit_ns in _I2C_MODES:
                            if rise_time_ns <= limit_ns:
                                max_mode = mode_name
                                break

                        entry["max_speed_mode"] = max_mode
                        if max_mode is None:
                            entry["rise_time_warning"] = (
                                f"Rise time {rise_time_ns:.0f}ns exceeds the "
                                f"Standard-mode limit (1000ns)")

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

    # CAN termination per bus (ISO 11898-2): a 100-150 ohm resistor between that bus's CANH and CANL
    canh_nets = [n for n in can_nets_found if "CANH" in n.upper() or "CAN_H" in n.upper()]
    canl_nets = [n for n in can_nets_found if "CANL" in n.upper() or "CAN_L" in n.upper()]
    pairs = can_bus_pairs(canh_nets, canl_nets)
    term_by_net: dict = {}
    dnp_by_net: dict = {}
    for canh_net, canl_net in pairs:
        termination = dnp_ref = None
        for p in (nets[canh_net]["pins"] if canh_net in nets else []):
            comp = comp_lookup.get(p["component"])
            if not comp or comp["type"] != "resistor":
                continue
            r_val = parsed_values.get(p["component"])
            if r_val and 100 <= r_val <= 150:
                other_pin = "1" if p["pin_number"] == "2" else "2"
                other_net, _ = pin_net.get((p["component"], other_pin), (None, None))
                if other_net != canl_net:
                    continue
                if comp.get("dnp"):
                    # An unfitted terminator is the per-node option: only bus-end nodes fit it
                    dnp_ref = dnp_ref or p["component"]
                    continue
                termination = f"{int(r_val)}\u03A9 ({p['component']})"
                break
        term_by_net[canh_net] = termination
        dnp_by_net[canh_net] = dnp_ref
        if term_by_net.get(canl_net) is None:
            term_by_net[canl_net] = termination
            dnp_by_net[canl_net] = dnp_ref
    # Logic-side entries (TX/RX, the transceiver placeholder) belong to a bus only on a one-bus design
    single = term_by_net[pairs[0][0]] if len(pairs) == 1 else None
    single_dnp = dnp_by_net.get(pairs[0][0]) if len(pairs) == 1 else None
    for key, entry in can_nets_found.items():
        entry["termination"] = term_by_net.get(key, single)
        dnp_ref = dnp_by_net.get(key, single_dnp) if entry["termination"] is None else None
        if dnp_ref:
            entry["termination_dnp"] = dnp_ref

    return list(can_nets_found.values())


def can_pair_key(net_name: str) -> str | None:
    """A CANH or CANL net's bus key: the name with its last CANH/CANL (CAN_H/CAN_L) marker blanked."""
    u = net_name.upper()
    best = None
    for marker, blank in (("CANH", "CAN#"), ("CANL", "CAN#"), ("CAN_H", "CAN_#"), ("CAN_L", "CAN_#")):
        i = u.rfind(marker)
        if i >= 0 and (best is None or i > best[0]):
            best = (i, u[:i] + blank + u[i + len(marker):])
    return best[1] if best else None


def can_bus_pairs(canh_nets: list, canl_nets: list) -> list[tuple[str, str]]:
    """(CANH, CANL) per bus: the same name with H for L; a CANH with no such partner takes the
    design's only CANL net, if there is exactly one."""
    pairs = []
    for h in canh_nets:
        cands = [lo for lo in canl_nets if can_pair_key(lo) == can_pair_key(h)]
        if not cands and len(canl_nets) == 1:
            cands = list(canl_nets)
        pairs += [(h, lo) for lo in cands]
    return pairs


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


_CS_TOKEN = re.compile(r"^N?(CS|SS|NSS|CSN|CSB|SSEL|CSEL)\d*N?$")


def _is_chip_select_net(net_name: str) -> bool:
    """A word of the net's own name is a chip select (``FLASH_CS``, ``~{CS0}``), not a
    substring of another word (``DAC_VSS``, ``SSP1_SCK``)."""
    leaf = net_leaf(net_name).upper().replace("~{", "").replace("}", "")
    return any(_CS_TOKEN.match(t) for t in re.split(r"[^A-Z0-9]+", leaf) if t)


def _ic_function(comp: dict) -> str:
    """The IC's functional class; legacy components carry none and are classified here."""
    return comp.get("functional_class") or classify_ic_function(
        comp.get("lib_id", ""), comp.get("value", ""), comp.get("description", ""))


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
            if _is_chip_select_net(net_name):
                if bus_id in ("0", "") or bus_id in nu.replace("_", ""):
                    cs_nets.append(net_name)
        spi_entry["chip_select_count"] = len(cs_nets)
        # SPI CS conflict: two or more slave CS inputs on one net (the controller drives it)
        cs_device_map = {}  # net_name -> [device_refs]
        for net_name in cs_nets:
            if net_name not in nets:
                continue
            slaves = set()
            for p in nets[net_name]["pins"]:
                comp = comp_lookup.get(p["component"])
                if (comp and comp["type"] == "ic" and (p.get("pin_type") or "") == "input"
                        and _ic_function(comp) not in ("mcu", "fpga")):
                    slaves.add(p["component"])
            if len(slaves) > 1:
                cs_device_map[net_name] = sorted(slaves)

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
    # (sheet_prefix, display_name.upper()) so a sheet-qualified net
    # (e.g. /s1/USB_P, display_name "USB_P") still pairs by name, but two
    # same-named nets on *different* sheets never cross-pair. Plain
    # assignment (not setdefault) preserves the earlier comprehension's
    # last-wins semantics on a case-insensitive collision: unqualified
    # boards must resolve a collision identically to the old
    # `{n.upper(): n for n in nets}` one-liner.
    net_names_upper: dict[tuple[str, str], str] = {}
    for k, v in nets.items():
        disp = v.get("display_name", k)
        if k.endswith(disp):
            prefix = k[: -len(disp)]
        elif k.startswith("/") and "display_name" in v:
            # A decoded display_name is not the key's tail; an escaped name has no '/'.
            prefix = k.rsplit("/", 1)[0] + "/"
        else:
            prefix = ""
        net_names_upper[(prefix, disp.upper())] = k
    found_pairs: set[tuple[str, str]] = set()  # track to avoid duplicates
    pair_suffixes = tuple(sfx.upper() for pair in _diff_suffix_pairs for sfx in pair)

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

                    # ESD protection: a clamp on each leg; a device on both lines is what it protects
                    pos_esd = {c for c in pos_comps
                               if is_protection_part(comp_lookup.get(c, {}), ctx, pair_suffixes)}
                    neg_esd = {c for c in neg_comps
                               if is_protection_part(comp_lookup.get(c, {}), ctx, pair_suffixes)}
                    entry["has_esd"] = bool(pos_esd and neg_esd)
                    if entry["has_esd"]:
                        entry["esd_protection"] = sorted(pos_esd | neg_esd)

                    # CAN-specific: check for termination resistor
                    if protocol == "CAN":
                        term_resistors = []
                        for c in components:
                            if c["type"] == "resistor":
                                r_n1 = pin_net.get((c["reference"], "1"), (None, None))[0]
                                r_n2 = pin_net.get((c["reference"], "2"), (None, None))[0]
                                if r_n1 and r_n2:
                                    if ({r_n1, r_n2} == {pos_real, neg_real}):
                                        term = {
                                            "ref": c["reference"],
                                            "value": c["value"],
                                            "ohms": parsed_values.get(c["reference"]),
                                        }
                                        if c.get("dnp"):
                                            term["dnp"] = True
                                        term_resistors.append(term)
                        entry["termination"] = term_resistors
                        entry["has_termination"] = any(not t.get("dnp") for t in term_resistors)

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


# PWR_FLAG symbols are not net pins here; KiCad counts their one power output pin.
_PWR_FLAG_PIN = {"component": "#FLG", "pin_number": "1", "pin_name": "pwr", "pin_type": "power_out"}


def _check_erc_warnings(ctx: AnalysisContext) -> list:
    """ERC records as KiCad 10 reports them with its default pin map and severities.

    Every net is checked (power, ground, unnamed and single-pin nets too), power-symbol
    pins included: pin_to_pin (pin map), no_driver / power_pin_not_driven (drive test,
    silenced by a no-connect marker) and no_connect_connected. NC-type pins only feed
    no_connect_connected: KiCad never joins them to a net (SCH_PIN::ConnectionPropagatesTo).
    """
    positions = erc_pins.pin_positions(getattr(ctx, "components", None) or [])
    erc_warnings = []

    for net_name, net_info in ctx.nets.items():
        pins = net_info["pins"]
        if net_info.get("has_pwr_flag"):
            pins = pins + [_PWR_FLAG_PIN]
        shown = unescape_string(net_name)
        all_pins = pins
        pins = [p for p in pins if erc_pins.pin_kind(p.get("pin_type")) != "no_connect"]
        real = [p for p in pins if not p["component"].startswith("#")]

        markers = erc_pins.pin_to_pin_markers(pins, positions)
        if markers:
            erc_warnings.append({
                "type": "pin_to_pin",
                "net": net_name,
                "severity": erc_pins.SEVERITY[max(m[2] for m in markers)],
                "message": f"Net '{shown}' connects conflicting pin types ({len(markers)} pin(s))",
                "pairs": [{
                    "pins": [f"{pins[i]['component']}.{pins[i]['pin_number']}",
                             f"{pins[j]['component']}.{pins[j]['pin_number']}"],
                    "pin_types": [erc_pins.pin_kind(pins[i].get("pin_type")),
                                  erc_pins.pin_kind(pins[j].get("pin_type"))],
                    "severity": erc_pins.SEVERITY[level],
                } for i, j, level in markers],
            })

        # A no-connect marker on the net silences the drive test (erc.cpp has_noconnect).
        undriven = None if net_info.get("_nc_marker") else erc_pins.undriven_kind(pins)
        if undriven == "pin_not_driven":
            erc_warnings.append({
                "type": "no_driver",
                "net": net_name,
                "severity": "error",
                "message": f"Net '{shown}' has input pins but no output driver",
                "pins": real,
            })
        elif undriven == "power_pin_not_driven":
            erc_warnings.append({
                "type": "power_pin_not_driven",
                "net": net_name,
                "severity": "error",
                "message": f"Net '{shown}' has power input pins but no power output driver",
                "pins": real,
            })

        if net_info.get("no_connect") and _no_connect_connected(all_pins, net_info, positions):
            erc_warnings.append({
                "type": "no_connect_connected",
                "net": net_name,
                "severity": "warning",
                "message": f"Net '{shown}' has a no-connect and other connections",
                "pins": [p for p in all_pins if not p["component"].startswith("#")],
            })

    return erc_warnings


def _no_connect_connected(pins: list[dict], net_info: dict, positions: dict) -> bool:
    """KiCad's no_connect_connected test for one net that carries a no-connect.

    An NC-type pin is a net of its own. It is connected when anything but a no-connect marker
    sits on its point (TestNoConnectPins): another pin, a wire end, a label; one record per
    point. A no-connect marker is connected when the net has more than one other pin, stacked
    pins counted once (ercCheckNoConnects).
    """
    if any(erc_pins.pin_kind(p.get("pin_type")) == "no_connect" for p in pins):
        return bool(net_info.get("_nc_touched"))
    if not net_info.get("_nc_marker"):
        return False
    unique: list[dict] = []
    for p in pins:
        if not any(erc_pins.is_stacked(p, q, positions) for q in unique):
            unique.append(p)
    return len(unique) > 1


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
                        v_est = abs(ctx.rail_voltage_or(net, _estimate_rail_voltage) or 0)
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
    nu = net_leaf(net_name).upper()
    if nu in ("GND", "VSS", "AGND", "DGND"):
        return 0
    v = _parse_voltage_from_net_name(net_name)
    if v is not None:
        return v
    # Hardcoded fallbacks for common names without voltage numbers
    if "VBUS" in nu:
        return 5.0
    # only non-data USB nets (VBUS-ish) default to 5V
    if "USB" in nu and not is_usb_data_net_name(nu):
        return 5.0
    return None
