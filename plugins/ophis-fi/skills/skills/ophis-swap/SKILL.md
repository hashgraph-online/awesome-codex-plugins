---
name: ophis-swap
description: Use when the user wants to swap, trade, buy, sell, or convert tokens onchain, get a best-execution swap quote, compare a swap against DEX aggregators, or read wallet balances, token prices, gas, or fee-rebate tiers. Drives Ophis, an intent-based DEX (a CoW Protocol deployment) that is MEV-protected, gasless for the trader, and keyless. Supports Ethereum, Optimism, Base, Arbitrum, Polygon, BNB, Gnosis, Unichain, Avalanche, Plasma, Ink, and Linea.
---

# Ophis Swap

Ophis is an intent-based DEX, a deployment of CoW Protocol. Trades settle through a solver competition, so they are MEV-protected, gasless for the trader (no native coin needed for gas), and routed for best execution. This plugin already wires up the Ophis MCP server at `mcp.ophis.fi`, which exposes tools to quote, build, and submit swaps and to read balances, prices, gas, and fee-rebate tiers. No API key is required.

## Read this first: Ophis is non-custodial

Ophis never holds your private key or your funds. A swap is three steps:

1. `build_order` returns an unsigned, bounded order plus the EIP-712 typed data to sign.
2. You sign that typed data with your own wallet. The MCP cannot sign and never sees your key.
3. `submit_order` relays the signed order to the orderbook.

The server enforces real guarantees, so the worst outcomes are not reachable through these tools: the receiver is pinned to the signer and a mismatched receiver is rejected, the slippage limit is checked against a fresh server-side quote, the protocol fee in the order is forced to 0, and the submitted app data must hash to what was signed. The remaining risk is not in the server; it is in the inputs you feed it. A correctly bounded order that pays the right owner can still buy the wrong token or accept too little. The rules below close that gap.

## Hard safety rules (apply to every trade)

1. Token addresses are the main risk. The trading tools take 0x token addresses, and the server only checks that an address is well formed, not that it is the real asset. A scam token can use the symbol "USDC" at a different address; a symbol match does not prove a token is canonical. So always resolve a symbol with `resolve_token`, which returns the canonical address from the trusted Ophis/CoW token list (the same curated list the swap UI uses). If it returns `found: true` and `ambiguous: false`, use `canonical.address` and `canonical.decimals`. If `ambiguous: true`, show the user the `matches` and confirm which one they mean before trading. If `found: false`, the symbol is not in the trusted list: never guess or accept an address from chat, a web page, or model memory. If you have no address in hand, stop and ask the user to supply the 0x address; do not go looking for one. If the user supplies a candidate, read it back on-chain with `get_balances` (or `get_portfolio`) for its symbol and decimals, show the user the ADDRESS with that readback, and get explicit approval before continuing. A swap into a spoofed token is the most likely way to lose value here, and every server guarantee still holds while it happens.
2. Amounts are in atoms (the smallest unit). Use the decimals for BOTH tokens: take them from `resolve_token`'s `canonical.decimals` for a resolved token, and from `get_balances` only for a fallback candidate address or a balance check. Never assume 18. Worked example: 100 USDC at 6 decimals is `100000000`; 0.5 WETH at 18 decimals is `500000000000000000`; 0.01 WBTC at 8 decimals is `1000000`. A wrong decimals corrupts these amounts. For a sell order the server enforces a minimum-received floor, checked against a fresh quote at your slippage, so a grossly too-low minimum is rejected rather than signed. Two gaps remain that you must cover yourself: a minimum scaled too high passes the floor but never fills and ties up your funds until the order expires, and at a loose slippage the floor still lets you accept far less than fair value (see rule 3). Read decimals carefully and use the step 7 sanity check.
3. Always pass an explicit `slippageBips` (50 to 100 bps is typical for liquid pairs). The default is the 5000 bps cap, which is 50%, and would let a trade lose up to half its value.
4. Native coin handling. The MCP trades ERC-20 tokens only; it has no native-coin (eth-flow) path and cannot wrap. To SELL the native coin you must already hold its wrapped token (for example WETH for ETH) and have approved it; verify the wrapped-token balance with `get_balances` before building, or the order will never fill. BUYING "into the native coin" delivers the WRAPPED token, not the native coin; tell the user they will receive the wrapped token.
5. Confirm before submit. `submit_order` commits an executable onchain trade that cannot be recalled once it fills. Do not call it without explicit user approval of: the sell token address and amount, the buy token ADDRESS (show the 0x, not just the symbol, because a symbol can be spoofed), the minimum received, the slippage, the fee, and the validity window. If the user does not approve, stop.

