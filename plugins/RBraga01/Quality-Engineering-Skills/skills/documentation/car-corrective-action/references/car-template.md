---
name: car-template
type: reference
parent_skill: car-corrective-action
author: RBraga01
version: "1.0"
status: approved
created: "2026-06-06"
last_updated: "2026-06-06"
updated_by: RBraga01
reviewed_by: RBraga01
license: MIT
---

# CAR Document Template and Verification Reference

Complete Corrective Action Report template with field instructions, root cause / corrective action quality checklist, effectiveness verification methods, and CAR vs SCAR distinction.
Use alongside the [car-corrective-action](../SKILL.md) skill.

> **Scope:** This document provides the fill-in template with field-by-field instructions for each CAR section, a quality checklist for verifying that the corrective action genuinely addresses the root cause, effectiveness verification methods matched to characteristic type, and a clear distinction between an internal CAR and a supplier-directed SCAR. For the full CAR structure rationale, PFMEA AP revision guidance, closure criteria, and common writing failures, see [car-corrective-action SKILL.md](../SKILL.md).

---

## 1. CAR Document Template

Fields marked **(R)** must be completed before opening the CAR. Fields marked **(I)** are completed during investigation. Fields marked **(C)** are completed at or after closure.

---

### SECTION 1 — HEADER (R)

```
CORRECTIVE ACTION REPORT (CAR)
================================
CAR Number:              _______________    (Format: CAR-YYYY-NNN, unique, sequential)
                                            Tip: link to site NCR prefix where applicable, e.g. CAR-2026-047
NCR / Finding Reference: _______________    (NCR number, audit finding reference, or customer concern #)
Trigger type:            [ ] NCR — internal    [ ] NCR — customer    [ ] Audit finding (Major)
                         [ ] Audit finding (Minor)    [ ] Customer complaint    [ ] Field return
Date Opened:             _______________
Owner (name, not function): _______________
Owner's department:      _______________
Target Closure Date:     _______________    (ISO 9001 Major NC: typically ≤ 90 days; check CSR)
Closure Authority:       _______________    Title: _______________
Actual Closure Date:     _______________    (C)
```

**Field instructions:**
- **CAR Number:** Never share a number between two issues. If a CAR is withdrawn (e.g., duplicate issue identified), mark it VOID and record the reason.
- **Owner:** Must be a named person with the authority and access to implement actions. "Quality department" is not acceptable. If ownership will transition, update the field and log the change.
- **Closure Authority:** Must be a named quality manager or equivalent with authority to confirm that all closure criteria are met. The owner and the closure authority must be different people.
- **Target closure date:** Check the customer-specific requirement (CSR) if the trigger is a customer complaint or an external audit finding from an OEM. IATF 16949 audit major NCs typically have a 90-day deadline imposed by the certification body; the customer may impose a shorter one.

---

### SECTION 2 — PROBLEM SUMMARY (R)

```
PROBLEM SUMMARY
================
State the non-conformance in objective, factual terms. Match the NCR or audit finding verbatim.
Do not re-interpret or soften the finding at this stage.

One to two sentences maximum. Include: what failed, where it was detected, measured values vs.
specification where applicable, and the reference document (NCR number, finding number).

Problem statement:
___________________________________________________________________________
___________________________________________________________________________

Example (NCR-triggered):
"47 of 200 connector housings in lot 2026-05-12-A had pin insertion depth 0.6–1.5 mm below
the lower specification limit (5.0 ± 0.3 mm). Detected at incoming inspection (NCR-2026-0047)."

Example (audit finding-triggered):
"Audit finding F-06 (VDA 6.3 process audit, 2026-05-28, auditor: J.Smith): Work instructions
for assembly station AS-04 do not specify the torque setpoint for M6 fasteners identified as a
special characteristic in the Control Plan (Score 4, P6.2)."
```

**Field instructions:**
- Copy the defect description from the NCR or audit finding report exactly. Do not paraphrase. If there is an error in the original finding, note it but use the exact wording.
- For customer complaints: quote the customer's complaint text and attach the customer communication.
- The problem summary must not pre-judge root cause. Write what was observed, not what caused it.

---

### SECTION 3 — IMMEDIATE CONTAINMENT (R if not already documented in NCR)

```
IMMEDIATE CONTAINMENT
======================
If containment was already documented and executed at NCR stage, reference it here:
NCR reference for containment:  _______________
Containment confirmed complete: [ ] Yes    Date confirmed: _______________

If containment has NOT been documented elsewhere, define it here:
Containment action:          _______________
Responsible person:          _______________
Completion date:             _______________
Scope (what is affected):    _______________    (e.g., Lot 2026-05-12-A, WIP at station AS-04, all output since date X)
Verification of containment: _______________    (who verified, what was checked, result)
```

