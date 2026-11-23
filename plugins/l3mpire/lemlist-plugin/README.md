# lemlist plugin

Official lemlist plugin for AI assistants and coding agents. It connects your assistant to the hosted lemlist MCP server:

```
https://app.lemlist.com/mcp
```

With it, your assistant can list your campaigns and their stats, create campaigns with email and LinkedIn sequences, add and search leads, search the lemlist B2B people database, and check the deliverability of your sending domains.

This repository holds the plugin manifests and the skills. The MCP server is run by lemlist; there is nothing to build or host.

## Skills

Four workflow skills ship with the plugin. Each one runs on the tools of the lemlist MCP server and stops with setup steps when the server is not connected.

| Skill | What it does |
|---|---|
| `lemlist-find-leads` | Turns an ideal customer profile into a checked list of people from the lemlist people database (companies first, then people), then saves them to the CRM or a campaign. Asks before spending enrichment credits. |
| `lemlist-launch-campaign` | Agrees on the brief, writes a short email and LinkedIn sequence, creates the campaign, adds the leads, runs the readiness check, and launches only after an explicit yes. |
| `lemlist-campaign-report` | Pulls campaign stats per campaign, channel and step over any period, and turns them into a short diagnosis with next actions. |
| `lemlist-deliverability-check` | Runs lemlist's deliverability audit (DNS, warm-up, volume, bounces, content) read-only and explains the verdict and the fixes in order. |

## Sign-in

The server uses OAuth 2.1 (dynamic client registration and PKCE). On first use your client opens a lemlist sign-in page, and you pick the lemlist team to connect on the consent screen. Any lemlist account works, including the free trial. Enrichment and people database searches use your team's credits. An API key can be used instead of OAuth: see the setup guide below.

## Install

| Client | How |
|---|---|
| Claude Code | `/plugin marketplace add l3mpire/lemlist-plugin` then `/plugin install lemlist@lemlist` |
| Gemini CLI | `gemini extensions install https://github.com/l3mpire/lemlist-plugin` |
| Grok Build | `grok plugin install l3mpire/lemlist-plugin` |
| Kiro | [![Add to Kiro](https://kiro.dev/images/add-to-kiro.svg)](https://kiro.dev/launch/mcp/add?name=lemlist&config=%7B%22url%22%3A%22https%3A%2F%2Fapp.lemlist.com%2Fmcp%22%2C%22disabled%22%3Afalse%2C%22autoApprove%22%3A%5B%5D%7D) |
| Cursor | `.cursor-plugin/plugin.json` |
| Any MCP client | add a remote (Streamable HTTP) server with the URL `https://app.lemlist.com/mcp` |

## Manifests

- `plugin.json` and `mcp.json`: [Agent Plugins](https://agent-plugins.org) manifest (GitHub Copilot)
- `.claude-plugin/`: Claude Code plugin and marketplace
- `.cursor-plugin/plugin.json`: Cursor
- `.grok-plugin/`: Grok
- `gemini-extension.json`: Gemini CLI
- `skills/`: workflow skills (`SKILL.md` per skill)

## Links

- Setup guide: https://help.lemlist.com/en/articles/13728466-set-up-the-lemlist-mcp-server-in-your-llm-client-oauth-or-api-key
- Official MCP Registry entry: `io.github.l3mpire/lemlist`
- lemlist: https://www.lemlist.com
- Privacy policy: https://www.lemlist.com/legal/privacy-policy
- Support: https://help.lemlist.com

## License

MIT
