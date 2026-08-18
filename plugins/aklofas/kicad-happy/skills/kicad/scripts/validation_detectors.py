"""Validation detectors — correctness checks that emit rich findings.

Separated from domain_detectors.py (which discovers circuit topologies).
These detectors check for design errors: missing components, wrong values,
protocol violations, sequencing issues.

Each validator takes an AnalysisContext (and optional detector results) and
returns a list of rich finding dicts via finding_schema.make_finding(
    source=ctx.source,).
"""

from __future__ import annotations

import re

from kicad_types import AnalysisContext
from kicad_utils import parse_value, parse_voltage_from_net_name

try:
    import os as _os, sys as _sys
    _ds_scripts = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                                '..', '..', 'datasheets', 'scripts')
    if _os.path.isdir(_ds_scripts):
        _sys.path.insert(0, _os.path.abspath(_ds_scripts))
    from datasheet_features import get_regulator_features, get_mcu_features
    _HAS_DS = True
except ImportError:
    _HAS_DS = False
    def get_regulator_features(mpn, **kw): return None
    def get_mcu_features(mpn, **kw): return None

from detector_helpers import (
    get_components_by_type, get_unique_ics, index_two_pin_components,
    match_ic_keywords,
)
from signal_detectors import _get_net_components
from finding_schema import make_finding, make_provenance
from lookup_helpers import get_facts, has_data, best


# ---------------------------------------------------------------------------
# Shared pull-up/pull-down detection helpers
# ---------------------------------------------------------------------------

def _find_pullups_on_net(
    ctx: AnalysisContext,
    net_name: str,
    resistor_nets: dict[str, tuple[str, str]],
    net_to_resistors: dict[str, list[str]],
) -> list[dict]:
    """Find pull-up resistors on a net (resistor between net and power rail).

    Returns list of dicts: [{ref, ohms, rail}].
    """
    pullups = []
    for rref in net_to_resistors.get(net_name, []):
        n1, n2 = resistor_nets.get(rref, (None, None))
        if not n1 or not n2:
            continue
        other = n2 if n1 == net_name else n1
        if ctx.is_power_net(other) and not ctx.is_ground(other):
            ohms = ctx.parsed_values.get(rref)
            pullups.append({'ref': rref, 'ohms': ohms, 'rail': other})
    return pullups


# Library / footprint substrings that identify a bridged-by-default solder
# jumper. SolderJumper_2_Bridged (Jumper library) is the canonical KiCad
# symbol; the footprint name carries _Bridged_ too. rc.2 4.1 expansion
# (SparkFun review — JP1/JP14/JP22 FP class on I2C buses behind bridged
# jumpers).
_BRIDGED_JUMPER_LIB_SUBSTRINGS = (
    'solderjumper_2_bridged',
    'solderjumper-2_p1.3mm_bridged',  # standard footprint suffix
)


def _bridged_jumper_neighbor_nets(ctx: AnalysisContext, net_name: str) -> list[str]:
    """Return nets reachable from `net_name` via one hop through a
    SolderJumper_2_Bridged. Used to extend pull-up search across
    bridged-by-default jumpers (PR-001 I2C check).
    """
    if not net_name:
        return []
    neighbors: list[str] = []
    seen: set[str] = set()
    for comp in ctx.components:
        lib = (comp.get('lib_id', '') + ' ' + comp.get('footprint', '')).lower()
        if not any(s in lib for s in _BRIDGED_JUMPER_LIB_SUBSTRINGS):
            continue
        ref = comp.get('reference')
        if not ref:
            continue
        # Two-pin jumper; collect nets on its pins
        jumper_nets = set()
        for pnum, (net, _) in (ctx.ref_pins.get(ref, {}) or {}).items():
            if net:
                jumper_nets.add(net)
        if net_name not in jumper_nets or len(jumper_nets) != 2:
            continue
        for n in jumper_nets:
            if n != net_name and n not in seen:
                seen.add(n)
                neighbors.append(n)
    return neighbors


def _find_pullups_on_net_with_bridged(
    ctx: AnalysisContext,
    net_name: str,
    resistor_nets: dict[str, tuple[str, str]],
    net_to_resistors: dict[str, list[str]],
) -> list[dict]:
    """Like `_find_pullups_on_net` but also walks one hop through
    SolderJumper_2_Bridged to find pullups attached on the bridged side
    of the jumper. rc.2 4.1 expansion (SparkFun review).
    """
    pullups = list(_find_pullups_on_net(ctx, net_name, resistor_nets, net_to_resistors))
    for neighbor in _bridged_jumper_neighbor_nets(ctx, net_name):
        for pu in _find_pullups_on_net(ctx, neighbor, resistor_nets, net_to_resistors):
            if pu not in pullups:
                pullups.append(pu)
    return pullups


def _find_pulldowns_on_net(
    ctx: AnalysisContext,
    net_name: str,
    resistor_nets: dict[str, tuple[str, str]],
    net_to_resistors: dict[str, list[str]],
) -> list[dict]:
    """Find pull-down resistors on a net (resistor between net and ground)."""
    pulldowns = []
    for rref in net_to_resistors.get(net_name, []):
        n1, n2 = resistor_nets.get(rref, (None, None))
        if not n1 or not n2:
            continue
        other = n2 if n1 == net_name else n1
        if ctx.is_ground(other):
            ohms = ctx.parsed_values.get(rref)
            pulldowns.append({'ref': rref, 'ohms': ohms, 'rail': other})
    return pulldowns


def _get_pin_net(ctx: AnalysisContext, ref: str, pin_names: tuple[str, ...]) -> str | None:
    """Find the net connected to a pin matching any of the given names."""
    pins = ctx.ref_pins.get(ref, {})
    for pnum, (net, _) in pins.items():
        comp = ctx.comp_lookup.get(ref)
        if not comp:
            continue
        for p in comp.get('pins', []):
            if p.get('number') == pnum and p.get('name', '').upper() in pin_names:
                return net
    # Fallback: check net pin_name via ctx.nets
    for pnum, (net, _) in pins.items():
        if not net or net not in ctx.nets:
            continue
        for np in ctx.nets[net]['pins']:
            if np['component'] == ref and np.get('pin_name', '').upper() in pin_names:
                return net
    return None


def _net_has_driver(ctx: AnalysisContext, net_name: str, exclude_ref: str) -> bool:
    """Check if a net has at least one push-pull driver (non-OD/OC IC output)."""
    if not net_name or net_name not in ctx.nets:
        return False
    for p in ctx.nets[net_name]['pins']:
        if p['component'] == exclude_ref:
            continue
        comp = ctx.comp_lookup.get(p['component'])
        if not comp:
            continue
        if comp['type'] == 'ic':
            return True  # Conservative: assume IC outputs can drive
    return False


# ---------------------------------------------------------------------------
# PU-001: Missing pull-ups / pull-downs
# ---------------------------------------------------------------------------

# Pin names that typically require pull-up resistors
_PULLUP_PIN_NAMES = (
    'NRST', 'NRESET', 'RESET', 'RST', 'RESET_N', 'RST_N', 'XRES',
    'EN', 'ENABLE', 'CE', 'SHDN', 'SHUTDOWN', 'nSHDN',
    'INT', 'IRQ', 'ALERT', 'DRDY', 'BUSY', 'RDY',
    'INT1', 'INT2', 'IRQ1', 'IRQ2', 'ALERT1', 'ALERT2',
    'SDA', 'SCL', 'I2C_SDA', 'I2C_SCL',
    'MISO',  # SPI open-drain mode
    'OD', 'OPEN_DRAIN',
    'PG', 'PGOOD', 'POWER_GOOD', 'nPG',
    'FAULT', 'nFAULT', 'FLAG', 'nFLAG',
    'STAT', 'STAT1', 'STAT2', 'CHG', 'nCHG',
    'WDI', 'WDO', 'MR', 'nMR',
)

# Pin names that typically require pull-down resistors
_PULLDOWN_PIN_NAMES = (
    'BOOT0',  # STM32 boot mode selection
    'MODE', 'CFG', 'SEL',
)

# ICs known to have open-drain / open-collector outputs
_OPEN_DRAIN_IC_KEYWORDS = (
    'pca9', 'tca9', 'pcf8574', 'pcf8575',  # I2C GPIO expanders
    'mcp23', 'sx1509',                       # GPIO expanders
    'ina219', 'ina226', 'ina228', 'ina260',  # Current monitors (ALERT)
    'tmp1', 'tmp4', 'lm75', 'ds18b20',       # Temp sensors (ALERT/DQ)
    'max3', 'max1',                           # Supervisors
    'tps38', 'tps386',                        # Voltage supervisors
    'stusb', 'fusb',                          # USB PD controllers
)

