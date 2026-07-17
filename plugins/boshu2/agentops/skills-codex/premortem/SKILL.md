---
name: premortem
description: Optionally challenge a frozen plan with one
---
# Premortem

Premortem is an optional plan-challenge strategy. It asks one fresh context to
identify concrete ways the resolved bead or caller intent could fail before implementation.
It is not part of the required RPI sequence and does not authorize readiness.

## Workflow

1. Resolve the existing intent source and derive its digest; inspect acceptance,
   non-goals, evidence requirements, and declared write scope there.
2. Use one fresh judge with a context ID distinct from the plan author.
3. Test acceptance completeness, edge behavior, scope, dependencies,
   reversibility, and evidence shape against cited repository facts.
4. Return one complete set of concrete findings and checked/not-checked scope.
5. Stop. The caller decides whether to revise the plan or invoke RPI.

Council or Dueling Idea Genies may be caller-supplied evidence, but Premortem
does not require either strategy and cannot turn consensus into approval.

## Adversarial defeat attempts

Actively try to construct each failure, not imagine it. For every candidate
failure, attempt a concrete defeat: write the input, command sequence, or
repository state that would make the plan fail, and run or cite the check
that shows whether the plan survives it. A finding is reportable as concrete
when it names the defeating construction and what the plan does when it
lands; a failure you could not construct is reported as attempted-and-blocked
with the obstacle named, which is itself evidence for the plan. The named
failure mode is armchair pessimism: a list of imagined risks with no
construction attempts, which reads as diligence while testing nothing. Stop
condition: every reported finding is backed by a defeat attempt — constructed,
or attempted with the blocking fact cited; a finding with neither is deleted,
not softened.

## Boundary

- Emit advisory findings, not `verdict.v2`, readiness, admission, or permission.
- Do not implement, validate the candidate, retry, repair, schedule, claim,
  change acceptance, operate Git, close work, release, or deliver.
- Any plan edit creates a new subject for a later caller-initiated Premortem.

## Output

Return `premortem-plan-review.v1` with the intent digest, author and judge context
IDs, findings, evidence references, `checked`, and `not_checked`. An empty
finding set means only that this optional challenge found no concrete defect;
it is never a lifecycle gate.
