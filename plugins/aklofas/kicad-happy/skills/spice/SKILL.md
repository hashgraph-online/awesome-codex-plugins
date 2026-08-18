---
name: spice
description: >-
  Run automatic SPICE simulations on subcircuits detected from KiCad schematic
  analysis — validates filter frequencies, divider ratios, opamp gains, LC
  resonance, and crystal load capacitance. Supports ngspice, LTspice, and Xyce
  (auto-detected). Generates testbenches, runs batch mode, produces structured
  pass/warn/fail report. Use when the user asks to simulate, verify, or
  validate any analog subcircuit — RC filters, LC filters, voltage dividers,
  opamp circuits, crystal oscillators. Also for "simulate my circuit", "run
  spice", "verify with simulation", "check my filter cutoff", "does this
  divider give the right voltage", "what's the bandwidth of this opamp stage".
  Consider suggesting simulation during design reviews when the schematic
  analyzer reports simulatable subcircuits and a SPICE simulator is available.
---

# SPICE Simulation Skill

Automatically generates and runs SPICE testbenches for circuit subcircuits detected by the `kicad` skill's schematic analyzer. Supports ngspice, LTspice, and Xyce (auto-detected). Validates calculated values (filter frequencies, divider ratios, opamp gains) against actual simulation results and produces a structured report.

This skill inverts the typical simulation workflow: instead of requiring users to create simulation sources and configure analysis (which ~2.5% of KiCad users do), it generates targeted testbenches automatically from the analyzer's subcircuit detections.

## Related Skills

| Skill | Purpose |
|-------|---------|
| `kicad` | Schematic/PCB analysis — produces the analyzer JSON this skill consumes |
| `digikey` | Parametric specs for behavioral models, datasheet downloads |
| `mouser` | Parametric specs (secondary source), datasheet downloads |
| `lcsc` | Parametric specs (no auth needed), datasheet downloads |
| `element14` | Parametric specs (international), datasheet downloads |
| `emc` | EMC pre-compliance — uses this skill's simulator infrastructure for SPICE-enhanced PDN impedance and EMI filter analysis |

**Handoff guidance:** The `kicad` skill's `analyze_schematic.py` produces the analysis JSON with subcircuit detections in the flat `findings[]` array (filtered by `detector` field). This skill reads that JSON, generates SPICE testbenches for simulatable subcircuits, runs the detected simulator (ngspice/LTspice/Xyce), and produces a structured verification report. Always run the schematic analyzer first. During a design review, run simulation after the analyzer and before writing the final report — simulation results should appear as a verification section in the report. The `emc` skill reuses this skill's simulator backend for SPICE-enhanced PDN impedance and EMI filter insertion loss checks — when ngspice is available, the EMC skill's `--spice-enhanced` flag activates these checks automatically.

## Requirements

- **A SPICE simulator** — one of the following (auto-detected, first available wins):
  - **ngspice** — `sudo apt install ngspice` (Linux) / `brew install ngspice` (macOS) / ngspice.sourceforge.io (Windows). Most common choice.
  - **LTspice** — free from analog.com/ltspice. Popular on Windows, works via wine on Linux.
  - **Xyce** — from xyce.sandia.gov. Parallel SPICE for large circuits.
  - Override with `--simulator ngspice|ltspice|xyce` or `SPICE_SIMULATOR` env var.
- **Python 3.10+** — stdlib only, no pip dependencies
- **Schematic analyzer JSON** — from `analyze_schematic.py --output`

If no simulator is installed, skip simulation gracefully and note it in the report. Do not treat a missing simulator as an error — it's an optional enhancement.

## Workflow

### Step 1: Run the schematic analyzer

```bash
python3 <kicad-skill-path>/scripts/analyze_schematic.py design.kicad_sch --analysis-dir analysis/
```

### Step 2: Run SPICE simulations

Pass `--analysis-dir analysis/` — the script auto-resolves `schematic.json`
from the manifest's current run, writes `spice.json` into the same run
folder, and parks intermediate `.cir` / `.raw` files at
`<run>/spice_work/` by default.

