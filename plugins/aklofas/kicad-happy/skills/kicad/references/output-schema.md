# Analyzer JSON Output Schema

**Generated from envelope dataclasses. Do not hand-edit.**
Regenerate: `python3 skills/kicad/scripts/gen_output_schema_md.py`

Source-of-truth modules:
- `skills/kicad/scripts/analyzer_envelope.py` — shared primitives (TrustSummary, Finding, BySeverity, ...)
- `skills/kicad/scripts/envelopes/*.py` — per-analyzer envelopes (schematic, pcb, gerber, thermal, cross_analysis)
- `skills/emc/scripts/emc_envelope.py` — EMC envelope

For the authoritative machine-readable JSON Schema Draft 2020-12, use `--schema` on any analyzer:

```bash
python3 skills/kicad/scripts/analyze_schematic.py --schema
python3 skills/kicad/scripts/analyze_pcb.py --schema
python3 skills/kicad/scripts/analyze_gerbers.py --schema
python3 skills/kicad/scripts/analyze_thermal.py --schema
python3 skills/emc/scripts/analyze_emc.py --schema
python3 skills/kicad/scripts/cross_analysis.py --schema
```

v1.4 schema-break notes:
- Output of `--schema` is real JSON Schema Draft 2020-12 (prior: descriptive-string dict).
- `schema_version` bumped 1.3.0 → 1.4.0 on every analyzer.
- `trust_summary.by_confidence` aggregate key renamed: `datasheet-backed` → `datasheet_backed`. Per-finding `confidence` VALUE stays `datasheet-backed`.

## Contract Tiers

Every analyzer envelope is organized into three tiers. Consumers can
rely on Tier 1 shapes; Tier 2 is analyzer-specific and best read via
the declared dataclass types; Tier 3 is compatibility residue slated
for removal and should not be written against in new code.

### Tier 1 — Standardized envelope (stable across v1.4)

Present on every analyzer output. Shape locked by the shared primitives
in `analyzer_envelope.py`. Breaking changes bump the analyzer's
`schema_version`.

- `analyzer_type` — `const` string discriminator naming the analyzer.
- `schema_version` — `const` string matching the semver.
- `summary` — per-analyzer roll-up (`total_findings`, `by_severity`,
  analyzer-specific counts). Inner shape is analyzer-specific but the
  top-level key is Tier 1.
- `trust_summary` — trust posture: `total_findings`, `trust_level`,
  `by_confidence`, `by_evidence_source`, `provenance_coverage_pct`,
  `bom_coverage` (schematic only).
- `findings` — `list[Finding]`. Actionable items with severity +
  recommendation.
- `assessments` — `list[Assessment]`. Informational measurements (no
  severity, no recommendation). Empty on analyzers with no assessment
  content today.
- `inputs` — `InputsBlock`. `source_files`, `source_hashes`, `run_id`,
  `config_hash`, `upstream_artifacts`.
- `compat` — `CompatBlock`. `minimum_consumer_version`,
  `deprecated_fields`, `experimental_fields`.

### Tier 2 — Analyzer-specific body

Everything emitted by a given analyzer that is not listed in Tier 1.
Shape is declared by the per-analyzer envelope in `envelopes/*.py` or
`emc_envelope.py`. Typical Tier 2 keys include `statistics`,
`components`, `nets`, `bom`, `ic_pin_analysis`, `design_analysis`,
`bus_topology`, `placement_analysis`, `power_net_routing`,
`connectivity_graph`, EMC `test_plan` / `regulatory_coverage`, thermal
`thermal_score`, gerber `layers` / `drills` / `completeness`, etc.

Several Tier 2 fields are currently typed as loose `dict` or
`list[dict]` with `TODO(v1.5)` markers. Consumers that need stable
shapes from these should wait for the v1.5 per-rule_id tightening pass.

### Tier 3 — Compatibility residue

Empty for v1.4. The v1.4 clean break removed prior residue:

- `schematic.file`, `pcb.file` — removed; use `inputs.source_files[0]`.
- `thermal.thermal_assessments` — renamed to `thermal.assessments`
  (sibling to `findings`, not inside it).
- Descriptive-string `--schema` output — replaced by real JSON Schema
  Draft 2020-12.
