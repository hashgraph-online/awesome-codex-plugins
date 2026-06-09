# Domain Pack: Infrastructure And Operations

Use this when a plan touches deployment, CI, cloud resources, queues, caches,
observability, secrets, jobs, service boundaries, or operational runbooks.

## Evidence To Gather

- Existing deployment pipeline and environment layout.
- Infrastructure-as-code modules and ownership boundaries.
- Secret management and configuration conventions.
- Logs, metrics, traces, alerts, and dashboards.
- Runtime limits, scaling assumptions, and failure budgets.
- Rollback, incident, and on-call procedures.

## Plan Must Decide

- Resource ownership and naming.
- Environment rollout order.
- Config and secret migration.
- Observability signals and alert thresholds.
- Failure modes, retries, and degradation behavior.
- Rollback and cleanup procedure.

## Tests First

- CI validates config and infrastructure syntax.
- Unit or integration tests cover retry/degradation logic.
- Smoke tests confirm health and dependency wiring.
- Rollback commands or disable flags are verified in non-production.
