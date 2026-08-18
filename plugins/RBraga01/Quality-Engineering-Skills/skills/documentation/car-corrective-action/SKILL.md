---
name: car-corrective-action
description: >-
  Write a corrective action report, CAPA, respond to an NCR or audit finding, or document
  an 8D D5 root cause action. Covers the full CAR structure: root cause analysis, corrective
  actions, implementation evidence, and verification of effectiveness (VOE) per ISO 9001
  §10.2. Use for any quality escape requiring documented systemic corrective action.
license: MIT
metadata:
  author: RBraga01
  version: "1.1"
  iso-9001: "10.2"
  iatf-16949: "10.2.3"
  domain: quality-engineering
  subdomain: documentation
  industries: automotive,electronics,aerospace,medical,general
  status: approved
  created: "2026-06-01"
  last_updated: "2026-06-04"
  updated_by: migmcc
  reviewed_by: RBraga01
  standard_edition: "ISO 9001:2015"
---

# Corrective Action Request (CAR) Writing

## When to use

A CAR is written in response to:
- An NCR requiring permanent corrective action
- A customer complaint
- An internal or external audit finding (Major or Minor non-conformance)
- A recurring non-conformance requiring systemic correction

The CAR is the documented evidence that the problem was analysed, corrected, and prevented from recurring. ISO 9001 §10.2.1 requires documented information of the actions taken and their results. For IATF 16949 audit Major NCs, CARs must typically be closed within 90 days; check the applicable CSR for customer-specific closure deadlines.

## Key distinction from NCR

| NCR | CAR |
|-----|-----|
| What is wrong (objective facts) | Why it is wrong + what is being done about it |
| Detection point and evidence | Root cause analysis + actions |
| Severity and disposition | Verification of effectiveness |
| Written immediately | Written after investigation |

A CAR references the NCR but extends it into corrective action territory.

---

## CAR structure

### 1. Header

| Field | Content |
|-------|---------|
| CAR number | Traceable to NCR or audit finding |
| NCR / finding reference | Links this CAR to the trigger event |
| Date opened | |
| Owner | Responsible person (name, not function) |
| Target closure date | |
| Closure authority | Named person with authority to close this CAR (quality manager or equivalent) |
| Actual closure date | (filled on closure) |

### 2. Problem summary

One or two sentences summarising the NCR or finding. Objective, factual. Must match the NCR description exactly — no new interpretation.

Example:
> "47 of 200 connector units in lot 2026-05-12-A had pin insertion depth 0.6–1.5 mm below lower specification limit (5.0 ± 0.3 mm). Detected at incoming inspection (NCR-2026-0047)."

### 3. Immediate containment (if not already in NCR)

Confirm containment is in place. If documented in the NCR, reference it. If not yet done, define it here.

### 4. Root cause analysis

This is the core of the CAR. Use structured methodology:

**Recommended tools:**
- [5-Why](../../problem-solving/5why-root-cause/) for linear cause chains
- [Fishbone](../../problem-solving/fishbone-analysis/) for complex or multi-factor problems

**Identify two root causes:**
1. **Root cause of occurrence** — why did the non-conformance happen?
2. **Root cause of escape** — why was it not detected before it reached the next customer?

**Document the chain, not just the conclusion:**

```
Root cause of occurrence:
Why: Connector pin depth OOS → Why: insertion force insufficient → 
Why: pneumatic jig set to wrong pressure → Why: pressure setpoint not in work instruction →
Root cause: Work instruction for Station 3 does not specify jig pressure setpoint.

Root cause of escape:
Why: Not detected at our outgoing inspection → Why: no depth measurement in outgoing
inspection plan → Root cause: Control Plan does not include pin depth at outgoing.
```

**Validation:** state how the root cause was confirmed. Acceptable validation methods:
- Reproduction test (demonstrated that removing/restoring the root cause produces/prevents the defect)
- Data correlation (statistical relationship between root cause variable and defect occurrence)
- Physical evidence (inspection of the failed part or process reveals the causal mechanism)
- Direct record review (confirms the absence of the required control)

A root cause supported only by team opinion (not validated by evidence) cannot be used as the basis for CAR closure.

### 5. Corrective actions

One corrective action for each root cause. The action must directly address the root cause — not a symptom.

| # | Root cause addressed | Corrective action | Owner | Target date |
|---|---------------------|-------------------|-------|-------------|
| 1 | WI missing jig pressure | Update WI-Station-3 to specify jig pressure 4.5 ± 0.2 bar | [Name] | 2026-06-05 |
| 2 | CP no depth check at outgoing | Add pin depth measurement to Control Plan at outgoing, 10% sample, n=5 per batch | [Name] | 2026-06-05 |

