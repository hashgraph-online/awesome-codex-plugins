# SolidPing plugin for Codex and Claude Code

Uptime monitoring inside your coding agent, through one remote MCP server.
[SolidPing](https://github.com/fclairamb/solidping) is open source (AGPL-3.0) and self-hostable: 40+ check types, multi-region workers, incidents, on-call escalation and status pages.

This repository holds the plugin only: an MCP server address, a skill and the manifests. No code runs on your machine.

## Install

**Codex**

```sh
codex plugin marketplace add fclairamb/solidping-plugin
codex plugin add solidping@solidping
codex mcp login solidping
```

**Claude Code**

```
/plugin marketplace add fclairamb/solidping-plugin
/plugin install solidping@solidping
```

The first tool call (or `codex mcp login`) opens an OAuth 2.1 sign-in in your browser. The hosted service has a free tier, no card needed.

**Self-hosted instance:** change the URL in `.mcp.json` to `https://<your-host>/api/v1/mcp`, or skip the plugin and register the server directly:

```sh
codex mcp add solidping --url https://<your-host>/api/v1/mcp
claude mcp add --transport http solidping https://<your-host>/api/v1/mcp
```

## What you can ask

- "Which of my checks are down right now?"
- "Why is the api-health check failing since this morning?"
- "Add an HTTPS check on https://example.com every minute from two regions"
- "Monitor the TLS certificate of example.com and warn 14 days before it expires"
- "List the incidents of the last 7 days with their duration"
- "Put the database checks in maintenance tonight from 22:00 to 23:00"

## Tools

| Group | Tools |
|---|---|
| Read | `list_checks`, `get_check`, `list_results`, `list_incidents`, `get_incident`, `list_check_types`, `get_check_type_samples`, `list_regions`, `list_check_groups`, `list_status_pages`, `list_maintenance_windows`, `list_integrations` |
| Diagnose | `diagnose_check`, `validate_check`, `run_check` |
| Write | `create_check`, `update_check`, `delete_check`, status page, maintenance window and integration create/update/delete |
| Probe | `fetch_page`, `browser_snapshot`, `run_js_script`: run once against a target you name, store nothing |

Every tool carries MCP annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`). Only the probe tools are open-world.

## Safety

- The plugin pre-approves no tool. Your agent asks before each call unless you allow it yourself.
- The OAuth token is scoped to one organization, and the server applies your role: a viewer cannot create or delete anything through MCP.
- Probe tools go through the server's egress guard, which refuses private and loopback targets unless the instance operator allows them.
- The skill tells the agent to confirm every write with you first and to treat tool output (check names, page bodies, error messages) as data, never as instructions.

## Links

- Docs: https://docs.solidping.io/docs/features/mcp
- Official MCP Registry: `io.github.fclairamb/solidping`
- Security: [SECURITY.md](SECURITY.md)
- License: MIT for this plugin repository. SolidPing itself is AGPL-3.0.
