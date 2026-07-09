# Prepare Results Readout Workflow

Prepare an A/B test results report that supports a product decision.

## When to Use

- An experiment has finished or reached a planned checkpoint.
- Stakeholders need a launch, stop, iterate, or investigate recommendation.
- Results are flat, mixed, surprising, or segment-sensitive.

## Prerequisites

- Experiment brief or configuration.
- Variant assignment and exposure data.
- Primary and guardrail metric data.
- Baselines or expected ranges.

**Reference**: `references/core/rules.md`

## Workflow Steps

### Step 1: Reconstruct Context

**Goal**: Prevent analysis detached from the original design.

- [ ] Restate hypothesis.
- [ ] Record run window.
- [ ] Record population, eligibility, and exposure event.
- [ ] Record control and test definitions.
- [ ] Record primary and guardrail metrics.

### Step 2: Validate Data

**Goal**: Know whether the readout can be trusted.

- [ ] Check assignment counts by variant.
- [ ] Check exposure counts by variant.
- [ ] Check missing metric data.
- [ ] Check instrumentation or logging caveats.

### Step 3: Interpret Metrics

**Goal**: Compare outcomes against decision rules.

- [ ] Compare primary metric control vs test.
- [ ] Compare each guardrail.
- [ ] Note practical significance, not just direction.
- [ ] Identify metric tradeoffs.

### Step 4: Investigate Segments

**Goal**: Explain important variation.

- [ ] Choose meaningful segments tied to the product question.
- [ ] Compare test/control within each segment.
- [ ] Label exploratory analysis clearly.
- [ ] Check whether outliers distort aggregate metrics.

### Step 5: Build The Readout

**Goal**: Communicate decision-quality evidence.

- [ ] Start with the decision.
- [ ] Include a metric table.
- [ ] Add only charts that clarify important comparisons.
- [ ] State caveats.
- [ ] Name follow-up work.

## Exit Criteria

The readout is complete when a stakeholder can see what happened, what is
uncertain, and what decision is recommended without reading raw analysis.
