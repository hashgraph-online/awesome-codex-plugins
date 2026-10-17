---
name: plan-kanban-tasks
description: Create a concise Product Development Requirement and one or more implementation-sized Kanban tasks when the user explicitly asks to plan or register work.
argument-hint: "[Required Features] [Constraints] [Acceptance Criteria]"
enable-shell-directives: true
---

# Plan Kanban work

1. Read the project instructions and relevant product code from the integration or feature worktree. Read existing task/spec metadata through the canonical controller; do not assume `.juno_task/plan.md` exists.
2. Produce one concise PDR covering the goal, current behavior, scope, exclusions, risks, dependencies, acceptance criteria, and focused tests.
3. Split only when pieces can be implemented and validated independently. Concurrent tasks must have explicit path ownership and dependencies.
4. Create tasks through the controller's `.juno_task/scripts/kanban.sh`. Put durable requirements and acceptance criteria in each task body; relate follow-ups instead of reopening archived IDs.
5. Store any durable specification through a controller-authorized metadata operation. Never create controller-private `.juno_task/specs`, tasks, ledger, state, or receipts inside a product or feature worktree.
6. Do not start implementation, create worktrees, push, deploy, or mutate production unless the user separately asks.

Use `--id`, not legacy `--ID`, for Kanban mutations. Return the task IDs and a short dependency/order summary.

$ARGUMENTS