**Field instructions:**
- Containment is not a corrective action. It is a firefighting step — stop the bleeding. Do not confuse "sort and replace" with "prevent recurrence."
- If the CAR is triggered by an audit finding rather than a physical defect, containment may take the form of an interim control (e.g., 100% inspection until the permanent corrective action is implemented). Define and document it here.
- For safety-related NCRs: containment must also cover any product already in the customer's supply chain. If customer field stock may be affected, this must be noted and the customer notified.

---

### SECTION 4 — ROOT CAUSE ANALYSIS (I)

```
ROOT CAUSE ANALYSIS
====================
Method used:  [ ] 5-Why    [ ] Fishbone (Ishikawa)    [ ] Both    [ ] Other: _______________
Cross-functional team involved: [ ] Yes    [ ] No    Team members: _______________

ROOT CAUSE 1 — OCCURRENCE (Why was the non-conformance produced?)
─────────────────────────────────────────────────────────────────
5-Why chain or Fishbone summary:

Why 1: _______________
Why 2: _______________
Why 3: _______________
Why 4: _______________
ROOT CAUSE (occurrence): _______________

Confirmation / validation method:
[ ] Reproduction test (removed/restored RC → defect disappeared/reappeared)
[ ] Data correlation (statistical relationship confirmed)
[ ] Physical evidence (mechanism visible on failed part or process)
[ ] Record review (confirms absence of required control)
[ ] Other: _______________
Validation evidence reference: _______________

ROOT CAUSE 2 — ESCAPE (Why was the non-conformance not detected before reaching the next customer?)
────────────────────────────────────────────────────────────────────────────────────────────────────
5-Why chain:

Why 1: _______________
Why 2: _______________
Why 3: _______________
ROOT CAUSE (escape): _______________

Validation method: _______________
Validation evidence reference: _______________
```

**Field instructions:**
- **Two root causes are required.** A CAR with only an occurrence root cause is incomplete. An escape root cause explains the gap in the quality system — this is what auditors and customers look for.
- **The "Why 1" should be the immediate cause (the defect mechanism), not a re-statement of the problem.** Example: if the problem is "pin depth out of spec," Why 1 is not "pin depth was too shallow" — it is "insertion force was insufficient."
- **Stop the 5-Why at the actionable level.** You do not need to continue to "because humans make mistakes" — stop when you reach a specific, controllable factor in your process.
- **Validation is mandatory.** A root cause that has not been validated is a hypothesis. The CAR may only proceed to corrective action when the root cause is confirmed. If validation requires a production test, schedule it and record the result.
- **If you cannot validate the root cause:** state explicitly that the root cause is the most probable cause based on [specific evidence], and describe what additional data would confirm or refute it. Do not state an unvalidated root cause as confirmed fact.
- **Audit finding CARs:** the occurrence root cause explains why the system gap exists (e.g., "the WI template does not include a field for process parameter setpoints"); the escape root cause explains why it was not caught internally (e.g., "WI review checklist does not verify that all SC parameters are included").

---

### SECTION 5 — CORRECTIVE ACTIONS (I)

```
CORRECTIVE ACTIONS
===================
One corrective action must directly address each root cause. Enter one row per action.

───────────────────────────────────────────────────────────────────────────────────────────────────
# | Root cause addressed      | Corrective action (specific)  | Owner  | Target date | Status
───────────────────────────────────────────────────────────────────────────────────────────────────
1 | RC — Occurrence:          |                               |        |             |
  | [paste RC text]           | [specific action]             | [Name] | [Date]      | [ ] Open
  |                           |                               |        |             | [ ] Complete
──|───────────────────────────|───────────────────────────────|────────|─────────────|─────────────
2 | RC — Escape:              |                               |        |             |
  | [paste RC text]           | [specific action]             | [Name] | [Date]      | [ ] Open
  |                           |                               |        |             | [ ] Complete
───────────────────────────────────────────────────────────────────────────────────────────────────

Additional actions (if RC requires more than one action, or for systemic prevention):
───────────────────────────────────────────────────────────────────────────────────────────────────
3 |                           |                               |        |             | [ ] Open
4 |                           |                               |        |             | [ ] Open
───────────────────────────────────────────────────────────────────────────────────────────────────
```

