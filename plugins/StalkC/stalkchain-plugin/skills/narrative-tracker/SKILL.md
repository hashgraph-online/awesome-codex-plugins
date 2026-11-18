---
name: narrative-tracker
description: Find the crypto narratives and themes traders are talking about and trading right now. Use when the user asks what the current narratives or metas are, what themes are hot, what traders are writing about, which sectors are rotating, or wants the coins and best calls behind a theme.
argument-hint: "[chain or theme]"
---

# What are the narratives right now?

Group what tracked traders are trading and writing into a few themes, with the coins and the most-liked calls behind each. Use the StalkChain connector. Written calls ("theses") cost five times a normal call, so read the boards first.

## 1. What's moving (cheap)

1. `stalkchain_fomo_token_board` with `board: "trending"` (250 credits).
2. `stalkchain_fomo_multi_trader_entries` with `windowMinutes: 240` and `minTraders: 2` (125): coins several tracked traders bought.

Add `chain` when the user names one.

## 2. What traders are writing (1,250 credits)

`stalkchain_fomo_theses_recent` with `sort: "recent"` and `limit: 100`, plus `chain` if named. Use `sort: "equity"` instead when the user wants calls backed by big positions. This feed has position size and profit but no likes.

Read the text and group the coins into three to six themes (for example AI agents, tokenized stocks, a celebrity meme, a chain rotation). A theme needs at least two coins or several traders; leave one-offs out.

## 3. Most-liked calls (ask first)

Likes come only from `stalkchain_fomo_theses_for_token` with `address`, `sort: "likes"` and `limit: 5` (1,250 credits per token). Offer it for the top coin in each theme and ask before spending, e.g. "Pulling the most-liked calls for the top coin in each of four themes costs 5,000 credits. Go ahead?"

## 4. Answer in this shape

For each theme, strongest first:

**Theme name:** one sentence on what the narrative is.
- Coins: tickers with chain, and which are on the trending board.
- Activity: how many theses and distinct traders, and the total position size behind them where known.
- Top calls: one or two, paraphrased in a line each, with the handle and likes if fetched.

Close with one sentence on the overall mood, and an offer to run **token-check** on any coin.

## Rules

- A narrative is what traders are saying, not a prediction. Never tell the user to buy into a theme.
- Paraphrase theses; don't paste them. Credit the handle.
- A missing value is `null`, never zero. "Tracked traders" are a curated set, not the whole market.
- Keep raw JSON out of the answer. Data, not financial advice.
