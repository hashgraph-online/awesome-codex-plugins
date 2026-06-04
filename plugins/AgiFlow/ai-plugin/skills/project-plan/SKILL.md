---
name: project-plan
description: "Plan a project or feature: research context, clarify requirements, decompose into vertical slices, and create tasks in Planning status. Use when starting new work or breaking down requirements. Invoked as /agiflow:project-plan <requirements>. Uses get_project_detail, list_tasks, list_work_units, create_task, batch_create_tasks."
tags:
  - agiflow
  - mcp
  - planning
  - decomposition
metadata:
  mirrors: backend/apis/agiflow-api .../prompts/plan.md
---

> Invoked as `/agiflow:project-plan`. In hosts without slash-prompts, this skill is triggered by matching intent and drives AgiFlow via its MCP tools.

**Usage**:

- `/agiflow:project-plan <requirements or feature description>` - Plan from requirements
- `/agiflow:project-plan` - Start interactive planning session

**Examples**:

- `/agiflow:project-plan Add user notification preferences`
- `/agiflow:project-plan Integrate Stripe billing with usage-based pricing`
- `/agiflow:project-plan` (interactive discovery)

---

**Guardrails**

- Tasks are created in **"Planning"** status — NOT "Todo"
- **No work units** are created during this skill — use `backlog-grooming` for that
- Use `tags` field for categorization (e.g. `feature:auth`, `bug:checkout`, `epic:billing`)
- Favor straightforward, minimal implementations first; add complexity only when requested
- Keep task scope focused on delivering user-visible progress
- Identify vague or ambiguous details and ask follow-up questions before creating tasks

---

## AgiFlow Project Management Guidelines

Follow the shared AgiFlow project-management guidelines in [`references/agiflow-agents.md`](../../references/agiflow-agents.md) — agent assignment, the task status workflow and transitions, work-unit best practices, and the tags strategy apply to this workflow.


---

**Steps**

## 1. Research Before Planning

**Do NOT jump to task breakdown.** You must understand the product, codebase, and existing work FIRST.

1. Use `get_project_detail` MCP tool to understand the current project scope and goals.
2. Use `list_members` MCP tool to get available agent members and their capabilities.
3. Use `list_tasks` MCP tool with relevant filters to check for similar or duplicate tasks.
4. Use `list_work_units` MCP tool to check for existing work units and understand feature organization.
5. **Read the codebase**: Use available tools to explore relevant source code, existing patterns, and architecture before proposing any tasks. Understand how similar features are already implemented.
6. **Check product context**: Review project documentation, existing specs, and artifacts attached to the project. Understand the product's current state — what's built, what's planned, what's in progress.
7. **Check dependencies**: Review what other work units and tasks are in-flight. Understand what's changing in the codebase right now to avoid conflicts.

**Detect project state:**

- **Greenfield** (no existing tasks/work units): Focus on scaffolding, initial architecture, and foundational tasks. Ask about technology choices, project structure, and initial setup needs.
- **Brownfield** (existing tasks/work units): Focus on integration points, affected areas, and backward compatibility. Check for overlap with existing work and patterns to follow.

**If you lack sufficient context to plan confidently**, create `spike:investigation` tasks to investigate unknowns before creating implementation tasks. Spike tasks are time-boxed (1-2 hours) and output knowledge (file paths, patterns, recommendations), not code. Mark implementation tasks that depend on spike results in their descriptions.

## 2. Clarify Requirements

5. Identify what the user is asking for and extract:
   - **User stories**: Who benefits and what they need
   - **Feature scope**: What is included and what is explicitly excluded
   - **Constraints**: Performance, security, compatibility, deadlines
   - **Dependencies**: External services, existing features, data requirements
   - **Test scenarios**: For each acceptance criterion, what must be verified? (happy path, error paths, edge cases)

6. Ask the user follow-up questions for any ambiguities:
   - Unclear acceptance criteria
   - Missing edge cases or error handling expectations
   - Priority and urgency
   - Preferred approach if multiple options exist
   - What test types are expected (unit, integration, E2E)?

**If requirements are already clear and well-defined, skip to Step 3.**
Do NOT proceed to decomposition until scope is sufficiently clear.

## 3. Decompose

For **simple features** (fewer than 5 tasks with obvious structure), skip decomposition and proceed directly to Step 4.

