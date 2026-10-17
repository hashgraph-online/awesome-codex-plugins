# Experiment Sensitivity Optimization Rules

Use these rules when redesigning an experiment for stronger signal or lower
traffic requirements.

## Core Rules

### 1. Start With The Decision, Not The Technique

Do not apply variance reduction before restating the decision.

- Name the business or product decision.
- Define the smallest practically meaningful change.
- Keep guardrails for risks outside the primary metric.

### 2. Prefer Metrics Close To The Mechanism

A broad metric may be too slow or noisy for the tested change.

- Choose a metric the feature can plausibly affect during the experiment window.
- Keep downstream metrics as guardrails when using a closer proxy.
- Document what the closer metric does and does not prove.

### 3. Remove Unnecessary Variants

Every additional variant consumes traffic and complicates interpretation.

- Keep a variant only if it answers a distinct decision.
- Use offline, qualitative, or prototype evaluation to filter options first.
- Avoid A/B/n designs when traffic is already scarce.

### 4. Use Capping For Outlier-Dominated Metrics

Capping can help when a few users dominate variance.

- Define the cap before analysis.
- Explain why extreme values are not the central decision signal.
- Preserve uncapped monitoring when extreme values are business-critical.

### 5. Use CUPED Or Covariates Only With Valid Pre-Treatment Data

Covariate methods depend on data quality.

- Confirm covariates are measured before treatment exposure.
- Confirm historical data relates to the outcome.
- Validate implementation on past or simulated data when possible.

### 6. Treat Sensitivity As An Evidence Tradeoff

Improving sensitivity changes what the result can claim.

- Separate directional learning from launch validation.
- Document interpretation limits.
- Revisit the full experiment design when sensitivity changes are substantial.

## Guidelines

Less strict recommendations:

- Pair feature-level primary metrics with business and user guardrails.
- Use `ml-experiment-evaluation` to reduce live variants for model or ranking
  experiments.
- Use `trustworthy-experiment-insights` when the question is whether an observed
  result is credible after the test runs.

## Exceptions

- **High-stakes decisions**: Prefer stronger power, duration, and guardrails
  even if the test costs more.
- **Exploratory prototypes**: A lighter metric can be acceptable if the team is
  explicit that the result is directional.

## Quick Reference

| Rule | Summary |
|------|---------|
| Decision first | Do not optimize a metric before naming the decision |
| Close metric | Prefer metrics near the feature mechanism |
| Fewer variants | Remove comparisons that do not answer distinct questions |
| Cap carefully | Cap outliers only with predeclared rationale |
| Validate covariates | CUPED needs valid pre-treatment data |
| Name limits | State what the sensitive design cannot prove |
