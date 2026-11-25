# @allswapio/mcp-server

[![allswapio/mcp-server MCP server](https://glama.ai/mcp/servers/allswapio/mcp-server/badges/score.svg)](https://glama.ai/mcp/servers/allswapio/mcp-server)

A read-only [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server for
[AllSwap](https://allswap.io). It speaks JSON-RPC 2.0 over stdio and offers three tools:

| Tool | What it does | Network |
| :--- | :--- | :---: |
| `list_supported_assets` | Fetches AllSwap's public asset catalog (`GET https://allswap.io/api/v2/assets`, no authentication; specification at <https://allswap.io/docs/openapi.json>) and filters it. | HTTPS GET |
| `get_official_channels` | Returns AllSwap's official website and documentation links, contact email, social accounts, Chrome extension ID, company registration details and its statement that it issues no token. | None |
| `get_tx_explorer_url` | Returns a block-explorer URL for a transaction hash on a supported mainnet network. Only the hash format is checked, not whether the transaction exists. | None |

It cannot create orders, quote prices, move funds or sign anything, and it takes no API keys, wallet keys
or credentials. All three tools carry the annotation `readOnlyHint: true`; only `list_supported_assets` has
`openWorldHint: true`. No runtime dependencies; Node.js 22 or later.

Documentation, with setup notes for Claude Desktop, Claude Code, Cursor and VS Code: <https://allswap.io/docs/mcp>.

## Use with an MCP client

```json
{
  "mcpServers": {
    "allswap": {
      "command": "npx",
      "args": ["-y", "@allswapio/mcp-server"]
    }
  }
}
```

MCP Registry name: `io.github.allswapio/mcp-server` (the `mcpName` in `package.json`; the registry metadata
is in `server.json` in the repository).

The command installed by the package is `allswap-mcp`. The environment variable `ALLSWAP_API_ORIGIN`
changes the origin used by `list_supported_assets` (default `https://allswap.io`). It must be an `http:` or
`https:` origin with no path, query or credentials (for example `https://allswap.io`); otherwise the command
prints one line to stderr and exits with code 2 before reading any input.

To try it by hand, send one JSON-RPC message per line on stdin:

```sh
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18"}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_tx_explorer_url","arguments":{"network":"btc","txHash":"4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b"}}}' \
  | npx -y @allswapio/mcp-server
```

The second reply contains
`"explorerUrl": "https://mempool.space/tx/4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b"`.

### Run in a container

No container image is published. To run the server in a container, build it yourself from this repository
(the `Dockerfile` is in the repository, not in the npm package):

```sh
docker build -t allswap-mcp .
```

Then use `"command": "docker"` with `"args": ["run", "--rm", "-i", "allswap-mcp"]` in the client configuration
above. The image runs as a non-root user and needs outbound HTTPS only for `list_supported_assets`.

## Tools

### `list_supported_assets`

| Argument | Type | Description |
| :--- | :--- | :--- |
| `symbol` | string | Optional. Exact symbol match, case-insensitive (`usdt` matches `USDT`). |
| `chainId` | string | Optional. Case-insensitive substring of the asset's `chainId` (`eip155` matches every EVM chain). |
| `quotableOnly` | boolean | Optional. `true` drops assets whose `quotable` is `false`. |
| `limit` | integer | Optional, 1-200, default 25. A value outside that range uses the default. |

Returns `{ observedAt, stale, totalAssets, matchedAssets, returnedAssets }`, where `returnedAssets` holds
the catalog entries as the API returns them. A non-2xx response, a redirect (redirects are not followed),
a response body over 5 MiB, a network error or a timeout (8 s) returns `{ error }` with `isError: true`.

### `get_official_channels`

No arguments. Returns a fixed object: website, documentation, OpenAPI and verification page links, support
and security contact (`service@allswap.io`), Telegram and X accounts, Chrome Web Store extension ID and
link, operating company (Haohang Network Technology Co., Limited), Hong Kong Business Registration No.,
D-U-N-S number, registered address, compliance page, and the statement that AllSwap issues no token,
presale or airdrop.

### `get_tx_explorer_url`

| Argument | Type | Description |
| :--- | :--- | :--- |
| `network` | string | Network key, case-insensitive (see below). |
| `txHash` | string | Transaction hash. |

Returns `{ network, txHash, explorerUrl, valid }`; `network` and `txHash` are echoed only when they are
strings (otherwise `null`). For an unknown network, a hash in the wrong format or a non-string argument,
`explorerUrl` is `null` and `valid` is `false`.

The `eip155:<id>` and `bip122:<hash>` keys and `solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp` are CAIP-2 chain ids.
The keys `tron:mainnet`, `ton:mainnet`, `ripple:0` and `near:mainnet` are aliases: the chain ids AllSwap's
public asset API (`GET /api/v2/assets`) uses for those chains. `stellar:public`, `sui:mainnet` and
`aptos:mainnet` are plain aliases. For Zcash, `bip122:00040fe8ec8471911baa1db1266ea15d` is the genesis-hash
CAIP-2 id and `bip122:0007104ccda289427919efc39dc9e4d4` is the chain id that AllSwap's public asset API
(`GET /api/v2/assets`) returns for Zcash.

| Network keys | Hash format | Explorer |
| :--- | :--- | :--- |
| `eth`, `eip155:1` | `0x` + 64 hex | etherscan.io |
| `arb`, `eip155:42161` | `0x` + 64 hex | arbiscan.io |
| `base`, `eip155:8453` | `0x` + 64 hex | basescan.org |
| `bsc`, `eip155:56` | `0x` + 64 hex | bscscan.com |
| `op`, `eip155:10` | `0x` + 64 hex | optimistic.etherscan.io |
| `pol`, `eip155:137` | `0x` + 64 hex | polygonscan.com |
| `avax`, `eip155:43114` | `0x` + 64 hex | snowtrace.io |
| `btc`, `bip122:000000000019d6689c085ae165831e93` | 64 hex | mempool.space |
| `ltc`, `bip122:12a765e31ffd4059bada1e25190f6e98` | 64 hex | litecoinspace.org |
| `doge`, `bip122:1a91e3dace36e2be3bf030a65679fe82` | 64 hex | blockchair.com |
| `bch`, `bip122:000000000000000000651ef99cb9fcbe` | 64 hex | blockchair.com |
| `zec`, `bip122:00040fe8ec8471911baa1db1266ea15d` (genesis hash), `bip122:0007104ccda289427919efc39dc9e4d4` (asset API id) | 64 hex | blockchair.com |
| `tron`, `tron:mainnet` | 64 hex | tronscan.org |
| `sol`, `solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp` | Base58, 32-96 chars | solscan.io |
| `ton`, `ton:mainnet` | 64 hex (Base64 hashes are not linked) | tonscan.org |
| `xrp`, `ripple:0` | 64 hex | xrpscan.com |
| `stellar`, `stellar:public` | 64 hex | stellar.expert |
| `near`, `near:mainnet` | Base58, 32-96 chars | nearblocks.io |
| `sui`, `sui:mainnet` | Base58, 32-96 chars | suiscan.xyz |
| `aptos`, `aptos:mainnet` | `0x` + 1-64 hex | explorer.aptoslabs.com |

## Protocol details

- Supported protocol revisions: `2025-11-25`, `2025-06-18`, `2025-03-26` and `2024-11-05`. The server
  implements the `initialize`-based revisions only and does not implement revision `2026-07-28`.
- `initialize` answers with the client's `protocolVersion` when it is one of the supported revisions, with
  `2025-11-25` when the client asks for any other revision, and with `2024-11-05` when the client sends none.
  The only capability is `tools`.
- Methods: `initialize`, `ping`, `tools/list`, `tools/call`. Notifications (messages without `id`) get no
  reply. Any other method returns `-32601` (including `server/discover`); an unknown tool or a tool name that
  is not a string returns `-32602`; a message that is not a JSON-RPC 2.0 request, or whose `id` is not a
  string, a number or null, returns `-32600`, with the request's `id` when that is a string, a number or null
  and `id: null` otherwise; a line that is not JSON returns `-32700` with `id: null`; an unexpected failure
  while handling or answering a line returns `-32603`, and the server keeps running.
- Batches (JSON arrays) are not supported and return `-32600`.

## Use as a library

```js
import { createMcpHandler, TOOLS } from "@allswapio/mcp-server";

const handle = createMcpHandler(); // options: { apiOrigin, fetchImpl, timeoutMs, maxBytes }
const reply = await handle({
  jsonrpc: "2.0",
  id: 1,
  method: "tools/call",
  params: { name: "get_tx_explorer_url", arguments: { network: "eth", txHash: "0x" + "ab".repeat(32) } },
});
console.log(TOOLS.map((tool) => tool.name));
// [ 'list_supported_assets', 'get_official_channels', 'get_tx_explorer_url' ]
console.log(JSON.parse(reply.result.content[0].text).explorerUrl);
// https://etherscan.io/tx/0xabab...abab
```

`createMcpHandler` throws a `TypeError` when `apiOrigin` is not an `http:` or `https:` origin.

## Security

Please report vulnerabilities privately to service@allswap.io. See [SECURITY.md](SECURITY.md).

## License inquiries

Questions about the licensing of this software or of anything it contains: service@allswap.io.

## License

[MIT](LICENSE). Copyright (c) 2026 Haohang Network Technology Co., Limited (AllSwap).
