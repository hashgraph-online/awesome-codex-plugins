---
name: stonkfun-research
description: Research tokens on StonkFun, the Solana launchpad for tokens paired with tokenized stocks (xStocks) and stablecoins. Use when the user mentions StonkFun, xStock pairs, a StonkFun token, launches, burns, holder rewards, creator fees, or StonkFun platform revenue.
argument-hint: "[token mint or creator wallet]"
---

# StonkFun research

Use the StalkChain connector's `stonk_*` tools. Each costs 250 credits unless noted.

## Pick the call

- **One token, quick:** `stonk_token` with `mint` for market data and the launch record (creator, launchpad, mode, quote pair, launch date).
- **One token, everything:** `stonk_token_report` with `mint` (about 1,250 credits, 1,500 for a pump launch). It covers market data, launch record, burns, holder rewards, airdrop, creator fees, backing and the creator's other launches, with flags. Add `includeTrackedHolders: true` (+500) only if the user asks which tracked traders hold it. In Claude and ChatGPT this shows the user an interactive card: add the interpretation and the flags that matter rather than re-listing every number.
- **One detail only:** `stonk_token_burns`, `stonk_token_rewards`, `stonk_token_airdrop`, `stonk_token_fees` or `stonk_token_backing` (pump launches only), each with `mint`.
- **Browse or search:** `stonk_tokens` with `sort` (`marketCap`, `newest` or `volume`) and optional `q` to search by name or ticker, or `quoteMint` for one pair.
- **Everything one wallet launched:** `stonk_launches` with `creator`. Many launches with few survivors is a serial-launcher pattern worth pointing out.
- **Platform view:** `stonk_stats` for totals and graduation thresholds, `stonk_revenue` for revenue, buybacks and burns, `stonk_rewards` for holder payouts across tokens.
- **Launching your own:** follow the **stonkfun-launch-guide** skill.

StonkFun mints are ordinary Solana tokens. For holder safety, smart money and dev checks on the same mint, follow the **token-check** skill.

## Answer in this shape

Lead with what the user asked. For a token: price, market cap, 24h volume, launch date, and who launched it. Then burns, rewards and fees, but only if they're non-zero or the user asked. Then anything notable, such as heavy burns, a reward-mode transfer tax, a creator with many dead launches, unclaimed fees, or a price far below its peak.

## Rules

- A missing value is `null`, never zero. Most tokens launch without an airdrop, and that's normal.
- Not financial advice. Present the data; never tell the user to buy or sell.
- Keep raw JSON out of the answer.
