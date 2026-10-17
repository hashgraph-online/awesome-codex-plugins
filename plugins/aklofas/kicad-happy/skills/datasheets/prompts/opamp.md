# Datasheet Op-Amp Extractor Subagent

You are extracting the **op-amp category extension** (topology, channels, supply range, AC/DC parameters, output swing, package, thermal characteristics) from an electronics component datasheet PDF.

## Task

Read `{{PDF_PATH}}` (focus pages: `{{PAGES}}`). Target MPN: **`{{MPN}}`**.

Produce a single JSON object matching this schema: `{{SCHEMA_PATH}}`.

## Field guide

- `opamp_topology`: enum. Choose the single closest match:
  - `general_purpose` — standard voltage-feedback BJT or CMOS op-amp without special rail-to-rail or precision claims (LM358, LM741, TL071)
  - `precision` — low offset/drift without rail-to-rail spec (OP07, OPA277)
  - `rail_to_rail_io` — rail-to-rail input AND output (MCP6001/2/4, MCP6271, OPA364)
  - `rail_to_rail_output` — rail-to-rail output only, not input (LMV358, LM2904N)
  - `jfet_input` — JFET differential input stage (TL071, TL081, OPA134)
  - `cmos_input` — CMOS input, rail-to-rail not specified (MAX4238)
  - `chopper` — auto-zero / chopper-stabilized (MCP6V01, LTC2054)
  - `instrumentation` — instrumentation amplifier topology (INA128, AD8221)
  - `comparator` — open-collector/open-drain output comparator (LM393, LM339)
  When multiple topologies apply (e.g. a part that is both CMOS and rail-to-rail I/O), prefer `rail_to_rail_io` over `cmos_input`; prefer `precision` over `general_purpose`.

- `channels`: integer ≥ 1. Single op-amp = 1, dual = 2, quad = 4. Found on cover or in Features section.

- `vsupply_range`: SpecValue list (unit: `"V"`). Total V+ to V− supply voltage. For single-supply parts store as `{min: min_V, max: max_V}`. For split-supply capable parts, store the single-supply equivalent as the primary entry (e.g. LM358: min=3, max=32) with a condition note mentioning the split-supply range. Condition carries supply topology.

- `vsupply_split_capable`: boolean or null. True when the datasheet explicitly specifies split (bipolar) supply operation (e.g. ±15V). False when single-supply only.

- `iq_per_amp`: SpecValue list (unit: `"A"`). Quiescent current PER OP-AMP CHANNEL. If the datasheet only publishes total supply current (ICC) for the whole package, divide by `channels` before storing. Condition carries VS and IO=0. Store µA as A (e.g. 100µA → `1e-4`).

- `gbw`: SpecValue list (unit: `"Hz"` — NOT MHz; store 1MHz as `1e6`). Gain-bandwidth product: frequency at which open-loop gain is 0dB. Found in AC Characteristics or from open-loop Bode plot. Condition carries supply voltage.

- `slew_rate`: SpecValue list (unit: `"V/s"` — NOT V/µs; store 0.6V/µs as `6e5`). Rate of output voltage change. Found in AC Characteristics table, or from step response graph. Condition carries supply and load.

- `vos`: SpecValue list (unit: `"V"`). Input offset voltage. Store mV as V (e.g. 7mV → `7e-3`). Condition carries VCM and temperature.

- `ib`: SpecValue list (unit: `"A"`). Input bias current. BJT-input op-amps: typically nA (e.g. 45nA → `4.5e-8`). CMOS/JFET-input: typically pA (e.g. 1pA → `1e-12`). Condition carries temperature.

- `cmrr`: SpecValue list (unit: `"dB"`). Common mode rejection ratio. Higher is better. Condition carries common mode input range and supply.

- `psrr`: SpecValue list (unit: `"dB"`). Power supply rejection ratio. Higher is better. Condition carries supply range.

- `vout_swing_high`: SpecValue list (unit: `"V"`). Positive output headroom — how far the output falls SHORT of V+. Store as a positive number. For rail-to-rail output parts, this is typically 25–50mV. For non-R-R parts, this may be 1.5–2V or more. Condition carries supply voltage and load current.

