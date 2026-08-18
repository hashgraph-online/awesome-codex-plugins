---
name: dvp-template
type: reference
parent_skill: dvp-test-plan
author: RBraga01
version: "1.0"
status: approved
created: "2026-06-06"
last_updated: "2026-06-06"
updated_by: migmcc
reviewed_by: RBraga01
license: MIT
---

# DVP&R — Template and Test Reference

Blank DVP&R template with column instructions, test category reference, sample size guidance, pass/fail documentation requirements, and DFMEA linkage table.
Use alongside the [dvp-test-plan](../SKILL.md) skill.

> **Scope:** This document covers the blank DVP&R template structure, column-by-column instructions, a reference library of test categories and example standards, sample size requirements per category, pass/fail criteria documentation standards, and the DFMEA-to-DVP linkage methodology. For the step-by-step DVP build and audit workflow, see [dvp-test-plan SKILL.md](../SKILL.md).

---

## 1. DVP&R Template — Blank Structure

**Document header fields (above the table):**

```
Part Number:                          Rev:
Part Name / Description:
Programme / Vehicle / Platform:
Customer:
Design Engineer:                      Phone / Email:
Quality Engineer:                     Phone / Email:
DVP&R Number:                         Rev:
Date Issued:                          Date Updated:
DFMEA Reference:                      DFMEA Rev:
Approved by (Engineering):            Date:
Approved by (Quality):                Date:
```

**Column structure — one row per test:**

| Col # | Column Name | Brief instruction |
|-------|------------|-------------------|
| 1 | Test Number | Sequential ID (DVP-001, DVP-002, ...) |
| 2 | DFMEA Reference | Failure mode number(s) this test validates |
| 3 | Test Name / Description | Full, specific test name with standard and duration |
| 4 | Test Specification / Method | Standard number + revision (e.g., ASTM B117-19) |
| 5 | Pass / Fail Criteria | Specific, measurable acceptance threshold |
| 6 | Sample Size | Number of parts to be tested |
| 7 | Who Performs | Internal / External lab name |
| 8 | Phase | P = Prototype / PL = Pre-launch / PR = Production |
| 9 | Planned Date | Scheduled completion date |
| 10 | Actual Date | Date test was completed (filled during execution) |
| 11 | Result | Pass / Fail / In Progress / Waived |
| 12 | Report Reference | Lab report number or document reference |
| 13 | Comments / Notes | Failures, deviations, re-test references |

---

## 2. Column-by-Column Instructions

### Column 1 — Test Number

Sequential reference number, unique within the DVP. Format: `DVP-001`, `DVP-002`, etc. Re-tests after failure add a suffix: `DVP-012-R1` (first re-test), `DVP-012-R2` (second re-test). Never delete a failed test row — failure history is a design record.

**Common mistakes:**
- Renumbering after adding rows mid-programme — creates gaps in the audit trail
- Deleting rows where tests failed and re-tests passed — conceals design history; the original Fail result must remain visible

---

### Column 2 — DFMEA Reference

The failure mode ID(s) from the DFMEA that this test is designed to validate. Enter the exact DFMEA row reference (e.g., "FM-014", "Function: Seal Housing / Failure Mode: Crack under thermal cycling"). If one test covers multiple failure modes, list all references.

**Common mistakes:**
- "See DFMEA" without a specific row reference — traceability cannot be confirmed
- A test row with no DFMEA reference — every test must validate something; if there is no DFMEA failure mode, the test may be redundant or the DFMEA is incomplete
- DFMEA updated after DVP was issued — DVP not updated to capture new H-AP failure modes

---

### Column 3 — Test Name / Description

The full, specific name of the test. Be precise: not "durability test" but "Thermal Shock Test -40°C to +125°C, 500 cycles, 30 min dwell per IEC 60068-2-14". Not "salt spray" but "Salt Spray Corrosion Test — 240 hours per ASTM B117".

The name must be specific enough that a different engineer unfamiliar with the programme could identify and procure the test without calling anyone.

**Common mistakes:**
- Generic names ("environmental test", "performance test") that require interpretation
- Test name that omits duration, number of cycles, or key parameters
- Name inconsistent with the test standard listed in Column 4

