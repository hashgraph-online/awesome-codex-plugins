# Codex Reset MCP server

[![smithery badge](https://smithery.ai/badge/suvadadepolo/codex-reset)](https://smithery.ai/servers/suvadadepolo/codex-reset)

Read-only facts about OpenAI Codex usage-limit resets, served by [codex-reset.com](https://codex-reset.com/) over the Model Context Protocol.

- **Endpoint:** `https://codex-reset.com/mcp`
- **Transport:** Streamable HTTP, JSON-RPC 2.0, protocol `2025-06-18`. POST only; a GET answers 405.
- **Auth:** none. No API key, no sign-up, no session.
- **Cost:** free, with credit (see [Terms](#terms)).
- **Docs:** [codex-reset.com/developers](https://codex-reset.com/developers) · [terminal walkthrough on dev.to](https://dev.to/codexreset/is-a-codex-usage-limit-reset-coming-check-from-your-terminal-with-a-free-api-or-mcp-3enb) · [server card](https://codex-reset.com/.well-known/mcp/server-card.json) · [llms.txt](https://codex-reset.com/llms.txt)

This repository holds the client configuration and directory metadata for the hosted server. There is nothing to install or run: the server lives at the endpoint above, and its source is not published here.

## Tools

All three tools are read-only (`readOnlyHint: true`) and read the same data as the site's public JSON API, so an agent and a browser never disagree.

| Tool | Returns | Arguments |
|---|---|---|
| `get_reset_forecast` | Probability of a Codex usage-limit reset in the next 24 and 48 hours, confidence, the last confirmed reset and any active official signal. A forecast, not a promise. | `locale` |
| `get_reset_timeline` | Dated record of verified resets and related announcements, newest first, each with its source URL. | `group` (`reset` \| `boost` \| `unlock` \| `credits`), `from`, `to` (`YYYY-MM-DD`), `limit` (1–50, default 10), `locale` |
| `get_codex_status` | Current Codex service state, to tell an outage apart from a usage limit. | `locale` |

`locale` is `en`, `zh`, `ja` or `es` and changes only the human-readable copy.

## Example prompts

- "Is Codex likely to reset its usage limits in the next 24 hours?"
- "When was the last verified Codex usage-limit reset, and where was it announced?"
- "List every Codex reset from August 2026 with its source link."
- "I'm getting errors in Codex. Is that an outage or did I hit my usage limit?"
- "Should I wait for a reset or keep working? Check the forecast and the service status."

## Setup

### Claude Code

```sh
claude mcp add --transport http codex-reset https://codex-reset.com/mcp
```

Or in `.mcp.json`:

```json
{
  "mcpServers": {
    "codex-reset": { "type": "http", "url": "https://codex-reset.com/mcp" }
  }
}
```

This repository is also a Claude Code plugin (`.claude-plugin/plugin.json` + `.mcp.json`).

### Codex CLI / IDE extension

`~/.codex/config.toml`:

```toml
[mcp_servers.codex-reset]
url = "https://codex-reset.com/mcp"
```

This repository is also a Codex plugin (`.codex-plugin/plugin.json`: the MCP server plus a `codex-reset` skill), listed in [awesome-codex-plugins](https://github.com/hashgraph-online/awesome-codex-plugins) and the [HOL plugin registry](https://hol.org/registry/plugins). The two `config.toml` lines above are all a plain Codex setup needs.

### Cursor

`.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global):

```json
{
  "mcpServers": {
    "codex-reset": { "url": "https://codex-reset.com/mcp" }
  }
}
```

### VS Code (GitHub Copilot)

`.vscode/mcp.json`:

```json
{
  "servers": {
    "codex-reset": { "type": "http", "url": "https://codex-reset.com/mcp" }
  }
}
```

### Gemini CLI

```sh
gemini extensions install https://github.com/suvadadepolo-blip/codex-reset-mcp
```

### Clients that only speak stdio

```sh
npx -y mcp-remote https://codex-reset.com/mcp
```

### Check it by hand

```sh
curl -sS https://codex-reset.com/mcp \
  -H 'content-type: application/json' \
  -H 'accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## Where it is listed

- Official MCP Registry: `io.github.suvadadepolo-blip/codex-reset`
- [Smithery](https://smithery.ai/servers/suvadadepolo/codex-reset)
- [cursor.directory](https://cursor.directory/plugins/codex-reset)
- [Glama](https://glama.ai/mcp/connectors/com.codex-reset/codex-reset)

## Terms

Reuse is free and keyless on one condition: credit. A site, app, bot message, dashboard, MCP tool or API that passes this data on names the source and links to it on the same surface: "Data: codex-reset.com", linked to https://codex-reset.com/. Personal use needs no visible credit. Full wording: [codex-reset.com/developers](https://codex-reset.com/developers) and the [terms of use](https://codex-reset.com/terms).

- Privacy: [codex-reset.com/privacy](https://codex-reset.com/privacy). The server keeps no session and needs no account.
- Contact: hello@codex-reset.com

Independent community project, not affiliated with OpenAI. "Codex" and "ChatGPT" are trademarks of OpenAI and are used only to describe what is being tracked.

## License

The configuration files in this repository are MIT-licensed. The data served by the endpoint is covered by the terms above.
