# Decision API Route Reference

A decision API takes one shared input and a set of typed questions, and returns typed answers with
probabilities instead of generated text. Several vendors now answer that contract, in two wire
dialects plus one SDK, and the dialects disagree on field names, on the container shapes, and on
where a confidence value lives. Picking the wrong row is the fastest way to a rejected request or
to a threshold that reads a number the route never produced.

This file holds the route tiers, the dialect map, the order to pick a route in, and the routes that
carry no first-party contract and must not be coded against. Price, limits, model ids, and endpoint
details live in the three snapshots under `official/`, not here.

## Contents

- Refresh Policy
- Route tiers
- Dialect map
- Route choice order
- Unverified routes
- Sources
- Evidence grade

## Refresh Policy

- last_verified_at: 2026-11-08
- refresh_when:
  - a route changes its endpoint, authentication header, dialect, or accepted model ids
  - a question type name or answer field changes on any route
  - a route moves between tiers, for example a preview becomes generally available or a route is retired
  - a route on the unverified list publishes a first-party request contract
  - a new vendor ships a decision API

Re-read the vendor pages read-only when this file is more than 30 days old and the network is
available. When it is not, state the snapshot date instead of guessing at current values.

## Route tiers

Tier decides what a generated artifact may assume. A tier is a property of the route, not of the
vendor, and one vendor can appear in more than one tier.

- **T1** is a native decision endpoint that answers typed questions over shared input.
- **T2** is an SDK or gateway in front of T1 or T3 routes. It adds no calibration of its own.
- **T3** is emulation on a general language model: structured output with an enum, plus token log
  probabilities only where that vendor still returns them.
- **T4** is a fixed-taxonomy classifier, guardrail, or judge. It is an appendix, not a decision API.

`Status` means `verified` when a first-party page captured in this snapshot documents the request
and answer contract, and `unverified` when it does not. A verified row is safe to generate code
from. An unverified row is a name to look up.

`Checker route` names the `--route` value of `scripts/check-decision-request.sh` that validates a
request body for that row, or `none` when the checker does not model the route.

### T1: native decision APIs

