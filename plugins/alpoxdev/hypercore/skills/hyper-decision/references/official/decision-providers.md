# Decision Provider Snapshot

Every vendor other than TypeSafe and OpenAI that ships a decision-style API as of 2026-11-08, plus the
two gateway layers, the provider coverage of the Vercel AI SDK, the general-model emulation tier, and
the fixed-classifier appendix. Facts here come from first-party vendor pages unless a row is marked
`B`, which means it rests on a third-party aggregator.

The cross-vendor route comparison, tiers, and route choice order are in the sibling route reference.
TypeSafe facts are in the Jev snapshot and OpenAI facts in the OpenAI snapshot.

## Contents

- Refresh Policy
- Perplexity Decisions
- Microsoft-Decision-1
- Liquid AI d1
- Cloudflare Clef
- Cloudflare Clairic, extraction only
- Parallel Decisions
- Baseten decision models
- Upstage Solar Decide
- Vercel AI SDK provider coverage
- Vercel AI Gateway decisions
- OpenRouter decisions and extractions
- T3: emulation on general models
- T4 appendix: fixed classifiers, guardrails, judges, retired surfaces
- Sources
- Evidence grade

## Refresh Policy

- last_verified_at: 2026-11-08
- refresh_when:
  - a vendor changes its endpoint, authentication, model ids, or question types
  - a vendor leaves beta, goes generally available, or is retired
  - an answer field changes, in particular where `confidence` lives or whether it exists
  - a gateway changes its decision surface, fallback contract, or billing rule
  - an AI SDK provider package ships a decision factory or changes what it emulates
  - a retirement date on the appendix passes

## Perplexity Decisions

- source_url: https://docs.perplexity.ai/docs/decisions/quickstart and
  https://docs.perplexity.ai/api-reference/decisions-post
- last_verified_at: 2026-11-08
- volatility: volatile
- summary: Perplexity keeps the System One field names (`state` plus a `questions` map,
  `noul`/`choice`/`score`) at its own `/v1/decisions` path, with its own models. It is the closest
  thing to a drop-in Jev replacement among the large vendors, and the only vendor that publishes its
  confidence formula besides TypeSafe.

| Item | Value |
| --- | --- |
| Endpoint | `POST https://api.perplexity.ai/v1/decisions` |
| Authentication | `Authorization: Bearer <key>` only; an `x-api-key` header returns 401 |
| Models | `pplx-decider-v1.2` (27B) and `pplx-decider-flash-v1.2` (4B); aliases `pplx-decider-latest` and `pplx-decider-flash-latest` |
| Question types | `noul`, `choice`, `score` |
| Options per `choice` | 1 to 255, and a `null` description is allowed |
| Levels per `score` | 1 to 10, with "use at least two" in the prose |
| Questions per request | at least 1; at most 100 in `mode: web_grounding` |
| Input | 256K input tokens for the state plus any one question; 32 MiB body |
| Images | up to 8 per question, 2,048 tiles each |
| Answer fields | `noul` scalar; `choice` with `probabilities` and `confidence`; `score` with `legend`, `probabilities`, and `confidence` |
| Price | `$0.02` per 1M input tokens for v1.2 and `$0.01` for flash; output free |
| Status | generally available, launched under October 2026 in the changelog |

Two operational traps. First, the state is billed again per question group or per question depending
on the model, so a many-question request is not as cheap as the per-token rate suggests. Second,
`web_grounding` caps the request at 100 questions and adds a per-search line item; both are request
level, not per answer.

Perplexity publishes the confidence formula it uses, for both choice and score. That makes it the one
vendor besides TypeSafe where a generated artifact may state how confidence is derived. It is still
not portable to another vendor.

## Microsoft-Decision-1

- source_url: https://learn.microsoft.com/en-us/azure/foundry/foundry-models/how-to/use-foundry-models-microsoft-decision
- last_verified_at: 2026-11-08
- volatility: volatile
- summary: A Foundry-hosted decision model that speaks the System One shape at a Microsoft-specific
  path on the customer's own Foundry resource. It is not the Azure OpenAI Decisions endpoint; that one
  is the `gpt-6-luna` contract in the OpenAI snapshot.

| Item | Value |
| --- | --- |
| Endpoint | `<your-foundry-resource-endpoint>/providers/microsoft/v1/systemone` |
| Authentication | Microsoft Entra ID bearer, or the `api-key` header |
| Model field | the deployment name, not the underlying model name |
| Question types | `noul`, `choice` with a `criteria` map, `score` with an ordered `criteria` list |
| Answer fields | `answers` keyed by question name, each `noul`, `choice` with `probabilities`, or `score` with `probabilities`, plus `model` and `usage` |
| Input | text or JSON state only; no image path is documented |
| Options and levels | counts are not stated on the how-to page |
| Price | per input token; the Gateway lists `$0.042` per 1M with output `$0` |
| Status | generally available in Foundry; how-to `ms.date` 2026-10-07; on the Gateway from 2026-10-09 |
| Regions | Europe (francecentral, germanywestcentral, italynorth, polandcentral, spaincentral, swedencentral, westeurope) and Asia Pacific (australiaeast, japaneast, japanwest, koreacentral, southeastasia, southindia); not available in Middle East and Africa |

The model does not generate prose: the how-to states it "doesn't generate a free-form response or
written rationale. It makes a focused judgment about text or JSON and returns a typed, numerical
decision." That is the cleanest statement in the corpus of what a decision model is for.

