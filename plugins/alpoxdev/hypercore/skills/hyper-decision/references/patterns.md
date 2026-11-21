# Judgement Patterns Reference

A decision request is shared input plus typed questions, and one call can carry several independent
questions. The shape of the judgment decides three things: which question type to use, how code
composes several answers, and where a threshold belongs. This file maps the eight judgement shapes
to a question type, then covers the patterns the vendors document, the rules for reading a
probability, and the one arithmetic rule that a composite score depends on.

Every type name here is the neutral one. The dialect that carries it on a given route is in
[`./question-design.md`](./question-design.md). Route facts, limits, and model ids are in
[`./providers.md`](./providers.md) and the snapshots under [`./official/`](./official/).

## Contents

- The eight judgement shapes
- Classification
- Detection
- Scoring
- Routing
- Search
- Retrieval and selection
- Ranking
- Verification
- Documented patterns
- Speculative fan-out
- Boolean screen first
- Companion boolean
- Routing by probability, not confidence
- Composite scoring and its coherence warning
- Gateway decision fallbacks
- When a second request is worth it
- Probability rules
- Vendor cookbooks as examples
- Sources

## The eight judgement shapes

Each shape below lists the question type that fits, how the surrounding code composes the answer,
how to treat a threshold, and one vendor example. The example is an illustration, not a
requirement.

### Classification

- **Question type:** Choice over the full set of labels.
- **Composition:** code maps the chosen option onto a branch. A taxonomy with levels becomes
  several Choice questions, one per level, with the levels below the first driven by the answer
  above.
- **Thresholds:** gate on the probability of the chosen option, and route the uncertain band to a
  person or to the level above in the taxonomy. Sorting a confident answer and a coin flip into the
  same bucket is the common mistake here.
- **Example:** the TypeSafe cookbook on hierarchical classification.

### Detection

- **Question type:** Boolean when the probability itself is the signal, for example whether a
  message carries personal data. Use a Score instead when the thing being detected has degrees.
- **Composition:** code thresholds the probability and picks a path. Several detectors over the
  same input go in one request and combine in code.
- **Thresholds:** the setting depends on what a miss costs against what a false alarm costs, so the
  two directions usually get different values. Tune both on labeled data, and send a probability
  that lands between the two thresholds to review rather than to either path.
- **Example:** the TypeSafe guardrails cookbook.

### Scoring

- **Question type:** Score with levels written as concrete situations. One Score per dimension;
  combine the dimensions in code with weights you own.
- **Composition:** normalize each Score onto a common range, then add the weighted parts. Keep each
  raw Score around so a wrong composite can be traced to the dimension that caused it.
- **Thresholds:** a Score clears or misses a threshold. Do not interpolate a precise number out of
  the levels.
- **Example:** the TypeSafe cookbook on classifying retrieved passages.

### Routing

- **Question type:** Choice over the handlers, one option per destination. Give every handler a
  description that says what belongs to it and what belongs to a neighbour.
- **Composition:** code calls the branch the answer names. When the destination needs arguments,
  ask for each argument as its own question over a closed set of values and call a typed function.
- **Thresholds:** gate the routing on the probability of the chosen handler, and keep a fallback
  handler for the uncertain band rather than forcing the nearest match.
- **Example:** the TypeSafe function-calling cookbook.

### Search

- **Question type:** Choice over the candidate line or passage ids for a plain-language query, plus
  a Boolean that checks whether the document holds an answer at all.
- **Composition:** code builds the candidate set first, sends it once, and reads the answer as a
  pointer into that set. The text itself is copied from the candidate, never regenerated.
- **Thresholds:** the Boolean gets a probability threshold; the Choice gets its own gate. A
  separate "no answer in this document" branch keeps an empty result honest.
- **Example:** the TypeSafe line-by-line search cookbook.

### Retrieval and selection

- **Question type:** two shapes. Pick one from a candidate set with a Choice over the shortlist, or
  rate each candidate with a Score or a Boolean per candidate and rank in code. Ask one question per
  query and candidate pair when the shortlist is small enough to enumerate in code.
- **Composition:** code builds the shortlist, sends one request per candidate set, and keeps the
  top matches. The retriever stays in code; the model only reorders what the retriever found.
