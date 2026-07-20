# Real-Service E2E

Use this reference when mocks would hide the failure mode: auth flows, payment/webhook flows, queues, databases, storage, third-party APIs in sandbox mode, or multiple services with serialization boundaries.

## Safety Gate

Before running real-service tests, prove the target is non-production:

- Test or sandbox credentials only.
- Dedicated test database, bucket, queue, project, or tenant.
- Destructive operations isolated by namespace or transaction rollback.
- Clear cleanup path.
- No live customer data.

If any safety check is unknown, stop and ask for an explicit test environment.

## Pattern

1. Create test-owned resources with unique names.
2. Exercise the full boundary through the public interface.
3. Assert durable state, emitted events, logs, and API responses.
4. Clean up in `defer`, fixture teardown, or transaction rollback.
5. Capture enough evidence to debug failures without rerunning blindly.

## What To Avoid

- Mocking the component whose integration is under test.
- Sharing mutable fixtures across tests.
- Sleeping for fixed durations when polling with timeouts would work.
- Running against production by default.
- Skipping cleanup on failure.

## Output

Record real-service test safety in `.agents/tests/summary.md`:

```markdown
## Real-Service Safety

| Check | Result |
|---|---|
| Non-production credentials | PASS/FAIL |
| Isolated namespace | PASS/FAIL |
| Cleanup verified | PASS/FAIL |
```

---

**Source:** Adapted from an external skill corpus / `testing-real-service-e2e-no-mocks`. Pattern-only, no verbatim text.
