# Pricing LLM calls in credits

Read this when the metered work is a call to a language model that bills by tokens. It covers the price table, how each provider's reported usage maps onto it, the arithmetic from tokens to credits, and the upper bound that the reservation holds. The lifecycle around the call is in [ai-calls-and-streams.md](ai-calls-and-streams.md), and runnable code in [ai-worked-example.md](ai-worked-example.md).

## What a call costs

A provider bills one call as a sum of token counts, each at its own price, plus per-call charges for some provider-side tools. The kinds that providers bill at different prices today:

| Kind | What it is | Notes |
| --- | --- | --- |
| `input` | Prompt tokens read at the normal input price | Includes the whole conversation history sent with the call |
| `cached_input` | Prompt tokens read from the provider's prompt cache | Cheaper than `input` on the providers below |
| `cache_write` | Prompt tokens written to the cache | Billed above `input` by some providers, and at a second price for a longer cache lifetime (`cache_write_long`) |
| `output` | Generated tokens | Reasoning or thinking tokens are billed as output tokens by all three providers below, also when the reasoning text is not returned |
| `call:<tool>` | One use of a provider-side tool, such as web search | A price per call, on top of the tokens the tool adds |

Prices also change with the request: the service tier or batch mode, the data region, and, on some models, the length of the prompt (a request above a threshold pays a higher price for all its tokens). Key the price rows by everything the project actually varies.

## The price table

Prices are integers in micro-units: millionths of a dollar (micro-USD) per 1,000,000 tokens, and micro-USD per call for tool charges. A price of 2.50 per million tokens is stored as 2500000. No floats and no decimals.

```sql
-- One row per published price list. Rows are never updated: a price change is a new version.
CREATE TABLE price_versions (
  id              BIGINT PRIMARY KEY,
  effective_from  TIMESTAMPTZ NOT NULL UNIQUE,
  markup_bps      INTEGER NOT NULL CHECK (markup_bps > 0),  -- 15000 = the user pays 1.5 times the provider cost
  source          TEXT NOT NULL                            -- the price pages read and the date they were read
);

CREATE TABLE model_prices (
  version_id  BIGINT NOT NULL REFERENCES price_versions (id),
  model       TEXT NOT NULL,                 -- '<provider>:<model id>' exactly as sent, plus tier if it changes the price
  band_from   BIGINT NOT NULL DEFAULT 0,     -- prompt tokens from which this price applies; 0 for one band
  kind        TEXT NOT NULL,                 -- input, cached_input, cache_write, cache_write_long, output, call:<tool>
  micros      BIGINT NOT NULL CHECK (micros >= 0),
  PRIMARY KEY (version_id, model, band_from, kind)
);

-- The reservation remembers which price list it was priced with.
ALTER TABLE credit_reservations ADD COLUMN price_version BIGINT REFERENCES price_versions (id);
```

- **Load prices from the provider's price page, never from memory or from this file.** Write them with a script into a new version, with the URLs and the date in `source`. Every version holds every model the app offers, so a lookup never mixes versions.
- **A price change is a new version with a future `effective_from`.** Providers announce changes in advance; enter them when announced. The version in force is the one with the latest `effective_from` that is not in the future, read with the database clock.
- **A reservation stores its `price_version`,** and the commit prices the call with that version. A price change in the middle of a long call changes nothing for that call.
- **Every model has a price for every kind its adapter can report.** A test reads the table and fails when a kind is missing. A missing price at commit time is a bug, not a zero.
- **`markup_bps` and the value of a credit are the owner's decisions.** The value of one credit (`MICROS_PER_CREDIT` below) is fixed for the life of the product, because sold credits must keep their value. Change the markup or the packs instead.
- **Batch mode, tiers and regions** each get their own `model` key (for example `anthropic:<model>:batch`) when the project uses them, so the bound and the commit read the same row set.

## From each provider's usage to the kinds

The adapter for each provider turns its usage object into counts per kind. The fields differ in what they include, and adding them the wrong way charges cached tokens twice.

**OpenAI, Responses API.** `usage.input_tokens` includes the cached and the cache-written tokens. The prompt caching guide computes ordinary input as `input_tokens - cached_tokens - cache_write_tokens`. `usage.output_tokens` includes `output_tokens_details.reasoning_tokens`, which are billed as output.

| Kind | From |
| --- | --- |
| `input` | `input_tokens - input_tokens_details.cached_tokens - input_tokens_details.cache_write_tokens` |
| `cached_input` | `input_tokens_details.cached_tokens` |
| `cache_write` | `input_tokens_details.cache_write_tokens_details.ttl_30m_tokens`, or `cache_write_tokens` when the details are absent |
| `cache_write_long` | `input_tokens_details.cache_write_tokens_details.ttl_12h_tokens` |
| `output` | `output_tokens` |

