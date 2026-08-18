# Multi-Region And Data Residency

## Topology And Boundary

| Function | Control Plane Region | Data Plane Region(s) | Loss Blast Radius |
| --- | --- | --- | --- |

## Residency Placement

| Data Class | Permitted Geographies | Processing Bound | Request Pinning Rule |
| --- | --- | --- | --- |

## Replication-Aware Affinity

| Operation/Data Class | Replication Mode | Write Region | Read Region | Required RPO | Lag Signal/Freshness | Session Pinning |
| --- | --- | --- | --- | --- | --- | --- |

## Recoverability Evidence

| Operation/Data Class | Observed Recoverable Point | Checkpoint Evidence | Acknowledged-Write Rule | Fencing/Consistency Boundary | Missing/Divergent-Write Reconciliation | Residual Gap |
| --- | --- | --- | --- | --- | --- | --- |

## Geo-Routing

| Traffic Class | Routing Rule | Unhealthy-Region Behavior | Owner |
| --- | --- | --- | --- |

## Region Evacuation Runbook

| Step | Action | Trigger/Authority | Abort Signal | Evidence |
| --- | --- | --- | --- | --- |

## Residency Under Failover

| Scenario | Compliant Fallback | Accepted Degradation | Owner |
| --- | --- | --- | --- |

## Rehearsal

| Drill | Date/Plan | Result | Gaps |
| --- | --- | --- | --- |
