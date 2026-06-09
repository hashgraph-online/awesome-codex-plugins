---
name: Slice
kind: primitive
status: tracer
see-also: [primitive, tracer-bullet, anti-pattern]
---
# Slice

A vertical work unit that cuts through multiple Primitives end-to-end.

## Definition

A Slice is a unit of change defined by the Primitives it crosses, not by the
files it modifies. A Slice has:

- a **goal** stated in one sentence
- a **Primitive set** it must traverse (skill + hook + CLI + eval + doc, or
  any subset, listed explicitly)
- a **decision gate** at the end: ship, defer to bd, or mark dead
- a single durable **artifact** (the diff, the audit doc, the council report)

A Slice is the unit of progress. A PR is one shape of Slice. A
tech-debt-audit pass over one feature is another shape. A bug fix that
touches only one Primitive is **not** a Slice — it is a patch.

## When to use

- When the scope of work crosses more than one Primitive. Bundle them into
  one Slice rather than threading state across many small PRs.
- When the question is "is this done?" — a Slice is done when its decision
  gate has fired and the artifact is committed.

## Anti-pattern

- **Horizontal slicing.** Editing 50 files but staying entirely within one
  Primitive layer (e.g. "rename all variables across all skills"). This is
  refactoring, not a Slice; it accumulates churn without proving any
  end-to-end behavior.
- **Slice without decision gate.** Work that crosses Primitives but ends in
  "we'll keep going" — the next session inherits ambiguous state. Every
  Slice must end with a yes/no, even if the answer is "defer."
- **Slice without artifact.** A session that touched code but produced no
  reviewable artifact (no diff, no audit doc, no committed plan). The Slice
  did not happen.

## Example in this codebase

- The CI eval-drift fix that landed this session is a Slice: it crossed
  evals (the suites), CLI (`ao eval run` was used to verify), CI workflow
  (artifact upload added), and docs (commit message), with a clear ship
  decision and a commit pair as artifact.
- The proposed tech-debt audit is a sequence of Slices, one per repo
  feature.

## See also

- `primitive.md` — the atomic units a Slice crosses
- `tracer-bullet.md` — the thinnest possible Slice (the test entry)
- `anti-pattern.md` — what horizontal slicing and gateless slicing cost
