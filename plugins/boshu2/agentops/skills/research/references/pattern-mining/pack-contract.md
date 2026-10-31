# Pattern-mining pack contract

Applies only when a durable `pattern-mining.v1` record is selected.
`<skill-dir>` is defined in [SKILL.md](../../SKILL.md).

A promotion needs at least three independent lineages, one anchored exemplar
each (copies and ports of one source count once, under Research's
[evidence rules](../../SKILL.md#evidence-rules)), a candidate formed before
inspecting a separate holdout, a passing holdout and successful
back-application of every refinement to the original exemplars. Every invariant
needs supporting alignment. Otherwise preserve the result as
`outcome: hypothesis` with `route: no-action`; do not package weak evidence as a rule.

Save `pattern-mining.json` by Research's
[save rule](../../SKILL.md#output-and-boundaries) and run
`bash "<skill-dir>/scripts/pattern-mining/validate-output.sh" <pattern.json>`.
A hypothesis record has this shape (`<...>` is a value to fill):

```json
{
  "schema_version": "pattern-mining.v1",
  "outcome": "hypothesis",
  "exemplars": ["<first file:line>", "<second file:line>"],
  "invariants": ["<what every exemplar shares>"],
  "variations": ["<legitimate difference>"],
  "incidental": ["<syntax or naming>"],
  "holdout": {"source": "<file:line not among exemplars, or empty>", "result": "not-run"},
  "back_application": "not-run",
  "route": "no-action",
  "shape": "no-action"
}
```

`holdout.result` is `pass`, `fail`, `inconclusive` or `not-run`;
`back_application` is `pass`, `fail` or `not-run`. A promotion sets
`outcome: "promote"`, `route: "operationalize"` and both results to `pass`.
The recommended `shape` (`no-action`, `reference-line`, `template`, `helper`
or `gate`) and the demonstrated `cost` of violation are optional, and a
`gate` needs `outcome: promote` and a `cost`. The validator checks that
exemplar strings differ, not that their lineages are independent: list copies
under their source, not as exemplars.

`route` is a compatibility field. `operationalize` marks a valid promotion and
dispatches nothing; what to build is `shape`, and a helper, template or gate
stays with the caller. Packaging a promoted pattern as a skill is
[Skill Builder's distillation mode](../../../skill-builder/SKILL.md#distill-expertise).
See the [pattern scenarios](pattern-mining.feature).
