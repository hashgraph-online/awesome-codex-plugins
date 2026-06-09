---
name: orgx-runtime-reporting
description: Use when a Codex execution should report progress, artifacts, blockers, or completion state back to OrgX during a live task.
---

# OrgX Runtime Reporting

Use this skill when Codex should keep OrgX updated during execution.

## Reporting contract

There are two reporting paths:

- **Active path:** call OrgX MCP tools during the work when you know the
  initiative, task, decision, blocker, or artifact context.
- **Chronicle readout:** for operator reporting, call
  `get_operator_chronicle` first when available and present
  `reportingNarrative.briefMarkdown` before drilling into individual entities.
- **Stale-client fallback:** if bootstrap or docs advertise
  `get_operator_chronicle` but the current AI client session has not refreshed
  its callable tool list, immediately call `orgx_recommend` or
  `_orgx_recommend` with `mode: "morning_brief"` and present the returned
  `reportingNarrative.briefMarkdown`. Do not ask the user to reconnect before
  giving the report.
- **Passive backstop:** Codex runtime hooks installed by `orgx-wizard hooks
  install` record compact session events and run summary-only local Work Graph
  reconciliation on `Stop`.

Do not treat hook presence as a substitute for intentional OrgX writes. Hooks
answer whether OrgX was used and can write a local report automatically; MCP
calls, or an explicitly opted-in successful Work Graph post, make the work
durable in OrgX while the session is still fresh.

## Workflow

1. Resolve available IDs from args, env, or the current OrgX context:
- `ORGX_INITIATIVE_ID`
- `ORGX_WORKSTREAM_ID`
- `ORGX_TASK_ID`
- `ORGX_RUN_ID`
- `ORGX_CORRELATION_ID`

2. For reporting questions, retrieve the operator chronicle:
- Use `get_operator_chronicle` with `period: "30d"` for broad clarity when it
  is callable in the current client.
- Use `period: "day"` or `period: "week"` when the user asks for yesterday or
  this week.
- If `get_operator_chronicle` is not callable in the current client, use the
  existing `orgx_recommend` / `_orgx_recommend` fallback with
  `mode: "morning_brief"` and the broadest supported period. Treat the direct
  tool as preferred, but do not block on client schema refresh.
- Lead with `reportingNarrative.briefMarkdown`, then call out gaps and the
  next action.

3. Emit activity at meaningful milestones:
- `intent`
- `execution`
- `handoff`
- `blocked`
- `completed`

4. Register proof of work:
- When you produce a file, diff, document, screenshot, or report, register it as an artifact with a concrete summary.

5. Handle blockers structurally:
- If judgment is required, request a decision with explicit options.
- If context is missing, report the exact missing dependency.

6. Close execution cleanly:
- When the task is complete and verified, emit completion activity and update entity state if the task ID is available.

7. If no OrgX IDs are available:
- Continue the work, but make the final response easy for the hook reconciler to
  classify: name decisions, artifacts, blockers, next actions, and verification.
- Do not claim OrgX was updated unless an MCP tool or API call actually
  succeeded.

8. Preserve Work Graph continuity:
- When a Work Graph report is generated, include its `work_graph_fingerprint`
  and `signup_hydration.hydration_key` in summaries or artifacts that are safe
  to store.
- Automatic Stop-hook reconciliation writes the latest local report to
  `~/.config/useorgx/wizard/hooks/reports/latest-work-graph-report.json`.
- Stop-hook posting requires `ORGX_HOOK_RECONCILE_POST=true` or
  `ORGX_WIZARD_HOOK_RECONCILE_POST=true` plus `ORGX_API_KEY`.
- Treat the fingerprint as the durable claim key that lets OrgX hydrate
  pre-signup audit value into a user's future workspace.
- Never derive the fingerprint from secrets or raw transcripts that would need
  to leave the local machine.

## Quality bar

- Never post empty status updates.
- Messages must be evidence-based and specific.
- Include OrgX IDs whenever available.
- Use `source_client=codex`.
- Preserve secrets: never emit tokens, cookies, API keys, or storage state into
  activity, retro, hook summaries, or final reports.
