# AgentDrives

Look up a SaaS tool, API or provider before your agent picks it. AgentDrives drives real products the way an agent would: it signs up, gets a key, does the work, tries to pay and leaves. For each product the record shows its agent level (L0 to L5), where our agent stopped and whether an agent can sign up, get a key and pay on its own.

This repository packages the AgentDrives MCP server and the `check-agent-access` skill for Claude Code, Codex, Cursor, Gemini CLI and any agent that reads Agent Skills.

## MCP server

`https://agentdrives.com/api/mcp`

Streamable HTTP. Read-only, no key.

| Tool | Use it when |
|---|---|
| `choose_provider_for_task` | You must pick a tool or provider for a task ("send an invoice") |
| `search_tools` | You have a product's name, domain or kind in mind |
| `get_provider` | You are about to use or recommend one product |
| `get_agent_surfaces` | You picked a product and need its API, MCP server, CLI, SDK, docs and payment |
| `compare_providers` | You are deciding between 2 or 3 products for one task |
| `list_best_providers` | You want the products in a category ranked by agent level |
| `list_categories` | You need a category id |
| `get_category` | You want a category's top 10 by level |
| `list_changes` | You need to know what changed at a product, or across the record lately |

## Install

**Claude Code**

```
/plugin marketplace add AgentDrives/agentdrives-mcp
/plugin install agentdrives@agentdrives
```

The server alone: `claude mcp add --transport http agentdrives https://agentdrives.com/api/mcp`

**Cursor**

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "agentdrives": { "url": "https://agentdrives.com/api/mcp" }
  }
}
```

**Gemini CLI**

```
gemini extensions install https://github.com/AgentDrives/agentdrives-mcp
```

**The skill, for any agent**

```
npx skills add AgentDrives/agentdrives-mcp
```

**Other MCP clients**

```json
{
  "mcpServers": {
    "agentdrives": { "type": "http", "url": "https://agentdrives.com/api/mcp" }
  }
}
```

## Levels

| Level | What an agent can do |
|---|---|
| L0 Read-only | Read about it. There is nothing to use. |
| L1 Needs a person | It can't get in on its own. |
| L2 Gets in | It gets in on its own but does less than half the core work. |
| L3 Does the work | It gets in on its own and does half the core work or more. |
| L4 Runs on its own | It does the core work and can leave on its own. |
| L5 Autonomous | All of that, and it can pay on its own for the work. |

## What's here

- `plugin.json` and `mcp.json`: the plugin in the shared Agent Plugins format
- `.claude-plugin/` and `.mcp.json`: the Claude Code plugin and its marketplace entry
- `.codex-plugin/`: the Codex plugin
- `.cursor-plugin/`: the Cursor plugin
- `gemini-extension.json`: the Gemini CLI extension
- `skills/check-agent-access/SKILL.md`: the skill, the same file agentdrives.com publishes at `/.well-known/agent-skills/check-agent-access/SKILL.md`. A daily workflow keeps the copy here in step.

## Security

See [SECURITY.md](SECURITY.md).

## Licence

The packaging in this repository is MIT. The data the server returns is CC BY 4.0: see [agentdrives.com/data/licence](https://agentdrives.com/data/licence).

Docs: [agentdrives.com/docs/mcp](https://agentdrives.com/docs/mcp)
