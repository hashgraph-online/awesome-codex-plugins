---
name: token-compare
description: Compare two to five crypto tokens side by side on safety, buy and sell flow, smart money and liquidity. Use when the user asks to compare coins, which of several tokens looks safer or stronger, "X vs Y", or wants a table across a few tickers or addresses.
argument-hint: <2 to 5 token addresses or tickers>
---

# Compare tokens side by side

Put two to five tokens in one table so the differences are obvious. Use the StalkChain connector. Batch calls cover all tokens at once, so use them before per-token calls.

## 1. Pin down each token

Tickers need an address: `stalkchain_fomo_search` with `q` and `type: "tokens"` (250 each). If a ticker is ambiguous, ask. More than five tokens: ask which five.

## 2. Batch calls first

1. Prices and liquidity: `stalkchain_token_prices` with `tokens` set to the Solana mints (250 for up to 50). For EVM tokens use `stalkchain_token_prices_multichain` with `tokens` as `{chain, address}` pairs (250).
2. Smart money: `stalkchain_fomo_top_traders_for_tokens` with `tokens` set to the addresses and `window: "7d"` (250 per token plus 250). It shows which top tracked traders hold which of the tokens.

## 3. Per token, cheapest first

**Solana:** `stalkchain_token_quality` with `token` (250) for organic volume, then `stalkchain_token_onchain` with `token` (250) for holders, LP burn, authorities, concentration and risk score.

**Flow, any chain:** `stalkchain_fomo_token_stats` with `address` (250): buys versus sells, unique buyers and net volume over 5m, 1h, 4h and 24h.

**EVM safety:** `stalkchain_fomo_analyze_token` with `address` and `chain` (750) instead of the Solana tools. In Claude and ChatGPT it shows a card per token, so keep the table as the summary.

Optional, if the user gives a trade size: `stalkchain_token_exit_check` with `token` and `usd` (500 each, Solana only).

## 4. Answer in this shape

**Table:** one column per token, one row per measure: price, market cap, liquidity, 24h change, total holders, top-10 share, LP burned, mint or freeze authority, organic volume share, 24h buy/sell ratio, net flow, tracked traders holding, risk score, main red flag.

**Where they differ most:** three to five sentences on the biggest gaps, e.g. "A has twice the liquidity of B but half its holders are snipers."

Then one line: *"This is data, not financial advice."*

## Rules

- Compare the data; don't pick a token to buy. "Fewest red flags in this data" is fine, "the best buy" is not.
- A missing value is `null`, never zero. Show it as "n/a" in the table, never 0.
- "Tracked traders" are a curated set, not every holder. Keep raw JSON out of the answer.
