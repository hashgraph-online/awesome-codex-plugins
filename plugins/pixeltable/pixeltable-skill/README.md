# Pixeltable Skill

Agent Skill that teaches AI coding assistants to write Pixeltable application files: `TableModel` in `app.py`, then `pxt schema update`, then `pxt service update`.

Verified against Pixeltable 0.7.8 on 2026-09-19: [docs/review-2.11.0.md](docs/review-2.11.0.md).

## Install

### Skill (recommended for most assistants)

Install the portable skill with [npx skills](https://github.com/vercel-labs/skills):

```bash
npx skills add pixeltable/pixeltable-skill
```

This installs `SKILL.md` and its references for supported coding assistants,
including Cursor, Copilot, Windsurf, and the Codex IDE extension.

**Google Antigravity** is not one of them: it reads
`~/.gemini/antigravity/skills`, which `npx skills` does not write to. Install
there with `./install.sh --platform antigravity`.

### Full plugin

Install the skill with its client-supported commands, agents, and hooks using
[npx plugins](https://github.com/vercel-labs/plugins):

```bash
npx plugins add pixeltable/pixeltable-skill
```

Client-native marketplace options:

- **Claude Code:** `/plugin marketplace add pixeltable/pixeltable-skill`, then
  `/plugin install pixeltable@pixeltable-skill`
- **ChatGPT desktop and Codex:**
  `codex plugin marketplace add pixeltable/pixeltable-skill --ref main`, then
  `codex plugin add pixeltable@pixeltable-skill`. Use `/plugins` in Codex or the
  **Plugins** page in ChatGPT desktop.

Restart or start a new conversation after installing. Repository marketplaces
are team-distribution sources; they do not publish to a public directory.

### Any LLM (paste URL into context)

- [llms.txt](https://www.pixeltable.com/llms.txt)
- [llms-full.txt](https://docs.pixeltable.com/llms-full.txt)

## What's Inside

```
skills/pixeltable-skill/
├── SKILL.md                    # Contract: app.py, schema update, service update
└── references/
    ├── core-api.md             # Tables, querying, views, UDFs, config
    ├── cli.md                  # pxt CLI
    ├── providers.md            # Import and output shape
    ├── workflows.md            # FastAPIRouter
    └── anti-patterns.md        # Wrong/right stack
```

Client manifests and marketplace metadata live alongside the shared skill so
each supported installer can discover the format it understands.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Run `python3 scripts/validate_plugin.py` after structural changes.

## Links

- [Pixeltable Docs](https://docs.pixeltable.com/) | [GitHub](https://github.com/pixeltable/pixeltable) | [MCP Server](https://github.com/pixeltable/mcp-server-pixeltable-developer) | [Discord](https://discord.gg/QPyqFYx2UN)
- Start: `pxt init` then `pxt service example --out app.py` then `pxt schema update app.py my_app` then `pxt service update app.py my_app`.

## License

Apache 2.0
