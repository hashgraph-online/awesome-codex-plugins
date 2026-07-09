---
name: gauge-rr-study-guide
type: reference
parent_skill: msa-gauge-rr
author: RBraga01
version: "1.0"
status: approved
created: "2026-06-06"
last_updated: "2026-06-06"
updated_by: migmcc
reviewed_by: RBraga01
license: MIT
---

# Gauge R&R Study Conductor Guide

Operational guide for planning, executing, and documenting a crossed Gauge R&R study (10 parts × 3 appraisers × 2 trials).
Use alongside the [msa-gauge-rr](../SKILL.md) skill.

> **Scope:** This document covers how to run the physical study — part selection, randomisation, data collection, method selection, and manual calculations with a worked numeric example. For interpretation thresholds, audit criteria, and study type selection, see [msa-gauge-rr SKILL.md](../SKILL.md).

---

## 1. Pre-Study Preparation Checklist

Before any measurements are taken, confirm the following:

| Item | Requirement | Verified |
|------|-------------|---------|
| Parts selected | 10 parts spanning the full process variation range | [ ] |
| Gauge identified | Single gauge to be studied (ID, calibration cert current) | [ ] |
| Calibration current | Gauge calibration certificate valid at time of study | [ ] |
| Appraisers selected | 3 appraisers who normally perform this measurement in production | [ ] |
| Appraiser briefing | All three briefed: do not share results, do not adjust gauge | [ ] |
| Location | Study performed in production conditions (not metrology lab, unless production is the lab) | [ ] |
| Specification available | USL, LSL, and tolerance value confirmed and recorded | [ ] |
| Data sheet ready | Blank data collection sheet prepared (see Section 4) | [ ] |
| Random order generated | Measurement order randomised per appraiser per trial | [ ] |

---

## 2. Part Selection Criteria

Part selection is the single most common study error. Incorrect part selection invalidates the ndc result.

### Rules for Selecting Parts

1. **Span the full process variation range.** Parts must cover the range of values the process actually produces — from low end to high end. Do NOT select parts near the nominal or tolerance centre.
2. **Include borderline parts.** At least 2 parts should be near (but within) the specification limits.
3. **Do not cherry-pick conforming parts only.** If the process produces parts close to the limit, those must be included.
4. **Avoid selecting based on measurement value if possible.** Ideal selection: take consecutive production parts and measure them independently, then verify spread before proceeding.
5. **Parts must be stable.** Parts must not change dimension during handling between trials. For elastic or deformable parts, use fixturing.
6. **10 parts minimum.** Fewer parts reduce the statistical power of the ndc calculation.

### How to Verify Adequate Spread

After selecting parts and before starting the study, measure all 10 parts once with a reference gauge. Plot values on a number line:

- If all 10 values cluster within 20% of the tolerance range → part selection is inadequate. Select new parts.
- If values span at least 70% of the observed process range → part selection is adequate.

### Label Parts Neutrally

Code parts 1–10 (or use production serial numbers). Do not write the measured value on the part label. Appraisers must not know which parts are "near the limit."

---

## 3. Randomisation Procedure

Each appraiser must measure all 10 parts in a different random order for each trial. This is not optional — it prevents sequence bias and ensures trial-to-trial variation is captured.

### Generating the Random Order

Use a random number generator (calculator, Excel RAND(), or drawn slips):

**Example randomisation for 10 parts, 3 appraisers, 2 trials:**

| Trial | Appraiser A | Appraiser B | Appraiser C |
|-------|------------|------------|------------|
| Trial 1 | 7,2,9,1,5,3,10,6,4,8 | 3,8,1,6,10,4,2,9,5,7 | 5,1,8,3,6,10,4,7,2,9 |
| Trial 2 | 4,10,3,8,2,6,1,5,9,7 | 9,5,2,7,1,8,6,3,10,4 | 2,6,9,4,7,1,8,5,3,10 |

**Rules:**
- Appraiser A completes all 10 parts (Trial 1) before Appraiser B starts.
- Appraiser A does NOT see Appraiser B's or C's results at any time.
- Appraiser A does NOT see their own Trial 1 results before Trial 2.
- Minimum time between trials for the same appraiser: sufficient to prevent memory of previous readings (typically the time for the other appraisers to complete their trial).
- The conductor (study coordinator) records all readings. Appraisers do not self-record.

