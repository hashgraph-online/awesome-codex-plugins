---
name: repo-contracts-and-boundaries
description: Use when turning architecture, layering, ownership, dependency direction, schemas, structural metrics, quality thresholds, baselines, allowlists, or generated quality snapshots into repository checks.
---

# Repo Contracts And Boundaries

## Overview

Convert architectural and structural-quality intent into checks that prevent new drift instead of relying on repeated prose warnings.

This skill owns both repository contracts and quality gardening because both use the same mechanism: collectible rules, diff gates, audit reports, baselines, and gradual debt reduction. For shared harness terms, see `../../references/harness-patterns.md`; when contract files are absent, use `references/build-when-missing.md`; for schema, fixture, and golden-payload contracts, see `references/schema-fixture-contracts.md`; for metrics and generated snapshots, see `references/quality-policy.md`.

## When To Use

- The user asks to define, protect, audit, or encode architecture boundaries, directory ownership, choke points, allowlists, baselines, or contracts.
- The repository has layering rules, but agents still add bypass calls or wrong dependencies.
- The user asks for structural metrics, quality reports, debt thresholds, regression budgets, or a gradual cleanup loop.
- You need to distinguish diff checks from full audit checks.

## Inputs Needed

- Architecture docs or expected layering.
- Current directory structure and known historical debt.
- Rules to protect: dependency direction, file size, public entrypoints, data access, interface boundaries, or similar constraints.
- Existing quality reports, generated snapshots, and CI or scheduled-run policy.

## Execution Order

- First: Read architecture docs, current code, existing checks, reports, and baselines to identify real boundaries and debt.
- Then: Design mechanical rules, collectible metrics, diff checks, audit reports, baselines, and allowlists.
- Finally: Output executable contracts, generated evidence, and a gradual convergence strategy.

## Step-by-Step Process

1. Search for `ARCHITECTURE.md`, contract docs, lint scripts, baseline files, and allowlists.
2. List protected rules; each rule must be checkable by script or review.
3. If architecture or contract surfaces are missing, bootstrap the minimum files and checker shape from `references/build-when-missing.md`.
4. Separate new drift from historical debt: new drift should fail, historical debt should enter a baseline.
5. Add only metrics tied to a concrete structural risk; keep them automatically collectible and avoid aggregate quality scores.
6. Design `--mode diff` for changed files and `--mode audit` for full-repository reports.
7. For each violation, output path, rule or metric, current value, threshold, reason, and suggested direction.
8. Define when baselines or allowlists may change, who owns generated snapshots, and what repayment note is required.

## Checks

- Mechanical: each rule can be checked by AST, regex, import graph, path scan, or report script.
- Baseline: historical debt is explicit and not hidden by a fake green state.
- Diff: new changes can be blocked cheaply.
- Exception: allowlist entries have owner, reason, and convergence plan.
- Metrics: every quality metric is repeatable and represents a real structural risk.
- Snapshots: generated reports name their source command and cannot silently become stale.
- Incentives: no aggregate score hides a critical finding.
- Overbuild: do not use a complex platform when a clear script is enough.

## Output Format

```markdown
# Repo Contracts And Boundaries

## Detected Mapping
- architecture:
- contracts:
- quality:
- validation:

## Protected Boundaries
-

## Diff Checks
-

## Audit Checks
-

## Baseline / Allowlist Policy
-

## Generated Reports / Snapshots
-

## Garden Loop
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
- Tracking metrics that cannot be collected repeatably.
- Publishing a polished total score that hides critical risk.
- Writing failure messages that do not tell an agent how to fix the violation.

## Example Prompts

- "Turn this project's architecture boundaries into checks."
- "Design a diff/audit contract checker for this repo."
- "How should we freeze new dependencies on these historical choke points?"
- "Track structural debt without inventing a fake quality score."
