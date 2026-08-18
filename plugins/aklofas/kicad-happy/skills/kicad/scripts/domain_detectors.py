"""
Domain-specific detector functions for specialized circuit blocks.

Identifies functional blocks (Ethernet, HDMI, RF, BMS, battery chargers,
motor drivers, etc.) by IC keyword matching and pin tracing. Separated from
signal_detectors.py which handles core passive/active circuit analysis
(filters, dividers, regulators, transistors).

Each detector takes an AnalysisContext (ctx) and returns its detection results.
"""

from __future__ import annotations

import re
from collections import Counter

from kicad_types import AnalysisContext
from kicad_utils import lookup_regulator_vref, parse_value, parse_voltage_from_net_name
from signal_detectors import _get_net_components
from detector_helpers import get_components_by_type, index_two_pin_components, match_ic_keywords, get_unique_ics
from finding_schema import make_finding, make_provenance


def detect_buzzer_speakers(ctx: AnalysisContext, transistor_circuits: list[dict]) -> list[dict]:
    """Detect buzzer/speaker driver circuits."""
    buzzer_speaker_circuits: list[dict] = []
    # Build index: net → transistor circuits that drive it
    tc_by_output_net: dict[str, list[dict]] = {}
    for tc in transistor_circuits:
        for key in ("drain_net", "collector_net"):
            n = tc.get(key)
            if n:
                tc_by_output_net.setdefault(n, []).append(tc)
    buzzer_speaker_types = ("buzzer", "speaker")
    for comp in ctx.components:
        if comp["type"] not in buzzer_speaker_types:
            continue
        ref = comp["reference"]
        # Find signal nets via direct pin lookup (buzzers/speakers are 2-pin)
        n1, n2 = ctx.get_two_pin_nets(ref)
        signal_net = None
        for net in (n1, n2):
            if net and not ctx.is_ground(net) and not ctx.is_power_net(net):
                signal_net = net
                break
        if not signal_net:
            continue
        net_comps = _get_net_components(ctx, signal_net, ref)
        driver_ic_ref = None
        series_resistor = None
        has_transistor_driver = False
        for nc in net_comps:
            if nc["type"] == "ic":
                driver_ic_ref = nc["reference"]
            elif nc["type"] == "resistor":
                series_resistor = nc
                # Follow resistor to see if IC is on the other side
                r_n1, r_n2 = ctx.get_two_pin_nets(nc["reference"])
                r_other = r_n2 if r_n1 == signal_net else r_n1
                if r_other:
                    for rc in _get_net_components(ctx, r_other, nc["reference"]):
                        if rc["type"] == "ic":
                            driver_ic_ref = rc["reference"]
            elif nc["type"] == "transistor":
                has_transistor_driver = True
        # Check indexed transistor circuits for this net
        for tc in tc_by_output_net.get(signal_net, []):
            has_transistor_driver = True
            if not driver_ic_ref and tc.get("gate_driver_ics"):
                driver_ic_ref = tc["gate_driver_ics"][0].get("reference", "")
        entry = {
            "reference": ref,
            "value": comp.get("value", ""),
            "type": comp["type"],
            "signal_net": signal_net,
            "has_transistor_driver": has_transistor_driver,
            "detector": "detect_buzzer_speakers",
            "rule_id": "BZ-DET",
            "category": "audio",
            "severity": "info",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "summary": f"{comp['type']} {ref} ({comp.get('value', '')}) on {signal_net}",
            "description": f"Detected {comp['type']} {ref} driven via {signal_net}.",
            "components": [ref],
            "nets": [signal_net] if signal_net else [],
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "Audio", "impact": "", "standard_ref": ""},
        }
        if driver_ic_ref:
            entry["driver_ic"] = driver_ic_ref
        if series_resistor:
            entry["series_resistor"] = {
                "reference": series_resistor["reference"],
                "value": series_resistor.get("value", ""),
            }
        if not has_transistor_driver and driver_ic_ref:
            entry["direct_gpio_drive"] = True
        entry["provenance"] = make_provenance("buzzer_topology", "deterministic", claimed_components=[ref])
        buzzer_speaker_circuits.append(entry)
    return buzzer_speaker_circuits


def detect_key_matrices(ctx: AnalysisContext) -> list[dict]:
    """Detect keyboard-style switch matrices."""
    key_matrices: list[dict] = []
    row_nets = {}
    col_nets = {}
    for net_name in ctx.nets:
        nn = net_name.upper().replace("_", "").replace("-", "").replace(" ", "")
        m_row = re.match(r'^ROW(\d+)$', nn)
        m_col = re.match(r'^COL(\d+)$', nn)
        if not m_row:
            m_row = re.match(r'^ROW(\d+)$', net_name.upper())
        if not m_col:
            m_col = re.match(r'^COL(?:UMN)?(\d+)$', net_name.upper())
        if m_row:
            row_nets[int(m_row.group(1))] = net_name
        elif m_col:
            col_nets[int(m_col.group(1))] = net_name

    if row_nets and col_nets:
        switch_count = 0
        diode_count = 0
        counted_refs: set[str] = set()
        for net_name in list(row_nets.values()) + list(col_nets.values()):
            if net_name in ctx.nets:
                for p in ctx.nets[net_name]["pins"]:
                    ref = p["component"]
                    if ref in counted_refs:
                        continue
                    comp = ctx.comp_lookup.get(ref)
                    if comp:
                        if comp["type"] == "switch":
                            switch_count += 1
                            counted_refs.add(ref)
                        elif comp["type"] == "diode":
                            diode_count += 1
                            counted_refs.add(ref)
        estimated_keys = max(switch_count, diode_count)
        if estimated_keys > 4 and row_nets and col_nets:
            key_matrices.append({
                "rows": len(row_nets),
                "columns": len(col_nets),
                "row_nets": list(row_nets.values()),
                "col_nets": list(col_nets.values()),
                "estimated_keys": estimated_keys,
                "switches_on_matrix": switch_count,
                "diodes_on_matrix": diode_count,
                "detection_method": "net_name",
                "detector": "detect_key_matrices",
                "rule_id": "KM-DET",
                "category": "human_interface",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Key matrix {len(row_nets)}x{len(col_nets)} ({estimated_keys} keys)",
                "description": f"Detected {len(row_nets)}x{len(col_nets)} key matrix with {estimated_keys} estimated keys.",
                "components": [],
                "nets": list(row_nets.values()) + list(col_nets.values()),
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Human Interface", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("keymatrix_diode_grid", "deterministic"),
            })

    # Topology-based detection: find switch-diode pairs and group by shared nets
    # to identify rows/columns regardless of net naming.
    if not key_matrices:
        # KH-152: Exclude solar cells and similar power-generation components
        switches = [c for c in ctx.components if c["type"] == "switch"
                    and "solar" not in c.get("lib_id", "").lower()
                    and "solar_cell" not in c.get("value", "").lower()]
        if len(switches) >= 4:
            # For each switch, find if either net has a diode (switch-diode pair)
            # KH-197b: Track paired switches to avoid double-counting
            switch_diode_pairs = []
            paired_switches: set[str] = set()
            for sw in switches:
                if sw["reference"] in paired_switches:
                    continue
                sn1, sn2 = ctx.get_two_pin_nets(sw["reference"])
                if not sn1 or not sn2:
                    continue
                # Check both nets for connected diodes
                found_pair = False
                for sw_net, other_net in ((sn1, sn2), (sn2, sn1)):
                    if found_pair:
                        break
                    if sw_net not in ctx.nets:
                        continue
                    for p in ctx.nets[sw_net]["pins"]:
                        comp = ctx.comp_lookup.get(p["component"])
                        if comp and comp["type"] == "diode" and p["component"] != sw["reference"]:
                            # Found a switch-diode pair: diode's other net = row, sw's other net = col
                            dn1, dn2 = ctx.get_two_pin_nets(p["component"])
                            diode_other = dn2 if dn1 == sw_net else dn1
                            if diode_other and diode_other != other_net:
                                switch_diode_pairs.append({
                                    "switch": sw["reference"],
                                    "diode": p["component"],
                                    "row_net": diode_other,
                                    "col_net": other_net,
                                })
                                paired_switches.add(sw["reference"])
                                found_pair = True
                            break
            # Group by row/col nets
            if len(switch_diode_pairs) >= 4:
                topo_row_nets = set()
                topo_col_nets = set()
                for pair in switch_diode_pairs:
                    topo_row_nets.add(pair["row_net"])
                    topo_col_nets.add(pair["col_net"])
                # KH-152: Reject if row/col nets are power rails
                topo_row_nets = {n for n in topo_row_nets
                                 if not ctx.is_power_net(n) and not ctx.is_ground(n)}
                topo_col_nets = {n for n in topo_col_nets
                                 if not ctx.is_power_net(n) and not ctx.is_ground(n)}
                # KH-197c: Resolve ambiguous nets that appear in both sets
                ambiguous = topo_row_nets & topo_col_nets
                if ambiguous:
                    row_votes = Counter(p["row_net"] for p in switch_diode_pairs)
                    col_votes = Counter(p["col_net"] for p in switch_diode_pairs)
                    for net in ambiguous:
                        if row_votes.get(net, 0) > col_votes.get(net, 0):
                            topo_col_nets.discard(net)
                        elif col_votes.get(net, 0) > row_votes.get(net, 0):
                            topo_row_nets.discard(net)
                        else:
                            # Tie — remove from both
                            topo_row_nets.discard(net)
                            topo_col_nets.discard(net)
                if len(topo_row_nets) >= 2 and len(topo_col_nets) >= 2:
                    key_matrices.append({
                        "rows": len(topo_row_nets),
                        "columns": len(topo_col_nets),
                        "row_nets": sorted(topo_row_nets),
                        "col_nets": sorted(topo_col_nets),
                        "estimated_keys": len(switch_diode_pairs),
                        "switches_on_matrix": len(switch_diode_pairs),
                        "diodes_on_matrix": len(switch_diode_pairs),
                        "detection_method": "topology",
                        "detector": "detect_key_matrices",
                        "rule_id": "KM-DET",
                        "category": "human_interface",
                        "severity": "info",
                        "confidence": "deterministic",
                        "evidence_source": "topology",
                        "summary": f"Key matrix {len(topo_row_nets)}x{len(topo_col_nets)} ({len(switch_diode_pairs)} keys, topology)",
                        "description": f"Detected {len(topo_row_nets)}x{len(topo_col_nets)} key matrix via topology analysis.",
                        "components": [],
                        "nets": sorted(topo_row_nets) + sorted(topo_col_nets),
                        "pins": [],
                        "recommendation": "",
                        "report_context": {"section": "Human Interface", "impact": "", "standard_ref": ""},
                        "provenance": make_provenance("keymatrix_diode_grid", "deterministic"),
                    })

    return key_matrices


def detect_isolation_barriers(ctx: AnalysisContext) -> list[dict]:
    """Detect galvanic isolation domains."""
    isolation_barriers: list[dict] = []

    # Find ground domains (include PE/Earth for isolation detection)
    ground_nets = [n for n in ctx.nets if ctx.is_ground(n)
                   or n.upper() in ("PE", "EARTH", "CHASSIS", "SHIELD")]
    if len(ground_nets) >= 2:
        ground_domains = {}
        for gn in ground_nets:
            gnu = gn.upper()
            if gnu in ("PE", "EARTH", "CHASSIS", "SHIELD"):
                domain = gnu.lower()
            else:
                domain = gnu.replace("GND", "").replace("_", "").replace("-", "").strip()
                if not domain:
                    domain = "main"
            ground_domains.setdefault(domain, []).append(gn)

        if len(ground_domains) >= 2:
            iso_keywords = (
                "adum", "iso7", "iso15", "adm268", "adm248",
                "optocoupl", "opto_isolat", "pc817", "tlp",
                "isolated", "isol_dc", "traco", "recom", "murata",
                "dcdc_iso", "r1sx", "am1s", "tmu", "iec",
            )

            isolation_components = []
            for c in ctx.components:
                val = (c.get("value", "") + " " + c.get("lib_id", "")).lower()
                if any(k in val for k in iso_keywords) or c["type"] == "optocoupler":
                    isolation_components.append({
                        "reference": c["reference"],
                        "value": c["value"],
                        "type": c["type"],
                        "lib_id": c.get("lib_id", ""),
                    })

            ground_domain_map = {}
            for gn in ground_nets:
                domain = gn.upper().replace("GND", "").replace("_", "").replace("-", "").strip()
                if not domain:
                    domain = "main"
                ground_domain_map[gn] = domain

            isolated_power_rails = [
                n for n in ctx.nets
                if ctx.is_power_net(n) and any(
                    k in n.upper() for k in ("ISO", "ISOL", "_B", "_SEC")
                )
            ]

            has_iso_evidence = (
                isolation_components
                or isolated_power_rails
                or any("ISO" in d.upper() for d in ground_domains if d != "main")
            )
            if has_iso_evidence:
                # Shared ground detection: check if any ground net
                # appears on both sides of an isolation component
                shared_ground_warnings: list[dict] = []
                for iso_comp in isolation_components:
                    iso_ref = iso_comp["reference"]
                    iso_pins = ctx.ref_pins.get(iso_ref, {})
                    if len(iso_pins) < 4:
                        continue
                    # Split pins into primary/secondary halves.
                    # Prefer VDD/GND pin names to identify sides (works for
                    # asymmetric parts like ADuM1201).  Fall back to
                    # pin-number bisection for parts without named power pins.
                    pin_nums = sorted(iso_pins.keys(),
                                      key=lambda x: int(x) if x.isdigit() else 0)
                    # Try name-based side detection: VDD1/GND1 = side A, VDD2/GND2 = side B
                    side_a_pins: list[str] = []
                    side_b_pins: list[str] = []
                    comp_obj = ctx.comp_lookup.get(iso_ref, {})
                    for pin in comp_obj.get("pins", []):
                        pname = pin.get("name", "").upper()
                        pnum = pin.get("number", "")
                        if any(pname.endswith(s) for s in ("1", "A", "_A", "_IN")):
                            side_a_pins.append(pnum)
                        elif any(pname.endswith(s) for s in ("2", "B", "_B", "_OUT")):
                            side_b_pins.append(pnum)
                    # Fall back to pin-number bisection if name detection didn't split
                    if not side_a_pins or not side_b_pins:
                        mid = len(pin_nums) // 2
                        side_a_pins = pin_nums[:mid]
                        side_b_pins = pin_nums[mid:]
                    # Collect ground nets reachable from each side (1 hop)
                    primary_grounds: set[str] = set()
                    secondary_grounds: set[str] = set()
                    for pnum in side_a_pins:
                        net, _ = iso_pins.get(pnum, (None, None))
                        if net and ctx.is_ground(net):
                            primary_grounds.add(net)
                    for pnum in side_b_pins:
                        net, _ = iso_pins.get(pnum, (None, None))
                        if net and ctx.is_ground(net):
                            secondary_grounds.add(net)
                    shared = primary_grounds & secondary_grounds
                    if shared:
                        shared_ground_warnings.append({
                            "isolation_component": iso_ref,
                            "shared_ground_nets": sorted(shared),
                        })

                iso_refs = [c["reference"] for c in isolation_components]
                entry = {
                    "ground_domains": {d: gnets for d, gnets in ground_domains.items()},
                    "isolation_components": isolation_components,
                    "isolated_power_rails": isolated_power_rails,
                    "pcb_advisory": (
                        "Isolation barrier detected — verify creepage/clearance "
                        "on PCB layout (IEC 60664-1)"
                    ),
                    "detector": "detect_isolation_barriers",
                    "rule_id": "IB-DET",
                    "category": "isolation",
                    "severity": "info",
                    "confidence": "deterministic",
                    "evidence_source": "topology",
                    "summary": f"Isolation barrier: {len(ground_domains)} ground domains, {len(isolation_components)} isolation component(s)",
                    "description": f"Detected galvanic isolation with {len(ground_domains)} ground domains.",
                    "components": iso_refs,
                    "nets": isolated_power_rails,
                    "pins": [],
                    "recommendation": "",
                    "report_context": {"section": "Isolation", "impact": "", "standard_ref": ""},
                }
                if shared_ground_warnings:
                    entry["shared_ground_warnings"] = shared_ground_warnings
                _iso_evidence = "isolation_optocoupler" if any(
                    ic.get("type") == "optocoupler" for ic in isolation_components
                ) else "isolation_digital"
                entry["provenance"] = make_provenance(_iso_evidence, "deterministic", claimed_components=iso_refs)
                isolation_barriers.append(entry)
    return isolation_barriers


def detect_ethernet_interfaces(ctx: AnalysisContext) -> list[dict]:
    """Detect Ethernet PHY + magnetics + connector chains."""
    ethernet_interfaces: list[dict] = []

    eth_phy_keywords = (
        "lan87", "lan91", "lan83", "dp838", "ksz8", "ksz9",
        "rtl81", "rtl83", "rtl88", "w5500", "w5100", "w5200",
        "enc28j60", "enc424", "dm9000", "ip101", "phy",
        "ethernet", "10base", "100base", "1000base",
    )
    magnetics_keywords = (
        "magnetics", "pulse", "transformer", "lan_tr", "rj45_mag",
        "hx1188", "hr601680", "g2406", "h5007",
    )

    eth_phys = []
    eth_magnetics = []
    eth_connectors = []
    seen_eth_refs = set()

    for c in ctx.components:
        if c["reference"] in seen_eth_refs:
            continue
        val_lib = (c.get("value", "") + " " + c.get("lib_id", "")).lower()
        if c["type"] == "ic" and any(k in val_lib for k in eth_phy_keywords):
            eth_phys.append(c)
            seen_eth_refs.add(c["reference"])
        elif c["type"] == "transformer" and any(k in val_lib for k in magnetics_keywords):
            eth_magnetics.append(c)
            seen_eth_refs.add(c["reference"])
        elif c["type"] == "connector":
            # Also detect by LAN reference prefix or integrated magnetics RJ45 part numbers
            if (any(k in val_lib for k in ("rj45", "8p8c", "ethernet", "magjack",
                                            "lpj4", "lpj0", "hr911", "hfj11",
                                            "arjp", "rjlbc"))
                    or c["reference"].upper().startswith("LAN")):
                eth_connectors.append(c)
                seen_eth_refs.add(c["reference"])

    # BFS from each PHY's TX/RX pins through transformers/CMCs/
    # resistors/caps to find linked magnetics and connectors (max 4 hops).
    # Includes both MII differential pairs and RMII single-ended signals.
    _eth_tx_rx_re = re.compile(
        r'(TXP|TXN|TX\+|TX-|TXD\+|TXD-|RXP|RXN|RX\+|RX-|RXD\+|RXD-|'
        r'TD\+|TD-|RD\+|RD-|MDI\d|'
        r'TXD\d|RXD\d|TXEN|TX_EN|CRS_DV|COL|REF_CLK|MDIO|MDC)', re.IGNORECASE)
    # Net name patterns for RMII/MII (fallback when PHY has no parsed pins)
    _eth_net_re = re.compile(
        r'(EMAC_TX|EMAC_RX|_TXD\d|_RXD\d|RMII|_MDIO|_MDC|TX_EN|CRS_DV|'
        r'TXP|TXN|RXP|RXN|MDI\d|TD\+|TD-|RD\+|RD-)', re.IGNORECASE)
    if eth_phys:
        eth_mag_refs = {m["reference"] for m in eth_magnetics}
        eth_conn_refs = {c["reference"] for c in eth_connectors}
        for phy in eth_phys:
            # Gather PHY TX/RX pin nets
            phy_diff_nets = set()
            for pin in phy.get("pins", []):
                pname = pin.get("name", "")
                if _eth_tx_rx_re.match(pname):
                    net_name, _ = ctx.pin_net.get(
                        (phy["reference"], pin["number"]), (None, None))
                    if net_name and not ctx.is_ground(net_name) and not ctx.is_power_net(net_name):
                        phy_diff_nets.add(net_name)
            # Fallback: when PHY pins are empty, scan nets for the PHY ref
            # and match on pin name or net name patterns
            if not phy_diff_nets:
                phy_ref = phy["reference"]
                for net_name, ndata in ctx.nets.items():
                    if ctx.is_ground(net_name) or ctx.is_power_net(net_name):
                        continue
                    for p in ndata.get("pins", []):
                        if p.get("component") == phy_ref:
                            pname = p.get("pin_name", "")
                            if _eth_tx_rx_re.match(pname) or _eth_net_re.search(net_name):
                                phy_diff_nets.add(net_name)
                                break

            # BFS outward through passives, transformers, CMCs
            visited_nets = set(phy_diff_nets)
            visited_refs = {phy["reference"]}
            found_magnetics = []
            found_connectors = []
            frontier = list(phy_diff_nets)

            for _ in range(4):  # max 4 hops
                if not frontier:
                    break
                next_frontier = []
                for net_name in frontier:
                    if net_name not in ctx.nets:
                        continue
                    for p in ctx.nets[net_name]["pins"]:
                        cref = p["component"]
                        if cref in visited_refs:
                            continue
                        comp = ctx.comp_lookup.get(cref)
                        if not comp:
                            continue
                        visited_refs.add(cref)
                        if cref in eth_mag_refs:
                            found_magnetics.append(comp)
                        elif cref in eth_conn_refs:
                            found_connectors.append(comp)
                        # Traverse through passives, transformers, ferrite beads
                        if comp["type"] in ("resistor", "capacitor", "inductor",
                                            "ferrite_bead", "transformer"):
                            # Follow all nets this component touches
                            for cpin in comp.get("pins", []):
                                cn, _ = ctx.pin_net.get(
                                    (cref, cpin["number"]), (None, None))
                                if cn and cn not in visited_nets:
                                    if not ctx.is_power_net(cn):
                                        visited_nets.add(cn)
                                        next_frontier.append(cn)
                            # Also try 2-pin approach
                            cn1, cn2 = ctx.get_two_pin_nets(cref)
                            for cn in (cn1, cn2):
                                if cn and cn not in visited_nets and not ctx.is_power_net(cn):
                                    visited_nets.add(cn)
                                    next_frontier.append(cn)
                        elif comp["type"] == "connector" and cref in eth_conn_refs:
                            pass  # already captured
                frontier = next_frontier

            # Fall back to global lists if BFS found nothing
            if not found_magnetics:
                found_magnetics = eth_magnetics
            if not found_connectors:
                found_connectors = eth_connectors

            # Bob Smith termination: ~75Ω from transformer center tap via cap to chassis GND
            # Reduces common-mode noise on Ethernet cable for EMC compliance
            bob_smith = None
            for mag in found_magnetics:
                if bob_smith:
                    break
                mag_ref = mag["reference"]
                # Check all nets this transformer connects to
                for (ref, pnum), (net_name, _) in ctx.pin_net.items():
                    if ref != mag_ref or not net_name:
                        continue
                    if ctx.is_power_net(net_name) or ctx.is_ground(net_name):
                        continue
                    if net_name not in ctx.nets:
                        continue
                    # Look for a ~75Ω resistor on this net
                    for p in ctx.nets[net_name]["pins"]:
                        rc = ctx.comp_lookup.get(p["component"])
                        if not rc or rc["type"] != "resistor":
                            continue
                        r_val = ctx.parsed_values.get(p["component"])
                        if not r_val or not (60 <= r_val <= 100):  # 75Ω ±33%
                            continue
                        # Check if the other end goes to ground (direct or via cap)
                        rn1, rn2 = ctx.get_two_pin_nets(p["component"])
                        r_other = rn2 if rn1 == net_name else rn1
                        if not r_other:
                            continue
                        if ctx.is_ground(r_other):
                            bob_smith = {
                                "resistor_ref": p["component"],
                                "resistor_value": rc.get("value", ""),
                                "ohms": r_val,
                                "transformer_ref": mag_ref,
                            }
                            break
                        # Check for cap in between (R → cap → GND)
                        if r_other in ctx.nets:
                            for cp in ctx.nets[r_other]["pins"]:
                                cc = ctx.comp_lookup.get(cp["component"])
                                if cc and cc["type"] == "capacitor":
                                    cn1, cn2 = ctx.get_two_pin_nets(cp["component"])
                                    c_other = cn2 if cn1 == r_other else cn1
                                    if c_other and ctx.is_ground(c_other):
                                        bob_smith = {
                                            "resistor_ref": p["component"],
                                            "resistor_value": rc.get("value", ""),
                                            "ohms": r_val,
                                            "cap_ref": cp["component"],
                                            "cap_value": cc.get("value", ""),
                                            "transformer_ref": mag_ref,
                                        }
                                        break
                        if bob_smith:
                            break
                    if bob_smith:
                        break

            # Impedance advisory: magnetics provide both isolation and 100Ω
            # differential impedance matching for Ethernet
            has_magnetics = bool(found_magnetics)
            if not has_magnetics:
                impedance_advisory = {
                    "status": "warning",
                    "detail": ("No magnetics/transformer detected between PHY and connector. "
                               "Ethernet requires magnetic isolation and impedance matching "
                               "(100\u03A9 differential)."),
                }
            else:
                impedance_advisory = {
                    "status": "pass",
                    "detail": "Magnetics present for impedance matching and isolation",
                }

            eth_comps = [phy["reference"]] + [m["reference"] for m in found_magnetics] + [c["reference"] for c in found_connectors]
            ethernet_interfaces.append({
                "phy_reference": phy["reference"],
                "phy_value": phy["value"],
                "phy_lib_id": phy.get("lib_id", ""),
                "magnetics": [
                    {"reference": m["reference"], "value": m["value"]}
                    for m in found_magnetics
                ],
                "connectors": [
                    {"reference": c["reference"], "value": c["value"]}
                    for c in found_connectors
                ],
                "bob_smith_termination": bob_smith,
                "impedance_advisory": impedance_advisory,
                "detector": "detect_ethernet_interfaces",
                "rule_id": "ET-DET",
                "category": "networking",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Ethernet PHY {phy['reference']} ({phy['value']})",
                "description": f"Detected Ethernet interface with PHY {phy['reference']}.",
                "components": eth_comps,
                "nets": [],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Networking", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("eth_phy_magjack", "deterministic", claimed_components=[phy["reference"]]),
            })
    return ethernet_interfaces