**Field instructions:**
- **Specificity test:** Could someone who did not attend the CAR investigation meetings implement this action correctly from the text alone? If not, it is not specific enough.
- **Operator training alone:** Never acceptable as the sole corrective action. Training addresses knowledge gaps but does not prevent a person from forgetting, being replaced, or being under pressure. The system must change. If training is appropriate, it must accompany a systemic change (e.g., WI update, visual aid installed, poka-yoke added).
- **Document update actions:** Must specify: which document, what change, what new revision number it will receive, who approves it, and by when. "Update the WI" is not acceptable. "Update WI-AS-04 to include torque setpoint 12 ± 1 Nm for M6 fasteners (item 3.4), rev D, to be approved by [Name] by [Date]" is acceptable.
- **Poka-yoke actions:** Specify the device type, what failure it detects/prevents, where it will be installed, and who will verify its effectiveness before use in production.

---

### SECTION 6 — IMPLEMENTATION EVIDENCE (C)

```
IMPLEMENTATION EVIDENCE
========================
For each corrective action, record the evidence that it was implemented.
Verbal implementation is not evidence. Documents must have new revision numbers.

───────────────────────────────────────────────────────────────────────────────────────────────
Action # | Evidence description                  | Evidence reference    | Date verified
───────────────────────────────────────────────────────────────────────────────────────────────
1        |                                       |                       |
2        |                                       |                       |
3        |                                       |                       |
───────────────────────────────────────────────────────────────────────────────────────────────

Documents revised as part of this CAR:
Document name / number   | Old revision | New revision | Approval date | Approved by
─────────────────────────|──────────────|──────────────|───────────────|────────────
                         |              |              |               |
                         |              |              |               |
```

**Field instructions:**
- **Each action needs its own evidence entry.** Do not combine evidence for multiple actions.
- **Acceptable evidence types:** revised document with new revision number and approval date; signed training attendance records naming operators trained; photograph of installed poka-yoke device with label showing installation date; equipment calibration record showing updated setpoint; process parameter record showing new setting is active.
- **Not acceptable:** "action completed per verbal confirmation from [Name]"; undated photos; training records without operator names.

---

### SECTION 7 — VERIFICATION OF EFFECTIVENESS (VOE) (C)

```
VERIFICATION OF EFFECTIVENESS (VOE)
=====================================
VOE method:      [ ] Monitoring period — zero recurrence    [ ] SPC / capability data
                 [ ] Audit / process observation            [ ] Inspection results
                 [ ] Customer scorecard data                [ ] Other: _______________

VOE metric:      _______________    (e.g., defect rate for characteristic X at station Y; Cpk of pin depth)
VOE volume:      _______________    (e.g., 3 consecutive deliveries; 100 production cycles; 30 subgroups)
VOE target:      _______________    (e.g., zero recurrence of defect type A; Cpk ≥ 1.33 sustained)
VOE basis:       _______________    (Why is this volume/duration sufficient? State the rationale)
VOE start date:  _______________    (date corrective actions were implemented in production)
VOE end date:    _______________    (date monitoring period completed)

VOE RESULTS
────────────
Monitoring data reference:   _______________
Result summary:              _______________
Recurrence observed:         [ ] Yes — CAR cannot close; return to Section 4    [ ] No
Cpk / capability result:     _______________    (if applicable)

VOE verdict:    [ ] EFFECTIVE — proceed to closure    [ ] NOT EFFECTIVE — return to root cause analysis
VOE assessed by: _______________    Date: _______________
```

**Field instructions:**
- **Define the VOE before collecting data.** Do not determine what "counts as effective" after you have seen the results. The method, metric, volume, and target must be defined and approved before the monitoring period starts.
- **Volume rationale:** You must justify the chosen monitoring volume. The minimum basis is: if the baseline defect rate was X%, what sample size gives ≥ 95% confidence that the new rate is below X%? For a process-change CAR where the mechanism has been eliminated rather than detected, the reasoning is different (confirm the new process condition is sustained) — state that explicitly.
- **For customer complaint CARs:** the VOE period typically cannot start until the first production lot under the new conditions is delivered to the customer and accepted. State this explicitly.
- **For audit finding CARs:** the VOE is typically a follow-up audit observation confirming the finding has been corrected and is sustained. Schedule a follow-up audit walkthrough for the specific process element and document the result.

---

### SECTION 8 — SYSTEMIC PREVENTION AND HORIZONTAL DEPLOYMENT (C)

```
SYSTEMIC PREVENTION
====================
Could this root cause exist in other parts, products, processes, or plants?
[ ] Yes    [ ] No    [ ] Unknown — investigation required

If Yes — affected areas identified:
───────────────────────────────────────────────────────────────────────────────────────────
Area / part / process         | Root cause present? | Action taken        | Completion date
──────────────────────────────|─────────────────────|─────────────────────|────────────────
                              |                     |                     |
                              |                     |                     |
───────────────────────────────────────────────────────────────────────────────────────────

Horizontal deployment complete: [ ] Yes    [ ] Not applicable — rationale: _______________
```

