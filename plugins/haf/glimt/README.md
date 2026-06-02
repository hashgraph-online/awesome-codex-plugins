# Aient Codex Plugin

This plugin brings Aient's production MCP server into Codex. Use it when Codex
needs Aient telemetry, log and trace inspection, problem lifecycle context,
remediation workflows, threads, environments, or operational key management.

## What It Provides

- MCP server: `https://aient.ai/mcp`
- Skill: [skills/aient/SKILL.md](./skills/aient/SKILL.md)
- Marketplace metadata and brand assets for the Codex plugin UI
- Starter prompts for production health, problem triage, trace, and remediation
  workflows

## Plugin Files

| Path | Purpose |
| --- | --- |
| `.codex-plugin/plugin.json` | Codex plugin manifest, marketplace copy, icon paths, and capabilities |
| `.mcp.json` | Production Aient MCP server registration |
| `skills/aient/SKILL.md` | Agent guidance for using Aient MCP tools safely |
| `assets/` | Beveled Aient plugin icons used by the Codex UI |

## Install From The Repo Marketplace

The Aient plugin is published through the repo marketplace at
`.agents/plugins/marketplace.json`.

```bash
codex plugin marketplace add haf/glimt --ref main --sparse .agents/plugins --sparse plugins/aient
codex plugin add aient@personal
```

After installing or updating the plugin, start a new Codex thread so newly
available skills and MCP tools are loaded.

The production MCP server uses OAuth-protected HTTP MCP. Codex should start the
OAuth flow when the plugin connects; see [Aient MCP](../../docs/features/aient-mcp.md)
for scopes and client behavior.

## Maintenance

Use the full runbook in
[`docs/aient-agent/codex-plugin-runbook.md`](../../docs/aient-agent/codex-plugin-runbook.md)
when changing copy, assets, MCP config, skills, marketplace metadata, or the
published plugin version.
