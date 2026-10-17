# Design Holdback Workflow

Plan a responsible long-term holdback for a feature rollout.

## When to Use

- Short-term A/B results may miss delayed effects.
- A feature's value may accumulate over weeks or months.
- The team needs a counterfactual after broad rollout.
- There is concern about metric degradation over time.

## Prerequisites

- Feature or change being rolled out.
- Reason short-term testing is insufficient.
- Candidate long-term metrics.
- Estimate of withholding cost.

**Reference**: `references/core/rules.md`

## Workflow Steps

### Step 1: State The Long-Term Question

**Goal**: Justify the holdback.

- [ ] Write the delayed, degradation, or cumulative effect being measured.
- [ ] Explain why short-term A/B testing cannot answer it.

### Step 2: Choose Holdback Type

**Goal**: Match design to the question.

- [ ] Use degradation holdback for delayed harm or regression.
- [ ] Use long-term cumulative holdback for compounding value.

### Step 3: Define Population And Duration

**Goal**: Limit cost while preserving measurement.

- [ ] Define eligible population.
- [ ] Choose holdback size.
- [ ] Set duration.
- [ ] Set readout cadence.

### Step 4: Define Metrics And Guardrails

**Goal**: Know what will be monitored.

- [ ] Choose long-term success metrics.
- [ ] Choose guardrails.
- [ ] Define escalation thresholds.

### Step 5: Assess Withholding Cost

**Goal**: Make ethical and business tradeoffs explicit.

- [ ] State user cost.
- [ ] State business cost.
- [ ] Identify safety, accessibility, or compliance concerns.

### Step 6: Set Exit Criteria

**Goal**: Prevent forgotten holdbacks.

- [ ] Define when to end normally.
- [ ] Define when to end early.
- [ ] Assign an owner.

## Exit Criteria

The holdback plan is ready when it has a clear long-term question, population,
duration, metrics, cost assessment, cadence, and owner.
