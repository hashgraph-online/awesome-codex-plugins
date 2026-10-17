# Review Experiment Credibility Workflow

Assess whether an experiment result should influence a product or engineering
decision.

## When to Use

- A result is surprising, suspiciously large, flat, mixed, or high-stakes.
- The team may have underpowered metrics.
- The experiment ended early or checked many metrics.
- Similar past experiments exist and can inform interpretation.

## Prerequisites

- Experiment result readout.
- Design assumptions: metrics, duration, MDE, sample size.
- Operational health checks when available.
- Comparable prior experiments, if any.

**Reference**: `references/core/rules.md`

## Workflow Steps

### Step 1: Confirm Interpretability

**Goal**: Do not analyze invalid experiment data as if it were clean.

- [ ] Check assignment, exposure, and metric health.
- [ ] Check whether treatment and control matched the intended design.
- [ ] Escalate to `experiment-verification-monitoring` if operational validity is unclear.

### Step 2: Check Power And Practical Significance

**Goal**: Distinguish "not significant" from "not informative."

- [ ] Compare actual sample/duration to the planned design.
- [ ] Identify underpowered primary or guardrail metrics.
- [ ] Compare observed effect to practical significance.

### Step 3: Check False Positive Risk

**Goal**: Avoid acting on noise.

- [ ] Flag early stopping, many comparisons, surprising segment wins, and weak priors.
- [ ] Compare observed lift to similar experiments.
- [ ] Consider replication or longer duration for high-stakes decisions.

### Step 4: Check False Negative Risk

**Goal**: Avoid discarding real effects hidden by poor sensitivity.

- [ ] Check noisy or broad metrics.
- [ ] Check whether variance reduction could help.
- [ ] Check whether the experiment duration was too short for the metric.

### Step 5: Recommend The Next Decision

**Goal**: Match confidence to action.

- [ ] Trust the result, trust with caveats, replicate, extend, investigate, or reject.
- [ ] State which decisions can be made now.
- [ ] State what evidence is still missing.

## Quick Checklist

```text
[ ] Operational validity checked
[ ] Power and practical significance checked
[ ] False positive risks reviewed
[ ] False negative risks reviewed
[ ] Similar experiments compared when available
[ ] Decision recommendation matches evidence strength
```

## Exit Criteria

The review is complete when it clearly states what can be decided from the
current evidence, what remains uncertain, and what follow-up is needed before a
higher-stakes decision.
