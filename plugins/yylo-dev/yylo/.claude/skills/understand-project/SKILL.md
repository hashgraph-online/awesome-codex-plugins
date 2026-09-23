---
name: understand-project
description: Inspect the current product architecture, dependencies, and validation loops before planning or implementing a requested change.
argument-hint: "[Main Task] [Constraints] [Ultimate Goal]"
enable-shell-directives: true
---

# Understand the project

1. Read `AGENTS.md`/`CLAUDE.md`, repository status, relevant source, tests, and existing product documentation in the integration or assigned feature worktree.
2. Read related Kanban tasks and durable specs through the canonical metadata controller. Do not assume `.juno_task/plan.md` exists and do not materialize controller-private metadata in a product worktree.
3. Trace only the dependencies and runtime paths needed for the requested goal. Use bounded parallel investigation when independent questions justify it.
4. Report current behavior, sources of truth, affected components, risks, unknowns, and the smallest useful validation loop.
5. If the user requested planning, hand the findings to `plan-kanban-tasks`. If implementation was requested, work only in the task worktree returned by `yy task start TASK_ID`.
6. Write a durable spec only when requested or materially useful, and route it to a controller-admitted location. Do not update root instructions with transient status.

## Invocation contract

The structured views below intentionally alias parts of the complete request; they are not additional user arguments.

### Main task

$1

### Constraints and context

$2

### Complete raw request

$ARGUMENTS