# Typical pull-up value range (ohms) — flag if outside
_PULLUP_MIN_OHMS = 1000      # 1k — below this is suspicious
_PULLUP_MAX_OHMS = 100000    # 100k — above this is weak

# Regulators with internal EN pull-up — EN can be left floating (the part
# enables itself by default) without a discrete external pull-up. Per-part
# prefixes from TI/MPS/Microchip; pattern-match against IC value/MPN upper-cased.
# rc.2 4.1 expansion (SparkFun + Manas review).
_INTERNAL_EN_PULLUP_REGULATOR_PREFIXES = (
    'TPS54302', 'TPS5430',     # TI sync buck (D-CAP2) — internal EN pull-up
    'TPS6213',                 # TI buck with internal soft-start + EN pull-up
    'MCP1727',                 # Microchip LDO
    'MP2315', 'MP2303',        # MPS sync bucks
    'LMR33630',                # TI sync buck
)
_EN_PIN_PATTERN_SET = frozenset((
    'EN', 'ENABLE', 'CE', 'SHDN', 'SHUTDOWN', 'NSHDN', 'ON', 'ONOFF', 'RUN',
))


def _has_internal_en_pullup(ic: dict, pin_name: str) -> bool:
    """True when (ic, pin) matches a regulator whose datasheet says EN may
    be left floating (internal pull-up). Used to suppress PU-001 missing-
    pullup warnings on those parts' EN pins.
    """
    pin_upper = pin_name.upper().replace('-', '').replace('_', '')
    if pin_upper not in _EN_PIN_PATTERN_SET:
        return False
    val_mpn = ((ic.get('mpn') or '') + ' ' + (ic.get('value') or '')).upper()
    return any(prefix in val_mpn for prefix in _INTERNAL_EN_PULLUP_REGULATOR_PREFIXES)


def validate_pullups(ctx: AnalysisContext) -> list[dict]:
    """PU-001: Check for missing pull-up/pull-down resistors on logic pins.

    Scans IC pins with names matching known open-drain, reset, enable, and
    interrupt patterns. For each, checks whether a pull-up or pull-down
    resistor exists on the same net. Emits findings for missing or
    out-of-range resistors.
    """
    findings: list[dict] = []

    resistors = get_components_by_type(ctx, 'resistor')
    resistor_nets, net_to_resistors = index_two_pin_components(ctx, resistors)

    ics = get_unique_ics(ctx)
    checked_nets: set[str] = set()

    cache_dir = getattr(ctx, 'cache_dir', None)
    design_context = getattr(ctx, 'design_context', None)

    for ic in ics:
        ref = ic['reference']
        mpn = ic.get('mpn') or ic.get('value') or ''
        facts = get_facts(mpn, cache_dir=cache_dir) if mpn else None
        pins = ctx.ref_pins.get(ref, {})

        for pnum, (net, _) in pins.items():
            if not net or ctx.is_power_net(net) or ctx.is_ground(net):
                continue
            if net in checked_nets:
                continue

            # Get pin name
            pin_name = ''
            for p in ic.get('pins', []):
                if p.get('number') == pnum:
                    pin_name = p.get('name', '')
                    break
            if not pin_name:
                # Try from net info
                for np in ctx.nets.get(net, {}).get('pins', []):
                    if np['component'] == ref and np['pin_number'] == pnum:
                        pin_name = np.get('pin_name', '')
                        break

            pin_upper = pin_name.upper().replace('-', '').replace('_', '')

            # Check if this pin needs a pull-up
            needs_pullup = False
            for pn in _PULLUP_PIN_NAMES:
                if pn.replace('-', '').replace('_', '') == pin_upper or pin_upper.endswith(pn.replace('-', '').replace('_', '')):
                    needs_pullup = True
                    break

            # Also check if IC is a known open-drain type
            if not needs_pullup and match_ic_keywords(ic, _OPEN_DRAIN_IC_KEYWORDS):
                # For OD ICs, check ALERT/INT/OUT pins
                if any(pin_upper.startswith(p) for p in ('INT', 'IRQ', 'ALERT', 'OUT', 'DRDY', 'DQ')):
                    needs_pullup = True

            needs_pulldown = False
            for pn in _PULLDOWN_PIN_NAMES:
                if pn.replace('-', '').replace('_', '') == pin_upper:
                    needs_pulldown = True
                    break

            if not needs_pullup and not needs_pulldown:
                continue

            checked_nets.add(net)

            if needs_pullup:
                # Datasheet path: if facts has recommended_pullup_range, use it.
                # Heuristic path: fall back to _PULLUP_MIN/MAX_OHMS (always fires
                # in v1.4 — no extracted MPN carries recommended_pullup_range yet;
                # 4d-active populates ctx.cache_dir to activate datasheet path).
                ds_range = None
                if facts is not None:
                    _specs = getattr(
                        getattr(facts, 'base', None), 'recommended_pullup_range', None
                    )
                    if has_data(_specs):
                        ds_range = best(_specs, min_confidence='medium')

                if ds_range is not None:
                    pu_confidence = 'datasheet-backed'
                    pu_evidence = 'datasheet'
                    pu_min = ds_range.min if ds_range.min is not None else _PULLUP_MIN_OHMS
                    pu_max = ds_range.max if ds_range.max is not None else _PULLUP_MAX_OHMS
                else:
                    pu_confidence = 'heuristic'
                    pu_evidence = 'topology'
                    pu_min = _PULLUP_MIN_OHMS
                    pu_max = _PULLUP_MAX_OHMS

                pullups = _find_pullups_on_net(ctx, net, resistor_nets, net_to_resistors)
                if not pullups:
                    # Check if another driver exists (push-pull output driving it)
                    if _net_has_driver(ctx, net, ref):
                        continue  # Net is actively driven, pull-up not strictly required

                    # Skip regulators whose EN pin has an internal pull-up
                    # (rc.2 4.1 expansion — TI/MPS/Microchip parts list).
                    if _has_internal_en_pullup(ic, pin_name):
                        continue

                    findings.append(make_finding(
                        detector='validate_pullups',
                        rule_id='PU-001',
                        category='signal_integrity',
                        summary=f'{ref} pin {pin_name} ({net}) missing pull-up resistor',
                        description=(
                            f'Pin {pin_name} on {ref} ({ic.get("value", "")}) is '
                            f'connected to net {net} but has no pull-up resistor. '
                            f'This pin type typically requires an external pull-up '
                            f'to a power rail for correct operation.'
                        ),
                        severity='warning',
                        confidence=pu_confidence,
                        evidence_source=pu_evidence,
                        components=[ref],
                        nets=[net],
                        pins=[{'ref': ref, 'pin': pin_name, 'function': 'open_drain_or_input'}],
                        recommendation=f'Add a 4.7k-10k pull-up resistor from {net} to the appropriate power rail.',
                        fix_params={
                            'type': 'add_component',
                            'components': [{'type': 'resistor', 'value': '10k',
                                            'net_from': net, 'net_to': '<power_rail>'}],
                            'basis': f'Pin {pin_name} is open-drain/input type requiring pull-up',
                        },
                        report_section='Signal Integrity',
                        impact='Pin may float or bus may not function without pull-up',
                        provenance=make_provenance('pu_missing_pullup', 'deterministic'),
                        design_context=design_context,
                        schema_era='v1.4',
                        source=ctx.source,))
                else:
                    # Check pull-up value range
                    for pu in pullups:
                        if pu['ohms'] is not None:
                            if pu['ohms'] < pu_min:
                                findings.append(make_finding(
                                    detector='validate_pullups',
                                    rule_id='PU-001',
                                    category='signal_integrity',
                                    summary=f'{ref} pin {pin_name}: pull-up {pu["ref"]} value too low ({pu["ohms"]:.0f}R)',
                                    description=(
                                        f'Pull-up {pu["ref"]} on net {net} has value '
                                        f'{pu["ohms"]:.0f} ohms, which is below the typical '
                                        f'minimum of {pu_min} ohms. This draws '
                                        f'excessive current when the output is low.'
                                    ),
                                    severity='info',
                                    confidence=pu_confidence,
                                    evidence_source=pu_evidence,
                                    components=[ref, pu['ref']],
                                    nets=[net],
                                    recommendation=f'Consider increasing {pu["ref"]} to 4.7k-10k.',
                                    provenance=make_provenance('pu_value_check', 'deterministic'),
                                    design_context=design_context,
                                    schema_era='v1.4',
                                    source=ctx.source,))
                            elif pu['ohms'] > pu_max:
                                findings.append(make_finding(
                                    detector='validate_pullups',
                                    rule_id='PU-001',
                                    category='signal_integrity',
                                    summary=f'{ref} pin {pin_name}: pull-up {pu["ref"]} value too high ({pu["ohms"]/1000:.0f}k)',
                                    description=(
                                        f'Pull-up {pu["ref"]} on net {net} has value '
                                        f'{pu["ohms"]/1000:.0f}k ohms, which is above the typical '
                                        f'maximum of {pu_max/1000:.0f}k ohms. The signal '
                                        f'rise time may be too slow for reliable operation.'
                                    ),
                                    severity='info',
                                    confidence=pu_confidence,
                                    evidence_source=pu_evidence,
                                    components=[ref, pu['ref']],
                                    nets=[net],
                                    recommendation=f'Consider decreasing {pu["ref"]} to 4.7k-10k.',
                                    provenance=make_provenance('pu_weak_pullup', 'deterministic'),
                                    design_context=design_context,
                                    schema_era='v1.4',
                                    source=ctx.source,))

            if needs_pulldown:
                pulldowns = _find_pulldowns_on_net(ctx, net, resistor_nets, net_to_resistors)
                if not pulldowns:
                    findings.append(make_finding(
                        detector='validate_pullups',
                        rule_id='PU-001',
                        category='signal_integrity',
                        summary=f'{ref} pin {pin_name} ({net}) missing pull-down resistor',
                        description=(
                            f'Pin {pin_name} on {ref} ({ic.get("value", "")}) is '
                            f'connected to net {net} but has no pull-down resistor. '
                            f'This pin requires a defined logic level at startup.'
                        ),
                        severity='warning',
                        confidence='heuristic',
                        evidence_source='topology',
                        components=[ref],
                        nets=[net],
                        pins=[{'ref': ref, 'pin': pin_name, 'function': 'mode_select'}],
                        recommendation=f'Add a 10k pull-down resistor from {net} to GND.',
                        fix_params={
                            'type': 'add_component',
                            'components': [{'type': 'resistor', 'value': '10k',
                                            'net_from': net, 'net_to': 'GND'}],
                            'basis': f'Pin {pin_name} is a mode/boot selection pin',
                        },
                        report_section='Signal Integrity',
                        impact='Pin floats at startup, undefined behavior',
                        provenance=make_provenance('pu_missing_pullup', 'deterministic'),
                        design_context=design_context,
                        schema_era='v1.4',
                        source=ctx.source,))

    return findings


