---
name: d0-d8-guide
type: reference
parent_skill: 8d-problem-solving
author: RBraga01
version: "1.0"
status: approved
created: "2026-06-01"
last_updated: "2026-06-03"
updated_by: RBraga01
reviewed_by: RBraga01
license: MIT
---

# D0–D8 Reference Guide

Complete reference for the Eight Disciplines (8D) problem-solving methodology.
Covers all disciplines from D0 (pre-work) through D8 (closure), with gate criteria,
evidence requirements, OEM-specific notes, and common rejection reasons.

---

## D0 — Emergency Response (Pre-Team)

D0 is not a numbered discipline in all OEM variants, but it is mandatory in practice.
Execute D0 **before** assembling the team whenever the defect poses an immediate risk.

### Purpose
Prevent further harm while the team is being assembled. D0 answers: "Is anyone already affected?"

### Required actions

1. **Safety assessment** — Is this a safety or regulatory issue?
   - If yes: escalate immediately to management, notify customer, do not ship
   - Document the safety decision regardless of outcome (even "not a safety issue" needs evidence)
   - **If safety or regulatory risk is confirmed: STOP the standard 8D timeline. Do not proceed to D1–D3 without documented management authorisation. The 8D resumes only after escalation is handled and management has acknowledged the risk in writing.**

2. **Suspect material identification** — What is already in the field, at the customer, or in transit?
   - Map all batches, serial numbers, or shipment dates in the suspect window
   - Flag all suspect stock: physically segregate (red tag, hold label, system block)

3. **Initial evidence capture** — Before anything is disturbed
   - Photos of the defect, batch labels, traceability markings
   - Measurement data if available
   - Production records for the suspect period

### D0 gate — complete when
- [ ] Safety and regulatory impact assessed and documented
- [ ] All suspect material identified by batch/lot/serial number
- [ ] Suspect stock physically segregated or blocked in the system
- [ ] Initial evidence captured and secured

### OEM notes
- **Ford TOPS-8D**: D0 called "Emergency Response Actions (ERA)" — mandatory field in submission
- **BMW G8D**: D0 captures initial problem statement and emergency actions before D1
- **VW QMSS**: Emergency containment must be documented with implementation timestamp

---

## D1 — Team Formation

### Purpose
Build the cross-functional team that has the knowledge and authority to solve the problem.

### Required members

| Role | Why mandatory |
|------|--------------|
| Champion (sponsor) | Has authority to release resources, approve actions, sign off D8 |
| Team leader | Owns the 8D, drives discipline completion, single point of contact |
| Quality engineer | Methodology, documentation, FMEA and Control Plan ownership |
| Production / process owner | Knows the process, can implement changes |
| Engineering | Design or process engineering authority |

Optional: supplier quality engineer, logistics, customer representative, maintenance.

### Validation questions
- Does someone on the team have authority to change the process (not just recommend)?
- Is every affected process step represented?
- Is the champion available to sign off at D8?

### D1 gate — complete when
- [ ] Team members listed with names, functions, and contact information
- [ ] Team leader identified
- [ ] Champion (sponsor) identified with sign-off authority
- [ ] Start date and target closure date documented

---

## D2 — Problem Description

### Purpose
Define what is wrong with precision so that anyone reading D2 can understand the problem
without asking questions. A strong D2 is the foundation of D4.

### Mandatory elements

**Quantification** — numbers, not adjectives

**Is/Is-Not scoping:**

| Dimension | IS | IS NOT |
|-----------|----|----|
| What (defect) | Specific defect with measurement | Similar defects not present |
| Which (part) | Part number, revision, batch | Other part numbers/batches |
| Where (found) | Location in process, customer, geography | Locations not affected |
| When (time) | Period when defect starts/ends | Before/after periods |
| How many | Rate, count, trend | |

### D2 gate — complete when
- [ ] Defect described with measured value and specification
- [ ] Part number, revision, and batch/lot identified
- [ ] Quantity affected stated as count and percentage
- [ ] Is/Is-Not matrix completed

---

## D3 — Interim Containment Actions (ICA)

### Purpose
Stop the non-conforming product from reaching the customer while D4–D5 are in progress.

### ICA requirements
- Must be past tense with evidence (not "we will sort" — "sorting completed on date, N parts rejected")
- Must physically prevent escape
- Must have an implementation date and responsible person
- **Containment is temporary — it must never be accepted as a permanent corrective action.** "We added 100% inspection" is a D3 ICA. The D5 PCA must eliminate or reduce the root cause, not just improve detection.

### D3 gate — complete when
- [ ] ICA implemented (past tense) with implementation date
- [ ] Evidence of ICA effectiveness documented
- [ ] Customer notified if product has reached them

---

## D4 — Root Cause Analysis

### The two root causes — mandatory
1. **Root Cause of Occurrence (RCO)** — why did the defect happen?
2. **Root Cause of Escape (RCE)** — why was it not detected?

### Root cause validation — both tests required
- **Reproducibility test**: can you deliberately create the defect by triggering the root cause?
- **Elimination test**: does removing the root cause prevent the defect in a trial?

