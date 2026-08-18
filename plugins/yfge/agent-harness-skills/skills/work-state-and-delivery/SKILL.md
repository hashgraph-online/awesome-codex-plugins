---
name: work-state-and-delivery
description: Use when designing or reconciling design docs, task boards, external trackers, execution plans, delivery records, handoffs, review evidence, task-to-change traceability, or repository commit-coupling policy.
---

# Work State And Delivery

## Overview

Keep intent, current work state, acceptance criteria, and delivery evidence connected without creating duplicate sources of truth.

This optional governance skill combines planning surfaces and delivery ledgers because they meet at task-to-change traceability. It also owns repository commit-coupling policy, but it should not load for an ordinary commit that already follows clear repository rules. For shared harness terms, see `../../references/harness-patterns.md`; when governance surfaces are missing, use `references/build-when-missing.md`; for delivery, skip, artifact, and commit rules, use `references/delivery-and-commit-policy.md`.

## When To Use

- The user asks where requirements, design decisions, tasks, acceptance criteria, or execution plans should live.
- A repository needs a task board, external-tracker mapping, delivery record, handoff note, or review evidence policy.
- Design docs, task state, ledgers, reviews, and commits duplicate or contradict each other.
- The user asks to design commit coupling, exact-path staging, task-state updates, or delivery-artifact policy for the repository.

Do not use this skill solely for `git status`, a read-only diff, or a normal commit when the repository already defines those rules.

## Inputs Needed

- Current requirement or delivery goal.
- Existing design docs, issue tracker or task file, execution plans, review template, ledger, and commit policy.
- Validation results, artifact references, task IDs, commits, risks, and required audit level.

## Execution Order

- First: Map existing design, work-state, execution-plan, ledger, review, and commit-policy surfaces.
- Then: Assign one owner for each kind of truth and define update, coupling, skip, and redaction rules.
- Finally: Output the minimum governance changes, acceptance criteria, and delivery evidence required for the repository profile.

## Step-by-Step Process

1. Search for design docs, `tasks.md`, issue references, execution plans, review templates, ledgers, release notes, and commit guidance.
2. Map each existing surface by responsibility rather than filename: design explains why and how; work state owns current status and acceptance; an execution plan coordinates complex work; delivery evidence records what changed and what was proved.
3. If a required role is missing, bootstrap only the minimum surface from `references/build-when-missing.md`; do not add a ledger or repo-local task file when an external system already satisfies the role.
4. Define update order: design decision first, work-state and acceptance second, execution-plan status third, delivery evidence after validation.
5. When a change completes, changes, or invalidates a tracked task, include its task-state update in the same logical commit or authoritative external-tracker update.
6. Define exact-path staging, validation evidence, artifact identity, and explicit skip rules in repository guidance; avoid a standalone commit skill for routine execution.
7. Keep delivery records concise and evidence-oriented; reference prompts or goals, changes, validation, artifacts, risks, tasks, reviews, and commits without storing private transcripts.

## Checks

- Ownership: each conclusion, status, and delivery claim has one authoritative surface.
- Acceptance: active tasks have executable acceptance criteria.
- Coupling: relevant task-state and delivery updates travel with the logical change or authoritative tracker update.
- Scope: exact-path staging and one-logical-purpose commits prevent unrelated work from entering delivery.
- Evidence: delivery claims match commands and artifacts that actually exist.
- Privacy: records omit secrets, private transcripts, sensitive payloads, and large temporary artifacts.
- Overhead: optional ledgers, local task files, and execution plans are not added without a repository need.

## Output Format

```markdown
# Work State And Delivery

## Detected Mapping
- design source:
- work-state:
- execution plan:
- ledger / review:
- commit policy:
- validation / artifacts:

## Source-Of-Truth Responsibilities
-

## Update And Commit Coupling
-

## Acceptance Criteria
-

## Delivery Evidence
-

## Skip / Redaction Policy
-
```

## Common Mistakes

- Creating `tasks.md` when a reliable external tracker already owns work state.
- Letting a ledger replace task status or acceptance criteria.
- Writing diaries instead of concise validation and risk evidence.
- Requiring every small commit to create task, plan, and ledger churn.
- Using `git add .` in a mixed worktree or recording delivery claims without proof.

## Example Prompts

- "Should this requirement live in a design doc, issue tracker, or execution plan?"
- "Unify our task state, review evidence, and handoff policy."
- "Define how tracked task updates and delivery artifacts should couple to commits."
