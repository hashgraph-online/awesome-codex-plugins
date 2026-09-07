---
name: council
description: 'Collect independent perspectives for an Triggers: "council", "multi-judge review", "independent perspectives".'
---
# Council

Council is an optional judgment strategy, not a lifecycle or delivery gate. Use
it when one fresh validator is insufficient for a named irreversible,
high-blast-radius, or genuinely contested decision. Do not convene a council for
a routine or reversible decision that a single fresh validator can settle: the
cost of independent contexts is warranted only by a named one-way door.

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

## Caller challenge

One consensus shape is never synthesized: **the judges agree the caller's stated
direction is wrong.** Independent agreement against the caller is a strong
signal, and it is still not authority — the caller holds context no judge was
given, and a synthesis that folds the judges' position into a recommendation
deletes that context without telling anyone it was overruled.

When two or more independent judgments recommend a change to something the caller
specified — merging what they separated, cutting what they asked for, reversing a
declared direction — record it as a `caller_challenge` entry, not a consensus
point. Each entry carries these fields (five required; `judge_count` and `disagreement_kind` optional):

- `caller_stated` — their direction, in their words, not paraphrased.
- `judges_recommend` — the change, and how many judges independently reached it.
- `reasoning` — the case at its strongest.
- `context_possibly_missing` — what the judges provably were not given. This is
  the field that makes the entry honest and the one most likely to be dropped;
  an entry without it is majority laundering wearing a new label.
- `cost_if_wrong` — what breaks if the caller's direction was right.

The caller's direction is the report's default and stays the default; the burden
of argument is on the judges. One adjustment: when the judges classify the change
as a security or feasibility defect rather than a preference, say which
(`disagreement_kind`) — the caller still decides, but they decide knowing the
kind of disagreement.

The named failure mode is **quiet adoption**: a council that converges against
the caller and returns a synthesis reading as if the caller had asked for the
judges' version all along. Stop condition: every judgment that contradicts a
caller-stated direction appears in `caller_challenge` with all five fields, or it
does not appear in the report at all.

Reversibility is the sibling question — whether the decision under challenge can
be undone at all is [`one-way-door`](../one-way-door/SKILL.md)'s to classify, not
the council's to assume.

## Synthesis section

The report ends with an explicit consensus/divergence synthesis: consensus
points with their methodology spread, divergence points with each side's
cited evidence, minority findings preserved in their own words,
unresolved assumptions, and any `caller_challenge` entries. Synthesis is
complete when every judge finding lands in exactly one of those buckets; a
finding silently dropped from synthesis is majority laundering.

## Output

- **Artifact directory:** `.agents/scratch/council/<run-id>/`.
- **Filename:** `council-report.json`.
- **Format:** `council-report.v1` JSON — the frozen question and subject digest,
  every judge's context ID, evidence methodology, cited evidence, and disclosed
  omissions, plus the consensus/divergence/minority/unresolved synthesis and any
  `caller_challenge` entries. It carries no `verdict`, `readiness`, or `PASS`
  field; the validator rejects one.
- **Validation command:**
  `skills/council/scripts/validate-output.sh <council-report.json>`.

A judge that times out, errors, or returns an evidence-free judgment is excluded
from agreement counting and recorded as non-returning; if fewer than two
independent judgments remain, report the round as insufficient rather than
synthesize a thin consensus.

## It's working if

Observable in the trace, without reading the prose — and the rubric a fresh
independent judge scores this skill against:

- Every judge finding lands in exactly one synthesis bucket; none is dropped.
- A judgment that contradicts a caller-stated direction appears as a
  `caller_challenge` entry with all five fields, never as a consensus point.
- Every consensus claim names at least two distinct evidence methodologies, or
  is labelled single-method agreement and weighted as one confirmation.
- No `verdict`, `readiness`, or `PASS` field appears anywhere in the report.

## Boundary

Council does not mint a verdict of any version — no `PASS`/`FAIL`/`NOT_PROVEN`,
no `verdict.v*` — edit the subject, retry work, choose a next action, or
authorize Git, closure, release, or delivery. When Council is used as a Validate
strategy, one accountable fresh validator consumes its report and Validate
remains the sole semantic result owner and the only optional `verdict.v2`
writer.
