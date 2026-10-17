# Experiment Sensitivity Optimization Guidelines

Use this file as the router. Load only the files needed for the user's task.

## By Task

| What you are doing | Load these files |
|--------------------|------------------|
| Reducing sample size or duration | `workflows/optimize-experiment-sensitivity.md`, `references/core/rules.md` |
| Choosing a more sensitive metric | `references/core/knowledge.md`, `references/core/rules.md` |
| Deciding whether to use capping or CUPED | `references/core/rules.md`, `references/core/examples.md` |
| Reviewing too many variants | `references/core/rules.md`, `references/core/examples.md` |

## By Symptom

| If you notice... | Load |
|------------------|------|
| The test would take too long to power | `workflows/optimize-experiment-sensitivity.md` |
| The metric is noisy or far from the feature | `references/core/knowledge.md` |
| A few extreme users dominate the metric | `references/core/rules.md` |
| Multiple variants split scarce traffic | `references/core/examples.md` |
| Historical covariates are available | `references/core/rules.md` |

## Decision Tree

```text
Why is signal weak?
|- Metric too broad/noisy -> choose closer or capped metric
|- Too many variants -> reduce variants or prefilter offline
|- Baseline variance high -> consider CUPED, stratification, covariates
|- Effect too small to matter -> revisit decision and MDE
```

## File Index

| File | Purpose |
|------|---------|
| `references/core/knowledge.md` | Sensitivity concepts and terms |
| `references/core/rules.md` | Practical optimization rules |
| `references/core/examples.md` | Scenario examples and anti-patterns |
| `workflows/optimize-experiment-sensitivity.md` | Repeatable sensitivity review |