```bash
# Recommended: auto-resolve schematic + write spice.json into the current run
python3 <skill-path>/scripts/simulate_subcircuits.py --analysis-dir analysis/

# Explicit form — positional or --schematic path
python3 <skill-path>/scripts/simulate_subcircuits.py analysis.json --output sim_report.json

# Simulate specific types only
python3 <skill-path>/scripts/simulate_subcircuits.py --analysis-dir analysis/ --types rc_filters,voltage_dividers

# Keep simulation files for debugging (default: <run>/spice_work/ when --analysis-dir is set, else a temp dir)
python3 <skill-path>/scripts/simulate_subcircuits.py --analysis-dir analysis/ --workdir ./spice_runs

# Increase timeout for complex circuits (default: 5s per subcircuit)
python3 <skill-path>/scripts/simulate_subcircuits.py --analysis-dir analysis/ --timeout 10

# Omit file paths from output (cleaner for reports)
python3 <skill-path>/scripts/simulate_subcircuits.py --analysis-dir analysis/ --compact
```

### Step 2b (optional): PCB parasitic-aware simulation

When both schematic and PCB exist, run parasitic-annotated simulation for more accurate results on analog circuits:

```bash
# Analyze PCB with full trace segment detail
python3 <kicad-skill-path>/scripts/analyze_pcb.py design.kicad_pcb --full --output pcb.json

# Extract parasitic R/L/C from PCB geometry
python3 <skill-path>/scripts/extract_parasitics.py pcb.json --output parasitics.json

# Run simulation with PCB parasitics injected into testbenches
python3 <skill-path>/scripts/simulate_subcircuits.py analysis.json --parasitics parasitics.json --output sim_report.json
```

With `--parasitics`, testbenches include trace resistance and via inductance between components. The report shows the parasitic impact — e.g., "48mΩ trace resistance shifts RC filter fc down 0.3%."

**When to use parasitic simulation:** Consider it when the design has high-impedance feedback networks (>100kΩ), LC filters or RF matching networks, long analog signal traces, or high-frequency circuits where trace inductance matters. For typical digital designs with low-impedance power regulation, the ideal simulation is sufficient.

### Step 2c (optional): Monte Carlo tolerance analysis

Run N simulations per subcircuit with randomized component values within tolerance bands. Reports statistical distributions and sensitivity analysis — which component contributes most to output variation.

```bash
# Run 100 Monte Carlo trials per subcircuit
python3 <skill-path>/scripts/simulate_subcircuits.py analysis.json --monte-carlo 100 --output sim_report.json

# Use uniform distribution (conservative worst-case envelope) instead of Gaussian
python3 <skill-path>/scripts/simulate_subcircuits.py analysis.json --monte-carlo 100 --mc-distribution uniform

# Set random seed for reproducibility (default: 42)
python3 <skill-path>/scripts/simulate_subcircuits.py analysis.json --monte-carlo 100 --mc-seed 123
```

**Tolerance sourcing:** Tolerances are extracted from component value strings first (e.g., "680K 1%" → 1%, "22uF/6.3V/20%/X5R" → 20%). When not specified in the value string, defaults are used: resistors 5%, capacitors 10%, inductors 20%.

**Output:** Each simulation result gains a `tolerance_analysis` section with:
- **statistics**: mean, std, min, max, 3-sigma bounds, spread percentage for the primary output metric (fc, Vout, gain, etc.)
- **sensitivity**: per-component contribution percentage showing which component dominates variation (e.g., "C3 (10% tol) contributes 68% of fc variation, R5 (5% tol) contributes 32%")
- **components**: list of toleranceable components with their resolved tolerance values

**When to use Monte Carlo:** Use it for feedback networks (regulator output accuracy), precision voltage dividers, RC/LC filters near spec limits, and any circuit where tolerance stacking could push behavior outside acceptable bounds. For N=100 at ~5-50ms per simulation, expect ~0.5-5s per subcircuit.

### Step 3: Interpret results and present to user

Read the JSON report and incorporate findings into the design review. See the "Interpreting Results" and "Presenting to Users" sections below.

## What Gets Simulated

The script selects subcircuits from the analyzer's `findings[]` array (grouped by detector type). Not every detection is simulatable — the script skips configurations that can't produce meaningful results (comparators, open-loop opamps, active oscillators).

