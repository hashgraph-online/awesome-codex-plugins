---
name: design
description: Use for standard or complex new work before coding or planning. Also handles vague goals — clarifies before designing.
---
# Design

`<gate>` No code until user approves the spec. `</gate>`

## Before designing

Goal too vague to name what to build, for whom, or what success looks like? Ask one question per turn until it's concrete. Don't propose solutions until then. Working notes can hold hypotheses, experiments, ruled-out directions (spike code → temporary worktree).

Clarify in dependency order. Resolve facts from the repo/tools; ask only the current decision frontier requiring user judgment. Don't ask downstream questions before prerequisite decisions or map the full dependency tree. Stop when implementation-affecting contract, data, failure, and test decisions are decided or deferred.

Goal clear? Propose 2-3 approaches with trade-offs; recommend one. Then write the spec.

## Multi-module changes

If `topology=multi-module` (triage announcement or coordinator spec/plan declaration), read `../references/multi-module.md` before designing. Create the coordinator spec with the declaration block (`topology: multi-module`, `change-set`, `coordinator`, `repos`) - this declaration is the on-disk mode marker downstream skills rely on.

- Identify workspace modules and Git boundaries separately.
- For multiple repositories, ask the user to designate one existing repository as coordinator. This is an implementation-affecting decision; do not infer it.
- Put only shared contracts and integration acceptance needed by this change in the coordinator spec.
- Put module-local decisions and acceptance in a spec inside each module's owning repository. Reference shared contracts; never duplicate them.
- Assign one stable change-set ID (in the declaration block) and declare every participating repository path relative to the coordinator.
- A missing repository or unresolved shared contract blocks handoff.

## Spec = list of decisions

A spec answers the open questions for THIS change. Typical:
- contract / interface?
- data shape?
- failure modes?
- out of scope?
- what test proves it?
- architecture?
- convention?

Do spec idiomatically. Record `convention` — stack best practices + project conventions for this change (see `../references/quality.md`); `tdd`/`review` verify against it.

**No question → no section.** Don't fill "Risks" / "Non-goals" if empty.

Use declarations, not narrative:
```
contract:  <interface>
invariant: <what must hold>
test:      <how we'll know>
convention: <stack best practices + project conventions — see ../references/quality.md>
deferred:  <not deciding now>
```

Reference code by path; never paste it.

Before handoff, close only decisions that affect implementation: contract, data, failure, test. Unresolved `Working notes` in those areas become decisions, `deferred`, or questions.

## Two layers, one file: `docs/staging/specs/YYYY-MM-DD-<topic>.md`
- Top: decisions, contracts, invariants (permanent).
- `## Working notes`: scratch, open questions, hypotheses, ruled-out directions (stripped at `ship`).

## Roadmap

**`docs/ROADMAP.md` already exists?**
- Does this work add new milestones? Append them to `docs/ROADMAP.md`.
- Otherwise, no roadmap action needed.

**`docs/ROADMAP.md` does not exist?**
- This work spans ≥ 3 milestones → create `docs/ROADMAP.md`:
  ```markdown
  - [ ] M1: <one-line goal>
  - [ ] M2: <one-line goal>
  - [ ] M3: <one-line goal>
  ```
- Otherwise → no roadmap needed. Describe full scope in spec.

Stubs are intent, not commitment; update before expanding.

If roadmap exists or was created, reference the current milestone in staging spec:
```
milestone: M1 (see docs/ROADMAP.md)
```

## Spec review gate

After spec is written to disk and before handing off to `plan`, inspect the spec to decide how many reviewers to dispatch. Read `../references/reviewers.md` for the trigger table and reviewer charters.

Count the triggers that match the spec. If only trigger 1 fires (the baseline), dispatch a single `spec-compliance` reviewer — this is the default behavior, same cost as today. If multiple triggers fire, dispatch each reviewer as an independent subagent in parallel.

All reviewers receive the spec path (not the spec content — let them read it). Collect findings, then synthesize: evaluate each finding critically, resolve conflicts between reviewers, spot what was missed, judge severity, and patch the spec once. Present to user: what was found, fixed, deferred — and why.

Report to user: which triggers fired, which reviewers ran, what was found and fixed.

## Abandon

If the user decides not to proceed after clarification, stop here. No spec, no plan, no ship. Record reason briefly in working notes. If exploration produced a knowledge artifact (protocol spec, RE findings, data structure map), save it to `docs/decisions/` via `archive`.

## Gates
`<gate>`

1. `docs/staging/specs/YYYY-MM-DD-<topic>.md` must exist on disk before handing off to `plan`. For multi-module work, the coordinator spec and every affected module spec must exist in their owning repositories.
2. Confirm with the user.

`</gate>`