# ---------------------------------------------------------------------------
# VM-001: Cross-domain voltage mismatch
# ---------------------------------------------------------------------------

_VOLTAGE_THRESHOLDS = {
    1.8: (0.4, 1.35, 0.63, 1.17, 2.0),
    2.5: (0.4, 2.0, 0.7, 1.7, 2.75),
    3.3: (0.4, 2.4, 0.8, 2.0, 3.6),
    5.0: (0.5, 4.4, 1.5, 3.5, 5.5),
}


def _estimate_rail_voltage_for_ic(ctx: AnalysisContext, ref: str) -> float | None:
    """Estimate IC supply rail voltage. Regulators use VIN pin; others use first power net."""
    comp = ctx.comp_lookup.get(ref, {})
    mpn = comp.get('mpn') or comp.get('value', '')
    feat = get_regulator_features(mpn) if mpn else None
    if feat and not feat.get('quality', {}).get('trusted', True):
        feat = None   # deterministic detectors keep the v1.4 trust gate (v2.0 §3.A.1)
    if feat and feat.get('vin_pin'):
        vin_pin = str(feat['vin_pin'])
        pins = ctx.ref_pins.get(ref, {})
        for pnum, (net, _) in pins.items():
            if str(pnum) == vin_pin and net and ctx.is_power_net(net) and not ctx.is_ground(net):
                v = parse_voltage_from_net_name(net)
                if v is not None:
                    return v

    pins = ctx.ref_pins.get(ref, {})
    for pnum, (net, _) in pins.items():
        if net and ctx.is_power_net(net) and not ctx.is_ground(net):
            v = parse_voltage_from_net_name(net)
            if v is not None:
                return v
    return None


def _closest_threshold(voltage: float) -> tuple:
    if voltage is None:
        return None
    best = None
    best_dist = float('inf')
    for v, thresh in _VOLTAGE_THRESHOLDS.items():
        dist = abs(v - voltage)
        if dist < best_dist:
            best_dist = dist
            best = thresh
    return best


def validate_voltage_levels(ctx: AnalysisContext, level_shifters: list[dict] | None = None) -> list[dict]:
    """VM-001: Detect signal nets crossing power domain boundaries without level shifting."""
    findings: list[dict] = []
    cache_dir = getattr(ctx, 'cache_dir', None)
    design_context = getattr(ctx, 'design_context', None)

    ic_voltages: dict[str, float] = {}
    for ic in get_unique_ics(ctx):
        v = _estimate_rail_voltage_for_ic(ctx, ic['reference'])
        if v is not None:
            ic_voltages[ic['reference']] = v
            # 4b lookup probe (informational; future v1.5 will use
            # facts.base.recommended_operating.VDD to validate the rail estimate).
            mpn = ic.get('mpn') or ic.get('value') or ''
            facts = get_facts(mpn, cache_dir=cache_dir) if mpn else None
            # facts probe is informational — confidence stays heuristic regardless.

    shifted_nets: set[str] = set()
    if level_shifters:
        for ls in level_shifters:
            for net in ls.get('shifted_nets', []):
                shifted_nets.add(net)
            ref = ls.get('reference', ls.get('ref', ''))
            for pnum, (net, _) in ctx.ref_pins.get(ref, {}).items():
                if net and not ctx.is_power_net(net) and not ctx.is_ground(net):
                    shifted_nets.add(net)

    checked_nets: set[str] = set()

    for net_name, net_info in ctx.nets.items():
        if net_name in checked_nets or ctx.is_power_net(net_name) or ctx.is_ground(net_name):
            continue
        if net_name in shifted_nets:
            continue

        ic_pins_on_net = []
        for p in net_info.get('pins', []):
            ref = p['component']
            if ref in ic_voltages:
                ic_pins_on_net.append({
                    'ref': ref, 'pin': p.get('pin_name', ''),
                    'pin_number': p['pin_number'], 'voltage': ic_voltages[ref],
                })

        if len(ic_pins_on_net) < 2:
            continue

        voltages = set(p['voltage'] for p in ic_pins_on_net)
        if len(voltages) <= 1:
            continue

        checked_nets.add(net_name)
        v_max = max(voltages)
        v_min = min(voltages)

        # Check if this is a regulator EN pin — skip if threshold is compatible
        _EN_PIN_PATTERNS = ('EN', 'ENABLE', 'CE', 'SHDN', 'nSHDN', 'ON', 'ON_OFF', 'RUN')
        skip_en = False
        for p in ic_pins_on_net:
            comp = ctx.comp_lookup.get(p['ref'], {})
            p_mpn = comp.get('mpn') or comp.get('value', '')
            # Datasheet-backed path: check EN pin threshold
            ds_feat = get_regulator_features(p_mpn) if p_mpn else None
            if ds_feat and not ds_feat.get('quality', {}).get('trusted', True):
                ds_feat = None   # deterministic detectors keep the v1.4 trust gate (v2.0 §3.A.1)
            if ds_feat and ds_feat.get('en_pin'):
                pin_names = ctx.ref_pins.get(p['ref'], {})
                for pnum, (net, pname) in pin_names.items():
                    if net == net_name and str(pnum) == str(ds_feat['en_pin']):
                        en_ih = ds_feat.get('en_v_ih_max')
                        if en_ih is not None and v_min >= 2 * en_ih:
                            skip_en = True
                            break
                if skip_en:
                    break
            # Heuristic fallback: pin name matches EN pattern on a regulator-family part
            if not ds_feat:
                val_mpn = ((comp.get('mpn') or '') + ' ' + (comp.get('value') or '')).upper()
                is_regulator_like = any(pfx in val_mpn for pfx in (
                    'TPS6', 'TPS5', 'LM25', 'LM33', 'LM317', 'AP21', 'AMS11',
                    'MP23', 'MP15', 'XL40', 'RT8', 'SY8', 'MIC29', 'NCP',
                    'LDO', 'BOOST', 'BUCK', 'REG',
                ))
                if is_regulator_like or comp.get('type') == 'power_regulator':
                    pin_name = (p.get('pin') or '').upper().strip()
                    if pin_name in _EN_PIN_PATTERNS:
                        skip_en = True
                        break
        if skip_en:
            continue

        low_thresh = _closest_threshold(v_min)
        if low_thresh is None:
            continue

        abs_max = low_thresh[4]
        if v_max > abs_max:
            severity = 'error'
            desc = (
                f'Net {net_name} connects ICs in {v_max}V and {v_min}V domains. '
                f'The {v_max}V output may exceed the {v_min}V input absolute maximum '
                f'rating of {abs_max}V, risking damage.'
            )
        else:
            high_thresh = _closest_threshold(v_max)
            voh = high_thresh[1] if high_thresh else v_max * 0.7
            vih = low_thresh[3]
            if voh < vih:
                severity = 'warning'
                desc = (
                    f'Net {net_name} connects ICs in {v_max}V and {v_min}V domains. '
                    f'The {v_max}V output VOH ({voh}V) may not meet the {v_min}V '
                    f'input VIH threshold ({vih}V).'
                )
            else:
                continue

        refs = list(set(p['ref'] for p in ic_pins_on_net))
        findings.append(make_finding(
            detector='validate_voltage_levels',
            rule_id='VM-001',
            category='signal_integrity',
            summary=f'Net {net_name}: {v_max}V / {v_min}V domain crossing without level shifter',
            description=desc,
            severity=severity,
            confidence='heuristic',
            evidence_source='topology',
            components=refs,
            nets=[net_name],
            pins=[{'ref': p['ref'], 'pin': p['pin'], 'function': 'signal_io'}
                  for p in ic_pins_on_net],
            recommendation=(
                f'Add a level shifter between the {v_max}V and {v_min}V domains on net {net_name}, '
                f'or verify that the connected ICs have tolerant inputs.'
            ),
            fix_params={
                'type': 'add_component',
                'components': [{'type': 'level_shifter',
                                'domain_a': f'{v_max}V', 'domain_b': f'{v_min}V',
                                'nets': [net_name]}],
                'basis': f'Net crosses {v_max}V to {v_min}V boundary',
            },
            report_section='Signal Integrity',
            impact='Risk of damage or unreliable logic levels',
            provenance=make_provenance('vm_rail_mismatch', 'deterministic'),
            design_context=design_context,
            schema_era='v1.4',
            source=ctx.source,))

    return findings


