# Market data on Chord

Every read is a plain GET on `https://api.getchord.xyz/v1`. No key needed (60 requests a minute per
IP). Responses are JSON; prices are USD
numbers, timestamps are Unix seconds (UTC) unless the field name ends in `At` and the value is in
milliseconds (`updatedAt`).

All numbers come from Chord's own index of on-chain swaps ("the tape"), except `ref-price`, which is
CoinGecko. Say which one you used.

This page covers the eight EVM chains. Solana has its own read-only family (`/v1/chains/solana/*`,
base58 addresses, `updatedAt` in seconds, different coverage): see `solana.md`.

```bash
BASE=https://api.getchord.xyz/v1
```

## 1. Resolve the token first

Never guess an address. Use the helper or the curated list of the chain:

```bash
python3 scripts/chord.py token base AERO        # candidates with address, decimals, tags, flags
curl -s "$BASE/tokens?chain=8453"               # curated list (any of 143, 4663, 5042, 43114, 8453, 56, 42161, 1)
curl -s "$BASE/arc/tokens/search?q=argus&limit=5"   # Arc: every token traded in 24h, listed or not
```

- The curated list is the source of truth for decimals and the canonical address of a symbol.
- On Arc, search ranks the listed token above same-named copies, but it can also return look-alikes
  (a search for `USDC` returns USDCHAIN, usdc.cool, JEANUSDC; the real USDC is the predeploy
  `0x3600000000000000000000000000000000000000` from the curated list).
- On Robinhood Chain several memecoins reuse stock tickers. The tokenized share has the tag `stock`
  and a name ending in "Robinhood Token".
- `/v1/tokens/search` is NOT a per-chain search (it ignores `chain`); do not use it to resolve symbols.

## 2. Price and 24h stats

`python3 scripts/chord.py price CHAIN TOKEN` picks the right call below, filters the answer to the one
token, and adds the CoinGecko cross-check where it exists. Raw calls:

| Chain | Call | Price field |
|---|---|---|
| Monad 143 | `GET /tokens/market?chain=143` | `market[<lower-case address>].priceUsd`, `change24h`, `volume24h` |
| Robinhood 4663 | `GET /tokens/market?chain=4663` | same shape, plus `txns24h`, `liquidityUsd`, `spark` (24 hourly closes) |
| Robinhood 4663, one token | `GET /rh/token/{addr}?hours=24` | `token.priceUsd`, `token.change24hPct`, `token.volume24h` |
| Arc 5042 | `GET /arc/token/{addr}?hours=24` | `token.priceUsd`, `token.change24hPct`, `token.marketCapUsd` |
| Avalanche, Base, BNB, Arbitrum, Ethereum | `GET /chains/{key}/token/{addr}?hours=24` | `stats24h.priceUsd`, `stats24h.change24hPct`, `stats24h.volUsd`, `byDex` |
| Avalanche, Base, BNB, Arbitrum, Ethereum | `GET /chains/{key}/token/{addr}/ref-price` | CoinGecko `priceUsd`; `404 NOT_LISTED` = CoinGecko does not know this contract |

`{key}` is `avalanche`, `base`, `bnb`, `arbitrum` or `ethereum` (the numeric id also works). The zero address in a
`/chains/...` path means the chain's wrapped native token.

```bash
curl -s "$BASE/tokens/market?chain=4663"                                             # every listed RH token
curl -s "$BASE/arc/token/0xece5ca8bf9220718e5727754026757512212cb3c?hours=24"      # ARGUS on Arc
curl -s "$BASE/chains/base/token/0x940181a94a35a4569e4529a3cdfb74e38fd98631?hours=24"   # AERO on Base
curl -s "$BASE/chains/base/token/0x940181a94a35a4569e4529a3cdfb74e38fd98631/ref-price"  # CoinGecko check
```

`/tokens/market` returns thousands of rows: filter by the resolved address, do not dump it.

