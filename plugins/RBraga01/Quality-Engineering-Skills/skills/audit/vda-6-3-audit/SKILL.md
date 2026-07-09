---
name: vda-6-3-audit
description: >-
  VDA 6.3 Process Audit — conduct or prepare for a process audit using the VDA 6.3 methodology,
  evaluate process elements P1–P7, calculate degree of fulfillment, classify findings, and generate
  an audit report. Use when a customer requests a VDA 6.3 audit, when auditing a supplier's
  manufacturing process, or when preparing for a VDA process audit visit. Covers VDA 6.3 4th edition (2023).
license: MIT
metadata:
  author: RBraga01
  version: "1.1"
  iatf-16949: "9.2.2"
  vda-reference: "VDA 6.3 Process Audit 4th Edition 2023"
  domain: quality-engineering
  subdomain: audit
  industries: automotive,electronics,general
  status: approved
  created: "2026-06-06"
  last_updated: "2026-06-06"
  updated_by: migmcc
  reviewed_by: RBraga01
  standard_edition: "VDA 6.3 Process Audit 4th Edition (2023)"
---

# VDA 6.3 Process Audit

## When to use

Use this skill when:
- Conducting a VDA 6.3 process audit at a supplier or internally
- Preparing for an OEM process audit visit (BMW, VW, Audi, Mercedes, Porsche, Stellantis)
- Auditing a new supplier during qualification
- Responding to a customer concern by conducting a focused process audit
- Evaluating a supplier's manufacturing process capability before SOP

## Prerequisites

- Customer audit scope (which process/product to audit)
- VDA 6.3 question catalogue (the auditor works from the standard questions)
- Process Flow Diagram, PFMEA, Control Plan, and Work Instructions for the audited process
- Access to the production area, equipment records, personnel, and quality records

## Workflow

### Step 1 — VDA 6.3 Structure Overview

VDA 6.3 is organised into 7 process elements (P1–P7):

| Element | Name | Applies to |
|---------|------|-----------|
| P1 | Potential Analysis | New suppliers — evaluates readiness before series production |
| P2 | Project Management | APQP and product/process development process |
| P3 | Planning the Product and Process Development | Design and process planning activities |
| P4 | Supplier Management (Purchasing) | Sub-supplier control and qualification |
| P5 | Process Input / Series | Incoming materials and components |
| P6 | Process Execution / Customer Satisfaction / Service | The manufacturing process itself |
| P7 | Customer Support / Customer Satisfaction / Service | Delivery performance, escalation, field support |

**For a focused series production audit (most common):** P5, P6, P7 are mandatory. P1–P4 are added for new supplier qualification or product launch audits.

---

### Step 2 — Rating system

Every question in VDA 6.3 is scored on a 0–10 scale:

| Score | Meaning |
|-------|---------|
| **10** | All requirements fulfilled — systematic, effective, and documented evidence exists |
| **8** | Requirement largely fulfilled — minor gaps, no systematic risk |
| **6** | Requirement partially fulfilled — deviations exist, limited risk |
| **4** | Requirement insufficiently fulfilled — significant gaps, risk to quality |
| **2** | Requirement not fulfilled — systematic failure, high risk |
| **0** | Not applicable OR not fulfilled with no evidence |

A score of **4 or less** on any question is a deficiency and must be documented with a finding and corrective action requirement.

---

### Step 3 — Degree of Fulfillment calculation

For each process element:

**Element score (%) = (Sum of all question scores) / (Maximum possible score) × 100**

**Weighting system (critical):** Each question in the VDA 6.3 question catalogue has a pre-assigned weighting factor of 1, 2, or 3. These weights are fixed in the standard — the auditor cannot change them. Questions covering safety-critical topics (error-proofing, special characteristics control, non-conformance segregation) typically carry weight 2 or 3. The maximum possible score per question = 10 × weighting factor.

To calculate the degree of fulfillment correctly:
- Use the official VDA 6.3 question catalogue, which lists each question with its weight
- Sum (score × weight) for all applicable questions in the element
- Divide by the sum of (10 × weight) for all applicable questions
- Do not average raw scores — applying equal weight to all questions is a calculation error that produces incorrect element ratings

If a question is not applicable (N/A), it is excluded from both the numerator and denominator.

#### VDA 6.3 rating thresholds

| Degree of fulfillment | Rating | Interpretation |
|----------------------|--------|----------------|
| ≥ 90% | A | Process suitable for series production — no significant concerns |
| 75% – < 90% | B | Conditionally suitable — corrective actions required within agreed timeframe |
| < 75% | C | Not suitable — series production release blocked until corrective action complete |

A rating of **C blocks SOP** — the customer will not release the supplier for series production until re-audit achieves at least B.

---

### Step 4 — P6 — Process Execution (the core audit)

P6 is the most extensive element and covers the actual manufacturing process. Key areas:

**P6.1 — Process inputs**
- Are incoming materials and components controlled?
- Are change management procedures in place and effective?
- Are specifications current and accessible at point of use?

**P6.2 — Personnel**
- Are operators qualified and trained for the tasks they perform?
- Are training records current?
- Is a qualification matrix maintained and used?

**P6.3 — Resources (equipment, tools, gauges)**
- Is equipment maintained per a preventive maintenance plan?
- Are calibration records current for all measurement equipment?
- Are work instructions present at every workstation and at the correct revision?

**P6.4 — Failure mode prevention (error-proofing)**
- Are poka-yoke devices in place for all High-AP failure modes?
- Are error-proofing devices checked at the correct frequency?
- Is the check result documented?

**P6.5 — Quality inspections and tests**
- Are incoming inspection, in-process inspection, and final inspection defined and performed?
- Are inspection records maintained and traceable?
- Is SPC in place for all special characteristics?

**P6.6 — Non-conformance management**
- Is non-conforming material identified, segregated, and controlled?
- Is there a defined reaction plan for out-of-control conditions?
- Are non-conformances escalated to quality and documented?

**P6.7 — Continuous improvement**
- Are quality KPIs tracked (reject rate, scrap, rework, OEE)?
- Are improvement actions driven by data?
- Are lessons learned captured and applied?

---

### Step 5 — Conduct the audit

**Pre-audit:**
- Request all relevant documentation: Process Flow, PFMEA, Control Plan, WIs, maintenance records, calibration records, training records
- Review and identify gaps before the site visit
- Confirm auditor qualification: VDA 6.3 audits require a trained, qualified auditor — internal auditors must hold a recognised VDA 6.3 auditor qualification (VDA QMC certification or OEM-equivalent). An unqualified person conducting the audit invalidates the result.
- Confirm auditor independence: the auditor must not have direct responsibility for the process being audited. Self-assessment by the process owner is not a substitute for an independent audit.

**Opening meeting:**
- Confirm scope, timing, and audit plan
- Introduce audit team and request the process owner to accompany

**Process walk (the audit):**
- Follow the process flow physically — start from incoming material, end at shipment
- For each step: observe, ask, verify records
- Ask: "Show me the record for this" — never accept verbal confirmation
- Score each question in real time; document evidence (positive and negative)

**Findings classification:**
- **Score 6:** Partial fulfilment — finding documented, corrective action required; deadline typically 90 days
- **Score 4:** Insufficient fulfilment — significant gap, represents active risk to quality; escalate deadline; customer OEMs often treat score-4 findings on critical questions (P6.4, P6.5, P6.6) as major deficiencies requiring immediate corrective action
- **Score 2:** Not fulfilled — systematic failure, high risk; corrective action with accelerated timeline required before next delivery
- **Score 0:** No evidence / not implemented — blocking; re-audit required before SOP release (if P1 applicable)

**Closing meeting:**
- Present scores and degree of fulfillment per element
- Confirm overall rating (A, B, or C)
- Agree on corrective action deadlines (typically 90 days for B-rating findings; accelerated for score-2 and score-4 findings)
- For B rating: schedule a follow-up audit or evidence review within 3 months to verify corrective actions are implemented — do not close the audit without this commitment in writing
- Confirm re-audit requirements if applicable (mandatory for C rating)

---

### Step 6 — Audit report structure

The VDA 6.3 report must contain:

1. Audit information: date, location, auditor, auditee, scope
2. Degree of fulfillment per element (P1–P7 as applicable)
3. Overall rating (A, B, C)
4. Finding list: for each score ≤ 6 — question, observation, evidence, score, deadline
5. Positive findings: best practices worth noting
6. Corrective action plan (CAP): supplier-signed, with root cause and due date per finding
7. Re-audit requirement if C rating

---

## Validation criteria

A VDA 6.3 audit is complete when:
- All applicable elements (P5, P6, P7 minimum for series) have been scored
- All findings (score ≤ 6) are documented with evidence
- Degree of fulfillment calculated and overall rating stated
- Corrective action plan signed by supplier quality management
- Re-audit scheduled if rating is C

## Common mistakes

- Auditor accepts verbal confirmation as evidence — always request the record
- Skipping the process walk and only reviewing documents — P6 requires observation of the live process
- Not documenting positive evidence — the report must balance findings and strengths
- Calculating degree of fulfillment without applying question weights
- Not confirming error-proofing device checks are being performed at the required frequency
- Closing meeting without confirming the corrective action deadline in writing
- Rating B without scheduling a follow-up to verify corrective actions are implemented

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
| 1.1 | 2026-06-06 | @migmcc | Expanded weighting system explanation in Step 3; added auditor qualification and independence requirements; improved findings classification (score 4 vs 6 distinction); added B-rating follow-up timeline |