---

### Column 4 — Test Specification / Method

The specific standard, revision, and any applicable test profile. Format: `[Standard body] [Number]-[Year], [Clause if specific]`.

Examples:
- `ASTM B117-19` (Salt Spray)
- `IEC 60068-2-1:2007, Test Ab (Cold Storage)` (Cold)
- `ISO 16750-3:2023, Table 2 (Road Surface Load)` (Vibration)
- `SAE J2530:2013` (Road Wheel Fatigue)
- Customer spec: `Ford ES-XW7T-1A278-AC, Rev 3` (OEM spec)

If using an internal test method without an external standard: reference the internal test specification number, revision, and the validation data that established the method. Internal-only tests on safety/regulatory characteristics are not acceptable.

**Common mistakes:**
- Omitting the revision year — standards change; the revision must be the version in effect at the time of testing
- Using a superseded standard version — check IHS, ASTM, ISO websites for current edition
- Referencing a customer spec number without revision — the spec may have changed between programme launch and test execution

---

### Column 5 — Pass / Fail Criteria

The specific, measurable acceptance threshold. Every criterion must be unambiguous — a different engineer should be able to make the same Pass/Fail call from the lab report without consulting the DVP author.

**Good examples:**
- "No corrosion (red rust) on functional surfaces after 240h; white corrosion on non-functional surfaces acceptable"
- "Burst pressure ≥ 180 bar; no leakage at 120 bar steady-state for 5 minutes"
- "Maximum deformation ≤ 2.0 mm measured at load point A after 10,000 cycles"
- "All dimensions within ±0.05 mm of nominal per drawing revision C, all 12 critical dims"

**Common mistakes:**
- "Meets specification" without stating what the specification says — not auditable
- "No failure" without defining what constitutes a failure
- "Acceptable appearance" without a reference standard or measurable limit
- Criteria that reference a document not included in the PPAP package

---

### Column 6 — Sample Size

The number of parts to be tested. Must be a specific number, not "TBD" or "as available". See Section 4 for sample size requirements by test category.

**Common mistakes:**
- n = 1 for destructive, durability, or reliability tests — single sample cannot establish statistical confidence
- Sample size selected for convenience ("we only have 3 parts") without evaluating whether 3 is sufficient
- No differentiation between samples for concurrent tests vs. sequential tests on the same parts

---

### Column 7 — Who Performs

Identify the performing laboratory by name and type:
- **Internal:** "[Company name] Internal Lab — [facility location]"
- **External:** "[Lab name], [City, Country], ISO/IEC 17025 cert # [number]"
- **Customer lab:** "Customer lab — [OEM facility]"

For regulatory / safety tests: must be an external accredited laboratory. ISO/IEC 17025 accreditation with scope covering the specific test method is required.

**Common mistakes:**
- "Internal / External TBD" — the performer must be committed in the DVP, not decided later
- Internal lab assigned to safety or regulatory tests that require external accreditation
- Lab name recorded but no accreditation reference — cannot verify the lab's competence

---

### Column 8 — Phase

| Code | Phase | When |
|------|-------|------|
| P | Prototype | Tests on design concept or prototype tooled parts — typically pre-production handmade or soft-tool parts |
| PL | Pre-launch | Tests on hard-tooled production-intent parts; all safety/regulatory must be PL or PR |
| PR | Production | Tests requiring production parts (OEM specs often mandate PR for certification) |

A test may appear in multiple phases (e.g., dimensional verification at P, PL, and PR). Each phase gets its own row or sub-row with its own result.

---

### Column 9 — Planned Date

The target completion date for the test, consistent with the programme timing plan. Must be before the PPAP submission date. For multi-phase tests, enter the planned date for this phase's execution.

---

### Column 10 — Actual Date

Filled during or after test execution. If a test is still "In Progress" at PPAP submission, it is an open item and the PPAP cannot be approved unless the customer grants a deviation with a committed completion date.

---

### Column 11 — Result

