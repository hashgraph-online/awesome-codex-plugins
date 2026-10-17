---
name: refine-task
description: Refine an existing Agiflow task into an unambiguous, testable specification without expanding its intended outcome. Use when a task is vague, lacks acceptance criteria, has unclear scope or dependencies, or is not ready for backlog grooming.
---

# Agiflow Refine Task

Make the selected task ready for confident execution while preserving its original intent.

## Workflow

1. Resolve the task with `get_current_scope`, `list_projects`, `list_tasks`, or `get_task` as needed.
2. Call `get_task` for full details and `list_task_comments` when prior decisions may affect scope.
3. Call `list_project_statuses` and `list_members` only when status or assignment context is relevant.
4. Evaluate the task for:
   - Clear user or business outcome
   - Concrete scope boundaries
   - Objective acceptance criteria
   - Known dependencies and blockers
   - Appropriate priority and assignee
   - Enough context to complete without guessing
5. Ask focused clarification questions for unresolved decisions. Do not invent requirements.
6. Draft the refined title, description, acceptance criteria, scope boundaries, and dependency notes.
7. Show the proposed changes and request approval.
8. After approval, call `update_task` with only the fields that need to change.
9. Call `get_task` again to verify the saved result.

## Quality Test

Acceptance criteria must be specific, measurable, achievable within the task, relevant to its outcome, and directly verifiable. Replace phrases such as "works correctly" or "handles errors" with observable behavior.

## Guardrails

- Do not add new product requirements during refinement.
- Do not move the task from Planning to Todo. Backlog grooming owns that transition.
- Do not delete the task.
- Preserve useful existing context and comments.

## Response

Summarize what changed, which ambiguities were resolved, and whether the task is ready for `backlog-grooming`.