- **Thresholds:** compare a gated automatic path against a human-reviewed path, and watch the
  agreement between them as the gate moves.
- **Example:** the TypeSafe re-ranking cookbook.

### Ranking

- **Question type:** Choice or Score over the candidates. The order the options are listed in is not
  a ranking; rank in code from a per-candidate Score or from the Choice answer's distribution.
- **Composition:** code ranks by the answer, then rechecks the top few against a fuller state in a
  second request when the first request only saw a summary.
- **Thresholds:** a rank cutoff is a product decision, not a model one. Set it where the cost of one
  more reviewed item balances the cost of a missed one.
- **Example:** the TypeSafe skill-suggestion cookbook.

### Verification

- **Question type:** Choice or Boolean over a claim and the source it cites. One Boolean cannot tell
  "the source gives no evidence" apart from "the source cannot be checked", so use a three-state
  Choice, or a second question that asks whether the source is sufficient to check the claim at
  all.
- **Composition:** code holds the claim and the source side by side in the input and asks one
  question per pair. The verdict drives a review path in code.
- **Thresholds:** an unsupported claim and an unverifiable one are different outcomes. Give them
  separate branches, and let the uncertain band land in review rather than in a pass.
- **Example:** the TypeSafe citation-check cookbook.

## Documented patterns

The patterns below are the ones the vendors document, stated without a vendor's type names so they
carry to any route. Each cites the page it comes from.

### Speculative fan-out

Send every question the code might need in one call, including ones that only matter on some
inputs, and let code ignore the answers it does not use. Questions run in parallel and cost only
their own tokens, so a speculative question is close to free. Ask "is this a return request?" and
"which item is being returned?" together, and read the second answer only when the first is yes.
Source: <https://docs.typesafe.ai/patterns/fan-out>.

### Boolean screen first

When a later, more expensive question only matters for a subset of inputs, put a Boolean screen in
the same request and let code branch on it. The screen is cheap, it makes the skip decision
explicit, and it keeps a whole second request off the common path. Source:
<https://docs.typesafe.ai/patterns/noul-screen>.

### Companion boolean

A Choice always returns one of its options, even when nothing fits, and a Box always returns four
edges, even when the object is absent. The vendor's own guidance is to add a companion Boolean that
asks whether any option applies (or whether the object is visible) rather than relying on a
catch-all option. The vendor reports that this worked better than an `other` or
`none of the above` option in its tests, and explains why: an `other` option competes with the
real options for probability. Source: <https://docs.typesafe.ai/primitives> and
<https://docs.typesafe.ai/patterns/companion-noul>.

### Routing by probability, not confidence

Route on the probability the answer already carries. For a Choice that is the probability of the
option you are about to act on; for a Boolean it is the probability of yes. Confidence is a
different statistic, and for a Choice with a fixed number of options it is a deterministic
transform of the top probability, so thresholding both adds no information.

The vendor puts it more bluntly: confidence is rarely the gate. Naive implementations use it as the
check that decides whether code acts, and it measures how concentrated the distribution is, which is
not the chance that the answer is correct. Another calculation over the probabilities usually suits a
use case better than a threshold on confidence. Source:
<https://docs.typesafe.ai/patterns/probability-routing>,
<https://docs.typesafe.ai/confidence.md>, and the vendor guidance at
<https://github.com/typesafe-ai/skills> (release v0.6.2, 2026-10-23).

### Composite scoring and its coherence warning

Break a broad judgment into atomic Scores and combine them in code with weights you control. When
the combined result disagrees with your team, the weights change instead of the prompt. Source:
<https://docs.typesafe.ai/patterns/composite-scoring>.

The warning is arithmetic. A question and its negation need not sum to one, and probabilities of
mutually exclusive labels need not sum to one either. One independent study measured a mean
deviation of 0.064 (95% CI 0.055 to 0.072) between "the label is X" and "the label is not X", and
found three single-label probabilities summing to 1.14 on average. If code adds, subtracts, or
renormalizes probabilities across questions, it is relying on a property the model does not
guarantee. Keep the composite as a weighted sum of separate answers and treat the result as a
ranking signal, not as a probability. Source: <https://arxiv.org/abs/2609.33209>.

