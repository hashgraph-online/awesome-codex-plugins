---
name: aiag-vda-2019
type: reference
parent_skill: pfmea-process
author: RBraga01
version: "1.0"
status: approved
created: "2026-06-01"
last_updated: "2026-06-03"
updated_by: RBraga01
reviewed_by: RBraga01
license: MIT
---

# PFMEA — AIAG-VDA 2019 Reference

Reference for Process FMEA per the AIAG-VDA FMEA Handbook (2019 joint edition).
Use alongside the [pfmea-process](../SKILL.md) skill and the [ap-table](../assets/ap-table.md).

> **Scope:** This document covers reference logic — rating tables, failure chain rules, audit findings, and governance.
> For the step-by-step execution workflow, see [pfmea-process SKILL.md](../SKILL.md).

---

## The 7-Step Approach — Summary

| Step | Name | Key output |
|------|------|-----------|
| 1 | Planning and Preparation | FMEA header, scope, team, timeline |
| 2 | Structure Analysis | Process hierarchy: Item → Process Step → Work Element |
| 3 | Function Analysis | Function of each process step and work element |
| 4 | Failure Analysis | Failure Effect → Failure Mode → Failure Cause chains |
| 5 | Risk Analysis | S / O / D ratings → Action Priority (H / M / L) |
| 6 | Optimization | Actions for H-AP items, revised ratings |
| 7 | Results Documentation | Final PFMEA, Control Plan linkage, revision history |

---

## Step 2 — Structure Analysis

### Process hierarchy

```
Process Item          (e.g., Steering Column Assembly Line)
└── Process Step      (e.g., Station 3 — Torque tightening of bolt M8)
    └── Work Element  (e.g., Pneumatic driver, 4M inputs)
```

**4M work elements** for each process step:

| M | Examples |
|---|---------|
| Man | Operator, setter, maintenance technician |
| Machine | Press, robot, torque wrench, conveyor, fixture |
| Method | Work instruction, sequence, parameter settings |
| Material | Component, raw material, lubricant, consumable |

Every work element that can cause a failure mode should appear in the structure.

**Traceability rule:** Every Work Element listed here must map to at least one Failure Cause in Step 4. A work element with no associated failure cause indicates an incomplete analysis — missing failure paths are the most common source of undetected risk.

### Structure Analysis tips
- One row in the PFMEA per failure cause, not per failure mode
- If a process step has 3 failure modes and each has 2 causes → 6 rows minimum
- All process steps from the Process Flow Diagram (PFD) must appear

---

## Step 3 — Function Analysis

### Function statement format

> **Verb + Noun + Measurable Standard**

| Bad (incomplete) | Good (complete) |
|-----------------|----------------|
| "Tighten bolt" | "Tighten bolt M8 to 22 ± 2 Nm" |
| "Inspect parts" | "100% inspect dimension A to 25.0 ± 0.5 mm" |
| "Apply adhesive" | "Apply adhesive bead, width 4–6 mm, length 120 ± 5 mm" |

**Special Characteristics flag:**
All Special Characteristics (SC) from the drawing must be identified at this step.
Use the customer-specific symbol (◆ for Ford, ★ for GM, shield for VW, etc.).
SC failure modes always carry S = 9 or S = 10.

**Testability rule:** Every Function must be measurable — a verification method must exist. "Tighten correctly" is not acceptable; "Tighten to 22 ± 2 Nm, verified by torque wrench calibrated to ±5%" is. A function with no measurable standard cannot be rated for Occurrence or Detection in Step 5.

---

## Step 4 — Failure Analysis

### Failure chain direction

Work from Effect → Mode → Cause (not the other way around):

```
Failure Effect (FE): what the customer experiences
      ↑
Failure Mode (FM): how the process step fails its function
      ↑
Failure Cause (FC): why the failure mode occurs
```

### Failure Effect levels

**End-user effect** (most severe — S = 7–10):
The impact on the vehicle operator or end-user if the failure reaches the field.

**Manufacturing effect** (S = 1–6):
The impact on the next operation, the assembly line, or internal quality.

Both must be documented. Severity is rated based on the **end-user effect**.

### Failure Mode examples by process type

| Process type | Example failure modes |
|-------------|----------------------|
| Torquing / fastening | Under-torque, over-torque, cross-thread, wrong fastener |
| Welding / joining | Cold joint, missing weld, wrong position, insufficient penetration |
| Assembly | Missing component, wrong component, backwards installation, damaged during assembly |
| Inspection | False accept (bad part passes), false reject (good part fails) |
| Material handling | Wrong material loaded, contamination, incorrect FIFO |
| Machining | Out of tolerance (too big, too small), wrong surface finish, wrong geometry |

### Multiple causes per failure mode

Each failure cause gets its own row. For one failure mode, typical causes include:

**Machine:** tool worn, fixture misaligned, parameter drift, calibration expired
**Man:** procedure not followed, untrained operator, workstation ergonomics
**Method:** incorrect parameter in work instruction, ambiguous instruction
**Material:** incoming non-conformance, incorrect grade, contamination

**Failure Cause validation:** Failure Causes must be validated using structured root cause analysis (e.g., [5-Why](../../../problem-solving/5why-root-cause/)). Unverified assumptions — "probably," "may be," "could be" — are not acceptable as final Failure Causes. For post-escape PFMEA updates, the FC must match the validated root cause from the 8D or CAPA closure, not a revised team opinion.

This closes the system loop: **8D escape → 5-Why → validated FC → PFMEA update → Control Plan update → Work Instruction update.**

---

## Step 5 — Severity Rating Table

Severity rates the **impact of the Failure Effect on the customer** (end-user or next operation).
Severity is a property of the Failure Effect, not the Failure Mode or Cause.
**Severity does not change unless the design changes.**

| S | Criteria |
|---|---------|
| 10 | Failure affects safe vehicle operation or involves non-compliance with government regulation — without warning |
| 9 | Failure affects safe vehicle operation or involves non-compliance with government regulation — with warning |
| 8 | Loss of primary function (vehicle operable, primary function lost) |
| 7 | Degraded primary function (vehicle operable, primary function reduced) |
| 6 | Loss of comfort/convenience function |
| 5 | Degraded comfort/convenience function |
| 4 | Appearance or audible noise, vehicle operable, item does not conform — noticed by most customers (>75%) |
| 3 | Appearance or audible noise, vehicle operable, item does not conform — noticed by some customers (25–75%) |
| 2 | Appearance or audible noise, vehicle operable, item does not conform — noticed by discriminating customers (<25%) |
| 1 | No discernible effect |

**Critical rule:** S = 9 or S = 10 → AP = H regardless of O and D. No exceptions.

---

## Step 5 — Occurrence Rating Table

Occurrence rates the **likelihood that the Failure Cause leads to the Failure Mode**,
given current prevention controls.

| O | Failure rate | Criteria |
|---|-------------|---------|
| 10 | ≥ 1 in 2 | Certain — failure is almost inevitable |
| 9 | 1 in 8 | Very high |
| 8 | 1 in 20 | High |
| 7 | 1 in 80 | Moderately high |
| 6 | 1 in 400 | Moderate |
| 5 | 1 in 2,000 | Low |
| 4 | 1 in 15,000 | Low — isolated failures |
| 3 | 1 in 150,000 | Very low |
| 2 | 1 in 1,500,000 | Remote |
| 1 | < 1 in 1,500,000 | Failure eliminated by prevention control |

**Notes:**
- O = 1 requires a poka-yoke or elimination control that makes the cause physically impossible
- Use process capability data (Cp, Cpk) to set O where statistical data exists
- In the absence of data, use historical failure rates from similar processes

---

## Step 5 — Detection Rating Table

Detection rates the **effectiveness of current detection controls** at catching the failure mode
before product reaches the next customer (internal or external).

| D | Criteria |
|---|---------|
| 10 | No detection control — failure not detectable |
| 9 | Control unlikely to detect — indirect or random check |
| 8 | Control may detect — visual, non-systematic |
| 7 | Low chance of detection — manual inspection, sampling |
| 6 | May detect — systematic visual or manual, moderate capability |
| 5 | Control likely to detect — variable gauging, attribute gauging |
| 4 | Good chance of detection — systematic gauging, moderate automation |
| 3 | Almost certain to detect — automated control, high reliability |
| 2 | Control certain to detect — 100% automated inspection, auto-reject |
| 1 | Prevention control makes failure impossible — poka-yoke, design change |

**Notes:**
- D = 1 and D = 2 require automated detection (not human-dependent)
- 100% manual inspection by an operator ≈ D = 6 (accounting for human fatigue and error)
- Automated vision systems with calibrated sensitivity ≈ D = 2 or D = 3

**Ratings justification rule:** All S / O / D ratings must include a documented justification — process capability data (Cpk), historical failure rates, field return data, or engineering rationale. A rating without justification is an unverified estimate and will be challenged in OEM audits. Where available, use real process data (SPC, Cpk, field returns) in preference to estimated ratings.

---

## Step 6 — Optimization

### Action priority for H-AP items

**Rule:** every H-AP row must have either an action (owner + date) or a documented escalation.

**Preferred action types** (in order of preference):

1. **Error prevention (poka-yoke)** — physical impossibility of the failure (O reduced to 1)
2. **Process redesign** — eliminate the root cause by changing the process
3. **Reduce occurrence** — add or improve a prevention control
4. **Improve detection** — add or improve a detection control (last resort — does not prevent defects)

Avoid closing H-AP items by only improving D (detection). Auditors and customers look for this pattern
as a sign that the team is not addressing root causes.

### Revised ratings

