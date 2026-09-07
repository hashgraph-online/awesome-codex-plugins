# Code review checklist

Use only the sections relevant to the diff.

## Correctness

- Boundary conditions, null/empty states, time, and timezone behavior
- Error propagation, retries, cancellation, and cleanup
- State transitions and invariants
- Backward compatibility and default behavior

## API and data

- Request/response and event contract drift
- Authorization at the resource boundary
- Transactions, partial writes, migrations, and rollback
- Pagination, ordering, idempotency, and duplicate delivery

## Concurrency

- Lost updates, races, double execution, and stale reads
- Lock scope and ordering
- Async lifetime, shared mutable state, and cancellation

## Security

- Injection and unsafe parsing
- Authentication and authorization gaps
- Secret or personal-data exposure
- SSRF, path traversal, unsafe redirects, and insecure deserialization
- Permission expansion in CI or infrastructure

## Reliability

- Timeouts and retry storms
- Resource leaks
- Unbounded queues, payloads, or loops
- Degraded dependency behavior

## Tests

- Does a test prove the changed behavior?
- Are meaningful failure and permission cases covered?
- Would the test fail against the original defect?
- Are mocks hiding integration behavior?

## Finding priority

- **Critical:** immediate compromise, broad data loss, or severe availability impact.
- **High:** likely correctness, security, or integrity failure in a normal path.
- **Medium:** real but narrower failure requiring a specific condition.
- **Low:** actionable issue with limited impact; omit preference-only feedback.
