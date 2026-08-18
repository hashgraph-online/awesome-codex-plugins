---
name: scar-template
type: reference
parent_skill: supplier-scar
author: RBraga01
version: "1.0"
status: approved
created: "2026-06-06"
last_updated: "2026-06-06"
updated_by: RBraga01
reviewed_by: RBraga01
license: MIT
---

# SCAR Document Template and Evaluation Reference

Complete SCAR document template with field instructions, 8D response evaluation scorecard, effectiveness verification checklist, supplier performance impact table, and escalation decision matrix.
Use alongside the [supplier-scar](../SKILL.md) skill.

> **Scope:** This document provides the fill-in template, evaluation criteria for reviewing a supplier's 8D response (per discipline), and the escalation framework linking SCAR outcomes to supplier rating and status changes. For escalation triggers (when an NCR becomes a SCAR), response rejection criteria, and the full SCAR workflow, see [supplier-scar SKILL.md](../SKILL.md).

---

## 1. SCAR Document Template

Copy this template for each new SCAR. All fields marked **(R)** are required before issuing the SCAR. Fields marked **(S)** are completed by the supplier. Fields marked **(V)** are completed during verification.

---

### SECTION A — IDENTIFICATION (R)

```
SUPPLIER CORRECTIVE ACTION REQUEST (SCAR)
==========================================
SCAR Number:         _______________    (Format: SCAR-YYYY-NNN, unique, sequential)
Date Issued:         _______________
Priority:            [ ] CRITICAL — Safety/field impact     [ ] HIGH — Customer or production impact
                     [ ] STANDARD — Systemic/recurrence issue
Issued by:           _______________    Title: _______________
Organisation:        _______________    Site/Location: _______________
Supplier Name:       _______________    Supplier Code: _______________
Supplier Contact:    _______________    Title: _______________
Supplier Email:      _______________    Phone: _______________
SCAR Coordinator:    _______________    (Supplier Quality Engineer responsible for follow-up)
```

**Field instructions:**
- **SCAR Number:** Never reuse a SCAR number. If a reissue is required (e.g., after a rejection), create a new SCAR and reference the previous one.
- **Priority CRITICAL:** Use when the non-conformance is or could be a safety risk, regulatory violation, or has reached the end customer. Triggers 24h acknowledgement requirement and escalation to supplier management.
- **Priority HIGH:** Use when a production line stop has occurred, customer complaint has been received, or an entire delivery lot is affected.
- **Priority STANDARD:** Use for systemic deficiencies, recurrence, or process-level issues without immediate customer impact.

---

### SECTION B — NON-CONFORMANCE DESCRIPTION (R)

```
Part Number:         _______________    Part Description: _______________
Drawing Revision:    _______________    Customer Part Number (if different): _______________
Delivery Reference:  _______________    (PO number / Delivery Note / Lot number)
Date of Delivery:    _______________    Date of Detection: _______________
Detected at:         [ ] Incoming inspection    [ ] In-process    [ ] Final inspection
                     [ ] Customer facility       [ ] Field/end user
Quantity Delivered:  _______________    Quantity Non-Conforming: _______________
Percent Affected:    _______________    %

DEFECT DESCRIPTION (objective, measured, specific — no opinions):
_____________________________________________________________________
_____________________________________________________________________
Example: "Pin insertion depth measured 4.2–4.6 mm on 23 units; specification is 5.0 ± 0.3 mm (range 4.7–5.3 mm)."

SPECIFICATION REFERENCE:
Drawing callout / spec clause: _______________
Required value:                _______________
Measured / observed value:     _______________

CUSTOMER IMPACT (if applicable):
[ ] Production line stop at customer          [ ] Customer complaint received
[ ] Field return / warranty claim             [ ] OEM escalation (customer 8D reference: _______)
[ ] No customer impact — internal issue only

NCR Reference: _______________    (Attach NCR or link)
Photographs / evidence attached: [ ] Yes    [ ] No
```

**Field instructions:**
- **Defect description:** Write what was measured or observed. Include the specification and the actual value. Do not write "part is bad" or "does not meet requirements" — state what was measured.
- **Quantity non-conforming:** Based on evidence. If 100% is suspected but not yet verified, state the entire delivery as suspect and require the supplier to confirm during D3.
- **Customer impact:** Accuracy here drives the supplier's urgency. If OEM escalation is ticked, attach the OEM concern reference number — the supplier needs to understand the full chain.

