---
name: 8d-report-writing
description: >-
  Submit an 8D to a customer, format a Ford 8D report, BMW G8D, VW QMSS, or OEM complaint
  response for formal submission. Covers OEM-specific format requirements, evidence standards,
  and discipline-by-discipline writing rules for D0–D8. Use when preparing an 8D report for
  Ford, BMW, VW/Audi, Stellantis, or any customer requiring formal 8D closure.
license: MIT
metadata:
  author: RBraga01
  version: "1.1"
  iso-9001: "10.2"
  iatf-16949: "10.2.3"
  domain: quality-engineering
  subdomain: documentation
  industries: automotive,electronics
  status: approved
  created: "2026-06-01"
  last_updated: "2026-06-03"
  updated_by: migmcc
  reviewed_by: RBraga01
  standard_edition: "ISO 9001:2015 / IATF 16949:2016"
---

# 8D Customer Report Writing

## When to use

Use when an 8D investigation is complete and a formal report must be submitted to the customer. This skill covers the writing quality and format — the methodology is in [8d-problem-solving](../../problem-solving/8d-problem-solving/).

The 8D report is a legal and commercial document. It is used by the customer to:

- Verify their claim was addressed
- Confirm containment protected their production
- Audit your corrective action quality
- Assess your supplier quality level for BIQS scoring, PPAP status, and future business decisions

A poorly written report — even with good corrective actions — signals low quality maturity.

## OEM format references

| OEM | Format | Submission system |
|-----|--------|------------------|
| Ford | 8D (Ford 8D form) | Covisint / GSDB / portal |
| BMW | G8D (Global 8D) | SupplierPortal (SIM) |
| VW / Audi | QMSS (Lieferantenselbstauskunft) | SupplyOn |
| Stellantis (ex-FCA, PSA) | 8D | CQMS |
| Mercedes-Benz | 8D / ATC | SupplyOn |
| Toyota (TMMNA) | 8D or A3 | SMART |

Always download the **current customer template** from the portal before writing. Templates change. Always align with the specific customer format and mandatory fields — do not modify OEM templates.

---

## Required 8D Report Checklist

☐ Correct OEM template used (latest version — downloaded before writing)
☐ D2 fully quantified and matches the customer claim and NCR exactly
☐ D3 containment implemented with evidence — past tense only
☐ D3 containment active until D6 verification is complete
☐ D4 includes both occurrence and escape root causes, each validated with objective evidence
☐ D5 actions directly address each root cause (RCO and RCE referenced)
☐ D6 includes objective verification data with justified sample size
☐ D7 includes PFMEA, CP, WI updates with revision numbers, plus horizontal deployment
☐ D8 includes champion sign-off and customer notification of closure
☐ All dates are chronological and consistent across D0–D8
☐ All statements are supported by attached or referenced evidence
☐ No speculative, apologetic, or subjective language used
☐ Consistent tense: past for completed actions, present for current state

---

## Writing rules — discipline by discipline

### D0 — Emergency Response

Write a brief statement of whether a safety/regulatory issue was identified and what emergency action was taken.

Always state explicitly whether safety/regulatory risk is present or not — "No safety risk identified" or "Safety risk identified — [action]."

**Good:** "No safety risk identified. Customer notified by email (attached) on 2026-05-14. Ship-hold placed on supplier lot 2026-05-12-A, covering 1,700 units across 2 delivery notes."

**Bad:** "We were notified of the issue and responded quickly."

Evidence required: customer notification email, ship-hold record.

---

### D1 — Team

List names and functions. The customer wants to see cross-functional involvement.

**Good:** Include at least quality engineer, production supervisor, and process/design engineer. Identify the team leader and customer contact point (if applicable) clearly.

**Bad:** "The quality team investigated." (no names, no functions, no evidence of cross-functional approach)

---

### D2 — Problem Description

This is the most read section — if D2 is vague, the customer will reject the report.

D2 must match exactly the NCR and the customer claim description. Any inconsistency between D2, the NCR, and customer claim data is treated as a credibility failure.

**Required content:**

- Exact non-conformance with measured values and specification
- Part number + revision
- Customer's claim reference number
- Quantity: rejected / inspected / population at risk
- Detection point (customer incoming, field, production)
- First detection date

**Good:** "Connector housing flange thickness measured at 1.8 mm (specification: 2.2 ± 0.1 mm, DWG-12345 rev B). Defect detected at customer incoming inspection 2026-05-13. 47 non-conforming units of 200 inspected (23.5%). Customer claim ref: CL-2026-4471."

---

### D3 — Interim Containment Actions

The customer needs to know their production is protected. This is the first thing many SQEs read.

Containment must remain active until D6 verification is complete and effectiveness is confirmed.

**Required content:**

- What was done (sort, 100% inspection, ship-hold)
- When it was implemented (date — must be before D4, D5, D6)
- Who did it
- How effectiveness was verified (zero escapes since ICA, sort results)

**Good:** "100% inspection of all suspect stock at customer (200 units, all checked by 2026-05-14, 47 units rejected, 153 units accepted and released after re-inspection). Ship-hold on remaining 1,500 units in our warehouse, confirmed by logistics on 2026-05-14. Zero additional escapes since ICA implementation."