def detect_hdmi_dvi_interfaces(ctx: AnalysisContext) -> list[dict]:
    """Detect HDMI/DVI interfaces: bridge ICs, connectors, PIO-DVI patterns."""
    hdmi_dvi: list[dict] = []

    # Bridge IC detection by part number
    _bridge_kw = (
        "lt8912", "it6613", "it6616", "it6632", "it6635",
        "adv7533", "adv7511", "adv7513", "adv7612",
        "ch7033", "ch7034", "ch7055",
        "sii9022", "sii9024", "sil9022", "sil9024",
        "tfp410", "tfp401",
        "anx7580", "anx7688",
        "it68051", "it66121",
    )
    for comp in ctx.components:
        if comp["type"] != "ic":
            continue
        val_lib = (comp.get("value", "") + " " + comp.get("lib_id", "")).lower()
        if any(k in val_lib for k in _bridge_kw):
            hdmi_dvi.append({
                "type": "bridge_ic",
                "reference": comp["reference"],
                "value": comp.get("value", ""),
                "detector": "detect_hdmi_dvi_interfaces",
                "rule_id": "HD-DET",
                "category": "video",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"HDMI/DVI bridge IC {comp['reference']} ({comp.get('value', '')})",
                "description": f"Detected HDMI/DVI bridge IC {comp['reference']}.",
                "components": [comp["reference"]],
                "nets": [],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Video", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("hdmi_tmds_topology", "deterministic", claimed_components=[comp["reference"]]),
            })

    # HDMI/DVI connector detection
    _hdmi_conn_kw = ("hdmi", "dvi", "tmds")
    hdmi_connectors = []
    for comp in ctx.components:
        if comp["type"] != "connector":
            continue
        val_lib = (comp.get("value", "") + " " + comp.get("lib_id", "")).lower()
        if any(k in val_lib for k in _hdmi_conn_kw):
            hdmi_connectors.append(comp)

    # PIO-DVI pattern: connector with 8+ series resistors (10-330R)
    # indicating RP2040/RP2350 PIO-driven DVI
    for conn in hdmi_connectors:
        # Count series resistors connected to connector pins
        series_resistors = []
        seen_refs = set()
        for pin in conn.get("pins", []):
            net_name, _ = ctx.pin_net.get(
                (conn["reference"], pin["number"]), (None, None))
            if not net_name or ctx.is_ground(net_name) or ctx.is_power_net(net_name):
                continue
            if net_name not in ctx.nets:
                continue
            for p in ctx.nets[net_name]["pins"]:
                if p["component"] == conn["reference"]:
                    continue
                comp = ctx.comp_lookup.get(p["component"])
                if not comp or comp["type"] != "resistor":
                    continue
                if comp["reference"] in seen_refs:
                    continue
                rv = ctx.parsed_values.get(comp["reference"])
                if rv and 10 <= rv <= 330:
                    series_resistors.append(comp["reference"])
                    seen_refs.add(comp["reference"])

        if len(series_resistors) >= 8:
            # Check if already captured by bridge IC detection
            already = any(e.get("connector") == conn["reference"] for e in hdmi_dvi)
            if not already:
                hdmi_dvi.append({
                    "type": "pio_dvi",
                    "connector": conn["reference"],
                    "connector_value": conn.get("value", ""),
                    "series_resistors": len(series_resistors),
                    "detector": "detect_hdmi_dvi_interfaces",
                    "rule_id": "HD-DET",
                    "category": "video",
                    "severity": "info",
                    "confidence": "deterministic",
                    "evidence_source": "topology",
                    "summary": f"PIO-DVI connector {conn['reference']} ({conn.get('value', '')})",
                    "description": f"Detected PIO-DVI pattern on connector {conn['reference']}.",
                    "components": [conn["reference"]],
                    "nets": [],
                    "pins": [],
                    "recommendation": "",
                    "report_context": {"section": "Video", "impact": "", "standard_ref": ""},
                    "provenance": make_provenance("hdmi_tmds_topology", "deterministic", claimed_components=[conn["reference"]]),
                })
        elif not any(e.get("connector") == conn["reference"] for e in hdmi_dvi):
            hdmi_dvi.append({
                "type": "hdmi_connector",
                "connector": conn["reference"],
                "connector_value": conn.get("value", ""),
                "detector": "detect_hdmi_dvi_interfaces",
                "rule_id": "HD-DET",
                "category": "video",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"HDMI/DVI connector {conn['reference']} ({conn.get('value', '')})",
                "description": f"Detected HDMI/DVI connector {conn['reference']}.",
                "components": [conn["reference"]],
                "nets": [],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Video", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("hdmi_tmds_topology", "deterministic", claimed_components=[conn["reference"]]),
            })

    # TMDS differential termination check: look for ~100Ω resistors on
    # TMDS data/clock nets connected to HDMI connectors or bridge ICs
    _tmds_pin_re = re.compile(
        r'(TMDS|D\d[+-]|CLK[+-]|CK[+-]|HPD|HDMI_D|HDMI_CLK|DVI_D|DVI_CLK)',
        re.IGNORECASE)
    for entry in hdmi_dvi:
        # Determine the component reference to scan
        comp_ref = entry.get("reference") or entry.get("connector")
        if not comp_ref:
            continue
        comp = ctx.comp_lookup.get(comp_ref)
        if not comp:
            continue

        # Gather signal nets from this component's TMDS-related pins
        tmds_nets: set[str] = set()
        for pin in comp.get("pins", []):
            pname = pin.get("name", "")
            if _tmds_pin_re.search(pname):
                net_name, _ = ctx.pin_net.get(
                    (comp_ref, pin["number"]), (None, None))
                if net_name and not ctx.is_ground(net_name) and not ctx.is_power_net(net_name):
                    tmds_nets.add(net_name)
        # Fallback: scan nets for pin names or TMDS-related net names
        if not tmds_nets:
            _tmds_net_re = re.compile(r'(TMDS|HDMI_D|HDMI_CLK|DVI_D)', re.IGNORECASE)
            for net_name, ndata in ctx.nets.items():
                if ctx.is_ground(net_name) or ctx.is_power_net(net_name):
                    continue
                for p in ndata.get("pins", []):
                    if p.get("component") == comp_ref:
                        pname = p.get("pin_name", "")
                        if _tmds_pin_re.search(pname) or _tmds_net_re.search(net_name):
                            tmds_nets.add(net_name)
                            break

        # Search for termination resistors (80–120Ω) on those nets
        term_resistors: list[dict] = []
        seen_term_refs: set[str] = set()
        for net_name in tmds_nets:
            if net_name not in ctx.nets:
                continue
            for p in ctx.nets[net_name]["pins"]:
                rc = ctx.comp_lookup.get(p["component"])
                if not rc or rc["type"] != "resistor":
                    continue
                if rc["reference"] in seen_term_refs:
                    continue
                rv = ctx.parsed_values.get(rc["reference"])
                if rv and 80 <= rv <= 120:
                    term_resistors.append({
                        "reference": rc["reference"],
                        "value": rc.get("value", ""),
                        "ohms": rv,
                    })
                    seen_term_refs.add(rc["reference"])

        if term_resistors:
            entry["termination"] = {
                "status": "pass",
                "detail": f"{len(term_resistors)} termination resistor(s) found on TMDS nets",
                "resistors": term_resistors,
            }
        elif tmds_nets:
            entry["termination"] = {
                "status": "warning",
                "detail": ("No ~100\u03A9 differential termination resistors detected "
                           "on TMDS nets. HDMI/DVI requires 100\u03A9 differential "
                           "impedance matching."),
            }
        # If no TMDS nets were identified, skip termination check silently

    return hdmi_dvi


def detect_lvds_interfaces(ctx: AnalysisContext) -> list[dict]:
    """Detect LVDS serializer/deserializer ICs and flag impedance requirements."""
    lvds_interfaces: list[dict] = []

    _lvds_keywords = (
        "ds90", "fpdlink", "fpd-link", "fpd_link", "lvds",
        "sn65lvds", "thc63", "max9217", "max9247",
        "ub924", "ub925",
    )
    _serializer_hints = ("ser", "driver", "transmit", "tx", "encoder", "ub925")
    _deserializer_hints = ("des", "receiver", "rx", "decoder", "ub924")

    for comp in ctx.components:
        if comp["type"] != "ic":
            continue
        val_lib = (comp.get("value", "") + " " + comp.get("lib_id", "")).lower()
        if not any(k in val_lib for k in _lvds_keywords):
            continue

        # Classify role
        role = "unknown"
        if any(h in val_lib for h in _serializer_hints):
            role = "serializer"
        elif any(h in val_lib for h in _deserializer_hints):
            role = "deserializer"
        else:
            # Heuristic: DS90Cx8xx — even last digit = serializer, odd = deserializer
            # e.g., DS90C124 (ser), DS90C125 (des), DS90CR286 (ser), DS90CF386 (des)
            # Not perfectly reliable, so leave as "unknown" if no strong hint
            pass

        lvds_interfaces.append({
            "reference": comp["reference"],
            "value": comp.get("value", ""),
            "lib_id": comp.get("lib_id", ""),
            "role": role,
            "impedance_required": "100\u03A9 differential (LVDS standard)",
            "detector": "detect_lvds_interfaces",
            "rule_id": "LV-DET",
            "category": "video",
            "severity": "info",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "summary": f"LVDS {role} {comp['reference']} ({comp.get('value', '')})",
            "description": f"Detected LVDS {role} IC {comp['reference']}.",
            "components": [comp["reference"]],
            "nets": [],
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "Video", "impact": "", "standard_ref": ""},
            "provenance": make_provenance("lvds_pair_topology", "deterministic", claimed_components=[comp["reference"]]),
        })

    return lvds_interfaces


def detect_memory_interfaces(ctx: AnalysisContext) -> list[dict]:
    """Detect memory ICs paired with MCUs/FPGAs."""
    memory_interfaces: list[dict] = []

    memory_keywords = (
        "sram", "dram", "ddr", "sdram", "psram", "flash", "eeprom",
        "w25q", "at25", "mx25", "is62", "is66", "cy62", "as4c",
        "mt41", "mt48", "k4b", "hy57", "is42", "25lc", "24lc",
        "at24", "fram", "fm25", "mb85", "s27k", "hyperram",
        "aps6404", "aps1604", "ly68",
    )
    processor_types = ("ic",)
    processor_keywords = (
        "stm32", "esp32", "rp2040", "atmega", "atsamd", "pic", "nrf5",
        "ice40", "ecp5", "artix", "spartan", "cyclone", "max10",
        "fpga", "mcu", "cortex", "risc",
    )

    memory_ics = []
    processor_ics = []
    seen_mem_refs = set()
    seen_proc_refs = set()
    for c in ctx.components:
        val_lib = (c.get("value", "") + " " + c.get("lib_id", "")).lower()
        if c["type"] == "ic":
            if any(k in val_lib for k in memory_keywords):
                if c["reference"] not in seen_mem_refs:
                    memory_ics.append(c)
                    seen_mem_refs.add(c["reference"])
            elif any(k in val_lib for k in processor_keywords):
                if c["reference"] not in seen_proc_refs:
                    processor_ics.append(c)
                    seen_proc_refs.add(c["reference"])

    for mem in memory_ics:
        mem_nets = {net for net, _ in ctx.ref_pins.get(mem["reference"], {}).values() if net}

        connected_processors = []
        for proc in processor_ics:
            proc_nets = {net for net, _ in ctx.ref_pins.get(proc["reference"], {}).values() if net}
            shared = mem_nets & proc_nets
            signal_shared = [n for n in shared if not ctx.is_power_net(n) and not ctx.is_ground(n)]
            if signal_shared:
                connected_processors.append({
                    "reference": proc["reference"],
                    "value": proc["value"],
                    "shared_signal_nets": len(signal_shared),
                })

        if connected_processors:
            proc_refs = [p["reference"] for p in connected_processors]
            memory_interfaces.append({
                "memory_reference": mem["reference"],
                "memory_value": mem["value"],
                "memory_lib_id": mem.get("lib_id", ""),
                "connected_processors": connected_processors,
                "total_pins": len(mem_nets),
                "detector": "detect_memory_interfaces",
                "rule_id": "MI-DET",
                "category": "memory",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Memory {mem['reference']} ({mem['value']}) connected to {len(connected_processors)} processor(s)",
                "description": f"Detected memory IC {mem['reference']} paired with processor(s).",
                "components": [mem["reference"]] + proc_refs,
                "nets": [],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Memory", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("memory_ic_topology", "deterministic", claimed_components=[mem["reference"]]),
            })
    return memory_interfaces


# RF IC frequency bands — maps lowercase keyword prefixes to operating frequency
RF_IC_BANDS = {
    "cc2500": {"freq_hz": 2.4e9, "band": "2.4GHz ISM"},
    "cc1101": {"freq_hz": 868e6, "band": "sub-GHz ISM"},
    "sx127": {"freq_hz": 868e6, "band": "LoRa sub-GHz"},
    "sx126": {"freq_hz": 868e6, "band": "LoRa sub-GHz"},
    "nrf24": {"freq_hz": 2.4e9, "band": "2.4GHz"},
    "nrf52": {"freq_hz": 2.4e9, "band": "2.4GHz BLE"},
    "nrf53": {"freq_hz": 2.4e9, "band": "2.4GHz BLE"},
    "esp32": {"freq_hz": 2.4e9, "band": "2.4GHz WiFi/BLE"},
    "at86rf": {"freq_hz": 2.4e9, "band": "802.15.4"},
    "si446": {"freq_hz": 868e6, "band": "sub-GHz"},
    "si4432": {"freq_hz": 868e6, "band": "sub-GHz"},
    "si4463": {"freq_hz": 868e6, "band": "sub-GHz"},
    "a7105": {"freq_hz": 2.4e9, "band": "2.4GHz"},
    "bk4819": {"freq_hz": 430e6, "band": "UHF"},
    "rfm9": {"freq_hz": 868e6, "band": "LoRa"},
    "rfm6": {"freq_hz": 868e6, "band": "FSK"},
}

# Heuristic gain/loss per RF component role (dB)
RF_ROLE_GAIN_DB = {
    "amplifier": 15.0,
    "switch": -0.5,
    "filter": -1.5,
    "balun": -0.5,
    "mixer": -7.0,
    "attenuator": -6.0,
    "coupler": -10.0,
    "power_detector": -20.0,
    "freq_multiplier": -10.0,
    "transceiver": 0.0,
}


def detect_rf_chains(ctx: AnalysisContext) -> list[dict]:
    """Detect RF signal chain components."""
    rf_chains: list[dict] = []

    rf_switch_keywords = (
        "sky134", "sky133", "sky131", "pe42", "as179", "as193",
        "hmc19", "hmc54", "hmc34", "bgrf", "rfsw", "spdt", "sp3t", "sp4t",
        "adrf", "hmc3",
    )
    rf_mixer_keywords = (
        "rffc50", "ltc5549", "lt5560", "hmc21", "sa612", "ade-", "tuf-",
        "mixer",
    )
    rf_amp_keywords = (
        "mga-", "bga-", "maal", "pga-", "gali-", "maa-", "bfp7", "bfr5",
        "hmc58", "hmc31", "lna", "mmic",
        "bgb7", "trf37", "sga-", "tqp3", "sky67",
        "maam", "admv",
    )
    rf_transceiver_keywords = (
        "max283", "at86rf", "cc1101", "cc2500", "sx127", "sx126",
        "rfm9", "rfm6", "nrf24", "si446",
        # KH-120: Less common RF transceiver/front-end ICs
        "bk4819", "cmx994", "cmx99", "si4463", "si4432", "a7105",
        "nrf52", "nrf53", "esp32",
    )
    rf_filter_keywords = (
        "saw", "baw", "fbar", "highpass", "lowpass", "bandpass",
        "fil-", "sf2", "ta0", "b39",
    )
    # KH-085: New RF component categories
    rf_attenuator_keywords = (
        "hmc47", "hmc54", "pe43", "pe44", "dat-", "rfsa",
    )
    rf_coupler_keywords = (
        "fpc0", "tcd-", "adc-", "bd-", "mdc-",
    )
    rf_power_detector_keywords = (
        "ltc559", "ad836", "hmc10", "hmc61", "hmc71",
    )
    rf_freq_multiplier_keywords = (
        "xx1000", "hmc57", "hmc20",
    )

    rf_switches = []
    rf_mixers = []
    rf_amplifiers = []
    rf_transceivers = []
    rf_filters = []
    rf_baluns = []
    rf_attenuators = []
    rf_couplers = []
    rf_power_detectors = []
    rf_freq_multipliers = []
    seen_rf_refs = set()

    for c in ctx.components:
        if c["reference"] in seen_rf_refs:
            continue
        val_lib = (c.get("value", "") + " " + c.get("lib_id", "")).lower()

        # KH-120: Also check "other" type — some RF ICs use non-standard
        # reference designators and get classified as "other"
        if c["type"] in ("ic", "other"):
            if any(k in val_lib for k in rf_switch_keywords):
                rf_switches.append(c)
                seen_rf_refs.add(c["reference"])
            elif any(k in val_lib for k in rf_mixer_keywords):
                rf_mixers.append(c)
                seen_rf_refs.add(c["reference"])
            elif any(k in val_lib for k in rf_amp_keywords):
                rf_amplifiers.append(c)
                seen_rf_refs.add(c["reference"])
            elif any(k in val_lib for k in rf_transceiver_keywords):
                rf_transceivers.append(c)
                seen_rf_refs.add(c["reference"])
            elif any(k in val_lib for k in rf_filter_keywords):
                rf_filters.append(c)
                seen_rf_refs.add(c["reference"])
            # KH-085: New RF categories
            elif any(k in val_lib for k in rf_attenuator_keywords):
                rf_attenuators.append(c)
                seen_rf_refs.add(c["reference"])
            elif any(k in val_lib for k in rf_coupler_keywords):
                rf_couplers.append(c)
                seen_rf_refs.add(c["reference"])
            elif any(k in val_lib for k in rf_power_detector_keywords):
                rf_power_detectors.append(c)
                seen_rf_refs.add(c["reference"])
            elif any(k in val_lib for k in rf_freq_multiplier_keywords):
                rf_freq_multipliers.append(c)
                seen_rf_refs.add(c["reference"])
        elif c["type"] == "transformer":
            if any(k in val_lib for k in ("balun", "bal-", "b0310", "bl14")):
                rf_baluns.append(c)
                seen_rf_refs.add(c["reference"])

    rf_component_count = (
        len(rf_switches) + len(rf_mixers) + len(rf_amplifiers)
        + len(rf_transceivers) + len(rf_filters) + len(rf_baluns)
        + len(rf_attenuators) + len(rf_couplers) + len(rf_power_detectors)
        + len(rf_freq_multipliers)
    )

    if rf_component_count >= 2:
        all_rf_refs = seen_rf_refs.copy()
        rf_nets_map = {}
        for ref in all_rf_refs:
            ref_nets = {net for net, _ in ctx.ref_pins.get(ref, {}).values()
                        if net and not ctx.is_power_net(net) and not ctx.is_ground(net)}
            rf_nets_map[ref] = ref_nets

        connections = []
        rf_ref_list = sorted(all_rf_refs)
        for i, ref_a in enumerate(rf_ref_list):
            for ref_b in rf_ref_list[i+1:]:
                shared = rf_nets_map.get(ref_a, set()) & rf_nets_map.get(ref_b, set())
                signal_shared = [n for n in shared if not n.startswith("__unnamed_")]
                if shared:
                    connections.append({
                        "from": ref_a,
                        "to": ref_b,
                        "shared_nets": len(shared),
                        "named_nets": signal_shared,
                    })

        def _rf_role(ref):
            comp = ctx.comp_lookup.get(ref)
            if not comp:
                return "unknown"
            val_lib = (comp.get("value", "") + " " + comp.get("lib_id", "")).lower()
            if any(k in val_lib for k in rf_switch_keywords):
                return "switch"
            if any(k in val_lib for k in rf_mixer_keywords):
                return "mixer"
            if any(k in val_lib for k in rf_amp_keywords):
                return "amplifier"
            if any(k in val_lib for k in rf_transceiver_keywords):
                return "transceiver"
            if any(k in val_lib for k in rf_filter_keywords):
                return "filter"
            # KH-085: New RF roles
            if any(k in val_lib for k in rf_attenuator_keywords):
                return "attenuator"
            if any(k in val_lib for k in rf_coupler_keywords):
                return "coupler"
            if any(k in val_lib for k in rf_power_detector_keywords):
                return "power_detector"
            if any(k in val_lib for k in rf_freq_multiplier_keywords):
                return "freq_multiplier"
            if comp["type"] == "transformer":
                return "balun"
            return "unknown"

        all_rf_chain_refs = [c["reference"] for c in (
            rf_switches + rf_mixers + rf_amplifiers + rf_transceivers +
            rf_filters + rf_baluns + rf_attenuators + rf_couplers +
            rf_power_detectors + rf_freq_multipliers
        )]
        rf_chains.append({
            "switches": [
                {"reference": c["reference"], "value": c["value"],
                 "lib_id": c.get("lib_id", "")}
                for c in rf_switches
            ],
            "mixers": [
                {"reference": c["reference"], "value": c["value"],
                 "lib_id": c.get("lib_id", "")}
                for c in rf_mixers
            ],
            "amplifiers": [
                {"reference": c["reference"], "value": c["value"],
                 "lib_id": c.get("lib_id", "")}
                for c in rf_amplifiers
            ],
            "transceivers": [
                {"reference": c["reference"], "value": c["value"],
                 "lib_id": c.get("lib_id", "")}
                for c in rf_transceivers
            ],
            "filters": [
                {"reference": c["reference"], "value": c["value"],
                 "lib_id": c.get("lib_id", "")}
                for c in rf_filters
            ],
            "baluns": [
                {"reference": c["reference"], "value": c["value"],
                 "lib_id": c.get("lib_id", "")}
                for c in rf_baluns
            ],
            # KH-085: New RF component categories
            "attenuators": [
                {"reference": c["reference"], "value": c["value"],
                 "lib_id": c.get("lib_id", "")}
                for c in rf_attenuators
            ],
            "couplers": [
                {"reference": c["reference"], "value": c["value"],
                 "lib_id": c.get("lib_id", "")}
                for c in rf_couplers
            ],
            "power_detectors": [
                {"reference": c["reference"], "value": c["value"],
                 "lib_id": c.get("lib_id", "")}
                for c in rf_power_detectors
            ],
            "freq_multipliers": [
                {"reference": c["reference"], "value": c["value"],
                 "lib_id": c.get("lib_id", "")}
                for c in rf_freq_multipliers
            ],
            "total_rf_components": rf_component_count,
            "connections": connections,
            "component_roles": {
                ref: _rf_role(ref) for ref in all_rf_refs
            },
            "detector": "detect_rf_chains",
            "rule_id": "RF-DET",
            "category": "rf",
            "severity": "info",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "summary": f"RF chain: {rf_component_count} components",
            "description": f"Detected RF signal chain with {rf_component_count} components.",
            "components": all_rf_chain_refs,
            "nets": [],
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "RF", "impact": "", "standard_ref": ""},
            "provenance": make_provenance("rf_chain_topology", "heuristic", claimed_components=all_rf_chain_refs),
        })

        # Enrich with operating frequency and gain budget
        chain = rf_chains[-1]
        comp_roles = chain["component_roles"]

        # Determine operating frequency from transceivers
        operating_freq = None
        freq_band = None
        for xcvr in rf_transceivers:
            val_lib = (xcvr.get("value", "") + " " + xcvr.get("lib_id", "")).lower()
            for prefix, band_info in RF_IC_BANDS.items():
                if prefix in val_lib:
                    operating_freq = band_info["freq_hz"]
                    freq_band = band_info["band"]
                    break
            if operating_freq:
                break

        # Compute per-stage gain/loss budget
        stage_gains = {}
        total_gain_db = 0.0
        for ref, role in comp_roles.items():
            gain = RF_ROLE_GAIN_DB.get(role, 0.0)
            stage_gains[ref] = {"role": role, "gain_dB": gain}
            total_gain_db += gain

        chain["operating_frequency_hz"] = operating_freq
        chain["frequency_band"] = freq_band
        chain["gain_budget_dB"] = round(total_gain_db, 1)
        chain["stage_gains"] = stage_gains
    return rf_chains


# Reference design matching value ranges (conservative to avoid false positives)
_RF_REFERENCE_DESIGNS: dict[str, dict] = {
    "esp32": {
        "keywords": ("esp32", "esp32-s", "esp32-c", "esp32-h"),
        "frequency_mhz": 2400,
        "inductor_range": (1.0e-9, 5.6e-9),   # 1.0-5.6 nH
        "capacitor_range": (0.5e-12, 3.3e-12),  # 0.5-3.3 pF
    },
    "cc1101": {
        "keywords": ("cc1101", "cc110"),
        "frequency_mhz": 433,
        "inductor_range": (5.6e-9, 22e-9),     # 5.6-22 nH
        "capacitor_range": (2.2e-12, 22e-12),   # 2.2-22 pF
    },
    "sx127x": {
        "keywords": ("sx127", "sx126", "rfm9", "ra-01", "ra01"),
        "frequency_mhz": 868,
        "inductor_range": (2.7e-9, 15e-9),     # 2.7-15 nH
        "capacitor_range": (0.8e-12, 10e-12),   # 0.8-10 pF
    },
    "nrf24": {
        "keywords": ("nrf24", "nrf52", "nrf53"),
        "frequency_mhz": 2400,
        "inductor_range": (2.2e-9, 8.2e-9),
        "capacitor_range": (0.8e-12, 4.7e-12),
    },
}


def _check_rf_reference_values(target_comp: dict,
                               matching_components: list[dict],
                               ) -> dict | None:
    """Check matching component values against known reference designs."""
    target_check = (target_comp.get("value", "") + " " +
                    target_comp.get("lib_id", "") + " " +
                    target_comp.get("description", "")).lower()

    matched_family = None
    for family, info in _RF_REFERENCE_DESIGNS.items():
        if any(kw in target_check for kw in info["keywords"]):
            matched_family = family
            break

    if not matched_family:
        return None

    info = _RF_REFERENCE_DESIGNS[matched_family]
    out_of_range: list[dict] = []

    for mc in matching_components:
        val = mc.get("henries") or mc.get("farads")
        if val is None:
            continue
        if mc["type"] == "inductor":
            lo, hi = info["inductor_range"]
            if val < lo or val > hi:
                out_of_range.append({
                    "ref": mc["ref"],
                    "value": mc.get("value", ""),
                    "actual": val,
                    "expected_range": f"{lo*1e9:.1f}-{hi*1e9:.1f} nH",
                })
        elif mc["type"] == "capacitor":
            lo, hi = info["capacitor_range"]
            if val < lo or val > hi:
                out_of_range.append({
                    "ref": mc["ref"],
                    "value": mc.get("value", ""),
                    "actual": val,
                    "expected_range": f"{lo*1e12:.1f}-{hi*1e12:.1f} pF",
                })

    return {
        "target_ic_family": matched_family,
        "frequency_mhz": info["frequency_mhz"],
        "values_in_range": len(out_of_range) == 0,
        "out_of_range_components": out_of_range,
    }


def detect_rf_matching(ctx: AnalysisContext) -> list[dict]:
    """Detect RF antenna matching networks (pi-match, L-match, T-match)."""
    rf_matching: list[dict] = []

    # Find antenna connectors
    _ant_prefixes = ("AE", "ANT")
    _ant_keywords = ("antenna", "u.fl", "ufl", "ipex", "mhf", "rf_conn")
    _ant_lib_keywords = ("antenna", "u.fl", "ufl", "sma", "ipex", "mhf", "rf_conn")
    antennas = []
    for comp in ctx.components:
        ref_prefix = "".join(c for c in comp["reference"] if c.isalpha())
        val_lower = comp.get("value", "").lower()
        lib_lower = comp.get("lib_id", "").lower()
        if (ref_prefix in _ant_prefixes
                or any(kw in val_lower for kw in _ant_keywords)
                or any(kw in lib_lower for kw in _ant_lib_keywords)):
            antennas.append(comp)

    for ant in antennas:
        # BFS from antenna through L/C components
        ant_nets = set()
        for pin in ant.get("pins", []):
            net_name, _ = ctx.pin_net.get((ant["reference"], pin["number"]), (None, None))
            if net_name and not ctx.is_ground(net_name) and not ctx.is_power_net(net_name):
                ant_nets.add(net_name)
        if not ant_nets:
            # Try 2-pin approach
            n1, n2 = ctx.get_two_pin_nets(ant["reference"])
            for n in (n1, n2):
                if n and not ctx.is_ground(n) and not ctx.is_power_net(n):
                    ant_nets.add(n)

        if not ant_nets:
            continue

        # BFS through passive matching components
        visited_nets = set(ant_nets)
        visited_refs = {ant["reference"]}
        matching_components = []
        frontier = list(ant_nets)
        target_ic = None

        for _ in range(6):  # Max 6 hops
            if not frontier:
                break
            next_frontier = []
            for net_name in frontier:
                if net_name not in ctx.nets:
                    continue
                for p in ctx.nets[net_name]["pins"]:
                    cref = p["component"]
                    if cref in visited_refs:
                        continue
                    comp = ctx.comp_lookup.get(cref)
                    if not comp:
                        continue
                    if comp["type"] in ("capacitor", "inductor", "ferrite_bead"):
                        # KH-150: Skip ferrite beads (EMI filtering, not RF matching)
                        _comp_desc = (comp.get("description", "") + " " +
                                      comp.get("keywords", "") + " " +
                                      comp.get("value", "")).lower()
                        if any(k in _comp_desc for k in ("ferrite", "bead", "emi")):
                            visited_refs.add(cref)
                            continue
                        if comp["type"] == "ferrite_bead":
                            visited_refs.add(cref)
                            continue
                        visited_refs.add(cref)
                        mc_parsed = ctx.parsed_values.get(cref)
                        matching_components.append({
                            "ref": cref,
                            "type": comp["type"],
                            "value": comp.get("value", ""),
                            "farads": mc_parsed if comp["type"] == "capacitor" and mc_parsed else None,
                            "henries": mc_parsed if comp["type"] == "inductor" and mc_parsed else None,
                            "ohms": mc_parsed if comp["type"] == "resistor" and mc_parsed else None,
                        })
                        # Follow through to other pin
                        cn1, cn2 = ctx.get_two_pin_nets(cref)
                        for cn in (cn1, cn2):
                            if cn and cn not in visited_nets and not ctx.is_power_net(cn):
                                # Allow ground as shunt element target
                                if not ctx.is_ground(cn):
                                    visited_nets.add(cn)
                                    next_frontier.append(cn)
                    elif comp["type"] == "ic" and not target_ic:
                        target_ic = cref
                        visited_refs.add(cref)
            frontier = next_frontier

        if not matching_components:
            continue

        # KH-150: Require target IC to be RF-related
        if target_ic:
            _target_comp = ctx.comp_lookup.get(target_ic, {})
            _target_check = (_target_comp.get("value", "") + " " +
                             _target_comp.get("lib_id", "") + " " +
                             _target_comp.get("description", "") + " " +
                             _target_comp.get("keywords", "")).lower()
            _rf_keywords = ("rf", "transceiver", "mixer", "lna", "wireless",
                            "radio", "bluetooth", "wifi", "zigbee", "lora",
                            "sx127", "cc1101", "nrf", "esp32", "at86",
                            "si446", "rfm", "ra0", "wl18", "antenna",
                            "433", "868", "915", "2.4g", "uwb", "gps",
                            "gnss", "amplifier_rf", "rf_amplifier")
            if not any(kw in _target_check for kw in _rf_keywords):
                continue

        # RF matching networks require at least one inductor — pure C networks
        # are decoupling/filtering, not impedance matching
        has_inductor = any(mc["type"] == "inductor" for mc in matching_components)
        if not has_inductor:
            continue

        # Value range filter: RF matching uses small-ish inductors and caps.
        # Thresholds set high enough for lower-frequency RF (433 MHz, HF/27 MHz)
        # where matching inductors can reach a few µH and caps tens of nF.
        # Very large values (power chokes, bulk caps) are still excluded.
        has_large_values = False
        for mc in matching_components:
            mc_val = parse_value(mc.get("value", ""))
            if mc_val is not None:
                if mc["type"] == "inductor" and mc_val > 10e-6:  # > 10uH
                    has_large_values = True
                    break
                if mc["type"] == "capacitor" and mc_val > 10e-9:  # > 10nF
                    has_large_values = True
                    break
        if has_large_values:
            continue

        # Classify topology
        n_series_l = 0
        n_shunt_c = 0
        n_series_c = 0
        for mc in matching_components:
            if mc["type"] == "inductor":
                n_series_l += 1
            elif mc["type"] == "capacitor":
                # Check if cap has one terminal to ground (shunt) vs series
                cn1, cn2 = ctx.get_two_pin_nets(mc["ref"])
                if ctx.is_ground(cn1) or ctx.is_ground(cn2):
                    n_shunt_c += 1
                else:
                    n_series_c += 1

        total = len(matching_components)
        if n_series_l >= 1 and n_shunt_c >= 2:
            topology = "pi_match"
        elif n_series_l >= 2 and n_shunt_c >= 1:
            topology = "T_match"
        elif total == 2 and (n_series_l + n_series_c) >= 1 and n_shunt_c >= 1:
            topology = "L_match"
        elif total >= 2:
            topology = "matching_network"
        else:
            topology = "matching_network"

        rm_comps = [ant["reference"]] + ([target_ic] if target_ic else []) + [mc["ref"] for mc in matching_components]
        entry = {
            "antenna": ant["reference"],
            "antenna_value": ant.get("value", ""),
            "topology": topology,
            "components": matching_components,
            "detector": "detect_rf_matching",
            "rule_id": "RM-DET",
            "category": "rf",
            "severity": "info",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "summary": f"RF {topology} matching network at {ant['reference']}",
            "description": f"Detected RF {topology} matching network near antenna {ant['reference']}.",
            "component_refs": rm_comps,
            "nets": [],
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "RF", "impact": "", "standard_ref": ""},
        }
        if target_ic:
            entry["target_ic"] = target_ic
            entry["target_value"] = ctx.comp_lookup.get(target_ic, {}).get("value", "")

        # Reference design value validation
        if target_ic:
            ref_check = _check_rf_reference_values(
                ctx.comp_lookup.get(target_ic, {}), matching_components)
            if ref_check:
                entry["reference_design_check"] = ref_check

        entry["advisory"] = [
            "RF ground stitching near antenna cannot be verified from "
            "schematic — check PCB layout"
        ]

        entry["provenance"] = make_provenance("rf_match_topology", "deterministic", claimed_components=[ant["reference"]])
        rf_matching.append(entry)

    return rf_matching


