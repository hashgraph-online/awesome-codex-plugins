# Datasheet Diode Extractor Subagent

You are extracting the **diode category extension** (forward/reverse ratings, recovery, capacitance, package, thermal limits) from an electronics component datasheet PDF.

## Task

Read `{{PDF_PATH}}` (focus pages: `{{PAGES}}`). Target MPN: **`{{MPN}}`**.

Produce a single JSON object matching this schema: `{{SCHEMA_PATH}}`.

## Field guide

- `diode_type`: enum. Choose the single closest match: `signal` (general-purpose small-signal), `switching` (fast switching, e.g. 1N4148), `schottky` (metal-semiconductor junction, low Vf), `zener` (voltage reference/clamp), `tvs` (transient voltage suppressor), `rectifier` (power rectifier, slow), `bridge` (bridge rectifier array), `varicap` (voltage-variable capacitor / tuning diode). The cover/Features section usually announces the type.
- `vf`: SpecValue list (`max`, `unit: "V"`). Multiple SpecValues when the datasheet gives Vf at different If test currents. Carry each test condition in `condition` (e.g. `"IF=10mA"`, `"iF=5A, TC=25°C"`). Found in Electrical Characteristics table.
- `if_max`: SpecValue list (`max`, `unit: "A"`). Emit separate SpecValues for continuous (IF), average rectified (IF(AV)), and repetitive peak (IFRM) variants — disambiguate via `condition` string. Found in Maximum/Absolute Maximum Ratings table.
- `ifsm`: SpecValue list (`max`, `unit: "A"`). Non-repetitive peak surge current. Single SpecValue typically. Condition carries pulse width or half-cycle description.
- `vr_max`: SpecValue list (`max`, `unit: "V"`). Emit separate SpecValues for VRRM (peak repetitive), VR (DC blocking), and VRWM (working peak inverse) when all three are specified. Found in Maximum Ratings table.
- `breakdown_voltage`: SpecValue list (`min`, `unit: "V"`). Reverse avalanche breakdown V_BR — distinct from vr_max (rated working voltage). Found in Electrical Characteristics. Null when not explicitly specified (many power Schottky diodes omit it).
- `ir`: SpecValue list (`max`, `unit: "A"`). Reverse leakage current. Multiple SpecValues for different reverse voltage and junction temperature test conditions. Found in Electrical Characteristics.
- `trr`: SpecValue list (`max`, `unit: "s"` — seconds, NOT nanoseconds). Reverse recovery time. Found in Dynamic / Switching Characteristics. Null for slow rectifiers and zeners.
- `cd`: SpecValue list (`max`, `unit: "F"` — farads, NOT picofarads). Junction capacitance. Condition carries Vr and test frequency. Most relevant for varicap, signal, and switching diodes.
- `vz`: SpecValue list (`typ`, `unit: "V"`). Zener breakdown voltage. Null for all non-zener diode types. Condition carries Iz test current.
- `power_dissipation`: SpecValue list (`max`, `unit: "W"`). Continuous power dissipation. Condition carries Ta or TL (e.g. `"TL≤25°C"`, `"TA=25°C"`). Found in Maximum Ratings.
- `tj_max`: SpecValue list (`unit: "°C"`). Operating junction temperature. Populate `min` with storage/operating lower bound if given, `max` with the upper limit. Found in Maximum Ratings.
- `thermal_resistance`: nested object with three nullable SpecValue-list sub-fields, all `unit: "K/W"`:
  - `rtheta_ja` — junction-to-ambient. Present for most packages; condition may specify board/pad conditions.
  - `rtheta_jc` — junction-to-case. Present for some power packages.
  - `rtheta_jl` — junction-to-lead. Common for SMD packages (SMC, SMA). Null for through-hole axial parts.
  Found in Thermal Characteristics table.
