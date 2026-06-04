# Dependency Resilience Matrix

## Dependency Contract

| Dependency | Operation | Criticality | Timeout | Retry | Idempotency |
| --- | --- | --- | --- | --- | --- |

## Failure Behavior

| Dependency | Circuit Breaker Or Fail-Fast Policy | Fallback | Failure Behavior | Response Path |
| --- | --- | --- | --- | --- |

## Timeout And Retry Budget

| Caller | Dependency | Deadline Budget | Backoff/Jitter | Retryable Conditions | Overload Stop Signal |
| --- | --- | --- | --- | --- | --- |

## External Dependency Signals

| Dependency | Rejection Or Blocking Signal | Provider-State Check | Escalation Path | User-Visible Symptom |
| --- | --- | --- | --- | --- |

## Queue Backpressure And Load Shedding

| Path | Threshold | Synchronous Response | Asynchronous Response | Preserved Traffic |
| --- | --- | --- | --- | --- |

## Degradation Contract

| Dependency Failure | User-Visible Behavior | Data Safety Rule | Alert Or Ticket | Rehearsal Evidence |
| --- | --- | --- | --- | --- |

## Health Checks

| Check | Liveness/Readiness/Startup/Dependency | Failure Behavior | Owner |
| --- | --- | --- | --- |

## Failure-Mode Tests

| Failure Mode | Test Or Experiment | Expected Behavior | Evidence |
| --- | --- | --- | --- |

## Ownership

| Dependency | Provider Owner | Consumer Owner | SLA/SLO Link | Review Cadence |
| --- | --- | --- | --- | --- |
