# OpenAI Decisions Snapshot

What OpenAI's own pages say about the Decisions API: the endpoint, the request and answer shape, the
limits, the price, the Azure variant, the Gateway path, and what OpenAI's general models do and do not
give a caller who wants a probability. Everything here was read from the pages listed under Sources
and captured on 2026-11-08.

This file is one of the places in this package where volatile vendor facts belong. The cross-vendor
route comparison is in the sibling route reference; the TypeSafe facts are in their own file.

## Contents

- Refresh Policy
- Endpoint and authentication
- Request shape
- Questions
- Answers and refusal
- Limits
- Pricing
- Status and dates
- Azure OpenAI Decisions
- Vercel AI Gateway, OpenAI-compatible decisions
- What general OpenAI models do and do not give
- Moderation as a fixed classifier
- Evals, graders, and fine-tuning
- Sources
- Evidence grade

## Refresh Policy

- last_verified_at: 2026-11-08
- refresh_when:
  - the endpoint, the accepted model, or the authentication header changes
  - the question types, the answer fields, or the refusal behaviour changes
  - a limit, a price, or the cached-input rate changes
  - the Azure rollout gains or loses a region
  - a general model gains or loses log probabilities
  - the eval and fine-tuning retirement dates pass

Re-read the vendor pages read-only when this file is more than 30 days old and the network is
available. When it is not, state the snapshot date instead of guessing.

## Endpoint and authentication

- source_url: https://developers.openai.com/api/docs/guides/decisions.md
- last_verified_at: 2026-11-08
- applies_to: the endpoint, the model, and the SDK entry point
- volatility: volatile
- summary: One endpoint answers typed questions about one input. `gpt-6-luna` is the only supported
  model.

| Item | Value |
| --- | --- |
| Path | `POST /v1/decisions` on the OpenAI API |
| Python SDK | `client.decisions.create(...)` |
| Authentication | `Authorization: Bearer <OPENAI_API_KEY>`, the standard OpenAI API key |
| Model | `gpt-6-luna`, documented as the only currently supported model |
| Vendor's own framing | the guide states the API "evaluates text, images, and JSON and returns typed answers about 10x faster than the Responses API" |

The 10x figure is unbenchmarked: no dataset, latency percentile, or methodology is published with it.
Treat it as a vendor claim, not as a design input.

## Request shape

- source_url: https://developers.openai.com/api/reference/resources/decisions/methods/create.md
- last_verified_at: 2026-11-08
- applies_to: the `input` field, its shapes, and the `input_json` part
- volatility: stable
- summary: `input` plays the role that `state` plays on the TypeSafe dialect, and it accepts more
  shapes than a plain string.

| Shape | Notes |
| --- | --- |
| String | plain text input, up to 10,485,760 characters |
| Input items | an array of items including messages and tool calls, so a conversation or an agent transcript can be the input |
| `input_json` | a JSON part with its own caps: 256 KiB, 10,000 values, and 32 container levels |
| Images | accepted, including images given by URL; the Azure page caps a request at 128 images and 32 MB combined |

Two consequences for generated code. First, a decision request is not limited to one string; an agent
transcript or a structured record can be the shared input, which is what makes the endpoint usable as
a gate inside a tool-using loop. Second, the `input_json` caps are smaller than a typical JSON
payload, so a large record has to be trimmed or split before it goes in.

## Questions

- source_url: https://developers.openai.com/api/reference/resources/decisions/methods/create.md
- last_verified_at: 2026-11-08
- applies_to: the `questions` array and the three question types
- volatility: stable
- summary: `questions` is an array, not a map, and every entry carries a unique `name` that keys the
  answer. One request takes 1 to 400 questions.

| Type | Request fields | Answer fields |
| --- | --- | --- |
| `predicate` | `instructions` | `probability`, a number from 0 to 1 |
| `choice` | `instructions`, `choices`: an array of `{ value, description }`, between 2 and 255 entries, each `value` unique | `choice`, `probabilities[]`, `confidence` |
| `score` | `instructions`, `levels`: an array of `{ label, description }`, `minItems: 2`, `maxItems: 10` | `score` (the probability-weighted mean of level indices, so it can fall between levels), `probabilities[]`, `confidence` |

Choice `value` may be a string or a boolean, per the reference. The `name` per question is required
for a usable answer: the response keys on it, and an unnamed question returns `name: null`.

Independent questions belong in one array; the vendor's own guidance is that a dependent sequence
("check damage first, then pick a repair category") goes into separate requests, because questions in
one request cannot read each other's answers.

The score floor is 2 here, unlike TypeSafe's schema, which accepts 1. A request generator that targets
both dialects must keep 2 or more levels.

## Answers and refusal

