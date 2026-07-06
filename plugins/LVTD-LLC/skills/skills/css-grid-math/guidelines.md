# CSS Grid Math Guidelines

Quick reference for finding the right file. Load only the files relevant to the task.

## Workflows

| Task | Workflow |
|------|----------|
| Apply or debug css grid math | `workflows/debug-grid-layout.md` |

## By Task

| What you're doing | Load these files |
|-------------------|------------------|
| Learn the concepts | `references/grid-layout/knowledge.md` |
| Apply rules to code | `references/grid-layout/rules.md`, `references/grid-layout/examples.md` |
| Derive a reusable formula | `references/grid-layout/patterns.md`, `references/grid-layout/rules.md` |
| Review an implementation | `references/grid-layout/checklist.md`, `references/grid-layout/rules.md` |
| Trace source coverage | `references/source-map.md` |

## By Code Element

| Working with... | Primary | Secondary |
|-----------------|---------|-----------|
| CSS declarations | `references/grid-layout/rules.md` | `references/grid-layout/examples.md` |
| JavaScript calculations | `references/grid-layout/patterns.md` | `references/grid-layout/checklist.md` |
| Design tokens or constants | `references/grid-layout/knowledge.md` | `references/grid-layout/rules.md` |
| Layout or visual regressions | `references/grid-layout/checklist.md` | `workflows/debug-grid-layout.md` |

## By Problem/Symptom

| If you notice... | Load these files |
|------------------|------------------|
| fr columns are not equal | `references/grid-layout/rules.md`, `references/grid-layout/checklist.md` |
| Item is one column off | `references/grid-layout/rules.md`, `references/grid-layout/checklist.md` |
| auto-fill leaves empty columns | `references/grid-layout/rules.md`, `references/grid-layout/checklist.md` |

## Decision Tree

```text
What do you need?
|
|-- Learn the model -> references/grid-layout/knowledge.md
|-- Fix code now -> references/grid-layout/rules.md + examples.md
|-- Create a formula -> references/grid-layout/patterns.md
|-- Review or debug -> workflows/debug-grid-layout.md + checklist.md
`-- Verify provenance -> references/source-map.md
```

## File Index

| File | Purpose |
|------|---------|
| `SKILL.md` | Skill trigger and minimal usage instructions |
| `guidelines.md` | Routing layer for progressive disclosure |
| `references/source-map.md` | Book citation traceability |
| `references/grid-layout/knowledge.md` | Core concepts and terms |
| `references/grid-layout/rules.md` | Actionable rules and exceptions |
| `references/grid-layout/examples.md` | Bad/good examples and refactoring pattern |
| `references/grid-layout/patterns.md` | Reusable formula patterns |
| `references/grid-layout/checklist.md` | Review checklist and red flags |
| `workflows/debug-grid-layout.md` | Step-by-step workflow |
