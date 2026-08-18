---
name: spc-control-charts
description: >-
  Statistical Process Control (SPC) — select the correct control chart, interpret out-of-control
  signals using Western Electric rules, calculate and interpret Cp, Cpk, Pp, Ppk. Use when setting
  up SPC for a new characteristic, interpreting control chart signals, responding to special cause
  variation, or auditing SPC implementation. Covers AIAG SPC 2nd edition and IATF 16949 §8.3.3.
license: MIT
metadata:
  author: RBraga01
  version: "1.1"
  iso-9001: "9.1"
  iatf-16949: "8.3.3, 9.1.1"
  aiag-reference: "AIAG SPC 2nd Edition"
  domain: quality-engineering
  subdomain: measurement
  industries: automotive,electronics,aerospace,medical,general
  status: approved
  created: "2026-06-06"
  last_updated: "2026-06-06"
  updated_by: migmcc
  reviewed_by: RBraga01
  standard_edition: "AIAG SPC 2nd Edition (2005)"
---

# Statistical Process Control (SPC)

## When to use

Use this skill when:
- Selecting the correct control chart type for a process characteristic
- Interpreting control chart signals — is this special cause or common cause?
- Calculating Cp, Cpk, Pp, Ppk and determining if the process is capable
- Responding to an out-of-control signal on a production line
- Setting up SPC for a new special characteristic (PPAP/APQP requirement)
- Auditing an SPC system for correctness and adequacy
- Explaining SPC results to a customer or during an audit

## Prerequisites

- The characteristic to monitor (variable or attribute data)
- Production data (minimum 25 subgroups for control limits, 100+ pieces for capability)
- MSA study completed and %GRR < 30% for variable charts
- Process specification (nominal + tolerance) for capability calculations
- Subgroup size decided based on rational subgrouping principle

## Workflow

### Step 1 — Select the correct control chart

#### Variable data (measured values — length, weight, pressure, temperature)

| Chart | When to use |
|-------|------------|
| **X̄-R (X-bar/Range)** | Subgroup size 2–9; most common in manufacturing |
| **X̄-S (X-bar/Sigma)** | Subgroup size ≥ 10; better sensitivity to spread |
| **I-MR (Individuals/Moving Range)** | Subgroup size = 1; one measurement per inspection (slow processes, destructive tests) |

#### Attribute data (counts, pass/fail, defect rates)

| Chart | When to use |
|-------|------------|
| **p-chart** | Proportion defective; variable subgroup size |
| **np-chart** | Number defective; constant subgroup size |
| **c-chart** | Count of defects per unit; constant inspection area |
| **u-chart** | Defects per unit; variable inspection area |

**Decision rule:** If you can measure it with a number, use a variable chart. Variable charts are more sensitive and require smaller samples to detect process shifts.

---

### Step 2 — Calculate control limits

#### X̄-R chart

From at least 25 subgroups of size n:

- **Centre line (X̄̄):** Grand average of all subgroup means
- **UCL_X̄ = X̄̄ + A₂ × R̄**
- **LCL_X̄ = X̄̄ − A₂ × R̄**
- **Centre line (R̄):** Average of all subgroup ranges
- **UCL_R = D₄ × R̄**
- **LCL_R = D₃ × R̄** (= 0 for n ≤ 6)

Constants for common subgroup sizes:

| n | A₂ | D₃ | D₄ |
|---|----|----|-----|
| 2 | 1.880 | 0 | 3.267 |
| 3 | 1.023 | 0 | 2.574 |
| 4 | 0.729 | 0 | 2.282 |
| 5 | 0.577 | 0 | 2.114 |

**Important:** Control limits are calculated FROM THE DATA — never set them to match the specification limits. Specification limits and control limits are completely separate concepts.

---

### Step 3 — Apply Western Electric Rules (out-of-control signals)

Divide the control chart into zones: Zone A (2–3σ from centre), Zone B (1–2σ), Zone C (0–1σ).

| Rule | Signal | Interpretation |
|------|--------|----------------|
| **Rule 1** | 1 point beyond 3σ (outside control limits) | Large, immediate shift |
| **Rule 2** | 9 consecutive points on same side of centre line | Process mean has shifted |
| **Rule 3** | 6 consecutive points steadily increasing or decreasing | Trend — tool wear, drift |
| **Rule 4** | 14 consecutive points alternating up and down | Systematic variation — two alternating distributions |
| **Rule 5** | 2 of 3 consecutive points in Zone A or beyond (same side) | Large shift signal |
| **Rule 6** | 4 of 5 consecutive points in Zone B or beyond (same side) | Moderate shift |
| **Rule 7** | 15 consecutive points in Zone C (either side of centre line) | Stratification — data from two separate distributions |
| **Rule 8** | 8 consecutive points beyond Zone C (either side) | Mixture — sampling from two processes |

