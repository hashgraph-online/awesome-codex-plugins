---
name: trader-playbook
description: Work out how a crypto trader actually trades, from their real fills and positions. Use when the user asks how a trader trades, their strategy or style, typical entry size, how long they hold, when they take profit, which chains they trade, or wants to learn from a trader's habits. Research only; never places trades.
argument-hint: <trader handle>
---

# How does this trader actually trade?

Describe the trader's habits from their own fills and closed positions: **sizing, hold time, taking profit, chains, and what their wins and losses look like.** Use the StalkChain connector. This is research only: it never copies, places or schedules a trade.

## 1. Find the trader

`stalkchain_fomo_search` with `q` and `type: "traders"` (250 credits). Confirm the account if several match. If **trader-check** already ran in this conversation, reuse what it found.

## 2. Pull the record, cheapest first

1. `stalkchain_fomo_trader_positions` with `trader`, `status: "closed"` and `limit: 200` (250): entry and exit prices, cost basis, realised profit, chain, opened and closed times. The provider returns only the most recent closed positions per page; page with `cursor` (250 each) or buy more with `deep: 4` (about 1,000). Ask before going past 1,000 credits.
2. `stalkchain_fomo_trader_swaps` with `trader` (250 per 100 fills): the individual buys and sells, which show scaling in and taking profit in parts.
3. `stalkchain_fomo_trader_positions` with `status: "open"` (250): what they're sitting in now and for how long.
4. Optional: `stalkchain_fomo_theses_by_trader` with `trader` (1,250) for why they say they enter. Ask first.

## 3. Work out the playbook

From the rows, compute:

- **Entry size:** median and range of cost basis. Leave out positions with no entry price: those tokens were received, not bought.
- **Hold time:** median from open to close, and the share closed within an hour, a day and a week.
- **Taking profit:** how often a position was sold in several parts versus all at once, and whether they sell into strength or cut losers fast.
- **Win rate and payoff:** share of closed positions in profit, average win against average loss.
- **Chains and coins:** where the trades happen, and whether they favour new launches or established coins.

Always state the sample: "Based on 63 closed positions from 2 Sep to 1 Oct."

## 4. Answer in this shape

**Style in one line:** e.g. "Fast Solana launch flipper: small entries, most exits within an hour, sells in two or three parts."

**The playbook:** a short table, measure then value, for the five areas above.

**What stands out:** two or three observations, such as one trade carrying most of the profit, or very different behaviour on winners and losers.

Then one line: *"Past behaviour doesn't predict future results. This is data, not financial advice."*

## Rules

- Never set up, suggest or place copy trades. If asked, say this plugin is read-only.
- A missing value is `null`, never zero. A small sample is a small sample: say so.
- Profit comes from tracked wallets only. Keep raw JSON out of the answer.
