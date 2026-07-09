# odw-codex

Codex adapter for Open Dynamic Workflows.

## What this is

Codex supports local plugins that can package skills, MCP servers, scripts, and
setup metadata. This adapter ships ODW as a local Codex plugin bundle while also
keeping the older direct MCP and skill installs as fallbacks.

- `.codex-plugin/plugin.json` - Codex plugin manifest
- `.mcp.json` - generated at install time so the plugin points at this checkout
- `skills/odw/SKILL.md` - the workflow playbook Codex can load as a skill
- `skills/ultracode/SKILL.md` - alias skill for users who ask Codex for ultracode-style execution
- `scripts/daemon-bridge.js` - zero-dependency bridge to the local daemon API
- `AGENTS.md` - drop-in repo instruction block

## Install from this checkout

```bash
odw-daemon integrate codex
odw-daemon doctor codex
```

The installer writes:

- `~/.codex/plugins/odw` - local plugin bundle
- `~/.agents/plugins/marketplace.json` - personal marketplace entry
- `~/.codex/config.toml` - fallback MCP server config
- `~/.agents/skills/odw` - fallback skill folder
- `~/.agents/skills/ultracode` - fallback ultracode alias skill folder

Start the daemon before running large workflows:

```bash
odw-daemon start
```

Then open Codex and ask for `workflow: ...`, `ultracode ...`, or
`/deep-research ...`. The plugin and skill route substantial work through the
ODW daemon so the chat window does not have to babysit every parallel agent.
