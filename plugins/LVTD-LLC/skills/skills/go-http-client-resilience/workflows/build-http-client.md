# Build HTTP Client Workflow

## Steps

### 1. Define the Operation

- [ ] Specify method, path, request/response schemas, auth, and idempotency.
- [ ] Set total deadline, maximum response size, and pagination limits.
- [ ] Choose streaming, bounded materialization, or bounded drain behavior.

### 2. Construct the Boundary

- [ ] Inject a reusable client or `Doer`.
- [ ] Build URLs safely and attach context.
- [ ] Configure transport and redirect policy.
- [ ] Treat `Client.Timeout` as a total redirect-and-body-reading budget.
- [ ] Clone a reviewed transport baseline and set pool limits from expected load.

### 3. Classify Responses

- [ ] Register body cleanup immediately after each successful `Do`, before
      status-specific branches.
- [ ] Close every body and bound every read or drain.
- [ ] Separate success, status, decode, transport, timeout, and cancellation failures.
- [ ] Preserve request IDs and safe operation context.

### 4. Add Resilience

- [ ] Enumerate retryable cases.
- [ ] Require idempotency for mutations.
- [ ] Add capped jittered backoff within the total budget.
- [ ] Respect rate-limit metadata and `Retry-After`.
- [ ] Inject waiting, clock, and jitter sources for deterministic tests.

### 5. Verify

- [ ] Unit-test with a function-backed transport.
- [ ] Test cancellation, oversized bodies, status errors, retry exhaustion, and body closure.
- [ ] Use `httptest.Server` for redirects, streaming, or protocol integration.
- [ ] Load-test connection reuse and pool limits when throughput depends on them.
- [ ] Confirm logs and errors contain no seeded secrets.
- [ ] Test repeated and cross-origin cursors, page/record caps, empty pages with
      a next cursor, per-page body closure, retry deduplication, cancellation
      between pages, and explicit partial-result semantics.

## Exit Criteria

- [ ] Every attempt is bounded by time, size, and retry policy.
- [ ] The operation is deterministic under cancellation and transient failure.
