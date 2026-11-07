# Jev Platform Snapshot

What the vendor pages say about Jev as a platform: the HTTP endpoint, the question and answer
shape, the limits and price in force when this file was written, the known jagged edges of the
current version, and the three routes this snapshot covers. Everything here was read
from the pages listed under Sources and captured on 2026-10-01. This file is the only place in
this skill where price, limits, model aliases, and route contracts belong.

## Contents

- Refresh Policy
- Evaluation endpoint
- Models, aliases, limits, and price
- Question types
- Answer types and confidence
- jev-1.13 jaggedness
- Official agent skill
- Vercel AI SDK and AI Gateway
- b.ai Decisions API
- Sources

## Refresh Policy

- last_verified_at: 2026-10-01
- refresh_when:
  - a vendor page changes a rate limit, price, or model alias
  - a route adds or drops a documented endpoint
  - the question or answer shape changes (`noul`, `choice`, `score`, `boolean`)
  - the jaggedness list for the current Jev version changes
- supports_rules:
  - rules/modes-and-routing.md
  - rules/safety-and-boundaries.md

When this snapshot is more than 30 days old and the network is available, re-read the vendor
pages read-only and update the dates here. When the network is not available, say the date out
loud instead of guessing at current values.

## Evaluation endpoint

- source_url: https://docs.typesafe.ai/api
- last_verified_at: 2026-10-01
- applies_to: the direct HTTP route, its request and response shape, and its error codes
- volatility: stable
- summary: One endpoint evaluates a shared `state` against a map of typed questions and returns
  one structured answer per question id. All three question types go to the same URL; the `model`
  field in the body picks the version that answers.

```http
POST https://api.typesafe.ai/v1/systemone
Authorization: Bearer plus your key
Content-Type: application/json
```

Request body:

| Field | Type | Notes |
| --- | --- | --- |
| `state` | string, object, or array | The content to evaluate. A chat log, a record, or the current state of your application. |
| `model` | string | `"jev-latest"` is the flagship alias. See the alias table below. |
| `questions` | map of id to question | A map you name. Answers come back under the same ids. The vendor states the id "is not sent to the underlying model and is not used in inference" (api, 2026-10-01). The b.ai page states that its map must be non-empty and that ids must not be empty or whitespace-only. |

Every question carries `type` and `instructions`. `instructions` accepts a string, an object, or an
array, so a long prompt with reference data can be split into a question field and data fields, then
pointed at by name in backticks. `criteria` is never a bare string: it is an object for a `noul`
question, a map of option to description for a `choice` question, and an ordered array for a `score`
question.

Response body: `model` (the versioned id that answered), `answers` (one entry per question id),
and `usage` with `input_tokens` and `output_tokens`.

The endpoint returns `401` for a missing or invalid key, `422` when the body fails validation
and the body names the offending field, `429` when a rate limit is hit, and `529` when the
service is overloaded. The vendor's advice for the last two is to "back off and retry after a
short delay" (api, 2026-10-01); the client SDKs do this by default.

The Python SDK and the JavaScript SDK both wrap this endpoint. The JavaScript SDK page documents
the `TypeSafeClient` class, `client.systemOne`, the `TYPESAFE_API_KEY` environment variable, and a
`choice()` helper; it does not show helpers for the other question types, so read that package's
type reference before using them.

## Models, aliases, limits, and price

- source_url: https://docs.typesafe.ai/models
- last_verified_at: 2026-10-01
- applies_to: model ids and aliases, rate limits, context length, accepted input, language support, price
- volatility: volatile
- summary: `jev-1.13.0` is the current versioned id. Two aliases point at it, both currently to the
  same build. Price is charged on input tokens only; output tokens are free. Rate limits move and
  the vendor says so on the page.

| Item | Value on 2026-10-01 |
| --- | --- |
| Versioned id | `jev-1.13.0` |
| `jev-latest` | resolves to `jev-1.13.0` (the default in the client SDKs) |
| `jev-preview` | resolves to `jev-1.13.0` as well; no preview build is available right now |
| Price | $42 per Btok, or $0.042 per million input tokens. Output tokens are free |
| Rate limits | 100K tokens per second and 40 requests per second |
| Context | 64k tokens per request; 32k for the `state` plus the longest single question |
| Input | Text only, as a string, JSON object, or array of text values. No image, audio, or video |

The page carries a warning that limits are "adjusting dynamically" and "can change without
notice" (models, 2026-10-01). A request over either limit returns `429`. A call may send many
questions in one request because the state is ingested once and evaluated in parallel.

