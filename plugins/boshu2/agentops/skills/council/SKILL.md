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
output_contract: council-report.v1 JSON (schemas/council-report.v1.schema.json) validated by this skill's scripts/validate-output.sh
---

# Council

Council is an optional judgment strategy for hard questions where contrasting
perspectives can expose alternatives, assumptions, or missed evidence. Use it
when the caller selects multiple views for brainstorming, architecture or
planning, or validation. Name the uncertainty that makes the additional
contexts useful; routine work needs no council. Neighbours: one opinion or
look-over is [Review](../review/SKILL.md), one adversarial challenge of a plan
is [Premortem](../premortem/SKILL.md), one consequential choice for Plan is
[Idea Genie](../idea-genie/SKILL.md), and an acceptance verdict is
[Validate](../validate/SKILL.md).

## Rules that decide the synthesis

They hold for a council you run and for judgments the caller already collected
elsewhere (several reviews, subagent reads) and asks you to synthesize.
Judgments made against different revisions are separate subjects, never
agreement on one.

- **No verdict.** Council returns no `PASS`, `FAIL`, `NOT_PROVEN`, readiness
  or approval, even when asked to turn agreement into one. Decline, and say
  that a fresh Validate read owns that judgment. The report goes to the caller
  as advisory findings, which cannot stand in for it.
- **Echo consensus weighs as one.** Agreement among judges that share one
  model or one evidence method counts as one confirmation, however many judges
  share it: unanimity from identical inputs and one shared method is not
  independent confirmation. Each consensus point names the `methodologies`
  (static reading, executing the subject, tracing history) and, where judges
  record `model_identity`, the `models` of its supporting judges; a point with
  only one of either sets `weighs_as_one: true`.
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
| Validate | Findings against the same subject and acceptance | Advisory findings; acceptance stays with a fresh Validate read |
| Duel | Ranked ideas, then scores for every other member's ideas | Ideas ranked by cross-member agreement, score gaps and dissent |
| Interview panel | An answer to each Interview question | Agreed and open answers the caller accepts or amends |

1. Freeze the question, constraints or acceptance, authorized evidence, and
   subject digest. Select participants, model pins, and real dispatch bounds;
   contexts stay in the author's model family unless the caller pins mixed
   models through [model-dispatch](../agent-native/references/model-dispatch.md).
   The caller may give each participant its own model, effort and perspective
   (for example architect, reliability, security or simplicity); the same model
   in separate contexts counts as separate participants on the roster, but their
   agreement still weighs as one. A requested profile or required leg with no
   authorized live adapter is listed by name in `diversity_unsatisfied`;
   available views may still return with that limit, but a missing required
   leg prevents convergence and no agreement substitutes for it.
2. Give each participant a fresh independent context and the same bounded
   packet, never the author's preferred conclusion; a perspective steers what a
   member examines, never what evidence it gets. Collect proposals or judgments
   before revealing any peer response. Reused or colliding context IDs make a
   view non-independent: repair the isolation within bounds or disclose it.
   Admit facts tied to a cited source and the caller's stated need and stakes;
   keep your own rankings, option-grading labels and summaries of files a
   participant can open itself out until synthesis. Word options you drafted
   with equal care, and say a participant may reject all of them or the
   question as posed. Show peer work in debate or duel scoring under neutral
   labels (A, B, C), not member or model names; the report keeps the mapping
   in each judge's `judgment`.
3. Require evidence, reasoning, and omissions. For brainstorming, distinguish
   new hypotheses from supported claims; novelty is not proof.
4. Synthesize the sealed initial views, or run a caller-selected mode below.
   Preserve dissent and changes of position. `subject_digest` covers what
   Validate's [Subject](../validate/SKILL.md#subject) binds: the
   `canonical_manifest_digest` of `ao provenance manifest`, or else
   `shasum -a 256 <files> | LC_ALL=C sort | shasum -a 256` over the subject's
   repo-relative paths, or the sha256 of a subject supplied only as text.
   Recompute it the same way before each later round and before synthesis; if
   it changed, name the change and rerun every participant on the new subject
   or return the incomplete outcome, never folding views of the old subject in.
   With nothing to bind (a brainstorm, an open design question, an interview
   panel), it is the sha256 of `question` as recorded, computed once; a
   reworded question is a new subject.
