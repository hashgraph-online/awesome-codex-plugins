---
name: engineering-loop
description: "Implement a repository code or configuration change through reproduction, focused checks, review, and evidence. Use for end-to-end features and fixes; not for explanation-only, review-only, research, content publishing, or production operations."
---

# Engineering Loop

Deliver a verified change with minimal supervision and proportionate checking.
Start with one agent. Delegate only when authorized and independent work or
review coverage justifies the overhead. Follow applicable repository and team
requirements; this skill adds no ticketing or mandatory-agent process.

## Establish the baseline

1. Read applicable `AGENTS.md` files and repository documentation.
2. Record the requested behavior, constraints, and observable done conditions.
3. Inspect the branch and working tree; preserve unrelated user-owned changes.
4. Before changing shared behavior, trace affected callers, consumers, and tests
   using targeted search or an available code graph. Expand along relevant paths.
5. Identify repository-native validation and run the smallest safe baseline
   that separates pre-existing failures from task regressions.

Resolve routine choices from evidence. Ask only for missing authority or a
material decision: ambiguous acceptance, incompatible public behavior, or
destructive/data-changing side effects not already authorized. Continue
independent authorized work while awaiting an answer.

Load only the needed reference:

- Long, cross-stack, or high-risk work: [loop-contract.md](references/loop-contract.md).
- Repeated iterations or explicit budgets: [loop-policy.md](references/loop-policy.md).
- Intermittent, performance, or unresolved defects: [hard-debugging.md](references/hard-debugging.md).
- Requested or risk-justified separate review: [independent-review.md](references/independent-review.md).

## Run the loop

1. Reproduce the defect, or capture the current behavior for a feature.
2. Choose the smallest coherent change and the evidence that will prove it.
3. Add a failing regression test first when practical.
4. Implement one bounded change and run the narrowest relevant check.
5. If an unplanned path is necessary, record why and update the scope and checks.
6. Classify failures as product, test, environment, assumption, or external
   blocker. Do not change product code to mask environment failures.
7. Run affected consumer checks and repository-required broader checks.
8. Review the complete diff first for task-contract compliance, then for code
   quality, regressions, security, and maintainability.
9. Fix consequential findings and rerun checks affected by those fixes.

Once acceptance evidence and required checks pass, broaden or repeat checks
only for new changes, failures, or unresolved concerns. Add tests when they
prove behavior or a meaningful invariant, not merely mirror a low-impact edit.

If no test harness exists, use a small repeatable script or documented manual
check with inputs, expected behavior, and observed results. Record missing
automated coverage; a build alone does not prove runtime behavior. Do not add
a large testing framework solely to satisfy the loop.

Keep a compact ledger of facts, changed files, commands, outcomes, and the next
decision instead of full logs.

## Stop conditions

- After two identical failures, stop blind retries and reclassify the cause.
  Resume only with changed relevant state or an evidence-producing probe.
- If discovery or review repeats without new evidence, checkpoint the diff,
  unresolved issue, and next useful probe. Do not restart the same cycle.
- Stop and report a blocker when progress requires missing authority, secrets,
  unavailable infrastructure, an unauthorized destructive action, or an
  unresolved material product decision.
- When an explicit loop budget is exhausted, stop with the latest judge
  evidence instead of silently expanding the budget.
  Without an explicit budget, continue only while a bounded next action can
  produce new evidence; productive iterations have no arbitrary fixed count.
- Never make a failing check pass by weakening assertions, deleting coverage,
  hiding errors, or silently changing acceptance criteria.
- Do not query production, deploy, migrate, merge, or publish unless the user
  explicitly authorizes that action.

## Finish with evidence

Report changed behavior and files, regression or acceptance proof, exact check
commands and outcomes, review disposition, and remaining limitations. Include
the final reviewed revision when independent review was used. Never label
blocked validation or unresolved consequential findings as complete.
See [evidence-example.md](references/evidence-example.md) for a filled-in handoff.
