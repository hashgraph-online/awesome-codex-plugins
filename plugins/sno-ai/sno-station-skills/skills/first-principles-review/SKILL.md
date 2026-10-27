---
name: first-principles-review
description: "MANUAL-ONLY: challenge a product idea, design, PRD, or architecture from first principles. Use only when the user names this skill. Research first, then write a local review and PRD handoff."
requires:
  programs: []
  harness:
    - {slot: 4.shell, need: required}
    - {slot: 4.file-read-write, need: required}
---

# First-Principles Reviewer

Run before a proposal hardens into requirements or source code. The owner is whoever owns the
work and decides what it should be; often that is the user. A PRD is a product requirements
document. Judge the problem framing,
constraints, and solution shape. Source code is evidence about the incumbent, not the main
review target; route source-defect review to `peer-review`.

## Invocation Gate

Proceed only when the human explicitly invokes this skill (`$first-principles-review` or
`/first-principles-review`) or names it in the current request. Do not infer invocation from the presence of a PRD or design.

## Workflow

1. **Freeze the boundary.** Identify the input, record its hash when it is a file, choose a
   local report path, and do not modify the reviewed input. Use
   `reports/<input-stem>-first-principles-review.md` unless the human names another path.
   Use a distinct report filename when the default already exists. If a named input is
   missing or unreadable, locate the canonical artifact, repair access within authority,
   and continue the review. Work on independent evidence meanwhile; ask only for an
   input that only the owner can supply. Never invent the missing artifact or claim
   a completed review without reading it.
2. **Research before challenging.** Read the relevant product intent, prior decisions,
   incumbent behavior, immediate code/design dependencies, and current external solutions.
   Record every source and every material gap. When current external facts matter, browse.
   Stop when another source cannot change a premise state, the disposition, or the next
   evidence-producing action. Record that stopping boundary.
3. **Re-derive the outcome.** State what the user or system must achieve without borrowing
   the proposed implementation.
4. **Classify constraints.** Mark each claim as `hard constraint`, `owner preference`, or
   `inherited assumption`. Cite evidence. A physical, legal, published-contract, measured
   economic, or explicit owner limit may be hard; familiarity is not.
5. **Challenge premises.** Build a ledger of load-bearing premises. Mark each
   `evidence-backed`, `unproven`, `inherited`, or `falsified`. Apply removal, inversion,
   substitution, do-nothing, and incumbent comparison where they can change the decision.
   A settled owner decision stays settled unless a specific new fact changes its basis. Name
   that fact before challenging the ruling; never relabel the ruling as inherited.
6. **Construct real alternatives.** Consider eliminating the need, reusing an incumbent or
   native capability, making the smallest viable change, and redesigning from true
   constraints. Include only materially distinct candidates. Do not force novelty or a
   candidate count.
7. **Choose a disposition.** Use exactly one: `PROCEED`, `REFRAME`, `SIMPLIFY`, `REPLACE`,
   `SPLIT`, `TEST-FIRST`, or `STOP`. For `SPLIT`, record at least two independently
   buildable outcomes inside the single handoff object. `PROCEED` means evidence is strong
   enough to enter PRD authoring, not to skip implementation or production verification.
   Use `TEST-FIRST` only when a missing fact could change the problem framing or selected
   direction before PRD authoring. Repeated benchmarks and rollout checks belong in acceptance
   implications or falsifiers and do not by themselves block `PROCEED`.
8. **Recommend one direction.** Compare the current proposal and surviving alternatives on
   outcome fit, complexity, failure surface, reversibility, time to evidence, and migration
   cost. Name observable evidence that would overturn the recommendation.
9. **Write and validate the report.** Follow `references/report-contract.md`, including its
   embedded JSON handoff. Run:

   ```bash
   python3 <skill-dir>/scripts/validate-report.py <report.md>
   python3 <skill-dir>/scripts/extract-prd-handoff.py <report.md> > <handoff.json>
   ```

   `<skill-dir>` is the folder that contains this SKILL.md. Both scripts need `python3`.

10. **Ask only after the report exists.** Keep questions out of the report. If a genuine
    owner decision survives research, ask one decision at a time in chat. Otherwise hand the
    report and extracted block to whoever writes the PRD (a PRD-writing skill, if one is installed).

## Judgment Rules

- By default this review is one pass (a project may choose otherwise): do not rerun it to confirm
  edits, and do not turn its output into a new review target. Whoever acts on the report records
  how each recommendation was handled, proves fixes deterministically, and continues.
- The report is the record of the review. Do not prewrite or self-author a `PROCEED` result
  before this workflow has inspected the evidence.
- Verified fact, inference, and unknown are different claims. Label them separately.
- A recommendation without falsifiers is advocacy, not review.
- No research or no challenged premise is an instrument failure, not a clean result.
- `PROCEED` means the proposal survived meaningful challenge; it does not mean exhaustive
  proof or production readiness.
- Preserve rejected alternatives and why they lost so the PRD author does not re-derive them.
- When existing source is supplied, use it to establish incumbent behavior, constraints, and
  coupling. Route source defects to `peer-review`.
- The report is bounded and non-exhaustive. Say so explicitly.

## Output

Create one independent local Markdown report. Report the exact path. Do not edit a target PRD
or automatically invoke a PRD skill. The embedded handoff is the downstream contract; prose
remains the human record.
