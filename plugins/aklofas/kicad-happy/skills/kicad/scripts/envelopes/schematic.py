"""Schematic analyzer output envelope (v1.4 SOT).

The runtime emits a sprawling result dict — ~40 top-level keys spanning
hard-typed core (summary, trust_summary, findings, components, nets,
bom, statistics) and many detector-specific analysis bags
(design_analysis, placement_analysis, bus_topology, sleep_current_audit,
etc.).  This envelope types every top-level key the runtime actually
emits on the simple fixture, while leaving the free-form analysis bags
as plain ``dict`` schemas.  Consumers get the discriminator fields
(analyzer_type, schema_version) as ``const`` strings and a guaranteed
shape for the universal blocks; detector-specific contents inside the
bags will tighten per rule_id in v1.5.

Additional properties are permitted by JSON Schema default so optional
sections that only appear on richer projects (sheets, project_settings,
pdn_impedance, etc.) validate cleanly whether present or absent.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Optional

# Make shared primitives importable when this module is loaded from
# tests, from the analyzer, or via generator tooling.
_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

from analyzer_envelope import (  # noqa: E402
    TrustSummary, Finding, Assessment, BySeverity, TitleBlock, InputsBlock, CompatBlock,
)


@dataclass
class SchematicSummary:
    """Top-level roll-up (mirrors the runtime's summary dict)."""
    total_findings: int = field(metadata={
        "description": "Count of findings[]."})
    by_severity: BySeverity = field(metadata={
        "description": "Breakdown by severity bucket."})


@dataclass
class PowerRailEntry:
    """Power rail statistic entry. Voltage may be null for ground nets."""
    name: str = field(metadata={
        "description": "Power rail net name."})
    voltage: Optional[float] = field(default=None, metadata={
        "description": "Rail voltage in volts; null for ground or "
                       "unresolved rails."})


@dataclass
class Statistics:
    """Component / net counts and coverage summaries."""
    total_components: int = field(metadata={
        "description": "Total component count (excluding power symbols)."})
    unique_parts: int = field(metadata={
        "description": "Count of distinct (value, footprint, MPN) triples."})
    dnp_parts: int = field(metadata={
        "description": "Components marked Do Not Populate."})
    total_nets: int = field(metadata={
        "description": "Count of distinct nets."})
    total_wires: int = field(metadata={
        "description": "Wire segment count."})
    total_no_connects: int = field(metadata={
        "description": "No-connect flag count."})
    component_types: dict[str, int] = field(metadata={
        "description": "Map: component type name -> count."})
    power_rails: list[PowerRailEntry] = field(metadata={
        "description": "Power rail net entries {name, voltage} detected."})
    missing_mpn: list[str] = field(metadata={
        "description": "References missing MPN property."})
    missing_footprint: list[str] = field(metadata={
        "description": "References missing footprint."})


@dataclass
class NetPin:
    """One pin participating in a net."""
    component: str = field(metadata={
        "description": "Component reference."})
    pin_number: str = field(metadata={
        "description": "Pin number on component."})
    pin_name: Optional[str] = field(default=None, metadata={
        "description": "Pin name."})
    pin_type: Optional[str] = field(default=None, metadata={
        "description": "Electrical type."})


@dataclass
class NetEntry:
    """Connectivity entry for one net."""
    name: str = field(metadata={
        "description": "Net name."})
    pins: list[NetPin] = field(metadata={
        "description": "Pins on this net."})
    point_count: int = field(metadata={
        "description": "Geometric connection point count."})
    no_connect: bool = field(default=False, metadata={
        "description": "Net terminated by a no-connect flag."})
    has_pwr_flag: bool = field(default=False, metadata={
        "description": "Net carries a PWR_FLAG ERC source declaration."})
    labels: list[str] = field(default_factory=list, metadata={
        "description": "Label strings attached to this net."})


@dataclass
class BomEntry:
    """One deduplicated BOM row."""
    value: Optional[str] = field(default=None, metadata={
        "description": "Value string."})
    footprint: Optional[str] = field(default=None, metadata={
        "description": "Footprint."})
    mpn: Optional[str] = field(default=None, metadata={
        "description": "MPN."})
    manufacturer: Optional[str] = field(default=None, metadata={
        "description": "Manufacturer."})
    digikey: Optional[str] = field(default=None, metadata={
        "description": "DigiKey SKU."})
    mouser: Optional[str] = field(default=None, metadata={
        "description": "Mouser SKU."})
    lcsc: Optional[str] = field(default=None, metadata={
        "description": "LCSC SKU."})
    element14: Optional[str] = field(default=None, metadata={
        "description": "element14 SKU."})
    datasheet: Optional[str] = field(default=None, metadata={
        "description": "Datasheet URL or local path."})
    description: Optional[str] = field(default=None, metadata={
        "description": "Description."})
    references: list[str] = field(default_factory=list, metadata={
        "description": "Refdes list."})
    quantity: int = field(default=0, metadata={
        "description": "Quantity for this line item."})
    dnp: bool = field(default=False, metadata={
        "description": "DNP flag."})
    type: Optional[str] = field(default=None, metadata={
        "description": "Component type."})


@dataclass
class PinCoverageWarning:
    """One entry in pin_coverage_warnings (KH-323)."""
    component: str = field(metadata={
        "description": "Component reference with pin coverage gap."})
    lib_id: str = field(metadata={
        "description": "KiCad library ID of the symbol."})
    expected_pins: int = field(metadata={
        "description": "Count of non-NC pins in the library symbol."})
    placed_pins: int = field(metadata={
        "description": "Count of pins actually placed across units."})
    missing_count: int = field(metadata={
        "description": "Count of missing placements."})
    message: str = field(metadata={
        "description": "Human-readable warning message."})


@dataclass
class SchematicEnvelope:
    """Top-level output of analyze_schematic.py.

    Tight typing on universal fields (analyzer_type, schema_version,
    summary, trust_summary, findings, statistics, bom, nets).  Loose
    ``dict`` typing on detector-specific analysis bags so each bag's
    per-rule_id shape can tighten independently in v1.5.

    Optional fields at the bottom are only emitted on richer projects
    (hierarchy, protocol_compliance, sleep_current_audit, etc.); the
    simple fixture emits only a few of them.
    """

    # --- Discriminators ---
    analyzer_type: str = field(metadata={
        "description": "Always 'schematic'.",
        "const": "schematic"})
    schema_version: str = field(metadata={
        "description": "Semver. Value: '1.4.0' at Track 1.1 landing.",
        "const": "1.4.0"})

    # --- Provenance ---
    inputs: InputsBlock = field(metadata={
        "description": "Source files, hashes, run_id, config_hash, upstream "
                       "artifacts for this run."})
    compat: CompatBlock = field(metadata={
        "description": "Schema compatibility metadata: minimum consumer "
                       "version + deprecated/experimental field lists."})

    # --- Universal core ---
    summary: SchematicSummary = field(metadata={
        "description": "Roll-up summary (total + by_severity)."})
    trust_summary: TrustSummary = field(metadata={
        "description": "Trust posture rollup (confidence + evidence source "
                       "+ optional BOM coverage)."})
    kicad_version: str = field(metadata={
        "description": "KiCad generator version string, e.g. '9.0' or '5 (legacy)'."})
    file_version: str = field(metadata={
        "description": "KiCad file format version string."})
    title_block: TitleBlock = field(metadata={
        "description": "KiCad title block (title/date/rev/company/comments)."})
    statistics: Statistics = field(metadata={
        "description": "Component, net, and coverage counts."})
    findings: list[Finding] = field(metadata={
        "description": "All findings (flat, rich-finding format)."})
    assessments: list[Assessment] = field(metadata={
        "description": "Informational assessments (empty for schematic at v1.4; "
                       "reserved for future measurement-style records)."})
    bom: list[BomEntry] = field(metadata={
        "description": "Deduplicated BOM rows."})
    components: list[dict] = field(metadata={
        "description": "Every non-power component as a dict. Shape is "
                       "effectively open: reference/value/lib_id/"
                       "footprint/datasheet/description/mpn/manufacturer/"
                       "distributor SKUs/geometry/uuid/type/parsed_value "
                       "plus internal bookkeeping (_sheet, pin_nets, "
                       "pin_uuids). Tightens to a typed Component in v1.5."})
    nets: dict[str, NetEntry] = field(metadata={
        "description": "Net connectivity map keyed by net name."})
    subcircuits: list[dict] = field(metadata={
        "description": "Hierarchical sub-sheets: "
                       "[{reference, path, sheet_name, sheet_file, instances}]."})
    ic_pin_analysis: list[dict] = field(metadata={
        "description": "Per-IC pin mappings. Each entry carries reference, "
                       "value, type, lib_id, mpn, description, datasheet, "
                       "function, total_pins, unconnected_pins, pins[], "
                       "power_pins[], signal_pins[], decoupling_caps_by_rail. "
                       "Covers type in {ic, connector, crystal, oscillator}; "
                       "transistors live in transistor_pin_analysis[] (F4)."})
    transistor_pin_analysis: list[dict] = field(metadata={
        "description": "Per-transistor pin mappings. Same shape as "
                       "ic_pin_analysis entries but filtered to "
                       "type=transistor (MOSFETs, BJTs, FETs). Lets bridge / "
                       "half-bridge / gate-driver reviewers verify "
                       "gate/source/drain wiring without reconstructing pin "
                       "maps from nets[].pins[] by hand. F4."})

    # --- Analysis bags (free-form dicts; shapes tighten per rule_id in v1.5) ---
    design_analysis: dict = field(metadata={
        "description": "Design-level analyses: net_classification, "
                       "power_domains, cross_domain_signals, bus_analysis "
                       "(i2c/spi/uart/can), differential_pairs, "
                       "erc_warnings, passive_warnings."})
    connectivity_issues: dict = field(metadata={
        "description": "Connectivity issue lists: single_pin_nets, "
                       "single_pin_net_findings, multi_driver_nets, "
                       "unconnected_pins, power_net_summary."})
    annotation_issues: dict = field(metadata={
        "description": "Annotation issue bag: duplicate_references, "
                       "unannotated, missing_value, zero_indexed_refs."})
    ground_domains: dict = field(metadata={
        "description": "Ground topology: ground_nets, multiple_domains, "
                       "domains, optional star-ground note."})
    bus_topology: dict = field(metadata={
        "description": "Bus wire statistics: bus_wire_count, bus_entry_count."})
    wire_geometry: dict = field(metadata={
        "description": "Wire-geometry summary: total_wires, "
                       "total_length_mm, avg_length_mm, optional "
                       "diagonal/short-wire callouts."})
    simulation_readiness: dict = field(metadata={
        "description": "SPICE readiness rollup: total_components, "
                       "likely_simulatable, needs_model, "
                       "simulatable_percent, components_without_model."})
    hierarchical_labels: dict = field(metadata={
        "description": "Label counts: global_label_count, "
                       "hierarchical_label_count, optional "
                       "unconnected_hierarchical or conflict warnings."})
    placement_analysis: dict = field(metadata={
        "description": "Placement stats: bounding_box, clusters, grid_size."})
    property_issues: dict = field(metadata={
        "description": "Property validation issues: missing/mismatched "
                       "symbol properties (MPN, footprint, datasheet, value), "
                       "blank description fields, non-ASCII character "
                       "warnings. Keyed by issue category."})
    sourcing_audit: dict = field(metadata={
        "description": "Sourcing audit: missing_mpn/digikey/lcsc lists, "
                       "mpn_coverage, mpn_percent, total_bom_components."})
    rail_voltages: dict[str, Optional[float]] = field(metadata={
        "description": "Per-net rail voltage (volts). Nulls permitted for "
                       "ground or unresolved rails."})

    # --- Runtime "also emitted" companions ---
    # These may be absent on some paths but the simple fixture emits them,
    # so they are required by default.  Optional-by-design blocks live
    # below.
    labels: list[dict] = field(default_factory=list, metadata={
        "description": "Extracted label records."})
    no_connects: list[dict] = field(default_factory=list, metadata={
        "description": "Extracted no-connect flag records."})
    power_symbols: list[dict] = field(default_factory=list, metadata={
        "description": "Power symbol placements: [{net_name, x, y, lib_id, "
                       "_sheet, _power_scope}]."})
    pwr_flag_warnings: list[dict] = field(default_factory=list, metadata={
        "description": "PWR_FLAG warnings: [{net, message, pin_types}]."})
    label_shape_warnings: list = field(default_factory=list, metadata={
        "description": "Label-shape mismatch warnings."})
    footprint_filter_warnings: list = field(default_factory=list, metadata={
        "description": "Footprint filter warnings from lib_symbols."})

    # --- Phase 4 capability pointer ---
    capability_mode_ref: Optional[dict] = field(default=None, metadata={
        "description": "Pointer to canonical analysis/capability_mode.json run-level "
                       "record. Shape: {source, run_id}. See Phase 4 spec §3.3."})

    # --- Stage/audience derived blocks ---
    audience_summary: Optional[dict] = field(default=None, metadata={
        "description": "Designer/reviewer/manager summary views; only "
                       "present when output filters ran."})

    # --- Project/intent/config attachments ---
    design_intent: Optional[dict] = field(default=None, metadata={
        "description": "Resolved design intent: approved_manufacturers, "
                       "ipc_class, target_market, operating_temp_range, "
                       "preferred_passive_size, product_class, "
                       "test_coverage_target, expected_lifetime_years, "
                       "detection_signals, source, confidence."})
    project_config: Optional[dict] = field(default=None, metadata={
        "description": "Copy of the resolved project block from "
                       ".kicad-happy.json (when present)."})
    project_settings: Optional[dict] = field(default=None, metadata={
        "description": "Selected KiCad project settings extracted from "
                       ".kicad_pro (when present)."})

    # --- Coverage / audit sections ---
    bom_lock: Optional[dict] = field(default=None, metadata={
        "description": "BOM lock verification: status, lock_pct, "
                       "components_with_mpn, missing_mpn, etc."})
    bom_optimization: Optional[dict] = field(default=None, metadata={
        "description": "BOM optimization bag: single_use_passive_values, "
                       "unique_value_counts, total_unique_footprints, "
                       "consolidation_suggestions."})
    missing_info: Optional[dict] = field(default=None, metadata={
        "description": "Data-gap rollup: missing_mpn, missing_footprint, "
                       "missing_datasheet, heuristic_vref."})
    # --- Specialised analysis (gated on content) ---
    sleep_current_audit: Optional[dict] = field(default=None, metadata={
        "description": "Sleep-current audit: rails, total_estimated_sleep_uA, "
                       "realistic_total_uA, conditional_pull_up_uA, "
                       "observations."})
    test_coverage: Optional[dict] = field(default=None, metadata={
        "description": "Test coverage audit: test_points, test_point_count, "
                       "covered_nets, uncovered_key_nets, observations, "
                       "optional debug_connectors."})
    assembly_complexity: Optional[dict] = field(default=None, metadata={
        "description": "Assembly complexity score and breakdown."})
    power_budget: Optional[dict] = field(default=None, metadata={
        "description": "Estimated power budget per rail."})
    power_sequencing: Optional[dict] = field(default=None, metadata={
        "description": "Power sequencing dependencies and warnings."})
    power_sequencing_validation: Optional[dict] = field(default=None, metadata={
        "description": "Validated power tree with provenance."})
    pdn_impedance: Optional[dict] = field(default=None, metadata={
        "description": "PDN impedance analysis per rail."})
    usb_compliance: Optional[dict] = field(default=None, metadata={
        "description": "USB compliance checks."})
    inrush_analysis: Optional[dict] = field(default=None, metadata={
        "description": "Inrush current estimation by rail."})
    protocol_compliance: Optional[dict] = field(default=None, metadata={
        "description": "Protocol compliance checks (I2C/SPI/UART/etc.)."})

    # --- Warnings / notices ---
    # TODO(v1.5): tighten these bare `list` fields to list[TypedItem] once
    # runtime shapes are finalized. Holding at `list` for v1.4 since items
    # are heterogeneous dicts with inconsistent keys across detector paths.
    text_annotations: Optional[list] = field(default=None, metadata={
        "description": "Text annotations extracted from the schematic."})
    alternate_pin_summary: Optional[dict] = field(default=None, metadata={
        "description": "Alternate-pin usage summary."})
    pin_coverage_warnings: Optional[list[PinCoverageWarning]] = field(default=None, metadata={
        "description": "KH-323: warnings about pin coverage gaps. Emitted "
                       "when a placed symbol has fewer pins connected than "
                       "the library definition expects. Present only when "
                       "such warnings fire."})
    instance_consistency_warnings: Optional[list] = field(default=None, metadata={
        "description": "Multi-instance symbol consistency warnings."})
    generic_symbol_warnings: Optional[list] = field(default=None, metadata={
        "description": "Warnings about generic symbol usage without MPN."})

    # --- Legacy / hierarchy / sheet metadata ---
    sheets: Optional[list] = field(default=None, metadata={
        "description": "Hierarchical sheet list (multi-sheet only)."})
    sheets_parsed: Optional[int] = field(default=None, metadata={
        "description": "Count of parsed sheets (legacy .sch)."})
    sheet_files: Optional[list[str]] = field(default=None, metadata={
        "description": "Parsed sheet file paths (legacy .sch)."})
    legacy_analysis_quality: Optional[dict] = field(default=None, metadata={
        "description": "Legacy .sch quality rollup: is_legacy_schematic, "
                       "library_resolution, pin_source_coverage."})
    hierarchy_context: Optional[dict] = field(default=None, metadata={
        "description": "Hierarchy context (sub-sheet analysis): "
                       "root_schematic, target_sheet, sheets_in_project, "
                       "cross_sheet_nets, project_power_rails, "
                       "reference_corrections_applied."})
    hierarchy_warning: Optional[str] = field(default=None, metadata={
        "description": "Emitted when sub-sheet was detected without root."})
    redirected_from: Optional[str] = field(default=None, metadata={
        "description": "Original filename when a sub-sheet was redirected "
                       "to the project root. Emitted in JSON as "
                       "'_redirected_from'.",
        "json_name": "_redirected_from"})
    stale_file_warning: Optional[str] = field(default=None, metadata={
        "description": "Emitted when input file is not in the project "
                       "sheet tree. Emitted in JSON as "
                       "'_stale_file_warning'.",
        "json_name": "_stale_file_warning"})
    net_classifications: Optional[dict] = field(default=None, metadata={
        "description": "Per-net classification map promoted from "
                       "signal_analysis (legacy alias of "
                       "design_analysis.net_classification)."})