### Reject these as root causes
- "Human error" — ask: why was the error possible?
- "Operator didn't follow procedure" — ask: why could they deviate?
- "Supplier sent bad parts" — ask: why wasn't it caught at incoming?

### D4 gate — complete when
- [ ] Two root causes identified (occurrence + escape), both validated with evidence
- [ ] Both root causes are systemic, backed by data

---

## D5 — Choose Permanent Corrective Actions

### PCA types (best to worst)
1. Eliminate the cause (poka-yoke, design change)
2. Reduce occurrence (prevention control)
3. Improve detection (detection control)

**Detection-only actions are not acceptable as the sole PCA if elimination or occurrence reduction is technically feasible.** Improving detection catches defects after they are made — it does not prevent them. A detection PCA alone must be justified in writing with evidence that prevention is not achievable.

### D5 gate — complete when
- [ ] One PCA per root cause selected
- [ ] Verification plan: what metric, what target, what method
- [ ] If detection-only PCA: documented justification that prevention was evaluated and ruled out

---

## D6 — Implement and Verify PCA Effectiveness

### Verification requirements
- **Sufficient production volume based on statistical confidence** — define sample size from the observed defect rate and risk level, not from a fixed number. Higher defect rate or safety-related failure mode requires a larger verification sample.
  - Reference formula: n ≥ log(α) / log(1 − p), where p = pre-PCA defect rate and α = acceptable probability of missing recurrence (typically 0.05).
  - Example: defect rate 2% (p = 0.02), α = 0.05 → n ≥ 148 units minimum.
- Before/after comparison with same metric as D2
- Zero recurrence of the exact defect mode
- ICA removed only after D6 verification is complete with data

### D6 gate — complete when
- [ ] PCAs implemented with date
- [ ] Verification data confirms zero recurrence
- [ ] ICA formally removed

---

## D7 — Prevent Recurrence

### Required updates — all mandatory
- [ ] PFMEA updated (revised occurrence and detection ratings, action plan updated)
- [ ] Control Plan updated
- [ ] Work Instructions / SOPs updated and re-issued
- [ ] Training conducted with records
- [ ] Lessons learned documented in quality system
- [ ] Horizontal deployment assessed (similar parts, processes, product families)

---

## D8 — Team Recognition and Closure

### Closure requirements
- [ ] Champion reviewed and signed off the complete 8D
- [ ] Customer notified of closure (if customer-initiated)
- [ ] Team recognition documented
- [ ] 8D report filed in quality records
- [ ] All D0–D7 objective evidence archived and traceable (photos, measurement records, updated documents with revision numbers, training records, verification data)

---

## OEM Submission Formats

| OEM | Format | D0 required | System |
|-----|--------|------------|--------|
| Ford | TOPS-8D | Yes (ERA) | GQTS |
| BMW | G8D | Yes | SRM/BQMS |
| VW/Audi | QMSS | Yes | FORMEL Q |
| Stellantis | 8D (MAQMSR) | Recommended | SQS Portal |
| GM | Global 8D | Recommended | Covisint |

See [oem-formats](../../../documentation/8d-report-writing/references/oem-formats.md) for full detail.

---

## Global 8D Validation Checklist

Use at closure review (D8) to confirm the full 8D is audit-ready. All items must be checked before the champion signs off.

| # | Item | Complete? |
|---|------|-----------|
| 1 | D0: Safety and regulatory risk assessed and documented (even if "not a risk") | ☐ |
| 2 | D0: Suspect material identified by batch/lot and physically segregated | ☐ |
| 3 | D1: Cross-functional team with champion and team leader named | ☐ |
| 4 | D2: Problem described with measured values vs. specification (not adjectives) | ☐ |
| 5 | D2: Is/Is-Not matrix completed with specific facts | ☐ |
| 6 | D3: Containment implemented (past tense) with date, responsible person, and effectiveness evidence | ☐ |
| 7 | D4: Root Cause of Occurrence identified, validated with data or experiment | ☐ |
| 8 | D4: Root Cause of Escape identified, validated with data or experiment | ☐ |
| 9 | D4: Both root causes are systemic (not "human error" or "operator mistake") | ☐ |
| 10 | D5: One PCA per root cause, addressing the root cause directly (not the symptom) | ☐ |
| 11 | D5: If detection-only PCA: justification documented that prevention was evaluated | ☐ |
| 12 | D6: Verification data shows zero recurrence over a statistically sufficient sample | ☐ |
| 13 | D6: ICA formally removed after verification is complete | ☐ |
| 14 | D7: PFMEA updated — revision number and date recorded | ☐ |
| 15 | D7: Control Plan updated — revision number and date recorded | ☐ |
| 16 | D7: Work Instructions updated and re-issued — revision number and date recorded | ☐ |
| 17 | D7: Horizontal deployment assessed; actions documented for similar parts/processes | ☐ |
| 18 | D8: All D0–D7 evidence archived and traceable | ☐ |
| 19 | D8: Champion sign-off obtained | ☐ |
| 20 | D8: Customer notified of closure (if customer-initiated complaint) | ☐ |
