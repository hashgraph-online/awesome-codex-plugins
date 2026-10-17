# Sendsets: the cold email API for AI agents

[Sendsets](https://sendsetsapi.com) gives AI agents a programmable way to run cold email. An agent (Claude Code, Codex, Cursor, Gemini CLI, ChatGPT, or your own code) can connect sending mailboxes, warm them up, build and launch outbound campaigns, add leads, and read and answer replies through an MCP server, a CLI, or a REST API instead of a sales dashboard.

This repository is the public, agent-facing home of Sendsets:

| What | Where |
|---|---|
| Remote MCP server | `https://api.sendsetsapi.com/v1/mcp` (streamable HTTP, OAuth 2.1 or API key) |
| Agent skills (`SKILL.md`) | [`skills/send-cold-email`](skills/send-cold-email/SKILL.md), [`skills/sendsets`](skills/sendsets/SKILL.md), [`skills/sendsets-cli`](skills/sendsets-cli/SKILL.md) |
| Claude Code plugin marketplace | [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json) |
| Codex plugin marketplace | [`.agents/plugins/marketplace.json`](.agents/plugins/marketplace.json), [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json) |
| Agent Plugins manifest | [`plugin.json`](plugin.json), [`mcp.json`](mcp.json) ([agent-plugins.org](https://agent-plugins.org)) |
| Gemini CLI extension | [`gemini-extension.json`](gemini-extension.json) |
| MCP Registry manifest | [`server.json`](server.json) (`io.github.AddisonHoff/sendsets`) |
| OpenAPI 3.1 spec | [openapi.json](https://gist.githubusercontent.com/AddisonHoff/abfb01a48dc15edef07cb188cbb70d04/raw/openapi.json) |
| Docs | [docs.sendsetsapi.com](https://docs.sendsetsapi.com/api/) |

Sign up at [app.sendsetsapi.com](https://app.sendsetsapi.com/auth/register). Free for up to 10 mailboxes.

## What an agent can do with it

The MCP server and the REST API expose the same service-layer tools. What a credential can see is limited by the scopes it was granted.

- **Campaigns**: create a draft, add and edit sequence steps, pick sender mailboxes, view leads, logs and stats, start and stop
- **Leads and contacts**: add, search, tag, bulk edit, read timelines and sent mail, manage segments
- **Mailboxes**: list and inspect connected mailboxes, adjust limits, toggle warmup, set tracking domains, check warmup standing
- **Inbox and replies**: list and read threads, draft and send replies, label, snooze, cancel scheduled sends
- **Runs**: durable, idempotent, preflighted campaign runs (`create_run`, `get_run`, `list_runs`, `cancel_run`)
- **Suppressions, analytics, webhooks**: manage the do-not-contact list, read dashboard analytics, manage signed webhooks

Send-class tools (`start_campaign`, `compose_email`, `send_reply`, and an autonomous `create_run`) go through a credential-bound policy. A call returns `executed`, `awaiting_approval` (a person approves it in the dashboard within 30 minutes), or `blocked`. Approval can never override a missing opt-out, a suppression, or a mailbox health check.

## Connect the MCP server

The server advertises OAuth 2.1 protected-resource metadata (RFC 9728) and supports dynamic client registration, so MCP clients that speak OAuth sign you in through the browser with no key to paste. A static `ssk_` API key from the dashboard works too, as `Authorization: Bearer ssk_...`.

**Claude Code**

```bash
claude mcp add --transport http sendsets https://api.sendsetsapi.com/v1/mcp
```

Or install the plugin, which adds the MCP server and the skills together:

```text
/plugin marketplace add AddisonHoff/sendsets
/plugin install sendsets@sendsets
```

**Claude (claude.ai and Claude Desktop)**: Settings > Connectors > Add custom connector, URL `https://api.sendsetsapi.com/v1/mcp`.

**Codex**

```bash
codex plugin marketplace add AddisonHoff/sendsets     # MCP server + skills as a plugin
```

or just the MCP server:

```bash
codex mcp add sendsets --url https://api.sendsetsapi.com/v1/mcp
codex mcp login sendsets
```

**Cursor** (`~/.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "sendsets": { "url": "https://api.sendsetsapi.com/v1/mcp" }
  }
}
```

**VS Code** (`.vscode/mcp.json`)

```json
{
  "servers": {
    "sendsets": { "type": "http", "url": "https://api.sendsetsapi.com/v1/mcp" }
  }
}
```

**Gemini CLI**

```bash
gemini extensions install https://github.com/AddisonHoff/sendsets
```

**Any client with a static key**

```json
{
  "mcpServers": {
    "sendsets": {
      "type": "http",
      "url": "https://api.sendsetsapi.com/v1/mcp",
      "headers": { "Authorization": "Bearer ssk_..." }
    }
  }
}
```

## Install the skills

`send-cold-email` is the direct path: take a lead list and send a cold email sequence with follow-ups, from mailbox check to launch and replies. The `sendsets` skill teaches an agent to read your product, propose five outbound workflows that use the product itself, then build and run the one you pick. The `sendsets-cli` skill is the full reference for driving Sendsets from a terminal.

```bash
npx skills add AddisonHoff/sendsets
```

Or copy [`skills/sendsets`](skills/sendsets) into `~/.claude/skills/` (Claude Code) or `~/.codex/skills/` (Codex). The same files are served at `https://sendsetsapi.com/skills/sendsets/SKILL.md`, and [`https://sendsetsapi.com/claude.md`](https://sendsetsapi.com/claude.md) is a one-link starting point for any coding agent.

## CLI

```bash
brew install addisonhoff/tap/sendsets                 # macOS, Linux
sendsets login --hostname sendsetsapi.com
sendsets doctor --json
```

Windows: `scoop bucket add sendsets https://github.com/AddisonHoff/homebrew-tap`, then `scoop install sendsets`. Archives and `checksums.txt` for every platform are on [sendsets-releases](https://github.com/AddisonHoff/sendsets-releases/releases/latest). The CLI signs in as a person and speaks only the public REST API; every command takes `--json`.

## REST API

Base URL `https://api.sendsetsapi.com/v1`. Errors carry a stable `code` and `request_id`, lists use `data` plus cursor `pagination`, and side-effectful writes accept an `Idempotency-Key`. Spec: [openapi.json](https://gist.githubusercontent.com/AddisonHoff/abfb01a48dc15edef07cb188cbb70d04/raw/openapi.json). Reference: [docs.sendsetsapi.com/api](https://docs.sendsetsapi.com/api/).

## What this plugin connects to

- The MCP server at `https://api.sendsetsapi.com/v1/mcp`, over HTTPS, authenticated with your own OAuth sign-in or API key. Every tool call reads or changes data in your Sendsets workspace; send tools deliver real email from your connected mailboxes.
- The skills may tell the agent to install the `sendsets` CLI with Homebrew or Scoop from [AddisonHoff/homebrew-tap](https://github.com/AddisonHoff/homebrew-tap), or from a release archive checked against its published `checksums.txt`. The CLI talks only to `https://api.sendsetsapi.com`.
- Nothing else. The plugin has no hooks, no local server and no scripts that run on install, and its MCP configuration never reads credentials from your environment.

## Safety defaults

Sendsets is conservative by default: 50 campaign emails per mailbox per day, 600 seconds between sends from one mailbox, gradual warmup, automatic suppression on bounces, complaints and unsubscribes, and a stop on reply. A test send and a live launch are separate decisions, and an agent should not launch a campaign unless the user asked it to send.

## License

The skills and manifests in this repository are licensed under Apache-2.0.