---

### SECTION C — RESPONSE REQUIREMENTS (R)

```
REQUIRED DELIVERABLES AND DEADLINES
=====================================
D3 — Immediate Containment Action
  Due:               _______________    (Default: 24–48 hours from SCAR issue date)
  Required content:  Confirmation that all suspect stock at supplier, in transit, and at our facility
                     has been identified, quarantined, and is under 100% inspection or hold.
                     Provide quantities: held at supplier ___, held in transit ___, held at our facility ___.
                     State method of inspection for clearing suspect stock.

D4 — Root Cause Analysis
  Due:               _______________    (Default: 7–14 days)
  Required content:  TWO root causes required:
                     (1) Root cause of occurrence — why was the defect produced?
                     (2) Root cause of escape — why was it not detected before shipment?
                     Support each root cause with physical evidence or data.
                     5-Why or Ishikawa diagram required; verbal explanation not acceptable.

D5–D6 — Permanent Corrective Actions and Implementation Evidence
  Due:               _______________    (Default: 30 days)
  Required content:  One corrective action addressing each root cause.
                     Training alone is not acceptable as a permanent corrective action.
                     Implementation evidence: revised documents with revision numbers, 
                     photos of installed poka-yoke, updated process parameters, 
                     training records with signatures.
                     D6: production data showing the process is now in control.

D7 — Systemic Prevention
  Due:               _______________    (Default: 30 days, same deadline as D5–D6)
  Required content:  Updated PFMEA (revised failure mode entry with new S/O/D ratings).
                     Updated Control Plan (if inspection or detection method changed).
                     Updated Work Instructions (if process method changed).
                     Horizontal deployment: list other part numbers, lines, or plants 
                     where the same failure mode could occur and confirm actions taken.

FULL 8D REPORT
  Due:               _______________    (Default: 30 days)
  Format:            [ ] Supplier's own 8D format (acceptable if covers all D1–D8)
                     [ ] Customer-provided 8D template (required if customer-specific)

Submission address:  _______________
Format:              [ ] PDF    [ ] Portal upload    [ ] Email attachment
```

**Field instructions:**
- **D3 deadline is non-negotiable.** Do not extend the D3 deadline. If containment cannot be confirmed in 24–48 hours, escalate to supplier management immediately.
- **Two root causes required:** Make this explicit in the SCAR text. Many suppliers provide only the occurrence root cause. Escape root cause is equally important — it explains the gap in the supplier's quality system.
- **Training alone:** If the supplier's corrective action is "retrain operator," it will be rejected. Make the rejection criteria clear upfront to save iteration cycles.

---

### SECTION D — CONTAINMENT VERIFICATION (R, completed by issuer after D3 receipt)

```
CONTAINMENT VERIFICATION (completed by Supplier Quality Engineer)
==================================================================
D3 received date:    _______________
D3 assessed by:      _______________

Supplier stock confirmed quarantined:     [ ] Yes    [ ] No    Qty: _______________
Transit stock confirmed recalled or held: [ ] Yes    [ ] No    Qty: _______________
Our facility stock confirmed segregated:  [ ] Yes    [ ] No    Qty: _______________
Inspection method confirmed adequate:     [ ] Yes    [ ] No
Results of 100% inspection:              Qty inspected: ___  Qty conforming: ___  Qty rejected: ___

D3 Accepted:  [ ] Yes    [ ] No — Rejection reason: _______________
Revised D3 deadline (if rejected):        _______________

Notes: _______________
```

---

### SECTION E — 8D RESPONSE RECORD (S, completed by supplier)

```
SUPPLIER RESPONSE (8D)
========================
D1 — Team:           _______________
D2 — Problem:        (should match Section B — if supplier re-describes the problem, verify alignment)
D3 — Containment:    [ ] Complete    Completion date: _______________
D4 — Root cause:
  Occurrence:        _______________
  Escape:            _______________
  Evidence:          _______________
D5 — Corrective action (occurrence): _______________
D5 — Corrective action (escape):     _______________
D6 — Implementation evidence:        _______________
     Completion date:                _______________
     Production data reference:      _______________
D7 — Systemic prevention:
  PFMEA updated:     [ ] Yes    Rev: ___    Date: ___
  Control Plan updated: [ ] Yes  Rev: ___   Date: ___
  WI updated:        [ ] Yes    Rev: ___    Date: ___
  Horizontal deployment confirmed: [ ] Yes  Areas covered: _______________
D8 — Closure confirmation:           _______________
Full 8D report attached: [ ] Yes    [ ] No
```