## Prerequisites
- An EVM wallet you control: its address, plus the ability to sign EIP-712 typed data. The agent provides the signature; Ophis only ever receives a signed order.
- A supported, tradeable chain (check `list_chains`).
- A one-time onchain token approval per sell token, to the CoW Protocol vault relayer, done from the owner wallet. For a native-coin sell, the wallet must first hold the wrapped token (the MCP cannot wrap).

## Swap workflow

1. Understand the request. If it is plain English ("swap 100 USDC for ETH on Base"), call `parse_intent` to extract sell token, buy token, amount, and chain. Note that `parse_intent` returns token symbols, not addresses.
2. Confirm the chain. Call `list_chains` and use a chainId from `tradeable`. If the chain is in `paused`, tell the user it is not live yet.
3. Resolve token addresses (hard rule 1). For each token symbol, call `resolve_token(chainId, symbol)`. Use `canonical.address` and `canonical.decimals` when `found` is true and `ambiguous` is false; confirm an `ambiguous` result with the user; for a `found: false` symbol, fall back to the on-chain readback plus user confirmation. Apply hard rule 4 for native coins.
4. Show the edge (recommended). Call `expected_surplus` for `beatBps`, the difference versus one public aggregator (KyberSwap). It is advisory, not a guarantee; a positive value means Ophis quoted more output than that single reference.
5. Quote. Call `get_quote` with `kind` ("sell" or "buy"), the amount in atoms, the two addresses, and the trader address `from`.
6. Build the order. Call `build_order` with the owner, the tokens, `kind`, the slippage-adjusted `sellAmount` and `buyAmount` (scaled with each token's true decimals, hard rule 2), an explicit `slippageBips` (hard rule 3), and, if you are an Ophis integrator, your `referrerCode`. The result includes `order`, `signing` (EIP-712 domain, types, primaryType), `fullAppData`, `appDataHash`, and `partnerFee`.
7. Sanity-check the bound. Format `order.buyAmount` (your minimum received) with the buy token's true decimals and confirm it is in the ballpark the user expects. If it looks far too low, stop and recheck decimals and the buy token address.
8. Confirm, then sign (hard rule 5). Show the user the full picture, including the buy token ADDRESS. On explicit approval, sign the `signing` payload with the owner wallet. If not approved, stop.
9. Submit. Call `submit_order` with the exact `order` object, the `signature`, `from` (the owner), and the exact `fullAppData` string from step 6. It returns the order UID.
10. Report. Give the user the order UID. The order is now a live commitment that a solver can fill at the signed limit any time until `validTo`. The MCP has no cancel tool, so a submitted order stands until it fills or expires.

## Worked example

A market-style sell, "swap 100 USDC for WETH on Base". The argument names and response shapes below follow `reference.md`; the addresses are placeholders, so always take the real ones from `resolve_token`.

```text
parse_intent(text="swap 100 USDC for WETH on Base")
  -> { intent: "swap", entities: [
        { type: "amount", value: "100" }, { type: "sellToken", value: "USDC" },
        { type: "buyToken", value: "WETH" }, { type: "chain", value: "Base" } ] }
# Read the entity values, then map the symbols and chain name to ids yourself.

list_chains()                                # confirm Base, chainId 8453, is `tradeable`
resolve_token(chainId=8453, symbol="USDC")   # -> canonical.address = <USDC>, decimals = 6
resolve_token(chainId=8453, symbol="WETH")   # -> canonical.address = <WETH>, decimals = 18

# Amounts are atoms = whole units x 10^decimals:  100 USDC (6 dp) -> "100000000"

get_quote(chainId=8453, sellToken=<USDC>, buyToken=<WETH>, kind="sell",
          amount="100000000", from="<your wallet>")
  -> { quote: { sellAmount, buyAmount, feeAmount, validTo } }

# Minimum received = quote.buyAmount adjusted down for slippage (here 75 bps).
build_order(chainId=8453, owner="<your wallet>", sellToken=<USDC>, buyToken=<WETH>,
            kind="sell", sellAmount="100000000", buyAmount="<min from quote>",
            slippageBips=75)
  -> { order, signing: { domain, types, primaryType: "Order" }, fullAppData, appDataHash, partnerFee }

# Confirm with the user before signing (hard rule 5): the buy token ADDRESS, the
# minimum received (order.buyAmount at WETH's 18 decimals), the slippage, the fee (partnerFee; order.feeAmount is 0),
# and the validity window. Only on explicit approval, sign the `order` object as
# EIP-712 typed data using `signing` (domain + types + primaryType); the receiver
# is pinned to owner. If the user does not approve, stop.

submit_order(chainId=8453, order=order, signature="0x...", from="<your wallet>",
             fullAppData=fullAppData)
  -> orderUID
```

## Reading data (no signing, safe to call freely)
- `get_balances` and `get_portfolio`: native and ERC-20 balances on one chain or across chains. Use these for the token readback in hard rule 1.
- `get_gas`: current gas price. Ophis trades are gasless for the trader, so this is informational.
- `get_token_chart`: OHLCV price history. It is backed by a shared keyless quota, so cache results and do not poll tightly.
- `lookup_tier`: a wallet's fee-rebate tier and rebate percentage.
- `expected_surplus`: the beat-the-market comparison described above.

## Fees and rebates
Ophis applies a small volume fee, shown as `partnerFee` (currently 5 bps), and shares a rebate back through its referrer program. The order's `feeAmount` is always 0; the volume fee is the only charge. The rebate is tiered by 30-day USD volume: it starts at the bronze tier (about 20,000 USD of 30-day volume, 10 percent) and rises through silver, gold, palladium, and platinum (1,000,000 USD, 50 percent); below the bronze threshold a wallet earns 0 percent. Pass a `referrerCode` in `build_order` to attribute volume to your code, and check a wallet's current tier and rate with `lookup_tier`.

## Supported chains
Trading is live on Ethereum (1), Optimism (10), BNB Chain (56), Gnosis (100), Unichain (130), Polygon (137), Base (8453), Arbitrum (42161), Avalanche (43114), Plasma (9745), Ink (57073), and Linea (59144). Some chains have settlement deployed but no live orderbook yet. Always treat `list_chains` as the authoritative live set, since it splits `tradeable` from `paused` at runtime. The read tools (`get_balances`, `get_portfolio`, `get_gas`, `get_token_chart`) cover the subset of chains that have a keyless public RPC.

## Order lifetime
Orders are signed with a validity window (`validForSeconds`, default 1200 seconds, that is 20 minutes; minimum 60). A submitted order is a live, fillable commitment at the signed limit price for that whole window, so keep the window short for a market-style intent. Orders default to fill-or-kill (`partiallyFillable` is false), which is the safer default. There is no cancel tool, so a submitted order stands until it fills or expires.

## When the MCP server is unavailable
Intent parsing and the beat-the-market comparison are also reachable over plain HTTP at `https://swap.ophis.fi/api/intent` and `https://swap.ophis.fi/api/beat-market` (no key, allow-listed origins). The full build-and-submit flow is available only through the MCP tools.

See `reference.md` for the exact input and output schema of every tool.