**Bad:** "We will perform 100% inspection going forward." (future tense is not containment — it's a promise)

---

### D4 — Root Cause Analysis

The most technically evaluated section. Customer SQEs specifically look for:

1. Is there a root cause of occurrence AND a root cause of escape?
2. Is the root cause specific enough (not generic "human error" or "supplier issue")?
3. Is it validated with objective evidence — not just logical reasoning?

Root cause must be supported by evidence (test, data, or experiment), not logical reasoning alone.

**Required content:**

- Root cause of occurrence (why did the defect happen?) — with the 5-Why chain
- Root cause of escape (why was it not detected?) — with the 5-Why chain
- Validation method (how was the root cause confirmed — test, data, reproduction experiment?)

**Good — root cause of occurrence:**
> D4 Why chain (occurrence):
> 1. Why flange thickness OOS? → Insufficient material removed at milling step
> 2. Why insufficient material removed? → Feed rate was 0.05 mm/rev instead of 0.03 mm/rev
> 3. Why wrong feed rate? → CNC programme parameter changed during tool changeover on 2026-05-10
> 4. Why was change not detected? → No parameter verification step after tool changeover
> Root cause: CNC programme parameter verification is not required by the work instruction after tool changeover.
> Validated by: Reproduction test confirmed defect at 0.05 mm/rev; zero defects at 0.03 mm/rev.

**Bad:** "Root cause: operator error. The operator changed the wrong setting."

---

### D5 — Corrective Actions

Each corrective action must directly address the root cause from D4 — reference whether it addresses the occurrence root cause (RCO) or escape root cause (RCE).

**Required content:**

- Description of the corrective action
- Which root cause it addresses (RCO or RCE)
- Implementation date
- Responsible person

**Good:** "Added mandatory CNC parameter verification step to WI-Milling-Station-2 (rev C, attached): operator must verify feed rate = 0.03 mm/rev by reading the CNC display before and after any tool changeover, and record in the batch log. [Addresses RCO]"

**Bad:** "We will retrain operators and improve our process."

---

### D6 — Implementation and Verification

The customer needs objective proof that the actions worked, not just that they were implemented.

Verification sample size must be justified based on defect rate and risk — not chosen arbitrarily.

**Required content:**

- Implementation date for each PCA
- Verification data (production run results, before/after comparison)
- Justified sample size
- ICA removal date and confirmation

**Good:** "PCA implemented 2026-06-04. Verification run: 500 units produced with revised WI (sample size justified by 0.235 defect rate, 95% confidence), 100% measurement of flange thickness — all within specification (mean 2.19 mm, ±0.04 mm, within ±0.1 mm tolerance). Zero defects detected. ICA (100% inspection) removed 2026-06-10 based on verified zero-defect production run."

**Bad:** "The corrective action has been implemented. No defects were found."

---

### D7 — Prevention (Systemic)

This shows the customer you manage your quality system properly, not just firefight.

All document updates must be implemented and active in production — not only documented in the 8D.

**Required content:**

- PFMEA revision (document number, revision letter, date)
- Control Plan revision (document number, revision letter, date)
- Work Instruction revision (document number, revision letter, date)
- Horizontal deployment (other lines, products, suppliers assessed and addressed)
- Lessons learned

**Good:** "PFMEA-Milling-St2 updated to rev D (attached): failure mode 'incorrect feed rate after changeover' added, O=4, D=3, AP=L. CP-Milling-St2 updated to rev G (attached): parameter check added post-changeover. WI-Milling-St2 updated to rev C (attached). Horizontal deployment: 3 similar CNC lines assessed — same parameter verification added to WI-CNC-01, WI-CNC-02, WI-CNC-03."

---

### D8 — Team Recognition

Brief close statement. Professional and factual.

Customer must be formally notified of closure with the final 8D report.

**Good:** "8D closed on 2026-06-15 with champion approval. Customer notified of closure with final 8D on 2026-06-15 (ref: email attached). Team formally recognised at department meeting 2026-06-15. 8D report filed in quality record system under QR-2026-0047."

---

## Tone and language

| Avoid | Use instead |
|-------|-------------|
| "We are sorry for the inconvenience" | Factual description of what happened and what was done |
| "Probably caused by..." | "Root cause confirmed by [test]: ..." |
| "We will try to prevent..." | "Prevention implemented on [date]: ..." |
| "The operator made a mistake" | "The work instruction did not specify the required parameter" |
| "Going forward, we will..." | Specific action with date implemented |

Use consistent tense: past for completed actions, present for current state.

An 8D report is a technical document. Apologetic or vague language reduces credibility with customer SQEs.

All statements in the 8D must be supported by attached or referenced evidence. Attach all supporting evidence: photos, measurement data, WI revisions, PFMEA updates, and test results.

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

- [OEM-specific requirements](references/oem-formats.md)

## Changelog

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-01 | @RBraga01 | Initial release |
| 1.1 | 2026-06-03 | @migmcc | Added OEM format requirements and customer submission checklists |
