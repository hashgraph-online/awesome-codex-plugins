---
name: dmaic
description: >-
  DMAIC (Define-Measure-Analyze-Improve-Control) — Six Sigma structured problem-solving for
  chronic, data-driven quality improvement projects. Use when a problem recurs despite corrective
  actions, when a process needs systematic capability improvement, or when a customer requests
  a Six Sigma approach. Use 8D for reactive single-incident problems; use DMAIC for recurring
  systemic issues requiring statistical analysis. Covers IATF 16949 §10.1 and ISO 9001 §10.3.
license: MIT
metadata:
  author: RBraga01
  version: "1.1"
  iso-9001: "10.3"
  iatf-16949: "10.1"
  domain: quality-engineering
  subdomain: problem-solving
  industries: automotive,electronics,aerospace,medical,general
  status: approved
  created: "2026-06-06"
  last_updated: "2026-06-06"
  updated_by: migmcc
  reviewed_by: RBraga01
  standard_edition: "Six Sigma DMAIC / ISO 9001:2015 §10.3 / IATF 16949:2016 §10.1"
---

# DMAIC (Six Sigma Problem Solving)

## When to use

Use DMAIC when:
- A problem has recurred multiple times despite previous corrective actions
- The process needs measurable, data-driven capability improvement (Cpk improvement target)
- The root cause is unknown and requires statistical analysis to identify
- A customer requires a Six Sigma approach or asks for a DMAIC report
- The improvement opportunity involves eliminating chronic waste (rework, scrap, test failures)

**Use 8D instead when:** The problem is a single customer complaint, an escape to the field, or requires immediate containment. 8D is reactive and fast. DMAIC is proactive and thorough — it takes weeks to months.

**Use PDCA instead when:** The improvement is incremental and the root cause is already known or assumed.

## Prerequisites

- A defined problem with measurable impact (reject rate, Cpk, scrap cost, defect count)
- Baseline data available or collectable
- Process owner and cross-functional team assigned
- Management support and a time budget (minimum 4–12 weeks depending on project scope)

## Workflow

### Phase 1 — DEFINE

**Objective:** Define the problem, the scope, the team, and the goal in measurable terms.

**Key tools and deliverables:**

**Project Charter** — The DMAIC starts and ends here. Contains:
- Problem statement: what is happening, where, since when, how much (measured impact)
- Goal statement: specific, measurable target (e.g., "Reduce connector reject rate from 3.2% to 0.5% by Q3")
- Scope: what is IN and OUT of scope (use Is/Is-Not to define boundaries)
- Business case: financial or customer impact ($, PPM, warranty cost)
- Team: Champion, Black Belt/Green Belt, process owner, operators, engineering

**SIPOC diagram:**
- Suppliers → Inputs → Process → Outputs → Customers
- Defines the process at a high level before diving into detail
- Identifies all inputs that could affect the output (Y)

**Voice of the Customer (VOC) → CTQ:**
- What does the customer care about? (VOC)
- Translate to a measurable Critical to Quality (CTQ) characteristic
- The CTQ becomes the Y (output) the project will improve

**Gate criteria to exit Define:**
- Problem is specific and measurable
- Goal is agreed with the Champion
- Scope is bounded
- Team is assigned and available

---

### Phase 2 — MEASURE

**Objective:** Establish the current baseline and validate the measurement system.

**Key tools and deliverables:**

**Process map (detailed):**
- Map every step of the process as it IS (not as it should be)
- Identify where defects are created or detected
- Mark each step: Value-Added (VA), Non-Value-Added (NVA), or Required Non-Value-Added

**Data collection plan:**
- What will be measured? (the Y and key process inputs Xs)
- How will it be measured? (gauge, method)
- How many samples? (for capability: minimum 100 pieces)
- Who will collect data? When? Where?

**MSA (Gauge R&R):**
- Validate the measurement system for the CTQ before collecting data
- %GRR < 30% required; <10% preferred
- If measurement system is inadequate: fix it before proceeding

**Baseline capability:**
- Calculate current Cpk/Ppk for the CTQ
- Establish current defect rate (PPM or %)
- This baseline is the MEASURE gate deliverable — do not proceed without it

**Gate criteria to exit Measure:**
- Baseline Cpk/PPM established with statistical confidence
- MSA complete and measurement system adequate
- Data collection plan executed with sufficient data

---

### Phase 3 — ANALYZE

**Objective:** Identify and confirm the root cause(s) of the problem using data.

**Key tools and deliverables:**

**Fishbone / Cause & Effect diagram:**
- Brainstorm potential causes using 6M (Man, Machine, Method, Material, Measurement, Mother Nature)
- All potential causes are hypotheses at this stage — none are confirmed

**Is/Is-Not analysis:**
- Scope the problem precisely — what IS affected vs. what IS NOT
- Narrows the hypothesis list before investing in analysis

**Multi-Vari study:**
- Understand whether variation is: positional (within-part), cyclical (part-to-part), or temporal (time-based)
- Identifies the dominant family of variation — directs the investigation

**Hypothesis testing:**
Confirm or reject hypotheses statistically. Selection guide:

| Situation | Tool |
|-----------|------|
| Compare means of 2 groups (continuous Y, e.g., Shift A vs. B) | t-test (paired if same parts measured twice) |
| Compare means of 3+ groups (e.g., 3 machines, 4 operators) | One-way ANOVA |
| Categorical Y (pass/fail) vs. categorical X (supplier, shift) | Chi-square test |
| Continuous Y vs. continuous X (does temperature predict dimension?) | Pearson correlation; then regression to quantify |
| Multiple Xs affecting one Y | Multiple regression; confirm no multicollinearity |

Use p < 0.05 as the significance threshold unless a different risk level is warranted. Always check the test's assumptions (normality for t-test/ANOVA; independence for chi-square).

**Root cause confirmation:**
- A root cause is NOT confirmed until data proves it
- Reject "human error" as a root cause — it is a symptom; ask why the error was possible
- Confirmed root causes: demonstrate that when the Xs change, the Y changes predictably

**Gate criteria to exit Analyze:**
- Root cause(s) confirmed with data (not assumed)
- Cause-and-effect quantified (Y = f(X) relationship established)
- Team agrees on which Xs to improve

---

### Phase 4 — IMPROVE

**Objective:** Develop, test, and implement solutions that address the confirmed root causes.

**Key tools and deliverables:**

**Solution generation:**
- Brainstorm solutions for each confirmed root cause
- Evaluate solutions: impact vs. effort vs. risk
- Do NOT select solutions based on opinion — test them

**Pilot / Design of Experiment (DOE):**
- Test the proposed solution on a small scale before full implementation
- DOE: systematically vary multiple factors to find the optimal process settings
- Simple experiments: OFAT (One Factor At A Time) for straightforward improvements

**Solution validation:**
- Run a production pilot with the solution in place
- Collect data: does the Y improve as predicted?
- Calculate new Cpk/PPM — compare to baseline and goal

**Implementation plan:**
- Who does what, by when, to implement the solution at full scale
- Change management: update Process Flow, PFMEA, Control Plan, Work Instructions, training

**Gate criteria to exit Improve:**
- Solution tested and statistically validated (not just "it seems better")
- Cpk/PPM improvement demonstrated in pilot data
- Implementation plan complete and approved

---

### Phase 5 — CONTROL

**Objective:** Sustain the gains — prevent the process from reverting to the old state.

**Key tools and deliverables:**

**Updated Control Plan:**
- Add new controls for the Xs identified in Analyze
- Define monitoring frequency and reaction plan for out-of-control conditions

**SPC / Statistical monitoring:**
- Install control charts on the critical Xs and the Y
- Set control limits from the improved process data
- Define who monitors and how often

**Updated PFMEA:**
- New failure modes identified during the project must be added
- Controls added in Improve must be reflected in the PFMEA current controls column

**Updated Work Instructions:**
- Document the new process steps, settings, or behaviours required
- Train operators and verify understanding

**Mistake-proofing (Poka-yoke):**
- For any root cause that was behavioural or procedural: add error-proofing to prevent recurrence
- Error-proofing is the highest-reliability control — prefer it over inspection or SPC alone

**Project handover:**
- Transfer ownership from the project team to the process owner
- Establish a 3–6 month monitoring period with defined Cpk targets; specify the minimum Cpk that constitutes "sustained improvement" (e.g., Cpk ≥ 1.33 for a minimum of 3 consecutive months of production data — not 3 months of calendar time)
- Close the project only when the monitoring criterion is met with actual production data — not lab data or pilot data

**Final project report:**
- Before and after: Cpk, PPM, financial savings
- Lessons learned for future projects

**Gate criteria to close the project:**
- Cpk/PPM goal achieved and sustained for minimum 3 months post-implementation
- All documents updated (PFMEA, CP, WIs)
- Process ownership transferred to process owner
- Financial benefits validated by Finance (if business case required it)

---

### DMAIC vs. 8D — quick reference

| Dimension | 8D | DMAIC |
|-----------|-----|-------|
| Trigger | Customer complaint, single escape | Recurring problem, capability gap |
| Timeline | Days to weeks | Weeks to months |
| Root cause method | 5-Why, Fishbone | Hypothesis testing, statistical analysis |
| Output | Corrective action to prevent recurrence | Optimised process with sustained capability |
| Standards | ISO 9001 §10.2, IATF 16949 §10.2.3 | ISO 9001 §10.3, IATF 16949 §10.1 |

## Validation criteria

A DMAIC project is complete when:
- Baseline and improved Cpk/PPM both quantified with data
- Root causes confirmed statistically (not assumed)
- Solution validated in a pilot before full implementation
- PFMEA, Control Plan, and Work Instructions updated
- Improved Cpk sustained for minimum 3 months post-implementation
- Financial or quality benefit measured and reported

## Common mistakes

- Jumping to Improve before confirming root cause (the most common DMAIC failure)
- Not performing MSA before collecting baseline data — baseline may be measurement noise
- Selecting the solution in Define before data analysis — biases the entire project
- Closing the project at Implementation without monitoring for sustainability
- Not updating PFMEA and Control Plan — process reverts within months
- Using DMAIC for a single-event problem that needs 8D containment first

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
| 1.1 | 2026-06-06 | @migmcc | Added hypothesis test selection guide in Phase 3; added monitoring period closure criteria in Phase 5 (Cpk sustained on production data, not pilot) |
