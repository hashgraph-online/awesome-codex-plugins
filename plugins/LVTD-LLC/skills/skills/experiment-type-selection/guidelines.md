# Experiment Type Selection Guidelines

## By Task

| What you are doing | Load |
|--------------------|------|
| Choosing a test type from a product question | `workflows/choose-experiment-type.md` |
| Comparing superiority, non-inferiority, and equivalence | `references/core/knowledge.md` |
| Reviewing whether a design answers the right question | `references/core/rules.md`, `references/core/examples.md` |
| Deciding whether holdbacks are needed | `references/core/knowledge.md`, `references/core/rules.md` |

## By Question

| Team question | Likely file |
|---------------|-------------|
| "Will the new experience beat the old one?" | `references/core/knowledge.md` |
| "Can we ship without making things worse?" | `references/core/rules.md` |
| "Are these experiences effectively the same?" | `references/core/rules.md` |
| "Will gains last after rollout?" | `references/core/examples.md` |

## Decision Tree

```text
What must be proven?
|- Improvement -> superiority
|- Not meaningfully worse -> non-inferiority
|- Practically similar -> equivalence
|- Multiple design choices -> A/B/n if traffic supports it
`- Durability or delayed harm -> holdback
```

## File Index

| File | Purpose |
|------|---------|
| `references/core/knowledge.md` | Definitions and distinctions |
| `references/core/rules.md` | Selection and misuse rules |
| `references/core/examples.md` | Scenario-based examples |
| `workflows/choose-experiment-type.md` | Repeatable selection workflow |