**Action required for ANY rule violation:** Stop and investigate immediately. Do not reset control limits. Do not restart until root cause is identified.

Most commonly applied in automotive: Rules 1, 2, 3 minimum. Rules 1–8 for safety-critical characteristics.

---

### Step 4 — Calculate and interpret process capability

**Capability data requirements:** Process capability is only valid when calculated on a process that is in statistical control (no out-of-control signals) and with a minimum of **100 consecutive parts** from that stable process. Fewer parts produce unreliable Cpk estimates — a Cpk calculated on 30 parts can vary by ±0.3 from the true value. Do not report Cpk based on fewer than 100 parts as a production capability figure; label it "preliminary" and state the sample size.

**Short-term capability (within-subgroup variation):**

- **Cp = (USL − LSL) / (6σ̂)**  — capability — process spread vs. tolerance
- **Cpk = min[(USL − X̄̄) / (3σ̂), (X̄̄ − LSL) / (3σ̂)]** — centred capability — accounts for process mean location

σ̂ = R̄ / d₂ (for X̄-R chart)

**Long-term performance (total variation including between-subgroup):**

- **Pp = (USL − LSL) / (6s)**  — same formula but uses overall standard deviation s
- **Ppk = min[(USL − X̄̄) / (3s), (X̄̄ − LSL) / (3s)]**

#### Acceptance criteria

| Index | Minimum | Target |
|-------|---------|--------|
| Cpk | 1.33 | 1.67 |
| Ppk | 1.33 | 1.67 |

| Cpk | Interpretation | PPAP action |
|-----|---------------|-------------|
| ≥ 1.67 | Excellent | ✅ Accepted |
| 1.33 – 1.67 | Acceptable | ✅ Accepted — monitor |
| 1.00 – 1.33 | Marginal | ⚠️ Customer approval required; add control measures |
| < 1.00 | Not capable | ❌ 100% inspection required; corrective action mandatory |

#### Cp vs. Cpk relationship

- Cp = Cpk: process is perfectly centred
- Cp > Cpk: process is off-centre — improve centering before widening control limits
- Never report only Cp without Cpk — a process can be off-centre and still show a good Cp

---

### Step 5 — Respond to an out-of-control condition

1. **Stop the process** (or place affected output on hold) — do not continue producing to an out-of-control process
2. **Contain** — identify affected output since last in-control point
3. **Investigate** — ask: what changed? (material lot, operator, shift, tooling, environment)
4. **Identify root cause** — use 5-Why or Fishbone (is-is-not to scope the problem first)
5. **Correct** — implement correction and verify the process returns to control
6. **Document** — note the signal, investigation, and action taken on the chart (or in the log)
7. **Update PFMEA and Control Plan** if the root cause reveals a new failure mode

Do NOT simply recalculate control limits after a shift to make the chart "look in control."

---

### Step 6 — Audit an SPC implementation

When reviewing SPC in production or at a supplier:

- [ ] Correct chart type selected for data type (variable vs. attribute)
- [ ] Minimum 25 subgroups used to calculate initial control limits
- [ ] Control limits calculated from process data — NOT set to specification limits
- [ ] Western Electric rules applied (minimum Rule 1, 2, 3)
- [ ] Out-of-control signals are annotated on the chart with the action taken
- [ ] Process capability calculated on stable (in-control) process only
- [ ] Cpk ≥ 1.33 minimum; 1.67 for special characteristics
- [ ] MSA study complete and %GRR < 30% for the gauge being used
- [ ] Control chart is used for decision-making — not filled in retroactively

---

## Validation criteria

An SPC implementation is adequate when:
- Chart type matches data type and subgroup size
- Control limits calculated from minimum 25 subgroups of production data
- Process in statistical control before capability is calculated
- Cpk ≥ 1.33 (minimum) for all monitored characteristics
- Out-of-control signals trigger documented investigation and corrective action

## Common mistakes

- Setting control limits equal to specification limits (a fundamental SPC error — these are different concepts)
- Calculating capability on an out-of-control process (meaningless — must be stable first)
- Reporting Cp but not Cpk — hides off-centre processes
- Using only n=1 individual charts when subgrouping would reveal more
- Filling in control charts retroactively at end of shift — defeats the purpose of real-time monitoring
- Recalculating control limits to eliminate out-of-control points without identifying root cause
- Reporting Cpk = 1.45 based on 30 parts — too few; minimum 100 pieces for reliable capability

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
| 1.1 | 2026-06-06 | @migmcc | Added 100-part minimum requirement for valid capability study in Step 4; clarified in-control prerequisite before capability calculation |
