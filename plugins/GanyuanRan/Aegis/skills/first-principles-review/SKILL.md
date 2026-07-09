---
name: first-principles-review
description: Use when the user explicitly asks for first principles, first-principles review, Occam's razor, or when a complex decision has ambiguous goals, competing constraints, repeated fixes, fallback growth, duplicate owners, or architecture/product direction risk.
---

# First Principles Review

## Purpose

Use this as a lightweight decision review before another Aegis workflow makes a
directional choice. It is a compositional skill, not a standalone workflow.

Do not replace `brainstorming`, `systematic-debugging`, `writing-plans`,
`requesting-code-review`, or `verification-before-completion`. Use it to clean
the decision surface those skills will act on.

When this review materially changes the direction, surface `Aegis Visibility`
in natural prose: name the first principle, dropped assumption, smallest
sufficient path, or owner / retirement falsifier that changed the decision.
Keep it advisory and task-specific; do not turn the lens into approval
authority or a generic skill trace.

## Use When

- The user asks for first principles, first-principles thinking, or Occam's
  razor.
- A design, plan, or fix has multiple plausible paths and unclear selection
  criteria.
- The task has ambiguous goals, competing constraints, or product/architecture
  direction risk.
- Debugging is drifting into repeated fixes, fallback growth, duplicate owners,
  consumer-side patches, or "just add another branch" reasoning.
- A review finds that the implementation may be locally correct but directionally
  wrong.

## Do Not Use

- Simple Q&A, status checks, tiny wording/config edits, or clearly bounded
  single-owner changes.
- Mechanical execution of an approved plan unless a new directional conflict
  appears.
- As a required step for every task, every turn, or every TDD cycle.

## Five-Line Review

Answer only what is needed, usually in five short lines:

```text
First Principle: What irreducible outcome must this satisfy?
Non-negotiables: What constraints cannot be broken?
Assumptions to Drop: What is habit, inherited shape, or unproven preference?
Smallest Sufficient Path: What is the least complex path that satisfies the first principle?
Escalation Signal: What finding would require spec/design/architecture review?
```

For repair choices, "smallest" means smallest sufficient stable repair, not the
smallest textual diff:

```text
Minimality Check:
- Smallest textual diff:
- Correct owner:
- Bug class fixed:
- New branch/fallback added:
- Old path retired or scheduled:
- Verdict: sufficient repair | local patch | needs first-principles review
```

## Decision Hygiene Review

Use this escalation only when a design, fix, or plan needs endorsement before it
is written into a spec or implementation plan.

Escalate from the five-line review when any of these risk signals appear:

- multiple plausible paths and no clear selection criteria
- a new owner, duplicate owner, fallback, adapter, or compat-only carrier
- an old path that may need delete-first handling or a retirement trigger
- an unverified assumption that the proposal depends on
- user language such as "more elegant", "long-term stable", "first
  principles", or "Occam"
- a plan could encode the wrong owner, abstraction, compatibility boundary, or
  retirement schedule

Use this compact shape:

```text
First-principles invariants:
- Non-negotiable goal:
- Non-negotiable constraints:
- Historical assumptions to delete:

Owner / retirement matrix:
- New canonical owner:
- Old owner:
- Compat-only carrier:
- Delete-first / retirement trigger:

Falsification matrix:
- Dependency-removal test:
- Counterexample scenario:
- Must fail / degrade / remain correct cases:

Verdict:
- Adopt / revise / reject / needs evidence:
- Blocking gaps:
- Next evidence:
```

## Architecture Integrity Lens

Use this narrower lens when a proposal is executable but may still encode the
wrong owner, abstraction, contract boundary, or retirement path. It is advisory
method-pack output and may be embedded inside `Decision Hygiene Review` when
that is enough.

Trigger it when any of these appear before approach selection, task
decomposition, review, or completion-risk reporting:

- responsibilities may overlap or a canonical owner is unclear
- the smallest diff adds a caller-side fallback, guard, adapter, or compat-only
  carrier
- an existing source-of-truth or contract could solve the class of problem at a
  higher level
- a stale owner, fallback, or old path may keep carrying real logic
- the work makes a long-term stability, "cleaner architecture", or
  higher-level simplification claim

Use this compact shape:

```text
Architecture Integrity Lens:
- Invariant: What must remain true for the system to be coherent?
- Canonical owner / contract: Which owner, contract, or source-of-truth should carry the behavior?
- Responsibility overlap: What duplicate owner, caller-side patch, fallback, or stale path might still carry real logic?
- Higher-level simplification: Can the problem be solved at the owner / contract / source-of-truth layer instead of by another local branch?
- Retirement / falsifier: What old path retires, or what evidence would disprove this architecture judgment?
- Verdict: proceed | revise design | split owner | return to baseline | needs ADR/baseline sync
```

Do not run this lens for every low-risk task. If it does not change the
decision surface, return to the active workflow immediately.

## Composition

- With `brainstorming`: run before approach selection when the request is broad,
  ambiguous, likely to inherit a poor product shape, or involves owner /
  retirement / fallback / adapter risk. Use `Decision Hygiene Review` or the
  narrower `Architecture Integrity Lens` before recommending or selecting an
  approach when those signals appear.
- With `systematic-debugging`: run after evidence shows repeated fixes, fallback
  growth, duplicate owners, or consumer-side patching.
- With `writing-plans`: run before task decomposition when the plan could encode
  the wrong owner, abstraction, compatibility boundary, fallback, adapter, or
  retirement schedule. If the approved spec did not already cover this, use
  `Decision Hygiene Review` or the `Architecture Integrity Lens` before writing
  tasks.
- With `requesting-code-review`: run when review should check direction and
  owner integrity, not just code quality.
- With `verification-before-completion`: use only to name residual directional
  risk. It does not grant completion authority.

## Boundaries

- Prefer evidence from current project files, baseline docs, tests, logs, and
  user requirements. If evidence is missing, mark the line as unknown rather
  than inventing a principle.
- Keep the result advisory. This skill may recommend escalation, but it does
  not create authoritative `GateDecision`, `PolicySnapshot`, or completion
  authority.
- If the five-line review does not change the decision surface, return to the
  active workflow immediately.
