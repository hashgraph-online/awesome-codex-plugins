# Experiment Type Selection Knowledge

Core concepts for matching an experiment design to the decision question.

## Overview

The right experiment type depends on the claim the team needs to make. A
superiority test asks whether the test variant performs better. A
non-inferiority test asks whether the test variant is not meaningfully worse. An
equivalence test asks whether variants are close enough to be treated as
similar. Holdbacks help validate longer-term impact.

## Test Types

### Superiority Test

**Definition**: A test designed to show that one variant performs better than
another on the target metric.

Use when the decision requires measurable upside before launch.

### Non-Inferiority Test

**Definition**: A test designed to show that a new experience is not worse than
control beyond an acceptable margin.

Use when the change has other benefits, such as engineering simplicity,
compliance, cost, or strategic alignment, and the team mainly needs to avoid
material metric harm.

### Equivalence Test

**Definition**: A test designed to show that two experiences are close enough
within a practical equivalence band.

Use when either experience is acceptable if user or business outcomes are
effectively the same.

### A/B/n Test

**Definition**: A test comparing more than one treatment against a control or
against each other.

Use when multiple variants are meaningfully distinct and traffic supports the
additional comparisons.

### Holdback

**Definition**: A population intentionally withheld from a rollout to preserve
a comparison group after launch.

Use when the team needs to monitor delayed effects, degradation, or cumulative
impact.

## Quick Reference

| Goal | Test Type |
|------|-----------|
| Prove uplift | Superiority |
| Ship safely without meaningful harm | Non-inferiority |
| Show practical sameness | Equivalence |
| Compare several clear alternatives | A/B/n |
| Measure delayed or cumulative impact | Holdback |
