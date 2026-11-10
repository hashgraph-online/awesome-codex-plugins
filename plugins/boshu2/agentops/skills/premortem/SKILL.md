---
name: premortem
description: 'Find how a rollout plan could fail before committing to it. Use when: asked what could go wrong or to poke holes in a plan.'
practices: [design-by-contract, adr]
hexagonal_role: domain
consumes: []
produces: [premortem-plan-review.v1]
context_rel:
- kind: supplier-to
  with: plan
skill_api_version: 1
user-invocable: true
metadata:
  capabilities: [challenge_plan]
  effects: [write_advisory_plan_review]
  canonical_status: canonical
  disposition: keep_strategy
  graph_root: true
  tier: judgment
  dependencies: []
  triggers: ["what could go wrong", "poke holes", "challenge this plan"]
output_contract: schemas/premortem-plan-review.v1.schema.json
---

# Premortem

Before implementation, a context that did not write the plan runs three checks
in order: who verifies each costly unit, which steps are one-way doors, and a
constructed defeat for each premise the plan takes for granted. Report findings
in the same order: a finding from the first or second check outranks any single
technical risk the third check constructs.
Premortem is an optional plan-challenge strategy, outside the required RPI
sequence, and does not authorize readiness.

| Use instead | When |
|---|---|
| [Review](../review/SKILL.md) | general advice on a plan or change |
| [Validate](../validate/SKILL.md) | acceptance of a finished change |
| [Council](../council/SKILL.md) | several independent views |

[Plan's shared challenge method](../plan/references/challenge.md) owns optional
exchange, dispatch and stopping rules; when no fresh context can be started,
step 2's labelled self-judged fallback replaces its no-stand-in rule here.

## The first check: who verifies, and are they fresh?

Test the plan's evidence shape before any technical risk: for every unit of
work, who verifies it? For an ordinary unit the author's checks and CI are the
gate, and that is not a finding
([Validate](../validate/SKILL.md#when-a-fresh-judgment-is-worth-it)). A unit is
costly when it meets a condition on Validate's list (a published release or
user instructions, a security boundary, destroyed data or tracker state, a
deleted protective check, behavior no deterministic check covers) or when a
later one-way step depends on it. The finding is a costly unit whose only
verification is checks its author wrote, with no check the author did not
write and no fresh author-distinct read, as in a closure step "the implementer
runs its own tests and closes" on a unit that guards authentication. Report
the shape once, listing its units.

## The second check: which steps are one-way doors?

Walk the steps and mark each two-way (the plan can back out of it) or one-way
(it cannot). For every one-way step name the exact undo cost, the point of no
return, and who holds the handle when it is crossed: the caller, or an agent
deciding inside a batch. A two-way failure costs a retry; a one-way failure
costs the thing itself. Watch for nineteen reversible steps followed by an
irreversible one, where the reflex trained by the first nineteen answers the
twentieth.

The named failure mode is **reversibility asserted, not traced**: a rollback
section that says "fully reversible" while one step revokes a credential,
force-pushes or publishes. A material irreversible action outside existing
caller authority is a finding; [Plan's Who decides](../plan/SKILL.md#who-decides)
owns undo cost and authorization, and prior authorization stays valid, so do
not demand repeated approval at the crossing or call every uncertain detail
irreversible. Stop condition: every step carries a mark, and every one-way mark
carries its undo cost.

## The third check: construct the failure

Draw candidate failures from what the plan takes for granted, not from a
generic risk list. Typical premises: a tool or service behaving as the plan
describes, the work holding at volumes far above or below what it expects where
volume matters, steps finishing in the stated order and time, and acceptance,
edge behavior, scope and dependencies being complete. Aim first at the decision
other steps rest on, and at any one-way step whose deciding premise is inferred
rather than cited. Name the fact that would show each premise false; when it
can be looked up now, look it up instead of reporting the premise as a risk.

For every candidate failure, attempt a concrete defeat: write the input,
command sequence or repository state that would make the plan fail, and run or
cite the check that shows whether the plan survives it. When execution is not
available, the constructed input or sequence plus a cited fact (file and line,
documented behavior, an observed output) counts as the attempt. A failure you
could not construct is reported as attempted-and-blocked with the obstacle
named, which is itself evidence for the plan. The named failure mode is
armchair pessimism: imagined risks with no construction, which reads as
diligence while testing nothing. A finding with neither a construction nor a
blocking fact is deleted, not softened.

## Workflow

1. Resolve the existing intent source and inspect its acceptance, non-goals,
   evidence requirements and declared write scope.
2. Judge from a context that did not write the plan, following the shared
   challenge method for identity, model selection, authorization and bounds. A
   plan the caller wrote can be judged here, with the caller as author. If this
   context wrote the plan and no fresh context can be started, run the checks
   anyway, state that the independence leg is missing, and return inline
   findings; never describe them as independent.
3. Run the three checks against cited repository facts. For integration or
   extension plans where anchoring on the working design is the risk, add the
   [derivation-diff challenge](references/derivation-diff.md).
4. Return one complete, bounded set of concrete findings with checked and
   not-checked scope, then stop: the caller decides whether to revise the plan
   or invoke RPI.

## It's working if

Observable in the output:

- each unit names its verifier, and self-verification of costly units is one
  finding listing those units; an ordinary unit graded by its author's checks
  and CI is no finding;
- each step is marked, and each one-way mark names its undo cost and point of
  no return;
- each finding cites a defeat attempt or the fact that blocked it;
- the set is bounded: a review that flags every step has reported nothing.

## Boundary

Emit advisory findings, no verdict of any version, readiness, admission or
permission. Do not implement, validate the candidate, retry, repair, schedule,
claim, change acceptance, operate Git, close work, release or deliver. Council
or [Idea Genie](../idea-genie/SKILL.md#duel-mode) duel mode may be
caller-supplied evidence, but Premortem requires neither and cannot turn
consensus into approval. Any plan edit creates a new subject for a later
caller-initiated Premortem.

## Output

Return findings inline by default:

```text
Findings (in check order, then most consequential first within each check)
1. <step> - <how it fails> - <construction, or the fact that blocked it> - <consequence>
Verifiers: <unit>: <who verifies>
Steps: <step>: two-way | one-way - <undo cost> - <point of no return> - <who holds the handle>
Checked: <what was examined>. Not checked: <what was not>.
Independence: <judge context, distinct from author> or "missing: <reason>"
```

When the caller requests a durable review, follow
[durable review](references/durable-review.md) to return and check
`premortem-plan-review.v1`. An empty finding set means only that this
optional challenge found no concrete defect; it is never a lifecycle gate.
