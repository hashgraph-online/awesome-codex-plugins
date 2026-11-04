"""Schematic analysis pipeline: the phases analyze_schematic.py ran implicitly,
as named functions with their real prerequisites passed explicitly (spec §4.3, D4).

Phase 1 detect_topologies      — in-order detectors (dependency order; series dividers merged, integrated LDOs appended;
                                  opamps before RC filters; exclusion sets passed as arguments)
Phase 2 reconcile_detections   — MUTATES phase-1 records: postfilter_vd_and_dedup rebinds the
                                  divider/feedback lists; enrich_transistor_led_drivers rewrites
                                  transistor records in place (detector/rule_id/category/summary)
Phase 3 run_domain_detectors   — domain, validation and lookup detectors; RS/PP audits share
                                  one BridgeFacts
Phase 4 assemble_signal_results — crystal/RC exclusion (after ADC detection consumed rc_filters),
                                  the signal_analysis dict in its historical key order,
                                  certifications/observations, capacitor enrichment + derating
                                  (both walk the dict recursively and MUTATE entries that carry
                                  'farads' and 'ref')
Project level: analyze_schematic → run_analyses → presentation.assemble_result.
Every body is verbatim from analyze_schematic.py; only the seams are new.
"""

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from kicad_core.diagnostics import merge, record
from kicad_core.sexp import parse_file
from kicad_core.values import snap_to_mil_grid as _snap_mil
from kicad_core.netnames import _clean_hierarchical_name
from kicad_core.netquery import (
    build_bridge_facts,
    build_ref_pins,
)
from schematic.reader import (
    compute_pin_positions,
    detect_sub_sheet,
)
from schematic.legacy_reader import (
    _resolve_legacy_libs,
    _snap_pins_to_wires,
    _parse_legacy_single_sheet,
)
from kicad_types import (
    AnalysisContext,
    build_analysis_context,
)
from schematic.connectivity import build_net_map
from schematic.hierarchy import (
    parse_all_sheets,
    merge_top_level_sheets,
)
from schematic.ic_analysis import (
    analyze_ic_pinouts,
    identify_subcircuits,
)
from schematic.net_analysis import (
    analyze_connectivity,
    analyze_design_rules,
    _estimate_rail_voltage,
)
from schematic.audits import (
    check_annotation_completeness,
    validate_label_shapes,
    audit_pwr_flags,
    validate_footprint_filters,
    audit_datasheet_coverage,
    audit_sourcing_fields,
    audit_sourcing_gate,
    audit_dnp_rate,
    check_generic_transistor_symbols,
    summarize_alternate_pins,
    classify_ground_domains,
    analyze_bus_topology,
    analyze_wire_geometry,
    check_simulation_readiness,
    audit_property_patterns,
    spatial_clustering,
    verify_pin_coverage,
    check_instance_consistency,
    validate_hierarchical_labels,
)
from schematic.system_analyses import (
    analyze_pdn_impedance,
    analyze_sleep_current,
    analyze_voltage_derating,
    analyze_protocol_compliance,
    analyze_power_budget,
    analyze_power_sequencing,
    analyze_bom_optimization,
    analyze_test_coverage,
    analyze_assembly_complexity,
    analyze_usb_compliance,
    analyze_inrush_current,
)
from schematic.bom_stats import (
    generate_bom,
    compute_statistics,
)
from signal_detectors import (
    audit_power_pin_dc_paths,
    audit_rail_sources,
    detect_bridge_circuits,
    detect_crystal_circuits,
    detect_current_sense,
    detect_decoupling,
    detect_design_observations,
    detect_integrated_ldos,
    detect_label_aliases,
    detect_lc_filters,
    enrich_transistor_led_drivers,
    detect_opamp_circuits,
    detect_power_regulators,
    detect_protection_devices,
    detect_rc_filters,
    detect_shorted_two_pin_components,
    detect_solder_jumpers,
    detect_transistor_circuits,
    detect_voltage_dividers,
    postfilter_vd_and_dedup,
    _merge_series_dividers,
)
from domain_detectors import (
    audit_connector_ground_distribution,
    audit_esd_protection,
    audit_led_circuits,
    detect_adc_circuits,
    detect_addressable_leds,
    detect_audio_circuits,
    detect_battery_chargers,
    detect_bms_systems,
    detect_buzzer_speakers,
    detect_clock_distribution,
    detect_debug_interfaces,
    detect_display_interfaces,
    detect_ethernet_interfaces,
    detect_hdmi_dvi_interfaces,
    detect_isolation_barriers,
    detect_key_matrices,
    detect_lvds_interfaces,
    detect_led_driver_ics,
    detect_level_shifters,
    detect_memory_interfaces,
    detect_motor_drivers,
    detect_power_path,
    detect_reset_supervisors,
    detect_rf_chains,
    detect_rf_matching,
    detect_rtc_circuits,
    detect_sensor_interfaces,
    detect_thermocouple_rtd,
    suggest_certifications,
    build_power_sequencing_graph,
    detect_wireless_modules,
    detect_transformer_feedback,
    detect_i2c_address_conflicts,
    detect_energy_harvesting,
    detect_pwm_led_dimming,
    detect_headphone_jack,
)
from validation_detectors import (
    validate_pullups,
    validate_voltage_levels,
    validate_i2c_bus,
    validate_spi_bus,
    validate_can_bus,
    validate_usb_bus,
    validate_power_sequencing as validate_power_seq_deps,
    validate_led_resistors,
    validate_feedback_stability,
    validate_crystal_load_caps,
)
from lookup_detectors import (
    detect_absolute_max_violations,
    detect_vcc_outside_recommended,
    detect_5v_on_non_tolerant_pin,
    detect_wrong_signal_type,
    detect_missing_required_components,
)
from schematic.presentation import assemble_legacy_result, assemble_result
from finding_schema import assign_finding_ids


def _resolve_lookup_paths(sch_path: str | Path,
                           analysis_dir: str | Path | None) -> Path | None:
    """Resolve the datasheets/extracted/ cache dir adjacent to the schematic.

    Returns None when the directory doesn't exist — `lookup()` already handles
    None gracefully. (The design_context severity channel this used to
    resolve was retired in v2.0; v3 removed the plumbing.)
    """
    sch_dir = Path(sch_path).resolve().parent
    candidates = [
        sch_dir / "datasheets" / "extracted",
        sch_dir.parent / "datasheets" / "extracted",
    ]
    return next((c for c in candidates if c.is_dir()), None)

ANALYZER_SOURCE = "sch"

MAX_TESTED_FORMAT_VERSION = 20260306  # bump when a newer corpus era is adopted


