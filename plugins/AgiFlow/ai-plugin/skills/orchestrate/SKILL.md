---
name: orchestrate
description: "Pipeline orchestration: dispatch the highest-priority ready tasks/work units to agents, manage capacity, and coordinate the Todo to Done flow. Invoked as /agiflow:orchestrate. Uses list_tasks, list_active_tasks_by_org, list_members, update_task, get_work_unit_progress."
tags:
  - agiflow
  - mcp
  - orchestration
  - dispatch
metadata:
  mirrors: backend/apis/agiflow-api .../prompts/orchestrate.md
---

> Invoked as `/agiflow:orchestrate`. In hosts without slash-prompts, this skill is triggered by matching intent and drives AgiFlow via its MCP tools.

**Usage**:

- `/agiflow:orchestrate` - Check pipeline state and dispatch the next highest-priority task

---

**Guardrails**

- This is a read-assess-dispatch loop, not an implementation prompt.
- Do NOT implement tasks here — use `/agiflow:run-task` for that.
- Keep capacity checks honest: do not dispatch if at capacity.
- Report pipeline state even when no dispatch is needed.

---

## AgiFlow Project Management Guidelines

Follow the shared AgiFlow project-management guidelines in [`references/agiflow-agents.md`](../../references/agiflow-agents.md) — agent assignment, the task status workflow and transitions, work-unit best practices, and the tags strategy apply to this workflow.


---

**Steps**
Track these steps as TODOs and complete them one by one.

## 1. Assess Current Pipeline State

1. Use `list_tasks` to count tasks in each active status column:
   - `status: "In Progress"` — tasks currently being coded by agents
   - `status: "Testing"` — tasks running test suites
   - `status: "Review"` — tasks awaiting human review
   - `status: "Blocked"` — tasks requiring human intervention
   - `status: "Todo"` — tasks ready for pickup (sorted by priority automatically)

2. Report the pipeline state in a concise table:
   ```
   Pipeline State:
   ┌──────────────┬───────┐
   │ Status       │ Count │
   ├──────────────┼───────┤
   │ Todo         │   N   │
   │ In Progress  │   N   │
   │ Testing      │   N   │
   │ Review       │   N   │
   │ Blocked      │   N   │
   └──────────────┴───────┘
   ```

## 2. Check Capacity

3. Determine active task count: `In Progress` + `Testing` combined.
4. Check capacity limit (default: 3 concurrent active tasks unless specified).
5. If at or above capacity:
   - Report: "At capacity (N active tasks). No dispatch needed."
   - List any Blocked tasks that need human attention.
   - Stop here.

## 3. Prioritize the Todo Queue

6. Use `list_tasks` with `status: "Todo"` to retrieve the ready queue.
   - Tasks are automatically sorted by priority (high → medium → low).
   - Within the same priority, tasks are ordered by position then creation date.

7. Review the top candidates:
   - Show the top 3-5 Todo tasks with: slug, title, priority, assignee, retryCount (from devInfo)
   - Skip any task where `devInfo.retryCount >= devInfo.maxRetries` (should be Blocked — flag it)

## 4. Dispatch

8. Pick the highest-priority eligible Todo task.
9. Report the dispatch decision:
   ```
   Dispatching: [SLUG] Task title (priority: high)
   Reason: Highest priority task in Todo queue
   ```
10. Instruct the agent to run the task:
    - Use `/agiflow:run-task <slug>` to execute it
    - Or if already in an agent session, invoke the run-task prompt directly

## 5. Surface Blocked Tasks

11. If there are any Blocked tasks, list them with their `blockedReason` from devInfo:
    ```
    Blocked Tasks Requiring Human Attention:
    - [SLUG] Task title: <blockedReason>
    ```
12. Suggest actions for each blocked task (e.g., resolve dependency, provide credentials, clarify spec).

**Common Mistakes to Avoid**

- ❌ Dispatching when already at capacity
- ❌ Picking a lower-priority task when a higher-priority Todo exists
- ❌ Dispatching a task that has `retryCount >= maxRetries` (it should be Blocked)
- ❌ Skipping the pipeline state report
- ❌ Attempting to implement the task inside this prompt