5. Return `council-report.v1` with its limits and, when the use produces one
   (design or plan does), its optional `recommendation`. Prefer one option
   only for a reason in the evidence; when options stay close, say either
   would serve and name the tradeoffs that separate them. Outside a
   caller-selected voting rule, a count of pros, cons or supporters breaks no
   tie. Council neither changes the subject nor grants implementation or
   delivery authority.

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

## Caller challenge

When judgments recommend a change to something the caller specified (merging
what they separated, cutting what they asked for, reversing a declared
direction), record it in `synthesis.caller_challenge`. Independent agreement
against the caller is a strong signal and still not authority: the caller
holds context no judge was given. Each entry has five fields:

- `caller_stated`: their direction, in their words, not paraphrased.
- `judges_recommend`: the change, who supports it, and whether their views were
  independent or peer-informed; never describe debate votes as independent.
- `reasoning`: the case at its strongest.
- `context_possibly_missing`: what the judges provably were not given; an
  entry without it is majority laundering wearing a new label.
- `cost_if_wrong`: what breaks if the caller's direction was right.

Optional `judge_count` needs at least two supporters; optional
`disagreement_kind` says whether the objection is a `preference`, `security`
or `feasibility` defect. The caller's direction stays the default and the
burden of argument is on the judges; the caller decides, knowing the kind of
disagreement. Stop condition: every judgment that contradicts a caller-stated
direction appears in `caller_challenge` with all five fields and in no other
synthesis bucket. Whether the challenged decision can be undone belongs in
[Plan](../plan/SKILL.md), with actual undo cost and existing authority; the
council must not assume either.

## Synthesis section

The report ends with an explicit consensus/divergence synthesis: consensus
points with their methodology spread, divergence points with each side's
cited evidence and whether the split is an evidence gap (name the fact or check
that would settle it) or a judgment call the caller owns, minority findings
preserved in their own words, unresolved assumptions, and any
`caller_challenge` entries. Synthesis is complete when every judge finding
lands in exactly one of those buckets; a finding silently dropped from
synthesis is majority laundering. Run facts (bounds, roster, threshold, tally,
stop reason, non-returning judges) go in `synthesis.notes`.

Two judges' defect findings are one point only when a single fix would resolve
both, judged by reading each defect and its fix, not the wording or a shared
location; proposals or answers are one point only when they recommend the same
change. Findings on the same lines with different failure modes stay
separate, opposing recommendations are divergence, and when unsure keep them
apart, since a wrong merge inflates agreement. A merged point keeps each
judge's own evidence.

## Output

`<skill-dir>` is the directory that contains this SKILL.md. Claude Code shows
it as "Base directory for this skill"; Codex lists this skill's SKILL.md path;
in an AgentOps source checkout it is `skills/council`. Replace `<skill-dir>`
with that absolute path before running a command. The working directory stays
the user's repository. If the host did not show where this skill is installed,
use the directory of the SKILL.md you read. If you cannot determine it, do not
guess a path or run a same-named script from the current repository; say the
bundled script is unavailable and check the report's fields by hand against
its [schema](schemas/council-report.v1.schema.json).

- **Destination:** caller-selected protected external non-Git storage;
  preserve existing legacy evidence. Missing routing is not a workspace
  fallback: when no destination is supplied, return the report inline in the
  conversation and write no file.
- **Filename:** `council-report.json`.
- **Format:** `council-report.v1` JSON ([schema](schemas/council-report.v1.schema.json)):
  the frozen `question` and `subject_digest`, any `recommendation`, every judge's
  `context_id`, `methodology`, cited `evidence` and `omissions`, and the
  synthesis buckets above. Record mode, round and candidate digest in each
  `judgment`. It carries no `verdict` or `readiness` field, and a `judgment`
  or `recommendation` that is only a verdict word is rejected.
- **Validation command:**
  `bash "<skill-dir>/scripts/validate-output.sh" <council-report.json>`, or
  `bash "<skill-dir>/scripts/validate-output.sh" -` with an inline report on stdin.

A judge that times out, errors, or returns an evidence-free judgment is excluded
from agreement counting and listed as non-returning in `synthesis.notes` with
its context ID and reason, never as a `judges` entry. If fewer than two
eligible initial judgments remain, report insufficient independent coverage
rather than synthesize a thin consensus; when no valid report can be formed,
return the incomplete outcome and available receipts without fabricating judge
records.
