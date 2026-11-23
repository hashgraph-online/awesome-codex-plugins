---
name: plan-review-triage
description: Triage plan monitor findings. Select untriaged targets, summarize open residuals, and persist durable triage headings. Invoke via /plan-review-triage; do not auto-load.
version: 0.1.0
category: core
disable-model-invocation: true
---

# /plan-review-triage

Triage plan monitor findings by selecting untriaged targets, summarizing open residuals, and persisting durable triage headings.

## When to use

- After a plan monitor is written by `/plan-external-review`
- When Field Report shows untriaged monitors
- At the end of a `/run-plan-all` queue
- For batch triage of multiple monitors with uniform outcome

Do **not** use this for creating monitors (use `/plan-external-review`), plan execution (use `/continue-plan` or `/run-plan`), or dogfood inbox analysis.

## Procedure

Full Steps 1-6 walk, selection order (git-fresh/HANDOFF-aligned/untriaged scan), closeout depth, termination gate, uniform batch HITL, paced Task dispatch for multi-plan Write residuals, and example flows: [procedure.md](./procedure.md)

Command SoT: [plan-review-triage.md](https://github.com/agent-kit-startup/agent-kit/blob/main/.cursor/commands/plan-review-triage.md)

HITL labels: [hitl-gates](https://github.com/agent-kit-startup/agent-kit/blob/main/skills/hitl-gates/SKILL.md)

## Selection order (bare command)

1. Git-fresh untriaged monitors (`git status` staged/untracked without triage heading)
2. HANDOFF-aligned (Run queue / Gaps monitors still untriaged)
3. All untriaged scan (prefer open gaps; include clean files for Ack-and-stop)
4. Hard stop if every candidate is already triaged

Never select solely by mtime.
