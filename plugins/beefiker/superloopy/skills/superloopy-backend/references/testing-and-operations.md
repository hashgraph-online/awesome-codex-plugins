# Testing and operations

Validation must prove the defined contract and failure semantics in the project's actual operating model. Passing a unit test, benchmark, or single fixture is not production evidence.

## Build layered evidence

- Run pure unit tests for local invariants and serialization.
- Run contract, integration, migration, and failure tests for every affected boundary. Include malformed inputs, denied authorization, cross-tenant attempts, duplicate operation IDs, timeouts, cancellations, partial dependencies, pool reuse, and adversarial retrieved content.
- Exercise transaction, isolation, query, constraint, concurrency, and migration behavior against a disposable real database with the production driver and pooling mode when feasible. Keep fixtures synthetic and secrets out of output.
- Prove forward and backward compatibility across the application/schema versions that coexist during rollout. Test upgrade, pause, resume, and the chosen rollback or roll-forward path.
- For natural-language queries, test semantic postconditions and multiple representative datasets. Execution success on one fixture does not prove user intent.

If a disposable environment is unavailable, run the safe static and isolated checks, state which behavior remains unproved, and do not claim database, migration, or tenant safety.

## Observe and control the running system

Define observability around user-visible outcomes and boundary decisions: structured logs, metrics, traces, health signals, and alerts tied to an owner and response. Correlate trace and audit records with operation IDs while redacting protected inputs and outputs and restricting retention and access.

Use bounded retries only for classified transient failures. Bound attempts, elapsed time, backoff, concurrency, and total work. Do not retry validation, authorization, conflict, destructive, or ambiguous write outcomes as if they were transient. Reconcile ambiguous outcomes against durable operation state before deciding to retry, complete, compensate, or escalate.

Collect performance evidence with representative data shape, concurrency, driver and pool mode, query plans or equivalent diagnostics, and agreed budgets. Record baseline and changed latency, throughput, resource use, result size, and lock or contention effects; synthetic benchmarks are scoped signals, not certification.

## Roll out and recover

Define rollout stages, version order, cohort size, feature or capability gates, health indicators, abort thresholds, data reconciliation, and the person or team authorized to proceed. Rehearse recovery at the proportional level: restore, replay, compensation, rollback, or roll-forward. Verify that operators can observe intermediate states and stop new work safely.

The minimum completion report contains:

- context, change classification, contracts, and assumptions;
- changed behavior and compatibility impact;
- exact validation commands and results, including real-database coverage;
- authorization, tenant, bounds, and adversarial-data evidence;
- performance evidence and remaining capacity assumptions;
- rollout stages, recovery path, monitoring, and owners;
- the project's own checks and definition of done: which conventions, hooks, linters, formatters, or generated-artifact regenerations were run, and their results;
- unresolved risks, missing production authority, evidence gaps, and blockers.

Claims in the completion report must be no broader than the evidence collected.