Because option and level counts are not documented, do not publish a limit for this route. Keep to the
portable bounds (2 to 255 options, 2 to 10 levels) rather than guessing at its own.

## Liquid AI d1

- source_url: https://docs.liquid.ai/api/guides/decisions and
  https://docs.liquid.ai/lfm/models/decision-models
- last_verified_at: 2026-11-08
- volatility: volatile
- summary: Liquid implements TypeSafe's System One API literally at its own path, serves it as a
  hosted product, and also ships open-weight decision models with extra primitives.

| Item | Value |
| --- | --- |
| Endpoint | `POST https://api.liquid.ai/decisions/v1/systemone` |
| Authentication | `Authorization: Bearer liquid_<key>` |
| Hosted models | `d1.1` (default, 65,536 context) and `d1-ultra` (32,768) |
| Open-weight models | `d1-2B`, `d1-omni-2B`, `d1-omni-600M` under the LFM Open License |
| Question types, hosted | `noul`, `choice`, `score` |
| Question types, open weights | also `box`/`boxes` and multi-select choice with `multiple: true` |
| Limits | 8 images per request, 4.5 MB body, 10,000 patches |
| Answer fields | `noul` scalar; `choice` and `score` with `probabilities` and `confidence` |
| Billing | input tokens only; output free |
| Errors | validation failures return `422` |
| Status | generally available (hosted) |

The vendor describes the model as returning "calibrated Noul, Choice, and Score answers with zero
generated tokens". Treat "calibrated" as a marketing adjective: no calibration curve or error metric
is published, here or for any other vendor in this file.

A model-id trap: Liquid's own docs name `d1.1` as the default hosted model and describe `d1` and
`d1-ultra` as the earlier models used on gateways. The Gateway catalog lists `liquid/d1` and
`liquid/d1-ultra`. Do not treat `d1` and `d1.1` as synonyms when writing a model id.

## Cloudflare Clef

- source_url: https://developers.cloudflare.com/ai/models/@cf/cloudflare/clef/ and the sibling model pages
- last_verified_at: 2026-11-08
- volatility: volatile
- summary: A family of open decision models hosted on Workers AI, invoked through the Workers AI
  binding rather than an HTTP decision path of their own. They use `noul`, so their payloads cannot be
  confused with the OpenAI dialect.

| Model | Size and context | Modalities | Price |
| --- | --- | --- | --- |
| `@cf/cloudflare/clef` | 27B, 65,536 context | text, JSON state, images (4 per request) | `$0.24` per 1M input tokens |
| `@cf/cloudflare/clef-flash` | 9B, 24,576 context | text, JSON state, images (4 per request) | `$0.038` per 1M input tokens |
| `@cf/cloudflare/clef-omni` | 30B mixture of experts, 3B active, 64,000 context | adds up to 4 audio clips and 2 videos | `$0.15` per 1M input tokens |

Shared properties: 1 to 64 questions per request, question ids use letters, digits, `_`, `.`, and `-`
up to 100 characters, `noul`/`choice`/`score` only, zero data retention, and output tokens are not
charged. The output schema requires `type`, `choice`, `probabilities`, and `confidence` on a choice
answer, and bounds `noul` to 0 to 1.

Invocation is `env.AI.run("@cf/cloudflare/clef")` inside a Worker, or the REST form
`POST /client/v4/accounts/{account_id}/ai/run/@cf/cloudflare/clef`. The request body carries `model`
and `input`, with `state` and `questions` nested inside `input` rather than at the top level. That
nesting is the difference most likely to break code copied from a `/v1/systemone` example.

## Cloudflare Clairic, extraction only

- source_url: https://developers.cloudflare.com/ai/models/@cf/cloudflare/clairic/
- last_verified_at: 2026-11-08
- volatility: volatile
- summary: A System One-style model that returns typed fields rather than answers to questions. It is
  an extraction route, not a decision route, and it is in preview.

| Item | Value |
| --- | --- |
| Model | `@cf/cloudflare/clairic`, 65,536 context |
| Field types | `text`, `number`, `date`, `time`, `datetime`, `duration`, `list`, `estimate`, `forecast` |
| Request | a `fields` map with no documented upper limit, plus a `reference_date` |
| Answer fields | `value`, `guess`, `span` or `spans`, `p_null`, `confidence`, `source`, and distribution keys (`mean`, `median`, `p10`, `p90`, `p_below`, `p_above`, `quantiles`, `steps`) |
| Input | text plus up to 4 PNG, JPEG, or WebP images |
| Other limits | an 8,192-token pass |
| Price | `$0.10` per 1M input tokens |
| Status | preview |

`p_null` is the field a decision-shaped design wants: it is the probability that the field is absent,
which is the closest thing extraction has to a refusal. Modelling extraction as a `choice` over
"present or absent" loses the value and its distribution, so keep the two routes apart in any generated
artifact.

## Parallel Decisions

- source_url: https://docs.parallel.ai/decisions/question-types and
  https://docs.parallel.ai/getting-started/pricing
- last_verified_at: 2026-11-08
- volatility: volatile
- summary: A decision API that retrieves web evidence before answering and returns citations at the
  request level. It is the one vendor billed per request rather than per token.

