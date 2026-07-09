---
name: agent-ledger-and-delivery
description: Use when designing agent_chats or agents_chat records, delivery evidence summaries, linked tasks or commits, validation notes, risks, review notes, or handoff records.
---

# Agent Ledger And Delivery

## Overview

Define how agent work is recorded so reviewers can see prompt, intent, changes, validation, risks, and linked tasks or commits.

This skill focuses on delivery evidence and long-term traceability, not commit splitting or task-state ownership. A ledger may reference tasks and commits, but `tasks.md`, an issue tracker, or another work-state surface remains responsible for current task status and acceptance criteria. For shared harness terms, see `../../references/harness-patterns.md`; when ledger files are absent, use `references/build-when-missing.md`. For ledger coupling and skip policy, see `references/delivery-coupling.md`.

## When To Use

- The user asks to create, refactor, or evaluate `agent_chats`, `agents_chat`, review descriptions, delivery records, linked tasks, or linked commits.
- A project requires AI collaboration records for each delivery.
- Validation, risk, next steps, and artifact references need a stable format.

## Inputs Needed

- Existing ledger directory and naming rules.
- User goal, change summary, validation commands, artifacts, task IDs, reviews, or commits.
- Whether the repository requires ledger updates in the same commit.

## Execution Order

- First: Read existing ledger rules and recent examples.
- Then: Design the record schema, naming, required sections, and task/commit/review coupling.
- Finally: Output a reusable ledger template and delivery checklist.

## Step-by-Step Process

1. Search for `agent_chats`, `agents_chat`, CI checks, AGENTS rules, and review templates.
2. Confirm record granularity: per commit, per review, per session, or per milestone.
3. If no ledger convention exists, bootstrap the minimum directory and template from `references/build-when-missing.md`.
4. Define filename, frontmatter, body sections, language, and redaction rules.
5. Define when ledger updates are required, when skip is allowed, and how skip is recorded.
6. Define how review or delivery summaries reference tasks, commits, validation, artifacts, risks, and next steps.
7. Keep ledger and atomic commit rules separate: this skill defines records; `atomic-commit-discipline` defines commit splitting.
8. Keep ledger and task-state rules separate: this skill summarizes evidence; the work-state surface owns current task status.

## Checks

- Completeness: prompt, goals, changes, validation, risks, and linked tasks or commits are present.
- Coupling: code changes have a corresponding ledger or explicit skip reason.
- Boundary: ledger summaries do not replace updates to task status or acceptance criteria.
- Readability: future agents can resume from the record; it is not just "done."
- Privacy: records do not include tokens, secrets, private chat transcripts, or sensitive logs.
- Duplication: avoid two ledger formats that drift from each other.

## Output Format

```markdown
# Agent Ledger And Delivery

## Detected Mapping
- ledger:
- work-state:
- validation:

## Ledger Policy
- Directory:
- Filename:
- Required metadata:
- Required sections:

## Delivery Summary Template
-

## Task / Commit / Review Coupling
-

## Validation Evidence
-

## Skip Policy
-
```

## Common Mistakes

- Writing a diary instead of validation and risk evidence.
- Letting the review summary disagree with actual validation.
- Treating a ledger entry as a substitute for updating task state.
- Mixing atomic commit rules into the ledger skill until responsibilities overlap.
- Recording sensitive content.

## Example Prompts

- "Design an agents_chat record policy for this project."
- "Make a review evidence template for this agent-driven repo."
- "What validation, tasks, and linked commits should this delivery record include?"