def _build_net_classifications(results: dict) -> dict[str, dict]:
    """Build net classification dict from existing detector results.

    Tags nets with signal type and characteristics for downstream PCB
    intelligence checks. Uses the 'nets' field from rich-format detections
    plus domain-specific fields where available.
    """
    classifications: dict[str, dict] = {}

    # Crystal circuits → clock nets (from load_cap nets and rich 'nets' field)
    for xc in results.get('crystal_circuits', []):
        freq = xc.get('frequency')
        # Rich format 'nets' field contains the crystal's connected nets
        for net in xc.get('nets', []):
            if net and net not in classifications:
                classifications[net] = {'type': 'clock', 'frequency_hz': freq, 'source': 'crystal_circuits'}
        # Load cap nets are clock-passive
        for lc in xc.get('load_caps', []):
            net = lc.get('net')
            if net and net not in classifications:
                classifications[net] = {'type': 'clock_passive', 'source': 'crystal_circuits'}

    # Power regulators → switching nodes and power rails
    for reg in results.get('power_regulators', []):
        sw_net = reg.get('sw_net')
        if sw_net:
            classifications[sw_net] = {'type': 'switching_node', 'frequency_hz': reg.get('switching_frequency_hz'), 'source': 'power_regulators'}
        output_rail = reg.get('output_rail')
        if output_rail and output_rail not in classifications:
            classifications[output_rail] = {'type': 'power_rail', 'source': 'power_regulators'}

    # Ethernet → differential nets (from rich 'nets' or domain-specific fields)
    for eth in results.get('ethernet_interfaces', []):
        # Try domain-specific differential net fields first
        for key in ('tx_p', 'tx_n', 'rx_p', 'rx_n', 'txp', 'txn', 'rxp', 'rxn'):
            net = eth.get(key)
            if net:
                classifications[net] = {'type': 'ethernet', 'differential': True, 'source': 'ethernet_interfaces'}
        # Fall back to rich 'nets' field
        for net in eth.get('nets', []):
            if net and net not in classifications:
                classifications[net] = {'type': 'ethernet', 'source': 'ethernet_interfaces'}

    # HDMI/DVI
    for hdmi in results.get('hdmi_dvi_interfaces', []):
        for net in hdmi.get('nets', []):
            if net and net not in classifications:
                classifications[net] = {'type': 'hdmi', 'differential': True, 'source': 'hdmi_dvi_interfaces'}

    # Memory interfaces
    for mem in results.get('memory_interfaces', []):
        for net in mem.get('nets', []):
            if net and net not in classifications:
                classifications[net] = {'type': 'memory', 'source': 'memory_interfaces'}

    # LVDS
    for lvds in results.get('lvds_interfaces', []):
        for net in lvds.get('nets', []):
            if net and net not in classifications:
                classifications[net] = {'type': 'lvds', 'differential': True, 'source': 'lvds_interfaces'}

    # RF chains
    for rf in results.get('rf_chains', []):
        for net in rf.get('nets', []):
            if net and net not in classifications:
                classifications[net] = {'type': 'rf', 'source': 'rf_chains'}

    # Clock distribution
    for clk in results.get('clock_distribution', []):
        freq = clk.get('frequency_hz')
        for net in clk.get('nets', []):
            if net and net not in classifications:
                classifications[net] = {'type': 'clock', 'frequency_hz': freq, 'source': 'clock_distribution'}

    # Validation findings → protocol nets (I2C, CAN, USB)
    for vf in results.get('validation_findings', []):
        rule = vf.get('rule_id', '')
        nets = vf.get('nets', [])
        if rule == 'PR-001':
            for net in nets:
                if net not in classifications:
                    classifications[net] = {'type': 'i2c', 'source': 'protocol_detection'}
        elif rule == 'PR-003':
            for net in nets:
                if net not in classifications:
                    classifications[net] = {'type': 'can', 'differential': True, 'source': 'protocol_detection'}
        elif rule == 'PR-004':
            for net in nets:
                if net not in classifications:
                    classifications[net] = {'type': 'usb', 'differential': True, 'source': 'protocol_detection'}

    return classifications


def detect_topologies(ctx: AnalysisContext) -> dict:
    """Phase 1: topology detectors in dependency order.

    Returns the phase-1 records keyed by their historical local names.
    """
    nets = ctx.nets

    # Run detectors in dependency order
    vd_result = detect_voltage_dividers(ctx)
    voltage_dividers = vd_result["voltage_dividers"]
    # KH-105/KH-115: Merge series resistors in divider chains
    voltage_dividers = _merge_series_dividers(voltage_dividers, ctx)
    feedback_networks = vd_result["feedback_networks"]

    lc_filters = detect_lc_filters(ctx)
    crystal_circuits = detect_crystal_circuits(ctx)
    # KH-145: Detect opamps BEFORE RC filters so feedback components can be excluded
    opamp_circuits = detect_opamp_circuits(ctx)
    # KH-107: Pass crystal_circuits to exclude crystal R/C from RC filter detection
    # KH-145: Pass opamp_circuits to exclude feedback R+C from RC filter detection
    rc_filters = detect_rc_filters(ctx, voltage_dividers, crystal_circuits, opamp_circuits)
    decoupling_analysis = detect_decoupling(ctx)
    current_sense = detect_current_sense(ctx)
    power_regulators = detect_power_regulators(ctx, voltage_dividers)
    integrated_ldos = detect_integrated_ldos(ctx, power_regulators)
    power_regulators.extend(integrated_ldos)

    # Build rail_voltages: net name → voltage from regulator outputs + power symbol names
    rail_voltages: dict[str, float] = {}
    for reg in power_regulators:
        out_rail = reg.get("output_rail")
        v_out = reg.get("estimated_vout")
        if out_rail and v_out is not None:
            rail_voltages[_clean_hierarchical_name(out_rail)] = v_out
    # Augment with voltages inferred from power symbol / net names
    for net_name in ctx.nets:
        clean = _clean_hierarchical_name(net_name)
        if clean not in rail_voltages:
            v = _estimate_rail_voltage(clean)
            if v is not None:
                rail_voltages[clean] = v

    protection_devices = detect_protection_devices(ctx)
    bridge_circuits, matched_fets, fet_pins = detect_bridge_circuits(ctx)
    transistor_circuits = detect_transistor_circuits(ctx, matched_fets, fet_pins)

    return {
        "rail_voltages": rail_voltages,
        "voltage_dividers": voltage_dividers,
        "feedback_networks": feedback_networks,
        "lc_filters": lc_filters,
        "crystal_circuits": crystal_circuits,
        "opamp_circuits": opamp_circuits,
        "rc_filters": rc_filters,
        "decoupling_analysis": decoupling_analysis,
        "current_sense": current_sense,
        "power_regulators": power_regulators,
        "protection_devices": protection_devices,
        "bridge_circuits": bridge_circuits,
        "matched_fets": matched_fets,
        "fet_pins": fet_pins,
        "transistor_circuits": transistor_circuits,
    }


def reconcile_detections(ctx: AnalysisContext, topo: dict) -> None:
    """Phase 2: cross-detector post-processing. MUTATES *topo* in place.

    postfilter_vd_and_dedup rebinds topo["voltage_dividers"] and
    topo["feedback_networks"]; enrich_transistor_led_drivers rewrites the
    records in topo["transistor_circuits"] in place.
    """
    voltage_dividers = topo["voltage_dividers"]
    feedback_networks = topo["feedback_networks"]
    transistor_circuits = topo["transistor_circuits"]

    # Post-processing that needs cross-detector data
    voltage_dividers, feedback_networks = postfilter_vd_and_dedup(
        voltage_dividers, feedback_networks, transistor_circuits, nets=ctx.nets)
    enrich_transistor_led_drivers(ctx, transistor_circuits)

    topo["voltage_dividers"] = voltage_dividers
    topo["feedback_networks"] = feedback_networks