def detect_bms_systems(ctx: AnalysisContext) -> list[dict]:
    """Detect Battery Management System ICs with cell monitoring."""
    bms_systems: list[dict] = []

    # KH-123: Only include multi-cell BMS/AFE ICs, not single-cell chargers.
    # Single-cell chargers (TP4056, MCP73871, etc.) handle charging only,
    # not cell balancing or multi-cell monitoring.
    bms_ic_keywords = (
        "bq769", "bq76920", "bq76930", "bq76940", "bq76952", "bq7694",
        "ltc681", "ltc682", "ltc683", "ltc680",
        "isl9420", "isl9421", "isl9424", "max1726", "max1730",
    )
    # "afe" removed — too many false positives (matches "safety", "cafe", etc.)

    bms_ics = []
    seen_bms_refs = set()
    for c in ctx.components:
        if c["reference"] in seen_bms_refs:
            continue
        val_lib = (c.get("value", "") + " " + c.get("lib_id", "")).lower()
        if c["type"] == "ic" and any(k in val_lib for k in bms_ic_keywords):
            bms_ics.append(c)
            seen_bms_refs.add(c["reference"])

    for bms_ic in bms_ics:
        ref = bms_ic["reference"]

        cell_pins = []
        bms_nets = set()
        for pnum, (net, _) in ctx.ref_pins.get(ref, {}).items():
            if not net:
                continue
            bms_nets.add(net)
            # Match on PIN NAME (not net name) — cell voltage pins are
            # named VC0..VC16, CELL0..CELL16, C0..C16 on BMS ICs
            pin_name = None
            if net in ctx.nets:
                for p in ctx.nets[net]["pins"]:
                    if p["component"] == ref and p["pin_number"] == pnum:
                        pin_name = (p.get("pin_name") or "").upper()
                        break
            if pin_name:
                m = re.match(r'^VC(\d+)[A-Z]?$', pin_name)
                if not m:
                    m = re.match(r'^CELL(\d+)', pin_name)
                if not m:
                    m = re.match(r'^C(\d+)$', pin_name)
                if m:
                    cell_pins.append({"pin": pnum, "pin_name": pin_name, "net": net})

        # Determine cell count from pin names, filtering out repurposed pins.
        # BQ76920 reuses VC3-5 for I2C/enable on 3/4-cell configs — these
        # connect to GND, SDA, SCL etc. instead of cell voltage nets.
        # Only count VC pins that connect to non-power, non-I2C nets.
        cell_numbers = set()
        valid_cell_pins = []
        for cp in cell_pins:
            net = cp["net"]
            net_upper = net.upper()
            # Skip pins connected to well-known non-cell nets
            if ctx.is_power_net(net) or ctx.is_ground(net):
                continue
            if any(k in net_upper for k in ("SDA", "SCL", "I2C", "CHG_EN",
                                             "DSG_EN", "ALERT", "TS", "REGOUT",
                                             "REGSRC")):
                continue
            valid_cell_pins.append(cp)
            m = re.match(r'^VC(\d+)', cp["pin_name"])
            if m:
                cell_numbers.add(int(m.group(1)))
            m = re.match(r'^CELL(\d+)', cp["pin_name"])
            if m:
                cell_numbers.add(int(m.group(1)))
            m = re.match(r'^C(\d+)$', cp["pin_name"])
            if m:
                cell_numbers.add(int(m.group(1)))

        balance_resistors = []
        cell_net_names = {cp["net"] for cp in valid_cell_pins}
        for net_name in cell_net_names:
            if net_name not in ctx.nets:
                continue
            for p in ctx.nets[net_name]["pins"]:
                comp = ctx.comp_lookup.get(p["component"])
                if comp and comp["type"] == "resistor" and p["component"] != ref:
                    r_ohms = ctx.parsed_values.get(p["component"])
                    balance_resistors.append({
                        "reference": p["component"],
                        "value": comp["value"],
                        "ohms": r_ohms,
                        "cell_net": net_name,
                    })

        chg_dsg_fets = []
        seen_fet_refs = set()
        power_path_keywords = ("BAT+", "BAT-", "PACK+", "PACK-", "CHG+", "DSG+",
                               "BATT+", "BATT-", "VBAT+", "VBAT-")
        for net_name in ctx.nets:
            if net_name.upper() not in power_path_keywords:
                continue
            for p in ctx.nets[net_name]["pins"]:
                comp = ctx.comp_lookup.get(p["component"])
                if (comp and comp["type"] == "transistor"
                        and p["component"] not in seen_fet_refs):
                    chg_dsg_fets.append({
                        "reference": p["component"],
                        "value": comp["value"],
                        "power_net": net_name,
                    })
                    seen_fet_refs.add(p["component"])

        ntc_sensors = []
        for net_name in bms_nets:
            if not net_name or net_name not in ctx.nets:
                continue
            for p in ctx.nets[net_name]["pins"]:
                comp = ctx.comp_lookup.get(p["component"])
                if comp and comp["type"] == "thermistor":
                    ntc_sensors.append({
                        "reference": p["component"],
                        "value": comp["value"],
                        "net": net_name,
                    })

        seen_ntc = set()
        unique_ntcs = []
        for ntc in ntc_sensors:
            if ntc["reference"] not in seen_ntc:
                unique_ntcs.append(ntc)
                seen_ntc.add(ntc["reference"])

        cell_count = max(cell_numbers) if cell_numbers else 0

        bms_comps = [ref] + [r["reference"] for r in balance_resistors] + [f["reference"] for f in chg_dsg_fets]
        bms_systems.append({
            "bms_reference": ref,
            "bms_value": bms_ic["value"],
            "bms_lib_id": bms_ic.get("lib_id", ""),
            "cell_voltage_pins": len(valid_cell_pins),
            "cell_count": cell_count,
            "cell_nets": sorted(cell_net_names),
            "balance_resistors": balance_resistors,
            "balance_resistor_count": len(balance_resistors),
            "charge_discharge_fets": chg_dsg_fets,
            "ntc_sensors": unique_ntcs,
            "detector": "detect_bms_systems",
            "rule_id": "BM-DET",
            "category": "battery",
            "severity": "info",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "summary": f"BMS {ref} ({bms_ic['value']}) {cell_count}-cell",
            "description": f"Detected Battery Management System IC {ref} monitoring {cell_count} cells.",
            "components": bms_comps,
            "nets": sorted(cell_net_names),
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "Battery", "impact": "", "standard_ref": ""},
            "provenance": make_provenance("bms_ic_topology", "deterministic", claimed_components=[ref]),
        })
    return bms_systems


# ---------------------------------------------------------------------------
# Battery charger and cell protection detector
# ---------------------------------------------------------------------------

# Charge current formulas: I_charge = K / R_prog (mA, R in kohm)
_CHARGER_PROG_FORMULAS: dict[str, tuple[float, str]] = {
    "tp4056": (1200.0, "I = 1200 / R_prog"),
    "tp4057": (1200.0, "I = 1200 / R_prog"),
    "tp5400": (1200.0, "I = 1200 / R_prog"),
    "mcp73831": (1000.0, "I = 1000 / R_prog"),
    "mcp73832": (1000.0, "I = 1000 / R_prog"),
    "mcp73871": (1000.0, "I = 1000 / R_prog"),
    "mcp73811": (1000.0, "I = 1000 / R_prog"),
    "mcp73812": (1000.0, "I = 1000 / R_prog"),
    "bq24040": (540.0, "I = 540 / R_prog"),
    "bq24045": (540.0, "I = 540 / R_prog"),
    "bq24070": (890.0, "I = 890 / R_prog"),
    "bq24073": (890.0, "I = 890 / R_prog"),
    "bq24074": (890.0, "I = 890 / R_prog"),
    "bq24075": (890.0, "I = 890 / R_prog"),
    "ltc4054": (1000.0, "I = 1000 / R_prog"),
    "ltc4056": (1000.0, "I = 1000 / R_prog"),
    "ltc4065": (1000.0, "I = 1000 / R_prog"),
    "cn3052": (1200.0, "I = 1200 / R_prog"),
    "cn3058": (1200.0, "I = 1200 / R_prog"),
    "cn3063": (1200.0, "I = 1200 / R_prog"),
    "cn3065": (1200.0, "I = 1200 / R_prog"),
    "cn3791": (1200.0, "I = 1200 / R_prog"),
    "mp2615": (1000.0, "I = 1000 / R_prog"),
    "mp2624": (1000.0, "I = 1000 / R_prog"),
    "mp2639": (1000.0, "I = 1000 / R_prog"),
}

_CHARGER_IC_KEYWORDS = tuple(_CHARGER_PROG_FORMULAS.keys()) + (
    "sgm4105", "sgm4154",
    "max1551", "max1555", "max1811",
)

_CELL_PROTECTION_KEYWORDS = (
    "dw01", "fs8205", "s-8261", "s8261", "xb8089",
    "ap9101", "ht4936", "r5421", "r5426",
    "bq2970", "bq29700", "bq2980",
    "cw1054", "cw1084",
)

_PROG_PIN_NAMES = {"PROG", "RPROG", "IPROG", "ISET", "ICHG", "ITERM"}
_STATUS_PIN_NAMES = {"STAT", "STAT1", "STAT2", "CHRG", "CHG", "DONE",
                     "PG", "PGOOD", "nCHG", "nSTAT"}
_BAT_PIN_NAMES = {"BAT", "VBAT", "BAT+", "BATT", "BATT+"}
_VIN_PIN_NAMES = {"VIN", "VBUS", "IN", "VCC", "USB"}


def detect_battery_chargers(ctx: AnalysisContext) -> list[dict]:
    """Detect single-cell battery charger ICs and cell protection circuits.

    Complements detect_bms_systems() which handles multi-cell BMS/AFE ICs.
    This detector covers linear and switching single-cell chargers (TP4056,
    MCP73831, BQ2404x, etc.) and standalone cell protection ICs (DW01+FS8205).
    """
    chargers: list[dict] = []
    protection_ics: list[dict] = []

    # --- Phase 1: Find charger ICs ---
    seen_refs: set[str] = set()
    for c in ctx.components:
        if c["type"] != "ic" or c["reference"] in seen_refs:
            continue
        val_lib = (c.get("value", "") + " " + c.get("lib_id", "")).lower()
        if any(k in val_lib for k in _CHARGER_IC_KEYWORDS):
            seen_refs.add(c["reference"])
            ref = c["reference"]

            # Identify the specific charger family for formula lookup
            charger_family = None
            for family_key in _CHARGER_PROG_FORMULAS:
                if family_key in val_lib:
                    charger_family = family_key
                    break

            # Classify charger type
            charger_type = "single_cell_linear"
            for sw_kw in ("mp26", "cn3791", "bq2407"):
                if sw_kw in val_lib:
                    charger_type = "single_cell_switching"
                    break

            # Scan pins for PROG, BAT, VIN, STATUS
            prog_info = None
            bat_net = None
            vin_net = None
            status_pins: list[dict] = []

            for pnum, (net, _) in ctx.ref_pins.get(ref, {}).items():
                if not net:
                    continue
                # Get pin name from net data
                pin_name = ""
                if net in ctx.nets:
                    for p in ctx.nets[net]["pins"]:
                        if p["component"] == ref and p["pin_number"] == pnum:
                            pin_name = (p.get("pin_name") or "").upper()
                            break

                # PROG pin — find connected resistor
                if pin_name in _PROG_PIN_NAMES:
                    for p in ctx.nets.get(net, {}).get("pins", []):
                        comp = ctx.comp_lookup.get(p["component"])
                        if comp and comp["type"] == "resistor" and p["component"] != ref:
                            r_ohms = ctx.parsed_values.get(p["component"])
                            if r_ohms and r_ohms > 0:
                                r_kohm = r_ohms / 1000.0
                                current_mA = None
                                formula = None
                                if charger_family and charger_family in _CHARGER_PROG_FORMULAS:
                                    k, formula = _CHARGER_PROG_FORMULAS[charger_family]
                                    current_mA = k / r_kohm
                                prog_info = {
                                    "prog_resistor": p["component"],
                                    "prog_resistance_ohms": r_ohms,
                                    "programmed_current_mA": round(current_mA, 1) if current_mA else None,
                                    "formula": formula,
                                }
                            break

                # Battery pin
                if pin_name in _BAT_PIN_NAMES and not bat_net:
                    bat_net = net

                # Input pin
                if pin_name in _VIN_PIN_NAMES and not vin_net:
                    vin_net = net

                # Status pins
                if pin_name in _STATUS_PIN_NAMES:
                    # Check if an LED is connected
                    has_led = False
                    for p in ctx.nets.get(net, {}).get("pins", []):
                        comp = ctx.comp_lookup.get(p["component"])
                        if comp and comp["type"] in ("led", "diode"):
                            vl = (comp.get("value", "") + " " + comp.get("lib_id", "")).lower()
                            if "led" in vl or comp["type"] == "led":
                                has_led = True
                                break
                    status_pins.append({
                        "pin": pin_name,
                        "net": net,
                        "has_led": has_led,
                    })

            # Fallback: if no pin-name match, try net-name heuristic for bat/vin
            if not bat_net:
                for pnum, (net, _) in ctx.ref_pins.get(ref, {}).items():
                    if net and any(k in net.upper() for k in ("VBAT", "BAT+", "BATT")):
                        bat_net = net
                        break
            if not vin_net:
                for pnum, (net, _) in ctx.ref_pins.get(ref, {}).items():
                    if net and any(k in net.upper() for k in ("VBUS", "VIN", "USB")):
                        vin_net = net
                        break

            entry: dict = {
                "charger_reference": ref,
                "charger_value": c.get("value", ""),
                "charger_lib_id": c.get("lib_id", ""),
                "charger_type": charger_type,
                "input_rail": vin_net,
                "battery_net": bat_net,
                "detector": "detect_battery_chargers",
                "rule_id": "BC-DET",
                "category": "battery",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Battery charger {ref} ({c.get('value', '')}) [{charger_type}]",
                "description": f"Detected {charger_type} battery charger IC {ref}.",
                "components": [ref],
                "nets": [n for n in (vin_net, bat_net) if n],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Battery", "impact": "", "standard_ref": ""},
            }
            if prog_info:
                entry["charge_current"] = prog_info
            if status_pins:
                entry["status_pins"] = status_pins

            entry["provenance"] = make_provenance("charger_ic_topology", "deterministic", claimed_components=[ref])
            chargers.append(entry)

    # --- Phase 2: Find cell protection ICs ---
    for c in ctx.components:
        if c["reference"] in seen_refs:
            continue
        val_lib = (c.get("value", "") + " " + c.get("lib_id", "")).lower()
        if c["type"] == "ic" and any(k in val_lib for k in _CELL_PROTECTION_KEYWORDS):
            seen_refs.add(c["reference"])
            prot_ref = c["reference"]

            # Find protection FETs: BFS 2 hops from protection IC pins
            # looking for transistors (DW01 drives gate of FS8205 dual FET)
            protection_fets: list[dict] = []
            seen_fets: set[str] = set()
            for pnum, (net, _) in ctx.ref_pins.get(prot_ref, {}).items():
                if not net or net not in ctx.nets:
                    continue
                for p in ctx.nets[net]["pins"]:
                    comp = ctx.comp_lookup.get(p["component"])
                    if (comp and comp["type"] == "transistor"
                            and p["component"] not in seen_fets
                            and p["component"] != prot_ref):
                        protection_fets.append({
                            "reference": p["component"],
                            "value": comp.get("value", ""),
                        })
                        seen_fets.add(p["component"])

            prot_entry = {
                "protection_ic": prot_ref,
                "protection_value": c.get("value", ""),
                "protection_lib_id": c.get("lib_id", ""),
                "protection_fets": protection_fets,
            }
            protection_ics.append(prot_entry)

    # --- Phase 3: Associate protection ICs with chargers ---
    # If a charger and protection IC share the battery net, link them
    for ch in chargers:
        ch["cell_protection"] = None
        if ch.get("battery_net"):
            for prot in protection_ics:
                prot_ref = prot["protection_ic"]
                prot_nets = set()
                for pnum, (net, _) in ctx.ref_pins.get(prot_ref, {}).items():
                    if net:
                        prot_nets.add(net)
                if ch["battery_net"] in prot_nets:
                    ch["cell_protection"] = prot
                    break

    # Add unlinked protection ICs as standalone entries
    linked_prots = {ch["cell_protection"]["protection_ic"]
                    for ch in chargers if ch.get("cell_protection")}
    for prot in protection_ics:
        if prot["protection_ic"] not in linked_prots:
            prot_ref = prot["protection_ic"]
            chargers.append({
                "charger_reference": None,
                "charger_value": None,
                "charger_lib_id": None,
                "charger_type": "standalone_protection",
                "input_rail": None,
                "battery_net": None,
                "cell_protection": prot,
                "detector": "detect_battery_chargers",
                "rule_id": "BC-DET",
                "category": "battery",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Standalone cell protection IC {prot_ref}",
                "description": f"Detected standalone cell protection IC {prot_ref} without paired charger.",
                "components": [prot_ref],
                "nets": [],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Battery", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("charger_ic_topology", "deterministic", claimed_components=[prot_ref]),
            })

    return chargers


# ---------------------------------------------------------------------------
# Motor driver detector
# ---------------------------------------------------------------------------

_MOTOR_DRIVER_KEYWORDS = (
    "drv8833", "drv8835", "drv8837", "drv8838", "drv8840",
    "drv8841", "drv8842", "drv8843", "drv8844",
    "drv8870", "drv8871", "drv8872", "drv8874",
    "drv8301", "drv8302", "drv8303", "drv8305",
    "l298", "l293", "l9110", "l6201", "l6202",
    "tb6612", "tb67h", "tb67s",
    "a4950", "a4988", "a4983",
    "tmc2100", "tmc2130", "tmc2208", "tmc2209", "tmc5160",
    "uln2003", "uln2803",
    "bd6211", "bd6220", "bd6231",
    "mp6513", "mp6515", "mp6522", "mp6530",
)

_GATE_DRIVER_KEYWORDS = (
    "ir2110", "ir2113", "ir2184", "ir2186", "ir2101", "ir2104",
    "ucc2152", "ucc2752", "ucc2150",
    "hip4086", "irs2186",
    "fan7388", "fan7390",
    "l6384", "l6387", "l6388",
    "ncp5106", "ncp5108",
    "fd6288",
)

_STEPPER_PIN_NAMES = {"STEP", "DIR", "MS1", "MS2", "MS3", "ENABLE",
                      "nENABLE", "nSLEEP", "nRESET", "SPREAD", "INDEX"}

_MOTOR_OUTPUT_PIN_NAMES = {"OUT1", "OUT2", "OUT3", "OUT4",
                           "OUT1A", "OUT1B", "OUT2A", "OUT2B",
                           "OUTA", "OUTB", "OUTC",
                           "AO", "BO", "CO",
                           "AOUT", "BOUT", "COUT",
                           "PHASE_A", "PHASE_B", "PHASE_C",
                           "MOT_A", "MOT_B",
                           "OUT_A+", "OUT_A-", "OUT_B+", "OUT_B-",
                           # 3-phase UVW notation (BLDC/PMSM)
                           "U", "V", "W", "UH", "UL", "VH", "VL", "WH", "WL",
                           # Gate driver high/low side notation
                           "AH", "AL", "BH", "BL", "CH", "CL"}

_GATE_OUTPUT_PIN_NAMES = {"HO", "LO", "HO1", "LO1", "HO2", "LO2",
                          "HO3", "LO3", "HIN", "LIN",
                          "OUTA", "OUTB"}

_BOOTSTRAP_PIN_NAMES = {"VB", "VB1", "VB2", "VB3", "VBOOT",
                        "VS", "VS1", "VS2", "VS3"}

_INDUCTIVE_LOAD_KEYWORDS = ("MOTOR", "FAN", "PUMP", "SOLENOID", "VALVE",
                            "COIL", "RELAY", "STEPPER", "ACTUATOR")


def detect_motor_drivers(ctx: AnalysisContext) -> list[dict]:
    """Detect motor driver ICs (H-bridge, stepper, BLDC) and gate drivers.

    Identifies integrated motor drivers and discrete gate driver + FET
    topologies. Checks for bootstrap capacitors, freewheeling diodes,
    and flags missing protection on inductive load nets.
    """
    drivers: list[dict] = []
    seen_refs: set[str] = set()

    for c in ctx.components:
        if c["type"] != "ic" or c["reference"] in seen_refs:
            continue
        val_lib = (c.get("value", "") + " " + c.get("lib_id", "")).lower()

        is_motor_driver = any(k in val_lib for k in _MOTOR_DRIVER_KEYWORDS)
        is_gate_driver = any(k in val_lib for k in _GATE_DRIVER_KEYWORDS)
        if not is_motor_driver and not is_gate_driver:
            continue

        seen_refs.add(c["reference"])
        ref = c["reference"]

        # Collect pin info
        motor_outputs: list[dict] = []
        gate_outputs: list[dict] = []
        control_inputs: list[dict] = []
        bootstrap_pins: dict[str, str] = {}  # pin_name → net
        power_supply = None
        has_stepper_pins = False

        for pnum, (net, _) in ctx.ref_pins.get(ref, {}).items():
            if not net:
                continue
            pin_name = ""
            if net in ctx.nets:
                for p in ctx.nets[net]["pins"]:
                    if p["component"] == ref and p["pin_number"] == pnum:
                        pin_name = (p.get("pin_name") or "").upper()
                        break

            if pin_name in _MOTOR_OUTPUT_PIN_NAMES:
                motor_outputs.append({"pin": pin_name, "net": net})
            elif pin_name in _GATE_OUTPUT_PIN_NAMES:
                gate_outputs.append({"pin": pin_name, "net": net})
            elif pin_name in _STEPPER_PIN_NAMES:
                has_stepper_pins = True
                control_inputs.append({"pin": pin_name, "net": net})
            elif pin_name in _BOOTSTRAP_PIN_NAMES:
                bootstrap_pins[pin_name] = net
            elif pin_name in ("VM", "VCC", "VS", "VMOT", "VIN") and not power_supply:
                if ctx.is_power_net(net) and not ctx.is_ground(net):
                    power_supply = net

        # Classify driver type
        if is_gate_driver:
            driver_type = "gate_driver"
        elif has_stepper_pins:
            driver_type = "stepper"
        elif len(motor_outputs) >= 6 or any("PHASE" in o["pin"] or o["pin"].endswith("C") for o in motor_outputs):
            driver_type = "brushless_3phase"
        else:
            driver_type = "dc_brushed_h_bridge"

        # --- Gate driver: find external FETs connected to gate outputs ---
        external_fets: list[dict] = []
        if is_gate_driver:
            seen_fets: set[str] = set()
            for go in gate_outputs:
                go_net = go["net"]
                if go_net not in ctx.nets:
                    continue
                # BFS up to 4 hops from gate output to find FETs
                visited_nets = {go_net}
                frontier = [go_net]
                for _hop in range(4):
                    next_frontier = []
                    for fn in frontier:
                        if fn not in ctx.nets:
                            continue
                        for p in ctx.nets[fn]["pins"]:
                            comp = ctx.comp_lookup.get(p["component"])
                            if not comp or p["component"] == ref:
                                continue
                            if (comp["type"] == "transistor"
                                    and p["component"] not in seen_fets):
                                external_fets.append({
                                    "reference": p["component"],
                                    "value": comp.get("value", ""),
                                    "gate_net": go_net,
                                })
                                seen_fets.add(p["component"])
                            # Continue BFS through passives (gate resistors, etc.)
                            if comp["type"] in ("resistor", "ferrite_bead"):
                                for pn2, (n2, _) in ctx.ref_pins.get(p["component"], {}).items():
                                    if n2 and n2 not in visited_nets:
                                        visited_nets.add(n2)
                                        next_frontier.append(n2)
                    frontier = next_frontier

        # --- Bootstrap capacitor detection ---
        bootstrap_caps: list[dict] = []
        vb_nets = {name: net for name, net in bootstrap_pins.items()
                   if name.startswith("VB")}
        vs_nets = {name: net for name, net in bootstrap_pins.items()
                   if name.startswith("VS")}
        for vb_name, vb_net in vb_nets.items():
            # Find matching VS pin (VB1↔VS1, VB↔VS)
            suffix = vb_name[2:]  # "" or "1" or "2"
            vs_net = vs_nets.get("VS" + suffix)
            if not vs_net or vb_net not in ctx.nets:
                continue
            # Find cap connected between VB and VS nets
            for p in ctx.nets[vb_net]["pins"]:
                comp = ctx.comp_lookup.get(p["component"])
                if comp and comp["type"] == "capacitor" and p["component"] != ref:
                    # Check if other pin connects to VS net
                    n1, n2 = ctx.get_two_pin_nets(p["component"])
                    other = n2 if n1 == vb_net else n1
                    if other == vs_net:
                        bootstrap_caps.append({
                            "reference": p["component"],
                            "value": comp.get("value", ""),
                            "between": [vb_name, "VS" + suffix],
                        })

        # --- Freewheeling diode detection on motor output nets ---
        output_nets = [o["net"] for o in motor_outputs]
        if is_gate_driver and external_fets:
            # For gate drivers, check FET drain/source nets instead
            for fet in external_fets:
                for pnum, (net, _) in ctx.ref_pins.get(fet["reference"], {}).items():
                    if net and net not in output_nets and not ctx.is_ground(net):
                        if not ctx.is_power_net(net):
                            output_nets.append(net)

        freewheeling_diodes: list[dict] = []
        missing_freewheeling: list[str] = []
        seen_diode_nets: set[str] = set()

        for out_net in output_nets:
            if out_net not in ctx.nets or out_net in seen_diode_nets:
                continue
            seen_diode_nets.add(out_net)

            # Check if any diode is on this net
            has_diode = False
            for p in ctx.nets[out_net]["pins"]:
                comp = ctx.comp_lookup.get(p["component"])
                if comp and comp["type"] == "diode" and p["component"] != ref:
                    freewheeling_diodes.append({
                        "reference": p["component"],
                        "value": comp.get("value", ""),
                        "net": out_net,
                    })
                    has_diode = True

            # Flag missing diode if net name suggests inductive load
            if not has_diode:
                net_upper = out_net.upper()
                if any(kw in net_upper for kw in _INDUCTIVE_LOAD_KEYWORDS):
                    missing_freewheeling.append(out_net)

        md_comps = [ref] + [f["reference"] for f in external_fets] + [d["reference"] for d in freewheeling_diodes]
        entry: dict = {
            "driver_reference": ref,
            "driver_value": c.get("value", ""),
            "driver_lib_id": c.get("lib_id", ""),
            "driver_type": driver_type,
            "motor_outputs": motor_outputs if not is_gate_driver else [],
            "gate_outputs": gate_outputs if is_gate_driver else [],
            "control_inputs": control_inputs,
            "power_supply": power_supply,
            "bootstrap_caps": bootstrap_caps,
            "freewheeling_diodes": freewheeling_diodes,
            "external_fets": external_fets,
            "detector": "detect_motor_drivers",
            "rule_id": "MD-DET",
            "category": "motor_control",
            "severity": "info",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "summary": f"Motor driver {ref} ({c.get('value', '')}) [{driver_type}]",
            "description": f"Detected {driver_type} motor driver IC {ref}.",
            "components": md_comps,
            "nets": [power_supply] if power_supply else [],
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "Motor Control", "impact": "", "standard_ref": ""},
        }
        if missing_freewheeling:
            entry["missing_freewheeling"] = missing_freewheeling

        _motor_evidence = "motor_hbridge" if driver_type == "dc_brushed_h_bridge" else "motor_driver_ic"
        entry["provenance"] = make_provenance(_motor_evidence, "deterministic", claimed_components=[ref])
        drivers.append(entry)

    return drivers




