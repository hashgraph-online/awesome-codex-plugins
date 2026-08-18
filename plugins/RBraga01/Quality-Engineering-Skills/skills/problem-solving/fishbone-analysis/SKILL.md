---
name: fishbone-analysis
description: >-
  Build an Ishikawa diagram, cause and effect analysis, or 6M fishbone to brainstorm and
  categorise all possible causes before narrowing to root cause with 5-Why. Covers Man,
  Machine, Method, Material, Measurement, and Environment (Mother Nature). Essential for
  8D D4 brainstorming sessions and CAPA root cause investigations.
license: MIT
metadata:
  author: RBraga01
  version: "1.1"
  iso-9001: "10.2"
  iatf-16949: "10.2.3"
  domain: quality-engineering
  subdomain: problem-solving
  industries: automotive,electronics,aerospace,medical,general
  status: approved
  created: "2026-06-01"
  last_updated: "2026-06-04"
  updated_by: migmcc
  reviewed_by: RBraga01
  standard_edition: "ISO 9001:2015"
---

# Fishbone (Ishikawa) Analysis

## When to use

Use fishbone analysis to brainstorm all possible causes of a quality problem **before** running 5-Why. It prevents tunnel vision and ensures no cause category is overlooked. Particularly valuable for complex defects with multiple potential contributing factors.

Typical use: 8D D4 brainstorming session, CAPA root cause investigation, initial problem analysis.

## Prerequisites

- Problem clearly defined with Is/Is-Not or 5W2H
- Cross-functional team (quality, production, engineering at minimum)
- Access to the process, machine, or product where defect occurred

## Required Fishbone Checklist

☐ Problem statement defined and agreed before starting — no cause language in the problem statement
☐ All 6M categories addressed — at least one entry per M, or documented justification if a category is not applicable
☐ Brainstorming completed before any evaluation or elimination — do not evaluate while generating
☐ Every cause classified as Confirmed, Probable, or Unlikely using objective evidence — not opinion alone
☐ Confirmed = supported by data or physical evidence; Probable = logical, consistent with Is/Is-Not, not yet confirmed; Unlikely = contradicted by data
☐ Confirmed and Probable causes cross-checked against existing PFMEA failure cause entries before proceeding to 5-Why
☐ Each Confirmed or Probable cause carries forward to its own 5-Why chain
☐ After root cause confirmed: horizontal deployment check — could the same cause exist in similar parts, processes, or product families?

---

## The 6M Framework

The six main "bones" of the fish. **All six must be addressed.** If a category genuinely does not apply, document: "No causes identified in this category after structured team review — not applicable because [reason]."

### 1. Man (Human Factors)

Questions to ask:
- Was the task performed by a trained, qualified operator?
- Is competence documented and current?
- Was the operator following the correct work instruction?
- Could fatigue, shift change, or distraction contribute?
- Is the task ergonomically difficult or error-prone?
- Is the same defect found on all shifts or only one? (single-shift → operator-specific)

### 2. Machine (Equipment)

Questions to ask:
- Is the machine calibrated? When was it last calibrated? Is it within interval?
- Has preventive maintenance been performed on schedule?
- Are there any known deviations (vibration, wear, temperature drift)?
- What is the machine capability (Cp, Cpk)? Is it capable for this feature?
- Is tooling worn or damaged?
- Is the jig or fixture functioning correctly?

### 3. Method (Process)

Questions to ask:
- Is there a documented work instruction for this operation?
- Is the work instruction current and at the workstation?
- Are process parameters (temperature, pressure, speed, torque) specified and controlled?
- Is there a control plan entry for this process step?
- Is the process sequence correct?
- Is the method different between shifts or operators?

### 4. Material (Input Material)

Questions to ask:
- Does the defect correlate with a specific incoming batch or supplier lot?
- Has the material specification been met (certificate of conformance, incoming inspection)?
- Has the material been stored correctly (temperature, humidity, FIFO)?
- Is the material traceable to its origin?
- Has the supplier changed anything recently (sub-supplier, process, location)?

