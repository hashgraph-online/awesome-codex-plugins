# Mnemoverse Memory

[![HOL trust score](https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fplugin%3Fslug%3Dmnemoverse%252Fmnemoverse%26metric%3Dtrust%26style%3Dflat)](https://hol.org/registry/plugins/mnemoverse%2Fmnemoverse)

Persistent memory for AI agents, shared across tools. One account gives Claude Code the same long-term memory it has in Cursor, VS Code, and any other MCP client: write a memory in one tool, recall it in another.

This plugin connects the hosted Mnemoverse memory server over MCP and adds the discipline that makes memory actually get used: recall before acting, save durable decisions and corrections afterwards.

## Install

One line, no directory and no review queue:

```
/plugin marketplace add mnemoverse/claude-plugin
/plugin install mnemoverse@mnemoverse
```

The first command registers this repository as a plugin marketplace; the second installs the plugin from it. Updates arrive with `/plugin marketplace update mnemoverse`.

To try it from a local checkout of this repository instead:

```
claude --plugin-dir ./
```

## First run: sign in once, no API key

The server at `https://mcp.mnemoverse.com/mcp` uses OAuth 2.1 with PKCE. On first use Claude Code opens a browser window; sign in to your Mnemoverse account (free tier at [console.mnemoverse.com](https://console.mnemoverse.com?utm_source=github&utm_medium=readme&utm_campaign=claude-plugin), no credit card) and grant the requested scopes, which include `memory:read` and `memory:write`. There is no API key to paste, and access can be revoked at any time from the console. The bundled `setup` skill walks Claude through this if anything goes wrong.

## What you get

**Three commands:**

| Command | What it does |
| --- | --- |
| `/mnemoverse:remember` | save a durable fact, decision, or correction, one fact per memory |
| `/mnemoverse:recall` | search memory before acting, with provenance, surfacing contradictions instead of hiding them |
| `/mnemoverse:memory-status` | counts, domains, and the newest memories |

**Two skills:**

- `agent-memory-discipline` (CC0, backend-neutral): standing rules for when to recall and what is worth saving. It names no vendor and works on any memory backend; it ships here so the connected memory is actually used.
- `setup`: guides Claude through connecting and troubleshooting the MCP server.

**The tools come from the remote server itself**: reading and writing memories, a newest-first listing, stats, usefulness feedback, shared rooms, and a vault alias listing (aliases only, values are never returned). The current list, with descriptions and schemas, is at the server's [card](https://mcp.mnemoverse.com/.well-known/mcp/server-card.json).

Neither the remote connector nor the [local package](https://mnemoverse.com/docs/api/mcp-server) has a delete tool, so a one-click sign-in can never wipe memory.

## Try these

1. `Remember that this project uses pnpm, not npm. We decided this after a lockfile conflict on 2026-08-01.`
2. `Before you touch the billing module, recall what we have decided about it in past sessions.`
3. `/mnemoverse:memory-status` after a week of use, to see what your sessions have been saving.

## What gets stored, and what does not

The plugin stores only what you or Claude explicitly save through the memory tools: single facts, decisions, corrections. It does not record conversations, does not read your chat history, and the bundled skill explicitly refuses to persist secrets, API keys, passwords, payment data, or personal identifiers.

Memory content lives in your Mnemoverse account. Privacy policy: [mnemoverse.com/privacy](https://mnemoverse.com/privacy).

## Troubleshooting

- **No browser window on first use**: run `/mcp` to check server status, or re-add manually with `claude mcp add --transport http mnemoverse https://mcp.mnemoverse.com/mcp`.
- **`401` after it used to work**: the token expired; the next tool call normally refreshes it. If not, remove and re-add the server to re-run sign-in.
- **`malformed_token` in logs**: something is sending an API key as a bearer token. The remote endpoint takes OAuth tokens only; API keys are for the [REST API](https://mnemoverse.com/docs/api/reference) and the local package.

More: [docs](https://mnemoverse.com/docs/api/remote-mcp-server).

## Why `.mcp.json` says `http` and `mcp.json` says `streamable-http`

Both files point at the same server, but each is read by a different host with its own vocabulary for the transport. `.mcp.json` is Claude Code's own project MCP config, where `type: "http"` is the canonical value ([code.claude.com/docs/en/mcp.md](https://code.claude.com/docs/en/mcp.md)); `streamable-http` is accepted there only as an alias. Root `mcp.json` follows the Agent Plugins 1.0.0 schema instead, whose `type` enum is `stdio | streamable-http | sse` and rejects `"http"` outright ([agent-plugins.org/schemas/1.0.0/mcp.schema.json](https://agent-plugins.org/schemas/1.0.0/mcp.schema.json)). `kimi.plugin.json` and the Cursor/Gemini manifests add two more dialects again (see `scripts/fixtures/`). `scripts/check-manifest-drift.mjs` guards all eight declarations of the server URL against drift while keeping each file's dialect intact; see its CI job, `manifest-drift-guard.yml`, for what it checks.

## Support

Issues in this repository, or [support@mnemoverse.com](mailto:support@mnemoverse.com).

The open-source MCP server package (MIT) lives at [mnemoverse/mcp-memory-server](https://github.com/mnemoverse/mcp-memory-server). A star there helps other builders find the project.

## License

Plugin: MIT. The bundled `agent-memory-discipline` skill is CC0-1.0 and lives at [mnemoverse/agent-memory-discipline](https://github.com/mnemoverse/agent-memory-discipline).
