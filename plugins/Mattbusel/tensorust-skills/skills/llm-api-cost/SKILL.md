---
name: llm-api-cost
description: Current, dated, source-cited LLM API prices per 1M tokens (Anthropic Claude, OpenAI GPT, Google Gemini, DeepSeek, Mistral, xAI Grok, Groq, Together AI, Fireworks, Cohere) and exact cost of a request from token counts, including prompt cache reads and writes, batch discounts and long-context tiers. Use to estimate or compare model costs, price token usage logs, set a budget, or fix a stale hard-coded price table in code. Python, Rust and JavaScript packages, plus raw JSON.
---

# LLM API cost

Uses `llm-prices`, a table re-read from each provider's official pricing page every day. Every row carries the pricing page URL and the date it was checked, so you can cite it.

## When to use

- The user asks what a model costs, which model is cheapest for a workload, or what a run, a log file or a month of traffic will cost.
- Code has a hand-kept price dict or constants (for example `"gpt-4o": {"input": 5, "output": 15}`) and the user wants it correct or kept current.
- The user wants a cost or budget check in CI.

Do not quote prices from memory. Model prices change often; read them from the table.

## How to get prices

Pick whichever fits the environment.

**Python** (`pip install llm-prices`, no dependencies, no network at runtime):

```python
import llm_prices
from llm_prices import Usage

p = llm_prices.lookup("claude-sonnet-4-6")          # model id, dated ids and aliases resolve
print(p.input, p.output, p.cache_read, p.source_url, p.checked)
print(p.cost(10_000, 2_000))                          # USD for 10k input + 2k output tokens
usage = Usage(input=2_048, cache_read=45_000, cache_write_5m=3_500, output=1_024)
print(p.cost_usage(usage, exact=True).total)          # exact Decimal, cache included
llm_prices.lookup_provider("groq", "openai/gpt-oss-120b")  # same model id on a specific host
```

**Rust** (`cargo add llm-prices`): `llm_prices::lookup("gpt-4o")`, `llm_prices::all()`.

**JavaScript / TypeScript**: `npm i github:Mattbusel/llm-prices#v1`, then `import { lookup } from "llm-prices"`. No install: `https://cdn.jsdelivr.net/gh/Mattbusel/llm-prices@v1/index.mjs`.

**Raw JSON** (any language, or just to read): `https://raw.githubusercontent.com/Mattbusel/llm-prices/main/prices.json`. Units are USD per 1M tokens; each provider block lists `source` and each row its `checked` date.

**CI**: the GitHub Action `uses: Mattbusel/llm-prices@v1` scans a repo for hard-coded prices that drifted from the table.

## Steps

1. Identify the model ids and, if it matters, the provider hosting them (OpenAI-compatible hosts such as Groq or Together price the same open model differently).
2. Look up each price. If `lookup` returns `None`, try `lookup_provider` with the host, or list `all_prices()` filtered by provider.
3. Compute cost from token counts with `cost` or `cost_usage` (use `exact=True` for billing).
4. Report the price per 1M tokens, the computed cost, and the source URL with its checked date.
5. When fixing a stale table in code, replace the constants with a lookup, or update them and cite the source URL in a comment.
