# Trustworthy Experiment Insights Guidelines

Use this file as the router. Load only the files needed for the user's task.

## By Task

| What you are doing | Load these files |
|--------------------|------------------|
| Reviewing whether a result is believable | `workflows/review-experiment-credibility.md`, `references/core/rules.md` |
| Investigating false positive risk | `references/core/knowledge.md`, `references/core/rules.md` |
| Investigating false negative risk | `references/core/rules.md`, `references/core/examples.md` |
| Comparing against prior experiments | `references/core/knowledge.md`, `references/core/examples.md` |
| Planning replication or longer duration | `references/core/rules.md` |

## By Symptom

| If you notice... | Load |
|------------------|------|
| A lift looks too good to be true | `workflows/review-experiment-credibility.md` |
| The team wants to ship from an underpowered metric | `references/core/rules.md` |
| A flat result may hide a real effect | `references/core/examples.md` |
| Results disagree with similar tests | `references/core/knowledge.md` |
| Many metrics or segments were checked | `references/core/rules.md` |

## Decision Tree

```text
Can the result be interpreted?
|- Operational health unknown -> experiment-verification-monitoring
|- Underpowered/noisy -> check false negative risk
|- Suspiciously strong/significant -> check false positive risk
|- Similar experiments exist -> compare or meta-analyze
|- Still credible -> decision-ready with caveats
```

## File Index

| File | Purpose |
|------|---------|
| `references/core/knowledge.md` | Insight-quality concepts |
| `references/core/rules.md` | Credibility and follow-up rules |
| `references/core/examples.md` | Result-review examples |
| `workflows/review-experiment-credibility.md` | Repeatable credibility workflow |