| Status | Meaning |
|--------|---------|
| Pass | Test completed; all pass/fail criteria met; lab report available |
| Fail | Test completed; one or more criteria not met; DFMEA action opened |
| In Progress | Test started but not complete |
| Not Started | Test not yet begun (should not exist at PPAP submission) |
| Waived | Customer has formally waived this test with written approval referencing the DVP row |
| Re-test — Pass | Re-test after corrective action; original Fail row retained |

---

### Column 12 — Report Reference

The lab report number, document number, or unique identifier that allows the test result to be retrieved and verified. For external labs: the lab's own report number. For internal tests: the internal document number per the supplier's quality records system.

**Common mistakes:**
- "See attached" without a document number — the DVP must be self-sufficient; attachments are supporting evidence, not the reference
- No report issued for internal tests — even internal tests must generate a traceable record

---

### Column 13 — Comments / Notes

Used for: failure descriptions, deviation references, re-test cross-references, notes on partial passes, and any conditions that affect the validity of the result (e.g., "sample 3 damaged in transit — result based on samples 1, 2, 4, 5"). If a Waiver was granted, reference the waiver document number here.

---

## 3. Test Category Reference

### Category A — Functional / Performance Tests

Verifies the product performs its intended design function under normal operating conditions.

| Test Type | Example Standards | Typical Parameter |
|-----------|-------------------|-------------------|
| Tensile / Pull strength | ISO 6892-1, ASTM E8/E8M | Maximum load, elongation at break |
| Compressive strength | ISO 604, ASTM D695 | Load at yield / at failure |
| Burst / proof pressure | SAE J1019, OEM specs | Pressure at burst; no leakage at proof pressure |
| Torque / breakaway torque | AIAG MSA reference, OEM specs | Minimum breakaway, installation torque |
| Electrical resistance / continuity | IEC 60512, OEM CSR | Resistance limits (mΩ or Ω range) |
| Flow rate / pressure drop | ISO 4021, OEM specs | Flow at specified pressure delta |
| Sealing / leak test | SAE J771, ISO 10110 | Maximum leak rate (mbar·l/s, cc/min) |
| Insertion / extraction force | IEC 60512-13, OEM specs | Min/max force within defined stroke |
| Load-deflection / spring rate | ASTM D1895, OEM specs | Deflection at specified load |

**Sample size guidance:** n ≥ 3 for destructive tests; n ≥ 5 for non-destructive functional tests where variability exists.

---

### Category B — Environmental Tests

Simulates the operating environment over the product's design life. Duration and severity levels must represent the design life or a validated accelerated equivalent.

| Test Type | Example Standards | Key Parameters |
|-----------|-------------------|----------------|
| Salt spray / corrosion | ASTM B117-19, ISO 9227 | Duration (hours); neutral salt spray (NSS) vs. acetic acid (AASS) |
| Thermal shock | IEC 60068-2-14, SAE J2236 | Temperature range; number of cycles; dwell time per extreme |
| Thermal cycling (slow ramp) | IEC 60068-2-14 Test Na; JEDEC JESD22-A104 | Ramp rate (°C/min); cycles; temperature extremes |
| Temperature soak (high) | IEC 60068-2-2, MIL-STD-810H Method 501 | Temperature; duration; loaded or unloaded |
| Temperature soak (low) | IEC 60068-2-1, MIL-STD-810H Method 502 | Temperature; duration |
| Humidity / Damp heat | IEC 60068-2-78, ISO 16750-4 | Temperature + RH %; duration (h) |
| Humidity cycling / condensation | IEC 60068-2-30; ASTM D2247 | Cycles; temperature/humidity profile |
| UV / xenon weathering | SAE J2527, ISO 4892-2 | Irradiance (W/m²); duration (kJ/m²); acceptance (ΔE colour shift, crack rating) |
| Fluid immersion / resistance | SAE J1717, OEM specs | Fluid types; concentration; immersion duration; visual + functional post-check |
| Pressure / altitude | IEC 60068-2-13, MIL-STD-810H Method 500 | Altitude (m); duration |