| Detector | Analysis | What's Measured | Model Fidelity | Trustworthiness |
|----------|----------|-----------------|----------------|-----------------|
| `rc_filters` | AC sweep | -3dB frequency, phase at fc | Exact (ideal passives) | High — mathematically exact |
| `lc_filters` | AC sweep | Resonant frequency, Q factor, bandwidth | Near-exact (ideal L/C + ESR) | High — small Q error from ESR |
| `voltage_dividers` | DC operating point | Output voltage, error % | Exact (ideal passives) | High — unloaded |
| `feedback_networks` | DC operating point | FB pin voltage, regulator Vout | Exact (ideal passives) | High — cross-refs power_regulators |
| `opamp_circuits` | AC sweep | Gain, -3dB bandwidth | Per-part or ideal | High with behavioral model, medium with ideal |
| `crystal_circuits` | AC impedance | Load capacitance validation | Approximate (generic BVD) | Medium |
| `transistor_circuits` | DC sweep | Threshold voltage, on-state current | Approximate (generic FET/BJT) | Medium |
| `current_sense` | DC operating point | Current at 50mV/100mV drop | Exact (ideal resistor) | High |
| `protection_devices` | DC sweep | Diode presence, clamping onset | Approximate (generic diode) | Low |
| `decoupling_analysis` | AC impedance | PDN impedance profile | Exact + ESR estimates | High for passives |
| `power_regulators` | DC operating point | Feedback divider Vout | Exact (ideal passives) | High |
| `rf_matching` | AC sweep | Matching network resonance | Exact (ideal L/C) | High |
| `bridge_circuits` | DC sweep | FET switching verification | Approximate (generic) | Medium |
| `snubber_circuits` | AC impedance | Snubber damping frequency | Exact (ideal R/C) | High |
| `rf_chains` | Gain budget | Per-stage gain/loss estimate | Heuristic | Low — role-based |
| `bms_systems` | DC operating point | Cell balance resistor validation | Exact | High |
| `inrush_analysis` | Transient | Inrush current profile | Approximate | Medium |

### What is NOT simulated

- **Comparators / open-loop opamps** — no feedback network to validate, skipped
- **Active oscillators** — self-contained modules, nothing to verify externally
- **Regulator control loop stability** — requires full compensator model (behavioral models cover DC feedback only)
- **Level-shifter FETs** — require modeling both FETs together, skipped
- **High-side power switches** — source and drain both on power rails, need full load context
- **Fuses and varistors** — require manufacturer-specific models
- **Anything without parsed component values** — if `parse_value()` couldn't extract R/C/L values, the detection is skipped

## Output Format

```json
{
  "summary": {"total": 5, "pass": 3, "warn": 1, "fail": 0, "skip": 1},
  "simulation_results": [
    {
      "subcircuit_type": "rc_filter",
      "components": ["R5", "C3"],
      "filter_type": "low-pass",
      "status": "pass",
      "expected": {"fc_hz": 15915, "type": "low-pass"},
      "simulated": {"fc_hz": 15878, "phase_at_fc_deg": -0.78},
      "delta": {"fc_error_pct": 0.23},
      "cir_file": "/tmp/spice_sim_xxx/rc-filter_R5_C3.cir",
      "log_file": "/tmp/spice_sim_xxx/rc-filter_R5_C3.log",
      "elapsed_s": 0.004
    }
  ],
  "workdir": "/tmp/spice_sim_xxx",
  "total_elapsed_s": 0.032,
  "simulator": "ngspice"
}
```

**Status values and what they mean:**

| Status | Meaning | Action |
|--------|---------|--------|
| **pass** | Simulation confirms the analyzer's detection within tolerance | Report as confirmed. No action needed. |
| **warn** | Simulation shows something worth noting — small deviation, model limitation, or edge case | Report with context. Often the "warn" reflects a real but minor issue (e.g., slight gain error from ideal opamp model). |
| **fail** | Simulation contradicts the analyzer — wrong frequency, large gain error, unexpected behavior | Investigate. Could be a real design issue, a topology misdetection by the analyzer, or a testbench generation bug. Check the `.cir` file and log. |
| **skip** | Could not simulate — missing data, unsupported configuration, simulator error | Note in report. Check the `note` field for the reason. |

## Interpreting Results

### Passive circuits (RC filters, LC filters, voltage dividers)

These simulations use ideal component models, so **the simulation is mathematically exact**. Any significant deviation (>1%) from the analyzer's calculated value indicates a bug in either:
- The analyzer's topology detection (e.g., it misidentified which net is input vs output)
- The testbench generation (topology reconstruction error)
- The analyzer's value parsing (component value parsed incorrectly)

