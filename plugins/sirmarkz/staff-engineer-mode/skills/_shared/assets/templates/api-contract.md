# API Contract

## Contract Decision

- Surface:
- Compatibility class:
- Planned or existing consumers:
- Primary risks:

## Consumer Impact

| Consumer Class | Request-Construction Surface | Known Signals | Usage | Impact | Migration Contact |
| --- | --- | --- | --- | --- | --- |

## Low-Traffic And Embedded Runtime Paths

| Entry Point | Runtime Or Client Constraint | Expected Request Shape | Telemetry Or Synthetic Check | Compatibility Evidence |
| --- | --- | --- | --- | --- |

## Operation And Resource Shape

| Operation | Resource | Request Shape | Response Shape | Generated-Client Ergonomics |
| --- | --- | --- | --- | --- |

## Compatibility Matrix

| Element | Current Behavior | New Behavior | Surface Parity Check | Compatible? | Migration Rule |
| --- | --- | --- | --- | --- | --- |

## Same-Contract Consumer Transition (When In Scope)

| Changed Element Or Version | Replacement | Old/New Overlap Mechanism | Consumer Cohort And Request Surface | Adoption And Compatibility Signal | Stop Or Rollback Condition | Support Deadline | Removal Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Transport Header Metadata And Callback Parity

| Surface Or Intermediary | Required Transport/Header/Metadata/Field | Consumer Dependency | Preservation Check | Failure Behavior |
| --- | --- | --- | --- | --- |

## Error And Retry Model

| Error | Retryable? | Client Action | Correlation | Redaction |
| --- | --- | --- | --- | --- |

## Idempotency And Bounds

| Mutation Or Collection | Idempotency Key | Page/Batch Limit | Filtering Semantics | Ordering | Rate Limit |
| --- | --- | --- | --- | --- | --- |

## Batch And Bulk Item Correlation (When In Scope)

| Operation | Item Correlation | Per-Item Result/Error | Partial-Success Rule | Whole-Request Rejection |
| --- | --- | --- | --- | --- |

## Malformed Request Isolation

| Operation | Malformed/Unsupported Case | Caller Error | Shared-State Isolation Check | Recovery Needed? |
| --- | --- | --- | --- | --- |

## Fanout And Partial Failure

| Aggregated Operation | Scope Boundary | Unavailable-Scope Behavior | Partial Result Signal | Global Failure Exception |
| --- | --- | --- | --- | --- |

## Polling Avoidance And Quota (When In Scope)

| Consumer Pattern | Expected Volume | Quota Risk | Stream/Export/Bulk/Projection Alternative | Rate-Limit Contract |
| --- | --- | --- | --- | --- |

## Result Metadata Invariants

| Collection Operation | Count/Total/Continuation Field | Payload Match Check | Partial Result Signal | Client Fallback |
| --- | --- | --- | --- | --- |

## Security And Audit Requirements

| Surface | Authentication/Authorization | Audit Event | Sensitive Data Rule | Abuse Control |
| --- | --- | --- | --- | --- |

## Deprecation And Evolution

| Field/Operation | Telemetry | Notice | Removal Check | Deadline |
| --- | --- | --- | --- | --- |
