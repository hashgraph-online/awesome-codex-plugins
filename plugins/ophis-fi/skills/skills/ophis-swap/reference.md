# Ophis MCP tool reference

The Ophis MCP server at `https://mcp.ophis.fi/mcp` exposes 12 tools. Every response is JSON in a single text block. All amounts are in atoms (the token's smallest unit). Read tools are safe to call freely; `submit_order` is the only state-changing tool.

## parse_intent
Parse a plain-English swap request into a structured intent.
- Input: `text` (string, 1 to 280 chars).
- Output: `{ intent: "swap" | "unknown", entities: [{ type: "sellToken" | "buyToken" | "amount" | "chain", value, raw, start, end }] }`.

## resolve_token
Resolve an ERC-20 token symbol to its canonical address from the trusted Ophis/CoW token list (the same curated list the swap UI uses). Fail-closed: returns the genuinely-canonical token or nothing, never a wrong-but-plausible scam address. Use it before quoting or building so you never trade an address taken from chat, the web, or memory.
- Input: `chainId` (int), `symbol` (string, 1 to 20 chars).
- Output: `{ chainId, query, found, ambiguous, canonical: { address, symbol, decimals, name, source } | null, matches: [{ address, symbol, decimals, name, source }], note }`. Each `matches` entry carries the address, so an ambiguous result can be shown to the user by address, not just symbol. `found: false` means no trusted match (do not guess; confirm with `get_balances` and the user). `ambiguous: true` means several trusted tokens share the symbol (e.g. native vs bridged); confirm which one the user means. Native coins are not returned; resolve the wrapped symbol (e.g. WETH).

## list_chains
List Ophis chains, split into tradeable and paused. No input.
- Output: `{ tradeable: [{ chainId, name, ophisOperated, orderbookUrl, settlement, partnerFee }], paused: [{ chainId, name, settlement, reason }] }`.

## get_quote
Best-execution quote from the chain's Ophis orderbook.
- Input: `chainId` (int), `sellToken` (0x), `buyToken` (0x), `kind` ("sell" | "buy"), `amount` (atoms string; for sell it is the amount before fee, for buy it is the amount after fee), `from` (0x trader), `validForSeconds` (int, optional, default 1200).
- Output: the CoW orderbook quote, including `quote.sellAmount`, `quote.buyAmount`, `quote.feeAmount`, `quote.validTo`.

## expected_surplus
Estimate how much better Ophis quotes than the open market for a sell.
- Input: `chainId` (int), `sellToken` (0x), `buyToken` (0x), `sellAmount` (atoms string), `from` (0x).
- Output: `{ chainId, sellToken, buyToken, sellAmount, ophisBuyAmount, reference: { name: "kyberswap", buyAmount } | null, beatBps, note }`. `beatBps` greater than 0 means Ophis quoted more output than the aggregator. The value can be null or negative.

## build_order
Build a bounded, ready-to-sign CoW order. Internally re-quotes to enforce slippage and rejects if the check fails.
- Input: `chainId` (int), `owner` (0x), `sellToken` (0x), `buyToken` (0x), `sellAmount` (atoms), `buyAmount` (atoms), `kind` ("sell" | "buy"), `validForSeconds` (int, optional, min 60, default 1200), `feeAmount` (optional; must be omitted or "0"), `partiallyFillable` (bool, optional, default false), `slippageBips` (int, optional, 0 to 5000, default cap 5000), `referrerCode` (optional, 3 to 64 chars of `[a-z0-9_-]`).
- For a sell order: `sellAmount` is exact, `buyAmount` is the minimum you accept (slippage-adjusted down from the quote). For a buy order: `buyAmount` is exact, `sellAmount` is the maximum you spend (slippage-adjusted up).
- The receiver is always pinned to `owner`; there is no receiver parameter.
- Output: `{ chainId, owner, orderbookUrl, order: { sellToken, buyToken, receiver, sellAmount, buyAmount, validTo, appData, feeAmount: "0", kind, partiallyFillable, sellTokenBalance: "erc20", buyTokenBalance: "erc20" }, signing: { domain, types, primaryType: "Order" }, fullAppData, appDataHash, partnerFee: { volumeBps, recipient } | null, next }`.

## submit_order
Relay a pre-signed order to the orderbook. The only state-changing tool.
- Input: `chainId` (int), `order` (the exact `order` object from `build_order`), `signature` (0x EIP-712 signature from the owner), `signingScheme` ("eip712" default, or "ethsign"), `from` (0x owner that signed), `fullAppData` (the exact string from `build_order`; max 8192 bytes; must hash to `order.appData`).
- The order's `receiver` must equal `from`, or the call is rejected.
- Output: the order UID string.

## lookup_tier
Look up a wallet's fee-rebate tier and live status.
- Input: `wallet` (0x).
- Output: 30-day USD volume mapped to a tier and that tier's rebate percentage. The full ladder is none (0 percent), bronze (20,000 USD, 10 percent), silver (50,000 USD, 15 percent), gold (100,000 USD, 25 percent), palladium (500,000 USD, 35 percent), platinum (1,000,000 USD, 50 percent). Below the bronze threshold a wallet sits at none and earns 0 percent.

## get_balances
Native plus ERC-20 balances on one chain via a public RPC multicall.
- Input: `chainId` (int), `owner` (0x), `tokens` (array of 0x, optional, max 50).
- Output: `{ chainId, owner, native: { symbol, decimals, raw, formatted }, tokens: [{ token, symbol, decimals, raw, formatted, error? }] }`.

## get_portfolio
Native and optional ERC-20 balances across multiple chains.
- Input: `owner` (0x), `chainIds` (array of int, optional, max 12; omit to scan all chains with a public RPC), `tokensByChain` (map of chainId string to array of 0x, optional, max 50 per chain).
- Output: `{ owner, chains: [ balances result per chain, or { chainId, error } ] }`.

## get_gas
Current gas price for a chain.
- Input: `chainId` (int).
- Output: `{ chainId, maxFeePerGas, maxPriorityFeePerGas, gasPrice, gasPriceGwei, nativeSymbol, note }`. Ophis trades are gasless for the trader, so this is informational.

## get_token_chart
OHLCV price history from the keyless GeckoTerminal market API.
- Input: `chainId` (int), `token` (0x), `timeframe` ("day" default, "hour", "minute"), `aggregate` (int, optional, default 1), `limit` (int, optional, 1 to 300, default 30).
- Output: `{ chainId, token, network, pool, timeframe, aggregate, candles: [{ t, o, h, l, c, v }] }`. Backed by a shared keyless quota; cache and do not poll tightly.

## Chains with a public RPC (for balances, portfolio, gas, charts)
1 Ethereum, 10 Optimism, 56 BNB Chain, 100 Gnosis, 137 Polygon, 8453 Base, 42161 Arbitrum, 43114 Avalanche, 57073 Ink, 59144 Linea.

Trading (quote, build, submit) additionally covers Plasma (9745), which has no keyless public RPC, so the read tools above do not cover it. Treat `list_chains` as the authoritative live set of tradeable chains.

## HTTP fallback (no MCP)
- `POST https://swap.ophis.fi/api/intent` with `{ "text": "..." }` returns the same parse as `parse_intent`.
- `GET https://swap.ophis.fi/api/beat-market` backs `expected_surplus`.
Both are keyless with allow-listed origins. The build and submit flow is MCP-only.