**Sample size guidance:** n ≥ 3 minimum; n ≥ 5 preferred for qualification. For multi-condition matrices (multiple fluid types or multiple temperature levels), n = 3 per condition.

---

### Category C — Safety / Regulatory Tests

Mandated by law, homologation, or OEM CSR. Must be performed by an externally accredited lab. Results must accompany the PPAP package. Failure in this category prevents PPAP approval without a customer and regulatory authority deviation.

| Regulation / Standard | Scope | Typical Parts |
|-----------------------|-------|---------------|
| ECE R10 (UN Regulation 10) | Electromagnetic Compatibility — vehicles | All electrical / electronic components |
| FMVSS 302 | Flammability of interior materials | Interior plastic, foam, fabric |
| FMVSS 205 | Glazing materials | Window glass |
| ECE R94 / R95 | Frontal / lateral crash | Structural and passive safety components |
| ISO 26262 | Functional safety — road vehicles (ASIL level) | Safety-critical electronics / SW |
| REACH (EC No 1907/2006) | Chemical substance restrictions | All parts (substance declaration) |
| RoHS (2011/65/EU) | Restriction of hazardous substances | Electrical and electronic equipment |
| ELV Directive (2000/53/EC) | End-of-life vehicle — prohibited materials | All automotive parts |
| IATF 16949 §8.3.3.3 | Special characteristics — safety validation | All SC-classified characteristics |
| ISO 11452 / CISPR 25 | EMC — radiated / conducted (component level) | Electronics, sensors, actuators |

**Sample size guidance:** Per the specific regulation or standard — typically n = 3 per test configuration; some regulations define minimum sample quantities explicitly. Never waive regulatory tests without written authority from the relevant regulatory body in addition to customer sign-off.

---

### Category D — Dimensional / Material Tests

Verification that design dimensions and material properties are realised in the production part.

| Test Type | Example Standards | Key Parameters |
|-----------|-------------------|----------------|
| CMM dimensional measurement | ASME Y14.5-2018; ISO 1101 | All drawing characteristics; GD&T datums |
| 3D scanning (full-field) | VDI/VDE 2634 | Point cloud vs. nominal CAD |
| Surface roughness (Ra/Rz) | ISO 4287, ASME B46.1 | Ra or Rz value; measurement direction |
| Hardness (HRC/HRB/HV/HB) | ASTM E18, ISO 6507 | Target hardness grade; number of test points |
| Tensile strength / yield strength | ISO 6892-1, ASTM E8 | UTS (MPa), Yield (MPa), Elongation (%) |
| Chemical composition (spectrometry) | ASTM E415, ISO 14284 | Alloy grade per material specification |
| Coating thickness | ISO 2178 (magnetic), ISO 1463 (cross-section) | Min/max coating thickness (µm) |
| Weld quality (visual + macro) | ISO 5817, AWS D1.1 | Defect class per standard; macro section for penetration |
| Porosity / void content | ASTM E2375, ASTM B276 | Acceptable porosity level per specification |

**Sample size guidance:** For dimensional results supporting PPAP Element 9: minimum 5 parts per cavity/spindle. For material tests: minimum 3 specimens per material lot.

---

### Category E — Durability / Reliability Tests

Establishes that the product meets its reliability target (e.g., B10 life, design life in cycles or hours) under representative or accelerated conditions.

| Test Type | Example Standards | Key Parameters |
|-----------|-------------------|----------------|
| Fatigue / cyclic load | SAE J1099, ASTM E466 | Number of cycles; load amplitude; R-ratio; S-N curve |
| Vibration — random | ISO 16750-3, IEC 60068-2-64, MIL-STD-810H Method 514 | PSD profile (g²/Hz); duration per axis; resonance dwell |
| Vibration — sine sweep | IEC 60068-2-6, ISO 16750-3 | Frequency range; amplitude; sweep rate; resonance dwell |
| Mechanical shock | IEC 60068-2-27, MIL-STD-810H Method 516 | Peak acceleration (g); pulse duration (ms); number of shocks; waveform |
| Wear / abrasion | ASTM G65, ISO 4649, Taber abraser | Abrasion cycles; material loss (mg or mm) |
| Contact fatigue / fretting | ASTM E1012, OEM specs | Cycles; contact pressure; slip amplitude |
| Seal / gasket compression set | ISO 815, ASTM D395 | Compression set % after defined temp/time |
| Actuator / switch endurance | IEC 60512-9, OEM CSR | Number of actuations; contact resistance before/after |
| Accelerated life test (ALT) | MIL-HDBK-217, Arrhenius model | Acceleration factor; field life correlation; B10 / MTTF claim |