- source_url: https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/decisions
- last_verified_at: 2026-11-08
- applies_to: the answer union, including refusal
- volatility: stable
- summary: Every question returns one answer object whose type is `predicate`, `choice`, `score`, or
  `refusal`. The Azure page states the distinction that matters: "A refusal is different from a
  `predicate` answer with a low probability".

A refusal is a fourth answer type, not a low-probability answer and not a failed request. Generated
code must branch on it: turning a refusal into `probability: 0`, the first choice, or a zero score
silently converts "the model declined" into "the model said no", which is a different decision. Route a
refusal to the same place as a low-confidence answer, or to a human.

Each answer echoes its `name`, so a caller can key answers by question name the way the TypeSafe
dialect keys by question id.

## Limits

- source_url: https://developers.openai.com/api/reference/resources/decisions/methods/create.md
- last_verified_at: 2026-11-08
- applies_to: per-request counts and per-field sizes
- volatility: volatile
- summary: The bounds are generous in question count and tight in JSON payload size.

| Item | Limit |
| --- | --- |
| Questions per request | 1 to 400 |
| Choices per `choice` question | 2 to 255, each value unique |
| Levels per `score` question | 2 to 10 |
| Entries in one `probabilities` array | at most 2,000 |
| String input | at most 10,485,760 characters |
| `input_json` | at most 256 KiB, 10,000 values, 32 container levels |
| Images per request | 128, with a combined 32 MB, per the Azure page that documents the same contract |

A 2,000-entry ceiling on `probabilities` means a choice question with 255 options and a few hundred
questions can approach it. Cap the option count or split the request.

## Pricing

- source_url: https://developers.openai.com/api/docs/guides/decisions.md
- last_verified_at: 2026-11-08
- applies_to: input pricing and the output line item
- volatility: volatile
- summary: The API is billed on input tokens and output is not charged.

| Item | Value |
| --- | --- |
| Uncached input | `$0.10` per 1 million tokens |
| Output | not charged on `/v1/decisions` |
| Cached input | the guide's wording implies a cached rate exists; this snapshot quotes no cached rate |

Output tokens for this endpoint are zero by construction: there is nothing to generate. The model
page's per-token rate applies to the same model on the general endpoints, not to `/v1/decisions`.

No regional price premium is quoted anywhere in the captured pages, so none is stated here. Azure
pricing is on Azure's own pricing page, which this snapshot does not assert.

## Status and dates

- source_url: https://developers.openai.com/api/docs/changelog.md
- last_verified_at: 2026-11-08
- applies_to: release timeline
- volatility: stable
- summary: The API went beta and then generally available inside one month.

| Date | Event |
| --- | --- |
| 2026-10-06 | Decisions API released in beta with `gpt-6-luna` |
| 2026-10-22 | Decisions API generally available with `gpt-6-luna` |

The beta allowed 200 questions per request and the GA allows 400, per the changelog's own framing of
the change. The dates are changelog-asserted; no second, independent date stamp was found.

## Azure OpenAI Decisions

- source_url: https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/decisions
- last_verified_at: 2026-11-08
- applies_to: the Azure variant of the same endpoint
- volatility: volatile
- summary: Azure serves the same request and answer contract at a dedicated path on the customer's
  own resource, with two operational differences that break code copied from the OpenAI path.

| Item | Value |
| --- | --- |
| Path | `/openai/v1/decisions` on `{resource}.openai.azure.com` |
| Model | `gpt-6-luna` deployment only; the `model` field takes the deployment name, not the model id |
| Authentication | `api-key` header, or Microsoft Entra ID |
| Questions per request | up to 400 |
| Images per request | up to 128, 32 MB combined |
| Rollout | rolling out to regions where `gpt-6-luna` is available; "East US 2 is excluded from the rollout" |
| SDK floors | openai-python 3.26.0 or newer, openai-node 7.30.0 or newer, OpenAI .NET 2.15.0 or newer |
| Page date | `ms.date` 2026-11-06 |

The deployment-name rule is the most common cause of a 404 on this path: the model id works on the
OpenAI path and fails on Azure. Do not advertise universal availability either; a region excluded from
the rollout returns an error that looks like a deployment problem.

## Vercel AI Gateway, OpenAI-compatible decisions

- source_url: https://vercel.com/docs/ai-gateway/sdks-and-apis/openai-decisions
- last_verified_at: 2026-11-08
- applies_to: the Gateway's OpenAI-shaped decision route
- volatility: volatile
- summary: The Gateway exposes `/v1/decisions` in the OpenAI shape, so an existing OpenAI client
  switches by changing the base URL, the credentials, and the model id.

