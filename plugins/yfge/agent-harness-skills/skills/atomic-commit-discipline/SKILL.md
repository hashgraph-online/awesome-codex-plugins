---
name: atomic-commit-discipline
description: Use when splitting changes into atomic commits, preparing commits from mixed worktrees, staging exact paths, including related task-state updates, writing Conventional Commits, or preventing unrelated changes.
---

# Atomic Commit Discipline

## Overview

Turn completed work into small, reviewable commits with scoped validation, related task-state updates, and no unrelated files.

This skill is not a review template or ledger template. It focuses on minimal commits, exact staged paths, task-state coupling, validation, and commit messages. For shared harness terms, see `../../references/harness-patterns.md`; when commit rules are absent, use `references/build-when-missing.md`. For delivery artifact evidence, see `references/delivery-artifact-checklist.md`.

## When To Use

- The user asks to commit, split commits, stage exact paths, or avoid unrelated changes.
- You are preparing a commit and need to inspect `git status` or diffs to avoid unrelated work.
- The worktree has multiple changes and you need to decide which belong in the same logical commit.
- A tracked task is completed, changed, or invalidated and its task-state update must travel with the related commit.
- The project requires Conventional Commits or a ledger entry paired with each commit.

## Inputs Needed

- Current `git status`, `git diff`, and `git diff --cached`.
- User goal and completed validation.
- Current task-state surface, such as `tasks.md`, `docs/tasks.md`, or the repository's issue tracker reference.
- Repository commit rules and whether ledger entries must be committed together.

## Execution Order

- First: Read `git status` and relevant diffs to identify your changes and unrelated changes.
- Then: Split staged paths by one logical behavior per commit, include related task-state updates, and run the minimum relevant validation.
- Finally: Write a Conventional Commit message, commit, and re-check status and commit contents.

## Step-by-Step Process

1. Run `git status --short --branch` and list all tracked and untracked changes.
2. Read `git diff -- <path>` for every file you intend to commit; do not commit changes you do not understand.
3. If no commit discipline is documented, bootstrap the minimum grouping and validation checklist from `references/build-when-missing.md`.
4. Identify whether the change completes, changes, or invalidates a tracked task; if yes, include the corresponding task-state update in the same logical commit.
5. Group by logical boundary: docs, tests, implementation, harness, ledger, and task state should not be mixed unless they describe the same logical change or repository rules require the same commit.
6. Run the smallest validation command that matches each group; fix failures before committing.
7. Use `git add <exact paths>`; avoid `git add .` unless the whole worktree contains only this change.
8. Write a Conventional Commit subject, and use the body for validation, skip reasons, task IDs, or linked artifacts when needed.
9. After committing, run `git show --stat --oneline HEAD` and `git status --short`.

## Checks

- Scope: each commit has one logical purpose.
- Ownership: no user-owned changes or temporary generated files are included by accident.
- Task coupling: task-state updates are present when the commit fulfills, changes, or invalidates a tracked task; unrelated task churn is absent.
- Validation: the commit has matching pre-commit validation.
- Message: the subject describes behavior, not "update files."
- Ledger: if the repository requires `agent_chats` in the same commit, it is staged with the change.

## Output Format

```markdown
# Atomic Commit Plan

## Detected Mapping
- work-state:
- ledger:
- validation:

## Worktree State
-

## Commit Groups
1. Subject:
   Paths:
   Task-state updates:
   Validation:

## Excluded Changes
-

## Final Checks
- First:
- Then:
- Finally:
```

## Common Mistakes

- Using `git add .` and bringing unrelated files into the commit.
- Mixing features, formatting, docs, refactors, and temporary fixes in one commit.
- Splitting a completed task's status update into a later unrelated commit.
- Committing before reading the diff.
- Writing commit messages such as "fix" or "update."
- Committing after validation fails.

## Example Prompts

- "Split these changes into atomic commits."
- "Commit only the harness docs and leave unrelated files unstaged."
- "Check git status and commit by logical group, including related task updates."
