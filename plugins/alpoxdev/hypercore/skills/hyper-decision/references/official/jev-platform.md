# Jev Platform Snapshot

What the vendor pages say about Jev as a platform: the HTTP endpoint, the request and answer shape,
the limits and price in force when this file was written, the published confidence formulas, the
known jagged edges of the current version, the client SDKs, and every route this snapshot covers.
Everything here was read from the pages listed under Sources and captured on 2026-11-08. This file
is one of the few places in this package where price, limits, model aliases, and route contracts
belong; the cross-vendor route reference is next to it, and the OpenAI facts are in their own file
beside this one.

## Contents

- Refresh Policy
- System One endpoint
- Models, aliases, limits, and price
- Question types
- Answer types, confidence, and its formulas
- Images, assets, and Box
- Errors and request rules
- Model jaggedness
- Client SDKs
- Official agent skill
- Vercel AI SDK and AI Gateway
- Other documented routes
- Availability
- Sources
- Evidence grade

## Refresh Policy

- last_verified_at: 2026-11-08
- refresh_when:
  - a vendor page changes a rate limit, price, context window, or model alias
  - a route adds or drops a documented endpoint
  - the question or answer shape changes (`noul`, `choice`, `score`, `box`)
  - the jaggedness list, the confidence formulas, or the error table changes
  - a client SDK ships a minor version
- supports_rules:
  - rules/modes-and-routing.md
  - rules/safety-and-boundaries.md

When this snapshot is more than 30 days old and the network is available, re-read the vendor pages
read-only and update the dates here. When the network is not available, say the date out loud
instead of guessing at current values.

## System One endpoint

- source_url: https://docs.typesafe.ai/api/system-one.md
- last_verified_at: 2026-11-08
- applies_to: the direct HTTP route, its request and response shape, and its error codes
- volatility: stable
- summary: One endpoint answers typed questions about a shared `state` and returns one structured
  answer per question id. All four question types go to the same URL; the `model` field in the body
  picks the version that answers.

```http
POST https://api.typesafe.ai/v1/systemone
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

The live OpenAPI document at `https://api.typesafe.ai/openapi.json` reports `info.version` `0.2.0`
and declares exactly two paths: `POST /v1/systemone` and `GET /v1/models`.

Request body:

| Field | Type | Notes |
| --- | --- | --- |
| `state` | string, object, or array | The content to evaluate. Text, JSON, or a structure that holds image placeholders. |
| `model` | string | `jev-latest` is the default alias. See the alias table below. |
| `questions` | map of id to question | `minProperties: 1`. Answers come back under the same ids. The vendor states the id is not used in inference. |
| `assets` | map, optional | Media assets keyed by an opaque placeholder. See the images section below. |

Required request fields per the schema are `model`, `state`, and `questions`. Every question carries
`type` and `instructions`. `instructions`, and every criteria entry, accept a string, object, array,
or `null` (`EntryType` in the schema).

Response body: `model` (the id that answered), `answers` (one per question id, each carrying a
`type` discriminator of `noul`, `choice`, `score`, or `box`), and `usage` with `input_tokens` and
`output_tokens`. Output tokens are documented as currently free of charge, and the JavaScript SDK
allows null token counts in `usage`.

`GET /v1/models` returns `{ models: [{ name, description, release_date }] }`. The vendor notes that
it currently lists the aliases, and that versioned ids such as `jev-1.14.0` are accepted whether or
not they appear in the list.

## Models, aliases, limits, and price

- source_url: https://docs.typesafe.ai/models.md
- last_verified_at: 2026-11-08
- applies_to: model ids and aliases, rate limits, context length, accepted input, question types, price
- volatility: volatile
- summary: Two versions are live. `jev-1.14.0` is the current release and both aliases point at it.
  Price is charged on input tokens only; output tokens are free. Rate limits are no longer published
  as numbers.