def detect_addressable_leds(ctx: AnalysisContext) -> list[dict]:
    """Detect addressable LED chains (WS2812, SK6812, APA102, etc.)."""
    chains: list[dict] = []

    # Keywords that identify addressable LEDs
    addr_keywords = ("ws2812", "ws2813", "ws2815", "sk6812", "apa102", "apa104",
                     "sk9822", "ws2811", "tm1809", "tm1812", "sm16703",
                     "neopixel", "dotstar")

    # Find addressable LED components
    # KH-122: Also search "diode" type — D-prefix addressable LEDs may be
    # misclassified when using custom library symbols
    addr_leds = {}
    for c in ctx.components:
        if c["type"] not in ("led", "ic", "other", "diode"):
            continue
        val_lower = c.get("value", "").lower()
        lib_lower = c.get("lib_id", "").lower()
        if any(k in val_lower or k in lib_lower for k in addr_keywords):
            addr_leds[c["reference"]] = c

    if not addr_leds:
        return chains

    # Determine protocol
    def _get_protocol(comp):
        vl = comp.get("value", "").lower()
        ll = comp.get("lib_id", "").lower()
        txt = vl + " " + ll
        if any(k in txt for k in ("apa102", "sk9822", "dotstar")):
            return "SPI (APA102)"
        return "single-wire (WS2812)"

    # Find DIN/DOUT pin nets for each LED
    led_din_net = {}  # ref -> net on DIN
    led_dout_net = {}  # ref -> net on DOUT
    din_names = {"DIN", "DI", "SDI", "DATAIN", "DATA_IN", "IN", "SDA"}
    dout_names = {"DOUT", "DO", "SDO", "DATAOUT", "DATA_OUT", "OUT"}

    for led_ref, led_comp in addr_leds.items():
        for pnum, (net, _) in ctx.ref_pins.get(led_ref, {}).items():
            if not net:
                continue
            pin_name = ""
            if net in ctx.nets:
                for p in ctx.nets[net]["pins"]:
                    if p["component"] == led_ref and p["pin_number"] == pnum:
                        pin_name = p.get("pin_name", "").upper().replace(" ", "")
                        break
            if pin_name in din_names:
                led_din_net[led_ref] = net
            elif pin_name in dout_names:
                led_dout_net[led_ref] = net

    # Build chain by tracing DOUT -> DIN connections
    used = set()
    for start_ref in addr_leds:
        if start_ref in used:
            continue
        # Walk backward to find chain start (LED whose DIN is not another LED's DOUT)
        head = start_ref
        visited_back = {head}
        while True:
            din = led_din_net.get(head)
            if not din or din not in ctx.nets:
                break
            found_prev = False
            for p in ctx.nets[din]["pins"]:
                pref = p["component"]
                if pref != head and pref in addr_leds and pref not in visited_back:
                    if led_dout_net.get(pref) == din:
                        head = pref
                        visited_back.add(head)
                        found_prev = True
                        break
            if not found_prev:
                break

        # Walk forward from head
        chain_refs = [head]
        used.add(head)
        cur = head
        while True:
            dout = led_dout_net.get(cur)
            if not dout or dout not in ctx.nets:
                break
            found_next = False
            for p in ctx.nets[dout]["pins"]:
                pref = p["component"]
                if pref != cur and pref in addr_leds and pref not in used:
                    if led_din_net.get(pref) == dout:
                        chain_refs.append(pref)
                        used.add(pref)
                        cur = pref
                        found_next = True
                        break
            if not found_next:
                break

        first_comp = addr_leds[chain_refs[0]]
        protocol = _get_protocol(first_comp)
        # Estimate current: 60mA per LED at full white for WS2812/SK6812
        per_led_ma = 60 if "APA102" not in protocol else 40
        chains.append({
            "chain_length": len(chain_refs),
            "first_led": chain_refs[0],
            "last_led": chain_refs[-1],
            "data_in_net": led_din_net.get(chain_refs[0], ""),
            "protocol": protocol,
            "led_type": first_comp.get("value", ""),
            "estimated_current_mA": len(chain_refs) * per_led_ma,
            "components": chain_refs,
            "detector": "detect_addressable_leds",
            "rule_id": "AL-DET",
            "category": "led_control",
            "severity": "info",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "summary": f"Addressable LED chain: {len(chain_refs)} LEDs ({protocol})",
            "description": f"Detected addressable LED chain of {len(chain_refs)} {first_comp.get('value', '')} LEDs.",
            "nets": [led_din_net.get(chain_refs[0], "")] if led_din_net.get(chain_refs[0]) else [],
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "LED Control", "impact": "", "standard_ref": ""},
            "provenance": make_provenance("aled_data_chain", "deterministic", claimed_components=[chain_refs[0]]),
        })

    # Also pick up single LEDs not in a chain
    for led_ref in addr_leds:
        if led_ref not in used:
            comp = addr_leds[led_ref]
            protocol = _get_protocol(comp)
            per_led_ma = 60 if "APA102" not in protocol else 40
            chains.append({
                "chain_length": 1,
                "first_led": led_ref,
                "last_led": led_ref,
                "data_in_net": led_din_net.get(led_ref, ""),
                "protocol": protocol,
                "led_type": comp.get("value", ""),
                "estimated_current_mA": per_led_ma,
                "components": [led_ref],
                "detector": "detect_addressable_leds",
                "rule_id": "AL-DET",
                "category": "led_control",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Addressable LED {led_ref} ({comp.get('value', '')}) [{protocol}]",
                "description": f"Detected single addressable LED {led_ref} ({comp.get('value', '')}).",
                "nets": [led_din_net.get(led_ref, "")] if led_din_net.get(led_ref) else [],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "LED Control", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("aled_data_chain", "deterministic", claimed_components=[led_ref]),
            })

    return chains


# ---------------------------------------------------------------------------
# ESD Protection Coverage Audit
# ---------------------------------------------------------------------------

# Connector interface classification for ESD risk level
_ESD_HIGH_RISK_KEYWORDS = (
    "usb", "hdmi", "ethernet", "rj45", "can", "rs485", "rs232", "rs-485",
    "rs-232", "displayport", "thunderbolt", "firewire", "ieee1394",
)
_ESD_MEDIUM_RISK_KEYWORDS = (
    "spi", "i2c", "iic", "uart", "serial", "header", "pin_header",
    "conn_01x", "conn_02x",
)
_ESD_LOW_RISK_KEYWORDS = (
    "debug", "swd", "jtag", "tag-connect", "st-link", "j-link",
    "programming", "isp", "icsp", "board_to_board", "b2b", "fpc",
)


def _classify_connector_interface(comp: dict) -> tuple[str, str]:
    """Classify connector interface type and risk level.

    Returns (interface_type, risk_level).
    """
    val = comp.get("value", "").lower()
    lib = comp.get("lib_id", "").lower()
    fp = comp.get("footprint", "").lower()
    combined = val + " " + lib + " " + fp

    def _kw_match(kw: str) -> bool:
        """Match keyword with word boundary for short keywords (<=3 chars)."""
        if len(kw) <= 3:
            return bool(re.search(r'\b' + re.escape(kw) + r'\b', combined))
        return kw in combined

    for kw in _ESD_HIGH_RISK_KEYWORDS:
        if _kw_match(kw):
            # More specific interface type
            if "usb" in combined:
                return "usb", "high_risk"
            if "hdmi" in combined:
                return "hdmi", "high_risk"
            if "ethernet" in combined or "rj45" in combined:
                return "ethernet", "high_risk"
            if _kw_match("can"):
                return "can", "high_risk"
            if "rs485" in combined or "rs-485" in combined:
                return "rs485", "high_risk"
            if "rs232" in combined or "rs-232" in combined:
                return "rs232", "high_risk"
            if "displayport" in combined:
                return "displayport", "high_risk"
            return kw, "high_risk"

    for kw in _ESD_MEDIUM_RISK_KEYWORDS:
        if _kw_match(kw):
            if _kw_match("spi"):
                return "spi", "medium_risk"
            if "i2c" in combined or _kw_match("iic"):
                return "i2c", "medium_risk"
            if "uart" in combined or "serial" in combined:
                return "uart", "medium_risk"
            return "header", "medium_risk"

    for kw in _ESD_LOW_RISK_KEYWORDS:
        if _kw_match(kw):
            return "debug", "low_risk"

    return "generic", "medium_risk"


def audit_esd_protection(ctx: AnalysisContext,
                         protection_devices: list[dict]) -> list[dict]:
    """Audit ESD protection coverage on external connectors.

    Cross-references connector signal nets against protection_devices output
    to identify unprotected external-facing signal lines.
    """
    # Build set of all protected nets
    protected_nets_set: set[str] = set()
    # Map net -> list of protection device refs
    net_to_esd: dict[str, list[str]] = {}
    for pd in protection_devices:
        pnets = pd.get("protected_nets", [])
        if not pnets:
            pn = pd.get("protected_net")
            if pn:
                pnets = [pn]
        for net in pnets:
            protected_nets_set.add(net)
            net_to_esd.setdefault(net, []).append(pd["ref"])

    # Quick lookup from ref -> protection_device entry
    pd_lookup: dict[str, dict] = {pd["ref"]: pd for pd in protection_devices}

    results: list[dict] = []

    for comp in ctx.components:
        if comp["type"] != "connector":
            continue

        interface_type, risk_level = _classify_connector_interface(comp)

        # Collect signal nets on this connector (exclude GND and power rails)
        signal_nets: list[str] = []
        for pin_num, (net_name, _) in ctx.ref_pins.get(comp["reference"], {}).items():
            if not net_name:
                continue
            if ctx.is_ground(net_name) or ctx.is_power_net(net_name):
                continue
            if net_name not in signal_nets:
                signal_nets.append(net_name)

        if not signal_nets:
            continue

        signal_nets.sort()
        prot = sorted(n for n in signal_nets if n in protected_nets_set)
        unprot = sorted(n for n in signal_nets if n not in protected_nets_set)

        if len(unprot) == 0:
            coverage = "full"
        elif len(prot) == 0:
            coverage = "none"
        else:
            coverage = "partial"

        # Collect ESD device refs covering this connector
        esd_refs: list[str] = sorted({
            ref for n in prot for ref in net_to_esd.get(n, [])
        })

        # Build detailed info for each ESD device
        esd_device_details: list[dict] = []
        for esd_ref in esd_refs:
            esd_comp = ctx.comp_lookup.get(esd_ref, {})
            detail: dict = {
                "ref": esd_ref,
                "value": esd_comp.get("value", ""),
                "lib_id": esd_comp.get("lib_id", ""),
            }
            # Pull protection_type from the protection_devices entry
            pd_entry = pd_lookup.get(esd_ref)
            if pd_entry:
                detail["protection_type"] = pd_entry.get("type", "")
            esd_device_details.append(detail)

        results.append({
            "connector_ref": comp["reference"],
            "connector_value": comp.get("value", ""),
            "interface_type": interface_type,
            "risk_level": risk_level,
            "signal_nets": signal_nets,
            "protected_nets": prot,
            "unprotected_nets": unprot,
            "coverage": coverage,
            "esd_devices": esd_refs,
            "esd_device_details": esd_device_details,
            "detector": "audit_esd_protection",
            "rule_id": "EP-AUD",
            "category": "protection",
            "severity": "info",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "summary": f"ESD audit {comp['reference']} ({interface_type}): {coverage} coverage",
            "description": f"ESD protection audit for {interface_type} connector {comp['reference']}: {coverage} coverage.",
            "components": [comp["reference"]] + esd_refs,
            "nets": signal_nets,
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "ESD Protection", "impact": "", "standard_ref": ""},
            "provenance": make_provenance("esd_coverage_audit", "deterministic", claimed_components=[comp["reference"]]),
        })

    return results


# ---------------------------------------------------------------------------
# Debug Interface Verification
# ---------------------------------------------------------------------------

_SWD_ALIASES: dict[str, tuple[str, ...]] = {
    "SWDIO": ("SWDIO", "SWD_IO", "TMS_SWDIO", "TMS/SWDIO"),
    "SWCLK": ("SWCLK", "SWD_CLK", "TCK_SWCLK", "TCK/SWCLK"),
}
_JTAG_ALIASES: dict[str, tuple[str, ...]] = {
    "TCK": ("TCK", "JTAG_TCK"),
    "TMS": ("TMS", "JTAG_TMS"),
    "TDI": ("TDI", "JTAG_TDI"),
    "TDO": ("TDO", "JTAG_TDO", "SWO"),
}
_RESET_ALIASES = ("NRESET", "NRST", "RESET", "RST", "SRST")
_DEBUG_CONNECTOR_KEYWORDS = (
    "jtag", "swd", "debug", "tag-connect", "tag_connect", "cortex",
    "st-link", "st_link", "j-link", "j_link", "arm_jtag", "arm_swd",
)


def detect_debug_interfaces(ctx: AnalysisContext) -> list[dict]:
    """Detect SWD/JTAG debug connectors and validate pin connections."""
    results: list[dict] = []

    for comp in ctx.components:
        if comp["type"] != "connector":
            continue

        val = comp.get("value", "").lower()
        lib = comp.get("lib_id", "").lower()
        combined = val + " " + lib

        # Stage 1: keyword match on value/lib_id
        is_debug_kw = any(kw in combined for kw in _DEBUG_CONNECTOR_KEYWORDS)

        # Gather pin names and nets for this connector
        pin_map: dict[str, tuple[str, str]] = {}  # pin_name_upper -> (net, pin_num)
        for pin_num, (net_name, _) in ctx.ref_pins.get(comp["reference"], {}).items():
            if not net_name or net_name not in ctx.nets:
                continue
            for p in ctx.nets[net_name]["pins"]:
                if p["component"] == comp["reference"] and p["pin_number"] == pin_num:
                    pname = p.get("pin_name", "").upper().replace(" ", "")
                    if pname:
                        pin_map[pname] = (net_name, pin_num)
                    break

        # Stage 2: classify interface by pin names found
        swd_found: dict[str, dict] = {}
        jtag_found: dict[str, dict] = {}

        for canonical, aliases in _SWD_ALIASES.items():
            for alias in aliases:
                # Check pin name match
                if alias in pin_map:
                    swd_found[canonical] = {"net": pin_map[alias][0], "pin_num": pin_map[alias][1]}
                    break
                # Check net name match (for generic connectors)
                for pname, (net, pnum) in pin_map.items():
                    if alias in net.upper():
                        swd_found[canonical] = {"net": net, "pin_num": pnum}
                        break
                if canonical in swd_found:
                    break

        for canonical, aliases in _JTAG_ALIASES.items():
            for alias in aliases:
                if alias in pin_map:
                    jtag_found[canonical] = {"net": pin_map[alias][0], "pin_num": pin_map[alias][1]}
                    break
                for pname, (net, pnum) in pin_map.items():
                    if alias in net.upper():
                        jtag_found[canonical] = {"net": net, "pin_num": pnum}
                        break
                if canonical in jtag_found:
                    break

        # Check for reset pin
        reset_info = None
        for alias in _RESET_ALIASES:
            if alias in pin_map:
                reset_info = {"net": pin_map[alias][0], "pin_num": pin_map[alias][1]}
                break
            for pname, (net, pnum) in pin_map.items():
                if alias in net.upper():
                    reset_info = {"net": net, "pin_num": pnum}
                    break
            if reset_info:
                break

        # Determine interface type
        has_swd = len(swd_found) >= 2  # SWDIO + SWCLK
        has_jtag = len(jtag_found) >= 3  # TCK + TMS + TDI (TDO optional)

        if not has_swd and not has_jtag and not is_debug_kw:
            continue

        if has_jtag and len(jtag_found) >= 4:
            interface_type = "jtag"
        elif has_swd:
            interface_type = "swd"
        elif has_jtag:
            interface_type = "jtag"
        elif is_debug_kw:
            # Keyword match but can't determine exact interface
            interface_type = "swd" if "swd" in combined else "jtag" if "jtag" in combined else "debug"
        else:
            continue

        # Build pins_found map with IC tracing
        all_pins = swd_found.copy() if interface_type == "swd" else jtag_found.copy()
        if reset_info:
            all_pins["nRESET"] = reset_info

        pins_found: dict[str, dict] = {}
        target_ics: list[str] = []
        for canonical, info in all_pins.items():
            net = info["net"]
            entry: dict = {"net": net}
            # Trace to an IC (MCU, FPGA)
            if net in ctx.nets:
                for p in ctx.nets[net]["pins"]:
                    if p["component"] == comp["reference"]:
                        continue
                    ic = ctx.comp_lookup.get(p["component"])
                    if ic and ic["type"] == "ic":
                        entry["connected_to_ic"] = p["component"]
                        if p["component"] not in target_ics:
                            target_ics.append(p["component"])
                        break
            pins_found[canonical] = entry

        # Determine missing and floating pins
        if interface_type == "swd":
            required = {"SWDIO", "SWCLK"}
        elif interface_type == "jtag":
            required = {"TCK", "TMS", "TDI", "TDO"}
        else:
            required = set()

        missing_pins = sorted(required - set(pins_found.keys()))

        # Check for floating (no-connect) pins among optional pins
        floating_pins: list[str] = []
        optional_check = {"SWO", "nRESET"} if interface_type == "swd" else {"TRST", "nRESET"}
        for alias_set in (_SWD_ALIASES, _JTAG_ALIASES):
            for canonical, aliases in alias_set.items():
                if canonical in pins_found:
                    continue
                if canonical not in optional_check:
                    continue
                for alias in aliases:
                    if alias in pin_map:
                        # Pin exists but wasn't matched — check if NC
                        net = pin_map[alias][0]
                        if net in ctx.nets and len(ctx.nets[net]["pins"]) <= 1:
                            floating_pins.append(canonical)
                        break

        # Determine target IC (most common)
        target_ic = target_ics[0] if target_ics else None

        status = "pass" if not missing_pins else "incomplete"

        di_comps = [comp["reference"]] + ([target_ic] if target_ic else [])
        results.append({
            "connector_ref": comp["reference"],
            "connector_value": comp.get("value", ""),
            "interface_type": interface_type,
            "pins_found": pins_found,
            "missing_pins": missing_pins,
            "floating_pins": floating_pins,
            "target_ic": target_ic,
            "status": status,
            "detector": "detect_debug_interfaces",
            "rule_id": "DI-DET",
            "category": "debug",
            "severity": "info",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "summary": f"Debug interface {comp['reference']} ({interface_type}): {status}",
            "description": f"Detected {interface_type} debug interface on connector {comp['reference']}.",
            "components": di_comps,
            "nets": [],
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "Debug", "impact": "", "standard_ref": ""},
            "provenance": make_provenance(f"debug_{interface_type}", "deterministic", claimed_components=[comp["reference"]]),
        })

    return results


# ---------------------------------------------------------------------------
# Power Path / Load Switch Detection
# ---------------------------------------------------------------------------

_LOAD_SWITCH_KEYWORDS = (
    "tps229", "tps2291", "tps2293", "tps2295",
    "tps2281", "tps2283", "tps2285",
    "tps2211", "tps2219", "tps2221",
    "tps22918", "tps22919", "tps22810",
    "sy6280", "sy6282", "sy6288",
    "rt9742", "rt9701", "ap2281", "ap2191",
    "stmps2", "ncp380", "ncp381",
    "mic205", "mic209",
)

_IDEAL_DIODE_KEYWORDS = (
    "ltc4412", "ltc4413", "ltc4414",
    "tps2113", "tps2115", "tps2121",
    "lm66100", "lm66200",
    "sm74611",
)

_USB_PD_KEYWORDS = (
    "fusb302", "stusb4500", "cypd3177", "husb238",
    "tps65987", "tps65988", "max77958",
    "ccg3", "ccg6",
)

# Pin name patterns for classification
_POWER_IN_PINS = {"VIN", "IN", "V_IN", "VINA", "VINB", "VIN1", "VIN2", "SUP", "VS"}
_POWER_OUT_PINS = {"VOUT", "OUT", "V_OUT", "VOUTA", "VOUTB", "VOUT1", "VOUT2"}
_ENABLE_PINS = {"EN", "ENABLE", "ON", "ON_OFF", "CTRL", "CE", "SHDN", "SHUTDOWN"}
_VBUS_PINS = {"VBUS", "V_BUS"}
_CC_PINS = {"CC1", "CC2", "CC"}
_SBU_PINS = {"SBU1", "SBU2", "SBU"}


def detect_power_path(ctx: AnalysisContext) -> list[dict]:
    """Detect load switches, ideal diodes, power MUXes, and USB PD controllers."""
    results: list[dict] = []
    matched_refs: set[str] = set()

    for comp in ctx.components:
        if comp["type"] != "ic":
            continue
        ref = comp["reference"]
        if ref in matched_refs:
            continue

        val = comp.get("value", "").lower()
        lib = comp.get("lib_id", "").lower()
        combined = val + " " + lib

        # Classify device type
        device_type = None
        if any(kw in combined for kw in _LOAD_SWITCH_KEYWORDS):
            device_type = "load_switch"
        elif any(kw in combined for kw in _IDEAL_DIODE_KEYWORDS):
            # Distinguish ideal diode from power MUX by pin count/keywords
            if any(kw in combined for kw in ("tps2113", "tps2115", "tps2121")):
                device_type = "power_mux"
            else:
                device_type = "ideal_diode"
        elif any(kw in combined for kw in _USB_PD_KEYWORDS):
            device_type = "usb_pd_controller"

        if not device_type:
            continue

        matched_refs.add(ref)

        # Map pin names to nets
        pin_nets: dict[str, str] = {}  # pin_name_upper -> net
        for pin_num, (net_name, _) in ctx.ref_pins.get(ref, {}).items():
            if not net_name:
                continue
            if net_name in ctx.nets:
                for p in ctx.nets[net_name]["pins"]:
                    if p["component"] == ref and p["pin_number"] == pin_num:
                        pname = p.get("pin_name", "").upper().replace(" ", "").replace("/", "_")
                        if pname:
                            pin_nets[pname] = net_name
                        break

        entry: dict = {
            "ref": ref,
            "value": comp.get("value", ""),
            "type": device_type,
        }

        if device_type == "load_switch":
            # Find input, output, enable nets
            input_rail = None
            output_rail = None
            enable_net = None

            for pname, net in pin_nets.items():
                if pname in _POWER_IN_PINS or pname.startswith("VIN"):
                    input_rail = net
                elif pname in _POWER_OUT_PINS or pname.startswith("VOUT"):
                    output_rail = net
                elif pname in _ENABLE_PINS or pname.startswith("EN"):
                    enable_net = net

            # Fallback: if no named pins found, infer from power nets
            if not input_rail and not output_rail:
                power_nets = [n for pn, n in pin_nets.items()
                              if ctx.is_power_net(n) and not ctx.is_ground(n)]
                if len(power_nets) >= 2:
                    input_rail = power_nets[0]
                    output_rail = power_nets[1]
                elif len(power_nets) == 1:
                    input_rail = power_nets[0]

            # Determine enable polarity from pin name
            enable_active_high = True
            for pname in pin_nets:
                if pname in ("SHDN", "SHUTDOWN"):
                    enable_active_high = False
                    if not enable_net:
                        enable_net = pin_nets[pname]
                    break

            entry["input_rail"] = input_rail
            entry["output_rail"] = output_rail
            entry["enable_net"] = enable_net
            entry["enable_active_high"] = enable_active_high

        elif device_type in ("ideal_diode", "power_mux"):
            # Find multiple inputs and single output
            inputs: list[str] = []
            output_rail = None

            for pname, net in pin_nets.items():
                if pname in _POWER_IN_PINS or pname.startswith("VIN"):
                    inputs.append(net)
                elif pname in _POWER_OUT_PINS or pname.startswith("VOUT"):
                    output_rail = net

            # Fallback for ideal diodes: anode is input, cathode is output
            if not inputs and not output_rail:
                power_nets = [n for pn, n in pin_nets.items()
                              if ctx.is_power_net(n) and not ctx.is_ground(n)]
                if len(power_nets) >= 2:
                    inputs = power_nets[:-1]
                    output_rail = power_nets[-1]

            entry["input_rails"] = inputs
            entry["output_rail"] = output_rail

        elif device_type == "usb_pd_controller":
            vbus_net = None
            cc_nets: list[str] = []
            sbu_nets: list[str] = []

            for pname, net in pin_nets.items():
                if pname in _VBUS_PINS or pname.startswith("VBUS"):
                    vbus_net = net
                elif pname in _CC_PINS or pname.startswith("CC"):
                    cc_nets.append(net)
                elif pname in _SBU_PINS or pname.startswith("SBU"):
                    sbu_nets.append(net)

            entry["vbus_net"] = vbus_net
            entry["cc_nets"] = cc_nets
            entry["sbu_nets"] = sbu_nets

            # USB-C CC resistor validation
            # UFP (sink) requires 5.1kΩ ±10% pull-down on each CC pin to GND
            # DFP (source) uses 56kΩ (default USB), 22kΩ (1.5A), or 10kΩ (3A)
            # PD controller IC on CC nets means discrete resistors not required
            cc_resistor_findings = []
            has_pd_controller = bool(entry.get("pd_controller"))

            if cc_nets and not has_pd_controller:
                for cc_net in cc_nets:
                    if cc_net not in ctx.nets:
                        continue
                    cc_resistors = []
                    for pin in ctx.nets[cc_net].get("pins", []):
                        comp = ctx.comp_lookup.get(pin["component"])
                        if not comp or comp["type"] != "resistor":
                            continue
                        r_val = ctx.parsed_values.get(pin["component"])
                        if r_val is None:
                            continue
                        # Check which net the other pin connects to
                        n1, n2 = ctx.get_two_pin_nets(pin["component"])
                        other_net = n2 if n1 == cc_net else n1
                        if other_net and ctx.is_ground(other_net):
                            cc_resistors.append({
                                "ref": pin["component"],
                                "ohms": r_val,
                                "value": comp.get("value", ""),
                                "to_net": other_net,
                            })

                    if not cc_resistors:
                        cc_resistor_findings.append({
                            "net": cc_net,
                            "status": "missing",
                            "message": f"No pull-down resistor on {cc_net} — "
                                       f"required for USB-C sink (UFP) role",
                        })
                    else:
                        for cr in cc_resistors:
                            r = cr["ohms"]
                            # 5.1kΩ ±10% for sink (UFP)
                            if 4590 <= r <= 5610:
                                cc_resistor_findings.append({
                                    "net": cc_net,
                                    "ref": cr["ref"],
                                    "ohms": r,
                                    "status": "correct_sink",
                                    "message": f"{cr['ref']} ({cr['value']}) on {cc_net} — "
                                               f"correct for UFP/sink role",
                                })
                            elif 50400 <= r <= 61600:  # 56kΩ ±10% = default USB
                                cc_resistor_findings.append({
                                    "net": cc_net, "ref": cr["ref"], "ohms": r,
                                    "status": "source_default",
                                    "message": f"{cr['ref']} ({cr['value']}) — "
                                               f"DFP source, default USB current",
                                })
                            elif 19800 <= r <= 24200:  # 22kΩ ±10% = 1.5A
                                cc_resistor_findings.append({
                                    "net": cc_net, "ref": cr["ref"], "ohms": r,
                                    "status": "source_1_5A",
                                    "message": f"{cr['ref']} ({cr['value']}) — "
                                               f"DFP source, 1.5A advertisement",
                                })
                            elif 9000 <= r <= 11000:  # 10kΩ ±10% = 3A
                                cc_resistor_findings.append({
                                    "net": cc_net, "ref": cr["ref"], "ohms": r,
                                    "status": "source_3A",
                                    "message": f"{cr['ref']} ({cr['value']}) — "
                                               f"DFP source, 3A advertisement",
                                })
                            else:
                                cc_resistor_findings.append({
                                    "net": cc_net, "ref": cr["ref"], "ohms": r,
                                    "status": "unexpected_value",
                                    "message": f"{cr['ref']} ({cr['value']}) = {r:.0f}Ω on {cc_net} — "
                                               f"not a standard USB-C CC value "
                                               f"(expected 5.1kΩ sink or 56k/22k/10k source)",
                                })

            if cc_resistor_findings:
                entry["cc_resistor_check"] = cc_resistor_findings

        entry.setdefault("detector", "detect_power_path")
        entry.setdefault("rule_id", "PP-DET")
        entry.setdefault("category", "power_management")
        entry.setdefault("severity", "info")
        entry.setdefault("confidence", "deterministic")
        entry.setdefault("evidence_source", "topology")
        entry.setdefault("summary", f"Power path {ref} ({comp.get('value', '')}) [{entry.get('type', device_type)}]")
        entry.setdefault("description", f"Detected {device_type} power path component {ref}.")
        entry.setdefault("components", [ref])
        entry.setdefault("nets", [])
        entry.setdefault("pins", [])
        entry.setdefault("recommendation", "")
        entry.setdefault("report_context", {"section": "Power Management", "impact": "", "standard_ref": ""})
        entry["provenance"] = make_provenance("ppath_topology", "deterministic", claimed_components=[ref])
        results.append(entry)

    return results


