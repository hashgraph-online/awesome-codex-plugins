# Optimize Experiment Sensitivity Workflow

Create a revised experiment design that improves signal without losing the
decision the test must answer.

## When to Use

- The test requires too much traffic or duration.
- The metric is noisy, broad, or slow-moving.
- Multiple variants make the sample-size requirement unrealistic.
- The team is considering capping, CUPED, stratification, or covariate adjustment.

## Prerequisites

- Experiment decision and current brief.
- Candidate metrics and baselines.
- Traffic or duration constraint.
- Available historical or pre-experiment data, if any.

**Reference**: `references/core/rules.md`

## Workflow Steps

### Step 1: Reconfirm The Decision

**Goal**: Avoid optimizing the wrong measurement problem.

- [ ] Write the decision the test must support.
- [ ] Define the smallest effect that would change the decision.
- [ ] Identify whether the test is exploratory, derisking, or launch-critical.

### Step 2: Inspect The Metric

**Goal**: Find a metric closer to the expected mechanism.

- [ ] Check whether the primary metric moves only after many downstream events.
- [ ] Identify a feature-level or behavior-level metric if appropriate.
- [ ] Keep guardrails for downstream business or user risk.

### Step 3: Reduce Design Waste

**Goal**: Remove avoidable traffic requirements.

- [ ] Remove variants that do not answer a distinct decision.
- [ ] Use offline or qualitative screening before live testing when possible.
- [ ] Split exploratory learning from launch validation.

### Step 4: Consider Variance Reduction

**Goal**: Improve precision without changing the meaning of the result.

- [ ] Use capping when extreme values dominate a metric.
- [ ] Use CUPED or covariate adjustment only when appropriate historical data exists.
- [ ] Use stratification when key groups differ predictably and can be assigned cleanly.

### Step 5: Record Tradeoffs

**Goal**: Make limitations visible before the test runs.

- [ ] Explain how each change affects interpretation.
- [ ] Name data prerequisites and validation checks.
- [ ] Update the experiment brief with metric and analysis changes.

## Quick Checklist

```text
[ ] Decision and meaningful effect restated
[ ] Metric is close to the feature mechanism
[ ] Extra variants removed or justified
[ ] Variance reduction technique selected only with prerequisites
[ ] Guardrails preserved
[ ] Interpretation limits documented
```

## Exit Criteria

The revised design is ready when it reduces traffic, duration, or noise while
still answering the original product decision with interpretable evidence.
