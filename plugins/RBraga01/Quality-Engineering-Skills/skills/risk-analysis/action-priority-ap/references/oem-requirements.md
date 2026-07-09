---
name: oem-requirements
type: reference
parent_skill: action-priority-ap
author: RBraga01
version: "1.0"
status: approved
created: "2026-06-01"
last_updated: "2026-06-03"
updated_by: migmcc
reviewed_by: RBraga01
license: MIT
---

# OEM Action Priority Requirements — Reference

OEM-specific requirements for Action Priority (AP) in PFMEA and DFMEA.
Use alongside the [action-priority-ap](../SKILL.md) skill.

---

## Why OEM Requirements Override General AIAG-VDA Guidance

This document complements AIAG-VDA guidelines. In case of conflict, OEM-specific requirements always take precedence.

The AIAG-VDA FMEA Handbook 2019 defines the AP framework as a minimum standard.
Each OEM publishes Customer-Specific Requirements (CSR) that may:
- Set stricter thresholds for mandatory action
- Define deadlines for closing H-AP items before milestones (PPAP, SOP)
- Require specific documentation formats for H-AP closure
- Add OEM-specific escalation paths when actions are not feasible

**CSR requirements are binding contractual obligations, not guidelines.**

Always check the current CSR. CSRs are updated annually or more frequently.

---

## Required OEM AP Compliance Checklist

☐ All H-AP items have an assigned owner and target date
☐ All H-AP items are either closed (action implemented + verified) or formally escalated with OEM approval
☐ All no-action decisions have OEM-required approval (SQE or equivalent) — documented
☐ All H-AP items are addressed (closed or formally approved) before PPAP submission
☐ Revised AP reflects implemented and verified actions — not planned actions
☐ Special Characteristics meet OEM-specific requirements (Cpk thresholds, inspection methods)
☐ FMEA updated after latest quality escape or field failure
☐ All actions, approvals, and escalations are documented and retained as audit evidence
☐ H-AP status reviewed at every project milestone (design review, process review, PPAP)

---

## Ford — AP Requirements

**Source document:** Ford Customer-Specific Requirements for IATF 16949

### H-AP mandatory actions
- Every H-AP item must have a corrective action assigned, with a named responsible engineer and a target date
- If no improvement is technically possible: document an **Engineering Justification (EJ)**
  - EJ must be signed by a qualified engineer
  - EJ must include a risk assessment and monitoring plan (where applicable)
  - EJ must be reviewed and approved by the Ford SQE (Supplier Quality Engineer)
  - Without an approved EJ, the FMEA is considered non-compliant

### PPAP submission requirements
- All H-AP items must be addressed (action completed or EJ approved) before PPAP Level 3 submission
- Unaddressed H-AP items at PPAP result in conditional approval at best, rejection at worst

### Special Characteristics
- Ford uses ◆ (safety characteristics) and ▲ (significant characteristics)
- ◆ characteristics: S must be 9 or 10; AP must be H; 100% inspection or mistake-proofing required
- ▲ characteristics: SPC or equivalent statistical control required

### Annual FMEA review
- Ford CSR requires PFMEA and DFMEA review at minimum annually
- H-AP items from the previous review that remain open must have a documented status update

---

## GM — AP Requirements

**Source document:** GM Supplier Quality Reference Manual (SQRM)

### BIQS integration
- GM's Supplier Quality scoring system (BIQS) tracks open H-AP items as a supplier performance metric
- Suppliers with unaddressed H-AP items at PPAP submission receive BIQS score deduction
- H-AP items open >90 days without documented progress receive escalation flags
- BIQS scoring impact must be monitored as part of supplier performance management

### PPAP requirements (BIQS context)
- All H-AP items must be closed before Level 3 PPAP
- "Closed" means: action implemented AND verified (revised AP documented with evidence)
- Accepted derogation: H-AP items with documented management acceptance + residual risk quantification

### Special Characteristics (GM)
- GM uses ◆ (safety), ● (key product characteristic), and YC/YS (supplier-controlled SCs)
- All ◆ characteristics: AP must be H; automatic rejection/sorting or poka-yoke required
- Level 4 or 5 PPAP required for safety characteristics (◆)

---

## VW / Audi — AP Requirements

**Source document:** FORMEL Q — Konkret (VW Group Supplier Quality Requirements)

### AP = H — mandatory action statement
VW requires that every H-AP item has a formal action statement:
- Description of the action
- Responsible engineer (name, not just function)
- Target date
- Verification criterion

### Formal acceptance when no action is possible
- No-action acceptance requires a formal document signed by:
  - Supplier's responsible engineer
  - Supplier's quality manager
  - VW SQE countersignature
- Without VW SQE countersignature, the H-AP item is considered open
- Time-bound commitments must include interim risk containment measures

