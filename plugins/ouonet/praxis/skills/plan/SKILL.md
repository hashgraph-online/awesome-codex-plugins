---
name: plan
description: Use after design approval for milestone plans with executable acceptance.
---
# Plan

`docs/staging/plans/YYYY-MM-DD-<topic>.md`. Reference the spec; don't restate it.

If unresolved spec notes affect implementation or task order, return to `design`.

## Rolling wave

Spec references a milestone (`milestone: MN`)? Check `docs/ROADMAP.md` — expand only that milestone. Leave the rest as stubs.

After `ship`: open `docs/ROADMAP.md`, confirm which milestone is next, then expand it. Return to `design` only if the milestone's goal materially changed.

## Milestone tasks (30-60 min each)

Every task is `- [ ] T<n>: <name>` - always a checkbox, never a heading. `tdd`/`subagents` flip it to `- [x]` on completion; `ship` refuses to run while any `- [ ]` remains.

```
goal:       <one sentence>
files:      <paths>
acceptance: <test or cmd>
spec:       <docs/staging/specs/...#anchor>
```

No exact code. No step-by-step. Acceptance is verifiable: a test, command, or scripted check — or, when none is possible, an explicit manual check (steps + expected result). Each task leaves the repo green.

Mark independent tasks: `[parallel] T3, T4, T5`.

Only mark `[parallel]` when shared contracts, state, errors, and acceptance are closed.

**Atomic expansion is deferred until dispatch time** - `subagents` expands a milestone into 2-5 min steps at dispatch time, not here.

for **New project**: derive an initialization task — scaffold code, tests, CI, and always include: `README.md`, `CHANGELOG.md`, `.gitignore`, and a `Makefile` (or equivalent task runner config).

## Don't put in the plan

background, architecture, rationale (spec), CI commands, copy-pasted acceptance.

## Hand off

`<gate>` `docs/staging/plans/YYYY-MM-DD-<topic>.md` must exist on disk before handing off to `tdd`/`subagents`.`</gate>`

Confirm plan with the user.

mostly `[parallel]` -> `subagents`. Otherwise -> `tdd`.