- `trust_summary.by_confidence.datasheet-backed` key — renamed to
  `datasheet_backed` (hyphen removed only for the aggregate-count key;
  the per-finding `confidence` VALUE still uses `datasheet-backed`).
- Deprecated `summary.critical` / `.high` / `.medium` / `.low` / `.info`
  keys on thermal — removed in v1.4.

## SchematicEnvelope

Output of `python3 skills/kicad/scripts/analyze_schematic.py <file>.kicad_sch`.

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `analyzer_type` | `string` | yes | Always 'schematic'. |
| `schema_version` | `string` | yes | Semver. Value: '1.4.0' at Track 1.1 landing. |
| `inputs` | `InputsBlock` | yes | Source files, hashes, run_id, config_hash, upstream artifacts for this run. |
| `compat` | `CompatBlock` | yes | Schema compatibility metadata: minimum consumer version + deprecated/experimental field lists. |
| `summary` | `SchematicSummary` | yes | Roll-up summary (total + by_severity). |
| `trust_summary` | `TrustSummary` | yes | Trust posture rollup (confidence + evidence source + optional BOM coverage). |
| `kicad_version` | `string` | yes | KiCad generator version string, e.g. '9.0' or '5 (legacy)'. |
| `file_version` | `string` | yes | KiCad file format version string. |
| `title_block` | `TitleBlock` | yes | KiCad title block (title/date/rev/company/comments). |
| `statistics` | `Statistics` | yes | Component, net, and coverage counts. |
| `findings` | `list[Finding]` | yes | All findings (flat, rich-finding format). |
| `assessments` | `list[Assessment]` | yes | Informational assessments (empty for schematic at v1.4; reserved for future measurement-style records). |
| `bom` | `list[BomEntry]` | yes | Deduplicated BOM rows. |
| `components` | `list[dict]` | yes | Every non-power component as a dict. Shape is effectively open: reference/value/lib_id/footprint/datasheet/description/mpn/manufacturer/distributor SKUs/geometry/uuid/type/parsed_value plus internal bookkeeping (_sheet, pin_nets, pin_uuids). Tightens to a typed Component in v1.5. |
| `nets` | `dict[str, NetEntry]` | yes | Net connectivity map keyed by net name. |
| `subcircuits` | `list[dict]` | yes | Hierarchical sub-sheets: [{reference, path, sheet_name, sheet_file, instances}]. |
| `ic_pin_analysis` | `list[dict]` | yes | Per-IC pin mappings. Each entry carries reference, value, type, lib_id, mpn, description, datasheet, function, total_pins, unconnected_pins, pins[], power_pins[], signal_pins[], decoupling_caps_by_rail. Covers type in {ic, connector, crystal, oscillator}; transistors live in transistor_pin_analysis[] (F4). |
| `transistor_pin_analysis` | `list[dict]` | yes | Per-transistor pin mappings. Same shape as ic_pin_analysis entries but filtered to type=transistor (MOSFETs, BJTs, FETs). Lets bridge / half-bridge / gate-driver reviewers verify gate/source/drain wiring without reconstructing pin maps from nets[].pins[] by hand. F4. |
| `design_analysis` | `dict` | yes | Design-level analyses: net_classification, power_domains, cross_domain_signals, bus_analysis (i2c/spi/uart/can), differential_pairs, erc_warnings, passive_warnings. |
| `connectivity_issues` | `dict` | yes | Connectivity issue lists: single_pin_nets, single_pin_net_findings, multi_driver_nets, unconnected_pins, power_net_summary. |
| `annotation_issues` | `dict` | yes | Annotation issue bag: duplicate_references, unannotated, missing_value, zero_indexed_refs. |
| `ground_domains` | `dict` | yes | Ground topology: ground_nets, multiple_domains, domains, optional star-ground note. |
| `bus_topology` | `dict` | yes | Bus wire statistics: bus_wire_count, bus_entry_count. |
| `wire_geometry` | `dict` | yes | Wire-geometry summary: total_wires, total_length_mm, avg_length_mm, optional diagonal/short-wire callouts. |
| `simulation_readiness` | `dict` | yes | SPICE readiness rollup: total_components, likely_simulatable, needs_model, simulatable_percent, components_without_model. |
| `hierarchical_labels` | `dict` | yes | Label counts: global_label_count, hierarchical_label_count, optional unconnected_hierarchical or conflict warnings. |
| `placement_analysis` | `dict` | yes | Placement stats: bounding_box, clusters, grid_size. |
| `property_issues` | `dict` | yes | Property validation issues: missing/mismatched symbol properties (MPN, footprint, datasheet, value), blank description fields, non-ASCII character warnings. Keyed by issue category. |
| `sourcing_audit` | `dict` | yes | Sourcing audit: missing_mpn/digikey/lcsc lists, mpn_coverage, mpn_percent, total_bom_components. |
| `rail_voltages` | `dict[str, float \| null]` | yes | Per-net rail voltage (volts). Nulls permitted for ground or unresolved rails. |
| `labels` | `list[dict]` | no | Extracted label records. |
| `no_connects` | `list[dict]` | no | Extracted no-connect flag records. |
| `power_symbols` | `list[dict]` | no | Power symbol placements: [{net_name, x, y, lib_id, _sheet, _power_scope}]. |
| `pwr_flag_warnings` | `list[dict]` | no | PWR_FLAG warnings: [{net, message, pin_types}]. |
| `label_shape_warnings` | `list` | no | Label-shape mismatch warnings. |
| `footprint_filter_warnings` | `list` | no | Footprint filter warnings from lib_symbols. |
| `capability_mode_ref` | `dict \| null` | no | Pointer to canonical analysis/capability_mode.json run-level record. Shape: {source, run_id}. See Phase 4 spec §3.3. |
| `audience_summary` | `dict \| null` | no | Designer/reviewer/manager summary views; only present when output filters ran. |
| `design_intent` | `dict \| null` | no | Resolved design intent: approved_manufacturers, ipc_class, target_market, operating_temp_range, preferred_passive_size, product_class, test_coverage_target, expected_lifetime_years, detection_signals, source, confidence. |
| `project_config` | `dict \| null` | no | Copy of the resolved project block from .kicad-happy.json (when present). |
| `project_settings` | `dict \| null` | no | Selected KiCad project settings extracted from .kicad_pro (when present). |
| `bom_lock` | `dict \| null` | no | BOM lock verification: status, lock_pct, components_with_mpn, missing_mpn, etc. |
| `bom_optimization` | `dict \| null` | no | BOM optimization bag: single_use_passive_values, unique_value_counts, total_unique_footprints, consolidation_suggestions. |
| `missing_info` | `dict \| null` | no | Data-gap rollup: missing_mpn, missing_footprint, missing_datasheet, heuristic_vref. |
| `sleep_current_audit` | `dict \| null` | no | Sleep-current audit: rails, total_estimated_sleep_uA, realistic_total_uA, conditional_pull_up_uA, observations. |
| `test_coverage` | `dict \| null` | no | Test coverage audit: test_points, test_point_count, covered_nets, uncovered_key_nets, observations, optional debug_connectors. |
| `assembly_complexity` | `dict \| null` | no | Assembly complexity score and breakdown. |
| `power_budget` | `dict \| null` | no | Estimated power budget per rail. |
| `power_sequencing` | `dict \| null` | no | Power sequencing dependencies and warnings. |
| `power_sequencing_validation` | `dict \| null` | no | Validated power tree with provenance. |
| `pdn_impedance` | `dict \| null` | no | PDN impedance analysis per rail. |
| `usb_compliance` | `dict \| null` | no | USB compliance checks. |
| `inrush_analysis` | `dict \| null` | no | Inrush current estimation by rail. |
| `protocol_compliance` | `dict \| null` | no | Protocol compliance checks (I2C/SPI/UART/etc.). |
| `text_annotations` | `list \| null` | no | Text annotations extracted from the schematic. |
| `alternate_pin_summary` | `dict \| null` | no | Alternate-pin usage summary. |
| `pin_coverage_warnings` | `list[PinCoverageWarning] \| null` | no | KH-323: warnings about pin coverage gaps. Emitted when a placed symbol has fewer pins connected than the library definition expects. Present only when such warnings fire. |
| `instance_consistency_warnings` | `list \| null` | no | Multi-instance symbol consistency warnings. |
| `generic_symbol_warnings` | `list \| null` | no | Warnings about generic symbol usage without MPN. |
| `sheets` | `list \| null` | no | Hierarchical sheet list (multi-sheet only). |
| `sheets_parsed` | `int \| null` | no | Count of parsed sheets (legacy .sch). |
| `sheet_files` | `list[string] \| null` | no | Parsed sheet file paths (legacy .sch). |
| `legacy_analysis_quality` | `dict \| null` | no | Legacy .sch quality rollup: is_legacy_schematic, library_resolution, pin_source_coverage. |
| `hierarchy_context` | `dict \| null` | no | Hierarchy context (sub-sheet analysis): root_schematic, target_sheet, sheets_in_project, cross_sheet_nets, project_power_rails, reference_corrections_applied. |
| `hierarchy_warning` | `string \| null` | no | Emitted when sub-sheet was detected without root. |
| `_redirected_from` | `string \| null` | no | Original filename when a sub-sheet was redirected to the project root. Emitted in JSON as '_redirected_from'. |
| `_stale_file_warning` | `string \| null` | no | Emitted when input file is not in the project sheet tree. Emitted in JSON as '_stale_file_warning'. |
| `net_classifications` | `dict \| null` | no | Per-net classification map promoted from signal_analysis (legacy alias of design_analysis.net_classification). |

