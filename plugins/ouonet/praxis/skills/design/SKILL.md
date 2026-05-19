---
name: design
description: Use for standard or complex new work before coding or planning.
---
# Design

`<gate>` No code until user approves the spec. `</gate>`

Ask one question per turn until you know what to build. Propose 2-3 approaches with trade-offs; recommend one. Then write the spec.

## Spec = list of decisions

A spec answers the open questions for THIS change. Typical:
- contract / interface?
- data shape?
- failure modes?
- out of scope?
- what test proves it?
- architecture? 

Do spec idiomatically.

**No question -> no section.** Don't fill "Risks" / "Non-goals" if empty.

Use declarations, not narrative:
```
contract:  <interface>
invariant: <what must hold>
test:      <how we'll know>
deferred:  <not deciding now>
```

Reference code by path; never paste it.

Before handoff, close only decisions that affect implementation: contract, data, failure, test. Unresolved `Working notes` in those areas become decisions, `deferred`, or questions.

## Two layers, one file: `docs/staging/specs/YYYY-MM-DD-<topic>.md`
- Top: decisions, contracts, invariants (permanent).
- `## Working notes`: scratch, open questions (stripped at `ship`).


## Gates
`<gate>`

1. `docs/staging/specs/YYYY-MM-DD-<topic>.md` must exist on disk before handing off to `plan`.
2. Confirm with the user.

`</gate>`