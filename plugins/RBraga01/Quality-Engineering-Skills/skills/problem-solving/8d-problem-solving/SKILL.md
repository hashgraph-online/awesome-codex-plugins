---
name: 8d-problem-solving
description: >-
  Open an 8D, run a G8D or TOPS-8D investigation, respond to a warranty complaint, or handle
  a customer quality escape with the 8 Disciplines methodology. Covers D0 emergency response
  through D8 team recognition with gate validation. Required for automotive OEM complaints —
  Ford, BMW, VW, Stellantis — and any quality escape needing documented root cause and PCA.
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
  last_updated: "2026-06-03"
  updated_by: RBraga01
  reviewed_by: RBraga01
  standard_edition: "ISO 9001:2015 / IATF 16949:2016"
---

# 8D Problem Solving

## Goal

Produce a validated, audit-ready 8D report with proven root causes and effective corrective actions that prevent recurrence — accepted by the customer and filed in the quality system.

## Required Execution Checklist

Quick-reference for agents and practitioners. All items must be complete before D8 closure.

- [ ] D0: Safety and regulatory risk assessed and documented
- [ ] D0: Suspect material identified and physically segregated
- [ ] D1: Cross-functional team assembled with champion identified
- [ ] D2: Problem described with measured values, part number, quantity, and Is/Is-Not
- [ ] D3: Containment implemented (past tense) with date and effectiveness evidence
- [ ] D4: Root cause of **occurrence** identified and validated with data or experiment
- [ ] D4: Root cause of **escape** identified and validated with data or experiment
- [ ] D5: One PCA per root cause selected, with verification plan
- [ ] D6: PCA implemented; verification data confirms zero recurrence; ICA formally removed
- [ ] D7: PFMEA, Control Plan, and Work Instructions updated (revision numbers documented)
- [ ] D7: Horizontal deployment assessed and actioned
- [ ] D8: Champion sign-off obtained; customer notified of closure

---

## When to use

Use 8D for customer-reported defects, internal escapes reaching downstream processes, field failures, or any non-conformance requiring documented root cause analysis. Mandatory for most automotive OEM customer complaints (Ford 8D, BMW G8D, VW QMSS, Stellantis).

## Prerequisites

- Defect or failure clearly identified and quantified
- Access to affected parts, process records, and measurement data
- Cross-functional team availability (quality, production, engineering minimum)

## Workflow

### D0 — Emergency Response (before the team is assembled)

Ask these questions first:
1. Is this a safety or regulatory issue? If yes → escalate immediately, notify customer
2. **Is there any potential for a product recall or regulatory event (safety, emissions, homologation compliance)?**
   - If yes → **STOP the standard 8D timeline. Escalate immediately to management and regulatory owner.** Do not proceed without documented management awareness. The 8D continues only with their authorisation.
3. Are suspect parts already at the customer or in the field? If yes → launch containment now (D3) before completing D1-D2
4. Capture initial evidence: photos, batch numbers, lot traceability, measurement data

D0 is complete when: safety is assessed, regulatory escalation decision documented, suspect material is identified and flagged.

---

### D1 — Team Formation

Build a cross-functional team. Required functions:
- **Champion** (sponsor, authority to release resources)
- **Team leader** (owns the 8D, drives completion)
- **Quality engineer** (methodology, documentation)
- **Production / process owner** (process knowledge)
- **Engineering** (design or process engineering)

Optional: supplier quality, logistics, customer representative.

Document: names, functions, team leader, start date, target closure date.

**Validation:** Is every affected process step represented? Does someone have authority to change the process?

---

### D2 — Problem Description

Define the problem precisely using Is/Is-Not and 5W2H. A weak D2 produces a weak D4.

**Is/Is-Not scoping (see [is-is-not-scoping](../is-is-not-scoping/) skill):**

| Question | IS | IS NOT |
|----------|----|--------|
| What is the problem? | e.g., dimensional out-of-spec | cosmetic scratch |
| What object/part? | Part number X, revision B | Part number Y |
| Where is it found? | Station 3, incoming inspection | Final test |
| When did it start? | Batch from 2026-05-12 | Earlier batches |
| How many? | 47 of 200 inspected (23.5%) | — |
| Trend? | Consistent since batch date | No spike |

**5W2H:**
- Who detected it? When? Where?
- What is the exact non-conformance (measured value vs. specification)?
- Why is it a problem (customer impact)?
- How was it detected? How many are affected?

D2 is complete when: a stranger could read it and know exactly what is wrong, on what, when, how many, and where in the supply chain.

---

### D3 — Interim Containment Actions (ICA)

ICA must **stop the non-conforming product from reaching the customer** while D4-D5 are in progress.

Typical ICAs:
- Sort / 100% inspection of suspect stock (in-process + field + customer)
- Ship-hold on all batches in the date range
- Add a specific inspection step at outgoing QC
- Customer notification and stock recovery (if product escaped)

**ICA validation — ask:**
- Does this ICA physically prevent the defect from escaping? (Yes/No — not "we will try")
- What is the evidence it is working? (inspection records, zero escapes since ICA date)
- Is it documented with an implementation date and responsible person?
- Is it temporary? (an ICA is not a permanent fix)