For **complex features** (5+ tasks, unclear boundaries, or multiple system areas):

7. Choose a decomposition strategy:

| Question                                                    | If yes...                               | Strategy          |
| ----------------------------------------------------------- | --------------------------------------- | ----------------- |
| Does the feature have 3+ distinct user-facing capabilities? | Users interact with it in multiple ways | **Functional**    |
| Is the core complexity in the data model and relationships? | Schema design matters most              | **Data-oriented** |
| Is the feature a multi-step workflow with a clear sequence? | "First X, then Y, then Z"               | **Temporal**      |
| Not sure?                                                   | Try two strategies and compare          | **Compare**       |

8. Produce vertical slices (each must be independently buildable, testable, and demonstrable):
   - **What**: One sentence — concrete, not abstract
   - **Inputs**: Data, services, APIs needed
   - **Outputs**: What it produces — UI, API response, side effect
   - **Done when**: WHEN [action], THEN [observable result]

**Slice quality check:**

- Can this slice be demonstrated to a user? (If not, it's a horizontal slice — recut it)
- Is it completable in one agent session (2-4 hours)?
- Does it have clear boundaries (what's in vs. out)?

9. Map dependencies between slices:
   - Identify the critical path (longest chain of dependent slices)
   - Identify parallelizable work (slices with no mutual dependencies)

10. Identify the MVP subset — the smallest set of slices that delivers user-visible value. Mark MVP slices.

11. Present decomposition to user for confirmation before creating tasks. Do NOT create tasks yet.

## 4. Create Tasks in "Planning" Status

12. For each slice or requirement, create tasks using `create_task` or `batch_create_tasks` MCP tool:

- **status**: `"planning"` (strict — NOT "todo")
- **title**: Clear, action-oriented (verb-led: "Implement", "Fix", "Refactor", "Update")
- **description**: Detailed context including requirements, constraints, and references to existing patterns
- **tags**: Categorization labels (e.g. `feature:auth`, `bug:checkout`, `epic:billing`, `spike:perf`, `chore:deps`)
- **priority**: "low" | "medium" | "high" based on impact
- **acceptanceCriteria**: 2-5 concrete, verifiable completion conditions per task
- **assignee**: Appropriate agent member from `list_members` (optional — can be assigned during grooming)

**Task guidelines:**

- Tasks should be completable in 15min - 2 hours each
- Include test tasks alongside implementation tasks (e.g., "Write unit tests for registration validation")
- Each critical acceptance criterion should map to at least one test case
- Order tasks by dependencies — create prerequisite tasks first
- For each acceptance criterion, consider: happy path, error path, edge cases

**DO NOT create work units** — leave that to `backlog-grooming`.

## 5. Verify Plan

13. Use `list_tasks` to verify all tasks were created correctly in "Planning" status.
14. Review completeness:

- All feature requirements are captured in tasks
- Acceptance criteria are concrete and verifiable
- Critical acceptance criteria have corresponding test tasks
- Dependencies are documented in descriptions
- Tags are applied consistently for categorization
- Agents are assigned where possible

15. Present a summary to the user:

- Total tasks created (all in "Planning" status)
- Tasks grouped by tag (feature areas)
- Dependency order
- MVP vs. full scope (if decomposition was applied)
- Any remaining open questions or risks

16. Recommend next steps:

- "Use **refine-task** on any tasks that need more depth before grooming."
- "Use **backlog-grooming** to prioritize tasks, promote to Todo, and group into work units for execution."

---

**Common Mistakes to Avoid**

- ❌ Creating tasks in "Todo" status (must use "Planning" — grooming promotes to Todo)
- ❌ Creating work units during planning (that's backlog-grooming's job)
- ❌ Skipping requirement clarification when scope is vague
- ❌ Producing horizontal slices ("all database tables first, then all APIs") instead of vertical slices
- ❌ Over-decomposing: 20 tiny slices when 5 well-scoped ones would do
- ❌ Under-decomposing: 2 giant slices that each take a week
- ❌ Tasks without tags (makes grooming harder)
- ❌ Acceptance criteria that say "should work correctly" (what does "correctly" mean?)
- ❌ Tasks taking >2 hours (they need further decomposition)
- ❌ Planning for 3 months of work (plan the next 2-4 weeks)
