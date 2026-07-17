"""EMC geometric rule checks — operates on schematic + PCB analyzer JSON output.

Each check function returns a list of finding dicts with:
  - category: str (ground_plane, decoupling, io_filtering, etc.)
  - severity: str (CRITICAL, HIGH, MEDIUM, LOW, INFO)
  - rule_id: str (e.g., GP-001)
  - title: str
  - description: str
  - components: list[str] (reference designators involved)
  - nets: list[str] (net names involved)
  - layer: str (optional)
  - recommendation: str

Zero external dependencies beyond Python 3.8+ stdlib.
"""

import math
import re
from typing import List, Dict, Optional, Any

from emc_formulas import (
    lambda_over_20, wavelength_in_pcb, bandwidth_from_rise_time,
    knee_frequency, switching_harmonics_in_band, trapezoidal_corner_frequencies,
    trapezoidal_harmonic_amplitude, dm_radiation_dbuv_m, dm_max_loop_area_m2,
    cm_radiation_dbuv_m, get_emission_limit, board_cavity_resonances,
    harmonic_spectrum, cap_self_resonant_freq, estimate_esl, estimate_esr,
    interplane_capacitance_pf_per_cm2, propagation_delay_ps_per_mm,
    pdn_target_impedance, pdn_impedance_sweep, find_anti_resonances, polygon_area,
    cap_value_for_srf, round_to_e12,
    diff_pair_skew_ps, diff_pair_cm_voltage, point_to_segment_distance,
    DIFF_PAIR_PROTOCOLS, MARKET_STANDARDS,
    build_power_tree, enrich_power_tree_with_pcb,
    distributed_pdn_impedance_sweep, cross_rail_transient_current,
    parallel_cap_impedance,
)
from kicad_utils import lookup_switching_freq as _estimate_switching_freq, build_net_id_map
from finding_schema import Det, get_findings

try:
    import os as _os, sys as _sys
    _ds_scripts = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                                '..', '..', 'datasheets', 'scripts')
    if _os.path.isdir(_ds_scripts):
        _sys.path.insert(0, _os.path.abspath(_ds_scripts))
    from datasheet_features import get_mcu_features as _get_mcu_features
except ImportError:
    def _get_mcu_features(mpn, **kw): return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_power_or_ground(name: str) -> bool:
    """Check if a net name is power or ground."""
    if not name:
        return False
    low = name.lower().strip('+')
    for prefix in ('gnd', 'vcc', 'vdd', 'vss', 'vee', 'v+', 'v-',
                   '+3v', '+5v', '+12v', '+1v', '+2v', '+24v', '+48v',
                   '3v3', '5v0', '1v8', '1v2', '0v9', '2v5',
                   'vbat', 'vin', 'vbus', 'vsys', 'vmot', 'vmotor',
                   'vpwr', 'vm',  # F6: motor supply rails (vm/vmot/vmotor)
                   'avcc', 'avdd', 'dvcc', 'dvdd', 'agnd', 'dgnd',
                   'pgnd', 'earth', 'pwr', 'power'):
        if low == prefix or low.startswith(prefix + '_') or low.startswith(prefix + '/'):
            return True
    # Patterns like +3.3V, +5V, etc.
    if re.match(r'^[+-]?\d+\.?\d*v', low):
        return True
    return False


def _is_ground_net(name: str) -> bool:
    """Check if a net name is specifically a ground net."""
    if not name:
        return False
    # Strip hierarchical sheet path prefix (e.g., "/Power Supply/GND" → "GND")
    if "/" in name:
        name = name.rsplit("/", 1)[-1]
    low = name.lower()
    if low in ('gnd', 'vss', 'agnd', 'dgnd', 'pgnd', 'gnda', 'gndd',
               'earth', 'vee', 'gndpwr', '0v'):
        return True
    if low.startswith('gnd') or low.endswith('gnd'):
        return True
    if low.startswith('vss'):
        return True
    return False


def _is_clock_net(name: str) -> bool:
    """Heuristic: is this net name likely a clock signal?"""
    if not name:
        return False
    low = name.lower()
    clock_patterns = ('clk', 'clock', 'xtal', 'osc', 'mclk', 'bclk',
                      'sclk', 'pclk', 'hclk', 'fclk', 'lrclk', 'sck',
                      'hse', 'lse', 'xin', 'xout', 'clkin', 'clkout')
    for p in clock_patterns:
        if p in low:
            return True
    return False


def _is_high_speed_net(name: str) -> bool:
    """Heuristic: is this net likely high-speed (>10 MHz edge rates)?"""
    if _is_clock_net(name):
        return True
    low = name.lower()
    hs_patterns = ('usb', 'hdmi', 'eth', 'rgmii', 'sgmii', 'pcie',
                   'ddr', 'sdram', 'lvds', 'mipi', 'sata')
    for p in hs_patterns:
        if p in low:
            return True
    return False


def _extract_package(footprint_lib: str) -> Optional[str]:
    """Extract MLCC package size from footprint library ID."""
    if not footprint_lib:
        return None
    m = re.search(r'(\d{4})', footprint_lib)
    if m:
        pkg = m.group(1)
        if pkg in ('0201', '0402', '0603', '0805', '1206', '1210', '1812', '2220'):
            return pkg
    return None


