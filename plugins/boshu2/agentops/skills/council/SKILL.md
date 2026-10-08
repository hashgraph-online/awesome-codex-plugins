---
name: council
description: 'Compare independent opinions from several models or contexts without inflating agreement. Use when: wanting a second opinion or debate, or summarizing several reviewers'' results.'
practices: [llm-eval-harness, design-by-contract]
hexagonal_role: domain
consumes: [explicit-question, evidence]
produces: [council-report.v1]
context_rel: []
skill_api_version: 1
user-invocable: true
metadata:
  graph_root: true
  tier: judgment
  dependencies: []
  capabilities: [collect_independent_judgments, synthesize_disagreement, bounded_deliberation, duel_scored_ideas, answer_interview_panel]
  effects: [write_advisory_council_report]
  canonical_status: canonical
  disposition: keep_strategy
output_contract: council-report.v1 JSON validated by skills/council/scripts/validate-output.sh
---

# Council

Council is an optional judgment strategy for hard questions where contrasting
perspectives can expose alternatives, assumptions, or missed evidence. Use it
when the caller selects multiple views for brainstorming, architecture or
planning, or validation. Name the uncertainty that makes the additional
contexts useful; routine work needs no council. Neighbours: one adversarial
challenge of a plan is [Premortem](../premortem/SKILL.md), one consequential
choice for Plan is [Idea Genie](../idea-genie/SKILL.md), and an acceptance
verdict is [Validate](../validate/SKILL.md).

## Rules that decide the synthesis

They hold for a council you run and for judgments the caller already collected
elsewhere (several reviews, subagent reads) and asks you to synthesize.

- **No verdict.** Council returns no `PASS`, `FAIL`, `NOT_PROVEN`, readiness
  or approval, even when asked to turn agreement into one. Decline, and say
  that a fresh Validate read owns that judgment; the council report is
  advisory input to it.
- **Echo consensus weighs as one.** Agreement among judges that share one
  model or one evidence method counts as one confirmation, however many judges
  share it. Name the methodologies and models behind every consensus claim.
- **The caller's direction stays the default.** A judgment that contradicts
  what the caller decided becomes a `caller_challenge` entry with all five
  fields, never a consensus point or a quiet change to the recommendation.
- **Nothing is dropped.** Initial views are sealed before any is shared, every
  finding lands in exactly one synthesis bucket, and dissent survives.

## Run a council

| Use | Ask each participant for | Return to the caller |
|---|---|---|
| Brainstorm | Distinct options, assumptions, and failure modes | Promising ideas and the objections worth testing |
| Design or plan | A proposed approach, tradeoffs, and evidence | A recommendation with unresolved decisions visible |
| Validate | Findings against the same subject and acceptance | Advisory findings for the accountable fresh validator |
| Duel | Ranked ideas, then scores for every other member's ideas | Ideas ranked by cross-member agreement, score gaps and dissent |
| Interview panel | An answer to each Interview question | Agreed and open answers the caller accepts or amends |

1. Freeze the question, constraints or acceptance, authorized evidence, and
   subject digest. Select participants, model pins, and real dispatch bounds.
   The caller may give each participant its own model, effort and perspective
   (for example architect, reliability, security or simplicity); the same model
   in separate contexts counts as separate participants on the roster, but their
   agreement still weighs as one model's confirmation.
2. Give each participant a fresh independent context and the same bounded
   packet, never the author's preferred conclusion; a perspective steers what a
   member examines, never what evidence it gets. Collect proposals or judgments
   before revealing any peer response. Reused or colliding context IDs make a
   view non-independent: repair the isolation within bounds or disclose it.
3. Require evidence, reasoning, and omissions. For brainstorming, distinguish
   new hypotheses from supported claims; novelty is not proof.
4. Synthesize the sealed initial views, or run a caller-selected mode below.
   Preserve dissent and changes of position.
5. Return `council-report.v1` with a recommendation and its limits. Council
   neither changes the subject nor grants implementation or delivery authority.

Independent comparison is the default. Multiple models can broaden the
perspectives offered; agreement alone proves no improvement.

## Optional modes

Load only the mode the caller selected:

- Bounded debate or a majority rule: [debate](references/debate.md). Replies
  that saw earlier answers are peer-informed, never new independent views, and
  a majority cannot establish truth or acceptance.
- Members scoring each other's ideas: [duel](references/duel.md).
- A council answering an Interview: [interview panel](references/interview-panel.md).
- A disagreement between validation judges that survives repair:
  [judge split](references/judge-split.md).

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

