# Choose ML Evaluation Strategy Workflow

Choose a practical evaluation path for a machine-learning product change.

## When to Use

- A team is deciding whether a model is ready for users.
- Many model variants compete for limited online traffic.
- Offline metrics and online results disagree.
- Ranking, search, or recommendations need high-sensitivity comparison.

## Prerequisites

- Model or ranker candidates.
- Product surface and affected user behavior.
- Candidate offline metrics.
- Available online metrics and logging constraints.

**Reference**: `references/core/rules.md`

## Workflow Steps

### Step 1: Define The Product Decision

**Goal**: Keep evaluation tied to product impact.

- [ ] State what launch, rollback, or iteration decision is needed.
- [ ] Identify the user experience risk of a poor model.
- [ ] Name business and user guardrails.

### Step 2: Start With Offline Filtering

**Goal**: Keep obviously poor models away from users.

- [ ] Choose offline metrics that reflect the model objective.
- [ ] Remove candidates that fail offline quality or safety thresholds.
- [ ] Record what offline evaluation cannot capture.

### Step 3: Check Offline-Online Relationship

**Goal**: Avoid optimizing a metric that does not translate.

- [ ] Compare prior offline metrics with online experiment outcomes.
- [ ] Identify objective mismatch, context mismatch, or noisy online metrics.
- [ ] Decide whether the offline metric suite needs revision.

### Step 4: Select Online Strategy

**Goal**: Use live traffic only when it answers a necessary question.

- [ ] Use interleaving for ranker comparisons where attribution can be logged.
- [ ] Use classic A/B testing when the decision is broad user/business impact.
- [ ] Use adaptive testing only when dynamic allocation has a justified reward.

### Step 5: Define Logging And Guardrails

**Goal**: Make the evaluation debuggable.

- [ ] Log exposure, ranker/model identity, position, attribution, and outcome.
- [ ] Monitor user trust, engagement, quality, and reliability guardrails.
- [ ] Define rollback criteria for poor user experience.

## Quick Checklist

```text
[ ] Product decision stated
[ ] Poor candidates filtered offline
[ ] Offline-online correlation checked or flagged
[ ] Online strategy selected for the right question
[ ] Logging and attribution requirements named
[ ] Guardrails and rollback rules defined
```

## Exit Criteria

The strategy is ready when it explains which candidates are filtered offline,
which need online evidence, which metrics decide each stage, and what logging is
required to trust the result.
