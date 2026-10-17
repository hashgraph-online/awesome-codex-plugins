# Datasheet Verification Reference

Automated cross-check of schematic connections against structured datasheet extractions. Catches pin voltage violations, missing required external components, and insufficient decoupling -- issues that manual review often misses because they require reading the datasheet for every IC.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Verification Checks](#verification-checks)
4. [Output Schema](#output-schema)
5. [Extraction Fields Used](#extraction-fields-used)
6. [Limitations](#limitations)
7. [Common User Intents](#common-user-intents)

---

## Overview

The verification bridge (`datasheet_verify.py`) compares what the schematic analyzer found (net voltages, connected components, decoupling caps) against what the datasheet says should be there (pin voltage limits, required external components, application circuit recommendations).

It runs as part of the schematic analysis pipeline. When the `datasheets/extracted/` cache directory exists and contains extraction JSON files for the design's ICs, the verifier activates automatically. When no extractions are available, it returns an empty result with a note.

**What it catches:**

- Net voltage exceeding a pin's absolute maximum rating (potential damage)
- Net voltage exceeding a pin's recommended operating range (potential malfunction)
- Missing capacitors, resistors, inductors, or diodes that the datasheet requires on specific pins
- Decoupling capacitor count or value falling short of application circuit recommendations

---

## Prerequisites

The verification pipeline has four stages. All must complete before verification can run:

### Stage 1: Download datasheets

Use `sync_datasheets_digikey.py` (or `fetch_datasheet_digikey.py` for individual parts) to download PDF datasheets for all ICs in the design. The script uses `analyze_schematic.py` to extract MPNs automatically.

```bash
python3 <skill-path>/scripts/sync_datasheets_digikey.py <project_dir>
```

PDFs are saved to `datasheets/` in the project directory.

### Stage 2: LLM extraction

The LLM reads the downloaded PDF pages and produces structured JSON for each IC. The page selector (`datasheet_page_selector.py`) identifies which pages contain pin tables, absolute maximum ratings, and application circuits. The agent then fills in the extraction schema documented in the **`datasheets` skill** — see `skills/datasheets/references/extraction-schema.md` for the canonical schema and `skills/datasheets/references/field-extraction-guide.md` for how to find each field in vendor datasheets.

This step is interactive — it requires the agent to read PDF pages and produce JSON. It cannot be fully automated.

### Stage 3: Cache extractions

Extraction JSON files are stored in `datasheets/extracted/` with filenames derived from the MPN (non-alphanumeric characters replaced with underscores). An optional `manifest.json` (legacy name `index.json`) provides case-insensitive MPN-to-file mapping.

```
datasheets/extracted/
  TPS61023DRLR.json
  STM32F405RGT6.json
  USBLC6_2SC6.json
  manifest.json       # optional (legacy name: index.json)
```

### Stage 4: Verification

The verifier runs automatically when `run_datasheet_verification()` is called with the schematic analysis JSON. It resolves the extraction directory by checking:

1. `<project_dir>/datasheets/extracted/`
2. `<project_dir>/../datasheets/extracted/`

If neither exists, verification is skipped.

---

## Verification Checks

### Pin voltage absolute maximum exceeded

**Type:** `pin_voltage_abs_max_exceeded`
**Severity:** CRITICAL
**Condition:** Net voltage > pin's `voltage_abs_max`

Compares the estimated voltage on each pin's connected net against the absolute maximum rating from the datasheet extraction. Net voltages are resolved from:

1. The top-level `rail_voltages` dict (e.g., `+3V3` -> 3.3V)
2. Name parsing heuristics: `+3V3` -> 3.3, `+5V` -> 5.0, `12V0` -> 12.0

GND pins are skipped. Pins without a `voltage_abs_max` in the extraction are skipped.

**Example finding:**

```
U3 pin 4 (VIN) on +12V (12.0V) exceeds absolute maximum (6.0V) by 6.00V
```

This is always CRITICAL -- exceeding absolute maximum ratings causes permanent device damage.

### Pin voltage operating range exceeded

**Type:** `pin_voltage_operating_exceeded`
**Severity:** HIGH or MEDIUM
**Condition:** Net voltage > pin's `voltage_operating_max` (but below `voltage_abs_max`)

Same net voltage resolution as above, but checks against the recommended operating maximum instead of the absolute maximum.

Severity depends on the margin to absolute maximum:
- **HIGH** when less than 10% margin to `voltage_abs_max`
- **MEDIUM** when 10% or more margin to `voltage_abs_max`

If no `voltage_abs_max` is available, the margin is treated as 0% (HIGH severity).

**Example finding:**

```
U1 pin 2 (VDD) on +5V (5.0V) exceeds recommended operating maximum (4.5V)
```

### Missing required external components

**Type:** `missing_required_external`
**Severity:** HIGH
**Condition:** Pin has `required_external` in extraction, but no matching component type found on the net

For each IC pin that has a `required_external` field in the extraction (e.g., "100nF bypass cap to GND", "10K pull-up to VCC"), the verifier checks whether any component of the expected type is connected to that pin's net.

The expected component type is parsed from the `required_external` text:

| Keywords in `required_external` | Expected type(s) |
|--------------------------------|-------------------|
| cap, capacitor, decoupling, bypass | `capacitor` |
| resistor, pull-up, pullup, pull-down, divider | `resistor` |
| inductor, ferrite, bead | `inductor`, `ferrite_bead` |
| diode, schottky | `diode` |

The check examines all other components connected to the same net (excluding the IC itself). If none of the connected component types match any of the expected types, a finding is generated.

If the `required_external` text cannot be parsed into any known component type, the pin is skipped.

**Example finding:**

```
U2 pin 8 (BYPASS): datasheet requires "100nF bypass cap to GND" but none found on net BYPASS_U2
```

### Decoupling insufficient

**Type:** `decoupling_insufficient`
**Severity:** HIGH or MEDIUM
**Condition:** Fewer matching capacitors on power pins than the application circuit recommends

Checks the `application_circuit` section of the extraction for these fields:

- `input_cap_recommended` (e.g., "10uF ceramic, X5R or X7R")
- `output_cap_recommended` (e.g., "22uF ceramic x2")
- `decoupling_cap` (e.g., "100nF per VDD pin")

For each recommendation, the verifier:

1. Parses the recommendation text to extract minimum capacitance, required count, dielectric preferences, and placement distance
2. Identifies all power pins on the IC (pins with type `power` and direction `input`, `output`, or `bidirectional`)
3. Finds all capacitors connected to those power pin nets
4. Counts capacitors whose parsed value meets at least 80% of the recommended minimum

Severity depends on how many matching caps were found:
- **HIGH** when zero matching caps found
- **MEDIUM** when some caps found but fewer than required count

**Recommendation parsing examples:**

| Text | Parsed as |
|------|-----------|
| `"10uF ceramic, X5R or X7R"` | min 10uF, count 1, dielectric [X5R, X7R] |
| `"22uF ceramic x2"` | min 22uF, count 2 |
| `"100nF"` | min 100nF, count 1 |
| `"4.7uF within 5mm"` | min 4.7uF, count 1, max distance 5mm |

The count multiplier is parsed from `xN` or `x N` suffixes. Dielectrics are recognized: X5R, X7R, X7S, C0G, NP0, X6S. Distance constraints are parsed from "within Nmm" or "< Nmm" patterns.

**Example finding:**

```
U4 (LM2596): datasheet recommends "22uF ceramic x2" but found 1/2 matching caps on power pins
```

---

## Output Schema

The `run_datasheet_verification()` function returns a dict with two keys:

### findings

Array of finding objects. Each finding has:

| Field | Type | Present in | Description |
|-------|------|------------|-------------|
| `type` | string | all | Finding type identifier (see check descriptions above) |
| `severity` | string | all | `CRITICAL`, `HIGH`, or `MEDIUM` |
| `ref` | string | all | Component reference (e.g., `U3`) |
| `mpn` | string | all | Manufacturer part number |
| `pin_number` | string | all | Pin number from schematic |
| `pin_name` | string | all | Pin name from extraction |
| `net` | string | all | Net name the pin connects to |
| `detail` | string | all | Human-readable description |
| `net_voltage_V` | float | voltage checks | Estimated net voltage |
| `abs_max_V` | float | voltage checks | Absolute maximum rating from datasheet |
| `margin_V` | float | abs_max | Margin (negative = violation) |
| `operating_max_V` | float | operating check | Operating maximum from datasheet |
| `required` | string | missing_external | The `required_external` text from extraction |
| `expected_types` | array | missing_external | Component types expected based on text parsing |
| `connected_types` | array | missing_external | Component types actually found on the net |
| `requirement_key` | string | decoupling | Which field the recommendation came from |
| `requirement_text` | string | decoupling | Raw recommendation text |
| `required_count` | int | decoupling | How many caps the datasheet recommends |
| `required_min_farads` | float | decoupling | Minimum capacitance per cap |
| `actual_count` | int | decoupling | How many matching caps were found |
| `actual_caps` | array | decoupling | List of `{ref, value}` for caps on power nets |

### summary

| Field | Type | Description |
|-------|------|-------------|
| `ics_checked` | int | Total ICs in the design |
| `ics_with_extractions` | int | ICs that had extraction data available |
| `total_findings` | int | Total number of findings |
| `by_severity` | object | Count per severity level (e.g., `{"CRITICAL": 1, "HIGH": 3}`) |
| `note` | string | Present only when no extraction directory was found |

**Example output:**

```json
{
  "findings": [
    {
      "type": "pin_voltage_abs_max_exceeded",
      "severity": "CRITICAL",
      "ref": "U3",
      "mpn": "TPS61023DRLR",
      "pin_number": "4",
      "pin_name": "VIN",
      "net": "+12V",
      "net_voltage_V": 12.0,
      "abs_max_V": 6.0,
      "margin_V": -6.0,
      "detail": "U3 pin 4 (VIN) on +12V (12.0V) exceeds absolute maximum (6.0V) by 6.00V"
    }
  ],
  "summary": {
    "ics_checked": 8,
    "ics_with_extractions": 5,
    "total_findings": 1,
    "by_severity": {"CRITICAL": 1}
  }
}
```

---

## Extraction Fields Used

Mapping of which extraction JSON fields drive which verification checks.

| Extraction Field | Location | Used By |
|-----------------|----------|---------|
| `pins[].voltage_abs_max` | Pin entry | Pin voltage abs max check |
| `pins[].voltage_operating_max` | Pin entry | Pin voltage operating range check |
| `pins[].required_external` | Pin entry | Missing required external check |
| `pins[].type` | Pin entry | All checks (filters GND pins, identifies power pins) |
| `pins[].direction` | Pin entry | Decoupling check (identifies power input/output pins) |
| `pins[].name` | Pin entry | All checks (used in finding detail text) |
| `pins[].number` | Pin entry | All checks (joins extraction pins to schematic pins) |
| `application_circuit.input_cap_recommended` | Top-level | Decoupling check |
| `application_circuit.output_cap_recommended` | Top-level | Decoupling check |
| `application_circuit.decoupling_cap` | Top-level | Decoupling check |

### Schematic analysis fields consumed

| Analysis Field | Used By |
|---------------|---------|
| `components[].type` | All checks (filters to ICs only) |
| `components[].reference` | All checks (component identification) |
| `components[].mpn` | All checks (extraction file lookup) |
| `components[].value` | All checks (fallback when mpn is absent) |
| `components[].pin_nets` | All checks (pin-to-net mapping) |
| `components[].parsed_value` | Decoupling check (capacitor value comparison) |
| `nets[].pins` | Missing external + decoupling (finds connected components) |
| `rail_voltages` | Voltage checks (net voltage estimation) |

---

## Limitations

**Extraction quality is LLM-dependent.** The extraction step relies on Claude reading PDF pages and filling in structured JSON. Complex datasheets, poor PDF formatting, or unusual pin table layouts can lead to incomplete or incorrect extractions. The quality scorer (`datasheet_score.py`) catches some gaps, but subtle errors (e.g., wrong voltage assigned to a pin) are not detectable.

**Net voltage estimation is heuristic.** Voltages are resolved from `rail_voltages` (which the schematic analyzer populates for detected power rails) and from net name parsing. Nets with non-standard names or dynamically regulated voltages may not have a voltage estimate, causing those pins to be skipped.

**Only ICs are checked.** The verifier filters to components with `type == "ic"`. Discrete transistors, MOSFETs used as switches, and other non-IC components with datasheets are not verified.

**required_external parsing is keyword-based.** The verifier recognizes common component type keywords (capacitor, resistor, inductor, diode) in the `required_external` text. Unusual phrasings or component types not in the keyword list will be silently skipped.

**Capacitance matching uses 80% tolerance.** A capacitor is considered "matching" if its parsed value is at least 80% of the recommended minimum. This is deliberately loose to account for value parsing ambiguity and the common practice of using slightly smaller values in constrained layouts.

**Decoupling checks only count caps on power pin nets.** Capacitors on signal pins or dedicated bypass nets that are not directly connected to a pin marked as `power` in the extraction will not be counted.

**No negative voltage checks.** The verifier only checks whether net voltage exceeds the maximum ratings. It does not check for negative voltage violations on pins with negative absolute maximum limits (e.g., ESD clamp pins rated to -0.3V).

**Single-sheet scope.** The verifier operates on the flattened component and net lists from the schematic analysis. It does not have visibility into hierarchical sheet boundaries or conditional assembly variants.

---

## Common User Intents

| User Says | What Happens |
|-----------|-------------|
| "Verify against datasheet" | Run full verification: all checks against all ICs with available extractions |
| "Check pin voltages" | Focus on `pin_voltage_abs_max_exceeded` and `pin_voltage_operating_exceeded` findings |
| "Are my decoupling caps right" | Focus on `decoupling_insufficient` findings; compare actual vs recommended for each IC |
| "What does the datasheet say about pin X on U3" | Load extraction for U3's MPN; look up the specific pin entry and report all fields |
| "Is U3 wired correctly" | Load extraction for U3; cross-reference every pin's `required_external` against the schematic |
| "Check if any pins are overvoltaged" | Same as "check pin voltages" -- look for voltage findings |
| "What external components does U5 need" | Load extraction for U5; list all pins with `required_external` populated and compare to what is connected |
| "Are there any datasheet violations" | Run full verification and report all findings grouped by severity |
