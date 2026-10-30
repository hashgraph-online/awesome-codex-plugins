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

## Other hosts: OpenClaw and Hermes Agent

Both hosts install this repository as a plugin and load its skills, but neither starts a sign-in for a server that comes from a plugin. Add the hosted server once as the host's own entry, under the same name, and sign in there.

### OpenClaw

```sh
openclaw plugins install mnemoverse --marketplace https://github.com/mnemoverse/claude-plugin
openclaw plugins inspect mnemoverse
openclaw mcp add mnemoverse --transport streamable-http --url https://mcp.mnemoverse.com/mcp --auth oauth
openclaw mcp login mnemoverse
```

`mcp login` prints the sign-in URL instead of opening a browser, so open it yourself and approve the scopes; it waits on a loopback callback, which the Mnemoverse sign-in accepts on any port. `openclaw mcp probe mnemoverse` lists the tools once you are signed in. Full walkthrough: [Install by host, OpenClaw](https://mnemoverse.com/docs/api/install-by-host#openclaw).

### Hermes Agent

```sh
hermes plugins install mnemoverse/claude-plugin --no-enable
hermes plugins list
hermes plugins enable <name printed by hermes plugins list>
```

Then add the server to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  mnemoverse:
    url: "https://mcp.mnemoverse.com/mcp"
    auth: oauth
```

and run `hermes mcp login mnemoverse` (Hermes opens the browser and waits on a loopback callback). Check with `hermes mcp test mnemoverse`. Keep the name `mnemoverse`: the native entry shadows the plugin's copy, which cannot sign in. Full walkthrough: [Install by host, Hermes Agent](https://mnemoverse.com/docs/api/install-by-host#hermes-agent).

## First run: sign in once, no API key

The server at `https://mcp.mnemoverse.com/mcp` uses OAuth 2.1 with PKCE. Installing the plugin does not open anything by itself: run `/mcp`, select the Mnemoverse server (from this plugin it is listed as `plugin:mnemoverse:mnemoverse`) and choose Authenticate, then sign in to your Mnemoverse account in the browser (free tier at [console.mnemoverse.com](https://console.mnemoverse.com?utm_source=github&utm_medium=readme&utm_campaign=claude-plugin), no credit card) and grant the requested scopes, which include `memory:read` and `memory:write`. There is no API key to paste. To disconnect, remove the server from your client; resetting your password in the console can also disconnect all connected apps at once. The bundled `setup` skill walks Claude through this if anything goes wrong.

## What you get

**Three commands:**

| Command | What it does |
| --- | --- |
| `/mnemoverse:remember` | save a durable fact, decision, or correction, one fact per memory |
| `/mnemoverse:recall` | search memory before acting, with provenance, surfacing contradictions instead of hiding them |
| `/mnemoverse:memory-status` | counts, domains, and the newest memories |

**Seven skills:**

- `agent-memory-discipline` (CC0, backend-neutral): standing rules for when to recall and what is worth saving. It names no vendor and works on any memory backend; it ships here so the connected memory is actually used.
- `setup`: guides Claude through connecting and troubleshooting the MCP server.
- `memory-search`: searches memory before answering, then rates which recalled memories helped.
- `memory-save`: saves a decision, preference, correction or lesson as one self-contained fact, never a secret.
- `memory-catch-up`: lists what was added since a given time, in personal memory or in a shared room (beta).
- `memory-onboard`: seeds memory with a project's conventions and decisions from its README, CLAUDE.md and AGENTS.md.
- `mnemoverse-docs`: for developers adding Mnemoverse memory to their own app or agent; picks the form and points to the docs page.

**The tools come from the remote server itself**: reading and writing memories, a newest-first listing, stats, usefulness feedback, shared rooms (beta), and a vault alias listing (aliases only, values are never returned). The current list, with descriptions and schemas, is at the server's [card](https://mcp.mnemoverse.com/.well-known/mcp/server-card.json).

## Try these

1. `Remember that this project uses pnpm, not npm. We decided this after a lockfile conflict on 2026-08-01.`
2. `Before you touch the billing module, recall what we have decided about it in past sessions.`
3. `/mnemoverse:memory-status` after a week of use, to see what your sessions have been saving.

## What gets stored, and what does not

The plugin stores only what you or Claude explicitly save through the memory tools: single facts, decisions, corrections. It does not record conversations, does not read your chat history, and the bundled skill explicitly refuses to persist secrets, API keys, passwords, payment data, or personal identifiers.

Memory content lives in your Mnemoverse account. Privacy policy: [mnemoverse.com/docs/legal/privacy-policy](https://mnemoverse.com/docs/legal/privacy-policy).

## Troubleshooting

- **No sign-in prompt**: Claude Code does not open the browser by itself. Run `/mcp`, select `plugin:mnemoverse:mnemoverse` and choose Authenticate. If the server is not listed, add it for all your projects with `claude mcp add --transport http --scope user mnemoverse https://mcp.mnemoverse.com/mcp`; it then appears in `/mcp` as `mnemoverse`, and you authenticate it the same way.
- **`401` after it used to work**: the token expired; the next tool call normally refreshes it. If not, run `/mcp`, select the server and choose Re-authenticate.
- **`malformed_token` in logs**: the bearer token is neither an OAuth token from the sign-in nor a Mnemoverse API key, for example a key copied without its `mk_live_` prefix, or a placeholder left in a config. Since 2026-10-19 the remote endpoint accepts either: a host that cannot complete the sign-in can send an API key as `Authorization: Bearer mk_live_...` ([details](https://mnemoverse.com/docs/api/remote-mcp-server#with-an-api-key-instead-of-the-sign-in)). A revoked or unknown key gets `invalid_api_key` instead.

More: [docs](https://mnemoverse.com/docs/api/remote-mcp-server).

## Why `.mcp.json` says `http` and `mcp.json` says `streamable-http`

Both files point at the same server, but each is read by a different host with its own vocabulary for the transport. `.mcp.json` is Claude Code's own project MCP config, where `type: "http"` is the canonical value ([code.claude.com/docs/en/mcp.md](https://code.claude.com/docs/en/mcp.md)); `streamable-http` is accepted there only as an alias. Root `mcp.json` follows the Agent Plugins 1.0.0 schema instead, whose `type` enum is `stdio | streamable-http | sse` and rejects `"http"` outright ([agent-plugins.org/schemas/1.0.0/mcp.schema.json](https://agent-plugins.org/schemas/1.0.0/mcp.schema.json)). `kimi.plugin.json` and the Cursor/Gemini manifests add two more dialects again (see `scripts/fixtures/`). `scripts/check-manifest-drift.mjs` guards all eight declarations of the server URL against drift while keeping each file's dialect intact; see its CI job, `manifest-drift-guard.yml`, for what it checks.

## Support

Issues in this repository, or [support@mnemoverse.com](mailto:support@mnemoverse.com).

The open-source MCP server package (MIT) lives at [mnemoverse/mcp-memory-server](https://github.com/mnemoverse/mcp-memory-server). A star there helps other builders find the project.

## License

Plugin: MIT. The bundled `agent-memory-discipline` skill is CC0-1.0 and lives at [mnemoverse/agent-memory-discipline](https://github.com/mnemoverse/agent-memory-discipline).
