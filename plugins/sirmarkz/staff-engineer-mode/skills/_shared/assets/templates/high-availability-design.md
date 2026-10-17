# High Availability Design

## Survivability Statement

- Survive loss of:
- While continuing:
- User-visible degradation allowed:

## Fault-Domain Inventory

| Component | Fault Domain | Shared Dependency | Replica/Quorum Placement | Operating-Envelope/Threshold Mismatch |
| --- | --- | --- | --- | --- |

| Component | Health/Control-Loop Dependency | Hidden Coupling | Mitigation |
| --- | --- | --- | --- |

## Capacity Model

| Scenario | Required Capacity | Available Capacity | Cache/Refill Load | Quota/Limit | Gap |
| --- | --- | --- | --- | --- | --- |

## Blast Radius And Isolation

| Fault Domain | Blast Radius | Partition/Shard/Tenant Isolation | Hidden Dependency | Exception |
| --- | --- | --- | --- | --- |

## DNS And Name Resolution

| Name | Authoritative Source | Resolver Path | TTL/Negative Cache | Failover Behavior | Single-Provider Exception |
| --- | --- | --- | --- | --- | --- |

## Failover Decision Record

| Trigger | Authority | Data Behavior | Rollback | Evidence |
| --- | --- | --- | --- | --- |

## Return To Normal

| Path | Recovery Step | Dependency | Last Validation | Gap |
| --- | --- | --- | --- | --- |

## Protective Mode Behavior

| Safety State | Protected Contract | Internal Coordination Needed | Override Criteria | Recovery Risk |
| --- | --- | --- | --- | --- |

## Health And Traffic Shift

| Fault Domain | Health Signal | Gray-Failure Threshold | Report Fanout/Control-Plane Load | Trigger | Traffic Action | Last Validation |
| --- | --- | --- | --- | --- | --- | --- |

## Validation Plan

| Test | Scope | Abort Criteria | Telemetry | Capture |
| --- | --- | --- | --- | --- |