| Item | Value |
| --- | --- |
| Path | `POST https://ai-gateway.vercel.sh/v1/decisions` |
| Authentication | `Authorization: Bearer $AI_GATEWAY_API_KEY`, or Vercel OIDC |
| Question types | `predicate`, `choice`, `score` |
| Choices per question | 1 to 255 |
| Levels per question | 2 to 10 |
| AI SDK floor | `ai` 7.0.128 or later for the SDK route |

The Gateway's decision fallback mechanism is a transport concern layered on top: it reruns a
successful but uncertain answer with a second model. Two things follow. A triggered fallback bills
both stages. And when the fallback is a language model rather than a native decision model, the
OpenAI-shaped surface omits `confidence` and `probabilities` rather than inventing them, so generated
code must treat both as optional. The detail lives in the sibling provider snapshot.

## What general OpenAI models do and do not give

- source_url: https://developers.openai.com/api/docs/guides/structured-outputs.md and
  https://developers.openai.com/api/reference/resources/chat/index.md
- last_verified_at: 2026-11-08
- applies_to: the emulation path on general models, and why it rarely produces a usable probability
- volatility: volatile
- summary: Structured Outputs gives a closed set with no confidence. Log probabilities give a
  token-level number on some models and are unavailable on the ones people actually pick.

| Capability | What it gives | Limit that binds |
| --- | --- | --- |
| Structured Outputs, `json_schema` with `strict: true` | the typed object only, with the enum enforced by constrained decoding | at most 1,000 enum values across all enum properties; a single string enum above 250 values is capped at 15,000 characters; at most 5,000 properties and 10 nesting levels; `additionalProperties: false` is mandatory; the root must be an object; `allOf`, `not`, `if`/`then`/`else`, and the dependent keywords are unsupported |
| `logprobs` with `top_logprobs`, Chat Completions | token-level log probabilities plus up to `top_logprobs` alternatives per position | `top_logprobs` is 0 to 20, and the number of returned entries may be fewer than requested |
| `logprobs` in the Responses API | the same token-level shape, via `include: ["message.output_text.logprobs"]` | same 0 to 20 cap; the Responses API has no `logit_bias` at all |
| `logit_bias`, Chat Completions only | a bias from -100 to 100 per token id | token-id level, not label level, so it is useless as a label API unless labels are single tokens |

Model gating is the part that ruins the emulation plan:

| Model | Log probabilities |
| --- | --- |
| GPT-6 Astra | not supported at all; the changelog states it "does not support custom `temperature` or `top_p` values or log probabilities (`logprobs`)" |
| GPT-5.4 and GPT-5.2 | supported only when `reasoning.effort` is `none`; any other effort raises an error |
| GPT-5, GPT-5-mini, GPT-5-nano | error at any reasoning effort |

An unsupported keyword with `strict: true` produces an error rather than a best-effort output, so a
schema that uses an unsupported construct fails loudly. That is the one good property of the
emulation path: it fails instead of quietly returning a label with no confidence.

What it never gives, on any model: a label-level probability distribution over a closed set. That is
exactly what the Decisions API adds, and it is why a caller who needs to threshold a probability
should not be sent down the structured-output path.

## Moderation as a fixed classifier

- source_url: https://developers.openai.com/api/docs/guides/moderation.md
- last_verified_at: 2026-11-08
- applies_to: the moderation endpoint, which is a classifier but not a decision API
- volatility: stable
- summary: Moderation returns 0 to 1 scores per category, covers text and images, and is free. The
  label set is fixed to the vendor's own categories, which is why it is an appendix, not a route.

| Item | Value |
| --- | --- |
| Model | `omni-moderation-latest`, equivalent to `omni-moderation-2024-09-26` |
| Endpoint | `POST /v1/moderations`, SDK `client.moderations.create` |
| Input | a string, an array of strings, or a multimodal array; images up to 20 MB; audio is not classified |
| Output | `category_scores` from 0 to 1 per category, boolean `categories`, and `flagged` |
| Categories | 13, including `harassment`, `hate`, `illicit`, `illicit/violent`, and `self-harm/intent` |
| Cost | free |
| Free-tier rate | 250 requests per minute, 5,000 per day, 10,000 tokens per minute |
| Inline moderation | added 2026-06-04: a `moderation` object in a generation request returns scores for both the input and the generated output |

The docs warn that policies relying on `category_scores` "may need recalibration over time", which is
the honest form of the general caveat: a category score is a model output that drifts with model
upgrades, not a fixed policy verdict.

## Evals, graders, and fine-tuning

- source_url: https://developers.openai.com/api/docs/deprecations.md
- last_verified_at: 2026-11-08
- applies_to: the judge and grader surfaces, which are being retired
- volatility: volatile
- summary: The eval platform and its graders are on a published shutdown path, and self-serve
  fine-tuning stops accepting new jobs. Neither is a durable recommendation.

