# ML Experiment Evaluation Rules

Use these rules when selecting an evaluation path for ML-powered product
changes.

## Core Rules

### 1. Filter Poor Models Before Live Exposure

Do not use users as the first quality gate.

- Define offline quality thresholds.
- Include safety or user-trust checks when possible.
- Send only plausible candidates to online evaluation.

### 2. Treat Offline Metrics As Directional Until Validated

Offline gains can fail online.

- Compare offline and online results across past experiments.
- Look for objective mismatch between model training and product outcomes.
- Update the offline metric suite when it rewards the wrong behavior.

### 3. Use Interleaving For Ranker Comparisons

Interleaving fits ranking contexts, not every ML feature.

- Require a user-facing ranked list or choice set.
- Log which ranker contributed each item and position.
- Use it as an early online signal, not always the final launch decision.

### 4. Use Online A/B Testing For Product Impact

When the question is user, business, or system impact, live evidence may be
needed.

- Keep control and treatment interpretable.
- Monitor guardrails for irrelevant recommendations, trust loss, reliability,
  and revenue or retention effects.
- Use `ab-test-design-brief` for the full test spec.

### 5. Escalate To Adaptive Methods Only With Infrastructure

Bandits need more than a model candidate list.

- Confirm real-time or timely data flow.
- Confirm dashboards and alerting.
- Confirm ownership for stale data, bad allocation, and rollback.

## Guidelines

Less strict recommendations:

- Build a correlation database that links offline metrics to online outcomes.
- Use offline evaluation to reduce the number of live variants.
- Keep model evaluation documentation understandable to product partners.

## Exceptions

- **Very low-risk internal tooling**: Offline and shadow-mode evidence may be
  enough when there is no meaningful user harm.
- **Critical safety changes**: Stronger live guardrails or staged rollouts may
  be needed even after offline quality looks good.

## Quick Reference

| Rule | Summary |
|------|---------|
| Filter first | Keep bad models away from users |
| Validate offline | Check whether offline gains translate |
| Interleave rankers | Use when ranked outputs and attribution exist |
| A/B for impact | Use live tests for product/business outcomes |
| Check infrastructure | Adaptive methods need operational support |
