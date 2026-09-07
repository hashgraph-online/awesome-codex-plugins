# TNT House Risk-Data API — Codex plugin

A Codex/ChatGPT plugin ([openai/plugins](https://developers.openai.com/codex/plugins) format)
wrapping the Risk-Data API's remote MCP server. Same production server already
listed on Smithery, Glama, and the Official MCP Registry — no separate
integration needed.

- `.codex-plugin/plugin.json` — manifest (name, description, keywords, interface metadata)
- `.mcp.json` — declares the remote server at `https://tnt-audit.com/api/mcp` (`http` type)
- `assets/icon.svg` — plugin icon

## What you get with zero configuration

- `check_token_risk` works with **no API key** for the first 3 calls/day per
  IP (100/day global cap) — a genuine anonymous trial, not a locked demo.
- Returns a 0-100 safety score, insider wallet cluster detection (shared
  first-funder tracing), mint/freeze authority status, honeypot risk, and
  LP-lock status for any Solana token mint.

## Higher limits / other tools

`check_token_risk_batch` (up to 25 mints/call) and `get_token_risk_history`
require a Bearer API key. Get a free key (15 calls/day) at
[tnt-audit.com/risk-api](https://tnt-audit.com/risk-api).

x402 pay-per-call ($0.02/call in USDC, no key at all) is also available for
fully autonomous agents — see
[tnt-audit.com/risk-api](https://tnt-audit.com/risk-api) for the x402
endpoint.

## Source product

This plugin wraps a server maintained in the main
[tnt-house](https://github.com/menantonio83-hue/tnt-house) repository. This
standalone repo exists only to satisfy plugin-directory conventions that
expect `.codex-plugin/plugin.json` at a repository root.

## Links

- Docs / pricing / changelog: https://tnt-audit.com/risk-api
- Main product repo: https://github.com/menantonio83-hue/tnt-house
- X: [@RiskDataApiSol](https://x.com/RiskDataApiSol)

## Security

This plugin's MCP server is read-only: it returns risk data about Solana
tokens and never signs transactions, moves funds, or requires wallet access.
See [SECURITY.md](./SECURITY.md).
