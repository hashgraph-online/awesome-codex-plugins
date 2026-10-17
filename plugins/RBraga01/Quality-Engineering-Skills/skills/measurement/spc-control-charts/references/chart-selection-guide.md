---
name: chart-selection-guide
type: reference
parent_skill: spc-control-charts
author: RBraga01
version: "1.0"
status: approved
created: "2026-06-06"
last_updated: "2026-06-06"
updated_by: migmcc
reviewed_by: RBraga01
license: MIT
---

# SPC Chart Selection and Reference Guide

Constants tables, Western Electric rules, out-of-control response guidance, capability formulas, and short-run SPC notes for practitioner use.
Use alongside the [spc-control-charts](../SKILL.md) skill.

> **Scope:** This document covers chart selection logic, control limit constants, WE rules with zone diagram, OOC response mapping, capability formula reference, and short-run SPC approaches. For the step-by-step workflow (subgroup sizing, limit calculation procedure, audit checklist, and interpretation), see [spc-control-charts SKILL.md](../SKILL.md).

---

## 1. Chart Selection Decision Tree

```
START: What type of data do you have?
│
├─► VARIABLE (measured number: length, weight, force, temperature, voltage)
│   │
│   └─► What is your subgroup size?
│       │
│       ├─► n = 1 (one measurement per inspection point)
│       │   Reason: slow process, destructive test, batch process, one unit per cycle
│       │   → USE: I-MR Chart (Individuals & Moving Range)
│       │   Note: Normality assumption stronger here. Check for non-normal distribution
│       │         before interpreting. Consider transformations for skewed data.
│       │
│       ├─► n = 2 to 9
│       │   Reason: multiple units sampled per time period, typical manufacturing
│       │   → USE: X̄-R Chart (X-bar / Range)
│       │   Note: Most common chart in automotive. Range captures within-subgroup spread.
│       │
│       └─► n ≥ 10
│           Reason: large subgroup, precise spread estimate needed
│           → USE: X̄-S Chart (X-bar / Sigma)
│           Note: S chart is more efficient than R chart for large n.
│               S chart has higher sensitivity to spread changes.
│
└─► ATTRIBUTE (counted, classified, pass/fail)
    │
    └─► Is your subgroup size CONSTANT or VARIABLE?
        │
        ├─► CONSTANT subgroup size
        │   │
        │   └─► Are you tracking DEFECTIVES (non-conforming units) or DEFECTS (non-conformances per unit)?
        │       │
        │       ├─► DEFECTIVES (a unit is either good or bad)
        │       │   → USE: np-Chart (number of defective units)
        │       │   Formula: np̄ ± 3√(np̄(1−p̄))
        │       │
        │       └─► DEFECTS (multiple defects possible per unit)
        │           → USE: c-Chart (count of defects)
        │           Formula: c̄ ± 3√c̄
        │           Assumes Poisson distribution
        │
        └─► VARIABLE subgroup size
            │
            └─► Defectives or defects per unit?
                │
                ├─► DEFECTIVES
                │   → USE: p-Chart (proportion defective)
                │   Formula: p̄ ± 3√(p̄(1−p̄)/n)    [control limits vary with n]
                │
                └─► DEFECTS per unit
                    → USE: u-Chart (defects per unit)
                    Formula: ū ± 3√(ū/n)    [control limits vary with n]
```

### Quick Reference Table

| Chart | Data type | Subgroup size | Plotted statistic |
|-------|-----------|---------------|-------------------|
| X̄-R | Variable | 2–9 | Subgroup mean and range |
| X̄-S | Variable | ≥ 10 | Subgroup mean and standard deviation |
| I-MR | Variable | 1 | Individual value and moving range (n=2 span) |
| p | Attribute (defectives) | Variable | Proportion defective |
| np | Attribute (defectives) | Constant | Number of defectives |
| c | Attribute (defects) | Constant | Count of defects |
| u | Attribute (defects) | Variable | Defects per unit |

---

## 2. Control Limit Constants Table

### X̄-R Chart Constants

