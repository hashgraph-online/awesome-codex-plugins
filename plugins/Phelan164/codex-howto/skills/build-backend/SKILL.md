---
name: build-backend
description: Build or modify backend APIs, services, jobs, persistence, and integrations while preserving contracts, authorization, data integrity, and failure behavior. Use for server-side features, database changes, background processing, backend defects, and service refactors; do not use for frontend-only or infrastructure-only work.
---

# Build Backend

## Domain contract

- Trace changed behavior from input through validation, authorization, domain
  logic, persistence, side effects, and response mapping.
- Preserve published contracts unless the request explicitly changes them.
- Enforce authorization at a trustworthy server-side boundary.
- Validate untrusted input before domain or persistence operations.
- Keep multi-write operations atomic where partial state would violate invariants.
- Design external calls for timeouts, retries, idempotency, and duplicate delivery where applicable.
- Do not query or mutate production data without explicit authorization.
- Do not fabricate migration, framework, or API behavior; verify version-sensitive details.
- Avoid broad service abstractions that are used once.

## Execute and verify

Read [references/contracts-and-data.md](references/contracts-and-data.md) when the task changes a public API, schema, transaction, job, or integration.

Implement the smallest change at the owning layer. Cover success, invalid
input, authorization, and material failure paths. Prefer:

```text
reproducing/focused test → contract/integration test → type/lint → build
```

For migrations, validate forward behavior and document rollback or roll-forward strategy.