| Item | Value |
| --- | --- |
| Endpoint | `POST https://api.parallel.ai/v1/decisions` |
| Authentication | `x-api-key: <key>` |
| Model selector | a `mode` field defaulting to `fast`, instead of a `model` field |
| Question types | `noul`, `choice` with 2 to 255 criteria keys, `score` with 2 to 10 levels |
| Questions per request | 1 to 100 |
| Input | up to 32,000 input tokens per question including the state |
| Answer fields | `noul` 0 to 1; `choice` with `probabilities`; `score` with `legend` and `probabilities`; plus `refusal` and a request-level `citations[]` |
| Images | none; rejected with `400` |
| Price | `$1` per 1,000 requests, up to 100 questions each |
| Status | generally available |

Its answer type table carries no `confidence` field, unlike every other vendor here. `citations` is
request level: the array "contains sources for the whole call. It does not map individual sources to
answers." A generated artifact must not render citations as if each answer had one.

The per-request price inverts the usual cost model: 100 questions in one request cost the same as one,
so batching is the whole economic argument here.

## Baseten decision models

- source_url: https://docs.baseten.co/inference/model-apis/decision-models
- last_verified_at: 2026-11-08
- volatility: volatile
- summary: Baseten hosts small decision models behind the System One API, at three sizes and three
  prices.

| Item | Value |
| --- | --- |
| Endpoint | `POST https://inference.baseten.co/v1/systemone` |
| Models | `joey-1` (2B), `elephant-1` (9B), `mammoth-1` (27B, a Qwen3.5-27B tune) |
| Context | 16,384 tokens |
| Question types | `noul`, `choice`, `score` |
| Price | `$0.01`, `$0.035`, and `$0.10` per 1M input tokens respectively |
| Status | available; on the Gateway from 2026-10-21 with a free week through 2026-10-27 |

The model cards advertise "answer probabilities and confidence in a single forward pass", and an
aggregator lists up to 16 images for these models. The Gateway cards say nothing about images, so
image support differs by route and is unverified on the direct path.

## Upstage Solar Decide

- source_url: https://developers.upstage.ai/docs/models/solar-decide.md
- last_verified_at: 2026-11-08
- volatility: volatile
- grade: `B`, see below
- summary: A beta decision model served as a System One endpoint. It is the one entry in this file
  whose numbers do not reconcile across sources, which is why the route reference lists it as
  unverified.

| Item | Value | Conflict |
| --- | --- | --- |
| Status | Beta | none |
| Schema | "uses the same /v1/systemone schema as Jev" | no field list, no answer schema, no limit table published |
| Context | 512K in one source, 524K in another | unresolved |
| Price | `$0.05` per 1M input in one source, `$0.1` per 1M in another | unresolved |
| Release | 2026-09-22 on the model page, 2026-09-28 on an aggregator page | unresolved |
| Question types | `noul`, `choice`, `score` | none |
| Input | text only | none |

Grading is `B` because the first-party page states compatibility and status but not one request field,
one answer field, or one limit. A generated artifact may name this route and say it is beta; it may not
state a limit or a price for it, and it may not write calling code against it.

## Vercel AI SDK provider coverage

- source_url: https://ai-sdk.dev/docs/ai-sdk-core/decisions and the per-package sources
- last_verified_at: 2026-11-08
- volatility: volatile
- summary: Seven provider packages implement the decision interface. Four are native, two emulate over
  structured output, and one proxies to the Gateway.

| Package | Factory | Wire endpoint | Kind | Question types | Probabilities | Confidence path |
| --- | --- | --- | --- | --- | --- | --- |
| `@ai-sdk/typesafe-ai` 3.0.34 | `typeSafeAi.decisionModel(id)` | `POST {baseURL}/systemone`, multipart when images are present | native | all four, with `boolean` mapped to `noul` and `box` passed through | native `probabilities` on choice and score | `typesafe.confidence[questionId]` and `typesafe.legend[questionId]` |
| `@ai-sdk/openai` 4.0.110 | `openai.decisionModel('gpt-6-luna')` | `POST {baseURL}/v1/decisions` | native | choice, score, boolean mapped to `predicate` | `probabilities` records, rounded to two decimals | `openai.confidence[questionId]` |
| `@ai-sdk/perplexity` 5.0.27 | `perplexity.decisionModel(id)` | `POST {baseURL}/v1/decisions` | native | choice, score, boolean mapped to `noul`; box unsupported | native distributions, "without rounding or normalization" | `perplexity.confidence` and `perplexity.legend` |
| `@ai-sdk/parallel` 3.0.3 | `parallel.decisionModel('fast')` | `POST {baseURL}/decisions`, body key `mode` | native, web-grounded | choice, score, boolean mapped to `noul`; no files, no box | native `probabilities`, zero-based weighted mean for score | `parallel.confidence`, `parallel.legend`, plus `citations` |
| `@ai-sdk/anthropic` 4.0.98 | `anthropic.decisionModel(id)` | Messages API plus structured output, with a JSON-tool fallback | emulated | choice, score, boolean | none, ever | none |
| `@ai-sdk/google` 4.0.113 | `google.decisionModel(id)` | Gemini `generationConfig.responseJsonSchema` | emulated | choice, score, boolean | none, ever | none |
| `@ai-sdk/gateway` 4.0.137 | `gateway.decisionModel(id)` | `POST {baseURL}/decision-model` with `ai-decision-model-specification-version: 4` and `ai-model-id` | proxied | choice, score, boolean; box rejected client-side | whatever the routed model returns | provider-defined blob, passed through |

