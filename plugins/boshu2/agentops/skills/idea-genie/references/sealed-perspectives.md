# Sealed perspectives

Loaded by [Idea Genie](../SKILL.md) duel mode when it briefs, compares and
refutes the sealed perspectives.

## Brief

Each prompt carries the frozen question and evidence paths and nothing from a
sibling. It asks the perspective to return:

- the mechanism that sets its approach apart;
- the evidence and the assumptions it rests on;
- its main tradeoff;
- the approaches it considered and rejected, with the reason.

The perspective stops once its mechanism can be set against the frozen
question. It adds detail only where detail could change feasibility or the
choice, and names a decisive assumption it cannot settle instead of guessing
it. Rejected approaches show where perspectives converge; named assumptions
are the first refutation targets in step 4.

## Convergence

When the perspectives share one mechanism and an open decision went
unexplored, start at most one more fresh context within the existing bounds,
aimed at that decision and shown neither the other perspectives nor a favored
answer. There is no second recovery. Report a single remaining mechanism as
the only viable one only with evidence that no other can meet the frozen
constraints; otherwise the comparison stays incomplete.

## State trace

For a stateful mechanism such as a queue, retry, cache, migration or
redelivery, the refutation is a table, not a prose walk-through. Pick one
sequence where a guarantee is at stake and write one row per step with each
relevant state and count after it. A double apply or a lost update shows as a
count the guarantee does not allow.
