---
name: project-plan
description: Turn a product goal or feature request into a clear Agiflow project plan with small, testable tasks in Planning status. Use when starting a project, decomposing a feature, clarifying requirements, or converting an idea into an actionable backlog.
---

# Agiflow Project Plan

Create a focused near-term plan. Plan tasks first and leave work-unit creation to backlog grooming.

## Workflow

1. Call `get_current_scope` and resolve the target project with `list_projects` when needed.
2. Call `get_project_detail`, `list_project_statuses`, and `list_tasks` to understand goals, configured statuses, and existing work.
3. Ask only the questions needed to resolve the intended outcome, users, scope, constraints, and definition of done.
4. Check for duplicate or overlapping tasks before proposing new ones.
5. Decompose the outcome into small vertical slices that can be completed and verified independently.
6. For each proposed task, include:
   - Clear title
   - Outcome-focused description
   - At least two testable acceptance criteria
   - Explicit in-scope and out-of-scope boundaries
   - Priority and useful categorization tags
   - Dependencies or sequencing notes when relevant
7. Present the complete task plan and request approval before writing.
8. After approval, use `batch_create_tasks` for multiple tasks or `create_task` for one task. Use the exact Planning status name returned by `list_project_statuses`.
9. Call `list_tasks` to verify the created tasks and report any per-item errors.

## Planning Rules

- Do not create work units in this workflow.
- Do not promote tasks to Todo.
- Prefer the smallest plan that delivers useful progress.
- Split tasks that combine unrelated outcomes or cannot be verified independently.
- Preserve existing work and avoid duplicates.

## Response

Report created task titles, priorities, dependencies, and any tasks that still need user decisions. Recommend `refine-task` for ambiguous tasks or `backlog-grooming` when the Planning backlog is ready.