---

### SECTION F — 8D EVALUATION AND ACCEPTANCE (V)

See Section 2 (8D Response Evaluation Scorecard) for detailed scoring criteria.

```
8D EVALUATION
==============
Evaluated by:        _______________    Date: _______________
Overall result:      [ ] Accepted    [ ] Rejected — see scorecard

Rejection notice issued:    [ ] Yes    Date: ___    Revised deadline: _______________
Revised 8D received:        [ ] Yes    Date: ___
Second evaluation result:   [ ] Accepted    [ ] Escalated

Notes: _______________
```

---

### SECTION G — EFFECTIVENESS VERIFICATION (V)

```
EFFECTIVENESS VERIFICATION
===========================
Planned verification method:    _______________
Monitoring period:              ___ deliveries / ___ days / ___ production cycles
Start date:                     _______________
Target:                         Zero recurrence of [defect description] during monitoring period
                                AND/OR: Cpk improvement from ___ to ___ on [characteristic]

Verification results:
  Monitoring period complete:   [ ] Yes    End date: _______________
  Recurrence observed:          [ ] Yes — ESCALATE    [ ] No
  Updated PFMEA received & verified: [ ] Yes    [ ] No
  Updated CP received & verified:    [ ] Yes    [ ] No
  Updated WI received & verified:    [ ] Yes    [ ] No
  Production data reviewed:          [ ] Yes    Reference: _______________

Effectiveness verdict:          [ ] Effective    [ ] Not effective — return to D4

Verified by:                    _______________    Date: _______________
```

---

### SECTION H — CLOSURE

```
SCAR CLOSURE
=============
All closure criteria met:       [ ] Yes    [ ] No — outstanding items: _______________
Supplier performance record updated: [ ] Yes
Supplier rating impact applied: [ ] Yes    New rating/category: _______________
Closure authority:              _______________    Title: _______________
Closure date:                   _______________
SCAR filed in supplier record:  [ ] Yes
```

---

## 2. 8D Response Evaluation Scorecard

Score each discipline 0–3. A total score below 16/24 is grounds for rejection. Any discipline scored 0 on a W3 gate criterion is an automatic rejection regardless of total.

| Discipline | Acceptance criteria (score 3) | Marginal (score 1–2) | Rejection criteria (score 0) | W |
|-----------|-------------------------------|---------------------|------------------------------|---|
| **D3 — Containment** | Containment completed (past tense) with quantity data. Covers supplier, transit, and customer facility. Inspection method is appropriate for the defect. Results (qty sorted, qty rejected) are provided. | Containment mentioned but incomplete location coverage, or no results data, or future-tense only for part of the scope. | "We will inspect going forward" — no completed containment. OR containment covers only one location. OR no results provided. | W3 |
| **D4 — Occurrence RC** | Root cause is specific, causal, and supported by physical evidence or data. 5-Why chain shows how the root cause produced the defect. Root cause is at a level that can be permanently addressed. | Root cause identified but not validated with evidence. Chain stops too early. Some logic gap between RC and defect. | "Human error", "operator mistake", "lack of attention", "customer specification changed" as final RC. No supporting evidence. Multiple possible causes listed with no confirmation of which is correct. | W3 |
| **D4 — Escape RC** | Root cause of escape is separate from occurrence RC. Explains specifically why the control plan / inspection did not detect the defect. Supported by review of the actual control plan and inspection records. | Escape RC identified but vague (e.g., "inspector missed it" without explaining why the system allowed that). | No escape RC provided. OR escape RC is identical to occurrence RC. OR "inspector was not paying attention" as final escape RC with no systemic gap identified. | W3 |
| **D5 — Corrective action (occurrence)** | Action directly addresses the confirmed occurrence RC. Specific: states what will be changed, how, by whom. Includes a poka-yoke or process change where feasible. Is not just training. | Action addresses the RC but is not the most robust solution (e.g., adds inspection when prevention is possible). No poka-yoke consideration. | Training as the sole corrective action. Action addresses a symptom, not the root cause. No specifics (e.g., "improve process"). | W2 |
| **D5 — Corrective action (escape)** | Action directly addresses the confirmed escape RC. Updates the inspection method, frequency, gauge, or detection control. Not just "add a check" — specifies what, at what frequency, with what method, and how results are recorded. | Action improves detection but does not fully address the gap in the control plan. OR the action requires operator attention rather than a systematic control. | No corrective action for escape RC. OR action is to "remind inspector to be more careful." | W2 |
| **D6 — Implementation evidence** | All actions confirmed as implemented with document revision numbers, approval dates, photos of installed equipment, or signed training records. Production data shows the process ran under the new conditions. | Some actions implemented and documented; others "in progress" with no evidence yet. | No implementation evidence. OR evidence is a promise/plan rather than completed actions. OR document revisions not incremented (revision number unchanged). | W3 |
| **D6 — Effectiveness data** | Production data shows process running under corrective actions. Minimum: 30 consecutive cycles or 3 sampling intervals without recurrence. Before/after comparison provided where applicable. Cpk data provided if characteristicis on SC. | Data provided but insufficient volume (e.g., 10 parts) or duration (e.g., one shift). No before/after comparison. | No production data. OR effectiveness section marked "TBD" or "to be monitored." OR data is from pre-implementation period. | W2 |
| **D7 — Systemic prevention** | PFMEA updated with revised S/O/D and new AP. Control Plan updated to reflect new detection method. Work Instructions updated at point-of-use revision. Horizontal deployment addressed for similar parts/processes. | PFMEA updated but CP or WI not yet updated. Horizontal deployment not addressed. | No PFMEA update. OR updated PFMEA does not include the confirmed failure mode. OR "not applicable" asserted without justification. | W2 |

