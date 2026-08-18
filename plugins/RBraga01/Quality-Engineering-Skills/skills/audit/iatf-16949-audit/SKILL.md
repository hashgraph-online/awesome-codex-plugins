---
name: iatf-16949-audit
description: >-
  Conduct an IATF audit, check supplemental requirements, or prepare for a manufacturing
  process audit or IATF 16949:2016 third-party assessment. Covers customer-specific
  requirements (CSR), all 16 automotive supplemental clauses, and the three required audit
  types: QMS audit, manufacturing process audit, and product audit. Use for internal IATF
  audits or supplier quality audits at automotive organisations.
license: MIT
metadata:
  author: RBraga01
  version: "1.1"
  iatf-16949: "9.2.2"
  domain: quality-engineering
  subdomain: audit
  industries: automotive,electronics
  status: approved
  created: "2026-06-01"
  last_updated: "2026-06-03"
  updated_by: migmcc
  reviewed_by: RBraga01
  standard_edition: "IATF 16949:2016"
---

# IATF 16949:2016 Internal Audit — Supplemental Requirements

## Goal

Audit the automotive-specific supplemental requirements of IATF 16949:2016, including CSR compliance and the three mandatory internal audit streams. Use in conjunction with [iso-9001-internal-audit](../iso-9001-internal-audit/) for a complete IATF audit.

---

## When to use

This skill covers the **IATF 16949 supplemental requirements** — the automotive additions to ISO 9001.

IATF 16949 requires three types of internal audit (§9.2.2.1). All three must be planned, executed, and recorded within the audit programme cycle:

1. **QMS audit** — covers the entire quality management system (ISO 9001 + IATF supplementals)
2. **Manufacturing process audit** — process-based, covers all manufacturing processes at least annually
3. **Product audit** — product-specific, verifies product conformance to specifications

All manufacturing processes must be audited at least annually, with increased frequency for high-risk or poor-performing areas.

---

## Required IATF Audit Checklist

☐ Verify all three audit streams are planned and executed within the programme cycle
☐ Confirm CSR register is current and that changes trigger QMS document updates
☐ Check contingency plans are documented, reviewed, and tested (not just written)
☐ Verify special characteristics are consistent across all documents (drawing, DFMEA, PFMEA, CP, WI)
☐ Confirm supplier monitoring and escalation are active with defined thresholds
☐ Check Control Plan ↔ PFMEA linkage is current
☐ Verify traceability and suspect material isolation capability (24-hour test)
☐ Review temporary deviations for approval, expiry, and active control
☐ Verify problem-solving methodology is applied with objective evidence of effectiveness
☐ Confirm management review includes all IATF supplemental inputs
☐ Do not accept verbal confirmation — verify by observing the process, interviewing personnel, and reviewing records

---

## Key IATF 16949 supplemental requirements — audit questions

### §4.3.2 — Customer-specific requirements (CSR)

This is the most commonly non-conforming IATF clause.

Questions:

- Is there a register of all applicable customer-specific requirements (CSRs)?
- For each OEM customer: have the latest CSRs been downloaded and reviewed?
- Are CSR requirements addressed in the QMS (procedures, control plans, work instructions)?
- Are personnel who deal with each customer aware of their specific requirements?
- CSR review must be revision-controlled and linked to implementation evidence in affected documents — is this traceable?
- *Evidence:* CSR register, evidence that each CSR has been reviewed and implemented, CSR revision dates vs. QMS document dates

**High-risk CSR areas:** PPAP requirements, problem-solving format requirements, special characteristics symbols, labelling specifications, sub-supplier approval requirements.

---

### §5.1.1.1 — Corporate responsibility

- Is there a documented corporate responsibility policy (ethics, anti-bribery)?
- Is there an escalation process for reporting ethical concerns?
- Are employees aware of how to report ethical concerns confidentially?
- *Evidence:* code of conduct, ethics policy, reporting mechanism (hotline or similar)

---

### §5.3.1 — Organisational roles, responsibilities, and authorities — supplemental

- Is there a person responsible for customer satisfaction?
- Are responsibilities for special characteristics defined?
- Is there a process for communicating customer requirements to all relevant functions?
- *Evidence:* roles matrix with customer satisfaction ownership identified

---

### §6.1.2.1 — Risk analysis (supplemental)

- Does the risk analysis consider lessons learned from similar products?
- Is warranty data, field returns, and customer complaints included as inputs?
- *Evidence:* risk analysis records with warranty/field data inputs

---

### §6.1.2.3 — Contingency plans

IATF requires documented contingency plans for:

- Key equipment failure
- Key supplier failure or disruption
- Labour shortages
- IT/infrastructure failure
- Natural disasters or site incidents affecting delivery

Questions:

- Are contingency plans documented for each of these scenarios?
- Are plans reviewed periodically (at least annually)?
- Are they tested or rehearsed?
- Does top management know who activates contingency plans?
- Do contingency plans include customer communication protocols and recovery priorities?
- *Evidence:* contingency plan document, last review date, test/simulation records

---

### §7.2.3 — Internal auditor competency

- Are internal auditors formally qualified or trained?
- Do auditors have process knowledge for the areas they audit?
- Is there evidence of auditor training (certification, OJT, qualification test)?
- Are auditors independent of the area they audit?
- Is auditor effectiveness periodically reviewed based on audit quality and finding accuracy?
- *Evidence:* auditor qualification records, audit schedule showing independence

---

### §7.2.4 — Second and third-party auditor competency

- For supplier audits: are supplier auditors trained and qualified?
- For customer audits: are there designated contacts?

---

### §8.3.2.1 — Design and development — supplemental

- Are special characteristics (SC) identified and documented in DFMEA and drawings?
- Are customer-specific SC symbols used correctly?
- Are SC characteristics flowed down to PFMEA, Control Plan, and work instructions?
- *Evidence:* drawing with SC marked, DFMEA with SC, PFMEA with SC, Control Plan with SC, WI with SC

---

### §8.3.3.3 — Special characteristics

- Is there a process to identify, document, and control all special characteristics?
- Do all documents (drawing, DFMEA, PFMEA, CP, WI) use consistent SC symbols?
- Are operators aware of which characteristics are special?
- Any inconsistency in SC identification across documents must be treated as a significant audit finding due to control failure — is SC consistency actively verified?
- *Evidence:* SC registry or matrix cross-referencing all documents

---

### §8.4.1.2 — Customer-directed sources (directed buy)

- When the customer directs a specific supplier (directed buy), is this documented?
- Is the directed supplier included in the approved supplier list?
- Is quality monitoring applied even if the customer selected the supplier?

---

### §8.4.2.3 — Supplier monitoring

IATF requires active supplier monitoring with specific actions for non-performing suppliers.

Questions:

- Is there a supplier performance monitoring system (PPM, on-time delivery, quality issues)?
- Is supplier performance reviewed at a defined frequency (minimum quarterly)?
- Are supplier development or escalation actions triggered based on defined performance thresholds?
- For poor performers: is there a documented escalation and improvement process?
- Are suppliers assessed for delivery of conforming product (not just quality level)?
- *Evidence:* supplier scorecards, last 4 quarters of performance data, improvement plans for poor performers

---

### §8.5.1.1 — Control plan

Questions:

- Is there a control plan for each production part?
- Does it cover: pre-launch, production, and reaction plan?
- Are all special characteristics in the control plan with specific control methods?
- Is the control plan linked to the PFMEA (detection controls match)?
- Are reaction plans in the Control Plan understood and applied at the point of use — not only documented?
- Was it updated after the last process or product change?
- *Evidence:* control plan, PFMEA (verify linkage), latest revision date vs. last process change date

---

### §8.5.2.1 — Identification and traceability — supplemental

- Is full traceability from raw material to finished product maintained?
- Can suspect material be isolated within 24 hours?
- Is there a procedure for handling suspect material?
- Are lot sizes defined to limit the scope of recalls?
- *Evidence:* traceability records, suspect material handling procedure, sample traceability exercise (ask for a part and trace it backwards)

---

### §8.5.6.1.1 — Control of changes — supplemental (temporary change)

IATF requires that temporary process changes (deviations) be strictly controlled.

Questions:

- Is there a process for managing temporary deviations (substituting a process step or material)?
- Are deviations approved in writing with defined expiry dates?
- Is there a register of all open temporary deviations?
- Are expired deviations actively closed or extended — not left open silently?
- Is the customer notified when required by their CSR?
- *Evidence:* deviation register, sample open deviation with expiry date and approval

---

### §8.7.1.1 — Customer notification

- Is there a procedure for notifying the customer when suspect material may have been shipped?
- Does it define when notification is required (not just when the customer asks)?
- Does the procedure specify notification timelines (e.g., 24 hours for safety-related escapes per CSR)?
- Has the procedure been triggered recently? Were notifications timely?
- *Evidence:* notification procedure, last notification records (if any)

---

### §9.2.2.1 — Internal audit programme — supplemental

IATF requires **three audit streams** — most organisations fail by only conducting clause-based audits:

1. **QMS audit** — covers clauses; must cover entire QMS within the audit programme cycle
2. **Manufacturing process audit** — process-based, all manufacturing processes annually minimum; uses VDA 6.3 or equivalent scoring
3. **Product audit** — product/shipment audits at defined frequency

Questions:

- Are all three audit types in the programme?
- Is the manufacturing process audit process-based (turtle diagram approach)?
- Are all processes and products covered within the audit cycle?
- Is the audit programme risk-based (higher risk = higher audit frequency)?
- Low process audit scores must trigger corrective action, management review, and re-audit planning — is this in place?
- *Evidence:* annual audit programme, audit reports for all three types, process audit records (not just clause audits)

---

### §9.3.2.1 — Management review — supplemental inputs

IATF management review must include (in addition to ISO 9001 §9.3.2):

- Cost of poor quality (COPQ)
- Warranty performance (if applicable)
- Customer satisfaction and field performance review
- Status of CSR compliance
- Manufacturing feasibility assessments

Questions:

- Are these topics covered in the management review agenda?
- Is there data for each topic?
- Are decisions from these IATF-specific inputs translated into actions with owners and due dates?
- *Evidence:* management review minutes with IATF-required topics explicitly addressed

---

### §10.2.3 — Problem solving

- Is there a documented problem-solving methodology (8D or equivalent)?
- Is the methodology applied consistently across all quality escapes?
- Does the 8D identify root cause of occurrence AND root cause of escape?
- Is effectiveness verified before closure?
- *Evidence:* problem-solving procedure, sample 8D reports, verification of effectiveness records

---

### §10.2.4 — Error proofing

- Is there a documented approach to applying error-proofing (poka-yoke)?
- Are poka-yoke devices tested at defined intervals (IATF requires: minimum at every start of production)?
- Are test records maintained?
- Are failed or bypassed error-proofing checks treated as production stop / reaction plan triggers where applicable?
- Are poka-yoke failures treated as non-conformances requiring CAPA?
- *Evidence:* poka-yoke register, test frequency, test records, last test date vs. interval

---

### §10.3.1 — Continual improvement plan

- Is there a formal, documented continual improvement plan?
- Does it include manufacturing process effectiveness (not just quality KPIs)?
- Is it reviewed at management review?
- *Evidence:* CI plan document, last review, evidence of CI activities

---

## Product audit — §9.2.2.3

A product audit verifies that finished products meet all requirements before shipment. It is one of the three mandatory IATF audit streams.

Focus areas for product audit:

- Product conformity to drawing and specification (dimensional, functional, visual)
- Packaging and labelling compliance (OEM label format, part number, revision, quantity)
- Traceability and release status (is the product formally released and traceable to its records?)
- Audit frequency based on risk, customer issues, and product criticality

Evidence required: product audit reports, measurement records, packaging inspection records, release documentation.

---

## Manufacturing process audit — turtle diagram approach

A manufacturing process audit (required annually for each process) uses a turtle diagram to assess:

| Input | Question |
|-------|---------|
| **Who** (Man) | Qualification requirements, training, availability |
| **With what** (Machine) | Equipment capability, maintenance, calibration |
| **Using what method** | Work instructions, current, at point of use |
| **With what material** | Incoming material control, traceability |
| **With what measurement** | Gauges, MSA, SPC |
| **Environment** | Cleanroom, temperature, ESD, contamination |
| **Process output** | First-pass yield, defect rate, scrap |
| **Customer feedback** | PPM, complaints, warranty |

For each element: is it adequate? Is it controlled? Is there objective evidence?

Each turtle element should be verified by direct observation, interview, and record review — not by document review alone.

A process audit must result in a process audit score (VDA 6.3 uses a percentage score by process element P1-P7). Low scores must trigger corrective action, management review input, and re-audit planning.

---

## Common IATF audit failures

1. **CSR register not updated** when customer publishes new CSR revision
2. **No manufacturing process audits** — only clause-based audits in the programme
3. **Contingency plans exist but were never tested**
4. **Temporary deviations without expiry dates** or expired deviations not closed
5. **SC not consistently marked** across drawing, PFMEA, control plan, and work instruction
6. **Error-proofing not tested** at every start of production (frequency not defined or records not kept)
7. **Problem-solving procedure exists** but CARs in practice skip root cause or VOE

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

- [IATF supplemental requirements checklist](references/supplemental-requirements.md)

## Changelog

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-01 | @RBraga01 | Initial release |
| 1.1 | 2026-06-03 | @migmcc | Added supplemental requirements reference and CSR audit coverage |