**OpenAI, Chat Completions.** `usage.prompt_tokens`, `prompt_tokens_details.cached_tokens` and `prompt_tokens_details.cache_write_tokens`, and `completion_tokens`, which counts reasoning tokens (`completion_tokens_details.reasoning_tokens`) for billing. The caching guide documents the subtraction for the Responses API only: compare one cached Chat Completions call with the provider's usage dashboard before you rely on the same arithmetic there.

**Anthropic, Messages API.** `usage.input_tokens` counts only the tokens after the last cache breakpoint. The documented total is `cache_read_input_tokens + cache_creation_input_tokens + input_tokens`. `output_tokens` includes thinking, which is billed as output at its full length even when only a summary or nothing is returned. `output_tokens_details.thinking_tokens` reports the thinking part.

| Kind | From |
| --- | --- |
| `input` | `input_tokens` |
| `cached_input` | `cache_read_input_tokens` |
| `cache_write` | `cache_creation.ephemeral_5m_input_tokens`, or `cache_creation_input_tokens` when the breakdown is absent |
| `cache_write_long` | `cache_creation.ephemeral_1h_input_tokens` |
| `output` | `output_tokens` |
| `call:web_search` | `server_tool_use.web_search_requests` |

On a model priced by prompt length, the length is all input tokens, cache reads and writes included.

**Google Gemini, `generateContent`.** `usageMetadata.promptTokenCount` includes the cached content (`cachedContentTokenCount`). `totalTokenCount` is prompt plus `toolUsePromptTokenCount` plus `thoughtsTokenCount` plus `candidatesTokenCount`. The price page lists the output price as including thinking tokens, and states that every token the model processes is billed, including internal tool instructions when grounding is used.

| Kind | From |
| --- | --- |
| `input` | `promptTokenCount - cachedContentTokenCount`, plus `toolUsePromptTokenCount` |
| `cached_input` | `cachedContentTokenCount` |
| `output` | `candidatesTokenCount + thoughtsTokenCount` |

The price page lists no separate price for `toolUsePromptTokenCount`; the mapping above prices it as input. Check it against the provider's billing report before relying on it. Explicit context caches are also billed for storage per token per hour. That is the cost of running the cache, not of one request: carry it in the markup, not in a per-call charge.

**Google Gemini, Interactions API.** `usage.total_input_tokens`, `total_cached_tokens`, `total_output_tokens`, `total_thought_tokens` and `total_tool_use_tokens`. Pricing for thinking is the sum of output and thought tokens, so `output` is `total_output_tokens + total_thought_tokens`. The pages read do not say whether `total_input_tokens` includes `total_cached_tokens`: check one cached call against the billing report before writing the `input` line.

## From kinds to credits

Multiply each count by its price, add the per-call charges, apply the markup, and round up once at the end. Rounding each kind separately adds up to several credits per call.

```js
const PER_MTOK = 1_000_000n;
const BPS = 10_000n;
export const MICROS_PER_CREDIT = 1_000n; // one credit is worth 0.001 at the sale price. Fixed for good.

// rates: { markupBps, perMTok: { input: 2500000n, ... }, perCall: { web_search: 10000n } }
// usage: { tokens: { input: 1200, output: 300 }, calls: { web_search: 1 } }
export function costOf(rates, usage) {
  let scaled = 0n; // micro-USD times 1,000,000
  for (const [kind, count] of Object.entries(usage.tokens)) {
    if (!count) continue;
    if (!Number.isSafeInteger(count) || count < 0) throw new TypeError(`bad token count for ${kind}`);
    const price = rates.perMTok[kind];
    if (price === undefined) throw new Error(`no price for ${kind}`);
    scaled += BigInt(count) * price;
  }
  for (const [tool, count] of Object.entries(usage.calls ?? {})) {
    if (!count) continue;
    const price = rates.perCall[tool];
    if (price === undefined) throw new Error(`no price for call:${tool}`);
    scaled += BigInt(count) * price * PER_MTOK;
  }
  const divisor = PER_MTOK * BPS * MICROS_PER_CREDIT;
  return {
    credits: Number((scaled * BigInt(rates.markupBps) + divisor - 1n) / divisor),
    providerMicros: Number((scaled + PER_MTOK - 1n) / PER_MTOK),
  };
}
```

