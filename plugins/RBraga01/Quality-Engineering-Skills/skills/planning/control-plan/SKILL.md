---
name: control-plan
description: >-
  Control Plan — build, review, or audit a Prototype, Pre-launch, or Production Control Plan linked
  to PFMEA failure modes and controls. Use when creating a new control plan, updating after a process
  change or corrective action, or auditing an existing CP for completeness and PFMEA alignment.
  Covers AIAG Control Plan reference manual and IATF 16949 §8.5.1.
license: MIT
metadata:
  author: RBraga01
  version: "1.1"
  iso-9001: "8.5.1"
  iatf-16949: "8.5.1"
  aiag-reference: "AIAG Control Plan Reference Manual"
  domain: quality-engineering
  subdomain: planning
  industries: automotive,electronics,aerospace,medical,general
  status: approved
  created: "2026-06-06"
  last_updated: "2026-06-06"
  updated_by: migmcc
  reviewed_by: RBraga01
  standard_edition: "AIAG Control Plan Reference Manual (1995) / IATF 16949:2016 §8.5.1"
---

# Control Plan

## When to use

Use this skill when:
- Creating a new Control Plan for prototype, pre-launch, or production
- Reviewing an existing Control Plan for completeness and accuracy
- Updating the CP after a process change, corrective action (D7), or PFMEA update
- Auditing a supplier's Control Plan during qualification or an IATF audit
- Linking PFMEA controls to the Control Plan after FMEA review

## Prerequisites

- Process Flow Diagram (required — CP must mirror the process flow sequence)
- PFMEA (required — CP controls derive from PFMEA recommended actions)
- Drawing with ballooned characteristics and tolerance data
- List of special and significant characteristics (SC, CC, KPC, KCC)
- MSA results for measurement systems referenced in the CP (for production CP)

## Workflow

### Step 1 — Determine the CP type

| Type | When | Purpose |
|------|------|---------|
| **Prototype** | During prototype builds | Describes dimensional, material, and functional tests in prototype phase |
| **Pre-launch** | After prototype, before PPAP | Describes controls in place during pilot/pre-production runs |
| **Production** | After PPAP approval, at SOP | The living document — updated throughout product life |

All three types may coexist during APQP phases. The Production CP is the one submitted as PPAP Element 7.

### Step 2 — Build the Control Plan structure

The CP is a table with one row per characteristic per process step. Each row contains:

**Header section (document-level):**
- Control Plan number and revision
- Part number and revision
- Part name / description
- Supplier / plant
- Supplier code (OEM code)
- Key contact / phone
- Core team (multi-functional)
- Date (original) and date (revised)
- Customer engineering approval (name/date) — if required
- Customer quality approval (name/date) — if required
- Supplier approval (name/date)

**Detail columns (one row per characteristic):**

| Column | What to enter |
|--------|--------------|
| Part/process number | Reference number from Process Flow |
| Process name / operation description | Name of the process step |
| Machine, device, jig, or tool | Equipment used at this step |
| Number | Characteristic number (links to balloon drawing) |
| Product characteristic | Product feature being controlled (dimension, material property, appearance) |
| Process characteristic | Process parameter being controlled (temperature, pressure, speed, torque) |
| Special characteristic classification | SC, CC, KPC, KCC, *, ▲ per customer symbology |
| Product/process specification / tolerance | Nominal value and tolerance band |
| Evaluation / measurement technique | Gauge type, method, or test used |
| Sample size | Number of parts per sample |
| Frequency | How often samples are taken (every hour, every lot, 100%) |
| Control method | How the process is controlled (SPC chart, go/no-go gauge, visual, 100% inspection) |
| Reaction plan | What to do if out-of-control or out-of-specification (who, what action, containment) |

### Step 3 — Populate from PFMEA

For each high-severity failure mode in the PFMEA:
1. Identify the current prevention and detection controls from the PFMEA
2. Transfer these controls into the corresponding CP row
3. The reaction plan must address what happens if the control detects a non-conformance

Every special characteristic (SC, CC, ★, ◆) in the PFMEA must appear in the CP.
Every recommended action completed in the PFMEA must be reflected in the updated CP controls.

