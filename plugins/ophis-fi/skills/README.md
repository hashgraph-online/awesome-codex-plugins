# Ophis plugin for Claude Code

Give your agent the ability to swap tokens onchain through [Ophis](https://ophis.fi), an intent-based DEX built on CoW Protocol. Trades are MEV-protected, gasless for the trader, and routed for best execution.

Installing this plugin does two things:

1. Wires up the Ophis MCP server (`https://mcp.ophis.fi/mcp`) so the agent gets 12 tools to quote, build, and submit swaps and to read balances, prices, gas, and fee-rebate tiers.
2. Adds the `ophis-swap` skill, which teaches the agent the correct, safe order of operations for a trade.

## Why an agent would use Ophis

- Keyless. No API key to provision, store, or rotate. The MCP server is public.
- Non-custodial. The server never holds your key or your funds. It builds an unsigned order, your wallet signs it, and the server relays the signed order. The receiver is always the signer and cannot be redirected.
- MEV-protected and gasless. Orders settle through a solver competition, so the trader pays no gas and is shielded from sandwich attacks.
- Safe token resolution. The `resolve_token` tool maps a symbol to its canonical address from the trusted Ophis/CoW token list and fails closed, so an agent never swaps into a token that merely spoofs a well-known symbol.
- See the edge. The `expected_surplus` tool compares an Ophis quote against a public aggregator (KyberSwap) and returns the difference in basis points.
- Rebate-eligible. Ophis applies a small volume fee and shares a rebate through its referrer program.

## Install

```
/plugin marketplace add ophis-fi/skills
/plugin install ophis@ophis-fi
```

Then ask the agent to swap, and it will use the Ophis tools. For example: "swap 100 USDC for ETH on Base."

## What the agent needs

- An EVM wallet it controls (an address plus the ability to sign EIP-712 typed data). Ophis only ever receives a signed order; it never sees the key.
- A one-time onchain approval per sell token, to the CoW Protocol vault relayer, done from the owner wallet.

## Tools

`parse_intent`, `resolve_token`, `list_chains`, `get_quote`, `expected_surplus`, `build_order`, `submit_order`, `lookup_tier`, `get_balances`, `get_portfolio`, `get_gas`, `get_token_chart`.

`submit_order` is the only state-changing tool; everything else is read or build only. See `skills/ophis-swap/reference.md` for full schemas.

## Supported chains

Ethereum, Optimism, BNB Chain, Gnosis, Polygon, Base, Arbitrum, Avalanche, Plasma, Ink, and Linea. Some chains are settlement-deployed but not yet live for trading; `list_chains` reports the authoritative live set.

## Links

- App: https://swap.ophis.fi
- Site: https://ophis.fi
- Contact: contact@ophis.fi
