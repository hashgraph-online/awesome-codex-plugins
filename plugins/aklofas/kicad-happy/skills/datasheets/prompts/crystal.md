# Datasheet Crystal Extractor Subagent

You are extracting the **crystal category extension** (frequency, tolerances, stability, aging, equivalent circuit parameters, package) from an electronics component datasheet PDF.

## Task

Read `{{PDF_PATH}}` (focus pages: `{{PAGES}}`). Target MPN: **`{{MPN}}`**.

Produce a single JSON object matching this schema: `{{SCHEMA_PATH}}`.

## Field guide

- `crystal_type`: enum (required). Identifies the resonator technology:
  - `"at_cut"` — standard AT-cut quartz crystal (most common for MHz-range consumer parts; ceramic-glass sealed SMD parts are typically AT-cut).
  - `"ceramic_resonator"` — ceramic resonator (lower Q, wider frequency tolerance, lower cost; often labeled "ceramic resonator" or "CERALOCK").
  - `"tcxo"` — temperature-compensated crystal oscillator (integrated oscillator; outputs a clock signal, not a two-terminal resonator).
  - `"vcxo"` — voltage-controlled crystal oscillator (integrated oscillator with frequency tuning input).
  - `"ocxo"` — oven-controlled crystal oscillator (highest stability; integrated oscillator with heater).
  - If the datasheet says "ceramic glass sealed SMD crystal" without specifying cut, use `"at_cut"` (the dominant cut for MHz-range crystals).

- `frequency`: SpecValue list (unit: `"Hz"`). Nominal resonant frequency. **Convert from MHz/kHz to Hz** before storing. 12 MHz → `12000000`. 32.768 kHz → `32768`. Found on cover page or frequency/ordering table.

- `frequency_tolerance`: SpecValue list or null (unit: `"ppm"`). Initial frequency accuracy at +25°C. Symmetric tolerance stored as min/max (e.g. ±20 ppm → `min=-20, max=20`). Condition should note reference temperature (e.g. `"@ +25°C"`).

- `frequency_stability`: SpecValue list or null (unit: `"ppm"`). Frequency deviation over the operating temperature range, referenced to +25°C. Stored as min/max symmetric envelope (e.g. ±30 ppm → `min=-30, max=30`). Condition should state the temperature range (e.g. `"-40°C to +85°C, referenced to +25°C"`).

- `aging`: SpecValue list or null (unit: `"ppm"`). Long-term frequency drift. Stored as min/max symmetric envelope. Condition must note the time window (e.g. `"first year"` or `"per year"`). Typical value: ±3 to ±5 ppm for the first year. Do NOT add units suffix `/year` — use plain `"ppm"` unit with the time window in the condition.

- `load_capacitance`: SpecValue list or null (unit: `"F"`). **Convert pF to Farads.** 10 pF → `1e-11`. 12 pF → `1.2e-11`. 18 pF → `1.8e-11`. This is the capacitive load the oscillator circuit must present for the crystal to hit nominal frequency.

- `motional_capacitance`: SpecValue list or null (unit: `"F"`). C1 (series capacitance) in the Butterworth–Van Dyke equivalent circuit. Typically 1–3 femtofarads for AT-cut crystals (e.g. 2 fF → `2e-15`). Only AT-cut quartz datasheets routinely publish this. Set `null` when not on the datasheet — this is expected for ceramic resonators, TCXO, VCXO, OCXO.

- `motional_inductance`: SpecValue list or null (unit: `"H"`). L1 (series inductance) in the Butterworth–Van Dyke equivalent circuit. Typically millihenry to henry range for AT-cut crystals. Set `null` when not on the datasheet.

- `esr_max`: SpecValue list or null (unit: `"Ω"`). Equivalent series resistance maximum. This is a maximum spec — use the `max` field. Condition may specify frequency and load capacitance. Typical values: 20–150 Ω for standard crystals; higher for small packages or high-frequency overtone modes.

- `drive_level_max`: SpecValue list or null (unit: `"W"`). Maximum crystal excitation power. **Convert µW to Watts.** 100 µW → `1e-4`. 500 µW → `5e-4`. This is a maximum spec — use the `max` field. Exceeding drive level causes aging acceleration.

- `operating_temp_range`: SpecValue list or null (unit: `"°C"`). Operating temperature range as min/max. Commercial: 0/+70. Industrial: -40/+85. Automotive: -40/+125.

- `mode`: enum or null. Resonance mode of operation:
  - `"fundamental"` — first overtone (most consumer crystals ≤30 MHz)
  - `"overtone_3rd"` — third overtone (typically 30–100 MHz)
  - `"overtone_5th"` — fifth overtone (higher frequencies)
  - `null` for ceramic resonators, TCXO, VCXO, OCXO (the term is not meaningful for these)