| Item | Value on 2026-11-08 |
| --- | --- |
| Versioned ids | `jev-1.14.0` (2026-10-14) and `jev-1.13.0` |
| `jev-latest` | resolves to `jev-1.14.0`, the SDK default |
| `jev-preview` | resolves to `jev-1.14.0`; the vendor states there is no preview build right now |
| Price | `$42` per billion input tokens, or `$0.042` per million. Output tokens are free |
| Rate limits | set per organization and shown in the developer console; measured in tokens per second and requests per second |
| Context | 64k tokens per request; 32k for the state plus the longest single question |
| Long context | sending `TypeSafe-Danger-Zone-Long-Context: true` raises both limits to 262k tokens |
| Question types | 1.14: Choice, Score, Noul, Box. 1.13: Choice, Score, Noul |
| Input | text and images; audio and video are not natively supported |

Rate limits deserve a plain statement: no current numeric limit is public. An archived snapshot
from 2026-09-29 showed 250,000 tokens per second and 1,200 requests per minute; a 2026-10-03
snapshot showed 100K tokens per second and 80 requests per second; the number was then removed from
the page entirely. Any hard number in a generated artifact is historical. A request over a limit
returns `429`.

The long-context header is documented as costing the same per token, and as slower and less
accurate than staying within the default limits. It works on 1.13 and 1.14 and is off by default.

Language support: the 1.14 changelog lists "better multilingual support" and the vendor states
English is where accuracy is best. Test non-English workloads against your own data before trusting
them.

Because an alias moves when a release ships, answers behind `jev-latest` can change with no change
on the caller's side. The response `model` field reports the version that answered. When confidence
thresholds were tuned against one version, pin that version id and move on purpose.

## Question types

- source_url: https://docs.typesafe.ai/primitives.md
- last_verified_at: 2026-11-08
- applies_to: the four question types, their criteria rules, and their answers
- volatility: stable
- summary: A question is one of four types. All four share `type` and `instructions`; three add
  their own `criteria` rules and Box adds none.

| Type | Criteria | Answer |
| --- | --- | --- |
| `noul` | optional `NoulCriteria` with `true` and `false`, nullable | `noul`, a number from 0 to 1, and no separate confidence |
| `choice` | required map of option to description, `minProperties: 1`, `maxProperties: 255` | `choice`, `probabilities`, `confidence` |
| `score` | required ordered array of level descriptions, `minItems: 1`, `maxItems: 10` in the schema; the prose says at least two | `score`, `legend`, `probabilities`, `confidence` |
| `box` | none; the vendor states "Box takes no `criteria`" | `box` with four edges, and `confidence` which may be null |

`noul` is the probability that the answer is yes, not a degree score: values near 0.5 mean
uncertainty. `score` returns a probability-weighted mean of level indices, so a three-level answer
can come back as `1.05`, and `legend` maps each level index back to its description. In HTTP JSON the
legend keys are stringified integers; the Python SDK exposes them as integers.

One documented conflict matters when a request is generated: the OpenAPI schema accepts a
`score` with a single level (`minItems: 1`), while the prose says a score "Should have at least two
levels". The AI SDK documents that TypeSafe and Perplexity accept a single level, returning score
`0` with probability `1`. Keep two or more levels in a generated artifact for portability, and know
that the API will not reject one level.

## Answer types, confidence, and its formulas

- source_url: https://docs.typesafe.ai/confidence.md
- last_verified_at: 2026-11-08
- applies_to: how certainty is reported, how it is computed, and how to gate behavior on it
- volatility: stable
- summary: Choice and Score answers carry a `confidence` from 0 to 1 computed from the answer's
  probability distribution. A concentrated distribution gives a high value; a flat one gives a low
  value. Noul answers carry no confidence field. Box answers carry one that may be null.

The vendor now publishes the formulas:

| Type | Formula | Note |
| --- | --- | --- |
| Noul | none | the docs offer `abs(2p - 1)` as a convenience, not as an API field |
| Choice | `(p_max - 1/n) / (1 - 1/n)` | `n` is the number of options |
| Score | `max(0, 1 - sum(p_i * abs(i - m)) / MAD_unif)`, where `MAD_unif = (1/n) * sum(abs(i - (n-1)/2))` | `m` is the score mean, `i` the level index |

