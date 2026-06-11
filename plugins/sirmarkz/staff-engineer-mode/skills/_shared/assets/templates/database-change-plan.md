# Database Change Plan

## Change Summary

- Database or store:
- Change type:
- Critical path:
- Rollback or forward-fix posture:

## Risk Assessment

| Risk | Lock/Lag/Plan Evidence | Impact | Mitigation | Stop Condition |
| --- | --- | --- | --- | --- |

## Critical-Path Database Risk

| Surface | Risk | Current Evidence | Mitigation |
| --- | --- | --- | --- |
| Failover |  |  |  |
| Replica/site dependency behavior |  |  |  |
| Connection limits |  |  |  |
| Session establishment |  |  |  |
| Metadata/control-plane health |  |  |  |
| Sequence/counter headroom |  |  |  |
| Query tail latency |  |  |  |
| Restore readiness |  |  |  |
| Write behavior |  |  |  |

## Data Migration Compatibility

| Source Version | Target Version | Capture Or Dump Mode | Writes During Copy | Consistency Validation | Fallback |
| --- | --- | --- | --- | --- | --- |

## Schema Permission Compatibility

| Object Or Query Path | Caller Identity | Required Permission Or Grant | Verification | Failure Response |
| --- | --- | --- | --- | --- |

## Phases

| Phase | Action | Confirmation Point | Abort/Rollback | Owner |
| --- | --- | --- | --- | --- |

## Backfill Or Maintenance

| Batch | Throttle | Checkpoint | Pause/Abort | Verification Query |
| --- | --- | --- | --- | --- |

## Monitoring

| Signal | Threshold | Owner | Response |
| --- | --- | --- | --- |

## Verification Invariants

| Query Or Invariant | Expected Result | When Run | Failure Response |
| --- | --- | --- | --- |

## Rollback Or Forward-Fix Decision

| Condition | Decision | Reason | Evidence |
| --- | --- | --- | --- |

## Cleanup Plan

| Cleanup Item | Delay | Check | Owner |
| --- | --- | --- | --- |