### 5. Measurement (Measurement System)

Questions to ask:
- Is the measurement system capable (MSA / Gauge R&R performed)?
- Is the gauge calibrated and within its calibration interval?
- Is the measurement method standardised (same fixture, same operator technique)?
- Could measurement error mask the defect (false acceptable)?
- Are measurement results repeatable between operators?

### 6. Mother Nature / Environment

Questions to ask:
- Does the defect correlate with ambient temperature or humidity?
- Are there vibration or contamination sources nearby?
- Is lighting adequate for visual inspection?
- Are there seasonal patterns?
- Does the cleanroom or ESD environment meet requirements?

---

## Workflow

### Step 1 — Draw the diagram

Write the problem (effect) at the head (right side). Draw the spine. Add six main bones labelled with the 6M categories.

### Step 2 — Brainstorm with the team

For each M category: "What in [M] could cause [the problem]?"

Capture all ideas without judgment — quantity first, evaluation second. **Do not evaluate or discard during brainstorming.** Allocate 30–60 minutes minimum. Time pressure is the most common reason causes are missed.

Add each cause as a sub-bone to the relevant M category. Sub-bones can branch further (cause of a cause).

### Step 3 — Evaluate and prioritise

Mark each cause as:
- **Confirmed** (supported by data or direct physical evidence — not opinion)
- **Probable** (logical, consistent with the Is/Is-Not pattern, but not yet confirmed by data)
- **Unlikely** (contradicted by data or the Is/Is-Not pattern)

Discard Unlikely causes. Investigate Confirmed and Probable causes. A cause cannot be classified as Confirmed without objective evidence (measurement data, physical demonstration, reproduction test, or direct record review).

### Step 4 — PFMEA cross-check

Before proceeding to 5-Why, cross-check Confirmed and Probable causes against the existing PFMEA:

- Is this failure cause already documented in the PFMEA? If yes, was its detection or prevention control supposed to prevent this defect?
- If the PFMEA did not capture this cause, flag it — the PFMEA must be updated after the root cause is confirmed.

### Step 5 — Connect to 5-Why

For each Confirmed or Probable cause, run a [5-Why chain](../5why-root-cause/) to reach the systemic root cause.

The fishbone identifies candidate causes. The 5-Why validates and deepens them.

After root cause is confirmed: assess whether the same cause could exist in similar parts, processes, or product families. Document horizontal deployment actions if applicable.

---

## Output format

Document the fishbone as a table (easier to include in reports than a diagram):

| M Category | Possible Cause | Evidence / Status | Proceed to 5-Why? |
|------------|----------------|-------------------|-------------------|
| Man | Untrained operator | Training record missing for operator 12 | Yes |
| Machine | Jig worn | Measured wear 0.3mm — limit 0.1mm | Yes |
| Method | No contingency instruction | Work instruction reviewed — confirmed absent | Yes |
| Material | Batch variation | No batch correlation found | No |
| Measurement | Gauge repeatability | GR&R = 8% — acceptable | No |
| Environment | Temperature | Controlled at 22°C ± 2°C — stable | No |

All 6M categories must appear in the table. If a category has no entries after structured brainstorming, document: "No causes identified in this category after structured team review."

---

## Common mistakes

- **Brainstorming under time pressure** — causes are missed; allocate 30–60 minutes minimum
- **Stopping at first-level causes** — "machine not calibrated" is a cause, but add sub-bone: why was it not calibrated?
- **Not using data to confirm/discard** — every cause must be validated against objective evidence, not just listed
- **Using fishbone as the root cause** — fishbone finds candidate causes; 5-Why finds root cause
- **Skipping categories** — if a category is left blank without justification, the analysis is incomplete and may miss the real cause
- **Classifying causes as Confirmed based on team opinion** — Confirmed requires evidence; without it, classify as Probable and plan verification

---

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
| 1.0 | 2026-06-01 | @RBraga01 | Initial release |
| 1.1 | 2026-06-04 | @migmcc | Polished 6M categories, added validation criteria and 5-Why integration |
