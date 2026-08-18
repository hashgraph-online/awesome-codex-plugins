---
name: 5why-root-cause
description: >-
  Drill into root cause with a 5-Why why chain, why analysis, or structured root cause
  investigation. Builds a Why chain from symptom to systemic root cause, validates each
  step with evidence, and detects circular reasoning. Use for 8D D4, CAPA, FMEA cause
  analysis, or any quality investigation requiring confirmed root cause identification.
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
  standard_edition: "ISO 9001:2015"
---

# 5-Why Root Cause Analysis

## Goal

Identify and validate a systemic root cause through a structured, evidence-based Why chain that can be directly linked to a corrective action.

## Required Execution Checklist

- [ ] Problem defined with measurable data (value vs. specification)
- [ ] Linear Why chain built — one cause path at a time, no branching
- [ ] Each Why supported by objective evidence (not opinion or "probably")
- [ ] Logical consistency verified — reversal check passed
- [ ] Systemic root cause identified (not "human error" or symptom)
- [ ] Root cause validated: reproducibility test + elimination test
- [ ] Output enables definition of corrective action (PCA or CAPA)

---

## When to use

Use 5-Why for any quality problem with a single, linear cause chain. Works best for process failures, equipment failures, and procedural non-compliances. For complex problems with multiple contributing causes, use [Fishbone](../fishbone-analysis/) first to identify candidate root causes, then use 5-Why to drill into each.

If multiple potential cause paths exist — do not combine them into one chain. **Run separate 5-Why chains for each path** and determine which is confirmed by evidence.

## Prerequisites

- Problem is clearly defined (use [Is/Is-Not](../is-is-not-scoping/) to scope if needed)
- The investigation team has access to the process, machine, or system where the defect occurred
- Physical evidence or production records are available

## Use within 8D — Occurrence and Escape

When used for 8D D4, two separate Why chains are required:

| Chain | Starting question | What it finds |
|-------|------------------|---------------|
| **Occurrence chain** | "Why did the defect happen?" | Root Cause of Occurrence (RCO) — the process or design failure that created the defect |
| **Escape chain** | "Why was the defect not detected before reaching the customer?" | Root Cause of Escape (RCE) — the detection system failure |

**Run each chain independently.** Do not mix occurrence and escape causes in the same chain — they have different corrective actions. The occurrence chain addresses prevention; the escape chain addresses detection.

---

## Workflow

### Step 1 — State the symptom precisely

Start with a factual, measurable problem statement. Not "the part was bad" but "dimension X measured 23.5mm; specification is 25.0 ± 0.5mm on part number Y, batch 2026-05-12."

The first Why answers: **"Why did [specific symptom] occur?"**

---

### Step 2 — Build the Why chain

For each Why, follow these rules:

**Rule 1: Each answer must be supported by evidence**
- Acceptable evidence: measurement data, production records, machine logs, direct observation, physical samples
- Not acceptable: "probably," "maybe," "someone said"

**Rule 2: Each answer must logically lead to the next Why**
- Test reversibility: "Because [Why N], therefore [Why N+1]"
- If the sentence doesn't make logical sense, the chain is broken

**Rule 3: Keep the chain focused**
- One Why chain = one cause path
- If you reach a fork (two possible causes), investigate both separately

**Rule 4: Stop at a systemic root cause**
- You have reached root cause when: fixing it would prevent the defect from ever recurring
- Typical systemic root causes: missing procedure, inadequate training system, process design gap, absence of poka-yoke, measurement system failure

---

### Step 3 — Validate the chain

Work backwards through the completed chain:

"Because [Why 5], therefore [Why 4]. Because [Why 4], therefore [Why 3]..."

If any step does not logically follow, revise that step.

---

### Step 4 — Validate the root cause

The root cause is correct if:
- **Reproducibility test:** can you deliberately create the defect by triggering the root cause? Yes → validated
- **Elimination test:** if you fix the root cause, does the defect disappear? (trial run or logical test)

**If neither test is possible, the root cause is not confirmed — it is a hypothesis.** Do not close the investigation on a hypothesis. Either obtain evidence to confirm it, or investigate alternative cause paths.

---

## Example

**Problem:** Connector pin bent at incoming inspection, 12/200 parts (6%).

| # | Why | Evidence | Validated? |
|---|-----|----------|------------|
| 1 | Why are pins bent? | Pins deformed during insertion into housing | Microscopy confirmed deformation pattern |
| 2 | Why during insertion? | Insertion force exceeded pin yield strength | Force measurement: 48N, pin rated to 35N |
| 3 | Why was force 48N? | Operator used incorrect insertion tool (hand press vs. pneumatic jig) | Tool log: jig under maintenance since 05-10 |
| 4 | Why was incorrect tool used? | No instruction specifying which tool to use when jig is unavailable | Work instruction reviewed — no contingency |
| 5 | Why no contingency? | Tool maintenance downtime not considered in work instruction design | Process FMEA missing this scenario |

**Root cause:** Work instruction design does not cover tool substitution contingency; FMEA does not identify tool maintenance as a failure scenario.

**Reversal check:** "Because FMEA doesn't cover tool maintenance → therefore no contingency instruction → therefore wrong tool used → therefore excess force → therefore pins bent." ✓ Logical.

---

## Common mistakes — reject these

**"Human error"** as a final answer
→ Ask: why was the error possible? What in the system allowed it?

**"Operator didn't follow the procedure"**
→ Ask: why didn't they follow it? Was it unclear? Not trained? Impossible to follow?

**"Machine was out of calibration"**
→ Ask: why? What is the calibration interval? Was it missed? Why?

**Circular reasoning**
→ "The part was defective because it didn't meet spec, because it was defective." → reframe the first Why as the physical mechanism.

**Stopping at a symptom, not a cause**
→ "The defect occurred because the part was wrong" — that IS the defect, not a cause.

**Branching the chain prematurely**
→ Each Why step should have one answer. If you have two, run two separate 5-Why chains.

## Output content

A validated 5-Why must include:
1. Problem statement (measured, quantified)
2. Each Why with: the answer, the supporting evidence, and validated (Yes/No)
3. Root cause statement
4. Reversal check (one sentence confirming logical flow)
5. Validation method (how the root cause was confirmed)
6. **Corrective action direction** — what type of action addresses this root cause (used as direct input to 8D D5 or CAPA)

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

- [Chain validation guide](references/chain-validation.md)

## Changelog

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-01 | @RBraga01 | Initial release |
| 1.1 | 2026-06-03 | @RBraga01 | Added dual-chain requirement (occurrence + escape), evidence status tracking |