## PCBEnvelope

Output of `python3 skills/kicad/scripts/analyze_pcb.py <file>.kicad_pcb`.

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `analyzer_type` | `string` | yes | Always 'pcb'. |
| `schema_version` | `string` | yes | Semver. Value: '1.4.0' at Track 1.1 landing. |
| `inputs` | `InputsBlock` | yes | Source files, hashes, run_id, config_hash, upstream artifacts for this run. |
| `compat` | `CompatBlock` | yes | Schema compatibility metadata: minimum consumer version + deprecated/experimental field lists. |
| `summary` | `PCBSummary` | yes | Roll-up summary (total + by_severity). |
| `trust_summary` | `TrustSummary` | yes | Trust posture rollup (confidence + evidence source). |
| `kicad_version` | `string` | yes | KiCad generator version string, e.g. '9.0'. |
| `file_version` | `string` | yes | KiCad file format version string (e.g. '20241228'). |
| `findings` | `list[Finding]` | yes | All PCB findings (flat list). |
| `assessments` | `list[Assessment]` | yes | Informational assessments (empty for PCB at v1.4). |
| `statistics` | `PCBStatistics` | yes | Board/component/net counts and routing rollup. |
| `setup` | `PCBSetup` | yes | Board setup block (thickness, soldermask, etc.). |
| `board_outline` | `BoardOutline` | yes | Edge.Cuts outline geometry + bounding box. |
| `connectivity` | `Connectivity` | yes | Routing completeness rollup. |
| `tracks` | `Tracks` | yes | Track summary + optional detailed arrays under --full. |
| `vias` | `Vias` | yes | Via summary + optional detailed array under --full. |
| `nets` | `dict[str, string]` | yes | Net ID (as string) -> net name. |
| `net_name_to_id` | `dict[str, int]` | yes | Net name -> integer net ID. Reverse of nets. |
| `layers` | `list[dict]` | yes | Layer stackup entries: [{number, name, type, alias}]. |
| `footprints` | `list[dict]` | yes | Every placed footprint. Fields include reference, value, library, footprint, layer, x, y, angle, type, mpn, manufacturer, description, pad_count, courtyard, courtyard_poly, pad_nets, connected_nets, sch_path, sheetname, sheetfile. Tightens to typed Footprint in v1.5. |
| `zones` | `list[dict]` | yes | Copper zones: [{net, net_name, layers, clearance, min_thickness, thermal_gap, thermal_bridge_width, outline_points, outline_area_mm2, is_filled, outline_bbox}]. |
| `keepout_zones` | `list[dict]` | yes | Keepout zones: [{name, layers, restrictions, bounding_box, area_mm2, nearby_components}]. |
| `net_classes` | `list[dict]` | yes | Net class definitions: [{name, clearance, track_width, via_diameter, via_drill}]. |
| `net_lengths` | `list[dict]` | yes | Per-net track length rollup: [{net, net_number, total_length_mm, segment_count, via_count, layers}]. |
| `component_groups` | `dict[str, ComponentGroup]` | yes | Refdes prefix -> {count, references}. |
| `silkscreen` | `dict` | yes | Silkscreen rollup: board_text_count, refs_visible_on_silk, refs_hidden_on_silk, documentation_warnings[], fab_notes_completeness, silkscreen_completeness. |
| `dfm_summary` | `dict` | yes | DFM rollup: dfm_tier, metrics, violation_count. |
| `project_settings` | `dict` | yes | Selected settings extracted from .kicad_pro: source, net_classes, design_rules. |
| `design_rule_compliance` | `dict` | no | Design rule compliance: compliant, rules_checked, rules_source; empty dict when project_settings missing or compliance not computed. TH-043. |
| `board_thickness_mm` | `float \| null` | no | Stackup thickness (mm); duplicated from setup for downstream consumers. Null when the source file has no (general (thickness ...)) entry. TH-043. |
| `board_metadata` | `dict` | no | Board metadata bag (paper size, title block fragments, etc.); empty dict when no metadata extracted. TH-043. |
| `power_net_routing` | `list[dict]` | no | Power net routing rollup: [{net, track_count, total_length_mm, min_width_mm, max_width_mm, widths_used}]; empty list when no power routing detected. TH-043-residual. |
| `ground_domains` | `dict` | no | Ground topology: domain_count, domains[], multi_domain_components. Always emitted; domain_count=0 is meaningful (no ground domain found). TH-043-residual. |
| `placement_density` | `dict` | no | Placement density: board_area_cm2, front_density_per_cm2, optional back_density_per_cm2; empty dict when density not computed. TH-043-residual. |
| `capability_mode_ref` | `dict \| null` | no | Pointer to canonical analysis/capability_mode.json run-level record. Shape: {source, run_id}. See Phase 4 spec §3.3. |
| `audience_summary` | `dict \| null` | no | Designer/reviewer/manager summary views; only present when output filters ran. |
| `design_intent` | `dict \| null` | no | Resolved design intent: product_class, ipc_class, target_market, operating_temp_range, preferred_passive_size, test_coverage_target, approved_manufacturers, expected_lifetime_years, detection_signals, confidence, source. |
| `project_config` | `dict \| null` | no | Copy of the resolved project block from .kicad-happy.json (when present). |
| `connectivity_graph` | `dict \| null` | no | Per-net connectivity graph (island map). Emitted only in --full mode. |
| `pad_to_pad_distances` | `dict \| null` | no | Pad-to-pad routing distances keyed by 'R1.2-D1.1' style endpoints. Emitted only in --full mode. |
| `thermal_analysis` | `dict \| null` | no | Thermal management analysis (when triggered). |
| `thermal_pad_vias` | `dict \| null` | no | Thermal pad via audit (when triggered). |
| `trace_proximity` | `dict \| null` | no | Trace proximity / crosstalk analysis (--proximity). |
| `copper_presence` | `dict \| null` | no | Copper presence sampling rollup (when triggered). |
| `tombstoning_risk` | `dict \| null` | no | Tombstoning risk analysis (when triggered). |
| `decoupling_placement` | `dict \| null` | no | Decoupling capacitor placement audit (when triggered). |
| `current_capacity` | `dict \| null` | no | Current capacity analysis (when triggered). |
| `placement_analysis` | `dict \| null` | no | Placement analysis details (when triggered). |
| `dfm` | `dict \| null` | no | Extended DFM analysis (when triggered). |