Because an alias moves when a new release ships, answers behind `jev-latest` can change with no
change on the caller's side. The response `model` field reports the version that answered. When
confidence thresholds were tuned against one version, pin that version id and move on purpose.

Language support: English is the primary training language and where accuracy is best. Other
languages, including CJK scripts, are handled but not equally well. Test on your own content
before trusting a non-English workload, and read the confidence signal closely when routing.

`GET /v1/models` lists the names an account may send, with a description and release date.

## Question types

- source_url: https://docs.typesafe.ai/api
- last_verified_at: 2026-10-01
- applies_to: the three question types, their criteria rules, and their answers
- volatility: stable
- summary: A question is one of three types. All three share `type` and `instructions`; each adds
  its own `criteria` rules.

| Type | Criteria | Answer |
| --- | --- | --- |
| `noul` | Optional object with the properties `true` and `false`; the b.ai route adds that only those two keys are allowed, and that each value is a string, object, or array | `noul`, a number from 0 (no) to 1 (yes) |
| `choice` | Required map of option to description. Maximum 255 options; `null` is allowed when an option needs no detail | `choice` (the highest-probability option), `probabilities` for every option, and `confidence` |
| `score` | Required ordered array of level descriptions. At least two levels; the API accepts up to 10. Items may be strings, objects, or arrays, but not `null` | `score` (a probability-weighted value that can fall between levels), `legend`, `probabilities`, and `confidence` |

`noul` is described as the probability that the answer is yes, not a degree score: values near
0.5 mean uncertainty. `score` returns a probability-weighted mean, so a three-level answer can
come back as 1.05, and `legend` maps each level index back to its description.

## Answer types and confidence

- source_url: https://docs.typesafe.ai/confidence
- last_verified_at: 2026-10-01
- applies_to: how certainty is reported and how to gate behavior on it
- volatility: stable
- summary: Choice and Score answers carry a `confidence` value from 0 to 1 derived from the shape
  of the probability distribution. A concentrated distribution gives a high value; a flat one
  gives a low value. Noul answers carry no separate confidence field.

The page states plainly that "a confidence threshold is not one number" (confidence,
2026-10-01). Different actions in the same system deserve different gates depending on what a
wrong answer costs. The vendor's own example routes anything under 0.5 to a human, acts freely
on a reversible action, and requires a higher bar before a destructive one.

Two cautions carried over here. Schema conformity is not correctness: a well-formed answer can
still be wrong, so thresholds belong on representative labeled data. And `confidence` is not the
selected option's probability; the raw distribution is in `probabilities` for anyone who wants a
different statistic.

## jev-1.13 jaggedness

- source_url: https://docs.typesafe.ai/model-jaggedness/jev-1.13
- last_verified_at: 2026-10-01
- applies_to: known failure modes of `jev-1.13` and the workaround the vendor recommends for each
- volatility: volatile
- summary: The page lists nine failure modes and opens with "Jev isn't perfect" (jaggedness,
  2026-10-01). It applies to `jev-1.13` and carries the vendor's own review date of 2026-09-17.

| # | Failure mode | Do this instead |
| --- | --- | --- |
| 1 | Literal reading: the answer follows the words written, not the intent behind them | Write the exact condition, and put boundary cases in the criteria |
| 2 | Math and numbers: counting, arithmetic, and numeric representations are unreliable | Keep the arithmetic in code; use names instead of hex or binary values |
| 3 | Date and time comparison: dates are read as text, not as ordered quantities | Extract the parts (a closed set, so a Choice works), assemble and compare in code |
| 4 | Indirection: double negatives and multi-hop questions cost accuracy | Reduce hops and point at the relevant state by name |
| 5 | Large state full of irrelevant detail: unrelated content acts as a distractor | Filter in code first and send only the fields the question needs |
| 6 | Adversarial content: state is data and is not treated as hostile by default | Write precise prompts and test edge cases before deploying widely |
| 7 | Contradictory instructions and criteria: the two can fight each other | Treat the criteria as an extension of the instruction and align the wording |
| 8 | Common-sense structural invariants: a question and its negation need not sum to 1 | Do not carry a threshold tuned on one question over to a different one |
| 9 | Generation: the model is not trained to produce text | Use a generative model, or turn extraction into a Choice over enumerated options |

A score output is also weak for recovering an exact number between two levels. It can decide
whether a value clears a threshold, but not reconstruct the value itself.

## Official agent skill

