---
name: engineering-loop
description: "Drive an authorized repository change through a verified local loop: baseline, reproduce, implement, test, review, and report evidence. Use for end-to-end features or fixes that should continue autonomously until observable acceptance criteria pass; do not use for explanation-only, review-only, or production operations."
---

# Engineering Loop

Own the change from a verified starting point to a reviewed result. Use one
agent and this skill alone unless a specialist changes a material decision.

## Establish the baseline

1. Read applicable `AGENTS.md` files and repository documentation.
2. Record the requested behavior, constraints, and observable done conditions.
3. Inspect the branch and working tree; preserve unrelated user-owned changes.
4. Identify repository-native validation and run the smallest safe baseline
   that separates pre-existing failures from task regressions.

For a long, cross-stack, or high-risk change, use the templates and failure
rules in [references/loop-contract.md](references/loop-contract.md).
When a task is expected to need repeated autonomous iterations or has an
explicit retry, time, token, or cost limit, also use
[references/loop-policy.md](references/loop-policy.md).
When a defect is intermittent, performance-related, difficult to reproduce, or
resists the first evidence-driven pass, use
[references/hard-debugging.md](references/hard-debugging.md).

## Run the loop

1. Reproduce the defect, or capture the current behavior for a feature.
2. Choose the smallest coherent change and the evidence that will prove it.
3. Add a failing regression test first when practical.
4. Implement one bounded change and run the narrowest relevant check.
5. Pause before expanding into an unplanned subsystem, public contract,
   migration, or external system. Record why the original scope is
   insufficient and obtain any authority the expansion requires.
6. Classify failures as product, test, environment, or assumption failures;
   fix the cause and rerun the affected check.
7. Run repository-required broader checks after focused checks pass.
8. Review the complete diff first for task-contract compliance, then for code
   quality, regressions, security, and maintainability.
9. Fix consequential findings and rerun checks affected by those fixes.

Keep a compact ledger of confirmed facts, changed files, commands, outcomes,
and the next decision. Return concise diagnostics instead of full logs.

## Stop conditions

- If the same command fails twice for the same reason, stop retrying and
  re-check the environment, target, permissions, and underlying assumption.
- Stop recursive discovery when each new finding redefines the same task
  boundary. Freeze the discovered scope or return for a scope decision instead
  of repeatedly recataloging the repository.
- Stop and report a blocker when progress requires missing authority, secrets,
  unavailable infrastructure, destructive action, or a product decision.
- When an explicit loop budget is exhausted, stop with the latest judge
  evidence instead of silently expanding the budget.
- Never make a failing check pass by weakening assertions, deleting coverage,
  hiding errors, or silently changing acceptance criteria.
- Do not query production, deploy, migrate, merge, or publish unless the user
  explicitly authorizes that action.

## Finish with evidence

Report:

1. behavior implemented or defect fixed;
2. changed files and important design decisions;
3. regression proof or acceptance evidence;
4. focused and broader commands with outcomes;
5. task-contract and code-quality findings fixed or explicitly unresolved;
6. unrun checks, residual risks, and blockers.
