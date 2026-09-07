# Backend contracts and data

## Public contracts

- Identify request, response, error, event, and schema consumers.
- Preserve field meaning, status behavior, ordering, pagination, and idempotency unless change is intentional.
- Update source schemas before generated clients or artifacts.
- Add compatibility tests for existing consumers when risk is material.

## Authorization

- Distinguish authentication from authorization.
- Check tenant, owner, role, and resource-level boundaries.
- Avoid trusting client-supplied identity, price, entitlement, or ownership.
- Test both allowed and denied cases.

## Persistence

- Name invariants that must survive failures.
- Use transactions for related writes when supported.
- Consider unique constraints, races, lock scope, retries, and duplicate delivery.
- Avoid read-then-write assumptions without concurrency protection.

## Migrations

- Decide whether old and new code can run during rollout.
- Prefer additive, backward-compatible stages for zero-downtime systems.
- Separate expansion, backfill, code switch, and cleanup when necessary.
- Define rollback or roll-forward behavior before deployment.
- Never run a destructive migration against production as an implicit test.

## External integrations

- Set timeouts.
- Bound retries and use backoff.
- Make retryable operations idempotent.
- Validate signatures and callback authenticity.
- Redact secrets and sensitive payloads from logs.
- Define behavior for partial outages.

## Observability

- Emit actionable errors without exposing sensitive data.
- Preserve request or trace correlation.
- Add metrics for a new critical failure mode when the repository has an established pattern.
