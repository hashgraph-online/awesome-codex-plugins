---
name: backlog-grooming
description: Review Agiflow Planning tasks for readiness, prioritize approved work, group related tasks into work units, and promote ready tasks to Todo. Use when grooming a backlog, organizing planned tasks, creating work units, or deciding what should be executed next.
---

# Agiflow Backlog Grooming

Treat grooming as the quality gate between Planning and Todo.

## Workflow

1. Resolve the target project and call `list_project_statuses` to discover its exact status names.
2. Call `list_tasks` for Planning tasks, `list_work_units` for existing active work units, and `list_members` for assignment context.
3. Call `get_task` for tasks whose readiness, dependencies, or acceptance criteria are unclear.
4. Classify every Planning task as:
   - Ready
   - Needs refinement
   - Blocked by a dependency
   - Duplicate or obsolete
5. Require a clear outcome, sufficient context, and at least two testable acceptance criteria before promotion.
6. Propose a priority order and explain the tradeoffs.
7. Group three to eight cohesive tasks into a work unit only when they deliver one shared capability. Leave one or two related tasks standalone and split groups larger than eight.
8. Review existing work units for shared dependencies and sequencing conflicts.
9. Present the proposed promotions, work units, assignments, and dependency order. Request approval before writing.
10. After approval:
    - Use `batch_create_work_units` for approved groups.
    - Use `update_task` to move only ready, ungated tasks to the exact Todo status and set their ordering.
11. Verify with `list_tasks` and `list_work_units`.

## Guardrails

- Never promote a vague task or a task missing testable acceptance criteria.
- Never promote a downstream task whose required upstream work is incomplete.
- Do not force unrelated work into one work unit.
- Do not modify records before the user approves the proposed grooming plan.
- Recommend `refine-task` for tasks that fail readiness checks.

## Response

Report promoted tasks, created work units, items left in Planning, dependency gates, and the recommended execution order.
