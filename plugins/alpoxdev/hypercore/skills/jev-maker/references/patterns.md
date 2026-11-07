# Judgement Patterns Reference

Every question asks one narrow judgment, and one call can carry several independent questions; the
shape of that judgment decides three things: which question type to use, how the code composes
several answers, and where a threshold belongs. This file maps the eight patterns this file covers to
a question type and a vendor cookbook, then covers the four documented patterns and the rules for
reading confidence.

Cookbook names and links below come from the vendor cookbook index captured on 2026-10-01. Treat
every threshold they print as an example for that recipe, not as a value to copy.

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
- The four documented patterns
- Confidence rules
- Cookbook index
- Sources

## The eight judgement shapes

Each shape below lists the question type that fits, how the surrounding code composes the answer,
how to treat a threshold, and the closest vendor cookbook.

### Classification

- **Question type:** Choice over the full set of labels, with an `other` option when the list might
  not cover every input.
- **Composition:** code maps the chosen option onto a branch. A taxonomy with levels becomes
  several Choice questions, one per level, with the levels below the first driven by the answer
  above.
- **Thresholds:** gate on `confidence` and route the uncertain band to a person or to the level
  above in the taxonomy. Sorting a confident answer and a coin flip into the same bucket is the
  common mistake here.
- **Nearest cookbook:** [Hierarchical classification](https://docs.typesafe.ai/cookbooks/hierarchical_classification)

### Detection

- **Question type:** Noul when the probability itself is the signal, for example whether a message
  carries personal data. Use a Score instead when the thing being detected has degrees.
- **Composition:** code thresholds the probability and picks a path. Several detectors over the
  same state go in one request and combine in code.
- **Thresholds:** the setting depends on what a miss costs against what a false alarm costs, so the
  two directions usually get different values. Tune both on labeled data, and send a probability that
  lands between the two thresholds to review rather than to either path.
- **Nearest cookbook:** [Guardrails for LLMs](https://docs.typesafe.ai/cookbooks/llm_guardrails)

### Scoring

- **Question type:** Score with levels written as concrete situations. One Score per dimension;
  combine the dimensions in code with weights you own.
- **Composition:** normalize each Score onto a common range, then add the weighted parts. Keep each
  raw Score around so a wrong composite can be traced to the dimension that caused it.
- **Thresholds:** a Score clears or misses a threshold. Do not interpolate a precise number out of
  the levels.
- **Nearest cookbook:** [Classifying RAG passages](https://docs.typesafe.ai/cookbooks/classifying_rag_passages)

### Routing

- **Question type:** Choice over the handlers, one option per destination. Give every handler a
  description that says what belongs to it and what belongs to a neighbour.
- **Composition:** code calls the branch the answer names. When the destination needs arguments,
  ask for each argument as its own question over a closed set of values and call a typed function.
- **Thresholds:** gate the routing itself on `confidence`, and keep a fallback handler for the
  uncertain band rather than forcing the nearest match.
- **Nearest cookbook:** [Function calling](https://docs.typesafe.ai/cookbooks/function_calling)

### Search

- **Question type:** Choice over the candidate line or passage ids for a plain-language query, plus
  a Noul that checks whether the document holds an answer at all.
- **Composition:** code builds the candidate set first, sends it once, and reads the answer as a
  pointer into that set. The text itself is copied from the candidate, never regenerated.
- **Thresholds:** the Noul gets a probability threshold; the Choice gets a confidence gate. A
  separate "no answer in this document" branch keeps an empty result honest.
- **Nearest cookbook:** [Line-by-line search](https://docs.typesafe.ai/cookbooks/semantic_find)

### Retrieval and selection

- **Question type:** two shapes. Pick one from a candidate set with a Choice over the shortlist, or
  rate each candidate with a Score or a Noul per candidate and rank in code. Ask one question per query
  and candidate pair when the shortlist is small enough to enumerate in code.
- **Composition:** code builds the shortlist, sends one request per candidate set, and keeps the
  top matches. The retriever stays in code; the model only reorders what the retriever found.
- **Thresholds:** compare a confidence-gated automatic path against a human-reviewed path, and
  watch the agreement between them as the gate moves.
- **Nearest cookbook:** [Re-ranking](https://docs.typesafe.ai/cookbooks/rerank_typesafe)

### Ranking

- **Question type:** Choice or Score over the candidates. The order the options are listed in is not a
  ranking; rank in code from a per-candidate Score or from the Choice answer's `probabilities`.
- **Composition:** code ranks by the answer, then rechecks the top few against a fuller state in a
  second request when the first request only saw a summary.
- **Thresholds:** a rank cutoff is a product decision, not a model one. Set it where the cost of
  one more reviewed item balances the cost of a missed one.
- **Nearest cookbook:** [Skill suggestion](https://docs.typesafe.ai/cookbooks/skill_suggestion)

### Verification

- **Question type:** Choice or Noul over a claim and the source it cites. One Noul cannot tell "the
  source gives no evidence" apart from "the source cannot be checked", so use a three-state Choice, or
  a second question that asks whether the source is sufficient to check the claim at all.
- **Composition:** code holds the claim and the source side by side in the state and asks one
  question per pair. The verdict drives a review path in code.
- **Thresholds:** an unsupported claim and an unverifiable one are different outcomes. Give them
  separate branches, and let the uncertain band land in review rather than in a pass.
- **Nearest cookbook:** [Double-checking citations](https://docs.typesafe.ai/cookbooks/citation_check)

## The four documented patterns

- **Speculative fan-out.** Send every question the code might need in one call, including ones that
  only matter on some inputs, and let code ignore the answers it does not use. Questions run in
  parallel and cost only their own tokens, so a speculative question is close to free. See
  <https://docs.typesafe.ai/patterns/fan-out>.
- **Confidence-gated routing.** The answer says what to do; `confidence` says whether to do it
  automatically, ask, or hand it to a person. Use it as a second axis rather than folding it into
  the answer itself. See <https://docs.typesafe.ai/patterns/confidence-routing>.
- **Composite scoring.** Break a broad judgment into atomic Scores and combine them in code with
  weights you control. When the combined result disagrees with your team, the weights change
  instead of the prompt. See <https://docs.typesafe.ai/patterns/composite-scoring>.
- **Intent routing.** Classify the incoming request and send it to the right handler: deterministic
  logic, a specialist model, or a person. The classification is the model's job; the routing table
  is the code's. See <https://docs.typesafe.ai/patterns/intent-routing>.

One request cannot answer a question that depends on another answer. When the second question
really needs the first answer to build its state, its options, or its data, make a second request.
When it does not, ask both in the first request and combine in code.

## Confidence rules

- Choice and Score answers carry a `confidence` value from 0 to 1, derived from the shape of the
  probability distribution. A peak concentrated on one outcome reads high; a flat distribution
  reads low.
- A Noul answer carries no separate `confidence`. Its probability is the signal, and a value near
  0.5 means the model gives yes and no equal weight. That is uncertainty, not a medium-strength
  answer, and reading it as intensity is the classic mistake.
- `confidence` is not the selected option's probability. When you want a different statistic, the
  full distribution is in `probabilities` and you can compute your own.
- Thresholds are evaluated on the user's own data. The vendor's examples and the cookbook numbers
  are illustrations, never universal rules: "the correct threshold values depend on your domain and
  the performance of the model for your use case" (confidence, 2026-10-01).
- A threshold is not one number per system. Different actions deserve different gates, with the
  higher bar on the action that is hard to undo. The vendor's own example routes anything under 0.5
  to a person, acts freely on a reversible action, and asks for more before a destructive one.
- Thresholds do not travel between question types or between questions. A question and its negation
  need not sum to one, and a value tuned on a Noul does not carry over to a Choice.
- When thresholds were tuned against a specific model version, pin that version id so a silent
  alias move cannot shift the answers underneath them.

## Cookbook index

The vendor index lists the recipes below. Each name links to the page it names.

| Cookbook | What it shows |
| --- | --- |
| [Self-consistency: nouls](https://docs.typesafe.ai/cookbooks/consistency_noul_cookbook) | Routing uncertain probabilities to human review while keeping the noul values visible |
| [Self-consistency: choices](https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook) | Adding an uncertain outcome to a moderation decision and comparing label agreement |
| [Parallel questions](https://docs.typesafe.ai/cookbooks/parallel_questions) | A many-question briefing in one call, with the cost and latency of batching measured |
| [Re-ranking](https://docs.typesafe.ai/cookbooks/rerank_typesafe) | Shortlists from a lexical retriever, then one question per query and candidate pair |
| [Line-by-line search](https://docs.typesafe.ai/cookbooks/semantic_find) | Scoring document lines against a query and checking whether the document answers it |
| [Structure recovery](https://docs.typesafe.ai/cookbooks/autoformat) | Rebuilding lost formatting by classifying every block after the lines are re-stitched |
| [Function calling](https://docs.typesafe.ai/cookbooks/function_calling) | Turning natural-language requests into calls to typed functions with closed-set arguments |
| [Skill suggestion](https://docs.typesafe.ai/cookbooks/skill_suggestion) | Ranking a large catalog, then rechecking the top few with their full text |
| [Knowledge graph entity alignment](https://docs.typesafe.ai/cookbooks/entity_alignment) | Deciding whether two catalog entries describe the same product, with companion checks |
| [Classifying RAG passages](https://docs.typesafe.ai/cookbooks/classifying_rag_passages) | Scoring retrieved passages and deciding in code which ones reach the answerer |
| [Double-checking citations](https://docs.typesafe.ai/cookbooks/citation_check) | Checking a quote's context against the source before trusting the citation |
| [Guardrails for LLMs](https://docs.typesafe.ai/cookbooks/llm_guardrails) | Screening messages in and out of a model, thresholding hazard and severity |
| [SDE cascade](https://docs.typesafe.ai/cookbooks/sde_cascade) | A two-stage extraction cascade: cheap pass, verify pass, expensive pass |
| [Date extraction](https://docs.typesafe.ai/cookbooks/date_extraction_cookbook) | Extracting named date parts, then resolving and validating them in code |
| [Pre-parsed value extraction](https://docs.typesafe.ai/cookbooks/pre_parsed_value_extraction_cookbook) | Finding candidates with a regular expression and letting the model select the span |
| [Hierarchical classification](https://docs.typesafe.ai/cookbooks/hierarchical_classification) | Walking a deep label hierarchy with parallel search over Choice probabilities |
| [Autoresearch feature discovery](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery) | Turning free text into numeric features and training a downstream model on the outputs |
| [Classification using confidence](https://docs.typesafe.ai/cookbooks/classification_using_confidence) | Reading a Choice answer's own confidence to choose between a fine and a coarse label |

## Sources

> Links checked 2026-10-01

| Claim | Source |
| --- | --- |
| The three question types, their answers, and the guidance to prefer the type the code can act on directly | <https://docs.typesafe.ai/primitives> |
| Choice and Score confidence, the noul probability as its own signal, and the caution that thresholds depend on the domain | <https://docs.typesafe.ai/confidence> |
| Composite scoring, speculative fan-out, confidence-gated routing, and intent routing as documented patterns | <https://docs.typesafe.ai/patterns/confidence-routing> and the sibling pattern pages under <https://docs.typesafe.ai/patterns.md> |
| Batching many questions in one call and combining the answers in code | <https://docs.typesafe.ai/concepts/how-to-build-with-system-one> |
| Not carrying a threshold between questions or question types, and the weak Score interpolation | <https://docs.typesafe.ai/model-jaggedness/jev-1.13> |
| The cookbook names, their URLs, and the one-line purpose of each | <https://docs.typesafe.ai/llms.txt> |
| The caution that schema conformity is not correctness and that thresholds belong on representative data | <https://docs.b.ai/llmservice/models/jev-1.13.0/> |

### Evidence grade

`PRIMARY` for the vendor facts above: each shape, pattern, and confidence rule traces to a vendor page
captured on 2026-10-01, and the cookbook names and links come from the vendor's own index rather
than from a third-party list. `LOCAL` for the parts of this file that are this package's own
recommendation rather than a vendor statement.

The mapping from a judgement shape to a particular cookbook is this package's recommendation. The
cookbook page linked in each row is the vendor's own recipe; the pairing is an editorial choice
that the vendor index does not state.

Not evidenced here and deliberately left unspecified: any universal recommended threshold, price, rate
limit, or model alias. Those belong in the platform snapshot beside this file.