def run_domain_detectors(ctx: AnalysisContext, topo: dict) -> dict:
    """Phase 3: domain, validation and lookup detectors (reads *topo*, does not rebind it).

    Returns the phase-3 records keyed by their historical local names.
    """
    rail_voltages = topo["rail_voltages"]
    crystal_circuits = topo["crystal_circuits"]
    rc_filters = topo["rc_filters"]
    power_regulators = topo["power_regulators"]
    protection_devices = topo["protection_devices"]
    transistor_circuits = topo["transistor_circuits"]

    buzzer_speaker_circuits = detect_buzzer_speakers(ctx, transistor_circuits)
    key_matrices = detect_key_matrices(ctx)
    isolation_barriers = detect_isolation_barriers(ctx)
    ethernet_interfaces = detect_ethernet_interfaces(ctx)
    hdmi_dvi_interfaces = detect_hdmi_dvi_interfaces(ctx)
    lvds_interfaces = detect_lvds_interfaces(ctx)
    memory_interfaces = detect_memory_interfaces(ctx)
    rf_chains = detect_rf_chains(ctx)
    rf_matching = detect_rf_matching(ctx)
    bms_systems = detect_bms_systems(ctx)
    battery_chargers = detect_battery_chargers(ctx)
    motor_drivers = detect_motor_drivers(ctx)
    addressable_led_chains = detect_addressable_leds(ctx)
    debug_interfaces = detect_debug_interfaces(ctx)
    power_path = detect_power_path(ctx)
    esd_coverage_audit = audit_esd_protection(ctx, protection_devices)
    adc_circuits = detect_adc_circuits(ctx, rc_filters, protection_devices)
    reset_supervisors = detect_reset_supervisors(ctx)
    clock_distribution = detect_clock_distribution(ctx, crystal_circuits)
    display_interfaces = detect_display_interfaces(ctx)
    sensor_interfaces = detect_sensor_interfaces(ctx)
    level_shifters = detect_level_shifters(ctx)
    audio_circuits = detect_audio_circuits(ctx)
    led_driver_ics = detect_led_driver_ics(ctx)
    rtc_circuits = detect_rtc_circuits(ctx, crystal_circuits)
    led_audit = audit_led_circuits(ctx, transistor_circuits)
    thermocouple_rtd = detect_thermocouple_rtd(ctx)
    power_sequencing_validation = build_power_sequencing_graph(
        ctx, power_regulators, power_path, reset_supervisors)
    connector_ground_audit = audit_connector_ground_distribution(ctx)

    # Validation detectors (rich findings)
    pullup_findings = validate_pullups(ctx)
    voltage_level_findings = validate_voltage_levels(ctx, level_shifters)
    i2c_findings = validate_i2c_bus(ctx)
    spi_findings = validate_spi_bus(ctx)
    can_findings = validate_can_bus(ctx)
    usb_findings = validate_usb_bus(ctx)
    power_seq_dep_findings = validate_power_seq_deps(ctx, power_regulators)
    led_resistor_findings = validate_led_resistors(ctx)
    feedback_stability_findings = validate_feedback_stability(ctx, power_regulators)
    crystal_load_findings = validate_crystal_load_caps(ctx, crystal_circuits)

    # Lookup detectors (Phase 4c) — consume v1.4 datasheet facts via lookup().
    # Soft-skip when get_facts() returns None (no MPN cache). Synonym-resolved
    # rail keys per addendum §A2; per-pin Pin.absolute_max overrides rail-level.
    am_001_findings = detect_absolute_max_violations(ctx, rail_voltages)
    ov_001_findings = detect_vcc_outside_recommended(ctx, rail_voltages)
    ft_001_findings = detect_5v_on_non_tolerant_pin(ctx, rail_voltages)
    pm_001_findings = detect_wrong_signal_type(ctx)
    ex_001_findings = detect_missing_required_components(ctx, power_regulators)

    # New domain detectors (rich format)
    wireless_modules = detect_wireless_modules(ctx)
    transformer_feedback = detect_transformer_feedback(ctx)
    i2c_address_conflicts = detect_i2c_address_conflicts(ctx)
    energy_harvesting = detect_energy_harvesting(ctx)
    pwm_led_dimming = detect_pwm_led_dimming(ctx, transistor_circuits)
    headphone_jacks = detect_headphone_jack(ctx)
    solder_jumpers = detect_solder_jumpers(ctx)
    bridge_facts = build_bridge_facts(
        ctx.components, build_ref_pins(ctx.nets), solder_jumpers)
    shorted_two_pin_components = detect_shorted_two_pin_components(ctx)
    rail_source_audit = audit_rail_sources(
        ctx, power_regulators=power_regulators, solder_jumpers=solder_jumpers,
        bridge_facts=bridge_facts)
    label_aliases = detect_label_aliases(ctx)
    power_pin_dc_paths = audit_power_pin_dc_paths(
        ctx, solder_jumpers=solder_jumpers, bridge_facts=bridge_facts)

    return {
        "buzzer_speaker_circuits": buzzer_speaker_circuits,
        "key_matrices": key_matrices,
        "isolation_barriers": isolation_barriers,
        "ethernet_interfaces": ethernet_interfaces,
        "hdmi_dvi_interfaces": hdmi_dvi_interfaces,
        "lvds_interfaces": lvds_interfaces,
        "memory_interfaces": memory_interfaces,
        "rf_chains": rf_chains,
        "rf_matching": rf_matching,
        "bms_systems": bms_systems,
        "battery_chargers": battery_chargers,
        "motor_drivers": motor_drivers,
        "addressable_led_chains": addressable_led_chains,
        "debug_interfaces": debug_interfaces,
        "power_path": power_path,
        "esd_coverage_audit": esd_coverage_audit,
        "adc_circuits": adc_circuits,
        "reset_supervisors": reset_supervisors,
        "clock_distribution": clock_distribution,
        "display_interfaces": display_interfaces,
        "sensor_interfaces": sensor_interfaces,
        "level_shifters": level_shifters,
        "audio_circuits": audio_circuits,
        "led_driver_ics": led_driver_ics,
        "rtc_circuits": rtc_circuits,
        "led_audit": led_audit,
        "thermocouple_rtd": thermocouple_rtd,
        "power_sequencing_validation": power_sequencing_validation,
        "connector_ground_audit": connector_ground_audit,
        "pullup_findings": pullup_findings,
        "voltage_level_findings": voltage_level_findings,
        "i2c_findings": i2c_findings,
        "spi_findings": spi_findings,
        "can_findings": can_findings,
        "usb_findings": usb_findings,
        "power_seq_dep_findings": power_seq_dep_findings,
        "led_resistor_findings": led_resistor_findings,
        "feedback_stability_findings": feedback_stability_findings,
        "crystal_load_findings": crystal_load_findings,
        "am_001_findings": am_001_findings,
        "ov_001_findings": ov_001_findings,
        "ft_001_findings": ft_001_findings,
        "pm_001_findings": pm_001_findings,
        "ex_001_findings": ex_001_findings,
        "wireless_modules": wireless_modules,
        "transformer_feedback": transformer_feedback,
        "i2c_address_conflicts": i2c_address_conflicts,
        "energy_harvesting": energy_harvesting,
        "pwm_led_dimming": pwm_led_dimming,
        "headphone_jacks": headphone_jacks,
        "solder_jumpers": solder_jumpers,
        "shorted_two_pin_components": shorted_two_pin_components,
        "rail_source_audit": rail_source_audit,
        "label_aliases": label_aliases,
        "power_pin_dc_paths": power_pin_dc_paths,
    }


def enrich_capacitor_records(results_dict, context):
    """Add package size, ESR, dielectric, and rated voltage to all cap entries.

    Walks through all detection dicts recursively, finds entries with a 'farads'
    key and a 'ref' key, and adds derived fields from the component's footprint
    and value string.
    """
    from kicad_core.passives import (extract_cap_package, estimate_cap_esr,
                                     classify_dielectric)
    from kicad_core.values import parse_rated_voltage

    def _enrich(obj):
        if isinstance(obj, dict):
            if "farads" in obj and "ref" in obj:
                ref = obj["ref"]
                comp = context.comp_lookup.get(ref)
                if comp:
                    # Package and ESR (existing)
                    if "package" not in obj:
                        fp = comp.get("footprint", "")
                        pkg = extract_cap_package(fp)
                        if pkg:
                            obj["package"] = pkg
                            esr = estimate_cap_esr(obj["farads"], pkg)
                            if esr is not None:
                                obj["esr_ohm"] = esr
                    # Dielectric classification (new)
                    if "dielectric" not in obj:
                        value_str = comp.get("value", "")
                        desc_str = comp.get("description", "")
                        obj["dielectric"] = classify_dielectric(value_str, desc_str)
                    # Rated voltage (new)
                    if "rated_voltage_V" not in obj:
                        value_str = comp.get("value", "")
                        rv = parse_rated_voltage(value_str)
                        if rv is not None:
                            obj["rated_voltage_V"] = rv
            for v in obj.values():
                _enrich(v)
        elif isinstance(obj, list):
            for item in obj:
                _enrich(item)

    _enrich(results_dict)