The shared emulation adapter lives in `@ai-sdk/provider-utils` and returns a bare choice label, a bare
score number, and a prompted P(true) for boolean, with no `probabilities` key at all. That is a
construction difference, not a model whim: `answer.probabilities?.[answer.choice]` is `undefined` on
Anthropic and Google by design.

Core behaviours that apply to every provider:

| Behaviour | Detail |
| --- | --- |
| Entry point | `experimental_decide`; `experimental_evaluate` is a deprecated alias |
| Provider contract | `Experimental_DecisionModelV4`, `specificationVersion: 'v4'`, `doDecide`, explicitly isolated from the stable provider contract and allowed to change in patch releases |
| Validation | distributions are checked against the answer and rejected rather than normalized, at a default absolute tolerance of `0.000001`; the `rounding` declaration allows half a unit in the last place per rounded value |
| Refusal | a refusal answer throws `Experimental_DecisionRefusalError`; there are no partial results |
| Calibration | "The SDK does not promise calibration across providers" |
| Log probabilities | no `logprob` symbol exists in the SDK's public decision types, so there is no emulation route through them |
| Unsupported options | `reasoning` and `maxOutputTokens` are accepted everywhere and honoured by almost no native provider, which emits an `unsupported` warning |

No provider package ships a decision factory for Baseten, Liquid, Microsoft-Decision-1, or ScaleDown,
even though the Gateway catalog routes to several of them. Where such a call is needed, the only
documented path is the TypeSafe provider with a custom base URL that implements `POST /systemone`, and
whether it accepts those vendors' payloads is unverified.

## Vercel AI Gateway decisions

- source_url: https://vercel.com/docs/ai-gateway/modalities/decision and
  https://vercel.com/docs/ai-gateway/models-and-providers/decision-fallbacks
- last_verified_at: 2026-11-08
- volatility: volatile
- summary: The Gateway puts one contract in front of native and emulated decision models, exposes two
  decision shapes, and adds a confidence-triggered fallback that no other route has.

Two surfaces:

| Surface | Path | Dialect | Notes |
| --- | --- | --- | --- |
| OpenAI-compatible | `POST https://ai-gateway.vercel.sh/v1/decisions` | OpenAI Decisions | `predicate`, `choice` with 1 to 255, `score` with 2 to 10; GET returns 405 |
| TypeSafe-compatible | base URL `https://ai-gateway.vercel.sh/typesafe`, `POST /typesafe/v1/systemone`, `GET /typesafe/v1/models` | System One | change only the base URL in the TypeSafe SDK; responses gain `provider_metadata.gateway` |

Decision fallbacks, the one decision-specific escalation mechanism in the corpus:

| Aspect | Contract |
| --- | --- |
| Entry shape | a string is an execution-error fallback; `{ model, when }` reruns after a successful primary whose answers match `when` |
| Predicates | `{ question, confidenceBelow }` for Choice and Score only; `{ question, probabilityBetween: [lo, hi] }` for Boolean and Noul only, inclusive; question-less forms check every question of the matching type |
| Combinators | `any`, `all`, and `atLeast: { count, conditions }` |
| Structural rules | the conditional object must be the first entry and `models` may hold only one; `question` is 1 to 256 characters and must name a question in the request; thresholds are finite in `[0, 1]` with `lo <= hi`; 1 to 20 conditions per combinator; nesting at most 5; only decision requests accept it, otherwise `400` before billing; the conditional model cannot equal the primary; one fallback stage per request |
| Sentinel | when a language model answers, the TypeSafe-compatible surface returns `confidence: 0` and `probabilities: {}` as unavailable sentinels, while `/v1/decisions` omits `confidence` and `probabilities`; Noul does not use the sentinel |
| Trigger reasons | `confidence_below`, `confidence_unavailable`, `probability_between`, `refused` |
| Headers | `x-ai-gateway-decision-fallback-{triggered, final-model, primary-model, triggering-questions, triggering-questions-truncated}`, plus deprecated `x-ai-gateway-evaluation-fallback-*` |
| Billing | a triggered fallback executes and bills both the primary and the fallback stages; no answer merging; at most two successful decision stages; a matching-but-failing fallback returns the fallback's error and still bills the primary |

The catalog quirk: `GET https://ai-gateway.vercel.sh/v1/models` labels all 15 decision entries
`"type": "evaluation"`, while the docs page, the UI filter, and the SDK all say decision. Filtering on
`type == "decision"` returns nothing; filter on `evaluation` or by model id. This is a Vercel-side fact
about Vercel's own API, and it is the kind of drift a generated artifact should not encode.

The SDK's own `GatewayDecisionModelId` union names 14 of those 15 entries, missing
`parallel/parallel-decisions-fast`. Because the union ends in `(string & {})`, that is an autocomplete
gap, not a runtime block.

## OpenRouter decisions and extractions

- source_url: https://openrouter.ai/docs/guides/community/jev,
  https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request, and
  https://openrouter.ai/docs/guides/community/extractions
- last_verified_at: 2026-11-08
- volatility: volatile
- summary: One aggregator in front of 15 or more vendors, in two alpha routes with the same envelope
  shape but different content: `questions` for decisions, `fields` for extraction.

