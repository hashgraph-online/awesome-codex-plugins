---
name: anti-ceremony
description: 'Guard outcome work against process overhead. Triggers: RPI pre-Plan guard; explicit "full anti-ceremony audit" requests.'
---
# Anti-Ceremony

Keep work tied to the caller-visible outcome and the proof still needed for it.
The default guard is a single, artifact-free judgment before RPI Plan; the full
honesty audit runs only on an explicit "full anti-ceremony audit" request.

## Prompt

```text
Quick guard. Outcome: "ao gate check lists the probe-coverage row". Proposed
process work: a coverage dashboard and a second audit pass. Remaining proof:
the gate row, green in CI. Stop condition: that gate passes on main.
```

## It's working if

- The response is the YAML shape below and nothing else: no file appears
  under `.agents/`, and no tracker write is issued.
- `reason:` is one sentence, and `parked_process_work:` names the
  dashboard-shaped items.
- A full audit appears only after the caller wrote `full anti-ceremony audit`.

## Quick guard

1. Freeze the caller-visible outcome in one short statement.
2. Park proposed process work that has no concrete consumer, gated subject or
   release decision, observed defect, or retirement condition.
3. Name the implementation or independent proof still missing.
4. Name the condition that ends this traversal.
5. Return `STOP` when the traversal would only create control artifacts or the
   frozen outcome is already sufficiently proved; otherwise return `CONTINUE`.

Progress needs evidence tied to acceptance or a named blocking uncertainty.
Digest movement, finding counts, and additional reviews alone earn no credit.
Informative red can justify a different experiment inside an explicitly selected
outer goal's unchanged acceptance and allowance; repeated no-information work
cannot. Keep required independent proof in `remaining_proof`, including every
necessary unresolved finding. Apply Validate's effect-based risk rule to the
cost of proof; never weaken the exact-subject or all-acceptance PASS bar.

Perform the guard exactly once in memory. Parking is a field in the response,
not a tracker or delivery mutation. Return this shape:

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
decision, observed defect, and retirement condition; return concise keep,
park, or drop findings in the response.

## Boundary

Before returning the decision, read `boundaries.md` in the rpi skill's
`references` directory. On malformed or missing inputs, return `STOP` with
the missing field named in the one-sentence reason.