### Step 4 — Special characteristics — mandatory coverage

| Classification | OEM symbol | CP requirement |
|----------------|-----------|----------------|
| Safety / Regulatory | ★ SC / ⬟ | 100% inspection OR demonstrated Cpk ≥ 1.67 + statistical monitoring |
| Critical Characteristic | CC / ◆ | Same as above — automatic stop if out of spec |
| Significant Characteristic | SC (Ford) / KPC | Process monitoring with defined sample plan and reaction |
| Key Control Characteristic | KCC | Process parameter monitoring (not product) — SPC or other control |

**OEM symbol conventions vary.** Always use the exact symbol specified in the customer's CSR:
- Ford: CC (Critical Characteristic) and SC (Significant Characteristic) — do not use ★ or ◆
- GM: ★ for safety-critical; Δ for significant
- VW / Audi: D (design feature, = CC), E (significant characteristic), I (functional dimension) per FORMEL Q
- BMW: G-SC (significant characteristic), G-CC (critical characteristic) per BMW standard
- Stellantis: CC and SC per MAQMSR — requires AIAG-VDA FMEA format alignment

Using the wrong symbol for the customer's OEM is an immediate finding at PPAP and IATF audit.

For all special characteristics: the reaction plan must specify who is notified, containment action, and when the process can restart.

### Step 5 — Reaction plan requirements

Every row in the CP must have a reaction plan. Minimum requirements:

- **Who** is responsible for taking action
- **What** immediate containment is applied (tag, sort, hold, stop production)
- **Who** is notified (supervisor, quality, engineering)
- **When** production may restart (after what verification)
- Reference to relevant Work Instruction or SOP for the reaction

A reaction plan that says only "notify supervisor" or "quarantine parts" is insufficient — it must specify the next step after notification.

### Step 6 — Audit an existing Control Plan

When reviewing a supplier's or internal CP, check:

**Structure:**
- [ ] All process steps from the Process Flow are represented
- [ ] Each special characteristic has its own dedicated row
- [ ] Revision level matches the current PFMEA and drawing revision

**Characteristics:**
- [ ] All SC/CC/KPC/KCC are listed with correct classification symbols
- [ ] Product AND process characteristics are both covered (not just product)
- [ ] Tolerances match the current released drawing

**Controls:**
- [ ] Measurement technique is specific (gauge type, not just "measure")
- [ ] Sample size and frequency are defined (not "as required" or "as needed")
- [ ] 100% inspection is specified where Cpk < 1.33
- [ ] SPC control charts are specified for characteristics where they are required

**Reaction plan:**
- [ ] Every row has a reaction plan
- [ ] Reaction plans specify concrete actions (not just "notify supervisor")
- [ ] Reaction plans are consistent with PFMEA failure mode severity

**Alignment:**
- [ ] CP controls match PFMEA current controls column for each failure mode
- [ ] Completed PFMEA recommended actions are reflected in updated controls
- [ ] CP revision date is more recent than most recent PFMEA update date

## Validation criteria

A complete Production Control Plan for PPAP submission must:
- Cover every operation in the Process Flow
- Include every special and significant characteristic with correct classification
- Have a MSA-validated measurement system for every variable characteristic on SC/CC
- Have a reaction plan for every row
- Be signed by the APQP team (multi-functional) and have customer approval if required
- Match the PFMEA revision level

## Common mistakes

- Control Plan created without reference to PFMEA — controls are generic, not linked to actual failure modes
- Reaction plan says "notify supervisor" only — not a reaction plan, just escalation
- Missing process characteristics — CP only controls product dimensions, not process parameters like temperature or torque
- Sample plan says "as required" — must specify a number and frequency
- SC/CC characteristics not identified with correct customer symbol — auditor will flag this immediately
- CP not updated after D7 of an 8D — the most common disconnect in corrective action systems
- Gauge type not specified — "visual inspection" or "measure" is not sufficient; must name the tool

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
| 1.1 | 2026-06-06 | @migmcc | Added OEM-specific special characteristic symbol conventions (Ford, GM, VW, BMW, Stellantis) in Step 4 |
