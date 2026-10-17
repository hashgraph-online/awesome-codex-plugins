---
name: chain-validation
type: reference
parent_skill: 5why-root-cause
author: RBraga01
version: "1.0"
status: approved
created: "2026-06-01"
last_updated: "2026-06-03"
updated_by: RBraga01
reviewed_by: RBraga01
license: MIT
---

# 5-Why Chain Validation Guide

Reference for building, validating, and rejecting 5-Why chains.
Use alongside the [5why-root-cause](../SKILL.md) skill.

> **Scope:** This guide focuses on **validation logic** — how to test whether a chain is correct.
> For the step-by-step execution workflow, see [5why-root-cause SKILL.md](../SKILL.md).

---

## Required Chain Validation Checklist

Use this checklist before accepting any 5-Why chain as complete.

- [ ] Each Why passes the "therefore" test (read backwards — logical at every step)
- [ ] Each step has objective evidence — no step marked "Validated: Yes" without supporting data
- [ ] No branching — one chain per cause path; separate chains for separate causes
- [ ] Chain ends in a systemic root cause (not "human error" or a symptom)
- [ ] Reversal check passes completely from end to beginning
- [ ] Root cause validated: reproducibility test + elimination test both attempted
- [ ] Separate escape chain completed (if used in 8D D4 context)
- [ ] Validated root cause feeds directly into a corrective action (8D D5 or CAPA)

---

## What Makes a Valid Why Chain

A valid 5-Why chain has three properties:

### 1. Logical continuity (the "therefore" test)

Every step must follow from the previous one. Test by reading backwards:

> "Because [Why N], therefore [Why N-1]."

If the sentence does not make logical sense, the chain is broken at that step.

**Example — valid chain:**

| # | Why | Therefore test |
|---|-----|---------------|
| 1 | Pins bent during insertion | — |
| 2 | Insertion force exceeded pin yield | Because force exceeded yield → pins bent ✓ |
| 3 | Operator used wrong tool | Because wrong tool → excess force ✓ |
| 4 | No instruction for tool substitution | Because no instruction → wrong tool used ✓ |
| 5 | Tool substitution not in FMEA | Because not in FMEA → no instruction written ✓ |

**Example — broken chain:**

| # | Why | Therefore test |
|---|-----|---------------|
| 1 | Part was out of spec | — |
| 2 | Supplier sent bad material | Because supplier sent bad material → part out of spec ✓ |
| 3 | Incoming inspection missed it | **Because incoming missed it → supplier sent bad material?** ✗ |

