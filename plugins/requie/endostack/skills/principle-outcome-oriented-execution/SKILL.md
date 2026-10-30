---
name: principle-outcome-oriented-execution
description: Use during a planned rewrite or migration with declared phases. Aim for a correct, fully checked final state rather than spending effort keeping each intermediate step working with compatibility code you will discard.
disable-model-invocation: true
---

# Outcome-oriented execution

In a planned rewrite or migration, the target is a correct end state you can verify. Effort spent keeping every intermediate step fully functional through disposable compatibility code is wasted.

## When it applies

Rewrites and migrations that were planned ahead and have declared phase boundaries.

It does not apply to unplanned work without declared phases or verification points, or to changes where intermediate breakage would reach users. A migration deployed incrementally to production must keep every step working.

## What to do

1. Put the integrity of the end state ahead of stability during the transition.
2. Allow intermediate breakage only if it was planned in advance, its scope is bounded, and it can be undone.
3. Declare up front, in the plan, where temporary breakage is permitted. For example: "Between phases 2 and 4, the legacy session store tests fail; nothing ships from this branch until phase 4."
4. Keep high-signal checks running on the areas actively being changed.
5. At the end of the plan, demand complete verification, both static checks and runtime checks.

Security checks are never part of the permitted breakage. If the migration moves authentication middleware, the authorization tests for the moved routes stay green at every phase, because a temporary gap there is the kind that ships by accident.

## The failure it prevents

Temporary shims that become permanent debt, and effort spent stabilizing intermediate states nobody will keep.

## Done when

The final state passes complete static and runtime verification.

Each unit still ends in a check ([principle-sequence-verifiable-units](../principle-sequence-verifiable-units/SKILL.md)); this principle only relaxes what that check must cover mid-plan.

Related: [principle-migrate-callers-then-delete-legacy-apis](../principle-migrate-callers-then-delete-legacy-apis/SKILL.md), [principle-sequence-verifiable-units](../principle-sequence-verifiable-units/SKILL.md), [principle-prove-it-works](../principle-prove-it-works/SKILL.md).