Because Choice confidence is a transformation of the top probability, the vendor states that
checking both "adds no independent evidence". Threshold the probability of the option you act on,
and read the number as risk: acting only above 0.9 is acting when the chance of a wrong option is
under 10 percent.

Starting thresholds the vendor names: Noul `0.7` and `0.3`, with an explicit third outcome for the
band between them; Score routing at `confidence < 0.5`. The vendor also states plainly that "a
confidence threshold is not one number", and that the right value depends on your domain and on the
model's performance for your use case.

Two cautions carried into every generated artifact. Schema conformity is not correctness: a
well-formed answer can be wrong. And `confidence` is not the probability that the selected answer is
correct.

## Images, assets, and Box

- source_url: https://docs.typesafe.ai/images.md
- last_verified_at: 2026-11-08
- applies_to: image input, the `assets` map, the gating header, and the limits
- volatility: volatile
- summary: Images are accepted on both live versions, in `state`, `instructions`, and `criteria`,
  behind a header and a request-level `assets` map. Box questions need 1.14.

Images and Box are gated by `TypeSafe-Danger-Zone-Images: true` on every request that carries an
image or a Box question. Without the header the request returns `400`.

Two transport shapes:

- JSON with an `assets` map. Each asset is keyed by an opaque placeholder, recommended to be a
  per-image UUID, and every occurrence of that placeholder inside a string in `state`, question
  `instructions`, or `criteria` is replaced with the asset. Object keys are not replaced.
- Multipart. The JSON request is the first part, named `request`, and each image is its own part.

Asset fields: `type` (optional but must be `image` when sent), `format` (`png`, `jpg`, `jpeg`; required
with `data_base64`), `data_base64`, and `part` (the multipart part name; with `part`, `data_base64` is
ignored).

Limits, per the vendor's limits table:

| Item | Limit |
| --- | --- |
| File size | 16 MiB per image file |
| Width and height | 280 to 1568 pixels each |
| Total pixels | 78,400 to 2,458,624 |
| All images in one request | 32 MiB |
| Expanded request | 32 MiB after every reference is replaced by its image |
| Reference length | at most 1,024 bytes of UTF-8 each, and 65,536 bytes across the request |
| Formats | PNG and JPEG; animated PNGs are rejected |

Every asset must be referenced; an unreferenced asset returns `400`. Each use adds the image again,
so repeating a reference costs tokens again. The API strips all metadata, including EXIF and color
profiles, and does not apply EXIF orientation. Each image counts as input tokens at the normal input
price; there is no separate image charge.

Box, per `primitives/box.md` and the schema:

- `BoxQuestion` requires `type` and only otherwise takes `instructions`; it takes no criteria.
- `BoxAnswer` requires `type`, `box`, and `confidence`. `BoxCoordinates` requires `top`, `bottom`,
  `left`, and `right`, each a fraction of height or width in the range 0 to 1, and each documented as
  the expected value of that edge's predicted position.
- `confidence` is `number | null`; the schema example shows `null` and the worked page shows `0.92`.
- There is no "not found" answer. A Box question about something absent still returns four edges, so
  pair it with a companion Noul.
- The vendor labels images and Box "Dreamer-ready": "Images and Box questions aren't yet up to our
  standards to call ready for production", and the request format, answers, and limits can change
  between releases.

## Errors and request rules

- source_url: https://docs.typesafe.ai/api/errors.md
- last_verified_at: 2026-11-08
- applies_to: status codes, body rules, compression, and the one documented machine-readable code
- volatility: stable
- summary: The error table has seven rows and the request rules are explicit about size, nesting,
  numbers, and compression.

| Status | Meaning |
| --- | --- |
| `400` | a request rule was violated, or an image or asset rule failed |
| `401` | missing or invalid key |
| `413` | payload too large |
| `415` | unsupported media type, including an unsupported compression encoding |
| `422` | the body failed validation, and the body names the offending field |
| `429` | a rate limit was hit |
| `529` | the service is temporarily overloaded |

Request rules:

- Body size at most 32 MiB; headers do not count.
- UTF-8 JSON without a byte order mark.
- At most 64 nested levels.
- Finite numbers only; `NaN`, `Infinity`, and values such as `1e400` are rejected.
- `Content-Encoding: gzip` (or `x-gzip`) or `zstd` is accepted, with a zstd window at most 8 MiB. The
  32 MiB limit applies to both the compressed and the decompressed body.

The only machine-readable error code documented anywhere in the corpus is `max_tokens_exceeded`.
Image and asset failures are plain `400` or `413` with prose causes. The OpenAPI document declares
only `200`, `400`, and `422` for `/v1/systemone`; `401`, `413`, `415`, `429`, and `529` are documented
in prose only.

The vendor's advice for `429` and `529` is to back off and retry after a short delay. The client SDKs
do this by default; see the SDK section for the exact defaults.

## Model jaggedness

- source_url: https://docs.typesafe.ai/model-jaggedness.md
- last_verified_at: 2026-11-08
- applies_to: known failure modes of the current model line and the workaround the vendor recommends
- volatility: volatile
- summary: The page lists nine failure modes. It is no longer version-scoped: the page title carries
  no version, and the page contains no version string at all. The old "Common-sense structural
  invariants" mode was replaced.

| # | Failure mode | Do this instead |
| --- | --- | --- |
| 1 | Literal reading: the answer follows the words written, not the intent behind them | Write the exact condition, and put boundary cases in the criteria |
| 2 | Math and numbers: counting, arithmetic, and numeric representations are unreliable | Keep the arithmetic in code; use names instead of hex or binary values |
| 3 | Date and time comparison: dates are read as text, not as ordered quantities | Extract the parts as a closed set, then assemble and compare in code |
| 4 | Indirection: double negatives and multi-hop questions cost accuracy | Reduce hops and point at the relevant state by name |
| 5 | Large state full of irrelevant detail: unrelated content acts as a distractor | Filter in code first and send only the fields the question needs |
| 6 | Adversarial content: state is data and is not treated as hostile by default | Write precise prompts and test edge cases before deploying widely |
| 7 | Contradictory instructions and criteria: the two can fight each other | Treat the criteria as an extension of the instruction and align the wording |
| 8 | Choice option order: the vendor observed that option order can affect the answer, and Jev leans toward the first option | Reorder the options and check that the answer stays consistent |
| 9 | Generation: the model is not trained to produce text | Use a generative model, or turn extraction into a Choice over enumerated options |

Two further statements belong with the list. Counting is called out as unreliable inside the Math
section. And Score levels are weak in numerical calibration: the vendor states Jev "will not be able
to help you reconstruct the exact number by interpolating between the nearest two levels". Use a
Score to decide whether a value clears a threshold, not to recover the value.

The old mode 8 carried the negation and identity guidance, including the worked example where a
question and its negation summed to more than 1. That section is gone from the current page. The
practical carry-over survives: do not assume a question and its negation sum to 1, and do not carry a
threshold tuned on one question over to a different one.

## Client SDKs

- source_url: https://docs.typesafe.ai/sdk/javascript.md and https://docs.typesafe.ai/sdk/python.md
- last_verified_at: 2026-11-08
- applies_to: package names, versions, environment variables, and retry defaults
- volatility: volatile
- summary: Both SDKs ship on 2026-10-14, both support images and Box, and both read the same four
  environment variable names.

