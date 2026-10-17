# Create A/B Test Brief Workflow

Create a decision-ready A/B test brief from a product idea.

## When to Use

- A team wants to A/B test a product change.
- An experiment idea lacks metrics, variants, or launch criteria.
- You need to review whether an experiment is ready to run.

## Prerequisites

- Product change or feature idea.
- Target audience or surface.
- Available analytics or instrumentation constraints.

**Reference**: `references/core/rules.md`

## Workflow Steps

### Step 1: State The Decision

**Goal**: Make clear what the test will decide.

- [ ] Write the ship, stop, or investigate decision.
- [ ] Identify who owns the decision.
- [ ] Record any non-negotiable guardrails.

### Step 2: Write The Hypothesis

**Goal**: Convert the idea into a measurable prediction.

- [ ] Note the observation or evidence behind the idea.
- [ ] Name the changed experience.
- [ ] Name the expected user behavior.
- [ ] Name the audience.
- [ ] Name the primary metric.

### Step 3: Choose Metrics

**Goal**: Make the measurement plan explicit.

- [ ] Choose one primary success metric.
- [ ] Add guardrail metrics for user, business, and system risk.
- [ ] Record baselines where available.
- [ ] If using a proxy, explain the missing ideal metric.

### Step 4: Define Variants And Eligibility

**Goal**: Make the comparison valid and interpretable.

- [ ] Define the control experience.
- [ ] Define the test experience.
- [ ] Write eligibility criteria.
- [ ] Define the exposure event.
- [ ] Choose pageview, session, or user randomization.

### Step 5: Set Confidence And Decision Rules

**Goal**: Prevent post-hoc decision making.

- [ ] Record minimum detectable effect or meaningful lift.
- [ ] Record sample size or duration assumptions.
- [ ] Define ship, do-not-ship, and investigate conditions.
- [ ] Note known validity risks.

## Quick Checklist

```text
[ ] Decision stated
[ ] Hypothesis complete
[ ] Primary and guardrail metrics selected
[ ] Baseline or proxy rationale recorded
[ ] Variants and eligibility clear
[ ] Randomization unit justified
[ ] Decision rules pre-committed
```

## Exit Criteria

The brief is ready when another team member can understand what will be tested,
who will be included, how success will be measured, and what decision each
likely result will trigger.
