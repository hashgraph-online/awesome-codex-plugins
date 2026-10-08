---
name: orgx-initiative-ops
description: Use when Codex is working on a repo or task that is scoped to an OrgX initiative, workstream, milestone, task, blocker, or decision and needs to use OrgX MCP as the source of truth.
---

# OrgX Initiative Ops

Use this skill when the task is tied to OrgX execution state rather than just local code.

## Workflow

1. Orient before editing:
- Call the OrgX workspace or initiative summary tools first.
- For broad status/reporting questions, prefer `get_operator_chronicle` first
  when available; it is the canonical decision, artifact, PR, goal, gap, and
  priority readout.
- If the hosted OrgX MCP bootstrap advertises `get_operator_chronicle` but the
  active AI client session has a stale callable tool list, immediately use
  `orgx_recommend` or `_orgx_recommend` with `mode: "morning_brief"` and report
  the returned `reportingNarrative.briefMarkdown`. Do not wait for the client to
  reconnect before answering the operator.
- If an initiative, workstream, task, blocker, or decision is named, treat OrgX as the source of truth for current status.

2. Reuse existing context before creating new structure:
- Query OrgX memory or list the relevant entities first.
- Only scaffold new work when no matching initiative structure already exists.

3. Work against the current slice:
- Prefer updating the current task or workstream instead of creating parallel duplicate work.
- Keep your local implementation aligned with the active OrgX entity state.

4. Report concrete progress:
- Use OrgX progress/activity tools for real execution milestones.
- Register artifacts when code, docs, plans, screenshots, or reports are produced.

5. Surface decisions explicitly:
- If work is blocked on judgment, request a decision with clear options and impact.
- Do not bury blockers in prose.
- Only a person settles a decision. `orgx_decide` with `action: "approve"` or
  `"reject"` never approves or rejects anything: it returns the decision's
  `review_url` in OrgX. Give the person that link, report the work as waiting
  on them, and never say a decision was approved or rejected unless OrgX shows
  it settled.

6. Close the loop:
- Launching or spawning work starts it; it does not finish it. Report it as
  started, keep the returned run ID, and check it with `orgx_command_status`
  (`kind: "run"`, or `kind: "decision"` for a decision) before claiming any
  outcome. When `next_poll_after_ms` is a number, check again after that many
  milliseconds; `null` means the state is final. Use `orgx_inspect` for
  anything without a run, decision or command ID.
- When a task is truly done, verify it first.
- Then update completion state in OrgX if the current task is known.

## Quality bar

- Never assume OrgX entity state from memory alone.
- Never mark work complete without verification.
- Prefer one verified task completion over broad unverified status claims.
- If a write's outcome is unclear (timeout, dropped connection), retry it with
  the same `idempotency_key`: OrgX replays the stored result instead of
  duplicating the write. Reusing a key with a different body is refused (422);
  a 409 means the first attempt is still in flight.
- Use `source_client=codex` whenever the tool supports client attribution.