## GerberEnvelope

Output of `python3 skills/kicad/scripts/analyze_gerbers.py <gerber_dir>/`.

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `analyzer_type` | `string` | yes | Always 'gerber'. |
| `schema_version` | `string` | yes | Semver. Value: '1.4.0' at Track 1.1 landing. |
| `inputs` | `InputsBlock` | yes | Source files, hashes, run_id, config_hash, upstream artifacts for this run. |
| `compat` | `CompatBlock` | yes | Schema compatibility metadata: minimum consumer version + deprecated/experimental field lists. |
| `summary` | `GerberSummary` | yes | Roll-up summary (total + by_severity). |
| `trust_summary` | `TrustSummary` | yes | Trust posture rollup (confidence + evidence source). |
| `directory` | `string` | yes | Resolved absolute path of the scanned gerber directory. |
| `layer_count` | `int` | yes | Layer count derived from gbrjob or filename heuristic. |
| `statistics` | `GerberStatistics` | yes | File / draw / flash / hole totals. |
| `completeness` | `Completeness` | yes | Expected-vs-found layers and drill presence. |
| `alignment` | `Alignment` | yes | Cross-layer alignment report. |
| `drill_classification` | `DrillClassification` | yes | Vias / component / mounting hole breakdown. |
| `pad_summary` | `PadSummary` | yes | Aperture-function rollup (SMD / via / TH / heatsink). |
| `findings` | `list[Finding]` | yes | All gerber findings (flat list). |
| `assessments` | `list[Assessment]` | yes | Informational assessments (empty for gerber at v1.4). |
| `board_dimensions` | `BoardDimensions` | yes | Physical board dimensions (from gbrjob or edge cuts). |
| `generator` | `string \| null` | no | Generator string (e.g. 'Pcbnew 10.0.1-...'); null if no GenerationSoftware tag and no gbrjob info. |
| `gerbers` | `list[dict]` | no | Per-gerber-file summary. Each item: {filename, layer_type, units, aperture_count, draw_count, flash_count, region_count, x2_attributes, x2_component_count, x2_net_count, x2_pin_count, aperture_analysis}. |
| `drills` | `list[dict]` | no | Per-drill-file summary. Each item: {filename, type, units, hole_count, layer_span, tools (T# -> {diameter_mm, hole_count, aper_function}), x2_attributes}. |
| `drill_tools` | `dict[str, dict]` | no | Aggregated tool map keyed by 'Xmm' diameter label with value {diameter_mm, count, type}. |
| `trace_widths` | `TraceWidths \| null` | no | Trace width rollup; omitted when no conductor apertures were observed. |
| `component_analysis` | `ComponentAnalysis \| null` | no | X2 component attribute rollup; omitted when no X2 component data in the gerber stream. |
| `net_analysis` | `NetAnalysis \| null` | no | X2 net attribute rollup; omitted when no X2 net data in the gerber stream. |
| `job_file` | `dict \| null` | no | Parsed .gbrjob contents: project_name, vendor, generator, layer_count, board_width_mm, board_height_mm, board_thickness_mm, creation_date, finish, stackup, design_rules, expected_files. Omitted when no .gbrjob present. |
| `zip_archives` | `list[dict] \| null` | no | Zip archive sweep; each entry: {filename, size_bytes, modified, total_files, gerber_files, drill_files, other_files, newest_member_date, staleness_warning}. Omitted when no .zip files in the directory. |
| `connectivity` | `list[dict] \| null` | no | Flat pin-to-net list from X2 attributes (--full only). Each item: {ref, pin, pin_name, net}. |
| `capability_mode_ref` | `dict \| null` | no | Pointer to canonical analysis/capability_mode.json run-level record. Shape: {source, run_id}. See Phase 4 spec §3.3. |
| `audience_summary` | `dict \| null` | no | Designer/reviewer/manager summary views; only present when output filters ran. |

## ThermalEnvelope

Output of `python3 skills/kicad/scripts/analyze_thermal.py --schematic ... --pcb ...`.

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `analyzer_type` | `string` | yes | Always 'thermal'. |
| `schema_version` | `string` | yes | Schema semver. Value: '1.4.0' at Track 1.1 landing. |
| `inputs` | `InputsBlock` | yes | Source JSON inputs, sha256s, run_id, plus upstream artifact metadata (schematic, pcb). |
| `compat` | `CompatBlock` | yes | Schema compatibility metadata: minimum consumer version + deprecated/experimental field lists. |
| `summary` | `ThermalSummary` | yes | Roll-up summary of thermal analysis. |
| `findings` | `list[Finding]` | yes | All thermal findings: TS-001..005, TP-001..002. |
| `assessments` | `list[Assessment]` | yes | TH-DET entries — per-component junction-temperature estimates. Informational (not findings). |
| `trust_summary` | `TrustSummary` | yes | Trust posture rollup. |
| `elapsed_s` | `float` | yes | Wall-clock analysis time in seconds. |
| `missing_info` | `ThermalMissingInfo \| null` | no | Emitted when any component used default thermal params. |
| `capability_mode_ref` | `dict \| null` | no | Pointer to canonical analysis/capability_mode.json run-level record. Shape: {source, run_id}. See Phase 4 spec §3.3. |

## EMCEnvelope

Output of `python3 skills/emc/scripts/analyze_emc.py --schematic ... --pcb ...`.

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `analyzer_type` | `string` | yes | Always 'emc'. |
| `schema_version` | `string` | yes | Semver. Value: '1.4.0' at Track 1.1 landing. |
| `inputs` | `InputsBlock` | yes | Source JSON inputs, sha256s, run_id, plus upstream artifact metadata (schematic, pcb). |
| `compat` | `CompatBlock` | yes | Schema compatibility metadata: minimum consumer version + deprecated/experimental field lists. |
| `target_standard` | `string` | yes | Target EMC standard key (e.g. 'fcc-class-b', 'cispr-class-b', 'cispr-25'). |
| `summary` | `EMCSummary` | yes | EMC roll-up summary (counts + risk score). |
| `findings` | `list[Finding]` | yes | All EMC findings. |
| `assessments` | `list[Assessment]` | yes | Informational assessments (empty for EMC at v1.4). |
| `trust_summary` | `TrustSummary` | yes | Trust posture rollup (confidence + evidence source). |
| `elapsed_s` | `float` | yes | Analysis wall-clock time in seconds. |
| `per_net_scores` | `list[PerNetScore]` | yes | Per-net EMC risk score rollup, sorted worst-first. |
| `test_plan` | `TestPlan` | yes | Pre-compliance test plan: frequency band priority, interface risk ranking, probe point suggestions. |
| `regulatory_coverage` | `RegulatoryCoverage` | yes | Coverage matrix vs. applicable standards for the target market. |
| `category_summary` | `dict[str, CategorySummaryEntry]` | yes | Category label -> {count, max_severity, severities, suppressed_count}. |
| `board_info` | `BoardInfo` | yes | Board-level rollup (dimensions, layer count, crystal + switching frequencies, ...). |
| `capability_mode_ref` | `dict \| null` | no | Pointer to canonical analysis/capability_mode.json run-level record. Shape: {source, run_id}. See Phase 4 spec §3.3. |
| `audience_summary` | `dict \| null` | no | Designer/reviewer/manager summary views. Present whenever findings[] is non-empty (the analyzer always builds this when findings exist). |
| `stage_filter` | `dict \| null` | no | Stage-filtered findings rollup. Present only when --stage is passed. |

## CrossAnalysisEnvelope

Output of `python3 skills/kicad/scripts/cross_analysis.py --schematic ... --pcb ...`.

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `analyzer_type` | `string` | yes | Always 'cross_analysis'. |
| `schema_version` | `string` | yes | Semver. Value: '1.4.0' at Track 1.1 landing. |
| `inputs` | `InputsBlock` | yes | Source JSON inputs, sha256s, run_id, plus upstream artifact metadata (schematic, pcb). |
| `compat` | `CompatBlock` | yes | Schema compatibility metadata: minimum consumer version + deprecated/experimental field lists. |
| `elapsed_s` | `float` | yes | Analysis wall-clock time in seconds. |
| `summary` | `CrossAnalysisSummary` | yes | Roll-up summary (total + by_severity). |
| `findings` | `list[Finding]` | yes | All cross-domain findings. |
| `assessments` | `list[Assessment]` | yes | Informational assessments (empty for cross-analysis at v1.4). |
| `trust_summary` | `TrustSummary` | yes | Trust posture rollup (confidence + evidence source). |
| `capability_mode_ref` | `dict \| null` | no | Pointer to canonical analysis/capability_mode.json run-level record. Shape: {source, run_id}. See Phase 4 spec §3.3. |
| `audience_summary` | `dict \| null` | no | Designer/reviewer/manager summary views. Added by apply_output_filters whenever findings[] is non-empty. |
| `stage_filter` | `dict \| null` | no | Stage-filtered findings rollup. Present only when --stage is passed. |
