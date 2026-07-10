# Long-Term Impact Evaluation Guidelines

Use this file as the router. Load only the files needed for the user's task.

## By Task

| What you are doing | Load these files |
|--------------------|------------------|
| Choosing a long-term measurement method | `workflows/choose-long-term-evaluation.md`, `references/core/rules.md` |
| Comparing holdbacks and alternatives | `references/core/knowledge.md`, `references/core/examples.md` |
| Planning post-period analysis | `references/core/rules.md`, `references/core/examples.md` |
| Using CLV models for long-term impact | `references/core/knowledge.md`, `references/core/rules.md` |
| Designing a detailed holdback | `holdback-experiment-design` |

## By Symptom

| If you notice... | Load |
|------------------|------|
| Short-term metrics may not predict long-term value | `references/core/knowledge.md` |
| A holdback is costly or politically hard | `workflows/choose-long-term-evaluation.md` |
| The team wants to roll out quickly but still measure later | `references/core/examples.md` |
| Continuous monitoring is being treated as causal proof | `references/core/rules.md` |
| CLV predictions may drift | `references/core/rules.md` |

## Decision Tree

```text
Need long-term causality?
|- Strong counterfactual required and cost acceptable -> holdback-experiment-design
|- Faster rollout with later comparison acceptable -> post-period analysis
|- Need anomaly detection after rollout -> continuous monitoring
|- Need predicted lifetime impact -> CLV model with validation
```

## File Index

| File | Purpose |
|------|---------|
| `references/core/knowledge.md` | Long-term evaluation concepts |
| `references/core/rules.md` | Method selection and risk rules |
| `references/core/examples.md` | Scenario examples |
| `workflows/choose-long-term-evaluation.md` | Repeatable selection workflow |
