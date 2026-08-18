---
name: pfmea-process
description: >-
  Build a PFMEA worksheet, process risk analysis, or AP table using the AIAG-VDA FMEA
  Handbook 2019 7-step approach. Covers Structure Analysis, Function Analysis, Failure
  Analysis, Risk Analysis (Action Priority H/M/L), Optimization, and Documentation.
  Required by IATF 16949 and OEM customer-specific requirements for new processes,
  process changes, and post-escape PFMEA updates.
license: MIT
metadata:
  author: RBraga01
  version: "1.1"
  iso-9001: "8.1"
  iatf-16949: "8.3.3.3"
  aiag-reference: "AIAG-VDA FMEA Handbook 2019, Steps 1–7"
  domain: quality-engineering
  subdomain: risk-analysis
  industries: automotive,electronics,aerospace,medical,general
  status: approved
  created: "2026-06-01"
  last_updated: "2026-06-03"
  updated_by: RBraga01
  reviewed_by: RBraga01
  standard_edition: "AIAG-VDA FMEA Handbook 2019"
---

# Process FMEA (PFMEA) — AIAG-VDA 2019

## Goal

Identify and prioritise process risk before production — using the AIAG-VDA 2019 7-step approach — so that high-priority failure modes are eliminated or controlled before they reach the customer, and the result feeds directly into the Control Plan and Work Instructions.

## Required Execution Checklist

- [ ] Scope defined: process step boundaries, model year, team assembled with cross-functional representation
- [ ] Process Flow Diagram (PFD) available and used as Step 2 input
- [ ] All process steps in the PFD have a corresponding entry in Structure Analysis (Step 2)
- [ ] Every process step has at least one Function defined in Step 3
- [ ] Failure chain complete for each function: Effect → Mode → Cause (in this direction — not reversed)
- [ ] All Failure Causes are evidence-based — no unverified assumptions used as final causes
- [ ] S/O/D ratings agreed by the cross-functional team and documented
- [ ] All Special Characteristics have S=9 or S=10
- [ ] Every H-AP item has a named owner, target date, and is tracked to closure
- [ ] PFMEA detection controls match the Control Plan; prevention controls match Work Instructions

---

## When to use

- New process development (pre-production)
- Existing process change or transfer
- After a quality escape (update to reflect failure mode)
- Periodic review (IATF requires annual review or at change)
- Customer-specific requirement (Ford, GM, Stellantis, BMW, VW all require PFMEA)

## Prerequisites

- Process flow diagram (PFD) — required for Step 2
- Product drawings with special characteristics identified
- DFMEA (if applicable) for effect severity reference
- Team: process engineer, quality engineer, production supervisor, maintenance

## The 7-Step AIAG-VDA 2019 Approach

---

### Step 1 — Planning and Preparation

Define the scope:
- **FMEA header:** part number, part name, model year, process step scope, revision, date, team
- **Analysis boundary:** which process steps are in scope (start point and end point)
- **Timeline:** new PFMEA or revision of existing?

Prepare:
- Process Flow Diagram (PFD) — this drives Steps 2 and 3
- List of Special Characteristics (SC) from the drawing (symbols: ◆ ★ ⬟ vary by customer)

---

### Step 2 — Structure Analysis

Map the process hierarchy:
```
Process Item (e.g., Steering Column Assembly Line)
└── Process Step (e.g., Station 3 — Torque tightening)
    └── Work Element (e.g., Pneumatic driver, torque wrench)
```

For each process step, identify the **4M inputs**: Man, Machine, Method, Material.

This structure becomes the "what can go wrong" framework in Step 4.

**Consistency check:** Every Process Step defined here must have at least one Function defined in Step 3. A process step with no function is incomplete — it cannot be analysed for failure in Step 4.

---

### Step 3 — Function Analysis

For each process step and work element, define:
- **Process function:** what should happen? (verb + noun + measurable characteristic)
  - Example: "Tighten bolt M8 to 22 ± 2 Nm"
- **Product characteristic:** what product feature results from this step?
  - Flag all Special Characteristics (SC) — these get highest attention in D/O/D ratings

**Functional chain:**
```
Work Element function → Process Step function → Product Characteristic
(tool applies torque) → (bolt is tightened to spec) → (joint meets strength requirement)
```

---

### Step 4 — Failure Analysis

For each function, identify the failure chain: **Failure Effect → Failure Mode → Failure Cause**

Work in this direction (Effect first, then Mode, then Cause):

**Failure Effect (FE):** what is the impact on the customer (internal or end user)?
- End-user effect (most severe): safety, regulatory non-compliance, loss of function
- Manufacturing effect: rework, scrap, line stoppage, warranty

**Failure Mode (FM):** how does this process step fail to perform its function?
- Example: "Bolt torqued too low", "Part installed backwards", "Incorrect material loaded"

**Failure Cause (FC):** what causes the failure mode?
- Machine: "Torque wrench not calibrated", "Air pressure drop"
- Man: "Work instruction not followed", "Untrained operator"
- Method: "Incorrect torque value in WI", "No torque verification step"
- Material: "Wrong bolt grade loaded", "Lubrication not applied"

**Multiple causes per failure mode are normal** — each FC gets its own row.

**Failure Cause validation:** Failure Causes must be supported by objective evidence or structured root cause analysis (e.g., [5-Why](../../problem-solving/5why-root-cause/)). Unverified assumptions — "probably," "may be," "could be" — must not be entered as final Failure Causes. For post-escape PFMEA updates, the FC must match the validated root cause from the 8D or CAPA, not a revised opinion.

