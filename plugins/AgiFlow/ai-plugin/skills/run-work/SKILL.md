---
name: run-work
description: "Execute a work unit end-to-end: sequence tasks by dependency, implement, test between tasks, commit, and track progress. Use to deliver a complete feature in one session. Invoked as /agiflow:run-work <work-unit>. Uses get_work_unit, list_tasks, update_task, get_work_unit_progress."
tags:
  - agiflow
  - mcp
  - execution
  - work-unit
metadata:
  mirrors: backend/apis/agiflow-api .../prompts/work.md
---

> Invoked as `/agiflow:run-work`. In hosts without slash-prompts, this skill is triggered by matching intent and drives AgiFlow via its MCP tools.

**Usage**:

- `/agiflow:run-work <work-unit-slug-or-id>` - Execute specific work unit
- `/agiflow:run-work` - List and select from available work units

**Examples**:

- `/agiflow:run-work DXX-WU-1` (using slug)
- `/agiflow:run-work 01K8FABMNEJG1XTA9JGHSNFV40` (using ID)
- `/agiflow:run-work` (interactive selection)

---

**Guardrails**

- Favor straightforward, minimal implementations first and add complexity only when it is requested or clearly required.
- Keep changes tightly scoped to the requested outcome within the work unit scope.
- A work unit represents a cohesive feature/epic that can be completed in one Claude Code session.

If a work unit slug/id is provided, load it with `get_work_unit`; otherwise list available work units with `list_work_units` for selection.

---

## AgiFlow Project Management Guidelines

Follow the shared AgiFlow project-management guidelines in [`references/agiflow-agents.md`](../../references/agiflow-agents.md) — agent assignment, the task status workflow and transitions, work-unit best practices, and the tags strategy apply to this workflow.


---

**Task Status Workflow (per task)**
Each task moves individually through: `Todo → In Progress → Testing → Review`
The work unit stays `in_progress` until all tasks reach `Review` or `Done`.
If any task hits `Blocked`, consider setting the work unit to `blocked` too.

**IMPORTANT: Planning Status Guard**
This skill ONLY executes tasks in "Todo" or later status. Tasks in "Planning" have NOT been groomed and are NOT ready for execution. Use `backlog-grooming` to promote Planning tasks to Todo first.

**Steps**
Track these steps as TODOs and complete them one by one.

## 1. Work Unit Selection & Loading

**If work unit slug/id NOT provided:**

1. Use `list_work_units` MCP tool to show available work units:
   - Filter by `status: "in_progress"` for active work, or work units with tasks in "Todo"
   - Do NOT pick up work units where all tasks are still in "Planning" status
   - Display: slug, title, type, priority, task count, status
2. Ask user to select which work unit to work on.
3. Once user selects, proceed with the selected work unit slug/id.

**If work unit slug/id IS provided:** 4. Use `get_work_unit` MCP tool with the provided slug/id to retrieve:

- Work unit: title, description, goals, type, priority, status, dates, devInfo
- Tasks: All tasks associated with this work unit (already included in response)
- Note: `get_work_unit` returns tasks automatically - no separate `list_tasks` call needed

5. Review the work unit and all its tasks to understand:
   - Complete feature scope and deliverables
   - Task dependencies and execution order
   - Acceptance criteria across all tasks

**5b. PLANNING STATUS GUARD (MANDATORY):**

- Check all tasks in the work unit
- If ANY task has status "Planning": **REFUSE to execute**
- Report: "Cannot execute: N task(s) are still in Planning status. Use **backlog-grooming** to promote them to Todo first."
- List the Planning tasks by title
- **STOP execution** — do not proceed

## 2. Start Work Unit Execution

6. If work unit status is "planning":
   - First verify ALL tasks are in "Todo" or later status (not "Planning")
   - If verified, use `update_work_unit` MCP tool to set status to "in_progress"
   - If any tasks are in "Planning", REFUSE and suggest `backlog-grooming`
7. Create a TODO list of all tasks in execution order (use TodoWrite tool).
8. Document execution plan in work unit via `update_work_unit` devInfo:
   ```typescript
   devInfo: {
     executionPlan: "Backend API → Frontend UI → Tests → Documentation",
     sessionId: "<current-session-id>",
     startedAt: "<timestamp>"
   }
   ```

## 3. Execute Tasks Sequentially

9. For each task in the work unit (in dependency order from the tasks array):
   - Review task details: title, description, acceptance criteria, assignee
   - Use `update_task` MCP tool to set status to "In Progress"
   - **BEFORE editing any code**: Use `architect` MCP `get_file_design_pattern` (MANDATORY)
   - Implement the task following acceptance criteria
   - **AFTER editing code**: Use `architect` MCP `review_code_change` (MANDATORY)
   - Update task `devInfo` with implementation notes:
     ```typescript
     devInfo: {
       filesChanged: ["path/to/file.ts:42"],
       testResults: { passed: true, coverage: "85%" },
       notes: "Implementation notes here"
     }
     ```
   - Mark acceptance criteria as checked via `update_task`

   **Testing phase for each task:**
   - Use `update_task` to move status to "Testing"
   - Run unit tests, integration tests, type check and lint for affected code
   - **If tests PASS**: proceed to move task to "Review"
   - **If tests FAIL**:
     - Increment `retryCount` in devInfo
     - If `retryCount >= maxRetries` (default: 2): move task to "Blocked", set work unit to "blocked", stop
     - If `retryCount < maxRetries`: move task back to "Todo", document failure, continue to next task or stop session
   - Use `update_task` to set status to "Review" when tests pass

   - Update your TODO list (mark task as completed)

