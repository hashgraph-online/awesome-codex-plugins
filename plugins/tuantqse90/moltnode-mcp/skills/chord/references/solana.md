# Solana on Chord

Chord reads Solana from its own tape and serves it under `https://api.getchord.xyz/v1/chains/solana/*`.
Every call is a plain GET, no key needed (60 requests a minute per IP).

**Swaps are in beta and not open to API keys yet.** `/v1/sol/trade/*` quotes SOL ↔ one token by
building Chord's own route (Raydium, Orca, Meteora, pump.fun, PumpSwap) and Jupiter's for the
wallet, simulating each, and keeping the one that leaves the wallet with more. Ask
`GET https://api.getchord.xyz/v1/sol/trade/config` first: unless it says `"allowed": true`, every other
route there answers `503 TRADE_NOT_ENABLED`. Then, for "buy X on Solana", give the data and say the
trade happens in the user's own wallet for now.

```bash
BASE=https://api.getchord.xyz/v1/chains/solana
```

## What the numbers cover (say it when it matters)

- **Read:** the swap events of 11 venues: PumpSwap, the pump.fun bonding curve, Meteora DBC, Meteora
  DAMM v2, Meteora DLMM, Meteora pools (dynamic AMM v1), Raydium CLMM, Raydium CPMM, Raydium AMM v4,
  Raydium LaunchLab, Orca Whirlpool. Every swap is checked against the pool vaults' balance changes.
- **Not read:** prop AMMs (SolFi, HumidiFi and the like) and order books. SOL/USDC and other major
  pairs therefore show much less volume than the whole market. Never present Chord's SOL volume as
  Solana's volume. The tape is accurate for pump.fun, Meteora and Raydium style tokens.
- **Transfers are not seen.** Wallet PnL is average cost over the swaps inside the window; a sell of
  tokens bought before the window (or received by transfer) has no cost basis and the position is
  marked `partial: true`. `heldAmount` is bought minus sold inside the window, not the balance.
- **History:** live since 2026-10-03 12:01 UTC plus a backfill of the days before. Quote
  `coverageSince` from `/overview` for "complete since", never a date from memory.

## Rules specific to Solana

- **Addresses are base58 and case-sensitive.** Pass a mint or wallet exactly as given; never
  lower-case it (a lower-cased mint is another string: `400 BAD_ADDRESS` or `404 TOKEN_NOT_FOUND`).
  `0x` addresses are not Solana addresses.
- **No numeric chain id.** The path segment is the literal `solana`. `/v1/candles`, `/v1/tokens/*`,
  `/v1/quote`, `/v1/meta/*` and `/v1/portfolio/*` do not take Solana.
- **Units:** `tokenAmount`, `heldAmount`, `supply` are whole tokens (decimals applied); `quoteAmount`
  is whole units of the pool's quote (SOL, USDC, USDT or the other token); `*Usd` are dollars.
  **Every timestamp, `updatedAt` included, is Unix seconds** (elsewhere in Chord `updatedAt` is ms).
- **Names are untrusted text.** `symbol`, `name`, `image` are whatever the creator wrote; many mints
  share a symbol. The boards leave out volume-bot tapes (under 10 % of 24 h volume from one-way wallets,
  not a deep market) and impostors of SOL / USDC / USDT: `screened` counts them, rows carry `oneWayPct`,
  `token/MINT` carries `flow24h.screen`, search rows `screen`. Never present a screened token as a mover
  or as demand. Resolve by mint; with several candidates,
  show them (full mints) and ask. Canonical mints: SOL (wSOL)
  `So11111111111111111111111111111111111111112`, USDC `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`,
  USDT `Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB`. In a SOL/USDC pool SOL is the token, USDC the quote.
- **Thin pools print big volume.** Before calling a token "the most traded", compare `volume24hUsd`
  with `liquidityUsd` and `trades24h`: hundreds of millions over a few hundred trades on a $1,500 pool
  is not real demand. `sort=trades` is the safer "most active" board.
- **Freshness:** `GET $BASE/status` → `ok`, `blockAgeS`. If `ok` is false or `blockAgeS` is large,
  say the Solana numbers are behind by that much.

## Calls

