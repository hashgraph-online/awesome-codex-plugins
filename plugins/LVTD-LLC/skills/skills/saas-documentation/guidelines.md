# SaaS Documentation Guidelines

Load the minimum files needed for the SaaS documentation task.

## By Task

| What you're doing | Load these files |
|-------------------|------------------|
| Planning docs for a hosted product or managed service | `references/core/knowledge.md`, `workflows/plan-saas-docs.md` |
| Writing SaaS release notes or upgrade guidance | `references/core/knowledge.md`, `workflows/plan-saas-docs.md` |
| Defining provider-managed versus customer-controlled responsibilities | `references/core/knowledge.md` |
| Creating support, operations, or incident runbooks | `references/core/knowledge.md`, `workflows/create-saas-runbook.md` |
| Reviewing whether public docs and internal docs are release-ready | `references/core/knowledge.md`, `workflows/plan-saas-docs.md` |
| Updating docs after a service, UI, browser, or permission change | `references/core/knowledge.md` |

## By Problem

| If you notice... | Load these files |
|------------------|------------------|
| Docs describe a feature but not customer action or impact | `workflows/plan-saas-docs.md` |
| Customers may all experience a change at the same time | `workflows/plan-saas-docs.md` |
| The docs blur provider and customer responsibilities | `references/core/knowledge.md` |
| Support needs a repeatable procedure for a managed-service issue | `workflows/create-saas-runbook.md` |
| Internal service docs are stale but affect customer support | `workflows/create-saas-runbook.md` |
| Release notes omit browser, UI, permission, billing, or service-limit changes | `references/core/knowledge.md` |

## File Index

| File | Purpose |
|------|---------|
| `references/core/knowledge.md` | SaaS concepts, rules, responsibility matrix, red flags, and examples |
| `workflows/plan-saas-docs.md` | Workflow for customer-facing SaaS docs and release readiness |
| `workflows/create-saas-runbook.md` | Workflow for internal support and operations runbooks |

## Companion Skills

Use `docs-release-maintenance` for general release, maintenance, deprecation, and stale-content work. Use `developer-docs-drafting` when the task is drafting a single page after SaaS scope and responsibilities are clear.