- `vout_swing_low`: SpecValue list (unit: `"V"`). Negative output headroom — how far the output rises ABOVE V−. Store as a positive number (not negative). For rail-to-rail output parts, typically 25–50mV. For parts with output including ground, this may be 5–20mV at light load. Condition carries supply voltage and load current.

- `output_drive_current`: SpecValue list (unit: `"A"`). Output source or sink current capability. May be published as short-circuit current (ISC), output sourcing current (ISOURCE), or output sinking current (ISINK). Multiple SpecValues when different conditions give different limits. Store mA as A (e.g. 30mA → `0.03`).

- `unity_gain_stable`: boolean or null. True when specified stable at gain=1. False when minimum stable gain is specified > 1. Null when not stated in datasheet.

- `shutdown_pin`: string or null. Pin number string when the part has a shutdown/enable pin (matches `base.pinout[*].numbers`). Null when no shutdown pin — most general-purpose op-amps have no shutdown pin.

- `thermal_resistance`: nested object with three nullable SpecValue-list sub-fields, all `unit: "°C/W"` or `"K/W"`:
  - `rtheta_ja` — junction-to-ambient. Present for most packages.
  - `rtheta_jc` — junction-to-case. Null when not specified.
  - `rtheta_jl` — junction-to-lead. Null for most op-amp packages.
  Found in Thermal Resistance or Package Characteristics section.

