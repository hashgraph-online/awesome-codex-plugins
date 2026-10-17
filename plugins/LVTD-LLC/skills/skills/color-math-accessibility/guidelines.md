# Color Math Accessibility Guidelines

Quick reference for finding the right file. Load only the files relevant to the task.

## Workflows

| Task | Workflow |
|------|----------|
| Apply or debug color math accessibility | `workflows/audit-color-system.md` |

## By Task

| What you're doing | Load these files |
|-------------------|------------------|
| Learn the concepts | `references/color-systems/knowledge.md` |
| Apply rules to code | `references/color-systems/rules.md`, `references/color-systems/examples.md` |
| Derive a reusable formula | `references/color-systems/patterns.md`, `references/color-systems/rules.md` |
| Review an implementation | `references/color-systems/checklist.md`, `references/color-systems/rules.md` |
| Trace source coverage | `references/source-map.md` |

## By Code Element

| Working with... | Primary | Secondary |
|-----------------|---------|-----------|
| CSS declarations | `references/color-systems/rules.md` | `references/color-systems/examples.md` |
| JavaScript calculations | `references/color-systems/patterns.md` | `references/color-systems/checklist.md` |
| Design tokens or constants | `references/color-systems/knowledge.md` | `references/color-systems/rules.md` |
| Layout or visual regressions | `references/color-systems/checklist.md` | `workflows/audit-color-system.md` |

## By Problem/Symptom

| If you notice... | Load these files |
|------------------|------------------|
| Palette looks balanced but text fails contrast | `references/color-systems/rules.md`, `references/color-systems/checklist.md` |
| Dark mode feels muddy | `references/color-systems/rules.md`, `references/color-systems/checklist.md` |
| Overlay text changes by page section | `references/color-systems/rules.md`, `references/color-systems/checklist.md` |

## Decision Tree

```text
What do you need?
|
|-- Learn the model -> references/color-systems/knowledge.md
|-- Fix code now -> references/color-systems/rules.md + examples.md
|-- Create a formula -> references/color-systems/patterns.md
|-- Review or debug -> workflows/audit-color-system.md + checklist.md
`-- Verify provenance -> references/source-map.md
```

## File Index

| File | Purpose |
|------|---------|
| `SKILL.md` | Skill trigger and minimal usage instructions |
| `guidelines.md` | Routing layer for progressive disclosure |
| `references/source-map.md` | Book citation traceability |
| `references/color-systems/knowledge.md` | Core concepts and terms |
| `references/color-systems/rules.md` | Actionable rules and exceptions |
| `references/color-systems/examples.md` | Bad/good examples and refactoring pattern |
| `references/color-systems/patterns.md` | Reusable formula patterns |
| `references/color-systems/checklist.md` | Review checklist and red flags |
| `workflows/audit-color-system.md` | Step-by-step workflow |
