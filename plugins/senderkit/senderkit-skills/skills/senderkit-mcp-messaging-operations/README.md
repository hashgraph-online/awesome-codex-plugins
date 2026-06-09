# SenderKit MCP Messaging Operations Skill

Portable AI-agent instructions for using the SenderKit MCP connector safely.

This open-source skill lives in the [`senderkit/senderkit-skills`](https://github.com/senderkit/senderkit-skills) GitHub repository under `skills/senderkit-mcp-messaging-operations/`. It helps Claude, Codex, Cursor-style agents, and other MCP-capable assistants use SenderKit MCP tools for messaging operations without overclaiming unsupported connector behavior.

## What it does

- Confirms whether the SenderKit MCP connection is in test or live mode.
- Sends registered SenderKit templates with variables, metadata, scheduling, idempotency, and email-only options.
- Sends raw one-off email, SMS, push, or web-push content when explicitly requested.
- Lists and inspects templates before using uncertain slugs.
- Lists, filters, and inspects messages for status or delivery debugging.
- Cancels messages only when they are still scheduled or queued.

## Contents

```text
skills/senderkit-mcp-messaging-operations/
|-- AGENTS.md
|-- README.md
|-- SKILL.md
|-- agents/
|   `-- openai.yaml
|-- llms.txt
`-- references/
    `-- sources.md
```

## Use with coding agents

Reuse from GitHub:

```bash
git clone https://github.com/senderkit/senderkit-skills.git
```

Codex (OpenAI) discovers skills from `.agents/skills/` directories — user scope (every repo) or a single repo's scope:

```bash
mkdir -p ~/.agents/skills
cp -R senderkit-skills/skills/senderkit-mcp-messaging-operations ~/.agents/skills/senderkit-mcp-messaging-operations
# repo-scoped instead? copy into <your-repo>/.agents/skills/
```

Restart Codex so it picks up the skill.

Prompt:

```text
Use $senderkit-mcp-messaging-operations to send a test message and verify its status through SenderKit MCP.
```

Claude / Anthropic-style plugins:

Install the `senderkit` plugin from this repository, or package `skills/senderkit-mcp-messaging-operations/` as a standalone skill. `SKILL.md` is the canonical instruction file, and the skill name declared there is `senderkit-mcp-messaging-operations`.

## Connecting the SenderKit MCP server

Installing the `senderkit` plugin auto-configures the MCP server, so the `senderkit_*` tools are
available without a separate setup step. The auth path differs per client:

- **Claude Code** — uses the repo's `.mcp.json` (`https://mcp.senderkit.com`, no key). On first
  use run `/mcp` and sign in; Claude Code drives the **OAuth** flow and you pick a workspace and
  test/live mode. No secret is stored in the repo. This is the default and recommended path.
- **Cursor** — the `.cursor-plugin/plugin.json` manifest points the server at
  `https://mcp.senderkit.com` over **OAuth** (no key in the repo). Toggle it on under Settings → MCP
  and sign in. To use an API key instead, add an `Authorization: Bearer ${env:SENDERKIT_API_KEY}`
  header in your own `~/.cursor/mcp.json` (the `sk_live_` / `sk_test_` prefix selects mode).
- **Codex** — the `.codex-plugin/plugin.json` manifest points `mcpServers` at
  `.codex-plugin/mcp.json`, which targets `https://mcp.senderkit.com` over **OAuth** (no key in
  the repo). Run `codex mcp login senderkit` to sign in. To use an API key instead, add
  `"bearer_token_env_var": "SENDERKIT_API_KEY"` to that server in your own config.

Prefer to wire it up manually, or use another client (Windsurf, VS Code, Zed, Claude Desktop)?
The SenderKit CLI writes the correct config per client:

```bash
senderkit mcp install --client cursor   # or codex, claude-code, vscode, zed, all
```

A local stdio server (`senderkit mcp`, no network hop) is also available for offline use; see
`https://docs.senderkit.com/mcp/installation`.

## MCP scope

This skill is based on the documented SenderKit MCP tools:

- `senderkit_context`
- `senderkit_send`
- `senderkit_send_raw`
- `senderkit_templates_list`
- `senderkit_templates_get`
- `senderkit_templates_create`
- `senderkit_templates_regenerate`
- `senderkit_messages_list`
- `senderkit_messages_get`
- `senderkit_cancel_message`

It can author **draft** templates (`senderkit_templates_create`, `senderkit_templates_regenerate`) but does not assume MCP support for publishing templates, editing published versions, rendering, webhook management, suppressions, contacts, campaigns, analytics, provider setup, or domain configuration.

Suggested skill description:

```text
Safely operate SenderKit through its MCP connector for sends, template lookup, message inspection, and pending-message cancellation.
```
