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
4. Preserve failure evidence before cleanup can erase it, then clean up in
   `defer`, fixture teardown, or a verified transaction rollback.
5. Verify cleanup and retain enough evidence to debug failures without rerunning
   blindly; a failed teardown is an unresolved result.

## What To Avoid

- Mocking the component whose integration is under test.
- Sharing mutable fixtures across tests.
- Sleeping for fixed durations when polling with timeouts would work.
- Running against production by default.
- Skipping cleanup on failure.

## Output

Return the environment and isolation checks, command/results, cleanup outcome
and material gaps through the existing handoff, following
[Test's output contract](../SKILL.md#output-specification). Persist reports only
when requested or required by a declared consumer, at the caller's explicitly
selected destination. This reference creates no `.agents/` output requirement.
Local instructions and authorized write scope outrank any optional template.
Preserve necessary failure and recovery evidence at its authorized source;
cleanup of test resources does not authorize deleting unique evidence.

---

**Source:** Adapted from an external skill corpus / `testing-real-service-e2e-no-mocks`. Pattern-only, no verbatim text.
