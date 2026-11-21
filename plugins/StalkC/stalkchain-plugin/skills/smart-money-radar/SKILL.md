---
name: smart-money-radar
description: Find what top crypto traders and smart money are buying or selling right now. Use when the user asks what's trending, what KOLs or whales are buying, which coins several traders just entered, what is hot today, or wants a list of new opportunities to research.
argument-hint: "[time window, chain, or buy/sell]"
---

# What smart money is doing right now

Give the user a short, ranked list of coins with a reason for each, then offer to check any of them. Use the StalkChain connector. Every lookup spends credits, and the live feeds are the cheapest calls there are, so start there.

## 1. Pick the right lens

Read what the user asked for. Default to the last hour of buys on all chains.

- **"What are traders buying?"** Call `stalkchain_fomo_multi_trader_entries` with `windowMinutes` (default 60), `minTraders` (default 3, lower it to 2 if nothing comes back), and `side: "buy"` (125 credits). This returns coins that several different tracked traders bought in the window. In Claude and ChatGPT it shows the user an interactive card, so keep your list short and add the pattern and what stands out.
- **"Is anyone piling into the same coin?"** Call `stalkchain_fomo_coordinated_activity` with `side`, `minTraders` and `windowMinutes` (125 credits).
- **"What's trending?"** Call `stalkchain_fomo_token_board` with `board: "trending"`, or `"graduated"` for coins that just left the launch curve (250 credits).
- **"What's the feed saying?"** Call `stalkchain_fomo_alerts` with `limit` around 50 for the raw live buys and sells (125 credits).
- **"What are traders writing about?"** Call `stalkchain_fomo_theses_recent` (1,250 credits). Use it only when asked, or follow the **narrative-tracker** skill.

Add `chain` (e.g. `solana`, `base`, `robinhood`) when the user names one.

The feed covers the newest 100 events per call. The response says which time range it actually covered; if that's shorter than the window asked for, say so, or narrow by `chain`.

## 2. Answer in this shape

A numbered list, at most ten coins, each on one line:

`1. TICKER (chain): 5 tracked traders bought in the last hour, first at 14:02, latest at 14:51, including @handle`

Then add one sentence on the overall pattern, for example "Mostly new Solana launches under $1M" or "Rotation into Base coins".

Close with an offer: *"Want me to check any of these before you buy? I'll look at holders, the dev, liquidity and real volume."* If they pick one, follow the **token-check** skill.

## Rules

- A coin several traders bought is a lead to research, not a recommendation. Never say "buy this".
- Say "tracked traders", not "everyone": the feeds cover a curated set of known traders.
- The dollar value on a buy in the feed is the trader's whole position after the buy, not the size of the buy. Don't add those values up and call it money bought.
- If nothing matches, widen the window or lower `minTraders` once, then say plainly that it's quiet.
- A missing value is `null`, never zero. Keep raw JSON out of the answer.