**Scoring:**

| Total score | Result |
|-------------|--------|
| 20–24 | Accepted |
| 16–19 | Accepted with conditions — specified open items must be closed within 14 days |
| 10–15 | Rejected — issue formal rejection notice; supplier must resubmit |
| Below 10 | Rejected with escalation — escalate to supplier management; consider controlled shipping |
| Any W3 scored 0 | Automatic rejection regardless of total |

---

## 3. Effectiveness Verification Checklist

Complete this checklist before closing the SCAR.

| Criterion | Verification method | Status |
|-----------|---------------------|--------|
| Zero recurrence of the same defect during the monitoring period | Review incoming inspection records for the defined number of subsequent deliveries | [ ] Pass [ ] Fail |
| Corrective action documents are at the correct revision and approved | Request current revision of PFMEA, CP, and WI; verify revision number matches the post-action version | [ ] Pass [ ] Fail |
| PFMEA reflects the failure mode with updated occurrence and detection ratings | Compare D4 failure mode description to PFMEA entry; confirm S/O/D revised | [ ] Pass [ ] Fail |
| Control Plan includes the new or updated detection method | Confirm CP includes the updated inspection step, frequency, and response plan | [ ] Pass [ ] Fail |
| Work Instruction at point-of-use is updated and operators are trained to new revision | Request training records; verify WI revision at the workstation matches approved version | [ ] Pass [ ] Fail |
| Horizontal deployment confirmed for similar parts or processes | Review supplier's horizontal deployment list; spot-check one additional part/line if feasible | [ ] Pass [ ] Fail |
| Supplier performance data (PPM, SCAR count) updated in supplier record | Verify internal supplier performance record reflects this SCAR closure and any PPM impact | [ ] Pass [ ] Fail |
| On-site verification completed (required for Priority CRITICAL) | Conduct a focused VDA 6.3 P6 walkthrough of the specific process step; document findings | [ ] Pass [ ] N/A |

**If any criterion fails:** Do not close the SCAR. Issue a formal notification to the supplier with a revised deadline. If the monitoring period reveals recurrence, escalate immediately per the escalation matrix (Section 5).

---

## 4. Supplier Performance Rating Impact Table

SCAR outcomes are linked directly to the supplier's quality classification and rating score. The specific point values are defined in the organisation's Supplier Quality Manual; the table below shows the impact categories.