| n | A₂ | D₃ | D₄ | d₂ | d₃ |
|---|----|----|-----|-----|-----|
| 2 | 1.880 | 0 | 3.267 | 1.128 | 0.853 |
| 3 | 1.023 | 0 | 2.574 | 1.693 | 0.888 |
| 4 | 0.729 | 0 | 2.282 | 2.059 | 0.880 |
| 5 | 0.577 | 0 | 2.114 | 2.326 | 0.864 |
| 6 | 0.483 | 0 | 2.004 | 2.534 | 0.848 |
| 7 | 0.419 | 0.076 | 1.924 | 2.704 | 0.833 |
| 8 | 0.373 | 0.136 | 1.864 | 2.847 | 0.820 |
| 9 | 0.337 | 0.184 | 1.816 | 2.970 | 0.808 |
| 10 | 0.308 | 0.223 | 1.777 | 3.078 | 0.797 |

**Formulas:**
- UCL_X̄ = X̄̄ + A₂ × R̄
- LCL_X̄ = X̄̄ − A₂ × R̄
- UCL_R = D₄ × R̄
- LCL_R = D₃ × R̄  (= 0 for n ≤ 6)
- σ̂ = R̄ / d₂  (short-term standard deviation estimate for capability)

### X̄-S Chart Constants

| n | A₃ | B₃ | B₄ | c₄ |
|---|----|----|-----|-----|
| 5 | 1.427 | 0 | 2.089 | 0.9400 |
| 6 | 1.287 | 0.030 | 1.970 | 0.9515 |
| 7 | 1.182 | 0.118 | 1.882 | 0.9594 |
| 8 | 1.099 | 0.185 | 1.815 | 0.9650 |
| 9 | 1.032 | 0.239 | 1.761 | 0.9693 |
| 10 | 0.975 | 0.284 | 1.716 | 0.9727 |

**Formulas:**
- UCL_X̄ = X̄̄ + A₃ × S̄
- LCL_X̄ = X̄̄ − A₃ × S̄
- UCL_S = B₄ × S̄
- LCL_S = B₃ × S̄  (= 0 for n ≤ 5)
- σ̂ = S̄ / c₄

### I-MR Chart Constants (n = 2 for moving range span)

| Chart | Centre line | UCL | LCL |
|-------|------------|-----|-----|
| Individuals | X̄ (grand mean) | X̄ + 2.660 × MR̄ | X̄ − 2.660 × MR̄ |
| Moving Range | MR̄ | 3.267 × MR̄ | 0 |

Note: 2.660 = 3/d₂ for n=2. MR̄ = average of all two-point moving ranges.

---

## 3. Western Electric Rules — Zone Diagram and Reference

### Zone Definition

Control limits are at ±3σ from the centre line (X̄̄). Divide the chart into 6 equal zones:

```
                         ┌─── UCL (+3σ) ─────────────────────────────
                         │
    Zone A (above) ──────┤   +2σ ─────────────────────────────────────
                         │
    Zone B (above) ──────┤   +1σ ─────────────────────────────────────
                         │
    Zone C (above) ──────┤   Centre line (X̄̄) ────────────────────────
                         │
    Zone C (below) ──────┤   −1σ ─────────────────────────────────────
                         │
    Zone B (below) ──────┤   −2σ ─────────────────────────────────────
                         │
                         └─── LCL (−3σ) ─────────────────────────────
```

Zone A = between ±2σ and ±3σ (outer zone)
Zone B = between ±1σ and ±2σ (middle zone)
Zone C = between centre line and ±1σ (inner zone)

### All 8 Western Electric Rules

| Rule | Pattern | Zone / Threshold | Signal meaning |
|------|---------|-----------------|----------------|
| **1** | 1 point beyond control limit | Beyond ±3σ (Zone A or outside) | Acute large shift or special cause |
| **2** | 9 consecutive points same side of centre line | Any zone, same side | Mean has shifted — process level change |
| **3** | 6 consecutive points steadily increasing or decreasing | Any | Trend — tool wear, heating, drift, degradation |
| **4** | 14 consecutive points alternating up and down | Any | Over-adjustment (tampering) or two alternating input streams |
| **5** | 2 of 3 consecutive points in Zone A or beyond, same side | Outer third | Large mean shift signal (less than Rule 1 sensitivity) |
| **6** | 4 of 5 consecutive points in Zone B or beyond, same side | Outer two-thirds | Moderate mean shift, sustained |
| **7** | 15 consecutive points in Zone C (either side) | Inner third only | Stratification — data from two distributions being mixed |
| **8** | 8 consecutive points beyond Zone C (either side, no centre line crossings) | Both outer zones | Mixture — process producing from two populations |