---

### Step 5 — Risk Analysis (Action Priority)

For each FC row, assign three ratings:

#### Severity (S) — impact of the Failure Effect on the customer

| S | Effect |
|---|--------|
| 10 | Safety — affects operator safety without warning |
| 9 | Regulatory non-compliance |
| 8 | Loss of primary function (end user) |
| 7 | Reduced primary function |
| 6 | Loss of comfort / convenience function |
| 5 | Reduced comfort / convenience function |
| 4 | Appearance issue — noticed by most |
| 3 | Appearance issue — noticed by some |
| 2 | Appearance issue — noticed by discriminating |
| 1 | No effect |

**Severity rates the EFFECT, not the mode or cause.** S=10 or S=9 means you must act regardless of O and D.

#### Occurrence (O) — likelihood the Failure Cause leads to the Failure Mode

| O | Failure Rate |
|---|-------------|
| 10 | ≥ 1 in 2 |
| 9 | 1 in 8 |
| 8 | 1 in 20 |
| 7 | 1 in 80 |
| 6 | 1 in 400 |
| 5 | 1 in 2,000 |
| 4 | 1 in 15,000 |
| 3 | 1 in 150,000 |
| 2 | 1 in 1,500,000 |
| 1 | Failure eliminated by prevention control |

O considers **prevention controls** already in place (poka-yoke, SPC, incoming inspection of material).

#### Detection (D) — effectiveness of detection controls before product reaches next customer

| D | Detection |
|---|-----------|
| 10 | No detection control |
| 9 | Control unlikely to detect |
| 8 | Control may detect |
| 7 | Control has low chance of detection |
| 6 | Control may detect — moderate |
| 5 | Control likely to detect |
| 4 | Control has good chance of detection |
| 3 | Control almost certain to detect |
| 2 | Control certain to detect — automatic rejection |
| 1 | Failure mode cannot occur (prevented) |

D considers **detection controls** already in place (gauging, inspection, poka-yoke).

#### Action Priority (AP) — replaces legacy RPN

Use the AP table (see [action-priority-ap](../action-priority-ap/) skill for full table):

| AP | Meaning | Required action |
|----|---------|-----------------|
| **H** (High) | Action required | Assign responsible owner + target date. Escalate if no improvement possible. |
| **M** (Medium) | Action recommended | Team should evaluate — reduction may be beneficial |
| **L** (Low) | No action required | Document rationale for no action |

**Critical rule:** S = 9 or 10 → AP is always H regardless of O and D.

**Ratings discipline:** All S/O/D ratings must be agreed by the cross-functional team — not assigned unilaterally by one engineer. Where team members disagree, document the rationale for the rating chosen. Ratings without team consensus are not acceptable for PPAP submission or customer OEM review.

---

### Step 6 — Optimization

For every H-AP item: define a corrective action.

For each action:
- Description of the action
- Responsible person (name, not function)
- Target completion date
- Re-assess S/O/D after action: new AP (revised)

**Priority for action type:**
1. **Prevent the cause** (best): eliminate the cause by design or poka-yoke
2. **Reduce occurrence**: add process control that makes the cause less likely
3. **Improve detection**: add or improve detection control (least preferred — doesn't prevent defect, only catches it)

Avoid the common trap of only improving detection (lowering D) — this catches defects but doesn't prevent them.

**Tracking discipline:** All actions must be logged in the PFMEA and tracked to closure with objective evidence (completed action description + implementation date + revised S/O/D ratings). Open H-AP items past their target date must be escalated to management with a documented reason for delay and a revised target date. A PFMEA with overdue open H-AP items is not acceptable for PPAP submission or OEM audit.

---

### Step 7 — Results Documentation

Final PFMEA deliverables:
- Completed PFMEA form with all 7 steps documented
- Summary of H-AP items and their actions (status: open/closed)
- Link to updated Control Plan (detection controls in PFMEA → control methods in CP)
- Link to updated Work Instructions (prevention controls → WI procedures)
- PFMEA revision history

**PFMEA → Control Plan linkage:**
Every detection control in the PFMEA must have a corresponding entry in the Control Plan. Every prevention control must be reflected in the Work Instruction.

## Validation checklist

Before releasing the PFMEA:
- [ ] All process steps from the PFD are in the Structure Analysis
- [ ] All Special Characteristics are identified and have S=9 or S=10
- [ ] Every H-AP item has an owner and a target date
- [ ] No H-AP items remain open without documented escalation reason
- [ ] Detection controls in PFMEA match the Control Plan
- [ ] Prevention controls in PFMEA match Work Instructions
- [ ] All Failure Causes are evidence-based (no unverified assumptions used as final causes)
- [ ] PFMEA review triggered by one of the mandatory events: process change, quality escape (post-8D update), or annual review (IATF 16949 §8.3.3.3)

## Output Format

At the start of each use, ask the user:

> "How would you like to receive the output?
> **A** — Structured Markdown (formatted tables and sections, ready to copy)
> **B** — Plain tables (simplified structure for Excel or Word)
> **C** — Narrative report (flowing text for a formal document or email)
>
> Default: A."

Adapt all output sections to the chosen format. If the platform or session context already defines a format preference, skip this question.

## Reference files

- [AIAG-VDA 2019 step-by-step guide](references/aiag-vda-2019.md)
- [Action Priority table](assets/ap-table.md)

## Changelog

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-01 | @RBraga01 | Initial release |
| 1.1 | 2026-06-03 | @RBraga01 | Expanded 7-step workflow with AP gate requirements and PPAP integration |