# ---------------------------------------------------------------------------
# PR-001..004: Protocol pin validation
# ---------------------------------------------------------------------------

_I2C_IC_KEYWORDS = (
    'pca9', 'tca9', 'pcf8574', 'pcf8575', 'mcp23', 'at24', 'eeprom',
    'ina219', 'ina226', 'ina228', 'ina260', 'ina3221',
    'tmp1', 'tmp4', 'lm75', 'sht3', 'sht4', 'bme280', 'bme680', 'bmp280',
    'mpu6050', 'mpu9250', 'icm20', 'lsm6', 'lis3', 'adxl3',
    'ads1015', 'ads1115', 'mcp4725', 'dac8', 'max517',
    'ds1307', 'ds3231', 'pcf8523', 'rv3028', 'rv8803',
    'si5351', 'pll', 'cdce',
    'tca6408', 'sx1509', 'pca6416',
    'as5600', 'as5048', 'vl53l',
    'is31fl', 'lp5024', 'pca9685',
    'stusb', 'fusb302', 'bq2597',
)
_I2C_SDA_NAMES = ('SDA', 'I2C_SDA', 'TWI_SDA', 'SDAI', 'SDA1', 'SDA2', 'SDATA')
_I2C_SCL_NAMES = ('SCL', 'I2C_SCL', 'TWI_SCL', 'SCLI', 'SCL1', 'SCL2', 'SCLK')
_I2C_PULLUP_RANGES = {
    'standard': (1000, 10000),
    'fast': (1000, 4700),
    'fast_plus': (470, 2200),
}

_SPI_IC_KEYWORDS = (
    'w25q', 'mx25', 'at25', 'sst26', 'is25', 'gd25',
    'mcp3', 'ads8', 'ad7', 'max11',
    'mcp49', 'dac8',
    'sx127', 'rfm9', 'cc1101', 'nrf24', 'si446',
    'enc28j', 'w5500', 'ksz8',
    'max7219', 'apa102', 'dotstar',
    'sd_card', 'sdcard',
    'lis3', 'adxl3', 'bmi160', 'icm42',
)
_SPI_CS_NAMES = ('CS', 'SS', 'NSS', 'SPI_CS', 'SPI_SS', 'CSN', 'NCS', 'CE0', 'CE1')

_CAN_IC_KEYWORDS = (
    'mcp2515', 'mcp2551', 'mcp2562', 'mcp25625',
    'sn65hvd', 'sn65hvd230', 'sn65hvd231', 'sn65hvd232',
    'tja1', 'tja1050', 'tja1051', 'tja1040', 'tja1042', 'tja1043',
    'iso1050', 'iso1042',
    'max3', 'max33',
    'adm3053',
)
_CAN_H_NAMES = ('CANH', 'CAN_H', 'CANHI', 'CAN_HIGH')
_CAN_L_NAMES = ('CANL', 'CAN_L', 'CANLO', 'CAN_LOW')

_USB_DP_NAMES = ('D+', 'DP', 'USB_DP', 'USB_D+', 'USBDP', 'D_P')
_USB_DM_NAMES = ('D-', 'DM', 'USB_DM', 'USB_D-', 'USBDM', 'D_N')