### Implementation Guidance by Application

| Application level | Rules applied | Rationale |
|------------------|--------------|-----------|
| Minimum (IATF 16949 basic compliance) | Rules 1, 2, 3 | Catches major shifts, trends, sustained drift |
| Standard automotive | Rules 1–6 | Adequate for most special characteristics |
| Safety/critical characteristics | Rules 1–8 | Maximum sensitivity required |
| Short-run or low-volume | Rule 1 only | Insufficient data for pattern rules |

---

## 4. Out-of-Control Action Response Guide

When a rule is triggered, the response depends on which rule fired and the direction of deviation.

| Rule triggered | First question to ask | Typical root causes | Containment action |
|---------------|----------------------|--------------------|--------------------|
| Rule 1 — Point beyond UCL or LCL | What changed at or just before this point? | Tool breakage, fixture failure, wrong material lot, gauge error, single operator mistake | Place all output since last in-control point on hold. Verify with reference measurement. |
| Rule 2 — 9 points same side | When did the shift start? (identify the subgroup where the run began) | Material lot change, new operator, shift change, gradual fixture wear, process parameter drift | Screen output from run start point. Investigate the change event at that time. |
| Rule 3 — 6 points trending | What consumable or process input degrades over time? | Tool wear, lubricant depletion, insert wear, temperature rise, electrode erosion | Do not stop immediately — confirm trend continues. Check tool condition. Replace consumable if confirmed. |
| Rule 4 — Alternating | Is the chart mixing two different operators, machines, or material streams? | Two operators with different technique, two heads on same fixture, automatic re-centering after each cycle | Investigate subgrouping strategy. Separate the two streams. |
| Rule 5 — 2 of 3 in Zone A | Is the process mean shifting? | Same as Rule 2 (earlier detection) | Verify process settings. Check last material change or setup. |
| Rule 6 — 4 of 5 in Zone B | Is there a moderate sustained shift? | Gradual drift, consistent setup offset between shifts | Check process settings, fixture, incoming material. |
| Rule 7 — 15 in Zone C | Are measurements suspiciously close to the centre line? | Rounded data (insufficient gauge resolution), over-adjustment causing over-control, data from mixed subgroups | Verify gauge resolution. Check if data is being rounded or re-centred. |
| Rule 8 — 8 beyond Zone C | Do points alternate between upper and lower halves without crossing centreline? | Two material lots mixed in same subgroup, two machines contributing to same chart | Separate by source. Verify subgrouping rational principle. |

**Post-response steps (all rules):**
1. Document the signal and the investigation on the chart or SPC log.
2. Identify root cause using 5-Why or fishbone.
3. Implement correction and verify process returns to in-control state.
4. Do NOT recalculate control limits to accommodate the shift. Limits are recalculated only when a verified, permanent process change has been implemented.
5. Update PFMEA and Control Plan if the root cause reveals a new or uncontrolled failure mode.

---

## 5. Process Capability Formula Reference

### Definitions

| Symbol | Definition |
|--------|-----------|
| USL | Upper specification limit |
| LSL | Lower specification limit |
| X̄̄ | Process grand mean |
| σ̂ | Short-term standard deviation (estimated from within-subgroup variation: R̄/d₂ or S̄/c₄) |
| s | Overall (long-term) standard deviation (calculated from all individual measurements) |

### Short-Term Capability Indices (use σ̂ — within-subgroup)

These reflect the process's best potential capability, using only within-subgroup variation.

| Index | Formula | What it measures |
|-------|---------|-----------------|
| Cp | (USL − LSL) / (6σ̂) | Spread potential — tolerance vs. process spread. Ignores where the mean sits. |
| Cpk | min[(USL − X̄̄) / (3σ̂), (X̄̄ − LSL) / (3σ̂)] | Centred capability — how far the mean is from the nearest limit. |
| Cpm | (USL − LSL) / (6√(σ̂² + (X̄̄ − T)²)) | Taguchi index — penalises deviation from target T. Less common. |