| Aspect | Decisions | Extractions |
| --- | --- | --- |
| Path | `POST https://openrouter.ai/api/alpha/decisions`, plus `POST /api/v1/systemone` | `POST https://openrouter.ai/api/alpha/extractions` |
| Content | `noul`, `choice` with a `criteria` map, `score` with an array, `box` | `fields` typed as `text`, `number`, `date`, `time`, `datetime`, `duration`, `list`, `estimate`, `forecast` with `reference_date` and `null_threshold` defaulting to 0.5 |
| Answer fields | `noul` with optional `confidence`; `choice` with `probabilities` and `confidence`; `score` with `legend`, `probabilities`, `confidence`; `box` with `confidence`; usage carries `cost` | `value`, `guess`, `span`, `p_null`, `confidence`, `source`, `spell_confidence`, plus distribution keys for estimates |
| Input | `state` as string, object, or array; `image_url`, `input_audio`, `video_url` parts; an `assets` map resolved per adapter | text state only; images and PDFs go through `assets` |
| Status | alpha, "the shape may change" | alpha, four models at read time |
| Price | pass-through provider pricing plus an OpenRouter fee; `usage.cost` returned | pass-through |

Two hard rules from the vendor's own pages. Box is "Served by TypeSafe Jev endpoints only; every other
provider rejects a box question with `400`" before anything reaches the upstream provider. And a request
that an endpoint cannot serve fails with `400`, because which question types, media parts, and asset
references an endpoint accepts depends on the provider; the adapter table differs per vendor, with
image caps of 4, 8, 16, or 128 depending on the model.

Moving a request between the two routes is not a key rename: the vendor states it "means rewriting each
question as a field as well as renaming the key". Keep extraction and decision artifacts separate.

The catalog count of 36 entries under `output_modalities=decisions` is an aggregator figure that
includes aliases and free tiers, so it is not a vendor count. It is graded `B` and is never a fact to
put in a generated artifact.

One thing that is not a decision API: the Jev routing surface (`typesafe/jev-router`) picks a chat model
and reasoning effort and returns text. A design that treats it as a decision endpoint is wrong.

## T3: emulation on general models

A T3 route enforces a closed set but does not produce a label-level probability. This table exists so a
request that names one is answered honestly rather than routed into a generated threshold.

| Vendor | Closed-set enforcement | Probability source | Caveat |
| --- | --- | --- | --- |
| OpenAI general models | Structured Outputs `json_schema` with `strict: true`, constrained decoding | `logprobs` with `top_logprobs` 0 to 20, Chat Completions only for `logit_bias`; Responses via `include` | GPT-6 Astra has no log probabilities; GPT-5.4 and 5.2 only at `reasoning.effort: none`; GPT-5, mini, and nano error; enum ceiling 1,000 values; no label-level distribution |
| Anthropic | `output_config.format` JSON schema, or strict tool use; constrained decoding | none: `logprob` appears zero times in the Messages API reference | enum case is not guaranteed; forced `tool_choice` returns 400 on current flagship models, so a single-classifier-tool pattern must use `auto`; prefill is unsupported on 4.6 and later |
| Google | `response_format` JSON schema compiled into a state machine; `text/x.enum` on legacy `generateContent` only | legacy `generateContent` `response_logprobs` with 0 to 20 top candidates | `responseLogprobs` is deprecated for Gemini 3.x and slated for removal; the Interactions API has no logprob field; unsupported schema constraints are stripped silently |
| xAI | `response_format.json_schema` with `enum`, `const`, `anyOf` | none usable: `logprobs` is "Not supported by models `grok-4.20` and newer; the field will be silently ignored if set" | no decision endpoint; `guidelines` moderation has only `decline` and no score |
| Groq | `strict: true` constrained decoding on select models | none: both `logprobs` and `top_logprobs` are "not yet supported by any of our models" | `strict` is limited to select models, and the default is best-effort |
| Mistral | `response_format` `json_object` or `json_schema` with `strict: true` | `logprobs`, `top_logprobs`, `prompt_logprobs` in the OpenAPI | token level, not label level; the classifier product is deprecated |
| Together | `response_format` `json_schema` on supported models | `logprobs` with per-token `logprob` and `top_logprobs` | token level; tuning for classification is documented as a use case, not a contract |
| Fireworks | JSON schema and custom BNF grammar mode | `logprobs`, with `--max-logprobs` defaulting to 5 | `json_schema` disables reasoning output; `pattern` is best-effort |
| AWS Bedrock | `outputConfig.textFormat` or `response_format`, a JSON Schema Draft 2020-12 subset with a compiled grammar cached 24 hours | per-model log probabilities | Guardrails confidence is ordinal (`NONE`/`LOW`/`MEDIUM`/`HIGH`); LLM-as-judge is an offline evaluation job, not an endpoint |

The common failure across all nine: a caller can enforce the label set, and can sometimes read a
token-level number, but cannot get the probability of each label in one call. Doing it manually means
generating each label and comparing sequences, which is a different and much more expensive design.

## T4 appendix: fixed classifiers, guardrails, judges, retired surfaces

Not decision APIs. Listed so a request that names one gets an audit or a design note rather than
generated decision code.