---

## 4. Data Collection Sheet Template

```
GAUGE R&R STUDY — DATA COLLECTION SHEET
=========================================
Part Number:          ________________    Characteristic:       ________________
Specification (USL):  ________________    Specification (LSL):  ________________
Tolerance (USL-LSL):  ________________    Units:                ________________
Gauge ID:             ________________    Gauge Description:    ________________
Calibration Cert #:   ________________    Calibration Expiry:   ________________
Study Date:           ________________    Location:             ________________
Conducted by:         ________________

APPRAISERS
Appraiser A: ________________    Appraiser B: ________________    Appraiser C: ________________

─────────────────────────────────────────────────────────────────────────────
         APPRAISER A           APPRAISER B           APPRAISER C
Part  T1      T2    Range   T1      T2    Range   T1      T2    Range
─────────────────────────────────────────────────────────────────────────────
 1   ____   ____   ____   ____   ____   ____   ____   ____   ____
 2   ____   ____   ____   ____   ____   ____   ____   ____   ____
 3   ____   ____   ____   ____   ____   ____   ____   ____   ____
 4   ____   ____   ____   ____   ____   ____   ____   ____   ____
 5   ____   ____   ____   ____   ____   ____   ____   ____   ____
 6   ____   ____   ____   ____   ____   ____   ____   ____   ____
 7   ____   ____   ____   ____   ____   ____   ____   ____   ____
 8   ____   ____   ____   ____   ____   ____   ____   ____   ____
 9   ____   ____   ____   ____   ____   ____   ____   ____   ____
10   ____   ____   ____   ____   ____   ____   ____   ____   ____
─────────────────────────────────────────────────────────────────────────────
X̄ᴬ  ____   ____           ____   ____           ____   ____
R̄ᴬ       ____                  ____                  ____
─────────────────────────────────────────────────────────────────────────────

PART AVERAGES (across all appraisers and trials):
Part:   1     2     3     4     5     6     7     8     9    10
Avg:  ____  ____  ____  ____  ____  ____  ____  ____  ____  ____
Rp (max part avg − min part avg): ____

RANGE AVERAGES:
R̄ overall = (R̄ᴬ + R̄ᴮ + R̄ᶜ) / 3 = ____
UCLR = D₄ × R̄ = ____   (D₄ for n=2: 3.267)

APPRAISER AVERAGES:
X̄ᴬ (grand) = ____   X̄ᴮ (grand) = ____   X̄ᶜ (grand) = ____
XDIFF = max(X̄ᴬ, X̄ᴮ, X̄ᶜ) − min(X̄ᴬ, X̄ᴮ, X̄ᶜ) = ____

CALCULATIONS (see Section 6):
EV = ____    AV = ____    GRR = ____
PV = ____    TV = ____
%GRR (of TV) = ____    %GRR (of Tolerance) = ____
ndc = ____

SIGNATURES:
Study conductor: ________________  Date: ________
Quality Engineer: _______________  Date: ________
```

---

## 5. ANOVA vs. Range Method — When to Use Which

Both methods calculate EV, AV, and GRR. Choose based on the following:

| Criteria | Range Method | ANOVA Method |
|---------|-------------|-------------|
| Calculation complexity | Simple — manual calculation feasible | Complex — requires software (Minitab, Excel ANOVA) |
| Interaction term (Appraiser × Part) | Not captured | Captured — shows if appraisers rank parts differently |
| Required by AIAG MSA 4th edition | Listed as acceptable | Preferred for PPAP |
| Use when | Quick field study, training, or no software available | PPAP submission, special characteristics, customer-required |
| Result accuracy | Slightly less accurate (ignores interaction) | More accurate |
| Sample size sensitivity | Works for 2 or 3 trials | Works for 2 or 3 trials |

**Decision rule:**
- For formal PPAP submission or IATF 16949 audit purposes: use ANOVA.
- For internal qualification, quick verification, or training exercises: Range method is acceptable.
- If ANOVA reveals a significant Appraiser × Part interaction (p < 0.05): investigate whether some appraisers are measuring certain parts differently. This points to a training or fixturing issue, not just gauge imprecision.

---

## 6. Calculation Reference — Range Method

### Constants Used

