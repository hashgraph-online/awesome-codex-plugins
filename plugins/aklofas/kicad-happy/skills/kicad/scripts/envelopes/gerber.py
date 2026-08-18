"""Gerber analyzer output envelope (v1.4 SOT).

The runtime of ``analyze_gerbers.py`` emits a tight core (analyzer_type,
schema_version, summary, trust_summary, directory, generator,
layer_count, statistics, completeness, alignment, drill_classification,
pad_summary, findings) plus optional/gated blocks
(trace_widths, component_analysis, net_analysis, job_file, zip_archives,
connectivity) and always emits the gerbers[]/drills[]/drill_tools
structural maps.

Tightens:
    - analyzer_type + schema_version carry ``const`` discriminators.
    - summary, trust_summary, statistics, completeness, alignment,
      drill_classification, pad_summary, trace_widths, component_analysis,
      net_analysis, board_dimensions are typed dataclasses mirroring
      runtime shape.
    - gerbers[]/drills[]/job_file/zip_archives/connectivity are typed as
      ``list[dict]`` / ``dict`` for v1.4 — tightens per entry in v1.5.

Mode gating:
    - ``--full`` adds ``connectivity`` at the top level (flat pin list).
    - Zip archive sweep only emits ``zip_archives`` when a .zip is
      present in the gerber directory.
    - ``trace_widths``, ``component_analysis``, ``net_analysis``,
      ``job_file`` appear only when the source data is parseable.
    - ``audience_summary`` is added by the output filter pipeline.

Additional properties are permitted by JSON Schema default.
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
class GerberSummary:
    """Top-level roll-up (mirrors the runtime's summary dict)."""
    total_findings: int = field(metadata={
        "description": "Count of findings[]."})
    by_severity: BySeverity = field(metadata={
        "description": "Breakdown by severity bucket."})


@dataclass
class GerberStatistics:
    """File/draw/flash/hole counts."""
    gerber_files: int = field(metadata={
        "description": "Count of parsed gerber files."})
    drill_files: int = field(metadata={
        "description": "Count of parsed drill (.drl) files."})
    total_holes: int = field(metadata={
        "description": "Sum of hole counts across all drill files."})
    total_flashes: int = field(metadata={
        "description": "Sum of flash operations across all gerber files."})
    total_draws: int = field(metadata={
        "description": "Sum of draw operations across all gerber files."})


@dataclass
class BoardDimensions:
    """Physical board size derived from gbrjob/Edge.Cuts/fallback."""
    width_mm: Optional[float] = field(default=None, metadata={
        "description": "Board width in mm; null if no dimension source was usable."})
    height_mm: Optional[float] = field(default=None, metadata={
        "description": "Board height in mm; null if no dimension source was usable."})
    area_mm2: Optional[float] = field(default=None, metadata={
        "description": "Board area in mm^2 (width_mm * height_mm); null if "
                       "dimensions unavailable."})
    source: Optional[str] = field(default=None, metadata={
        "description": "Dimension origin: 'gbrjob' | 'edge_cuts' | 'layer_extents'."})


@dataclass
class Completeness:
    """Layer/drill completeness rollup."""
    expected_layers: list[str] = field(metadata={
        "description": "Layers expected for the board stackup "
                       "(sourced from gbrjob when available, filename "
                       "heuristic otherwise)."})
    found_layers: list[str] = field(metadata={
        "description": "Layers actually present in the directory."})
    missing: list[str] = field(metadata={
        "description": "Expected layers not found on disk."})
    extra: list[str] = field(metadata={
        "description": "Found layers not in the expected set."})
    complete: bool = field(metadata={
        "description": "True when missing == [] and all expected layers present."})
    has_pth_drill: bool = field(metadata={
        "description": "True when a plated through-hole drill file was found."})
    has_npth_drill: bool = field(metadata={
        "description": "True when a non-plated through-hole drill file was found."})
    source: str = field(metadata={
        "description": "How expected_layers was derived: 'gbrjob' | "
                       "'filename_heuristic'."})


@dataclass
class LayerExtent:
    """Bounding dimensions of a single layer's drawn content."""
    width: float = field(metadata={
        "description": "Max extent in X (mm) across flashes/draws on this layer."})
    height: float = field(metadata={
        "description": "Max extent in Y (mm) across flashes/draws on this layer."})


@dataclass
class Alignment:
    """Cross-layer alignment report."""
    aligned: bool = field(metadata={
        "description": "True when copper/edge layers agree in outer extents."})
    issues: list[str] = field(metadata={
        "description": "Human-readable descriptions of alignment mismatches."})
    layer_extents: dict[str, LayerExtent] = field(metadata={
        "description": "Per-layer bounding extents keyed by layer name "
                       "(e.g. 'F.Cu', 'Edge.Cuts', 'drill_mixed')."})


@dataclass
class DrillClassTool:
    """One tool/diameter entry inside a drill classification bucket."""
    diameter_mm: float = field(metadata={"description": "Tool diameter in mm."})
    count: int = field(metadata={"description": "Hole count for this tool."})


@dataclass
class DrillClassBucket:
    """A classified bucket of drills (vias, component holes, mounting)."""
    count: int = field(metadata={
        "description": "Total hole count in this bucket."})
    tools: list[DrillClassTool] = field(metadata={
        "description": "Per-diameter breakdown."})


@dataclass
class DrillClassification:
    """Functional classification of drill holes."""
    classification_method: str = field(metadata={
        "description": "How holes were classified: 'x2_attributes' | "
                       "'diameter_heuristic'."})
    vias: DrillClassBucket = field(metadata={
        "description": "Via drills bucket."})
    component_holes: DrillClassBucket = field(metadata={
        "description": "Component pin drills bucket."})
    mounting_holes: DrillClassBucket = field(metadata={
        "description": "Mounting/NPTH drills bucket."})


@dataclass
class PadSummary:
    """Aperture-function rollup from gerber flashes."""
    smd_apertures: int = field(metadata={
        "description": "Count of SMD pad apertures."})
    via_apertures: int = field(metadata={
        "description": "Count of via pad apertures."})
    tht_holes: int = field(metadata={
        "description": "Count of through-hole pad apertures (component drills)."})
    heatsink_apertures: int = field(metadata={
        "description": "Count of heatsink/thermal apertures."})
    smd_ratio: float = field(metadata={
        "description": "SMD pad ratio = smd_apertures / total pads."})
    smd_source: str = field(metadata={
        "description": "Where SMD classification came from: "
                       "'x2_aperture_function' | 'size_heuristic'."})


@dataclass
class TraceWidths:
    """Trace width rollup derived from conductor apertures."""
    unique_widths_mm: list[float] = field(metadata={
        "description": "Sorted list of distinct conductor widths (mm)."})
    width_count: int = field(metadata={
        "description": "Count of unique widths."})
    min_trace_mm: float = field(metadata={
        "description": "Minimum conductor width (mm)."})
    max_trace_mm: float = field(metadata={
        "description": "Maximum conductor width (mm)."})
    min_feature_mm: float = field(metadata={
        "description": "Minimum feature size (mm) — smallest aperture used "
                       "for any conductor/flash."})


@dataclass
class ComponentAnalysis:
    """X2 component attribute rollup."""
    total_unique: int = field(metadata={
        "description": "Count of distinct component references."})
    total_pads: int = field(metadata={
        "description": "Total pad flash count attributed to components."})
    front_side: int = field(metadata={
        "description": "Count of front-side components."})
    back_side: int = field(metadata={
        "description": "Count of back-side components."})
    has_x2_data: bool = field(metadata={
        "description": "True when X2 component attributes were present in "
                       "the gerber stream."})
    component_refs: list[str] = field(metadata={
        "description": "All component references (e.g. ['D1','J1','R1'])."})
    pads_per_component: dict[str, int] = field(metadata={
        "description": "Reference -> pad flash count."})


@dataclass
class NetAnalysis:
    """X2 net attribute rollup."""
    total_unique: int = field(metadata={
        "description": "Count of distinct nets."})
    total_pins: int = field(metadata={
        "description": "Total pin count across all nets."})
    named_nets: int = field(metadata={
        "description": "Count of nets with names."})
    unnamed_nets: int = field(metadata={
        "description": "Count of unnamed/anonymous nets."})
    power_nets: list[str] = field(metadata={
        "description": "Power net names identified (e.g. ['+5V','GND'])."})
    signal_nets: list[str] = field(metadata={
        "description": "Non-power signal net names."})


@dataclass
class DrillTool:
    """One tool from the aggregated drill_tools map."""
    diameter_mm: float = field(metadata={"description": "Tool diameter in mm."})
    count: int = field(metadata={"description": "Hole count for this tool."})
    type: str = field(metadata={
        "description": "Drill file classification: 'PTH' | 'NPTH' | "
                       "'mixed' | 'unknown'."})


@dataclass
class GerberEnvelope:
    """Top-level output of analyze_gerbers.py.

    Tight typing on universal fields; loose ``dict`` / ``list[dict]``
    typing on gerbers[]/drills[]/job_file/zip_archives/connectivity for
    v1.4 (tightens in v1.5).
    """

    # --- Discriminators ---
    analyzer_type: str = field(metadata={
        "description": "Always 'gerber'.",
        "const": "gerber"})
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
    summary: GerberSummary = field(metadata={
        "description": "Roll-up summary (total + by_severity)."})
    trust_summary: TrustSummary = field(metadata={
        "description": "Trust posture rollup (confidence + evidence source)."})
    directory: str = field(metadata={
        "description": "Resolved absolute path of the scanned gerber directory."})
    layer_count: int = field(metadata={
        "description": "Layer count derived from gbrjob or filename heuristic."})
    statistics: GerberStatistics = field(metadata={
        "description": "File / draw / flash / hole totals."})
    completeness: Completeness = field(metadata={
        "description": "Expected-vs-found layers and drill presence."})
    alignment: Alignment = field(metadata={
        "description": "Cross-layer alignment report."})
    drill_classification: DrillClassification = field(metadata={
        "description": "Vias / component / mounting hole breakdown."})
    pad_summary: PadSummary = field(metadata={
        "description": "Aperture-function rollup (SMD / via / TH / heatsink)."})
    findings: list[Finding] = field(metadata={
        "description": "All gerber findings (flat list)."})
    assessments: list[Assessment] = field(metadata={
        "description": "Informational assessments (empty for gerber at v1.4)."})
    board_dimensions: BoardDimensions = field(metadata={
        "description": "Physical board dimensions (from gbrjob or edge cuts)."})
    generator: Optional[str] = field(default=None, metadata={
        "description": "Generator string (e.g. 'Pcbnew 10.0.1-...'); null if "
                       "no GenerationSoftware tag and no gbrjob info."})

    # --- Structural arrays/maps (always emitted even if empty) ---
    # TODO(v1.5): tighten items to typed GerberFile / DrillFile with
    # per-aperture structure and X2 attribute shape.
    gerbers: list[dict] = field(default_factory=list, metadata={
        "description": "Per-gerber-file summary. Each item: "
                       "{filename, layer_type, units, aperture_count, "
                       "draw_count, flash_count, region_count, "
                       "x2_attributes, x2_component_count, x2_net_count, "
                       "x2_pin_count, aperture_analysis}."})
    drills: list[dict] = field(default_factory=list, metadata={
        "description": "Per-drill-file summary. Each item: "
                       "{filename, type, units, hole_count, layer_span, "
                       "tools (T# -> {diameter_mm, hole_count, "
                       "aper_function}), x2_attributes}."})
    # TODO(v1.5): tighten to dict[str, DrillTool].
    drill_tools: dict[str, dict] = field(default_factory=dict, metadata={
        "description": "Aggregated tool map keyed by 'Xmm' diameter label "
                       "with value {diameter_mm, count, type}."})

    # --- Optional blocks (content-gated) ---
    trace_widths: Optional[TraceWidths] = field(default=None, metadata={
        "description": "Trace width rollup; omitted when no conductor "
                       "apertures were observed."})
    component_analysis: Optional[ComponentAnalysis] = field(default=None, metadata={
        "description": "X2 component attribute rollup; omitted when no X2 "
                       "component data in the gerber stream."})
    net_analysis: Optional[NetAnalysis] = field(default=None, metadata={
        "description": "X2 net attribute rollup; omitted when no X2 net "
                       "data in the gerber stream."})
    # TODO(v1.5): tighten to typed JobFile with stackup/design_rules shape.
    job_file: Optional[dict] = field(default=None, metadata={
        "description": "Parsed .gbrjob contents: project_name, vendor, "
                       "generator, layer_count, board_width_mm, "
                       "board_height_mm, board_thickness_mm, creation_date, "
                       "finish, stackup, design_rules, expected_files. "
                       "Omitted when no .gbrjob present."})
    # TODO(v1.5): tighten to typed ZipArchive entries.
    zip_archives: Optional[list[dict]] = field(default=None, metadata={
        "description": "Zip archive sweep; each entry: {filename, "
                       "size_bytes, modified, total_files, gerber_files, "
                       "drill_files, other_files, newest_member_date, "
                       "staleness_warning}. Omitted when no .zip files "
                       "in the directory."})

    # --- --full mode additions ---
    # TODO(v1.5): tighten to typed ConnectivityPin.
    connectivity: Optional[list[dict]] = field(default=None, metadata={
        "description": "Flat pin-to-net list from X2 attributes (--full "
                       "only). Each item: {ref, pin, pin_name, net}."})

    # --- Phase 4 capability pointer ---
    capability_mode_ref: Optional[dict] = field(default=None, metadata={
        "description": "Pointer to canonical analysis/capability_mode.json run-level "
                       "record. Shape: {source, run_id}. See Phase 4 spec §3.3."})

    # --- Stage/audience derived blocks ---
    audience_summary: Optional[dict] = field(default=None, metadata={
        "description": "Designer/reviewer/manager summary views; only "
                       "present when output filters ran."})
