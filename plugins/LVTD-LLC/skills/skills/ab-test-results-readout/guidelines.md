# A/B Test Results Readout Guidelines

## By Task

| What you are doing | Load |
|--------------------|------|
| Preparing a stakeholder readout | `workflows/prepare-results-readout.md` |
| Checking data quality before analysis | `references/core/rules.md` |
| Explaining mixed or flat results | `references/core/knowledge.md`, `references/core/examples.md` |
| Planning subgroup analysis | `references/core/rules.md`, `references/core/examples.md` |
| Choosing visualizations | `references/core/examples.md` |

## By Symptom

| If you notice... | Load |
|------------------|------|
| Primary metric and guardrails conflict | `references/core/rules.md` |
| Average result is small but suspicious | `references/core/knowledge.md` |
| Users may respond differently by segment | `references/core/examples.md` |
| Charts are confusing or overloaded | `references/core/rules.md` |

## Decision Tree

```text
What is uncertain?
|- Can we trust the data? -> references/core/rules.md
|- What happened overall? -> workflow
|- Why did it happen? -> subgroup analysis examples
`- What should we do? -> output format in SKILL.md
```

## File Index

| File | Purpose |
|------|---------|
| `references/core/knowledge.md` | Concepts for readouts and deeper analysis |
| `references/core/rules.md` | Data, interpretation, and visualization rules |
| `references/core/examples.md` | Report examples and anti-patterns |
| `workflows/prepare-results-readout.md` | Repeatable readout workflow |
