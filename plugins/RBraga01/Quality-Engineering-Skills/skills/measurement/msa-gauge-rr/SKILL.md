---
name: msa-gauge-rr
description: >-
  Measurement System Analysis (MSA) and Gauge Repeatability & Reproducibility (Gauge R&R) — plan,
  execute, and interpret an MSA study for variable or attribute measurement systems. Use when
  qualifying a gauge for a new part, validating a measurement system before PPAP, interpreting
  Gauge R&R results, or auditing MSA studies for adequacy. Covers AIAG MSA 4th edition.
license: MIT
metadata:
  author: RBraga01
  version: "1.1"
  iso-9001: "7.1.5"
  iatf-16949: "7.1.5.1, 7.1.5.2"
  aiag-reference: "AIAG MSA 4th Edition"
  domain: quality-engineering
  subdomain: measurement
  industries: automotive,electronics,aerospace,medical,general
  status: approved
  created: "2026-06-06"
  last_updated: "2026-06-06"
  updated_by: migmcc
  reviewed_by: RBraga01
  standard_edition: "AIAG MSA 4th Edition (2010)"
---

# Measurement System Analysis (MSA) / Gauge R&R

## When to use

Use this skill when:
- Qualifying a measurement system for a new part or process (PPAP requirement)
- Interpreting Gauge R&R results — is this gauge acceptable?
- Auditing a supplier's MSA study for correctness and adequacy
- Selecting the right study type for a given measurement situation
- Investigating a quality problem where measurement error may be a factor
- Responding to a customer request for MSA data on a specific characteristic

## Prerequisites

- The characteristic to be measured (product or process)
- The gauge or measurement system to be studied
- Production parts spanning the expected process variation (10 parts minimum)
- At least 2 trained appraisers who normally perform the measurement
- The specification (tolerance) for the characteristic

## Workflow

### Step 1 — Select the MSA study type

| Study type | When to use |
|-----------|-------------|
| **Gauge R&R (crossed)** | Variable data, 2–3 appraisers, each measures all parts (most common) |
| **Gauge R&R (nested)** | Variable data, parts are destroyed during measurement (e.g., tensile test) |
| **Attribute MSA** | Pass/fail, go/no-go, visual inspection — data is not a number |
| **Bias study** | Accuracy of a single gauge vs. a reference standard |
| **Linearity study** | Whether gauge accuracy is consistent across its measurement range |
| **Stability study** | Whether gauge accuracy drifts over time |

For PPAP: Crossed Gauge R&R is required for all variable gauges on special characteristics.

---

### Step 2 — Crossed Gauge R&R study procedure

**Setup:**
- Minimum **10 parts** selected to represent the full process variation range (not cherry-picked from centre of tolerance)
- Minimum **2 appraisers** (3 preferred)
- Minimum **2 trials** per appraiser per part (3 preferred)
- Parts randomly numbered and labelled — appraisers must not see each other's measurements
- Measurement conditions must match normal production conditions

**Standard study design:**
- 10 parts × 3 appraisers × 2 trials = 60 measurements
- 10 parts × 2 appraisers × 3 trials = 60 measurements

**Execution:**
1. Appraiser A measures all 10 parts in random order — record results
2. Appraiser B measures all 10 parts in random order — record results
3. Appraiser C measures all 10 parts in random order — record results
4. Repeat the cycle for trial 2 (and trial 3 if applicable)
5. Appraisers must not see their own previous results or other appraisers' results during the study

**Do NOT:**
- Allow appraisers to adjust the gauge between trials
- Use parts that are all near the nominal value (no spread)
- Record only one trial (single measurement per appraiser per part is insufficient)

---

### Step 3 — Interpret the results

#### %GRR (Gauge R&R as % of Total Variation or % of Tolerance)

| %GRR | Interpretation | Decision |
|------|---------------|---------|
| < 10% | Excellent | ✅ Gauge accepted |
| 10% – 30% | Marginal | ⚠️ May be acceptable based on application — requires engineering review and customer approval |
| > 30% | Unacceptable | ❌ Gauge not suitable — investigate and improve before use in production |

**Two calculation methods:**
- **% of Study Variation (% of TV):** GRR / Total Variation × 100 — preferred when process is in control
- **% of Tolerance:** GRR / Tolerance × 100 — use when process capability is unknown or for attribute gauging

For PPAP, %GRR < 30% (tolerance method) is the typical customer acceptance criterion. <10% is the target.

#### Number of Distinct Categories (ndc)

ndc = 1.41 × (Part Variation / GRR)

| ndc | Interpretation |
|-----|---------------|
| ≥ 5 | ✅ Gauge can distinguish adequate number of categories |
| 3 – 4 | ⚠️ Gauge can be used for go/no-go decisions only |
| 1 – 2 | ❌ Gauge cannot distinguish parts — unacceptable |

