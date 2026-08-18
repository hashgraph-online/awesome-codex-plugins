# ML Experiment Evaluation Guidelines

Use this file as the router. Load only the files needed for the user's task.

## By Task

| What you are doing | Load these files |
|--------------------|------------------|
| Choosing an ML evaluation strategy | `workflows/choose-ml-evaluation-strategy.md`, `references/core/rules.md` |
| Designing offline evaluation | `references/core/knowledge.md`, `references/core/rules.md` |
| Evaluating rankers with interleaving | `references/core/rules.md`, `references/core/examples.md` |
| Deciding whether a model deserves online traffic | `references/core/examples.md`, `references/core/rules.md` |

## By Symptom

| If you notice... | Load |
|------------------|------|
| Bad models reach users before filtering | `references/core/rules.md` |
| Offline gains do not match online results | `references/core/knowledge.md` |
| Ranking teams fight for test capacity | `references/core/examples.md` |
| The team wants a bandit for ML allocation | `adaptive-experimentation-strategy` first, then `references/core/rules.md` |
| Many model variants need screening | `workflows/choose-ml-evaluation-strategy.md` |

## Decision Tree

```text
What kind of ML decision is this?
|- Filter bad candidates -> offline evaluation
|- Compare rankers with scarce traffic -> interleaving
|- Confirm user/business impact -> online A/B test
|- Dynamically allocate among options -> adaptive-experimentation-strategy
```

## File Index

| File | Purpose |
|------|---------|
| `references/core/knowledge.md` | ML evaluation terms and strategy types |
| `references/core/rules.md` | Strategy selection and validation rules |
| `references/core/examples.md` | Common ML evaluation scenarios |
| `workflows/choose-ml-evaluation-strategy.md` | Repeatable selection workflow |
