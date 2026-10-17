"""EMC analyzer output envelope (v1.4 SOT).

The runtime emits ~13 top-level keys on the simple fixture: tight core
(analyzer_type, schema_version, summary, trust_summary, target_standard,
elapsed_s) plus EMC-specific analysis bags (findings, per_net_scores,
test_plan, regulatory_coverage, category_summary, board_info) and an
optional audience_summary emitted whenever findings exist.

Tightens:
    - analyzer_type + schema_version carry ``const`` discriminators.
    - summary, trust_summary are typed dataclasses mirroring the runtime
      shape.
    - test_plan decomposes into typed FrequencyBand / InterfaceRisk /
      ProbePoint sub-records.
    - regulatory_coverage + category_summary + board_info use typed
      shells with ``list[dict]`` / ``dict`` leaves for v1.4; tightens
      per rule_id in v1.5.

Mode gating:
    - ``audience_summary`` is emitted whenever findings are present
      (apply_output_filters always runs). Marked Optional since a
      zero-finding run may omit it.
    - ``stage_filter`` appears only when ``--stage`` is passed; marked
      Optional.

Sibling-module layout:
    This module lives in skills/emc/scripts/ alongside analyze_emc.py.
    The analyzer already puts skills/kicad/scripts/ on sys.path before
    importing; this envelope re-derives the path so it can also be
    imported standalone (tests, generator tooling).
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Optional

# Bridge to skills/kicad/scripts/ for shared primitives. emc_envelope.py
# is a sibling of analyze_emc.py under skills/emc/scripts/, so reach up
# two levels and across into skills/kicad/scripts/.
_HERE = os.path.dirname(os.path.abspath(__file__))
_KICAD_SCRIPTS = os.path.abspath(os.path.join(_HERE, "..", "..", "kicad", "scripts"))
if _KICAD_SCRIPTS not in sys.path:
    sys.path.insert(0, _KICAD_SCRIPTS)

from analyzer_envelope import (  # noqa: E402
    TrustSummary, Finding, Assessment, BySeverity, InputsBlock, CompatBlock,
)


@dataclass
class EMCSummary:
    """Top-level roll-up (mirrors the runtime's summary dict)."""
    total_findings: int = field(metadata={
        "description": "Count of findings[] post-filter."})
    categories_checked: int = field(metadata={
        "description": "Number of EMC categories exercised on this run."})
    active: int = field(metadata={
        "description": "Non-suppressed finding count."})
    suppressed: int = field(metadata={
        "description": "Suppressed finding count."})
    by_severity: BySeverity = field(metadata={
        "description": "Breakdown by severity bucket."})
    emc_risk_score: float = field(metadata={
        "description": "Composite EMC risk score, 0 (worst) to 100 (best)."})


@dataclass
class FrequencyBand:
    """One entry in test_plan.frequency_bands."""
    band: str = field(metadata={
        "description": "Human-readable band label (e.g. '30-88 MHz')."})
    freq_min_hz: float = field(metadata={
        "description": "Lower band edge in Hz."})
    freq_max_hz: float = field(metadata={
        "description": "Upper band edge in Hz."})
    risk_level: str = field(metadata={
        "description": "Risk label: 'none', 'low', 'medium', 'high'."})
    source_count: int = field(metadata={
        "description": "Number of detected emission sources in this band."})
    sources: list[str] = field(metadata={
        "description": "Human-readable source labels (e.g. crystal MHz, "
                       "switching frequency)."})


@dataclass
class InterfaceRisk:
    """One entry in test_plan.interface_risks."""
    connector: str = field(metadata={
        "description": "Connector reference designator (e.g. 'J1')."})
    value: str = field(metadata={
        "description": "Connector value/part label."})
    protocol: str = field(metadata={
        "description": "Detected protocol or 'unknown'."})
    risk_score: int = field(metadata={
        "description": "Risk score 0-10."})
    reasons: list[str] = field(metadata={
        "description": "Short reasons explaining the score."})


@dataclass
class ProbePoint:
    """One entry in test_plan.probe_points (near-field probe suggestion)."""
    x: float = field(metadata={
        "description": "Probe location X in mm."})
    y: float = field(metadata={
        "description": "Probe location Y in mm."})
    type: str = field(metadata={
        "description": "Probe-point category tag (e.g. "
                       "'unfiltered_connector', 'switching_regulator')."})
    ref: str = field(metadata={
        "description": "Associated reference designator."})
    reason: str = field(metadata={
        "description": "Human-readable reason the probe was suggested."})


@dataclass
class TestPlan:
    """Pre-compliance test plan derived from findings + board info."""
    frequency_bands: list[FrequencyBand] = field(metadata={
        "description": "Standard EMC frequency bands tagged with detected "
                       "emission sources + risk level."})
    interface_risks: list[InterfaceRisk] = field(metadata={
        "description": "Per-connector risk ranking for radiated/conducted "
                       "emissions from cabled I/O."})
    probe_points: list[ProbePoint] = field(metadata={
        "description": "Suggested near-field probe locations for bench "
                       "pre-compliance."})


@dataclass
class CoverageMatrixEntry:
    """One row in regulatory_coverage.coverage_matrix."""
    standard: str = field(metadata={
        "description": "Standard label (e.g. 'FCC Part 15 Class B')."})
    test_type: str = field(metadata={
        "description": "'radiated' | 'conducted' | other test type."})
    coverage: str = field(metadata={
        "description": "Coverage label: 'minimal' | 'indirect' | 'partial' "
                       "| 'good'."})
    checked_rules: list[str] = field(metadata={
        "description": "Rule IDs that contribute to this row's coverage."})
    total_applicable_rules: int = field(metadata={
        "description": "Total applicable rule IDs for this standard + "
                       "test type."})
    note: Optional[str] = field(default=None, metadata={
        "description": "Qualifier/caveat text (optional)."})


@dataclass
class RegulatoryCoverage:
    """Regulatory coverage rollup for the target market/standard."""
    market: str = field(metadata={
        "description": "Target market key: 'us' | 'eu' | 'automotive' | "
                       "'medical' | 'military'."})
    applicable_standards: list[str] = field(metadata={
        "description": "Standards applicable to the target market."})
    coverage_matrix: list[CoverageMatrixEntry] = field(metadata={
        "description": "Per-standard coverage rows."})


@dataclass
class CategorySummaryEntry:
    """One value in category_summary (key = category label)."""
    count: int = field(metadata={
        "description": "Total findings in this category (suppressed + active)."})
    max_severity: str = field(metadata={
        "description": "Highest severity seen: 'error' | 'warning' | 'info'."})
    severities: BySeverity = field(metadata={
        "description": "Severity histogram for this category."})
    suppressed_count: int = field(metadata={
        "description": "Count of suppressed findings in this category."})


@dataclass
class PerNetScore:
    """One entry in per_net_scores[]."""
    net: str = field(metadata={
        "description": "Net name."})
    score: float = field(metadata={
        "description": "Per-net EMC risk score 0-100 (higher = better)."})
    finding_count: int = field(metadata={
        "description": "Count of findings touching this net."})
    rules: list[str] = field(metadata={
        "description": "Sorted unique rule IDs contributing to the score."})


@dataclass
class BoardInfo:
    """Board-level rollup used for reporting + frequency band targeting."""
    # All fields optional — depends on which of schematic/pcb is provided.
    board_width_mm: Optional[float] = field(default=None, metadata={
        "description": "Board width in mm (from PCB analyzer)."})
    board_height_mm: Optional[float] = field(default=None, metadata={
        "description": "Board height in mm (from PCB analyzer)."})
    layer_count: Optional[int] = field(default=None, metadata={
        "description": "Copper layer count (from PCB analyzer)."})
    footprint_count: Optional[int] = field(default=None, metadata={
        "description": "Total footprint count (from PCB analyzer)."})
    via_count: Optional[int] = field(default=None, metadata={
        "description": "Total via count (from PCB analyzer)."})
    has_stackup: Optional[bool] = field(default=None, metadata={
        "description": "True when a stackup block was present."})
    board_thickness_mm: Optional[float] = field(default=None, metadata={
        "description": "Stackup thickness in mm (when has_stackup)."})
    total_components: Optional[int] = field(default=None, metadata={
        "description": "Total components from schematic analyzer."})
    total_nets: Optional[int] = field(default=None, metadata={
        "description": "Total nets from schematic analyzer."})
    highest_frequency_hz: Optional[float] = field(default=None, metadata={
        "description": "Highest crystal frequency detected, in Hz."})
    crystal_frequencies_hz: Optional[list[float]] = field(default=None, metadata={
        "description": "Sorted unique crystal frequencies in Hz."})
    switching_frequencies_hz: Optional[list[float]] = field(default=None, metadata={
        "description": "Sorted unique switching-regulator frequencies in Hz."})


@dataclass
class EMCEnvelope:
    """Top-level output of analyze_emc.py.

    Tight typing on universal fields (analyzer_type, schema_version,
    summary, trust_summary, target_standard, elapsed_s). Typed
    sub-structures for test_plan (FrequencyBand / InterfaceRisk /
    ProbePoint), regulatory_coverage (CoverageMatrixEntry), per_net_scores
    (PerNetScore), category_summary (CategorySummaryEntry), and
    board_info. audience_summary and stage_filter remain loose dicts for
    v1.4 — tighten per rule_id / audience slice in v1.5.
    """

    # --- Discriminators ---
    analyzer_type: str = field(metadata={
        "description": "Always 'emc'.",
        "const": "emc"})
    schema_version: str = field(metadata={
        "description": "Semver. Value: '1.4.0' at Track 1.1 landing.",
        "const": "1.4.0"})

    # --- Provenance ---
    inputs: InputsBlock = field(metadata={
        "description": "Source JSON inputs, sha256s, run_id, plus upstream "
                       "artifact metadata (schematic, pcb)."})
    compat: CompatBlock = field(metadata={
        "description": "Schema compatibility metadata: minimum consumer "
                       "version + deprecated/experimental field lists."})

    # --- Universal core ---
    target_standard: str = field(metadata={
        "description": "Target EMC standard key (e.g. 'fcc-class-b', "
                       "'cispr-class-b', 'cispr-25')."})
    summary: EMCSummary = field(metadata={
        "description": "EMC roll-up summary (counts + risk score)."})
    findings: list[Finding] = field(metadata={
        "description": "All EMC findings."})
    assessments: list[Assessment] = field(metadata={
        "description": "Informational assessments (empty for EMC at v1.4)."})
    trust_summary: TrustSummary = field(metadata={
        "description": "Trust posture rollup (confidence + evidence source)."})
    elapsed_s: float = field(metadata={
        "description": "Analysis wall-clock time in seconds."})

    # --- EMC analysis bags ---
    per_net_scores: list[PerNetScore] = field(metadata={
        "description": "Per-net EMC risk score rollup, sorted worst-first."})
    test_plan: TestPlan = field(metadata={
        "description": "Pre-compliance test plan: frequency band priority, "
                       "interface risk ranking, probe point suggestions."})
    regulatory_coverage: RegulatoryCoverage = field(metadata={
        "description": "Coverage matrix vs. applicable standards for the "
                       "target market."})
    category_summary: dict[str, CategorySummaryEntry] = field(metadata={
        "description": "Category label -> {count, max_severity, severities, "
                       "suppressed_count}."})
    board_info: BoardInfo = field(metadata={
        "description": "Board-level rollup (dimensions, layer count, "
                       "crystal + switching frequencies, ...)."})

    # --- Phase 4 capability pointer ---
    capability_mode_ref: Optional[dict] = field(default=None, metadata={
        "description": "Pointer to canonical analysis/capability_mode.json run-level "
                       "record. Shape: {source, run_id}. See Phase 4 spec §3.3."})

    # --- Stage/audience derived blocks ---
    audience_summary: Optional[dict] = field(default=None, metadata={
        "description": "Designer/reviewer/manager summary views. Present "
                       "whenever findings[] is non-empty (the analyzer "
                       "always builds this when findings exist)."})
    stage_filter: Optional[dict] = field(default=None, metadata={
        "description": "Stage-filtered findings rollup. Present only when "
                       "--stage is passed."})