def apply_capacitor_derating(results_dict):
    """Apply DC bias derating to capacitor entries where applied voltage is known.

    Cross-references regulator output voltages with output_capacitors and
    decoupling_analysis to compute effective_farads after DC bias derating.
    Only adds derating fields when both package and applied voltage are known.
    """
    from kicad_core.passives import estimate_dc_bias_derating

    # Build rail → voltage map from power regulators
    rail_voltage = {}
    for reg in results_dict.get("power_regulators", []):
        vout = reg.get("vout_estimated") or reg.get("estimated_vout")
        rail = reg.get("output_rail", "")
        if vout and vout > 0 and rail:
            # Use the highest voltage seen for a rail (conservative)
            if rail not in rail_voltage or vout > rail_voltage[rail]:
                rail_voltage[rail] = vout

    def _derate_cap(cap, applied_v):
        """Add derating fields to a single cap entry."""
        farads = cap.get("farads", 0)
        package = cap.get("package")
        dielectric = cap.get("dielectric")
        if not farads or farads <= 0 or not package or not dielectric:
            return

        # Determine rated voltage: from cap entry, or estimate from rail
        rated_v = cap.get("rated_voltage_V")
        if rated_v is None:
            # Conservative estimate based on typical voltage ratings
            if applied_v <= 1.8:
                rated_v = 6.3
            elif applied_v <= 3.3:
                rated_v = 6.3
            elif applied_v <= 5.0:
                rated_v = 10.0
            elif applied_v <= 12.0:
                rated_v = 25.0
            else:
                rated_v = applied_v * 2  # assume 2:1 margin

        voltage_ratio = applied_v / rated_v
        remaining = estimate_dc_bias_derating(dielectric, package, voltage_ratio)

        cap["applied_voltage_V"] = applied_v
        cap["derating_factor"] = round(remaining, 3)
        cap["effective_farads"] = farads * remaining

    # Derate output and input capacitors on power regulators
    for reg in results_dict.get("power_regulators", []):
        vout = reg.get("vout_estimated") or reg.get("estimated_vout")
        if not vout or vout <= 0:
            continue
        for cap in reg.get("output_capacitors", []):
            _derate_cap(cap, vout)

    # Derate decoupling analysis capacitors
    for rail_entry in results_dict.get("decoupling_analysis", []):
        rail_name = rail_entry.get("rail", "")
        v = rail_voltage.get(rail_name)
        if not v:
            continue
        any_derated = False
        for cap in rail_entry.get("capacitors", []):
            _derate_cap(cap, v)
            if "effective_farads" in cap:
                any_derated = True
        # Add total effective capacitance alongside nominal
        if any_derated:
            total_eff = sum(
                c.get("effective_farads", c["farads"])
                for c in rail_entry["capacitors"]
            )
            rail_entry["total_effective_capacitance_uF"] = round(total_eff * 1e6, 3)

    # Derate LC filter capacitors where rail voltage is known
    for filt in results_dict.get("lc_filters", []):
        rail = filt.get("rail", "")
        v = rail_voltage.get(rail)
        if v and "capacitor" in filt:
            cap = filt["capacitor"]
            if isinstance(cap, dict) and "farads" in cap:
                _derate_cap(cap, v)


def assemble_signal_results(ctx: AnalysisContext, topo: dict, domain: dict) -> dict:
    """Phase 4: crystal/RC exclusion, the signal_analysis dict (historical key order),
    net classifications, certifications, observations, capacitor enrichment + derating.
    """
    rail_voltages = topo["rail_voltages"]
    voltage_dividers = topo["voltage_dividers"]
    feedback_networks = topo["feedback_networks"]
    lc_filters = topo["lc_filters"]
    crystal_circuits = topo["crystal_circuits"]
    opamp_circuits = topo["opamp_circuits"]
    rc_filters = topo["rc_filters"]
    decoupling_analysis = topo["decoupling_analysis"]
    current_sense = topo["current_sense"]
    power_regulators = topo["power_regulators"]
    protection_devices = topo["protection_devices"]
    bridge_circuits = topo["bridge_circuits"]
    transistor_circuits = topo["transistor_circuits"]
    buzzer_speaker_circuits = domain["buzzer_speaker_circuits"]
    key_matrices = domain["key_matrices"]
    isolation_barriers = domain["isolation_barriers"]
    ethernet_interfaces = domain["ethernet_interfaces"]
    hdmi_dvi_interfaces = domain["hdmi_dvi_interfaces"]
    lvds_interfaces = domain["lvds_interfaces"]
    memory_interfaces = domain["memory_interfaces"]
    rf_chains = domain["rf_chains"]
    rf_matching = domain["rf_matching"]
    bms_systems = domain["bms_systems"]
    battery_chargers = domain["battery_chargers"]
    motor_drivers = domain["motor_drivers"]
    addressable_led_chains = domain["addressable_led_chains"]
    debug_interfaces = domain["debug_interfaces"]
    power_path = domain["power_path"]
    esd_coverage_audit = domain["esd_coverage_audit"]
    adc_circuits = domain["adc_circuits"]
    reset_supervisors = domain["reset_supervisors"]
    clock_distribution = domain["clock_distribution"]
    display_interfaces = domain["display_interfaces"]
    sensor_interfaces = domain["sensor_interfaces"]
    level_shifters = domain["level_shifters"]
    audio_circuits = domain["audio_circuits"]
    led_driver_ics = domain["led_driver_ics"]
    rtc_circuits = domain["rtc_circuits"]
    led_audit = domain["led_audit"]
    thermocouple_rtd = domain["thermocouple_rtd"]
    power_sequencing_validation = domain["power_sequencing_validation"]
    connector_ground_audit = domain["connector_ground_audit"]
    pullup_findings = domain["pullup_findings"]
    voltage_level_findings = domain["voltage_level_findings"]
    i2c_findings = domain["i2c_findings"]
    spi_findings = domain["spi_findings"]
    can_findings = domain["can_findings"]
    usb_findings = domain["usb_findings"]
    power_seq_dep_findings = domain["power_seq_dep_findings"]
    led_resistor_findings = domain["led_resistor_findings"]
    feedback_stability_findings = domain["feedback_stability_findings"]
    crystal_load_findings = domain["crystal_load_findings"]
    am_001_findings = domain["am_001_findings"]
    ov_001_findings = domain["ov_001_findings"]
    ft_001_findings = domain["ft_001_findings"]
    pm_001_findings = domain["pm_001_findings"]
    ex_001_findings = domain["ex_001_findings"]
    wireless_modules = domain["wireless_modules"]
    transformer_feedback = domain["transformer_feedback"]
    i2c_address_conflicts = domain["i2c_address_conflicts"]
    energy_harvesting = domain["energy_harvesting"]
    pwm_led_dimming = domain["pwm_led_dimming"]
    headphone_jacks = domain["headphone_jacks"]
    solder_jumpers = domain["solder_jumpers"]
    shorted_two_pin_components = domain["shorted_two_pin_components"]
    rail_source_audit = domain["rail_source_audit"]
    label_aliases = domain["label_aliases"]
    power_pin_dc_paths = domain["power_pin_dc_paths"]

    # Remove R/C components that appear in crystal circuits from RC filter
    # results — prevents misclassifying crystal feedback resistors + load caps
    # as RC filters (e.g., "10M + 22pF = 723Hz RC filter").
    if crystal_circuits and rc_filters:
        xtal_refs = set()
        for xc in crystal_circuits:
            for lc in xc.get("load_caps", []):
                xtal_refs.add(lc["ref"])
            if "feedback_resistor" in xc:
                xtal_refs.add(xc["feedback_resistor"])
        if xtal_refs:
            rc_filters = [
                f for f in rc_filters
                if f.get("resistor", {}).get("reference") not in xtal_refs
                and f.get("capacitor", {}).get("reference") not in xtal_refs
            ]

    results = {
        "rail_voltages": rail_voltages,
        "voltage_dividers": voltage_dividers,
        "rc_filters": rc_filters,
        "lc_filters": lc_filters,
        "feedback_networks": feedback_networks,
        "crystal_circuits": crystal_circuits,
        "snubbers": [],
        "decoupling_analysis": decoupling_analysis,
        "current_sense": current_sense,
        "power_regulators": power_regulators,
        "protection_devices": protection_devices,
        "opamp_circuits": opamp_circuits,
        "bridge_circuits": bridge_circuits,
        "transistor_circuits": transistor_circuits,
        "buzzer_speaker_circuits": buzzer_speaker_circuits,
        "key_matrices": key_matrices,
        "isolation_barriers": isolation_barriers,
        "ethernet_interfaces": ethernet_interfaces,
        "hdmi_dvi_interfaces": hdmi_dvi_interfaces,
        "lvds_interfaces": lvds_interfaces,
        "memory_interfaces": memory_interfaces,
        "rf_chains": rf_chains,
        "rf_matching": rf_matching,
        "bms_systems": bms_systems,
        "battery_chargers": battery_chargers,
        "motor_drivers": motor_drivers,
        "addressable_led_chains": addressable_led_chains,
        "debug_interfaces": debug_interfaces,
        "power_path": power_path,
        "esd_coverage_audit": esd_coverage_audit,
        "adc_circuits": adc_circuits,
        "reset_supervisors": reset_supervisors,
        "clock_distribution": clock_distribution,
        "display_interfaces": display_interfaces,
        "sensor_interfaces": sensor_interfaces,
        "level_shifters": level_shifters,
        "audio_circuits": audio_circuits,
        "led_driver_ics": led_driver_ics,
        "rtc_circuits": rtc_circuits,
        "led_audit": led_audit,
        "thermocouple_rtd": thermocouple_rtd,
        "power_sequencing_validation": power_sequencing_validation,
        "connector_ground_audit": connector_ground_audit,
        "wireless_modules": wireless_modules,
        "transformer_feedback": transformer_feedback,
        "i2c_address_conflicts": i2c_address_conflicts,
        "energy_harvesting": energy_harvesting,
        "pwm_led_dimming": pwm_led_dimming,
        "headphone_jacks": headphone_jacks,
        "solder_jumpers": solder_jumpers,
        "shorted_two_pin_components": shorted_two_pin_components,
        "rail_source_audit": rail_source_audit,
        "label_aliases": label_aliases,
        "power_pin_dc_paths": power_pin_dc_paths,
        "validation_findings": (
            pullup_findings +
            voltage_level_findings +
            i2c_findings +
            spi_findings +
            can_findings +
            usb_findings +
            power_seq_dep_findings +
            led_resistor_findings +
            feedback_stability_findings +
            crystal_load_findings
        ),
        "lookup_findings": (
            am_001_findings +
            ov_001_findings +
            ft_001_findings +
            pm_001_findings +
            ex_001_findings
        ),
    }

    net_classifications = _build_net_classifications(results)
    if net_classifications:
        results["net_classifications"] = net_classifications

    # Certification suggestions cross-reference all domain detections
    cert_suggestions = suggest_certifications(ctx, results)
    if cert_suggestions:
        results["suggested_certifications"] = cert_suggestions

    results["design_observations"] = detect_design_observations(ctx, results)

    # Post-process: enrich capacitor entries with package size and estimated ESR
    enrich_capacitor_records(results, ctx)
    apply_capacitor_derating(results)

    return results


