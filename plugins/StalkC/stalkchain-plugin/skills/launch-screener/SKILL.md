---
name: launch-screener
description: Screen new crypto token launches for red flags. Use when the user asks for new launches, fresh coins, new pairs, recently graduated tokens, or "anything new worth a look today", and wants a shortlist checked for rugs, snipers and dodgy deployers.
argument-hint: "[chain or max market cap]"
---

# Screen today's new launches

Turn the board of new tokens into a short, checked list. Use the StalkChain connector. Most new launches fail the screen, so filter with cheap calls before spending on deep ones.

## 1. Get the candidates

1. `stalkchain_fomo_token_board` with `board: "graduated"` (250 credits): early-stage tokens that just left the launch curve, usually under $1M. Use `board: "trending"` if the user wants what's moving rather than what's new.
2. `stalkchain_fomo_multi_trader_entries` with `windowMinutes: 240`, `minTraders: 2` (125): which of these, if any, several tracked traders have bought.
3. Filter locally to the chain and market cap the user asked for, and keep about eight candidates. Prefer ones with tracked-trader buys.

For a one-call scan on any chain, `stalkchain_fomo_trending_analysis` with `board`, `topN` (3–5), `chain` and `maxMarketCapUsd` reads the board and analyses the top tokens (about 250 plus 750 per token). Use it when the user wants depth on a few rather than a wide screen.

## 2. Cheap filter (Solana)

For each candidate, `stalkchain_token_quality` with `token` (250). Drop tokens with mostly wash volume or live mint or freeze authority, and say how many you dropped and why.

## 3. Deep check on the survivors

For the best three to five (ask before going past five):

1. `stalkchain_token_onchain` with `token` (250): LP burn, top-10 concentration, sniper and insider share, risk score.
2. `stalkchain_token_deployer` with `token` (500): what else the deployer launched and how it ended.
3. `stalkchain_token_early_buyers` with `token` (500): whether the first buyers already sold, and bundler share still held.

**EVM candidates:** the on-chain tools are Solana-only. Use `stalkchain_fomo_analyze_token` with `address` and `chain` (750) instead.

## 4. Answer in this shape

**Shortlist:** a table: token, chain, market cap, age, tracked traders in, LP burned, top-10 share, deployer record, and the main red flag (or "none found").

**Dropped:** one line with how many failed the cheap filter and the most common reason.

**Closer look:** one or two sentences on the cleanest one or two, with the numbers.

End with: *"A clean screen is not a reason to buy. This is data, not financial advice."* Offer to run **token-check** on any of them.

## Rules

- "Worth a look" means worth researching, never worth buying. Don't rank by expected return.
- A missing value is `null`, never zero. An unknown deployer is not a clean deployer.
- "Tracked traders" are a curated set, not every holder. Keep raw JSON out of the answer.