| Surface | State |
| --- | --- |
| Evals platform | read-only for existing users since 2026-10-31; scheduled to shut down 2026-11-30 |
| Graders, including `label_model` and `score_model` | deprecated together with evals and fine-tuning; `POST /v1/fine_tuning/alpha/graders/run` still resolves but the guide marks the whole surface deprecated |
| Self-serve fine-tuning | no new jobs from 2027-01-06; new organizations already could not create jobs from 2026-05-07; GPT-4.1 and 4o fine-tuning base models shut down 2027-01-14 |
| Reinforcement fine-tuning | does not exist in the current documentation; the guide path redirects into the Graders reference |

`label_model` graders do enforce a closed set ("the labels to assign to each item") and a model that
supports structured outputs, so they read like a decision API in a code sample. They are a shutdown
notice, not a recommendation: do not build a new decision path on them.

## Sources

> Links checked 2026-11-08.

| Claim | Source |
| --- | --- |
| The Decisions guide: the endpoint, `gpt-6-luna` as the only supported model, the "10x faster" claim, the input and output billing split, and the 1 to 400 question range | <https://developers.openai.com/api/docs/guides/decisions.md> |
| The create reference: 1 to 400 questions, 2 to 255 choices, `minItems: 2` and `maxItems: 10` levels, the answer fields, `input_json` and string input caps, and the 2,000-entry `probabilities` ceiling | <https://developers.openai.com/api/reference/resources/decisions/methods/create.md> |
| The beta on 2026-10-06 and GA on 2026-10-22, and the 200 to 400 question change | <https://developers.openai.com/api/docs/changelog.md> |
| Azure's `/openai/v1/decisions`, the deployment-name rule, 400 questions, 128 images and 32 MB, `api-key` or Entra ID, the East US 2 exclusion, and the SDK floors | <https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/decisions> |
| The refusal distinction | <https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/decisions> |
| Structured Outputs' 1,000 enum ceiling, the 250-value and 15,000-character rule, the 5,000-property and 10-level caps, `additionalProperties: false`, and the error on unsupported keywords | <https://developers.openai.com/api/docs/guides/structured-outputs.md> |
| `top_logprobs` 0 to 20, the fewer-entries note, and `logit_bias` from -100 to 100 | <https://developers.openai.com/api/reference/resources/chat/index.md> |
| GPT-6 Astra dropping `temperature`, `top_p`, and `logprobs`, and the `include` removal for Responses | <https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra.md> |
| GPT-5.4 and GPT-5.2 supporting `temperature`, `top_p`, and `logprobs` only at `reasoning.effort: none`, and GPT-5, mini, and nano erroring | <https://developers.openai.com/api/docs/guides/latest-model/gpt-5.4.md> |
| The 2026-09-03 changelog line on GPT-6 Astra and log probabilities | <https://developers.openai.com/api/docs/changelog.md> |
| Moderation: `omni-moderation-latest`, text and image input, no audio, free, 20 MB images, the recalibration warning, the 13 categories, and the free-tier rate limits | <https://developers.openai.com/api/docs/guides/moderation.md> and <https://developers.openai.com/api/reference/resources/moderations/index.md> |
| The inline moderation object added 2026-06-04 | <https://developers.openai.com/api/docs/changelog.md> |
| Evals read-only from 2026-10-31 and shutdown on 2026-11-30, and the fine-tuning end date | <https://developers.openai.com/api/docs/deprecations.md> |
| Graders returning a label or a 0 to 1 score, `label_model` requiring structured outputs, and the deprecation of graders | <https://developers.openai.com/api/docs/guides/graders.md> and <https://developers.openai.com/api/reference/resources/graders/index.md> |
| The Gateway's OpenAI-compatible decisions route, its 1 to 255 and 2 to 10 bounds, and the base-URL switch | <https://vercel.com/docs/ai-gateway/sdks-and-apis/openai-decisions> and <https://vercel.com/changelog/openai-decisions-api-now-available-on-ai-gateway> |
| `gpt-6-luna`'s supported endpoints and its `reasoning.effort` values | <https://developers.openai.com/api/docs/models/gpt-6-luna.md> |

### Evidence grade

`PRIMARY` for everything in this file: each fact comes from an OpenAI or Microsoft page for the
product being described, captured on 2026-11-08, except the Gateway row, which comes from Vercel's own
page about its own route.

`SECONDARY` for two items, marked where used: the "10x faster" figure is an unbenchmarked vendor claim,
and the presence of a cached-input rate is inferred from the word "uncached" in the pricing sentence
rather than quoted as a number.

Not evidenced by these pages, and deliberately left unspecified: any regional price premium on the
OpenAI path, any calibration promise for the returned probabilities, the cached-input rate, and any
latency measurement.