Majors (BTC, ETH) have no single "BTC" token on these chains. Quote the wrapped token you used and
say so: cbBTC on Base, BTC.b on Avalanche, BTCB on BNB Chain, cirBTC on Arc, WETH on any chain.

## 3. Candles

```bash
curl -s "$BASE/candles?chain=8453&token=0x940181a94a35a4569e4529a3cdfb74e38fd98631&tf=1h&limit=24"
```

- Works on all eight EVM chains. `tf`: `1m 5m 15m 1h 4h 1d 1w`. `limit` up to 1000; page with `from` / `to`
  (Unix seconds). `fill=1` carries the close through empty buckets.
- Each candle: `t` (bucket start), `o h l c` (USD), `v` (USD volume), `n` (trades). `forming: true`
  means the last candle is still open.
- BNB Chain answers carry `ingestFloor.minTradeUsd` (trades under that size are not recorded): say so
  when it matters.

## 4. Boards: what traded most, what is moving

`python3 scripts/chord.py board CHAIN --limit 10 [--sort volume|trades|change]` returns compact rows for
any of the eight EVM chains. Raw calls (always pass `limit`):

| Chain | Most traded 24h | Movers |
|---|---|---|
| Arc 5042 | `GET /arc/tokens?sort=volume&limit=10` (sorts: `volume trades traders change mcap`; default limit 100; `includeUnlisted=1` adds tokens without curated metadata) | `GET /arc/trending?limit=10` (2-hour acceleration score) |
| Robinhood 4663 | `GET /rh/tokens?sort=volume&limit=10` (`volume trades traders change`) | `sort=change` |
| Avalanche, Base, BNB, Arbitrum, Ethereum | `GET /chains/{key}/tokens?sort=volume&limit=10` (`volume trades change`) | `sort=change` |
| Monad 143 | `GET /tokens/market?chain=143`, sort rows by `volume24h` yourself | sort by `change24h` |

Arc rows carry `flags`: `wash` (a day's volume carried by one or two wallets) and `impostor` (an
unlisted token wearing a listed symbol). Flagged rows sort below clean ones; mention the flag when
you show such a row. `traders` counts attributed wallets (routers and bots are not wallets).

## 5. Chain totals and venues

```bash
curl -s "$BASE/arc/overview"            # last24h {volUsd, swaps, tokens}, venues24h, hourly24, daily, coverage
curl -s "$BASE/rh/overview"
curl -s "$BASE/chains/base/overview"    # also wallets {today, yesterday}
curl -s "$BASE/arc/venues?days=7"       # per-venue daily series and share; rh/venues and chains/{key}/venues?days=1..30 too
curl -s "$BASE/chains/base/status"      # freshness: recentAt, staleSec, backfillComplete
```

## 6. Token detail: holders, trades, pools, launches

```bash
curl -s "$BASE/arc/token/{addr}/holders?limit=20"     # holders, concentration top1..top100, top rows
curl -s "$BASE/rh/token/{addr}/holders?limit=20"
curl -s "$BASE/arc/token/{addr}/trades?limit=50"      # newest prints
curl -s "$BASE/chains/base/token/{addr}/trades?limit=50"
curl -s "$BASE/arc/token/{addr}/pools"                # every indexed pool (V2/V3 address or V4 poolId + hooks)
curl -s "$BASE/arc/graduated?hours=24&limit=20"       # new Arc launches that passed Chord's screens
curl -s "$BASE/arc/launchers?hours=24"                # who is creating pools
```

Holder answers include `complete` and `coverage`: when `complete` is false the ledger is still
backfilling, so say the counts may be partial. The zero address and `0x...dead` in the top rows are
burned supply, not holders.

## 7. Wallets and smart money

```bash
curl -s "$BASE/smart-money/top?chain=4663&source=onchain&window=7d&limit=10"   # 5042, 4663, 143; window 24h 7d 30d all
curl -s "$BASE/portfolio/{wallet}/pnl?chain=4663"     # 5042, 4663, 143 or all
curl -s "$BASE/portfolio/{wallet}/trades?chain=4663"
curl -s "$BASE/chains/base/wallet/{wallet}"           # Avalanche, Base, BNB, Arbitrum, Ethereum: swaps + average-cost PnL
```