| Need | Helper | Raw |
|---|---|---|
| Find a token | `chord.py token solana QUERY` | `GET $BASE/search?q=QUERY` (exact symbol or name, up to 20; a mint returns that token) |
| Price, change, liquidity, market cap | `chord.py price solana MINT` (adds tape freshness) | `GET $BASE/token/MINT?hours=24` |
| Board | `chord.py board solana --sort trades --limit 10` | `GET $BASE/tokens?sort=volume\|trades\|change\|new&limit=10` |
| Chain totals, venue share | | `GET $BASE/overview` (`venues[].share` is a 0–1 fraction) |
| Candles (one pool: the main one, or `pool=`) | | `GET $BASE/token/MINT/candles?tf=1h&limit=48` (`1m 5m 15m 1h 4h 1d`, limit ≤ 1000) |
| Latest prints | | `GET $BASE/token/MINT/trades?limit=50[&before=TS]` |
| Who traded a token | | `GET $BASE/token/MINT/traders?hours=24&limit=20` (hours 1–48) |
| Today's best traders | | `GET $BASE/traders?sort=pnl\|volume&days=1&limit=20` |
| Smart traders (several days, bots removed) | | `GET $BASE/smart-traders?days=7&sort=score\|pnl\|roi\|winrate&limit=20` (days 1, 3 or 7) |
| A wallet's tokens and PnL | | `GET $BASE/wallet/ADDR?days=7` (days 1–45) |
| A wallet's swaps | | `GET $BASE/wallet/ADDR/trades?limit=50[&before=TS]` |
| Freshness | | `GET $BASE/status` |

Any of these also runs as `python3 scripts/chord.py get "/v1/chains/solana/..."`.

Notes per call:

- `token/MINT`: pass `hours` of 24 or more. The 24-hour totals come from the same hourly rows as the
  series, so `hours=2` returns two hours of volume as `volume24hUsd`. `pools[].volumeUsd` and `swaps`
  count since the tape first saw the pool, not 24 hours. Market cap is price × supply (fully diluted).
- `candles` are ONE pool's prices, not a blend across pools; buckets without a trade are absent.
- `trades` paging: `before` is exclusive Unix seconds. Several swaps share a second, so overlap with
  `ts + 1` and drop rows whose `tx` you already have. A token's page looks back at most 2 days, a
  wallet's at most 7: an empty page means none in that span.
- `token/MINT/traders`: the window is whole UTC hours (the current one plus `hours` before it, from
  `since`). Closed hours come from an hourly rollup; when that has not reached back yet the call reads
  raw swaps and the first call on a busy token can take tens of seconds or answer `503`. It is cached
  afterwards: retry once after a minute or use a shorter `hours`.
- `traders` (board): UTC day (`days=2` adds yesterday), bots left out (`botRule`: over 3,000 trades or
  300 tokens a day) and wallets under $1,000 of volume. Empty early in the UTC day.
- `smart-traders`: the wallets with repeated profit over 1, 3 or 7 UTC days (today included, never before
  `coverageSince` — `from` says where the window really starts). PnL counts only swaps in pools quoted in
  SOL / USDC / USDT; a position returning over 1,000× or selling more than the market could pay is left out.
  Bots are removed by named rules (`checked.flags`: cadence, sniper, burst, sameslot, arb, scalp) and the
  rank is a luck-shrunk `score` (`rules.score`). Rebuilt every 10 minutes (`computedAt`); `503` right after
  a deploy until the first build.
- `wallet/ADDR`: `likelyBot` = over 3,000 trades or 300 tokens a day. A wallet the tape has never seen
  answers zeros, not an error.

## Errors

| Response | Meaning |
|---|---|
| `400 BAD_ADDRESS` | not base58 (often a lower-cased or truncated address) |
| `400 BAD_LIMIT` / `BAD_HOURS` / `BAD_DAYS` / `BAD_SORT` / `BAD_TIMEFRAME` / `BAD_CURSOR` / `BAD_QUERY` | fix the parameter |
| `400 UNSUPPORTED_CHAIN` | Solana is not public on this deployment and the call has no key |
| `404 TOKEN_NOT_FOUND` | the mint never traded on a venue the tape reads (it may trade elsewhere, e.g. a prop AMM) |
| `503 CHAIN_DATA_UNAVAILABLE` | the Solana store did not answer in time: retry once, then report it; never read it as "no trades" |