### SOP freeze implication
- Production launch (SOP — Start of Production) cannot proceed with open H-AP items
- Exception: written time-bound commitment signed by both supplier management and VW SQE

### Special Characteristics (VW)
- VW uses D (safety), KM (quality feature), and I (product feature) classification
- All D-characteristics: AP must be H; 100% automated inspection or poka-yoke mandatory
- KM characteristics: SPC with Cpk ≥ 1.67 required (not 1.33)

---

## BMW — AP Requirements

**Source document:** BMW Group Standard QM 10005 / BQMS requirements

### Open issues list
- BMW requires all H-AP items to appear on a formal "Open Issues List" maintained by the supplier
- The list must be shared with the BMW SQE at each project gate review
- H-AP items on the open issues list are tracked until formally closed with evidence
- Open Issues List must be version-controlled and traceable across project phases

### Gate review integration
- BMW uses project gate reviews (Concept, Design, Pre-Series, Ramp-Up, SOP)
- At each gate: all H-AP items must be either closed or have a formally accepted action plan
- Unaddressed H-AP items block gate approval

### Residual risk acceptance
- BMW does not routinely accept residual H-AP risk without engineering justification
- Justification must include: quantified residual risk, monitoring plan, and BMW SQE sign-off
- Safety-related H-AP (S=9 or S=10) residual risk acceptance requires BMW engineering approval

### Special Characteristics (BMW)
- BMW uses Merkmal (M) for safety and E for emission-relevant
- M-characteristics: Cpk ≥ 1.67 and 100% automated inspection required
- AP must be H for all M-characteristic failure modes

---

## Stellantis — AP Requirements

**Source document:** MAQMSR (Manufacturing Assurance Quality Management System Requirements)

### H-AP item escalation path
- If no action is feasible: supplier quality manager escalates to Stellantis SQE
- Stellantis SQE reviews and either approves residual risk acceptance or requires alternative action
- No unilateral supplier decision on H-AP "no action" — SQE approval always required
- SQE approval must be documented and retained as audit evidence

### PPAP timing
- All H-AP items must be addressed before PPAP submission
- "Addressed" = action implemented + evidence available, or formal SQE-approved no-action rationale

---

## OEM Comparison Table — H-AP Closure Requirements

| Requirement | Ford | GM | VW | BMW | Stellantis |
|-------------|------|----|----|-----|-----------|
| Named responsible engineer | Yes | Yes | Yes | Yes | Yes |
| Target date mandatory | Yes | Yes | Yes | Yes | Yes |
| H-AP must close before PPAP | Yes (or EJ) | Yes | Yes (or SQE) | Yes (or gate) | Yes (or SQE) |
| No-action requires OEM countersignature | Yes (EJ + SQE) | Case by case | Yes | Yes | Yes |
| H-AP items tracked on formal list | GQTS | BIQS | FORMEL Q | Open Issues List | SQS |
| Annual FMEA review of open H-AP | Yes | Yes | Yes | Yes | Yes |
| Residual risk acceptance allowed | Conditional (EJ) | Conditional | Conditional (SQE) | Rare (SQE) | Conditional (SQE) |

---

## Residual Risk Acceptance — Governance

When no corrective action is achievable, residual risk acceptance must include:
- Written justification explaining why no improvement is technically or economically feasible
- Risk assessment of the residual risk (likelihood × severity estimate)
- Mitigation or monitoring plan (detection controls, containment, periodic review)
- OEM approval (SQE countersignature where required by CSR)
- Document retention: this record must be available for audits and PPAP review

H-AP status must be reviewed at every project milestone (design review, process review, PPAP) to confirm that open items are still tracked and approved.

---

## Practical Guidance — Applying AP in FMEA Reviews

### Before PPAP submission
1. Print or export all H-AP rows from the PFMEA/DFMEA
2. For each row: confirm action is implemented (past tense) with evidence
3. Confirm revised AP is documented (new S/O/D ratings with the actions in place)
4. If any H-AP remain without action: prepare the OEM-specific no-action justification document and obtain OEM SQE signature before submission

### During an audit
If an auditor challenges an AP rating:
1. Walk through the AP table with the auditor using S, O, and D values
2. Show the evidence for O rating (failure rate data or Cpk) and D rating (inspection records, test results)
3. For H-AP items, show the action status (implemented with date and evidence, or formal escalation document)
4. Never argue that an H-AP was "acceptable as-is" without a signed justification — this is an automatic major finding

### After a quality escape
When a field failure or customer complaint traces to a failure mode in the PFMEA:
1. Update the O rating to reflect actual field failure rate (will likely increase)
2. Check the AP — it may change from M to H after the O update
3. If it becomes H: immediately assign an action, even if the PFMEA was previously approved
4. Notify the OEM SQE of the PFMEA update if the escape was an OEM-reported incident