### Gateway decision fallbacks

A gateway can rerun a successful decision on a second model when the first answer is uncertain.
Vercel AI Gateway takes a conditional entry as the first element of `providerOptions.gateway.models`
with `when: { question, confidenceBelow }` for Choice and Score, or
`when: { question, probabilityBetween: [lo, hi] }` for Boolean, plus `any`, `all`, and `atLeast`
combinators. This is the only built-in escalation mechanism this package knows of, and it has two
costs. A triggered fallback bills both stages, and a language-model fallback returns no
distribution: on the TypeSafe-compatible surface the gateway reports `confidence: 0` and
`probabilities: {}` as unavailable sentinels, and on the OpenAI-compatible surface it omits both
fields. Treat a fallback as a second opinion, not as a calibrated second probability. Source:
<https://vercel.com/docs/ai-gateway/models-and-providers/decision-fallbacks> and
<https://vercel.com/changelog/confidence-based-decision-fallbacks>.

## When a second request is worth it

One request cannot answer a question that depends on another answer. Send a second request when
code needs the first answer to build the next input, to fetch evidence, or to choose the next
options; when a field added for one question measurably misleads another; or when different sets of
questions need to be cached or versioned separately. In every other case, ask both questions in the
first request and combine in code. Source:
<https://github.com/typesafe-ai/skills> (release v0.6.2, 2026-10-23).

## Probability rules

- A probability is a group rate. The vendor states that calibration rates "describe groups of
  predictions, not a guarantee about any single answer". Never write "the model is 92 percent likely
  to be right about this item"; write what your own labeled sample showed at that band. Source:
  <https://docs.typesafe.ai/introduction/machine-learning-primer.md>.
- A Boolean carries the probability of yes and nothing else. A value near 0.5 means the model gives
  yes and no equal weight, which is uncertainty rather than a medium-strength answer. When you need
  a degree instead of a yes/no, use a Score with defined levels.
- Confidence is not the probability that the answer is correct. It measures how concentrated the
  distribution is, and the vendor says so directly. For a Choice with a fixed number of options it
  is a transform of the top probability, so it is rarely the gate: use the probability of the action
  you are about to take, and keep confidence as a diagnostic. Source:
  <https://docs.typesafe.ai/confidence.md>.
- A Score's position is not a measurement. The model can clear a threshold or order two items, but
  it cannot reconstruct the underlying number between two levels. Source:
  <https://docs.typesafe.ai/model-jaggedness.md>.
- Thresholds are evaluated on your own data. The vendor's examples are illustrations, never
  universal rules: "the correct threshold values depend on your domain and the performance of the
  model for your use case". Source: <https://docs.typesafe.ai/confidence.md>.
- A threshold is not one number per system. Different actions deserve different gates, with the
  higher bar on the action that is hard to undo. The vendor's own starting point for a Boolean is
  0.7 and 0.3, with its own outcome for the band between. Source:
  <https://docs.typesafe.ai/confidence.md>.
- Thresholds do not travel between question types or between questions. A value tuned on a Boolean
  does not carry over to a Choice, and a value tuned on one question does not carry over to a
  related one. Source: <https://docs.typesafe.ai/confidence.md>.
- When thresholds were tuned against a specific model version, pin that version id so a silent
  alias move cannot shift the answers underneath them. Source:
  <https://docs.typesafe.ai/models.md>.
- A refusal is not a low probability. On the OpenAI dialect a refusal is a fourth answer type per
  question, and the vendor states that it is different from a predicate answer with a low
  probability. Give it its own branch. Source:
  <https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/decisions>.

## Vendor cookbooks as examples

These are TypeSafe's own recipes, kept as worked examples of the shapes above. Read the names as
illustrations of a pattern, not as a required library, and read the current list from the vendor
index rather than from this file.