def analyze_signal_paths(ctx: AnalysisContext) -> dict:
    """Analyze signal processing circuits: filters, dividers, feedback networks.

    Orchestrator that calls individual detector functions from signal_detectors.py.
    Each detector takes an AnalysisContext and returns its detection results.
    """
    topo = detect_topologies(ctx)
    reconcile_detections(ctx, topo)
    domain = run_domain_detectors(ctx, topo)
    return assemble_signal_results(ctx, topo, domain)


def analyze_legacy_schematic(path: str, analysis_dir: str | Path | None = None) -> dict:
    """Parse a KiCad 5 legacy .sch file and return the same structure as analyze_schematic.

    Legacy format uses line-oriented text with $Comp/$EndComp blocks, coordinates
    in mils (1/1000 inch), and positional field numbering (F0=ref, F1=value, etc.).

    For hierarchical designs, recursively parses all subsheets referenced by
    $Sheet blocks and merges connectivity across sheets.

    Parses .lib files to populate component pin data for pin-to-net mapping
    and signal analysis.
    """
    all_components = []
    all_wires = []
    all_labels = []
    all_junctions = []
    all_no_connects = []
    sheets_parsed = []
    all_sch_lines = {}  # path -> LIBS: lines for lib resolution

    to_parse = [str(Path(path).resolve())]
    parsed = set()

    while to_parse:
        sheet_path = to_parse.pop(0)
        if sheet_path in parsed:
            continue
        parsed.add(sheet_path)

        components, wires, labels, junctions, no_connects, sub_sheets, lib_lines = \
            _parse_legacy_single_sheet(sheet_path)

        all_sch_lines[sheet_path] = lib_lines

        # Tag elements with sheet index to keep coordinate spaces separate
        sheet_idx = len(sheets_parsed)
        for c in components:
            c["_sheet"] = sheet_idx
        for w in wires:
            w["_sheet"] = sheet_idx
        for lbl in labels:
            lbl["_sheet"] = sheet_idx
        for j in junctions:
            j["_sheet"] = sheet_idx
        for nc in no_connects:
            nc["_sheet"] = sheet_idx

        all_components.extend(components)
        all_wires.extend(wires)
        all_labels.extend(labels)
        all_junctions.extend(junctions)
        all_no_connects.extend(no_connects)
        sheets_parsed.append(sheet_path)

        for sub_path in sub_sheets:
            if sub_path not in parsed:
                to_parse.append(sub_path)

    # Resolve .lib files and parse pin data
    root_path = str(Path(path).resolve())
    lib_symbols, legacy_resolution = _resolve_legacy_libs(root_path, all_sch_lines)

    # Build a reverse lookup for cache lib names: bare_symbol -> full cache name.
    # Cache libs store "Library_Symbol" while schematics reference bare "Symbol"
    # or "Library:Symbol".  This handles both forms.
    _cache_suffix_map: dict[str, str] = {}
    for sym_name in lib_symbols:
        if "_" in sym_name:
            bare = sym_name.rsplit("_", 1)[-1]
            # Only map if the bare name is unique (avoid ambiguity)
            if bare not in _cache_suffix_map:
                _cache_suffix_map[bare] = sym_name
            else:
                _cache_suffix_map[bare] = None  # ambiguous — don't use
        # Also try full name after last colon-like underscore
        # e.g., "OLIMEX_IC_BL4054B-42TPRN(SOT23-5)" → "BL4054B-42TPRN(SOT23-5)"
        parts = sym_name.split("_")
        if len(parts) >= 3:
            tail = "_".join(parts[2:])
            if tail and tail not in _cache_suffix_map:
                _cache_suffix_map[tail] = sym_name

    # Populate pin positions for each component using lib symbol data.
    # V2 format uses bare symbol names ("MIC5207-BM5"), V4 uses "Library:Symbol".
    # Cache libs use underscores ("Device_C") instead of colons ("Device:C").
    for comp in all_components:
        lib_id = comp.get("lib_id", "")
        sym_def = lib_symbols.get(lib_id)
        _pin_src = "parsed_lib"
        if not sym_def and ":" in lib_id:
            # V4: try underscore form (cache lib naming) and bare symbol name
            bare_name = lib_id.split(":", 1)[1]
            sym_def = (lib_symbols.get(lib_id.replace(":", "_"))
                       or lib_symbols.get(bare_name))
        else:
            bare_name = lib_id
        if not sym_def:
            # Bare name lookup via cache suffix map (handles cache libs
            # that store "Library_Symbol" while schematic uses bare "Symbol")
            cache_key = _cache_suffix_map.get(bare_name)
            if cache_key:
                sym_def = lib_symbols.get(cache_key)
                _pin_src = "suffix_match"
        if sym_def:
            comp["pins"] = compute_pin_positions(comp, {lib_id: sym_def})
            comp["_pin_source"] = _pin_src
            # KH-216: Store unit-valid pin numbers for pin_nets filtering
            comp["_unit_pins"] = {p["number"] for p in comp["pins"]}
            # Snap pin positions to mil grid — eliminates floating-point drift
            # from trig-based rotation so pins align with wire endpoints.
            for pin in comp["pins"]:
                pin["x"] = _snap_mil(pin["x"])
                pin["y"] = _snap_mil(pin["y"])

    # KH-016 fix: Snap component pins to nearby wire endpoints when the
    # computed pin positions don't match any wire (caused by KiCad version
    # differences in standard library pin offsets).  For each pin, if no wire
    # endpoint is within COORD_EPSILON, find the closest wire endpoint on the
    # same sheet within a generous radius and snap to it.
    _snap_pins_to_wires(all_components, all_wires)

    # Extract power symbols (preserve _sheet so build_net_map keeps coordinate
    # spaces separate — without it, power symbols from sub-sheets all land in
    # sheet 0's coordinate space and fail to connect to their actual wires).
    power_symbols = []
    for comp in all_components:
        if comp["type"] == "power_symbol":
            ps = {
                "net_name": comp["value"],
                "x": comp["x"],
                "y": comp["y"],
                "lib_id": comp["lib_id"],
            }
            if "_sheet" in comp:
                ps["_sheet"] = comp["_sheet"]
            ps["_power_scope"] = comp.get("_power_scope", "global")
            power_symbols.append(ps)

    # Generate BOM
    bom = generate_bom(all_components)

    # Build nets from wires + labels + power symbols + component pins
    nets = build_net_map(all_components, all_wires, all_labels, power_symbols, all_junctions,
                         all_no_connects,
                         sheet_names=[Path(p).stem for p in sheets_parsed])

    stats = compute_statistics(all_components, nets, bom, all_wires, all_no_connects)

    # Subcircuit detection (IC + 1-hop neighbors)
    # Build shared analysis context for legacy path
    _cache_dir = _resolve_lookup_paths(path, analysis_dir)
    ctx = build_analysis_context(
        all_components, nets, lib_symbols,
        no_connects=all_no_connects, source=ANALYZER_SOURCE,
        cache_dir=_cache_dir, project_dir=str(Path(path).parent))

    subcircuits = identify_subcircuits(ctx)

    # Signal path and filter analysis
    signal_analysis = analyze_signal_paths(ctx)

    # Design rule analysis
    design_analysis = analyze_design_rules(ctx, results_in=signal_analysis)

    # Filter to real components (non-power) for annotation check
    real_components = [
        c for c in all_components
        if c["type"] not in ("power_symbol", "power_flag", "flag")
    ]
    annotation_issues = check_annotation_completeness(real_components)

    result = assemble_legacy_result(
        nets=nets,
        all_components=all_components,
        signal_analysis=signal_analysis,
        real_components=real_components,
        sheets_parsed=sheets_parsed,
        stats=stats,
        bom=bom,
        subcircuits=subcircuits,
        design_analysis=design_analysis,
        all_labels=all_labels,
        all_no_connects=all_no_connects,
        power_symbols=power_symbols,
        annotation_issues=annotation_issues,
        legacy_resolution=legacy_resolution,
    )
    result["diagnostics"] = merge(ctx.diagnostics)
    return result


