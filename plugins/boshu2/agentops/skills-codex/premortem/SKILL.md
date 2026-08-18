---
name: premortem
description: Optionally challenge a frozen plan with one
---
# Premortem

Premortem is an optional plan-challenge strategy. It asks one fresh context to
identify concrete ways the resolved bead or caller intent could fail before implementation.
It is not part of the required RPI sequence and does not authorize readiness.

## The first check: who verifies, and are they fresh? (MEASURED)

Before any technical risk, test the plan's EVIDENCE SHAPE: for every unit of
work, who verifies it, and is the verifying context distinct from the
authoring context? A plan whose closure step is "the implementer runs its own
tests and closes" contains no independent judgment anywhere — self-graded
green is the classic false-done, and it outranks any single technical risk
because it silently converts every other failure into a shipped one.

> Measured 2026-08-04, probe `premortem-self-validation` (gpt-5.6-luna, N=2,
> directional): without this doctrine loaded the producer named the planted
> self-validation flaw in 1/2 runs; with it loaded, 2/2. Ledger:
> `evals/skill-probes/LEDGER.md`.

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

## Derivation-diff challenge

A challenger that critiques the handed plan is a yes-man with extra steps: it
anchors on the author's design and rationalizes it. Derive independently, then
diff. Give one fresh context ONLY the intent source and the plan's declared
ground truth — the vendor docs and stock behavior for integration work, the
repo's patterns and behavior spec for extension — and never the author's design.
Have it sketch its own design from that ground truth alone. The diff between that
independent design and the working plan is the challenge artifact; each
divergence is a finding to defend or adopt. Convergence is weak evidence the plan
follows the ground truth; divergence names where it may not.

Two questions the challenger answers with an artifact, not an opinion:

- Cathedral: is this the smallest real thing, or does it rebuild what already
  exists? Artifact — the simplest version that satisfies acceptance, plus the
  named reason it is insufficient. No named reason means build the simple one.
- Grain: for integration work, does every component the plan writes have a native
  counterpart in the substrate? Artifact — the native-counterpart list, one row
  per component the plan authors, naming the substrate feature it duplicates or
  the reason none exists.

These are integration- and extension-class checks. The Grain question's
native-counterpart list applies only to integration-class work; do not impose it
on routine feature work.

## Boundary

- Emit advisory findings, no verdict of any version, readiness, admission, or permission.
- Do not implement, validate the candidate, retry, repair, schedule, claim,
  change acceptance, operate Git, close work, release, or deliver.
- Any plan edit creates a new subject for a later caller-initiated Premortem.

## Output

Return `premortem-plan-review.v1` with the intent digest, author and judge context
IDs, findings, evidence references, `checked`, and `not_checked`. An empty
finding set means only that this optional challenge found no concrete defect;
it is never a lifecycle gate.
