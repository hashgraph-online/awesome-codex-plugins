# Concurrency

Assume duplicate requests can arrive at the same time on different processes.
Application-level checks are not enough when a database is the shared state.

## Preferred Defenses

- Unique constraints for one-per-key invariants.
- Transactions for multi-row state changes.
- `SELECT ... FOR UPDATE` when a workflow must inspect and mutate a row.
- Optimistic version columns when the user can retry conflicts.
- Advisory locks only when the lock key and failure behavior are simple.

## Tests

Write at least one test that submits the same operation concurrently:

```rust
let first = tokio::spawn(send_request(client.clone(), payload.clone()));
let second = tokio::spawn(send_request(client.clone(), payload.clone()));

let (first, second) = tokio::try_join!(first, second)?;
```

Assert durable effects, not just status codes:

- One row was created.
- One email or outbox item exists.
- Both responses are acceptable under the API contract.

## Isolation Notes

Postgres `READ COMMITTED` is often enough when unique constraints enforce the
invariant. Use stronger isolation or explicit locks when the invariant spans
multiple rows and cannot be expressed as a constraint.
