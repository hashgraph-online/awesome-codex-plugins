# Improve Experiment Throughput Workflow

Create a practical plan for running more experiments without weakening evidence.

## When to Use

- Teams are waiting for testing availability.
- Roadmap experiments conflict or block each other.
- Leadership wants a higher experimentation rate.
- The team is considering overlapping experiments.

## Prerequisites

- Recent experiment inventory or roadmap.
- Product surfaces, audiences, and primary metrics.
- Known platform constraints: traffic, assignment, QA, dashboards, analysis.

**Reference**: `references/core/rules.md`

## Workflow Steps

### Step 1: Map The Pipeline

**Goal**: Identify where experiment rate is actually constrained.

- [ ] List the last 5-10 experiments and where each waited.
- [ ] Separate setup delay, QA delay, traffic delay, analysis delay, and decision delay.
- [ ] Identify surfaces or audiences with repeated capacity contention.

### Step 2: Classify Experiment Dependencies

**Goal**: Decide what can safely run together.

- [ ] Mark tests that affect the same surface, metric, eligibility, or user journey.
- [ ] Mark tests with independent user experiences and metrics.
- [ ] Identify experiments that must run before another test can be interpreted.

### Step 3: Choose A Testing Strategy

**Goal**: Pick the simplest strategy that increases rate while preserving insight.

- [ ] Use isolated tests for high-stakes, high-interference, or precision-critical changes.
- [ ] Use overlapping tests when changes are independent enough and capacity is the constraint.
- [ ] Use a hybrid strategy for mixed roadmaps.

### Step 4: Add Safeguards

**Goal**: Make overlaps observable and reversible.

- [ ] Define conflict dimensions: surface, audience, metric, feature area, time window.
- [ ] Add dashboard visibility into active and upcoming tests.
- [ ] Define when conflicts trigger review, isolation, restart, or cancellation.

### Step 5: Update Process And Tooling

**Goal**: Make the strategy adoptable.

- [ ] Add scheduling rules to the experimentation playbook.
- [ ] Add metadata fields for test owner, surface, audience, metrics, and conflict risk.
- [ ] Define an owner for resolving capacity conflicts.

## Quick Checklist

```text
[ ] Bottleneck identified with evidence
[ ] Tests classified by dependency and interference risk
[ ] Isolated/overlapping/hybrid strategy selected
[ ] Conflict safeguards defined
[ ] Capacity visibility improved
[ ] Scheduling rules documented
```

## Exit Criteria

The throughput plan is ready when teams can see testing capacity, know which
tests may overlap, and have explicit rules for isolating or deferring tests when
validity is at risk.
