"""Cross-analysis output envelope (v1.4 SOT).

The runtime of ``cross_analysis.py`` emits a minimal top-level shape —
the analyzer is a second-pass consumer of schematic and PCB JSON, so
there are no structural maps of its own. Every cross-domain check
(CC-001, EG-001, DA-001, XV-001..003, NR-001, RP-002, TW-001, PS-002,
VS-002, DP-005) writes into the shared ``findings[]`` array.

Top-level runtime keys (current):
    analyzer_type, schema_version, elapsed_s, summary, findings,
    trust_summary

Stage/audience pipeline may add:
    audience_summary — always added by ``apply_output_filters`` when
                       findings[] is non-empty
    stage_filter     — added only when ``--stage`` is passed

Tightens:
    - analyzer_type + schema_version carry ``const`` discriminators.
    - summary is a typed dataclass mirroring runtime shape
      (total_findings + by_severity).
    - trust_summary reuses shared ``TrustSummary`` primitive.

Additional properties are permitted by JSON Schema default. The
cross-analysis envelope is intentionally small: unlike the schematic /
PCB / EMC analyzers, it produces no structural bags of its own.
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
    TrustSummary, Finding, Assessment, BySeverity, InputsBlock, CompatBlock,
)


@dataclass
class CrossAnalysisSummary:
    """Top-level roll-up (mirrors the runtime's summary dict)."""
    total_findings: int = field(metadata={
        "description": "Count of findings[]."})
    by_severity: BySeverity = field(metadata={
        "description": "Breakdown by severity bucket."})


@dataclass
class CrossAnalysisEnvelope:
    """Top-level output of cross_analysis.py.

    Cross-analysis consumes schematic + PCB analyzer JSON and produces
    findings for checks that span the boundary: connector current
    capacity, ESD coverage gaps, decoupling adequacy, schematic/PCB
    cross-validation, and PCB intelligence (plane splits, trace widths,
    differential pair quality, via stitching density).
    """

    # --- Discriminators ---
    analyzer_type: str = field(metadata={
        "description": "Always 'cross_analysis'.",
        "const": "cross_analysis"})
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
    elapsed_s: float = field(metadata={
        "description": "Analysis wall-clock time in seconds."})
    summary: CrossAnalysisSummary = field(metadata={
        "description": "Roll-up summary (total + by_severity)."})
    findings: list[Finding] = field(metadata={
        "description": "All cross-domain findings."})
    assessments: list[Assessment] = field(metadata={
        "description": "Informational assessments (empty for cross-analysis at v1.4)."})
    trust_summary: TrustSummary = field(metadata={
        "description": "Trust posture rollup (confidence + evidence source)."})

    # --- Phase 4 capability pointer ---
    capability_mode_ref: Optional[dict] = field(default=None, metadata={
        "description": "Pointer to canonical analysis/capability_mode.json run-level "
                       "record. Shape: {source, run_id}. See Phase 4 spec §3.3."})

    # --- Stage/audience derived blocks ---
    audience_summary: Optional[dict] = field(default=None, metadata={
        "description": "Designer/reviewer/manager summary views. Added "
                       "by apply_output_filters whenever findings[] is "
                       "non-empty."})
    stage_filter: Optional[dict] = field(default=None, metadata={
        "description": "Stage-filtered findings rollup. Present only "
                       "when --stage is passed."})
