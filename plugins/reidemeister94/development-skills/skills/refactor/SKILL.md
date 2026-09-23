---
name: refactor
description: "Audit an existing project against its standards and apply selected improvements while preserving behavior."
argument-hint: "[focus]"
user-invocable: true
disable-model-invocation: true
effort: xhigh
disallowed-tools: Write Edit NotebookEdit
---

# Refactor

Bring an existing project closer to its standards without changing user-visible behavior.
This is the repository-convergence exception in the [development loop](../../shared/development-loop.md).
It can inspect the whole target but can change only an approved tranche.

`$ARGUMENTS` is a free-text focus, such as `database queries`, `src/orders`, or a planned feature.
With a focus, audit that area and its required dependencies. Without one, audit the whole project.
The audit is always read-only. The user chooses what to change afterwards.

The audit changes nothing in the target.
The frontmatter withholds write tools during the audit, but the rule holds even when the harness exposes them.

## 1. Audit

Apply the loop's Standards gate and the [engineering contract](../../shared/engineering.md).
Record the source paths you selected.

Use focused owners where their signal exists:

- `align-docs` in inspection-only mode for repository context and documentation;
- `staff-review` for code quality inside the scope.

Then inspect what these owners do not cover.
Check the data model, query access paths, batching, indexes, repeated work, held resources, retries, recomputation, and behavior with multiple owners.

Exclude generated code and dependencies.
Record inspected surfaces and gaps.
Confirm disputed library behavior in official documentation for the installed version.

Every finding includes evidence, location, [severity](../../shared/review-categories.md), expected result, impact, effort, change risk, dependencies, confidence, and required proof.

## 2. Rank

Do not invent a score.
Put security and data-loss risks before normal impact-to-effort ordering.
Severity measures defect risk. Impact over effort orders the roadmap.

Use repository history to weight code that changes often.
Group findings with one root cause into one item.
Label each item `strong`, `worth exploring`, or `speculative`. Mark estimated values as estimates.
Diagnose only. Do not design the fix yet.

## 3. Choose

Present the roadmap, then ask the user to select tranches.
Selecting none ends the work with the audit.
A tranche covers one area, has compatible dependencies, and shares one verification and rollback strategy.

A pure audit writes nothing.
Save the roadmap under `docs/plans/` only after the user selects work or explicitly asks to save it.

## 4. Converge

Run a full cycle for each tranche:

1. Use `brainstorming` and `create-test` to settle invariants, thresholds, failure cases, and rollback.
2. Capture a characterization proof that passes on unchanged code and after the refactor.
3. Write the plan and chronicle, then present the plan for approval before code changes.
4. Implement in small slices and run the nearest check after each slice.

Finish with cumulative verification, independent review, and a recalculated roadmap.
If a tranche fails proof or review, stop and report it.

Keep business changes as separate tasks.
Do not widen a tranche during implementation. Record a new finding in the roadmap.
Never commit.

## 5. Resume

The saved roadmap and any incomplete tranche plan are the persistent state.
A later run resumes them instead of repeating the audit.