| n (trials per appraiser) | d₂* | K₁ (= 1/d₂*) | D₄ |
|--------------------------|-----|--------------|-----|
| 2 | 1.128 | 0.8862 | 3.267 |
| 3 | 1.693 | 0.5908 | 2.574 |

For appraiser variation (number of appraisers = 3), use K₂ = 0.5231 directly from AIAG MSA 4th ed. Table IV. This corresponds to d₂* ≈ 1.912 (range of 3 values, 1 range calculated). Note: the value 1.693 in the EV table above is d₂* for 3 trials per appraiser — it is not the correct value for the AV calculation.

### Step-by-Step Formulas

**Step 1 — Equipment Variation (EV = Repeatability)**

EV = R̄_overall × K₁

Where:
- R̄_overall = average of all within-appraiser ranges across all parts
- K₁ = 1/d₂* for the number of trials (n = 2 → K₁ = 0.8862; n = 3 → K₁ = 0.5908)

EV is the 5.15σ spread (representing 99% of the gauge variation distribution).

**Step 2 — Appraiser Variation (AV = Reproducibility)**

AV = √[(XDIFF × K₂)² − (EV² / (n × r))]

Where:
- XDIFF = range of appraiser grand averages = max(X̄ᴬ, X̄ᴮ, X̄ᶜ) − min(X̄ᴬ, X̄ᴮ, X̄ᶜ)
- K₂ = 1/d₂* for number of appraisers (3 appraisers → K₂ = 0.5231)
- n = number of trials per appraiser
- r = number of parts

If the expression under the square root is negative, set AV = 0 (this occurs when appraiser variation is negligible relative to EV).

**Step 3 — Gauge R&R (GRR)**

GRR = √(EV² + AV²)

**Step 4 — Part Variation (PV)**

PV = Rp × K₃

Where:
- Rp = range of part averages = max(part avg) − min(part avg)
- K₃ = 1/d₂* for number of parts (10 parts → K₃ = 0.3146)

**Step 5 — Total Variation (TV)**

TV = √(GRR² + PV²)

**Step 6 — %GRR (two versions)**

%GRR (Study Variation) = (GRR / TV) × 100

%GRR (Tolerance) = (GRR / Tolerance) × 100    ← use for PPAP

**Step 7 — Number of Distinct Categories (ndc)**

ndc = 1.41 × (PV / GRR)

Round down to nearest integer.

---

## 7. Worked Numeric Example

**Study parameters:**
- Characteristic: Pin diameter, nominal 10.00 mm, tolerance ±0.15 mm → Tolerance = 0.30 mm
- 10 parts, 3 appraisers (A, B, C), 2 trials each

**Raw data (measurements in mm, deviation from nominal for readability):**

| Part | A-T1 | A-T2 | A-Range | B-T1 | B-T2 | B-Range | C-T1 | C-T2 | C-Range | Part Avg |
|------|------|------|---------|------|------|---------|------|------|---------|----------|
| 1 | 9.92 | 9.91 | 0.01 | 9.93 | 9.91 | 0.02 | 9.92 | 9.93 | 0.01 | 9.920 |
| 2 | 9.95 | 9.96 | 0.01 | 9.95 | 9.97 | 0.02 | 9.96 | 9.95 | 0.01 | 9.958 |
| 3 | 10.03 | 10.04 | 0.01 | 10.02 | 10.03 | 0.01 | 10.03 | 10.04 | 0.01 | 10.030 |
| 4 | 9.98 | 9.97 | 0.01 | 9.99 | 9.98 | 0.01 | 9.97 | 9.98 | 0.01 | 9.980 |
| 5 | 10.08 | 10.07 | 0.01 | 10.08 | 10.09 | 0.01 | 10.07 | 10.08 | 0.01 | 10.080 |
| 6 | 9.87 | 9.88 | 0.01 | 9.86 | 9.88 | 0.02 | 9.88 | 9.87 | 0.01 | 9.873 |
| 7 | 10.11 | 10.12 | 0.01 | 10.10 | 10.11 | 0.01 | 10.12 | 10.11 | 0.01 | 10.113 |
| 8 | 9.94 | 9.93 | 0.01 | 9.94 | 9.93 | 0.01 | 9.93 | 9.94 | 0.01 | 9.935 |
| 9 | 10.06 | 10.05 | 0.01 | 10.05 | 10.06 | 0.01 | 10.06 | 10.07 | 0.01 | 10.058 |
| 10 | 9.90 | 9.89 | 0.01 | 9.90 | 9.91 | 0.01 | 9.89 | 9.90 | 0.01 | 9.898 |