| Route | Endpoint | Auth header | Env var | Dialect | Question types | Probability source | Confidence path | Status (date) | Checker route | Verified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TypeSafe direct | `POST https://api.typesafe.ai/v1/systemone` | `Authorization: Bearer <key>` | `TYPESAFE_API_KEY` | System One | `noul`, `choice`, `score`, `box` (Jev 1.14 only) | `choice.probabilities`, `score.probabilities`; `noul.noul` is P(true) | `answers.<id>.confidence` on choice and score; box `confidence` may be `null`; none on noul | GA; `jev-1.14.0` released 2026-10-14 | `systemone` | verified |
| OpenAI Decisions | `POST /v1/decisions` on the OpenAI API (SDK: `client.decisions.create`) | `Authorization: Bearer <key>` | `OPENAI_API_KEY` | OpenAI Decisions | `predicate`, `choice`, `score` | `predicate.probability`; `choice.probabilities[]`; `score.probabilities[]` plus a probability-weighted `score` | `answers[].confidence` on choice and score; none on predicate | GA 2026-10-22; model `gpt-6-luna` only | `openai` | verified |
| Azure OpenAI Decisions | `POST /openai/v1/decisions` on the Azure resource (SDK: `decisions.create`) | `api-key: <key>` or Microsoft Entra ID | `AZURE_OPENAI_API_KEY` is not named by the vendor page; pass the key explicitly | OpenAI Decisions | same as OpenAI | same as OpenAI | same as OpenAI | rolling out per region, East US 2 excluded; page dated 2026-11-06 | `openai` | verified |
| Perplexity Decisions | `POST https://api.perplexity.ai/v1/decisions` | `Authorization: Bearer <key>` (`x-api-key` returns 401) | `PERPLEXITY_API_KEY` is a project convention; the vendor page names no variable | System One | `noul`, `choice`, `score` | `choice.probabilities`, `score.probabilities`; `noul.noul` is P(yes) | `answers.<id>.confidence` on choice and score; formula published | GA; Decisions changelog entry under October 2026 | `systemone` | verified |
| Microsoft-Decision-1 | `<foundry-endpoint>/providers/microsoft/v1/systemone` | Entra ID bearer or `api-key` | not named by the vendor page | System One | `noul`, `choice`, `score` | `answers.<id>.probabilities` | `answers.<id>.confidence` | GA in Foundry; how-to dated 2026-10-07 | `systemone` | verified |
| Liquid AI d1 | `POST https://api.liquid.ai/decisions/v1/systemone` | `Authorization: Bearer liquid_<key>` | not named by the vendor page | System One | `noul`, `choice`, `score` on hosted; open weights add `box`/`boxes` and multi-select choice | `choice`/`score` `probabilities` | `confidence` | GA (hosted); open weights under the LFM Open License | `systemone` | verified |
| Cloudflare Clef | `POST https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/ai/run/@cf/cloudflare/clef` (or `env.AI.run`) | `Authorization: Bearer $CLOUDFLARE_API_TOKEN` | `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` | System One | `noul`, `choice`, `score` | `probabilities` per question | `confidence` on choice and score | GA per model card; zero data retention | `systemone` | verified |
| Parallel Decisions | `POST https://api.parallel.ai/v1/decisions` | `x-api-key: <key>` | not named by the vendor page | System One, with `mode` instead of `model` | `noul`, `choice` (2 to 255), `score` (2 to 10 levels) | `probabilities` on choice and score; no `confidence` field in its answer type table | none documented; request-level `citations[]` instead | GA | `systemone` | verified |
| Baseten decision models | `POST https://inference.baseten.co/v1/systemone` | `Authorization: Bearer <key>` | not named by the vendor page | System One | `noul`, `choice`, `score` | `probabilities` plus confidence | `confidence` | available; page modified 2026-10-29 | `systemone` | verified |
| Upstage Solar Decide | System One endpoint; the vendor console docs did not render and no request spec URL resolved | Upstage key, or via OpenRouter | not documented | System One | `noul`, `choice`, `score` | "calibrated probability taken directly from the model" | not separately published | Beta, page version dated 2026-09-22 | `none` | unverified (see below) |
| DigitalOcean (Jev reseller) | `POST https://inference.do-ai.run/v1/systemone` | `Authorization: Bearer $MODEL_ACCESS_KEY` | `MODEL_ACCESS_KEY` (the vendor example's name) | System One | `noul`, `choice`, `score`; no box | `probabilities` from Jev | `confidence` | GA reseller; page last verified 2026-09-28; `typesafe-jev-1.13.0` only | `systemone` | verified for the 1.13 contract |
| b.ai (Jev reseller) | `POST https://api.b.ai/v1/decisions` | `Authorization: Bearer <key>` or `x-api-key: <key>` | `BAI_API_KEY` is a project convention; the vendor page names no variable | System One | `noul`, `choice`, `score`; no box | `probabilities` | `confidence` | `jev-1.13.0` or `jev-latest` only; 1.14 not listed in its sitemap | `bai` | verified |

One row needs a caveat about what the checker validates: Cloudflare's Workers AI body carries `model`
and `input`, with `state` and `questions` nested inside `input`, so the `systemone` checker route
validates the inner payload rather than the transport envelope.

### T2: SDKs and gateways

| Route | Endpoint or SDK entry | Auth header | Env var | Dialect | Question types | Probability source | Confidence path | Status (date) | Checker route | Verified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Vercel AI SDK | `experimental_decide({ model, state, questions })`; `Experimental_DecisionModelV4` with `doDecide` | per provider package | `TYPESAFE_AI_API_KEY` for the TypeSafe provider, `OPENAI_API_KEY` for the OpenAI provider | AI SDK | `boolean`, `choice`, `score`, `box`; per-model support varies | native providers pass `probabilities` through; the Anthropic and Google adapters return none | `providerMetadata.<provider>.confidence[questionId]`, plus `.legend` on TypeSafe | experimental; `ai@7.0.164` on 2026-11-06 | `aisdk` | verified |
| Vercel AI Gateway, OpenAI-compatible decisions | `POST https://ai-gateway.vercel.sh/v1/decisions`; `gateway.decisionModel('<vendor>/<model>')` | `Authorization: Bearer $AI_GATEWAY_API_KEY`, or Vercel OIDC | `AI_GATEWAY_API_KEY` | OpenAI Decisions | `predicate`, `choice` (1 to 255), `score` (2 to 10 levels) | routed model's own probabilities | `providerMetadata.gateway...`; language-model fallbacks return no confidence | GA route; decision fallbacks documented 2026-10-08 | `openai` | verified |
| Vercel AI Gateway, TypeSafe-compatible decisions | `POST https://ai-gateway.vercel.sh/typesafe/v1/systemone`; `GET /typesafe/v1/models` | `Authorization: Bearer $AI_GATEWAY_API_KEY` | `AI_GATEWAY_API_KEY` | System One | `noul`, `choice`, `score`, `box` on TypeSafe endpoints | routed model's own | `confidence`; `0` plus `probabilities: {}` as an unavailable sentinel when a language model answers | GA route; same fallback contract | `systemone` | verified |
| OpenRouter decisions (alpha) | `POST https://openrouter.ai/api/alpha/decisions` | `Authorization: Bearer $OPENROUTER_API_KEY` | `OPENROUTER_API_KEY` | System One envelope with `assets` | `noul`, `choice`, `score`; `box` only on TypeSafe endpoints, every other provider rejects it with `400` | routed model's own | `confidence` where the routed model supplies it | alpha, "the shape may change" | `systemone` | verified as alpha |
| OpenRouter System One | `POST https://openrouter.ai/api/v1/systemone` | `Authorization: Bearer $OPENROUTER_API_KEY` | `OPENROUTER_API_KEY` | System One | `noul`, `choice`, `score`, `box` on TypeSafe endpoints | routed model's own | `confidence` | live; the TypeSafe SDK works by changing `base_url` and using `~typesafe/jev-latest` | `systemone` | verified |
| OpenRouter extractions (alpha) | `POST https://openrouter.ai/api/alpha/extractions` | `Authorization: Bearer $OPENROUTER_API_KEY` | `OPENROUTER_API_KEY` | extraction `fields` | none; typed fields (`text`, `number`, `date`, `time`, `datetime`, `duration`, `list`, `estimate`, `forecast`) | per-field `confidence`, `p_null` | per-field | alpha | `none` | verified as alpha |

### T3: emulation on a general language model

| Route | Entry | Dialect | Question types it can be forced into | Probability source | Caveat | Checker route | Verified |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenAI general models | Responses or Chat Completions with `json_schema` strict, plus logprobs where the model allows them | Structured output plus token logprobs | `boolean`, `choice`, `score` as a JSON schema enum or ordered number | token logprobs only where documented; `top_logprobs` caps at 20 | no label-level probability; GPT-6 Astra returns no logprobs at all | `none` | verified |
| Anthropic | Messages API with `output_config.format` JSON schema, or strict tool use | structured output | `boolean`, `choice`, `score` | none: no logprobs in the Messages API | forced `tool_choice` returns 400 on current flagship models | `none` | verified |
| Google | `response_format` JSON schema, or legacy `generateContent` logprobs | structured output | `boolean`, `choice`, `score` | legacy `generateContent` logprobs, deprecated for Gemini 3.x | none on the Interactions API | `none` | verified |
| xAI | `response_format.json_schema` | structured output | `boolean`, `choice`, `score` | none usable: `logprobs` "will be silently ignored" on `grok-4.20` and newer | no decision endpoint | `none` | verified |
| Groq | `strict: true` constrained decoding on select models | structured output | `boolean`, `choice`, `score` | none: both `logprobs` and `top_logprobs` are unsupported on every model | best-effort schema by default | `none` | verified |
| Mistral | `response_format` JSON schema | structured output | `boolean`, `choice`, `score` | `logprobs`, `top_logprobs`, `prompt_logprobs` | token level, not label level | `none` | verified |
| Together | `response_format` `json_schema` | structured output | `boolean`, `choice`, `score` | `logprobs` with `top_logprobs` | token level | `none` | verified |
| Fireworks | JSON schema or BNF grammar mode | structured output | `boolean`, `choice`, `score` | `logprobs`; `--max-logprobs` default 5 | `json_schema` disables reasoning output | `none` | verified |
| Bedrock | `outputConfig.textFormat` or `response_format` JSON Schema subset | structured output | `boolean`, `choice`, `score` | per-model log probabilities | Guardrails confidence is ordinal, not numeric | `none` | verified |

A T3 route is never the answer when the caller needs a probability to threshold. It returns no
distribution, and a prompted self-estimate is not a calibrated probability.

### T4: fixed-taxonomy classifiers, guardrails, and judges

Not decision APIs. They are listed so a request that names one is recognized and routed to an audit
or a design note instead of to generated decision code. The appendix table in
`official/decision-providers.md` carries the details.

| Route | What it returns | Why it is not a decision route |
| --- | --- | --- |
| OpenAI, Mistral moderation | `category_scores` 0 to 1 over a fixed category list | the caller cannot define the label set |
| Azure Content Safety, Bedrock Guardrails | severity bands, or `NONE`/`LOW`/`MEDIUM`/`HIGH` | ordinal grades cannot be thresholded as probabilities |
| Google `classifyText`, `moderateText` | confidence over a fixed taxonomy | fixed taxonomy, no caller questions |
| Scorable, Contextual LMUnit, Galileo | a 0 to 1 score or a 5-point scale plus a justification | judge scores, not per-question probabilities |
| Retired: Patronus, Atla Selene, Cohere classify, OpenAI Evals and graders, Inception Mercury Decide | nothing durable | retired or retiring; see the appendix for dates |

## Dialect map

Three wire shapes cover every verified row. The neutral names on the left are what a generated
artifact should think in; the columns are what goes on the wire.

| Concept | System One dialect | OpenAI Decisions dialect | AI SDK |
| --- | --- | --- | --- |
| Shared input key | `state` (string, object, or array) | `input` (string, or an array of input items including messages and tool calls) | `state` (string, JSON object, or an array of content parts) |
| Question container | `questions` is a map of id to question | `questions` is an array, each entry carrying a unique `name` | `questions` is a map of id to question |
| Yes/no type | `noul` | `predicate` | `boolean` |
| Yes/no answer | `noul`: a number 0 to 1, no confidence | `probability`: a number 0 to 1 | `probability`, required |
| Choice options | `criteria`: a map of option to description, 1 to 255 entries | `choices`: an array of `{ value, description }`, 2 to 255 entries | `criteria` map, or the provider's native shape |
| Choice answer | `choice`, `probabilities`, `confidence` | `choice`, `probabilities[]`, `confidence` | `choice`, `probabilities` where native |
| Score levels | `criteria`: an ordered array of level descriptions, 1 to 10 in the schema, 2 or more in the prose | `levels`: an array of `{ label, description }`, 2 to 10 | `criteria` ordered array |
| Score answer | `score` (a probability-weighted mean), `legend`, `probabilities`, `confidence` | `score`, `probabilities[]`, `confidence` | `score`, `legend` where native |
| Box | `box` with `top`, `bottom`, `left`, `right` as 0 to 1 fractions, plus `confidence`; Jev 1.14 only | not supported | `box` in the spec; only the TypeSafe provider implements it |
| Refusal | not a separate answer type | a fourth answer type per question | the SDK throws `Experimental_DecisionRefusalError` |
| Confidence location | `answers.<id>.confidence` | `answers[].confidence` | `providerMetadata.<provider>.confidence[questionId]` |
| Distributions | always present on choice and score | always present on choice and score | optional; absent by construction on the Anthropic and Google adapters |

Rules that follow from the map and bite in practice:

- A refusal is not a negative answer. Do not turn it into `probability: 0`, the first choice, or a
  zero score.
- `noul`, `predicate`, and `boolean` all carry one P(true) scalar. None of these vendors calls that
  number confidence.
- `confidence` is vendor-specific and not portable. Only TypeSafe, Perplexity, and the AI SDK's
  provider metadata carry it at all, and each computes it its own way.
- `box` is TypeSafe Jev 1.14 only on hosted routes. Liquid's open weights add `box`, but the hosted
  d1 route documents `noul`/`choice`/`score` only.
- A JSON array sent as `state` is read as a list of content parts by the AI SDK, so wrap records in
  an object or a typed part.

## Route choice order

Start from what the repository already contains. Pick the first rule that matches, and say which
route was chosen and why when the artifact is handed over.

1. **An existing dependency decides.** If the project already depends on `ai` and a route in this
   file already supplies a decision provider package for it, use the AI SDK route. The dependency
   decides because the package is installed and the project's other model calls already go through
   it.
2. **An OpenAI dependency and existing OpenAI usage decides.** If the project already depends on the
   `openai` package and calls OpenAI today, use OpenAI Decisions. Repointing a client that already
   holds `OPENAI_API_KEY` costs one new method call.
3. **A TypeSafe dependency decides.** If the project depends on `@typesafe-ai/sdk`, `typesafe-sdk`,
   or has `api.typesafe.ai` in its code or config, use the TypeSafe direct route.
4. **Otherwise choose by the stated constraint.** With nothing in the repository to decide, ask what
   the caller needs and recommend one route: TypeSafe direct when the task wants distributions,
   box output, or the widest question-type set, and OpenAI Decisions when the project is already
   OpenAI-shaped or an Azure deployment is the deployment path. Say why in one sentence.
5. **Never silently fall to T3.** When the caller needs a probability to act on, a T3 route is not
   an option. Say that it returns no distribution and offer a T1 route or a review path instead.

An environment variable name being set is weaker evidence than a project file. A key name proves
something about the machine, not about this repository. When the project's own files, such as a lock
file, config, existing client code, or an env example, name a different route, that route wins, and
when the two disagree, say which route was chosen and why.

Neither a key nor a high confidence value authorizes a live call. Ask before the first real request,
state the cost, and keep the call count to the minimum that answers the question.

## Unverified routes

These routes market, resell, or front a decision model, and this snapshot holds no first-party
request contract for them that is complete enough to write code against. They are recorded so a
request naming one is recognized, not so code can be generated for it.

- **Netlify AI Gateway.** The page documents that the TypeSafe SDK reads `TYPESAFE_API_KEY` and
  `TYPESAFE_BASE_URL` and lists four Jev model ids, but it documents injection, not a request
  contract of its own. Treat it as a deployment convenience over the TypeSafe SDK, and verify the
  injected base URL before use.
- **AI/ML API.** One vendor model page advertises `POST https://api.aimlapi.com/v1/decisions` with
  `typesafe/jev-1.14`, and a generated schema page disagrees with the TypeSafe schema on the score
  floor. The lanes do not agree on one contract, so no code.
- **Upstage Solar Decide request spec.** The model is real and its page is first-party, but it
  states only that it uses the same `/v1/systemone` schema, is in Beta, and carries no field list,
  no limit table, and no answer schema. The currency of its two published prices also differs
  between lanes.
- **Convai Innovations Laya.** The gateway model card describes typed answers with probabilities,
  but the first-party docs were not found and the provider link on the card 404s.
- **Any other route with no first-party request contract.** A model card, a changelog entry, or a
  gateway listing is not a contract.

Instruction for every entry above: do not generate code. Read the vendor's own documentation first,
confirm the endpoint, the authentication header, the accepted model ids, the question type names,
and the answer fields, then add a verified row here before any code is produced for it.

The same rule applies to a route that is not in the tier tables at all: no verified row, no code.

## Sources

> Links checked 2026-11-08.

| Claim | Source |
| --- | --- |
| The TypeSafe direct endpoint, the Bearer header, the four question types, and the choice, score, and box answer fields | <https://docs.typesafe.ai/api/system-one.md> and <https://api.typesafe.ai/openapi.json> |
| `jev-1.14.0` from 2026-10-14, `jev-1.13.0` still callable, both aliases on 1.14, and the Box requirement | <https://docs.typesafe.ai/models.md> and <https://docs.typesafe.ai/changelog.md> |
| `TYPESAFE_API_KEY`, `TYPESAFE_BASE_URL`, `TYPESAFE_DEFAULT_MODEL`, and `TYPESAFE_LOG_LEVEL` read by the TypeSafe SDKs | <https://docs.typesafe.ai/sdk/javascript/api/variables/ENV.md> and <https://docs.typesafe.ai/sdk/python/api/constants.md> |
| The OpenAI Decisions endpoint, `gpt-6-luna`, `predicate`/`choice`/`score`, the 1 to 400 question range, 2 to 255 choices, and 2 to 10 levels | <https://developers.openai.com/api/docs/guides/decisions.md> and <https://developers.openai.com/api/reference/resources/decisions/methods/create.md> |
| OpenAI Decisions GA on 2026-10-22 after a 2026-10-06 beta | <https://developers.openai.com/api/docs/changelog.md> |
| The Azure endpoint, `api-key` or Entra ID, and the East US 2 exclusion | <https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/decisions> |
| The Perplexity endpoint, Bearer-only auth, `noul`/`choice`/`score`, its published confidence formula, 1 to 255 options, 1 to 10 levels, and 8 images per question | <https://docs.perplexity.ai/api-reference/decisions-post> and <https://docs.perplexity.ai/docs/decisions/quickstart> |
| The Perplexity Decisions launch under October 2026 | <https://docs.perplexity.ai/docs/resources/changelog> |
| Microsoft-Decision-1 on `<foundry-endpoint>/providers/microsoft/v1/systemone` with the deployment name as `model`, text or JSON state only | <https://learn.microsoft.com/en-us/azure/foundry/foundry-models/how-to/use-foundry-models-microsoft-decision> |
| Liquid's `POST /decisions/v1/systemone`, its TypeSafe System One implementation, input-only billing, and the 4.5 MB body limit | <https://docs.liquid.ai/api/guides/decisions> |
| Liquid's hosted models and open-weight box and multi-select additions | <https://docs.liquid.ai/lfm/models/decision-models> |
| Clef and Clef Flash model sizes, context, prices, and the 1 to 64 question bound | <https://developers.cloudflare.com/ai/models/@cf/cloudflare/clef/> and <https://developers.cloudflare.com/ai/models/@cf/cloudflare/clef-flash/> |
| Clef Omni's audio and video caps | <https://developers.cloudflare.com/ai/models/@cf/cloudflare/clef-omni/> |
| Clairic as an extraction model with `fields`, `p_null`, and estimate and forecast distributions | <https://developers.cloudflare.com/ai/models/@cf/cloudflare/clairic/> |
| Parallel's endpoint, `x-api-key`, 1 to 100 questions, 2 to 255 options, 2 to 10 levels, its answer type table, and `$1` per 1,000 requests | <https://docs.parallel.ai/decisions/question-types> and <https://docs.parallel.ai/getting-started/pricing> |
| Parallel rejecting images with 400 | <https://openrouter.ai/docs/guides/community/multimodal-decisions> |
| Baseten hosting decision models through the System One API, and its model and context list | <https://docs.baseten.co/inference/model-apis/decision-models> |
| The Upstage Beta label, the `/v1/systemone` schema claim, and its version date | <https://developers.upstage.ai/docs/models/solar-decide.md> |
| The DigitalOcean endpoint, `MODEL_ACCESS_KEY`, and the single `typesafe-jev-1.13.0` id | <https://docs.digitalocean.com/products/inference/how-to/use-system-one-api/> |
| The b.ai endpoint, both auth headers, the two accepted ids, and the absence of a box type | <https://docs.b.ai/llmservice/api/decisions-api/> |
| `experimental_decide`, `Experimental_DecisionModelV4`, and the per-provider support table | <https://ai-sdk.dev/docs/ai-sdk-core/decisions> and <https://ai-sdk.dev/docs/reference/ai-sdk-core/decide> |
| `TYPESAFE_AI_API_KEY` and `TYPESAFE_AI_BASE_URL` read by the AI SDK TypeSafe provider | <https://ai-sdk.dev/providers/ai-sdk-providers/typesafe-ai> |
| The Anthropic and Google adapters omitting choice and score distributions | <https://ai-sdk.dev/docs/ai-sdk-core/decisions> |
| The Gateway `/v1/decisions` route, its `predicate`/`choice`/`score` types, and its 1 to 255 and 2 to 10 bounds | <https://vercel.com/docs/ai-gateway/sdks-and-apis/openai-decisions> |
| The Gateway `/typesafe/v1/systemone` and `/typesafe/v1/models` paths | <https://vercel.com/docs/ai-gateway/sdks-and-apis/typesafe> |
| Decision fallbacks, the `confidence: 0` and `probabilities: {}` sentinel, and double billing | <https://vercel.com/docs/ai-gateway/models-and-providers/decision-fallbacks> |
| The Gateway catalog still labelling decision models `"type": "evaluation"` | <https://ai-gateway.vercel.sh/v1/models> |
| OpenRouter's two decision surfaces, the alpha warning, and box being served only by TypeSafe endpoints | <https://openrouter.ai/docs/guides/community/jev> and <https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request> |
| OpenRouter's per-provider adapter differences, including the 400 on unsupported media | <https://openrouter.ai/docs/guides/community/multimodal-decisions> |
| OpenRouter extractions as a separate `fields` route | <https://openrouter.ai/docs/guides/community/extractions> |
| The TypeSafe SDK's OpenRouter base URL and `~typesafe/jev-latest` slug | <https://docs.typesafe.ai/sdk/python/usage/basic.md> |
| Netlify injecting `TYPESAFE_API_KEY` and `TYPESAFE_BASE_URL` | <https://docs.netlify.com/build/ai-gateway/overview/> |
| AI/ML API's advertised endpoint and model id | <https://aimlapi.com/models/typesafe-jev-1-14> |
| Laya's gateway card and missing first-party docs | <https://vercel.com/ai-gateway/models/laya> |
| OpenAI structured output enum limits and `top_logprobs` maximum 20 | <https://developers.openai.com/api/docs/guides/structured-outputs.md> and <https://developers.openai.com/api/reference/resources/chat/index.md> |
| GPT-6 Astra returning no logprobs, GPT-5.4 and 5.2 only at `reasoning.effort: none` | <https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra.md> and <https://developers.openai.com/api/docs/guides/latest-model/gpt-5.4.md> |
| Anthropic structured outputs, the forced `tool_choice` 400, and the absence of logprobs | <https://platform.claude.com/docs/en/build-with-claude/structured-outputs> and <https://platform.claude.com/docs/en/api/messages> |
| Gemini's enum surface, the deprecated `responseLogprobs` for Gemini 3.x, and the 0 to 20 logprob cap | <https://docs.cloud.google.com/gemini-enterprise-agent-platform/reference/models/inference> and <https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/control-generated-output> |
| xAI silently ignoring `logprobs` on `grok-4.20` and newer | <https://docs.x.ai/openapi.json> |
| Groq supporting neither `logprobs` nor `top_logprobs` | <https://console.groq.com/docs/api-reference> |
| Mistral moderation scores and the deprecated classifier factory | <https://docs.mistral.ai/studio/safety-moderation> |
| Together's `logprobs` and Fireworks' grammar mode and `--max-logprobs` default | <https://docs.together.ai/docs/inference/chat/logprobs> and <https://docs.fireworks.ai/structured-responses/structured-response-formatting> |
| Bedrock's structured-output subset and ordinal Guardrails confidence | <https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_GuardrailContentFilter.html> |
| The retired and retiring judge products | <https://docs.patronus.ai/docs/lynx/overview> and <https://developers.openai.com/api/docs/deprecations> |

### Evidence grade

`PRIMARY` for every verified row: each contract detail comes from the vendor page named in the
table above and was captured on 2026-11-08. `SECONDARY` for the unverified list, which is a routing
warning rather than a contract; the entries rest on vendor pages that document a listing, an
injection mechanism, or a partial spec, not on a full request and answer contract.

`B` marks facts that come from a third-party aggregator rather than the vendor itself: the two
Gateway catalog facts (the `"evaluation"` type label and the 15 entries) and the OpenRouter
adapter table's image rules. They are labelled where used, and no generated artifact may rest on
them alone.

Not evidenced here and deliberately left unspecified: any vendor's real-world latency, any
calibration claim, and the current model ids on the unverified routes.
