# JavaScript UI Math Guidelines

Quick reference for finding the right file. Load only the files relevant to the task.

## Workflows

| Task | Workflow |
|------|----------|
| Apply or debug javascript ui math | `workflows/debug-ui-number-logic.md` |

## By Task

| What you're doing | Load these files |
|-------------------|------------------|
| Learn the concepts | `references/ui-numbers/knowledge.md` |
| Apply rules to code | `references/ui-numbers/rules.md`, `references/ui-numbers/examples.md` |
| Derive a reusable formula | `references/ui-numbers/patterns.md`, `references/ui-numbers/rules.md` |
| Review an implementation | `references/ui-numbers/checklist.md`, `references/ui-numbers/rules.md` |
| Trace source coverage | `references/source-map.md` |

## By Code Element

| Working with... | Primary | Secondary |
|-----------------|---------|-----------|
| CSS declarations | `references/ui-numbers/rules.md` | `references/ui-numbers/examples.md` |
| JavaScript calculations | `references/ui-numbers/patterns.md` | `references/ui-numbers/checklist.md` |
| Design tokens or constants | `references/ui-numbers/knowledge.md` | `references/ui-numbers/rules.md` |
| Layout or visual regressions | `references/ui-numbers/checklist.md` | `workflows/debug-ui-number-logic.md` |

## By Problem/Symptom

| If you notice... | Load these files |
|------------------|------------------|
| Carousel goes to -1 | `references/ui-numbers/rules.md`, `references/ui-numbers/checklist.md` |
| 0 is ignored as an option | `references/ui-numbers/rules.md`, `references/ui-numbers/checklist.md` |
| Displayed sum is 0.30000000000000004 | `references/ui-numbers/rules.md`, `references/ui-numbers/checklist.md` |

## Decision Tree

```text
What do you need?
|
|-- Learn the model -> references/ui-numbers/knowledge.md
|-- Fix code now -> references/ui-numbers/rules.md + examples.md
|-- Create a formula -> references/ui-numbers/patterns.md
|-- Review or debug -> workflows/debug-ui-number-logic.md + checklist.md
`-- Verify provenance -> references/source-map.md
```

## File Index

| File | Purpose |
|------|---------|
| `SKILL.md` | Skill trigger and minimal usage instructions |
| `guidelines.md` | Routing layer for progressive disclosure |
| `references/source-map.md` | Book citation traceability |
| `references/ui-numbers/knowledge.md` | Core concepts and terms |
| `references/ui-numbers/rules.md` | Actionable rules and exceptions |
| `references/ui-numbers/examples.md` | Bad/good examples and refactoring pattern |
| `references/ui-numbers/patterns.md` | Reusable formula patterns |
| `references/ui-numbers/checklist.md` | Review checklist and red flags |
| `workflows/debug-ui-number-logic.md` | Step-by-step workflow |