@dataclass
class SchematicAnalyses:
    """Project-level analyses analyze_schematic() computes between the context and the result."""
    subcircuits: Any
    ic_analysis: Any
    transistor_analysis: Any
    connectivity_issues: Any
    signal_analysis: Any
    design_analysis: Any
    annotation_issues: Any
    label_shape_warnings: Any
    pwr_flag_warnings: Any
    fp_filter_warnings: Any
    sourcing_audit: Any
    datasheet_coverage_findings: Any
    sourcing_gate_findings: Any
    dnp_rate_findings: Any
    alternate_pins: Any
    ground_domains: Any
    bus_topology: Any
    wire_geometry: Any
    sim_readiness: Any
    property_issues: Any
    placement: Any
    pin_coverage: Any
    instance_issues: Any
    hier_label_analysis: Any
    generic_sym_warnings: Any
    pdn_analysis: Any
    power_sequencing: Any
    sleep_current: Any
    voltage_derating: Any
    power_budget: Any
    bom_optimization: Any
    test_coverage: Any
    assembly_complexity: Any
    usb_compliance: Any
    inrush_analysis: Any
    protocol_compliance: Any


def run_analyses(ctx: AnalysisContext, parsed: dict, path: str, nets: dict, bom: list) -> SchematicAnalyses:
    """Project-level analyses, in their historical call order."""
    all_components = parsed["components"]
    all_wires = parsed["wires"]
    all_labels = parsed["labels"]
    all_no_connects = parsed["no_connects"]
    all_lib_symbols = parsed["lib_symbols"]
    merged_bus = parsed["bus_elements"]

    pin_net = ctx.pin_net

    # Identify subcircuits
    subcircuits = identify_subcircuits(ctx)

    # Detailed IC pinout analysis for datasheet cross-referencing
    ic_analysis = analyze_ic_pinouts(ctx)
    # Parallel transistor pinout analysis (F4) — same code path, different
    # filter. ic_pin_analysis stays IC/connector/crystal/oscillator-only for
    # consumer compatibility; transistors go in their own array.
    transistor_analysis = analyze_ic_pinouts(ctx, target_types={"transistor"})

    # Analyze connectivity for issues
    connectivity_issues = analyze_connectivity(all_components, nets, all_no_connects)

    # Signal path and filter analysis
    signal_analysis = analyze_signal_paths(ctx)

    # Deep EE analysis: power domains, buses, differential pairs, ERC
    design_analysis = analyze_design_rules(ctx, results_in=signal_analysis)

    # ---- New Tier 1 + Tier 2 analyses ----

    # Reuse known_power_rails from context for PWR_FLAG audit
    known_power_rails = ctx.known_power_rails

    annotation_issues = check_annotation_completeness(all_components)
    label_shape_warnings = validate_label_shapes(all_labels, nets)
    pwr_flag_warnings = audit_pwr_flags(all_components, nets, known_power_rails)
    fp_filter_warnings = validate_footprint_filters(all_components, all_lib_symbols)
    sourcing_audit = audit_sourcing_fields(all_components)
    datasheet_coverage_findings = audit_datasheet_coverage(
        all_components, str(Path(path).parent))
    sourcing_gate_findings = audit_sourcing_gate(all_components)
    dnp_rate_findings = audit_dnp_rate(all_components)
    alternate_pins = summarize_alternate_pins(all_lib_symbols)
    ground_domains = classify_ground_domains(nets, all_components)
    bus_topology = analyze_bus_topology(merged_bus, all_labels, nets)
    wire_geometry = analyze_wire_geometry(all_wires)
    sim_readiness = check_simulation_readiness(all_components, all_lib_symbols)
    property_issues = audit_property_patterns(all_components)
    placement = spatial_clustering(all_components)
    pin_coverage = verify_pin_coverage(all_components, all_lib_symbols)
    instance_issues = check_instance_consistency(all_components)
    hier_label_analysis = validate_hierarchical_labels(all_labels, nets, merged_bus)
    generic_sym_warnings = check_generic_transistor_symbols(all_components, str(path))

    # ---- Tier 3: High-level design analyses ----
    pdn_analysis = analyze_pdn_impedance(ctx, signal_analysis)
    # KH-374: power_sequencing must run before sleep_current so the sleep
    # audit can consult real EN connectivity (en_source) instead of just
    # EN-pin-name presence.
    power_sequencing = analyze_power_sequencing(ctx, signal_analysis)
    sleep_current = analyze_sleep_current(ctx, signal_analysis, power_sequencing)
    voltage_derating = analyze_voltage_derating(ctx, signal_analysis,
                                                 project_dir=str(Path(path).parent))
    power_budget = analyze_power_budget(ctx, signal_analysis)
    bom_optimization = analyze_bom_optimization(all_components)
    test_coverage = analyze_test_coverage(ctx)
    assembly_complexity = analyze_assembly_complexity(all_components)
    usb_compliance = analyze_usb_compliance(ctx, signal_analysis)
    inrush_analysis = analyze_inrush_current(ctx, signal_analysis)
    protocol_compliance = analyze_protocol_compliance(all_components, nets, design_analysis, signal_analysis, pin_net)

    return SchematicAnalyses(
        subcircuits=subcircuits,
        ic_analysis=ic_analysis,
        transistor_analysis=transistor_analysis,
        connectivity_issues=connectivity_issues,
        signal_analysis=signal_analysis,
        design_analysis=design_analysis,
        annotation_issues=annotation_issues,
        label_shape_warnings=label_shape_warnings,
        pwr_flag_warnings=pwr_flag_warnings,
        fp_filter_warnings=fp_filter_warnings,
        sourcing_audit=sourcing_audit,
        datasheet_coverage_findings=datasheet_coverage_findings,
        sourcing_gate_findings=sourcing_gate_findings,
        dnp_rate_findings=dnp_rate_findings,
        alternate_pins=alternate_pins,
        ground_domains=ground_domains,
        bus_topology=bus_topology,
        wire_geometry=wire_geometry,
        sim_readiness=sim_readiness,
        property_issues=property_issues,
        placement=placement,
        pin_coverage=pin_coverage,
        instance_issues=instance_issues,
        hier_label_analysis=hier_label_analysis,
        generic_sym_warnings=generic_sym_warnings,
        pdn_analysis=pdn_analysis,
        power_sequencing=power_sequencing,
        sleep_current=sleep_current,
        voltage_derating=voltage_derating,
        power_budget=power_budget,
        bom_optimization=bom_optimization,
        test_coverage=test_coverage,
        assembly_complexity=assembly_complexity,
        usb_compliance=usb_compliance,
        inrush_analysis=inrush_analysis,
        protocol_compliance=protocol_compliance,
    )



