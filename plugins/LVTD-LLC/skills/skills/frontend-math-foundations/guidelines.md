# Frontend Math Foundations Guidelines

Quick reference for finding the right file. Load only the files relevant to the task.

## Workflows

| Task | Workflow |
|------|----------|
| Apply or debug frontend math foundations | `workflows/choose-math-approach.md` |

## By Task

| What you're doing | Load these files |
|-------------------|------------------|
| Learn the concepts | `references/math-foundations/knowledge.md` |
| Apply rules to code | `references/math-foundations/rules.md`, `references/math-foundations/examples.md` |
| Derive a reusable formula | `references/math-foundations/patterns.md`, `references/math-foundations/rules.md` |
| Review an implementation | `references/math-foundations/checklist.md`, `references/math-foundations/rules.md` |
| Trace source coverage | `references/source-map.md` |

## By Code Element

| Working with... | Primary | Secondary |
|-----------------|---------|-----------|
| CSS declarations | `references/math-foundations/rules.md` | `references/math-foundations/examples.md` |
| JavaScript calculations | `references/math-foundations/patterns.md` | `references/math-foundations/checklist.md` |
| Design tokens or constants | `references/math-foundations/knowledge.md` | `references/math-foundations/rules.md` |
| Layout or visual regressions | `references/math-foundations/checklist.md` | `workflows/choose-math-approach.md` |

## By Problem/Symptom

| If you notice... | Load these files |
|------------------|------------------|
| Formula works only for one viewport | `references/math-foundations/rules.md`, `references/math-foundations/checklist.md` |
| CSS and JS duplicate the same calculation | `references/math-foundations/rules.md`, `references/math-foundations/checklist.md` |
| Layout math is hard to explain | `references/math-foundations/rules.md`, `references/math-foundations/checklist.md` |

## Decision Tree

```text
What do you need?
|
|-- Learn the model -> references/math-foundations/knowledge.md
|-- Fix code now -> references/math-foundations/rules.md + examples.md
|-- Create a formula -> references/math-foundations/patterns.md
|-- Review or debug -> workflows/choose-math-approach.md + checklist.md
`-- Verify provenance -> references/source-map.md
```

## File Index

| File | Purpose |
|------|---------|
| `SKILL.md` | Skill trigger and minimal usage instructions |
| `guidelines.md` | Routing layer for progressive disclosure |
| `references/source-map.md` | Book citation traceability |
| `references/math-foundations/knowledge.md` | Core concepts and terms |
| `references/math-foundations/rules.md` | Actionable rules and exceptions |
| `references/math-foundations/examples.md` | Bad/good examples and refactoring pattern |
| `references/math-foundations/patterns.md` | Reusable formula patterns |
| `references/math-foundations/checklist.md` | Review checklist and red flags |
| `workflows/choose-math-approach.md` | Step-by-step workflow |
