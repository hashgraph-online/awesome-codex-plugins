# A/B Testing Platform Strategy Guidelines

## By Task

| What you are doing | Load |
|--------------------|------|
| Making a build-vs-buy recommendation | `workflows/decide-platform-strategy.md`, `references/core/rules.md` |
| Listing platform components | `references/core/knowledge.md` |
| Planning a minimum viable platform | `references/core/rules.md`, `references/core/examples.md` |
| Reviewing a platform roadmap | `references/core/examples.md` |

## By Symptom

| If you notice... | Load |
|------------------|------|
| The team wants a perfect platform before first tests | `references/core/rules.md` |
| Assignment exists but exposure logging is unclear | `references/core/knowledge.md` |
| Buy option ignores internal data constraints | `references/core/examples.md` |
| Platform demand is cultural, not technical | `references/core/rules.md` |

## Decision Tree

```text
What is the platform question?
|- Need first experiments -> minimum viable setup
|- Need scale/self-service -> platform roadmap
|- Build or buy -> workflow
`- Measurement trust issue -> knowledge + rules
```

## File Index

| File | Purpose |
|------|---------|
| `references/core/knowledge.md` | Platform concepts and components |
| `references/core/rules.md` | Build-vs-buy and roadmap rules |
| `references/core/examples.md` | Practical scenarios |
| `workflows/decide-platform-strategy.md` | Repeatable decision workflow |
