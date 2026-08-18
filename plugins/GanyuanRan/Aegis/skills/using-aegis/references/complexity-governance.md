# Aegis Complexity Governance Reference

Use this reference when a skill needs the shared interpretation for complexity
budgeting, pressure signals, closure, or major-complexity follow-up without
repeating the full explanation in every skill body.

## Purpose

This reference keeps the Aegis hot and semi-hot skills compact while preserving
one shared interpretation of complexity governance across planning,
implementation, and completion.

## Artifact Classes

At minimum, treat complexity as applying to maintained artifacts, not only
production code:

- `Source Complexity`: production and library source owners
- `Test Complexity`: maintained test source owners, helpers, harnesses, routers,
  and assertion/build orchestration
- `Decision / Plan Complexity`: spec, brief, plan, baseline, and ADR artifacts
  whose structure affects implementation quality
- `Process Artifact Complexity`: checkpoints, evidence, reflections, and other
  durable work records whose sprawl affects continuity, reviewability, or
  handoff quality

Do not treat a maintained test source file as a cheap `tests-only` exception.

## Compact Budget Shape

```text
Complexity Budget:
- Artifact class:
- Target files / artifacts:
- Current pressure:
- Projected post-change pressure:
- Budget result: within-budget | at-risk | over-budget
- Planned governance:
```

## Shared Pressure Signals

Typical pressure signals:

- 800+ line maintained source or maintained test file as a soft pressure
  signal, not an automatic edit ban
- 1200+ line maintained artifact, or a touched artifact in the largest
  5-10% of the target project, as a strong pressure signal
- touched cohesive block over roughly 80 lines
- deep nesting or mixed reasons to change
- generic owner receiving another responsibility
- fallback / adapter / guard / compatibility branch growth
- owner mismatch or duplicate-owner risk
- plan / process artifact fan-out that harms execution clarity
- multi-owner sprawl, duplicated decision text, unreadable work-log structure,
  or handoff-hostile artifact layout

A new file is not automatically better. Prefer a new file only when owner,
contract, call path, and retirement story are clearer than add-in-place growth.

## Phase Rules

Planning / pre-edit:

- If projected result is `over-budget`, do not silently continue with
  add-in-place growth.
- Revise the boundary, add governance work, split the task, or explicitly mark
  the slice as requiring follow-up.
- If the target edit file is over-budget or mixed-purpose, classify edit intent
  before non-trivial source edits:
  `wiring-only`, `move-out / extract-first`,
  `local-fix-without-new-responsibility`, `new-responsibility`, or
  `emergency / compatibility patch`.
- `new-responsibility` must not be added in place to an over-budget or
  mixed-purpose owner by default. Reuse or extract the correct owner, split the
  task, or pause for plan review.
- `move-out / extract-first` is allowed when the overloaded owner gets thinner
  or clearer. `wiring-only` and local fixes are allowed when they do not add a
  responsibility.

Completion:

```text
Complexity Closure:
- Budget status: within-budget | exceeded-and-governed | exceeded-unresolved
- Governed now:
- Deferred follow-up:
- Completion impact: complete | needs-follow-up | not-complete
```

- If `Complexity Closure` is `exceeded-unresolved`, Aegis must not claim the
  task is complete.
- If completion-time complexity is over budget, classify the repair decision as
  `govern-now`, `follow-up-required`, or `not-complete`. `govern-now` may
  continue only inside the current authorized slice with a clear verification
  boundary; otherwise report follow-up or downgrade completion.

## Major Complexity Follow-up

When the current slice encounters a materially oversized maintained artifact
that it cannot fully govern, emit:

```text
Major Complexity Alert:
- Artifact:
- Why it is materially oversized:
- Why this slice cannot fully govern it:
- Recommended follow-up:
```

Use this to keep the user aware that a separate complexity-governance slice may
be needed.
