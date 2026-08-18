# Adaptive Experimentation Strategy Guidelines

Use this file as the router. Load only the files needed for the user's task.

## By Task

| What you are doing | Load these files |
|--------------------|------------------|
| Deciding whether adaptive testing fits | `workflows/evaluate-adaptive-strategy.md`, `references/core/rules.md` |
| Comparing sequential tests and bandits | `references/core/knowledge.md`, `references/core/rules.md` |
| Planning Thompson sampling or contextual bandits | `references/core/rules.md`, `references/core/examples.md` |
| Checking engineering readiness | `workflows/evaluate-adaptive-strategy.md`, `references/core/examples.md` |

## By Symptom

| If you notice... | Load |
|------------------|------|
| The team wants to stop tests early | `references/core/knowledge.md` |
| The team wants to maximize reward during testing | `references/core/rules.md` |
| Personalization depends on user context | `references/core/examples.md` |
| Real-time data pipelines are immature | `workflows/evaluate-adaptive-strategy.md` |
| The decision needs causal precision more than reward | `experiment-type-selection` first |

## Decision Tree

```text
Why adapt?
|- Stop early with controlled decision rules -> sequential testing
|- Allocate more traffic to better performers -> bandit
|- Bayesian probabilistic allocation -> Thompson sampling
|- Personalize by context -> contextual bandit
|- Need clean causal readout -> fixed-horizon or standard experiment type
```

## File Index

| File | Purpose |
|------|---------|
| `references/core/knowledge.md` | Adaptive testing concepts |
| `references/core/rules.md` | Selection and readiness rules |
| `references/core/examples.md` | Use-case examples and anti-patterns |
| `workflows/evaluate-adaptive-strategy.md` | Repeatable readiness workflow |
