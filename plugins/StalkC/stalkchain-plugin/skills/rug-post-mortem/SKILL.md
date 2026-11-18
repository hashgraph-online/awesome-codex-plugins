---
name: rug-post-mortem
description: Reconstruct what happened to a crypto token that crashed or died. Use when the user asks what happened to a coin, whether it was a rug pull, who dumped it, who sold first, who made money on it, or why the price collapsed.
argument-hint: <token address or ticker>
---

# What happened to this coin?

Build a timeline from the data: **who got in first, who sold first, who made money, and whether the pattern looks like a rug or a fade.** Use the StalkChain connector. Calls are listed cheapest first; stop when the story is clear.

## 1. Pin down the token

If the user gave a ticker, call `stalkchain_fomo_search` with `q` and `type: "tokens"` (250 credits) and confirm which token. Dead coins often share tickers with live ones.

## 2. Gather the evidence (Solana)

1. `stalkchain_token_onchain` with `token` (250): whether it is already flagged rugged, LP burn, mint and freeze authority, the dev's remaining holding, and price change across windows.
2. `stalkchain_fomo_token_devs` with `address` (250): the dev's and insiders' positions, what they sold, realised profit and hold time.
3. `stalkchain_token_pnl_leaders` with `token` (250): the wallets that made and lost the most, and whether they still hold. On-chain, so it covers every wallet.
4. `stalkchain_token_early_buyers` with `token` (500): when the first buyers got in, whether they sold, what they made, and bundler share.
5. Price path: `stalkchain_price_history` with `chain: "solana"`, `address`, `startTime`, `endTime` and `interval` (`1h` for a fast collapse, `1d` otherwise; 250). For finer detail, `stalkchain_fomo_token_candles` with `address` and `resolution` (250) may work; if it errors, carry on without it.
6. Only if the dev looks like a repeat launcher: `stalkchain_token_deployer` with `token` (500).
7. Only if the crash was within the last day: `stalkchain_fomo_kol_sell_pressure` with `address` (375) for which tracked traders sold. It only reaches back 24 hours.

**EVM tokens:** use `stalkchain_fomo_token_devs`, `stalkchain_fomo_token_stats` (flow by window, 250) and `stalkchain_price_history` with the token's `chain`. The holder-level tools above are Solana-only, so say what you couldn't see.

## 3. Answer in this shape

**What happened:** two or three sentences, e.g. "Price fell 94% in six hours after the deployer sold its full position into the pool."

**Timeline:** launch, first buys, peak, first big sells, collapse, each with a time and the numbers behind it.

**Who sold first:** dev, insiders, early buyers or tracked traders, in order, with amounts where known.

**Who made money:** the top winners and losers, and how much of the profit sits with one or a few wallets.

**Rug or fade?** Say which pattern the data fits and why. Rug signs: dev or insiders selling into the peak, LP pulled or unburned, authorities live, bundlers exiting together. Fade signs: dev still holding, broad selling, no single dominant seller.

Then one line: *"This is data, not financial advice."*

## Rules

- Describe wallets and what they did. Don't accuse a person of fraud or guess who owns a wallet.
- A missing value is `null`, never zero. An empty dev list means no dev position is known, not that there was no dev.
- "Tracked traders" are a curated set, not every holder. Keep raw JSON out of the answer.
