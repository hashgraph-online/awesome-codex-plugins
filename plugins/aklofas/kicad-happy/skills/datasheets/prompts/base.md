# Datasheet Base Extractor Subagent

You are extracting the **base block** (package, thermal, ESD, absolute maximums, recommended operating conditions, compliance, moisture sensitivity) from an electronics component datasheet PDF.

## Task

Read `{{PDF_PATH}}` (focus pages: `{{PAGES}}`). Target MPN: **`{{MPN}}`**.

Produce a single JSON object matching this schema: `{{SCHEMA_PATH}}`.

**You do not extract pinout** — that's a separate task. Emit `"pinout": []`; the schema requires the key and the merger fills it from the pinout task.

## Field guide

- `package`: object with `code` (required string, e.g. "TO-263-5", "QFN-32"), `pin_count`, `pitch_mm`, `body_mm` (`{length, width, height}` in mm), `thermal_pad` (bool), and an `evidence` block (`{page, section, confidence, method}`).
- `thermal`: object keyed by parameter name (`theta_ja`, `theta_jc`, `psi_jt`, `psi_jb`, ...). Each value is a list of `SpecValue` objects (`min`, `typ`, `max`, `unit`, `condition`, `notes`, `evidence`).
- `absolute_max`: object keyed by parameter name (e.g. `VIN_max`, `TJ_max`, `Tstg`, `Vesd_HBM`). Each value is a list of SpecValue.
- `recommended_operating`: object keyed by parameter name (e.g. `VIN`, `TA`, `IL`). Each value is a list of SpecValue.
- `esd`: object keyed by ESD model (`HBM`, `CDM`, `MM`). Each value is a list of SpecValue (`typ` voltage in V).
- `moisture_sensitivity`: object `{msl, peak_reflow_c, evidence}` — `msl` is the JEDEC level as an integer 1–6, `peak_reflow_c` a number in °C. Null when the datasheet gives no MSL.
- `compliance`: array of objects `{mark, rating, evidence}` (e.g. `{"mark": "AEC-Q100", "rating": "Grade 1"}`); `rating` and `evidence` may be null. Empty array when none.
- `pin_relationships`: emit `[]`. Cross-pin conditions stated in prose (e.g. "EN must be ≥ 1.4 V referenced to VIN") belong to the pinout task, which records them in the pin's `notes`.

## Hard rules

1. **Canonical SI units everywhere.** Voltage in `V`, current in `A`, resistance in `Ω`, capacitance in `F` (NOT µF — store 470 µF as `4.7e-4` with unit `F`), inductance in `H`, frequency in `Hz`, temperature in `°C`, time in `s`, charge in `C`, power in `W`. Thermal resistance in `°C/W`.
2. **Every numeric SpecValue requires an `evidence` block** with `page` (PDF page where the value was read), `section` (textual section name from the PDF), `confidence` (`high` for table values, `medium` for prose, `low` for ambiguous/inferred), and `method` (one of `table`, `prose`, `curve`, `calculated`, `derived`). Use `curve` for values read off a graph, `calculated` for values resolved from a symbolic expression, `derived` for values inferred from other facts.
3. **OMIT fields you cannot locate** rather than guessing. Required: `family` (string), `package` (with `code`), `absolute_max`, `recommended_operating` (objects, `{}` when the datasheet lists none) and `pinout` (`[]` here). Everything else may be omitted; `compliance` and `pin_relationships` are arrays (`[]` when empty, never null), and the other optional fields may be null. An empty value is much better than a hallucinated one.
4. **For family PDFs**, extract values applicable to `{{MPN}}`. If a value is family-wide (e.g., absolute max VIN), state it. If it is variant-specific, state the variant value. Use `notes` field to call out variant-specific spec.
5. **No pinout data here** (`"pinout": []`). The pinout subagent runs separately.

## Output format

Return only the JSON object — no surrounding prose, no Markdown code fences. Output must validate against `{{SCHEMA_PATH}}`.

Example (abbreviated; `recommended_operating` is filled the same way as `absolute_max`):

```json
{
  "family": "step-down switching regulator",
  "package": {
    "code": "TO-263-5",
    "pin_count": 5,
    "thermal_pad": true,
    "evidence": {"page": 1, "section": "Features", "confidence": "medium", "method": "prose"}
  },
  "thermal": {
    "theta_ja": [{"min": null, "typ": 50, "max": null, "unit": "°C/W",
                  "condition": "TO-263 mounted vertically, 1oz Cu, 1in² pour", "notes": null,
                  "evidence": {"page": 5, "section": "Thermal Information", "confidence": "high", "method": "table"}}]
  },
  "absolute_max": {
    "VIN_max": [{"max": 45, "unit": "V", "min": null, "typ": null, "condition": null, "notes": null,
                 "evidence": {"page": 5, "section": "Absolute Maximum Ratings", "confidence": "high", "method": "table"}}]
  },
  "recommended_operating": {},
  "moisture_sensitivity": {"msl": 3, "peak_reflow_c": 260},
  "compliance": [{"mark": "RoHS", "rating": null}],
  "pinout": []
}
```
