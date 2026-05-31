---
name: run-task
description: "Execute a single Todo task through In Progress to Review, meeting every acceptance criterion with tests and vibe-lint checks. Refuses Planning-status tasks. Invoked as /agiflow:run-task <task>. Uses get_task, update_task, create_task_comment."
tags:
  - agiflow
  - mcp
  - execution
  - task
metadata:
  mirrors: backend/apis/agiflow-api .../prompts/task.md
---

> Invoked as `/agiflow:run-task`. In hosts without slash-prompts, this skill is triggered by matching intent and drives AgiFlow via its MCP tools.

**Usage**:

- `/agiflow:run-task <task-slug-or-id>` - Execute specific task
- `/agiflow:run-task` - List and select from available tasks

**Examples**:

- `/agiflow:run-task DXX-2` (using slug)
- `/agiflow:run-task 01K8FABMNEJG1XTA9JGHSNFV40` (using ID)
- `/agiflow:run-task` (interactive selection)

---

**Guardrails**

- Favor straightforward, minimal implementations first and add complexity only when it is requested or clearly required.
- Keep changes tightly scoped to the requested outcome within the task scope.
- A task represents a single, focused unit of work that can be completed in one session.

If a task slug/id is provided, load it with `get_task`; otherwise list available tasks with `list_tasks` for selection.

---

## AgiFlow Project Management Guidelines

Follow the shared AgiFlow project-management guidelines in [`references/agiflow-agents.md`](../../references/agiflow-agents.md) — agent assignment, the task status workflow and transitions, work-unit best practices, and the tags strategy apply to this workflow.


---

**Task Status Workflow**
Tasks move through these statuses in order:
`Planning → Todo → In Progress → Testing → Review → Done`
Exception paths: `Blocked` (requires human intervention), `Cancelled` (terminal).

**IMPORTANT: Planning Status Guard**
This skill ONLY executes tasks in "Todo" or later status. Tasks in "Planning" have NOT been groomed and are NOT ready for execution. Use `backlog-grooming` to promote Planning tasks to Todo first.

**Steps**
Track these steps as TODOs and complete them one by one.

## 1. Task Selection & Loading

**If task slug/id NOT provided:**

1. Use `list_tasks` MCP tool to show available tasks:
   - For the ready queue, filter by `status: "Todo"` (sorted by priority automatically)
   - Do NOT pick up tasks in "Planning" status — they have not been groomed yet
   - Display: slug, title, priority, assignee, acceptance criteria count
2. Ask user to select which task to work on.
3. Once user selects, proceed with the selected task slug/id.

**If task slug/id IS provided:** 4. Use `get_task` MCP tool with the provided slug/id to retrieve:

- Task: title, description, priority, status, acceptance criteria
- Comments: Previous progress updates and discussions

5. Review the task details to understand:
   - Complete requirements and deliverables
   - Acceptance criteria that must be met
   - Any blockers or dependencies noted in comments

**5b. PLANNING STATUS GUARD (MANDATORY):**

- If task status is "Planning": **REFUSE to execute**
- Report: "Cannot execute task [SLUG]: still in Planning status. Use **backlog-grooming** to promote it to Todo first."
- **STOP execution** — do not proceed

## 2. Start Task Execution

6. If task status is "Todo", use `update_task` MCP tool to set status to "In Progress".
7. Create a TODO list of acceptance criteria in execution order (use TodoWrite tool).
8. Document execution start in task via `update_task` devInfo:
   ```typescript
   devInfo: {
     currentSession: "<current-session-id>",
     startedAt: "<timestamp>"
   }
   ```

## 3. Implement Task

9. For each acceptance criterion:
   - Review the specific requirement
   - **BEFORE editing any code**: Use `vibe-lint` MCP `get-file-design-pattern` (MANDATORY)
   - Implement the criterion keeping changes minimal and focused
   - **AFTER editing code**: Use `vibe-lint` MCP `review-code-change` (MANDATORY)
   - Update task `devInfo` with implementation notes:
     ```typescript
     devInfo: {
       filesChanged: ["path/to/file.ts:42"],
       testResults: { passed: true, coverage: "85%" },
       notes: "Implementation notes here",
       currentSession: "<session-id>"
     }
     ```
   - Mark acceptance criterion as checked via `update_task`
   - Update your TODO list (mark criterion as completed)

