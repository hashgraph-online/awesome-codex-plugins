---
name: council
description: Collect independent perspectives for an
---
# Council

Council is an optional judgment strategy, not a lifecycle or delivery gate. Use
it when one fresh validator is insufficient for a named irreversible,
high-blast-radius, or genuinely contested decision.

1. Freeze one question, acceptance surface, evidence set, and subject digest.
2. Give each judge an independent context and the same bounded packet.
3. Require each judge to cite evidence, disclose omissions, and return its own
   judgment without seeing other answers first.
4. Synthesize agreement and disagreement without majority laundering. Preserve
   minority evidence and unresolved assumptions.
5. Write `council-report.v1` and return it to the caller.

## Methodology-weighted agreement

Agreement across differing evidence methodologies counts more than agreement
within one. Record each judge's evidence methodology (for example: static
reading, executing the subject, tracing history) alongside its judgment. A
consensus claim must name at least two distinct methodologies among its
supporting judges; otherwise report it as single-method agreement and weight
it as one confirmation, however many judges share it. The named failure mode
is echo consensus: unanimous judgment produced from identical inputs by one
shared method, laundered as independent confirmation.

## Model-diversity axis

When the caller pins judges to model profiles, record each judge's
`model_identity` beside its methodology and context ID (see
the `agent-native` model-dispatch recipe).
Cross-model agreement is an additional diversity axis: single-model unanimity
is weighted as one confirmation with the same anti-echo-consensus rationale,
regardless of how many judges share that model. If a requested profile has no
live adapter, disclose `diversity_unsatisfied` on the report and continue
single-model — never silently, never via `claude -p`.

## Fresh sessions per round

Every judging round uses fresh judge contexts with new context IDs, distinct
from the author, the synthesizer, and every prior round. A judge that has
seen another judge's answer, or its own prior-round answer, is no longer
independent: exclude its judgment from agreement counting and admit it only
as labeled commentary. Reused or colliding context IDs are a checkable stop
condition — repair the isolation or report the round as non-independent.

## Synthesis section

The report ends with an explicit consensus/divergence synthesis: consensus
points with their methodology spread, divergence points with each side's
cited evidence, minority findings preserved in their own words, and
unresolved assumptions. Synthesis is complete when every judge finding lands
in exactly one of those buckets; a finding silently dropped from synthesis is
majority laundering.

## Boundary

Council does not write `verdict.v2`, edit the subject, retry work, choose a next
action, or authorize Git, closure, release, or delivery. When Council is used as
a Validate strategy, one accountable fresh validator consumes its report and
Validate remains the sole durable verdict writer.