def validate_i2c_bus(ctx: AnalysisContext) -> list[dict]:
    """PR-001: Validate I2C bus integrity — pull-ups, values, address conflicts."""
    findings: list[dict] = []
    resistors = get_components_by_type(ctx, 'resistor')
    resistor_nets, net_to_resistors = index_two_pin_components(ctx, resistors)

    i2c_buses: dict[str, dict] = {}
    for ic in get_unique_ics(ctx):
        ref = ic['reference']
        if not match_ic_keywords(ic, _I2C_IC_KEYWORDS):
            continue
        sda_net = _get_pin_net(ctx, ref, _I2C_SDA_NAMES)
        scl_net = _get_pin_net(ctx, ref, _I2C_SCL_NAMES)
        if not sda_net or not scl_net:
            continue
        bus_key = f'{sda_net}:{scl_net}'
        bus = i2c_buses.setdefault(bus_key, {'sda_net': sda_net, 'scl_net': scl_net, 'devices': []})
        bus['devices'].append(ref)

    for bus_key, bus in i2c_buses.items():
        sda, scl = bus['sda_net'], bus['scl_net']
        refs = bus['devices']

        sda_pullups = _find_pullups_on_net_with_bridged(ctx, sda, resistor_nets, net_to_resistors)
        if not sda_pullups:
            findings.append(make_finding(
                detector='validate_i2c_bus', rule_id='PR-001', category='protocol_integrity',
                summary=f'I2C bus {sda}/{scl}: SDA missing pull-up',
                description=f'I2C bus with {len(refs)} device(s) ({", ".join(refs)}) has no pull-up on SDA net {sda}.',
                severity='error', confidence='deterministic', evidence_source='topology',
                components=refs, nets=[sda, scl],
                recommendation='Add a 4.7k pull-up resistor from SDA to VDD.',
                fix_params={'type': 'add_component', 'components': [{'type': 'resistor', 'value': '4.7k', 'net_from': sda, 'net_to': '<VDD>'}], 'basis': 'I2C spec requires pull-ups on SDA'},
                standard_ref='I2C specification UM10204 section 3.1.1', impact='I2C bus non-functional',
                provenance=make_provenance('pr_i2c_spec', 'deterministic'),
            
                source=ctx.source,))

        scl_pullups = _find_pullups_on_net_with_bridged(ctx, scl, resistor_nets, net_to_resistors)
        if not scl_pullups:
            findings.append(make_finding(
                detector='validate_i2c_bus', rule_id='PR-001', category='protocol_integrity',
                summary=f'I2C bus {sda}/{scl}: SCL missing pull-up',
                description=f'I2C bus with {len(refs)} device(s) ({", ".join(refs)}) has no pull-up on SCL net {scl}.',
                severity='error', confidence='deterministic', evidence_source='topology',
                components=refs, nets=[sda, scl],
                recommendation='Add a 4.7k pull-up resistor from SCL to VDD.',
                fix_params={'type': 'add_component', 'components': [{'type': 'resistor', 'value': '4.7k', 'net_from': scl, 'net_to': '<VDD>'}], 'basis': 'I2C spec requires pull-ups on SCL'},
                standard_ref='I2C specification UM10204 section 3.1.1', impact='I2C bus non-functional',
                provenance=make_provenance('pr_i2c_spec', 'deterministic'),
            
                source=ctx.source,))

        for net_label, pullups in [('SDA', sda_pullups), ('SCL', scl_pullups)]:
            for pu in pullups:
                if pu['ohms'] is not None:
                    low, high = _I2C_PULLUP_RANGES['standard']
                    if pu['ohms'] < low or pu['ohms'] > high:
                        findings.append(make_finding(
                            detector='validate_i2c_bus', rule_id='PR-001', category='protocol_integrity',
                            summary=f'I2C {net_label} pull-up {pu["ref"]} out of range ({pu["ohms"]:.0f}R)',
                            description=f'I2C {net_label} pull-up {pu["ref"]} is {pu["ohms"]:.0f} ohms. Recommended: {low}-{high} ohms for standard-mode.',
                            severity='info', confidence='heuristic', evidence_source='topology',
                            components=[pu['ref']], nets=[bus['sda_net'] if net_label == 'SDA' else bus['scl_net']],
                            recommendation=f'Use a pull-up in the {low}-{high} ohm range.',
                            fix_params={'type': 'resistor_value_change', 'component': pu['ref'], 'current_value': pu['ohms'], 'target_range': [low, high], 'suggested_value': 4700},
                            standard_ref='I2C specification UM10204 Table 10',
                            provenance=make_provenance('pr_i2c_spec', 'deterministic'),
                        
                            source=ctx.source,))

        # Address conflict: flag multiple same-IC-type on same bus
        if len(refs) >= 2:
            value_counts: dict[str, list[str]] = {}
            for ref in refs:
                comp = ctx.comp_lookup.get(ref)
                if comp:
                    val = comp.get('value', '').lower()
                    value_counts.setdefault(val, []).append(ref)
            for val, refs_with_val in value_counts.items():
                if len(refs_with_val) > 1:
                    findings.append(make_finding(
                        detector='validate_i2c_bus', rule_id='PR-001', category='protocol_integrity',
                        summary=f'I2C bus: possible address conflict — {len(refs_with_val)}x {val}',
                        description=f'Multiple {val} ({", ".join(refs_with_val)}) on same I2C bus. Verify address pins differ.',
                        severity='warning', confidence='heuristic', evidence_source='topology',
                        components=refs_with_val, nets=[bus['sda_net'], bus['scl_net']],
                        recommendation='Verify address pin configurations (A0/A1/A2) differ.',
                        impact='Address conflict causes bus corruption',
                        provenance=make_provenance('pr_i2c_spec', 'deterministic'),
                    
                        source=ctx.source,))

    return findings


def validate_spi_bus(ctx: AnalysisContext) -> list[dict]:
    """PR-002: Validate SPI bus — CS pull-ups."""
    findings: list[dict] = []
    resistors = get_components_by_type(ctx, 'resistor')
    resistor_nets, net_to_resistors = index_two_pin_components(ctx, resistors)

    for ic in get_unique_ics(ctx):
        ref = ic['reference']
        if not match_ic_keywords(ic, _SPI_IC_KEYWORDS):
            continue
        cs_net = _get_pin_net(ctx, ref, _SPI_CS_NAMES)
        if cs_net and not ctx.is_power_net(cs_net) and not ctx.is_ground(cs_net):
            pullups = _find_pullups_on_net(ctx, cs_net, resistor_nets, net_to_resistors)
            if not pullups:
                findings.append(make_finding(
                    detector='validate_spi_bus', rule_id='PR-002', category='protocol_integrity',
                    summary=f'SPI device {ref}: CS pin ({cs_net}) missing pull-up',
                    description=f'SPI CS on {ref} ({ic.get("value", "")}) net {cs_net} has no pull-up. Device may be inadvertently selected during reset.',
                    severity='warning', confidence='heuristic', evidence_source='topology',
                    components=[ref], nets=[cs_net],
                    recommendation=f'Add a 10k pull-up on {cs_net}.',
                    fix_params={'type': 'add_component', 'components': [{'type': 'resistor', 'value': '10k', 'net_from': cs_net, 'net_to': '<VDD>'}], 'basis': 'SPI CS should be pulled high when not driven'},
                    impact='Device may be selected during reset causing bus contention',
                    provenance=make_provenance('pr_spi_spec', 'deterministic'),
                
                    source=ctx.source,))
    return findings


def validate_can_bus(ctx: AnalysisContext) -> list[dict]:
    """PR-003: Validate CAN bus — termination resistors."""
    findings: list[dict] = []
    resistors = get_components_by_type(ctx, 'resistor')
    resistor_nets, net_to_resistors = index_two_pin_components(ctx, resistors)

    can_transceivers = []
    for ic in get_unique_ics(ctx):
        if match_ic_keywords(ic, _CAN_IC_KEYWORDS):
            ref = ic['reference']
            canh = _get_pin_net(ctx, ref, _CAN_H_NAMES)
            canl = _get_pin_net(ctx, ref, _CAN_L_NAMES)
            if canh or canl:
                can_transceivers.append({'ref': ref, 'value': ic.get('value', ''), 'canh': canh, 'canl': canl})

    for xcvr in can_transceivers:
        canh, canl = xcvr['canh'], xcvr['canl']
        if not canh or not canl:
            continue
        term_found = False
        for rref in net_to_resistors.get(canh, []):
            n1, n2 = resistor_nets.get(rref, (None, None))
            if not n1 or not n2:
                continue
            other = n2 if n1 == canh else n1
            if other == canl:
                ohms = ctx.parsed_values.get(rref)
                if ohms is not None and 100 <= ohms <= 150:
                    term_found = True
                    break
        if not term_found:
            findings.append(make_finding(
                detector='validate_can_bus', rule_id='PR-003', category='protocol_integrity',
                summary=f'CAN transceiver {xcvr["ref"]}: no 120R termination',
                description=f'CAN transceiver {xcvr["ref"]} ({xcvr["value"]}) has no 120R termination between CANH ({canh}) and CANL ({canl}).',
                severity='warning', confidence='deterministic', evidence_source='topology',
                components=[xcvr['ref']], nets=[n for n in [canh, canl] if n],
                recommendation=f'Add a 120R resistor between {canh} and {canl} if at bus end.',
                fix_params={'type': 'add_component', 'components': [{'type': 'resistor', 'value': '120', 'net_from': canh, 'net_to': canl}], 'basis': 'ISO 11898 requires 120R termination'},
                standard_ref='ISO 11898-2 section 7.3', impact='Bus reflections cause communication errors',
                provenance=make_provenance('pr_can_spec', 'deterministic'),
            
                source=ctx.source,))
    return findings


