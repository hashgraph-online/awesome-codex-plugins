---
name: backlog-grooming
description: "Groom Planning tasks: verify readiness, prioritize, promote to Todo, and group into 3-8 task work units. The only gate from Planning to Todo. Invoked as /agiflow:backlog-grooming. Uses list_tasks, update_task, reorder_tasks, batch_create_work_units, list_work_units."
tags:
  - agiflow
  - mcp
  - grooming
  - work-units
  - prioritization
metadata:
  mirrors: backend/apis/agiflow-api .../prompts/backlogGrooming.md
---

> Invoked as `/agiflow:backlog-grooming`. In hosts without slash-prompts, this skill is triggered by matching intent and drives AgiFlow via its MCP tools.

**Usage**:

- `/agiflow:backlog-grooming` - Groom the planning backlog
- `/agiflow:backlog-grooming <tag-filter>` - Groom tasks with specific tags

**Examples**:

- `/agiflow:backlog-grooming` (review all planning tasks)
- `/agiflow:backlog-grooming feature:auth` (groom auth-related tasks only)

---

**Purpose**
Prioritize tasks from "Planning" to "Todo", group them into work units, and validate readiness for execution. This is the **ONLY** skill that moves tasks from Planning to Todo — no other workflow should bypass this gate.

**Guardrails**

- ONLY operate on tasks in "Planning" status
- REFUSE to promote tasks that lack acceptance criteria (minimum 2) — suggest `refine-task` first
- REFUSE to promote tasks with vague descriptions — suggest `refine-task` first
- Work units are created ONLY during this skill (not during project-plan or run-work)
- All promoted tasks must have a clear "done" definition
- Work-unit dependencies must be explicit at the **work unit level**, not hidden inside mixed task groupings
- If a task can ship independently, it MUST live in its own standalone path or its own work unit; do NOT mix it into a downstream dependent work unit

---

## AgiFlow Project Management Guidelines

Follow the shared AgiFlow project-management guidelines in [`references/agiflow-agents.md`](../../references/agiflow-agents.md) — agent assignment, the task status workflow and transitions, work-unit best practices, and the tags strategy apply to this workflow.


---

**Steps**

## 1. Load Planning Backlog

1. Use `list_tasks` MCP tool with `status: "planning"` to load all tasks awaiting grooming.
2. Use `list_work_units` MCP tool to understand existing work unit organization.
3. Use `list_members` MCP tool to understand available agents and their capabilities.

If no tasks are in "Planning" status, report: "No tasks to groom. Use **project-plan** to create tasks first."

## 2. Assess Readiness

4. For each planning task, check:

| Criterion                          | Required?   | If missing                      |
| ---------------------------------- | ----------- | ------------------------------- |
| Has 2+ acceptance criteria         | Yes         | Flag — suggest `refine-task`    |
| Description has sufficient context | Yes         | Flag — suggest `refine-task`    |
| Priority is set                    | Yes         | Can be set during grooming      |
| Tags are applied                   | Recommended | Can be set during grooming      |
| Assignee is set                    | Optional    | Can be assigned during grooming |

5. Categorize tasks:
   - **Ready**: Meets all required criteria — can be promoted
   - **Needs refinement**: Missing acceptance criteria or vague description — suggest `refine-task`
   - **Blocked**: Has unresolved dependencies or unknowns

6. Present readiness report to user:
   - N tasks ready for promotion
   - M tasks need refinement (list them with reasons)
   - K tasks are blocked (list blockers)

Do NOT promote tasks that need refinement. The user must address them first.

## 3. Prioritize

7. For ready tasks, apply prioritization criteria:

| Factor                 | Weight       | How to assess                              |
| ---------------------- | ------------ | ------------------------------------------ |
| **Business value**     | High         | User-facing > internal tooling > tech debt |
| **Risk / uncertainty** | High         | Higher risk = do sooner to fail fast       |
| **Dependencies**       | Must respect | Blockers before dependents                 |
| **Effort vs. impact**  | Medium       | Quick wins first if equal priority         |
| **Tags**               | Grouping     | Related tags suggest natural batches       |

8. Present ranked priority list to user for confirmation:
   - Rank, title, tags, priority, estimated effort
   - Call out any dependency constraints ("Task A must come before Task B")
   - Highlight quick wins (high impact, low effort)

9. Get user confirmation on priority order before promoting.

## 4. Group into Work Units

10. Analyze ready tasks and identify cohesive groups:

### GROUP INTO WORK UNIT when:

- 3-8 related tasks that deliver a single cohesive feature
- Tasks share the same tag prefix (e.g. all `feature:auth` tasks)
- Tasks can be completed in ONE agent session (2-4 hours)
- Tasks have clear dependencies and should be executed together
- All tasks in the work unit share the same upstream dependency story and can merge back to `main` together

### DO NOT CREATE WORK UNIT when:

- Only 1-2 tasks (leave as standalone)
- Unrelated tasks (bugs across different areas)
- Maintenance work (dependency updates, config changes)
- More than 8 tasks (split into multiple work units)
- Some tasks are independently executable now, but others are blocked on upstream work — split them into separate work units or leave the smaller independent slice standalone

11. Use `batch_create_work_units` MCP tool to create all work units at once. Each work unit should have:

- **title**: Clear feature name (e.g., "Authentication Feature")
- **type**: "feature" (most common), "epic" (multi-feature), "initiative" (business goals)
- **description**: What this work unit delivers and why
- **status**: "planning"
- **priority**: Based on business impact
- **estimatedEffort**: Story points (Fibonacci: 1, 2, 3, 5, 8, 13)
- **taskIds**: List of task IDs belonging to this work unit
- **devInfo**: Include `executionPlan` describing implementation order