| Surface | Output | Status | Why it is not a decision API |
| --- | --- | --- | --- |
| OpenAI moderation (`omni-moderation-latest`) | `category_scores` 0 to 1 over 13 fixed categories, plus `categories` and `flagged` | GA; free; images up to 20 MB; inline moderation added 2026-06-04 | the caller cannot define the label set |
| Mistral moderation (`/v1/moderations`, `/v1/chat/moderations`) | `category_scores` over 9 to 10 categories including `pii` and `jailbreaking`, plus boolean `categories` | Moderation 2 GA 2026-03-01; free | fixed taxonomy; the Mistral classifier product is deprecated |
| Mistral Shieldstral 1.0 | a yes/no classification over natural-language policy questions | public preview 2026-08-04 | policy prompts, no probabilities |
| Azure AI Content Safety | 0 to 7 severity, and per-category confidence | GA; several preview capabilities retire 2027-04-30 | fixed taxonomy, severity not probability |
| Azure OpenAI content filter | per-category `severity` in `safe`/`low`/`medium`/`high` plus `filtered`, in `prompt_filter_results` and `content_filter_results` | GA | it blocks rather than scores: a filtered prompt returns 400 |
| Bedrock Guardrails (`ApplyGuardrail`) | `action` of `GUARDRAIL_INTERVENED` or `NONE`, and per-filter confidence of `NONE`/`LOW`/`MEDIUM`/`HIGH`; contextual grounding returns a `score` | GA | ordinal grades cannot be thresholded as probabilities |
| Google `classifyText` / `moderateText` | `confidence` per category on Google's own taxonomy, plus severity on a subset | GA | fixed taxonomy, no caller questions |
| Hugging Face Inference Providers `zero-shot-classification` / `text-classification` | `[{label, score}]`, with `candidate_labels` and `multi_label` | GA | no multi-question batching, no ordered score primitive, no schema |
| Guard models: Llama Guard 4, Qwen3Guard, Granite Guardian | a text label such as `safe`/`unsafe`, `<score>yes</score>`, or a 3-tier severity | model cards current | text output that must be parsed; no closed-set API |
| Guard model: ShieldGemma | a real probability from `softmax` over Yes/No logits | docs marked deprecated, last updated 2026-01-15 | the only guard family in this set with a number; self-hosted only |
| Prometheus 2 | `[RESULT] (1-5)` from a four-part prompt | model card undated | rubric score, not a probability |
| Rerankers: Cohere Rerank 5, Voyage, Jina | `relevance_score` in 0 to 1 per document | current | an ordered decision over a document set for one query, not over caller questions; Cohere warns the number is not linear |
| Scorable | a 0 to 1 score plus a justification | current | judge score, not per-question probability |
| Contextual LMUnit | a score on a 5-point continuous scale, input capped at 7,000 tokens | current | judge score |
| Galileo (Splunk Agent Observability) | normalized log-probabilities of True/False over its own metrics; a Decision Scorer with `answer_options[]` and `num_judges` | current since the 2026-08-07 rebrand | observability product; scores are its metrics, not your questions |
| Retired: Patronus | nothing; "its evaluation API, SDKs, evaluators, Lynx, GLIDER and Percival are all retired" | retired | gone |
| Retired: Atla Selene | repository archived 2025-07-21, "The Atla API is no longer active" | retired | gone |
| Retired: Cohere classify | `POST /v1/classify` still in the v1 spec, filed under Deprecated; default-embed-model use deprecated 2025-01-31 | effectively end of life | an embedding nearest-neighbour classifier, never an LLM classifier |
| Retiring: OpenAI Evals and graders | a label or a 0 to 1 score | read-only 2026-10-31, shutdown 2026-11-30 | a shutdown notice, not a route |
| Retiring: Inception Mercury Decide | calibrated per-answer probability on a System One endpoint | banner "Going away November 8, 2026" | end of life on the snapshot date |

Guard models deserve one sentence of synthesis: of the five families checked, one returns a number and
four return text. That is precisely the failure mode decision APIs exist to remove.

## Sources

> Links checked 2026-11-08.