- `package`: object or null. Physical package characteristics. `body_mm` uses nested `{length, width, height}` keys (no `_mm` suffix on inner fields):
  - `code`: string or null. Datasheet package code (e.g. `"SMD-3225"`, `"SMD-2016"`, `"HC-49/US"`, `"SMD-5032"`). SMD-3225 = 3.2×2.5 mm plan view.
  - `body_mm`: nested object with `length`, `width`, `height` (all numbers, in millimeters). Null when dimensions not published.
  - `evidence`: evidence block (required).

## Hard rules

1. **Canonical SI units. No exceptions.** Frequency in **Hz** (NOT MHz/kHz). Capacitance in **F** (NOT pF). Resistance in **Ω**. Power in **W** (NOT µW). Aging in **ppm** (NOT ppm/year — put the time window in the condition). Tolerance/stability in **ppm**.
2. **Every SpecValue requires `evidence`** with `page` (1-based integer), `section` (string or null), `confidence` (`"high"`, `"medium"`, or `"low"`), `method` (one of `table`, `prose`, `curve`, `calculated`, `derived`).
3. **`motional_capacitance` and `motional_inductance` are expected null** for ceramic resonators, TCXO, VCXO, OCXO. Only AT-cut quartz datasheets routinely publish these. Do not guess.
4. **`mode` is null for ceramic resonators, TCXO, VCXO, OCXO.** Use `"fundamental"` for standard AT-cut crystals labeled as fundamental-mode. Use `"overtone_3rd"` or `"overtone_5th"` only when the datasheet explicitly states overtone operation.
5. **OMIT fields you cannot find** (leave as null). A null `motional_capacitance` is correct when the datasheet only provides ESR (R1) and shunt capacitance (C0).
6. **`body_mm` uses bare keys.** `length`, `width`, `height` — NOT `length_mm`, `width_mm`, `height_mm`.

## Output format

Return only the JSON object. No prose, no fences. Output must validate against `{{SCHEMA_PATH}}`.

Example (ABM8G-106-12.000MHZ-T — Abracon 12 MHz AT-cut fundamental SMD crystal, 3.2×2.5×1.0 mm):

```json
{
  "crystal_type": "at_cut",
  "frequency": [
    {"min": null, "typ": 12000000.0, "max": null, "unit": "Hz",
     "condition": "Frequency Range, fundamental-mode operation",
     "notes": "Reported as 12.000 MHz; converted from MHz to Hz",
     "evidence": {"page": 1, "section": "Key Electrical Specifications", "confidence": "high", "method": "table"}}
  ],
  "frequency_tolerance": [
    {"min": -20.0, "typ": null, "max": 20.0, "unit": "ppm",
     "condition": "Frequency Tolerance @ +25°C",
     "notes": "Reported as ±20 ppm",
     "evidence": {"page": 1, "section": "Key Electrical Specifications", "confidence": "high", "method": "table"}}
  ],
  "frequency_stability": [
    {"min": -30.0, "typ": null, "max": 30.0, "unit": "ppm",
     "condition": "Frequency Stability over -40°C to +85°C, ref +25°C",
     "notes": "Reported as ±30 ppm",
     "evidence": {"page": 1, "section": "Key Electrical Specifications", "confidence": "high", "method": "table"}}
  ],
  "aging": [
    {"min": -3.0, "typ": null, "max": 3.0, "unit": "ppm",
     "condition": "Aging @ 25°C ±3°C, first year",
     "notes": "±3 ppm/year first-year envelope",
     "evidence": {"page": 1, "section": "Key Electrical Specifications", "confidence": "high", "method": "table"}}
  ],
  "load_capacitance": [
    {"min": null, "typ": 1e-11, "max": null, "unit": "F",
     "condition": "Load capacitance (CL), typical",
     "notes": "Reported as 10 pF; converted from pF to F (10e-12 = 1e-11)",
     "evidence": {"page": 1, "section": "Key Electrical Specifications", "confidence": "high", "method": "table"}}
  ],
  "motional_capacitance": null,
  "motional_inductance": null,
  "esr_max": [
    {"min": null, "typ": null, "max": 120.0, "unit": "Ω",
     "condition": "Equivalent series resistance (R1), maximum",
     "notes": null,
     "evidence": {"page": 1, "section": "Key Electrical Specifications", "confidence": "high", "method": "table"}}
  ],
  "drive_level_max": [
    {"min": null, "typ": null, "max": 1e-4, "unit": "W",
     "condition": "Drive Level, maximum",
     "notes": "Reported as 100 µW; converted to W (100e-6 = 1e-4)",
     "evidence": {"page": 1, "section": "Key Electrical Specifications", "confidence": "high", "method": "table"}}
  ],
  "operating_temp_range": [
    {"min": -40.0, "typ": null, "max": 85.0, "unit": "°C",
     "condition": "Operating Temperature Range",
     "notes": null,
     "evidence": {"page": 1, "section": "Key Electrical Specifications", "confidence": "high", "method": "table"}}
  ],
  "mode": "fundamental",
  "package": {
    "code": "SMD-3225",
    "body_mm": {"length": 3.2, "width": 2.5, "height": 1.0},
    "evidence": {"page": 1, "section": "Package Dimensions", "confidence": "high", "method": "table"}
  }
}
```