10. Between tasks:
    - Commit changes with meaningful commit messages
    - Run tests to ensure no regressions
    - Update work unit progress in devInfo

## 4. Work Unit Progress Tracking

11. The work unit tasks array automatically updates as tasks are completed.
    - Use `get_work_unit` to check current state and task statuses
    - Track: How many tasks in Review or Done vs. total?
    - Monitor: Are we on track for target date?
    - Work unit stays `in_progress` until all tasks reach `Review` or `Done`

12. Update work unit `devInfo` as you progress via `update_work_unit`:
    ```typescript
    devInfo: {
      executionPlan: "...",
      sessionId: "<session-id>",
      startedAt: "<timestamp>",
      progress: {
        completedTasks: 3,
        totalTasks: 8,
        lastTaskCompleted: "Implement cart API",
        currentTask: "Add cart UI component"
      },
      testResults: {
        unitTests: "passing",
        integrationTests: "passing",
        coverage: "85%"
      },
      blockers: [] // or list any blockers encountered
    }
    ```

## 5. Work Unit Completion

13. When ALL tasks in work unit are in "Review" or "Done":
    - Verify all tasks have status "Review" or "Done"
    - Verify all acceptance criteria across all tasks are met
    - Run full test suite for the feature
    - Review all files changed (use git diff)

14. Draft a PR description for the work unit (DO NOT create the PR yet - just draft the text):
    - Title format: `[WORK-UNIT-SLUG] Work unit title` (e.g., `[DXX-WU-1] Shopping cart feature`)
    - Body should include:
      - Work unit reference and summary
      - List of tasks completed
      - Summary of all changes across tasks
      - Files modified (use `file.ts:42` format)
      - Test results

15. Use `update_work_unit` to set status to "completed" and save draft PR text and commit message:

    ```typescript
    {
      status: "completed",
      completedAt: new Date(),
      devInfo: {
        ...existing,
        draftCommitMessage: "feat(cart): implement shopping cart feature\n\n- Add cart API endpoints\n- Add cart UI components\n- Add integration tests\n\nCloses: DXX-WU-1",
        draftPr: {
          title: "[DXX-WU-1] Shopping cart feature",
          body: "## Summary\n\nImplemented shopping cart feature.\n\n## Tasks Completed\n\n- [DXX-1] Add cart API\n- [DXX-2] Add cart UI\n- [DXX-3] Add cart tests\n\n## Changes\n\n- Added cart endpoints\n- Added cart components\n- Added integration tests\n\n## Files Modified\n\n- src/api/cart.ts:42\n- src/components/Cart.tsx:15\n- tests/cart.test.ts:1\n\n## Test Results\n\nAll tests passing. Coverage: 85%"
        },
        finalNotes: "All tasks completed. Files changed: [...]. Tests passing.",
        completedBy: "<member-id>",
        totalDuration: "3.5 hours"
      }
    }
    ```

    **Note on draftCommitMessage**: Write a conventional commit message that will be used for the final git commit. Format: `type(scope): description` with optional body listing changes.

16. Create final summary comment documenting:
    - Work unit scope and goals achieved
    - All files created/modified (use `file.ts:42` format)
    - Test coverage and results
    - Any follow-up work needed
    - Performance or architectural notes

## 6. Handle Blockers or Scope Changes

17. If blocked on a task:
    - Use `update_task` to set task status to "Blocked"
    - Use `update_work_unit` to set status to "blocked"
    - Document blocker in work unit devInfo
    - Use `create_task_comment` on blocked task with details explaining what human intervention is needed
    - Consider creating follow-up tasks for blockers

18. If scope changes during execution:
    - Use `create_task` to add new tasks to work unit
    - Update work unit description/goals if needed
    - Communicate scope change in work unit comments

**Common Mistakes to Avoid**

- ❌ Starting without reviewing all tasks in work unit (lack of context)
- ❌ Working on tasks in wrong order (missing dependencies)
- ❌ Skipping vibe-lint MCP validation (MANDATORY for every file)
- ❌ Not tracking work unit-level progress in devInfo
- ❌ Completing tasks in isolation without considering work unit goals
- ❌ Not running integration tests between tasks
- ❌ Moving task to "Review" without first going through "Testing"
- ❌ Marking work unit complete when tasks are still in "In Progress" or "Testing"
- ❌ Not documenting scope changes or blockers
- ❌ Forgetting to commit between tasks (losing incremental progress)
- ❌ Not updating work unit status when blocked
- ❌ Setting work unit to "completed" before all tasks reach "Review" or "Done"
- ❌ Executing tasks that are still in "Planning" status (must be promoted to "Todo" via `backlog-grooming` first)