- PnL is average-cost from the wallet's swaps. Tokens that arrived by transfer have no cost basis and
  are excluded (`untrackedAmount`). It is not a balance sheet.
- The smart-money board ranks by a skill-adjusted score with routers and bots removed; `pnlUsd` can
  be mostly unrealized (`unrealizedUsd`). Say that when you quote it.
- On Avalanche, Base, BNB, Arbitrum and Ethereum the raw tape is short (days, see the `window` field): say how far back
  the numbers go.
- Chord has no balance endpoint in the public REST API. For "what is in my wallet" use Ask with the
  wallet (Chord Ask at https://getchord.xyz/ask) or the user's wallet / block explorer.

## 8. Liquidity (Arc, Robinhood Chain, Monad)

```bash
curl -s "$BASE/lp/overview?chain=5042"
curl -s "$BASE/lp/pools?chain=5042&sort=fee_tvl&limit=10"     # TVL, volume, fees, fee/TVL, APR; suspect pools hidden unless flagged=1
curl -s "$BASE/lp/positions?chain=5042&owner={wallet}&status=open"
curl -s "$BASE/lp/leaderboard?chain=5042&sort=profit&limit=10"
```

APR figures annualise one window of fees: say which window (`interval`) and that it is not a forecast.

## 9. Freshness and coverage

- `updatedAt` (ms) on most answers; `coverage.stale: true` or a large `staleSec` means the rollup is
  behind. Say so instead of presenting old numbers as live.
- `503 NOT_READY` means a rollup has not run on this deployment; retry once later, then report.
- Robinhood Chain stock tokens trade around the clock on-chain while the underlying exchange does
  not: see `stocks.md`.

## 10. Backtests (Hyperliquid perps, FX, gold)

`GET /v1/backtest` replays one bar-close strategy over stored candles. It is a simulation: nothing
is traded, and it is not about the eight EVM chains above (the candles are Hyperliquid perps and
Dukascopy FX / metals).

```
GET /v1/backtest?symbol=BTC&interval=4h&strategy=supertrend&days=365
```

- `symbol`: a Hyperliquid coin id, matched without case (`BTC`, `ETH`, `kPEPE`), or `EURUSD`,
  `GBPUSD`, `USDJPY`, `USDCHF`, `AUDUSD`, `USDCAD`, `USDSEK`, `NZDUSD`, `EURJPY`, `GBPJPY`, `EURGBP`,
  `XAUUSD` (`gold`), `XAGUSD` (`silver`).
- `interval`: `1m` `5m` `15m` `30m` `1h` `4h` `1d`. `days`: 1 to 3650 (default 365), ending now.
- `strategy` and its parameters: `supertrend` (`atr` 10, `mult` 3) · `ema_cross` (`fast` 20,
  `slow` 50) · `rsi` (`length` 14, `lower` 30, `upper` 70) · `donchian` (`length` 20) · `buy_hold`.
- Optional: `side` (`long` / `short` / `both`), `feeBps` per side (default 4.5 on Hyperliquid, 1 on
  FX), `stopPct`, `takePct`, `leverage` (0.1 to 20).

The model: signal on a closed bar, fill at the next bar's open, one position at a time, no funding
and no slippage. The answer repeats it in `assumptions`: quote that sentence with the result. Every
time field here is Unix MILLISECONDS. `from`, `to` and `bars` are the window that was really tested,
which can be shorter than `days` (the store holds about seven months of 1h Hyperliquid bars, years
of 4h and 1d). Fewer than 50 bars is a `400` whose message says what the store keeps: try a coarser
interval. Compare `metrics.totalReturnPct` with `metrics.buyHoldPct` before calling a strategy good.
