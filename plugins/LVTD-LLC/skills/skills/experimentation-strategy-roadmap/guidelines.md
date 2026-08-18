# Experimentation Strategy Roadmap Guidelines

Use this file as the router. Load only the files needed for the user's task.

## By Task

| What you are doing | Load these files |
|--------------------|------------------|
| Prioritizing experimentation roadmap work | `workflows/prioritize-experimentation-roadmap.md`, `references/core/rules.md` |
| Deciding whether to platformize an advanced method | `references/core/rules.md`, `references/core/examples.md` |
| Balancing rate, quality, and cost | `references/core/knowledge.md`, `references/core/rules.md` |
| Aligning experimentation with company strategy | `references/core/knowledge.md`, `references/core/examples.md` |

## By Symptom

| If you notice... | Load |
|------------------|------|
| Teams want advanced methods without clear use cases | `references/core/rules.md` |
| Platform work is disconnected from company goals | `workflows/prioritize-experimentation-roadmap.md` |
| Tools are powerful but hard to adopt | `references/core/examples.md` |
| Quality and speed priorities conflict | `references/core/knowledge.md` |
| A technique worked once and may be platformized | `references/core/rules.md` |

## Decision Tree

```text
What is the roadmap problem?
|- Too slow -> experimentation-throughput-strategy
|- Untrusted results -> experiment-verification-monitoring or trustworthy-experiment-insights
|- Too expensive -> experiment-sensitivity-optimization or long-term-impact-evaluation
|- New advanced method -> prototype, score, then platformize if justified
|- Broad prioritization -> this skill
```

## File Index

| File | Purpose |
|------|---------|
| `references/core/knowledge.md` | Roadmap concepts and building blocks |
| `references/core/rules.md` | Prioritization and platformization rules |
| `references/core/examples.md` | Strategy and tradeoff examples |
| `workflows/prioritize-experimentation-roadmap.md` | Repeatable roadmap workflow |
