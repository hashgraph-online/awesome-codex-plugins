# Simulation Models Reference

Documentation of the SPICE models used across all phases — ideal models, per-part behavioral models, and PCB parasitic extraction. Covers accuracy envelopes, when to trust or qualify results, and the model resolution cascade.

## Table of Contents

1. [Model Resolution Cascade](#model-resolution-cascade)
2. [Passive Components](#passive-components)
3. [Ideal Opamp Model](#ideal-opamp-model)
4. [Generic Semiconductor Models](#generic-semiconductor-models)
5. [Crystal Equivalent Circuit](#crystal-equivalent-circuit)
6. [Ideal LDO Model](#ideal-ldo-model)
7. [Net Name Handling](#net-name-handling)
8. [Measurement Techniques](#measurement-techniques)
9. [Testbench Topology Reconstruction](#testbench-topology-reconstruction)
10. [Per-Part Behavioral Models](#per-part-behavioral-models)
11. [PCB Parasitic Extraction](#pcb-parasitic-extraction)
12. [Analyzer Integration Points](#analyzer-integration-points)

---

## Model Resolution Cascade

When the skill encounters an active component (opamp, LDO, comparator), it resolves the model through this cascade:

1. **Project cache** — `<project>/spice/models/manifest.json` (legacy name: `index.json`) stores previously resolved models (instant, no network)
2. **Distributor API parametric data** — queries LCSC (no auth), DigiKey, element14, Mouser for real electrical specs like GBW, slew rate, offset voltage. Structured JSON, no PDF parsing.
3. **Structured datasheet extraction** — reads pre-extracted specs from `<project>/datasheets/extracted/<MPN>.json`. Cached JSON produced by the `datasheets` skill, scored 0-10 for completeness. See `skills/datasheets/references/extraction-schema.md` and `skills/datasheets/references/quality-scoring.md`.
4. **Datasheet PDF regex extraction** — reads downloaded PDFs from `<project>/datasheets/`, extracts specs via text pattern matching. Requires `pdftotext`. Last-resort fallback.
5. **Built-in lookup table** — `spice_part_library.py` has ~100 common parts with datasheet-verified specs. Offline safety net.
6. **Ideal model fallback** — generic model with fixed parameters (e.g., 10 MHz GBW for opamps)

Real data from APIs and datasheets takes priority over the lookup table. The table serves as an offline fallback when no network or downloaded PDFs are available. Passive components (R, C, L) always use the simulator's exact built-in primitives (standard SPICE R/C/L elements) — no model resolution needed. All three supported simulators (ngspice, LTspice, Xyce) handle these identically.

The lookup table also includes crystal driver specs for ~30 MCU families (STM32, ESP32, nRF52, ATmega, RP2040) with oscillator transconductance values for startup margin analysis.

---

## Passive Components

Resistors, capacitors, and inductors use ngspice's built-in primitive elements (R, C, L). No subcircuit or model card is needed — these are mathematically exact ideal components.

**What this means for simulation accuracy:**
- RC filter cutoff frequencies are exact: fc = 1/(2*pi*R*C)
- LC resonant frequencies are exact: f0 = 1/(2*pi*sqrt(L*C))
- Voltage divider ratios are exact: Vout = Vin * Rbot/(Rtop+Rbot)

**What is NOT modeled:**
- Resistor temperature coefficient (TCR)
- Capacitor ESR, ESL, and voltage coefficient
- Inductor core saturation, DCR, and self-resonant frequency
- Component tolerance (all values are nominal)
- Parasitic capacitance of resistors, parasitic inductance of capacitors

For the subcircuits this skill simulates, these parasitics are rarely significant. The one exception is **LC filters at high frequencies** (>10 MHz) where capacitor ESL and inductor self-resonant frequency can shift the actual resonance. The simulation will show the ideal resonance; a user working above 10 MHz should be advised to check component SRF specifications.

### Inductor ESR in LC Filters

LC filter testbenches add a small series resistance to the inductor to prevent infinite Q (which makes the resonance unmeasurable in practice). The ESR is calculated as:

```
R_esr = 2 * pi * f_resonant * L / Q_assumed
```

Where Q_assumed = 100. This gives realistic peak gain (~40 dB) and measurable bandwidth. The resonant frequency is not affected by ESR — only the Q factor and peak gain.

Real inductor Q values:

| Inductor Type | Typical Q at Rated Frequency |
|---------------|------------------------------|
| Power inductor (shielded) | 10-30 |
| Multilayer chip inductor | 20-60 |
| Wire-wound chip inductor | 40-100 |
| Air-core RF inductor | 100-300 |

If the simulated Q factor matters (e.g., for a filter selectivity assessment), note that Q=100 is an assumption and the real value depends on the specific inductor.

---

## Ideal Opamp Model

### Circuit

```
.subckt IDEAL_OPAMP inp inn out vcc vee
Rin inp inn 1e12          * 1 TΩ input impedance
E1  int 0   inp inn 1e6   * Voltage-controlled source, Aol=1,000,000
R1  int out 1              * Output resistance (with C1, forms the pole)
C1  out 0   15.9155m       * Single-pole rolloff: fp = 1/(2*pi*1*15.9mF) = 10 Hz
Dhigh out vcc DLIMIT       * Rail clamp (positive)
Dlow  vee out DLIMIT       * Rail clamp (negative)
.model DLIMIT D(N=1)
.ends
```

### Key Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Open-loop gain (Aol) | 1,000,000 (120 dB) | Real opamps: 100k-10M (100-140 dB) |
| Gain-bandwidth product | 10 MHz | See comparison table below |
| Input impedance | 1 TΩ | Real FET-input: 1 TΩ; BJT-input: 1-10 MΩ |
| Output impedance | ~1 Ω at DC | Real opamps: 10-1000 Ω open-loop |
| Input offset voltage | 0 V | Real opamps: 0.01-10 mV |
| Input bias current | 0 A | Real opamps: 1 pA - 1 µA |
| Slew rate | Not modeled | Real opamps: 0.3-2000 V/µs |
| CMRR | Infinite | Real opamps: 60-140 dB |
| Supply current | 0 A | Real opamps: 0.3 µA - 10 mA |
| Rail-to-rail output | Clamped by diodes | Actual swing depends on output stage topology |

### GBW Comparison

The ideal model's 10 MHz GBW is a rough middle ground. Here's how it compares to common opamps:

| Part | GBW | Bandwidth at Gain=10 | Ideal Model BW at Gain=10 |
|------|-----|----------------------|---------------------------|
| LM358 | 1 MHz | 100 kHz | 1 MHz (10x too high) |
| MCP6002 | 1 MHz | 100 kHz | 1 MHz (10x too high) |
| TLV2372 | 3 MHz | 300 kHz | 1 MHz (3x too high) |
| OPA2340 | 5.5 MHz | 550 kHz | 1 MHz (2x too high) |
| AD8605 | 10 MHz | 1 MHz | 1 MHz (correct) |
| OPA1612 | 80 MHz | 8 MHz | 1 MHz (8x too low) |
| AD8099 | 710 MHz | 71 MHz | 1 MHz (71x too low) |

**Guidance for reporting:** The gain measurement at 1 kHz is always accurate (well within the flat passband of any real opamp). The bandwidth measurement is only accurate if the real part happens to have GBW near 10 MHz. Always qualify bandwidth results with the actual part's GBW.

### What the Ideal Opamp Model IS Good For

1. **Validating feedback network gain** — confirms Rf/Ri ratio produces expected gain
2. **Catching resistor value errors** — a 10x gain error from swapped resistors shows up clearly
3. **Verifying inverting vs non-inverting topology** — the sign of the gain confirms configuration
4. **Integrator/compensator zero-pole placement** — RC time constants in the feedback network

### What It Is NOT Good For

1. **Bandwidth prediction** — always wrong unless GBW happens to be 10 MHz
2. **Stability analysis** — real opamp phase characteristics differ significantly
3. **Slew rate limiting** — not modeled at all
4. **Output current/voltage limits** — rail clamp is crude
5. **Noise analysis** — no noise sources in the model
6. **CMRR effects** — not modeled

---

## Generic Semiconductor Models

These model cards use ngspice built-in equations with typical (not manufacturer-specific) parameters. They're included for future expansion but are not currently used in Phase 1 testbenches (passive and opamp circuits don't need them).

### Diode Models

| Model Name | Based On | Forward Drop | Reverse Breakdown | Use Case |
|------------|----------|--------------|-------------------|----------|
| D_GENERIC | 1N4148 | ~0.7 V | 100 V | General purpose |
| D_SCHOTTKY | Generic | ~0.3 V | 40 V | Schottky rectifier |
| D_ZENER3V3 | Generic | ~0.7 V | 3.3 V (reverse) | 3.3V Zener |
| D_ZENER5V1 | Generic | ~0.7 V | 5.1 V (reverse) | 5.1V Zener |

### Transistor Models

| Model Name | Based On | hFE/Beta | fT | Use Case |
|------------|----------|----------|-----|----------|
| NPN_GENERIC | 2N2222 | 200 | ~300 MHz | General NPN |
| PNP_GENERIC | 2N2907 | 200 | ~200 MHz | General PNP |
| NMOS_GENERIC | Level 1 | Vth=1.5V | — | Generic N-MOSFET |
| PMOS_GENERIC | Level 1 | Vth=-1.5V | — | Generic P-MOSFET |

These models are suitable for DC bias point and basic switching analysis. They are NOT suitable for:
- RF circuit simulation (parasitic capacitances are generic)
- Precision analog (offset, noise, matching not modeled)
- Power electronics (SOA, thermal effects not modeled)

---

## Crystal Equivalent Circuit

The Butterworth-Van Dyke (BVD) model represents a quartz crystal as a series RLC (motional branch) in parallel with a shunt capacitance C0:

```
         Lm       Cm       Rm
xtal1 ---[===]---||---[===]--- xtal2
  |                               |
  +----------||-------------------+
             C0
```

### Model Parameters by Frequency Range

| Parameter | <1 MHz (e.g., 32.768 kHz) | >1 MHz (e.g., 8-25 MHz) |
|-----------|---------------------------|--------------------------|
| Rm (motional resistance) | 40 kΩ | 30 Ω |
| Cm (motional capacitance) | 2 fF | 20 fF |
| Lm (motional inductance) | Calculated from f and Cm | Calculated from f and Cm |
| C0 (shunt capacitance) | 1.5 pF | 5 pF |

**These are generic estimates.** Real crystal parameters vary significantly between manufacturers and even batches. The datasheet specifies Rm (ESR) and CL (load capacitance) — these are the two most important parameters for oscillator design.

### What the Crystal Simulation Tests

The testbench validates that the **load capacitor values produce a reasonable effective CL**:

```
CL_effective = (C1 * C2) / (C1 + C2) + C_stray
```

Where C_stray ≈ 3 pF (typical PCB stray capacitance). The analyzer calculates this and the simulation confirms the cap values. The primary check is:
- Are both load caps present?
- Is the effective CL in a reasonable range (4-30 pF)?
- If the crystal datasheet specifies CL, does it match?

### What It Does NOT Test

- Whether the oscillator will actually start (requires the driving amplifier model)
- Negative resistance margin (requires the IC's crystal driver model)
- Frequency pulling from CL mismatch (requires precise crystal parameters)
- Drive level and crystal aging effects

---

## Ideal LDO Model

The LDO subcircuit models a linear regulator's DC behavior:

```
.subckt IDEAL_LDO vin vout gnd fb
* Error amplifier compares FB pin to internal Vref
* PMOS pass element with dropout ~0.2V
```

This model is **not currently used in Phase 1 testbenches** — regulator simulation requires control loop modeling for stability analysis, which is Phase 2. The model is included in the codebase for future use.

---

## Net Name Handling

KiCad net names are translated to ngspice-safe names:

| KiCad Net | ngspice Net | Rule |
|-----------|-------------|------|
| `GND`, `gnd`, `earth`, `VSS` | `0` | Ground nets → node 0 |
| `3V3` | `n3V3` | Leading digit → prefix with `n` |
| `Net-(U3-pin7)` | `Net__U3_pin7_` | Special chars → underscores |
| `__unnamed_0` | `__unnamed_0` | Internal nets pass through |

The `_sanitize_net()` function in `spice_models.py` handles this translation. When debugging a `.cir` file, KiCad net names in the comment header map to the sanitized names in the netlist.

### Voltage Inference from Net Names

For voltage divider simulations, the input voltage is inferred from the top net name:

| Net Name Pattern | Inferred Voltage |
|------------------|------------------|
| `3V3`, `+3.3V` | 3.3 V |
| `5V`, `+5V`, `5V0` | 5.0 V |
| `1V8` | 1.8 V |
| `12V` | 12.0 V |
| `VBUS`, `USB_VBUS` | 5.0 V |
| `VBAT`, `BATTERY` | 3.7 V |
| `VCC`, `VDD` | 3.3 V (default for modern designs) |
| Anything else | 3.3 V (default) |

If the inferred voltage is wrong, the absolute Vout value will be wrong but the error percentage will still be ~0% (because both expected and simulated use the same ratio). The key metric is the error percentage, not the absolute voltage.

---

## Measurement Techniques

### ngspice Backend

The ngspice backend uses `.control` blocks (ngspice scripting) rather than `.meas` statements in the netlist body. This is because:

1. `.control` blocks allow `let` for computed values (e.g., `let target = gain_1k - 3`)
2. Results are written as ASCII text via `echo`, avoiding binary `.raw` file parsing
3. Flow control (`if`/`else`) is available for conditional measurement

### LTspice and Xyce Backends

LTspice and Xyce use `.meas`/`.measure` statements directly in the netlist body (no `.control` block). Measurement results are parsed from the `.log` file (LTspice) or stdout (Xyce). The `SpiceTestbench` class abstracts the difference — generators define measurement intent (what to measure), and the backend renders the simulator-specific syntax.

### Key ngspice Gotchas

**`meas` cannot reference other `meas` variables.** This fails:
```spice
meas ac gain_dc find vdb(out) at=10
meas ac bw_3db when vdb(out)=gain_dc-3  * ERROR: gain_dc is not a number here
```

The workaround is to use `let` after `meas`:
```spice
meas ac gain_1k find vdb(out) at=1k
let target = gain_1k - 3
meas ac bw_3db when vdb(out)=target fall=1
```

**`find ... at=X` requires X to be in the swept range.** If the AC sweep starts at 1 Hz and you ask `find ... at=0.1`, the measurement fails silently and the variable is empty.

**Empty variables produce empty strings in `echo`.** When a measurement fails, `$&varname` expands to nothing, producing `key=` in the output file. The parser (`spice_results.py`) handles this by treating empty values as `None`.

**`when ... rise=1` and `fall=1` matter.** For a bandpass response, there are two -3dB crossings — one rising and one falling. Use `rise=1` for the lower frequency crossing and `fall=1` for the upper.

---

## Testbench Topology Reconstruction

The testbench generators reconstruct subcircuit topology from the analyzer's detection data. This is the most error-prone part of the pipeline — the analyzer reports which components are involved and what nets they connect to, but the testbench must reconstruct the full circuit from this information.

### RC Filter Topology

The analyzer reports `type` (low-pass, high-pass, RC-network), `input_net`, `output_net`, and `ground_net`. The testbench places:
- **Low-pass:** R from input to output, C from output to ground
- **High-pass:** C from input to output, R from output to ground
- **RC-network (ambiguous):** Defaults to low-pass

### Opamp Topology

This is the most complex reconstruction. The testbench must:
1. Place the ideal opamp with correct pin assignment
2. Place the feedback resistor/capacitor between output and inverting input
3. Place the input resistor appropriately (depends on configuration)
4. Bias the non-inverting input for inverting configurations (tie to ground)
5. Connect power supply rails

**Common failure modes:**
- **Floating non-inverting input** — inverting configurations need the positive input biased. The testbench adds `Rpos_bias` (0.001 Ω to ground) for this.
- **Transimpedance amplifiers** — no input resistor means the stimulus must be a current source, not a voltage source. Currently these configurations often skip.
- **Buffer (unity gain)** — output connected directly to inverting input. The testbench must drive the non-inverting input instead.
- **Non-inverting amplifier** — the "input resistor" from the analyzer is actually the ground-leg resistor (from inverting input to ground, setting the gain). The testbench repositions it.

### Voltage Divider Topology

Straightforward: VIN → R_top → mid_net → R_bottom → ground. No load resistor is added — the simulation validates the unloaded ratio, which matches what the analyzer calculates.

---

## Per-Part Behavioral Models

When a recognized MPN is detected (e.g., LM358, TL072, MCP6002), the skill generates a parameterized `.subckt` with the part's actual GBW, slew rate, input offset, and output swing from the lookup table in `spice_part_library.py`.

### Model Parameters Used

| Parameter | Source | Impact |
|-----------|--------|--------|
| `gbw_hz` | Datasheet GBW | Sets the dominant pole → correct bandwidth at any gain |
| `aol_db` | Datasheet open-loop gain | Determines loop gain margin and gain accuracy |
| `slew_vus` | Datasheet slew rate | (Reserved for future transient simulation) |
| `vos_mv` | Datasheet input offset | Shifts DC operating point by Vos |
| `rin_ohms` | Datasheet input impedance | Affects high-impedance source loading |
| `swing_v` | Datasheet output swing from rail | Determines output clipping points |
| `rro`/`rri` | Rail-to-rail output/input | Affects clamp behavior near supply rails |

### Adaptive Measurement Frequency

The gain measurement frequency adapts to each circuit's expected bandwidth:

```
f_measure = GBW / (100 × |gain|)
```

Clamped to [1, 1000] Hz. This ensures the measurement is in the passband even for high-gain circuits with low-GBW parts, preventing false failures from measuring above the bandwidth.

### Behavioral Model Gain Warnings

When a behavioral model shows a large gain deviation (>2 dB) from expected, the result is a **warn** (not fail). This is because the lower Aol in real parts makes the testbench topology reconstruction more sensitive — small feedback path errors that the ideal model's massive loop gain masked can produce gain discrepancies with realistic models. These warnings flag circuits worth investigating but are not automatically design bugs.

---

## PCB Parasitic Extraction

Phase 3 adds the ability to inject PCB layout parasitics into SPICE testbenches for pre-layout vs post-layout comparison.

### Extraction Pipeline

```
analyze_pcb.py --full → pcb.json (with trace_segments and via_details)
extract_parasitics.py → parasitics.json (per-net R, L, C values)
simulate_subcircuits.py --parasitics parasitics.json → annotated simulation
```

### Parasitic Formulas

**Trace resistance (IPC-2221A):**
```
R = ρ_Cu × L / (W × T)
ρ_Cu = 1.68×10⁻⁸ Ω·m (copper at 20°C)
```
For 1oz copper (T=0.035mm), 0.254mm wide, 25.4mm long: R = 48 mΩ

**Via resistance:**
```
R_via = ρ_Cu × H / (π × ((D/2)² - ((D-2T_plating)/2)²))
T_plating ≈ 25 µm typical
```

**Via inductance:**
```
L_via ≈ (µ₀ × H / 2π) × ln(2H/D)
```
Typical 0.3mm drill through 1.6mm board: ~0.7 nH

### Injection Thresholds

Parasitics are only injected when significant relative to the circuit:
- Trace R injected if >0.1% of the smallest resistor in the subcircuit
- Via L injected if the circuit operates above ~10 MHz
- Coupling C injected if >1% of any capacitor in the subcircuit

---

## Analyzer Integration Points

The SPICE skill consumes data from multiple analyzer outputs:

### From Schematic Analyzer (`analyze_schematic.py`)
- **findings[]** — all 21+ subcircuit detections (grouped by `detector` field)
- **Component MPN** — `det["value"]` used for behavioral model lookup
- **Power rail nets** — for opamp supply inference
- **Regulator output capacitors** — values, package sizes, ESR estimates
- **Compensation capacitors** — feed-forward/compensation role on FB nets

### From PCB Analyzer (`analyze_pcb.py --full`)
- **trace_segments** — per-segment width, length, layer, impedance
- **via_details** — drill size, layer span, stub length
- **pad_to_pad_distances** — actual routed distance between components
- **return_path_continuity** — ground plane coverage under signal traces
- **stackup** — εr, dielectric thickness, copper weight for impedance

### From Gerber Analyzer (`analyze_gerbers.py`)
- **net_copper_usage** — per-net draw/flash operation counts (proxy for copper area)
