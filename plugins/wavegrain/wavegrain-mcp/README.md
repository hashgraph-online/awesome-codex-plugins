<p align="center">
  <img src="assets/wavegrain-wave-icon-512.png" alt="Wavegrain" width="96" height="96">
</p>

# Wavegrain MCP server

[![mcptry](https://mcptry.com/badge/com.wavegrain/mcp)](https://mcptry.com/servers/com.wavegrain/mcp)
[![Listed on Skillselion](https://skillselion.com/badge/mcp/tool/com.wavegrain/mcp.svg)](https://skillselion.com/mcp/tool/com.wavegrain/mcp)

Curated TikTok slideshows and Instagram carousels for your brand on autopilot, made and scheduled from your AI assistant.

[Wavegrain](https://wavegrain.com) makes curated TikTok slideshows and Instagram carousels for your brand on autopilot.
Its MCP server lets Claude, ChatGPT, Claude Code, Codex, Cursor and any other MCP client work in your Wavegrain account: plan posts for a brand, make slideshows, change slide text, put posts on your Calendar and export them.

Full docs, the tool list and limits: **https://wavegrain.com/mcp**

This repo holds the setup files, a plugin for Claude Code and an agent skill.
The server itself is hosted by Wavegrain; there is nothing to install or run.

## Server

| | |
| --- | --- |
| Address | `https://wavegrain.com/api/mcp` |
| Transport | Streamable HTTP |
| Sign-in | OAuth 2.1 for claude.ai, the Claude app and ChatGPT; an access key for everything else |
| Registry name | `com.wavegrain/mcp` ([server.json](server.json)) |

You need a Wavegrain account.
[Sign up](https://wavegrain.com/signup).

## Connect

### Claude (claude.ai, desktop and phone)

1. In Claude on the web or the desktop app, open Customize, then Connectors. Choose Add, then Add custom connector.
2. Name it Wavegrain and paste `https://wavegrain.com/api/mcp`.
3. Sign in to Wavegrain in the window that opens, then choose the permissions and the daily credit limit.

A connector you add on claude.ai also works in the Claude app on your phone.
More: [Wavegrain for Claude](https://wavegrain.com/mcp/claude).

### ChatGPT

1. In ChatGPT, open Plugins, press the plus button, then choose Add custom MCP server.
2. Name it Wavegrain, paste `https://wavegrain.com/api/mcp`, and choose OAuth to sign in.
3. Sign in to Wavegrain in the window that opens, then choose the permissions and the daily credit limit.

Your ChatGPT plan or workspace must allow custom MCP servers.
More: [Wavegrain for ChatGPT](https://wavegrain.com/mcp/chatgpt).

### Kiro

[![Add to Kiro](https://kiro.dev/images/add-to-kiro.svg)](https://kiro.dev/launch/mcp/add?name=wavegrain&config=%7B%22url%22%3A%22https%3A%2F%2Fwavegrain.com%2Fapi%2Fmcp%22%2C%22disabled%22%3Afalse%2C%22autoApprove%22%3A%5B%5D%7D)

1. Press Add to Kiro above, and let your browser open Kiro.
2. Kiro adds the server `https://wavegrain.com/api/mcp`. Sign in to Wavegrain in the window that opens, then choose the permissions and the daily credit limit.

### Tools that use an access key

Make a key in Wavegrain under Settings, AI agents, and give it only the permissions it needs.
Save it in the `WAVEGRAIN_MCP_TOKEN` environment variable, so the key is not written into a config file you might share or commit.

**Claude Code, as a plugin** (adds the server and the Wavegrain skill):

```text
/plugin marketplace add wavegrain/wavegrain-mcp
/plugin install wavegrain@wavegrain
```

**Claude Code, server only:**

```bash
claude mcp add --transport http --scope user wavegrain https://wavegrain.com/api/mcp --header "Authorization: Bearer $WAVEGRAIN_MCP_TOKEN"
```

**Codex:**

```bash
codex mcp add wavegrain --url https://wavegrain.com/api/mcp --bearer-token-env-var WAVEGRAIN_MCP_TOKEN
```

**Cursor**, in `~/.cursor/mcp.json` (keep any servers already in it):

```json
{
  "mcpServers": {
    "wavegrain": {
      "url": "https://wavegrain.com/api/mcp",
      "headers": { "Authorization": "Bearer ${env:WAVEGRAIN_MCP_TOKEN}" }
    }
  }
}
```

More: [Wavegrain for Cursor](https://wavegrain.com/mcp/cursor).

**VS Code:**

```bash
code --add-mcp '{"name":"wavegrain","type":"http","url":"https://wavegrain.com/api/mcp","headers":{"Authorization":"Bearer ${env:WAVEGRAIN_MCP_TOKEN}"}}'
```

**Any other MCP tool:** use the address `https://wavegrain.com/api/mcp`, the Streamable HTTP transport and the header `Authorization: Bearer <your access key>`.
If the tool can sign in with OAuth, give it only the address.

## Skill

[`skills/wavegrain/SKILL.md`](skills/wavegrain/SKILL.md) tells an agent when to use Wavegrain and which tools to call for the common jobs.
Install it with any tool that reads agent skills, for example:

```bash
npx skills add wavegrain/wavegrain-mcp
```

## What it can do

Each key or connected app has its own permissions:

- **read**: your brands and each brand's brief, formats, slideshows, Calendar, image collections, credits and where each post stands. Reading is free.
- **write**: change saved work without spending credits: slide text, photos and order, captions, Calendar slots, brand settings and exports.
- **generate**: spend your normal credits to make brands, slideshows and images, within the limit each call names and the key's daily limit.
- **post**: post a slideshow to your connected accounts, after you confirm a summary of what goes where. Never on by default.
- **approve**: approve finished slideshows for posting. Off until you turn it on for that key or app in Settings.

The full list of tools is on [wavegrain.com/mcp](https://wavegrain.com/mcp).

## Example prompts

- "Copy and create this slideshow for my brand: <link>"
- "Make a 6-slide carousel about morning routines for my active brand. Spend at most 10 credits."
- "Plan a week of posts for my brand and put them on my Wavegrain Calendar."
- "Change the headline on slide 2 of my latest slideshow, then export it."

## Files

| File | For |
| --- | --- |
| [`server.json`](server.json) | The entry in the official MCP Registry |
| [`.mcp.json`](.mcp.json) | The server for the Claude Code plugin (reads `WAVEGRAIN_MCP_TOKEN`) |
| [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json) | The Claude Code plugin |
| [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json) | Lets `/plugin marketplace add wavegrain/wavegrain-mcp` find the plugin |
| [`skills/wavegrain/SKILL.md`](skills/wavegrain/SKILL.md) | The agent skill |

## Links

- Website: https://wavegrain.com
- MCP docs: https://wavegrain.com/mcp
- Developer docs: https://wavegrain.com/developers
- Privacy: https://wavegrain.com/privacy
- Support: support@wavegrain.com

The files in this repo are under the [MIT license](LICENSE).
The Wavegrain name and logo are not.
