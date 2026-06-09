# Event Workflow Contract

## Contract

- Producer:
- Consumers:
- Workflow or topic:
- Compatibility policy:

## Producer/Consumer Responsibility

| Party | Responsibility | Failure Response | Owner |
| --- | --- | --- | --- |

## Schema And Compatibility

| Field/Event | Required | Compatibility Rule | Default | Validation |
| --- | --- | --- | --- | --- |

## Trigger Compatibility

| Trigger Or Consumer | Version Boundary | Delayed Event Behavior | Rollback/Fix Behavior | Verification |
| --- | --- | --- | --- | --- |

## Delivery Semantics

| Step | Ordering | Partitioning | Idempotency | Duplicate Handling |
| --- | --- | --- | --- | --- |

## Retry, DLQ, And Replay

| Failure | Retry/Backoff | DLQ Or Poison Path | Replay Method | Manual Repair |
| --- | --- | --- | --- | --- |

## Overload Signals

| Signal | Threshold | Response | Owner |
| --- | --- | --- | --- |

## Queue/Workflow Overload

| Queue/Workflow | Depth | Age | Drain Rate | Consumer Concurrency | Poison Path | Batched-Item Status |
| --- | --- | --- | --- | --- | --- | --- |

## External Side Effects

| Side Effect | Volume Bound | Acceptance Signal | Suppression/Rejection Signal | Rollback Or Throttle |
| --- | --- | --- | --- | --- |

## Observability

| Signal | Age/Lag/Depth/Error/Replay | Source | Alert |
| --- | --- | --- | --- |