| Cookbook | What it shows |
| --- | --- |
| Self-consistency: nouls | Routing uncertain probabilities to human review while keeping the values visible |
| Self-consistency: choices | Adding an uncertain outcome to a moderation decision and comparing label agreement |
| Parallel questions | A many-question briefing in one call, with the cost and latency of batching measured |
| Re-ranking | Shortlists from a lexical retriever, then one question per query and candidate pair |
| Line-by-line search | Scoring document lines against a query and checking whether the document answers it |
| Structure recovery | Rebuilding lost formatting by classifying every block after the lines are re-stitched |
| Function calling | Turning natural-language requests into calls to typed functions with closed-set arguments |
| Skill suggestion | Ranking a large catalog, then rechecking the top few with their full text |
| Knowledge graph entity alignment | Deciding whether two catalog entries describe the same product, with companion checks |
| Classifying RAG passages | Scoring retrieved passages and deciding in code which ones reach the answerer |
| Double-checking citations | Checking a quote's context against the source before trusting the citation |
| Guardrails for LLMs | Screening messages in and out of a model, thresholding hazard and severity |
| SDE cascade | A two-stage extraction cascade: cheap pass, verify pass, expensive pass |
| Date extraction | Extracting named date parts, then resolving and validating them in code |
| Pre-parsed value extraction | Finding candidates with a regular expression and letting the model select the span |
| Hierarchical classification | Walking a deep label hierarchy with parallel search over Choice probabilities |
| Autoresearch feature discovery | Turning free text into numeric features and training a downstream model on the outputs |
| Classification using confidence | Reading a Choice answer's own confidence to choose between a fine and a coarse label |

## Sources

> Links checked 2026-11-08.

| Claim | Source |
| --- | --- |
| The question types, their answers, and the guidance to prefer the type the code can act on directly | <https://docs.typesafe.ai/primitives> |
| Boolean probability as its own signal, Choice and Score confidence as a transform of the distribution, the 0.7 and 0.3 starting band, and the caution that thresholds depend on the domain | <https://docs.typesafe.ai/confidence.md> |
| Probability routing, companion Boolean, Boolean screen, composite scoring, and speculative fan-out as documented patterns | <https://docs.typesafe.ai/patterns/probability-routing>, <https://docs.typesafe.ai/patterns/companion-noul>, <https://docs.typesafe.ai/patterns/noul-screen>, <https://docs.typesafe.ai/patterns/composite-scoring>, <https://docs.typesafe.ai/patterns/fan-out> |
| A Choice always picks one option and a Box always returns four edges, and the vendor's preference for a companion Boolean over an `other` option | <https://docs.typesafe.ai/primitives> |
| The second-request rule, decisions as a truth table in code, and the warning that confidence is rarely the gate | <https://github.com/typesafe-ai/skills> (release v0.6.2, 2026-10-23) |
| Negation pairs missing 1.0 by 0.064 and single-label probabilities summing to 1.14 | <https://arxiv.org/abs/2609.33209> |
| Gateway decision fallbacks, their trigger predicates, the double billing, and the unavailable sentinels | <https://vercel.com/docs/ai-gateway/models-and-providers/decision-fallbacks> and <https://vercel.com/changelog/confidence-based-decision-fallbacks> |
| The weak Score interpolation and the Choice option-order bias | <https://docs.typesafe.ai/model-jaggedness.md> |
| A refusal is a separate answer type and not a low probability | <https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/decisions> |
| Probabilities as group rates rather than per-item odds | <https://docs.typesafe.ai/introduction/machine-learning-primer.md> |
| Pinning a version id when thresholds were tuned against one version | <https://docs.typesafe.ai/models.md> |
| The cookbook names and their one-line purpose | <https://docs.typesafe.ai/llms.txt> |

### Evidence grade

`PRIMARY` for the vendor facts above: each pattern, threshold rule, and probability rule traces to
a vendor page captured on 2026-11-08. `PRIMARY` for the gateway fallback contract, which comes from
the gateway vendor's own page. `SECONDARY` for the coherence numbers, which come from a single
independent preprint with released analysis but no venue review. `LOCAL` for the mapping from a
judgement shape to a particular vendor cookbook, which is this package's editorial pairing and not
a vendor statement.

Not evidenced here and deliberately left unspecified: any universal recommended threshold, price,
rate limit, or model id. Those live in [`./providers.md`](./providers.md) and the snapshots under
[`./official/`](./official/).
