#!/usr/bin/env python3
"""Cross-domain analysis — checks requiring both schematic and PCB data.

Consumes schematic and PCB analyzer JSON outputs. Produces rich findings
for checks that span the schematic-PCB boundary: connector current capacity,
ESD coverage gaps, decoupling adequacy, and schematic/PCB cross-validation.

Usage:
    python3 cross_analysis.py --schematic sch.json --pcb pcb.json [--output cross_analysis.json]
    python3 cross_analysis.py --schematic sch.json  # PCB-less mode (limited checks)
    python3 cross_analysis.py --schema               # Print output schema
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from finding_schema import make_finding, compute_trust_summary, assign_finding_ids
from kicad_utils import build_net_id_map as _build_net_id_map
from envelopes.cross_analysis import CrossAnalysisEnvelope
from schema_codec import emit_schema
from inputs_builder import build_inputs, build_upstream_artifact, build_compat
from capability_mode import get_capability_mode_ref

ANALYZER_SOURCE = "cross"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_ground_net(name: str) -> bool:
    if not name:
        return False
    n = name.upper().replace('/', '').replace('-', '').replace('_', '')
    return n in ('GND', 'VSS', 'DGND', 'AGND', 'PGND', 'GNDD', 'GNDA',
                 'GND_D', 'GND_A', 'EARTH', 'CHASSIS', '0V')


def _is_power_net(name: str) -> bool:
    if not name:
        return False
    n = name.upper()
    if _is_ground_net(name):
        return True
    if n.startswith(('+', 'VCC', 'VDD', 'VBUS', 'VIN', 'VBAT', 'VSYS')):
        return True
    if re.match(r'^\+?\d+V\d*', n):
        return True
    return False


def _parse_voltage_from_name(name: str) -> float | None:
    if not name:
        return None
    m = re.search(r'(\d+)V(\d+)', name.upper())
    if m:
        return float(m.group(1)) + float(m.group(2)) / (10 ** len(m.group(2)))
    m = re.search(r'(\d+\.?\d*)V', name.upper())
    if m:
        return float(m.group(1))
    return None


def _flagged_return_path_entries(pcb: dict, threshold_pct: float = 95.0) -> dict[str, dict]:
    """Return nets with measured return-plane coverage below threshold."""
    flagged: dict[str, dict] = {}
    for entry in pcb.get('return_path_continuity', []) or []:
        net_name = entry.get('net', '')
        coverage = entry.get('reference_plane_coverage_pct', 100)
        if net_name and isinstance(coverage, (int, float)) and coverage < threshold_pct:
            flagged[net_name] = entry
    return flagged


def _island_size_map(graph: dict) -> dict[int, int]:
    """Return {island_id: member_count} for a connectivity graph."""
    sizes: dict[int, int] = {}
    for island_id in (graph.get('components', {}) or {}).values():
        if isinstance(island_id, int):
            sizes[island_id] = sizes.get(island_id, 0) + 1
    return sizes


# ---------------------------------------------------------------------------
# CC-001: Connector current capacity
# ---------------------------------------------------------------------------

_IPC2152_1OZ_10C = {
    0.5: 0.25, 1.0: 0.50, 2.0: 1.10, 3.0: 1.80,
    5.0: 3.50, 7.0: 5.50, 10.0: 9.0,
}


def _min_trace_width_for_current(current_a: float) -> float:
    prev_i, prev_w = 0.0, 0.0
    for i, w in sorted(_IPC2152_1OZ_10C.items()):
        if current_a <= i:
            if prev_i == 0:
                return w
            frac = (current_a - prev_i) / (i - prev_i)
            return prev_w + frac * (w - prev_w)
        prev_i, prev_w = i, w
    return prev_w


_NET_NAME_HEURISTICS = [
    (re.compile(r'(?i)CLK|CLOCK|XTAL|OSC'), 'clock'),
    (re.compile(r'(?i)USB_D[PM]|USB_D\+|USB_D.|USBDP|USBDM'), 'usb'),
    (re.compile(r'(?i)ETH_|MDIO|MDC|TX[PN]|RX[PN]'), 'ethernet'),
    (re.compile(r'(?i)DDR_|DQ\d|DQS|DM\d|CKE|ODT'), 'memory'),
    (re.compile(r'(?i)^SDA$|^SCL$|I2C'), 'i2c'),
    (re.compile(r'(?i)CAN[HL]|CAN_[HL]'), 'can'),
    (re.compile(r'(?i)MISO|MOSI|SCK|SPI'), 'spi'),
    (re.compile(r'(?i)\bSW$|SW_NODE|^LX$'), 'switching_node'),
    (re.compile(r'(?i)LVDS|MIPI'), 'lvds'),
]

_HIGH_SPEED_TYPES = {'clock', 'usb', 'ethernet', 'memory', 'hdmi', 'lvds', 'rf'}


def _get_net_classification(net_name, schematic):
    if schematic:
        classifications = schematic.get('net_classifications', {})
        if net_name in classifications:
            return classifications[net_name]
    for pattern, net_type in _NET_NAME_HEURISTICS:
        if pattern.search(net_name):
            return {'type': net_type, 'source': 'name_heuristic'}
    return None


def _get_highest_frequency(schematic):
    highest = 0.0
    if not schematic:
        return highest
    findings = schematic.get('findings', [])
    for f in findings:
        det = f.get('detector', '')
        if det == 'detect_crystal_circuits':
            freq = f.get('frequency')
            if isinstance(freq, (int, float)) and freq > highest:
                highest = freq
        elif det == 'detect_power_regulators':
            freq = f.get('switching_frequency_hz')
            if isinstance(freq, (int, float)) and freq > highest:
                highest = freq
    return highest


def _point_to_segment_distance(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / length_sq))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.sqrt((px - proj_x) ** 2 + (py - proj_y) ** 2)


def check_connector_current(schematic: dict, pcb: dict | None) -> list[dict]:
    """CC-001: Check connector pin current capacity vs trace width."""
    findings: list[dict] = []
    if not pcb:
        return findings

    footprints = pcb.get('footprints', [])
    fp_map = {fp.get('reference', ''): fp for fp in footprints}

    segments = pcb.get('tracks', {}).get('segments', [])
    net_id_map = _build_net_id_map(pcb)

    net_min_width: dict[str, float] = {}
    for seg in segments:
        net_id = seg.get('net', 0)
        net_name = net_id_map.get(net_id, '') if isinstance(net_id, int) else str(net_id)
        w = seg.get('width', 0) or 0
        if net_name and w > 0:
            if net_name not in net_min_width or w < net_min_width[net_name]:
                net_min_width[net_name] = w

    components = schematic.get('components', [])
    connectors = [c for c in components if c.get('type') == 'connector']
    regulators = [f for f in schematic.get('findings', [])
                  if f.get('detector') == 'detect_power_regulators']

    for conn in connectors:
        ref = conn['reference']
        fp = fp_map.get(ref)
        if not fp:
            continue
        for pad in fp.get('pads', []):
            net_name = pad.get('net_name', '')
            if not net_name or _is_ground_net(net_name) or not _is_power_net(net_name):
                continue
            voltage = _parse_voltage_from_name(net_name)
            if voltage is None:
                continue
            total_current = sum(
                reg.get('estimated_iout_A', 0) or 0
                for reg in regulators
                if reg.get('input_rail') == net_name
            )
            if total_current <= 0:
                continue
            trace_w = net_min_width.get(net_name)
            if trace_w is None:
                continue
            min_w = _min_trace_width_for_current(total_current)
            if trace_w < min_w * 0.8:
                findings.append(make_finding(
                    detector='check_connector_current', rule_id='CC-001',
                    category='current_capacity',
                    summary=f'Connector {ref}: trace on {net_name} too narrow for ~{total_current:.1f}A',
                    description=(
                        f'Power net {net_name} at connector {ref} carries estimated '
                        f'{total_current:.1f}A but narrowest trace is {trace_w:.2f}mm. '
                        f'IPC-2152 recommends >= {min_w:.2f}mm (1oz Cu, 10C rise).'
                    ),
                    severity='warning', confidence='heuristic', evidence_source='topology',
                    components=[ref], nets=[net_name],
                    recommendation=f'Widen trace on {net_name} to >= {min_w:.1f}mm or use copper pour.',
                    standard_ref='IPC-2152', impact='Trace overheating and voltage drop',
                
                    source=ANALYZER_SOURCE,))
    return findings


# ---------------------------------------------------------------------------
# EG-001: ESD coverage gap analysis
# ---------------------------------------------------------------------------

_EXTERNAL_CONNECTOR_KEYWORDS = (
    'usb', 'rj45', 'rj11', 'ethernet', 'hdmi', 'displayport',
    'barrel', 'dc_jack', 'bnc', 'sma', 'din', 'dsub', 'db9', 'db25',
    'screw_terminal', 'phoenix', 'molex',
)


def check_esd_coverage_gaps(schematic: dict, pcb: dict | None) -> list[dict]:
    """EG-001: Check for external connector pins missing ESD protection."""
    findings: list[dict] = []
    protection = [f for f in schematic.get('findings', [])
                  if f.get('detector') == 'detect_protection_devices']

    protected_nets: set[str] = set()
    for pd in protection:
        pnet = pd.get('protected_net', '')
        if pnet:
            protected_nets.add(pnet)
        for pn in pd.get('protected_nets', []):
            protected_nets.add(pn)

    components = schematic.get('components', [])
    connectors = [c for c in components if c.get('type') == 'connector']

    # Build pin_net lookup from schematic components
    pin_net_data = schematic.get('pin_net', {})

    for conn in connectors:
        val_lib = (conn.get('value', '') + ' ' + conn.get('lib_id', '')).lower()
        if not any(k in val_lib for k in _EXTERNAL_CONNECTOR_KEYWORDS):
            continue
        ref = conn['reference']

        unprotected_nets = []
        # Check via pin_net data (keys are "ref:pin_number" strings or tuples)
        if isinstance(pin_net_data, dict):
            for key, val in pin_net_data.items():
                key_str = str(key)
                if not key_str.startswith(ref + ':') and not key_str.startswith(f"('{ref}'"):
                    continue
                net = val[0] if isinstance(val, (list, tuple)) else val
                if not net or _is_power_net(net) or _is_ground_net(net):
                    continue
                if net not in protected_nets:
                    unprotected_nets.append(net)

        # Deduplicate
        unprotected_nets = list(dict.fromkeys(unprotected_nets))

        if unprotected_nets:
            findings.append(make_finding(
                detector='check_esd_coverage_gaps', rule_id='EG-001',
                category='esd_protection',
                summary=f'Connector {ref}: {len(unprotected_nets)} unprotected signal pin(s)',
                description=(
                    f'External connector {ref} ({conn.get("value", "")}) has '
                    f'{len(unprotected_nets)} unprotected signal net(s): '
                    f'{", ".join(unprotected_nets[:5])}{"..." if len(unprotected_nets) > 5 else ""}.'
                ),
                severity='warning', confidence='heuristic', evidence_source='topology',
                components=[ref], nets=unprotected_nets[:10],
                recommendation='Add TVS or ESD clamp diodes on unprotected external nets.',
                fix_params={
                    'type': 'add_protection',
                    'components': [{'type': 'tvs_diode', 'nets': unprotected_nets[:5]}],
                    'basis': 'IEC 61000-4-2 requires ESD protection on accessible pins',
                },
                standard_ref='IEC 61000-4-2', impact='ESD damage on unprotected pins',
            
                source=ANALYZER_SOURCE,))
    return findings


# ---------------------------------------------------------------------------
# DA-001: Decoupling strategy adequacy
# ---------------------------------------------------------------------------

def check_decoupling_adequacy(schematic: dict, pcb: dict | None) -> list[dict]:
    """DA-001: Per-IC decoupling assessment — count, value, and placement."""
    findings: list[dict] = []
    decoupling_list = [f for f in schematic.get('findings', [])
                       if f.get('detector') == 'detect_decoupling']
    decoupling = decoupling_list[0] if decoupling_list else {}
    if not decoupling:
        return findings

    rails = decoupling.get('per_rail', decoupling.get('rails', []))
    if isinstance(rails, dict):
        rails = list(rails.values())

    for rail in rails:
        rail_name = rail.get('rail', rail.get('name', ''))
        caps = rail.get('capacitors', [])
        ics = rail.get('ics', rail.get('ic_count', 0))
        ic_count = ics if isinstance(ics, int) else len(ics) if isinstance(ics, list) else 0
        if ic_count == 0:
            continue
        cap_count = len(caps)
        if cap_count < ic_count:
            findings.append(make_finding(
                detector='check_decoupling_adequacy', rule_id='DA-001',
                category='power_integrity',
                summary=f'Rail {rail_name}: {cap_count} caps for {ic_count} ICs',
                description=(
                    f'Power rail {rail_name} has {cap_count} decoupling cap(s) for '
                    f'{ic_count} IC(s). Best practice: at least one 100nF per IC.'
                ),
                severity='warning' if cap_count == 0 else 'info',
                confidence='heuristic', evidence_source='topology',
                nets=[rail_name],
                recommendation=f'Add {ic_count - cap_count} more 100nF caps on {rail_name}.',
                fix_params={
                    'type': 'add_component',
                    'components': [{'type': 'capacitor', 'value': '100n',
                                    'net_from': rail_name, 'net_to': 'GND'}] * min(ic_count - cap_count, 5),
                    'basis': 'One 100nF per IC power pin pair minimum',
                },
                impact='Increased power supply noise and EMI',
            
                source=ANALYZER_SOURCE,))
    return findings


# ---------------------------------------------------------------------------
# XV-001..003: Schematic/PCB cross-validation
# ---------------------------------------------------------------------------

def check_cross_validation(schematic: dict, pcb: dict | None) -> list[dict]:
    """XV-001..003: Cross-validate schematic and PCB data consistency."""
    findings: list[dict] = []
    if not pcb:
        return findings

    sch_refs = {c.get('reference', '') for c in schematic.get('components', [])
                if c.get('reference', '') and not c['reference'].startswith('#')}
    pcb_refs = {fp.get('reference', '') for fp in pcb.get('footprints', [])
                if fp.get('reference', '') and not fp['reference'].startswith('#')}

    in_sch_not_pcb = sch_refs - pcb_refs
    in_pcb_not_sch = pcb_refs - sch_refs

    # XV-001: Components in schematic but not PCB
    real_missing = {r for r in in_sch_not_pcb if not r.startswith(('TP', 'MH', 'NT', 'FID'))}
    if real_missing:
        findings.append(make_finding(
            detector='check_cross_validation', rule_id='XV-001', category='design_sync',
            summary=f'{len(real_missing)} component(s) in schematic but not PCB',
            description=f'Missing from PCB: {", ".join(sorted(real_missing)[:20])}{"..." if len(real_missing) > 20 else ""}.',
            severity='warning', confidence='deterministic', evidence_source='topology',
            components=sorted(real_missing)[:20],
            recommendation='Update PCB from schematic (Tools > Update PCB from Schematic).',
            impact='Missing components on manufactured board',
        
            source=ANALYZER_SOURCE,))

    # XV-001: Components in PCB but not schematic
    real_extra = {r for r in in_pcb_not_sch if not r.startswith(('TP', 'MH', 'NT', 'FID', 'H', 'G'))}
    if real_extra:
        findings.append(make_finding(
            detector='check_cross_validation', rule_id='XV-001', category='design_sync',
            summary=f'{len(real_extra)} component(s) in PCB but not schematic',
            description=f'Extra in PCB: {", ".join(sorted(real_extra)[:20])}{"..." if len(real_extra) > 20 else ""}.',
            severity='info', confidence='deterministic', evidence_source='topology',
            components=sorted(real_extra)[:20],
            recommendation='Verify these are intentional (mounting holes, test points, fiducials).',
        
            source=ANALYZER_SOURCE,))

    # XV-002: Value consistency
    pcb_fp_map = {fp.get('reference', ''): fp for fp in pcb.get('footprints', [])}
    sch_comp_map = {c.get('reference', ''): c for c in schematic.get('components', [])}
    for ref in sch_refs & pcb_refs:
        sch_val = sch_comp_map.get(ref, {}).get('value', '')
        pcb_fp = pcb_fp_map.get(ref, {})
        pcb_val = pcb_fp.get('value', '')
        # KH-326: skip cross-check if either value is malformed (not a string).
        # Parser edge case in analyze_pcb.py footprint parsing can yield a list.
        if not isinstance(sch_val, str) or not isinstance(pcb_val, str):
            continue
        if sch_val and pcb_val and sch_val != pcb_val:
            if sch_val.replace(' ', '') == pcb_val.replace(' ', ''):
                continue
            # Skip when the PCB "value" is actually the footprint library name
            # (never synced from schematic — KiCad default on fresh placement)
            pcb_footprint = pcb_fp.get('footprint', '')
            if pcb_val == pcb_footprint or pcb_val == pcb_footprint.split(':')[-1]:
                continue
            findings.append(make_finding(
                detector='check_cross_validation', rule_id='XV-002', category='design_sync',
                summary=f'{ref}: value mismatch — "{sch_val}" vs "{pcb_val}"',
                description=f'{ref} has "{sch_val}" in schematic but "{pcb_val}" in PCB.',
                severity='warning', confidence='deterministic', evidence_source='topology',
                components=[ref],
                recommendation='Sync PCB with schematic to resolve value differences.',
                impact='Wrong component may be placed during assembly',
            
                source=ANALYZER_SOURCE,))

    return findings


# ---------------------------------------------------------------------------
# NR-001: Critical net routing near board edges
# ---------------------------------------------------------------------------

_EDGE_DISTANCE_ERROR_MM = 1.0
_EDGE_DISTANCE_WARN_MM = 2.0


def check_critical_net_routing(schematic, pcb):
    """NR-001: Flag high-speed/clock signal traces routed near board edges."""
    findings = []
    if not pcb:
        return findings
    segments = pcb.get('tracks', {}).get('segments', [])
    if not segments:
        return findings
    outline = pcb.get('board_outline', {})
    outline_segs = outline.get('segments', [])
    if not outline_segs:
        return findings
    net_id_map = _build_net_id_map(pcb)
    flagged_nets = {}
    for seg in segments:
        net_id = seg.get('net', 0)
        net_name = net_id_map.get(net_id, '') if isinstance(net_id, int) else str(net_id)
        if not net_name or _is_power_net(net_name) or _is_ground_net(net_name):
            continue
        classification = _get_net_classification(net_name, schematic)
        if not classification or classification.get('type') not in _HIGH_SPEED_TYPES:
            continue
        mx = (seg.get('x1', 0) + seg.get('x2', 0)) / 2
        my = (seg.get('y1', 0) + seg.get('y2', 0)) / 2
        min_dist = float('inf')
        for edge in outline_segs:
            ex1 = edge.get('x1', edge.get('start_x', 0))
            ey1 = edge.get('y1', edge.get('start_y', 0))
            ex2 = edge.get('x2', edge.get('end_x', 0))
            ey2 = edge.get('y2', edge.get('end_y', 0))
            d = _point_to_segment_distance(mx, my, ex1, ey1, ex2, ey2)
            if d < min_dist:
                min_dist = d
        if min_dist < _EDGE_DISTANCE_WARN_MM:
            if net_name not in flagged_nets or min_dist < flagged_nets[net_name]:
                flagged_nets[net_name] = min_dist
    for net_name, dist in flagged_nets.items():
        classification = _get_net_classification(net_name, schematic)
        net_type = classification.get('type', 'signal') if classification else 'signal'
        severity = 'error' if dist < _EDGE_DISTANCE_ERROR_MM else 'warning'
        findings.append(make_finding(
            detector='check_critical_net_routing', rule_id='NR-001',
            category='signal_routing',
            summary=f'{net_type} net {net_name}: {dist:.1f}mm from board edge',
            description=f'High-speed {net_type} net {net_name} is routed {dist:.1f}mm from the board edge. Signals near edges radiate more effectively.',
            severity=severity, confidence='deterministic', evidence_source='topology',
            nets=[net_name],
            recommendation=f'Re-route {net_name} at least {_EDGE_DISTANCE_WARN_MM}mm from board edges.',
            impact='Increased EMI radiation and susceptibility',
        
            source=ANALYZER_SOURCE,))
    return findings


# ---------------------------------------------------------------------------
# RP-002: Enhanced return path validation
# ---------------------------------------------------------------------------

def check_return_path_enhanced(schematic, pcb):
    """RP-002: Check for reference plane gaps under classified signal nets."""
    findings = []
    if not pcb:
        return findings
    segments = pcb.get('tracks', {}).get('segments', [])
    if not segments:
        return findings
    conn_graph = pcb.get('connectivity_graph', {})
    net_id_map = _build_net_id_map(pcb)
    rpc_flagged = _flagged_return_path_entries(pcb, threshold_pct=95.0)
    has_rpc_data = len(pcb.get('return_path_continuity', []) or []) > 0
    plane_gaps = []
    for net_name, graph in conn_graph.items():
        if not (_is_ground_net(net_name) or _is_power_net(net_name)):
            continue
        for gap in graph.get('gaps', []):
            plane_gaps.append({**gap, 'net': net_name})
    if not plane_gaps:
        rpc = pcb.get('return_path_continuity', [])
        for entry in rpc:
            coverage = entry.get('reference_plane_coverage_pct', 100)
            if coverage < 90:
                net_name = entry.get('net', '')
                classification = _get_net_classification(net_name, schematic)
                if classification and classification.get('type') in _HIGH_SPEED_TYPES:
                    findings.append(make_finding(
                        detector='check_return_path_enhanced', rule_id='RP-002',
                        category='return_path',
                        summary=f'Net {net_name}: {coverage:.0f}% reference plane coverage',
                        description=f'High-speed net {net_name} has only {coverage:.0f}% reference plane coverage.',
                        severity='warning', confidence='heuristic', evidence_source='topology',
                        nets=[net_name],
                        recommendation='Re-route signal to avoid reference plane gaps.',
                        impact='Increased loop area and EMI',
                    
                        source=ANALYZER_SOURCE,))
        return findings
    flagged = set()
    for seg in segments:
        net_id = seg.get('net', 0)
        net_name = net_id_map.get(net_id, '') if isinstance(net_id, int) else str(net_id)
        if not net_name or _is_power_net(net_name) or _is_ground_net(net_name):
            continue
        if net_name in flagged:
            continue
        if has_rpc_data and net_name not in rpc_flagged:
            continue
        classification = _get_net_classification(net_name, schematic)
        if not classification:
            continue
        sx1, sy1 = seg.get('x1', 0), seg.get('y1', 0)
        sx2, sy2 = seg.get('x2', 0), seg.get('y2', 0)
        seg_min_x, seg_max_x = min(sx1, sx2), max(sx1, sx2)
        seg_min_y, seg_max_y = min(sy1, sy2), max(sy1, sy2)
        for gap in plane_gaps:
            bbox = gap.get('bbox', [0, 0, 0, 0])
            if (seg_max_x >= bbox[0] and seg_min_x <= bbox[2] and
                    seg_max_y >= bbox[1] and seg_min_y <= bbox[3]):
                net_type = classification.get('type', 'signal')
                severity = 'error' if net_type in _HIGH_SPEED_TYPES else 'warning'
                findings.append(make_finding(
                    detector='check_return_path_enhanced', rule_id='RP-002',
                    category='return_path',
                    summary=f'{net_type} net {net_name} crosses {gap["net"]} plane gap',
                    description=f'{net_type} signal {net_name} crosses a gap in {gap["net"]} plane on layer {gap.get("layer", "?")}.',
                    severity=severity, confidence='deterministic', evidence_source='topology',
                    nets=[net_name, gap['net']],
                    recommendation=f'Re-route {net_name} to avoid the {gap["net"]} plane gap, or bridge with a stitching capacitor.',
                    impact='Increased EMI from enlarged return path loop',
                
                    source=ANALYZER_SOURCE,))
                flagged.add(net_name)
                break
    return findings


# ---------------------------------------------------------------------------
# TW-001: Trace width validation
# ---------------------------------------------------------------------------

def check_trace_width_power(schematic, pcb):
    """TW-001: Check all power net trace widths against IPC-2152."""
    findings = []
    if not pcb or not schematic:
        return findings
    segments = pcb.get('tracks', {}).get('segments', [])
    if not segments:
        return findings
    net_id_map = _build_net_id_map(pcb)
    regulators = [f for f in schematic.get('findings', [])
                  if f.get('detector') == 'detect_power_regulators']
    net_current = {}
    for reg in regulators:
        output_rail = reg.get('output_rail', '')
        iout = reg.get('estimated_iout_A', 0) or 0
        if output_rail and iout > 0:
            net_current[output_rail] = max(net_current.get(output_rail, 0), iout)
        input_rail = reg.get('input_rail', '')
        if input_rail and iout > 0:
            net_current[input_rail] = net_current.get(input_rail, 0) + iout
    if not net_current:
        return findings
    net_min_width = {}
    for seg in segments:
        net_id = seg.get('net', 0)
        net_name = net_id_map.get(net_id, '') if isinstance(net_id, int) else str(net_id)
        w = seg.get('width', 0) or 0
        if net_name in net_current and w > 0:
            if net_name not in net_min_width or w < net_min_width[net_name]:
                net_min_width[net_name] = w
    for net_name, current in net_current.items():
        trace_w = net_min_width.get(net_name)
        if trace_w is None:
            continue
        min_w = _min_trace_width_for_current(current)
        if trace_w < min_w * 0.8:
            findings.append(make_finding(
                detector='check_trace_width_power', rule_id='TW-001',
                category='current_capacity',
                summary=f'Power net {net_name}: trace {trace_w:.2f}mm too narrow for ~{current:.1f}A',
                description=f'Power net {net_name} carries ~{current:.1f}A but narrowest trace is {trace_w:.2f}mm. IPC-2152 recommends >= {min_w:.2f}mm.',
                severity='warning', confidence='heuristic', evidence_source='topology',
                nets=[net_name],
                recommendation=f'Widen {net_name} traces to >= {min_w:.1f}mm or use copper pour.',
                fix_params={'type': 'resistor_value_change', 'change': f'trace width -> {min_w:.1f}mm', 'basis': f'IPC-2152: {current:.1f}A'},
                standard_ref='IPC-2152', impact='Trace overheating and voltage drop',
            
                source=ANALYZER_SOURCE,))
    return findings


# ---------------------------------------------------------------------------
# PS-002: Plane split detection
# ---------------------------------------------------------------------------

def check_plane_splits(schematic, pcb):
    """PS-002: Detect ground/power plane splits and signal traces crossing them."""
    findings = []
    if not pcb:
        return findings
    conn_graph = pcb.get('connectivity_graph', {})
    if not conn_graph:
        return findings
    segments = pcb.get('tracks', {}).get('segments', [])
    net_id_map = _build_net_id_map(pcb)
    rpc_flagged = _flagged_return_path_entries(pcb, threshold_pct=95.0)
    for plane_net, graph in conn_graph.items():
        if not (_is_ground_net(plane_net) or _is_power_net(plane_net)):
            continue
        if graph.get('islands', 1) <= 1:
            continue
        island_sizes = _island_size_map(graph)
        significant_islands = [size for size in island_sizes.values() if size >= 2]
        is_intentional = any(plane_net.upper().startswith(p) for p in ('AGND', 'DGND', 'PGND', 'GNDA', 'GNDD'))
        gaps = graph.get('gaps', [])
        if not gaps:
            continue
        crossing_signals = []
        for seg in segments:
            seg_net_id = seg.get('net', 0)
            seg_net = net_id_map.get(seg_net_id, '') if isinstance(seg_net_id, int) else str(seg_net_id)
            if not seg_net or _is_power_net(seg_net) or _is_ground_net(seg_net):
                continue
            sx1, sy1 = seg.get('x1', 0), seg.get('y1', 0)
            sx2, sy2 = seg.get('x2', 0), seg.get('y2', 0)
            for gap in gaps:
                bbox = gap.get('bbox', [0, 0, 0, 0])
                if (max(sx1, sx2) >= bbox[0] and min(sx1, sx2) <= bbox[2] and
                        max(sy1, sy2) >= bbox[1] and min(sy1, sy2) <= bbox[3]):
                    if seg_net not in crossing_signals:
                        crossing_signals.append(seg_net)
                    break
        crossing_signals_rpc = [s for s in crossing_signals if s in rpc_flagged]
        if len(significant_islands) <= 1 and not crossing_signals_rpc:
            continue
        if is_intentional:
            severity = 'info'
        elif crossing_signals_rpc:
            has_hs = any(_get_net_classification(s, schematic) and
                         _get_net_classification(s, schematic).get('type') in _HIGH_SPEED_TYPES
                         for s in crossing_signals_rpc)
            severity = 'error' if has_hs else 'warning'
        else:
            severity = 'info'
        desc_signals = f' Signals crossing: {", ".join(crossing_signals_rpc[:5])}.' if crossing_signals_rpc else ''
        findings.append(make_finding(
            detector='check_plane_splits', rule_id='PS-002',
            category='plane_integrity',
            summary=f'{plane_net} plane split: {graph["islands"]} islands{", " + str(len(crossing_signals_rpc)) + " signals crossing" if crossing_signals_rpc else ""}',
            description=f'{plane_net} plane has {graph["islands"]} disconnected islands.{desc_signals}',
            severity=severity, confidence='deterministic', evidence_source='topology',
            nets=[plane_net] + crossing_signals_rpc[:5],
            recommendation=(
                'Bridge the plane gap with copper pour or stitching vias. '
                'If zones were modified after the last fill, run KiCad '
                'Edit → Fill All Zones (B) and re-run the analyzer first — '
                'stale zone fills are a common cause of apparent plane splits.'
            ),
            impact='Return path discontinuity increases EMI',

            source=ANALYZER_SOURCE,))
    return findings


# ---------------------------------------------------------------------------
# VS-002: Via stitching density
# ---------------------------------------------------------------------------

_SPEED_OF_LIGHT = 3e8
_EFFECTIVE_ER = 4.2


def check_via_stitching_density(schematic, pcb):
    """VS-002: Check ground via stitching density against frequency requirements."""
    findings = []
    if not pcb:
        return findings
    via_list = pcb.get('vias', {}).get('vias', [])
    if not via_list:
        return findings
    net_id_map = _build_net_id_map(pcb)
    outline = pcb.get('board_outline', {})
    bbox = outline.get('bounding_box', {})
    board_w = bbox.get('width', 0)
    board_h = bbox.get('height', 0)
    if board_w <= 0 or board_h <= 0:
        return findings
    highest_freq = _get_highest_frequency(schematic)
    if highest_freq <= 0:
        highest_freq = 100e6
    wavelength_mm = (_SPEED_OF_LIGHT / math.sqrt(_EFFECTIVE_ER) / highest_freq) * 1000
    max_spacing_mm = wavelength_mm / 20
    board_x0 = bbox.get('x', bbox.get('min_x', 0))
    board_y0 = bbox.get('y', bbox.get('min_y', 0))
    gnd_vias = []
    for via in via_list:
        net_id = via.get('net', 0)
        net_name = net_id_map.get(net_id, '') if isinstance(net_id, int) else str(net_id)
        if _is_ground_net(net_name):
            gnd_vias.append((via.get('x', 0), via.get('y', 0)))
    if not gnd_vias:
        findings.append(make_finding(
            detector='check_via_stitching_density', rule_id='VS-002',
            category='via_stitching',
            summary='No ground stitching vias found',
            description='The board has no ground vias. Ground stitching vias are important for EMC.',
            severity='warning', confidence='deterministic', evidence_source='topology',
            recommendation=f'Add ground stitching vias at <= {max_spacing_mm:.0f}mm spacing.',
            impact='Poor ground plane connectivity between layers',
        
            source=ANALYZER_SOURCE,))
        return findings
    cell_size = max_spacing_mm
    if cell_size <= 0:
        return findings
    cells_x = max(1, int(math.ceil(board_w / cell_size)))
    cells_y = max(1, int(math.ceil(board_h / cell_size)))
    cell_counts = {}
    total_cells = cells_x * cells_y
    for vx, vy in gnd_vias:
        cx = max(0, min(int((vx - board_x0) / cell_size), cells_x - 1))
        cy = max(0, min(int((vy - board_y0) / cell_size), cells_y - 1))
        cell_counts[(cx, cy)] = cell_counts.get((cx, cy), 0) + 1
    empty_cells = total_cells - len(cell_counts)
    empty_pct = (empty_cells / total_cells * 100) if total_cells > 0 else 0
    if empty_pct > 30:
        findings.append(make_finding(
            detector='check_via_stitching_density', rule_id='VS-002',
            category='via_stitching',
            summary=f'Via stitching sparse: {empty_pct:.0f}% of board lacks ground vias',
            description=f'{empty_pct:.0f}% of board area (at {cell_size:.1f}mm grid) has no ground stitching vias. For {highest_freq/1e6:.0f}MHz, lambda/20 = {max_spacing_mm:.1f}mm.',
            severity='warning' if empty_pct > 50 else 'info',
            confidence='heuristic', evidence_source='topology',
            recommendation=f'Add ground stitching vias at <= {max_spacing_mm:.0f}mm intervals.',
            impact='Degraded ground plane connectivity at high frequencies',
        
            source=ANALYZER_SOURCE,))
    return findings


# ---------------------------------------------------------------------------
# DP-005: Differential pair routing quality
# ---------------------------------------------------------------------------

_DIFF_PAIR_SUFFIXES = [
    (re.compile(r'(.+)[_]?P$'), re.compile(r'(.+)[_]?N$')),
    (re.compile(r'(.+)\+$'), re.compile(r'(.+)-$')),
    (re.compile(r'(.+)_DP$'), re.compile(r'(.+)_DN$')),
    (re.compile(r'(.+)_TXP$'), re.compile(r'(.+)_TXN$')),
    (re.compile(r'(.+)_RXP$'), re.compile(r'(.+)_RXN$')),
]


def _find_diff_pairs(net_names, schematic):
    """Return pairs of net names that are explicitly marked differential.

    F7: The previous implementation had a suffix-only fallback loop that
    paired any nets matching `<base>P`/`<base>N` regardless of whether the
    schematic analyzer had identified them as a real differential interface.
    On gate-driver designs (INH/INL, HIN/LIN) and op-amp current-sense
    circuits (OUTP/OUTN, INP/INN) this fired DP-005 on every conventional
    naming pair. The fallback is gone — DP-005 now only fires when
    ``schematic['net_classifications'][<net>]['differential']`` is True
    for both endpoints. Conservative loss: any genuine diff pair the
    schematic analyzer failed to classify won't get a DP-005 finding.
    But every real differential interface (USB / LVDS / Ethernet / HDMI /
    CAN / etc.) is already classified by `_build_net_classifications`, so
    the loss is small relative to the false-positive reduction.
    """
    pairs = []
    if not schematic:
        return pairs
    classifications = schematic.get('net_classifications', {})
    diff_nets = [n for n, c in classifications.items() if c.get('differential')]
    if not diff_nets:
        return pairs
    seen = set()
    for p_pat, n_pat in _DIFF_PAIR_SUFFIXES:
        for net in diff_nets:
            if net in seen:
                continue
            m = p_pat.match(net)
            if m:
                base = m.group(1)
                for net2 in diff_nets:
                    if net2 in seen:
                        continue
                    m2 = n_pat.match(net2)
                    if m2 and m2.group(1) == base:
                        pairs.append((net, net2))
                        seen.add(net)
                        seen.add(net2)
                        break
    return pairs


def check_diff_pair_quality(schematic, pcb):
    """DP-005: Check differential pair routing quality."""
    findings = []
    if not pcb:
        return findings
    segments = pcb.get('tracks', {}).get('segments', [])
    via_list = pcb.get('vias', {}).get('vias', [])
    if not segments:
        return findings
    net_id_map = _build_net_id_map(pcb)
    all_net_names = list(set(net_id_map.values()))
    pairs = _find_diff_pairs(all_net_names, schematic)
    if not pairs:
        return findings
    net_stats = {}
    for seg in segments:
        net_id = seg.get('net', 0)
        net_name = net_id_map.get(net_id, '') if isinstance(net_id, int) else str(net_id)
        if not net_name:
            continue
        x1, y1 = seg.get('x1', 0), seg.get('y1', 0)
        x2, y2 = seg.get('x2', 0), seg.get('y2', 0)
        length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        stats = net_stats.setdefault(net_name, {'length_mm': 0, 'via_count': 0, 'layers': set()})
        stats['length_mm'] += length
        stats['layers'].add(seg.get('layer', ''))
    for via in (via_list or []):
        net_id = via.get('net', 0)
        net_name = net_id_map.get(net_id, '') if isinstance(net_id, int) else str(net_id)
        if net_name in net_stats:
            net_stats[net_name]['via_count'] = net_stats[net_name].get('via_count', 0) + 1
    for p_net, n_net in pairs:
        p_stats = net_stats.get(p_net)
        n_stats = net_stats.get(n_net)
        if not p_stats or not n_stats:
            continue
        issues = []
        p_vias = p_stats.get('via_count', 0)
        n_vias = n_stats.get('via_count', 0)
        if p_vias != n_vias:
            issues.append(f'via asymmetry ({p_vias} vs {n_vias})')
        p_layers = len(p_stats.get('layers', set()))
        n_layers = len(n_stats.get('layers', set()))
        if p_layers != n_layers:
            issues.append(f'layer transition asymmetry ({p_layers} vs {n_layers} layers)')
        p_len = p_stats.get('length_mm', 0)
        n_len = n_stats.get('length_mm', 0)
        avg_len = (p_len + n_len) / 2
        if avg_len > 0:
            mismatch_pct = abs(p_len - n_len) / avg_len * 100
            if mismatch_pct > 5:
                issues.append(f'length mismatch {abs(p_len - n_len):.1f}mm ({mismatch_pct:.0f}%)')
        if issues:
            findings.append(make_finding(
                detector='check_diff_pair_quality', rule_id='DP-005',
                category='differential_pair',
                summary=f'Diff pair {p_net}/{n_net}: {", ".join(issues)}',
                description=f'Differential pair {p_net}/{n_net} has routing issues: {"; ".join(issues)}.',
                severity='warning', confidence='deterministic', evidence_source='topology',
                nets=[p_net, n_net],
                recommendation='Match via counts, layer transitions, and trace lengths between P and N.',
                impact='Degraded signal integrity and increased common-mode EMI',
            
                source=ANALYZER_SOURCE,))
    return findings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_all_checks(schematic: dict, pcb: dict | None) -> list[dict]:
    findings: list[dict] = []
    findings.extend(check_connector_current(schematic, pcb))
    findings.extend(check_esd_coverage_gaps(schematic, pcb))
    findings.extend(check_decoupling_adequacy(schematic, pcb))
    findings.extend(check_cross_validation(schematic, pcb))
    # PCB intelligence checks
    findings.extend(check_critical_net_routing(schematic, pcb))
    findings.extend(check_return_path_enhanced(schematic, pcb))
    findings.extend(check_trace_width_power(schematic, pcb))
    findings.extend(check_plane_splits(schematic, pcb))
    findings.extend(check_via_stitching_density(schematic, pcb))
    findings.extend(check_diff_pair_quality(schematic, pcb))
    return findings


def main():
    parser = argparse.ArgumentParser(
        description='Cross-domain analysis — schematic + PCB combined checks')
    parser.add_argument('--schematic', '-s', default=None,
                        help='Schematic analyzer JSON. Auto-resolved from --analysis-dir current run when omitted.')
    parser.add_argument('--pcb', '-p', default=None,
                        help='PCB analyzer JSON (optional). Auto-resolved from --analysis-dir current run when omitted.')
    parser.add_argument('--output', '-o', default=None, help='Output JSON file path')
    parser.add_argument('--schema', action='store_true', help='Print output schema and exit')
    parser.add_argument('--text', action='store_true', help='Print human-readable text report')
    parser.add_argument('--analysis-dir', default=None, help='Write into analysis cache directory')
    parser.add_argument('--stage', default=None,
                        choices=['schematic', 'layout', 'pre_fab', 'bring_up'],
                        help='Filter findings by review stage')
    parser.add_argument('--audience', default=None,
                        choices=['designer', 'reviewer', 'manager'],
                        help='Audience level for summaries and --text output')
    parser.add_argument('--only-deterministic', action='store_true',
                        help='Accepted for consistency; analyzers never write llm_* fields. '
                             'Honored by downstream consumers (Phase 4 spec §3.4).')

    args = parser.parse_args()

    if args.schema:
        emit_schema(CrossAnalysisEnvelope)

    if args.analysis_dir and (not args.schematic or not args.pcb):
        from analysis_cache import get_current_run
        from pathlib import Path as _AutoPath
        _current = get_current_run(args.analysis_dir)
        if _current is not None:
            _run_dir, _ = _current
            if not args.schematic:
                _sch = _AutoPath(_run_dir) / "schematic.json"
                if _sch.is_file():
                    args.schematic = str(_sch)
            if not args.pcb:
                _pcb = _AutoPath(_run_dir) / "pcb.json"
                if _pcb.is_file():
                    args.pcb = str(_pcb)

    if not args.schematic:
        parser.error('--schematic is required (or pass --analysis-dir with a current run containing schematic.json)')

    t0 = time.time()

    with open(args.schematic, 'r') as f:
        schematic = json.load(f)

    if 'signal_analysis' in schematic and 'findings' not in schematic:
        print(f'Error: {args.schematic} uses the pre-v1.3 '
              f'signal_analysis wrapper format.\n'
              f'Re-run analyze_schematic.py to produce the current '
              f'findings[] format.', file=sys.stderr)
        sys.exit(1)

    pcb = None
    if args.pcb:
        with open(args.pcb, 'r') as f:
            pcb = json.load(f)

    # Build inputs provenance block (Track 1.3).
    from pathlib import Path as _Path
    _upstream_artifacts = {
        "schematic": build_upstream_artifact(_Path(args.schematic), schematic),
    }
    _source_files = [_Path(args.schematic)]
    if pcb is not None and args.pcb:
        _upstream_artifacts["pcb"] = build_upstream_artifact(_Path(args.pcb), pcb)
        _source_files.append(_Path(args.pcb))

    # Resolve canonical analysis_dir ONCE (audit Highest-Risk #4).
    if args.analysis_dir:
        _analysis_dir = _Path(args.analysis_dir)
    elif args.output:
        _analysis_dir = _Path(args.output).parent
    else:
        _analysis_dir = _Path("analysis")

    # Resolve capability_mode_ref BEFORE build_inputs (audit Highest-Risk #5).
    _capability_mode_ref = get_capability_mode_ref(_analysis_dir)

    inputs = build_inputs(
        source_files=_source_files,
        upstream_artifacts=_upstream_artifacts,
        run_id=_capability_mode_ref["run_id"],
    )
    compat = build_compat()

    findings = run_all_checks(schematic, pcb)
    elapsed = time.time() - t0

    sev_counts = {'error': 0, 'warning': 0, 'info': 0}
    for f_item in findings:
        sev = f_item.get('severity', 'info')
        sev_counts[sev] = sev_counts.get(sev, 0) + 1

    result = {
        'analyzer_type': 'cross_analysis',
        'schema_version': '1.4.0',
        'inputs': inputs,
        'compat': compat,
        'elapsed_s': round(elapsed, 3),
        'summary': {'total_findings': len(findings), 'by_severity': sev_counts},
        'findings': findings,
        'assessments': [],
        'trust_summary': compute_trust_summary(findings),
    }

    from output_filters import apply_output_filters
    apply_output_filters(result, args.stage, args.audience)

    # Guarantee every finding carries a stable finding_id (Layer 2 merge keys
    # on it). Runs after filtering; before any output branch.
    assign_finding_ids(result.get("findings", []), "cross_analysis")

    # Wire capability_mode_ref (Phase 4 spec §3.3). Resolved early so
    # inputs.run_id and capability_mode_ref.run_id match.
    result["capability_mode_ref"] = _capability_mode_ref

    if args.text:
        from output_filters import format_text
        print(format_text(result.get('findings', []), args.audience or 'designer', args.stage))
        sys.exit(0)

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f'Cross-analysis: {len(findings)} findings -> {args.output}', file=sys.stderr)
    elif args.analysis_dir:
        # Route into the current run folder via the manifest so that
        # cross_analysis.json co-locates with schematic.json + pcb.json
        # instead of landing at the analysis-dir root.
        import tempfile
        from analysis_cache import overwrite_current, CANONICAL_OUTPUTS, get_current_run
        analysis_dir = args.analysis_dir
        if not os.path.isabs(analysis_dir):
            analysis_dir = os.path.abspath(analysis_dir)
        filename = CANONICAL_OUTPUTS.get('cross_analysis', 'cross_analysis.json')
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_out = os.path.join(tmp_dir, filename)
            with open(tmp_out, 'w') as f:
                json.dump(result, f, indent=2)
            overwrite_current(analysis_dir, tmp_dir, source_hashes=None)
        current = get_current_run(analysis_dir)
        if current:
            out_path = os.path.join(current[0], filename)
        else:
            out_path = os.path.join(analysis_dir, filename)
        print(f'Cross-analysis: {len(findings)} findings -> {out_path}', file=sys.stderr)
    else:
        print(json.dumps(result, indent=2))

    return 0


if __name__ == '__main__':
    sys.exit(main())
