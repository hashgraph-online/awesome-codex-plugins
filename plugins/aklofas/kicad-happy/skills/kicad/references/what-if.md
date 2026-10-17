# What-If Parameter Sweep Reference

Interactive parameter sweep for KiCad designs. Patches component values in analyzer JSON, recalculates affected subcircuit fields, and shows before/after impact. Supports single changes, multi-point sweeps, tolerance corner analysis, inverse fix suggestions, EMC impact preview, and PCB parasitic awareness.

## Table of Contents

1. [Overview](#overview)
2. [CLI Reference](#cli-reference)
3. [Value Formats](#value-formats)
4. [Fix Suggestions](#fix-suggestions)
5. [E-Series Snapping](#e-series-snapping)
6. [EMC Impact Preview](#emc-impact-preview)
7. [PCB Parasitic Awareness](#pcb-parasitic-awareness)
8. [Recalculable Fields](#recalculable-fields)
9. [JSON Output Schema](#json-output-schema)
10. [Common User Intents](#common-user-intents)
11. [Combinability](#combinability)

---

## Overview

The what-if pipeline operates in three stages:

1. **Patch** -- Locate all subcircuit detections in `findings[]` (grouped by detector) that reference the changed component(s) and replace their stored values.
2. **Recalculate** -- Re-derive dependent fields (cutoff frequency, divider ratio, opamp gain, etc.) using the formulas in `_recalc_derived()`.
3. **Compare** -- Diff the original and patched detections, report before/after values with percentage deltas.

The tool operates on analyzer JSON produced by `analyze_schematic.py`. It never re-parses the schematic file -- it works entirely on the pre-analyzed data.

**When to use it:**
- Exploring component value trade-offs before committing to a design change.
- Answering "what if I change R5 to 4.7k" style questions instantly.
- Finding the right component value to hit a target spec (--fix mode).
- Evaluating tolerance spread impact on derived parameters.
- Previewing EMC consequences of a component change before re-running the full EMC suite.

---

## CLI Reference

```
python3 what_if.py <input> [changes...] [options]
```

### Positional Arguments

| Argument | Description |
|----------|-------------|
| `input` | Analyzer JSON file (from `analyze_schematic.py`) |
| `changes` | Zero or more `REF=VALUE` pairs (e.g., `R5=4.7k C3=22n`) |

### Options

| Flag | Description |
|------|-------------|
| `--spice` | Re-run SPICE simulations on affected subcircuits (requires ngspice/LTspice/Xyce) |
| `--output FILE`, `-o FILE` | Write patched analysis JSON to file (for downstream EMC, thermal, or diff analysis) |
| `--text` | Human-readable text output instead of JSON |
| `--emc` | Show EMC impact preview (runs `analyze_emc.py` on original and patched JSON) |
| `--pcb FILE` | PCB analysis JSON for parasitic awareness (auto-discovered if omitted) |
| `--fix TYPE[INDEX]` | Inverse-solve for component values to hit a target (e.g., `--fix voltage_dividers[0]`) |
| `--target VALUE` | Target value for `--fix` mode (e.g., `3.3` for ratio, `1000` for Hz) |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Invalid input, parse error, or missing data |

---

## Value Formats

### Single Value

```
R5=4.7k
C3=22n
L1=10u
```

Standard engineering notation. The parser uses `parse_value()` from `kicad_utils.py` with automatic component type detection based on the reference prefix (`C` -> capacitor, `L` -> inductor, everything else -> resistor by default).

### Comma Sweep

```
R5=1k,2.2k,4.7k,10k
```

Evaluates the circuit at each listed value. Results are formatted as a markdown table in `--text` mode. Only one component may use sweep syntax per invocation.

### Log-Range Sweep

```
R5=1k..100k:10
```

Generates `N` logarithmically spaced values between start and stop (inclusive). The step count is capped at 50.

**Syntax:** `START..STOP:N`

The log distribution is computed as: `v[i] = start * (stop/start)^(i/(N-1))`

### Tolerance Suffix

```
R5=4.7k+-5%
R5=4.7k±5%
```

Both `+-` and the Unicode `±` character are accepted. The tolerance triggers worst-case corner analysis: all 2^N combinations of each toleranced component at its +tol and -tol extremes. Capped at 6 components (64 corners).

Default tolerances when the suffix is omitted but tolerance mode is active:

| Prefix | Default Tolerance |
|--------|-------------------|
| `C`, `VC` | 10% |
| `L` | 20% |
| All others | 5% |

### Combined Formats

Sweep and tolerance can be combined on a single component:

```
R5=1k,2.2k,4.7k+-5%
```

This sweeps through the listed values and also computes tolerance corners at each step.

Multiple non-sweep changes can be specified alongside a single sweep:

```
R5=1k,2.2k,4.7k C3=22n
```

Here `C3` is held fixed at 22nF while `R5` sweeps.

---

## Fix Suggestions

The `--fix` mode runs an inverse solver to find component values that achieve a target specification.

### Syntax

```
python3 what_if.py analysis.json --fix TYPE[INDEX] --target VALUE
```

Where `TYPE[INDEX]` references a detection type and index (e.g., `voltage_dividers[0]`, `rc_filters[2]`). Internally, findings are grouped by detector name.

### Target Inference

When `--target` is omitted, the solver attempts to infer the target from the detection context:

| Detection Type | Inferred Target |
|---------------|-----------------|
| `voltage_dividers`, `feedback_networks` | `ratio = regulator_vref / target_vout` (from detection metadata) |
| `crystal_circuits` | `effective_load_pF = target_load_pF` (from detection metadata) |
| All others | Error -- `--target` is required |

### Inverse Solver Formulas

For each detection type, the solver holds one component fixed and computes the ideal value for the other. Both directions are reported as separate suggestions.

**voltage_dividers / feedback_networks** (target: `ratio`)

| Solve For | Formula | Equation ID |
|-----------|---------|-------------|
| R_bottom (fix R_top) | `R_bot = R_top * ratio / (1 - ratio)` | EQ-WI-001 |
| R_top (fix R_bottom) | `R_top = R_bot * (1 - ratio) / ratio` | EQ-WI-002 |

**rc_filters** (target: `cutoff_hz`)

| Solve For | Formula | Equation ID |
|-----------|---------|-------------|
| C (fix R) | `C = 1 / (2*pi*R*f_c)` | EQ-WI-003 |
| R (fix C) | `R = 1 / (2*pi*C*f_c)` | EQ-WI-004 |

**lc_filters** (target: `resonant_hz`)

| Solve For | Formula | Equation ID |
|-----------|---------|-------------|
| C (fix L) | `C = 1 / ((2*pi*f_0)^2 * L)` | EQ-WI-005 |
| L (fix C) | `L = 1 / ((2*pi*f_0)^2 * C)` | EQ-WI-006 |

**opamp_circuits** (target: `gain` or `gain_dB`)

When `gain_dB` is the target field, it is converted to linear gain first: `gain = 10^(gain_dB/20)`.

| Configuration | Formula | Equation ID |
|--------------|---------|-------------|
| Non-inverting | `R_f = R_i * (|gain| - 1)` | EQ-WI-007 |
| Inverting / default | `R_f = R_i * |gain|` | EQ-WI-008 |

**crystal_circuits** (target: `effective_load_pF`)

| Solve For | Formula | Equation ID |
|-----------|---------|-------------|
| Each load cap (symmetric) | `C_load = 2 * (target_pF - C_stray)` | EQ-WI-009 |

Default stray capacitance: 3.0 pF.

**current_sense** (target: `max_current_100mV_A` or `max_current_50mV_A`)

| Target | Formula | Equation ID |
|--------|---------|-------------|
| `max_current_100mV_A` | `R_shunt = 0.100 / I_target` | EQ-WI-010 |
| `max_current_50mV_A` | `R_shunt = 0.050 / I_target` | EQ-WI-011 |

### Output

Each suggestion includes the ideal (exact) value plus E-series snapped alternatives at E12, E24, and E96 with error percentage. If PCB analysis is available, footprint compatibility warnings are generated for capacitor values that may exceed the package size limit.

---

## E-Series Snapping

All fix suggestions are snapped to standard E-series values using `snap_to_e_series()` from `kicad_utils.py`.

**Algorithm:**
1. Extract the decade: `decade = 10^floor(log10(value))`
2. Normalize: `normalized = value / decade`
3. Find the closest value in the series decade list.
4. Reconstruct: `snapped = best * decade`
5. Compute error: `error_pct = (snapped - value) / value * 100`

**Available series:**

| Series | Values per Decade | Typical Tolerance |
|--------|-------------------|-------------------|
| E12 | 12 | 10% |
| E24 | 24 | 5% |
| E96 | 96 | 1% |

All three series are reported for every fix suggestion, allowing the user to choose based on availability and precision requirements.

---

## EMC Impact Preview

The `--emc` flag runs the full EMC analyzer (`analyze_emc.py`) on both the original and patched analysis JSON, then diffs the results.

### Protocol

1. The patched analysis JSON is written to a temporary file.
2. `analyze_emc.py` is invoked as a subprocess with `--schematic` pointing to each temporary file.
3. If `--pcb` is specified, it is passed through as well.
4. A 30-second timeout is enforced per invocation.
5. Temporary files are cleaned up regardless of outcome.

### Output Fields

| Field | Type | Description |
|-------|------|-------------|
| `before_risk` | string | Overall risk level before change |
| `after_risk` | string | Overall risk level after change |
| `resolved` | array | Findings that disappeared after the change |
| `improved` | array | Findings whose risk level decreased |
| `new_findings` | array | Findings that appeared after the change |
| `unchanged` | integer | Count of findings with no change |

Text mode renders this as a summary with per-finding detail.

---

## PCB Parasitic Awareness

When PCB analysis data is available, the tool annotates each affected subcircuit with trace resistance and inductance estimates.

### Providing PCB Data

1. **Explicit:** `--pcb pcb_analysis.json`
2. **Auto-discovery:** If the schematic JSON is at `analysis/schematic/foo.json`, the tool looks for `analysis/pcb/*.json` automatically.

### Trace Parasitic Formulas

Trace resistance (EQ-WI-012):

```
R_trace = rho * length / (width * thickness)
```

Where `rho` = 1.72e-8 ohm-m (copper), `thickness` = 35e-6 m (1 oz copper).

Trace inductance (EQ-WI-013, valid when length > width):

```
L_trace = 2e-7 * length * ln(2 * length / width)
```

Both are computed per net segment and summed for all track segments connected to the component.

### Footprint Compatibility

For capacitor fix suggestions, the tool checks the suggested value against typical maximum capacitance for common package sizes:

| Package | Typical Max (ceramic MLCC) |
|---------|---------------------------|
| 0402 | 100 nF |
| 0603 | 1 uF |
| 0805 | 10 uF |
| 1206 | 22 uF |
| 1210 | 47 uF |

A warning is emitted when a suggested E-series value exceeds the package limit.

---

## Recalculable Fields

The recalculation engine (`_recalc_derived` in `spice_tolerance.py`) updates these fields after patching component values:

| Detection Type | Field | Formula | Equation ID |
|---------------|-------|---------|-------------|
| `rc_filters` | `cutoff_hz` | `1 / (2*pi*R*C)` | EQ-RC-001 |
| `voltage_dividers`, `feedback_networks` | `ratio` | `R_bot / (R_top + R_bot)` | EQ-VD-001 |
| `lc_filters` | `resonant_hz` | `1 / (2*pi*sqrt(L*C))` | EQ-LC-001 |
| `lc_filters` | `impedance_ohms` | `sqrt(L/C)` | EQ-LC-002 |
| `crystal_circuits` | `effective_load_pF` | `(C1*C2)/(C1+C2) * 1e12 + C_stray` | EQ-XL-001 |
| `opamp_circuits` (inverting) | `gain` | `-R_f / R_i` | EQ-OA-001 |
| `opamp_circuits` (non-inverting) | `gain` | `1 + R_f / R_i` | EQ-OA-002 |
| `opamp_circuits` | `gain_dB` | `20 * log10(|gain|)` | EQ-OA-003 |
| `current_sense` | `max_current_50mV_A` | `0.050 / R_shunt` | EQ-CS-001 |
| `current_sense` | `max_current_100mV_A` | `0.100 / R_shunt` | EQ-CS-002 |
| `power_regulators` (feedback divider) | `ratio` | `R_bot / (R_top + R_bot)` | EQ-VD-001 |

The comparison engine also checks for any additional fields present in the detection that were not explicitly registered (e.g., `estimated_vout`).

---

## JSON Output Schema

### Single-Value Mode

```json
{
  "changes": {
    "R5": {
      "before": 10000.0,
      "after": 4700.0,
      "before_str": "10k",
      "after_str": "4.7k",
      "unit": "ohms"
    }
  },
  "affected_subcircuits": [
    {
      "type": "voltage_dividers",
      "label": "voltage divider R5/R6",
      "components": ["R5", "R6"],
      "delta": [
        {"field": "ratio", "before": 0.5, "after": 0.6808, "delta_pct": 36.2}
      ],
      "before": {"ratio": 0.5},
      "after": {"ratio": 0.6808},
      "parasitics": {},
      "tolerance": [],
      "spice_delta": {}
    }
  ],
  "summary": {
    "components_changed": 1,
    "subcircuits_affected": 1,
    "spice_verified": false
  },
  "emc_delta": null
}
```

The `parasitics`, `tolerance`, `spice_delta`, and `emc_delta` fields are only present when the corresponding options are active.

### Sweep Mode

```json
{
  "ref": "R5",
  "values": [1000.0, 2200.0, 4700.0, 10000.0],
  "value_strs": ["1k", "2.2k", "4.7k", "10k"],
  "results": [
    {
      "value": 1000.0,
      "value_str": "1k",
      "affected_subcircuits": [
        {
          "type": "voltage_dividers",
          "label": "voltage divider R5/R6",
          "delta": [{"field": "ratio", "before": 0.5, "after": 0.909}],
          "after": {"ratio": 0.909}
        }
      ]
    }
  ]
}
```

### Fix Mode

```json
{
  "fix_suggestions": [
    {
      "detection_type": "voltage_dividers",
      "detection_index": 0,
      "target_field": "ratio",
      "target_value": 0.3,
      "suggestions": [
        {
          "ref": "R6",
          "field": "ohms",
          "current": 10000.0,
          "ideal": 4285.7,
          "anchor_ref": "R5",
          "anchor_value": 10000.0,
          "e_series": {
            "E12": {"value": 3900.0, "error_pct": -9.0},
            "E24": {"value": 4300.0, "error_pct": 0.3},
            "E96": {"value": 4320.0, "error_pct": 0.8}
          }
        }
      ],
      "footprint_warnings": []
    }
  ]
}
```

### Tolerance Fields (within affected_subcircuits)

```json
{
  "tolerance": [
    {
      "field": "cutoff_hz",
      "nominal": 1591.55,
      "worst_low": 1447.77,
      "worst_high": 1768.39,
      "spread_pct": 20.1
    }
  ]
}
```

---

## Common User Intents

Natural-language queries and their corresponding command invocations.

| User Says | Command |
|-----------|---------|
| "What if I change R5 to 4.7k" | `what_if.py analysis.json R5=4.7k --text` |
| "Sweep R5 through some standard values" | `what_if.py analysis.json R5=1k,2.2k,4.7k,10k --text` |
| "Sweep R5 from 1k to 100k" | `what_if.py analysis.json R5=1k..100k:10 --text` |
| "What's the tolerance spread on this filter" | `what_if.py analysis.json R5=10k+-5% C3=100n+-10% --text` |
| "What value gives me 3.3V on this divider" | `what_if.py analysis.json --fix voltage_dividers[0] --target 3.3 --text` |
| "Fix the crystal load capacitance" | `what_if.py analysis.json --fix crystal_circuits[0] --text` (target inferred) |
| "How does changing C3 affect EMC" | `what_if.py analysis.json C3=1u --emc --text` |
| "What if I use a 4.7k with 1% tolerance instead" | `what_if.py analysis.json R5=4.7k+-1% --text` |
| "Change R5 and C3 together, show me the filter response" | `what_if.py analysis.json R5=4.7k C3=22n --text` |
| "Export the patched design for EMC analysis" | `what_if.py analysis.json R5=4.7k --output patched.json` |
| "Verify with SPICE" | `what_if.py analysis.json R5=4.7k --spice --text` |
| "What's the best R value for 1kHz cutoff" | `what_if.py analysis.json --fix rc_filters[0] --target 1000 --text` |
| "Set the opamp gain to 20 dB" | `what_if.py analysis.json --fix opamp_circuits[0] --target 20 --text` (target field = `gain_dB`) |
| "What shunt resistor for 5A max" | `what_if.py analysis.json --fix current_sense[0] --target 5 --text` |

For fix mode, the `--target` value is in the natural unit of the first derived field for that detection type (ratio for dividers, Hz for filters, linear gain or dB for opamps, pF for crystals, amps for current sense).

---

## Combinability

Which flags and modes work together:

| Combination | Supported | Notes |
|-------------|-----------|-------|
| Single change + `--text` | Yes | Primary use case |
| Single change + `--spice` | Yes | Runs SPICE on original and patched |
| Single change + `--emc` | Yes | Full EMC diff |
| Single change + `--pcb` | Yes | Adds parasitic annotations |
| Single change + `--output` | Yes | Exports patched JSON |
| Single change + tolerance | Yes | Corner analysis on toleranced components |
| Sweep + `--text` | Yes | Markdown table output |
| Sweep + tolerance | Yes | Tolerance corners at each sweep point |
| Sweep + fixed changes | Yes | Other components held at specified values |
| Sweep + `--spice` | No | Sweep mode does not run SPICE |
| Sweep + `--emc` | No | Sweep mode exits before EMC |
| Sweep + `--output` | No | Sweep mode exits before export |
| `--fix` + `--target` | Yes | Primary fix use case |
| `--fix` (no `--target`) | Partial | Only works for detection types with inferrable targets |
| `--fix` + `--pcb` | Yes | Adds footprint compatibility warnings for capacitors |
| `--fix` + changes | No | Fix mode ignores positional changes |
| `--fix` + `--spice` | No | Fix mode exits before SPICE |
| `--fix` + `--emc` | No | Fix mode exits before EMC |
| `--emc` + `--pcb` | Yes | PCB data passed through to EMC analyzer |
| Multiple changes (no sweep) | Yes | All changed components patched simultaneously |
| Multiple sweeps | No | Only one component may use sweep syntax |
