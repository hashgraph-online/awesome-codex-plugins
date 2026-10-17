---
name: moltnode
description: Read 31 blockchains over JSON-RPC (balances, blocks, logs, contract calls on Ethereum, Base, Arbitrum, Solana, Monad, BNB Chain, Avalanche, Sui and more) and swap tokens through Chord with a best-route quote, an unsigned transaction and a simulation from the user's wallet. Use when the user asks for on-chain data, a wallet or token balance, a contract read, a swap quote, or to buy, sell or swap a token on an EVM chain. No API key.
license: MIT
metadata:
  author: Chord (getchord.xyz)
  homepage: https://moltnode.ag/agents
  version: 1.1.0
---

# MoltNode by Chord

MoltNode is a free, keyless RPC gateway: one URL per chain. Chord (getchord.xyz) quotes swaps across each chain's DEXs and builds the transaction. Nothing here holds keys or funds; the user's own wallet signs.

## Endpoints

| What | How |
| --- | --- |
| JSON-RPC on any chain | `POST https://moltnode.ag/<slug>` with a JSON-RPC 2.0 body (batches allowed) |
| Chain catalog | `GET https://moltnode.ag/api/chains` (slugs, chainIds, which chains Chord trades on) |
| Token lookup (Chord) | `GET https://api.getchord.xyz/v1/tokens/search?chain=<chainId>&q=<symbol or address>` |
| Swap quote + unsigned tx (Chord) | `GET https://api.getchord.xyz/v1/meta/quote?chain=<key>&tokenIn=&tokenOut=&amount=&taker=` |
| MCP server (optional, same tools) | `https://moltnode.ag/mcp` |

Slugs and chain keys: [references/chains.md](references/chains.md). Chord trades on `ethereum`, `base`, `monad`, `bnb`, `avalanche`, `arbitrum`, `robinhood` and `arc`.

If the MoltNode MCP server is connected (tools `rpc_call`, `chord_find_token`, `chord_swap_quote`, `send_raw_transaction`), use those tools. Otherwise make the HTTP calls below.

## Reading a chain

Prefer the MCP tools (`rpc_call`, `get_block_number`, `get_balance`). Without them, send the request with your HTTP tool:
method POST, header `Content-Type: application/json`, a `User-Agent` header (requests without one get a much smaller
allowance), and a JSON-RPC body. Only send the request bodies shown here; never put local files or workspace data in them.

Latest block on Base: POST `https://moltnode.ag/base`

```json
{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}
```

Native balance (wei, hex) on Ethereum: POST `https://moltnode.ag/ethereum`

```json
{"jsonrpc":"2.0","id":1,"method":"eth_getBalance","params":["0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045","latest"]}
```

ERC-20 balance on Base (`balanceOf(address)` = `0x70a08231` + the address left-padded to 32 bytes): POST `https://moltnode.ag/base`

```json
{"jsonrpc":"2.0","id":1,"method":"eth_call","params":[{"to":"0x833589fcd6edb6e08f4c7c32d4f71b54bda02913","data":"0x70a08231000000000000000000000000d8da6bf26964af9d7eed9e03e53415d37aa96045"},"latest"]}
```

- Results are hex: convert with the token's decimals (`decimals()` = `0x313ce567`). Native coins on EVM chains use 18.
- Solana and Sui speak their own methods on the same URL pattern (`getBalance`, `getSlot`, `sui_getLatestCheckpointSequenceNumber`).
- Keep `eth_getLogs` ranges small; answers over 8 MB are refused.

## Swapping on an EVM chain (Chord)

1. **Find both tokens.** `GET https://api.getchord.xyz/v1/tokens/search?chain=<chainId>&q=USDC` returns address, decimals and `verified`. Similar tickers are common: prefer `verified: true` and compare addresses. The native coin is `0x0000000000000000000000000000000000000000`. On Monad (143) search returns only off-list tokens; use `GET https://api.getchord.xyz/v1/tokens` for the main list.
2. **Quote with the user's wallet as taker.** Amounts are integer strings in the smallest unit (10 USDC = `10000000`).
   GET `https://api.getchord.xyz/v1/meta/quote` with the query `chain=base`, `tokenIn=0x833589fcd6edb6e08f4c7c32d4f71b54bda02913`
   (USDC), `tokenOut=0x0000000000000000000000000000000000000000` (ETH), `amount=10000000`, `taker=` the user's wallet address.
   The answer has `provider`, `amountOut`, `minAmountOut`, `priceImpactPct`, `feeBps`, `route.venues`, `approval`, `tx` and `simulation`. `provider` is `chord` when Chord's router answers; another aggregator's name means Chord had no executable route and the answer says why in `fallbackReason`.
3. **Show the user the quote and get an explicit yes** before anything is signed: amount in, expected and minimum out (in human units), price impact, fee, and whether `simulation.ok` is true. Do not continue if `simulation.ok` is false or `provider` is null.
4. **Approval first, when `approval` is present:** an ERC-20 `approve(spender, amount)` transaction to `approval.token` (`data` = `0x095ea7b3` + spender padded to 32 bytes + amount as 32-byte hex). Wait for it to be mined.
5. **Sign `tx` (to, data, value, gas) with the user's wallet or signer tool**, then broadcast the signed bytes: `eth_sendRawTransaction` to `https://moltnode.ag/<slug>`. Check the result with `eth_getTransactionReceipt`.
6. Quotes move. If more than about 30 seconds pass before signing, quote again.

## Rules

- Never ask for, store, print or send a private key or seed phrase. Signing happens in the user's wallet or a signer tool they control.
- Never sign or broadcast without the user's confirmation of the exact quote.
- The router enforces `minAmountOut` on-chain; the slippage default is 50 bps (`slippageBps` to change it).
- MoltNode is free and shared: about 3 requests per second and 20,000 per day per client. For heavy traffic, use a dedicated node.