# ---------------------------------------------------------------------------
# ADC Signal Conditioning
# ---------------------------------------------------------------------------

_ADC_IC_KEYWORDS = (
    "ads1", "ads8", "mcp33", "mcp34", "mcp35",
    "max114", "max119", "max11", "ltc24", "ltc23",
    "ad7", "adc08", "adc12", "ads12", "ads13",
    "mcp32", "nau7802",
)

_VREF_IC_KEYWORDS = (
    "ref20", "ref30", "ref31", "ref32", "ref33", "ref19",
    "lm431", "tl431", "lm4040", "lt1009", "ad584",
    "adr44", "adr36", "adr38", "max60", "lt6656",
    "mcp15", "lm385",
)

_ADC_PIN_PREFIXES = ("AIN", "ADC", "AN", "CH", "INP", "INN", "IN+", "IN-",
                     "AINP", "AINN", "MUX", "VIN")
_VREF_PIN_NAMES = {"VREF", "REFIN", "REFOUT", "REF", "REF+", "REF-",
                   "VREF+", "VREF-", "VREFP", "VREFN", "REFP", "REFN"}
_SPI_PIN_NAMES = {"SCLK", "SCK", "CLK", "MOSI", "SDI", "DIN", "MISO",
                  "SDO", "DOUT", "CS", "CSN", "SS", "NSS"}
_I2C_PIN_NAMES = {"SDA", "SCL"}

# ADC resolution inference from part number prefix
_ADC_RESOLUTION_MAP = {
    "ads111": 16, "ads101": 12, "ads131": 24, "ads126": 24,
    "ads861": 16, "ads868": 16,
    "mcp320": 12, "mcp330": 10, "mcp340": 10, "mcp342": 18,
    "mcp346": 16, "mcp356": 24, "mcp355": 24,
    "max1161": 12, "max1163": 12, "max1194": 10, "max1198": 8,
    "max1192": 10, "max1141": 14,
    "ltc24": 24, "ltc23": 16,
    "ad760": 16, "ad770": 14, "ad799": 8,
    "adc081": 8, "adc082": 8, "adc121": 12, "adc122": 12,
    "nau780": 24,
}


def _infer_adc_resolution(value: str, lib_id: str) -> int | None:
    """Infer ADC resolution in bits from part number."""
    combined = (value + " " + lib_id).lower()
    for prefix, bits in _ADC_RESOLUTION_MAP.items():
        if prefix in combined:
            return bits
    return None


def _infer_interface(pin_names: set[str]) -> str | None:
    """Infer communication interface from pin names."""
    if pin_names & _SPI_PIN_NAMES:
        return "spi"
    if pin_names & _I2C_PIN_NAMES:
        return "i2c"
    return None


def detect_adc_circuits(ctx: AnalysisContext,
                        rc_filters: list[dict],
                        protection_devices: list[dict]) -> list[dict]:
    """Detect external ADC ICs and voltage reference ICs.

    Cross-references rc_filters for anti-aliasing and protection_devices
    for input protection on ADC input nets.
    """
    results: list[dict] = []
    matched_refs: set[str] = set()

    # Build net → RC filter index for anti-aliasing cross-reference
    rc_by_net: dict[str, list[dict]] = {}
    for rcf in rc_filters:
        for key in ("resistor", "capacitor"):
            comp = rcf.get(key, {})
            ref = comp.get("reference")
            if ref:
                for pin_num, (net, _) in ctx.ref_pins.get(ref, {}).items():
                    if net:
                        rc_by_net.setdefault(net, []).append(rcf)

    # Build net → protection device index
    prot_by_net: dict[str, list[dict]] = {}
    for pd in protection_devices:
        pnets = pd.get("protected_nets", [])
        if not pnets:
            pn = pd.get("protected_net")
            if pn:
                pnets = [pn]
        for net in pnets:
            prot_by_net.setdefault(net, []).append(pd)

    # Phase 1: Detect VREF ICs (needed before ADCs so we can link them)
    vref_entries: dict[str, dict] = {}  # ref -> entry
    vref_output_nets: dict[str, str] = {}  # net -> vref_ref

    for comp in ctx.components:
        if comp["type"] != "ic":
            continue
        ref = comp["reference"]
        val = comp.get("value", "").lower()
        lib = comp.get("lib_id", "").lower()
        combined = val + " " + lib

        if not any(kw in combined for kw in _VREF_IC_KEYWORDS):
            continue
        if ref in matched_refs:
            continue
        matched_refs.add(ref)

        # Infer output voltage
        vref_v, _ = lookup_regulator_vref(comp.get("value", ""), comp.get("lib_id", ""))

        # Find output net
        output_net = None
        for pin_num, (net_name, _) in ctx.ref_pins.get(ref, {}).items():
            if not net_name or ctx.is_ground(net_name):
                continue
            if net_name in ctx.nets:
                for p in ctx.nets[net_name]["pins"]:
                    if p["component"] == ref and p["pin_number"] == pin_num:
                        pname = p.get("pin_name", "").upper()
                        if pname in _VREF_PIN_NAMES or pname in ("OUT", "VOUT", "OUTPUT"):
                            output_net = net_name
                            break
            if output_net:
                break

        # Fallback: for 2-3 pin VREFs (e.g., TL431, LM4040), use non-power, non-ground net
        if not output_net:
            for pin_num, (net_name, _) in ctx.ref_pins.get(ref, {}).items():
                if net_name and not ctx.is_ground(net_name) and not ctx.is_power_net(net_name):
                    output_net = net_name
                    break

        entry = {
            "ref": ref,
            "value": comp.get("value", ""),
            "type": "voltage_reference",
            "output_voltage": vref_v,
            "output_net": output_net,
            "consumers": [],
            "detector": "detect_adc_circuits",
            "rule_id": "AD-DET",
            "category": "analog",
            "severity": "info",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "summary": f"Voltage reference {ref} ({comp.get('value', '')})" + (f" {vref_v}V" if vref_v else ""),
            "description": f"Detected voltage reference IC {ref}.",
            "components": [ref],
            "nets": [output_net] if output_net else [],
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "Analog", "impact": "", "standard_ref": ""},
        }

        entry["provenance"] = make_provenance("adc_ic_topology", "deterministic", claimed_components=[ref])

        if output_net:
            vref_output_nets[output_net] = ref
            # Trace consumers on the output net
            if output_net in ctx.nets:
                for p in ctx.nets[output_net]["pins"]:
                    if p["component"] != ref:
                        ic = ctx.comp_lookup.get(p["component"])
                        if ic and ic["type"] == "ic" and p["component"] not in entry["consumers"]:
                            entry["consumers"].append(p["component"])

        vref_entries[ref] = entry
        results.append(entry)

    # Phase 2: Detect ADC ICs
    for comp in ctx.components:
        if comp["type"] != "ic":
            continue
        ref = comp["reference"]
        if ref in matched_refs:
            continue
        val = comp.get("value", "").lower()
        lib = comp.get("lib_id", "").lower()
        combined = val + " " + lib

        if not any(kw in combined for kw in _ADC_IC_KEYWORDS):
            continue
        matched_refs.add(ref)

        # Map pin names to nets
        pin_nets: dict[str, str] = {}
        all_pin_names: set[str] = set()
        for pin_num, (net_name, _) in ctx.ref_pins.get(ref, {}).items():
            if not net_name or net_name not in ctx.nets:
                continue
            for p in ctx.nets[net_name]["pins"]:
                if p["component"] == ref and p["pin_number"] == pin_num:
                    pname = p.get("pin_name", "").upper().replace(" ", "")
                    if pname:
                        pin_nets[pname] = net_name
                        all_pin_names.add(pname)
                    break

        # Find analog input channels
        input_channels: list[str] = []
        channel_nets: dict[str, str] = {}  # channel_name -> net
        for pname, net in pin_nets.items():
            if any(pname.startswith(prefix) for prefix in _ADC_PIN_PREFIXES):
                if not ctx.is_power_net(net) and not ctx.is_ground(net):
                    input_channels.append(pname)
                    channel_nets[pname] = net
        input_channels.sort()

        # Infer resolution and interface
        resolution = _infer_adc_resolution(comp.get("value", ""), comp.get("lib_id", ""))
        interface = _infer_interface(all_pin_names)

        # Find VREF source
        vref_source = None
        for pname, net in pin_nets.items():
            if pname in _VREF_PIN_NAMES:
                if net in vref_output_nets:
                    vref_ref = vref_output_nets[net]
                    vref_entry = vref_entries.get(vref_ref, {})
                    vref_source = {
                        "ref": vref_ref,
                        "voltage": vref_entry.get("output_voltage"),
                    }
                break

        # Cross-reference anti-aliasing filters on input channels
        anti_aliasing: list[dict] = []
        for ch_name, ch_net in channel_nets.items():
            for rcf in rc_by_net.get(ch_net, []):
                aa_entry = {"channel": ch_name}
                r_comp = rcf.get("resistor", {})
                c_comp = rcf.get("capacitor", {})
                if r_comp.get("reference"):
                    aa_entry["rc_ref_r"] = r_comp["reference"]
                if c_comp.get("reference"):
                    aa_entry["rc_ref_c"] = c_comp["reference"]
                if rcf.get("cutoff_hz"):
                    aa_entry["cutoff_hz"] = rcf["cutoff_hz"]
                anti_aliasing.append(aa_entry)
                break  # one filter per channel

        # Cross-reference input protection
        input_protection: list[dict] = []
        for ch_name, ch_net in channel_nets.items():
            for pd in prot_by_net.get(ch_net, []):
                input_protection.append({
                    "channel": ch_name,
                    "device": pd["ref"],
                })
                break  # one protection device per channel

        adc_comps = [ref] + ([vref_source["ref"]] if vref_source else [])
        entry = {
            "ref": ref,
            "value": comp.get("value", ""),
            "type": "external_adc",
            "resolution_bits": resolution,
            "interface": interface,
            "input_channels": input_channels,
            "detector": "detect_adc_circuits",
            "rule_id": "AD-DET",
            "category": "analog",
            "severity": "info",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "summary": f"ADC {ref} ({comp.get('value', '')})" + (f" {resolution}-bit" if resolution else ""),
            "description": f"Detected external ADC {ref}" + (f" ({resolution}-bit)" if resolution else "") + ".",
            "components": adc_comps,
            "nets": [],
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "Analog", "impact": "", "standard_ref": ""},
        }
        if vref_source:
            entry["vref_source"] = vref_source
        if anti_aliasing:
            entry["anti_aliasing"] = anti_aliasing
        if input_protection:
            entry["input_protection"] = input_protection

        entry["provenance"] = make_provenance("adc_ic_topology", "deterministic", claimed_components=[ref])
        results.append(entry)

    return results


# ---------------------------------------------------------------------------
# Reset / Supervisor Circuits
# ---------------------------------------------------------------------------

_SUPERVISOR_IC_KEYWORDS = (
    "tps38", "tps37", "max809", "max810", "max803",
    "stm6315", "stm690", "mcp120", "mcp130",
    "cat811", "cat810", "sgm809", "apx803", "bd48",
    "adm803", "adm809", "adm810",
)

_WATCHDOG_IC_KEYWORDS = (
    "max6369", "max6370", "max6381",
    "tps3431", "tps3813", "tps3823", "tps3824",
    "adm6316", "adm6320", "stwd100",
)

_RESET_OUTPUT_PINS = {"RST", "RESET", "NRST", "NRESET", "~{RST}", "~{RESET}",
                      "~{NRST}", "~{NRESET}", "RSTN", "RESETN", "MR", "RESETOUT",
                      "RESET_OUT", "RST_OUT", "RSTOUT"}
_RESET_INPUT_PINS = {"NRST", "NRESET", "RST", "RESET", "~{RST}", "~{RESET}",
                     "~{NRST}", "~{NRESET}", "RSTN", "RESETN"}
_WDI_PINS = {"WDI", "WD", "WDT", "WDOG"}
_SUPERVISOR_VIN_PINS = {"VIN", "SENSE", "VSS", "VS", "IN", "VCC", "VDD"}


def _is_reset_net_name(net_name: str) -> bool:
    """Check if a net name suggests it's a reset signal."""
    nu = net_name.upper().replace("-", "").replace("_", "").replace(" ", "")
    return any(k in nu for k in ("NRST", "NRESET", "RESET", "RST"))


def _find_target_ic_on_reset_net(ctx: AnalysisContext, reset_net: str,
                                  exclude_ref: str) -> str | None:
    """Trace a reset net to find the target MCU/IC."""
    if reset_net not in ctx.nets:
        return None
    for p in ctx.nets[reset_net]["pins"]:
        if p["component"] == exclude_ref:
            continue
        ic = ctx.comp_lookup.get(p["component"])
        if ic and ic["type"] == "ic":
            pname = p.get("pin_name", "").upper().replace(" ", "")
            if pname in _RESET_INPUT_PINS or _is_reset_net_name(reset_net):
                return p["component"]
    return None


def detect_reset_supervisors(ctx: AnalysisContext) -> list[dict]:
    """Detect voltage supervisor ICs, watchdog ICs, and RC reset networks."""
    results: list[dict] = []
    matched_refs: set[str] = set()

    for comp in ctx.components:
        if comp["type"] != "ic":
            continue
        ref = comp["reference"]
        if ref in matched_refs:
            continue
        val = comp.get("value", "").lower()
        lib = comp.get("lib_id", "").lower()
        combined = val + " " + lib

        # Classify
        is_supervisor = any(kw in combined for kw in _SUPERVISOR_IC_KEYWORDS)
        is_watchdog = any(kw in combined for kw in _WATCHDOG_IC_KEYWORDS)
        if not is_supervisor and not is_watchdog:
            continue
        matched_refs.add(ref)

        # Map pin names to nets
        pin_nets: dict[str, str] = {}
        for pin_num, (net_name, _) in ctx.ref_pins.get(ref, {}).items():
            if not net_name or net_name not in ctx.nets:
                continue
            for p in ctx.nets[net_name]["pins"]:
                if p["component"] == ref and p["pin_number"] == pin_num:
                    pname = p.get("pin_name", "").upper().replace(" ", "")
                    if pname:
                        pin_nets[pname] = net_name
                    break

        # Find reset output pin
        reset_net = None
        reset_active_low = True
        for pname, net in pin_nets.items():
            if pname in _RESET_OUTPUT_PINS:
                reset_net = net
                # Active-low if pin name has overbar or starts with N
                reset_active_low = ("~{" in pname or pname.startswith("N")
                                    or pname.startswith("RESET") and "N" not in pname)
                # Correction: plain "RST" or "RESET" is ambiguous — check for overbar
                if pname in ("RST", "RESET", "RESETOUT", "RESET_OUT", "RST_OUT", "RSTOUT"):
                    reset_active_low = True  # most supervisors are active-low
                break

        # Find target IC
        target_ic = _find_target_ic_on_reset_net(ctx, reset_net, ref) if reset_net else None

        if is_supervisor:
            # Find monitored rail (VIN/SENSE pin)
            monitored_rail = None
            for pname, net in pin_nets.items():
                if pname in _SUPERVISOR_VIN_PINS and ctx.is_power_net(net):
                    monitored_rail = net
                    break

            # Infer threshold voltage from part number
            threshold_v, _ = lookup_regulator_vref(comp.get("value", ""), comp.get("lib_id", ""))

            sup_comps = [ref] + ([target_ic] if target_ic else [])
            results.append({
                "ref": ref,
                "value": comp.get("value", ""),
                "type": "voltage_supervisor",
                "monitored_rail": monitored_rail,
                "threshold_voltage": threshold_v,
                "reset_net": reset_net,
                "target_ic": target_ic,
                "reset_active_low": reset_active_low,
                "detector": "detect_reset_supervisors",
                "rule_id": "RS-DET",
                "category": "power_management",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Voltage supervisor {ref} ({comp.get('value', '')})" + (f" monitoring {monitored_rail}" if monitored_rail else ""),
                "description": f"Detected voltage supervisor IC {ref}.",
                "components": sup_comps,
                "nets": [n for n in (monitored_rail, reset_net) if n],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Power Management", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("reset_supervisor_ic", "deterministic", claimed_components=[ref]),
            })

        elif is_watchdog:
            # Find WDI pin
            wdi_net = None
            for pname, net in pin_nets.items():
                if pname in _WDI_PINS:
                    wdi_net = net
                    break

            wd_comps = [ref] + ([target_ic] if target_ic else [])
            results.append({
                "ref": ref,
                "value": comp.get("value", ""),
                "type": "watchdog",
                "wdi_net": wdi_net,
                "reset_net": reset_net,
                "target_ic": target_ic,
                "detector": "detect_reset_supervisors",
                "rule_id": "RS-DET",
                "category": "power_management",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Watchdog {ref} ({comp.get('value', '')})",
                "description": f"Detected watchdog IC {ref}.",
                "components": wd_comps,
                "nets": [n for n in (wdi_net, reset_net) if n],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Power Management", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("reset_supervisor_ic", "deterministic", claimed_components=[ref]),
            })

    # Phase 2: Detect RC reset networks
    # Find nets that look like reset signals and have both a resistor and capacitor
    reset_nets_seen: set[str] = set()
    for net_name, net_info in ctx.nets.items():
        if not _is_reset_net_name(net_name):
            continue
        if net_name in reset_nets_seen:
            continue

        resistors: list[dict] = []
        capacitors: list[dict] = []
        target_ic = None

        for p in net_info["pins"]:
            comp = ctx.comp_lookup.get(p["component"])
            if not comp:
                continue
            if comp["type"] == "resistor":
                r_val = parse_value(comp.get("value", ""))
                if r_val and r_val >= 1000:  # at least 1k for reset RC
                    resistors.append({"ref": comp["reference"], "ohms": r_val})
            elif comp["type"] == "capacitor":
                c_val = parse_value(comp.get("value", ""), component_type="capacitor")
                if c_val and c_val >= 1e-9:  # at least 1nF
                    capacitors.append({"ref": comp["reference"], "farads": c_val})
            elif comp["type"] == "ic":
                pname = p.get("pin_name", "").upper().replace(" ", "")
                if pname in _RESET_INPUT_PINS:
                    target_ic = p["component"]

        if resistors and capacitors and target_ic:
            reset_nets_seen.add(net_name)
            r = resistors[0]
            c = capacitors[0]
            tau_s = r["ohms"] * c["farads"]
            results.append({
                "ref_r": r["ref"],
                "ref_c": c["ref"],
                "type": "rc_reset",
                "reset_net": net_name,
                "time_constant_ms": round(tau_s * 1000, 3),
                "target_ic": target_ic,
                "detector": "detect_reset_supervisors",
                "rule_id": "RS-DET",
                "category": "power_management",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"RC reset network on {net_name} ({round(tau_s * 1000, 3)} ms)",
                "description": f"Detected RC reset network on net {net_name}.",
                "components": [r["ref"], c["ref"]] + ([target_ic] if target_ic else []),
                "nets": [net_name],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Power Management", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("reset_supervisor_ic", "deterministic", claimed_components=[r["ref"], c["ref"]]),
            })

    return results


# ---------------------------------------------------------------------------
# Clock Distribution
# ---------------------------------------------------------------------------

_CLOCK_BUFFER_KEYWORDS = (
    "si535", "si534", "si533", "cdce9", "cdcel9", "cdcvf",
    "sit9", "cy22", "cy23", "lmk0", "ics55",
)

_PLL_KEYWORDS = (
    "adf43", "adf45", "max287", "si544", "si546",
    "lmx25", "hmc83",
)

_CLOCK_INPUT_PINS = {"CLKIN", "CLK_IN", "XCLK", "MCLK", "SCLK", "BCLK",
                     "FCLK", "REFCLK", "CLK", "CKIN", "XA", "XI", "XTAL_IN",
                     "XTAL1", "OSC_IN", "OSCI"}
_CLOCK_OUTPUT_PINS = {"CLKOUT", "CLK_OUT", "CLK0", "CLK1", "CLK2", "CLK3",
                      "CLK4", "CLK5", "CLK6", "CLK7", "FOUT", "MCLK_OUT",
                      "OUT0", "OUT1", "OUT2", "OUT3", "XB", "XO", "XTAL_OUT",
                      "XTAL2", "OSC_OUT", "OSCO"}


def _find_series_termination(ctx: AnalysisContext, net_name: str,
                              source_ref: str) -> dict | None:
    """Check for series termination resistor (22-100Ω) on a clock net."""
    if net_name not in ctx.nets:
        return None
    for p in ctx.nets[net_name]["pins"]:
        comp = ctx.comp_lookup.get(p["component"])
        if not comp or comp["type"] != "resistor" or p["component"] == source_ref:
            continue
        r_val = parse_value(comp.get("value", ""))
        if r_val and 22 <= r_val <= 100:
            return {"ref": comp["reference"], "ohms": r_val}
    return None


def _trace_clock_consumers(ctx: AnalysisContext, net_name: str,
                            source_ref: str) -> list[str]:
    """Find IC consumers on a clock net, excluding the source.

    When ctx.nq is available, traces through clock buffers to find
    downstream consumers (e.g., SI5351 → MCU, FPGA).
    """
    consumers: list[str] = []
    if net_name not in ctx.nets:
        return consumers
    seen: set[str] = {source_ref}
    for p in ctx.nets[net_name]["pins"]:
        ref = p["component"]
        if ref in seen:
            continue
        comp = ctx.comp_lookup.get(ref)
        if not comp or comp["type"] != "ic":
            continue
        seen.add(ref)
        # Check if this IC is a clock buffer — trace through to outputs
        if ctx.nq:
            val_lib = (comp.get("value", "") + " " + comp.get("lib_id", "")).lower()
            if any(kw in val_lib for kw in _CLOCK_BUFFER_KEYWORDS):
                for out_net in ctx.nq.trace_through(net_name, ref):
                    if ctx.is_ground(out_net) or ctx.is_power_net(out_net):
                        continue
                    for downstream in ctx.nq.ics_on_net(out_net, exclude_ref=ref):
                        dref = downstream["reference"]
                        if dref not in seen:
                            seen.add(dref)
                            consumers.append(dref)
                continue
        consumers.append(ref)
    return consumers


def detect_clock_distribution(ctx: AnalysisContext,
                               crystal_circuits: list[dict]) -> list[dict]:
    """Detect clock buffer/PLL ICs and trace oscillator outputs to consumers."""
    results: list[dict] = []
    matched_refs: set[str] = set()

    for comp in ctx.components:
        if comp["type"] != "ic":
            continue
        ref = comp["reference"]
        if ref in matched_refs:
            continue
        val = comp.get("value", "").lower()
        lib = comp.get("lib_id", "").lower()
        combined = val + " " + lib

        is_buffer = any(kw in combined for kw in _CLOCK_BUFFER_KEYWORDS)
        is_pll = any(kw in combined for kw in _PLL_KEYWORDS)
        if not is_buffer and not is_pll:
            continue
        matched_refs.add(ref)

        # Map pin names to nets
        pin_nets: dict[str, str] = {}
        for pin_num, (net_name, _) in ctx.ref_pins.get(ref, {}).items():
            if not net_name or net_name not in ctx.nets:
                continue
            for p in ctx.nets[net_name]["pins"]:
                if p["component"] == ref and p["pin_number"] == pin_num:
                    pname = p.get("pin_name", "").upper().replace(" ", "")
                    if pname:
                        pin_nets[pname] = net_name
                    break

        # Find reference/clock input
        ref_input = None
        ref_source = None
        for pname, net in pin_nets.items():
            if pname in _CLOCK_INPUT_PINS:
                ref_input = {"net": net}
                # Trace to find source (crystal or oscillator)
                if net in ctx.nets:
                    for p in ctx.nets[net]["pins"]:
                        if p["component"] == ref:
                            continue
                        src = ctx.comp_lookup.get(p["component"])
                        if src and src["type"] in ("crystal", "oscillator"):
                            ref_source = p["component"]
                            break
                if ref_source:
                    ref_input["source"] = ref_source
                break

        # Find clock outputs
        outputs: list[dict] = []
        for pname, net in sorted(pin_nets.items()):
            if pname in _CLOCK_OUTPUT_PINS:
                consumers = _trace_clock_consumers(ctx, net, ref)
                term = _find_series_termination(ctx, net, ref)
                outputs.append({
                    "pin": pname,
                    "net": net,
                    "consumers": consumers,
                    "series_termination": term,
                })

        device_type = "clock_generator" if is_buffer else "pll"
        entry: dict = {
            "ref": ref,
            "value": comp.get("value", ""),
            "type": device_type,
            "detector": "detect_clock_distribution",
            "rule_id": "CD-DET",
            "category": "timing",
            "severity": "info",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "summary": f"Clock {device_type} {ref} ({comp.get('value', '')})",
            "description": f"Detected {device_type} IC {ref}.",
            "components": [ref],
            "nets": [],
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "Timing", "impact": "", "standard_ref": ""},
        }
        if ref_input:
            entry["reference_input"] = ref_input
        if outputs:
            entry["outputs"] = outputs

        entry["provenance"] = make_provenance("clock_buffer_topology", "deterministic", claimed_components=[ref])
        results.append(entry)

    # Phase 2: Trace standalone oscillator outputs from crystal_circuits
    for xc in crystal_circuits:
        # Active oscillators have an output net but crystal_circuits doesn't trace consumers
        if xc.get("type") != "active_oscillator":
            continue
        osc_ref = xc.get("reference")
        if not osc_ref or osc_ref in matched_refs:
            continue

        output_net = xc.get("output_net")
        if not output_net:
            continue

        consumers = _trace_clock_consumers(ctx, output_net, osc_ref)
        if not consumers:
            continue

        term = _find_series_termination(ctx, output_net, osc_ref)
        results.append({
            "ref": osc_ref,
            "value": xc.get("value", ""),
            "type": "oscillator_output",
            "frequency_hz": xc.get("frequency_hz"),
            "output_net": output_net,
            "consumers": consumers,
            "series_termination": term,
            "detector": "detect_clock_distribution",
            "rule_id": "CD-DET",
            "category": "timing",
            "severity": "info",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "summary": f"Oscillator output {osc_ref} ({xc.get('value', '')})" + (f" {xc.get('frequency_hz', '')/1e6:.3g} MHz" if xc.get("frequency_hz") else ""),
            "description": f"Detected active oscillator {osc_ref} driving clock output.",
            "components": [osc_ref] + consumers,
            "nets": [output_net] if output_net else [],
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "Timing", "impact": "", "standard_ref": ""},
            "provenance": make_provenance("clock_buffer_topology", "deterministic", claimed_components=[osc_ref]),
        })

    return results


# ---------------------------------------------------------------------------
# Shared helper: build pin name → net map for an IC
# ---------------------------------------------------------------------------

def _build_pin_net_map(ctx: AnalysisContext, ref: str) -> dict[str, str]:
    """Build pin_name_upper → net_name map for a component."""
    pin_nets: dict[str, str] = {}
    for pin_num, (net_name, _) in ctx.ref_pins.get(ref, {}).items():
        if not net_name or net_name not in ctx.nets:
            continue
        for p in ctx.nets[net_name]["pins"]:
            if p["component"] == ref and p["pin_number"] == pin_num:
                pname = p.get("pin_name", "").upper().replace(" ", "")
                if pname:
                    pin_nets[pname] = net_name
                break
    return pin_nets


# ---------------------------------------------------------------------------
# Display / Touch Interface Detection
# ---------------------------------------------------------------------------

_DISPLAY_IC_KEYWORDS = (
    "ssd1306", "ssd1309", "ssd1327", "ssd1351",
    "st7735", "st7789", "st7796", "st7920",
    "ili9341", "ili9488", "ili9486", "ili9325",
    "hx8357", "uc1701", "sh1106", "sh1107",
    "nt35", "gc9a01", "rm68140",
    "ssd1681", "il0373", "gdew",
)

_TOUCH_IC_KEYWORDS = (
    "ft6236", "ft6336", "ft5436", "ft5x06",
    "gt911", "gt928", "gt9xx",
    "xpt2046", "tsc2046", "ads7843",
    "cst816", "cst328",
    "stmpe811", "stmpe610",
    "cap1188", "mpr121",
)

