---
name: triage
description: Diagnose stalled, blocked, overloaded, or unhealthy Agiflow projects and recommend specific corrective actions. Use for project health checks, blocked work, conflicting priorities, obsolete tasks, overloaded assignees, or an unmanageable backlog.
---

# Agiflow Triage

Diagnose before prescribing. Read the workspace first and separate evidence from inference.

## Workflow

1. Call `get_current_scope` and resolve the target project when one is specified.
2. Call `list_active_tasks_by_org`, `list_work_units`, and `list_members`.
3. For relevant items, call `get_task`, `get_work_unit`, `get_work_unit_progress`, and `list_task_comments` to inspect details and documented blockers.
4. Identify:
   - Stalled tasks or work units
   - Explicit blockers and unresolved dependencies
   - Missing or vague acceptance criteria
   - High-priority unassigned work
   - Excessive work in progress
   - Obsolete or duplicate tasks
   - Priority inversions
5. Classify each finding as Blocker, Warning, or Note.
6. Recommend one specific action for each finding and explain the expected impact.
7. Present the report and ask which actions the user approves.
8. Execute only approved actions with the appropriate tools, such as `update_task`, `create_task`, `batch_create_tasks`, or `create_task_comment`.
9. Re-read affected records to verify the result.

## Mutation Rules

- Do not change anything during diagnosis.
- Document the reason with `create_task_comment` before cancelling or materially re-scoping a task.
- Use `update_task` only after approval for reassignment, priority, status, or scope changes.
- Create new tasks only when the user approves the proposed corrective work.
- Do not use deletion as a default cleanup action.

## Response

Provide a concise health summary, evidence for each finding, severity, recommended action, and the three highest-priority next steps.
