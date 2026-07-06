---
name: rust-idempotent-workflows
description: Use when designing, implementing, testing, or debugging Rust service workflows that must be safe under retries, duplicate requests, crashes, concurrent submissions, background workers, queues, email/payment/notification side effects, idempotency keys, transaction isolation, or save-and-replay API behavior.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Rust Idempotent Workflows
  category: Rust
  tags: rust,idempotency,retries,background-jobs,concurrency
---

# Rust Idempotent Workflows

Use this skill to make Rust workflows reliable when clients retry, workers
crash, requests race, and external side effects cannot be rolled back.

## Core Workflow

1. Write the failure story before writing code. List what happens if the process
   crashes after each database write and after each external side effect.
2. Identify the idempotency boundary: HTTP endpoint, command handler, queue job,
   webhook, or external callback.
3. Choose the idempotency strategy:
   - Natural idempotency from a unique business key.
   - Client-provided idempotency key with save-and-replay.
   - Server-generated deduplication key.
   - Outbox or queue table for side effects.
4. Put state transitions and idempotency records in the same transaction when
   they must agree.
5. Make duplicate concurrent requests deterministic. Use unique constraints,
   locks, serializable transactions, or explicit conflict handling.
6. Treat external side effects as at-least-once unless the provider guarantees
   more. Store enough state to retry or reconcile.
7. Add tests for duplicate requests, retry after timeout, concurrent requests,
   crash windows when practical, and worker retry behavior.

## Idempotency Key Rules

Read `references/idempotency.md` before adding idempotency keys or save-and-
replay behavior.

- Bind the key to the authenticated user or tenant.
- Store a hash of the request payload when replaying responses.
- Return the original response for exact replays.
- Reject reuse of the same key with a different payload.
- Expire records only after product and provider retry windows have passed.

## Background Work Rules

Read `references/background-workers.md` when adding queue tables, polling
workers, retries, or external side effects.

- Commit durable intent before sending external effects.
- Use `pending`, `in_progress`, `succeeded`, and `failed` states deliberately.
- Keep retry counts, next-attempt timestamps, and last error summaries.
- Make workers safe to run in multiple processes.

## Concurrency Rules

Read `references/concurrency.md` when duplicate requests, locks, isolation
levels, or unique constraints are part of the fix.

Use the database as the source of truth for deduplication when multiple app
instances can process the same workflow.

## Reference Files

- `references/idempotency.md`: idempotency keys, save-and-replay, and request
  payload binding.
- `references/background-workers.md`: queue tables, worker loops, retry
  boundaries, and outbox behavior.
- `references/concurrency.md`: lock choices, transaction isolation, and duplicate
  request tests.
