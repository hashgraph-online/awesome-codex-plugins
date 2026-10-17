# Stock tokens on Robinhood Chain (4663)

Robinhood Chain carries tokenized US stocks and ETFs (83 today: NVDA, TSLA, AAPL, SPY, QQQ, GLD,
MSTR, COIN...). They trade on-chain, around the clock, mostly against USDG (the chain's dollar
stablecoin, 6 decimals) and ETH. Chord indexes every swap of them.

## A stock token is not the share

Say this whenever the user might confuse the two:

- A stock token is an ERC-20 on Robinhood Chain whose price tracks the underlying share. It is not
  a share held in the user's name at a broker. Which rights it carries (dividends, votes,
  redemption) and who may hold it are set by the issuer's terms, not by Chord: do not claim
  shareholder rights or eligibility.
- "Buy $100 of AAPL" is ambiguous. Ask whether they mean the real share (a brokerage, not Chord) or
  the AAPL stock token on Robinhood Chain. Only the second is something Chord can quote.
- The token trades when the exchange is closed (nights, weekends, holidays). Its price then is
  whatever on-chain buyers and sellers agree, and can drift from the last exchange price.

## Same ticker, different token

Memecoins on Robinhood Chain reuse stock tickers. Today `GME` has four tokens, `AMC` three, `NET`
two. Only one row is the tokenized share:

- tag `stock` in `/v1/tokens?chain=4663` (ETFs also carry `etf`), and
- a name ending in "Robinhood Token" (e.g. "NVIDIA • Robinhood Token"), and
- presence in `/v1/rh/stocks` (that endpoint lists only stock tokens).

`python3 scripts/chord.py token robinhood GME` shows every candidate and points at the stock row.
Never quote a row tagged `meme` as "the GameStop stock".

## The screener: `GET /v1/rh/stocks`

```bash
python3 scripts/chord.py stock NVDA            # one row, compact, with the field meanings attached
curl -s https://api.getchord.xyz/v1/rh/stocks   # all of them
```

One row per stock token (no parameters; filter by `symbol` or `address` yourself):

| Field | Meaning |
|---|---|
| `priceUsd`, `change24hPct` | last on-chain trade price and 24h change, from Chord's tape |
| `volume24h`, `buyVolume24h`, `sellVolume24h`, `trades24h`, `traders` | 24h activity |
| `liquidityUsd` | pool liquidity Chord sees for the token |
| `navUsd` | the reference price of the underlying, when one is published |
| `navSource` | `xyz-perp` = the trade.xyz perpetual's mark on Hyperliquid (tracks the underlying 24/7, can carry a small funding premium off-hours); `catalogue` = the issuer's exchange rate at the last catalogue refresh |
| `basisPct` | gap of the token to `navUsd`, percent: `(priceUsd / navUsd - 1) x 100`. Positive = the token trades above the reference |
| `offHours7d.sharePct` | share of the last 7 days' volume traded outside the NYSE session (09:30 to 16:00 New York, Mon to Fri; holidays not modelled) |

The answer's `note` field restates these definitions; read it if a field looks different.

### "Price of NVDA's stock token and its gap to the real stock"

1. `chord.py stock NVDA` (or `GET /v1/rh/stocks` and take the row with `symbol` NVDA).
2. Answer with `priceUsd`, `navUsd`, `navSource`, `basisPct`, plus the time (`updatedAt`).
3. Say what the reference is: with `navSource = xyz-perp` it is a perpetual's mark price that tracks
   the share around the clock, not the official exchange print. Chord does not serve exchange quotes.
4. If `navUsd` is null (about 40 % of rows today, e.g. SPY, GLD, USO), say Chord has no reference
   price for that one. For the real share's price, Ask can look it up (it reads the Nasdaq quote per
   ticker, Chord Ask at https://getchord.xyz/ask), or the user can check a market data site. Do not compute a gap from a
   remembered price.

Example from 2026-10-02 (see `examples.md`): NVDA token $234.31, reference $234.01 (xyz-perp), gap
+0.13 %, 24h volume $30.8M, 57.7 % of the last 7 days' volume outside NYSE hours.

## One stock in depth

```bash
curl -s "https://api.getchord.xyz/v1/rh/token/0xd0601CE157Db5bdC3162BbaC2a2C8aF5320D9EEC?hours=168"   # hourly series + venue split
curl -s "https://api.getchord.xyz/v1/candles?chain=4663&token=0xd0601CE157Db5bdC3162BbaC2a2C8aF5320D9EEC&tf=1h&limit=48"
curl -s "https://api.getchord.xyz/v1/rh/token/0xd0601CE157Db5bdC3162BbaC2a2C8aF5320D9EEC/holders?limit=20"
curl -s "https://api.getchord.xyz/v1/tokens/stats/0xd0601CE157Db5bdC3162BbaC2a2C8aF5320D9EEC"            # 5m/1h/6h/24h windows, ATH, pools
```

## Buying or selling a stock token

It is an ordinary swap on chain 4663 (`references/quote-and-swap.md`):

```bash
python3 scripts/chord.py quote robinhood USDG NVDA 100
```

- Pay with USDG (needs an approval to the router) or ETH (native, no approval). Gas is ETH.
- Chord's fee is 0 bps on most stock tokens, USDG and WETH; read `feeBps` from the quote.
- Same confirmation flow as any swap. In the summary, name the token as "NVDA stock token on
  Robinhood Chain" with its full address, and add one line that it is not the share itself.
- Off-hours, the token can trade at a premium or discount to the reference; show `basisPct` when it
  is large (say above 1 %).

## Market movers

- On-chain: `GET /v1/rh/stocks`, sort by `change24hPct` or `volume24h` yourself.
- The US market itself (the real share's price and trend, earnings dates, news): not in the REST
  API. Chord Ask reads it (Nasdaq quote and levels per ticker, earnings calendar, news) at https://getchord.xyz/ask.
