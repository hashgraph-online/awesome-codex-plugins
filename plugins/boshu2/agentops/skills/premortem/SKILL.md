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
  triggers: ["one judge", "challenge this plan"]
output_contract: skills/premortem/schemas/premortem-plan-review.v1.schema.json
---

# Premortem

Premortem is an optional plan-challenge strategy. It asks one fresh context to
identify concrete ways the resolved bead or caller intent could fail before implementation.
It is not part of the required RPI sequence and does not authorize readiness.
[Plan's shared challenge method](../plan/references/challenge.md) owns optional
exchange, independence and stopping rules; Premortem owns the three checks
below. Neighbours: general advice is [Review](../review/SKILL.md), acceptance
of a finished change is [Validate](../validate/SKILL.md), and several
independent views are [Council](../council/SKILL.md).

Run the checks in this order; they outrank any single technical risk.

## The first check: who verifies, and are they fresh?

Test the plan's evidence shape before any technical risk: for every unit of
work, who verifies it, and is the verifying context distinct from the one that
authored it? A plan whose closure step is "the implementer runs its own tests
and closes" contains no independent judgment anywhere. Self-graded green is the
classic false-done, and it ranks first because it silently converts every other
failure into a shipped one.

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
caller authority is a finding; trace actual undo cost and authorization with
[Plan](../plan/SKILL.md). Prior authorization remains valid: do not demand
repeated approval at the crossing or call every uncertain detail irreversible.
Stop condition: every step carries a mark, and every one-way mark carries its
undo cost.

## The third check: construct the failure

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
   evidence requirements and declared write scope. Its digest is the SHA-256 of
   the exact intent text as supplied (for example `shasum -a 256 plan.md`).
2. Judge from a context that did not write the plan, following the shared
   challenge method for identity, model selection, authorization and bounds. A
   plan the caller wrote can be judged here, with the caller as author. If this
   context wrote the plan and no fresh context can be started, run the checks
   anyway, state that the independence leg is missing, and return inline
   findings; never describe them as independent.
3. Run the three checks, then test acceptance completeness, edge behavior,
   scope and dependencies against cited repository facts. For integration or
   extension plans where anchoring on the working design is the risk, add the
   [derivation-diff challenge](references/derivation-diff.md).
4. Return one complete, bounded set of concrete findings with checked and
   not-checked scope.
5. Stop. The caller decides whether to revise the plan or invoke RPI.

Council or Dueling Idea Genies may be caller-supplied evidence, but Premortem
requires neither and cannot turn consensus into approval.

## Prompt

```text
Premortem this plan before I implement: bead ag-4f21 proposes rewriting
`scripts/regen-all.sh` to call `ao gate check` instead of shelling out to
the Python generators, touching cli/internal/gates/regen.go. Plan and
acceptance are in the bead. Find concrete ways it fails.
```

## It's working if

Observable in the trace, without reading the prose, and the rubric a fresh
independent judge scores this skill against:

- Every unit of work carries a named verifier, and any unit verified by the
  context that authored it comes back as a finding.
- Every step carries a two-way or one-way mark, and each one-way mark names its
  undo cost and its point of no return.
- Every reported finding cites a defeat attempt (the input, command or
  repository state constructed) or the fact that blocked the construction.
- The finding set is bounded: a review that flags every step has reported
  nothing.

## Boundary

- Emit advisory findings, no verdict of any version, readiness, admission, or permission.
- Do not implement, validate the candidate, retry, repair, schedule, claim,
  change acceptance, operate Git, close work, release, or deliver.
- Any plan edit creates a new subject for a later caller-initiated Premortem.

## Output

Return findings inline by default:

```text
Findings (most consequential first)
1. <step> - <how it fails> - <construction, or the fact that blocked it> - <consequence>
Verifiers: <unit>: <who verifies>; self-verified units are findings
One-way steps: <step> - <undo cost> - <point of no return> - <who holds the handle>
Checked: <what was examined>. Not checked: <what was not>.
Independence: <judge context, distinct from author> or "missing: <reason>"
```

When the caller requests a durable review, return `premortem-plan-review.v1`
with the intent digest, author and judge context IDs, findings, evidence
references, `checked`, and `not_checked`, and check it with this skill's
`scripts/validate-output.sh`. The schema requires distinct author and judge
IDs, so a review without an independent judge stays inline. An empty finding
set means only that this optional challenge found no concrete defect; it is
never a lifecycle gate.