_DISPLAY_CONTROL_PINS = {"DC", "D/C", "A0", "RS", "CMD"}
_BACKLIGHT_PINS = {"BL", "LED", "LEDA", "BACKLIGHT", "BLK"}
_DISPLAY_RESET_PINS = {"RES", "RST", "RESET", "NRST"}

# Display type inference from IC keyword
_OLED_KEYWORDS = ("ssd1306", "ssd1309", "ssd1327", "ssd1351", "sh1106", "sh1107")
_EPAPER_KEYWORDS = ("ssd1681", "il0373", "gdew")


def detect_display_interfaces(ctx: AnalysisContext) -> list[dict]:
    """Detect display controller and touch controller ICs."""
    results: list[dict] = []
    matched_refs: set[str] = set()

    for comp in ctx.components:
        if comp["type"] != "ic":
            continue
        ref = comp["reference"]
        if ref in matched_refs:
            continue
        val = comp.get("value", "").lower()
        lib = comp.get("lib_id", "").lower()
        combined = val + " " + lib

        is_display = any(kw in combined for kw in _DISPLAY_IC_KEYWORDS)
        is_touch = any(kw in combined for kw in _TOUCH_IC_KEYWORDS)
        if not is_display and not is_touch:
            continue
        matched_refs.add(ref)

        pin_nets = _build_pin_net_map(ctx, ref)
        all_pins = set(pin_nets.keys())

        # Infer interface
        interface = None
        if all_pins & {"SCK", "SCLK", "CLK", "MOSI", "SDI", "SDA"} and all_pins & _DISPLAY_CONTROL_PINS:
            interface = "spi"
        elif all_pins & {"SCK", "SCLK", "CLK", "MOSI", "SDI", "DIN"}:
            interface = "spi"
        elif all_pins & {"SDA", "SCL"}:
            interface = "i2c"
        elif all_pins & {"D0", "D1", "D2", "D3"}:
            interface = "parallel"

        if is_display:
            # Classify display type
            display_type = "lcd"
            if any(kw in combined for kw in _OLED_KEYWORDS):
                display_type = "oled"
            elif any(kw in combined for kw in _EPAPER_KEYWORDS):
                display_type = "e-paper"

            # Find control pins
            dc_net = None
            for pname in _DISPLAY_CONTROL_PINS:
                if pname in pin_nets:
                    dc_net = pin_nets[pname]
                    break

            reset_net = None
            for pname in _DISPLAY_RESET_PINS:
                if pname in pin_nets:
                    reset_net = pin_nets[pname]
                    break

            # Find backlight
            backlight = None
            for pname in _BACKLIGHT_PINS:
                if pname in pin_nets:
                    bl_net = pin_nets[pname]
                    backlight = {"pin": pname, "net": bl_net}
                    # Check if a resistor or driver is on the BL net
                    if bl_net in ctx.nets:
                        for p in ctx.nets[bl_net]["pins"]:
                            if p["component"] == ref:
                                continue
                            rc = ctx.comp_lookup.get(p["component"])
                            if rc and rc["type"] == "resistor":
                                backlight["resistor"] = p["component"]
                            elif rc and rc["type"] == "ic":
                                backlight["driver_ic"] = p["component"]
                    break

            results.append({
                "ref": ref,
                "value": comp.get("value", ""),
                "type": "display",
                "display_type": display_type,
                "interface": interface,
                "dc_pin_net": dc_net,
                "reset_net": reset_net,
                "backlight": backlight,
                "detector": "detect_display_interfaces",
                "rule_id": "DP-DET",
                "category": "display",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Display {ref} ({comp.get('value', '')}) [{display_type}/{interface}]",
                "description": f"Detected {display_type} display controller IC {ref}.",
                "components": [ref],
                "nets": [n for n in (dc_net, reset_net) if n],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Display", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("display_controller", "deterministic", claimed_components=[ref]),
            })

        elif is_touch:
            # Find interrupt pin
            interrupt_net = None
            interrupt_connected = False
            for pname in ("INT", "IRQ", "PENIRQ", "nINT", "ALERT"):
                if pname in pin_nets:
                    interrupt_net = pin_nets[pname]
                    # Check if connected to an IC
                    if interrupt_net in ctx.nets:
                        for p in ctx.nets[interrupt_net]["pins"]:
                            if p["component"] == ref:
                                continue
                            ic = ctx.comp_lookup.get(p["component"])
                            if ic and ic["type"] == "ic":
                                interrupt_connected = True
                                break
                    break

            reset_net = None
            for pname in _DISPLAY_RESET_PINS:
                if pname in pin_nets:
                    reset_net = pin_nets[pname]
                    break

            results.append({
                "ref": ref,
                "value": comp.get("value", ""),
                "type": "touch_controller",
                "interface": interface,
                "interrupt_net": interrupt_net,
                "interrupt_connected": interrupt_connected,
                "reset_net": reset_net,
                "detector": "detect_display_interfaces",
                "rule_id": "DP-DET",
                "category": "display",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Touch controller {ref} ({comp.get('value', '')}) [{interface}]",
                "description": f"Detected touch controller IC {ref}.",
                "components": [ref],
                "nets": [n for n in (interrupt_net, reset_net) if n],
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Display", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("display_controller", "deterministic", claimed_components=[ref]),
            })

    return results


# ---------------------------------------------------------------------------
# Sensor Fusion Detection
# ---------------------------------------------------------------------------

_IMU_KEYWORDS = (
    "mpu6", "mpu9", "icm20", "icm42", "lsm6", "lsm9",
    "bno0", "bmi1", "bmi2", "bmi3",
    "lis2", "lis3", "lsm3", "adxl3",
    "kxtj3", "mc3419", "mma845",
)
_ENV_SENSOR_KEYWORDS = (
    "bme28", "bme68", "bmp28", "bmp39", "bmp58",
    "sht3", "sht4", "hdc10", "hdc20", "si70", "aht",
    "lps22", "lps25", "ms56", "dps310",
)
_MAG_KEYWORDS = (
    "hmc58", "qmc58", "lis3m", "lis2m", "mmc56",
    "ak8963", "ak0991", "bmm150", "rm3100",
)

_SENSOR_INT_PINS = {"INT", "INT1", "INT2", "DRDY", "IRQ", "ALERT", "RDY", "BUSY"}
_SENSOR_SPI_PINS = {"SCK", "SCLK", "CLK", "MOSI", "SDI", "MISO", "SDO", "CS", "CSN", "NCS"}
_SENSOR_I2C_PINS = {"SDA", "SCL"}


def detect_sensor_interfaces(ctx: AnalysisContext) -> list[dict]:
    """Detect IMU, environmental, and magnetometer sensor ICs."""
    results: list[dict] = []
    matched_refs: set[str] = set()

    # Collect all sensor entries with their bus nets for clustering
    sensor_bus_nets: dict[str, list[str]] = {}  # ref -> list of bus net names

    for comp in ctx.components:
        if comp["type"] != "ic":
            continue
        ref = comp["reference"]
        if ref in matched_refs:
            continue
        val = comp.get("value", "").lower()
        lib = comp.get("lib_id", "").lower()
        combined = val + " " + lib

        # Classify sensor type
        sensor_type = None
        if any(kw in combined for kw in _IMU_KEYWORDS):
            sensor_type = "motion"
        elif any(kw in combined for kw in _ENV_SENSOR_KEYWORDS):
            sensor_type = "environmental"
        elif any(kw in combined for kw in _MAG_KEYWORDS):
            sensor_type = "magnetic"

        if not sensor_type:
            continue
        matched_refs.add(ref)

        pin_nets = _build_pin_net_map(ctx, ref)
        all_pins = set(pin_nets.keys())

        # Infer interface
        interface = None
        bus_nets: list[str] = []
        if all_pins & _SENSOR_SPI_PINS:
            interface = "spi"
            for pname in ("SCK", "SCLK", "CLK", "MOSI", "SDI", "MISO", "SDO"):
                if pname in pin_nets:
                    bus_nets.append(pin_nets[pname])
        if all_pins & _SENSOR_I2C_PINS:
            # SPI takes precedence if CS pin present, else I2C
            if not (interface == "spi" and all_pins & {"CS", "CSN", "NCS"}):
                interface = "i2c"
                bus_nets = []
                for pname in ("SDA", "SCL"):
                    if pname in pin_nets:
                        bus_nets.append(pin_nets[pname])

        sensor_bus_nets[ref] = bus_nets

        # Check interrupt pins
        interrupt_pins: list[dict] = []
        for pname in sorted(all_pins & _SENSOR_INT_PINS):
            net = pin_nets[pname]
            connected_to = None
            if net in ctx.nets:
                for p in ctx.nets[net]["pins"]:
                    if p["component"] == ref:
                        continue
                    ic = ctx.comp_lookup.get(p["component"])
                    if ic and ic["type"] == "ic":
                        connected_to = p["component"]
                        break
            interrupt_pins.append({
                "pin": pname,
                "net": net,
                "connected_to_ic": connected_to,
            })

        results.append({
            "ref": ref,
            "value": comp.get("value", ""),
            "type": sensor_type,
            "interface": interface,
            "interrupt_pins": interrupt_pins,
            "bus_peers": [],  # filled in clustering pass
            "detector": "detect_sensor_interfaces",
            "rule_id": "SI-DET",
            "category": "sensors",
            "severity": "info",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "summary": f"Sensor {ref} ({comp.get('value', '')}) [{sensor_type}/{interface}]",
            "description": f"Detected {sensor_type} sensor IC {ref}.",
            "components": [ref],
            "nets": bus_nets,
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "Sensors", "impact": "", "standard_ref": ""},
            "provenance": make_provenance("sensor_ic_topology", "heuristic", claimed_components=[ref]),
        })

    # Clustering pass: find sensors sharing bus nets
    if len(results) >= 2:
        for i, entry in enumerate(results):
            ref = entry["ref"]
            my_nets = set(sensor_bus_nets.get(ref, []))
            if not my_nets:
                continue
            peers = []
            for j, other in enumerate(results):
                if i == j:
                    continue
                other_nets = set(sensor_bus_nets.get(other["ref"], []))
                if my_nets & other_nets:
                    peers.append(other["ref"])
            entry["bus_peers"] = peers

    return results


# ---------------------------------------------------------------------------
# Level Shifter Detection
# ---------------------------------------------------------------------------

_LEVEL_SHIFTER_KEYWORDS = (
    "txb0", "txs0", "tca9", "lsf0", "sn74lvc", "sn74avc",
    "sn74cb3", "sn74cbt", "nlsx", "nts0", "fxl", "adg320",
    "max395", "gtl2", "pca960", "tca641", "fxma", "txu0",
    # 4.1 expansion (rc.2): SparkFun + Manas reviews
    "lvc1t45", "lvc2t45", "lvc8t45",  # 74LVC*T45 / SN74LVC*T45 translator family
    "nvt20",                          # NXP NVT200x autobus translator
    "pca9306", "pca9517",             # NXP/TI I2C bus repeaters with level translation
)

_VCCA_PINS = {"VCCA", "VA", "VCC_A", "VREF1", "VREF_A", "VIN_A", "VDDA"}
_VCCB_PINS = {"VCCB", "VB", "VCC_B", "VREF2", "VREF_B", "VIN_B", "VDDB"}
_LS_ENABLE_PINS = {"OE", "EN", "ENABLE", "DIR"}

# Bidirectional vs unidirectional inference
_BIDIR_KEYWORDS = ("txb0", "gtl2", "lsf0", "fxma", "nlsx", "sn74cb3", "sn74cbt")
_UNIDIR_KEYWORDS = ("txs0", "sn74lvc", "sn74avc", "txu0")


def _infer_voltage(ctx: AnalysisContext, net_name: str | None) -> float | None:
    """Try to infer voltage from a power net name."""
    if not net_name:
        return None
    from kicad_utils import parse_voltage_from_net_name
    return parse_voltage_from_net_name(net_name)


def detect_level_shifters(ctx: AnalysisContext) -> list[dict]:
    """Detect level shifter ICs and discrete BSS138-based shifters."""
    results: list[dict] = []
    matched_refs: set[str] = set()

    # Phase 1: IC-based level shifters
    for comp in ctx.components:
        if comp["type"] != "ic":
            continue
        ref = comp["reference"]
        if ref in matched_refs:
            continue
        val = comp.get("value", "").lower()
        lib = comp.get("lib_id", "").lower()
        combined = val + " " + lib

        if not any(kw in combined for kw in _LEVEL_SHIFTER_KEYWORDS):
            continue

        # KH-227: Exclude pure logic gates (not level shifters)
        _val_lib = (comp.get("value", "") + " " + comp.get("lib_id", "")).lower()
        _logic_gate_patterns = ("1g00", "1g02", "1g04", "1g08", "1g14", "1g32",
                                "1g86", "2g00", "2g02", "2g04", "2g08", "2g14",
                                "2g32", "2g86", "3g14",
                                "inverter", "nand_gate", "nor_gate", "and_gate",
                                "or_gate", "xor_gate", "schmitt")
        if any(g in _val_lib for g in _logic_gate_patterns):
            continue

        matched_refs.add(ref)

        pin_nets = _build_pin_net_map(ctx, ref)
        all_pins = set(pin_nets.keys())

        # Find supply pins
        vcca_net = None
        vccb_net = None
        for pname in _VCCA_PINS:
            if pname in pin_nets:
                vcca_net = pin_nets[pname]
                break
        for pname in _VCCB_PINS:
            if pname in pin_nets:
                vccb_net = pin_nets[pname]
                break

        # Fallback: if no VCCA/VCCB found, look for VCC pins
        if not vcca_net and not vccb_net:
            vcc_nets = []
            for pname, net in pin_nets.items():
                if pname.startswith("VCC") or pname.startswith("VDD"):
                    if ctx.is_power_net(net) and not ctx.is_ground(net):
                        vcc_nets.append(net)
            if len(vcc_nets) >= 2:
                vcca_net = vcc_nets[0]
                vccb_net = vcc_nets[1]
            elif len(vcc_nets) == 1:
                vcca_net = vcc_nets[0]

        # Find signal nets (non-power, non-ground, non-enable)
        shifted_nets: list[str] = []
        for pname, net in pin_nets.items():
            if pname in _VCCA_PINS | _VCCB_PINS | _LS_ENABLE_PINS:
                continue
            if ctx.is_ground(net) or ctx.is_power_net(net):
                continue
            if net not in shifted_nets:
                shifted_nets.append(net)

        # Infer direction
        direction = "bidirectional"
        if any(kw in combined for kw in _UNIDIR_KEYWORDS):
            direction = "unidirectional"
        elif any(kw in combined for kw in _BIDIR_KEYWORDS):
            direction = "bidirectional"

        side_a: dict = {"supply_net": vcca_net}
        side_b: dict = {"supply_net": vccb_net}
        va = _infer_voltage(ctx, vcca_net)
        vb = _infer_voltage(ctx, vccb_net)
        if va:
            side_a["voltage"] = va
        if vb:
            side_b["voltage"] = vb

        results.append({
            "ref": ref,
            "value": comp.get("value", ""),
            "type": "level_shifter_ic",
            "direction": direction,
            "side_a": side_a,
            "side_b": side_b,
            "shifted_nets": sorted(shifted_nets),
            "channel_count": len(shifted_nets) // 2 or len(shifted_nets),
            "detector": "detect_level_shifters",
            "rule_id": "LS-DET",
            "category": "signal_integrity",
            "severity": "info",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "summary": f"Level shifter {ref} ({comp.get('value', '')}) [{direction}]",
            "description": f"Detected {direction} level shifter IC {ref}.",
            "components": [ref],
            "nets": sorted(shifted_nets),
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "Signal Integrity", "impact": "", "standard_ref": ""},
            "provenance": make_provenance("levelshift_topology", "deterministic", claimed_components=[ref]),
        })

    # Phase 2: Discrete BSS138 level shifters
    # Pattern: N-channel MOSFET with gate to low-voltage rail,
    # drain and source each with pull-up resistors to different voltage rails
    for comp in ctx.components:
        if comp["type"] != "transistor":
            continue
        ref = comp["reference"]
        if ref in matched_refs:
            continue
        val = comp.get("value", "").lower()
        lib = comp.get("lib_id", "").lower()
        combined = val + " " + lib

        # Only look for common discrete shifter MOSFETs
        if not any(kw in combined for kw in ("bss138", "2n7002", "bss84")):
            continue

        pin_nets = _build_pin_net_map(ctx, ref)

        gate_net = pin_nets.get("G") or pin_nets.get("GATE")
        drain_net = pin_nets.get("D") or pin_nets.get("DRAIN")
        source_net = pin_nets.get("S") or pin_nets.get("SOURCE")

        if not gate_net or not drain_net or not source_net:
            continue

        # Gate should connect to a power rail (low-voltage side)
        if not ctx.is_power_net(gate_net):
            continue

        # Find pull-up resistors on drain and source nets
        def _find_pullup(net_name):
            if not net_name or net_name not in ctx.nets:
                return None
            for p in ctx.nets[net_name]["pins"]:
                if p["component"] == ref:
                    continue
                rc = ctx.comp_lookup.get(p["component"])
                if not rc or rc["type"] != "resistor":
                    continue
                r_val = parse_value(rc.get("value", ""))
                if r_val and 1000 <= r_val <= 100000:  # 1k-100k typical pull-up
                    # Check other side goes to a power rail
                    rn1, _ = ctx.pin_net.get((rc["reference"], "1"), (None, None))
                    rn2, _ = ctx.pin_net.get((rc["reference"], "2"), (None, None))
                    other = rn2 if rn1 == net_name else rn1
                    if ctx.is_power_net(other):
                        return {"ref": rc["reference"], "supply_net": other}
            return None

        drain_pullup = _find_pullup(drain_net)
        source_pullup = _find_pullup(source_net)

        if not drain_pullup or not source_pullup:
            continue
        # Must pull up to different rails for level shifting
        if drain_pullup["supply_net"] == source_pullup["supply_net"]:
            continue

        matched_refs.add(ref)

        # Determine which side is A (low) and B (high)
        va = _infer_voltage(ctx, source_pullup["supply_net"])
        vb = _infer_voltage(ctx, drain_pullup["supply_net"])
        if va and vb and va > vb:
            # Swap so side_a is lower voltage
            source_pullup, drain_pullup = drain_pullup, source_pullup
            source_net, drain_net = drain_net, source_net

        ls_sig_nets = sorted({drain_net, source_net} - {gate_net})
        results.append({
            "ref": ref,
            "value": comp.get("value", ""),
            "type": "discrete_level_shifter",
            "gate_net": gate_net,
            "side_a": {"pullup_ref": source_pullup["ref"], "supply_net": source_pullup["supply_net"]},
            "side_b": {"pullup_ref": drain_pullup["ref"], "supply_net": drain_pullup["supply_net"]},
            "signal_nets": ls_sig_nets,
            "detector": "detect_level_shifters",
            "rule_id": "LS-DET",
            "category": "signal_integrity",
            "severity": "info",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "summary": f"Discrete level shifter {ref} ({comp.get('value', '')})",
            "description": f"Detected discrete BSS138-style level shifter using {ref}.",
            "components": [ref, source_pullup["ref"], drain_pullup["ref"]],
            "nets": ls_sig_nets,
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "Signal Integrity", "impact": "", "standard_ref": ""},
            "provenance": make_provenance("levelshift_topology", "deterministic", claimed_components=[ref]),
        })

    return results


# ---------------------------------------------------------------------------
# Audio Circuit Detection
# ---------------------------------------------------------------------------

_AUDIO_AMP_KEYWORDS = (
    "tpa31", "tpa32", "tpa62", "tpa60",
    "max983", "max984",
    "lm386", "lm48",
    "pam84", "pam83",
    "tas57", "tas21", "tas58",
    "tda7", "tda2",
    "ssm23", "ssm21",
    "sta3",
)

_AUDIO_CODEC_KEYWORDS = (
    "wm89", "wm87",
    "es83", "es81",
    "ak49", "ak45",
    "pcm51", "pcm17", "pcm29", "pcm30",
    "cs42", "cs43", "cs44", "cs47",
    "sgtl5", "tlv320",
    "nau88", "adau17",
)

_I2S_PINS = {"BCLK", "LRCK", "LRCLK", "WSEL", "WS", "SDIN", "SDOUT",
             "SDAT", "DIN", "DOUT", "DACDAT", "ADCDAT", "MCLK"}
_AUDIO_OUTPUT_PINS = {"OUT+", "OUT-", "OUTP", "OUTN", "SPKR", "SPK+", "SPK-",
                      "HP", "HPL", "HPR", "HPOUT", "LOUT", "ROUT", "LOUT1",
                      "ROUT1", "LOUT2", "ROUT2", "LINEOUT", "SPKOUTP", "SPKOUTN"}
_AUDIO_INPUT_PINS = {"IN+", "IN-", "INP", "INN", "LINEIN", "LIN", "RIN",
                     "MIC", "MICIN", "MICP", "MICN", "LMICIN", "RMICIN",
                     "LINPUT1", "RINPUT1", "LINPUT2", "RINPUT2"}

# Class-D amp keywords for amplifier class inference
_CLASS_D_KEYWORDS = ("tpa31", "tpa32", "max983", "tas57", "tas58", "sta3", "ssm23")


def detect_audio_circuits(ctx: AnalysisContext) -> list[dict]:
    """Detect audio amplifier and codec ICs."""
    results: list[dict] = []
    matched_refs: set[str] = set()

    for comp in ctx.components:
        if comp["type"] != "ic":
            continue
        ref = comp["reference"]
        if ref in matched_refs:
            continue
        val = comp.get("value", "").lower()
        lib = comp.get("lib_id", "").lower()
        combined = val + " " + lib

        is_amp = any(kw in combined for kw in _AUDIO_AMP_KEYWORDS)
        is_codec = any(kw in combined for kw in _AUDIO_CODEC_KEYWORDS)
        if not is_amp and not is_codec:
            continue
        matched_refs.add(ref)

        pin_nets = _build_pin_net_map(ctx, ref)
        all_pins = set(pin_nets.keys())

        # Infer interface
        interface = None
        if all_pins & _I2S_PINS:
            interface = "i2s"
        elif all_pins & {"SDA", "SCL"}:
            interface = "i2c"
        else:
            interface = "analog"

        # Find output nets
        output_nets: list[str] = []
        for pname in sorted(all_pins & _AUDIO_OUTPUT_PINS):
            net = pin_nets[pname]
            if not ctx.is_ground(net) and not ctx.is_power_net(net):
                output_nets.append(net)

        # Trace output load
        output_load = None
        for net in output_nets:
            if net not in ctx.nets:
                continue
            for p in ctx.nets[net]["pins"]:
                if p["component"] == ref:
                    continue
                lc = ctx.comp_lookup.get(p["component"])
                if not lc:
                    continue
                if lc["type"] in ("speaker", "buzzer"):
                    output_load = "speaker"
                    break
                if lc["type"] == "connector":
                    cv = (lc.get("value", "") + " " + lc.get("lib_id", "")).lower()
                    if any(k in cv for k in ("audio", "headphone", "hp", "jack", "phone")):
                        output_load = "headphone"
                    else:
                        output_load = "connector"
                    break
            if output_load:
                break

        if is_amp:
            # Classify amplifier class
            amp_class = "class_ab"
            if any(kw in combined for kw in _CLASS_D_KEYWORDS):
                amp_class = "class_d"

            # Check for LC output filter (class-D amps)
            has_output_filter = False
            if amp_class == "class_d":
                for net in output_nets:
                    if net not in ctx.nets:
                        continue
                    has_inductor = False
                    has_cap = False
                    for p in ctx.nets[net]["pins"]:
                        lc = ctx.comp_lookup.get(p["component"])
                        if lc and lc["type"] == "inductor":
                            has_inductor = True
                        elif lc and lc["type"] == "capacitor":
                            has_cap = True
                    if has_inductor and has_cap:
                        has_output_filter = True
                        break

            entry: dict = {
                "ref": ref,
                "value": comp.get("value", ""),
                "type": "audio_amplifier",
                "amplifier_class": amp_class,
                "interface": interface,
                "output_nets": output_nets,
                "detector": "detect_audio_circuits",
                "rule_id": "AU-DET",
                "category": "audio",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Audio amplifier {ref} ({comp.get('value', '')}) [{amp_class}/{interface}]",
                "description": f"Detected {amp_class} audio amplifier IC {ref}.",
                "components": [ref],
                "nets": output_nets,
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Audio", "impact": "", "standard_ref": ""},
            }
            if output_load:
                entry["output_load"] = output_load
            if amp_class == "class_d":
                entry["has_output_filter"] = has_output_filter
            entry["provenance"] = make_provenance("audio_codec_topology", "deterministic", claimed_components=[ref])
            results.append(entry)

        elif is_codec:
            has_adc = bool(all_pins & _AUDIO_INPUT_PINS)
            has_dac = bool(all_pins & _AUDIO_OUTPUT_PINS)

            entry = {
                "ref": ref,
                "value": comp.get("value", ""),
                "type": "audio_codec",
                "interface": interface,
                "has_adc": has_adc,
                "has_dac": has_dac,
                "output_nets": output_nets,
                "detector": "detect_audio_circuits",
                "rule_id": "AU-DET",
                "category": "audio",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Audio codec {ref} ({comp.get('value', '')}) [{interface}]",
                "description": f"Detected audio codec IC {ref}.",
                "components": [ref],
                "nets": output_nets,
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Audio", "impact": "", "standard_ref": ""},
            }
            if output_load:
                entry["output_load"] = output_load
            entry["provenance"] = make_provenance("audio_codec_topology", "deterministic", claimed_components=[ref])
            results.append(entry)

    return results


# ---------------------------------------------------------------------------
# LED Driver IC Detection
# ---------------------------------------------------------------------------

_LED_DRIVER_IC_KEYWORDS = (
    "pca9685", "pca968",
    "tlc594", "tlc595",
    "is31fl", "is31",
    "lp556", "lp503",
    "al880", "al881",
    "cat410", "cat420",
    "bcr42",
    "ap303", "mp330",
    "tps611",
)

_LED_PWM_KEYWORDS = ("pca9685", "pca968", "tlc594", "tlc595")
_LED_MATRIX_KEYWORDS = ("is31fl", "is31")
_LED_CC_KEYWORDS = ("al880", "al881", "cat410", "cat420", "bcr42", "ap303", "mp330", "tps611")
_LED_RGB_KEYWORDS = ("lp556", "lp503")

_LED_CURRENT_SET_PINS = {"IREF", "REXT", "ISET", "RSET", "RIREF"}
_LED_OUTPUT_PREFIXES = ("OUT", "LED", "CH", "PWM", "DRV")


def detect_led_driver_ics(ctx: AnalysisContext) -> list[dict]:
    """Detect dedicated LED driver ICs (PWM, matrix, constant-current)."""
    results: list[dict] = []
    matched_refs: set[str] = set()

    for comp in ctx.components:
        if comp["type"] != "ic":
            continue
        ref = comp["reference"]
        if ref in matched_refs:
            continue
        val = comp.get("value", "").lower()
        lib = comp.get("lib_id", "").lower()
        combined = val + " " + lib

        if not any(kw in combined for kw in _LED_DRIVER_IC_KEYWORDS):
            continue
        matched_refs.add(ref)

        pin_nets = _build_pin_net_map(ctx, ref)
        all_pins = set(pin_nets.keys())

        # Classify driver type
        if any(kw in combined for kw in _LED_PWM_KEYWORDS):
            driver_type = "pwm_led_driver"
        elif any(kw in combined for kw in _LED_MATRIX_KEYWORDS):
            driver_type = "matrix_led_driver"
        elif any(kw in combined for kw in _LED_CC_KEYWORDS):
            driver_type = "constant_current_led_driver"
        elif any(kw in combined for kw in _LED_RGB_KEYWORDS):
            driver_type = "rgb_led_driver"
        else:
            driver_type = "led_driver"

        # Infer interface
        interface = None
        if all_pins & {"SDA", "SCL"}:
            interface = "i2c"
        elif all_pins & {"SCK", "SCLK", "CLK", "MOSI", "SDI"}:
            interface = "spi"

        # Count output channels
        channels = 0
        for pname in all_pins:
            if any(pname.startswith(prefix) for prefix in _LED_OUTPUT_PREFIXES):
                if not ctx.is_power_net(pin_nets.get(pname, "")) and not ctx.is_ground(pin_nets.get(pname, "")):
                    channels += 1

        # Find current set resistor
        current_set = None
        for pname in _LED_CURRENT_SET_PINS:
            if pname in pin_nets:
                net = pin_nets[pname]
                if net in ctx.nets:
                    for p in ctx.nets[net]["pins"]:
                        if p["component"] == ref:
                            continue
                        rc = ctx.comp_lookup.get(p["component"])
                        if rc and rc["type"] == "resistor":
                            r_val = parse_value(rc.get("value", ""))
                            current_set = {"ref": rc["reference"], "net": net}
                            if r_val:
                                current_set["ohms"] = r_val
                            break
                break

        entry: dict = {
            "ref": ref,
            "value": comp.get("value", ""),
            "type": driver_type,
            "interface": interface,
            "detector": "detect_led_driver_ics",
            "rule_id": "LI-DET",
            "category": "led_control",
            "severity": "info",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "summary": f"LED driver {ref} ({comp.get('value', '')}) [{driver_type}]",
            "description": f"Detected {driver_type} LED driver IC {ref}.",
            "components": [ref],
            "nets": [],
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "LED Control", "impact": "", "standard_ref": ""},
        }
        if channels > 0:
            entry["channels"] = channels
        if current_set:
            entry["current_set"] = current_set

        entry["provenance"] = make_provenance("led_resistor_topology", "deterministic", claimed_components=[ref])
        results.append(entry)

    return results


