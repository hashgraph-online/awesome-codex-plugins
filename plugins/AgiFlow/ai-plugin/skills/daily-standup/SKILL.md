---
name: daily-standup
description: "Read-only project pulse: what got done, what's in progress, what's blocked, and what's next. Use for daily orientation or stakeholder summaries. Invoked as /agiflow:daily-standup. Uses list_tasks, list_active_tasks_by_org, list_work_units, get_work_unit_progress."
tags:
  - agiflow
  - mcp
  - standup
  - reporting
metadata:
  mirrors: backend/apis/agiflow-api .../prompts/dailyStandup.md
---

> Invoked as `/agiflow:daily-standup`. In hosts without slash-prompts, this skill is triggered by matching intent and drives AgiFlow via its MCP tools.

**Usage**:

- `/agiflow:daily-standup` - Get today's standup summary
- `/agiflow:daily-standup <project-slug-or-id>` - Standup for a specific project

**Examples**:

- `/agiflow:daily-standup` (org-wide standup)
- `/agiflow:daily-standup my-project` (project-specific standup)

---

**Purpose**
Provide a quick daily pulse: what happened, what's next, what's blocked. Designed for the start-of-day check-in — users open the app and want a 2-minute overview, not a deep dive.

**Guardrails**

- Keep it brief — this is a standup, not a retrospective.
- Lead with what changed (completed, moved, blocked) since last check.
- Always end with a clear "here's what to do next" recommendation.
- Do not make changes — this is a read-only status check.

---

## AgiFlow Project Management Guidelines

Follow the shared AgiFlow project-management guidelines in [`references/agiflow-agents.md`](../../references/agiflow-agents.md) — agent assignment, the task status workflow and transitions, work-unit best practices, and the tags strategy apply to this workflow.


---

**Steps**

## 1. Gather Current State

1. Use `list_active_tasks_by_org` MCP tool to get all active tasks.
2. Use `list_work_units` MCP tool with `status: "in_progress"` to get active work units.
3. If a specific project is provided, use `get_project_detail` for focused view.
4. Use `list_members` MCP tool to understand who's working.

## 2. What Happened (Done)

5. Identify recently completed work:
   - Tasks that moved to "Done" or "Review" status
   - Work units that were completed
   - Look at task devInfo for completion timestamps

6. Summarize completions:
   - What was delivered?
   - Who completed it?
   - Any notable achievements or milestones?

## 3. What's In Progress (Doing)

7. Identify current active work:
   - Tasks in "In Progress" status
   - Work units in "in_progress" status with progress info

8. For each active item:
   - What's the task/work unit about?
   - Who's working on it?
   - How far along? (check acceptance criteria checked vs. total)
   - Expected completion?

## 4. What's Blocked (Blockers)

9. Identify blockers:
   - Work units with status "blocked"
   - Tasks with recent blocker comments
   - Tasks in "In Progress" with no recent updates (potentially stuck)
   - High-priority items that haven't been picked up

10. For each blocker:
    - What's blocking it?
    - How long has it been blocked?
    - Who can unblock it?

## 5. What's Next (Recommendations)

11. Based on current state, recommend:
    - Which task or work unit to pick up next
    - Which blocker to resolve first
    - Whether to continue current work or pivot

**Priority logic:**

- Unblock blocked items first (they're wasting time)
- Finish in-progress work before starting new work (reduce WIP)
- Start highest-priority unstarted work
- Refine tasks that need refinement before assigning

## 6. Present Standup

12. Format the standup concisely:

```
## Daily Standup

### Done (since last check)
- [task slug] [title] — completed by [assignee]
- [task slug] [title] — moved to review

### In Progress
- [task slug] [title] — [assignee], [N/M] acceptance criteria done
- [WU slug] [title] — [N/M] tasks complete

### Blocked
- [task slug] [title] — [blocker description]

### Next Up
1. [Recommended action] — [why]
2. [Second recommendation] — [why]

### Quick Stats
- Active tasks: [N] | Completed today: [N] | Blocked: [N]
```

If nothing happened since last check, say so clearly: "No changes since last standup. Current focus: [what's in progress]."

---

**Common Mistakes to Avoid**

- Making the standup too long (keep it scannable)
- Only reporting status without recommending next actions
- Ignoring blocked items
- Not surfacing unassigned high-priority work
- Making changes during standup (this is read-only)
