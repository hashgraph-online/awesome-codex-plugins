---
name: triage
description: "Diagnose project health: classify issues by severity (BLOCKER/WARNING/NOTE) and recommend actions for stuck, overdue, or unwieldy backlogs. Invoked as /agiflow:triage. Uses list_tasks, list_active_tasks_by_org, list_work_units, get_project_detail."
tags:
  - agiflow
  - mcp
  - triage
  - diagnostics
metadata:
  mirrors: backend/apis/agiflow-api .../prompts/triage.md
---

> Invoked as `/agiflow:triage`. In hosts without slash-prompts, this skill is triggered by matching intent and drives AgiFlow via its MCP tools.

**Usage**:

- `/agiflow:triage` - Diagnose project health and surface actionable problems
- `/agiflow:triage <project-slug-or-id>` - Triage a specific project

**Examples**:

- `/agiflow:triage` (triage current project or org)
- `/agiflow:triage my-project` (triage specific project)

---

**Purpose**
Diagnose stalled, blocked, or unhealthy project states and recommend concrete actions. Also handles task lifecycle management: cancelling/archiving obsolete tasks, re-prioritizing (moving Todo tasks back to Planning), and fast-tracking incoming bugs. Real projects get stuck — this skill helps users identify WHY and decide WHAT TO DO, not just see status.

**Guardrails**

- Diagnose before prescribing — understand the problem before suggesting solutions.
- Surface problems by severity: blockers first, then warnings, then notes.
- Recommend specific actions (reassign, split, refine, cancel, re-prioritize) — not vague advice.
- Do not make changes automatically — present findings and let the user decide.
- When cancelling tasks, document the reason in a comment before changing status.

---

## AgiFlow Project Management Guidelines

Follow the shared AgiFlow project-management guidelines in [`references/agiflow-agents.md`](../../references/agiflow-agents.md) — agent assignment, the task status workflow and transitions, work-unit best practices, and the tags strategy apply to this workflow.


---

**Steps**

## 1. Load Project State

1. Use `list_active_tasks_by_org` MCP tool to get all active (non-completed) tasks across the organization.
2. Use `list_work_units` MCP tool to get work unit status overview.
3. Use `list_members` MCP tool to understand team capacity.
4. If a specific project is provided, use `get_project_detail` to focus on that project.

## 2. Identify Problems

5. Analyze the data and flag issues in these categories:

### Stalled Work

- Tasks in "In Progress" with no recent devInfo updates (stalled execution)
- Work units in "in_progress" where no tasks have moved in a long time
- Tasks assigned to an agent but showing no activity

**For each stalled item:**

- When was it last updated?
- Is there a blocker documented in comments?
- Is the task too large (needs decomposition)?
- Is the assignee available?

### Blocked Items

- Work units with status "blocked"
- Tasks with blocker comments but no follow-up
- Tasks that depend on other incomplete tasks

**For each blocked item:**

- What's the blocker? (check comments with `list_task_comments`)
- Can the blocker be resolved, worked around, or descoped?
- Should the blocked task be reassigned or split?

### Quality Gaps

- Tasks with no acceptance criteria (unrefined)
- Tasks with vague descriptions ("implement feature X")
- High-priority tasks that are unassigned
- Work units with more than 8 tasks (too complex for one session)

### Imbalance

- One agent assigned to too many in-progress tasks (context switching)
- All tasks "In Progress", nothing "Done" (no focus)
- High-priority items in backlog while low-priority items are being worked on

## 3. Severity Classification

6. Classify each finding:

| Severity    | Meaning                            | Action needed              |
| ----------- | ---------------------------------- | -------------------------- |
| **BLOCKER** | Prevents progress on critical path | Must resolve now           |
| **WARNING** | Creates risk or inefficiency       | Should resolve this sprint |
| **NOTE**    | Improvement opportunity            | Address when convenient    |

## 4. Recommend Actions

7. For each problem, recommend ONE specific action:

| Problem                           | Recommended Action                                            | Tool to Use                                                          |
| --------------------------------- | ------------------------------------------------------------- | -------------------------------------------------------------------- |
| Task stalled, too large           | Split into smaller tasks                                      | `batch_create_tasks` + `update_task` (close original)                |
| Task stalled, unclear scope       | Refine the task                                               | Suggest `refine-task` skill                                          |
| Task blocked by dependency        | Reorder or reassign                                           | `update_task` to change assignee or priority                         |
| Work unit blocked                 | Create unblocking task                                        | `batch_create_tasks` for the blocker fix                             |
| Task unrefined (no AC)            | Add acceptance criteria                                       | Suggest `refine-task` skill                                          |
| Agent overloaded                  | Reassign tasks                                                | `update_task` to change assignee                                     |
| No focus (everything in-progress) | Pick ONE work unit to finish                                  | `update_task` to deprioritize others                                 |
| Wrong priorities being worked     | Reprioritize backlog                                          | `update_task` to adjust priorities                                   |
| Task obsolete or descoped         | Cancel with documented reason                                 | `create_task_comment` (reason) + `update_task` (status: "cancelled") |
| Todo task needs re-scoping        | Move back to Planning                                         | `update_task` (status: "planning") for re-grooming                   |
| Incoming bug, urgent              | Fast-track: create in Planning with `bug:` tag, high priority | `create_task` + suggest `backlog-grooming` to promote                |

## 5. Present Triage Report

8. Present findings to the user:

```
## Triage Report

**Scope:** [Organization / Project name]
**Date:** [current date]

### Summary
- Active tasks: [N]
- In progress: [N]
- Blocked: [N]
- Issues found: [N blockers, N warnings, N notes]

### Blockers (must resolve)
1. **[Task/WU slug]** — [problem description]
   - Recommendation: [specific action]
   - Impact: [what's affected if not resolved]

### Warnings (should resolve)
1. **[Task/WU slug]** — [problem description]
   - Recommendation: [specific action]

### Notes (nice to fix)
1. **[observation]** — [suggestion]

### Health Score
[Quick assessment: Healthy / Needs Attention / At Risk]

### Recommended Next Steps
1. [Most important action]
2. [Second most important action]
3. [Third action]
```

## 6. Execute (with user approval)

9. After presenting findings, ask the user which actions they want to take.
10. Execute approved actions using the appropriate MCP tools.
11. After changes, re-check state with `list_active_tasks_by_org` to confirm improvements.

---

**Diagnostic Patterns**

| What you observe                     | What it usually means             | What to do                                                        |
| ------------------------------------ | --------------------------------- | ----------------------------------------------------------------- |
| 40 tasks, no work units              | Planned without organizing        | Group into work units                                             |
| Work units exist, all tasks "Todo"   | Planned but not started           | Pick one work unit, start execution                               |
| Everything "In Progress"             | No focus, context switching       | Finish ONE thing, then move on                                    |
| High-priority items in backlog       | Wrong things being worked on      | Reprioritize and reassign                                         |
| Tasks with no acceptance criteria    | Unrefined, will fail in execution | Refine before assigning                                           |
| Agent with 5+ in-progress tasks      | Overloaded, nothing finishing     | Limit WIP to 2-3 per agent                                        |
| Completed tasks with unchecked AC    | Rubber-stamped, not actually done | Review with `review-work`                                         |
| Old tasks nobody mentions anymore    | Scope changed, tasks are obsolete | Cancel with reason documented                                     |
| Todo tasks that keep getting skipped | Wrong priority or unclear scope   | Re-prioritize or move back to Planning                            |
| User reports a bug mid-sprint        | Incoming bug needs fast-tracking  | Create with `bug:` tag, high priority, suggest `backlog-grooming` |

---

**Common Mistakes to Avoid**

- Only reporting status without diagnosing root causes
- Suggesting vague actions ("improve task descriptions") instead of specific ones
- Making changes without user approval
- Ignoring blocked items (they don't unblock themselves)
- Not checking task comments for context on why things stalled
- Treating symptoms (reassigning a stalled task) without addressing causes (task was too vague)
