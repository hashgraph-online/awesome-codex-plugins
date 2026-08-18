"""Thermal analyzer output envelope (v1.4 SOT)."""
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
    TrustSummary, Finding, Assessment, BySeverity, InputsBlock, CompatBlock,
)


@dataclass
class ThermalHottest:
    ref: str = field(metadata={
        "description": "Reference designator of the hottest analyzed component."})
    tj_estimated_c: float = field(metadata={
        "description": "Estimated junction temperature (°C) of the hottest component."})


@dataclass
class ThermalSummary:
    total_findings: int = field(metadata={"description": "Count of findings[]."})
    components_assessed: int = field(metadata={
        "description": "Number of components for which thermal estimation ran."})
    active: int = field(metadata={
        "description": "Non-suppressed findings count."})
    suppressed: int = field(metadata={
        "description": "Findings suppressed by project config."})
    by_severity: BySeverity = field(metadata={
        "description": "Breakdown by severity bucket."})
    thermal_score: Optional[float] = field(metadata={
        "description": "Composite thermal risk score, 0-100. None when no "
                       "components were assessable (see skipped_reason) — a "
                       "100/100 default in that case would falsely suggest a "
                       "clean thermal pass (F3)."})
    total_board_dissipation_w: float = field(metadata={
        "description": "Sum of estimated dissipation (W) across all analyzed components."})
    components_analyzed: int = field(metadata={
        "description": "Number of components that received a full thermal assessment "
                       "(may differ from components_assessed if some were filtered)."})
    components_above_85c: int = field(metadata={
        "description": "Count of components with estimated Tj above 85 °C."})
    components_above_tjmax: int = field(metadata={
        "description": "Count of components with estimated Tj above their datasheet Tj_max."})
    ambient_c: float = field(metadata={
        "description": "Ambient temperature (°C) used for the thermal model."})
    hottest_component: Optional[ThermalHottest] = field(default=None, metadata={
        "description": "Hottest analyzed component by estimated Tj. "
                       "Omitted when no components were assessed."})
    skipped_reason: Optional[str] = field(default=None, metadata={
        "description": "Why thermal scoring was skipped (thermal_score is "
                       "None). Present only when no components could be "
                       "assessed — e.g., missing MPNs or no datasheet "
                       "extraction cache. F3."})


@dataclass
class ThermalMissingInfo:
    default_rtheta_ja: list[str] = field(default_factory=list, metadata={
        "description": "Component references that used a package-default Rθ_JA "
                       "because no datasheet value was available. Empty when "
                       "every assessed component had a datasheet-sourced "
                       "Rθ_JA. TH-043."})
    default_tj_max: list[str] = field(default_factory=list, metadata={
        "description": "Component references that used a default max junction "
                       "temperature (typically 125 °C). Empty when every "
                       "assessed component had a datasheet-sourced Tj_max. "
                       "TH-043."})


@dataclass
class ThermalEnvelope:
    """Top-level output of analyze_thermal.py."""
    analyzer_type: str = field(metadata={
        "description": "Always 'thermal'.",
        "const": "thermal"})
    schema_version: str = field(metadata={
        "description": "Schema semver. Value: '1.4.0' at Track 1.1 landing.",
        "const": "1.4.0"})

    # --- Provenance ---
    inputs: InputsBlock = field(metadata={
        "description": "Source JSON inputs, sha256s, run_id, plus upstream "
                       "artifact metadata (schematic, pcb)."})
    compat: CompatBlock = field(metadata={
        "description": "Schema compatibility metadata: minimum consumer "
                       "version + deprecated/experimental field lists."})

    summary: ThermalSummary = field(metadata={
        "description": "Roll-up summary of thermal analysis."})
    findings: list[Finding] = field(metadata={
        "description": "All thermal findings: TS-001..005, TP-001..002."})
    assessments: list[Assessment] = field(metadata={
        "description": "TH-DET entries — per-component junction-temperature "
                       "estimates. Informational (not findings)."})
    trust_summary: TrustSummary = field(metadata={
        "description": "Trust posture rollup."})
    elapsed_s: float = field(metadata={
        "description": "Wall-clock analysis time in seconds."})
    missing_info: Optional[ThermalMissingInfo] = field(default=None, metadata={
        "description": "Emitted when any component used default thermal params."})

    # --- Phase 4 capability pointer ---
    capability_mode_ref: Optional[dict] = field(default=None, metadata={
        "description": "Pointer to canonical analysis/capability_mode.json run-level "
                       "record. Shape: {source, run_id}. See Phase 4 spec §3.3."})