- BigInt keeps the product exact: ten million tokens at a price of a thousand dollars per million tokens already passes 2^53 in plain numbers. Python integers have no such limit.
- `credits` is what the user is charged. `providerMicros` is what the provider will bill, stored next to it for the margin report and the comparison with the provider's invoice.
- A call that used nothing costs zero credits. A call that used anything costs at least one.

## The upper bound

The reservation is the price of the most the call can cost. Compute it from the same limits that are passed to the call.

- **Output.** The maximum output tokens sent with the request. All three providers count reasoning or thinking inside that limit: OpenAI's `max_output_tokens` (Responses) and `max_completion_tokens` (Chat Completions), Anthropic's `max_tokens`, and Gemini's output limit, which its thinking guide says applies to thinking and output combined. Never send a request without the limit: without it the bound is the model's own maximum.
- **Prompt.** Count it before the call and add a margin. OpenAI has `POST /v1/responses/input_tokens`, Anthropic `POST /v1/messages/count_tokens` (documented as an estimate that can differ slightly), Gemini `countTokens`. A count from a local tokenizer works too, with a larger margin. Price every prompt token at the larger of the `input` and cache-write prices, because whether the cache is hit is known only afterwards.
- **Prompt-length bands.** Take the band from the counted prompt plus the margin. When the prompt is near a threshold, the higher band is the bound.
- **Provider-side tools.** A tool billed per call needs a cap on calls in the bound. Pass the provider's limit where one exists (OpenAI's Responses API has `max_tool_calls` for built-in tools). Without a cap, do not enable a billed tool on metered requests.
- **What the bound is not.** It is not the price the user pays. The commit charges the reported usage, at most the bound, and releases the rest.

```js
// counted: the prompt tokens from the count endpoint or a local tokenizer. The margin covers
// an estimate that is a little low and the framing of the messages. Use the result for the
// price band and for the bound.
export const promptBound = (counted) => counted + Math.ceil(counted / 20) + 64;

export function boundUsage(rates, { promptTokens, maxOutputTokens, maxToolCalls = {} }) {
  // Every prompt token at the larger of the input and cache-write prices.
  const promptKind = ['cache_write_long', 'cache_write', 'input']
    .filter((kind) => rates.perMTok[kind] !== undefined)
    .reduce((a, b) => (rates.perMTok[a] >= rates.perMTok[b] ? a : b));
  return { tokens: { [promptKind]: promptTokens, output: maxOutputTokens }, calls: maxToolCalls };
}
```

The reservation amount is `costOf(rates, boundUsage(rates, { promptTokens: promptBound(counted), maxOutputTokens })).credits`. If the account cannot cover it, answer 402 with that amount, or lower `maxOutputTokens` to what the available credits cover and say so to the user. Never call the model unreserved.

## Rules

- Prices come from the provider's price page, through a script that writes a new version. Nobody edits a price row.
- The reservation stores the price version, and the commit uses it.
- Usage is mapped per provider and per API with the subtraction that provider documents. Cached and cache-written tokens are never priced twice.
- Reasoning and thinking tokens are priced as output.
- One rounding, up, after the markup.
- The bound is computed from the limits sent with the request, and the commit never charges more than the bound.
- Credits charged and the provider cost are both stored for every call.

## Not a bug

- The reserved amount is several times what the call ends up costing. The bound covers the worst case. The difference comes back at commit.
- Two identical prompts cost different amounts. Cache hits differ from call to call.
- A call that returned no visible text costs credits. Reasoning tokens are billed as output, and an answer cut by the output limit can consist of reasoning only.
- The sum of `providerMicros` for a day differs from the provider's invoice by a few cents. Each call is rounded up, and the provider rounds its own way. Investigate a difference that grows with volume.

## Sources

- https://developers.openai.com/api/reference/resources/responses/methods/create (usage, `max_output_tokens`, `max_tool_calls`)
- https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create (usage, `max_completion_tokens`)
- https://developers.openai.com/api/docs/guides/prompt-caching
- https://developers.openai.com/api/docs/guides/reasoning
- https://developers.openai.com/api/reference/resources/responses/subresources/input_tokens/methods/count
- https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- https://platform.claude.com/docs/en/build-with-claude/thinking
- https://platform.claude.com/docs/en/build-with-claude/extended-thinking
- https://platform.claude.com/docs/en/build-with-claude/token-counting
- https://platform.claude.com/docs/en/about-claude/pricing (long context pricing, web search)
- https://ai.google.dev/api/generate-content (`usageMetadata`)
- https://ai.google.dev/gemini-api/docs/thinking
- https://ai.google.dev/gemini-api/docs/tokens
- https://ai.google.dev/gemini-api/docs/pricing
- https://ai.google.dev/gemini-api/docs/caching

Checked 2026-11-15.