# ---------------------------------------------------------------------------
# Tier 3: High-level design analysis functions
# ---------------------------------------------------------------------------


def analyze_schematic(path: str, project_root: str | None = None,
                      no_hierarchy: bool = False,
                      analysis_dir: str | Path | None = None) -> dict:
    """Main analysis function. Returns complete structured data.

    For hierarchical designs (multi-sheet), recursively parses all sub-sheets
    and merges connectivity. Global and hierarchical labels connect nets across
    sheets.

    If *path* is a sub-sheet (not the root), the function auto-discovers the
    root schematic via ``.kicad_pro`` and redirects to a full-project analysis.
    The result includes ``_redirected_from`` with the original filename.  If the
    file is not part of any active sheet tree, ``_stale_file_warning`` is set.

    Args:
        path: Path to .kicad_sch file to analyze.
        project_root: Optional path to root .kicad_sch for hierarchy context.
            Auto-discovered from .kicad_pro if not provided.
        no_hierarchy: If True, skip hierarchy auto-discovery entirely.
            Useful when analysing a sub-sheet in isolation.
    """
    # Detect legacy format
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        first_line = f.readline().strip()

    if first_line.startswith("EESchema"):
        return analyze_legacy_schematic(path, analysis_dir=analysis_dir)

    # Parse root sheet and all sub-sheets recursively via parse_all_sheets().
    root_tree = parse_file(path)

    is_sub = detect_sub_sheet(root_tree, file_path=path)
    hierarchy_warning = None

    if is_sub and not no_hierarchy:
        from kicad_core.project import discover_root_schematic
        root_path = project_root or discover_root_schematic(path)
        if root_path:
            # Redirect: analyze the full project from the root schematic.
            # This gives a complete picture (all sheets, all components)
            # instead of analyzing a sub-sheet in isolation.
            original_basename = os.path.basename(path)
            root_basename = os.path.basename(root_path)
            print(f"Note: {original_basename} is a sub-sheet — analyzing "
                  f"full project from root {root_basename}",
                  file=sys.stderr)
            result = analyze_schematic(root_path, no_hierarchy=True)
            result["_redirected_from"] = original_basename

            # Stale file check: is the original file in the project tree?
            target_abs = str(Path(path).resolve())
            in_project = any(
                str(Path(s).resolve()) == target_abs
                for s in result.get("sheets", []))
            if not in_project:
                result["_stale_file_warning"] = (
                    f"{original_basename} is not referenced by any sheet "
                    f"in the project ({root_basename}). It may be a stale "
                    f"or abandoned child schematic.")
                print(f"Warning: {original_basename} is not part of the "
                      f"active project sheet tree", file=sys.stderr)

            return result
        else:
            hierarchy_warning = (
                "File appears to be a sub-sheet (has hierarchical labels but "
                "no symbol_instances). No root schematic found. Component "
                "references may be incomplete. Use --project-root for full "
                "hierarchy analysis."
            )
    elif is_sub and no_hierarchy:
        hierarchy_warning = (
            "File appears to be a sub-sheet but hierarchy discovery is "
            "disabled (--no-hierarchy). Component references may be incomplete."
        )

    pipeline_diagnostics: list = []
    parsed = parse_all_sheets(path, root_tree=root_tree, diagnostics=pipeline_diagnostics)

    merge_top_level_sheets(parsed, path, root_tree, diagnostics=pipeline_diagnostics)

    all_components = parsed["components"]
    all_wires = parsed["wires"]
    all_labels = parsed["labels"]
    all_junctions = parsed["junctions"]
    all_no_connects = parsed["no_connects"]
    all_lib_symbols = parsed["lib_symbols"]
    all_text_annotations = parsed["text_annotations"]
    merged_bus = parsed["bus_elements"]
    root_title_block = parsed["title_block"]
    sheets_parsed = parsed["sheets_parsed"]
    power_symbols = parsed["power_symbols"]
    root_symbol_instances = parsed["root_symbol_instances"]
    generator_version = parsed["generator_version"]
    file_version = parsed["file_version"]

    try:
        _v = int(file_version)
    except (TypeError, ValueError):
        _v = None
    format_newer_note = None
    if _v is not None and _v > MAX_TESTED_FORMAT_VERSION:
        format_newer_note = (
            f"file format version {_v} is newer than the max tested "
            f"({MAX_TESTED_FORMAT_VERSION}); analysis is best-effort")

    # Build net map across all sheets
    nets = build_net_map(all_components, all_wires, all_labels, power_symbols, all_junctions,
                         all_no_connects,
                         sheet_names=[Path(p).stem for p in sheets_parsed],
                         bus_elements=merged_bus)

    # Generate BOM
    bom = generate_bom(all_components)

    # Build shared analysis context (pin_net and every index are built once, here)
    _cache_dir = _resolve_lookup_paths(path, analysis_dir)
    ctx = build_analysis_context(
        all_components, nets, all_lib_symbols,
        no_connects=all_no_connects, generator_version=generator_version,
        source=ANALYZER_SOURCE, cache_dir=_cache_dir, project_dir=str(Path(path).parent))

    analyses = run_analyses(ctx, parsed, path, nets, bom)
    result = assemble_result(ctx, parsed, nets, bom, analyses, path=path,
                             sheets_parsed=sheets_parsed,
                             hierarchy_warning=hierarchy_warning,
                             format_newer_note=format_newer_note,
                             generator_version=generator_version,
                             file_version=file_version)
    result["diagnostics"] = merge(pipeline_diagnostics, ctx.diagnostics)
    return result