**Action quality check:**
- Does this action, if implemented, prevent the root cause from occurring again?
- Is it specific (who does what, by when)?
- Can its implementation be verified?

### 6. Implementation evidence

For each corrective action, document that it was actually implemented:

| Action | Evidence of implementation | Date verified |
|--------|---------------------------|---------------|
| WI updated | WI-Station-3 rev C, approved 2026-06-04, attached | 2026-06-04 |
| Training conducted | Training attendance record attached (4 operators) | 2026-06-04 |
| Control Plan updated | CP rev F, approved 2026-06-04, attached | 2026-06-04 |

Documents must be revised with a new revision number and approval date. Verbal implementation is not evidence.

### 7. Verification of effectiveness (VOE)

This is where most CARs fail. The action is implemented, but nobody checks whether it actually prevents the defect.

**VOE requirements (ISO 9001 §10.2.1.e):**

1. **Method:** how will you check if the corrective action worked? (data collection, monitoring period)
2. **Metric:** what will you measure? (defect rate, inspection results)
3. **Volume/duration:** what sample size or time period constitutes sufficient evidence?
4. **Target:** what result confirms the action was effective?

**VOE minimum volume guidance:**
- For a defect with known base rate: the VOE sample must be large enough to observe at least one recurrence if the action had failed. Example: if baseline defect rate was 5%, a zero-defect sample of 60 units gives 95% confidence the rate is now below 5%.
- For process parameter changes: minimum 30 consecutive production cycles under the new conditions, or as defined by the Control Plan sampling frequency × 3 periods.
- For detection control improvements: minimum one full inspection cycle of the affected product family with zero escapes.
- Minimum in all cases: state the volume used and the basis for choosing it. "Zero defects in 10 units" is not a valid VOE for a high-volume process.

**VOE result:**
- Record the actual results after the monitoring period
- State: Effective / Not effective
- If not effective: return to root cause analysis and repeat

### 8. AP revision (AIAG-VDA, if applicable)

If the non-conformance relates to a PFMEA failure mode with an Action Priority (AP) rating:

- After verified implementation of the corrective action, the PFMEA must be updated with a revised S, O, and/or D rating
- The revised AP (AP-revised) must reflect the improvement — it must be lower than the original AP or documented with justification if unchanged
- Revised AP is recorded only after VOE is complete, not at the time of action planning

### 9. Systemic prevention and horizontal deployment

Ask: could this same root cause exist in similar parts, processes, or product families?

If yes:
- List the similar areas
- Document the actions taken to extend the corrective action
- Evidence that horizontal deployment is complete

### 10. Lessons learned

One or two sentences capturing the key learning for future reference:

> "Work instruction templates for assembly stations must include all process parameter setpoints. Control Plans must cover outgoing inspection of all safety-relevant characteristics."

File in the lessons learned register and reference in PFMEA update.

---

## Closure criteria

A CAR may only be closed when ALL of the following are true, and the closure authority (named in the header) has signed off:

- [ ] Root causes of occurrence and escape are documented with validation evidence
- [ ] Corrective actions are implemented and documented with revision numbers and approval dates
- [ ] VOE is complete with documented sample volume and confirms effectiveness
- [ ] PFMEA is updated (revised failure mode entry, revised AP if applicable)
- [ ] Control Plan is updated (if detection control changed)
- [ ] Work Instructions are updated (if process control changed)
- [ ] Horizontal deployment is documented
- [ ] Customer notified of closure (if CAR was triggered by customer complaint or CSR-required notification)
- [ ] Closure authority sign-off obtained

---

## Common mistakes

- **"Retrain operators"** as a corrective action for human error — this is never sufficient alone; the system that allowed the error must be changed
- **Closing without VOE** — the most common reason for recurring non-conformances
- **VOE on insufficient sample** — "zero defects in 5 units" is not effectiveness verification; define the minimum volume before collecting data
- **Implementing actions without updating PFMEA and Control Plan** — next audit will find the gap
- **Generic actions** — "review procedures" → not specific; must state which procedure, revised to say what, by whom, by when
- **Closing without named authority sign-off** — any team member closing a CAR without defined authority is a governance gap
- **Missing AP revision** — when PCA addresses a PFMEA failure mode, the revised AP must be recorded after VOE

---

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
| 1.0 | 2026-06-01 | @RBraga01 | Initial release |
| 1.1 | 2026-06-04 | @migmcc | Expanded CAR linkage to D5-D6, added effectiveness verification requirements |
