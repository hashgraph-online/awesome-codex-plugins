# plori Codex plugin

A one-install plugin for [plori](https://plori.ai): cloud computers for AI agents, with
persistent disks, real tools, and memory that survives between sessions.

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
