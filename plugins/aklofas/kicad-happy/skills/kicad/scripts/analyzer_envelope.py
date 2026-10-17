"""Shared envelope primitives for all analyzer outputs.

Source-of-truth types composed by per-analyzer envelope modules. Every
field carries a description via field(metadata={"description": ...}) so
the schema codec can produce self-documenting JSON Schema.

Scope: this module holds only the primitives reused by multiple analyzer
envelopes (ByConfidence, ByEvidenceSource, BySeverity, BomCoverage,
TrustSummary, TitleBlock, Finding). Analyzer-specific types — Statistics,
SchematicSummary, PCBSummary, ThermalSummary, etc. — live in
``envelopes/*.py`` alongside each analyzer's top-level envelope.

Primitive pairings: ``BySeverity`` is composed by per-analyzer
``<X>Summary`` dataclasses (e.g. ``SchematicSummary.by_severity``,
``ThermalSummary.by_severity``) to report the severity histogram for
that run. ``TrustSummary`` is the trust-posture rollup (confidence +
evidence source) and deliberately does NOT include a severity
breakdown — severity lives on the per-analyzer Summary, trust posture
lives on TrustSummary.

Serialization convention: dataclass field names use snake_case Python
identifiers; the emitted JSON uses the same names verbatim. No alias
layer. When a key in the emitted JSON contains a hyphen (like
'datasheet-backed' in trust_summary.by_confidence), we rename to
snake_case ('datasheet_backed') as part of the v1.4 schema break.
Consumers must update. This is documented in the v1.4 release notes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ByConfidence:
    """Count of findings by confidence bucket."""
    deterministic: int = field(metadata={
        "description": "Findings with deterministic evidence (topology, exact match)."})
    heuristic: int = field(metadata={
        "description": "Findings from heuristic pattern matching."})
    datasheet_backed: int = field(metadata={
        "description": "Findings validated against extracted datasheet facts. "
                       "Key renamed from 'datasheet-backed' at v1.4."})


@dataclass
class ByEvidenceSource:
    """Count of findings by evidence source taxonomy."""
    datasheet: int = field(metadata={"description": "Extracted datasheet table/prose."})
    topology: int = field(metadata={"description": "Schematic topology inference."})
    heuristic_rule: int = field(metadata={"description": "Pattern/rule heuristic."})
    symbol_footprint: int = field(metadata={"description": "KiCad symbol or footprint metadata."})
    bom: int = field(metadata={"description": "BOM property (MPN/value/description)."})
    geometry: int = field(metadata={"description": "PCB geometric measurement."})
    api_lookup: int = field(metadata={"description": "Distributor/vendor API lookup."})


@dataclass
class BySeverity:
    """Count of findings by severity bucket (v1.3 vocabulary)."""
    error: int = field(metadata={"description": "Severity 'error' count."})
    warning: int = field(metadata={"description": "Severity 'warning' count."})
    info: int = field(metadata={"description": "Severity 'info' count."})


@dataclass
class BomCoverage:
    """BOM coverage percentages (schematic analyzer only)."""
    mpn_pct: float = field(metadata={
        "description": "Percent of non-power components with an MPN property."})
    datasheet_pct: float = field(metadata={
        "description": "Percent of non-power components with a datasheet URL or local file."})


@dataclass
class TrustSummary:
    """Rollup of finding trust posture across an analyzer run.

    Emitted by every analyzer. Bom coverage is schematic-only.
    """
    total_findings: int = field(metadata={"description": "Count of findings[]."})
    trust_level: str = field(metadata={
        "description": "Aggregate trust label: 'high', 'mixed', or 'low'."})
    by_confidence: ByConfidence = field(metadata={
        "description": "Breakdown of findings[] by confidence bucket."})
    by_evidence_source: ByEvidenceSource = field(metadata={
        "description": "Breakdown of findings[] by evidence source."})
    provenance_coverage_pct: Optional[float] = field(default=None, metadata={
        "description": "Percent of findings[] carrying explicit provenance metadata. "
                       "None when total_findings == 0 (avoids misleading '100% of nothing')."})
    bom_coverage: Optional[BomCoverage] = field(default=None, metadata={
        "description": "BOM coverage — emitted by schematic analyzer only."})


@dataclass
class TitleBlock:
    """KiCad title block (schematic only)."""
    title: Optional[str] = field(default=None, metadata={"description": "Title."})
    date: Optional[str] = field(default=None, metadata={"description": "Date."})
    rev: Optional[str] = field(default=None, metadata={"description": "Revision."})
    company: Optional[str] = field(default=None, metadata={"description": "Company."})
    comments: Optional[dict[str, str]] = field(default=None, metadata={
        "description": "Comments by number ('1', '2', ...) -> text."})


@dataclass
class Finding:
    """One entry in an analyzer's findings[] array.

    This is the rich-finding envelope locked in v1.3 round 2. Detector-
    specific fields live in `extra` as a free-form dict (JSON object with
    no schema constraint for v1.4; tightened per-rule_id in v1.5).
    """
    detector: str = field(metadata={
        "description": "Detector name (e.g. 'voltage_divider', 'ld_1117')."})
    rule_id: str = field(metadata={
        "description": "Stable rule identifier (e.g. 'PU-001', 'TS-001')."})
    severity: str = field(metadata={
        "description": "'error' | 'warning' | 'info'."})
    confidence: str = field(metadata={
        "description": "'deterministic' | 'heuristic' | 'datasheet-backed'."})
    evidence_source: str = field(metadata={
        "description": "Evidence taxonomy: 'datasheet', 'topology', 'heuristic_rule', "
                       "'symbol_footprint', 'bom', 'geometry', 'api_lookup'."})
    summary: str = field(metadata={"description": "One-line human-readable summary."})
    category: Optional[str] = field(default=None, metadata={
        "description": "Domain category: 'power', 'signal_integrity', 'dfm', etc."})
    components: Optional[list[str]] = field(default=None, metadata={
        "description": "Component references involved (e.g. ['R1', 'U3'])."})
    nets: Optional[list[str]] = field(default=None, metadata={
        "description": "Net names involved."})
    # TODO(v1.5): tighten to list[PinRef] once detectors emit consistent shape.
    pins: Optional[list] = field(default=None, metadata={
        "description": "Pins involved. Items may be dicts "
                       "({component, pin_number, pin_name}) or shorthand "
                       "strings ('R1.2'). Pin shape tightens to typed "
                       "PinRef in v1.5."})
    recommendation: Optional[str] = field(default=None, metadata={
        "description": "Actionable fix or next step for the designer."})
    description: Optional[str] = field(default=None, metadata={
        "description": "Longer-form description (optional, rendered in reports)."})
    report_context: Optional[dict] = field(default=None, metadata={
        "description": "Free-form context block for report rendering "
                       "(e.g. measured values, thresholds, schematic snippet references). "
                       "Tightens to typed shape per rule_id in v1.5."})
    provenance: Optional[dict] = field(default=None, metadata={
        "description": "Evidence provenance (source_file, sha256, extraction_id, ...). "
                       "Tightens to typed Provenance in v1.5."})
    detection_id: Optional[str] = field(default=None, metadata={
        "description": "Stable per-finding ID for cross-run tracking."})
    finding_id: Optional[str] = field(default=None, metadata={
        "description": "Stable cross-run identifier derived in make_finding(). "
                       "Format: {source}:{detection_id} or {source}:{rule_id}:{locator}. "
                       "See Phase 4 spec §3.2."})
    stages: Optional[list[str]] = field(default=None, metadata={
        "description": "Review stages this finding applies to: "
                       "'schematic', 'layout', 'pre_fab', 'bring_up'."})
    extra: Optional[dict] = field(default=None, metadata={
        "description": "Detector-specific extension fields (unconstrained for v1.4). "
                       "Tightens to per-rule_id typed schema in v1.5."})


@dataclass
class Assessment:
    """One entry in an analyzer's assessments[] array.

    Assessments are informational measurements — factual observations a
    consumer may surface alongside findings but that do not themselves
    imply any action or warning. They are NOT trust-summarized (no
    severity, no recommendation). Domain-specific measurement fields
    (e.g. junction temperature, margin, current draw) live in `extra`.

    Example: thermal TH-DET entries (per-component Tj estimates) are
    assessments, not findings. A thermal *warning* about a component
    exceeding its Tj_max is a Finding; a thermal *measurement* that a
    component is running at 45°C with 80°C of margin is an Assessment.
    """
    detector: str = field(metadata={
        "description": "Analyzer that produced the assessment (e.g. 'analyze_thermal')."})
    rule_id: str = field(metadata={
        "description": "Stable rule identifier (e.g. 'TH-DET')."})
    confidence: str = field(metadata={
        "description": "'deterministic' | 'heuristic' | 'datasheet-backed'."})
    evidence_source: str = field(metadata={
        "description": "Evidence taxonomy: 'datasheet', 'topology', 'heuristic_rule', "
                       "'symbol_footprint', 'bom', 'geometry', 'api_lookup'."})
    summary: str = field(metadata={"description": "One-line human-readable summary."})
    category: Optional[str] = field(default=None, metadata={
        "description": "Domain category: 'thermal', 'power', 'signal_integrity', etc."})
    components: Optional[list[str]] = field(default=None, metadata={
        "description": "Component references the assessment applies to."})
    nets: Optional[list[str]] = field(default=None, metadata={
        "description": "Net names the assessment applies to."})
    # TODO(v1.5): tighten to list[PinRef] once detectors emit consistent shape.
    pins: Optional[list] = field(default=None, metadata={
        "description": "Pins involved. Items may be dicts or shorthand strings ('R1.2'). "
                       "Pin shape tightens to typed PinRef in v1.5."})
    description: Optional[str] = field(default=None, metadata={
        "description": "Longer-form description (optional, rendered in reports)."})
    report_context: Optional[dict] = field(default=None, metadata={
        "description": "Free-form context block for report rendering "
                       "(e.g. thresholds, standard refs)."})
    provenance: Optional[dict] = field(default=None, metadata={
        "description": "Evidence provenance (source_file, sha256, extraction_id, ...)."})
    detection_id: Optional[str] = field(default=None, metadata={
        "description": "Stable per-assessment ID for cross-run tracking."})
    finding_id: Optional[str] = field(default=None, metadata={
        "description": "Stable cross-run identifier. When populated, format is "
                       "{source}:{detection_id} or {source}:{rule_id}:{locator} per Phase 4 spec §3.2. "
                       "Populated by make_finding() for findings; thermal assessments carry None until Task 4."})
    extra: Optional[dict] = field(default=None, metadata={
        "description": "Assessment-specific measurement fields (e.g. tj_estimated_c, "
                       "margin_c, pdiss_w for thermal). Free-form for v1.4; tightens "
                       "to per-rule_id typed schema in v1.5."})


@dataclass
class UpstreamArtifact:
    """One entry in ``InputsBlock.upstream_artifacts``.

    Names a prior analyzer JSON that this run consumed. Carries the
    artifact's sha256 so consumers can detect whether the upstream has
    drifted since the downstream run read it, plus the upstream's
    schema_version and run_id so cross-run provenance chains can be
    walked.
    """
    path: str = field(metadata={
        "description": "Path to the upstream analyzer JSON file."})
    sha256: str = field(metadata={
        "description": "SHA-256 of the upstream JSON at read time "
                       "(hex, unprefixed)."})
    schema_version: str = field(metadata={
        "description": "schema_version of the upstream envelope."})
    run_id: str = field(metadata={
        "description": "run_id of the upstream run (for provenance chains)."})


@dataclass
class InputsBlock:
    """Provenance record of everything an analyzer run consumed.

    Emitted by every analyzer. ``source_files`` and ``source_hashes`` list
    every file read from disk. ``upstream_artifacts`` carries structured
    metadata about prior-stage analyzer JSONs (thermal reads schematic +
    pcb JSON; EMC and cross-analysis do the same). Raw-input analyzers
    (schematic, pcb, gerber) emit an empty ``upstream_artifacts`` dict.

    ``run_id`` uniquely identifies this run (see ``run_id.py`` for
    format). ``config_hash`` is sha256 of the resolved
    ``.kicad-happy.json`` when one was loaded, otherwise null.
    """
    source_files: list[str] = field(metadata={
        "description": "Paths of every file read from disk during this run, "
                       "in the order read."})
    source_hashes: dict[str, str] = field(metadata={
        "description": "Map: source_file path -> SHA-256 hex. Every entry in "
                       "source_files has a corresponding entry here."})
    run_id: str = field(metadata={
        "description": "Unique identifier for this analyzer run. Format: "
                       "'YYYYMMDDTHHMMSSZ-<6 hex chars>' "
                       "(see run_id.generate_run_id)."})
    upstream_artifacts: dict[str, UpstreamArtifact] = field(metadata={
        "description": "Map: stage name ('schematic', 'pcb', ...) -> "
                       "UpstreamArtifact. Empty for raw-input analyzers."})
    config_hash: Optional[str] = field(default=None, metadata={
        "description": "SHA-256 of the resolved .kicad-happy.json config file, "
                       "or null when no project config was loaded."})


@dataclass
class CompatBlock:
    """Schema compatibility metadata.

    Surfaces which consumer version is required to safely read this
    envelope, plus structured deprecation state. For v1.4 all envelopes
    emit ``minimum_consumer_version="1.4.0"`` with empty deprecation and
    experimental lists — the v1.4 clean break removed prior residue. As
    fields are scheduled for removal in v1.5+ or introduced as
    experimental, they accumulate here.

    Dotted-path strings identify envelope keys (e.g.
    ``"trust_summary.by_confidence.datasheet-backed"``).
    """
    minimum_consumer_version: str = field(metadata={
        "description": "Minimum consumer library/CLI version required to "
                       "safely read this envelope. Typically matches the "
                       "analyzer's schema_version."})
    deprecated_fields: list[str] = field(metadata={
        "description": "Dotted-path names of envelope keys scheduled for "
                       "removal in a future minor/major release. Consumers "
                       "should log or refuse reads that rely on these."})
    experimental_fields: list[str] = field(metadata={
        "description": "Dotted-path names of envelope keys whose shape may "
                       "change without a schema_version bump. Consumers "
                       "should treat them as best-effort."})
