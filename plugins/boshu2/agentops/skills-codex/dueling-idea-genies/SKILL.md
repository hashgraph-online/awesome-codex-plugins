---
name: dueling-idea-genies
description: Challenge a consequential idea with sealed
---
# Dueling Idea Genies

Produce independent challenges for a consequential choice. The result is
advisory evidence for Plan. It never decides whether a plan is ready and never
turns a later optional Premortem challenge into an approval gate.

## Constraints

- Keep generation sealed until every perspective is complete to prevent later
  proposals from anchoring on earlier ones.
- Preserve dissent and concrete refutation attempts because Plan must see alternatives
  that synthesis might otherwise erase.
- Keep reversible choices lightweight because they do not warrant a pane manager,
  messaging service, council, or model-family rule.
- Emit no readiness, approval, quorum, retry, budget, helper, delivery, or
  tracker state because this strategy supplies evidence rather than lifecycle
  authority.

## Workflow

1. Freeze the question, constraints, evidence paths, and comparison rubric.
2. For a one-way door, create at least two fresh contexts with distinct context
   identifiers. Each produces its perspective before any is revealed.
3. Reveal the sealed perspectives and cross-review by evidence, reversibility,
   system fit, failure modes, and cost.
4. Attempt concrete refutations. Preserve disagreements, failed refutations,
   and minority reasoning.
5. Write `idea-challenge.v1`, validate it, and pass the artifact to Plan as one
   optional input alongside research and operator intent.

For a cheap two-way door, emit the lightweight packet directly after one fresh
challenge. Do not manufacture panel ceremony.

## Output Specification

- **Artifact directory:** `.agents/ideas/<run-id>/`
- **Filename:** `idea-challenge.json`
- **Format:** `idea-challenge.v1` JSON with route-specific fields enforced by
  the validator
- **Validation command:**
  `skills/dueling-idea-genies/scripts/validate-output.sh <idea-challenge.json>`
- **Downstream handoff:** `handoff.owner` is exactly `plan`; Plan may accept,
  reject, or combine the advisory evidence

## Quality

- One-way packets prove distinct context IDs and cross-review another
  perspective by named dimensions.
- Dissent and refutation attempts remain explicit.
- The packet contains no semantic readiness field or decision.
- The validator passes before handoff to Plan.

## Do not

- Let perspectives see one another before sealed generation completes.
- Convert consensus, transport availability, or a self-score into readiness.
- Require orchestration infrastructure for a reversible choice.

## References

- [Dueling Idea Genies behavior](references/dueling-idea-genies.feature)