In testing across real projects, passive simulations consistently show <0.3% error — essentially confirming the analyzer's math is correct. A "pass" here means the calculated cutoff frequency, resonant frequency, or divider ratio is accurate.

**What these simulations do NOT tell you:** Whether the real circuit behaves this way. The simulation uses ideal isolated subcircuits without loading from downstream stages, PCB parasitics, or temperature effects. A voltage divider that simulates perfectly at 1.65V may actually produce 1.62V when loaded by a high-impedance ADC input — but that loading effect is real circuit behavior, not an analyzer error.

### Opamp circuits

For recognized parts (~100 common opamps in the lookup table), the skill uses a **per-part behavioral model** with the correct GBW, slew rate, input offset, and output swing. For unrecognized parts, it falls back to the ideal model (Aol=1e6, GBW=10MHz).

The `model_note` field in the report indicates which model was used:
- `"LM358 behavioral (lookup:LM358, GBW=1.0MHz)"` — per-part model, bandwidth results are accurate
- `"ideal opamp (Aol=1e6, GBW~10MHz)"` — fallback, bandwidth results are approximate

When the behavioral model is used, the simulation correctly captures bandwidth limitations. An LM358 at gain=-100 shows bandwidth of ~10 kHz (correct for 1 MHz GBW), while the ideal model would misleadingly report ~100 kHz.

For opamps with behavioral models, gain-bandwidth limitation warnings are informational — they flag where the part's GBW constrains the circuit. These are valuable design insights, not simulation errors.

### Crystal circuits

Crystal simulations validate load capacitor selection — they check that the effective load capacitance is in a reasonable range for the crystal's specified CL. They use a generic Butterworth-Van Dyke equivalent circuit model with typical parameters, not the specific crystal's data. The primary value is catching missing or grossly wrong load capacitors, not precise frequency prediction.

### When simulations fail or skip

Check the `note` field first. Common causes:

| Note | Cause | Fix |
|------|-------|-----|
| "could not measure -3dB frequency" | AC sweep range doesn't include the -3dB point | Check if the filter fc is very low (<0.1 Hz) or very high (>100 MHz) |
| "AC measurement failed" | Testbench topology error — the circuit doesn't converge | Check `.cir` file for floating nodes or missing connections |
| "Testbench generation failed: KeyError" | Analyzer detection is missing expected fields | Check analyzer JSON — the detection may be incomplete |
| "ngspice/ltspice/xyce failed: ..." | Simulator error | Check `.log` file for error messages |

When debugging, use `--workdir` to preserve simulation files. The `.cir` file is a standard SPICE netlist that can be run manually (`ngspice -b file.cir`, or opened in LTspice/Xyce). The `.log` file contains simulator stdout/stderr.

## Presenting Results to Users

When incorporating simulation results into a design review report, follow this pattern:

### For passing simulations (confidence builders)

```
### RC Filter R5/C3 (fc=15.9kHz lowpass) -- Confirmed
Simulated fc=15.9kHz, <0.3% from calculated. Phase=-45 deg at fc as expected.
```

Keep passing results brief — they confirm what the analyzer already reported. Group them if there are many.

### For warnings (context required)

```
### Opamp U4A (inverting gain=-10)
Simulated gain=20.0dB at 1kHz, matching expected -10x. Bandwidth 98.8kHz
(ideal model). Note: LM358 GBW is ~1MHz, so actual bandwidth would be
~100kHz — verify signal frequency stays below 85kHz for <1dB gain error.
```

### For failures (investigation needed)

```
### RC Filter R12/C8 -- MISMATCH
Simulated fc=3.2kHz vs expected 15.9kHz (80% deviation). This likely indicates
the analyzer misidentified the filter topology — R12 may be serving a different
purpose (pull-up, not series filter element). Manually verify the circuit
around R12/C8 in the schematic.
```

### For skips (note the gap)

```
### Crystal Y1 (32.768kHz) -- Not simulated
Active oscillator module — no external load caps to validate.
```

### Summary line for the simulation section

```
## Simulation Verification (4 pass, 1 warn, 0 fail, 1 skip)
Verified 5 subcircuits in 0.03s. All passive circuits confirmed.
One opamp result requires interpretation (see U4A above).
```

## Model Accuracy Reference

For detailed information about the behavioral models used, their accuracy envelopes, and known limitations, read `references/simulation-models.md`. Consult this reference when:
- A user questions the accuracy of a simulation result
- An opamp or crystal simulation shows unexpected behavior
- You need to explain what "ideal model" means in concrete terms