- `package`: object with `code` (string), `pin_count` (integer), `pitch_mm` (number or null), `body_mm` (nested object with `length`, `width`, `height` — all numbers in millimeters; aligns with `base.schema.json`'s body_mm shape), `thermal_pad` (boolean or null), `evidence`. Found in Package Dimensions / Mechanical Data section.

## Hard rules

1. **Canonical SI units.** Voltage in V. Current in A (store µA as A: 100µA → `1e-4`). Frequency in Hz (NOT MHz: 1MHz → `1e6`). Slew rate in V/s (NOT V/µs: 0.6V/µs → `6e5`). CMRR/PSRR in dB. The verifier rejects non-SI prefix strings and non-canonical unit tokens.
2. **Every SpecValue requires `evidence`** with `page` (1-based integer), `section` (string or null), `confidence` (`"high"`, `"medium"`, or `"low"`), `method` (one of `table`, `prose`, `curve`, `calculated`, `derived`). Use `"table"` for parameter tables; `"curve"` for values read off a graph; `"prose"` for values from descriptive text.
3. **iq_per_amp is per-channel, not total.** If the datasheet publishes only total ICC (e.g. 1mA for a dual op-amp), divide by `channels` (0.5mA → `5e-4`). Document this in the `notes` field.
4. **shutdown_pin matches base.pinout[*].numbers.** If the part has a shutdown/enable/standby pin, the pin number string must match the number recorded in the base pinout extraction.
5. **Deferred fields — omit entirely.** `noise_voltage_density`, `noise_current_density`, and `phase_margin` are NOT in this schema (deferred to v1.5 due to V/√Hz and degrees unit issues). Do not attempt to squeeze them into other fields.
6. **OMIT fields you cannot find** with null. No guessing. A missing `slew_rate` is better than a hallucinated one.
7. **vout_swing_high and vout_swing_low are positive headroom numbers.** They represent the gap between the output rail and V+/V−, NOT the absolute output voltage. For a rail-to-rail part with VOH=VDD−25mV, store `vout_swing_high=0.025`.

## Output format

Return only the JSON object. No prose, no fences. Output must validate against `{{SCHEMA_PATH}}`.

Example (LM358 — Fairchild/ON Semi BJT general-purpose dual single-supply, SOIC-8/PDIP-8; values from datasheet at VCC=5V, TA=25°C):

```json
{
  "opamp_topology": "general_purpose",
  "channels": 2,
  "vsupply_range": [
    {"min": 3, "typ": null, "max": 32, "unit": "V",
     "condition": "Single supply (VCC to GND); split supply ±1.5V to ±16V also supported",
     "notes": "LM358/LM358A: 3V–32V single, ±1.5V–±16V split. From Absolute Maximum Ratings.",
     "evidence": {"page": 2, "section": "Absolute Maximum Ratings", "confidence": "high", "method": "table"}}
  ],
  "vsupply_split_capable": true,
  "iq_per_amp": [
    {"min": null, "typ": 2.5e-4, "max": 6e-4, "unit": "A",
     "condition": "RL=inf, VCC=5V; per-amp (ICC total / 2 channels)",
     "notes": "Datasheet ICC typ=0.5mA total for dual; per-amp = 0.25mA typ. Max ICC=1.2mA total → 0.6mA per-amp.",
     "evidence": {"page": 3, "section": "Electrical Characteristics", "confidence": "high", "method": "table"}}
  ],
  "gbw": [
    {"min": null, "typ": 1e6, "max": null, "unit": "Hz",
     "condition": "Unity-gain crossover from open-loop frequency response graph",
     "notes": "GBW not tabulated; read from open-loop Bode plot (~1MHz at 0dB crossover).",
     "evidence": {"page": 7, "section": "Typical Performance Characteristics", "confidence": "medium", "method": "curve"}}
  ],
  "slew_rate": null,
  "vos": [
    {"min": null, "typ": 2.9e-3, "max": 7e-3, "unit": "V",
     "condition": "VCM=0V to VCC-1.5V, VO(P)=1.4V, RS=0Ω, TA=25°C",
     "notes": null,
     "evidence": {"page": 3, "section": "Electrical Characteristics", "confidence": "high", "method": "table"}}
  ],
  "ib": [
    {"min": null, "typ": 4.5e-8, "max": 2.5e-7, "unit": "A",
     "condition": "TA=25°C",
     "notes": "Datasheet IBIAS typ=45nA, max=250nA.",
     "evidence": {"page": 3, "section": "Electrical Characteristics", "confidence": "high", "method": "table"}}
  ],
  "cmrr": [
    {"min": 65, "typ": 65, "max": null, "unit": "dB",
     "condition": "TA=25°C",
     "notes": null,
     "evidence": {"page": 3, "section": "Electrical Characteristics", "confidence": "high", "method": "table"}}
  ],
  "psrr": [
    {"min": 65, "typ": 100, "max": null, "unit": "dB",
     "condition": "TA=25°C",
     "notes": null,
     "evidence": {"page": 3, "section": "Electrical Characteristics", "confidence": "high", "method": "table"}}
  ],
  "vout_swing_high": [
    {"min": null, "typ": null, "max": 2.0, "unit": "V",
     "condition": "VCC=30V, RL=10kΩ; headroom from V+ (VOH=28V → ~2V below VCC)",
     "notes": "Output is NOT rail-to-rail. VOH=28V at VCC=30V → ~2V headroom.",
     "evidence": {"page": 3, "section": "Electrical Characteristics", "confidence": "high", "method": "table"}}
  ],
  "vout_swing_low": [
    {"min": null, "typ": 5e-3, "max": 20e-3, "unit": "V",
     "condition": "VCC=5V, RL=10kΩ; VO(L) typ=5mV, max=20mV above GND",
     "notes": null,
     "evidence": {"page": 3, "section": "Electrical Characteristics", "confidence": "high", "method": "table"}}
  ],
  "output_drive_current": [
    {"min": 20e-3, "typ": 30e-3, "max": null, "unit": "A",
     "condition": "VI(+)=1V, VI(-)=0V, VCC=15V, VO(P)=2V; source current (ISOURCE)",
     "notes": "Sink current (ISINK) typ=15mA at same conditions.",
     "evidence": {"page": 3, "section": "Electrical Characteristics", "confidence": "high", "method": "table"}}
  ],
  "unity_gain_stable": true,
  "shutdown_pin": null,
  "thermal_resistance": {
    "rtheta_ja": [
      {"min": null, "typ": null, "max": 150, "unit": "°C/W",
       "condition": "SOIC-8 package, free air",
       "notes": "Typical value for SOIC-8; not explicitly tabulated in this datasheet.",
       "evidence": {"page": 2, "section": "Absolute Maximum Ratings", "confidence": "medium", "method": "prose"}}
    ],
    "rtheta_jc": null,
    "rtheta_jl": null
  },
  "package": {
    "code": "SOIC-8", "pin_count": 8, "pitch_mm": 1.27,
    "body_mm": {"length": 4.9, "width": 3.9, "height": 1.5},
    "thermal_pad": false,
    "evidence": {"page": 8, "section": "Package Dimensions", "confidence": "medium", "method": "table"}
  }
}
```
