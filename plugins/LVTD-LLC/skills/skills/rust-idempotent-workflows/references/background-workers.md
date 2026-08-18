# Background Workers

Background workers make reliability harder because work can be claimed, retried,
or interrupted independently of the original request.

## Queue Table Shape

Typical durable fields:

- `id`
- `task_type`
- `payload`
- `status`
- `attempt_count`
- `next_attempt_at`
- `locked_by`
- `locked_at`
- `last_error`
- `created_at`
- `updated_at`

Use JSON payloads only when schema evolution and validation are understood.

## Claiming Work

Use database mechanisms that allow multiple workers:

- `FOR UPDATE SKIP LOCKED` for polling workers.
- A leased `locked_at` timestamp so abandoned work can be retried.
- Unique constraints for deduplication.

## Retry Policy

- Classify errors as retryable or terminal.
- Use bounded exponential backoff with jitter when practical.
- Store enough error context for operators without leaking secrets.
- Move permanently failed jobs to a visible state instead of dropping them.

## Outbox Pattern

When a request must update local state and send an external message, commit the
local state and an outbox row in one transaction. A worker sends the external
message and marks the outbox row complete.

This avoids the crash window where the database commits but the process exits
before sending the message, or the message sends but the database rolls back.
