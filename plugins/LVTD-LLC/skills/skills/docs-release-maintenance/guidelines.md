# Docs Release Maintenance Guidelines

Load the minimum files needed for the task.

## By Task

| What you're doing | Load these files |
|-------------------|------------------|
| Planning docs for a software release | `references/core/knowledge.md`, `workflows/plan-doc-release-maintenance.md` |
| Creating a publishing checklist | `references/core/knowledge.md` |
| Assigning docs ownership or freshness checks | `references/core/knowledge.md` |
| Setting up maintenance automation | `references/core/knowledge.md` |
| Refreshing existing docs after drift, feedback, or product evolution | `references/core/knowledge.md`, `workflows/refresh-existing-docs.md` |
| Deciding whether to patch or restructure stale content | `references/core/knowledge.md`, `workflows/refresh-existing-docs.md` |
| Planning SaaS release docs, upgrade notes, or internal runbooks | `references/core/knowledge.md`, `workflows/plan-doc-release-maintenance.md` |
| Deprecating or deleting docs | `references/core/knowledge.md`, `workflows/plan-doc-release-maintenance.md` |

## By Problem

| If you notice... | Load these files |
|------------------|------------------|
| Docs are planned after code freeze | `references/core/knowledge.md` |
| Release notes omit user impact or required action | `references/core/knowledge.md` |
| No owner exists for high-risk docs | `references/core/knowledge.md` |
| The team wants to delete stale docs without redirects | `workflows/plan-doc-release-maintenance.md` |
| Patch additions have made a topic long, brittle, or hard to scan | `workflows/refresh-existing-docs.md` |
| A small product change affects related docs in other sections | `workflows/refresh-existing-docs.md` |
| SaaS users need to know what changed, what is managed, and what they control | `references/core/knowledge.md` |

## File Index

| File | Purpose |
|------|---------|
| `references/core/knowledge.md` | Core concepts, rules, checks, examples, and patterns |
| `workflows/plan-doc-release-maintenance.md` | Step-by-step workflow |
| `workflows/refresh-existing-docs.md` | Workflow for stale content, patch buildup, and dependency audits |