- source_url: https://docs.typesafe.ai/agent-skill.md
- last_verified_at: 2026-10-01
- applies_to: the vendor-published agent skill, what it covers, and how it is installed
- volatility: volatile
- summary: The vendor ships one agent skill that gives a coding agent the three question types,
  the architectural patterns, and best practices for structuring evaluations. It is an
  orientation and design aid.

Installation, per the page:

```bash
npx skills add typesafe-ai/skills --skill typesafe-ai
```

The installer asks which agent to target, installs project-local by default, and takes `-g` for a
global install. A Claude Code plugin path exists as well, and a manual copy of the vendor's
skill folder is a third option; the page asks for exactly one method to avoid duplicate copies.
Updates come through the same installer, the plugin marketplace, or a fresh copy, and the page
notes that a stale copy is what causes an agent to invent request or response fields.

Two habits from the page carry into this skill: keep the constants (questions and thresholds) in
a single file so a human can review them, and expect to edit questions collaboratively rather
than accepting a first draft.

## Vercel AI SDK and AI Gateway

- source_url: https://ai-sdk.dev/docs/ai-sdk-core/evaluation
- last_verified_at: 2026-10-01
- applies_to: the evaluation API of the `ai` package, its question types, and its confidence reporting
- volatility: volatile
- summary: The SDK exposes `experimental_evaluate`, which takes a model, one shared `state`, and a
  map of questions, and returns one answer per question id. The API and the evaluation model
  specification are marked experimental and may change in patch releases.

Differences from the direct route that matter when writing code:

- The question type for a yes/no judgment on this route is `boolean`, not `noul`. Answers carry a
  required `probability`, described as the model-estimated probability of true, checked to be
  finite and inside `[0, 1]`. The SDK does not promise calibration.
- Choice and Score distributions are optional here, and language-model adapters may not supply
  them at all. When a distribution is present the SDK validates that it sums to one, at a default
  absolute tolerance of `0.000001`, and rejects invalid output rather than normalizing it.
- TypeSafe's own Choice and Score confidence is exposed at
  `result.providerMetadata?.typesafe?.confidence`, keyed by question id. The page warns it "is not
  the selected option's probability or a portable confidence measure" (evaluation, 2026-10-01).
- A string model id resolves through Vercel AI Gateway unless a default provider is configured,
  and Gateway authentication uses `AI_GATEWAY_API_KEY` or Vercel OIDC.
- A provider factory form also exists: `typeSafeAi.evaluationModel('jev-latest')`.

Gateway model card, from the Gateway's own page:

- source_url: https://vercel.com/ai-gateway/models/jev
- last_verified_at: 2026-10-01
- applies_to: the Gateway listing for Jev
- volatility: volatile
- summary: Model id `typesafe-ai/jev`, type `evaluation`, providers listed as `typesafe-ai` and
  `digitalocean`, context window 32,000, maximum output tokens 0, price $0.042 per 1M input
  tokens. Detailed capability metadata was not reported, so treat the rest as unspecified here.

The version of the `@ai-sdk/typesafe-ai` package is not verified by this snapshot; pin the
installed version in the calling project instead of quoting a number.

## b.ai Decisions API

- source_url: https://docs.b.ai/llmservice/api/decisions-api/
- last_verified_at: 2026-10-01
- applies_to: the b.ai route, its request and response fields, and its settlement rules
- volatility: volatile
- summary: A second official route for the same model. It serves classification, scoring, and
  yes/no judgments and returns structured results rather than free-form text.

- Endpoint: `POST https://api.b.ai/v1/decisions`, with `Content-Type: application/json`. Only POST
  is supported; `stream` is omitted or set to `false`.
- Authentication, two ways: `Authorization: Bearer plus your key`, or the `x-api-key` header with
  the same value.
- `model` must be `jev-1.13.0` or `jev-latest`. No other id is accepted on this route.
- `state` accepts a string, object, or array. `null`, numbers, and booleans are rejected.
- `questions` is a non-empty map. Ids must not be empty or whitespace-only.
- `noul` criteria may be omitted; when present it must be an object whose only allowed keys are
  `"true"` and `"false"`, each mapping to a string, object, or array.
- `choice` criteria is required and must hold 1 to 255 options; a description may be `null`.
- `score` criteria is required and must be an array of 2 to 10 items, each a string, object, or
  array, and never `null`.

