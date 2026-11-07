# Diff Analysis Reference

Compare two KiCad analysis JSON files (base vs head) and report changes. Supports schematic, PCB, EMC, and SPICE analyzer outputs with auto-detection. Zero dependencies — Python 3.10+ stdlib only.

## Table of Contents

1. [Overview](#overview)
2. [CLI Reference](#cli-reference)
3. [Analyzer Types](#analyzer-types)
4. [Severity Classification](#severity-classification)
5. [Identity Matching](#identity-matching)
6. [Output Schema](#output-schema)
7. [Integration with analysis_cache](#integration-with-analysis_cache)
8. [Common User Intents](#common-user-intents)

---

## Overview

The diff pipeline has five stages:

1. **Detect type** -- Read `analyzer_type` from both JSONs (falls back to heuristic key inspection for older files). Reject if types mismatch.
2. **Dispatch** -- Route to the type-specific diff function: `diff_schematic`, `diff_pcb`, `diff_emc`, or `diff_spice`.
3. **Match by identity** -- For list-based sections (components, detections, findings, footprints), build identity maps from each side and partition into added, removed, and matched pairs.
4. **Compare values** -- For matched pairs, compare registered value fields. Numeric deltas below the threshold percentage are suppressed.
5. **Classify severity** -- Walk the diff result and assign an overall severity: `none`, `minor`, `major`, or `breaking`.

The tool operates on pre-analyzed JSON produced by `analyze_schematic.py`, `analyze_pcb.py`, `analyze_emc.py`, or the SPICE pipeline. It never re-parses source files.

**When to use it:**
- Comparing design revisions (base branch vs PR, v1 vs v2).
- Reviewing what changed after a schematic edit.
- Tracking EMC regression/improvement across iterations.
- Verifying SPICE simulation stability after component changes.
- Automated CI gating via severity threshold.

---

## CLI Reference

```
python3 diff_analysis.py <base> <head> [options]
python3 diff_analysis.py --analysis-dir <analysis_dir> [options]
```

### Positional Arguments

| Argument | Description |
|----------|-------------|
| `base` | Path to base (old) analysis JSON (not needed with `--analysis-dir`) |
| `head` | Path to head (new) analysis JSON (not needed with `--analysis-dir`) |

### Options

| Flag | Description |
|------|-------------|
| `--output FILE`, `-o FILE` | Write output to file instead of stdout |
| `--text` | Human-readable text output instead of JSON |
| `--threshold FLOAT` | Ignore numeric deltas below this percentage (default: `1.0`) |
| `--analysis-dir DIR`, `-d DIR` | Resolve base and head from the folder's `manifest.json`; with no `--run`, diffs the previous run against the current one |
| `--run RUN_ID` | Run to compare: give it twice (base, then head), or once to diff that run against the current one. Accepts `current`, `previous`, or a run ID (`YYYY-MM-DD_HHMM`) |
| `--type TYPE` | Output to diff with `--analysis-dir` (`schematic`, `pcb`, `emc`, `spice`, `deep_review`). Default: the first output both runs have; `--trend` defaults to `schematic` |
| `--trend N` | Show metric trends across the last N runs instead of a diff (requires `--analysis-dir`) |
| `--only-deterministic` | Read `analysis/<run>/<analyzer>.json` even when an `analysis/merged/<run>/` overlay exists |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Invalid input, parse error, type mismatch, or unrecognized analyzer type |

---

## Analyzer Types

### Schematic

Diff function: `diff_schematic(base, head, threshold)`

Compared sections:

| Section | Identity Key | Compared Fields | Source Path |
|---------|-------------|-----------------|-------------|
| Statistics | n/a (scalar paths) | `total_components`, `total_nets`, `unique_parts`, `total_wires`, `total_no_connects` | `statistics.*` |
| Components | `reference` | `value`, `footprint`, `mpn` | `components[]` |
| Signal analysis | Per-type via SIGNAL_REGISTRY, else finding identity (below) | Per-type via SIGNAL_REGISTRY, plus `severity`; `summary` for types with no value fields | `findings[]` grouped by detector via `group_findings_by_detection_type()` |
| BOM | `(value, footprint)` tuple | `quantity` | `bom[]` |
| Connectivity | JSON-serialized item, unnamed-net numbers ignored | new/resolved (set diff) | `connectivity_issues.{single_pin_nets,floating_nets,multi_driver_nets}` |
| ERC warnings | `(type, net, message)` tuple; on an unnamed net, its pins instead of its number | new/resolved (set diff) | `design_analysis.erc_warnings[]` |

Signal analysis is reconstructed from `findings[]` via `group_findings_by_detection_type()`, then iterates all detector types present in either base or head. For each detection type, identity and value fields come from `SIGNAL_REGISTRY` (derived from `detection_schema.SCHEMAS`). Unknown detection types fall back to `["reference"]` identity with no value fields. A detection keeps that registry key (its `detection_id` first) only when no other finding of its type shares it in either run; every other finding is matched by its identity (`diff_engine.finding_key`): its `finding_id`, unless the id is positional — a `#N` collision suffix, or a locator naming an `__unnamed_N` net — in which case a content key of `rule_id`, sorted nets (unnamed-net numbers dropped), sorted components and `summary`. Findings that still share a key are numbered after sorting by content, so list order never pairs two different findings, and a renumbered unnamed net never reads as a change. Severities compare by meaning (legacy `WARN` = `warning`). The diff output still uses `signal_analysis` as a key for backward compatibility with diff consumers.

### PCB

Diff function: `diff_pcb(base, head, threshold)`

| Section | Identity Key | Compared Fields | Source Path |
|---------|-------------|-----------------|-------------|
| Statistics | n/a (scalar paths) | `footprint_count`, `track_segments`, `via_count`, `zone_count`, `net_count`, `copper_layers_used`, `board_width_mm`, `board_height_mm`, `total_track_length_mm` | `statistics.*` |
| Routing completeness | n/a (scalar) | `routing_complete`, `unrouted_count` | `connectivity.*` |
| Footprints | `reference` | `value`, `footprint` (the `Lib:Name` FPID; `library` or `lib_id` in older JSON), `layer` | `footprints[]` |
| Findings | finding identity (as schematic) | `severity` (new/resolved/changed) | `findings[]` |

### EMC

Diff function: `diff_emc(base, head, threshold)`

| Section | Identity Key | Compared Fields | Source Path |
|---------|-------------|-----------------|-------------|
| Risk score | n/a (scalar) | `emc_risk_score` (0 = worst, 100 = lowest risk; a fall is a regression) | `summary.emc_risk_score` |
| Severity distribution | n/a (scalar paths) | `error`, `warning`, `info` (`critical`, `high`, `medium`, `low`, `info` in pre-v1.4 output) | `summary.by_severity.*` (`summary.*`) |
| Findings | finding identity (as schematic); `rule_id::sorted(nets)::sorted(components)` for findings without a `finding_id` | `severity` (new/resolved/changed) | `findings[]` |
| Per-net scores | `net` | `score` (filtered by threshold) | `per_net_scores[]` |

Per-net score changes are sorted by absolute delta (largest first).

### SPICE

Diff function: `diff_spice(base, head, threshold)`

| Section | Identity Key | Compared Fields | Source Path |
|---------|-------------|-----------------|-------------|
| Summary counts | n/a (scalar paths) | `pass`, `warn`, `fail`, `skip`, `info`, `total` | `summary.*` |
| Simulation results | `subcircuit_type::sorted(components)` | `status` (transitions annotated) | `simulation_results[]` |
| Monte Carlo concerns | `subcircuit_type::metric` | new/resolved (set diff) | `monte_carlo_summary.concerns[]` |

Status transitions from `pass` to `fail` or `warn` are annotated as regressions with up to 3 delta fields from the result.

---

## Severity Classification

Function: `classify_severity(analyzer_type, diff_result)`

Evaluation order (first match wins):

### Breaking

| Analyzer | Condition |
|----------|-----------|
| SPICE | Any `status_changes` entry where `base_status == "pass"` and `head_status == "fail"` |
| EMC | Any new finding whose normalized severity is `error` (legacy `CRITICAL` or `HIGH`) |
| Schematic | Any new ERC warning (`erc.new_warnings` non-empty) |

### Major

| Condition |
|-----------|
| `signal_analysis` key present in diff |
| `components` key present in diff |
| `findings` key present in diff (EMC) |
| `status_changes` key present in diff (SPICE) |
| `footprints` with any added, removed, or modified entries (PCB) |
| `routing_complete` or `unrouted` present (PCB) |

### Minor

| Condition |
|-----------|
| Any other non-empty section: `statistics`, EMC `risk_score`, `by_severity` or `per_net_scores`, `bom`, `connectivity`, resolved-only `erc`, SPICE `summary`, `new_results`, `removed_results` or `monte_carlo`, assessments added or removed |

### None

No section changed (an `assessments` block holding only `unchanged_count` is not a change).

### Regressions

`classify_regressions(analyzer_type, diff_result)` lists changes that made the design worse: new ERC warnings, new connectivity issues and removed protection devices (schematic), new error-severity findings and a fall in the EMC risk score (EMC; the score is 0 = worst, 100 = lowest risk), pass-to-fail transitions (SPICE), and an increase in unrouted nets (PCB).

---

## Identity Matching

### SIGNAL_REGISTRY

`SIGNAL_REGISTRY` is derived at import time from `detection_schema.SCHEMAS`:

```python
SIGNAL_REGISTRY = {dt: (s.identity_fields, s.value_fields) for dt, s in _SCHEMAS.items()}
```

Each detection type maps to `(identity_fields, value_fields)` where both are lists of dotpath strings.

**Registered detection types and their identity/value fields:**

| Detection Type | Identity Fields | Value Fields |
|---------------|-----------------|--------------|
| `rc_filters` | `resistor.ref`, `capacitor.ref` | `cutoff_hz` |
| `lc_filters` | `inductor.ref`, `capacitor.ref` | `resonant_hz` |
| `voltage_dividers` | `r_top.ref`, `r_bottom.ref` | `ratio`, `vout_estimated` |
| `feedback_networks` | `r_top.ref`, `r_bottom.ref` | `ratio` |
| `opamp_circuits` | `reference` | `gain`, `gain_dB`, `configuration` |
| `crystal_circuits` | `reference` | `frequency`, `effective_load_pF` |
| `current_sense` | `shunt.ref` | `max_current_50mV_A`, `max_current_100mV_A` |
| `power_regulators` | `ref` | `vout_estimated`, `topology` |
| `transistor_circuits` | `reference` | `type` |
| `protection_devices` | `reference`, `type` | `protected_net` |
| `bridge_circuits` | `topology` | (none) |
| `rf_matching` | `antenna_ref` | (none) |
| `bms_systems` | `bms_reference` | `cell_count` |
| `decoupling_analysis` | `rail_net` | (none) |
| `rf_chains` | (none) | (none) |
| `ethernet_interfaces` | `phy_ref` | (none) |
| `memory_interfaces` | `type` | (none) |
| `isolation_barriers` | `isolator_ref` | (none) |
| `snubber_circuits` | (none) | (none) |

### Dotpath Resolution

Identity and value fields use dotted paths (e.g., `r_top.ref`) resolved by `_resolve()`. Each segment indexes into nested dicts. Returns `None` if any segment is missing.

### Identity Key Building

`_identity_key(item, fields)` extracts the value at each dotpath and joins them with `::`. List values are sorted and joined with `|`. If any field resolves to `None`, the entire key is `None` and the item is excluded from matching.

Example: for a voltage divider with `r_top.ref = "R1"` and `r_bottom.ref = "R2"`, the identity key is `R1::R2`.

### Generic Fallback

When a detection type is not in `SIGNAL_REGISTRY`, `_generic_identity()` is used. It tries:

1. Top-level `reference` or `ref` field.
2. Any nested dict with a `ref` sub-key.

Returns `None` if nothing is found. The diff then matches the item by its `finding_id`, or, without one, by a content key (rule id, nets, components and summary); only the multi-run trend extraction skips it.

### Validation

`validate_signal_registry(sample_output)` checks that every key in `SIGNAL_REGISTRY` has at least one finding with a matching detector in `findings[]`. Returns warning strings for any missing keys. Useful for catching stale registry entries after schema changes.

---

## Output Schema

### Top-Level Structure

```json
{
  "diff_version": "1.0",
  "analyzer_type": "schematic|pcb|emc|spice",
  "base_file": "/path/to/base.json",
  "head_file": "/path/to/head.json",
  "has_changes": true,
  "summary": {
    "total_changes": 5,
    "added": 2,
    "removed": 1,
    "modified": 2,
    "metric_changes": ["statistics.total_components"],
    "severity": "major"
  },
  "diff": { ... }
}

```

### Summary Counts

`summary.total_changes` = `added + removed + modified`, each counting listed items:

| Analyzer | Added | Removed | Modified |
|----------|-------|---------|----------|
| Schematic | New components, detections, BOM lines, connectivity issues, ERC warnings | Removed components, detections, BOM lines; resolved connectivity issues and ERC warnings | Changed components and detections; BOM quantity changes |
| PCB | New footprints + new findings | Removed footprints + resolved findings | Changed footprints + severity-changed findings |
| EMC, thermal | New findings | Resolved findings | Severity-changed findings; changed per-net scores (EMC) |
| SPICE | New simulation results + new Monte Carlo concerns | Removed simulation results + resolved Monte Carlo concerns | Status-changed results |

Assessments added or removed count on every analyzer type.

`summary.metric_changes` lists, sorted, the analyzer-output paths of the scalars that moved: `statistics.*`, `connectivity.routing_complete`, `connectivity.unrouted_count`, `summary.emc_risk_score`, `summary.by_severity.*` and the SPICE `summary.*` counts. They are not in `total_changes`, so one added part is not counted again through every rollup it moves.

`has_changes` is true when any diff section changed, including a metric-only change (`total_changes` 0).

### Diff Section (by analyzer type)

The `diff` object contains only sections with actual changes. Empty sections are omitted.

**Schematic diff keys:** `statistics`, `components`, `signal_analysis`, `bom`, `connectivity`, `erc`

**PCB diff keys:** `statistics`, `routing_complete`, `unrouted`, `footprints`, `findings`

**EMC diff keys:** `risk_score`, `by_severity`, `findings`, `per_net_scores`

**SPICE diff keys:** `summary`, `status_changes`, `new_results`, `removed_results`, `monte_carlo`

### List Diff Format

All list-based sections (components, signal analysis detections, footprints) use the same structure:

```json
{
  "added": [{ "reference": "R5", "value": "10k", ... }],
  "removed": [{ "reference": "R3", "value": "4.7k", ... }],
  "modified": [{
    "identity": "R1/R2",
    "changes": [{
      "field": "ratio",
      "base": 0.5,
      "head": 0.33,
      "delta_pct": -34.0
    }]
  }],
  "unchanged_count": 12
}
```

The `delta_pct` field is only present for numeric comparisons where the base value is nonzero.

### Text Output

The `--text` flag renders a summary header followed by per-section detail. Items are capped at `MAX_TEXT_ITEMS` (20) with a "... and N more changes" footer counting the listed items not printed. Per-section caps: 5 items for components/footprints/findings, 3 items for signal analysis detections per type. Routing, unrouted and statistics changes print as `base → head` lines; the findings block is labelled by source (`EMC Findings:`, `PCB Findings:`, `Thermal Findings:`). `--output` files are written as UTF-8.

Format:

```
Design Changes: schematic (major) — 5 changes
  +2 added, -1 removed, ~2 modified

Components:
  + R5 10k 0402
  - R3 4.7k 0603
  ~ R1: value 10k → 4.7k

Signal Analysis:
  + New Voltage Dividers: r_top_ref=R5 r_bottom_ref=R6
  ~ Rc Filters R1/C3: cutoff_hz 1591.55 → 3386.28
```

---

## Integration with analysis_cache

`analysis_cache.should_create_new_run()` uses diff_analysis programmatically to decide whether new analyzer outputs warrant a new timestamped run folder.

**Protocol:**

1. Import `diff_engine` (adding the scripts directory to `sys.path` if needed).
2. For each output type present in both the current run and the new outputs, load both JSONs.
3. Read `analyzer_type` from the base JSON and dispatch to the matching diff function (`diff_schematic`, `diff_pcb`, `diff_emc`, `diff_spice`).
4. Call `classify_severity()` on the diff result.
5. If any severity meets or exceeds the configured threshold (default: `major`), return `True` (create new run). At the default a finding- or routing-only change starts a new run; a statistics- or score-only change (`minor`) overwrites the current one.
6. If no current run exists, return `True` (first run).
7. If all diffs are below threshold, return `False` (overwrite current run).

The threshold comparison uses a severity ordering: `none=0`, `minor=1`, `major=2`, `breaking=3`.

---

## Common User Intents

Natural-language queries and their corresponding command invocations.

| User Says | Command |
|-----------|---------|
| "What changed between these two analyses" | `diff_analysis.py old.json new.json --text` |
| "Show me changes as JSON" | `diff_analysis.py old.json new.json` |
| "Ignore small changes" | `diff_analysis.py old.json new.json --threshold 5.0 --text` |
| "Compare my schematic revisions" | `diff_analysis.py base.json head.json --text` |
| "Did the EMC risk get worse" | `diff_analysis.py emc_old.json emc_new.json --text` |
| "Any SPICE regressions" | `diff_analysis.py spice_old.json spice_new.json --text` |
| "Save the diff report" | `diff_analysis.py base.json head.json --output diff.json` |
| "Diff my last two runs" | `diff_analysis.py --analysis-dir analysis/ --text` |
| "Show trends over time" | `diff_analysis.py --analysis-dir analysis/ --trend 5 --text` |