After actions are implemented, re-rate S / O / D and compute the revised AP.
Document:
- Revised S (usually unchanged unless design changed)
- Revised O (should decrease if prevention control added)
- Revised D (should decrease if detection control added)
- Revised AP (should be M or L after H-AP actions)

### Action tracking and governance

All actions must be tracked to completion with objective evidence: implementation date, responsible person's confirmation, and revised S/O/D recorded in the PFMEA. Evidence of action completion (photo, calibration record, updated WI revision) must be archived.

**Escalation rule:** Open H-AP items past their target date must be escalated to management. Document: the reason for delay, the revised target date, and management acknowledgement. A PFMEA with overdue open H-AP items is not acceptable for PPAP submission or OEM audit.

---

## Step 7 — PFMEA to Control Plan Linkage

Every **detection control** in the PFMEA must have a corresponding entry in the Control Plan.
Every **prevention control** must be reflected in the Work Instruction.

| PFMEA field | → | Control Plan / WI field |
|------------|---|------------------------|
| Detection control | → | Control method (CP) |
| Control frequency | → | Sample size and frequency (CP) |
| Special Characteristic | → | SC symbol on CP and drawing |
| Prevention control | → | Process parameter / instruction step (WI) |

Failure to maintain this linkage is one of the most common IATF 16949 audit findings.

### Mandatory PFMEA review events (IATF 16949 §8.3.3.3)

The PFMEA must be reviewed and updated at each of the following events:

| Trigger | Required action | Timing |
|---------|----------------|--------|
| Quality escape confirmed (8D closed) | Update FC, ratings, and actions to match validated root cause | Within 30 days of 8D closure |
| Process change (equipment, method, material, layout) | Update structure, function, and failure analysis for changed elements | Before the change is released to production |
| Annual review (IATF minimum) | Review all H-AP items; confirm ratings are still current; check CP and WI alignment | At least once per calendar year |
| New customer-specific requirement | Review severity ratings and SC designations | Before next PPAP or submission |

A PFMEA that has never been updated since initial release is a red flag in any IATF or OEM audit.

---

## Common PFMEA Audit Findings

| Finding | Root cause | Fix |
|---------|-----------|-----|
| S = 9/10 with AP = M | AP table not applied correctly | Check AP table; S ≥ 9 always produces H |
| H-AP items with no owner or date | Optimization step skipped | Assign owner (name) and date to every H-AP row |
| Special Characteristics with S < 9 | Severity rated at manufacturing level, not end-user | Re-rate at end-user impact |
| Detection controls in PFMEA not in Control Plan | Steps 5 and 7 done in silos | Cross-check PFMEA and CP for every control |
| Prevention controls not in Work Instructions | WI not updated after PFMEA | Update WI revision, reissue, retain evidence |
| Occurrence rated without data justification | Guessing | Add reference to historical rate or Cpk data |
| PFMEA not updated after quality escape | Reactive updates missed | PFMEA must be revised within 30 days of a confirmed escape |
| Failure Causes are assumptions, not validated | 5-Why or RCA not performed | Validate each FC with structured analysis; post-escape FC must match 8D root cause |
| Ratings with no data justification | Team estimated without evidence | Add Cpk reference, historical rate, or engineering rationale to each rating |

---

## Global PFMEA Validation Checklist

Use at PFMEA release, PPAP submission, or audit preparation. All items must be confirmed before the PFMEA is considered complete.

| # | Item | Complete? |
|---|------|-----------|
| 1 | All process steps from the Process Flow Diagram are included in Structure Analysis | ☐ |
| 2 | Every Work Element maps to at least one Failure Cause in Step 4 | ☐ |
| 3 | All Functions are defined with Verb + Noun + Measurable Standard | ☐ |
| 4 | Every Function has a measurable verification method | ☐ |
| 5 | Failure chain direction is Effect → Mode → Cause for every row | ☐ |
| 6 | All Failure Causes are evidence-based — no unverified assumptions used as final causes | ☐ |
| 7 | For post-escape updates: FCs match the validated 8D/CAPA root cause | ☐ |
| 8 | All Special Characteristics identified and carry S = 9 or S = 10 | ☐ |
| 9 | S/O/D ratings include data justification (Cpk, historical rate, or engineering rationale) | ☐ |
| 10 | S/O/D ratings agreed by the cross-functional team and documented | ☐ |
| 11 | AP table applied correctly — S = 9 or 10 produces H regardless of O and D | ☐ |
| 12 | Every H-AP item has a named owner and target date | ☐ |
| 13 | No H-AP item is closed with detection improvement only (without written justification) | ☐ |
| 14 | All actions implemented and verified — revised S/O/D recorded with evidence | ☐ |
| 15 | No H-AP item is overdue without documented escalation to management | ☐ |
| 16 | Detection controls in PFMEA match corresponding entries in the Control Plan | ☐ |
| 17 | Prevention controls in PFMEA reflected in Work Instructions (current revision) | ☐ |
| 18 | PFMEA review triggered by one of: quality escape, process change, or annual review | ☐ |