# ---------------------------------------------------------------------------
# RTC Circuit Detection
# ---------------------------------------------------------------------------

_RTC_IC_KEYWORDS = (
    "ds1307", "ds3231", "ds3232", "ds1302",
    "pcf8523", "pcf8563", "pcf2129",
    "rv3028", "rv3032", "rv8803", "rv1805",
    "mcp7940", "mcp7941",
    "isl1208", "isl1218", "isl12",
    "ab1805", "ab0805", "abx8",
    "m41t", "rx8025", "rx8900",
    "bq3285", "bq4802",
)

_VBAT_PINS = {"VBAT", "VBACK", "VBACKUP", "BAT", "BATT"}
_RTC_INT_PINS = {"INT", "INTA", "INTB", "IRQ", "nINT", "~{INT}"}
_RTC_SQW_PINS = {"SQW", "CLKOUT", "CLK_OUT", "FOUT", "32K"}

# RTCs with internal TCXO (no external crystal needed)
_INTERNAL_OSC_KEYWORDS = ("ds3231", "ds3232", "rv8803", "rx8900")


def detect_rtc_circuits(ctx: AnalysisContext,
                        crystal_circuits: list[dict]) -> list[dict]:
    """Detect RTC ICs with battery backup and crystal pairing."""
    results: list[dict] = []
    matched_refs: set[str] = set()

    # Build crystal-to-IC map from crystal_circuits
    crystal_by_ic: dict[str, str] = {}  # ic_ref -> crystal_ref
    for xc in crystal_circuits:
        ic = xc.get("connected_to")
        xref = xc.get("reference")
        if ic and xref:
            crystal_by_ic[ic] = xref

    for comp in ctx.components:
        if comp["type"] != "ic":
            continue
        ref = comp["reference"]
        if ref in matched_refs:
            continue
        val = comp.get("value", "").lower()
        lib = comp.get("lib_id", "").lower()
        combined = val + " " + lib

        if not any(kw in combined for kw in _RTC_IC_KEYWORDS):
            continue
        matched_refs.add(ref)

        pin_nets = _build_pin_net_map(ctx, ref)
        all_pins = set(pin_nets.keys())

        # Interface
        interface = None
        if all_pins & {"SDA", "SCL"}:
            interface = "i2c"
        elif all_pins & {"SCK", "SCLK", "CLK", "MOSI", "SDI"}:
            interface = "spi"

        # Internal oscillator?
        has_internal_osc = any(kw in combined for kw in _INTERNAL_OSC_KEYWORDS)

        # External crystal — check crystal_circuits for a crystal connected to this IC
        external_crystal = crystal_by_ic.get(ref)
        # Also check by scanning crystal pins on this IC
        if not external_crystal:
            for pname in all_pins:
                if any(k in pname for k in ("XTAL", "OSC", "X1", "X2", "XI", "XO",
                                             "X32K", "XT1", "XT2")):
                    net = pin_nets[pname]
                    if net in ctx.nets:
                        for p in ctx.nets[net]["pins"]:
                            if p["component"] == ref:
                                continue
                            xc = ctx.comp_lookup.get(p["component"])
                            if xc and xc["type"] in ("crystal", "oscillator"):
                                external_crystal = p["component"]
                                break
                    if external_crystal:
                        break

        # Battery backup
        battery_backup = None
        for pname in _VBAT_PINS:
            if pname in pin_nets:
                vbat_net = pin_nets[pname]
                if vbat_net in ctx.nets:
                    for p in ctx.nets[vbat_net]["pins"]:
                        if p["component"] == ref:
                            continue
                        bc = ctx.comp_lookup.get(p["component"])
                        if bc and bc["type"] in ("battery", "capacitor"):
                            battery_backup = {
                                "pin": pname,
                                "net": vbat_net,
                                "battery_ref": p["component"],
                            }
                            break
                if not battery_backup:
                    battery_backup = {"pin": pname, "net": vbat_net, "battery_ref": None}
                break

        # Interrupt pin
        interrupt_net = None
        interrupt_connected = False
        for pname in _RTC_INT_PINS:
            if pname in pin_nets:
                interrupt_net = pin_nets[pname]
                if interrupt_net in ctx.nets:
                    for p in ctx.nets[interrupt_net]["pins"]:
                        if p["component"] == ref:
                            continue
                        ic = ctx.comp_lookup.get(p["component"])
                        if ic and ic["type"] == "ic":
                            interrupt_connected = True
                            break
                break

        # SQW/CLKOUT pin
        sqw_net = None
        for pname in _RTC_SQW_PINS:
            if pname in pin_nets:
                sqw_net = pin_nets[pname]
                break

        rtc_comps = [ref] + ([external_crystal] if external_crystal else [])
        entry: dict = {
            "ref": ref,
            "value": comp.get("value", ""),
            "type": "rtc",
            "interface": interface,
            "has_internal_oscillator": has_internal_osc,
            "external_crystal": external_crystal,
            "detector": "detect_rtc_circuits",
            "rule_id": "RT-DET",
            "category": "timing",
            "severity": "info",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "summary": f"RTC {ref} ({comp.get('value', '')}) [{interface}]",
            "description": f"Detected RTC IC {ref}.",
            "components": rtc_comps,
            "nets": [],
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "Timing", "impact": "", "standard_ref": ""},
        }
        if battery_backup:
            entry["battery_backup"] = battery_backup
        if interrupt_net:
            entry["interrupt_net"] = interrupt_net
            entry["interrupt_connected"] = interrupt_connected
        if sqw_net:
            entry["sqw_net"] = sqw_net

        entry["provenance"] = make_provenance("rtc_crystal_topology", "deterministic", claimed_components=[ref])
        results.append(entry)

    return results


# ---------------------------------------------------------------------------
# LED Lighting Audit
# ---------------------------------------------------------------------------

# Forward voltage estimates by LED color (for current calculation)
_LED_VF = {
    "red": 2.0, "orange": 2.0, "yellow": 2.0, "amber": 2.0,
    "green": 3.2, "blue": 3.2, "white": 3.2, "uv": 3.5,
}

# Per-color Vf floor — the MINIMUM forward voltage below which an LED of
# this color will not light at all. Used by LA-004 to flag LEDs on rails
# that are below their color's floor. rc.2 4.1 expansion (Manas review).
_LED_VF_FLOOR = {
    "red": 1.85, "orange": 2.0, "yellow": 2.0, "amber": 2.0,
    "green": 2.1, "blue": 3.0, "white": 3.0, "uv": 3.2,
}


def _estimate_led_vf(comp: dict) -> float:
    """Estimate LED forward voltage from value/lib_id color hints."""
    combined = (comp.get("value", "") + " " + comp.get("lib_id", "")).lower()
    for color, vf in _LED_VF.items():
        if color in combined:
            return vf
    return 2.0  # default to red/generic


def _detect_led_color(comp: dict) -> str | None:
    """Return the lowercase color string for an LED, or None if no color
    hint is present in value/lib_id."""
    combined = (comp.get("value", "") + " " + comp.get("lib_id", "")).lower()
    for color in _LED_VF.keys():
        if color in combined:
            return color
    return None


def audit_led_circuits(ctx: AnalysisContext,
                       transistor_circuits: list[dict]) -> list[dict]:
    """Audit all LEDs for proper current limiting.

    Catches direct GPIO→resistor→LED circuits and flags LEDs with missing
    current limiting. Excludes LEDs already handled by transistor-based
    detect_led_drivers() and addressable LED detection.
    """
    results: list[dict] = []

    # Build set of LED refs already claimed by transistor drivers
    driven_led_refs: set[str] = set()
    for tc in transistor_circuits:
        if tc.get("led_driver"):
            led_ref = tc["led_driver"].get("led_ref")
            if led_ref:
                driven_led_refs.add(led_ref)

    # Also exclude addressable LEDs (type will be "led" but value matches WS2812 etc.)
    addr_keywords = ("ws2812", "ws2813", "ws2815", "sk6812", "sk6805", "sk6803",
                     "apa102", "apa104", "sk9822", "ws2811", "neopixel", "dotstar")

    _seen_refs = set()
    for comp in ctx.components:
        if comp["type"] != "led":
            continue
        ref = comp["reference"]
        if ref in _seen_refs:
            continue
        _seen_refs.add(ref)
        if ref in driven_led_refs:
            continue

        # Skip addressable LEDs
        val_lower = comp.get("value", "").lower()
        lib_lower = comp.get("lib_id", "").lower()
        if any(k in val_lower or k in lib_lower for k in addr_keywords):
            continue

        # Skip multi-pin LEDs (RGB, RAGB) — they need per-channel analysis
        comp_pins = comp.get("pins", [])
        if len(comp_pins) > 2:
            continue

        # Get both pins
        n1, n2 = ctx.get_two_pin_nets(ref)
        if not n1 or not n2:
            continue

        # Classify each net: power, ground, signal
        supply_net = None
        signal_net = None
        for net in (n1, n2):
            if ctx.is_ground(net):
                continue
            if ctx.is_power_net(net):
                supply_net = net
            else:
                signal_net = net

        # If both are signal nets, pick the one that's not ground-adjacent
        if not supply_net and not signal_net:
            continue

        # Look for series resistor on the non-ground net(s)
        series_resistor = None
        has_unparsed_resistor = False
        driver_source = None
        check_nets = [n for n in (n1, n2) if n and not ctx.is_ground(n)]

        def _scan_net_for_resistor(net, exclude_ref):
            """Scan a net for a current-limiting resistor. Returns (resistor_dict, unparsed_flag)."""
            nonlocal supply_net, driver_source
            if net not in ctx.nets:
                return None, False
            found_unparsed = False
            for p in ctx.nets[net]["pins"]:
                if p["component"] == exclude_ref:
                    continue
                rc = ctx.comp_lookup.get(p["component"])
                if not rc:
                    continue
                if rc["type"] == "resistor":
                    r_val = parse_value(rc.get("value", ""))
                    if r_val is None:
                        found_unparsed = True
                        continue
                    if r_val < 10 or r_val > 100000:
                        continue
                    res = {"ref": rc["reference"], "ohms": r_val}
                    # Check what's on the resistor's other side
                    rn1, rn2 = ctx.get_two_pin_nets(rc["reference"])
                    r_other = rn2 if rn1 == net else rn1
                    if r_other and not supply_net and ctx.is_power_net(r_other):
                        supply_net = r_other
                    if r_other and r_other in ctx.nets:
                        for rp in ctx.nets[r_other]["pins"]:
                            if rp["component"] == rc["reference"]:
                                continue
                            src = ctx.comp_lookup.get(rp["component"])
                            if src and src["type"] == "ic":
                                driver_source = rp["component"]
                                break
                    return res, False
                elif rc["type"] == "ic" and not driver_source:
                    driver_source = rc["reference"]
            return None, found_unparsed

        for net in check_nets:
            series_resistor, unparsed = _scan_net_for_resistor(net, ref)
            if unparsed:
                has_unparsed_resistor = True
            if series_resistor:
                break

        # If no resistor found, trace through LED chains (LED→LED→...→resistor)
        if not series_resistor:
            visited_leds: set[str] = {ref}
            frontier_nets = list(check_nets)
            for _ in range(5):  # max 5 hops through LED chain
                next_nets: list[str] = []
                for net in frontier_nets:
                    if net not in ctx.nets:
                        continue
                    for p in ctx.nets[net]["pins"]:
                        if p["component"] in visited_leds:
                            continue
                        pc = ctx.comp_lookup.get(p["component"])
                        if not pc:
                            continue
                        if pc["type"] == "led":
                            # Follow through this LED to its other net
                            visited_leds.add(p["component"])
                            ln1, ln2 = ctx.get_two_pin_nets(p["component"])
                            for ln in (ln1, ln2):
                                if ln and ln != net and not ctx.is_ground(ln):
                                    next_nets.append(ln)
                if not next_nets:
                    break
                # Check the next set of nets for a resistor
                for net in next_nets:
                    series_resistor, unparsed = _scan_net_for_resistor(net, "")
                    if unparsed:
                        has_unparsed_resistor = True
                    if series_resistor:
                        break
                if series_resistor:
                    break
                frontier_nets = next_nets

        # Determine drive method
        if series_resistor:
            drive_method = "resistor_limited"
        elif driver_source:
            drive_method = "ic_direct"
        elif has_unparsed_resistor:
            drive_method = "resistor_unparsed"
        else:
            drive_method = "direct_drive"

        la_comps = [ref] + ([series_resistor["ref"]] if series_resistor else []) + ([driver_source] if driver_source else [])
        entry: dict = {
            "ref": ref,
            "value": comp.get("value", ""),
            "type": "indicator_led",
            "drive_method": drive_method,
            "detector": "audit_led_circuits",
            "rule_id": "LA-AUD",
            "category": "led_control",
            "severity": "info",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "summary": f"LED {ref} ({comp.get('value', '')}) [{drive_method}]",
            "description": f"LED audit: {ref} using {drive_method} drive method.",
            "components": la_comps,
            "nets": [supply_net] if supply_net else [],
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "LED Audit", "impact": "", "standard_ref": ""},
        }

        if series_resistor:
            entry["series_resistor"] = series_resistor
        if supply_net:
            entry["supply_net"] = supply_net
        if driver_source:
            entry["driver_source"] = driver_source

        # Estimate current for resistor-limited LEDs
        if series_resistor and supply_net:
            v_supply = parse_voltage_from_net_name(supply_net)
            if v_supply:
                vf = _estimate_led_vf(comp)
                if v_supply > vf:
                    i_ma = (v_supply - vf) / series_resistor["ohms"] * 1000
                    entry["estimated_current_mA"] = round(i_ma, 1)

        # Flag issues
        if drive_method == "direct_drive":
            entry["issue"] = "no_current_limiting_resistor"
        elif drive_method == "resistor_unparsed":
            entry["issue"] = "has_resistor_unparsed_value"

        entry["provenance"] = make_provenance("led_audit", "deterministic", claimed_components=[ref])
        results.append(entry)

        # LA-004 — rail-Vf floor check: if v_supply is below the LED's
        # color floor, the LED can't forward-bias at all. rc.2 4.1
        # expansion (Manas review).
        if supply_net:
            v_supply = parse_voltage_from_net_name(supply_net)
            color = _detect_led_color(comp)
            floor = _LED_VF_FLOOR.get(color) if color else None
            if v_supply is not None and floor is not None and v_supply < floor:
                results.append({
                    "ref": ref,
                    "type": "indicator_led",
                    "detector": "audit_led_circuits",
                    "rule_id": "LA-004",
                    "category": "led_control",
                    "severity": "warning",
                    "confidence": "heuristic",
                    "evidence_source": "topology",
                    "summary": (f"LED {ref} ({color}) on {supply_net}: "
                                f"rail {v_supply:.2f}V is below the "
                                f"{color}-LED Vf floor of {floor:.2f}V "
                                f"— LED will not light"),
                    "description": (f"LED {ref} is a {color} LED on rail "
                                    f"{supply_net} ({v_supply:.2f}V). "
                                    f"The minimum forward voltage for a "
                                    f"{color} LED is ~{floor:.2f}V; below "
                                    f"this the diode does not forward-bias "
                                    f"and no light is emitted."),
                    "components": [ref],
                    "nets": [supply_net],
                    "pins": [],
                    "supply_net": supply_net,
                    "supply_voltage": v_supply,
                    "color": color,
                    "color_vf_floor": floor,
                    "recommendation": (
                        f"Either move {ref} to a rail at or above "
                        f"{floor:.2f}V, or select a {color} LED variant "
                        f"with a lower-than-typical Vf (specialty parts "
                        f"exist down to ~1.8V for red)."
                    ),
                    "report_context": {
                        "section": "LED Audit",
                        "impact": "Indicator LED never lights",
                        "standard_ref": "",
                    },
                    "provenance": make_provenance("led_audit", "heuristic", claimed_components=[ref]),
                })

    return results


# ---------------------------------------------------------------------------
# Thermocouple / RTD Interface Detection
# ---------------------------------------------------------------------------

_TC_IC_KEYWORDS = (
    "max31855", "max31856", "max3185",
    "max6675", "max667",
    "ad8495", "ad8494", "ad8496", "ad8497",
    "ads1118",
    "mcp960",
)

_RTD_IC_KEYWORDS = (
    "max31865", "max3186",
    "ads124",
)

_TC_INPUT_PINS = {"T+", "T-", "TC+", "TC-", "INP", "INN",
                  "THERMOCOUPLE+", "THERMOCOUPLE-"}
_RTD_REF_PINS = {"RREF+", "RREF-", "REFIN+", "REFIN-", "RREF"}
_RTD_FORCE_PINS = {"FORCE+", "FORCE-", "RTDIN+", "RTDIN-", "F+", "F-"}

# ICs with internal cold junction compensation
_INTERNAL_CJC_KEYWORDS = ("max31855", "max31856", "max3185", "max6675", "max667", "mcp960")


def detect_thermocouple_rtd(ctx: AnalysisContext) -> list[dict]:
    """Detect thermocouple amplifier and RTD interface ICs."""
    results: list[dict] = []
    matched_refs: set[str] = set()

    for comp in ctx.components:
        if comp["type"] != "ic":
            continue
        ref = comp["reference"]
        if ref in matched_refs:
            continue
        val = comp.get("value", "").lower()
        lib = comp.get("lib_id", "").lower()
        combined = val + " " + lib

        is_tc = any(kw in combined for kw in _TC_IC_KEYWORDS)
        is_rtd = any(kw in combined for kw in _RTD_IC_KEYWORDS)
        if not is_tc and not is_rtd:
            continue
        matched_refs.add(ref)

        pin_nets = _build_pin_net_map(ctx, ref)
        all_pins = set(pin_nets.keys())

        # Infer interface
        interface = None
        if all_pins & {"SCK", "SCLK", "CLK", "MISO", "SDO", "CS", "CSN"}:
            interface = "spi"
        elif all_pins & {"SDA", "SCL"}:
            interface = "i2c"
        elif "ad849" in combined:
            interface = "analog"

        if is_tc and not is_rtd:
            # Thermocouple amplifier
            has_cjc = any(kw in combined for kw in _INTERNAL_CJC_KEYWORDS)

            # Find sensor input nets
            sensor_nets: list[str] = []
            for pname in sorted(all_pins & _TC_INPUT_PINS):
                sensor_nets.append(pin_nets[pname])

            results.append({
                "ref": ref,
                "value": comp.get("value", ""),
                "type": "thermocouple_amplifier",
                "interface": interface,
                "cold_junction_compensation": "internal" if has_cjc else "external",
                "sensor_input_nets": sensor_nets,
                "detector": "detect_thermocouple_rtd",
                "rule_id": "TC-DET",
                "category": "sensors",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Thermocouple amplifier {ref} ({comp.get('value', '')}) [{interface}]",
                "description": f"Detected thermocouple amplifier IC {ref}.",
                "components": [ref],
                "nets": sensor_nets,
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Sensors", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("thermo_ic_topology", "deterministic", claimed_components=[ref]),
            })

        elif is_rtd:
            # RTD interface
            # Find reference resistor
            ref_resistor = None
            for pname in _RTD_REF_PINS:
                if pname in pin_nets:
                    net = pin_nets[pname]
                    if net in ctx.nets:
                        for p in ctx.nets[net]["pins"]:
                            if p["component"] == ref:
                                continue
                            rc = ctx.comp_lookup.get(p["component"])
                            if rc and rc["type"] == "resistor":
                                r_val = parse_value(rc.get("value", ""))
                                ref_resistor = {"ref": rc["reference"]}
                                if r_val:
                                    ref_resistor["ohms"] = r_val
                                break
                    if ref_resistor:
                        break

            # Infer sensor type from reference resistor value
            sensor_type = None
            if ref_resistor and ref_resistor.get("ohms"):
                ohms = ref_resistor["ohms"]
                if 380 <= ohms <= 470:
                    sensor_type = "pt100"
                elif 3800 <= ohms <= 4700:
                    sensor_type = "pt1000"

            # Find sensor input nets
            sensor_nets = []
            for pname in sorted(all_pins & (_RTD_FORCE_PINS | _TC_INPUT_PINS)):
                sensor_nets.append(pin_nets[pname])

            rtd_comps = [ref] + ([ref_resistor["ref"]] if ref_resistor else [])
            entry: dict = {
                "ref": ref,
                "value": comp.get("value", ""),
                "type": "rtd_interface",
                "interface": interface,
                "detector": "detect_thermocouple_rtd",
                "rule_id": "TC-DET",
                "category": "sensors",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"RTD interface {ref} ({comp.get('value', '')})" + (f" [{sensor_type}]" if sensor_type else ""),
                "description": f"Detected RTD interface IC {ref}.",
                "components": rtd_comps,
                "nets": sensor_nets,
                "pins": [],
                "recommendation": "",
                "report_context": {"section": "Sensors", "impact": "", "standard_ref": ""},
            }
            if ref_resistor:
                entry["reference_resistor"] = ref_resistor
            if sensor_type:
                entry["sensor_type"] = sensor_type
            if sensor_nets:
                entry["sensor_input_nets"] = sensor_nets

            entry["provenance"] = make_provenance("thermo_ic_topology", "deterministic", claimed_components=[ref])
            results.append(entry)

    return results


# ---------------------------------------------------------------------------
# Power Sequencing Validation
# ---------------------------------------------------------------------------

_EN_PIN_NAMES = {"EN", "ENABLE", "ON", "ON/OFF", "CE", "SHDN", "SHUTDOWN",
                 "EN1", "EN2", "EN3",
                 "~{EN}", "~{SHDN}", "~{ENABLE}", "~{CE}"}
_PG_PIN_NAMES = {"PG", "PGOOD", "PG1", "PG2", "POWER_GOOD", "POK", "nPG",
                 "~{PG}", "~{PGOOD}", "~{POWER_GOOD}", "~{POK}"}


def validate_power_sequencing(ctx: AnalysisContext,
                               power_regulators: list[dict],
                               power_path: list[dict],
                               reset_supervisors: list[dict]) -> dict:
    """Cross-reference power regulators, load switches, and supervisors
    to build a power-up dependency graph and flag sequencing issues."""

    power_tree: list[dict] = []
    enable_chains: list[dict] = []
    issues: list[dict] = []

    # Collect all power sources (regulators + load switches)
    all_sources: list[dict] = []
    for reg in power_regulators:
        all_sources.append({
            "ref": reg["ref"],
            "kind": "regulator",
            "input_rail": reg.get("input_rail"),
            "output_rail": reg.get("output_rail"),
            "voltage": reg.get("estimated_vout"),
        })
    for pp in power_path:
        if pp.get("type") == "load_switch":
            all_sources.append({
                "ref": pp["ref"],
                "kind": "load_switch",
                "input_rail": pp.get("input_rail"),
                "output_rail": pp.get("output_rail"),
                "voltage": None,
                "enable_net": pp.get("enable_net"),
            })

    # For each source, find EN and PG pins by scanning IC pins
    source_en_nets: dict[str, str | None] = {}  # ref -> en_net
    source_pg_nets: dict[str, str | None] = {}  # ref -> pg_net

    def _match_pin(pin_nets: dict[str, str], names: set[str]) -> str | None:
        """Match a pin name from *pin_nets* against a set of canonical names.

        KiCad 6+ overbar markup (``~{EN}``) is stripped before comparison so
        that both ``EN`` and ``~{EN}`` match the canonical ``"EN"`` entry.
        Trailing digits are also stripped for base-name matching (e.g.
        ``EN1`` matches if ``"EN"`` is in *names*).
        """
        # First pass: direct lookup (fast path for exact matches)
        for pname in names:
            if pname in pin_nets:
                return pin_nets[pname]
        # Second pass: normalize raw pin names and match against base names
        # KH-223: strip ~{ } overbar wrappers and retry
        for raw_pname, net in pin_nets.items():
            norm = raw_pname.replace("~{", "").replace("}", "")
            if norm in names:
                return net
            # Also try with trailing digits stripped (EN1 → EN)
            base = norm.rstrip("0123456789")
            if base and base in names:
                return net
        return None

    for src in all_sources:
        ref = src["ref"]
        pin_nets = _build_pin_net_map(ctx, ref)

        # EN pin
        en_net = src.get("enable_net")  # load switches already have this
        if not en_net:
            en_net = _match_pin(pin_nets, _EN_PIN_NAMES)
        source_en_nets[ref] = en_net

        # PG pin
        pg_net = _match_pin(pin_nets, _PG_PIN_NAMES)
        source_pg_nets[ref] = pg_net

    # Build PG→EN cross-reference: which PG net drives which EN net
    pg_to_ref: dict[str, str] = {}  # pg_net -> source ref that outputs it
    for ref, pg_net in source_pg_nets.items():
        if pg_net:
            pg_to_ref[pg_net] = ref

    # Trace enable chains and build power tree
    output_rails: dict[str, dict] = {}  # rail_name -> source info
    for src in all_sources:
        ref = src["ref"]
        rail = src.get("output_rail")
        if rail:
            output_rails[rail] = src

        en_net = source_en_nets.get(ref)
        en_source = None
        en_type = "always_on"

        if en_net:
            if ctx.is_power_net(en_net):
                en_type = "tied_to_rail"
                en_source = en_net
            elif en_net in pg_to_ref:
                en_type = "pg_daisy_chain"
                en_source = pg_to_ref[en_net]
                enable_chains.append({
                    "regulator": ref,
                    "en_net": en_net,
                    "en_source": en_source,
                    "type": "pg_daisy_chain",
                })
            else:
                # Check if EN net has any driver (IC pin, connector)
                has_driver = False
                if en_net in ctx.nets:
                    for p in ctx.nets[en_net]["pins"]:
                        if p["component"] == ref:
                            continue
                        ec = ctx.comp_lookup.get(p["component"])
                        if ec and ec["type"] in ("ic", "connector"):
                            has_driver = True
                            en_source = p["component"]
                            en_type = "gpio_controlled"
                            break
                if not has_driver:
                    # Check if net has any pins at all beyond the EN pin itself
                    pin_count = len(ctx.nets.get(en_net, {}).get("pins", []))
                    if pin_count <= 1:
                        en_type = "floating"
                        issues.append({
                            "type": "floating_enable",
                            "ref": ref,
                            "rail": rail,
                            "en_net": en_net,
                        })

        # Build power tree entry
        tree_entry: dict = {
            "rail": rail,
            "source": ref,
            "source_type": src["kind"],
        }
        if src.get("voltage"):
            tree_entry["voltage"] = src["voltage"]
        tree_entry["enable_type"] = en_type
        if en_source:
            tree_entry["enabled_by"] = en_source
        power_tree.append(tree_entry)

    # Check supervisors for issues
    for sup in reset_supervisors:
        if sup.get("type") != "voltage_supervisor":
            continue
        rail = sup.get("monitored_rail")
        threshold = sup.get("threshold_voltage")
        if rail and threshold:
            # Find nominal voltage of monitored rail
            src = output_rails.get(rail)
            nominal = src.get("voltage") if src else parse_voltage_from_net_name(rail)
            if nominal and threshold > nominal:
                issues.append({
                    "type": "supervisor_threshold_above_nominal",
                    "ref": sup["ref"],
                    "monitored_rail": rail,
                    "threshold": threshold,
                    "nominal": nominal,
                })

    # Topological sort for sequence order
    # Build adjacency: source ref → list of refs it enables
    deps: dict[str, list[str]] = {}
    for chain in enable_chains:
        src = chain["en_source"]
        tgt = chain["regulator"]
        deps.setdefault(src, []).append(tgt)

    # Assign sequence order via BFS
    visited: set[str] = set()
    order: dict[str, int] = {}
    queue: list[tuple[str, int]] = []

    # Start with sources that have no enable dependency (always-on)
    for entry in power_tree:
        if entry["enable_type"] in ("always_on", "tied_to_rail"):
            ref = entry["source"]
            if ref not in visited:
                queue.append((ref, 0))
                visited.add(ref)

    while queue:
        ref, seq = queue.pop(0)
        order[ref] = seq
        for child in deps.get(ref, []):
            if child not in visited:
                queue.append((child, seq + 1))
                visited.add(child)

    # Apply sequence order to power tree
    for entry in power_tree:
        ref = entry["source"]
        if ref in order:
            entry["sequence_order"] = order[ref]

    # Sort power tree by sequence order
    power_tree.sort(key=lambda e: (e.get("sequence_order", 999), e.get("rail") or ""))

    result: dict = {
        "power_tree": power_tree,
        "provenance": make_provenance("pseq_enable_chain", "heuristic"),
    }
    if enable_chains:
        result["enable_chains"] = enable_chains
    if issues:
        result["issues"] = issues

    return result


# ---------------------------------------------------------------------------
# Connector Ground Pin Distribution Audit
# ---------------------------------------------------------------------------

