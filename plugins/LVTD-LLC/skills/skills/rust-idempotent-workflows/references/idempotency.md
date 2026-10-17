# Idempotency

Idempotency means a client can safely retry the same operation and observe the
same effect. It does not mean every endpoint should ignore duplicates.

## Strategy Choices

Natural idempotency:

- `PUT /resource/{id}` where the payload fully replaces state.
- Confirming an already-confirmed subscription.
- Creating a unique resource keyed by a natural unique constraint.

Idempotency key:

- Payment-like operations.
- Email or notification dispatch requests.
- Endpoint creates a resource and returns generated data.

Outbox:

- A database change must trigger an external side effect.
- The side effect cannot be rolled back with the database transaction.

## Save And Replay

Store:

- User or tenant ID.
- Idempotency key.
- Request payload hash.
- Response status and body when complete.
- State: `pending`, `completed`, `failed`.
- Expiration timestamp.

On repeat:

- Same key and same payload: return stored response or wait/retry according to
  project policy if still pending.
- Same key and different payload: return conflict.
- Missing key on an endpoint that requires it: return bad request.

## Tests

- Same key and same payload returns the same result.
- Same key and different payload is rejected.
- Concurrent duplicate requests create one durable effect.
- Retry after a simulated timeout does not send duplicate external effects.
