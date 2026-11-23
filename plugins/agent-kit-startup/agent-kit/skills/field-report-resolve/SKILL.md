---
name: field-report-resolve
description: Resolve Field Report attention cards by checking eligibility and dismissing when answered or subject-resolved. Invoke via /field-report-resolve; do not auto-load.
version: 0.1.0
category: core
disable-model-invocation: true
---

# /field-report-resolve

Resolve Field Report attention cards by verifying eligibility and dismissing when the subject is answered or resolved.

## When to use

- Clearing attention cards after the underlying issue is resolved
- Validating that pending questions have been answered
- Checking that untriaged monitors have been triaged
- Resetting cadence windows after review is complete
- Recording an operator verdict for an owed plan that has nothing to review (delivered nothing, superseded)

Do **not** use this for creating Field Report cards, triaging monitors (use `/plan-review-triage`), or analyzing unprocessed dogfood.

## Procedure

Per-id-shape locate/check/dismiss-eligibility detail for `attention:prompt:<chatId>`, `attention:report:<slug>`, and `attention:cadence:<windowId>`: [procedure.md](./procedure.md)

Command SoT: [field-report-resolve.md](https://github.com/agent-kit-startup/agent-kit/blob/main/.cursor/commands/field-report-resolve.md)

HITL: Task(explore) delegation for transcript/monitor/plan scans; hide-after-check confirmation when dismissing before resolution is complete. On a cadence id, the per-plan verdict Ask (`plan-verdict`: `Delivered nothing` / `Superseded` / `Keep owed`) comes before the window decision.
