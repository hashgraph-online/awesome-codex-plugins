---
name: pattern-mining
description: Test repeated implementation shapes against
---
# Pattern Mining

Decide whether repeated code demonstrates a reusable rule or only a plausible
hypothesis. Similar names and syntax are not enough; the abstraction must
survive examples it was not designed around.

## Constraints

- To prevent lineage copies from faking recurrence, use independently
  implemented exemplars with repository anchors.
- Because the candidate must generalize, form it without seeing the holdout and
  back-apply every holdout-driven refinement.
- To keep weak evidence from becoming architecture, route hypotheses to
  `no-action`; only a fully proven promotion may reach `operationalize`.

## Workflow

1. State the candidate pattern and collect independently implemented
   exemplars with repository anchors. Use `research` when coverage is unclear.
2. From the exemplars, separate required invariants, legitimate variation
   points, and incidental similarity.
3. Require at least three distinct exemplars before promotion is possible.
   Form the candidate abstraction without using the holdout.
4. Test it against every exemplar, then a separate holdout. Back-apply the
   refined abstraction to the original exemplars so the holdout fix cannot
   silently break them.
5. Emit `outcome: promote` only when the exemplar floor, holdout, and
   back-application all pass. Route that evidence to `operationalize`, which
   decides whether the eventual shape is a skill, gate, library, template, or
   no action.
6. Otherwise emit `outcome: hypothesis` with `route: no-action`. Keep the
   evidence bounded and name what additional observation would retest it.

## Diff/align across exemplars

Invariants are extracted mechanically, not remembered. Lay the exemplars side
by side, align them structurally (same role, same position in the flow — not
same variable names), and diff: what survives every alignment is a candidate
invariant; what varies by site is a variation point; what varies with no
functional consequence is incidental. Work pairwise before generalizing — an
"invariant" derived by skimming all exemplars at once is usually the first
exemplar's shape with the others squinted into agreement. Stop condition: every
line of the candidate abstraction is traceable to a surviving alignment across
all exemplars, or it is deleted. The named failure mode is eyeball
convergence — declaring similarity from memory of the files rather than from an
explicit alignment, which smuggles one lineage's incidentals into the rule.

## Explicit search recipes

Exemplar discovery is part of the evidence and must be replayable. Record the
exact queries used — `rg` patterns, glob scopes, structural searches — in the
output packet, alongside which hits were kept and why the rest were excluded.
A recipe that returns hits you did not examine is unfinished coverage: either
examine them or narrow the recipe and record the narrowed form. The named
failure mode is convenience sampling — mining only the files already in
context, which biases the exemplar set toward one author or one era of the
codebase and fakes independence at step 1. If no recipe can be written that
finds the exemplars, the recurrence claim is unverifiable and the outcome
stays `hypothesis`.

## Packaging-shape catalog

A promoted pattern lands in exactly one shape, and naming the intended shape
before promotion sharpens the holdout test. The catalog, in ascending
commitment: **no-action** (evidence retained, nothing built), **checklist
line** (rule in an existing doc or skill), **template** (copyable exemplar),
**library/helper** (shared executable code), **gate** (deterministic check
that blocks). Match commitment to evidence strength: three exemplars and one
holdout justify a checklist line or template; a gate needs demonstrated cost
of violation, not just recurrence. This skill only records the recommended
shape in the packet — `operationalize` owns the packaging decision. The named
failure mode is shape inflation: routing a barely-promoted pattern straight to
a gate or library because building feels like progress, which turns weak
evidence into architecture the same way skipping the holdout would.

## Output Specification

- **Artifact directory:** `.agents/patterns/<run-id>/`
- **Filename convention:** `pattern-mining.json`
- **Format:** `pattern-mining.v1` JSON containing the outcome, distinct
  exemplars, invariants, variations, incidental details, holdout result,
  back-application result, and route.
- **Validation command:** `skills/pattern-mining/scripts/validate-output.sh <pattern-mining.json>`
- **Downstream handoff:** pass a validated `promote` artifact to
  `operationalize`; retain a validated `hypothesis` artifact as bounded
  evidence with `route: no-action`.

Promotion requires at least three distinct exemplars, one separate passing
holdout, successful back-application, and at least one invariant. Any weaker
packet remains a hypothesis and cannot route to reusable packaging.

The validator is the machine boundary:

```bash
skills/pattern-mining/scripts/validate-output.sh <pattern.json>
```

This skill owns evidence for the pattern. It never creates the reusable
artifact itself and never promotes a failed or untested holdout.

Executable behavior:
[references/pattern-mining.feature](references/pattern-mining.feature).

## Quality

- Exemplars are independent and repository-anchored; copied implementations do
  not inflate the evidence floor.
- Invariants, legitimate variations, and incidental similarities stay distinct
  through holdout testing and back-application.
- The named validator passes before a promotion reaches `operationalize` or a
  hypothesis is retained as `no-action` evidence.

## Do not

- Count copies from one implementation lineage as independent exemplars.
- Hide variation by calling it incidental.
- Route a hypothesis directly to a skill, rule, gate, or library.