## Script Reference

| Script | Purpose |
|--------|---------|
| `scripts/simulate_subcircuits.py` | Main orchestrator — CLI entry point, reads JSON, generates testbenches, runs simulator, produces report |
| `scripts/spice_templates.py` | Testbench generators per detector type — one function per detector name |
| `scripts/spice_models.py` | Behavioral model definitions (ideal opamp, generic semiconductors), net sanitization, engineering notation formatting |
| `scripts/spice_results.py` | Simulation output parsing and per-type evaluation with pass/warn/fail/skip logic |
| `scripts/spice_simulator.py` | Simulator backends — ngspice, LTspice, Xyce auto-detection and batch execution |
| `scripts/spice_part_library.py` | Lookup table of electrical specs for ~100 common opamps, LDOs, comparators, voltage references, crystal drivers |
| `scripts/spice_model_generator.py` | Parameterized behavioral .subckt generation from specs dicts |
| `scripts/spice_model_cache.py` | Project-local model cache in `spice/models/` next to the schematic |
| `scripts/spice_spec_fetcher.py` | Queries distributor APIs (LCSC, DigiKey, element14, Mouser), structured datasheet extractions, and PDF regex for parametric specs |
| `scripts/extract_parasitics.py` | Compute trace R, via L, coupling C from PCB analysis JSON |

## Per-Part Behavioral Models

When the analyzer detects an opamp with a recognized MPN (e.g., LM358, TL072, MCP6002), the skill uses a **per-part behavioral model** instead of the generic ideal opamp. The model captures the actual GBW, slew rate, input offset, and output swing from the part's datasheet.

Model resolution cascade:
1. **Project cache** (`<project>/spice/models/`) — previously resolved models
2. **v1.4 typed datasheet facts** — via `lookup(mpn, cache_dir=<project>/datasheets/extracted)` from the `datasheets` skill. Returns `DatasheetFacts` with `opamp.gbw`, `opamp.slew_rate`, etc. as `SpecValue` instances with trust gating. Recommended source when present.
3. **Distributor API specs** — queries LCSC (no auth), DigiKey, element14, Mouser for real parametric data
4. **v1.3 structured datasheet extraction** — reads pre-extracted specs from `<project>/datasheets/extracted/` (legacy dict-shaped JSON, scored for quality). Dual-read compat path; still consulted when v1.4 cache misses.
5. **Datasheet PDF regex extraction** — reads from `<project>/datasheets/`, extracts via text pattern matching (last resort)
6. **Built-in lookup table** — ~100 common parts as offline fallback
7. **Ideal model fallback** — if the MPN isn't recognized by any source

The `model_note` field in the report indicates which model was used: `"LM358 behavioral (lookup:LM358, GBW=1.0MHz)"` vs `"ideal opamp (Aol=1e6, GBW~10MHz)"`.

Models are cached project-locally in a `spice/` directory alongside the schematic files (same pattern as `datasheets/`). This keeps models co-located with the design and handles board revisions and subprojects naturally.

## Known Limitations

- **Voltage dividers are simulated unloaded.** The analyzer's ratio is R_bot/(R_top+R_bot) without loading. Adding a load resistor would make the simulation more "real" but would create false "errors" relative to the analyzer's calculated value. The purpose is to validate the calculation, not model the full circuit.
- **LC filter Q factor uses estimated inductor ESR.** A default Q=100 is assumed for the inductor. Real inductor Q varies from 10 (power inductors) to 300+ (RF inductors). The resonant frequency is accurate regardless of Q.
- **Opamp supply rails are inferred from net names.** May default to +/-5V if the power nets aren't labeled with voltage. Single-supply designs are detected when only VCC is found (VEE defaults to 0V).
- **Per-part models cover ~100 common parts.** Uncommon opamps/LDOs fall back to ideal models. The lookup table can be extended by adding entries to `spice_part_library.py`.
- **High-gain opamp circuits with realistic GBW** may show lower-than-expected gain at the 1 kHz measurement point when bandwidth is limited. This is physically correct behavior (the model correctly captures the GBW limitation) but may need lower-frequency measurement for accurate gain comparison.
- **Net names from the analyzer may be `__unnamed_N`.** These are KiCad internal net names for unlabeled wires. They work correctly in simulation but make `.cir` files less readable.