def _safe_float(val, default=0.0):
    """Safely convert a value to float (handles None, str, etc.)."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _suggest_filtering(conn_ref: str, combined_lower: str) -> str:
    """Generate protocol-specific filtering suggestion for IO-001."""
    if 'usb' in combined_lower:
        return (
            f'Add ESD protection (e.g., USBLC6-2SC6 or TPD2E2U06) on {conn_ref} '
            f'data lines. Add ferrite bead (600Ω@100MHz) on VBUS. '
            f'For USB 3.x, add common-mode choke on SuperSpeed pairs.'
        )
    if 'ethernet' in combined_lower or 'rj45' in combined_lower:
        return (
            f'Add common-mode choke on TX/RX pairs near {conn_ref}. '
            f'Ethernet magnetics (if not integrated) provide galvanic isolation '
            f'and CM rejection.'
        )
    if 'hdmi' in combined_lower:
        return (
            f'Add ESD protection array on {conn_ref} TMDS pairs. '
            f'Add common-mode choke for EMI reduction on TMDS clock.'
        )
    if 'sma' in combined_lower or 'bnc' in combined_lower:
        return (
            f'Ensure {conn_ref} has proper ground connection to chassis/enclosure. '
            f'Add ESD protection if connected to external antenna.'
        )
    return (
        f'Add a ferrite bead (e.g., BLM18AG601SN1D, 600Ω@100MHz) on signal '
        f'lines near {conn_ref}. Add ESD/TVS protection for external interfaces.'
    )


def _suggest_pdn_cap(peak, cap_models, plane_cap_f, z_target, spice_backend,
                     sweep_before=None):
    """Generate a specific cap suggestion for a PDN anti-resonance peak.

    # EQ-093: C_suggest = 1/(4π²f²ESL) then round to E12 (PDN cap selection)
    # Source: Derived from EQ-089 (inverse SRF) + EQ-090 (E12 rounding)
    Picks a cap whose SRF falls at the peak frequency, optionally verifies
    with SPICE that the peak is resolved.  When sweep_before is provided,
    reuses the existing sweep data instead of re-simulating.
    """
    peak_freq = peak.get('freq_hz', 0)
    if peak_freq <= 0:
        return 'Add a capacitor with SRF near the anti-resonance frequency.'

    # Pick 0603 package and compute required capacitance
    package = '0603'
    esl = estimate_esl(package)
    c_farads = cap_value_for_srf(peak_freq, esl)
    c_rounded = round_to_e12(c_farads)

    # Format value nicely
    if c_rounded >= 1e-6:
        c_str = f'{c_rounded*1e6:.1f}µF'
    elif c_rounded >= 1e-9:
        c_str = f'{c_rounded*1e9:.0f}nF'
    else:
        c_str = f'{c_rounded*1e12:.0f}pF'

    suggestion = (
        f'Add {c_str} {package} MLCC near the IC power pins '
        f'(SRF ≈ {peak_freq/1e6:.1f}MHz fills the anti-resonance gap).'
    )

    # SPICE verification if available
    if spice_backend and cap_models:
        try:
            from emc_spice import verify_pdn_with_suggested_cap
            suggested = {
                'farads': c_rounded,
                'esr_ohm': estimate_esr(package),
                'esl_h': esl,
            }
            ok, before, after = verify_pdn_with_suggested_cap(
                cap_models, suggested, plane_cap_f, z_target, spice_backend,
                sweep_before=sweep_before)
            if ok and before is not None and after is not None:
                if after < before * 0.5:
                    suggestion += (
                        f' (SPICE-verified: peak reduced from '
                        f'{before:.2f}Ω to {after:.2f}Ω)'
                    )
                elif after < z_target:
                    suggestion += f' (SPICE-verified: peak resolved to {after:.2f}Ω)'
                else:
                    suggestion += (
                        f' (SPICE: peak reduced to {after:.2f}Ω but still '
                        f'above target {z_target:.3f}Ω — may need additional caps)'
                    )
        except Exception:
            suggestion += ' (analytical — verify with SPICE)'
    else:
        suggestion += ' (analytical — verify with SPICE if available)'

    return suggestion


def _connector_refs(footprints: list) -> list:
    """Find footprints that are likely external connectors."""
    connectors = []
    for fp in footprints:
        ref = fp.get('reference', '')
        raw_val = fp.get('value', '')
        val = (raw_val if isinstance(raw_val, str) else str(raw_val)).lower()
        raw_lib = fp.get('library', fp.get('lib_id', ''))
        lib = (raw_lib if isinstance(raw_lib, str) else str(raw_lib)).lower()
        if ref.startswith('J') or ref.startswith('P') or ref.startswith('CN'):
            # Exclude internal headers, test points, and jumpers
            if 'test' in val or 'tp' in val or 'jumper' in val or 'solder' in val:
                continue
            if ref.upper().startswith('JP') or ref.upper().startswith('SJ'):
                continue
            connectors.append(fp)
        elif 'connector' in lib or 'conn_' in lib or 'usb' in lib:
            connectors.append(fp)
    return connectors


# ---------------------------------------------------------------------------
# Finding construction helper
# ---------------------------------------------------------------------------

_EMC_SEVERITY_MAP = {
    'CRITICAL': 'error',
    'HIGH': 'error',
    'MEDIUM': 'warning',
    'LOW': 'info',
    'INFO': 'info',
    # Already-normalized pass-through
    'error': 'error',
    'warning': 'warning',
    'info': 'info',
}


def _normalize_severity(sev):
    """Map legacy EMC uppercase severities to the standard envelope vocabulary.

    Rich-format consumers expect {error, warning, info}. EMC rules were
    authored against the pre-v1.3 CRITICAL/HIGH/MEDIUM/LOW/INFO scheme —
    translate here rather than touch every call site.
    """
    if not isinstance(sev, str):
        return 'info'
    return _EMC_SEVERITY_MAP.get(sev, _EMC_SEVERITY_MAP.get(sev.upper(), 'info'))


def _make_finding(category, severity, rule_id, title, description,
                  recommendation='', components=None, nets=None,
                  confidence='deterministic',
                  evidence_source=None, fix_params=None,
                  report_section=None, impact=None, standard_ref=None,
                  **extra):
    """Build a standardized EMC finding dict with rich format fields.

    All EMC findings flow through this single factory. The rich format
    fields (detector, summary, pins, evidence_source, report_context)
    are auto-populated for backward compatibility.
    """
    finding = {
        'category': category,
        'severity': _normalize_severity(severity),
        'rule_id': rule_id,
        'confidence': confidence,
        'title': title,
        'description': description,
        'components': components if components is not None else [],
        'nets': nets if nets is not None else [],
        'recommendation': recommendation,
        # Rich format additions
        'detector': f'emc_{category}',
        'summary': title,
        'pins': [],
        'evidence_source': evidence_source or ('heuristic_rule' if confidence == 'heuristic' else 'topology'),
        'report_context': {
            'section': report_section or category.replace('_', ' ').title(),
            'impact': impact or '',
            'standard_ref': standard_ref or '',
        },
    }
    if fix_params is not None:
        finding['fix_params'] = fix_params
    if extra:
        finding.update(extra)
    return finding


# ---------------------------------------------------------------------------
# Category 1: Ground Plane Integrity
# ---------------------------------------------------------------------------

def check_return_path_coverage(pcb: Dict, severity_threshold: str = 'all') -> List[Dict]:
    """Check return path continuity for signal traces.

    Uses the PCB analyzer's return_path_continuity data (requires --full).
    """
    findings = []
    rpc = pcb.get('return_path_continuity') if pcb else None
    if rpc is None:
        findings.append(_make_finding(
            'ground_plane', 'INFO', 'GP-001',
            title='Return path analysis data not available',
            description=(
                'PCB analysis did not include return path continuity data. '
                'Run the PCB analyzer with --full flag to enable GP-001 '
                'reference plane coverage checking.'
            ),
            recommendation='Re-run PCB analysis with: python3 analyze_pcb.py <file> --full',
        ))
        return findings

    for entry in rpc:
        net_name = entry.get('net', '')
        coverage = entry.get('reference_plane_coverage_pct', 100)
        trace_mm = entry.get('total_trace_mm', 0)

        if coverage >= 95:
            continue

        is_hs = _is_high_speed_net(net_name) or _is_clock_net(net_name)

        if coverage < 50:
            severity = 'CRITICAL'
            title = 'Signal has major reference plane gap'
        elif coverage < 80:
            severity = 'CRITICAL' if is_hs else 'HIGH'
            title = 'Signal has significant reference plane gap'
        elif coverage < 95:
            severity = 'HIGH' if is_hs else 'MEDIUM'
            title = 'Signal has partial reference plane gap'
        else:
            continue

        findings.append(_make_finding(
            'ground_plane', severity, 'GP-001',
            title=title,
            description=(
                f'Net {net_name} has {coverage:.0f}% reference plane coverage '
                f'over {trace_mm:.1f}mm of routing. '
                f'Return current must detour around the gap, creating a loop antenna.'
            ),
            nets=[net_name],
            recommendation=(
                'Route this signal to avoid ground plane gaps, or fill the void. '
                'If a split is intentional, add a bridge capacitor across the gap.'
            ),
            confidence='heuristic',
            signal_net=net_name,
            coverage_pct=round(coverage, 1),
            trace_mm=round(trace_mm, 2),
            is_high_speed_or_clock=is_hs,
        ))

    return findings


def check_ground_zone_coverage(pcb: Dict) -> List[Dict]:
    """Check overall ground plane quality from zone data."""
    findings = []
    zones = pcb.get('zones', [])
    layers = pcb.get('layers', [])
    copper_layers = [l['name'] for l in layers if l.get('type') in ('signal', 'power')]

    # Find ground zones
    gnd_zones = [z for z in zones if _is_ground_net(z.get('net_name', ''))]

    if not gnd_zones and len(copper_layers) >= 2:
        rec = ('Add a solid ground pour on at least one inner layer.'
               if len(copper_layers) >= 4
               else 'Add a ground pour on B.Cu covering as much area as possible.')
        findings.append(_make_finding(
            'ground_plane', 'CRITICAL', 'GP-002',
            title='No ground plane zones detected',
            description=(
                f'Board has {len(copper_layers)} copper layers but no ground '
                f'plane zones were found. A solid ground plane is the single '
                f'most important EMC design feature.'
            ),
            recommendation=rec,
        ))
        return findings

    # Check ground zones for fragmentation
    for gz in gnd_zones:
        islands = gz.get('island_count', 1)
        fill_ratio = gz.get('fill_ratio', 1.0)
        layer = gz.get('layers', ['?'])[0] if isinstance(gz.get('layers'), list) else '?'

        if islands > 3:
            findings.append(_make_finding(
                'ground_plane', 'HIGH', 'GP-003',
                title='Fragmented ground plane',
                description=(
                    f'Ground zone on {layer} has {islands} disconnected islands. '
                    f'Fragmented ground planes create slot antennas and return '
                    f'path discontinuities.'
                ),
                nets=[gz.get('net_name', 'GND')],
                recommendation=(
                    'Connect ground plane islands with traces or vias. '
                    'Check for routing channels that split the ground plane.'
                ),
                layer=layer,
            ))

        if fill_ratio < 0.6:
            findings.append(_make_finding(
                'ground_plane', 'MEDIUM', 'GP-004',
                title='Low ground plane fill ratio',
                description=(
                    f'Ground zone on {layer} has {fill_ratio*100:.0f}% fill ratio. '
                    f'Excessive routing or thermal relief patterns may be '
                    f'reducing ground plane effectiveness.'
                ),
                nets=[gz.get('net_name', 'GND')],
                recommendation='Reduce routing density on this layer or move signals to other layers.',
                layer=layer,
            ))

    return findings


def check_ground_domains(pcb: Dict) -> List[Dict]:
    """Check for multiple ground domains that may cause issues."""
    findings = []
    gd = pcb.get('ground_domains', {})
    domain_count = gd.get('domain_count', 1)

    if domain_count > 1:
        domains = gd.get('domains', [])
        domain_names = [d.get('net_name', '?') for d in domains] if isinstance(domains, list) else []
        findings.append(_make_finding(
            'ground_plane', 'MEDIUM', 'GP-005',
            title=f'{domain_count} ground domains detected',
            description=(
                f'Board has {domain_count} separate ground domains: '
                f'{", ".join(domain_names[:5])}. '
                f'Multiple ground domains require careful single-point '
                f'connection to avoid ground loops and EMI.'
            ),
            nets=domain_names[:5],
            recommendation=(
                'Verify ground domains connect at a single, intentional point '
                '(typically near the ADC for analog/digital split). '
                'Ensure no signal traces cross the domain boundary.'
            ),
        ))

    return findings


# ---------------------------------------------------------------------------
# Category 2: Decoupling Effectiveness
# ---------------------------------------------------------------------------

def check_decoupling_distance(pcb: Dict) -> List[Dict]:
    """Check decoupling cap placement distance from ICs."""
    findings = []
    decoupling = pcb.get('decoupling_placement', [])

    for entry in decoupling:
        ic_ref = entry.get('ic', '')
        closest = entry.get('closest_cap_mm') or 0
        nearby = entry.get('nearby_caps', [])

        if not isinstance(closest, (int, float)) or closest <= 0:
            continue

        if closest > 8.0:
            findings.append(_make_finding(
                'decoupling', 'HIGH', 'DC-001',
                title=f'Decoupling cap too far from {ic_ref}',
                description=(
                    f'Nearest decoupling cap to {ic_ref} ({entry.get("value", "")}) '
                    f'is {closest:.1f}mm away. Each mm of trace adds 0.3-0.8 nH '
                    f'of loop inductance, reducing decoupling effectiveness '
                    f'at high frequencies.'
                ),
                components=[ic_ref] + [c['cap'] for c in nearby[:2]],
                recommendation=f'Move decoupling cap within 2-3mm of {ic_ref} power pins.',
            ))
        elif closest > 5.0:
            findings.append(_make_finding(
                'decoupling', 'MEDIUM', 'DC-001',
                title=f'Decoupling cap moderately far from {ic_ref}',
                description=(
                    f'Nearest decoupling cap to {ic_ref} ({entry.get("value", "")}) '
                    f'is {closest:.1f}mm away. Recommended: <3mm for best '
                    f'high-frequency performance.'
                ),
                components=[ic_ref] + [c['cap'] for c in nearby[:2]],
                recommendation=f'Move decoupling cap closer to {ic_ref} power pins if layout permits.',
            ))

    return findings


def check_missing_decoupling(pcb: Dict, schematic: Optional[Dict] = None) -> List[Dict]:
    """Check for ICs without any nearby decoupling capacitor."""
    findings = []
    footprints = pcb.get('footprints', [])
    decoupling = pcb.get('decoupling_placement', [])

    # ICs that have decoupling analysis entries
    ics_with_caps = {e.get('ic', '') for e in decoupling}

    # All IC-like footprints
    for fp in footprints:
        ref = fp.get('reference', '')
        if not re.match(r'^(U|IC)\d', ref):
            continue
        # Skip known non-ICs (ESD, TVS, etc.)
        raw_val = fp.get('value', '')
        val = (raw_val if isinstance(raw_val, str) else str(raw_val)).lower()
        if any(p in val for p in ('esd', 'tvs', 'test', 'tp', 'net_tie')):
            continue
        if ref not in ics_with_caps:
            findings.append(_make_finding(
                'decoupling', 'HIGH', 'DC-002',
                title=f'No decoupling cap found near {ref}',
                description=(
                    f'{ref} ({fp.get("value", "?")}) has no capacitor within '
                    f'10mm. Every IC with power pins needs at least one '
                    f'decoupling capacitor.'
                ),
                components=[ref],
                recommendation=(
                    f'Add 100nF X7R 0402 + 1µF X5R 0603 close to {ref} power pins. '
                    f'For high-speed ICs, add 10nF C0G for high-frequency decoupling. '
                    f'Place caps on the same side as {ref} with short, wide traces to vias.'
                ),
                confidence='heuristic',
                fix_params={
                    'type': 'add_component',
                    'components': [{'type': 'capacitor', 'value': '100n'}],
                    'basis': 'Standard 100nF decoupling per IC',
                },
            ))

    return findings


def check_decoupling_via_distance(pcb: Dict) -> List[Dict]:
    """DC-003: Check distance from decoupling caps to nearest via.

    The trace between a decoupling cap pad and its via to the power/ground
    plane adds connection inductance that degrades high-frequency
    decoupling. Each mm of trace adds ~0.5-0.8 nH.

    Requires individual via positions (from --full mode or vias.vias list).

    Ref: LearnEMC, "Estimating the Connection Inductance of Decoupling
    Capacitors" — via placement matters more than cap-to-IC distance.
    """
    # EQ-086: d = √(Δx²+Δy²) (cap-to-via distance for connection inductance)
    findings = []
    decoupling = pcb.get('decoupling_placement', [])
    if not decoupling:
        return findings

    vias_data = pcb.get('vias', {})
    via_list = vias_data.get('vias', [])
    if not via_list:
        return findings

    # KH-341: on 2-layer boards the "via to plane" model doesn't apply —
    # decoupling current returns through pours/traces, not plane vias.
    layers = pcb.get('layers', [])
    copper_layer_count = len([l for l in layers
                              if l.get('type') in ('signal', 'power')])
    if copper_layer_count == 2:
        return findings

    zones = pcb.get('zones', [])
    footprints = pcb.get('footprints', [])
    fp_positions = {fp.get('reference', ''): (fp.get('x') or 0, fp.get('y') or 0)
                    for fp in footprints}
    fp_by_ref = {fp.get('reference', ''): fp for fp in footprints}

    def _cap_in_same_net_pour(fp: Dict) -> bool:
        """True if the cap sits inside a same-layer zone of one of its own
        nets — the pour IS the connection, no via needed (KH-341).

        KH-356: analyzer output strips pad geometry from footprints, so
        this works from what survives: footprint center + connected_nets
        (pad_nets fallback). Center containment is a good proxy for a
        chip cap's pad positions.
        """
        fp_layer = fp.get('layer', 'F.Cu')
        fx = fp.get('x')
        fy = fp.get('y')
        if fx is None or fy is None:
            return False
        cap_nets = fp.get('connected_nets') or [
            v.get('net') for v in (fp.get('pad_nets') or {}).values()
            if isinstance(v, dict) and v.get('net')]
        for net in cap_nets:
            for z in zones:
                if z.get('net_name') != net:
                    continue
                if fp_layer not in (z.get('layers') or []):
                    continue
                bbox = z.get('filled_bbox') or z.get('outline_bbox')
                if not bbox or len(bbox) != 4:
                    continue
                if bbox[0] <= fx <= bbox[2] and bbox[1] <= fy <= bbox[3]:
                    return True
        return False

    for entry in decoupling:
        for cap_info in entry.get('nearby_caps', []):
            cap_ref = cap_info.get('cap', '')
            if cap_ref not in fp_positions:
                continue

            cx, cy = fp_positions[cap_ref]

            _cap_fp = fp_by_ref.get(cap_ref)
            if _cap_fp and _cap_in_same_net_pour(_cap_fp):
                continue

            # Find nearest via to this cap
            min_via_dist = float('inf')
            for via in via_list:
                vx = via.get('x', 0)
                vy = via.get('y', 0)
                d = math.sqrt((cx - vx)**2 + (cy - vy)**2)
                if d < min_via_dist:
                    min_via_dist = d

            if min_via_dist == float('inf'):
                continue

            # Flag if cap is >3mm from nearest via (high connection inductance)
            if min_via_dist > 3.0:
                est_inductance = min_via_dist * 0.7  # ~0.7 nH/mm
                findings.append(_make_finding(
                    'decoupling', 'MEDIUM', 'DC-003',
                    title=f'Decoupling cap {cap_ref} far from via',
                    description=(
                        f'{cap_ref} is {min_via_dist:.1f}mm from the nearest '
                        f'via (~{est_inductance:.1f}nH connection inductance). '
                        f'Long traces between cap and via degrade high-frequency '
                        f'decoupling effectiveness.'
                    ),
                    components=[cap_ref, entry.get('ic', '')],
                    recommendation=(
                        f'Place a via directly adjacent to {cap_ref} pads. '
                        f'Use fat, short traces from cap pads to via.'
                    ),
                ))

    return findings


# ---------------------------------------------------------------------------
# Category 3: I/O Interface Filtering
# ---------------------------------------------------------------------------

def check_connector_filtering(pcb: Dict, schematic: Optional[Dict] = None) -> List[Dict]:
    """Check for filter components near external connectors."""
    # EQ-035: d = √(Δx²+Δy²) (filter-to-connector distance)
    findings = []
    footprints = pcb.get('footprints', [])
    connectors = _connector_refs(footprints)

    if not connectors:
        return findings

    # Find filter-like components (ferrites, CM chokes, ESD, TVS)
    filters = []
    for fp in footprints:
        ref = fp.get('reference', '')
        raw_val = fp.get('value', '')
        val = (raw_val if isinstance(raw_val, str) else str(raw_val)).lower()
        raw_lib = fp.get('library', fp.get('lib_id', ''))
        lib = (raw_lib if isinstance(raw_lib, str) else str(raw_lib)).lower()
        is_filter = False
        if ref.startswith('FB') or ref.startswith('L'):
            if 'ferrite' in val or 'ferrite' in lib or 'bead' in val:
                is_filter = True
            elif ref.startswith('FB'):
                is_filter = True
        if any(kw in val for kw in ('esd', 'tvs', 'pesd', 'usblc', 'prtr',
                                     'ip4220', 'tpd', 'sp05', 'cm_choke',
                                     'common_mode')):
            is_filter = True
        if 'common_mode' in lib or 'cmchoke' in lib:
            is_filter = True
        if is_filter:
            filters.append(fp)

    # Also include protection devices from schematic
    protection_refs = set()
    if schematic:
        for pd in get_findings(schematic, Det.PROTECTION_DEVICES):
            protection_refs.add(pd.get('reference', ''))

    # For each connector, check if there's a filter component nearby
    for conn in connectors:
        cx = conn.get('x') or 0
        cy = conn.get('y') or 0
        conn_ref = conn.get('reference', '')
        conn_val = conn.get('value', '')

        has_nearby_filter = False
        for filt in filters:
            fx = filt.get('x') or 0
            fy = filt.get('y') or 0
            dist = math.sqrt((cx - fx)**2 + (cy - fy)**2)
            if dist <= 25.0:
                has_nearby_filter = True
                break

        # Also check schematic-detected protection
        if not has_nearby_filter:
            conn_nets = set()
            for pad in conn.get('pads', []):
                n = pad.get('net_name', '')
                if n and not _is_power_or_ground(n):
                    conn_nets.add(n)

            if schematic:
                for pd in get_findings(schematic, Det.PROTECTION_DEVICES):
                    prot_net = pd.get('protected_net', '')
                    if prot_net in conn_nets:
                        has_nearby_filter = True
                        break

        if not has_nearby_filter:
            # Determine if this connector is likely external
            # Simple heuristic: USB, HDMI, Ethernet, barrel jack, RJ45 are external
            is_external = False
            combined = (conn_val + ' ' + conn.get('library', conn.get('lib_id', ''))).lower()
            for kw in ('usb', 'hdmi', 'rj45', 'rj11', 'ethernet', 'barrel',
                       'dc_jack', 'audio', 'jack', 'dsub', 'vga', 'sma',
                       'bnc', 'screw_terminal', 'phoenix', 'molex_minifit',
                       'power_entry', 'iec_60320'):
                if kw in combined:
                    is_external = True
                    break

            # F6: power-only-connector gate. If every net at this connector
            # is a power/ground rail (no signal lines), the IO-001 fix isn't
            # a board-level ferrite bead — a saturating ferrite on a tens-of-
            # amps DC input would burn. The right answer for power cabling is
            # a system-level common-mode choke or shielded cable with chassis
            # termination. Downgrade severity + reword the recommendation.
            #
            # The PCB analyzer strips per-pad geometry from output; the
            # consumer-visible field is `pad_nets`
            # ({pad_num: {net: name, pin: num}}) — same field IO-002 reads
            # at line 803. Reading `pads` (the parser-internal field) returns
            # [] and silently no-ops the gate. Verified against harness
            # fixtures Tropaion/ZigBee_SmartMeter_Reader and
            # diondokter/induction-heater.
            pad_nets = conn.get('pad_nets', {})
            all_pad_nets = [
                v.get('net', '') for v in pad_nets.values()
                if isinstance(v, dict) and v.get('net')
            ]
            power_only = (
                bool(all_pad_nets)
                and all(_is_power_or_ground(n) for n in all_pad_nets)
            )
            if power_only:
                severity = 'INFO'
                recommendation = (
                    f'{conn_ref} appears to be a power-only connector (all '
                    f'pins are power/ground rails). A board-level ferrite '
                    f'bead would saturate at typical power-supply currents. '
                    f'If radiated EMI is a concern on the cable, add a '
                    f'system-level common-mode choke or use shielded cable '
                    f'with chassis termination.'
                )
            else:
                severity = 'HIGH' if is_external else 'LOW'
                recommendation = _suggest_filtering(conn_ref, combined)
            findings.append(_make_finding(
                'io_filtering', severity, 'IO-001',
                title=f'No EMC filtering near {conn_ref}',
                description=(
                    f'Connector {conn_ref} ({conn_val}) has no ferrite bead, '
                    f'CM choke, or ESD protection within 25mm. Unfiltered I/O '
                    f'cables are the dominant source of radiated emissions — '
                    f'common-mode current as low as 5 µA can exceed FCC Class B.'
                ),
                components=[conn_ref],
                recommendation=recommendation,
                confidence='heuristic',
                fix_params={
                    'type': 'add_component',
                    'components': [{'type': 'ferrite_bead'}],
                    'basis': 'EMI filter on external I/O',
                },
            ))

    return findings


def check_connector_ground_pins(pcb: Dict,
                                schematic: Optional[Dict] = None) -> List[Dict]:
    """IO-002: Flag connectors with insufficient ground pins.

    High-speed connectors need adequate ground pins for return current
    and shielding. Rule of thumb: at least 1 ground pin per 4 signal pins,
    or at least 2 ground pins for connectors with >4 signal pins.

    Uses pad_nets from PCB footprint data to count GND vs signal pads.
    """
    findings = []
    footprints = pcb.get('footprints', [])
    connectors = _connector_refs(footprints)

    for conn in connectors:
        conn_ref = conn.get('reference', '')
        conn_val = conn.get('value', '')
        pad_nets = conn.get('pad_nets', {})

        if not pad_nets:
            continue

        gnd_count = 0
        sig_count = 0
        for pad_num, pad_data in pad_nets.items():
            net = pad_data.get('net', '') if isinstance(pad_data, dict) else ''
            if not net or net in ('', 'unconnected'):
                continue
            if _is_ground_net(net):
                gnd_count += 1
            elif not _is_power_or_ground(net):
                sig_count += 1

        if sig_count <= 2:
            continue  # Small connectors don't need multiple grounds

        # Rule: at least 1 GND per 4 signal pins, minimum 2 GND for >4 signals
        min_gnd = max(2, (sig_count + 3) // 4)

        if gnd_count < min_gnd:
            # Check if this is a high-speed connector
            is_hs = False
            combined = (conn_val + ' ' + conn.get('library', conn.get('lib_id', ''))).lower()
            for kw in ('usb', 'hdmi', 'ethernet', 'rj45', 'pcie', 'sata', 'lvds'):
                if kw in combined:
                    is_hs = True
                    break

            severity = 'MEDIUM' if is_hs else 'LOW'
            findings.append(_make_finding(
                'io_filtering', severity, 'IO-002',
                title=f'Insufficient ground pins on {conn_ref}',
                description=(
                    f'{conn_ref} ({conn_val}) has {gnd_count} ground pin(s) '
                    f'for {sig_count} signal pins. Recommended: at least '
                    f'{min_gnd} ground pins for adequate return current path '
                    f'and cable shielding.'
                ),
                components=[conn_ref],
                recommendation=(
                    f'Ensure {conn_ref} has sufficient ground pins. '
                    f'For high-speed interfaces, ground pins should be '
                    f'distributed among signal pins, not grouped at one end.'
                ),
                confidence='heuristic',
            ))

    return findings


# ---------------------------------------------------------------------------
# Category 4: Switching Regulator EMC
# ---------------------------------------------------------------------------

def check_switching_harmonics(schematic: Dict, standard: str = 'fcc-class-b') -> List[Dict]:
    """Check if switching regulator harmonics overlap with emission limit bands."""
    findings = []
    regulators = get_findings(schematic, Det.POWER_REGULATORS)

    for reg in regulators:
        topology = reg.get('topology', '').lower()
        if topology in ('ldo', 'linear'):
            continue  # LDOs don't switch

        ref = reg.get('ref', reg.get('reference', ''))
        val = reg.get('value', '')

        # Try to get switching frequency: prefer pre-computed field, fall back to local estimate
        sw_freq = reg.get('switching_frequency_hz')
        if sw_freq is None:
            sw_freq = _estimate_switching_freq(val)
        if sw_freq is None:
            sw_freq = _default_switching_freq(topology)
        if sw_freq is None:
            continue

        # Estimate rise time (technology-dependent, typically 5-20ns for modern parts)
        rise_time = 10e-9  # default 10ns
        duty_cycle = 0.5  # default

        # Try to estimate duty from Vin/Vout for buck
        vin = reg.get('input_voltage', None)
        vout = reg.get('vout_estimated', None)
        if topology == 'buck' and vin and vout and vin > 0:
            duty_cycle = max(0.1, min(0.9, vout / vin))

        f1, f2 = trapezoidal_corner_frequencies(duty_cycle, rise_time, sw_freq)

        # Check overlap with FCC bands
        bands = [
            ('30-88 MHz', 30e6, 88e6),
            ('88-216 MHz', 88e6, 216e6),
            ('216-960 MHz', 216e6, 960e6),
        ]

        for band_name, band_min, band_max in bands:
            harmonics = switching_harmonics_in_band(sw_freq, band_min, band_max)
            if harmonics:
                # Estimate amplitude of strongest harmonic in this band
                n_min = harmonics[0]
                amp = trapezoidal_harmonic_amplitude(
                    n_min, 12.0, duty_cycle, rise_time, sw_freq)

                # Spread-spectrum modulation reduces peak harmonic energy
                ss_detected = _has_spread_spectrum(val)
                if ss_detected:
                    amp *= 0.18  # ~-15 dB attenuation from frequency spreading

                severity = 'INFO'
                if len(harmonics) > 10 and n_min < 100:
                    severity = 'MEDIUM'
                if n_min < 30:
                    severity = 'HIGH'

                findings.append(_make_finding(
                    'switching_emc', severity, 'SW-001',
                    title=f'{ref} harmonics in {band_name} band',
                    description=(
                        f'{ref} ({val}) switching at {sw_freq/1e6:.1f} MHz has '
                        f'{len(harmonics)} harmonics in the {band_name} band '
                        f'(harmonics {harmonics[0]}-{harmonics[-1]}). '
                        f'Envelope rolloff at {f2/1e6:.0f} MHz (-40 dB/decade above).'
                        + (' Spread-spectrum modulation detected (~-15 dB).'
                           if ss_detected else '')
                    ),
                    components=[ref],
                    recommendation=(
                        f'Minimize switching loop area for {ref}. Place input '
                        f'cap as close as possible.'
                        + ('' if ss_detected else
                           ' Consider spread-spectrum modulation if available.')
                    ),
                    confidence='heuristic',
                ))

    return findings


def _default_switching_freq(topology: str) -> float | None:
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


def _has_spread_spectrum(value: str) -> bool:
    """Detect if a switching regulator has spread-spectrum modulation."""
    if not value:
        return False
    val = value.upper()
    ss_keywords = ('SSCG', 'SPREAD', 'DITHER', 'FHSS', 'JITTER',
                   '-SS', '_SS', '/SS')
    return any(kw in val for kw in ss_keywords)


# ---------------------------------------------------------------------------
# Category 5: Clock Routing Quality
# ---------------------------------------------------------------------------

def check_clock_routing(pcb: Dict, schematic: Optional[Dict] = None) -> List[Dict]:
    """Check clock signal routing quality for EMC."""
    findings = []
    layers = pcb.get('layers', [])
    footprints = pcb.get('footprints', [])
    net_lengths_map = _build_net_length_map(pcb)

    # Determine if stripline layers exist (inner signal layers between planes)
    copper_layers = [l for l in layers if l.get('type') in ('signal', 'power')]
    has_inner_layers = len(copper_layers) > 2

    # Identify clock nets from schematic
    clock_nets = set()
    if schematic:
        crystals = get_findings(schematic, Det.CRYSTAL_CIRCUITS)
        for xtal in crystals:
            # Crystal in/out nets are clock nets
            for pin in xtal.get('pins', []):
                net = pin.get('net', '')
                if net:
                    clock_nets.add(net)
        # Also check bus analysis for SPI clocks
        buses = schematic.get('design_analysis', {}).get('buses', {})
        for bus_type in ('spi', 'i2s'):
            for bus in buses.get(bus_type, []):
                for sig in bus.get('signals', []):
                    if _is_clock_net(sig.get('net', '')):
                        clock_nets.add(sig['net'])

    # Also find clock-like nets by name
    for net_name in net_lengths_map:
        if _is_clock_net(net_name):
            clock_nets.add(net_name)

    for net_name in clock_nets:
        nl = net_lengths_map.get(net_name, {})
        length_mm = nl.get('total_length_mm', nl.get('track_length_mm', 0))
        layer_dist = nl.get('layers', nl.get('layer_distribution', {}))

        if length_mm <= 0:
            continue

        # Check if clock is routed on outer layers
        outer_segs = 0
        total_segs = 0
        for lname, ldata in layer_dist.items():
            seg_count = ldata.get('segments', ldata) if isinstance(ldata, dict) else ldata
            if isinstance(seg_count, dict):
                seg_count = seg_count.get('segments', 1)
            total_segs += seg_count
            if lname in ('F.Cu', 'B.Cu'):
                outer_segs += seg_count

        outer_ratio = outer_segs / total_segs if total_segs > 0 else 0

        if has_inner_layers and outer_ratio > 0.5:
            findings.append(_make_finding(
                'clock_routing', 'MEDIUM', 'CK-001',
                title=f'Clock {net_name} on outer layer',
                description=(
                    f'Clock net {net_name} is {outer_ratio*100:.0f}% routed on '
                    f'outer layers (microstrip). Inner stripline layers provide '
                    f'better shielding from radiation.'
                ),
                nets=[net_name],
                recommendation='Route clock signals on inner layers (stripline) when possible.',
            ))

        # Check for excessively long clock traces
        if length_mm > 100:
            findings.append(_make_finding(
                'clock_routing', 'MEDIUM', 'CK-002',
                title=f'Long clock trace: {net_name}',
                description=(
                    f'Clock net {net_name} is {length_mm:.0f}mm long. '
                    f'Long clock traces act as antennas and radiate harmonics '
                    f'more effectively.'
                ),
                nets=[net_name],
                recommendation='Minimize clock trace length. Place clock source close to destination.',
                confidence='heuristic',
            ))

    return findings


def check_clock_near_connector(pcb: Dict,
                               schematic: Optional[Dict] = None,
                               net_id_map: Optional[Dict] = None) -> List[Dict]:
    """CK-003: Flag clock traces routed near external connectors.

    Clock harmonics can couple to cables via proximity, increasing
    radiated emissions. Checks if any clock net's trace segments pass
    within 10mm of an external connector.

    Requires --full mode for track segment coordinates.
    """
    # EQ-087: d = √(Δx²+Δy²) (clock trace midpoint to connector distance)
    findings = []
    tracks = pcb.get('tracks', {})
    segments = tracks.get('segments', [])
    if not segments:
        return findings

    footprints = pcb.get('footprints', [])
    connectors = _connector_refs(footprints)
    if not connectors:
        return findings

    # Build net ID → name map (reuse if provided)
    net_id_to_name = net_id_map if net_id_map is not None else _build_net_id_to_name(pcb)

    # Connector positions
    conn_positions = []
    for conn in connectors:
        cx = conn.get('x') or 0
        cy = conn.get('y') or 0
        conn_positions.append((conn.get('reference', ''), cx, cy))

    flagged_pairs = set()
    PROXIMITY_MM = 10.0

    for seg in segments:
        net_id = seg.get('net', 0)
        net_name = net_id_to_name.get(net_id, '') if isinstance(net_id, int) else str(net_id)

        if not _is_clock_net(net_name):
            continue

        mid_x = (seg.get('x1', 0) + seg.get('x2', 0)) / 2
        mid_y = (seg.get('y1', 0) + seg.get('y2', 0)) / 2

        for conn_ref, cx, cy in conn_positions:
            pair_key = (net_name, conn_ref)
            if pair_key in flagged_pairs:
                continue
            dist = math.sqrt((mid_x - cx)**2 + (mid_y - cy)**2)
            if dist < PROXIMITY_MM:
                flagged_pairs.add(pair_key)
                findings.append(_make_finding(
                    'clock_routing', 'MEDIUM', 'CK-003',
                    title=f'Clock {net_name} routed near connector {conn_ref}',
                    description=(
                        f'Clock net {net_name} passes within {dist:.1f}mm of '
                        f'connector {conn_ref}. Clock harmonics can couple '
                        f'to attached cables via proximity, increasing '
                        f'radiated emissions.'
                    ),
                    components=[conn_ref],
                    nets=[net_name],
                    recommendation=(
                        f'Route {net_name} away from {conn_ref}, or add '
                        f'ground guard traces between the clock and connector.'
                    ),
                ))

                if len(findings) > 10:
                    return findings

    return findings


def check_crystal_guard_ring(pcb: Dict, schematic: Optional[Dict] = None) -> List[Dict]:
    """Check for ground pour coverage near crystal/oscillator components."""
    findings = []
    if not schematic:
        return findings

    crystals = get_findings(schematic, Det.CRYSTAL_CIRCUITS)
    if not crystals:
        return findings

    footprints = pcb.get('footprints', [])
    zones = pcb.get('zones', [])

    # Build ref->position lookup from footprints
    fp_pos = {}
    for fp in footprints:
        ref = fp.get('reference', '')
        if ref:
            fp_pos[ref] = (fp.get('x', 0), fp.get('y', 0))

    # Find ground zones with bounding boxes
    gnd_zones = [z for z in zones if _is_ground_net(z.get('net_name', ''))]

    for xtal in crystals:
        ref = xtal.get('reference', '')
        if not ref or ref not in fp_pos:
            continue

        cx, cy = fp_pos[ref]

        # Check if any ground zone covers the crystal area (within 5mm)
        has_ground_pour = False
        for gz in gnd_zones:
            bbox = gz.get('filled_bbox') or gz.get('outline_bbox')
            if not bbox:
                continue
            # Handle both dict and list bbox formats
            if isinstance(bbox, dict):
                bx_min, by_min = bbox.get('min_x', 0), bbox.get('min_y', 0)
                bx_max, by_max = bbox.get('max_x', 0), bbox.get('max_y', 0)
            elif isinstance(bbox, list) and len(bbox) >= 4:
                bx_min, by_min, bx_max, by_max = bbox[0], bbox[1], bbox[2], bbox[3]
            else:
                continue
            if (bx_min - 5 <= cx <= bx_max + 5 and
                by_min - 5 <= cy <= by_max + 5):
                has_ground_pour = True
                break

        if not has_ground_pour:
            freq = xtal.get('frequency') or 0
            freq_str = f"{freq/1e6:.1f} MHz" if freq > 1e6 else f"{freq/1e3:.1f} kHz"
            findings.append(_make_finding(
                'clock_routing', 'MEDIUM', 'CK-004',
                title=f'No ground pour near crystal {ref}',
                description=(
                    f'Crystal {ref} ({freq_str}) has no ground zone within 5mm. '
                    f'A local ground pour under and around the crystal reduces '
                    f'parasitic coupling and improves frequency stability.'
                ),
                components=[ref],
                recommendation=(
                    f'Add a ground pour on the layer below {ref}, extending '
                    f'at least 3mm beyond the crystal footprint on all sides.'
                ),
                confidence='heuristic',
            ))

    return findings


# ---------------------------------------------------------------------------
# Category 6: Via Stitching
# ---------------------------------------------------------------------------

def check_via_stitching(pcb: Dict, schematic: Optional[Dict] = None) -> List[Dict]:
    """Check ground via stitching spacing against frequency requirements."""
    # EQ-043: spacing = √(area/count) vs λ/20 (via stitching check)
    findings = []
    vias = pcb.get('vias', {})
    stats = pcb.get('statistics', {})
    board_outline = pcb.get('board_outline', {})

    # Estimate highest frequency on the board
    highest_freq = 50e6  # default assumption: 50 MHz
    if schematic:
        crystals = get_findings(schematic, Det.CRYSTAL_CIRCUITS)
        for xtal in crystals:
            freq = xtal.get('frequency') or 0
            if isinstance(freq, (int, float)) and freq > highest_freq:
                highest_freq = freq
        # Also consider 3rd harmonic of clocks
        highest_freq *= 3

    # Via stitching spacing requirement
    required_spacing_mm = lambda_over_20(highest_freq) * 1000  # convert m to mm

    # Count ground stitching vias (prefer detailed list over total count)
    via_list = vias.get('vias', [])
    if via_list:
        # Build net ID → name mapping to resolve numeric via net IDs
        net_id_map = _build_net_id_to_name(pcb)
        gnd_via_count = 0
        for v in via_list:
            v_net = v.get('net', 0)
            if isinstance(v_net, str):
                net_name = v_net
            elif isinstance(v_net, int) and v_net in net_id_map:
                net_name = net_id_map[v_net]
            else:
                net_name = ''
            if _is_ground_net(net_name):
                gnd_via_count += 1
        via_count = gnd_via_count if gnd_via_count > 0 else len(via_list)
    else:
        via_count = vias.get('count', stats.get('via_count', 0))
    bbox = board_outline.get('bounding_box', None) or {}
    board_w = bbox.get('width', stats.get('board_width_mm', 50)) or 50
    board_h = bbox.get('height', stats.get('board_height_mm', 50)) or 50
    board_area = board_w * board_h  # mm²

    if board_area <= 0:
        return findings

    # Estimate average via-to-via spacing assuming uniform distribution
    if via_count > 1:
        avg_spacing = math.sqrt(board_area / via_count)
    else:
        avg_spacing = None  # Can't estimate

    if avg_spacing is None or avg_spacing > required_spacing_mm * 2:
        spacing_note = (f'~{avg_spacing:.0f}mm avg spacing'
                       if avg_spacing is not None else 'no vias detected')
        findings.append(_make_finding(
            'via_stitching', 'MEDIUM', 'VS-001',
            title='Via stitching may be insufficient',
            description=(
                f'Board has {via_count} vias across {board_area:.0f} mm² '
                f'({spacing_note}). For the highest frequency '
                f'on this board ({highest_freq/1e6:.0f} MHz), λ/20 stitching '
                f'requires ≤{required_spacing_mm:.0f}mm spacing.'
            ),
            recommendation=(
                f'Add ground stitching vias at ≤{required_spacing_mm:.0f}mm '
                f'intervals, especially at board edges and near connectors.'
            ),
            confidence='heuristic',
        ))

    return findings


# ---------------------------------------------------------------------------
# Category 7: Stackup Quality
# ---------------------------------------------------------------------------

def check_stackup(pcb: Dict) -> List[Dict]:
    """Check PCB stackup for EMC best practices."""
    findings = []
    setup = pcb.get('setup', {})
    stackup = setup.get('stackup', [])
    layers = pcb.get('layers', [])

    if not stackup:
        return findings

    # Build ordered list of copper layers with their dielectric thickness to neighbors
    copper_layers = []
    for i, layer in enumerate(stackup):
        if layer.get('type') == 'copper':
            copper_layers.append({
                'name': layer.get('name', f'layer_{i}'),
                'index': i,
                'thickness': _safe_float(layer.get('thickness'), 0.035),
            })

    if len(copper_layers) < 2:
        return findings

    # Check for adjacent signal layers without reference plane
    layer_types = pcb.get('layers', [])
    layer_type_map = {l['name']: l.get('type', 'signal') for l in layer_types}

    for i in range(len(copper_layers) - 1):
        l1 = copper_layers[i]
        l2 = copper_layers[i + 1]
        t1 = layer_type_map.get(l1['name'], 'signal')
        t2 = layer_type_map.get(l2['name'], 'signal')

        # Two adjacent signal layers with no ground/power between them.
        # F9: severity scales by copper-layer count — on a 2-layer board
        # the designer can't insert a reference plane in this revision
        # (the issue is a stackup choice, not a fixable defect), so demote
        # to info with a "consider 4-layer next revision" recommendation.
        # 3+ layers: designer has real reorder options, keep HIGH.
        if t1 == 'signal' and t2 == 'signal':
            two_layer = len(copper_layers) <= 2
            findings.append(_make_finding(
                'stackup', 'INFO' if two_layer else 'HIGH', 'SU-001',
                title=f'Adjacent signal layers: {l1["name"]}, {l2["name"]}',
                description=(
                    f'Signal layers {l1["name"]} and {l2["name"]} are adjacent '
                    f'without a reference plane between them. This causes high '
                    f'crosstalk and poor return path control for signals on both layers.'
                ),
                recommendation=(
                    'Consider a 4-layer stackup with internal reference planes '
                    'for the next revision if signal integrity or EMC issues arise.'
                    if two_layer else
                    'Reorder stackup to place a ground or power plane between '
                    'every pair of signal layers.'
                ),
            ))

    # Check ground plane proximity (dielectric thickness)
    for i, cl in enumerate(copper_layers):
        lt = layer_type_map.get(cl['name'], 'signal')
        if lt != 'signal':
            continue

        # Find nearest reference plane
        min_dielectric = float('inf')
        nearest_ref = None
        for j, rl in enumerate(copper_layers):
            rt = layer_type_map.get(rl['name'], 'signal')
            if rt in ('power', 'ground', 'mixed') or _is_ground_net(rl['name']):
                # Calculate dielectric thickness between layers
                # Sum dielectric layers between them in the stackup
                idx_min = min(cl['index'], rl['index'])
                idx_max = max(cl['index'], rl['index'])
                d_total = 0
                for k in range(idx_min + 1, idx_max):
                    if stackup[k].get('type') != 'copper':
                        d_total += _safe_float(stackup[k].get('thickness'))
                if d_total < min_dielectric:
                    min_dielectric = d_total
                    nearest_ref = rl['name']

        if min_dielectric > 0.3 and nearest_ref:
            findings.append(_make_finding(
                'stackup', 'LOW', 'SU-002',
                title=f'Signal layer {cl["name"]} far from reference plane',
                description=(
                    f'Signal layer {cl["name"]} is {min_dielectric:.2f}mm from '
                    f'nearest reference plane ({nearest_ref}). Tight coupling '
                    f'(0.1-0.2mm) reduces loop area and improves EMC.'
                ),
                recommendation='Consider stackup adjustment to reduce signal-to-reference spacing.',
            ))

    # Check for interplane capacitance
    for i in range(len(copper_layers) - 1):
        l1 = copper_layers[i]
        l2 = copper_layers[i + 1]
        t1 = layer_type_map.get(l1['name'], 'signal')
        t2 = layer_type_map.get(l2['name'], 'signal')

        if (t1 == 'power' and _is_ground_net(l2['name'])) or \
           (_is_ground_net(l1['name']) and t2 == 'power'):
            # Power/ground plane pair — check dielectric thickness
            idx_min = min(l1['index'], l2['index'])
            idx_max = max(l1['index'], l2['index'])
            d_total = 0
            epsilon_r = 4.4
            for k in range(idx_min + 1, idx_max):
                if stackup[k].get('type') != 'copper':
                    d_total += _safe_float(stackup[k].get('thickness'))
                    epsilon_r = _safe_float(stackup[k].get('epsilon_r'), 4.4)

            if d_total > 0:
                cap = interplane_capacitance_pf_per_cm2(d_total, epsilon_r)
                if d_total > 0.2:
                    findings.append(_make_finding(
                        'stackup', 'LOW', 'SU-003',
                        title='Power/ground planes spaced for low interplane capacitance',
                        description=(
                            f'Power/ground plane pair ({l1["name"]}/{l2["name"]}) '
                            f'has {d_total:.2f}mm dielectric ({cap:.0f} pF/cm²). '
                            f'Thin dielectric (0.1-0.15mm, ~26-39 pF/cm²) provides '
                            f'better high-frequency decoupling.'
                        ),
                        recommendation='Use thin prepreg between power/ground plane pairs.',
                    ))

    return findings


# ---------------------------------------------------------------------------
# Category 8: Emission Estimates (Informational)
# ---------------------------------------------------------------------------

def estimate_cavity_resonances(pcb: Dict) -> List[Dict]:
    """Calculate board cavity resonance frequencies."""
    findings = []
    stats = pcb.get('statistics', {})
    setup = pcb.get('setup', {})
    stackup = setup.get('stackup', [])

    board_w = stats.get('board_width_mm', 0) or 0
    board_h = stats.get('board_height_mm', 0) or 0

    if not board_w or not board_h or board_w <= 0 or board_h <= 0:
        return findings

    # Get average epsilon_r from stackup
    epsilon_r = 4.4
    for layer in stackup:
        er = layer.get('epsilon_r')
        if er is not None:
            try:
                er = float(er)
                if er > 1:
                    epsilon_r = er
                    break
            except (ValueError, TypeError):
                pass

    resonances = board_cavity_resonances(
        board_w / 1000, board_h / 1000, epsilon_r, max_freq_hz=3e9, max_modes=5)

    if resonances:
        first_5 = resonances[:5]
        mode_strs = [f'({r["mode"][0]},{r["mode"][1]}) at {r["freq_mhz"]:.0f} MHz'
                     for r in first_5]
        findings.append(_make_finding(
            'emission_estimate', 'INFO', 'EE-001',
            title='Board cavity resonance frequencies',
            description=(
                f'Board ({board_w:.0f}×{board_h:.0f}mm, εr={epsilon_r:.1f}) '
                f'cavity resonances: {"; ".join(mode_strs)}. '
                f'PDN impedance spikes at these frequencies. Ensure adequate '
                f'decoupling at and around these frequencies.'
            ),
            recommendation='Add decoupling capacitors with SRF near these frequencies.',
            confidence='heuristic',
        ))

    return findings


def estimate_switching_emissions(schematic: Dict,
                                 standard: str = 'fcc-class-b',
                                 spice_backend=None) -> List[Dict]:
    """Estimate switching regulator emissions relative to limits.

    # EQ-094: V_n = V_peak × 2/(nπ) × sin(nπD) (trapezoidal harmonic envelope)
    # Source: Ott "EMC Engineering" (Wiley, 2009) Section 7.3
    When spice_backend is available, runs transient FFT to get actual
    harmonic amplitudes and compares against the analytical envelope.
    """
    findings = []
    regulators = get_findings(schematic, Det.POWER_REGULATORS)

    for reg in regulators:
        topology = reg.get('topology', '').lower()
        if topology in ('ldo', 'linear'):
            continue

        ref = reg.get('ref', reg.get('reference', ''))
        val = reg.get('value', '')
        sw_freq = reg.get('switching_frequency_hz') or _estimate_switching_freq(val)
        if sw_freq is None:
            sw_freq = _default_switching_freq(topology)
        if sw_freq is None:
            continue

        # Generate harmonic spectrum
        v_peak = reg.get('input_voltage', 12.0) or 12.0
        duty_cycle = 0.5
        vout = reg.get('vout_estimated')
        if topology == 'buck' and vout and v_peak > 0:
            duty_cycle = max(0.1, min(0.9, vout / v_peak))

        f1, f2 = trapezoidal_corner_frequencies(duty_cycle, 10e-9, sw_freq)

        # SPICE FFT enhancement: get actual harmonic amplitudes
        fft_note = ''
        if spice_backend:
            try:
                from emc_spice import run_switching_fft
                ok, harmonics = run_switching_fft(
                    v_peak, duty_cycle, 10e-9, sw_freq,
                    spice_backend, n_harmonics=10, timeout=15)
                if ok and harmonics:
                    # Compare SPICE harmonics with envelope at a few points
                    fft_samples = []
                    for h in harmonics[:5]:
                        env_amp = trapezoidal_harmonic_amplitude(
                            h['harmonic'], v_peak, duty_cycle, 10e-9, sw_freq)
                        env_dbuv = 20 * math.log10(env_amp * 1e6) if env_amp > 0 else -999
                        fft_samples.append(
                            f'h{h["harmonic"]}={h["amplitude_dbuv"]:.0f}dBµV '
                            f'(envelope: {env_dbuv:.0f})')
                    fft_note = ' SPICE FFT: ' + ', '.join(fft_samples[:3]) + '.'
            except Exception:
                pass

        ss_note = (' Spread-spectrum modulation detected (~-15 dB peak reduction).'
                   if _has_spread_spectrum(val) else '')
        findings.append(_make_finding(
            'emission_estimate', 'INFO', 'EE-002',
            title=f'{ref} harmonic envelope',
            description=(
                f'{ref} ({val}) switching at {sw_freq/1e6:.2f} MHz, '
                f'duty ≈{duty_cycle*100:.0f}%. Harmonic envelope: '
                f'flat to {f1/1e6:.1f} MHz, -20 dB/dec to {f2/1e6:.0f} MHz, '
                f'-40 dB/dec above. '
                f'Harmonics extend into FCC test range starting at '
                f'{max(1, int(30e6/sw_freq))}th harmonic.'
                + fft_note + ss_note
            ),
            components=[ref],
            recommendation=(
                'Minimize the hot loop area (input cap → high-side switch → '
                'inductor → low-side switch → input cap). Every halving of '
                'loop area reduces emissions by 6 dB.'
            ),
            confidence='heuristic',
        ))

    return findings


def check_switching_node_area(pcb: Optional[Dict],
                              schematic: Optional[Dict],
                              net_id_map: Optional[Dict] = None) -> List[Dict]:
    """SW-002: Flag large switching node copper area.

    # EQ-095: A_track = Σ(width_mm × length_mm) (switching node copper area)
    # Source: Engineering heuristic — switching node area directly
    # correlates with radiated emissions (antenna effect)
    For switching regulators, the SW/PH/LX net should have minimal copper
    area — just enough to connect the IC pin to the inductor pad. Large
    copper on the switching node acts as an antenna for switching noise.

    Checks both zone copper area AND track copper area (width × length).
    Track area requires --full mode for segment coordinates.
    """
    findings = []
    if not schematic or not pcb:
        return findings

    regulators = get_findings(schematic, Det.POWER_REGULATORS)
    zones = pcb.get('zones', [])
    segments = pcb.get('tracks', {}).get('segments', [])

    # Build id→name and name→id maps for segment net matching
    id_to_name = net_id_map if net_id_map is not None else _build_net_id_to_name(pcb)
    name_to_id = {v: k for k, v in id_to_name.items()}

    for reg in regulators:
        sw_net = reg.get('sw_net')
        if not sw_net:
            continue
        topology = reg.get('topology', '').lower()
        if topology in ('ldo', 'linear'):
            continue

        ref = reg.get('ref', reg.get('reference', ''))
        val = reg.get('value', '')

        # Zone copper area on SW net
        zone_area = 0
        for zone in zones:
            if zone.get('net_name') != sw_net:
                continue
            a = zone.get('outline_area_mm2') or zone.get('filled_area_mm2') or 0
            if isinstance(a, (int, float)):
                zone_area += a

        # Track copper area on SW net (width × length per segment)
        track_area = 0
        sw_net_id = name_to_id.get(sw_net)
        if segments and sw_net_id is not None:
            for seg in segments:
                if seg.get('net') != sw_net_id:
                    continue
                w = seg.get('width', 0) or 0
                x1, y1 = seg.get('x1', 0), seg.get('y1', 0)
                x2, y2 = seg.get('x2', 0), seg.get('y2', 0)
                length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                track_area += w * length

        total_area = zone_area + track_area

        if total_area < 25:
            continue

        severity = 'HIGH' if total_area > 100 else 'MEDIUM'

        # Build description with breakdown
        parts = []
        if zone_area > 0:
            parts.append(f'{zone_area:.0f}mm² zone')
        if track_area > 0:
            parts.append(f'{track_area:.0f}mm² traces')
        area_desc = ' + '.join(parts) if len(parts) > 1 else parts[0] if parts else f'{total_area:.0f}mm²'

        findings.append(_make_finding(
            'switching_emc', severity, 'SW-002',
            title=f'Large switching node area for {ref}',
            description=(
                f'{ref} ({val}) switching node net {sw_net} has '
                f'{area_desc} ({total_area:.0f}mm² total). The SW node '
                f'should be minimal — large copper area acts as an antenna '
                f'for switching noise.'
            ),
            components=[ref],
            nets=[sw_net],
            recommendation=(
                f'Minimize copper on {sw_net}. Use only the trace/pad area '
                f'needed to connect {ref} SW pin to the inductor. '
                f'Remove any copper pour on the switching node net.'
            ),
            confidence='heuristic',
        ))

    return findings


def check_input_cap_loop_area(pcb: Optional[Dict],
                              schematic: Optional[Dict],
                              spice_backend=None) -> List[Dict]:
    """SW-003: Estimate hot loop area for switching regulators.

    The hot loop (input cap → IC → inductor → back) should be as small
    as possible. Large loops radiate switching noise. Uses component
    placement coordinates from PCB data to estimate the enclosed area.

    For integrated converters (most common), approximates as a triangle:
    input cap → IC → inductor.

    When SPICE is available, estimates radiated E-field from loop area ×
    switching current × frequency using dm_radiation_dbuv_m().
    """
    # EQ-088: A = polygon_area(cap, IC, inductor) (hot loop area estimation)
    findings = []
    if not schematic or not pcb:
        return findings

    regulators = get_findings(schematic, Det.POWER_REGULATORS)

    # Prefer pre-computed loop areas from PCB analyzer (enrichment 2.4)
    precomputed = pcb.get('switching_loop_areas', []) if pcb else []
    if precomputed:
        for loop in precomputed:
            area_mm2 = loop.get('area_mm2', 0)
            if area_mm2 < 25:
                continue  # Acceptable

            ref = loop.get('regulator_ref', '')
            val = loop.get('regulator_value', '')
            inductor_ref = loop.get('inductor_ref', '')
            cap_ref = loop.get('cap_ref', '')

            severity = 'HIGH' if area_mm2 > 100 else 'MEDIUM'

            desc = (
                f'{ref} ({val}) hot loop area ≈ {area_mm2:.0f}mm² '
                f'(triangle: {cap_ref} → {ref} → {inductor_ref}). '
                f'Recommended: <25mm² for low EMI.'
            )

            # SPICE radiation estimate
            spice_note = ''
            if spice_backend and area_mm2 > 25:
                reg_match = None
                for reg in regulators:
                    if reg.get('ref', reg.get('reference', '')) == ref:
                        reg_match = reg
                        break
                if reg_match:
                    sw_freq = (reg_match.get('switching_frequency_hz') or
                               _estimate_switching_freq(val) or
                               _default_switching_freq(reg_match.get('topology', '')))
                    if sw_freq:
                        area_m2 = area_mm2 * 1e-6
                        pdiss = reg_match.get('power_dissipation', {})
                        i_sw = pdiss.get('estimated_iout_A', 0.5)
                        e_dbuv = dm_radiation_dbuv_m(sw_freq, area_m2, i_sw, 3.0,
                                                      ground_plane=True)
                        limit = get_emission_limit(sw_freq, 'fcc-class-b')
                        if limit:
                            margin = limit[0] - e_dbuv
                            spice_note = (
                                f' Estimated radiation at {sw_freq/1e6:.1f}MHz: '
                                f'{e_dbuv:.0f} dBµV/m (limit: {limit[0]:.0f}, '
                                f'margin: {margin:.0f}dB).'
                            )

            findings.append(_make_finding(
                'switching_emc', severity, 'SW-003',
                title=f'Large hot loop for {ref}',
                description=desc + spice_note,
                components=[ref, inductor_ref, cap_ref],
                recommendation=(
                    f'Place {cap_ref}, {ref}, and {inductor_ref} in a tight triangle. '
                    f'Minimize trace length between them. Input cap should be adjacent '
                    f'to the IC with the inductor on the opposite side.'
                ),
                confidence='heuristic',
            ))
        return findings

    footprints = pcb.get('footprints', [])

    # Build position lookup
    fp_pos = {}
    for fp in footprints:
        ref = fp.get('reference', '')
        if ref:
            fp_pos[ref] = (fp.get('x') or 0, fp.get('y') or 0)

    for reg in regulators:
        topology = reg.get('topology', '').lower()
        if topology in ('ldo', 'linear', 'unknown', 'ic_with_internal_regulator'):
            continue

        ref = reg.get('ref', reg.get('reference', ''))
        val = reg.get('value', '')
        inductor_ref = reg.get('inductor')
        input_caps = reg.get('input_capacitors', [])

        if not inductor_ref or not input_caps:
            continue

        # Get positions
        ic_pos = fp_pos.get(ref)
        ind_pos = fp_pos.get(inductor_ref)
        cap_ref = input_caps[0].get('ref', '')
        cap_pos = fp_pos.get(cap_ref)

        if not ic_pos or not ind_pos or not cap_pos:
            continue
        if ic_pos == (0, 0) or ind_pos == (0, 0) or cap_pos == (0, 0):
            continue

        # Compute triangle area (input cap, IC, inductor)
        from emc_formulas import polygon_area
        area_mm2 = polygon_area([cap_pos, ic_pos, ind_pos])

        if area_mm2 < 25:
            continue  # Acceptable

        if area_mm2 > 100:
            severity = 'HIGH'
        else:
            severity = 'MEDIUM'

        desc = (
            f'{ref} ({val}) hot loop area ≈ {area_mm2:.0f}mm² '
            f'(triangle: {cap_ref} → {ref} → {inductor_ref}). '
            f'Recommended: <25mm² for low EMI.'
        )

        # SPICE enhancement: estimate radiated emission from loop
        spice_note = ''
        if spice_backend and area_mm2 > 25:
            sw_freq = reg.get('switching_frequency_hz') or _estimate_switching_freq(val) or _default_switching_freq(topology)
            if sw_freq:
                area_m2 = area_mm2 * 1e-6
                # Estimate switching current from power dissipation or default 0.5A
                pdiss = reg.get('power_dissipation', {})
                i_sw = pdiss.get('estimated_iout_A', 0.5)
                e_dbuv = dm_radiation_dbuv_m(sw_freq, area_m2, i_sw, 3.0, ground_plane=True)
                limit = get_emission_limit(sw_freq, 'fcc-class-b')
                if limit:
                    margin = limit[0] - e_dbuv
                    spice_note = (
                        f' Estimated radiation at {sw_freq/1e6:.1f}MHz: '
                        f'{e_dbuv:.0f} dBµV/m (limit: {limit[0]:.0f}, '
                        f'margin: {margin:.0f}dB).'
                    )

        findings.append(_make_finding(
            'switching_emc', severity, 'SW-003',
            title=f'Large hot loop for {ref}',
            description=desc + spice_note,
            components=[ref, inductor_ref, cap_ref],
            nets=[reg.get('sw_net', '')] if reg.get('sw_net') else [],
            recommendation=(
                f'Place {cap_ref}, {ref}, and {inductor_ref} in a tight triangle. '
                f'Minimize trace length between them. Input cap should be adjacent '
                f'to the IC with the inductor on the opposite side.'
            ),
            confidence='heuristic',
        ))

    return findings


# ---------------------------------------------------------------------------
# Shared helper: net length map
# ---------------------------------------------------------------------------

def _build_net_id_to_name(pcb: Dict) -> Dict[int, str]:
    """Build mapping from numeric net ID to net name.

    PCB analyzer emits ``nets: {str(id): name}`` and
    ``net_name_to_id: {name: int_id}``.  This helper handles the
    string-key JSON round-trip.
    """
    nets = pcb.get('nets', {})
    if not isinstance(nets, dict):
        return {}
    return {int(k): str(v) for k, v in nets.items()
            if v and str(k).isdigit()}


def _build_net_length_map(pcb: Dict) -> Dict[str, Dict]:
    """Normalize net_lengths (list or dict) into a dict keyed by net name."""
    raw = pcb.get('net_lengths', [])
    if isinstance(raw, dict):
        return raw
    result = {}
    if isinstance(raw, list):
        for entry in raw:
            name = entry.get('net', '')
            if name:
                result[name] = entry
    return result


def _get_stackup_dielectric_height(pcb: Dict, layer_name: str) -> Optional[float]:
    """Get dielectric thickness between a signal layer and its nearest reference plane."""
    stackup = pcb.get('setup', {}).get('stackup', [])
    if not stackup:
        return None
    # Find the layer index in stackup
    layer_idx = None
    for i, layer in enumerate(stackup):
        if layer.get('name') == layer_name and layer.get('type') == 'copper':
            layer_idx = i
            break
    if layer_idx is None:
        return None
    # Search adjacent dielectric layers
    for direction in (1, -1):
        idx = layer_idx + direction
        if 0 <= idx < len(stackup) and stackup[idx].get('type') != 'copper':
            t = stackup[idx].get('thickness')
            if t is not None:
                try:
                    return float(t)
                except (ValueError, TypeError):
                    pass
    return None


# ---------------------------------------------------------------------------
# Category 9: Differential Pair EMC
# ---------------------------------------------------------------------------

def check_diff_pair_skew(pcb: Optional[Dict],
                         schematic: Optional[Dict]) -> List[Dict]:
    """DP-001: Check intra-pair length mismatch / skew."""
    findings = []
    if not schematic or not pcb:
        return findings

    diff_pairs = schematic.get('design_analysis', {}).get('differential_pairs', [])
    if not diff_pairs:
        return findings

    net_map = _build_net_length_map(pcb)
    stackup = pcb.get('setup', {}).get('stackup', [])
    epsilon_r = 4.4
    for layer in stackup:
        er = layer.get('epsilon_r')
        if er is not None:
            try:
                er = float(er)
                if er > 1:
                    epsilon_r = er
                    break
            except (ValueError, TypeError):
                pass

    for pair in diff_pairs:
        pos_net = pair.get('positive', '')
        neg_net = pair.get('negative', '')
        protocol = pair.get('type', 'unknown')

        pos_data = net_map.get(pos_net, {})
        neg_data = net_map.get(neg_net, {})

        pos_len = pos_data.get('total_length_mm', pos_data.get('total_length', 0)) or 0
        neg_len = neg_data.get('total_length_mm', neg_data.get('total_length', 0)) or 0

        if pos_len <= 0 or neg_len <= 0:
            continue

        delta_mm = abs(pos_len - neg_len)
        skew = diff_pair_skew_ps(delta_mm, epsilon_r)
        proto_info = DIFF_PAIR_PROTOCOLS.get(protocol, {})
        max_skew = proto_info.get('max_skew_ps', 50)

        if skew <= max_skew * 0.5:
            continue  # Within comfortable margin

        if skew > max_skew:
            severity = 'HIGH'
            pct_over = (skew / max_skew - 1) * 100
            title = f'{protocol} diff pair skew exceeds limit'
            desc_extra = f'Exceeds {protocol} limit of {max_skew} ps by {pct_over:.0f}%.'
        else:
            severity = 'MEDIUM'
            title = f'{protocol} diff pair skew approaching limit'
            desc_extra = f'{protocol} limit is {max_skew} ps.'

        findings.append(_make_finding(
            'diff_pair', severity, 'DP-001',
            title=title,
            description=(
                f'Differential pair {pos_net}/{neg_net} has {delta_mm:.1f}mm '
                f'length mismatch ({skew:.1f} ps skew). {desc_extra}'
            ),
            components=pair.get('shared_ics', [])[:3],
            nets=[pos_net, neg_net],
            recommendation=(
                f'Match trace lengths to within {max_skew * 0.5:.0f} ps '
                f'({max_skew * 0.5 / propagation_delay_ps_per_mm(epsilon_r):.1f}mm). '
                f'Use length-matched serpentine routing.'
            ),
        ))

    return findings


def check_diff_pair_cm_radiation(pcb: Optional[Dict],
                                 schematic: Optional[Dict],
                                 standard: str = 'fcc-class-b') -> List[Dict]:
    """DP-002: Estimate common-mode radiation from diff pair skew."""
    # EQ-036: E_cm from V_cm and cable length using EQ-003
    findings = []
    if not schematic or not pcb:
        return findings

    diff_pairs = schematic.get('design_analysis', {}).get('differential_pairs', [])
    if not diff_pairs:
        return findings

    net_map = _build_net_length_map(pcb)
    epsilon_r = 4.4

    for pair in diff_pairs:
        pos_net = pair.get('positive', '')
        neg_net = pair.get('negative', '')
        protocol = pair.get('type', 'unknown')

        # Classify USB speed from MCU endpoint extraction
        usb_speed_resolved = None
        if protocol == 'USB':
            for ic_ref in pair.get('shared_ics', []):
                comp = next((c for c in (schematic or {}).get('components', [])
                             if c.get('reference') == ic_ref), None)
                if comp and comp.get('type') not in ('connector',):
                    mcu_mpn = comp.get('mpn') or comp.get('value', '')
                    mcu_feat = _get_mcu_features(mcu_mpn) if mcu_mpn else None
                    if mcu_feat and not mcu_feat.get('quality', {}).get('trusted', True):
                        mcu_feat = None   # deterministic detectors keep the v1.4 trust gate (v2.0 §3.A.1)
                    if mcu_feat:
                        usb_speed_resolved = mcu_feat.get('usb_speed')
                        break
            if usb_speed_resolved == 'HS':
                proto_info = DIFF_PAIR_PROTOCOLS.get('USB-HS')
            elif usb_speed_resolved == 'SS':
                proto_info = DIFF_PAIR_PROTOCOLS.get('USB3')
            else:
                proto_info = DIFF_PAIR_PROTOCOLS.get('USB-FS')
        else:
            proto_info = DIFF_PAIR_PROTOCOLS.get(protocol)
        if not proto_info:
            continue

        pos_len = (net_map.get(pos_net, {}).get('total_length_mm') or
                   net_map.get(pos_net, {}).get('total_length', 0)) or 0
        neg_len = (net_map.get(neg_net, {}).get('total_length_mm') or
                   net_map.get(neg_net, {}).get('total_length', 0)) or 0

        if pos_len <= 0 or neg_len <= 0:
            continue

        delta_mm = abs(pos_len - neg_len)
        if delta_mm < 0.1:
            continue

        skew = diff_pair_skew_ps(delta_mm, epsilon_r)
        rise_time_ps = proto_info['rise_time_ns'] * 1000
        v_cm = diff_pair_cm_voltage(proto_info['v_diff'], skew, rise_time_ps)

        if v_cm < 0.001:  # Less than 1mV — negligible
            continue

        # Estimate CM current (assume 150Ω cable impedance)
        i_cm = v_cm / 150.0

        # Estimate radiation at knee frequency
        f_knee = knee_frequency(proto_info['rise_time_ns'] * 1e-9)
        e_dbuv = cm_radiation_dbuv_m(f_knee, 1.0, i_cm, 3.0)

        limit = get_emission_limit(f_knee, standard)
        if not limit:
            continue
        limit_dbuv, limit_dist = limit

        # Normalize to measurement distance
        if limit_dist != 3.0:
            e_dbuv += 20 * math.log10(3.0 / limit_dist)

        margin = limit_dbuv - e_dbuv

        if margin < 6:
            if protocol == 'USB' and usb_speed_resolved not in ('HS', 'SS'):
                severity = 'INFO'
            else:
                severity = 'HIGH' if margin < 0 else 'MEDIUM'
            proto_label = f'USB-{usb_speed_resolved}' if protocol == 'USB' and usb_speed_resolved else protocol
            findings.append(_make_finding(
                'diff_pair', severity, 'DP-002',
                title=f'{proto_label} skew-induced CM radiation risk',
                description=(
                    f'{pos_net}/{neg_net}: {skew:.1f}ps skew generates '
                    f'{v_cm*1000:.1f}mV CM voltage → estimated '
                    f'{e_dbuv:.0f} dBµV/m at {f_knee/1e6:.0f} MHz '
                    f'(limit: {limit_dbuv:.0f} dBµV/m, margin: {margin:.0f} dB).'
                ),
                components=pair.get('shared_ics', [])[:3],
                nets=[pos_net, neg_net],
                recommendation=(
                    f'Reduce length mismatch or add common-mode filtering '
                    f'(CM choke) at the connector.'
                ),
                confidence='datasheet-backed',
            ))

    return findings


def check_diff_pair_reference_plane(pcb: Optional[Dict],
                                    schematic: Optional[Dict]) -> List[Dict]:
    """DP-003: Check for reference plane changes under diff pair routing."""
    findings = []
    if not schematic or not pcb:
        return findings

    diff_pairs = schematic.get('design_analysis', {}).get('differential_pairs', [])
    if not diff_pairs:
        return findings

    layer_trans = pcb.get('layer_transitions', [])
    if not layer_trans:
        return findings

    # Build map: net_name → transition info
    trans_map = {}
    for lt in layer_trans:
        net = lt.get('net', '')
        if net:
            trans_map[net] = lt

    for pair in diff_pairs:
        pos_net = pair.get('positive', '')
        neg_net = pair.get('negative', '')
        protocol = pair.get('type', 'unknown')

        for net_name in (pos_net, neg_net):
            trans = trans_map.get(net_name)
            if not trans:
                continue

            via_count = trans.get('via_count', 0)
            if via_count <= 0:
                continue

            layers = trans.get('copper_layers', [])
            if len(layers) <= 1:
                continue

            findings.append(_make_finding(
                'diff_pair', 'HIGH', 'DP-003',
                title=f'{protocol} diff pair changes layers',
                description=(
                    f'Net {net_name} (part of {protocol} diff pair) transitions '
                    f'across {len(layers)} layers ({", ".join(layers)}) with '
                    f'{via_count} via(s). Each layer transition is a potential '
                    f'DM-to-CM conversion point. Ensure stitching vias or '
                    f'decoupling caps at each transition.'
                ),
                components=pair.get('shared_ics', [])[:3],
                nets=[net_name],
                recommendation=(
                    'Add ground stitching vias within 2× dielectric height of '
                    'each signal via. Preferably route diff pairs on a single '
                    'layer to avoid layer transitions entirely.'
                ),
            ))

    return findings


def check_diff_pair_layer(pcb: Optional[Dict],
                          schematic: Optional[Dict]) -> List[Dict]:
    """DP-004: Check if diff pairs are routed on outer vs inner layers."""
    findings = []
    if not schematic or not pcb:
        return findings

    diff_pairs = schematic.get('design_analysis', {}).get('differential_pairs', [])
    if not diff_pairs:
        return findings

    layers = pcb.get('layers', [])
    copper_layers = [l for l in layers if l.get('type') in ('signal', 'power')]
    if len(copper_layers) <= 2:
        return findings  # 2-layer board — no inner layers available

    net_map = _build_net_length_map(pcb)

    for pair in diff_pairs:
        protocol = pair.get('type', 'unknown')
        for net_name in (pair.get('positive', ''), pair.get('negative', '')):
            nl = net_map.get(net_name, {})
            layer_dist = nl.get('layers', {})
            if not layer_dist:
                continue

            outer_segs = 0
            total_segs = 0
            for lname, ldata in layer_dist.items():
                seg_count = ldata.get('segments', ldata) if isinstance(ldata, dict) else ldata
                if isinstance(seg_count, dict):
                    seg_count = seg_count.get('segments', 1)
                total_segs += seg_count
                if lname in ('F.Cu', 'B.Cu'):
                    outer_segs += seg_count

            if total_segs <= 0:
                continue
            outer_ratio = outer_segs / total_segs

            if outer_ratio > 0.5:
                findings.append(_make_finding(
                    'diff_pair', 'MEDIUM', 'DP-004',
                    title=f'{protocol} diff pair on outer layer',
                    description=(
                        f'Net {net_name} ({protocol} diff pair) is '
                        f'{outer_ratio*100:.0f}% routed on outer layers. '
                        f'Inner stripline layers provide better shielding '
                        f'and lower radiation for high-speed differential pairs.'
                    ),
                    components=pair.get('shared_ics', [])[:3],
                    nets=[net_name],
                    recommendation=(
                        'Route differential pairs on inner stripline layers '
                        'when possible for reduced EMI.'
                    ),
                ))

    return findings


# ---------------------------------------------------------------------------
# Category 10: Board Edge Analysis
# ---------------------------------------------------------------------------

def _point_to_edges_min_distance(px: float, py: float,
                                 edges: List[Dict]) -> float:
    """Minimum distance from a point to any board edge segment."""
    min_dist = float('inf')
    for edge in edges:
        etype = edge.get('type', 'line')
        start = edge.get('start', [0, 0])
        end = edge.get('end', [0, 0])
        if etype == 'line' or etype == 'rect':
            d = point_to_segment_distance(px, py, start[0], start[1],
                                          end[0], end[1])
        elif etype == 'arc' and edge.get('mid'):
            # Approximate arc as two line segments through midpoint
            mid = edge['mid']
            d1 = point_to_segment_distance(px, py, start[0], start[1],
                                           mid[0], mid[1])
            d2 = point_to_segment_distance(px, py, mid[0], mid[1],
                                           end[0], end[1])
            d = min(d1, d2)
        else:
            d = point_to_segment_distance(px, py, start[0], start[1],
                                          end[0], end[1])
        if d < min_dist:
            min_dist = d
    return min_dist


def check_trace_near_board_edge(pcb: Dict,
                                schematic: Optional[Dict] = None,
                                net_id_map: Optional[Dict] = None) -> List[Dict]:
    """BE-001: Flag signal traces routed near board edges."""
    findings = []
    tracks = pcb.get('tracks', {})
    segments = tracks.get('segments', [])
    edges = pcb.get('board_outline', {}).get('edges', [])

    if not segments:
        return findings  # No segment data (--full not used)
    if not edges:
        return findings

    # Build net ID → name map for classification (reuse if provided)
    net_name_map = net_id_map if net_id_map is not None else _build_net_id_to_name(pcb)

    # Track which nets we've already flagged to avoid duplicates
    flagged_nets = set()
    near_edge_count = 0

    for seg in segments:
        layer = seg.get('layer', '')
        if layer not in ('F.Cu', 'B.Cu'):
            continue  # Inner layers are shielded

        net_id = seg.get('net', 0)
        net_name = net_name_map.get(net_id, '') if isinstance(net_id, int) else str(net_id)
        if _is_power_or_ground(net_name):
            continue

        if net_name in flagged_nets:
            continue

        # Get dielectric height for this layer
        h = _get_stackup_dielectric_height(pcb, layer) or 0.2  # default 0.2mm

        x1, y1 = seg.get('x1', 0), seg.get('y1', 0)
        x2, y2 = seg.get('x2', 0), seg.get('y2', 0)
        mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2

        dist = _point_to_edges_min_distance(mid_x, mid_y, edges)

        if dist < h:
            is_hs = _is_high_speed_net(net_name) or _is_clock_net(net_name)
            severity = 'HIGH' if is_hs else 'MEDIUM'
            near_edge_count += 1
            flagged_nets.add(net_name)

            if near_edge_count > 10:
                # Summarize rather than list every trace
                findings.append(_make_finding(
                    'board_edge', 'MEDIUM', 'BE-001',
                    title=f'{len(flagged_nets)} signals routed near board edge',
                    description=(
                        f'{len(flagged_nets)} signal nets are within {h:.2f}mm '
                        f'(dielectric height) of the board edge on outer layers. '
                        f'Traces near the edge lack full ground plane reference '
                        f'and radiate efficiently.'
                    ),
                    nets=sorted(flagged_nets)[:5],
                    recommendation='Keep signal traces at least 3× dielectric height from board edges.',
                ))
                return findings

            findings.append(_make_finding(
                'board_edge', severity, 'BE-001',
                title=f'Signal near board edge: {net_name}',
                description=(
                    f'Net {net_name} on {layer} is {dist:.2f}mm from the '
                    f'board edge (dielectric height: {h:.2f}mm). Traces near '
                    f'the edge lack full ground plane reference and act as '
                    f'slot antennas.'
                ),
                nets=[net_name],
                recommendation='Route signal away from board edge or add ground pour to the edge area.',
            ))

    return findings


def check_ground_pour_ring(pcb: Dict) -> List[Dict]:
    """BE-002: Check for ground pour coverage at board edges."""
    # EQ-039: Edge coverage from GND zone bounding box sampling
    findings = []
    edges = pcb.get('board_outline', {}).get('edges', [])
    zones = pcb.get('zones', [])

    if not edges:
        return findings

    gnd_zones = [z for z in zones if _is_ground_net(z.get('net_name', ''))]
    if not gnd_zones:
        return findings  # GP-002 already flags missing ground planes

    # Sample points along board edges
    uncovered_count = 0
    total_samples = 0
    SAMPLE_INTERVAL = 5.0  # mm

    for edge in edges:
        start = edge.get('start', [0, 0])
        end = edge.get('end', [0, 0])
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.sqrt(dx * dx + dy * dy)
        if length < 1.0:
            continue

        n_samples = max(2, int(length / SAMPLE_INTERVAL) + 1)
        for k in range(n_samples):
            t = k / max(n_samples - 1, 1)
            px = start[0] + t * dx
            py = start[1] + t * dy
            total_samples += 1

            # Check if any ground zone bbox covers this point (with 2mm margin)
            covered = False
            for gz in gnd_zones:
                bbox = gz.get('filled_bbox') or gz.get('outline_bbox')
                if not bbox:
                    continue
                if isinstance(bbox, dict):
                    bx_min = bbox.get('min_x', 0) - 2
                    by_min = bbox.get('min_y', 0) - 2
                    bx_max = bbox.get('max_x', 0) + 2
                    by_max = bbox.get('max_y', 0) + 2
                elif isinstance(bbox, list) and len(bbox) >= 4:
                    bx_min = bbox[0] - 2
                    by_min = bbox[1] - 2
                    bx_max = bbox[2] + 2
                    by_max = bbox[3] + 2
                else:
                    continue
                if bx_min <= px <= bx_max and by_min <= py <= by_max:
                    covered = True
                    break

            if not covered:
                uncovered_count += 1

    if total_samples > 0 and uncovered_count > 0:
        coverage_pct = (1 - uncovered_count / total_samples) * 100
        if coverage_pct < 90:
            findings.append(_make_finding(
                'board_edge', 'MEDIUM', 'BE-002',
                title='Incomplete ground pour at board edges',
                description=(
                    f'Ground pour covers ~{coverage_pct:.0f}% of the board '
                    f'perimeter ({uncovered_count}/{total_samples} sample points '
                    f'lack nearby ground zone). A continuous ground guard ring '
                    f'around the board perimeter reduces edge radiation. '
                    f'(Note: uses bounding box approximation.)'
                ),
                recommendation=(
                    'Add ground pour on outer layers extending to within 2mm '
                    'of all board edges, connected by stitching vias.'
                ),
            ))

    return findings


def check_connector_area_stitching(pcb: Dict,
                                   schematic: Optional[Dict] = None) -> List[Dict]:
    """BE-003: Check via stitching density near external connectors."""
    # EQ-034: Via density in connector proximity region
    findings = []
    footprints = pcb.get('footprints', [])
    connectors = _connector_refs(footprints)
    if not connectors:
        return findings

    # Get all via positions
    vias_data = pcb.get('vias', {})
    via_list = vias_data.get('vias', [])
    if not via_list:
        return findings  # Can't check without individual via positions

    # Get diff pair protocols for connector frequency estimation
    dp_nets = {}
    if schematic:
        for pair in schematic.get('design_analysis', {}).get('differential_pairs', []):
            for net in (pair.get('positive', ''), pair.get('negative', '')):
                if net:
                    dp_nets[net] = pair.get('type', 'unknown')

    for conn in connectors:
        cx = conn.get('x') or 0
        cy = conn.get('y') or 0
        conn_ref = conn.get('reference', '')
        conn_val = conn.get('value', '')

        # Estimate highest frequency at this connector
        highest_freq = 100e6  # default
        conn_nets = set()
        for pad in conn.get('pads', []):
            n = pad.get('net_name', '')
            if n and not _is_power_or_ground(n):
                conn_nets.add(n)
                proto = dp_nets.get(n)
                if proto:
                    proto_info = DIFF_PAIR_PROTOCOLS.get(proto, {})
                    tr = proto_info.get('rise_time_ns', 1.0) * 1e-9
                    f = knee_frequency(tr)
                    if f > highest_freq:
                        highest_freq = f

        # Count vias within 10mm
        radius = 10.0
        nearby_vias = 0
        for via in via_list:
            vx = via.get('x', 0)
            vy = via.get('y', 0)
            dist = math.sqrt((cx - vx)**2 + (cy - vy)**2)
            if dist <= radius:
                nearby_vias += 1

        if nearby_vias <= 0:
            continue

        # Check if via density is sufficient
        area_mm2 = math.pi * radius**2
        avg_spacing = math.sqrt(area_mm2 / nearby_vias) if nearby_vias > 0 else float('inf')
        required_spacing = lambda_over_20(highest_freq) * 1000  # m to mm

        if avg_spacing > required_spacing * 2:
            is_external = False
            combined = (conn_val + ' ' + conn.get('library', conn.get('lib_id', ''))).lower()
            for kw in ('usb', 'hdmi', 'rj45', 'ethernet', 'sma', 'bnc',
                       'barrel', 'dc_jack', 'audio', 'dsub'):
                if kw in combined:
                    is_external = True
                    break

            severity = 'HIGH' if is_external else 'MEDIUM'
            findings.append(_make_finding(
                'board_edge', severity, 'BE-003',
                title=f'Insufficient via stitching near {conn_ref}',
                description=(
                    f'{conn_ref} ({conn_val}) area has {nearby_vias} vias '
                    f'within 10mm (~{avg_spacing:.0f}mm avg spacing). '
                    f'For signals up to {highest_freq/1e6:.0f} MHz, '
                    f'λ/20 requires ≤{required_spacing:.0f}mm spacing.'
                ),
                components=[conn_ref],
                recommendation=(
                    f'Add ground stitching vias at ≤{required_spacing:.0f}mm '
                    f'intervals around {conn_ref}.'
                ),
            ))

    return findings


# ---------------------------------------------------------------------------
# Category 11: Crosstalk / Signal Integrity for EMC
# ---------------------------------------------------------------------------

def check_crosstalk_3h_rule(pcb: Dict,
                            schematic: Optional[Dict] = None) -> List[Dict]:
    """XT-001: Check trace spacing against the 3H crosstalk rule.

    For microstrip traces, spacing of 3× the dielectric height gives <3%
    near-end crosstalk. Closer spacing creates coupling that adds to
    emissions and can cause false signal transitions.

    Requires --proximity flag on PCB analyzer for trace_proximity data.

    Ref: Bogatin, "Signal and Power Integrity", Ch. 13.
         Howard Johnson, "High-Speed Digital Design", Ch. 5.
    """
    findings = []
    tp = pcb.get('trace_proximity', {})
    pairs = tp.get('proximity_pairs', [])
    if not pairs:
        return findings

    # Get dielectric height from stackup
    stackup = pcb.get('setup', {}).get('stackup', [])
    h_default = 0.2  # mm default
    for layer in stackup:
        if layer.get('type') in ('core', 'prepreg'):
            try:
                h = float(layer.get('thickness', 0.2))
                if h > 0:
                    h_default = h
                    break
            except (ValueError, TypeError):
                pass

    grid_size = tp.get('grid_size_mm', 0.5)
    threshold_3h = 3 * h_default  # 3H rule

    # Build the set of known differential pairs so we don't flag nets that
    # are *supposed* to be close-coupled (USB D+/D-, LVDS, Ethernet, CAN, etc.).
    # The schematic analyzer emits diff pairs at
    # `design_analysis.differential_pairs` (list of dicts with positive /
    # negative / type / ...).  A few legacy output paths also stashed them
    # elsewhere — check all three for safety.
    diff_pair_keys: set[tuple[str, str]] = set()
    if schematic:
        _design = schematic.get('design_analysis', {}) or {}
        _dp_sources = [
            _design.get('differential_pairs') or [],                              # current path
            (_design.get('buses', {}) or {}).get('differential_pairs') or [],     # legacy nested path
            schematic.get('differential_pairs') or [],                            # legacy top-level
        ]
        for _dps in _dp_sources:
            for _dp in _dps:
                if not isinstance(_dp, dict):
                    continue
                _pos = _dp.get('positive')
                _neg = _dp.get('negative')
                if _pos and _neg:
                    diff_pair_keys.add(tuple(sorted([_pos, _neg])))

    # Classify nets for aggressor/victim pairing
    flagged = set()

    for pair in pairs:
        net_a = pair.get('net_a', '')
        net_b = pair.get('net_b', '')
        coupling_mm = pair.get('approx_coupling_mm', 0)
        layer = pair.get('layer', '')
        shared_cells = pair.get('shared_cells', 0)

        # Grid spacing is the proxy for trace spacing
        # If two nets share grid cells, they're within grid_size of each other
        # This means spacing < grid_size, which for 0.5mm grid is tight
        if grid_size >= threshold_3h:
            continue  # Grid is too coarse to detect 3H violations

        # Minimum coupling length to flag (ignore very short parallel runs)
        if coupling_mm < 5.0:
            continue

        # Only flag on outer layers (inner stripline has lower crosstalk)
        if layer not in ('F.Cu', 'B.Cu', ''):
            continue

        pair_key = tuple(sorted([net_a, net_b]))
        if pair_key in flagged:
            continue
        flagged.add(pair_key)

        # Suppress: known differential pairs are supposed to run close-coupled.
        if pair_key in diff_pair_keys:
            continue

        # Check if aggressor-victim pair (clock/switching near analog/sensitive)
        a_is_aggressor = _is_clock_net(net_a) or _is_high_speed_net(net_a)
        b_is_aggressor = _is_clock_net(net_b) or _is_high_speed_net(net_b)
        a_is_sensitive = 'adc' in net_a.lower() or 'analog' in net_a.lower() or 'sense' in net_a.lower()
        b_is_sensitive = 'adc' in net_b.lower() or 'analog' in net_b.lower() or 'sense' in net_b.lower()

        aggressor_victim = (a_is_aggressor and b_is_sensitive) or (b_is_aggressor and a_is_sensitive)

        if aggressor_victim:
            severity = 'HIGH'
        elif a_is_aggressor or b_is_aggressor:
            severity = 'MEDIUM'
        else:
            severity = 'LOW'

        findings.append(_make_finding(
            'crosstalk', severity, 'XT-001',
            title=f'Close trace spacing: {net_a} / {net_b}',
            description=(
                f'Nets {net_a} and {net_b} run parallel for ~{coupling_mm:.0f}mm '
                f'on {layer or "outer layer"} within {grid_size}mm spacing '
                f'(3H rule requires ≥{threshold_3h:.1f}mm for <3% crosstalk, '
                f'H={h_default:.2f}mm). '
                + ('Aggressor-victim pair detected. ' if aggressor_victim else '')
            ),
            nets=[net_a, net_b],
            recommendation=(
                f'Increase spacing to ≥{threshold_3h:.1f}mm (3× dielectric height) '
                f'or insert a ground guard trace between them.'
            ),
            confidence='heuristic',
        ))

        if len(findings) > 15:
            findings.append(_make_finding(
                'crosstalk', 'MEDIUM', 'XT-001',
                title=f'{len(flagged)}+ trace pairs with close spacing (truncated)',
                description='Multiple net pairs violate the 3H spacing rule. Review trace spacing board-wide.',
                recommendation=f'Increase trace spacing to ≥{threshold_3h:.1f}mm on outer layers.',
                confidence='heuristic',
            ))
            break

    return findings


# ---------------------------------------------------------------------------
# Category 12: EMI Filter Verification
# ---------------------------------------------------------------------------

def check_emi_filter_effectiveness(pcb: Optional[Dict],
                                   schematic: Optional[Dict],
                                   spice_backend=None) -> List[Dict]:
    """EF-001: Verify EMI input filter cutoff vs switching frequency.

    For each switching regulator, check if there's an LC filter on the
    input rail with cutoff well below the switching frequency.
    When spice_backend is provided, simulates actual insertion loss.

    Ref: Paul, "Introduction to EMC", Ch. 9.
         Analog Devices, "Speed Up the Design of EMI Filters for SMPS".
    """
    # EQ-037: ratio = f_sw/f_cutoff; ratio >= 5 for adequate EMI filter
    findings = []
    if not schematic:
        return findings

    regulators = get_findings(schematic, Det.POWER_REGULATORS)
    lc_filters = get_findings(schematic, Det.LC_FILTERS)
    rc_filters = get_findings(schematic, Det.RC_FILTERS)

    if not regulators:
        return findings

    for reg in regulators:
        topology = reg.get('topology', '').lower()
        if topology in ('ldo', 'linear'):
            continue  # LDOs don't need EMI input filters

        ref = reg.get('ref', reg.get('reference', ''))
        val = reg.get('value', '')
        sw_freq = reg.get('switching_frequency_hz') or _estimate_switching_freq(val) or _default_switching_freq(topology)
        if not sw_freq:
            continue

        input_rail = reg.get('input_rail', '')

        # Look for an LC filter on the input rail
        # Match by shared nets between filter components and regulator input
        has_input_filter = False
        filter_fc = None

        for lc in lc_filters:
            # Check if the LC filter shares the input rail net
            inductor_ref = lc.get('inductor', '')
            lc_freq = lc.get('resonant_frequency', lc.get('resonant_hz', 0))
            if lc_freq and lc_freq > 0:
                # Check if this filter's frequency is in the right range
                # (well below switching frequency = good EMI filter)
                if lc_freq < sw_freq:
                    has_input_filter = True
                    filter_fc = lc_freq
                    break

        if not has_input_filter:
            # No input filter detected — INFO only (many designs rely on
            # cap-only filtering which we can't easily distinguish)
            continue

        # Check if filter cutoff is far enough below switching frequency
        ratio = sw_freq / filter_fc if filter_fc and filter_fc > 0 else 0

        if ratio < 5:
            findings.append(_make_finding(
                'emi_filter', 'MEDIUM', 'EF-001',
                title=f'EMI filter cutoff too close to {ref} switching frequency',
                description=(
                    f'{ref} ({val}) switching at {sw_freq/1e6:.2f} MHz has '
                    f'an input LC filter with fc={filter_fc/1e6:.2f} MHz '
                    f'(ratio f_sw/f_c = {ratio:.1f}×). Recommended: '
                    f'f_c should be ≤ f_sw/5 for adequate attenuation '
                    f'(-40 dB/decade rolloff).'
                ),
                components=[ref],
                nets=[input_rail] if input_rail else [],
                recommendation=(
                    f'Increase filter inductance or capacitance to lower '
                    f'cutoff to ≤{sw_freq/5/1e6:.2f} MHz.'
                ),
                confidence='heuristic',
            ))
        elif ratio >= 5:
            findings.append(_make_finding(
                'emi_filter', 'INFO', 'EF-002',
                title=f'EMI filter verified for {ref}',
                description=(
                    f'{ref} ({val}) switching at {sw_freq/1e6:.2f} MHz has '
                    f'input LC filter with fc={filter_fc/1e6:.2f} MHz '
                    f'(ratio {ratio:.0f}×). Provides ≥{20*math.log10(ratio)*2:.0f} dB '
                    f'attenuation at switching frequency.'
                ),
                components=[ref],
                nets=[input_rail] if input_rail else [],
                recommendation='Input EMI filter appears adequate.',
                confidence='heuristic',
            ))

    return findings


# ---------------------------------------------------------------------------
# Category 13: ESD Protection Path Analysis
# ---------------------------------------------------------------------------

def check_esd_protection_path(pcb: Dict,
                              schematic: Optional[Dict] = None) -> List[Dict]:
    """ES-001/ES-002: Analyze ESD protection placement quality.

    Beyond just checking if a TVS is near a connector (IO-001), this
    checks:
    - Distance from connector pad to TVS pad (trace length proxy)
    - TVS ground via count (ground path inductance)

    During an 8kV IEC 61000-4-2 strike, dI/dt = 30A/0.8ns = 37.5 GA/s.
    Each nH of inductance creates 37.5V of overshoot.

    Ref: TI SLVA680, "ESD Protection Layout Guide".
         ST AN5686, "PCB Layout Tips for ESD Protection".
    """
    # EQ-038: V_overshoot = L × dI/dt; dI/dt = 37.5 GA/s for 8kV ESD
    findings = []
    if not schematic or not pcb:
        return findings

    protection = get_findings(schematic, Det.PROTECTION_DEVICES)
    if not protection:
        return findings

    net_id_map = build_net_id_map(pcb)
    footprints = pcb.get('footprints', [])
    connectors = _connector_refs(footprints)
    if not connectors:
        return findings

    # Build footprint position lookup
    fp_positions = {}
    fp_pads = {}
    for fp in footprints:
        ref = fp.get('reference', '')
        fp_positions[ref] = (fp.get('x') or 0, fp.get('y') or 0)
        fp_pads[ref] = fp.get('pads', [])

    # Map protection devices to their positions
    prot_refs = set()
    prot_by_net = {}
    for pd in protection:
        ref = pd.get('reference', pd.get('ref', ''))
        prot_refs.add(ref)
        pnet = pd.get('protected_net', '')
        if pnet:
            prot_by_net.setdefault(pnet, []).append(pd)

    # Count ground vias near each protection device
    vias_data = pcb.get('vias', {})
    all_vias = vias_data.get('vias', [])

    for pd in protection:
        ref = pd.get('reference', pd.get('ref', ''))
        ptype = pd.get('type', '')
        if ptype not in ('tvs', 'esd', 'esd_ic', 'tvs_array', 'varistor'):
            continue

        if ref not in fp_positions:
            continue
        px, py = fp_positions[ref]

        # Check distance from nearest external connector
        min_conn_dist = float('inf')
        nearest_conn = ''
        for conn in connectors:
            cx = conn.get('x') or 0
            cy = conn.get('y') or 0
            d = math.sqrt((px - cx)**2 + (py - cy)**2)
            if d < min_conn_dist:
                min_conn_dist = d
                nearest_conn = conn.get('reference', '')

        if min_conn_dist > 50:
            continue  # Not near any connector

        # ES-001: Check distance (trace length proxy)
        if min_conn_dist > 15:
            # Estimate trace inductance from distance
            est_inductance_nh = min_conn_dist * 0.7  # ~0.7 nH/mm for microstrip
            est_overshoot_v = est_inductance_nh * 1e-9 * 37.5e9  # V = L × dI/dt
            findings.append(_make_finding(
                'esd_path', 'MEDIUM', 'ES-001',
                title=f'ESD device {ref} far from connector {nearest_conn}',
                description=(
                    f'{ref} ({ptype}) is {min_conn_dist:.1f}mm from {nearest_conn}. '
                    f'Estimated pre-TVS trace inductance: ~{est_inductance_nh:.0f}nH '
                    f'→ ~{est_overshoot_v:.0f}V overshoot during 8kV ESD strike '
                    f'(dI/dt = 37.5 GA/s). Recommended: <10mm.'
                ),
                components=[ref, nearest_conn],
                recommendation=(
                    f'Move {ref} closer to {nearest_conn}. The ESD current path '
                    f'from connector to TVS should be as short as possible.'
                ),
                confidence='heuristic',
                fix_params={
                    'type': 'add_protection',
                    'components': [{'type': 'tvs_diode'}],
                    'basis': 'ESD protection on external pins',
                },
            ))

        # ES-002: Check ground via count near TVS
        if all_vias:
            gnd_vias_near = 0
            for via in all_vias:
                vx = via.get('x', 0)
                vy = via.get('y', 0)
                d = math.sqrt((px - vx)**2 + (py - vy)**2)
                if d <= 3.0:  # Within 3mm of TVS
                    net_id = via.get('net')
                    if isinstance(net_id, int):
                        net_name = net_id_map.get(net_id, '')
                    else:
                        net_name = via.get('net_name', '') if isinstance(via.get('net_name'), str) else ''
                    if _is_ground_net(net_name):
                        gnd_vias_near += 1

            if gnd_vias_near == 0:
                findings.append(_make_finding(
                    'esd_path', 'HIGH', 'ES-002',
                    title=f'No ground via near ESD device {ref}',
                    description=(
                        f'{ref} ({ptype}) has no ground stitching via within 3mm. '
                        f'The TVS ground pad inductance is the most critical '
                        f'parasitic in ESD protection — each nH adds ~37.5V '
                        f'overshoot during an 8kV strike.'
                    ),
                    components=[ref],
                    recommendation=(
                        f'Add multiple ground vias directly adjacent to {ref} '
                        f'ground pad. Use fat, short traces to ground plane.'
                    ),
                    confidence='heuristic',
                ))
            elif gnd_vias_near == 1:
                findings.append(_make_finding(
                    'esd_path', 'LOW', 'ES-002',
                    title=f'Single ground via near ESD device {ref}',
                    description=(
                        f'{ref} ({ptype}) has {gnd_vias_near} ground via within 3mm. '
                        f'Multiple parallel vias reduce ground inductance. '
                        f'Two vias halve the inductance (~0.5nH → ~0.25nH).'
                    ),
                    components=[ref],
                    recommendation=f'Add a second ground via near {ref} for lower inductance.',
                    confidence='heuristic',
                ))

    return findings


# ---------------------------------------------------------------------------
# Thermal-EMC Interaction
# ---------------------------------------------------------------------------

# MLCC DC bias derating — imported from kicad_utils (single source of truth)
from kicad_utils import (classify_dielectric as _classify_dielectric,
                         estimate_dc_bias_derating as _estimate_dc_bias_derating)


def check_thermal_emc(pcb: Optional[Dict],
                      schematic: Optional[Dict]) -> List[Dict]:
    """TH-001/TH-002: Check for thermal effects that degrade EMC performance.

    TH-001: MLCC DC bias derating — flags caps that may have significantly
    reduced effective capacitance, shifting SRF and creating PDN gaps.

    TH-002: Ferrite bead near hot component — flags ferrite beads within
    10mm of switching regulators (thermal permeability degradation).

    Ref: Analog Devices, "Temperature and Voltage Variation of Ceramic
    Capacitors"; Murata DC bias characteristic documentation.
    """
    # EQ-042: DC bias derating lookup + ferrite µ thermal degradation
    findings = []
    if not schematic:
        return findings

    # TH-001: Cap DC bias derating on power rails
    regulators = get_findings(schematic, Det.POWER_REGULATORS)
    for reg in regulators:
        vout = reg.get('vout_estimated') or reg.get('estimated_vout')
        if not vout or vout <= 0:
            continue

        output_caps = reg.get('output_capacitors', [])
        ref_reg = reg.get('ref', reg.get('reference', ''))
        output_rail = reg.get('output_rail', '')

        for cap in output_caps:
            farads = cap.get('farads', 0)
            if not farads or farads <= 0:
                continue

            cap_ref = cap.get('ref', '?')
            package = cap.get('package')
            if not package:
                continue
            value_str = cap.get('value', '')

            # Use pre-computed derating from schematic analyzer when available
            remaining = cap.get('derating_factor')
            dielectric = cap.get('dielectric')
            if remaining is None:
                # Fallback: compute inline (EMC-only runs without schematic enrichment)
                if dielectric is None:
                    dielectric = _classify_dielectric(value_str)
                rated_v = cap.get('rated_voltage_V')
                if rated_v is None:
                    rated_v = 10.0
                    if vout <= 1.8:
                        rated_v = 6.3
                    elif vout <= 3.3:
                        rated_v = 6.3
                    elif vout <= 5.0:
                        rated_v = 10.0
                    elif vout <= 12.0:
                        rated_v = 25.0
                remaining = _estimate_dc_bias_derating(dielectric, package, vout / rated_v)

            effective_uf = farads * remaining * 1e6
            nominal_uf = farads * 1e6

            if remaining < 0.5:
                findings.append(_make_finding(
                    'thermal_emc', 'MEDIUM', 'TH-001',
                    title=f'{cap_ref} may have significant DC bias derating',
                    description=(
                        f'{cap_ref} ({nominal_uf:.1f}µF {dielectric} {package}) on '
                        f'{output_rail or ref_reg} {vout}V rail: estimated '
                        f'{remaining*100:.0f}% effective capacitance under DC bias '
                        f'({effective_uf:.1f}µF actual vs {nominal_uf:.1f}µF nominal). '
                        f'SRF shifts by {1/math.sqrt(remaining):.1f}× — may create '
                        f'gaps in decoupling coverage.'
                    ),
                    components=[cap_ref, ref_reg],
                    nets=[output_rail] if output_rail else [],
                    recommendation=(
                        f'Use a larger package (lower derating), higher voltage '
                        f'rating, or C0G/NP0 dielectric for critical decoupling. '
                        f'Alternatively, add more caps to compensate.'
                    ),
                    confidence='datasheet-backed',
                ))

    # TH-002: Ferrite bead near switching regulator (thermal degradation)
    if pcb:
        footprints = pcb.get('footprints', [])

        # Find switching regulator positions
        reg_positions = []
        for reg in regulators:
            if reg.get('topology', '').lower() in ('ldo', 'linear'):
                continue
            ref = reg.get('ref', reg.get('reference', ''))
            for fp in footprints:
                if fp.get('reference') == ref:
                    reg_positions.append({
                        'ref': ref,
                        'x': fp.get('x') or 0,
                        'y': fp.get('y') or 0,
                    })
                    break

        # Find ferrite beads
        for fp in footprints:
            ref = fp.get('reference', '')
            # KH-326: coerce malformed upstream value (rare parser edge case
            # where fp_text value has no text body) to empty string.
            _raw_val = fp.get('value', '')
            val = _raw_val.lower() if isinstance(_raw_val, str) else ''
            _raw_lib = fp.get('library', fp.get('lib_id', ''))
            lib = _raw_lib.lower() if isinstance(_raw_lib, str) else ''
            is_ferrite = ref.startswith('FB') or ('ferrite' in val) or ('bead' in val) or ('ferrite' in lib)
            if not is_ferrite:
                continue

            fx = fp.get('x') or 0
            fy = fp.get('y') or 0

            for reg_pos in reg_positions:
                dist = math.sqrt((fx - reg_pos['x'])**2 + (fy - reg_pos['y'])**2)
                if dist <= 10.0:
                    findings.append(_make_finding(
                        'thermal_emc', 'LOW', 'TH-002',
                        title=f'Ferrite {ref} near switching regulator {reg_pos["ref"]}',
                        description=(
                            f'{ref} ({fp.get("value","")}) is {dist:.1f}mm from '
                            f'switching regulator {reg_pos["ref"]}. Ferrite '
                            f'permeability decreases with temperature — if the '
                            f'regulator runs hot, the ferrite impedance may '
                            f'drop 30-50% above 85°C, reducing filtering.'
                        ),
                        components=[ref, reg_pos['ref']],
                        recommendation=(
                            'Verify ferrite bead thermal rating. Consider '
                            'relocating away from heat source or using a '
                            'higher-temperature-rated ferrite.'
                        ),
                        confidence='datasheet-backed',
                    ))
                    break  # One finding per ferrite

    return findings


# ---------------------------------------------------------------------------
# Shielding / Enclosure Advisory
# ---------------------------------------------------------------------------

def check_shielding_advisory(pcb: Dict,
                             schematic: Optional[Dict] = None,
                             standard: str = 'fcc-class-b') -> List[Dict]:
    """SH-001: Advisory on connector aperture slot antenna frequencies.

    Calculates the frequency at which each connector cutout acts as a
    resonant slot antenna (f = c / 2L). If this coincides with a known
    emission source, the connector becomes an efficient radiator.

    SH-002: Estimate minimum shielding effectiveness needed.

    Ref: Ott, "EMC Engineering", Ch. 6 — aperture theory.
    """
    findings = []
    stats = pcb.get('statistics', {})
    footprints = pcb.get('footprints', [])
    connectors = _connector_refs(footprints)

    if not connectors:
        return findings

    # Collect known emission frequencies
    emission_freqs = []
    if schematic:
        for xtal in get_findings(schematic, Det.CRYSTAL_CIRCUITS):
            f = xtal.get('frequency') or 0
            if isinstance(f, (int, float)) and f > 0:
                emission_freqs.append(f)
                emission_freqs.append(f * 2)  # 2nd harmonic
                emission_freqs.append(f * 3)  # 3rd harmonic

        for reg in get_findings(schematic, Det.POWER_REGULATORS):
            if reg.get('topology', '').lower() in ('ldo', 'linear'):
                continue
            sw = reg.get('switching_frequency_hz') or _estimate_switching_freq(reg.get('value', '')) or _default_switching_freq(reg.get('topology', ''))
            if sw:
                # Add harmonics that fall in EMC test range
                for n in range(1, 20):
                    h = sw * n
                    if h > 30e6:
                        emission_freqs.append(h)
                    if h > 1e9:
                        break

    # Common connector sizes (approximate aperture dimensions in mm)
    # USB-A: ~12mm, USB-C: ~9mm, RJ45: ~16mm, HDMI: ~15mm, barrel: ~8mm
    connector_sizes = {
        'usb': 12, 'usb_c': 9, 'usb-c': 9, 'type_c': 9, 'type-c': 9,
        'rj45': 16, 'rj11': 12, 'ethernet': 16,
        'hdmi': 15, 'vga': 20, 'dsub': 25, 'db9': 18, 'db25': 40,
        'sma': 8, 'bnc': 12, 'barrel': 8, 'dc_jack': 10,
        'audio': 8, 'jack': 8,
    }

    for conn in connectors:
        conn_ref = conn.get('reference', '')
        conn_val = conn.get('value', '')
        combined = (conn_val + ' ' + conn.get('library', conn.get('lib_id', ''))).lower()

        # Estimate aperture size
        aperture_mm = 12  # default
        for kw, size in connector_sizes.items():
            if kw in combined:
                aperture_mm = size
                break

        # Calculate slot resonance: f = c / (2 × L)
        aperture_m = aperture_mm / 1000
        f_slot = 3e8 / (2 * aperture_m)  # Hz

        # Check if any emission frequency is near the slot resonance (within 20%)
        coincidence = False
        coincident_freqs = []
        for ef in emission_freqs:
            if 0.8 * f_slot <= ef <= 1.2 * f_slot:
                coincidence = True
                coincident_freqs.append(ef)

        if coincidence:
            freq_strs = [f'{f/1e6:.0f} MHz' for f in coincident_freqs[:3]]
            findings.append(_make_finding(
                'shielding', 'MEDIUM', 'SH-001',
                title=f'{conn_ref} aperture resonates near emission source',
                description=(
                    f'{conn_ref} ({conn_val}) has ~{aperture_mm}mm aperture → '
                    f'slot resonance at {f_slot/1e9:.1f} GHz. Board emission '
                    f'sources at {", ".join(freq_strs)} are near this resonance. '
                    f'The connector cutout may act as an efficient radiator '
                    f'at these frequencies.'
                ),
                components=[conn_ref],
                recommendation=(
                    'Ensure the enclosure provides adequate shielding around '
                    'this connector. Consider a shielded connector variant '
                    'or adding absorber material.'
                ),
                confidence='heuristic',
            ))
        # Non-coincident connectors: no finding (reduces noise)

    return findings


# ---------------------------------------------------------------------------
# PDN Impedance Analysis
# ---------------------------------------------------------------------------

def check_pdn_impedance(pcb: Optional[Dict],
                        schematic: Optional[Dict],
                        spice_backend=None) -> List[Dict]:
    """PD-001/PD-002: Analyze decoupling network impedance per power rail.

    For each power regulator with detected output capacitors, model the
    parallel impedance of the decoupling network, compute target impedance,
    and flag anti-resonance peaks that exceed the target.

    When spice_backend is provided, uses SPICE AC analysis for more accurate
    impedance sweep (captures phase interactions). Falls back to analytical.
    """
    # EQ-041: Z_pdn(f) vs Z_target = V×ripple%/(0.5×I_transient)
    findings = []
    if not schematic:
        return findings

    regulators = get_findings(schematic, Det.POWER_REGULATORS)
    if not regulators:
        return findings

    # Get interplane capacitance from PCB stackup
    plane_cap_f = 0
    if pcb:
        setup = pcb.get('setup', {})
        stackup = setup.get('stackup', [])
        # Find tightest power/ground plane pair
        for i in range(len(stackup) - 1):
            l1 = stackup[i]
            l2 = stackup[i + 1] if i + 1 < len(stackup) else {}
            # Look for adjacent copper layers (potential plane pair)
            if l1.get('type') == 'copper' and l2.get('type') != 'copper':
                # Check the next copper layer after this dielectric
                for j in range(i + 2, len(stackup)):
                    if stackup[j].get('type') == 'copper':
                        d_mm = 0
                        er = 4.4
                        for k in range(i + 1, j):
                            if stackup[k].get('type') != 'copper':
                                try:
                                    d_mm += float(stackup[k].get('thickness', 0))
                                    er_val = stackup[k].get('epsilon_r')
                                    if er_val:
                                        er = float(er_val)
                                except (ValueError, TypeError):
                                    pass
                        if d_mm > 0 and d_mm < 0.3:
                            # Estimate board area from stats
                            stats = pcb.get('statistics', {})
                            w = (stats.get('board_width_mm') or 50)
                            h = (stats.get('board_height_mm') or 50)
                            area_cm2 = (w * h) / 100
                            c_pf_per_cm2 = interplane_capacitance_pf_per_cm2(d_mm, er)
                            plane_cap_f = c_pf_per_cm2 * area_cm2 * 1e-12  # Convert pF to F
                        break

    for reg in regulators:
        ref = reg.get('ref', reg.get('reference', ''))
        val = reg.get('value', '')
        vout = reg.get('vout_estimated') or reg.get('estimated_vout')
        output_rail = reg.get('output_rail', '')
        output_caps = reg.get('output_capacitors', [])

        if not output_caps or not vout:
            continue

        # Build cap models for PDN sweep
        cap_models = []
        for cap in output_caps:
            farads = cap.get('farads', 0)
            if not farads or farads <= 0:
                continue
            package = cap.get('package')
            if not package:
                # No package data — skip package-dependent analysis
                continue
            esr = cap.get('esr_ohm') or estimate_esr(package)
            esl = cap.get('esl_h') or estimate_esl(package)
            cap_models.append({
                'ref': cap.get('ref', '?'),
                'farads': farads,
                'esr_ohm': esr,
                'esl_h': esl,
                'package': package,
            })

        if not cap_models:
            continue

        # Estimate transient current (heuristic from regulator type)
        i_transient = 0.5  # default 500mA
        pdiss = reg.get('power_dissipation', {})
        i_out = pdiss.get('estimated_iout_A', 0.5)
        if i_out and i_out > 0:
            i_transient = min(i_out * 2, 5.0)  # Up to 2× steady-state

        z_target = pdn_target_impedance(vout, ripple_pct=5.0,
                                        i_transient_a=i_transient)

        # Sweep impedance — use SPICE if available, otherwise analytical
        sweep = None
        spice_verified = False
        if spice_backend and len(cap_models) >= 2:
            try:
                from emc_spice import run_pdn_spice
                ok, spice_sweep = run_pdn_spice(
                    cap_models, plane_cap_f, spice_backend,
                    freq_start=1e3, freq_stop=1e9)
                if ok and spice_sweep:
                    sweep = spice_sweep
                    spice_verified = True
            except Exception:
                pass
        if sweep is None:
            sweep = pdn_impedance_sweep(cap_models, plane_cap_f=plane_cap_f,
                                        freq_start=1e3, freq_stop=1e9)

        method_note = ' (SPICE-verified)' if spice_verified else ' (analytical)'

        # Find anti-resonances
        peaks = find_anti_resonances(sweep, z_target=z_target)
        exceeding = [p for p in peaks if p.get('exceeds_target')]

        if exceeding:
            peak_strs = [f'{p["freq_mhz"]:.1f} MHz ({p["impedance_ohm"]:.2f}Ω)'
                         for p in exceeding[:3]]
            findings.append(_make_finding(
                'pdn', 'HIGH', 'PD-001',
                title=f'{output_rail or ref} PDN anti-resonance exceeds target',
                description=(
                    f'{ref} ({val}) {output_rail} rail{method_note}: target impedance '
                    f'{z_target:.3f}Ω (Vout={vout}V, 5% ripple, '
                    f'{i_transient:.1f}A transient). '
                    f'Anti-resonance peak(s) exceed target at: '
                    f'{", ".join(peak_strs)}. '
                    f'Decoupling: {len(cap_models)} caps '
                    f'({", ".join(c["ref"] + " " + str(c["farads"]*1e6) + "µF" for c in cap_models[:4])}).'
                ),
                components=[ref] + [c['ref'] for c in cap_models[:3]],
                nets=[output_rail] if output_rail else [],
                recommendation=_suggest_pdn_cap(
                    exceeding[0], cap_models, plane_cap_f, z_target,
                    spice_backend, sweep_before=sweep),
                confidence='datasheet-backed' if spice_verified else 'heuristic',
                spice_verified=spice_verified,
                rail=output_rail,
                target_impedance_ohm=round(z_target, 4),
                vout_v=vout,
                transient_amps=round(i_transient, 3),
                method='spice' if spice_verified else 'analytical',
                peak_frequency_hz=round(exceeding[0]['freq_mhz'] * 1e6),
                peak_impedance_ohm=round(exceeding[0]['impedance_ohm'], 4),
                exceeding_peaks=[
                    {'frequency_hz': round(p['freq_mhz'] * 1e6),
                     'impedance_ohm': round(p['impedance_ohm'], 4)}
                    for p in exceeding
                ],
                decoupling_cap_count=len(cap_models),
            ))
        elif peaks:
            # Peaks exist but don't exceed target — INFO
            peak_strs = [f'{p["freq_mhz"]:.1f} MHz ({p["impedance_ohm"]:.3f}Ω)'
                         for p in peaks[:3]]
            findings.append(_make_finding(
                'pdn', 'INFO', 'PD-002',
                title=f'{output_rail or ref} PDN anti-resonances within target',
                description=(
                    f'{ref} ({val}) {output_rail} rail: target impedance '
                    f'{z_target:.3f}Ω. Anti-resonance peaks at: '
                    f'{", ".join(peak_strs)} — all within target. '
                    f'{len(cap_models)} decoupling caps.'
                ),
                components=[ref],
                nets=[output_rail] if output_rail else [],
                recommendation='PDN impedance is within target. No action needed.',
                confidence='datasheet-backed' if spice_verified else 'heuristic',
                spice_verified=spice_verified,
                rail=output_rail,
                target_impedance_ohm=round(z_target, 4),
                method='spice' if spice_verified else 'analytical',
                peaks=[
                    {'frequency_hz': round(p['freq_mhz'] * 1e6),
                     'impedance_ohm': round(p['impedance_ohm'], 4)}
                    for p in peaks
                ],
                decoupling_cap_count=len(cap_models),
            ))

    return findings


def check_pdn_distributed(pcb: Optional[Dict],
                          schematic: Optional[Dict],
                          spice_backend=None) -> List[Dict]:
    """PD-003/PD-004: Full-board PDN analysis with trace parasitics and cross-rail coupling.

    # EQ-096: I_reflected = P_downstream / V_upstream (reflected transient current)
    # Source: Novak "Power Distribution Network Design Methodologies" (IPC, 2008) Ch. 6
    PD-003: Distributed rail impedance at IC load point exceeds target.
           The impedance seen by an IC is higher than at the regulator output
           due to trace R+L between them. Local decoupling caps help but may
           introduce new anti-resonances.

    PD-004: Upstream PDN sees reflected transient from downstream switching
           regulator. A buck converter drawing pulsed current at its switching
           frequency creates ripple on the input rail that affects all other
           loads sharing that rail.

    Ref: Bogatin, "Signal and Power Integrity — Simplified" Ch. 10-12;
         Smith, "Decoupling Capacitor Calculations for ASICs";
         Basso, "Switch-Mode Power Supplies" (McGraw-Hill).
    """
    findings = []
    if not schematic:
        return findings

    regulators = get_findings(schematic, Det.POWER_REGULATORS)
    if not regulators:
        return findings

    power_budget = schematic.get('power_budget', {})
    decoupling = get_findings(schematic, Det.DECOUPLING)

    # Build and enrich power tree
    tree = build_power_tree(regulators, power_budget, decoupling)
    if not tree:
        return findings

    if pcb:
        enrich_power_tree_with_pcb(tree, pcb)

    # Interplane capacitance (reuse same logic as check_pdn_impedance)
    plane_cap_f = 0
    if pcb:
        setup = pcb.get('setup', {})
        stackup = setup.get('stackup', [])
        if stackup:
            stats = pcb.get('statistics', {})
            w = stats.get('board_width_mm', 0)
            h = stats.get('board_height_mm', 0)
            board_area_cm2 = (w * h) / 100.0 if w and h else 0
            # Find tightest power/ground plane pair
            for i in range(len(stackup) - 1):
                layer = stackup[i]
                if not isinstance(layer, dict):
                    continue
                if layer.get('type') not in ('core', 'prepreg'):
                    continue
                try:
                    d_mm = float(layer.get('thickness', 0))
                    er = float(layer.get('epsilon_r', 4.4))
                except (ValueError, TypeError):
                    continue
                if 0 < d_mm < 0.3 and board_area_cm2 > 0:
                    cpf = interplane_capacitance_pf_per_cm2(d_mm, er)
                    plane_cap_f = max(plane_cap_f, cpf * board_area_cm2 * 1e-12)

    # --- PD-003: Distributed rail impedance at IC load point ---
    for rail_name, node in tree.items():
        if not node.get('load_ics'):
            continue
        if not node.get('output_caps'):
            continue

        r_trace = node.get('trace_r_total_ohm', 0)
        l_trace = node.get('trace_l_total_h', 0)

        # Only fire PD-003 if we have meaningful trace parasitics
        # (otherwise PD-001 already covers this rail)
        if r_trace <= 0.001 and l_trace <= 0.1e-9:
            continue

        vout = node['voltage']
        total_load_mA = node['total_load_mA']
        i_transient = min(total_load_mA / 1000.0 * 2, 5.0)
        if i_transient <= 0:
            i_transient = 0.5

        z_target = pdn_target_impedance(vout, ripple_pct=5.0,
                                        i_transient_a=i_transient)

        # Run distributed sweep
        sweep_result = distributed_pdn_impedance_sweep(
            node, plane_cap_f=plane_cap_f)

        ic_sweep = sweep_result.get('sweep_at_worst_ic', [])
        worst_ic = sweep_result.get('worst_ic_ref', '')

        # Check IC sweep: anti-resonance peaks OR minimum impedance above target
        peaks = find_anti_resonances(ic_sweep, z_target=z_target)
        exceeding = [p for p in peaks if p.get('exceeds_target')]

        # Also check if the minimum impedance at IC exceeds target
        # (covers the case of undersized decoupling where there are no
        # anti-resonance peaks but the entire curve is above target)
        z_min_at_ic = min((pt['impedance_ohm'] for pt in ic_sweep),
                          default=float('inf'))
        z_min_at_reg = min((pt['impedance_ohm'] for pt in
                            sweep_result.get('sweep_at_regulator', [])),
                           default=float('inf'))

        # PD-003 fires if: (a) anti-resonance peaks exceed target, OR
        # (b) minimum IC impedance exceeds target AND is meaningfully
        # worse than at the regulator (trace parasitics are the cause)
        trace_impact = z_min_at_ic > z_min_at_reg * 1.2  # 20% worse

        if exceeding or (z_min_at_ic > z_target and trace_impact):
            reg_ref = node['regulator']['ref']
            r_note = f'Trace R={r_trace * 1000:.1f}mΩ'
            l_note = f'L={l_trace * 1e9:.1f}nH'

            if exceeding:
                peak_strs = [f'{p["freq_mhz"]:.1f}MHz ({p["impedance_ohm"]:.3f}Ω)'
                             for p in exceeding[:3]]
                detail = (
                    f'Anti-resonance peak(s) exceed target at IC: '
                    f'{", ".join(peak_strs)}.')
            else:
                detail = (
                    f'Minimum impedance at IC is {z_min_at_ic:.3f}Ω '
                    f'(vs {z_min_at_reg:.3f}Ω at regulator output) — '
                    f'trace parasitics degrade the entire impedance profile.')

            findings.append(_make_finding(
                'pdn', 'HIGH', 'PD-003',
                title=(f'{rail_name} PDN impedance at {worst_ic or "load IC"} '
                       f'exceeds target ({r_note}, {l_note} trace)'),
                description=(
                    f'{reg_ref} {rail_name} rail: target impedance '
                    f'{z_target:.3f}Ω (5% ripple, {i_transient:.1f}A transient). '
                    f'{detail} '
                    f'The regulator output caps alone may meet target, but the '
                    f'IC sees higher impedance due to the interconnect.'
                ),
                components=([reg_ref] + ([worst_ic] if worst_ic else [])
                            + [c['ref'] for c in node['output_caps'][:2]]),
                nets=[rail_name],
                recommendation=(
                    f'Add local decoupling capacitor(s) near {worst_ic or "load IC"}. '
                    f'Consider a 100nF MLCC within 2mm of the IC power pins to '
                    f'reduce impedance at high frequencies, plus bulk cap if '
                    f'low-frequency impedance is too high.'
                ),
            ))

    # --- PD-004: Cross-rail coupling from downstream switching ---
    for rail_name, node in tree.items():
        downstream_refs = node.get('downstream_regulators', [])
        if not downstream_refs:
            continue

        upstream_v = node['voltage']
        total_reflected = 0.0
        worst_freq = 0
        worst_downstream_ref = ''

        for ds_ref in downstream_refs:
            # Find the downstream node
            ds_node = None
            for other_name, other_node in tree.items():
                if other_node['regulator']['ref'] == ds_ref:
                    ds_node = other_node
                    break
            if not ds_node:
                continue

            i_trans, f_sw = cross_rail_transient_current(ds_node, upstream_v)
            if i_trans > 0 and f_sw > 0:
                total_reflected += i_trans
                if i_trans > total_reflected - i_trans:  # this one is the worst
                    worst_freq = f_sw
                    worst_downstream_ref = ds_ref

        if total_reflected <= 0 or worst_freq <= 0:
            continue

        # Check if upstream PDN can handle the reflected transient
        # at the switching frequency
        existing_load_mA = node['total_load_mA']
        combined_transient = (existing_load_mA / 1000.0 * 2) + total_reflected
        z_target_combined = pdn_target_impedance(
            upstream_v, ripple_pct=5.0, i_transient_a=combined_transient)

        # Get upstream impedance at the switching frequency
        reg_caps = node.get('output_caps', [])
        if not reg_caps:
            continue
        z_at_sw = parallel_cap_impedance(worst_freq, reg_caps)

        if z_at_sw > z_target_combined and z_at_sw < float('inf'):
            reg_ref = node['regulator']['ref']
            findings.append(_make_finding(
                'pdn', 'MEDIUM', 'PD-004',
                title=(f'{rail_name} PDN sees {total_reflected:.2f}A '
                       f'reflected transient from {worst_downstream_ref} '
                       f'at {worst_freq/1e6:.1f}MHz'),
                description=(
                    f'{worst_downstream_ref} is a switching regulator drawing '
                    f'pulsed current from the {rail_name} rail at '
                    f'{worst_freq/1e6:.1f}MHz. The reflected transient '
                    f'({total_reflected:.2f}A) combined with the rail\'s own '
                    f'load ({existing_load_mA}mA) pushes the effective '
                    f'transient to {combined_transient:.2f}A. The upstream '
                    f'PDN impedance at {worst_freq/1e6:.1f}MHz is '
                    f'{z_at_sw:.3f}Ω vs target {z_target_combined:.3f}Ω.'
                ),
                components=[reg_ref, worst_downstream_ref],
                nets=[rail_name],
                recommendation=(
                    f'Add input decoupling on {worst_downstream_ref}\'s '
                    f'input (a 10-22µF bulk cap plus 100nF MLCC), or add '
                    f'bulk capacitance on the {rail_name} rail.'
                ),
            ))

    return findings


# ---------------------------------------------------------------------------
# Category 12: Return Path Enhancement
# ---------------------------------------------------------------------------

def check_layer_transition_stitching(pcb: Dict,
                                     schematic: Optional[Dict] = None) -> List[Dict]:
    """RP-001: Check for ground stitching vias at signal layer transitions.

    When a signal changes layers via a through-via, the return current must
    also change planes. A nearby ground stitching via provides a low-impedance
    path for this transition. Without one, the return current takes a long
    detour, creating a loop antenna.

    Ref: Ott, "PCB Stack-Up Part 6"; Sierra Circuits return path guide.
    """
    # EQ-040: Via distance from layer transition vias
    findings = []
    layer_trans = pcb.get('layer_transitions', [])
    if not layer_trans:
        return findings

    # Get all via positions for proximity search
    vias_data = pcb.get('vias', {})
    all_vias = vias_data.get('vias', [])
    if not all_vias:
        return findings  # Can't check without individual via positions

    # Build set of ground nets
    gnd_nets = set()
    nets = pcb.get('nets', {})
    if isinstance(nets, dict):
        for name in nets:
            if _is_ground_net(name):
                gnd_nets.add(name)
    elif isinstance(nets, list):
        for n in nets:
            name = n.get('name', '') if isinstance(n, dict) else ''
            if _is_ground_net(name):
                gnd_nets.add(name)

    # Identify which vias are ground vias (connected to ground nets)
    gnd_via_positions = []
    for via in all_vias:
        net = via.get('net_name', via.get('net', ''))
        if isinstance(net, str) and _is_ground_net(net):
            gnd_via_positions.append((via.get('x', 0), via.get('y', 0)))
        elif isinstance(net, int):
            # Net number — look up name
            if isinstance(nets, dict):
                net_name = nets.get(net, nets.get(str(net), ''))
            else:
                net_name = ''
            if _is_ground_net(str(net_name)):
                gnd_via_positions.append((via.get('x', 0), via.get('y', 0)))

    if not gnd_via_positions:
        return findings  # Can't determine which vias are ground

    # Get default dielectric height for proximity threshold
    default_h = 0.2  # mm
    stackup = pcb.get('setup', {}).get('stackup', [])
    for layer in stackup:
        if layer.get('type') in ('core', 'prepreg'):
            try:
                h = float(layer.get('thickness', 0.2))
                if h > 0:
                    default_h = h
                    break
            except (ValueError, TypeError):
                pass

    search_radius = max(default_h * 2, 1.0)  # At least 1mm, or 2× dielectric height

    # Classify nets as high-speed or diff-pair for severity
    hs_nets = set()
    dp_nets = set()
    if schematic:
        for pair in schematic.get('design_analysis', {}).get('differential_pairs', []):
            dp_nets.add(pair.get('positive', ''))
            dp_nets.add(pair.get('negative', ''))

    flagged_nets = set()

    for lt in layer_trans:
        net_name = lt.get('net', '')
        if not net_name or _is_power_or_ground(net_name):
            continue
        if net_name in flagged_nets:
            continue

        layers = lt.get('copper_layers', [])
        if len(layers) <= 1:
            continue

        via_positions = lt.get('via_positions', [])
        if not via_positions:
            continue

        # Check each signal via for a nearby ground via
        unstitched_count = 0
        total_transitions = len(via_positions)

        for vp in via_positions:
            vx = vp.get('x', 0)
            vy = vp.get('y', 0)

            # Find nearest ground via
            min_dist = float('inf')
            for gx, gy in gnd_via_positions:
                d = math.sqrt((vx - gx)**2 + (vy - gy)**2)
                if d < min_dist:
                    min_dist = d

            if min_dist > search_radius:
                unstitched_count += 1

        if unstitched_count == 0:
            continue

        flagged_nets.add(net_name)
        is_dp = net_name in dp_nets
        is_hs = _is_high_speed_net(net_name) or _is_clock_net(net_name)

        if is_dp:
            severity = 'HIGH'
        elif is_hs:
            severity = 'HIGH'
        elif unstitched_count == total_transitions:
            severity = 'MEDIUM'
        else:
            severity = 'LOW'

        findings.append(_make_finding(
            'return_path', severity, 'RP-001',
            title=f'Missing stitching via at layer transition: {net_name}',
            description=(
                f'Net {net_name} has {total_transitions} layer transition(s) '
                f'across {", ".join(layers)}. '
                f'{unstitched_count} transition(s) have no ground stitching '
                f'via within {search_radius:.1f}mm. The return current must '
                f'find an alternate path, creating a loop antenna.'
            ),
            nets=[net_name],
            recommendation=(
                f'Add a ground stitching via within {search_radius:.1f}mm '
                f'of each signal via. Place the ground via adjacent to '
                f'the signal via on the same pad cluster.'
            ),
        ))

        # Limit to avoid flooding output on large boards
        if len(findings) > 20:
            findings.append(_make_finding(
                'return_path', 'MEDIUM', 'RP-001',
                title=f'{len(flagged_nets)}+ nets missing stitching vias (truncated)',
                description=(
                    'More than 20 nets have layer transitions without nearby '
                    'ground stitching vias. Review via placement board-wide.'
                ),
                recommendation='Add ground stitching vias at all signal layer transitions.',
            ))
            break

    return findings


# ---------------------------------------------------------------------------
# Pre-compliance test plan generator
# ---------------------------------------------------------------------------

def generate_test_plan(schematic: Optional[Dict], pcb: Optional[Dict],
                       findings: List[Dict],
                       standard: str = 'fcc-class-b') -> Dict:
    """Generate a pre-compliance test plan from analysis results.

    Returns a dict with frequency_bands, interface_risks, and probe_points.
    This is NOT a check — it produces advisory output, not findings.
    """
    plan = {
        'frequency_bands': [],
        'interface_risks': [],
        'probe_points': [],
    }

    # --- Frequency band prioritization ---
    # Collect emission sources
    sources_by_band = {}  # band_label → list of source descriptions

    # Get standard bands
    from emc_formulas import STANDARDS
    limit_table = STANDARDS.get(standard, STANDARDS.get('fcc-class-b', []))
    bands = []
    for f_min, f_max, limit, dist in limit_table:
        label = f'{f_min:.0f}-{f_max:.0f} MHz'
        bands.append({'label': label, 'min_hz': f_min * 1e6, 'max_hz': f_max * 1e6,
                      'limit_dbuv': limit, 'distance_m': dist})
        sources_by_band[label] = []

    # Switching regulator harmonics
    if schematic:
        for reg in get_findings(schematic, Det.POWER_REGULATORS):
            if reg.get('topology', '').lower() in ('ldo', 'linear'):
                continue
            ref = reg.get('ref', reg.get('reference', ''))
            val = reg.get('value', '')
            topology_local = reg.get('topology', '')
            sw_freq = reg.get('switching_frequency_hz') or _estimate_switching_freq(val) or _default_switching_freq(topology_local)
            if not sw_freq:
                continue
            for band in bands:
                harmonics = switching_harmonics_in_band(
                    sw_freq, band['min_hz'], band['max_hz'])
                if harmonics:
                    sources_by_band[band['label']].append(
                        f'{ref} ({val}) harmonics {harmonics[0]}-{harmonics[-1]}')

        # Crystal harmonics (up to 5th)
        for xtal in get_findings(schematic, Det.CRYSTAL_CIRCUITS):
            freq = xtal.get('frequency') or 0
            if not isinstance(freq, (int, float)) or freq <= 0:
                continue
            ref = xtal.get('reference', '?')
            for n in range(1, 6):
                h_freq = freq * n
                for band in bands:
                    if band['min_hz'] <= h_freq < band['max_hz']:
                        sources_by_band[band['label']].append(
                            f'{ref} {freq/1e6:.1f}MHz harmonic {n} ({h_freq/1e6:.1f}MHz)')

    for band in bands:
        src_list = sources_by_band[band['label']]
        if len(src_list) > 5:
            risk = 'high'
        elif len(src_list) > 1:
            risk = 'medium'
        elif len(src_list) > 0:
            risk = 'low'
        else:
            risk = 'none'
        plan['frequency_bands'].append({
            'band': band['label'],
            'freq_min_hz': band['min_hz'],
            'freq_max_hz': band['max_hz'],
            'risk_level': risk,
            'source_count': len(src_list),
            'sources': src_list[:10],
        })

    # Sort by source count descending
    plan['frequency_bands'].sort(key=lambda b: b['source_count'], reverse=True)

    # --- Interface risk ranking ---
    if pcb:
        footprints = pcb.get('footprints', [])
        connectors = _connector_refs(footprints)
        io_findings = [f for f in findings if f.get('rule_id') == 'IO-001']
        unfiltered_refs = set()
        for f in io_findings:
            unfiltered_refs.update(f.get('components', []))

        protocol_speeds = {
            'USB3': 9, 'HDMI': 9, 'PCIe': 8, 'USB': 7, 'Ethernet': 7,
            'SATA': 7, 'LVDS': 6, 'MIPI': 6, 'RS-485': 3, 'CAN': 3,
        }

        dp_nets = {}
        if schematic:
            for pair in schematic.get('design_analysis', {}).get('differential_pairs', []):
                for net in (pair.get('positive', ''), pair.get('negative', '')):
                    if net:
                        dp_nets[net] = pair.get('type', 'unknown')

        for conn in connectors:
            ref = conn.get('reference', '')
            val = conn.get('value', '')
            score = 3  # base
            reasons = []

            # Check protocol
            conn_nets = set()
            for pad in conn.get('pads', []):
                n = pad.get('net_name', '')
                if n:
                    conn_nets.add(n)
            proto = None
            for n in conn_nets:
                if n in dp_nets:
                    proto = dp_nets[n]
                    break
            if proto:
                score = protocol_speeds.get(proto, 4)
                reasons.append(f'{proto} interface')

            if ref in unfiltered_refs:
                score += 2
                reasons.append('No EMC filtering detected')

            if not pair.get('has_esd', True) if proto else True:
                pass  # Can't easily check per-connector ESD from here

            plan['interface_risks'].append({
                'connector': ref,
                'value': val,
                'protocol': proto or 'unknown',
                'risk_score': score,
                'reasons': reasons if reasons else ['General I/O'],
            })

        plan['interface_risks'].sort(key=lambda i: i['risk_score'], reverse=True)

    # --- Suggested probe points ---
    if pcb:
        footprints = pcb.get('footprints', [])

        # Switching regulator areas (inductors)
        for fp in footprints:
            ref = fp.get('reference', '')
            val = fp.get('value', '').lower()
            if ref.startswith('L') and not ref.startswith('LED'):
                x = fp.get('x') or 0
                y = fp.get('y') or 0
                if x or y:
                    plan['probe_points'].append({
                        'x': round(x, 1), 'y': round(y, 1),
                        'type': 'inductor',
                        'ref': ref,
                        'reason': f'Switching inductor — highest dI/dt source',
                    })

        # Crystal oscillators
        for fp in footprints:
            ref = fp.get('reference', '')
            if ref.startswith('Y') or ref.startswith('X'):
                x = fp.get('x') or 0
                y = fp.get('y') or 0
                if x or y:
                    plan['probe_points'].append({
                        'x': round(x, 1), 'y': round(y, 1),
                        'type': 'crystal',
                        'ref': ref,
                        'reason': f'Crystal/oscillator — clock harmonics source',
                    })

        # Unfiltered connectors
        for f in findings:
            if f.get('rule_id') == 'IO-001':
                for comp_ref in f.get('components', []):
                    for fp in footprints:
                        if fp.get('reference') == comp_ref:
                            x = fp.get('x') or 0
                            y = fp.get('y') or 0
                            if x or y:
                                plan['probe_points'].append({
                                    'x': round(x, 1), 'y': round(y, 1),
                                    'type': 'unfiltered_connector',
                                    'ref': comp_ref,
                                    'reason': 'Unfiltered I/O — cable radiation risk',
                                })
                            break

    return plan


# ---------------------------------------------------------------------------
# Regulatory coverage analysis
# ---------------------------------------------------------------------------

def analyze_regulatory_coverage(standard: str, market: Optional[str],
                                findings: List[Dict]) -> Dict:
    """Analyze which EMC standards apply and what the tool covers.

    Returns a dict with applicable_standards and coverage_matrix.
    """
    # Determine market from standard if not provided
    if not market:
        if 'fcc' in standard:
            market = 'us'
        elif 'cispr-25' in standard:
            market = 'automotive'
        elif 'mil' in standard:
            market = 'military'
        elif 'cispr' in standard:
            market = 'eu'
        else:
            market = 'us'

    applicable = MARKET_STANDARDS.get(market, MARKET_STANDARDS['us'])

    # Rules that provide coverage for each test type
    coverage_rules = {
        'radiated': {
            'checks': ['GP-001', 'GP-002', 'GP-003', 'GP-004', 'GP-005',
                        'DC-001', 'DC-002', 'SW-001', 'CK-001', 'CK-002',
                        'VS-001', 'SU-001', 'SU-002', 'IO-001',
                        'DP-001', 'DP-002', 'DP-003', 'DP-004',
                        'BE-001', 'BE-002', 'BE-003',
                        'EE-001', 'EE-002'],
            'note': 'Design rule checks identify common radiation sources. Cannot predict absolute emission levels.',
        },
        'conducted': {
            'checks': ['SW-001', 'DC-001', 'DC-002', 'EE-002'],
            'note': 'Switching harmonic analysis and decoupling checks. EMI filter verification not yet implemented.',
        },
        'esd': {
            'checks': ['IO-001'],
            'note': 'Checks for ESD/TVS presence near connectors. Does not verify protection path routing or clamping voltage.',
        },
        'eft': {
            'checks': [],
            'note': 'EFT/burst immunity requires lab testing. Input filtering checks (DC-001, IO-001) provide indirect coverage.',
        },
        'surge': {
            'checks': [],
            'note': 'Surge immunity requires lab testing. TVS/MOV placement checks provide indirect coverage.',
        },
        'transient': {
            'checks': [],
            'note': 'Automotive transient testing requires lab testing.',
        },
        'radiated_immunity': {
            'checks': [],
            'note': 'Radiated RF immunity requires lab testing. Ground plane and decoupling quality help.',
        },
        'conducted_susceptibility': {
            'checks': [],
            'note': 'Conducted susceptibility requires lab testing.',
        },
    }

    # Which rule_ids actually ran (produced findings)
    ran_rules = set()
    for f in findings:
        ran_rules.add(f.get('rule_id', ''))

    matrix = []
    for std_entry in applicable:
        std_type = std_entry.get('type', '')
        rules_info = coverage_rules.get(std_type, {'checks': [], 'note': 'Not covered.'})

        relevant_rules = rules_info['checks']
        checked = [r for r in relevant_rules if r in ran_rules]

        if len(checked) >= len(relevant_rules) * 0.5 and relevant_rules:
            coverage = 'partial'
        elif checked:
            coverage = 'minimal'
        elif relevant_rules:
            coverage = 'indirect'
        else:
            coverage = 'lab_only'

        matrix.append({
            'standard': std_entry['name'],
            'test_type': std_type,
            'coverage': coverage,
            'checked_rules': checked,
            'total_applicable_rules': len(relevant_rules),
            'note': rules_info['note'],
        })

    return {
        'market': market,
        'applicable_standards': [s['name'] for s in applicable],
        'coverage_matrix': matrix,
    }


# ---------------------------------------------------------------------------
# Inductor Magnetic Leakage
# ---------------------------------------------------------------------------

def check_inductor_leakage(pcb: Dict, schematic: Dict) -> List[Dict]:
    """ML-001: Flag unshielded switching inductors near sensitive circuits.

    Checks proximity of unshielded/unknown-shielding power inductors to
    sensitive analog components (ADCs, opamps, crystals, RF chains).
    Uses magnetic dipole H-field estimate to quantify coupling risk.

    Ref: Ott, "EMC Engineering" Ch. 11 — near-field coupling from
    switching inductor leakage flux causes noise injection into
    high-impedance analog circuits.
    """
    findings = []
    if not pcb or not schematic:
        return findings

    from kicad_utils import classify_inductor_shielding
    from emc_formulas import estimate_inductor_h_field

    footprints = pcb.get('footprints', [])
    regulators = get_findings(schematic, Det.POWER_REGULATORS)

    # Build ref → footprint position map
    fp_pos = {}
    fp_info = {}
    for fp in footprints:
        ref = fp.get('reference', '')
        if ref:
            fp_pos[ref] = (fp.get('x') or 0, fp.get('y') or 0)
            fp_info[ref] = fp

    # Collect switching inductor refs with shielding classification
    sw_inductors = []
    for reg in regulators:
        if reg.get('topology', '').lower() not in ('switching', 'buck', 'boost',
                                                    'buck-boost', 'sepic'):
            continue
        ind_ref = reg.get('inductor')
        if not ind_ref or ind_ref not in fp_pos:
            continue
        fp = fp_info.get(ind_ref, {})
        shielding = classify_inductor_shielding(
            footprint_lib=fp.get('library', fp.get('footprint', '')),
            value_str=fp.get('value', ''),
            mpn=fp.get('mpn', ''))
        if shielding == 'shielded':
            continue  # Shielded inductors have minimal leakage
        sw_inductors.append({
            'ref': ind_ref,
            'x': fp_pos[ind_ref][0],
            'y': fp_pos[ind_ref][1],
            'shielding': shielding,
            'reg_ref': reg.get('ref', reg.get('reference', '')),
            'sw_freq': reg.get('switching_frequency_hz', 0),
        })

    if not sw_inductors:
        return findings

    # Collect sensitive component positions from signal analysis
    sensitive_refs = set()
    # ADCs
    for adc in get_findings(schematic, Det.ADC_CIRCUITS):
        r = adc.get('ic', {}).get('ref') or adc.get('reference', '')
        if r:
            sensitive_refs.add(r)
    # Opamps
    for op in get_findings(schematic, Det.OPAMP_CIRCUITS):
        r = op.get('ic', {}).get('ref') or op.get('reference', '')
        if r:
            sensitive_refs.add(r)
    # Crystal oscillators
    for xtal in get_findings(schematic, Det.CRYSTAL_CIRCUITS):
        r = xtal.get('reference', '')
        if r:
            sensitive_refs.add(r)
        # Also flag the IC driving the crystal
        for conn in xtal.get('connected_ic', []):
            ic_ref = conn if isinstance(conn, str) else conn.get('ref', '')
            if ic_ref:
                sensitive_refs.add(ic_ref)
    # RF chains
    for rf in get_findings(schematic, Det.RF_CHAINS):
        for comp in rf.get('components', []):
            if isinstance(comp, str):
                r = comp
            else:
                r = comp.get('ref') or comp.get('reference', '')
            if r:
                sensitive_refs.add(r)

    # Filter to those with PCB positions
    sensitive = []
    for ref in sensitive_refs:
        if ref in fp_pos:
            sensitive.append({'ref': ref, 'x': fp_pos[ref][0], 'y': fp_pos[ref][1]})

    if not sensitive:
        return findings

    # Check proximity: flag when unshielded inductor is within 15mm of sensitive component
    import math
    proximity_threshold_mm = 15.0

    for ind in sw_inductors:
        for sens in sensitive:
            # EQ-106: Proximity gate — emit ML-001 when d_mm < 15mm AND
            #   H_field_A_per_m (from EQ-105, assuming I_peak = 1A, package
            #   = 5mm) exceeds threshold.
            #   d = √((x_ind - x_sens)² + (y_ind - y_sens)²).
            # Source: Threshold from Ott, "EMC Engineering" Ch. 11
            #   rule-of-thumb for unshielded switching inductor coupling to
            #   high-impedance analog nodes.
            dx = ind['x'] - sens['x']
            dy = ind['y'] - sens['y']
            dist_mm = math.sqrt(dx * dx + dy * dy)
            if dist_mm > proximity_threshold_mm:
                continue
            if dist_mm < 0.1:
                dist_mm = 0.1  # Avoid division by zero

            # Estimate H-field (assume 1A peak ripple current, 5mm package)
            h_field = estimate_inductor_h_field(
                peak_current_a=1.0,
                distance_m=dist_mm * 1e-3,
                inductor_size_mm=5.0)

            shielding_note = ind['shielding']
            if shielding_note == 'unknown':
                shielding_note = 'unknown (assumed unshielded)'

            severity = 'MEDIUM'
            if dist_mm < 8.0 and ind['shielding'] == 'unshielded':
                severity = 'HIGH'

            findings.append(_make_finding(
                'inductor_leakage', severity, 'ML-001',
                title='{ind} ({shield}) is {dist:.1f}mm from sensitive {sens}'.format(
                    ind=ind['ref'], shield=shielding_note,
                    dist=dist_mm, sens=sens['ref']),
                description=(
                    'Switching inductor {ind} ({shield} shielding, '
                    '{reg} at {freq}) is {dist:.1f}mm from {sens}. '
                    'Estimated H-field at this distance: {h:.2f} A/m '
                    '(1A peak ripple assumption). '
                    'Unshielded inductor magnetic leakage can couple '
                    'into nearby high-impedance analog circuits, '
                    'injecting switching noise.'
                ).format(
                    ind=ind['ref'], shield=shielding_note,
                    reg=ind['reg_ref'],
                    freq='{:.0f} kHz'.format(ind['sw_freq'] / 1e3) if ind['sw_freq'] else 'unknown freq',
                    dist=dist_mm, sens=sens['ref'],
                    h=h_field),
                components=[ind['ref'], sens['ref']],
                recommendation=(
                    'Use a shielded inductor (Coilcraft XGL/XAL, Wurth '
                    'WE-MAPI, Vishay IHLP, TDK SPM) or increase '
                    'separation to >15mm. Orient inductor axis '
                    'perpendicular to sensitive traces.'
                ),
                confidence='heuristic',
            ))

    return findings


# ---------------------------------------------------------------------------
# Master runner
# ---------------------------------------------------------------------------

def run_all_checks(schematic: Optional[Dict], pcb: Optional[Dict],
                   standard: str = 'fcc-class-b',
                   severity_threshold: str = 'all',
                   spice_backend=None) -> List[Dict]:
    """Run all EMC rule checks and return combined findings.

    Args:
        schematic: Schematic analyzer JSON (optional).
        pcb: PCB analyzer JSON (optional, but most checks need it).
        standard: Target EMC standard.
        severity_threshold: Minimum severity to include.
        spice_backend: SimulatorBackend instance for SPICE-enhanced
                       PDN/filter analysis (optional, None = analytical only).

    Returns:
        List of finding dicts, sorted by severity.
    """
    severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'INFO': 4}
    threshold = severity_order.get(severity_threshold.upper(), 4)

    all_findings = []

    # Pre-compute shared lookups for PCB checks
    net_id_map = _build_net_id_to_name(pcb) if pcb else {}

    if pcb:
        all_findings.extend(check_return_path_coverage(pcb))
        all_findings.extend(check_ground_zone_coverage(pcb))
        all_findings.extend(check_ground_domains(pcb))
        all_findings.extend(check_decoupling_distance(pcb))
        all_findings.extend(check_missing_decoupling(pcb, schematic))
        all_findings.extend(check_decoupling_via_distance(pcb))
        all_findings.extend(check_connector_filtering(pcb, schematic))
        all_findings.extend(check_connector_ground_pins(pcb, schematic))
        all_findings.extend(check_clock_routing(pcb, schematic))
        all_findings.extend(check_clock_near_connector(pcb, schematic, net_id_map))
        all_findings.extend(check_crystal_guard_ring(pcb, schematic))
        all_findings.extend(check_via_stitching(pcb, schematic))
        all_findings.extend(check_stackup(pcb))
        all_findings.extend(estimate_cavity_resonances(pcb))
        # Board edge checks
        all_findings.extend(check_trace_near_board_edge(pcb, schematic, net_id_map))
        all_findings.extend(check_ground_pour_ring(pcb))
        all_findings.extend(check_connector_area_stitching(pcb, schematic))
        # Return path enhancement
        all_findings.extend(check_layer_transition_stitching(pcb, schematic))
        # Crosstalk (requires --proximity PCB data)
        all_findings.extend(check_crosstalk_3h_rule(pcb, schematic))
        # ESD protection path (requires both schematic + PCB)
        all_findings.extend(check_esd_protection_path(pcb, schematic))
        # Shielding advisory
        all_findings.extend(check_shielding_advisory(pcb, schematic, standard))

    if schematic:
        all_findings.extend(check_switching_harmonics(schematic, standard))
        all_findings.extend(estimate_switching_emissions(schematic, standard, spice_backend))
        all_findings.extend(check_emi_filter_effectiveness(pcb, schematic, spice_backend))

    # Checks requiring both schematic and PCB
    if schematic and pcb:
        all_findings.extend(check_diff_pair_skew(pcb, schematic))
        all_findings.extend(check_diff_pair_cm_radiation(pcb, schematic, standard))
        all_findings.extend(check_diff_pair_reference_plane(pcb, schematic))
        all_findings.extend(check_diff_pair_layer(pcb, schematic))
        all_findings.extend(check_pdn_impedance(pcb, schematic, spice_backend))
        all_findings.extend(check_pdn_distributed(pcb, schematic, spice_backend))
        all_findings.extend(check_thermal_emc(pcb, schematic))
        all_findings.extend(check_switching_node_area(pcb, schematic, net_id_map))
        all_findings.extend(check_input_cap_loop_area(pcb, schematic, spice_backend))
        all_findings.extend(check_inductor_leakage(pcb, schematic))

    # Filter by severity
    if severity_threshold.lower() != 'all':
        all_findings = [f for f in all_findings
                        if severity_order.get(f['severity'], 4) <= threshold]

    # Sort by severity (critical first)
    all_findings.sort(key=lambda f: severity_order.get(f['severity'], 4))

    return all_findings
