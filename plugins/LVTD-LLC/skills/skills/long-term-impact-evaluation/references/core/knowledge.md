# Long-Term Impact Evaluation Knowledge

Core concepts for evaluating sustained product impact.

## Overview

Some product effects appear, fade, compound, or reverse after the initial A/B
test window. Long-term evaluation helps teams avoid optimizing for short-term
spikes that do not produce durable value.

## Key Concepts

### Long-Term Holdback

**Definition**: Withholding a feature from a group after rollout to preserve a
long-term counterfactual.

Holdbacks provide strong long-term measurement but can be costly, complex, and
hard to justify if withheld users lose value.

### Post-Period Analysis

**Definition**: Comparing outcomes after the experiment period or after rollout
to estimate delayed impact.

Post-period analysis can be cheaper than holdbacks but is more vulnerable to
seasonality, campaigns, and other external changes.

### Continuous Monitoring

**Definition**: Ongoing tracking of metrics after rollout to detect changes,
regressions, or unexpected issues.

Monitoring is useful for alerting and trend detection but does not provide the
same causal counterfactual as an experiment.

### CLV Model

**Definition**: A predictive model estimating customer lifetime value or
long-term value from shorter-term behavior and user attributes.

CLV models can estimate long-term impact faster, but predictions can drift when
behavior or external conditions change.

### Short-Term And Long-Term Metric Relationship

**Definition**: The evidence that early metric movement predicts sustained user
or business value.

Weak relationships make short-term wins risky to interpret as durable impact.

## Terminology

| Term | Definition |
|------|------------|
| Counterfactual | What would have happened without the rollout |
| Confounder | External factor that affects outcome interpretation |
| Seasonality | Time-based pattern that can mimic or hide product impact |
| Model drift | Degradation when prediction relationships change |
| Monitoring cadence | How often long-term metrics are reviewed |

## How It Relates To

- **Holdback experiment design**: Use for detailed population, duration, and
  withholding-cost planning.
- **Trustworthy experiment insights**: Use when deciding whether long-term
  evidence is credible enough to act on.
- **Experimentation strategy roadmap**: Use when long-term measurement competes
  with cost, speed, and usability.

## Common Misconceptions

- **Myth**: A strong short-term win guarantees long-term value.
  **Reality**: Effects can fade, reverse, or create delayed downside.
- **Myth**: Monitoring after rollout proves causality.
  **Reality**: Monitoring detects changes but often lacks a counterfactual.
- **Myth**: Holdbacks are always the best answer.
  **Reality**: Their accuracy can be outweighed by user, business, or complexity
  cost.

## Quick Reference

| Concept | One-Line Summary |
|---------|------------------|
| Holdback | Strong counterfactual, higher cost |
| Post-period analysis | Faster rollout, more confounding |
| Continuous monitoring | Detects trends, not causal proof |
| CLV model | Predicts long-term value, risk of drift |
| Metric relationship | Whether short-term movement predicts durable value |