def finalize_for_cli(result: dict, config: dict, *, schematic_path: str, lifecycle: bool,
                     stage: str | None, audience: str | None,
                     diagnostics: list | None = None) -> None:
    """Phase 5: command-specific annotation; mutates *result*.

    Project config summary, design intent + CERT-001 gating, power_rails config, lifecycle
    audit / LC-007, datasheet verification, stage/audience filters, summary + trust_summary
    recompute, finding_id assignment. Body verbatim from analyze_schematic.py::main; the only
    seams are args.* -> parameters and one extra '..' on the datasheets path (this file is one
    directory deeper).
    """
    # Attach project config summary to output for downstream consumers
    project = config.get("project", {})
    if project:
        result["project_config"] = project

    # Resolve design intent for downstream consumers
    try:
        from project_config import resolve_design_intent
        sch_data_for_intent = {
            'components': result.get('components', []),
            'title_block': result.get('title_block', {}),
        }
        intent = resolve_design_intent(config,
                                        schematic_data=sch_data_for_intent)
        result['design_intent'] = intent

        # Gate CERT-001 blanket certification suggestions on target_market.
        # For hobby projects, "EU EMC compliance required" and the fallback
        # FCC Part 15 Subpart B fire as noise on every board.  Keep specific
        # triggers (RF, wireless, battery, USB, ethernet, HV) — those
        # represent real circuit hazards regardless of market.
        target_market = (intent or {}).get('target_market', 'hobby')
        if target_market == 'hobby':
            _blanket_cert_prefixes = (
                'FCC Part 15 Subpart B',
                'CISPR 32 / CE EMC Directive',
            )
            result['findings'] = [
                f for f in result.get('findings', [])
                if not (isinstance(f, dict)
                        and f.get('rule_id') == 'CERT-001'
                        and any(str(f.get('standard', '')).startswith(p)
                                for p in _blanket_cert_prefixes))
            ]
    except ImportError:
        pass

    # Apply power_rails config (ignore/flag/voltage_overrides)
    try:
        from project_config import apply_power_rails_config
        stats = result.get('statistics', {})
        rv = result.get('rail_voltages', {})
        pr = stats.get('power_rails', [])
        if rv or pr:
            filtered_rv, filtered_pr, flagged = apply_power_rails_config(
                rv, pr, config)
            result['rail_voltages'] = filtered_rv
            stats['power_rails'] = filtered_pr
            if flagged:
                result['flagged_rails'] = flagged
    except ImportError:
        pass
    except Exception as exc:
        record(diagnostics, "schematic.pipeline.finalize_for_cli", exc,
               "power_rails config not applied")

    # rc.2 4.3 — LC-007 lifecycle-skipped INFO finding. Emit explicitly so
    # reviewers see "lifecycle audit not run" in the findings list rather
    # than silently missing it. Fires in three cases:
    #   1. --lifecycle flag was not passed (most common — high frequency)
    #   2. --lifecycle passed but no MPNs in BOM
    #   3. --lifecycle passed but the audit raised an exception
    _lifecycle_skip_reason: str | None = None
    if not lifecycle:
        _lifecycle_skip_reason = (
            "--lifecycle flag not passed (run with --lifecycle to query "
            "DigiKey / Mouser / LCSC / element14 for obsolescence + "
            "operating-temp coverage; requires network + API keys)"
        )
    else:
        try:
            from lifecycle_audit import audit_bom
            project_dir = str(Path(schematic_path).parent)
            lifecycle = audit_bom(result, project_dir=project_dir)
            if lifecycle and lifecycle.get("components_checked", 0) > 0:
                result["lifecycle_audit"] = lifecycle
                print(f"Lifecycle: {lifecycle.get('lifecycle_summary', {})}", file=sys.stderr)
            else:
                _lifecycle_skip_reason = (
                    "no components with MPNs to check — populate MPN "
                    "fields on BOM parts and re-run with --lifecycle"
                )
                print("Lifecycle: no components with MPNs to check", file=sys.stderr)
        except ImportError:
            _lifecycle_skip_reason = "lifecycle_audit.py not found"
            print("Warning: lifecycle_audit.py not found", file=sys.stderr)
        except (OSError, ValueError, TypeError, KeyError) as e:
            _lifecycle_skip_reason = f"audit raised {type(e).__name__}: {e}"
            print(f"Warning: lifecycle audit failed: {e}", file=sys.stderr)

    if _lifecycle_skip_reason is not None:
        if 'findings' not in result:
            result['findings'] = []
        result['findings'].append({
            "detector": "audit_lifecycle_skipped",
            "rule_id": "LC-007",
            "severity": "info",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "category": "lifecycle",
            "summary": f"Lifecycle audit not run — {_lifecycle_skip_reason.split(' (')[0]}",
            "description": (
                f"Component lifecycle / obsolescence audit was not run "
                f"this session. Reason: {_lifecycle_skip_reason}. The "
                f"review cannot report active / NRND / EOL / obsolete "
                f"status, last-time-buy windows, or operating-temperature "
                f"coverage for any BOM part. Treat the lifecycle section "
                f"of the report as 'not performed'."
            ),
            "components": [],
            "nets": [],
            "pins": [],
            "recommendation": (
                "Run with --lifecycle (requires DIGIKEY_CLIENT_ID / "
                "MOUSER_SEARCH_API_KEY / ELEMENT14_API_KEY env vars; "
                "LCSC needs no auth) to populate this section. If "
                "intentionally skipped, note it explicitly in the report's "
                "'Not Performed' section."
            ),
            "report_context": {
                "section": "Component Lifecycle",
                "impact": "No obsolescence / temperature-grade evidence available.",
                "standard_ref": "",
            },
        })

    # Datasheet verification — cross-check extracted datasheet data against schematic
    try:
        # Import datasheet_verify from the datasheets skill
        import os as _os, sys as _sys
        _ds_scripts = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                                    '..', '..', '..', 'datasheets', 'scripts')
        if _os.path.isdir(_ds_scripts):
            _sys.path.insert(0, _os.path.abspath(_ds_scripts))
        from datasheet_verify import run_datasheet_verification
        project_dir = str(Path(schematic_path).parent)
        ds_verify = run_datasheet_verification(result, project_dir=project_dir)
        if ds_verify.get("findings") or ds_verify.get("summary", {}).get("ics_with_extractions", 0) > 0:
            result["datasheet_verification"] = ds_verify
    except ImportError:
        pass
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as e:
        # AttributeError added for rc.3 — defense against future None-leaks
        # in datasheet_verify.py (see _load_extraction normalization).
        result["datasheet_verification"] = {
            "findings": [],
            "summary": {"error": f"{type(e).__name__}: {e}"},
        }

    from output_filters import apply_output_filters
    apply_output_filters(result, stage, audience)

    # Recompute summary + trust_summary from the final findings list — post-
    # filters (CERT-001 hobby gating, power_rails config, lifecycle audit,
    # datasheet verification, output_filters stage filter) can mutate
    # findings[] after the initial summary was built. Keep the envelope
    # consistent with what actually ships in findings[].
    _final_findings = result.get('findings', []) if isinstance(result.get('findings'), list) else []
    _sev_counts = {"error": 0, "warning": 0, "info": 0}
    for _f in _final_findings:
        if not isinstance(_f, dict):
            continue
        _s = str(_f.get('severity', 'info')).lower()
        if _s in _sev_counts:
            _sev_counts[_s] += 1
        else:
            _sev_counts['info'] += 1
    if isinstance(result.get('summary'), dict):
        result['summary']['total_findings'] = len(_final_findings)
        result['summary']['by_severity'] = _sev_counts
    try:
        from finding_schema import compute_trust_summary
        result['trust_summary'] = compute_trust_summary(_final_findings, bom=result.get('bom'))
    except ImportError:
        pass
    except Exception as exc:
        record(diagnostics, "schematic.pipeline.finalize_for_cli", exc,
               "trust_summary not recomputed after filters")

    # Guarantee every finding carries a stable finding_id (Layer 2 merge keys
    # on it). Runs after all filtering/appends; before any output branch.
    assign_finding_ids(result.get('findings', []), 'schematic')