def audit_connector_ground_distribution(ctx: AnalysisContext) -> list[dict]:
    """Check ground pin distribution on multi-pin connectors.

    Professional rule: ground pins every 2-3 signal pins for EMI control.
    Flags connectors with >4 signal pins per ground pin or no ground pins.
    """
    results: list[dict] = []
    for comp in ctx.components:
        if comp.get("type") != "connector":
            continue
        pin_nets = comp.get("pin_nets", {})
        # Also build from ref_pins if pin_nets not populated on the component
        if not pin_nets:
            rp = ctx.ref_pins.get(comp["reference"], {})
            pin_nets = {pn: net for pn, (net, _) in rp.items() if net}
        if len(pin_nets) < 5:
            continue

        ref = comp["reference"]
        gnd_count = 0
        signal_count = 0
        for pin_num, net in pin_nets.items():
            if isinstance(net, tuple):
                net = net[0]  # handle (net_name, pin_info) tuples
            if not net:
                continue
            if ctx.is_ground(net):
                gnd_count += 1
            elif not ctx.is_power_net(net):
                signal_count += 1

        if signal_count == 0:
            continue

        if gnd_count == 0:
            results.append({
                "ref": ref, "value": comp.get("value", ""),
                "total_pins": len(pin_nets), "ground_pins": 0,
                "signal_pins": signal_count,
                "status": "warning",
                "detail": f"{ref}: {len(pin_nets)}-pin connector has no ground pins",
                "detector": "audit_connector_ground_distribution",
                "rule_id": "CG-AUD",
                "category": "connectors",
                "severity": "warning",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Connector {ref} has no ground pins ({len(pin_nets)} pins)",
                "description": f"Connector {ref} has {signal_count} signal pins but no ground pins.",
                "components": [ref],
                "nets": [],
                "pins": [],
                "recommendation": "Add ground pin(s) for EMI control.",
                "report_context": {"section": "Connector Ground", "impact": "", "standard_ref": ""},
                "provenance": make_provenance("cg_ground_audit", "deterministic", claimed_components=[ref]),
            })
        else:
            ratio = signal_count / max(gnd_count, 1)
            if ratio > 4:
                results.append({
                    "ref": ref, "value": comp.get("value", ""),
                    "total_pins": len(pin_nets), "ground_pins": gnd_count,
                    "signal_pins": signal_count, "signal_per_ground": round(ratio, 1),
                    "status": "advisory",
                    "detail": (f"{ref}: {ratio:.0f} signal pins per ground pin "
                               f"(recommended: \u22643 for EMI control)"),
                    "detector": "audit_connector_ground_distribution",
                    "rule_id": "CG-AUD",
                    "category": "connectors",
                    "severity": "info",
                    "confidence": "deterministic",
                    "evidence_source": "topology",
                    "summary": f"Connector {ref}: {ratio:.0f}:1 signal-to-ground ratio",
                    "description": f"Connector {ref} has {ratio:.1f} signal pins per ground pin.",
                    "components": [ref],
                    "nets": [],
                    "pins": [],
                    "recommendation": "Add more ground pins (target \u22643 signal pins per ground).",
                    "report_context": {"section": "Connector Ground", "impact": "", "standard_ref": ""},
                    "provenance": make_provenance("cg_ground_audit", "deterministic", claimed_components=[ref]),
                })
    return results


# ---------------------------------------------------------------------------
# Certification Suggestion
# ---------------------------------------------------------------------------

def suggest_certifications(ctx: AnalysisContext, signal_analysis: dict) -> list[dict]:
    """Suggest applicable certifications based on design characteristics.

    Cross-references existing domain detections to identify likely
    required standards/certifications.
    """
    suggestions: list[dict] = []

    # Wireless modules / RF → FCC/CE/IC
    rf_chains = signal_analysis.get("rf_chains", [])
    if rf_chains:
        suggestions.append({
            "standard": "FCC Part 15",
            "region": "US",
            "reason": f"RF transceiver detected ({len(rf_chains)} chain(s))",
            "components": [c.get("reference", c.get("ref", "")) for c in rf_chains[:3]],
        })
        suggestions.append({
            "standard": "CE RED (Radio Equipment Directive)",
            "region": "EU",
            "reason": "RF transceiver detected",
        })

    # WiFi/BT modules
    for comp in ctx.components:
        val_lib = (comp.get("value", "") + " " + comp.get("lib_id", "")).lower()
        if any(k in val_lib for k in ("esp32", "esp8266", "nrf52", "cc254",
                                       "wl18", "cyw43", "ap621", "bcm43")):
            if not any(s["standard"] == "FCC Part 15" for s in suggestions):
                suggestions.append({
                    "standard": "FCC Part 15",
                    "region": "US",
                    "reason": f"Wireless module detected: {comp['reference']}",
                })
            break

    # Battery/charger → safety standards
    battery_chargers = signal_analysis.get("battery_chargers", [])
    bms_systems = signal_analysis.get("bms_systems", [])
    if battery_chargers or bms_systems:
        suggestions.append({
            "standard": "IEC 62133 / UL 2054",
            "region": "International",
            "reason": "Battery charging/management circuitry detected",
        })
        suggestions.append({
            "standard": "UN 38.3",
            "region": "International (shipping)",
            "reason": "Lithium battery transport safety testing",
        })

    # USB → USB-IF compliance
    usb_compliance = signal_analysis.get("usb_compliance", [])
    if usb_compliance:
        suggestions.append({
            "standard": "USB-IF Compliance",
            "region": "International",
            "reason": "USB interface detected",
        })

    # Ethernet → EMC
    ethernet = signal_analysis.get("ethernet_interfaces", [])
    if ethernet:
        suggestions.append({
            "standard": "IEEE 802.3 / CISPR 32",
            "region": "International",
            "reason": "Ethernet interface detected — EMC compliance required",
        })

    # High voltage detection (>60V)
    rail_voltages = signal_analysis.get("rail_voltages", {})
    max_voltage = max((v for v in rail_voltages.values()
                       if isinstance(v, (int, float))), default=0)
    if max_voltage > 60:
        suggestions.append({
            "standard": "IEC 62368-1 (Safety)",
            "region": "International",
            "reason": f"High voltage detected: {max_voltage:.0f}V (>60V safety threshold)",
        })

    # General EMC (all products)
    if not any(s["standard"].startswith("FCC") for s in suggestions):
        suggestions.append({
            "standard": "FCC Part 15 Subpart B (Unintentional Radiator)",
            "region": "US",
            "reason": "All electronic devices require unintentional radiator compliance",
        })
    if not any("CISPR" in s["standard"] or "CE" in s["standard"]
               for s in suggestions):
        suggestions.append({
            "standard": "CISPR 32 / CE EMC Directive",
            "region": "EU",
            "reason": "All electronic devices require EMC compliance for EU market",
        })

    # Annotate each suggestion with finding metadata so the trust_summary
    # doesn't flag them as unknown confidence/evidence.
    for s in suggestions:
        s.setdefault('detector', 'suggest_certifications')
        s.setdefault('rule_id', 'CERT-001')
        s.setdefault('category', 'certification')
        s.setdefault('severity', 'info')
        s.setdefault('confidence', 'heuristic')
        s.setdefault('evidence_source', 'topology')
        s.setdefault('summary', s.get('reason', ''))
        s.setdefault('description', f"{s.get('standard', '')}: {s.get('reason', '')}")
        s.setdefault('components', s.get('components', []))
        s.setdefault('nets', [])
        s.setdefault('pins', [])
        s.setdefault('recommendation', '')
        s.setdefault('report_context', {
            'section': 'Certifications', 'impact': '', 'standard_ref': ''})

    return suggestions


def _get_pin_net_domain(ctx: AnalysisContext, ref: str, pin_names: tuple) -> str | None:
    """Find net connected to a pin matching names (domain_detectors version)."""
    pins = ctx.ref_pins.get(ref, {})
    for pnum, (net, _) in pins.items():
        comp = ctx.comp_lookup.get(ref)
        if not comp:
            continue
        for p in comp.get('pins', []):
            if p.get('number') == pnum and p.get('name', '').upper() in pin_names:
                return net
    for pnum, (net, _) in pins.items():
        if not net or net not in ctx.nets:
            continue
        for np in ctx.nets[net]['pins']:
            if np['component'] == ref and np.get('pin_name', '').upper() in pin_names:
                return net
    return None


# ---------------------------------------------------------------------------
# WL-001: Wireless module validation
# ---------------------------------------------------------------------------

_WIFI_BLE_KEYWORDS = (
    'esp32', 'esp8266', 'esp32s', 'esp32c', 'esp32h',
    'nrf52', 'nrf53', 'nrf91', 'nrf7002',
    'cc2640', 'cc2652', 'cc1352', 'cc3220',
    'cyw43', 'cyw20',
    'da1469', 'da1458',
    'stm32wb', 'stm32wl', 'stm32wba',
    'rp2040w', 'pico_w',
    'atecc', 'atwinc', 'atwilc',
    'bg22', 'bg24', 'mg24',
)

_LORA_KEYWORDS = (
    'sx1276', 'sx1278', 'sx1262', 'sx1261', 'sx1280',
    'rfm95', 'rfm96', 'rfm98', 'rfm69',
    'ra01', 'ra02',
    'llcc68',
    'lr1110', 'lr1120', 'lr1121',
    'stm32wl',
)

_CELLULAR_KEYWORDS = (
    'sim7000', 'sim7600', 'sim7080', 'sim800', 'sim900',
    'bg96', 'bg77', 'bc66', 'bc95',
    'sara', 'lara', 'toby',
    'mc60', 'mc20',
    'a7670', 'a7608',
)

_GPS_KEYWORDS = (
    'neo6m', 'neo7m', 'neo8m', 'neom8', 'neom9', 'zed',
    'l76', 'l86', 'l96',
    'sam_m8q', 'sam_m10',
    'gps', 'gnss',
    'pa1010', 'pa1616',
)

_ANTENNA_PIN_NAMES = ('ANT', 'ANTENNA', 'RF', 'RF_OUT', 'RF_IN', 'RFIO', 'ANT_SW')
_SIM_PIN_NAMES = ('SIM_VCC', 'SIM_RST', 'SIM_IO', 'SIM_CLK', 'SIM_DET')


def detect_wireless_modules(ctx: AnalysisContext) -> list[dict]:
    """WL-001: Detect WiFi/BLE, LoRa, cellular, and GPS modules."""
    results: list[dict] = []
    for ic in get_unique_ics(ctx):
        ref = ic['reference']
        val = ic.get('value', '')
        wl_type = None
        if match_ic_keywords(ic, _WIFI_BLE_KEYWORDS):
            wl_type = 'wifi_ble'
        elif match_ic_keywords(ic, _LORA_KEYWORDS):
            wl_type = 'lora'
        elif match_ic_keywords(ic, _CELLULAR_KEYWORDS):
            wl_type = 'cellular'
        elif match_ic_keywords(ic, _GPS_KEYWORDS):
            wl_type = 'gps'
        if not wl_type:
            continue

        ant_net = _get_pin_net_domain(ctx, ref, _ANTENNA_PIN_NAMES)
        entry = {
            'detector': 'detect_wireless_modules', 'rule_id': 'WL-001',
            'category': 'wireless', 'reference': ref, 'value': val,
            'wireless_type': wl_type, 'antenna_net': ant_net,
            'severity': 'info', 'confidence': 'deterministic',
            'evidence_source': 'topology',
            'summary': f'{wl_type.replace("_", "/")} module {ref} ({val})',
            'description': f'Detected {wl_type} wireless module {ref} ({val}).',
            'components': [ref], 'nets': [ant_net] if ant_net else [],
            'pins': [], 'recommendation': '',
            'report_context': {'section': 'Wireless', 'impact': '', 'standard_ref': ''},
        }
        if wl_type == 'cellular':
            sim_nets = {}
            for sn in _SIM_PIN_NAMES:
                net = _get_pin_net_domain(ctx, ref, (sn,))
                if net:
                    sim_nets[sn] = net
            entry['sim_pins'] = sim_nets
            if not sim_nets:
                entry['severity'] = 'warning'
                entry['recommendation'] = 'Verify SIM card connections for cellular module.'
        entry['provenance'] = make_provenance('wireless_antenna_match', 'heuristic', claimed_components=[ref])
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# TF-001: Transformer-coupled SMPS feedback
# ---------------------------------------------------------------------------

_FLYBACK_CONTROLLER_KEYWORDS = (
    'uc3842', 'uc3843', 'uc3844', 'uc3845', 'uc284', 'uc384',
    'lt3748', 'lt3573', 'lt3798',
    'top2', 'top3', 'tnr', 'tny2', 'tny3',
    'viper', 'viper22', 'viper53',
    'lnk3', 'lnk6',
    'ob2263', 'ob2269',
    'mp15', 'mp17',
    'ap393', 'fsd2',
)

_OPTOCOUPLER_KEYWORDS = (
    'pc817', 'el817', 'tlp', 'sfh6', 'hcpl', 'acpl', 'cny17',
    'ps2501', 'ps2561', '4n25', '4n35', 'moc3',
    'fod8', 'fod3', 'vo618', 'vo3120',
)

_TL431_KEYWORDS = ('tl431', 'tlv431', 'lm431', 'ka431', 'az431', 'lmv431')


def detect_transformer_feedback(ctx: AnalysisContext) -> list[dict]:
    """TF-001: Detect isolated SMPS feedback loops (optocoupler + TL431)."""
    results: list[dict] = []
    controllers = [ic for ic in get_unique_ics(ctx) if match_ic_keywords(ic, _FLYBACK_CONTROLLER_KEYWORDS)]
    optocouplers = [c for c in ctx.components
                    if match_ic_keywords(c, _OPTOCOUPLER_KEYWORDS)
                    or 'optocoupler' in (c.get('lib_id', '') + c.get('value', '')).lower()]
    tl431s = [c for c in ctx.components
              if match_ic_keywords(c, _TL431_KEYWORDS) or 'tl431' in c.get('value', '').lower()]

    if not controllers:
        return results

    for ctrl in controllers:
        ref = ctrl['reference']
        entry = {
            'detector': 'detect_transformer_feedback', 'rule_id': 'TF-001',
            'category': 'isolated_power', 'reference': ref, 'value': ctrl.get('value', ''),
            'controller_type': 'flyback', 'optocoupler': None, 'shunt_reference': None,
            'severity': 'info', 'confidence': 'heuristic', 'evidence_source': 'topology',
            'summary': f'Isolated SMPS controller {ref} ({ctrl.get("value", "")})',
            'description': f'Detected flyback/isolated SMPS controller {ref}.',
            'components': [ref], 'nets': [], 'pins': [], 'recommendation': '',
            'report_context': {'section': 'Isolated Power', 'impact': '', 'standard_ref': ''},
        }
        fb_net = _get_pin_net_domain(ctx, ref, ('FB', 'COMP', 'VFB', 'OPTO'))
        if fb_net:
            for opto in optocouplers:
                opto_ref = opto['reference']
                for pnum, (net, _) in ctx.ref_pins.get(opto_ref, {}).items():
                    if net == fb_net:
                        entry['optocoupler'] = {'ref': opto_ref, 'value': opto.get('value', '')}
                        entry['components'].append(opto_ref)
                        break
        if entry['optocoupler']:
            opto_ref = entry['optocoupler']['ref']
            for pnum, (net, _) in ctx.ref_pins.get(opto_ref, {}).items():
                if not net:
                    continue
                for tl in tl431s:
                    tl_ref = tl['reference']
                    for tp, (tnet, _) in ctx.ref_pins.get(tl_ref, {}).items():
                        if tnet == net:
                            entry['shunt_reference'] = {'ref': tl_ref, 'value': tl.get('value', '')}
                            entry['components'].append(tl_ref)
                            break
            entry['confidence'] = 'deterministic'
            entry['description'] = (
                f'Isolated SMPS {ref} with optocoupler feedback via {entry["optocoupler"]["ref"]}'
                f'{" and " + entry["shunt_reference"]["ref"] + " shunt reference" if entry["shunt_reference"] else ""}.'
            )
        entry['provenance'] = make_provenance('smps_transformer_topology', 'deterministic', claimed_components=[ref])
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# IA-001: I2C address conflict detection
# ---------------------------------------------------------------------------

_I2C_DEVICE_ADDRESSES = {
    'ina219': {'base': 0x40, 'pins': ('A0', 'A1')},
    'ina226': {'base': 0x40, 'pins': ('A0', 'A1')},
    'ina228': {'base': 0x40, 'pins': ('A0', 'A1')},
    'pca9685': {'base': 0x40, 'pins': ('A0', 'A1', 'A2', 'A3', 'A4', 'A5')},
    'ads1115': {'base': 0x48, 'pins': ('ADDR',)},
    'ads1015': {'base': 0x48, 'pins': ('ADDR',)},
    'bme280': {'base': 0x76, 'pins': ('SDO',)},
    'bmp280': {'base': 0x76, 'pins': ('SDO',)},
    'sht3': {'base': 0x44, 'pins': ('ADDR',)},
    'mcp4725': {'base': 0x60, 'pins': ('A0', 'A1', 'A2')},
    'at24c': {'base': 0x50, 'pins': ('A0', 'A1', 'A2')},
    'pcf8574': {'base': 0x20, 'pins': ('A0', 'A1', 'A2')},
    'pcf8575': {'base': 0x20, 'pins': ('A0', 'A1', 'A2')},
    'mcp23017': {'base': 0x20, 'pins': ('A0', 'A1', 'A2')},
    'ds1307': {'base': 0x68, 'pins': ()},
    'ds3231': {'base': 0x68, 'pins': ()},
}


def _resolve_addr_pin(ctx: AnalysisContext, ref: str, pin_name: str) -> str:
    net = _get_pin_net_domain(ctx, ref, (pin_name,))
    if not net:
        return 'unknown'
    if ctx.is_ground(net):
        return 'gnd'
    if ctx.is_power_net(net):
        return 'vcc'
    net_lower = net.lower()
    if 'sda' in net_lower:
        return 'sda'
    if 'scl' in net_lower:
        return 'scl'
    return 'unknown'


def detect_i2c_address_conflicts(ctx: AnalysisContext) -> list[dict]:
    """IA-001: Detect I2C devices with potentially conflicting addresses."""
    results: list[dict] = []
    buses: dict = {}

    for ic in get_unique_ics(ctx):
        ref = ic['reference']
        combined = (ic.get('value', '') + ' ' + ic.get('lib_id', '')).lower()
        device_type = None
        for keyword in _I2C_DEVICE_ADDRESSES:
            if keyword in combined:
                device_type = keyword
                break
        if not device_type:
            continue
        sda_net = _get_pin_net_domain(ctx, ref, ('SDA', 'I2C_SDA'))
        scl_net = _get_pin_net_domain(ctx, ref, ('SCL', 'I2C_SCL'))
        if not sda_net or not scl_net:
            continue
        dev_info = _I2C_DEVICE_ADDRESSES[device_type]
        addr_config = {pin: _resolve_addr_pin(ctx, ref, pin) for pin in dev_info['pins']}
        buses.setdefault((sda_net, scl_net), []).append({
            'ref': ref, 'value': ic.get('value', ''), 'device_type': device_type,
            'addr_config': addr_config, 'base_addr': dev_info['base'],
        })

    for (sda_net, scl_net), devices in buses.items():
        addr_groups: dict = {}
        for dev in devices:
            config_str = f"{dev['device_type']}:{','.join(f'{k}={v}' for k, v in sorted(dev['addr_config'].items()))}"
            addr_groups.setdefault(config_str, []).append(dev)
        for config_str, group in addr_groups.items():
            if len(group) < 2:
                continue
            refs = [d['ref'] for d in group]
            dev_type = group[0]['device_type']
            base = group[0]['base_addr']
            results.append(make_finding(
                detector='detect_i2c_address_conflicts', rule_id='IA-001', category='protocol_integrity',
                summary=f'I2C address conflict: {len(refs)}x {dev_type} at same address on {sda_net}/{scl_net}',
                description=f'{len(refs)} instances of {dev_type} ({", ".join(refs)}) have identical address configs ({config_str.split(":", 1)[1]}).',
                severity='error', confidence='deterministic', evidence_source='topology',
                components=refs, nets=[sda_net, scl_net],
                recommendation='Reconfigure address pins (A0/A1/A2) to assign unique addresses.',
                fix_params={'type': 'swap_connection', 'components': refs[1:], 'change': 'Rewire address pins', 'basis': f'{dev_type} base 0x{base:02X}'},
                impact='Bus corruption — multiple devices respond to same address',
                provenance=make_provenance('i2c_addr_conflict', 'deterministic', claimed_components=refs),
            
                source=ctx.source,))
    return results


# ---------------------------------------------------------------------------
# SC-001: Supercapacitor / energy harvesting
# ---------------------------------------------------------------------------

_HARVESTER_KEYWORDS = (
    'bq25570', 'bq25504', 'bq25505',
    'ltc3108', 'ltc3109', 'ltc3588',
    'spv1040', 'spv1050',
    'adp5090', 'adp5091', 'adp5092',
    'max20361',
    'ab1815',
    'mb39c', 'mb39d',
    'e_peas', 'aem1094', 'aem3094',
)

_SUPERCAP_KEYWORDS = ('supercap', 'edlc', 'ultracap', 'gold_cap', 'super_cap')


def detect_energy_harvesting(ctx: AnalysisContext) -> list[dict]:
    """SC-001: Detect energy harvesting ICs and supercapacitor circuits."""
    results: list[dict] = []
    for ic in get_unique_ics(ctx):
        if not match_ic_keywords(ic, _HARVESTER_KEYWORDS):
            continue
        ref = ic['reference']
        results.append({
            'detector': 'detect_energy_harvesting', 'rule_id': 'SC-001',
            'category': 'energy_harvesting', 'reference': ref, 'value': ic.get('value', ''),
            'harvester_type': 'energy_harvesting_ic',
            'severity': 'info', 'confidence': 'deterministic', 'evidence_source': 'topology',
            'summary': f'Energy harvesting IC {ref} ({ic.get("value", "")})',
            'description': f'Detected energy harvesting PMIC {ref} ({ic.get("value", "")}).',
            'components': [ref], 'nets': [], 'pins': [], 'recommendation': '',
            'report_context': {'section': 'Energy Harvesting', 'impact': '', 'standard_ref': ''},
            'provenance': make_provenance('eharvest_topology', 'heuristic', claimed_components=[ref]),
        })
    for comp in ctx.components:
        if comp['type'] != 'capacitor':
            continue
        val = comp.get('value', '').lower()
        lib = comp.get('lib_id', '').lower()
        combined = val + ' ' + lib
        farads = ctx.parsed_values.get(comp['reference'])
        is_supercap = any(k in combined for k in _SUPERCAP_KEYWORDS)
        if not is_supercap and farads is not None and farads >= 0.1:
            is_supercap = True
        if is_supercap:
            results.append({
                'detector': 'detect_energy_harvesting', 'rule_id': 'SC-001',
                'category': 'energy_harvesting', 'reference': comp['reference'],
                'value': comp.get('value', ''), 'harvester_type': 'supercapacitor',
                'capacitance_F': farads,
                'severity': 'info', 'confidence': 'deterministic', 'evidence_source': 'topology',
                'summary': f'Supercapacitor {comp["reference"]} ({comp.get("value", "")})',
                'description': f'Detected supercapacitor {comp["reference"]}.',
                'components': [comp['reference']], 'nets': [], 'pins': [], 'recommendation': '',
                'report_context': {'section': 'Energy Harvesting', 'impact': '', 'standard_ref': ''},
                'provenance': make_provenance('eharvest_topology', 'heuristic', claimed_components=[comp['reference']]),
            })
    return results


# ---------------------------------------------------------------------------
# PL-001: PWM LED dimming topology
# ---------------------------------------------------------------------------

def detect_pwm_led_dimming(ctx: AnalysisContext, transistor_circuits: list[dict]) -> list[dict]:
    """PL-001: Detect transistor-driven LED circuits.

    Finds transistors whose load_type is 'led' or whose collector/drain net
    connects to LEDs. Covers both MOSFET and BJT LED drivers.
    """
    results: list[dict] = []
    for tc in transistor_circuits:
        ref = tc.get('reference', '')
        leds_on_load: list[str] = []

        if tc.get('load_type') == 'led':
            for net_key in ('collector_net', 'drain_net'):
                load_net = tc.get(net_key, '')
                if load_net and load_net in ctx.nets:
                    for p in ctx.nets[load_net]['pins']:
                        comp = ctx.comp_lookup.get(p['component'])
                        if comp and comp['type'] == 'led' and p['component'] not in leds_on_load:
                            leds_on_load.append(p['component'])

        if not leds_on_load:
            continue

        sense_r = tc.get('emitter_resistor') or tc.get('source_resistor')
        load_net = tc.get('collector_net', tc.get('drain_net', ''))

        results.append({
            'detector': 'detect_pwm_led_dimming', 'rule_id': 'PL-001',
            'category': 'led_control', 'reference': ref,
            'transistor_type': tc.get('type', ''),
            'leds': leds_on_load,
            'sense_resistor': sense_r,
            'severity': 'info', 'confidence': 'deterministic', 'evidence_source': 'topology',
            'summary': f'Transistor-driven LED: {ref} driving {", ".join(leds_on_load)}',
            'description': (
                f'Transistor {ref} ({tc.get("value", "")}) drives LED(s) '
                f'{", ".join(leds_on_load)} {"with" if sense_r else "without"} '
                f'current sense resistor.'
            ),
            'components': [ref] + leds_on_load, 'nets': [load_net] if load_net else [],
            'pins': [],
            'recommendation': '' if sense_r else 'Consider adding a current sense resistor for LED current regulation.',
            'report_context': {'section': 'LED Control', 'impact': '', 'standard_ref': ''},
            'provenance': make_provenance('pwm_led_topology', 'deterministic', claimed_components=[ref]),
        })
    return results


# ---------------------------------------------------------------------------
# AH-001: Audio headphone jack switch detection
# ---------------------------------------------------------------------------

_AUDIO_CODEC_KEYWORDS = (
    'wm8', 'wm8960', 'wm8978', 'wm8731', 'wm8994',
    'sgtl5000', 'tlv320', 'cs42', 'cs43', 'cs47',
    'es8388', 'es8311', 'es7210',
    'max9', 'max98',
    'ssm26', 'adau17',
    'ak4', 'ak5',
    'pcm51', 'pcm17', 'pcm29', 'pcm31',
    'tas2', 'tas5', 'tas6',
    'nau88',
)

_HP_JACK_KEYWORDS = ('headphone', 'hp_jack', 'audio_jack', 'phone_jack', 'trrs', 'trs')
_HP_DET_PIN_NAMES = ('HP_DET', 'HPDET', 'JACKDET', 'JACK_DET', 'DETECT', 'DET', 'SENSE', 'SW')


def detect_headphone_jack(ctx: AnalysisContext) -> list[dict]:
    """AH-001: Detect headphone jack insertion detection and codec wiring."""
    results: list[dict] = []
    codecs = [ic for ic in get_unique_ics(ctx) if match_ic_keywords(ic, _AUDIO_CODEC_KEYWORDS)]
    hp_jacks = [c for c in ctx.components if c['type'] == 'connector'
                and any(k in (c.get('value', '') + ' ' + c.get('lib_id', '')).lower() for k in _HP_JACK_KEYWORDS)]
    if not hp_jacks:
        return results

    for jack in hp_jacks:
        ref = jack['reference']
        det_net = _get_pin_net_domain(ctx, ref, _HP_DET_PIN_NAMES)
        entry = {
            'detector': 'detect_headphone_jack', 'rule_id': 'AH-001',
            'category': 'audio', 'reference': ref, 'value': jack.get('value', ''),
            'detection_pin_net': det_net, 'associated_codec': None,
            'severity': 'info', 'confidence': 'heuristic', 'evidence_source': 'topology',
            'summary': f'Headphone jack {ref} ({jack.get("value", "")})',
            'description': f'Detected headphone jack {ref}.',
            'components': [ref], 'nets': [], 'pins': [], 'recommendation': '',
            'report_context': {'section': 'Audio', 'impact': '', 'standard_ref': ''},
        }
        jack_pins = ctx.ref_pins.get(ref, {})
        for codec in codecs:
            codec_ref = codec['reference']
            codec_nets = set(net for net, _ in ctx.ref_pins.get(codec_ref, {}).values() if net)
            jack_nets = set(net for net, _ in jack_pins.values() if net)
            shared = {n for n in (codec_nets & jack_nets) if n and not ctx.is_power_net(n) and not ctx.is_ground(n)}
            if shared:
                entry['associated_codec'] = {'ref': codec_ref, 'value': codec.get('value', '')}
                entry['components'].append(codec_ref)
                entry['nets'] = list(shared)[:5]
                break
        if not det_net and entry['associated_codec']:
            entry['recommendation'] = (
                f'Headphone jack {ref} has no insertion detection pin connected. '
                f'Consider connecting switch pin to codec {entry["associated_codec"]["ref"]} HP_DET input.'
            )
        entry['provenance'] = make_provenance('headphone_jack_topology', 'deterministic', claimed_components=[ref])
        results.append(entry)
    return results
