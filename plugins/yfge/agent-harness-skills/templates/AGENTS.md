# Agent Entrypoint Template

Harness role: entrypoint

## Scope

This file applies to `{REPOSITORY_SCOPE}`.

## Source Of Truth

- Product or domain decisions: `{DESIGN_SOURCE}`
- Current work state: `{WORK_STATE_SOURCE}`
- Validation commands: `{VALIDATION_SOURCE}`
- Delivery evidence: `{LEDGER_SOURCE}`

## Agent Rules

- Read this file before making changes in scope.
- Prefer existing project conventions over new abstractions.
- Keep private URLs, credentials, local paths, and account names out of commits.

## Minimum Validation

- Docs-only changes: `{DOCS_CHECK}`
- Code or behavior changes: `{CODE_CHECK}`
- Runtime-sensitive changes: `{RUNTIME_CHECK_OR_REASON}`

## Commit Policy

- Stage exact paths.
- Keep one logical purpose per commit.
- Include related work-state updates when a tracked task is completed, changed, or invalidated.