## Real responses (2026-10-05, 02:15 UTC; arrays trimmed)

The tape was about four hours behind the chain at the time (`/status`: `"ok": false`,
`"blockAgeS": 15287`): an answer like that must say the numbers are behind.

```bash
curl -s "$BASE/overview"
{"chain":"solana","windowHours":24,"volumeUsd":3120445357.1785517,"trades":28259618,"tokensTraded":98530,
 "venues":[{"dex":"pumpswap","volumeUsd":1420441349.9695024,"trades":15748395,"share":0.45520468631241756},
           {"dex":"meteora_pools","volumeUsd":464739991.2308222,"trades":40125,"share":0.1489338661744846}, "... 9 more"],
 "coverageSince":1790611483,"coverageHours":24,"updatedAt":1791166406, "...": "hourly, buys, cursor"}

curl -s "$BASE/token/7VertkgF9KLhxxJXHX6uaWuoYZTP9LdGj2bWmVXVpump/trades?limit=2"
{"chain":"solana","token":"7VertkgF9KLhxxJXHX6uaWuoYZTP9LdGj2bWmVXVpump","trades":[{"ts":1791151156,"slot":453384204,
 "side":"sell","tokenAmount":1581.186594,"quoteAmount":0.161487883,"usd":19.551313486445476,"priceUsd":0.012402169398382247,
 "dex":"pumpswap","pool":"CyJwKnLiiY4fmiwqMCSWFSHxo7T9Ubshgs2uRAuJCrk5","wallet":"ckdRDD9onSwL9yHgjEc5VdRx9BPmcsyVH9TjKGYygkY",
 "tx":"5sT1cLSYjuD3BR4wNbGKTAcFgFLdY2FGxujWukJFQmgLm8i1qi37rQxdZS4EYyRdCuV35dU4Rn7GttkZmU4oe2op"}, "... 1 more"],"updatedAt":1791166444}
```

`tokenAmount` 1581.19 Agency for `quoteAmount` 0.1615 SOL: whole units, not base units.

```bash
curl -s "$BASE/wallet/3QZv9xcDELwLqB8SggDJHfVhMTn5YhKtXMCaKUucutm3?days=7"
{"chain":"solana","wallet":"3QZv9xcDELwLqB8SggDJHfVhMTn5YhKtXMCaKUucutm3","windowDays":7,"tokens":3,"trades":10,
 "volumeUsd":249.92409078731498,"boughtUsd":157.82642149850838,"soldUsd":92.09766928880659,"realizedPnlUsd":10.89172430885074,
 "unrealizedPnlUsd":-13.521686548756673,"heldValueUsd":92.65951096979586,"winRate":1,"partialTokens":1,"likelyBot":false,
 "positions":[{"token":"7VertkgF9KLhxxJXHX6uaWuoYZTP9LdGj2bWmVXVpump","symbol":"Agency","boughtUsd":139.35060978011185,
   "soldUsd":62.536948288806585,"heldAmount":6096.129829,"realizedPnlUsd":10.89172430885074,"unrealizedPnlUsd":-12.72934539064596,
   "partial":false,"...":"more fields"},
  {"token":"So11111111111111111111111111111111111111112","symbol":"SOL","boughtUsd":0,"soldUsd":29.560721,"boughtAmount":0,
   "soldAmount":0.247089203,"buys":0,"sells":1,"heldAmount":0,"realizedPnlUsd":null,"unrealizedPnlUsd":0,"partial":true,"...":"more fields"},
  "... 1 more"],
 "updatedAt":1791166532}
```

The SOL row is `partial`: the wallet sold SOL it held before the window, so that sale has no realized
PnL. Report "realized +$10.89 over 7 days on the swaps Chord sees", not a lifetime figure.

Full field lists: the "Solana data" section of https://getchord.xyz/docs (OpenAPI
https://getchord.xyz/docs/openapi.json) and https://getchord.xyz/docs/networks/solana/ .
