---
name: perps-check
description: Read the perps market on Hyperliquid and who is positioned in it. Use when the user asks which wallets or top traders are long or short a coin ("who is long $HYPE", "are whales short BTC") and their size, entry, PnL or liquidation prices, about funding rates, open interest, whether longs or shorts are crowded, a funding arbitrage between Hyperliquid, Binance and Bybit, what is hot on Hyperliquid, stock perps such as TSLA or NVDA, or a perp chart.
argument-hint: "[coin or stock ticker]"
---

# Check a perp market

Answer one question: **who is paying whom, how crowded is it, and what is it doing?** Use the StalkChain connector. Each call below is 250 credits; most answers need two.

## 0. Who is long and who is short

When the user asks which wallets or traders are long or short a coin, or their PnL on it ("$HYPE" in a long/short question means the HYPE perp), call `stalkchain_perps_smart_money` first, with `coin` and `traders: 100` (750 credits). It returns, for the most profitable Hyperliquid traders: how many hold the coin, long and short counts, dollar size, average entries, unrealized PnL, the nearest liquidation prices on each side, and the biggest positions by wallet. Show a long/short summary table, then the biggest shorts and biggest longs with wallet, size, entry, unrealized PnL, leverage and liquidation price. Don't use the social-trading feed or FOMO trader positions for this: they only cover FOMO users.

## 1. The market

`stalkchain_perps_markets` with `coins` set to what the user named (`venue: "stocks"` for TSLA, NVDA, HOOD, gold or the S&P 500): mark price, 24h change and volume, open interest in USD, funding per hour and per year, and premium to the oracle.

No coin named ("what is hot on Hyperliquid")? Call it with `sortBy` set to `volume`, `openInterest`, `funding` or `fundingNegative` and `limit: 10`.

## 2. Funding

`stalkchain_perps_funding` with `coins` and, when the user asks about a trend, `days` (one coin only):

- Positive funding means longs pay shorts; the longs are crowded. Negative means the opposite.
- The spread between venues is a basis trade only if it is wide and both venues have depth. Say that it ignores fees, borrow and the risk of the spread moving.
- With `days`: the average, the extremes, and how often longs paid.

## 3. Only if asked

- A chart: `stalkchain_perps_candles` with `coin`, `interval` and `hours`.
- One named wallet: `stalkchain_perps_wallet`. The best traders overall: `stalkchain_perps_leaderboard`.

## 4. Answer in this shape

**Market:** price, 24h change, volume and open interest, in one line.

**Funding:** per year on Hyperliquid, Binance and Bybit, and who pays.

**What it means:** one or two sentences, e.g. "Longs have paid 95% of hours this week; positioning is one-sided."

Then one line: *"This is data, not financial advice."*

## Rules

- Quote funding per year as well as per hour; hourly numbers look tiny and mislead.
- Open interest is in USD. Don't mix it with coin units.
- Never tell the user to open, close or size a position. Lay out the facts.
- A missing value is `null`, never zero. Keep raw JSON out of the answer.
