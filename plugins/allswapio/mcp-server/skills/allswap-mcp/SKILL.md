---
name: allswap-mcp
description: Set up and use the read-only AllSwap MCP server (@allswapio/mcp-server 1.0.2, stdio) to look up AllSwap's public asset catalog, its official channels and company details, and block-explorer links for transaction hashes.
version: 1.0.0
metadata:
  openclaw:
    requires:
      bins:
        - npx
    envVars:
      - name: ALLSWAP_API_ORIGIN
        required: false
        description: Optional. Origin used by list_supported_assets for its one GET request. Default https://allswap.io. Leave unset in normal use.
    homepage: https://allswap.io/docs/mcp
---

# AllSwap MCP server

`@allswapio/mcp-server` is a small, read-only Model Context Protocol server that runs locally over stdio.
It has three tools and no runtime dependencies. It takes no API keys, wallet keys or other credentials.

Documentation: https://allswap.io/docs/mcp. Source: https://github.com/allswapio/mcp-server (MIT). Package: https://www.npmjs.com/package/@allswapio/mcp-server.

## When to use it

Use this server when the user asks:

- whether AllSwap lists a given asset, or which assets it lists on a given chain (`list_supported_assets`);
- for AllSwap's official website, documentation, support contact, social accounts, Chrome extension ID or
  company registration details, for example to check that a link or account claiming to be AllSwap is
  genuine (`get_official_channels`);
- for a block-explorer link to a transaction hash on a supported mainnet (`get_tx_explorer_url`).

Do not use it to get prices, quotes, fees, order status or balances: it has no such tool. It cannot create
orders, sign anything or move funds.

## Set it up

Requires Node.js 22 or later (`npx` comes with Node.js). Always pin the version; do not use `@latest`.

OpenClaw (saved MCP server definition):

```sh
openclaw mcp add allswap --command npx --arg -y --arg @allswapio/mcp-server@1.0.2
openclaw mcp probe allswap
```

`probe` should report three tools. Other MCP clients that use an `mcpServers` JSON configuration:

```json
{
  "mcpServers": {
    "allswap": {
      "command": "npx",
      "args": ["-y", "@allswapio/mcp-server@1.0.2"]
    }
  }
}
```

`ALLSWAP_API_ORIGIN` is optional and should normally stay unset. If it is set, it must be an `http:` or
`https:` origin with no path, query or credentials, otherwise the server prints one line to stderr and
exits with code 2.

Some clients show the tools with the server name as a prefix (for example `allswap__get_tx_explorer_url`);
the tool names below are the names the server itself reports.

## Tools

Every tool returns one text content item that contains a JSON object. All three tools are annotated
`readOnlyHint: true`.

### `list_supported_assets`

Makes one HTTPS `GET https://allswap.io/api/v2/assets` (public, no authentication, redirects not
followed, 8 s timeout, body capped at 5 MiB) and filters the result locally.

| Argument | Type | Meaning |
| :--- | :--- | :--- |
| `symbol` | string, optional | Exact symbol, case-insensitive. `usdt` matches `USDT`; `US` matches nothing. |
| `chainId` | string, optional | Case-insensitive substring of the asset's CAIP-2 `chainId`. `eip155` matches every EVM chain; `tron` matches `tron:mainnet`. |
| `quotableOnly` | boolean, optional | Only the boolean `true` filters out assets whose `quotable` is `false`. |
| `limit` | integer, optional | 1 to 200, default 25. Any other value uses 25. |

Returns `{ observedAt, stale, totalAssets, matchedAssets, returnedAssets }`. `returnedAssets` holds the
catalog entries exactly as the API returns them (fields such as `assetId`, `chainId`, `symbol`,
`decimals`, `quotable`). `matchedAssets` can be larger than the number returned; raise `limit` or narrow
the filters to see the rest. `totalAssets` counts the entries in that one response; the server does not
follow a pagination cursor.

On a non-200 response, a redirect, an oversized body, a network error or a timeout it returns
`{ "error": "..." }` with `isError: true`. Report the error to the user; do not retry in a loop.

### `get_official_channels`

No arguments, no network access. Returns a fixed object: website (`https://allswap.io`), documentation
(`https://allswap.io/docs`), OpenAPI specification, verification page, support and security contact
(`service@allswap.io`), Telegram and X accounts, Chrome Web Store extension ID and link, the operating
company (Haohang Network Technology Co., Limited), its Hong Kong Business Registration No., D-U-N-S number
and registered address, the compliance page, and the statement that AllSwap issues no token, presale or
airdrop.

Use these values as given. If a user shows a link, account or contact that is not in this object, say it
is not among AllSwap's listed official channels.

### `get_tx_explorer_url`

No network access. Builds an explorer URL from the hash format alone; it does not check that the
transaction exists.

| Argument | Type | Meaning |
| :--- | :--- | :--- |
| `network` | string | Network key or CAIP-2 id, case-insensitive: for example `eth`, `eip155:8453`, `btc`, `tron`, `sol`, `ton`, `near:mainnet`. |
| `txHash` | string | The transaction hash. |

Returns `{ network, txHash, explorerUrl, valid }`. For an unknown network, a hash in the wrong format or a
non-string argument, `explorerUrl` is `null` and `valid` is `false`. Hash formats: EVM networks `0x` + 64
hex; Bitcoin, Litecoin, Dogecoin, Bitcoin Cash, Zcash, Tron, TON, XRP and Stellar 64 hex (TON Base64
hashes are not linked); Solana, NEAR and Sui Base58 of 32 to 96 characters; Aptos `0x` + 1 to 64 hex.
The full table of network keys is in the README of the source repository.

## Worked examples

1. "Does AllSwap list USDT on Tron?"

   Call `list_supported_assets` with `{ "symbol": "USDT", "chainId": "tron" }`. If `matchedAssets` is 0,
   it is not in the catalog response. Otherwise answer from the returned entry (its `assetId`, `decimals`
   and whether `quotable` is `true`), and mention `observedAt` and `stale` when the user needs to know
   how current the catalog is.

2. "Give me an explorer link for this Bitcoin transaction:
   4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b"

   Call `get_tx_explorer_url` with `{ "network": "btc", "txHash": "4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b" }`.
   The reply contains
   `"explorerUrl": "https://mempool.space/tx/4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b"`
   and `"valid": true`. Tell the user the link only reflects the hash format; the explorer shows whether
   the transaction exists.

3. "Someone on Telegram says they are AllSwap support. Is that real?"

   Call `get_official_channels` with `{}` and compare the account or contact the user was given with the
   `telegram`, `x`, `supportEmail` and `website` values. If it does not match, say so and give the user
   the listed channels.

4. A hash with the wrong format, for example `{ "network": "eth", "txHash": "abc" }`, returns
   `"valid": false` and `"explorerUrl": null`. Ask the user to check the hash and the network instead of
   guessing another network.

## Limits

- Read-only. The server cannot quote prices, show fees, create or track orders, sign transactions or move
  funds, and it never asks for keys or credentials.
- Network use: only `list_supported_assets` makes a request, one public GET to the catalog endpoint per
  call. The other two tools work offline.
- The asset catalog changes over time; treat each answer as a snapshot at `observedAt`.
- `get_tx_explorer_url` checks formats only and covers the networks listed in its table; anything else
  returns `valid: false`.
