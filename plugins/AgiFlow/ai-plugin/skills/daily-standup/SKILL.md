---
name: daily-standup
description: Produce a concise read-only Agiflow status summary covering completed work, work in progress, blockers, and recommended next priorities. Use for daily standups, morning checks, stakeholder updates, or a quick project pulse.
---

# Agiflow Daily Standup

Give a brief, evidence-based project pulse. Do not modify workspace data.

## Workflow

1. Call `get_current_scope` and resolve the requested project when needed.
2. Call `list_active_tasks_by_org` for current active work.
3. Call `list_work_units` for active and blocked work units.
4. Call `get_project_detail` when the summary is project-specific.
5. Call `list_members` to resolve assignee context.
6. Call `get_task`, `get_work_unit_progress`, or `list_task_comments` only when needed to confirm progress or a blocker.
7. Summarize:
   - Done or moved to Review since the latest available update
   - Current work in progress
   - Blocked or stalled items
   - Highest-priority next actions

## Priority Logic

1. Resolve blockers that prevent other work.
2. Finish existing work in progress before starting more work.
3. Select the highest-priority ready item.
4. Recommend refinement when a task is not ready.

## Output Format

Use short sections titled Done, In Progress, Blocked, and Next Up. Include task or work-unit identifiers when available. State clearly when no recent changes or blockers are found.

## Guardrails

- Remain read-only. Do not call mutation tools.
- Do not claim an item changed recently unless the returned data supports that conclusion.
- Distinguish confirmed blockers from possible signs of stalled work.
- Keep the summary scannable and end with one clear recommendation.