Leave standalone tasks (1-2 tasks) ungrouped — they can be executed individually via `run-task`.

## 5. Cross-Work-Unit Dependency Analysis

**Before promoting ANY tasks, you MUST analyze dependencies across ALL work units — not just the ones you're creating now.**
**CRITICAL:** Work units merge back to `main` only after the work unit completes. Because of that, dependency management must be explicit at the work-unit level. Do NOT create a work unit that contains both:

- tasks that can start immediately, and
- tasks that depend on another work unit being completed and merged.

If you find mixed readiness inside a proposed work unit, split it into:

- an independent standalone task or parallel work unit, and
- a downstream dependent work unit that stays in `Planning` until its upstream work units are completed and merged.

12. **Load full WU context**: Use `list_work_units` to retrieve ALL existing work units in `planning`, `in_progress`, or `review` status. You need the complete picture, not just the new WUs.

13. **Identify cross-WU touchpoints**: For each new work unit, check if it shares any of the following with existing or other new WUs:
    - **Shared files/modules**: Two WUs modifying the same source files (high merge conflict risk)
    - **API contracts**: A WU producing an API that another WU consumes
    - **Shared schemas**: Database migrations or model changes that other WUs depend on
    - **Shared UI components**: A WU creating components another WU needs to use

14. **Determine execution order across WUs**:

    | Relationship                                       | Rule                                      |
    | -------------------------------------------------- | ----------------------------------------- |
    | WU-B consumes API/schema/component created by WU-A | WU-A must finish first (upstream)         |
    | WU-A and WU-B modify the same core files           | Run sequentially — do NOT run in parallel |
    | WU-A and WU-B are fully independent                | Can run in parallel                       |

    **Merge-aware rule:** if WU-B needs code from WU-A to exist on `main`, then WU-B is downstream even if one or two tasks inside it look independently executable. Split those tasks out rather than keeping a mixed WU.

15. **Annotate dependencies in WU descriptions**: For any downstream WU, add to its description:

    ```
    **Depends on:** [WU slug/title] — [reason: e.g., "needs the user API endpoints from WU-A"]
    **Cannot start until:** [WU slug] is "completed" and merged back to `main`
    **Merge rule:** this work unit must not be dispatched until all upstream dependencies are merged
    ```

16. **Apply sequential gating**:
    - **Upstream WUs** (no dependencies): Promote their tasks to "Todo" normally
    - **Downstream WUs** (depend on upstream): Keep all of their tasks in "Planning" — do NOT promote any of them to "Todo" yet
    - **Mixed readiness discovered inside one proposed WU**: do NOT promote only the independent tasks while leaving the rest behind. Split the work into separate WUs or leave the independent slice standalone, then promote only the standalone/upstream unit.

    **Promotion rule**: REFUSE to promote tasks that depend on work from an upstream WU that is not yet "completed" and merged. The merge train must be respected.

17. Present the cross-WU execution plan to the user:
    ```
    Work Unit Execution Order:
    1. [WU-A slug] — no dependencies, can start immediately
    2. [WU-B slug] — no dependencies, can run in parallel with WU-A
    3. [WU-C slug] — depends on WU-A and WU-B being completed and merged; all tasks held in Planning
    ```

## 6. Promote Tasks: Planning -> Todo

18. For each approved task (in priority order), respecting the gating rules from Step 5:

- Use `update_task` MCP tool with `status: "todo"`
- Set `position` for ordering within the Todo column (lower = higher priority)
- Assign agent if not already assigned
- Respect dependency order: prerequisite tasks get lower position numbers
- **Do NOT promote tasks that are gated by an upstream work unit that is not yet completed and merged**

This is the **ONLY** path from Planning to Todo. No other skill should bypass this.

## 7. Verify

19. Use `list_tasks` with `status: "todo"` to confirm all promotions.
20. Use `list_work_units` to confirm groupings are correct.
21. Present summary to user:

- N tasks promoted from Planning to Todo
- M work units created (with task counts)
- K tasks left in Planning (need refinement)
- J tasks held in Planning (gated by upstream WU dependencies and merge order)
- Cross-WU execution order
- Dependency order and execution sequence
- Agent assignments

22. Recommend next steps:

- "Use **run-work** to execute a work unit (implements all its tasks sequentially)."
- "Use **run-task** to execute standalone tasks individually."
- "Use **orchestrate** for automated priority-based task dispatch."
- If downstream WUs are gated: "After [upstream WU] completes and is merged to `main`, run **backlog-grooming** again to promote the held tasks."

---

**Common Mistakes to Avoid**

- Promoting tasks without acceptance criteria (quality gate violation)
- Creating work units with >8 tasks (too complex for one session)
- Grouping unrelated tasks into one work unit (not cohesive)
- Skipping user confirmation on priority order
- Not respecting dependency ordering when setting positions
- Promoting blocked tasks (resolve blockers first)
- Creating work units during project-plan (that's this skill's job)
- Promoting dependent WU tasks while the upstream WU is still in progress (causes merge conflicts)
- Creating WUs in isolation without checking existing WUs for shared file/module touchpoints
- Mixing independent and downstream-dependent tasks inside one work unit when work units only merge at completion
- Promoting a subset of tasks from a downstream-dependent work unit instead of splitting that work into separate merge-safe units
- Not annotating cross-WU dependencies in WU descriptions (next grooming session loses context)
