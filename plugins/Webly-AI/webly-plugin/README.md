# Webly skill and plugin

[Webly](https://webly.ai) is website hosting for agents. This repo ships the
`webly` skill: your agent publishes a site in seconds with no account, and when
you want to keep it, you sign in once and the site becomes yours, editable over
Webly's MCP server.

## Install

Paste this into Claude Code, Codex, Cursor or any agent that can run commands:

```
Set up Webly, website hosting for agents.
If I have npm: npx skills add Webly-AI/webly-plugin --skill webly -g
If not: curl -fsSL https://webly.ai/install.sh | bash
Then read https://api.webly.ai/docs and ask me what I'd like to publish.
```

Or install it yourself:

| Where | Command |
| --- | --- |
| Any agent, with npm | `npx skills add Webly-AI/webly-plugin --skill webly -g` |
| Any agent, no npm | `curl -fsSL https://webly.ai/install.sh \| bash` |
| Claude Code plugin | `/plugin marketplace add Webly-AI/webly-plugin` then `/plugin install webly@webly` |
| Cursor plugin | Install **Webly** from the [Cursor Marketplace](https://cursor.com/marketplace) |
| Gemini CLI extension | `gemini extensions install https://github.com/Webly-AI/webly-plugin` then `/mcp auth webly` |

The skill goes into `~/.claude/skills/webly` and `~/.agents/skills/webly`, so it's
there in every folder and every new session. The Claude Code plugin also adds the
Webly MCP server and a session-start hook; the Cursor plugin adds the skill and the MCP server. The helper needs Node 18+.

## How it works

1. **Publish without an account.** "Put this folder online." The agent runs the
   bundled helper and gives you a `*.webly.site` link. The site is live and
   editable for 24 hours and can be claimed for 7 days; unclaimed sites are
   deleted.
2. **Keep it.** "Keep my site" or "make me an account." The agent registers the
   Webly MCP server and opens the sign-in page for you. You approve once, and the
   site moves into your workspace, permanently.
3. **Build on it.** Over MCP the agent gets drafts, a quality gate, publish only
   when you say yes, rollback, a blog and CMS, forms, custom domains and analytics.

Everything the agent needs to pick up later is saved on your computer
(`~/.webly/`), so a new session, `/clear` or a restart carries on where you left
off. The secret token that proves you own an unclaimed site never leaves that
file except when the claim page opens in your browser.

Already signed in? Ask your agent to "connect my Webly account".

On the consent page you pick an access level:

| Scope | Role | What the agent may do |
| --- | --- | --- |
| `webly:content` | `content_editor` | Read sites and pages; create, update and publish CMS items and blog posts; upload assets |
| `webly:edit` | `full_editor` | The above plus source files, deploys, publish / rollback / unpublish, CMS schema, domains |
| `webly:admin` | `admin` | The above plus create/rename/delete websites, manage API keys, read the audit log |

No browser on this machine (server, container, CI)? Create a key at
[app.webly.ai/dashboard/keys](https://app.webly.ai/dashboard/keys) and add it as a
header on the MCP server; see [webly.ai/agent.md](https://webly.ai/agent.md),
Phase 3b.

## Updating

The skill checks for a newer release and tells your agent. To update by hand:

```bash
npx skills update webly -g               # npx skills installs
curl -fsSL https://webly.ai/install.sh | bash   # install.sh installs
claude plugin update webly@webly         # the Claude Code plugin
```

## Contents

```
.claude-plugin/marketplace.json   marketplace manifest
.cursor-plugin/plugin.json        Cursor plugin manifest (skills/webly + Webly MCP server)
assets/logo.svg                   marketplace logo
gemini-extension.json             Gemini CLI extension (Webly MCP server, GEMINI.md, skills/)
GEMINI.md                         Gemini CLI context
install.sh                        installs skills/webly for Claude Code and Codex
skills/webly/                     the skill, for npx skills and install.sh
plugins/webly/
  .claude-plugin/plugin.json      plugin manifest
  .mcp.json                       Webly MCP server (https://api.webly.ai/v1/mcp)
  hooks/hooks.json                session start: `webly.mjs doctor --brief`
  skills/webly/                   the same skill
```

The skill and its helper are generated from the Webly repo
(`skills/webly`, `scripts/webly.mjs`) by `scripts/sync-plugin.sh`. Edit them there,
not here. The full API and MCP reference is at
[api.webly.ai/docs](https://api.webly.ai/docs).

## Development

```bash
claude plugin validate .
claude plugin validate plugins/webly
/plugin marketplace add ./path/to/webly-plugin   # test locally
```

## License

Apache-2.0
