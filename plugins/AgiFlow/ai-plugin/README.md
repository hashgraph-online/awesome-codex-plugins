# AgiFlow AI Plugin

Official AgiFlow plugin for AI coding clients. Drive AgiFlow project management — planning,
grooming, execution, and review — directly from your AI coding tool.

Works with **Claude Code**, **Codex**, **Cursor**, **Antigravity**, and **Gemini CLI**.

## Installation

This repo is a self-contained, multi-client plugin bundle. Until it is published to each client's
marketplace, load it as a local plugin directory.

### Claude Code

```bash
git clone <your-remote>/agiflow-ai-plugin
claude --plugin-dir ./agiflow-ai-plugin
```

The bundled `.mcp.json` wires the AgiFlow MCP server automatically. Use `/mcp` inside Claude Code to
check the connection.

### Antigravity (Google)

Place the plugin folder in one of Antigravity's plugin locations, then restart:

```bash
# Workspace-level (this project only)
mkdir -p .agents/plugins && cp -R /path/to/agiflow-ai-plugin .agents/plugins/

# Global (all workspaces)
mkdir -p ~/.gemini/config/plugins && cp -R /path/to/agiflow-ai-plugin ~/.gemini/config/plugins/
```

Antigravity reads the root `plugin.json` marker, the `skills/`, and `mcp_config.json` automatically.

### Cursor

Add manually in **Cursor Settings → MCP / Plugins**, pointing at this folder. Cursor's stable surface
is MCP config — the bundled `.mcp.json` provides it.

### Codex

Add the AgiFlow plugin marketplace, then install the plugin from that marketplace:

```bash
codex plugin marketplace add AgiFlow/ai-plugin
codex plugin add agiflow-ai-plugin@agiflow
```

For local development, point Codex at this checkout as a marketplace root:

```bash
codex plugin marketplace add ./agiflow-ai-plugin
codex plugin add agiflow-ai-plugin@agiflow
```

### Gemini CLI

```bash
gemini extensions install <your-remote>/agiflow-ai-plugin
```

The bundled `gemini-extension.json` connects the AgiFlow MCP server via `mcp-remote`.

## How to develop

```bash
git clone <your-remote>/agiflow-ai-plugin
claude --plugin-dir ./agiflow-ai-plugin
```

- Add new workflow instructions under `skills/<name>/SKILL.md`.
- Keep shared guidance in `references/` (e.g. `references/agiflow-agents.md`).
- See `references/plugin-types.md` for per-client manifest notes.

## Features

This plugin connects to the AgiFlow MCP server (`https://agiflow.io/api/v1/mcp`) and exposes AgiFlow
tools across these categories:

- **Projects** — create, inspect, and update projects and their statuses
- **Tasks** — create, list, get, update, reorder, and batch-create tasks
- **Work units** — group tasks into deliverable features/epics and track progress
- **Workflows** — acquire/release locks and coordinate multi-agent runs
- **Members** — list and assign agent members to work
- **Comments** — document decisions and progress on tasks
- **Vault** — read and set scoped configuration entries

### Bundled skills

The plugin ships 10 workflow skills that mirror AgiFlow's scrum pipeline. Your AI client loads them on
demand when your request matches their description — you generally don't invoke them by name:

| Skill | Phase | Use it to… |
| --- | --- | --- |
| `getting-started` | orient | get coached on where to start and which workflow fits |
| `project-plan` | Planning | break requirements into vertical-slice tasks (Planning status) |
| `refine-task` | Planning | turn a vague task into an autonomous-ready spec |
| `backlog-grooming` | Planning → Todo | verify, prioritize, and promote tasks into work units |
| `run-work` | Todo → Done | execute a whole work unit end-to-end in one session |
| `run-task` | Todo → Done | execute a single task through to Review |
| `review-work` | Review | verify acceptance criteria and file follow-ups |
| `triage` | diagnose | classify project issues by severity and recommend actions |
| `daily-standup` | report | a read-only pulse of done / in-progress / blocked / next |
| `orchestrate` | dispatch | route the highest-priority ready work to agents |

Shared guidelines (status model, transitions, tags, work-unit sizing) live in
[`references/agiflow-agents.md`](references/agiflow-agents.md).

## Example usage

```
> Plan a feature: add per-user notification preferences
> Groom the backlog and promote the ready tasks to Todo

> Run task DXX-2
> Execute the checkout work unit end-to-end

> Review the auth work unit against its acceptance criteria
> Give me a daily standup for this project

> Why is this project stuck?
> What should an agent pick up next?
```

## Self-hosted

For a self-hosted AgiFlow instance, point the MCP wiring at your endpoint via the
`AGIFLOW_AI_PLUGIN_MCP_URL` environment variable (consumed by `gemini-extension.json`):

```bash
export AGIFLOW_AI_PLUGIN_MCP_URL="https://mcp.your-agiflow-instance.com/api/v1/mcp"
```

For other clients, edit the server URL in `.mcp.json`, `mcp.json`, and `mcp_config.json`.

## Documentation

- AgiFlow: https://agiflow.io
- Plugin client compatibility: [`references/plugin-types.md`](references/plugin-types.md)

## License

MIT
