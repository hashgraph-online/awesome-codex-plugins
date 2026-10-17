---
name: pdca-improvement
description: >-
  Run a PDCA cycle, Plan Do Check Act improvement cycle, or structured improvement project.
  Guides through problem analysis, piloting, verification, and standardisation. Distinguished
  from 8D: PDCA is for proactive improvement initiatives, 8D is for reactive defect response.
  Use for process optimisation, lessons learned implementation, and quality objectives.
license: MIT
metadata:
  author: RBraga01
  version: "1.1"
  iso-9001: "10.3"
  iatf-16949: "10.3.1"
  domain: quality-engineering
  subdomain: problem-solving
  industries: automotive,electronics,aerospace,medical,general
  status: approved
  created: "2026-06-01"
  last_updated: "2026-06-06"
  updated_by: migmcc
  reviewed_by: RBraga01
  standard_edition: "ISO 9001:2015"
---

# PDCA Improvement Cycle

## When to use

Use PDCA for:
- Continuous improvement initiatives (not problem reactions — use 8D for that)
- Implementing a process optimisation with uncertain outcome
- Piloting a change before full deployment
- Structured improvement from lessons learned or audit findings
- Meeting a quality objective that requires a new approach

**Key distinction from 8D:** PDCA is proactive or slow-burn improvement. 8D is reactive to a specific defect or failure. Both use root cause analysis, but PDCA has a broader scope and a pilot step before full deployment.

**When PDCA is used for corrective action** (e.g., responding to an audit finding or recurring NC): a [Corrective Action Request (CAR)](../../documentation/car-corrective-action/) must also be opened to document root cause, actions, and VOE per ISO 9001 §10.2. PDCA is the improvement methodology; the CAR is the governance record.

## Prerequisites

- Improvement goal defined (with target metric)
- Baseline data available (current performance)
- Owner and resources assigned

---

## Workflow

### PLAN — Analyse and define the approach

1. **Define the current situation**
   - What is the problem or improvement opportunity?
   - What is the current measured performance? (baseline)
   - What is the target? (SMART: Specific, Measurable, Achievable, Relevant, Time-bound)

2. **Analyse root cause**
   - Use [Fishbone](../fishbone-analysis/) and [5-Why](../5why-root-cause/) to understand why current performance is below target
   - Use data: Pareto charts, run charts, capability studies

3. **Develop the improvement plan**
   - What specific actions will close the gap?
   - Who is responsible for each action?
   - What is the timeline?
   - What resources are needed?
   - What risks does the change introduce? Review the applicable PFMEA — does this change add or remove a failure mode? Does it affect any existing prevention or detection control?

4. **Define the pilot scope**
   - Which process, line, or area will pilot the change?
   - What volume or duration is needed to validate effectiveness? Define this before starting the pilot — do not decide after seeing results.
   - What will you measure, and how?

**Pilot volume guidance:** as a minimum, the pilot should produce enough output to statistically distinguish signal from noise. Typical references:
- Process capability change: minimum 30 consecutive cycles or units under the new conditions
- Defect rate reduction: minimum volume to yield at least 5 expected events at the old rate (e.g., if baseline defect rate = 2%, minimum pilot = 250 units)
- Time-dependent improvement: minimum 4 weeks of sustained performance data

**Plan gate:** Is the root cause understood? Is the pilot scope defined with explicit volume/duration minimum? Is success measurable against a specific target?

---

### DO — Implement (pilot)

1. Implement the planned changes in the pilot scope only
2. Train affected personnel
3. Execute and collect data during the pilot
4. Document what actually happened vs. what was planned (deviations are data)

**Do not deploy broadly at this stage.** The pilot is to learn, not to commit.

---

### CHECK — Verify results

Compare pilot results against the Plan targets:

| Metric | Baseline | Target | Pilot result | Gap closed? |
|--------|----------|--------|--------------|-------------|
| [KPI 1] | | | | |
| [KPI 2] | | | | |

Ask:
- Did the change produce the expected improvement?
- Were there any unexpected negative effects?
- Is the improvement sustainable (stable over time) or a one-time effect?
- Was the pilot conducted under representative conditions (same operators, same materials, same environment as production)?

**Check gate:**
- If target met → proceed to Act (standardise)
- If partially met → revise Plan, run another Do-Check cycle
- If not met → return to Plan, re-analyse root cause

---

### ACT — Standardise or revise

**If the pilot succeeded:**

1. Update process documents: work instructions, control plan, PFMEA — each must be revised to reflect the new process
2. If the PFMEA includes failure modes related to the improved process step, update affected S/O/D ratings and AP
3. Deploy to all applicable areas (horizontal deployment) — list each area and confirm deployment is complete
4. Train all affected personnel — training records required
5. Set up ongoing monitoring to confirm the improvement holds
6. Share lessons learned — enter in lessons learned register

**If the pilot failed or was inconclusive:**

1. Document what was learned
2. Revise the Plan (new root cause hypothesis or new approach)
3. Repeat the cycle

**Do not standardise an unverified change.** Standardising a failed pilot permanently embeds the problem.

---

### Required PDCA documentation (ISO 9001 §10.3)

For the cycle to be auditable, the following records must exist at closure:

- [ ] Baseline measurement with data source and date
- [ ] Root cause analysis (fishbone or 5-Why output)
- [ ] Pilot plan with explicit volume/duration minimum and success criteria
- [ ] Pilot execution data (before/after comparison)
- [ ] Check gate decision (proceed / revise / restart) with supporting data
- [ ] Updated PFMEA, Control Plan, and Work Instructions (if applicable) with new revision numbers and approval dates
- [ ] Training records for all affected personnel
- [ ] Horizontal deployment log (areas assessed, actions taken)
- [ ] Lessons learned register entry

---

## Gate summary

| Gate | Key question | Pass criterion |
|------|-------------|----------------|
| Plan | Is root cause understood and pilot scoped? | Root cause confirmed, target measurable, pilot volume/duration defined |
| Do | Was the pilot conducted as planned? | Actions implemented, data collected per plan |
| Check | Did the change achieve the target? | Target metric met or exceeded; minimum pilot volume reached |
| Act | Are documents updated and deployment complete? | PFMEA/CP/WI revised, training done, horizontal deployment documented |

---

## Common mistakes

- **Skipping Plan** — jumping straight to Do without understanding root cause
- **Undefined pilot volume** — deciding after the pilot how much data is "enough"; set the minimum before starting
- **Skipping Check** — deploying broadly after pilot without verifying data
- **Treating Act as permanent before Check** — standardising before the pilot result is confirmed
- **One cycle only** — PDCA is a cycle; if the first cycle doesn't solve it, run another
- **Using PDCA for urgent defects** — for customer complaints or safety issues, use 8D instead
- **Not updating PFMEA** — a process change without PFMEA update leaves the risk register inaccurate

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
| 1.1 | 2026-06-04 | @migmcc | Polished PDCA cycle workflow and D6 verification integration |
