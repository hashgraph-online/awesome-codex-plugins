# Commitment Ladder Design Guidelines

Quick routing for commitment ladder design tasks. Load only the files needed for the current request.

## By Task

| What you are doing | Load these files |
| --- | --- |
| Understand the principle | references/commitment/knowledge.md |
| Create or rewrite copy | references/commitment/rules.md, references/commitment/examples.md |
| Audit an existing surface | references/commitment/smells.md, references/commitment/checklist.md |
| Run the full workflow | workflows/build-commitment-ladder.md |

## By Problem or Symptom

| If you notice | Load these files |
| --- | --- |
| The copy feels pushy or manipulative | references/commitment/smells.md |
| The evidence behind a claim is unclear | references/commitment/rules.md |
| The user needs a practical rewrite | references/commitment/examples.md |
| The task has several steps or stakeholders | workflows/build-commitment-ladder.md |

## Decision Tree

```
Start
|- Need concepts? -> references/commitment/knowledge.md
|- Need to create? -> references/commitment/rules.md + examples.md
|- Need to audit? -> references/commitment/smells.md + checklist.md
\- Need repeatable process? -> workflows/build-commitment-ladder.md
```

## File Index

| File | Purpose |
| --- | --- |
| references/commitment/knowledge.md | Definitions, concepts, and source grounding |
| references/commitment/rules.md | Core rules, guidelines, exceptions |
| references/commitment/examples.md | Bad/better examples |
| references/commitment/smells.md | Anti-patterns and detection |
| references/commitment/checklist.md | Fast pass/fail checklist |
| workflows/build-commitment-ladder.md | Create a sequence of small, authentic commitments that lead toward a meaningful user goal. |
