---
name: backlog-add
description: Enqueue a plan to backlog without activating it. Includes Broad Intake review, product-context reasoning, and conflict triage. Invoke via /backlog-add; do not auto-load.
version: 0.1.0
category: core
disable-model-invocation: true
---

# /backlog-add

Enqueue a plan to backlog without activating it, after Broad Intake review and conflict triage.

## When to use

- Queue a plan for later work without making it the active plan
- Add a plan when the active plan should remain active
- Enqueue multiple plans in sequence
- Write residuals plans from `/plan-review-triage`

Do **not** use this for activating a plan (use `/start-project` with Gate B) or starting execution immediately (use `/continue-plan` or `/run-plan` after activation).

## Procedure

Full Broad Intake bucket table, triage labels, product-context reasoning, Task(explore) delegation fields, and post-write inbox Ask: [procedure.md](./procedure.md)

Command SoT: [backlog-add.md](https://github.com/agent-kit-startup/agent-kit/blob/main/.cursor/commands/backlog-add.md)

HITL labels: [hitl-gates](https://github.com/agent-kit-startup/agent-kit/blob/main/skills/hitl-gates/SKILL.md)
