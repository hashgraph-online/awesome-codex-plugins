# Sweep — deciding each candidate route

Load this only from the "Repair the class" section, once the diff-anchored enumeration has produced
its candidates.
Every disposition here is decided by a command's output, never by reasoning about intent.
A candidate that no command can classify takes the fourth row, not a guess.

| Does it reach the defect? (run the reproduction, or its equivalent input, through this site) | Was it correct before? (run this site's existing test, or the invariant, at the base commit) | Disposition |
|---|---|---|
| yes — the symptom reproduces here | — | **Repair here, in this change**, with a case that fails without it. |
| no | yes — its current behavior is right | **Pin it.** Add the assertion that locks its present behavior, or carry a filed follow-up id. Do not rewrite shared code under it; if the shared code must change, route the repair so this site keeps its behavior. |
| no | no — it is wrong in a different way | **Out of scope.** Pin it the same way; a note is not a discharge. |
| cannot run either check | | **Record as unverified** in the receipt, name the command that would decide it, and do not touch it. |

The count is checkable: if the diff changes N symbols and the `routes_into_the_mechanism` field has
fewer than N rows, the enumeration is not finished.