| SCAR outcome | PPM impact | Rating score impact | Supplier status impact |
|-------------|------------|---------------------|------------------------|
| SCAR closed on time, first-time 8D accepted, effective | None (defect PPM already counted at detection) | No negative adjustment | Status maintained |
| SCAR closed on time, 8D accepted on second submission | No additional PPM penalty | Minor negative adjustment (typical: −3 to −5 points on annual score) | Status maintained — note on record |
| SCAR closed late (>30 days past deadline without agreed extension) | PPM impact recorded plus late-closure penalty | Moderate negative adjustment (typical: −5 to −10 points) | Status review triggered if 2+ late closures in 12 months |
| SCAR rejected twice — third submission required | PPM maintained | Significant negative adjustment (typical: −10 to −15 points) | Controlled shipping Level 1 triggered |
| SCAR recurrence (same defect within 12 months of previous SCAR) | PPM of new event + recurrence surcharge | Major negative adjustment (typical: −15 to −20 points) | Controlled shipping Level 2; supplier improvement plan mandatory |
| SCAR effectiveness not confirmed (VOE failed) | PPM maintained; monitoring period extended | Significant negative adjustment | Elevated monitoring status; next delivery requires pre-shipment approval |
| SCAR open with no response after 45 days, no communication | PPM maintained | Maximum negative adjustment; automatic escalation | Escalation to disqualification review |

**Classification thresholds** (representative — align with your organisation's SQM):

| Annual supplier score | Classification | Implications |
|----------------------|----------------|-------------|
| ≥ 85 points | Preferred Supplier | Eligible for new business; reduced incoming inspection |
| 70–84 points | Approved Supplier | Eligible for continuation; standard incoming inspection |
| 55–69 points | Conditional Supplier | No new business; corrective programme required; increased incoming inspection |
| < 55 points | Disqualification Review | New business blocked; re-qualification required; immediate escalation to procurement |

---

## 5. Escalation Decision Matrix

Use this matrix to determine the appropriate escalation action based on SCAR status and supplier behaviour.

| Condition | Elapsed time | Escalation action | Who acts |
|-----------|-------------|-------------------|----------|
| D3 not received | > 48 hours from SCAR issue | Call supplier management (not just quality contact); send written escalation notice | SQE + Manager |
| Full 8D not received | > 30 days from SCAR issue | Send formal overdue notice; escalate to supplier's General Manager or VP Quality | SQE + Manager |
| 8D rejected twice | After second rejection | Conduct emergency on-site visit; escalate to supplier's site director; consider controlled shipping | SQE + Manager + Procurement |
| SCAR open > 60 days with no closure path | Regardless of submission count | Issue formal supplier improvement plan; block new business; notify procurement | SQE + Manager + Procurement |
| Recurrence during monitoring period | Any point during VOE | New SCAR issued immediately referencing previous SCAR; controlled shipping Level 2 mandatory | SQE |
| Second recurrence (same defect, third SCAR) | — | Escalate to disqualification review; notify OEM customer if applicable; engage procurement for alternative supplier | SQE + Manager + Procurement + Customer |

### Controlled Shipping Levels

| Level | Trigger | Requirement | Duration |
|-------|---------|-------------|---------|
| CS Level 1 | First major SCAR failure, 8D rejected twice, or first recurrence | Supplier performs 100% inspection of every delivery with documented results sent with each shipment | Until 5 consecutive clean deliveries received |
| CS Level 2 | Second recurrence or CS Level 1 insufficient | Third-party inspection agency performs 100% inspection at supplier facility before shipment; cost borne by supplier | Until re-audit achieves satisfactory VDA 6.3 P6 score AND 10 consecutive clean deliveries |
| CS Level 3 / Disqualification trigger | Three SCARs for same defect within 24 months, or single safety-critical escape reaching field | Full disqualification review process; parallel qualification of alternative supplier initiated; OEM customer notified | Indefinite — exit only through formal re-qualification |

### Escalation Communication Template

When escalating beyond the standard SCAR channel, send a formal escalation notice to the supplier's senior management:

```
Subject: Escalation Notice — SCAR [SCAR-YYYY-NNN] — [Supplier Name] — [Part Number]

This notice is sent to senior management of [Supplier Name] to inform you of an escalation 
in the status of the above Supplier Corrective Action Request.

Current status: [8D overdue / response rejected / recurrence detected / controlled shipping triggered]
Original issue date: [date]
Defect description: [one sentence from Section B]
Customer impact: [state impact]

Required immediate actions:
1. [Specific action with deadline]
2. [Specific action with deadline]

Failure to respond by [date] will result in:
- [Controlled shipping Level X implementation]
- [New business hold]
- [Customer notification]

Please confirm receipt and commitment to the above actions within 24 hours.

[Issuer name, title, contact]
```