ndc ≥ 5 is required for measurement systems used on special characteristics.

#### Repeatability vs. Reproducibility

| Component | Description | Common cause |
|-----------|-------------|-------------|
| **EV (Equipment Variation / Repeatability)** | Variation when same appraiser measures same part multiple times | Gauge imprecision, worn parts, environment |
| **AV (Appraiser Variation / Reproducibility)** | Variation between different appraisers measuring the same part | Training inconsistency, measurement technique, gauge setup |

If EV > AV: investigate gauge (calibration, maintenance, resolution)
If AV > EV: investigate training, measurement procedure, gauge fixture/setup

#### When %GRR > 30% — improving the measurement system

A result >30% means the gauge is not suitable for production use. Do not proceed to PPAP — investigate and retest. Common root causes and actions:

| Root cause (high EV) | Action |
|---------------------|--------|
| Gauge resolution too coarse | Replace with a gauge of finer resolution (rule: resolution ≤ 10% of tolerance) |
| Gauge worn or damaged | Inspect, recalibrate, or replace the gauge |
| Environmental interference (vibration, temperature) | Move measurement to a stable environment; add fixture if needed |
| Inconsistent part fixturing | Design a repeatable fixture or measurement aid |

| Root cause (high AV) | Action |
|---------------------|--------|
| Measurement technique varies by appraiser | Develop a standardised measurement instruction (WI with photos/video) |
| Gauge difficult to read or position | Redesign fixture; add a datum locator; use a self-positioning gauge |
| Training gap | Retrain all appraisers using the standardised measurement WI; repeat the study |

After implementing improvements: re-run the full study. Do not accept a %GRR > 30% result with a customer waiver unless the characteristic is non-critical and the customer explicitly agrees in writing.

---

### Step 4 — Attribute MSA (pass/fail gauges)

For go/no-go gauges, visual inspection, and any pass/fail decision:

**Expanded attribute study (recommended for PPAP):**
- 50 parts spanning the full range (include parts near the accept/reject boundary)
- 3 appraisers × 3 trials per part = 450 measurements
- Calculate % agreement (within appraiser and between appraisers)
- Calculate kappa statistic (Cohen's kappa ≥ 0.9 is acceptable)

**Short method (minimum acceptable):**
- 20 parts × 2 appraisers × 2 trials
- 90% agreement within and between appraisers required
- Include borderline parts near the specification limit

---

### Step 5 — Audit an existing MSA study

When reviewing a supplier's or internal MSA, check:

- [ ] Parts selected represent the full process variation range (not all near nominal)
- [ ] Minimum 10 parts, 2 appraisers, 2 trials confirmed
- [ ] Appraisers did not see each other's or their own previous results
- [ ] %GRR result stated clearly (tolerance method or study variation method — which one?)
- [ ] ndc ≥ 5 for all special characteristics
- [ ] EV vs. AV breakdown analysed and interpreted
- [ ] %GRR < 30% (conditional: <10% preferred)
- [ ] For attribute gauges: kappa statistic calculated
- [ ] Study performed in production conditions (not in metrology lab if production measurement is on the line)
- [ ] Gauge calibration certificate current at time of study

---

## Validation criteria

An MSA study is acceptable for PPAP when:
- %GRR < 30% (tolerance method) — <10% preferred
- ndc ≥ 5
- Study conducted with production appraisers using production gauges in production conditions
- Parts selected from the full process variation range
- Results documented with part numbers, appraiser IDs, gauge ID, and calibration reference

## Common mistakes

- Parts selected near the nominal value only — artificially inflates ndc and understates GRR
- Appraiser A re-measures all parts immediately — not the same as separate trials (must separate in time)
- Using metrology lab gauges for an MSA of a production line gauge — study must use the same gauge in the same conditions
- %GRR > 30% submitted in PPAP without explanation or customer waiver
- Gauge calibration expired at time of MSA study — study is invalid
- ndc < 5 on a special characteristic — automatic PPAP finding in IATF audits
- Attribute MSA with only 2 appraisers and no borderline parts — study has no discriminating power

## Output Format

At the start of each use, ask the user:

> "How would you like to receive the output?
> **A** — Structured Markdown (formatted tables and sections, ready to copy)
> **B** — Plain tables (simplified structure for Excel or Word)
> **C** — Narrative report (flowing text for a formal document or email)
>
> Default: A."

Adapt all output sections to the chosen format. If the platform or session context already defines a format preference, skip this question.

## Changelog

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-06 | @RBraga01 | Initial release |
| 1.1 | 2026-06-06 | @migmcc | Added improvement guidance for %GRR > 30% — root cause table for high EV and high AV with corrective actions |