Default to fresh contexts in the author's model family on both Codex and Claude.
The caller selects mixed-family review explicitly and may pin each model, using
the bounded adapter in [agent-native's model-dispatch recipe](../agent-native/references/model-dispatch.md);
review time comes from caller/native bounds, with no fixed ten-minute cap.
Record each pinned judge's `model_identity` beside its methodology and context
ID. Single-model unanimity is weighted as one confirmation, for the same reason
as single-method agreement. If a requested profile has no authorized live
adapter, disclose `diversity_unsatisfied`; available views may still be
returned with that limitation but do not satisfy the missing leg. A required
cross-family validation leg remains unsatisfied and prevents convergence;
Council cannot substitute single-model agreement for it.

## Caller challenge

One consensus shape is never synthesized: **the judges agree the caller's stated
direction is wrong.** Independent agreement against the caller is a strong
signal, and it is still not authority: the caller holds context no judge was
given, and a synthesis that folds the judges' position into a recommendation
deletes that context without telling anyone it was overruled.

When judgments recommend a change to something the caller specified (merging
what they separated, cutting what they asked for, reversing a declared
direction), record it as a `caller_challenge` entry, not a consensus point. Use
these five fields; optional `judge_count` requires at least two supporters,
while `disagreement_kind` classifies the objection:

- `caller_stated`: their direction, in their words, not paraphrased.
- `judges_recommend`: the change, who supports it, and whether their views were
  independent or peer-informed; never describe debate votes as independent.
- `reasoning`: the case at its strongest.
- `context_possibly_missing`: what the judges provably were not given. This is
  the field that makes the entry honest and the one most likely to be dropped;
  an entry without it is majority laundering wearing a new label.
- `cost_if_wrong`: what breaks if the caller's direction was right.

The caller's direction is the report's default and stays the default; the burden
of argument is on the judges. When the judges classify the change as a security
or feasibility defect rather than a preference, say which
(`disagreement_kind`); the caller still decides, knowing the kind of
disagreement.

The named failure mode is **quiet adoption**: a council that converges against
the caller and returns a synthesis reading as if the caller had asked for the
judges' version all along. Stop condition: every judgment that contradicts a
caller-stated direction appears in `caller_challenge` with all five fields, or it
does not appear in the report at all. Whether the challenged decision can be
undone belongs in [Plan](../plan/SKILL.md), with actual undo cost and existing
authority; the council must not assume either.

## Synthesis section

The report ends with an explicit consensus/divergence synthesis: consensus
points with their methodology spread, divergence points with each side's
cited evidence, minority findings preserved in their own words,
unresolved assumptions, and any `caller_challenge` entries. Synthesis is
complete when every judge finding lands in exactly one of those buckets; a
finding silently dropped from synthesis is majority laundering.

## Output

- **Destination:** caller-selected protected external non-Git storage;
  preserve existing legacy evidence. Missing routing is not a workspace
  fallback: when no destination is supplied, return the report inline in the
  conversation and write no file.
- **Filename:** `council-report.json`.
- **Format:** `council-report.v1` JSON: the frozen question and subject digest,
  every judge's context ID, evidence methodology, cited evidence, and disclosed
  omissions, plus the consensus/divergence/minority/unresolved synthesis and any
  `caller_challenge` entries. Record mode and candidate digest in each
  `judgment` and methodology and source references in their existing fields; no
  new schema is needed. It carries no `verdict`, `readiness`, or `PASS` field;
  the validator rejects one.
- **Validation command:** this skill's
  `scripts/validate-output.sh <council-report.json>`.

A judge that times out, errors, or returns an evidence-free judgment is excluded
from agreement counting and recorded as non-returning; if fewer than two
eligible initial judgments remain, report insufficient independent coverage
rather than synthesize a thin consensus. If no valid report can be formed,
return the incomplete outcome and available receipts without fabricating judge
records.

## Prompt

```text
Use /agentops:council to compare architectures for reliable Job redelivery.
Use four distinct available models I authorize for this source. Have each
propose an approach independently, then debate the alternatives. Require
three of four to support the same exact recommendation. Cap debate at five
rounds and the whole council at 60 minutes. Preserve objections and explain
what evidence we still need before implementation or validation.
```

Resolve the actual authorized model pins before dispatch; these example bounds
are caller choices, not skill defaults. For validation, provide the unchanged
acceptance and exact candidate, and return findings to the fresh validator
without voting on PASS.

## It's working if

- Initial views are sealed before cross-review; any debate is bounded and
  labeled peer-informed, with exact-candidate votes and dissent preserved.
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
