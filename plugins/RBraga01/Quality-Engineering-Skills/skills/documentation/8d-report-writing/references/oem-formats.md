---
name: oem-formats
type: reference
parent_skill: 8d-report-writing
author: RBraga01
version: "1.0"
status: approved
created: "2026-06-01"
last_updated: "2026-06-03"
updated_by: migmcc
reviewed_by: RBraga01
license: MIT
---

# OEM 8D Report Formats — Reference

Differences between OEM-specific 8D submission formats.
Use alongside the [8d-report-writing](../SKILL.md) skill.

---

## Format Comparison Overview

> This table is a summary. Always confirm requirements in the latest OEM template and CSR before submission.

| Element | Ford TOPS-8D | BMW G8D | VW QMSS | GM Global 8D | Stellantis |
|---------|-------------|---------|---------|-------------|-----------|
| D0 field | Yes — ERA | Yes | Yes | Optional | Recommended |
| Is/Is-Not | Mandatory | Optional | Mandatory | Recommended | Recommended |
| Two root causes (occ + escape) | Mandatory | Mandatory | Mandatory | Mandatory | Mandatory |
| D7 horizontal deployment | Mandatory | Mandatory | Mandatory | Recommended | Recommended |
| Champion sign-off (D8) | Mandatory | Mandatory | Mandatory | Mandatory | Mandatory |
| Submission system | GQTS / SupplierPortal | SRM / BQMS | FORMEL Q / SQMS | Covisint / Supplier Portal | SQS Portal |
| Typical response time (D3 ICA) | 24 h (critical) / 5 days | 24 h (critical) / 8 days | 24 h (safety) / 5 days | 24 h / 5 days | 24 h / 5 days |
| PPM tracking integration | Yes | Yes | Yes | Yes | Yes |

---

## Ford — TOPS-8D

**Full name:** Team Oriented Problem Solving — 8 Disciplines

### Key requirements

**D0 — Emergency Response Actions (ERA)**

- Mandatory field in TOPS-8D form
- ERA must include: immediate action taken, date, responsible person, confirmation that suspect stock is identified
- ERA is evaluated before the 8D response timer starts for D3
- Missing or weak ERA may result in immediate rejection before technical review

**D2 — Problem Description**

- Is/Is-Not is a mandatory structured field in the Ford form (not free text)
- Problem description must reference the customer symptom as reported (verbatim from the concern)
- Ford Concern ID must be referenced

**D4 — Root Cause**

- Must explicitly separate root cause of occurrence and root cause of non-detection
- "Verification method" is a mandatory sub-field — what test confirmed this is the root cause

**D6 — Verification**

- Ford specifies minimum run quantity for different product types
- Include SPC data or inspection records showing before/after comparison

**D7 — Systemisation**

- Must reference specific PFMEA revision number after update
- Must reference specific Control Plan revision number after update
- "Lessons learned shared with" is a mandatory field — names or product families listed

**Submission timing**

- Safety defects: D3 within 24 hours of acknowledgement
- Non-safety defects: Initial response within 5 business days, full 8D within 30 days
- Delays must be proactively communicated to the Ford SQE with justification
- Always check the current Ford CSR (Customer-Specific Requirements) for updates

---

## BMW — G8D

**Full name:** Global 8D (BMW Group)

### Key differences from standard 8D

**Structured problem statement in D2**

BMW's G8D form has structured fields for:

- "Problem as described by customer" (verbatim)
- "Problem as found at supplier" (your own investigation)
- "Defect rate at customer" (PPM or %)
- "Defect rate in your process" (internal data)

**D4 — Separate cause fields**

BMW explicitly separates:

- "Why did the defect occur?" (occurrence root cause)
- "Why was the defect not detected?" (escape root cause)
- Each has its own 5-Why section in the form

**D5 / D6 — Action effectiveness**

- BMW requires a "lessons learned" connection in D5: which existing failure mode / FMEA entry was this related to?
- D6 requires evidence that the FMEA and Control Plan were actually updated (revision numbers)

**D7 — Similar products**

BMW requires explicit documentation of:

- Which similar BMW part numbers were assessed for the same root cause
- What was found / what actions were taken for each

**8D presentation**

For premium defects (safety, significant warranty cost), BMW may require a live 8D presentation at the supplier quality engineer's request. The written 8D is the basis — prepare for verbal Q&A. Reports must be consistent with any presented data — discrepancies between written and verbal responses are treated as non-compliance.

**Submission system:** SRM (Supplier Relationship Management) or BQMS depending on BMW division

---

## VW / Audi — QMSS / FORMEL Q

**Full name:** Quality Management Supplier System (VW Group)

### Key requirements

**Immediate notification (D0)**

VW requires notification within 24 hours for safety-related defects, and within 5 days for non-safety defects. Notification must include: part number, quantity affected, initial containment status.

**D2 — Is/Is-Not**

FORMEL Q form has a mandatory Is/Is-Not structured section. Each dimension (what, where, when, how many) must be completed. Leaving fields empty is not accepted.

**D4 — Causal chain**

VW uses a "causal chain" format:

- Level 1: Direct cause (the immediate failure mechanism)
- Level 2: Systemic cause (why the direct cause was possible)
- Level 3: Escape cause (why the detection system failed)

All three must be answered.

**D7 — Process / product audit**

After a major defect, VW may require a formal process audit of the affected production line. The audit result and the resulting actions are referenced in D7.

**Secured quantity (FORMEL Q field)**

A unique VW requirement: in D3, document the "secured quantity" — the number of confirmed-good parts available to ship while the non-conforming stock is being managed. Missing secured quantity may result in rejection of D3 containment.

**Submission timing:** initial response 24 hours; full 8D within 25 working days (check current CSR)

---

## GM — Global 8D

### Key requirements

**BIQS integration**

GM's Supplier Quality system (BIQS — Become Involved in Quality Systems) links 8D status to the supplier's BIQS score. Open 8Ds and late 8Ds directly reduce the supplier score. Late 8D submissions impact supplier performance score and escalation status.

**D7 — Lessons learned register**

GM requires lessons learned to be entered into the supplier's own lessons learned register, and a reference to that register entry in D7.

**Verification requirements (D6)**

GM specifies minimum quantities for different defect types. Always check the current GM Supplier Quality Reference Manual (SQRM) for the applicable threshold.

**Submission timing:** D3 acknowledgement within 24 hours; full 8D within 30 days

---

## Stellantis — MAQMSR 8D

### Key requirements

**MAQMSR framework**

Stellantis follows the MAQMSR (Manufacturing Assurance Quality Management System Requirements). 8D is the mandatory problem-solving format for customer-reported concerns.

**SQE approval for H-AP with no action**

If a PFMEA H-AP item has no corrective action (documented management acceptance of residual risk), Stellantis SQE must approve the acceptance document before D8 can close. Closure without SQE approval for H-AP acceptance is not valid.

**Submission timing:** 24 hours for D0/D3 notification; 30 days for full 8D; extensions require SQE approval

---

## Timing Requirements — Cross-OEM

| Event | Ford | BMW | VW | GM | Stellantis |
|-------|------|-----|----|----|-----------|
| D3 ICA (safety) | 24 h | 24 h | 24 h | 24 h | 24 h |
| D3 ICA (non-safety) | 5 days | 8 days | 5 days | 5 days | 5 days |
| Full 8D | 30 days | Check CSR | 25 WD | 30 days | 30 days |

Delays in D3 or final 8D submission must be proactively communicated to the OEM SQE with justification before the deadline passes — do not wait to be chased.

---

## Common OEM Submission Mistakes

| Mistake | Impact | Fix |
|---------|--------|-----|
| Submitting in future tense ("will be implemented") | 8D rejected — D3 and D6 must be past tense with evidence | Verify implementation before submission |
| Missing D0 / ERA field | 8D returned for revision | Always complete D0 even if brief |
| "Human error" as root cause | D4 rejected by SQE | Always go systemic — what in the system allowed the error |
| D7 without PFMEA/CP revision numbers | Audit finding | Include revision numbers and dates in D7 |
| Sending own template instead of OEM form | Submission rejected | Always use the current OEM form — download before each submission |
| Missing champion signature (D8) | 8D not formally closed | Obtain sign-off before submitting closure |
| Mismatch between NCR, 8D, and customer claim data | Credibility failure / rejection risk | Verify D2 matches NCR and claim exactly |

Incomplete or non-compliant 8Ds are typically returned by OEMs and may negatively affect supplier performance ratings.

---

## Version and Submission Governance

- Maintain a controlled copy of each submitted 8D with version number and submission date
- Ensure consistency between NCR, customer complaint, and 8D report data before submission
- Always confirm template version before submission — check the template revision/date field

---

## Requesting Current OEM Templates

OEM forms update regularly. Always download the current version from:

- **Ford**: Ford Supplier Portal → Quality → TOPS-8D template
- **BMW**: SRM → Supplier Quality → G8D template
- **VW**: FORMEL Q portal → QMSS → Document download
- **GM**: GM Supplier Portal → Supplier Quality → Global 8D
- **Stellantis**: SQS Portal → Quality Documents → 8D template

Do not use a template downloaded more than 12 months ago without checking for updates. Always confirm the template revision/date before submission.

---

## 8D Submission Checklist (OEM)

☐ Correct OEM template used (latest version confirmed)
☐ D0 / ERA completed (if required by OEM)
☐ D2 matches customer claim exactly (verbatim where required)
☐ D3 containment implemented with evidence (past tense)
☐ Secured quantity documented (VW/Audi requirement)
☐ D4 includes both occurrence and escape root causes — each validated with objective evidence
☐ D5 actions directly linked to root causes (RCO and RCE)
☐ D6 includes objective verification data with justified sample size
☐ D7 includes PFMEA, CP, WI updates with revision numbers — all active in production
☐ D7 includes lessons learned register entry and horizontal deployment to similar products
☐ D8 includes champion sign-off
☐ All OEM-specific mandatory fields completed (Is/Is-Not, secured quantity, lessons learned, etc.)
☐ All supporting evidence attached (photos, data, revised documents)
☐ Dates are chronological and consistent across all disciplines
☐ Controlled copy retained with version and submission date
