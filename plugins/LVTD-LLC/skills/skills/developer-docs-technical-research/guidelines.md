# Developer Docs Technical Research Guidelines

Load the minimum files needed for the research task.

## By Task

| What you're doing | Load these files |
|-------------------|------------------|
| Researching a feature before docs planning or drafting | `references/core/knowledge.md`, `workflows/research-feature-docs.md` |
| Preparing SME interviews | `references/core/knowledge.md`, `workflows/interview-doc-sources.md` |
| Reconciling conflicting implementation, product, or support facts | `references/core/knowledge.md`, `workflows/research-feature-docs.md` |
| Building a source-of-truth map | `references/core/knowledge.md` |
| Turning research into doc-ready notes | `references/core/knowledge.md`, `workflows/research-feature-docs.md` |
| Deciding whether an oddity should be documented or filed as a product issue | `references/core/knowledge.md` |

## By Problem

| If you notice... | Load these files |
|------------------|------------------|
| Specs explain implementation but not user impact | `workflows/research-feature-docs.md` |
| Engineers, PMs, QA, or support describe different behavior | `workflows/research-feature-docs.md` |
| A draft has many TODOs that need owners | `references/core/knowledge.md` |
| A feature has unclear defaults, limits, permissions, errors, or security effects | `workflows/research-feature-docs.md` |
| SME interviews produce verbal answers but no durable source | `workflows/interview-doc-sources.md` |
| The docs would need to explain a confusing product path | `references/core/knowledge.md` |

## File Index

| File | Purpose |
|------|---------|
| `references/core/knowledge.md` | Research concepts, rules, question bank, red flags, and output patterns |
| `workflows/research-feature-docs.md` | Step-by-step feature research workflow |
| `workflows/interview-doc-sources.md` | Workflow for preparing, running, and closing SME interviews |

## Companion Skills

Use `developer-docs-planning` after research when the next decision is content type, scope, outline, or release plan. Use `developer-docs-editing-review` when the draft exists and the work is technical verification or review.
