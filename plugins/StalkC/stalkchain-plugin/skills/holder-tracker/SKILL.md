---
name: holder-tracker
description: Track how a token's holders change over time by taking snapshots and comparing them. Use when the user wants to watch a token's holders, see who joined or left since yesterday or last week, track whether smart money is accumulating or exiting, or set up a daily holder check. Works well as a scheduled task.
argument-hint: <token address or ticker>
---

# Track a token's holders over time

There is no holder history to look up, so this skill builds one: **take a snapshot now, take another later, and compare.** Use the StalkChain connector.

## 1. Pin down the token

Tickers need an address: `stalkchain_fomo_search` with `q` and `type: "tokens"` (250 credits). Confirm the token if several match.

## 2. Take a snapshot

`stalkchain_fomo_token_snapshot` with `address`, plus `chain` if needed and `holdersLimit` (default 50) (500 credits). It returns the capture time, price, total holders, top-10 share, the tracked traders holding it with amounts and values, and 24h flow.

**Save it.** Where you can write files (Claude Code, Cowork, Cursor), save the result unchanged to `snapshots/<token address>/<capturedAt>.json` in the user's project and tell them where. Where you can't, keep it in this conversation and say the comparison must happen here, or in an app that can save files.

## 3. Compare with an earlier snapshot

Find the most recent earlier snapshot for the same token (in `snapshots/<token address>/`, or earlier in the conversation). Call `stalkchain_fomo_compare_snapshots` with `before` and `after` set to the two saved snapshots (0 credits, no data fetched). It lists new tracked holders, exits, who added and who trimmed, and the change in total holders, top-10 share and price.

If there's no earlier snapshot, say this is the baseline and when a comparison would be useful (a day or a week later).

## 4. Make it automatic

This suits a scheduled task, for example every morning: "Take a holder snapshot of `<address>`, compare it with the last one, and summarise the changes." Each run costs 500 credits. Offer to set one up if the app supports scheduled tasks; the **watchlist-analyst** agent can cover several tokens in one daily brief.

## 5. Answer in this shape

**Since <earlier time>:** one sentence, e.g. "Three tracked traders joined and one exited; total holders up 12%."

**Tracked traders:** joined, exited, added, trimmed, with handles and USD values.

**Whole token:** total holders, top-10 share and price, then and now.

For a first snapshot: the baseline numbers and where it was saved.

## Rules

- Don't edit a saved snapshot; compare it as captured.
- A missing value is `null`, never zero. "Tracked traders" are a curated set, not every holder.
- Holder changes are data, not a signal to buy or sell. Keep raw JSON out of the answer.
