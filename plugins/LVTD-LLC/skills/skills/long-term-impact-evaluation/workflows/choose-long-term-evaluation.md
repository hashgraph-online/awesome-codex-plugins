# Choose Long-Term Evaluation Workflow

Choose a practical method for measuring delayed or sustained product impact.

## When to Use

- Short-term A/B test metrics may not capture durable effect.
- The team is considering a long-term holdback.
- A full holdback is costly and alternatives are needed.
- Product wants post-rollout monitoring or CLV prediction.

## Prerequisites

- Short-term experiment result or planned rollout.
- Candidate short-term and long-term metrics.
- Expected delay window for the effect.
- Cost of withholding or delayed rollout.

**Reference**: `references/core/rules.md`

## Workflow Steps

### Step 1: State The Long-Term Question

**Goal**: Avoid measuring "long term" vaguely.

- [ ] Name the delayed behavior or business outcome.
- [ ] Estimate when the effect should appear.
- [ ] Explain why initial A/B metrics are insufficient.

### Step 2: Map Short-Term To Long-Term Metrics

**Goal**: Know whether early signals are trustworthy proxies.

- [ ] Identify short-term metrics affected by the feature.
- [ ] Identify long-term metrics that matter.
- [ ] Note evidence linking the short-term and long-term metrics.

### Step 3: Compare Methods

**Goal**: Match rigor to cost.

- [ ] Use holdbacks when a strong counterfactual is required and cost is acceptable.
- [ ] Use post-period analysis when rollout speed matters and confounding can be managed.
- [ ] Use continuous monitoring for anomaly detection, not causal proof.
- [ ] Use CLV models when prediction is useful and model drift is monitored.

### Step 4: Define Risks And Controls

**Goal**: Make limitations explicit.

- [ ] Name seasonality, campaigns, external changes, or product drift.
- [ ] Define metric cadence and comparison windows.
- [ ] Define when the method will be considered insufficient.

### Step 5: Recommend Next Action

**Goal**: Produce a decision-ready plan.

- [ ] Select one method or a hybrid.
- [ ] Explain why rejected methods were too costly, weak, or complex.
- [ ] Define the next review point.

## Quick Checklist

```text
[ ] Long-term question named
[ ] Short-term and long-term metrics mapped
[ ] Holdback, post-period, monitoring, and CLV options compared
[ ] Cost and confounding risks documented
[ ] Method selected with decision rules
```

## Exit Criteria

The plan is ready when it identifies the long-term effect, chooses a method that
fits the decision and constraints, and states what evidence can and cannot be
claimed from that method.