**Accelerated test — field life correlation requirement:** When a test uses acceleration (elevated temperature, increased load amplitude, compressed cycles), the DVP must state the acceleration model used (Arrhenius, Coffin-Manson, Miner's rule, etc.), the acceleration factor (AF), and the field life equivalent. Example: "500 thermal shock cycles at ΔT = 165°C (Coffin-Manson β = 2.0) represents 15 years / 150,000 km equivalent."

**Sample size guidance:** See Section 4.

---

## 4. Sample Size Requirements by Test Category

| Category | Test Type | Minimum n | Rationale |
|----------|-----------|-----------|-----------|
| A — Functional | Non-destructive (measured, then parts are reusable) | 5 | Captures part-to-part variability |
| A — Functional | Destructive (part consumed by the test) | 3 minimum; 5 preferred | Cost-constrained minimum; 3 establishes a range |
| B — Environmental | Non-destructive (parts measured pre/post) | 3 minimum; 5 preferred | Pre/post comparison; detects variability in degradation |
| B — Environmental | Destructive (dissected, cross-sectioned post-test) | 3 | Minimum for qualification |
| B — Environmental | Multi-condition matrix (e.g., 3 temperatures × 3 fluids) | 3 per cell | Each condition independently validated |
| C — Regulatory | Per regulation | As required by regulation | Refer to the specific standard — cannot be reduced without regulatory authority approval |
| D — Dimensional | CMM / hand measurement (PPAP Element 9) | 5 per cavity / spindle | AIAG PPAP 4th ed requirement |
| D — Dimensional | Material properties (tensile, hardness, composition) | 3 specimens per lot | Lot-based — traceability must link specimens to the part lot |
| E — Durability | Fatigue / vibration / endurance | 3 minimum; 5 preferred for life claim | 3 establishes a distribution; B10 claim requires ≥ 5 for statistical confidence with Weibull analysis |
| E — Reliability | ALT (accelerated life test) with field life claim | 5 minimum (Weibull r = 2); 10 preferred | B10 life claim at 90% confidence level requires adequate n — use Weibull calculator to confirm |
| C — Regulatory / Safety | EMC, crash, homologation | Per regulation; typically 3 | Cannot deviate without regulatory authority; some regulations specify exact quantities |

**Statistical guidance for reliability claims:**
- B10 life at 90% confidence with Weibull shape parameter β = 2: minimum n = 5 — but only if the test duration is extended to ≈ 2.1× the B10 design life. Testing exactly to the B10 life with n = 5 does not achieve 90% confidence.
- B10 life at 90% confidence with β = 1 (exponential): minimum n = 12 — requires test duration ≈ 1.8× the B10 design life.
- For testing exactly to the B10 design life (no time extension): n ≥ 22 is required regardless of β, to achieve 90% confidence of ≥ 90% reliability. Use the formula n = ln(1−C) / ln(R) where C = 0.90 and R = 0.90.
- Use the AMSAA / Crow reliability growth tool or Weibull analysis software to calculate the exact test duration multiplier for your β and n combination before committing to a test plan.

---

## 5. Pass / Fail Criteria Documentation Requirements

The following elements must be present in every DVP pass/fail criterion. Absence of any element makes the criterion non-auditable and creates a PPAP risk.

| Requirement | Description | Example |
|-------------|-------------|---------|
| Measurable threshold | Numeric limit or defined attribute standard | "≥ 150 bar", "≤ 2.0 mm deflection", "Grade A per ISO 5817" |
| Reference | Standard, drawing, or spec that defines the criterion | "per ASTM B117-19", "per drawing rev C dim 14", "per Ford ES-spec DS-123 Rev 2" |
| Measurement point / location | Where on the part the measurement is taken | "at load point A (per test fixture drawing TF-002)", "on functional bore surface only" |
| Condition at measurement | When / how the measurement is taken relative to the test | "immediately after test end, within 1h", "at room temperature after 24h conditioning" |
| Disposition of acceptable boundary | How the boundary case is handled | "values equal to the limit are Pass", or "limit is exclusive — values equal to limit require engineering review" |

**Attribute criteria (visual / functional) additional requirements:**
- Reference to a visual standard (golden sample, limit sample, photograph with annotations, or published standard table)
- Defined viewing conditions if appearance is part of the criterion (lighting level, viewing distance, viewing angle)
- Training record for inspectors using the attribute standard (if an internal standard)

---

## 6. DVP to DFMEA Linkage Table

How to establish and verify the bi-directional link between each DVP test row and the DFMEA failure mode(s) it validates.

### Linkage Construction Rules

1. **Every H-AP failure mode must have at least one DVP test.** If a failure mode cannot be tested (analysis-only justification), document this in the DVP with the analytical method used and the engineer's sign-off — this is a conscious decision, not an omission.

2. **One test may cover multiple failure modes.** A thermal shock test validates failure modes related to thermal expansion, solder joint fatigue, material embrittlement, and seal degradation simultaneously — list all referenced DFMEA failure mode IDs in Column 2.

3. **Multiple tests may cover one failure mode.** A high-severity failure mode should be validated by more than one test approach (functional test + durability test) — belt and suspenders for high-AP items.

4. **The DFMEA detection control must match the DVP test method.** If the DFMEA says "validated by design analysis only" but the DVP has no test for that failure mode, the DFMEA detection rating (D) is unjustified.

### DFMEA Column to DVP Column Mapping

| DFMEA Column | DFMEA Content | Maps to DVP Column | DVP Usage |
|--------------|--------------|-------------------|-----------|
| Function | What the design element is supposed to do | Col 3 (partially) | Test name context — what the test is verifying the function against |
| Failure Mode | How the function fails | Col 2 — DFMEA Reference | The failure mode ID drives the DVP row existence |
| Failure Effect | What the customer/user experiences | Col 5 — Pass/Fail Criteria (indirectly) | The effect's severity determines the stringency of the criterion |
| Failure Cause | Root cause of the failure mode | Col 3, Col 4 — Test type and method | Test method is chosen to recreate or stress the failure cause mechanism |
| Severity (S) rating | S ≥ 9 | Col 7 — Who Performs | Safety effects (S ≥ 9) must use accredited external lab |
| Action Priority (AP) | H-AP, M-AP, L-AP | Col 6, Col 8 | H-AP: larger sample size; Phase PL or PR required (not P-only) |
| Current Detection Control | "DVP test [reference]" | Confirms test exists in DVP | If DFMEA says "validated by DVP" and the DVP row does not exist, DFMEA detection rating is unjustified |
| Recommended Action (completed) | New test added; test criteria tightened | New DVP row or updated Col 5 | Completed DFMEA actions that add or modify tests must be reflected in the DVP |

### Audit Cross-Reference Matrix (how to perform the linkage audit)

**Step 1:** Extract all H-AP failure modes from the DFMEA. List their IDs.

**Step 2:** For each H-AP failure mode ID, verify there is at least one DVP row with that ID in Column 2 and a non-blank result in Column 11.

**Step 3:** For each DVP row, verify the DFMEA failure mode ID in Column 2 exists in the DFMEA and is still current (not superseded by a DFMEA revision).

**Step 4:** Verify that DVP test specifications (Column 4) use the same standard revision referenced in the DFMEA notes or engineering specification.

**Step 5:** Verify that all DVP rows show "Pass" or "Waived (with reference)" — no "In Progress", "Not Started", or bare "Fail" rows at PPAP submission.

**Step 6:** Check DVP revision date against DFMEA revision date. If the DFMEA was updated after the DVP was issued, the DVP must reflect any new or modified failure modes — especially any new H-AP items added during a design review.