D3 is complete when: suspect product is contained with objective evidence, customer notified if applicable.

---

### D4 — Root Cause Analysis

Find TWO root causes:
1. **Root cause of occurrence** — why did the defect happen?
2. **Root cause of escape (detection failure)** — why was it not detected before reaching the customer/next process?

Use these tools (see referenced skills):
- [5-Why](../5why-root-cause/) for each root cause
- [Fishbone / Ishikawa](../fishbone-analysis/) for brainstorming categories
- [Is/Is-Not](../is-is-not-scoping/) to scope the problem boundaries

**Root cause validation:**
- Can you reproduce the defect by deliberately creating the root cause?
- Does removing the root cause prevent the defect in a trial run?
- Is it backed by data, not opinion?

**Reject these as final root causes:**
- "Human error" (not systemic — ask WHY the error was possible)
- "Operator didn't follow instructions" (ask WHY they didn't, or couldn't)
- "Supplier delivered bad parts" (ask WHY your incoming inspection did not catch it)

**Evidence rule:** A root cause must be proven by data or physical experiment — not by logical reasoning alone. If you can only argue it is plausible, it is a hypothesis. Reproduce the defect by triggering the root cause; eliminate the defect by removing it. Both tests required.

D4 is complete when: both root causes are validated with objective evidence, not opinion.

---

### D5 — Choose Permanent Corrective Actions (PCA)

For each root cause from D4, select a permanent corrective action that:
- Directly addresses that specific root cause (not a symptom)
- Can be verified as effective
- Is feasible within the available time and resources

**Evaluation matrix (for each candidate PCA):**
- Does it address the root cause? (Yes/No)
- Can effectiveness be measured? (metric + target)
- Is it risk-free to implement? (FMEA check)
- Timeline: realistic?

Document: PCA description, responsible owner, target implementation date, verification method.

D5 is complete when: one PCA per root cause is selected and documented with verification plan.

---

### D6 — Implement and Verify Effectiveness

Implement the PCAs. After implementation:

**Verification requirements:**
- Run sufficient production volume to achieve statistical confidence — **define sample size based on the observed defect rate and risk level** (higher defect rate or safety-related defect → larger sample required). Do not use fixed generic numbers; align the sample with the detection probability needed.
  - Guidance: if pre-PCA defect rate was p, the verification sample should be large enough that the probability of observing zero defects if p is still present is below 5%. Formula: n ≥ log(0.05) / log(1 − p).
- Measure the original defect metric before and after
- Confirm zero recurrence of the exact defect mode

**Verification evidence to capture:**
- Process control charts or inspection data after PCA
- Before/after comparison (defect rate or measurement data)
- Signed-off by quality and production

ICA (D3) can only be removed **after** D6 verification is complete with objective evidence.

D6 is complete when: data confirms the defect is eliminated, ICA formally removed.

---

### D7 — Prevent Recurrence (Systemisation)

The most valuable — and most skipped — discipline. Prevents the same root cause from appearing elsewhere.

**Required updates:**
- [ ] PFMEA updated: add/revise failure mode, update occurrence and detection ratings
- [ ] Control Plan updated: add control for root cause and escape
- [ ] Work Instructions / SOPs updated and re-issued
- [ ] Incoming inspection updated (if supplier or material related)
- [ ] Lessons learned documented and shared with similar product lines
- [ ] Training conducted for affected operators / inspectors

**Horizontal deployment:**
- Are there similar part numbers, processes, or product families that could have the same root cause?
- If yes → extend PCAs to those areas and document

D7 is complete when: all process documents are updated and changes are live in production.

---

### D8 — Team Recognition

Formally close the 8D:
- Team leader presents the completed 8D to the champion
- Champion validates all disciplines are complete with evidence
- Team is formally recognised (acknowledgement — not necessarily financial)
- 8D report is filed in the quality records system
- Closure communicated to the customer (if customer-initiated complaint)

D8 is complete when: champion signs off, customer notified of closure.

---

## Validation — is the 8D complete?

Before closing, verify:
- [ ] D2 problem description is objective and quantified
- [ ] D3 ICA has implementation date and verification evidence
- [ ] D4 has two root causes (occurrence + escape), both validated with evidence
- [ ] D5 PCAs directly address D4 root causes
- [ ] D6 verification data shows zero recurrence after PCA
- [ ] D7: FMEA, control plan, and work instructions are all updated
- [ ] D8: champion sign-off and customer notification (if applicable)

## Common mistakes

- **Skipping D0:** jumping to D2 before confirming the customer has no more suspect stock
- **Weak D2:** vague problem description leads to wrong root cause
- **D3 as D6:** treating containment as the permanent fix ("we added 100% inspection" is not a PCA)
- **Symptom as root cause:** "machine was miscalibrated" — why? "supplier sent wrong material" — why wasn't it caught?
- **Not updating D7 documents:** the most common audit finding

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

- [D0–D8 detailed guide](references/d0-d8-guide.md)
- [8D report template](assets/8d-template.md)

## Changelog

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-01 | @RBraga01 | Initial release |
| 1.1 | 2026-06-03 | @RBraga01 | Added Required Execution Checklist, D-level validation criteria, OEM gate rules |