def validate_usb_bus(ctx: AnalysisContext) -> list[dict]:
    """PR-004: Validate USB data lines — series resistors."""
    findings: list[dict] = []
    resistors = get_components_by_type(ctx, 'resistor')
    resistor_nets, net_to_resistors = index_two_pin_components(ctx, resistors)

    for comp in ctx.components:
        if comp['type'] != 'connector':
            continue
        val_lib = (comp.get('value', '') + ' ' + comp.get('lib_id', '')).lower()
        if 'usb' not in val_lib:
            continue
        ref = comp['reference']
        dp_net = _get_pin_net(ctx, ref, _USB_DP_NAMES)
        dm_net = _get_pin_net(ctx, ref, _USB_DM_NAMES)
        if not dp_net and not dm_net:
            continue

        for net_label, net in [('D+', dp_net), ('D-', dm_net)]:
            if not net:
                continue
            series_r = [rref for rref in net_to_resistors.get(net, [])
                        if ctx.parsed_values.get(rref) is not None and 15 <= ctx.parsed_values[rref] <= 33]
            # Check if MCU endpoint has native USB PHY
            mcu_on_net = None
            for p in ctx.nets.get(net, {}).get('pins', []):
                c = ctx.comp_lookup.get(p['component'], {})
                if c.get('type') not in ('connector',) and match_ic_keywords(c, ('esp32', 'stm32', 'rp2040', 'rp2350', 'nrf52', 'samd', 'lpc', 'atm')):
                    mcu_mpn = c.get('mpn') or c.get('value', '')
                    mcu_feat = get_mcu_features(mcu_mpn) if mcu_mpn else None
                    if mcu_feat and not mcu_feat.get('quality', {}).get('trusted', True):
                        mcu_feat = None   # deterministic detectors keep the v1.4 trust gate (v2.0 §3.A.1)
                    if mcu_feat and mcu_feat.get('has_native_usb_phy') is True and mcu_feat.get('usb_series_r_required') is False:
                        mcu_on_net = p['component']
                        break
            if mcu_on_net:
                continue
            if not series_r and 'usb_c' not in val_lib and 'usb3' not in val_lib:
                findings.append(make_finding(
                    detector='validate_usb_bus', rule_id='PR-004', category='protocol_integrity',
                    summary=f'USB connector {ref}: {net_label} ({net}) missing series resistor',
                    description=f'USB {net_label} on {ref} has no series resistor (typically 22R for USB 2.0).',
                    severity='info', confidence='heuristic', evidence_source='topology',
                    components=[ref], nets=[net],
                    recommendation=f'Add a 22R series resistor on {net_label} near the connector.',
                    fix_params={'type': 'add_component', 'components': [{'type': 'resistor', 'value': '22', 'net_from': net, 'net_to': f'{net}_MCU'}], 'basis': 'USB 2.0 recommends 22R series termination'},
                    standard_ref='USB 2.0 specification section 7.1.2',
                    provenance=make_provenance('pr_uart_spec', 'deterministic'),
                
                    source=ctx.source,))
    return findings


# ---------------------------------------------------------------------------
# PS-001: Power sequencing dependency graph
# ---------------------------------------------------------------------------

_ENABLE_PIN_NAMES = ('EN', 'ENABLE', 'CE', 'SHDN', 'ON', 'nSHDN', 'ON_OFF', 'RUN')
_PG_PIN_NAMES = ('PG', 'PGOOD', 'POWER_GOOD', 'nPG', 'PGD', 'POK')

_SEQUENCING_SENSITIVE_KEYWORDS = (
    'stm32', 'esp32', 'nrf52', 'rp2040', 'samd', 'sam3', 'sam4',
    'zynq', 'artix', 'spartan', 'kintex', 'ecp5', 'ice40',
    'ddr', 'lpddr', 'sdram',
    'phy', 'dp83', 'ksz8', 'lan87', 'rtl8',
)


def validate_power_sequencing(
    ctx: AnalysisContext,
    power_regulators: list[dict],
) -> list[dict]:
    """PS-001: Build enable-pin dependency graph and check for sequencing issues."""
    findings: list[dict] = []
    if not power_regulators:
        return findings

    reg_by_output: dict[str, dict] = {}
    reg_by_ref: dict[str, dict] = {}
    for reg in power_regulators:
        ref = reg.get('ref', reg.get('reference', ''))
        output = reg.get('output_rail', '')
        if ref and output:
            reg_by_output[output] = reg
            reg_by_ref[ref] = reg

    enable_edges: list[tuple[str, str]] = []
    for reg in power_regulators:
        ref = reg.get('ref', reg.get('reference', ''))
        en_net = _get_pin_net(ctx, ref, _ENABLE_PIN_NAMES)
        if not en_net:
            continue
        if en_net in reg_by_output:
            enabler = reg_by_output[en_net]
            enabler_ref = enabler.get('ref', enabler.get('reference', ''))
            enable_edges.append((enabler_ref, ref))

    adj: dict[str, list[str]] = {}
    for src, dst in enable_edges:
        adj.setdefault(src, []).append(dst)

    def _has_cycle(start: str) -> list[str] | None:
        visited: set[str] = set()
        path: list[str] = []
        def dfs(node: str) -> list[str] | None:
            if node in visited:
                idx = path.index(node) if node in path else -1
                if idx >= 0:
                    return path[idx:] + [node]
                return None
            visited.add(node)
            path.append(node)
            for nxt in adj.get(node, []):
                cycle = dfs(nxt)
                if cycle:
                    return cycle
            path.pop()
            return None
        return dfs(start)

    reported_cycles: set[str] = set()
    for start in adj:
        cycle = _has_cycle(start)
        if cycle:
            cycle_key = '->'.join(sorted(cycle))
            if cycle_key not in reported_cycles:
                reported_cycles.add(cycle_key)
                findings.append(make_finding(
                    detector='validate_power_sequencing', rule_id='PS-001', category='power_integrity',
                    summary=f'Circular enable dependency: {" -> ".join(cycle)}',
                    description=f'Power regulator enable chain forms a cycle: {" -> ".join(cycle)}. No regulator in the cycle can start.',
                    severity='error', confidence='deterministic', evidence_source='topology',
                    components=list(set(cycle)),
                    recommendation='Break the cycle by connecting one enable pin to an always-on rail.',
                    impact='System fails to power on', report_section='Power Integrity',
                    provenance=make_provenance('ps_sequence_check', 'heuristic'),
                
                    source=ctx.source,))

    for reg in power_regulators:
        ref = reg.get('ref', reg.get('reference', ''))
        output_rail = reg.get('output_rail', '')
        if not output_rail:
            continue
        sensitive_loads = []
        for net_name, net_info in ctx.nets.items():
            if net_name != output_rail:
                continue
            for p in net_info.get('pins', []):
                comp = ctx.comp_lookup.get(p['component'])
                if comp and match_ic_keywords(comp, _SEQUENCING_SENSITIVE_KEYWORDS):
                    sensitive_loads.append(p['component'])
        if not sensitive_loads:
            continue
        comp = ctx.comp_lookup.get(ref, {})
        mpn = comp.get('mpn') or comp.get('value', '')
        ds_feat = get_regulator_features(mpn) if mpn else None
        if ds_feat and not ds_feat.get('quality', {}).get('trusted', True):
            ds_feat = None   # deterministic detectors keep the v1.4 trust gate (v2.0 §3.A.1)
        if ds_feat and ds_feat.get('has_pg') is False:
            continue
        pg_net = _get_pin_net(ctx, ref, _PG_PIN_NAMES)
        if not pg_net:
            if ds_feat is None and mpn:
                findings.append(make_finding(
                    detector='validate_power_sequencing', rule_id='PS-001', category='power_integrity',
                    summary=f'Regulator {ref}: PG status unknown for {mpn} (no datasheet extraction)',
                    description=f'Regulator {ref} ({mpn}) supplies {output_rail} to {", ".join(sensitive_loads[:3])} but PG status is unknown. Run sync_datasheets to verify.',
                    severity='info', confidence='heuristic', evidence_source='topology',
                    components=[ref] + sensitive_loads[:3], nets=[output_rail],
                    recommendation=f'Run sync_datasheets to verify whether {mpn} has a PG pin.',
                    report_section='Power Integrity', impact='Downstream devices may latch up or boot incorrectly',
                    provenance=make_provenance('ps_sequence_check', 'heuristic'),
                
                    source=ctx.source,))
                continue
            findings.append(make_finding(
                detector='validate_power_sequencing', rule_id='PS-001', category='power_integrity',
                summary=f'Regulator {ref}: no power-good feedback, feeds {", ".join(sensitive_loads[:3])}',
                description=f'Regulator {ref} supplies {output_rail} to sequencing-sensitive device(s) ({", ".join(sensitive_loads[:3])}) but has no PG output connected.',
                severity='warning', confidence='heuristic', evidence_source='topology',
                components=[ref] + sensitive_loads[:3], nets=[output_rail],
                recommendation=f'Connect {ref} PG output to downstream regulator enable pins.',
                report_section='Power Integrity', impact='Downstream devices may latch up or boot incorrectly',
                provenance=make_provenance('ps_sequence_check', 'heuristic'),
            
                source=ctx.source,))

    return findings


# ---------------------------------------------------------------------------
# LR-001: LED resistor sizing validation
# ---------------------------------------------------------------------------

_LED_VF_BY_COLOR = {
    'red': 1.8, 'orange': 2.0, 'amber': 2.0, 'yellow': 2.1,
    'green': 2.2, 'blue': 3.2, 'white': 3.2, 'uv': 3.3, 'ir': 1.2,
}
_LED_VF_DEFAULT = 2.0
_LED_IF_MAX_DEFAULT_MA = 20
_LED_IF_RECOMMENDED_MA = 10


def _guess_led_color(value: str, lib_id: str) -> str | None:
    combined = (value + ' ' + lib_id).lower()
    for color in _LED_VF_BY_COLOR:
        if color in combined:
            return color
    return None


