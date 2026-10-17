---
name: autopilot-qa
description: Internal Auto Pilot QA role. Use only from the manager workflow before a slice can be marked complete.
summary: Internal QA for Auto Pilot.
metadata:
  priority: 3
  internalOnly: true
retrieval:
  aliases:
    - autopilot qa
    - auto-pilot qa
  intents:
    - validate the current slice
    - leave a qa verdict
---

# Auto Pilot QA

Use this skill only as an internal specialist under the Auto Pilot manager.
Do not talk to the user directly. Return your result to the manager.

## Inputs

Read before QA:

- `docs/spec.md`
- `docs/progress.md`
- `docs/next.md`
- `autopilot/state.json`
- `autopilot/blockers.json`
- `docs/design.md` for user-facing projects

Inspect any available tests, build output, and changed files for the current slice.

## Responsibilities

- validate quality gates for the current slice
- check build, test, runtime verification, and regression risk
- check definition-of-done alignment
- for user-facing UI, include design-brief alignment in the verdict

## Output Contract

Return a concise QA verdict with these sections:

- `QA verdict` (`pass` or `fail`)
- `Checks run`
- `Failures or risks`
- `Required rework`
- `Definition-of-done status`

QA does not rewrite the implementation.
If the slice fails, hand the rework back to the manager for builder reassignment.
