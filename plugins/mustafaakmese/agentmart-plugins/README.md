# AgentMart plugin

AgentMart (https://agentmart.ciphyr.ai), run by Ciphyr Tech OÜ in Estonia, hosts the parts of an AI
agent's work that need a server that stays on after the session ends: always-on utilities (webhook inbox,
memory locker, wake-up calls, share link, uptime watch, form inbox, ask my human, heartbeat monitor, owner
reminders, durable queue, Project Blueprint), mail tools (an email list check that finds addresses that
would bounce, a sender health check of a domain's email DNS, and a hosted unsubscribe list) and tested
TypeScript code kits (among them email campaigns and invitations). Items are paid from a prepaid balance
that the human tops up on Stripe's page; the agent asks the human before every purchase (or follows a
standing rule the human set).

MIT covers the files in this repository. The AgentMart service itself is proprietary, run by Ciphyr Tech OÜ.

This repository is one plugin for many coding agents. It connects the AgentMart MCP server and adds
two skills:

- **check-the-shelf**: when a task needs one of the always-on parts above and nothing the user already
  has covers it, compare a ready part with building it and with free options, then let the human
  choose.
- **agentmart-buying-rules**: sign in safely, get funds only through the human, and buy only with the
  human's clear yes.

## When not to use it

- For the user's own product code, or when they asked you to build the part yourself.
- When the project already has a service for it (a queue, a scheduler, an inbox).
- When a free local option is enough for the task.

## Install

Tested by us: Claude Code. The other lines follow each app's own documentation; if one fails, please open
an issue.

| App | How |
|---|---|
| Claude Code | `claude plugin marketplace add mustafaakmese/agentmart-plugins`, then `claude plugin install agentmart@agentmart-plugins` |
| Codex | `codex plugin marketplace add mustafaakmese/agentmart-plugins`, then `/plugins` |
| Cursor | the button below adds the MCP server; for the skills too, copy this repository to `~/.cursor/plugins/local/agentmart` (a Cursor Marketplace listing is not there yet) |
| VS Code (agent plugins) | "Chat: Install Plugin From Source" with this repository's address |
| Google Antigravity | `agy plugin install https://github.com/mustafaakmese/agentmart-plugins` |
| Gemini CLI (now for companies; individuals use Antigravity) | `gemini extensions install https://github.com/mustafaakmese/agentmart-plugins` |
| Devin (plugins are a beta for enterprises) | `devin plugins install mustafaakmese/agentmart-plugins` |
| Skills only, any agent | `npx skills add mustafaakmese/agentmart-plugins --skill check-the-shelf` |
| Any MCP client | add the remote server `https://agentmart.ciphyr.ai/mcp` (streamable HTTP, OAuth) |

<a href="https://cursor.com/en/install-mcp?name=agentmart&config=eyJ1cmwiOiJodHRwczovL2FnZW50bWFydC5jaXBoeXIuYWkvbWNwIn0%3D">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://cursor.com/deeplink/mcp-install-light.svg">
    <img alt="Add the AgentMart MCP server to Cursor" src="https://cursor.com/deeplink/mcp-install-dark.svg" height="32">
  </picture>
</a>

## Sign in

Your app signs in with OAuth on AgentMart's approval page (one click, no password), so no token
appears in the chat. In Claude Code: type `/mcp`, pick `plugin:agentmart:agentmart`, choose
**Authenticate**. In Gemini CLI: `/mcp auth agentmart`. An approval alone gives the app an empty
passport; to use an account's balance, the owner gets a one-time code on the Add an AI app page of
agentmart.ciphyr.ai and pastes it on the approval page. Searching and reading the catalog need no
sign-in.

## What it runs, sends and fetches

- No local code, no hooks, no scripts, no rules that write to your files.
- One remote MCP server: `https://agentmart.ciphyr.ai/mcp`. Your client talks to it directly.
- Whatever the agent sends to AgentMart's tools (search words, items it stores in a utility, messages
  it schedules) goes to AgentMart's servers. Privacy notice: https://agentmart.ciphyr.ai/privacy.
  Terms: https://agentmart.ciphyr.ai/terms.
- Nothing is bought without a tool call that your client shows you, and the skills tell the agent to
  ask you first. Prices are never written here: the agent reads them from the catalog.

## Files

| Path | Read by |
|---|---|
| `plugin.json`, `mcp.json` | Agent Plugins 1.0: Codex, Cursor, VS Code, Copilot (and Antigravity reads `plugin.json`) |
| `.claude-plugin/plugin.json`, `.mcp.json`, `.claude-plugin/marketplace.json` | Claude Code (and skills.sh) |
| `.agents/plugins/marketplace.json`, `.codex-plugin/plugin.json` | Codex, and plugin scanners |
| `.cursor-plugin/plugin.json` | Cursor and cursor.directory |
| `.devin-plugin/plugin.json` | Devin (with the server inline) |
| `mcp_config.json` | Google Antigravity, next to `plugin.json` |
| `gemini-extension.json`, `GEMINI.md` | Gemini CLI |
| `skills/` | Every app above |

## Security

See `SECURITY.md`. How to report a security problem: https://agentmart.ciphyr.ai/.well-known/security.txt.

## License

The files in this repository (manifests, skills) are under the MIT license in `LICENSE`. The AgentMart
name and logo are not licensed under MIT. The AgentMart service and the items it sells are covered by
https://agentmart.ciphyr.ai/terms.

## Support

https://agentmart.ciphyr.ai/support, or let your agent use the `send_feedback` tool. The manual for
agents is https://agentmart.ciphyr.ai/llms.txt (an index); the whole manual in one file is
https://agentmart.ciphyr.ai/llms-full.txt.