def validate_led_resistors(ctx: AnalysisContext) -> list[dict]:
    """LR-001: Check LED current-limiting resistor values."""
    findings: list[dict] = []
    leds = [c for c in ctx.components if c['type'] == 'led']
    if not leds:
        return findings

    resistors = get_components_by_type(ctx, 'resistor')
    resistor_nets, net_to_resistors = index_two_pin_components(ctx, resistors)

    cache_dir = getattr(ctx, 'cache_dir', None)
    design_context = getattr(ctx, 'design_context', None)

    for led in leds:
        ref = led['reference']
        mpn = led.get('mpn') or led.get('value') or ''
        facts = get_facts(mpn, cache_dir=cache_dir) if mpn else None

        # Probe diode.vf and diode.if_max from datasheet facts.
        # DatasheetFacts.diode does not exist in v1.4 (DiodeBlock is v1.5 expansion),
        # so _vf_specs and _if_specs will always be None today — heuristic always fires.
        # The wiring activates automatically once DiodeBlock lands in v1.5 / 4d-active.
        _vf_specs = getattr(getattr(facts, 'diode', None), 'vf', None)
        _if_specs = getattr(getattr(facts, 'diode', None), 'if_max', None)

        ds_vf = best(_vf_specs, min_confidence='medium') if has_data(_vf_specs) else None
        ds_if = best(_if_specs, min_confidence='medium') if has_data(_if_specs) else None

        # If either Vf or If is datasheet-backed, treat the whole finding as datasheet-backed.
        # Per-field fallback is handled below when computing the actual values.
        if ds_vf is not None or ds_if is not None:
            lr_confidence = 'datasheet-backed'
            lr_evidence = 'datasheet'
        else:
            lr_confidence = 'heuristic'
            lr_evidence = 'topology'

        n1, n2 = ctx.get_two_pin_nets(ref)
        if not n1 or not n2:
            continue

        anode_net = cathode_net = None
        if ctx.is_power_net(n1) and not ctx.is_ground(n1):
            anode_net, cathode_net = n1, n2
        elif ctx.is_power_net(n2) and not ctx.is_ground(n2):
            anode_net, cathode_net = n2, n1
        elif ctx.is_ground(n2):
            anode_net, cathode_net = n1, n2
        elif ctx.is_ground(n1):
            anode_net, cathode_net = n2, n1
        else:
            anode_net, cathode_net = n1, n2

        series_resistors = []
        for net in (n1, n2):
            for rref in net_to_resistors.get(net, []):
                rn1, rn2 = resistor_nets.get(rref, (None, None))
                if not rn1 or not rn2:
                    continue
                other = rn2 if rn1 == net else rn1
                if ctx.is_power_net(other) or ctx.is_ground(other):
                    ohms = ctx.parsed_values.get(rref)
                    if ohms is not None and ohms > 0:
                        series_resistors.append({'ref': rref, 'ohms': ohms, 'rail': other})

        if not series_resistors:
            has_driver = False
            for net in (n1, n2):
                for p in ctx.nets.get(net, {}).get('pins', []):
                    comp = ctx.comp_lookup.get(p['component'])
                    if comp and comp['type'] in ('transistor', 'ic'):
                        has_driver = True
                        break
                if has_driver:
                    break
            if not has_driver:
                findings.append(make_finding(
                    detector='validate_led_resistors', rule_id='LR-001', category='component_integrity',
                    summary=f'LED {ref}: no current-limiting resistor found',
                    description=f'LED {ref} ({led.get("value", "")}) has no series current-limiting resistor.',
                    severity='error', confidence=lr_confidence, evidence_source=lr_evidence,
                    components=[ref], nets=[n for n in (n1, n2) if n],
                    recommendation='Add a current-limiting resistor (typically 330R-1k for 3.3V).',
                    fix_params={'type': 'add_component', 'components': [{'type': 'resistor', 'value': '330', 'net_from': n1, 'net_to': n2}], 'basis': 'LED requires series current limiting'},
                    impact='LED overcurrent causes failure',
                    provenance=make_provenance('lr_resistor_check', 'deterministic'),
                    design_context=design_context,
                    schema_era='v1.4',
                    source=ctx.source,))
            continue

        color = _guess_led_color(led.get('value', ''), led.get('lib_id', ''))
        # Use datasheet Vf (typ) if available; fall back to color-heuristic or default.
        if ds_vf is not None and ds_vf.typ is not None:
            vf = ds_vf.typ
        else:
            vf = _LED_VF_BY_COLOR.get(color, _LED_VF_DEFAULT) if color else _LED_VF_DEFAULT
        # Use datasheet If_max (max, else typ) if available; fall back to constant.
        if ds_if is not None and ds_if.max is not None:
            if_max_ma = ds_if.max * 1000  # SpecValue in amps → mA
        elif ds_if is not None and ds_if.typ is not None:
            if_max_ma = ds_if.typ * 1000
        else:
            if_max_ma = _LED_IF_MAX_DEFAULT_MA

        for sr in series_resistors:
            rail_v = parse_voltage_from_net_name(sr['rail'])
            if rail_v is None or rail_v <= vf:
                continue
            current_ma = (rail_v - vf) / sr['ohms'] * 1000

            if current_ma > if_max_ma * 2:
                findings.append(make_finding(
                    detector='validate_led_resistors', rule_id='LR-001', category='component_integrity',
                    summary=f'LED {ref}: current too high ({current_ma:.0f}mA via {sr["ref"]})',
                    description=f'LED {ref} draws ~{current_ma:.0f}mA through {sr["ref"]} ({sr["ohms"]:.0f}R) from {sr["rail"]} ({rail_v}V). Exceeds typical {if_max_ma:.0f}mA max.',
                    severity='warning', confidence=lr_confidence, evidence_source=lr_evidence,
                    components=[ref, sr['ref']], nets=[n for n in (n1, n2) if n],
                    recommendation=f'Increase {sr["ref"]} to {(rail_v - vf) / (_LED_IF_RECOMMENDED_MA / 1000):.0f}R for ~{_LED_IF_RECOMMENDED_MA}mA.',
                    fix_params={'type': 'resistor_value_change', 'component': sr['ref'], 'current_value': sr['ohms'], 'target_metric': 'led_current_mA', 'target_value': _LED_IF_RECOMMENDED_MA, 'actual_value': current_ma, 'formula': f'R = (Vrail - Vf) / Iled = ({rail_v} - {vf}) / {_LED_IF_RECOMMENDED_MA/1000}'},
                    impact='LED overcurrent reduces lifespan',
                    provenance=make_provenance('lr_resistor_check', 'deterministic'),
                    design_context=design_context,
                    schema_era='v1.4',
                    source=ctx.source,))

            power_w = (current_ma / 1000) ** 2 * sr['ohms']
            if power_w > 0.25:
                findings.append(make_finding(
                    detector='validate_led_resistors', rule_id='LR-001', category='component_integrity',
                    summary=f'LED resistor {sr["ref"]}: power dissipation {power_w*1000:.0f}mW',
                    description=f'Resistor {sr["ref"]} dissipates {power_w*1000:.0f}mW. Exceeds 250mW typical for small packages.',
                    severity='info', confidence=lr_confidence, evidence_source=lr_evidence,
                    components=[sr['ref']],
                    recommendation='Use a larger package resistor or increase resistance.',
                    provenance=make_provenance('lr_resistor_check', 'deterministic'),
                    design_context=design_context,
                    schema_era='v1.4',
                    source=ctx.source,))

    return findings


# ---------------------------------------------------------------------------
# XT-001: Crystal load capacitance mismatch
# ---------------------------------------------------------------------------

