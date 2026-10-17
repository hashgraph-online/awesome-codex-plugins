# Examples (real responses)

Every call below was run against `https://api.getchord.xyz` on 2026-10-02 around 20:20 UTC (a Friday,
just after the NYSE close). Responses are trimmed: long arrays keep their first rows and end with a
`"... N more"` marker, long hex strings are shortened with `...`. Numbers are as returned. They are
examples of shape and scale, not current prices: always call the API again.

## A. Worked answers

### A1. "What is the price of NVDA's stock token on Robinhood Chain and its gap to the real stock?"

```bash
python3 scripts/chord.py stock NVDA                 # compact; or:
curl -s https://api.getchord.xyz/v1/rh/stocks      # and take the row with symbol NVDA
```

```json
{
 "address": "0xd0601CE157Db5bdC3162BbaC2a2C8aF5320D9EEC",
 "symbol": "NVDA",
 "name": "NVIDIA \u2022 Robinhood Token",
 "decimals": 18,
 "tags": ["stock"],
 "priceUsd": 234.12252662208834,
 "change24hPct": 1.1325502230818296,
 "volume24h": 31174659.47870438,
 "trades24h": 59262,
 "traders": 6375,
 "liquidityUsd": 6948448,
 "navUsd": 234.1,
 "navSource": "xyz-perp",
 "basisPct": 0.009622649332907685,
 "offHours7d": {"volUsd": 120490605.96319114, "trades": 231609, "sharePct": 57.80322500654304}
}
```

Answer shape:

> **NVDA stock token, Robinhood Chain (4663)**: $234.12 (24h +1.13 %), from Chord's index of
> on-chain trades. Reference price $234.10 (`navSource: xyz-perp`, the trade.xyz perpetual's mark on
> Hyperliquid, which tracks the share around the clock); the token trades +0.01 % against it.
> 24h volume $31.2M; 57.8 % of the last 7 days' volume traded outside NYSE hours.
> The token tracks the share; it is not the share itself. Chord does not serve the exchange's own
> quote: for that, ask Chord Ask or a market data site.
> Follow-ups: the 48-hour chart of the token? A quote in USDG?

### A2. "Quote 50 USDC to AERO on Base"

```bash
python3 scripts/chord.py quote base USDC AERO 50
```

```json
{
 "chain": {"id": 8453, "name": "Base", "gasToken": "ETH"},
 "sell": {"symbol": "USDC", "address": "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913", "decimals": 6, "amount": "50", "amountRaw": "50000000"},
 "buy": {"symbol": "AERO", "address": "0x940181a94a35a4569e4529a3cdfb74e38fd98631", "decimals": 18},
 "noRoute": false,
 "expectedOutGross": "64.306788963640761322",
 "fee": {"bps": 5, "amount": "0.03215339448182038", "token": "AERO"},
 "expectedOutAfterFee": "64.274635569158940942",
 "minimumReceived": "63.953262391313146238",
 "slippageBps": 50,
 "priceImpactPct": "0.0000",
 "valueLossPct": -0.17,
 "route": [
   {"dex": "aerodrome_slipstream_3", "percent": 100, "pool": "0x4e392fbfe4d0557c82d2f97f02ec39daa31516dd"},
   {"dex": "aerodrome_slipstream_3", "percent": 100, "pool": "0x4e506648d493c8870f55e870480f92f2f33ece51"}
  ],
 "router": "0x1b1fee89a381e595fe6536b99ba91f3e16e9601a",
 "approvalNeeded": true,
 "blockNumber": 52091636,
 "warnings": [],
 "quotedAt": 1790972626,
 "quoteFile": "/tmp/chord-quote-8453-1790972626.json"
}
```

Message to the user (then stop and wait):

| Field | Value |
|---|---|
| Action | Swap: sell USDC for AERO (quote only so far) |
| Chain | Base (8453); gas in ETH |
| You sell | 50 USDC `0x833589fcd6edb6e08f4c7c32d4f71b54bda02913` |
| You receive (estimate, after fee) | 64.27463 AERO `0x940181a94a35a4569e4529a3cdfb74e38fd98631` |
| Minimum received | 63.95326 AERO at 0.5 % slippage |
| Price impact / value loss | 0.00 % / -0.17 % |
| Chord fee | 5 bps (0.0321 AERO) |
| Route | aerodrome_slipstream_3, two hops |
| Router (`to`, approval spender) | `0x1B1Fee89A381E595Fe6536b99Ba91F3E16e9601a` |
| Approval | approve exactly 50 USDC to the router first |

> Reply **confirm** with your wallet address to build the unsigned transaction for your wallet to
> sign, or **cancel**.

