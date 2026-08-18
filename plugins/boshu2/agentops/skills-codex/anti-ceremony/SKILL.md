---
name: anti-ceremony
description: 'Guard outcome work against process overhead. Triggers: RPI pre-Plan guard; explicit "full anti-ceremony audit" requests.'
---
# Anti-Ceremony

Keep work tied to the caller-visible outcome and the proof still needed for it.
The default guard is a single, artifact-free judgment before RPI Plan.

## Modes

| Trigger | Mode |
|---|---|
| RPI pre-Plan invocation or ordinary use | Quick guard |
| Explicit request for a full anti-ceremony audit | Full honesty audit |

Never promote the quick guard into the full audit without the explicit trigger.

## Quick guard

1. Freeze the caller-visible outcome in one short statement.
2. Park proposed process work that has no concrete consumer, gated subject or
   release decision, observed defect, or retirement condition.
3. Name the implementation or independent proof still missing.
4. Name the condition that ends this traversal.
5. Return `STOP` when the traversal would only create control artifacts or the
   frozen outcome is already sufficiently proved; otherwise return `CONTINUE`.

Perform the guard exactly once in memory. Write no worksheet, ledger, capture,
dashboard, prompt packet, or other hidden artifact. Parking is a field in the
response, not a tracker or delivery mutation.

Return this shape:

```yaml
decision: CONTINUE | STOP
reason: <exactly one sentence>
frozen_outcome: <nonempty string>
parked_process_work: [<work item>, ...]
remaining_proof: [<proof item>, ...]
stop_condition: <nonempty string>
```

The two lists contain strings and may be empty. Done when every field is
present and the decision explains whether one RPI traversal earns its cost.

## Full honesty audit

Run this mode only when the caller explicitly requests it. Examine each named
control artifact or ceremony step for its consumer, gated subject or release
decision, observed defect, and retirement condition. Return concise keep,
park, or drop findings in the response; create no audit artifact unless the
caller separately requests one.

## Boundaries

The guard makes one admission judgment. It does not retry, repair, replan,
dispatch core phases, operate Git or a tracker, deliver, release, or select a
next action. On malformed or missing inputs, return `STOP` with the missing
field named in the one-sentence reason and stop.
