# Persistent Connection Systems

## Connection Protocol

| Phase | Behavior | Timeout/Threshold | Owner |
| --- | --- | --- | --- |

## Authentication And Authorization

| Connection/Action/Subscription | Authenticated Or Deliberately Anonymous | Authentication/Principal Binding | Authorization | Anonymous/Public Scope | Abuse/Rate Bounds | Token Expiry/Revocation | Audit/Disconnect Behavior |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Reconnect And Resume

| Event | Backoff Rule | Cursor Scope/Epoch | Replay Retention | Expired-Cursor Behavior | Deduplication/Idempotency | Sequence/Gap Guard | Snapshot/Resync |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Backpressure

| Channel/Connection | Buffer Limit | Overflow Behavior | Slow-Consumer Signal |
| --- | --- | --- | --- |

## Presence And Fanout

| State | Establish | Refresh | Cleanup |
| --- | --- | --- | --- |

## Protocol-Tied Capacity

| Limit | Budget | Lifecycle Decision Protected | Signal | Action Trigger |
| --- | --- | --- | --- | --- |

## Drain On Deploy

| Step | Behavior | Reconnect-Rate Bound | Verification |
| --- | --- | --- | --- |

## Gap Detection

| Stream | Ordering Rule | Gap Signal | Repair/Resume Path |
| --- | --- | --- | --- |
