<p align="center"><img src="assets/hero.png" alt="looot-plugin: looot for Claude Code, Codex and Cursor" width="100%"></p>

# looot plugin

[![License](https://img.shields.io/github/license/loootai/looot-plugin)](LICENSE) [![Docs](https://img.shields.io/badge/docs-docs.looot.ai-12A06A)](https://docs.looot.ai)

The looot plugin for Claude Code, Codex and Cursor: the looot MCP server (https://api.looot.ai/mcp,
browser sign-in, no key in any file) plus one skill that takes an agent from sign-in to a paid result.

## Install for agents

```bash
claude mcp add --transport http looot https://api.looot.ai/mcp
```

Claude Code plugin: `/plugin marketplace add loootai/looot-plugin`

See also: [awesome-looot-use-cases](https://github.com/loootai/awesome-looot-use-cases) (copy-paste recipes) and [awesome-gtm](https://github.com/loootai/awesome-gtm) (open-source GTM tools).

MIT licensed. The hosted looot service it connects to has its own terms: https://looot.ai/terms

## Install (Claude Code)

```text
/plugin marketplace add loootai/looot-plugin
/plugin install looot@looot
/mcp   (pick plugin:looot:looot, then Authenticate)
```

Then ask for what you need, for example "Use looot to find the work email of Patrick Collison at
stripe.com" or "Use looot to pull today's trending TikTok videos". The skill also runs as `/looot:looot`.

Replit users can add the looot MCP server alone (browser sign-in, no token): [![Add to Replit](https://replit.com/badge?caption=Add%20to%20Replit)](https://replit.com/integrations?mcp=eyJkaXNwbGF5TmFtZSI6Imxvb290IiwiYmFzZVVybCI6Imh0dHBzOi8vYXBpLmxvb290LmFpL21jcCJ9)

Codex and Cursor install steps, the skill list and the commands are in [PLUGIN-README.md](PLUGIN-README.md).

## Layout

| Path | What |
|---|---|
| `.claude-plugin/marketplace.json` | Claude Code marketplace (one plugin: `looot`) |
| `.agents/plugins/marketplace.json` | Codex marketplace |
| `.cursor-plugin/marketplace.json` | Cursor marketplace |
| `plugins/claude-code/looot/` | Claude Code plugin: `.mcp.json` and the `looot` skill |
| `plugins/codex/looot/` | Codex plugin |
| `plugins/cursor/looot/` | Cursor plugin |

These files are generated. Change them at the source and run `scripts/sync-from-monorepo.sh`, never by hand.

## Status

Installs tested by hand in Claude Code and Codex (up to "waiting for sign-in"). Cursor follows its
published format and is not tested yet.
