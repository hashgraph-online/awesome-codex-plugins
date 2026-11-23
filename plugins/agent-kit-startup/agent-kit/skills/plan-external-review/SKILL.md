---
name: plan-external-review
description: Arm external Claude reviewer for plan audits with autonomous background PTY spawn and freshness-gated wait. Invoke via /plan-external-review; do not auto-load.
version: 0.1.0
category: core
disable-model-invocation: true
---

# /plan-external-review

Arm an external Claude Code reviewer to audit a completed plan and produce a findings monitor.

## When to use

- After a plan completes and before merging to production
- When autonomous plan audit is enabled (`mode: "autonomous"`)
- In `/run-plan` exhaustion hook or `/run-plan-all` queue-end
- For batch review of multiple plans in one session

Do **not** use this for inline plan editing, triage of existing monitors (use `/plan-review-triage`), or CI-only headless runs without freshness-gated wait.

## Procedure

Manual arm detail, script commands, autonomous vs paste-only modes, background PTY spawn, freshness-gated wait, soft-fail contract, and reviewer cascade: [procedure.md](./procedure.md)

Command SoT: [plan-external-review.md](https://github.com/agent-kit-startup/agent-kit/blob/main/.cursor/commands/plan-external-review.md)

HITL: paste-only fallback when background spawn is unavailable; wait-monitoring budget enforcement; exit 3 is timeout-only, never review done.

## Exit codes

- `0` = fresh monitor ready
- `3` = timeout (slice or total; not review done)
- `4` = soft-fail while waiting (missing `claude`, silent PTY, session-cap refuse)
