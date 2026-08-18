# Trustworthy Experiment Insights Knowledge

Core concepts for judging the credibility of experiment results.

## Overview

Experiment results are only useful when the insight is trustworthy. A result can
be statistically significant but misleading, or flat because the design could
not detect the effect that mattered.

## Key Concepts

### False Positive

**Definition**: Concluding there is an effect when the observed result is noise
or an artifact.

False positive risk rises with many comparisons, early stopping, surprising
large effects, weak priors, and uncorrected repeated looks.

### False Negative

**Definition**: Missing a real effect because the experiment could not detect
it.

False negative risk rises when metrics are underpowered, noisy, broad, or too
slow to move within the test window.

### Statistical Power

**Definition**: The probability that the experiment can detect a true effect of
the planned size.

Power depends on sample size, variance, effect size, and design assumptions.

### Meta-Analysis

**Definition**: Comparing or combining evidence across similar experiments to
understand whether a result fits broader product evidence.

Useful meta-analysis requires careful comparison of populations, metrics,
features, and time periods.

### Replication

**Definition**: Running another experiment or follow-up check to test whether a
result repeats.

Replication is especially useful for high-stakes or surprising results.

## Terminology

| Term | Definition |
|------|------------|
| Practical significance | Whether an observed effect is large enough to matter |
| Prior evidence | Relevant evidence from past experiments or domain knowledge |
| Underpowered metric | Metric without enough sample or sensitivity to detect the needed effect |
| Suspicious lift | Effect size that is much larger than comparable evidence would suggest |
| Covariate adjustment | Analysis method using pre-treatment variables to reduce noise |

## How It Relates To

- **A/B test results readout**: Use this skill after or during a readout when
  the decision depends on result credibility.
- **Experiment sensitivity optimization**: Use before rerunning or extending an
  underpowered test.
- **Experiment verification monitoring**: Operational validity must be checked
  before statistical credibility.

## Common Misconceptions

- **Myth**: Significant means true.
  **Reality**: False positives still happen, especially with weak design or many
  comparisons.
- **Myth**: Not significant means no effect.
  **Reality**: The experiment may not have had enough power or sensitivity.
- **Myth**: Similar experiments can be compared directly.
  **Reality**: Population, timing, metrics, and implementation differences can
  change meaning.

## Quick Reference

| Concept | One-Line Summary |
|---------|------------------|
| False positive | Mistaking noise for real effect |
| False negative | Missing real effect because design was weak |
| Power | Ability to detect the planned effect |
| Meta-analysis | Compare evidence across similar tests |
| Replication | Check whether surprising evidence repeats |