---

### SECTION 9 — DOCUMENT UPDATES (C)

```
DOCUMENT UPDATES
=================
[ ] PFMEA updated    Reference failure mode: _______________    New AP: _______________
                     PFMEA revision: ___    Approval date: _______________
[ ] Control Plan updated    CP revision: ___    Approval date: _______________
[ ] Work Instruction(s) updated    WI number(s): _______________    Rev(s): _______________
[ ] No document updates required — rationale: _______________

Documents not applicable to this CAR: _______________
```

---

### SECTION 10 — LESSONS LEARNED (C)

```
LESSONS LEARNED
================
What is the key learning from this CAR that should be applied to future designs or processes?
Maximum 3 sentences. Focus on what the system should do differently, not just what happened.

Lessons learned statement:
___________________________________________________________________________
___________________________________________________________________________

Lessons learned register entry number: _______________    Date filed: _______________
Shared with (teams / projects / sites): _______________
```

---

### SECTION 11 — CLOSURE (C)

```
CLOSURE SIGN-OFF
=================
All closure criteria verified:
[ ] Root cause of occurrence validated and documented
[ ] Root cause of escape validated and documented
[ ] Corrective actions implemented with revision numbers and approval dates
[ ] VOE complete: monitoring volume reached, zero recurrence confirmed (or effectiveness data reviewed)
[ ] PFMEA updated (or explicitly documented as not applicable with rationale)
[ ] Control Plan updated (or not applicable with rationale)
[ ] Work Instructions updated (or not applicable with rationale)
[ ] Horizontal deployment documented
[ ] Customer notified of closure (if required by trigger type or CSR)
[ ] Lessons learned filed

Outstanding items at closure (if any):  [ ] None    [ ] See notes: _______________

Closed by (closure authority):  _______________    Date: _______________
Signature:                       _______________
```

---

## 2. Root Cause vs. Corrective Action Quality Checklist

Use this checklist to verify that the corrective action genuinely addresses the root cause, before submitting the CAR for approval or sending to a customer.

### Part A — Root Cause Quality

| Check | Pass criteria | Red flag |
|-------|--------------|----------|
| Specificity | Root cause names a specific condition, parameter, or gap — not a category. | "Human error," "lack of training," "process variability," "insufficient quality." |
| Causality | Removing the root cause would prevent the defect from occurring. Test: "If we fix this, can the defect still happen?" — answer must be "No." | Root cause and defect are correlated but removing RC does not guarantee the defect is prevented. |
| Actionability | The root cause can be addressed by a specific, permanent action. | Root cause is a fundamental uncertainty or an external factor outside the organisation's control. |
| Validation | Root cause is confirmed by evidence (reproduction, data, record review). | Root cause is stated as confirmed but supported only by team consensus. |
| Two causes present | Both occurrence RC and escape RC are documented and distinct. | Only one RC provided. OR escape RC is "operator did not notice" without going deeper. |

### Part B — Corrective Action Quality

| Check | Pass criteria | Red flag |
|-------|--------------|----------|
| Direct linkage | There is a clear logical chain from RC → corrective action → prevention of RC recurring. | Action addresses a symptom or intermediate cause, not the confirmed root cause. |
| Specificity | Action states: what will change, how, to what standard, by whom, by when. | "Improve process," "review procedure," "increase awareness," "retrain staff." |
| Permanence | Action changes the system — a document, a device, a process parameter, a verification step. | Action relies entirely on operator behaviour, memory, or attention. |
| Feasibility | Action has an owner with the authority and access to implement it. | Owner is a function or department rather than a named individual. |
| Verifiability | It is possible to confirm whether the action was implemented or not. | Action is inherently subjective or unverifiable (e.g., "ensure operators are more careful"). |
| Proportionality | The depth and scope of the action matches the severity of the non-conformance. | Trivial action for a safety NC; excessive corrective actions for a paperwork minor finding. |

### The Training Test

Apply this test whenever "operator training" appears as a corrective action:

> "If this operator is replaced by a new hire next month, will the new hire, following the existing procedures, also produce this defect?"

- If **Yes**: training is addressing a people problem but not a system problem. Training may be part of the action but cannot be the whole action. The system (WI, procedure, poka-yoke) must change.
- If **No**: training is appropriate because the root cause was genuinely a knowledge gap and the system (updated WI, clear standard) will prevent recurrence even with personnel turnover.

