# Adaptive Experimentation Strategy Knowledge

Core concepts for adaptive testing beyond fixed-horizon A/B tests.

## Overview

Adaptive testing changes the experiment process while the test runs. It can stop
early, shift traffic toward better variants, or personalize allocation, but it
adds statistical, product, and operational complexity.

## Key Concepts

### Sequential Testing

**Definition**: A testing approach with planned interim analyses and rules for
stopping early while still preserving valid decision logic.

Sequential testing is useful when early answers can save time but the team still
needs a defined end point.

### Multi-Armed Bandit

**Definition**: An adaptive allocation strategy that balances learning about
variants with sending more traffic to variants that appear to perform better.

Bandits focus on reward during the experiment, not only final comparison.

### Thompson Sampling

**Definition**: A Bayesian bandit algorithm that samples from current beliefs
about each variant and allocates traffic based on those sampled outcomes.

It is often used when the team wants a practical exploration/exploitation
mechanism.

### Contextual Bandit

**Definition**: A bandit that uses context features to personalize which option
is shown to which user or situation.

Contextual bandits require reliable features, reward measurement, and monitoring
for user experience and fairness concerns.

### Exploration And Exploitation

**Definition**: The tradeoff between learning about uncertain options and using
the option currently believed to be best.

Adaptive strategies make this tradeoff explicit and operational.

## Terminology

| Term | Definition |
|------|------------|
| Reward | Outcome the adaptive system tries to maximize |
| Allocation | Percentage or probability of traffic sent to each option |
| Interim analysis | Planned evaluation before the final test end |
| Context feature | User, session, or environment signal used for personalization |
| Stale data | Reward or context data too old to support reliable allocation |

## How It Relates To

- **Experiment type selection**: Use a simpler test type when it answers the
  decision with less operational risk.
- **ML experiment evaluation**: Bandits often appear in ML contexts, but model
  quality filtering still matters.
- **Experiment verification monitoring**: Adaptive systems need stronger active
  dashboards and alerts.

## Common Misconceptions

- **Myth**: Adaptive tests are always better than A/B tests.
  **Reality**: They are better for specific allocation and decision problems.
- **Myth**: Bandits give the same clean readout as fixed A/B tests.
  **Reality**: They optimize allocation and require different interpretation.
- **Myth**: Contextual bandits are just segmented A/B tests.
  **Reality**: They dynamically personalize based on context and reward data.

## Quick Reference

| Concept | One-Line Summary |
|---------|------------------|
| Sequential testing | Planned early decisions |
| Bandit | Dynamic allocation to balance learning and reward |
| Thompson sampling | Bayesian allocation method |
| Contextual bandit | Adaptive personalization by context |
| Exploration/exploitation | Learning versus using the apparent winner |
