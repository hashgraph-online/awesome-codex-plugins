---
name: portfolio-review
description: Review the user's own crypto wallet or bags and rank the holdings by risk. Use when the user asks to review their wallet or portfolio, what's risky in their bags, which of their coins look shaky, how concentrated they are, or pastes their own wallet address and asks what to worry about.
argument-hint: <wallet address>
---

# Review a portfolio, riskiest first

Answer: **which of these holdings carry the most risk, and why?** Use the StalkChain connector. Every lookup spends credits, so check only the holdings that matter.

## 1. Get the holdings

- Solana addresses are base58, 32–44 characters; EVM addresses are `0x` plus 40 hex characters.
- Call `stalkchain_wallet_portfolio` with `wallet`, `minValueUsd` around 50 to drop dust, and `chains` set to the chains in play: `["solana"]` for a Solana address, the EVM chains the user names otherwise (250 credits per five chains; all seven is 500).
- If the user gave a trader handle instead, find them with `stalkchain_fomo_search` (`type: "traders"`, 250) and use `stalkchain_fomo_trader_balances` with `trader` (250).

In Claude and ChatGPT, `stalkchain_wallet_portfolio` shows the user an interactive card. Don't re-list every holding; go straight to the risk read. Where no card appears (a terminal), include the top holdings.

## 2. Pick what to check

Take the five largest holdings by value. Skip native coins (SOL, ETH, BNB) and major stablecoins: a rug check tells you nothing about them. Say how many you skipped. Ask before checking more than five, since each costs about 1,000 credits.

## 3. Quick read per holding, cheapest first

**Solana tokens**
1. `stalkchain_token_quality` with `token` (250): organic versus wash volume, verified flag, authority audit.
2. `stalkchain_token_onchain` with `token` (250): LP burn, live mint or freeze authority, top-10 concentration, risk score, already-rugged flag.
3. `stalkchain_fomo_kol_sell_pressure` with `address` (375): how many tracked holders sold recently and who still holds.
4. Only for the largest position, or when liquidity looks thin: `stalkchain_token_exit_check` with `token` and `usd` set to the position's value (500).

**EVM tokens:** `stalkchain_fomo_analyze_token` with `address` and `chain` (750): flow, holders, tracked traders, dev positions. In Claude and ChatGPT it also shows a card.

## 4. Answer in this shape

**Overview:** total value, number of holdings, and concentration (the share in the largest holding and in the top three).

**Ranked by risk:** a table, riskiest first: holding, value, share of portfolio, risk level (high, medium, low), and the one or two flags behind it.

**Worth a closer look:** the top one or two, with the numbers behind each flag.

**Not checked:** skipped holdings and anything the data couldn't cover.

Then one line: *"This is data, not financial advice."*

## Rules

- Risk level reflects the flags found, not a prediction. Never tell the user to sell, hold or buy.
- A missing value is `null`, never zero. No flags found is not the same as safe.
- "Tracked traders" are a curated set, not every holder.
- Keep raw JSON out of the answer.
