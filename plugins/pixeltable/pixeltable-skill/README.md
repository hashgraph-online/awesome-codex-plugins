# Pixeltable Skill

The backend agents build with: multimodal database, orchestration, and serving in one file.

This plugin teaches AI coding assistants to build Pixeltable applications: tables with computed columns, embedding indexes and vector search, RAG, tool-calling agents, and video, audio, image, and document pipelines across 25+ AI providers. The agent declares the schema as `TableModel` classes in `app.py`, creates the tables with `pxt schema update`, and serves HTTP routes with `pxt service update`.

Verified against Pixeltable 0.7.11 on 2026-09-28: [docs/review-2.12.0.md](docs/review-2.12.0.md).

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
[npx plugins](https://www.npmjs.com/package/plugins):

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

## Pixeltable Cloud MCP

The plugin configures no MCP server. Pixeltable Cloud users can add the hosted [Cloud MCP](https://pixeltable.com/developers/mcp-cloud) at `https://www.pixeltable.com/mcp/cloud` and sign in through the browser. It reads the organization selected at sign-in: databases, services, catalog entries, schemas, up to 25 table rows per call, and logs. It also starts a database at once. Stopping a database, restarting a service, or setting a secret returns a preview first and runs only when called again with `confirm: true`. It deletes nothing and does not deploy; use the `pxt` CLI for that. Add `?read_only=true` to the URL for the read tools only, or `?db=<name>` to limit it to one database. The Skill mentions it so an agent can suggest it to a Cloud user.

The [Docs MCP](https://docs.pixeltable.com/mcp) searches public documentation. The [developer MCP](https://github.com/pixeltable/mcp-server-pixeltable-developer) is a separate local server with catalog, query, and REPL tools.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Run `python3 scripts/validate_plugin.py` after structural changes.

## Links

- [Pixeltable Docs](https://docs.pixeltable.com/) | [GitHub](https://github.com/pixeltable/pixeltable) | [MCP Server](https://github.com/pixeltable/mcp-server-pixeltable-developer) | [Discord](https://discord.gg/QPyqFYx2UN)
- Start: `pxt init` then `pxt service example --out app.py` then `pxt schema update app.py my_app` then `pxt service update app.py my_app`.

## License

Apache 2.0
