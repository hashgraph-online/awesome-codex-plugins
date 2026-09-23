# plori Codex plugin

A one-install plugin for [plori](https://plori.ai): persistent cloud environments for AI agents,
with durable disks, real tools, and memory that stays with each agent.

Installing this plugin gives Codex two things at once:

- **The plori MCP server** (`.mcp.json`): the remote server at `https://api.plori.ai/mcp`,
  so `create_agent`, `invoke_agent`, `schedule_run`, and the rest become tools in your
  Codex session. Authentication is OAuth 2.1, auto-detected on first use (sign in once
  with an email code), or an API key.
- **The plori skill** (`skills/plori/SKILL.md`): teaches Codex how to connect, create
  agents, invoke them and read replies, answer human-in-the-loop requests, and schedule
  deferred runs. Its content is the same one served at
  `https://plori.ai/.well-known/agent-skills/plori/SKILL.md`.

## Install

Add this marketplace, then install the plugin:

```
codex plugin marketplace add plori-ai/codex-plugin
codex plugin add plori@plori
```

The plori server is authenticated over OAuth 2.1 the first time Codex reaches a tool;
approve the one-time email sign-in when the browser opens. Running an agent spends credits
on your plori account.

### Or connect the MCP server directly (no plugin)

The plugin is a convenience wrapper. You can also add the remote server on its own:

```
codex mcp add plori --url https://api.plori.ai/mcp
codex mcp login plori
```

## Background runs

A plori run often takes longer than the tool call that started it. Codex gives an MCP
tool 60 seconds by default, and the plori server returns within that: `invoke_agent`
holds your call for about 50 seconds, then answers with a `run_id` and a
`poll_after_seconds` delay. Call `get_run_result` again after that delay until the run
completes or reports `awaiting_input`.

For work that runs for minutes, use the plori CLI, version 0.4.0 or later:

```sh
curl -fsSL https://plori.ai/install.sh | sh
plori login
plori watch --events terminal,input &   # one JSON line per run that ends or pauses
plori inbox                             # the same information, one shot
```

Each `plori watch` line names the run. Read the reply with `plori result <agent>
<run-id>`, and answer a paused run with `plori answer <run-id> <tool-call-id>
--approve`.

To let a single tool call run longer instead, add the plori server to
`~/.codex/config.toml` yourself, as in
[Or connect the MCP server directly](#or-connect-the-mcp-server-directly-no-plugin),
and set `tool_timeout_sec` on that entry:

```toml
[mcp_servers.plori]
url = "https://api.plori.ai/mcp"
tool_timeout_sec = 900
```

This plugin does not ship that value. The documented fields for a plugin-bundled
remote MCP server are `type`, `url`, and `headers`; none of them set a timeout. The
plugin-scoped config keys (`plugins."plori".mcp_servers.plori.*`) cover enabling a
server, its tool allowlists, and tool approval, not timeouts.

## What is inside

```
.codex-plugin/plugin.json           # the plugin manifest
.mcp.json                           # remote MCP server (api.plori.ai/mcp)
skills/plori/SKILL.md               # the plori skill
.agents/plugins/marketplace.json    # self-marketplace (lists this plugin at ./)
SECURITY.md                         # vulnerability disclosure policy
```

Nothing here runs local code or installs third-party software: the plugin only points
Codex at the hosted plori MCP server and adds the skill text.

## Links

- Site: https://plori.ai
- MCP connect guide: https://plori.ai/mcp
- Integration front door: https://plori.ai/agents.md
- CLI on npm: https://www.npmjs.com/package/@plori/cli
- Questions: dev@plori.ai

## License

MIT
