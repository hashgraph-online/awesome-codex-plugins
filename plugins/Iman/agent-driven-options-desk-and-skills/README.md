# option-desk plugin

Built by `scripts/package.py` from `shell/skills`, `.claude/commands` and `.claude/agents`. It carries both `.codex-plugin` and `.claude-plugin` manifests. Do not edit here: edit the sources and rebuild, or the next build will discard your changes.

The MCP server entry expects `optiondesk-mcp` on PATH, which `install.sh` puts there.

What reaches which host. The local skills work in Claude Code, ChatGPT and Codex. The two agents are Claude only: Codex reads agents as TOML under ~/.codex/agents and ignores these Markdown ones entirely, so they ship here as inert weight for that host. The commands are Claude first: Codex converts a plugin's commands into skills at install time but skips any command whose body uses $1-style placeholders, so five of the six do not appear there and desk-mark does.

Without the local binary the skills remain instructions and cannot produce fresh market numbers. ChatGPT on the web also needs a hosted HTTP MCP connector to execute the tools; this bundle provides only local stdio MCP.
