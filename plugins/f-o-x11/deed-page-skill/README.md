# deed.page MCP server and agent skill

[![deed.page skill on AI Agents Listing](https://aiagentslisting.com/deed-page-skill/badge.svg?claim=fa12ee67e464c1b602809f23e618375c)](https://aiagentslisting.com/mcp/deed-page-skill)
[![ToolSDK MCP Registry](https://badges.toolsdk.ai/badge/@toolsdk-remote/deed-page)](https://toolsdk-ai.github.io/toolsdk-mcp-registry/#%40toolsdk-remote%2Fdeed-page)

deed.page publishes a file or folder to a permanent `https://<slug>.deed.page/` URL in one call. No account, API key, email code, or claim link. This repo documents the hosted remote MCP server (`https://deed.page/mcp`, see [MCP server](#mcp-server)) and contains the deed.page agent skill, which does the same with one `curl` request.

It works with Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot CLI, Grok Bot, Hermes Agent, and any agent that reads `SKILL.md` files ([agentskills.io](https://agentskills.io) format).

- Website: https://deed.page
- Docs: https://deed.page/docs
- llms.txt: https://deed.page/llms.txt
- OpenAPI: https://deed.page/openapi.json
- MCP server: https://deed.page/mcp

## MCP server

deed.page runs a hosted remote MCP server. Agents use it to publish a file or folder to a permanent `https://<slug>.deed.page/` URL and then update, version, password-protect, or delete it. The source code is not in this repo; the server is hosted at the URL below.

| | |
| --- | --- |
| URL | `https://deed.page/mcp` |
| Transport | Streamable HTTP |
| MCP Registry name | `page.deed/deed-page` |
| Auth | None to start. See [Authentication](#authentication). |

### Configure

VS Code / GitHub Copilot (`.vscode/mcp.json`):

```json
{
  "servers": {
    "deed-page": {
      "type": "http",
      "url": "https://deed.page/mcp"
    }
  }
}
```

Claude Code:

```bash
claude mcp add --transport http deed-page https://deed.page/mcp
```

Any other MCP client: add a remote (Streamable HTTP) server with the URL `https://deed.page/mcp`.

### Authentication

No account, API key, or OAuth is needed. The first `publish_site` call returns an owner token (`deed_tok_...`) once. That token is the key to update or delete the sites it owns. Send it back in one of two ways:

- as the optional `Authorization: Bearer deed_tok_...` header, or
- as the `token` argument of a tool.

Keep the token secret. `rotate_token` replaces it and `revoke_token` revokes it.

### Tools

26 tools:

| Tool | What it does |
| --- | --- |
| `publish_site` | Publish files to a live permanent URL at a slug. The first call returns the owner token. |
| `update_site` | Replace a site's files, or merge in only the paths sent. |
| `get_site` | Check whether a slug is live, with its URL, version, size, and timestamps (no token needed). |
| `list_sites` | List every live site the token owns. |
| `delete_site` | Permanently remove a site. |
| `list_versions` | List a site's retained versions. |
| `restore_version` | Make a retained version live again. |
| `get_manifest` | Get the signed (Ed25519) manifest of a site version. |
| `plan_upload` | Plan a large upload: returns which files are already stored and an upload URL for each missing one. |
| `finalize_upload` | Commit a large upload as a new version. |
| `set_site_access` | Set or clear a site password. |
| `set_listing` | List a site in the public gallery, or remove it. |
| `site_analytics` | Cookieless view counts, top paths, referrers, and AI crawler counts for a site. |
| `add_domain` | Attach a custom domain and get the DNS records to create. |
| `list_domains` | List custom domains. |
| `domain_status` | Check and refresh a custom domain's verification and certificate status. |
| `remove_domain` | Remove a custom domain. |
| `whoami` | Show the plan, limits, and usage for the token. |
| `get_upgrade_link` | Get a checkout link for a paid plan. |
| `set_badge` | Show or hide the "Published with deed.page" badge. Hiding it needs a paid plan. |
| `claim_share_credit` | Free only, once per token: send the URL of the user's public X or Reddit post about deed.page for +25 sites and 50 MB per site. |
| `rotate_token` | Issue a new owner token; every site carries over. |
| `revoke_token` | Revoke the current token or all tokens. |
| `create_webhook` | Register a webhook for site and domain events. |
| `list_webhooks` | List registered webhooks. |
| `delete_webhook` | Delete a webhook. |

### Use

Ask your agent to "publish this folder to deed.page" or "host this report and give me a link". The agent calls `publish_site` with the files and answers with the live URL. To change the site later, it calls `update_site` with the same slug and token.

Free plan: 25 sites, 25 MB per site, 60 publishes per hour. Free sites are public, so do not publish secrets. Static files only. Free sites show a small "Published with deed.page" badge; Hobby ($3/mo) and Pro never do.

## Skill and plugins

The skill is one file: [`skills/deed-page/SKILL.md`](skills/deed-page/SKILL.md). The repo is also a plugin that bundles the skill with the hosted deed.page MCP server, with manifests for each agent:

| File | Format |
| --- | --- |
| [`plugin.json`](plugin.json), [`mcp.json`](mcp.json) | [Agent Plugins 1.0](https://agent-plugins.org) (Codex, Cursor, Copilot CLI, Kiro) |
| [`.grok-plugin/plugin.json`](.grok-plugin/plugin.json) | Grok Bot |
| [`.cursor-plugin/plugin.json`](.cursor-plugin/plugin.json) | Cursor |
| [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json), [`.agents/plugins/marketplace.json`](.agents/plugins/marketplace.json) | Codex |
| [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json), [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json), [`.mcp.json`](.mcp.json) | Claude Code |
| [`gemini-extension.json`](gemini-extension.json) | Gemini CLI |

Quick install for any agent:

```bash
npx skills add f-o-x11/deed-page-skill
```

## Install

### Any agent (skills.sh)

```bash
npx skills add f-o-x11/deed-page-skill
```

Add `-g` to install for all projects, or `-a claude-code`, `-a codex`, `-a cursor`, or `-a hermes-agent` to pick the agent.

### Claude Code

As a plugin:

```bash
claude plugin marketplace add f-o-x11/deed-page-skill
claude plugin install deed-page@deed-page
```

Or as a plain skill:

```bash
git clone --depth 1 https://github.com/f-o-x11/deed-page-skill /tmp/deed-page-skill
mkdir -p ~/.claude/skills && cp -r /tmp/deed-page-skill/skills/deed-page ~/.claude/skills/
```

### Codex

As a plugin (skill + MCP server):

```bash
codex plugin marketplace add f-o-x11/deed-page-skill
```

Then install `deed-page` from the plugin directory. As a plain skill:

```bash
npx skills add f-o-x11/deed-page-skill -a codex -g
```

Or inside Codex: `$skill-installer install https://github.com/f-o-x11/deed-page-skill/tree/main/skills/deed-page`

### Cursor

As a plain skill:

```bash
npx skills add f-o-x11/deed-page-skill -a cursor
```

### GitHub Copilot CLI

```bash
copilot plugin marketplace add f-o-x11/deed-page-skill
copilot plugin install deed-page@deed-page
```

### Grok Bot

The repo includes a Grok Bot plugin manifest in [`.grok-plugin/plugin.json`](.grok-plugin/plugin.json). Until it is in the Grok Bot plugin catalog, add the remote MCP server `https://deed.page/mcp`, or install the skill with `npx skills add f-o-x11/deed-page-skill`.

### Any MCP client

Add the remote MCP server `https://deed.page/mcp` (Streamable HTTP, no auth needed to start; see [MCP server](#mcp-server)). It is listed in the official MCP Registry as `page.deed/deed-page`.

### Gemini CLI

```bash
gemini extensions install https://github.com/f-o-x11/deed-page-skill
```

This installs the skill and the deed.page MCP server (`https://deed.page/mcp`, no auth) from [`gemini-extension.json`](gemini-extension.json).

### Hermes Agent

```bash
hermes skills install f-o-x11/deed-page-skill/skills/deed-page
```

Or from the deed.page well-known endpoint: `hermes skills install well-known:https://deed.page/.well-known/skills/deed-page`.

Or `npx skills add f-o-x11/deed-page-skill -a hermes-agent -g`.

## What it does

Ask your agent to "publish this", "host this report", or "give me a link". The agent runs:

```bash
curl -sS -T index.html "https://deed.page/v1/sites?slug=my-report-7f3a2c&ref=skill-gh" -H "X-Client: <agent name>"
```

and answers with the `url` from the JSON response. The first publish returns a `token` once. It is the key to update or delete that site, so keep it safe.

- Free plan: 25 sites, 25 MB per site, 60 publishes per hour.
- Free sites are public. Do not publish secrets.
- Static files only.

`?ref=skill-gh` tells deed.page that a publish came from this skill. It does not change what is published. Set `DEED_REF` to override it. You can also say where you found deed.page with the optional `X-Deed-Heard-From` header on the first publish (at most 200 characters).

## Network endpoints and credentials

- The skill calls only `https://deed.page/v1/sites` with `curl`. The MCP server is `https://deed.page/mcp`. Published sites live at `https://<slug>.deed.page/`.
- No account or API key is needed. The first publish returns a site token once; the skill saves it to `~/.config/deed-page/token` (mode 600), loads it into `DEEDPAGE_TOKEN` before later publishes so every site stays under one owner, and sends it only to `https://deed.page`.
- No install scripts, hooks, or executable code. See [SECURITY.md](SECURITY.md).

## Privacy and support

- Privacy policy: https://deed.page/privacy
- Terms: https://deed.page/terms
- Support: https://deed.page/support or ops@avatar33.com
- Security reports: ops@avatar33.com (see [SECURITY.md](SECURITY.md))

## License

MIT. Copyright (c) 2026 Avatar 8 LLC.

deed.page is operated by Avatar 8 LLC. Contact: ops@avatar33.com. Report abuse: https://deed.page/abuse.
