# Experiment Verification Monitoring Guidelines

Use this file as the router. Load only the files needed for the user's task.

## By Task

| What you are doing | Load these files |
|--------------------|------------------|
| Creating an experimentation quality roadmap | `workflows/create-experiment-quality-roadmap.md`, `references/core/rules.md` |
| Designing prelaunch QA or spot-check tooling | `references/core/knowledge.md`, `references/core/rules.md` |
| Adding canaries or active monitoring | `references/core/rules.md`, `references/core/examples.md` |
| Planning A/A tests | `references/core/knowledge.md`, `references/core/rules.md` |
| Investigating leakage or interference | `references/core/examples.md`, `references/core/rules.md` |

## By Symptom

| If you notice... | Load |
|------------------|------|
| Tests launch with wrong treatment or targeting | `references/core/rules.md` |
| Results are invalid because exposure logging failed | `references/core/examples.md` |
| Teams catch issues only after final readout | `workflows/create-experiment-quality-roadmap.md` |
| Platform health is assumed but untested | `references/core/knowledge.md` |
| Overlapping tests may conflict | `experimentation-throughput-strategy` and `references/core/rules.md` |

## Decision Tree

```text
Where can quality fail?
|- Before launch -> prelaunch QA and spot-check tooling
|- Early launch -> canary and exposure/metric monitoring
|- Platform infrastructure -> A/A tests
|- Cross-test effects -> leakage/interference checks
|- After results -> trustworthy-experiment-insights
```

## File Index

| File | Purpose |
|------|---------|
| `references/core/knowledge.md` | Verification and monitoring concepts |
| `references/core/rules.md` | Quality rules and gates |
| `references/core/examples.md` | Failure scenarios and fixes |
| `workflows/create-experiment-quality-roadmap.md` | Repeatable roadmap workflow |
