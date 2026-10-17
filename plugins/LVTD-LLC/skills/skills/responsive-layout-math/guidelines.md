# Responsive Layout Math Guidelines

Quick reference for finding the right file. Load only the files relevant to the task.

## Workflows

| Task | Workflow |
|------|----------|
| Apply or debug responsive layout math | `workflows/design-fluid-layout.md` |

## By Task

| What you're doing | Load these files |
|-------------------|------------------|
| Learn the concepts | `references/fluid-layouts/knowledge.md` |
| Apply rules to code | `references/fluid-layouts/rules.md`, `references/fluid-layouts/examples.md` |
| Derive a reusable formula | `references/fluid-layouts/patterns.md`, `references/fluid-layouts/rules.md` |
| Review an implementation | `references/fluid-layouts/checklist.md`, `references/fluid-layouts/rules.md` |
| Trace source coverage | `references/source-map.md` |

## By Code Element

| Working with... | Primary | Secondary |
|-----------------|---------|-----------|
| CSS declarations | `references/fluid-layouts/rules.md` | `references/fluid-layouts/examples.md` |
| JavaScript calculations | `references/fluid-layouts/patterns.md` | `references/fluid-layouts/checklist.md` |
| Design tokens or constants | `references/fluid-layouts/knowledge.md` | `references/fluid-layouts/rules.md` |
| Layout or visual regressions | `references/fluid-layouts/checklist.md` | `workflows/design-fluid-layout.md` |

## By Problem/Symptom

| If you notice... | Load these files |
|------------------|------------------|
| Layout jumps too abruptly | `references/fluid-layouts/rules.md`, `references/fluid-layouts/checklist.md` |
| 100vh section cuts off on mobile | `references/fluid-layouts/rules.md`, `references/fluid-layouts/checklist.md` |
| Nested columns are unexpectedly narrow | `references/fluid-layouts/rules.md`, `references/fluid-layouts/checklist.md` |

## Decision Tree

```text
What do you need?
|
|-- Learn the model -> references/fluid-layouts/knowledge.md
|-- Fix code now -> references/fluid-layouts/rules.md + examples.md
|-- Create a formula -> references/fluid-layouts/patterns.md
|-- Review or debug -> workflows/design-fluid-layout.md + checklist.md
`-- Verify provenance -> references/source-map.md
```

## File Index

| File | Purpose |
|------|---------|
| `SKILL.md` | Skill trigger and minimal usage instructions |
| `guidelines.md` | Routing layer for progressive disclosure |
| `references/source-map.md` | Book citation traceability |
| `references/fluid-layouts/knowledge.md` | Core concepts and terms |
| `references/fluid-layouts/rules.md` | Actionable rules and exceptions |
| `references/fluid-layouts/examples.md` | Bad/good examples and refactoring pattern |
| `references/fluid-layouts/patterns.md` | Reusable formula patterns |
| `references/fluid-layouts/checklist.md` | Review checklist and red flags |
| `workflows/design-fluid-layout.md` | Step-by-step workflow |
