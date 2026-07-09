# Evaluate Adaptive Strategy Workflow

Decide whether adaptive testing is justified and what must be in place before
using it.

## When to Use

- Fixed-horizon A/B tests are too slow for the decision.
- The team wants to allocate more traffic to better-performing variants.
- The product can personalize based on context.
- Leadership wants to platformize bandits or sequential testing.

## Prerequisites

- Candidate use case and variants.
- Reward metric and guardrails.
- Data latency, dashboard, and alerting capabilities.
- Owners for algorithm, platform, product, and operations.

**Reference**: `references/core/rules.md`

## Workflow Steps

### Step 1: Clarify The Goal

**Goal**: Avoid using adaptive testing for the wrong problem.

- [ ] State whether the goal is early stopping, reward maximization, or personalization.
- [ ] State whether a clean causal estimate is required.
- [ ] Identify user or business cost of exploration.

### Step 2: Choose Candidate Strategy

**Goal**: Match strategy to need.

- [ ] Use sequential testing when the team needs planned interim decisions.
- [ ] Use bandits when reward during the test matters.
- [ ] Use Thompson sampling when probabilistic allocation is appropriate.
- [ ] Use contextual bandits when context features should influence allocation.

### Step 3: Check Infrastructure Readiness

**Goal**: Prevent adaptive systems from failing operationally.

- [ ] Confirm timely reward measurement.
- [ ] Confirm assignment and allocation updates are reliable.
- [ ] Confirm dashboards show traffic allocation, reward, and guardrails.
- [ ] Confirm alert and rollback ownership.

### Step 4: Plan Rollout

**Goal**: Introduce complexity incrementally.

- [ ] Start with one well-defined use case.
- [ ] Run shadow or limited exposure if possible.
- [ ] Document templates and decision rules for future teams.

### Step 5: Define Monitoring And Review

**Goal**: Keep adaptive allocation accountable.

- [ ] Monitor stale data and allocation anomalies.
- [ ] Review exploration cost and user experience.
- [ ] Decide whether to platformize after initial use cases.

## Quick Checklist

```text
[ ] Adaptive goal stated
[ ] Simpler test type considered
[ ] Reward and guardrails defined
[ ] Data freshness and allocation updates verified
[ ] Dashboards and alerts planned
[ ] Rollback and ownership defined
```

## Exit Criteria

The recommendation is ready when it explains why adaptive testing is justified,
which method fits, what infrastructure gaps remain, and how the first use case
will be monitored safely.