- `package`: object with `code` (string), `pin_count` (integer), `pitch_mm` (number or null), `body_mm` (nested object with `length`, `width`, `height` — all numbers in millimeters; aligns with `base.schema.json`'s body_mm shape), `thermal_pad` (boolean or null), `evidence`. Found in Package Dimensions / Mechanical Data section.
- `marking_code`: string or null. Surface marking printed on the package (e.g. `"V4148"`, `"B540"`). Found in Marking / Ordering Information section.
- `polarity_marking_convention`: string or null. How the cathode is identified on the physical part (e.g. `"cathode band"`, `"polarity band on plastic body"`, `"K mark"`, `"flat side = cathode"`).

## Hard rules

1. **Canonical SI units.** Capacitance in F (NOT pF — store 4pF as `4e-12` with `unit: "F"`). Time in s (NOT ns — store 8ns as `8e-9` with `unit: "s"`). Resistance in Ω. Voltage in V. Current in A. Power in W. Thermal resistance in K/W. The verifier rejects non-SI prefix strings.
2. **Every SpecValue requires `evidence`** with `page` (1-based integer), `section` (string or null), `confidence` (`"high"`, `"medium"`, or `"low"`), `method` (one of `table`, `prose`, `curve`, `calculated`, `derived`). Use `"table"` for values read from a parameter table; `"curve"` for values read off a graph (lower confidence); `"prose"` for values found in descriptive text; `"calculated"` for values resolved from a symbolic expression; `"derived"` for values inferred from other datasheet facts.
3. **OMIT fields you cannot find** with null. No guessing. A missing `trr` is much better than a hallucinated one.
4. **Type-specific fields.** `vz` only for zeners. `trr` typically null for slow rectifiers and zeners. `cd` most relevant for varicaps and signal/switching diodes — still populate for other types if the datasheet specifies it.
5. **Multiple test conditions = multiple SpecValues.** If `vf` is given at If=1mA AND If=10mA AND If=100mA, emit three separate SpecValue entries in the `vf` array, each with a distinct `condition` string. Same rule applies to `if_max` (continuous / average / peak) and `vr_max` (VRRM / VR / VRWM).

## Output format

Return only the JSON object. No prose, no fences. Output must validate against `{{SCHEMA_PATH}}`.

Example (MBRS540T3G — ON Semiconductor Schottky power rectifier, SMC package):

```json
{
  "diode_type": "schottky",
  "vf": [{"min": null, "typ": null, "max": 0.50, "unit": "V",
          "condition": "iF=5A, TC=25°C", "notes": null,
          "evidence": {"page": 2, "section": "Electrical Characteristics", "confidence": "high", "method": "table"}}],
  "if_max": [
    {"min": null, "typ": null, "max": 5.0, "unit": "A",
     "condition": "Average rectified, TC=105°C", "notes": null,
     "evidence": {"page": 2, "section": "Maximum Ratings", "confidence": "high", "method": "table"}},
    {"min": null, "typ": null, "max": 10.0, "unit": "A",
     "condition": "Repetitive peak, square wave 20kHz, TC=80°C", "notes": null,
     "evidence": {"page": 2, "section": "Maximum Ratings", "confidence": "high", "method": "table"}}
  ],
  "ifsm": [{"min": null, "typ": null, "max": 190, "unit": "A",
            "condition": "Halfwave single phase 60Hz surge", "notes": null,
            "evidence": {"page": 2, "section": "Maximum Ratings", "confidence": "high", "method": "table"}}],
  "vr_max": [{"min": null, "typ": null, "max": 40, "unit": "V",
              "condition": "VRRM / VRWM / VR (DC blocking)", "notes": null,
              "evidence": {"page": 2, "section": "Maximum Ratings", "confidence": "high", "method": "table"}}],
  "tj_max": [{"min": -65, "typ": null, "max": 150, "unit": "°C", "condition": null, "notes": null,
              "evidence": {"page": 2, "section": "Maximum Ratings", "confidence": "high", "method": "table"}}],
  "thermal_resistance": {
    "rtheta_ja": [{"min": null, "typ": 111, "max": null, "unit": "K/W", "condition": "Min pad", "notes": null,
                   "evidence": {"page": 2, "section": "Thermal Characteristics", "confidence": "high", "method": "table"}}],
    "rtheta_jc": null,
    "rtheta_jl": [{"min": null, "typ": 12, "max": null, "unit": "K/W", "condition": "Min pad", "notes": null,
                   "evidence": {"page": 2, "section": "Thermal Characteristics", "confidence": "high", "method": "table"}}]
  },
  "package": {
    "code": "SMC", "pin_count": 2, "pitch_mm": null,
    "body_mm": {"length": 5.9, "width": 6.875, "height": 2.28},
    "thermal_pad": false,
    "evidence": {"page": 5, "section": "Package Dimensions", "confidence": "high", "method": "table"}
  },
  "marking_code": "B540",
  "polarity_marking_convention": "polarity band on plastic body indicates cathode",
  "trr": null, "cd": null, "vz": null, "breakdown_voltage": null, "power_dissipation": null,
  "ir": [{"min": null, "typ": null, "max": 3e-4, "unit": "A", "condition": "Rated DC voltage, TC=25°C", "notes": null,
          "evidence": {"page": 2, "section": "Electrical Characteristics", "confidence": "high", "method": "table"}}]
}
```