### Long-Term Performance Indices (use s — overall standard deviation)

These include all variation sources (between-subgroup drift, shifts, etc.).

| Index | Formula | What it measures |
|-------|---------|-----------------|
| Pp | (USL − LSL) / (6s) | Overall spread performance over the study period. |
| Ppk | min[(USL − X̄̄) / (3s), (X̄̄ − LSL) / (3s)] | Overall centred performance. This is the realistic long-term prediction. |

### Interpretation Table

| Cpk / Ppk | Sigma level (approx.) | DPPM (approx.) | PPAP / IATF verdict |
|-----------|----------------------|----------------|---------------------|
| ≥ 1.67 | 5σ | < 233 ppm | Excellent — accepted without restriction |
| 1.33 – 1.67 | 4σ | 233 – 6,210 ppm | Acceptable — accepted, increased monitoring recommended for new processes |
| 1.00 – 1.33 | 3σ | 6,210 – 66,807 ppm | Marginal — 100% inspection, corrective action, customer approval required |
| < 1.00 | < 3σ | > 66,807 ppm | Not capable — PPAP blocked, mandatory corrective action |

### Critical Rules for Capability Calculations

1. **Process must be in statistical control before calculating capability.** If the process is not stable (control chart has out-of-control signals), the capability indices are meaningless. Stabilise first, then calculate.
2. **Report Cpk, not just Cp.** Cp measures spread potential regardless of where the mean sits. A process can have Cp = 2.00 but be completely off-centre. Cpk is always ≤ Cp.
3. **Minimum sample size for reliable capability:** 100 individual measurements. Capability calculated from 30 parts has a ±40% confidence interval — not suitable for PPAP submission.
4. **Cp = Cpk:** process is centred. **Cp >> Cpk:** process is significantly off-centre — centering improvement yields immediate Cpk gain.
5. **Ppk < Cpk always** (or equal): if Ppk is significantly lower than Cpk, the process is drifting or shifting between subgroups over time — the short-term capability is not sustained long-term.

---

## 6. Short-Run SPC — Notes for Small Batch Production

Standard X̄-R charts assume enough production to collect 25+ subgroups from a single part/process combination. For short-run, high-mix production, two approaches are used:

### DNOM (Deviation from Nominal) Chart

**Use when:** Multiple part numbers share the same process, same gauge, and similar tolerances. Each part has a different nominal but similar process variation.

**How it works:**
- Plot (X̄ − Nominal) instead of X̄ for each part.
- Control limits are calculated from the deviation data (all parts combined).
- All parts share a common centre line of zero.

**Conditions for validity:**
- Process variation (σ) is similar across all part numbers.
- Same gauge used for all parts.
- Same process and operation for all parts.

**Reject DNOM if:** part variations differ significantly (e.g., machined steel parts vs. rubber gaskets on same chart).

### Standardised (Z-score) Chart

**Use when:** Part families have different nominal values AND different process variations (σ values differ).

**How it works:**
- Plot Z = (X̄ − X̄̄ₚₐᵣₜ) / σ̂_part for each subgroup.
- Control limits are universal: UCL = +3, LCL = −3 (in standard deviation units).
- Each part contributes its own reference mean and standard deviation to normalise the chart.

**Requirements:** Each part number must have a historical mean (X̄̄) and estimated standard deviation (σ̂) from prior production.

### Z-MR Chart for Individuals (Short-Run)

For processes producing one unit per cycle across multiple part numbers:

- Z = (X_i − X̄̄_part) / σ̂_part — plotted as individuals
- MR = |Z_i − Z_{i-1}| — moving range in standardised units
- UCL/LCL = ±3 for Z chart; UCL_MR = 3.267 for MR chart

**When to use:** Low-volume machined parts, tooling qualification, laboratory test results across multiple test types.

### Short-Run SPC — Key Cautions

- Do not use Western Electric pattern rules (Rules 2–8) until at least 20–25 points are plotted for a given part/product. Pattern rules require adequate data.
- Capability indices (Cp, Cpk) cannot be reliably estimated in short-run scenarios from production data alone. Use process qualification data or historical analogous-process data with justified transfer.
- Short-run SPC is a monitoring tool, not a substitute for robust process qualification.
