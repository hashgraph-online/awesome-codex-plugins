---
name: discover
description: Use when the goal is vague or vision-level and can't be defined well enough for design questions.
---
# Discover

`<gate>` No design, no code, no spec until "confirmed direction" is filled and user confirms. `</gate>`

The goal of discover is to turn a vague goal into a problem statement concrete enough for `design`. Ask one question per turn.

## Discovery note: `docs/discovery/YYYY-MM-DD-<topic>.md`

```markdown
## Goal
<original vague goal>

## Hypotheses
- [ ] <hypothesis A>
- [x] <hypothesis B> → validated: <evidence>
- [~] <hypothesis C> → invalidated: <reason>

## Investigation plan
Contingent steps — update as findings arrive. Not a build plan.
- [x] Phase 1: <what> → <what to decide after>
- [ ] Phase 2: <what> (scope determined by Phase 1)

## Experiments
### YYYY-MM-DD — <experiment name>
what: <what was done>
saw:  <what was observed>
conclusion: <what this means>

## Confirmed direction
<fill one of:>
- problem statement: who / what problem / what context / success signal
- knowledge spec: data structures, protocols, or system behavior confirmed

## Ruled out
- <idea> — <why ruled out>
```

Discovery notes accumulate across sessions. Check existing notes before starting.

## Spike code: `spikes/YYYY-MM-DD-<topic>/`

Spike code validates a hypothesis, not a feature.

- Each spike has a `README.md` stating which hypothesis it tests.
- No tests required.
- No coupling to main code paths.
- Deleted when discovery ends (learnings stay in the note).
- If spike code is worth keeping, it must go through `design → plan → tdd` — no direct promotion.

## Gate

`<gate>`
`docs/discovery/YYYY-MM-DD-<topic>.md` must exist with "Confirmed direction" filled.

Then choose the exit with the user:

- **→ design**: direction is a problem to solve — hand off to `design`, referencing the discovery note.
- **→ archive**: direction is a knowledge artifact (RE findings, protocol spec, data structure map) — save to `docs/discovery/<topic>-spec.md`, no design needed.
`</gate>`

## Abandon

If the user decides not to proceed:

1. Append to the discovery note:
   ```
   ## Abandoned — YYYY-MM-DD
   reason: <why>
   validated: <what was confirmed>
   invalidated: <what was ruled out>
   ```
2. Delete `spikes/<topic>/` — learnings are in the note.
3. No staging spec, no plan, no ship needed.
4. Discovery note stays in `docs/discovery/` permanently as a record.
