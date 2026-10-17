# Experiment Sensitivity Optimization Knowledge

Core concepts for making A/B tests more sensitive and resource-efficient.

## Overview

Experiment sensitivity is the ability to detect a meaningful effect in a noisy
environment. Better sensitivity can reduce sample-size needs, shorten duration,
or make results easier to trust, but only when the metric still represents the
decision the team needs to make.

## Key Concepts

### Minimum Detectable Effect

**Definition**: The smallest change the experiment is designed to detect with
the planned sample size and statistical assumptions.

MDE should be tied to practical significance. Detecting an effect too small to
matter wastes effort; missing a meaningful effect can lead to a false negative.

### Metric Sensitivity

**Definition**: How readily a metric responds to the change being tested.

Metrics closer to the feature mechanism often move faster than broad business
metrics, but they still need guardrails to prevent local optimization.

### Capping Metric Technique

**Definition**: Limiting extreme values in a metric so a small number of users
does not dominate variance.

Capping can improve precision when outliers are not central to the decision.

### CUPED

**Definition**: A variance reduction technique that uses pre-experiment or
historical covariates to reduce noise in outcome estimates.

CUPED requires relevant historical data and careful implementation so the
adjustment improves precision without distorting interpretation.

### Variant Reduction

**Definition**: Removing or consolidating variants so traffic is not split
across comparisons that do not answer distinct decisions.

Fewer variants can increase power and make learning easier to interpret.

## Terminology

| Term | Definition |
|------|------------|
| Power | Probability of detecting a true effect of the planned size |
| Variance | Amount of noise or spread in metric outcomes |
| Covariate | Pre-treatment variable used to explain outcome variation |
| Guardrail | Metric that protects against unacceptable downside |
| Practical significance | Whether an effect is large enough to matter |

## How It Relates To

- **A/B test design brief**: Sensitivity changes should be reflected in the
  metric, duration, and decision-rule sections.
- **Trustworthy experiment insights**: Better sensitivity reduces some false
  negative risk, but does not remove false positive risk.
- **ML experiment evaluation**: Offline filtering can reduce live variants for
  model experiments.

## Common Misconceptions

- **Myth**: A smaller MDE is always better.
  **Reality**: The effect must be meaningful enough to change a decision.
- **Myth**: A sensitive metric can replace guardrails.
  **Reality**: Sensitive metrics need guardrails because they can optimize a
  narrow behavior at broader cost.
- **Myth**: CUPED is just a switch to turn on.
  **Reality**: It depends on covariate quality and implementation correctness.

## Quick Reference

| Concept | One-Line Summary |
|---------|------------------|
| MDE | Smallest effect the test is built to detect |
| Sensitive metric | Metric close to the expected mechanism |
| Capping | Reduce outlier-driven variance |
| CUPED | Use historical covariates to reduce noise |
| Variant reduction | Stop splitting traffic across unnecessary comparisons |
