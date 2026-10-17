# A/B Test Design Brief Guidelines

Use this file as the router. Load only the files needed for the user's task.

## By Task

| What you are doing | Load these files |
|--------------------|------------------|
| Creating a new experiment spec | `workflows/create-ab-test-brief.md`, `references/core/rules.md` |
| Choosing metrics or guardrails | `references/core/knowledge.md`, `references/core/rules.md` |
| Defining eligibility or exposure | `references/core/rules.md`, `references/core/examples.md` |
| Reviewing an existing brief | `references/core/rules.md`, `references/core/examples.md` |

## By Symptom

| If you notice... | Load |
|------------------|------|
| The hypothesis is just "test X" | `references/core/rules.md` |
| The team lacks the ideal metric | `references/core/knowledge.md` |
| The variant changes many variables | `references/core/examples.md` |
| Results may not generalize | `references/core/rules.md` |

## Decision Tree

```text
What is missing?
|- Hypothesis -> references/core/rules.md
|- Metrics -> references/core/knowledge.md
|- Variant design -> references/core/examples.md
|- Full brief -> workflows/create-ab-test-brief.md
```

## File Index

| File | Purpose |
|------|---------|
| `references/core/knowledge.md` | Core experiment anatomy concepts |
| `references/core/rules.md` | Practical design and readiness rules |
| `references/core/examples.md` | Brief examples and common mistakes |
| `workflows/create-ab-test-brief.md` | Repeatable creation workflow |
