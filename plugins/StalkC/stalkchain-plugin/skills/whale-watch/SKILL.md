---
name: whale-watch
description: Spot large buys and sells by tracked crypto traders, recent moves by named whale wallets, and the biggest Hyperliquid perps traders. Use when the user asks about whale activity, big buys or big sells, large trades right now, what a whale wallet has been doing, leveraged whales on Hyperliquid, or wants trades above a dollar amount.
argument-hint: "[minimum USD, chain, token or wallet]"
---

# Whale watch

Show the user the biggest recent moves: **large trades by tracked traders, and what named wallets have been moving.** Use the StalkChain connector. The live feed is the cheapest call there is, so start there.

## 1. Big trades by tracked traders

Call `stalkchain_fomo_alerts` (125 credits per call) with:

- `type: "buy"` or `type: "sell"` (one call each if the user wants both), or `type: "whale"` for the feed's own whale events;
- `minUsd` set to the user's threshold (default 10,000);
- `chain`, `tokenAddress` or `trader` when the user names one, and `since` for a time window.

Know what the dollar figure means. On a **buy** it is the trader's whole position after the buy, not the size of the buy. On a **sell** it is the realised profit or loss on that sale. Use `tradeUsd` when present for the trade size. For the true size of the few largest buys, call `stalkchain_fomo_trade_detail` with `tradeId` and `trader` (250 each), and ask before checking more than three.

Each call returns at most the newest 100 events, so a long window may not be fully covered; filter by type and chain to reach further back, and say what time range you covered.

Free alternative for "right now": `stalkchain_fomo_watch_stream` with `stream: "trades"`, `minUsd`, `side` and `durationSeconds` (0 credits) listens to live on-chain fills, where the dollar value is the real fill size. It covers Solana and Robinhood Chain only and may not be available on every plan; if it errors, use the feed above.

## 2. Named wallets

- **EVM wallet:** `stalkchain_wallet_transfers` with `wallet`, `chain` and `limit` (500 credits): transfers in and out, newest first, with USD values where known.
- **Solana wallet:** there is no transfer list. Use `stalkchain_wallet_pnl` with `wallet` (500) for positions and recent profit.
- **A trader's handle:** filter the feed with `trader`, or follow **trader-check**.

## 3. Perps whales (Hyperliquid)

When the user asks about leverage, perps or Hyperliquid whales:

- Who is long or short one coin: `stalkchain_perps_smart_money` with `coin` and `traders: 100` (750 credits), not one wallet at a time.
- `stalkchain_perps_leaderboard` with `window` (250 credits): the biggest winners or, with `sortBy: "losses"`, losers. It covers every Hyperliquid trader, not just tracked ones.
- `stalkchain_perps_wallet` with `wallet` (250 each) for what a whale is long or short now, with liquidation prices. Ask before checking more than three.

## 4. Answer in this shape

**Biggest moves:** a table, largest first: time, trader or wallet, buy or sell, token and chain, size, and which measure the size is (trade size, position value or realised profit).

**Pattern:** one or two sentences, e.g. "Mostly sells on Base; two tracked traders took profit on the same coin."

**Wallets:** for each named wallet, its largest moves in the period.

Then one line: *"This is data, not financial advice."*

## Rules

- Never present a position value or realised profit as a buy or sell size. Label which one it is.
- "Tracked traders" are a curated set, not every whale on chain. A missing value is `null`, never zero.
- A big buy is not a reason to buy. Don't speculate about who owns a wallet. Keep raw JSON out of the answer.
