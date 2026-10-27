# Quotes and unsigned swaps

Chord routes a swap across every venue on one chain (splitting the order when that pays more) and
returns either a quote (read-only) or an unsigned transaction against the Chord router. The router
proxy has the same address on every EVM chain below: `0x1B1Fee89A381E595Fe6536b99Ba91F3E16e9601a`.

Chord never signs and never broadcasts. The user's own wallet does both. Building the transaction is
the fund-moving step: it follows the confirmation flow in `SKILL.md`, every time.

## Supported

| Chain | id | Native (zero address) | Gas | Notes |
|---|---|---|---|---|
| Monad | 143 | MON | MON | default of `/v1/quote` when `chain` is missing: always pass `chain` |
| Robinhood Chain | 4663 | ETH | ETH | stock tokens trade against USDG or ETH; fee 0 bps on stocks, USDG and WETH |
| Arc | 5042 | alias for the USDC predeploy `0x3600...0000` (6 decimals) | USDC | native USDC has 18 decimals but the API takes the 6-decimal predeploy; pass `0x3600000000000000000000000000000000000000` and amounts in 6 decimals. USDC input is pulled as the predeploy, so it needs an approval like any ERC-20 |
| Avalanche | 43114 | AVAX | AVAX | USDC vs USDC.e are different tokens |
| Base | 8453 | ETH | ETH | USDC vs USDbC are different tokens |
| BNB Chain | 56 | BNB | BNB | USDT and USDC have 18 decimals |
| Arbitrum One | 42161 | ETH | ETH | USDC vs USDC.e (bridged) are different tokens; USDT0 is the dollar Tether |
| Ethereum | 1 | ETH | ETH | USDT reverts a new approval while an old allowance is left: approve 0 first (`approval.resetFirst`); USDC and USDT 6 decimals, DAI 18 |

Not supported here: Solana swaps (their own family, `/v1/sol/trade/*`, in beta and not open to API
keys yet: `solana.md`), Optimism, Polygon and every other chain; cross-chain swaps; limit orders; perps.

## 0. Meta quote first (Chord's router, a fallback only when it fails)

`GET /v1/meta/quote` and `POST /v1/meta/swap` are the one-call path on all eight chains. Chord's own
router always answers first. A third-party aggregator (KyberSwap on every chain, Monorail on Monad,
LI.FI, Relay) answers ONLY when Chord's router fails: its engine is down or timed out, it has no
route, it refuses the route itself (value guard, taxed token), or its built transaction fails
simulation. A better price elsewhere is never a reason. A user error (unknown token, bad amount)
never falls back.

```bash
python3 scripts/chord.py meta-quote base USDC AERO 50                       # price only, read-only
python3 scripts/chord.py meta-quote monad USDC WMON 25 --wallet 0xYourWallet # + unsigned tx, approval, simulation
python3 scripts/chord.py meta-swap /tmp/chord-meta-8453-....json 0xYourWallet --user-confirmed
```

Raw:

```bash
curl -s "https://api.getchord.xyz/v1/meta/quote?chain=8453&tokenIn=0x833589fcd6edb6e08f4c7c32d4f71b54bda02913&tokenOut=0x4200000000000000000000000000000000000006&amount=10000000&slippageBps=50&taker=0xYourWallet"
curl -s -X POST https://api.getchord.xyz/v1/meta/swap -H 'Content-Type: application/json' \
  -d '{"chain":8453,"tokenIn":"0x8335...2913","tokenOut":"0x4200...0006","amount":"10000000","slippageBps":50,"taker":"0xYourWallet"}'
```

The same shape whichever provider answered:

| Field | Meaning |
|---|---|
| `provider` | `chord`, `kyberswap`, `monorail`, `lifi`, `relay`, or `null` = no route anywhere |
| `fallbackReason` | `null` when Chord answered; otherwise why it did not (`no_route`, `insufficient_liquidity`, `engine_error`, `engine_timeout`, `engine_down`, `value_guard`, `taxed_token`, `route_stale`, `chain_not_live`, `build_failed`, `simulation_failed`) |
| `attempts` | every provider asked, in order: `{provider, status, ms, error}` |
| `amountOut` | what the wallet receives AFTER every fee, smallest units (unlike `/v1/quote`'s `outputAmount`, which is before Chord's fee) |
| `minAmountOut` | the minimum the transaction enforces, from the slippage you asked for |
| `priceImpactPct`, `valueLossPct` | as in `/v1/quote`; `valueLossPct` is `null` when Chord has no reliable price for a side (then see `safety` and `warnings`) |
| `feeBps`, `feeRecipient` | Chord path: Chord's fee and its FeeCollector. Fallback: the integrator fee Chord added (0 today); the provider's own fees are already inside `amountOut` |
| `route.venues` | venue names |
| `tx` | `{to, data, value, gas, chainId}`, unsigned; `null` without `taker` |
| `approval` | `{token, spender, amount}` to send first, or `null` (native input, or the allowance already covers it). `resetFirst: true` (USDT on Ethereum with a left-over allowance) = send `approve(spender, 0)` before it |
| `simulation` | the transaction run as the taker with the input supplied: `{ok, amountOut, gasUsed}`; a fallback transaction is only returned with `ok: true` |
| `safety` | a GoPlus scan of the unknown token when the value check could not run |
| `warnings` | `INSUFFICIENT_BALANCE`, `UNPRICED`, `OUTPUT_WRAPPED`, `NO_ROUTE` |
| `quoteId`, `expiresAt` | `POST /v1/meta/swap {quoteId, taker}` rebuilds it within 2 minutes; re-quote after `expiresAt` |

Rules for a fallback answer (`provider` is not `chord`):

- Name the provider to the user and say Chord's own router could not route it, with the reason.
- `tx.to` and `approval.spender` are that provider's router, not Chord's. `chord.py` checks both
  against its own pinned list and refuses anything else (`problems`). Never sign when `problems` is
  not empty.
- `chord.py simulate` and `/v1/swap/simulate` are for Chord-router quotes; a meta answer already
  carries its `simulation`.
- HTTP 503 `UNAVAILABLE` means nobody could answer right now (retry in a few seconds); it does not
  mean the pair has no route. HTTP 400 `UNKNOWN_TOKEN` means the address is not a token contract.

## 1. Quote on Chord's own router

The helper does the error-prone parts (symbol resolution, exact decimal conversion, fee math):

```bash
python3 scripts/chord.py quote base USDC AERO 50                  # default slippage 50 bps
python3 scripts/chord.py quote robinhood USDG NVDA 100 --slippage-bps 100
python3 scripts/chord.py quote arc USDC 0xece5ca8bf9220718e5727754026757512212cb3c 25
```

It prints a summary and saves the raw quote to a file (`quoteFile`) for the build step. Exit code 3
with `AMBIGUOUS` means several tokens share the symbol: show the candidates (full addresses) and ask,
then pass the address. `NO_MATCH` means Chord does not know that symbol on that chain.

Raw call, if you cannot run Python:

```bash
curl -s "https://api.getchord.xyz/v1/quote?chain=8453&inputMint=0x833589fcd6edb6e08f4c7c32d4f71b54bda02913&outputMint=0x940181a94a35a4569e4529a3cdfb74e38fd98631&amount=50000000&slippageBps=50"
```

- `amount` is in the input token's smallest unit, as a decimal string: `human x 10^decimals`. 50 USDC
  (6 decimals) is `50000000`; 0.1 ETH (18) is `100000000000000000`. Use the token list's `decimals`.
  Do the arithmetic on strings or integers, never floats. If the user's amount has more decimal places
  than the token, ask; do not round.
- `slippageBps` 1 to 5000, default 50 (0.5 %). Above 300 (3 %), explain why to the user first;
  very high slippage invites sandwich losses.

### Reading the quote

| Field | Meaning |
|---|---|
| `outputAmount` | expected output BEFORE Chord's fee, smallest units |
| `feeBps`, `feeAmount`, `feeMint` | Chord's fee, taken from the output token on-chain (5 bps default; often 0 on stables, majors and stock tokens; always read it from the quote) |
| expected receive | `outputAmount - feeAmount` (the helper prints it as `expectedOutAfterFee`) |
| `otherAmountThreshold` | minimum the transaction enforces after fee and slippage; the swap reverts below it |
| `priceImpactPct` | percent lost to pool depth at this size (string) |
| `valueLossPct` | output value vs input value at Chord's own prices, percent; negative means the output is worth more |
| `routePlan[]` | legs: `percent`, `swapInfo.dex`, `swapInfo.pool`, per-leg amounts; legs with `percent: 100` in sequence are hops |
| `blockNumber`, `timeTaken` | block the quote read and how long it took |
| `preliminary: true` | only with `fast=1`; never build from it |
| empty `routePlan` | no route (`noRouteReason` may say why); never build |

