---
name: design-doc-and-task-board
description: Use when deciding how requirements should be captured in design docs, tasks.md, external task systems, exec plans, acceptance criteria, status updates, or planning source-of-truth files.
---

# Design Doc And Task Board

## Overview

Decide where intent, design, work state, and acceptance criteria should live so they do not drift.

Design docs explain why and how; a work-state surface tracks current tasks, statuses, acceptance criteria, and task-to-change traceability; exec plans describe how to execute a complex batch of changes. `tasks.md` or `docs/tasks.md` is the lightweight repo-local default when no reliable Jira, Linear, GitHub Issues, internal board, or equivalent tracker exists. For shared harness terms, see `../../references/harness-patterns.md`; when planning files are absent, use `references/build-when-missing.md`.

## When To Use

- The user asks whether a requirement belongs in a design doc, `tasks.md`, an external task system, or an exec plan.
- README, design docs, tasks, and exec plans start to duplicate or drift.
- Requirements need to become tasks, statuses, acceptance criteria, and commit-linked change records.

## Inputs Needed

- Current requirement or change goal.
- Existing task tracker or `tasks.md`, design docs, exec plans, README, and docs index.
- Change size, cross-module scope, and whether long-term tracking is needed.

## Execution Order

- First: Read existing planning and work-state sources of truth and identify how this project expresses intent and status.
- Then: Decide whether this requirement belongs in a design doc, existing task system, repo-local task board, exec plan, or combination.
- Finally: Output the doc/task sync strategy, acceptance criteria, and update order.

## Step-by-Step Process

1. Search for `tasks.md`, `PLANS.md`, `docs/design*`, `docs/exec-plans`, README, issue references, and documented external task systems.
2. Identify each file's actual responsibility; do not infer solely from names.
3. If no reliable work-state surface exists, bootstrap the minimum design/task/exec-plan set from `references/build-when-missing.md`, using `tasks.md` or `docs/tasks.md` as the repo-local default.
4. Classify by complexity: small fixes update tasks only; architecture or cross-module changes start with a design doc; multi-day batches use an exec plan.
5. Write task entries with owner, status, acceptance criteria, linked paths, and the expected commit or change reference; do not put chat notes into `tasks.md`.
6. When design changes, update the design source of truth first, then sync task state and acceptance criteria.
7. When a tracked task is completed, changed, or invalidated by a commit, include that task-state update in the same logical commit as the related change.
8. Output drift checks: one conclusion has one source of truth, and other files reference it.

## Checks

- Responsibility: design doc, work-state surface, and exec plan each have a clear role.
- Sync: task status matches current code and design decisions.
- Acceptance: every task has executable acceptance criteria.
- Granularity: tasks are small enough to verify and large enough to express user value.
- Commit coupling: task-state updates travel with the logical commit that fulfills, changes, or invalidates them.
- Pollution: `tasks.md` does not become a chat log or unordered TODO list.

## Output Format

```markdown
# Design Doc And Task Board Decision

## Detected Mapping
- design source:
- work-state:
- exec plan:

## Where This Belongs
- Design doc:
- Work-state surface:
- Exec plan:

## Update Order
- First:
- Then:
- Finally:

## Task Entries
-

## Commit Coupling
-

## Acceptance Criteria
-

## Drift Checks
-
```

## Common Mistakes

- Putting task status into a design doc where it cannot be maintained.
- Updating only the task surface while leaving the design source of truth stale.
- Completing a task in code while leaving its task-state update for a later unrelated commit.
- Opening a large exec plan for every small requirement.
- Writing tasks with no acceptance criteria, such as "improve" or "optimize."

## Example Prompts

- "Should this requirement live in a design doc, an issue tracker, or tasks.md?"
- "Turn this design into a task board and acceptance criteria."
- "Our task board and design docs have drifted; how should we converge them?"