| Item | JavaScript | Python |
| --- | --- | --- |
| Package | `@typesafe-ai/sdk` `0.7.0` (2026-10-14) | `typesafe-sdk` `0.7.5` (2026-10-14), import `typesafe_sdk` |
| Runtime floor | Node.js 22 or newer | Python 3.10 or newer |
| Client | `TypeSafeClient` | `TypeSafeClient` and `AsyncTypeSafeClient` |
| API key variable | `TYPESAFE_API_KEY` | `TYPESAFE_API_KEY` (`API_KEY_ENV`) |
| Base URL variable | `TYPESAFE_BASE_URL`, default `https://api.typesafe.ai` | `TYPESAFE_BASE_URL` (`BASE_URL_ENV`) |
| Model variable | `TYPESAFE_DEFAULT_MODEL`, default `jev-latest` | `TYPESAFE_DEFAULT_MODEL` (`DEFAULT_MODEL_ENV`) |
| Log level variable | `TYPESAFE_LOG_LEVEL`, default `warn` | `TYPESAFE_LOG_LEVEL` (`LOG_LEVEL_ENV`) |
| Request compression | zstd for bodies of 1 KiB or more on Node 22.15+; disable with `compression: false` | zstd by default, with a `zstd` extra |
| Default timeout | 10,000 ms | `DEFAULT_TIMEOUT = 10.0`; `RetryPolicy` carries `timeout=30.0` |

Retry defaults, as documented:

- JavaScript `RetryPolicy`: `maxRetries 2`, `httpStatuses {408, 429, 500 to 599}`,
  `backoffInitialMs 500`, `backoffMaxMs 5000`, `backoffJitter 0.25`, `maxRetryAfterMs 60000`,
  `respectRetryAfter true`, and retries on connection and timeout errors.
- Python `RetryPolicy`: `max_retries=2`, `backoff_initial=0.5`, `backoff_max=5.0`,
  `backoff_jitter=0.25`, `http_statuses={408, 429, 500 to 599}`, `respect_retry_after=True`,
  `timeout=30.0`.

Note what the default set excludes: `529` is not in either retry list, so an overloaded response is
surfaced to the caller unless the policy is widened.

Other documented surface: the JavaScript package exports `TypeSafeClient`, a `choice()` helper, a
`box()` helper, `image()`, `Image.fromBase64()`, asset helpers, `ENV`, and typed error classes, and
sends image requests as multipart. The Python package exposes `system_one(...)`, `models.list()`, a
`response_model=` option, and per-type views `nouls`, `choices`, `scores`, and `boxes`.

## Official agent skill

- source_url: https://docs.typesafe.ai/agent-skill.md
- last_verified_at: 2026-11-08
- applies_to: the vendor-published agent skill and how it is installed
- volatility: volatile
- summary: The vendor ships one agent skill that gives a coding agent the question types, the
  patterns, and the practices for structuring evaluations. It is an orientation and design aid.

Two install routes are documented, and the page asks for exactly one to avoid duplicate copies:

```bash
npx skills add typesafe-ai/skills --skill typesafe-ai
```

```bash
claude plugin marketplace add typesafe-ai/skills
claude plugin install typesafe@typesafe-ai
```

The installer asks which agent to target, installs project-local by default, and takes `-g` for a
global install. Updates come through the same installer or the plugin marketplace, and the page notes
that a stale copy is what causes an agent to invent request or response fields. The GitHub repository
still resolves, but its doc links use a `/go/*` prefix that redirects to the canonical pages.

## Vercel AI SDK and AI Gateway

- source_url: https://ai-sdk.dev/docs/ai-sdk-core/decisions
- last_verified_at: 2026-11-08
- applies_to: the decision API of the `ai` package, its question types, its confidence reporting, and
  the Gateway routes for Jev
- volatility: volatile
- summary: The SDK function is now `experimental_decide`; the old name `experimental_evaluate` is a
  deprecated alias. The provider interface is `Experimental_DecisionModelV4` and is isolated from the
  stable provider contract.

Facts that matter when writing code:

- `experimental_decide({ model, state, questions, ... })` decides answers to named questions
  against one shared state. `experimental_evaluate` still exists as a deprecated alias with the same
  shape, and was renamed in `ai@7.0.128` on 2026-10-05.
- `Experimental_DecisionModelV4` is exported from `@ai-sdk/provider`, carries
  `specificationVersion: 'v4'`, `provider`, `modelId`, `supportedQuestionTypes`, and `doDecide()`,
  and its source comment says it may change in patch releases. Pin the installed versions: `ai`
  `7.0.164` and `@ai-sdk/provider` `4.0.36` were current on 2026-11-06.