10. Between acceptance criteria:
    - Commit changes with meaningful commit messages
    - Run tests to ensure no regressions
    - Update task devInfo with progress

## 4. Testing Phase

11. When ALL acceptance criteria are met:
    - Verify all criteria have status checked
    - Use `update_task` to move status to "Testing"
    - Run the full test suite for affected code:
      - Unit tests
      - Integration tests
      - Type checking and lint

12. **If tests PASS:**
    - Update devInfo with passing test results
    - Proceed to step 13 (Task Completion)

13. **If tests FAIL:**
    - Increment `retryCount` in devInfo:
      ```typescript
      devInfo: {
        ...existing,
        retryCount: (existing.retryCount ?? 0) + 1,
        lastFailureReason: "<description of what failed>"
      }
      ```
    - If `retryCount >= maxRetries` (default maxRetries = 2):
      - Use `update_task` to move status to "Blocked"
      - Use `create_task_comment` to document the repeated failure and what human intervention is needed
      - Stop — do not retry
    - If `retryCount < maxRetries`:
      - Use `update_task` to move status back to "Todo"
      - Use `create_task_comment` to document the failure reason
      - Stop — agent will re-pick from Todo queue on next cycle

## 5. Task Completion

14. After tests pass, review all files changed (use git diff).

15. Draft a PR description for the task (DO NOT create the PR yet - just draft the text):
    - Title format: `[TASK-SLUG] Task title` (e.g., `[DXX-2] Add user authentication`)
    - Body should include:
      - Task reference and summary
      - List of changes made
      - Files modified (use `file.ts:42` format)
      - Test results

16. Use `update_task` to set status to "Review" and save draft PR text and commit message:

    ```typescript
    {
      status: "Review",
      devInfo: {
        ...existing,
        draftCommitMessage: "feat(auth): add user authentication\n\n- Add login endpoint with session management\n- Add password validation\n- Add unit tests for auth flow",
        draftPr: {
          title: "[DXX-2] Add user authentication",
          body: "## Summary\n\nImplemented user authentication feature.\n\n## Changes\n\n- Added login endpoint\n- Added session management\n\n## Files Modified\n\n- src/auth/login.ts:42\n- src/auth/session.ts:15\n\n## Test Results\n\nAll tests passing."
        },
        finalNotes: "All acceptance criteria met. Files changed: [...]. Tests passing.",
        completedBy: "<member-id>",
        totalDuration: "45 minutes"
      }
    }
    ```

    **Note on draftCommitMessage**: Write a conventional commit message that will be used for the final git commit. Format: `type(scope): description` with optional body listing changes.

17. Use `create_task_comment` to add final summary:
    - Task scope and goals achieved
    - All files created/modified (use `file.ts:42` format)
    - Test coverage and results
    - Any follow-up work needed

## 6. Handle Blockers

18. If blocked at any point:
    - Use `update_task` to set status to "Blocked"
    - Use `update_task` to update devInfo with blocker details:
      ```typescript
      devInfo: {
        ...existing,
        blockedReason: "<why the task is blocked>",
        blockedBy: "<memberId or 'system'>"
      }
      ```
    - Use `create_task_comment` on task with blocker information explaining what human intervention is needed

**Reference**

- Use `get_task` to review task details before starting
- Use `list_task_comments` to see previous progress updates
- Use `update_task` to track devInfo and acceptance criteria progress

**Integration with Other Tools**

- **vibe-lint MCP**: ALWAYS use before/after editing files for pattern compliance
- **Scaffolding MCP**: Document scaffolded code in task comments

**Common Mistakes to Avoid**

- ❌ Starting work without reviewing task details with `get_task`
- ❌ Not moving task to "In Progress" before starting
- ❌ Skipping vibe-lint MCP validation (MANDATORY for every file)
- ❌ Not tracking devInfo (files changed, tests, session ID)
- ❌ Marking acceptance criteria checked before actually completing them
- ❌ Moving to "Review" without going through "Testing" first
- ❌ Not documenting progress in comments
- ❌ Forgetting to add file references (file.ts:42 format) in final comment
- ❌ Not running tests before moving to "Review"
- ❌ Not committing changes incrementally
- ❌ Moving to "Blocked" without explaining what human intervention is needed
- ❌ Skipping retryCount increment when moving failed task back to "Todo"
- ❌ Starting work on a task in "Planning" status (must be promoted to "Todo" via `backlog-grooming` first)