Step 3 is a separate why chain (why didn't we catch it?), not a continuation of steps 1–2.
This is where the **two root causes** pattern applies: occurrence and escape.

---

### 2. Evidence at every step

Each "Why" answer must be supported by:

| Acceptable evidence | Not acceptable |
|--------------------|----------------|
| Measurement data (force measurement, dimensional data) | "Probably" / "maybe" |
| Production records (machine logs, work order data) | "Someone said" |
| Direct observation (photographed condition, witnessed event) | Unverified assumptions |
| Physical samples (failed part, tool condition) | Team consensus without data |
| Documents (work instruction, calibration records, FMEA) | "It must have been" |

If evidence is unavailable, mark the step as "hypothesis — to be verified" and treat the chain
as unvalidated until evidence is obtained.

**No step may be marked "Validated: Yes" without objective evidence.** A chain with unconfirmed steps is a hypothesis chain — useful for investigation direction, but not acceptable for D4 closure or CAPA submission.

---

### 3. Systemic root cause at the end

A valid chain ends at a **systemic** root cause: something in the system that allowed the failure.

**Systemic root causes (accept these):**
- Missing or inadequate procedure / work instruction
- Gap in the FMEA (failure mode not identified)
- Training system failure (no qualification standard, no competence check)
- Absence of a poka-yoke where one should exist
- Process design gap (no step to prevent this failure mode)
- Measurement system inadequacy (gauge incapable, no MSA performed)
- Maintenance programme gap (no PM step for this failure mode)

**Non-systemic answers (reject these):**
- "Human error" — not systemic; ask why the error was possible
- "Operator carelessness" — not systemic; ask what in the system allowed carelessness
- "Supplier problem" — only half the chain; add why it was not caught
- "Machine failure" — only half the chain; add why it was not maintained/detected

---

## The Reversal Check (Mandatory)

After completing the chain, verify it by reading it forwards:

> "Because [Why 5], therefore [Why 4].
> Because [Why 4], therefore [Why 3].
> Because [Why 3], therefore [Why 2].
> Because [Why 2], therefore [Why 1] — which caused [the symptom]."

Every "therefore" transition must be logically sound. If any step fails the reversal check:
- Revise the why answer at that step
- Or split into two separate chains (one for occurrence, one for escape)

---

## Common Chain Failures

### Circular reasoning

The answer to a Why restates the previous Why in different words.

**Example:**
- Why are the parts out of spec? — Because they don't meet the specification.
- Why don't they meet the specification? — Because they are out of spec.

Fix: reframe the first Why as the physical mechanism that caused the non-conformance.

### Jumping to conclusion

The chain skips from symptom directly to root cause without establishing the path.

**Example:**
- Why was the defect not detected? — Because we don't have enough inspectors.

This may be true but skips: What detection method existed? Why did it fail to catch this?
What is the capability of the detection method? Fix: answer each step explicitly.

### Premature branching

Trying to put two separate cause paths into one chain.

**Example:**
- Why 3: "Either the gauge was wrong or the operator made an error"

Fix: run two separate 5-Why chains, one for each candidate cause. Validate each independently.

### Stopping at a symptom

The chain stops at something that is still a consequence of a deeper cause.

**Example:**
- Why was the wrong torque applied? — Because the torque wrench was set incorrectly.

This is still a symptom. Continue: Why was it set incorrectly? What in the system allowed it?

### Single-point-of-failure assumption

Assuming the chain has only one cause when multiple independent causes contributed.

Use [Fishbone](../../fishbone-analysis/) to map all candidate causes first, then run a
5-Why chain for each confirmed or probable cause.

---

## Output Format for a Validated Chain

A complete, documented 5-Why must include:

```
Problem statement: [measured, quantified — what, which part, how many]

Why Chain:
  Why 1: [answer] | Evidence: [source] | Validated: Yes/No
  Why 2: [answer] | Evidence: [source] | Validated: Yes/No
  Why 3: [answer] | Evidence: [source] | Validated: Yes/No
  Why 4: [answer] | Evidence: [source] | Validated: Yes/No
  Why 5: [answer] | Evidence: [source] | Validated: Yes/No

Root cause: [systemic statement]

Reversal check: "Because [Why 5], therefore [Why 4]. Because [Why 4]..." [result: passes/fails at step N]

Validation method: [reproducibility test result / elimination test result]
```

---

## Escape Chain (Root Cause of Non-Detection)

Always run a **separate** 5-Why chain for why the defect was not caught:

```
Why was the defect not detected before reaching [next process / customer]?

Why 1: [Which detection control existed and how it failed]
Why 2: [Why did the control fail?]
Why 3: [What in the system caused the control to be inadequate?]
...
Root cause of escape: [systemic detection system gap]
```

Both chains must be validated independently.
Both root causes must appear in D4 of the 8D report.
Both root causes must have corresponding PCAs in D5.

---

## From Validated Root Cause to Corrective Action

A validated root cause is only useful if it drives an action. The chain is not complete until the corrective action direction is defined.

| Root cause type | Corrective action direction |
|-----------------|----------------------------|
| Missing procedure / work instruction | Write or update the procedure to close the gap |
| FMEA gap (failure mode not identified) | Update PFMEA: add failure mode, assign AP, define prevention/detection control |
| Training system failure | Define competence standard; add OJT verification; update competence matrix |
| Absent poka-yoke | Design and implement an error-proofing device for this failure mode |
| Process design gap | Revise process to add the missing prevention step |
| Measurement system inadequacy | Upgrade gauge; perform MSA; add calibration step |

**Validated root causes feed directly into:**
- **8D D5** — Permanent Corrective Actions (one PCA per root cause)
- **CAPA** — Corrective Action Request linked to this chain
- **PFMEA update** — new or revised failure mode entry with updated O/D ratings