- The question type for a yes/no judgment on this route is `boolean`, which the TypeSafe provider
  maps to `noul`. Boolean answers carry a required `probability`. The SDK does not promise
  calibration across providers.
- The TypeSafe provider factory is `typeSafeAi.decisionModel('jev-latest')`; the old
  `evaluationModel` is a deprecated alias. Its package is `@ai-sdk/typesafe-ai` `3.0.34`.
- The TypeSafe provider reads `TYPESAFE_AI_API_KEY` and `TYPESAFE_AI_BASE_URL` (default
  `https://api.typesafe.ai/v1`). These names are deliberately different from the TypeSafe SDK's
  `TYPESAFE_API_KEY` and `TYPESAFE_BASE_URL`.
- TypeSafe's own choice and score confidence is at
  `result.providerMetadata.typesafe.confidence[questionId]`, and the structured Score legend is at
  `result.providerMetadata.typesafe.legend[questionId]`. The docs warn confidence "is not the
  selected option's probability or a portable confidence measure".
- When a distribution is present, the SDK validates that it matches the answer and rejects invalid
  output rather than normalizing it, at a default absolute tolerance of `0.000001`.
- Provider support is uneven by design. The TypeSafe provider supports all four types including
  `box`; OpenAI, Perplexity, and Parallel support the first three natively; the Anthropic and Google
  adapters emulate all three over structured output and omit choice and score probability
  distributions entirely.
- Only the Gateway route has decision-aware routing, through `providerOptions.gateway.models`.

Gateway model ids and cards:

| Item | Value |
| --- | --- |
| Model id on the Gateway | `typesafe-ai/jev`, with `typesafe-ai/jev-1.13.0` and `typesafe-ai/jev-1.14.0` also in the catalog |
| Providers listed on the card | `typesafe-ai` and `digitalocean` |
| Context window on the card | 32,000 |
| Maximum output tokens | 0 |
| Price | `$0.042` per million input tokens; output `$0` |
| Catalog type label | `evaluation`, not `decision`; filtering on `decision` returns nothing |
| Supported specification | `v4` |

The Gateway exposes two decision surfaces for Jev: an OpenAI-compatible `POST /v1/decisions` with
`predicate`, `choice`, and `score` questions, and a TypeSafe-compatible base URL at
`https://ai-gateway.vercel.sh/typesafe` with `POST /typesafe/v1/systemone` and
`GET /typesafe/v1/models`.

