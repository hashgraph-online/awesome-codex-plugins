---
name: chord-charts
description: Draw a candlestick price chart (SVG) with volume for any token traded on Ethereum, Base, Monad, BNB Chain, Avalanche, Arbitrum, Robinhood Chain (tokenized stocks such as NVDA, TSLA), Arc or Solana, from Chord's own DEX trade data, and summarise the move (change, high, low, volume, trades). Use when the user asks for a chart, candles, price history or "how did X move" for a token on those chains. No API key; Python 3 standard library only.
license: MIT
metadata:
  author: Chord (getchord.xyz)
  homepage: https://getchord.xyz
  version: 1.0.0
---

# Chord charts

Chord indexes every DEX swap on its chains and builds candles from those trades. `scripts/chart.py` turns them into a standalone SVG candlestick chart and prints a JSON summary.

## Draw a chart

```bash
python3 scripts/chart.py --chain base --token AERO --tf 1h --limit 48
python3 scripts/chart.py --chain solana --token BONK --tf 15m --limit 96
python3 scripts/chart.py --chain robinhood --token NVDA --tf 1d --limit 60
python3 scripts/chart.py --chain arbitrum --token 0x912ce59144191c1204e64559fe8253a0e49e6548 --tf 4h --limit 42 --out arb.svg
```

- `--chain`: `ethereum`, `base`, `monad`, `bnb`, `avalanche`, `arbitrum`, `robinhood`, `arc`, `solana`.
- `--token`: a symbol or name, or an address (`0x…` on EVM chains, the base58 mint on Solana, case-sensitive). A symbol is resolved through Chord's search; the script prints the address it picked. Similar tickers are common: if the user named a token loosely, show them the resolved address.
- `--tf`: `1m 5m 15m 1h 4h 1d 1w` (Solana up to `1d`). `--limit`: number of candles, up to 1000.
- Output: the SVG file (path in the summary, default `chart-<symbol>-<chain>-<tf>.svg`) and a JSON summary on stdout: `symbol`, `token`, `open`, `close`, `changePct`, `high`, `low`, `volumeUsd`, `trades`, `lastCandleOpen`.

Show the user the chart file and a one-line read of the summary, for example: "AERO on Base, last 48 hours: $0.884, -2.75%, range $0.831 to $0.920, $10.5M traded."

## Notes

- Prices are in USD from on-chain trades. Wrapped majors stand in for the coin: WETH for ETH, cbBTC on Base, BTC.b on Avalanche, BTCB on BNB Chain, WMON on Monad. Say which token you charted.
- Robinhood Chain stock tokens trade around the clock on-chain, so their candles can move while the US market is closed.
- Solana candles are one pool's prices (the main pool), not a blend across pools.
- If the last candle is still open, `lastCandleOpen` is true and the subtitle says so.
- About 60 requests a minute without a key; a chart costs one or two requests.
- For raw data without a chart: `GET https://api.getchord.xyz/v1/candles?chain=<chainId>&token=<address>&tf=1h&limit=48` (EVM) or `GET https://api.getchord.xyz/v1/chains/solana/token/<mint>/candles?tf=1h&limit=48`.
