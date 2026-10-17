# Data Migration

Inspect constraints/indexes, callers, real volume/legacy data, tooling, and
deployment order. Decide expand/contract compatibility, batches, idempotency,
checkpoints, invalid-data handling, verification queries, rollback limits, and
authority. Use dual writes only when required.

Verify empty/populated migrations, old/new callers, resumable retries, legacy
records, and rollback/disable paths. Preserve integrity/tenant isolation; separate
reversible code changes from irreversible data transformations.
