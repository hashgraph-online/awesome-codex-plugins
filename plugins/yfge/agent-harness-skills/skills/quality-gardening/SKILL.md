---
name: quality-gardening
description: Use when designing quality snapshots, generated quality reports, structural metrics, debt thresholds, regression budgets, quality gates, or gradual cleanup loops.
---

# Quality Gardening

## Overview

Track quality as concrete metrics and debt movement, not as a vague single score.

This skill freezes new degradation first, then uses generated metrics to show current quality and convergence direction. For shared harness terms, see `../../references/harness-patterns.md`; when quality surfaces are absent, use `references/build-when-missing.md`. For generated snapshot ownership, see `references/generated-snapshot-ownership.md`.

## When To Use

- The user asks to design, evaluate, or maintain `QUALITY_SCORE.md`, quality reports, quality snapshots, debt reduction, or red lines.
- A repository needs structural metrics beyond lint and tests.
- The team needs periodic gardening instead of a one-time large refactor.

## Inputs Needed

- Current quality pain points: large files, scattered events, direct API calls, duplicated entrypoints, missing tests, or similar risks.
- Source paths to scan and paths to exclude.
- CI or scheduled run strategy.

## Execution Order

- First: Find existing quality docs, generated reports, lint checks, and baselines.
- Then: Choose a small set of trackable metrics and thresholds; do not create a fake aggregate score.
- Finally: Output the quality report shape, gate policy, and convergence cadence.

## Step-by-Step Process

1. Search for `QUALITY_SCORE.md`, quality scripts, baselines, and CI gardening workflows.
2. Choose four to eight metrics, and make each one automatically collectable.
3. If no quality report exists, bootstrap the minimum score/report/baseline set from `references/build-when-missing.md`.
4. Separate blocking gates from informational reports.
5. Use thresholds or baselines for historical problems; new degradation should fail.
6. Generate Markdown for humans and JSON for scripts and trends.
7. Design a gardening cadence: lower one threshold or close one allowlist item at a time.

## Checks

- Metrics: each metric is repeatable and reflects a real structural risk.
- Thresholds: checks freeze new degradation instead of demanding immediate full cleanup.
- Reports: each finding includes path, metric, current value, threshold, and suggested action.
- CI: it is clear which metrics fail builds and which only report.
- Incentives: do not hide critical risks behind one attractive total score.

## Output Format

```markdown
# Quality Gardening

## Detected Mapping
- quality:
- validation:
- work-state:

## Metrics
| Metric | Source | Threshold | Gate |
| --- | --- | --- | --- |

## Generated Reports
-

## Baseline Policy
-

## Garden Loop
-

## Non-Goals
-
```

## Common Mistakes

- Inventing a good-looking total score that does not guide repairs.
- Tracking too many metrics, so nobody reads or fixes them.
- Skipping baselines, which makes the quality gate unusable on day one.
- Treating one large refactor as quality governance.

## Example Prompts

- "Design QUALITY_SCORE.md and a quality report for this repo."
- "How should we track structural debt without inventing a fake score?"
- "Add historical large files and scattered calls to a quality garden."
