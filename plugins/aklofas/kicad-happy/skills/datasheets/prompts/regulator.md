# Datasheet Regulator Extractor Subagent

You are extracting the **regulator category extension** (topology, voltages, currents, frequencies, application capacitor/inductor recommendations, stability conditions) from an electronics component datasheet PDF.

## Task

Read `{{PDF_PATH}}` (focus pages: `{{PAGES}}`). Target MPN: **`{{MPN}}`**.

Produce a single JSON object matching this schema: `{{SCHEMA_PATH}}`.

## Field guide

- `topology`: enum. Choose the single closest match: `ldo` (linear), `buck` (step-down switcher), `boost` (step-up), `buck_boost`, `sepic`, `flyback`, `charge_pump`, `isolated`. The cover/Features section usually announces the topology.
- `vin_range`, `vout_range`: SpecValue lists (`min`, `max`, `unit: "V"`).
- `iout_max`: SpecValue list (`max`, `unit: "A"`, `condition` may carry temp/heatsinking note).
- `reference_voltage`: SpecValue list (adjustable parts only — e.g. LM2596-ADJ has 1.23V typ; fixed parts use null).
- `feedback_pin`, `compensation_pin`, `enable_pin`, `power_good_pin`: pin number strings matching `base.pinout[].numbers` exactly. Null when N/A.
- `cin_min`, `cout_min`: SpecValue list (`min`, `unit: "F"` — capacitance in Farads, NOT µF). The application section recommends these.
- `inductor_range`: SpecValue list (`min`, `max`, `unit: "H"`) for switchers.
- `switching_freq`: SpecValue list (`typ`, `unit: "Hz"`) for switchers; null for LDOs/charge pumps that aren't fixed-frequency.
- `dropout`: SpecValue list (`typ`, `max`, `unit: "V"`) for LDOs only; null for switchers.
- `psrr`, `line_regulation`, `load_regulation`: SpecValue lists; populate when called out.
- `stability_conditions`: object with `cap_types_allowed` (array of strings: `ceramic`, `tantalum`, `polymer`, `electrolytic`), `esr_range` (SpecValue list, `unit: "Ω"`), `notes`, `evidence`. Null when datasheet does not specify.
- `sequencing`: pre-defined sequencing requirements (multi-rail PMICs); null for single-output regulators.

## Hard rules

1. **Canonical SI units.** Capacitance in F (NOT µF — store 470µF as `4.7e-4` with `unit: "F"`). Inductance in H. Frequency in Hz. Voltage in V. Current in A. Resistance in Ω. The verifier rejects µF/nF/pF strings.
2. **Pin references must use exact pin numbers from the pinout extraction.** When the regulator extractor runs in parallel with pinout, infer pin numbers from the datasheet's pin description block (which is on the same pages you have access to). If a referenced pin isn't on your pages, use the pin name in `notes` and leave the pin field null.
3. **Family PDF disambiguation.** For LM2596-ADJ specifically: most fields are family-wide. The `vout_range` is variant-specific (-ADJ has wide adjustable range; fixed variants have a single nominal Vout). Use the -ADJ row in the ordering info table.
4. **Every SpecValue requires `evidence`** with `page`, `section`, `confidence`, `method`.
5. **OMIT fields you cannot find** with null. Do not guess. A missing `inductor_range` is much better than a hallucinated one.

## Output format

Return only the JSON object. No prose, no fences. Output must validate against `{{SCHEMA_PATH}}`.

Example (LM2596-ADJ):

```json
{
  "topology": "buck",
  "vin_range": [{"min": 4.5, "max": 40, "unit": "V", "typ": null, "condition": null, "notes": null,
                 "evidence": {"page": 5, "section": "Recommended Operating Conditions", "confidence": "high", "method": "table"}}],
  "vout_range": [{"min": 1.23, "max": 37, "unit": "V", "typ": null, "condition": null, "notes": "Adjustable via FB divider",
                  "evidence": {"page": 1, "section": "Features", "confidence": "medium", "method": "prose"}}],
  "iout_max": [{"max": 3, "unit": "A", "min": null, "typ": null, "condition": "with adequate heatsinking", "notes": null,
                "evidence": {"page": 1, "section": "Features", "confidence": "medium", "method": "prose"}}],
  "reference_voltage": [{"min": 1.18, "typ": 1.23, "max": 1.28, "unit": "V", "condition": null, "notes": null,
                         "evidence": {"page": 5, "section": "Electrical Characteristics", "confidence": "high", "method": "table"}}],
  "switching_freq": [{"typ": 150000, "unit": "Hz", "min": null, "max": null, "condition": null, "notes": null,
                      "evidence": {"page": 5, "section": "Electrical Characteristics", "confidence": "high", "method": "table"}}],
  "feedback_pin": "4",
  "enable_pin": "5"
}
```
