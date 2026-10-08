# Pattern-mining pack contract

Applies only when a durable `pattern-mining.v1` record is selected.

A promotion needs at least three distinct anchored exemplars, a candidate formed
before inspecting a separate holdout, a passing holdout and successful
back-application of every refinement to the original exemplars. Every invariant
needs supporting alignment. Otherwise preserve the result as
`outcome: hypothesis` with `route: no-action`; do not package weak evidence as a rule.

Write `pattern-mining.json` to `.agents/scratch/pattern-mining/<run-id>/` or an
authorized caller location and run
`skills/research/scripts/pattern-mining/validate-output.sh <pattern.json>`.
Preserve the schema's `outcome`, `exemplars`, `invariants`, `variations`,
`incidental`, `holdout`, `back_application` and `route` fields. The
compatibility route value `operationalize` on a valid promotion refers to
[Skill Builder's distillation mode](../../../skill-builder/SKILL.md#distill-expertise);
it is not a retired skill invocation or automatic dispatch. See the
[pattern scenarios](pattern-mining.feature).
