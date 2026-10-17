# Inclusive Experiment Analysis Guidelines

## By Task

| What you are doing | Load |
|--------------------|------|
| Planning inclusive segment dimensions | `references/core/knowledge.md`, `references/core/rules.md` |
| Reviewing subgroup impact after a test | `workflows/review-inclusive-impact.md` |
| Checking test/control balance | `references/core/rules.md` |
| Explaining inclusive design risks | `references/core/examples.md` |

## By Symptom

| If you notice... | Load |
|------------------|------|
| A feature may affect accessibility | `references/core/examples.md` |
| The result is positive only for majority users | `references/core/rules.md` |
| Test/control composition looks imbalanced | `references/core/rules.md` |
| The team lacks relevant dimensions | `references/core/knowledge.md` |

## Decision Tree

```text
What risk is present?
|- Accessibility or assistive tech -> examples
|- Device/bandwidth constraints -> examples
|- Segment imbalance -> rules
|- Missing data -> knowledge + recommendation caveat
`- Unknown subgroup effect -> workflow
```

## File Index

| File | Purpose |
|------|---------|
| `references/core/knowledge.md` | Inclusive testing concepts |
| `references/core/rules.md` | Design and interpretation rules |
| `references/core/examples.md` | Scenario examples |
| `workflows/review-inclusive-impact.md` | Inclusive review workflow |