One reproducibility defect is open: on the Gateway, `response.modelId` comes back as the alias that
was sent, and no field in the result names a version (vercel/ai issue #21213, open since 2026-09-20).
`jev-latest` moved from 1.13 to 1.14 on 2026-10-14, so an unpinned Gateway call can change model
underneath an unchanged request. Pin a versioned id where reproducibility matters, and log the
reported model.

## Other documented routes

Each of these is an official route for the same model, with its own contract. The cross-vendor
comparison and the route choice order are in the sibling route reference.

### b.ai Decisions API

- source_url: https://docs.b.ai/llmservice/api/decisions-api/
- last_verified_at: 2026-11-08
- summary: `POST https://api.b.ai/v1/decisions`, Bearer or `x-api-key`, POST only with `stream`
  omitted or `false`. Only `jev-1.13.0` and `jev-latest` are accepted, and there is no box type.

Answer rules: choice and score carry `confidence` (noul does not), `probabilities` must carry exactly
the option keys or string level indices, and values must sum to 1 within 0.0001. A score answer also
carries `legend`. Usage counts are required and their sum may not exceed 2147483647; responses over
16 MiB are rejected. A `429` may carry an empty or non-JSON body, so check the status first. There is
no idempotency guarantee, so a retry after a timeout may repeat work. Credits settle at 1 USD =
1,000,000 Credits.

The 1.14 model page is not in b.ai's sitemap, so the absence of 1.14 there is sitemap-scoped rather
than proven.

### DigitalOcean Inference

- source_url: https://docs.digitalocean.com/products/inference/how-to/use-system-one-api/
- last_verified_at: 2026-11-08
- summary: `POST https://inference.do-ai.run/v1/systemone` with
  `Authorization: Bearer $MODEL_ACCESS_KEY`, serving one id, `typesafe-jev-1.13.0`. The page was last
  verified by the vendor on 2026-09-28.

The page documents text state and the `noul`, `choice`, and `score` types only. It documents no image
path and no box type, and states that Jev is a third-party model, so the account must be on a
qualifying tier. Treat images and box as unsupported on this route until the vendor documents them.

### OpenRouter

- source_url: https://openrouter.ai/docs/guides/community/jev
- last_verified_at: 2026-11-08
- summary: Two surfaces. `POST https://openrouter.ai/api/alpha/decisions` is alpha and the vendor
  warns the shape may change; `POST https://openrouter.ai/api/v1/systemone` is the System One surface.
  The Jev model id is `typesafe/jev-1.14`, with `~typesafe/jev-latest` as the router alias used by the
  TypeSafe SDK against base URL `https://openrouter.ai/api`.

The model endpoint reports a `262,144` context length and `$0.000000042` per prompt token. Box
questions are "Served by TypeSafe Jev endpoints only; every other provider rejects a box question
with `400`" before anything is sent upstream. The OpenRouter model list is not TypeSafe's shape, so
the TypeSafe SDK's `models.list()` fails there.

## Availability

- source_url: https://status.typesafe.ai/index.json
- last_verified_at: 2026-11-08
- summary: The status feed carried eight incidents at read time, updated 2026-11-07, including
  `2026-10-30 System overload`, `2026-10-14 Elevated Latency`, `2026-09-28 Degradation in API
  Traffic`, and `2026-09-21 API issues`.

The feed reports no public uptime percentage: every resource's `uptime` field is null. Treat the
service as fast and useful but not uniformly available, keep retries and a fallback path in any
request path that must not fail, and do not quote an uptime figure.

## Sources

> Links checked 2026-11-08.

| Claim | Source |
| --- | --- |
| The `/v1/systemone` path, the Bearer header, the request fields, the question id rule, and the response fields | <https://docs.typesafe.ai/api/system-one.md> |
| OpenAPI `info.version` 0.2.0, the two paths, the `questions` minimum, the `assets` map, the 1 to 255 and 1 to 10 bounds, the answer `type` discriminator, the `confidence` union on Box, and the two header enums | <https://api.typesafe.ai/openapi.json> |
| The four question types and their criteria rules, and the Box "takes no criteria" rule | <https://docs.typesafe.ai/primitives.md>, <https://docs.typesafe.ai/primitives/box.md> |
| `jev-1.14.0` and `jev-1.13.0`, both aliases on 1.14, the per-organization rate limit text, the 64k/32k default, the 262k long-context header, the question types per version, and text plus image input | <https://docs.typesafe.ai/models.md> |
| The 1.14 release on 2026-10-14, multilingual support, Box, images, and long context | <https://docs.typesafe.ai/changelog.md> |
| The image header, the `assets` rules, the limit table, metadata stripping, and the token cost of images | <https://docs.typesafe.ai/images.md> and <https://docs.typesafe.ai/concepts/state.md> |
| The three confidence formulas, the "adds no independent evidence" line, and the 0.7, 0.3, and 0.5 starting thresholds | <https://docs.typesafe.ai/confidence.md> |
| The seven error rows, the 32 MiB body limit, 64 nesting levels, the finite-number rule, the compression rules, and `max_tokens_exceeded` | <https://docs.typesafe.ai/api/errors.md> |
| The nine jaggedness modes, mode 8 being choice option order, the unversioned page, and the weak Score interpolation | <https://docs.typesafe.ai/model-jaggedness.md> |
| The documented thresholds for Noul and Score routing | <https://docs.typesafe.ai/patterns/probability-routing.md> and <https://docs.typesafe.ai/patterns/confidence-routing.md> |
| The JS SDK version, Node floor, `ENV` variable names, retry defaults, and compression behaviour | <https://docs.typesafe.ai/sdk/javascript.md>, <https://docs.typesafe.ai/sdk/javascript/changelog.md>, <https://docs.typesafe.ai/sdk/javascript/api/variables/ENV.md>, <https://docs.typesafe.ai/sdk/javascript/api/interfaces/RetryPolicy.md> |
| The Python SDK version, constants, retry defaults, and per-type views | <https://docs.typesafe.ai/sdk/python.md>, <https://docs.typesafe.ai/sdk/python/changelog.md>, <https://docs.typesafe.ai/sdk/python/api/constants.md>, <https://docs.typesafe.ai/sdk/python/api/retries.md> |
| The two agent-skill install routes and the stale-copy warning | <https://docs.typesafe.ai/agent-skill.md> |
| `experimental_decide`, `Experimental_DecisionModelV4`, the `boolean` mapping, the tolerance, and provider coverage | <https://ai-sdk.dev/docs/ai-sdk-core/decisions>, <https://ai-sdk.dev/docs/reference/ai-sdk-core/decide> |
| `typeSafeAi.decisionModel`, `TYPESAFE_AI_API_KEY`, `TYPESAFE_AI_BASE_URL`, `providerMetadata.typesafe.confidence`, and `.legend` | <https://ai-sdk.dev/providers/ai-sdk-providers/typesafe-ai> and <https://github.com/vercel/ai/pull/24627> |
| The rename from `experimental_evaluate` to `experimental_decide` in `ai@7.0.128` on 2026-10-05 | <https://github.com/vercel/ai/pull/21935> |
| The Gateway model id, providers, context, output tokens, price, and `evaluation` type | <https://vercel.com/ai-gateway/models/jev> |
| The three versioned Gateway ids, the `v4` specification, and the 15 `evaluation` entries | <https://ai-gateway.vercel.sh/v1/models> |
| The OpenAI-compatible Gateway decisions route and its question bounds | <https://vercel.com/docs/ai-gateway/sdks-and-apis/openai-decisions> |
| The TypeSafe-compatible Gateway paths | <https://vercel.com/docs/ai-gateway/sdks-and-apis/typesafe> |
| The alias-only `modelId` defect | <https://github.com/vercel/ai/issues/21213> |
| The b.ai endpoint, auth headers, accepted ids, answer rules, 0.0001 tolerance, usage sum bound, 16 MiB limit, and 429 advice | <https://docs.b.ai/llmservice/api/decisions-api/> |
| The b.ai model page, credit conversion, context bounds, and cautions | <https://docs.b.ai/llmservice/models/jev-1.13.0/> |
| The DigitalOcean endpoint, `MODEL_ACCESS_KEY`, the single id, and the tier restriction | <https://docs.digitalocean.com/products/inference/how-to/use-system-one-api/> |
| The OpenRouter surfaces, alpha warning, box rejection rule, and the `typesafe/jev-1.14` id | <https://openrouter.ai/docs/guides/community/jev> |
| The OpenRouter context length and prompt price | <https://openrouter.ai/api/v1/models/typesafe/jev-1.14/endpoints> |
| The TypeSafe SDK's OpenRouter base URL and slug | <https://docs.typesafe.ai/sdk/python/usage/basic.md> |
| The status incidents and the null uptime fields | <https://status.typesafe.ai/index.json> |
| The page inventory used to find the pages above | <https://docs.typesafe.ai/llms.txt> |

### Evidence grade

`PRIMARY` for everything in this file except the availability section and the two clearly marked
third-party facts. Each fact comes from a vendor page belonging to the service being described,
captured on 2026-11-08. The Gateway catalog's `evaluation` type label and the 15-entry count come
from Vercel's own live API and are vendor facts about Vercel, not about TypeSafe; they are marked
where used. The status page is a vendor-operated BetterStack feed, so it is `PRIMARY` for the
incident list and `SECONDARY` for any inference about uptime, which it does not publish.

Not evidenced by these pages, and deliberately left unspecified: any current numeric rate limit, any
calibration promise, any latency benchmark beyond the vendor's own prose, and a 1.13 sunset date,
which no page states.