---

## 3. Effectiveness Verification Methods by Characteristic Type

Choose the VOE method based on the type of characteristic being corrected. The table below provides the standard method, minimum sample basis, and what "effective" looks like.

| Characteristic type | Primary VOE method | Minimum volume | "Effective" definition |
|---------------------|-------------------|----------------|------------------------|
| **Variable — SC (special characteristic)** | SPC data review (Cpk on corrected characteristic) | 25 subgroups minimum under new conditions; 100 individual measurements for Cpk calculation | Cpk ≥ 1.33 sustained; no out-of-control signals on the relevant chart |
| **Variable — non-SC dimensional** | Inspection results — zero recurrence over monitoring period | 3 consecutive delivery lots or 60 production units (whichever greater) | Zero non-conforming measurements on the corrected characteristic across the monitoring volume |
| **Functional / electrical / performance parameter** | End-of-line test pass rate | 50 consecutive production units at final test | Zero failures on the corrected parameter; no degraded test margins on related parameters |
| **Attribute — visual or assembly** | In-process inspection + outgoing audit | 5 production runs or 200 units (whichever greater) | Zero defects of the corrected type detected at in-process inspection or outgoing |
| **Audit finding — procedure or documentation gap** | Follow-up audit observation at the specific process element | Single follow-up visit, minimum 30 days after implementation | Auditor confirms the finding is resolved (process observed; documents verified at current revision) |
| **Audit finding — systemic gap (multiple departments or sites)** | Follow-up audit at each affected site or process | One follow-up audit per site; sample two sites if more than three are affected | All sampled sites confirm the corrective action is implemented and sustained |
| **Process parameter drift (SPC Rule 3 — trend)** | SPC monitoring with extended control period | 15 subgroups after the trend-correcting action | No re-occurrence of the trend signal for 15 subgroups; range chart stable |
| **Customer complaint — field return** | Customer feedback and warranty data | 90 days of field data after corrected production begins shipping | Zero warranty returns or complaints of the same type from production lots made after implementation date |
| **Supplier sub-component** | Incoming inspection results on receiving dock | 5 consecutive deliveries under the new incoming inspection plan | Zero non-conforming units on the corrected characteristic across all monitored deliveries |

---

## 4. CAR vs. SCAR Distinction

Understanding when to use a CAR vs. a SCAR prevents duplication, confusion in routing, and ensures the correct authority is managing the issue.

| Dimension | CAR (Corrective Action Report) | SCAR (Supplier Corrective Action Request) |
|-----------|-------------------------------|-------------------------------------------|
| **Direction** | Internal — issued by quality to an internal process owner OR received by the organisation from a customer / auditor | External — issued by the organisation TO a supplier; or received by the organisation FROM a customer and caused by a supplier |
| **Trigger** | Internal NCR, internal audit finding, customer complaint (where internal root cause), recurring internal defect | Supplier NCR, supplier-caused customer complaint, supplier audit finding, supplier delivery failure |
| **Owner** | Internal quality engineer / process owner | Supplier Quality Engineer (internally); assigned supplier contact (externally) |
| **Response authority** | Internal quality management | Supplier's quality management |
| **Follow-up mechanism** | Internal VOE per Section 7 | SCAR effectiveness verification including supplier document updates and potential on-site verification |
| **Escalation path** | Internal: escalate to site quality manager → VP Quality | External: escalate to supplier management → controlled shipping → disqualification |
| **Document control** | Filed in the organisation's quality management system | Filed in the supplier quality record AND the organisation's QMS |
| **PFMEA update responsibility** | Organisation's process PFMEA owner | Supplier's PFMEA (organisation verifies receipt and content) |

### When a customer-issued concern becomes both a CAR and a SCAR

If a customer complaint is received and investigation reveals the root cause is at a sub-supplier:

1. **Open a CAR internally** — to manage the organisation's response to the customer, document the investigation, and track the systemic prevention (including supplier oversight gap).
2. **Issue a SCAR to the sub-supplier** — to direct the sub-supplier's corrective action, obtain their 8D, and verify effectiveness.
3. **Link both documents** — the CAR references the SCAR number; the SCAR references the CAR and the customer concern.
4. **The CAR cannot close until the SCAR is closed and effective** — the organisation's corrective action is incomplete until the supplier has demonstrated permanent resolution.

The internal CAR in this scenario must also address the systemic question: "Why did our incoming inspection / sub-supplier monitoring system allow this non-conformance to reach our customer?" — this is the escape root cause at the organisation level, separate from the supplier's escape root cause.
