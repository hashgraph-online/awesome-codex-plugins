# Agiflow Project Management Guidelines

## Agent Assignment Strategy

### When Creating Tasks

**CRITICAL**: Every task MUST be assigned to an appropriate agent member based on the work required.

Use `list-members` MCP tool to get available agents and their capabilities, then assign tasks appropriately based on the member's role and description.

### Agent Selection Process

1. Call `list-members` to get all available agent members
2. Review each member's role, description, and capabilities
3. Match the task requirements to the most suitable agent
4. Assign the task using the agent's member name

## Task Status Workflow

### Status Columns

1. **Planning** - Task created but not yet groomed (use `backlog-grooming` to promote)
2. **Todo** - Task groomed and ready for execution
3. **In Progress** - Actively being worked on
4. **Testing** - Implementation complete, running tests
5. **Review** - Tests passed, needs review
6. **Done** - Completed and verified
7. **Blocked** - Requires human intervention
8. **Cancelled** - Terminal state

### Status Transitions

```
Planning → Todo: ONLY via backlog-grooming (strict gate)
Todo → In Progress: Start working on task
In Progress → Testing: Implementation complete, running tests
Testing → Review: Tests passed
Testing → Todo: Tests failed (retry)
Testing → Blocked: Tests failed repeatedly
Review → Done: Review passed, task complete
Review → In Progress: Changes requested, back to development
In Progress → Blocked: Cannot proceed
Blocked → Todo: Blocker resolved
```

**IMPORTANT**: Tasks in "Planning" status are NOT ready for execution. Only `backlog-grooming` can promote them to "Todo".

## Work Unit Best Practices

1. **Feature Type for Most Work**: Use "feature" type for most work units (single cohesive capability)
2. **Epic for Large Initiatives**: Use "epic" type for large initiatives with multiple child features
3. **Limit Nesting**: Keep work unit nesting to 2 levels maximum (epic → feature)
4. **Clear Scope**: Each work unit should have a clear, deliverable outcome
5. **Organize Tasks**: Group related tasks under work units; use tags for categorization
6. **Session Completion**: Design work units that can be completed in one session (2-4 hours)
7. **Task-First Workflow**: Always create tasks FIRST, then associate with work units using taskIds

## Tags Strategy

Use the `tags` field on tasks for categorization. Format: `type:label`

**Required prefixes** (use one per task):

- `feat:` — New feature work (e.g. `feat:auth`, `feat:billing`)
- `bug:` — Bug fix (e.g. `bug:checkout`, `bug:login`)
- `chore:` — Maintenance, config, deps (e.g. `chore:deps`, `chore:ci`)
- `refactor:` — Code improvement without behavior change (e.g. `refactor:api-layer`)
- `spike:` — Research or feasibility exploration (e.g. `spike:perf`, `spike:feasibility`)

**Optional prefixes** (add for grouping):

- `epic:` — Cross-cutting initiative (e.g. `epic:onboarding`, `epic:payments`)
- `domain:` — Domain area (e.g. `domain:billing`, `domain:auth`)
- `pkg:` — Package scope in monorepo (e.g. `pkg:backend-api`, `pkg:web-app`)

**Multiple tags**: Comma-separated (e.g. `feat:auth,domain:auth,epic:onboarding`)

Tags help `backlog-grooming` group related tasks into work units and enable automated reporting (velocity by type, bug-to-feature ratio).

## Planning Best Practices

### Task Creation

- **Create tasks in "Planning" status** - Use `backlog-grooming` to promote to "Todo"
- **Always assign to an agent** - No task should be created without an assignee
- **Write clear titles** - Use action verbs (Implement, Fix, Update, Refactor)
- **Add acceptance criteria** - Define what "done" means (2-5 criteria per task)
- **Set appropriate priority** - Use high/medium/low based on impact
- **Include descriptions** - Provide context and requirements
- **Use tags for categorization** - Apply `type:label` format (e.g. `feature:auth`)
- **Order by dependencies** - Create prerequisite tasks first

### Work Unit Organization

- **3-8 tasks per work unit** - Keep work units focused and completable in one session
- **Related tasks only** - Only group tasks that deliver a cohesive feature
- **Use taskIds parameter** - Associate tasks with work units during creation
- **Leave standalone tasks alone** - Don't force 1-2 tasks into work units
- **Split large features** - Break down >8 tasks into multiple work units