**Appraiser grand averages:**
- X̄ᴬ = (9.92+9.91+9.95+9.96+10.03+10.04+9.98+9.97+10.08+10.07+9.87+9.88+10.11+10.12+9.94+9.93+10.06+10.05+9.90+9.89) / 20 = **9.987**
- X̄ᴮ = **9.987**
- X̄ᶜ = **9.987**

**Average ranges:**
- R̄ᴬ = (0.01+0.01+0.01+0.01+0.01+0.01+0.01+0.01+0.01+0.01) / 10 = **0.010**
- R̄ᴮ = (0.02+0.02+0.01+0.01+0.01+0.02+0.01+0.01+0.01+0.01) / 10 = **0.013**
- R̄ᶜ = **0.010**
- R̄_overall = (0.010 + 0.013 + 0.010) / 3 = **0.011**

**UCLR check:** UCLR = 3.267 × 0.011 = 0.036. All individual ranges are below 0.036 — no outliers.

**Calculations:**

| Metric | Formula | Result |
|--------|---------|--------|
| EV | 0.011 × 0.8862 | **0.00975 mm** |
| XDIFF | max(9.987, 9.987, 9.987) − min = | **0.000 mm** |
| AV | √[(0.000 × 0.5231)² − (0.00975² / (2×10))] → negative → | **0.000 mm** |
| GRR | √(0.00975² + 0²) | **0.00975 mm** |
| Rp (part avg range) | 10.113 − 9.873 | **0.240 mm** |
| PV | 0.240 × 0.3146 | **0.07550 mm** |
| TV | √(0.00975² + 0.07550²) | **0.07612 mm** |
| %GRR (of TV) | (0.00975 / 0.07612) × 100 | **12.8%** |
| %GRR (of Tolerance) | (0.00975 / 0.30) × 100 | **3.25%** |
| ndc | 1.41 × (0.07550 / 0.00975) | **10.9 → 10** |

**Interpretation:**
- %GRR of Tolerance = 3.25% → Excellent (< 10%). Gauge is fully acceptable.
- %GRR of TV = 12.8% → Marginal when compared to study variation, but this is largely because parts are well-spread (good PV). Tolerance method is the primary criterion for PPAP.
- ndc = 10 → Well above the minimum of 5. Gauge can distinguish 10 categories of part variation.
- EV dominates GRR (AV = 0): gauge precision is the limiting factor, not appraiser technique. No training issue.

---

## 8. MSA Study Report — What to Include

The formal MSA study report submitted with PPAP or to a customer must contain:

| Section | Content |
|---------|---------|
| Study identification | Part number, characteristic, specification, tolerance, units |
| Gauge data | Gauge ID, type, resolution, calibration certificate number, expiry date |
| Study parameters | Date, location, appraisers (by ID/code — not always by name), trials, parts |
| Part selection rationale | Statement confirming parts span the full process variation range |
| Raw data table | All readings (all appraisers, all trials, all parts) |
| Range chart | Appraiser range charts with UCLR — confirm no points above UCL |
| Average chart | Part averages by appraiser — part variation must dominate |
| Results summary | EV, AV, GRR (absolute and as %), PV, TV, ndc |
| Method used | ANOVA or Range method — state which |
| Acceptance criteria applied | %GRR < 30% (tolerance method) AND ndc ≥ 5 |
| Decision | Accepted / Marginal (with justification) / Rejected |
| Signatures | Study conductor, Quality Engineer, approval authority |
| Attachments | Calibration certificate, randomisation table used |

**Do not report only %GRR of TV.** Always report both %GRR of TV and %GRR of Tolerance, and state which criterion was used for the acceptance decision.

**Flag any UCLR violations.** If any individual range exceeds UCLR = D₄ × R̄, that measurement was inconsistent. Investigate before closing the study. If the outlier is confirmed to be a special cause (mis-reading, part moved during measurement), it may be excluded and the study recalculated — document the reason.
