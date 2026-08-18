# Flexbox Math Guidelines

Quick reference for finding the right file. Load only the files relevant to the task.

## Workflows

| Task | Workflow |
|------|----------|
| Apply or debug flexbox math | `workflows/debug-flex-distribution.md` |

## By Task

| What you're doing | Load these files |
|-------------------|------------------|
| Learn the concepts | `references/flex-distribution/knowledge.md` |
| Apply rules to code | `references/flex-distribution/rules.md`, `references/flex-distribution/examples.md` |
| Derive a reusable formula | `references/flex-distribution/patterns.md`, `references/flex-distribution/rules.md` |
| Review an implementation | `references/flex-distribution/checklist.md`, `references/flex-distribution/rules.md` |
| Trace source coverage | `references/source-map.md` |

## By Code Element

| Working with... | Primary | Secondary |
|-----------------|---------|-----------|
| CSS declarations | `references/flex-distribution/rules.md` | `references/flex-distribution/examples.md` |
| JavaScript calculations | `references/flex-distribution/patterns.md` | `references/flex-distribution/checklist.md` |
| Design tokens or constants | `references/flex-distribution/knowledge.md` | `references/flex-distribution/rules.md` |
| Layout or visual regressions | `references/flex-distribution/checklist.md` | `workflows/debug-flex-distribution.md` |

## By Problem/Symptom

| If you notice... | Load these files |
|------------------|------------------|
| Equal flex values produce unequal widths | `references/flex-distribution/rules.md`, `references/flex-distribution/checklist.md` |
| Long text breaks the row | `references/flex-distribution/rules.md`, `references/flex-distribution/checklist.md` |
| One item stops shrinking | `references/flex-distribution/rules.md`, `references/flex-distribution/checklist.md` |

## Decision Tree

```text
What do you need?
|
|-- Learn the model -> references/flex-distribution/knowledge.md
|-- Fix code now -> references/flex-distribution/rules.md + examples.md
|-- Create a formula -> references/flex-distribution/patterns.md
|-- Review or debug -> workflows/debug-flex-distribution.md + checklist.md
`-- Verify provenance -> references/source-map.md
```

## File Index

| File | Purpose |
|------|---------|
| `SKILL.md` | Skill trigger and minimal usage instructions |
| `guidelines.md` | Routing layer for progressive disclosure |
| `references/source-map.md` | Book citation traceability |
| `references/flex-distribution/knowledge.md` | Core concepts and terms |
| `references/flex-distribution/rules.md` | Actionable rules and exceptions |
| `references/flex-distribution/examples.md` | Bad/good examples and refactoring pattern |
| `references/flex-distribution/patterns.md` | Reusable formula patterns |
| `references/flex-distribution/checklist.md` | Review checklist and red flags |
| `workflows/debug-flex-distribution.md` | Step-by-step workflow |
