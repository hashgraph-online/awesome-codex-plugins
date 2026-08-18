# ML Experiment Evaluation Knowledge

Core concepts for evaluating machine-learning product changes.

## Overview

ML evaluation usually needs a hierarchy of evidence. Offline metrics can filter
bad candidates cheaply, interleaving can compare rankers with fewer users, and
online A/B tests can confirm real user and business impact.

## Key Concepts

### Offline Evaluation

**Definition**: Measuring model quality on historical, held-out, or simulated
data before exposing users.

Offline evaluation is useful for filtering poor candidates and iterating fast,
but it does not prove online product impact.

### Offline-Online Correlation

**Definition**: The relationship between offline metric movement and online
experiment outcomes.

Weak correlation can come from mismatched objectives, missing context, noisy
online metrics, or offline data that no longer reflects current behavior.

### Interleaving

**Definition**: A ranking evaluation method that mixes outputs from multiple
rankers in one user experience and attributes user actions back to rankers.

Interleaving can increase sensitivity for ranker comparisons and reduce testing
capacity pressure, but it requires ranking context and careful attribution.

### Online A/B Test

**Definition**: Live comparison of user outcomes between model treatments and a
control or alternative model.

Online tests are needed when the product decision depends on actual user,
business, or system impact.

### Evaluation Hierarchy

**Definition**: A staged path from cheap offline filtering to live user
evaluation only when live evidence is needed.

The hierarchy prevents every model idea from consuming user traffic.

## Terminology

| Term | Definition |
|------|------------|
| Precision | Share of predicted positives that are relevant |
| Recall | Share of relevant items retrieved |
| NDCG | Ranking quality metric that discounts lower positions |
| Attribution | Mapping a user action to the model or ranker that produced an item |
| Ranker | Model or algorithm that orders items for users |

## How It Relates To

- **Adaptive experimentation strategy**: Bandits and contextual bandits are
  online allocation strategies, not substitutes for model quality filtering.
- **Experiment sensitivity optimization**: Offline filtering and interleaving can
  reduce live traffic needs.
- **Experiment verification monitoring**: ML evaluations need additional
  logging and guardrails because poor recommendations can damage user trust.

## Common Misconceptions

- **Myth**: Offline wins are enough to launch.
  **Reality**: Offline metrics may not translate to online product impact.
- **Myth**: Every model needs a full A/B test.
  **Reality**: Poor candidates should be filtered before live traffic.
- **Myth**: Interleaving works for all ML changes.
  **Reality**: It mainly fits ranking or choice contexts with attribution.

## Quick Reference

| Concept | One-Line Summary |
|---------|------------------|
| Offline evaluation | Cheap model filtering before user exposure |
| Offline-online correlation | Whether offline gains predict online gains |
| Interleaving | Sensitive ranker comparison in one experience |
| A/B test | Live impact validation |
| Evaluation hierarchy | Escalate evidence only when needed |
