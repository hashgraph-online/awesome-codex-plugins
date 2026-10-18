<p align="center"><img src="assets/logo.png" width="120" alt="MoltNode"></p>

# MoltNode by Chord: MCP server

<!-- mcp-name: io.github.tuantqse90/moltnode -->

Read 31 blockchains and swap tokens from any AI agent. One hosted MCP server, no API key, no signup.

- **Read**: JSON-RPC on Ethereum, Base, Arbitrum, Solana, Monad, BNB Chain, Avalanche, Sui and 23 more, through [MoltNode](https://moltnode.ag) (automatic failover across providers).
- **Trade**: best-route swap quotes from [Chord](https://getchord.xyz) on Ethereum, Base, Monad, BNB Chain, Avalanche, Arbitrum, Robinhood Chain and Arc, with the unsigned transaction, the approval it needs and a simulation run from your wallet. Your agent signs with its own key; nothing is ever held for you.

```
https://moltnode.ag/mcp
```

## Connect

**Claude Code**

```bash
claude mcp add --transport http moltnode https://moltnode.ag/mcp
```

Or install everything as a plugin (MoltNode + Chord MCP servers and the three skills):

```
/plugin install moltnode --marketplace tuantqse90/moltnode-mcp
```

**Cursor, Windsurf, VS Code, Claude Desktop and any client that takes a URL**

```json
{
  "mcpServers": {
    "moltnode": { "type": "http", "url": "https://moltnode.ag/mcp" }
  }
}
```

In Claude Desktop or claude.ai you can also add it under Settings → Connectors → Add custom connector, with the URL above.

**Clients that only start local commands (stdio)**

```json
{
  "mcpServers": {
    "moltnode": { "command": "npx", "args": ["-y", "moltnode-mcp"] }
  }
}
```

(`npx -y github:tuantqse90/moltnode-mcp` works too.)

The stdio bridge in this repo (`index.mjs`) forwards every call to the hosted server, so both give the same tools.

## Tools

| Tool | What it does |
| --- | --- |
| `list_chains` | Every chain MoltNode serves (slug, chainId, native coin, endpoint) and the ones Chord trades on |
| `rpc_call` | Any JSON-RPC method on any chain: `eth_call`, `eth_getLogs`, Solana `getBalance`, Sui methods, … |
| `get_block_number` | Latest block of an EVM chain |
| `get_balance` | Native-coin balance of an address on an EVM chain |
| `chord_find_token` | Token address, decimals and verified flag by symbol or name |
| `chord_swap_quote` | Best route across the chain's DEXs + unsigned `tx` + `approval` (as a ready transaction) + simulation from the taker wallet |
| `send_raw_transaction` | Broadcast a signed transaction |

## How an agent swaps

1. `chord_find_token` → the addresses and decimals of the two tokens (the zero address is the native coin).
2. `chord_swap_quote` with `taker` = the agent's wallet. Amounts are integer strings in the token's smallest unit (`10000000` = 10 USDC).
3. If the answer has `approval`, sign and send `approval.tx` first.
4. Sign `tx` with the agent's own key.
5. `send_raw_transaction` on the same chain.

The router enforces `minAmountOut` on-chain. Chord's own router answers first; another aggregator is used only when Chord has no route, and the answer says which.

## Agent skills

Install with the skills CLI (Claude Code, Codex, Cursor, Gemini CLI and more): `npx skills add tuantqse90/moltnode-mcp`, or in Hermes: `hermes skills tap add tuantqse90/moltnode-mcp`. Gemini CLI extension: `gemini extensions install https://github.com/tuantqse90/moltnode-mcp`.

- `skills/moltnode/`: read 31 chains and swap through Chord end to end, with the safety rules (never handle a private key, confirm the quote before signing).
- `skills/chord-swap/`: safe best-route token swaps through Chord on Ethereum, Base, Arbitrum, BNB Chain, Avalanche, Monad, Robinhood Chain, Arc and Solana: finds the right token, checks it for honeypots and taxes, quotes, waits for the user's yes, then returns an unsigned transaction with a simulation for the user's own wallet. Plain HTTP, no key, no scripts.
- `skills/chord-charts/`: candlestick chart (SVG) with volume for any token on Ethereum, Base, Monad, BNB Chain, Avalanche, Arbitrum, Robinhood Chain, Arc or Solana, from Chord's trade data (`python3 scripts/chart.py --chain base --token AERO --tf 1h`).
- `skills/chord/`: Chord's trading and market-data skill (quotes, unsigned swaps, token boards, candles, wallet PnL, smart money, holders, LP pools), marketplace edition: no key handling, no environment variables, no installer (generated from Chord's skill at nullterminal `5f07c02e`; the Ask command, which needs a key, is left out). The original with Ask: https://getchord.xyz/docs/skills/chord/

`skills/moltnode/SKILL.md` is a SKILL.md skill (Claude Code, Codex CLI, Cursor, Gemini CLI, OpenClaw and others): when to read a chain, how to run a swap end to end, and the safety rules (never handle a private key, confirm the quote before signing). Install it by copying the folder into your agent's skills directory, e.g. `~/.claude/skills/moltnode/`.

## Without MCP

- Function-calling definitions (Anthropic and OpenAI shapes), with the HTTP call behind each tool: https://moltnode.ag/tool-schema.json
- Plain JSON-RPC: `POST https://moltnode.ag/<chain>` (e.g. `https://moltnode.ag/base`)
- Chain catalog: https://moltnode.ag/api/chains · OpenAPI: https://moltnode.ag/openapi.json · Brief for LLMs: https://moltnode.ag/llms.txt
- Live swap quote in the browser and full viem / web3.py code: https://moltnode.ag/trade

## Chains

Read: Monad, Ethereum, Base, Arbitrum One, Optimism, Polygon, BNB Chain, Solana, Avalanche C-Chain, HyperEVM, Berachain, Abstract, Sei, Sonic, Mantle, Taiko, zkSync Era, ZetaChain, opBNB, BOB, Edge, Stable, Katana, Morph, Swellchain, 0G, TAC, X Layer, Gnosis, Fantom, Sui.

Trade (Chord): Ethereum, Base, Monad, BNB Chain, Avalanche, Arbitrum, Robinhood Chain, Arc.

## Limits

Free and shared: short bursts of 60 requests, then 3 requests per second and 20,000 per day per client; answers up to 8 MB. Past a limit the tools answer with the wait time. Send a User-Agent. For heavy production traffic, run your own node.

## Links

- MoltNode: https://moltnode.ag · for agents: https://moltnode.ag/agents
- Chord: https://getchord.xyz · docs: https://getchord.xyz/docs/ · Chord's own MCP (17 more tools: boards, candles, wallet PnL, smart money, LP pools): https://api.getchord.xyz/v1/mcp

## License

MIT
