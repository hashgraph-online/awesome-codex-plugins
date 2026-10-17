# Experimentation Throughput Strategy Guidelines

Use this file as the router. Load only the files needed for the user's task.

## By Task

| What you are doing | Load these files |
|--------------------|------------------|
| Diagnosing an experiment queue or testing delay | `workflows/improve-experiment-throughput.md`, `references/core/rules.md` |
| Choosing isolated versus overlapping tests | `references/core/knowledge.md`, `references/core/rules.md` |
| Reviewing interaction-effect risk | `references/core/rules.md`, `references/core/examples.md` |
| Designing capacity dashboards or coordination tooling | `references/core/knowledge.md`, `references/core/examples.md` |

## By Symptom

| If you notice... | Load |
|------------------|------|
| Teams wait weeks for traffic or test slots | `workflows/improve-experiment-throughput.md` |
| Experiments touch the same surface or metric | `references/core/rules.md` |
| Teams want to run every test in isolation | `references/core/examples.md` |
| Teams want to overlap everything | `references/core/rules.md` |
| No one can see current or upcoming experiments | `references/core/knowledge.md` |

## Decision Tree

```text
Is the bottleneck traffic or coordination?
|- Traffic -> consider overlapping or sensitivity improvements
|- Coordination -> improve scheduling, ownership, and visibility
|- Quality failures -> use experiment-verification-monitoring first
```

## File Index

| File | Purpose |
|------|---------|
| `references/core/knowledge.md` | Throughput concepts and terminology |
| `references/core/rules.md` | Selection and coordination rules |
| `references/core/examples.md` | Common throughput scenarios |
| `workflows/improve-experiment-throughput.md` | Repeatable improvement workflow |
