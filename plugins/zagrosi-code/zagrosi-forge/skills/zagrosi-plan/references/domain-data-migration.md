# Domain Pack: Data Migration

Use this when a plan changes schemas, storage models, backfills, data access,
import/export jobs, search indexes, queues, or durable identifiers.

## Evidence To Gather

- Current schema, migrations, indexes, constraints, and access paths.
- Data volume, nullability, uniqueness, and historical edge cases.
- Existing migration tooling and deployment ordering.
- Read/write code paths that must remain compatible.
- Backfill, retry, observability, and rollback conventions.

## Plan Must Decide

- Expand/contract sequence.
- Backward compatibility period and dual-read or dual-write behavior.
- Backfill batching, idempotency, and resume behavior.
- Failure handling and rollback limits.
- Verification queries and data quality checks.
- Operational runbook and owner approval points.

## Tests First

- Migration applies to empty and populated databases.
- Old and new code paths remain compatible during rollout.
- Backfill is idempotent and resumable.
- Invalid or legacy records are handled explicitly.
- Rollback or disable path is documented and tested where practical.
