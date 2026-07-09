# A/B Test Design Brief Knowledge

Core concepts for designing product A/B tests that can support a decision.

## Overview

An A/B test compares user behavior between an unchanged control experience and
a changed test experience. The design brief makes the comparison interpretable:
it states the prediction, the population, the variants, the metrics, and the
decision rules before the test runs.

## Key Concepts

### Hypothesis

**Definition**: A specific prediction about how a product change will affect a
defined audience and measurable outcome.

Good hypotheses include evidence or reasoning, the proposed change, the target
audience, and the metric that will prove or disprove the prediction.

### Success Metric

**Definition**: The main metric used to decide whether the test achieved its
goal.

The success metric should reflect what the change is intended to improve. If
the ideal metric is unavailable, use a proxy only after naming the missing data
and why the proxy is acceptable.

### Guardrail Metric

**Definition**: A metric monitored to ensure the change does not create an
unacceptable downside.

Guardrails often represent user retention, revenue, reliability, performance,
or other business-critical concerns.

### Baseline

**Definition**: The expected current value of a metric before the change.

Baselines help teams estimate lift, regression, duration, and whether results
are plausible.

### Eligibility and Exposure

**Definition**: Eligibility identifies who can enter the experiment; exposure
identifies when a user has actually encountered the tested experience.

Eligibility and exposure define the population that results can represent.

## Terminology

| Term | Definition |
|------|------------|
| Control | The unchanged experience used as comparison |
| Test variant | The changed experience being evaluated |
| Proxy metric | A measurable substitute for a better unavailable metric |
| Randomization unit | The unit assigned to variants, such as user, session, or pageview |
| Minimum detectable effect | The smallest change worth detecting |

## Common Misconceptions

- **Myth**: Any positive movement means ship.
  **Reality**: Guardrails, statistical confidence, and practical significance
  still matter.
- **Myth**: Exposure criteria are just implementation detail.
  **Reality**: They define what population the result can safely describe.
- **Myth**: A proxy metric is as good as the ideal metric.
  **Reality**: A proxy is a compromise that needs a rationale.
