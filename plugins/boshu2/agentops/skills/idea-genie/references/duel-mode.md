# Duel mode workflow

Loaded by [Idea Genie](../SKILL.md) for a one-way door, after its door-class
check. `<skill-dir>` and the validator exit codes are as Idea Genie states them.

## Workflow

1. Freeze the question, constraints, evidence paths and comparison rubric.
   Leave unknowns open. An assumption only one approach needs stays with that
   approach; in the shared constraints it would rule rivals out unseen.
2. Generate at least two sealed perspectives under
   [Council's](../../council/SKILL.md#run-a-council) participant, isolation and
   model-pin rules (steps 1 and 2), with each prompt asking for the return in
   [sealed perspectives](sealed-perspectives.md#brief). Record each
   native context id as `context_id` and any pinned profile as
   `model_identity`. If you cannot start two fresh contexts, say so, write no
   packet, and return the open question with the check that would settle it;
   never play a perspective yourself or make up a context id.
3. Reveal the sealed perspectives and cross-review every one on all five of
   evidence, reversibility, system fit, failure modes and cost. Each review
   comes from the reviewing perspective's own context, or from a fresh one
   given only the proposals once that context has closed; never write a
   review under a perspective id yourself.
   Compare perspectives by mechanism, not by name: two that rely on the same
   mechanism count as one alternative, and fewer than two distinct ones is an
   incomplete comparison, not a winner; one bounded recovery is in
   [convergence](sealed-perspectives.md#convergence). A perspective
   that breaks a frozen constraint is out, whatever its other strengths.
   A combination of parts from several perspectives is a new candidate with no
   inherited support: walk one concrete example through each guarantee the
   combined design needs before listing it, or list it as unchecked so Plan
   does not combine on trust.
4. Attempt concrete refutations. A premise of the frozen question that every
   perspective builds on gains no support from their agreement: check it at
   its source. Refute a stateful mechanism with a
   [state trace](sealed-perspectives.md#state-trace), not prose.
   Keep disagreements, failed refutations and minority reasoning explicit, so
   the caller sees the alternatives a synthesis would erase.
5. Return the packet below inline. Write it to a file only at a destination the
   caller names, outside the user's work tree unless the caller asks for a
   path inside it, and check it with
   `bash "<skill-dir>/scripts/validate-challenge.sh" <path | ->`.

```json
{
  "schema_version": "idea-challenge.v1",
  "door_class": "one-way",
  "sealed_generation": true,
  "perspectives": [
    {"id": "P1", "context_id": "<native context id>", "proposal": "<mechanism, evidence, tradeoff>"},
    {"id": "P2", "context_id": "<a different context id>", "proposal": "<mechanism, evidence, tradeoff>"}
  ],
  "cross_reviews": [
    {"reviewer": "P1", "subject": "P2", "dimensions": {"evidence": "<finding>", "reversibility": "<finding>", "system_fit": "<finding>", "failure_modes": "<finding>", "cost": "<finding>"}},
    {"reviewer": "P2", "subject": "P1", "dimensions": {"evidence": "<finding>", "reversibility": "<finding>", "system_fit": "<finding>", "failure_modes": "<finding>", "cost": "<finding>"}}
  ],
  "disagreements": ["<where the perspectives still differ>"],
  "refutations": [{"claim": "<what was attacked>", "attempt": "<the concrete test>", "result": "<what the attempt showed>"}]
}
```

Each perspective has a distinct `id` and `context_id` and a `proposal`, plus
`model_identity` when pinned. Every perspective is the `subject` of at least
one cross-review by another; `dimensions` holds all five rubric keys and no
others, each a text finding. `disagreements` and `refutations` each need at
least one entry. The validator rejects any other field except an optional
legacy `handoff` (`owner` `plan`, `artifact_dir`, optional `route`), which new
packets omit.