If the user only asked for a quote, end with the quote and a follow-up ("Want me to prepare the
transaction?") instead of the confirm line.

### A3. "Which tokens on Arc traded the most in the last 24h?"

```bash
python3 scripts/chord.py board arc --limit 10        # compact; or:
curl -s "https://api.getchord.xyz/v1/arc/tokens?sort=volume&limit=10"
```

```json
{
 "chain": 5042,
 "sinceHour": 1790888400,
 "sort": "volume",
 "total": 1469,
 "updatedAt": 1790972525669,
 "tokens": [
   {
    "address": "0x171a4217b86a807a64eb94757db6849fb4bdbaa0",
    "symbol": "cirBTC",
    "name": "cirBTC",
    "listed": true,
    "priceUsd": 84352.34348771402,
    "change24hPct": -0.33231779595271904,
    "volume24h": 8810169.251741001,
    "trades24h": 27666,
    "traders": 3268,
    "marketCapUsd": 434343258.89922684
   },
   {
    "address": "0x128cc466b61f542da60c70e3aa11c10e19b84edb",
    "symbol": "WETH",
    "name": "Wrapped Ether",
    "listed": true,
    "priceUsd": 2667.372923701913,
    "change24hPct": -1.0656785461005014,
    "volume24h": 1744722.9605400001,
    "trades24h": 6960,
    "traders": 705,
    "marketCapUsd": 15868984.370089365
   },
   {
    "address": "0xece5ca8bf9220718e5727754026757512212cb3c",
    "symbol": "ARGUS",
    "name": "Argus",
    "listed": true,
    "priceUsd": 0.015819461924536954,
    "change24hPct": 14.834691179027804,
    "volume24h": 961902.3118469998,
    "trades24h": 5433,
    "traders": 2183,
    "marketCapUsd": 15819461.924536955
   },
   "... 7 more"
  ]
}
```

Answer shape (all ten rows came back clean, no `flags`):

| # | Token | Address | 24h volume | Trades | Price | 24h |
|---|---|---|---|---|---|---|
| 1 | cirBTC | `0x171a4217b86a807a64eb94757db6849fb4bdbaa0` | $8,810,169 | 27,666 | $84352.3 | -0.3 % |
| 2 | WETH | `0x128cc466b61f542da60c70e3aa11c10e19b84edb` | $1,744,723 | 6,960 | $2667.37 | -1.1 % |
| 3 | ARGUS | `0xece5ca8bf9220718e5727754026757512212cb3c` | $961,902 | 5,433 | $0.0158195 | +14.8 % |
| 4 | EURC | `0xbef5f6d51cb62b58e6a8f77868681825c6fe21c1` | $950,830 | 8,567 | $1.12523 | +0.1 % |
| 5 | SI | `0x2f1a737aad9feccb9dc37a4d2fc1bab013667d7a` | $181,210 | 11,578 | $2.46277e-06 | -94.4 % |
| 6 | ARCMAN | `0x5849fd68a097b3ee7d87ce88a0fcbb76857648ff` | $178,523 | 6,604 | $0.0138206 | +7.4 % |
| 7 | TOLLY | `0xbc43ce8dec648ea298c4275559b81d6261c90b67` | $168,005 | 3,334 | $0.00408554 | +12.0 % |
| 8 | JEANUSDC | `0x31229e953d133fdc1cd77c76df8ddcc4c4514c86` | $160,957 | 5,242 | $0.000102156 | -48.6 % |
| 9 | EXIT | `0x7036e5bc60c12588c7a6a0756823f1ed5e6e24e4` | $130,253 | 5,384 | $0.00287123 | -3.7 % |
| 10 | COTC | `0x12c1b03a6c38dee58d5d94beb276c39e907d11aa` | $128,253 | 1,030 | $2.69799e-06 | -83.6 % |

> Arc (5042), Chord's index, 24h to 20:22 UTC. Volume is USD across every venue. JEANUSDC is a memecoin, not
> USDC. Follow-ups: the 2-hour movers (`/v1/arc/trending`)? Holders of ARGUS?

## B. Safety and refusals

### B1. Same ticker, several tokens

```bash
python3 scripts/chord.py quote robinhood USDG GME 10      # exit code 3
```

```json
{
 "error": "AMBIGUOUS",
 "role": "tokenOut",
 "chain": 4663,
 "query": "GME",
 "message": "Several tokens share this symbol. Show the user the can... 0x address.",
 "candidates": [
   {"symbol": "GME", "name": "GameStop \u2022 Robinhood Token", "address": "0x1b0E319c6A659F002271B69dB8A7df2F911c153E", "tags": ["stock"]},
   {"symbol": "GME", "name": "GameStop", "address": "0x7e86381A763F0Ecca2bDF27C54eAC403ddD48123", "tags": ["meme"]},
   {"symbol": "GME", "name": "GameStop", "address": "0xc2362aff2a2a4cc1f48cf3dab2c4e2605eb94ba3", "tags": ["meme"]},
   "... 1 more"
  ]
}
```

Ask which one; the `stock` row is the GameStop stock token, the `meme` rows are unrelated coins.

### B2. A "USDT" at the wrong address

```bash
curl -s "https://api.getchord.xyz/v1/chains/bnb/token/0x1234567890abcdef1234567890abcdef12345678/ref-price"
{"error":"NOT_LISTED","message":"CoinGecko does not list this token on this chain"}
curl -s "https://api.getchord.xyz/v1/chains/bnb/token/0x55d398326f99059ff775485246999027b3197955/ref-price"
{"chain":56,"address":"0x55d398326f99059ff775485246999027b3197955","priceUsd":0.999916,"change24hPct":0.03,"source":"coingecko","ageS":0}
```

The first address is not Tether's USDT on BNB Chain; the canonical one is `0x55d3...7955` (18 decimals).

### B3. Unsupported chain, Solana swap, too many decimals

```bash
python3 scripts/chord.py quote optimism USDC WETH 1
{"error": "unsupported chain 'optimism'. Chord covers: Monad (143), Robinhood Chain (4663), Arc (5042), Avalanche (43114), Base (8453), BNB Chain (56), Arbitrum One (42161), Ethereum (1), plus Solana data (read-only). It does not cover Optimism, Polygon or other chains."}
python3 scripts/chord.py quote solana USDC SOL 1
{"error": "Solana is read-only in Chord: use 'token solana QUERY', 'price solana MINT', 'board solana' or 'get /v1/chains/solana/...'. Chord does not quote, route or build Solana swaps."}
python3 scripts/chord.py quote bnb USDT CAKE 10.1234567890123456789
{"error": "amount '10.1234567890123456789' has 19 decimal places; this token has 18. Ask the user, do not round silently."}
```

### B4. Building without the user's yes

```bash
python3 scripts/chord.py swap-tx /tmp/chord-quote-8453-1790972626.json 0xUSER
{"error": "refused: show the user the quote summary and wait for their explicit yes in a new message, then re-run with --user-confirmed. Never pass this flag on the user's behalf."}
```

### B5. After the user replied "confirm" in a new message

```bash
python3 scripts/chord.py swap-tx /tmp/chord-quote-8453-1790972626.json 0x000000000000000000000000000000000000dEaD --user-confirmed
```

```json
{
 "unsigned": true,
 "chain": {"id": 8453, "name": "Base", "gasToken": "ETH"},
 "from": "0x000000000000000000000000000000000000dEaD",
 "transaction": {
   "to": "0x1B1Fee89A381E595Fe6536b99Ba91F3E16e9601a",
   "data": "0x9287687c0000000000000000...(2,250 hex chars)",
   "value": "0",
   "gasLimit": "1500000",
   "chainId": 8453
  },
 "summary": "... (sell, buy, expectedOutAfterFee, minimumReceived, priceImpactPct, route as in A2)",
 "approval": {
   "token": "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
   "spender": "0x1B1Fee89A381E595Fe6536b99Ba91F3E16e9601a",
   "amountRaw": "50000000",
   "note": "Approve exactly this amount (not unlimited) before the swap, or the swap reverts."
  },
 "problems": [],
 "next": "Hand this to the user's own wallet to review and sign. Chord and this script never sign or broadcast."
}
```

```bash
python3 scripts/chord.py simulate /tmp/chord-quote-8453-1790972626.json 0x000000000000000000000000000000000000dEaD
{"chain": 8453, "from": "0x000000000000000000000000000000000000dEaD", "simulation": {"ok": false, "revert": "Router is not approved to spend the input token yet \u2014 the card approves first, then swaps.", "selector": "0x7939f424"}}
```

The simulation fails until the approval is sent: expected. Hand both transactions (approve, then
swap) to the user's wallet; say they are unsigned and not sent.

## C. Raw quote and swap

```bash
curl -s "https://api.getchord.xyz/v1/quote?chain=8453&inputMint=0x833589fcd6edb6e08f4c7c32d4f71b54bda02913&outputMint=0x940181a94a35a4569e4529a3cdfb74e38fd98631&amount=50000000&slippageBps=50"
```

```json
{
 "inputMint": "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
 "outputMint": "0x940181a94a35a4569e4529a3cdfb74e38fd98631",
 "inputAmount": "50000000",
 "outputAmount": "64388335644909640188",
 "otherAmountThreshold": "64034360769701749442",
 "slippageBps": 50,
 "priceImpactPct": "0.0000",
 "routePlan": [
   {
    "percent": 100,
    "swapInfo": {
      "dex": "pancake_v3",
      "pool": "0x72ab388e2e2f6facef59e3c3fa2c4e29011c2d38",
      "inputMint": "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
      "outputMint": "0x4200000000000000000000000000000000000006",
      "inputAmount": "50000000",
      "outputAmount": "18745505847564571",
      "adapter": "0xd55fe37e30435cF15fe2C7fcAAF1aBf19d13b195",
      "extraData": "0x00000000000000000000000072ab388e2e2f6facef59e3c3fa2c4e29011c2d38"
     }
   },
   "... 1 more"
  ],
 "gasEstimate": "400000",
 "gasCostUSD": "0",
 "blockNumber": 52091618,
 "timeTaken": 0.481,
 "feeBps": 5,
 "feeAmount": "32194167822454820",
 "feeMint": "0x940181a94a35a4569e4529a3cdfb74e38fd98631",
 "feeTier": "custom",
 "valueLossPct": -0.3
}
```

`outputAmount` is before the fee; the user receives `outputAmount - feeAmount`, at least
`otherAmountThreshold`. `POST /v1/swap` with `{"quoteResponse": <this>, "userPublicKey": "0x...", "slippageBps": 50, "chain": 8453}`
returns `{"transaction": {"to": "0x1B1Fee89A381E595Fe6536b99Ba91F3E16e9601a", "data": "0x...", "value": "0", "gasLimit": "1500000", "chainId": 8453}, "lastValidBlockHeight": 0}`.

## D. Data endpoints

### D1. Curated token list (Base)

```bash
curl -s "https://api.getchord.xyz/v1/tokens?chain=8453"
```

```json
{
 "tokens": [
   {"address": "0x4d5cb527bd9d87c727b6dbe01114adc086e646a2", "symbol": "RX", "name": "ReachX Mainnet", "decimals": 18, "tags": []},
   {"address": "0x2f85d372bef829e866f8917378ff20a88e7fc403", "symbol": "$COOL", "name": "CoolCoin", "decimals": 10, "tags": []},
   "... 524 more"
  ]
}
```

### D2. Arc search

```bash
curl -s "https://api.getchord.xyz/v1/arc/tokens/search?q=argus&limit=5"
```

```json
{
 "chain": 5042,
 "q": "argus",
 "total": 64,
 "coverage": {"resolved": 4331, "total": 4331},
 "tokens": [
   {
    "address": "0xece5ca8bf9220718e5727754026757512212cb3c",
    "symbol": "ARGUS",
    "name": "Argus",
    "listed": true,
    "priceUsd": 0.016075519994272883,
    "volume24h": 961275.2524569997
   },
   {
    "address": "0x7b959dd14657bf0a062270a6b277801c14a4e322",
    "symbol": "ARGUS",
    "name": "argus",
    "listed": true,
    "priceUsd": 2.987664183612997e-06,
    "volume24h": 165.0993322931831
   },
   "... 3 more"
  ]
}
```

Two tokens answer to ARGUS: the listed one with $961k of volume and a same-named copy with $165. Show the address of the one you mean.

### D3. Robinhood Chain price map (filter by address)

```bash
curl -s "https://api.getchord.xyz/v1/tokens/market?chain=4663"
```

```json
{
 "market": {
   "0xd0601ce157db5bdc3162bbac2a2c8af5320d9eec": {
     "priceUsd": 234.12252662208834,
     "change24h": 1.13,
     "volume24h": 31262984,
     "txns24h": 59376,
     "liquidityUsd": 6948448,
     "spark": [231.14771595046804, 231.63948149418846, 231.71645966631812, "... 21 more"]
    },
   "...": "3758 more addresses"
  },
 "updatedAt": 1790972514024
}
```

Thousands of rows: look up the resolved lower-case address, never dump the map.

### D4. Monad price map (filter by address)

```bash
curl -s "https://api.getchord.xyz/v1/tokens/market?chain=143"
```

```json
{
 "market": {
   "0x3bd359c1119da7da1d913d1c4d2b7c461115433a": {"priceUsd": 0.032477572393044954, "change24h": -4.102829782194771, "volume24h": 8531940},
   "...": "169 more addresses"
  }
}
```

### D5. One Arc token

```bash
curl -s "https://api.getchord.xyz/v1/arc/token/0xece5ca8bf9220718e5727754026757512212cb3c?hours=24"
```

```json
{
 "chain": 5042,
 "hours": 24,
 "updatedAt": 1790972519134,
 "token": {
   "address": "0xece5ca8bf9220718e5727754026757512212cb3c",
   "symbol": "ARGUS",
   "name": "Argus",
   "decimals": 18,
   "listed": true,
   "priceUsd": 0.015819461924536954,
   "change24hPct": 14.834691179027804,
   "volume24h": 961902.3118469998,
   "trades24h": 5433,
   "traders": 2183,
   "marketCapUsd": 15819461.924536955,
   "routable": true
  },
 "series": [
   {
    "hour": 1790888400,
    "volUsd": 13635.575575,
    "buyUsd": 8999.218913,
    "sellUsd": 4636.356662,
    "trades": 121,
    "buys": 43,
    "sells": 78,
    "priceLast": 0.014111740620829422
   },
   "... 23 more"
  ],
 "byDex": [{"dex": "uniswap_v4", "volUsd": 748044.7017059998, "trades": 3235, "sharePct": 77.82555171253661}, "... 4 more"]
}
```

### D6. One Base token

```bash
curl -s "https://api.getchord.xyz/v1/chains/base/token/0x940181a94a35a4569e4529a3cdfb74e38fd98631?hours=24"
```

```json
{
 "chain": 8453,
 "token": {"address": "0x940181a94a35a4569e4529a3cdfb74e38fd98631", "symbol": "AERO", "name": "Aerodrome", "decimals": 18, "logoURI": null},
 "hours": 24,
 "stats24h": {
   "volUsd": 11659808.65965602,
   "buyUsd": 6034445.651880765,
   "sellUsd": 5625363.0077752555,
   "trades": 52581,
   "buys": 18149,
   "sells": 34432,
   "lastTs": 1790972075,
   "dominantDex": "aerodrome_v2",
   "priceUsd": 0.7660377547997806,
   "priceThen": 0.7724317956142199,
   "change24hPct": -0.8277806339334948,
   "sinceHour": 1790888400
  },
 "coverage": {"recentAt": 1790972101, "stale": false},
 "updatedAt": 1790972520698,
 "series": [
   {
    "hour": 1790888400,
    "volUsd": 223434.07760241575,
    "buyUsd": 65720.95217940398,
    "sellUsd": 157713.1254230116,
    "trades": 1393,
    "buys": 316,
    "sells": 1077,
    "priceLast": 0.7857493175845156
   },
   "... 23 more"
  ],
 "byDex": [
   {"dex": "aerodrome_v2", "volUsd": 3985141.7470603636, "trades": 7566, "sharePct": 34.17844892128728},
   {"dex": "aerodrome_slipstream_3", "volUsd": 3580078.546346505, "trades": 4020, "sharePct": 30.704436503610022},
   "... 20 more"
  ]
}
```

### D7. CoinGecko reference price (Base)

```bash
curl -s "https://api.getchord.xyz/v1/chains/base/token/0x940181a94a35a4569e4529a3cdfb74e38fd98631/ref-price"
```

```json
{
 "chain": 8453,
 "address": "0x940181a94a35a4569e4529a3cdfb74e38fd98631",
 "priceUsd": 0.775027,
 "change24hPct": -1.63,
 "source": "coingecko",
 "ageS": 0
}
```

CoinGecko's price for the same contract: a cross-check, not Chord's index.

### D8. Candles

```bash
curl -s "https://api.getchord.xyz/v1/candles?chain=8453&token=0x940181a94a35a4569e4529a3cdfb74e38fd98631&tf=1h&limit=24"
```

```json
{
 "chain": 8453,
 "token": "0x940181a94a35a4569e4529a3cdfb74e38fd98631",
 "tf": "1h",
 "source": "index",
 "from": 1790888400,
 "to": 1790974800,
 "forming": true,
 "candles": [
   {"t": 1790888400, "o": 0.7860416934459864, "h": 0.7860417117243488, "l": 0.7814081161198063, "c": 0.7814116641885517, "v": 60432.69, "n": 201},
   {"t": 1790892000, "o": 0.7862782470393389, "h": 0.794620943103556, "l": 0.7824455999508125, "c": 0.789425117685149, "v": 117437.94, "n": 220},
   "... 22 more"
  ]
}
```

### D9. Robinhood Chain board

```bash
curl -s "https://api.getchord.xyz/v1/rh/tokens?sort=volume&limit=10"
```

```json
{
 "chain": 4663,
 "sort": "volume",
 "total": 430,
 "updatedAt": 1790972527213,
 "tokens": [
   {
    "address": "0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73",
    "symbol": "WETH",
    "name": "WETH",
    "tags": ["bridged"],
    "priceUsd": 2667.3010748022007,
    "change24hPct": -1.13001138003328,
    "volume24h": 552073022.1722026,
    "trades24h": 426372,
    "traders": 40688
   },
   {
    "address": "0xd0601CE157Db5bdC3162BbaC2a2C8aF5320D9EEC",
    "symbol": "NVDA",
    "name": "NVIDIA \u2022 Robinhood Token",
    "tags": ["stock"],
    "priceUsd": 234.11959615741412,
    "change24hPct": 1.131284367249319,
    "volume24h": 31174659.47870438,
    "trades24h": 59262,
    "traders": 6375
   },
   "... 8 more"
  ]
}
```

### D10. Base board

```bash
curl -s "https://api.getchord.xyz/v1/chains/base/tokens?sort=volume&limit=10"
```

```json
{
 "chain": 8453,
 "sort": "volume",
 "total": 8842,
 "coverage": {"recentAt": 1790972101, "stale": false},
 "updatedAt": 1790972528762,
 "tokens": [
   {
    "address": "0x4200000000000000000000000000000000000006",
    "symbol": "WETH",
    "priceUsd": 2667.0895941123554,
    "change24hPct": -1.1596746711006856,
    "volume24h": 369574321.23158294,
    "trades24h": 289704,
    "dominantDex": "uniswap_v3"
   },
   {
    "address": "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf",
    "symbol": "cbBTC",
    "priceUsd": 84339.60999585968,
    "change24hPct": -0.3228823640731626,
    "volume24h": 282847345.52659637,
    "trades24h": 170709,
    "dominantDex": "aerodrome_slipstream_3"
   },
   "... 8 more"
  ]
}
```

### D11. Arc movers (2-hour score)

```bash
curl -s "https://api.getchord.xyz/v1/arc/trending?limit=10"
```

```json
{
 "chain": 5042,
 "window": "2h",
 "updatedAt": 1790972530361,
 "tokens": [
   {
    "address": "0x6299980df0e66f65c16ea8f45cbc732a20c96070",
    "symbol": "NOAH",
    "priceUsd": 2.4890983839844824e-06,
    "change24hPct": -76.85751742152091,
    "volume24h": 81260.65288699989,
    "trades24h": 6494,
    "score": 13.78
   },
   "... 9 more"
  ]
}
```

### D12. Chain overview (Base)

```bash
curl -s "https://api.getchord.xyz/v1/chains/base/overview"
```

```json
{
 "chain": 8453,
 "last24h": {"volUsd": 1207045295.2029176, "swaps": 2079863, "tokens": 8867, "venues": 143, "sinceHour": 1790888400},
 "wallets": {"day": 1790899200, "today": 74727, "yesterday": 84242},
 "updatedAt": 1790972535119,
 "venues24h": [
   {"dex": "aerodrome_slipstream_3", "volUsd": 421932009.05195147, "trades": 329240, "tokens": 193, "sharePct": 34.955772639917384},
   {"dex": "uniswap_v3", "volUsd": 420933127.31327665, "trades": 850834, "tokens": 1604, "sharePct": 34.873018352017446},
   "... 141 more"
  ]
}
```

### D13. Freshness (Base)

```bash
curl -s "https://api.getchord.xyz/v1/chains/base/status"
```

```json
{
 "chain": 8453,
 "enabled": true,
 "tape": true,
 "public": true,
 "recentAt": 1790972101,
 "staleSec": 437,
 "floorHour": 1790175600,
 "genesisHour": null,
 "backfillComplete": true,
 "retentionCutoffDay": 1790640000,
 "ingestFloor": {"minTradeUsd": 0, "history": []},
 "updatedAt": 1790972538233
}
```

### D14. Holders (Arc)

```bash
curl -s "https://api.getchord.xyz/v1/arc/token/0xece5ca8bf9220718e5727754026757512212cb3c/holders?limit=20"
```

```json
{
 "chain": 5042,
 "token": "0xece5ca8bf9220718e5727754026757512212cb3c",
 "tracked": true,
 "complete": true,
 "holders": 20843,
 "heldByWalletsPct": 86.6485,
 "concentration": {"top1": 2.97, "top5": 10.46, "top10": 18.52, "top20": 30.67, "top50": 47.49, "top100": 58.74},
 "top": [
   {
    "holder": "0x000000000000000000000000000000000000dead",
    "balance": "70971584741804324012221097",
    "amount": 70971584.741804,
    "sharePct": 7.0971,
    "kind": "burn"
   },
   {
    "holder": "0x8366a39cc670b4001a1121b8f6a443a643e40951",
    "balance": "41564172550978455704852803",
    "amount": 41564172.550978,
    "sharePct": 4.1564,
    "kind": "pool"
   },
   "... 18 more"
  ]
}
```

kind burn = burned supply (0x...dead), not a holder.

### D15. Latest trades (Base)

```bash
curl -s "https://api.getchord.xyz/v1/chains/base/token/0x940181a94a35a4569e4529a3cdfb74e38fd98631/trades?limit=50"
```

```json
{
 "chain": 8453,
 "token": "0x940181a94a35a4569e4529a3cdfb74e38fd98631",
 "nextBefore": "1790972463:52091558:219",
 "trades": [
   {
    "tx": "0x780dfb60b0f717f806f9d1fe9383a5162876f02d779cd2923c31a82fbe7907e0",
    "logIndex": 165,
    "block": 52091601,
    "dex": "uniswap_v3",
    "side": "sell",
    "tokenAmt": 9.510188763606598,
    "usd": 7.380426,
    "priceUsd": 0.7760546276687239,
    "ts": 1790972549,
    "wallet": "0xd05ec60c2ddaaa1f2bb1b03adbb5b3cbb32fa7ae",
    "pool": "0xe5b5f522e98b5a2baae212d4da66b865b781db97"
   },
   "... 49 more"
  ]
}
```

### D16. Arc launches that passed the screens

```bash
curl -s "https://api.getchord.xyz/v1/arc/graduated?hours=24&limit=20"
```

```json
{
 "chain": 5042,
 "hours": 24,
 "total": 3,
 "screened": {"not_routable": 1010, "impostor": 0, "no_sells": 0, "few_traders": 6, "serial_creator": 382, "no_trades": 731, "no_symbol": 0},
 "tokens": [
   {
    "address": "0xa2b9970d18d7cd8ad994110da761b9e967eb5172",
    "symbol": "CHINACOIN",
    "name": "\u56fd\u5e86\u5e01",
    "priceUsd": 5.036267231857139e-06,
    "volume24h": 926.9344749999999,
    "trades24h": 25,
    "traders": 3,
    "launchedAt": 1790918176,
    "launcherName": "TOLLY",
    "creator": "0x516bec88e8e98426ccc614ba4ae47eefe134fc3b"
   },
   "... 2 more"
  ]
}
```

### D17. Smart money (Robinhood Chain, 7 days)

```bash
curl -s "https://api.getchord.xyz/v1/smart-money/top?chain=4663&source=onchain&window=7d&limit=10"
```

```json
{
 "window": "7d",
 "chain": 4663,
 "source": "onchain",
 "totalWallets": 157342,
 "indexedToBlock": 78513680,
 "botsRemoved": {"cadence": 326, "nonceOrDenylist": 0, "behavior": 0},
 "note": "ranked by Smart Score \u2014 skill-adjusted, realized-weighted profit (est. at current prices)",
 "wallets": [
   {
    "wallet": "0x917e5c6c35de36e564a680bc3b6acabd3d7a15c4",
    "pnlUsd": 128110.61616693069,
    "realizedUsd": 56133.92753898777,
    "unrealizedUsd": 71976.68862794292,
    "volumeUsd": 66874.19336149725,
    "trades": 12,
    "winRate": 0.5,
    "topToken": {"symbol": "astro", "pnlUsd": 128757.58042142291},
    "archetype": "degen",
    "smartScore": 60447.19042907635
   },
   "... 9 more"
  ]
}
```

pnlUsd mixes realized and unrealized profit (here more than half is unrealized): quote both parts.

### D18. Wallet PnL (Robinhood Chain)

```bash
curl -s "https://api.getchord.xyz/v1/portfolio/0x681d22c5e615c7a876026ceba3dc36c6dde5b97d/pnl?chain=4663"
```

```json
{
 "realized": -6315.547806268156,
 "unrealized": 7675.9286692203605,
 "total": 1360.3808629522046,
 "updatedAt": 1790972563234,
 "tokens": [
   {
    "token": "0x07ebb29a38fbcb41563817e5e19f2cec619c90d2",
    "symbol": "BUN",
    "realizedUsd": 0,
    "unrealizedUsd": 23953.942176295175,
    "curAmount": 1156358.8958147105,
    "curValue": 78648.23955831614,
    "avgCost": 0.029735862301852874,
    "roiPct": 128.72615176324663,
    "untrackedAmount": 530567.3761916787
   },
   "... 6 more"
  ]
}
```

### D19. Wallet PnL (Base)

```bash
curl -s "https://api.getchord.xyz/v1/chains/base/wallet/0xd05ec60c2ddaaa1f2bb1b03adbb5b3cbb32fa7ae"
```

```json
{
 "chain": 8453,
 "wallet": "0xd05ec60c2ddaaa1f2bb1b03adbb5b3cbb32fa7ae",
 "window": {"fromTs": 1790121600, "toTs": 1790972593, "days": 10},
 "trades": 738,
 "realizedUsd": -2.1630270311521858,
 "unrealizedUsd": -2.766000191638079,
 "totalUsd": -4.929027222790268,
 "volumeUsd": 2209.011398688162,
 "soldWithoutBasisUsd": 141.03987426086283,
 "tokens": [
   {
    "symbol": "MORPHO",
    "buys": 96,
    "sells": 93,
    "realizedUsd": -3.648804033311385,
    "unrealizedUsd": -0.9685817271261072,
    "holdsTokens": 27.131382808261442,
    "avgCostUsd": 2.5860896421659194,
    "lastPriceUsd": 2.5503899605842206
   },
   "... 26 more"
  ]
}
```

### D20. LP pools (Arc)

```bash
curl -s "https://api.getchord.xyz/v1/lp/pools?chain=5042&sort=fee_tvl&limit=10"
```

```json
{
 "chain": 5042,
 "sort": "fee_tvl",
 "interval": "24h",
 "minTvl": 10000,
 "hidden": 2211,
 "total": 100,
 "pools": [
   {
    "pool": "0x6b849ecb360d69a31bb1e972bbe048a32e25c324e4235b1d87911e16d1e857f2",
    "dex": "uniswap_v4",
    "kind": "v4",
    "feeBps": 400,
    "lpAccess": "open",
    "tvlUsd": 10084.06,
    "vol": {"h1": 76.056094, "h6": 804.6717819999999, "h24": 7554.068175, "d7": 142037.00204300004},
    "fees": {"h1": 3.0422437600000003, "h6": 32.18687128, "h24": 302.162727},
    "feeTvlPct": {"h1": 0.030168838344873, "h6": 0.31918563832424635, "h24": 2.9964392020674215},
    "aprPct": 1093.7003087546088,
    "suspect": false,
    "token0": {"address": "0x3600000000000000000000000000000000000000", "symbol": "USDC"},
    "token1": {"address": "0x4c9b47dbd5933aa4574b2c27f82419e4dbbd0222", "symbol": "ASTOCK"}
   },
   "... 9 more"
  ]
}
```

### D21. LP positions of a wallet (Arc)

```bash
curl -s "https://api.getchord.xyz/v1/lp/positions?chain=5042&owner=0x048bd1eeda0d2465255e7d9fa2b30bfe9ec4e0f9&status=open"
```

```json
{
 "chain": 5042,
 "owner": "0x048bd1eeda0d2465255e7d9fa2b30bfe9ec4e0f9",
 "status": "open",
 "summary": {"open": 1, "closed": 0, "wins": 0, "winRatePct": null, "realizedPnlUsd": 0, "feesUsd": 42040.68143034718, "openValueUsd": 62212.1828041179},
 "positions": [
   {
    "pool": "0xd86a9e58d668acc7c13bd547f9fa5cc113ae0083a9fc39f97aab857349ee343d",
    "dex": "uniswap_v4",
    "symbol": "DUKE",
    "anchorSymbol": "USDC",
    "inUsd": 176482.0998002338,
    "valueUsd": 62212.1828041179,
    "feesUsd": 42040.68143034718,
    "pnlUsd": -72229.2355657687,
    "pnlPct": -40.92723038060374,
    "inRange": true,
    "ageHours": 386.57916666666665
   }
  ]
}
```

### D22. Ask status

```bash
curl -s "https://api.getchord.xyz/v1/ask/status"
```

```json
{"enabled": true, "chain": 5042, "guest": true, "privy": true, "budget": {"used": 3294264, "total": 50000000}}
```

### D23. Ask picks

```bash
curl -s "https://api.getchord.xyz/v1/ask/picks"
```

```json
{
 "chain": 5042,
 "computedAt": 1790966695,
 "trackRecord7d": {"graded": 120, "open": 75, "rightWayPct": 36, "avgMovePct": -3.4},
 "picks": [
   {
    "token": "0xf43eb8de897fbc7f2502483b2bef7bb9ea179229",
    "symbol": "ZEN",
    "side": "bearish",
    "score": -6.13,
    "confidence": "high",
    "priceUsd": 6.8972,
    "why": ["sellers 95% of the last hour (978 trades)", "only 19.1% of buying from real wallets", "no volume shelf under the price"],
    "against": ["trading within 8% of the day's VWAP"]
   },
   "... 16 more"
  ]
}
```