| Claim | Source |
| --- | --- |
| Perplexity's endpoint, Bearer-only auth, models and aliases, 1 to 255 options with `null` allowed, 1 to 10 levels, 100 questions in `web_grounding`, 256K input, 32 MiB body, 8 images per question, its confidence formula, and per-question state billing | <https://docs.perplexity.ai/docs/decisions/quickstart> and <https://docs.perplexity.ai/api-reference/decisions-post> |
| Perplexity's price for v1.2 and flash, and the 2026-10 launch | <https://docs.perplexity.ai/docs/resources/changelog> |
| Microsoft-Decision-1's path, auth, deployment-name rule, question types, text-only state, GA status, and the no-rationale statement | <https://learn.microsoft.com/en-us/azure/foundry/foundry-models/how-to/use-foundry-models-microsoft-decision> |
| Microsoft-Decision-1's regional availability, including the Middle East and Africa exclusion | <https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure-region-availability> |
| Two decision products on Foundry and no third | <https://learn.microsoft.com/api/search?search=Decisions%20API> and <https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure> |
| Liquid's endpoint, auth, hosted and open-weight model ids, limits, input-only billing, and 422 validation errors | <https://docs.liquid.ai/api/guides/decisions> and <https://docs.liquid.ai/lfm/models/decision-models> |
| Clef and Clef Flash sizes, contexts, prices, 1 to 64 questions, id rules, and output schema | <https://developers.cloudflare.com/ai/models/@cf/cloudflare/clef/> and <https://developers.cloudflare.com/ai/models/@cf/cloudflare/clef-flash/> |
| Clef Omni's audio and video caps and context | <https://developers.cloudflare.com/ai/models/@cf/cloudflare/clef-omni/> |
| Clairic's field types, `p_null`, distribution keys, limits, price, and preview status | <https://developers.cloudflare.com/ai/models/@cf/cloudflare/clairic/> |
| Parallel's question types, 1 to 100 questions, 32,000 tokens per question, no images, and its answer type table | <https://docs.parallel.ai/decisions/question-types> and <https://docs.parallel.ai/decisions/decisions-quickstart> |
| Parallel's `$1` per 1,000 requests and up to 100 questions per request | <https://docs.parallel.ai/getting-started/pricing> |
| Parallel's request-level `citations` with no per-answer mapping | <https://docs.parallel.ai/decisions/decisions-quickstart> |
| Baseten's System One hosting, model list, and 16,384 context | <https://docs.baseten.co/inference/model-apis/decision-models> |
| Baseten's Gateway availability date and price tiers | <https://vercel.com/changelog/basetens-mammoth-1-and-elephant-1-now-available-on-ai-gateway-for-free> |
| Upstage's Beta label, the `/v1/systemone` schema claim, and its document version date | <https://developers.upstage.ai/docs/models/solar-decide.md> |
| The AI SDK's decision entry point, provider contract, tolerance, refusal behaviour, and calibration disclaimer | <https://ai-sdk.dev/docs/ai-sdk-core/decisions> and <https://ai-sdk.dev/docs/reference/ai-sdk-core/decide> |
| Per-provider native versus emulated implementation, question type support, and the emulation adapter returning no distributions | <https://raw.githubusercontent.com/vercel/ai/main/packages/provider-utils/src/decision-language-model.ts>, <https://raw.githubusercontent.com/vercel/ai/main/packages/typesafe-ai/src/typesafe-ai-decision-model.ts>, <https://raw.githubusercontent.com/vercel/ai/main/packages/openai/src/openai-decision-model.ts>, <https://raw.githubusercontent.com/vercel/ai/main/packages/perplexity/src/perplexity-decision-model.ts>, <https://raw.githubusercontent.com/vercel/ai/main/packages/parallel/src/parallel-decision-model.ts>, <https://raw.githubusercontent.com/vercel/ai/main/packages/gateway/src/gateway-decision-model.ts> |
| The Gateway's per-package limits, including Perplexity's 1 to 128 questions and Parallel's name pattern | <https://raw.githubusercontent.com/vercel/ai/main/packages/perplexity/src/perplexity-decision-model.ts> and <https://raw.githubusercontent.com/vercel/ai/main/packages/parallel/src/parallel-decision-model.ts> |
| No decision factory exists in the other provider packages | the same package sources, grepped per package on 2026-11-08 |
| The Gateway's two decision surfaces, the rename from evaluation models, and the deprecated aliases | <https://vercel.com/docs/ai-gateway/modalities/decision> and <https://vercel.com/docs/ai-gateway/sdks-and-apis/typesafe> |
| The Gateway's OpenAI-compatible decision bounds | <https://vercel.com/docs/ai-gateway/sdks-and-apis/openai-decisions> |
| The full decision-fallback contract, sentinels, trigger reasons, headers, and double billing | <https://vercel.com/docs/ai-gateway/models-and-providers/decision-fallbacks> |
| The confidence-based fallback launch | <https://vercel.com/changelog/confidence-based-decision-fallbacks> |
| The 15 catalog entries all labelled `evaluation`, and the three Jev ids | <https://ai-gateway.vercel.sh/v1/models> |
| The Gateway decision model id union naming 14 of the 15 entries | <https://raw.githubusercontent.com/vercel/ai/main/packages/gateway/src/gateway-decision-model-settings.ts> |
| OpenRouter's decision path, its alpha status, the box restriction, and the adapter differences | <https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request> and <https://openrouter.ai/docs/guides/community/multimodal-decisions> |
| OpenRouter's extraction route, its field types, and the rewrite warning between the two routes | <https://openrouter.ai/docs/guides/community/extractions> |
| The 36-entry decision catalog, its aliases and free tiers, and the 15-vendor span | <https://openrouter.ai/api/v1/models?output_modalities=decisions> |
| Jev Router as a routing surface rather than a decision endpoint | <https://openrouter.ai/docs/guides/routing/routers/jev-router> |
| OpenAI's structured-output enum ceiling and `top_logprobs` cap | <https://developers.openai.com/api/docs/guides/structured-outputs.md> and <https://developers.openai.com/api/reference/resources/chat/index.md> |
| GPT-6 Astra's missing log probabilities, and GPT-5.4 and 5.2 needing `reasoning.effort: none` | <https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra.md> and <https://developers.openai.com/api/docs/guides/latest-model/gpt-5.4.md> |
| Anthropic's structured outputs, the forced `tool_choice` 400, the prefill removal, and the absence of log probabilities | <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>, <https://platform.claude.com/docs/en/build-with-claude/tool-use/implement-tool-use>, <https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency>, <https://platform.claude.com/docs/en/api/messages> |
| Gemini's structured output, `text/x.enum`, the 0 to 20 logprob cap, and the `responseLogprobs` deprecation for Gemini 3.x | <https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/control-generated-output> and <https://docs.cloud.google.com/gemini-enterprise-agent-platform/reference/models/inference> |
| xAI's schema support, its silently ignored `logprobs`, and its moderation limits | <https://docs.x.ai/developers/model-capabilities/text/structured-outputs.md>, <https://docs.x.ai/openapi.json>, <https://docs.x.ai/developers/advanced-api-usage/custom-moderation-controls.md> |
| Groq's unsupported `logprobs` and `top_logprobs`, and its limited `strict` support | <https://console.groq.com/docs/api-reference> and <https://console.groq.com/docs/structured-outputs> |
| Mistral's moderation scores, Shieldstral's preview status, and the deprecated classifier product | <https://docs.mistral.ai/studio/safety-moderation>, <https://docs.mistral.ai/models/shieldstral-1-0.md>, <https://docs.mistral.ai/resources/deprecated/finetuning/classifier_factory.md> |
| Together's `logprobs` and Fireworks' grammar mode and `--max-logprobs` default | <https://docs.together.ai/docs/inference/chat/logprobs> and <https://docs.fireworks.ai/structured-responses/structured-response-formatting> |
| Bedrock's structured-output subset, its grammar cache, and its ordinal Guardrails confidence | <https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-use-independent-api.md> and <https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_GuardrailContentFilter.html> |
| Bedrock's LLM-as-judge being an evaluation job | <https://docs.aws.amazon.com/bedrock/latest/userguide/evaluation-judge.md> |
| OpenAI moderation's categories, free tier, and recalibration warning | <https://developers.openai.com/api/docs/guides/moderation.md> |
| Azure Content Safety's 0 to 7 severity and the 2027-04-30 retirement of preview capabilities | <https://learn.microsoft.com/en-us/azure/ai-services/content-safety/overview> and <https://learn.microsoft.com/en-us/azure/ai-services/content-safety/concepts/harm-categories> |
| Azure OpenAI's content-filter severity bands and the 400 on a filtered prompt | <https://learn.microsoft.com/en-us/azure/foundry-classic/foundry-models/concepts/content-filter> |
| Google's `classifyText` confidence and `moderateText` severity | <https://cloud.google.com/natural-language/docs/reference/rest/v2/ClassificationCategory> and <https://cloud.google.com/natural-language/docs/reference/rest/v2/documents/moderateText> |
| Hugging Face's zero-shot and text classification response shape | <https://raw.githubusercontent.com/huggingface/hub-docs/main/docs/inference-providers/tasks/zero-shot-classification.md> |
| Llama Guard 4's text output, Qwen3Guard's severity, Granite Guardian's `<score>`, ShieldGemma's softmax probability, and Prometheus's 1 to 5 scale | <https://llama.com/docs/model-cards-and-prompt-formats/llama-guard-4/>, <https://huggingface.co/Qwen/Qwen3Guard-Gen-8B/raw/main/README.md>, <https://huggingface.co/ibm-granite/granite-guardian-3.3-8b/raw/main/README.md>, <https://huggingface.co/google/shieldgemma-9b>, <https://huggingface.co/prometheus-eval/prometheus-7b-v2.0/raw/main/README.md> |
| Cohere Rerank's calibrated score and its non-linearity warning | <https://docs.cohere.com/docs/rerank.md> and <https://docs.cohere.com/reference/rerank.md> |
| Voyage and Jina rerank output shapes | <https://docs.voyageai.com/reference/reranker-api.md> and <https://docs.jina.ai/llms.txt> |
| Scorable's 0 to 1 score and justification, and LMUnit's 5-point scale | <https://docs.scorable.ai/llms-full.txt> and <https://docs.contextual.ai/api-reference/lmunit/lmunit.md> |
| Galileo's log-probability classification, its Decision Scorer, and the Splunk rebrand | <https://docs.galileo.ai/concepts/luna/luna>, <https://docs.galileo.ai/api-reference/data/create-decision-scorer-version>, <https://docs.galileo.ai/> |
| Patronus's retirement notice | <https://docs.patronus.ai/docs/lynx/overview> |
| Atla's archived repository and inactive API | <https://github.com/atla-ai/atla-sdk-python> |
| Cohere classify's deprecated status and default-embed deprecation date | <https://docs.cohere.com/changelog/classify-default-model-deprecation.md> |
| OpenAI Evals' read-only date and shutdown date | <https://developers.openai.com/api/docs/deprecations> |
| Inception Mercury Decide's retirement banner | <https://openrouter.ai/inception/mercury-decide> |

### Evidence grade

`PRIMARY` for every vendor section except Upstage, which is graded `B` and marked in place: its
first-party page states status and schema compatibility but publishes no request field, answer field,
or limit, and its numbers disagree across sources.

`SECONDARY`, marked where used, for three sets: the OpenRouter catalog count of 36 entries and its
vendor span, which are an aggregator's own figures; the Baseten image cap, which comes from an
aggregator rather than the vendor; and the Gateway catalog's `evaluation` type label, which is a Vercel
fact about Vercel's API rather than a decision-API contract.

Not evidenced by these pages, and deliberately left unspecified: any calibration measurement for any
vendor, any latency figure, Microsoft-Decision-1's option and level counts, and whether the
TypeSafe-compatible base URL accepts the payloads of the vendors that have no AI SDK provider package.