def validate_crystal_load_caps(
    ctx: AnalysisContext,
    crystal_circuits: list[dict],
) -> list[dict]:
    """XT-001: Emit findings when crystal load capacitance is out_of_spec or marginal.

    Reads pre-computed fields from detect_crystal_circuits() output:
    - load_cap_status: 'ok' | 'marginal' | 'unverified' | 'out_of_spec'
    - target_load_source: 'datasheet' | 'parsed_from_value' | 'frequency_default'
    - effective_load_pF, target_load_pF, load_cap_error_pct

    XT-001 fires only for 'out_of_spec' and 'marginal'; 'ok' and 'unverified' are silent.
    Confidence/evidence_source tracks the target_load_source.
    """
    findings: list[dict] = []
    design_context = getattr(ctx, 'design_context', None)

    for xc in crystal_circuits:
        status = xc.get('load_cap_status')
        if status not in ('out_of_spec', 'marginal'):
            continue

        ref = xc.get('reference', '')
        target_load_source = xc.get('target_load_source')
        effective_pF = xc.get('effective_load_pF')
        target_pF = xc.get('target_load_pF')
        error_pct = xc.get('load_cap_error_pct')

        if target_load_source == 'datasheet':
            xt_confidence = 'datasheet-backed'
            xt_evidence = 'datasheet'
        else:
            xt_confidence = 'heuristic'
            xt_evidence = 'topology'

        severity = 'warning' if status == 'out_of_spec' else 'info'

        load_caps = xc.get('load_caps', [])
        cap_refs = [lc['ref'] for lc in load_caps]

        error_str = f'{error_pct:+.1f}%' if error_pct is not None else 'unknown'
        eff_str = f'{effective_pF:.1f}pF' if effective_pF is not None else 'unknown'
        tgt_str = f'{target_pF:.1f}pF' if target_pF is not None else 'unknown'
        src_label = {'datasheet': 'datasheet', 'parsed_from_value': 'value string', 'frequency_default': 'frequency default'}.get(target_load_source or '', target_load_source or 'unknown')

        findings.append(make_finding(
            detector='validate_crystal_load_caps',
            rule_id='XT-001',
            category='timing',
            summary=f'Crystal {ref}: load capacitance {status.replace("_", " ")} ({eff_str} vs {tgt_str} target)',
            description=(
                f'Crystal {ref} effective load capacitance is {eff_str} '
                f'({error_str} from {tgt_str} target from {src_label}). '
                f'Mismatched CL shifts oscillation frequency and may cause marginal startup.'
            ),
            severity=severity,
            confidence=xt_confidence,
            evidence_source=xt_evidence,
            components=[ref] + cap_refs,
            nets=[lc['net'] for lc in load_caps],
            recommendation=(
                f'Adjust load capacitors so CL_eff = (C1*C2)/(C1+C2) + C_stray ≈ {tgt_str}. '
                f'Typical C_stray is 3-5pF.'
            ),
            provenance=make_provenance('xtal_load_cap_check', xt_confidence),
            design_context=design_context,
            schema_era='v1.4',
            source=ctx.source,
        ))

    return findings


# ---------------------------------------------------------------------------
# FS-001: Feedback network stability pre-check
# ---------------------------------------------------------------------------

_REQUIRES_COMPENSATION_KEYWORDS = (
    'lm2596', 'lm2576',
    'tps5430', 'tps5450', 'tps54', 'tps40',
    'lm259', 'lm317', 'lm337', 'lm350',
    'lt308', 'lt108',
    'mc34', 'mc33',
    'uc384', 'uc282',
)

# Internally-compensated regulators — no external compensation needed.
# Checked BEFORE _REQUIRES_COMPENSATION_KEYWORDS so wins over broad matches
# like 'tps54' (which catches TPS54302's D-CAP2 part by accident). rc.2 4.1
# expansion (Manas review).
_INTERNALLY_COMPENSATED_KEYWORDS = (
    'tps54302',                # TI D-CAP2 (already a more-specific 'tps54' match)
    'tps62',                   # TI TPS62xxx DCS-Control family
    'mpm3833',                 # MPS POL module
    'ap6',                     # Diodes Inc. AP6xxx synchronous buck family
)

_FB_PIN_NAMES = ('FB', 'VFEEDBACK', 'VFB', 'ADJ', 'VADJ', 'COMP', 'VSEN')

_FB_IMPEDANCE_MIN = 1000
_FB_IMPEDANCE_MAX = 1000000


def validate_feedback_stability(
    ctx: AnalysisContext,
    power_regulators: list[dict],
) -> list[dict]:
    """FS-001: Check regulator feedback networks for stability concerns."""
    findings: list[dict] = []
    cache_dir = getattr(ctx, 'cache_dir', None)
    design_context = getattr(ctx, 'design_context', None)

    for reg in power_regulators:
        ref = reg.get('ref', reg.get('reference', ''))
        fb_div = reg.get('feedback_divider')
        if not fb_div:
            continue

        r_top = fb_div.get('r_top', {}).get('ohms')
        r_bottom = fb_div.get('r_bottom', {}).get('ohms')
        if r_top is None or r_bottom is None:
            continue

        parallel_impedance = (r_top * r_bottom) / (r_top + r_bottom) if (r_top + r_bottom) > 0 else 0

        # 4b lookup wiring: probe regulator facts (currently informational only;
        # validation logic stays heuristic). Future v1.5/4d-active will validate
        # cout_min and esr_range against schematic when datasheet provides them.
        mpn = reg.get('mpn') or ''
        if not mpn:
            comp_entry = ctx.comp_lookup.get(ref)
            mpn = (comp_entry.get('mpn') if comp_entry else '') or ''
        facts = get_facts(mpn, cache_dir=cache_dir) if mpn else None
        # facts probe is informational — confidence stays heuristic regardless.

        if parallel_impedance < _FB_IMPEDANCE_MIN:
            findings.append(make_finding(
                detector='validate_feedback_stability', rule_id='FS-001', category='power_integrity',
                summary=f'Regulator {ref}: feedback divider impedance too low ({parallel_impedance:.0f}R)',
                description=f'Feedback divider for {ref} has parallel impedance of {parallel_impedance:.0f} ohms. Low impedance wastes quiescent current.',
                severity='info', confidence='heuristic', evidence_source='topology',
                components=[ref, fb_div['r_top'].get('ref', ''), fb_div['r_bottom'].get('ref', '')],
                recommendation=f'Increase divider resistors to achieve >{_FB_IMPEDANCE_MIN} ohm parallel impedance.',
                provenance=make_provenance('fs_stability_check', 'heuristic'),
                design_context=design_context,
                schema_era='v1.4',
                source=ctx.source,))

        if parallel_impedance > _FB_IMPEDANCE_MAX:
            findings.append(make_finding(
                detector='validate_feedback_stability', rule_id='FS-001', category='power_integrity',
                summary=f'Regulator {ref}: feedback divider impedance too high ({parallel_impedance/1000:.0f}k)',
                description=f'Feedback divider for {ref} has parallel impedance of {parallel_impedance/1000:.0f}k ohms. High impedance is noise-susceptible.',
                severity='warning', confidence='heuristic', evidence_source='topology',
                components=[ref, fb_div['r_top'].get('ref', ''), fb_div['r_bottom'].get('ref', '')],
                recommendation=f'Decrease divider resistors to below {_FB_IMPEDANCE_MAX/1000:.0f}k parallel impedance.',
                provenance=make_provenance('fs_stability_check', 'heuristic'),
                design_context=design_context,
                schema_era='v1.4',
                source=ctx.source,))

        comp = ctx.comp_lookup.get(ref)
        if (comp and match_ic_keywords(comp, _REQUIRES_COMPENSATION_KEYWORDS)
                and not match_ic_keywords(comp, _INTERNALLY_COMPENSATED_KEYWORDS)):
            fb_net = _get_pin_net(ctx, ref, _FB_PIN_NAMES)
            comp_net = _get_pin_net(ctx, ref, ('COMP', 'CC', 'RC'))
            check_net = comp_net or fb_net
            if check_net:
                caps_on_fb = [p['component'] for p in ctx.nets.get(check_net, {}).get('pins', [])
                              if ctx.comp_lookup.get(p['component'], {}).get('type') == 'capacitor']
                if not caps_on_fb:
                    findings.append(make_finding(
                        detector='validate_feedback_stability', rule_id='FS-001', category='power_integrity',
                        summary=f'Regulator {ref}: missing compensation capacitor',
                        description=f'Regulator {ref} ({comp.get("value", "")}) typically requires external compensation on {check_net}.',
                        severity='warning', confidence='heuristic', evidence_source='heuristic_rule',
                        components=[ref], nets=[check_net],
                        recommendation=f'Add a compensation network per {comp.get("value", "")} datasheet.',
                        fix_params={'type': 'add_component', 'components': [{'type': 'capacitor', 'value': '10n', 'net_from': check_net, 'net_to': 'GND'}], 'basis': f'{comp.get("value", "")} requires external compensation'},
                        impact='Regulator may oscillate or have poor transient response',
                        provenance=make_provenance('fs_stability_check', 'heuristic'),
                        design_context=design_context,
                        schema_era='v1.4',
                        source=ctx.source,))

    return findings
