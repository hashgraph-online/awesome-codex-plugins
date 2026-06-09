# Container Runtime And Orchestration

## Resource Bounds

| Workload | Request | Limit | OOM Behavior | Eviction Behavior |
| --- | --- | --- | --- | --- |

## Drain Contract

| Workload | Stop Intake Step | In-Flight Completion/Handoff | Deadline | Grace Period Alignment |
| --- | --- | --- | --- | --- |

## Probe Spec

| Workload | Readiness Check | Liveness Check | Startup Check | Thresholds |
| --- | --- | --- | --- | --- |

## Lifecycle Ordering

| Workload | Init Dependency | Sidecar Dependency | Startup Order | Shutdown Order |
| --- | --- | --- | --- | --- |

## Host Lifecycle

| Disruption | Cordon/Drain Step | Capacity Floor | Churn Bound | Owner |
| --- | --- | --- | --- | --- |

## Image And Security Context

| Image | Base | Run-As | Filesystem Mode | Dropped Capabilities | Size/Cold-Start Budget |
| --- | --- | --- | --- | --- | --- |

## Disruption Verification

| Scenario | Expected Behavior | Signal | Stop Condition |
| --- | --- | --- | --- |