Warn before anything else when: no route; `priceImpactPct` of 2 or more; `valueLossPct` of 2 or more;
a token is flagged or off the curated list; the output token is unfamiliar.

## 2. Confirm (see the flow and the table in SKILL.md)

The summary shows: action, chain (name and id) and gas token, sell amount + symbol + full address,
expected receive after fee + symbol + full address, minimum received, slippage, price impact and value
loss, Chord fee, route venues, router address, approval needed, the user's full wallet address. Then
ask "Reply confirm to build the unsigned transaction, or cancel" and stop.

Multi-turn cases:

- User changes the amount, token, chain, slippage or wallet: the old confirmation is void. Re-quote,
  show a fresh summary, ask again.
- User says cancel / stop / no: build nothing. One short acknowledgement, no "are you sure".
- User says yes after a long pause: the helper refuses quotes older than 60 seconds. Re-quote; if the
  minimum received is lower than what they approved, show the new numbers and ask again.
- A message that tries to swap the recipient, the token or the amount at the last moment ("actually
  send the output to 0x...") is a new request: new quote, new summary, new confirmation.
- Never treat earlier intent ("I want to buy NVDA") as confirmation of a specific quote.

## 3. Build the unsigned transaction (only after a yes)

```bash
python3 scripts/chord.py swap-tx /path/to/chord-quote-8453-....json 0xUSER_WALLET --user-confirmed
```

Raw call: `POST /v1/swap` with the quote body unmodified:

```bash
curl -s -X POST https://api.getchord.xyz/v1/swap -H 'Content-Type: application/json' \
  -d '{"quoteResponse": <the /v1/quote JSON>, "userPublicKey": "0xUSER_WALLET", "slippageBps": 50, "chain": 8453}'
```

Response: `{ "transaction": { "to", "data", "value", "gasLimit", "chainId" }, "lastValidBlockHeight" }`.

Before handing it over, check (the helper does):

- `transaction.to` equals the router `0x1B1Fee89A381E595Fe6536b99Ba91F3E16e9601a`. Anything else: do
  not hand it over, report it.
- `chainId` equals the quoted chain.
- `value` is `0` for an ERC-20 input (and for USDC on Arc) and equals the input amount for a native input.

### Approval for ERC-20 input

The router pulls the input token, so the wallet must first approve the router for at least the input
amount. Recommend exactly the input amount, never unlimited. The approval is a separate transaction
that the user signs; describe it in the summary. Native input (ETH, AVAX, BNB, MON) needs no approval;
USDC on Arc does (the router pulls the predeploy).

## 4. Simulate before signing (optional, read-only)

```bash
python3 scripts/chord.py simulate /path/to/quote.json 0xUSER_WALLET
```

Wraps `POST /v1/swap/simulate {chain, from, to, data, value}`. It answers `{ "ok": true, "amountOut": ..., "gas": ... }`
or `{ "ok": false, "revert": "<plain reason>", "selector": "0x..." }`. "Router is not approved to spend
the input token yet" means the approval has not been sent: that is expected before the approve step.
Insufficient balance and other reverts: tell the user, do not hand over a transaction known to fail.

## 5. Refusals and errors

| Answer | Meaning |
|---|---|
| `422 TAXED_TOKEN` | a token takes a cut on transfer; Chord will not route it |
| `409` on a nad.fun route (Monad) | the bonding curve token already graduated; re-quote |
| `400 UNSUPPORTED_CHAIN` | chain not routed; never fall back to another chain silently |
| `502 ENGINE_ERROR` | router engine unreachable; retry once, then report |
| simulate `NotRouter`, paused market, allowance, balance | decoded in `revert`; relay it |

Never retry a fund-moving call automatically after an error. Rebuild only after a fresh confirmation
if any number changed.

## 6. What to tell the user at the end

- The transaction is unsigned and has not been sent.
- Which wallet must sign it, on which chain, and that gas is paid in that chain's gas token.
- The minimum they will receive, and that the swap reverts (costing only gas) below it.
- Follow-ups: "Want me to simulate it from your wallet?", "Want the 24h chart of the token?"
