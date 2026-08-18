# Holdback Experiment Design Guidelines

## By Task

| What you are doing | Load |
|--------------------|------|
| Designing a holdback | `workflows/design-holdback.md` |
| Choosing degradation vs cumulative holdback | `references/core/knowledge.md`, `references/core/rules.md` |
| Estimating holdback cost | `references/core/rules.md` |
| Reviewing a holdback plan | `references/core/examples.md` |

## By Symptom

| If you notice... | Load |
|------------------|------|
| Short-term test may miss delayed effects | `references/core/knowledge.md` |
| The team wants a holdback "just in case" | `references/core/rules.md` |
| Withholding creates user or revenue cost | `references/core/rules.md` |
| Long-term metrics need cadence | `workflows/design-holdback.md` |

## Decision Tree

```text
Why hold back?
|- Detect degradation after launch -> degradation holdback
|- Measure cumulative long-term value -> long-term cumulative holdback
|- Unsure or no question -> do not hold back yet
`- Feature has high user benefit -> shorten, reduce, or avoid holdback
```

## File Index

| File | Purpose |
|------|---------|
| `references/core/knowledge.md` | Holdback concepts and types |
| `references/core/rules.md` | Design, cost, and exit rules |
| `references/core/examples.md` | Practical scenarios |
| `workflows/design-holdback.md` | Holdback planning workflow |
