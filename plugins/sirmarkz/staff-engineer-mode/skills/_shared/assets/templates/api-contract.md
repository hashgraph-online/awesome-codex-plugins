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

## Transport Header Metadata And Callback Parity

| Surface Or Intermediary | Required Transport/Header/Metadata/Field | Consumer Dependency | Preservation Check | Failure Behavior |
| --- | --- | --- | --- | --- |

## Error And Retry Model

| Error | Retryable? | Client Action | Correlation | Redaction |
| --- | --- | --- | --- | --- |

## Idempotency And Bounds

| Mutation Or List | Idempotency Key | Page/Batch Limit | Ordering | Rate Limit |
| --- | --- | --- | --- | --- |

## Malformed Request Isolation

| Operation | Malformed/Unsupported Case | Caller Error | Shared-State Isolation Check | Recovery Needed? |
| --- | --- | --- | --- | --- |

## Fanout And Partial Failure

| Aggregated Operation | Scope Boundary | Unavailable-Scope Behavior | Partial Result Signal | Global Failure Exception |
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