Response fields parallel the direct route: `model`, `answers`, and `usage`. On this route the
answer rules are stated explicitly. `confidence` is required for choice and score, and the page
notes that "noul does not return a separate confidence" (decisions, 2026-10-01). Choice and score
`probabilities` must carry exactly the option keys or string level indices of that question, and
"the values must sum to 1 within a tolerance of 0.0001" (decisions, 2026-10-01). A score answer
also needs `legend`, mapping each string level index to a non-null description. The confidence
value is derived from the distribution and must not be recomputed as the maximum option
probability; the page also warns it is not answer accuracy.

Two hard bounds: the two usage counts are required and their sum must not exceed 2147483647, and
responses larger than 16 MiB are rejected. Invalid answers or usage produce an error rather than
a success with estimated usage.

Rate limits behave differently here. A `429` may carry an empty or non-JSON body, so check the
HTTP status before parsing. Retry with bounded exponential backoff. The endpoint offers no
idempotency guarantee, so a retry after a timeout may repeat upstream work. Questions inside one
request are evaluated independently; one question cannot read another's answer, so dependent
questions either split into separate requests or combine in code.

Settlement converts at a fixed rate:

- source_url: https://docs.b.ai/llmservice/models/jev-1.13.0/
- last_verified_at: 2026-10-01
- applies_to: the b.ai model page, its listed capabilities, and its credit conversion
- volatility: volatile
- summary: The model id is `jev-1.13.0` with `jev-latest` resolving to it. Credits settle at
  1 USD = 1,000,000 Credits, and Jev is billed for input tokens only. The page repeats the 64K
  and 32K context limits, the 255 and 2-to-10 bounds, and states that noul has no separate
  confidence field.

That page also states the caution worth keeping: schema conformity does not guarantee correct
judgments, so validate thresholds on representative data and pin a versioned id when behavior
must stay consistent. The same page lists the unreliable areas, arithmetic, counting, date
comparisons, and multi-hop reasoning, and notes that multilingual work, including CJK text,
needs workload-specific validation. Prices on the page are described as standard reference
prices; bonuses and account benefits can lower the actual cost.

## Sources

> Links checked 2026-10-01. Next re-verification: 2026-10-31.

| Claim | Source |
| --- | --- |
| The endpoint, its headers, the request fields, the question id rule, the response fields, and the 401/422/429/529 behavior | <https://docs.typesafe.ai/api> |
| The three question types and their criteria rules and answer shapes | <https://docs.typesafe.ai/api> |
| Model ids, the two aliases, the price, the rate limits, the context budgets, text-only input, and the language-support note | <https://docs.typesafe.ai/models> |
| Confidence derivation, the "not one number" rule, and the 0.5 floor in the vendor example | <https://docs.typesafe.ai/confidence> |
| The nine jaggedness modes, their workarounds, and the 2026-09-17 review date | <https://docs.typesafe.ai/model-jaggedness/jev-1.13> |
| The official skill's scope, its install commands, the single-constants-file habit, and the stale-copy failure | <https://docs.typesafe.ai/agent-skill.md> |
| `experimental_evaluate`, the `boolean` type, the distribution tolerance, the Gateway confidence path, and the Gateway authentication note | <https://ai-sdk.dev/docs/ai-sdk-core/evaluation> |
| The Gateway model card: id, type, providers, context window, output tokens, and price | <https://vercel.com/ai-gateway/models/jev> |
| The b.ai endpoint, both auth headers, the model ids, the per-type criteria rules, the answer fields, the 0.0001 tolerance, the usage sum bound, the 16 MiB limit, and the 429 guidance | <https://docs.b.ai/llmservice/api/decisions-api/> |
| The b.ai model page: ids, credit conversion, the context bounds, and the multilingual and schema-conformity cautions | <https://docs.b.ai/llmservice/models/jev-1.13.0/> |
| The JavaScript SDK page used for the `TypeSafeClient`, `client.systemOne`, `TYPESAFE_API_KEY`, and `choice()` facts | <https://docs.typesafe.ai/sdk/javascript.md> |
| The page inventory used to find the pages above | <https://docs.typesafe.ai/llms.txt> |

### Evidence grade

`PRIMARY` for everything on this page. Each row of the table above is a vendor page belonging to
the service being described, captured verbatim on 2026-10-01 and stored alongside this snapshot's
evidence. The one exception is the b.ai pages, which are JavaScript-rendered and were read as
rendered article text rather than raw markdown; the text was read in full and did not change
between two reads.

Not evidenced by these pages, and deliberately left unspecified: the version of the
`@ai-sdk/typesafe-ai` package, any claim that the JavaScript SDK carries helpers for question
types other than `choice`, and the number of vendor cookbooks.
