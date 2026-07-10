---
name: krypton-execution
description: Use when executing an approved Krypton plan, GOAL.md, or implementation plan that already defines intent, ownership, contract, cutover, task boundaries, and acceptance evidence. Use for main-agent execution with explorer, plan-reviewer, reviewer, maintainer, or verifier gates.
---

# Krypton Execution

Krypton Execution runs an approved plan without drifting from its ownership, cutover, and evidence contract.

## Required Roles

Use the role expectations in `../../docs/required-roles.md` when the harness supports named agents. Implementation stays with the main agent. The normal execution stack is:

```text
explorer -> main agent -> plan-reviewer -> reviewer -> maintainer -> verifier
```

Use the individual prompt templates in this skill folder:

- `post-plan-reviewer-prompt.md`
- `reviewer-prompt.md`
- `maintainer-prompt.md`

## Entry Rule

Do not invent the plan inside this workflow. If no approved plan, goal document, or clear task board exists, ask for one direct input or use Krypton Planning first. Prefer a full Krypton goal package:

```text
docs/goals/<goal-slug>/PLAN.md
docs/goals/<goal-slug>/GOAL.md
docs/goals/<goal-slug>/EVIDENCE.md
```

Before work starts, restate:

```text
Goal:
Plan path:
Intent:
Truth owner:
Contract boundary:
Cutover:
Displaced path:
Acceptance evidence:
Kill criteria:
Forbidden moves:
```

## Task Board

Turn the plan into an ordered board:

```text
Task:
Owner:
Input:
Files allowed:
Files forbidden:
Output:
Evidence:
Depends on:
Parallel safe:
```

Run implementation tasks sequentially in the main agent unless the approved plan explicitly says otherwise.

## Execution Loop

For each task:

1. Confirm the task still matches the plan contract.
2. Gather only the context needed for the task.
3. Implement directly in the main agent.
4. Review the result before integration or checkpoint.
5. Check for wrong owner, duplicate path, missing cutover, contract drift, and weak proof.
6. Commit or checkpoint only the current task files when the local workflow expects commits.
7. Update the task board.

The main agent owns implementation, integration, and final coherence.

## Evidence Gate

Do not call the goal complete because tests, lint, typecheck, or diffs passed. Those are supporting checks.

Completion requires target-perspective evidence, such as:

- UI or visual change: browser state, screenshot, or rendered output.
- API or data flow: request/response, fixture, trace, or persisted record.
- CLI or workflow: command plus important output proving the behavior.
- Migration or cutover: old path deleted, redirected, demoted, or shimmed with a removal trigger.
- Hidden logic: deterministic artifact showing the intended result.

If evidence cannot be captured, report the blocker and say `implemented but unproven`.

Record the accepted evidence in `EVIDENCE.md` before the final response when the repo uses Krypton goal packages.

## Final Gates

Before final response:

1. Run POST plan review when the plan had a review gate.
2. Run correctness review for behavior, data integrity, trust, and missing evidence.
3. Run maintainability review for duplicate paths, stale artifacts, coupling, and unclear ownership.
4. Fix important findings or record why they remain.
5. Summarize changed artifacts, acceptance evidence, review result, and blockers.
