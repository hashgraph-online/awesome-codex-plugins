# Data Pipeline Reliability Plan

## Pipeline Scope

- Source:
- Sink:
- Freshness target:
- Correctness target:
- Critical-path provisioning/control-data dependency:

## Pipeline SLI/SLO

| Journey/Dataset | SLI | SLO | Measurement Source | Missing-Signal Behavior |
| --- | --- | --- | --- | --- |

## Dataset Responsibility And Lineage

| Dataset | Owner | Upstream Source | Downstream Consumer | Transformation |
| --- | --- | --- | --- | --- |

## Stateful Streaming Features

| Feature | Expected Output Signal | Silent-Failure Detection | Recovery Or Restart Path | Consumer Impact |
| --- | --- | --- | --- | --- |

## Freshness And Quality Signals

| Signal | Source | Threshold | Missing-Signal Behavior | Owner |
| --- | --- | --- | --- | --- |

## Validation And Publish Checks

| Check | Blocks Publish? | Failure Response | Evidence |
| --- | --- | --- | --- |

## Runtime-Expanded Destinations

| Destination Template | Runtime Parameter | Compatibility Example | Validation | Replay For Missed Runs |
| --- | --- | --- | --- | --- |

## Replay And Idempotency

| Stage | Idempotency Key | Replay Method | Duplicate Handling | Verification |
| --- | --- | --- | --- | --- |

## Backlog Recovery And Fairness

| Queue Or Propagation Path | Critical-Path Dependency | Shared Persistence/Indexing Dependency | Backlog Age Signal | Drain Rate | Owner |
| --- | --- | --- | --- | --- | --- |

| Queue Or Propagation Path | Recovery Behavior | Recovery Side Effect | Fairness/Rate Limit | Non-Critical Shed/Disable Path |
| --- | --- | --- | --- | --- |

## Late, Bad, Or Missing Data

| Failure | Detection | Quarantine/DLQ | Repair Path | User Impact |
| --- | --- | --- | --- | --- |

## Backfill Runbook

| Step | Throttle | Checkpoint | Abort | Validation |
| --- | --- | --- | --- | --- |

## Consumer Impact And Recovery Tests

| Consumer | Impact | Notification Path | Recovery Test Or Plan | Gap |
| --- | --- | --- | --- | --- |
