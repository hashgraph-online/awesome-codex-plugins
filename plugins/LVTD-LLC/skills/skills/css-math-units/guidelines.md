# CSS Math Units Guidelines

Quick reference for finding the right file. Load only the files relevant to the task.

## Workflows

| Task | Workflow |
|------|----------|
| Apply or debug css math units | `workflows/debug-css-calculation.md` |

## By Task

| What you're doing | Load these files |
|-------------------|------------------|
| Learn the concepts | `references/css-calculations/knowledge.md` |
| Apply rules to code | `references/css-calculations/rules.md`, `references/css-calculations/examples.md` |
| Derive a reusable formula | `references/css-calculations/patterns.md`, `references/css-calculations/rules.md` |
| Review an implementation | `references/css-calculations/checklist.md`, `references/css-calculations/rules.md` |
| Trace source coverage | `references/source-map.md` |

## By Code Element

| Working with... | Primary | Secondary |
|-----------------|---------|-----------|
| CSS declarations | `references/css-calculations/rules.md` | `references/css-calculations/examples.md` |
| JavaScript calculations | `references/css-calculations/patterns.md` | `references/css-calculations/checklist.md` |
| Design tokens or constants | `references/css-calculations/knowledge.md` | `references/css-calculations/rules.md` |
| Layout or visual regressions | `references/css-calculations/checklist.md` | `workflows/debug-css-calculation.md` |

## By Problem/Symptom

| If you notice... | Load these files |
|------------------|------------------|
| Font sizes grow unexpectedly | `references/css-calculations/rules.md`, `references/css-calculations/checklist.md` |
| Box is wider than declared width | `references/css-calculations/rules.md`, `references/css-calculations/checklist.md` |
| calc() is invalid | `references/css-calculations/rules.md`, `references/css-calculations/checklist.md` |

## Decision Tree

```text
What do you need?
|
|-- Learn the model -> references/css-calculations/knowledge.md
|-- Fix code now -> references/css-calculations/rules.md + examples.md
|-- Create a formula -> references/css-calculations/patterns.md
|-- Review or debug -> workflows/debug-css-calculation.md + checklist.md
`-- Verify provenance -> references/source-map.md
```

## File Index

| File | Purpose |
|------|---------|
| `SKILL.md` | Skill trigger and minimal usage instructions |
| `guidelines.md` | Routing layer for progressive disclosure |
| `references/source-map.md` | Book citation traceability |
| `references/css-calculations/knowledge.md` | Core concepts and terms |
| `references/css-calculations/rules.md` | Actionable rules and exceptions |
| `references/css-calculations/examples.md` | Bad/good examples and refactoring pattern |
| `references/css-calculations/patterns.md` | Reusable formula patterns |
| `references/css-calculations/checklist.md` | Review checklist and red flags |
| `workflows/debug-css-calculation.md` | Step-by-step workflow |
