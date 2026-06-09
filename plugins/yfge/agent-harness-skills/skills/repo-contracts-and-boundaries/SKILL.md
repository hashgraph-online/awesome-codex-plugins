---
name: repo-contracts-and-boundaries
description: Use when turning architecture, layering, directory ownership, dependency direction, file-size limits, choke points, baselines, or allowlists into repository checks.
---

# Repo Contracts And Boundaries

## Overview

Convert architectural intent into checks that prevent new drift instead of relying on repeated prose warnings.

This skill freezes new violations first and then supports gradual baseline reduction. For shared harness terms, see `../../references/harness-patterns.md`; when contract files are absent, use `references/build-when-missing.md`. For schema, fixture, and golden-payload contracts, see `references/schema-fixture-contracts.md`.

## When To Use

- The user mentions architecture boundaries, directory ownership, choke points, allowlists, baselines, or contracts.
- The repository has layering rules, but agents still add bypass calls or wrong dependencies.
- You need to distinguish diff checks from full audit checks.

## Inputs Needed

- Architecture docs or expected layering.
- Current directory structure and known historical debt.
- Rules to protect: dependency direction, file size, public entrypoints, data access, interface boundaries, or similar constraints.

## Execution Order

- First: Read architecture docs and current code to identify real boundaries and known debt.
- Then: Design diff checks, audit checks, baselines, and allowlists.
- Finally: Output executable contract rules and a gradual convergence strategy.

## Step-by-Step Process

1. Search for `ARCHITECTURE.md`, contract docs, lint scripts, baseline files, and allowlists.
2. List protected rules; each rule must be checkable by script or review.
3. If architecture or contract surfaces are missing, bootstrap the minimum files and checker shape from `references/build-when-missing.md`.
4. Separate new drift from historical debt: new drift should fail, historical debt should enter a baseline.
5. Design `--mode diff` for changed files and `--mode audit` for full-repository reports.
6. For each violation, output path, rule, reason, and suggested direction.
7. Define when allowlists may change and what repayment note is required.

## Checks

- Mechanical: each rule can be checked by AST, regex, import graph, path scan, or report script.
- Baseline: historical debt is explicit and not hidden by a fake green state.
- Diff: new changes can be blocked cheaply.
- Exception: allowlist entries have owner, reason, and convergence plan.
- Overbuild: do not use a complex platform when a clear script is enough.

## Output Format

```markdown
# Repo Contracts And Boundaries

## Detected Mapping
- architecture:
- contracts:
- validation:

## Protected Boundaries
-

## Diff Checks
-

## Audit Checks
-

## Baseline / Allowlist Policy
-

## Failure Message Shape
-

## Rollout Plan
-
```

## Common Mistakes

- Skipping baselines, which makes checks permanently red because of historical debt.
- Running audit only, which still lets agents introduce new drift.
- Treating architecture advice as a rule when it cannot be mechanically checked.
- Writing failure messages that do not tell an agent how to fix the violation.

## Example Prompts

- "Turn this project's architecture boundaries into checks."
- "Design a diff/audit contract checker for this repo."
- "How should we freeze new dependencies on these historical choke points?"
